"""Acquisition for prepared assets: find the best official copy of a trailer, in the agreed order, and record where
it came from and on what terms.

Order (adv-20261029-server-handover, phase 1; a rule, not a preference):
  1 publisher_file   a file the publisher issued itself: an MP4 linked from its own release or news page, on its
                     own host (or a generic CDN the publisher's own page links). Ubisoft and SEGA publish real MP4s.
  2 press_asset      a public press-asset site the publisher runs (Square Enix press hubs), one level from the page.
  3 steam            Steam store data: each trailer is a streaming manifest ffmpeg reads with no login.
  4 live_feed        an authorised live feed (Twitch via streamlink). Stub: refuses; live shows are the
                     event-capture service's job (ops/backoffice/event-capture) until it is wired here.
  5 youtube          bounded fallback: one attempt, no retry loops, never cookies. Stub: refuses until Mohammad
                     answers the 28 Sep rule (YouTube asks for a sign-in; media toolbox E2).

Nothing here logs in, sends cookies or uses a third-party downloader. Every candidate carries its rights record
(rights.yaml, mirrored in ops/rights-register.md) and the embargo and music notes found on its page.
"""
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (X11; Linux x86_64) dxb-prepare/1 (official trailers for news coverage)'
PAGE_MAX = 3 * 1024 * 1024          # bytes read of any HTML page
MAX_MB = int(os.environ.get('PREPARE_MAX_MB') or 2000)    # largest single file fetched
MAX_SECS = int(os.environ.get('PREPARE_MAX_SECS') or 600)  # longest stretch kept from a stream (Steam)
VIDEO_EXT = ('.mp4', '.mov', '.m4v')
STEPS = {1: 'publisher_file', 2: 'press_asset', 3: 'steam', 4: 'live_feed', 5: 'youtube'}
YOUTUBE = ('youtube.com', 'youtu.be', 'youtube-nocookie.com')
TWITCH = ('twitch.tv',)
NO_PAGE = YOUTUBE + TWITCH + ('x.com', 'twitter.com')    # pages not read (login walls, consent pages)


class Refused(Exception):
    """A step that cannot or may not run; the reason is recorded and the next step is tried."""


# ------------------------------------------------------------------ http (tests replace these)

def http_get(url, max_bytes=PAGE_MAX, timeout=30):
    """(final url, content type, body bytes) of a plain GET with no cookies."""
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.headers.get('Content-Type', ''), r.read(max_bytes)


def http_stream(url, dst, max_bytes, timeout=60):
    """Stream `url` to `dst`; returns (bytes, content type). Refuses HTML and anything past max_bytes."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get('Content-Type', '')
        if 'html' in ctype or 'text/' in ctype:
            raise Refused(f'not a video file ({ctype})')
        size = int(r.headers.get('Content-Length') or 0)
        if size > max_bytes:
            raise Refused(f'file is {size / 1e6:.0f} MB, over the {max_bytes / 1e6:.0f} MB cap')
        n = 0
        with open(dst + '.part', 'wb') as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                n += len(b)
                if n > max_bytes:
                    raise Refused(f'file passed the {max_bytes / 1e6:.0f} MB cap while downloading')
                f.write(b)
    os.replace(dst + '.part', dst)
    return n, ctype


def ffmpeg_copy(src, dst, secs=MAX_SECS):
    """Copy a stream (Steam's HLS manifest) to an mp4 without re-encoding, at most `secs` seconds."""
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-t', str(secs), '-c', 'copy',
                        '-movflags', '+faststart', dst + '.part.mp4'], capture_output=True, text=True, timeout=900)
    if p.returncode:
        raise Refused('ffmpeg could not read the stream: ' + (p.stderr or '').strip()[:200])
    os.replace(dst + '.part.mp4', dst)
    return os.path.getsize(dst)


# ------------------------------------------------------------------ rights

def load_rights(path=None):
    import yaml
    with open(path or os.path.join(HERE, 'rights.yaml'), encoding='utf-8') as f:
        return yaml.safe_load(f)


def host_of(url):
    return (urllib.parse.urlsplit(url).hostname or '').lower()


def suffix_match(host, suffixes):
    host = (host or '').lower()
    return any(host == s or host.endswith('.' + s) for s in (x.lower() for x in suffixes or ()))


def publisher_for_host(rights, host, press=False):
    for key, p in rights['publishers'].items():
        if suffix_match(host, p.get('press_hosts' if press else 'hosts')):
            return key
    return None


def publisher_for_steam(rights, names):
    low = {n.strip().lower() for n in names or ()}
    for key, p in rights['publishers'].items():
        if low & {n.lower() for n in p.get('steam_names') or ()}:
            return key
    return None


def rights_record(rights, key, steam_publishers=None):
    """What the manifest carries about the terms. Unknown publisher: basis unreviewed, flagged for review."""
    if key and key in rights['publishers']:
        p = rights['publishers'][key]
        rec = {'publisher': p['name'], 'register_key': key, 'basis': p['basis'], 'terms': p['terms'],
               'excerpt_only': bool(p.get('excerpt_only')), 'on_screen_credit': bool(p.get('on_screen_credit', True)),
               'music_flag': p.get('music_flag'), 'credit': f"{p['name']} (official trailer)",
               'rights_review': p['basis'] == 'unreviewed'}
    else:
        who = ', '.join(steam_publishers or []) or 'unknown publisher'
        rec = {'publisher': who, 'register_key': None, 'basis': 'unreviewed',
               'terms': 'No entry in ops/rights-register.md: credit the publisher on screen, editorial excerpt only, '
                        'review before use.', 'excerpt_only': True, 'on_screen_credit': True, 'music_flag': None,
               'credit': f'{who} (official trailer)', 'rights_review': True}
    rec['register'] = 'ops/rights-register.md'
    return rec


# ------------------------------------------------------------------ page reading

_HREF = re.compile(r'''(?:href|src|content|data-src|data-video|data-mp4)\s*=\s*["']([^"'<>]+)["']''', re.I)
_BARE = re.compile(r'''https?://[^\s"'<>()]+''', re.I)
_STEAM = re.compile(r'store\.steampowered\.com/app/(\d+)', re.I)
_EMBARGO = re.compile(r'[^.\n]{0,80}\bembargo(?:ed)?\b[^.\n]{0,120}', re.I)
_MUSIC = re.compile(r'[^.\n]{0,80}\b(?:music|soundtrack|song)\b[^.\n]{0,40}\b(?:not (?:be )?(?:cleared|licensed|used)|'
                    r'restricted|may not|must not|licen[cs]ed|rights?)\b[^.\n]{0,80}', re.I)


def links(html, base):
    """Absolute http(s) links from attributes and bare text, in page order, without duplicates."""
    out, seen = [], set()
    text = htmllib.unescape(html)
    for m in list(_HREF.finditer(text)) + list(_BARE.finditer(text)):
        raw = m.group(1) if m.re is _HREF else m.group(0)
        u = urllib.parse.urljoin(base, raw.strip().replace('\\/', '/'))
        if u.startswith(('http://', 'https://')) and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def is_video_url(u):
    return urllib.parse.urlsplit(u).path.lower().endswith(VIDEO_EXT)


def steam_appids(*texts):
    ids = []
    for t in texts:
        for m in _STEAM.finditer(t or ''):
            if int(m.group(1)) not in ids:
                ids.append(int(m.group(1)))
    return ids


def page_notes(text):
    """Embargo and music sentences found on a page, for a person to read (not a decision)."""
    t = re.sub(r'<[^>]+>', ' ', text or '')
    t = re.sub(r'\s+', ' ', htmllib.unescape(t))
    emb = _EMBARGO.search(t)
    mus = _MUSIC.search(t)
    return {'embargo': emb.group(0).strip()[:240] if emb else None,
            'music': mus.group(0).strip()[:240] if mus else None}


def accept_publisher_file(rights, file_url, page_url):
    """The publisher key when `file_url` counts as publisher-issued from `page_url`, else None."""
    fh, ph = host_of(file_url), host_of(page_url) if page_url else ''
    key = publisher_for_host(rights, fh)
    if key:
        return key
    page_key = publisher_for_host(rights, ph)
    if page_key and suffix_match(fh, rights.get('cdn_suffixes')):
        return page_key
    return None


# ------------------------------------------------------------------ Steam (store data, no login)

def steam_app(appid, http=None):
    http = http or http_get
    _, _, body = http(f'https://store.steampowered.com/api/appdetails?appids={int(appid)}&cc=us&l=en')
    d = json.loads(body)
    data = (next(iter(d.values())) or {}).get('data') or {}
    movies = []
    for m in data.get('movies') or []:
        hls = m.get('hls_h264') or (m.get('mp4') or {}).get('max')
        if hls:
            movies.append({'id': int(m.get('id') or 0), 'name': (m.get('name') or '').strip(), 'hls': hls,
                           'highlight': bool(m.get('highlight'))})
    return {'appid': int(appid), 'name': data.get('name') or '', 'publishers': data.get('publishers') or [],
            'movies': movies}


def _norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def steam_search(title, http=None):
    """An appid whose store name is exactly the game name at the head of the title (one search, no guessing)."""
    http = http or http_get
    head = re.split(r'\s[-|–—]\s|\s\|\s|:\s(?=(?:official|launch|gameplay|reveal|announce|story|release)\b)', title or '',
                    flags=re.I)[0]
    term = _norm(head)
    if len(term) < 4:
        return None
    _, _, body = http('https://store.steampowered.com/api/storesearch/?term=' + urllib.parse.quote(term)
                      + '&l=english&cc=US')
    for it in (json.loads(body).get('items') or [])[:5]:
        n = _norm(it.get('name'))
        if n and len(n) >= 4 and n == term:      # the whole game name, exactly: "Kitsune" never matches "Kitsune: The..."
            return int(it['id'])
    return None


def choose_movie(movies, title):
    """The trailer whose name shares most words with the item's title; ties go to the newest (highest id)."""
    if not movies:
        return None, 0.0
    want = set(_norm(title).split()) - {'the', 'a', 'of', 'and', 'trailer', 'official'}
    best, score = None, -1.0
    for m in movies:
        have = set(_norm(m['name']).split())
        s = len(want & have) / max(1, len(have)) if want else 0.0
        if s > score or (s == score and m['id'] > best['id']):
            best, score = m, s
    return best, round(score, 2)


# ------------------------------------------------------------------ planning

def plan(item, rights, http=None, steam_lookup=True):
    """Ordered candidates for one watch item or hand request: [{'step', 'method', ...}], plus notes.
    item: {'url', 'title', 'summary', 'media': [{'type', 'url'}]}. Reads the item's page once (and at most three
    press pages linked from it); never reads YouTube, Twitch or X pages."""
    http = http or http_get
    url = item.get('url') or ''
    notes, cands, page_html, page_url = [], [], '', url
    if url.startswith(('http://', 'https://')) and not suffix_match(host_of(url), NO_PAGE) and not is_video_url(url):
        try:
            page_url, ctype, body = http(url)
            page_html = body.decode('utf-8', 'replace') if 'html' in ctype or 'xml' in ctype or not ctype else ''
        except Exception as e:  # noqa: BLE001 (a page that cannot be read is a note, not a failure)
            notes.append(f'page not read: {type(e).__name__}: {str(e)[:120]}')
    pn = page_notes(page_html + ' ' + (item.get('summary') or ''))
    found = [m['url'] for m in item.get('media') or [] if m.get('url')]
    if is_video_url(url):
        found.insert(0, url)
    found += links(page_html, page_url) if page_html else []
    found += _BARE.findall(item.get('summary') or '')

    # 1. publisher-issued file
    for u in found:
        if is_video_url(u):
            key = accept_publisher_file(rights, u, page_url if page_html else url)
            if key:
                cands.append({'step': 1, 'method': STEPS[1], 'url': u, 'page': page_url, 'publisher': key})
            else:
                notes.append(f'video link not taken (host {host_of(u)} is no publisher in rights.yaml)')
    # 2. public press asset, one level from the page
    press = [u for u in dict.fromkeys(found) if publisher_for_host(rights, host_of(u), press=True)]
    if publisher_for_host(rights, host_of(url), press=True) and url not in press:
        press.insert(0, url)
    for pu in press[:3]:
        key = publisher_for_host(rights, host_of(pu), press=True)
        if is_video_url(pu):
            cands.append({'step': 2, 'method': STEPS[2], 'url': pu, 'page': page_url, 'publisher': key})
            continue
        try:
            fu, ctype, body = http(pu)
            ph = body.decode('utf-8', 'replace')
            for v in links(ph, fu):
                if is_video_url(v) and (publisher_for_host(rights, host_of(v), press=True)
                                        or publisher_for_host(rights, host_of(v)) == key
                                        or suffix_match(host_of(v), rights.get('cdn_suffixes'))):
                    cands.append({'step': 2, 'method': STEPS[2], 'url': v, 'page': fu, 'publisher': key})
            pn2 = page_notes(ph)
            pn = {k: pn[k] or pn2[k] for k in pn}
        except Exception as e:  # noqa: BLE001
            notes.append(f'press page not read: {host_of(pu)}: {type(e).__name__}')
    # 3. Steam store data
    ids = steam_appids(url, page_html, item.get('summary') or '', ' '.join(found))
    if not ids and steam_lookup:
        try:
            a = steam_search(item.get('title') or '', http)
            if a:
                ids = [a]
                notes.append(f'steam app {a} found by title search')
        except Exception as e:  # noqa: BLE001
            notes.append(f'steam search failed: {type(e).__name__}')
    for a in ids[:2]:
        cands.append({'step': 3, 'method': STEPS[3], 'appid': a, 'page': f'https://store.steampowered.com/app/{a}/'})
    # 4 and 5: recorded so the refusal is visible
    for u in [url] + found:
        if suffix_match(host_of(u), TWITCH):
            cands.append({'step': 4, 'method': STEPS[4], 'url': u, 'page': u})
            break
    for u in [url] + found:
        if suffix_match(host_of(u), YOUTUBE):
            cands.append({'step': 5, 'method': STEPS[5], 'url': u, 'page': u})
            break
    # dedup (same step and url), keep order by step
    seen, out = set(), []
    for c in sorted(cands, key=lambda c: c['step']):
        k = (c['step'], c.get('url') or c.get('appid'))
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out, notes, pn


# ------------------------------------------------------------------ fetching

def stream_id(hls):
    """The number render_job.py matches as trailer_id: the folder after the appid in the stream's path
    (.../store_trailers/<appid>/<id>/...), which is not always the movie id of the store data."""
    m = re.search(r'/store_trailers/\d+/(\d+)/', hls or '') or re.search(r'/steam/apps/(\d+)/', hls or '')
    return int(m.group(1)) if m else None


def resolve(cand, item_title='', http=None):
    """Step 3 only: read the Steam app once and choose the trailer, so the exact stream is known (and a file
    already prepared from it is found) before anything is downloaded. Sets cand['url'] to the stream."""
    if cand['step'] != 3 or 'movie' in cand:
        return cand
    app = steam_app(cand['appid'], http)
    mv, score = choose_movie(app['movies'], item_title)
    if not mv:
        raise Refused(f"steam app {cand['appid']} lists no trailers")
    cand.update(app=app, movie=mv, name_match=score, url=mv['hls'])
    return cand


def fetch(cand, dst, rights, item_title='', http=None, max_mb=None):
    """Fetch one candidate to `dst`; returns the source record for the manifest. Raises Refused."""
    step = cand['step']
    max_bytes = int((max_mb or MAX_MB) * 1e6)
    if step == 4:
        raise Refused('live feed (Twitch via streamlink) is not wired into prepare yet; live shows go through '
                      'ops/backoffice/event-capture')
    if step == 5:
        raise Refused('YouTube fallback is off: one attempt, no cookies, only after Mohammad answers the 28 Sep rule '
                      '(media toolbox E2)')
    if step in (1, 2):
        n, ctype = http_stream(cand['url'], dst, max_bytes)
        rec = rights_record(rights, cand.get('publisher'))
        return {'step': step, 'method': cand['method'], 'url': cand['url'], 'page': cand.get('page'),
                'bytes': n, 'content_type': ctype}, rec
    if step == 3:
        resolve(cand, item_title, http)
        app, mv, score = cand['app'], cand['movie'], cand['name_match']
        n = ffmpeg_copy(mv['hls'], dst)
        key = publisher_for_steam(rights, app['publishers'])
        rec = rights_record(rights, key, app['publishers'])
        return {'step': 3, 'method': 'steam', 'url': mv['hls'], 'page': cand['page'], 'bytes': n,
                'steam': {'appid': app['appid'], 'game': app['name'], 'movie_id': mv['id'], 'trailer': mv['name'],
                          'name_match': score, 'trailers_listed': len(app['movies']),
                          'item_trailer': 'likely' if score >= 0.5 else
                          'unknown: a Steam trailer of the same game, maybe not the one the item announced',
                          'render_job_footage': {'steam': app['appid'], 'trailer': mv['name'],
                                                 'trailer_id': stream_id(mv['hls']) or mv['id']}}}, rec
    raise Refused(f'unknown step {step}')


def ffmpeg_available():
    return shutil.which('ffmpeg') is not None
