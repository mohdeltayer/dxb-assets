"""Lane choice for the T0 breaking render (render-breaking.yml, 27 Oct 2026): a breaking job never waits in a queue.

  route    (GitHub-hosted, a few seconds) `busy`: the dxb-render server is taken when any run of this repository has a job
           on a runner labelled dxb-render that is queued or in progress (another render, a server check, another T0
           job). Free: lane `server`. Taken: lane `hosted`, and the server is not asked at all.
  hosted   (only when the lane is `server`, as a standby) `standby`: waits up to GRACE seconds for the run's `server` job
           to start. Started: the server renders and this job stands down. Not started (the server is offline or slow):
           this job claims the render by running the step named CLAIM, and renders on GitHub.
  server   its first step runs `claim`: if the hosted job already ran CLAIM, the server stands down. Both deciding in the
           same few seconds would render twice; the second commit then rebases over an identical file, which is harmless.

Every function prints what it saw and writes `go=true|false` (or `lane=`) to $GITHUB_OUTPUT. Nothing here prints a token.
Needs GH_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID; the workflow grants `actions: read`.

    python3 render_route.py busy | standby | claim
"""
import json, os, subprocess, sys, time

LABEL = 'dxb-render'
CLAIM = 'Hosted render claimed'
GRACE = int(os.environ.get('T0_GRACE', '25'))


def gh(path):
    p = subprocess.run(['gh', 'api', path], capture_output=True, text=True, timeout=40)
    if p.returncode:
        raise RuntimeError(p.stderr.strip()[-200:])
    return json.loads(p.stdout)


def out(k, v):
    print(f'render_route: {k}={v}', flush=True)
    if os.environ.get('GITHUB_OUTPUT'):
        open(os.environ['GITHUB_OUTPUT'], 'a').write(f'{k}={v}\n')


def jobs_of(repo, run):
    return gh(f'repos/{repo}/actions/runs/{run}/jobs?per_page=100&filter=latest').get('jobs', [])


def busy(repo, me):
    """Names of jobs holding or waiting for the server, from every other live run."""
    held = []
    for status in ('in_progress', 'queued'):
        for r in gh(f'repos/{repo}/actions/runs?status={status}&per_page=50').get('workflow_runs', []):
            if str(r['id']) == str(me):
                continue
            for j in jobs_of(repo, r['id']):
                if j.get('status') in ('queued', 'in_progress') and LABEL in (j.get('labels') or []):
                    held.append(f"{r.get('name')}/{j.get('name')} ({j.get('status')})")
    return held


def main(what):
    repo, run = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_RUN_ID']
    forced = os.environ.get('LANE_INPUT', 'auto')
    if what == 'busy':
        if forced in ('server', 'hosted'):
            out('lane', forced)
            return
        try:
            held = busy(repo, run)
        except Exception as e:                          # cannot tell: GitHub is the safe lane, it never waits on the server
            print(f'render_route: could not read the runs ({e}); hosted')
            out('lane', 'hosted')
            return
        print('render_route: server holders: ' + ('; '.join(held) or 'none'))
        out('lane', 'hosted' if held else 'server')
    elif what == 'standby':
        t0 = time.time()
        while time.time() - t0 < GRACE:
            try:
                sv = [j for j in jobs_of(repo, run) if j.get('name') == 'server']
            except Exception:
                sv = []
            if sv and sv[0].get('status') in ('in_progress', 'completed'):
                print(f'render_route: the server picked the job up after {time.time() - t0:.0f} s; standing down')
                out('go', 'false')
                return
            time.sleep(3)
        print(f'render_route: the server did not start within {GRACE} s; rendering on GitHub')
        out('go', 'true')
    elif what == 'claim':
        try:
            hj = [j for j in jobs_of(repo, run) if j.get('name') == 'hosted']
            taken = any(s.get('name') == CLAIM and s.get('status') in ('in_progress', 'completed')
                        for j in hj for s in j.get('steps') or [])
        except Exception:
            taken = False
        print('render_route: ' + ('GitHub already claimed this render; the server stands down' if taken else 'the server renders'))
        out('go', 'false' if taken else 'true')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
