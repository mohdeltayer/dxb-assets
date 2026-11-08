#!/usr/bin/env python3
"""Daily desk audit (adv-20261104-desk-manifest, point 2): compare ops/desks.json with what actually ran.

    python3 ops/desk_audit.py --board <dxb-queue>/desk/board.json [--runs newsroom/helper-runs.jsonl] [--now ISO]

Prints one line per finding, most urgent first, or "desk audit: all present". The morning digest puts these
lines at the top of its card and adds a board question for each MISSING one; the server runs it on the keeper
timer once the keeper carries it. Reads files only; writes nothing.

DEAD (adv-20261107-keeper-blind-and-lost-submit, item 7): a task with "period_min" and "dead_after_runs" whose own
evidence (board handoffs whose "from" matches "board_from", helper-runs lines whose "run" or "session" matches
"runs_match") is older than dead_after_runs periods is listed as dead, with its task name, at the top of the card.

UNACKED (Mohammad, 8 Nov 2026: "Production 2's run prompt reads the board Handoffs addressed to it before the digest
and acknowledges each"): a handoff written since ACK_FROM whose "to" names Production 2 and that no later Production 2
handoff mentions by id ("ack: <id>") within ACK_MIN minutes. Notices to "all" (started, released, digest lines) need
no acknowledgement. Listed with its age, oldest first.

NOT-FOLLOWING-RULES (adv-20261108-no-decision-stalls): a handoff from the last 24 hours whose text says a decision is
needed ("decision", "need Mohammad", "needs Mohammad") without citing where the repo was searched (CLAUDE.md, STYLE.md,
BUILD.md, a newsroom/ or notes/ file, or a card id). A question put on the board's Questions list is the right place."""
import argparse, datetime as dt, json, os, re

DUBAI = dt.timezone(dt.timedelta(hours=4))


def _t(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return None


def last_seen(t, board, runs):
    """Latest evidence of one task: (time, where) from its board handoffs and its helper-runs lines."""
    best, where = None, None
    bf = t.get('board_from')
    if bf:
        for h in board.get('handoffs', []):
            if isinstance(h, dict) and re.search(bf, str(h.get('from', ''))):
                x = _t(h.get('at', ''))
                if x and (best is None or x > best):
                    best, where = x, 'board'
    rm = t.get('runs_match')
    if rm and runs:
        for r in runs:
            if re.search(rm, str(r.get('session', '')) + ' ' + str(r.get('run', ''))):
                x = _t(r.get('at', ''))
                if x and (best is None or x > best):
                    best, where = x, 'helper-runs'
    return best, where


ACK_MIN = 70                 # one hourly run plus its writing time
ACK_FROM = '2026-11-08T16:00:00Z'   # the first handoffs written under the rule (Pokémon, GTA VI ep1)
P2 = re.compile(r'production 2', re.I)
DECISION = re.compile(r'\bdecision\b|\bneeds? mohammad', re.I)
CITED = re.compile(r'CLAUDE\.md|STYLE\.md|BUILD\.md|newsroom/|notes/|\badv-20\d{6}-|\bprod-20\d{6}-', re.I)


def unacked(board, now):
    """Handoffs addressed to Production 2 (or all) with no later Production 2 handoff naming their id."""
    hs = [h for h in board.get('handoffs', []) if isinstance(h, dict)]
    out = []
    for h in hs:
        to, hid, at = str(h.get('to', '')), h.get('id'), _t(h.get('at', ''))
        if not hid or not at or P2.search(str(h.get('from', ''))):
            continue
        if not P2.search(to) or at < _t(ACK_FROM):
            continue
        age = (now - at).total_seconds() / 60
        if age <= ACK_MIN or age > 72 * 60:
            continue
        acked = any(P2.search(str(x.get('from', ''))) and (_t(x.get('at', '')) or at) >= at and hid in
                    ' '.join(str(x.get(k, '')) for k in ('id', 'done', 'next', 'evidence', 'ack'))
                    for x in hs)
        if not acked:
            out.append((age, f"UNACKED Production 2: {hid} from {h.get('from', '?')} waiting {age:.0f} min "
                             f"(no later Production 2 line names it)"))
    return [l for _, l in sorted(out, reverse=True)]


def not_following(board, now):
    out = []
    for h in board.get('handoffs', []):
        if not isinstance(h, dict):
            continue
        at = _t(h.get('at', ''))
        if not at or (now - at).total_seconds() > 24 * 3600:
            continue
        text = ' '.join(str(h.get(k, '')) for k in ('done', 'next'))
        if DECISION.search(text) and not CITED.search(text):
            out.append(f"NOT-FOLLOWING-RULES {h.get('from', '?')}: {h.get('id', '?')} asks for a decision without "
                       f"citing the section searched (search CLAUDE.md, STYLE.md, newsroom/ first; questions go on "
                       f"the board's Questions list)")
    return out


def audit(desks, board, runs, now):
    today = now.astimezone(DUBAI)
    ids = {h.get('id') for h in board.get('handoffs', [])}
    out = []
    for d in desks['desks']:
        for t in d.get('tasks', []):
            st = str(t.get('status', ''))
            if st.startswith('FAILING'):
                out.append(f"FAILING {d['name']}: {t['name']}: {st.split(':', 1)[1].strip()}")
            sid, due = t.get('started_id'), t.get('due')
            if sid and due and t.get('session') == 'fresh':
                hh, mm = map(int, due.split(':'))
                if (today.hour, today.minute) >= (hh, mm):
                    want = sid.format(date=today.strftime('%Y%m%d'))
                    if want not in ids:
                        out.append(f"MISSING {d['name']}: no {want} on the board (due {due} Dubai)")
            gap = t.get('max_gap_min')
            if gap and 'helper-runs' in str(t.get('evidence', '')) and runs is not None:
                last = max((r.get('at', '') for r in runs), default='')
                if last:
                    age = (now - dt.datetime.fromisoformat(last.replace('Z', '+00:00'))).total_seconds() / 60
                    if age > gap:
                        out.append(f"LATE {d['name']}: {t['name']} last ran {age:.0f} min ago (limit {gap})")
                else:
                    out.append(f"MISSING {d['name']}: {t['name']} has no run on record")
            per, n = t.get('period_min'), t.get('dead_after_runs')
            if per and n:
                seen, where = last_seen(t, board, runs)
                if seen is None:
                    out.append(f"DEAD {d['name']}: {t['name']}: no run on record")
                else:
                    age = (now - seen).total_seconds() / 60
                    if age > per * n + 15:
                        out.append(f"DEAD {d['name']}: {t['name']}: silent for {int(age // per)} runs "
                                   f"(last {where} {seen.astimezone(DUBAI).strftime('%d %b %H:%M')} Dubai)")
        for h in d.get('housekeeping', []):
            if h.get('status') == 'MISSING':
                out.append(f"MISSING {d['name']}: {h['name']}: {h.get('note', '')}")
        for g in d.get('gaps', []):
            out.append(f"GAP {d['name']}: {g}")
    out += unacked(board, now) + not_following(board, now)
    order = {'DEAD': 0, 'UNACKED': 1, 'MISSING': 2, 'FAILING': 3, 'LATE': 4, 'NOT-FOLLOWING-RULES': 5, 'GAP': 6}
    return sorted(out, key=lambda s: order.get(s.split()[0], 9)) or ['desk audit: all present']


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--desks', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desks.json'))
    ap.add_argument('--board', required=True)
    ap.add_argument('--runs')
    ap.add_argument('--now')
    a = ap.parse_args()
    now = dt.datetime.fromisoformat(a.now.replace('Z', '+00:00')) if a.now else dt.datetime.now(dt.timezone.utc)
    runs = [json.loads(l) for l in open(a.runs) if l.strip()] if a.runs and os.path.exists(a.runs) else None
    for line in audit(json.load(open(a.desks)), json.load(open(a.board)), runs, now):
        print(line)
