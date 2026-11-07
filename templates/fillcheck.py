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

Second test, the band layout is the weak-source exception (adv-20261107-band-layout-drift, Mohammad 7 Nov 2026, 11:38
Dubai): a 16:9 trailer or gameplay source fills 9:16, cropped to the subject. The full-frame band layout (indigo band
above and below, footage at its own width) is only for a source that cannot fill 9:16 inside the 2x cap, and the brief
names the sources tried. So a portrait footage shot that plays after the headline's last frame and carries a designed
band (BAND_MIN of the height or more) fails unless the job's lowres_ok names the sources tried: a list of at least two
sources, {"searched": [...], "result": "..."} with at least two, or a string in the form "A, B: what they had". A credit
line in the band changes nothing (it is still band), and a lowres_ok that names no source never counts. fill_ok waives
one shot as before; the storybeat page is exempt as before.

    python3 fillcheck.py <video> [t ...]     prints the row classes of frames at those times
"""
import os, subprocess, sys

import numpy as np

FOOTAGE_MIN = 0.60
BLUR_MAX = 0.05
BAND_MIN = 0.15            # a designed band this tall, after the headline, is the band layout
HEAD_SECS = 3.5            # reel.reel's default head_secs; a job may set its own
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


def weak_source(v):
    """The sources tried, when lowres_ok names at least two (or 'A, B: result'); else None."""
    if isinstance(v, dict):
        got = v.get('searched') or v.get('sources') or v.get('checked') or []
        got = [x for x in (got if isinstance(got, (list, tuple)) else str(got).split(',')) if str(x).strip()]
        return ', '.join(map(str, got)) if len(got) >= 2 else None
    if isinstance(v, (list, tuple)):
        got = [x for x in v if isinstance(x, str) and x.strip()]
        return ', '.join(got) if len(got) >= 2 else None
    if isinstance(v, str) and ':' in v:
        names = [x for x in v.split(':', 1)[0].split(',') if x.strip()]
        return v.strip() if len(names) >= 2 and v.split(':', 1)[1].strip() else None
    return None


def check(job, upload_dir, starts=None):
    """Raise ValueError naming every footage shot that sits in a blurred fill or fills under 60% of the height, and
    every band-layout shot after the headline without a weak-source reason. starts: each shot's start on the timeline
    (render_job's timeline); without it the shots are taken back to back."""
    weak = weak_source(job.get('lowres_ok'))
    head = float(job.get('head_secs') or HEAD_SECS)
    if starts is None:
        starts, t0 = [], 0.0
        for sh in job.get('shots') or []:
            starts.append(t0)
            t0 += float(sh[2])
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
        elif not storybeat and flat >= BAND_MIN and i < len(starts) and float(starts[i]) + du > head + 0.05:
            if weak:
                print(f'fill: shot {i} band layout after the headline, weak source named: {weak}', flush=True)
            else:
                bad.append(f'shot {i} {f} from {max(float(starts[i]), head):.2f} s: band layout ({flat:.0%} band, '
                           f'footage {foot:.0%}) after the headline with no weak source named; the footage fills 9:16 '
                           'cropped to the subject unless no copy fills inside the 2x cap, and then lowres_ok names the '
                           'sources tried ("IGN, publisher press site, Steam: none above 720p") '
                           '(adv-20261107-band-layout-drift)')
    if bad:
        raise ValueError('footage does not fill the frame (adv-20261030-one-piece-fortnite-hold, '
                         'adv-20261107-band-layout-drift): ' + '; '.join(bad)
                         + '. A 16:9 source fills 9:16 cropped to the subject; the band layout (footage as large as '
                           'the 2x cap allows between designed bands) is for a weak source with the sources named in '
                           'lowres_ok; never a blurred fill. fill_ok=[[file, start, reason]] after a look.')


if __name__ == '__main__':
    p = sys.argv[1]
    for t in [float(x) for x in sys.argv[2:]] or [1.0]:
        img = frame(p, t)
        print(t, 'footage %.0f%%, band %.0f%%, blurred %.0f%%' % tuple(100 * x for x in rows(img)))
