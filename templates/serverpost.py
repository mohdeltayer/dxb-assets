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
sys.path.insert(0, os.path.join(REPO, 'ops'))
try:
    import cadence as CAD                               # ops/cadence.json (Mohammad, 23 Nov 2026)
except ImportError:                                      # a checkout without ops/: the same numbers, said once
    import types as _t
    CAD = _t.SimpleNamespace(SPACING={'day': 30, 'night': 60}, MAX_GAP={'day': 60, 'night': 120}, BUFFER=6, AHEAD_MIN=2,
                             LEAD_MIN=15, band=lambda x: 'night' if (x if x.tzinfo else x.replace(tzinfo=__import__('datetime').timezone.utc)).astimezone(__import__('datetime').timezone(__import__('datetime').timedelta(hours=4))).hour < 8 else 'day')
LEAD_MIN = CAD.LEAD_MIN                      # a slot is at least 15 minutes out (rolling queue)
QUICK = os.path.join(REPO, 'newsroom', 'quickpost.jsonl')
QUICK_SPACING = getattr(CAD, 'QUICK_SPACING', 10)       # split by platform (Mohammad, 24 Nov 2026)
REEL_AFTER_QUICK = dt.timedelta(hours=getattr(CAD, 'REEL_AFTER_QUICK_H', 2))
REEL_XT_MAX = dt.timedelta(hours=getattr(CAD, 'REEL_XT_MAX_H', 24))
QUICK_LEAD_MIN = 3                                       # a quick post is scheduled a few minutes out (T0: within 10 of detection)
QUICK_NET = {'x': 'twitter', 'threads': 'threads'}
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
    raw = git_show(re.sub(r'-reel-v\d+\.mp4$', '-qc.json', out)) or git_show(re.sub(r'\.mp4$', '-qc.json', out))
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


def prior(story, ledger, subs, now):
    """What the logs know of this story in Publer: None; ('posted', at); ('scheduled', earliest slot) when every submit
    of it is still in the future (rule 3: a newer version replaces it); ('unknown', None) for an intent with no slot."""
    slots, pub, bare = [], False, False
    for r in subs:
        if r.get('story') != story or r.get('state') not in ('intent', 'scheduled', 'published'):
            continue
        pub = pub or r.get('state') == 'published'
        sl = t(r.get('slot'))
        if sl:
            slots.append(sl)
        else:
            bare = True
    for r in ledger:
        if r.get('story') == story and r.get('state') in ('scheduled', 'ready') and t(r.get('slot')):
            slots.append(t(r['slot']))
    if not slots and not pub and not bare:
        return None
    if pub or any(x <= now for x in slots):
        return 'posted', min(slots) if slots else None
    if bare and not slots:
        return 'unknown', None
    return 'scheduled', min(slots)


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
def next_slot(now, extra=(), publer=None):
    """The earliest quarter hour LEAD_MIN out that keeps ops/cadence.json's spacing. Publer is the only record of what is
    scheduled and posted (Mohammad, 23 Nov 2026): with a Publer read, its posts decide; the repository's logs stand in
    only while the server has no posting key."""
    import workorder as W
    if publer is not None:
        import publercheck as PC
        times = [t(PC.norm_post(p)['at']) for p in publer if 'kind:quick' not in PC.norm_post(p)['labels']]
        posts = [{'at': x} for x in times if x] + [{'at': x} for x in extra]
        return _first_free(now, posts, W)
    rows = load(os.path.join(REPO, 'newsroom', 'commitments.json'), {}) or {}
    rows = rows.get('rows', []) if isinstance(rows, dict) else rows
    led = load(os.path.join(REPO, 'templates', 'assets', 'format-ledger.json'), []) or []
    held = [t(r.get('slot')) for r in jsonl(LEDGER) if r.get('state') in ('ready', 'scheduled') and t(r.get('slot'))]
    posts = W.merge_posts(W.posts_from_commitments(rows, led), W.posts_from_logs(SUBMISSIONS, PUBLISHED),
                          [{'at': x, 'state': 'scheduled', 'labels': set(), 'networks': {}} for x in list(extra) + held])
    return _first_free(now, posts, W)


def _first_free(now, posts, W):
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
def _curl(args, key, ws=None, data=None, timeout=60, method=None):
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
        if method:
            cmd += ['-X', method]
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


def publer_ctx(key):
    """(workspace id, {platform: account id}) or (None, reason)."""
    code, ws = _curl([f'{API}/workspaces'], key, timeout=30)
    if code != 200 or not isinstance(ws, list) or not ws:
        return None, f'workspace lookup HTTP {code}'
    wid = next((w.get('id') for w in ws if (w.get('name') or '').strip().lower() == WORKSPACE.lower()), None) or \
        (ws[0].get('id') if len(ws) == 1 else None)
    if not wid:
        return None, 'workspace not found'
    code, accs = _curl([f'{API}/accounts'], key, wid, timeout=30)
    if code != 200 or not isinstance(accs, list):
        return None, f'accounts HTTP {code}'
    acc = {}
    for a in accs:
        prov = str(a.get('provider') or a.get('type') or '').lower()
        for p, n in NETWORK.items():
            if prov.startswith(n) and p not in acc:
                acc[p] = a.get('id')
    return (wid, acc), None


def publer_posts(key, wid, now):
    """Scheduled posts (today to 4 days out) and the last 48 hours of published ones, as the API returns them."""
    out = []
    spans = [('scheduled', now.date(), (now + dt.timedelta(days=4)).date()),
             ('published', (now - dt.timedelta(hours=48)).date(), now.date())]
    for state, a, b in spans:
        for page in range(6):
            code, js = _curl([f'{API}/posts?state={state}&from={a.isoformat()}&to={b.isoformat()}&page={page}'], key, wid,
                             timeout=30)
            items = js.get('posts') if isinstance(js, dict) else js
            if code != 200 or not isinstance(items, list):
                if page == 0:
                    raise RuntimeError(f'posts {state} HTTP {code}')
                break
            for p in items:
                p.setdefault('state', state)
            out += items
            if len(items) < 20:
                break
    return out


def publer_delete(key, wid, ids):
    """Deletes unpublished scheduled posts by id (rule 3: v2 replaces v1 while v1 has not posted)."""
    q = '&'.join('post_ids[]=' + re.sub(r'[^A-Za-z0-9]', '', str(i)) for i in ids if i)
    code, _ = _curl([f'{API}/posts?{q}'], key, wid, timeout=30, method='DELETE')
    return code in (200, 202, 204), f'delete HTTP {code}'


def publer_schedule(key, ctx, out, texts, labels, slot):
    """Schedules the Reel; (ok, note). `slot` is one time for every network or {platform: time}; a platform with no time or
    no text is left out (split by platform, 24 Nov 2026: the Reel's X and Threads post may come later or not at all).
    Never prints an id or a body."""
    wid, acc = ctx
    fname = os.path.basename(out)
    code, med = _curl([f'{API}/media?types[]=video&search=' + re.sub(r'[^A-Za-z0-9._-]', '', fname)], key, wid, timeout=30)
    items = (med or {}).get('media') if isinstance(med, dict) else med
    mid = next((m.get('id') for m in items or [] if m.get('name') == fname), None)
    if not mid:
        return False, f'the Reel is not in the Publer library by name (media HTTP {code})'
    slots = slot if isinstance(slot, dict) else {p: slot for p in NETWORK}
    posts = []
    for p, n in NETWORK.items():
        if not slots.get(p):
            continue
        if not acc.get(p) or not texts.get(p):
            return False, f'the account or the text for {p} is missing'
        net = {'type': 'video', 'text': texts[p], 'media': [{'id': mid, 'type': 'video'}]}
        if p == 'instagram':
            net['details'] = {'type': 'reel'}
        posts.append({'networks': {n: net}, 'accounts': [{'id': acc[p], 'scheduled_at': iso(slots[p])}],
                      'labels': [{'name': l} for l in labels]})
    if not posts:
        return False, 'no network to schedule'
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


# ---------------------------------------------------------------------------------------------- quick posts (24 Nov 2026)
def quick_slot(sid, publer=None):
    """The story's quick post time (scheduled or ready, from Publer's kind:quick posts or the quick log), or None."""
    base = base_of_story(sid)
    xs = [t(r.get('slot')) for r in jsonl(QUICK) if r.get('story') == sid and r.get('state') in ('ready', 'scheduled')]
    if publer:
        import publercheck as PC
        for p in publer:
            n = PC.norm_post(p)
            if 'kind:quick' in n['labels'] and f'story:{base}' in n['labels']:
                xs.append(t(n['at']))
    xs = [x for x in xs if x]
    return min(xs) if xs else None


def base_of_story(sid):
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', str(sid or ''))


def reel_networks(sid, slot, texts, publer=None):
    """({platform: time}, note) for a Reel (split by platform, Mohammad 24 Nov 2026): Instagram at the Reel's slot; X and
    Threads as their own post, at least REEL_AFTER_QUICK after the story's quick post, with the story's reel_x and
    reel_threads texts (a first line that leads with what the video shows), and not at all once the quick post is older
    than REEL_XT_MAX. A story with no quick post keeps the three networks at one time, as before."""
    q = quick_slot(sid, publer)
    if q is None:
        return {'instagram': slot, 'x': slot, 'threads': slot}, ''
    xt = max(slot, q + REEL_AFTER_QUICK)
    if xt - q > REEL_XT_MAX:
        return {'instagram': slot}, f'Instagram only: the quick post went out {iso(q)}, over 24 hours before'
    if not (texts.get('reel_x') and texts.get('reel_threads')):
        return {'instagram': slot}, 'Instagram only: no reel_x / reel_threads text in the story file (the Reel\'s X and ' \
                                    'Threads post needs its own first line about what the video shows)'
    note = f'X and Threads at {iso(xt)}, {int((xt - q).total_seconds() // 60)} min after the quick post' if xt != slot else ''
    return {'instagram': slot, 'x': xt, 'threads': xt}, note


def quick_next(now, publer=None, extra=(), t0=False):
    """The first minute QUICK_LEAD_MIN out (2 for T0) that is QUICK_SPACING from every other quick post."""
    import publercheck as PC
    taken = [t(r.get('slot')) for r in jsonl(QUICK) if r.get('state') in ('ready', 'scheduled')]
    taken += [t(PC.norm_post(p)['at']) for p in publer or [] if 'kind:quick' in PC.norm_post(p)['labels']]
    taken = [x for x in taken + list(extra) if x]
    x = (now + dt.timedelta(minutes=2 if t0 else QUICK_LEAD_MIN)).replace(second=0, microsecond=0)
    for _ in range(24 * 60):
        if all(abs((p - x).total_seconds()) >= QUICK_SPACING * 60 for p in taken):
            return x
        x += dt.timedelta(minutes=1)
    return x


def publer_schedule_quick(key, ctx, card, texts, labels, slot):
    """The quick card as a photo post on X and Threads at one time; (ok, note)."""
    wid, acc = ctx
    fname = os.path.basename(card)
    code, med = _curl([f'{API}/media?types[]=photo&search=' + re.sub(r'[^A-Za-z0-9._-]', '', fname)], key, wid, timeout=30)
    items = (med or {}).get('media') if isinstance(med, dict) else med
    mid = next((m.get('id') for m in items or [] if m.get('name') == fname), None)
    if not mid:
        return False, f'the card is not in the Publer library by name (media HTTP {code})'
    posts = [{'networks': {n: {'type': 'photo', 'text': texts[p], 'media': [{'id': mid, 'type': 'photo'}]}},
              'accounts': [{'id': acc[p], 'scheduled_at': iso(slot)}], 'labels': [{'name': l} for l in labels]}
             for p, n in QUICK_NET.items() if acc.get(p) and texts.get(p)]
    if len(posts) < 2:
        return False, 'the X or Threads account or text is missing'
    code, js = _curl([f'{API}/posts/schedule'], key, wid, data={'bulk': {'state': 'scheduled', 'posts': posts}})
    job = (js or {}).get('job_id') if isinstance(js, dict) else None
    if code not in (200, 201) or not job:
        return False, f'schedule HTTP {code}'
    import time
    for _ in range(20):
        time.sleep(3)
        code, st = _curl([f'{API}/job_status/{job}'], key, wid, timeout=30)
        s_ = str((st or {}).get('status', '')).lower() if isinstance(st, dict) else ''
        if s_ in ('complete', 'completed'):
            return True, 'job status complete'
        if s_ == 'failed':
            return False, 'job status failed'
    return False, 'job status not complete after 60 s (look the posts up in Publer before any retry)'


def quick_labels(story, base):
    g = story.get('genre')
    g = g[0] if isinstance(g, list) and g else g
    return ['kind:quick', 'tpl:quick', 'skin:house'] + ([f'genre:{g}'] if g else []) + [f'story:{base}']


def quick_sweep(now=None, dry=False, key=None, ctx=None, posts=None):
    """Schedules every rendered quick card on X and Threads (or writes it ready for the connector)."""
    import publercheck as PC
    import quickpost as QP
    if not QP.live():
        return []
    now = now or now_utc()
    rows = jsonl(QUICK)
    last = {}
    for r in rows:
        last[r.get('story')] = r
    acts, taken = [], []
    for sid, r in last.items():
        if r.get('state') != 'rendered':
            continue
        at = t(r.get('at'))
        if at and now - at > dt.timedelta(hours=REEL_XT_MAX.total_seconds() // 3600):
            acts.append(dict(r, at=iso(now), state='skipped', note='rendered over 24 hours ago; not posted'))
            continue
        story = load(os.path.join(STORIES, f'{sid}.json'), None)
        if not isinstance(story, dict) or re.search(r'dropped|held|pulled|parked', str(story.get('status', '')), re.I) \
                or story.get('held_by_mohammad'):
            acts.append(dict(r, at=iso(now), state='skipped', note='story dropped or held'))
            continue
        tx = QP.texts(story)
        if not (tx.get('x') and tx.get('threads')):
            acts.append(dict(r, at=iso(now), state='held', note='no x or threads text in the story file'))
            continue
        others = [p for p in (posts or []) if 'kind:quick' in PC.norm_post(p)['labels']] + \
                 [p for p in (posts or []) if PC.norm_post(p)['state'] == 'published']
        act, line = PC.verdict(sid, r.get('base'), story.get('game'), tx['x'], others)
        if act != 'prepare':
            acts.append(dict(r, at=iso(now), state='skipped', note=line))
            continue
        slot = quick_next(now, posts, taken, bool(r.get('t0')))
        taken.append(slot)
        labels = quick_labels(story, r.get('base'))
        row = dict(r, at=iso(now), slot=iso(slot), labels=labels, networks=['x', 'threads'])
        if dry:
            acts.append(dict(row, state='(dry) quick'))
            continue
        if key and ctx:
            ok, why = publer_schedule_quick(key, ctx, r['card'], tx, labels, slot)
            if ok:
                acts.append(dict(row, state='scheduled', note=why))
                continue
            row['note'] = f'Publer API: {why}'
        acts.append(dict(row, state='ready', note=(row.get('note', '') + '; schedule through the Publer connector: a photo '
                                                   'post on X and Threads at the slot, the card from cards/, texts quick_x/x '
                                                   'and quick_threads/threads from the story file, the labels; then '
                                                   'quickpost.py scheduled <story> --slot <ISO>').strip('; ')))
    if not dry:
        for a in acts:
            append(QUICK, a)
    return acts


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
    base = re.sub(r'-reel-v\d+\.mp4$', '', os.path.basename(str(job.get('out') or ''))) or \
        re.sub(r'^\d{4}-\d{2}-\d{2}-', '', str(story.get('id') or ''))
    if base:
        out.append(f'story:{base}')             # Publer is the source of truth (23 Nov): the story id rides on every post
    return out


def record_schedule(story, slot, labels, state, note, by, nets=None):
    at = iso(now_utc())
    nets = nets or {p: slot for p in ('instagram', 'x', 'threads')}
    for p, when in nets.items():
        append(SUBMISSIONS, {'commitment': story, 'platform': p, 'story': story, 'state': state, 'at': at,
                             'labels': ','.join(labels), 'slot': iso(when), 'job_status': 'complete' if state == 'scheduled' else None,
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
        if any(r.get('out') == out and r.get('state') in ('held', 'duplicate', 'ready', 'scheduled') for r in mine):
            continue                                            # this Reel was decided already
        pr = prior(sid, ledger, subs, now)
        if pr and pr[0] in ('posted', 'unknown'):
            if pr[0] == 'posted' and any(r.get('state') in ('scheduled', 'ready') for r in mine) and \
                    not any(r.get('out') == out for r in mine):
                actions.append({'at': iso(now), 'story': sid, 'base': base, 'out': out, 'state': 'duplicate',
                                'note': 'an earlier version already posted; this version is not posted (rule 3, 23 Nov)'})
            continue                                            # Production 2 or the connector has it
        replace_at = pr[1] if pr and pr[0] == 'scheduled' else None
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
        if verdict == 'none' and not replace_at:
            dup = recent_game(dict(story, id=sid), subs, now)
            if dup:
                actions.append(dict(row, state='held', note=f'no director verdict and the same game went out in the '
                                    f'last 48 hours ({dup}): a duplicate or a follow-up? a director pass schedules it'))
                continue
        st_t = story.get('texts') or {}
        texts = {p: st_t.get(p) for p in ('instagram', 'x', 'threads')}
        if not all(texts.values()):
            actions.append(dict(row, state='held', note='story texts missing for ' +
                                ', '.join(p for p, v in texts.items() if not v) + '; write them in the story file'))
            continue
        # Publer is the source of truth (Mohammad, 23 Nov 2026): read it again just before the submit
        import publercheck as PC
        ctx, posts, why_ctx = None, None, None
        if key and not dry:
            ctx, why_ctx = publer_ctx(key)
            if ctx:
                try:
                    posts = publer_posts(key, ctx[0], now)
                except Exception as ex:                 # noqa: BLE001
                    why_ctx = str(ex)
        own = [p for p in PC.from_logs(now) if p.get('story') != sid]
        reel_posts = [p for p in (posts or []) if 'kind:quick' not in PC.norm_post(p)['labels']]   # our quick post is not a repeat
        act, line = PC.verdict(sid, base, story.get('game'), texts['instagram'], reel_posts + own)
        if act == 'stop':
            actions.append(dict(row, state='duplicate', note=line))
            continue
        old = [PC.norm_post(p) for k, p in PC.matches(sid, base, story.get('game'), texts['instagram'], reel_posts)
               if k == 'story'] if act == 'replace' else []
        if old:
            replace_at = min((t(p['at']) for p in old if t(p['at'])), default=replace_at)
        if replace_at and replace_at > now + dt.timedelta(minutes=2):
            slot = replace_at                                   # v2 takes v1's minute (rule 3)
        else:
            slot = next_slot(now, taken, posts)
        taken.append(slot)
        labels = labels_for(job, dict(story, id=sid), qc)
        nets, nnote = reel_networks(sid, slot, st_t, posts)
        if 'x' in nets and quick_slot(sid, posts) is not None:      # the Reel's own X and Threads text (24 Nov 2026)
            texts = dict(texts, x=st_t.get('reel_x'), threads=st_t.get('reel_threads'))
        row.update(slot=iso(slot), labels=labels, networks={p: iso(x) for p, x in nets.items()})
        if nnote:
            row['split'] = nnote
        if replace_at:
            row['replaces'] = 'the scheduled earlier version at ' + iso(replace_at)
        if verdict == 'none':
            row['note'] = note or 'no director verdict'
        elif note:
            row['note'] = note
        if dry:
            actions.append(dict(row, state='(dry) schedule'))
            continue
        if key and not ctx:
            row['note'] = (row.get('note', '') + f'; Publer API: {why_ctx}').strip('; ')
        if key and ctx and old:
            ok_d, why_d = publer_delete(key, ctx[0], [p['id'] for p in old if p['state'] != 'published'])
            if not ok_d:
                row['note'] = (row.get('note', '') + f'; the earlier version was not deleted ({why_d})').strip('; ')
                ctx = None                                      # never two versions in Publer: hand it to the connector
        if key and ctx:
            ok, why = publer_schedule(key, ctx, out, texts, labels, nets)
            if ok:
                record_schedule(sid, slot, labels, 'scheduled', row.get('note', ''), 'server', nets)
                actions.append(dict(row, state='scheduled', publer=why))
                continue
            row['note'] = (row.get('note', '') + f'; Publer API: {why}').strip('; ')
        actions.append(dict(row, state='ready', note=(row.get('note', '') + '; check Publer first (scheduled and the last 48 '
                                                       'hours published, publercheck.py), ' +
                                                       ('delete the scheduled earlier version, ' if replace_at else '') +
                                                       'schedule through the Publer connector at the slot with the labels '
                                                       '(each network at its time in "networks"; X and Threads with the story\'s '
                                                       'reel_x and reel_threads when a quick post went out), '
                                                       'then serverpost.py scheduled').strip('; ')))
    if not dry:
        for a in actions:
            append(LEDGER, a)
    try:                                                    # quick posts (split by platform, 24 Nov 2026)
        qctx = qposts = None
        if key and not dry:
            qctx, _ = publer_ctx(key)
            qposts = publer_posts(key, qctx[0], now) if qctx else None
        actions += [dict(a, base=(a.get('base') or '') + ' (quick)') for a in quick_sweep(now, dry, key, qctx, qposts)]
    except Exception as ex:                                 # noqa: BLE001
        actions.append({'state': 'quick-error', 'base': 'quick posts', 'note': str(ex)[:200]})
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
