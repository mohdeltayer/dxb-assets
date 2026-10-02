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
import math, os, shutil, subprocess, tempfile
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
        words = headline.split(); tw = lambda x: probe.textlength(x, font=f, **G.AR)
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
            # Footage is 16:9, so filling 9:16 enlarges it (1.78x for 1080p, more
            # for letterboxed trailers): lanczos keeps edges, a light unsharp
            # restores what the enlargement softens. 4K sources need neither.
            sharp = ',unsharp=5:5:0.5:5:5:0.0' if _height(C.U + f) < H else ''
            fc.append(f'[{i}:v]scale=-2:{H}:flags=lanczos{sharp},crop={W}:{H}:(iw-{W})*{fo}:0,fps=30,settb=AVTB,setsar=1,format=yuv420p[v{i}]')
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
    subprocess.run(args + ['-filter_complex', ';'.join(fc)] + maps + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-crf', '15', out], check=True)
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


def reel(shots, headline, label, lines, source, date, out, theme='stylized', sound=None,
         country=None, head_secs=3.5, vivid=True, style=None, voice=None, duck_db=18):
    """`voice`: his processed read (templates/voice.py output). It plays over
    the footage, whose own sound drops about `duck_db` under it and comes back
    up in the pauses; the shots should add up to at least the read's length."""
    G._ACC = G.ACCENTS[theme]
    style = style or pick_style(out)
    tmp = tempfile.mkdtemp(prefix='reel-')
    starts, end = montage(shots, f'{tmp}/cut.mp4')
    if callable(lines):                    # lines placed against the cut's own shot starts
        lines = lines(starts, end)
    if lines and isinstance(lines[0], str):
        lines = spread(lines, head_secs + 0.1, end)
    layers = [(head_layer(headline, label, f'{tmp}/head.png', source, date, country,
                          vivid=vivid, theme=theme, seed=sum(map(ord, out)), style=style), 0, head_secs)]
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
                   ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-crf', '16', body], check=True)
    if voice:
        body = _voice_over(body, voice, end, duck_db, f'{tmp}/voiced.mp4')
    sound = sound or G.SOUNDS.get(label, 'neon')
    bed = None                             # clips with no sound rotate the everyday bed; the jingle stays
    if sound == 'neon':
        bed = outro._cached('bed', sonic.rotate(os.path.basename(out)))
    done = outro.append(body, out, sound, bed=bed, accent=G.ACCENTS[theme])
    shutil.rmtree(tmp, ignore_errors=True)  # the temp renders filled the disk on 2 Oct
    return done, starts, end
