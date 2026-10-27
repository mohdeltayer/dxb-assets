"""SQLite store for the mechanical watch: schema, source sync, ingest, pending queries, pruning."""
import datetime as dt
import json
import os
import re
import sqlite3
import urllib.parse

import feedlib

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, 'schema.sql')
TRACKING = re.compile(r'^(utm_|fbclid$|gclid$|mc_|ref$|ref_|cmp$|cid$|campaign$|spm$)', re.I)


def now_dt():
    return dt.datetime.now(dt.timezone.utc)


def iso_s(t):
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def iso_m(t):
    return t.strftime('%Y-%m-%dT%H:%MZ')


def open_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path, timeout=60)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA busy_timeout=60000')
    with open(SCHEMA, encoding='utf-8') as f:
        db.executescript(f.read())
    return db


def meta_get(db, key, default=None):
    r = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    return r[0] if r else default


def meta_set(db, key, value):
    db.execute('INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))


def url_key(u):
    p = urllib.parse.urlsplit(u.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k)]
    scheme = 'https' if p.scheme in ('http', 'https') else p.scheme
    return urllib.parse.urlunsplit((scheme, p.netloc.lower(), p.path.rstrip('/') or '/', urllib.parse.urlencode(q), ''))


def sync_sources(db, sources):
    """Make the sources table match the config. Reads state (etag, failures) is kept; sources
    that left the config are disabled, never deleted (their items stay for deduplication)."""
    keep = set()
    for s in sources:
        keep.add(s.id)
        db.execute(
            '''INSERT INTO sources(id,name,kind,url,interval_min,breaking,enabled,origin)
               VALUES(?,?,?,?,?,?,1,?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, kind=excluded.kind, url=excluded.url,
                 interval_min=excluded.interval_min, breaking=excluded.breaking, enabled=1, origin=excluded.origin''',
            (s.id, s.name, s.kind, s.url, s.interval_min, int(s.breaking), s.origin))
    marks = ','.join('?' * len(keep)) or "''"
    db.execute('UPDATE sources SET enabled=0 WHERE id NOT IN (%s)' % marks, tuple(keep))
    db.commit()


def due_sources(db, sources, now, force=False, only_breaking=False):
    rows = {r['id']: r for r in db.execute('SELECT * FROM sources WHERE enabled=1')}
    out = []
    for s in sources:
        r = rows.get(s.id)
        if r is None or (only_breaking and not s.breaking):
            continue
        if not force and r['next_due_at'] and r['next_due_at'] > iso_s(now + dt.timedelta(seconds=45)):
            continue
        out.append(s)
    return out


def record_poll(db, src, now, status, items=0, new=0, ms=0, error=None, etag=None, last_modified=None):
    r = db.execute('SELECT consecutive_failures FROM sources WHERE id=?', (src.id,)).fetchone()
    fails = (r['consecutive_failures'] if r else 0)
    if status == 'error':
        fails += 1
        back = min(2 ** fails, 8)   # a failing source is asked less often, up to 8x its interval
        nxt = now + dt.timedelta(minutes=src.interval_min * back)
        db.execute('UPDATE sources SET last_poll_at=?, last_error=?, consecutive_failures=?, next_due_at=? WHERE id=?',
                   (iso_s(now), error, fails, iso_s(nxt), src.id))
    else:
        nxt = now + dt.timedelta(minutes=src.interval_min)
        db.execute('''UPDATE sources SET last_poll_at=?, last_ok_at=?, last_error=NULL, consecutive_failures=0, next_due_at=?,
                      etag=COALESCE(?, etag), last_modified=COALESCE(?, last_modified) WHERE id=?''',
                   (iso_s(now), iso_s(now), iso_s(nxt), etag, last_modified, src.id))
    db.execute('INSERT INTO polls(source_id,at,status,items,new_items,ms,error) VALUES(?,?,?,?,?,?,?)',
               (src.id, iso_s(now), status, items, new, ms, error))


def ingest(db, src, got, now, first_window_h=2, ignore=None):
    """Store the new items of one source. Returns the number inserted.

    First successful read of a source: items older than first_window_h are baseline (recorded,
    never handed over). After that everything unseen is a new item. Duplicates are matched on
    the normalised URL and on the title, within the source (the same two tests as watch_feeds.py).
    """
    wf = feedlib.watch_feeds()
    row = db.execute('SELECT baselined FROM sources WHERE id=?', (src.id,)).fetchone()
    first = not row['baselined']
    cutoff = iso_m(now - dt.timedelta(hours=first_window_h))
    first_seen = iso_s(now)
    n = 0
    for it in got[:30]:
        title, link = it['title'].strip(), it['url'].strip()
        if src.kind == 'gnews' and (title.lstrip().startswith('-') or len(title.split(' - ')[0].split()) < 3 or 'Shop' in title):
            continue   # store, cart and section pages, not news (as watch_feeds.py)
        junk = int(bool(src.kind == 'outlet' and wf.JUNK.search(title)) or bool(ignore and ignore.search(title)))
        baseline = int(first and not (it['published'] and it['published'] >= cutoff))
        try:
            db.execute(
                '''INSERT INTO items(source_id,source,kind,title,url,url_key,published,first_seen,summary,media,breaking,baseline,junk)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (src.id, src.name, src.kind, title, link, url_key(link), it['published'], first_seen, it.get('summary', ''),
                 json.dumps(it.get('media', []), ensure_ascii=False), int(src.breaking), baseline, junk))
            n += 1
        except sqlite3.IntegrityError:
            continue
    if first:
        db.execute('UPDATE sources SET baselined=1 WHERE id=?', (src.id,))
    return n


def pending_breaking(db, now, max_age_days=2):
    """Items from breaking sources not yet handed over. Too-old ones are closed as dropped (seq 0)."""
    recent = iso_m(now - dt.timedelta(days=max_age_days))
    db.execute("UPDATE items SET breaking_seq=0 WHERE breaking=1 AND breaking_seq IS NULL AND published<>'' AND published<?", (recent,))
    db.execute('UPDATE items SET breaking_seq=0 WHERE breaking=1 AND breaking_seq IS NULL AND (baseline=1 OR junk=1)')
    return db.execute('SELECT * FROM items WHERE breaking=1 AND breaking_seq IS NULL ORDER BY COALESCE(NULLIF(published,\'\'), first_seen) DESC').fetchall()


def pending_digest(db, now, max_age_days=2):
    """Items not yet carried by an hourly digest. Baseline and junk are closed; stale ones are
    recorded, not reported (seq 0). Returns the rows to report."""
    recent = iso_m(now - dt.timedelta(days=max_age_days))
    db.execute('UPDATE items SET digest_seq=0 WHERE digest_seq IS NULL AND (baseline=1 OR junk=1)')
    db.execute("UPDATE items SET digest_seq=0 WHERE digest_seq IS NULL AND published<>'' AND published<?", (recent,))
    return db.execute('SELECT * FROM items WHERE digest_seq IS NULL ORDER BY id').fetchall()


def prune(db, now, item_days=60, poll_days=7):
    db.execute('DELETE FROM items WHERE first_seen<? AND (digest_seq IS NOT NULL) AND (breaking=0 OR breaking_seq IS NOT NULL)',
               (iso_s(now - dt.timedelta(days=item_days)),))
    db.execute('DELETE FROM polls WHERE at<?', (iso_s(now - dt.timedelta(days=poll_days)),))
    db.execute('DELETE FROM handoffs WHERE created_at<?', (iso_s(now - dt.timedelta(days=30)),))
    db.commit()
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')


def item_dict(r):
    return {
        'id': r['id'], 'source': r['source'], 'source_kind': r['kind'], 'title': r['title'], 'url': r['url'],
        'published': r['published'] or None, 'first_seen': r['first_seen'], 'summary': r['summary'] or None,
        'media': json.loads(r['media'] or '[]'), 'breaking_source': bool(r['breaking']),
        'breaking_seq': r['breaking_seq'] or None,
    }
