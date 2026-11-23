#!/usr/bin/env python3
"""The server's publish step: the Director's verdict is a plain file, the server schedules (Mohammad, 23 Nov 2026).

Case: three Production 2 runs on 23 Nov (and runs on 17 and 18 Nov) stopped because the safety filter refused the Director
helper's `presubmit.py director` command, so the finished inKONBINI Reel (rendered 05:19Z, qc pass) was never scheduled.
Now nothing records an approval by command:

1. The Director writes its verdict as a plain file beside the job: jobs/director/<name>.json
       {"story": "<story id>", "out": "cards/YYYY-MM/<name>-reel-vN.mp4", "verdict": "pass" | "fix",
        "reason": "<code, fix only>", "fix": "<the one fix, one line>", "reasons": ["<why>", ...],
        "job_patch": {<job fields to change, optional>}, "at": "<ISO time>", "by": "<director>"}
   reason codes: picture (wrong_subject, framing, overlap, unreadable_text) move the job to the 16:9 showcase layout;
   text and content (factual_error, unclear_text, graphic) need "job_patch" with the corrected fields (headline, lines,
   shots...). `python3 templates/serverpost.py check <file>` validates a file; it records nothing.
2. `serverpost.py sweep` (server-post.yml, on every keeper tick and by hand) reads every live Reel rendered in the last
   6 hours that is not yet posted:
   - qc fail: never scheduled (the server's own checks stop it).
   - verdict pass: scheduled in the next free slot.
   - verdict fix: the job goes back to jobs/live with the fix and "rerender", render-live runs once more, and the new
     Reel is scheduled when it lands, with no second director round (a hard reason on the new Reel, factual_error or
     graphic, still holds it). A text or content fix without "job_patch" holds the Reel: a known wrong fact never posts.
   - no file 20 minutes after the render: scheduled anyway (the server checks passed), noted "no director verdict".
   Series episodes, evergreen bank pieces, the test lane and stories already submitted are left alone.
3. Scheduling: with PUBLER_POST_KEY (scopes workspaces, accounts, media, posts, job_status) the server schedules the Reel
   on Instagram, X and Threads at the same minute through Publer's API and reads the job status back. Without the key
   it writes a "ready" row: the work order shows it as an alarm with the slot, and Production 2 submits it through the
   Publer connector (no presubmit), then records it with
       python3 templates/serverpost.py scheduled <story> --slot <ISO> [--note "..."]
4. Everything goes to newsroom/serverpost.jsonl and, for the keeper's cadence, newsroom/submissions.jsonl (slot and
   state per platform). The work order lists the rows of the last 6 hours (no director verdict, ready, held), and the
   inbox mirror carries it to the board. No Publer ids, keys or response bodies are written or printed.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'ops', 'backoffice', 'keeper'))

UTC = dt.timezone.utc
LEDGER = os.path.join(REPO, 'newsroom', 'serverpost.jsonl')
SUBMISSIONS = os.path.join(REPO, 'newsroom', 'submissions.jsonl')
PUBLISHED = os.path.join(REPO, 'newsroom', 'published.jsonl')
TIMES = os.path.join(REPO, 'templates', 'assets', 'render-times.json')
STORIES = os.path.join(REPO, 'newsroom', 'stories')
SINCE = '2026-11-23T08:30:00Z'     # Reels rendered before the release are Production 2's (no backlog sweep)
WINDOW_H = 6
WAIT_MIN = 20
LEAD_MIN = 15                      # a slot is at least 15 minutes out (rolling queue)
PICTURE = ('wrong_subject', 'framing', 'overlap', 'unreadable_text')
CONTENT = ('factual_error', 'unclear_text', 'graphic')
HARD = ('factual_error', 'graphic')
API = 'https://app.publer.com/api/v1'
WORKSPACE = os.environ.get('PUBLER_WORKSPACE', 'The Digi-Lounge')
NETWORK = {'instagram': 'instagram', 'x': 'twitter', 'threads': 'threads'}


def now_utc():
    return dt.datetime.now(UTC)


def t(s):
    try:
        x = dt.datetime.fromisoformat(str(s).strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    return x if x.tzinfo else x.replace(tzinfo=UTC)


def iso(x):
    return x.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def jsonl(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def append(path, row):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')


def load(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------------------------------------- the director's file
def director_path(base):
    return os.path.join(REPO, 'jobs', 'director', base + '.json')


def check(d):
    """Problems with a director file (a list; empty when it is valid)."""
    p = []
    if not isinstance(d, dict):
        return ['not a JSON object']
    v = str(d.get('verdict', '')).lower()
    if v not in ('pass', 'fix'):
        p.append('verdict is "pass" or "fix"')
    if not str(d.get('out', '')).endswith('.mp4'):
        p.append('out: the Reel judged, cards/YYYY-MM/<name>-reel-vN.mp4')
    if not t(d.get('at')):
        p.append('at: an ISO time')
    if v == 'fix':
        r = d.get('reason')
        if r not in PICTURE + CONTENT:
            p.append('reason: one of ' + ', '.join(PICTURE + CONTENT))
        if not str(d.get('fix', '')).strip():
            p.append('fix: the one fix, in one line')
        if r in CONTENT and not isinstance(d.get('job_patch'), dict):
            p.append(f'job_patch: a {r} fix carries the corrected job fields (without it the Reel is held, never posted)')
    if d.get('job_patch') is not None and not isinstance(d.get('job_patch'), dict):
        p.append('job_patch is an object of job fields')
    return p


# ---------------------------------------------------------------------------------------------- what is waiting
def version(out):
    m = re.search(r'-reel-v(\d+)\.mp4$', str(out or ''))
    return int(m.group(1)) if m else 0


def base_of(name):
    return re.sub(r'-reel-v\d+\.mp4$', '', os.path.basename(str(name or '')))


def git_show(path):
    r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + path], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def qc_of(out):
    raw = git_show(re.sub(r'\.mp4$', '-qc.json', out))
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def candidates(now, times=None):
    """The newest render of each live Reel finished in the last WINDOW_H hours (and after SINCE)."""
    times = times if times is not None else (load(TIMES, []) or [])
    since = max(t(SINCE), now - dt.timedelta(hours=WINDOW_H))
    latest = {}
    for e in times:
        at = t(e.get('finished_at') or e.get('at'))
        name = e.get('name') or ''
        if not at or at < since or not name.endswith('.mp4') or not re.search(r'-reel-v\d+\.mp4$', name):
            continue
        b = base_of(name)
        if b not in latest or version(name) >= version(latest[b]['name']):
            latest[b] = dict(e, _at=at)
    return latest


def submitted(story, ledger, subs):
    """True when the story already has a submit (Production 2's presubmit or the connector) or a scheduled row here."""
    for r in subs:
        if r.get('story') == story and r.get('state') in ('intent', 'scheduled', 'published'):
            return True
    return any(r.get('story') == story and r.get('state') in ('scheduled', 'ready') for r in ledger)


def recent_game(story, subs, now, hours=48):
    """A story on the same game scheduled or posted in the last hours (its id), else None: with no director verdict the
    server holds such a Reel (Production 2 drops duplicates on the board, and the story file may still say building)."""
    try:
        import gamekey as GK
        key = GK.key(story.get('game') or '')
    except Exception:                                   # noqa: BLE001
        key = str(story.get('game') or '').strip().lower()
    if not key:
        return None
    for r in subs:
        if r.get('story') in (None, story.get('id')) or r.get('state') not in ('scheduled', 'published'):
            continue
        at = t(r.get('slot') or r.get('at'))
        if not at or now - at > dt.timedelta(hours=hours) or at - now > dt.timedelta(hours=hours):
            continue
        other = load(os.path.join(STORIES, f"{r['story']}.json"), {}) or {}
        try:
            ok = GK.key(other.get('game') or '') == key
        except Exception:                               # noqa: BLE001
            ok = str(other.get('game') or '').strip().lower() == key
        if ok:
            return r['story']
    return None


# ---------------------------------------------------------------------------------------------- slot
def next_slot(now, extra=()):
    import workorder as W
    rows = load(os.path.join(REPO, 'newsroom', 'commitments.json'), {}) or {}
    rows = rows.get('rows', []) if isinstance(rows, dict) else rows
    led = load(os.path.join(REPO, 'templates', 'assets', 'format-ledger.json'), []) or []
    posts = W.merge_posts(W.posts_from_commitments(rows, led), W.posts_from_logs(SUBMISSIONS, PUBLISHED),
                          [{'at': x, 'state': 'scheduled', 'labels': set(), 'networks': {}} for x in extra])
    start = now + dt.timedelta(minutes=LEAD_MIN)
    x = start.replace(second=0, microsecond=0)
    x += dt.timedelta(minutes=(15 - x.minute % 15) % 15)
    for _ in range(4 * 48):
        gap = dt.timedelta(minutes=W.SPACING[W.band(x)])
        if all(abs((p['at'] - x).total_seconds()) >= gap.total_seconds() for p in posts):
            return x
        x += dt.timedelta(minutes=15)
    return x


# ---------------------------------------------------------------------------------------------- Publer (posting key)
def _curl(args, key, ws=None, data=None, timeout=60):
    with tempfile.NamedTemporaryFile('w', suffix='.cfg', delete=False) as cfg:
        cfg.write(f'header = "Authorization: Bearer-API {key}"\n')
        if ws:
            cfg.write(f'header = "Publer-Workspace-Id: {ws}"\n')
        cfg.write('header = "Content-Type: application/json"\n')
    body = None
    try:
        cmd = ['curl', '-sS', '--max-time', str(timeout), '-K', cfg.name, '-w', '\n%{http_code}']
        if data is not None:
            body = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
            json.dump(data, body, ensure_ascii=False)
            body.close()
            cmd += ['-X', 'POST', '--data-binary', '@' + body.name]
        r = subprocess.run(cmd + args, capture_output=True, text=True)
    finally:
        os.unlink(cfg.name)
        if body:
            os.unlink(body.name)
    out, _, code = r.stdout.rpartition('\n')
    try:
        js = json.loads(out) if out.strip() else None
    except ValueError:
        js = None
    return (int(code) if code.strip().isdigit() else 0), js


def publer_schedule(key, out, texts, labels, slot):
    """Schedules the Reel on the three networks; (ok, note). Never prints an id or a body."""
    code, ws = _curl([f'{API}/workspaces'], key, timeout=30)
    if code != 200 or not isinstance(ws, list) or not ws:
        return False, f'workspace lookup HTTP {code}'
    wid = next((w.get('id') for w in ws if (w.get('name') or '').strip().lower() == WORKSPACE.lower()), None) or \
        (ws[0].get('id') if len(ws) == 1 else None)
    if not wid:
        return False, 'workspace not found'
    code, accs = _curl([f'{API}/accounts'], key, wid, timeout=30)
    if code != 200 or not isinstance(accs, list):
        return False, f'accounts HTTP {code}'
    acc = {}
    for a in accs:
        prov = str(a.get('provider') or a.get('type') or '').lower()
        for p, n in NETWORK.items():
            if prov.startswith(n) and p not in acc:
                acc[p] = a.get('id')
    fname = os.path.basename(out)
    code, med = _curl([f'{API}/media?types[]=video&search=' + re.sub(r'[^A-Za-z0-9._-]', '', fname)], key, wid, timeout=30)
    items = (med or {}).get('media') if isinstance(med, dict) else med
    mid = next((m.get('id') for m in items or [] if m.get('name') == fname), None)
    if not mid:
        return False, f'the Reel is not in the Publer library by name (media HTTP {code})'
    when = iso(slot)
    posts = []
    for p, n in NETWORK.items():
        if not acc.get(p) or not texts.get(p):
            continue
        net = {'type': 'video', 'text': texts[p], 'media': [{'id': mid, 'type': 'video'}]}
        if p == 'instagram':
            net['details'] = {'type': 'reel'}
        posts.append({'networks': {n: net}, 'accounts': [{'id': acc[p], 'scheduled_at': when}],
                      'labels': [{'name': l} for l in labels]})
    if len(posts) < 3:
        return False, 'an account or a text is missing: ' + ', '.join(p for p in NETWORK if not (acc.get(p) and texts.get(p)))
    code, js = _curl([f'{API}/posts/schedule'], key, wid, data={'bulk': {'state': 'scheduled', 'posts': posts}})
    job = (js or {}).get('job_id') if isinstance(js, dict) else None
    if code not in (200, 201) or not job:
        return False, f'schedule HTTP {code}'
    import time
    for _ in range(20):
        time.sleep(3)
        code, st = _curl([f'{API}/job_status/{job}'], key, wid, timeout=30)
        s = str((st or {}).get('status', '')).lower() if isinstance(st, dict) else ''
        if s in ('complete', 'completed'):
            fails = (st.get('payload') or {}).get('failures') if isinstance(st.get('payload'), dict) else None
            return (not fails), ('job status complete' + (f', {len(fails)} failed' if fails else ''))
        if s == 'failed':
            return False, 'job status failed'
    return False, 'job status not complete after 60 s (look the posts up in Publer before any retry)'


# ---------------------------------------------------------------------------------------------- the sweep
def labels_for(job, story, qc):
    kind = 'evergreen' if (job.get('post_kind') == 'evergreen') else ('breaking' if job.get('profile') == 'breaking' else 'news')
    tpl = 'showcase' if job.get('layout') == 'showcase' else (job.get('template') or 'trailer')
    snd = str((qc or {}).get('sound') or '').split(':')[0] or 'trailer'
    g = story.get('genre')
    g = g[0] if isinstance(g, list) and g else g
    out = [f'kind:{kind}', f'tpl:{tpl}', f'skin:{job.get("skin") or "house"}', f'sound:{snd}']
    if g:
        out.append(f'genre:{g}')
    return out


def record_schedule(story, slot, labels, state, note, by):
    at = iso(now_utc())
    for p in ('instagram', 'x', 'threads'):
        append(SUBMISSIONS, {'commitment': story, 'platform': p, 'story': story, 'state': state, 'at': at,
                             'labels': ','.join(labels), 'slot': iso(slot), 'job_status': 'complete' if state == 'scheduled' else None,
                             'by': by, 'note': note})


def rerender(base, job, d, current_out):
    """The job back to jobs/live with the director's fix, the next version, and the rerender note."""
    import presubmit as PS
    j = dict(job)
    j.update(d.get('job_patch') or {})
    v = version(current_out) + 1
    j['out'] = re.sub(r'-reel-v\d+\.mp4$', f'-reel-v{v}.mp4', current_out)
    j['rerender'] = {'reason': d.get('reason'), 'note': (d.get('fix') or '')[:200]}
    path = os.path.join(REPO, 'jobs', 'live', base + '.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
        f.write('\n')
    moved = None
    if d.get('reason') in PICTURE:
        moved = PS.to_showcase(path, d.get('reason'), d.get('fix') or '')
    return path, j['out'], moved


def sweep(now=None, dry=False, key=None):
    now = now or now_utc()
    ledger = jsonl(LEDGER)
    subs = jsonl(SUBMISSIONS)
    taken = []
    actions = []
    for base, e in sorted(candidates(now).items(), key=lambda kv: kv[1]['_at']):
        job = load(os.path.join(REPO, 'jobs', 'done', base + '.json'))
        if not isinstance(job, dict):
            continue
        out = job.get('out') or ''
        if not out.startswith('cards/20') or os.path.basename(out) != e['name']:
            continue                                            # the test lane, or the job moved on since
        sid = job.get('story')
        story = load(os.path.join(STORIES, f'{sid}.json'), None) if sid else None
        if not isinstance(story, dict):
            continue
        if isinstance(job.get('intro'), dict) and job['intro'].get('series'):
            continue                                            # series episodes: the studio schedules them
        if job.get('post_kind') == 'evergreen' or story.get('held_by_mohammad') or \
                re.search(r'dropped|held|pulled|parked', str(story.get('status', '')), re.I):
            continue
        mine = [r for r in ledger if r.get('base') == base]
        if submitted(sid, ledger, subs) or any(r.get('out') == out and r.get('state') == 'held' for r in mine):
            continue
        qc = qc_of(out)
        if (qc or {}).get('verdict') == 'fail':
            continue
        age = (now - e['_at']).total_seconds() / 60
        d = load(director_path(base))
        probs = check(d) if d is not None else None
        fixed_before = [r for r in mine if r.get('state') == 'fix_render']
        verdict, note = None, ''
        if isinstance(d, dict) and str(d.get('verdict', '')).lower() == 'fix' and d.get('reason') in CONTENT \
                and d.get('out') == out and not isinstance(d.get('job_patch'), dict) and not fixed_before:
            actions.append({'at': iso(now), 'story': sid, 'base': base, 'out': out, 'director': 'fix', 'state': 'held',
                            'qc': (qc or {}).get('verdict'), 'note': f'{d.get("reason")} fix without job_patch: held, never '
                            'posted with it; the director adds job_patch, or Mohammad decides'})
            continue
        if d is not None and probs:
            verdict, note = 'none', 'director file unreadable (' + '; '.join(probs) + '); treated as no verdict'
            if age < WAIT_MIN:
                continue
        elif d is not None and d.get('out') == out:
            verdict = str(d['verdict']).lower()
        elif d is not None and fixed_before and version(out) > version(d.get('out')):
            verdict, note = 'pass', f'fix render of {d.get("reason")} landed ({os.path.basename(out)}); scheduled as fixed'
        elif age >= WAIT_MIN:
            verdict, note = 'none', f'no director verdict {int(age)} min after the render; the server checks passed'
        else:
            continue                                            # the director still has time
        row = {'at': iso(now), 'story': sid, 'base': base, 'out': out, 'director': verdict, 'qc': (qc or {}).get('verdict')}
        if verdict == 'fix':
            if fixed_before:                                    # one fix render only, then it posts
                if d.get('reason') in HARD:
                    actions.append(dict(row, state='held', note=f'second {d.get("reason")} verdict on the fixed Reel: '
                                        'held, never posted with a known wrong fact or graphic content; Mohammad decides'))
                    continue
                verdict, note = 'pass', 'fix already rendered once; scheduled'
            elif d.get('reason') in CONTENT and not isinstance(d.get('job_patch'), dict):
                actions.append(dict(row, state='held', note=f'{d.get("reason")} fix without job_patch: held, never '
                                    'posted with it; the director adds job_patch, or Mohammad decides'))
                continue
            else:
                if dry:
                    actions.append(dict(row, state='fix_render', note='(dry) ' + d.get('fix', '')))
                    continue
                path, new_out, moved = rerender(base, job, d, out)
                actions.append(dict(row, state='fix_render', next_out=new_out, job=os.path.relpath(path, REPO),
                                    note=f'{d.get("reason")}: {d.get("fix")}' + (f'; showcase ({moved})' if moved else '')))
                continue
        if verdict == 'none':
            dup = recent_game(dict(story, id=sid), subs, now)
            if dup:
                actions.append(dict(row, state='held', note=f'no director verdict and the same game went out in the '
                                    f'last 48 hours ({dup}): a duplicate or a follow-up? a director pass schedules it'))
                continue
        texts = {p: (story.get('texts') or {}).get(p) for p in ('instagram', 'x', 'threads')}
        if not all(texts.values()):
            actions.append(dict(row, state='held', note='story texts missing for ' +
                                ', '.join(p for p, v in texts.items() if not v) + '; write them in the story file'))
            continue
        slot = next_slot(now, taken)
        taken.append(slot)
        labels = labels_for(job, story, qc)
        row.update(slot=iso(slot), labels=labels)
        if verdict == 'none':
            row['note'] = note or 'no director verdict'
        elif note:
            row['note'] = note
        if dry:
            actions.append(dict(row, state='(dry) schedule'))
            continue
        if key:
            ok, why = publer_schedule(key, out, texts, labels, slot)
            if ok:
                record_schedule(sid, slot, labels, 'scheduled', row.get('note', ''), 'server')
                actions.append(dict(row, state='scheduled', publer=why))
                continue
            row['note'] = (row.get('note', '') + f'; Publer API: {why}').strip('; ')
        actions.append(dict(row, state='ready', note=(row.get('note', '') + '; schedule through the Publer connector '
                                                       'at the slot, then serverpost.py scheduled').strip('; ')))
    if not dry:
        for a in actions:
            append(LEDGER, a)
    return actions


def recent_notes(now=None, path=None, hours=WINDOW_H):
    """Work order lines: rows of the last hours worth showing (no director verdict, ready, held, fix render)."""
    now = now or now_utc()
    rows = jsonl(path or LEDGER)
    done = {r.get('story') for r in rows if r.get('state') == 'scheduled'}
    out = []
    for r in rows:
        at = t(r.get('at'))
        if not at or now - at > dt.timedelta(hours=hours):
            continue
        s = r.get('state')
        if s == 'ready' and r.get('story') in done:
            continue
        if s == 'scheduled' and r.get('director') != 'none':
            continue
        out.append(r)
    return out


def main(argv):
    if argv and argv[0] == 'check' and len(argv) > 1:
        d = load(argv[1])
        p = check(d) if d is not None else ['not readable JSON']
        print('director file: ' + ('valid' if not p else 'problems:\n  - ' + '\n  - '.join(p)))
        return 0 if not p else 1
    if argv and argv[0] == 'sweep':
        dry = '--dry' in argv
        now = t(argv[argv.index('--now') + 1]) if '--now' in argv else None
        acts = sweep(now, dry, os.environ.get('PUBLER_POST_KEY') or None)
        for a in acts:
            print('serverpost: %s %s%s%s' % (a['state'], a['base'], (' at ' + a['slot']) if a.get('slot') else '',
                                             (' (' + a['note'] + ')') if a.get('note') else ''))
        if not acts:
            print('serverpost: nothing to do')
        return 0
    if argv and argv[0] == 'scheduled' and len(argv) > 1 and '--slot' in argv:
        sid = argv[1]
        slot = t(argv[argv.index('--slot') + 1])
        note = argv[argv.index('--note') + 1] if '--note' in argv else 'scheduled through the Publer connector'
        story = load(os.path.join(STORIES, f'{sid}.json'), {}) or {}
        if not slot or not story:
            print('serverpost: give a story id that exists and --slot <ISO>')
            return 1
        prev = [r for r in jsonl(LEDGER) if r.get('story') == sid]
        base = (prev[-1].get('base') if prev else None) or re.sub(r'^\d{4}-\d{2}-\d{2}-', '', sid)
        job = load(os.path.join(REPO, 'jobs', 'done', base + '.json'), {}) or {}
        labels = labels_for(job, story, qc_of(job.get('out', '')) if job.get('out') else None)
        record_schedule(sid, slot, labels, 'scheduled', note, 'connector')
        append(LEDGER, {'at': iso(now_utc()), 'story': sid, 'base': base, 'out': job.get('out'), 'state': 'scheduled',
                        'slot': iso(slot), 'labels': labels, 'note': note, 'director': (prev[-1].get('director') if prev else None)})
        print(f'serverpost: {sid} recorded as scheduled at {iso(slot)}')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
