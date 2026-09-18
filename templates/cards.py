"""
DXB-KNIGHT card templates.

All cards: 1600 x 2000 (4:5), violet ground, Inter, phone-first type sizes.

    roundup(...)   showcase recaps, multiple announcements     max 4 items
    single(...)    one announcement, the hero card             1 item
    charts(...)    weekly sales charts                         up to 10 rows
    compare(...)   two things side by side, prices or specs    2 columns
    quote(...)     a statement someone made                    1 quote

Each returns the output path.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1600, 2000

GROUND = (22, 12, 51)
TILE   = (32, 20, 64)
TILE_2 = (40, 26, 78)
INK    = (255, 253, 250)
SUB    = (198, 186, 235)
MUTED  = (138, 126, 178)
RULE   = (62, 46, 108)

ACCENTS = [
    (255, 150, 50), (110, 200, 255), (60, 255, 150),
    (255, 80, 130), (210, 140, 255), (255, 215, 80), (100, 240, 220),
]
GOOD = (60, 255, 150)
BAD  = (255, 80, 130)

F = '/home/claude/fonts/Inter.ttf'
U = '/mnt/user-data/uploads/'
CREST = '/home/claude/crest-tint.png'
M = 70


def font(size, weight=400):
    f = ImageFont.truetype(F, size)
    try:
        f.set_variation_by_axes([min(max(size, 14), 32), weight])
    except Exception:
        pass
    return f


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _base(header, subheader):
    im = Image.new('RGB', (W, H), GROUND)
    d = ImageDraw.Draw(im)
    d.text((M, 110), header, font=font(96, 800), fill=INK)
    if subheader:
        d.text((M, 228), subheader, font=font(46, 400), fill=SUB)
    return im, d


def _footer(im, date, source):
    """Crest and wordmark left, source centred, date right. One baseline."""
    d = ImageDraw.Draw(im)
    d.line([M, H - 150, W - M, H - 150], fill=RULE, width=2)

    base = H - 96                       # shared vertical centre

    c = Image.open(CREST).convert('RGBA').resize((58, 58), Image.LANCZOS)
    im.paste(c, (M, base - 29), c)
    d = ImageDraw.Draw(im)
    d.text((M + 74, base), 'DXB-KNIGHT', font=font(28, 800),
           fill=SUB, anchor='lm')

    if source:
        d.text((W / 2, base), source.upper(), font=font(28, 700),
               fill=MUTED, anchor='mm')
    if date:
        d.text((W - M, base), date.upper(), font=font(28, 700),
               fill=SUB, anchor='rm')
    return im


def _fit(path, box_w, box_h, bias=0.35):
    src = Image.open(U + path).convert('RGB')
    target = box_w / box_h
    sw, sh = src.size
    if sw / sh > target:
        nw = int(sh * target)
        x0 = int((sw - nw) * bias)
        src = src.crop((x0, 0, x0 + nw, sh))
    else:
        nh = int(sw / target)
        src = src.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return src.resize((box_w, box_h), Image.LANCZOS)


def _rounded(im, src, xy, radius=16):
    mask = Image.new('L', src.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, src.size[0], src.size[1]], radius=radius, fill=255)
    im.paste(src, xy, mask)


# ---------------------------------------------------------------- ROUNDUP ---
def roundup(header, subheader, items, date, source, out):
    """items: (title, sub, date, image|None), max 4. Showcase recaps."""
    assert len(items) <= 4
    im, d = _base(header, subheader)
    TOP, GAP, IMG_W = 430, 26, 420
    n = len(items)
    row_h = int((H - TOP - 220 - GAP * (n - 1)) / n)

    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ys = []
    for i in range(n):
        y = TOP + i * (row_h + GAP)
        ys.append(y)
        d.rounded_rectangle([M, y, W - M, y + row_h], radius=22, fill=TILE)
        gd.rounded_rectangle([M, y + 22, M + 14, y + row_h - 22],
                             radius=7, fill=ACCENTS[i % 7] + (255,))

    im = Image.alpha_composite(im.convert('RGBA'),
                               glow.filter(ImageFilter.GaussianBlur(22)))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(8)))
    im = Image.alpha_composite(im, glow).convert('RGB')
    d = ImageDraw.Draw(im)

    tf, sf, df = font(86, 800), font(46, 400), font(64, 800)
    for i, (title, sub, date, img) in enumerate(items):
        y, colour = ys[i], ACCENTS[i % 7]
        tw = W - M * 2 - 70 - (IMG_W + 40 if img else 0)
        if img:
            _rounded(im, _fit(img, IMG_W, row_h - 44),
                     (W - M - 30 - IMG_W, y + 22))
            d = ImageDraw.Draw(im)
        tl, sl = wrap(d, title, tf, tw), wrap(d, sub, sf, tw)
        cy = y + (row_h - (len(tl) * 96 + 14 + len(sl) * 54 + 20 + 70)) / 2
        for ln in tl:
            d.text((M + 58, cy), ln, font=tf, fill=INK); cy += 96
        cy += 14
        for ln in sl:
            d.text((M + 58, cy), ln, font=sf, fill=SUB); cy += 54
        d.text((M + 58, cy + 20), date, font=df, fill=colour)

    _footer(im, date, source).save(out)
    return out


# ----------------------------------------------------------------- SINGLE ---
def single(kicker, title, lines, release, image, date, source, out, accent=0):
    """One announcement. Image fills the top half, text below."""
    im = Image.new('RGB', (W, H), GROUND)
    colour = ACCENTS[accent % 7]

    art_h = 860
    _rounded(im, _fit(image, W - M * 2, art_h), (M, 110), radius=24)
    d = ImageDraw.Draw(im)

    y = 110 + art_h + 60
    d.text((M, y), kicker.upper(), font=font(40, 800), fill=colour)
    y += 68

    tf = font(108, 800)
    for ln in wrap(d, title, tf, W - M * 2):
        d.text((M, y), ln, font=tf, fill=INK); y += 118
    y += 24

    bf = font(50, 400)
    for line in lines:
        for ln in wrap(d, line, bf, W - M * 2):
            d.text((M, y), ln, font=bf, fill=SUB); y += 62
        y += 12

    if date:
        d.text((M, H - 250), release, font=font(76, 800), fill=colour)

    _footer(im, date, source).save(out)
    return out


# ----------------------------------------------------------------- CHARTS ---
def charts(header, subheader, rows, hardware, date, source, out):
    """rows: (rank, platform, title, week, lifetime|None). hardware: (label, n)."""
    im, d = _base(header, subheader)
    y = 400
    rf, pf, tf, nf = (font(46, 800), font(32, 700),
                      font(44, 600), font(42, 800))

    for rank, plat, title, week, life in rows[:10]:
        d.rounded_rectangle([M, y, W - M, y + 92], radius=14, fill=TILE)
        d.text((M + 26, y + 46), str(rank), font=rf, fill=SUB, anchor='lm')
        d.text((M + 92, y + 46), plat, font=pf, fill=MUTED, anchor='lm')
        t = title if d.textlength(title, font=tf) < 780 else title[:34] + '...'
        d.text((M + 210, y + 46), t, font=tf, fill=INK, anchor='lm')
        d.text((W - M - 26, y + 46), f'{week:,}', font=nf, fill=INK, anchor='rm')
        y += 102

    y += 34
    d.text((M, y), 'HARDWARE', font=font(40, 800), fill=SUB); y += 70
    for i, (label, n) in enumerate(hardware):
        d.rounded_rectangle([M, y, W - M, y + 88], radius=14, fill=TILE_2)
        d.text((M + 32, y + 44), label, font=font(46, 700), fill=INK, anchor='lm')
        d.text((W - M - 32, y + 44), f'{n:,}', font=font(50, 800),
               fill=ACCENTS[i % 7], anchor='rm')
        y += 98

    _footer(im, date, source).save(out)
    return out


# ---------------------------------------------------------------- COMPARE ---
def compare(header, subheader, left, right, date, source, out):
    """left/right: dict(label, price, sub, rows[list of str], image|None).

    If either side has an image, both columns get a 420px art panel at the top.
    """
    im, d = _base(header, subheader)
    TOP, BOT = 430, H - 220
    colw = (W - M * 2 - 30) // 2
    has_art = bool(left.get('image') or right.get('image'))
    ART_H = 420 if has_art else 0

    for i, (side, x) in enumerate(((left, M), (right, M + colw + 30))):
        colour = GOOD if i == 0 else BAD
        d.rounded_rectangle([x, TOP, x + colw, BOT], radius=22, fill=TILE)

        y = TOP + 26
        if ART_H:
            if side.get('image'):
                _rounded(im, _fit(side['image'], colw - 52, ART_H),
                         (x + 26, y), radius=16)
            else:
                d.rounded_rectangle([x + 26, y, x + colw - 26, y + ART_H],
                                    radius=16, fill=TILE_2)
            d = ImageDraw.Draw(im)
            y += ART_H + 34

        lf = font(58, 800)
        for ln in wrap(d, side['label'], lf, colw - 60):
            d.text((x + 30, y), ln, font=lf, fill=INK)
            y += 70
        y += 14
        d.text((x + 30, y), side['price'], font=font(88, 800), fill=colour)
        y += 112
        if side.get('sub'):
            d.text((x + 30, y), side['sub'], font=font(40, 400), fill=MUTED)
            y += 72

        rows = side['rows']
        remaining = BOT - 40 - y
        rf_size = 44
        while rf_size > 30:
            rf = font(rf_size, 400)
            need = sum((len(wrap(d, r, rf, colw - 60)) * (rf_size + 14) + 12)
                       for r in rows)
            if need <= remaining:
                break
            rf_size -= 2
        rf = font(rf_size, 400)
        for row in rows:
            for ln in wrap(d, row, rf, colw - 60):
                d.text((x + 30, y), ln, font=rf, fill=SUB)
                y += rf_size + 14
            y += 12

    _footer(im, date, source).save(out)
    return out


# ------------------------------------------------------------------ QUOTE ---
def quote(header, text, attribution, context, date, source, out,
          accent=3, image=None):
    """A statement someone made. Optional image sits under the quote."""
    im = Image.new('RGB', (W, H), GROUND)
    d = ImageDraw.Draw(im)
    colour = ACCENTS[accent % 7]

    d.text((M, 140), header.upper(), font=font(44, 800), fill=colour)
    d.line([M, 226, M + 180, 226], fill=colour, width=8)

    ART_H = 620 if image else 0
    top = 320
    bottom = H - 220 - (ART_H + 50 if image else 0)

    # grow the quote until it fills the space it has
    size = 150
    while size > 70:
        qf = font(size, 700)
        lines = wrap(d, f'"{text}"', qf, W - M * 2)
        block = len(lines) * (size + 20) + 50 + 84 + len(context) * 72
        if block <= bottom - top:
            break
        size -= 4

    qf = font(size, 700)
    lines = wrap(d, f'"{text}"', qf, W - M * 2)
    block = len(lines) * (size + 20) + 50 + 84 + len(context) * 72
    y = top + max(0, (bottom - top - block) / 2)

    for ln in lines:
        d.text((M, y), ln, font=qf, fill=INK)
        y += size + 20
    y += 40

    d.text((M, y), attribution, font=font(54, 800), fill=colour)
    y += 84

    cf = font(44, 400)
    for line in context:
        for ln in wrap(d, line, cf, W - M * 2):
            d.text((M, y), ln, font=cf, fill=SUB)
            y += 58
        y += 14

    if image:
        _rounded(im, _fit(image, W - M * 2, ART_H), (M, H - 220 - ART_H),
                 radius=24)

    _footer(im, date, source).save(out)
    return out
