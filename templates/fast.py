"""DXB-KNIGHT fast-lane card.

For news posted within minutes of breaking. The image is the story and the
post text carries the facts, so the card holds only what makes it ours: the
label, one headline line and the mark. 1600 x 1200 is 4:3, which X shows
uncropped in the feed, and it leaves an exact 16:9 panel for the image.

Same palette and argument names as flex.py. The full card (flex.single)
remains the considered version, posted later as a reply to the fast post.
"""
from PIL import Image, ImageDraw
import cards as C
import flex

W, H, M = 1600, 1200, 40
# 1520 x 855 is exactly 16:9, the shape of nearly every trailer frame and
# screenshot, so the usual source fills the panel with no bars.
PANEL = (M, M, W - M, M + 855)
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


def fast(kicker, headline, label, media, date, source, out,
         background='reported', accent='cold', crop=False):
    """One image, one line. Raises if the headline needs a second line:
    a fast card that needs two lines of headline is a full card."""
    bg, panel, panel2, edge = flex.ground(background)
    acc = flex.resolve(accent)
    sup = flex.resolve(flex.SUPPORT.get(flex.TERRITORY.get(accent, accent), accent))

    im = Image.new('RGB', (W, H), bg)
    plate = _media(media, PANEL, panel, crop)
    mask = Image.new('L', plate.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *plate.size], radius=22, fill=255)
    im.paste(plate, PANEL[:2], mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(list(PANEL), radius=22, outline=acc, width=5)
    flex.filled_label(d, label, PANEL[0] + 26, PANEL[3] - 26, acc, bg, size=40, anchor='lb')

    # Strip: kicker and headline left, mark and source right.
    crest_w = 330
    room = W - M * 2 - crest_w - 30
    d.text((M, 960), kicker.upper(), font=F(30, 800), fill=sup, anchor='lm')
    for size in (68, 62, 56):
        hf = F(size, 800)
        if d.textlength(headline, font=hf) <= room:
            break
    else:
        raise ValueError(f'headline is {int(d.textlength(headline, font=hf) - room)}px '
                         f'too long at 56pt: cut words, or build the full card')
    d.text((M, 1055), headline, font=hf, fill=flex.INK, anchor='lm')

    crest = Image.open(C.CREST).convert('RGBA').resize((52, 52), Image.LANCZOS)
    cx = W - M - crest_w
    im.paste(crest, (cx, 960 - 26), crest)
    d = ImageDraw.Draw(im)
    d.text((cx + 66, 960), 'DXB-KNIGHT', font=F(30, 800), fill=flex.INK, anchor='lm')
    muted = flex.lift(flex.BODY, -0.25, bg)
    d.text((W - M, 1035), source.upper(), font=F(24, 600), fill=muted, anchor='rm')
    d.text((W - M, 1073), date.upper(), font=F(24, 600), fill=muted, anchor='rm')
    im.save(out)
    return out
