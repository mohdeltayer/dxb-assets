"""Job versions and dispatches per Reel (adv-20261110-one-render-per-reel, item G and the measure, Mohammad 10 Nov 2026).

On 10 Nov a Warhammer Survivors re-render took the job back from git and rendered v1 instead of v3. Every server render
now records the job file's blob sha (`git hash-object`) in its render-times entry as `job_sha`, with `dispatches`: the
renders of the same story in the last 24 hours, this one included (target 1; the work order alarms at 3).

    python3 templates/jobsha.py check <story> <sha>     refuses a job whose sha an earlier render of the story used when a
                                                       later render used another one (an older version restored)
    python3 templates/jobsha.py count <story>           prints the dispatches this render makes
"""
import datetime as dt
import json
import os
import sys

TIMES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'render-times.json')
WINDOW_H = 24
ALARM = 3


def _entries(path=TIMES):
    try:
        d = json.load(open(path, encoding='utf-8'))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _at(e):
    for k in ('finished_at', 'at', 'date', 'ts'):
        v = e.get(k)
        if v:
            try:
                x = dt.datetime.fromisoformat(str(v).replace('Z', '+00:00'))
                return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
            except ValueError:
                continue
    return None


def of_story(story, entries):
    return [e for e in entries if isinstance(e, dict) and str(e.get('story') or e.get('name') or '').startswith(story)]


def check(story, sha, entries):
    """None when fine; the reason when `sha` is an older version of the story's job than the last one rendered."""
    rows = [e for e in of_story(story, entries) if e.get('job_sha')]
    if not rows or rows[-1]['job_sha'] == sha:
        return None
    if any(e['job_sha'] == sha for e in rows[:-1]):
        return (f'{story}: this job file is an older version (sha {sha[:8]}) than the last one rendered '
                f'({rows[-1]["job_sha"][:8]}); write the fix onto the current job, never restore an earlier commit')
    return None


def count(story, entries, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    n = 0
    for e in of_story(story, entries):
        t = _at(e)
        if t is None or (now - t).total_seconds() <= WINDOW_H * 3600:
            n += 1
    return n + 1


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['check'] and len(a) == 3:
        r = check(a[1], a[2], _entries())
        if r:
            print(f'::error::{r}')
            sys.exit(1)
        print(f'job version: {a[2][:8]} ok')
    elif a[:1] == ['count'] and len(a) == 2:
        print(count(a[1], _entries()))
    else:
        raise SystemExit(__doc__)
