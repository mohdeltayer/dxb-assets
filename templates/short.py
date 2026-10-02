"""Digital Lounge TikTok and YouTube Shorts (29 Sep 2026, Mohammad).

The Reels built for Instagram (`ig_ar`) put the clip in a 16:9 strip with
text above and below; on a full-screen phone feed that reads as a slide,
and the Shorts sat at 0 to 8 views. These versions are for TikTok and
YouTube only (X and Instagram keep their cards):

- `clip`: the footage fills the full 9:16 height, the chip and one big
  headline sit low in the frame from the first second, a small brand line
  under them. The facts go in the caption, not on the video.
- `chart`: a sales chart as a Short: a question as the hook for the first
  second or so, then the top 5 as a countdown (`sales_reel`), number one
  last.
- Both end on a 1 second end card (the outro's final frame), not the
  3.6 second animated outro, and sit inside the Reels safe zone.

    short.chart(rows, 'أسبوع 14 إلى 20 سبتمبر 2026', '30 Sep 2026', out,
                hook='من تصدّر مبيعات اليابان؟')
    short.clip('trailer.mp4', out, 'تنطلق Monster Hunter Outlanders في 29 أكتوبر',
               label='رسمي', clip_start=66, clip_seconds=10, audio=True)
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter

import cards as C
import fast_ar as A
import ig_ar as G
import outro
import sales_reel as S

W, H = 1080, 1920
FPS = 30
END = 1.0                   # the end card, after a 0.3 s crossfade
XF = 0.3
HOOK = 1.8                  # the chart's opening question
BOTTOM = 1360               # the headline's last line ends here
BRAND_Y = 1420              # the small brand line, inside SAFE_BOTTOM (1480)


def end_still():
    """The outro card's final frame: mark, name, tag, platforms, handle."""
    p = os.path.join(outro.CACHE, 'short-end.png')
    if not os.path.exists(p):
        os.makedirs(outro.CACHE, exist_ok=True)
        v = outro.card('neon', os.path.join(tempfile.mkdtemp(), 'card.mp4'))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-sseof', '-0.05', '-i', v,
                        '-frames:v', '1', p], check=True)
    return p


def finish(video, out, style='neon'):
    """Crossfade into the 1 second end card. A clip with its own sound keeps
    it, faded out; a silent one gets the flavour's bed under it."""
    d = outro._dur(video)
    total = d - XF + END + XF
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', video,
           '-loop', '1', '-t', f'{END + XF:.2f}', '-i', end_still()]
    v = (f'[0:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[v0];'
         f'[1:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[v1];'
         f'[v0][v1]xfade=transition=fade:duration={XF}:offset={d - XF:.3f}[v]')
    if outro._has_audio(video):
        a = f'[0:a]afade=t=out:st={max(0, d - 0.8):.2f}:d=0.8,apad[a]'
    else:
        bed = style
        if style == 'neon':                     # silent clip: rotate the everyday bed
            import sonic
            bed = sonic.rotate(out)
        cmd += ['-stream_loop', '-1', '-i', outro._cached('bed', bed)]
        a = (f'[2:a]volume=-2dB,afade=t=in:d=0.3,atrim=0:{total:.3f},'
             f'afade=t=out:st={total - 0.9:.2f}:d=0.9[a]')
    subprocess.run(cmd + ['-filter_complex', v + ';' + a, '-map', '[v]', '-map', '[a]',
                          '-t', f'{total:.3f}', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium',
                          '-crf', '20', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000',
                          '-movflags', '+faststart', out], check=True)
    return out


def _brand(im, y=BRAND_Y):
    """Small mark and name, right-aligned in the safe zone."""
    d = ImageDraw.Draw(im)
    s = 64
    mark = Image.open(A.MARK).convert('RGB').resize((s, s), Image.LANCZOS)
    mask = Image.new('L', (s * 4, s * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, s * 4 - 1, s * 4 - 1), fill=255)
    mask = mask.resize((s, s), Image.LANCZOS)
    x = W - G.SAFE_RIGHT
    im.paste(mark, (x - s, y - s // 2), mask)
    d.text((x - s - 16, y), 'ديجيتال لاونج', font=A.F('Bold', 38), fill=A.INK, anchor='rm', **G.AR)


def _overlay(headline, label, path, size=66, step=86):
    """A soft band behind the text only, fading in above the chip and out
    below the brand line, so the footage shows through the rest of the
    frame (29 Sep 2026, Mohammad: the first cut's shade covered about 45%
    of the screen). A dark glow under the letters holds white text on pale
    footage without a solid panel."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    probe = ImageDraw.Draw(Image.new('RGBA', (W, H)))
    h = G._head(probe, headline, 0, label, None, size, step, right=G.SAFE_RIGHT, left=G.SAFE_LEFT)
    top = BOTTOM - h
    a0, a1 = top - 140, BRAND_Y + 70          # band: fade in, hold, fade out
    g = Image.new('L', (1, H), 0)
    for yy in range(H):
        if yy < a0 or yy > a1 + 120:
            v = 0
        elif yy < top:
            v = (yy - a0) / (top - a0)
        elif yy <= a1:
            v = 1
        else:
            v = 1 - (yy - a1) / 120
        g.putpixel((0, yy), int(v * 150))
    shade = Image.new('RGBA', (W, H), A.GROUND + (255,))
    shade.putalpha(g.resize((W, H)))
    im.alpha_composite(shade)
    text = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    G._head(ImageDraw.Draw(text), headline, top, label, None, size, step,
            right=G.SAFE_RIGHT, left=G.SAFE_LEFT)
    _brand(text)
    glow = Image.new('RGBA', (W, H), A.GROUND + (0,))
    glow.putalpha(text.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, v * 2)))
    im.alpha_composite(glow)
    im.alpha_composite(text)
    im.save(path)
    return path


def clip(video, out, headline, label=None, clip_start=0, clip_seconds=8, audio=True,
         focus=0.5, style='neon'):
    """Footage at full height (16:9 cropped to 9:16 around `focus`, 0 left to
    1 right), chip and headline low in the frame, 1 second end card."""
    src = video if os.path.isabs(video) else C.U + video
    tmp = tempfile.mkdtemp(prefix='short-')
    ov = _overlay(headline, label, f'{tmp}/ov.png')
    body = f'{tmp}/body.mp4'
    vf = (f'[0:v]scale=-2:{H},crop={W}:{H}:(iw-{W})*{focus}:0,setsar=1,fps={FPS}[c];'
          f'[c][1:v]overlay=0:0,format=yuv420p[v]')
    cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', str(clip_start), '-t', str(clip_seconds),
           '-i', src, '-i', ov, '-filter_complex', vf, '-map', '[v]']
    cmd += ['-map', '0:a?', '-c:a', 'aac'] if audio else ['-an']
    subprocess.run(cmd + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', body], check=True)
    return finish(body, out, style)


def _hook(question, sub, date, path, source='فاميتسو (Famitsu)', arts=()):
    im = Image.new('RGB', (W, H), A.GROUND)
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-200, 400, W + 200, 1500], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    im = Image.composite(Image.new('RGB', (W, H), A.hx('#2A2870')), im, glow).convert('RGBA')
    d = ImageDraw.Draw(im)
    y = G._head(d, question, 640, 'أرقام', None, 92, 118, right=G.SAFE_RIGHT, left=G.SAFE_LEFT)
    d.text((W - G.SAFE_RIGHT, y + 40), sub, font=A.F('Medium', 40), fill=A.BODY, anchor='rm', **G.AR)
    # the week's box art in a row, right to left in rank order: the answer is in
    # the picture but not named, so the countdown still pays off
    if arts:
        bh, gap = 200, 16
        boxes = []
        for a in arts:
            b = S.trim(a)
            boxes.append(b.resize((max(1, round(b.width * bh / b.height)), bh), Image.LANCZOS))
        while sum(b.width for b in boxes) + gap * (len(boxes) - 1) > W - G.SAFE_LEFT - G.SAFE_RIGHT:
            bh -= 10
            boxes = [b.resize((max(1, round(b.width * bh / b.height)), bh), Image.LANCZOS) for b in boxes]
        x = W - G.SAFE_RIGHT
        for b in boxes:
            im.alpha_composite(b.convert('RGBA'), (x - b.width, int(y + 110)))
            x -= b.width + gap
    G._footer(im, G.SAFE_BOTTOM - G.REEL_FH, source, date, 'cold', 7, right=G.SAFE_RIGHT,
              fh=G.REEL_FH, left=G.SAFE_LEFT, handles=False)
    im.convert('RGB').save(path)
    return path


def chart(rows, week_label, date, out, hook, title='الأكثر مبيعًا في اليابان',
          source='فاميتسو (Famitsu)'):
    """The top 5 as a Short: the hook question, then the countdown, then the
    1 second end card, under the `stats` bed."""
    tmp = tempfile.mkdtemp(prefix='short-chart-')
    seen, arts = set(), []
    for r in sorted(rows, key=lambda r: r['rank'])[:5]:
        if r['art'] not in seen:
            seen.add(r['art'])
            arts.append(r['art'])
    hook_png = _hook(hook, week_label, date, f'{tmp}/hook.png', source, arts)
    hold = S.HOLD
    S.HOLD = 2.6
    try:
        body = S.body(sorted(rows, key=lambda r: r['rank'])[:5], week_label, date,
                      f'{tmp}/body.mp4', title=title, source=source)
    finally:
        S.HOLD = hold
    joined = f'{tmp}/joined.mp4'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-t', f'{HOOK + XF:.2f}',
                    '-i', hook_png, '-i', body, '-filter_complex',
                    f'[0:v]fps={FPS},setsar=1,format=yuv420p[a];[1:v]fps={FPS},setsar=1,format=yuv420p[b];'
                    f'[a][b]xfade=transition=fade:duration={XF}:offset={HOOK:.2f}[v]',
                    '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', joined], check=True)
    return finish(joined, out, 'stats')
