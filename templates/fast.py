"""DXB-KNIGHT fast-lane card.

For news posted within minutes of breaking. The image or clip is the story
and the post text carries the facts, so the card is the media, full bleed,
plus the footer every full card has: the crest and DXB-KNIGHT left, the
source centre, the date right. No headline and no kicker.

The media frame is 1600 x 900, exactly 16:9 and edge to edge, the shape of
nearly every trailer and screenshot, so the usual source fills it with no
bars. A chip sits bottom left on the media; the gold GULF chip rides beside
it for regional stories.

Pass `video` (a filename, or a list of (filename, start, seconds)) and an
.mp4 `out` for a moving card. Everything else is identical.
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw
import cards as C
import flex

W, MH = 1600, 900            # media frame, full bleed
RULE = 6                     # accent rule under the media
H = MH + RULE + 124          # footer below
M = 40
F = flex.F

#: The agreed fast-lane chips. What happened and how sure we are.
CHIPS = ('breaking', 'just in', 'official', 'report', 'leak', 'rumour',
         'first look', 'out now', 'delayed', 'price')


def _still(path, backing, crop):
    src = Image.open(C.U + path).convert('RGB')
    if crop:
        # Fill the frame. Only when nothing important sits at the edges:
        # a face, a logo or headline text means contain instead.
        k = max(W / src.width, MH / src.height)
        art = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
        l, t = (art.width - W) // 2, (art.height - MH) // 2
        return art.crop((l, t, l + W, t + MH))
    plate = Image.new('RGB', (W, MH), backing)
    k = min(W / src.width, MH / src.height)
    art = src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))), Image.LANCZOS)
    plate.paste(art, ((W - art.width) // 2, (MH - art.height) // 2))
    return plate


def _chips(d, label, gulf, acc, bg):
    x = M
    if label:
        x = flex.filled_label(d, label, M, MH - 34, acc, bg, size=44, anchor='lb')[2] + 16
    if gulf:
        flex.filled_label(d, 'GULF', x, MH - 34, flex.ACCENTS[flex.GULF_CHIP], bg,
                          size=44, anchor='lb')


def _footer(im, bg, acc, source, date):
    d = ImageDraw.Draw(im)
    d.rectangle([0, MH, W, MH + RULE], fill=acc)
    base = MH + RULE + 62
    crest = Image.open(C.CREST).convert('RGBA').resize((56, 56), Image.LANCZOS)
    im.paste(crest, (M, base - 28), crest)
    d = ImageDraw.Draw(im)
    muted = flex.lift(flex.BODY, -0.25, bg)
    d.text((M + 72, base), 'DXB-KNIGHT', font=F(32, 800), fill=flex.INK, anchor='lm')
    d.text((W / 2, base), source.upper(), font=F(30, 600), fill=muted, anchor='mm')
    d.text((W - M, base), date.upper(), font=F(30, 600), fill=muted, anchor='rm')


def fast(media, date, source, out, label=None, gulf=False,
         background='reported', accent='cold', crop=False,
         video=None, clip_start=0, clip_seconds=8, audio=False):
    if label and label.lower() not in CHIPS:
        raise ValueError(f'"{label}" is not a fast-lane chip: {", ".join(CHIPS)}')
    bg = flex.ground(background)[0]
    acc = flex.resolve(accent)
    backing = (0, 0, 0)

    im = Image.new('RGB', (W, H), bg)
    if not video:
        im.paste(_still(media, backing, crop), (0, 0))
        _footer(im, bg, acc, source, date)
        _chips(ImageDraw.Draw(im), label, gulf, acc, bg)
        im.save(out)
        return out

    if not out.lower().endswith('.mp4'):
        raise ValueError('a video card must be written to a .mp4 path')
    _footer(im, bg, acc, source, date)
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _chips(ImageDraw.Draw(top), label, gulf, acc, bg)
    clips = ([(video, clip_start, clip_seconds)] if isinstance(video, str)
             else [tuple(c) for c in video])
    tmp = tempfile.mkdtemp(prefix='dxbfast-')
    base_p, top_p = os.path.join(tmp, 'base.png'), os.path.join(tmp, 'top.png')
    im.save(base_p)
    top.save(top_p)
    paths = [C.U + c[0] for c in clips]
    keep_audio = audio and all(flex._has_audio(p) for p in paths)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-i', base_p]
    for (_, st, dur), p in zip(clips, paths):
        cmd += ['-ss', str(st), '-t', str(dur), '-i', p]
    n = len(clips)
    cmd += ['-loop', '1', '-i', top_p]
    fit = ('increase' if crop else 'decrease')
    post = (f'crop={W}:{MH}' if crop else f'pad={W}:{MH}:(ow-iw)/2:(oh-ih)/2:color=black')
    parts = ''.join(f'[{i + 1}:v]scale={W}:{MH}:force_original_aspect_ratio={fit},'
                    f'{post},setsar=1,fps=30,format=yuv420p[s{i}];' for i in range(n))
    if keep_audio:
        concat = ''.join(f'[s{i}][{i + 1}:a]' for i in range(n)) + f'concat=n={n}:v=1:a=1[vid][aud];'
        amap = ['-map', '[aud]', '-c:a', 'aac', '-b:a', '128k']
    else:
        concat = ''.join(f'[s{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0[vid];'
        amap = ['-an']
    chain = (parts + concat + '[0:v][vid]overlay=0:0:shortest=1[a];'
             f'[a][{n + 1}:v]overlay=0:0:shortest=1,format=yuv420p[out]')
    cmd += ['-filter_complex', chain, '-map', '[out]'] + amap + [
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', '30',
        '-movflags', '+faststart', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffmpeg failed:\n{r.stderr[-1200:]}')
    return out
