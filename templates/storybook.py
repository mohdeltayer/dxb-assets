"""The storybook look for story-beat Reels (B8, Mohammad on the episode 6 preview, 28 Oct 2026: "It could look like a
story book where the text is written and we are shifting the camera from one part to another with the scenes playing").

Built by storybeat.build() when the spec has "look": "storybook". The card and word beats are mounted pictures on one
long page in our palette (the panel indigo with a paper grain, a soft lamp-light vignette, a light mat and a soft shadow
under each picture, a small play-mark ornament under each card), the trailer stretch or still playing inside each
frame. The camera holds on one picture while its beat plays, then glides to the next picture (an eased move of `move`
seconds, `pre` of them before the cut, so the move straddles the beat boundary while no line is on screen). Pictures
alternate a little left and right down the page, so every glide is a diagonal; the next picture just shows at the foot
of the frame, under the Reels caption area, as a page that continues. The cover and the climax stay full screen
(storybeat.beat_clip) and cut in and out; after them the camera settles onto the page from a little above.

The camera is rendered here, frame by frame, with subpixel (bilinear) placement, so slow ends of a glide never step a
whole pixel at a time (the stills judder of 18 Oct 2026). No text is drawn: reel.py draws the lines and moves them with
the page from the `motion` this returns (render_job's `page_motion`), so the words stay written on their page.

Nothing here is pink, no brand but ours, no font: the house identity (indigo, play mark, end card) is unchanged.
"""
import math, os, shutil, subprocess, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import cards as C
import storybeat as SB

W, H, FPS = SB.W, SB.H, SB.FPS
PAGE = (30, 29, 74)            # #1E1D4A, the panel indigo: the page
MAT = (236, 234, 248)          # the mount around each picture, ink-light (never white-hot, never warm)
HAIR = (120, 118, 178)         # the hairline inside the mount
AZURE, EDGE = (40, 182, 246), (63, 61, 168)
MATW = 10                      # mount width
SIDE, SWAY = 160, 60           # page margin either side of the frame; pictures sit SWAY left or right of centre
STEP_MIN = 1280                # page distance between two pictures: the next one just shows at the frame's foot (y >= 1840)
TOP = 700                      # page above the first picture, so the first settle starts on paper
ENTRY, ENTRY_SECS = 260, 0.7   # after a full-screen beat the camera settles onto the page from ENTRY px above
MOVE, PRE = 0.9, 0.3           # the glide between pictures: MOVE seconds, PRE of them before the cut
HOLD_MIN = 0.6                 # a picture holds still at least this long between its two glides
XF = 0.2                       # a `stay` beat dissolves into the same frame over XF seconds


def ease(u):
    """Cubic ease in and out on [0, 1]; reel.py uses the same curve for the lines (page_expr)."""
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (2 - 2 * u) ** 3 / 2


def window(kind):
    """(w, h, y on screen) of a picture on the page."""
    return (SB.CARD_W, SB.CARD_H, SB.CARD_Y) if kind == 'card' else (SB.WORD_W, SB.WORD_H, SB.WORD_Y)


def layout(beats):
    """slot_of[i] (index into slots, None for a full-screen beat) and slots [{kind, cx, cy, ww, wh, wy, beats}]: the
    camera's top-left on the page when it holds on that picture, and the picture's size and place on screen."""
    slots, slot_of, prev = [], [], None
    for i, b in enumerate(beats):
        if b['kind'] not in SB.PAGE_KINDS:
            slot_of.append(None)
            continue
        if b.get('stay') and slots and slot_of and slot_of[-1] is not None:
            if b['kind'] != slots[-1]['kind']:
                raise ValueError(f'storybook: beat {i} stays in a {slots[-1]["kind"]} frame but is a {b["kind"]} beat')
            slots[-1]['beats'].append(i)
            slot_of.append(len(slots) - 1)
            continue
        ww, wh, wy = window(b['kind'])
        n = len(slots)
        if prev is None:
            cy = TOP
        else:
            bottom = prev['wy'] + prev['wh'] + MATW + 40      # the picture above (mount and shadow) leaves the frame
            cy = prev['cy'] + max(STEP_MIN, bottom)
        cx = SIDE + (SWAY if n % 2 else -SWAY)
        prev = dict(kind=b['kind'], cx=cx, cy=cy, ww=ww, wh=wh, wy=wy, beats=[i])
        slots.append(prev)
        slot_of.append(n)
    return slot_of, slots


def _page(slots, seed=29):
    """The whole page, uint8 (PH, PW, 3): grain, mounts, shadows and ornaments; the pictures are pasted per frame."""
    PW = W + 2 * SIDE
    PH = int(max(s['cy'] for s in slots) + H + 400)
    rng = np.random.default_rng(seed)
    low = rng.normal(0, 1, (PH // 60 + 2, PW // 60 + 2)).astype(np.float32)
    mott = np.asarray(Image.fromarray(low).resize((PW, PH), Image.BICUBIC), dtype=np.float32)   # soft light and shade
    mid = rng.normal(0, 1, (PH // 6 + 2, PW // 6 + 2)).astype(np.float32)
    tooth = np.asarray(Image.fromarray(mid).resize((PW, PH), Image.BILINEAR), dtype=np.float32)  # the paper's tooth
    fib = Image.new('L', (PW, PH), 0)                          # paper fibres: short, faint, lighter strokes
    df = ImageDraw.Draw(fib)
    for _ in range(PW * PH // 2500):
        x, y = rng.uniform(0, PW), rng.uniform(0, PH)
        a, ln = rng.uniform(0, math.pi), rng.uniform(8, 34)
        df.line((x, y, x + ln * math.cos(a), y + ln * math.sin(a) * 0.6), fill=int(rng.uniform(40, 110)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32) / 255.0
    tile = rng.normal(0, 1, (256, 256)).astype(np.float32)                                         # fine grain
    grain = np.tile(tile, (PH // 256 + 1, PW // 256 + 1))[:PH, :PW]
    lum = 1.0 + 0.035 * mott + 0.018 * tooth + 0.02 * grain + 0.22 * fib
    del mott, tooth, fib, grain
    page = np.empty((PH, PW, 3), np.uint8)
    for c in range(3):
        page[..., c] = np.clip(PAGE[c] * lum, 0, 255).astype(np.uint8)
    del lum
    im = Image.fromarray(page)
    for s in slots:
        x0 = s['cx'] + (W - s['ww']) // 2
        y0 = s['cy'] + s['wy']
        box = (x0 - MATW, y0 - MATW, x0 + s['ww'] + MATW, y0 + s['wh'] + MATW)
        pad = 70                                               # a soft shadow under the mount, lifted as on a page
        sh = Image.new('L', (box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad), 0)
        ImageDraw.Draw(sh).rectangle((pad, pad, pad + box[2] - box[0], pad + box[3] - box[1]), fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        im.paste((6, 6, 20), (box[0] - pad + 8, box[1] - pad + 18), sh)
        d = ImageDraw.Draw(im)
        d.rectangle(box, fill=MAT)
        d.rectangle((x0 - 3, y0 - 3, x0 + s['ww'] + 2, y0 + s['wh'] + 2), outline=HAIR, width=2)
        if s['kind'] == 'card':                                # the ornament: a small play mark between two rules
            oy = y0 + s['wh'] + MATW + 70
            mx = s['cx'] + W // 2
            d.line((mx - 140, oy, mx - 26, oy), fill=EDGE, width=2)
            d.line((mx + 26, oy, mx + 140, oy), fill=EDGE, width=2)
            d.polygon([(mx - 8, oy - 11), (mx - 8, oy + 11), (mx + 11, oy)], fill=AZURE)
    return np.asarray(im).copy()


def _vignette():
    """Lamp light on the page: the centre full, the edges and the foot a little darker (screen space)."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.44) / (H * 0.62)) ** 2)
    v = 1.0 - 0.32 * np.clip(r - 0.55, 0, 1) ** 1.3
    return v[..., None].astype(np.float32)


class Frames:
    """The picture inside one frame for one beat, read from ffmpeg in order; asks before frame 0 get frame 0 and asks
    after the last get the last (the frame holds still while the camera arrives or leaves)."""

    def __init__(self, b, w, h, secs):
        self.w, self.h = w, h
        self.n = int(round(secs * FPS))
        src = os.path.join(C.U, b['src'])
        bw = ',hue=s=0' if b.get('bw') else ''
        ins, vf = SB._card_src(b, src, w, h, self.n, secs, bw)
        if b['kind'] == 'word':
            vf += ',' + SB.WORD_DIM
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-nostdin', *ins, '-vf', vf + ',format=rgb24', '-an',
                                   '-frames:v', str(self.n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.i, self.cur = -1, None
        self.foot = None
        if b['kind'] == 'word':                    # the darker foot under the word, as in the classic look
            yy = np.arange(h, dtype=np.float32)
            t = np.clip((yy - h * 0.45) / (h * 0.55), 0, 1) ** 1.4 * (185 / 255)
            self.foot = t[:, None, None]

    def get(self, i):
        i = min(max(i, 0), self.n - 1)
        while self.i < i:
            buf = self.p.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3:
                if self.cur is None:
                    raise RuntimeError('storybook: no frames from ffmpeg: ' + self.p.stderr.read().decode()[-800:])
                self.n = self.i + 1                # a short source: hold its last frame
                break
            fr = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)
            if self.foot is not None:
                fr = (fr * (1 - self.foot) + np.array((10, 9, 30), np.float32) * self.foot).astype(np.uint8)
            self.cur, self.i = fr, self.i + 1
        return self.cur

    def close(self):
        try:
            self.p.stdout.close()
            self.p.kill()
            self.p.wait()
        except OSError:
            pass


def plan(spec):
    """Beat start frames and times, the layout, and the camera events [(start, secs, from, to)] in track seconds;
    `moves` [[t_cut, pre, post, dx, dy]] is what the job carries as page_motion. Stops when a picture would not hold
    still for HOLD_MIN between its glides."""
    beats = spec['beats']
    move, pre = float(spec.get('move', MOVE)), float(spec.get('pre', PRE))
    slot_of, slots = layout(beats)
    frames, cuts, f, t = [], [], 0, 0.0
    for b in beats:
        frames.append(f); cuts.append(round(f / FPS, 3))   # frame-exact, so the job's shots cut where the beats do
        f += int(round(float(b["secs"]) * FPS))
    total_f, total = f, round(f / FPS, 3)
    ends = cuts[1:] + [total]
    events, moves = [], []
    for k, s in enumerate(slot_of):
        if s is None or (k and slot_of[k - 1] == s):
            continue
        to = (slots[s]['cx'], slots[s]['cy'])
        if k and slot_of[k - 1] is not None:   # from the picture before: glide across the page
            fr = (slots[slot_of[k - 1]]['cx'], slots[slot_of[k - 1]]['cy'])
            events.append((cuts[k] - pre, move, fr, to))
            moves.append([cuts[k], pre, round(move - pre, 3), to[0] - fr[0], to[1] - fr[1]])
        else:                                  # after the cover or the climax: settle onto the page
            fr = (to[0], to[1] - ENTRY)
            events.append((cuts[k], ENTRY_SECS, fr, to))
            moves.append([cuts[k], 0.0, ENTRY_SECS, 0, ENTRY])
    for s, sl in enumerate(slots):             # each picture holds still long enough to be looked at
        a, z = cuts[sl['beats'][0]], ends[sl['beats'][-1]]
        k0, k1 = sl['beats'][0], sl['beats'][-1]
        arrive = a + (move - pre if k0 and slot_of[k0 - 1] is not None else ENTRY_SECS)
        leave = z - (pre if k1 + 1 < len(beats) and slot_of[k1 + 1] is not None else 0.0)
        if leave - arrive < HOLD_MIN - 1e-6:
            raise ValueError(f'storybook: the picture of beat {k0} holds {leave - arrive:.2f} s between its glides '
                             f'(at least {HOLD_MIN}); lengthen the beat, mark the next beat stay, or shorten move')
    return dict(slot_of=slot_of, slots=slots, frames=frames, cuts=cuts, total_f=total_f, total=total,
                events=events, moves=moves)


def camera(events, g):
    """The camera's top-left on the page at track second g (float)."""
    cur = None
    for st, secs, fr, to in events:
        if g < st:
            break
        cur = (st, secs, fr, to)
    if cur is None:
        st, secs, fr, to = events[0]
        return fr
    st, secs, fr, to = cur
    e = ease((g - st) / secs) if secs > 0 else 1.0
    return (fr[0] + (to[0] - fr[0]) * e, fr[1] + (to[1] - fr[1]) * e)


def _run_page(p, k0, k1, page, vig, out, spec):
    """Beats k0..k1-1 (all on the page) as one clip, frame by frame."""
    beats = p['beats']
    slots, slot_of = p['slots'], p['slot_of']
    used = range(len(slots))                   # every picture on the page, the ones of other runs held still
    readers = {}                               # beat -> Frames, opened when first needed, closed when the run ends
    def reader(k):
        if k not in readers:
            s = slots[slot_of[k]]
            readers[k] = Frames(beats[k], s['ww'], s['wh'], float(beats[k]['secs']))
        return readers[k]
    f0, f1 = p['frames'][k0], (p['frames'][k1] if k1 < len(beats) else p['total_f'])
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    PH, PW = page.shape[:2]
    try:
        for f in range(f0, f1):
            g = f / FPS
            cx, cy = camera(p['events'], g)
            ix, iy = int(math.floor(cx)), int(math.floor(cy))
            fx, fy = cx - ix, cy - iy
            ix, iy = min(max(ix, 0), PW - W - 1), min(max(iy, 0), PH - H - 1)
            buf = page[iy:iy + H + 1, ix:ix + W + 1].copy()
            for s in used:
                sl = slots[s]
                px, py = sl['cx'] + (W - sl['ww']) // 2 - ix, sl['cy'] + sl['wy'] - iy
                if px >= W + 1 or py >= H + 1 or px + sl['ww'] <= 0 or py + sl['wh'] <= 0:
                    continue
                ks = [k for k in sl['beats'] if k0 <= k < k1] or sl['beats']
                cur = ks[0]
                for k in ks:                   # the beat that is playing in this frame (or the nearest one)
                    if f >= p['frames'][k]:
                        cur = k
                fr = reader(cur).get(f - p['frames'][cur])
                j = ks.index(cur)
                if j and f - p['frames'][cur] < XF * FPS:          # a stay beat dissolves in its frame
                    a = (f - p['frames'][cur] + 1) / (XF * FPS + 1)
                    prev = reader(ks[j - 1]).get(10 ** 9)
                    fr = (fr.astype(np.float32) * a + prev.astype(np.float32) * (1 - a)).astype(np.uint8)
                x0, y0 = max(px, 0), max(py, 0)
                x1, y1 = min(px + sl['ww'], W + 1), min(py + sl['wh'], H + 1)
                buf[y0:y1, x0:x1] = fr[y0 - py:y1 - py, x0 - px:x1 - px]
            if fx or fy:
                b = buf.astype(np.float32)
                img = (b[:-1, :-1] * ((1 - fx) * (1 - fy)) + b[:-1, 1:] * (fx * (1 - fy))
                       + b[1:, :-1] * ((1 - fx) * fy) + b[1:, 1:] * (fx * fy))
            else:
                img = buf[:-1, :-1].astype(np.float32)
            img *= vig
            enc.stdin.write(np.clip(img + 0.5, 0, 255).astype(np.uint8).tobytes())
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError('storybook encode: ' + enc.stderr.read().decode()[-800:])
    finally:
        for r in readers.values():
            r.close()
        if enc.poll() is None:
            enc.kill()


def build(spec):
    """The storybook picture track: (cuts, total, motion) where motion is {"track": <file name>, "moves": [...]}."""
    p = plan(spec)
    p['beats'] = spec['beats']
    tmp = tempfile.mkdtemp(prefix='storybook-')
    try:
        page = _page(p['slots']) if p['slots'] else None
        vig = _vignette()
        parts, k, n = [], 0, len(spec['beats'])
        while k < n:
            b = spec['beats'][k]
            part = os.path.join(tmp, f'p{len(parts):02d}.mp4')
            if p['slot_of'][k] is None:
                SB.beat_clip(b, spec.get('bg'), part, k)
                k += 1
            else:
                k1 = k
                while k1 < n and p['slot_of'][k1] is not None:
                    k1 += 1
                _run_page(p, k, k1, page, vig, part, spec)
                k = k1
            parts.append(part)
        lst = os.path.join(tmp, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{x}'\n" for x in parts))
        out = spec['out']
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        SB._run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'libx264', '-preset', 'medium',
                 '-crf', '16', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out])
        return p['cuts'], p['total'], {'track': os.path.basename(out), 'moves': p['moves']}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
