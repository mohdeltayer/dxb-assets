"""Story-beat picture track (advisor card adv-20261027-road-to-ocarina, approved by Mohammad 27 Oct 2026).

Builds the silent 1080x1920 picture track of a story-beat Reel: every beat is one picture card (an official
still, or a short stretch of an official trailer playing inside the card) over a blurred, slowly drifting copy of
the episode's key art; a beat may be black and white (the past), the one-word emotional beat over a dimmed picture,
the key art full screen (the cover), or official footage full screen (the climax, no text). No text is drawn here:
the headline, the beat lines, the reveal and the series badge are drawn by reel.py on the runner (render_job.py),
where the Dubai font is, so the composite is used as one 9:16 footage file cut on the beat boundaries.

Spec (JSON): {"out": "live/<date>/<name>.mp4", "bg": "<key art in uploads>", "look": "classic",
              "beats": [{"secs": 3.5, "kind": "cover"},
                        {"secs": 2.6, "kind": "card", "src": "oot-x.mp4", "t": 12.0},      # clip in the card
                        {"secs": 2.6, "kind": "card", "src": "oot-still.jpg", "bw": true},  # still, slow push-in
                        {"secs": 2.4, "kind": "word", "src": "oot-x.mp4", "t": 30.0},       # the word over a dimmed picture
                        {"secs": 5.0, "kind": "climax", "src": "oot-x.mp4", "t": 40.0, "focus": 0.5}]}
Sources are read from the uploads folder (cards.U).

B8, Mohammad's points on the episode 6 preview (28 Oct 2026; build desk 29 Oct):
  - A "word" beat always sits over a picture ("One screen وحيدا seems odd without a picture"): it takes `src` (a
    still, or a clip with `t`) shown as a tall card, dimmed, with a darker foot where reel.py draws the word. A word
    beat without `src` fails check().
  - "look": "storybook" ("It could look like a story book where the text is written and we are shifting the camera
    from one part to another with the scenes playing"): the card and word beats sit as mounted pictures on one long
    page in our indigo (paper grain, soft lamp-light vignette, a small ornament under each picture), the scenes
    playing inside them, and the camera glides from one picture to the next between beats (`move`: seconds of the
    glide, `pre` of them before the cut; default 0.9 and 0.3). The cover and the climax stay full screen, cut in
    and out as in the classic look; the camera settles onto the page after them. A beat with `"stay": true` keeps
    the previous picture's place on the page (the scene changes inside the same frame with a short dissolve), so a
    line that runs over two beats is never pulled along by a camera move. build() returns `motion`: the page moves
    in track seconds, which the job carries as `page_motion` so reel.py moves the beat lines with the page.
    "classic" (the default) builds exactly what it built before.

    python3 storybeat.py <spec.json>          -> builds, prints {"out", "cuts", "total", "motion"}
    python3 storybeat.py check <spec.json>    -> the spec check only
"""
import json, os, subprocess, sys, tempfile, shutil

sys.path.insert(0, os.path.dirname(__file__))
import cards as C   # noqa: E402

W, H, FPS = 1080, 1920, 30
CARD_W, CARD_H = 940, 528          # a 16:9 card, centred above the line band
CARD_Y = 560                       # top of the card: clear of the headline zone's lower edge and of the low lines
WORD_W, WORD_H = 940, 1000         # the word beat's picture: a tall card whose foot carries the word (reel.py draws
WORD_Y = 470                       # the low line at SAFE_BOTTOM - 40 = 1440), so the word sits on the picture
BORDER = 6
CLIMAX_H = 1216                    # climax frame height: 1216/720 = 1.69x for a 720p source
VIDEO = ('.mp4', '.mov', '.mkv', '.webm')
KINDS = ('cover', 'card', 'word', 'climax')
LOOKS = ('classic', 'storybook')
PAGE_KINDS = ('card', 'word')      # the beats that sit on the storybook page


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(' '.join(cmd[:6]) + ' ...\n' + r.stderr[-1500:])


def check(spec, files=False):
    """Stop on a spec that would build a wrong track: unknown kinds or looks, a beat without its picture, a clip
    without its start, and (B8, 29 Oct 2026) a one-word beat over a bare ground. `files=True` also checks that
    every source is in uploads."""
    errs = []
    look = spec.get('look', 'classic')
    if look not in LOOKS:
        errs.append(f'look {look!r}: one of {", ".join(LOOKS)}')
    if not spec.get('beats'):
        errs.append('no beats')
    if not spec.get('bg') and look == 'classic':
        errs.append('bg: the key art for the blurred ground')
    prev_page = False
    for i, b in enumerate(spec.get('beats') or []):
        k = b.get('kind')
        if k not in KINDS:
            errs.append(f'beat {i}: kind {k!r}, one of {", ".join(KINDS)}')
            continue
        try:
            if float(b['secs']) <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            errs.append(f'beat {i}: secs must be a positive number')
        src = b.get('src')
        if k == 'word' and not src:
            errs.append(f'beat {i}: a word beat sits over a picture (Mohammad, 28 Oct 2026): give it src, a still or a '
                        'clip with t')
        elif k in ('card', 'climax') and not src:
            errs.append(f'beat {i}: a {k} beat needs src')
        elif k == 'cover' and not (src or spec.get('bg')):
            errs.append(f'beat {i}: a cover needs src or the spec\'s bg')
        if src and src.lower().endswith(VIDEO) and 't' not in b:
            errs.append(f'beat {i}: {src} is a clip; give its start t (seconds)')
        if files:
            for f in [src] + ([spec.get('bg')] if i == 0 and spec.get('bg') else []):
                if f and not os.path.exists(os.path.join(C.U, f)):
                    errs.append(f'beat {i}: {f} is not in uploads')
        if b.get('stay'):
            if look != 'storybook':
                errs.append(f'beat {i}: stay is for the storybook look')
            elif k not in PAGE_KINDS or not prev_page:
                errs.append(f'beat {i}: stay keeps the previous picture\'s place; it needs a card or word beat after one')
        prev_page = k in PAGE_KINDS
    for key in ('move', 'pre'):
        if key in spec and not (isinstance(spec[key], (int, float)) and spec[key] >= 0):
            errs.append(f'{key} must be a number of seconds')
    if spec.get('pre', 0.3) > spec.get('move', 0.9):
        errs.append('pre is part of move: pre <= move')
    if errs:
        raise ValueError('storybeat spec: ' + '; '.join(errs))
    return True


def _ground(bg, secs, seed, dark):
    """The blurred, slowly drifting key art: scaled to cover, zoompan drift, heavy blur, dimmed."""
    frames = int(round(secs * FPS))
    zoom = "zoompan=z='1.06+0.0004*on':x='iw/2-(iw/zoom/2)+%d*sin(on/90)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d" % (
        18 + 6 * (seed % 3), frames, W, H, FPS)
    bright = -0.26 if dark else -0.12
    return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},{zoom},"
            f"boxblur=26:3,eq=brightness={bright}:saturation=1.1")


#: The word beat's picture: dimmed, a little less colour, and a darker foot so the large word reads over it.
WORD_DIM = 'eq=brightness=-0.16:saturation=0.8'


def _foot(path, w, h):
    """A PNG the size of the word picture, transparent at the top, dark at the foot (where the word sits)."""
    from PIL import Image
    g = Image.new('L', (1, h), 0)
    for y in range(h):
        t = max(0.0, (y - h * 0.45) / (h * 0.55))
        g.putpixel((0, y), int(185 * t ** 1.4))
    im = Image.new('RGBA', (w, h), (10, 9, 30, 255))
    im.putalpha(g.resize((w, h)))
    im.save(path)
    return path


def _card_src(b, src, w, h, frames, secs, bw):
    """ffmpeg input args and the filter that makes the picture inside a card of w x h (a clip playing, or a still
    with a slow push-in)."""
    if src.lower().endswith(VIDEO):
        fx = float(b.get('focus', 0.5))
        return (['-ss', str(b['t']), '-t', f'{secs:.3f}', '-i', src],
                f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}:(iw-{w})*{fx}:(ih-{h})/2{bw}")
    fx = float(b.get('focus', 0.5))
    return (['-loop', '1', '-t', f'{secs:.3f}', '-i', src],
            f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2}:(iw-{w*2})*{fx}:(ih-{h*2})/2,"
            f"zoompan=z='1.0+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={FPS}{bw}")


def beat_clip(b, bg, out, seed):
    secs = float(b['secs'])
    kind = b['kind']
    src = os.path.join(C.U, b['src']) if b.get('src') else None
    bw = ',hue=s=0' if b.get('bw') else ''
    frames = int(round(secs * FPS))
    if kind == 'climax':                       # official footage at climax size: the frame CLIMAX_H tall (a 720p
        fx = float(b.get('focus', 0.5))        # source stays under the 2x enlargement cap), cropped to the full
        hh = int(b.get('height', CLIMAX_H))    # width at `focus`, over a blurred, dimmed copy of the same footage
        fc = (f"[0:v]fps={FPS},split[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.28{bw}[g];"
              f"[b]scale=-2:{hh}:flags=lanczos,crop={W}:{hh}:(iw-{W})*{fx}:0{bw}[f];"
              f"[g][f]overlay=0:{(H - hh) // 2},setsar=1[v]")
        _run(['ffmpeg', '-v', 'error', '-y', '-ss', str(b['t']), '-t', f'{secs:.3f}', '-i', src, '-an', '-filter_complex', fc,
              '-map', '[v]', '-frames:v', str(frames), '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out])
        return
    if kind == 'cover':                        # the key art full screen, a slow push-in, no blur
        fx = float(b.get('focus', 0.5))
        img = os.path.join(C.U, b.get('src') or bg)
        vf = (f"scale=-2:{H*2},crop={W*2}:{H*2}:(iw-{W*2})*{fx}:0,"
              f"zoompan=z='1.0+0.0007*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}{bw},setsar=1")
        _run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', f'{secs:.3f}', '-i', img, '-vf', vf, '-frames:v', str(frames),
              '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out])
        return
    ground = _ground(bg, secs, seed, dark=(kind == 'word')) + bw
    inputs = ['-loop', '1', '-t', f'{secs:.3f}', '-i', os.path.join(C.U, bg)]
    if kind == 'word':                         # B8: the word over its picture, a tall dimmed card with a dark foot
        ins, card = _card_src(b, src, WORD_W, WORD_H, frames, secs, bw)
        inputs += ins + ['-loop', '1', '-t', f'{secs:.3f}', '-i', _foot(out + '.foot.png', WORD_W, WORD_H)]
        x = (W - WORD_W) // 2
        sx, sy = x - BORDER + 10, WORD_Y - BORDER + 16
        fc = (f"[0:v]{ground},drawbox=x={sx}:y={sy}:w={WORD_W+2*BORDER}:h={WORD_H+2*BORDER}:color=black@0.45:t=fill[g];"
              f"[1:v]{card},{WORD_DIM},format=rgba[p];[2:v]format=rgba[f];[p][f]overlay=0:0,"
              f"pad={WORD_W+2*BORDER}:{WORD_H+2*BORDER}:{BORDER}:{BORDER}:color=white[c];"
              f"[g][c]overlay={x-BORDER}:{WORD_Y-BORDER},setsar=1[v]")
    else:
        if src.lower().endswith(VIDEO):        # a stretch of official footage playing inside the card
            inputs += ['-ss', str(b['t']), '-t', f'{secs:.3f}', '-i', src]
            card = f"[1:v]fps={FPS},scale={CARD_W}:{CARD_H}:force_original_aspect_ratio=increase,crop={CARD_W}:{CARD_H}{bw}"
        else:                                  # an official still: a slow push-in inside the card
            inputs += ['-loop', '1', '-t', f'{secs:.3f}', '-i', src]
            card = (f"[1:v]scale={CARD_W*2}:{CARD_H*2}:force_original_aspect_ratio=increase,crop={CARD_W*2}:{CARD_H*2},"
                    f"zoompan=z='1.0+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={CARD_W}x{CARD_H}:fps={FPS}{bw}")
        x = (W - CARD_W) // 2
        sx, sy = x - BORDER + 10, CARD_Y - BORDER + 16     # a soft dark band under the card lifts it off the ground
        fc = (f"[0:v]{ground},drawbox=x={sx}:y={sy}:w={CARD_W+2*BORDER}:h={CARD_H+2*BORDER}:color=black@0.45:t=fill[g];"
              f"{card},pad={CARD_W+2*BORDER}:{CARD_H+2*BORDER}:{BORDER}:{BORDER}:color=white[c];"
              f"[g][c]overlay={x-BORDER}:{CARD_Y-BORDER},setsar=1[v]")
    try:
        _run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[v]', '-an', '-frames:v', str(frames),
              '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out])
    finally:
        if os.path.exists(out + '.foot.png'):
            os.remove(out + '.foot.png')


def build(spec):
    check(spec)
    if spec.get('look', 'classic') == 'storybook':
        import storybook
        return storybook.build(spec)
    tmp = tempfile.mkdtemp(prefix='storybeat-')
    try:
        parts, cuts, t = [], [], 0.0
        for i, b in enumerate(spec['beats']):
            p = os.path.join(tmp, f'b{i:02d}.mp4')
            beat_clip(b, spec['bg'], p, i)
            parts.append(p)
            cuts.append(round(t, 3))
            t += float(b['secs'])
        lst = os.path.join(tmp, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
        out = spec['out']
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        _run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'libx264', '-preset', 'medium',
              '-crf', '16', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out])
        return cuts, round(t, 3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        check(json.load(open(sys.argv[2])), files=True)
        print('storybeat spec ok')
        sys.exit(0)
    spec = json.load(open(sys.argv[1]))
    res = build(spec)
    cuts, total = res[0], res[1]
    out = {'out': spec['out'], 'cuts': cuts, 'total': total}
    if len(res) > 2:
        out['motion'] = res[2]
    print(json.dumps(out))
