# "On this day" retro Reel (Mohammad, 10 to 11 Oct 2026). The top: the console-skinned chip, date, "صدرت <game>".
# A real CRT on a cabinet (Pexels 16707770, Oktay Köseoğlu, Pexels License) plays the game's footage on its own screen.
# Under it, first a fact sheet (developer, publisher, console; the box art stands beside the TV), then the facts one at a time.
# 11 Oct: bigger type to fill the lower half, and the console's own colours on pixel-edged label blocks beside each row and
# each fact, so the look matches the machine, not only the 8-bit jingle (CONSOLES). The safe-zone floor stays at 1480.
#   import retro
#   retro.render(dict(clip=..., start=2.0, dur=27.5, date='11 أكتوبر 1999', game='Jet Force Gemini', console='n64',
#                     box='box.jpg', sheet=[('اللعبة', 'Jet Force Gemini'), ...], facts=[[line, line, line], ...]), 'out.mp4')
# then outro.append(out, final, style='retro').
import json, math, os, sys, shutil, subprocess, tempfile
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
K = 0.34                                          # photo scale as first approved: the TV (source x 750 to 2940, top y 594), top at y 588
OX, OY = 590 - 1845 * K, 588 - 594 * K          # TV centred at x 590 so the box art stands on the cabinet at its left
FADE = (400, 588)                                 # the photo fades in under the title as first approved (dark grounds)
FADE_LIGHT = (536, 596)                           # on a white ground it appears only below the title: the wall under dark type read messy
GLASS = (900, 720, 2420, 1830)                    # the screen in the photo
WASH = 1116                                       # the wash over the cabinet starts at its top edge so the text reads
Y0 = 1156                                         # the lower area runs from here to FLOOR

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
    'atari2600': dict(type=(245, 130, 32), ground=(40, 25, 16), motif='wood', fill=(122, 74, 36), grain=True, rim=(192, 195, 199), ink=(246, 236, 214),
                      trim=('bars', [(228, 49, 38), (245, 130, 32), (250, 196, 40)]), waves=((228, 49, 38), (245, 130, 32))),
    'nes':       dict(ground=(28, 28, 32), fill=(38, 38, 42), rim=(184, 184, 188), ink=(240, 240, 244), band=(196, 0, 43), motif='grid',
                      trim=('buttons', [(196, 0, 43), (196, 0, 43)]), waves=((196, 0, 43), (184, 184, 188))),
    'famicom':   dict(type=(212, 172, 84), ground=(54, 14, 22), fill=(212, 172, 84), rim=(150, 28, 40), ink=(110, 20, 30),
                      trim=('buttons', [(150, 28, 40), (150, 28, 40)]), waves=((150, 28, 40), (212, 172, 84))),
    'mastersystem': dict(ground=(16, 16, 19), light=(244, 244, 246), motif='grid', fill=(30, 30, 34), rim=(230, 0, 18), ink=(244, 244, 248),
                      trim=('grid', [(230, 0, 18)]), waves=((30, 91, 198), (200, 200, 205))),
    'snes':      dict(type=(154, 143, 216), ground=(38, 33, 62), fill=(200, 200, 206), rim=(79, 67, 174), ink=(60, 50, 140),
                      trim=('buttons', [(79, 67, 174), (79, 67, 174), (154, 143, 216), (154, 143, 216)]), waves=((79, 67, 174), (154, 143, 216))),
    'sfc':       dict(ground=(34, 34, 40), fill=(200, 200, 206), rim=(110, 110, 120), ink=(40, 40, 48),
                      trim=('diamond', [(45, 159, 74), (245, 196, 0), (42, 79, 184), (208, 2, 27)]), waves=((245, 196, 0), (45, 159, 74))),
    'megadrive': dict(type=(232, 190, 80), ground=(14, 14, 17), motif='grid', fill=(30, 30, 34), rim=(230, 0, 18), ink=(232, 190, 80),
                      trim=('ring', [(230, 0, 18)]), waves=((230, 0, 18), (232, 190, 80))),
    'gameboy':   dict(type=(96, 112, 232), ground=(7, 7, 11), fill=(196, 198, 204), brushed=True, rim=(92, 94, 104), ink=(58, 60, 70),
                      trim=('led', [(228, 30, 40)]), waves=None, motif='rays'),          # the 1989 box: black, silver band, rays
    'gamegear':  dict(ground=(12, 12, 16), fill=(34, 34, 40), rim=(30, 91, 198), ink=(244, 244, 248),
                      trim=('buttons', [(30, 91, 198), (30, 91, 198)]), waves=((30, 91, 198), (200, 200, 205))),
    'n64':       dict(ground=(28, 28, 34), fill=(40, 40, 46), rim=(110, 110, 120), ink=(244, 243, 255),
                      trim=('squares', [(228, 32, 46), (255, 194, 14), (0, 166, 81), (0, 97, 175)]), waves=((255, 194, 14), (0, 166, 81))),
    'ps1':       dict(ground=(36, 36, 43), fill=(196, 196, 202), rim=(110, 110, 120), ink=(40, 40, 48),
                      trim=('symbols', [(0, 160, 120), (230, 0, 18), (58, 110, 200), (150, 150, 160)]), waves=((247, 198, 0), (0, 160, 160))),
    'saturn':    dict(type=(90, 150, 240), ground=(18, 19, 27), fill=(36, 36, 42), rim=(30, 91, 198), ink=(244, 244, 248),
                      trim=('squares', [(30, 91, 198), (230, 0, 18), (245, 196, 0), (0, 166, 81)]), waves=((30, 91, 198), (245, 196, 0))),
    'dreamcast': dict(type=(242, 107, 29), ground=(16, 30, 54), light=(246, 246, 248), fill=(236, 236, 240), rim=(170, 170, 178), ink=(40, 40, 48),
                      trim=('swirl', [(242, 107, 29)]), waves=((242, 107, 29), (0, 96, 168))),
    'gba':       dict(type=(124, 112, 210), ground=(30, 24, 74), fill=(75, 63, 158), rim=(124, 112, 210), ink=(244, 243, 255),
                      trim=('buttons', [(124, 112, 210), (124, 112, 210)]), waves=((75, 63, 158), (124, 112, 210))),
    'ps2':       dict(type=(40, 120, 220), ground=(8, 14, 36), motif='lines', fill=(20, 24, 40), rim=(40, 120, 220), ink=(244, 244, 248),
                      trim=('symbols', [(0, 160, 120), (230, 0, 18), (58, 110, 200), (150, 150, 160)]), waves=((0, 55, 145), (40, 120, 220))),
    'gamecube':  dict(ground=(34, 26, 74), fill=(106, 90, 205), rim=(60, 50, 140), ink=(244, 243, 255),
                      trim=('buttons', [(60, 180, 75), (230, 60, 50), (245, 196, 0)]), waves=((106, 90, 205), (60, 180, 75))),
    'xbox':      dict(type=(155, 240, 11), ground=(10, 22, 11), fill=(22, 28, 22), rim=(16, 124, 16), ink=(200, 250, 120),
                      trim=('jewel', [(16, 124, 16), (155, 240, 11)]), waves=((16, 124, 16), (155, 240, 11))),
}

DARK_TEXT = (24, 24, 30)
def gnd(spec):
    """The ground: the console's dark tone, or white when the story asks for it and the console's box is white
    (Mohammad, 11 Oct 2026: white is a green light to use when needed, not the default)."""
    k = SKINS[spec['console']]
    if spec.get('light'):
        if 'light' not in k: raise ValueError(f"{CONSOLES[spec['console']]['name']}: no white box, no white ground")
        return k['light']
    return k['ground']
def txt(spec): return DARK_TEXT if lum(gnd(spec)) > 0.6 else INK   # white ground, dark type

def contrast(a, b):
    def lin(c):
        r, g, b_ = [v / 255 for v in c]
        f = lambda u: u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b_)
    la, lb = lin(a), lin(b); hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def title_ink(spec):
    """The console's own lettering colour for the title line (SKINS 'type'), when it reads on the ground;
    otherwise the plain ink."""
    c = SKINS[spec['console']].get('type')
    return c if c and contrast(c, gnd(spec)) >= 3.0 else txt(spec)

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
        v = 1 if yy < FADE_LIGHT[0] else max(0, 1 - (yy - FADE_LIGHT[0]) / 60) if yy < FADE_LIGHT[0] + 60 else 0 if yy < 1490 else min(1, (yy - 1490) / 110)
        keep.putpixel((0, y), int(255 * v))
    m.putalpha(ImageChops.multiply(m.split()[3], keep.resize((SW, SH))))
    return m

def scene(ground=GROUND, kind=None):
    """The CRT photo on the console's ground (Mohammad, 11 Oct 2026: the ground matches the console, not indigo)."""
    fade = FADE_LIGHT if lum(ground) > 0.6 else FADE
    im = Image.new('RGB', (SW, SH), ground)
    pat = motif(kind, ground) if kind else None
    if pat: im = im.convert('RGBA'); im.alpha_composite(pat); im = im.convert('RGB')
    ph = Image.open(PHOTO).convert('RGB'); k = K * S
    ph = ph.resize((int(ph.width * k), int(ph.height * k)), Image.LANCZOS)
    x, y = sc(OX), sc(OY)
    a = Image.new('L', ph.size, 255); d = ImageDraw.Draw(a)
    for i in range(ph.height):                                # transparent above FADE[0], full by FADE[1]
        yy = (y + i) / S; v = min(1, max(0, (yy - fade[0]) / (fade[1] - fade[0])))
        if v < 1: d.line([(0, i), (ph.width, i)], fill=int(255 * v ** 1.4))
        else: break
    im.paste(ph, (x, y), a)
    im = im.convert('RGBA')
    g = Image.new('L', (1, SH), 0)
    for yy in range(SH):
        t = (yy - sc(WASH)) / sc(Y0 - 6 - WASH)                 # full before the first row of type
        g.putpixel((0, yy), int(255 * min(1, max(0, t)) ** 0.8))
    wash = Image.new('RGBA', (SW, SH), ground + (255,)); wash.putalpha(g.resize((SW, SH))); im.alpha_composite(wash)
    if pat: im.alpha_composite(pat)                             # the pattern again over the wash, in the bottom band only
    x0, y0 = fr(*GLASS[:2]); x1, y1 = fr(*GLASS[2:])           # cut the glass out; the footage plays behind it
    m = Image.new('L', im.size, 255)
    ImageDraw.Draw(m).rounded_rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], sc(62), fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(3))))
    return im, (sc(x0), sc(y0), sc(x1) - sc(x0), sc(y1) - sc(y0))

# Handhelds sit on a desk, not on the TV (Mohammad, 11 Oct 2026). Top-down desk photo from the media scout's package
# (Unsplash WW8jBak7bo), the handheld's own product shot laid on it, the footage on its screen.
DESKS = {
    'cassette': dict(photo='/mnt/user-data/uploads/scene-desk-4-pexels32759887.jpg', window=(0, 0, 3000, 2520), dev=(0.5, 0.52)),
    'carts': dict(photo='/mnt/user-data/uploads/scout/c1-pexels16247234.jpg', window=(0, 2560, 2200, 4360), dev=(0.42, 0.50)),
}
DESK = 'cassette'                                                       # window: the source crop; dev: where the device centre lands (fractions)
HANDHELDS = {
    # the product shot, how far it is turned in the photo (degrees, undone so the device faces the viewer: Mohammad,
    # 11 Oct 2026), its width on the frame, and the DMG green screen
    'gameboy': dict(photo='/mnt/user-data/uploads/retro-gameboy-front.webp', turn=0, width=360, dmg=True),   # his front-on shot, 11 Oct
}

def device(key):
    """The handheld cut from its white product background and turned upright. Returns the RGBA device and the
    screen box inside it (found from the LCD's own green)."""
    import numpy as np
    hh = HANDHELDS[key]
    src = Image.open(hh['photo']).convert('RGB')
    if hh['turn']: src = src.rotate(hh['turn'], Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    arr = np.array(src).astype(int)
    white = (arr.min(axis=2) > 236).astype('uint8') * 255
    wm = Image.fromarray(white).copy()                         # fromarray shares a read-only buffer
    ImageDraw.floodfill(wm, (2, 2), 128); ImageDraw.floodfill(wm, (src.width - 3, src.height - 3), 128)
    body = wm.point(lambda v: 0 if v == 128 else 255).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    ys, xs = np.where((g > r + 10) & (g > b + 40) & (g > 60))     # the LCD's olive green, lit or dark
    lcd = (np.percentile(xs, 0.5), np.percentile(ys, 0.5), np.percentile(xs, 99.5), np.percentile(ys, 99.5))
    bb = body.getbbox(); dev = src.crop(bb).convert('RGBA'); dev.putalpha(body.crop(bb))
    return dev, (lcd[0] - bb[0], lcd[1] - bb[1], lcd[2] - bb[0], lcd[3] - bb[1])

def desk_scene(spec):
    """Handhelds: the desk under the text, the device upright on it with its screen cut out. Returns the scene and
    the screen's centre and size on the drawn (S-scaled) frame."""
    key = spec['console']; hh = HANDHELDS.get(key)
    if not hh:
        raise ValueError(f"{CONSOLES[key]['name']}: no handheld photo yet for the desk scene")
    ground, kind = gnd(spec), SKINS[key].get('motif')
    im = Image.new('RGB', (SW, SH), ground)
    pat = motif(kind, ground) if kind else None
    if pat: im = im.convert('RGBA'); im.alpha_composite(pat); im = im.convert('RGB')
    dk = DESKS[spec.get('desk', DESK)]
    desk = Image.open(dk['photo']).convert('RGB').crop(dk['window'])
    top_y = sc(FADE_LIGHT[0]); hgt = sc(1420) - top_y; wid = SW   # the band under the title, full width, cropped to fit
    k = max(wid / desk.width, hgt / desk.height)
    desk = desk.resize((int(desk.width * k), int(desk.height * k)), Image.LANCZOS)
    cx, cy = (desk.width - wid) // 2, 0
    desk = desk.crop((cx, cy, cx + wid, cy + hgt))
    desk = Image.eval(desk, lambda v: int(v * 0.72))
    a = Image.new('L', desk.size, 255); d = ImageDraw.Draw(a)
    fade = sc(FADE_LIGHT[1] - FADE_LIGHT[0])
    for i in range(fade): d.line([(0, i), (desk.width, i)], fill=int(255 * (i / fade) ** 1.2))
    im.paste(desk, (0, top_y), a)
    im = im.convert('RGBA')
    if pat: im.alpha_composite(pat)
    g = Image.new('L', (1, SH), 0)                             # the same wash as the TV scene, so the sheet reads
    for yy in range(SH):
        t = (yy - sc(WASH)) / sc(Y0 - 6 - WASH)
        g.putpixel((0, yy), int(255 * min(1, max(0, t)) ** 0.8))
    wash = Image.new('RGBA', (SW, SH), ground + (255,)); wash.putalpha(g.resize((SW, SH)))
    dev, lcd = device(key)
    kk = min(sc(hh['width']) / dev.width, sc(WASH + 30 - FADE_LIGHT[1] - 4) / dev.height)   # never into the sheet
    dev = dev.resize((int(dev.width * kk), int(dev.height * kk)), Image.LANCZOS)
    dx = int(dk['dev'][0] * SW - dev.width / 2); dy = int(top_y + dk['dev'][1] * hgt - dev.height / 2)
    dy = max(dy, sc(FADE_LIGHT[1] + 4)); dy = min(dy, sc(WASH + 30) - dev.height)
    sh = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))             # a soft shadow on the desk
    sm = Image.new('L', (SW, SH), 0); sm.paste(dev.split()[3], (dx + sc(14), dy + sc(20)))
    sh.putalpha(sm.point(lambda v: int(v * 0.6))); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(sc(14))))
    im.alpha_composite(dev, (dx, dy)); im.alpha_composite(wash)
    x0, y0, x1, y1 = [v * kk for v in lcd]; x0 += dx; x1 += dx; y0 += dy; y1 += dy
    m = Image.new('L', (SW, SH), 255); ImageDraw.Draw(m).rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(1.2))))
    return im, dict(cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, w=x1 - x0, h=y1 - y0, angle=0)

# The room (Mohammad, 11 Oct 2026, from his references: a warm 70s and 80s den with the set inside it, not a cut-out TV on a
# flat ground). Unsplash J_30KpjyTgk: wallpaper, a lamp, a wood-cased Philips on a stand. The footage is mapped onto the
# tube in perspective. `quad` is the glass's corners in the photo (tl, tr, br, bl); `scale` the photo's scale on the frame;
# `top` where the photo's top edge lands; `cx` where the screen centre lands across the frame.
ROOMS = {
    'den': dict(photo='/mnt/user-data/uploads/scene-room-4-unsplash-J_30KpjyTgk.jpg',
                quad=[(1882, 620), (2350, 606), (2346, 960), (1880, 962)], scale=0.78, top=220, cx=520),
}
ROOM = 'den'
# The den built in code (Mohammad, 11 Oct 2026, from the "Lights on, one by one" prompt pack he sent): templates/room3d/room.html
# is a three.js scene with a deterministic renderAt(t), render.mjs captures a seamless loop in headless Chromium, and the
# screen's corners come out of the same render. Nothing in it is licensed from anyone. scene='room3d' uses it.
ROOM3D = dict(video=os.path.join(HERE, 'assets', 'retro', 'room3d-loop.mp4'), quad=os.path.join(HERE, 'assets', 'retro', 'room3d-quad.json'))

def room3d_quad():
    q = json.load(open(ROOM3D['quad']))['quad']
    return [(x * S, y * S) for x, y in q]

def scrim_layer(spec, out):
    """The ground over the title band and the sheet, as a layer of its own for a video base."""
    ground = gnd(spec); top_a, bot_a = 0.62, 0.84                  # the code-built room is dark already: lighter scrims
    g = Image.new('L', (1, H), 0)
    for y in range(H):
        if y < 540: v = top_a
        elif y < 660: v = top_a * (1 - (y - 540) / 120) ** 1.2
        elif y < WASH - 60: v = 0.0
        elif y < Y0 - 6: v = bot_a * ((y - WASH + 60) / (Y0 - 6 - WASH + 60)) ** 0.9
        else: v = bot_a
        g.putpixel((0, y), int(255 * v))
    im = Image.new('RGBA', (W, H), ground + (255,)); im.putalpha(g.resize((W, H))); im.save(out)

def room_scene(spec):
    """The full-bleed room with scrims for the type, the tube cut out. Returns the scene and the screen quad on the
    drawn (S-scaled) frame."""
    rm = ROOMS[spec.get('room', ROOM)]; ground = gnd(spec)
    ph = Image.open(rm['photo']).convert('RGB')
    k = rm['scale'] * S
    ph = ph.resize((int(ph.width * k), int(ph.height * k)), Image.LANCZOS)
    qx = sum(p[0] for p in rm['quad']) / 4
    ox, oy = sc(rm['cx']) - qx * k, sc(rm['top'])
    im = Image.new('RGBA', (SW, SH), ground + (255,))
    im.paste(ph, (int(ox), int(oy)))
    # scrims: the ground over the title band and over the sheet, the room showing between them
    g = Image.new('L', (1, SH), 0)
    for yy in range(SH):
        y = yy / S
        if y < 540: v = 0.92
        elif y < 660: v = 0.92 * (1 - (y - 540) / 120) ** 1.2
        elif y < WASH - 60: v = 0.0
        elif y < Y0 - 6: v = 0.96 * ((y - WASH + 60) / (Y0 - 6 - WASH + 60)) ** 0.9
        else: v = 0.96
        g.putpixel((0, yy), int(255 * v))
    scrim = Image.new('RGBA', (SW, SH), ground + (255,)); scrim.putalpha(g.resize((SW, SH))); im.alpha_composite(scrim)
    q = [(ox + x * k, oy + y * k) for x, y in rm['quad']]
    m = Image.new('L', (SW, SH), 255); ImageDraw.Draw(m).polygon(q, fill=0)
    im.putalpha(ImageChops.multiply(im.split()[3], m.filter(ImageFilter.GaussianBlur(1.6))))
    return im, q

def quad_mask(q, bx, by, bw, bh, out):
    """The screen's shape inside its bounding box, for alphamerge after the perspective warp."""
    m = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(x - bx, y - by) for x, y in q], fill=255)
    m.filter(ImageFilter.GaussianBlur(1.2)).save(out)

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

def fit(d, text, sizes, width, weight='Bold'):
    """The largest size that keeps the line inside width."""
    for z in sizes:
        f = A.F(weight, z)
        if d.textlength(text, font=f, **opt(text)) <= width: return f, z
    raise AssertionError(('too wide even at the smallest size', text))

def boxart(t, spec):
    """The game's box stands on the cabinet beside the TV (or lies on the desk beside a handheld), in front of the
    photo and clear of the screen, with a soft shadow under it."""
    if not spec.get('box') or (not CONSOLES[spec['console']].get('handheld') and spec.get('scene', 'room') in ('room', 'room3d')): return
    box = Image.open(spec['box']).convert('RGBA')
    hand = CONSOLES[spec['console']].get('handheld')
    maxw, maxh = (200, 250) if hand else (150, 190)
    k = min(maxw / box.width, maxh / box.height); box = box.resize((int(box.width * k), int(box.height * k)), Image.LANCZOS)
    if hand: box = box.rotate(6, Image.BICUBIC, expand=True)
    x = L; base = (WASH + 14) if not hand else WASH                 # standing on the cabinet's top edge, or on the desk
    y = base - box.height
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sm = Image.new('L', (W, H), 0); sm.paste(box.split()[3], (x + 10, y + 12))
    sh.putalpha(sm.point(lambda v: int(v * 0.65))); t.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    t.alpha_composite(box, (x, y))

def top(spec, out):
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hand = CONSOLES[spec['console']].get('handheld')
    if hand or spec.get('scene', 'room') not in ('room', 'room3d'): waves(t, spec['console'])
    title_chip(t, spec['console'])
    if SKINS[spec['console']].get('motif') and (hand or spec.get('scene', 'room') not in ('room', 'room3d')):
        sc_ = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sc_).rounded_rectangle([L + 40, 352, R + 40, 548], 60, fill=gnd(spec) + (215,))
        t.alpha_composite(sc_.filter(ImageFilter.GaussianBlur(34)))
    d = ImageDraw.Draw(t); ink = txt(spec)
    d.text((R, 350), spec['date'], font=A.F('Bold', 84), fill=ink, anchor='ra', **AR)
    title = f"صدرت \u2066{spec['game']}\u2069"
    f, z = fit(d, title, range(66, 43, -2), R - L)
    d.text((R, 456), title, font=f, fill=title_ink(spec), anchor='ra', **AR)
    assert d.textbbox((R, 456), title, font=f, anchor='ra', **AR)[3] <= FADE_LIGHT[0] + 12, 'title runs into the picture'
    boxart(t, spec)
    t.save(out)

def sheet(spec, out):
    """Developer, publisher, console, as large as the space allows. The game row is left out: the title says it."""
    con = CONSOLES[spec['console']]; cols = con['colours']; ink = txt(spec)
    rows = [(k, v) for k, v in spec['sheet'] if v != spec['game']]
    probe = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    cw = max(probe.textlength(k, font=A.F('Bold', 36), **AR) for k, _ in rows) + 44   # every label block the same width
    vx0 = R - cw - 24; room = vx0 - L
    for scale in (1.0, 0.94, 0.88, 0.82):                       # shrink everything together until it fits the floor
        t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
        y = Y0
        for i, (k, v) in enumerate(rows):
            c = cols[(i + 1) % len(cols)]; ch = 56
            vx = vx0; mw = 0
            if v == con['name'] and con.get('mark'):
                mark = Image.open(os.path.join(HERE, 'assets', 'retro', con['mark'])).convert('RGBA'); mh = int(60 * scale)
                mark = mark.resize((int(mark.width * mh / mark.height), mh), Image.LANCZOS); mw = mark.width + 16
            lines = v if isinstance(v, list) else [v]
            sizes = [int(z * scale) for z in ((62, 58, 54, 50) if len(lines) == 1 else (50, 46, 42, 38, 34))]
            z = min(fit(d, line, sizes, room - mw, 'Bold' if len(lines) == 1 else 'Medium')[1] for line in lines)
            f = A.F('Bold' if len(lines) == 1 else 'Medium', z); step = int(z * 1.32)
            block(d, [R - cw, y + 4, R, y + 4 + ch], c)
            d.text((R - cw / 2, y + 4 + ch / 2 + 1), k, font=A.F('Bold', 36), fill=GROUND if lum(c) > 0.5 else INK, anchor='mm', **AR)
            if mw:
                t.alpha_composite(mark, (int(vx - mark.width), int(y + (ch - mark.height) / 2 + 4))); vx -= mw
            for j, line in enumerate(lines):
                d.text((vx, y + (ch + 8 - z * 1.25) / 2 + j * step), line, font=f, fill=ink, anchor='ra', **opt(line))
            y += max(ch, step * len(lines)) + 26
        if t.getbbox()[3] <= FLOOR: break
    bb = t.getbbox(); assert bb[0] >= L and bb[3] <= FLOOR, ('sheet leaves the safe zone', bb)
    t.save(out)

def fact(spec, i, out):
    lines = spec['facts'][i]; c = CONSOLES[spec['console']]['colours'][i % 4]; ink = txt(spec)
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    chip(d, R, Y0, 'هل تعلم؟', c, 40)
    z = min(fit(d, s, range(70, 49, -2), R - 50 - L, 'Medium')[1] for s in lines)
    while Y0 + 92 + (len(lines) - 1) * int(z * 1.36) + int(z * 1.45) > FLOOR and z > 46: z -= 2   # and the height (descenders)
    f, step, top_ = A.F('Medium', z), int(z * 1.36), Y0 + 92
    for j in range(len(lines)):                                 # a pixel square at the start of each line, in the fact's colour
        yy = top_ + j * step + int(z * 0.42)
        block(d, [R - 24, yy, R, yy + 24], c, px=4)
    for j, s in enumerate(lines):
        d.text((R - 46, top_ + j * step), s, font=f, fill=ink, anchor='ra', **opt(s))
    bb = t.getbbox(); assert bb[0] >= L and bb[3] <= FLOOR, ('outside the safe zone', bb, lines)
    t.save(out)

def render(spec, out, push=0.03, sheet_secs=6.0):
    clip, start, dur = spec['clip'], spec['start'], spec['dur']
    tmp = tempfile.mkdtemp(prefix='retro-')
    try:
        key = spec['console']; hand = CONSOLES[key].get('handheld')
        if hand:                                                # handhelds: the desk, footage on the device's own screen
            base, geo = desk_scene(spec)
            w, h = int(geo['w'] / 2) * 2, int(geo['h'] / 2) * 2; lcdfx(w, h, f'{tmp}/fx.png')
        elif spec.get('scene', 'room') == 'room3d':
            base, q = None, room3d_quad()
            xs, ys = [p[0] for p in q], [p[1] for p in q]
            x0, y0 = int(min(xs)), int(min(ys)); w, h = int(max(xs) - x0 + 1) // 2 * 2, int(max(ys) - y0 + 1) // 2 * 2
            screenfx(w, h, f'{tmp}/fx.png'); quad_mask(q, x0, y0, w, h, f'{tmp}/qm.png'); scrim_layer(spec, f'{tmp}/scrim.png')
        elif spec.get('scene', 'room') == 'room':
            base, q = room_scene(spec)
            xs, ys = [p[0] for p in q], [p[1] for p in q]
            x0, y0 = int(min(xs)), int(min(ys)); w, h = int(max(xs) - x0 + 1) // 2 * 2, int(max(ys) - y0 + 1) // 2 * 2
            screenfx(w, h, f'{tmp}/fx.png'); quad_mask(q, x0, y0, w, h, f'{tmp}/qm.png')
        else:
            base, (x0, y0, w, h) = scene(gnd(spec), SKINS[key].get('motif'))
            screenfx(w, h, f'{tmp}/fx.png')
        if base is not None: base.save(f'{tmp}/base.png')
        top(spec, f'{tmp}/top.png'); sheet(spec, f'{tmp}/s0.png')
        segs = [(f'{tmp}/s0.png', 0, sheet_secs)]
        per = (dur - sheet_secs) / len(spec['facts'])
        for i, lines in enumerate(spec['facts']):
            fact(spec, i, f'{tmp}/s{i + 1}.png')
            a, b = sheet_secs + i * per, sheet_secs + (i + 1) * per
            need = len(' '.join(lines)) / 14 + 0.5              # every fact stays long enough to read once
            assert b - a >= need, ('fact too fast', i, b - a, need)
            segs.append((f'{tmp}/s{i + 1}.png', a, b))
        cy = (geo['cy'] if hand else y0 + h / 2) / SH; z = f"({1 / S}/(1-{push}*t/{dur}))"
        room = not hand and spec.get('scene', 'room') in ('room', 'room3d'); r3 = not hand and spec.get('scene', 'room') == 'room3d'
        base_src = ['-stream_loop', '-1', '-t', str(dur), '-i', ROOM3D['video']] if r3 else ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/base.png']
        ins = [*base_src, '-ss', str(start), '-t', str(dur), '-i', clip,
               '-loop', '1', '-t', str(dur), '-i', f'{tmp}/fx.png', '-loop', '1', '-t', str(dur), '-i', f'{tmp}/top.png']
        cx0, cy0, cw, ch = spec.get('crop', (10, 5, 330, 216))
        if hand:
            dmg = ",format=gray,format=rgb24,lutrgb=r='15+val*0.55':g='56+val*0.52':b=15" if HANDHELDS[key].get('dmg') else ''
            fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos{dmg},format=rgba[g];"
                  f"[g][2:v]overlay=0:0[gs];"
                  f"color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay=x='{geo['cx']}-w/2':y='{geo['cy']}-h/2'[sc];")
        elif room:                                              # warp the picture onto the tube, then cut it to the glass
            pts = ':'.join(f"{a}={v - (x0 if i % 2 == 0 else y0):.1f}" for i, (a, v) in enumerate(zip(
                ['x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3'], [c for p in (q[0], q[1], q[3], q[2]) for c in p])))
            ins += ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/qm.png']
            fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos,eq=saturation=1.2:contrast=1.1:brightness=0.03,format=rgba[g];"
                  f"[g][2:v]overlay=0:0,format=rgb24,perspective={pts}:sense=destination:interpolation=cubic,format=rgba[gw];"
                  f"[gw][4:v]alphamerge[gs];color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay={x0}:{y0}[sc];")
        else:
            fc = (f"[1:v]crop={cw}:{ch}:{cx0}:{cy0},scale={w}:{h}:flags=lanczos,eq=saturation=1.25:contrast=1.15:brightness=0.05,format=rgba[g];"
                  f"[g][2:v]overlay=0:0[gs];color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay={x0}:{y0}[sc];")
        if r3:                                                  # the room is a video under the picture, the scrims a layer above
            ins += ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/scrim.png']
            fc = fc.replace(f"color=c=0x0b0d10:s={SW}x{SH}:d={dur}[blk];[blk][gs]overlay={x0}:{y0}[sc];",
                            f"[0:v]scale={SW}:{SH}:flags=lanczos,format=rgba[bg];[bg][gs]overlay={x0}:{y0}[full];")
        else:
            fc += f"[0:v]format=rgba[bg];[sc][bg]overlay=0:0[full];"
        fc += (
               f"[full]scale=w='ceil({SW}*{z}/2)*2':h='ceil({SH}*{z}/2)*2':eval=frame:flags=bicubic,"
               f"crop={W}:{H}:x='(iw-{W})/2':y='(ih-{H})*{cy}',format=rgba[cam];")
        fc += f"[cam][5:v]overlay=0:0[cam2];[cam2][3:v]overlay=0:0[v0];" if r3 else f"[cam][3:v]overlay=0:0[v0];"
        base_in = 6 if r3 else 5 if room else 4
        for i, (n, a, b) in enumerate(segs):
            ins += ['-loop', '1', '-t', str(dur), '-i', n]
            fi = f"fade=t=in:st={max(0, a - 0.01)}:d=0.35:alpha=1," if a > 0 else ''
            fo = f"fade=t=out:st={b - 0.35}:d=0.35:alpha=1" if b < dur else 'null'
            fc += f"[{base_in + i}:v]format=rgba,{fi}{fo}[s{i}];[v{i}][s{i}]overlay=0:0[v{i + 1}];"
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
    if not CONSOLES[k].get('handheld') and spec.get('scene', 'room') == 'room3d':
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1', '-i', ROOM3D['video'], '-frames:v', '1', f'{outdir}/room.png'], check=True)
        base = Image.open(f'{outdir}/room.png').convert('RGBA'); scrim_layer(spec, f'{outdir}/scrim.png'); base.alpha_composite(Image.open(f'{outdir}/scrim.png'))
    else:
        base = (desk_scene(spec) if CONSOLES[k].get('handheld') else room_scene(spec) if spec.get('scene', 'room') == 'room'
                else scene(gnd(spec), SKINS[k].get('motif')))[0]
        base = base.resize((W, H), Image.LANCZOS)      # the first frame shows the whole drawing at 1/S
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
