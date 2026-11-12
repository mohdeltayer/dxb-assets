"""Pre-submit step for every Publer submit (adv-20261105-p2-audit-fixes, items 2 and 3, 5 Nov 2026).

Production 2's audit found Reels submitted with no director check, the same story submitted three times and twice
again on retries, and published writebacks and the heartbeat skipped. Publer is reached through the connector, so
code cannot stand in front of it; this script is the step the session runs around every submit, and it refuses
instead of letting a skipped step through. The file a check passed is bound by its git blob id: any re-render
changes the id and the director check must be run again.

    python3 templates/presubmit.py director <story> PASS <out.mp4> --job <job.json> --by <director> [--note "..."] [--looked "<what the three look frames show>"]
    python3 templates/presubmit.py intent <commitment> <platform> <story> <out.mp4> --labels kind:news,tpl:trailer [--slot ISO]
                                                                     # before submit_publer_posts
    python3 templates/presubmit.py line <commitment> --ids ig:<last6> x:<last6> th:<last6>   # the board's scheduled line
    python3 templates/presubmit.py result <commitment> <platform> scheduled|failed --job-status complete|failed
                                                                     # after get_publer_job_status reads back
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
result (adv-20261107-keeper-blind-and-lost-submit, item 1, 7 Nov 2026): a submit is done only when the post's own
Publer job status has been read back (get_publer_job_status) and reads complete; 'scheduled' refuses without
--job-status complete, and a job status of failed records 'failed'. Publer's posts list lags (the Danganronpa post was
missing from it for hours while live), so the list is a secondary read, never the proof. The board 'scheduled' line
quotes the printed line: platform, job status and the read time. Publer post and job ids stay out of the repository
and the board (both are public); the server keeper matches posts by network and slot time.
published writes the story's `published` block, one line in newsroom/published.jsonl and, with --queue, the
heartbeat (ops/heartbeat.json in the dxb-queue clone; commit and push it there). Intents live in
newsroom/submissions.jsonl: commit it with the story file after each step.
Platforms: instagram, x, threads.

Release 2026-11-10 (rules into the gate):
  director PASS needs --by <director>: the job's "built_by" must be someone else (a separate director).
  intent needs --labels kind:<news|evergreen|series|breaking>,tpl:<template> (tpl:showcase for a showcase layout,
    which must match the job the director passed); kind:evergreen also needs --slot <ISO time>: never two evergreen in a
    row, and 3 hours from the last evergreen between 08:00 and 24:00 Dubai; otherwise the slot stays empty. The posts
    are read from keeper-status (the server's Publer read), else the commitments and the format ledger.
  line <commitment> --ids ig:<last6> x:<last6> th:<last6>: the board's 'scheduled:' line, refused unless every platform
    has a 'scheduled' result with its job status read back as complete. Only the last six characters of each Publer
    post id are given and printed (the board is the only place they go; never into this repository).
  published marks the evergreen bank row of an evergreen story 'used <date>' in newsroom/evergreen.md.
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
KINDS = ('news', 'evergreen', 'series', 'breaking')
SHORT = {'ig': 'instagram', 'instagram': 'instagram', 'x': 'x', 'th': 'threads', 'threads': 'threads'}
BANK = REPO / 'newsroom' / 'evergreen.md'


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
            'problems': probs, 'template': job.get('template'), 'layout': job.get('layout'),
            'evergreen': buildgate.is_evergreen(job), 'built_by': job.get('built_by')}


def _who(x):
    return ' '.join(str(x or '').lower().replace('_', '-').split())


def qc_of(out):
    """The server's qc.json beside a Reel (<base>-qc.json), from disk or git (the slim clone has no cards/), or None."""
    import re as _re
    rel = _re.sub(r'-reel-v\d+$', '', str(out)[:-4] if str(out).endswith('.mp4') else str(out)) + '-qc.json'
    p = REPO / rel
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    for rev in ('HEAD', 'origin/main'):
        r = subprocess.run(['git', '-C', str(REPO), 'show', f'{rev}:{rel}'], capture_output=True, text=True)
        if r.returncode == 0:
            try:
                return json.loads(r.stdout)
            except ValueError:
                return None
    return None


def director(sid, verdict, out, note='', job=None, by=None, looked=None):
    if verdict not in ('PASS', 'FIX'):
        raise SystemExit('presubmit: verdict is PASS or FIX')
    f, s = story(sid)
    cl = checklist(job, out) if job else None
    qc = qc_of(out)
    if verdict == 'PASS':
        # the server's verdict is final on what it measured (adv-20261112-qc-notes-become-failures)
        if qc and qc.get('verdict') == 'fail':
            raise SystemExit('presubmit refused: the server QC failed this Reel:\n  - ' + '\n  - '.join(
                f"{x.get('check')}: {x.get('detail')}" for x in qc.get('findings') or []) + '\nfix the job and render again')
        if qc and qc.get('look_frames') and not (looked or '').strip():
            raise SystemExit('presubmit refused: a card-led Reel: read its three look frames ('
                             + ', '.join(qc['look_frames']) + ') and say what they show with --looked "<one line>" '
                             '(adv-20261112-qc-notes-become-failures item 6)')
        if qc is None:
            print(f'presubmit: no qc.json beside {out} (fetch main, or a render.yml Reel): the server verdict was not read')
        if not cl:
            raise SystemExit('presubmit: director PASS needs --job <the job file that rendered it> (its reel_check)')
        if not cl['ok']:
            raise SystemExit('presubmit refused: the job does not pass the build gate:\n  - ' + '\n  - '.join(cl['problems']))
        if not _who(by):
            raise SystemExit('presubmit refused: director PASS needs --by <the director> (a separate agent or session)')
        if _who(by) == _who(cl.get('built_by')) or _who(cl.get('built_by')) in _who(by).split():
            raise SystemExit(f'presubmit refused: the director ({by}) is the builder ({cl.get("built_by")}); the PASS '
                             'comes from a separate director (release 2026-11-10)')
    s['director_check'] = {'verdict': verdict, 'out': out, 'blob': blob(out), 'at': now(), 'note': note,
                           'checklist': cl, 'by': by, 'qc': (qc or {}).get('verdict'), 'looked': looked}
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n')
    print(f'director {verdict} recorded for {out} ({s["director_check"]["blob"][:10]})')


def labels_problems(labels, cl):
    """kind and tpl labels against the job the director passed."""
    ls = {x.strip().split(':', 1)[0].lower(): x.strip().split(':', 1)[1].strip().lower()
          for x in (labels or '').split(',') if ':' in x}
    out = []
    kind, tpl = ls.get('kind'), ls.get('tpl')
    if kind not in KINDS:
        out.append(f'label kind:<{"|".join(KINDS)}> missing or unknown ({kind})')
    want = 'showcase' if (cl or {}).get('layout') == 'showcase' else (cl or {}).get('template')
    if not tpl:
        out.append(f'label tpl:<template> missing{(" (tpl:" + want + ")") if want else ""}')
    elif want and tpl != want:
        out.append(f'label tpl:{tpl} does not match the job the director passed (tpl:{want})')
    if (cl or {}).get('evergreen') and kind != 'evergreen':
        out.append('the job is evergreen (post_kind, دليل chip or bank): label kind:evergreen')
    return out, kind


def evergreen_slot_problems(slot):
    """CLAUDE.md 'Evergreen spacing and the news search' (9 Nov 2026): never two evergreen in a row; 3 hours from the
    last evergreen between 08:00 and 24:00 Dubai; the slot stays empty otherwise."""
    sys.path.insert(0, str(REPO / 'ops' / 'backoffice' / 'keeper'))
    import workorder as W
    at = W.t(slot)
    if not at:
        return ['--slot <ISO time> is needed for kind:evergreen']
    subprocess.run(['git', '-C', str(REPO), 'fetch', '-q', '--depth', '1', 'origin',
                    '+keeper-status:refs/remotes/origin/keeper-status'], check=False, capture_output=True)
    r = subprocess.run(['git', '-C', str(REPO), 'show', 'refs/remotes/origin/keeper-status:keeper/server-in.json'],
                       capture_output=True, text=True)
    posts = []
    try:
        srv = json.loads(r.stdout) if r.returncode == 0 else None
        if srv and srv.get('posts') is not None:
            posts = W.posts_from_server(srv)
    except ValueError:
        pass
    if not posts:
        rows = json.loads((REPO / 'newsroom' / 'commitments.json').read_text()).get('rows', [])
        led = json.loads((REPO / 'templates' / 'assets' / 'format-ledger.json').read_text())
        posts = W.posts_from_commitments(rows, led)
    before = [p for p in posts if p['at'] < at]
    me = {'at': at, 'labels': {'kind:evergreen'}, 'state': 'scheduled'}
    return [w for w in W.problems_for(me, before, None) if 'evergreen' in w]


def intent(commitment, platform, sid, out, labels=None, slot=None):
    if platform not in PLATFORMS:
        raise SystemExit(f'presubmit: platform is one of {", ".join(PLATFORMS)}')
    _, s = story(sid)
    d = s.get('director_check') or {}
    lp, kind = labels_problems(labels, d.get('checklist'))
    if lp:
        raise SystemExit('presubmit refused: Publer labels (release 2026-11-10):\n  - ' + '\n  - '.join(lp))
    if kind == 'evergreen':
        ep = evergreen_slot_problems(slot)
        if ep:
            raise SystemExit('presubmit refused: evergreen at this slot: ' + '; '.join(ep) +
                             '. The slot stays empty unless news fills it (CLAUDE.md, Evergreen spacing, 9 Nov 2026).')
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
                 'state': 'intent', 'at': now(), 'labels': labels})
    print(f'intent recorded: {commitment} {platform}; submit now, then presubmit.py result')


def result(commitment, platform, state, job_status=None):
    if state not in ('scheduled', 'failed', 'published'):
        raise SystemExit('presubmit: state is scheduled, failed or published')
    js = (job_status or '').lower()
    if state in ('scheduled', 'published') and js != 'complete':
        raise SystemExit(f'presubmit refused: {state} needs the job status read back: call get_publer_job_status on '
                         'the submit until it reads complete, then --job-status complete (a failed job: --job-status '
                         'failed and state failed). The posts list lags; it is not the proof.')
    if js == 'failed' and state != 'failed':
        raise SystemExit('presubmit refused: the job status reads failed; record state failed')
    prev = last_state(commitment, platform)
    if not prev:
        raise SystemExit(f'presubmit: no intent for {commitment} {platform}')
    at = now()
    append(LOG, dict(prev, state=state, at=at, job_status=js or None, job_read_at=at if js else None))
    print(f'{commitment} {platform}: {state}' + (f'; Publer job status {js} (read {at[11:16]}Z)' if js else '')
          + ('; board line: "scheduled: ' + commitment + ' ' + platform + f', job status complete {at[11:16]}Z"'
             if state == 'scheduled' else ''))


ID6 = __import__('re').compile(r'^[0-9a-zA-Z]{6}$')


def line(commitment, ids, slot=None):
    """The board's 'scheduled:' line: every platform scheduled with its job status read back, and the last six
    characters of each Publer post id (never more; never stored here)."""
    got = {}
    for x in ids or []:
        k, _, v = x.partition(':')
        p = SHORT.get(k.lower())
        if not p or not ID6.match(v or ''):
            raise SystemExit(f'presubmit refused: id "{x}": give <ig|x|th>:<the last six characters of the Publer post id>')
        got[p] = v
    rows = {p: last_state(commitment, p) for p in PLATFORMS}
    sent = [p for p, r in rows.items() if r]
    bad = [p for p in sent if not (rows[p].get('state') in ('scheduled', 'published') and rows[p].get('job_status') == 'complete')]
    if not sent or bad:
        raise SystemExit(f'presubmit refused: no job status read back as complete for {", ".join(bad or PLATFORMS)}; '
                         'run presubmit.py result ... --job-status complete first')
    missing = [p for p in sent if p not in got]
    if missing:
        raise SystemExit(f'presubmit refused: Publer post id (last six) missing for {", ".join(missing)}')
    read = max(rows[p].get('job_read_at') or '' for p in sent)
    ab = {'instagram': 'ig', 'x': 'x', 'threads': 'th'}
    print(f'scheduled: {commitment}{(" at " + slot) if slot else ""}, {len(sent)}/{len(sent)}, job status complete '
          f'(read {read[11:16]}Z), ids ' + ' '.join(f'{ab[p]}:{got[p]}' for p in sent))


def mark_bank_used(s, out, at):
    """An evergreen story's bank row in newsroom/evergreen.md becomes 'used <date>' when it publishes."""
    if not BANK.exists() or not out:
        return None
    import re
    base = re.sub(r'-reel-v\d+\.mp4$', '', pathlib.Path(out).name)
    lines = BANK.read_text().split('\n')
    for i, row in enumerate(lines):
        if row.startswith('|') and base and base in row:
            cells = row.split('|')
            if len(cells) >= 3:
                cells[-2] = f' used {at[:10]} (published {at[11:16]}Z) '
                lines[i] = '|'.join(cells)
                BANK.write_text('\n'.join(lines))
                return base
    return None


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
    cl = (s.get('director_check') or {}).get('checklist') or {}
    if cl.get('evergreen') or s.get('bank') or str(s.get('post_kind', '')).lower() == 'evergreen':
        used = mark_bank_used(s, (s.get('director_check') or {}).get('out'), at)
        print(f'evergreen bank: {"row " + used + " marked used" if used else "no matching row in newsroom/evergreen.md"} '
              '(commit newsroom/evergreen.md)')
    append(PUBLISHED, {'story': sid, 'commitment': commitment, 'title': s.get('title'), 'chip': s.get('chip'),
                       'template': s.get('template'), 'published_at': at, 'links': links})
    if queue:
        hb = pathlib.Path(queue) / 'ops' / 'heartbeat.json'
        hb.parent.mkdir(parents=True, exist_ok=True)
        hb.write_text(json.dumps({'last_published': at, 'story': sid, 'checked_at': at}, indent=1) + '\n')
        print(f'heartbeat written: {hb} (commit and push it in dxb-queue)')
    else:
        print('heartbeat not written: pass --queue <dxb-queue clone> (ops/heartbeat.json), then push it')
    try:                                         # backstory pages (adv-20261102-story-brief part 2): one log line each
        sys.path.insert(0, str(REPO / 'newsroom'))
        import context
        pages = context.append(sid)
        print('context pages: ' + (', '.join(f'newsroom/context/{p}.md' for p in pages) or 'none match'))
    except Exception as e:                       # never blocks the published record
        print(f'context pages not updated ({type(e).__name__}: {e})')
    print(f'published recorded: {sid} in newsroom/published.jsonl and the story file (commit the context pages too)')


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
        by = a[a.index('--by') + 1] if '--by' in a else None
        looked = a[a.index('--looked') + 1] if '--looked' in a else None
        director(a[1], a[2], a[3], note, jobp, by, looked)
    elif cmd == 'intent' and len(a) >= 5:
        labels = a[a.index('--labels') + 1] if '--labels' in a else None
        slot = a[a.index('--slot') + 1] if '--slot' in a else None
        intent(*a[1:5], labels=labels, slot=slot)
    elif cmd == 'line' and len(a) >= 3:
        ids = a[a.index('--ids') + 1:] if '--ids' in a else []
        ids = [x for x in ids if not x.startswith('--')]
        slot = None
        line(a[1], ids, slot)
    elif cmd == 'result' and len(a) >= 4:
        js = a[a.index('--job-status') + 1] if '--job-status' in a else None
        result(a[1], a[2], a[3], js)
    elif cmd == 'published' and len(a) >= 3:
        links = a[a.index('--links') + 1:a.index('--links') + 4] if '--links' in a else []
        q = a[a.index('--queue') + 1] if '--queue' in a else None
        published(a[1], a[2], links, q)
    elif cmd == 'show' and len(a) == 2:
        show(a[1])
    else:
        raise SystemExit(__doc__)
