"""Digital Lounge sonic identity: a short jingle and a quiet background
bed built from the same motif, all synthesised here, so the music is
original and owned (no library, no claims).

Two directions, both in D:
- 'neon':  D F# A E, a bright rising add9 motif, glass bell and pluck.
- 'hijaz': D Eb F# A, the Hijaz tetrachord, on a plucked string that
  reads as oud, over the same pad.

`jingle(style, path)` writes about 3 seconds; `bed(style, path, bars=8)`
writes a seamless loop at 96 BPM (16 bars is 40 seconds, longer than
most clips, so it rarely repeats) meant to sit under a silent clip.
Write the bed as .wav: mp3 pads the ends and clicks when looped. `under(video, bed, out)` lays the bed under a video
that has no sound, looped and faded to the clip length.
"""
import os
import subprocess
import numpy as np
from pedalboard import (Pedalboard, Reverb, LowpassFilter, HighpassFilter,
                        Compressor, Limiter, Chorus)

SR = 48000


def hz(note):
    """'D4' / 'Eb5' / 'F#3' -> Hz."""
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n, rest = note[0], note[1:]
    acc = 0
    while rest and rest[0] in '#b':
        acc += 1 if rest[0] == '#' else -1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + names[n] + acc
    return 440.0 * 2 ** ((midi - 69) / 12)


MOTIF = {'neon': ['D5', 'F#5', 'A5', 'E6'],
         'hijaz': ['D5', 'Eb5', 'F#5', 'A5']}
CHORD = {'neon': ['D3', 'A3', 'D4', 'F#4', 'E5'],
         'hijaz': ['D3', 'A3', 'D4', 'F#4', 'A4']}
# Bed progressions, two bars per chord.
PROG = {'neon': [['D3', 'F#3', 'A3', 'E4'], ['B2', 'D3', 'F#3', 'A3'],
                 ['G2', 'B2', 'D3', 'F#3'], ['A2', 'C#3', 'E3', 'A3']],
        'hijaz': [['D3', 'F#3', 'A3', 'D4'], ['Eb3', 'G3', 'Bb3', 'Eb4'],
                  ['D3', 'F#3', 'A3', 'D4'], ['C3', 'Eb3', 'G3', 'C4']]}


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.3, s=0.0, r=0.2):
    """Attack, exponential decay to sustain, release at the end."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    rn = int(r * SR)
    if rn and rn < n:
        e[-rn:] *= np.linspace(1, 0, rn)
    return e


def pluck(freq, dur, bright=0.5):
    """Karplus-Strong string: reads as a clean oud or harp pluck."""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    rng = np.random.default_rng(int(freq * 100))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    decay = 0.996
    for i in range(n):
        j = i % p
        out[i] = buf[j]
        buf[j] = decay * (bright * buf[j] + (1 - bright) * 0.5 * (buf[j] + buf[(j + 1) % p]))
    return out * env(n, a=0.002, d=dur, r=0.05)


def bell(freq, dur, ratio=2.0, index=2.2):
    """FM glass bell."""
    t = t_(dur)
    mod = index * np.exp(-t / 0.35) * np.sin(2 * np.pi * freq * ratio * t)
    return np.sin(2 * np.pi * freq * t + mod) * env(len(t), a=0.003, d=0.6, r=0.1)


def pad(notes, dur, attack=0.6):
    """Detuned saw pad, darkened later by a low-pass."""
    t = t_(dur)
    out = np.zeros(len(t))
    for nt in notes:
        f = hz(nt)
        for det in (-0.08, 0.0, 0.08):
            ph = (f * (1 + det / 100) * t) % 1.0
            out += (2 * ph - 1) * 0.33
    out /= max(1, len(notes))
    e = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / 0.8)
    return out * e


def sub(freq, dur):
    t = t_(dur)
    f = freq * (1 + 0.6 * np.exp(-t / 0.05))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), a=0.002, d=0.5, r=0.1)


def riser(dur):
    t = t_(dur)
    rng = np.random.default_rng(7)
    return rng.normal(0, 1, len(t)) * (t / dur) ** 2 * 0.25


def place(buf, sig, at):
    i = int(at * SR)
    end = min(len(buf), i + len(sig))
    buf[i:end] += sig[:end - i]


def _lufs(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    return float(out.rsplit('I:', 1)[1].split('LUFS')[0])


def _write(st, path, loud=-16):
    """Stereo float array (2, n) -> file at a static gain to `loud` LUFS.
    Static, not ffmpeg's dynamic loudnorm, so a loop's ends still meet."""
    import wave
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.5
    tmp = path + '.raw.wav'
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st.T, -1, 1) * 32767).astype('<i2').tobytes())
    gain = loud - _lufs(tmp)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-af',
           f'volume={gain:.2f}dB,alimiter=limit=0.84:level=false', '-ar', str(SR)]
    cmd += (['-c:a', 'libmp3lame', '-b:a', '192k'] if path.endswith('.mp3') else [])
    subprocess.run(cmd + [path], check=True)
    os.remove(tmp)
    return path


def _stereo(y):
    st = np.stack([y, y]).astype(np.float32)
    return Pedalboard([Chorus(rate_hz=0.3, depth=0.15, mix=0.25)])(st, SR)


def jingle(style, path):
    dur = 3.4
    buf = np.zeros(int(dur * SR))
    place(buf, riser(0.35) * 0.5, 0.0)
    step = 0.16
    for k, nt in enumerate(MOTIF[style]):
        at = 0.35 + k * step
        if style == 'hijaz':
            place(buf, pluck(hz(nt), 1.2, bright=0.6) * 0.9, at)
            place(buf, bell(hz(nt) * 2, 0.8) * 0.12, at)
        else:
            place(buf, bell(hz(nt), 1.2) * 0.6, at)
            place(buf, pluck(hz(nt) / 2, 0.8, bright=0.3) * 0.5, at)
    hit = 0.35 + 4 * step
    chord = Pedalboard([LowpassFilter(1800)])(pad(CHORD[style], dur - hit, attack=0.05)
                                              .astype(np.float32), SR)
    place(buf, chord * 0.45, hit)
    place(buf, sub(hz('D2'), 1.2) * 0.8, hit)
    place(buf, bell(hz(CHORD[style][-1]) * 2, 1.6, ratio=3.5, index=1.2) * 0.2, hit + 0.02)
    fx = Pedalboard([HighpassFilter(35), Reverb(room_size=0.55, wet_level=0.28, dry_level=0.8),
                     Compressor(threshold_db=-14, ratio=2.5), Limiter(-1.0)])
    y = _stereo(fx(buf.astype(np.float32), SR))
    fade = int(0.4 * SR)
    y[:, -fade:] *= np.linspace(1, 0, fade)
    return _write(y, path, loud=-14)


def bed(style, path, bars=16, bpm=96):
    beat = 60 / bpm
    bar = 4 * beat
    length = bars * bar
    tail = 3.0
    buf = np.zeros(int((length + tail) * SR))
    prog = PROG[style]
    for b in range(bars):
        chord = prog[(b // 2) % len(prog)]
        at = b * bar
        if b % 2 == 0:
            place(buf, pad(chord, 2 * bar + 0.5, attack=1.2) * 0.35, at)
            place(buf, sub(hz(chord[0]) / 2, 1.5) * 0.25, at)
        # quiet eighth-note arpeggio on the chord, an octave up
        for e8 in range(8):
            nt = chord[[0, 1, 2, 3, 2, 1, 2, 3][e8]]
            f = hz(nt) * 2
            sig = pluck(f, 0.5, bright=0.35) if style == 'hijaz' else bell(f, 0.45, index=1.0)
            place(buf, sig * (0.16 if e8 % 2 == 0 else 0.10), at + e8 * beat / 2)
    # the jingle's motif, softly, every 8 bars (bar 5, 13, ...)
    for b0 in range(4, bars, 8):
        for k, nt in enumerate(MOTIF[style]):
            sig = pluck(hz(nt), 1.0, 0.55) if style == 'hijaz' else bell(hz(nt), 1.0)
            place(buf, sig * 0.22, b0 * bar + k * beat / 2)
    fx = Pedalboard([LowpassFilter(5000), HighpassFilter(40),
                     Reverb(room_size=0.7, wet_level=0.3, dry_level=0.7),
                     Compressor(threshold_db=-18, ratio=2), Limiter(-1.0)])
    y = _stereo(fx(buf.astype(np.float32), SR))
    n = int(length * SR)
    loop = y[:, :n].copy()
    loop[:, :y.shape[1] - n] += y[:, n:]  # wrap the tail so the loop is seamless
    return _write(loop, path, loud=-18)


def under(video, bed_path, out, level_db=-2, jingle_path=None):
    """Bed under a silent video: looped, trimmed and faded to its length.
    With `jingle_path` the jingle closes the clip, the bed fading out
    under it."""
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                              '-of', 'csv=p=0', video], capture_output=True, text=True).stdout)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', video, '-stream_loop', '-1', '-i', bed_path]
    if jingle_path:
        j = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                  '-of', 'csv=p=0', jingle_path], capture_output=True, text=True).stdout)
        at = max(0.0, d - j)
        fc = (f'[1:a]volume={level_db}dB,afade=t=in:d=0.4,afade=t=out:st={max(0, at - 0.3):.2f}:d=1.0,'
              f'atrim=0:{d:.2f}[b];[2:a]adelay={int(at * 1000)}:all=1[j];'
              f'[b][j]amix=inputs=2:duration=first:normalize=0[a]')
        cmd += ['-i', jingle_path, '-filter_complex', fc, '-map', '0:v', '-map', '[a]']
    else:
        af = f'volume={level_db}dB,afade=t=in:d=0.4,afade=t=out:st={max(0, d - 1.2):.2f}:d=1.2'
        cmd += ['-map', '0:v', '-map', '1:a', '-af', af]
    subprocess.run(cmd + ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-t', f'{d:.2f}',
                          '-movflags', '+faststart', out], check=True)
    return out
