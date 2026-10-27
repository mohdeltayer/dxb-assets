"""Retries per Reel and first-commit-to-receipt minutes, from git history alone (prerender checks, 27 Oct 2026).

    python3 newsroom/render_retries.py [days=3] [ref=origin/main] [--causes]

For every story that got a Publer receipt in the window (cards/YYYY-MM/<name>-reel-vN-publer.json, added by the
render workflow's "Publer receipt" commit):
  job commits   commits that added or changed jobs/render/<name>.json (or jobs/live/): the versions production pushed
  retries       job commits - 1 (a fix pushed after a failed or rejected render)
  renders       the render workflow's commits that removed the job file (a render that finished)
  minutes       first job commit to the story's first receipt commit
Reads `git log --format --name-status` only (trees, never file contents), so it is safe on the slim partial clone.
A job re-dispatched without a change, and a render that failed without a commit, leave no trace in git and are not
counted: the retry numbers are a floor.
"""
import collections
import re
import statistics
import subprocess
import sys


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True, check=True).stdout


def log(ref, since, *paths, extra=()):
    out, cur = [], None
    for ln in git('log', f'--since={since}', '--format=C %H %ct %s', '--name-status', *extra, ref, '--', *paths).splitlines():
        if ln.startswith('C '):
            _, h, ct, subj = ln.split(' ', 3)
            cur = (h[:7], int(ct), subj)
        elif ln.strip() and cur:
            st, path = ln.split('\t', 1)
            out.append((cur, st[0], path))
    return out


# A retry is a later commit of the same job file; its subject says why. These words in it mark a fix to the footage
# (a bad stretch, a flagged source, a wrong stretch), the part prerender.py is meant to catch; the rest are text,
# timing, strip and spelling fixes it does not touch. A heuristic from the subjects, not a record of the cause.
SOURCE = re.compile(r'smear|black|blocky|letterbox|title card|fade|flash|offset|bars|flicker|slate|end card|dark|source flag|'
                    r'lowbit|decode|damaged|frozen|item card|clean picture|trim', re.I)


def stats(days=3, ref='origin/main'):
    since = f'{days + 2} days ago'            # the first job commit of a story whose receipt is in the window may be older
    jobs = collections.defaultdict(list)
    renders = collections.defaultdict(list)
    for (h, ct, subj), st, path in log(ref, since, 'jobs/render', 'jobs/live'):
        m = re.match(r'jobs/(?:render|live)/([^/]+)\.json$', path)
        if not m or m.group(1) == 'README':
            continue
        (renders if st == 'D' else jobs)[m.group(1)].append((ct, h, subj))
    receipts = collections.defaultdict(list)
    for (h, ct, subj), st, path in log(ref, f'{days} days ago', 'cards', extra=('--diff-filter=A',)):
        m = re.match(r'cards/[^/]+/(.+)-reel-v\d+-publer\.json$', path)
        if m:
            receipts[m.group(1)].append((ct, h))
    rows = []
    for name, rc in receipts.items():
        js = sorted(jobs.get(name, []))
        if not js:
            continue
        first = js[0][0]
        got = sorted(r for r in rc if r[0] >= first)
        if not got:
            continue
        rows.append({'name': name, 'job_commits': len(js), 'retries': len(js) - 1, 'renders': len(renders.get(name, [])),
                     'minutes': round((got[0][0] - first) / 60, 1), 'first_job': js[0][1], 'receipt': got[0][1],
                     'fixes': [(h, subj) for _, h, subj in js[1:]]})
    rows.sort(key=lambda r: -r['minutes'])
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    days = int(args[0]) if args else 3
    ref = args[1] if len(args) > 1 else 'origin/main'
    rows = stats(days, ref)
    if not rows:
        print('no receipts with a job commit in the window'); return
    print(f'{"story":58} {"jobs":>4} {"retry":>5} {"renders":>7} {"min":>6}')
    for r in rows:
        print(f'{r["name"][:58]:58} {r["job_commits"]:>4} {r["retries"]:>5} {r["renders"]:>7} {r["minutes"]:>6}')
    mins = [r['minutes'] for r in rows]
    ret = [r['retries'] for r in rows]
    print(f'\nReels {len(rows)} (last {days} days, {ref})')
    print(f'retries per Reel: mean {statistics.mean(ret):.2f}, {sum(1 for x in ret if x)} of {len(ret)} had at least one, '
          f'worst {max(ret)}; job commits per Reel mean {statistics.mean(r["job_commits"] for r in rows):.2f}')
    print(f'first commit to receipt (min): median {statistics.median(mins):.1f}, mean {statistics.mean(mins):.1f}, '
          f'worst {max(mins):.1f} ({rows[0]["name"]}), best {min(mins):.1f}')
    if '--causes' in sys.argv:
        fx = [(r['name'], h, subj) for r in rows for h, subj in r['fixes']]
        src = [x for x in fx if SOURCE.search(x[2])]
        print(f'\nretry commits: {len(fx)}; subject names a footage fix: {len(src)} (heuristic)')
        for n, h, subj in fx:
            print(f'  {"SRC" if SOURCE.search(subj) else "   "} {n[:40]:40} {h} {subj[:110]}')
        print(f'stories with a footage-fix retry: {len({n for n, *_ in src})} of {len(rows)}')
    one = [r['minutes'] for r in rows if r['retries'] == 0]
    many = [r['minutes'] for r in rows if r['retries']]
    if one and many:
        print(f'no retry: median {statistics.median(one):.1f} min (n={len(one)}); with a retry: median {statistics.median(many):.1f} min (n={len(many)})')


if __name__ == '__main__':
    main()
