# «الطريق إلى Ocarina» series intro (Mohammad, 11 Oct 2026): 4.5 s of Nintendo's Zelda 40th Anniversary Triforce Medley
# (the Triforce of Courage lighting up with Link's silhouette, 3.8-8.0 s) under the release trailer's Triforce-to-logo fanfare, cropped 9:16 on the green triangle,
# with the series title in gold and the days left to 5 Nov.
import sys, subprocess
sys.path.insert(0, '/home/user/dxb-assets/templates')
from PIL import Image, ImageDraw, ImageFilter
import fast_ar as A
SRC = '/mnt/user-data/uploads/oot-triforce-medley.mov'
PIC = ('/mnt/user-data/uploads/oot-trailer-a.mp4', 181.2)    # Mohammad, 11 Oct: picture from option C, Nintendo's release trailer (Triforce fades, logo bursts in)
MUSIC = (SRC, 3.8)                                            # sound from his upload, the Triforce Medley orchestra
W, H, R = 1080, 1920, 910
BACK = ('/mnt/user-data/uploads/oot-gameplay-1920.mp4', 536.0)   # 11 Oct: Hyrule Field under the castle, blurred and dark behind the title, so the grid tile is not black
GOLD, INK = A.THEMES['gold'][1], (244, 243, 255)
AR = A.AR

def days_line(n):
    """Arabic count with the right agreement; 0 means launch day."""
    if n <= 0: return 'متوفرة الآن'
    if n == 1: return 'باقي يوم واحد'
    if n == 2: return 'باقي يومان'
    if n <= 10: return f'باقي {n} أيام'
    return f'باقي {n} يومًا'

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

def backdrop(d):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(BACK[1]), '-i', BACK[0], '-frames:v', '1', f'{d}/i-back-src.png'], check=True)
    im = Image.open(f'{d}/i-back-src.png').convert('RGB')
    w = int(im.height * W / H); x = (im.width - w) // 2
    im = im.crop((x, 0, x + w, im.height)).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(22))
    im = Image.blend(Image.new('RGB', (W, H), (6, 8, 6)), im, 0.55); im.save(f'{d}/i-back.png')

def intro(n, out, d='.'):
    layers(n, d); band_mask(d); backdrop(d)
    fc = ("[0:v]scale=1080:608:flags=lanczos,fps=30,format=rgba[sv];[5:v]format=gray[bm];[sv][bm]alphamerge[sb];"
          "color=c=black:s=1080x1920:d=4.2,format=rgba[cv];[cv][sb]overlay=0:656,format=gbrp[tb];[6:v]format=gbrp[bk];[bk][tb]blend=all_mode=screen,format=rgba[v0];"
          "[v0][1:v]overlay=0:0[v1];"
          "[2:v]format=rgba[ti];[3:v]format=rgba,fade=t=in:st=0.6:d=0.4:alpha=1[da];"
          "[v1][ti]overlay=x=0:y='max(0,0)'[v2];[v2][da]overlay=0:0,format=yuv420p[v]")
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(PIC[1]), '-t', '4.2', '-i', PIC[0],
                    '-loop', '1', '-t', '4.2', '-i', f'{d}/i-shade.png', '-loop', '1', '-t', '4.2', '-i', f'{d}/i-title.png',
                    '-loop', '1', '-t', '4.2', '-i', f'{d}/i-days.png', '-ss', str(MUSIC[1]), '-t', '4.2', '-i', MUSIC[0], '-loop', '1', '-t', '4.2', '-i', f'{d}/i-band.png',
                    '-loop', '1', '-t', '4.2', '-i', f'{d}/i-back.png',
                    '-filter_complex', fc, '-map', '[v]', '-map', '4:a',
                    '-af', 'afade=t=in:d=0.15,afade=t=out:st=3.75:d=0.45', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '4.2', out], check=True)
    return out

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 23
    print(intro(n, f'oot-intro-{n}.mp4'))
