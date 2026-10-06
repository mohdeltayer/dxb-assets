"""Guess-the-creator quiz Reel (Mohammad, 6 Oct 2026, for Masahiro Sakurai's
dinner photo with nine other game directors).

It opens on the story's photo, darkened, under the question; then one round
per creator: an official image of their best-known character fills the 9:16
frame and pans slowly, "who created this character?" and a 3-2-1 countdown
sit low in the frame, then the answer replaces them (the creator's name, the
game and its year). It closes on the photo again with the credit and a last
line for the comments. Every round's attribution is checked against credits
before it goes in: the quiz is only fun if every answer holds.

    rounds = [dict(art=('kirby-1.jpg', (0.3, 0.6)), name='ماساهيرو ساكوراي',
                   latin='Masahiro Sakurai', game="Kirby's Dream Land", year=1992), ...]
    reel(rounds, hook, sub, photo=('sakurai-dinner.jpg', (0.4, 0.6)),
         close=('كم واحدًا عرفت؟', 'الصورة: ماساهيرو ساكوراي على X'),
         date='6 Oct 2026', out='cards/2026-10/directors-quiz-reel-v1.mp4')

lang='ar' is the Digital Lounge cut (Dubai type, right-aligned, the play-mark
end card and jingle); lang='en' is the DXB-KNIGHT cut (Inter, left-aligned,
a crest end card, no Digital Lounge sound). Images are official art only
(store pages, Steam, press kits), 1920 wide where one exists. Text stays in
the Reels safe zone (ig_ar.SAFE_*).
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

W, H = 1080, 1920
L, R = G.SAFE_LEFT, W - G.SAFE_RIGHT            # 96 .. 910
TOP, BOT = G.SAFE_TOP, G.SAFE_BOTTOM            # 285 .. 1480
SUB = 'quiz'                                    # stills are copied to uploads/<SUB>/
ASK, TELL = 2.4, 2.8                            # seconds: question with countdown, then the answer
HOOK, CLOSE = 3.8, 4.6
GAP = 0.2          # one text fades out before the next fades in

TEXT = {
    'ar': dict(ask='من صنع هذه اللعبة؟', of='من {n}'),
    'en': dict(ask='Who made this game?', of='{i} of {n}'),
}


class _Type:
    """Fonts and alignment for one cut."""
    def __init__(self, lang):
        self.ar = lang == 'ar'
        self.x = R if self.ar else L
        self.anchor_s = 'rs' if self.ar else 'ls'
        self.anchor_m = 'rm' if self.ar else 'lm'
        self.ink, self.body, self.ground = (A.INK, A.BODY, A.GROUND) if self.ar else (C.INK, C.SUB, C.GROUND)

    def f(self, weight, size):
        if self.ar:
            return A.F(weight, size)
        return C.font(size, {'Bold': 750, 'Medium': 560, 'Regular': 420}[weight])


def _kw(T, s):
    """Arabic shaping only for lines with Arabic in them: a Latin line set
    right to left reorders ("428: Shibuya Scramble" came out as ":428")."""
    return dict(G.AR) if T.ar and any('\u0600' <= ch <= '\u06ff' for ch in s) else {}


def _text(lay, xy, s, f, fill, anchor, T, stroke=5):
    """Text with a dark outline and a soft shadow, as on the Reel lines."""
    kw = _kw(T, s)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor, **kw)
    out = m.filter(ImageFilter.MaxFilter(stroke if stroke % 2 else stroke + 1))
    sh = out.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.6))
    for col, mk, off in [((0, 0, 0), sh, (3, 4)), (T.ground, out, (0, 0)), (fill, m, (0, 0))]:
        c = Image.new('RGBA', (W, H), col + (255,)); a = Image.new('L', (W, H), 0)
        a.paste(mk, off); c.putalpha(a); lay.alpha_composite(c)


def _fits(T, s, f, room=R - L):
    kw = _kw(T, s)
    return ImageDraw.Draw(Image.new('RGBA', (8, 8))).textlength(s, font=f, **kw) <= room


def _sized(T, s, weight, size, low):
    while not _fits(T, s, T.f(weight, size)) and size > low:
        size -= 2
    if not _fits(T, s, T.f(weight, size)):
        raise ValueError(f'line runs out of the safe zone: {s}')
    return T.f(weight, size)


def _counter(lay, T, i, n, accent):
    """Round number, small, at the top of the safe zone."""
    d = ImageDraw.Draw(lay)
    s = TEXT['ar' if T.ar else 'en']['of'].format(i=i, n=n)
    s = f'{i} {s}' if T.ar else s
    f = T.f('Bold', 36)
    kw = dict(G.AR) if T.ar else {}
    tw = d.textlength(s, font=f, **kw)
    x0, x1 = (T.x - tw - 36, T.x) if T.ar else (T.x, T.x + tw + 36)
    d.rounded_rectangle([x0, TOP + 10, x1, TOP + 70], radius=12, fill=accent)
    d.text(((x0 + x1) / 2, TOP + 40), s, font=f, fill=T.ground, anchor='mm', **kw)


def ask_layer(T, i, n, digit, accent, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    RL._band(lay, 0, TOP + 120, True, 150)
    RL._band(lay, 980, H, False, 230)
    _counter(lay, T, i, n, accent)
    q = TEXT['ar' if T.ar else 'en']['ask']
    _text(lay, (T.x, BOT - 150), q, _sized(T, q, 'Bold', 70, 46), T.ink, T.anchor_s, T)
    big = T.f('Bold', 230)
    _text(lay, (W // 2 - 40, BOT - 260), str(digit), big, accent, 'ms', T, stroke=9)
    lay.save(path); return path


def tell_layer(T, i, n, r, accent, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    RL._band(lay, 0, TOP + 120, True, 150)
    RL._band(lay, 900, H, False, 235)
    _counter(lay, T, i, n, accent)
    d = ImageDraw.Draw(lay)
    y = BOT - 40
    meta = f'{r["game"]}  ·  {r["year"]}'
    _text(lay, (T.x, y), meta, _sized(T, meta, 'Medium', 44, 30), T.body, T.anchor_s, T, stroke=3)
    y -= 70
    if T.ar:                                        # the Latin under the Arabic name, as on the Reels
        _text(lay, (T.x, y), r['latin'], _sized(T, r['latin'], 'Medium', 50, 34), T.ink, T.anchor_s, T, stroke=3)
        y -= 82
        _text(lay, (T.x, y), r['name'], _sized(T, r['name'], 'Bold', 92, 60), accent, T.anchor_s, T, stroke=7)
    else:
        _text(lay, (T.x, y), r['latin'], _sized(T, r['latin'], 'Bold', 92, 56), accent, T.anchor_s, T, stroke=7)
    y -= 120
    d.rectangle([T.x - 60, y, T.x, y + 6] if T.ar else [T.x, y, T.x + 60, y + 6], fill=accent)
    lay.save(path); return path


def hook_layer(T, hook, sub, accent, path, chip=None):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    plate = Image.new('L', (W, H), 0)
    ImageDraw.Draw(plate).rectangle([0, 640, W, 1320], fill=225)
    plate = plate.filter(ImageFilter.GaussianBlur(80))
    g = Image.new('RGBA', (W, H), T.ground + (255,)); g.putalpha(plate); lay.alpha_composite(g)
    d = ImageDraw.Draw(lay)
    kw = dict(G.AR) if T.ar else {}
    f = T.f('Bold', 80)
    words, lines, cur = ([] if '\n' in hook else hook.split()), [], ''
    if '\n' in hook:                                # breaks set by hand win (a phrase never splits)
        lines = hook.split('\n')
        f = T.f('Bold', max(sz for sz in range(56, 82, 2) if all(_fits(T, ln, T.f('Bold', sz)) for ln in lines)))
    for w_ in words:                                 # greedy wrap inside the safe zone
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f, **kw) <= R - L:
            cur = t
        else:
            lines.append(cur); cur = w_
    if words:
        lines.append(cur)
    if len(lines) > 4:
        raise ValueError('hook too long for four lines')
    y = 960 - len(lines) * 104 // 2
    if chip:
        cf = T.f('Bold', 40); cw = d.textlength(chip, font=cf, **kw)
        x0, x1 = (T.x - cw - 32, T.x) if T.ar else (T.x, T.x + cw + 32)
        d.rounded_rectangle([x0, y - 120, x1, y - 60], radius=12, fill=accent)
        d.text(((x0 + x1) / 2, y - 90), chip, font=cf, fill=T.ground, anchor='mm', **kw)
    for k, ln in enumerate(lines):
        _text(lay, (T.x, y + k * 104), ln, f, T.ink, T.anchor_m, T, stroke=6)
    y2 = y + len(lines) * 104 + 20
    d.rectangle([T.x - 50, y2, T.x, y2 + 5] if T.ar else [T.x, y2, T.x + 50, y2 + 5], fill=accent)
    _text(lay, (T.x, y2 + 60), sub, _sized(T, sub, 'Medium', 52, 34), T.body, T.anchor_m, T, stroke=3)
    lay.save(path); return path


def close_layer(T, big, credit, accent, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    RL._band(lay, 1000, H, False, 235)
    _text(lay, (T.x, BOT - 110), big, _sized(T, big, 'Bold', 84, 54), accent, T.anchor_s, T, stroke=7)
    _text(lay, (T.x, BOT - 30), credit, _sized(T, credit, 'Medium', 36, 26), T.body, T.anchor_s, T, stroke=3)
    lay.save(path); return path


def _crest_card(out, secs=2.4):
    """DXB-KNIGHT end card: crest, name and handle on the card ground. No sound
    (the jingle is a Digital Lounge mark)."""
    im = Image.new('RGB', (W, H), C.GROUND)
    cr = Image.open(C.CREST).convert('RGBA').resize((300, 300), Image.LANCZOS)
    im.paste(cr, ((W - 300) // 2, 700), cr)
    d = ImageDraw.Draw(im)
    d.text((W // 2, 1100), 'DXB-KNIGHT', font=C.font(84, 800), fill=C.INK, anchor='mm')
    d.text((W // 2, 1180), '@DXBNIN', font=C.font(44, 500), fill=C.SUB, anchor='mm')
    p = out + '.png'; im.save(p)
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-loop', '1', '-framerate', '30', '-t', str(secs),
                    '-i', p, '-vf', 'format=yuv420p', '-c:v', 'libx264', out], check=True)
    return out


def reel(rounds, hook, sub, photo, close, date, out, lang='ar', theme='stylized', chip=None, draft=False):
    T = _Type(lang)
    accent = G.ACCENTS[theme] if T.ar else C.accent_colour('cross')
    os.makedirs(C.U + SUB, exist_ok=True)
    def up(f):
        dst = f'{SUB}/{os.path.basename(f)}'
        if not os.path.exists(C.U + dst) or os.path.getmtime(f) > os.path.getmtime(C.U + dst):
            shutil.copy(f, C.U + dst)
        return dst
    n = len(rounds)
    shots = [(up(photo[0]), None, HOOK, photo[1])]
    shots += [(up(r['art'][0]), None, ASK + TELL, r['art'][1]) for r in rounds]
    shots += [(up(photo[0]), None, CLOSE, photo[1][::-1])]
    starts, end = RL.timeline(shots)
    tmp = tempfile.mkdtemp(prefix='quiz-')
    try:
        # (png, from, to, fade): the hook dims the photo with its own plate
        layers = [(hook_layer(T, hook, sub, accent, f'{tmp}/h.png', chip), 0, starts[1] + GAP - 0.05, 0.3)]
        for i, r in enumerate(rounds, 1):
            s = starts[i]; step = ASK / 3
            for k, digit in enumerate((3, 2, 1)):
                a = s + k * step + (GAP if k == 0 else 0); z = s + (k + 1) * step
                layers.append((ask_layer(T, i, n, digit, accent, f'{tmp}/a{i}{digit}.png'), a, z, 0.12))
            layers.append((tell_layer(T, i, n, r, accent, f'{tmp}/t{i}.png'), s + ASK, starts[i + 1] + GAP - 0.05, 0.2))
        layers.append((close_layer(T, close[0], close[1], accent, f'{tmp}/c.png'), starts[-1] + GAP, end, RL.X))
        RL.montage(shots, f'{tmp}/cut.mp4', fast=draft)
        args = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', f'{tmp}/cut.mp4']
        for p, *_ in layers:
            args += ['-loop', '1', '-t', f'{end:.2f}', '-i', p]
        fc = ['[0:v]setsar=1,fps=30[v0]']
        for i, (p, a, z, fd) in enumerate(layers, 1):
            fin = f',fade=t=in:st={a:.2f}:d={fd}:alpha=1' if a > 0 else ''
            fout = f',fade=t=out:st={z - fd:.2f}:d={fd}:alpha=1' if z < end - 0.01 else ''
            fc += [f'[{i}:v]format=rgba{fin}{fout}[l{i}]', f'[v{i - 1}][l{i}]overlay=0:0:shortest=1[v{i}]']
        fc.append(f'[v{len(layers)}]format=yuv420p[v]')
        body = f'{tmp}/body.mp4'
        subprocess.run(args + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                       + (RL.DRAFT_ENC if draft else ['-preset', 'slow', '-crf', '16']) + [body], check=True)
        if draft:
            done = os.path.splitext(out)[0] + '-draft.mp4'
            shutil.move(body, done)
            return done, starts, end
        if T.ar:
            return outro.append(body, out, 'neon', accent=accent), starts, end
        card = _crest_card(f'{tmp}/crest.mp4')
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', body, '-i', card, '-filter_complex',
                        f'[0:v]settb=AVTB,fps=30[a];[1:v]settb=AVTB,fps=30,setsar=1[b];'
                        f'[a][b]xfade=transition=fade:duration={RL.X}:offset={end - RL.X:.3f},format=yuv420p[v]',
                        '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', out], check=True)
        return out, starts, end
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
