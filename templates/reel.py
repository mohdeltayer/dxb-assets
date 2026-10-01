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
import os, subprocess, tempfile
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


def head_layer(headline, label, path, source, date, country=None, hs=66, hst=86):
    """Chip, headline and the credit line on a soft band at the top."""
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
        words = headline.split(); tw = lambda x: probe.textlength(x, font=f, **G.AR)
        bw = min(max(tw(' '.join(words[:k])), tw(' '.join(words[k:]))) for k in range(1, len(words)))
        hl = max(L, int(W - R - bw - 16))
    end = G._head(probe, headline, G.SAFE_TOP + 10, label, country, hs, hst, right=R, left=hl)
    meta_y = end + 30
    _band(im, 0, meta_y + 220, True, 190)
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    G._head(d, headline, G.SAFE_TOP + 10, label, country, hs, hst, right=R, left=hl)
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


def montage(shots, out):
    """Cut the shots into one 9:16 clip with crossfades; returns (starts, end)."""
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
            fc.append(f'[{i}:v]scale=-2:{H},crop={W}:{H}:(iw-{W})*{fo}:0,fps=30,settb=AVTB,setsar=1,format=yuv420p[v{i}]')
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
    subprocess.run(args + ['-filter_complex', ';'.join(fc)] + maps + ['-c:v', 'libx264', '-crf', '18', out], check=True)
    return starts, t


def spread(texts, t0, t1, gap=0.0):
    """Give each sentence a share of [t0, t1] by its length, at least 1.8 s."""
    w = [max(len(x), 14) for x in texts]
    span = t1 - t0; out, t = [], t0
    for x, k in zip(texts, w):
        d = max(1.8, span * k / sum(w))
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


def reel(shots, headline, label, lines, source, date, out, theme='stylized', sound=None,
         country=None, head_secs=3.5):
    G._ACC = G.ACCENTS[theme]
    tmp = tempfile.mkdtemp(prefix='reel-')
    starts, end = montage(shots, f'{tmp}/cut.mp4')
    if callable(lines):                    # lines placed against the cut's own shot starts
        lines = lines(starts, end)
    if lines and isinstance(lines[0], str):
        lines = spread(lines, head_secs + 0.1, end)
    layers = [(head_layer(headline, label, f'{tmp}/head.png', source, date, country), 0, head_secs)]
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
                   ['-c:v', 'libx264', '-crf', '21', body], check=True)
    sound = sound or G.SOUNDS.get(label, 'neon')
    bed = None                             # clips with no sound rotate the everyday bed; the jingle stays
    if sound == 'neon':
        bed = outro._cached('bed', sonic.rotate(os.path.basename(out)))
    return outro.append(body, out, sound, bed=bed, accent=G.ACCENTS[theme]), starts, end
