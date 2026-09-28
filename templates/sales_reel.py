"""Digital Lounge sales-chart Reel: the week's top 5 as box art (trial,
28 Sep 2026, Mohammad: "animated, the top five as box art").

A 9:16 Reel in the Reels safe zone. The header (chip أرقام, title, week and
source) is up from the first frame; the rows then arrive as a countdown,
5 to 1, one every two beats of the `stats` bed (124 BPM), each fading in
with a short slide and its weekly number counting up. Number one lands
last and gets the azure edge. Nothing zooms or pans. The clip ends on the
outro card with the stats jingle, the bed under the whole chart.

Box art comes from the publisher's own pages (Nintendo Japan product
pages, Capcom's e-capcom shop, the PlayStation Store), never a retailer.
`trim` cuts the white or transparent margin those images carry.

    rows = [dict(rank=1, title='Rhythm Heaven Groove', plat='Switch',
                 week=24756, life=1000045, was=2, new=False,
                 art='live/.../rhythm-heaven-groove.png'), ...]
    reel(rows, 'أسبوع 7 إلى 13 سبتمبر', '17 Sep 2026', out)
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw

import fast_ar as A
import ig_ar as G
import outro
import sonic

W, H = 1080, 1920
FPS = 30
L, R = G.SAFE_LEFT, W - G.SAFE_RIGHT          # 96 .. 910
BEAT = 60 / sonic.FLAVOURS['stats']['bpm']
STEP = 2 * BEAT                                 # one row every two beats
FIRST = BEAT                                    # first row on beat two
HOLD = 2.6                                      # after number one lands
ROW_H, ROW_GAP, ROWS_Y = 158, 12, 494
PLAT = {'Switch': 'Switch', 'Switch2': 'Switch 2', 'PS5': 'PS5', 'PS4': 'PS4',
        'XboxSeries': 'Xbox Series'}
# Down is amber, not red: red drifts toward pink on the indigo ground.
UP, DOWN = A.hx('#3DDC97'), A.hx('#FFB547')


def trim(path):
    """Box art without the white or transparent margin around it."""
    im = Image.open(path).convert('RGBA')
    white = Image.new('RGBA', im.size, (255, 255, 255, 255))
    diff = ImageChops.difference(im, white).convert('L').point(lambda v: 255 if v > 18 else 0)
    alpha = im.getchannel('A').point(lambda v: 255 if v > 20 else 0)
    box = ImageChops.multiply(diff, alpha).getbbox()
    return im.crop(box) if box else im


def _ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def _fmt(n):
    return f'{n:,}'


def _base(title, week_label, source, date):
    im = Image.new('RGB', (W, H), A.GROUND)
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-200, 300, W + 200, 1500], fill=70)
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    im = Image.composite(Image.new('RGB', (W, H), A.hx('#24226A')), im, glow)
    d = ImageDraw.Draw(im)
    # chip, title, week line
    f = A.F('Bold', 38)
    tw = d.textlength('أرقام', font=f, **G.AR)
    d.rounded_rectangle([R - tw - 36, 300, R, 356], radius=12, fill=A.AZURE)
    d.text((R - 18, 328), 'أرقام', font=f, fill=A.GROUND, anchor='rm', **G.AR)
    d.text((R, 400), title, font=A.F('Bold', 58), fill=A.INK, anchor='rm', **G.AR)
    d.text((R, 460), week_label, font=A.F('Regular', 32), fill=A.BODY, anchor='rm', **G.AR)
    foot_y = G.SAFE_BOTTOM - G.REEL_FH
    G._footer(im, foot_y, source, date, 'cold', 7, right=G.SAFE_RIGHT, fh=G.REEL_FH,
              left=G.SAFE_LEFT, handles=False)
    return im


def _row(r, count):
    """One row on transparency, right to left: rank, box, title, number."""
    lay = Image.new('RGBA', (R - L, ROW_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    top = r['rank'] == 1
    d.rounded_rectangle([0, 0, R - L - 1, ROW_H - 1], radius=18, fill=A.hx('#1E1D4A') + (235,),
                        outline=(A.AZURE + (255,)) if top else (A.hx('#3F3DA8') + (255,)),
                        width=4 if top else 2)
    x = R - L - 22
    d.text((x, ROW_H / 2), str(r['rank']), font=A.F('Bold', 76 if top else 62),
           fill=A.AZURE if top else A.INK, anchor='rm')
    x -= 70
    art = trim(r['art'])
    bh = ROW_H - 26
    art = art.resize((max(1, round(art.width * bh / art.height)), bh), Image.LANCZOS)
    lay.alpha_composite(art, (int(x - art.width), 13))
    x -= art.width + 22
    title, size = r['title'], 30
    while size > 25 and d.textlength(title, font=A.F('Bold', size)) > x - 196:
        size -= 1                          # shrink a little before cutting
    tf = A.F('Bold', size)
    while d.textlength(title, font=tf) > x - 196 and len(title) > 4:
        title = title[:-2].rstrip() + '…' if not title.endswith('…') else title[:-3].rstrip() + '…'
    d.text((x, 38), title, font=tf, fill=A.INK, anchor='rm')
    pf = A.F('Medium', 24)
    plat = PLAT.get(r['plat'], r['plat'])
    pw = d.textlength(plat, font=pf)
    d.rounded_rectangle([x - pw - 24, 64, x, 98], radius=8, fill=A.hx('#5552E0'))
    d.text((x - 12, 81), plat, font=pf, fill=A.INK, anchor='rm')
    if r.get('new'):
        prev = 'جديد'
        pc = A.AZURE
    elif r.get('was'):
        prev = f'الأسبوع الماضي: {r["was"]}'
        pc = UP if r['was'] > r['rank'] else DOWN if r['was'] < r['rank'] else A.BODY
    else:
        prev, pc = '', A.BODY
    if prev:
        d.text((x - pw - 40, 81), prev, font=A.F('Medium', 24), fill=pc, anchor='rm', **G.AR)
    d.text((x, 124), f'الإجمالي {_fmt(r["life"])}', font=A.F('Regular', 24), fill=A.BODY,
           anchor='rm', **G.AR)
    # this week's number, counting up, on the left
    d.text((24, ROW_H / 2 - 16), _fmt(count), font=A.F('Bold', 40), fill=A.INK, anchor='lm')
    d.text((24, ROW_H / 2 + 30), 'نسخة هذا الأسبوع', font=A.F('Regular', 22), fill=A.BODY,
           anchor='lm', **G.AR)
    return lay


def body(rows, week_label, date, out, title='الأكثر مبيعًا في اليابان',
         source='فاميتسو (Famitsu)'):
    rows = sorted(rows, key=lambda r: r['rank'])[:5]
    base = _base(title, week_label, source, date).convert('RGBA')
    order = sorted(rows, key=lambda r: -r['rank'])          # 5 first, 1 last
    starts = {r['rank']: FIRST + i * STEP for i, r in enumerate(order)}
    dur = FIRST + (len(order) - 1) * STEP + HOLD
    tmp = tempfile.mkdtemp(prefix='sales-')
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = base.copy()
        for r in rows:
            k = (t - starts[r['rank']]) / 0.3
            if k <= 0:
                continue
            a = _ease(k)
            count = int(r['week'] * _ease((t - starts[r['rank']]) / 0.7))
            lay = _row(r, count)
            if a < 1:
                lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
            y = ROWS_Y + (r['rank'] - 1) * (ROW_H + ROW_GAP)
            im.alpha_composite(lay, (int(L - 40 * (1 - a)), y))
        im.convert('RGB').save(f'{tmp}/{f:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', str(FPS), out],
                   check=True)
    return out


def reel(rows, week_label, date, out, **kw):
    """The chart with the stats bed under it, closing on the outro card."""
    b = body(rows, week_label, date, os.path.join(tempfile.mkdtemp(), 'chart.mp4'), **kw)
    return outro.append(b, out, 'stats')
