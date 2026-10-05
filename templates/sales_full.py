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
dimmed mosaic of the week's games, then the end card with the stats
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
    size = 64
    while d.textlength(r['title'], font=A.F('Bold', size)) > R - L and size > 40:
        size -= 2
    ty = cy - 34
    _text(lay, (R, ty), r['title'], A.F('Bold', size), A.INK, 'rs')
    if d.textlength(r['title'], font=A.F('Bold', size)) > R - L:
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


def hw_layer(hw, title, week_label, accent, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _top_line(lay, title, week_label, accent)
    widest = max(h['week'] for h in hw)
    y = 560
    for h in hw:
        row = S._hw_row(h, 1.0, h['week'], widest)
        lay.alpha_composite(row, (L, y)); y += S.ROW_H + 22
    if y > BOT:
        raise ValueError('hardware rows run past the safe zone')
    lay.save(path); return path


def reel(rows, week_label, date, out, hardware=(), hook='من تصدّر مبيعات اليابان هذا الأسبوع؟',
         title='الأكثر مبيعًا في اليابان', hw_title='مبيعات الأجهزة في اليابان',
         source='فاميتسو (Famitsu)', theme='gold', hook_secs=3.6, hw_secs=6.5, draft=False):
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
        if hardware:
            bg = [(up(r['shot'][0]), sum(r['shot'][1]) / 2) for r in sorted(rows, key=lambda r: r['rank'])[:6]]
            mosaic(bg, C.U + f'{SUB}/hw-bg.jpg', cols=2, rows=3, dim=0.55)
            shots.append((f'{SUB}/hw-bg.jpg', None, hw_secs, (0.5, 0.5)))
        starts, end = RL.timeline(shots)
        layers = [(hook_layer(hook, week_label, source, date, theme, f'{tmp}/h.png'), 0, starts[1] + RL.X)]
        for i, r in enumerate(rows, 1):
            z = starts[i + 1] + RL.X if i + 1 < len(starts) else end
            layers.append((entry_layer(r, title, week_label, accent, f'{tmp}/e{i}.png'), starts[i], z))
        if hardware:
            layers.append((hw_layer(hardware, hw_title, week_label, accent, f'{tmp}/hw.png'), starts[-1], end))
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
        if draft:
            done = os.path.splitext(out)[0] + '-draft.mp4'
            shutil.move(body, done)
            return done, starts, end
        return outro.append(body, out, 'stats', accent=accent), starts, end
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
