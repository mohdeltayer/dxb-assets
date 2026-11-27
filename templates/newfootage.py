"""Trailer news shows the new trailer (Mohammad, 28 Nov 2026). Autofix only: it never refuses, holds or delays a Reel.

Case: the Hollow Knight: Silksong Sea of Sorrow Reel (27 Nov) ran the base game's Release and Reveal trailers from Steam
(uploaded Aug 2025 and earlier) under lines about the new expansion trailer; viewers wrote "you showed the game trailer,
not the DLC trailer".

When a story is about a new trailer, DLC, expansion, update or reveal (`about_new`), each footage video's publish date
(`file_date`: the upload stamp in a Steam trailer's path, a dated URL path, the item's "published", or the file's
Last-Modified header) is compared with the story's date. Footage older than the announcement (STALE_DAYS) cannot carry
the Reel. `fix(job)` then, in order:
  a. a new trailer: the job's footage source (steam:<appid>, a Nintendo, IGN or PlayStation page) read again for a video
     dated on or after the announcement; the stale shots move onto it (the shot picker places them);
  b. official stills of the new content: the og:image / twitter:image of the story's official pages first, then of the
     outlets that carried the news (the publisher's art they relay), 1000 px wide or more; every footage shot becomes a
     still with a slow pan, our bed under it, and the credit says what it is («اللقطات: صورة رسمية للمحتوى الجديد»);
  c. nothing reachable: the old footage stays, credited as what it is («اللقطات: من اللعبة الأساسية لا من العرض
     الجديد»), so it is never presented as the new trailer.
Every step is on the picture ladder in qc.json. A failure of the check itself is a warning.
"""
import datetime as dt
import email.utils
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STALE_DAYS = 3             # footage more than this many days older than the story is not the new trailer
MIN_W = 1000               # an official still narrower than this is not used
VIDEO = ('.mp4', '.mov', '.mkv', '.webm', '.m4v')
KINDS = {'trailer', 'reveal', 'dlc', 'expansion', 'update', 'announcement', 'teaser', 'season', 'crossover'}
WORDS = ['توسعة', 'إضافة', 'المحتوى الإضافي', 'عرض دعائي', 'العرض الدعائي', 'إعلان تشويقي', 'تحديث', 'الموسم', 'كشفت',
         'تكشف', 'يكشف', 'كشف', 'DLC', 'expansion', 'trailer', 'teaser', 'update', 'season', 'reveal']
UA = {'User-Agent': 'Mozilla/5.0 (compatible; dxb-render)'}
CREDIT_STILL = 'اللقطات: صورة رسمية للمحتوى الجديد'
CREDIT_OLD = 'اللقطات: من اللعبة الأساسية لا من العرض الجديد'


def _get(url, timeout=30, head=False):
    req = urllib.request.Request(url, headers=UA, method='HEAD' if head else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (r.headers, b'' if head else r.read())


def about_new(job):
    """True for a story about a new trailer, DLC, expansion, update or reveal."""
    if str(job.get('kind_news') or '').lower() in KINDS or str(job.get('story_class') or '') == 'trailer' \
            and str(job.get('kind_news') or '').lower() in KINDS:
        return True
    t = ' '.join(str(job.get(k) or '') for k in ('headline', 'spoken'))
    return any(w.lower() in t.lower() for w in WORDS)


def story_date(job):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', str(job.get('story') or ''))
    return dt.date.fromisoformat(m.group(1)) if m else None


def _ts_in_path(url):
    """A unix time in the path (Steam trailers: /store_trailers/<app>/<id>/<hash>/<upload time>/...)."""
    for seg in str(url).split('?')[0].split('/'):
        if seg.isdigit() and len(seg) == 10 and 1.3e9 < int(seg) < 2.2e9:
            return dt.datetime.fromtimestamp(int(seg), dt.timezone.utc).date()
    return None


def _date_in_path(url):
    m = re.search(r'/(20\d{2})/(\d{1,2})/(\d{1,2})/', str(url))
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


_STEAM = {}


def _steam_hls(appid, name):
    if appid not in _STEAM:
        import footage
        try:
            _STEAM[appid] = footage.steam_trailers(appid)
        except Exception:                                   # noqa: BLE001
            _STEAM[appid] = []
    return next((t.get('hls') for t in _STEAM[appid] if t['name'].strip() == str(name).strip()), None)


def file_date(item):
    """(date or None, how) for one footage item."""
    if item.get('published'):
        try:
            return dt.date.fromisoformat(str(item['published'])[:10]), 'published'
        except ValueError:
            pass
    if item.get('steam') and item.get('trailer'):
        hls = _steam_hls(int(item['steam']), item['trailer'])
        d = _ts_in_path(hls) if hls else None
        if d:
            return d, 'steam upload stamp'
    url = item.get('url')
    if url:
        d = _date_in_path(url) or _ts_in_path(url)
        if d:
            return d, 'dated url'
        try:
            h, _ = _get(url, head=True)
            lm = h.get('Last-Modified')
            if lm:
                return email.utils.parsedate_to_datetime(lm).date(), 'last-modified'
        except Exception:                                   # noqa: BLE001
            pass
    return None, 'unknown'


def stale(job):
    """[(file, date, how)] of footage videos older than the story by more than STALE_DAYS; [] when not trailer news."""
    sd = story_date(job)
    if not sd or not about_new(job):
        return []
    out = []
    for it in job.get('footage') or []:
        if not str(it.get('file', '')).lower().endswith(VIDEO):
            continue
        d, how = file_date(it)
        if d and (sd - d).days > STALE_DAYS:
            out.append((it['file'], d, how))
    return out


def _og_images(url):
    try:
        _h, body = _get(url)
    except Exception:                                       # noqa: BLE001
        return []
    html = body.decode('utf-8', 'ignore')
    out = []
    for prop in ('og:image', 'twitter:image', 'og:image:url'):
        for m in re.finditer(r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]*>', html, re.I):
            c = re.search(r'content=["\']([^"\']+)', m.group(0))
            if c and c.group(1).startswith('http') and c.group(1) not in out:
                out.append(c.group(1).replace('&amp;', '&'))
    return out


def _sources(job, story):
    """Official pages first, then outlets; never the base game's store page (its art is the old game)."""
    srcs = list((story or {}).get('sources') or [])
    off = [s for s in srcs if s.get('role') in ('primary', 'official') and 'store.steampowered.com/app' not in str(s.get('url'))
           and 'nintendo.com/us/store' not in str(s.get('url'))]
    rest = [s for s in srcs if s not in off and s.get('role') == 'outlet']
    return [(s['url'], s.get('role'), s.get('name')) for s in off + rest if s.get('url')]


def stills(job, story, upath, n=3):
    """Download up to n official stills of the new content; [(file, source url)]."""
    out = []
    for url, role, _name in _sources(job, story):
        for img in _og_images(url):
            if len(out) >= n:
                return out
            try:
                _h, data = _get(img)
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(data))
                if im.width < MIN_W:
                    continue
                f = f"{job['name']}-newart-{len(out)}.jpg"
                im.convert('RGB').save(os.path.join(upath, f), quality=92)
                out.append((f, url))
            except Exception:                               # noqa: BLE001
                continue
    return out


def _credit(job, text):
    """Put `text` as the footage part of every credit («... · اللقطات: ...»), or add it to a credit without one."""
    for c in job.get('credits') or []:
        if len(c) > 2 and isinstance(c[2], str):
            base = re.split(r'\s*[·\n]\s*(?:ال)?لقطات\s*:', c[2])[0].strip()
            c[2] = f'{base} · {text}' if base else text


def fix(job, upath, story=None, fetch=None, ladder=None, warn=None):
    """The autofix in the module note. Returns the step taken ('a', 'b', 'c') or None when nothing was stale."""
    old = stale(job)
    if not old:
        return None
    oldf = {f for f, _d, _h in old}
    sd = story_date(job)
    why = ', '.join(f'{f} {d} ({h})' for f, d, h in old)
    fresh = [it['file'] for it in job.get('footage') or [] if str(it.get('file', '')).lower().endswith(VIDEO)
             and it['file'] not in oldf]
    if not fresh and job.get('footage_source') and fetch:    # a. a new trailer from the same official source
        try:
            import footage
            r = footage.resolve(job['footage_source'], name=job['name'], do_check=False, game=job.get('game'))
            for c in r.get('candidates') or []:
                d, _how = file_date(c['job'])
                if d and (sd - d).days <= STALE_DAYS:
                    item = dict(c['job'], file=f"{job['name']}-new-{len(fresh)}.mp4")
                    fetch(item)
                    job['footage'].append(item)
                    fresh.append(item['file'])
                    break
        except Exception as e:                              # noqa: BLE001
            if warn:
                warn('new trailer', f'{type(e).__name__}: {e}')
    if fresh:
        k = 0
        for i, sh in enumerate(job.get('shots') or []):
            if isinstance(sh, list) and sh and sh[0] in oldf:
                sh[0], sh[1] = fresh[k % len(fresh)], 'auto'
                sh[3:] = [None]
                k += 1
        import autoshots as AS
        AS.expand(job)
        if ladder:
            ladder('picture', 'reel', 'a', f'trailer news: the new trailer ({", ".join(fresh)}) in place of older footage: {why}')
        return 'a'
    imgs = []
    try:
        imgs = stills(job, story, upath)
    except Exception as e:                                  # noqa: BLE001
        if warn:
            warn('new stills', f'{type(e).__name__}: {e}')
    if imgs:                                                # b. official stills of the new content, slow pan
        k = 0
        for i, sh in enumerate(job.get('shots') or []):
            if isinstance(sh, list) and sh and sh[0] in oldf:
                f = imgs[k % len(imgs)][0]
                sh[:] = [f, None, float(sh[2]), [0.42, 0.58] if k % 2 == 0 else [0.58, 0.42]]
                k += 1
        job['footage'] = [it for it in job.get('footage') or [] if it.get('file') not in oldf] + \
            [{'file': f, 'note': f'official still of the new content, from {u}'} for f, u in imgs]
        job.pop('shots_auto', None)
        job['track'] = None
        job['bed_reason'] = 'trailer news with no new trailer reachable: official stills of the new content'
        job['stylised'] = False                             # stills fill the frame; no detector step for them
        job['showcase_fallback'] = False
        _credit(job, CREDIT_STILL)
        if ladder:
            ladder('picture', 'reel', 'b', f'trailer news: official stills of the new content ({len(imgs)} from '
                   f'{", ".join(sorted({u for _f, u in imgs}))}) in place of older footage: {why}')
        return 'b'
    _credit(job, CREDIT_OLD)                                # c. the old footage, named as what it is
    if ladder:
        ladder('picture', 'reel', 'c', f'trailer news: no new trailer or official still reachable; older footage stays, '
               f'credited as the base game: {why}')
    if warn:
        warn('new trailer', f'older footage carries trailer news, credited as the base game: {why}')
    return 'c'


if __name__ == '__main__':
    j = json.load(open(sys.argv[1], encoding='utf-8'))
    print(json.dumps({'about_new': about_new(j), 'story_date': str(story_date(j)),
                      'stale': [(f, str(d), h) for f, d, h in stale(j)]}, ensure_ascii=False))
