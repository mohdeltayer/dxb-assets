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
"""
import json, os, re, subprocess, sys

MARK = 'Failure marker'
COMMIT = 'Commit back'
JOB_NAME = re.compile(r'^render \((jobs/render/[A-Za-z0-9._-]+\.json)\)$')


def verdict(job, file_exists):
    """(retry?, why) for one matrix job of the failed run, from its Actions API record."""
    if job.get('conclusion') != 'failure':
        return False, f"conclusion {job.get('conclusion')}"
    steps = {s.get('name'): s for s in job.get('steps') or []}
    if steps.get(MARK, {}).get('conclusion') == 'success':
        return False, 'its own steps failed (failure marker ran): reported as it was'
    c = steps.get(COMMIT, {})
    if c.get('started_at') and c.get('conclusion') != 'skipped':
        return False, 'the commit step started: the Reel may have landed'
    if not file_exists:
        return False, 'the job file is gone from the branch: the Reel landed'
    return True, 'no error from our steps and nothing committed: runner lost'


def gh(*args):
    p = subprocess.run(['gh', *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr.strip()[-300:]


def main():
    repo, run, ref = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_REF_NAME']
    if os.environ.get('RETRY_INPUT') == '1' or os.environ.get('GITHUB_RUN_ATTEMPT', '1') != '1':
        print('render_retry: this run is itself a retry or a re-run; never retried again')
        return
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
        print(f'render_retry: {file}: {"RETRY" if ok else "no retry"}, {why}')
        if ok:
            rc, _, err = gh('workflow', 'run', 'render.yml', '--repo', repo, '--ref', ref, '-f', f'job={file}', '-f', 'retry=1')
            print(f'render_retry: {file}: dispatched' if rc == 0 else f'render_retry: {file}: dispatch failed: {err}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:                       # the retry is a convenience, never a failure of its own
        print(f'render_retry: {e}')
    sys.exit(0)
