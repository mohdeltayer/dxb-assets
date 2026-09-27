"""DXB-KNIGHT explainer clip (trial, 27 Sep 2026).

Steps through a patent's own figures, one step per figure, with the step
text beside the drawing, so a reader sees the mechanism the filing
describes and nothing it does not. 1600 x 900, the fast-lane frame.

steps: [(figure_png, heading, text, extras)], extras a dict that may hold
'ring': (x, y, r) in panel pixels for a pulsing azure ring.
"""
import math
import subprocess

from PIL import Image, ImageDraw
import cards as C
import flex

W, H = 1600, 900
M = 60
PANEL = (M, 120, 900, 790)          # drawing, on white
TEXT_X = 950
FPS = 30


def _wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if cur and d.textlength(t, font=f) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + [cur] if cur else lines


def _base(bg, acc, title, source, date):
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    d.text((M, 62), title.upper(), font=flex.F(34, 800), fill=acc, anchor='lm')
    d.rectangle([0, H - 84, W, H - 82], fill=flex.lift(bg, 0.15))
    crest = Image.open(C.CREST).convert('RGBA').resize((44, 44), Image.LANCZOS)
    im.paste(crest, (M, H - 64), crest)
    d = ImageDraw.Draw(im)
    muted = flex.lift(flex.BODY, -0.25, bg)
    d.text((M + 58, H - 42), 'DXB-KNIGHT', font=flex.F(28, 800), fill=flex.INK, anchor='lm')
    d.text((W / 2, H - 42), source.upper(), font=flex.F(26, 600), fill=muted, anchor='mm')
    d.text((W - M, H - 42), date.upper(), font=flex.F(26, 600), fill=muted, anchor='rm')
    return im


def _figure(path):
    x0, y0, x1, y1 = PANEL
    src = Image.open(path).convert('RGB')
    k = min((x1 - x0 - 40) / src.width, (y1 - y0 - 40) / src.height)
    art = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
    plate = Image.new('RGB', (x1 - x0, y1 - y0), 'white')
    plate.paste(art, ((plate.width - art.width) // 2, (plate.height - art.height) // 2))
    mask = Image.new('L', plate.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, plate.width - 1, plate.height - 1], 22, fill=255)
    return plate, mask


def _ease(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def _slid(plate, spec, t):
    """Lift a drawn object out of the figure and slide it into place:
    spec = dict(box=(x0, y0, x1, y1), frm=(dx, dy), to=(dx, dy), dur=s)."""
    from PIL import ImageChops
    x0, y0, x1, y1 = spec['box']
    sprite = plate.crop((x0, y0, x1, y1))
    out = plate.copy()
    ImageDraw.Draw(out).rectangle([x0, y0, x1, y1], fill='white')
    k = _ease(t / spec.get('dur', 1.2))
    dx = spec['frm'][0] + (spec['to'][0] - spec['frm'][0]) * k
    dy = spec['frm'][1] + (spec['to'][1] - spec['frm'][1]) * k
    layer = Image.new('RGB', out.size, 'white')
    layer.paste(sprite, (int(x0 + dx), int(y0 + dy)))
    return ImageChops.darker(out, layer)


def _dots(d, pts, acc, t, period=1.4, n=3):
    """Azure dots running along a polyline in panel pixels, looping."""
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    for i in range(n):
        u = ((t / period) - i * 0.12) % 1
        s = u * total
        for (a, b), L in zip(zip(pts, pts[1:]), seg):
            if s <= L:
                x = a[0] + (b[0] - a[0]) * s / L
                y = a[1] + (b[1] - a[1]) * s / L
                r = 13 - i * 3
                d.ellipse([PANEL[0] + x - r, PANEL[1] + y - r, PANEL[0] + x + r, PANEL[1] + y + r],
                          fill=acc)
                break
            s -= L


def _step_frame(base, plate, mask, n, total, heading, text, acc, extras, t):
    im = base.copy()
    if 'slide' in extras:
        plate = _slid(plate, extras['slide'], t)
    im.paste(plate, PANEL[:2], mask)
    d = ImageDraw.Draw(im)
    if 'path' in extras:
        _dots(d, extras['path'], acc, t)
    ring = extras.get('ring')
    if ring and t >= extras.get('ring_from', 0):
        x, y, r = ring
        t = t - extras.get('ring_from', 0)
        for k in range(3):
            ph = (t * 1.2 + k / 3) % 1
            rr = r * (0.6 + 0.9 * ph)
            a = int(255 * (1 - ph))
            col = tuple(int(255 + (acc[i] - 255) * a / 255) for i in range(3))
            d.ellipse([PANEL[0] + x - rr, PANEL[1] + y - rr, PANEL[0] + x + rr, PANEL[1] + y + rr],
                      outline=col, width=6)
    y = 170
    d.text((TEXT_X, y), f'STEP {n} OF {total}', font=flex.F(30, 800), fill=acc)
    y += 58
    f = flex.F(56, 800)
    for ln in _wrap(d, heading, f, W - TEXT_X - M):
        d.text((TEXT_X, y), ln, font=f, fill=flex.INK)
        y += 66
    y += 22
    f = flex.F(38, 450)
    for ln in _wrap(d, text, f, W - TEXT_X - M):
        d.text((TEXT_X, y), ln, font=f, fill=flex.BODY)
        y += 52
    # progress dots
    base_bg = base.getpixel((5, 5))
    for i in range(total):
        cx = TEXT_X + i * 34
        d.ellipse([cx, 740, cx + 16, 756], fill=acc if i < n else tuple(int(acc[j] * 0.3 + base_bg[j] * 0.7) for j in range(3)))
    return im


def _end_frame(base, lines, acc):
    im = base.copy()
    d = ImageDraw.Draw(im)
    y = 280
    for i, ln in enumerate(lines):
        f = flex.F(64 if i == 0 else 40, 800 if i == 0 else 450)
        for w in _wrap(d, ln, f, W - 2 * M - 200):
            d.text((W / 2, y), w, font=f, fill=flex.INK if i == 0 else flex.BODY, anchor='mm')
            y += 80 if i == 0 else 56
        y += 20
    return im


def explainer(steps, end_lines, title, source, date, out, seconds=3.4, end_seconds=2.6,
              fade=0.35, background='voiced', accent='cold'):
    bg = flex.ground(background)[0]
    acc = flex.resolve(accent)
    base = _base(bg, acc, title, source, date)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = None
    plates = [_figure(s[0]) for s in steps]
    total = len(steps)
    segs = [(i, seconds) for i in range(total)] + [('end', end_seconds)]
    for key, dur in segs:
        nf = int(dur * FPS)
        for k in range(nf):
            t = k / FPS
            if key == 'end':
                fr = _end_frame(base, end_lines, acc)
            else:
                path, heading, text, extras = steps[key]
                fr = _step_frame(base, *plates[key], key + 1, total, heading, text, acc, extras, t)
            if prev is not None and t < fade:
                fr = Image.blend(prev, fr, t / fade)
            p.stdin.write(fr.tobytes())
            last = fr
        prev = last
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError('ffmpeg failed')
    return out
