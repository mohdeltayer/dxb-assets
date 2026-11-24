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
    python3 render_route.py live <job.json>      render-live's route job: lane server or overflow

Server lanes (Mohammad, 19 Nov 2026): templates/assets/server-lanes.json sets `runners` (runner instances on dxb-render-1),
`render_slots` (renders at once for a normal job) and `t0_reserve` (extra render slots only T0 and breaking jobs take).
A job goes to the server when fewer renders than its limit are on the server (normal: render_slots; T0 and breaking:
render_slots + t0_reserve, and a runner instance must be free so it never waits); otherwise a normal job overflows to render.yml at once and a
T0 job renders on a GitHub runner, so nothing waits in a queue behind a render. Reads and checks (prerender, watch,
server checks) are not renders: they take any free instance and are never counted against the render slots.
"""
import json, os, subprocess, sys, time

LABEL = 'dxb-render'
LANES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'server-lanes.json')


def lanes():
    try:
        c = json.load(open(LANES))
    except (OSError, ValueError):
        c = {}
    c.setdefault('runners', 1)
    c.setdefault('render_slots', 1)
    c.setdefault('t0_reserve', 0)
    c.setdefault('render_jobs', {'render-live': ['live'], 'render-breaking': ['server'], 'server-capacity-test': ['capacity']})
    return c


SEEN_FROM = {'watch-digest.yml': 24, 'render-live.yml': 12, 'server-check.yml': 4}    # workflows that run on the server


def runners_seen(repo, held_names=()):
    """Distinct runner instances (label dxb-render) seen on recent server jobs and on the jobs holding the server now.
    At least 1; on any error 1, which keeps today's single-lane routing."""
    names = set(n for n in held_names if n)
    try:
        for wf, n in SEEN_FROM.items():
            for r in gh(f'repos/{repo}/actions/workflows/{wf}/runs?per_page={n}').get('workflow_runs', []):
                for j in jobs_of(repo, r['id']):
                    if LABEL in (j.get('labels') or []) and j.get('runner_name'):
                        names.add(j['runner_name'])
    except Exception as e:
        print(f'render_route: could not count runner instances ({e}); assuming 1')
        return 1, sorted(names)
    return max(1, len(names)), sorted(names)


def effective(c, count):
    """render_slots and t0_reserve cut to the instances that exist: slots <= runners, slots + reserve <= runners."""
    slots = max(1, min(c['render_slots'], count))
    return dict(c, runners=count, render_slots=slots, t0_reserve=max(0, min(c['t0_reserve'], count - slots)))


def priority(job):
    """T0 and breaking jobs: a slip of tier 0, a job marked tier 0 / T0 or priority, the breaking profile or kind."""
    tier = job.get('tier', (job.get('slip') or {}).get('tier'))
    return (str(tier).upper() in ('0', 'T0') or job.get('priority') is True or job.get('profile') == 'breaking'
            or job.get('kind') == 'breaking')


def decide(holders, is_priority, c=None):
    """holders: [(workflow, job name, status)] on the server. Returns (lane, reason)."""
    c = c or lanes()
    rj = c['render_jobs']
    renders = [h for h in holders if h[1] in rj.get(h[0], [])]
    limit = c['render_slots'] + (c['t0_reserve'] if is_priority else 0)
    free = c['runners'] - len(holders)
    why = f"{len(renders)} render(s) and {len(holders) - len(renders)} other job(s) on the server; " \
          f"{c['runners']} runner(s), render limit {limit}{' (T0)' if is_priority else ''}"
    if len(renders) < limit and (free >= 1 or not is_priority):
        return 'server', why                    # a normal job may wait a moment behind a read; a T0 job never waits
    if not c.get('overflow', True):             # 24 Nov 2026: GitHub overflow timed out at 15 minutes; queue on the server
        return 'server', why + '; overflow off (server-lanes.json): queued on the server until lanes 2 and 3 exist'
    return 'overflow', why
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


def holders(repo, me):
    """(workflow, job, status) of every job holding or waiting for the server, from every other live run."""
    held = []
    for status in ('in_progress', 'queued'):
        for r in gh(f'repos/{repo}/actions/runs?status={status}&per_page=50').get('workflow_runs', []):
            if str(r['id']) == str(me):
                continue
            for j in jobs_of(repo, r['id']):
                if j.get('status') in ('queued', 'in_progress') and LABEL in (j.get('labels') or []):
                    held.append((r.get('name'), j.get('name'), j.get('status')))
                    if j.get('runner_name'):
                        RUNNING.add(j['runner_name'])
    return held


RUNNING = set()


def config(repo):
    c = lanes()
    if c['runners'] == 'auto':
        count, names = runners_seen(repo, RUNNING)
        print(f"render_route: runner instances seen: {count} ({', '.join(names) or 'none named'})")
    else:
        count = int(c['runners'])
    c = effective(c, count)
    print(f"render_route: lanes in force: {c['runners']} instance(s), {c['render_slots']} render slot(s), "
          f"{c['t0_reserve']} T0 reserve")
    return c


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
            held = holders(repo, run)
        except Exception as e:                          # cannot tell: GitHub is the safe lane, it never waits on the server
            print(f'render_route: could not read the runs ({e}); hosted')
            out('lane', 'hosted')
            return
        print('render_route: server holders: ' + ('; '.join(f'{w}/{j} ({s})' for w, j, s in held) or 'none'))
        lane, why = decide(held, True, config(repo))    # a breaking job is T0: it may take the reserved slot
        print('render_route: ' + why)
        out('lane', 'server' if lane == 'server' else 'hosted')
    elif what == 'live':
        job = json.load(open(sys.argv[2]))
        try:
            held = holders(repo, run)
        except Exception as e:                          # cannot tell: the server is still the default for the live lane
            print(f'render_route: could not read the runs ({e}); server')
            out('lane', 'server')
            return
        print('render_route: server holders: ' + ('; '.join(f'{w}/{j} ({s})' for w, j, s in held) or 'none'))
        lane, why = decide(held, priority(job), config(repo))
        print('render_route: ' + why + f' -> {lane}')
        out('lane', lane)
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
