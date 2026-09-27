"""Digital Lounge Instagram card, Arabic, 4:5 (1080 x 1350).

The fast card's language in a portrait frame: the media on top, an azure
rule under it, the chip right to left, the wave footer with the play mark
and the name right, the date left and the source beneath. The space a 16:9
picture leaves in a 4:5 frame takes a short Arabic headline (`headline`),
because an Instagram caption is folded away behind "more"; without one the
media is set on a blurred, darkened copy of itself instead.
"""
import os

from PIL import Image, ImageDraw, ImageFilter
import cards as C
import fast_ar as A

W, H = 1080, 1350
MH = 608                     # 16:9 media, full width
RULE = 6
FOOT = 176                   # wave footer
M = 44
AR = A.AR


def _media(path, crop, box_h):
    src = Image.open(C.U + path).convert('RGB')
    if crop:
        k = max(W / src.width, box_h / src.height)
        art = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
        l, t = (art.width - W) // 2, (art.height - box_h) // 2
        return art.crop((l, t, l + W, t + box_h))
    # Blurred, darkened fill behind the contained picture: no black bars.
    k = max(W / src.width, box_h / src.height)
    back = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
    l, t = (back.width - W) // 2, (back.height - box_h) // 2
    back = back.crop((l, t, l + W, t + box_h)).filter(ImageFilter.GaussianBlur(36))
    back = Image.blend(back, Image.new('RGB', back.size, A.GROUND), 0.55)
    k = min(W / src.width, box_h / src.height)
    art = src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))), Image.LANCZOS)
    back.paste(art, ((W - art.width) // 2, (box_h - art.height) // 2))
    return back


def _chip(d, text, x_right, y_bottom, fill, ink, size=40):
    f = A.F('Bold', size)
    w = d.textlength(text, font=f, **AR)
    bw, bh = w + 48, int(size * 1.5)
    x0, y0 = x_right - bw, y_bottom - bh
    d.rounded_rectangle([x0, y0, x_right, y_bottom], radius=10, fill=fill)
    d.text((x_right - 24, y0 + bh / 2 + 2), text, font=f, fill=ink, anchor='rm', **AR)
    return x0


def _chips(d, label, country, y_bottom):
    x = W - M
    if label:
        x = _chip(d, label, x, y_bottom, A.AZURE, A.GROUND) - 14
    if country:
        _chip(d, country, x, y_bottom, A.INDIGO, A.INK)


def _wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if cur and d.textlength(trial, font=f, **AR) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + [cur] if cur else lines


def _footer(im, source, date, theme, seed):
    top = H - FOOT
    im.paste(A._waves(W, FOOT, theme, seed), (0, top))
    d = ImageDraw.Draw(im)
    d.rectangle([0, top, W, top + 3], fill=A.hx('#3F3DA8'))
    row = top + 58
    size = 58
    mark = Image.open(A.MARK).convert('RGB').resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((size, size), Image.LANCZOS), mask.resize((size, size), Image.LANCZOS)
    im.paste(mark, (W - M - size, row - size // 2), mask)
    d = ImageDraw.Draw(im)
    d.text((W - M - size - 16, row), 'ديجيتال لاونج', font=A.F('Bold', 40),
           fill=A.INK, anchor='rm', **AR)
    d.text((M, row), A.arabic_date(date), font=A.F('Medium', 32), fill=A.BODY,
           anchor='lm', **AR)
    f = A.F('Medium', 30)
    if d.textlength(source, font=f, **AR) > W - 2 * M and '(' in source:
        source = source.split('(')[0].strip()
    d.text((W - M, row + 70), source, font=f, fill=A.BODY, anchor='rm', **AR)


def ig_ar(media, date, source, out, headline=None, label=None, country=None,
          theme='cold', crop=False):
    """`headline`: one short Arabic line or two, the hook, not the caption.
    Without it the media takes the whole space above the footer."""
    if theme not in A.THEMES:
        raise ValueError(f'theme is one of {", ".join(A.THEMES)}')
    if label and label not in A.PICKS + A.ALTERNATIVES:
        raise ValueError(f'"{label}" is not an Arabic fast chip: {"، ".join(A.PICKS)}')
    if country and country not in A.COUNTRIES:
        raise ValueError(f'"{country}" is not a country chip: {"، ".join(A.COUNTRIES)}')
    im = Image.new('RGB', (W, H), A.GROUND)
    seed = __import__('zlib').crc32(os.path.basename(out).encode())
    if headline:
        im.paste(_media(media, crop, MH), (0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, MH, W, MH + RULE], fill=A.AZURE)
        panel_top, panel_bot = MH + RULE, H - FOOT
        _chips(d, label, country, MH - 28)
        f = A.F('Bold', 68)
        lines = _wrap(d, headline, f, W - 2 * M)
        if len(lines) > 4:
            raise ValueError(f'headline runs to {len(lines)} lines; keep it to 4')
        step = 100
        y = panel_top + ((panel_bot - panel_top) - step * len(lines)) / 2
        for line in lines:
            d.text((W - M, y + step / 2), line, font=f, fill=A.INK, anchor='rm', **AR)
            y += step
    else:
        box = H - FOOT - RULE
        im.paste(_media(media, crop, box), (0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, box, W, box + RULE], fill=A.AZURE)
        _chips(d, label, country, box - 34)
    _footer(im, source, date, theme, seed)
    im.save(out)
    return out
