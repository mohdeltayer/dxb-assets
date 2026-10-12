"""Our own graphics (numbers Reels) on a living ground.

Mohammad, 12 Oct 2026, on the Resident Evil box office Reel: once the
headline goes, the charts sat on a big flat purple ground and the Reel felt
stale; add faint wavy lines behind them that never get in the way. So every
graphic is drawn on a transparent canvas (`canvas()`), and `shots()` turns
each one into a clip over the indigo ground with the banner's wave lines in
the theme's colours drifting slowly sideways for the whole Reel: a little
stronger at the top and the bottom, faint behind the chart and the lines.
The drift runs on one clock across all the slides, so the crossfades between
them never double the lines. The clips go to reel() like any footage.

    import numgfx as NG
    im = NG.canvas(); ...draw...; im.save(UP + 're-gfx-1.png')
    shots = NG.shots([('re-gfx-1.png', 3.6), ('re-gfx-2.png', 5.0)], 'gold', 're-film')
"""
import math, os, subprocess, tempfile, shutil
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import cards as C, fast_ar as A, reel as RL

W, H = RL.W, RL.H
SPEED = 26          # px a second the waves drift
FPS = 30
SUB = 'numbers'     # clips are written under uploads/numbers/


def canvas():
    """A transparent 1080x1920 canvas for one graphic (no ground of its own)."""
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def _profile(y):
    """Wave strength down the frame: clear at the top and bottom edges of the
    content, faint behind the chart (y 300 to 1350) and the story lines."""
    top = max(0.0, 1 - y / 420) ** 1.2
    bot = max(0.0, (y - 1380) / 540) ** 1.2
    return 0.10 + 0.26 * max(top, bot)


def _mask(theme, seed):
    """White wave lines on black, 2W wide and periodic in W, faded by _profile."""
    freq, amp, gap = A.THEMES[theme][2:]
    m = max(1, round(freq / math.pi))           # whole waves across W, so the drift loops
    n = m * 2 + 1
    gap = gap * 4                               # sparser than the banner
    k = 2
    lay = Image.new('L', (2 * W * k, H * k), 0); d = ImageDraw.Draw(lay)
    ph = (seed % 628) / 100
    for j in range(-2, H // gap + 3):
        pts = [(x, (j * gap + amp * math.sin(2 * math.pi * m * x / (W * k) + j * 0.22 + ph)
                    + amp * 0.5 * math.sin(2 * math.pi * n * x / (W * k) + ph * 1.7 + j * 0.1)) * k)
               for x in range(0, 2 * W * k + 12, 12)]
        d.line(pts, fill=255, width=2 * k)
    lay = lay.resize((2 * W, H), Image.LANCZOS)
    prof = Image.new('L', (1, H))
    for y in range(H):
        prof.putpixel((0, y), int(255 * _profile(y)))
    return ImageChops.multiply(lay, prof.resize(lay.size))


def _ground():
    """The indigo ground with the soft glow the graphics used to carry."""
    g = Image.new('RGB', (W, H), A.GROUND); d = ImageDraw.Draw(g)
    d.ellipse([-300, 450, W + 300, 1400], fill=(34, 33, 92))
    return g.filter(ImageFilter.GaussianBlur(160))


def _gradient(theme):
    left, right = A.THEMES[theme][:2]
    row = Image.new('RGB', (2, 1)); row.putpixel((0, 0), left); row.putpixel((1, 0), right)
    return row.resize((W, H), Image.BILINEAR)


def slide(graphic, secs, theme, out, seed=0, t0=0.0, fast=False):
    """One graphic (RGBA, any 9:16 size) over the drifting ground, `secs` long,
    its drift starting at the shared clock `t0`. Returns `out`."""
    tmp = tempfile.mkdtemp(prefix='numbers-')
    try:
        _ground().save(f'{tmp}/g.png'); _gradient(theme).save(f'{tmp}/c.png')
        _mask(theme, seed).save(f'{tmp}/m.png')
        Image.open(graphic).convert('RGBA').resize((W, H), Image.LANCZOS).save(f'{tmp}/f.png')
        x = f"mod(({t0:.3f}+t)*{SPEED}\\,{W})"
        fc = (f"[2:v]format=gray,crop={W}:{H}:x='{x}':y=0[m];"
              f"[1:v]format=rgb24[c];[c][m]alphamerge[w];"
              f"[0:v][w]overlay=0:0:format=auto[gw];[gw][3:v]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]")
        args = ['ffmpeg', '-nostdin', '-y', '-v', 'error']
        for p in ('g', 'c', 'm', 'f'):
            args += ['-loop', '1', '-framerate', str(FPS), '-t', f'{secs:.3f}', '-i', f'{tmp}/{p}.png']
        enc = RL.DRAFT_ENC if fast else ['-preset', 'slow', '-crf', '15']
        subprocess.run(args + ['-filter_complex', fc, '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                       + enc + [out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def shots(slides, theme, name, fast=False):
    """[(graphic file in uploads, seconds)] -> reel() shots. Each slide becomes
    uploads/numbers/<name>-<i>.mp4 on the shared drift clock (so the
    crossfades line up) and is cut in whole, focus 0.5."""
    os.makedirs(C.U + SUB, exist_ok=True)
    seed = sum(map(ord, name))
    out, t = [], 0.0
    for i, (g, secs) in enumerate(slides):
        f = f'{SUB}/{name}-{i + 1}.mp4'
        slide(C.U + g, secs, theme, C.U + f, seed=seed, t0=t, fast=fast)
        out.append((f, 0.0, secs, 0.5))
        t += secs - RL.X                         # the next slide starts inside this one's crossfade
    return out
