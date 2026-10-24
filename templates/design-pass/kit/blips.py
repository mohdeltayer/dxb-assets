"""Motion kit sound (pilot, advisor memo 24 Oct 2026): tiny UI blips built from our four-note motif
(D F# A E, the neon flavour in sonic.py), mixed well under the trailer or the bed, never over speech.

    python3 blips.py <video in> <moments.json> <video out>

moments.json is a list of [seconds, kind]; kinds: tick, settle, open, press, unlock, wipe. The video
stream is copied; the audio is the Reel's own track with the blips added at BLIP_DB under its level.
"""
import json, subprocess, sys
import numpy as np

SR = 48000
NOTE = {'D6': 1174.66, 'F#6': 1479.98, 'A6': 1760.0, 'E7': 2637.02, 'D7': 2349.32}
BLIP_DB = -14            # peak of a blip against the Reel's own peak: under the music, still heard on a phone


def tone(f, ms, gain=1.0, decay=28.0):
    """A soft sine with its octave, a 3 ms attack and a quick exponential tail: tonal, never noise."""
    n = int(SR * ms / 1000)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.003) * np.exp(-t * decay)
    return gain * env * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t))


def seq(notes, step_ms, ms, gain=1.0):
    out = np.zeros(int(SR * (step_ms * (len(notes) - 1) + ms) / 1000))
    for i, f in enumerate(notes):
        s = tone(f, ms, gain)
        o = int(SR * step_ms * i / 1000)
        out[o:o + len(s)] += s
    return out


KINDS = {
    'tick':   lambda: tone(NOTE['A6'], 40, 0.35, decay=60),                     # each step of a count
    'settle': lambda: tone(NOTE['D6'], 160, 0.8) + tone(NOTE['A6'], 160, 0.5),   # the count lands
    'open':   lambda: seq([NOTE['D6'], NOTE['A6']], 60, 120, 0.7),              # photo box opens
    'press':  lambda: tone(NOTE['F#6'], 90, 0.7, decay=40),                      # chip press
    'unlock': lambda: seq([NOTE['D6'], NOTE['F#6'], NOTE['A6'], NOTE['E7']], 55, 140, 0.6),
    'wipe':   lambda: tone(NOTE['E7'], 70, 0.4, decay=45),                       # card transition
}


def mix(video, moments, out):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    peak = float(np.abs(a).max()) or 0.5
    g = peak * 10 ** (BLIP_DB / 20)
    for t, kind in moments:
        b = KINDS[kind]()
        b = (b / np.abs(b).max() * g).astype(np.float32)
        o = int(round(t * SR))
        n = min(len(b), len(a) - o)
        if n > 0:
            a[o:o + n] += b[:n, None]
    a = np.clip(a, -1, 1)
    wav = out + '.blips.f32'
    a.tofile(wav)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', wav,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                    out], check=True)
    import os
    os.remove(wav)
    return out


if __name__ == '__main__':
    mix(sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3])
