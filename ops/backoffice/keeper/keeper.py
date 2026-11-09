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
                   [--board F] [--releases DIR] [--runs F]                 desk alarms (prod-20261102-build-status-json)
  keeper.py line   [--status F | --commitments F] [--now ISO]                'overdue commitments: N, at risk: M'
  keeper.py show   [--commitments F] [--now ISO]                            the ladder per row, sends nothing
  keeper.py compare --mine S --theirs G --state F [--out F]                 the server's status against GitHub's

Environment: KEEPER_MODE (alarm-only, the default, or fallback), KEEPER_NTFY (on or off), KEEPER_NTFY_TOPIC (the
topic itself, from an Actions secret) or KEEPER_TOPIC_FILE (a root-owned file on the server). The topic is never
printed or logged.

Evidence and coverage (adv-20261107-keeper-blind-and-lost-submit, 7 Nov 2026, with its corrections of 07:30Z and 13:10Z):
  - Publer as a second evidence source, on the server only: with the posts-scope key file KEEPER_PUBLER_KEY_FILE
    (default /etc/dxb-keeper/publer.key; workspace by name, KEEPER_PUBLER_WORKSPACE) each pass reads Publer's scheduled
    and published posts and matches them to rows by network and slot time (within MATCH_MIN). A Publer post confirms a
    platform even when production's entry is missing; the missing entry is a yellow 'evidence gap' alarm, not a red
    'no post'. Publer's list lags (the Danganronpa post was absent from it for six hours while live), so a slot is
    called missed only when two Publer reads at least MISS_GAP_MIN apart both miss it; one empty read is never evidence.
    Post ids stay in the server's private state, never in a public file. Without the key file nothing changes.
  - A claimed slot (production 'claimed' or claimed_by) with no post 20 minutes before it alarms: deliver it, or release
    it with a board line (slot rule: the :30 session owns even hours, the :35 session odd hours).
  - Coverage: the gap since the last published post; past 60 minutes by day (08:00 to 24:00 Dubai) or 120 by night the
    status line reads 'GAP: build or bank; no-build is not an allowed outcome' and alarms once per gap.
  - The bank floor is BANK_MIN ready Reels (6); under it is an alarm like coverage, once a day.
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
MATCH_MIN = 10              # a Publer post within 10 minutes of a row's slot, on the row's network, is that row's post
MISS_GAP_MIN = 10           # two Publer reads this far apart must both miss a post before it counts as missing
T_CLAIM = -20               # a claimed slot with no post 20 minutes before it alarms
ALARM_MAX_AGE_H = 6         # a row whose slot passed more than 6 hours ago is reported, never pushed
COVER_DAY_MIN, COVER_NIGHT_MIN = 60, 120
DELIVERY = ('not_submitted', 'submitting', 'scheduled', 'published', 'failed', 'uncertain')


# ---------------------------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------------------------
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def parse_time(s):
    """ISO time with an offset (Dubai slots: 2026-10-31T00:00+04:00). A time without an offset is Dubai time."""
    if not s:
        return None
    s = str(s).strip()
    d = re.match(r'^(\d{4}-\d\d-\d\d)[ T](\d\d?):(\d\d)\s*(Dubai|GST)\b', s, re.I)
    if d:                                    # Production 2's rows: "2026-11-07 12:15 Dubai" (7 Nov audit: 36 rows unread)
        s = '%sT%02d:%s+04:00' % (d.group(1), int(d.group(2)), d.group(3))
    w = re.match(r'^(?:[A-Za-z]{3},?\s+)?(\d\d?)\s+([A-Za-z]{3})[a-z]*\.?(?:\s+(\d{4}))?,?\s+(\d\d?):(\d\d)\s*(Dubai|GST)\b', s, re.I)
    if w and w.group(2).title() in MONTHS:   # "Sun 08 Nov 22:30 Dubai (18:30Z)" (Production 2 from 8 Nov): the keeper read
        mo, day = MONTHS.index(w.group(2).title()) + 1, int(w.group(1))   # none of them on 9 Nov's build-night tick
        if w.group(3):
            year = int(w.group(3))
        else:                                # no year written: the year that puts the slot nearest to now
            ref = datetime.now(timezone.utc)
            year = min((ref.year - 1, ref.year, ref.year + 1),
                       key=lambda y: abs((datetime(y, mo, min(day, 28), tzinfo=timezone.utc) - ref).days))
        s = '%04d-%02d-%02dT%02d:%s+04:00' % (year, mo, day, int(w.group(4)), w.group(5))
    s = s.replace('Z', '+00:00')
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
def assess(row, now, mode, pub=None):
    """One row's place on the ladder. Returns a dict the status, the alarms and the tests read. pub: the Publer
    evidence for this row ({'seen': {platform: state}, 'confirmed_missing': bool, 'read': bool}), or None."""
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
    gap_platforms = []
    if pub and pub.get('seen'):                           # Publer's own state confirms what production did not write
        for p, st in pub['seen'].items():
            have = a['delivery'].get(p)
            if have is None:
                continue
            rank = {'not_submitted': 0, 'submitting': 1, 'uncertain': 1, 'scheduled': 2, 'published': 3}
            if st in ('scheduled', 'published') and rank.get(have, 0) < rank[st]:
                if have in ('not_submitted', 'submitting', 'uncertain'):
                    gap_platforms.append(p)
                a['delivery'][p] = st
        if gap_platforms:
            a['evidence_gap'] = gap_platforms
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
        if a.get('evidence_gap'):
            a['alarm'] = 'evidence-gap'
            a['note'] = 'Publer shows it on %s; production wrote no entry: write it (presubmit.py published)' % \
                ', '.join(a['evidence_gap'])
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
            if a.get('evidence_gap'):
                a['alarm'] = 'evidence-gap'
                a['note'] = 'Publer shows it scheduled on %s; production wrote no entry: record the result' % \
                    ', '.join(a['evidence_gap'])
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
        if to_slot <= -T_CLAIM and (a['production'] == 'claimed' or row.get('claimed_by')):
            a['alarm'] = 'claim'
            a['note'] = 'claimed by %s with no post 20 minutes before the slot: deliver it, or release it with a board ' \
                        'line (the :30 session owns even hours, the :35 session odd hours)' % (row.get('claimed_by') or 'a session')
    elif to_slot > 0:
        a['stage'] = 'T-15: no evidence it is scheduled'
        a['commitment'] = 'at_risk'
        a['alarm'] = 'at-risk'
    elif pub and pub.get('read') and not pub.get('confirmed_missing'):
        a['stage'] = 'slot passed, Publer read once'          # one empty read is not evidence (13:10Z note)
        a['commitment'] = 'at_risk'
        a['note'] = 'not in Publer on one read; a second read %d minutes later decides' % MISS_GAP_MIN
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


def summarise(rows, now, mode, pubs=None):
    pubs = pubs or {}
    assessed = [assess(r, now, mode, pubs.get(r.get('id'))) for r in rows]
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
             'unconfirmed': 'Publication unconfirmed', 'bad-row': 'Commitment row unreadable',
             'evidence-gap': 'Evidence gap', 'claim': 'Claimed slot, no post'}[a['alarm']]
    lines = ['%s: %s, %s' % (title, a['title'], a['slot_dubai'] or a['slot']),
             'stage: %s; production %s; delivery %s' % (a['stage'], a['production'],
                                                         ', '.join('%s %s' % kv for kv in a['delivery'].items()))]
    if a.get('note'):
        lines.append(a['note'])
    return {'title': '%s: %s' % (title, cut(a['title'], 60)), 'lines': lines,
            'priority': 'high' if a['alarm'] in ('missed', 'delivery', 'at-risk', 'claim') else 'default',
            'tags': 'warning' if a['alarm'] == 'evidence-gap' else 'alarm_clock'}


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
        t = parse_time(a.get('slot'))
        if t and now - t > timedelta(hours=ALARM_MAX_AGE_H):
            continue                       # an old row stays in the status, it never pages (one push per live slot)
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
# Desk alarms (prod-20261102-build-status-json, Mohammad 2 Nov 2026): 01:20 Dubai with no build started line,
# 04:15 Dubai with no release note, 90 minutes without a Production 2 hourly watch run. Each input is optional; a
# missing input gives a status line that says so and never an alarm. One push per gap (deduplicated in the state).
# ---------------------------------------------------------------------------------------------
STARTED_AT = (1, 20)        # Dubai: the build desk starts 01:07
RELEASE_AT = (4, 15)        # Dubai: the release is 04:00
WINDOW_END = (6, 0)         # Dubai: the build night's alarms stop here
WATCH_GAP_MIN = 90
LOG_STALE_MIN = 24 * 60      # a log with no run for a day is not being written: report, never alarm


def _night(now):
    """(release date as YYYYMMDD and YYYY-MM-DD, Dubai time) for the build night now falls in."""
    d = now.astimezone(DUBAI)
    return d.strftime('%Y%m%d'), d.strftime('%Y-%m-%d'), d


def _past(d, hm):
    return (d.hour, d.minute) >= hm


def started_line(board, ymd):
    j = board if isinstance(board, dict) else {}
    want = 'build-%s-started' % ymd
    for h in j.get('handoffs') or []:
        if isinstance(h, dict) and str(h.get('id', '')).startswith(want):
            return True
    return False


def last_watch(runs_path):
    last = None
    try:
        with open(runs_path, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if not str(r.get('run', '')).startswith('hourly-watch'):
                    continue
                t = parse_time(str(r.get('at', '')))
                if t and (last is None or t > last):
                    last = t
    except OSError:
        return None, False
    return last, True


def desk_checks(now, board_path=None, releases=None, runs=None):
    """([status lines], [alarms as {key, title, lines}])."""
    if not (board_path or releases or runs):
        return [], []                            # not asked: the status is exactly as before
    ymd, ymd_dash, d = _night(now)
    lines, alarms = [], []
    in_night = _past(d, (0, 0)) and not _past(d, WINDOW_END)
    # 1. started line
    if board_path:
        board = load_json(board_path, None)
        if board is None:
            lines.append('build started line: board not readable')
        else:
            ok = started_line(board, ymd)
            lines.append('build started line %s: %s' % (ymd, 'present' if ok else 'missing'))
            if not ok and in_night and _past(d, STARTED_AT):
                alarms.append({'key': 'desk|started|' + ymd, 'title': 'Build desk: no started line',
                               'lines': ['Build desk: no started line build-%s-started at %s Dubai' % (ymd, d.strftime('%H:%M')),
                                         'The 01:07 Dubai run did not write its line on dxb-queue desk/board.md.']})
    else:
        lines.append('build started line: board not read (no token for dxb-queue)')
    # 2. release note
    if releases:
        f = os.path.join(releases, ymd_dash + '.md')
        ok = os.path.exists(f)
        lines.append('release note %s: %s' % (ymd_dash, 'present' if ok else 'missing'))
        if not ok and in_night and _past(d, RELEASE_AT):
            alarms.append({'key': 'desk|release|' + ymd, 'title': 'Build desk: no release note',
                           'lines': ['Build desk: no ops/build/releases/%s.md on main at %s Dubai' % (ymd_dash, d.strftime('%H:%M')),
                                     'The 04:00 release (or its skipped-release note) is missing.']})
    # 3. Production 2 hourly watch
    if runs:
        last, readable = last_watch(runs)
        if not readable:
            lines.append('hourly watch: runs log not readable')
        elif last is None:
            lines.append('hourly watch: no run logged')
        else:
            gap = mins(now - last)
            if gap >= LOG_STALE_MIN:             # nobody is logging here: say so, never page on it
                lines.append('hourly watch: log stale, last run %s, %d min ago (is Production 2 logging to '
                             'newsroom/helper-runs.jsonl?)' % (dubai(last), gap))
                return lines, alarms
            lines.append('hourly watch: last run %s, %d min ago' % (dubai(last), gap))
            if gap >= WATCH_GAP_MIN:
                alarms.append({'key': 'desk|watch|' + last.strftime('%Y-%m-%dT%H:%MZ'),
                               'title': 'Hourly watch: %d min without a run' % gap,
                               'lines': ['Hourly watch: no run logged for %d min (last %s Dubai)' % (gap, dubai(last)),
                                         'Production 2 logs each run in newsroom/helper-runs.jsonl.']})
    return lines, alarms


def raise_desk(alarms, state, now):
    sent = state.setdefault('sent_desk', {})
    log, raised = [], []
    for a in alarms:
        if a['key'] in sent:
            continue
        ok = send({'title': a['title'], 'lines': a['lines'], 'priority': 'high', 'tags': 'alarm_clock'}, log, now)
        sent[a['key']] = {'at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'pushed': ok}
        raised.append({'key': a['key'], 'title': a['title'], 'lines': a['lines'], 'pushed': ok})
        log.append('%s ALARM %s' % (now.strftime('%H:%MZ'), a['lines'][0]))
    old = now - timedelta(days=3)
    for k, v in list(sent.items()):
        t = parse_time(v.get('at', ''))
        if t and t < old:
            del sent[k]
    return raised, log



# ---------------------------------------------------------------------------------------------
# Publer as a second evidence source (adv-20261107-keeper-blind-and-lost-submit item 2, with the 07:30Z and 13:10Z
# corrections). Server only: the key file is root-owned on dxb-render-1. Post ids stay in the private state.
# ---------------------------------------------------------------------------------------------
PUBLER_API = 'https://app.publer.com/api/v1'
NETWORKS = {'instagram': 'instagram', 'twitter': 'x', 'x': 'x', 'threads': 'threads'}


def publer_key():
    f = os.environ.get('KEEPER_PUBLER_KEY_FILE', '/etc/dxb-keeper/publer.key')
    try:
        with open(f, encoding='utf-8') as fh:
            k = re.sub(r'\s+', '', fh.read())
        return k or None
    except OSError:
        return None


def _publer_get(path, key, workspace=None, timeout=30):
    headers = {'Authorization': 'Bearer-API ' + key, 'User-Agent': 'dxb-keeper', 'Accept': 'application/json'}
    if workspace:
        headers['Publer-Workspace-Id'] = workspace
    req = urllib.request.Request(PUBLER_API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8') or 'null')


class PublerReader:
    """Reads scheduled and published posts between two times. fetch() returns [{'network', 'state', 'at', 'id',
    'link'}] or raises; errors are reported with the key and ids removed."""

    def __init__(self, key, workspace_name=None, get=None):
        self.key, self.get = key, get or _publer_get
        self.workspace_name = workspace_name or os.environ.get('KEEPER_PUBLER_WORKSPACE', 'The Digi-Lounge')
        self.workspace = os.environ.get('KEEPER_PUBLER_WORKSPACE_ID') or None

    def _workspace(self):
        if self.workspace:
            return self.workspace
        ws = self.get('/workspaces', self.key)
        ws = ws.get('workspaces', ws) if isinstance(ws, dict) else ws
        for w in ws or []:
            if str(w.get('name', '')).strip().lower() == self.workspace_name.strip().lower():
                self.workspace = str(w.get('id'))
                return self.workspace
        if ws and len(ws) == 1:
            self.workspace = str(ws[0].get('id'))
            return self.workspace
        raise RuntimeError('workspace %r not found' % self.workspace_name)

    def fetch(self, start, end):
        ws, out = self._workspace(), []
        q = 'state[]=scheduled&state[]=published&from=%s&to=%s' % (start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                                  end.strftime('%Y-%m-%dT%H:%M:%SZ'))
        for page in range(0, 10):
            r = self.get('/posts?%s&page=%d' % (q, page), self.key, ws)
            posts = (r or {}).get('posts') or []
            for p in posts:
                net = NETWORKS.get(str(p.get('network') or p.get('provider') or '').lower())
                at = parse_time(str(p.get('scheduled_at') or p.get('published_at') or ''))
                if net and at:
                    st = str(p.get('state') or '').lower()
                    out.append({'network': net, 'state': 'published' if st.startswith('publish') else 'scheduled'
                                if st.startswith('schedul') else st, 'at': at, 'id': str(p.get('id') or ''),
                                'link': p.get('post_link') or '', 'labels': label_names(p.get('labels'))})
            total = (r or {}).get('total_pages')
            if not posts or (total is not None and page + 1 >= int(total)):
                break
        return out


def publer_evidence(rows, posts, state, now):
    """{row id: {'seen': {platform: state}, 'read': True, 'confirmed_missing': bool}} and the misses kept in state
    (two reads MISS_GAP_MIN apart must both miss a platform). Ids go to state['publer_ids'] (private, server only)."""
    misses = state.setdefault('publer_miss', {})
    ids = state.setdefault('publer_ids', {})
    out = {}
    for r in rows:
        slot = parse_time(r.get('slot'))
        if not slot or not r.get('id'):
            continue
        seen, missing_now = {}, []
        for p in platforms_of(r):
            best = None
            for post in posts:
                if post['network'] == p and abs(mins(post['at'] - slot)) <= MATCH_MIN:
                    if best is None or (post['state'] == 'published' and best['state'] != 'published'):
                        best = post
            k = '%s|%s' % (r['id'], p)
            if best:
                seen[p] = best['state']
                ids[k] = {'id': best['id'], 'seen': now.strftime('%Y-%m-%dT%H:%M:%SZ')}
                misses.pop(k, None)
            elif slot - timedelta(minutes=30) <= now:      # only from T-30 does a missing post matter
                first = parse_time(misses.get(k))
                if first is None:
                    misses[k] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
                    missing_now.append((p, False))
                else:
                    missing_now.append((p, mins(now - first) >= MISS_GAP_MIN))
        confirmed = bool(missing_now) and all(c for _, c in missing_now)
        out[r['id']] = {'seen': seen, 'read': True, 'confirmed_missing': confirmed}
    old = now - timedelta(days=3)
    for d in (misses, ids):
        for k in list(d):
            t = parse_time(d[k] if isinstance(d[k], str) else d[k].get('seen'))
            if t and t < old:
                del d[k]
    return out


def label_names(x):
    out = []
    for l in x or []:
        out.append(str(l.get('name', '')) if isinstance(l, dict) else str(l))
    return [l.strip() for l in out if l and l.strip()][:12]


class PayloadReader:
    """Posts from the server's Publer read (server-summary.json, sent with the repository_dispatch; build 10 Nov 2026):
    GitHub's keeper has no Publer key, so it takes the server's read when it is fresh. No ids in it."""

    def __init__(self, summary):
        self.summary = summary or {}

    def fetch(self, start, end):
        out = []
        for p in self.summary.get('posts') or []:
            at = parse_time(str(p.get('at') or ''))
            if at and start <= at <= end and p.get('network') in ('instagram', 'x', 'threads'):
                out.append({'network': p['network'], 'state': p.get('state', ''), 'at': at, 'id': '', 'link': '',
                            'labels': label_names(p.get('labels'))})
        return out


LAST_READ = {}               # the last read of this pass: {'at', 'posts'} or {'at', 'error'} (for server-summary.json)


def server_summary(now, line):
    """What the server sends GitHub's keeper: its Publer read without ids or links."""
    posts = [{'at': p['at'].strftime('%Y-%m-%dT%H:%M:%SZ'), 'network': p['network'], 'state': p['state'],
              'labels': p.get('labels') or []} for p in LAST_READ.get('posts') or []]
    return {'generated_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'publer_read_at': LAST_READ['at'] if LAST_READ.get('posts') is not None else None,
            'publer': line, 'posts': posts if LAST_READ.get('posts') is not None else None,
            'code': os.environ.get('KEEPER_CODE_REV') or None}


def read_publer(rows, state, now, reader=None):
    """(evidence per row or {}, status line, latest published time seen in Publer or None)."""
    LAST_READ.clear()
    if reader is None:
        key = publer_key()
        if not key:
            return {}, 'publer: not read (no key file; evidence from production only)', None
        reader = PublerReader(key)
    try:
        posts = reader.fetch(now - timedelta(hours=36), now + timedelta(hours=48))
    except Exception as e:                                  # never blocks the pass; the key never reaches the text
        msg = re.sub(r'[A-Za-z0-9_\-]{24,}', '[redacted]', str(e))[:120]
        LAST_READ.update({'at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'error': msg})
        return {}, 'publer: read failed (%s); evidence from production only' % msg, None
    LAST_READ.update({'at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'posts': posts})
    ev = publer_evidence(rows, posts, state, now)
    pub = [p['at'] for p in posts if p['state'] == 'published' and p['at'] <= now]
    n_s = sum(1 for p in posts if p['state'] == 'scheduled')
    return ev, 'publer: read %s, %d published and %d scheduled in the window' % (now.strftime('%H:%MZ'), len(pub), n_s), \
        (max(pub) if pub else None)


# ---------------------------------------------------------------------------------------------
# Coverage (item 5) and the bank floor (item 6)
# ---------------------------------------------------------------------------------------------
def last_published(status_rows, rows, publer_last=None, now=None):
    """Latest post time: a row's delivery 'at', else the slot of a row published (or scheduled on every platform with
    its slot passed), else Publer's own latest published post."""
    by_id = {r.get('id'): r for r in rows}
    best = publer_last
    now = now or datetime.now(timezone.utc)
    for a in status_rows:
        slot = parse_time(a.get('slot'))
        delivered = a['stage'] == 'published' or a.get('commitment') in ('fulfilled_on_time', 'fulfilled_late')
        # a row scheduled on every platform whose slot has passed counts as a post for coverage, even before
        # production confirms it published (the confirmation gap is its own alarm, 'publication unconfirmed')
        went = a['stage'] in ('scheduled', 'publication unconfirmed') and slot is not None and slot <= now
        if not (delivered or went):
            continue
        r = by_id.get(a['id']) or {}
        ats = [parse_time(d.get('at')) for d in delivery_of(r).values() if d.get('at')]
        t = max([x for x in ats if x], default=None) or parse_time(r.get('slot'))
        if t and (best is None or t > best):
            best = t
    return best


def digest_note(path, now):
    """The watch's branch head for the coverage alarm (adv-20261108-stories-tab addendum_0545): a gap is never blamed
    on the server's digest without the seq the branch actually held. path: watch/digest.json fetched from the
    watch-digest branch. Returns ('watch-digest branch: seq N at HH:MM Dubai, M min old', seq) or a 'not read' line."""
    if not path:
        return None, None
    d = load_json(path, None)
    if not isinstance(d, dict) or d.get('seq') is None:
        return 'watch-digest branch: not read', None
    t = parse_time(d.get('generated_at'))
    age = ', %d min old' % mins(now - t) if t else ''
    return 'watch-digest branch: seq %s at %s%s' % (d.get('seq'), dubai(t) if t else '?', age), d.get('seq')


def coverage(last, now, digest_line=None):
    """(line, gap minutes or None, over the limit?)."""
    if last is None:
        return 'coverage: no published post on record', None, False
    gap = mins(now - last)
    limit = COVER_NIGHT_MIN if now.astimezone(DUBAI).hour < 8 else COVER_DAY_MIN
    if gap > limit:
        return ('coverage: GAP %d min since the last post (%s); build or bank; no-build is not an allowed outcome%s'
                % (gap, dubai(last), ('; ' + digest_line) if digest_line else '')), gap, True
    return 'coverage: last post %s, %d min ago (limit %d)' % (dubai(last), gap, limit), gap, False

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


BANK_MIN = 6                # ready Reels (adv-20261107-keeper-blind-and-lost-submit item 6; was 3)


def _verified_source(cell):
    """A bank row's Source cell counts when it names a primary (adv-20261108-no-decision-stalls, 9 Nov 2026): not
    empty, not '?', 'unverified', 'none' or '-', and not marked 'no primary'."""
    c = (cell or '').strip().lower()
    return bool(c) and not c.startswith(('?', 'unverified', 'none', '-')) and 'no primary' not in c


DATED = re.compile(r'release day|\bdated\b|«باقي|intro counts|only on|\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* \d{1,2} '
                   r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* 20\d\d', re.I)


def _dated(cell):
    """A bank row tied to one day (an anniversary's release day, a series countdown, 'dated 10 Nov only') cannot fill
    any gap, so the floor does not count it (release 2026-11-10). 'what would date it' text such as 'Nintendo results in
    early November' is a staleness note, not a fixed day."""
    return bool(DATED.search(cell or ''))


def bank_line(commitments_path):
    """Finished Reels in the evergreen bank (newsroom/evergreen.md, first table, Status starting 'ready').
    Under BANK_MIN is an at-risk line (adv-20261105-p2-audit-fixes, item 5). Since 9 Nov a row counts only with a
    template and a verified source (adv-20261108-no-decision-stalls item 3); a table without a Source column counts
    as before, with a note. Returns (count or None, line)."""
    path = os.path.join(os.path.dirname(os.path.abspath(commitments_path)), 'evergreen.md')
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except OSError:
        return None, 'bank: not read (no newsroom/evergreen.md)'
    table = text.split('\n## ', 1)[0]
    head, n, skipped, dated = None, 0, 0, 0
    for row in table.splitlines():
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if head is None and cells and cells[0].lower() == 'name':
            head = [c.lower() for c in cells]
            continue
        if len(cells) < 5 or not cells[-1].lower().startswith('ready'):
            continue
        if head and 'source' in head and len(cells) == len(head):
            tpl = cells[head.index('template')] if 'template' in head else 'x'
            if not tpl.strip() or not _verified_source(cells[head.index('source')]):
                skipped += 1
                continue
        if head and 'dates it' in head and len(cells) == len(head) and _dated(cells[head.index('dates it')]):
            dated += 1
            continue
        n += 1
    note = '' if head and 'source' in head else ' (no Source column: sources not checked)'
    if skipped:
        note += ', %d ready without a verified source not counted' % skipped
    if dated:
        note += ', %d ready but tied to one day not counted' % dated
    if n < BANK_MIN:
        return n, 'bank: at risk, %d undated ready Reels (minimum %d)%s' % (n, BANK_MIN, note)
    return n, 'bank: %d undated ready Reels%s' % (n, note)


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
        rows = rows_of(commitments)
        server = load_json(getattr(args, 'server', None), None) if getattr(args, 'server', None) else None
        sat = parse_time(str((server or {}).get('publer_read_at') or ''))
        if os.environ.get('KEEPER_PUBLER', 'on').lower() == 'off':
            pubs, pline, plast = {}, 'publer: off', None
        elif server and sat and (server or {}).get('posts') is not None and mins(now - sat) <= SERVER_FRESH_MIN:
            pubs, pline, plast = read_publer(rows, state, now, PayloadReader(server))
            LAST_READ['at'] = sat.strftime('%Y-%m-%dT%H:%M:%SZ')
            pline = pline.replace('publer: read %s' % now.strftime('%H:%MZ'),
                                  "publer: the server's read of %s" % sat.strftime('%H:%MZ'), 1)
        else:
            pubs, pline, plast = read_publer(rows, state, now)
        write(os.path.join(out, 'server-summary.json'), json.dumps(server_summary(now, pline), ensure_ascii=False) + '\n')
        status = summarise(rows, now, mode, pubs)
        raised, alog = raise_alarms(status, state, now)
        status['bank_ready'], bl = bank_line(args.commitments)
        status['six'].append(bl)
        status['six'].append(pline)
        dline, dseq = digest_note(getattr(args, 'digest', None), now)
        if dline:
            status['watch_digest'] = {'line': dline, 'seq': dseq}
        cline, cgap, cover_over = coverage(last_published(status['rows'], rows, plast, now), now, dline)
        status['coverage'] = cline
        status['coverage_gap_min'] = cgap
        status['six'].insert(0, cline)
        extra = []
        if cover_over:
            lp = last_published(status['rows'], rows, plast, now)
            extra.append({'key': 'cover|' + lp.strftime('%Y-%m-%dT%H:%MZ'), 'title': 'Coverage gap: %d min' % cgap,
                          'lines': [cline, 'Production 2: the next run ends with a scheduled submit or a banked piece queued.']})
        if status['bank_ready'] is not None and status['bank_ready'] < BANK_MIN:
            extra.append({'key': 'bank|%s|%d' % (now.astimezone(DUBAI).strftime('%Y%m%d'), status['bank_ready']),
                          'title': 'Bank under the floor: %d ready' % status['bank_ready'],
                          'lines': [bl, 'Any run that builds no news builds a bank piece (idle card, mandatory).']})
        if os.environ.get('KEEPER_COVER_ALARMS', 'on').lower() != 'off':   # the server sets off: GitHub's keeper pushes
            xr, xl = raise_desk(extra, state, now)
            raised, alog = list(raised) + xr, list(alog) + xl
    dlines, dalarms = desk_checks(now, args.board, args.releases, args.runs)
    draised, dlog = raise_desk(dalarms, state, now)
    status['desk'] = dlines
    status.setdefault('six', [])
    status['six'] += dlines
    raised = list(raised) + draised
    alog = list(alog) + dlog
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
            if s.get('coverage'):
                print(s['coverage'])
            return 0
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    c = load_json(args.commitments, None)
    if c is None:
        print('overdue commitments: ?, at risk: ? (no keeper status and no commitments file)')
        return 2
    st = summarise(rows_of(c), now, 'alarm-only')
    print(st['line'] + ' (counted locally, not from the keeper)')
    print(coverage(last_published(st['rows'], rows_of(c), None, now), now)[0])
    return 0


def cmd_show(args):
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    s = summarise(rows_of(load_json(args.commitments, {})), now, os.environ.get('KEEPER_MODE', 'alarm-only'))
    s['six'].append(bank_line(args.commitments)[1])
    print(s['line'])
    for l in s['six']:
        print('  ' + l)
    for a in s['rows']:
        print('%-36s %-26s %+6s  %-38s %s' % (cut(a['id'] or '', 36), a['slot_dubai'] or '-',
                                            a['minutes_to_slot'] if a['minutes_to_slot'] is not None else '',
                                            a['stage'], ' '.join('%s:%s' % kv for kv in a['delivery'].items())))
    return 0


# ---------------------------------------------------------------------------------------------
# Two keepers (addendum_0615): the server's timer is the clock; GitHub's keeper.yml is the secondary
# ---------------------------------------------------------------------------------------------
SERVER_FRESH_MIN = 20       # GitHub's keeper takes the server's Publer read when it is this fresh
STALE_MIN = 15              # GitHub's status older than this, against the server's own pass: alarm
CMP_WINDOW_MIN = 10         # two passes this close (and on the same commitments) must agree


def compare(mine, theirs, state, now):
    """Compare the server's status with GitHub's (keeper-status). Returns (line, alarm or None). A disagreement alarms
    only when it holds on two server passes in a row (a row can cross a rung between the two passes); a stale or
    unreadable GitHub status alarms once an hour. The server can read GitHub's public branch; GitHub cannot read the
    server, so the comparison runs here."""
    cmp = state.setdefault('compare', {})
    if not theirs or not theirs.get('generated_at'):
        line, key = 'compare: GitHub keeper status unreadable', 'unreadable'
    else:
        tm, tt = parse_time(mine.get('generated_at')) or now, parse_time(theirs['generated_at'])
        age = mins(tm - tt)
        if age > STALE_MIN:
            line, key = 'compare: GitHub keeper status is %d min old (its schedule was delayed or dropped)' % age, 'stale'
        elif abs(age) <= CMP_WINDOW_MIN and mine.get('commitments_sha') == theirs.get('commitments_sha') and \
                (mine.get('overdue'), mine.get('at_risk')) != (theirs.get('overdue'), theirs.get('at_risk')):
            line = 'compare: keepers disagree: server "%s", GitHub "%s"' % (mine.get('line'), theirs.get('line'))
            key = 'disagree|%s|%s' % (mine.get('line'), theirs.get('line'))
        else:
            cmp['pending'] = None
            return 'compare: GitHub keeper agrees (%s, %+d min)' % (theirs.get('line'), -age), None
    if key.startswith('disagree'):
        if cmp.get('pending') != key:                 # first sighting: wait one pass
            cmp['pending'] = key
            return line + ' (once; alarms if it holds on the next pass)', None
    last = parse_time((cmp.get('alarmed') or {}).get(key.split('|')[0]))
    if last and now - last < timedelta(minutes=60):
        return line + ' (alarmed within the hour)', None
    cmp.setdefault('alarmed', {})[key.split('|')[0]] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    title = {'unreadable': 'Keeper check: GitHub status unreadable', 'stale': 'Keeper check: GitHub keeper stale',
             'disagree': 'Keepers disagree'}[key.split('|')[0]]
    return line, {'title': title, 'lines': [line, 'server: %s' % mine.get('line')], 'priority': 'default',
                  'tags': 'alarm_clock'}


def cmd_compare(args):
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    mine = load_json(args.mine, {})
    theirs = load_json(args.theirs, None)
    state = load_json(args.state, {})
    line, alarm = compare(mine, theirs, state, now)
    log = []
    if alarm:
        send(alarm, log, now)
    write(args.state, json.dumps(state, ensure_ascii=False, indent=1) + '\n')
    if args.out:
        write(args.out, line + '\n')
    try:
        with open(os.path.join(os.path.dirname(args.state), 'keeper.log'), 'a', encoding='utf-8') as f:
            for l in log + ['%s %s' % (now.strftime('%Y-%m-%dT%H:%MZ'), line)]:
                f.write(l + '\n')
    except OSError:
        pass
    print(line)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('tick')
    t.add_argument('--commitments', default='newsroom/commitments.json')
    t.add_argument('--state')
    t.add_argument('--out', default=os.path.expanduser('~/backoffice/keeper'))
    t.add_argument('--now')
    t.add_argument('--board', help='dxb-queue desk/board.json (optional)')
    t.add_argument('--releases', help='ops/build/releases (optional)')
    t.add_argument('--runs', help='newsroom/helper-runs.jsonl (optional)')
    t.add_argument('--server', help="server-summary.json from dxb-render-1's repository_dispatch (optional): its Publer read")
    t.add_argument('--digest', help='watch/digest.json from the watch-digest branch (optional): the coverage alarm names its seq')
    l = sub.add_parser('line')
    l.add_argument('--status')
    l.add_argument('--commitments', default='newsroom/commitments.json')
    l.add_argument('--now')
    c = sub.add_parser('compare')
    c.add_argument('--mine', required=True)
    c.add_argument('--theirs', required=True)
    c.add_argument('--state', required=True)
    c.add_argument('--out')
    c.add_argument('--now')
    s = sub.add_parser('show')
    s.add_argument('--commitments', default='newsroom/commitments.json')
    s.add_argument('--now')
    args = ap.parse_args(argv)
    return {'tick': cmd_tick, 'line': cmd_line, 'show': cmd_show, 'compare': cmd_compare}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
