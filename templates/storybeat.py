"""Story-beat picture track (advisor card adv-20261027-road-to-ocarina, approved by Mohammad 27 Oct 2026).

Builds the silent 1080x1920 picture track of a story-beat Reel: every beat is one picture card (an official
still, or a short stretch of an official trailer playing inside the card) over a blurred, slowly drifting copy of
the episode's key art; a beat may be black and white (the past), a bare ground for the one-word emotional beat, the
key art full screen (the cover), or official footage full screen (the climax, no text). No text is drawn here: the
headline, the beat lines, the reveal and the series badge are drawn by reel.py on the runner (render_job.py), where
the Dubai font is, so the composite is used as one 9:16 footage file cut on the beat boundaries.

Spec (JSON): {"out": "live/<date>/<name>.mp4", "bg": "<key art in uploads>",
              "beats": [{"secs": 3.5, "kind": "cover"},
                        {"secs": 2.6, "kind": "card", "src": "oot-x.mp4", "t": 12.0},      # clip in the card
                        {"secs": 2.6, "kind": "card", "src": "oot-still.jpg", "bw": true},  # still, slow push-in
                        {"secs": 2.4, "kind": "word"},                                      # ground only, darker
                        {"secs": 5.0, "kind": "climax", "src": "oot-x.mp4", "t": 40.0, "focus": 0.5}]}
Sources are read from the uploads folder (cards.U). python3 storybeat.py <spec.json>  -> prints the cut list.
"""
import json, os, subprocess, sys, tempfile, shutil

sys.path.insert(0, os.path.dirname(__file__))
import cards as C   # noqa: E402

W, H, FPS = 1080, 1920, 30
CARD_W, CARD_H = 940, 528          # a 16:9 card, centred above the line band
CARD_Y = 560                       # top of the card: clear of the headline zone's lower edge and of the low lines
BORDER = 6
VIDEO = ('.mp4', '.mov', '.mkv', '.webm')


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(' '.join(cmd[:6]) + ' ...\n' + r.stderr[-1500:])


def _ground(bg, secs, seed, dark):
    """The blurred, slowly drifting key art: scaled to cover, zoompan drift, heavy blur, dimmed."""
    frames = int(round(secs * FPS))
    zoom = "zoompan=z='1.06+0.0004*on':x='iw/2-(iw/zoom/2)+%d*sin(on/90)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d" % (
        18 + 6 * (seed % 3), frames, W, H, FPS)
    bright = -0.32 if dark else -0.20
    return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},{zoom},"
            f"boxblur=26:3,eq=brightness={bright}:saturation=0.85")


def beat_clip(b, bg, out, seed):
    secs = float(b['secs'])
    kind = b['kind']
    src = os.path.join(C.U, b['src']) if b.get('src') else None
    bw = ',hue=s=0' if b.get('bw') else ''
    frames = int(round(secs * FPS))
    if kind == 'climax':                       # official footage full screen, the 9:16 window at `focus`
        fx = float(b.get('focus', 0.5))
        crop = f"crop=ih*9/16:ih:(iw-ih*9/16)*{fx}:0"
        vf = f"{crop},scale={W}:{H}:flags=lanczos,fps={FPS}{bw},setsar=1"
        _run(['ffmpeg', '-v', 'error', '-y', '-ss', str(b['t']), '-t', f'{secs:.3f}', '-i', src, '-an', '-vf', vf,
              '-frames:v', str(frames), '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out])
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
    if kind == 'word':
        fc = f"[0:v]{ground},setsar=1[v]"
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
    _run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[v]', '-an', '-frames:v', str(frames),
          '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out])


def build(spec):
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
    spec = json.load(open(sys.argv[1]))
    cuts, total = build(spec)
    print(json.dumps({'out': spec['out'], 'cuts': cuts, 'total': total}))
