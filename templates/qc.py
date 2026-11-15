"""Server quality control, one verdict per Reel (adv-20261110-one-render-per-reel, item H, Mohammad 10 Nov 2026, 17:27
Dubai).

After every server render the workflow writes <name>-qc.json beside the Reel: "pass" or "fail" and every finding in one
list, so the session opens a Reel only when qc says fail and then gets the whole list. Mechanical text faults (a glued
prefix, a flipping % or +) are fixed by the server itself before the render (textrules.fix) and listed here as
`autofixed`; a Latin-first line, length or reading time is never changed by the server.

    python3 templates/qc.py write <job.json> <out.mp4> <qc.json> [--autofix changes.json] [--log render.log]
    python3 templates/qc.py fail <job.json> <qc.json> --log render.log      the verdict of a render that stopped
    python3 templates/qc.py rerender <job.json>     exit 1 when the story may not render again (item E, below)

Director limit (adv-20261115-one-render-server-checks item E, Mohammad 15 Nov 2026): with the verdict at pass the
director looks once at the look frames (every Reel now) and may send the Reel back once, for a hard reason only
(presubmit.py director FIX --reason wrong_subject | graphic | unreadable_text | factual_error). The send-back is one line
under `director_sendbacks` here and in the story file, carried over to the next render's qc.json. No third render:
`qc.py rerender` refuses a render of a story the director passed, or one already rendered again after its send-back,
unless the job names "rerender": {"reason", "note"}.

The findings come from the checks the render already ran (text rules and drawn text, safe zone, first frame and grid
corner, fill, decode and smear, sound against picture, length, pace, credits, burnt-in text, lifeless score): a render
that reaches the commit passed every hard check; a render that stopped is fail with the error lines of its log. The
pass then goes to the director helper once, and on to scheduling.

What the server measures fails the Reel (adv-20261112-qc-notes-become-failures, Mohammad 12 Nov 2026, after the
Roblox Saudi games Reel went out as pass with lifeless over, a closing card and lines over the card's text):
  lifeless   the lifeless score `over` fails a news Reel (storybook pages and the tribute variant exempt)
  close      the last 2 s on our own card fails (end on a picture)
  length     under 12 s of story before the end card fails (formats.LENGTH_EXEMPT and breaking exempt)
  collision  a story line over a card's text (render_job prints `collision:`; the text check refuses it first)
Card-led templates (LOOK) get three frames beside qc.json, 360 px wide (first, middle, last story frame,
`<base>-look-1.jpg` to `-3.jpg`, listed as `look_frames`): the builder reads them before scheduling (presubmit
director --looked). presubmit refuses a director PASS on a Reel whose qc verdict is fail.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

NOTE = re.compile(r'^(?:source quality|first frame|cover picture|speech check|design pass|render_job: (?:audio split|lifeless|design pass)'
                  r'|smear check|weak-source path|text check \(estimate\)|pace|length|close|collision|autofocus: profile)[: ].*', re.I)
ERR = re.compile(r'(?:Error|ValueError|SystemExit|refused|FAILED|text check: \d+ problem|  - )', re.I)


def _log_lines(path):
    try:
        return [ln.rstrip('\n') for ln in open(path, encoding='utf-8', errors='replace')]
    except OSError:
        return []


def _times(name):
    try:
        d = json.load(open(os.path.join(HERE, 'assets', 'render-times.json'), encoding='utf-8'))
        rows = [e for e in d if isinstance(e, dict) and str(e.get('name', '')).startswith(name)]
        return rows[-1] if rows else {}
    except (OSError, ValueError):
        return {}


LOOK = ('numbers', 'list', 'explainer', 'quote', 'edition')   # card-led: three frames for one automatic look
MIN_LENGTH = 12.0
LIFELESS_EXEMPT = ('storybeat',)                               # storybook pages (and "tribute": true)


def _exempt_length(job):
    import formats
    return (job.get('template') in formats.LENGTH_EXEMPT or job.get('kind') == 'breaking'
            or job.get('profile') == 'breaking')


def findings_from_notes(job, notes):
    """The notes the server measured that fail the Reel (adv-20261112-qc-notes-become-failures)."""
    out = []
    for n in notes:
        if n.startswith('render_job: lifeless: {'):
            try:
                r = json.loads(n[len('render_job: lifeless: '):])
            except ValueError:
                continue
            if r.get('over') and job.get('template') not in LIFELESS_EXEMPT and not job.get('tribute'):
                out.append({'check': 'lifeless', 'detail': f"lifeless score {r.get('score')} (still_share {r.get('still_share')}, "
                            f"longest still {r.get('longest_still')} s): too much of the Reel holds still; footage behind "
                            "the cards, the count-up and row reveal, more cuts"})
        elif n.startswith('close:') and not _exempt_length(job) and job.get('template') != 'storybeat':
            out.append({'check': 'close', 'detail': n})
        elif n.startswith('collision:'):
            out.append({'check': 'collision', 'detail': n})
        else:
            m = re.match(r'length ([\d.]+) s before the end card', n)
            if m and float(m.group(1)) < MIN_LENGTH and not _exempt_length(job):
                out.append({'check': 'length', 'detail': n + f'; under {MIN_LENGTH:.0f} s fails: add a beat of footage'})
    return out


def _duration(path):
    import subprocess
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def look_frames(job, out, tail=2.0):
    """Three frames of the Reel, 360 px wide, beside qc.json: the first frame, the middle and the last story frame
    before the end card. Returns their paths ([] when ffmpeg cannot read the file). Card-led templates only until
    15 Nov; every Reel since (item E)."""
    import subprocess
    if not os.path.exists(out):   # every Reel since 15 Nov (adv-20261115-one-render-server-checks item E): the director
        return []                  # looks once at these three frames when the verdict is pass
    secs = _duration(out)
    if not secs:
        return []
    body = max(0.1, secs - tail)
    base = re.sub(r'-reel-v\d+$', '', os.path.splitext(out)[0])
    paths = []
    for i, t in enumerate((0.0, body / 2, max(0.0, body - 0.15)), 1):
        p = f'{base}-look-{i}.jpg'
        r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', out, '-frames:v', '1',
                            '-vf', 'scale=360:-2', '-q:v', '3', p], capture_output=True)
        if r.returncode == 0 and os.path.exists(p):
            paths.append(p)
    return paths


def sound_of(job, log=None):
    """adv-20261112-sound-by-code item 4: "trailer", "trailer-voiced" or "bed:<flavour>" (with the job's bed_reason),
    from the render log's "render_job: sound:" line, else from the job."""
    for ln in reversed(_log_lines(log) if log else []):
        if ln.startswith('render_job: sound: '):
            return ln[len('render_job: sound: '):].strip()
    tr = job.get('track')
    if tr and tr != 'bed':
        return 'trailer-voiced' if (job.get('speech_ok') or job.get('speech_keep')) else 'trailer'
    why = str(job.get('bed_reason') or '').strip()
    return f"bed:{job.get('sound') or 'neon'}" + (f' ({why})' if why else '')


def person_shown(job):
    """adv-20261111-person-stories-gate item 4: true when the job's first person window opens on frame 0, false when a
    person is its subject (subject_person, or the kind quote, people or cast) and none opens there, else "n/a"."""
    p = job.get('person') or []
    try:
        opens = bool(p) and float(p[0][3]) <= 0.05
    except (IndexError, TypeError, ValueError):
        opens = False
    if opens:
        return True
    if job.get('subject_person') or job.get('kind_news') in ('quote', 'people', 'cast'):
        return False
    return 'n/a'


def write(job, out, qc_path, autofix=None, log=None):
    import textrules as TR
    notes = [ln.strip() for ln in _log_lines(log) if NOTE.match(ln.strip())] if log else []
    soft = [f for f in TR.check(job) if f not in TR.hard([f])]
    t = _times(os.path.basename(out))
    found = findings_from_notes(job, notes)
    if person_shown(job) is False:                 # the people rule: the gate refuses it; a Reel that slips through fails
        found.append({'check': 'person', 'detail': 'a person is the subject and no photo box opens on frame 0'})
    d = {'name': job.get('name'), 'out': out, 'verdict': 'fail' if found else 'pass',
         'at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'findings': found, 'notes': notes[:60] + [f"estimate: {f['where']}: {f['fix']}" for f in soft],
         'autofixed': autofix or [], 'job_sha': os.environ.get('JOB_SHA'),
         'dispatches': int(os.environ['DISPATCHES']) if os.environ.get('DISPATCHES', '').isdigit() else None,
         'source_summary': t.get('source_summary'), 'quality': t.get('quality'), 'final_enc': t.get('final_enc'),
         'look_frames': look_frames(job, out), 'person_shown': person_shown(job), 'sound': sound_of(job, log)}
    prev = previous(qc_path)
    if prev.get('director_sendbacks'):               # item E: the send-backs stay with the Reel across renders
        d['director_sendbacks'] = prev['director_sendbacks']
    json.dump(d, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


def previous(qc_path):
    """The qc.json this render replaces, from disk or from main (the runner's checkout is sparse), or {}."""
    import subprocess
    try:
        return json.load(open(qc_path, encoding='utf-8'))
    except (OSError, ValueError):
        pass
    rel = os.path.relpath(os.path.abspath(qc_path), os.path.dirname(HERE))
    for rev in ('HEAD', 'origin/main'):
        r = subprocess.run(['git', '-C', os.path.dirname(HERE), 'show', f'{rev}:{rel}'], capture_output=True, text=True)
        if r.returncode == 0:
            try:
                return json.loads(r.stdout)
            except ValueError:
                return {}
    return {}


RERENDER_REASONS = ('wrong_subject', 'graphic', 'unreadable_text', 'factual_error', 'source_changed')


def rerender_problem(job, stories_dir=None):
    """Item E, no third render: once the director has passed a story (its story file's director_check is PASS on a
    Reel the server qc passed), or has used its one send-back and the Reel was rendered again, a new render of the story
    is refused unless the job names {"rerender": {"reason": one of RERENDER_REASONS, "note": ...}}. None when it may
    render."""
    sid = job.get('story')
    if not sid or job.get('kind') in ('famitsu', 'breaking'):
        return None
    rr = job.get('rerender') or {}
    if isinstance(rr, dict) and rr.get('reason') in RERENDER_REASONS and len(str(rr.get('note') or '')) >= 10:
        return None
    path = os.path.join(stories_dir or os.path.join(os.path.dirname(HERE), 'newsroom', 'stories'), f'{sid}.json')
    try:
        s = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    dc = s.get('director_check') or {}
    if dc.get('verdict') == 'PASS' and dc.get('qc') != 'fail':
        return (f'{sid}: the director passed this story ({dc.get("at")}, {dc.get("out")}); a director PASS is final, so '
                'no new render. If something must change, name it in the job: "rerender": {"reason": one of '
                + ', '.join(RERENDER_REASONS) + ', "note": "<what changed>"}')
    sb = [x for x in s.get('director_sendbacks') or [] if x.get('qc') == 'pass']
    if sb:
        last = sb[-1]
        try:
            t0 = dt.datetime.fromisoformat(str(last.get('at')).replace('Z', '+00:00'))
        except ValueError:
            return None
        rendered_after = []
        try:
            times = json.load(open(os.path.join(HERE, 'assets', 'render-times.json'), encoding='utf-8'))
        except (OSError, ValueError):
            times = []
        base = re.sub(r'-reel-v\d+\.mp4$', '', os.path.basename(str(last.get('out') or '')))
        for e in times if isinstance(times, list) else []:
            if not isinstance(e, dict) or not str(e.get('name', '')).startswith((job.get('name') or '~', base or '~')):
                continue
            try:
                t = dt.datetime.fromisoformat(str(e.get('finished_at') or e.get('at')).replace('Z', '+00:00'))
            except ValueError:
                continue
            if (t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)) > t0:
                rendered_after.append(e.get('name'))
        if rendered_after:
            return (f'{sid}: the director sent this story back once ({last.get("reason")}) and it was rendered again '
                    f'({rendered_after[-1]}); no third render (adv-20261115-one-render-server-checks item E). The '
                    'director passes it with a note; a real change names "rerender" with its reason')
    return None


def fail(job, qc_path, log=None):
    lines = _log_lines(log) if log else []
    found = []
    for ln in lines:
        s = ln.strip()
        if s.startswith('TEXTCHECK_JSON: '):
            try:
                found += [dict(p, check='text') for p in json.loads(s[len('TEXTCHECK_JSON: '):]).get('problems', [])]
            except ValueError:
                pass
        elif ERR.search(s) and len(found) < 80 and not s.startswith('TEXTCHECK_JSON'):
            found.append({'check': 'render', 'detail': s[:400]})
    d = {'name': job.get('name'), 'verdict': 'fail', 'at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'findings': found, 'job_sha': os.environ.get('JOB_SHA')}
    json.dump(d, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    if a[:1] == ['write'] and len(a) >= 4:
        fx = json.load(open(opt('--autofix'), encoding='utf-8')) if opt('--autofix') and os.path.exists(opt('--autofix')) else []
        r = write(json.load(open(a[1], encoding='utf-8')), a[2], a[3], fx, opt('--log'))
        print(f"qc: {r['name']}: {r['verdict']}, {len(r['findings'])} findings, {len(r['autofixed'])} autofixed, "
              f"{len(r['notes'])} notes, {len(r['look_frames'])} look frames")
        if r['verdict'] == 'fail':
            print('QC_JSON: ' + json.dumps(r, ensure_ascii=False))
    elif a[:1] == ['sound-entry'] and len(a) >= 4:   # the render's commit step: sound and footage on its render-times entry
        job = json.load(open(a[1], encoding='utf-8'))
        import buildgate
        times = json.load(open(a[3], encoding='utf-8'))
        if times and isinstance(times[-1], dict):
            times[-1]['sound'] = sound_of(job, a[2])
            times[-1]['footage'] = buildgate.footage_job(job)
            json.dump(times, open(a[3], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print(f"qc: sound {times[-1]['sound']}, footage {times[-1]['footage']}")
    elif a[:1] == ['rerender'] and len(a) >= 2:      # render-live, before the render: no third render (item E)
        r = rerender_problem(json.load(open(a[1], encoding='utf-8')))
        if r:
            print(f'::error::{r}')
            sys.exit(1)
        print('qc: render allowed (no director PASS or spent send-back on this story)')
    elif a[:1] == ['fail'] and len(a) >= 3:
        r = fail(json.load(open(a[1], encoding='utf-8')), a[2], opt('--log'))
        print(f"qc: {r['name']}: fail, {len(r['findings'])} findings")
        print('QC_JSON: ' + json.dumps(r, ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
