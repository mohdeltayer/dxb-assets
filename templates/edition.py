"""The `edition` Reel template (advisor, 14 Oct 2026): special and collector's
editions, bundles, limited consoles, accessories and tier contents.

The shape: a 3.5 s trailer hook with the headline (reel.py's normal cover),
then the contents one at a time on the numgfx living ground as publisher
press-render cut-outs, the hero item first and largest, each drifting in from
the right with a soft shadow, its name in Dubai Bold 64 and an optional
one-line note in Dubai Medium 44 in the body colour, 2.5 to 3 s each, four to
six items; then ONE composition frame of every item with the price strip
pinned low (price, date, where; the strip only, never a line); 2 s of
footage under the closing line; the end card. The trailer's music runs under
the whole Reel (`track=`). Gold theme for premium editions, otherwise the
story's theme; chip رسمي or السعر.

This module builds the middle of that Reel as ordinary shots:

    items = [('deluxe.png', 'النسخة الفاخرة', 'تضم كل المحتوى'),
             ('artbook.png', 'كتاب الفن', None), ...]       # png files in uploads
    mid = edition.shots(items, 'gold', 'game-collectors')    # products + composition
    reel([hook] + mid + [closing], ..., strip=[...])         # by hand, or
    reel([hook, closing], ..., products=items, strip=[...])  # with the reel.py hook

`products()` writes one clip per item and `composition()` the closing frame,
all under uploads/numbers/ (so reel.py treats them as our own graphics: no
picture finish) on one ground and one drift clock, exactly as numgfx.shots does.
`cutout()` prepares a press render: transparent PNG from a plain white or
black background.
"""
import os, shutil, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cards as C, fast_ar as A, ig_ar as G, reel as RL, numgfx as NG

W, H = RL.W, RL.H
SAFE_L, SAFE_R = G.SAFE_LEFT, W - G.SAFE_RIGHT        # x 96 to 910
SAFE_T, SAFE_B = G.SAFE_TOP, G.SAFE_BOTTOM            # y 285 to 1480
FPS = NG.FPS
MIN_ITEMS, MAX_ITEMS = 4, 6
HERO_FRAC, ITEM_FRAC = 0.70, 0.55     # item width as a share of the safe width (814 px)
HERO_MAXH, ITEM_MAXH = 720, 580       # tall items (an art book) are limited by height instead
NAME_SIZE, NOTE_SIZE = 64, 44
DRIFT_AT, DRIFT_SECS = 0.30, 0.60     # drift starts after the crossfade; about 0.6 s, ease-out
TEXT_AT, TEXT_FADE = 0.55, 0.35
PAD = 110                              # room round an item for its shadow
RULE_W = 44                            # the little accent rule above the name (as in the credit line)


# ---------------------------------------------------------------------------
# Cut-outs
# ---------------------------------------------------------------------------
def _trim(im, thresh=8):
    a = np.asarray(im.getchannel('A'))
    ys, xs = np.where(a > thresh)
    if not len(xs):
        raise ValueError('the cut-out is empty (nothing opaque)')
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def _runs(reach, near, axis):
    """One propagation pass: every run of `near` pixels along `axis` that holds
    a reached pixel becomes reached."""
    a, r = (near, reach) if axis == 1 else (near.T, reach.T)
    a = np.pad(a, ((0, 0), (0, 1))); r = np.pad(r, ((0, 0), (0, 1)))     # a False column ends every row
    flat = a.ravel()
    start = flat & ~np.concatenate([[False], flat[:-1]])
    ids = np.cumsum(start) * flat
    hit = np.zeros(int(ids.max()) + 1, bool)
    hit[ids[r.ravel() & flat]] = True; hit[0] = False
    out = hit[ids].reshape(a.shape)[:, :-1]
    return out if axis == 1 else out.T


def _border_reach(near):
    """The part of the boolean mask `near` connected (4-way) to the image border.
    Row and column runs alternate until nothing changes: numpy only, no scipy."""
    reach = np.zeros_like(near)
    for sl in (np.s_[0, :], np.s_[-1, :], np.s_[:, 0], np.s_[:, -1]):
        reach[sl] = near[sl]
    for _ in range(400):
        new = _runs(_runs(reach, near, 1), near, 0)
        if (new == reach).all():
            break
        reach = new
    return reach


def cutout(src, out_png, tol=28, feather=1.0):
    """Press render -> transparent PNG, trimmed to the item. Returns
    (out_png, method) and prints which method was used:

    'already transparent'   the file has real transparency; only trimmed
    'rembg'                 the rembg package, when installed
    'flood-fill (near-white)' / '(near-black)'   the PIL fallback: the background
        colour is read from the border, every pixel within `tol` of it that is
        connected to the border goes (a loop or hole inside the item stays), the
        mask is eroded one pixel against the halo and feathered by `feather` px.
    Raises ValueError when the border is neither near-white nor near-black
    (send a transparent PNG, or install rembg when disk allows). A soft grey
    studio shadow on white may survive the fallback; check the result."""
    im = Image.open(src)
    rgba = im.convert('RGBA')
    a = np.asarray(rgba.getchannel('A'))
    if (a < 250).mean() > 0.01:
        method, out = 'already transparent', rgba
    else:
        try:
            from rembg import remove                      # not installed on this container (disk < 600 MB)
            method, out = 'rembg', remove(im.convert('RGB')).convert('RGBA')
        except ImportError:
            method, out = None, None
        if out is None:
            rgb = np.asarray(im.convert('RGB')).astype(np.int16)
            border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            white = (border.min(axis=1) >= 235).mean(); black = (border.max(axis=1) <= 25).mean()
            if max(white, black) < 0.85:
                raise ValueError(f'{src}: the border is neither plain white nor plain black '
                                 f'(white {white:.0%}, black {black:.0%}); send a transparent PNG or use rembg')
            kind = 'near-white' if white >= black else 'near-black'
            pick = border[(border.min(axis=1) >= 235) if kind == 'near-white' else (border.max(axis=1) <= 25)]
            bg = np.median(pick, axis=0)
            near = np.abs(rgb - bg).max(axis=2) <= tol
            fg = ~_border_reach(near)
            m = Image.fromarray((fg * 255).astype(np.uint8))
            m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # specks and hairline halos
            m = m.filter(ImageFilter.MinFilter(3))                                       # one pixel in against the halo
            m = m.filter(ImageFilter.GaussianBlur(feather))
            out = im.convert('RGB').convert('RGBA'); out.putalpha(m)
            method = f'flood-fill ({kind})'
    out = _trim(out)
    out.save(out_png)
    print(f'cutout: {os.path.basename(out_png)} by {method}')
    return out_png, method


# ---------------------------------------------------------------------------
# Text and item layers
# ---------------------------------------------------------------------------
def _probe():
    return ImageDraw.Draw(Image.new('L', (W, H)))


def _lines(text, font, room, maxlines, what):
    """Wrap one name or note: '|' sets breaks by hand, otherwise the same
    wrapper as the reel lines, two lines balanced so no word hangs alone.
    Every visual line must open on an Arabic word."""
    probe = _probe()
    tw = lambda s: probe.textlength(s, font=font, **G.AR)
    if '|' in text:
        lines = [x.strip() for x in text.split('|')]
    else:
        lines = G._wrap(probe, text, font, room)
        if len(lines) == 2:
            words = G._tokens(text)
            k = min(range(1, len(words)), key=lambda k: max(tw(' '.join(words[:k])), tw(' '.join(words[k:]))))
            lines = [' '.join(words[:k]), ' '.join(words[k:])]
    if len(lines) > maxlines:
        raise ValueError(f'{what} runs to {len(lines)} lines (limit {maxlines}): {text}')
    for x in lines:
        if tw(x) > room:
            raise ValueError(f'{what} runs out of the safe zone: {x}')
    RL.rtl_starts(lines, what)
    return lines


def _text_size(name, note, name_size, note_size):
    """(name lines, note lines, block height) for a name and its note."""
    room = SAFE_R - SAFE_L
    nl = _lines(name, A.F('Bold', name_size), room, 2, 'item name')
    ol = _lines(note, A.F('Medium', note_size), room, 1, 'item note') if note else []
    h = RULE_W // 11 + 22 + name_size + (len(nl) - 1) * round(name_size * 1.3)
    if ol:
        h += 22 + note_size + 12
    return nl, ol, h + 16


def _put_text(im, lines, font, x, y, fill, anchor, step, shadow=True):
    """Draw lines with a soft ground-coloured shadow under them. Returns the y of
    the last baseline."""
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    for i, ln in enumerate(lines):
        d.text((x, y + i * step), ln, font=font, fill=255, anchor=anchor, **G.AR)
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.75))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 255)); lay.putalpha(sh); im.alpha_composite(lay)
    lay = Image.new('RGBA', (W, H), fill + (255,)); lay.putalpha(mask); im.alpha_composite(lay)
    return y + (len(lines) - 1) * step


def text_layer(name, note, y_top, accent, name_size=NAME_SIZE, note_size=NOTE_SIZE):
    """One item's name (Dubai Bold) and note (Dubai Medium, body colour), right-
    aligned on the safe edge under a small accent rule, the block starting at
    `y_top`. Returns (RGBA layer 1080x1920, (x0, y0, x1, y1) of the block)."""
    nl, ol, h = _text_size(name, note, name_size, note_size)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([SAFE_R - RULE_W, y_top, SAFE_R, y_top + 4], fill=accent + (255,))
    step = round(name_size * 1.3)
    base = y_top + 4 + 22 + name_size
    last = _put_text(im, nl, A.F('Bold', name_size), SAFE_R, base, A.INK, 'rs', step)
    if ol:
        _put_text(im, ol, A.F('Medium', note_size), SAFE_R, last + 22 + note_size, A.BODY, 'rs', step)
    return im, (SAFE_L, y_top, SAFE_R, y_top + h)


def _prep(png, target_w, max_h, lowres_ok=False):
    """Load an item from uploads (or a path), trim, scale to `target_w` wide
    unless that is taller than `max_h`. An enlargement beyond reel.MAX_ZOOM
    stops the build (a soft press render looks soft at this size)."""
    p = png if os.path.isabs(png) else C.U + png
    im = _trim(Image.open(p).convert('RGBA'))
    s = min(target_w / im.width, max_h / im.height)
    if s > RL.MAX_ZOOM and not lowres_ok:
        raise ValueError(f'{png}: enlarged {s:.1f}x to fit ({im.width}x{im.height} to '
                         f'{round(im.width * s)}x{round(im.height * s)}); find a larger render or pass lowres_ok=True')
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def _with_shadow(item, blur=24, dy=26, opacity=0.62):
    """The item over its own soft drop shadow, on a transparent layer PAD larger
    on every side."""
    lay = Image.new('RGBA', (item.width + 2 * PAD, item.height + 2 * PAD), (0, 0, 0, 0))
    sh = Image.new('L', lay.size, 0)
    sh.paste(item.getchannel('A'), (PAD, PAD + dy))
    sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    dark = Image.new('RGBA', lay.size, (4, 3, 16, 255)); dark.putalpha(sh)
    lay.alpha_composite(dark)
    lay.alpha_composite(item, (PAD, PAD))
    return lay


def _check_items(items, loose, what='items'):
    n = len(items)
    if not (MIN_ITEMS <= n <= MAX_ITEMS or (loose and 2 <= n <= MAX_ITEMS)):
        raise ValueError(f'an edition Reel shows {MIN_ITEMS} to {MAX_ITEMS} {what}, got {n}')
    for it in items:
        if len(it) != 3:
            raise ValueError(f'each item is (png, name, note or None), got {it!r}')


def _accent(theme):
    return G.ACCENTS[theme]


# ---------------------------------------------------------------------------
# Rendering one clip: living ground + (drifting) art layer + text layer
# ---------------------------------------------------------------------------
def _render(art, text, secs, theme, out, ground, seed, t0, region, drift=None, fast=False, check=True):
    """art, text: RGBA PIL layers. `drift` = (x, y) the art layer's final top-left
    when it should drift in from the right; None lays `art` full-frame, still."""
    tmp = tempfile.mkdtemp(prefix='edition-')
    try:
        tp = f'{tmp}/text.png'; text.save(tp)
        if check:
            NG.check_ground(tp, ground, theme, seed=seed, t0=t0, region=region)
        files, graph = NG._build_ground(ground, theme, seed, t0, tmp)
        n = len(files)
        art.save(f'{tmp}/art.png')
        if drift:
            x, y = drift
            xe = f"({x}+({W}-{x})*pow(1-min(1\\,max(0\\,(t-{DRIFT_AT})/{DRIFT_SECS}))\\,3))"
            ov = f"overlay=x='{xe}':y={y}:eval=frame:format=auto"
        else:
            ov = 'overlay=0:0:format=auto'
        fc = (f"{graph};[{n}:v]format=rgba[art];[gw][art]{ov}[a];"
              f"[{n + 1}:v]format=rgba,fade=t=in:st={TEXT_AT}:d={TEXT_FADE}:alpha=1[tx];"
              f"[a][tx]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]")
        args = (['ffmpeg', '-nostdin', '-y', '-v', 'error'] +
                NG._run_inputs(files + [f'{tmp}/art.png', tp], secs))
        enc = RL.DRAFT_ENC if fast else RL.FINAL_ENC
        subprocess.run(args + ['-filter_complex', fc, '-map', '[v]', '-t', f'{secs:.3f}', '-c:v', 'libx264',
                               '-pix_fmt', 'yuv420p'] + enc + [out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def _setup(name, ground):
    os.makedirs(C.U + NG.SUB, exist_ok=True)
    return NG._resolve(ground, name, None), sum(map(ord, name))   # never 'still': no official image here


def clock(n, secs=2.8):
    """Where the shared drift clock stands after `n` product clips (each one
    starts inside the previous one's crossfade)."""
    return n * (secs - RL.X)


# ---------------------------------------------------------------------------
# products(): one clip per item
# ---------------------------------------------------------------------------
def products(items, theme, name, secs=2.8, note_size=NOTE_SIZE, name_size=NAME_SIZE, fast=False,
             ground=None, t0=0.0, lowres_ok=False, loose=False, check=True):
    """items: [(png, name_text, note_or_None)], png a transparent cut-out in uploads
    (see cutout()). One 1080x1920 clip per item, `secs` long, on the living ground
    (the ground style rotates through the ledger, keyed by `name`; the wave clock
    runs on from `t0` and continues across the items, as numgfx.shots does). The
    cut-out drifts in from the right over about 0.6 s (ease-out) with a soft
    drop shadow, the first (hero) at about 70% of the safe width and the rest at
    55%; the name (Dubai Bold `name_size`) and note (Dubai Medium `note_size`,
    body colour) fade in under it, right-aligned in the safe zone. Every name
    and note line must open on an Arabic word, and the pair must be readable
    in `secs` (reel.read_secs). Returns reel() shots
    [(uploads/numbers/<name>-prod-<i>.mp4, 0.0, secs, 0.5), ...]."""
    _check_items(items, loose)
    ground, seed = _setup(name, ground)
    acc = _accent(theme)
    out, t = [], t0
    span = SAFE_R - SAFE_L
    for i, (png, nm, note) in enumerate(items):
        hero = i == 0
        need = RL.read_secs(nm.replace('|', ' ') + (' ' + note if note else ''))
        if secs < need - 0.05:
            raise ValueError(f'item {i + 1} needs {need:.1f}s to read, the clip is {secs:.1f}s: {nm}')
        item = _prep(png, round(span * (HERO_FRAC if hero else ITEM_FRAC)), HERO_MAXH if hero else ITEM_MAXH, lowres_ok)
        nl, ol, th = _text_size(nm, note, name_size, note_size)
        gap = 44
        block = item.height + gap + th
        top = SAFE_T + max(0, (SAFE_B - SAFE_T - block) // 2) - 14
        art = _with_shadow(item)
        ax = (SAFE_L + SAFE_R) // 2 - art.width // 2
        ay = top - PAD
        text, region = text_layer(nm, note, top + item.height + gap, acc, name_size, note_size)
        f = f'{NG.SUB}/{name}-prod-{i + 1}.mp4'
        _render(art, text, secs, theme, C.U + f, ground, seed, t, region, drift=(ax, ay), fast=fast, check=check)
        out.append((f, 0.0, secs, 0.5))
        t += secs - RL.X
    return out


# ---------------------------------------------------------------------------
# composition(): every item on one frame, room kept for the price strip
# ---------------------------------------------------------------------------
COMP_NAME = (46, 34)          # label sizes: hero, the rest (they shrink to COMP_MIN to fit)
COMP_MIN = 28


def _label_lines(text, size, room):
    """A composition label: up to two lines, centred, shrinking to COMP_MIN."""
    for s in range(size, COMP_MIN - 1, -2):
        try:
            return s, _lines(text, A.F('Bold', s), room, 2, 'label')
        except ValueError as e:
            if 'opens on' in str(e):
                raise
            last = e
    raise last


def _grid(n_rest):
    """(rows, cols) for the rest of the items: one row up to three, else two."""
    if n_rest <= 3:
        return 1, n_rest
    return 2, (n_rest + 1) // 2


def composition(items, theme, name, secs=3.0, fast=False, ground=None, t0=None, strip_room=True,
                lowres_ok=False, loose=False, check=True, item_secs=2.8):
    """One frame with every item laid out: the hero largest on top, centred, the
    rest in a row (up to three) or a grid of two rows under it, bottoms on a
    common line, a centred label under each (names only, no notes). Same ground
    and drift clock as products() (`t0` defaults to where `len(items)` clips of
    `item_secs` leave the clock). `strip_room=True` keeps everything above the
    price strip's top (reel.STRIP_TOP), because the reel.py hook pins the strip
    on this frame. Returns the reel() shot (uploads/numbers/<name>-comp.mp4,
    0.0, secs, 0.5)."""
    _check_items(items, loose)
    ground, seed = _setup(name, ground)
    t0 = clock(len(items), item_secs) if t0 is None else t0
    acc = _accent(theme)
    span = SAFE_R - SAFE_L
    top = SAFE_T + 6
    bottom = (RL.STRIP_TOP - 30) if strip_room else SAFE_B
    avail = bottom - top
    rest = items[1:]
    rows, cols = _grid(len(rest))
    gx, gy_hero, gy_rows = 24, 34, 30
    cell_w = (span - gx * (cols - 1)) / cols
    hs, hl = _label_lines(items[0][1], COMP_NAME[0], span)
    labs = [_label_lines(it[1], COMP_NAME[1], cell_w - 8) for it in rest]
    # one label size for the whole row of the rest: the smallest any needed
    rs = min(s for s, _ in labs); labs = [(rs, _lines(it[1], A.F('Bold', rs), cell_w - 8, 2, 'label')) for it in rest]
    lstep_h, lstep_r = round(hs * 1.3), round(rs * 1.3)
    hero_lab_h = 18 + len(hl) * lstep_h
    rest_lab_h = 16 + max(len(ls) for _, ls in labs) * lstep_r
    free = avail - hero_lab_h - rows * rest_lab_h - gy_hero - (rows - 1) * gy_rows
    hero_h = min(HERO_MAXH, int(free * (0.52 if rows == 1 else 0.42)))
    row_h = int((free - hero_h) / rows)
    hero = _prep(items[0][0], round(span * HERO_FRAC), hero_h, lowres_ok)
    rest_im = [_prep(it[0], int(cell_w - 12), row_h, lowres_ok) for it in rest]
    cap = hero.width * hero.height                     # the hero stays the largest
    big = max(im.width * im.height for im in rest_im)
    if big > 0.8 * cap:
        k = (0.8 * cap / big) ** 0.5
        rest_im = [im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS) for im in rest_im]
    block = hero.height + hero_lab_h + gy_hero + rows * row_h + (rows - 1) * gy_rows + rest_lab_h * rows
    y = top + max(0, (avail - block) // 2)
    art = Image.new('RGBA', (W, H), (0, 0, 0, 0)); text = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cx = (SAFE_L + SAFE_R) // 2

    def put(im, cx_, bottom_y):
        lay = _with_shadow(im, blur=18, dy=18)
        art.alpha_composite(lay, (round(cx_ - lay.width / 2), bottom_y - im.height - PAD))

    put(hero, cx, y + hero.height)
    ly = y + hero.height + 18 + hs
    _put_text(text, hl, A.F('Bold', hs), cx, ly, A.INK, 'ms', lstep_h)
    d = ImageDraw.Draw(text)
    d.rectangle([cx - RULE_W // 2, ly + (len(hl) - 1) * lstep_h + 22, cx + RULE_W // 2, ly + (len(hl) - 1) * lstep_h + 26],
                fill=acc + (255,))
    y += hero.height + hero_lab_h + gy_hero
    for r in range(rows):
        row = rest_im[r * cols:(r + 1) * cols]; rl = labs[r * cols:(r + 1) * cols]
        n = len(row)
        x0 = SAFE_L + (span - (n * cell_w + (n - 1) * gx)) / 2
        for k, (im, (_, ls)) in enumerate(zip(row, rl)):
            ccx = x0 + cell_w / 2 + k * (cell_w + gx)
            put(im, ccx, y + row_h)
            _put_text(text, ls, A.F('Bold', rs), ccx, y + row_h + 14 + rs, A.INK, 'ms', lstep_r)
        y += row_h + rest_lab_h + gy_rows
    ys = np.nonzero(np.asarray(text.getchannel('A')).max(axis=1) > 16)[0]
    region = (SAFE_L, int(ys.min()), SAFE_R, int(ys.max()) + 1)
    f = f'{NG.SUB}/{name}-comp.mp4'
    _render(art, text, secs, theme, C.U + f, ground, seed, t0, region, drift=None, fast=fast, check=check)
    return (f, 0.0, secs, 0.5)


def shots(items, theme, name, secs=2.8, comp_secs=3.0, fast=False, ground=None, lowres_ok=False, loose=False, **kw):
    """products() then composition() on one ground and one clock: the whole
    middle of the Reel as reel() shots, the composition last. `kw` goes to
    products() (note_size, name_size)."""
    _check_items(items, loose)
    ground, _ = _setup(name, ground)
    mid = products(items, theme, name, secs=secs, fast=fast, ground=ground, lowres_ok=lowres_ok, loose=loose, **kw)
    mid.append(composition(items, theme, name, secs=comp_secs, fast=fast, ground=ground, t0=clock(len(items), secs),
                           lowres_ok=lowres_ok, loose=loose))
    return mid
