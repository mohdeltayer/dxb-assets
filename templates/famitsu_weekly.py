"""Weekly Famitsu sales Reel on the server (Mohammad, 19 Nov 2026: "set this as a weekly Thursday job on the server:
gather box art and screenshots for the likely top 10 before 16:45 Dubai and build as soon as the article is up").

Famitsu posts the week's chart on Thursday at 22:00 JST (13:00Z, 17:00 Dubai); holiday weeks move, and each article
ends with the next date ("次回は...に掲載予定"). `.github/workflows/famitsu-weekly.yml` runs this on dxb-render-1:

    python3 templates/famitsu_weekly.py prep            fetch every screenshot and box art the likely top 10 needs
    python3 templates/famitsu_weekly.py watch [mins]     poll Famitsu's new-article list until this week's chart is up
    python3 templates/famitsu_weekly.py build <url>      parse it, write jobs/render/famitsu-<week>-sales.json
    python3 templates/famitsu_weekly.py remember <job>   record a job built by hand as the newest (art + last week)

Likely top 10: last week's chart (the newest jobs/done or jobs/render famitsu-*-sales job) plus every title in the art
library released in the last three weeks. Art comes from `assets/famitsu-art.json` (English title -> screenshot with
its pan, optional box art), filled from every Famitsu job built so far; a title not in it is looked up on Nintendo's
US store by name (Switch and Switch 2 only: the product's own nsuid, the first 1920-wide screenshot). A Japanese title
not in famitsu.TITLES, or a title with no art found, stops the build and writes `newsroom/famitsu-pending.json` with
the parsed chart and what is missing, so a session finishes it (nothing is guessed). The render is the usual
sales_full famitsu job (render.yml); scheduling in Publer stays with a session (server publishing is parked).
"""
import datetime as dt
import glob
import html
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import famitsu as F  # noqa: E402

ART = os.path.join(HERE, 'assets', 'famitsu-art.json')
PENDING = os.path.join(ROOT, 'newsroom', 'famitsu-pending.json')
LAST = os.path.join(HERE, 'assets', 'famitsu-last.json')     # the newest job as built (render.yml deletes job files)
LIST = 'https://www.famitsu.com/category/new-article/page/%d'
MARK = '【ソフト＆ハード週間販売数】'
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
AR_MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر',
             'ديسمبر']
AR_COUNT = {2: 'لعبتان جديدتان', 3: 'ثلاث ألعاب جديدة', 4: 'أربع ألعاب جديدة', 5: 'خمس ألعاب جديدة',
            6: 'ست ألعاب جديدة', 7: 'سبع ألعاب جديدة', 8: 'ثماني ألعاب جديدة', 9: 'تسع ألعاب جديدة',
            10: 'عشر ألعاب جديدة'}
NINTENDO_IMG = 'https://assets.nintendo.com/image/upload/f_jpg/q_auto/'


def _get(url, timeout=40):
    return subprocess.run(['curl', '-sL', '-m', str(timeout), '-A', 'Mozilla/5.0', url],
                          capture_output=True, text=True).stdout


def _iso(date):
    try:
        return dt.datetime.strptime(date, '%d %b %Y').date().isoformat()
    except (TypeError, ValueError):
        return ''


def load_art():
    try:
        return json.load(open(ART, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_art(art):
    json.dump(art, open(ART, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)


def key(title, plat=None):
    t = ' '.join(title.replace('\n', ' ').split())
    return f'{t} | {plat}' if plat else t


def jobs():
    """Every Famitsu sales job on disk, newest article first."""
    out = []
    for p in glob.glob(os.path.join(ROOT, 'jobs', '*', 'famitsu-*-sales.json')) + [LAST]:
        try:
            j = json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if j.get('kind') == 'famitsu' and j.get('rows'):
            out.append(j)
    seen, uniq = set(), []
    for j in sorted(out, key=lambda j: (j.get('article_id') or 0, j.get('date', '')), reverse=True):
        if j['name'] not in seen:
            seen.add(j['name'])
            uniq.append(j)
    return uniq


def learn(job, art=None):
    """Add a job's screenshots and box art to the library, keyed by title (and title | platform)."""
    art = art if art is not None else load_art()
    items = {f['file']: f for f in job.get('footage', [])}
    for r in job['rows']:
        shot = items.get(r['shot'][0])
        if not shot:
            continue
        e = {'shot': shot, 'pan': r['shot'][1], 'title': r['title'], 'seen': job.get('date'),
             'seen_iso': _iso(job.get('date'))}
        if r.get('art') and items.get(r['art']):
            e['art'] = items[r['art']]
        for k in (key(r['title'], r['plat']), key(r['title'])):
            art.setdefault(k, {}).update(e)
    return art


def learn_save(job):
    save_art(learn(job))


def wrap(title, width=30):
    """Two lines for a long title: after its colon, before a ' + ', else at the space nearest the middle."""
    if len(title) <= width:
        return title
    if ': ' in title:
        return title.replace(': ', ':\n', 1)
    if ' + ' in title:
        return title.replace(' + ', '\n+ ', 1)
    sp = [i for i, c in enumerate(title) if c == ' ']
    i = min(sp, key=lambda i: abs(i - len(title) / 2)) if sp else None
    return title if i is None else title[:i] + '\n' + title[i + 1:]


def remember(job):
    """Keep the newest job (its article, rows and hardware) for next week's change and likely list."""
    json.dump(job, open(LAST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    learn_save(job)


def nintendo_lookup(title, plat):
    """A Switch or Switch 2 title's own screenshot from Nintendo's US store, by its product slug. None when not found."""
    if plat not in ('Switch', 'Switch2'):
        return None
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower().replace("'", '')).strip('-')
    for suffix in (('-switch-2', '-switch') if plat == 'Switch2' else ('-switch',)):
        page = _get(f'https://www.nintendo.com/us/store/products/{slug}{suffix}/')
        m = re.search(r'"nsuid":"(\d+)"', page)
        if not m:
            continue
        ids = sorted(set(re.findall(rf'store/software/switch2?/{m.group(1)}/[0-9a-f]{{40,64}}', page)))
        for pid in ids:
            url = NINTENDO_IMG + pid
            size = subprocess.run(['curl', '-sL', '-m', '30', url, '-o', '/tmp/fw-probe.jpg'], capture_output=True)
            try:
                from PIL import Image
                w, h = Image.open('/tmp/fw-probe.jpg').size
            except Exception:  # noqa: BLE001
                continue
            if w >= 1280 and abs(w / h - 16 / 9) < 0.05:
                name = 'fw-' + re.sub(r'[^a-z0-9]+', '-', title.lower())[:40].strip('-') + '.jpg'
                return {'shot': {'file': name, 'url': url}, 'pan': [0.3, 0.6], 'title': title,
                        'source': f'nintendo.com/us/store/products/{slug}{suffix}/', 'auto': True}
    return None


def prep(cache=None):
    """Before the article: download and open every screenshot and box art the likely top 10 needs (last week's chart
    plus the library's titles seen in the last three weeks). A link that no longer opens is dropped from the library
    entry, and the title is looked up again on Nintendo's US store, so the build finds working art at 17:00 Dubai.
    Returns the titles still without art."""
    from PIL import Image
    cache = cache or os.environ.get('FAMITSU_CACHE') or os.path.join('/tmp', 'famitsu-art')
    os.makedirs(cache, exist_ok=True)
    art = load_art()
    js = jobs()
    for j in js:
        learn(j, art)
    want = {key(r['title'], r['plat']): (r['title'], r['plat']) for r in (js[0]['rows'] if js else [])}
    cutoff = (dt.date.today() - dt.timedelta(days=21)).isoformat()
    for k, e in art.items():
        if ' | ' in k and str(e.get('seen_iso', '')) >= cutoff:
            want.setdefault(k, (e['title'], k.split(' | ')[1]))
    ok, lost = 0, []
    for k, (title, plat) in sorted(want.items()):
        e = art.get(k)
        good = bool(e)
        for item in ([e['shot']] + ([e['art']] if e.get('art') else [])) if e else []:
            dst = os.path.join(cache, item['file'])
            src = item.get('url') or ('https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/' + item['repo']
                                      if item.get('repo') else None)
            if not src:
                good = False
                continue
            subprocess.run(['curl', '-sL', '-m', '60', '-o', dst, src], capture_output=True)
            try:
                Image.open(dst).verify()
                ok += 1
            except Exception:  # noqa: BLE001
                good = False
        if not good:
            found = nintendo_lookup(title.replace('\n', ' '), plat)
            if found:
                art[k] = found
                print(f'famitsu_weekly: prep: {k}: new art from {found["source"]}', flush=True)
            else:
                lost.append(k)
    save_art(art)
    print(f'famitsu_weekly: prep: {ok} images open for {len(want)} likely titles; without art: {lost or "none"}',
          flush=True)
    return lost


def latest_article():
    """(url, title) of the newest weekly chart article on Famitsu's new-article list, or (None, None)."""
    for page in (1, 2, 3):
        t = html.unescape(_get(LIST % page))
        for m in re.finditer(r'href="(/article/\d{6}/\d+)"[^>]*>(.{0,400}?)</a>', t, re.S):
            text = re.sub(r'<[^>]+>', '', m.group(2))
            if MARK in text:
                return 'https://www.famitsu.com' + m.group(1), text.strip()
    return None, None


def article_id(url):
    m = re.search(r'/article/(\d{6})/(\d+)', url or '')
    return int(m.group(1) + m.group(2).zfill(7)) if m else 0


def watch(minutes=360, every=90):
    """Poll until a chart article newer than the last job's appears; print its URL (GITHUB_OUTPUT too)."""
    js = jobs()
    last = max([article_id(j.get('article', '')) for j in js] + [0])
    end = time.time() + minutes * 60
    while time.time() < end:
        url, title = latest_article()
        if url and article_id(url) > last:
            print(f'famitsu_weekly: watch: up: {url} {title}', flush=True)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f'url={url}\n')
            return url
        time.sleep(every)
    print('famitsu_weekly: watch: no new chart article in the window', flush=True)
    return None


def build(url):
    period, nxt, software, hardware = F.parse(F.fetch(url))
    if not period or not software:
        raise SystemExit(f'famitsu_weekly: {url} did not parse as a weekly chart')
    y, m1, d1, m2, d2 = map(int, period.groups())
    js = jobs()
    prev = js[0] if js else None
    art = load_art()
    for j in js:
        learn(j, art)
    missing, rows, footage = [], [], {}
    for r in software:
        if r['jp'] not in F.TITLES:
            missing.append({'rank': r['rank'], 'jp': r['jp'], 'need': 'English title in famitsu.TITLES'})
            continue
        title = F.TITLES[r['jp']]
        e = art.get(key(title, r['plat'])) or art.get(key(title)) or nintendo_lookup(title, r['plat'])
        if not e:
            missing.append({'rank': r['rank'], 'title': title, 'plat': r['plat'], 'need': 'official screenshot'})
            continue
        art.setdefault(key(title, r['plat']), e)
        row = dict(rank=r['rank'], title=wrap(title),
                   plat=r['plat'], week=r['week'], life=r['life'], new=r['new'], shot=[e['shot']['file'], e['pan']])
        if r.get('was'):
            row['was'] = r['was']
        if r['rank'] == 1 and e.get('art'):
            row['art'] = e['art']['file']
            footage[e['art']['file']] = e['art']
        footage[e['shot']['file']] = e['shot']
        rows.append(row)
    fams = F.families(hardware)
    lastw = {h['name']: h['week'] for h in (prev or {}).get('hardware', [])}
    hw = [dict(name=n, week=w, life=sum(m[2] for m in models), last=lastw.get(n, w)) for n, w, models in fams]
    stem = f'famitsu-{MONTHS[m1 - 1]}{d1}-{d2}-sales' if m1 == m2 else \
        f'famitsu-{MONTHS[m1 - 1]}{d1}-{MONTHS[m2 - 1]}{d2}-sales'
    today = dt.datetime.now(dt.timezone.utc)
    chart = dict(url=url, period=period.group(0), rows=rows, hardware=hw, missing=missing, at=today.isoformat())
    if missing:
        json.dump(chart, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('famitsu_weekly: build stopped, missing: ' + json.dumps(missing, ensure_ascii=False), flush=True)
        return None
    new = [r for r in rows if r['new']]
    if rows[0]['new']:
        hook = f'تصدّرت {rows[0]["title"].split(chr(10))[0]} مبيعات اليابان'
    elif len(new) >= 2:
        hook = f'{AR_COUNT[len(new)]} في قائمة اليابان'
    else:
        hook = 'قائمة مبيعات اليابان هذا الأسبوع'
    span = (f'{d1} إلى {d2} {AR_MONTHS[m2 - 1]}' if m1 == m2 else
            f'{d1} {AR_MONTHS[m1 - 1]} إلى {d2} {AR_MONTHS[m2 - 1]}')
    low = [r['title'].replace('\n', ' ') for r in rows if 'nintendo' in footage[r['shot'][0]].get('url', '') and
           footage[r['shot'][0]].get('w', 1920) < 1920]
    job = dict(name=stem, out=f'cards/{y}-{m2:02d}/{stem}-reel-v1.mp4', kind='famitsu',
               week_label=f'أسبوع {span} {y}', date=today.strftime('%-d %b %Y'), hook=hook,
               article=url, article_id=article_id(url), previous=(prev or {}).get('article'),
               lowres_ok={'searched': ['Nintendo US store', 'publisher press site'],
                          'result': 'some screenshots exist at 1280x720 only (server weekly build)'},
               note=f'Famitsu {span} {y} ({url}); built by famitsu_weekly on the server', story=f'{today:%Y-%m-%d}-{stem}',
               built_by='famitsu-weekly', footage=list(footage.values()), rows=rows, hardware=hw)
    path = os.path.join(ROOT, 'jobs', 'render', stem + '.json')
    json.dump(job, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    remember(job)
    save_art(art)
    if os.path.exists(PENDING):
        os.remove(PENDING)
    print(f'famitsu_weekly: job written: {os.path.relpath(path, ROOT)} ({len(rows)} rows, hook «{hook}»)', flush=True)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'job={os.path.relpath(path, ROOT)}\n')
    return path


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    if argv[0] == 'prep':
        prep()
    elif argv[0] == 'watch':
        return 0 if watch(int(argv[1]) if len(argv) > 1 else 360) else 3
    elif argv[0] == 'until':          # minutes from now to a UTC HH:MM today, at most 340 (a hosted job's limit)
        h, m = map(int, argv[1].split(':'))
        now = dt.datetime.now(dt.timezone.utc)
        end = now.replace(hour=h, minute=m, second=0, microsecond=0)
        print(max(1, min(340, int((end - now).total_seconds() // 60))))
    elif argv[0] == 'build':
        return 0 if build(argv[1]) else 2
    elif argv[0] == 'remember':
        remember(json.load(open(argv[1], encoding='utf-8')))
        print(f'famitsu_weekly: remembered {argv[1]}')
    elif argv[0] == 'learn':
        art = load_art()
        for j in jobs():
            learn(j, art)
        save_art(art)
        print(f'famitsu_weekly: {len(art)} library keys')
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
