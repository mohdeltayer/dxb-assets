#!/usr/bin/env python3
"""Prepared trailers (back office service 4, phase 1 INTAKE of adv-20261029-server-handover). A script, not an
agent: for every watch item above the threshold it fetches the best official copy of the trailer, runs the source
checks once, maps the shots, faces, subjects and burnt-in text, and stores the result with its rights record, so a
render later starts from a checked file and a shot map instead of a download.

    prepare.py one <steam appid | url> --name N [--title T] [--force]   prepare one source by hand
    prepare.py one <local file> --name N --rights <key> [--page P]      a file Mohammad or a publisher sent
    prepare.py from-watch [--max N] [--dry-run]                         items above the threshold from the watch
    prepare.py handover [--force]                                       index and sheets to dxb-watch, branch prepared
    prepare.py cleanup [--dry-run]                                      7-day expiry and the 40 GB disk floor
    prepare.py status                                                   store, ledger, models, tools, disk
    prepare.py list [--all]                                             prepared assets, newest first
    prepare.py show <key>                                               one manifest, summarised
    prepare.py models                                                   fetch YuNet and NanoDet (official, sha256)
    prepare.py beats [file|dir ...]                                     beat grid per music bed, cached

Environment (all optional): PREPARE_HOME (~/backoffice/prepare), PREPARE_STORE (default
/var/cache/dxb-render/prepared when writable), PREPARE_MODELS, PREPARE_WATCH_DB (~/backoffice/watch/watch.db),
PREPARE_WATCH_DIGEST (~/backoffice/watch/out/digest.json), PREPARE_MIN_SCORE (4), PREPARE_MAX_ITEMS (2 a tick),
PREPARE_WINDOW_H (24), PREPARE_KEEP_DAYS (7), PREPARE_FLOOR_GB (40), PREPARE_MAX_STORE_GB (80),
PREPARE_RENDER_CHECK=off, PREPARE_BUSY_PATTERN, PREPARE_PAUSE_WAIT (600 s), PREPARE_STEAM_SEARCH=off,
PREPARE_SPLIT=on (with COCKTAIL_DIR), PREPARE_BEDS (extra bed folders, colon separated), PREPARE_HANDOFF=off (the
hand-over writes ~/backoffice/prepare/handover/out only), PREPARE_HANDOFF_BRANCH (prepared).
Exit codes: 0 done or nothing to do, 1 failure, 75 paused for a render or held by the disk floor.
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import resource
import shutil
import sqlite3
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import acquire as AQ   # noqa: E402
import analyse as AN   # noqa: E402
import handover as HO   # noqa: E402

PAUSED = 75
HOME = os.environ.get('PREPARE_HOME') or os.path.expanduser('~/backoffice/prepare')
BUSY = os.environ.get('PREPARE_BUSY_PATTERN') or r'render_job\.py|Runner\.Worker'
OFFICIAL_KINDS = {'official', 'youtube', 'x', 'page'}       # first-party sources of the watch (not outlet, not gnews)
TRAILER_WORDS = re.compile(r'\b(trailer|teaser|reveal|gameplay|announce(?:ment)?|launch|first look|showcase|'
                           r'overview|PV)\b|トレーラー|ティザー|映像|PV', re.I)


def env_f(name, default):
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return float(default)


def store_dir():
    d = os.environ.get('PREPARE_STORE')
    if d:
        return d
    cache = os.environ.get('DXB_CACHE') or '/var/cache/dxb-render'
    if os.path.isdir(cache) and os.access(cache, os.W_OK):
        return os.path.join(cache, 'prepared')
    return os.path.join(HOME, 'assets')


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t=None):
    return (t or now()).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso(s):
    try:
        return dt.datetime.strptime(s[:19].rstrip('Z'), '%Y-%m-%dT%H:%M:%S').replace(tzinfo=dt.timezone.utc)
    except (ValueError, TypeError):
        try:
            return dt.datetime.strptime(s[:16], '%Y-%m-%dT%H:%M').replace(tzinfo=dt.timezone.utc)
        except (ValueError, TypeError):
            return None


def log(*a):
    print(now().strftime('%H:%M:%SZ'), *a, flush=True)


def slug(s, n=48):
    s = re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')
    return (s[:n].rstrip('-') or 'asset')


def key_for(name, ref):
    import hashlib
    return f'{slug(name)}-{hashlib.sha1(str(ref).encode()).hexdigest()[:8]}'


# ------------------------------------------------------------------ render pause

class Paused(Exception):
    pass


def render_active():
    if os.environ.get('PREPARE_RENDER_CHECK') == 'off':
        return False
    try:
        return subprocess.run(['pgrep', '-f', BUSY], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def wait_idle(max_wait=None):
    """Renders always win: while one runs, wait (15 s steps) up to PREPARE_PAUSE_WAIT, then give up the tick."""
    max_wait = env_f('PREPARE_PAUSE_WAIT', 600) if max_wait is None else max_wait
    end = time.time() + max_wait
    while render_active():
        if time.time() >= end:
            raise Paused('a render is running')
        time.sleep(min(15, max(1, end - time.time())))


@contextlib.contextmanager
def lock():
    os.makedirs(os.path.join(HOME, 'state'), exist_ok=True)
    f = open(os.path.join(HOME, 'state', 'prepare.lock'), 'w')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        yield False
        return
    try:
        yield True
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


# ------------------------------------------------------------------ ledger

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
  key TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, step INTEGER, method TEXT,
  request TEXT NOT NULL, source_url TEXT, source_page TEXT, watch_item TEXT, path TEXT, bytes INTEGER,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS assets_source ON assets(source_url);
CREATE TABLE IF NOT EXISTS seen (
  watch_item TEXT PRIMARY KEY, score INTEGER, decision TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
  asset_key TEXT, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def db():
    os.makedirs(HOME, exist_ok=True)
    c = sqlite3.connect(os.path.join(HOME, 'prepare.db'), timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def put_asset(c, **kw):
    kw.setdefault('updated_at', iso())
    cols = ','.join(kw)
    c.execute(f'INSERT INTO assets ({cols}) VALUES ({",".join("?" * len(kw))}) ON CONFLICT(key) DO UPDATE SET '
              + ','.join(f'{k}=excluded.{k}' for k in kw if k != 'key'), list(kw.values()))
    c.commit()


def set_meta(c, k, v):
    c.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', (k, v))
    c.commit()


# ------------------------------------------------------------------ disk

def free_gb(path):
    p = path
    while not os.path.exists(p):
        p = os.path.dirname(p) or '/'
    return shutil.disk_usage(p).free / 1e9


def dir_bytes(p):
    n = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                n += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return n


def asset_dirs(store):
    out = []
    if not os.path.isdir(store):
        return out
    for n in os.listdir(store):
        p = os.path.join(store, n)
        if not os.path.isdir(p):
            continue
        created = None
        mp = os.path.join(p, 'manifest.json')
        if os.path.exists(mp):
            try:
                with open(mp) as f:
                    created = parse_iso(json.load(f).get('created_at') or '')
            except (OSError, ValueError):
                pass
        if created is None:
            created = dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc)
        out.append((created, n, p))
    return sorted(out)


def cleanup(dry=False, c=None, store=None):
    """Expire assets older than PREPARE_KEEP_DAYS; drop half-written folders older than 2 h; then, oldest first,
    assets older than 1 h while free space is under PREPARE_FLOOR_GB or the store is over PREPARE_MAX_STORE_GB.
    Only touches folders inside the prepared store. Returns [(name, reason)]."""
    store = store or store_dir()
    keep = env_f('PREPARE_KEEP_DAYS', 7)
    floor = env_f('PREPARE_FLOOR_GB', 40)
    cap = env_f('PREPARE_MAX_STORE_GB', 80) * 1e9
    gone, t = [], now()
    items = asset_dirs(store)
    left = []
    for created, n, p in items:
        age_h = (t - created).total_seconds() / 3600
        if n.endswith('.partial') and age_h > 2:
            gone.append((n, 'half-written, over 2 h old'))
        elif not n.endswith('.partial') and age_h > keep * 24:
            gone.append((n, f'older than {keep:g} days'))
        else:
            left.append((created, n, p))
    removed_bytes = 0
    for n, _ in gone:
        p = os.path.join(store, n)
        removed_bytes += dir_bytes(p)
        if not dry:
            shutil.rmtree(p, ignore_errors=True)
    total = sum(dir_bytes(p) for _, _, p in left)
    free = free_gb(store) + (removed_bytes / 1e9 if dry else 0)
    for created, n, p in list(left):
        if free >= floor and total <= cap:
            break
        if n.endswith('.partial') or (t - created).total_seconds() < 3600:
            continue
        b = dir_bytes(p)
        why = f'disk floor ({free:.1f} GB free, floor {floor:g} GB)' if free < floor else \
            f'store over {cap / 1e9:g} GB'
        gone.append((n, why))
        if not dry:
            shutil.rmtree(p, ignore_errors=True)
        free += b / 1e9
        total -= b
    if c is not None and not dry:
        for n, why in gone:
            c.execute("UPDATE assets SET status='deleted', updated_at=?, detail=? WHERE key=?", (iso(), why, n))
        c.commit()
    return gone


def room_for(store, est_bytes):
    """True when fetching about est_bytes keeps free space at or above the floor."""
    return free_gb(store) - est_bytes / 1e9 >= env_f('PREPARE_FLOOR_GB', 40)


# ------------------------------------------------------------------ one asset

def tool_versions():
    v = {}
    for mod in ('cv2', 'scenedetect', 'librosa', 'numpy'):
        try:
            m = __import__(mod)
            v[mod] = getattr(m, '__version__', '?')
        except ImportError:
            v[mod] = None
    t = shutil.which('tesseract')
    if t:
        out = subprocess.run([t, '--version'], capture_output=True, text=True)
        v['tesseract'] = ((out.stdout or out.stderr).splitlines() or ['?'])[0].split()[-1]
    else:
        v['tesseract'] = None
    f = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split()
    v['ffmpeg'] = f[2] if len(f) > 2 else None
    for name in AN.MODELS:
        v[name] = AN.MODELS[name]['file'] if AN.model_path(name) else None
    return v


def prepare_item(item, name, rights, c, force=False, max_mb=None):
    """Plan, fetch and analyse one item. Returns (status, key, detail). Raises Paused."""
    t_all = time.time()
    ru0 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    store = store_dir()
    os.makedirs(store, exist_ok=True)
    request = item.get('appid') or item.get('url') or (
        f"file:{item['local']}:{os.path.getsize(item['local'])}" if item.get('local') else None)
    key = key_for(name, request)
    final = os.path.join(store, key)
    if os.path.exists(os.path.join(final, 'manifest.json')) and not force:
        return 'exists', key, 'already prepared'
    wait_idle()
    tm = {}
    t0 = time.time()
    if item.get('local'):
        cands, notes, pn = [{'step': 0, 'method': 'hand', 'path': item['local'], 'publisher': item.get('publisher'),
                             'page': item.get('page')}], ['file given by hand'], {'embargo': None, 'music': None}
    elif item.get('appid'):
        cands, notes, pn = [{'step': 3, 'method': 'steam', 'appid': int(item['appid']),
                             'page': f"https://store.steampowered.com/app/{int(item['appid'])}/"}], [], \
            {'embargo': None, 'music': None}
    else:
        cands, notes, pn = AQ.plan(item, rights, steam_lookup=os.environ.get('PREPARE_STEAM_SEARCH') != 'off')
    tm['plan'] = round(time.time() - t0, 2)
    if not cands:
        put_asset(c, key=key, name=name, status='no-source', request=str(request), created_at=iso(),
                  watch_item=item.get('watch_item'), detail='; '.join(notes)[:900] or 'no candidate found')
        return 'no-source', key, '; '.join(notes) or 'no candidate in steps 1 to 5'
    if not room_for(store, 0.6e9):
        cleanup(c=c, store=store)
        if not room_for(store, 0.6e9):
            return 'disk-floor', key, f'{free_gb(store):.1f} GB free, floor {env_f("PREPARE_FLOOR_GB", 40):g} GB'
    work = final + '.partial'
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    src = os.path.join(work, 'source.mp4')
    attempts, got = [], None
    t0 = time.time()
    for cand in cands:
        wait_idle()
        try:
            if cand['step'] == 3:
                AQ.resolve(cand, item.get('title') or name)
            dup = cand.get('url') and cand['step'] in (1, 2, 3) and c.execute(
                "SELECT key, path FROM assets WHERE source_url = ? AND status = 'ready' AND key != ?",
                (cand['url'], key)).fetchone()
            if dup and dup['path'] and os.path.exists(os.path.join(dup['path'], 'manifest.json')):
                shutil.rmtree(work, ignore_errors=True)
                return 'duplicate', dup['key'], f"same {cand['method']} file as {dup['key']}"
            if cand['step'] == 0:
                shutil.copyfile(cand['path'], src)
                got = ({'step': 0, 'method': 'hand', 'url': 'file:' + os.path.basename(cand['path']),
                        'page': cand.get('page'), 'bytes': os.path.getsize(src)},
                       AQ.rights_record(rights, cand.get('publisher')), cand)
                attempts.append({'step': 0, 'method': 'hand', 'result': 'ok', 'url': os.path.basename(cand['path'])})
                break
            got = AQ.fetch(cand, src, rights, item.get('title') or name, max_mb=max_mb) + (cand,)
            attempts.append({'step': cand['step'], 'method': cand['method'], 'result': 'ok',
                             'url': cand.get('url') or cand.get('appid')})
            break
        except AQ.Refused as e:
            attempts.append({'step': cand['step'], 'method': cand['method'], 'result': 'refused', 'reason': str(e)[:300],
                             'url': cand.get('url') or cand.get('appid')})
        except Exception as e:  # noqa: BLE001 (one source failing moves to the next)
            attempts.append({'step': cand['step'], 'method': cand['method'], 'result': 'failed',
                             'reason': f'{type(e).__name__}: {str(e)[:200]}', 'url': cand.get('url') or cand.get('appid')})
        for f in (src, src + '.part', src + '.part.mp4'):
            if os.path.exists(f):
                os.remove(f)
    tm['fetch'] = round(time.time() - t0, 2)
    if not got:
        shutil.rmtree(work, ignore_errors=True)
        why = '; '.join(f"{a['method']}: {a.get('reason')}" for a in attempts)
        status = 'refused' if all(a['result'] == 'refused' for a in attempts) else 'failed'
        put_asset(c, key=key, name=name, status=status, request=str(request), created_at=iso(),
                  watch_item=item.get('watch_item'), detail=why[:900])
        return status, key, why
    source, rights_rec, cand = got
    rights_rec = dict(rights_rec, embargo=pn.get('embargo'), page_music_note=pn.get('music'))
    man = {'version': 1, 'key': key, 'name': name, 'status': 'analysing', 'created_at': iso(),
           'request': request, 'watch': item.get('watch'), 'source': dict(source, file='source.mp4', fetched_at=iso()),
           'attempts': attempts, 'plan_notes': notes, 'rights': rights_rec}

    def step(label, fn, *a, **kw):
        wait_idle()
        t = time.time()
        try:
            return fn(*a, **kw)
        finally:
            tm[label] = round(time.time() - t, 2)

    info = step('probe', AN.probe, src)
    man['probe'] = info
    dec = step('decode', AN.decode, src)
    if not dec['clean'] and cand['step'] in (1, 2, 3):
        log(f'{key}: decode errors ({dec["errors"]}), downloading once more')
        os.remove(src)
        try:
            t = time.time()
            AQ.fetch(cand, src, rights, item.get('title') or name, max_mb=max_mb)
            tm['refetch'] = round(time.time() - t, 2)
            dec = step('decode2', AN.decode, src)
            dec['retried'] = True
        except Exception as e:  # noqa: BLE001
            dec = dict(dec, retried=True, refetch_error=str(e)[:200])
    man['checks'] = {'decode': dec}
    if not dec['clean'] or not info['video']:
        man['status'] = 'damaged' if info['video'] else 'no-video'
        if os.path.exists(src):
            os.remove(src)                       # never build shots from a damaged file; the manifest says why
        man['source']['file'] = None
    else:
        man['checks']['bitrate'] = step('bitrate', AN.DC.bitrate_flag, src)
        man['checks']['smear'] = step('smear', AN.smear, src, info['duration'], info['fps'])
        sc, notes2, tm2, frames = AN.shot_map(src, info, log=log, busy=wait_idle)
        tm.update(tm2)
        man['scenes'] = sc
        man['tools_notes'] = notes2
        man['summary'] = {
            'scenes': len(sc), 'with_faces': sum(1 for s in sc if s['faces']),
            'profile': sum(1 for s in sc if s['profile']), 'with_text': sum(1 for s in sc if s['text']),
            'cut_text': sum(1 for s in sc if s['cut_text']), 'focus_found': sum(1 for s in sc if s['focus'] is not None),
            'blocky': sum(1 for s in sc if isinstance(s['block'], dict) and s['block']['blocky']),
            'first_frame_text': sc[0]['text_on_cut_frame'] if sc else []}
        man['sheet'] = os.path.basename(step('sheet', AN.contact_sheet, os.path.join(work, 'sheet.jpg'), sc, frames,
                                             info['w']) or '') or None
        del frames
        audio = {'present': info['audio']}
        if info['audio']:
            b = step('beats', AN.beats, src, os.path.join(HOME, 'beats'))
            audio['beats'] = ({'tempo': b['tempo'], 'n': b['n'], 'file': 'beats.json'} if b else
                              'skipped: librosa not installed')
            if b:
                with open(os.path.join(work, 'beats.json'), 'w') as f:
                    json.dump(b, f)
            audio['split'] = step('split', AN.split_audio, src, work)
        man['audio'] = audio
        man['status'] = 'ready'
    man['tools'] = tool_versions()
    ru1 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = sum(b.ru_utime + b.ru_stime - a.ru_utime - a.ru_stime for a, b in zip(ru0, ru1))
    tm['total'] = round(time.time() - t_all, 2)
    man['timings'] = tm
    man['cpu_s'] = round(cpu, 1)
    man['bytes'] = dir_bytes(work)
    with open(os.path.join(work, 'manifest.json'), 'w') as f:
        json.dump(man, f, indent=1, ensure_ascii=False)
    shutil.rmtree(final, ignore_errors=True)
    os.replace(work, final)
    put_asset(c, key=key, name=name, status=man['status'], step=source['step'], method=source['method'],
              request=str(request), source_url=source['url'], source_page=source.get('page'),
              watch_item=item.get('watch_item'), path=final, bytes=man['bytes'], created_at=man['created_at'],
              detail=json.dumps(man.get('summary') or man['checks'])[:900])
    with open(os.path.join(HOME, 'timings.jsonl'), 'a') as f:      # the 2 Nov gate reads this
        f.write(json.dumps({'key': key, 'at': man['created_at'], 'status': man['status'], 'method': source['method'],
                            'source_secs': info['duration'], 'bytes': man['bytes'], 'cpu_s': man['cpu_s'],
                            'timings': tm, 'watch_item': item.get('watch_item'),
                            'watch_first_seen': (item.get('watch') or {}).get('first_seen')}) + '\n')
    return man['status'], key, f"{source['method']}, {info['w']}x{info['h']}, {info['duration']:.0f} s, " \
                               f"{len(man.get('scenes') or [])} scenes, {tm['total']:.0f} s"


# ------------------------------------------------------------------ the watch

def score(it):
    """Points and reasons for one watch item; the threshold is PREPARE_MIN_SCORE (4)."""
    pts, why = 0, []
    media = it.get('media') or []
    vids = [m['url'] for m in media if m.get('type') == 'video' and m.get('url')]
    url = it.get('url') or ''
    if AQ.suffix_match(AQ.host_of(url), AQ.YOUTUBE + AQ.TWITCH) or AQ.is_video_url(url):
        vids.append(url)
    if it.get('kind') in OFFICIAL_KINDS:
        pts += 2
        why.append('official')
    if vids:
        pts += 2
        why.append('video link')
    if TRAILER_WORDS.search(it.get('title') or ''):
        pts += 1
        why.append('trailer word')
    if AQ.steam_appids(url, it.get('summary') or ''):
        pts += 1
        why.append('steam link')
    if it.get('breaking'):
        pts += 1
        why.append('breaking source')
    if not (vids or 'trailer word' in why or 'steam link' in why):
        pts = min(pts, 1)                         # nothing that points at a video: never prepared
    return pts, why


def watch_items(window_h):
    """Recent handed-over-able items from the watch's SQLite (read-only), else its digest.json."""
    dbp = os.environ.get('PREPARE_WATCH_DB') or os.path.expanduser('~/backoffice/watch/watch.db')
    since = iso(now() - dt.timedelta(hours=window_h))
    if os.path.exists(dbp):
        c = sqlite3.connect(f'file:{dbp}?mode=ro', uri=True, timeout=30)
        c.row_factory = sqlite3.Row
        rows = c.execute('SELECT id, source, kind, title, url, published, first_seen, summary, media, breaking '
                         'FROM items WHERE baseline = 0 AND junk = 0 AND first_seen >= ? ORDER BY first_seen DESC '
                         'LIMIT 1000', (since,)).fetchall()
        c.close()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d['media'] = json.loads(d['media'] or '[]')
            except ValueError:
                d['media'] = []
            d['watch_item'] = f"watch:{d['id']}"
            out.append(d)
        return out, 'watch.db'
    dg = os.environ.get('PREPARE_WATCH_DIGEST') or os.path.expanduser('~/backoffice/watch/out/digest.json')
    if os.path.exists(dg):
        with open(dg) as f:
            j = json.load(f)
        out = []
        for it in j.get('official') or []:
            if (it.get('first_seen') or '') >= since:
                out.append({'id': it.get('id'), 'source': it.get('source'), 'kind': it.get('source_kind') or 'official',
                            'title': it.get('title'), 'url': it.get('url'), 'published': it.get('published'),
                            'first_seen': it.get('first_seen'), 'summary': it.get('summary') or '',
                            'media': it.get('media') or [], 'breaking': it.get('breaking_source'),
                            'watch_item': f"watch:{it.get('id')}"})
        return out, 'digest.json'
    return [], 'none (no watch.db or digest.json)'


def pick(items, c, min_score, limit):
    seen = {r['watch_item'] for r in c.execute('SELECT watch_item FROM seen')}
    scored = []
    for it in items:
        if it['watch_item'] in seen:
            continue
        p, why = score(it)
        if p >= min_score:
            scored.append((p, it.get('first_seen') or '', it, why))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)     # highest score first, then the newest
    return scored[:limit], len(scored)


# ------------------------------------------------------------------ commands

def cmd_one(a):
    rights = AQ.load_rights()
    ref = a.source.strip()
    if os.path.isfile(ref):
        if not a.rights:
            log('a local file needs --rights <publisher key in rights.yaml> (and --page, where it came from)')
            return 1
        item = {'local': os.path.abspath(ref), 'publisher': a.rights, 'page': a.page}
    else:
        item = {'appid': int(ref)} if ref.isdigit() else {'url': ref}
    item['title'] = a.title or a.name
    with lock() as got:
        if not got:
            log('another pass is running')
            return 1
        c = db()
        try:
            st, key, detail = prepare_item(item, a.name, rights, c, force=a.force, max_mb=a.max_mb)
        except Paused as e:
            log('paused:', e)
            return PAUSED
        log(f'{st}: {key}: {detail}')
        if st in ('ready', 'exists'):
            print(os.path.join(store_dir(), key, 'manifest.json'))
        return 0 if st in ('ready', 'exists') else (PAUSED if st == 'disk-floor' else 1)


def cmd_from_watch(a):
    min_score = int(env_f('PREPARE_MIN_SCORE', 4))
    limit = a.max if a.max is not None else int(env_f('PREPARE_MAX_ITEMS', 2))
    if not a.dry_run and render_active():
        log('a render is running: paused')
        return PAUSED
    with lock() as got:
        if not got:
            log('another pass is running, skipped')
            return 0
        c = db()
        set_meta(c, 'last_tick', iso())
        if not a.dry_run:
            for n, why in cleanup(c=c):
                log(f'cleanup: {n}: {why}')
        items, src = watch_items(env_f('PREPARE_WINDOW_H', 24))
        chosen, total = pick(items, c, min_score, limit)
        log(f'watch ({src}): {len(items)} items in the window, {total} above score {min_score}, taking {len(chosen)}')
        if a.dry_run:
            for p, _, it, why in chosen:
                log(f'  {p} [{", ".join(why)}] {it.get("source")}: {it.get("title")} {it.get("url")}')
            return 0
        rights = AQ.load_rights()
        rc = 0
        for p, _, it, why in chosen:
            name = it.get('title') or 'trailer'
            item = {'url': it.get('url'), 'title': it.get('title'), 'summary': it.get('summary'),
                    'media': it.get('media'), 'watch_item': it['watch_item'],
                    'watch': {'item': it['watch_item'], 'source': it.get('source'), 'kind': it.get('kind'),
                              'title': it.get('title'), 'url': it.get('url'), 'published': it.get('published'),
                              'first_seen': it.get('first_seen'), 'score': p, 'why': why}}
            try:
                st, key, detail = prepare_item(item, name, rights, c)
            except Paused as e:
                log('paused mid-tick:', e, '(the item is retried next tick)')
                return PAUSED
            except Exception as e:  # noqa: BLE001 (one bad item never stops the tick)
                st, key, detail = 'error', key_for(name, it.get('url')), f'{type(e).__name__}: {str(e)[:200]}'
                rc = 1
            if st == 'disk-floor':
                log('disk floor:', detail, '(nothing fetched; retried next tick)')
                return PAUSED
            c.execute('INSERT OR REPLACE INTO seen VALUES (?, ?, ?, ?, ?, ?)',
                      (it['watch_item'], p, st, detail[:500], key, iso()))
            c.commit()
            log(f'{st}: {key}: {detail}')
        try:
            n = beat_files([], quiet=True)     # beat grids of new music beds (cached, so a few seconds at most)
            if n:
                log(f'beats: {n} new bed(s)')
        except Paused:
            return PAUSED
        HO.run(c, store_dir(), HOME, iso(), log)   # index and sheets to the news desk when the store changed
        return rc


def cmd_handover(a):
    c = db()
    res = HO.run(c, store_dir(), HOME, iso(), log, force=a.force)
    log('handover:', res)
    return 1 if res == 'failed' else 0


def cmd_cleanup(a):
    c = db()
    gone = cleanup(dry=a.dry_run, c=c)
    for n, why in gone:
        log(('would remove' if a.dry_run else 'removed'), n, '-', why)
    store = store_dir()
    log(f'store {store}: {len(asset_dirs(store))} folders, {dir_bytes(store) / 1e9:.2f} GB; free {free_gb(store):.1f} GB '
        f'(floor {env_f("PREPARE_FLOOR_GB", 40):g})')
    return 0


def cmd_status(a):
    c = db()
    store = store_dir()
    print('home   ', HOME)
    print('store  ', store, f'({dir_bytes(store) / 1e9:.2f} GB, {len(asset_dirs(store))} folders)')
    print('free   ', f'{free_gb(store):.1f} GB (floor {env_f("PREPARE_FLOOR_GB", 40):g} GB, keep '
                     f'{env_f("PREPARE_KEEP_DAYS", 7):g} days)')
    print('models ', AN.model_dir(), {n: bool(AN.model_path(n)) for n in AN.MODELS})
    print('tools  ', tool_versions())
    for r in c.execute('SELECT status, COUNT(*) n FROM assets GROUP BY status'):
        print('assets ', r['status'], r['n'])
    lt = c.execute("SELECT value FROM meta WHERE key='last_tick'").fetchone()
    print('tick   ', lt[0] if lt else 'never')
    print('render ', 'active' if render_active() else 'idle')
    return 0


def cmd_list(a):
    c = db()
    q = 'SELECT * FROM assets ' + ('' if a.all else "WHERE status IN ('ready','damaged') ") + \
        'ORDER BY created_at DESC LIMIT 50'
    for r in c.execute(q):
        print(f"{r['created_at']}  {r['status']:<9} {r['method'] or '-':<15} {r['key']}  {r['detail'][:90]}")
    return 0


def cmd_show(a):
    p = os.path.join(store_dir(), a.key, 'manifest.json')
    with open(p) as f:
        m = json.load(f)
    print(json.dumps({k: m.get(k) for k in ('key', 'status', 'source', 'rights', 'probe', 'checks', 'summary',
                                            'audio', 'timings', 'cpu_s', 'bytes')}, indent=1, ensure_ascii=False))
    return 0


def cmd_models(a):
    res = AN.fetch_models(log=log)
    for k, v in res.items():
        print(k, v, f"({AN.MODELS[k]['licence']})")
    return 0 if all(not str(v).startswith('error') for v in res.values()) else 1


def bed_paths(args):
    if args:
        return args
    dirs = [os.path.expanduser('~/.cache/digi-sound')]
    dirs += [d for d in (os.environ.get('PREPARE_BEDS') or '').split(':') if d]
    return [d for d in dirs if os.path.exists(d)]


def cmd_beats(a):
    beat_files(a.paths)
    return 0


def beat_files(paths, quiet=False):
    """Beat grid of every bed file under `paths` (default: the bed cache folders); returns how many were new."""
    files, new = [], 0
    for p in bed_paths(paths):
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p)
                            if f.lower().endswith(('.wav', '.flac', '.mp3', '.m4a', '.ogg')))
        elif os.path.exists(p):
            files.append(p)
    if not files:
        if not quiet:
            log('no bed files found (pass files or folders; default ~/.cache/digi-sound and PREPARE_BEDS)')
        return 0
    for f in files:
        wait_idle()
        t = time.time()
        b = AN.beats(f, os.path.join(HOME, 'beats'))
        if b is None:
            if not quiet:
                log(f'{os.path.basename(f)}: skipped (librosa missing or no sound)')
            continue
        new += 0 if b['cached'] else 1
        if not quiet or not b['cached']:
            log(f'{os.path.basename(f)}: {b["tempo"]} BPM, {b["n"]} beats over {b["secs"]} s'
                f'{" (cached)" if b["cached"] else ""} in {time.time() - t:.1f} s')
    return new


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('one')
    p.add_argument('source', help='a Steam appid, a page or file URL, or a local file (with --rights)')
    p.add_argument('--rights', help='for a local file: the publisher key in rights.yaml it came from')
    p.add_argument('--page', help='for a local file: the page or message it came from')
    p.add_argument('--name', required=True)
    p.add_argument('--title', help='the trailer title, used to choose among Steam trailers')
    p.add_argument('--force', action='store_true')
    p.add_argument('--max-mb', type=float, default=None)
    p.set_defaults(fn=cmd_one)
    p = sub.add_parser('from-watch')
    p.add_argument('--max', type=int, default=None)
    p.add_argument('--dry-run', action='store_true')
    p.set_defaults(fn=cmd_from_watch)
    p = sub.add_parser('handover')
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_handover)
    p = sub.add_parser('cleanup')
    p.add_argument('--dry-run', action='store_true')
    p.set_defaults(fn=cmd_cleanup)
    sub.add_parser('status').set_defaults(fn=cmd_status)
    p = sub.add_parser('list')
    p.add_argument('--all', action='store_true')
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser('show')
    p.add_argument('key')
    p.set_defaults(fn=cmd_show)
    sub.add_parser('models').set_defaults(fn=cmd_models)
    p = sub.add_parser('beats')
    p.add_argument('paths', nargs='*')
    p.set_defaults(fn=cmd_beats)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == '__main__':
    sys.exit(main())
