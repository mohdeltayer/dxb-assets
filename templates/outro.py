"""Digital Lounge Reel end card, moving on the jingle (trial, 28 Sep 2026).

Mohammad's idea: the closing jingle is the moment to switch to the
channel's mark and accounts, instead of carrying the handle in every
footer. The clip fades into the card, then the card follows the jingle:
the play mark is there from the fade, each of the four motif notes lights
one platform (X, Instagram, TikTok, YouTube, right to left as Arabic
reads), and the name, tagline and handle come up on the final chord.
Nothing zooms or pans; the only motion is a fade and one soft ring per
platform.

`card(style, out)` renders the card alone (9:16, silent).
`append(video, out, style='neon', bed=None)` adds it to a Reel: the clip
crossfades into the card and the jingle plays on it. A clip with sound
keeps it, faded out before the jingle, and gets nothing else (Mohammad,
28 Sep 2026); a clip with no sound gets the flavour's bed under it
(`bed` overrides the cached one). ig_ar Reels call this by default.
Everything sits in the Reels safe zone (ig_ar.SAFE_*).
"""
import math
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter

import fast_ar as A
import ig_ar as G
import sonic

W, H = 1080, 1920
FPS = 30
CX = (G.SAFE_LEFT + W - G.SAFE_RIGHT) // 2      # 503, the middle of the safe zone
LEAD = 0.3                                       # the crossfade, before the first note
MARK_Y, MARK = 700, 300
NAME_Y, TAG_Y = 930, 1010
ROW_Y, GLYPH, GAP = 1150, 64, 56
HANDLE_Y = 1265
PLATFORMS = ('x', 'instagram', 'tiktok', 'youtube')   # lit right to left


def _ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def _glyph(d, name, x, y, s, c):
    w = max(3, s // 10)
    if name == 'x':
        d.line((x + s * 0.1, y + s * 0.1, x + s * 0.9, y + s * 0.9), fill=c, width=w + 3)
        d.line((x + s * 0.9, y + s * 0.1, x + s * 0.1, y + s * 0.9), fill=c, width=w - 1)
    elif name == 'instagram':
        d.rounded_rectangle([x, y, x + s, y + s], radius=s / 3.2, outline=c, width=w)
        r = s * 0.24
        d.ellipse([x + s / 2 - r, y + s / 2 - r, x + s / 2 + r, y + s / 2 + r], outline=c, width=w)
        d.ellipse([x + s * 0.71, y + s * 0.17, x + s * 0.85, y + s * 0.31], fill=c)
    elif name == 'tiktok':
        # a single note: head, stem, and the flag curling right
        d.ellipse([x + s * 0.12, y + s * 0.56, x + s * 0.5, y + s * 0.94], outline=c, width=w)
        d.line((x + s * 0.5 - w / 2, y + s * 0.75, x + s * 0.5 - w / 2, y + s * 0.06), fill=c, width=w)
        d.arc([x + s * 0.48, y - s * 0.3, x + s * 0.98, y + s * 0.36], 90, 180, fill=c, width=w)
    elif name == 'youtube':
        d.rounded_rectangle([x, y + s * 0.16, x + s, y + s * 0.84], radius=s * 0.2, fill=c)
        d.polygon([(x + s * 0.4, y + s * 0.33), (x + s * 0.4, y + s * 0.67),
                   (x + s * 0.7, y + s * 0.5)], fill=A.GROUND)


def _base():
    """Indigo ground with a soft glow behind the mark, and the mark."""
    im = Image.new('RGB', (W, H), A.GROUND)
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([CX - 420, MARK_Y - 420, CX + 420, MARK_Y + 420], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new('RGB', (W, H), A.hx('#2A2870')), im, glow)
    mark = Image.open(A.MARK).convert('RGB').resize((MARK * 2, MARK * 2), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((MARK, MARK), Image.LANCZOS), mask.resize((MARK, MARK), Image.LANCZOS)
    im.paste(mark, (CX - MARK // 2, MARK_Y - MARK // 2), mask)
    return im


def _layer(draw_fn):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    return lay


def _fade(lay, a):
    if a <= 0:
        return None
    if a < 1:
        lay = lay.copy()
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    return lay


def card(style, out, theme_accent=None):
    notes, chord = sonic.beats(style)
    notes = [LEAD + t for t in notes]
    chord += LEAD
    dur = LEAD + 3.6
    acc = theme_accent or A.AZURE
    base = _base()
    row_w = len(PLATFORMS) * GLYPH + (len(PLATFORMS) - 1) * GAP
    xs = [CX + row_w / 2 - GLYPH - i * (GLYPH + GAP) for i in range(len(PLATFORMS))]
    glyphs = [_layer(lambda d, n=n, x=x: _glyph(d, n, x, ROW_Y - GLYPH / 2, GLYPH, A.INK))
              for n, x in zip(PLATFORMS, xs)]
    name = _layer(lambda d: d.text((CX, NAME_Y), 'ديجيتال لاونج', font=A.F('Bold', 84),
                                   fill=A.INK, anchor='mm', **G.AR))
    tag = _layer(lambda d: d.text((CX, TAG_Y), 'أخبار الألعاب', font=A.F('Medium', 46),
                                  fill=A.BODY, anchor='mm', **G.AR))
    handle = _layer(lambda d: d.text((CX, HANDLE_Y), G.HANDLE, font=A.F('Medium', 42),
                                     fill=A.BODY, anchor='mm'))
    tmp = tempfile.mkdtemp(prefix='outro-')
    n = int(round(dur * FPS))
    for f in range(n):
        t = f / FPS
        im = base.convert('RGBA')
        d = ImageDraw.Draw(im)
        for i, (g, x) in enumerate(zip(glyphs, xs)):
            k = (t - notes[i]) / 0.12
            lay = _fade(g, _ease(k))
            if lay:
                im.alpha_composite(lay)
            ring = (t - notes[i]) / 0.45          # one soft ring as the note sounds
            if 0 <= ring <= 1:
                r = GLYPH * (0.62 + 0.35 * _ease(ring))
                cx, cy = x + GLYPH / 2, ROW_Y
                a = int(200 * (1 - ring))
                d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=acc + (a,), width=3)
        for lay0, t0 in ((name, chord), (tag, chord + 0.12), (handle, chord + 0.24)):
            lay = _fade(lay0, _ease((t - t0) / 0.25))
            if lay:
                im.alpha_composite(lay)
        ring = (t - chord) / 0.7                   # the mark answers the chord once
        if 0 <= ring <= 1:
            r = MARK / 2 + 8 + 40 * _ease(ring)
            d.ellipse([CX - r, MARK_Y - r, CX + r, MARK_Y + r], outline=acc + (int(170 * (1 - ring)),),
                      width=4)
        im.convert('RGB').save(f'{tmp}/{f:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', str(FPS), out],
                   check=True)
    return out


def _dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)


def _has_audio(p):
    return bool(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a',
                                '-show_entries', 'stream=index', '-of', 'csv=p=0', p],
                               capture_output=True, text=True).stdout.strip())


CACHE = os.path.expanduser('~/.cache/digi-sound')


def _cached(kind, style):
    os.makedirs(CACHE, exist_ok=True)
    p = f'{CACHE}/{kind}-{style}.' + ('mp3' if kind == 'jingle' else 'wav')
    if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(sonic.__file__):
        (sonic.jingle if kind == 'jingle' else sonic.bed)(style, p)
    return p


def append(video, out, style='neon', bed=None, jingle=None, accent=None):
    if style not in sonic.FLAVOURS:
        raise ValueError(f'sound is one of {", ".join(sonic.FLAVOURS)}')
    tmp = tempfile.mkdtemp(prefix='outro-')
    end = card(style, f'{tmp}/card.mp4', accent)
    jingle = jingle or _cached('jingle', style)
    d = _dur(video)
    total = d - LEAD + LEAD + 3.6
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', video, '-i', end, '-i', jingle]
    v = (f'[0:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[v0];'
         f'[1:v]fps={FPS},setsar=1,format=yuv420p[v1];'
         f'[v0][v1]xfade=transition=fade:duration={LEAD}:offset={d - LEAD:.3f}[v];')
    j = f'[2:a]adelay={int(d * 1000)}:all=1[j];'
    if _has_audio(video):
        a = f'[0:a]afade=t=out:st={max(0, d - 0.6):.2f}:d=0.6[b];'
    else:
        cmd += ['-stream_loop', '-1', '-i', bed or _cached('bed', style)]
        a = (f'[3:a]volume=-2dB,afade=t=in:d=0.4,atrim=0:{d:.3f},'
             f'afade=t=out:st={max(0, d - 1.0):.2f}:d=1.0[b];')
    fc = v + j + a + f'[b][j]amix=inputs=2:duration=longest:normalize=0,apad[a]'
    subprocess.run(cmd + ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{total:.3f}',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-c:a', 'aac',
                          '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', out], check=True)
    return out
