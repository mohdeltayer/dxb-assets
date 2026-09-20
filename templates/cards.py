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
import os
import subprocess
import tempfile

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
    (255, 90, 74),
]

# One accent per card, chosen by what the story is about. The ground never
# changes: the violet is the brand, the accent is the label.
ACCENT_KEY = {
    'nintendo':    7,   # red     - Nintendo, Switch, Switch 2
    'playstation': 1,   # blue    - Sony, PS5, PS5 Pro
    'xbox':        2,   # green   - Microsoft, Xbox, Game Pass
    'cross':       0,   # orange  - cross-platform, or the industry at large
    'pc':          4,   # violet  - PC, Steam, Valve, handheld PCs
    'business':    5,   # yellow  - layoffs, funding, charts, legal, sales
    'gulf':        6,   # teal    - UAE, Gulf, MENA
}


# Roundup rows and chart hardware rows cycle through these to keep adjacent
# items apart. Red is left out on purpose: next to the pink it reads as a
# near-repeat, and in a roundup the colours are separators, not labels.
CYCLE = ACCENTS[:7]


def accent_colour(a):
    """Accept a key name ('nintendo') or a raw index. Names are preferred."""
    if isinstance(a, str):
        try:
            a = ACCENT_KEY[a.lower()]
        except KeyError:
            raise KeyError(
                f'unknown accent {a!r}; use one of {sorted(ACCENT_KEY)}')
    return ACCENTS[a % len(ACCENTS)]


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


def _base(header, subheader, chip=None, chip_accent='cross'):
    ground, tile, _ = palette(chip_accent)
    im = Image.new('RGB', (W, H), ground)
    d = ImageDraw.Draw(im)
    d.text((M, 110), header, font=font(96, 800), fill=INK)
    if subheader:
        d.text((M, 228), subheader, font=font(46, 400), fill=SUB)
    # On headered cards the chip sits top right, level with the header.
    _chip(d, chip, accent_colour(chip_accent), W - M, 116,
          anchor='rt', fill=tile)
    return im, d


def _footer(im, date, source):
    """Crest and wordmark left, source centred, date right. One baseline."""
    d = ImageDraw.Draw(im)
    d.line([M, H - 150, W - M, H - 150], fill=RULE, width=2)

    base = H - 96                       # shared vertical centre

    c = Image.open(CREST).convert('RGBA').resize((58, 58), Image.LANCZOS)
    im.paste(c, (M, base - 29), c)
    d = ImageDraw.Draw(im)
    d.text((M + 74, base), 'DXB-KNIGHT', font=font(34, 800),
           fill=SUB, anchor='lm')

    if source:
        d.text((W / 2, base), source.upper(), font=font(34, 700),
               fill=MUTED, anchor='mm')
    if date:
        d.text((W - M, base), date.upper(), font=font(34, 700),
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


def _chip(d, text, colour, x, y, anchor='lt', size=58, fill=None):
    """The chip: one short hard fact. A date, a price, a frame rate.

    Always true, always under about eight characters. It is never a
    punchline on its own: the humour comes from the fact being absurd.
    Pass None or '' to leave it off, which is right when a story has no
    single number worth pulling out.
    """
    if not text:
        return
    f = font(size, 800)
    t = text.upper()
    w = d.textlength(t, font=f)
    box_w, box_h = w + 56, int(size * 1.45)
    x0 = x if 'l' in anchor else x - box_w
    y0 = y if 't' in anchor else y - box_h
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h],
                        radius=16, fill=fill if fill else GROUND)
    d.text((x0 + 28, y0 + box_h / 2), t, font=f, fill=colour, anchor='lm')


# --- Ground ---------------------------------------------------------------
# The ground carries the accent. Measured 20 Sep: shifting hue alone left
# the seven grounds 1.4 dE apart at worst, which is invisible. Mixing the
# accent into the ground in linear RGB and then pinning lightness to a
# narrow dark band gives 8.6 dE at worst, which reads.
GROUND_MIX = 0.40          # how much accent goes into the ground
GROUND_L = (5.0, 7.0)      # darkest L*, plus how much lighter a pale accent may go


def _s2l(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _l2s(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _lightness(rgb):
    r, g, b = [_s2l(v) for v in rgb]
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    fy = y ** (1 / 3) if y > 0.008856 else (7.787 * y + 16 / 116)
    return 116 * fy - 16


def _ground_for(accent_rgb):
    """A dark ground carrying the accent, pinned into the lightness band."""
    base = [_s2l(v) for v in GROUND]
    acc = [_s2l(v) for v in accent_rgb]
    m = [b * (1 - GROUND_MIX) + a * GROUND_MIX for b, a in zip(base, acc)]

    lo, span = GROUND_L
    want_L = lo + span * max(0.0, min(1.0, (_lightness(accent_rgb) - 55) / 40))
    fy = (want_L + 16) / 116
    want_Y = fy ** 3 if fy ** 3 > 0.008856 else (fy - 16 / 116) / 7.787

    y = 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]
    if y > 0:
        m = [v * want_Y / y for v in m]
    return tuple(int(round(_l2s(v) * 255)) for v in m)


def _lift(ground, amount):
    """A tile colour: the ground, lifted toward the ink."""
    return tuple(int(round(c + (i - c) * amount))
                 for c, i in zip(ground, INK))


def palette(accent):
    """Ground, tile and tile-2 for this card's accent."""
    g = _ground_for(accent_colour(accent))
    return g, _lift(g, 0.07), _lift(g, 0.11)


# ---------------------------------------------------------------- ROUNDUP ---
def roundup(header, subheader, items, date, source, out, chip=None, accent='cross'):
    """items: (title, sub, date, image|None), max 4. Showcase recaps."""
    assert len(items) <= 4
    im, d = _base(header, subheader, chip, accent)
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
                             radius=7, fill=CYCLE[i % len(CYCLE)] + (255,))

    im = Image.alpha_composite(im.convert('RGBA'),
                               glow.filter(ImageFilter.GaussianBlur(22)))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(8)))
    im = Image.alpha_composite(im, glow).convert('RGB')
    d = ImageDraw.Draw(im)

    tf, sf, df = font(86, 800), font(46, 400), font(64, 800)
    for i, (title, sub, date, img) in enumerate(items):
        y, colour = ys[i], CYCLE[i % len(CYCLE)]
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
def single(kicker, title, lines, release, image, date, source, out,
           accent='cross', video=None, clip_start=0, clip_seconds=6,
           audio=False):
    """One announcement. Artwork fills the top, text below.

    Pass `video` (a filename in the uploads folder) instead of relying on
    `image` to get a moving art panel and an MP4 out. Everything else is
    identical, so a card can be switched between still and moving without
    touching the copy. Use it only when the motion is the story.
    """
    ART_Y, ART_H = 110, 860
    ground, _, _ = palette(accent)
    im = Image.new('RGB', (W, H), ground)
    colour = accent_colour(accent)
    d = ImageDraw.Draw(im)

    if image and not video:
        _rounded(im, _fit(image, W - M * 2, ART_H), (M, ART_Y), radius=24)
        d = ImageDraw.Draw(im)

    y = ART_Y + ART_H + 60
    d.text((M, y), kicker.upper(), font=font(46, 800), fill=colour)
    y += 76

    tf = font(108, 800)
    for ln in wrap(d, title, tf, W - M * 2):
        d.text((M, y), ln, font=tf, fill=INK); y += 118
    y += 24

    # Body type is sized for a phone timeline, so it will not silently
    # shrink far to fit. It steps down a little, then refuses: if the copy
    # still does not fit, the copy is too long and has to be cut.
    LIMIT = H - 190                      # clear of the footer rule
    for size in (56, 54, 52, 50, 48):
        bf = font(size, 450)
        step, gap = int(size * 1.25), 16
        need = sum(len(wrap(d, ln, bf, W - M * 2)) for ln in lines) * step \
            + gap * (len(lines) - 1)
        if y + need <= LIMIT:
            break
    else:
        raise ValueError(
            f'body copy is too long for this card: needs {y + need - LIMIT}px '
            f'more than there is. Cut roughly '
            f'{int((y + need - LIMIT) / step) + 1} line(s).')

    for line in lines:
        for ln in wrap(d, line, bf, W - M * 2):
            d.text((M, y), ln, font=bf, fill=SUB); y += step
        y += gap

    im = _footer(im, date, source)

    if not video:
        # The chip sits on the artwork, bottom-left, clear of the body copy.
        _chip(ImageDraw.Draw(im), release, colour, M + 30, ART_Y + ART_H - 30,
              anchor='lb', fill=ground)
        im.save(out)
        return out

    return _render_video(im, colour, release, video, out,
                         ART_Y, ART_H, clip_start, clip_seconds, audio,
                         ground)


def _has_audio(path):
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a',
             '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', path],
            check=True, capture_output=True, text=True)
        return 'audio' in r.stdout
    except Exception:
        return False


def _render_video(base, colour, release, video, out, art_y, art_h,
                  clip_start, clip_seconds, audio=False, ground=None):
    """Composite one or more clips into the art panel and write an MP4.

    `video` is either a filename, or a list of (filename, start, seconds)
    for a sequence. Segments are cut, not crossfaded: on a panel this size
    a dissolve reads as a smear.
    """
    if not out.lower().endswith('.mp4'):
        raise ValueError('a video card must be written to a .mp4 path')

    clips = ([(video, clip_start, clip_seconds)] if isinstance(video, str)
             else [tuple(c) for c in video])
    if not clips:
        raise ValueError('no clips given')

    art_w = W - M * 2
    tmp = tempfile.mkdtemp(prefix='dxbcard-')
    base_p = os.path.join(tmp, 'base.png')
    mask_p = os.path.join(tmp, 'mask.png')
    chip_p = os.path.join(tmp, 'chip.png')
    base.save(base_p)

    mask = Image.new('L', (art_w, art_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, art_w, art_h], radius=24, fill=255)
    mask.save(mask_p)

    # The chip rides above the video, so it gets its own transparent layer.
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _chip(ImageDraw.Draw(top), release, colour, M + 30, art_y + art_h - 30,
          anchor='lb', fill=ground or GROUND)
    top.save(chip_p)

    paths = [U + c[0] for c in clips]
    keep_audio = audio and all(_has_audio(p) for p in paths)

    cmd = ['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-i', base_p]
    for (name, st, dur), p in zip(clips, paths):
        cmd += ['-ss', str(st), '-t', str(dur), '-i', p]
    n = len(clips)
    cmd += ['-i', mask_p, '-loop', '1', '-i', chip_p]
    i_mask, i_chip = n + 1, n + 2

    # Every segment is normalised to the panel before it is joined, so
    # mixed sources (portrait phone capture, 60fps landscape) concatenate.
    parts = ''.join(
        f'[{i + 1}:v]scale={art_w}:{art_h}:force_original_aspect_ratio=increase,'
        f'crop={art_w}:{art_h},setsar=1,fps=30,format=yuv420p[s{i}];'
        for i in range(n))
    vrefs = ''.join(f'[s{i}]' for i in range(n))

    if keep_audio:
        arefs = ''.join(f'[{i + 1}:a]' for i in range(n))
        joined = ''.join(f'[s{i}][{i + 1}:a]' for i in range(n))
        concat = f'{joined}concat=n={n}:v=1:a=1[vid][aud];'
        amap = ['-map', '[aud]', '-c:a', 'aac', '-b:a', '128k']
    else:
        concat = f'{vrefs}concat=n={n}:v=1:a=0[vid];'
        amap = ['-an']

    chain = (
        parts + concat +
        f'[vid][{i_mask}:v]alphamerge[vida];'
        f'[0:v][vida]overlay={M}:{art_y}:shortest=1[a];'
        f'[a][{i_chip}:v]overlay=0:0:shortest=1[b];'
        f'[b]scale=1080:1350,format=yuv420p[out]'
    )
    cmd += ['-filter_complex', chain, '-map', '[out]'] + amap + [
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
        '-r', '30', '-movflags', '+faststart', out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffmpeg failed:\n{r.stderr[-1200:]}')
    return out


# ----------------------------------------------------------------- CHARTS ---
def charts(header, subheader, rows, hardware, date, source, out, chip=None, accent='business'):
    """rows: (rank, platform, title, week, lifetime|None). hardware: (label, n)."""
    im, d = _base(header, subheader, chip, accent)
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
               fill=CYCLE[i % len(CYCLE)], anchor='rm')
        y += 98

    _footer(im, date, source).save(out)
    return out


# ---------------------------------------------------------------- COMPARE ---
def compare(header, subheader, left, right, date, source, out, chip=None, accent='cross'):
    """left/right: dict(label, price, sub, rows[list of str], image|None).

    If either side has an image, both columns get a 420px art panel at the top.
    """
    im, d = _base(header, subheader, chip, accent)
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
          accent='cross', image=None, chip=None):
    """A statement someone made. Optional image sits under the quote."""
    im = Image.new('RGB', (W, H), GROUND)
    d = ImageDraw.Draw(im)
    colour = accent_colour(accent)

    d.text((M, 140), header.upper(), font=font(44, 800), fill=colour)
    d.line([M, 226, M + 180, 226], fill=colour, width=8)
    _chip(d, chip, colour, W - M, 128, anchor='rt', fill=TILE)

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
