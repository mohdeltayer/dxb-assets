"""DXB-KNIGHT flexible entertainment design system.

Same 1600 x 2000 canvas, same wireframe, same type hierarchy. What varies
is background family, accent choice and treatment. Colour and effect are
separate: a bright accent is a colour, glow is a treatment, and one does
not imply the other.
"""
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
           display=None, gulf=False):
    """One story.

    `background` takes a mode ('reported', 'voiced') or a name ('navy',
    'purple'). `accent` takes a territory ('cold', 'stylized', 'playful',
    'spectacle') or an accent name. `support` is picked automatically unless
    given. `gulf=True` adds the gold GULF chip beside the label; it rides on
    whatever accent the topic already earned.
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

    place_media(im, ART, media, panel)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(list(ART), radius=24, outline=acc,
                        width=6 if treatment != 'flat' else 5)

    if treatment == 'neon':
        im = _glow(im, lambda dd, col: dd.rounded_rectangle(list(ART), radius=24,
                                                            outline=col, width=6), acc)
        d = ImageDraw.Draw(im)

    box = filled_label(d, label, M + 34, ART[3] - 34, acc, bg, anchor='lb')
    if gulf:
        filled_label(d, 'GULF', box[2] + 18, ART[3] - 34, ACCENTS[GULF_CHIP],
                     bg, anchor='lb')

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

    footer(im, bg, source, date, edge).save(out)
    return out
