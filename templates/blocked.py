"""Blocked stretches: what no Reel shows (Mohammad, 27 Nov 2026, shot rules 1 and 4). Autofix only: nothing here
refuses, holds or delays a Reel.

Reels are for a general Gulf audience. A kiss is fine; anything more intimate is not (kissing in a shower or bed,
partial nudity, lingerie or swimwear close-ups, suggestive dancing, strip-club scenes). The stretches live in
templates/assets/blocked-stretches.json, keyed by trailer, each entry [start, end, reason] in the trailer's seconds.

  ranges(job, f)        the blocked ranges on file f's own timeline (a stream copy that starts at s is offset by s)
  split(stretches, rs)  clean stretches with the blocked ranges cut out (the automatic shot picker uses it)
  clear(job, ...)       every footage shot overlapping a blocked range moves, in this order (rule 4):
                          a. another clean shot of the same trailer (a matching shot first, never another blocked or
                             romance stretch), b. another official trailer of the game in the job's footage,
                          c. an official still or key art in the job's footage (slow push-in), d. the least bad free
                          moment that is not blocked. The Reel always ships; every move is on the picture ladder.
  scan_new(job)         a mature-rated trailer not in the ledger is scanned once on first use (a classifier over one
                        frame a second); the new entry is written to RUNNER_TEMP/blocked-new.json and committed with
                        the render. A scan that cannot run is a warning, never a hold.

CLI: python3 templates/blocked.py add <trailer or file> <start> <end> <reason>   (the director's fix, or by hand)
     python3 templates/blocked.py merge <blocked-new.json>                         (the workflow, after a render)
     python3 templates/blocked.py show <file>
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'assets', 'blocked-stretches.json')
PAD = 0.15                 # seconds either side of a blocked range a shot also keeps clear of
VIDEO = ('.mp4', '.mov', '.mkv', '.webm', '.m4v')
STILL = ('.jpg', '.jpeg', '.png', '.webp')
ROMANCE = {'couple', 'romance', 'kiss', 'nightlife', 'bar', 'bed', 'club', 'dance', 'dancing'}
_CACHE = {}


def load(path=None):
    path = path or LEDGER
    if path not in _CACHE:
        try:
            _CACHE[path] = json.load(open(path, encoding='utf-8'))
        except (OSError, ValueError):
            _CACHE[path] = {'trailers': {}}
    return _CACHE[path]


def _base(x):
    return os.path.basename(str(x or '').split('?')[0]).lower()


def _item(job, f):
    return next((it for it in (job or {}).get('footage') or [] if it.get('file') == f), None)


def key_for(job, f, led=None):
    """(trailer key, offset) for file f of the job, or (None, 0.0). The offset is the trailer second at the file's 0."""
    led = led or load()
    it = _item(job, f) or {'file': f}
    names = {_base(it.get('file')), _base(it.get('repo')), _base(it.get('url')), str(it.get('repo') or '').lower(),
             str(it.get('url') or '').lower()} - {''}
    off = float(it.get('start') or 0.0) if it.get('stream') else 0.0
    m = re.match(r'(.+?)-from-([0-9.]+)\.mp4$', str(f))   # hook stream copies (render_job.hook_pick)
    if m:
        names.add(_base(m.group(1)))
        off = off or float(m.group(2))
    for k, e in (led.get('trailers') or {}).items():
        keys = {k.lower(), _base(e.get('url')), str(e.get('url') or '').lower()} | {str(x).lower() for x in e.get('files') or []} \
            | {_base(x) for x in e.get('files') or []}
        if names & (keys - {''}):
            return k, off
    return None, 0.0


EXTRA = {}                 # file -> [(a, b, reason)] set for this render: each trailer's end slate (render_job.shot_rules)


def ranges(job, f, led=None):
    """[(a, b, reason)] on file f's timeline, padded by PAD, plus this render's EXTRA ranges for f."""
    led = led or load()
    k, off = key_for(job, f, led)
    out = list(EXTRA.get(f, []))
    if not k:
        return out
    return out + [(float(a) - off - PAD, float(b) - off + PAD, str(r)) for a, b, r in led['trailers'][k].get('blocked') or []
                  if float(b) - off > 0]


def hit(job, f, st, secs, led=None):
    """The reason of the first blocked range the stretch [st, st + secs] touches, or None."""
    for a, b, r in ranges(job, f, led):
        if st < b and st + secs > a:
            return r
    return None


def split(stretches, rs):
    """Shotpick stretches ({'start', 'end', ...}) with the blocked ranges taken out."""
    if not rs:
        return stretches
    out = []
    for s in stretches:
        pieces = [(float(s['start']), float(s['end']))]
        for a, b, _r in rs:
            nxt = []
            for x, y in pieces:
                if b <= x or a >= y:
                    nxt.append((x, y))
                    continue
                if a > x:
                    nxt.append((x, a))
                if b < y:
                    nxt.append((b, y))
            pieces = nxt
        for x, y in pieces:
            if y - x > 0.5:
                out.append(dict(s, start=round(x, 2), end=round(y, 2)))
    return out


def romance(stretch):
    t = {str(x).lower() for x in stretch.get('tags') or []}
    return bool(t & ROMANCE) or any(w in str(stretch.get('label') or '').lower() for w in ('couple', 'kiss', 'bed'))


def _vids(job):
    return [it['file'] for it in job.get('footage') or [] if str(it.get('file', '')).lower().endswith(VIDEO)]


def _stills(job):
    return [it['file'] for it in job.get('footage') or [] if str(it.get('file', '')).lower().endswith(STILL)
            and '-gfx-' not in str(it.get('file')) and not str(it.get('role', '')).startswith('person')]


def _taken(job, skip=None):
    out = {}
    for k, s in enumerate(job.get('shots') or []):
        if k == skip or not (isinstance(s, list) and len(s) > 2 and isinstance(s[1], (int, float))):
            continue
        out.setdefault(s[0], []).append((float(s[1]), float(s[1]) + float(s[2])))
    return out


def _free(st, secs, taken):
    return all(st + secs <= a or st >= b for a, b in taken)


def candidates(job, f, secs, dur, read=None, prefer=None):
    """Start times on file f for a shot of secs, best first: prefer(f) -> [(start, focus)] (a matching shot), the clean
    stretches the read found, then evenly spaced points. None of them blocked."""
    rs = ranges(job, f)
    out = []
    for st, fo in (prefer(f) if prefer else []) or []:
        out.append((float(st), fo, 'matching shot'))
    for s in split(sorted((read or {}).get('shots') or [], key=lambda s: s['start']), rs):
        if float(s['end']) - float(s['start']) >= secs:
            out.append((float(s['start']) + 0.1, s.get('focus'), 'clean stretch'))
    v0 = float((read or {}).get('picture_start') or 0.0)
    hi = (dur or 0.0) - 9.0 - secs                       # never the end slate (render_job.TAIL_SKIP)
    if hi > v0 + 0.3:
        out += [(v0 + 0.3 + (hi - v0 - 0.3) * k / 23, None, 'evenly spaced') for k in range(24)]
    return [(round(st, 2), fo, why) for st, fo, why in out if not any(st < b and st + secs > a for a, b, _ in rs)]


def clear(job, dur_of=None, frame_ok=None, reads=None, prefer=None, ladder=None):
    """Move every footage shot that overlaps a blocked range (see the module note). Returns the moved slots.
    dur_of(f) -> seconds; frame_ok(f, st, secs, dur) -> (bool, why); reads: {file: shotpick result};
    prefer(f, i) -> [(start, focus)]; ladder(kind, slot, step, why)."""
    shots = job.get('shots') or []
    vids = _vids(job)
    reads = reads or {}
    moved = []
    for i, sh in enumerate(shots):
        if not (isinstance(sh, list) and len(sh) > 2 and sh[0] in vids and isinstance(sh[1], (int, float))):
            continue
        why = hit(job, sh[0], float(sh[1]), float(sh[2]))
        if not why:
            continue
        secs = float(sh[2])
        taken = _taken(job, skip=i)
        pick = None
        order = [sh[0]] + [v for v in vids if v != sh[0]]
        spare = None
        for step, f in zip(['a'] + ['b'] * (len(order) - 1), order):
            d = dur_of(f) if dur_of else 0.0
            cands = candidates(job, f, secs, d, reads.get(f), (lambda g, i=i: prefer(g, i)) if prefer else None)
            cands.sort(key=lambda c: (0 if c[2] == 'matching shot' else 1, abs(c[0] - float(sh[1])) if f == sh[0] else 0))
            for st, fo, how in cands:
                if not _free(st, secs, taken.get(f, [])):
                    continue
                spare = spare or (f, st, fo, how, step)
                if frame_ok is None or frame_ok(f, st, secs, d)[0]:
                    pick = (f, st, fo, how, step)
                    break
            if pick:
                break
        if not pick:
            still = next(iter(_stills(job)), None)
            if still:
                sh[0], sh[1] = still, 0.0
                if len(sh) > 3:
                    sh[3] = None
                moved.append(i)
                if ladder:
                    ladder('picture', i, 'c', f'blocked ({why}): the official still {still} with slow motion')
                continue
            pick = spare
        if not pick:                                   # nothing free at all: the nearest unblocked second on its file
            rs = ranges(job, sh[0])
            st = max([b for a, b, _ in rs if a <= float(sh[1]) + secs] + [float(sh[1])])
            pick = (sh[0], round(st, 2), None, 'past the blocked range', 'd')
        f, st, fo, how, step = pick
        sh[0], sh[1] = f, st
        if len(sh) > 3:
            sh[3] = [[0.0, fo]] if isinstance(fo, (int, float)) else None
        moved.append(i)
        for key in ('cut_ok', 'drift_ok'):
            job.setdefault(key, []).append([f, st, 'blocked stretch avoided (27 Nov 2026)'])
        if ladder:
            ladder('picture', i, step, f'blocked ({why}): moved to {f} at {st} s ({how})')
    if moved:
        print(f'blocked: {len(moved)} shot(s) moved off blocked stretches: {moved}', flush=True)
    return moved


# ---- first-use scan of a mature-rated trailer -------------------------------------------------------------------------

RATING_WORDS = re.compile(r'MATURE|PEGI\s*18|NUDITY|SEXUAL|ADULTS\s*ONLY|\b18\+', re.I)
NSFW_MODEL = 'Falconsai/nsfw_image_detection'      # ViT image classifier, Apache-2.0 (model card), run on CPU
NSFW_MIN = 0.5
SCAN_CAP = 150.0                                   # seconds for one trailer's scan; past it the scan stops (a warning)


def _frame(path, t, w=480):
    out = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.2f}', '-i', path, '-frames:v', '1',
                          '-vf', f'scale={w}:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, timeout=30)
    return out.stdout


def mature(job, path):
    """True for a mature-rated trailer: the job says so, its game is listed, or a rating card in its first or last
    seconds reads MATURE, PEGI 18, Nudity or Sexual (tesseract)."""
    if job.get('mature'):
        return True
    try:
        import gamekey
        g = gamekey.key(job.get('game') or job.get('game_short'))
        if g and g in (load().get('mature_games') or []):
            return True
    except Exception:                                # noqa: BLE001
        pass
    import shutil
    if not shutil.which('tesseract'):
        return False
    try:
        dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                             path], text=True).strip() or 0)
    except (subprocess.CalledProcessError, ValueError, OSError):
        dur = 0.0
    for t in [0.5, 1.5, 2.5, 4.0] + ([dur - 4.0, dur - 2.0] if dur > 12 else []):
        png = _frame(path, t, 1280)
        if not png:
            continue
        txt = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '11'], input=png, capture_output=True,
                             timeout=20).stdout.decode('utf-8', 'ignore')
        if RATING_WORDS.search(txt):
            return True
    return False


_SCAN_PY = r"""
import io, json, sys
from PIL import Image
from transformers import pipeline
clf = pipeline('image-classification', model=sys.argv[1], device=-1)
out = []
for p in sys.argv[2:]:
    r = clf(Image.open(p).convert('RGB'))
    out.append(max([x['score'] for x in r if x['label'].lower() == 'nsfw'] + [0.0]))
print('@@' + json.dumps(out))
"""


def scan_file(path, cap=SCAN_CAP):
    """[(start, end, reason)] from one frame a second through the classifier, merged and padded half a second."""
    import tempfile
    import time
    t0 = time.time()
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                         path], text=True).strip() or 0)
    tmp = tempfile.mkdtemp(prefix='blkscan-')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', 'fps=1,scale=384:-2', '-q:v', '4',
                    os.path.join(tmp, 'f%05d.jpg')], timeout=cap, check=True)
    frames = sorted(os.listdir(tmp))
    env = dict(os.environ)
    if subprocess.run([sys.executable, '-c', 'import transformers'], capture_output=True).returncode:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--timeout', '60', 'transformers==4.46.3'],
                       capture_output=True, timeout=180, check=True)   # only on a first-use scan
    try:
        r = subprocess.run([sys.executable, '-c', _SCAN_PY, NSFW_MODEL] + [os.path.join(tmp, x) for x in frames],
                           capture_output=True, text=True, env=env, timeout=max(30.0, cap - (time.time() - t0)), check=True)
        scores = json.loads([l for l in r.stdout.splitlines() if l.startswith('@@')][-1][2:])
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    hot = [k for k, s in enumerate(scores) if s >= NSFW_MIN]
    out = []
    for k in hot:
        a, b = max(0.0, k - 0.5), min(dur, k + 1.5)
        if out and a <= out[-1][1]:
            out[-1][1] = b
            out[-1][2] = max(out[-1][2], scores[k])
        else:
            out.append([a, b, scores[k]])
    return [(round(a, 2), round(b, 2), f'classifier: nsfw {s:.2f}') for a, b, s in out]


def scan_new(job, upath, warn=None):
    """Scan, once, every mature-rated trailer of the job that the ledger does not know. New entries go to
    RUNNER_TEMP/blocked-new.json (merged and committed by the workflow) and into the loaded ledger, so this render
    already avoids them. Returns the keys added."""
    led = load()
    added = []
    for f in _vids(job):
        if key_for(job, f, led)[0]:
            continue
        path = os.path.join(upath, f)
        try:
            if not mature(job, path):
                continue
            rs = scan_file(path)
        except Exception as e:                        # noqa: BLE001  a scan that cannot run never holds a Reel
            if warn:
                warn('blocked scan', f'{f}: mature trailer not scanned ({type(e).__name__}: {str(e)[:160]}); shots as picked')
            continue
        it = _item(job, f) or {}
        k = re.sub(r'\.(mp4|mov|mkv|webm|m4v)$', '', _base(it.get('url')) or f, flags=re.I) or f
        e = {'game': job.get('game') or job.get('game_short'), 'url': it.get('url'), 'files': [f] + ([it['repo']] if it.get('repo') else []),
             'scanned': 'auto, first use, ' + NSFW_MODEL + ' at 1 fps', 'blocked': [list(x) for x in rs]}
        if it.get('stream') and it.get('start'):
            e['blocked'] = [[a + float(it['start']), b + float(it['start']), r] for a, b, r in e['blocked']]
        led.setdefault('trailers', {})[k] = e
        added.append(k)
        print(f'blocked: first-use scan of {f}: {len(rs)} blocked stretch(es)', flush=True)
    note_new(added)
    return added


def note_new(keys):
    """Write the named ledger entries to RUNNER_TEMP/blocked-new.json for the workflow to merge and commit."""
    if not keys or not os.environ.get('RUNNER_TEMP'):
        return
    p = os.path.join(os.environ['RUNNER_TEMP'], 'blocked-new.json')
    try:
        cur = json.load(open(p, encoding='utf-8'))
    except (OSError, ValueError):
        cur = {}
    led = load()
    cur.update({k: led['trailers'][k] for k in keys if k in led.get('trailers', {})})
    json.dump(cur, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def add(job_extra):
    """[[trailer or file, start, end, reason]]: entries a director or the build adds (job "blocked_add")."""
    led = load()
    for f, a, b, r in job_extra or []:
        k, off = key_for({}, f, led)
        if not k:
            k = re.sub(r'\.(mp4|mov|mkv|webm|m4v)$', '', _base(f)) or f
            led.setdefault('trailers', {}).setdefault(k, {'files': [f], 'scanned': 'by eye', 'blocked': []})
        led['trailers'][k].setdefault('blocked', []).append([round(float(a) + off, 2), round(float(b) + off, 2), str(r)])
        note_new([k])
    return led


def _save(led, path=None):
    json.dump(led, open(path or LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(path or LEDGER, 'a').write('\n')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['add'] and len(a) >= 5:
        _save(add([[a[1], float(a[2]), float(a[3]), ' '.join(a[4:])]]))
        print('added')
    elif a[:1] == ['merge'] and len(a) == 2:
        led = load()
        new = json.load(open(a[1], encoding='utf-8'))
        for k, e in new.items():                      # a new trailer, or new stretches of a known one
            have = led.setdefault('trailers', {}).setdefault(k, e)
            if have is not e:
                seen = {tuple(x[:2]) for x in have.get('blocked') or []}
                have.setdefault('blocked', []).extend(x for x in e.get('blocked') or [] if tuple(x[:2]) not in seen)
        _save(led)
        print(f'merged {len(new)}')
    elif a[:1] == ['show'] and len(a) == 2:
        print(json.dumps(ranges({}, a[1]), ensure_ascii=False))
    else:
        print(__doc__)
