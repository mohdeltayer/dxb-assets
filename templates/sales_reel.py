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
STEP = 3 * BEAT                                 # one row every three beats (slowed 28 Sep)
FIRST = BEAT                                    # first row on beat two
HOLD = 3.4                                      # after number one lands
PAGE_HOLD = 2.0                                 # before turning a page
IN, COUNT = 0.45, 1.0                           # row slide-in and count-up
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


def _base(title, week_label, source, date, page=''):
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
    line = f'{page} · {week_label}' if page else week_label
    d.text((R, 460), line, font=A.F('Regular', 32), fill=A.BODY, anchor='rm', **G.AR)
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


def _hw_row(h, frac, count, widest):
    """Hardware row: family name right, bar growing left, number, change."""
    lay = Image.new('RGBA', (R - L, ROW_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, R - L - 1, ROW_H - 1], radius=18, fill=A.hx('#1E1D4A') + (235,),
                        outline=A.hx('#3F3DA8') + (255,), width=2)
    x = R - L - 24
    d.text((x, 40), h['name'], font=A.F('Bold', 36), fill=A.INK, anchor='rm')
    d.text((x, 84), f'الإجمالي {_fmt(h["life"])}', font=A.F('Regular', 24), fill=A.BODY,
           anchor='rm', **G.AR)
    if h.get('last'):
        ch = (h['week'] - h['last']) / h['last'] * 100
        col = UP if ch >= 0 else DOWN
        # Dubai has no arrow glyphs, so the triangle is drawn
        ty = 122
        tri = ([(x - 16, ty + 7), (x, ty + 7), (x - 8, ty - 7)] if ch >= 0 else
               [(x - 16, ty - 7), (x, ty - 7), (x - 8, ty + 7)])
        d.polygon(tri, fill=col)
        d.text((x - 26, ty), f'{abs(ch):.0f}% عن الأسبوع الماضي', font=A.F('Medium', 24),
               fill=col, anchor='rm', **G.AR)
    bx0, bx1 = 24, x - 260
    bar1 = x - 310                                  # clear of the change line
    w = max(6, (bar1 - bx0) * (h['week'] / widest) * frac)
    d.rounded_rectangle([bar1 - w, 100, bar1, 128], radius=10, fill=A.AZURE)
    d.text((bx1, 52), _fmt(count), font=A.F('Bold', 40), fill=A.INK, anchor='rm')
    d.text((bx1 - d.textlength(_fmt(count), font=A.F('Bold', 40)) - 12, 56), 'جهاز',
           font=A.F('Regular', 24), fill=A.BODY, anchor='rm', **G.AR)
    return lay


def _slot_y(i):
    return ROWS_Y + i * (ROW_H + ROW_GAP)


def body(rows, week_label, date, out, hardware=(), title='الأكثر مبيعًا في اليابان',
         source='فاميتسو (Famitsu)'):
    """rows: the software top 10 (or 5). hardware: [dict(name, week, life,
    last)] in display order. Pages: ranks 10 to 6, 5 to 1, then hardware,
    each a countdown on the stats beat, crossfading into the next."""
    rows = sorted(rows, key=lambda r: r['rank'])[:10]
    pages = []
    if len(rows) > 5:
        pages.append(('sw', 'المراكز 10 إلى 6', rows[5:]))
    pages.append(('sw', 'المراكز 5 إلى 1' if len(rows) > 5 else '', rows[:5]))
    if hardware:
        pages.append(('hw', 'مبيعات الأجهزة', list(hardware)))
    XF = 0.5
    plan, t0 = [], 0.0
    for kind, label, items in pages:
        n = len(items)
        hold = HOLD if (kind, label) == (pages[-1][0], pages[-1][1]) else PAGE_HOLD
        dur = FIRST + (n - 1) * STEP + hold
        plan.append((kind, label, items, t0, dur))
        t0 += dur - XF
    total = t0 + XF
    bases = {label: _base(title, week_label, source, date, label).convert('RGBA')
             for _, label, _, _, _ in plan}
    widest = max((h['week'] for h in hardware), default=1)
    tmp = tempfile.mkdtemp(prefix='sales-')

    def draw(kind, label, items, start, t):
        im = bases[label].copy()
        if kind == 'sw':
            order = sorted(items, key=lambda r: -r['rank'])
            for i, r in enumerate(order):
                st = start + FIRST + i * STEP
                k = (t - st) / IN
                if k <= 0:
                    continue
                a = _ease(k)
                lay = _row(r, int(r['week'] * _ease((t - st) / COUNT)))
                if a < 1:
                    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
                im.alpha_composite(lay, (int(L - 40 * (1 - a)), _slot_y((r['rank'] - 1) % 5)))
        else:
            order = sorted(range(len(items)), key=lambda i: items[i]['week'])   # smallest first
            for n_, i in enumerate(order):
                h = items[i]
                st = start + FIRST + n_ * STEP
                k = (t - st) / IN
                if k <= 0:
                    continue
                a = _ease(k)
                g = _ease((t - st) / COUNT)
                lay = _hw_row(h, g, int(h['week'] * g), widest)
                if a < 1:
                    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
                im.alpha_composite(lay, (int(L - 40 * (1 - a)), _slot_y(i)))
        return im

    for f in range(int(round(total * FPS))):
        t = f / FPS
        live = [p for p in plan if p[3] <= t < p[3] + p[4]] or [plan[-1]]
        frame = draw(*live[0][:3], live[0][3], t)
        if len(live) > 1:                                  # crossfade into the next page
            nxt = draw(*live[1][:3], live[1][3], t)
            frame = Image.blend(frame, nxt, min(1, (t - live[1][3]) / XF))
        frame.convert('RGB').save(f'{tmp}/{f:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', str(FPS), out],
                   check=True)
    return out


def reel(rows, week_label, date, out, **kw):
    """The chart with the stats bed under it, closing on the outro card."""
    b = body(rows, week_label, date, os.path.join(tempfile.mkdtemp(), 'chart.mp4'), **kw)
    return outro.append(b, out, 'stats')
