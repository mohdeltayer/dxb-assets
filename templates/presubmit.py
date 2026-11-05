"""Pre-submit step for every Publer submit (adv-20261105-p2-audit-fixes, items 2 and 3, 5 Nov 2026).

Production 2's audit found Reels submitted with no director check, the same story submitted three times and twice
again on retries, and published writebacks and the heartbeat skipped. Publer is reached through the connector, so
code cannot stand in front of it; this script is the step the session runs around every submit, and it refuses
instead of letting a skipped step through. The file a check passed is bound by its git blob id: any re-render
changes the id and the director check must be run again.

    python3 templates/presubmit.py director <story> PASS <out.mp4> --job <job.json> [--note "..."]   # after the director check
    python3 templates/presubmit.py intent <commitment> <platform> <story> <out.mp4>    # before submit_publer_posts
    python3 templates/presubmit.py result <commitment> <platform> scheduled|failed     # after the submit returns
    python3 templates/presubmit.py published <commitment> <story> --links <ig> <x> <threads> [--queue <dxb-queue clone>]
    python3 templates/presubmit.py show <commitment>

director PASS needs --job: the job file that rendered this Reel (the local copy the build wrote; the render removes it
from main). Its "out" must be this file and the build gate (templates/buildgate.py: story, lane, reel_check with no
"no", stills reason) must pass; the result is recorded with the job's sha256 (adv-20261102-reel-checklist point 3).

intent refuses (exit 1) when:
  - the story has no director PASS for exactly this file (its blob id on origin/main),
  - that PASS carries no passed checklist (reel_check) from the job that made the file,
  - the same commitment and platform already have an intent that is not marked failed: look the post up in Publer
    (list_publer_posts by caption) first; never submit it again.
published writes the story's `published` block, one line in newsroom/published.jsonl and, with --queue, the
heartbeat (ops/heartbeat.json in the dxb-queue clone; commit and push it there). Intents live in
newsroom/submissions.jsonl: commit it with the story file after each step.
Platforms: instagram, x, threads.
"""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
STORIES = REPO / 'newsroom' / 'stories'
LOG = REPO / 'newsroom' / 'submissions.jsonl'
PUBLISHED = REPO / 'newsroom' / 'published.jsonl'
PLATFORMS = ('instagram', 'x', 'threads')


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def blob(out):
    """Git blob id of the rendered file on origin/main (tree lookup only; the video itself is never downloaded)."""
    subprocess.run(['git', '-C', str(REPO), 'fetch', '-q', '--depth', '1', '--filter=blob:none', 'origin', 'main'],
                   check=False)
    for ref in ('origin/main', 'HEAD'):
        r = subprocess.run(['git', '-C', str(REPO), 'rev-parse', f'{ref}:{out}'], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    raise SystemExit(f'presubmit: {out} is not on main; the render commit must land first')


def story(sid):
    f = STORIES / f'{sid}.json'
    if not f.exists():
        raise SystemExit(f'presubmit: no story file newsroom/stories/{sid}.json')
    return f, json.loads(f.read_text())


def entries():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]


def append(path, row):
    with open(path, 'a') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')


def last_state(commitment, platform):
    rows = [r for r in entries() if r.get('commitment') == commitment and r.get('platform') == platform]
    return rows[-1] if rows else None


def checklist(job_path, out):
    """The job's checklist verdict: {'job', 'sha256', 'ok', 'problems'} (build gate on the job that made `out`)."""
    sys.path.insert(0, str(REPO / 'templates'))
    import buildgate
    raw = pathlib.Path(job_path).read_bytes()
    job = json.loads(raw)
    probs = buildgate.problems(job_path, job)
    if job.get('out') and job['out'] != out:
        probs.append(f'job "out" is {job["out"]}, not {out}')
    return {'job': buildgate._rel(job_path), 'sha256': hashlib.sha256(raw).hexdigest(), 'ok': not probs,
            'problems': probs}


def director(sid, verdict, out, note='', job=None):
    if verdict not in ('PASS', 'FIX'):
        raise SystemExit('presubmit: verdict is PASS or FIX')
    f, s = story(sid)
    cl = checklist(job, out) if job else None
    if verdict == 'PASS':
        if not cl:
            raise SystemExit('presubmit: director PASS needs --job <the job file that rendered it> (its reel_check)')
        if not cl['ok']:
            raise SystemExit('presubmit refused: the job does not pass the build gate:\n  - ' + '\n  - '.join(cl['problems']))
    s['director_check'] = {'verdict': verdict, 'out': out, 'blob': blob(out), 'at': now(), 'note': note,
                           'checklist': cl}
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n')
    print(f'director {verdict} recorded for {out} ({s["director_check"]["blob"][:10]})')


def intent(commitment, platform, sid, out):
    if platform not in PLATFORMS:
        raise SystemExit(f'presubmit: platform is one of {", ".join(PLATFORMS)}')
    _, s = story(sid)
    d = s.get('director_check') or {}
    b = blob(out)
    if d.get('verdict') != 'PASS' or d.get('blob') != b:
        raise SystemExit(f'presubmit refused: no director PASS for this file ({out}, {b[:10]}); '
                         f'run the director check, then presubmit.py director {sid} PASS {out} --job <job>')
    if not (d.get('checklist') or {}).get('ok'):
        raise SystemExit(f'presubmit refused: the director PASS for {out} carries no passed checklist; '
                         f'record it again with --job <job file> (reel_check, story, lane)')
    prev = last_state(commitment, platform)
    if prev and prev.get('state') != 'failed':
        raise SystemExit(f'presubmit refused: {commitment} on {platform} already has a submit ({prev.get("state")} '
                         f'at {prev.get("at")}). Look the post up in Publer first; never submit it twice.')
    append(LOG, {'commitment': commitment, 'platform': platform, 'story': sid, 'file_blob': b,
                 'state': 'intent', 'at': now()})
    print(f'intent recorded: {commitment} {platform}; submit now, then presubmit.py result')


def result(commitment, platform, state):
    if state not in ('scheduled', 'failed', 'published'):
        raise SystemExit('presubmit: state is scheduled, failed or published')
    prev = last_state(commitment, platform)
    if not prev:
        raise SystemExit(f'presubmit: no intent for {commitment} {platform}')
    append(LOG, dict(prev, state=state, at=now()))
    print(f'{commitment} {platform}: {state}')


def published(commitment, sid, links, queue=None):
    f, s = story(sid)
    rows = {p: last_state(commitment, p) for p in PLATFORMS}
    missing = [p for p, r in rows.items() if not r]
    if missing:
        print(f'presubmit: note: no intent recorded for {", ".join(missing)}')
    for p, r in rows.items():
        if r and r.get('state') != 'published':
            append(LOG, dict(r, state='published', at=now()))
    at = now()
    s['published'] = {'at': at, 'commitment': commitment, 'links': links}
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n')
    append(PUBLISHED, {'story': sid, 'commitment': commitment, 'title': s.get('title'), 'chip': s.get('chip'),
                       'template': s.get('template'), 'published_at': at, 'links': links})
    if queue:
        hb = pathlib.Path(queue) / 'ops' / 'heartbeat.json'
        hb.parent.mkdir(parents=True, exist_ok=True)
        hb.write_text(json.dumps({'last_published': at, 'story': sid, 'checked_at': at}, indent=1) + '\n')
        print(f'heartbeat written: {hb} (commit and push it in dxb-queue)')
    else:
        print('heartbeat not written: pass --queue <dxb-queue clone> (ops/heartbeat.json), then push it')
    print(f'published recorded: {sid} in newsroom/published.jsonl and the story file')


def show(commitment):
    for r in entries():
        if r.get('commitment') == commitment:
            print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    cmd = a[0]
    if cmd == 'director' and len(a) >= 4:
        note = a[a.index('--note') + 1] if '--note' in a else ''
        jobp = a[a.index('--job') + 1] if '--job' in a else None
        director(a[1], a[2], a[3], note, jobp)
    elif cmd == 'intent' and len(a) == 5:
        intent(*a[1:5])
    elif cmd == 'result' and len(a) == 4:
        result(*a[1:4])
    elif cmd == 'published' and len(a) >= 3:
        links = a[a.index('--links') + 1:a.index('--links') + 4] if '--links' in a else []
        q = a[a.index('--queue') + 1] if '--queue' in a else None
        published(a[1], a[2], links, q)
    elif cmd == 'show' and len(a) == 2:
        show(a[1])
    else:
        raise SystemExit(__doc__)
