"""Cards drawn where the Dubai font is (21 Oct 2026). The container has had no font since the
reset, so a job file describes its cards and the runner draws them before the render:

    "gfx": [{"file": "ys8-gfx-date.png", "kind": "fact", "label": "موعد الصدور",
             "value": "25 فبراير 2027", "note": "على Nintendo Switch 2"}]

Each card is drawn on a transparent canvas (numgfx.canvas) and the shot that names it
(`-gfx-` in the file name) lays it on the ground as before (numgfx.slide; `ground_footage`
puts the game's trailer behind it). One fact per card, held alone or under a one-line frame
(CLAUDE.md, 14 Oct 2026: one fact, one place)."""
from PIL import Image, ImageDraw, ImageFilter
import fast_ar as A, ig_ar as G, numgfx as NG, reel as RL

X0, X1 = G.SAFE_LEFT, NG.W - G.SAFE_RIGHT     # the plate spans the safe zone's width
CY = 960                                      # plate centre: clear of the headline band and the story lines
VALUE_SIZES = (128, 116, 104, 92, 84)
LABEL, NOTE = 46, 52


def fact(path, value, label=None, note=None, theme='cold'):
    """One figure or date, large, on a soft plate tinted with the theme; an optional label above
    it (body colour, accent rule under it) and an optional note below (ink). Label and note open
    on an Arabic word; nothing leaves the safe zone; no text under numgfx.MIN_TEXT."""
    for t, what in ((label, 'card label'), (note, 'card note')):
        if t:
            RL.rtl_starts([t], what)
    left, right = A.THEMES[theme][:2]
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 72
    vs = next((s for s in VALUE_SIZES if probe.textlength(value, font=A.F('Bold', s), **G.AR) <= room), None)
    if vs is None:
        raise ValueError(f'card value is wider than the plate at {VALUE_SIZES[-1]} px: {value}')
    for t, w, s in ((label, 'Medium', LABEL), (note, 'Medium', NOTE)):
        if t and probe.textlength(t, font=A.F(w, s), **G.AR) > room:
            raise ValueError(f'card text is wider than the plate: {t}')
    rows = ([('label', LABEL + 34)] if label else []) + [('value', vs + 30)] + ([('note', NOTE + 26)] if note else [])
    h = sum(r[1] for r in rows) + 96
    y0, y1 = CY - h // 2, CY + h // 2
    if y0 < G.SAFE_TOP or y1 > G.SAFE_BOTTOM:
        raise ValueError(f'card ({y0}-{y1}) leaves the safe zone')
    im = NG.canvas()
    soft = Image.new('L', (NG.W, NG.H), 0)
    ImageDraw.Draw(soft).rounded_rectangle([X0 - 10, y0 - 10, X1 + 10, y1 + 10], radius=40, fill=120)
    sh = Image.new('RGBA', (NG.W, NG.H), A.GROUND + (255,)); sh.putalpha(soft.filter(ImageFilter.GaussianBlur(16)))
    im.alpha_composite(sh)
    tint = tuple(round(A.GROUND[i] * 0.84 + left[i] * 0.16) for i in range(3))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([X0, y0, X1, y1], radius=32, fill=tint + (200,), outline=right + (110,), width=2)
    cx, y = (X0 + X1) // 2, y0 + 48
    for kind, step in rows:
        if kind == 'label':
            d.text((cx, y + LABEL), label, font=A.F('Medium', LABEL), fill=A.BODY, anchor='ms', **G.AR)
            d.rounded_rectangle([cx - 60, y + LABEL + 16, cx + 60, y + LABEL + 22], radius=3, fill=right)
        elif kind == 'value':
            d.text((cx, y + vs), value, font=A.F('Bold', vs), fill=A.INK, anchor='ms', **G.AR)
        else:
            d.text((cx, y + NOTE), note, font=A.F('Medium', NOTE), fill=A.INK, anchor='ms', **G.AR)
        y += step
    im.save(path)
    return path


KINDS = {'fact': fact}


def build(item, path, theme):
    """One card from a job file's "gfx" entry."""
    kw = {k: v for k, v in item.items() if k not in ('file', 'kind')}
    return KINDS[item.get('kind', 'fact')](path, theme=kw.pop('theme', theme), **kw)
