"""Desk board trim (adv-20261118-templates-never-refuse C, Mohammad 18 Nov 2026).

dxb-queue desk/board.md and board.json had grown to 570 KB and every run read all of it. The trim keeps on the board
only what a run needs, and moves the rest to desk/archive/ (nothing is deleted):
  board.json  roles, rules, digest lock, standing orders, questions, and the handoffs that are open (to a production
              desk and not acknowledged) or less than 48 hours old; older handoffs go to desk/archive/board-<date>.json
  board.md    rebuilt: sections 0 to 2 as they are, 3 the kept handoffs (long text cut to TEXT_MAX, the full entry stays
              in board.json), 4 the questions, 5 the run lines of the last 24 hours; every older line of the old board.md
              is appended to desk/archive/board-<date>.md
The new board.md stays under MAX_BYTES (30 KB); if it would not, the oldest kept run lines and closed handoffs go first.

    python3 ops/backoffice/dispatch/boardtrim.py <desk dir> [--now ISO] [--dry]
Run daily at 04:00 Dubai by dxb-queue's boardtrim.yml (Mohammad, 24 Nov 2026: Production 2 runs stopped early on context
with the board at 285 KB); it prints what moved. The latest 'p2 queue' line stays whatever its age; a kept run line over
LINE_MAX is cut on the board, its full text archived under its own day.
"""
import datetime as dt
import json
import os
import re
import sys

MAX_BYTES = 30_000
HANDOFF_KEEP_H = 48
RUN_KEEP_H = 24
TEXT_MAX = 300
LIMIT = [TEXT_MAX]          # shrinks to 160, then 90, before any run line of the last 24 hours leaves the board
UTC = dt.timezone.utc
DATE_RE = re.compile(r'(20\d\d)-?(\d\d)-?(\d\d)')
TIME_RE = re.compile(r'^- (?:(20\d\d-\d\d-\d\d)T)?(\d\d):(\d\d)')


def _t(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return None


def handoff_time(h):
    for k in ('at', 'acknowledged_at'):
        if h.get(k) and _t(h[k]):
            return _t(h[k])
    m = DATE_RE.search(str(h.get('id', '')))
    if m:
        return dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 23, 59, tzinfo=UTC)
    return None


OPEN_MAX_H = 72              # an unacknowledged handoff older than this is stale, not open (it goes to the archive)


def is_open(h, now=None):
    to = str(h.get('to') or '').lower()
    if 'production' not in to or h.get('acknowledged_at') or h.get('closed'):
        return False
    at = handoff_time(h)
    return now is None or at is None or now - at <= dt.timedelta(hours=OPEN_MAX_H)


def split_handoffs(handoffs, now):
    keep, old = [], []
    for h in handoffs:
        at = handoff_time(h)
        if is_open(h, now) or at is None or now - at <= dt.timedelta(hours=HANDOFF_KEEP_H):
            keep.append(h)
        else:
            old.append(h)
    return keep, old


ISO_RE = re.compile(r'(20\d\d-\d\d-\d\d)T(\d\d):(\d\d)')
OUT_OF_ORDER_H = 3          # lines from two writers may be a few minutes out of order; a jump back of more is a new day
QUESTION_KEEP_D = 14        # questions older than this leave board.md (they stay in board.json and the archive)
LINE_MAX = 600              # a kept run line longer than this is cut on the board; the full line goes to the archive


def dated_lines(lines, now):
    """Each line with its time, dated backwards from the newest line (24 Nov 2026: dating forwards from a start date
    drifted, every small out-of-order pair moved a day on, and lines of 23 Nov read as 3 Dec, so nothing was trimmed).
    The last line is on now's date (the day before when its time is later than now). Walking back, a line whose time
    is more than OUT_OF_ORDER_H later than the line after it is on the day before. A line that carries its own ISO time
    at the same HH:MM (a '- 2026-11-24T..' prefix, 'started 2026-11-24T21:07Z') anchors the date."""
    out = [None] * len(lines)
    cur = now.date()
    nxt = None
    for i in range(len(lines) - 1, -1, -1):
        ln = lines[i]
        hm = TIME_RE.match(ln)
        if not hm:
            out[i] = (ln, None)
            continue
        h, mi = min(int(hm.group(2)), 23), min(int(hm.group(3)), 59)
        anchor = hm.group(1)
        if not anchor:
            for m in ISO_RE.finditer(ln):
                if (int(m.group(2)), int(m.group(3))) == (h, mi):
                    anchor = m.group(1)
                    break
        if anchor:
            cur = dt.date.fromisoformat(anchor)
        elif nxt is None:
            if (h, mi) > (now.hour, now.minute) and h - now.hour > OUT_OF_ORDER_H:
                cur -= dt.timedelta(days=1)
        elif (h * 60 + mi) - (nxt.hour * 60 + nxt.minute) > OUT_OF_ORDER_H * 60 and nxt.date() == cur:
            cur -= dt.timedelta(days=1)
        w = dt.datetime(cur.year, cur.month, cur.day, h, mi, tzinfo=UTC)
        out[i] = (ln, w)
        nxt = w
    last = None
    for i, (ln, w) in enumerate(out):              # undated lines take the time of the line before them
        out[i] = (ln, w or last or now)
        last = out[i][1]
    return out


def _qtime(q):
    m = DATE_RE.search(json.dumps(q, ensure_ascii=False) if isinstance(q, dict) else str(q))
    try:
        return dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=UTC) if m else None
    except ValueError:
        return None


def _cut(s, n=None):
    n = n or LIMIT[0]
    s = ' '.join(str(s or '').split())
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def handoff_md(h):
    at = h.get('at') or ''
    head = f"### {h.get('id')}\n- {h.get('from')} -> {h.get('to')}{', ' + at if at else ''}"
    body = [f"- done: {_cut(h.get('done'))}"]
    for k in ('next', 'must_not_repeat', 'evidence'):
        if h.get(k):
            body.append(f'- {k}: {_cut(h[k], min(200, LIMIT[0]))}')
    if h.get('acknowledged_at'):
        body.append(f"- acknowledged: {h.get('acknowledged_by')} {h['acknowledged_at']}")
    return '\n'.join([head] + body) + '\n'


def trim(md, board, now):
    lines = md.split('\n')
    sec = {}
    cur = 'head'
    for ln in lines:
        if ln.startswith('## '):
            cur = ln[3:].strip()
        sec.setdefault(cur, []).append(ln)
    head_keys = [k for k in sec if k == 'head' or k.startswith(('0.', '1.', '2.'))]
    run_src = []                                   # run lines: every '- HH:MMZ' / '- YYYY-..' line outside sections 0-2
    for k, v in sec.items():
        if k in head_keys:
            continue
        run_src += [ln for ln in v if TIME_RE.match(ln)]
    dated = dated_lines(run_src, now)
    recent = [(ln, w) for ln, w in dated if now - w <= dt.timedelta(hours=RUN_KEEP_H)]
    old_dated = [(ln, w) for ln, w in dated if now - w > dt.timedelta(hours=RUN_KEEP_H)]
    queue = [ln for ln, w in dated if re.match(r'^- (?:\S+ )?\d\d:\d\dZ p2 queue', ln)]
    if queue and queue[-1] not in [ln for ln, _ in recent]:   # the latest p2 queue line stays, whatever its age
        recent.insert(0, next(x for x in dated if x[0] == queue[-1]))
    latest_q = queue[-1] if queue else None
    cap = [LINE_MAX]

    def runs_at(rs):                               # run lines cut to the cap; the latest p2 queue line stays whole
        return [ln if (len(ln) <= cap[0] or ln == latest_q) else ln[:cap[0] - 1].rstrip() + '…' for ln, _ in rs]
    old_runs = [ln for ln, _ in old_dated]
    by_day = {}
    for ln, w in old_dated:
        by_day.setdefault(w.strftime('%Y-%m-%d'), []).append(ln)
    q_cut = now - dt.timedelta(days=QUESTION_KEEP_D)
    qs = [q for q in board.get('questions') or [] if 'RESOLVED' not in str(q)]
    q_old = [q for q in qs if (_qtime(q) or now) < q_cut]
    qs = [q for q in qs if q not in q_old]
    keep_h, old_h = split_handoffs(board.get('handoffs') or [], now)
    new_board = dict(board, handoffs=keep_h)

    def build(kh, kr):
        out = []
        for k in head_keys:
            out += sec[k]
        out += ['## 3. Handoffs', f'Open, and the last {HANDOFF_KEEP_H} hours; older ones in desk/archive/ '
                '(boardtrim.py). Full text in board.json.', '']
        out += [handoff_md(h) for h in kh]
        out += ['## 4. Questions for Mohammad']
        out += [(f"- [{q.get('card') or q.get('id') or ''}] {_cut(q.get('question') or q.get('text') or q, min(200, LIMIT[0]))}"
                 if isinstance(q, dict) else f'- {_cut(q, min(200, LIMIT[0]))}') for q in qs]
        if q_old:
            out += [f'- ({len(q_old)} older than {QUESTION_KEEP_D} days: in board.json and desk/archive)']
        out += ['', f'## 5. Run lines (last {RUN_KEEP_H} hours; append new ones below)'] + kr + ['']
        return '\n'.join(out)

    kr_src = list(recent)
    kh = list(keep_h)
    LIMIT[0] = TEXT_MAX
    text = build(kh, runs_at(kr_src))
    for lim, c in ((160, 400), (160, 300), (90, 240), (90, 200), (90, 160)):   # shorter text before fewer lines
        if len(text.encode()) <= MAX_BYTES:
            break
        LIMIT[0], cap[0] = lim, c
        text = build(kh, runs_at(kr_src))
    kr = runs_at(kr_src)
    while len(text.encode()) > MAX_BYTES and (kr_src or any(not is_open(h, now) for h in kh)):
        closed = [h for h in kh if not is_open(h, now)]
        if closed:                                 # closed handoffs leave the md first (they stay in board.json)
            kh.remove(closed[0])
        else:
            gone = kr_src.pop(0 if kr_src[0][0] != latest_q or len(kr_src) == 1 else 1)
            old_runs.append(gone[0])
            by_day.setdefault(gone[1].strftime('%Y-%m-%d'), []).append(gone[0])
        kr = runs_at(kr_src)
        text = build(kh, kr)
    for ln, w in kr_src:                           # a line cut on the board keeps its full text in its day's archive
        if len(ln) > cap[0] and ln != latest_q:
            by_day.setdefault(w.strftime('%Y-%m-%d'), []).append(ln)
    dropped_from_md = [h for h in keep_h if h not in kh]
    archive_md = '\n'.join([ln for k, v in sec.items() if k not in head_keys for ln in v
                            if not TIME_RE.match(ln)])
    return text, new_board, old_h, archive_md, {'handoffs_kept': len(keep_h), 'handoffs_archived': len(old_h),
                                                'handoffs_md_only_in_json': len(dropped_from_md),
                                                'run_lines_kept': len(kr), 'run_lines_archived': len(old_runs),
                                                'board_md_bytes': len(text.encode()), 'archive_days': sorted(by_day)}, by_day


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    desk = argv[0]
    now = _t(argv[argv.index('--now') + 1]) if '--now' in argv else dt.datetime.now(UTC)
    md = open(os.path.join(desk, 'board.md'), encoding='utf-8').read()
    board = json.load(open(os.path.join(desk, 'board.json'), encoding='utf-8'))
    text, nb, old_h, arch_md, stats, by_day = trim(md, board, now)
    print('boardtrim: ' + json.dumps(stats))
    if '--dry' in argv:
        return 0
    ad = os.path.join(desk, 'archive')
    os.makedirs(ad, exist_ok=True)
    day = now.strftime('%Y-%m-%d')
    ap = os.path.join(ad, f'board-{day}.json')
    prev = json.load(open(ap, encoding='utf-8')) if os.path.exists(ap) else []
    json.dump(prev + old_h, open(ap, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    stamp = f'\n<!-- archived {now.strftime("%Y-%m-%dT%H:%MZ")} -->\n'
    with open(os.path.join(ad, f'board-{day}.md'), 'a', encoding='utf-8') as f:   # handoffs and questions as they were
        f.write(stamp + arch_md + '\n')
    for d, lns in sorted(by_day.items()):        # run lines, each in the file of its own day
        with open(os.path.join(ad, f'board-{d}.md'), 'a', encoding='utf-8') as f:
            f.write(stamp + '\n'.join(lns) + '\n')
    nb['updated_at'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    nb['updated_by'] = 'boardtrim'
    with open(os.path.join(desk, 'board.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(nb, ensure_ascii=False, indent=1))
    open(os.path.join(desk, 'board.md'), 'w', encoding='utf-8').write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
