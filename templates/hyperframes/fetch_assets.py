"""HyperFrames pilot (advisor, 23 Oct 2026): fetch and cut the official assets both pilot pieces use.

Nothing here is committed: each piece's assets/ folder is ignored by git. Run from the repo root:
    python3 templates/hyperframes/fetch_assets.py
Sources are the publishers' own: Rockstar's launch trailer (IGN's MP4 copy) and the GTA VI logo from
rockstargames.com/VI; CD PROJEKT RED's Oshima announcement image from its own post (@CDPRJP, 19 Oct).
"""
import os, re, shutil, subprocess, sys, urllib.request
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
GTA_MP4 = 'https://assets.ign.com/videos/mediaconvert/2026/10/15/1920/5a1ba86e-5f70-46c6-be76-e83223a908cc-1792069737.mp4'
GTA_PAGE = 'https://www.rockstargames.com/VI'
OSHIMA = 'https://pbs.twimg.com/media/HU-MoiTaMAAi55l.jpg?name=orig'
MARK = os.path.join(HERE, '..', 'digi-mark.jpg')


def get(url, out):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(out, 'wb') as f:
        f.write(r.read())
    return out


def gta(d):
    os.makedirs(d, exist_ok=True)
    raw = get(GTA_MP4, os.path.join(d, 'raw.mp4'))
    # 3 to 15 s: the marina, the boat and the phone call; no guns (checked on the 2 s map, 23 Oct)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '3', '-i', raw, '-t', '12', '-an', '-c:v', 'libx264',
                    '-preset', 'veryfast', '-crf', '20', os.path.join(d, 'gta6-launch-1920.mp4')], check=True)
    os.remove(raw)
    html = urllib.request.urlopen(urllib.request.Request(GTA_PAGE, headers=UA), timeout=60).read().decode('utf8', 'ignore')
    path = re.search(r'/VI/_next/static/media/poster_logo\.[A-Za-z0-9-]+\.png', html).group(0)
    logo = get('https://www.rockstargames.com' + path, os.path.join(d, 'logo.png'))
    im = Image.open(logo); im.crop(im.getbbox()).save(os.path.join(d, 'gta6-logo-trim.png')); os.remove(logo)
    shutil.copy(MARK, os.path.join(d, 'digi-mark.jpg'))


def oshima(d):
    os.makedirs(d, exist_ok=True)
    src = get(OSHIMA, os.path.join(d, 'cdpr.jpg'))
    im = Image.open(src)
    im.save(os.path.join(d, 'cdpr-full.jpg'), quality=95)                                # full image: the opener and the window
    im.crop((222, 96, 950, 614)).save(os.path.join(d, 'kojima-photo.jpg'), quality=95)   # the photo, above the anime box
    im.crop((606, 682, 950, 1026)).save(os.path.join(d, 'oshima-anime.jpg'), quality=95)  # the anime portrait
    os.remove(src)
    shutil.copy(MARK, os.path.join(d, 'digi-mark.jpg'))


if __name__ == '__main__':
    which = sys.argv[1:] or ['gta6-numbers', 'oshima-card']
    if 'gta6-numbers' in which: gta(os.path.join(HERE, 'gta6-numbers', 'assets'))
    if 'oshima-card' in which: oshima(os.path.join(HERE, 'oshima-card', 'assets'))
    print('assets ready:', ', '.join(which))
