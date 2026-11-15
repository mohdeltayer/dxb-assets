"""Weekly count of director send-backs by reason (adv-20261115-one-render-server-checks item F, Mohammad 15 Nov 2026).

Every send-back the director makes on a Reel the server qc passed is one line under `director_sendbacks` in the Reel's
cards/YYYY-MM/<name>-qc.json (presubmit.py director FIX --reason ...) and in its story file. Once a week this counts them
by reason code over the last DAYS days; any reason seen THRESHOLD times or more is a candidate server check and goes on
a card for the build desk (the reason, the Reels, the notes).

    python3 ops/sendbacks.py [--days 7] [--card out.json]      prints the table; --card writes the inbox card when a
                                                                 reason reaches the threshold (exit 2), else nothing

Reads origin/main through git (the slim clone has no cards/ on disk): file names from the log, contents with git show.
"""
import collections
import datetime as dt
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DAYS = 7
THRESHOLD = 3


def _git(*a):
    r = subprocess.run(['git', '-C', str(REPO), *a], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def _paths(days):
    subprocess.run(['git', '-C', str(REPO), 'fetch', '-q', '--depth', '200', '--filter=blob:none', 'origin', 'main'],
                   capture_output=True)
    out = set()
    for ln in _git('log', f'--since={days}.days', '--format=', '--name-only', 'origin/main', '--',
                   'cards/', 'newsroom/stories/').splitlines():
        ln = ln.strip()
        if ln.endswith('-qc.json') or (ln.startswith('newsroom/stories/') and ln.endswith('.json')):
            out.add(ln)
    return sorted(out)


def collect(days=DAYS, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=days)
    seen, rows = set(), []
    for p in _paths(days):
        raw = _git('show', f'origin/main:{p}')
        try:
            d = json.loads(raw) if raw else {}
        except ValueError:
            continue
        for x in d.get('director_sendbacks') or []:
            try:
                t = dt.datetime.fromisoformat(str(x.get('at')).replace('Z', '+00:00'))
            except ValueError:
                continue
            t = t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
            key = (x.get('out'), x.get('at'), x.get('reason'))
            if t < since or key in seen:
                continue
            seen.add(key)
            rows.append(dict(x, source=p))
    return rows


def summary(rows):
    by = collections.defaultdict(list)
    for x in rows:
        by[x.get('reason') or '?'].append(x)
    return dict(sorted(by.items(), key=lambda kv: -len(kv[1])))


def card(by, days=DAYS):
    hot = {k: v for k, v in by.items() if len(v) >= THRESHOLD and k != 'qc_fail'}
    if not hot:
        return None
    today = dt.date.today().isoformat()
    body = '\n'.join(f'- {k}: {len(v)} send-backs in {days} days: ' + '; '.join(
        f"{pathlib.Path(str(x.get('out'))).name} ({x.get('note') or 'no note'})" for x in v[:6]) for k, v in hot.items())
    return {'id': f'prod-{today.replace("-", "")}-sendback-candidates', 'from': 'production', 'to': 'advisor',
            'kind': 'decision', 'status': 'open', 'desk': 'build',
            'title': 'Candidate server checks: director send-back reasons seen 3 times this week',
            'summary': f'{len(hot)} reason{"s" if len(hot) > 1 else ""} reached {THRESHOLD} send-backs in {days} days; '
                       'each is a candidate for a check that runs before the first render.',
            'body': body + '\n\nadv-20261115-one-render-server-checks item F (ops/sendbacks.py).',
            'options': [{'label': 'Build the check', 'effect': 'The build desk turns the reason into a pre-render check.'},
                        {'label': 'Not now', 'effect': 'Recorded; counted again next week.'}],
            'created_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}


def main(argv):
    days = int(argv[argv.index('--days') + 1]) if '--days' in argv else DAYS
    rows = collect(days)
    by = summary(rows)
    print(f'director send-backs, last {days} days: {len(rows)}')
    for k, v in by.items():
        print(f'  {k:16} {len(v):3}' + ('  <- candidate server check' if len(v) >= THRESHOLD and k != 'qc_fail' else ''))
    c = card(by, days)
    if '--card' in argv and c:
        json.dump(c, open(argv[argv.index('--card') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('card written: ' + c['id'])
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
