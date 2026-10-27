"""Two small steps for .github/workflows/prerender.yml, stdlib only (the server has no gh).

    python3 templates/prerender_ci.py gate    wait up to PRERENDER_WAIT seconds (default 300) for the job named `server`
                                              to leave the queue; writes `fallback=true` to $GITHUB_OUTPUT when it never
                                              got a runner (the dxb-render server is busy or down), else `false`
    python3 templates/prerender_ci.py yielded the server job's first step, for a server that picks the job up late: writes
                                              `skip=1` to $GITHUB_OUTPUT when the GitHub-hosted fallback already ran, so
                                              the same checks are not read twice

Reads this run's own job records with the workflow's read-only token (`actions: read`); writes nothing anywhere else.
"""
import json
import os
import sys
import time
import urllib.request


def jobs():
    url = 'https://api.github.com/repos/%s/actions/runs/%s/attempts/%s/jobs?per_page=100' % (
        os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_RUN_ID'], os.environ.get('GITHUB_RUN_ATTEMPT', '1'))
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req, timeout=30))['jobs']


def named(name):
    return next((j for j in jobs() if j['name'] == name), None)


def out(k, v):
    print(f'{k}={v}', flush=True)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f'{k}={v}\n')


def gate():
    wait = int(os.environ.get('PRERENDER_WAIT') or 300)
    t0 = time.time()
    while True:
        try:
            j = named('server')
        except Exception as e:                       # noqa: BLE001  an API blip is not a reason to run the fallback
            print('jobs API:', e, flush=True)
            j = {'status': 'queued'} if time.time() - t0 < wait else None
        if j and j['status'] != 'queued':                 # (no record yet counts as queued: the job is still being created)
            print(f"server job {j['status']} after {time.time() - t0:.0f} s: no fallback", flush=True)
            return out('fallback', 'false')
        if time.time() - t0 >= wait:
            print(f'server job still queued after {wait} s: the GitHub-hosted fallback runs the checks', flush=True)
            return out('fallback', 'true')
        time.sleep(10)


def yielded():
    try:
        j = named('fallback')
    except Exception as e:                           # noqa: BLE001
        print('jobs API:', e, flush=True)
        j = None
    ran = bool(j) and (j['status'] == 'in_progress' or (j['status'] == 'completed' and j.get('conclusion') != 'skipped'))
    print('fallback already ran: this job stands down' if ran else 'no fallback ran: the server reads the footage', flush=True)
    out('skip', '1' if ran else '0')


if __name__ == '__main__':
    {'gate': gate, 'yielded': yielded}[sys.argv[1]]()
