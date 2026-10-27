#!/usr/bin/env python3
"""Mechanical watch (back office service 1): reads the official sources and the outlet feeds on a
timer, keeps what is new in SQLite, and hands the news desk a digest. No Claude tokens, no agents.

    watch.py poll [--force] [--only-breaking]   read the sources that are due; hand over breaking items
    watch.py digest [--no-poll]                 the hourly digest (polls first)
    watch.py status                             what the store holds and how the sources are doing
    watch.py sources                            the sources, cadence and breaking flags as configured
    watch.py prune                              drop old rows

Environment (all optional): WATCH_HOME (default ~/backoffice/watch), WATCH_PUSH=off (write files,
push nothing, mark nothing handed over), WATCH_REMOTE, WATCH_BRANCH, WATCH_TOKEN_FILE,
WATCH_EMPTY_PUSH_H, WATCH_CONFIG, WATCH_NEWSROOM, WATCH_RENDER_CHECK=off, WATCH_PAUSE_ALL=1,
WATCH_FIRST_WINDOW_H, WATCH_SELF_UPDATE=off, WATCH_JOBS.
Exit codes: 0 done or nothing to do, 1 failure, 75 paused for a render.
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import digest as dg      # noqa: E402
import fetchers          # noqa: E402
import handoff           # noqa: E402
import sources as srcmod  # noqa: E402
import store             # noqa: E402

HOME = os.environ.get('WATCH_HOME') or os.path.expanduser('~/backoffice/watch')
DB_PATH = os.path.join(HOME, 'watch.db')
OUT = os.path.join(HOME, 'out')
STATE = os.path.join(HOME, 'state')
CLONE = os.path.join(HOME, 'handoff')
BUSY = os.environ.get('WATCH_BUSY_PATTERN') or r'render_job\.py|Runner\.Worker'
JOBS = int(os.environ.get('WATCH_JOBS') or 8)
POLL_BUDGET_S = 200   # a pass never runs longer than this (the unit's own timeout is 240)


def log(*a):
    print(dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%SZ'), *a, flush=True)


def render_active():
    if os.environ.get('WATCH_RENDER_CHECK') == 'off':
        return False
    try:
        return subprocess.run(['pgrep', '-f', BUSY], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@contextlib.contextmanager
def lock(wait_s=0):
    os.makedirs(STATE, exist_ok=True)
    f = open(os.path.join(STATE, 'watch.lock'), 'w')
    end = time.time() + wait_s
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            if time.time() >= end:
                f.close()
                yield False
                return
            time.sleep(2)
    try:
        yield True
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


def handoff_cfg(cfg):
    h = dict(cfg.get('handoff', {}))
    for k, env in (('remote', 'WATCH_REMOTE'), ('branch', 'WATCH_BRANCH'), ('token_file', 'WATCH_TOKEN_FILE'),
                   ('empty_push_min_gap_h', 'WATCH_EMPTY_PUSH_H')):
        if os.environ.get(env):
            h[k] = os.environ[env]
    return h


def push_enabled():
    return os.environ.get('WATCH_PUSH', 'on').lower() != 'off'


# ------------------------------------------------------------------ polling

def fetch_one(src, etag, lm):
    t0 = time.time()
    try:
        with fetchers.polite(src.target):
            body, new_etag, new_lm = fetchers.http_get(src.target, etag, lm)
        items = fetchers.read_source(src, body)
        return src, 'ok', items, new_etag, new_lm, None, int((time.time() - t0) * 1000)
    except fetchers.Unchanged:
        return src, 'unchanged', [], None, None, None, int((time.time() - t0) * 1000)
    except Exception as e:   # noqa: BLE001 - every failure is recorded against its source
        return src, 'error', [], None, None, fetchers.error_text(e), int((time.time() - t0) * 1000)


def poll(db, cfg, sources, force=False, only_breaking=False):
    now = store.now_dt()
    store.sync_sources(db, sources)
    due = store.due_sources(db, sources, now, force=force, only_breaking=only_breaking)
    first_h = float(os.environ.get('WATCH_FIRST_WINDOW_H') or cfg.get('first_poll_window_h', 2))
    conds = {r['id']: (r['etag'], r['last_modified']) for r in db.execute('SELECT id, etag, last_modified FROM sources')}
    t0 = time.time()
    new_total, errors, ok = 0, [], 0
    with ThreadPoolExecutor(JOBS) as ex:
        futs = [ex.submit(fetch_one, s, *conds.get(s.id, (None, None))) for s in due]
        for fu in futs:
            try:
                src, status, items, etag, lm, err, ms = fu.result(timeout=max(5, POLL_BUDGET_S - (time.time() - t0)))
            except Exception as e:   # noqa: BLE001
                log('poll budget exceeded, stopping this pass:', type(e).__name__)
                break
            if status == 'error':
                store.record_poll(db, src, now, 'error', ms=ms, error=err)
                errors.append('%s (%s)' % (src.name, err))
                continue
            ok += 1
            n = store.ingest(db, src, items, now, first_h) if status == 'ok' else 0
            store.record_poll(db, src, now, status, items=len(items), new=n, ms=ms, etag=etag, last_modified=lm)
            new_total += n
            if n:
                log('new %-3d %s' % (n, src.name))
    db.commit()
    log('poll: %d due, %d read, %d failed, %d new items, %.1fs' % (len(due), ok, len(errors), new_total, time.time() - t0))
    for e in errors:
        log('  failed:', e)
    return len(due), errors, new_total


# ------------------------------------------------------------------ hand-over

def write_out(files):
    os.makedirs(OUT, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
            f.write(text)


def new_seq(db, kind, now):
    cur = db.execute("INSERT INTO handoffs(kind,created_at,status) VALUES(?,?,'pending')", (kind, store.iso_s(now)))
    db.commit()
    return cur.lastrowid


def close_handoff(db, seq, status, n, detail=''):
    db.execute('UPDATE handoffs SET status=?, n_items=?, detail=? WHERE seq=?', (status, n, detail[:300], seq))
    db.commit()


def squash_due(db, cfg_h, now):
    last = store.meta_get(db, 'handoff_squashed_at')
    if not last:
        store.meta_set(db, 'handoff_squashed_at', store.iso_s(now))
        return False
    return last < store.iso_s(now - dt.timedelta(days=float(cfg_h.get('squash_days', 7))))


def deliver(db, cfg, files, message, seq, n_items):
    """Write the files to the out folder, then push them. Returns True when handed over."""
    write_out(files)
    h = handoff_cfg(cfg)
    if not push_enabled():
        close_handoff(db, seq, 'dry', n_items, 'WATCH_PUSH=off: files in ' + OUT)
        return False
    now = store.now_dt()
    try:
        squash = squash_due(db, h, now)
        res = handoff.push(CLONE, files, message, h, squash_due=squash)
    except (handoff.PushError, OSError, subprocess.SubprocessError) as e:
        close_handoff(db, seq, 'failed', n_items, str(e))
        log('handoff failed:', str(e)[:200])
        return False
    if squash and res == 'pushed':
        store.meta_set(db, 'handoff_squashed_at', store.iso_s(now))
    store.meta_set(db, 'last_push_at', store.iso_s(now))
    close_handoff(db, seq, 'pushed', n_items, res)
    log('handoff #%d %s (%d items)' % (seq, res, n_items))
    return True


def hand_over_breaking(db, cfg, sources_total):
    now = store.now_dt()
    pending = store.pending_breaking(db, now, cfg.get('report_max_age_days', 2))
    db.commit()
    if not pending:
        return 0
    seq = new_seq(db, 'breaking', now)
    p = dg.breaking_payload(db, now, seq, pending, sources_total)
    files = {'breaking.json': dg.dumps(p), 'breaking.txt': dg.breaking_text(p)}
    ids = [r['id'] for r in pending]
    if deliver(db, cfg, files, 'watch #%d breaking %s: %d items' % (seq, store.iso_m(now), len(ids)), seq, len(ids)):
        db.executemany('UPDATE items SET breaking_seq=? WHERE id=?', [(seq, i) for i in ids])
        db.commit()
    elif not push_enabled():
        print(files['breaking.txt'], end='')
    return len(ids)


def hourly(db, cfg, sources_total):
    now = store.now_dt()
    rows = store.pending_digest(db, now, cfg.get('report_max_age_days', 2))
    db.commit()
    h = handoff_cfg(cfg)
    last_h = db.execute("SELECT MAX(created_at) FROM handoffs WHERE kind='hourly' AND status IN ('pushed','dry')").fetchone()[0]
    seq = new_seq(db, 'hourly', now)
    nc = cfg.get('not_covered', [])
    p = dg.hourly_payload(db, now, seq, rows, last_h, nc, sources_total)
    # the breaking file travels with every hourly push so the desk always sees the last day's list
    b = dg.breaking_payload(db, now, seq, [], sources_total)
    files = {'digest.json': dg.dumps(p), 'digest.txt': dg.hourly_text(p), 'breaking.json': dg.dumps(b),
             'breaking.txt': dg.breaking_text(b)}
    quiet = not p['official'] and not p['outlets']
    gap_h = float(h.get('empty_push_min_gap_h', 1))
    last_push = store.meta_get(db, 'last_push_at')
    if quiet and push_enabled() and last_push and last_push > store.iso_s(now - dt.timedelta(hours=gap_h) + dt.timedelta(minutes=5)):
        close_handoff(db, seq, 'skipped', 0, 'nothing new and the last push is younger than %g h' % gap_h)
        log('digest: nothing new, last push %s, skipped' % last_push)
        db.executemany('UPDATE items SET digest_seq=0 WHERE id=?', [(r['id'],) for r in rows])
        db.commit()
        return
    n = len(p['official']) + sum(len(g['items']) for g in p['outlets'])
    if deliver(db, cfg, files, 'watch #%d hourly %s: %d official, %d outlet stories' % (seq, store.iso_m(now), len(p['official']), len(p['outlets'])), seq, n):
        db.executemany('UPDATE items SET digest_seq=? WHERE id=?', [(seq, r['id']) for r in rows])
        db.commit()
    elif not push_enabled():
        print(files['digest.txt'], end='')


# ------------------------------------------------------------------ commands

def self_update():
    if os.environ.get('WATCH_SELF_UPDATE') == 'off' or not os.path.isdir(os.path.join(handoff_repo(), '.git')):
        return
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    tf = os.environ.get('WATCH_PULL_TOKEN_FILE')
    if tf and os.access(tf, os.R_OK):
        env = handoff.git_env(tf)
    try:
        p = subprocess.run(['git', '-C', handoff_repo(), 'pull', '--ff-only', '-q'], env=env, capture_output=True, text=True, timeout=120)
        if p.returncode:
            log('self-update skipped:', handoff.scrub(p.stderr)[:150])
    except (OSError, subprocess.SubprocessError) as e:
        log('self-update skipped:', type(e).__name__)


def handoff_repo():
    return os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def cmd_poll(a):
    with lock(0) as got:
        if not got:
            log('another pass is running, skipped')
            return 0
        cfg = srcmod.load_config()
        sources = srcmod.build(cfg)
        busy = render_active()
        only_breaking = a.only_breaking
        if busy:
            if os.environ.get('WATCH_PAUSE_ALL') == '1':
                log('render active: paused')
                return 75
            only_breaking = True   # a handful of GETs at nice 10; breaking sources must not wait out a render
            log('render active: reading breaking sources only')
        db = store.open_db(DB_PATH)
        poll(db, cfg, sources, force=a.force, only_breaking=only_breaking)
        hand_over_breaking(db, cfg, len(sources))
        return 0


def cmd_digest(a):
    with lock(150) as got:
        if not got:
            log('another pass is still running, digest skipped')
            return 1
        self_update()
        cfg = srcmod.load_config()
        sources = srcmod.build(cfg)
        db = store.open_db(DB_PATH)
        if not a.no_poll:
            busy = render_active()
            if busy and os.environ.get('WATCH_PAUSE_ALL') == '1':
                log('render active: polling paused, digest from what is stored')
            else:
                poll(db, cfg, sources, only_breaking=busy)
                hand_over_breaking(db, cfg, len(sources))
        hourly(db, cfg, len(sources))
        store.prune(db, store.now_dt())
        return 0


def cmd_status(a):
    db = store.open_db(DB_PATH)
    q = lambda s: db.execute(s).fetchone()[0]
    size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    print('db: %s  %.1f MB' % (DB_PATH, size / 1e6))
    print('sources: %d enabled, %d failing now' % (q('SELECT COUNT(*) FROM sources WHERE enabled=1'), q('SELECT COUNT(*) FROM sources WHERE consecutive_failures>0')))
    print('items: %d total, %d waiting for the hourly digest, %d waiting as breaking' % (
        q('SELECT COUNT(*) FROM items'), q('SELECT COUNT(*) FROM items WHERE digest_seq IS NULL AND baseline=0 AND junk=0'),
        q('SELECT COUNT(*) FROM items WHERE breaking=1 AND breaking_seq IS NULL AND baseline=0 AND junk=0')))
    print('last poll: %s   last push: %s' % (q('SELECT MAX(last_poll_at) FROM sources'), store.meta_get(db, 'last_push_at', 'never')))
    for r in db.execute('SELECT seq, kind, created_at, status, n_items, detail FROM handoffs ORDER BY seq DESC LIMIT 5'):
        print('  handoff #%d %s %s %s items=%d %s' % (r['seq'], r['kind'], r['created_at'], r['status'], r['n_items'], r['detail'] or ''))
    for r in db.execute('SELECT name, consecutive_failures, last_error FROM sources WHERE consecutive_failures>0 AND enabled=1 ORDER BY consecutive_failures DESC'):
        print('  failing: %s x%d %s' % (r['name'], r['consecutive_failures'], r['last_error']))
    print('token file:', 'readable' if os.access(handoff_cfg(srcmod.load_config()).get('token_file', ''), os.R_OK) else 'MISSING or unreadable')
    print('render active now:', render_active())
    return 0


def cmd_sources(a):
    cfg = srcmod.load_config()
    ss = srcmod.build(cfg)
    for s in sorted(ss, key=lambda s: (not s.breaking, s.kind, s.name)):
        print('%-9s %3d min %s %-45s %s' % (s.kind, s.interval_min, 'BREAKING' if s.breaking else '        ', s.name, s.origin))
    print('%d sources (%d breaking)' % (len(ss), sum(s.breaking for s in ss)))
    return 0


def cmd_prune(a):
    db = store.open_db(DB_PATH)
    store.prune(db, store.now_dt())
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('poll'); p.add_argument('--force', action='store_true'); p.add_argument('--only-breaking', action='store_true')
    p.set_defaults(fn=cmd_poll)
    p = sub.add_parser('digest'); p.add_argument('--no-poll', action='store_true'); p.set_defaults(fn=cmd_digest)
    sub.add_parser('status').set_defaults(fn=cmd_status)
    sub.add_parser('sources').set_defaults(fn=cmd_sources)
    sub.add_parser('prune').set_defaults(fn=cmd_prune)
    a = ap.parse_args()
    os.makedirs(HOME, exist_ok=True)
    try:
        return a.fn(a)
    except Exception as e:   # noqa: BLE001
        log('FAILED:', type(e).__name__, str(e)[:300])
        return 1


if __name__ == '__main__':
    sys.exit(main())
