"""One automatic retry for a render job whose runner was lost (render runner, 26 Oct 2026, safeguard 3).

A lost runner cannot be retried from inside its own job, so render.yml has a small follow-up job (`retry`, only on
failure) that runs this script. For every matrix job of the run that failed it asks the Actions API what happened and
re-dispatches the workflow for that job file, once, with `retry=1`, only when all of these hold:
  - the job ended `failure` and none of our own steps said so: the last step of the render job, "Failure marker",
    runs when any step fails or the run is cancelled, so a job whose marker never ran died without an error from
    our checks, the tools or the commit (a lost or preempted runner, a runner that never started);
  - the "Commit back" step never started, so nothing was pushed;
  - the job file is still on the branch (the render commit deletes it, so a missing file means the Reel landed);
  - this is the first attempt of a run that is not itself a retry (`retry` input empty, run attempt 1).
Everything else (a decode or smear check, the text check, pace, a step timeout, a failed install, a failed commit,
a human cancel) wrote the marker and is reported as it was, never retried. Nothing here prints a token.

    python3 render_retry.py          # in the retry job; GH_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_REF_NAME

Runner fix (Mohammad, 24 Nov 2026: keep overflowing to GitHub, fix the runner instead):
  - an install step that failed or hung past its own limit (INSTALL_STEPS: "Python packages" 5 minutes, "Tools" 5
    minutes) is retried once too, like a lost runner;
  - a render that is not retried (its own checks failed, or the retry itself failed) falls back to the server queue,
    never to nothing: the job file moves from jobs/render/ to jobs/live/ (contents API) and render-live runs with
    lane=server, which queues on dxb-render-1 and never overflows back. Not when the Reel landed (job file gone) or the
    commit step started.
"""
import json, os, re, subprocess, sys

MARK = 'Failure marker'
INSTALL_STEPS = ('Python packages', 'Tools')
COMMIT = 'Commit back'
JOB_NAME = re.compile(r'^render \((jobs/render/[A-Za-z0-9._-]+\.json)\)$')


def verdict(job, file_exists):
    """(retry?, why) for one matrix job of the failed run, from its Actions API record."""
    if job.get('conclusion') != 'failure':
        return False, f"conclusion {job.get('conclusion')}"
    steps = {s.get('name'): s for s in job.get('steps') or []}
    c = steps.get(COMMIT, {})
    hung = [n for n in INSTALL_STEPS if steps.get(n, {}).get('conclusion') in ('failure', 'cancelled')]
    if hung and not (c.get('started_at') and c.get('conclusion') != 'skipped') and file_exists:
        return True, f'install step "{hung[0]}" failed or hung past its limit: retried once'
    if steps.get(MARK, {}).get('conclusion') == 'success':
        return False, 'its own steps failed (failure marker ran): reported as it was'
    if c.get('started_at') and c.get('conclusion') != 'skipped':
        return False, 'the commit step started: the Reel may have landed'
    if not file_exists:
        return False, 'the job file is gone from the branch: the Reel landed'
    return True, 'no error from our steps and nothing committed: runner lost'


def fallback_ok(job, file_exists):
    """(fall back to the server?, why) for a failed runner render that is not retried."""
    if job.get('conclusion') not in ('failure', 'cancelled', 'timed_out'):
        return False, f"conclusion {job.get('conclusion')}"
    c = {s.get('name'): s for s in job.get('steps') or []}.get(COMMIT, {})
    if c.get('started_at') and c.get('conclusion') != 'skipped':
        return False, 'the commit step started: the Reel may have landed'
    if not file_exists:
        return False, 'the job file is gone from the branch: the Reel landed'
    return True, 'runner render failed: queued on the server (render-live lane=server)'


def to_server(repo, ref, file):
    """Moves jobs/render/<name>.json to jobs/live/ through the contents API and starts render-live with lane=server."""
    import base64
    name = file.rsplit('/', 1)[-1]
    rc, out, err = gh('api', f'repos/{repo}/contents/{file}?ref={ref}')
    if rc:
        return f'could not read {file}: {err}'
    meta = json.loads(out)
    body = {'message': f'Runner fallback: {name[:-5]} queued on the server (render-live lane=server; 24 Nov 2026)',
            'content': meta['content'].replace('\n', ''), 'branch': ref}
    dst = f'jobs/live/{name}'
    rc, o2, _ = gh('api', f'repos/{repo}/contents/{dst}?ref={ref}')
    if rc == 0:
        body['sha'] = json.loads(o2)['sha']
    rc, _, err = gh('api', '-X', 'PUT', f'repos/{repo}/contents/{dst}', '--input', '-', stdin=json.dumps(body))
    if rc:
        return f'could not write {dst}: {err}'
    gh('api', '-X', 'DELETE', f'repos/{repo}/contents/{file}', '--input', '-',
       stdin=json.dumps({'message': f'Runner fallback: {name[:-5]} moved to jobs/live', 'sha': meta['sha'], 'branch': ref}))
    rc, _, err = gh('workflow', 'run', 'render-live.yml', '--repo', repo, '--ref', ref, '-f', f'job={name[:-5]}', '-f', 'lane=server')
    return 'queued on the server' if rc == 0 else f'render-live dispatch failed: {err}'


def gh(*args, stdin=None):
    p = subprocess.run(['gh', *args], capture_output=True, text=True, input=stdin)
    return p.returncode, p.stdout, p.stderr.strip()[-300:]


def main():
    repo, run, ref = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_REF_NAME']
    if os.environ.get('GITHUB_RUN_ATTEMPT', '1') != '1':
        print('render_retry: a manual re-run; nothing automatic')
        return
    is_retry = os.environ.get('RETRY_INPUT') == '1'
    rc, out, err = gh('api', f'repos/{repo}/actions/runs/{run}/jobs?per_page=100')
    if rc:
        print(f'render_retry: could not read the run: {err}')
        return
    for job in json.loads(out).get('jobs', []):
        m = JOB_NAME.match(job.get('name') or '')
        if not m:
            continue
        file = m.group(1)
        exists = gh('api', f'repos/{repo}/contents/{file}?ref={ref}')[0] == 0
        ok, why = verdict(job, exists)
        if ok and is_retry:
            ok, why = False, why + '; but this run is already the retry'
        print(f'render_retry: {file}: {"RETRY" if ok else "no retry"}, {why}')
        if ok:
            rc, _, err = gh('workflow', 'run', 'render.yml', '--repo', repo, '--ref', ref, '-f', f'job={file}', '-f', 'retry=1')
            if rc == 0:
                print(f'render_retry: {file}: dispatched')
                continue
            print(f'render_retry: {file}: dispatch failed: {err}')
        fb, fwhy = fallback_ok(job, exists)
        print(f'render_retry: {file}: {"SERVER FALLBACK" if fb else "no fallback"}, {fwhy}')
        if fb:
            print(f'render_retry: {file}: ' + to_server(repo, ref, file))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:                       # the retry is a convenience, never a failure of its own
        print(f'render_retry: {e}')
    sys.exit(0)
