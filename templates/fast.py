"""DXB-KNIGHT fast-lane card.

For news posted within minutes of breaking. The image is the story and the
post text carries the facts, so the card is the image and the footer: the
DXB-KNIGHT mark, the source and the date, in the same places as on every
full card. No headline and no kicker.

The image panel is 1520 x 855, exactly 16:9, the shape of nearly every
trailer frame and screenshot, so the usual source fills it with no bars.
The full card (flex.single) remains the considered version, posted later as
a reply to the fast post.
"""
from PIL import Image, ImageDraw
import cards as C
import flex

M = 40
PANEL = (M, M, 1600 - M, M + 855)
W, H = 1600, PANEL[3] + 150
F = flex.F


def _media(path, box, backing, crop):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    src = Image.open(C.U + path).convert('RGB')
    if crop:
        # Fill the panel. Only for frames where nothing important sits at
        # the edges: a face, a logo or headline text means contain instead.
        k = max(bw / src.width, bh / src.height)
        art = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
        l, t = (art.width - bw) // 2, (art.height - bh) // 2
        return art.crop((l, t, l + bw, t + bh))
    plate = Image.new('RGB', (bw, bh), backing)
    k = min(bw / src.width, bh / src.height)
    art = src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))), Image.LANCZOS)
    plate.paste(art, ((bw - art.width) // 2, (bh - art.height) // 2))
    return plate


def fast(media, date, source, out, label=None,
         background='reported', accent='cold', crop=False):
    bg, panel, panel2, edge = flex.ground(background)
    acc = flex.resolve(accent)

    im = Image.new('RGB', (W, H), bg)
    plate = _media(media, PANEL, panel, crop)
    mask = Image.new('L', plate.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *plate.size], radius=22, fill=255)
    im.paste(plate, PANEL[:2], mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(list(PANEL), radius=22, outline=acc, width=5)
    if label:
        flex.filled_label(d, label, PANEL[0] + 26, PANEL[3] - 26, acc, bg, size=40, anchor='lb')

    # Footer: the full card's footer, same order and weights.
    base = PANEL[3] + 80
    crest = Image.open(C.CREST).convert('RGBA').resize((56, 56), Image.LANCZOS)
    im.paste(crest, (M, base - 28), crest)
    d = ImageDraw.Draw(im)
    muted = flex.lift(flex.BODY, -0.25, bg)
    d.text((M + 72, base), 'DXB-KNIGHT', font=F(32, 800), fill=flex.INK, anchor='lm')
    d.text((W / 2, base), source.upper(), font=F(30, 600), fill=muted, anchor='mm')
    d.text((W - M, base), date.upper(), font=F(30, 600), fill=muted, anchor='rm')
    im.save(out)
    return out
