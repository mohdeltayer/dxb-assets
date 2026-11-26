"""Shot checks on the server's own copy, before the first render (adv-20261115-one-render-server-checks, items B, C, D;
Mohammad 15 Nov 2026: "if the server can do it, focus on that so the director does not check multiple times").

On 15 Nov every Reel rendered three times although server qc passed each time. The send-backs this replaces:
  B  shot times picked on a different copy than the server renders. Duck Side of the Moon: the server copy's video
     starts 1.18 s into the seek timeline (1.52 s by its own clock), so the shots crossed the trailer's scene cuts and
     one landed on a letterboxed stretch (v1, v2).
  C  the subject drifts out of the 9:16 window during a shot (Dreamlight Valley v1, Ranger's Path v1; POPUCOM v2's
     submarine too, which the detector cannot see on stylised art).
  D  a card's ground on a busy frame (Duck v1, v2: the trailer behind the card was mid-action).

    python3 templates/shotgate.py job <job.json>        every footage file fetched first; prints every problem, exit 1
    python3 templates/shotgate.py read <uploads file>   the file's facts: picture start, scene cuts, letterbox

B, per footage shot: it may not start more than PIC_TOL before the picture (the video stream's start time minus the
file's, in the seek coordinates of `ffmpeg -ss`, on the copy in uploads), may not
cross one of the trailer's scene cuts (reel.scenes at CUT_THRESH, a cut within CUT_EDGE of either end is the shot's own
edge), and may not sit on a letterboxed stretch (reel._bars over the shot, as the montage reads it; bars over LB_TOL
rows and LB_SHARE of the height). Each refusal names
the nearest clean start: the start closest to the job's own, inside one scene, after the picture start and with no
letterbox, for the same length (or says how short the shot must be where no such start is near).
C, per footage shot: the subject (the largest person, vehicle or animal YOLOv8n finds in the shot's first frame that
the window holds at least half of, else the largest one) is
looked for again at the middle and the end (a subject already half out of the window at the first frame is
"cut"); when less than DRIFT_INSIDE of it is inside the 9:16 window the shot uses
(its focus, the letterbox crop and the frame height), the frames between are read every SAMPLE_STEP s and the problem
reads "subject leaves the crop at N s" with the longest safe length. Without the detector the check is skipped, said.
D, per -gfx- card on footage ("ground_footage", or the card's own [file, start]): ground_pick() picks the calmest window
of the card's length in the named stretch ([file, start] or [file, start, span]; span GROUND_SPAN s by default): the
lowest mix of motion and contrast on the 9:16 centre the ground shows, and prints it. "ground_seek": "fixed" in a job
keeps the seek as written (start plus the card's place on the clock).

Waivers, each after someone has looked: "cut_ok": [[file, start, reason]], "letterbox_ok": [[file, start, reason]]
(or "lowres_ok" naming the copies searched), "drift_ok": [[file, start, reason]]; start is the shot's own start.
Stills, our -gfx- cards and jobs/test examples without footage in uploads are not read. The breaking profile and
Famitsu Reels are outside it (speed first; their own checks run).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CUT_THRESH = 0.3          # scene score for a cut that refuses a shot (autofocus places keyframes at 0.2)
CUT_EDGE = 0.12           # a cut this close to a shot's start or end is the shot's own edge
LB_TOL = 8                # rows of letterbox under this are noise (reel._bars) ...
LB_SHARE = 0.015          # ... or under this share of the height (Duck v3, 15 Nov: 12 of 1080 rows, an encoder edge)
PIC_TOL = 0.25            # a shot may start this much before the picture (it loses that much, no black shows)
DRIFT_INSIDE = 0.5        # share of the subject that must stay inside the window
SAMPLE_STEP = 0.2
SUBJECT_MIN = 0.01        # subjects smaller than this share of the frame are not followed
AIMED_ELSEWHERE = 0.15    # under this share inside at the start, the window is framed on something else
CUT_MIN = 0.03            # a subject at least this share of the frame, half out of the window from the start, is cut
GROUND_SPAN = 12.0
GROUND_FPS = 6
SEARCH = 12.0             # seconds either side of a refused start searched for a clean one
STILL = ('.jpg', '.jpeg', '.png', '.webp')
# Crop fix (Mohammad, 26 Nov 2026, after the Dragon Quest Monsters Reel: the monster half out of the frame on the right,
# empty desert held for 5 s, HUD text cut at the left edge). Autofixes, never refusals: re-aim, another stretch, else the
# 16:9 showcase (render_job.shot_ladder). frame_problems() below.
LONG_MAX = 4.0            # no footage shot longer than this, unless it moves and its subject stays in the window
MOTION_MIN = 8.0          # mean grey difference (0-255, 160 px wide) between a shot's first and last frame: moving
TEXT_CONF = 70            # tesseract confidence for a word crossing the window edge (HUD numbers and captions)
TEXT_MIN_H = 0.015        # ... at least this share of the frame high (noise is smaller)
STYLISED_GENRES = {'anime', 'family', 'platformer', 'party', 'cosy', 'cozy', 'kids', 'cartoon', 'mascot', 'monster',
                   'creature collector', 'monster collector'}
STYLISED_WORDS = ('pokemon', 'pok\u00e9mon', 'mario', 'kirby', 'zelda', 'dragon quest', 'monster', 'digimon', 'yo-kai',
                  'animal crossing', 'splatoon', 'pikmin', 'sonic', 'one piece', 'dragon ball', 'naruto', 'my hero',
                  'persona', 'fire emblem', 'xenoblade', 'smash bros', 'donkey kong', 'yoshi', 'metroid', 'palworld',
                  'cookie run', 'genshin', 'honkai', 'zenless', 'hello kitty', 'minecraft', 'roblox', 'rayman', 'crash',
                  'spyro', 'ratchet', 'astro bot', 'slime', 'chocobo', 'puyo', 'blue archive', 'melty blood')

_BOXES_PY = r"""
import json, os, sys
w, cls, paths = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3:]
from ultralytics import YOLO
if not os.path.exists(w):
    os.makedirs(os.path.dirname(w) or '.', exist_ok=True)
    from ultralytics.utils.downloads import attempt_download_asset
    attempt_download_asset(w)
out = []
for r in YOLO(w).predict(paths, imgsz=640, conf=0.25, classes=cls, device='cpu', verbose=False):
    h, wd = r.orig_shape
    bs = []
    for (x1, y1, x2, y2), c in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist()):
        bs.append([x1 / wd, x2 / wd, y1 / h, y2 / h, int(c)])
    out.append(bs)
print('@@' + json.dumps(out))
"""


def _U():
    import cards as C
    return C.U


def _probe(path):
    """(width, height, picture start, duration) of the file's first video stream. The picture start is in the seek
    coordinates reel.py uses (`ffmpeg -ss T -i file` seeks to T past the file's own start time): the video stream's
    start time minus the file's (Trafficity, 15 Nov: video 1.588 s, file 0.640 s, so the picture starts at 0.948 s)."""
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,start_time:format=duration,start_time', '-of', 'json', path],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout or '{}')
        st = (d.get('streams') or [{}])[0]
        fs = float((d.get('format') or {}).get('start_time') or 0)
        return (int(st.get('width') or 0), int(st.get('height') or 0), max(0.0, float(st.get('start_time') or 0) - fs),
                float((d.get('format') or {}).get('duration') or 0))
    except (ValueError, TypeError):
        return 0, 0, 0.0, 0.0


def read(f):
    """The copy's own facts, as the render will read them."""
    path = _U() + f
    w, h, v0, dur = _probe(path)
    return {'file': f, 'width': w, 'height': h, 'picture_start': round(v0, 3), 'duration': round(dur, 3)}


def _cuts(f, a, secs):
    """Source seconds of the scene cuts between a and a + secs."""
    import reel
    a = max(0.0, a)
    return [round(a + c, 3) for c in reel.scenes(f, a, secs, CUT_THRESH)[1:]]


def _letterbox_rows(f, a, secs, full, bars=None):
    """Picture rows the montage keeps for this stretch (reel._bars, or `bars` already read), and whether that is a letterbox."""
    import reel
    if os.path.basename(f) in reel.NOBARS:
        return full, False
    _crop, rows = bars or reel._bars(_U() + f, max(0.0, a), max(0.3, secs))
    return rows, bool(full and rows < full - max(LB_TOL, LB_SHARE * full))


def _waived(job, key, f, start):
    for w in job.get(key) or []:
        if isinstance(w, (list, tuple)) and len(w) >= 3 and w[0] == f and abs(float(w[1]) - float(start)) < 0.05 \
                and len(str(w[2]).strip()) >= 5:
            return True
    return False


def _clean(f, s, secs, info):
    """Whether [s, s + secs] is inside one scene, after the picture start and unletterboxed."""
    if s < info['picture_start'] - 0.02 or (info['duration'] and s + secs > info['duration'] + 0.02):
        return False
    if any(s + CUT_EDGE < c < s + secs - CUT_EDGE for c in _cuts(f, s, secs)):
        return False
    return not _letterbox_rows(f, s, secs, info['height'])[1]


def nearest_clean(f, start, secs, info):
    """The clean start of the same length closest to `start`, from the scene starts around it and steps of 0.25 s;
    None when there is none within SEARCH s."""
    lo = max(info['picture_start'], start - SEARCH)
    hi = min(start + SEARCH, (info['duration'] or start + SEARCH + secs) - secs)
    if hi < lo:
        return None
    around = _cuts(f, lo, hi - lo + secs)
    cands = {round(c + 0.04, 2) for c in around} | {round(c - 0.04 - secs, 2) for c in around}
    k = 0.25
    while k <= SEARCH:
        cands |= {round(start + k, 2), round(start - k, 2)}
        k += 0.25
    cands.add(round(max(info['picture_start'], lo), 2))
    for s in sorted((c for c in cands if lo <= c <= hi), key=lambda c: abs(c - start))[:40]:
        if _clean(f, s, secs, info):
            return s
    return None


def _shot_rows(job, shots):
    """[(index, file, start, secs, focus)] for the footage shots (not stills, not our cards)."""
    out = []
    for i, sh in enumerate(shots):
        f, st, secs, fo = sh[0], sh[1], sh[2], (sh[3] if len(sh) > 3 else None)
        if st is None or isinstance(st, list) or not isinstance(f, str):
            continue
        if f.endswith(STILL) or '-gfx-' in f or f.startswith('numgfx'):
            continue
        if not os.path.exists(_U() + f):
            continue
        out.append((i, f, float(st), float(secs), fo))
    return out


def timing_problems(job, shots):
    """Item B: picture start, scene cuts and letterbox per shot, read on the server's copy."""
    out, infos = [], {}
    for i, f, st, secs, _fo in _shot_rows(job, shots):
        info = infos.setdefault(f, read(f))
        why = []
        if st < info['picture_start'] - PIC_TOL:
            why.append(f"starts at {st:.2f} s, before the picture on the server's copy ({info['picture_start']:.2f} s)")
        cut = [c for c in _cuts(f, st, secs) if st + CUT_EDGE < c < st + secs - CUT_EDGE]
        if cut and not _waived(job, 'cut_ok', f, st):
            why.append(f"crosses the trailer's scene cut at {cut[0]:.2f} s (shot {st:.2f} to {st + secs:.2f} s; "
                       f"up to the cut it holds {cut[0] - st - 0.04:.2f} s)")
        rows, boxed = _letterbox_rows(f, st, secs, info['height'])
        if boxed and not (_waived(job, 'letterbox_ok', f, st) or job.get('lowres_ok')):
            why.append(f'is letterboxed on this stretch ({rows} of {info["height"]} rows of picture)')
        if why:
            s = nearest_clean(f, st, secs, info)
            nxt = (f'nearest clean start {s:.2f} s for the same {secs:.2f} s' if s is not None else
                   f'no clean start of {secs:.2f} s within {SEARCH:.0f} s: pick another stretch or shorten the shot')
            out.append({'where': f'shot {i}', 'rule': 'shot_timing', 'file': f, 'start': st, 'secs': secs,
                        'detail': f'shot {i} ({f} {st:.2f} s): ' + '; '.join(why) + f'; {nxt}', 'clean_start': s,
                        'cut_at': round(cut[0], 3) if cut and not _waived(job, 'cut_ok', f, st) else None,
                        'picture_start': info['picture_start'], 'duration': info['duration']})
    return out, infos


def _frame(f, t, bars, path_out):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{max(0.0, t):.3f}', '-i', _U() + f,
                    '-frames:v', '1', '-vf', f'{bars}scale=640:-2', path_out], check=True)


def detect_boxes(paths):
    """[[x1, x2, y1, y2, class] in shares of the frame] per image, or None when the detector cannot run."""
    import reel
    if not paths:
        return []
    env = dict(os.environ)
    if os.path.isdir(reel.YOLO_LIBS):
        env['PYTHONPATH'] = reel.YOLO_LIBS + os.pathsep + env.get('PYTHONPATH', '')
    try:
        r = subprocess.run([sys.executable, '-c', _BOXES_PY, reel.YOLO_WEIGHTS, str(reel.SUBJECT_CLASSES).replace(' ', '')]
                           + list(paths), capture_output=True, text=True, env=env, check=True)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith('@@')][-1]
        return json.loads(line[2:])
    except Exception as e:                                     # noqa: BLE001
        why = (getattr(e, 'stderr', '') or str(e)).strip().splitlines()[-1:] or ['?']
        print(f'shotgate: subject detector unavailable ({why[0][:160]}); drift not checked', flush=True)
        return None


def _window(fo, off, secs, iw, rows):
    """(left, right) of the 9:16 window as shares of the picture at `off` s into the shot."""
    import reel
    x = reel._fo_at(_focus(fo), off, secs) if fo is not None else 0.5
    sw = iw * reel.H / max(rows, 1)
    share = min(1.0, reel.W / sw)
    left = float(x) * (1 - share)
    return left, left + share


def _focus(fo):
    if isinstance(fo, list) and fo and isinstance(fo[0], (list, tuple)):
        return [tuple(k) for k in fo]
    return fo


def _inside(box, win):
    x1, x2 = box[0], box[1]
    ov = max(0.0, min(x2, win[1]) - max(x1, win[0]))
    return ov / max(1e-6, min(x2 - x1, win[1] - win[0]))


def _area(b):
    return (b[1] - b[0]) * (b[3] - b[2])


def _follow(prev, boxes):
    """The box in `boxes` that continues `prev`: same class, nearest centre."""
    same = [b for b in boxes if b[4] == prev[4]] or boxes
    if not same:
        return None
    cx = (prev[0] + prev[1]) / 2
    return min(same, key=lambda b: abs((b[0] + b[1]) / 2 - cx))


def drift_problems(job, shots):
    """Item C: the subject at the start, middle and end of each shot against the window the shot uses."""
    import reel
    rows_ = [r for r in _shot_rows(job, shots) if not _waived(job, 'drift_ok', r[1], r[2])]
    if not rows_:
        return []
    tmp = tempfile.mkdtemp(prefix='shotgate-')
    try:
        plan, paths, geo = [], [], {}
        for i, f, st, secs, fo in rows_:
            if f not in geo:
                _w, h, _v0, _d = _probe(_U() + f)
                crop, rows = reel._bars(_U() + f, st, secs)
                iw = int(crop.split('crop=')[1].split(':')[0]) if crop else _w
                geo[f] = (crop, iw, rows or h)
            for k, q in enumerate((0.1, secs / 2, max(0.1, secs - 0.1))):
                p = f'{tmp}/{i}-{k}.png'
                _frame(f, st + q, geo[f][0], p)
                plan.append((i, q)); paths.append(p)
        found = detect_boxes(paths)
        if found is None:
            return []
        by = {}
        for (i, q), bs in zip(plan, found):
            by.setdefault(i, []).append((q, bs))
        out = []
        for i, f, st, secs, fo in rows_:
            samples = by.get(i) or []
            if not samples or not samples[0][1]:
                continue
            _crop, iw, rows = geo[f]
            win0 = _window(fo, samples[0][0], secs, iw, rows)
            big = [b for b in samples[0][1] if _area(b) >= SUBJECT_MIN]
            if not big:
                continue
            framed = [b for b in big if _inside(b, win0) >= DRIFT_INSIDE]
            # the subject is the one the window frames (Ranger's Path v3, 15 Nov: the window held the ranger in the
            # middle while a larger foreground ranger stood at its edge); only when it frames none is the largest one cut
            subj = max(framed or big, key=_area)
            first_in = _inside(subj, win0)
            if first_in < AIMED_ELSEWHERE:
                continue                                       # the window aims at something else: not this subject
            track, tp = [[round(samples[0][0], 2), round(subj[0], 4), round(subj[1], 4)]], subj
            for q, bs in samples[1:]:                          # where the subject is at each sample, for the autofix
                b = _follow(tp, bs)                            # (adv-20261117-gates-fix-not-refuse B)
                if b is not None:
                    track.append([round(q, 2), round(b[0], 4), round(b[1], 4)]); tp = b
            geo_fix = {'share': round(win0[1] - win0[0], 4), 'track': track, 'secs': secs, 'focus': fo}
            if first_in < DRIFT_INSIDE and _area(subj) >= CUT_MIN:
                out.append({**geo_fix, 'where': f'shot {i}', 'rule': 'subject_cut', 'file': f, 'start': st,
                            'detail': f'shot {i} ({f} {st:.2f} s): the subject is cut by the 9:16 edge from the first '
                                      f'frame ({first_in:.0%} of it inside the window); reframe it (focus) or pick a shot '
                                      'with the subject centred, or waive with drift_ok after looking'})
                continue
            prev, last_in, out_at = subj, samples[0][0], None
            for q, bs in samples[1:]:
                b = _follow(prev, bs)
                if b is None:
                    continue
                if _inside(b, _window(fo, q, secs, iw, rows)) < DRIFT_INSIDE:
                    out_at = q
                    break
                prev, last_in = b, q
            if out_at is None:
                continue
            fine, ts = [], []                                  # where between last_in and out_at it leaves
            t = last_in + SAMPLE_STEP
            while t < out_at:
                p = f'{tmp}/{i}-f{len(ts)}.png'
                _frame(f, st + t, geo[f][0], p)
                fine.append(p); ts.append(t)
                t += SAMPLE_STEP
            leave = out_at
            for t, bs in zip(ts, detect_boxes(fine) or []):
                b = _follow(prev, bs)
                if b is not None and _inside(b, _window(fo, t, secs, iw, rows)) < DRIFT_INSIDE:
                    leave = t
                    break
                if b is not None:
                    prev = b
            safe = max(0.0, leave - 0.1)
            out.append({**geo_fix, 'where': f'shot {i}', 'rule': 'subject_drift', 'file': f, 'start': st, 'safe_secs': round(safe, 2),
                        'detail': f'shot {i} ({f} {st:.2f} s): the subject leaves the 9:16 crop at {st + leave:.2f} s '
                                  f'({leave:.2f} s into the shot); longest safe length {safe:.2f} s, or reframe it '
                                  '(focus keyframes), or waive with drift_ok after looking'})
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def stylised(job):
    """True for stylised and cartoon games (monsters, mascots, anime, Nintendo), where YOLOv8n's person, vehicle and
    animal classes see no subject: "stylised": true/false in the job decides; else its genre or the game's name."""
    if isinstance(job.get('stylised'), bool):
        return job['stylised']
    g = job.get('genre')
    gs = {str(x).lower() for x in (g if isinstance(g, list) else [g]) if x}
    if gs & STYLISED_GENRES:
        return True
    name = ' '.join(str(job.get(k) or '') for k in ('game', 'game_key', 'game_short', 'name')).lower()
    return any(w in name for w in STYLISED_WORDS)


def _grey_small(path):
    from PIL import Image
    return Image.open(path).convert('L').resize((160, 90))


def _motion(a, b):
    import numpy as np
    return float(np.abs(np.asarray(_grey_small(a), dtype=float) - np.asarray(_grey_small(b), dtype=float)).mean())


def _edge_words(path, win):
    """Words (HUD numbers included) whose box crosses an edge of the window, read with tesseract on the full frame;
    None without tesseract."""
    import reel
    from PIL import Image
    im = Image.open(path).convert('RGB')
    w, h = im.size
    boxes = reel._word_boxes(im, TEXT_CONF, letters=1)
    if boxes is None:
        return None
    x0, x1 = win[0] * w, win[1] * w
    return [wd for wd, l, t, r, b in boxes if (b - t) >= TEXT_MIN_H * h and any(ch.isalnum() for ch in wd)
            and (l < x0 < r or l < x1 < r)]


def frame_problems(job, shots):
    """The crop fix (Mohammad, 26 Nov 2026), per footage shot, on three frames (start, middle, end) of the window the
    shot uses: subject_unseen (a stylised game where the detector sees no subject: the showcase, not a saliency guess),
    subject_empty (no person, vehicle or animal inside the window: ground, sky or wall), subject_text_cut (HUD or
    on-screen text crossing the window edge) and shot_long (over LONG_MAX s unless it moves and the subject stays in).
    Inside the showcase layout only shot_long applies. Waiver after a look: "frame_ok": [[file, start, reason]]."""
    all_rows, seen_at = [], set()
    for r in _shot_rows(job, shots):        # a repeated (file, start) is a placeholder render_job.respread moves later:
        if _waived(job, 'frame_ok', r[1], r[2]) or (r[1], round(r[2], 2)) in seen_at:   # judge each moment once
            continue
        seen_at.add((r[1], round(r[2], 2)))
        all_rows.append(r)
    if not all_rows:
        return []
    boxed = job.get('layout') == 'showcase'
    sty = stylised(job)
    key = lambda r: (r[1], round(r[2], 2), round(r[3], 2), json.dumps(r[4]), boxed, sty)
    rows_ = [r for r in all_rows if key(r) not in _FP_CACHE]   # each shot is read once per process (autofix re-asks)
    if rows_:
        for r, probs in zip(rows_, _frame_read(job, rows_, boxed, sty)):
            _FP_CACHE[key(r)] = probs
    out = []
    for r in all_rows:
        for p in _FP_CACHE[key(r)]:
            d = dict(p)
            d['where'] = f'shot {r[0]}'
            d['detail'] = f'shot {r[0]} ' + d['detail']
            out.append(d)
    return out


_FP_CACHE = {}


def _frame_read(job, rows_, boxed, sty):
    """frame_problems' reading for `rows_`: one list of problems (without 'where') per row, in order."""
    if sty and not boxed:                              # stylised art: the detector cannot see it; render_job.scan moves the
        return [[{'rule': 'subject_unseen', 'file': f, 'start': st, 'secs': secs, 'focus': fo,   # Reel to the showcase
                  'detail': f'({f} {st:.2f} s): stylised art, the detector sees no subject to frame; the 16:9 showcase '
                            'rather than a saliency guess (crop fix, 26 Nov 2026)'}] for i, f, st, secs, fo in rows_]
    tmp = tempfile.mkdtemp(prefix='framecheck-')
    try:
        import reel
        plan, paths, geo = [], [], {}
        for i, f, st, secs, fo in rows_:
            if f not in geo:
                _w, h, _v0, _d = _probe(_U() + f)
                crop, rows = reel._bars(_U() + f, st, secs)
                iw = int(crop.split('crop=')[1].split(':')[0]) if crop else _w
                geo[f] = (crop, iw, rows or h)
            for k, q in enumerate((0.1, secs / 2, max(0.1, secs - 0.1))):
                p = f'{tmp}/{i}-{k}.png'
                _frame(f, st + q, geo[f][0], p)
                plan.append((i, q)); paths.append(p)
        found = None if boxed else detect_boxes(paths)
        by = {}
        for n, (i, q) in enumerate(plan):
            by.setdefault(i, []).append((q, paths[n], (found[n] if found is not None else None)))
        res = []
        for i, f, st, secs, fo in rows_:
            out = []
            res.append(out)
            smp = by.get(i) or []
            if len(smp) < 3:
                continue
            _crop, iw, rows = geo[f]
            wins = [_window(fo, q, secs, iw, rows) for q, _p, _b in smp]
            seen = [None if bs is None else [b for b in bs if _area(b) >= SUBJECT_MIN] for _q, _p, bs in smp]
            inside = [None if s is None else any(_inside(b, w) >= DRIFT_INSIDE for b in s) for s, w in zip(seen, wins)]
            base = {'file': f, 'start': st, 'secs': secs, 'focus': fo}
            if not boxed and found is not None:
                if inside[1] is False and not any(inside):
                    out.append({**base, 'rule': 'subject_empty',
                                'detail': f'({f} {st:.2f} s): no character, creature, face or vehicle inside the '
                                          '9:16 window (ground, sky or wall); re-aim or another stretch (crop fix)'})
                    continue
            if not boxed:
                cut = _edge_words(smp[1][1], wins[1])
                if cut:
                    out.append({**base, 'rule': 'subject_text_cut',
                                'detail': f'({f} {st:.2f} s): on-screen text cut by the 9:16 edge '
                                          f'({" ".join(cut[:4])}); re-aim or another stretch (crop fix)'})
                    continue
            if secs > LONG_MAX + 0.05:
                moving = _motion(smp[0][1], smp[2][1]) >= MOTION_MIN
                held = boxed or (found is not None and all(x for x in inside))
                if not (moving and held):
                    out.append({**base, 'rule': 'shot_long', 'safe_secs': LONG_MAX,
                                'detail': f'({f} {st:.2f} s): {secs:.2f} s on one shot, over {LONG_MAX:.0f} s '
                                          + ('without movement' if not moving else 'and the subject is not held in the '
                                             'window throughout') + f'; trimmed to {LONG_MAX:.1f} s (crop fix)'})
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ground_pick(f, start, span, secs, t0=0.0):
    """Item D: the calmest window of `secs` in [start, start + span] of `f` (motion plus contrast on the 9:16 centre the
    footage ground shows, at GROUND_FPS). Returns (seek, its score, the score of the seek as written (start + t0))."""
    import numpy as np
    info = read(f)
    lo = max(start, info['picture_start'])
    hi = min(start + span, info['duration'] or start + span)
    if hi - lo < secs + 0.2:
        return start + t0, None, None
    w, h = 36, 64
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{lo:.3f}', '-t', f'{hi - lo:.3f}', '-i', _U() + f,
                        '-an', '-vf', f'fps={GROUND_FPS},scale=-2:{h * 4},crop={w * 4}:{h * 4},scale={w}:{h},format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True)
    n = len(r.stdout) // (w * h)
    if n < 3:
        return start + t0, None, None
    fr = np.frombuffer(r.stdout[:n * w * h], np.uint8).reshape(n, h, w).astype(float)
    motion = np.r_[0, np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))]
    contrast = fr.std(axis=(1, 2))
    busy = motion * 2.0 + contrast * 0.5
    k = max(1, int(round(secs * GROUND_FPS)))
    if n <= k:
        return start + t0, None, None
    win = np.convolve(busy, np.ones(k) / k, mode='valid')
    best = int(np.argmin(win))
    named = int(round((start + t0 - lo) * GROUND_FPS))
    named_score = float(win[named]) if 0 <= named < len(win) else None
    return round(lo + best / GROUND_FPS, 2), round(float(win[best]), 1), (round(named_score, 1) if named_score is not None else None)


def problems(job, shots):
    """Every B and C problem for the job's footage shots (as reel takes them: [file, start, secs, focus])."""
    if job.get('kind') in ('famitsu', 'breaking') or job.get('profile') == 'breaking':
        return []
    tp, _ = timing_problems(job, shots)
    return tp + drift_problems(job, shots) + frame_problems(job, shots)


def enforce(job, shots):
    p = problems(job, shots)
    for x in p:
        print('shotgate: ' + x['detail'], flush=True)
    if p:
        print('SHOTGATE_JSON: ' + json.dumps({'job': job.get('name'), 'ok': False, 'problems': p}, ensure_ascii=False),
              flush=True)
        raise SystemExit(f'shotgate: {len(p)} shot problem{"s" if len(p) > 1 else ""} on the server copy (above); '
                         'fix the shot list before the render (adv-20261115-one-render-server-checks)')
    print('shotgate: shots clean on the server copy (picture start, scene cuts, letterbox, subject drift)', flush=True)


def main(argv):
    if len(argv) < 2 or argv[0] not in ('job', 'read'):
        raise SystemExit(__doc__)
    if argv[0] == 'read':
        print(json.dumps(read(argv[1])))
        return 0
    import render_job as RJ
    job = json.load(open(argv[1], encoding='utf-8'))
    for item in job.get('footage', []):
        RJ.fetch(item)
    p = problems(job, job.get('shots') or [])
    for x in p:
        print('shotgate: ' + x['detail'])
    print('SHOTGATE_JSON: ' + json.dumps({'job': job.get('name'), 'ok': not p, 'problems': p}, ensure_ascii=False))
    return 1 if p else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
