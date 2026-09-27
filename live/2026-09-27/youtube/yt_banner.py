"""Digital Lounge YouTube banner, 2560x1440: the X banner (digi3) redrawn
at YouTube's size. Everything that must be read sits in the 1546x423 area
YouTube shows on every device; the lines fill the rest for TV."""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 2560, 1440
SAFE = (507, 508, 2053, 931)          # x0, y0, x1, y1 shown on all devices
FONTS = '/root/fonts-private/dubai/Dubai-'
AR = dict(direction='rtl', language='ar')


def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


GROUND, AZURE, INDIGO = hx('#141332'), hx('#28B6F6'), hx('#5552E0')
INK, BODY = hx('#F4F3FF'), hx('#C9C8E6')
F = lambda w, s: ImageFont.truetype(FONTS + w + '.ttf', s)


def waves(strength, k=2, gap=34, amp=70, freq=3.2):
    big = Image.new('RGB', (W * k, H * k), GROUND)
    d = ImageDraw.Draw(big)
    for j in range(-6, H // gap + 8):
        pts = []
        for x in range(0, W * k + 24, 12):
            u = x / (W * k)
            y = (j * gap + amp * math.sin(u * freq + j * 0.12)
                 + amp * 0.45 * math.sin(u * freq * 2.1 - j * 0.05 + 1.3)) * k
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            u = a[0] / (W * k)
            c = tuple(int(INDIGO[i] + (AZURE[i] - INDIGO[i]) * u) for i in range(3))
            c = tuple(int(GROUND[i] + (c[i] - GROUND[i]) * strength) for i in range(3))
            d.line((a, b), fill=c, width=3 * k)
    return big.resize((W, H), Image.LANCZOS)


def banner():
    im = waves(0.85)
    # The dark plate the name sits on, with the lines barely showing through.
    px0, px1, py0, py1 = 760, 1800, 535, 905
    im.paste(waves(0.12).crop((px0, py0, px1, py1)), (px0, py0))
    d = ImageDraw.Draw(im)
    cx = W // 2
    d.text((cx, 660), 'ديجيتال لاونج', font=F('Bold', 150), fill=INK, anchor='mm', **AR)
    d.text((cx, 788), 'أخبار الألعاب', font=F('Medium', 62), fill=AZURE, anchor='mm', **AR)
    f = F('Medium', 34)
    text = 'DIGITAL LOUNGE'
    sp = 14
    w = sum(d.textlength(ch, font=f) for ch in text) + sp * (len(text) - 1)
    x = cx - w / 2
    for ch in text:
        d.text((x, 862), ch, font=f, fill=BODY, anchor='lm')
        x += d.textlength(ch, font=f) + sp
    return im


if __name__ == '__main__':
    im = banner()
    im.save('digi-youtube-banner.png', optimize=True)
    # Preview with YouTube's crop guides: TV (all), desktop strip, all devices.
    p = im.copy()
    d = ImageDraw.Draw(p)
    d.rectangle([0, SAFE[1], W - 1, SAFE[3]], outline=(255, 255, 255), width=4)
    d.rectangle(SAFE, outline=(255, 200, 0), width=6)
    p.resize((1280, 720)).save('digi-youtube-banner-guides.png')
