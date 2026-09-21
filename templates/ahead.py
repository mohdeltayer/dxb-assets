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


def _neon(im, xy, text, font, color, glow=18, anchor='mm'):
    """Outlined neon lettering over a soft glow, the September treatment."""
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=color + (255,),
                               anchor=anchor, stroke_width=3,
                               stroke_fill=color + (255,))
    halo = layer.filter(ImageFilter.GaussianBlur(glow)).split()[3]
    im.paste(Image.new('RGB', im.size, color), (0, 0),
             halo.point(lambda a: int(a * 0.55)))
    sharp = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sharp).text(xy, text, font=font, fill=(0, 0, 0, 0),
                               anchor=anchor, stroke_width=4,
                               stroke_fill=color + (255,))
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


def ahead(title_lines, items, footer, out, theme='halloween'):
    t = THEMES[theme]
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
            s = rng.choice((1, 1, 1, 2))
            d.ellipse([sx, sy, sx + s, sy + s],
                      fill=tuple(min(255, c + 90) for c in t['bg1']))

    tf = ImageFont.truetype(os.path.join(FONTS, t['font']), t['title_size'])
    ty = 130
    for line in title_lines:
        _neon(im, (W // 2, ty), line, tf, t['title'])
        ty += 130

    tw, th, gap = 340, 420, 44
    x0 = (W - (3 * tw + 2 * gap)) // 2
    rows = (410, 880)
    for i, (date, name, sub, image) in enumerate(items[:6]):
        col, row = i % 3, i // 3
        _tile(im, (x0 + col * (tw + gap), rows[row], tw, th), t,
              t['borders'][i % len(t['borders'])], date, name, sub, image)

    d = ImageDraw.Draw(im)
    d.text((W // 2, H - 24), footer, font=F(18, 500), fill=t['foot'], anchor='mm')
    im.save(out)
    return out
