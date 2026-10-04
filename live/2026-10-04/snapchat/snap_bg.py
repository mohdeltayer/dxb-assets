"""Digital Lounge Snapchat profile background, 1080x1920: the banner's wave
lines only, no text, because Snapchat lays the mark, name and buttons over
the lower part. Portrait so any crop Snapchat takes still shows lines; the
bottom fades darker so the white name reads."""
import math
from PIL import Image, ImageDraw

W, H, K = 1080, 1920, 2


def hx(h):
    return tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))


GROUND, AZURE, INDIGO = hx('#141332'), hx('#28B6F6'), hx('#5552E0')


def waves(strength=1.0, gap=30, amp=95, freq=2.6):
    big = Image.new('RGB', (W * K, H * K), GROUND)
    d = ImageDraw.Draw(big)
    for j in range(-6, H // gap + 8):
        pts = []
        for x in range(0, W * K + 24, 10):
            u = x / (W * K)
            y = (j * gap + amp * math.sin(u * freq + j * 0.11)
                 + amp * 0.45 * math.sin(u * freq * 2.1 - j * 0.05 + 1.3)) * K
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            u = a[0] / (W * K)
            c = [INDIGO[i] + (AZURE[i] - INDIGO[i]) * u for i in range(3)]
            c = tuple(int(GROUND[i] + (c[i] - GROUND[i]) * strength) for i in range(3))
            d.line((a, b), fill=c, width=3 * K)
    return big.resize((W, H), Image.LANCZOS)


def shade(im, y0=0.5, top=0.0, bottom=0.7):
    """Ground colour laid over the image: light at the top, heavier from y0 down."""
    mask = Image.new('L', (1, H))
    for y in range(H):
        t = y / H
        a = top + (bottom - top) * max(0.0, (t - y0) / (1 - y0)) ** 1.2
        mask.putpixel((0, y), int(255 * a))
    return Image.composite(Image.new('RGB', (W, H), GROUND), im, mask.resize((W, H)))


if __name__ == '__main__':
    shade(waves()).save('digi-snapchat-background.png', optimize=True)
