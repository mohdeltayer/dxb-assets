"""Digest writer: turns the store's pending rows into digest.json, breaking.json and digest.txt.

digest.txt keeps the line shapes of newsroom/watch_feeds.py (OFFICIAL, OUTLETS, failed:) so the
Watcher's habits and prompts carry over; the JSON adds media links, first-seen times and the
sequence number the news desk uses to know what it has not read yet.
"""
import datetime as dt
import json
import socket

import feedlib
import store

SCHEMA_VERSION = 1
SINGLES_CAP = 25          # one-outlet stories shown per digest, as watch_feeds.py
BREAKING_WINDOW_H = 24    # breaking.json keeps what went out as breaking in the last day
FAIL_AFTER = 2            # consecutive failed reads before a source is listed under failed


def health(db, now, sources_total):
    rows = db.execute('SELECT name, consecutive_failures, last_error, last_ok_at, breaking FROM sources WHERE enabled=1').fetchall()
    last = db.execute('SELECT MAX(last_poll_at) FROM sources').fetchone()[0]
    ok = sum(1 for r in rows if r['consecutive_failures'] == 0)
    failed = ['%s (%s%s)' % (r['name'], r['last_error'] or 'failed', ', %dx' % r['consecutive_failures'] if r['consecutive_failures'] > 1 else '')
              for r in rows if r['consecutive_failures'] >= FAIL_AFTER]
    return {
        'host': socket.gethostname(), 'last_poll_at': last, 'sources_enabled': len(rows), 'sources_ok': ok,
        'sources_failing': len(failed), 'failed': sorted(failed),
    }, sorted(failed)


def media_note(it):
    kinds = [m['type'] for m in it['media']]
    if not kinds:
        return ''
    parts = ['%d %s' % (kinds.count(k), k) for k in ('image', 'video', 'audio') if k in kinds]
    return ' | media: ' + ', '.join(parts)


def outlet_groups(db, now, rows):
    """Stories from outlet feeds with something new in this digest, with every outlet that ran
    them in the last 24 hours (same clustering and ordering as watch_feeds.py)."""
    wf = feedlib.watch_feeds()
    day = store.iso_m(now - dt.timedelta(hours=24))
    fresh = {r['id'] for r in rows if r['kind'] == 'outlet'}
    pool = [dict(r) for r in db.execute(
        "SELECT * FROM items WHERE kind='outlet' AND junk=0 AND COALESCE(NULLIF(published,''), first_seen)>=?", (day,))]
    pool.sort(key=lambda e: e['published'] or '')
    groups = [g for g in wf.cluster(pool) if any(e['id'] in fresh for e in g['items'])]
    key_pub = lambda g: max(e['published'] or '' for e in g['items'])
    groups.sort(key=key_pub, reverse=True)
    groups.sort(key=lambda g: len({e['source'] for e in g['items']}), reverse=True)
    out, singles = [], 0
    for g in groups:
        srcs = sorted({e['source'] for e in g['items']})
        if len(srcs) == 1:
            singles += 1
            if singles > SINGLES_CAP:
                continue
        lead = g['items'][0]
        media = next((json.loads(e['media']) for e in g['items'] if json.loads(e['media'] or '[]')), [])
        out.append({
            'count': len(srcs), 'published': lead['published'] or None, 'title': lead['title'], 'url': lead['url'],
            'sources': srcs, 'ar_relay': all(s.endswith('(AR)') for s in srcs), 'media': media,
            'items': [{'source': e['source'], 'title': e['title'], 'url': e['url'], 'published': e['published'] or None} for e in g['items']],
        })
    return out


def breaking_payload(db, now, seq, pending, cfg_sources_total):
    horizon = store.iso_s(now - dt.timedelta(hours=BREAKING_WINDOW_H))
    items = []
    for r in pending:
        d = store.item_dict(r)
        d['breaking_seq'] = seq
        items.append(d)
    older = [store.item_dict(r) for r in db.execute(
        'SELECT * FROM items WHERE breaking=1 AND breaking_seq>0 AND first_seen>=? ORDER BY breaking_seq DESC, id DESC', (horizon,))]
    h, _ = health(db, now, cfg_sources_total)
    return {
        'schema': SCHEMA_VERSION, 'file': 'breaking', 'generated_at': store.iso_s(now), 'seq': seq,
        'note': 'items: first handed over in this push (breaking_seq == seq). recent: handed over in the last %d h. '
                'An item from a breaking source is a lead from a first-party source, not a verdict: the Verifier grades it.' % BREAKING_WINDOW_H,
        'items': items, 'recent': older, 'watcher': h,
    }


def hourly_payload(db, now, seq, rows, since, not_covered, sources_total):
    off_rows = [r for r in rows if r['kind'] != 'outlet']
    items = []
    for r in sorted(off_rows, key=lambda r: r['published'] or '', reverse=True):
        d = store.item_dict(r)
        d['digest_seq'] = seq
        items.append(d)
    groups = outlet_groups(db, now, rows)
    h, failed = health(db, now, sources_total)
    return {
        'schema': SCHEMA_VERSION, 'file': 'digest', 'generated_at': store.iso_s(now), 'seq': seq, 'kind': 'hourly',
        'since': since, 'official': items, 'outlets': groups, 'failed': failed,
        'not_covered': not_covered, 'watcher': h,
    }


def hourly_text(p):
    lines = ['WATCH DIGEST seq=%d generated=%s since=%s host=%s' % (p['seq'], p['generated_at'], p['since'] or 'start', p['watcher']['host']),
             'OFFICIAL']
    for e in p['official']:
        sent = ' | already sent as breaking #%d' % e['breaking_seq'] if e.get('breaking_seq') else ''
        lines.append('%s | %s | %s | %s%s%s' % (e['published'] or 'no time', e['source'], e['title'], e['url'], media_note(e), sent))
    if not p['official']:
        lines.append('nothing new')
    lines.append('OUTLETS (%d stories with something new; count = outlets carrying it in 24 h)' % len(p['outlets']))
    for g in p['outlets']:
        relay = ' | AR RELAY: date it from the first report' if g['ar_relay'] else ''
        lines.append('%d | %s | %s | %s | %s%s' % (g['count'], g['published'] or 'no time', g['title'], ', '.join(g['sources']), g['url'], relay))
    lines.append('failed: ' + ('; '.join(p['failed']) if p['failed'] else 'none'))
    lines.append('not covered: ' + '; '.join(n['name'] for n in p['not_covered']))
    return '\n'.join(lines) + '\n'


def breaking_text(p):
    lines = ['BREAKING SOURCES seq=%d generated=%s' % (p['seq'], p['generated_at']), 'NEW IN THIS PUSH (%d)' % len(p['items'])]
    row = lambda e: '%s | %s | %s | %s%s | #%s' % (e['published'] or 'no time', e['source'], e['title'], e['url'], media_note(e), e.get('breaking_seq'))
    lines += [row(e) for e in p['items']]
    lines.append('HANDED OVER IN THE LAST %d H (%d)' % (BREAKING_WINDOW_H, len(p['recent'])))
    lines += [row(e) for e in p['recent']]
    return '\n'.join(lines) + '\n'


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + '\n'
