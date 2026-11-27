"""The shot matches its line (Mohammad, 27 Nov 2026, shot rule 2). Autofix only: it never refuses or holds a Reel.

Each footage shot's line (the story line over it; the headline for the first shot) is read for its subject: a vehicle
(a driving or car-physics story gets cars), a person or character (a character story gets that character, by name
where the game's curated library tags one), an animal, a place. The shot's own middle frame is read by the same
detector as autofocus (YOLOv8n: person, vehicle, animal). A shot that does not show its line's subject moves to one
that does, in this order: the game's curated stretches tagged for it (templates/assets/game-stretches.json, on a file
the job holds), then the clean stretches the shot read found whose middle frame shows it. No match: the shot keeps its
place unless it is a romance or intimate stretch, which moves to the nearest clean action shot. Blocked stretches are
never a candidate. Every move is on the picture ladder (qc.json `ladder`).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BUDGET = 75.0              # seconds for the whole pass (frames and one detector run)
MAX_CANDS = 24             # read-stretch candidates per job

WORDS = {
    'vehicle': ['سيارة', 'سيارات', 'القيادة', 'قيادة', 'يقود', 'تقود', 'السباق', 'سباق', 'المركبات', 'مركبة', 'شاحنة',
                'دراجة', 'دراجات', 'الطائرة', 'طائرة', 'طائرات', 'قارب', 'يخت', 'مطاردة', 'فيزياء', 'drive', 'driving',
                'car', 'cars', 'vehicle', 'racing', 'race', 'truck', 'bike', 'plane', 'boat', 'chase', 'physics'],
    'person': ['شخصية', 'الشخصية', 'شخصيات', 'البطل', 'البطلة', 'بطل', 'بطلة', 'الممثل', 'الممثلة', 'يؤدي', 'تؤدي',
               'character', 'protagonist', 'hero', 'heroine', 'actor', 'actress', 'cast'],
    'animal': ['حيوان', 'حيوانات', 'وحش', 'وحوش', 'تمساح', 'الصيد', 'صيد', 'animal', 'animals', 'creature', 'monster',
               'hunt', 'hunting', 'wildlife'],
}
TAG_CLASS = {'car': 'vehicle', 'driving': 'vehicle', 'bike': 'vehicle', 'plane': 'vehicle', 'police': 'vehicle',
             'person': 'person', 'people': 'person', 'crowd': 'person', 'jason': 'person', 'lucia': 'person',
             'action': 'action'}
COCO = {0: 'person', **{k: 'vehicle' for k in range(1, 9)}, **{k: 'animal' for k in range(14, 24)}}

_DET = r"""
import json, os, sys
w, paths = sys.argv[1], sys.argv[2:]
from ultralytics import YOLO
out = []
for r in YOLO(w).predict(paths, imgsz=640, conf=0.3, device='cpu', verbose=False):
    h, wd = r.orig_shape
    seen = {}
    for c, (x1, y1, x2, y2) in zip(r.boxes.cls.tolist(), r.boxes.xyxy.tolist()):
        a = (x2 - x1) * (y2 - y1) / (wd * h)
        seen[int(c)] = max(seen.get(int(c), 0.0), a)
    out.append(seen)
print('@@' + json.dumps(out))
"""


def line_text(job, i):
    """The text over shot i: its line group's lines, and the headline for the first shot."""
    out = []
    if i == 0:
        out.append(str(job.get('headline') or ''))
    for g in job.get('lines') or []:
        if len(g) > 2 and isinstance(g[0], int) and isinstance(g[1], int) and g[0] <= i <= g[1]:
            out += [x[0] if isinstance(x, list) else str(x) for x in g[2]]
    return ' '.join(out)


def wants(text, subjects=None):
    """(classes, named tags): what the line is about."""
    t = ' ' + re.sub(r'[ً-ْ]', '', str(text or '')).lower() + ' '
    cls = {k for k, ws in WORDS.items() if any(re.search(r'(?<![\w؀-ۿ])[وفبلك]?(?:ال)?' + re.escape(w.lower())
                                                       + r'(?![\w؀-ۿ])', t) or w.lower() in t.split() for w in ws)}
    named = {tag for tag, ws in (subjects or {}).items() if any(w.lower() in t for w in ws)}
    for tag in named:
        if TAG_CLASS.get(tag) in ('person', 'vehicle'):
            cls.add(TAG_CLASS[tag])
    return cls, named


def detect(frames, weights=None):
    """[{class group: largest box share}] per frame; [] when the detector cannot run."""
    import reel
    weights = weights or reel.YOLO_WEIGHTS
    env = dict(os.environ)
    if os.path.isdir(reel.YOLO_LIBS):
        env['PYTHONPATH'] = reel.YOLO_LIBS + os.pathsep + env.get('PYTHONPATH', '')
    try:
        r = subprocess.run([sys.executable, '-c', _DET, weights] + list(frames), capture_output=True, text=True, env=env,
                           check=True, timeout=BUDGET)
        raw = json.loads([l for l in r.stdout.splitlines() if l.startswith('@@')][-1][2:])
    except Exception as e:                       # noqa: BLE001
        print(f'subjectmatch: detector unavailable ({str(e)[:120]})', flush=True)
        return []
    out = []
    for seen in raw:
        g = {}
        for c, a in seen.items():
            k = COCO.get(int(c))
            if k:
                g[k] = max(g.get(k, 0.0), a)
        out.append(g)
    return out


def _grab(path, t, out):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', path, '-frames:v', '1',
                    '-vf', 'scale=640:-2', out], capture_output=True, timeout=20)
    return os.path.exists(out)


def run(job, upath, reads=None, frame_ok=None, dur_of=None, ladder=None):
    """Match every footage shot to its line (module note). Returns the moved slots."""
    import blocked as B
    import variety
    t_end = time.time() + BUDGET
    shots = job.get('shots') or []
    vids = B._vids(job)
    reads = reads or {}
    cur, subjects = variety.curated(job.get('game') or job.get('game_short'))
    held = {}                                                 # curated file id -> (job file, offset)
    for s in cur:
        for it in job.get('footage') or []:
            if it.get('file') in vids and (it.get('url') == s['url'] or (it.get('repo') and it['repo'] in (s.get('same') or []))):
                held[s['file']] = (it['file'], float(it.get('start') or 0.0) if it.get('stream') else 0.0)
    need = {}
    for i, sh in enumerate(shots):
        if not (isinstance(sh, list) and len(sh) > 2 and sh[0] in vids and isinstance(sh[1], (int, float))):
            continue
        cls, named = wants(line_text(job, i), subjects)
        rom = any(B.romance(s) and held.get(s['file'], (None,))[0] == sh[0]
                  and float(s['start']) - held[s['file']][1] < float(sh[1]) + float(sh[2])
                  and float(sh[1]) < float(s['start']) - held[s['file']][1] + float(s['secs']) for s in cur)
        if cls or named or rom:
            need[i] = (cls, named, rom)
    if not need:
        return []
    tmp = tempfile.mkdtemp(prefix='subj-')
    frames, keys = [], []
    for i in need:                                           # the shot's own middle frame
        sh = shots[i]
        p = os.path.join(tmp, f'shot{i}.png')
        if _grab(os.path.join(upath, sh[0]), float(sh[1]) + float(sh[2]) / 2, p):
            frames.append(p)
            keys.append(('shot', i, sh[0], float(sh[1]), None))
    pool = []                                                # read stretches as candidates
    for f in vids:
        for s in B.split(sorted((reads.get(f) or {}).get('shots') or [], key=lambda s: s['start']), B.ranges(job, f)):
            pool.append((f, float(s['start']) + 0.1, float(s['end']), s.get('focus')))
    step = max(1, len(pool) // MAX_CANDS)
    for n, (f, st, en, fo) in enumerate(pool[::step][:MAX_CANDS]):
        if time.time() > t_end - 30:
            break
        p = os.path.join(tmp, f'c{n}.png')
        if _grab(os.path.join(upath, f), (st + en) / 2, p):
            frames.append(p)
            keys.append(('cand', n, f, st, (en, fo)))
    det = detect(frames) if frames else []
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    seen = {k: (det[n] if n < len(det) else None) for n, k in enumerate(keys)}
    moved = []
    for i, (cls, named, rom) in need.items():
        sh = shots[i]
        secs = float(sh[2])
        got = next((v for k, v in seen.items() if k[0] == 'shot' and k[1] == i), None)
        if got is not None and cls and any(got.get(c, 0) >= 0.02 for c in cls) and not named and not rom:
            continue                                          # it already shows what the line is about
        if got is None and not named and not rom:
            continue                                          # no read: the shot stands
        taken = B._taken(job, skip=i)
        pick = None
        # 1. curated stretches tagged for the line (a named character first), on a file the job holds
        best = []
        for s in cur:
            if s['file'] not in held or B.romance(s):
                continue
            tags = set(s.get('tags') or [])
            sc = 3 * len(tags & named) + sum(1 for t in tags if TAG_CLASS.get(t) in cls)
            if sc <= 0 and not rom:
                continue
            if rom and sc <= 0 and not (tags & {'action', 'car', 'city'}):
                continue
            f, off = held[s['file']]
            st = round(float(s['start']) - off, 2)
            ln = min(secs, float(s['secs']) + 1.5)
            if st < 0 or B.hit(job, f, st, ln) or not B._free(st, ln, taken.get(f, [])):
                continue
            best.append((sc, f, st, s.get('focus'), s.get('label')))
        best.sort(key=lambda x: -x[0])
        for sc, f, st, fo, label in best:
            if frame_ok is None or frame_ok(f, st, secs, dur_of(f) if dur_of else None)[0]:
                pick = (f, st, fo, f'curated: {label}')
                break
        # 2. read stretches whose middle frame shows the line's subject (or any action subject for a romance shot)
        if not pick:
            want = cls or ({'vehicle', 'person'} if rom else set())
            for k, v in seen.items():
                if k[0] != 'cand' or not v or not any(v.get(c, 0) >= 0.02 for c in want):
                    continue
                f, st, (en, fo) = k[2], k[3], k[4]
                if en - st < secs or B.hit(job, f, st, secs) or not B._free(st, secs, taken.get(f, [])):
                    continue
                pick = (f, round(st, 2), fo, 'read stretch showing ' + '/'.join(sorted(c for c in want if v.get(c, 0) >= 0.02)))
                break
        if not pick or (pick[0] == sh[0] and abs(pick[1] - float(sh[1])) < 0.3):
            continue
        f, st, fo, how = pick
        sh[0], sh[1] = f, st
        if len(sh) > 3:
            sh[3] = [[0.0, fo]] if isinstance(fo, (int, float)) else None
        for key in ('cut_ok', 'drift_ok'):
            job.setdefault(key, []).append([f, st, 'shot matches line (27 Nov 2026)'])
        moved.append(i)
        if ladder:
            ladder('picture', i, 'a', f'shot matches line ({", ".join(sorted(cls | named)) or "no romance"}): {f} at {st} s, {how}')
    if moved:
        print(f'subjectmatch: {len(moved)} shot(s) moved to match their line: {moved}', flush=True)
    return moved
