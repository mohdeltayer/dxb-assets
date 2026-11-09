"""The work order and the hop alarms (adv-20261109-coordination-in-code items 1 and 2; build 10 Nov 2026).

Mohammad, 9 Nov 20:05 Dubai: he was the only component reliably reading both accounts; every failure that day was a
session not reading what another wrote. Decision: the server coordinates, sessions execute.

The clock is dxb-render-1's keeper timer (every 5 minutes; GitHub's own */5 schedule ran keeper.yml only every 4 to 8
hours on 8 and 9 Nov). Every 10 minutes, and at :27, server_tick.sh sends keeper.yml a repository_dispatch carrying its
Publer read (times, networks, states and labels; never a post id). keeper.yml reads the board, desk/orders/ and
desk/mirror.json of dxb-queue with its read-only token, the watch-digest branch, newsroom/commitments.json and the
format ledger, and runs `keeper.py workorder`, which writes into keeper-status:

  keeper/work-order.json and keeper/work-order.md   once an hour, from :25 Dubai (the ":30 work order"), in this order:
      1 alarms to clear first; 2 Mohammad's orders (T0 first); 3 open handoffs to Production 2, oldest first, with due;
      4 the digest head seq and the previous run's scout leads and rejections; 5 the next slot due under the cadence;
      6 the caps (evergreen allowed and when it reopens, numbers allowed, the card-led window).
  keeper/hop.json                                    every pass: the hop alarms now.

Hop alarms (each one: a line at the top of the work order that the next Production 2 run clears first, one ntfy push
per alarm key, a row in keeper-status status.json `hop`):
  unacked    a handoff to Production 2 that no Production 2 line names after 20 minutes
  no-line    no Production 2 board line in the hour by :50 Dubai
  no-ids     a Production 2 'scheduled:' line without the Publer post ids (one per platform; the board is private)
  caps       a post (published or scheduled) outside the caps: a third template in a row, two evergreen in a row,
             evergreen within 3 hours of another between 08:00 and 24:00 Dubai, card-led over 2 in 6, a template over
             4 in a Dubai day
  mirror     desk/mirror.json older than 2 hours
  digest     a Production 2 line that read a digest seq below the branch head at its time
  publer     keeper coverage stale: no Publer read by the server in 15 minutes

The work order is public (keeper-status is a branch of dxb-assets): it carries ids of handoffs and orders, titles,
times and rule names, never a Publer id, a link to a post, a token or a card's body. The Production 1 inbox mirror
copies it to dxb-queue desk/work-order.json and desk/work-order.md.

    python3 workorder.py --board b.json [--orders dir] [--mirror m.json] [--digest d.json] [--digests dir]
                         [--server s.json] [--commitments c.json] [--ledger f.json] [--out dir] [--now ISO] [--force]
"""
import argparse, datetime as dt, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
for p in (os.path.join(ROOT, 'templates'), os.path.join(ROOT, 'ops')):
    if p not in sys.path:
        sys.path.insert(0, p)

UTC = dt.timezone.utc
DUBAI = dt.timezone(dt.timedelta(hours=4))
P2 = re.compile(r'production[\s_-]*2', re.I)
SUPERSEDED = re.compile(r'\b(supersed\w*|withdrawn|closed|replaced by)\b', re.I)
CLOSING = re.compile(r'\b(scheduled|published|declined|dropped|superseded|rejected|done)\b', re.I)
ACK_HOP_MIN = 20             # a handoff to Production 2 not named by a Production 2 line after 20 minutes
LINE_BY_MIN = 50             # a Production 2 board line in the hour by :50 Dubai
MIRROR_MAX_H = 2             # desk/mirror.json older than this
PUBLER_MAX_MIN = 15          # the server's last Publer read older than this
WRITE_FROM_MIN = 25          # the hourly work order is written by the first pass from :25 Dubai
RULE_FROM = '2026-11-09T16:25:00Z'   # build start (build-20261110-started): no-ids and caps alarms look at lines and posts from here on
EVERGREEN_GAP_H = 3          # CLAUDE.md "Evergreen spacing and the news search" (9 Nov 2026)
SPACING = {'day': 30, 'night': 60}
MAX_GAP = {'day': 60, 'night': 120}
ID_TOKEN = re.compile(r'\b[0-9a-f]{24}\b|\b\d{9,}\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
ID6 = re.compile(r'\b(?:ig|x|th|instagram|threads):[0-9A-Za-z]{6}\b')   # presubmit.py line: last six of each id
SCHEDULED_LINE = re.compile(r'(?:^|[\s.;(])scheduled:\s', re.I)


# ----------------------------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------------------------
def t(s):
    if isinstance(s, dt.datetime):
        return s if s.tzinfo else s.replace(tzinfo=UTC)
    try:
        x = dt.datetime.fromisoformat(str(s).strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    return x if x.tzinfo else x.replace(tzinfo=UTC)


def iso(x):
    return x.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ') if x else None


def dub(x, day=True):
    if not x:
        return '?'
    d = x.astimezone(DUBAI)
    return d.strftime('%a %d %b %H:%M Dubai') if day else d.strftime('%H:%M')


def cut(s, n):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def scrub(s):
    """No post ids or links in the public work order."""
    s = ID_TOKEN.sub('[id]', str(s or ''))
    return re.sub(r'https?://(?:www\.)?(?:publer\.com|instagram\.com|x\.com|twitter\.com|threads\.(?:net|com))\S*',
                  '[post link]', s)


def load(path, default):
    if not path:
        return default
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def band(x):
    return 'night' if x.astimezone(DUBAI).hour < 8 else 'day'


def text_of(h, keys=('id', 'done', 'next', 'evidence', 'ack')):
    v = []
    for k in keys:
        x = h.get(k, '')
        v.append(' '.join(map(str, x)) if isinstance(x, list) else str(x))
    return ' '.join(v)


def handoffs(board):
    return [h for h in (board or {}).get('handoffs', []) if isinstance(h, dict) and h.get('id')]


def p2_lines(board):
    return sorted((h for h in handoffs(board) if P2.search(str(h.get('from', ''))) and t(h.get('at'))),
                  key=lambda h: t(h['at']))


# ----------------------------------------------------------------------------------------------------------------
# posts: the server's Publer read first, the commitments and the format ledger when there is none
# ----------------------------------------------------------------------------------------------------------------
def _labels(x):
    out = []
    for l in x or []:
        out.append(str(l.get('name', '')) if isinstance(l, dict) else str(l))
    return [l.strip() for l in out if l and l.strip()]


def posts_from_server(server):
    """Publer posts grouped by minute: [{'at', 'state', 'labels', 'networks'}] (a Reel goes to three networks)."""
    groups = {}
    for p in (server or {}).get('posts', []) or []:
        at = t(p.get('at'))
        if not at:
            continue
        k = at.strftime('%Y-%m-%dT%H:%M')
        g = groups.setdefault(k, {'at': at, 'state': 'scheduled', 'labels': set(), 'networks': {}})
        g['networks'][p.get('network', '?')] = p.get('state', '?')
        g['labels'] |= set(_labels(p.get('labels')))
        if p.get('state') == 'published':
            g['state'] = 'published'
    # posts a minute or two apart (Instagram lags X) are one Reel
    out = []
    for g in sorted(groups.values(), key=lambda g: g['at']):
        if out and (g['at'] - out[-1]['at']).total_seconds() <= 180 and not (set(g['networks']) & set(out[-1]['networks'])):
            out[-1]['networks'].update(g['networks'])
            out[-1]['labels'] |= g['labels']
            if g['state'] == 'published':
                out[-1]['state'] = 'published'
            continue
        out.append(g)
    return out


SKIP_STATUS = re.compile(r'dropped|pulled|cancel|supersed|draft|deleted|held|not posted|parked', re.I)
SLOT_TXT = re.compile(r'(\d{1,2}):(\d{2})Z')


def posts_from_commitments(rows, ledger):
    """Fallback when the server's read is missing: rows scheduled or published, with tpl and kind from the ledger."""
    led = {}
    for e in ledger or []:
        led[str(e.get('name', ''))] = e
    out = []
    for r in rows or []:
        st = str(r.get('status', ''))
        dl = r.get('delivery') or {}
        if SKIP_STATUS.search(st) and not any(v in ('scheduled', 'published') for v in dl.values()):
            continue
        if not (re.search(r'schedul|publish|fulfil', st, re.I) or dl):
            continue
        at = t(r.get('slot')) or _slot_text(r.get('slot'))
        if not at:
            continue
        job = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', str(r.get('job', '')))
        e = led.get(job) or {}
        labels = set()
        if e.get('format'):
            labels.add('tpl:' + e['format'])
        kind = 'evergreen' if (e.get('bank') or str(r.get('kind', '')).lower() == 'evergreen') else 'news'
        labels.add('kind:' + kind)
        out.append({'at': at, 'state': 'published' if re.search(r'publish|fulfil', st, re.I) else 'scheduled',
                    'labels': labels, 'networks': {p: '?' for p in r.get('platforms', [])}})
    return sorted(out, key=lambda p: p['at'])


def _slot_text(s):
    """'Mon 09 Nov 20:30 Dubai (16:30Z)' with no year: the UTC part, this year."""
    s = str(s or '')
    m = re.search(r'(\d{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* .*?\((\d{1,2}):(\d{2})Z\)', s)
    if not m:
        return None
    months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
    year = dt.datetime.now(UTC).year
    try:
        d = dt.datetime(year, months.index(m.group(2)) + 1, int(m.group(1)), int(m.group(3)), int(m.group(4)), tzinfo=UTC)
    except ValueError:
        return None
    # the Dubai date can be a day after the UTC date (late evening UTC): trust the Z time, fix the day by the Dubai text
    m2 = re.search(r'(\d{2}) \w+ (\d{1,2}):(\d{2}) Dubai', s)
    if m2 and d.astimezone(DUBAI).day != int(m2.group(1)):
        d -= dt.timedelta(days=1)
    return d


def tpl_of(p):
    for l in p.get('labels', ()):
        if l.lower().startswith('tpl:'):
            return l.split(':', 1)[1].strip().lower()
    return None


def kind_of(p):
    for l in p.get('labels', ()):
        if l.lower().startswith('kind:'):
            return l.split(':', 1)[1].strip().lower()
    return None


# ----------------------------------------------------------------------------------------------------------------
# the cadence and the caps
# ----------------------------------------------------------------------------------------------------------------
def next_slot(posts, now):
    times = sorted({p['at'] for p in posts})
    past = [x for x in times if x <= now]
    future = [x for x in times if x > now]
    if not past:
        return {'last_post': None, 'covered_until': None, 'due_by': None, 'earliest': iso(now), 'overdue': None,
                'line': 'next slot: no post on record; post as soon as a story is ready'}
    cur = past[-1]
    for x in future:
        if x <= cur + dt.timedelta(minutes=MAX_GAP[band(cur)]):
            cur = x
        else:
            break
    due = cur + dt.timedelta(minutes=MAX_GAP[band(cur)])
    earliest = max(now, cur + dt.timedelta(minutes=SPACING[band(max(now, cur))]))
    overdue = due < now
    line = ('next slot: OVERDUE, nothing since %s (gap limit %d min passed at %s)' % (dub(cur), MAX_GAP[band(cur)], dub(due, False))
            if overdue else 'next slot: due by %s (covered until %s); earliest %s under the spacing'
            % (dub(due), dub(cur, False), dub(earliest, False)))
    return {'last_post': iso(past[-1]), 'covered_until': iso(cur), 'due_by': iso(due), 'earliest': iso(earliest),
            'overdue': overdue, 'line': line}


def _formats():
    try:
        import formats as F
        return F
    except Exception:                                   # noqa: BLE001  (keeper.yml without templates/)
        return None


def problems_for(p, before, F):
    """Why post p breaks the caps, given the posts before it (time order)."""
    out = []
    tpl, kind = tpl_of(p), kind_of(p)
    series = set(getattr(F, 'SERIES', ())) if F else set()
    seq = [q for q in before if tpl_of(q) and tpl_of(q) not in series]
    if tpl and tpl not in series:
        last2 = [tpl_of(q) for q in seq[-2:]]
        if len(last2) == 2 and all(x == tpl for x in last2):
            out.append('third %s in a row' % tpl)
        if F:
            fam = F.FAMILY.get(tpl)
            if fam == 'card':
                recent = [tpl_of(q) for q in seq[-(F.WINDOW - 1):]]
                n = sum(1 for x in recent if F.FAMILY.get(x) == 'card')
                if n >= F.CARD_MAX:
                    out.append('card-led %d of the last %d (at most %d in %d)' % (n + 1, len(recent) + 1, F.CARD_MAX, F.WINDOW))
            day = p['at'].astimezone(DUBAI).date()
            n = sum(1 for q in seq if tpl_of(q) == tpl and q['at'].astimezone(DUBAI).date() == day)
            if n >= F.DAY_MAX:
                out.append('%s %d times on Dubai day %s (at most %d)' % (tpl, n + 1, day, F.DAY_MAX))
    if kind == 'evergreen':
        if before and kind_of(before[-1]) == 'evergreen':
            out.append('two evergreen posts in a row')
        if band(p['at']) == 'day':
            last_eg = [q for q in before if kind_of(q) == 'evergreen']
            if last_eg and (p['at'] - last_eg[-1]['at']) < dt.timedelta(hours=EVERGREEN_GAP_H):
                out.append('evergreen %d min after the last evergreen (3 hours by day)'
                           % ((p['at'] - last_eg[-1]['at']).total_seconds() // 60))
    return out


def caps(posts, now, at=None):
    """The caps for the next post (at: its time; default now)."""
    F = _formats()
    at = at or now
    before = [p for p in posts if p['at'] < at]
    prev = before[-1] if before else None
    eg = [p for p in before if kind_of(p) == 'evergreen']
    reopen, why = at, []
    if prev and kind_of(prev) == 'evergreen':
        why.append('the last post (%s) was evergreen: never two in a row; reopens after the next news post' % dub(prev['at'], False))
        reopen = None
    if eg and reopen is not None:
        r = eg[-1]['at'] + dt.timedelta(hours=EVERGREEN_GAP_H)
        if r > at and band(at) == 'day':
            reopen = r
            why.append('last evergreen %s: 3 hours by day' % dub(eg[-1]['at'], False))
    if reopen is not None and band(reopen) == 'day':
        why.append('by day evergreen only fills a gap no news can fill, after a logged news search beyond the digest')
    ev_ok = reopen is not None and reopen <= at
    numbers = problems_for({'at': at, 'labels': {'tpl:numbers', 'kind:news'}}, before, F) if F else ['formats not read']
    seq = [tpl_of(q) for q in before if tpl_of(q)]
    window = seq[-((F.WINDOW if F else 6) - 1):]
    cards = [x for x in window if F and F.FAMILY.get(x) == 'card']
    return {
        'at': iso(at),
        'evergreen_allowed': ev_ok,
        'evergreen_reopens': iso(reopen) if reopen else 'after the next news post',
        'evergreen_why': why,
        'numbers_allowed': not numbers, 'numbers_why': numbers,
        'card_led_window': '%d of the last %d card-led (at most %d in %d)' % (len(cards), len(window), F.CARD_MAX if F else 2, F.WINDOW if F else 6),
        'card_led_allowed': len(cards) < (F.CARD_MAX if F else 2),
        'last_templates': seq[-3:],
    }


def cap_breaches(posts, now):
    F = _formats()
    out = []
    since = max(t(RULE_FROM), now - dt.timedelta(hours=3))
    for i, p in enumerate(posts):
        if p['at'] < since:
            continue
        for why in problems_for(p, posts[:i], F):
            out.append({'at': iso(p['at']), 'state': p['state'], 'template': tpl_of(p), 'kind': kind_of(p), 'why': why})
    return out


# ----------------------------------------------------------------------------------------------------------------
# handoffs, orders, scout
# ----------------------------------------------------------------------------------------------------------------
DUE_TXT = re.compile(r'\bdue (?:by |at )?(\d{1,2}):(\d{2}) Dubai', re.I)
T0 = re.compile(r'\bT0\b|breaking lane', re.I)


def _due(h, at):
    m = DUE_TXT.search(' '.join(str(h.get(k, '')) for k in ('done', 'next', 'title', 'note')))
    if m:
        d = at.astimezone(DUBAI).replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
        if d < at.astimezone(DUBAI) - dt.timedelta(hours=1):
            d += dt.timedelta(days=1)
        return d.astimezone(UTC)
    if h.get('t0') is True or T0.search(text_of(h, ('id', 'done', 'next', 'title'))):
        return at
    return at + dt.timedelta(minutes=60)


def open_handoffs(board, now, days=3):
    """Handoffs addressed to Production 2 that no Production 2 line has closed, oldest first."""
    hs, lines = handoffs(board), p2_lines(board)
    out = []
    for h in hs:
        at = t(h.get('at'))
        if not at or P2.search(str(h.get('from', ''))) or not P2.search(str(h.get('to', ''))):
            continue
        if now - at > dt.timedelta(days=days):
            continue
        hid = str(h['id'])
        named = [x for x in lines if t(x['at']) >= at and hid in text_of(x)]
        closed = [x for x in named if CLOSING.search(_around(text_of(x), hid))]
        # the author (or the studio) may close its own handoff: a later line naming it as superseded or withdrawn
        closed += [x for x in hs if x is not h and t(x.get('at')) and t(x['at']) >= at and hid in text_of(x)
                   and SUPERSEDED.search(_around(text_of(x), hid))]
        if closed:
            continue
        due = _due(h, at)
        out.append({'id': hid, 'from': cut(h.get('from'), 60), 'at': iso(at), 'due': iso(due), 'overdue': due < now,
                    't0': due == at, 'acked': bool(named), 'ack_at': iso(t(named[0]['at'])) if named else None,
                    'ask': cut(scrub(h.get('next') or h.get('done')), 280)})
    return sorted(out, key=lambda x: x['at'])


def _around(text, hid, n=160):
    i = text.find(hid)
    return text[max(0, i - 20): i + len(hid) + n] if i >= 0 else ''


def orders_open(orders, board, now):
    lines = p2_lines(board)
    out = []
    for o in orders or []:
        oid = str(o.get('id') or '')
        at = t(o.get('created_at') or o.get('at'))
        if not oid or not at or str(o.get('status', 'open')).lower() in ('done', 'closed', 'dropped'):
            continue
        named = [x for x in lines if t(x['at']) >= at and oid in text_of(x)]
        if any(CLOSING.search(_around(text_of(x), oid)) for x in named):
            continue
        t0 = bool(o.get('t0') or o.get('T0'))
        due = at if t0 else at + dt.timedelta(minutes=60)
        out.append({'id': oid, 'title': cut(scrub(o.get('title')), 160), 'source': cut(o.get('url') or o.get('source_url') or '', 200),
                    'note': cut(scrub(o.get('note')), 240), 't0': t0, 'at': iso(at), 'due': iso(due),
                    'overdue': due < now, 'acked': bool(named)})
    return sorted(out, key=lambda o: (not o['t0'], o['at']))


LEADS = (re.compile(r'Leads carried:\s*(.+)', re.I | re.S), re.compile(r'Ranked leads:\s*(.+)', re.I | re.S),
         re.compile(r'(Scout \(Haiku\).+)', re.I | re.S))
NOT_REASONS = re.compile(r'single[- ]outlet|no primary read|no written primary|only in (?:the |a )?(?:youtube )?video|'
                         r'arabic[- ]only|held for (?:a |the )?(?:statement|trace)|not on (?:the )?newsroom', re.I)
REJECT = re.compile(r'\b(?:reject\w*|no_source|denied|harmful_or_out_of_scope|duplicate)\b', re.I)


def scout_carry(board, now, hours=3):
    """The newest scout list of the last 3 hours and the rejections Production 2 wrote with it."""
    lines = [h for h in p2_lines(board) if now - t(h['at']) <= dt.timedelta(hours=hours)]
    leads, rej, src = None, [], None
    for h in reversed(lines):
        txt = ' '.join(str(h.get(k, '')) for k in ('done', 'next'))
        if leads is None:
            for rx in LEADS:
                m = rx.search(txt)
                if m:
                    leads, src = cut(scrub(m.group(1)), 700), h['id']
                    break
        for r in re.split(r'(?<=[.;])\s+', str(h.get('done', ''))):
            if len(rej) < 6 and REJECT.search(r):
                rej.append(cut(scrub(r.strip()), 220))
        if leads is not None:
            break
    return {'from_line': src, 'leads': leads, 'rejections': rej}


# ----------------------------------------------------------------------------------------------------------------
# hop alarms
# ----------------------------------------------------------------------------------------------------------------
def _needed_ids(line):
    m = re.search(r'\b([1-3])/\1\b', line)
    return int(m.group(1)) if m else 3


def hop_alarms(board, now, posts, mirror=None, server=None, history=None, server_at=None):
    out = []
    lines = p2_lines(board)
    # unacked
    for h in open_handoffs(board, now, days=1):
        age = (now - t(h['at'])).total_seconds() / 60
        if not h['acked'] and age > ACK_HOP_MIN:
            out.append({'key': 'hop|unacked|' + h['id'], 'kind': 'unacked',
                        'line': 'handoff %s to Production 2 unacknowledged %d min (from %s at %s)' % (h['id'], age, h['from'], dub(t(h['at']), False)),
                        'clears': "this run's board line: ack: %s (scheduled HH:MM Dubai | building, target HH:MM | declined: reason)" % h['id']})
    # no Production 2 line by :50 (only while the lane is live: a line in the last 24 hours)
    d = now.astimezone(DUBAI)
    if d.minute >= LINE_BY_MIN and lines and now - t(lines[-1]['at']) <= dt.timedelta(hours=24):
        hour0 = d.replace(minute=0, second=0, microsecond=0).astimezone(UTC)
        if not any(t(h['at']) >= hour0 for h in lines):
            out.append({'key': 'hop|no-line|' + d.strftime('%Y%m%d%H'), 'kind': 'no-line',
                        'line': 'no Production 2 board line since %s (last %s)' % (dub(hour0, False), dub(t(lines[-1]['at']))),
                        'clears': 'a Production 2 board line for this hour'})
    # scheduled without ids
    for h in lines:
        at = t(h['at'])
        if at < t(RULE_FROM) or now - at > dt.timedelta(hours=24):
            continue
        done = str(h.get('done', ''))
        if SCHEDULED_LINE.search(done):
            need, have = _needed_ids(done), len(ID6.findall(text_of(h, ('done', 'evidence'))))
            if have < need:
                out.append({'key': 'hop|no-ids|' + str(h['id']), 'kind': 'no-ids',
                            'line': 'scheduled line %s carries %d of %d Publer post id suffixes' % (h['id'], have, need),
                            'clears': 'the line printed by templates/presubmit.py line <commitment> --ids ig:<last6> x:<last6> th:<last6> (job status read back)'})
    # caps
    for b in cap_breaches(posts, now):
        out.append({'key': 'hop|caps|%s|%s' % (b['at'], b['why']), 'kind': 'caps',
                    'line': 'post %s (%s, %s, %s) is outside the caps: %s' % (dub(t(b['at'])), b['state'], b['template'] or '?', b['kind'] or '?', b['why']),
                    'clears': 'move or replace the post if it is still scheduled; if it went out, say why on the board'})
    # mirror
    if mirror is not None:
        g = t((mirror or {}).get('generated_at'))
        if not g or now - g > dt.timedelta(hours=MIRROR_MAX_H):
            out.append({'key': 'hop|mirror|' + (iso(g) or 'none'), 'kind': 'mirror',
                        'line': 'inbox mirror export is %s old (desk/mirror.json %s)' % ('%d min' % ((now - g).total_seconds() // 60) if g else 'of unknown age', dub(g) if g else 'unread'),
                        'clears': 'Production 1: run the inbox mirror task'})
    # digest
    if history:
        try:
            import desk_audit as DA
            stale = DA.stale_digest({'handoffs': [h for h in lines if now - t(h['at']) <= dt.timedelta(hours=3)]}, history, now)
        except Exception:                                   # noqa: BLE001
            stale = []
        for s in stale:
            m = re.search(r': (\S+) read digest seq', s)
            out.append({'key': 'hop|digest|' + (m.group(1) if m else s[:40]), 'kind': 'digest', 'line': cut(s, 240),
                        'clears': 'the next run reads the digest with the forced refspec and prints "digest seq read: N (branch head N)"'})
    # publer coverage on the server
    pr = t((server or {}).get('publer_read_at'))
    if not pr or now - pr > dt.timedelta(minutes=PUBLER_MAX_MIN):
        why = ('the server sent no Publer read' if not server else
               'last Publer read %s' % dub(pr) if pr else 'server read failed: %s' % cut(scrub((server or {}).get('publer', '')), 120))
        out.append({'key': 'hop|publer|' + now.astimezone(DUBAI).strftime('%Y%m%d%H'), 'kind': 'publer',
                    'line': 'keeper coverage stale: no Publer read in %d min (%s; server pass %s)' % (PUBLER_MAX_MIN, why, dub(server_at) if server_at else 'none received'),
                    'clears': 'Production 1: check dxb-keeper.timer and /etc/dxb-keeper/publer.key on dxb-render-1 (backoffice-install keeper)'})
    return out


# ----------------------------------------------------------------------------------------------------------------
# the work order
# ----------------------------------------------------------------------------------------------------------------
def build(board, now, posts, orders=None, mirror=None, digest=None, server=None, history=None, server_at=None):
    alarms = hop_alarms(board, now, posts, mirror, server, history, server_at)
    hand = open_handoffs(board, now)
    nxt = next_slot(posts, now)
    cp = caps(posts, now, max(now, t(nxt['earliest']) or now))
    head = None
    if isinstance(digest, dict) and digest.get('seq') is not None:
        g = t(digest.get('generated_at'))
        head = {'seq': digest.get('seq'), 'generated_at': iso(g), 'age_min': int((now - g).total_seconds() // 60) if g else None}
    return {
        'generated_at': iso(now), 'generated_dubai': dub(now),
        'source': 'keeper.yml workorder (adv-20261109-coordination-in-code)',
        'posts_from': 'publer via the server' if (server or {}).get('posts') is not None and posts and server else 'commitments and format ledger',
        'alarms': alarms,
        'orders': orders_open(orders, board, now),
        'handoffs': hand,
        'digest_head': head,
        'scout': scout_carry(board, now),
        'next_slot': nxt,
        'caps': cp,
        'instructions': 'Production 2: execute this work order top to bottom. Clear the alarms first, then the orders '
                        '(T0 first), then the handoffs oldest first, then the scout (fresh digest with the forced '
                        'refspec; carried leads first), then fill the next slot under the caps. Report each item on '
                        'the board with evidence: "wo <generated_at> item <n>: <outcome> (evidence)".',
    }


def markdown(wo):
    n = [0]

    def num():
        n[0] += 1
        return n[0]
    L = ['# Work order, %s' % wo['generated_dubai'],
         '',
         wo['instructions'],
         '',
         'Posts read from: %s.' % wo['posts_from'],
         '',
         '## 1. Alarms to clear first']
    if wo['alarms']:
        for a in wo['alarms']:
            L.append('%d. ALARM %s: %s. Clears with: %s.' % (num(), a['kind'], a['line'], a['clears']))
    else:
        L.append('none')
    L += ['', "## 2. Mohammad's orders (T0 first)"]
    if wo['orders']:
        for o in wo['orders']:
            L.append('%d. %s%s: %s%s%s. Due %s%s.' % (num(), 'T0 ' if o['t0'] else '', o['id'], o['title'],
                                                     ' (%s)' % o['source'] if o['source'] else '',
                                                     '; note: ' + o['note'] if o['note'] else '',
                                                     dub(t(o['due'])), ', OVERDUE' if o['overdue'] else ''))
    else:
        L.append('none')
    L += ['', '## 3. Open handoffs to Production 2 (oldest first)']
    if wo['handoffs']:
        for h in wo['handoffs']:
            L.append('%d. %s (from %s, %s): %s Due %s%s; %s.' % (
                num(), h['id'], h['from'], dub(t(h['at'])), h['ask'], dub(t(h['due'])), ', OVERDUE' if h['overdue'] else '',
                'acknowledged %s, not closed' % dub(t(h['ack_at']), False) if h['acked'] else 'NOT acknowledged'))
    else:
        L.append('none')
    L += ['', '## 4. Digest and the scout']
    dh = wo['digest_head']
    L.append('%d. Digest head: %s. Read it with git fetch -q origin +watch-digest:refs/remotes/origin/watch-digest and print '
             '"digest seq read: N (branch head N)".' % (num(), 'seq %s at %s, %s min old' % (dh['seq'], dub(t(dh['generated_at'])), dh['age_min']) if dh else 'not read'))
    sc = wo['scout']
    L.append('%d. Scout first (Haiku, at most five leads, rejection reasons: no_source, denied, harmful_or_out_of_scope, '
             'duplicate). The orders and handoffs above are not scout leads to judge: build them from the source they name. '
             'Coverage over caution (r4): search for each story itself (a web search, the outlet it came from, the press '
             'wires); a credible outlet is a source (تقرير), an official video or press release a primary; no_source only '
             'after that search, confirmed by the editor. Carried from %s: %s' % (
                 num(), sc['from_line'] or 'no recent run', sc['leads'] or 'no leads carried'))
    for r in sc['rejections']:
        bad = NOT_REASONS.search(r)
        L.append('   - last run rejected: %s%s' % (r, ' <- "%s" is not a reason: re-check and build as تقرير' % bad.group(0)
                                                   if bad else ''))
    L += ['', '## 5. Next slot']
    L.append('%d. %s' % (num(), wo['next_slot']['line']))
    c = wo['caps']
    L += ['', '## 6. Caps']
    L.append('%d. Evergreen: %s%s.' % (num(), 'allowed' if c['evergreen_allowed'] else 'NOT allowed, reopens %s' % (
        dub(t(c['evergreen_reopens'])) if t(c['evergreen_reopens']) else c['evergreen_reopens']),
        ('; ' + '; '.join(c['evergreen_why'])) if c['evergreen_why'] else ''))
    L.append('%d. Numbers: %s.' % (num(), 'allowed' if c['numbers_allowed'] else 'NOT allowed (%s)' % '; '.join(c['numbers_why'])))
    L.append('%d. Card-led window: %s; last templates %s.' % (num(), c['card_led_window'], ', '.join(c['last_templates']) or 'none read'))
    L.append('')
    return '\n'.join(L)


def raise_hops(alarms, state_path, out, now):
    """One ntfy push per hop alarm key (keeper.raise_desk and its state), the rows into status.json as `hop` and
    one line each into status.txt, so keeper-status carries them."""
    import keeper as K
    state = load(state_path, {}) or {}
    raised, log = K.raise_desk([{'key': a['key'], 'title': 'Hop alarm: %s' % a['kind'],
                                 'lines': [a['line'], 'Clears with: ' + a['clears']]} for a in alarms], state, now)
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
        f.write('\n')
    sp = os.path.join(out, 'status.json')
    st = load(sp, None)
    if isinstance(st, dict):
        st['hop'] = [{'kind': a['kind'], 'line': a['line'], 'clears': a['clears']} for a in alarms]
        st.setdefault('six', [])
        st['six'] = [l for l in st['six'] if not l.startswith('hop alarm')] + \
            ['hop alarm %s: %s' % (a['kind'], a['line']) for a in alarms] or st['six']
        with open(sp, 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(os.path.join(out, 'status.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join([st.get('line', '')] + st['six']) + '\n')
    if log:
        with open(os.path.join(out, 'keeper.log'), 'a', encoding='utf-8') as f:
            f.write('\n'.join(log) + '\n')
    return len(raised)


def due_to_write(prev, now, force=False):
    if force or not prev:
        return True
    g = t(prev.get('generated_at'))
    d = now.astimezone(DUBAI)
    if d.minute < WRITE_FROM_MIN:
        return not g or now - g > dt.timedelta(minutes=70)
    hour = d.replace(minute=0, second=0, microsecond=0)
    return not g or g.astimezone(DUBAI) < hour.replace(minute=WRITE_FROM_MIN)


def run(args):
    now = t(args.now) if args.now else dt.datetime.now(UTC)
    board = load(args.board, {}) or {}
    orders = []
    if args.orders and os.path.isdir(args.orders):
        for f in sorted(glob.glob(os.path.join(args.orders, '*.json'))):
            o = load(f, None)
            if isinstance(o, dict):
                o.setdefault('id', os.path.basename(f)[:-5])
                orders.append(o)
    mirror = load(args.mirror, None) if args.mirror else None
    digest = load(args.digest, None)
    server = load(args.server, None)
    server_at = t((server or {}).get('generated_at'))
    rows = load(args.commitments, {})
    rows = rows.get('rows', []) if isinstance(rows, dict) else rows
    ledger = load(args.ledger, [])
    sp = posts_from_server(server) if server and server.get('posts') is not None and t(server.get('publer_read_at')) \
        and now - t(server['publer_read_at']) <= dt.timedelta(hours=2) else []
    posts = sp or posts_from_commitments(rows, ledger)
    history = None
    if args.digests and os.path.isdir(args.digests):
        import desk_audit as DA
        history = DA.digest_history(folder=args.digests)
    wo = build(board, now, posts, orders, mirror, digest, server if sp else None, history, server_at)
    out = args.out
    os.makedirs(out, exist_ok=True)
    hop = {'generated_at': iso(now), 'alarms': wo['alarms']}
    with open(os.path.join(out, 'hop.json'), 'w', encoding='utf-8') as f:
        json.dump(hop, f, ensure_ascii=False, indent=1)
        f.write('\n')
    if args.state:
        hop['raised'] = raise_hops(wo['alarms'], args.state, out, now)
        with open(os.path.join(out, 'hop.json'), 'w', encoding='utf-8') as f:
            json.dump(hop, f, ensure_ascii=False, indent=1)
            f.write('\n')
    prev = load(os.path.join(out, 'work-order.json'), None)
    wrote = due_to_write(prev, now, args.force)
    if wrote:
        with open(os.path.join(out, 'work-order.json'), 'w', encoding='utf-8') as f:
            json.dump(wo, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(os.path.join(out, 'work-order.md'), 'w', encoding='utf-8') as f:
            f.write(markdown(wo))
    print('workorder: %s; %d alarms, %d orders, %d open handoffs; %s' % (
        'written' if wrote else 'kept (next from :%02d Dubai)' % WRITE_FROM_MIN, len(wo['alarms']), len(wo['orders']),
        len(wo['handoffs']), wo['next_slot']['line']))
    return wo, wrote


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    for a in ('board', 'orders', 'mirror', 'digest', 'digests', 'server', 'commitments', 'ledger', 'now', 'state'):
        ap.add_argument('--' + a)
    ap.add_argument('--out', default='.')
    ap.add_argument('--force', action='store_true')
    run(ap.parse_args(argv))
    return 0


if __name__ == '__main__':
    sys.exit(main())
