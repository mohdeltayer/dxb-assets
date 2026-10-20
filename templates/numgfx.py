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

Grounds vary and windows hold clips (Mohammad, 14 Oct 2026, after the GBA
Nintendo Classics Reel): the ground comes in several styles (`GROUNDS`) that
rotate per Reel through assets/ground-ledger.json like the band styles, each
checked for readability under the graphic's text before it renders
(`check_ground`), and `window()` / `window_shots()` play a short clip inside
a graphic's framed window instead of a still.

    shots = NG.shots([...], 'gold', 're-film')                  # ground rotates
    shots = NG.shots([...], 'gold', 're-film', ground='grid')   # or pick one
    NG.window('gba-gfx-3.png', 'clip.mp4', (60, 500, 960, 640), 12.0, 4.0, out, 'cold', punch=True)
"""
import json, math, os, subprocess, tempfile, shutil
from functools import lru_cache
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import cards as C, fast_ar as A, ig_ar as G, reel as RL

W, H = RL.W, RL.H
SPEED = 26          # px a second the waves drift
FPS = 30
SUB = 'numbers'     # clips are written under uploads/numbers/
MIN_TEXT = 40       # the smallest type on a card (advisor review, 14 Oct 2026): an attribution line is 40 px or moves to the credit line


def canvas():
    """A transparent 1080x1920 canvas for one graphic (no ground of its own)."""
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


# Game-skinned numbers (advisor, 20 Oct 2026; Mohammad on the GTA 6 pre-orders Reel: "looks a bit generic, adding a
# logo or a theme close to the game is more attractive"). A numbers card about one game wears it: its official key art
# or a trailer frame blurred behind (the 'still' ground, always, when `still` is given; _resolve) and its official logo
# on a plate above the main figure, so the first frame (the grid tile) shows logo, figure and headline together.
# Multi-game charts pass no still: they keep the rotating living ground and put each game's art beside its row.
LOGO_BOX = (190, 690, 890, 890)     # under the headline (it ends near y 650), above the figure; inside the safe zone
LOGO_PAD = 30                       # logo clear of the plate's edge


def logo_plate(logo, box=LOGO_BOX, theme='cold'):
    """The game's official logo (a transparent PNG) centred on a plate cut to `box` exactly (logos need plating):
    the indigo ground at 78%, rounded, a 3 px edge in the theme's accent. Returns an RGBA image the size of `box`."""
    w, h = box[2] - box[0], box[3] - box[1]
    plate = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    acc = G.ACCENTS[theme]
    ImageDraw.Draw(plate).rounded_rectangle([1, 1, w - 2, h - 2], 26, fill=A.hx('#141332') + (199,),
                                            outline=tuple(acc[:3]) + (255,), width=3)
    art = Image.open(logo).convert('RGBA')
    art = art.crop(art.getbbox() or (0, 0, art.width, art.height))
    k = min((w - 2 * LOGO_PAD) / art.width, (h - 2 * LOGO_PAD) / art.height)
    art = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))), Image.LANCZOS)
    plate.alpha_composite(art, ((w - art.width) // 2, (h - art.height) // 2))
    return plate


def put_logo(im, logo, box=LOGO_BOX, theme='cold'):
    """Draw the plated logo onto a canvas() graphic at `box`. Returns the canvas."""
    im.alpha_composite(logo_plate(logo, box, theme), tuple(box[:2]))
    return im


def _profile(y):
    """Wave strength down the frame: clear at the top and bottom edges of the
    content, faint behind the chart (y 300 to 1350) and the story lines."""
    top = max(0.0, 1 - y / 420) ** 1.2
    bot = max(0.0, (y - 1380) / 540) ** 1.2
    return 0.10 + 0.26 * max(top, bot)


def _mask(theme, seed, gapmul=4, slant=0, strength=1.0):
    """White wave lines on black, 2W wide and periodic in W, faded by _profile.
    `gapmul` is the line spacing in banner gaps (4 = the original, 2 = dense),
    `slant` how many gaps each line climbs across one W (0 = level; a whole
    number, so the drift still loops), `strength` scales the lines."""
    freq, amp, gap = A.THEMES[theme][2:]
    m = max(1, round(freq / math.pi))           # whole waves across W, so the drift loops
    n = m * 2 + 1
    gap = gap * gapmul                          # sparser than the banner
    k = 2
    lay = Image.new('L', (2 * W * k, H * k), 0); d = ImageDraw.Draw(lay)
    ph = (seed % 628) / 100
    for j in range(-2 - 2 * abs(slant), H // gap + 3):
        pts = [(x, (j * gap + amp * math.sin(2 * math.pi * m * x / (W * k) + j * 0.22 + ph)
                    + amp * 0.5 * math.sin(2 * math.pi * n * x / (W * k) + ph * 1.7 + j * 0.1)
                    + slant * gap * x / (W * k)) * k)
               for x in range(0, 2 * W * k + 12, 12)]
        d.line(pts, fill=255, width=2 * k)
    lay = lay.resize((2 * W, H), Image.LANCZOS)
    prof = Image.new('L', (1, H))
    for y in range(H):
        prof.putpixel((0, y), int(255 * min(1.0, _profile(y) * strength)))
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




# ---------------------------------------------------------------------------
# Ground styles (Mohammad, 14 Oct 2026: "add variety without losing the
# ability to read"). Every style drifts slowly on the one shared clock `t0`,
# so the crossfades between slides never double, and every style is measured
# under the graphic's text before it renders (check_ground).
# ---------------------------------------------------------------------------
GROUNDS = ['waves', 'glow', 'wash', 'grid', 'waves-angled', 'waves-dense', 'still']
GROUND_LEDGER = os.path.join(os.path.dirname(__file__), 'assets', 'ground-ledger.json')

#: Readability limits, on a 0 to 255 luminance scale (Rec. 601).
MEAN_MARGIN = 12            # mean under the text may exceed the plain indigo's by this much
LOCAL_MAX = 90              # after a 64 px box blur, nothing under the text gets brighter
STILL_DIMS = (0.55, 0.65, 0.75)     # the 'still' ground dims harder before it gives up
DEFAULT_BAND = (96, 380, 984, 1300)  # text area when the graphic gives no usable box

#: Luminance a colour may add at its strongest (glow, wash), so a pale amber
#: and a deep indigo both stay under the readability limit.
GLOW_GAIN, WASH_GAIN, GRID_ALPHA = 30.0, 9.0, 0.50


def rotate_ground(name, allow=None):
    """The ground for this Reel: kept on a re-render, else the one rested
    longest in assets/ground-ledger.json (same scheme as reel.pick_style, so
    no two Reels in a row share one). `allow` limits the choice, for example
    without 'still' when the story has no official image."""
    allow = [g for g in GROUNDS if allow is None or g in allow]
    try:
        book = json.load(open(GROUND_LEDGER))
    except (OSError, ValueError):
        book = {}
    key = os.path.basename(name)
    if book.get(key) not in allow:
        used = list(book.values())
        last = {g: max([i for i, v in enumerate(used) if v == g], default=-1) for g in allow}
        book.pop(key, None)                      # a changed pick moves to the end of the history
        book[key] = min(allow, key=lambda g: last[g])
        json.dump(book, open(GROUND_LEDGER, 'w'), indent=1)
    return book[key]


def _lum(a):
    a = np.asarray(a, dtype=np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


@lru_cache(maxsize=1)
def _plain():
    return _ground()


def _gain_alpha(colour, gain):
    """Alpha at which `colour` over the indigo adds `gain` luminance."""
    base = float(_lum(np.array(A.GROUND)))
    return min(1.0, gain / max(float(_lum(np.array(colour))) - base, 40.0))


def _blob(colour, peak, size=1300, sigma=340):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r2 = ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / sigma ** 2
    a = (255 * peak * np.exp(-r2)).astype(np.uint8)
    im = np.zeros((size, size, 4), np.uint8); im[..., :3] = colour; im[..., 3] = a
    return Image.fromarray(im, 'RGBA')


def _wash_image(theme, period):
    """Diagonal two-tone, W + period wide and periodic in `period`, so the
    boundary can drift sideways for ever. Soft edge, low opacity."""
    c1, c2 = A.THEMES[theme][:2]
    w = W + period
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(H, dtype=np.float32))
    u = np.sin(2 * np.pi * (xx + 0.55 * yy) / period)
    f = 0.5 + 0.5 * np.tanh(2.2 * u)             # 0 on one side of the boundary, 1 on the other
    a1, a2 = _gain_alpha(c1, WASH_GAIN), _gain_alpha(c2, WASH_GAIN)
    rgb = np.zeros((H, w, 4), np.uint8)
    for ch in range(3):
        rgb[..., ch] = (c1[ch] * (1 - f) + c2[ch] * f).astype(np.uint8)
    rgb[..., 3] = (255 * (a1 * (1 - f) + a2 * f)).astype(np.uint8)
    return Image.fromarray(rgb, 'RGBA')


def _grid_image(theme, step=40):
    """A fine dot grid, W + step by H + step, in the theme's first colour."""
    col = A.THEMES[theme][0]
    ss = 4
    im = Image.new('RGBA', ((W + step) * ss, (H + step) * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a = int(255 * GRID_ALPHA); r = 1.9 * ss
    for y in range(step // 2, H + step, step):
        for x in range(step // 2, W + step, step):
            cx, cy = x * ss, y * ss
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    return im.resize((W + step, H + step), Image.LANCZOS)


def _still_image(still, dim):
    """The official image, blurred and dimmed with the indigo (ig_ar's bg_dim
    look), 1.2x the frame wide so it can pan: returns (image, pan range px)."""
    half_h = H // 2
    pw = int(W * 1.2) // 2
    im = Image.open(still).convert('RGB')
    s = max(pw / im.width, half_h / im.height)
    im = im.resize((max(pw, round(im.width * s)), max(half_h, round(im.height * s))), Image.LANCZOS)
    l, t = (im.width - pw) // 2, (im.height - half_h) // 2
    im = im.crop((l, t, l + pw, t + half_h)).filter(ImageFilter.GaussianBlur(40))
    im = im.resize((pw * 2, H), Image.BICUBIC)
    im = Image.blend(im, Image.new('RGB', im.size, A.GROUND), dim)
    return im, im.width - W


def _build_ground(ground, theme, seed, t0, tmp, still=None, dim=None):
    """Write the ground's input images into `tmp` and return (files, graph):
    `files[0]` is the base, the rest are layers; `graph` is the filter text
    that ends in the label [gw], numbering its inputs from 0 and using the
    shared clock (t0 + t) for every drift."""
    if ground not in GROUNDS:
        raise ValueError(f'ground is one of {", ".join(GROUNDS)}, not {ground!r}')
    T = f'({t0:.3f}+t)'
    files = []

    def save(img, name):
        f = f'{tmp}/{name}.png'; img.save(f); files.append(f); return f

    if ground in ('waves', 'waves-angled', 'waves-dense'):
        save(_plain(), 'g'); save(_gradient(theme), 'c')
        if ground == 'waves':
            save(_mask(theme, seed), 'm')
        elif ground == 'waves-angled':
            save(_mask(theme, seed + 90, slant=5), 'm')
        else:
            save(_mask(theme, seed + 40, gapmul=2, strength=0.8), 'm')
        speed = SPEED * (1.25 if ground == 'waves-angled' else 1.0)
        x = f"mod({T}*{speed}\\,{W})"
        return files, (f"[2:v]format=gray,crop={W}:{H}:x='{x}':y=0[m];"
                       f"[1:v]format=rgb24[c];[c][m]alphamerge[w];"
                       f"[0:v][w]overlay=0:0:format=auto[gw]")
    if ground == 'glow':
        c1, c2 = A.THEMES[theme][:2]
        save(_plain(), 'g')
        save(_blob(c1, _gain_alpha(c1, GLOW_GAIN)), 'b1'); save(_blob(c2, _gain_alpha(c2, GLOW_GAIN)), 'b2')
        ph = (seed % 628) / 100
        x1 = f"{250 - 650}+170*sin(2*PI*{T}/17+{ph:.2f})"
        y1 = f"{560 - 650}+150*sin(2*PI*{T}/13+{ph + 1:.2f})"
        x2 = f"{850 - 650}+170*sin(2*PI*{T}/19+{ph + 2:.2f})"
        y2 = f"{1450 - 650}+150*sin(2*PI*{T}/15+{ph + .5:.2f})"
        return files, (f"[0:v][1:v]overlay=x='{x1}':y='{y1}':format=auto:eval=frame[a];"
                       f"[a][2:v]overlay=x='{x2}':y='{y2}':format=auto:eval=frame[gw]")
    if ground == 'wash':
        period = 2 * W
        save(_plain(), 'g'); save(_wash_image(theme, period), 'w')
        x = f"mod({T}*{SPEED * 0.8:.1f}\\,{period})"
        return files, f"[1:v]crop={W}:{H}:x='{x}':y=0[w];[0:v][w]overlay=0:0:format=auto[gw]"
    if ground == 'grid':
        save(_plain(), 'g'); save(_grid_image(theme), 'd')
        return files, (f"[1:v]crop={W}:{H}:x='mod({T}*7\\,40)':y='mod({T}*5\\,40)'[d];"
                       f"[0:v][d]overlay=0:0:format=auto[gw]")
    # 'still'
    if not still:
        raise ValueError("ground 'still' needs still=<official image>")
    img, pan = _still_image(still, STILL_DIMS[0] if dim is None else dim)
    save(img, 'bg')
    half = pan / 2
    return files, f"[0:v]crop={W}:{H}:x='{half:.1f}+{half:.1f}*sin(2*PI*{T}/70)':y=0[gw]"


def _run_inputs(files, secs):
    args = []
    for f in files:
        args += ['-loop', '1', '-framerate', str(FPS), '-t', f'{secs:.3f}', '-i', f]
    return args


def _ground_frame(files, graph, tmp):
    """One frame of the ground alone at the clock `t0` (already in `graph`)."""
    out = f'{tmp}/frame.png'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error'] + _run_inputs(files, 0.2)
                   + ['-filter_complex', graph + ';[gw]format=rgb24[o]', '-map', '[o]', '-frames:v', '1', out],
                   check=True)
    return Image.open(out).convert('RGB')


def text_region(graphic):
    """(x0, y0, x1, y1) of the graphic's non-transparent pixels, or the default
    text band when they cover nearly the whole frame (no usable box)."""
    a = np.array(Image.open(graphic).convert('RGBA').resize((W, H), Image.LANCZOS))[..., 3]
    ys, xs = np.where(a > 16)
    if not len(xs):
        return DEFAULT_BAND
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    if (box[2] - box[0]) * (box[3] - box[1]) > 0.85 * W * H:
        return DEFAULT_BAND
    return box


def measure(frame, region):
    """Mean luminance over `region` and the highest local (64 px box blur)
    luminance inside it."""
    L = _lum(np.array(frame))
    l8 = Image.fromarray(np.clip(L, 0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(32))
    x0, y0, x1, y1 = region
    return float(L[y0:y1, x0:x1].mean()), float(np.array(l8)[y0:y1, x0:x1].max())


def _check(ground, frame, region):
    mean, peak = measure(frame, region)
    base = measure(_plain(), region)[0]
    stats = dict(ground=ground, region=region, mean=round(mean, 1), base=round(base, 1),
                 delta=round(mean - base, 1), max_local=round(peak, 1))
    stats['ok'] = mean <= base + MEAN_MARGIN and peak < LOCAL_MAX
    return stats


def check_ground(graphic, ground, theme, seed=0, t0=0.0, still=None, region=None):
    """Render one ground frame at `t0` and measure it under the graphic's text.
    Returns the numbers (mean, base, delta, max_local, dim for 'still'); raises
    ValueError naming the ground and the numbers when it is too bright. The
    'still' ground dims harder (0.55, 0.65, 0.75) before it raises."""
    region = region or text_region(graphic)
    tmp = tempfile.mkdtemp(prefix='numbers-')
    try:
        for dim in (STILL_DIMS if ground == 'still' else (None,)):
            files, graph = _build_ground(ground, theme, seed, t0, tmp, still=still, dim=dim)
            st = _check(ground, _ground_frame(files, graph, tmp), region)
            st['dim'] = dim
            if st['ok']:
                return st
        raise ValueError(
            f"ground {ground!r} is too bright under the text {region}: mean {st['mean']} against the "
            f"plain indigo's {st['base']} (limit +{MEAN_MARGIN}), max local {st['max_local']} (limit "
            f"{LOCAL_MAX})" + (f", after dimming to {dim}" if dim else ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _resolve(ground, out, still):
    """A story about one game wears its art: with `still` the ground is 'still' (advisor, 20 Oct 2026), never a
    rotated plain style. Without it the ground rotates among the others (multi-game charts, company results)."""
    if ground is None:
        ground = 'still' if still else rotate_ground(out, allow=[g for g in GROUNDS if g != 'still'])
    return ground


def _still_dim(graphic, ground, theme, seed, t0, still):
    """Dim for the 'still' ground that passes the check (raises if none does)."""
    return check_ground(graphic, ground, theme, seed=seed, t0=t0, still=still)['dim']


def slide(graphic, secs, theme, out, seed=0, t0=0.0, fast=False, ground=None, still=None, check=True):
    """One graphic (RGBA, any 9:16 size) over the drifting ground, `secs` long,
    its drift starting at the shared clock `t0`. Returns `out`.

    `ground` is one of GROUNDS; None takes the one rested longest in the
    ledger (keyed by the file name; shots() resolves it once per Reel).
    `still` is the official image the 'still' ground blurs. The ground is
    measured under the graphic's text first (`check=False` skips it)."""
    ground = _resolve(ground, out, still)
    dim = _still_dim(graphic, ground, theme, seed, t0, still) if (check and ground == 'still') else None
    if check and ground != 'still':
        check_ground(graphic, ground, theme, seed=seed, t0=t0)
    tmp = tempfile.mkdtemp(prefix='numbers-')
    try:
        files, graph = _build_ground(ground, theme, seed, t0, tmp, still=still, dim=dim)
        Image.open(graphic).convert('RGBA').resize((W, H), Image.LANCZOS).save(f'{tmp}/f.png')
        n = len(files)
        fc = f"{graph};[gw][{n}:v]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]"
        args = ['ffmpeg', '-nostdin', '-y', '-v', 'error'] + _run_inputs(files + [f'{tmp}/f.png'], secs)
        enc = RL.DRAFT_ENC if fast else RL.FINAL_ENC
        subprocess.run(args + ['-filter_complex', fc, '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                       + enc + [out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def shots(slides, theme, name, fast=False, ground=None, still=None):
    """[(graphic file in uploads, seconds)] -> reel() shots. Each slide becomes
    uploads/numbers/<name>-<i>.mp4 on the shared drift clock (so the
    crossfades line up) and is cut in whole, focus 0.5. The ground is chosen
    once for the Reel (`ground=None` rotates through the ledger, keyed by
    `name`, so a re-render keeps it)."""
    os.makedirs(C.U + SUB, exist_ok=True)
    seed = sum(map(ord, name))
    ground = _resolve(ground, name, still)
    out, t = [], 0.0
    for i, (g, secs) in enumerate(slides):
        f = f'{SUB}/{name}-{i + 1}.mp4'
        slide(C.U + g, secs, theme, C.U + f, seed=seed, t0=t, fast=fast, ground=ground, still=still)
        out.append((f, 0.0, secs, 0.5))
        t += secs - RL.X                         # the next slide starts inside this one's crossfade
    return out


# ---------------------------------------------------------------------------
# Clip windows (Mohammad, 14 Oct 2026: "small clips in the same place of the
# image windows"). The footage plays inside the graphic's frame, muted.
# ---------------------------------------------------------------------------
def _probe_size(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height', '-of', 'csv=p=0', path], capture_output=True, text=True, check=True)
    w, h = r.stdout.strip().split(',')[:2]
    return int(w), int(h)


def _fit_filter(src, box, pixel):
    """Scale the clip to cover the box and crop the centre. `pixel` scales with
    nearest-neighbour, at the next whole-number factor when that costs under
    15% of the picture (retro screens stay crisp), else to fit."""
    bx, by, bw, bh = box
    sw, sh = src
    s = max(bw / sw, bh / sh)
    if not pixel:
        return f"scale={math.ceil(sw * s)}:{math.ceil(sh * s)}:flags=lanczos,crop={bw}:{bh}"
    f = math.ceil(s)
    if f / s <= 1.15 and s >= 1:
        return f"scale={sw * f}:{sh * f}:flags=neighbor,crop={bw}:{bh}"
    return f"scale={math.ceil(sw * s)}:{math.ceil(sh * s)}:flags=neighbor,crop={bw}:{bh}"


def window(graphic, clip, box, start, secs, out, theme, ground=None, seed=0, t0=0.0, fast=False,
           pixel=False, still=None, check=True, punch=False):
    """Footage `clip` (a file in uploads) inside the rectangle `box=(x, y, w, h)`
    of the 1080x1920 frame, under the transparent `graphic` (so its frame and
    edge draw over the clip), on the living ground. The clip is cropped to the
    box aspect from the centre and muted; `pixel=True` scales it with
    nearest-neighbour. `start` is the clip time the window opens on. If the
    clip stops early its last frame holds. `punch=True` clears the graphic's
    own pixels inside the box (for a graphic that still carries its still
    picture there). Returns `out`."""
    x, y, bw, bh = box
    ground = _resolve(ground, out, still)
    dim = _still_dim(graphic, ground, theme, seed, t0, still) if (check and ground == 'still') else None
    if check and ground != 'still':
        check_ground(graphic, ground, theme, seed=seed, t0=t0)
    tmp = tempfile.mkdtemp(prefix='numbers-')
    try:
        files, graph = _build_ground(ground, theme, seed, t0, tmp, still=still, dim=dim)
        g = Image.open(graphic).convert('RGBA').resize((W, H), Image.LANCZOS)
        if punch:
            g.paste((0, 0, 0, 0), (x, y, x + bw, y + bh))
        g.save(f'{tmp}/f.png')
        src = C.U + clip
        n = len(files)
        fit = _fit_filter(_probe_size(src), box, pixel)
        fc = (f"{graph};[{n + 1}:v]fps={FPS},{fit},setsar=1,format=yuv420p,"
              f"tpad=stop_mode=clone:stop_duration={secs:.3f}[cl];"
              f"[gw][cl]overlay={x}:{y}:format=auto[gc];"
              f"[gc][{n}:v]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]")
        args = (['ffmpeg', '-nostdin', '-y', '-v', 'error'] + _run_inputs(files + [f'{tmp}/f.png'], secs)
                + ['-ss', f'{start:.3f}', '-t', f'{secs:.3f}', '-i', src])
        enc = RL.DRAFT_ENC if fast else RL.FINAL_ENC
        subprocess.run(args + ['-filter_complex', fc, '-map', '[v]', '-an', '-t', f'{secs:.3f}',
                               '-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + enc + [out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def window_shots(items, theme, name, fast=False, ground=None, still=None, pixel=False, punch=False):
    """[(graphic, clip, box, start, secs)] (graphic and clip are files in
    uploads; a sixth item, True or False, overrides `pixel` for that window)
    -> reel() shots, like shots(): uploads/numbers/<name>-<i>.mp4 on the
    shared clock, one ground for the whole Reel."""
    os.makedirs(C.U + SUB, exist_ok=True)
    seed = sum(map(ord, name))
    ground = _resolve(ground, name, still)
    out, t = [], 0.0
    for i, it in enumerate(items):
        g, clip, box, start, secs = it[:5]
        f = f'{SUB}/{name}-{i + 1}.mp4'
        window(C.U + g, clip, box, start, secs, C.U + f, theme, ground=ground, seed=seed, t0=t, fast=fast,
               pixel=it[5] if len(it) > 5 else pixel, still=still, punch=punch)
        out.append((f, 0.0, secs, 0.5))
        t += secs - RL.X
    return out
