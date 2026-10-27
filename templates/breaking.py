"""The T0 breaking card (advisor card adv-20261027-build-until-thursday, item 2, approved by Mohammad, 27 Oct 2026).

For a verified, official story that is breaking right now, with no time to cut footage: ONE image (the game's key art, a
still from the source post, or the first clean frame of the official trailer), ONE headline, ONE line of what happened,
the credit line (source, date), the chip, the persistent mark, the breaking bed and the standard end card. Same house
identity as every Reel: Dubai type from DUBAI_FONTS, chip row and headline exactly where reel.head_layer puts them (grid
corner rule included), the safe zone (x 96 to 910, y 285 to 1480), the crimson theme for عاجل, the story line in
reel.line_layer's white Bold with the indigo outline.

What is prebuilt and cached, and what is per story
  cached per theme (breaking.parts, under outro.CACHE/breaking-plate): the wave plate (theme gradient + the numgfx wave mask,
      drawn once; its drift is a crop expression over the cached mask, so no per-frame work) and the scrim (dark gradient
      so the line and the headline hold on any art). The end-card master and the bed come from outro's own caches
      (outro.card_master, outro.evolving_bed); `warm` builds all of it ahead of a story.
  per story: the Ken Burns push on the one image (the only real per-frame work, one zoompan), the text layers (PIL) and
      ONE ffmpeg pass that lays image, plate, scrim and text, then outro.append's single veryfast encode and the cached end
      card. No montage pass, no separate text pass, no demucs, no picture finish, no shot sheet.

Job file (kind "breaking"; render_job.py runs it, the same flags as every job):

    {"kind": "breaking", "name": "x", "out": "cards/2026-10/x-reel-v1.mp4",
     "footage": [{"file": "x-art.jpg", "url": "https://..."}],     # the one image, fetched like footage (url, repo, steam)
     "image": "x-art.jpg",                                          # a file in uploads, or ["clip.mp4", 12.3]: its frame at 12.3 s
     "focus": [0.5, 0.5],                                           # where the 9:16 window sits on the picture (x on a wide image,
                                                                    # y on a tall one); judged on the sheet, default centre
     "headline": "...", "line": "...\\n...",                        # one hook, one line of what happened (hand breaks kept)
     "label": "عاجل", "source": "...", "date": "27 Oct 2026",
     "theme": "cold", "style": "bold", "sound": null,               # عاجل forces crimson and the breaking bed; sound defaults to breaking
     "secs": null, "lowres_ok": null, "country": null}

Length: the headline owns 0 to 3.5 s, the credit line enters at 2 s, the line from 3.6 s for its reading time plus a hold
(8 s at least), then the 2 s end card. The image pushes in 6% over the whole clip, the wave plate drifts: nothing is
static from frame one. A picture that would be enlarged past reel.MAX_ZOOM (counting the push) stops the render unless
`lowres_ok` names the copies searched, as for footage.

    python3 breaking.py check <job>       # plan, enlargement (needs the image in uploads for the second)
    python3 breaking.py warm <job>|--all  # plate, end-card master and bed for a job's theme and length, or for every theme
"""
import json, math, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                        # noqa: E402
from PIL import Image, ImageDraw, ImageFont                # noqa: E402
import cards as C, fast_ar as A, ig_ar as G, numgfx as NG, outro, reel   # noqa: E402

W, H, FPS = reel.W, reel.H, 30
HEAD_SECS = 3.5                          # the headline's time, as reel(head_secs=)
LINE_AT = HEAD_SECS + 0.1                # the line enters just after it, as reel.spread does
HOLD = 1.6                               # seconds the line stays after its reading time
MIN_SECS, MAX_SECS = 8.0, 22.0           # before the end card
SUB = 2                                  # the push runs on a 2x enlargement: half-pixel steps (zoompan is single-threaded;
                                         # 3x doubles its time and 4x, the stills_clips setting, is ten times a 60 s budget)
PUSH = 0.06                              # the image grows 6% over the clip
WAVES = 1.5                              # wave strength: a touch bolder than the numbers Reels, it is the breaking skin
VER = 1                                  # bump when the plate's design changes: the cache key
PLATE_DIR = os.path.join(outro.CACHE, 'breaking-plate')
SOUND = 'breaking'
KEYS = ('name', 'out', 'image', 'headline', 'line', 'label', 'source', 'date')


def theme_of(job):
    """crimson for عاجل (reel.reel does the same), else the job's theme."""
    return 'crimson' if job['label'] == 'عاجل' else job.get('theme', 'cold')


def sound_of(job):
    return job.get('sound') or SOUND


def plan(job):
    """Timing: {'end', 'frames', 'line_at', 'need'}; the line gets its reading time (reel.read_secs) and a hold."""
    miss = [k for k in KEYS if not job.get(k)]
    if miss:
        raise ValueError(f'breaking job needs {", ".join(miss)}')
    need = reel.read_secs(job['line'])
    end = float(job.get('secs') or max(MIN_SECS, round(LINE_AT + need + HOLD, 1)))
    frames = round(end * FPS)
    end = frames / FPS
    if LINE_AT + need > end + 0.01:
        raise ValueError(f'the line needs {need:.1f} s to read and starts at {LINE_AT:.1f} s: secs {end:.1f} is too short')
    if end > MAX_SECS:
        raise ValueError(f'{end:.1f} s: a T0 card is {MIN_SECS:.0f} to {MAX_SECS:.0f} s, past that it is a standard Reel')
    return dict(end=end, frames=frames, line_at=LINE_AT, need=need)


# ---------------------------------------------------------------- the one image
def source(job, build=True):
    """Path of the card's one image: a file in uploads, or a frame of a clip ([file, seconds], letterbox cropped).
    None when it is not in uploads (the container check before the render)."""
    im = job['image']
    if isinstance(im, str):
        p = C.U + im
        return p if os.path.exists(p) else None
    f, t = im
    if not os.path.exists(C.U + f):
        return None
    out = f'{C.U}numbers/{job["name"]}-t0frame.png'
    if build or os.path.exists(out):
        if not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            bars, _ = reel._bars(C.U + f, t, 1)
            vf = bars.rstrip(',') or 'null'
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(t), '-i', C.U + f, '-frames:v', '1',
                            '-vf', vf, out], check=True)
        return out
    return None


def window(w, h, focus):
    """(x0, y0, cw, ch): the 9:16 window on a w x h picture. A wide picture keeps its full height and the window slides
    across it by focus x; a tall one keeps its full width and slides down by focus y."""
    fx, fy = focus
    if w * 16 >= h * 9:
        ch, cw = h, round(h * 9 / 16)
        return round((w - cw) * fx), 0, cw, ch
    cw, ch = w, round(w * 16 / 9)
    return 0, round((h - ch) * fy), cw, ch


def enlargement(job, path):
    """How far the window is enlarged to fill 1080 x 1920 at the end of the push; stops past reel.MAX_ZOOM
    unless lowres_ok names the copies checked."""
    w, h = Image.open(path).size
    _, _, cw, ch = window(w, h, job.get('focus', (0.5, 0.5)))
    z = H / ch * (1 + PUSH)
    if z > reel.MAX_ZOOM and not reel.lowres_reason(job.get('lowres_ok')):
        raise ValueError(f'{os.path.basename(path)}: a {w}x{h} picture is enlarged {z:.1f}x to fill 9:16 (cap {reel.MAX_ZOOM:.0f}x); '
                         f'find a larger image, or name the copies checked in lowres_ok ("{reel.LOWRES_EXAMPLE}")')
    return z


# ---------------------------------------------------------------- the cached plate
def parts(theme):
    """(gradient, wave mask, scrim) PNGs for a theme, drawn once and kept (the plate: its drift is a crop over the
    mask). Keyed by VER and the theme's colours, never by file times, so a fresh checkout does not rebuild them."""
    os.makedirs(PLATE_DIR, exist_ok=True)
    key = f'{theme}-{_stamp(theme)}'
    paths = [f'{PLATE_DIR}/{key}-{n}.png' for n in ('grad', 'mask', 'scrim')]
    if all(os.path.exists(p) for p in paths):
        return paths
    NG._gradient(theme).save(paths[0] + '.part.png')
    NG._mask(theme, 0, strength=WAVES).save(paths[1] + '.part.png')
    _scrim().save(paths[2] + '.part.png')
    for p in paths:
        os.replace(p + '.part.png', p)
    return paths


def _stamp(theme):
    import hashlib
    raw = json.dumps([VER, theme, A.THEMES[theme], A.GROUND, WAVES, W, H])
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def _scrim():
    """A dark gradient over the picture: the headline's top, and a deep floor under the line, so white type holds on pale
    key art. The soft band behind the headline is head_layer's own."""
    y = np.linspace(0, 1, H)[:, None]
    top = np.clip(1 - y / 0.32, 0, 1) ** 1.5 * 0.32
    floor = np.clip((y - 0.45) / 0.55, 0, 1) ** 1.3 * 0.78
    a = np.clip(np.maximum(top, floor) + 0.12, 0, 0.88)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = A.GROUND
    rgba[..., 3] = (a * 255).astype(np.uint8)[:, 0][:, None]
    return Image.fromarray(rgba, 'RGBA')


# ---------------------------------------------------------------- text layers
def layers(job, p, tmp):
    """[(png, from, to)] in stacking order: the persistent mark, the headline block (chip, headline, band), the credit
    line, the one line. Timings and fades as in reel.reel."""
    theme = theme_of(job)
    G._ACC = G.ACCENTS[theme]
    hs = job.get('head_size', reel.HEAD_SIZE)
    style = job.get('style') or 'bold'
    if style == 'frame':
        style = 'bold'                      # the bottom waves of `frame` are the plate's here
    head = reel.head_layer(job['headline'], job['label'], f'{tmp}/head.png', job['source'], job['date'], job.get('country'),
                           hs=hs, hst=hs + 20, vivid=True, theme=theme, seed=sum(map(ord, job['name'])), style=style,
                           meta_path=f'{tmp}/meta.png')
    out = [(reel.mark_layer(f'{tmp}/mark.png'), 0, p['end']),
           (head, 0, HEAD_SECS),
           (f'{tmp}/meta.png', min(reel.CREDIT_AT, HEAD_SECS - 0.5), HEAD_SECS),
           (reel.line_layer(job['line'], f'{tmp}/line.png'), p['line_at'], p['end'])]
    return out


def textcheck(job):
    """Headline and line drawn alone (needs the Dubai font), so a bad wrap or a Latin-led line stops in seconds."""
    p = plan(job)
    tmp = tempfile.mkdtemp(prefix='t0-text-')
    try:
        layers(job, p, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check(job):
    p = plan(job)
    s = source(job, build=False)
    z = enlargement(job, s) if s else None
    print(f"breaking: {job['name']}: {p['end']:.1f} s before the end card, line {p['line_at']:.1f} to {p['end']:.1f} s "
          f"(reads in {p['need']:.1f} s), image " + (f'enlarged {z:.2f}x at the end of the push' if z else 'not in uploads, enlargement unchecked'),
          flush=True)
    return p['end']


# ---------------------------------------------------------------- render
def _tight(png, tmp, i):
    """A text layer cropped to the box its pixels occupy (faint glow tails under 3/255 ignored), with the box's
    corner on even pixels for the chroma planes: (png, x, y). The layers are 1080 x 1920 with most of it empty, and a
    full-frame overlay costs 30 ms a frame; the small box costs a fraction."""
    im = Image.open(png).convert('RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 2 else 0).getbbox()
    if not bb:
        return None
    x0, y0, x1, y1 = bb[0] & ~1, bb[1] & ~1, (bb[2] + 1) & ~1, (bb[3] + 1) & ~1
    out = f'{tmp}/tight{i}.png'
    im.crop((x0, y0, x1, y1)).save(out, compress_level=1)
    return out, x0, y0


def _hold(i, fmt, end):
    """A still input (no -loop: decoded once) held for the whole clip with the loop filter, timestamped by frame number."""
    return f'[{i}:v]format={fmt},loop=loop=-1:size=1:start=0,setpts=N/({FPS}*TB),trim=duration={end:.3f}'


def compose(job, p, tmp, lay, body, draft=False):
    """ONE ffmpeg pass: the picture with its push, the scrim, the drifting waves, then the text layers, to a lossless
    intermediate (or a draft). Layers fade as in reel.reel (0.2 s in and out). Stills are decoded once and held
    (loop filter) and each text layer is cropped to its own box, which is what keeps the pass near the cost of the push."""
    theme = theme_of(job)
    grad, mask, scrim = parts(theme)
    path = source(job)
    if not path:
        raise FileNotFoundError(f"{job['image']}: not in uploads (add it to the job's footage)")
    w, h = Image.open(path).size
    x0, y0, cw, ch = window(w, h, job.get('focus', (0.5, 0.5)))
    enlargement(job, path)
    sub = 1 if draft else SUB
    n, end = p['frames'], p['end']
    tight = [(_tight(png, tmp, i), a, z) for i, (png, a, z) in enumerate(lay)]
    args = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', path, '-i', grad, '-i', mask, '-i', scrim]
    fc = [f"[0:v]crop={cw}:{ch}:{x0}:{y0},scale={W * sub}:{H * sub}:flags=lanczos,"
          f"zoompan=z='1+{PUSH}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[v0]",
          _hold(3, 'yuva420p', end) + '[sc]', '[v0][sc]overlay=0:0:format=auto[v1]',
          _hold(2, 'gray', end) + f",crop={W}:{H}:x='mod(t*{NG.SPEED},{W})':y=0[m]",
          _hold(1, 'yuv420p', end) + '[c]', '[c][m]alphamerge[w]',
          '[v1][w]overlay=0:0:format=auto[v2]']
    k, j = 2, 4
    for t, a, z in tight:
        if not t:
            continue
        png, lx, ly = t
        args += ['-i', png]
        fin = f',fade=t=in:st={a:.2f}:d=0.2:alpha=1' if a > 0 else ''
        fout = f',fade=t=out:st={z - 0.2:.2f}:d=0.2:alpha=1' if z < end - 0.01 else ''
        fc += [_hold(j, 'yuva420p', end) + f'{fin}{fout}[l{j}]', f'[v{k}][l{j}]overlay={lx}:{ly}:format=auto[v{k + 1}]']
        k += 1
        j += 1
    fc.append(f'[v{k}]format=yuv420p[v]')
    enc = reel.DRAFT_ENC if draft else reel.inter_enc()
    subprocess.run(args + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-an', '-t', f'{end:.3f}',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p'] + enc + [body], check=True)
    return body


def render(job, out, draft=False):
    """The T0 card to `out` (or `<out>-draft.mp4`). Returns the path. Stage seconds go to render-times.json with
    the profile 'breaking-card'."""
    stages, t = {}, time.time()

    def lap(k):
        nonlocal t
        stages[k] = time.time() - t
        t = time.time()

    p = plan(job)
    theme, sound = theme_of(job), sound_of(job)
    ext = 'mp4' if draft else 'mkv'
    tmp = tempfile.mkdtemp(prefix='t0-')
    try:
        print(f"breaking: {job['name']}: {p['end']:.1f} s, theme {theme}, sound {sound}", flush=True)
        parts(theme)
        lay = layers(job, p, tmp)
        lap('checks')                        # plate from the cache, text layers drawn
        body = compose(job, p, tmp, lay, f'{tmp}/body.{ext}', draft)
        lap('compose')
        if draft:
            done = os.path.splitext(out)[0] + '-draft.mp4'
            shutil.move(body, done)
            return done
        done = outro.append(body, out, sound, bed=None, accent=G.ACCENTS[theme], enc=reel.PROFILES['breaking']['enc'])
        lap('outro')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('render times', reel._record_times(os.path.basename(out), 'breaking-card', stages), flush=True)
    return done


def sheet(job, path):
    """The source picture with the 9:16 window at the start and the end of the push, and the window itself beside it:
    the framing and the enlargement judged on one image (the card has no shots to sheet)."""
    src = source(job)
    im = Image.open(src).convert('RGB')
    w, h = im.size
    x0, y0, cw, ch = window(w, h, job.get('focus', (0.5, 0.5)))
    z = H / ch * (1 + PUSH)
    k = 900 / max(w, h)
    big = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    ex, ey = cw * PUSH / (2 * (1 + PUSH)), ch * PUSH / (2 * (1 + PUSH))
    d.rectangle([x0 * k, y0 * k, (x0 + cw) * k, (y0 + ch) * k], outline=(255, 90, 78), width=3)
    d.rectangle([(x0 + ex) * k, (y0 + ey) * k, (x0 + cw - ex) * k, (y0 + ch - ey) * k], outline=(255, 181, 71), width=2)
    crop = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((round(560 * 9 / 16), 560), Image.LANCZOS)
    out = Image.new('RGB', (big.width + crop.width + 30, max(big.height, crop.height) + 70), (20, 19, 50))
    out.paste(big, (10, 10)); out.paste(crop, (big.width + 20, 10))
    try:
        f = ImageFont.load_default(size=22)
    except TypeError:
        f = ImageFont.load_default()
    ImageDraw.Draw(out).text((12, out.height - 52), f'{os.path.basename(src)} {w}x{h}  window {cw}x{ch} at {x0},{y0}  enlarged x{z:.2f} at the end of the push'
                             + ('  SOFT' if z > reel.MAX_ZOOM else ''), fill=(244, 243, 255), font=f)
    out.save(path, quality=88)
    return path


def warm(job=None):
    """Everything a T0 render reads from a cache, built ahead: the plate for the theme(s), the end-card master and the
    bed for the job's length (or, with no job, every theme and 6 to 24 s). A cache hit costs nothing."""
    t = time.time()
    if job:
        p = plan(job)
        todo = [(theme_of(job), sound_of(job), [math.ceil(p['end']), math.ceil(p['end']) + 1])]
    else:
        todo = [(th, SOUND, list(range(6, 25))) for th in ('crimson', 'cold', 'stylized', 'playful', 'spectacle', 'emerald', 'gold')]
    for theme, sound, lens in todo:
        G._ACC = G.ACCENTS[theme]
        parts(theme)
        outro.card_master(sound, G.ACCENTS[theme])
        for s in lens:
            outro.evolving_bed(sound, float(s))
    print(f'breaking: caches warm ({time.time() - t:.0f} s)', flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    step = sys.argv[1]
    if step == 'warm' and sys.argv[2] == '--all':
        warm()
    else:
        j = json.load(open(sys.argv[2]))
        if step == 'check':
            print('clip %.1f s' % check(j))
        elif step == 'warm':
            warm(j)
        else:
            raise SystemExit(__doc__)
