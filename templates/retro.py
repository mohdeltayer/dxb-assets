# "On this day" retro Reel (Mohammad, 10 to 11 Oct 2026). The top stays as approved: gold chip, date, "صدرت <game>".
# A real CRT on a cabinet (Pexels 16707770, Oktay Köseoğlu, Pexels License) plays the game's footage on its own screen.
# Under it, first a fact sheet (game, developer, publisher, console, with the box art), then the fun facts one at a time.
# 11 Oct: bigger type to fill the lower half, and the console's own colours on pixel-edged label blocks beside each row and
# each fact, so the look matches the machine, not only the 8-bit jingle (CONSOLES). The safe-zone floor stays at 1480.
#   import retro
#   retro.render(dict(clip=..., start=2.0, dur=27.5, date='11 أكتوبر 1999', game='Jet Force Gemini', console='n64',
#                     box='box.jpg', sheet=[('اللعبة', 'Jet Force Gemini'), ...], facts=[[line, line, line], ...]), 'out.mp4')
# then outro.append(out, final, style='retro').
import os, sys, shutil, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import fast_ar as A, reel as RL

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, S = 1080, 1920, 1.06                       # S: the frame is drawn 6% larger for the slow push-in
SW, SH = int(W * S), int(H * S)
R, L, FLOOR = 910, 96, 1480                       # Reels safe zone (ig_ar.SAFE_*)
GROUND, INK, BODY = (20, 19, 50), (244, 243, 255), (201, 200, 230)
GOLD2 = A.THEMES['gold'][1]
AR = A.AR
PHOTO = '/mnt/user-data/uploads/scout/tv1-pexels16707770.jpg'
K = 0.34                                          # photo scale: the TV (source x 750 to 2940, top y 594) centred, top at y 572
OX, OY = 540 - 1845 * K, 572 - 594 * K
GLASS = (900, 720, 2420, 1830)                    # the screen in the photo
WASH = 1100                                       # dark wash over the cabinet starts here so the text reads
Y0 = 1140                                         # the lower area runs from here to FLOOR

# Each console's own colours, in the order the blocks use them (rows top to bottom, facts one by one).
# No pink: the brand rule covers our own blocks, so PlayStation takes its logo's colours, not the square button.
CONSOLES = {
    'n64':      dict(name='Nintendo 64', mark='n64-mark.png', colours=[(228, 32, 46), (255, 194, 14), (0, 166, 81), (0, 97, 175)]),
    'nes':      dict(name='NES', colours=[(196, 0, 43), (169, 169, 169), (110, 110, 118), (230, 230, 230)]),
    'famicom':  dict(name='Famicom', colours=[(176, 30, 44), (212, 175, 90), (240, 236, 224), (176, 30, 44)]),
    'snes':     dict(name='Super Nintendo', colours=[(79, 67, 174), (154, 143, 216), (208, 2, 27), (245, 196, 0)]),
    'sfc':      dict(name='Super Famicom', colours=[(208, 2, 27), (245, 196, 0), (45, 159, 74), (42, 79, 184)]),
    'gameboy':  dict(name='Game Boy', colours=[(155, 188, 15), (139, 172, 15), (48, 98, 48), (155, 188, 15)]),
    'gba':      dict(name='Game Boy Advance', colours=[(75, 63, 158), (124, 112, 210), (75, 63, 158), (124, 112, 210)]),
    'gamecube': dict(name='GameCube', colours=[(106, 90, 205), (60, 180, 75), (230, 60, 50), (245, 196, 0)]),
    'ps1':      dict(name='PlayStation', colours=[(230, 0, 18), (247, 198, 0), (0, 160, 160), (58, 76, 168)]),
    'ps2':      dict(name='PlayStation 2', colours=[(0, 55, 145), (40, 120, 220), (0, 55, 145), (40, 120, 220)]),
    'megadrive': dict(name='Mega Drive', colours=[(230, 0, 18), (30, 91, 198), (170, 170, 170), (230, 0, 18)]),
    'saturn':   dict(name='Sega Saturn', colours=[(30, 91, 198), (230, 0, 18), (245, 196, 0), (0, 166, 81)]),
    'dreamcast': dict(name='Dreamcast', colours=[(242, 107, 29), (0, 96, 168), (242, 107, 29), (0, 96, 168)]),
    'xbox':     dict(name='Xbox', colours=[(16, 124, 16), (155, 240, 11), (16, 124, 16), (155, 240, 11)]),
}

def sc(v): return int(round(v * S))
def fr(x, y): return OX + x * K, OY + y * K
def lum(c): return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255
def opt(t): return {} if t.isascii() else AR

def block(d, box, c, px=6):
    """A pixel-edged menu block: notched corners, a light top-left edge and a dark bottom-right edge, as on a cartridge-era UI."""
    x0, y0, x1, y1 = box
    hi = tuple(min(255, int(v + (255 - v) * 0.45)) for v in c); lo = tuple(int(v * 0.55) for v in c)
    d.rectangle([x0 + px, y0, x1 - px, y1], fill=lo); d.rectangle([x0, y0 + px, x1, y1 - px], fill=lo)
    d.rectangle([x0 + px, y0, x1 - px, y1 - px], fill=hi); d.rectangle([x0, y0 + px, x1 - px, y1 - px], fill=hi)
    d.rectangle([x0 + px, y0 + px, x1 - px, y1 - px], fill=c)
    d.rectangle([x0 + px, y0 + px // 2 + px, x1 - 2 * px, y0 + px + px // 2 + px], fill=hi)   # a short shine line

def chip(d, right, y, text, c, size, pad=20, h=None):
    f = A.F('Bold', size); w = d.textlength(text, font=f, **AR) + 2 * pad; h = h or int(size * 1.5)
    block(d, [right - w, y, right, y + h], c)
    d.text((right - pad, y + h / 2 + 1), text, font=f, fill=GROUND if lum(c) > 0.5 else INK, anchor='rm', **AR)
    return w

def scene():
    im = Image.new('RGB', (SW, SH), GROUND)
    ph = Image.open(PHOTO).convert('RGB'); k = K * S
    ph = ph.resize((int(ph.width * k), int(ph.height * k)), Image.LANCZOS)
    x, y = sc(OX), sc(OY)
    a = Image.new('L', ph.size, 255); d = ImageDraw.Draw(a)
    fade = sc(200)                                            # the photo fades in from the ground above the TV
    for i in range(fade): d.line([(0, i), (ph.width, i)], fill=int(255 * (i / fade) ** 1.4))
    im.paste(ph, (x, y), a)
    im = im.convert('RGBA')
    g = Image.new('L', (1, SH), 0)
    for yy in range(SH):
        t = (yy - sc(WASH)) / sc(160)
        g.putpixel((0, yy), int(232 * min(1, max(0, t)) ** 0.9))
    wash = Image.new('RGBA', (SW, SH), GROUND + (255,)); wash.putalpha(g.resize((SW, SH))); im.alpha_composite(wash)
    x0, y0 = fr(*GLASS[:2]); x1, y1 = fr(*GLASS[2:])           # cut the glass out; the footage plays behind it
    m = Image.new('L', im.size, 255)
    ImageDraw.Draw(m).rounded_rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], sc(62), fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(3))))
    return im, (sc(x0), sc(y0), sc(x1) - sc(x0), sc(y1) - sc(y0))

def screenfx(w, h, out):
    fx = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
    for y in range(0, h, 3): d.line([0, y, w, y], fill=(0, 0, 0, 38))           # scanlines
    vg = Image.new('L', (w, h), 0); ImageDraw.Draw(vg).rounded_rectangle([sc(12), sc(12), w - sc(12), h - sc(12)], sc(40), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(sc(30)))
    dark = Image.new('RGBA', (w, h), (0, 0, 0, 255)); dark.putalpha(ImageChops.invert(vg).point(lambda v: int(v * 0.8))); fx.alpha_composite(dark)
    gl = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([int(w * 0.62), int(h * -0.1), int(w * 1.05), int(h * 0.3)], fill=(255, 255, 255, 40))
    fx.alpha_composite(gl.filter(ImageFilter.GaussianBlur(sc(20)))); fx.save(out)

def top(spec, out):
    cols = CONSOLES[spec['console']]['colours']
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    RL._waves(t, 290, 'gold', 11, alpha=0.6)
    b = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); RL._waves(b, 420, 'gold', 23, alpha=0.5)
    t.alpha_composite(b.transpose(Image.FLIP_TOP_BOTTOM), (0, H - 420))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle([R - 300, 300, R, 366], 12, fill=GOLD2)
    d.text((R - 24, 335), 'في مثل هذا اليوم', font=A.F('Bold', 44), fill=GROUND, anchor='rm', **AR)
    x = R - 300 - 22                                          # the console's colours as four pixel squares beside the chip
    for c in reversed(cols):
        block(d, [x - 30, 318, x, 348], c, px=4); x -= 38
    d.text((R, 386), spec['date'], font=A.F('Bold', 66), fill=INK, anchor='ra', **AR)
    d.text((R, 474), f"صدرت {spec['game']}", font=A.F('Bold', 54), fill=INK, anchor='ra', **AR)
    t.save(out)

def sheet(spec, out):
    con = CONSOLES[spec['console']]; cols = con['colours']
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    box = Image.open(spec['box']).convert('RGBA')
    bh = spec.get('box_h', 170); box = box.resize((int(box.width * bh / box.height), bh), Image.LANCZOS)
    bw = box.width; by = Y0 + 8
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([L + 8, by + 12, L + bw + 8, by + bh + 12], fill=(0, 0, 0, 150))
    t.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))            # the box art sits in a pixel frame in the console's first colour
    block(ImageDraw.Draw(frame), [L - 8, by - 8, L + bw + 8, by + bh + 8], cols[0], px=6); t.alpha_composite(frame)
    t.alpha_composite(box, (L, by))
    val, sub, csize, step = A.F('Bold', 46), A.F('Medium', 34), 30, 72
    cw = max(d.textlength(k, font=A.F('Bold', csize), **AR) for k, _ in spec['sheet']) + 40    # every label block the same width
    vx0 = R - cw - 20; room = vx0 - (L + bw + 30)
    y = Y0
    for i, (k, v) in enumerate(spec['sheet']):
        c = cols[i % len(cols)]; ch = 52
        f = A.F('Bold', csize); block(d, [R - cw, y + 2, R, y + 2 + ch], c)
        d.text((R - cw / 2, y + 2 + ch / 2 + 1), k, font=f, fill=GROUND if lum(c) > 0.5 else INK, anchor='mm', **AR)
        vx = vx0
        if v == con['name'] and con.get('mark'):
            mark = Image.open(os.path.join(HERE, 'assets', 'retro', con['mark'])).convert('RGBA'); mh = 46
            mark = mark.resize((int(mark.width * mh / mark.height), mh), Image.LANCZOS)
            t.alpha_composite(mark, (int(vx - mark.width), y + 6)); vx -= mark.width + 14
            assert d.textlength(v, font=val) <= room - mark.width - 14, ('too wide', v)
        if isinstance(v, list):                                 # a two-line value in the smaller weight
            for j, line in enumerate(v):
                assert d.textlength(line, font=sub, **opt(line)) <= room, ('too wide', line)
                d.text((vx, y + 6 + j * 46), line, font=sub, fill=INK, anchor='ra', **opt(line))
            y += 46 * len(v) + 20
        else:
            assert d.textlength(v, font=val, **opt(v)) <= room, ('too wide', v)
            d.text((vx, y), v, font=val, fill=INK, anchor='ra', **opt(v)); y += step
    bb = t.getbbox(); assert bb[0] >= L - 30 and bb[3] <= FLOOR, ('sheet leaves the safe zone', bb)
    t.save(out)

def fact(spec, i, out):
    lines = spec['facts'][i]; c = CONSOLES[spec['console']]['colours'][i % 4]
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    chip(d, R, Y0, 'هل تعلم؟', c, 36)
    f, step, top_ = A.F('Medium', 54), 78, Y0 + 84
    for j in range(len(lines) * 2):                             # a column of pixel squares beside the lines, in the same colour
        yy = top_ + 10 + j * 39
        block(d, [R - 22, yy, R, yy + 22], c if j % 2 == 0 else tuple(int(v * 0.6) for v in c), px=4)
    for j, s in enumerate(lines):
        assert d.textlength(s, font=f, **opt(s)) <= R - 46 - L, ('too wide', s)
        d.text((R - 46, top_ + j * step), s, font=f, fill=INK, anchor='ra', **opt(s))
    bb = t.getbbox(); assert bb[0] >= L and bb[3] <= FLOOR, ('outside the safe zone', bb, lines)
    t.save(out)

def render(spec, out, push=0.03, sheet_secs=6.0):
    clip, start, dur = spec['clip'], spec['start'], spec['dur']
    tmp = tempfile.mkdtemp(prefix='retro-')
    try:
        base, (x0, y0, w, h) = scene(); base.save(f'{tmp}/base.png')
        screenfx(w, h, f'{tmp}/fx.png'); top(spec, f'{tmp}/top.png'); sheet(spec, f'{tmp}/s0.png')
        segs = [(f'{tmp}/s0.png', 0, sheet_secs)]
        per = (dur - sheet_secs) / len(spec['facts'])
        for i, lines in enumerate(spec['facts']):
            fact(spec, i, f'{tmp}/s{i + 1}.png')
            a, b = sheet_secs + i * per, sheet_secs + (i + 1) * per
            need = len(' '.join(lines)) / 14 + 0.5              # every fact stays long enough to read once
            assert b - a >= need, ('fact too fast', i, b - a, need)
            segs.append((f'{tmp}/s{i + 1}.png', a, b))
        cy = (y0 + h / 2) / SH; z = f"({1 / S}/(1-{push}*t/{dur}))"
        ins = ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/base.png', '-ss', str(start), '-t', str(dur), '-i', clip,
               '-loop', '1', '-t', str(dur), '-i', f'{tmp}/fx.png', '-loop', '1', '-t', str(dur), '-i', f'{tmp}/top.png']
        cx0, cy0, cw, ch = spec.get('crop', (10, 5, 330, 216))
        fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos,eq=saturation=1.25:contrast=1.15:brightness=0.05,format=rgba[g];"
              f"[g][2:v]overlay=0:0[gs];color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay={x0}:{y0}[sc];"
              f"[0:v]format=rgba[bg];[sc][bg]overlay=0:0[full];"
              f"[full]scale=w='ceil({SW}*{z}/2)*2':h='ceil({SH}*{z}/2)*2':eval=frame:flags=bicubic,"
              f"crop={W}:{H}:x='(iw-{W})/2':y='(ih-{H})*{cy}',format=rgba[cam];[cam][3:v]overlay=0:0[v0];")
        for i, (n, a, b) in enumerate(segs):
            ins += ['-loop', '1', '-t', str(dur), '-i', n]
            fi = f"fade=t=in:st={max(0, a - 0.01)}:d=0.35:alpha=1," if a > 0 else ''
            fo = f"fade=t=out:st={b - 0.35}:d=0.35:alpha=1" if b < dur else 'null'
            fc += f"[{4 + i}:v]format=rgba,{fi}{fo}[s{i}];[v{i}][s{i}]overlay=0:0[v{i + 1}];"
        fc += f"[v{len(segs)}]format=yuv420p[v]"
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', *ins, '-filter_complex', fc, '-map', '[v]', '-map', '1:a?',
                        '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-t', str(dur), out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def stills(spec, outdir):
    """The overlay layers alone, for a quick look before a render."""
    os.makedirs(outdir, exist_ok=True)
    top(spec, f'{outdir}/top.png'); sheet(spec, f'{outdir}/s0.png')
    for i in range(len(spec['facts'])): fact(spec, i, f'{outdir}/s{i + 1}.png')
    base, _ = scene(); base = base.resize((W, H), Image.LANCZOS)          # the first frame shows the whole drawing at 1/S
    for n in ['s0'] + [f's{i + 1}' for i in range(len(spec['facts']))]:
        im = Image.new('RGBA', (W, H), (11, 13, 16, 255)); im.alpha_composite(base)
        im.alpha_composite(Image.open(f'{outdir}/top.png')); im.alpha_composite(Image.open(f'{outdir}/{n}.png'))
        im.convert('RGB').save(f'{outdir}/look-{n}.jpg', quality=90)

JFG = dict(clip='/mnt/user-data/uploads/retro-jfg-trailer.mp4', start=2.0, dur=27.5, date='11 أكتوبر 1999',
           game='Jet Force Gemini', console='n64', box='/mnt/user-data/uploads/retro-jfg-box.jpg',
           sheet=[('اللعبة', 'Jet Force Gemini'), ('التطوير', 'رير (Rare)'),
                  ('النشر', ['رير في أمريكا وأوروبا', 'نينتيندو (Nintendo) في اليابان']), ('الجهاز', 'Nintendo 64')],
           facts=[["صدرت في اليابان باسم Star Twins", "إذ رأت نينتيندو", "أن اسمها صعب النطق هناك"],
                  ["للوصول إلى المرحلة الأخيرة", "يجب إنقاذ مخلوقات Tribals كلها", "وعددها 282"],
                  ["كان بطلاها في البداية طفلين", "ثم جُعلا أكبر سنًا لقلق نينتيندو", "من طفلين يقتلان كل هذه المخلوقات"]])

if __name__ == '__main__':
    stills(JFG, sys.argv[1] if len(sys.argv) > 1 else '.')
