"""Digital Lounge weekly sales Reel in the full-screen format (draft for
Mohammad, 5 Oct 2026; replaces sales_reel's rows on a flat ground, which
left bare bands above and below the chart).

Every second of it is picture. It opens on a 2x2 mosaic of the top four
games under the question (the answer is in the picture, not named), then
counts down 10 to 1, each entry on an official screenshot of that game
filling the 9:16 frame and panning slowly, with the numbers laid over a
soft band low in the frame: the rank large in the theme colour, the box
art beside it, the title as the publisher writes it, platform, last week's
place and the two figures (this week, since launch). Hardware follows on a
dimmed mosaic of the week's games, counting from last week's numbers to
this week's with the rows re-sorting live (hw_clip), then the end card with the stats
jingle; the stats bed plays under the whole chart. Everything stays in the
Reels safe zone (ig_ar.SAFE_*).

    rows = [dict(rank=1, title='Derby Stallion 2', plat='Switch2', week=29336,
                 life=29336, new=True, art='box.jpg',
                 shot=('screen.jpg', (0.0, 0.2))), ...]
    reel(rows, 'أسبوع 21 إلى 27 سبتمبر 2026', '1 Oct 2026', out, hardware=hw,
         hook='من تصدّر مبيعات اليابان هذا الأسبوع؟')

`shot` is an official screenshot (publisher store page, Steam, press kit),
1920 wide where one exists, and the pan's (from, to) focus, 0 left to 1
right; keep logos and text in the art out of the window. Box art comes
from the publisher's own pages, never a retailer.
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter

import cards as C
import fast_ar as A
import ig_ar as G
import outro
import reel as RL
import sales_reel as S

W, H = 1080, 1920
L, R = G.SAFE_LEFT, W - G.SAFE_RIGHT            # 96 .. 910
TOP, BOT = G.SAFE_TOP, G.SAFE_BOTTOM            # 285 .. 1480
PLAT = S.PLAT
UP, DOWN = S.UP, S.DOWN
SUB = 'fam-full'                                # stills are copied to uploads/<SUB>/


def _secs(rank):
    """Time on screen: the lower ranks briefly, the top five longer, number one longest."""
    return 5.2 if rank == 1 else 4.0 if rank <= 5 else 3.4


def _text(lay, xy, s, f, fill, anchor, ar=False, stroke=5):
    """Text with an indigo outline and a soft shadow, as on the Reel lines."""
    kw = dict(G.AR) if ar else {}
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor, **kw)
    out = m.filter(ImageFilter.MaxFilter(stroke if stroke % 2 else stroke + 1))
    sh = out.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.6))
    for col, mk, off in [((0, 0, 0), sh, (3, 4)), (A.GROUND, out, (0, 0)), (fill, m, (0, 0))]:
        c = Image.new('RGBA', (W, H), col + (255,)); a = Image.new('L', (W, H), 0)
        a.paste(mk, off); c.putalpha(a); lay.alpha_composite(c)


def _top_line(lay, title, week_label, accent, source='فاميتسو (Famitsu)'):
    """The chart's name and week, small, under the top of the safe zone."""
    RL._band(lay, 0, TOP + 190, True, 170)
    d = ImageDraw.Draw(lay)
    d.rectangle([R - 44, TOP + 22, R, TOP + 26], fill=accent)
    _text(lay, (R - 60, TOP + 24), title, A.F('Bold', 36), A.INK, 'rm', ar=True, stroke=3)
    _text(lay, (R, TOP + 76), f'{source}\u200f  ·  \u200f{week_label}', A.F('Medium', 30), A.BODY, 'rm', ar=True, stroke=3)


def _chip(d, x_right, y, text, fill, ink, f, ar=True):
    kw = dict(G.AR) if ar else {}
    tw = d.textlength(text, font=f, **kw)
    d.rounded_rectangle([x_right - tw - 28, y, x_right, y + 50], radius=10, fill=fill)
    d.text((x_right - 14, y + 25), text, font=f, fill=ink, anchor='rm', **kw)
    return x_right - tw - 28


def entry_layer(r, title, week_label, accent, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _top_line(lay, title, week_label, accent)
    RL._band(lay, 860, H, False, 235)
    # numbers block, from the bottom of the safe zone up
    y_num = BOT - 70                                   # baseline of the two figures
    nf, lf = A.F('Bold', 66), A.F('Regular', 30)
    _text(lay, (R, y_num), S._fmt(r['week']), nf, A.INK, 'rs')
    _text(lay, (R, y_num + 44), 'نسخة هذا الأسبوع', lf, A.BODY, 'rm', ar=True, stroke=3)
    if r['life'] != r['week']:
        _text(lay, (L + 330, y_num), S._fmt(r['life']), A.F('Bold', 50), A.BODY, 'rs')
        _text(lay, (L + 330, y_num + 44), 'منذ الإصدار', lf, A.BODY, 'rm', ar=True, stroke=3)
    # platform chip and last week's place
    d = ImageDraw.Draw(lay)
    cy = y_num - 160
    x = _chip(d, R, cy, PLAT.get(r['plat'], r['plat']), A.INDIGO, A.INK, A.F('Medium', 32), ar=False)
    tf = A.F('Medium', 32)
    if r.get('new'):
        _chip(d, x - 16, cy, 'جديد', A.AZURE, A.GROUND, tf)
    elif r.get('was'):
        col = UP if r['was'] > r['rank'] else DOWN if r['was'] < r['rank'] else A.BODY
        t = f'الأسبوع الماضي: {r["was"]}'
        tx = x - 22
        if r['was'] != r['rank']:                      # Dubai has no arrows, so the triangle is drawn
            ty = cy + 25
            tri = ([(tx - 20, ty + 9), (tx, ty + 9), (tx - 10, ty - 9)] if r['was'] > r['rank'] else
                   [(tx - 20, ty - 9), (tx, ty - 9), (tx - 10, ty + 9)])
            d.polygon(tri, fill=col); tx -= 32
        _text(lay, (tx, cy + 25), t, tf, col, 'rm', ar=True, stroke=3)
    # title, as the publisher writes it, shrinking before it would leave the zone
    # a long title may carry one hand break ("\n"); the lines stack upwards
    parts = r['title'].split('\n')
    wide = lambda s: max(d.textlength(p, font=A.F('Bold', s)) for p in parts)
    size = 64
    while wide(size) > R - L and size > 40:
        size -= 2
    ty = cy - 34
    for k, p in enumerate(reversed(parts)):
        _text(lay, (R, ty - k * round(size * 1.15)), p, A.F('Bold', size), A.INK, 'rs')
    ty -= (len(parts) - 1) * round(size * 1.15)
    if wide(size) > R - L:
        raise ValueError(f'title runs out of the safe zone: {r["title"]}')
    # rank, large, with the box art to its left
    rf = A.F('Bold', 250 if r['rank'] == 1 else 210)
    ry = ty - size - 30
    _text(lay, (R, ry), str(r['rank']), rf, accent, 'rs', stroke=7)
    rw = d.textlength(str(r['rank']), font=rf)
    _text(lay, (R - rw - 24, ry - 20), 'المركز', A.F('Medium', 34), A.BODY, 'rs', ar=True, stroke=3)
    if r.get('art'):
        b = S.trim(r['art']).convert('RGBA')
        bh = 250 if r['rank'] == 1 else 220
        b = b.resize((max(1, round(b.width * bh / b.height)), bh), Image.LANCZOS)
        if b.width > 360:
            b = b.resize((360, round(b.height * 360 / b.width)), Image.LANCZOS)
        edge = Image.new('RGBA', (b.width + 8, b.height + 8), A.GROUND + (255,))
        x0, y0 = L, ry - b.height
        sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle([x0, y0, x0 + b.width + 8, y0 + b.height + 8], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(12))
        s = Image.new('RGBA', (W, H), (0, 0, 0, 255)); s.putalpha(sh); lay.alpha_composite(s)
        lay.alpha_composite(edge, (x0, y0)); lay.alpha_composite(b, (x0 + 4, y0 + 4))
    if ry - (250 if r['rank'] == 1 else 210) < TOP + 120:
        raise ValueError('entry block runs into the top line')
    lay.save(path); return path


def mosaic(images, path, cols=2, rows=2, dim=0.0):
    """Tiles filling 1080x1920; images are (file, focus) with the file in
    uploads. `dim` darkens toward the ground (for a background)."""
    im = Image.new('RGB', (W, H), A.GROUND)
    tw, th = W // cols, H // rows
    for k, (f, fo) in enumerate(images[:cols * rows]):
        a = Image.open(C.U + f).convert('RGB')
        sc = max(tw / a.width, th / a.height)
        a = a.resize((round(a.width * sc), round(a.height * sc)), Image.LANCZOS)
        x = int((a.width - tw) * fo); y = (a.height - th) // 2
        im.paste(a.crop((x, y, x + tw, y + th)), ((k % cols) * tw, (k // cols) * th))
    d = ImageDraw.Draw(im)
    for c in range(1, cols):
        d.rectangle([c * tw - 3, 0, c * tw + 2, H], fill=A.GROUND)
    for r_ in range(1, rows):
        d.rectangle([0, r_ * th - 3, W, r_ * th + 2], fill=A.GROUND)
    if dim:
        im = Image.blend(im, Image.new('RGB', (W, H), A.GROUND), dim)
    im.save(path, quality=93); return path


def hook_layer(hook, sub, source, date, theme, path):
    """The question over the mosaic, centred in the safe zone on a soft plate."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    plate = Image.new('L', (W, H), 0)
    ImageDraw.Draw(plate).rectangle([0, 700, W, 1260], fill=215)
    plate = plate.filter(ImageFilter.GaussianBlur(70))
    g = Image.new('RGBA', (W, H), A.GROUND + (255,)); g.putalpha(plate); lay.alpha_composite(g)
    d = ImageDraw.Draw(lay)
    G._ACC = G.ACCENTS[theme]
    probe = ImageDraw.Draw(Image.new('RGBA', (W, H)))
    lines = G._wrap(probe, hook, A.F('Bold', 88), R - L)
    y = 1000 - (len(lines) * 112) // 2 - 40
    end = G._head(d, hook, y, 'أرقام', None, 88, 112, right=G.SAFE_RIGHT, left=G.SAFE_LEFT, chip=G._ACC)
    d.rectangle([R - 44, end + 34, R, end + 38], fill=G._ACC)
    d.text((R - 62, end + 36), f'{source}‏  ·  ‏{sub}', font=A.F('Medium', 34), fill=A.BODY,
           anchor='rm', **G.AR)
    lay.save(path); return path


CONSOLES = {'Switch 2': 'switch2.png', 'Switch': 'switch.png', 'PS5': 'ps5.png',
            'Xbox Series': 'xbox-series.png'}
HW_ROW, HW_GAP, HW_Y = 196, 20, 580          # four rows end at 1424, inside the safe zone
PLATE = 168


def _plate(name):
    """The console's own product shot, contained on a soft indigo plate the
    size of the games' box art."""
    pl = Image.new('RGBA', (PLATE, PLATE), (0, 0, 0, 0))
    g = Image.new('L', (PLATE, PLATE), 0)
    ImageDraw.Draw(g).ellipse([-30, -30, PLATE + 30, PLATE + 30], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(28))
    ground = Image.composite(Image.new('RGB', (PLATE, PLATE), A.hx('#5552E0')),
                             Image.new('RGB', (PLATE, PLATE), A.hx('#2A2870')), g).convert('RGBA')
    m = Image.new('L', (PLATE, PLATE), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, PLATE - 1, PLATE - 1], radius=16, fill=255)
    pl.paste(ground, (0, 0), m)
    f = os.path.join(os.path.dirname(__file__), 'assets', 'consoles', CONSOLES.get(name, ''))
    if os.path.isfile(f):
        im = Image.open(f).convert('RGBA'); im.thumbnail((PLATE - 22, PLATE - 22), Image.LANCZOS)
        pl.alpha_composite(im, ((PLATE - im.width) // 2, (PLATE - im.height) // 2))
    return pl


def _hw_row(h, week, life, frac_bar, change_a, plate):
    """One hardware row at a moment of the count: plate right, name, total,
    this moment's number and bar, and the change line fading in at the end."""
    w = R - L
    lay = Image.new('RGBA', (w, HW_ROW), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w - 1, HW_ROW - 1], radius=18, fill=A.hx('#1E1D4A') + (232,),
                        outline=A.hx('#3F3DA8') + (255,), width=2)
    lay.alpha_composite(plate, (w - PLATE - 14, (HW_ROW - PLATE) // 2))
    x = w - PLATE - 34                              # right column: name, then the total
    d.text((x, 48), h['name'], font=A.F('Bold', 40), fill=A.INK, anchor='rm')
    d.text((x, 100), f'الإجمالي {S._fmt(life)}', font=A.F('Regular', 26), fill=A.BODY, anchor='rm', **G.AR)
    nf = A.F('Bold', 50)                            # left: this moment's number, the change under it
    d.text((24, 50), S._fmt(round(week)), font=nf, fill=A.INK, anchor='lm')
    d.text((24 + d.textlength(S._fmt(round(week)), font=nf) + 12, 56), 'جهاز', font=A.F('Regular', 26),
           fill=A.BODY, anchor='lm', **G.AR)
    if change_a > 0 and h.get('last'):
        ch = (h['week'] - h['last']) / h['last'] * 100
        col = UP if ch >= 0 else DOWN
        cl = Image.new('RGBA', (w, HW_ROW), (0, 0, 0, 0)); cd = ImageDraw.Draw(cl)
        ty, ct = 100, f'{abs(ch):.0f}% عن الأسبوع الماضي'
        cf = A.F('Medium', 26)
        cd.text((24, ty), ct, font=cf, fill=col, anchor='lm', **G.AR)
        tx = 24 + cd.textlength(ct, font=cf, **G.AR) + 10   # the triangle leads the line, read right to left
        tri = ([(tx, ty + 8), (tx + 18, ty + 8), (tx + 9, ty - 8)] if ch >= 0 else
               [(tx, ty - 8), (tx + 18, ty - 8), (tx + 9, ty + 8)])
        cd.polygon(tri, fill=col)                    # Dubai has no arrows, so it is drawn
        cl.putalpha(cl.getchannel('A').point(lambda v: int(v * change_a)))
        lay.alpha_composite(cl)
    span = x - 24                                   # the bar grows leftward from under the name
    bw = max(8, span * frac_bar)
    d.rounded_rectangle([x - bw, 140, x, 166], radius=11, fill=A.AZURE)
    return lay


def _ease2(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def hw_clip(hw, title, week_label, accent, bg, out, secs=8.0, hold=1.2, count=2.4, fast=False,
            source='فاميتسو (Famitsu)'):
    """The hardware slide as its own clip (Mohammad, 5 Oct 2026): every
    console opens on last week's number and counts to this week's, its bar
    following, and the rows keep sorted by the live numbers, so a console that
    overtakes another slides up past it. The caption reads «الأسبوع الماضي»
    over the opening numbers and «هذا الأسبوع» once the count starts; the
    change on last week fades in when the count lands."""
    fps = 30
    n = int(round(secs * fps))
    base = Image.open(bg).convert('RGBA').resize((W, H))
    _top_line(base, title, week_label, accent, source)
    caps = []
    for t in ('الأسبوع الماضي', 'هذا الأسبوع'):
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        _text(c, (R, HW_Y - 54), t, A.F('Bold', 52), accent, 'rs', ar=True, stroke=5)
        caps.append(c)
    plates = {h['name']: _plate(h['name']) for h in hw}
    top = max(max(h['week'], h.get('last') or h['week']) for h in hw)
    slot = lambda k: HW_Y + k * (HW_ROW + HW_GAP)
    if slot(len(hw)) - HW_GAP > BOT:
        raise ValueError('hardware rows run past the safe zone')
    start = lambda h: h.get('last') or h['week']
    ys = {h['name']: slot(k) for k, h in enumerate(sorted(hw, key=lambda h: -start(h)))}
    proc = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                             '-s', f'{W}x{H}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                            + (RL.DRAFT_ENC if fast else ['-preset', 'slow', '-crf', '16']) + [out],
                            stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        k = _ease2((t - hold) / count)
        cur = {h['name']: start(h) + (h['week'] - start(h)) * k for h in hw}
        order = sorted(hw, key=lambda h: -cur[h['name']])
        for j, h in enumerate(order):                # each row eases toward its live place
            ys[h['name']] += (slot(j) - ys[h['name']]) * 0.2
        fr = base.copy()
        ca = _ease2((t - hold + 0.15) / 0.3)
        for c, a in ((caps[0], 1 - ca), (caps[1], ca)):
            if a > 0.01:
                cc = c.copy(); cc.putalpha(c.getchannel('A').point(lambda v: int(v * a))); fr.alpha_composite(cc)
        chg = _ease2((t - hold - count) / 0.4)
        for h in sorted(hw, key=lambda h: ys[h['name']], reverse=True):   # the row moving up draws on top
            life = h['life'] - h['week'] + cur[h['name']]
            row = _hw_row(h, cur[h['name']], round(life), cur[h['name']] / top, chg, plates[h['name']])
            fr.alpha_composite(row, (L, int(round(ys[h['name']]))))
        proc.stdin.write(fr.convert('RGB').tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError('hardware clip encode failed')
    return out


def reel(rows, week_label, date, out, hardware=(), hook='من تصدّر مبيعات اليابان هذا الأسبوع؟',
         title='الأكثر مبيعًا في اليابان', hw_title='مبيعات الأجهزة في اليابان',
         source='فاميتسو (Famitsu)', theme='gold', hook_secs=3.6, hw_secs=8.0, draft=False):
    accent = G.ACCENTS[theme]
    rows = sorted(rows, key=lambda r: -r['rank'])        # countdown, 10 to 1
    os.makedirs(C.U + SUB, exist_ok=True)
    def up(f):
        dst = f'{SUB}/{os.path.basename(f)}'
        if not os.path.exists(C.U + dst):
            shutil.copy(f, C.U + dst)
        return dst
    tmp = tempfile.mkdtemp(prefix='salesfull-')
    try:
        top4 = sorted(rows, key=lambda r: r['rank'])[:4]
        mosaic([(up(r['shot'][0]), sum(r['shot'][1]) / 2) for r in top4], f'{tmp}/hook.jpg')
        shutil.copy(f'{tmp}/hook.jpg', C.U + f'{SUB}/hook.jpg')
        shots = [(f'{SUB}/hook.jpg', None, hook_secs, (0.5, 0.5))]
        for r in rows:
            shots.append((up(r['shot'][0]), None, _secs(r['rank']), r['shot'][1]))
        starts, end = RL.timeline(shots)
        layers = [(hook_layer(hook, week_label, source, date, theme, f'{tmp}/h.png'), 0, starts[1] + RL.X)]
        for i, r in enumerate(rows, 1):
            z = starts[i + 1] + RL.X if i + 1 < len(starts) else end
            layers.append((entry_layer(r, title, week_label, accent, f'{tmp}/e{i}.png'), starts[i], z))
        RL.montage(shots, f'{tmp}/cut.mp4', fast=draft)
        args = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', f'{tmp}/cut.mp4']
        for p, _, _ in layers:
            args += ['-loop', '1', '-t', f'{end:.2f}', '-i', p]
        fc = ['[0:v]setsar=1,fps=30[v0]']
        for i, (p, a, z) in enumerate(layers, 1):
            fin = f',fade=t=in:st={a:.2f}:d={RL.X}:alpha=1' if a > 0 else ''
            fout = f',fade=t=out:st={z - RL.X:.2f}:d={RL.X}:alpha=1' if z < end - 0.01 else ''
            fc += [f'[{i}:v]format=rgba{fin}{fout}[l{i}]', f'[v{i - 1}][l{i}]overlay=0:0:shortest=1[v{i}]']
        fc.append(f'[v{len(layers)}]format=yuv420p[v]')
        body = f'{tmp}/body.mp4'
        subprocess.run(args + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                       + (RL.DRAFT_ENC if draft else ['-preset', 'slow', '-crf', '16']) + [body], check=True)
        if hardware:                       # the animated hardware slide, crossfaded on
            bg = [(up(r['shot'][0]), sum(r['shot'][1]) / 2) for r in sorted(rows, key=lambda r: r['rank'])[:6]]
            mosaic(bg, f'{tmp}/hw-bg.jpg', cols=2, rows=3, dim=0.55)
            hw_clip(hardware, hw_title, week_label, accent, f'{tmp}/hw-bg.jpg', f'{tmp}/hw.mp4', hw_secs,
                    fast=draft, source=source)
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-i', f'{tmp}/hw.mp4',
                            '-filter_complex', f'[0:v]settb=AVTB,fps=30[a];[1:v]settb=AVTB,fps=30[b];'
                            f'[a][b]xfade=transition=fade:duration={RL.X}:offset={end - RL.X:.3f}[v]',
                            '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                           + (RL.DRAFT_ENC if draft else ['-preset', 'slow', '-crf', '16']) + [f'{tmp}/all.mp4'], check=True)
            body = f'{tmp}/all.mp4'
            end += hw_secs - RL.X
        if draft:
            done = os.path.splitext(out)[0] + '-draft.mp4'
            shutil.move(body, done)
            return done, starts, end
        return outro.append(body, out, 'stats', accent=accent), starts, end
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
