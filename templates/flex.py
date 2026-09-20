"""DXB-KNIGHT flexible entertainment design system.

Same 1600 x 2000 canvas, same wireframe, same type hierarchy. What varies
is background family, accent choice and treatment. Colour and effect are
separate: a bright accent is a colour, glow is a treatment, and one does
not imply the other.
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter
import cards as C

W, H, M = 1600, 2000, 70
ART = (M, 110, W - M, 970)
F = C.font


def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


BACKGROUNDS = {'navy': hx('#111D29'), 'purple': hx('#1D1440')}

#: Background says who is talking.
MODE = {'reported': 'navy', 'voiced': 'purple'}

ACCENTS = {
    'cyan':     hx('#42D7FF'),
    'lavender': hx('#BBA3FF'),
    'amber':    hx('#FFC03A'),
    'rose':     hx('#FF4D6D'),
    'coral':    hx('#FF5C45'),
    'gold':     hx('#FFD34E'),
}

#: Gold is the Gulf chip and nothing else. It sits 4 degrees from amber,
#: so on a border the two stop being distinguishable.
RESERVED = {'gold'}

#: Accent says how the subject feels. Spectacle carries two: rose leads,
#: coral is the deliberate alternate when rose would sit next to amber or
#: vanish into pink artwork.
TERRITORY = {
    'cold':      'cyan',       # sci-fi, horror, hardware, specs, business, legal
    'stylized':  'lavender',   # fantasy, RPG, anime, mystery, story-led
    'playful':   'amber',      # platformers, party, fighting, sports, jokes
    'spectacle': 'rose',       # blockbuster reveals, movies, TV, pop culture
}
ALTERNATES = {'spectacle': ('rose', 'coral')}

SUPPORT = {'cyan': 'lavender', 'lavender': 'cyan', 'amber': 'cyan',
           'rose': 'amber', 'coral': 'amber'}

GULF_CHIP = 'gold'
DEFAULT = dict(background='navy', accent='cyan', treatment='flat')

#: Row separators in a list. Coral is left out on purpose: stacked
#: directly above or below amber, 34 degrees of hue is not enough.
CYCLE = ('cyan', 'lavender', 'amber', 'rose')

INK, BODY = hx('#F7FAFC'), hx('#D7E1EA')
TREATMENTS = ('flat', 'spotlight', 'neon')


def resolve(name):
    """A territory name, an accent name or a raw RGB triple."""
    if not isinstance(name, str):
        return tuple(name)
    key = TERRITORY.get(name.lower(), name.lower())
    if key in RESERVED:
        raise ValueError(f'{key} is reserved for the Gulf chip, not a card accent')
    try:
        return ACCENTS[key]
    except KeyError:
        raise KeyError(f'unknown accent {name!r}; territories are '
                       f'{sorted(TERRITORY)}, accents are '
                       f'{sorted(set(ACCENTS) - RESERVED)}')


def lift(c, amount, toward=(255, 255, 255)):
    return tuple(int(round(a + (b - a) * amount)) for a, b in zip(c, toward))


def surfaces(bg):
    """Coordinated lighter shades for grouped panels."""
    return lift(bg, 0.07), lift(bg, 0.12), lift(bg, 0.20)


def _glow(im, draw_fn, colour, spread=26, passes=(26, 10)):
    """An illuminated edge. Only ever called by the neon treatment."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), colour + (255,))
    out = im.convert('RGBA')
    for r in passes:
        out = Image.alpha_composite(out, layer.filter(ImageFilter.GaussianBlur(r)))
    return Image.alpha_composite(out, layer).convert('RGB')


def _contain(path, bw, bh):
    src = Image.open(C.U + path).convert('RGB')
    k = min(bw / src.width, bh / src.height)
    return src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))),
                      Image.LANCZOS)


def place_media(im, box, path, backing, radius=24):
    """Media keeps its own colours. Nothing is tinted, overlaid or graded."""
    x0, y0, x1, y1 = box
    plate = Image.new('RGB', (x1 - x0, y1 - y0), backing)
    art = _contain(path, x1 - x0, y1 - y0)
    plate.paste(art, ((x1 - x0 - art.width) // 2, (y1 - y0 - art.height) // 2))
    mask = Image.new('L', plate.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *plate.size], radius=radius, fill=255)
    im.paste(plate, (x0, y0), mask)


def filled_label(d, text, x, y, accent, bg, size=56, anchor='lb'):
    """A filled label: accent block, background-coloured type."""
    f = F(size, 800)
    t = text.upper()
    w = d.textlength(t, font=f)
    bw, bh = w + 54, int(size * 1.46)
    x0 = x if 'l' in anchor else x - bw
    y0 = y if 't' in anchor else y - bh
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=10, fill=accent)
    d.text((x0 + 27, y0 + bh / 2), t, font=f, fill=bg, anchor='lm')
    return (x0, y0, x0 + bw, y0 + bh)


def ground(background):
    """bg plus its three coordinated surface shades."""
    background = MODE.get(str(background).lower(), background)
    bg = (BACKGROUNDS[background] if isinstance(background, str)
          else tuple(background))
    return (bg,) + surfaces(bg)


def heading(d, header, subheader, label, acc, bg):
    """The header block used by every template except `single`, which leads
    with media instead. The chip sits top right, level with the header."""
    d.text((M, 110), header, font=F(96, 800), fill=INK)
    if subheader:
        d.text((M, 228), subheader, font=F(44, 450), fill=BODY)
    if label:
        filled_label(d, label, W - M, 116, acc, bg, anchor='rt')


def marks(d, acc, bg, label, gulf, treatment):
    """The panel border and the chips. Drawn on the card for a still, and on
    a transparent layer riding above the clip for a video, so they read the
    same either way."""
    d.rounded_rectangle(list(ART), radius=24, outline=acc,
                        width=6 if treatment != 'flat' else 5)
    box = filled_label(d, label, M + 34, ART[3] - 34, acc, bg, anchor='lb')
    if gulf:
        filled_label(d, 'GULF', box[2] + 18, ART[3] - 34, ACCENTS[GULF_CHIP],
                     bg, anchor='lb')


def _has_audio(path):
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a',
             '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', path],
            check=True, capture_output=True, text=True)
        return 'audio' in r.stdout
    except Exception:
        return False


def _render_video(base, top, video, out, panel, clip_start, clip_seconds,
                  audio):
    """Composite one or more clips into the panel and write an MP4.

    `video` is a filename, or a list of (filename, start, seconds). Segments
    are cut, not crossfaded: on a panel this size a dissolve reads as a smear.

    The clip is *contained* and padded onto the panel shade, matching how a
    still is placed. Cropping to fill would make video the one place the
    system throws away part of the frame.
    """
    if not out.lower().endswith('.mp4'):
        raise ValueError('a video card must be written to a .mp4 path')
    clips = ([(video, clip_start, clip_seconds)] if isinstance(video, str)
             else [tuple(c) for c in video])
    if not clips:
        raise ValueError('no clips given')

    x0, y0, x1, y1 = ART
    aw, ah = x1 - x0, y1 - y0
    tmp = tempfile.mkdtemp(prefix='dxbflex-')
    base_p = os.path.join(tmp, 'base.png')
    mask_p = os.path.join(tmp, 'mask.png')
    top_p = os.path.join(tmp, 'top.png')
    base.save(base_p)
    top.save(top_p)

    mask = Image.new('L', (aw, ah), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, aw, ah], radius=24, fill=255)
    mask.save(mask_p)

    paths = [C.U + c[0] for c in clips]
    keep_audio = audio and all(_has_audio(p) for p in paths)
    pad = '0x%02X%02X%02X' % tuple(panel)

    cmd = ['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-i', base_p]
    for (_, st, dur), p in zip(clips, paths):
        cmd += ['-ss', str(st), '-t', str(dur), '-i', p]
    n = len(clips)
    cmd += ['-i', mask_p, '-loop', '1', '-i', top_p]
    i_mask, i_top = n + 1, n + 2

    # Each segment is normalized to the panel before joining, so mixed
    # sources (portrait capture, 60fps landscape) concatenate cleanly.
    parts = ''.join(
        f'[{i + 1}:v]scale={aw}:{ah}:force_original_aspect_ratio=decrease,'
        f'pad={aw}:{ah}:(ow-iw)/2:(oh-ih)/2:color={pad},setsar=1,fps=30,'
        f'format=yuv420p[s{i}];' for i in range(n))
    vrefs = ''.join(f'[s{i}]' for i in range(n))

    if keep_audio:
        joined = ''.join(f'[s{i}][{i + 1}:a]' for i in range(n))
        concat = f'{joined}concat=n={n}:v=1:a=1[vid][aud];'
        amap = ['-map', '[aud]', '-c:a', 'aac', '-b:a', '128k']
    else:
        concat = f'{vrefs}concat=n={n}:v=1:a=0[vid];'
        amap = ['-an']

    chain = (
        parts + concat +
        f'[vid][{i_mask}:v]alphamerge[vida];'
        f'[0:v][vida]overlay={x0}:{y0}:shortest=1[a];'
        f'[a][{i_top}:v]overlay=0:0:shortest=1[b];'
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


def footer(im, bg, source, date, rule_colour):
    d = ImageDraw.Draw(im)
    d.line([M, H - 150, W - M, H - 150], fill=rule_colour, width=3)
    base = H - 92
    crest = Image.open(C.CREST).convert('RGBA').resize((56, 56), Image.LANCZOS)
    im.paste(crest, (M, base - 28), crest)
    d = ImageDraw.Draw(im)
    d.text((M + 72, base), 'DXB-KNIGHT', font=F(32, 800), fill=INK, anchor='lm')
    d.text((W / 2, base), source.upper(), font=F(30, 600), fill=lift(BODY, -0.25, bg),
           anchor='mm')
    d.text((W - M, base), date.upper(), font=F(30, 600), fill=lift(BODY, -0.25, bg),
           anchor='rm')
    return im


def single(kicker, title, lines, label, media, date, source, out,
           background='reported', accent='cold', support=None, treatment='flat',
           display=None, gulf=False, video=None, clip_start=0, clip_seconds=6,
           audio=False):
    """One story.

    `background` takes a mode ('reported', 'voiced') or a name ('navy',
    'purple'). `accent` takes a territory ('cold', 'stylized', 'playful',
    'spectacle') or an accent name. `support` is picked automatically unless
    given. `gulf=True` adds the gold GULF chip beside the label; it rides on
    whatever accent the topic already earned.

    Pass `video` instead of relying on `media` to write an MP4: a filename,
    or a list of (filename, start, seconds) for a sequence. `out` must then
    end in .mp4. Everything else is identical, so a card can be switched
    between still and moving without touching the copy.
    """
    assert treatment in TREATMENTS, treatment
    background = MODE.get(str(background).lower(), background)
    bg = BACKGROUNDS[background] if isinstance(background, str) else tuple(background)
    acc = resolve(accent)
    if support is None:
        support = SUPPORT.get(TERRITORY.get(str(accent).lower(),
                                            str(accent).lower()))
    sup = resolve(support) if support is not None else acc
    panel, panel2, edge = surfaces(bg)

    im = Image.new('RGB', (W, H), bg)

    if treatment == 'spotlight':
        wash = Image.new('RGB', (W, H), bg)
        wd = ImageDraw.Draw(wash)
        for i in range(120):
            k = i / 120
            wd.rectangle([0, int(H * k), W, H], fill=lift(bg, 0.10 * (1 - k), acc))
        im = Image.blend(im, wash, 0.55)

    if video:
        # The panel shade is laid down now and the clip composited into it
        # later, so the letterbox bars match a still card's backing.
        ImageDraw.Draw(im).rounded_rectangle(list(ART), radius=24, fill=panel)
    else:
        place_media(im, ART, media, panel)
    d = ImageDraw.Draw(im)

    if treatment == 'neon':
        im = _glow(im, lambda dd, col: dd.rounded_rectangle(list(ART), radius=24,
                                                            outline=col, width=6), acc)
        d = ImageDraw.Draw(im)

    if not video:
        marks(d, acc, bg, label, gulf, treatment)

    y = ART[3] + 64
    if display and treatment == 'neon':
        df = F(120, 800)
        im = _glow(im, lambda dd, col: dd.text((M, y), display.upper(), font=df, fill=col),
                   sup, passes=(22, 8))
        d = ImageDraw.Draw(im)
        y += 150

    d.text((M, y), kicker.upper(), font=F(44, 800), fill=sup)
    y += 72
    d.rectangle([M, y - 16, M + 120, y - 8], fill=acc)
    y += 16

    tf = F(106, 800)
    for ln in C.wrap(d, title, tf, W - M * 2):
        d.text((M, y), ln, font=tf, fill=INK); y += 116
    y += 28

    bf = F(54, 450)
    for p in lines:
        for ln in C.wrap(d, p, bf, W - M * 2):
            d.text((M, y), ln, font=bf, fill=BODY); y += 68
        y += 18

    im = footer(im, bg, source, date, edge)

    if not video:
        im.save(out)
        return out

    top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    marks(ImageDraw.Draw(top), acc, bg, label, gulf, treatment)
    return _render_video(im, top, video, out, panel, clip_start, clip_seconds,
                         audio)


# ---------------------------------------------------------------- ROUNDUP ---
def roundup(header, subheader, items, date, source, out, label=None,
            background='reported', accent='cold', treatment='flat'):
    """A showcase recap. `items` is (title, sub, when, image|None), max 4.

    Row thumbnails are cropped, not contained. The hero panel on `single`
    is the story's picture and cropping it throws away content; a row
    thumbnail only has to say which game the row is about, and letterboxing
    four of them leaves the card full of bars.
    """
    assert len(items) <= 4, 'a roundup holds four items at most'
    bg, panel, panel2, edge = ground(background)
    acc = resolve(accent)
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    heading(d, header, subheader, label, acc, bg)

    TOP, GAP, IMG_W = 430, 26, 420
    n = len(items)
    row_h = int((H - TOP - 220 - GAP * (n - 1)) / n)

    bars = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bars)
    ys = []
    for i in range(n):
        y = TOP + i * (row_h + GAP)
        ys.append(y)
        d.rounded_rectangle([M, y, W - M, y + row_h], radius=22, fill=panel)
        bd.rounded_rectangle([M + 26, y + 24, M + 38, y + row_h - 24],
                             radius=6,
                             fill=ACCENTS[CYCLE[i % len(CYCLE)]] + (255,))

    if treatment == 'neon':
        for r in (22, 8):
            im = Image.alpha_composite(
                im.convert('RGBA'),
                bars.filter(ImageFilter.GaussianBlur(r))).convert('RGB')
    im = Image.alpha_composite(im.convert('RGBA'), bars).convert('RGB')
    d = ImageDraw.Draw(im)

    tf, sf, wf = F(80, 800), F(44, 450), F(56, 800)
    for i, (title, sub, when, img) in enumerate(items):
        y = ys[i]
        colour = ACCENTS[CYCLE[i % len(CYCLE)]]
        tw = W - M * 2 - 100 - (IMG_W + 40 if img else 0)
        if img:
            C._rounded(im, C._fit(img, IMG_W, row_h - 44),
                       (W - M - 30 - IMG_W, y + 22))
            d = ImageDraw.Draw(im)
        tl = C.wrap(d, title, tf, tw)
        sl = C.wrap(d, sub, sf, tw) if sub else []
        block = (len(tl) * 90 + (14 + len(sl) * 54 if sl else 0)
                 + (20 + 62 if when else 0))
        cy = y + (row_h - block) / 2
        for ln in tl:
            d.text((M + 66, cy), ln, font=tf, fill=INK); cy += 90
        if sl:
            cy += 14
            for ln in sl:
                d.text((M + 66, cy), ln, font=sf, fill=BODY); cy += 54
        if when:
            d.text((M + 66, cy + 20), when, font=wf, fill=colour)

    footer(im, bg, source, date, edge).save(out)
    return out


# ----------------------------------------------------------------- CHARTS ---
def charts(header, subheader, rows, hardware, date, source, out, label=None,
           background='reported', accent='cold'):
    """rows: (rank, platform, title, week, lifetime|None). hardware: (label, n).

    A chart is always `cold`, never the platform that won the week, or
    every chart card takes the colour of whoever is selling and the
    territory stops meaning anything.
    """
    bg, panel, panel2, edge = ground(background)
    acc = resolve(accent)
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    heading(d, header, subheader, label, acc, bg)
    muted = lift(BODY, -0.30, bg)

    y = 400
    rf, pf, tf, nf = F(44, 800), F(30, 700), F(42, 600), F(42, 800)
    for rank, plat, title, week, _life in rows[:10]:
        d.rounded_rectangle([M, y, W - M, y + 92], radius=14, fill=panel)
        d.text((M + 26, y + 46), str(rank), font=rf, fill=BODY, anchor='lm')
        d.text((M + 92, y + 46), plat, font=pf, fill=muted, anchor='lm')
        t = title if d.textlength(title, font=tf) < 780 else title[:34] + '...'
        d.text((M + 210, y + 46), t, font=tf, fill=INK, anchor='lm')
        d.text((W - M - 26, y + 46), f'{week:,}', font=nf, fill=INK,
               anchor='rm')
        y += 102

    if hardware:
        y += 34
        d.text((M, y), 'HARDWARE', font=F(38, 800), fill=BODY); y += 68
        for name, n in hardware:
            d.rounded_rectangle([M, y, W - M, y + 88], radius=14, fill=panel2)
            d.text((M + 32, y + 44), name, font=F(44, 700), fill=INK,
                   anchor='lm')
            # One colour for every hardware line. Cycling through the accents
            # here made Switch 2 cyan and PS5 lavender, which reads as a
            # platform key, and the platform key is exactly what was retired.
            d.text((W - M - 32, y + 44), f'{n:,}', font=F(48, 800),
                   fill=acc, anchor='rm')
            y += 98

    footer(im, bg, source, date, edge).save(out)
    return out


# ---------------------------------------------------------------- COMPARE ---
def compare(header, subheader, left, right, date, source, out, label=None,
            background='reported', accent='cold', support=None):
    """Two things side by side.

    left/right: dict(label, price, sub, rows=[str], image=None). The left
    column takes the accent, the right takes the support colour. Neither
    means better: this is a comparison, not a verdict.
    """
    bg, panel, panel2, edge = ground(background)
    acc = resolve(accent)
    if support is None:
        support = SUPPORT.get(TERRITORY.get(str(accent).lower(),
                                            str(accent).lower()))
    sup = resolve(support) if support is not None else acc

    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    heading(d, header, subheader, label, acc, bg)
    muted = lift(BODY, -0.30, bg)

    TOP, BOT = 430, H - 220
    colw = (W - M * 2 - 30) // 2
    has_art = bool(left.get('image') or right.get('image'))
    ART_H = 420 if has_art else 0

    for i, (side, x) in enumerate(((left, M), (right, M + colw + 30))):
        colour = acc if i == 0 else sup
        d.rounded_rectangle([x, TOP, x + colw, BOT], radius=22, fill=panel)

        y = TOP + 26
        if ART_H:
            if side.get('image'):
                C._rounded(im, C._fit(side['image'], colw - 52, ART_H),
                           (x + 26, y), radius=16)
            else:
                d.rounded_rectangle([x + 26, y, x + colw - 26, y + ART_H],
                                    radius=16, fill=panel2)
            d = ImageDraw.Draw(im)
            y += ART_H + 34

        lf = F(54, 800)
        for ln in C.wrap(d, side['label'], lf, colw - 60):
            d.text((x + 30, y), ln, font=lf, fill=INK); y += 68
        y += 14
        if side.get('price'):
            d.text((x + 30, y), side['price'], font=F(84, 800), fill=colour)
            y += 108
        if side.get('sub'):
            d.text((x + 30, y), side['sub'], font=F(38, 450), fill=muted)
            y += 70

        rows = side.get('rows') or []
        remaining = BOT - 40 - y
        size = 42
        while size > 30:
            rf = F(size, 450)
            need = sum(len(C.wrap(d, r, rf, colw - 60)) * (size + 14) + 12
                       for r in rows)
            if need <= remaining:
                break
            size -= 2
        rf = F(size, 450)
        for row in rows:
            for ln in C.wrap(d, row, rf, colw - 60):
                d.text((x + 30, y), ln, font=rf, fill=BODY); y += size + 14
            y += 12

    footer(im, bg, source, date, edge).save(out)
    return out


# ------------------------------------------------------------------ QUOTE ---
def quote(header, text, attribution, context, date, source, out,
          background='reported', accent='cold', media=None, label=None):
    """A statement someone made. Optional media sits under the quote.

    The quote grows to fill the space it has, so a short line lands large
    and a long one stays readable rather than overflowing.
    """
    bg, panel, panel2, edge = ground(background)
    acc = resolve(accent)
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)

    d.text((M, 140), header.upper(), font=F(44, 800), fill=acc)
    d.rectangle([M, 218, M + 160, 226], fill=acc)
    if label:
        filled_label(d, label, W - M, 128, acc, bg, anchor='rt')

    ART_H = 620 if media else 0
    top = 320
    bottom = H - 220 - (ART_H + 50 if media else 0)
    context = list(context or [])

    size = 148
    while size > 70:
        qf = F(size, 700)
        lines = C.wrap(d, f'"{text}"', qf, W - M * 2)
        block = (len(lines) * (size + 20) + 40 + 84
                 + len(context) * 72)
        if block <= bottom - top:
            break
        size -= 4

    qf = F(size, 700)
    lines = C.wrap(d, f'"{text}"', qf, W - M * 2)
    block = len(lines) * (size + 20) + 40 + 84 + len(context) * 72
    y = top + max(0, (bottom - top - block) / 2)

    for ln in lines:
        d.text((M, y), ln, font=qf, fill=INK); y += size + 20
    y += 40
    d.text((M, y), attribution, font=F(52, 800), fill=acc)
    y += 84

    cf = F(42, 450)
    for line in context:
        for ln in C.wrap(d, line, cf, W - M * 2):
            d.text((M, y), ln, font=cf, fill=BODY); y += 56
        y += 14

    if media:
        place_media(im, (M, H - 220 - ART_H, W - M, H - 220), media, panel)
        ImageDraw.Draw(im).rounded_rectangle(
            [M, H - 220 - ART_H, W - M, H - 220], radius=24, outline=acc,
            width=5)

    footer(im, bg, source, date, edge).save(out)
    return out
