"""Damaged-footage checks (advisor, 21 Oct 2026, after the Battlefield 1 Reel went out with decode damage at
5.3 s: a blocky smear of the previous shot over a new scene, from a damaged IGN download).

decode_errors(path)   every frame decoded once (ffmpeg -v error ... -f null -); any line is damage
smear_times(path)     sudden blocky smear: long straight edges in the picture area jump far above the clip's
                      own level and stay for more than 3 frames (the Battlefield 1 smear read 15 to 17 against
                      1 to 4 for the rest of the Reel); returns [(start s, end s, peak)]
dense_strip(path,out) 4 frames a second through the whole clip, so the first second of every shot is seen

Source quality (Mohammad, 24 Oct 2026, inbox 16:26Z, after the ARMS check): the checks above look for broken
video; these look for a valid but weak source. The ARMS hoop swing (Nintendo's only copy, 1280x720 at 2.6 Mbps,
enlarged 2.7x) broke into big squares in a fast camera move.
probe(path)           (width, height, fps, video bit/s), cached per file
bitrate_floor(w,h,f)  the floor for that source: 5 Mbps at 1080p, 3 Mbps at 720p (see BITRATE_*)
bitrate_flag(path)    None, or 'low bitrate 2.6 Mbps (floor 3.0 Mbps for 1280x720 at 30 fps)'
block_ratio(path,s,d) the 8x8 block-edge ratio the encoder leaves over a stretch: (median, peak, frames);
                      a peak above BLOCK_MAX reads as blocky once the shot is enlarged past 2x

    python3 templates/decodecheck.py <file.mp4> [--strip out.jpg]
    python3 templates/decodecheck.py <file.mp4> --blocks <start> <seconds>
"""
import json, math, os, subprocess, sys
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


# Source quality (24 Oct 2026). The bitrate floor is for the bits that land in the 9:16 window, written in source
# terms: 5 Mbps for a 16:9 1080p source at 30 fps, 3 Mbps at 720p, in between and below on (height / 1080) ** 1.26
# (0.63 in pixels, the exponent the two approved points give). It holds at 5 Mbps above 1080p, since a larger source
# is enlarged less and the same bits in the window serve it (IGN's 1440p30 at 5.3 Mbps and 4K60 at 15 Mbps pass). A
# source narrower than 16:9 (a vertical cut) keeps more of its width, so its floor falls with the share it keeps; one
# under 30 fps spends its bits on fewer frames, so its floor falls with fps / 30 (a 24 fps Steam trailer: 4 Mbps).
BITRATE_FLOOR = 5.0e6
BITRATE_720 = 3.0e6
BITRATE_EXP = math.log(BITRATE_FLOOR / BITRATE_720) / math.log(1080 / 720)
# Block-edge ratio: mean luma step across 8-pixel boundaries over the mean step everywhere else, per frame at the
# source's own size (no scaling, so the grid stays put). ARMS: the hoop swing read median 1.41, peak 1.56 over 0.2 s
# (frame max 1.61); the clean ARMS shots peaked 1.41 to 1.45; Steam and IGN 1080p trailers 1.06 to 1.30.
BLOCK_MAX = 1.5          # peak of the BLOCK_WIN rolling mean above this: blocky
BLOCK_WIN = 0.2          # seconds: a burst the eye catches, not one odd frame
BLOCK_FPS = 30           # frames read per second at most (a 60 fps source is read on every other frame)
_PROBE, _BLOCK = {}, {}


def probe(path):
    """(width, height, fps, video bit/s) of a file's first video stream; bit/s from the stream, else the
    container's, else size over duration."""
    key = (path, os.path.getmtime(path), os.path.getsize(path))
    if key not in _PROBE:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                            'stream=width,height,r_frame_rate,bit_rate:format=bit_rate,duration', '-of', 'json', path],
                           capture_output=True, text=True)
        j = json.loads(r.stdout or '{}')
        st = (j.get('streams') or [{}])[0]
        fm = j.get('format') or {}
        n, d = (str(st.get('r_frame_rate', '30/1')).split('/') + ['1'])[:2]
        fps = float(n) / float(d or 1) if float(d or 1) else 30.0
        bps = st.get('bit_rate') or fm.get('bit_rate')
        if not bps or bps == 'N/A':
            bps = os.path.getsize(path) * 8 / max(0.1, float(fm.get('duration') or 1))
        _PROBE[key] = (int(st.get('width', 0)), int(st.get('height', 0)), fps, float(bps))
    return _PROBE[key]


def bitrate_floor(w, h, fps):
    share = min(1.0, h * 9 / 16 / w) if w else 1.0     # the part of the width the 9:16 window keeps (16:9: 0.316)
    k = min(1.0, (h / 1080) ** BITRATE_EXP) * min(1.0, fps / 30)
    return BITRATE_FLOOR * k * (9 / 16) ** 2 / share


def bitrate_flag(path):
    w, h, fps, bps = probe(path)
    floor = bitrate_floor(w, h, fps)
    if bps >= floor:
        return None
    return f'low bitrate {bps / 1e6:.1f} Mbps (floor {floor / 1e6:.1f} Mbps for {w}x{h} at {fps:.0f} fps)'


def block_ratio(path, start, dur, crop=None):
    """(median, peak, frames) of the 8x8 block-edge ratio over [start, start + dur] of `path`, read at its own size.
    `crop` (w, h, x, y) keeps to the picture inside a letterbox; the grid is counted from the coded frame's origin.
    The peak is the highest BLOCK_WIN rolling mean. Flat frames (black, fades) are skipped. About 0.3 s per second
    of 720p and 0.6 s per second of 1080p on the container."""
    key = (path, round(float(start), 3), round(float(dur), 3), crop, os.path.getmtime(path))
    if key in _BLOCK:
        return _BLOCK[key]
    W0, H0, fps, _ = probe(path)
    w, h, x, y = crop or (W0, H0, 0, 0)
    vf = (f'crop={w}:{h}:{x}:{y},' if crop else '') + 'format=gray'
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(start), '-t', str(dur), '-i', path, '-an',
                          '-vf', vf, '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    step = max(1, round(fps / BLOCK_FPS))
    bc = ((np.arange(w - 1) + x) % 8) == 7     # between pixel 7 and 8 of each block, across
    br = ((np.arange(h - 1) + y) % 8) == 7     # and down
    n, i, out = w * h, 0, []
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        i += 1
        if (i - 1) % step:
            continue
        f = np.frombuffer(buf, np.uint8).reshape(h, w).astype(np.int16)
        dx, dy = np.abs(np.diff(f, axis=1)), np.abs(np.diff(f, axis=0))
        den = dx[:, ~bc].mean() + dy[~br, :].mean()
        if den > 1.0:
            out.append((dx[:, bc].mean() + dy[br, :].mean()) / den)
    p.stdout.close(); p.wait()
    if not out:
        res = (0.0, 0.0, 0)
    else:
        r = np.array(out)
        k = max(1, min(len(r), round(BLOCK_WIN * fps / step)))
        res = (round(float(np.median(r)), 2), round(float(np.convolve(r, np.ones(k) / k, 'valid').max()), 2), len(r))
    _BLOCK[key] = res
    return res


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
    if '--blocks' in sys.argv:
        k = sys.argv.index('--blocks')
        med, peak, n = block_ratio(p, float(sys.argv[k + 1]), float(sys.argv[k + 2]))
        print(f'blocks: median {med}, peak {peak} over {n} frames' + (' (blocky)' if peak > BLOCK_MAX else ''))
        print('bitrate:', bitrate_flag(p) or 'ok (%.1f Mbps)' % (probe(p)[3] / 1e6))
        sys.exit(0)
    errs = decode_errors(p)
    print('decode:', 'clean' if not errs else f'{len(errs)} errors, first: {errs[0]}')
    sm = smear_times(p)
    print('smear:', 'none' if not sm else ', '.join(f'{a:.2f} to {b:.2f} s (peak {v})' for a, b, v in sm))
    if '--strip' in sys.argv:
        print(dense_strip(p, sys.argv[sys.argv.index('--strip') + 1]))
    sys.exit(1 if errs or sm else 0)
