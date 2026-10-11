# "On this day" retro Reel (Mohammad, 10 to 11 Oct 2026). The top: the console-skinned chip, date, "صدرت <game>".
# A real CRT on a cabinet (Pexels 16707770, Oktay Köseoğlu, Pexels License) plays the game's footage on its own screen.
# Under it, first a fact sheet (game, developer, publisher, console, with the box art), then the fun facts one at a time.
# 11 Oct: bigger type to fill the lower half, and the console's own colours on pixel-edged label blocks beside each row and
# each fact, so the look matches the machine, not only the 8-bit jingle (CONSOLES). The safe-zone floor stays at 1480.
#   import retro
#   retro.render(dict(clip=..., start=2.0, dur=27.5, date='11 أكتوبر 1999', game='Jet Force Gemini', console='n64',
#                     box='box.jpg', sheet=[('اللعبة', 'Jet Force Gemini'), ...], facts=[[line, line, line], ...]), 'out.mp4')
# then outro.append(out, final, style='retro').
import math, os, sys, shutil, subprocess, tempfile
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
    # Atari 2600 (VCS): the woodgrain front, the Atari red-orange and the silver switches. Big in the Gulf in the late 70s and 80s.
    'atari2600': dict(name='Atari 2600', colours=[(228, 49, 38), (245, 130, 32), (150, 92, 48), (192, 195, 199)]),
    # NES (the Western grey box): light grey, the logo and button red, charcoal, pale grey.
    'nes':      dict(name='NES', colours=[(196, 0, 43), (184, 184, 188), (92, 92, 100), (226, 226, 230)]),
    # Famicom (Japan): cream body, the deep maroon trim, the gold controller faces.
    'famicom':  dict(name='Famicom', colours=[(150, 28, 40), (212, 172, 84), (238, 230, 210), (150, 28, 40)]),
    'mastersystem': dict(name='Master System', colours=[(230, 0, 18), (30, 91, 198), (200, 200, 205), (230, 0, 18)]),
    'snes':     dict(name='Super Nintendo', colours=[(79, 67, 174), (154, 143, 216), (190, 190, 196), (110, 98, 200)]),
    'sfc':      dict(name='Super Famicom', colours=[(208, 2, 27), (245, 196, 0), (45, 159, 74), (42, 79, 184)]),
    'megadrive': dict(name='Mega Drive', colours=[(230, 0, 18), (30, 91, 198), (170, 170, 170), (230, 0, 18)]),
    'gameboy':  dict(name='Game Boy', handheld=True, colours=[(60, 170, 255), (250, 214, 60), (245, 140, 30), (196, 198, 204)]),
    'gamegear': dict(name='Game Gear', handheld=True, colours=[(30, 91, 198), (230, 0, 18), (200, 200, 205), (245, 196, 0)]),
    'n64':      dict(name='Nintendo 64', mark='n64-mark.png', colours=[(228, 32, 46), (255, 194, 14), (0, 166, 81), (0, 97, 175)]),
    'ps1':      dict(name='PlayStation', colours=[(230, 0, 18), (247, 198, 0), (0, 160, 160), (58, 76, 168)]),
    'saturn':   dict(name='Sega Saturn', colours=[(30, 91, 198), (230, 0, 18), (245, 196, 0), (0, 166, 81)]),
    'dreamcast': dict(name='Dreamcast', colours=[(242, 107, 29), (0, 96, 168), (242, 107, 29), (0, 96, 168)]),
    'gba':      dict(name='Game Boy Advance', handheld=True, colours=[(75, 63, 158), (124, 112, 210), (75, 63, 158), (124, 112, 210)]),
    'ps2':      dict(name='PlayStation 2', colours=[(0, 55, 145), (40, 120, 220), (0, 55, 145), (40, 120, 220)]),
    'gamecube': dict(name='GameCube', colours=[(106, 90, 205), (60, 180, 75), (230, 60, 50), (245, 196, 0)]),
    'xbox':     dict(name='Xbox', colours=[(16, 124, 16), (155, 240, 11), (16, 124, 16), (155, 240, 11)]),
}

# The «في مثل هذا اليوم» chip and the wave lines borrow each console's own look (Mohammad, 11 Oct 2026: the gold chip
# did not blend). fill/rim/ink colour the chip, grain/lcd texture it, trim is the artifact beside it, waves the two wave colours.
SKINS = {
    'atari2600': dict(ground=(40, 25, 16), motif='wood', fill=(122, 74, 36), grain=True, rim=(192, 195, 199), ink=(246, 236, 214),
                      trim=('bars', [(228, 49, 38), (245, 130, 32), (250, 196, 40)]), waves=((228, 49, 38), (245, 130, 32))),
    'nes':       dict(ground=(28, 28, 32), fill=(38, 38, 42), rim=(184, 184, 188), ink=(240, 240, 244), band=(196, 0, 43), motif='grid',
                      trim=('buttons', [(196, 0, 43), (196, 0, 43)]), waves=((196, 0, 43), (184, 184, 188))),
    'famicom':   dict(ground=(54, 14, 22), fill=(212, 172, 84), rim=(150, 28, 40), ink=(110, 20, 30),
                      trim=('buttons', [(150, 28, 40), (150, 28, 40)]), waves=((150, 28, 40), (212, 172, 84))),
    'mastersystem': dict(ground=(244, 244, 246), motif='grid', fill=(30, 30, 34), rim=(230, 0, 18), ink=(244, 244, 248),
                      trim=('grid', [(230, 0, 18)]), waves=((30, 91, 198), (200, 200, 205))),
    'snes':      dict(ground=(38, 33, 62), fill=(200, 200, 206), rim=(79, 67, 174), ink=(60, 50, 140),
                      trim=('buttons', [(79, 67, 174), (79, 67, 174), (154, 143, 216), (154, 143, 216)]), waves=((79, 67, 174), (154, 143, 216))),
    'sfc':       dict(ground=(34, 34, 40), fill=(200, 200, 206), rim=(110, 110, 120), ink=(40, 40, 48),
                      trim=('diamond', [(45, 159, 74), (245, 196, 0), (42, 79, 184), (208, 2, 27)]), waves=((245, 196, 0), (45, 159, 74))),
    'megadrive': dict(ground=(14, 14, 17), motif='grid', fill=(30, 30, 34), rim=(230, 0, 18), ink=(232, 190, 80),
                      trim=('ring', [(230, 0, 18)]), waves=((230, 0, 18), (232, 190, 80))),
    'gameboy':   dict(ground=(7, 7, 11), fill=(196, 198, 204), brushed=True, rim=(92, 94, 104), ink=(58, 60, 70),
                      trim=('led', [(228, 30, 40)]), waves=None, motif='rays'),          # the 1989 box: black, silver band, rays
    'gamegear':  dict(ground=(12, 12, 16), fill=(34, 34, 40), rim=(30, 91, 198), ink=(244, 244, 248),
                      trim=('buttons', [(30, 91, 198), (30, 91, 198)]), waves=((30, 91, 198), (200, 200, 205))),
    'n64':       dict(ground=(28, 28, 34), fill=(40, 40, 46), rim=(110, 110, 120), ink=(244, 243, 255),
                      trim=('squares', [(228, 32, 46), (255, 194, 14), (0, 166, 81), (0, 97, 175)]), waves=((255, 194, 14), (0, 166, 81))),
    'ps1':       dict(ground=(36, 36, 43), fill=(196, 196, 202), rim=(110, 110, 120), ink=(40, 40, 48),
                      trim=('symbols', [(0, 160, 120), (230, 0, 18), (58, 110, 200), (150, 150, 160)]), waves=((247, 198, 0), (0, 160, 160))),
    'saturn':    dict(ground=(18, 19, 27), fill=(36, 36, 42), rim=(30, 91, 198), ink=(244, 244, 248),
                      trim=('squares', [(30, 91, 198), (230, 0, 18), (245, 196, 0), (0, 166, 81)]), waves=((30, 91, 198), (245, 196, 0))),
    'dreamcast': dict(ground=(246, 246, 248), fill=(236, 236, 240), rim=(170, 170, 178), ink=(40, 40, 48),
                      trim=('swirl', [(242, 107, 29)]), waves=((242, 107, 29), (0, 96, 168))),
    'gba':       dict(ground=(30, 24, 74), fill=(75, 63, 158), rim=(124, 112, 210), ink=(244, 243, 255),
                      trim=('buttons', [(124, 112, 210), (124, 112, 210)]), waves=((75, 63, 158), (124, 112, 210))),
    'ps2':       dict(ground=(8, 14, 36), motif='lines', fill=(20, 24, 40), rim=(40, 120, 220), ink=(244, 244, 248),
                      trim=('symbols', [(0, 160, 120), (230, 0, 18), (58, 110, 200), (150, 150, 160)]), waves=((0, 55, 145), (40, 120, 220))),
    'gamecube':  dict(ground=(34, 26, 74), fill=(106, 90, 205), rim=(60, 50, 140), ink=(244, 243, 255),
                      trim=('buttons', [(60, 180, 75), (230, 60, 50), (245, 196, 0)]), waves=((106, 90, 205), (60, 180, 75))),
    'xbox':      dict(ground=(10, 22, 11), fill=(22, 28, 22), rim=(16, 124, 16), ink=(200, 250, 120),
                      trim=('jewel', [(16, 124, 16), (155, 240, 11)]), waves=((16, 124, 16), (155, 240, 11))),
}

DARK_TEXT = (24, 24, 30)
def light(key): return lum(SKINS[key]['ground']) > 0.6
def txt(key): return DARK_TEXT if light(key) else INK          # white box, white ground, dark type

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

def motif(kind, ground):
    """The console box's own background pattern, drawn at frame scale: kept to the bands above the TV and below
    the safe floor so the sheet and facts sit on plain ground."""
    m = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    if kind == 'rays':                                          # Game Boy box: yellow and orange rays, bright near the centre
        import numpy as np
        cx, cy = SW / 2, sc(900)
        for i in range(44):
            a0 = i * 2 * math.pi / 44 + 0.03; a1 = a0 + 0.03 + 0.018 * (i % 3)
            c = [(255, 214, 60), (245, 140, 30), (255, 236, 150)][i % 3]
            r = sc(2400)
            d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=c + (255,))
        yy, xx = np.mgrid[0:SH, 0:SW]
        dist = np.hypot(xx - cx, (yy - cy) * 0.8) / sc(1000)
        fall = np.clip(0.62 - 0.5 * dist, 0.07, 0.62)
        m.putalpha(Image.fromarray((np.array(m.split()[3]) * fall).astype('uint8')))
    elif kind == 'grid':                                        # NES and Mega Drive black boxes: a fine grey grid
        gc = (30, 30, 36, 40) if lum(ground) > 0.6 else (150, 150, 160, 46)
        for x in range(0, SW, sc(36)): d.line([(x, 0), (x, SH)], fill=gc, width=sc(2))
        for y in range(0, SH, sc(36)): d.line([(0, y), (SW, y)], fill=gc, width=sc(2))
    elif kind == 'wood':                                        # Atari: the woodgrain front
        for i in range(0, SH, sc(9)):
            pts = [(x, i + sc(4) * math.sin(x / sc(90) + i * 0.013)) for x in range(0, SW + 20, 20)]
            d.line(pts, fill=(20, 10, 4, 70), width=sc(3))
    elif kind == 'lines':                                       # PS2 boxes: fine horizontal blue lines
        for y in range(0, SH, sc(10)): d.line([(0, y), (SW, y)], fill=(40, 120, 220, 40), width=sc(2))
    keep = Image.new('L', (1, SH), 0)                           # full in the top band and the bottom band, clear between
    for y in range(SH):
        yy = y / S
        v = 1 if yy < 560 else max(0, 1 - (yy - 560) / 90) if yy < 650 else 0 if yy < 1490 else min(1, (yy - 1490) / 110)
        keep.putpixel((0, y), int(255 * v))
    m.putalpha(ImageChops.multiply(m.split()[3], keep.resize((SW, SH))))
    return m

def scene(ground=GROUND, kind=None):
    """The CRT photo on the console's dark ground (Mohammad, 11 Oct 2026: the ground matches the console, not indigo)."""
    im = Image.new('RGB', (SW, SH), ground)
    pat = motif(kind, ground) if kind else None
    if pat: im = im.convert('RGBA'); im.alpha_composite(pat); im = im.convert('RGB')
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
    wash = Image.new('RGBA', (SW, SH), ground + (255,)); wash.putalpha(g.resize((SW, SH))); im.alpha_composite(wash)
    if pat: im.alpha_composite(pat)                             # the pattern again over the wash, in the bottom band only
    x0, y0 = fr(*GLASS[:2]); x1, y1 = fr(*GLASS[2:])           # cut the glass out; the footage plays behind it
    m = Image.new('L', im.size, 255)
    ImageDraw.Draw(m).rounded_rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], sc(62), fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(3))))
    return im, (sc(x0), sc(y0), sc(x1) - sc(x0), sc(y1) - sc(y0))

# Handhelds sit on a desk, not on the TV (Mohammad, 11 Oct 2026). Top-down desk photo from the media scout's package
# (Unsplash WW8jBak7bo), the handheld's own product shot laid on it, the footage on its screen.
DESK = '/mnt/user-data/uploads/scene-desk-3-unsplash-WW8jBak7bo.jpg'
HANDHELDS = {
    # photo, screen corners in the photo (tl, tr, br, bl), the device's width on the frame, and the DMG green screen
    'gameboy': dict(photo='/mnt/user-data/uploads/retro-gameboy.jpg', screen=[(1329, 640), (2076, 841), (1788, 1618), (1063, 1389)],
                    width=470, top=584, dmg=True),
}

def desk_scene(ground, kind, key):
    """The desk under the text bands, the handheld on it with its screen cut out. Returns the scene and the screen's
    centre, size and angle on the drawn (S-scaled) frame."""
    hh = HANDHELDS.get(key)
    if not hh:
        raise ValueError(f"{CONSOLES[key]['name']}: no handheld photo yet for the desk scene")
    im = Image.new('RGB', (SW, SH), ground)
    pat = motif(kind, ground) if kind else None
    if pat: im = im.convert('RGBA'); im.alpha_composite(pat); im = im.convert('RGB')
    desk = Image.open(DESK).convert('RGB')                     # a vertical slice of the desk, from y 560 down
    top_y = sc(560); hgt = SH - top_y; wid = SW
    k = hgt / desk.height; sw = int(wid / k); x0 = (desk.width - sw) // 2
    desk = desk.crop((x0, 0, x0 + sw, desk.height)).resize((wid, hgt), Image.LANCZOS)
    desk = Image.eval(desk, lambda v: int(v * 0.8))
    a = Image.new('L', desk.size, 255); d = ImageDraw.Draw(a)
    fade = sc(160)
    for i in range(fade): d.line([(0, i), (desk.width, i)], fill=int(255 * (i / fade) ** 1.4))
    im.paste(desk, (0, top_y), a)
    ImageDraw.Draw(im).rectangle([0, sc(1420), SW, SH], fill=ground)   # nothing of the desk under the caption area
    im = im.convert('RGBA')
    if pat: im.alpha_composite(pat)
    g = Image.new('L', (1, SH), 0)                             # the same wash as the TV scene, so the sheet reads
    for yy in range(SH):
        t = (yy - sc(WASH)) / sc(160)
        g.putpixel((0, yy), int(250 * min(1, max(0, t)) ** 0.9))
    wash = Image.new('RGBA', (SW, SH), ground + (255,)); wash.putalpha(g.resize((SW, SH)))
    # the handheld: cut from its white product background, screen cut out
    src = Image.open(hh['photo']).convert('RGB')
    import numpy as np
    arr = np.array(src).astype(int)
    white = (arr.min(axis=2) > 236).astype('uint8') * 255
    wm = Image.fromarray(white).copy(); ImageDraw.floodfill(wm, (2, 2), 128); ImageDraw.floodfill(wm, (src.width - 3, src.height - 3), 128)
    body = wm.point(lambda v: 0 if v == 128 else 255).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    scr = Image.new('L', src.size, 0); ImageDraw.Draw(scr).polygon(hh['screen'], fill=255)
    body = ImageChops.subtract(body, scr.filter(ImageFilter.GaussianBlur(2)))
    bb = body.getbbox(); src, body = src.crop(bb), body.crop(bb)
    kk = sc(hh['width']) / src.width
    dev = src.resize((int(src.width * kk), int(src.height * kk)), Image.LANCZOS).convert('RGBA')
    dev.putalpha(body.resize(dev.size, Image.LANCZOS))
    dx, dy = (SW - dev.width) // 2, sc(hh['top'])
    sh = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))             # a soft shadow on the desk
    sm = Image.new('L', (SW, SH), 0); sm.paste(dev.split()[3], (dx + sc(18), dy + sc(26)))
    sh.putalpha(sm.point(lambda v: int(v * 0.6))); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(sc(16))))
    im.alpha_composite(wash)
    hole = Image.new('L', (SW, SH), 0); hole.paste(dev.split()[3], (dx, dy))
    im.alpha_composite(dev, (dx, dy))
    # the frame is opaque except the screen: punch the screen out of the whole scene
    q = [((x - bb[0]) * kk + dx, (y - bb[1]) * kk + dy) for x, y in hh['screen']]
    m = Image.new('L', (SW, SH), 255); ImageDraw.Draw(m).polygon(q, fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(1.5))))
    (tlx, tly), (trx, try_), (brx, bry), (blx, bly) = q
    w = math.hypot(trx - tlx, try_ - tly); h = math.hypot(blx - tlx, bly - tly)
    ang = math.atan2(try_ - tly, trx - tlx)
    cx = (tlx + trx + brx + blx) / 4; cy = (tly + try_ + bry + bly) / 4
    return im, dict(cx=cx, cy=cy, w=w, h=h, angle=ang)

def lcdfx(w, h, out):
    """A handheld's LCD: a faint pixel grid and a soft shade at the edges, no scanlines or CRT glare."""
    fx = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
    for x in range(0, w, 3): d.line([x, 0, x, h], fill=(0, 0, 0, 26))
    for y in range(0, h, 3): d.line([0, y, w, y], fill=(0, 0, 0, 26))
    d.rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0, 90), width=4); fx.save(out)

def screenfx(w, h, out):
    fx = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
    for y in range(0, h, 3): d.line([0, y, w, y], fill=(0, 0, 0, 38))           # scanlines
    vg = Image.new('L', (w, h), 0); ImageDraw.Draw(vg).rounded_rectangle([sc(12), sc(12), w - sc(12), h - sc(12)], sc(40), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(sc(30)))
    dark = Image.new('RGBA', (w, h), (0, 0, 0, 255)); dark.putalpha(ImageChops.invert(vg).point(lambda v: int(v * 0.8))); fx.alpha_composite(dark)
    gl = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([int(w * 0.62), int(h * -0.1), int(w * 1.05), int(h * 0.3)], fill=(255, 255, 255, 40))
    fx.alpha_composite(gl.filter(ImageFilter.GaussianBlur(sc(20)))); fx.save(out)

def title_chip(t, key, text='في مثل هذا اليوم', y=300, h=66, size=44):
    """The console-skinned chip at the top right, and its artifact to the left. Returns the chip's left edge."""
    k = SKINS[key]; d = ImageDraw.Draw(t); f = A.F('Bold', size)
    w = int(d.textlength(text, font=f, **AR)) + 52 + (22 if k.get('band') else 0); x0 = R - w
    block(d, [x0, y, R, y + h], k['fill'], px=6)
    if k.get('grain'):                                          # Atari: the woodgrain front panel
        for i in range(9):
            yy = y + 8 + i * 6.3
            pts = [(xx, yy + 2.2 * math.sin(xx / 23 + i * 1.7)) for xx in range(x0 + 6, R - 5, 6)]
            d.line(pts, fill=(96, 56, 26), width=2)
    if k.get('brushed'):                                        # Game Boy box: the brushed-silver band
        for xx in range(x0 + 6, R - 5, 2):
            v = 170 + int(40 * math.sin(xx * 0.37) * math.sin(xx * 0.051))
            d.line([(xx, y + 6), (xx, y + h - 6)], fill=(v, v + 2, v + 8), width=1)
    if k.get('lcd'):                                            # Game Boy: the dot-matrix screen
        for xx in range(x0 + 6, R - 5, 4): d.line([(xx, y + 6), (xx, y + h - 6)], fill=(139, 172, 15), width=1)
        for yy in range(y + 6, y + h - 5, 4): d.line([(x0 + 6, yy), (R - 6, yy)], fill=(139, 172, 15), width=1)
    if k.get('band'):                                           # NES: the red label band at the start of the line
        d.rectangle([R - 26, y + 6, R - 8, y + h - 6], fill=k['band'])
    rim = k['rim']                                              # a hard pixel rim, no rounding
    d.line([(x0 + 6, y), (R - 6, y)], fill=rim, width=4); d.line([(x0 + 6, y + h), (R - 6, y + h)], fill=rim, width=4)
    d.line([(x0, y + 6), (x0, y + h - 6)], fill=rim, width=4); d.line([(R, y + 6), (R, y + h - 6)], fill=rim, width=4)
    for cx, cy in [(x0, y), (R - 6, y), (x0, y + h - 6), (R - 6, y + h - 6)]:
        d.rectangle([cx + 1, cy + 1, cx + 5, cy + 5], fill=rim)
    d.text((R - 26 - (22 if k.get('band') else 0), y + h / 2 + 1), text, font=f, fill=k['ink'], anchor='rm', **AR)
    trim(t, k['trim'], x0 - 20, y + h / 2)
    return x0

def trim(t, spec, right, cy):
    kind, cols = spec; d = ImageDraw.Draw(t)
    def ball(x, y, r, c):
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * 0.6) for v in c))
        d.ellipse([x - r, y - r, x + r - 2, y + r - 2], fill=c)
        d.ellipse([x - r * 0.45, y - r * 0.6, x - r * 0.05, y - r * 0.25], fill=tuple(min(255, v + 90) for v in c))
    if kind == 'squares':
        x = right
        for c in reversed(cols): block(d, [x - 30, cy - 15, x, cy + 15], c, px=4); x -= 38
    elif kind == 'bars':                                        # Atari's striped 80s box art
        x = right
        for c in reversed(cols): d.polygon([(x - 12, cy - 22), (x, cy - 22), (x - 14, cy + 22), (x - 26, cy + 22)], fill=c); x -= 20
    elif kind == 'buttons':
        x = right - 17
        for c in reversed(cols): ball(x, cy, 16, c); x -= 40
    elif kind == 'diamond':                                     # Super Famicom: X top, A right, B bottom, Y left
        x = right - 34; r = 12
        for (dx, dy), c in zip([(0, -19), (19, 0), (0, 19), (-19, 0)], [cols[2], cols[3], cols[1], cols[0]]): ball(x + dx, cy + dy, r, c)
    elif kind == 'symbols':                                     # PlayStation's four face buttons, drawn as outlines
        x = right - 18; r = 14
        tri, circ, cross, sq = cols
        d.ellipse([x - r, cy - r, x + r, cy + r], outline=circ, width=5); x -= 40
        d.line([(x - r, cy - r), (x + r, cy + r)], fill=cross, width=5); d.line([(x - r, cy + r), (x + r, cy - r)], fill=cross, width=5); x -= 40
        d.rectangle([x - r + 2, cy - r + 2, x + r - 2, cy + r - 2], outline=sq, width=5); x -= 40
        d.polygon([(x, cy - r - 2), (x + r + 2, cy + r - 2), (x - r - 2, cy + r - 2)], outline=tri, width=5)
    elif kind == 'grid':                                        # Master System's red grid
        c = cols[0]; x0 = right - 64
        for i in range(5): d.line([(x0 + i * 16, cy - 22), (x0 + i * 16, cy + 22)], fill=c, width=3)
        for i in range(4): d.line([(x0, cy - 22 + i * 14.6), (x0 + 64, cy - 22 + i * 14.6)], fill=c, width=3)
    elif kind == 'ring':                                        # Mega Drive's red disc
        x = right - 24; d.ellipse([x - 24, cy - 24, x + 24, cy + 24], outline=cols[0], width=6); d.ellipse([x - 9, cy - 9, x + 9, cy + 9], fill=cols[0])
    elif kind == 'led':                                         # Game Boy's battery light
        x = right - 12
        g = Image.new('RGBA', t.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([x - 20, cy - 20, x + 20, cy + 20], fill=cols[0] + (140,))
        t.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(t); ball(x, cy, 9, cols[0])
    elif kind == 'swirl':                                       # Dreamcast's spiral
        x = right - 26; c = cols[0]
        pts = [(x + (2 + 2.6 * a) * math.cos(a), cy + (2 + 2.6 * a) * math.sin(a)) for a in [i / 10 for i in range(0, 85)]]
        d.line(pts, fill=c, width=6)
    elif kind == 'jewel':                                       # the original Xbox's green jewel
        x = right - 24
        g = Image.new('RGBA', t.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([x - 30, cy - 30, x + 30, cy + 30], fill=cols[1] + (120,))
        t.alpha_composite(g.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(t)
        d.ellipse([x - 22, cy - 22, x + 22, cy + 22], fill=cols[0]); d.ellipse([x - 22, cy - 22, x + 22, cy + 22], outline=cols[1], width=3)

def waves(t, key):
    """The brand's wave lines in the console's two colours instead of gold, top and bottom."""
    if not SKINS[key].get('waves') or SKINS[key].get('motif'): return   # the box pattern stands in for the waves
    # never a red into blue blend: its middle runs through magenta, and no pink is ours (brand rule)
    A.THEMES['_retro'] = (*SKINS[key]['waves'], 3.0, 38, 15)
    RL._waves(t, 290, '_retro', 11, alpha=0.55)
    b = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); RL._waves(b, 420, '_retro', 23, alpha=0.45)
    t.alpha_composite(b.transpose(Image.FLIP_TOP_BOTTOM), (0, H - 420))

def top(spec, out):
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    waves(t, spec['console']); title_chip(t, spec['console'])
    d = ImageDraw.Draw(t)
    d.text((R, 386), spec['date'], font=A.F('Bold', 66), fill=txt(spec['console']), anchor='ra', **AR)
    d.text((R, 474), f"صدرت \u2066{spec['game']}\u2069", font=A.F('Bold', 54), fill=txt(spec['console']), anchor='ra', **AR)
    t.save(out)

def sheet(spec, out):
    con = CONSOLES[spec['console']]; cols = con['colours']
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    bw = -30                                                    # no box art: the values may run to the left edge
    if spec.get('box'):
        box = Image.open(spec['box']).convert('RGBA')
        bh = spec.get('box_h', 170); box = box.resize((int(box.width * bh / box.height), bh), Image.LANCZOS)
        bw = box.width; by = Y0 + 8
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([L + 8, by + 12, L + bw + 8, by + bh + 12], fill=(0, 0, 0, 150))
        t.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
        frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))        # the box art sits in a pixel frame in the console's first colour
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
                d.text((vx, y + 6 + j * 46), line, font=sub, fill=txt(spec['console']), anchor='ra', **opt(line))
            y += 46 * len(v) + 20
        else:
            f = val if d.textlength(v, font=val, **opt(v)) <= room else sub      # a long studio name drops to the smaller weight
            assert d.textlength(v, font=f, **opt(v)) <= room, ('too wide', v)
            d.text((vx, y + (0 if f is val else 8)), v, font=f, fill=txt(spec['console']), anchor='ra', **opt(v)); y += step
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
        d.text((R - 46, top_ + j * step), s, font=f, fill=txt(spec['console']), anchor='ra', **opt(s))
    bb = t.getbbox(); assert bb[0] >= L and bb[3] <= FLOOR, ('outside the safe zone', bb, lines)
    t.save(out)

def render(spec, out, push=0.03, sheet_secs=6.0):
    clip, start, dur = spec['clip'], spec['start'], spec['dur']
    tmp = tempfile.mkdtemp(prefix='retro-')
    try:
        key = spec['console']; hand = CONSOLES[key].get('handheld')
        if hand:                                                # handhelds: the desk, footage on the device's own screen
            base, geo = desk_scene(SKINS[key]['ground'], SKINS[key].get('motif'), key)
            w, h = int(geo['w'] / 2) * 2, int(geo['h'] / 2) * 2; lcdfx(w, h, f'{tmp}/fx.png')
        else:
            base, (x0, y0, w, h) = scene(SKINS[key]['ground'], SKINS[key].get('motif'))
            screenfx(w, h, f'{tmp}/fx.png')
        base.save(f'{tmp}/base.png'); top(spec, f'{tmp}/top.png'); sheet(spec, f'{tmp}/s0.png')
        segs = [(f'{tmp}/s0.png', 0, sheet_secs)]
        per = (dur - sheet_secs) / len(spec['facts'])
        for i, lines in enumerate(spec['facts']):
            fact(spec, i, f'{tmp}/s{i + 1}.png')
            a, b = sheet_secs + i * per, sheet_secs + (i + 1) * per
            need = len(' '.join(lines)) / 14 + 0.5              # every fact stays long enough to read once
            assert b - a >= need, ('fact too fast', i, b - a, need)
            segs.append((f'{tmp}/s{i + 1}.png', a, b))
        cy = (geo['cy'] if hand else y0 + h / 2) / SH; z = f"({1 / S}/(1-{push}*t/{dur}))"
        ins = ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/base.png', '-ss', str(start), '-t', str(dur), '-i', clip,
               '-loop', '1', '-t', str(dur), '-i', f'{tmp}/fx.png', '-loop', '1', '-t', str(dur), '-i', f'{tmp}/top.png']
        cx0, cy0, cw, ch = spec.get('crop', (10, 5, 330, 216))
        if hand:
            dmg = ",format=gray,format=rgb24,lutrgb=r='15+val*0.55':g='56+val*0.52':b=15" if HANDHELDS[key].get('dmg') else ''
            a = geo['angle']
            fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos{dmg},format=rgba[g];"
                  f"[g][2:v]overlay=0:0,rotate={a}:ow=rotw({a}):oh=roth({a}):c=black@0[gs];"
                  f"color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay=x='{geo['cx']}-w/2':y='{geo['cy']}-h/2'[sc];")
        else:
            fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos,eq=saturation=1.25:contrast=1.15:brightness=0.05,format=rgba[g];"
                  f"[g][2:v]overlay=0:0[gs];color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay={x0}:{y0}[sc];")
        fc += (
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
    k = spec['console']
    base = (desk_scene(SKINS[k]['ground'], SKINS[k].get('motif'), k) if CONSOLES[k].get('handheld') else scene(SKINS[k]['ground'], SKINS[k].get('motif')))[0]
    base = base.resize((W, H), Image.LANCZOS)          # the first frame shows the whole drawing at 1/S
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
