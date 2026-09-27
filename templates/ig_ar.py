"""Digital Lounge Instagram card, Arabic (agreed 27 Sep 2026: option B).

Stills are 4:5 (1080 x 1350): the picture contained, never cropped, on a
blurred and darkened copy of itself, the chip bottom right on the media,
an azure rule, and the wave footer (play mark and name right, date left,
source beneath). No headline, as on the X fast card.

Video is a 9:16 Reel (1080 x 1920) built so its middle 1080 x 1350 is the
same card: the feed shows a Reel cut to 4:5, so everything that matters
sits in that band. Above it the blurred clip runs on; below it the wave
footer runs on, under Instagram's own caption and buttons.
"""
import os
import subprocess
import tempfile
import zlib

from PIL import Image, ImageDraw, ImageFilter
import cards as C
import flex
import fast_ar as A

W = 1080
H4 = 1350                    # 4:5 still
H9 = 1920                    # 9:16 Reel
BAND = (H9 - H4) // 2        # 285: where the 4:5 band starts in the Reel
RULE = 6
FOOT = 176
M = 44
AR = A.AR
DIM = 0.55                   # how far the blurred fill sinks into the ground


def _cover(src, w, h):
    k = max(w / src.width, h / src.height)
    art = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
    l, t = (art.width - w) // 2, (art.height - h) // 2
    return art.crop((l, t, l + w, t + h))


def _contain(src, w, h):
    k = min(w / src.width, h / src.height)
    return src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))), Image.LANCZOS)


def _chip(d, text, x_right, y_bottom, fill, ink, size=40):
    f = A.F('Bold', size)
    w = d.textlength(text, font=f, **AR)
    bw, bh = w + 48, int(size * 1.5)
    x0, y0 = x_right - bw, y_bottom - bh
    d.rounded_rectangle([x0, y0, x_right, y_bottom], radius=10, fill=fill)
    d.text((x_right - 24, y0 + bh / 2 + 2), text, font=f, fill=ink, anchor='rm', **AR)
    return x0


def _chips(d, label, country, y_bottom):
    x = W - M
    if label:
        x = _chip(d, label, x, y_bottom, A.AZURE, A.GROUND) - 14
    if country:
        _chip(d, country, x, y_bottom, A.INDIGO, A.INK)


def _footer(im, top, height, source, date, theme, seed):
    """Waves over `height` from `top`; the type sits in its first FOOT px."""
    im.paste(A._waves(W, height, theme, seed), (0, top))
    d = ImageDraw.Draw(im)
    d.rectangle([0, top - RULE, W, top], fill=A.AZURE)
    row = top + 58
    size = 58
    mark = Image.open(A.MARK).convert('RGB').resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((size, size), Image.LANCZOS), mask.resize((size, size), Image.LANCZOS)
    im.paste(mark, (W - M - size, row - size // 2), mask)
    d = ImageDraw.Draw(im)
    d.text((W - M - size - 16, row), 'ديجيتال لاونج', font=A.F('Bold', 40),
           fill=A.INK, anchor='rm', **AR)
    d.text((M, row), A.arabic_date(date), font=A.F('Medium', 32), fill=A.BODY,
           anchor='lm', **AR)
    f = A.F('Medium', 30)
    if d.textlength(source, font=f, **AR) > W - 2 * M and '(' in source:
        source = source.split('(')[0].strip()
    d.text((W - M, row + 70), source, font=f, fill=A.BODY, anchor='rm', **AR)


def _check(label, country, theme):
    if theme not in A.THEMES:
        raise ValueError(f'theme is one of {", ".join(A.THEMES)}')
    if label and label not in A.PICKS + A.ALTERNATIVES:
        raise ValueError(f'"{label}" is not an Arabic fast chip: {"، ".join(A.PICKS)}')
    if country and country not in A.COUNTRIES:
        raise ValueError(f'"{country}" is not a country chip: {"، ".join(A.COUNTRIES)}')


def ig_ar(media, date, source, out, label=None, country=None, theme='cold',
          video=None, clip_start=0, clip_seconds=8, audio=False, subtitles=(),
          src_crop=None):
    """A 4:5 still from `media`, or with `video` (a file in uploads) a 9:16
    Reel written to an .mp4 `out`. `subtitles`: [(start, end, arabic)].
    `src_crop` ('w:h:x:y', from ffmpeg's cropdetect) trims a trailer's own
    letterbox before the clip is set in the frame."""
    _check(label, country, theme)
    seed = zlib.crc32(os.path.basename(out).encode())
    if video:
        return _reel(video, date, source, out, label, country, theme, seed,
                     clip_start, clip_seconds, audio, subtitles, src_crop)
    box = H4 - FOOT - RULE
    src = Image.open(C.U + media).convert('RGB')
    back = _cover(src, W, box).filter(ImageFilter.GaussianBlur(36))
    back = Image.blend(back, Image.new('RGB', back.size, A.GROUND), DIM)
    art = _contain(src, W, box)
    back.paste(art, ((W - art.width) // 2, (box - art.height) // 2))
    im = Image.new('RGB', (W, H4), A.GROUND)
    im.paste(back, (0, 0))
    _chips(ImageDraw.Draw(im), label, country, box - 34)
    _footer(im, box + RULE, FOOT, source, date, theme, seed)
    im.save(out)
    return out


def _subtitle_png(text, path, y_bottom):
    im = Image.new('RGBA', (W, H9), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = A.F('Bold', 46)
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if cur and d.textlength(trial, font=f, **AR) > W - 2 * M - 40:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    lines += [cur] if cur else []
    step = 66
    y = y_bottom - step * len(lines)
    for line in lines:
        w = d.textlength(line, font=f, **AR)
        d.rounded_rectangle([(W - w) / 2 - 20, y - 4, (W + w) / 2 + 20, y + step - 2],
                            radius=10, fill=A.GROUND + (205,))
        d.text((W / 2, y + step / 2 - 2), line, font=f, fill=A.INK, anchor='mm', **AR)
        y += step
    im.save(path)
    return path


def _reel(video, date, source, out, label, country, theme, seed,
          clip_start, clip_seconds, audio, subtitles, src_crop=None):
    if not out.lower().endswith('.mp4'):
        raise ValueError('a Reel must be written to a .mp4 path')
    box_bottom = BAND + H4 - FOOT - RULE          # 1453: the media area ends
    if src_crop:
        cw, ch = (int(v) for v in src_crop.split(':')[:2])
    else:
        cw, ch = 16, 9
    vid_h = W * ch // cw // 2 * 2                 # the clip, contained
    vid_y = BAND + (H4 - FOOT - RULE - vid_h) // 2
    tmp = tempfile.mkdtemp(prefix='dlreel-')
    top = Image.new('RGBA', (W, H9), (0, 0, 0, 0))
    _footer(top, box_bottom + RULE, H9 - box_bottom - RULE, source, date, theme, seed)
    _chips(ImageDraw.Draw(top), label, country, box_bottom - 34)
    top_p = os.path.join(tmp, 'top.png')
    top.save(top_p)
    subs = [(_subtitle_png(t, os.path.join(tmp, f'sub{i}.png'), box_bottom - 118), st, en)
            for i, (st, en, t) in enumerate(subtitles)]
    p = C.U + video
    keep_audio = audio and flex._has_audio(p)
    g = '0x%02X%02X%02X' % A.GROUND
    cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', str(clip_start), '-t', str(clip_seconds),
           '-i', p, '-loop', '1', '-i', top_p]
    for png, _, _ in subs:
        cmd += ['-loop', '1', '-i', png]
    pre = f'crop={src_crop},' if src_crop else ''
    chain = (f'[0:v]{pre}fps=30,split[a][b];'
             f'[a]scale={W}:{box_bottom}:force_original_aspect_ratio=increase,'
             f'crop={W}:{box_bottom},boxblur=40:2,setsar=1,format=rgba[bl];'
             f'color=c={g}@{DIM}:s={W}x{box_bottom}:r=30,format=rgba[dim];'
             f'[bl][dim]overlay=0:0:shortest=1[bg];'
             f'[b]scale={W}:{vid_h}:force_original_aspect_ratio=decrease,'
             f'pad={W}:{vid_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[v];'
             f'color=c={g}:s={W}x{H9}:r=30[cv];'
             f'[cv][bg]overlay=0:0:shortest=1[c1];'
             f'[c1][v]overlay=0:{vid_y}:shortest=1[c2];'
             f'[c2][1:v]overlay=0:0:shortest=1[s0];')
    for k, (_, st, en) in enumerate(subs):
        chain += (f"[s{k}][{2 + k}:v]overlay=0:0:shortest=1:"
                  f"enable='between(t,{st},{en})'[s{k + 1}];")
    chain += f'[s{len(subs)}]format=yuv420p[out]'
    amap = (['-map', '0:a', '-c:a', 'aac', '-b:a', '128k'] if keep_audio else ['-an'])
    cmd += ['-filter_complex', chain, '-map', '[out]'] + amap + [
        '-t', str(clip_seconds), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
        '-r', '30', '-movflags', '+faststart', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffmpeg failed:\n{r.stderr[-1500:]}')
    return out
