"""A dispatch takes a job name or a path (adv-20261110-one-render-per-reel, item B, Mohammad 10 Nov 2026).

The first of seven Warhammer Survivors dispatches failed in 11 s: the job input had to be the full path. Every render and
prerender workflow now resolves its `job` input here: a path (jobs/<dir>/<name>.json) is kept as it is; a bare name
(`warhammer-survivors-out-now-november-10`, with or without .json) is looked up in the workflow's folders, in order, and
must match exactly one file.

    python3 templates/jobpath.py <workflow> <input>      prints the path; exit 1 with the reason
    workflows: live (jobs/live), render (jobs/render), breaking (jobs/breaking, jobs/test),
               prerender (jobs/prerender, jobs/live, jobs/render, jobs/breaking, jobs/test)
"""
import os
import re
import sys

DIRS = {
    'live': ['jobs/live'],
    'render': ['jobs/render'],
    'breaking': ['jobs/breaking', 'jobs/test'],
    'prerender': ['jobs/prerender', 'jobs/live', 'jobs/render', 'jobs/breaking', 'jobs/test'],
}
PATH = re.compile(r'^jobs/(?:render|live|prerender|test|breaking)/[A-Za-z0-9._-]+\.json$')
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,150}$')


def resolve(workflow, value, root='.'):
    v = (value or '').strip()
    if workflow not in DIRS:
        raise ValueError(f'workflow {workflow!r}: one of {", ".join(DIRS)}')
    allowed = DIRS[workflow]
    if '/' in v:
        if not PATH.match(v) or os.path.dirname(v) not in allowed:
            raise ValueError(f'job {v!r}: a path must be one of {", ".join(d + "/<name>.json" for d in allowed)}, '
                             'or give the bare name')
        if not os.path.exists(os.path.join(root, v)):
            raise ValueError(f'{v} is not on main')
        return v
    if not NAME.match(v):
        raise ValueError(f'job {v!r}: a name (letters, digits, dot, dash, underscore) or jobs/<dir>/<name>.json')
    name = v[:-5] if v.endswith('.json') else v
    hits = [f'{d}/{name}.json' for d in allowed if os.path.exists(os.path.join(root, d, name + '.json'))]
    if not hits:
        raise ValueError(f'no job named {name!r} in {", ".join(allowed)} on main; commit it first')
    if len(hits) > 1:
        raise ValueError(f'{name!r} is in more than one folder ({", ".join(hits)}); give the path')
    return hits[0]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    try:
        print(resolve(sys.argv[1], sys.argv[2]))
    except ValueError as e:
        print(f'::error::{e}', file=sys.stderr)
        sys.exit(1)
