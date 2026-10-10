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
"""
import math, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter
import cards as C, fast_ar as A, ig_ar as G, outro, sonic

W, H = 1080, 1920
L, R = G.SAFE_LEFT, G.SAFE_RIGHT
X = 0.4                                   # crossfade between shots
SYM = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'dirham-symbol-mask.png')).convert('L')
STILL = ('.jpg', '.jpeg', '.png', '.webp')


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


def head_layer(headline, label, path, source, date, country=None, hs=66, hst=86,
               vivid=False, theme='cold', seed=0, style='lines'):
    """Chip, headline and the credit line on a soft band at the top. `vivid`
    colours the chip with the theme and lays the theme's wave lines in the band."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    probe = ImageDraw.Draw(Image.new('RGBA', (W, H)))
    room = W - R - L
    while True:                            # a long Latin name shrinks the headline, never the frame
        f = A.F('Bold', hs)
        lines = G._wrap(probe, headline, f, room)
        if len(lines) <= 3 and all(probe.textlength(x, font=f, **G.AR) <= room for x in lines):
            break
        if hs <= 48:
            raise ValueError(f'headline will not fit the safe zone: {headline}')
        hs, hst = hs - 4, hst - 5
    hl = L
    if len(lines) == 2:                    # balance two lines so no word hangs alone
        words = G._tokens(headline); tw = lambda x: probe.textlength(x, font=f, **G.AR)
        bw = min(max(tw(' '.join(words[:k])), tw(' '.join(words[k:]))) for k in range(1, len(words)))
        hl = max(L, int(W - R - bw - 16))
    chip = G._ACC if vivid else None
    end = G._head(probe, headline, G.SAFE_TOP + 10, label, country, hs, hst, right=R, left=hl)
    meta_y = end + 30
    _band(im, 0, meta_y + 220, True, 190)
    if vivid:
        _colour(im, meta_y + 140, theme, seed, style)
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    G._head(d, headline, G.SAFE_TOP + 10, label, country, hs, hst, right=R, left=hl, chip=chip)
    d.rectangle([W - R - 44, meta_y - 2, W - R, meta_y + 2], fill=G._ACC)
    d.text((W - R - 62, meta_y), f'{source}\u200f  ·  \u200f{A.arabic_date(date)}', font=A.F('Medium', 32),
           fill=A.BODY, anchor='rm', **G.AR)
    glow = Image.new('RGBA', (W, H), A.GROUND + (0,))
    glow.putalpha(t.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, v * 2)))
    im.alpha_composite(glow); im.alpha_composite(t); im.save(path); return path


def line_layer(text, path, price=None, shade=False, top=False, size=70, step=96):
    """One sentence, right-aligned; bottom line on SAFE_BOTTOM - 40, or
    under SAFE_TOP with top=True."""
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
    if len(lines) > 3:
        raise ValueError(f'{len(lines)} lines; keep a sentence to 3: {text}')
    base0 = G.SAFE_TOP + 110 if top else G.SAFE_BOTTOM - 40 - step * (len(lines) - 1)
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
    for col, m, off in [((0, 0, 0), shadow, (3, 4)), (A.GROUND, outline, (0, 0)), (A.INK, mask, (0, 0))]:
        lay = Image.new('RGBA', (W, H), col + (255,)); a = Image.new('L', (W, H), 0)
        a.paste(m, off); lay.putalpha(a); im.alpha_composite(lay)
    im.save(path); return path


def _has_audio(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries',
                        'stream=index', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return bool(r.stdout.strip())


def _height(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=height', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


MIN_SRC_H = 700     # picture rows a clip must keep once its bars are cut


def _bars(p, s, d):
    """The picture inside a trailer's letterbox, as an ffmpeg crop (or '').
    On 3 Oct 2026 the Steam Deck Reel enlarged letterboxed Valve clips bars
    and all, leaving black bands across the frame."""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-ss', str(s), '-t', str(min(d, 3)), '-i', p,
                        '-vf', 'cropdetect=limit=24:round=2:reset=0', '-f', 'null', '-'],
                       capture_output=True, text=True)
    found = [l.split('crop=')[-1].split()[0] for l in r.stderr.splitlines() if 'crop=' in l]
    if not found:
        return '', _height(p)
    w, h, x, y = map(int, found[-1].split(':'))
    full = _height(p)
    return (f'crop={w}:{h}:{x}:{y},', h) if h < full - 8 else ('', full)


def _fo_expr(fo):
    """A focus for ffmpeg's crop: a number, or per-scene keyframes
    [(offset, focus), ...] that switch at the trailer's own cuts."""
    if not isinstance(fo, (list, tuple)):
        return str(fo)
    expr = str(fo[-1][1])
    for (t, f), (t2, _) in reversed(list(zip(fo, fo[1:]))):
        expr = f'if(lt(t,{t2:.3f}),{f},{expr})'
    return expr


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


def autofocus(f, start, dur, thresh=0.2):
    """Per-scene focus keyframes for one continuous stretch: at each of the
    trailer's cuts, aim the 9:16 window at that scene's subject (Mohammad,
    6 Oct 2026: "choose a better focus area"). Returns [(offset, focus)]."""
    bars, rows = _bars(C.U + f, start, dur)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width',
                            '-of', 'csv=p=0', C.U + f], capture_output=True, text=True).stdout.strip()
    iw = int(bars.split('crop=')[1].split(':')[0]) if bars else int(probe)
    sw_ = iw * H / rows                       # width after scaling the picture to the frame height
    cuts = scenes(f, start, dur, thresh) + [dur]
    keys = []
    for a, b in zip(cuts, cuts[1:]):
        xs = []
        for t in (a + (b - a) * q for q in (0.25, 0.5, 0.75)):
            tmp = tempfile.mktemp(suffix='.png')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start + t:.2f}', '-i', C.U + f, '-frames:v', '1',
                            '-vf', f'{bars}scale=320:-2', tmp], check=True)
            xs.append(_salient_x(Image.open(tmp))); os.remove(tmp)
        c = sorted(xs)[1]
        keys.append((round(a, 3), round(min(1, max(0, (c * sw_ - W / 2) / max(sw_ - W, 1))), 3)))
    return keys


def montage(shots, out, lowres_ok=False, fast=False):
    """Cut the shots into one 9:16 clip with crossfades; returns (starts, end).
    Letterbox bars are cropped before the enlargement; a clip with fewer than
    MIN_SRC_H rows of picture stops the render (it would be enlarged 3x or
    more and look soft) unless lowres_ok."""
    stills = [os.path.splitext(s[0])[1].lower() in STILL for s in shots]
    sound = any(not st and _has_audio(C.U + s[0]) for s, st in zip(shots, stills))
    args = ['ffmpeg', '-nostdin', '-y', '-v', 'error']
    fc = []
    for i, ((f, s, d, fo), st) in enumerate(zip(shots, stills)):
        if st:
            a, b = fo if isinstance(fo, (tuple, list)) else (fo, fo)
            args += ['-loop', '1', '-framerate', '30', '-t', str(d), '-i', C.U + f]
            fc.append(f'[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,'
                      f"crop={W}:{H}:x='(iw-{W})*({a}+({b}-{a})*t/{d})':y='(ih-{H})/2',"
                      f'fps=30,settb=AVTB,setsar=1,format=yuv420p[v{i}]')
        else:
            args += ['-ss', str(s), '-t', str(d), '-i', C.U + f]
            # Footage is 16:9, so filling 9:16 enlarges it (1.78x for 1080p, more
            # for letterboxed trailers): lanczos keeps edges, a light unsharp
            # restores what the enlargement softens. 4K sources need neither.
            bars, rows = _bars(C.U + f, s, d)
            if rows < MIN_SRC_H and not lowres_ok:
                raise ValueError(f'{f}: only {rows} rows of picture (bars cut); find a sharper copy '
                                 f'or pass lowres_ok=True')
            sharp = ',unsharp=5:5:0.5:5:5:0.0' if rows < H else ''
            fc.append(f"[{i}:v]{bars}scale=-2:{H}:flags=lanczos{sharp},crop={W}:{H}:x='(iw-{W})*({_fo_expr(fo)})':y=0,fps=30,settb=AVTB,setsar=1,format=yuv420p[v{i}]")
    if sound:
        for i, ((f, s, d, fo), st) in enumerate(zip(shots, stills)):
            if st or not _has_audio(C.U + f):
                fc.append(f'anullsrc=r=48000:cl=stereo,atrim=0:{d}[a{i}]')
            else:
                fc.append(f'[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]')
    starts, t, pv, pa = [0.0], shots[0][2], 'v0', 'a0'
    for i in range(1, len(shots)):
        off = t - X; starts.append(off)
        fc.append(f'[{pv}][v{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[xv{i}]'); pv = f'xv{i}'
        if sound:
            fc.append(f'[{pa}][a{i}]acrossfade=d={X}[xa{i}]'); pa = f'xa{i}'
        t = off + shots[i][2]
    maps = ['-map', f'[{pv}]'] + (['-map', f'[{pa}]', '-c:a', 'aac', '-b:a', '192k'] if sound else [])
    subprocess.run(args + ['-filter_complex', ';'.join(fc)] + maps + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + (DRAFT_ENC if fast else ['-preset', 'slow', '-crf', '15']) + [out], check=True)
    return starts, t


def read_secs(text):
    """Time a viewer needs to read a line once: about 14 characters a second
    plus half a second to find it, never under 2.2 s (Mohammad, 3 Oct 2026:
    the Steam Deck lines went by too fast to read)."""
    return max(2.2, 0.5 + len(text.replace('\n', ' ').replace('|', ' ')) / 14)


DRAFT_ENC = ['-preset', 'ultrafast', '-crf', '30']
PINK_FLAG = False         # Mohammad, 4 Oct 2026: pink in game footage and official art is fine
PINK = (210, 242)       # PIL HSV hue band for pink and magenta (red and purple stay out)


def _frame(f, t, w=240):
    tmp = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, t):.2f}', '-i', f, '-frames:v', '1',
                    '-vf', f'scale={w}:-2', tmp], check=True)
    im = Image.open(tmp).convert('RGB'); os.remove(tmp); return im


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


def shotsheet(shots, out):
    """Before any render: the first, middle and last frame of every shot, in
    one sheet, labelled with the seek time, so title cards, end slates,
    logos and pink are caught before the encode (3 Oct 2026: Nagoshi and
    Micron each rendered four times over things this sheet shows). Returns
    (sheet path, [(shot index, time, flags)]) for frames flagged pink or black."""
    from PIL import ImageDraw as D
    tiles, flagged = [], []
    for i, (f, s, d, _) in enumerate(shots):
        if os.path.splitext(f)[1].lower() in STILL:
            im = Image.open(C.U + f).convert('RGB'); im.thumbnail((240, 240))
            tiles.append((i, 'still', im)); continue
        for t in (s + 0.15, s + d / 2, s + d - 0.15):
            im = _frame(C.U + f, t)
            fl = _flags(im)
            if fl:
                flagged.append((i, round(t, 2), fl))
            tiles.append((i, f'{t:.1f}' + (' ' + '+'.join(fl) if fl else ''), im))
    th = max(im.height for _, _, im in tiles)
    cols = 9
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (240 * cols, (th + 22) * rows), (20, 19, 50))
    d = D.Draw(sheet)
    for k, (i, lab, im) in enumerate(tiles):
        x, y = (k % cols) * 240, (k // cols) * (th + 22)
        sheet.paste(im, (x, y + 22))
        d.text((x + 4, y + 4), f'#{i} {shots[i][0][:18]} @{lab}', fill=(255, 80, 80) if '+' in lab or 'pink' in lab
               or 'black' in lab else (255, 230, 120))
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
            t0 = starts[a] + (0.25 if a else 3.6)
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
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
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
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-t', f'{end:.3f}', out], check=True)
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
         lowres_ok=False, read_check=True, track=None, draft=False, head_size=66):
    """`track`: (file, start) plays one continuous stretch of that trailer's
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
    G._ACC = G.ACCENTS[theme]
    tmp = tempfile.mkdtemp(prefix='reel-')
    try:
        starts, end = timeline(shots)          # known before the slow encode
        if callable(lines):                    # lines placed against the cut's own shot starts
            lines = lines(starts, end)
        if lines and isinstance(lines[0], str):
            lines = spread(lines, head_secs + 0.1, end)
        if read_check and not voice:
            check_reading(lines, end)
        for i, (text, _, _, kw) in enumerate(lines):   # a line outside the safe zone stops here, not after the encode
            line_layer(text, f'{tmp}/l{i}.png', **kw)
        montage(shots, f'{tmp}/cut.mp4', lowres_ok, fast=draft)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    style = style or pick_style(out)       # after the checks, so a stopped render takes no turn
    layers = [(head_layer(headline, label, f'{tmp}/head.png', source, date, country, hs=head_size,   # a long Latin title can take 60 so its line opens in Arabic
                          hst=head_size + 20, vivid=vivid, theme=theme, seed=sum(map(ord, out)), style=style), 0, head_secs)]
    if vivid and style == 'frame':          # the bottom waves stay for the whole clip
        layers.insert(0, (frame_layer(f'{tmp}/frame.png', theme, sum(map(ord, out))), 0, end))
    for i, (text, a, z, kw) in enumerate(lines):
        layers.append((line_layer(text, f'{tmp}/l{i}.png', **kw), a, min(z, end)))
    for i in range(1, len(layers) - 1):    # a line leaves before the next arrives
        p, a, z = layers[i]; layers[i] = (p, a, min(z, layers[i + 1][1]))
    args = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', f'{tmp}/cut.mp4']
    for p, _, _ in layers:
        args += ['-loop', '1', '-t', f'{end:.2f}', '-i', p]
    fc = ['[0:v]setsar=1,fps=30[v0]']
    for i, (p, a, z) in enumerate(layers, 1):
        fin = f',fade=t=in:st={a:.2f}:d=0.2:alpha=1' if a > 0 else ''
        fout = f',fade=t=out:st={z - 0.2:.2f}:d=0.2:alpha=1' if z < end - 0.01 else ''
        fc += [f'[{i}:v]format=rgba{fin}{fout}[l{i}]', f'[v{i - 1}][l{i}]overlay=0:0:shortest=1[v{i}]']
    fc.append(f'[v{len(layers)}]format=yuv420p[v]')
    body = f'{tmp}/body.mp4'
    amap = ['-map', '0:a?', '-c:a', 'aac']
    subprocess.run(args + ['-filter_complex', ';'.join(fc), '-map', '[v]'] + amap +
                   ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + (DRAFT_ENC if draft else ['-preset', 'slow', '-crf', '16'])
                   + [body], check=True)
    if track == 'bed':                     # no good stretch in the trailer: our own bed under the cut (6 Oct 2026)
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-map', '0:v', '-c:v', 'copy', '-an',
                        f'{tmp}/silent.mp4'], check=True)
        body = f'{tmp}/silent.mp4'
    elif track:
        body = _track(body, track, end, f'{tmp}/track.mp4')
    if voice:
        body = _voice_over(body, voice, end, duck_db, f'{tmp}/voiced.mp4')
    if draft:                              # no end card, no bed: the draft is for checking the cut
        done = os.path.splitext(out)[0] + '-draft.mp4'
        shutil.move(body, done)
        shutil.rmtree(tmp, ignore_errors=True)
        return done, starts, end
    sound = sound or G.SOUNDS.get(label, 'neon')
    bed = None                             # clips with no sound rotate the everyday bed; the jingle stays
    if sound == 'neon':
        bed = outro._cached('bed', sonic.rotate(os.path.basename(out)))
    done = outro.append(body, out, sound, bed=bed, accent=G.ACCENTS[theme])
    shutil.rmtree(tmp, ignore_errors=True)  # the temp renders filled the disk on 2 Oct
    return done, starts, end
