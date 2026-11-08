# «الطريق إلى GTA VI» series intro (Mohammad, 8 Nov 2026, studio request studio-gta-vi-series): about 3 s, the same on
# every episode, in the spectacle theme (azure to amber; no pink in our colours, Rockstar's own sunset footage may be
# pink and stays). Fixed parts: the series chip «الحلقة N», the title, «باقي N يومًا» counted from the launch date
# verified on Rockstar's GTA VI page, Rockstar's own picture with its credit, and our own sound (sonic.py flavour
# "gtavi", nothing licensed). Everything after the intro is the episode's own material; the outro is every Reel's.
#
# Launch date (the countdown's only source, never memory): Rockstar Games, rockstargames.com/VI, read 8 Nov 2026 03:40Z:
# "Coming November 19, 2026"; Take-Two, results for fiscal Q1 2027 (7 Aug 2026): "Grand Theft Auto VI | PS5, Xbox
# Series X|S | November 19, 2026". If either changes, LAUNCH changes here first and check() refuses old counts.
#
# Picture: Rockstar's launch trailer (15 Oct 2026, IGN's 3840 copy), 25.15 to 27.18 s: the Vice City skyline at
# sunset after the logo has gone, then Lucia and Jason in the convertible, slowed to 0.75x with motion-compensated
# frames (templates/assets/gtavi/intro-band.mp4, 1080x608, 2.63 s); the backdrop is the same skyline, blurred and
# dimmed into the indigo ground (intro-back.jpg). Both are committed, so the intro renders wherever the Dubai font is.
#
#     python3 gta_intro.py <days> [episode] [out.mp4]    # the intro alone (needs the Dubai font)
#     gta_intro.intro(days, out, episode=N, final=True)  # encoded like outro.append's body, for the concat join
#     gta_intro.join(intro_mp4, reel_mp4, out)           # intro + finished Reel, concat demuxer, no re-encode
#     job: "intro": {"series": "gtavi", "days": N, "episode": E, "date": "YYYY-MM-DD"}   (date = the post's Dubai date)
import os, sys, subprocess, shutil, tempfile, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
import fast_ar as A

ASSETS = os.path.join(HERE, 'assets', 'gtavi')
BAND = os.path.join(ASSETS, 'intro-band.mp4')
BACK = os.path.join(ASSETS, 'intro-back.jpg')
LAUNCH = datetime.date(2026, 11, 19)          # Rockstar's GTA VI page and Take-Two's Q1 FY27 release (see above)
SERIES = 'الطريق إلى GTA VI'
CREDIT = 'المصدر: روكستار غيمز (Rockstar Games)'
SECS = 2.9                                     # the band is 2.63 s; its last frame holds under the chord's tail
W, H = 1080, 1920
AZURE, AMBER = A.THEMES['spectacle'][0], A.THEMES['spectacle'][1]
INK, BODY, GROUND = (244, 243, 255), (201, 200, 230), (20, 19, 50)
BAND_Y = 700                                   # band 700 to 1308
SAFE_L, SAFE_R = 96, 910                       # the Reels safe zone (x 96 to 910, y 285 to 1480)


def days_line(n):
    """Arabic count with the right agreement; 0 means launch day."""
    if n <= 0: return 'متوفرة الآن'
    if n == 1: return 'باقي يوم واحد'
    if n == 2: return 'باقي يومان'
    if n <= 10: return f'باقي {n} أيام'
    return f'باقي {n} يومًا'


def days_for(date):
    """Days left to LAUNCH from a post's Dubai date (YYYY-MM-DD or a date)."""
    d = date if isinstance(date, datetime.date) else datetime.date.fromisoformat(str(date))
    return (LAUNCH - d).days


def _gradient_text(text, font, y, anchor='ma'):
    """Text filled azure (right, where an Arabic line starts) to amber (left), on a transparent layer."""
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).text((W // 2, y), text, font=font, fill=255, anchor=anchor, **A.AR)
    box = mask.getbbox() or (0, 0, W, H)
    grad = Image.new('RGBA', (W, H))
    g = ImageDraw.Draw(grad)
    x0, x1 = box[0], max(box[2], box[0] + 1)
    for x in range(W):
        t = min(1.0, max(0.0, (x1 - x) / (x1 - x0)))          # 0 at the right edge (azure), 1 at the left (amber)
        c = tuple(int(AZURE[i] + (AMBER[i] - AZURE[i]) * t) for i in range(3))
        g.line([(x, 0), (x, H)], fill=c + (255,))
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out, box


def layers(n, d, episode=1):
    """The intro's still layers: shade, chip, title (gradient, with a soft glow), days line, credit, rules."""
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = Image.new('L', (1, H), 0)
    for y in range(H):
        t = max(0.0, 1 - y / 760); g.putpixel((0, y), int(170 * t ** 1.2))
    blk = Image.new('RGBA', (W, H), GROUND + (255,)); blk.putalpha(g.resize((W, H))); shade.alpha_composite(blk)
    shade.save(f'{d}/g-shade.png')

    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
    fc = A.F('Bold', 50); chip = f'الحلقة {episode}'
    tw = dt.textlength(chip, font=fc, **A.AR); ch = 75
    x1 = SAFE_R; x0 = int(x1 - tw - 44); y0 = 345                  # the chip row, clear of the grid corner (x 940+)
    dt.rounded_rectangle((x0, y0, x1, y0 + ch), radius=14, fill=AMBER + (255,))
    dt.text(((x0 + x1) // 2, y0 + ch // 2 + 2), chip, font=fc, fill=GROUND, anchor='mm', **A.AR)
    for size in range(104, 71, -4):                                  # the largest title that fits the safe width
        title, box = _gradient_text(SERIES, A.F('Bold', size), 448)
        if box[0] >= SAFE_L - 16 and box[2] <= W - 76:
            break
    else:
        raise ValueError(f'gta_intro: the title does not fit even at 72 px ({box})')
    glow = title.filter(ImageFilter.GaussianBlur(16)); top.alpha_composite(glow); top.alpha_composite(title)
    top.save(f'{d}/g-title.png')

    c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
    dc.text((W // 2, 590), days_line(n), font=A.F('Medium', 68), fill=INK, anchor='ma', **A.AR)
    c.save(f'{d}/g-days.png')

    r = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(r)
    for y in (BAND_Y - 6, BAND_Y + 608 + 2):                       # thin azure-to-amber rules on the band's edges
        for x in range(W):
            t = x / (W - 1)
            dr.point((x, y), fill=tuple(int(AMBER[i] + (AZURE[i] - AMBER[i]) * t) for i in range(3)) + (230,))
            dr.point((x, y + 1), fill=tuple(int(AMBER[i] + (AZURE[i] - AMBER[i]) * t) for i in range(3)) + (230,))
    dr.text((SAFE_R, BAND_Y + 608 + 30), CREDIT, font=A.F('Medium', 40), fill=BODY, anchor='ra', **A.AR)
    r.save(f'{d}/g-credit.png')


def band_mask(d):
    m = Image.new('L', (1080, 608), 255); dm = ImageDraw.Draw(m)
    for i in range(24):                                             # trims the trailer's own thin bars, soft edge
        v = int(255 * (i / 24) ** 1.4); dm.line([(0, i), (1080, i)], fill=v); dm.line([(0, 607 - i), (1080, 607 - i)], fill=v)
    m.save(f'{d}/g-band.png')


def sting(d):
    """Our own sound: the gtavi flavour's jingle (motif and chord), cut to the intro with a short fade."""
    import sonic
    path = f'{d}/g-sting.wav'
    sonic.jingle('gtavi', path)
    return path


def intro(n, out, episode=1, d=None, final=False):
    """The intro with «days_line(n)» and «الحلقة episode». `final=True` encodes it as outro.append encodes a Reel's body
    (reel.FINAL_ENC, high profile, the same track timescale, outro.FINAL_A), so join() needs no re-encode."""
    own = d is None
    d = d or tempfile.mkdtemp(prefix='gta-intro-')
    try:
        for f in (BAND, BACK):
            if not os.path.exists(f):
                raise FileNotFoundError(f'gta_intro: {f} is missing; the intro uses only its committed Rockstar picture')
        layers(n, d, episode); band_mask(d); music = sting(d)
        fc = (f"[0:v]fps=30,tpad=stop_mode=clone:stop_duration=0.5,format=rgba[sv];[6:v]format=gray[bm];[sv][bm]alphamerge[sb];"
              f"[5:v]format=rgba[bk];[bk][sb]overlay=0:{BAND_Y}[v0];[v0][1:v]overlay=0:0[v1];"
              "[2:v]format=rgba[ti];[3:v]format=rgba[da];[7:v]format=rgba[cr];"                     # all on frame 0: it is the grid tile
              "[v1][ti]overlay=0:0[v2];[v2][da]overlay=0:0[v3];[v3][cr]overlay=0:0,fps=30,format=yuv420p[v]")
        af = f'aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={SECS - 0.35}:d=0.35'
        if final:
            import reel, outro
            enc = ['-c:v', 'libx264'] + reel.FINAL_ENC + ['-pix_fmt', 'yuv420p', '-profile:v', 'high', '-video_track_timescale', '15360'] + outro.FINAL_A
        else:
            enc = ['-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000']
        L = ['-loop', '1', '-t', str(SECS), '-i']
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', BAND] + L + [f'{d}/g-shade.png'] + L + [f'{d}/g-title.png']
                       + L + [f'{d}/g-days.png'] + ['-t', str(SECS), '-i', music] + L + [BACK] + L + [f'{d}/g-band.png']
                       + L + [f'{d}/g-credit.png']
                       + ['-filter_complex', fc, '-map', '[v]', '-map', '4:a', '-af', af] + enc + ['-t', str(SECS), out], check=True)
        return out
    finally:
        if own:
            shutil.rmtree(d, ignore_errors=True)


def join(intro_mp4, reel_mp4, out):
    """The intro ahead of a finished Reel (end card included). First the concat demuxer with stream copy; if the joined
    file does not decode clean (the 8 Nov episode 1 render on dxb-render-1 failed the output decode check with "non
    monotonically increasing dts" after the stream-copy join), the two are joined again with the concat filter at the
    Reel's final encode, so the decode check never sees a broken seam."""
    import decodecheck
    tmp = tempfile.mkdtemp(prefix='gta-join-')
    try:
        lst = f'{tmp}/list.txt'
        open(lst, 'w').write(f"file '{os.path.abspath(intro_mp4)}'\nfile '{os.path.abspath(reel_mp4)}'\n")
        part = f'{tmp}/joined.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                        '-movflags', '+faststart', part], check=True)
        errs = decodecheck.decode_errors(part)
        if errs:
            print(f'gta_intro: stream-copy join did not decode clean ({errs[0][:120]}); joining again with one encode',
                  flush=True)
            reencode(intro_mp4, reel_mp4, part)
            errs = decodecheck.decode_errors(part)
            if errs:
                raise ValueError(f'gta_intro: joined Reel still has decode errors: {errs[0]}')
            JOINED['mode'] = 'encode'
        else:
            JOINED['mode'] = 'copy'
        shutil.move(part, out)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


JOINED = {'mode': None}                                             # how the last join was made, for the render log


def reencode(intro_mp4, reel_mp4, out):
    """Concat filter, video and audio, at the Reel's final encode (reel.FINAL_ENC, outro.FINAL_A)."""
    import reel, outro
    fc = ('[0:v]setpts=PTS-STARTPTS,fps=30,format=yuv420p[v0];[1:v]setpts=PTS-STARTPTS,fps=30,format=yuv420p[v1];'
          '[0:a]aresample=48000,asetpts=PTS-STARTPTS[a0];[1:a]aresample=48000,asetpts=PTS-STARTPTS[a1];'
          '[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]')
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', intro_mp4, '-i', reel_mp4, '-filter_complex', fc,
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264'] + reel.FINAL_ENC
                   + ['-pix_fmt', 'yuv420p', '-profile:v', 'high', '-video_track_timescale', '15360'] + outro.FINAL_A
                   + ['-movflags', '+faststart', out], check=True)


def check(spec):
    """The job's `intro` key: {"series": "gtavi", "days": N, "episode": E, "date": "YYYY-MM-DD"}. The count must be the
    days from the post's Dubai date to LAUNCH (never typed from memory), and the episode a whole number 1 to 12."""
    if not isinstance(spec, dict) or spec.get('series') != 'gtavi':
        raise ValueError('intro: {"series": "gtavi", "days": N, "episode": E, "date": "YYYY-MM-DD"}')
    if not spec.get('date'):
        raise ValueError('intro: gtavi needs "date" (the post\'s Dubai date) so the count is computed, not typed')
    want = days_for(spec['date'])
    if spec.get('days') != want:
        raise ValueError(f'intro: days {spec.get("days")!r} does not match {want} days from {spec["date"]} to launch {LAUNCH}')
    if want < 0:
        raise ValueError(f'intro: {spec["date"]} is after launch ({LAUNCH}); the countdown series has ended')
    if not isinstance(spec.get('episode'), int) or not 1 <= spec['episode'] <= 12:
        raise ValueError(f'intro: episode must be 1 to 12, got {spec.get("episode")!r}')
    for f in (BAND, BACK):
        if not os.path.exists(f):
            raise FileNotFoundError(f'gta_intro: {f} is missing')


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else days_for(datetime.date.today())
    ep = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    print(intro(n, sys.argv[3] if len(sys.argv) > 3 else f'gta-intro-{n}.mp4', episode=ep))
