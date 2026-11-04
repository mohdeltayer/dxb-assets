"""Review scores, read from Metacritic and OpenCritic (studio, adv-20261104-review-scores-template, Mohammad 4 Nov 2026).

The review-scores Reel never carries a number typed by hand: the totals and the outlet list come from the two
aggregators' own pages, read at build time, cached, and stamped with the time they were read.

    python3 templates/reviewscores.py fetch --mc <metacritic slug> --oc <opencritic id>[/slug] [--fresh] [--out f.json]
    python3 templates/reviewscores.py find "<game name>"          # Metacritic slugs with platform and date
    python3 templates/reviewscores.py show <cached json>          # the spread, high, low and totals as the job wants them

What it reads (read-only, one request per page, a browser User-Agent, no login, no API key):
  - Metacritic: backend.metacritic.com, the same JSON the site's pages load: the game page (critic score, review count,
    positive, mixed, negative) and the critic reviews list (outlet, Metacritic's 0 to 100 score, date, author, url).
    Metacritic shows every outlet on its 100 scale, so its list is used for coverage only; never for an outlet's own score.
  - OpenCritic: the game page and its /reviews page, from the state the site embeds in the HTML (its API needs a key):
    top critic average, percent recommended, number of top critic reviews and of all reviews, and per review the outlet,
    the score and its ScoreFormat (the outlet's own scale: "0 to 10 incl decimals", "0 to 5 stars", ...), authors,
    date and url. `own_scale()` turns a score back into what the outlet printed (9/10, 5/5, 95/100).
  - An outlet with a verbal verdict (Saudi Gamer's «أسطورية», a "Recommended") is read from its own page by the person
    writing the job and entered with `verdict`; the aggregator's 5/5 or 100 is never shown in its place.

Cache: uploads/cache/reviews/<mc slug>.json. A cached read younger than CACHE_MIN minutes is reused unless --fresh;
every read keeps `read_at` (UTC) so the card's «حتى ...» line and the job's `totals_read_at` say when the numbers were
true. Totals move for days after an embargo lifts; a job built from a read older than STALE_MIN minutes is refused by
`check_job` (render_job.check calls it for template reviewscores).
"""
import datetime as dt, html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(os.environ.get('DXB_UPLOADS', '/mnt/user-data/uploads'), 'cache', 'reviews')   # as cards.U
CACHE_MIN = 30          # reuse a read this young
STALE_MIN = 180         # a job's totals older than this at render time are refused (re-read, then render)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
MC = 'https://backend.metacritic.com'
OC = 'https://opencritic.com'


def _get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json,text/html'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:                      # noqa: BLE001  (a read-only fetch: retry, then say why)
            err = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f'reviewscores: could not read {url}: {err}')


# ---------- Metacritic ----------

def mc_find(name):
    q = urllib.parse.quote(name)
    d = json.loads(_get(f'{MC}/finder/metacritic/search/{q}/web?offset=0&limit=20&mcoTypeId=13'
                        '&componentName=search-tabs&componentDisplayName=Search+Page+Tab+Filters&componentType=FilterConfig'))
    return [{'slug': it.get('slug'), 'title': it.get('title'), 'date': it.get('releaseDate'),
             'platforms': [p.get('name') for p in it.get('platforms') or []],
             'score': (it.get('criticScoreSummary') or {}).get('score')}
            for it in (d.get('data') or {}).get('items', [])]


def mc_summary(slug):
    d = json.loads(_get(f'{MC}/composer/metacritic/pages/games/{slug}/web?filter=all&sort=date'))
    for comp in d.get('components', []):
        item = (comp.get('data') or {}).get('item') or {}
        s = item.get('criticScoreSummary')
        if s and item.get('slug') == slug:
            return {'score': s.get('score'), 'reviews': s.get('reviewCount'), 'positive': s.get('positiveCount'),
                    'mixed': s.get('neutralCount'), 'negative': s.get('negativeCount'), 'sentiment': s.get('sentiment'),
                    'title': item.get('title'), 'url': f'https://www.metacritic.com/game/{slug}/'}
    raise RuntimeError(f'reviewscores: no critic score summary on the Metacritic page for {slug}')


def mc_reviews(slug, cap=200):
    out, off = [], 0
    while off < cap:
        d = json.loads(_get(f'{MC}/reviews/metacritic/critic/games/{slug}/web?offset={off}&limit=10&filterBySentiment=all'
                            '&sort=score&componentName=critic-reviews&componentDisplayName=critic+Reviews'
                            '&componentType=ReviewList'))
        items = (d.get('data') or {}).get('items') or []
        out += [{'outlet': r.get('publicationName'), 'mc_score': r.get('score'), 'date': r.get('date'),
                 'author': r.get('author') or None, 'url': r.get('url')} for r in items]
        total = (d.get('data') or {}).get('totalResults') or 0
        off += 10
        if not items or off >= total:
            break
    return out


# ---------- OpenCritic ----------

def _oc_state(url):
    s = _get(url)
    m = re.search(r'<script id="(?:serverApp-state|ng-state)"[^>]*>(.*?)</script>', s, re.S)
    if not m:
        raise RuntimeError(f'reviewscores: no embedded state on {url} (OpenCritic changed its page?)')
    t = html.unescape(m.group(1))
    for a, b in (('&q;', '"'), ('&a;', '&'), ('&s;', "'"), ('&l;', '<'), ('&g;', '>')):
        t = t.replace(a, b)
    return json.loads(t)


def own_scale(score, fmt):
    """An OpenCritic score (0 to 100) back on the outlet's own scale, as printed: '9/10', '9.5/10', '5/5', '4.5/5',
    '95/100'. `fmt` is the review's ScoreFormat ({name, base, ...}); base is what OpenCritic multiplied by."""
    if score is None or not fmt:
        return None
    base = fmt.get('base') or 1
    top = round(100 / base)
    v = score / base
    v = int(v) if abs(v - round(v)) < 1e-6 else round(v, 1)
    return f'{v}/{top}'


def oc_game(ident):
    """ident: '21344' or '21344/the-legend-of-zelda-ocarina-of-time' (the id from the game's OpenCritic url)."""
    gid = str(ident).split('/')[0]
    slug = str(ident).split('/', 1)[1] if '/' in str(ident) else 'x'
    st = _oc_state(f'{OC}/game/{gid}/{slug}')
    g = st.get(f'game/{gid}') or {}
    top = g.get('topCriticScore')
    summary = {'name': g.get('name'), 'top_critic_average': None if top is None or top < 0 else round(top),
               'percent_recommended': None if (g.get('percentRecommended') or -1) < 0 else round(g['percentRecommended']),
               'top_critic_reviews': g.get('numTopCriticReviews'), 'reviews': g.get('numReviews'),
               'tier': g.get('tier'), 'url': f'{OC}/game/{gid}/{slug}'}
    rs = _oc_state(f'{OC}/game/{gid}/{slug}/reviews')
    reviews = []
    for k, v in rs.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and 'Outlet' in v[0]:
            for r in v:
                fmt = r.get('ScoreFormat') or {}
                reviews.append({'outlet': (r.get('Outlet') or {}).get('name'), 'score': r.get('score'),
                                'scale': fmt.get('name'), 'own': own_scale(r.get('score'), fmt),
                                'stars': bool(fmt.get('isStars')),
                                'authors': [a.get('name') for a in r.get('Authors') or []],
                                'date': (r.get('publishedDate') or '')[:10], 'url': (r.get('externalUrl') or '').strip(),
                                'snippet': r.get('snippet')})
    return summary, reviews


# ---------- the read, cached ----------

def fetch(mc_slug, oc_ident, fresh=False, out=None):
    os.makedirs(CACHE, exist_ok=True)
    path = out or os.path.join(CACHE, f'{mc_slug}.json')
    if not fresh and os.path.exists(path):
        d = json.load(open(path))
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d['read_at'])).total_seconds() / 60
        if age < CACHE_MIN:
            d['cached_min'] = round(age)
            return d
    mc = mc_summary(mc_slug)
    ocs, ocr = oc_game(oc_ident)
    d = {'read_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
         'metacritic': mc, 'metacritic_reviews': mc_reviews(mc_slug), 'opencritic': ocs, 'opencritic_reviews': ocr}
    json.dump(d, open(path, 'w'), ensure_ascii=False, indent=1)
    return d


def dubai(read_at):
    """'2026-11-04T13:20:00+00:00' -> ('4 نوفمبر', '17:20'), Dubai time, for the totals card."""
    import fast_ar as A
    t = dt.datetime.fromisoformat(read_at).astimezone(dt.timezone(dt.timedelta(hours=4)))
    return f'{t.day} {A.MONTHS[t.month - 1]}', t.strftime('%H:%M')


def show(d):
    mc, oc = d['metacritic'], d['opencritic']
    print(f"read {d['read_at']}  Metacritic {mc['score']} ({mc['reviews']} reviews; +{mc['positive']} ~{mc['mixed']} "
          f"-{mc['negative']})  OpenCritic top critic {oc['top_critic_average']}, {oc['percent_recommended']}% recommend, "
          f"{oc['top_critic_reviews']} top critics, {oc['reviews']} reviews")
    rs = sorted(d['opencritic_reviews'], key=lambda r: (r['score'] is None, -(r['score'] or 0)))
    for r in rs:
        print(f"  {r['own'] or 'unscored':>8}  {r['outlet']:<22} {r['date']}  {', '.join(r['authors']) or '-'}  {r['url']}")
    lo = [r for r in rs if r['score'] is not None]
    if lo:
        print(f"lowest on OpenCritic: {lo[-1]['outlet']} {lo[-1]['own']}; Metacritic's lowest: "
              f"{min(d['metacritic_reviews'], key=lambda r: r['mc_score'] or 999)}")


def check_job(job, now=None):
    """Errors for a reviewscores job (render_job.check): totals read from the pages and recent; every spread row and
    verdict on an outlet's own scale with a date; quotes short and attributed."""
    errs = []
    t = job.get('review_scores') or {}
    ra = t.get('totals_read_at')
    if not ra:
        errs.append('review_scores.totals_read_at missing: run reviewscores.py fetch and copy read_at')
    else:
        now = now or dt.datetime.now(dt.timezone.utc)
        age = (now - dt.datetime.fromisoformat(ra)).total_seconds() / 60
        if age > STALE_MIN:
            errs.append(f'totals read {round(age)} minutes ago (over {STALE_MIN}): fetch again before the render')
    for k in ('metacritic', 'opencritic'):
        if not t.get(k):
            errs.append(f'review_scores.{k} missing')
    for row in t.get('spread', []):
        if not row.get('score') or not row.get('date'):
            errs.append(f"spread row {row.get('outlet')}: score as printed and the review date are required")
    for v in t.get('verdicts', []):
        for q in ('positive', 'negative'):
            qq = v.get(q) or {}
            words = len((qq.get('ar') or '').split())
            if qq and words > 15:
                errs.append(f"{v.get('outlet')} {q} quote is {words} words (15 at most)")
            if qq and not qq.get('en') and not v.get('arabic_source'):
                errs.append(f"{v.get('outlet')} {q} quote: keep the original wording in 'en' for the translation check")
        if not v.get('reviewer'):
            errs.append(f"{v.get('outlet')}: name the reviewer")
    return errs


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] not in ('fetch', 'find', 'show'):
        sys.exit(__doc__)
    if a[0] == 'find':
        for r in mc_find(' '.join(a[1:])):
            print(r)
    elif a[0] == 'show':
        show(json.load(open(a[1])))
    else:
        opt = {a[i]: a[i + 1] for i in range(1, len(a) - 1) if a[i].startswith('--') and a[i] != '--fresh'}
        d = fetch(opt['--mc'], opt['--oc'], fresh='--fresh' in a, out=opt.get('--out'))
        show(d)
        print('cache:', opt.get('--out') or os.path.join(CACHE, opt['--mc'] + '.json'))
