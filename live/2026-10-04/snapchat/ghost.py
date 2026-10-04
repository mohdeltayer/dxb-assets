"""Snapchat ghost as an outline glyph, same stroke weight as outro._glyph."""
import math
from PIL import Image, ImageDraw

# Right half of the silhouette, top centre to bottom centre (unit square);
# the left half mirrors it.
_RIGHT = [(0.50, 0.07), (0.66, 0.11), (0.76, 0.24), (0.78, 0.40), (0.78, 0.50),
          (0.88, 0.53), (0.92, 0.58), (0.86, 0.62), (0.79, 0.64), (0.82, 0.73),
          (0.92, 0.79), (0.94, 0.83), (0.80, 0.86), (0.70, 0.89), (0.60, 0.88), (0.50, 0.92)]


def _spline(pts, n=12):
    out = []
    P = pts[-1:] + pts + pts[:2]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    return out


def outline():
    left = [(1 - x, y) for x, y in reversed(_RIGHT[1:-1])]
    return _spline(_RIGHT + left)


def glyph(d, x, y, s, c, k=4):
    """Draw on an ImageDraw `d` (RGBA layer) at (x, y), size s."""
    w = max(3, s // 10)
    big = Image.new('L', (s * k + 2 * w * k, s * k + 2 * w * k), 0)
    bd = ImageDraw.Draw(big)
    pts = [(w * k + px * s * k, w * k + py * s * k) for px, py in outline()]
    r = w * k / 2                                   # round pen along the dense spline
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / (r / 3)))
        for i in range(n):
            px, py = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            bd.ellipse([px - r, py - r, px + r, py + r], fill=255)
    m = big.resize((s + 2 * w, s + 2 * w), Image.LANCZOS)
    solid = Image.new('RGBA', m.size, c + (255,))
    d._image.paste(solid, (int(x) - w, int(y) - w), m)
