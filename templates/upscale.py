"""AI upscaling test for Reel footage (Mohammad, 12 Oct 2026: image quality).

A 16:9 trailer is cropped to a 9:16 window and enlarged to 1080x1920: 1.78x
from 1080p, 2.4x from a letterboxed film trailer, which looks soft with plain
lanczos. This runs Real-ESRGAN x2 (xinntao, BSD-3; weights in /root/models,
not in git) on the cropped window first, then lanczos to 1080x1920, so the
two can be compared side by side before it is used on a post.

    python3 templates/upscale.py <file in uploads> <start> <seconds> <focus> <out-stem> [crop=W:H:X:Y]

Writes <out-stem>-compare.mp4 (left: today's lanczos + unsharp, right:
Real-ESRGAN) and <out-stem>-compare.png (one frame, both halves at full size).
CPU only here (no GPU): roughly a few seconds a frame, so test short stretches.
"""
import os, sys, subprocess, tempfile, shutil, glob
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

U = '/mnt/user-data/uploads/'
MODEL = '/root/models/RealESRGAN_x2plus.pth'
W, H = 1080, 1920


class RDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1); s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        x1 = s.l(s.conv1(x)); x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
        x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1))); x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
        return s.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x


class RRDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__(); s.rdb1, s.rdb2, s.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)

    def forward(s, x):
        return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    """The Real-ESRGAN generator (x2: the input is pixel-unshuffled first)."""
    def __init__(s, nf=64, nb=23, gc=32):
        super().__init__()
        s.conv_first = nn.Conv2d(12, nf, 3, 1, 1)
        s.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        f = s.conv_first(F.pixel_unshuffle(x, 2))
        f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode='nearest')))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))


_net = None
def net():
    global _net
    if _net is None:
        _net = RRDBNet()
        _net.load_state_dict(torch.load(MODEL, map_location='cpu')['params_ema'], strict=True)
        _net.eval(); torch.set_num_threads(os.cpu_count())
    return _net


def _to_t(im):        # PIL -> 1x3xHxW float (no numpy: torch's numpy bridge is broken in this container)
    w, h = im.size
    t = torch.frombuffer(bytearray(im.convert('RGB').tobytes()), dtype=torch.uint8)
    return t.view(h, w, 3).permute(2, 0, 1).unsqueeze(0).float() / 255


def _to_im(t):
    t = (t.squeeze(0).clamp(0, 1) * 255).round().to(torch.uint8).permute(1, 2, 0).contiguous()
    h, w, _ = t.shape
    return Image.frombytes('RGB', (w, h), bytes(t.flatten().tolist()))


def sr(im):
    """One frame, upscaled 2x by Real-ESRGAN."""
    w, h = im.size
    pw, ph = w % 2, h % 2                  # pixel_unshuffle needs even sides
    if pw or ph:
        im = im.crop((0, 0, w - pw, h - ph))
    with torch.no_grad():
        return _to_im(net()(_to_t(im)))


def compare(f, start, secs, focus, stem, crop=''):
    tmp = tempfile.mkdtemp(prefix='upscale-')
    try:
        src = (crop + ',' if crop else '')
        # the 9:16 window reel.py would take, at source resolution
        win = f"{src}crop=ih*9/16:ih:(iw-ih*9/16)*{focus}:0"
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', str(secs), '-i', U + f,
                        '-vf', win + ',fps=30', f'{tmp}/s%04d.png'], check=True)
        for p in sorted(glob.glob(f'{tmp}/s*.png')):
            im = Image.open(p)
            base = im.resize((W, H), Image.LANCZOS)            # today: lanczos (reel.py adds a light unsharp after)
            ai = sr(im).resize((W, H), Image.LANCZOS)
            base.save(p.replace('/s', '/b')); ai.save(p.replace('/s', '/a'))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', f'{tmp}/b%04d.png',
                        '-framerate', '30', '-i', f'{tmp}/a%04d.png', '-filter_complex',
                        '[0:v]unsharp=5:5:0.5:5:5:0.0[l];[l][1:v]hstack,format=yuv420p', '-c:v', 'libx264',
                        '-crf', '14', '-preset', 'slow', stem + '-compare.mp4'], check=True)
        mid = sorted(glob.glob(f'{tmp}/b*.png'))[len(glob.glob(f'{tmp}/b*.png')) // 2]
        b, a = Image.open(mid), Image.open(mid.replace('/b', '/a'))
        s = Image.new('RGB', (W * 2, H)); s.paste(b, (0, 0)); s.paste(a, (W, 0)); s.save(stem + '-compare.png')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return stem + '-compare.mp4'


if __name__ == '__main__':
    a = sys.argv[1:]
    print(compare(a[0], float(a[1]), float(a[2]), float(a[3]), a[4], a[5] if len(a) > 5 else ''))
