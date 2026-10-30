# «الطريق إلى Ocarina» series intro (Mohammad, 11 Oct 2026): 4.2 s of Nintendo's Zelda 40th Anniversary Triforce Medley
# (the Triforce of Courage lighting up with Link's silhouette, 3.8-8.0 s) under the release trailer's Triforce-to-logo fanfare, cropped 9:16 on the green triangle,
# with the series title in gold and the days left to 5 Nov.
#
# Sources (B8, 29 Oct 2026): his upload (uploads/oot-triforce-medley.mov) was lost with the container reset and is not in
# git. The intro sound is therefore the exact 4.2 s the published episodes 4 and 5 carried (identical in both, decoded
# from cards/2026-10/ocarina-road-ep4-the-music-episode-v1.mp4 0 to 4.2 s, fades included) in
# templates/assets/ocarina/intro-medley.flac. When his file is back in uploads it is used again, as before. The picture
# and the backdrop fall back the same way to templates/assets/ocarina/ (trailer A 181.2 s as the 1080x608 band; Hyrule
# Field under the castle from Aonuma's presentation, blurred and dimmed), so the intro renders on the runner, the only
# place with the Dubai font. Nothing here is other music: no stand-in is ever used.
#
#     python3 ocarina_intro.py <days> [out.mp4]            # the intro alone
#     ocarina_intro.intro(n, out, final=True)              # encoded like outro.append's body, for the concat join
#     ocarina_intro.join(intro_mp4, reel_mp4, out)          # intro + finished Reel, concat demuxer, no re-encode
import os, sys, subprocess, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
import cards as C
import fast_ar as A
ASSETS = os.path.join(HERE, 'assets', 'ocarina')
SRC = C.U + 'oot-triforce-medley.mov'                         # his upload, the Triforce Medley orchestra
PIC_UP = (C.U + 'oot-trailer-a.mp4', 181.2)                   # Mohammad, 11 Oct: picture from option C, Nintendo's release trailer (Triforce fades, logo bursts in)
BACK_UP = (C.U + 'oot-gameplay-1920.mp4', 536.0)              # 11 Oct: Hyrule Field under the castle, blurred and dark behind the title, so the grid tile is not black
MEDLEY = os.path.join(ASSETS, 'intro-medley.flac')           # the published intro's 4.2 s, already faded in and out
BAND = os.path.join(ASSETS, 'intro-band.mp4')                 # trailer A 181.2 to 185.4 s, 1080x608, 30 fps
BACK = os.path.join(ASSETS, 'intro-back.jpg')                 # the backdrop, already blurred and dimmed (backdrop() below)
SECS = 4.2
W, H, R = 1080, 1920, 910
GOLD, INK = A.THEMES['gold'][1], (244, 243, 255)
AR = A.AR


def days_line(n):
    """Arabic count with the right agreement; 0 means launch day."""
    if n <= 0: return 'متوفرة الآن'
    if n == 1: return 'باقي يوم واحد'
    if n == 2: return 'باقي يومان'
    if n <= 10: return f'باقي {n} أيام'
    return f'باقي {n} يومًا'


def sources():
    """(music, picture, backdrop): his upload and the uploads trailer when present, else the committed assets.
    music is (file, start, prefaded)."""
    music = (SRC, 3.8, False) if os.path.exists(SRC) else (MEDLEY, 0.0, True)
    if not os.path.exists(music[0]):
        raise FileNotFoundError('the Triforce Medley is missing (uploads/oot-triforce-medley.mov and '
                                'templates/assets/ocarina/intro-medley.flac); no other music is used for the intro')
    pic = PIC_UP if os.path.exists(PIC_UP[0]) else (BAND, 0.0)
    back = BACK_UP if os.path.exists(BACK_UP[0]) else None
    return music, pic, back


def layers(n, d):
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = Image.new('L', (1, H), 0)
    for y in range(H):
        t = max(0.0, 1 - y / 900); g.putpixel((0, y), int(200 * t ** 1.3))   # dark top so the gold reads
    blk = Image.new('RGBA', (W, H), (8, 10, 6, 255)); blk.putalpha(g.resize((W, H))); shade.alpha_composite(blk); shade.save(f'{d}/i-shade.png')
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(t)
    dr.text((W // 2, 330), 'الطريق إلى Ocarina', font=A.F('Bold', 112), fill=GOLD, anchor='ma', **AR)
    glow = t.filter(ImageFilter.GaussianBlur(18)); t2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); t2.alpha_composite(glow); t2.alpha_composite(t)
    t2.save(f'{d}/i-title.png')
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
    dc.text((W // 2, 482), days_line(n), font=A.F('Medium', 66), fill=INK, anchor='ma', **AR)
    c.save(f'{d}/i-days.png')


def band_mask(d):
    m = Image.new('L', (1080, 608), 255); dm = ImageDraw.Draw(m)
    for i in range(150):                                         # top and bottom 150 px fade into the black canvas
        v = int(255 * (i / 150) ** 1.6); dm.line([(0, i), (1080, i)], fill=v); dm.line([(0, 607 - i), (1080, 607 - i)], fill=v)
    m.save(f'{d}/i-band.png')


def backdrop(d, back=None):
    if back is None:                                             # the committed backdrop, already processed
        shutil.copy(BACK, f'{d}/i-back.png' if BACK.endswith('.png') else f'{d}/i-back.jpg')
        return f'{d}/i-back.png' if BACK.endswith('.png') else f'{d}/i-back.jpg'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(back[1]), '-i', back[0], '-frames:v', '1', f'{d}/i-back-src.png'], check=True)
    im = Image.open(f'{d}/i-back-src.png').convert('RGB')
    w = int(im.height * W / H); x = (im.width - w) // 2
    im = im.crop((x, 0, x + w, im.height)).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(22))
    im = Image.blend(Image.new('RGB', (W, H), (6, 8, 6)), im, 0.55); im.save(f'{d}/i-back.png')
    return f'{d}/i-back.png'


def intro(n, out, d=None, final=False):
    """The 4.2 s intro with «days_line(n)». `final=True` encodes it as outro.append encodes a Reel's body
    (reel.FINAL_ENC, high profile, the same track timescale, outro.FINAL_A), so join() needs no re-encode."""
    own = d is None
    d = d or tempfile.mkdtemp(prefix='oot-intro-')
    try:
        music, pic, back = sources()
        layers(n, d); band_mask(d); bk = backdrop(d, back)
        fc = ("[0:v]scale=1080:608:flags=lanczos,fps=30,format=rgba[sv];[5:v]format=gray[bm];[sv][bm]alphamerge[sb];"
              "color=c=black:s=1080x1920:d=4.2:r=30,format=rgba[cv];[cv][sb]overlay=0:656,format=gbrp[tb];[6:v]format=gbrp[bk];[bk][tb]blend=all_mode=screen,format=rgba[v0];"
              "[v0][1:v]overlay=0:0[v1];"
              "[2:v]format=rgba[ti];[3:v]format=rgba,fade=t=in:st=0.6:d=0.4:alpha=1[da];"
              "[v1][ti]overlay=x=0:y='max(0,0)'[v2];[v2][da]overlay=0:0,fps=30,format=yuv420p[v]")
        af = 'aformat=sample_rates=48000:channel_layouts=stereo' + ('' if music[2] else ',afade=t=in:d=0.15,afade=t=out:st=3.75:d=0.45')
        if final:                                                 # read the live values, so a change to the Reel's encode follows here
            import reel, outro
            enc = ['-c:v', 'libx264'] + reel.FINAL_ENC + ['-pix_fmt', 'yuv420p', '-profile:v', 'high', '-video_track_timescale', '15360'] + outro.FINAL_A
        else:
            enc = ['-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000']
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(pic[1]), '-t', str(SECS), '-i', pic[0],
                        '-loop', '1', '-t', str(SECS), '-i', f'{d}/i-shade.png', '-loop', '1', '-t', str(SECS), '-i', f'{d}/i-title.png',
                        '-loop', '1', '-t', str(SECS), '-i', f'{d}/i-days.png', '-ss', str(music[1]), '-t', str(SECS), '-i', music[0],
                        '-loop', '1', '-t', str(SECS), '-i', f'{d}/i-band.png', '-loop', '1', '-t', str(SECS), '-i', bk,
                        '-filter_complex', fc, '-map', '[v]', '-map', '4:a', '-af', af] + enc + ['-t', str(SECS), out], check=True)
        return out
    finally:
        if own:
            shutil.rmtree(d, ignore_errors=True)


def join(intro_mp4, reel_mp4, out):
    """The intro ahead of a finished Reel (reel.py's output, end card included): concat demuxer, stream copy."""
    tmp = tempfile.mkdtemp(prefix='oot-join-')
    try:
        lst = f'{tmp}/list.txt'
        open(lst, 'w').write(f"file '{os.path.abspath(intro_mp4)}'\nfile '{os.path.abspath(reel_mp4)}'\n")
        part = f'{tmp}/joined.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                        '-movflags', '+faststart', part], check=True)
        shutil.move(part, out)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check(spec):
    """The job's `intro` key: {"series": "ocarina", "days": N} (N >= 0, days left to 5 Nov 2026)."""
    if not isinstance(spec, dict) or spec.get('series') != 'ocarina':
        raise ValueError('intro: {"series": "ocarina", "days": N}; the Ocarina intro is the only series intro')
    if not isinstance(spec.get('days'), int) or spec['days'] < 0:
        raise ValueError(f'intro: days must be a whole number of days left to 5 Nov 2026, got {spec.get("days")!r}')
    sources()                                                     # the medley must exist; never a stand-in


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 23
    print(intro(n, sys.argv[2] if len(sys.argv) > 2 else f'oot-intro-{n}.mp4'))
