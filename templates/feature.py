"""Magazine pages for a multi-image post.

A feature is a run of pages that ride in one post (four on X) and open as a
swipe. Each page is a full 1600x2000 card so it sits in the same feed as the
flex cards, but the chrome is a magazine's: a running header naming the
series and part, a segmented progress bar, a page number, and a cue at the
foot of every page saying what comes next. The cover carries the headline
and a contents list; inside pages carry one section each, with a stat or a
pull quote to break the column.

Palette and type are the card system's. Geometry is this file's own.
"""
from PIL import Image, ImageDraw
import flex
from flex import W, H, M, F, INK, BODY, lift, resolve, ground, footer

THEMES = {
    # the channel's own voiced purple with its cyan
    'knight':   dict(bg=(29, 20, 64),  acc=(66, 215, 255), hi=(66, 215, 255)),
    # PlayStation blue on the channel purple: brand as accent only
    'sony':     dict(bg=(29, 20, 64),  acc=(0, 112, 209),  hi=(77, 163, 255)),
    # PlayStation blue on a blue-black page: brand as the room
    'sony-deep':dict(bg=(9, 20, 44),   acc=(0, 112, 209),  hi=(77, 163, 255)),
    'nintendo': dict(bg=(29, 20, 64),  acc=(230, 0, 18),   hi=(255, 96, 106)),
    'nintendo-deep': dict(bg=(38, 8, 16), acc=(230, 0, 18), hi=(255, 96, 106)),
    'xbox':     dict(bg=(29, 20, 64),  acc=(16, 124, 16),  hi=(82, 204, 82)),
    'xbox-deep':dict(bg=(8, 22, 14),   acc=(16, 124, 16),  hi=(82, 204, 82)),
}


def _theme(theme, background, accent):
    if theme:
        t = THEMES[theme]
        bg = t['bg']
        return (bg,) + flex.surfaces(bg), t['acc'], t['hi']
    bg, *surf = ground(background)
    acc = resolve(accent)
    return (bg,) + tuple(surf), acc, acc


TOP = 210            # first content line, below the running header + bar
CUE_Y = H - 250      # the next-page cue sits above the footer rule
BODY_SIZE, BODY_STEP = 48, 62


def _chrome(im, series, part, n, total, acc, hi, bg, surf):
    d = ImageDraw.Draw(im)
    d.text((M, 78), f'{series}  ·  {part}'.upper(), font=F(30, 800), fill=hi, anchor='lm')
    d.text((W - M, 78), f'{n:02d} / {total:02d}', font=F(30, 600),
           fill=lift(BODY, -0.15, bg), anchor='rm')
    gap, y = 14, 124
    seg = (W - 2 * M - gap * (total - 1)) / total
    for i in range(total):
        x0 = M + i * (seg + gap)
        d.rounded_rectangle([x0, y, x0 + seg, y + 8], radius=4,
                            fill=acc if i < n else surf[1])


def _cue(im, text, hi, bg, last=False):
    """The page-turn line. Arrow drawn, not typed, so no font can drop it."""
    d = ImageDraw.Draw(im)
    f = F(34, 800)
    t = text.upper()
    tw = d.textlength(t, font=f)
    x = W - M - 70
    d.text((x, CUE_Y), t, font=f, fill=hi if not last else lift(BODY, -0.1, bg),
           anchor='rm')
    ax0, ax1, ay = x + 18, W - M, CUE_Y
    col = hi if not last else lift(BODY, -0.1, bg)
    d.line([ax0, ay, ax1, ay], fill=col, width=5)
    d.polygon([(ax1, ay), (ax1 - 16, ay - 12), (ax1 - 16, ay + 12)], fill=col)


def cover(series, part, title, dek, contents, media, date, source, out,
          total=4, background='voiced', accent='cold', theme=None):
    (bg, *surf), acc, hi = _theme(theme, background, accent)
    im = Image.new('RGB', (W, H), bg)
    _chrome(im, series, part, 1, total, acc, hi, bg, surf)
    flex.place_media(im, (M, TOP - 40, W - M, 930), media, surf[0])
    d = ImageDraw.Draw(im)
    y = 990
    tf = F(108, 800)
    for ln in flex.C.wrap(d, title, tf, W - 2 * M):
        d.text((M, y), ln, font=tf, fill=INK); y += 118
    y += 18
    df = F(46, 450)
    for ln in flex.C.wrap(d, dek, df, W - 2 * M):
        d.text((M, y), ln, font=df, fill=BODY); y += 58
    y += 48
    d.text((M, y), 'INSIDE', font=F(28, 800), fill=hi); y += 48
    nf, cf = F(38, 800), F(40, 450)
    for i, item in enumerate(contents, start=2):
        d.text((M, y), f'{i:02d}', font=nf, fill=hi)
        d.text((M + 90, y), item, font=cf, fill=INK); y += 56
    _cue(im, 'swipe to open', hi, bg)
    return footer(im, bg, source, date, surf[2]).save(out) or out


def page(series, part, n, section_title, paras, date, source, out, next_title,
         total=4, stat=None, pull=None, media=None, background='voiced',
         accent='cold', last=False, theme=None, pull_by=None):
    """One section. `stat` is (big, caption); `pull` is a quote line.
    `media` is an optional strip under the section title."""
    (bg, *surf), acc, hi = _theme(theme, background, accent)
    im = Image.new('RGB', (W, H), bg)
    _chrome(im, series, part, n, total, acc, hi, bg, surf)
    d = ImageDraw.Draw(im)
    y = TOP
    d.text((M - 6, y - 60), f'{n:02d}', font=F(220, 800), fill=surf[1])
    y += 190
    tf = F(84, 800)
    for ln in flex.C.wrap(d, section_title, tf, W - 2 * M):
        d.text((M, y), ln, font=tf, fill=INK); y += 94
    y += 24
    d.rectangle([M, y, M + 120, y + 8], fill=acc); y += 44
    if media:
        flex.place_media(im, (M, y, W - M, y + 420), media, surf[0]); y += 450
        d = ImageDraw.Draw(im)
    bf = F(BODY_SIZE, 450)
    for p in paras:
        for ln in flex.C.wrap(d, p, bf, W - 2 * M):
            d.text((M, y), ln, font=bf, fill=BODY); y += BODY_STEP
        y += 20
    if stat:
        big, cap = stat
        y += 20
        d.rounded_rectangle([M, y, W - M, y + 250], radius=22, fill=surf[0])
        d.text((M + 48, y + 125), big, font=F(140, 800), fill=hi, anchor='lm')
        bw = d.textlength(big, font=F(140, 800))
        cf = F(38, 450)
        cy = y + 125 - 24 * (len(flex.C.wrap(d, cap, cf, W - 2 * M - bw - 150)) - 1)
        for ln in flex.C.wrap(d, cap, cf, W - 2 * M - bw - 150):
            d.text((M + 100 + bw, cy), ln, font=cf, fill=INK, anchor='lm'); cy += 48
        y += 290
    if pull:
        y += 20
        d.rectangle([M, y, M + 10, y + 10], fill=acc)
        qf = F(60, 800)
        lines = flex.C.wrap(d, pull, qf, W - 2 * M - 60)
        d.rectangle([M, y, M + 8, y + 72 * len(lines)], fill=acc)
        for ln in lines:
            d.text((M + 48, y), ln, font=qf, fill=INK); y += 72
        if pull_by:
            y += 10
            d.text((M + 48, y), pull_by.upper(), font=F(28, 700), fill=hi); y += 40
    if y > CUE_Y - 60:
        raise ValueError(f'page {n} runs {y - (CUE_Y - 60)}px into the cue: cut copy')
    _cue(im, ('next · ' + next_title) if not last else next_title, acc, bg, last)
    return footer(im, bg, source, date, surf[2]).save(out) or out
