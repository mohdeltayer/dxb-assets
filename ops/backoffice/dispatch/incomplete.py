"""Unfinished work handed to the next run (adv-20261117-server-speed-for-p2 E, Mohammad 17 Nov 2026).

A Production 2 run that ends INCOMPLETE used to say so only in prose on the board (RPG Maker U2U, 17 Nov 06:11Z: the
render still in its Render step, the Director and Publer steps left). The next run had to find that line and parse it.
Now the run also writes one row in dxb-queue desk/incomplete.json: story, job, render run id, the next step, and when it
must be done by. The keeper's work order prints every open row right after the alarms, before Mohammad's orders, as
"pick up first"; a row older than 2 hours raises an `incomplete` alarm. The run that finishes the item closes the row.

    python3 incomplete.py open  --file desk/incomplete.json --story <story id> --next "<the next step>"
                                [--job jobs/live/<name>.json] [--run <render run id>] [--slot <ISO>] [--by <who>]
    python3 incomplete.py close --file desk/incomplete.json --story <story id> --outcome "<what was done>"
    python3 incomplete.py show  --file desk/incomplete.json

Opening a story that already has a row replaces its next step (one row per story). Closed rows are dropped after a
day. No Publer ids, links to posts or tokens: the file is read by the public work order.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

UTC = dt.timezone.utc
KEEP_CLOSED_HOURS = 24
STALE_MIN = 120                       # an open row older than this raises the `incomplete` alarm on the work order
ID_TOKEN = re.compile(r'\b[0-9a-f]{24}\b|https?://\S+', re.I)
STORY = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,150}$')
JOB = re.compile(r'^jobs/(?:live|render|test|breaking|done|prerender)/[A-Za-z0-9._-]+\.json$')


def now_iso(now=None):
    return (now or dt.datetime.now(UTC)).strftime('%Y-%m-%dT%H:%M:%SZ')


def t(s):
    try:
        x = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return x if x.tzinfo else x.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None


def load(path):
    try:
        d = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return {'rows': []}
    return d if isinstance(d, dict) and isinstance(d.get('rows'), list) else {'rows': []}


def save(path, d, now=None):
    now = now or dt.datetime.now(UTC)
    d['rows'] = [r for r in d['rows'] if r.get('state') == 'open'
                 or (t(r.get('closed_at')) and now - t(r['closed_at']) <= dt.timedelta(hours=KEEP_CLOSED_HOURS))]
    d['updated_at'] = now_iso(now)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write('\n')


def clean(text, what):
    text = (text or '').strip()
    if ID_TOKEN.search(text):
        raise SystemExit(f'incomplete: no Publer ids or links in {what} (the work order is public)')
    return text


def open_row(path, story, nxt, job=None, run=None, slot=None, by=None, now=None):
    if not STORY.match(story or ''):
        raise SystemExit('incomplete: --story is a story id (letters, digits, dot, dash, underscore)')
    if not (nxt or '').strip():
        raise SystemExit('incomplete: --next says the one step the next run takes first')
    if job and not JOB.match(job):
        raise SystemExit('incomplete: --job is jobs/<live|render|test|breaking|done>/<name>.json')
    if run and not re.fullmatch(r'\d{5,20}', str(run)):
        raise SystemExit('incomplete: --run is the render run id (digits)')
    if slot and not t(slot):
        raise SystemExit('incomplete: --slot is an ISO time')
    d = load(path)
    row = {'story': story, 'state': 'open', 'next': clean(nxt, '--next'), 'job': job, 'run': str(run) if run else None,
           'slot': slot, 'by': clean(by, '--by') or None, 'at': now_iso(now)}
    old = [r for r in d['rows'] if r.get('story') == story and r.get('state') == 'open']
    if old:
        row['first_at'] = old[0].get('first_at') or old[0].get('at')
    d['rows'] = [r for r in d['rows'] if not (r.get('story') == story and r.get('state') == 'open')] + [row]
    save(path, d, now)
    return row


def close_row(path, story, outcome, now=None):
    d = load(path)
    hit = None
    for r in d['rows']:
        if r.get('story') == story and r.get('state') == 'open':
            r.update(state='closed', closed_at=now_iso(now), outcome=clean(outcome, '--outcome'))
            hit = r
    if not hit:
        raise SystemExit(f'incomplete: no open row for {story}')
    save(path, d, now)
    return hit


def open_rows(d):
    rows = (d or {}).get('rows') if isinstance(d, dict) else None
    return sorted([r for r in rows or [] if isinstance(r, dict) and r.get('state') == 'open'],
                  key=lambda r: str(r.get('first_at') or r.get('at') or ''))


def age_min(r, now):
    a = t(r.get('first_at') or r.get('at'))
    return int((now - a).total_seconds() // 60) if a else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=('open', 'close', 'show'))
    ap.add_argument('--file', required=True)
    ap.add_argument('--story')
    ap.add_argument('--next')
    ap.add_argument('--job')
    ap.add_argument('--run')
    ap.add_argument('--slot')
    ap.add_argument('--by')
    ap.add_argument('--outcome')
    a = ap.parse_args(argv)
    if a.cmd == 'open':
        print(json.dumps(open_row(a.file, a.story, a.next, a.job, a.run, a.slot, a.by), ensure_ascii=False))
    elif a.cmd == 'close':
        if not (a.outcome or '').strip():
            raise SystemExit('incomplete: --outcome says what was done (published, dropped and why)')
        print(json.dumps(close_row(a.file, a.story, a.outcome), ensure_ascii=False))
    else:
        now = dt.datetime.now(UTC)
        for r in open_rows(load(a.file)):
            print('%s (%s min): next %s; job %s; run %s' % (r['story'], age_min(r, now), r['next'], r.get('job') or '-',
                                                             r.get('run') or '-'))


if __name__ == '__main__':
    sys.exit(main())
