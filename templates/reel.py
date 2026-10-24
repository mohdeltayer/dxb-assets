"""Digital Lounge Reel in the full-screen format (agreed 30 Sep to 1 Oct 2026,
first used on the Ocarina of Time post).

The footage fills the 9:16 frame and keeps its own sound. The chip, a large
headline and a credit line (accent rule, source · date) sit at the top for
the opening seconds, then the story runs low in the frame as short
sentences one after another, white Dubai Bold with an indigo outline and a
soft shadow, no plate and no footer; the end card (outro.py) follows. Text
stays inside the Reels safe zone (ig_ar.SAFE_*), and a line that would run
past it stops the render. Shots run in their source order: cutting back
and forth through a trailer makes its music jump.

Stills get the same treatment: each image fills the frame and pans slowly
across, so nothing is left empty, and with no sound of its own the clip
gets the flavour's bed under it.

    reel(shots, headline, label, lines, source, date, out)

shots: ('clip.mp4', start, seconds, focus) for footage, focus 0 left to 1
       right; ('art.jpg', None, seconds, (from, to)) for a still, the pan
       running from one focus to the other. Files live in uploads.
lines: [(text, t0, t1, opts)] with times on the finished clip, or plain
       strings to spread over the clip by length. '|' sets a line break by
       hand (a newline). opts: top=True (above a lower-third game UI), price='289'
       (digits with the dirham symbol to their left), shade=True (a light
       indigo shade low in the frame, for pale footage).
strip: [(label, value), ...] (2 or 3) pins the `split` template's fact strip low in the
       safe zone from the end of the headline to the end of the clip (14 Oct 2026); the
       lines rise above it and never repeat a value. A value is a string, or
       ('aed', '149') for digits with the dirham symbol left of them.
"""
import json, math, os, re, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter
import cards as C, fast_ar as A, ig_ar as G, outro, sonic
import skins as SK
import decodecheck as DC

W, H = 1080, 1920
L, R = G.SAFE_LEFT, G.SAFE_RIGHT
X = 0.4                                   # crossfade between shots
TRANSITION = 'fade'                       # the xfade between shots; a game skin swaps it for its own (advisor, 20 Oct 2026)
SYM = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'dirham-symbol-mask.png')).convert('L')
STILL = ('.jpg', '.jpeg', '.png', '.webp')


def _arabic(ch):
    o = ord(ch)
    return 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF


def rtl_starts(lines, what):
    """Every visual line opens on an Arabic word (Mohammad, 27 Sep 2026; checked
    on the wrapped lines since 13 Oct, after a headline wrapped «(Finji)», «30
    دقيقة» and «PS5» to the start of a line). Quotation marks before the word
    are fine; a Latin word, a digit or a bracket is not."""
    for ln in lines:
        t = ln.strip().lstrip('«"“\u200f')
        if t and not _arabic(t[0]):
            raise ValueError(f'{what} line opens on {t[:12]!r}, not an Arabic word; rebreak or reword: {ln}')
        m = GLUED.search(ln)
        if m:                              # 24 Oct 2026: ARMS v3 drew «لـSwitch 2» as «Switch 2لـ»
            raise ValueError(f'{what} line glues an Arabic prefix to a Latin word ({m.group(0)!r}), which flips on '
                             f'screen; reword with a space («لجهاز Switch 2», «و Zelda» or «وسلسلة Zelda»): {ln}')


#: An Arabic letter or tatweel written straight onto a Latin letter or digit («لـSwitch», «وZelda»):
#: the image library's bidi puts the prefix after the name on screen. Post text is not affected.
GLUED = re.compile('[\u0621-\u064A\u0640][A-Za-z]')   # digits after و or ل render in order


def _band(im, y0, y1, up, alpha):
    g = Image.new('L', (1, H), 0)
    for y in range(max(0, y0), min(H, y1)):
        t = (y - y0) / (y1 - y0)
        g.putpixel((0, y), int(alpha * ((1 - t) if up else t) ** 0.8))
    s = Image.new('RGBA', (W, H), A.GROUND + (255,)); s.putalpha(g.resize((W, H))); im.alpha_composite(s)


def _waves(im, y1, theme, seed, alpha=0.7, width=2, tighten=0, lift=1.0):
    """The banner's wave lines in the theme's colours, full strength at the
    top and fading out by y1: the colourful part of the vivid look."""
    left, right, freq, amp, gap = A.THEMES[theme]
    gap, amp = gap - tighten, amp * lift
    k = 2; lay = Image.new('RGBA', (W * k, y1 * k), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ph = (seed % 628) / 100
    for j in range(-4, y1 // gap + 5):
        pts = [(x, (j * gap + amp * math.sin(x / (W * k) * freq + j * 0.22 + ph)
                    + amp * 0.5 * math.sin(x / (W * k) * freq * 2.3 + ph * 1.7)) * k)
               for x in range(0, W * k + 24, 12)]
        for a, b in zip(pts, pts[1:]):
            u = a[0] / (W * k); fade = max(0.0, 1 - a[1] / (y1 * k)) ** 1.3
            c = tuple(int(left[i] + (right[i] - left[i]) * u) for i in range(3))
            d.line((a, b), fill=c + (int(255 * alpha * fade),), width=width * k)
    im.alpha_composite(lay.resize((W, y1), Image.LANCZOS))


def _glow(im, y1, theme, alpha=0.8):
    """A soft wash of the theme's two colours, left to right, fading down."""
    left, right = A.THEMES[theme][:2]
    row = Image.new('RGB', (2, 1)); row.putpixel((0, 0), left); row.putpixel((1, 0), right)
    wash = row.resize((W, y1), Image.BILINEAR).convert('RGBA')
    fade = Image.new('L', (1, y1))
    for y in range(y1):
        fade.putpixel((0, y), int(255 * alpha * max(0.0, 1 - y / y1) ** 1.6))
    wash.putalpha(fade.resize((W, y1))); im.alpha_composite(wash)


#: Four ways to colour the top band, all approved on 2 Oct 2026. `style=None`
#: in reel() rotates them through STYLE_LEDGER so a run of posts varies.
STYLES = ('lines', 'bold', 'glow', 'frame')
STYLE_LEDGER = os.path.join(os.path.dirname(__file__), 'assets', 'style-ledger.json')


def pick_style(out):
    """The style for this file: kept on a re-render, else the one rested longest."""
    import json
    try:
        book = json.load(open(STYLE_LEDGER))
    except (OSError, ValueError):
        book = {}
    key = os.path.basename(out)
    if key not in book:
        used = list(book.values())
        last = {s: max([i for i, v in enumerate(used) if v == s], default=-1) for s in STYLES}
        book[key] = min(STYLES, key=lambda s: last[s])
        json.dump(book, open(STYLE_LEDGER, 'w'), indent=1)
    return book[key]


def _colour(im, y1, theme, seed, style):
    if style == 'bold':
        _waves(im, y1, theme, seed, alpha=0.95, width=3, tighten=4, lift=1.3)
    elif style == 'glow':
        _glow(im, y1, theme)
    else:                                   # 'lines' and the top half of 'frame'
        _waves(im, y1, theme, seed)


def frame_layer(path, theme, seed, h=420):
    """For style 'frame': fainter waves rising from the bottom, behind the story lines."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    band = Image.new('RGBA', (W, h), (0, 0, 0, 0)); _waves(band, h, theme, seed + 3, alpha=0.55)
    im.alpha_composite(band.transpose(Image.FLIP_TOP_BOTTOM), (0, H - h)); im.save(path); return path


#: The grid tile (advisor, 19 Oct 2026): Instagram's Reels icon covers the top right of every grid
#: tile, where the chip sat. The chip row drops CHIP_DROP px, the headline with it, and no chip or
#: text may fall in the GRID_CORNER px square at the top right of the first frame's 3:4 window
#: (1080x1440, centred: y 240 to 1680). head_layer stops when it would.
CHIP_DROP, GRID_CORNER = 60, 140
HEAD_TOP = G.SAFE_TOP + 10 + CHIP_DROP
GRID_TOP = (H - W * 4 // 3) // 2
#: Grid tile headlines (advisor, 24 Oct 2026, agreed with Mohammad): at grid size the old 66 px
#: headline read like a caption and faded on bright footage. The first-frame headline is now about
#: 1.5 times larger (HEAD_SIZE), at most HEAD_LINES short lines, never below HEAD_MIN (only a full game name
#: that cannot be cut shrinks it that far; anything else is cut to fewer words), on a stronger band (HEAD_BAND) with a wider
#: glow behind the type, so it holds on pale skies and white scenes.
HEAD_SIZE, HEAD_MIN, HEAD_LINES, HEAD_BAND = 100, 72, 2, 225


def grid_corner_clear(im, what='head'):
    """Stop when anything drawn on `im` (RGBA, W x H) reaches the grid tile's top-right corner."""
    box = (W - GRID_CORNER, GRID_TOP, W, GRID_TOP + GRID_CORNER)
    if im.getchannel('A').crop(box).point(lambda v: 255 if v > 40 else 0).getbbox():
        raise ValueError(f'{what} reaches the grid tile corner (Reels icon, x {box[0]} to {W}, y {box[1]} to {box[3]})')


def head_layer(headline, label, path, source, date, country=None, hs=HEAD_SIZE, hst=None,
               vivid=False, theme='cold', seed=0, style='lines', meta_path=None, skin=None):
    """Chip and headline on a soft band at the top; the credit line (rule, source · date)
    is written to `meta_path` as its own layer when given, else drawn with the head. `vivid`
    colours the chip with the theme and lays the theme's wave lines in the band. `skin` (a game
    skins pilot kit, skins.KITS) lays the kit's band decoration and a plate behind chip and
    headline instead, and colours the chip and the credit rule with the kit; the chip's place
    and the grid-corner rule do not change."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    probe = ImageDraw.Draw(Image.new('RGBA', (W, H)))
    room = W - R - L
    if hs < HEAD_MIN:
        raise ValueError(f'head_size {hs} is under HEAD_MIN {HEAD_MIN} (grid tile memo, 24 Oct 2026); cut the headline instead')
    hst = hst or hs + 20
    while True:                            # a long Latin name shrinks the headline a little, never below HEAD_MIN
        f = A.F('Bold', hs)
        lines = G._wrap(probe, headline, f, room)
        if (len(lines) <= HEAD_LINES and all(probe.textlength(x, font=f, **G.AR) <= room for x in lines)
                and all(_arabic(x.lstrip('«"“\u200f')[0]) for x in lines if x)):   # a Latin-led wrap shrinks too
            break
        if hs - 4 < HEAD_MIN:
            raise ValueError(f'headline needs more than {HEAD_LINES} lines at {HEAD_MIN} px; cut it to a few words: {headline}')
        hs, hst = hs - 4, hst - 5
    hl = L
    if len(lines) == 2 and '\n' not in headline:   # balance two lines so no word hangs alone (a hand-set break is kept)
        words = G._tokens(headline); tw = lambda x: probe.textlength(x, font=f, **G.AR)
        ks = [k for k in range(1, len(words)) if _arabic(words[k][0])]   # never split before a Latin name (24 Oct 2026)
        if ks:
            bw = min(max(tw(' '.join(words[:k])), tw(' '.join(words[k:]))) for k in ks)
            hl = max(L, int(W - R - bw - 16))
            if any(x and not _arabic(x.lstrip('«"“\u200f')[0]) for x in G._wrap(probe, headline, f, W - hl - R)):
                hl = L                     # the balanced width would open a line on Latin: keep the full width
    rtl_starts(G._wrap(probe, headline, f, W - hl - R), 'headline')
    chip = SK.chip(skin) if skin else G._ACC if vivid else None
    acc = SK.load(skin)['accent'] if skin else G._ACC
    end = G._head(probe, headline, HEAD_TOP, label, country, hs, hst, right=R, left=hl)
    meta_y = end + 30
    _band(im, 0, meta_y + 220, True, HEAD_BAND)
    if skin:                               # the kit's decoration and its plate behind chip and headline
        SK.top(im, meta_y + 140, skin, seed)
        SK.plate(im, (max(L - 20, hl - 28), HEAD_TOP - 18, W - R + 20, end + 14), skin)
    elif vivid:
        _colour(im, meta_y + 140, theme, seed, style)
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    G._head(d, headline, HEAD_TOP, label, country, hs, hst, right=R, left=hl, chip=chip)
    grid_corner_clear(t)
    if not meta_path:                      # one layer, as before 14 Oct
        d.rectangle([W - R - 44, meta_y - 2, W - R, meta_y + 2], fill=acc)
        d.text((W - R - 62, meta_y), f'{source}\u200f  ·  \u200f{A.arabic_date(date)}', font=A.F('Medium', 32),
               fill=A.BODY, anchor='rm', **G.AR)
    _glowed(im, t, blur=16, gain=2.6); im.save(path)
    if meta_path:                          # the credit line on its own layer: it enters at CREDIT_AT (advisor, 14 Oct 2026)
        m = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
        d.rectangle([W - R - 44, meta_y - 2, W - R, meta_y + 2], fill=acc)
        d.text((W - R - 62, meta_y), f'{source}\u200f  ·  \u200f{A.arabic_date(date)}', font=A.F('Medium', 32),
               fill=A.BODY, anchor='rm', **G.AR)
        _glowed(Image.new('RGBA', (W, H), (0, 0, 0, 0)), m).save(meta_path)
    return path


def _glowed(im, t, blur=10, gain=2):
    """Lay the drawn text `t` on `im` with a soft ground-coloured glow behind it."""
    glow = Image.new('RGBA', (W, H), A.GROUND + (0,))
    glow.putalpha(t.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, int(v * gain))))
    im.alpha_composite(glow); im.alpha_composite(t); return im


#: The hook (advisor, 14 Oct 2026): the footage moves from frame one under the chip and
#: headline; the credit line (rule, source · date) enters at CREDIT_AT; the headline is a hook
#: (a number, a question or the surprise), never a label.
CREDIT_AT = 2.0
#: The persistent mark (advisor, 14 Oct 2026): the play mark at MARK_PX, MARK_ALPHA opacity,
#: top left inside the safe zone, on screen for the whole Reel. `MARK_PERSIST = False` turns it off.
MARK_PERSIST, MARK_PX, MARK_ALPHA = True, 48, 0.5
#: Length target (advisor, 14 Oct 2026): 12 to 20 s of story before the end card; four lines is the
#: normal case, six only when the story needs them. reel() warns outside it; the brief states the total.
LENGTH = (12.0, 20.0)


def mark_layer(path):
    """The play mark, round, MARK_PX wide at MARK_ALPHA, on the chip row's empty left end
    (the chip sits at the right): x SAFE_LEFT, centred on the chip row."""
    mark = Image.open(A.MARK).convert('RGB').resize((MARK_PX * 4, MARK_PX * 4), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((MARK_PX, MARK_PX), Image.LANCZOS), mask.resize((MARK_PX, MARK_PX), Image.LANCZOS)
    mask = mask.point(lambda v: int(v * MARK_ALPHA))
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = HEAD_TOP + 57 - int(57 * 1.5 / 2) - MARK_PX // 2     # the chip row's middle (chip bottom at +57, 57 high)
    im.paste(mark, (G.SAFE_LEFT, y), mask); im.save(path); return path


def length_note(end, exempt=False):
    """One line for the brief and the render log: the total before the end card, and
    a warning when it sits outside LENGTH (`exempt`: handson and edition, formats.LENGTH_EXEMPT)."""
    lo, hi = LENGTH
    note = f'length {end:.1f} s before the end card (target {lo:.0f} to {hi:.0f} s)'
    if exempt:
        return note + ' (exempt template)'
    if not lo <= end <= hi:
        note += ': outside the target; four lines is the normal case, six only when the story needs them'
    return note


#: Attention (advisor, 14 Oct 2026): something changes on screen every PACE seconds (a cut, a line, a strip, a number);
#: the last CLOSE seconds before the end card are a picture, never a card. Both are warnings at the check step.
PACE, CLOSE = 4.0, 2.0


def pace_note(starts, end, lines, strip_at=None):
    """Warn on any stretch longer than PACE with no change on screen."""
    ev = sorted(set([0.0, end] + list(starts) + [a for _, a, _, _ in lines] + ([strip_at] if strip_at else [])))
    gaps = [(a, b) for a, b in zip(ev, ev[1:]) if b - a > PACE + 0.05]
    return '' if not gaps else 'pace: nothing changes for ' + ', '.join(f'{b - a:.1f} s at {a:.1f}' for a, b in gaps) + f' (change every {PACE:.0f} s)'


def close_note(shots):
    """Warn when the Reel ends on our own graphic instead of a picture."""
    f = shots[-1][0]
    return f'close: the last {CLOSE:.0f} s are a card ({f}); end on a picture' if _ours(f) else ''


def _reveal(lines, idx):
    """Word-by-word reveal of one line (the key line only, advisor 14 Oct 2026): the line
    becomes cumulative prefixes, each a layer, entering a quarter second apart."""
    text, a, z, kw = lines[idx]
    toks = re.findall(r'\S+|\n', text)
    words = [t for t in toks if t != '\n']
    dt = min(0.25, (z - a) * 0.4 / max(len(words), 1))
    out, k = [], 0
    for n in range(1, len(words) + 1):
        pre, c = [], 0
        for t in toks:
            if t == '\n':
                if pre: pre.append('\n')
            else:
                if c == n: break
                pre.append(t); c += 1
        txt = ' '.join(pre).replace(' \n ', '\n').strip()
        out.append((txt, a + (n - 1) * dt, z, kw))
    return lines[:idx] + out + lines[idx + 1:]


STILLS = 'stills'   # push-in clips are written under uploads/stills/
#: Stills move at SUB times the frame and are scaled down last (advisor, 18 Oct 2026; Mohammad:
#: "some of the stills feel shaky"): zoompan and crop place the picture in whole pixels, so a 3%
#: push or a slow pan at 1080x1920 stepped a pixel at a time and juddered. At 4x the steps are a
#: quarter pixel at the output. The finish (cas, grade, grain) runs after the downscale, so the
#: grain is not magnified. STILLS_VER is in the clip names, so clips from before the fix are
#: re-rendered, never reused.
SUB = 4
STILLS_VER = 's4'


def _still_finish(f):
    """The picture finish for an official still, applied at the output size."""
    return f',cas=0.5,{GRADE}' if FINISH and not _ours(f) else ''


def stills_clips(images, name, secs=3.0, push=0.03, focus=0.5, cutout=False, theme='cold', fast=False):
    """The `stills` template (advisor, 14 Oct 2026): each official image as a clip of
    `secs` with a slow push-in of `push` (2 to 4%), or with `cutout=True` the subject cut
    out of its backdrop (edition.cutout) and laid still on the drifting living ground, so
    the ground moves behind it (parallax). Pass the result as `shots` with `cut=True` so the
    cuts are hard, and the lines enter on the cuts. Returns [(file, 0.0, secs, 0.5), ...]."""
    out = []
    frames = int(secs * 30)
    if cutout:
        import edition, numgfx as NG
    for i, img in enumerate(images):
        src = img if os.path.isabs(img) else C.U + img
        fo = focus[i] if isinstance(focus, (list, tuple)) else focus
        if cutout:
            os.makedirs(C.U + NG.SUB, exist_ok=True)
            png = f'{C.U}{NG.SUB}/{name}-cut-{i}.png'
            edition.cutout(src, png)
            it = Image.open(png).convert('RGBA'); sc = min(820 / it.width, 1100 / it.height)
            it = it.resize((max(1, int(it.width * sc)), max(1, int(it.height * sc))), Image.LANCZOS)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.alpha_composite(it, ((W - it.width) // 2, (H - it.height) // 2 - 60))
            lay.save(png)
            clip = f'{NG.SUB}/{name}-still-{i}.mp4'
            NG.slide(png, secs, theme, C.U + clip, seed=sum(map(ord, name)) + i, t0=i * secs, fast=fast, check=False)
        else:
            os.makedirs(C.U + STILLS, exist_ok=True)
            clip = f'{STILLS}/{name}-still-{i}-{STILLS_VER}.mp4'
            sw, sh = W * SUB, H * SUB
            vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh}:x='(iw-{sw})*{fo}':y='(ih-{sh})/2',"
                  f"zoompan=z='1+{push}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={sw}x{sh}:fps=30,"
                  f"scale={W}:{H}:flags=lanczos{_still_finish(img)},format=yuv420p")
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-loop', '1', '-t', str(secs), '-i', src, '-vf', vf, '-t', str(secs),
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + (DRAFT_ENC if fast else ['-preset', 'medium', '-crf', '16']) + [C.U + clip], check=True)
        out.append((clip, 0.0, secs, 0.5))
    return out


def line_layer(text, path, price=None, shade=False, top=False, size=70, step=96, lift=0, ink=None, skin=None):
    """One sentence, right-aligned; bottom line on SAFE_BOTTOM - 40, or
    under SAFE_TOP with top=True. `lift` raises a low line (the split template
    lifts them over its fact strip). `skin` takes the kit's outline and ink."""
    f = A.F('Bold', size); probe = ImageDraw.Draw(Image.new('L', (W, H)))
    tw = lambda s: probe.textlength(s, font=f, **G.AR)
    full = text + (f' {price}' if price else '')
    room = W - R - L
    if '\n' in full:
        lines = [x.strip() for x in full.split('\n')]
    else:
        lines = G._wrap(probe, full, f, room - (size if price else 0))
        if len(lines) == 2:               # balance two lines, no word left alone
            words = full.split()
            k = min(range(1, len(words)), key=lambda k: max(tw(' '.join(words[:k])), tw(' '.join(words[k:]))))
            lines = [' '.join(words[:k]), ' '.join(words[k:])]
    for i, x in enumerate(lines):
        if tw(x) > room - (size if price and i == len(lines) - 1 else 0):
            raise ValueError(f'line runs out of the safe zone: {x}')
    cap = 2 if lift else 3                 # over a split strip a sentence is two visual lines at most (14 Oct 2026)
    if len(lines) > cap:
        raise ValueError(f'{len(lines)} lines; keep a sentence to {cap}' + (' over the strip' if lift else '') + f': {text}')
    rtl_starts(lines, 'story')
    base0 = G.SAFE_TOP + 110 if top else G.SAFE_BOTTOM - 40 - lift - step * (len(lines) - 1)
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    for i, ln in enumerate(lines):
        b = base0 + i * step
        d.text((W - R, b), ln, font=f, fill=255, anchor='rs', **G.AR)
        if price and i == len(lines) - 1:
            _, y0, _, y1 = d.textbbox((0, b), price, font=f, anchor='ls')
            dh = y1 - y0
            s = SYM.resize((round(SYM.width * dh / SYM.height), dh), Image.LANCZOS)
            sx = d.textbbox((W - R, b), ln, font=f, anchor='rs', **G.AR)[0] - round(dh * 0.3) - s.width
            if sx < L:
                raise ValueError(f'price runs out of the safe zone ({sx})')
            mask.paste(255, (sx, b - dh), s)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shade:
        _band(im, 1150, H, False, 110)
    outline = mask.filter(ImageFilter.MaxFilter(7))
    shadow = outline.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.7))
    oc, kink = SK.line_colours(skin) if skin else (A.GROUND, A.INK)
    for col, m, off in [((0, 0, 0), shadow, (3, 4)), (oc, outline, (0, 0)), (ink or kink, mask, (0, 0))]:
        lay = Image.new('RGBA', (W, H), col + (255,)); a = Image.new('L', (W, H), 0)
        a.paste(m, off); lay.putalpha(a); im.alpha_composite(lay)
    im.save(path); return path


def credit_layer(text, path, low=False, size=36, y=None, band=False):
    """A small credit naming footage that is not of the story's subject itself,
    «لقطات من Fortnite» over a delayed game that has never been shown (Mohammad,
    13 Oct 2026, review priority 3). Right-aligned under the safe top, or just
    above the safe bottom when the story lines sit at the top."""
    rtl_starts([text], 'credit')
    f = A.F('Medium', size)
    y = y if y is not None else G.SAFE_BOTTOM - 10 if low else G.SAFE_TOP + 40
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).text((W - R, y), text, font=f, fill=255, anchor='rs', **G.AR)
    if ImageDraw.Draw(mask).textlength(text, font=f, **G.AR) > W - R - L:
        raise ValueError(f'credit runs out of the safe zone: {text}')
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if band:                                   # a soft dark band behind it, for pale or busy ground (23 Oct 2026,
        box = mask.getbbox()                   # the Miyamoto Reel: a credit over a light grey portrait and a logo rim)
        if box:
            b = Image.new('L', (W, H), 0)
            ImageDraw.Draw(b).rectangle((box[0] - 24, box[1] - 14, box[2] + 24, box[3] + 14), fill=140)
            lay = Image.new('RGBA', (W, H), A.GROUND + (255,)); lay.putalpha(b.filter(ImageFilter.GaussianBlur(10)))
            im.alpha_composite(lay)
    outline = mask.filter(ImageFilter.MaxFilter(5))
    for col, m in [(A.GROUND, outline), (A.BODY, mask)]:
        lay = Image.new('RGBA', (W, H), col + (255,)); lay.putalpha(m); im.alpha_composite(lay)
    im.save(path); return path


#: People stories show the person (advisor, 23 Oct 2026, from Mohammad, after the Miyamoto honour Reel never
#: showed Miyamoto): the person's official photo in a framed window over the running footage, a name plate
#: with their role under the name, in the first 3 to 4 seconds, then back to full footage. The window sits
#: right of centre between the headline band and the story lines, clear of the grid tile's top-right corner.
PERSON_BOX = (450, 750, 460, 490)     # x, y, w, h: right edge on the safe right (910), under the credit line of a two-line HEAD_SIZE headline (24 Oct 2026; was y 700, h 540), bottom at 1240 above a two-line story line
PERSON_MAX_ZOOM = 2.0                 # a photo enlarged past 2x into the window reads soft on a phone; find a larger one


def person_layer(photo, name, role, path, theme='cold', box=PERSON_BOX, focus=(0.5, 0.33), credit=None):
    """`photo` (a file in uploads, ideally the company's press photo) cover-cropped into `box`
    around `focus` (x, y as 0 to 1 of the photo, the face; the default suits a head-and-shoulders
    portrait), with a rounded frame edged in the theme accent, a soft shadow, and a plate inside
    the window's lower part: `name` (Bold) over `role` (Medium, body colour), right-aligned, and
    an optional small `credit` line for a licensed image («الصورة: ويكيميديا كومنز، CC BY-SA 4.0»).
    Every text line opens on an Arabic word. Stops when the photo would be enlarged past
    PERSON_MAX_ZOOM or a text line will not fit the plate."""
    x, y, bw, bh = box
    src = Image.open(photo if os.path.isabs(photo) else C.U + photo).convert('RGB')
    sw, sh = src.size
    scale = max(bw / sw, bh / sh)
    if scale > PERSON_MAX_ZOOM:
        raise ValueError(f'person photo {photo} is {sw}x{sh}: enlarged {scale:.1f}x into the window; find a larger one')
    cw, ch = bw / scale, bh / scale
    fx, fy = focus
    cx = min(max(fx * sw - cw / 2, 0), sw - cw); cy = min(max(fy * sh - ch / 2, 0), sh - ch)
    pic = src.crop((round(cx), round(cy), round(cx + cw), round(cy + ch))).resize((bw, bh), Image.LANCZOS)
    pad, rad = 26, 22
    texts = [(name, 'Bold', (46, 42, 38, 34), A.INK), (role, 'Medium', (32, 30, 28, 26), A.BODY)]
    if credit:
        texts.append((credit, 'Medium', (22, 20), A.BODY))
    probe = ImageDraw.Draw(Image.new('L', (W, H)))
    rows = []
    for text, weight, sizes, col in texts:
        rtl_starts([text], 'person plate')
        for s in sizes:
            f = A.F(weight, s)
            if probe.textlength(text, font=f, **G.AR) <= bw - 2 * pad:
                break
        else:
            raise ValueError(f'person plate line will not fit the window: {text}')
        rows.append((text, f, s, col))
    gaps = [int(s * 1.25) for _, _, s, _ in rows]
    plate_h = sum(gaps) + pad + 10
    # the plate: the window's own lower part darkened to the ground colour so the type holds on any photo
    shade = Image.new('L', (1, bh), 0)
    top = bh - plate_h - 70
    for j in range(max(0, top), bh):
        shade.putpixel((0, j), int(235 * min(1, (j - top) / 70) ** 1.2))
    shade = shade.resize((bw, bh))
    win = pic.convert('RGBA')
    win.alpha_composite(Image.merge('RGBA', [Image.new('L', (bw, bh), c) for c in A.GROUND] + [shade]))
    d = ImageDraw.Draw(win)
    yb = bh - pad
    for (text, f, s, col), g in zip(reversed(rows), reversed(gaps)):
        d.text((bw - pad, yb), text, font=f, fill=col + (255,), anchor='rs', **G.AR)
        yb -= g
    mask = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), rad, fill=255)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh_m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh_m).rounded_rectangle((x + 6, y + 12, x + bw + 6, y + bh + 12), rad, fill=150)
    sh_l = Image.new('RGBA', (W, H), (0, 0, 0, 255)); sh_l.putalpha(sh_m.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(sh_l)
    im.paste(win, (x, y), mask)
    acc = G.ACCENTS.get(theme, A.AZURE)
    ImageDraw.Draw(im).rounded_rectangle((x, y, x + bw - 1, y + bh - 1), rad, outline=acc + (255,), width=4)
    im.save(path); return path


#: The `split` template's fact strip (Mohammad, 14 Oct 2026): footage runs the whole
#: Reel and two or three facts (date, price, platforms) stay pinned low in the safe
#: zone while the lines narrate above it. A fact lives here or in a line, never both.
STRIP_H = 160
STRIP_BOTTOM = G.SAFE_BOTTOM - 24
STRIP_TOP = STRIP_BOTTOM - STRIP_H
STRIP_LIFT = STRIP_H + 32             # how far the story lines rise to clear it
STRIP_VALUE_SIZES = (56, 48, 44)      # one size for the whole strip: the largest at which every value fits
STRIP_LABEL_SIZES = (34, 30)


def _strip_text(v):
    """A strip value as the text a line would have to repeat to duplicate it."""
    return v[1] if isinstance(v, tuple) else v


def strip_check(items, lines=()):
    """Stop on a malformed strip, or on a story line that already says a strip
    value (one fact, one place). `lines` are the (text, t0, t1, opts) of reel()."""
    if not 2 <= len(items) <= 3:
        raise ValueError(f'a strip takes 2 or 3 items, got {len(items)}')
    for label, v in items:
        if isinstance(v, tuple) and (len(v) != 2 or v[0] != 'aed' or not str(v[1]).strip()):
            raise ValueError(f"strip value {v!r}: use a string, or ('aed', '149') for the dirham symbol")
    rtl_starts([label for label, _ in items], 'strip label')
    for text, _, _, kw in lines:
        hay = (text + (f" {kw['price']}" if kw.get('price') else '')).replace('|', ' ').replace('\n', ' ').casefold()
        for label, v in items:
            val = _strip_text(v).strip()
            if val and val.casefold() in hay:
                raise ValueError(f'the strip already shows {val!r} ({label}); a line must not say it again: {text}')


def strip_layer(items, path, theme='cold', skin=None):
    """The fact strip alone, 1080x1920 transparent: a rounded soft band (the
    ground tinted with the theme, about 70% opaque) at x SAFE_LEFT to W - SAFE_RIGHT,
    bottom at SAFE_BOTTOM - 24, items as equal columns right to left with thin
    rules in the theme's second colour. Each item: label in Dubai Medium (34) over
    the value in Dubai Bold (56, or 48 then 44 so every value fits one size). Raises
    when something leaves the safe zone, a label does not open on an Arabic word, or
    a text will not fit its column. `skin` draws the kit's plate and colours instead of the band."""
    strip_check(items)
    left, right = A.THEMES[theme][:2]
    x0, x1, y0, y1 = L, W - R, STRIP_TOP, STRIP_BOTTOM
    if x0 < G.SAFE_LEFT or x1 > W - G.SAFE_RIGHT or y1 > G.SAFE_BOTTOM or y0 < G.SAFE_TOP:
        raise ValueError(f'the strip ({x0}-{x1}, {y0}-{y1}) leaves the safe zone')
    n = len(items); cw = (x1 - x0) / n; room = cw - 28
    probe = ImageDraw.Draw(Image.new('L', (W, H)))

    def vwidth(v, size):               # (width, symbol width) of a value at a size
        f = A.F('Bold', size)
        if isinstance(v, tuple):
            dh = probe.textbbox((0, 0), v[1], font=f, anchor='ls')[3] - probe.textbbox((0, 0), v[1], font=f, anchor='ls')[1]
            sw = round(SYM.width * dh / SYM.height)
            return probe.textlength(v[1], font=f, **G.AR) + round(dh * 0.3) + sw, dh
        return probe.textlength(v, font=f, **G.AR), 0
    ls = next((s for s in STRIP_LABEL_SIZES if all(probe.textlength(l, font=A.F('Medium', s), **G.AR) <= room for l, _ in items)), None)
    if ls is None:
        raise ValueError(f'a strip label is wider than its column ({room:.0f}px at {STRIP_LABEL_SIZES[-1]}): '
                         f'{[l for l, _ in items]}; shorten it or use 2 items')
    vs = next((s for s in STRIP_VALUE_SIZES if all(vwidth(v, s)[0] <= room for _, v in items)), None)
    if vs is None:
        raise ValueError(f'a strip value is wider than its column ({room:.0f}px at {STRIP_VALUE_SIZES[-1]}): '
                         f'{[_strip_text(v) for _, v in items]}; shorten it or use 2 items')

    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    soft = Image.new('L', (W, H), 0)   # a wider, blurred shadow so the band's edge is soft
    ImageDraw.Draw(soft).rounded_rectangle([x0 - 8, y0 - 8, x1 + 8, y1 + 8], radius=34, fill=110)
    sh = Image.new('RGBA', (W, H), A.GROUND + (255,)); sh.putalpha(soft.filter(ImageFilter.GaussianBlur(14))); im.alpha_composite(sh)
    tint = tuple(round(A.GROUND[i] * 0.86 + left[i] * 0.14) for i in range(3))
    d = ImageDraw.Draw(im)
    body, ink = A.BODY, A.INK
    if skin:                           # the kit's plate, rules in its edge colour, its ink
        k = SK.load(skin); SK.plate(im, (x0, y0, x1, y1), skin); d = ImageDraw.Draw(im)
        right, body, ink = k['edge'], k['body'], k['ink']
    else:
        d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=tint + (178,), outline=right + (90,), width=2)
    for i in range(1, n):              # thin rules in the theme's second colour
        rx = round(x1 - i * cw)
        d.line([(rx, y0 + 26), (rx, y1 - 26)], fill=right + (170,), width=2)
    fl, fv = A.F('Medium', ls), A.F('Bold', vs)
    lab_y, val_y = y0 + 56, y1 - 34
    for i, (label, v) in enumerate(items):
        cx = x1 - (i + 0.5) * cw
        d.text((cx, lab_y), label, font=fl, fill=body, anchor='ms', **G.AR)
        w, dh = vwidth(v, vs)
        if isinstance(v, tuple):       # digits with the dirham symbol to their left, as on the price lines
            dw = probe.textlength(v[1], font=fv, **G.AR); sw = round(SYM.width * dh / SYM.height)
            d.text((cx + w / 2, val_y), v[1], font=fv, fill=ink, anchor='rs', **G.AR)
            sym = Image.new('RGBA', (sw, dh), ink + (255,))
            sym.putalpha(SYM.resize((sw, dh), Image.LANCZOS))
            im.alpha_composite(sym, (round(cx - w / 2), val_y - dh))
        else:
            d.text((cx, val_y), v, font=fv, fill=ink, anchor='ms', **G.AR)
        for t, f, yy in ((label, fl, lab_y), (_strip_text(v), fv, val_y)):    # nothing may leave the column or the band
            bb = probe.textbbox((cx, yy), t, font=f, anchor='ms', **G.AR)
            if bb[0] < cx - cw / 2 + 6 or bb[2] > cx + cw / 2 - 6 or bb[1] < y0 + 4 or bb[3] > y1 - 4:
                raise ValueError(f'strip text {t!r} leaves its column or the band: {bb}')
    im.save(path); return path


def _has_audio(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries',
                        'stream=index', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return bool(r.stdout.strip())


def _height(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=height', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


#: Picture finish for every Reel (Mohammad, 12 Oct 2026, after the TEKKEN three-way test:
#: "make the filters standard for every Reel"): a light denoise before the enlargement so
#: compression blocks are not blown up, contrast-adaptive sharpening after it, a touch of
#: contrast and colour, and a fine moving grain that reads as detail on a phone and survives
#: Instagram's re-encode. Applied to footage and official stills, never to our own graphics
#: (numgfx clips under uploads/numbers/), which stay clean. FINISH = False turns it off.
FINISH = True
DENOISE = 'hqdn3d=1.5:1.5:4:4'
GRADE = 'eq=contrast=1.04:saturation=1.06,noise=alls=3:allf=t'


def _ours(f):
    return f.startswith('numbers/')


MAX_ZOOM = 2.0      # most a shot may be enlarged to fill 9:16 (Mohammad, 12 Oct 2026: image quality;
                    # the letterboxed Street Fighter trailer went out enlarged 2.4x and looked soft)
MIN_SRC_H = int(H / MAX_ZOOM)   # so a clip must keep 960 rows of picture once its bars are cut (was 700)

# Source quality checks (Mohammad, 24 Oct 2026, inbox 16:26Z, after the ARMS check). The ARMS soundtrack Reel broke
# into big squares at 12.2 to 12.9 s: Nintendo's only copy is 1280x720 at about 2.6 Mbps, enlarged 2.7x, and its own
# compression blocks grew in a fast camera swing. The decode and smear checks look for broken video, not a weak one.
# 1. Bitrate floor: a source under its floor (decodecheck.bitrate_floor: 5 Mbps at 1080p, 3 at 720p) is flagged
#    `lowbit` on the shot sheet and in the check output. A flag, not a stop.
# 2. Block check: a footage shot enlarged past MAX_ZOOM has its source stretch read for the 8x8 block-edge ratio
#    (decodecheck.block_ratio); a peak above DC.BLOCK_MAX is `blocky` on the sheet and stops the render unless
#    blocky_ok names the shot [(file, start, reason)] after someone has looked at it.
# 3. lowres_ok names the copies checked: a string, a list of the sources searched, or {"searched": [...], "result":
#    "..."}. A bare True stops the render (lowres_reason).
LOWRES_EXAMPLE = 'IGN, Nintendo store, publisher press site, Steam: none above 720p'


def lowres_reason(v):
    """The waiver for a soft source as text, or None when there is none. lowres_ok must name the copies that were
    searched (24 Oct 2026): a string, a list of sources, or {"searched": [...], "result": "..."}; a bare True (or
    an empty or one-word reason) stops with the reason to write."""
    if v is None or v is False or v == '' or v == [] or v == {}:
        return None
    if isinstance(v, dict):
        got = v.get('searched') or v.get('sources') or v.get('checked')
        got = ', '.join(got) if isinstance(got, (list, tuple)) else (got or '')
        res = v.get('result') or v.get('found') or v.get('note') or ''
        txt = (got + (': ' + res if res else '')).strip()
    elif isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v):
        txt = ', '.join(x.strip() for x in v if x.strip())
    elif isinstance(v, str):
        txt = v.strip()
    else:
        txt = ''
    if len(txt) < 12 or txt.lower() in ('true', 'yes', 'none exists', 'no other copy'):
        raise ValueError(f'lowres_ok must name the copies checked (Mohammad, 24 Oct 2026), not {v!r}: write the '
                         f'sources searched and what they had, e.g. "lowres_ok": "{LOWRES_EXAMPLE}", or '
                         '{"searched": ["IGN", "Nintendo store"], "result": "none above 720p"}')
    return txt


def _footage(f):
    """A source file the quality checks read: not a still, not our graphics, not a cached or stills clip."""
    return (os.path.splitext(f)[1].lower() not in STILL and not _ours(f)
            and not f.startswith((CACHE + '/', STILLS + '/')) and os.path.exists(C.U + f))


def source_quality(shots):
    """{shot index: {'zoom', 'bitrate' (flag text or None), 'block' ((median, peak, frames) or None), 'blocky'}}
    for every footage shot. The block ratio is read only where the shot is enlarged past MAX_ZOOM, on the shot's
    own stretch inside its letterbox; a few seconds a shot."""
    out = {}
    for i, (f, s, d, fo) in enumerate(shots):
        if s is None or not _footage(f):
            continue
        bars, rows = _bars(C.U + f, s, d)
        z = H / rows
        blk = None
        if z > MAX_ZOOM:
            crop = tuple(map(int, bars.split('crop=')[1].rstrip(',').split(':'))) if bars else None
            blk = DC.block_ratio(C.U + f, s, d, crop)
        out[i] = {'zoom': round(z, 2), 'rows': rows, 'bitrate': DC.bitrate_flag(C.U + f), 'block': blk,
                  'blocky': bool(blk and blk[1] > DC.BLOCK_MAX)}
    return out


def _waived(f, s, blocky_ok):
    for w in blocky_ok or ():
        if len(w) >= 3 and w[0] == f and abs(float(w[1]) - float(s)) < 0.05 and str(w[2]).strip():
            return str(w[2]).strip()
    return None


def quality_gate(shots, lowres_ok=None, blocky_ok=None):
    """Before the render: print every source-quality flag, then stop on a bare lowres_ok, a clip under MIN_SRC_H
    rows or a still past MAX_ZOOM with no lowres reason, or a blocky shot that blocky_ok does not waive. All the
    problems are listed in one error. Returns source_quality's report."""
    problems = []
    try:
        reason = lowres_reason(lowres_ok)
    except ValueError as e:
        reason, problems = None, [str(e)]
    q = source_quality(shots)
    seen, small = set(), []
    for i, (f, s, d, fo) in enumerate(shots):
        if os.path.splitext(f)[1].lower() in STILL and os.path.exists(C.U + f):
            z = zoom((f, s, d, fo))
            if z > MAX_ZOOM and not reason:
                problems.append(f'{f}: a still enlarged {z:.1f}x to fill 9:16; find a larger image or name the copies '
                                'checked in lowres_ok')
            continue
        if i not in q:
            continue
        r = q[i]
        if r['bitrate'] and f not in seen:
            print(f'source quality: {f}: {r["bitrate"]} (lowbit)', flush=True)
        seen.add(f)
        if r['rows'] < MIN_SRC_H:
            small.append(f'{f} at {s} ({r["rows"]} rows, enlarged {r["zoom"]}x)')
        if r['block']:
            med, peak, _ = r['block']
            w = _waived(f, s, blocky_ok)
            tag = 'blocky' if r['blocky'] else 'ok'
            print(f'source quality: shot {i} {f} at {s} for {d} s, enlarged {r["zoom"]}x: block ratio median {med}, '
                  f'peak {peak} ({tag}{", waived: " + w if r["blocky"] and w else ""})', flush=True)
            if r['blocky'] and not w:
                problems.append(f'shot {i} {f} at {s} for {d} s is blocky: block ratio peak {peak} over '
                                f'{DC.BLOCK_MAX} enlarged {r["zoom"]}x (the source\'s own compression blocks will show); '
                                'use another stretch or a better copy, or after looking pass '
                                f'blocky_ok=[["{f}", {s}, "reason"]]')
    if small and reason:
        print(f'source quality: under {MIN_SRC_H} rows: ' + ', '.join(small) + f'; lowres_ok: {reason}', flush=True)
    elif small:
        problems.append(f'under {MIN_SRC_H} rows of picture: ' + ', '.join(small) + '; find a 4K or unletterboxed '
                        f'copy, or name the copies checked in lowres_ok ("{LOWRES_EXAMPLE}")')
    if problems:
        raise ValueError('source quality:\n  ' + '\n  '.join(problems))
    return q


def zoom(shot):
    """How much a shot is enlarged to fill the 9:16 frame: 1080p footage
    1.78x, a letterboxed 2.39:1 trailer about 2.4x, 4K about 1x."""
    f, s, d, _ = shot
    if os.path.splitext(f)[1].lower() in STILL:
        iw, ih = Image.open(C.U + f).size
        return max(W / iw, H / ih)
    return H / _bars(C.U + f, s, d)[1]


NOBARS = set()                            # file names whose black is picture, not letterbox (product renders on black)


def _bars(p, s, d):
    """The picture inside a trailer's letterbox, as an ffmpeg crop (or '').
    On 3 Oct 2026 the Steam Deck Reel enlarged letterboxed Valve clips bars
    and all, leaving black bands across the frame. A file named in NOBARS
    is taken whole (16 Oct 2026: ASUS's product loops float the handheld on
    pure black, which cropdetect read as bars and enlarged 3.4x)."""
    if os.path.basename(p) in NOBARS:
        return '', _height(p)
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-ss', str(s), '-t', str(min(d, 3)), '-i', p,
                        '-vf', 'cropdetect=limit=24:round=2:reset=0', '-f', 'null', '-'],
                       capture_output=True, text=True)
    found = [l.split('crop=')[-1].split()[0] for l in r.stderr.splitlines() if 'crop=' in l]
    if not found:
        return '', _height(p)
    w, h, x, y = map(int, found[-1].split(':'))
    full = _height(p)
    return (f'crop={w}:{h}:{x}:{y},', h) if h < full - 8 else ('', full)


class Pan(list):
    """Two focus keyframes [(t_frac, x), (t_frac, x)] for one scene or one shot
    (14 Oct 2026): the 9:16 window sits at the first x until the first t_frac of
    the scene, pans linearly to the second x, and holds it from the second
    t_frac on. t_frac is 0 at the scene's start and 1 at its end. A plain
    number is still a fixed focus, so nothing existing changes."""


def pan(x0, x1, t0=0.25, t1=0.75):
    """A Pan from focus x0 (at t0 of the scene) to x1 (at t1)."""
    return Pan([(t0, x0), (t1, x1)])


def _pan_at(p, u):
    """Focus of Pan `p` at fraction `u` of its scene, clamped at the ends."""
    (t0, x0), (t1, x1) = p[0], p[1]
    if u <= t0 or t1 - t0 < 1e-6:
        return x0
    if u >= t1:
        return x1
    return x0 + (x1 - x0) * (u - t0) / (t1 - t0)


def _pan_expr(p, a, b):
    """ffmpeg expression for Pan `p` over the scene running a..b seconds."""
    if b is None:
        raise ValueError('a Pan needs the shot length to know where its scene ends')
    (t0, x0), (t1, x1) = p[0], p[1]
    ta, tb = a + t0 * (b - a), a + t1 * (b - a)
    if tb - ta < 1e-3:
        return str(x0)
    return f'if(lt(t,{ta:.3f}),{x0},if(gt(t,{tb:.3f}),{x1},{x0}+({x1}-{x0})*(t-{ta:.3f})/{tb - ta:.3f}))'


def _fo_expr(fo, d=None):
    """A focus for ffmpeg's crop: a number, per-scene keyframes
    [(offset, focus), ...] that switch at the trailer's own cuts, or a Pan
    (the whole shot, or any scene's focus) that moves between two keyframes.
    `d` is the shot length, needed where a Pan runs to the shot's end."""
    if isinstance(fo, Pan):
        return _pan_expr(fo, 0, d)
    if not isinstance(fo, (list, tuple)):
        return str(fo)

    def one(f, a, b):
        return _pan_expr(f, a, b) if isinstance(f, Pan) else str(f)
    expr = one(fo[-1][1], fo[-1][0], d)
    for i in range(len(fo) - 2, -1, -1):
        (t, f), t2 = fo[i], fo[i + 1][0]
        expr = f'if(lt(t,{t2:.3f}),{one(f, t, t2)},{expr})'
    return expr


def _fo_at(fo, off, d):
    """The focus _fo_expr gives `off` seconds into a shot of length `d`."""
    if isinstance(fo, Pan):
        return _pan_at(fo, off / max(d, 1e-6))
    if not isinstance(fo, (list, tuple)):
        return float(fo)
    for i, (t, f) in enumerate(fo):
        t2 = fo[i + 1][0] if i + 1 < len(fo) else d
        if off < t2 or i == len(fo) - 1:
            return _pan_at(f, (off - t) / max(t2 - t, 1e-6)) if isinstance(f, Pan) else float(f)


def scenes(f, start, dur, thresh=0.2):
    """Offsets (from `start`) where the trailer cuts, 0 first."""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-ss', str(start), '-t', str(dur), '-i', C.U + f,
                        '-vf', f"select='gt(scene,{thresh})',showinfo", '-an', '-f', 'null', '-'],
                       capture_output=True, text=True)
    cuts = [float(l.split('pts_time:')[1].split()[0]) for l in r.stderr.splitlines() if 'pts_time:' in l]
    out = [0.0]
    for c in cuts:
        if c - out[-1] >= 0.5:
            out.append(round(c, 3))
    return out


def _salient_x(img):
    """Where the subject sits across a frame (0 left .. 1 right), from a
    spectral-residual saliency map (Hou and Zhang, 2007), so the 9:16 zoom
    follows faces, ships and logos instead of the centre."""
    import numpy as np
    g = np.asarray(img.convert('L').resize((128, max(16, int(128 * img.height / img.width)))), float)
    F = np.fft.fft2(g); A = np.log(np.abs(F) + 1e-9); P = np.angle(F)
    k = np.ones((3, 3)) / 9
    from numpy.lib.stride_tricks import sliding_window_view as sw
    Ap = np.pad(A, 1, mode='edge'); R = A - (sw(Ap, (3, 3)) * k).sum(axis=(-1, -2))
    S = np.abs(np.fft.ifft2(np.exp(R + 1j * P))) ** 2
    S = np.asarray(Image.fromarray((S / S.max() * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(4)), float)
    S = np.where(S > np.percentile(S, 90), S, 0)
    col = S.sum(axis=0)
    return float((col * np.arange(len(col))).sum() / max(col.sum(), 1e-9) / (len(col) - 1))


#: Subject detector for autofocus (14 Oct 2026): YOLOv8n on the CPU, weights in /root/models
#: (not in git; fetched there on first use). It runs in a child process so its own numpy
#: (YOLO_LIBS, numpy 2.x, which torch needs) never mixes with this process's numpy.
YOLO_WEIGHTS = os.environ.get('YOLO_WEIGHTS', '/root/models/yolov8n.pt')
YOLO_LIBS = os.environ.get('YOLO_LIBS', '/root/models/pylibs')
#: COCO ids: person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, then every animal
#: (bird to giraffe). COCO has no "face", so a person box stands for one.
SUBJECT_CLASSES = list(range(0, 9)) + list(range(14, 24))
SAMPLES = (0.1, 0.5, 0.9)        # where in a scene autofocus looks
KEYS = (0.25, 0.75)              # where in a scene the two keyframes sit
_DETECT_PY = r"""
import json, os, sys
w, cls, paths = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3:]
from ultralytics import YOLO
if not os.path.exists(w):
    os.makedirs(os.path.dirname(w) or '.', exist_ok=True)
    from ultralytics.utils.downloads import attempt_download_asset
    attempt_download_asset(w)
out = []
for r in YOLO(w).predict(paths, imgsz=640, conf=0.25, classes=cls, device='cpu', verbose=False):
    h, wd = r.orig_shape
    best = None
    for (x1, y1, x2, y2) in r.boxes.xyxy.tolist():
        a = (x2 - x1) * (y2 - y1)
        if best is None or a > best[1]:
            best = ((x1 + x2) / 2 / wd, a / (wd * h))
    out.append(best)
print('@@' + json.dumps(out))
"""


def detect_subjects(paths):
    """[(centre x 0..1, box area share) or None] per image: the largest person,
    vehicle or animal YOLOv8n finds. All None (with a note on stderr) when the
    detector cannot run, so autofocus falls back to saliency."""
    env = dict(os.environ)
    if os.path.isdir(YOLO_LIBS):
        env['PYTHONPATH'] = YOLO_LIBS + os.pathsep + env.get('PYTHONPATH', '')
    try:
        r = subprocess.run([sys.executable, '-c', _DETECT_PY, YOLO_WEIGHTS, str(SUBJECT_CLASSES).replace(' ', '')] + list(paths),
                           capture_output=True, text=True, env=env, check=True)
        line = [l for l in r.stdout.splitlines() if l.startswith('@@')][-1]
        import json
        return [tuple(x) if x else None for x in json.loads(line[2:])]
    except Exception as e:
        why = (getattr(e, 'stderr', '') or str(e)).strip().splitlines()[-1:] or ['?']
        print(f'autofocus: detector unavailable ({why[0][:160]}), using saliency', file=sys.stderr)
        return [None] * len(paths)


def _keyframes(samples):
    """samples [(t_frac, x or None)] -> the subject's x at KEYS, interpolated
    from the detected samples only (clamped at their ends); None if none."""
    pts = [(q, x) for q, x in samples if x is not None]
    if not pts:
        return None
    def at(u):
        if u <= pts[0][0]:
            return pts[0][1]
        for (q0, x0), (q1, x1) in zip(pts, pts[1:]):
            if u <= q1:
                return x0 + (x1 - x0) * (u - q0) / (q1 - q0)
        return pts[-1][1]
    return [at(u) for u in KEYS]


#: Face turn for autofocus and the shot sheet (advisor, 21 Oct 2026: no side-on centring). YuNet (OpenCV)
#: finds the faces, profiles included; MediaPipe's face landmarker gives the yaw from its transformation
#: matrix for every face it can mesh. Its own detector skips faces turned past about 45 degrees (the
#: Stellaris man at 148 s, the Aphelion astronaut at 23 s), so for those the yaw comes from YuNet's five
#: points: the eyes close up as the head turns (eye gap over eye-to-mouth height, FACE_E0 when frontal)
#: and the nose's side gives the direction. Both models live in /root/models (not in git; fetched on
#: first use). Needs `pip install mediapipe` and libEGL (`apt-get install -y libegl1`); without them,
#: or on the runner, framing is exactly as before.
FACE_LANDMARKER = os.environ.get('FACE_LANDMARKER', '/root/models/face_landmarker.task')
FACE_DETECTOR = os.environ.get('FACE_DETECTOR', '/root/models/face_detection_yunet_2023mar.onnx')
FACE_URLS = ('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
             'https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx')
FACE_MIN = 0.12          # a face this share of the frame height or taller is the subject; smaller ones are background
FACE_E0 = 1.1            # eye gap over eye-to-mouth height on a frontal face (YuNet points, measured on two trailers)
FRONT_YAW = 30           # |yaw| below this: front
PROFILE_YAW = 60         # |yaw| above this: profile, framed with look room and flagged on the sheet; between: three-quarter
LOOK_ROOM = 2 / 3        # a profile face sits a third in from the side it turns away from
LOOK_MIN = 0.55          # less room than this on the side it looks to: the window cannot frame it, replace the shot
_FACES_PY = r"""
import json, math, os, sys, urllib.request
lmk, det, urls, paths = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), sys.argv[4:]
import cv2, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
for p, u in zip((lmk, det), urls):
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        urllib.request.urlretrieve(u, p + '.part'); os.replace(p + '.part', p)
lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=lmk), num_faces=4, output_facial_transformation_matrixes=True,
    min_face_detection_confidence=0.3, min_face_presence_confidence=0.3))
E0 = float(os.environ.get('FACE_E0', '1.1'))
out = []
for p in paths:
    im = cv2.imread(p); h, w = im.shape[:2]
    yn = cv2.FaceDetectorYN.create(det, '', (w, h), 0.6, 0.3, 50)
    found = yn.detect(im)[1]
    r = lm.detect(mp.Image.create_from_file(p))
    mesh = []
    for pts, M in zip(r.face_landmarks, r.facial_transformation_matrixes):
        xs, ys = [q.x for q in pts], [q.y for q in pts]
        mesh.append([(min(xs) + max(xs)) / 2, (max(ys) - min(ys)), math.degrees(math.atan2(M[0][2], M[2][2])), (min(ys) + max(ys)) / 2])
    faces = []
    for f in (found if found is not None else []):
        x, y, bw, bh = (float(v) for v in f[:4])
        m = [k for k in mesh if x <= k[0] * w <= x + bw and y <= k[3] * h <= y + bh]
        if m:
            yaw = m[0][2]; mesh.remove(m[0])
        else:
            ex, ey, my = (f[4] + f[6]) / 2, (f[5] + f[7]) / 2, (f[11] + f[13]) / 2
            e = abs(float(f[6] - f[4])) / max(float(my - ey), 1.0)
            yaw = math.degrees(math.acos(min(1.0, e / E0))) * (1 if f[8] >= ex else -1)
        faces.append(((x + bw / 2) / w, bh / h, round(yaw, 1), (y + bh / 2) / h))
    faces += [(k[0], k[1], round(k[2], 1), k[3]) for k in mesh]
    out.append(max(faces, key=lambda q: q[1]) if faces else None)
print('@@' + json.dumps(out))
"""


def turn(yaw):
    """'front', 'three-quarter' or 'profile' for a face's yaw in degrees."""
    a = abs(yaw)
    return 'front' if a < FRONT_YAW else 'profile' if a > PROFILE_YAW else 'three-quarter'


def detect_faces(paths, what='autofocus'):
    """[(centre x 0..1, height share, yaw degrees, centre y 0..1) or None] per image: the tallest face of at least
    FACE_MIN of the frame height. Negative yaw looks towards the frame's left, positive towards its
    right. All None (with a note on stderr) when MediaPipe or a model is missing, so framing stays as it was."""
    try:
        r = subprocess.run([sys.executable, '-c', _FACES_PY, FACE_LANDMARKER, FACE_DETECTOR, json.dumps(FACE_URLS)] + list(paths),
                           capture_output=True, text=True, check=True, env=dict(os.environ, FACE_E0=str(FACE_E0)))
        line = [l for l in r.stdout.splitlines() if l.startswith('@@')][-1]
        return [tuple(x) if x and x[1] >= FACE_MIN else None for x in json.loads(line[2:])]
    except Exception as e:
        why = [l for l in (getattr(e, 'stderr', '') or str(e)).strip().splitlines() if 'Error' in l][-1:] or ['?']
        print(f'{what}: face model unavailable ({why[0][:160]}), faces not measured', file=sys.stderr)
        return [None] * len(paths)


def look_x(face, wf):
    """Where to aim the 9:16 window (centre, 0..1 across the picture) for a face: on it when front or
    three-quarter; for a profile, shifted so the face sits a third in from the side it turns away from
    and the room is on the side it looks to. `wf` is the window's width as a share of the picture."""
    x, yaw = face[0], face[2]
    if turn(yaw) != 'profile':
        return x
    return x + (LOOK_ROOM - 0.5) * wf * (1 if yaw > 0 else -1)


def look_room(face, fo, wf):
    """Share of the 9:16 window on the side a profile face looks to, at focus `fo` (0 when the face
    centre falls outside the window)."""
    x, yaw = face[0], face[2]
    p = (x - fo * (1 - wf)) / wf                 # the face's place across the window, 0 left .. 1 right
    if not 0 <= p <= 1:                          # the face is outside the window: no framing at all
        return 0.0
    return 1 - p if yaw > 0 else p


class Focus(list):
    """autofocus's [(offset, focus)], plus `profile`: [(offset, side, room)] for each scene whose face is
    in profile, `side` the way it looks and `room` the share of the window on that side (LOOK_MIN at
    least, or the shot is replaced). A plain list everywhere else: job files store it as before."""
    def __init__(self, *a):
        super().__init__(*a)
        self.profile = []


def autofocus(f, start, dur, thresh=0.2, keyframes=False):
    """Per-scene focus for one continuous stretch: at each of the trailer's cuts,
    aim the 9:16 window at that scene's subject (Mohammad, 6 Oct 2026: "choose a
    better focus area"; advisor, 14 Oct 2026: aim at a detected subject, not at
    texture). Three frames per scene (10, 50 and 90%) go through YOLOv8n; the
    largest person, vehicle or animal in each sets where the subject is, and the
    scene gets two keyframes, the subject at 25% and at 75% of the scene,
    interpolated from the frames it was found in. Where nothing is detected the
    spectral saliency (_salient_x, the median of the three frames) stays as the
    fallback and the window holds still.

    Returns [(offset, focus)] with one focus per scene (the mean of its two
    keyframes), the shape the render scripts have always taken; with
    keyframes=True each focus is a Pan of the two keyframes, so the window moves
    with the subject. Either goes straight into a shot as its focus.

    Faces (advisor, 21 Oct 2026): the same frames go through the face pass
    (detect_faces). A face of at least FACE_MIN of the frame height is the
    subject: front and three-quarter faces are centred, a profile is framed
    with look room (look_x). The result is a Focus, whose `profile` lists each
    scene with a profile face, the side it looks to and the room it got; under
    LOOK_MIN the window cannot frame it and the shot is replaced. Without faces,
    or without MediaPipe, the focus is exactly as before."""
    bars, rows = _bars(C.U + f, start, dur)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width',
                            '-of', 'csv=p=0', C.U + f], capture_output=True, text=True).stdout.strip()
    iw = int(bars.split('crop=')[1].split(':')[0]) if bars else int(probe)
    sw_ = iw * H / rows                       # width after scaling the picture to the frame height
    cuts = scenes(f, start, dur, thresh) + [dur]
    tmp = tempfile.mkdtemp(prefix='autofocus-')
    try:
        paths = []
        for k, (a, b) in enumerate(zip(cuts, cuts[1:])):
            for j, q in enumerate(SAMPLES):
                p = f'{tmp}/{k}-{j}.png'
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{start + a + (b - a) * q:.2f}', '-i', C.U + f,
                                '-frames:v', '1', '-vf', f'{bars}scale=640:-2', p], check=True)
                paths.append(p)
        found = detect_subjects(paths)
        faces = detect_faces(paths)
        wf = W / sw_                          # the window's width as a share of the picture
        keys = Focus()
        for k, a in enumerate(cuts[:-1]):
            row = found[k * len(SAMPLES):(k + 1) * len(SAMPLES)]
            frow = faces[k * len(SAMPLES):(k + 1) * len(SAMPLES)]
            kf = _keyframes([(q, look_x(fc, wf) if fc else d[0] if d else None) for q, d, fc in zip(SAMPLES, row, frow)])
            if kf is None:                    # nothing detected: saliency, held still
                xs = [_salient_x(Image.open(p)) for p in paths[k * len(SAMPLES):(k + 1) * len(SAMPLES)]]
                kf = [sorted(xs)[1]] * 2
            fk = [round(min(1, max(0, (c * sw_ - W / 2) / max(sw_ - W, 1))), 3) for c in kf]
            keys.append((round(a, 3), pan(fk[0], fk[1], *KEYS) if keyframes else round(sum(fk) / 2, 3)))
            prof = [(q, fc) for q, fc in zip(SAMPLES, frow) if fc and turn(fc[2]) == 'profile']
            if prof:                          # look room as framed: where the window is at each sampled frame
                side = 'right' if sum(fc[2] for _, fc in prof) > 0 else 'left'
                at = (lambda q: _pan_at(pan(fk[0], fk[1], *KEYS), q)) if keyframes else (lambda q: sum(fk) / 2)
                room = round(min(look_room(fc, at(q), wf) for q, fc in prof), 2)
                keys.profile.append((round(a, 3), side, room))
                print(f'autofocus: profile face at {start + a:.1f} s looks {side}, {room:.0%} look room'
                      + ('' if room >= LOOK_MIN else '; the 9:16 window cannot frame it, replace the shot'), file=sys.stderr)
        return keys
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def montage(shots, out, lowres_ok=False, fast=False):
    """Cut the shots into one 9:16 clip with crossfades; returns (starts, end).
    Letterbox bars are cropped before the enlargement; a clip with fewer than
    MIN_SRC_H rows of picture, or a still enlarged past MAX_ZOOM, stops the
    render (it would look soft) unless lowres_ok names the copies checked
    (lowres_reason: a bare True stops, 24 Oct 2026)."""
    lowres_ok = lowres_reason(lowres_ok)
    stills = [os.path.splitext(s[0])[1].lower() in STILL for s in shots]
    sound = any(not st and _has_audio(C.U + s[0]) for s, st in zip(shots, stills))
    args = ['ffmpeg', '-nostdin', '-y', '-v', 'error']
    fc = []
    if CACHE_PICTURE and not fast:         # the picture pass per footage shot comes from the cache (advisor, 14 Oct 2026)
        shots = [((cached_shot(f, s, d, fo, lowres_ok), 0.0, d, fo) if not st and not _ours(f) and not f.startswith((CACHE + '/', STILLS + '/')) else (f, s, d, fo))
                 for (f, s, d, fo), st in zip(shots, stills)]
    for i, ((f, s, d, fo), st) in enumerate(zip(shots, stills)):
        if st:
            a, b = fo if isinstance(fo, (tuple, list)) else (fo, fo)
            if isinstance(fo, Pan):
                a, b = fo[0][1], fo[1][1]
            z = zoom((f, s, d, fo))
            if z > MAX_ZOOM and not lowres_ok:
                raise ValueError(f'{f}: a still enlarged {z:.1f}x to fill 9:16; find a larger image or name the copies checked in lowres_ok')
            args += ['-loop', '1', '-framerate', '30', '-t', str(d), '-i', C.U + f]
            sw, sh = W * SUB, H * SUB              # pan at 4x, scale down last (18 Oct 2026: whole-pixel pans judder)
            fc.append(f'[{i}:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,'
                      f"crop={sw}:{sh}:x='(iw-{sw})*({a}+({b}-{a})*t/{d})':y='(ih-{sh})/2',"
                      f'scale={W}:{H}:flags=lanczos{_still_finish(f)},'
                      f'fps=30,settb=AVTB,setsar=1,format=yuv420p[v{i}]')
        elif f.startswith((CACHE + '/', STILLS + '/')):   # already the finished picture at 1080x1920, exactly d long (cache, or stills_clips push-ins)
            args += ['-t', str(d), '-i', C.U + f]
            fc.append(f'[{i}:v]settb=AVTB,setsar=1,format=yuv420p[v{i}]')
        else:
            args += ['-ss', str(s), '-t', str(d), '-i', C.U + f]
            # Footage is 16:9, so filling 9:16 enlarges it (1.78x for 1080p, more
            # for letterboxed trailers): lanczos keeps edges and the FINISH chain
            # cleans and sharpens around it (lighter on 4K, which is not enlarged).
            bars, rows = _bars(C.U + f, s, d)
            if rows < MIN_SRC_H and not lowres_ok:
                raise ValueError(f'{f}: only {rows} rows of picture (bars cut), enlarged {H / rows:.1f}x; '
                                 f'find a 4K or unletterboxed copy, or name the copies checked in lowres_ok ("{LOWRES_EXAMPLE}")')
            if FINISH and not _ours(f):     # the standard finish (12 Oct 2026): denoise, enlarge, adaptive sharpen, grade
                pre, post = f'{DENOISE},', f",cas={0.7 if rows < H else 0.4},{GRADE}"
            else:                           # our graphics, or FINISH off: the old lanczos + light unsharp
                pre, post = '', (',unsharp=5:5:0.5:5:5:0.0' if rows < H else '')
            fc.append(f"[{i}:v]{bars}{pre}scale=-2:{H}:flags=lanczos,crop={W}:{H}:x='(iw-{W})*({_fo_expr(fo, d)})':y=0{post},fps=30,tpad=stop_mode=clone:stop_duration=0.5,trim=duration={d},setpts=PTS-STARTPTS,settb=AVTB,setsar=1,format=yuv420p[v{i}]")   # padded and trimmed to exactly d: a clip a few frames short ended the xfade chain early (12 Oct)
    if sound:
        for i, ((f, s, d, fo), st) in enumerate(zip(shots, stills)):
            if st or not _has_audio(C.U + f):
                fc.append(f'anullsrc=r=48000:cl=stereo,atrim=0:{d}[a{i}]')
            else:
                fc.append(f'[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]')
    starts, t, pv, pa = [0.0], shots[0][2], 'v0', 'a0'
    if X < 0.1:                             # hard cuts: concat, each shot trimmed to its slot. Chained xfades with a
        n, segs = len(shots), []            # 1-frame overlap drift a frame a shot and stop early (He-Man, 12 Oct: 28 s of 35)
        for i, (_, _, d, _) in enumerate(shots):
            slot = d - X if i < n - 1 else d
            fc.append(f'[v{i}]trim=duration={slot:.3f},setpts=PTS-STARTPTS[cv{i}]'); segs.append(f'[cv{i}]')
            if sound:
                fc.append(f'[a{i}]atrim=duration={slot:.3f},asetpts=PTS-STARTPTS[ca{i}]'); segs.append(f'[ca{i}]')
            if i: starts.append(starts[-1] + shots[i - 1][2] - X)
        t = starts[-1] + shots[-1][2]
        fc.append(''.join(segs) + f'concat=n={n}:v=1:a={1 if sound else 0}' + ('[cv][ca]' if sound else '[cv]'))
        pv, pa = 'cv', 'ca'
    for i in range(1, len(shots) if X >= 0.1 else 1):
        off = t - X; starts.append(off)
        fc.append(f'[{pv}][v{i}]xfade=transition={TRANSITION}:duration={X}:offset={off:.3f}[xv{i}]'); pv = f'xv{i}'
        if sound:
            fc.append(f'[{pa}][a{i}]acrossfade=d={X}[xa{i}]'); pa = f'xa{i}'
        t = off + shots[i][2]
    aenc = ['-c:a', 'aac', '-b:a', '192k'] if fast else ['-c:a', 'pcm_s16le']   # lossless sound in the intermediate
    maps = ['-map', f'[{pv}]'] + (['-map', f'[{pa}]'] + aenc if sound else [])
    subprocess.run(args + ['-filter_complex', ';'.join(fc)] + maps + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + (DRAFT_ENC if fast else inter_enc()) + [out], check=True)
    return starts, t


def read_secs(text):
    """Time a viewer needs to read a line once: about 14 characters a second
    plus half a second to find it, never under 2.2 s (Mohammad, 3 Oct 2026:
    the Steam Deck lines went by too fast to read)."""
    return max(2.2, 0.5 + len(text.replace('\n', ' ').replace('|', ' ')) / 14)


DRAFT_ENC = ['-preset', 'ultrafast', '-crf', '30']
#: Render time (advisor, 14 Oct 2026). One encode per Reel: the montage and the text pass write lossless intermediates
#: (INTER_ENC; a near-lossless crf 8 when the disk has under 3 GB free), and only outro.append encodes, at FINAL_ENC
#: (Instagram re-encodes to about 5 Mbps, so slow/15 bought nothing visible). The picture pass per footage shot
#: (bars, denoise, enlarge, cas, grade) is cached under uploads/cache keyed by (file, start, duration, focus) so a text
#: or strip change only re-burns the text. PROFILES['breaking'] is the breaking lane's fast path.
FINAL_ENC = ['-preset', 'medium', '-crf', '18']
INTER_ENC = ['-preset', 'ultrafast', '-qp', '0']
CACHE = 'cache'                      # uploads/cache/<key>.mkv
CACHE_PICTURE = True
PROFILES = {'breaking': dict(finish=False, enc=['-preset', 'veryfast', '-crf', '20'], music=False)}
TIMES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'render-times.json')


def inter_enc():
    free = shutil.disk_usage(C.U).free
    return INTER_ENC if free > 3e9 else ['-preset', 'ultrafast', '-crf', '8']


def _shot_key(f, s, d, fo):
    import hashlib
    src = C.U + f
    raw = json.dumps([f, s, d, repr(fo), FINISH, MAX_ZOOM, DENOISE, GRADE, os.path.getmtime(src), os.path.getsize(src)])
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def cached_shot(f, s, d, fo, lowres_ok=False):
    """The picture pass for one footage shot, rendered once to uploads/cache/<key>.mkv
    (video at inter_enc, the shot's own sound as pcm) and reused by every later
    render of the same (file, start, duration, focus). Returns the cache path
    relative to uploads."""
    lowres_ok = lowres_reason(lowres_ok)
    os.makedirs(C.U + CACHE, exist_ok=True)
    key = _shot_key(f, s, d, fo)
    rel = f'{CACHE}/{key}.mkv'
    if os.path.exists(C.U + rel):
        return rel
    bars, rows = _bars(C.U + f, s, d)
    if rows < MIN_SRC_H and not lowres_ok:
        raise ValueError(f'{f}: only {rows} rows of picture (bars cut), enlarged {H / rows:.1f}x; '
                         f'find a 4K or unletterboxed copy, or name the copies checked in lowres_ok ("{LOWRES_EXAMPLE}")')
    if FINISH and not _ours(f):
        pre, post = f'{DENOISE},', f",cas={0.7 if rows < H else 0.4},{GRADE}"
    else:
        pre, post = '', (',unsharp=5:5:0.5:5:5:0.0' if rows < H else '')
    vf = (f"{bars}{pre}scale=-2:{H}:flags=lanczos,crop={W}:{H}:x='(iw-{W})*({_fo_expr(fo, d)})':y=0{post},"
          f"fps=30,tpad=stop_mode=clone:stop_duration=0.5,trim=duration={d},setpts=PTS-STARTPTS,setsar=1,format=yuv420p")
    a = ['-map', '0:a?', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2'] if _has_audio(C.U + f) else ['-an']
    tmp = C.U + rel + '.part.mkv'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(s), '-t', str(d), '-i', C.U + f, '-vf', vf,
                    '-map', '0:v', '-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + inter_enc() + a + ['-t', str(d), tmp], check=True)
    os.replace(tmp, C.U + rel)
    return rel


def warm_cache(shots, lowres_ok=False):
    """Rule 6 (advisor, 14 Oct 2026): for a dated story, run the picture pass the
    evening before so the render on the day is text and outro only."""
    out = []
    for f, s, d, fo in shots:
        if os.path.splitext(f)[1].lower() not in STILL and not _ours(f) and not f.startswith(CACHE + '/'):
            out.append(cached_shot(f, s, d, fo, lowres_ok))
    return out


def _record_times(name, profile, stages):
    try:
        led = json.load(open(TIMES))
    except (OSError, ValueError):
        led = []
    import datetime
    now = datetime.datetime.utcnow(); total = sum(stages.values())
    led.append(dict(name=name, profile=profile or 'standard', at=now.strftime('%Y-%m-%dT%H:%MZ'),
                    stages={k: round(v, 1) for k, v in stages.items()}, total=round(total, 1),
                    # lanes (advisor, 20 Oct 2026): runner or container, queued and finished, render minutes
                    lane=os.environ.get('RENDER_LANE', 'container'),
                    queued_at=os.environ.get('RENDER_QUEUED_AT') or (now - datetime.timedelta(seconds=total)).strftime('%Y-%m-%dT%H:%MZ'),
                    finished_at=now.strftime('%Y-%m-%dT%H:%MZ'), render_min=round(total / 60, 2)))
    json.dump(led[-100:], open(TIMES, 'w'), indent=1)
    return led[-1]
PINK_FLAG = False         # Mohammad, 4 Oct 2026: pink in game footage and official art is fine
PINK = (210, 242)       # PIL HSV hue band for pink and magenta (red and purple stay out)


def _frame(f, t, w=240):
    tmp = tempfile.mktemp(suffix='.png')
    for back in range(13):                  # a seek past the picture's last frame writes nothing and exits 0
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, t - 0.25 * back):.2f}', '-i', f,
                        '-frames:v', '1', '-vf', f'scale={w}:-2', tmp], check=True)   # (SteamOS v3 sheet, 24 Oct)
        if os.path.exists(tmp):
            if back:
                print(f'sheet frame: {os.path.basename(f)} has no picture at {t:.2f} s, used {t - 0.25 * back:.2f} s')
            im = Image.open(tmp).convert('RGB'); os.remove(tmp); return im
    raise SystemExit(f'sheet frame: {os.path.basename(f)} has no picture at or 3 s before {t:.2f} s')


def _flags(im):
    """'pink' when over 3% of the frame is saturated pink or magenta, 'black'
    for a near-black frame (a fade or a gap between scenes)."""
    out = []
    h, sat, v = im.convert('HSV').split()
    hd, sd, vd = h.getdata(), sat.getdata(), v.getdata()
    n = len(hd)
    pink = sum(1 for a, b, c in zip(hd, sd, vd) if PINK[0] <= a <= PINK[1] and b > 90 and c > 90)
    if PINK_FLAG and pink / n > 0.03:      # off: the no-pink rule is for our colours, not the games
        out.append('pink')
    if sum(vd) / n < 22:
        out.append('black')
    return out


ACCENT = (40, 182, 246)      # azure, the Digital Lounge accent: the crop window on the sheet


def _src_size(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                        '-of', 'csv=p=0', p], capture_output=True, text=True)
    w, h = r.stdout.strip().split(',')[:2]
    return int(w), int(h)


def _window(bars, srcw, srch, focus):
    """The 9:16 window a shot takes from its source, in source pixels
    (left, top, right, bottom), given the letterbox crop and the focus."""
    px, py, pw, ph = 0, 0, srcw, srch
    if bars:
        pw, ph, px, py = map(int, bars.split('crop=')[1].rstrip(',').split(':'))
    ww = ph * W / H                          # window width in picture pixels
    x0 = px + (pw - ww) * min(1, max(0, focus))
    return x0, py, x0 + ww, py + ph


def _word_boxes(im, conf=70, letters=3):
    """(word, left, top, right, bottom) for each word tesseract reads in `im` (PIL), with at
    least `letters` letters at `conf` or better; None when the tesseract binary is absent."""
    import shutil, tempfile
    if not shutil.which('tesseract'):
        return None
    with tempfile.NamedTemporaryFile(suffix='.png') as tf:
        im.convert('L').save(tf.name)
        r = subprocess.run(['tesseract', tf.name, '-', '--psm', '11', 'tsv'], capture_output=True, text=True)
    out = []
    for ln in r.stdout.splitlines()[1:]:
        c = ln.split('\t')
        if len(c) == 12 and c[11].strip() and float(c[10]) >= conf:
            w = ''.join(ch for ch in c[11] if ch.isalpha())
            if len(w) >= letters:
                l, t, ww, hh = map(int, c[6:10])
                out.append((w, l, t, l + ww, t + hh))
    return out


def _words(im, conf=70):
    """Words tesseract reads in `im` (PIL), at least three letters at `conf` or better. The
    first frame is the grid tile (advisor, 19 Oct 2026): a slate, title card or publisher text
    behind the headline ("GAMES PRESENTS" on the Rockstar tile) is caught by this. Needs the
    tesseract binary (`apt-get install -y tesseract-ocr` in a new container); None when absent."""
    b = _word_boxes(im, conf)
    return None if b is None else [w for w, *_ in b]


def edge_text(im, x0, x1, conf=60):
    """Words in the full frame `im` whose box crosses an edge of the crop window x0..x1 (in
    `im` pixels): printed text, a logo or a subtitle the 9:16 crop would cut (advisor, 20 Oct
    2026). Drop the shot when the text does not matter; when it is the point (the Edgerunners 2
    Oshima card), rebuild it as a vertical card in the game's own style. Returns
    [(word, box)], [] when clean, None without tesseract."""
    b = _word_boxes(im, conf)
    if b is None:
        return None
    return [(w, (l, t, r, bt)) for w, l, t, r, bt in b if l < x0 < r or l < x1 < r]


def _vert(f, s, d, fo, t, width=1280):
    """The cropped vertical frame the phone shows at seek time `t` of shot (f, s, d, fo)."""
    full = _frame(C.U + f, t, width)
    bars = _bars(C.U + f, s, d)[0]; srcw, srch = _src_size(C.U + f)
    x0, y0, x1, y1 = _window(bars, srcw, srch, _fo_at(fo, t - s, d)); k = full.width / srcw
    return full.crop((round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)))


def first_clean(shot, step=0.2, upto=3.0):
    """The first seek time in the shot whose vertical frame carries no readable text, or None."""
    f, s, d, fo = shot
    t = s
    while t <= s + min(upto, d - 0.5):
        w = _words(_vert(f, s, d, fo, t))
        if w is not None and not w:
            return round(t, 2)
        t += step
    return None


def shotsheet(shots, out):
    """Before any render: the first, middle and last frame of every shot, in
    one sheet, labelled with the seek time, so title cards, end slates,
    logos and pink are caught before the encode (3 Oct 2026: Nagoshi and
    Micron each rendered four times over things this sheet shows). Each
    footage frame is a pair (14 Oct 2026): the cropped vertical frame the
    phone will show, and beside it the full 16:9 frame with the crop window
    outlined in the accent, so the editor sees what the crop took. Returns
    (sheet path, [(shot index, time, flags)]) for frames flagged pink or black, for
    readable text in the first shot's first frame (the grid tile; advisor, 19 Oct 2026),
    with the first clean seek time after it, and for text, a logo or a subtitle that the
    crop window cuts (`cut-text`, outlined in red; advisor, 20 Oct 2026), and for frames whose
    main face is in profile (`profile`, the face outlined in amber; advisor, 21 Oct 2026): fix it
    or justify it in the brief. Source quality (24 Oct 2026, after ARMS): `lowbit` for a source under its bitrate
    floor and `blocky` for a shot enlarged past MAX_ZOOM whose source stretch reads blocky (source_quality)."""
    from PIL import ImageDraw as D
    FW, FH = 288, 162                        # the full frame; the vertical crop beside it is FH tall
    VW = round(FH * W / H)
    tiles, flagged = [], []
    f0, s0, d0, fo0 = shots[0]               # the grid tile: no text in the first frame (advisor, 19 Oct 2026)
    if os.path.splitext(f0)[1].lower() in STILL:
        w0 = _words(Image.open(C.U + f0).convert('RGB'))
    else:
        w0 = _words(_vert(f0, s0, d0, fo0, s0))
    if w0 is None:
        print('shotsheet: tesseract missing, first-frame text not checked (apt-get install -y tesseract-ocr)')
    elif w0:
        fc = None if os.path.splitext(f0)[1].lower() in STILL else first_clean(shots[0])
        flagged.append((0, s0, ['text: ' + ' '.join(w0[:4]) + (f'; first clean frame at {fc}' if fc is not None else '; no clean frame in the first 3 s')]))
    seen = {(i, t): _frame(C.U + f, t, 640) for i, (f, s, d, fo) in enumerate(shots)
            if os.path.splitext(f)[1].lower() not in STILL for t in (s + 0.15, s + d / 2, s + d - 0.15)}
    tmp = tempfile.mkdtemp(prefix='sheetfaces-')
    try:                                     # every footage frame through the face pass at once (advisor, 21 Oct 2026)
        for n, im in enumerate(seen.values()):
            im.save(f'{tmp}/{n}.png')
        faces = dict(zip(seen, detect_faces([f'{tmp}/{n}.png' for n in range(len(seen))], 'shotsheet') if seen else []))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    qual = source_quality(shots)              # bitrate floor and block check (24 Oct 2026, after ARMS)
    for i, (f, s, d, fo) in enumerate(shots):
        z = zoom(shots[i])
        soft = ['soft'] if z > MAX_ZOOM else []       # enlarged past MAX_ZOOM: look for a sharper copy
        if soft:
            flagged.append((i, s, soft))
        q = qual.get(i) or {}
        if q.get('bitrate'):
            soft = soft + ['lowbit']
            flagged.append((i, s, [q['bitrate']]))
        if q.get('blocky'):
            soft = soft + ['blocky']
            flagged.append((i, s, [f'blocky: block ratio peak {q["block"][1]} (median {q["block"][0]}) enlarged {q["zoom"]}x']))
        if os.path.splitext(f)[1].lower() in STILL:
            im = Image.open(C.U + f).convert('RGB'); im.thumbnail((240, 240))
            tiles.append((i, f'still x{z:.1f}' + (' +soft' if soft else ''), im)); continue
        bars = _bars(C.U + f, s, d)[0]
        srcw, srch = _src_size(C.U + f)
        for t in (s + 0.15, s + d / 2, s + d - 0.15):
            full = seen[i, t]
            face = faces.get((i, t))
            side = face and turn(face[2]) == 'profile' and ['profile']
            fl = _flags(full.resize((240, round(240 * full.height / full.width)))) + soft + (side or [])
            if fl:
                flagged.append((i, round(t, 2), fl))
            x0, y0, x1, y1 = _window(bars, srcw, srch, _fo_at(fo, t - s, d))
            k = full.width / srcw
            big = _frame(C.U + f, t, 1280); kb = big.width / srcw   # text cut by the crop (advisor, 20 Oct 2026)
            cut = edge_text(big, x0 * kb, x1 * kb) or []
            if cut:
                fl = fl + ['cut-text']
                flagged.append((i, round(t, 2), ['text cut by the crop: ' + ' '.join(w for w, _ in cut[:4])]))
            vert = full.crop((round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k))).resize((VW, FH))
            thumb = full.resize((FW, round(FW * full.height / full.width)))
            dr = D.Draw(thumb)
            k2 = thumb.width / srcw
            dr.rectangle([x0 * k2, y0 * k2, x1 * k2 - 1, y1 * k2 - 1], outline=ACCENT, width=3)
            if side:                                             # the profile face, outlined in amber on the full frame
                fx, fy, fh = face[0] * thumb.width, face[3] * thumb.height, face[1] * thumb.height
                dr.rectangle([fx - fh * 0.4, fy - fh * 0.5, fx + fh * 0.4, fy + fh * 0.5],
                             outline=(255, 176, 0), width=2)
            for _, (l, tp, r, bt) in cut:                        # the cut words, outlined in red on the full frame
                q = k2 / kb
                dr.rectangle([l * q - 1, tp * q - 1, r * q + 1, bt * q + 1], outline=(255, 60, 60), width=2)
            tile = Image.new('RGB', (FW + 4 + VW, max(thumb.height, FH)), (20, 19, 50))
            tile.paste(vert, (0, 0)); tile.paste(thumb, (VW + 4, 0))
            tiles.append((i, f'{t:.1f} x{z:.1f}' + (' +' + '+'.join(fl) if fl else ''), tile))
    cw = max(im.width for _, _, im in tiles) + 6
    th = max(im.height for _, _, im in tiles)
    cols = max(1, 1560 // cw)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cw * cols, (th + 22) * rows), (20, 19, 50))
    d = D.Draw(sheet)
    for k, (i, lab, im) in enumerate(tiles):
        x, y = (k % cols) * cw, (k // cols) * (th + 22)
        sheet.paste(im, (x, y + 22))
        d.text((x + 4, y + 4), f'#{i} {shots[i][0][:16]} @{lab}', fill=(255, 80, 80) if '+' in lab else (255, 230, 120))
    sheet.save(out)
    return out, flagged


def strip(video, out, every=2.5):
    """After a render: a frame every `every` seconds across the finished
    Reel, for the last look before it is shown."""
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video],
                       capture_output=True, text=True)
    dur = float(r.stdout)
    ts = [0.3] + [1.5 + k * every for k in range(int((dur - 2) / every))]
    ims = [_frame(video, t, 216) for t in ts]
    cols = 10
    sheet = Image.new('RGB', (216 * cols, ims[0].height * ((len(ims) + cols - 1) // cols)))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * 216, (k // cols) * im.height))
    sheet.save(out)
    return out


def timeline(shots):
    """Shot start times and total length of the cut, as montage() builds it."""
    starts, t = [0.0], shots[0][2]
    for sh in shots[1:]:
        starts.append(t - X); t = t - X + sh[2]
    return starts, t


def spread(texts, t0, t1, gap=0.0):
    """Give each sentence a share of [t0, t1] by its length, at least its
    reading time."""
    w = [max(len(x), 14) for x in texts]
    span = t1 - t0; out, t = [], t0
    for x, k in zip(texts, w):
        d = max(read_secs(x), span * k / sum(w))
        out.append((x, t, min(t + d, t1), {})); t += d
    return out


def by_shot(groups):
    """groups: [(first_shot, last_shot, [texts or (text, opts)])]; each group's
    sentences share the time from the first shot's start to the next shot
    after the last one. Returns a function for reel(lines=...)."""
    def place(starts, end):
        out = []
        for a, b, texts in groups:
            t0 = starts[a] + (0.25 if a else 3.6)   # the first line waits for the head band
            t1 = starts[b + 1] if b + 1 < len(starts) else end
            span = (t1 - t0) / len(texts)
            for i, x in enumerate(texts):
                text, kw = (x, {}) if isinstance(x, str) else x
                out.append((text, t0 + i * span, t0 + (i + 1) * span, kw))
        return out
    return place


def _voice_over(body, voice, end, duck_db, out):
    """Lay the read over the cut: the footage's sound drops `duck_db` while he
    speaks (40 ms down, 450 ms back up) and returns in the pauses; a cut with
    no sound gets the voice alone (outro still adds the jingle)."""
    import numpy as np, soundfile as sf
    tmp = os.path.dirname(out)
    sr, n = 48000, int(round(end * 48000))
    def wav(src, dst, extra=()):
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', src, *extra, '-vn', '-ac', '2',
                        '-ar', str(sr), '-c:a', 'pcm_f32le', dst], check=True)
        x, _ = sf.read(dst, dtype='float32', always_2d=True); return x
    v = wav(voice, f'{tmp}/v.wav')
    if len(v) > n + sr // 20:
        raise ValueError(f'the read runs {len(v) / sr:.1f}s but the shots only {end:.1f}s; add footage')
    v = np.pad(v, ((0, max(0, n - len(v))), (0, 0)))[:n]
    mix = v.copy()
    if _has_audio(body):
        bg = wav(body, f'{tmp}/bg.wav'); bg = np.pad(bg, ((0, max(0, n - len(bg))), (0, 0)))[:n]
        hop = sr // 100; frames = n // hop
        rms = np.sqrt((v[:frames * hop].mean(axis=1) ** 2).reshape(frames, hop).mean(axis=1))
        db = 20 * np.log10(rms + 1e-9)
        active = (db > db.max() - 30).astype('float32')      # speaking: within 30 dB of the loudest
        target = 1 - (1 - 10 ** (-duck_db / 20)) * active
        g = np.empty_like(target); cur = 1.0
        down, up = 1 - np.exp(-1 / 4), 1 - np.exp(-1 / 45)  # about 40 ms down, 450 ms up
        for i, t in enumerate(target):
            cur += (t - cur) * (down if t < cur else up); g[i] = cur
        gain = np.interp(np.arange(n), np.arange(frames) * hop + hop / 2, g).astype('float32')
        mix = bg * gain[:, None] + v
    peak = np.abs(mix).max()
    if peak > 0.89:
        mix *= 0.89 / peak
    sf.write(f'{tmp}/mix.wav', mix, sr, subtype='FLOAT')
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-i', f'{tmp}/mix.wav',
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy'] + (['-c:a', 'pcm_s16le'] if out.endswith('.mkv') else ['-c:a', 'aac', '-b:a', '192k']) + [
                    '-t', f'{end:.3f}', out], check=True)
    return out


def _music(f):
    """`f` without its voices: demucs' two-stem split keeps the music and
    effects. Cached next to the upload as <name>-music.wav. demucs runs in
    DEMUCS_PY (a Python with demucs installed), default this one."""
    dst = C.U + os.path.splitext(f)[0] + '-music.wav'
    if not os.path.exists(dst):
        tmp = tempfile.mkdtemp(prefix='demucs-')
        try:
            subprocess.run([os.environ.get('DEMUCS_PY', sys.executable), '-m', 'demucs', '--two-stems=vocals',
                            '-o', tmp, C.U + f], check=True, capture_output=True)
            stem = os.path.splitext(os.path.basename(f))[0]
            shutil.move(f'{tmp}/htdemucs/{stem}/no_vocals.wav', dst)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return dst


def _track(body, track, end, out):
    """Put one continuous stretch of a trailer's own sound under the cut, so
    the music runs on instead of jumping at every shot (Mohammad, 3 Oct 2026).
    `track` is (file, start) or (file, start, 'music') to strip the voices."""
    f, start, *mode = track
    src = _music(f) if mode and mode[0] == 'music' else C.U + f
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-ss', str(start), '-t', f'{end:.3f}', '-i', src,
                    '-filter_complex', '[1:a]aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.3[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy'] + (['-c:a', 'pcm_s16le'] if out.endswith('.mkv') else ['-c:a', 'aac', '-b:a', '192k']) +
                   ['-t', f'{end:.3f}', out], check=True)
    return out


def _sting(body, sting, at, out, draft=False):
    """Mix a skin's short sting into the body's sound at `at` seconds, under the footage (advisor, 20 Oct 2026)."""
    ms = int(at * 1000)
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-i', sting, '-filter_complex',
                    f'[1:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},volume=0.8[s];'
                    f'[0:a][s]amix=inputs=2:duration=first:normalize=0[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy']
                   + (['-c:a', 'aac'] if draft else ['-c:a', 'pcm_s16le']) + [out], check=True)
    return out


def check_reading(lines, end):
    """Stop when a line is on screen for less than its reading time, naming
    the line and how much footage would fix it. Lines placed by hand are
    trimmed so one leaves before the next arrives, so check after that."""
    short = []
    for k, (text, a, z, _) in enumerate(lines):
        z = min(z, end, lines[k + 1][1] if k + 1 < len(lines) else end)
        need = read_secs(text)
        if z - a < need - 0.05:
            short.append(f'  "{text.splitlines()[0]}…" {z - a:.1f}s of {need:.1f}s')
    if short:
        raise ValueError('lines too fast to read; add related footage or move the line:\n' + '\n'.join(short))


def reel(shots, headline, label, lines, source, date, out, theme='stylized', sound=None,
         country=None, head_secs=3.5, vivid=True, style=None, voice=None, duck_db=18,
         lowres_ok=False, read_check=True, track=None, draft=False, head_size=HEAD_SIZE, cut=False, credits=None, strip=None,
         products=None, template=None, tribute=False, reveal=None, profile=None, pace_ok=False, skin=None,
         person=None, blocky_ok=None):
    """`blocky_ok`: [(file, start, reason)], shots enlarged past MAX_ZOOM whose source reads blocky (quality_gate,
    24 Oct 2026) and that someone has looked at; `lowres_ok` names the copies checked (lowres_reason), never True.
    `person`: [(photo, name, role, t0, t1, opts), ...] (advisor, 23 Oct 2026, people stories show the person):
    the person's official photo in a framed window with a name plate over the running footage from t0 to t1
    (Reel seconds; the first appearance within the first 3 to 4 s, with the line that names them), opts
    {'focus': (x, y), 'credit': text} as in person_layer. The footage and its sound keep running under it.
    `skin`: a game skins pilot kit, 'scifi' or 'fantasy' (advisor, 20 Oct 2026; skins.py, the kit's tokens in
    templates/web/skins/<kit>.css): the kit's band decoration and plates, its line outline and entrance, its shot
    to shot transition, a light leak over each cut (fantasy) and a short sting at the first line. None (the default)
    is the house look exactly as before; عاجل always keeps its crimson house skin.
    `strip`: [(label, value), ...], 2 or 3 facts for the `split` template
    (Mohammad, 14 Oct 2026): a slim strip pinned low in the safe zone from the end
    of the headline to the end of the clip, the story lines rising above it. A
    value is a string or ('aed', '149'); a line that already says a value stops
    the render (one fact, one place). See strip_layer.
    `products`: [(png, name, note_or_None), ...], the `edition` template (advisor, 14 Oct 2026),
    4 to 6 items: `shots` is then just [hook, closing] (a trailer stretch for the headline,
    and about 2 s of footage under the closing line). The items go between them as
    edition.products() clips, one per item, and ONE composition frame of every item,
    all on the living ground; the `strip` is pinned on the composition frame only
    (a line may not overlap it, and no line is lifted). Shot indices for by_shot()
    and credits count the expanded list: hook 0, items 1..n, composition n + 1,
    closing n + 2. Run the trailer's music under the whole Reel with `track=`. See edition.py.
    `credits`: [(first_shot, last_shot, text)] labels footage that is not
    of the story's subject («لقطات من Fortnite»), shown over those shots.
    `cut=True` joins the shots with hard cuts instead of crossfades: the
    Comparison format (Mohammad, 10 Oct 2026), two states side by side in time
    with their labels as lines, no soft blending.
    `track`: (file, start) plays one continuous stretch of that trailer's
    sound under the whole cut, in place of each shot's own; `track='bed'` drops
    the footage's sound for our own bed (`sound=` picks the flavour to match the
    tone, default the everyday rotation) when no stretch of the trailer is good
    (Mohammad, 6 Oct 2026); add 'music' as a third item to strip its voices
    (demucs). Otherwise footage keeps its own sound (Mohammad, 3 Oct 2026).
    `draft=True` is the quick look before the real encode: ultrafast at a
    low quality, no end card, written next to `out` as <name>-draft.mp4 and
    about three times faster. Fix shots on the draft, then render for real.
    `voice`: his processed read (templates/voice.py output). It plays over
    the footage, whose own sound drops about `duck_db` under it and comes back
    up in the pauses; the shots should add up to at least the read's length.
    Without a voice every line must stay up for its reading time (read_secs);
    the render stops otherwise, so a short story gets more related footage."""
    global X
    lowres_ok = lowres_reason(lowres_ok)   # a bare True stops here, before anything is built (24 Oct 2026)
    if label == 'عاجل':                    # عاجل is a skin on any template (advisor, 14 Oct 2026): crimson and the breaking bed
        theme, sound = 'crimson', sound or 'breaking'
        skin = None                        # and stays crimson on any game skin (advisor, 20 Oct 2026)
    if skin == 'house':
        skin = None
    if skin and skin not in SK.KITS:
        raise ValueError(f'skin {skin!r}: the pilot kits are {", ".join(SK.KITS)}; the others wait for the pilot result')
    if tribute:                            # the stills variant for a death (advisor, 14 Oct 2026): cold, no waves, no chip, body-grey
        theme, vivid, label, sound = 'cold', False, None, sound or 'neon_c'   # lines, slow dissolves, a calm bed, a quiet end card
    if (cut or tribute) and X not in (0.04, 1.0):   # hard cuts for Comparison and stills, slow dissolves for a tribute; restored on the way out
        keep, X = X, (1.0 if tribute else 0.04)
        try:
            return reel(shots, headline, label, lines, source, date, out, theme, sound, country, head_secs, vivid,
                        style, voice, duck_db, lowres_ok, read_check, track, draft, head_size, credits=credits, strip=strip,
                        products=products, template=template, tribute=tribute, reveal=reveal, profile=profile, pace_ok=pace_ok,
                        skin=skin, person=person, blocky_ok=blocky_ok)
        finally:
            X = keep
    global FINISH
    if profile and not PROFILES[profile].get('finish', True) and FINISH:   # the breaking profile: no picture finish, no demucs
        keep_f, FINISH = FINISH, False
        try:
            return reel(shots, headline, label, lines, source, date, out, theme, sound, country, head_secs, vivid,
                        style, voice, duck_db, lowres_ok, read_check, track, draft, head_size, cut, credits=credits, strip=strip,
                        products=products, template=template, tribute=tribute, reveal=reveal, profile=profile, pace_ok=pace_ok,
                        skin=skin, person=person, blocky_ok=blocky_ok)
        finally:
            FINISH = keep_f
    if profile and not PROFILES[profile].get('music', True) and isinstance(track, (tuple, list)) and len(track) > 2:
        track = tuple(track[:2])
    import time
    stages, _t = {}, time.time()
    def lap(k):
        nonlocal _t
        stages[k] = time.time() - _t; _t = time.time()
    G._ACC = G.ACCENTS[theme]
    comp = None                            # index of the composition shot (edition template)
    if products:                           # hook + items + composition + closing (14 Oct 2026)
        if len(shots) < 2:
            raise ValueError('products needs shots=[hook, closing]: a trailer stretch first, footage for the closing line last')
        import edition
        mid = edition.shots(products, theme, os.path.splitext(os.path.basename(out))[0], fast=draft)
        comp = len(shots) - 1 + len(products)
        shots = list(shots[:-1]) + mid + list(shots[-1:])
    tmp = tempfile.mkdtemp(prefix='reel-')
    try:
        starts, end = timeline(shots)          # known before the slow encode
        import formats
        print(length_note(end, exempt=template in formats.LENGTH_EXEMPT))   # 12 to 20 s target (advisor, 14 Oct 2026)
        if callable(lines):                    # lines placed against the cut's own shot starts
            lines = lines(starts, end)
        if lines and isinstance(lines[0], str):
            lines = spread(lines, head_secs + 0.1, end)
        if read_check and not voice:
            check_reading(lines, end)
        pn = pace_note(starts, end, lines, head_secs if strip else None)
        if pn and not pace_ok:                 # review of the Nano Reel (advisor, 14 Oct 2026): ten seconds on one still went out
            raise ValueError(pn + '; cut to a second angle, add a line or a strip, or pass pace_ok=True with the reason in the brief')
        for note in (pn, close_note(shots)):
            if note: print(note)               # attention rules (advisor, 14 Oct 2026)
        if reveal is not None:                 # word-by-word reveal on the key line only
            lines = _reveal(lines, reveal)
        if tribute:
            lines = [(t, a, z, {**kw, 'ink': A.BODY}) for t, a, z, kw in lines]
        if strip:                              # lines rise over the strip; a repeated fact or a bad strip stops here
            strip_check(strip, lines); strip_layer(strip, f'{tmp}/strip.png', theme, skin=skin)
            if comp is None:
                lines = [(t, a, z, kw if kw.get('top') else {**kw, 'lift': STRIP_LIFT}) for t, a, z, kw in lines]
            else:                          # edition: the strip owns the composition frame, no line may share it
                sa, sz = starts[comp], starts[comp + 1]
                for t, a, z, _ in lines:
                    if a < sz and z > sa:
                        raise ValueError(f'the composition frame ({sa:.1f} to {sz:.1f}s) carries the strip only, never a line: {t}')
        for i, (text, _, _, kw) in enumerate(lines):   # a line outside the safe zone stops here, not after the encode
            line_layer(text, f'{tmp}/l{i}.png', skin=skin, **kw)
        quality_gate(shots, lowres_ok, blocky_ok)   # bitrate floor, block check, named lowres_ok (24 Oct 2026)
        lap('checks')
        ext = 'mp4' if draft else 'mkv'             # lossless intermediates for the real render (advisor, 14 Oct 2026)
        global TRANSITION
        keep_tr = TRANSITION
        if skin:                                    # the kit's cut between shots
            TRANSITION = SK.transition(skin)
        try:
            montage(shots, f'{tmp}/cut.{ext}', lowres_ok, fast=draft)
        finally:
            TRANSITION = keep_tr
        lap('montage')
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    style = style or ('lines' if skin else pick_style(out))   # after the checks, so a stopped render takes no turn; a skin takes none
    layers = [(head_layer(headline, label, f'{tmp}/head.png', source, date, country, hs=head_size,   # HEAD_SIZE unless a job asks for more; never below HEAD_MIN
                          hst=head_size + 20, vivid=vivid, theme=theme, seed=sum(map(ord, out)), style=style,
                          meta_path=f'{tmp}/meta.png', skin=skin), 0, head_secs)]
    if vivid and style == 'frame' and not skin:   # the bottom waves stay for the whole clip
        layers.insert(0, (frame_layer(f'{tmp}/frame.png', theme, sum(map(ord, out))), 0, end))
    if MARK_PERSIST:                        # the play mark, small and half transparent, for the whole Reel (14 Oct 2026)
        layers.insert(0, (mark_layer(f'{tmp}/mark.png'), 0, end))
    fixed = len(layers)                     # these never get trimmed by the next line
    layers.append((f'{tmp}/meta.png', min(CREDIT_AT, head_secs - 0.5), head_secs))   # the credit line enters at 2 s
    for i, (text, a, z, kw) in enumerate(lines):
        layers.append((line_layer(text, f'{tmp}/l{i}.png', skin=skin, **kw), a, min(z, end)))
    line_paths = {f'{tmp}/l{i}.png' for i in range(len(lines))}
    for i in range(fixed + 1, len(layers) - 1):    # a line leaves before the next arrives (the head and credit are not lines)
        p, a, z = layers[i]; layers[i] = (p, a, min(z, layers[i + 1][1]))
    if strip:                              # after the trim: the strip stays for the rest of the clip, fading in over 0.4 s
        if comp is None:                   # it hides under a card (advisor review, 14 Oct 2026): never card, frame line and strip stacked
            a0, segs = head_secs, []
            for i, (f, _, _, _) in enumerate(shots):
                if _ours(f):
                    z = starts[i]; a1 = starts[i + 1] if i + 1 < len(starts) else end
                    if z - a0 > 0.6: segs.append((a0, z))
                    a0 = a1
            if end - a0 > 0.6: segs.append((a0, end))
            for a, z in segs:
                layers.append((f'{tmp}/strip.png', a, z))
        else:
            layers.append((f'{tmp}/strip.png', starts[comp], starts[comp + 1]))
    for j, (photo, name, role, a, z, *opt) in enumerate(person or []):   # after the trim: the window overlaps the lines
        opt = opt[0] if opt else {}
        if not 0 <= a < z <= end:
            raise ValueError(f'person window {name} runs {a} to {z} s, outside the clip (0 to {end:.1f} s)')
        layers.append((person_layer(photo, name, role, f'{tmp}/p{j}.png', theme=theme, focus=tuple(opt.get('focus', (0.5, 0.33))),
                                    credit=opt.get('credit')), a, z))
    for j, (first, last, text, *opt) in enumerate(credits or []):   # after the trim: credits overlap the lines
        opt = opt[0] if opt else {}
        # {'from_start': True, 'low': True, 'size': 42, 'band': True}: a stand-in credit readable on the grid tile, low so it
        # clears the headline (23 Oct 2026, the Mass Effect leak Reel, where stand-in footage sat under «تسرب عرض»)
        a = 0.0 if opt.get('from_start') and first == 0 else max(starts[first] + 0.2, head_secs + 0.1)   # not under the headline
        z = starts[last + 1] if last + 1 < len(starts) else end
        low = opt.get('low', any(kw.get('top') and la < z and lz > a for _, la, lz, kw in lines))
        if z - a > 0.5:                                        # a low credit sits just above the strip, not on it
            layers.append((credit_layer(text, f'{tmp}/c{j}.png', low=low, size=opt.get('size', 36),
                                        y=STRIP_TOP - 12 if low and strip else None, band=opt.get('band', False)), a, z))
    if skin and SK.leak_layer(f'{tmp}/leak.png', skin):   # fantasy: a warm light leak over each cut
        for s0 in starts[1:]:
            if s0 + 0.35 < end:
                layers.append((f'{tmp}/leak.png', max(0.05, s0 - 0.3), s0 + 0.35))
    ent = SK.entrance(skin) if skin else None
    args = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', f'{tmp}/cut.{ext}']
    for p, _, _ in layers:
        args += ['-loop', '1', '-t', f'{end:.2f}', '-i', p]
    fc = ['[0:v]setsar=1,fps=30[v0]']
    for i, (p, a, z) in enumerate(layers, 1):
        moving = bool(ent) and p in line_paths and a > 0 and (ent[0] or ent[1])
        fd = 0.4 if strip and p == f'{tmp}/strip.png' else (round(ent[2] * 0.8, 2) if moving else 0.2)
        fin = f",fade=t=in:st={a:.2f}:d={fd}:alpha=1" if a > 0 else ''
        fout = f',fade=t=out:st={z - 0.2:.2f}:d=0.2:alpha=1' if z < end - 0.01 else ''
        if moving:                          # the kit's entrance: in from dx right and dy below, easing out over its duration
            u = f'min(1\\,max(0\\,(t-{a:.2f})/{ent[2]}))'
            pos = f"x='{ent[0]}*pow(1-{u}\\,3)':y='{ent[1]}*pow(1-{u}\\,3)':eval=frame"
        else:
            pos = '0:0'
        fc += [f'[{i}:v]format=rgba{fin}{fout}[l{i}]', f'[v{i - 1}][l{i}]overlay={pos}:shortest=1[v{i}]']
    fc.append(f'[v{len(layers)}]format=yuv420p[v]')
    body = f'{tmp}/body.{ext}'
    amap = ['-map', '0:a?'] + (['-c:a', 'aac'] if draft else ['-c:a', 'copy'])
    subprocess.run(args + ['-filter_complex', ';'.join(fc), '-map', '[v]'] + amap +
                   ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + (DRAFT_ENC if draft else inter_enc())
                   + [body], check=True)
    lap('text')
    if track == 'bed':                     # no good stretch in the trailer: our own bed under the cut (6 Oct 2026)
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-map', '0:v', '-c:v', 'copy', '-an',
                        f'{tmp}/silent.{ext}'], check=True)
        body = f'{tmp}/silent.{ext}'
    elif track:
        body = _track(body, track, end, f'{tmp}/track.{ext}')
    if voice:
        body = _voice_over(body, voice, end, duck_db, f'{tmp}/voiced.{ext}')
    if skin and lines and _has_audio(body):   # the kit's sting at the cut into the first line
        body = _sting(body, sonic.sting(skin, f'{tmp}/sting.wav'), lines[0][1], f'{tmp}/sting.{ext}', draft)
    lap('audio')
    if draft:                              # no end card, no bed: the draft is for checking the cut
        done = os.path.splitext(out)[0] + '-draft.mp4'
        shutil.move(body, done)
        shutil.rmtree(tmp, ignore_errors=True)
        return done, starts, end
    sound = sound or G.SOUNDS.get(label, 'neon')
    bed = None                             # clips with no sound rotate the everyday bed; the jingle stays
    if sound == 'neon':
        bed = outro.evolving_bed(sonic.rotate(os.path.basename(out)), end)
    elif sound in sonic.EVERYDAY:              # a named everyday bed (the tribute's calm neon_c)
        bed = outro.evolving_bed(sound, end)
    done = outro.append(body, out, sound, bed=bed, accent=G.ACCENTS[theme], quiet=tribute,
                        enc=PROFILES[profile]['enc'] if profile else None)   # the one real encode (advisor, 14 Oct 2026)
    lap('outro')
    shutil.rmtree(tmp, ignore_errors=True)  # the temp renders filled the disk on 2 Oct
    print('render times', _record_times(os.path.basename(out), profile, stages))
    return done, starts, end
