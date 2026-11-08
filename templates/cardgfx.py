"""Cards drawn where the Dubai font is (21 Oct 2026). The container has had no font since the
reset, so a job file describes its cards and the runner draws them before the render:

    "gfx": [{"file": "ys8-gfx-date.png", "kind": "fact", "label": "موعد الصدور",
             "value": "25 فبراير 2027", "note": "على Nintendo Switch 2"}]

A UAE price is written ["aed", "25.20"]: the digits with the Central Bank's dirham symbol to
their left, as on the strip (26 Oct 2026; the house glossary never puts «درهم» on screen).

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


def _vwidth(probe, value, size):
    """(width, symbol height) of a card value at a size; ('aed', digits) adds the dirham symbol."""
    f = A.F('Bold', size)
    if isinstance(value, tuple):
        bb = probe.textbbox((0, 0), value[1], font=f, anchor='ls')
        dh = bb[3] - bb[1]
        return probe.textlength(value[1], font=f, **G.AR) + round(dh * 0.3) + round(RL.SYM.width * dh / RL.SYM.height), dh
    return probe.textlength(value, font=f, **G.AR), 0


def fact(path, value, label=None, note=None, theme='cold'):
    """One figure or date, large, on a soft plate tinted with the theme; an optional label above
    it (body colour, accent rule under it) and an optional note below (ink). Label and note open
    on an Arabic word; nothing leaves the safe zone; no text under numgfx.MIN_TEXT."""
    for t, what in ((label, 'card label'), (note, 'card note')):
        if t:
            RL.rtl_starts([t], what)
    if isinstance(value, list):
        value = tuple(value)
    if isinstance(value, tuple) and (len(value) != 2 or value[0] != 'aed' or not str(value[1]).strip()):
        raise ValueError(f"card value {value!r}: use a string, or ['aed', '25.20'] for the dirham symbol")
    left, right = A.THEMES[theme][:2]
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 72
    vs = next((s for s in VALUE_SIZES if _vwidth(probe, value, s)[0] <= room), None)
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
        elif kind == 'value' and isinstance(value, tuple):     # digits, the dirham symbol to their left
            w, dh = _vwidth(probe, value, vs)
            sw = round(RL.SYM.width * dh / RL.SYM.height)
            d.text((cx + w / 2, y + vs), value[1], font=A.F('Bold', vs), fill=A.INK, anchor='rs', **G.AR)
            sym = Image.new('RGBA', (sw, dh), A.INK + (255,))
            sym.putalpha(RL.SYM.resize((sw, dh), Image.LANCZOS))
            im.alpha_composite(sym, (round(cx - w / 2), y + vs - dh))
            d = ImageDraw.Draw(im)
        elif kind == 'value':
            d.text((cx, y + vs), value, font=A.F('Bold', vs), fill=A.INK, anchor='ms', **G.AR)
        else:
            d.text((cx, y + NOTE), note, font=A.F('Medium', NOTE), fill=A.INK, anchor='ms', **G.AR)
        y += step
    im.save(path)
    return path


# ---------- review scores (studio, adv-20261104-review-scores-template, Mohammad 4 Nov 2026) ----------
# Three cards for the review-scores template: the spread of outlet scores, one outlet's verdict with a liked and a
# disliked line, and the Metacritic and OpenCritic totals with the time they were read. Scores are shown on each outlet's
# own scale exactly as printed ("9/10", "5/5", "95/100", or a word such as «أسطورية»); never converted. Outlet names are
# text (no logos unless licensed). Every Arabic line opens on an Arabic word; a score is drawn left to right on its own.

NEG = (0xE5, 0x38, 0x3B)          # the disliked line's tag: crimson (never pink)
TOP = 470                         # a review card starts under the chip row and the credit line (the headline has gone)
RCY = 930                         # review cards sit a little higher than CY: more of them, still clear of the story lines


def _plate(im, y0, y1, theme, alpha=205):
    left, right = A.THEMES[theme][:2]
    soft = Image.new('L', (NG.W, NG.H), 0)
    ImageDraw.Draw(soft).rounded_rectangle([X0 - 10, y0 - 10, X1 + 10, y1 + 10], radius=40, fill=120)
    sh = Image.new('RGBA', (NG.W, NG.H), A.GROUND + (255,)); sh.putalpha(soft.filter(ImageFilter.GaussianBlur(16)))
    im.alpha_composite(sh)
    tint = tuple(round(A.GROUND[i] * 0.84 + left[i] * 0.16) for i in range(3))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([X0, y0, X1, y1], radius=32, fill=tint + (alpha,), outline=right + (110,), width=2)
    return d, left, right


def _fits(d, text, weight, sizes, room, rtl=True):
    for s in sizes:
        if d.textlength(text, font=A.F(weight, s), **(G.AR if rtl else {})) <= room:
            return s
    raise ValueError(f'card text is wider than the plate at {sizes[-1]} px: {text}')


def _wrap(d, text, f, width, most, what='card'):
    """Greedy wrap; a break set by hand (\\n) is kept. Every visual line is checked to open on an Arabic word (a wrapped
    line that starts on a digit or a Latin name flips on screen)."""
    if '\n' in text:
        lines = [x for part in text.split('\n') if part.strip() for x in _wrap(d, part, f, width, most, what)]
        if len(lines) > most:
            raise ValueError(f'card text needs {len(lines)} lines (at most {most}); shorten it: {text}')
        return lines
    lines, cur = [], ''
    for w in text.split():
        trial = (cur + ' ' + w).strip()
        if cur and d.textlength(trial, font=f, **G.AR) > width:
            lines.append(cur); cur = w
        else:
            cur = trial
    lines += [cur] if cur else []
    if len(lines) > most:
        raise ValueError(f'card text needs {len(lines)} lines (at most {most}); shorten it: {text}')
    RL.rtl_starts(lines, what)
    return lines


def _is_word(score):
    """A verbal verdict («أسطورية», «يوصى بها») rather than digits."""
    return any('؀' <= ch <= 'ۿ' for ch in str(score))


def scores(path, rows, title=None, theme='cold', show=None):
    """The spread: 3 to 6 outlets, one row each in two lines: the outlet (Arabic, then the Latin in brackets) across the
    row, then the score as the outlet printed it on the left in the theme accent and the review date on the right.
    `rows`: [{"outlet": "آي جي إن (IGN)", "score": "9/10", "date": "في 4 نوفمبر"}, ...]; `title` an optional frame line
    above («تقييمات المواقع»). `show` draws only the first N rows on the full-size plate, so the card can build in two
    beats (pace rule: something changes every 3 to 4 s) without the plate jumping."""
    if not 3 <= len(rows) <= 6:
        raise ValueError(f'the spread holds 3 to 6 outlets, not {len(rows)}')
    RL.rtl_starts([r['outlet'] for r in rows] + [r['date'] for r in rows] + ([title] if title else []), 'scores card')
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 96
    name_size = min(_fits(probe, r['outlet'], 'Bold', (52, 48, 44, 40), room) for r in rows)
    for r in rows:
        word = _is_word(r['score'])
        sw = probe.textlength(str(r['score']), font=A.F('Bold', 52 if word else 64), **(G.AR if word else {}))
        dw = probe.textlength(r['date'], font=A.F('Medium', NG.MIN_TEXT), **G.AR)
        if sw + dw + 40 > room:
            raise ValueError(f"score and date do not fit one line: {r['score']} / {r['date']}")
    row_h, title_h = 140, (90 if title else 0)
    h = title_h + row_h * len(rows) + 56
    y0 = max(TOP, RCY - h // 2)
    y1 = y0 + h
    if y1 > G.SAFE_BOTTOM - 120:
        raise ValueError(f'scores card ({y0}-{y1}) runs into the story lines; fewer outlets')
    im = NG.canvas()
    d, left, right = _plate(im, y0, y1, theme)
    y = y0 + 28
    if title:
        d.text((X1 - 48, y + 50), title, font=A.F('Medium', 48), fill=A.BODY, anchor='rs', **G.AR)
        y += title_h
    for i, r in enumerate(rows[:show] if show else rows):
        if i:
            d.line([X0 + 40, y, X1 - 40, y], fill=right + (70,), width=2)
        d.text((X1 - 48, y + 60), r['outlet'], font=A.F('Bold', name_size), fill=A.INK, anchor='rs', **G.AR)
        d.text((X1 - 48, y + 120), r['date'], font=A.F('Medium', NG.MIN_TEXT), fill=A.BODY, anchor='rs', **G.AR)
        word = _is_word(r['score'])
        d.text((X0 + 48, y + 124), str(r['score']), font=A.F('Bold', 52 if word else 64), fill=right,
               anchor='ls', **(G.AR if word else {}))
        y += row_h
    im.save(path)
    return path


def verdict(path, outlet, reviewer, score, positive, negative, score_note=None, theme='cold', stage=2):
    """One outlet's review: the outlet and reviewer, the score as printed (or the outlet's word), then one line it liked
    and one it did not, each a short faithful excerpt in «» (15 words at most). `positive` and `negative` are the Arabic
    text; the job keeps the original wording beside it for the translation check. `stage=1` draws the outlet and the
    score only on the full plate (the first beat), `stage=2` the whole card."""
    RL.rtl_starts([outlet, reviewer, positive, negative] + ([score_note] if score_note else []), 'verdict card')
    for q in (positive, negative):
        if len(q.split()) > 15:
            raise ValueError(f'quote over 15 words: {q}')
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 96
    word = _is_word(score)
    ssize = _fits(probe, str(score), 'Bold', (112, 100, 92, 84), room, rtl=word)
    osize = _fits(probe, outlet, 'Bold', (54, 50, 46, 42), room)
    qf = A.F('Medium', 46)
    plines = _wrap(probe, f'«{positive}»', qf, room - 20, 3, 'verdict quote')
    nlines = _wrap(probe, f'«{negative}»', qf, room - 20, 3, 'verdict quote')
    rows = 70 + 56 + (ssize + 36) + (52 if score_note else 0) + 30 + (66 + 58 * len(plines)) + 24 + (66 + 58 * len(nlines))
    h = rows + 80
    y0 = max(TOP, RCY - h // 2)
    y1 = y0 + h
    if y1 > G.SAFE_BOTTOM - 120:
        raise ValueError(f'verdict card ({y0}-{y1}) runs into the story lines; shorten the quotes')
    im = NG.canvas()
    d, left, right = _plate(im, y0, y1, theme)
    cx, xr, y = (X0 + X1) // 2, X1 - 48, y0 + 40
    d.text((xr, y + osize), outlet, font=A.F('Bold', osize), fill=A.INK, anchor='rs', **G.AR); y += 70
    d.text((xr, y + 44), reviewer, font=A.F('Medium', 44), fill=A.BODY, anchor='rs', **G.AR); y += 56
    d.text((cx, y + ssize), str(score), font=A.F('Bold', ssize), fill=right, anchor='ms', **(G.AR if word else {}))
    y += ssize + 36
    if score_note:
        d.text((cx, y + 44), score_note, font=A.F('Medium', 44), fill=A.BODY, anchor='ms', **G.AR); y += 52
    y += 30
    for tag, colour, lines in ((('ما أعجبه', right, plines), ('ما انتقده', NEG, nlines)) if stage >= 2 else ()):
        tf = A.F('Bold', 42)
        tw = d.textlength(tag, font=tf, **G.AR)
        d.rounded_rectangle([xr - tw - 36, y, xr, y + 56], radius=10, fill=colour + (230,))
        d.text((xr - 18, y + 28), tag, font=tf, fill=A.GROUND, anchor='rm', **G.AR)
        y += 66
        for ln in lines:
            d.text((xr, y + 48), ln, font=qf, fill=A.INK, anchor='rs', **G.AR); y += 58
        y += 24
    im.save(path)
    return path


def totals(path, metacritic, opencritic, read, growing=True, theme='cold', stage=2):
    """The two aggregators side by side, numbers only from their pages (reviewscores.py) and the time they were read.
    `metacritic`: {"score": 96, "reviews": 81}; `opencritic`: {"average": 96, "recommended": 100, "critics": 17};
    `read`: «حتى الساعة 17:05 بتوقيت الإمارات\nيوم 4 نوفمبر» (a hand break keeps a date off the start of a line).
    `growing` adds «والعدد يزداد» (a fresh game's count is still rising). The percentage is written «100 بالمئة»: a % sign
    after a number flips to its far side in right-to-left text (22 Oct 2026). `stage=1` draws Metacritic only on the full
    plate (the first beat), `stage=2` both and the read time."""
    foot = read + ('، والعدد يزداد' if growing else '')
    mc_lines = ['ميتاكريتيك (Metacritic)', f"من {metacritic['reviews']} مراجعة"]
    oc_lines = ['أوبن كريتيك (OpenCritic)', f"متوسط {opencritic['critics']} ناقدًا بارزًا",
                f"يوصي بها {opencritic['recommended']} بالمئة منهم"]
    RL.rtl_starts(mc_lines + oc_lines + [foot], 'totals card')
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 96
    for t in mc_lines + oc_lines:
        _fits(probe, t, 'Medium', (46, 42, 40), room)
    flines = _wrap(probe, foot, A.F('Medium', NG.MIN_TEXT + 2), room, 2, 'totals card')
    blocks = [52 + 130 + 50 * (len(mc_lines) - 1), 52 + 130 + 50 * (len(oc_lines) - 1)]
    h = 40 + sum(blocks) + 20 + 20 + 50 * len(flines) + 40
    y0 = max(TOP, RCY - h // 2)
    y1 = y0 + h
    if y1 > G.SAFE_BOTTOM - 120:
        raise ValueError(f'totals card ({y0}-{y1}) runs into the story lines')
    im = NG.canvas()
    d, left, right = _plate(im, y0, y1, theme)
    cx, y = (X0 + X1) // 2, y0 + 40
    both = ((mc_lines[0], str(metacritic['score']), mc_lines[1:]), (oc_lines[0], str(opencritic['average']), oc_lines[1:]))
    for (name, value, notes), block in zip(both[:1] if stage < 2 else both, blocks):
        d.text((cx, y + 46), name, font=A.F('Bold', _fits(probe, name, 'Bold', (50, 46, 42), room)), fill=A.INK,
               anchor='ms', **G.AR)
        d.text((cx, y + 52 + 118), value, font=A.F('Bold', 120), fill=right, anchor='ms')
        yy = y + 52 + 130
        for n in notes:
            d.text((cx, yy + 42), n, font=A.F('Medium', 42), fill=A.BODY, anchor='ms', **G.AR); yy += 50
        y += block
        if name == mc_lines[0]:
            d.line([X0 + 120, y + 10, X1 - 120, y + 10], fill=right + (70,), width=2)
            y += 20
    y += 20
    for ln in (flines if stage >= 2 else []):
        d.text((cx, y + 42), ln, font=A.F('Medium', NG.MIN_TEXT + 2), fill=A.BODY, anchor='ms', **G.AR); y += 50
    im.save(path)
    return path



# ---------------------------------------------------------------- hardware ranking (8 Nov 2026)
# `product` and `ranking`: a console's official product shot (templates/assets/consoles/, sources in SOURCES.md) on a
# white rounded tile, with the maker's own figure. Built for the Nintendo hardware top five; any maker's lifetime
# hardware figures can use them. Images are shown at 1x or smaller, never enlarged.
import os
CONSOLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'consoles')
BAR_TRACK = (255, 255, 255, 30)


GAMES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'games')


def _tile(name, w, h, radius=24, max_k=1.0):
    """The product shot on a white rounded tile of w x h (white ground, the shot fitted inside with a margin)."""
    folder = CONSOLES if os.path.exists(os.path.join(CONSOLES, name + '.png')) else GAMES
    src = Image.open(os.path.join(folder, name + '.png')).convert('RGBA')
    pad = max(8, round(min(w, h) * 0.06))
    k = min((w - 2 * pad) / src.width, (h - 2 * pad) / src.height)
    if k > max_k:
        raise ValueError(f'console image {name}.png ({src.width}x{src.height}) would be enlarged {k:.2f}x in a {w}x{h} tile; '
                         'use a smaller tile or a larger source (never enlarge)')
    src = src.resize((max(1, round(src.width * k)), max(1, round(src.height * k))), Image.LANCZOS)
    tile = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    tile.alpha_composite(src, ((w - src.width) // 2, (h - src.height) // 2))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    tile.putalpha(mask)
    return tile


def product(path, image, name, value, unit, label, note=None, theme='cold', tile=(440, 220), y0=690):
    """One console, large: a label (the rank, «المركز الأول»), the product tile, the name, the figure, its unit, and an
    optional note. `value` is the figure as the maker printed it ("157.20"); `unit` the words after it («مليون جهاز»)."""
    RL.rtl_starts([label, unit] + ([note] if note else []), 'product card')
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    room = X1 - X0 - 72
    tw, th = tile
    vs = next((s for s in (112, 104, 92, 84) if probe.textlength(value, font=A.F('Bold', s)) <= room), None)
    if vs is None:
        raise ValueError(f'product value is wider than the plate: {value}')
    for t, w, s in ((label, 'Medium', LABEL), (unit, 'Medium', NOTE), (note, 'Medium', NG.MIN_TEXT), (name, 'Bold', 48)):
        if t and probe.textlength(t, font=A.F(w, s), **G.AR) > room:
            raise ValueError(f'product card text is wider than the plate: {t}')
    h = 40 + (LABEL + 34) + (th + 22) + (50 + 12) + (vs + 16) + (NOTE + 14) + ((NG.MIN_TEXT + 18) if note else 0) + 34
    y1 = y0 + h
    if y1 > G.SAFE_BOTTOM - 120:
        raise ValueError(f'product card ({y0}-{y1}) runs into the story lines; use a smaller tile')
    im = NG.canvas()
    d, left, right = _plate(im, y0, y1, theme)
    cx, y = (X0 + X1) // 2, y0 + 40
    d.text((cx, y + LABEL), label, font=A.F('Medium', LABEL), fill=A.BODY, anchor='ms', **G.AR)
    d.rounded_rectangle([cx - 60, y + LABEL + 14, cx + 60, y + LABEL + 20], radius=3, fill=right)
    y += LABEL + 34
    im.alpha_composite(_tile(image, tw, th, max_k=1.6), (cx - tw // 2, y))
    y += th + 22
    d = ImageDraw.Draw(im)
    d.text((cx, y + 46), name, font=A.F('Bold', 48), fill=A.INK, anchor='ms', **G.AR)
    y += 50 + 12
    d.text((cx, y + vs), value, font=A.F('Bold', vs), fill=right, anchor='ms')
    y += vs + 16
    d.text((cx, y + NOTE), unit, font=A.F('Medium', NOTE), fill=A.INK, anchor='ms', **G.AR)
    y += NOTE + 14
    if note:
        d.text((cx, y + NG.MIN_TEXT + 8), note, font=A.F('Medium', NG.MIN_TEXT), fill=A.BODY, anchor='ms', **G.AR)
    im.save(path)
    return path


def ranking(path, rows, title=None, theme='cold', show=None):
    """The countdown table: `rows` in rank order, first (the leader) first, 3 to 6 of them, each
    {"rank": "5", "name": "Game Boy Advance", "value": "81.51", "unit": "مليون جهاز", "image": "gba", "n": 81.51}.
    Every row: the rank badge, the product tile, the name, the figure with its unit, and a bar whose length follows `n`
    against the largest. `show` reveals that many rows from the bottom up (the countdown: show=1 is rank 5 alone); rows
    not yet revealed stay as faint empty slots, so the plate never jumps."""
    if not 3 <= len(rows) <= 6:
        raise ValueError(f'the ranking holds 3 to 6 rows, not {len(rows)}')
    RL.rtl_starts([r['unit'] for r in rows] + ([title] if title else []), 'ranking card')
    probe = ImageDraw.Draw(Image.new('L', (NG.W, NG.H)))
    n_rows = len(rows)
    shown = n_rows if show is None else show
    row_h, tile, title_h = 140, 104, (80 if title else 0)
    h = title_h + row_h * n_rows + 48
    y0 = TOP                                         # story lines run from about y 1320: the plate ends well above them
    y1 = y0 + h
    if y1 > 1300:
        raise ValueError(f'ranking card ({y0}-{y1}) runs into the story lines; fewer rows')
    big = max(float(r['n']) for r in rows)
    im = NG.canvas()
    d, left, right = _plate(im, y0, y1, theme)
    y = y0 + 24
    if title:
        d.text((X1 - 44, y + 52), title, font=A.F('Medium', 46), fill=A.BODY, anchor='rs', **G.AR)
        y += title_h
    bx_r = X1 - 44                                   # the badge's right edge
    for i, r in enumerate(rows):
        revealed = i >= n_rows - shown
        cy = y + row_h // 2
        d = ImageDraw.Draw(im)
        if i:
            d.line([X0 + 40, y, X1 - 40, y], fill=right + (60,), width=2)
        d.ellipse([bx_r - 64, cy - 32, bx_r, cy + 32], fill=(right + (230,)) if revealed else (255, 255, 255, 26))
        d.text((bx_r - 32, cy + 4), str(r['rank']), font=A.F('Bold', 40), fill=A.GROUND if revealed else A.BODY,
               anchor='mm')
        tx1 = bx_r - 64 - 16                          # tile right edge
        if not revealed:
            d.rounded_rectangle([tx1 - tile, cy - tile // 2, tx1, cy + tile // 2], radius=20, outline=(255, 255, 255, 40), width=2)
            d.rounded_rectangle([X0 + 48, cy - 7, tx1 - tile - 20, cy + 7], radius=7, fill=BAR_TRACK)
            y += row_h
            continue
        im.alpha_composite(_tile(r['image'], tile, tile, radius=20), (tx1 - tile, cy - tile // 2))
        d = ImageDraw.Draw(im)
        tr = tx1 - tile - 20                          # text right edge
        room = tr - (X0 + 48)
        name_f = A.F('Bold', 44)
        vtxt = r['value'] + ' ' + r['unit']
        val_f = A.F('Medium', NG.MIN_TEXT)
        if probe.textlength(vtxt, font=val_f, **G.AR) > room:
            raise ValueError(f"ranking row does not fit: {r['name']} / {vtxt}")
        if probe.textlength(r['name'], font=name_f, **G.AR) <= room:
            name_lines, ys = [r['name']], [cy - 22]
            vy, by = cy + 22, cy + 38
        else:                                          # a long title breaks after its colon, two lines of 40 px
            name_f = A.F('Bold', NG.MIN_TEXT)
            words = r['name'].split(' ')               # two balanced lines, a colon keeps its word
            best = None
            for k in range(1, len(words)):
                a, b = ' '.join(words[:k]), ' '.join(words[k:])
                w = max(probe.textlength(a, font=name_f, **G.AR), probe.textlength(b, font=name_f, **G.AR))
                if best is None or w < best[0]:
                    best = (w, [a, b])
            name_lines = [t.rstrip(':') for t in best[1]] if best else [r['name']]   # a colon at a line end flips to the far side in RTL
            if any(probe.textlength(t, font=name_f, **G.AR) > room for t in name_lines):
                raise ValueError(f"ranking row does not fit: {r['name']}")
            ys, vy, by = [cy - 46, cy - 6], cy + 36, cy + 50
        for t, ty in zip(name_lines, ys):
            d.text((tr, ty), t, font=name_f, fill=A.INK, anchor='rs', **G.AR)
        d.text((tr, vy), vtxt, font=val_f, fill=A.BODY, anchor='rs', **G.AR)
        blen = max(24, round(room * float(r['n']) / big))
        d.rounded_rectangle([tr - room, by, tr, by + 9], radius=5, fill=BAR_TRACK)
        d.rounded_rectangle([tr - blen, by, tr, by + 9], radius=5, fill=right + (255,))
        y += row_h
    im.save(path)
    return path


KINDS = {'fact': fact, 'scores': scores, 'verdict': verdict, 'totals': totals,
         'product': product, 'ranking': ranking}


def build(item, path, theme):
    """One card from a job file's "gfx" entry."""
    kw = {k: v for k, v in item.items() if k not in ('file', 'kind')}
    return KINDS[item.get('kind', 'fact')](path, theme=kw.pop('theme', theme), **kw)
