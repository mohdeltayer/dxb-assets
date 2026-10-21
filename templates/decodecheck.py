"""Damaged-footage checks (advisor, 21 Oct 2026, after the Battlefield 1 Reel went out with decode damage at
5.3 s: a blocky smear of the previous shot over a new scene, from a damaged IGN download).

decode_errors(path)   every frame decoded once (ffmpeg -v error ... -f null -); any line is damage
smear_times(path)     sudden blocky smear: long straight edges in the picture area jump far above the clip's
                      own level and stay for more than 3 frames (the Battlefield 1 smear read 15 to 17 against
                      1 to 4 for the rest of the Reel); returns [(start s, end s, peak)]
dense_strip(path,out) 4 frames a second through the whole clip, so the first second of every shot is seen

    python3 templates/decodecheck.py <file.mp4> [--strip out.jpg]
"""
import subprocess, sys
import numpy as np

W, H = 270, 480          # analysis size for a 9:16 Reel; a 16:9 source is read at 480x270
RUN = 7                  # an edge counts when it runs straight for this many pixels
MIN_FRAMES = 8           # a crossfade between two busy shots reads 4 to 6 frames; the Battlefield 1 smear read 23
FLOOR, RATIO = 12.0, 4.0 # flagged when above both the floor and RATIO times the median around it


def decode_errors(path, start=None, dur=None):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error'] + (['-ss', str(start)] if start else []) + ['-i', path]
    cmd += (['-t', str(dur)] if dur else []) + ['-f', 'null', '-']
    p = subprocess.run(cmd, capture_output=True, text=True)
    return [l for l in (p.stderr or '').splitlines() if l.strip()]


def _frames(path, start=None, dur=None):
    w, h = (W, H)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                            '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')
    if len(probe) == 2 and int(probe[0]) > int(probe[1]):
        w, h = H, W
    cmd = ['ffmpeg', '-nostdin', '-v', 'error'] + (['-ss', str(start)] if start else []) + ['-i', path]
    cmd += (['-t', str(dur)] if dur else []) + ['-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    fps = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip() or '30/1'
    n, d = (fps.split('/') + ['1'])[:2]
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32), float(n) / float(d or 1)


BANDS = ((0.30, 0.56), (0.80, 0.96))   # of a 9:16 frame: below the headline band, and below the lines and strip;
                                       # our own text enters elsewhere and would read as straight edges


def _straight(fr):
    """Density of long straight edges (horizontal and vertical) in the picture area. A vertical Reel is read in
    BANDS only, clear of our headline, lines and strip; a 16:9 source is read whole bar the edges."""
    h = fr.shape[0]
    if h > fr.shape[1]:
        g = np.concatenate([fr[int(a * h):int(b * h)] for a, b in BANDS])
    else:
        g = fr[h // 12: -h // 12]
    out = []
    for gr, ax in ((np.abs(np.diff(g, axis=0)), 1), (np.abs(np.diff(g, axis=1)), 0)):
        s = gr > 40
        acc = s[:, :-RUN + 1] if ax == 1 else s[:-RUN + 1]
        for k in range(1, RUN):
            acc = acc & (s[:, k:k - RUN + 1 or None] if ax == 1 else s[k:k - RUN + 1 or None])
        out.append(acc.mean() * 1e3)
    return out


LOCAL = 1.5   # seconds either side: the baseline is the footage around the frame, not the whole clip


def smear_times(path, start=None, dur=None):
    """Runs of more than 3 frames whose straight-edge density jumps above both FLOOR and RATIO times the median of
    the footage within LOCAL seconds either side. Damage arrives with a cut and heals; busy art (pixel art, UI,
    rings) is busy for the whole shot, so its own neighbourhood lifts the bar."""
    F, fps = _frames(path, start, dur)
    if len(F) < MIN_FRAMES:
        return []
    M = np.array([_straight(f) for f in F])
    k = int(LOCAL * fps)
    hits = np.zeros(len(F), bool)
    for i in range(len(F)):
        lo, hi = max(0, i - k), min(len(F), i + k + 1)
        ring = np.concatenate([M[lo:max(lo, i - 2)], M[min(hi, i + 3):hi]]) if hi - lo > 6 else M[lo:hi]
        base = np.median(ring, axis=0)
        hits[i] = bool(np.any(M[i] > np.maximum(FLOOR, RATIO * base)))
    found, i, t0 = [], 0, float(start or 0)
    while i < len(hits):
        if hits[i]:
            j = i
            while j < len(hits) and hits[j]:
                j += 1
            if j - i >= MIN_FRAMES:
                found.append((round(t0 + i / fps, 2), round(t0 + j / fps, 2), round(float(M[i:j].max()), 1)))
            i = j
        else:
            i += 1
    return found


def dense_strip(path, out, fps=4, width=108):
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                               capture_output=True, text=True).stdout.strip() or 0)
    cols = 16
    rows = max(1, int(dur * fps + cols - 1) // cols)
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', path, '-vf',
                    f"fps={fps},scale={width}:-2,drawtext=text='%{{pts\\:hms}}':x=2:y=2:fontsize=11:fontcolor=yellow:"
                    f"box=1:boxcolor=black@0.6,tile={cols}x{rows}", '-frames:v', '1', out], check=True)
    return out


def check(path, waived=()):
    """Raise on decode errors or a smear outside the waived [(t0, t1, reason)] ranges; return the smears found."""
    errs = decode_errors(path)
    if errs:
        raise ValueError(f'{path}: decode errors ({len(errs)}), first: {errs[0]}')
    bad = [s for s in smear_times(path) if not any(a <= s[0] <= b for a, b, *_ in waived)]
    if bad:
        raise ValueError(f'{path}: blocky smear at ' + ', '.join(f'{a:.2f} to {b:.2f} s (peak {p})' for a, b, p in bad)
                         + '; look at the frames, then re-fetch the source or pass block_ok=[[t0, t1, reason]]')
    return bad


if __name__ == '__main__':
    p = sys.argv[1]
    errs = decode_errors(p)
    print('decode:', 'clean' if not errs else f'{len(errs)} errors, first: {errs[0]}')
    sm = smear_times(p)
    print('smear:', 'none' if not sm else ', '.join(f'{a:.2f} to {b:.2f} s (peak {v})' for a, b, v in sm))
    if '--strip' in sys.argv:
        print(dense_strip(p, sys.argv[sys.argv.index('--strip') + 1]))
    sys.exit(1 if errs or sm else 0)
