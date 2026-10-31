#!/usr/bin/env python3
"""The promise keeper: checks every open commitment against its slot and raises alarms (adv-20261030-promise-keeper,
with the amendments of its addendum_2251, Mohammad 30 Oct 2026).

A script, not an agent: no Claude in the loop. Every 5 minutes it reads newsroom/commitments.json, works out where
each open promise stands on the ladder from its slot T, and writes a status (one line for the sessions, six lines
for the dashboard and the morning digest, and the rows). It never posts, schedules or deletes anything; the
fallback a row names is recorded as what would apply (alarm-only) until fallback publishing is switched on by a
release (KEEPER_MODE=fallback), and even then this script only records the decision for the ops session.

Evidence comes from our side (option 2 on the card): ops writes each row's delivery per platform at submit and at
the slot check. Older rows that carry only a free-text `evidence` are read as before ("scheduled", "published").

  keeper.py tick   [--commitments F] [--state S] [--out DIR] [--now ISO]   one pass: status files, alarms
  keeper.py line   [--status F | --commitments F] [--now ISO]                'overdue commitments: N, at risk: M'
  keeper.py show   [--commitments F] [--now ISO]                            the ladder per row, sends nothing

Environment: KEEPER_MODE (alarm-only, the default, or fallback), KEEPER_NTFY (on or off), KEEPER_NTFY_TOPIC (the
topic itself, from an Actions secret) or KEEPER_TOPIC_FILE (a root-owned file on the server). The topic is never
printed or logged.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

DUBAI = timezone(timedelta(hours=4))
PLATFORMS = ('instagram', 'x', 'threads')
FALLBACKS = ('publish-last-passed', 'bank-piece', 'shift-series-one-day', 'card-only')

# The ladder from the slot T (addendum B), in minutes.
T_SOURCES, T_QC, T_SUBMIT, T_EVIDENCE, T_CONFIRM = -90, -45, -30, -15, 5
ON_TIME_MIN = 15            # published within 15 minutes of the slot counts as on time
LOG_KEEP = 500              # lines of keeper.log kept on the status branch

PRODUCTION = ('queued', 'claimed', 'ready', 'rendered', 'qc_passed', 'blocked', 'rejected')
DELIVERY = ('not_submitted', 'submitting', 'scheduled', 'published', 'failed', 'uncertain')


# ---------------------------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------------------------
def parse_time(s):
    """ISO time with an offset (Dubai slots: 2026-10-31T00:00+04:00). A time without an offset is Dubai time."""
    if not s:
        return None
    s = str(s).strip().replace('Z', '+00:00')
    m = re.match(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d)(:\d\d)?(\.\d+)?([+-]\d\d:?\d\d)?$', s)
    if not m:
        return None
    base = m.group(1) + (m.group(2) or ':00')
    off = m.group(4)
    if off and ':' not in off:
        off = off[:3] + ':' + off[3:]
    dt = datetime.fromisoformat(base + (off or '+04:00'))
    return dt.astimezone(timezone.utc)


def dubai(dt):
    return dt.astimezone(DUBAI).strftime('%a %d %b %H:%M') + ' Dubai'


def mins(delta):
    return int(delta.total_seconds() // 60)


# ---------------------------------------------------------------------------------------------
# Rows: the three state dimensions (addendum A), read from new fields or the older free text
# ---------------------------------------------------------------------------------------------
def platforms_of(row):
    out = []
    for p in row.get('platforms') or PLATFORMS:
        p = str(p).lower().strip()
        p = {'twitter': 'x', 'ig': 'instagram'}.get(p, p)
        if p not in out:
            out.append(p)
    return out


def delivery_of(row):
    """{platform: {'state': ..., 'url': ..., 'at': ...}} for every platform of the row."""
    plats = platforms_of(row)
    raw = row.get('delivery') if isinstance(row.get('delivery'), dict) else {}
    legacy = ' '.join(str(row.get(k) or '') for k in ('status', 'evidence')).lower()
    links = row.get('links') if isinstance(row.get('links'), dict) else {}
    out = {}
    for p in plats:
        d = raw.get(p)
        if isinstance(d, str):
            d = {'state': d}
        d = dict(d or {})
        if not d.get('state'):
            if links.get(p) or links.get({'x': 'X', 'instagram': 'Instagram', 'threads': 'Threads'}[p] if p in PLATFORMS else p):
                d['state'] = 'published'
            elif row.get('done') or 'published' in legacy:
                d['state'] = 'published'
            elif 'scheduled' in legacy:
                d['state'] = 'scheduled'
            else:
                d['state'] = 'not_submitted'
        if d['state'] not in DELIVERY:
            d['state'] = 'uncertain'
        out[p] = d
    return out


def production_of(row):
    p = str(row.get('production') or '').lower().replace(' ', '_')
    if p in PRODUCTION:
        return p
    return 'queued'


def due_of(row):
    """(slot now, original due): original_due_at never changes; slot may have moved (with history)."""
    slot = parse_time(row.get('slot'))
    orig = parse_time(row.get('original_due_at')) or slot
    return slot, orig


# ---------------------------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------------------------
def assess(row, now, mode):
    """One row's place on the ladder. Returns a dict the status, the alarms and the tests read."""
    slot, orig = due_of(row)
    title = row.get('title') or row.get('id')
    a = {'id': row.get('id'), 'title': title, 'kind': row.get('kind'), 'slot': row.get('slot'),
         'slot_dubai': dubai(slot) if slot else None, 'fallback': row.get('fallback'),
         'held': bool(row.get('held_by_mohammad')), 'production': production_of(row),
         'delivery': {p: d['state'] for p, d in delivery_of(row).items()}, 'stage': None, 'commitment': 'open',
         'alarm': None, 'note': None, 'minutes_to_slot': None, 'would_apply': None}
    if not slot:
        a.update(stage='no slot', commitment='open', alarm='bad-row', note='row has no readable slot')
        return a
    to_slot = mins(slot - now)
    a['minutes_to_slot'] = to_slot
    states = list(a['delivery'].values())
    published = [p for p, s in a['delivery'].items() if s == 'published']
    exceptions = {p: s for p, s in a['delivery'].items() if s in ('failed', 'uncertain')}

    if row.get('commitment') in ('fulfilled_on_time', 'fulfilled_late', 'missed') or row.get('done'):
        a['commitment'] = row.get('commitment') or 'fulfilled'
        a['stage'] = 'closed'
        return a
    if states and all(s == 'published' for s in states):
        at = max((parse_time(d.get('at')) for d in delivery_of(row).values() if d.get('at')), default=None)
        late = at and at > slot + timedelta(minutes=ON_TIME_MIN)
        a['commitment'] = 'fulfilled_late' if late else 'fulfilled_on_time'
        if orig and slot and slot > orig:
            a['commitment'] = 'fulfilled_late'           # moved slot: the promise was kept late, never on time
        a['stage'] = 'published'
        a['logged'] = bool(row.get('logged') or row.get('inbox_published'))
        return a
    if a['held']:
        a['stage'] = 'held by Mohammad'
        return a

    scheduled_all = states and all(s in ('scheduled', 'published') for s in states)
    if exceptions:
        a['stage'] = 'delivery exception'
        a['commitment'] = 'at_risk'
        a['alarm'] = 'delivery'
        a['note'] = ', '.join('%s %s' % (p, s) for p, s in sorted(exceptions.items())) + \
            '; look the post up before any retry (never resubmit blind)'
        return a
    if scheduled_all:
        if to_slot <= -T_CONFIRM:                         # T+5 and not every platform confirmed published
            a['stage'] = 'publication unconfirmed'
            a['commitment'] = 'at_risk'
            a['alarm'] = 'unconfirmed'
            a['note'] = 'not confirmed published on %s by T+%d; reconcile, never move silently' % (
                ', '.join(p for p, s in a['delivery'].items() if s != 'published'), T_CONFIRM)
        else:
            a['stage'] = 'scheduled'
        return a

    # Not scheduled on every platform yet.
    if to_slot > -T_SOURCES:
        a['stage'] = 'ahead'
    elif to_slot > -T_QC:
        a['stage'] = 'T-90: sources and template path decided now'
    elif to_slot > -T_SUBMIT:
        a['stage'] = 'T-45: QC-ready or fallback committed'
        a['commitment'] = 'at_risk'
    elif to_slot > -T_EVIDENCE:
        a['stage'] = 'T-30: submit now'
        a['commitment'] = 'at_risk'
    elif to_slot > 0:
        a['stage'] = 'T-15: no evidence it is scheduled'
        a['commitment'] = 'at_risk'
        a['alarm'] = 'at-risk'
    else:
        a['stage'] = 'slot passed, not scheduled'
        a['commitment'] = 'missed' if to_slot <= -60 else 'at_risk'
        a['alarm'] = 'missed'
        fb = row.get('fallback') if row.get('fallback') in FALLBACKS else 'card-only'
        a['would_apply'] = fb
        a['note'] = ('fallback %s %s' % (fb, 'recorded for ops (alarm-only mode)' if mode != 'fallback'
                                         else 'decided: ops applies it now'))
    if a['production'] == 'blocked':
        a['note'] = ((a['note'] + '; ') if a['note'] else '') + \
            'production blocked: the post goes out on the current template unless Mohammad holds it'
    return a


def summarise(rows, now, mode):
    assessed = [assess(r, now, mode) for r in rows]
    open_rows = [a for a in assessed if a['stage'] not in ('closed', 'published')]
    overdue = [a for a in open_rows if a['stage'] == 'slot passed, not scheduled']
    at_risk = [a for a in open_rows if a['commitment'] == 'at_risk' and a not in overdue]
    line = 'overdue commitments: %d, at risk: %d' % (len(overdue), len(at_risk))

    # The six lines (addendum G).
    def closest():
        cand = [a for a in open_rows if a['minutes_to_slot'] is not None and a['stage'] not in ('scheduled',
                                                                                                'held by Mohammad')]
        if not cand:
            return 'closest promise to failure: none (every open promise is scheduled or held)'
        a = min(cand, key=lambda x: x['minutes_to_slot'])
        return 'closest promise to failure: %s, %s (%+d min), %s' % (a['title'], a['slot_dubai'],
                                                                      a['minutes_to_slot'], a['stage'])
    uncertain = ['%s %s' % (a['id'], p) for a in assessed for p, s in a['delivery'].items() if s == 'uncertain']
    failed = ['%s %s' % (a['id'], p) for a in assessed for p, s in a['delivery'].items() if s == 'failed']
    future = sorted(parse_time(a['slot']) for a in assessed
                    if a['slot'] and parse_time(a['slot']) and parse_time(a['slot']) > now
                    and a['stage'] in ('scheduled',))
    if future:
        points = [now] + future
        gap = max(((points[i + 1] - points[i]), points[i]) for i in range(len(points) - 1))
        cover = 'confirmed future coverage: until %s; largest gap %d min from %s' % (
            dubai(future[-1]), mins(gap[0]), dubai(gap[1]))
    else:
        cover = 'confirmed future coverage: none scheduled'
    unlogged = [a['id'] for a in assessed if a['stage'] == 'published' and not a.get('logged')]
    six = [
        closest(),
        'oldest owner request not started: not read by the keeper (the inbox is read by the sessions)',
        'submissions with uncertain outcome: ' + (', '.join(uncertain) or 'none'),
        'destinations that failed independently: ' + (', '.join(failed) or 'none'),
        cover,
        'published posts not yet in the shared log: ' + (', '.join(unlogged) or 'none'),
    ]
    return {'generated_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'mode': mode, 'line': line,
            'overdue': len(overdue), 'at_risk': len(at_risk), 'six': six, 'rows': assessed}


# ---------------------------------------------------------------------------------------------
# Alarms (one per row and rung; deduplicated across passes through the state file)
# ---------------------------------------------------------------------------------------------
def alarm_key(a):
    return '%s|%s|%s' % (a['id'], a['alarm'], a['slot'])


def alarm_message(a):
    title = {'at-risk': 'At risk', 'missed': 'Missed slot', 'delivery': 'Delivery exception',
             'unconfirmed': 'Publication unconfirmed', 'bad-row': 'Commitment row unreadable'}[a['alarm']]
    lines = ['%s: %s, %s' % (title, a['title'], a['slot_dubai'] or a['slot']),
             'stage: %s; production %s; delivery %s' % (a['stage'], a['production'],
                                                         ', '.join('%s %s' % kv for kv in a['delivery'].items()))]
    if a.get('note'):
        lines.append(a['note'])
    return {'title': '%s: %s' % (title, cut(a['title'], 60)), 'lines': lines,
            'priority': 'high' if a['alarm'] in ('missed', 'delivery', 'at-risk') else 'default', 'tags': 'alarm_clock'}


def cut(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def topic():
    t = os.environ.get('KEEPER_NTFY_TOPIC', '').strip()
    if t:
        return t
    f = os.environ.get('KEEPER_TOPIC_FILE', '/etc/dxb-backup/ntfy-topic')
    try:
        with open(f, encoding='utf-8') as fh:
            return re.sub(r'\s+', '', fh.read()) or None
    except OSError:
        return None


def send(msg, log, now):
    """True when sent or printed (KEEPER_NTFY=off). The topic never reaches a log."""
    if os.environ.get('KEEPER_NTFY', 'on').lower() == 'off':
        log.append('%s ntfy off: %s' % (now.strftime('%H:%MZ'), msg['title']))
        return True
    t = topic()
    if not t:
        log.append('%s ntfy: no topic configured, alarm in the status only: %s' % (now.strftime('%H:%MZ'), msg['title']))
        return False
    url = os.environ.get('KEEPER_NTFY_URL', 'https://ntfy.sh').rstrip('/') + '/' + t
    req = urllib.request.Request(url, data='\n'.join(msg['lines']).encode('utf-8'),
                                 headers={'Title': msg['title'].encode('utf-8').decode('latin-1', 'ignore'),
                                          'Priority': msg['priority'], 'Tags': msg['tags'], 'User-Agent': 'dxb-keeper'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
        log.append('%s ntfy sent: %s' % (now.strftime('%H:%MZ'), msg['title']))
        return True
    except (urllib.error.URLError, OSError) as e:
        log.append('%s ntfy failed (%s): %s' % (now.strftime('%H:%MZ'), str(e).replace(t, '[topic]')[:120], msg['title']))
        return False


def raise_alarms(status, state, now):
    """New alarms only: a row's rung alarms once. Returns (alarms raised now, log lines)."""
    sent = state.setdefault('sent', {})
    log, raised = [], []
    for a in status['rows']:
        if not a.get('alarm'):
            continue
        k = alarm_key(a)
        if k in sent:
            continue
        msg = alarm_message(a)
        ok = send(msg, log, now)
        sent[k] = {'at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'pushed': ok}
        raised.append({'key': k, 'title': msg['title'], 'lines': msg['lines'], 'pushed': ok})
        log.append('%s ALARM %s' % (now.strftime('%H:%MZ'), msg['lines'][0]))
    # Forget alarms for slots more than 2 days old, so the state stays small.
    old = now - timedelta(days=2)
    for k in list(sent):
        t = parse_time(k.rsplit('|', 1)[-1])
        if t and t < old:
            del sent[k]
    return raised, log


# ---------------------------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------------------------
def load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def rows_of(commitments):
    rows = commitments.get('rows') if isinstance(commitments, dict) else commitments
    return [r for r in (rows or []) if isinstance(r, dict)]


def cmd_tick(args):
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    mode = os.environ.get('KEEPER_MODE', 'alarm-only')
    commitments = load_json(args.commitments, None)
    out = args.out
    state_path = args.state or os.path.join(out, 'state.json')
    state = load_json(state_path, {})
    log_path = os.path.join(out, 'keeper.log')
    try:
        with open(log_path, encoding='utf-8') as f:
            log_lines = f.read().splitlines()
    except OSError:
        log_lines = []
    if commitments is None:
        status = {'generated_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'mode': mode,
                  'line': 'overdue commitments: ?, at risk: ? (commitments file unreadable)',
                  'overdue': None, 'at_risk': None, 'six': [], 'rows': [], 'error': 'commitments file unreadable'}
        raised, alog = [], ['%s ERROR commitments file unreadable: %s' % (now.strftime('%H:%MZ'), args.commitments)]
    else:
        status = summarise(rows_of(commitments), now, mode)
        raised, alog = raise_alarms(status, state, now)
    digest = hashlib.sha256(json.dumps(commitments, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12] \
        if commitments is not None else None
    status['commitments_sha'] = digest
    status['alarms_now'] = raised
    state['last_pass'] = status['generated_at']
    log_lines += alog + ['%s %s' % (now.strftime('%Y-%m-%dT%H:%MZ'), status['line'])]
    write(os.path.join(out, 'status.json'), json.dumps(status, ensure_ascii=False, indent=1) + '\n')
    write(os.path.join(out, 'status.txt'), '\n'.join([status['line']] + status['six']) + '\n')
    write(log_path, '\n'.join(log_lines[-LOG_KEEP:]) + '\n')
    write(state_path, json.dumps(state, ensure_ascii=False, indent=1) + '\n')
    print(status['line'])
    for a in raised:
        print('alarm:', a['lines'][0])
    return 2 if status.get('error') else 0


def cmd_line(args):
    if args.status:
        s = load_json(args.status, None)
        if s and s.get('line'):
            age = ''
            t = parse_time(s.get('generated_at'))
            if t:
                age = ' (keeper pass %s, %d min ago)' % (t.strftime('%H:%MZ'), mins(datetime.now(timezone.utc) - t))
            print(s['line'] + age)
            return 0
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    c = load_json(args.commitments, None)
    if c is None:
        print('overdue commitments: ?, at risk: ? (no keeper status and no commitments file)')
        return 2
    print(summarise(rows_of(c), now, 'alarm-only')['line'] + ' (counted locally, not from the keeper)')
    return 0


def cmd_show(args):
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    s = summarise(rows_of(load_json(args.commitments, {})), now, os.environ.get('KEEPER_MODE', 'alarm-only'))
    print(s['line'])
    for l in s['six']:
        print('  ' + l)
    for a in s['rows']:
        print('%-36s %-26s %+6s  %-38s %s' % (cut(a['id'] or '', 36), a['slot_dubai'] or '-',
                                            a['minutes_to_slot'] if a['minutes_to_slot'] is not None else '',
                                            a['stage'], ' '.join('%s:%s' % kv for kv in a['delivery'].items())))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('tick')
    t.add_argument('--commitments', default='newsroom/commitments.json')
    t.add_argument('--state')
    t.add_argument('--out', default=os.path.expanduser('~/backoffice/keeper'))
    t.add_argument('--now')
    l = sub.add_parser('line')
    l.add_argument('--status')
    l.add_argument('--commitments', default='newsroom/commitments.json')
    l.add_argument('--now')
    s = sub.add_parser('show')
    s.add_argument('--commitments', default='newsroom/commitments.json')
    s.add_argument('--now')
    args = ap.parse_args(argv)
    return {'tick': cmd_tick, 'line': cmd_line, 'show': cmd_show}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
