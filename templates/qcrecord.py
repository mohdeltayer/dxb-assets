#!/usr/bin/env python3
"""QC bound to the file (adv-20261030-promise-keeper, addendum_2251 item D, Mohammad 30 Oct 2026).

A pass is a record, not a sentence. The record carries the hashes of exactly what was checked: the video file, the
text (on-screen text from the job, and the post text once bound), the asset manifest (the job and its sources), the
template revision (the render code) and the rules revision (STYLE.md and the thresholds below). Any edit to the video,
the text or the assets invalidates it; a change of template or rules makes it stale (run `make` again, no re-render).
A prose "director passed" cannot authorise scheduling: only `gate` on a valid PASS record can.

The checks run on decoded frames at shot boundaries and at text changes (from the job's timeline; without a job, at
scene cuts and once a second), never on the end card. Two composition profiles, measured on the active, unblurred
footage (blurred fill and the source's own borders excluded):

  portrait_crop   footage at least 55% of the canvas area and 90% of its width (text may sit on the picture)
  wide_preserve   footage at least 95% of the width and 28% of the area, text rails above and below, and our text
                  never inside the footage rectangle

Gate results:
  PASS      every footage shot meets the profile
  REPAIR    it does not, and one bounded automatic repair is named: `profile:wide_preserve` (the layout already meets
            wide_preserve: QC again with that profile, no re-render), `text_to_rails` (wide_preserve with our text on
            the picture: re-render with the lines in the rails), `crop_borders` (the source's own black bars inside the
            frame: re-render with the bars cropped). The repaired file is QC'd once more with --attempt 2; a second
            failure is FALLBACK, never a second repair.
  FALLBACK  the file does not pass and no repair applies (or the repair was tried): the commitment's fallback runs
  REJECT    the file must never post: decode errors, or footage in a blurred fill of itself

    python3 templates/qcrecord.py make <video> [--job J] [--text T] [--profile P] [--attempt N] [--out R]
    python3 templates/qcrecord.py verify <record> [--video V] [--job J] [--text T]
    python3 templates/qcrecord.py gate <record> --video V [--job J] [--text T]    exit 0 only on a valid PASS
    python3 templates/qcrecord.py bind <record> --video V --text T                 add the post text after the render
    python3 templates/qcrecord.py measure <video> [t ...]                          one frame's reading (debug)

`--text` is the post text as a JSON object (caption, x, threads, title...) or a plain text file. `gate` prints one
JSON line for the commitments row's `qc` field, which is how the keeper tells a bound pass from a claimed one.
Exit codes: 0 PASS and valid; 3 REPAIR; 4 FALLBACK; 5 REJECT; 6 invalid or stale record; 2 usage or unreadable input.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SCHEMA = 'dxb-qc/1'
RULES = {
    'version': 'qc-2026-10-31.1',
    'profiles': {
        'portrait_crop': {'area_min': 0.55, 'width_min': 0.90, 'text_on_footage': True},
        'wide_preserve': {'area_min': 0.28, 'width_min': 0.95, 'text_on_footage': False},
    },
    'blur_max': 0.05,          # blurred fill outside the footage, share of the canvas (as fillcheck.BLUR_MAX)
    'endcard_secs': 2.3,       # outro.CARD plus the body's fade: never measured
    'crossfade': 0.4,          # reel.X: a boundary sample sits just after the crossfade
}
PROFILES = RULES['profiles']
RESULTS = ('PASS', 'REPAIR', 'FALLBACK', 'REJECT')
EXIT = {'PASS': 0, 'REPAIR': 3, 'FALLBACK': 4, 'REJECT': 5}

W, H, C = 540, 960, 20          # frames read at half of 1080x1920, in 20 px cells (27 x 48)
DETAIL = 3.0                    # mean step between neighbouring pixels above this: detail (footage or type)
MODE_FRAC = 0.6                 # a detailed cell whose pixels mostly share one level: type on a flat ground
BLUR_DX = 8.0                   # a smooth cell whose colour drifts sideways from its neighbours: a blur, not a band
BAND_BLUR, BAND_FOOT = 0.10, 0.15  # a part of the frame under these shares of blur and footage cells is a designed band
BAND_LUM, GROUND_BLUE = 170, 10 # our grounds: no brighter than 170, blue at least 10 over red (indigo, theme washes)
COPY_CORR, COPY_MIN_PX = 0.6, 200  # a part correlating at 0.6 with a fill made from the footage is a blurred copy;
COPY_LOOSE, COPY_BLUR, COPY_DETAIL = 0.25, 0.15, 0.35  # at 0.25 when it is a blur (blur cells, little detail)
INK_MIN, INK_SPREAD = 225, 24   # our type: near-white ink ...
EDGE_MAX, EDGE_NEAR = 70, 3     # ... with an indigo outline or ground within 3 px
TEXT_ROW_PX = 30                # two 20 px bands of rows each holding 30 or more ink pixels inside the footage: a line
BAR_LUM = 18                    # the source's own black bars
EDGE_STEP, EDGE_SPAN = 18, 0.35 # a straight edge: a run over 35% of a row stepping by more than 18 levels


# ---------------------------------------------------------------------------------------------
# Hashes
# ---------------------------------------------------------------------------------------------
def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def sha_json(obj):
    return sha_bytes(canon(obj).encode('utf-8'))


def _norm_text(s):
    return re.sub(r'[ \t]+', ' ', str(s)).strip()


def screen_text(job):
    """Every string the Reel draws, from the job (headline, label, lines, credits, strip, person plates, inserts)."""
    if not job:
        return None
    out = {}
    for k in ('headline', 'label', 'source', 'date', 'country'):
        if job.get(k) is not None:
            out[k] = _norm_text(job[k])
    if job.get('lines'):
        out['lines'] = [[a, b, [_norm_text(x[0] if isinstance(x, list) else x) for x in texts]]
                        for a, b, texts in job['lines']]
    if job.get('credits'):
        out['credits'] = [[c[0], c[1], _norm_text(c[2])] for c in job['credits'] if len(c) >= 3]
    for k in ('strip', 'insert', 'frame'):
        if job.get(k):
            out[k] = job[k]
    if job.get('person'):
        out['person'] = [[_norm_text(p[1]), _norm_text(p[2])] for p in job['person'] if len(p) >= 3]
    return out


def post_text(path):
    """The post text (caption, X, Threads, title): a JSON object, or a plain text file taken as one field."""
    if not path:
        return None
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    try:
        obj = json.loads(raw)
    except ValueError:
        return {'text': _norm_text(raw)}
    if isinstance(obj, dict):
        return {k: (_norm_text(v) if isinstance(v, str) else v) for k, v in obj.items()}
    return {'text': obj}


def text_hashes(job, post):
    scr = screen_text(job)
    s = sha_json(scr) if scr is not None else None
    p = sha_json(post) if post is not None else None
    return {'screen_sha256': s, 'post_sha256': p, 'sha256': sha_json([s, p])}


VOLATILE = ('note',)            # prose about the job, not what renders


def manifest(job, uploads=None):
    """The job (minus prose) and every source it names, with the local file's hash when the file is at hand."""
    if not job:
        return {'sha256': None, 'job_sha256': None, 'assets': []}
    uploads = uploads or os.environ.get('DXB_UPLOADS') or ''
    names = []
    for item in job.get('footage') or []:
        if isinstance(item, dict):
            ident = {k: item[k] for k in sorted(item) if k in ('file', 'url', 'steam', 'trailer', 'ign', 'nintendo',
                                                               'start', 'secs', 'repo')}
            names.append(ident)
    for sh in job.get('shots') or []:
        if sh and isinstance(sh[0], str) and not any(n.get('file') == sh[0] for n in names):
            names.append({'file': sh[0]})
    for p in job.get('person') or []:
        if p and isinstance(p[0], str):
            names.append({'file': p[0], 'role': 'person'})
    assets = []
    for n in names:
        a = dict(n)
        f = n.get('file')
        path = os.path.join(uploads, f) if (f and uploads) else None
        if path and os.path.isfile(path):
            a['sha256'] = sha_file(path)
        assets.append(a)
    jsha = sha_json({k: v for k, v in job.items() if k not in VOLATILE})
    # the asset hashes are recorded when the files are at hand (the runner), but the binding uses the job and the
    # source identities only, so verify gives the same answer on a session that has the job but not the footage
    ident = [{k: v for k, v in a.items() if k != 'sha256'} for a in assets]
    return {'sha256': sha_json([jsha, ident]), 'job_sha256': jsha, 'assets': assets}


def _git(*args):
    try:
        return subprocess.run(['git', '-C', ROOT] + list(args), capture_output=True, text=True,
                              timeout=20).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def template_rev():
    """The render code: every .py in templates/ and the web-motion and HyperFrames sources, by content."""
    files = []
    for base, dirs, names in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', 'assets', 'fonts', 'voice_stubs')]
        for n in names:
            if n.endswith(('.py', '.html', '.css', '.js', '.mjs')):
                files.append(os.path.join(base, n))
    h = hashlib.sha256()
    for p in sorted(files):
        h.update(os.path.relpath(p, HERE).encode() + b'\0' + sha_file(p).encode() + b'\n')
    return {'sha256': h.hexdigest(), 'git': _git('rev-parse', '--short=12', 'HEAD')}


def rules_rev():
    """STYLE.md (the rules in force) and this module's thresholds."""
    style = os.path.join(ROOT, 'STYLE.md')
    s = sha_file(style) if os.path.isfile(style) else None
    return {'sha256': sha_json([s, RULES]), 'style_sha256': s, 'version': RULES['version']}


def binding(rec):
    """One digest over what the record vouches for: hand-editing its result or any hash breaks it."""
    keys = [rec.get('result'), rec.get('profile'), rec.get('attempt'), rec['video'].get('sha256'),
            rec['text'].get('sha256'), rec['manifest'].get('sha256'), rec['template_rev'].get('sha256'),
            rec['rules_rev'].get('sha256')]
    return sha_json(keys)


# ---------------------------------------------------------------------------------------------
# Frames
# ---------------------------------------------------------------------------------------------
def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height:format=duration', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    st = (d.get('streams') or [{}])[0]
    return int(st.get('width', 0)), int(st.get('height', 0)), float(d.get('format', {}).get('duration') or 0)


def frame(path, t):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0.0, t):.3f}', '-i', path, '-frames:v', '1',
                          '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    if len(raw) < W * H * 3:
        return None
    return np.frombuffer(raw[:W * H * 3], np.uint8).reshape(H, W, 3).astype(np.float32)


def cells(rgb):
    """Per cell: 'f' detail with spread (footage), 't' type on a flat ground, 'b' a blur (smooth, its colour drifting
    sideways from its neighbours), '.' flat (a designed band, a bar, a dark patch). Also each cell's mean colour."""
    import numpy as np
    g = rgb.mean(axis=2)
    gx = np.abs(np.diff(g, axis=1))
    gy = np.abs(np.diff(g, axis=0))
    R, K = H // C, W // C
    mean = rgb.reshape(R, C, K, C, 3).mean(axis=(1, 3))
    det = np.zeros((R, K))
    for r in range(R):
        for k in range(K):
            det[r, k] = (gx[r * C:(r + 1) * C, k * C:(k + 1) * C - 1].mean()
                         + gy[r * C:(r + 1) * C - 1, k * C:(k + 1) * C].mean()) / 2
    smooth = det <= DETAIL
    pair = smooth[:, :-1] & smooth[:, 1:]                       # drift is read between two smooth cells only, so
    dx = np.abs(np.diff(mean, axis=1)).sum(axis=2) * pair       # type beside a band never reads as a blur
    cnt = np.zeros((R, K))
    drift = np.zeros((R, K))
    drift[:, :-1] += dx
    drift[:, 1:] += dx
    cnt[:, :-1] += pair
    cnt[:, 1:] += pair
    drift = np.where(cnt > 0, drift / np.maximum(cnt, 1), 0.0)
    out = np.full((R, K), '.', dtype='<U1')
    for r in range(R):
        for k in range(K):
            ys, xs = slice(r * C, (r + 1) * C), slice(k * C, (k + 1) * C)
            cell = g[ys, xs]
            if det[r, k] > DETAIL:
                mf = float((np.abs(cell - np.median(cell)) <= 6).mean())
                out[r, k] = 't' if mf >= MODE_FRAC else 'f'
            elif drift[r, k] > BLUR_DX:
                out[r, k] = 'b'
    return out, mean


def _edges(g, axis, span):
    """Straight edges across the picture: for axis 0, rows y where a run of columns stepping sharply to the next row
    covers at least `span` of the width (the top or bottom of a box or a band). Returns positions in pixels. A run,
    not a total: textured footage steps in scattered columns on many rows, and cutting there split real shots."""
    import numpy as np
    step = np.abs(np.diff(g, axis=axis)) > EDGE_STEP
    if axis == 1:
        step = step.T
    n = step.shape[1]
    out = []
    for y in np.nonzero(step.mean(axis=1) >= span)[0]:
        best = run = 0
        for v in step[y]:
            run = run + 1 if v else 0
            best = max(best, run)
        if best >= span * n:
            out.append(int(y) + 1)
    return out


def _segments(cuts, n, minlen):
    pts = [0] + [c for c in cuts if 0 < c < n] + [n]
    segs = []
    for a, b in zip(pts, pts[1:]):
        if b - a >= minlen:
            segs.append((a, b))
    return segs


def _is_band(c, ground):
    """A part of the frame that is nearly all flat cells and type on one of our grounds: a designed band, a rail, or
    the source's own black bar. A flat part in any other colour (a white seamless, the grey face of a console) is
    picture."""
    return bool(ground) and float((c == 'b').mean()) < BAND_BLUR and float((c == 'f').mean()) < BAND_FOOT


def _ground(px, rails=True):
    """Is this the colour of a ground we design or a black bar? Our grounds are the indigo and the theme washes (blue
    over red, never brighter than BAND_LUM); a black bar is dark in any tint. Beside the footage (rails=False) only
    black bars count: our layouts put bands above and below it, never at its sides."""
    import numpy as np
    r, g, b = [float(np.median(px[..., i])) for i in range(3)]
    lum = (r + g + b) / 3
    if lum <= BAR_LUM:
        return True
    return rails and lum <= BAND_LUM and b - r >= GROUND_BLUE


def copy_corr(rgb, core, other):
    """How closely `other` (x0, y0, x1, y1) matches a blurred fill made from the picture in `core`: the core scaled to
    cover the canvas about its centre, as a fill is made, then compared on luminance at low resolution (a dimmed fill
    still correlates). Under COPY_MIN_PX pixels to compare: 0 (too small to call)."""
    import numpy as np
    from PIL import Image, ImageFilter
    x0, y0, x1, y1 = core
    bw, bh = x1 - x0, y1 - y0
    if bw < C or bh < C:
        return 0.0
    s = max(W / float(bw), H / float(bh))
    im = Image.fromarray(rgb[y0:y1, x0:x1].astype(np.uint8)).convert('L')
    big = im.resize((max(W, int(round(bw * s))), max(H, int(round(bh * s)))), Image.BILINEAR)
    left, top = (big.width - W) // 2, (big.height - H) // 2
    synth = big.crop((left, top, left + W, top + H))
    q = 4                                                    # compare at a quarter, both softened alike
    sm = lambda img: np.asarray(img.resize((W // q, H // q), Image.BOX).filter(ImageFilter.GaussianBlur(3)),
                                np.float32)
    a = sm(synth)
    b = sm(Image.fromarray(rgb.astype(np.uint8)).convert('L'))
    ox0, oy0, ox1, oy1 = [v // q for v in other]
    a, b = a[oy0:oy1, ox0:ox1].ravel(), b[oy0:oy1, ox0:ox1].ravel()
    if a.size < COPY_MIN_PX or a.std() < 1 or b.std() < 1:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def is_copy(corr, core_detail, detail, blur):
    """A blurred copy of the footage: it matches a fill made from the footage closely, or it matches loosely and looks
    like a blur (its colour drifting with almost no detail, far less than the footage's)."""
    if corr >= COPY_CORR:
        return True
    return corr >= COPY_LOOSE and blur >= COPY_BLUR and detail <= COPY_DETAIL * max(core_detail, 1e-6)


def _footage_span(segs, cls, box, rgb):
    """The footage among the parts of a frame, and the parts that are a blurred copy of it.

    segs are (start, end) along one axis, cls(seg) the cell classes of a part, box(start, end) its rectangle. A part is
    a designed band or picture. The most detailed picture part is the core; a touching picture part joins it unless it
    is a blurred copy of the core (copy_corr at least COPY_CORR): a soft sky over a city joins, the blur of a boxed
    clip does not. Returns (start, end, copies) or None."""
    parts, blurs = [], {}
    for s in segs:
        c, ground = cls(s)
        parts.append((s, float((c == 'f').mean()), len(segs) == 1 or not _is_band(c, ground)))
        blurs[s] = float((c == 'b').mean())
    if not any(p[2] for p in parts):
        return None
    core = max(range(len(parts)), key=lambda i: (parts[i][2], parts[i][1]))
    cbox = box(*parts[core][0])
    lo = hi = core
    copies = []

    def copy(j):
        return is_copy(copy_corr(rgb, cbox, box(*parts[j][0])), parts[core][1], parts[j][1], blurs[parts[j][0]])

    def ok(j, k):
        if not parts[j][2] or abs(parts[j][0][0] - parts[k][0][1]) > 2 * C and abs(parts[k][0][0] - parts[j][0][1]) > 2 * C:
            return False
        if copy(j):
            copies.append(parts[j][0])
            return False
        return True
    while lo > 0 and ok(lo - 1, lo):
        lo -= 1
    while hi < len(parts) - 1 and ok(hi + 1, hi):
        hi += 1
    for j, p in enumerate(parts):                            # copies beyond a band (a box between rails in a blur)
        if (j < lo - 1 or j > hi + 1) and p[2] and p[0] not in copies and copy(j):
            copies.append(p[0])
    return parts[lo][0][0], parts[hi][0][1], copies


def ink(rgb):
    """Pixels of our type: near-white with an indigo outline or ground within EDGE_NEAR pixels."""
    import numpy as np
    lum = rgb.mean(axis=2)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    white = (rgb.min(axis=2) >= INK_MIN) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= INK_SPREAD)
    dark = (lum <= EDGE_MAX) & (B >= R + 12) & (B >= G + 10)
    near = np.zeros_like(dark)
    n = EDGE_NEAR
    pad = np.pad(dark, n)
    for dy in range(-n, n + 1):
        for dx in range(-n, n + 1):
            near |= pad[n + dy:n + dy + H, n + dx:n + dx + W]
    return white & near


def measure(rgb):
    """One frame: the footage rectangle (canvas fractions), its area and width, the share of the canvas that is a
    blurred copy of it, our type inside it, and black bars along it.

    The picture is cut at straight edges (the top and bottom of a band or a box, the sides of a box). With no such
    edge the whole frame is one part and all footage, however soft or dark it is."""
    import numpy as np
    cl, mean = cells(rgb)
    R, K = cl.shape
    g = rgb.mean(axis=2)
    cpx = np.repeat(np.repeat(cl, C, axis=0), C, axis=1)         # cell classes at pixel resolution
    rows = _footage_span(_segments(_edges(g, 0, EDGE_SPAN), H, 2 * C), lambda s: (cpx[s[0]:s[1]], _ground(rgb[s[0]:s[1]])),
                         lambda a, b: (0, a, W, b), rgb)
    res = {'cells_footage': round(float((cl == 'f').mean()), 3)}
    if not rows:
        res.update(rect=None, area=0.0, width=0.0, height=0.0, blur=0.0, text_px=0, text_on_footage=False,
                   bars=False)
        return res
    y0, y1, rcopies = rows
    cols = _footage_span(_segments(_edges(g[y0:y1], 1, EDGE_SPAN), W, 2 * C), lambda s: (cpx[y0:y1, s[0]:s[1]], _ground(rgb[y0:y1, s[0]:s[1]], False)),
                         lambda a, b: (a, y0, b, y1), rgb) or (0, W, [])
    x0, x1, ccopies = cols
    blur = (sum((b - a) * W for a, b in rcopies) + sum((b - a) * (y1 - y0) for a, b in ccopies)) / float(W * H)
    ik = ink(rgb)[y0:y1, x0:x1]
    nb = (y1 - y0) // C
    per = ik[:nb * C].reshape(nb, C, -1).sum(axis=(1, 2)) if nb else np.zeros(0)
    hot = per >= TEXT_ROW_PX
    text_on = bool(any(hot[i] and hot[i + 1] for i in range(len(hot) - 1)))   # a line of type is two bands tall
    lum = mean.mean(axis=2)
    r0, r1 = y0 // C, -(-y1 // C)
    bars = False                                                # the source's own black bars: dark flat full rows
    for rr in (range(max(0, r0 - 3), r0), range(r1, min(R, r1 + 3))):
        rr = list(rr)
        if len(rr) >= 2 and all((cl[r] == '.').all() and lum[r].max() <= BAR_LUM for r in rr):
            bars = True
    res.update(rect=[round(x0 / W, 3), round(y0 / H, 3), round((x1 - x0) / W, 3), round((y1 - y0) / H, 3)],
               area=round((y1 - y0) * (x1 - x0) / float(H * W), 3), width=round((x1 - x0) / float(W), 3),
               height=round((y1 - y0) / float(H), 3), blur=round(blur, 3), text_px=int(per.max()) if per.size else 0,
               text_on_footage=text_on, bars=bars)
    return res


# ---------------------------------------------------------------------------------------------
# Where to look: shot boundaries and text changes
# ---------------------------------------------------------------------------------------------
def _graphic(f):
    return isinstance(f, str) and ('-gfx-' in f or f.startswith('numgfx/'))


def timeline(job):
    """(shot starts, body end, shot kinds) as reel.timeline builds the cut: each shot overlaps the next by X."""
    X = RULES['crossfade']
    shots = job.get('shots') or []
    starts, t = [], 0.0
    for i, sh in enumerate(shots):
        starts.append(t if i == 0 else t)
        t += float(sh[2]) - (X if i < len(shots) - 1 else 0.0)
    kinds = ['graphic' if _graphic(sh[0]) else 'footage' for sh in shots]
    return starts, t, kinds


def line_times(job, starts, end):
    """Each line's appearance, as reel.by_shot places it (the first group waits for the head band)."""
    out = []
    for a, b, texts in job.get('lines') or []:
        if a >= len(starts):
            continue
        t0 = starts[a] + (0.25 if a else 3.6)
        t1 = starts[b + 1] if b + 1 < len(starts) else end
        span = (t1 - t0) / max(1, len(texts))
        out += [t0 + i * span for i in range(len(texts))]
    return out


def scene_cuts(path, limit=60):
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', path, '-an', '-vf',
                        "scale=270:480,select='gt(scene,0.3)',showinfo", '-f', 'null', '-'],
                       capture_output=True, text=True)
    return [float(m.group(1)) for m in re.finditer(r'pts_time:([\d.]+)', p.stderr or '')][:limit]


def samples(path, job, duration):
    """[(t, shot index or None, kind, why)] over the body only (the end card is ours and never measured)."""
    endcard = 0.0 if (job and job.get('outro') is False) else RULES['endcard_secs']
    body_end = max(0.5, duration - endcard)
    offset = 0.0
    if job and job.get('intro') is not None:
        offset = float((job.get('intro') or {}).get('secs', 4.2)) if isinstance(job.get('intro'), dict) else 4.2
    pts = []
    if job and job.get('shots'):
        starts, end, kinds = timeline(job)
        X = RULES['crossfade']
        for i, s in enumerate(starts):
            dur = float(job['shots'][i][2])
            pts.append((s + (X + 0.1 if i else 0.05), i, 'boundary'))
            pts.append((s + dur / 2.0, i, 'middle'))
        for t in line_times(job, starts, end):
            pts.append((t + 0.35, None, 'text'))
        out = []
        for t, i, why in pts:
            t += offset
            if t >= body_end:
                continue
            if i is None:                                   # the shot under a text change
                i = max([k for k, s in enumerate(starts) if s + offset <= t] or [0])
            out.append((round(t, 2), i, kinds[i] if i < len(kinds) else 'footage', why))
    else:
        cuts = [t + 0.15 for t in scene_cuts(path)]
        grid = [0.05] + [float(k) + 0.5 for k in range(int(body_end))]
        out = [(round(t, 2), None, 'footage', 'cut') for t in cuts] + [(round(t, 2), None, 'footage', 'grid')
                                                                        for t in grid]
        out = [s for s in out if s[0] < body_end]
    seen, uniq = set(), []
    for s in sorted(out):
        if s[0] not in seen:
            seen.add(s[0])
            uniq.append(s)
    return uniq


# ---------------------------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------------------------
def judge(reads, profile, attempt):
    """reads: [{'t', 'shot', 'kind', 'why', ...measure}]. Returns (result, reason, repair, shots)."""
    prof = PROFILES[profile]
    groups = {}
    for r in reads:
        key = r['shot'] if r['shot'] is not None else 'f%.2f' % r['t']
        groups.setdefault(key, []).append(r)
    shots, failing = [], []
    for key, rs in groups.items():
        if all(r['kind'] == 'graphic' for r in rs):
            shots.append({'shot': key, 'kind': 'graphic', 'verdict': 'exempt'})
            continue
        rs = [r for r in rs if r['kind'] != 'graphic']
        # a dark frame can hide part of the picture, a layout never changes inside one shot: the best footage
        # reading of the shot, the middle blur reading, and any frame with our type on the picture
        best = max(rs, key=lambda r: (r['area'], r['width']))
        blur = sorted(r['blur'] for r in rs)[len(rs) // 2]
        text = [r['t'] for r in rs if r.get('text_on_footage')]
        s = {'shot': key, 'kind': 'footage', 'area': best['area'], 'width': best['width'], 'rect': best.get('rect'),
             'blur': blur, 'text_on_footage_at': text, 'bars': any(r.get('bars') for r in rs),
             'times': [r['t'] for r in rs]}
        why = []
        if blur > RULES['blur_max']:
            why.append('blurred fill %.0f%%' % (100 * blur))
        if best['area'] < prof['area_min']:
            why.append('footage area %.0f%% < %.0f%%' % (100 * best['area'], 100 * prof['area_min']))
        if best['width'] < prof['width_min']:
            why.append('footage width %.0f%% < %.0f%%' % (100 * best['width'], 100 * prof['width_min']))
        if text and not prof['text_on_footage']:
            why.append('our text inside the footage at %s s' % ', '.join('%.2f' % t for t in text[:4]))
        s['verdict'] = 'fail' if why else 'pass'
        s['why'] = why
        shots.append(s)
        if why:
            failing.append(s)
    if any(s['kind'] == 'footage' and s['blur'] > RULES['blur_max'] for s in shots):
        bad = [s for s in shots if s['kind'] == 'footage' and s['blur'] > RULES['blur_max']]
        return 'REJECT', 'footage in a blurred fill (shot %s)' % ', '.join(str(s['shot']) for s in bad), None, shots
    if not failing:
        n = sum(1 for s in shots if s['kind'] == 'footage')
        return 'PASS', ('%d footage shots meet %s' % (n, profile)) if n else 'no footage shots: composition not ' \
                                                                               'measured', None, shots
    reason = '; '.join('shot %s: %s' % (s['shot'], ', '.join(s['why'])) for s in failing)
    if attempt >= 2:
        return 'FALLBACK', reason + ' (after the one repair)', None, shots
    wide = PROFILES['wide_preserve']
    if profile == 'portrait_crop' and all(s['width'] >= wide['width_min'] and s['area'] >= wide['area_min']
                                          and not s['text_on_footage_at'] for s in failing):
        return 'REPAIR', reason, 'profile:wide_preserve', shots
    if profile == 'wide_preserve' and all(s['width'] >= wide['width_min'] and s['area'] >= wide['area_min']
                                          for s in failing):
        return 'REPAIR', reason, 'text_to_rails', shots
    if all(s['bars'] for s in failing):
        return 'REPAIR', reason, 'crop_borders', shots
    return 'FALLBACK', reason, None, shots


def decode_errors(path):
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-f', 'null', '-'], capture_output=True,
                       text=True)
    return [l for l in (p.stderr or '').splitlines() if l.strip()]


def profile_of(job, given=None):
    if given:
        return given
    q = (job or {}).get('qc')
    if isinstance(q, str) and q in PROFILES:
        return q
    if isinstance(q, dict) and q.get('profile') in PROFILES:
        return q['profile']
    return (job or {}).get('composition') if (job or {}).get('composition') in PROFILES else 'portrait_crop'


def make(video, job=None, post=None, profile=None, attempt=1, uploads=None, quiet=False):
    profile = profile_of(job, profile)
    if profile not in PROFILES:
        raise ValueError('unknown profile %r: %s' % (profile, ', '.join(PROFILES)))
    try:
        w, h, dur = probe(video)
        unreadable = None
    except (subprocess.CalledProcessError, ValueError) as e:
        w, h, dur, unreadable = 0, 0, 0.0, 'ffprobe cannot read the file (%s)' % str(e)[-80:]
    rec = {'schema': SCHEMA, 'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'tool': 'templates/qcrecord.py', 'profile': profile, 'attempt': int(attempt),
           'video': {'name': os.path.basename(video), 'sha256': sha_file(video), 'bytes': os.path.getsize(video),
                     'width': w, 'height': h, 'duration': round(dur, 3)},
           'text': text_hashes(job, post), 'manifest': manifest(job, uploads),
           'template_rev': template_rev(), 'rules_rev': rules_rev()}
    errs = [unreadable] if unreadable else decode_errors(video)
    reads = []
    if not errs:
        for t, i, kind, why in samples(video, job, dur):
            img = frame(video, t)
            if img is None:
                continue
            m = measure(img)
            m.update(t=t, shot=i, kind=kind, why=why)
            reads.append(m)
            if not quiet:
                print('qc: %6.2f s shot %-4s %-8s %-8s footage %3.0f%% of area, %3.0f%% of width, blur %2.0f%%%s'
                      % (t, i if i is not None else '-', kind, why, 100 * m['area'], 100 * m['width'],
                         100 * m['blur'], ', our text on the picture' if m.get('text_on_footage') else ''), flush=True)
    if errs:
        result, reason, repair, shots = 'REJECT', 'decode errors (%d), first: %s' % (len(errs), errs[0][:160]), None, []
    elif not reads:
        result, reason, repair, shots = 'FALLBACK', 'no frame could be read', None, []
    else:
        result, reason, repair, shots = judge(reads, profile, int(attempt))
    rec.update(result=result, reason=reason, repair=repair, shots=shots,
               samples=[{k: r.get(k) for k in ('t', 'shot', 'kind', 'why', 'area', 'width', 'blur', 'text_px', 'rect')}
                        for r in reads])
    rec['binding'] = binding(rec)
    return rec


# ---------------------------------------------------------------------------------------------
# Verify, bind, gate
# ---------------------------------------------------------------------------------------------
def verify(rec, video=None, job=None, post=None, video_sha=None):
    """(state, reasons): VALID, INVALID (an edit since the check, or a forged record) or STALE (template or rules
    changed since: QC again, no re-render). Only what is given is compared; the video always must be."""
    reasons, stale = [], []
    if rec.get('schema') != SCHEMA:
        return 'INVALID', ['not a %s record' % SCHEMA]
    if rec.get('result') not in RESULTS:
        return 'INVALID', ['unknown result %r' % rec.get('result')]
    if rec.get('binding') != binding(rec):
        reasons.append('the record was edited after it was made (binding digest differs)')
    vs = sha_file(video) if video else video_sha
    if not vs:
        reasons.append('no video given: a record is only valid against the file it names')
    elif vs != rec['video']['sha256']:
        reasons.append('video changed since the check')
    if job is not None:
        if text_hashes(job, None)['screen_sha256'] != rec['text'].get('screen_sha256'):
            reasons.append('on-screen text changed since the check')
        if manifest(job)['sha256'] != rec['manifest'].get('sha256'):
            reasons.append('job or assets changed since the check')
    if post is not None and sha_json(post) != rec['text'].get('post_sha256'):
        reasons.append('post text differs from the bound text' if rec['text'].get('post_sha256')
                       else 'post text not bound: run bind')
    if template_rev()['sha256'] != rec['template_rev'].get('sha256'):
        stale.append('template revision changed since the check')
    if rules_rev()['sha256'] != rec['rules_rev'].get('sha256'):
        stale.append('rules revision changed since the check')
    if reasons:
        return 'INVALID', reasons + stale
    if stale:
        return 'STALE', stale
    return 'VALID', []


def bind(rec, video, post):
    state, why = verify(rec, video=video)
    if state == 'INVALID':
        raise ValueError('cannot bind text to an invalid record: ' + '; '.join(why))
    rec = dict(rec)
    rec['text'] = dict(rec['text'])
    rec['text']['post_sha256'] = sha_json(post)
    rec['text']['sha256'] = sha_json([rec['text'].get('screen_sha256'), rec['text']['post_sha256']])
    rec['bound_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rec['binding'] = binding(rec)
    return rec


def row_field(rec, path=None):
    """What the commitments row carries in `qc`: the keeper reads this, never a sentence."""
    return {'result': rec['result'], 'profile': rec['profile'], 'record': path, 'binding': rec['binding'],
            'video_sha256': rec['video']['sha256'], 'text_sha256': rec['text']['sha256'],
            'post_text_bound': bool(rec['text'].get('post_sha256')), 'checked_at': rec['created_at']}


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------
def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _write(path, rec):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, path)


def default_out(video):
    stem = os.path.splitext(video)[0]
    return re.sub(r'-reel-v\d+$', '', stem) + '-qc.json' if re.search(r'-reel-v\d+$', stem) else stem + '-qc.json'


def main(argv=None):
    ap = argparse.ArgumentParser(description='QC record bound to the file (promise keeper, addendum D)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make')
    m.add_argument('video')
    m.add_argument('--job')
    m.add_argument('--text')
    m.add_argument('--profile', choices=sorted(PROFILES))
    m.add_argument('--attempt', type=int, default=1)
    m.add_argument('--out')
    m.add_argument('--uploads')
    for name in ('verify', 'gate', 'bind'):
        p = sub.add_parser(name)
        p.add_argument('record')
        p.add_argument('--video', required=name in ('gate', 'bind'))
        p.add_argument('--video-sha')
        p.add_argument('--job')
        p.add_argument('--text', required=name in ('gate', 'bind'))
    me = sub.add_parser('measure')
    me.add_argument('video')
    me.add_argument('t', nargs='*', type=float)
    a = ap.parse_args(argv)
    try:
        job = _load(a.job) if getattr(a, 'job', None) else None
        post = post_text(a.text) if getattr(a, 'text', None) else None
    except (OSError, ValueError) as e:
        print('qc: unreadable input: %s' % e, file=sys.stderr)
        return 2
    if a.cmd == 'measure':
        for t in a.t or [1.0]:
            print(t, json.dumps(measure(frame(a.video, t))))
        return 0
    if a.cmd == 'make':
        rec = make(a.video, job, post, a.profile, a.attempt, a.uploads)
        out = a.out or default_out(a.video)
        _write(out, rec)
        print('qc: %s%s: %s (%s) -> %s' % (rec['result'], (' ' + rec['repair']) if rec['repair'] else '',
                                          rec['video']['name'], rec['reason'], out))
        return EXIT[rec['result']]
    rec = _load(a.record)
    if a.cmd == 'bind':
        rec = bind(rec, a.video, post)
        _write(a.record, rec)
        print('qc: post text bound to %s' % rec['video']['name'])
        return 0
    state, why = verify(rec, video=a.video, job=job, post=post, video_sha=a.video_sha)
    if a.cmd == 'verify':
        print('qc: %s %s%s' % (state, rec.get('result'), (': ' + '; '.join(why)) if why else ''))
        return 0 if state == 'VALID' else 6
    # gate: only a valid PASS authorises scheduling
    if state != 'VALID':
        print('qc gate: NO, record %s: %s' % (state, '; '.join(why)))
        return 6
    if rec['result'] != 'PASS':
        print('qc gate: NO, %s%s: %s' % (rec['result'], (' ' + rec['repair']) if rec.get('repair') else '',
                                       rec.get('reason')))
        return EXIT[rec['result']]
    print('qc gate: YES')
    print(json.dumps(row_field(rec, os.path.relpath(a.record, ROOT) if os.path.isabs(a.record) else a.record),
                     ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
