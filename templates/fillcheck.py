"""Full-frame footage, never a box in a blurred fill (advisor card adv-20261030-one-piece-fortnite-hold, Mohammad
30 Oct 2026, 21:40 Dubai: the One Piece x Fortnite Reel put a small anime clip in the middle of a blur of itself).

Rule: no blurred-fill or pillarbox box for footage. When the best source cannot fill 9:16 at full height without going
below 1080 px on its short side, the Reel uses the full-frame treatment: the footage as large as the 2x cap allows, with a
designed band (template colour, chip row, headline) above and below, never a blur of the same picture. A render whose
main footage occupies less than 60% of the frame height fails.

What is measured: footage that reel.py crops itself (a landscape source) always fills the frame, so only portrait
sources are read, the picture tracks composed before the render (storybeat, storybook, a full-frame composite). Three
frames per footage shot, each row of the frame classed by its detail (mean step between neighbouring pixels) and its
spread (standard deviation along the row): footage (detail), flat (a designed band: almost no spread), or blurred (spread
without detail: a blur). A shot fails when blurred rows pass BLUR_MAX of the height, or, outside the storybeat template
(its page is the look Mohammad chose on 30 Oct), when footage rows are under FOOTAGE_MIN of the height.
`"fill_ok": [[file, start, reason]]` waives one shot after someone has looked at it.

    python3 fillcheck.py <video> [t ...]     prints the row classes of frames at those times
"""
import os, subprocess, sys

import numpy as np

FOOTAGE_MIN = 0.60
BLUR_MAX = 0.05
W, H = 270, 480                 # frames are read at a quarter of 1080x1920
DETAIL, SOFT, FLAT = 2.0, 1.0, 6.0   # segment detail above DETAIL is footage, under SOFT a blur or a band (a band when
                                   # its rows have spread under FLAT); between the two, footage only next to footage
EDGE_STEP, EDGE_FRAC = 10, 0.6  # a box edge: over 60% of the columns step by more than 10 levels to the next row


def frame(path, t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1', '-vf',
                          f'scale={W}:{H}:flags=area,format=gray', '-f', 'rawvideo', '-'],
                         capture_output=True, check=True).stdout
    if len(raw) < W * H:
        return None
    return np.frombuffer(raw[:W * H], np.uint8).reshape(H, W).astype(np.float32)


def rows(img):
    """(footage, flat, blurred) shares of the frame height. The frame is cut into segments at full-width straight
    edges (a box's top and bottom, a band's rule: rows where most columns step sharply to the next row); each segment
    is footage (detail), a flat band (no spread along its rows) or a blur (spread without detail)."""
    step = np.abs(np.diff(img, axis=0))
    frac = (step > EDGE_STEP).mean(axis=1)
    cuts = [0] + [y + 1 for y in range(len(frac)) if frac[y] > EDGE_FRAC] + [img.shape[0]]
    detail = np.abs(np.diff(img, axis=1)).mean(axis=1)
    spread = img.std(axis=1)
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a < 3:
            continue                                   # the edge rows themselves
        d, s = float(detail[a:b].mean()), float(np.median(spread[a:b]))
        segs.append((a, b, 'foot' if d > DETAIL else 'mid' if d > SOFT else 'flat' if s < FLAT else 'blur'))
    changed = True                                     # a soft part of the picture (sand, sky) next to it is the picture
    while changed:
        changed = False
        for k, (a, b, c) in enumerate(segs):
            if c == 'mid' and any(0 <= j < len(segs) and segs[j][2] == 'foot' for j in (k - 1, k + 1)):
                segs[k] = (a, b, 'foot')
                changed = True
    segs = [(a, b, 'blur' if c == 'mid' else c) for a, b, c in segs]
    feet = [k for k, sg in enumerate(segs) if sg[2] == 'foot']
    if feet:                                           # a smooth sky inside the picture is still the picture
        for k in range(feet[0], feet[-1] + 1):
            segs[k] = (segs[k][0], segs[k][1], 'foot')
    foot = sum(b - a for a, b, c in segs if c == 'foot')
    flat = sum(b - a for a, b, c in segs if c == 'flat')
    blur = sum(b - a for a, b, c in segs if c == 'blur')
    n = float(img.shape[0])
    return foot / n, flat / n, blur / n


def _size(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height', '-of', 'csv=p=0', path], text=True).strip().split(',')
    return int(out[0]), int(out[1])


def check(job, upload_dir):
    """Raise ValueError naming every footage shot that sits in a blurred fill or fills under 60% of the height."""
    waived = {(str(w[0]), round(float(w[1]), 2)) for w in (job.get('fill_ok') or []) if len(w) >= 3 and len(str(w[2])) >= 10}
    storybeat = job.get('template') == 'storybeat'
    bad, sizes = [], {}
    for i, sh in enumerate(job.get('shots') or []):
        f, st, du = str(sh[0]), sh[1], float(sh[2])
        path = os.path.join(upload_dir, f)
        if st is None or os.path.splitext(f)[1].lower() in ('.jpg', '.jpeg', '.png', '.webp') or '-gfx-' in f:
            continue
        if not os.path.exists(path) or (f, round(float(st), 2)) in waived:
            continue
        if f not in sizes:
            sizes[f] = _size(path)
        w, h = sizes[f]
        if h <= w:
            continue                                   # reel.py crops a landscape source to fill the frame
        reads = []
        for k in (0.2, 0.5, 0.8):
            img = frame(path, float(st) + du * k)
            if img is not None:
                reads.append(rows(img))
        if not reads:
            continue
        # a dark or soft frame can hide part of the picture, a layout never changes inside one shot: the best footage
        # reading and the middle blur reading of three frames
        foot = max(r[0] for r in reads)
        blur = sorted(r[2] for r in reads)[len(reads) // 2]
        flat = max(0.0, 1.0 - foot - blur)
        t = float(st) + du * 0.5
        print(f'fill: shot {i} {f} @{t:.2f}: footage {foot:.0%}, band {flat:.0%}, blurred {blur:.0%}', flush=True)
        if blur > BLUR_MAX:
            bad.append(f'shot {i} {f} at {t:.2f} s: {blur:.0%} of the height is a blurred fill')
        elif not storybeat and foot < FOOTAGE_MIN:
            bad.append(f'shot {i} {f} at {t:.2f} s: footage fills {foot:.0%} of the height (under {FOOTAGE_MIN:.0%})')
    if bad:
        raise ValueError('footage in a box or a blurred fill (adv-20261030-one-piece-fortnite-hold): ' + '; '.join(bad)
                         + '. Use the full-frame treatment (the footage as large as the 2x cap allows between designed '
                           'bands in the template colour), or fill_ok=[[file, start, reason]] after a look.')


if __name__ == '__main__':
    p = sys.argv[1]
    for t in [float(x) for x in sys.argv[2:]] or [1.0]:
        img = frame(p, t)
        print(t, 'footage %.0f%%, band %.0f%%, blurred %.0f%%' % tuple(100 * x for x in rows(img)))
