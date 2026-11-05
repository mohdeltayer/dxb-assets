#!/usr/bin/env python3
"""Daily desk audit (adv-20261104-desk-manifest, point 2): compare ops/desks.json with what actually ran.

    python3 ops/desk_audit.py --board <dxb-queue>/desk/board.json [--runs newsroom/helper-runs.jsonl] [--now ISO]

Prints one line per finding, most urgent first, or "desk audit: all present". The morning digest puts these
lines at the top of its card and adds a board question for each MISSING one; the server runs it on the keeper
timer once the keeper carries it. Reads files only; writes nothing."""
import argparse, datetime as dt, json, os

DUBAI = dt.timezone(dt.timedelta(hours=4))


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
        for h in d.get('housekeeping', []):
            if h.get('status') == 'MISSING':
                out.append(f"MISSING {d['name']}: {h['name']}: {h.get('note', '')}")
        for g in d.get('gaps', []):
            out.append(f"GAP {d['name']}: {g}")
    order = {'MISSING': 0, 'FAILING': 1, 'LATE': 2, 'GAP': 3}
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
