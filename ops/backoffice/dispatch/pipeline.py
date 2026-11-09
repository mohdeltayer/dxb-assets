"""The pipeline record (release 2026-11-10 r3, pipeline visibility; adv-20261109-coordination-in-code).

dxb-queue desk/pipeline.json is the one place that says where every story in production stands. Production 2's record
keeper (a Haiku helper, task card "Record keeper" in newsroom/delegation.md) writes a row on each state change; the
inbox mirror (every 15 minutes) turns the open rows and the commitments into the inbox's `pipeline` collection.

Rows come only from a story or build handoff: the id is a board handoff id, or a story id under newsroom/stories/.
A row closes on published, dropped or superseded (a newer row names it in `supersedes`); closed rows stay three days.

    python3 pipeline.py set --file desk/pipeline.json --board desk/board.json --stories newsroom/stories \
        --id <handoff or story id> --state <state> [--title T] [--slot ISO] [--evidence E] [--supersedes ID] [--by WHO]
    python3 pipeline.py show --file desk/pipeline.json
    python3 pipeline.py docs --file desk/pipeline.json --commitments newsroom/commitments.json --existing <dir> --out <json>

States, in order: claimed, building, rendering, director, scheduled, published (closed), dropped (closed),
superseded (closed). A row never moves backwards except to dropped. No Publer ids, links to posts or tokens.
"""
import argparse, datetime as dt, json, os, re, sys

STATES = ('claimed', 'building', 'rendering', 'director', 'scheduled', 'published', 'dropped', 'superseded')
CLOSED = ('published', 'dropped', 'superseded')
KEEP_CLOSED_DAYS = 3
UTC = dt.timezone.utc
ID_TOKEN = re.compile(r'\b[0-9a-f]{24}\b|https?://\S+', re.I)


def now_iso():
    return dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def t(s):
    try:
        x = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return x if x.tzinfo else x.replace(tzinfo=UTC)
    except ValueError:
        return None


def load(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(path, doc):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, path)


def known(rid, board, stories_dir):
    hs = {str(h.get('id')) for h in (board or {}).get('handoffs', []) if isinstance(h, dict)}
    return rid in hs or bool(stories_dir and os.path.exists(os.path.join(stories_dir, rid + '.json')))


def upsert(doc, rid, state, at=None, title=None, slot=None, evidence=None, supersedes=None, by=None, board=None,
           stories_dir=None):
    """Returns the row; raises ValueError for an unknown id, an unknown state or a backwards move."""
    if state not in STATES:
        raise ValueError(f'state is one of {", ".join(STATES)}')
    if not known(rid, board, stories_dir):
        raise ValueError(f'{rid}: not a board handoff id nor a story under newsroom/stories/ (rows come only from a '
                         'story or build handoff)')
    at = at or now_iso()
    rows = doc.setdefault('rows', [])
    row = next((r for r in rows if r.get('id') == rid), None)
    if row is None:
        row = {'id': rid, 'state': state, 'since': at, 'history': []}
        rows.append(row)
    else:
        old = row.get('state')
        if old in CLOSED and state != old:
            raise ValueError(f'{rid} is closed ({old}); write a new row that supersedes it')
        if state != 'dropped' and old in STATES and STATES.index(state) < STATES.index(old):
            raise ValueError(f'{rid}: {old} cannot move back to {state}')
        if state != old:
            row['state'], row['since'] = state, at
    row['history'].append({'state': state, 'at': at, **({'by': by} if by else {})})
    for k, v in (('title', title), ('slot', slot), ('evidence', evidence)):
        if v:
            row[k] = ID_TOKEN.sub('[id]', v) if k == 'evidence' else v
    if state in CLOSED:
        row['closed_at'] = at
    if supersedes:
        old = next((r for r in rows if r.get('id') == supersedes), None)
        if old and old.get('state') not in CLOSED:
            old['state'], old['since'], old['closed_at'] = 'superseded', at, at
            old.setdefault('history', []).append({'state': 'superseded', 'at': at, 'by': rid})
        row['supersedes'] = supersedes
    doc['updated_at'] = at
    return row


def prune(doc, now):
    keep = []
    for r in doc.get('rows', []):
        c = t(r.get('closed_at'))
        if r.get('state') in CLOSED and c and now - c > dt.timedelta(days=KEEP_CLOSED_DAYS):
            continue
        keep.append(r)
    doc['rows'] = keep
    return doc


def docs(doc, commitments, now, existing=None):
    """Writes for the inbox's `pipeline` collection: one per row, the commitment's slot when the row has none;
    delete for rows pruned or gone."""
    rows = (commitments or {}).get('rows', []) if isinstance(commitments, dict) else (commitments or [])
    by_job = {}
    for c in rows:
        for k in (c.get('id'), re.sub(r'^\d{4}-\d{2}-\d{2}-', '', str(c.get('job', '')))):
            if k:
                by_job[str(k)] = c
    out, seen = [], set()
    for r in prune(dict(doc), now).get('rows', []):
        c = by_job.get(r['id']) or {}
        data = {'title': r.get('title') or c.get('title') or r['id'], 'state': r['state'], 'since': r.get('since'),
                'slot': r.get('slot') or c.get('slot'), 'evidence': r.get('evidence'), 'closed_at': r.get('closed_at'),
                'supersedes': r.get('supersedes'), 'open': r['state'] not in CLOSED,
                'age_min': int((now - t(r['since'])).total_seconds() // 60) if t(r.get('since')) else None}
        seen.add(r['id'])
        out.append({'op': 'set', 'doc_id': re.sub(r'[^A-Za-z0-9_.~:@+-]', '-', r['id'])[:200], 'data': data})
    for k in (existing or {}):
        if k not in {w['doc_id'] for w in out}:
            out.append({'op': 'delete', 'doc_id': k})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('set')
    for a in ('file', 'board', 'stories', 'id', 'state', 'title', 'slot', 'evidence', 'supersedes', 'by', 'at'):
        s.add_argument('--' + a)
    sh = sub.add_parser('show')
    sh.add_argument('--file', required=True)
    d = sub.add_parser('docs')
    for a in ('file', 'commitments', 'existing', 'out', 'now'):
        d.add_argument('--' + a)
    a = ap.parse_args(argv)
    if a.cmd == 'set':
        doc = load(a.file, {'about': 'desk/pipeline.json: ops/backoffice/dispatch/pipeline.py', 'rows': []})
        try:
            r = upsert(doc, a.id, a.state, a.at, a.title, a.slot, a.evidence, a.supersedes, a.by,
                       load(a.board, {}), a.stories)
        except ValueError as e:
            raise SystemExit(f'pipeline refused: {e}')
        prune(doc, dt.datetime.now(UTC))
        save(a.file, doc)
        print(f'pipeline: {r["id"]} {r["state"]} since {r["since"]}')
    elif a.cmd == 'show':
        for r in load(a.file, {}).get('rows', []):
            print(r.get('since'), r.get('state'), r.get('id'), '|', r.get('title', ''))
    else:
        now = t(a.now) if a.now else dt.datetime.now(UTC)
        ex = {}
        if a.existing and os.path.isdir(a.existing):
            ex = {n[:-5]: 1 for n in os.listdir(a.existing) if n.endswith('.json')}
        w = docs(load(a.file, {}), load(a.commitments, {}), now, ex)
        save(a.out, w)
        print('pipeline docs: %d writes (%d open)' % (len(w), sum(1 for x in w if x['op'] == 'set' and x['data']['open'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
