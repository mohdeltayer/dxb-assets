"""Hand-over of prepared trailers to the news desk (phase 1 INTAKE, adv-20261029-server-handover).

The main session works in a cloud container and cannot read the server's disk, and footage must never go into
dxb-assets (public) or a public Actions artifact. So after a tick that changed the store, prepare pushes a small
picture of it to the private dxb-watch repo, on its own branch (`prepared`, never the watch's `main`):

    prepared/index.json            one entry per asset of the last PREPARE_KEEP_DAYS days, newest first: key, game,
                                   status, the watch item it came from (source, url, first seen), source method and
                                   page, rights basis and credit, probe, flags, scene count, focus found, timings
    prepared/sheets/<key>.jpg      the contact sheet of every ready asset still in the store

Source files stay on the server; a render job reaches them by key (phase 2). The branch always holds exactly one
commit with exactly the current files (force-pushed), so expired sheets disappear and the repo stays small.

It reuses the watch's push plumbing (handoff.git_env: the token is read by git from the root-owned file, never on a
command line or in a log) and the watch's remote and token file from its sources.yaml. No new secret.
PREPARE_HANDOFF=off writes the files to ~/backoffice/prepare/handover/out only. The watch's own code is unchanged.
"""
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
WATCH_DIR = os.path.join(os.path.dirname(HERE), 'watch')

# Only these manifest fields leave the server: no local paths, no attempts log with hosts' query strings.
SOURCE_KEYS = ('step', 'method', 'page', 'url', 'publisher', 'fetched_at', 'steam')
RIGHTS_KEYS = ('publisher', 'register_key', 'basis', 'credit', 'terms', 'excerpt_only', 'on_screen_credit',
               'music_flag', 'rights_review', 'embargo', 'page_music_note')
PROBE_KEYS = ('w', 'h', 'fps', 'duration', 'kbps', 'audio', 'video')
MAX_SHEET_BYTES = 3_000_000


def _pick(d, keys):
    d = d or {}
    return {k: d[k] for k in keys if k in d and d[k] is not None}


def _clean_url(u):
    """Drop query strings (signed CDN links) before anything leaves the server."""
    if not isinstance(u, str):
        return u
    return u.split('?', 1)[0]


def entry(man, has_sheet):
    src = _pick(man.get('source'), SOURCE_KEYS)
    for k in ('url', 'page'):
        if k in src:
            src[k] = _clean_url(src[k])
    w = man.get('watch') or {}
    e = {
        'key': man.get('key'), 'game': man.get('name'), 'status': man.get('status'),
        'created_at': man.get('created_at'),
        'watch': {'item': w.get('item'), 'source': w.get('source'), 'title': w.get('title'),
                  'url': _clean_url(w.get('url')), 'published': w.get('published'),
                  'first_seen': w.get('first_seen'), 'score': w.get('score')},
        'source': src,
        'rights': _pick(man.get('rights'), RIGHTS_KEYS),
        'probe': _pick(man.get('probe'), PROBE_KEYS),
        'summary': man.get('summary'),
        'flags': flags(man),
        'focus_found': (man.get('summary') or {}).get('focus_found'),
        'beats': ((man.get('audio') or {}).get('beats') or {}) if isinstance((man.get('audio') or {}).get('beats'),
                                                                               dict) else None,
        'timings': man.get('timings'), 'cpu_s': man.get('cpu_s'), 'bytes': man.get('bytes'),
        'sheet': f"prepared/sheets/{man.get('key')}.jpg" if has_sheet else None,
    }
    return {k: v for k, v in e.items() if v not in (None, {}, [])}


def flags(man):
    """The checks a brief needs before choosing shots, in a few words each."""
    out = []
    ch = man.get('checks') or {}
    dec = ch.get('decode') or {}
    if dec and not dec.get('clean', True):
        out.append('decode errors')
    if ch.get('bitrate'):                                   # decodecheck.bitrate_flag: a sentence, or None
        out.append('lowbit')
    if ch.get('smear'):                                     # analyse.smear: [[start, end, peak], ...]
        out.append('smear %d' % len(ch['smear']))
    s = man.get('summary') or {}
    for k in ('profile', 'cut_text', 'blocky'):
        if s.get(k):
            out.append(f'{k} {s[k]}')
    if s.get('first_frame_text'):
        out.append('text on first frame')
    st = (man.get('source') or {}).get('steam') or {}
    if str(st.get('item_trailer', '')).startswith('unknown'):
        out.append('may not be the announced trailer')     # 26 Oct rule: trailer news shows the trailer
    r = man.get('rights') or {}
    if r.get('embargo'):
        out.append('embargo')
    if r.get('music_flag') or r.get('page_music_note'):
        out.append('music restriction')
    if r.get('rights_review'):
        out.append('rights unreviewed')
    return out


def build(store, rows):
    """Return ({name: bytes}, n_ready). rows: asset rows (dict-like) from prepare.db, newest first."""
    entries, files = [], {}
    for r in rows:
        man = None
        mp = os.path.join(r['path'] or os.path.join(store, r['key']), 'manifest.json')
        if r['status'] in ('ready', 'damaged', 'no-video') and os.path.exists(mp):
            try:
                with open(mp, encoding='utf-8') as f:
                    man = json.load(f)
            except (OSError, ValueError):
                man = None
        if man is None:
            entries.append({'key': r['key'], 'game': r['name'], 'status': r['status'],
                            'created_at': r['created_at'], 'detail': (r['detail'] or '')[:300]})
            continue
        sheet = os.path.join(os.path.dirname(mp), man.get('sheet') or 'sheet.jpg')
        has = man.get('status') == 'ready' and os.path.exists(sheet) and os.path.getsize(sheet) <= MAX_SHEET_BYTES
        if has:
            with open(sheet, 'rb') as f:
                files[f"prepared/sheets/{man['key']}.jpg"] = f.read()
        entries.append(entry(man, has))
    n_ready = sum(1 for e in entries if e.get('status') == 'ready')
    index = {'version': 1, 'assets': len(entries), 'ready': n_ready, 'entries': entries}
    files['prepared/index.json'] = (json.dumps(index, indent=1, ensure_ascii=False) + '\n').encode('utf-8')
    return files, n_ready


def digest(files):
    h = hashlib.sha256()
    for k in sorted(files):
        if k == 'prepared/index.json':
            continue
        h.update(k.encode())
        h.update(hashlib.sha256(files[k]).digest())
    # the index changes only through its entries; generated-at stamps are kept out of it on purpose
    h.update(hashlib.sha256(files['prepared/index.json']).digest())
    return h.hexdigest()


def write_out(out, files, clear=True):
    if clear:
        shutil.rmtree(out, ignore_errors=True)
    for name, data in files.items():
        p = os.path.join(out, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)


def config():
    """remote and token file from the watch's sources.yaml; branch 'prepared'. Env overrides for tests."""
    h = {}
    try:
        import yaml
        with open(os.path.join(WATCH_DIR, 'sources.yaml'), encoding='utf-8') as f:
            h = dict((yaml.safe_load(f) or {}).get('handoff') or {})
    except (OSError, ImportError, ValueError):
        pass
    h['branch'] = os.environ.get('PREPARE_HANDOFF_BRANCH') or 'prepared'
    if h['branch'] in ('main', 'master'):
        raise ValueError('the prepared hand-over never pushes to the watch branch')
    for k, env in (('remote', 'PREPARE_HANDOFF_REMOTE'), ('token_file', 'PREPARE_HANDOFF_TOKEN_FILE')):
        if os.environ.get(env):
            h[k] = os.environ[env]
    return h


def push(workdir, files, message, h):
    """Replace the branch with one commit holding exactly `files`. Returns 'pushed'. Raises handoff.PushError."""
    import sys
    sys.path.insert(0, WATCH_DIR)
    import handoff
    token = h.get('token_file')
    if not token or not os.access(token, os.R_OK):
        raise handoff.PushError('token file %s is missing or not readable' % token)
    if not h.get('remote'):
        raise handoff.PushError('no remote configured')
    env = handoff.git_env(token)
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir)
    handoff.git(['init', '-q'], workdir, env)
    handoff.git(['checkout', '-q', '--orphan', 'prepared'], workdir, env)
    handoff.git(['remote', 'add', 'origin', h['remote']], workdir, env)
    write_out(workdir, files, clear=False)        # a fresh folder: clearing it would remove .git
    ident = ['-c', 'user.name=' + h.get('commit_name', 'dxb-prepare'),
             '-c', 'user.email=' + h.get('commit_email', 'noreply@github.com'), '-c', 'commit.gpgsign=false']
    handoff.git(['add', '-A'], workdir, env)
    handoff.git(ident + ['commit', '-q', '-m', message], workdir, env)
    handoff.git(['push', '-q', '--force', 'origin', 'HEAD:refs/heads/' + h['branch']], workdir, env, timeout=300)
    return 'pushed'


def run(c, store, home, iso_now, log, force=False):
    """Build, compare with the last hand-over, push when changed. Never raises: returns a one-word outcome."""
    keep = float(os.environ.get('PREPARE_KEEP_DAYS') or 7)
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM assets WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?) ORDER BY created_at DESC",
        (f'-{keep:g} days',))]
    files, n_ready = build(store, rows)
    d = digest(files)
    last = c.execute("SELECT value FROM meta WHERE key='handover_digest'").fetchone()
    if last and last[0] == d and not force:
        return 'unchanged'
    out = os.path.join(home, 'handover', 'out')
    write_out(out, files)
    if os.environ.get('PREPARE_HANDOFF', 'on').lower() == 'off':
        log(f'handover: {len(rows)} entries, {n_ready} ready, written to {out} (PREPARE_HANDOFF=off)')
        return 'dry'
    try:
        h = config()
        res = push(os.path.join(home, 'handover', 'clone'), files,
                   f'Prepared trailers {iso_now}: {len(rows)} entries, {n_ready} ready', h)
    except Exception as e:  # noqa: BLE001 (a failed hand-over never fails the tick; next change retries)
        msg = str(e)
        try:
            import sys
            sys.path.insert(0, WATCH_DIR)
            import handoff
            msg = handoff.scrub(msg)
        except Exception:  # noqa: BLE001
            msg = msg[-300:]
        log('handover failed:', msg[:300])
        return 'failed'
    c.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('handover_digest', d))
    c.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('handover_at', iso_now))
    c.commit()
    log(f'handover {res}: {len(rows)} entries, {n_ready} ready, {len(files) - 1} sheets')
    return res
