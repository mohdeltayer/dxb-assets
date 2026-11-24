#!/usr/bin/env python3
"""Quick posts: split by platform (Mohammad, 24 Nov 2026).

X and Threads get a fast news post: an image card made in seconds with templates/fast_ar.py (the story's official key art
or screenshot full bleed, our chip, our footer, Dubai type, no other outlet's logo) and a short Arabic text (one or two
lines, the source named; no hashtags on X; on Threads the source line). Instagram (and later TikTok and YouTube) get the
Reels. When the story's Reel is ready it goes to Instagram as before and to X and Threads as its own post, at least
REEL_AFTER_H hours after the quick post, with its own text that leads with what the video shows (story texts reel_x and
reel_threads); a quick post older than REEL_MAX_H hours keeps the Reel off X and Threads (serverpost.reel_networks).

Picture, in order (the first that is an official image wins; a card never carries another outlet's logo or watermark):
  1. story "art": an official image URL the editor names (press kit, store page, publisher's post);
  2. the Steam store page's screenshots, then its header, when the footage is steam:<appid>;
  3. a frame of the job's first footage shot (the official trailer the Reel is cut from), 0.6 s into the shot;
  4. the first screenshot on a Nintendo, PlayStation or Xbox store page named as a source.
Text: texts quick_x / quick_threads when the editor wrote them, else the story's x / threads texts (the short news texts;
hashtags are stripped on X). Chip: the story's label on the fast ladder (fast_ar.PICKS), عاجل on T0.

    python3 templates/quickpost.py render <story id> <out.jpg> [--json out.json]   card and texts (needs the Dubai font)
    python3 templates/quickpost.py plan <story id>                                 what it would use, no render
Rows: newsroom/quickpost.jsonl (state rendered, ready, scheduled, skipped), read by serverpost.quick_sweep.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
STORIES = os.path.join(REPO, 'newsroom', 'stories')
LEDGER = os.path.join(REPO, 'newsroom', 'quickpost.jsonl')
UA = 'Mozilla/5.0 (X11; Linux x86_64) dxb-quickpost'
RAW = 'https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/'
REEL_AFTER_H = 2
REEL_MAX_H = 24
GENRE_THEME = {'rpg': 'stylized', 'fantasy': 'stylized', 'anime': 'stylized', 'jrpg': 'stylized',
               'family': 'playful', 'sports': 'playful', 'racing': 'playful', 'fighting': 'playful', 'mobile': 'playful',
               'open world': 'spectacle', 'shooter': 'spectacle', 'action': 'spectacle', 'adventure': 'spectacle',
               'industry/hardware': 'cold', 'horror': 'cold', 'strategy/sim': 'emerald', 'indie': 'emerald',
               'live service/mmo': 'stylized', 'regional/esports': 'emerald'}


def load(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def story_of(sid):
    return load(os.path.join(STORIES, sid + '.json'), None)


def base_of(sid):
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', sid)


def job_of(sid):
    b = base_of(sid)
    for d in ('live', 'done', 'render'):
        j = load(os.path.join(REPO, 'jobs', d, b + '.json'))
        if isinstance(j, dict):
            return j
    return {}


def tier0(story, job):
    sl = story.get('slip') or {}
    return str(sl.get('tier', job.get('tier', ''))).upper() in ('0', 'T0') or job.get('priority') is True or \
        job.get('profile') == 'breaking' or story.get('label') == 'عاجل'


def chip(story, job):
    import fast_ar as FA
    if tier0(story, job) and story.get('label') in ('رسمي', 'جديد', 'عاجل'):
        return 'عاجل'
    lab = story.get('label') or story.get('chip') or 'جديد'
    return lab if lab in FA.PICKS + FA.EVERGREEN else 'جديد'


def theme(story, label):
    if label == 'عاجل':
        return 'crimson'
    g = story.get('genre')
    g = (g[0] if isinstance(g, list) and g else g) or ''
    return GENRE_THEME.get(str(g).lower(), 'cold')


def source_name(story, job):
    """The outlet or company the card's footer names: the job's credit after «المصدر:», else the primary source name."""
    for c in job.get('credits') or []:
        txt = c[2] if isinstance(c, list) and len(c) > 2 else (c if isinstance(c, str) else '')
        m = re.search(r'المصدر:\s*([^·،\n]+)', str(txt))
        if m:
            return m.group(1).strip()
    if job.get('source'):
        return re.split(r'[·،\n]', str(job['source']))[0].strip()
    for s in story.get('sources') or []:
        if s.get('role') == 'primary' and s.get('name'):
            return re.split(r'[,،(]', s['name'])[0].strip()
    return 'ديجيتال لاونج'


def date_en(now=None):
    return (now or dt.datetime.now(dt.timezone.utc)).strftime('%-d %b %Y')


def texts(story):
    t = story.get('texts') or {}
    x = t.get('quick_x') or t.get('x') or ''
    x = re.sub(r'\s*#\S+', '', x).strip()                 # no hashtags on X (28 Sep 2026)
    th = t.get('quick_threads') or t.get('threads') or ''
    if th and 'المصدر' not in th:
        th = th.rstrip() + '\n\nالمصدر: ' + source_name(story, {})
    return {'x': x, 'threads': th}


def _get(url, path, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(path, 'wb') as f:
        f.write(r.read())
    return path


def _steam_app(story, job):
    for it in job.get('footage') or []:
        m = re.search(r'steam(?:static|powered)?[^0-9]*/(?:apps|app|steam/apps)/(\d+)', str(it.get('url') or ''))
        if m:
            return m.group(1)
    m = re.search(r'steam:(\d+)', json.dumps(story.get('footage'), ensure_ascii=False) + str(job.get('footage_source') or ''))
    if m:
        return m.group(1)
    for s in story.get('sources') or []:
        m = re.search(r'store\.steampowered\.com/app/(\d+)', str(s.get('url') or ''))
        if m:
            return m.group(1)
    return None


def candidates(story, job):
    """[(kind, url_or_spec, note)] in the order of the docstring."""
    out = []
    if story.get('art'):
        out.append(('url', story['art'], 'official image named in the story'))
    app = _steam_app(story, job)
    if app:
        try:
            req = urllib.request.Request(f'https://store.steampowered.com/api/appdetails?appids={app}&cc=ae&filters=screenshots,basic',
                                         headers={'User-Agent': UA})
            d = json.load(urllib.request.urlopen(req, timeout=30)).get(app, {}).get('data') or {}
            for s in (d.get('screenshots') or [])[:3]:
                out.append(('url', s.get('path_full'), f'Steam screenshot (app {app})'))
            if d.get('header_image'):
                out.append(('url', d['header_image'], f'Steam header (app {app})'))
        except Exception as e:                          # noqa: BLE001
            print(f'quickpost: Steam {app} not read ({e})')
    shots = [s for s in job.get('shots') or [] if isinstance(s, list) and len(s) > 2 and isinstance(s[1], (int, float))]
    feet = {it.get('file'): it for it in job.get('footage') or [] if it.get('file')}
    for s in shots[:2]:
        it = feet.get(s[0]) or {}
        src = it.get('url') or (RAW + it['repo'] if it.get('repo') else None)   # a committed official copy (public repo)
        if src and not str(src).endswith(('.png', '.jpg', '.webp')):
            out.append(('frame', (src, float(s[1]) + 0.6), f'frame of the official trailer at {float(s[1]) + 0.6:.1f} s'))
    return out


def fetch_image(story, job, tmp):
    from PIL import Image
    for kind, spec, note in candidates(story, job):
        try:
            p = os.path.join(tmp, 'art')
            if kind == 'url':
                _get(spec, p + '.src')
            else:
                url, at = spec
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{at:.2f}', '-i', url, '-frames:v', '1',
                                p + '.src.png'], check=True, timeout=120)
                os.replace(p + '.src.png', p + '.src')
            im = Image.open(p + '.src').convert('RGB')
            if im.width < 900 or im.height < 500:
                print(f'quickpost: {note}: {im.width}x{im.height} too small')
                continue
            im.save(p + '.jpg', quality=94)
            return p + '.jpg', note
        except Exception as e:                          # noqa: BLE001
            print(f'quickpost: {note}: not used ({e})')
    raise RuntimeError('no official image found (story art, Steam, a trailer frame); add "art" to the story file')


def render(sid, out, now=None):
    import fast_ar as FA
    story = story_of(sid)
    if not isinstance(story, dict):
        raise SystemExit(f'quickpost: no story file newsroom/stories/{sid}.json')
    job = job_of(sid)
    tmp = tempfile.mkdtemp(prefix='quick-')
    img, note = fetch_image(story, job, tmp)
    lab = chip(story, job)
    th = theme(story, lab)
    src = source_name(story, job)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    FA.fast_ar(img, date_en(now), src, out, label=lab, theme=th)
    return {'story': sid, 'base': base_of(sid), 'card': out, 'image': note, 'chip': lab, 'theme': th, 'source': src,
            'texts': texts(story), 't0': tier0(story, job)}


def plan(sid):
    story = story_of(sid) or {}
    job = job_of(sid)
    return {'story': sid, 'chip': chip(story, job), 'source': source_name(story, job), 'texts': texts(story),
            't0': tier0(story, job), 'images': [n for _, _, n in candidates(story, job)]}


def main(argv):
    if len(argv) >= 3 and argv[0] == 'render':
        r = render(argv[1], argv[2])
        if '--json' in argv:
            json.dump(r, open(argv[argv.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('QUICK_JSON: ' + json.dumps(r, ensure_ascii=False))
        return 0
    if len(argv) >= 2 and argv[0] == 'plan':
        print(json.dumps(plan(argv[1]), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
