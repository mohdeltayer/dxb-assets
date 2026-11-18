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
Run daily by Production 1's morning digest task (the server has no key that can push to dxb-queue); it prints what moved.
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


def dated_lines(lines, start_date):
    """Each line with the date it belongs to: a line naming a date (an id like p2-20261109-..., an ISO time) sets it;
    an undated '- HH:MMZ' line keeps the last one; a time earlier than the last one on the same date moves a day on."""
    cur, last_hm, out = start_date, None, []
    for ln in lines:
        m = DATE_RE.search(ln)
        hm = TIME_RE.match(ln)
        if m:
            try:
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                if d >= cur:
                    cur, last_hm = d, None
            except ValueError:
                pass
        when = None
        if hm:
            if hm.group(1):
                cur = dt.date.fromisoformat(hm.group(1))
            h, mi = int(hm.group(2)), int(hm.group(3))
            if last_hm and (h, mi) < last_hm and not m and not hm.group(1):
                cur += dt.timedelta(days=1)
            last_hm = (h, mi)
            when = dt.datetime(cur.year, cur.month, cur.day, min(h, 23), min(mi, 59), tzinfo=UTC)
        out.append((ln, when or dt.datetime(cur.year, cur.month, cur.day, 23, 59, tzinfo=UTC)))
    return out


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
    start = (now - dt.timedelta(days=30)).date()
    dated = dated_lines(run_src, start)
    keep_runs = [ln for ln, w in dated if now - w <= dt.timedelta(hours=RUN_KEEP_H)]
    old_runs = [ln for ln, w in dated if now - w > dt.timedelta(hours=RUN_KEEP_H)]
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
                 if isinstance(q, dict) else f'- {_cut(q, min(200, LIMIT[0]))}') for q in board.get('questions') or []
                if 'RESOLVED' not in str(q)]
        out += ['', f'## 5. Run lines (last {RUN_KEEP_H} hours; append new ones below)'] + kr + ['']
        return '\n'.join(out)

    kh, kr = list(keep_h), list(keep_runs)
    LIMIT[0] = TEXT_MAX
    text = build(kh, kr)
    for lim in (160, 90):                          # shorter text first: the full entries stay in board.json
        if len(text.encode()) <= MAX_BYTES:
            break
        LIMIT[0] = lim
        text = build(kh, kr)
    while len(text.encode()) > MAX_BYTES and (kr or any(not is_open(h, now) for h in kh)):
        closed = [h for h in kh if not is_open(h, now)]
        if closed:                                 # closed handoffs leave the md first (they stay in board.json)
            kh.remove(closed[0])
        else:
            old_runs.append(kr.pop(0))
        text = build(kh, kr)
    dropped_from_md = [h for h in keep_h if h not in kh]
    archive_md = '\n'.join([ln for k, v in sec.items() if k not in head_keys for ln in v
                            if not TIME_RE.match(ln)] + old_runs)
    return text, new_board, old_h, archive_md, {'handoffs_kept': len(keep_h), 'handoffs_archived': len(old_h),
                                                'handoffs_md_only_in_json': len(dropped_from_md),
                                                'run_lines_kept': len(kr), 'run_lines_archived': len(old_runs),
                                                'board_md_bytes': len(text.encode())}


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    desk = argv[0]
    now = _t(argv[argv.index('--now') + 1]) if '--now' in argv else dt.datetime.now(UTC)
    md = open(os.path.join(desk, 'board.md'), encoding='utf-8').read()
    board = json.load(open(os.path.join(desk, 'board.json'), encoding='utf-8'))
    text, nb, old_h, arch_md, stats = trim(md, board, now)
    print('boardtrim: ' + json.dumps(stats))
    if '--dry' in argv:
        return 0
    ad = os.path.join(desk, 'archive')
    os.makedirs(ad, exist_ok=True)
    day = now.strftime('%Y-%m-%d')
    ap = os.path.join(ad, f'board-{day}.json')
    prev = json.load(open(ap, encoding='utf-8')) if os.path.exists(ap) else []
    json.dump(prev + old_h, open(ap, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(ad, f'board-{day}.md'), 'a', encoding='utf-8') as f:
        f.write(f'\n<!-- archived {now.strftime("%Y-%m-%dT%H:%MZ")} -->\n' + arch_md + '\n')
    nb['updated_at'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    nb['updated_by'] = 'boardtrim'
    with open(os.path.join(desk, 'board.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(nb, ensure_ascii=False, indent=1))
    open(os.path.join(desk, 'board.md'), 'w', encoding='utf-8').write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
