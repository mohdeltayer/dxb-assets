"""Game skins pilot (advisor, 20 Oct 2026; CLAUDE.md "Game skins, footage behind text, rebuilt cards").

A single-game story wears its genre's look; the house theme stays for multi-game, industry, hardware, policy and our
own series. Two genre kits are in the pilot, `scifi` and `fantasy` (the third pilot piece, the house look with footage
behind, is numgfx's 'footage' ground). Each kit's tokens live in templates/web/skins/<kit>.css, the one source for the
web-motion route (skin.html) and for this module, which draws the kit in PIL so the Arabic stays Dubai and every check in
reel.py still runs.

What a kit changes (reel(..., skin='scifi')): the top band's decoration in place of the wave lines, a plate behind the
headline, the split strip's plate, the story lines' outline colour, the line entrance (slide or rise), the shot to shot
transition, a warm light leak over each cut (fantasy), and a short sting at the cut into the first line. What never
changes: Dubai type, the play mark, the chip position, the safe zone, the grid-corner rule, the end card on the jingle,
عاجل in crimson (reel() drops the skin for it), the reading-pace and rtl checks.

Card-led templates draw their card plates with plate(im, box, kit), so a card matches the Reel's kit.

    import skins
    skins.load('scifi')['edge']           # (47, 224, 255)
    skins.plate(im, (x0, y0, x1, y1), 'fantasy')
"""
import math, os, re
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(HERE, 'web', 'skins')
KITS = ('scifi', 'fantasy')
W, H = 1080, 1920
SS = 2                                   # supersampling for the plates' thin lines
_cache = {}


def _value(v):
    v = v.strip()
    if re.fullmatch(r'#[0-9a-fA-F]{6}', v):
        return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
    m = re.fullmatch(r'(-?[\d.]+)(px|s)?', v)
    if m:
        n = float(m.group(1))
        return int(n) if m.group(2) == 'px' else n
    return v


def load(kit):
    """The kit's custom properties as a dict: colours as RGB tuples, px as int, seconds and plain numbers as float."""
    if kit not in _cache:
        if kit not in KITS + ('house',):
            raise ValueError(f'skin {kit!r}: the pilot kits are {", ".join(KITS)} (and house); the others wait for the pilot')
        text = re.sub(r'/\*.*?\*/', '', open(os.path.join(CSS, f'{kit}.css')).read(), flags=re.S)
        _cache[kit] = {k: _value(v) for k, v in re.findall(r'--([\w-]+)\s*:\s*([^;]+);', text)}
    return _cache[kit]


def _rgba(c, a):
    return tuple(c) + (max(0, min(255, int(round(a)))),)


# ---- plates -----------------------------------------------------------------------------------------------------

def _chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def plate(im, box, kit, alpha=1.0):
    """The kit's plate behind a text block, drawn onto `im` (RGBA, full frame). sci-fi: chamfered corners (top left,
    bottom right), thin scan lines inside, a cyan edge and yellow ticks on the square corners. fantasy: a soft
    parchment-dark plate with a gold double rule and small flourishes at the corners."""
    k = load(kit)
    x0, y0, x1, y1 = box
    pad = 40                                          # room for ticks and flourishes outside the box
    ox, oy = x0 - pad, y0 - pad
    lw, lh = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    lay = Image.new('RGBA', (lw * SS, lh * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    s = lambda pts: [((px - ox) * SS, (py - oy) * SS) for px, py in pts]
    rule = max(1, k.get('rule', 2)) * SS
    a = 255 * k['plate-alpha'] * alpha
    if kit == 'scifi':
        c = k['chamfer']
        poly = _chamfer(x0, y0, x1, y1, c)
        d.polygon(s(poly), fill=_rgba(k['plate'], a))
        mask = Image.new('L', lay.size, 0); ImageDraw.Draw(mask).polygon(s(poly), fill=255)
        scan = Image.new('RGBA', lay.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(scan)
        for y in range(y0, y1, max(3, k['scan-gap'])):
            ds.line(s([(x0, y), (x1, y)]), fill=_rgba(k['edge'], 255 * k['scan-alpha'] * alpha), width=SS)
        scan.putalpha(ImageChops.multiply(scan.getchannel('A'), mask)); lay.alpha_composite(scan)
        d.line(s(poly + poly[:1]), fill=_rgba(k['edge'], 210 * alpha), width=rule, joint='curve')
        t, g = k['tick'], 7                           # yellow ticks just outside the two square corners
        for (cx, cy, sx, sy) in ((x1 + g, y0 - g, -1, 1), (x0 - g, y1 + g, 1, -1)):
            d.line(s([(cx + sx * t, cy), (cx, cy), (cx, cy + sy * t)]), fill=_rgba(k['accent2'], 235 * alpha), width=rule + SS)
        d.line(s([(x0 + c + 18, y1 - 10), (x0 + c + 18 + 64, y1 - 10)]), fill=_rgba(k['accent2'], 200 * alpha), width=rule)
    elif kit == 'fantasy':
        r = k['radius']
        d.rounded_rectangle(s([(x0, y0), (x1, y1)]), radius=r * SS, fill=_rgba(k['plate'], a),
                            outline=_rgba(k['edge'], 215 * alpha), width=rule)
        g = k['rule-gap']
        d.rounded_rectangle(s([(x0 + g, y0 + g), (x1 - g, y1 - g)]), radius=max(2, r - g // 2) * SS,
                            outline=_rgba(k['edge'], 140 * alpha), width=max(SS, rule // 2 + 1))
        f = k['corner']
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            dx, dy = cx + sx * g / 2, cy + sy * g / 2      # a diamond on the corner, two small curls running along the rules
            q = f * 0.32
            d.polygon(s([(dx, dy - q), (dx + q, dy), (dx, dy + q), (dx - q, dy)]), fill=_rgba(k['edge'], 235 * alpha))
            for ax in (0, 1):
                pts = []
                for i in range(19):
                    u = i / 18
                    rr = f * (0.95 - 0.55 * u)
                    th = u * 1.6 * math.pi
                    along, across = rr * (1 - math.cos(th)) * 0.9, rr * math.sin(th) * 0.45
                    px, py = (dx + sx * (q + along), dy + sy * across) if ax == 0 else (dx + sx * across, dy + sy * (q + along))
                    pts.append((px, py))
                d.line(s(pts), fill=_rgba(k['edge'], 190 * alpha), width=max(SS, rule // 2 + 1), joint='curve')
    else:                                             # house: the strip's rounded soft band
        d.rounded_rectangle(s([(x0, y0), (x1, y1)]), radius=k.get('radius', 26) * SS, fill=_rgba(k['plate'], a),
                            outline=_rgba(k['edge'], 120 * alpha), width=rule)
    im.alpha_composite(lay.resize((lw, lh), Image.LANCZOS), (ox, oy))
    return im


# ---- the top band -------------------------------------------------------------------------------------------------

def top(im, y1, kit, seed=0):
    """The kit's decoration across the top band, fading out by y1, in place of the house wave lines."""
    k = load(kit)
    lay = Image.new('RGBA', (W * SS, y1 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fade = lambda y: max(0.0, 1 - y / y1) ** 1.3
    if kit == 'scifi':
        tint = Image.new('RGBA', (W, y1), _rgba(k['edge'], 0))         # a cool tint so the grid tile carries the kit's colour
        tint.putalpha(Image.linear_gradient('L').resize((W, y1)).transpose(Image.FLIP_TOP_BOTTOM).point(lambda v: int(v * 0.30)))
        for y in range(0, y1, k['scan-gap']):
            d.line([(0, y * SS), (W * SS, y * SS)], fill=_rgba(k['edge'], 255 * k['scan-alpha'] * 1.4 * fade(y)), width=SS)
        step = 28                                                        # the faint dot grid, top left (the chip sits right)
        for gy in range(40, int(y1 * 0.7), step):
            for gx in range(24, 360, step):
                a = 255 * k['grid-alpha'] * 2.2 * fade(gy) * (1 - gx / 380)
                d.ellipse([(gx - 2) * SS, (gy - 2) * SS, (gx + 2) * SS, (gy + 2) * SS], fill=_rgba(k['edge'], a))
        ry = int(y1 * 0.16) + (seed % 17)                                 # one broken rule across, with a yellow dash
        d.line([(0, ry * SS), (W * 0.58 * SS, ry * SS)], fill=_rgba(k['edge'], 150 * fade(ry)), width=2 * SS)
        d.line([(W * 0.62 * SS, ry * SS), (W * SS, ry * SS)], fill=_rgba(k['edge'], 90 * fade(ry)), width=2 * SS)
        d.line([(W * 0.58 * SS + 8 * SS, ry * SS), (W * 0.62 * SS - 8 * SS, ry * SS)], fill=_rgba(k['accent2'], 230 * fade(ry)), width=4 * SS)
        im.alpha_composite(tint, (0, 0))
    elif kit == 'fantasy':
        left, right = k['accent'], k['accent2']
        row = Image.new('RGB', (2, 1)); row.putpixel((0, 0), right); row.putpixel((1, 0), left)   # gold on the right, where the chip is
        wash = row.resize((W, y1), Image.BILINEAR).convert('RGBA')
        wash.putalpha(Image.linear_gradient('L').resize((W, y1)).transpose(Image.FLIP_TOP_BOTTOM)
                      .point(lambda v: int(v * k['wash-alpha'] * (v / 255) ** 0.6)))
        im.alpha_composite(wash, (0, 0))
        ph = (seed % 628) / 100
        for j, base in enumerate((0.10, 0.27, 0.44)):                    # three thin scrolls with small loops (trochoids)
            yb = y1 * base; pts = []
            for i in range(0, 241):
                u = i / 240
                th = u * 2 * math.pi * 7 + ph + j
                pts.append(((u * (W + 80) - 40 + 16 * math.sin(th)) * SS, (yb + 13 * math.cos(th) + 18 * math.sin(u * 5 + j)) * SS))
            a = 255 * k['curl-alpha'] * fade(yb)
            d.line(pts, fill=_rgba(k['edge'], a), width=2 * SS, joint='curve')
    im.alpha_composite(lay.resize((W, y1), Image.LANCZOS), (0, 0))
    return im


# ---- the rest of the kit ------------------------------------------------------------------------------------------

def chip(kit):
    return load(kit)['chip']


def line_colours(kit):
    """(outline, ink) for the story lines."""
    k = load(kit)
    return k['outline'], k['ink']


def entrance(kit):
    """(dx, dy, seconds): the story lines enter from dx px to the right and dy px below, over `seconds`."""
    k = load(kit)
    return k.get('enter-dx', 0), k.get('enter-dy', 0), k.get('enter-dur', 0.2)


def transition(kit):
    """The ffmpeg xfade transition between shots."""
    return load(kit).get('cut', 'fade')


def leak_layer(path, kit):
    """A warm light leak (fantasy) for the cuts: soft amber light from the top right and the bottom left, or None."""
    k = load(kit)
    if not isinstance(k.get('leak'), tuple):
        return None
    im = Image.new('RGBA', (W // 4, H // 4), _rgba(k['leak'], 0)); m = Image.new('L', im.size, 0); d = ImageDraw.Draw(m)
    d.ellipse([W // 4 * 0.55, -H // 4 * 0.15, W // 4 * 1.25, H // 4 * 0.35], fill=int(255 * k['leak-alpha']))
    d.ellipse([-W // 4 * 0.3, H // 4 * 0.7, W // 4 * 0.35, H // 4 * 1.1], fill=int(255 * k['leak-alpha'] * 0.6))
    im.putalpha(m.filter(ImageFilter.GaussianBlur(40)))
    im.resize((W, H), Image.BICUBIC).save(path)
    return path
