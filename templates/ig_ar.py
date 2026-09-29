"""Digital Lounge Instagram card, Arabic (agreed 27 Sep 2026).

The news layout. Top to bottom: the chip and a short headline, the media
at full width and 16:9 (never cropped, the X rule), a distinct panel with
one or two sentences of detail, then the footer laid out as on X: the
play mark and name right with @the_digilounge and the X and Instagram
glyphs under the name, the source centre, the date left.

Stills are 3:4 (1080 x 1440), the size Instagram now shows uncropped in
both the feed and the profile grid. Video is a 9:16 Reel (1080 x 1920):
the same stack inside the middle 1080 x 1350 band the feed shows, a band
for Arabic subtitles between the clip and the panel, and the blurred clip
behind everything instead of flat colour.
"""
import os
import re
import subprocess
import tempfile
import zlib

from PIL import Image, ImageDraw, ImageFilter
import cards as C
import flex
import fast_ar as A

W = 1080
H_STILL = 1440
H_REEL = 1920
BAND = (H_REEL - 1350) // 2      # 285: the part of a Reel the feed shows starts here
MH = 608                         # 16:9 media at full width
RULE = 6
FH = 132                         # footer
M = 64
AR = A.AR
PANEL = A.hx('#1E1D4A')
HANDLE = '@the_digilounge'

#: Instagram accent per theme (Mohammad, 27 Sep 2026: some liberty with
#: colour on Instagram, as on X). The accent carries the rule under the
#: media, the panel edge and the footer's top line; the chip stays azure on
#: every story and the ground stays indigo. None of them is pink.
ACCENTS = {'cold': A.AZURE, 'stylized': A.hx('#A5A3FF'),
           'playful': A.hx('#3DDCB4'), 'spectacle': A.hx('#FFB547')}
_ACC = A.AZURE
SOURCE_MAX = 380

#: Jingle flavour by chip, for Reels (sonic.FLAVOURS).
SOUNDS = {'عاجل': 'breaking', 'متوفر الآن': 'launch', 'متاح الآن': 'launch', 'صدر': 'launch',
          'أرقام': 'stats', 'إحصائيات': 'stats'}


# ---------------------------------------------------------------- text

_LAT_END = re.compile(r'[A-Za-z0-9|:.,!?)\]\-]$')
_LAT_START = re.compile(r'^[A-Za-z0-9(|]')


def _tokens(text):
    """Words, with English names and a number and the word after it kept
    together, so "Hearts of Stone" or "3 ديسمبر" never breaks over a line."""
    out = []
    for w in text.split():
        if out and ((_LAT_END.search(out[-1]) and _LAT_START.match(w)) or out[-1].isdigit()):
            out[-1] += ' ' + w
        else:
            out.append(w)
    return out


def _wrap(d, text, f, width):
    lines, cur = [], ''
    for w in _tokens(text):
        trial = (cur + ' ' + w).strip()
        if cur and d.textlength(trial, font=f, **AR) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + [cur] if cur else lines


# ---------------------------------------------------------------- parts

def _chip(d, text, x_right, y_bottom, fill, ink, size=38):
    f = A.F('Bold', size)
    w = d.textlength(text, font=f, **AR)
    bw, bh = w + 48, int(size * 1.5)
    x0, y0 = x_right - bw, y_bottom - bh
    d.rounded_rectangle([x0, y0, x_right, y_bottom], radius=10, fill=fill)
    d.text((x_right - 24, y0 + bh / 2 + 2), text, font=f, fill=ink, anchor='rm', **AR)
    return x0


def _head(d, text, y, label, country, size, step, right=M, left=M):
    """Chip row then the headline; returns the y under the last line."""
    x = W - right
    if label:
        x = _chip(d, label, x, y + 57, A.AZURE, A.GROUND) - 14
    if country:
        _chip(d, country, x, y + 57, A.INDIGO, A.INK)
    if label or country:
        y += 57 + 22
    f = A.F('Bold', size)
    lines = _wrap(d, text, f, W - left - right)
    if len(lines) > 3:
        raise ValueError(f'headline runs to {len(lines)} lines; keep it to 3')
    for line in lines:
        d.text((W - right, y + step / 2), line, font=f, fill=A.INK, anchor='rm', **AR)
        y += step
    return y


def _panel(d, text, y, size, step, pad=34, right=M, left=M):
    """The detail panel: lighter indigo, an azure edge on the reading side."""
    f = A.F('Medium', size)
    lines = _wrap(d, text, f, W - left - right - 2 * pad - 10)
    h = pad * 2 + step * len(lines) - (step - size)
    d.rounded_rectangle([left, y, W - right, y + h], radius=18, fill=PANEL)
    d.rounded_rectangle([W - right - 8, y + 18, W - right, y + h - 18], radius=4, fill=_ACC)
    ty = y + pad
    for line in lines:
        d.text((W - right - pad - 12, ty + size / 2 + 4), line, font=f, fill=A.INK,
               anchor='rm', **AR)
        ty += step
    return y + h


def _icon_x(d, x, y, s, c):
    d.line((x, y, x + s, y + s), fill=c, width=4)
    d.line((x + s, y, x, y + s), fill=c, width=2)


def _icon_ig(d, x, y, s, c):
    w = max(2, s // 9)
    d.rounded_rectangle([x, y, x + s, y + s], radius=s / 3.2, outline=c, width=w)
    r = s * 0.24
    cx, cy = x + s / 2, y + s / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    d.ellipse([x + s * 0.72, y + s * 0.18, x + s * 0.84, y + s * 0.30], fill=c)


def _footer(im, y, source, date, theme, seed, right=M, fh=FH, left=M, handles=True):
    """As on X, right to left: mark and name, source centre, date left.
    The handle, shared by the X and Instagram accounts, sits under the name;
    handles=False drops it for a Reel that ends on the outro card, which
    carries the handle and every platform instead."""
    im.paste(A._waves(W, fh, theme, seed), (0, y))
    d = ImageDraw.Draw(im)
    d.rectangle([0, y, W, y + 3], fill=_ACC)
    mid = y + fh // 2
    size = 62
    mark = Image.open(A.MARK).convert('RGB').resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new('L', mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.width - 1, mark.height - 1), fill=255)
    mark, mask = mark.resize((size, size), Image.LANCZOS), mask.resize((size, size), Image.LANCZOS)
    im.paste(mark, (W - right - size, mid - size // 2), mask)
    d = ImageDraw.Draw(im)
    xr = W - right - size - 16
    d.text((xr, mid - 16 if handles else mid), 'ديجيتال لاونج', font=A.F('Bold', 34),
           fill=A.INK, anchor='rm', **AR)
    if handles:
        f = A.F('Medium', 24)
        d.text((xr, mid + 24), HANDLE, font=f, fill=A.BODY, anchor='rm')
        s = 20
        ix = xr - d.textlength(HANDLE, font=f) - 12 - s
        _icon_ig(d, ix, mid + 24 - s / 2, s, A.BODY)
        _icon_x(d, ix - s - 10, mid + 24 - s / 2 + 1, s - 2, A.BODY)
    f = A.F('Medium', 28)
    if d.textlength(source, font=f, **AR) > SOURCE_MAX and '(' in source:
        source = source.split('(')[0].strip()      # no room for both forms
    d.text(((left + W - right) / 2 - 40, mid), source, font=f, fill=A.BODY, anchor='mm', **AR)
    d.text((left, mid), A.arabic_date(date), font=f, fill=A.BODY, anchor='lm', **AR)


def _media(path):
    src = Image.open(C.U + path).convert('RGB')
    k = max(W / src.width, MH / src.height)
    art = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
    l, t = (art.width - W) // 2, (art.height - MH) // 2
    return art.crop((l, t, l + W, t + MH))


def _check(label, country, theme):
    if theme not in A.THEMES:
        raise ValueError(f'theme is one of {", ".join(A.THEMES)}')
    if label and label not in A.PICKS + A.ALTERNATIVES:
        raise ValueError(f'"{label}" is not an Arabic fast chip: {"، ".join(A.PICKS)}')
    if country and country not in A.COUNTRIES:
        raise ValueError(f'"{country}" is not a country chip: {"، ".join(A.COUNTRIES)}')


# ---------------------------------------------------------------- entry

def ig_ar(media, date, source, out, headline, summary, label=None, country=None,
          theme='cold', video=None, clip_start=0, clip_seconds=8, audio=False,
          subtitles=(), src_crop=None, accent=None, handles=None, outro=True, sound=None,
          cover=0.0, bg_dim=0.72):
    """`headline`: the hook, one or two lines. `summary`: one or two
    sentences of detail for the panel. `media` is a 16:9 still (a file in
    uploads); with `video` instead, a 9:16 Reel is written to an .mp4 `out`.
    `subtitles`: [(start, end, arabic)]. `src_crop` ('w:h:x:y' from
    cropdetect) trims a trailer's own letterbox first. The accent follows
    `theme` (ACCENTS); `accent` overrides it with a colour.
    Every Reel ends on the outro card with the jingle (Mohammad, 28 Sep
    2026), so its footer drops the handle; stills keep it. `sound` picks
    the jingle flavour (sonic.FLAVOURS), by default from the chip: عاجل
    breaking, متوفر الآن launch, أرقام stats, anything else neon; occasion
    flavours (ramadan, eid, halloween, christmas) are passed by hand. A
    trailer kept with `audio=True` plays its own sound and then only the
    jingle; a clip with no sound gets the flavour's bed under it.
    `cover` (seconds, trial 29 Sep 2026) opens the Reel on the clip full
    screen with the chip and headline, then fades into the card: Instagram
    shows the first frame as the grid tile, and an all-indigo first frame
    made the grid a purple wall. `bg_dim` is how much indigo sits over the
    blurred clip behind the card (0.72 was the only value until then)."""
    _check(label, country, theme)
    global _ACC
    _ACC = ACCENTS[theme] if accent is None else accent
    seed = zlib.crc32(os.path.basename(out).encode())
    if video:
        if not outro:
            return _reel(video, date, source, out, headline, summary, label, country, theme,
                         seed, clip_start, clip_seconds, audio, subtitles, src_crop,
                         True if handles is None else handles, cover, bg_dim)
        import outro as O
        body = os.path.join(tempfile.mkdtemp(prefix='dlreel-'), 'body.mp4')
        _reel(video, date, source, body, headline, summary, label, country, theme, seed,
              clip_start, clip_seconds, audio, subtitles, src_crop,
              False if handles is None else handles, cover, bg_dim)
        return O.append(body, out, sound or SOUNDS.get(label, 'neon'), accent=_ACC)
    im = Image.new('RGB', (W, H_STILL), A.GROUND)
    d = ImageDraw.Draw(im)
    y = _head(d, headline, 70, label, country, 64, 88) + 30
    im.paste(_media(media), (0, y))
    d = ImageDraw.Draw(im)
    d.rectangle([0, y + MH, W, y + MH + RULE], fill=_ACC)
    end = _panel(d, summary, y + MH + RULE + 40, 37, 58)
    if end > H_STILL - FH - 16:
        raise ValueError('headline and summary do not fit; shorten one of them')
    _footer(im, H_STILL - FH, source, date, theme, seed,
            handles=True if handles is None else handles)
    im.save(out)
    return out


#: Reels safe zone (27 Sep 2026). Instagram's Reels UI puts a column of
#: buttons down the right and the account name and caption along the
#: bottom; TikTok does the same. The feed also cuts a Reel to its middle
#: 4:5. Text, chips and the footer stay inside all three; only the clip
#: runs full width.
SAFE_TOP = BAND                 # 285: where the feed's 4:5 cut starts
SAFE_BOTTOM = 1480              # above the name and caption
SAFE_RIGHT = 170                # clear of the like, comment, share column
SAFE_LEFT = 96                  # tall phones trim each side of a Reel or Short
REEL_FH = 112


def _subtitle_png(text, path, y):
    im = Image.new('RGBA', (W, H_REEL), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = (SAFE_LEFT + W - SAFE_RIGHT) / 2
    room = W - SAFE_LEFT - SAFE_RIGHT - 40
    size = 46                         # shrink to hold one line before wrapping
    while size > 36 and d.textlength(text, font=A.F('Bold', size), **AR) > room:
        size -= 2
    f = A.F('Bold', size)
    for line in _wrap(d, text, f, room):
        w = d.textlength(line, font=f, **AR)
        d.rounded_rectangle([cx - w / 2 - 18, y, cx + w / 2 + 18, y + 64], radius=10,
                            fill=A.GROUND + (230,))
        d.text((cx, y + 32), line, font=f, fill=A.INK, anchor='mm', **AR)
        y += 70
    im.save(path)
    return path


def _cover_png(headline, label, country, path):
    """The opening frame: a dark fade up from the bottom, then the chip and
    headline, placed inside the 3:4 middle Instagram shows on the grid
    (y 240 to 1680) and inside the Reels safe zone."""
    im = Image.new('RGBA', (W, H_REEL), (0, 0, 0, 0))
    g = Image.new('L', (1, H_REEL), 0)
    for yy in range(H_REEL):
        g.putpixel((0, yy), int(max(0, min(1, (yy - 820) / 520)) * 225))
    shade = Image.new('RGBA', (W, H_REEL), A.GROUND + (255,))
    shade.putalpha(g.resize((W, H_REEL)))
    im.alpha_composite(shade)
    d = ImageDraw.Draw(im)
    _head(d, headline, 1180, label, country, 54, 70, right=SAFE_RIGHT, left=SAFE_LEFT)
    im.save(path)
    return path


def _reel(video, date, source, out, headline, summary, label, country, theme, seed,
          clip_start, clip_seconds, audio, subtitles, src_crop, handles=True, cover=0.0,
          bg_dim=0.72):
    if not out.lower().endswith('.mp4'):
        raise ValueError('a Reel must be written to a .mp4 path')
    if src_crop:
        cw, ch = (int(v) for v in src_crop.split(':')[:2])
    else:
        cw, ch = 16, 9
    vid_h = W * ch // cw // 2 * 2
    # The overlay: everything but the clip and the subtitles, on transparency.
    top = Image.new('RGBA', (W, H_REEL), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    vid_y = _head(d, headline, SAFE_TOP + 10, label, country, 46, 62, right=SAFE_RIGHT,
                  left=SAFE_LEFT) + 18
    rule_y = vid_y + vid_h
    d.rectangle([0, rule_y, W, rule_y + RULE], fill=_ACC)
    sub_y = rule_y + RULE + 14
    panel_y = sub_y + 70 + 14 if subtitles else rule_y + RULE + 20   # one subtitle line
    end = _panel(d, summary, panel_y, 33, 48, pad=26, right=SAFE_RIGHT, left=SAFE_LEFT)
    foot_y = SAFE_BOTTOM - REEL_FH
    if end > foot_y - 8:
        raise ValueError(f'headline and summary do not fit the Reel safe zone (panel ends {end}, '
                         f'footer at {foot_y}); keep the headline to two lines and the summary to two')
    foot = Image.new('RGB', (W, foot_y + REEL_FH), A.GROUND)
    _footer(foot, foot_y, source, date, theme, seed, right=SAFE_RIGHT, fh=REEL_FH,
            left=SAFE_LEFT, handles=handles)
    top.paste(foot.crop((0, foot_y, W, foot_y + REEL_FH)), (0, foot_y))
    tmp = tempfile.mkdtemp(prefix='dlreel-')
    top_p = os.path.join(tmp, 'top.png')
    top.save(top_p)
    subs = [(_subtitle_png(t, os.path.join(tmp, f'sub{i}.png'), sub_y), st, en)
            for i, (st, en, t) in enumerate(subtitles)]
    cov_p = _cover_png(headline, label, country, os.path.join(tmp, 'cover.png')) if cover else None
    p = C.U + video
    keep_audio = audio and flex._has_audio(p)
    g = '0x%02X%02X%02X' % A.GROUND
    pre = f'crop={src_crop},' if src_crop else ''
    cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', str(clip_start), '-t', str(clip_seconds),
           '-i', p, '-loop', '1', '-i', top_p]
    for png, _, _ in subs:
        cmd += ['-loop', '1', '-i', png]
    if cov_p:
        cmd += ['-loop', '1', '-i', cov_p]
    chain = (f'[0:v]{pre}fps=30,split=3[a][b][f];' if cov_p else f'[0:v]{pre}fps=30,split[a][b];')
    chain += (
             f'[a]scale={W}:{H_REEL}:force_original_aspect_ratio=increase,'
             f'crop={W}:{H_REEL},boxblur=40:2,setsar=1,format=rgba[bl];'
             f'color=c={g}@{bg_dim}:s={W}x{H_REEL}:r=30,format=rgba[dim];'
             f'[bl][dim]overlay=0:0:shortest=1[bg];'
             f'[b]scale={W}:{vid_h},setsar=1[v];'
             f'[bg][v]overlay=0:{vid_y}:shortest=1[c1];'
             f'[c1][1:v]overlay=0:0:shortest=1[s0];')
    for k, (_, st, en) in enumerate(subs):
        chain += (f"[s{k}][{2 + k}:v]overlay=0:0:shortest=1:"
                  f"enable='between(t,{st},{en})'[s{k + 1}];")
    last = f's{len(subs)}'
    if cov_p:
        ci = 2 + len(subs)
        chain += (f'[f]scale={W}:{H_REEL}:force_original_aspect_ratio=increase,crop={W}:{H_REEL},'
                  f'setsar=1,format=rgba[fb0];[fb0][{ci}:v]overlay=0:0:shortest=1,format=rgba,'
                  f'fade=t=out:st={cover}:d=0.35:alpha=1[fb];[{last}][fb]overlay=0:0:shortest=1[cv];')
        last = 'cv'
    chain += f'[{last}]format=yuv420p[out]'
    amap = (['-map', '0:a', '-c:a', 'aac', '-b:a', '128k'] if keep_audio else ['-an'])
    cmd += ['-filter_complex', chain, '-map', '[out]'] + amap + [
        '-t', str(clip_seconds), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
        '-r', '30', '-movflags', '+faststart', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffmpeg failed:\n{r.stderr[-1500:]}')
    return out
