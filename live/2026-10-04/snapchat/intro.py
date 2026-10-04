"""Digital Lounge Snapchat Highlight intro, 1080x1920, about 10 s: the mark
comes up on the jingle, the name and tagline on its chord, then four lines
on what the account covers and the handle. Story UI covers the top bar and
the reply bar, so everything sits between y 300 and 1600, centred."""
import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, '/home/user/dxb-assets/templates')
from PIL import Image, ImageDraw, ImageFilter
import fast_ar as A
import ig_ar as G
import outro as O
import sonic
from snap_bg import waves

W, H, FPS, DUR = 1080, 1920, 30, 10.5
CX = W // 2
MARK_Y, MARK = 560, 300
NAME_Y, TAG_Y, RULE_Y = 800, 905, 980
LINES = ['أحدث الإعلانات ومواعيد الإصدار',
         'أسعار الألعاب والأجهزة في المنطقة',
         'أخبار PlayStation وXbox وNintendo',
         'مشهد الألعاب في الخليج والعالم العربي']
LINE_Y0, LINE_GAP = 1065, 84
FOOT_Y = 1460


def base():
    im = waves(0.35)
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([CX - 460, MARK_Y - 460, CX + 460, MARK_Y + 460], fill=110)
    im = Image.composite(Image.new('RGB', (W, H), A.hx('#2A2870')), im, glow.filter(ImageFilter.GaussianBlur(170)))
    return im


def mark_layer():
    m = Image.open(A.MARK).convert('RGB').resize((MARK * 2, MARK * 2), Image.LANCZOS)
    mask = Image.new('L', m.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, m.width - 1, m.height - 1), fill=255)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay.paste(m.resize((MARK, MARK), Image.LANCZOS), (CX - MARK // 2, MARK_Y - MARK // 2),
              mask.resize((MARK, MARK), Image.LANCZOS))
    return lay


def foot(d):
    f = A.F('Medium', 44)
    tw = d.textlength(G.HANDLE, font=f)
    g, gap = 52, 26
    total = 2 * g + gap + 34 + tw
    x = CX - total / 2
    O._glyph(d, 'x', x, FOOT_Y - g / 2, g, A.INK)
    O._glyph(d, 'instagram', x + g + gap, FOOT_Y - g / 2, g, A.INK)
    d.text((x + 2 * g + gap + 34, FOOT_Y), G.HANDLE, font=f, fill=A.BODY, anchor='lm')


def render(out):
    notes, chord = sonic.beats('neon')
    b = base()
    mk = mark_layer()
    L = O._layer
    name = L(lambda d: d.text((CX, NAME_Y), 'ديجيتال لاونج', font=A.F('Bold', 96), fill=A.INK, anchor='mm', **G.AR))
    tag = L(lambda d: d.text((CX, TAG_Y), 'أخبار الألعاب بالعربي، كل يوم', font=A.F('Medium', 50),
                             fill=A.AZURE, anchor='mm', **G.AR))
    rule = L(lambda d: d.rounded_rectangle([CX - 70, RULE_Y - 3, CX + 70, RULE_Y + 3], 3, fill=A.AZURE))
    lines = [L(lambda d, t=t, i=i: d.text((CX, LINE_Y0 + i * LINE_GAP), t, font=A.F('Medium', 48),
                                          fill=A.INK, anchor='mm', **G.AR)) for i, t in enumerate(LINES)]
    ft = L(foot)
    for lay in lines + [name, tag]:
        bb = lay.getbbox()
        assert bb[0] >= 70 and bb[2] <= W - 70 and bb[1] >= 300 and bb[3] <= 1600, bb
    sched = ([(mk, 0.1, 0.5)] + [(name, chord, 0.3), (tag, chord + 0.15, 0.3), (rule, chord + 0.3, 0.3)]
             + [(l, chord + 1.0 + 0.55 * i, 0.35) for i, l in enumerate(lines)]
             + [(ft, chord + 1.0 + 0.55 * 4 + 0.3, 0.35)])
    tmp = tempfile.mkdtemp(prefix='intro-')
    for f in range(int(DUR * FPS)):
        t = f / FPS
        im = b.convert('RGBA')
        for lay, t0, ln in sched:
            l2 = O._fade(lay, O._ease((t - t0) / ln))
            if l2:
                im.alpha_composite(l2)
        d = ImageDraw.Draw(im)
        for i, n in enumerate(notes):                       # the mark rings on each note
            r = (t - n) / 0.5
            if 0 <= r <= 1:
                rad = MARK / 2 + 6 + 36 * O._ease(r)
                d.ellipse([CX - rad, MARK_Y - rad, CX + rad, MARK_Y + rad], outline=A.AZURE + (int(150 * (1 - r)),), width=4)
        im.convert('RGB').save(f'{tmp}/{f:04d}.png')
    jin, bed = O._cached('jingle', 'neon'), O._cached('bed', 'neon')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png',
                    '-i', jin, '-stream_loop', '-1', '-i', bed,
                    '-filter_complex',
                    f'[2:a]atrim=0:{DUR - 2.6},asetpts=PTS-STARTPTS,volume=-8dB,afade=t=in:d=0.8,'
                    f'afade=t=out:st={DUR - 2.6 - 1.2}:d=1.2,adelay=2600|2600[b];'
                    f'[1:a][b]amix=inputs=2:duration=longest:normalize=0,atrim=0:{DUR}[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                    '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), out], check=True)
    Image.open(f'{tmp}/{int(DUR * FPS) - 1:04d}.png').save(out.replace('.mp4', '.png'), optimize=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return out


if __name__ == '__main__':
    print(render('digi-snapchat-intro.mp4'))
