"""The lookout card: a themed month-ahead (or week-ahead) grid.

Separate from the flex.py card system. Same canvas as the September
original (1320x1389): a neon title, a 2x3 grid of tiles, each with art on
top, a big date, an event name and a one-line sub, and a footer for the
timezone note. `theme` picks the palette and title font; the geometry never
changes, so a new month is a theme swap and six new items.

    ahead(['THE MONTH', 'AHEAD.'], items, footer, out, theme='halloween')

`items` is up to six (date, name, sub, image|None). `sub` is a string, or
a (platforms, note) pair for a second line: every tile should name its
platforms the same way, and notes like a demo date go on the line below. With no image the art
panel is a graded wash in the tile's border colour, which is the placeholder
to review layout against before real art goes in.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import flex
from flex import F

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
W, H = 1320, 1389

THEMES = {
    # October: pumpkin, candy, slime, blood, bone, amber on black-purple.
    'halloween': dict(
        bg0=(13, 7, 22), bg1=(26, 11, 46), title=(255, 122, 26),
        font='Bungee.ttf', title_size=118,
        borders=[(255, 122, 26), (155, 77, 255), (124, 255, 74),
                 (232, 48, 58), (242, 234, 216), (255, 176, 32)],
        tile=(22, 12, 40), ink=(255, 255, 255), sub=(160, 150, 180),
        foot=(120, 110, 140), stars=True),
    # September's look, kept so the original can be re-cut.
    'neon': dict(
        bg0=(20, 10, 50), bg1=(28, 14, 66), title=(255, 60, 200),
        font='Bungee.ttf', title_size=118,
        borders=[(255, 200, 60), (255, 80, 180), (220, 200, 255),
                 (80, 200, 255), (255, 150, 60), (180, 255, 80)],
        tile=(30, 18, 70), ink=(255, 255, 255), sub=(170, 160, 200),
        foot=(130, 120, 160), stars=True),
}


def _pumpkin(draw, box, color, sw):
    """A jack-o'-lantern outline sized to a letter box, same stroke as the
    text so it reads as the O it replaces.

    Three side-by-side lobes give the bumpy silhouette and the rib lines
    where they overlap; the face is filled, like a lit cut-out, so it still
    reads at feed size.
    """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    top = y0 + h * 0.16                      # stem pokes above this
    bot = y1
    bh = bot - top
    # lobes: centre is tallest, sides a little shorter and pushed outward
    lobes = [(cx - w * 0.28, top + bh * 0.06, w * 0.62),
             (cx + w * 0.28, top + bh * 0.06, w * 0.62),
             (cx,            top,             w * 0.70)]
    for lx, lt, lw in lobes:
        draw.ellipse([lx - lw / 2, lt, lx + lw / 2, bot], outline=color, width=sw)
    # stem: short, thick, leaning right
    draw.line([(cx - w * 0.02, top + sw), (cx + w * 0.06, y0 + h * 0.03),
               (cx + w * 0.16, y0 + h * 0.01)], fill=color, width=sw + 3,
              joint='curve')
    # face: filled cut-outs
    ey = top + bh * 0.40
    ew, eh = w * 0.11, bh * 0.16
    for ex in (cx - w * 0.20, cx + w * 0.20):
        draw.polygon([(ex, ey - eh * 0.6), (ex - ew, ey + eh * 0.5),
                      (ex + ew, ey + eh * 0.5)], fill=color)
    my = top + bh * 0.70
    mw, mh = w * 0.32, bh * 0.10
    draw.polygon([(cx - mw, my - mh), (cx - mw * 0.55, my + mh),
                  (cx - mw * 0.2, my), (cx + mw * 0.2, my),
                  (cx + mw * 0.55, my + mh), (cx + mw, my - mh),
                  (cx + mw * 0.6, my - mh * 0.2), (cx, my + mh * 0.35),
                  (cx - mw * 0.6, my - mh * 0.2)], fill=color)


def _neon(im, xy, text, font, color, glow=18, anchor='mm', mark='@',
          glyph_level=1.0):
    """Outlined neon lettering over a soft glow, the September treatment.

    A `mark` character in `text` is replaced by a pumpkin drawn in the same
    stroke, sized to the font's O, so 'M@NTH' reads as MONTH in costume.
    `glyph_level` scales the pumpkin's brightness and glow on its own, which
    is what the flicker animation drives; the letters never dim.
    """
    parts = text.split(mark)
    probe = ImageDraw.Draw(im)
    o_w = probe.textlength('O', font=font)
    widths = [probe.textlength(t, font=font) for t in parts]
    total = sum(widths) + o_w * (len(parts) - 1)
    cx, cy = xy
    x = cx - total / 2
    cap = probe.textbbox((0, 0), 'M', font=font)
    top, bot = cy - (cap[3] - cap[1]) / 2, cy + (cap[3] - cap[1]) / 2

    def paint(sw, fill_alpha, target, want):
        d = ImageDraw.Draw(target)
        px = x
        for i, t in enumerate(parts):
            if t:
                if want == 'text':
                    d.text((px, cy), t, font=font, fill=color + (fill_alpha,),
                           anchor='lm', stroke_width=sw,
                           stroke_fill=color + (255,))
                px += widths[i]
            if i < len(parts) - 1:
                if want == 'glyph':
                    _pumpkin(d, (px - o_w * 0.04, top - (bot - top) * 0.08,
                                 px + o_w * 1.04, bot), color + (255,), sw)
                px += o_w

    gl = max(0.0, min(1.0, glyph_level))
    dim = tuple(int(c * gl) for c in color)
    for want, lvl, col in (('text', 1.0, color), ('glyph', gl, dim)):
        layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
        paint(3, 255, layer, want)
        halo = layer.filter(ImageFilter.GaussianBlur(glow)).split()[3]
        im.paste(Image.new('RGB', im.size, col), (0, 0),
                 halo.point(lambda a, k=lvl: int(a * 0.55 * k)))
        sharp = Image.new('RGBA', im.size, (0, 0, 0, 0))
        paint(4, 0, sharp, want)
        if want == 'glyph' and gl < 1.0:
            r, g, b, a = sharp.split()
            sharp = Image.merge('RGBA', (r.point(lambda v: int(v * gl)),
                                         g.point(lambda v: int(v * gl)),
                                         b.point(lambda v: int(v * gl)), a))
        im.paste(sharp, (0, 0), sharp)


def _tile(im, box, t, border, date, name, sub, image):
    x, y, w, h = box
    r = 28
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([x, y, x + w, y + h], radius=r,
                                           outline=border + (255,), width=6)
    halo = glow.filter(ImageFilter.GaussianBlur(14)).split()[3]
    im.paste(Image.new('RGB', im.size, border), (0, 0),
             halo.point(lambda a: int(a * 0.7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=t['tile'],
                        outline=border, width=4)

    # Art panel: top half, rounded on top only. Contain-and-cover the
    # supplied image; without one, a graded wash in the border colour.
    aw, ah = w - 8, h // 2
    mask = Image.new('L', (aw, ah), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, aw, ah + r], radius=r - 4,
                                           fill=255)
    if image:
        src = Image.open(flex.C.U + image).convert('RGB')
        k = max(aw / src.width, ah / src.height)
        src = src.resize((int(src.width * k) + 1, int(src.height * k) + 1),
                         Image.LANCZOS)
        ox, oy = (src.width - aw) // 2, (src.height - ah) // 2
        art = src.crop((ox, oy, ox + aw, oy + ah))
    else:
        base = tuple(int(c * 0.38) for c in border)
        art = Image.new('RGB', (aw, ah), base)
        ad = ImageDraw.Draw(art)
        for i in range(ah):
            ad.line([0, i, aw, i],
                    fill=tuple(int(c * (1 - 0.45 * i / ah)) for c in base))
    im.paste(art, (x + 4, y + 4), mask)

    cx = x + w // 2
    lines = [sub] if isinstance(sub, str) else [l for l in sub if l]
    d.text((cx, y + h * 0.64), date, font=F(74, 900), fill=t['ink'], anchor='mm')
    d.text((cx, y + h * 0.77), name.upper(), font=F(24, 800), fill=t['ink'],
           anchor='mm')
    ys = (0.87,) if len(lines) == 1 else (0.855, 0.925)
    for ln, fy in zip(lines, ys):
        d.text((cx, y + h * fy), ln, font=F(18, 500), fill=t['sub'], anchor='mm')


def _body(items, footer, t):
    """Everything except the title: background, stars, tiles, footer."""
    im = Image.new('RGB', (W, H), t['bg0'])
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([0, y, W, y],
               fill=tuple(int(a + (b - a) * k) for a, b in zip(t['bg0'], t['bg1'])))
    if t['stars']:
        import random
        rng = random.Random(7)
        for _ in range(90):
            sx, sy = rng.randrange(W), rng.randrange(H)
            sz = rng.choice((1, 1, 1, 2))
            d.ellipse([sx, sy, sx + sz, sy + sz],
                      fill=tuple(min(255, c + 90) for c in t['bg1']))
    tw, th, gap = 340, 420, 44
    x0 = (W - (3 * tw + 2 * gap)) // 2
    rows = (410, 880)
    for i, (date, name, sub, image) in enumerate(items[:6]):
        col, row = i % 3, i // 3
        _tile(im, (x0 + col * (tw + gap), rows[row], tw, th), t,
              t['borders'][i % len(t['borders'])], date, name, sub, image)
    d = ImageDraw.Draw(im)
    d.text((W // 2, H - 24), footer, font=F(18, 500), fill=t['foot'], anchor='mm')
    return im


def _title(im, title_lines, t, glyph_level=1.0):
    tf = ImageFont.truetype(os.path.join(FONTS, t['font']), t['title_size'])
    ty = 130
    for line in title_lines:
        _neon(im, (W // 2, ty), line, tf, t['title'], glyph_level=glyph_level)
        ty += 130


def ahead(title_lines, items, footer, out, theme='halloween'):
    t = THEMES[theme]
    im = _body(items, footer, t)
    _title(im, title_lines, t)
    im.save(out)
    return out


def _flicker(n, seed=3):
    """Per-frame brightness for the glyph: steady with a faint hum, the odd
    dip, a rare double-blink, and full brightness at both ends so the loop
    is seamless."""
    import random
    rng = random.Random(seed)
    lv = [1.0] * n
    i = 6
    while i < n - 8:
        r = rng.random()
        if r < 0.035:                        # single dip, 1-3 frames
            k = rng.randint(1, 3); lvl = rng.uniform(0.25, 0.65)
            for j in range(k): lv[i + j] = lvl
            i += k + rng.randint(4, 14)
        elif r < 0.045:                      # double blink
            for j, l in enumerate((0.3, 1.0, 0.2)): lv[i + j] = l
            i += 3 + rng.randint(8, 20)
        else:
            i += 1
    return [max(0.0, min(1.0, l * rng.uniform(0.97, 1.0))) if 0 < i < n - 1 else 1.0
            for i, l in enumerate(lv)]


def ahead_video(title_lines, items, footer, out, theme='halloween',
                seconds=8, fps=30, seed=3):
    """The same card as `ahead`, as a looping MP4 where the title glyph
    flickers like a neon tube. Written to a .mp4 path via ffmpeg."""
    import subprocess, tempfile
    if not out.lower().endswith('.mp4'):
        raise ValueError('ahead_video writes an .mp4')
    t = THEMES[theme]
    base = _body(items, footer, t)
    n = seconds * fps
    levels = _flicker(n, seed)
    tmp = tempfile.mkdtemp(prefix='dxbahead-')
    # yuv420p needs even dimensions; H is 1389, so pad one row of background.
    canvas_h = H + (H % 2)
    for i, lvl in enumerate(levels):
        fr = base.copy()
        _title(fr, title_lines, t, glyph_level=lvl)
        if canvas_h != H:
            pad = Image.new('RGB', (W, canvas_h), t['bg1'])
            pad.paste(fr, (0, 0)); fr = pad
        fr.save(os.path.join(tmp, f'{i:04d}.png'))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(fps),
                    '-i', os.path.join(tmp, '%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19',
                    '-movflags', '+faststart', out], check=True)
    return out, levels
