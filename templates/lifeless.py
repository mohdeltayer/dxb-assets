"""Lifeless score: how much of a finished Reel is a picture that does not move (adv-20261102-borrow-openmontage, part 1).

Our own code, written from the idea only (OpenMontage's "slideshow risk"; nothing read, copied or vendored from it,
AGPLv3). Measured on the decoded file, so it judges what ships:

  still_share     share of the story runtime (end card excluded) where the picture is near-still
  longest_still   the longest near-still stretch, in seconds
  cuts_per_10s    picture changes (hard cuts and fast crossfades) per 10 seconds
  held_under_text share of the runtime where the middle of the frame holds still while the frame as a whole moves:
                  text entering or leaving over a held picture

Frames are read at FPS, grey, at 90x160 (an area average, so the moving grain of the picture finish cancels out).
A frame is near-still when its mean change from the previous frame is under STILL (grey levels of 255); a change
over CUT is a cut. The score is 0 (alive) to 100 (a slideshow):

  score = 100 * (0.45 * still_share + 0.25 * min(longest_still / LONG, 1) + 0.15 * held_under_text
                 + 0.15 * max(0, 1 - cuts_per_10s / CUTS_OK))

Report only for its first three days (the card): render_job.py prints it after the decode checks and writes it to
render-times.json as `lifeless`; nothing is refused. After the calibration (notes/lifeless-calibration.md) a
threshold returns REPAIR (proposed REPAIR_AT, flagged as `over` in the report until then). Storybook pages are a declared exception for the stills share, not for the rest
(`storybook=True` leaves still_share out and rescales).

    python3 templates/lifeless.py <reel.mp4> [--storybook] [--tail 2.0]
"""
import json
import subprocess
import sys

import numpy as np

FPS = 10
W, H = 90, 160
STILL = 0.6          # mean grey change per frame under which the picture counts as held
CUT = 18.0           # mean grey change over which a frame counts as a cut
LONG = 6.0           # a still stretch this long counts fully in the score
CUTS_OK = 2.5        # cuts per 10 s at which the cut term is zero
MID = (0.30, 0.70)   # the middle band of the frame (rows), clear of the headline band and the story lines
TAIL = 2.0           # the end card (outro.CARD), left out
REPAIR_AT = 38.0     # proposed threshold after report-only (calibration of 5 Nov: notes/lifeless-calibration.md)


def frames(path):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', f'fps={FPS},scale={W}:{H}:flags=area,format=gray',
           '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (W * H)
    return np.frombuffer(raw[:n * W * H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)


def runs(mask):
    """Lengths of the True runs in a boolean array."""
    out, n = [], 0
    for m in mask:
        if m:
            n += 1
        elif n:
            out.append(n); n = 0
    if n:
        out.append(n)
    return out


def score(path, storybook=False, tail=TAIL):
    f = frames(path)
    keep = max(2, len(f) - int(round(tail * FPS)))
    f = f[:keep]
    d = np.abs(np.diff(f, axis=0))
    full = d.mean(axis=(1, 2))
    a, b = int(H * MID[0]), int(H * MID[1])
    mid = d[:, a:b, :].mean(axis=(1, 2))
    secs = len(full) / FPS
    still = full < STILL
    cut = full > CUT
    held_text = (mid < STILL) & (full >= STILL) & ~cut
    still_share = float(still.mean()) if len(full) else 0.0
    longest = max(runs(still), default=0) / FPS
    cuts = sum(1 for r in runs(cut))                 # a crossfade over two frames counts once
    cuts10 = cuts / secs * 10 if secs else 0.0
    held = float(held_text.mean()) if len(full) else 0.0
    terms = {'still': 0.45 * still_share, 'long': 0.25 * min(longest / LONG, 1.0), 'held': 0.15 * held,
             'cuts': 0.15 * max(0.0, 1.0 - cuts10 / CUTS_OK)}
    if storybook:
        terms.pop('still')
        total = sum(terms.values()) / 0.55
    else:
        total = sum(terms.values())
    return {'score': round(100 * total, 1), 'still_share': round(still_share, 3), 'longest_still': round(longest, 1),
            'cuts_per_10s': round(cuts10, 2), 'held_under_text': round(held, 3), 'secs': round(secs, 1),
            'storybook': storybook, 'mode': 'report-only'}


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    tail = float(a[a.index('--tail') + 1]) if '--tail' in a else TAIL
    print(json.dumps(score(a[0], storybook='--storybook' in a, tail=tail)))
