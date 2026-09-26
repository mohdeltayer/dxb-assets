"""Digital Lounge fast-lane card, Arabic.

The same 1600 x 900 frame as `fast.py`, media full bleed, mirrored right to
left: the chip sits bottom right on the media, the footer runs mark and
name right, source centre, date left. Indigo ground, azure chip and rule,
Dubai type, the play mark. No pink or magenta.

Dubai's licence forbids redistribution and this repo is public, so the
font is not in git. Unzip Mohammad's dubai.zip into FONTS before rendering.
"""
import math
import os
import zlib

from PIL import Image, ImageDraw, ImageFont
import fast

FONTS = '/root/fonts-private/dubai/'
MARK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'digi-mark.jpg')


def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


GROUND, AZURE, INDIGO = hx('#141332'), hx('#28B6F6'), hx('#5552E0')
INK, BODY = hx('#F4F3FF'), hx('#C9C8E6')
AR = dict(direction='rtl', language='ar')

#: The banner's wave lines, repeated faintly behind the footer. The theme
#: follows the story the way DXB-KNIGHT's accent does; the chip and rule
#: stay azure on every theme. Each entry: left colour, right colour,
#: wave frequency, amplitude, line spacing. No pink or magenta.
THEMES = {
    'cold':      (INDIGO, AZURE, 4.0, 34, 16),        # sci-fi, horror, hardware, business
    'stylized':  (INDIGO, hx('#A5A3FF'), 2.4, 46, 18),  # RPG, fantasy, anime, story-led
    'playful':   (AZURE, hx('#3DDCB4'), 9.0, 20, 14),   # platformers, party, sports
    'spectacle': (AZURE, hx('#FFB547'), 6.0, 40, 11),   # blockbusters, film and TV
}
#: How far the lines rise out of the ground: subtle, the type sits on top.
STRENGTH = 0.45

#: The agreed picks, then the alternatives used only when Mohammad asks.
PICKS = ('عاجل', 'جديد', 'رسمي', 'تقرير', 'تسريب', 'شائعة', 'نظرة أولى',
         'متوفر الآن', 'تأجيل', 'السعر', 'تجربة')
ALTERNATIVES = ('الآن', 'وصل للتو', 'حسب تقارير', 'إشاعة', 'أول نظرة',
                'متاح الآن', 'صدر', 'مؤجل', 'سعر', 'انطباعات')

#: A regional story names its country, never "the Gulf".
COUNTRIES = ('الإمارات', 'السعودية', 'قطر', 'الكويت', 'البحرين', 'عُمان',
             'مصر', 'الأردن', 'المغرب', 'العراق', 'لبنان', 'تونس', 'الجزائر')

MONTHS = ('يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو',
          'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر')
_EN = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct',
       'nov', 'dec')


def arabic_date(date):
    """'26 Sep 2026' -> '26 سبتمبر 2026'. Western digits, as Gulf outlets use."""
    day, month, year = date.split()
    return f'{int(day)} {MONTHS[_EN.index(month[:3].lower())]} {year}'


def F(weight, size):
    path = f'{FONTS}Dubai-{weight}.ttf'
    if not os.path.exists(path):
        raise FileNotFoundError(
            f'{path} is missing. Ask Mohammad to upload dubai.zip and unzip it '
            f'into {FONTS} (the font is not kept in the repo).')
    return ImageFont.truetype(path, size)


def _chip(d, text, x_right, fill, ink):
    f = F('Bold', 44)
    w = d.textlength(text, font=f, **AR)
    bw, bh = w + 56, 66
    x0, y0 = x_right - bw, fast.MH - 34 - bh
    d.rounded_rectangle([x0, y0, x_right, y0 + bh], radius=10, fill=fill)
    d.text((x_right - 28, y0 + bh / 2 + 2), text, font=f, fill=ink, anchor='rm', **AR)
    return x0


def _chips(d, label, country):
    x = fast.W - fast.M
    if label:
        x = _chip(d, label, x, AZURE, GROUND) - 16
    if country:
        _chip(d, country, x, INDIGO, INK)


def _waves(w, h, theme, seed):
    """Footer-sized cut of the banner lines. `seed` shifts the phase so no
    two cards share exactly the same footer."""
    left, right, freq, amp, gap = THEMES[theme]
    k = 3
    big = Image.new('RGB', (w * k, h * k), GROUND)
    d = ImageDraw.Draw(big)
    ph = (seed % 628) / 100
    for j in range(-4, h // gap + 5):
        pts = []
        for x in range(0, w * k + 24, 12):
            u = x / (w * k)
            y = (j * gap + amp * math.sin(u * freq + j * 0.22 + ph)
                 + amp * 0.5 * math.sin(u * freq * 2.3 + ph * 1.7)) * k
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            u = a[0] / (w * k)
            c = tuple(int(left[i] + (right[i] - left[i]) * u) for i in range(3))
            c = tuple(int(GROUND[i] + (c[i] - GROUND[i]) * STRENGTH) for i in range(3))
            d.line((a, b), fill=c, width=2 * k)
    return big.resize((w, h), Image.LANCZOS)


def _footer(im, source, date, theme, seed):
    W, H, M, MH, RULE = fast.W, fast.H, fast.M, fast.MH, fast.RULE
    im.paste(_waves(W, H - MH - RULE, theme, seed), (0, MH + RULE))
    d = ImageDraw.Draw(im)
    d.rectangle([0, MH, W, MH + RULE], fill=AZURE)
    base = MH + RULE + 62
    size = 60
    mark = Image.open(MARK).convert('RGB').resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((size, size), Image.LANCZOS), mask.resize((size, size), Image.LANCZOS)
    im.paste(mark, (W - M - size, base - size // 2), mask)
    d = ImageDraw.Draw(im)
    d.text((W - M - size - 18, base), 'ديجيتال لاونج', font=F('Bold', 42),
           fill=INK, anchor='rm', **AR)
    d.text((W / 2, base), source, font=F('Medium', 36), fill=BODY, anchor='mm', **AR)
    d.text((M, base), arabic_date(date), font=F('Medium', 36), fill=BODY, anchor='lm', **AR)


def fast_ar(media, date, source, out, label=None, country=None, theme='cold',
            crop=False, video=None, clip_start=0, clip_seconds=8, audio=False):
    """`date` in the English form ('26 Sep 2026'); `source` as the Arabic
    reader knows it (فاميتسو, IGN); `theme` one of THEMES, chosen per story
    like DXB-KNIGHT's accent."""
    if theme not in THEMES:
        raise ValueError(f'theme is one of {", ".join(THEMES)}')
    seed = zlib.crc32(os.path.basename(out).encode())
    if label and label not in PICKS + ALTERNATIVES:
        raise ValueError(f'"{label}" is not an Arabic fast chip: {"، ".join(PICKS)}')
    if country and country not in COUNTRIES:
        raise ValueError(f'"{country}" is not a country chip: {"، ".join(COUNTRIES)}')
    return fast.compose(media, out, GROUND,
                        lambda im: _footer(im, source, date, theme, seed),
                        lambda d: _chips(d, label, country),
                        crop, video, clip_start, clip_seconds, audio)
