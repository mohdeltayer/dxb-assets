"""Digital Lounge sonic identity: a short jingle and a quiet background
bed built from the same four-note motif, all synthesised here, so the
music is original and owned (no library, no claims).

Every flavour keeps the motif's shape (four notes, rising, same timing)
and changes the mode, the instruments, the tempo and the rhythm:

    neon       everyday. D F# A E on glass bells.
    hijaz      regional. D Eb F# A on a plucked, oud-like string.
  occasions
    ramadan    hijaz, slow, oud and qanun, a soft frame drum.
    eid        hijaz, bright, oud with bells, the maqsum rhythm.
    halloween  D F A Eb, music box over a low drone, minor.
    christmas  the neon motif on glockenspiel; a soft celesta, one light
               shake of bells a bar (the busier first cut was distracting).
  post types
    stats      sales charts (Famitsu, Circana): fast, a kick and hats,
               sixteenth-note arpeggio that climbs like a counter.
    breaking   a repeated pulse and three pick-up notes before the motif.
    launch     out now and release dates: bright, a light beat.
    digest     the Friday weekly: neon with a soft beat, for under a voice.

No noise swells and no saw pads (Mohammad, 28 Sep 2026): both read as a
whoosh or a plane. Percussion is tonal (sine and FM hits), never noise.

`jingle(style, path)` writes about 3.5 seconds at -14 LUFS.
`bed(style, path, bars=16)` writes a seamless loop at -18 LUFS; write it
as .wav, since mp3 pads the ends and clicks when looped.
`under(video, bed, out, jingle_path=None)` lays the bed under a video
with no sound of its own, closing on the jingle.
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


NEON = dict(motif=['D5', 'F#5', 'A5', 'E6'], chord=['D3', 'A3', 'D4', 'F#4', 'E5'],
            prog=[['D3', 'F#3', 'A3', 'E4'], ['B2', 'D3', 'F#3', 'A3'],
                  ['G2', 'B2', 'D3', 'F#3'], ['A2', 'C#3', 'E3', 'A3']])
HIJAZ = dict(motif=['D5', 'Eb5', 'F#5', 'A5'], chord=['D3', 'A3', 'D4', 'F#4', 'A4'],
             prog=[['D3', 'F#3', 'A3', 'D4'], ['Eb3', 'G3', 'Bb3', 'Eb4'],
                   ['D3', 'F#3', 'A3', 'D4'], ['C3', 'Eb3', 'G3', 'C4']])

# lead: the motif's voice; arp: the bed's arpeggio; drums: a pattern name;
# step: seconds between motif notes in the jingle; sixteenths: arp speed.
FLAVOURS = {
    'neon':      dict(NEON, lead='bell', arp='bell', bpm=96, step=0.16),
    'hijaz':     dict(HIJAZ, lead='oud', arp='oud', bpm=96, step=0.16),
    'ramadan':   dict(HIJAZ, lead='oud', arp='qanun', bpm=76, step=0.2, drums='daf_slow'),
    'eid':       dict(HIJAZ, chord=['D3', 'A3', 'D4', 'F#4', 'A4', 'D5'], lead='oud+bell',
                      arp='qanun', bpm=108, step=0.14, drums='maqsum'),
    'halloween': dict(motif=['D5', 'F5', 'A5', 'Eb6'], chord=['D2', 'A2', 'D3', 'F3', 'A3'],
                      prog=[['D3', 'F3', 'A3', 'D4'], ['Bb2', 'D3', 'F3', 'A3'],
                            ['G2', 'Bb2', 'D3', 'G3'], ['A2', 'C#3', 'E3', 'G3']],
                      lead='musicbox', arp='musicbox', bpm=84, step=0.2, drone='D2'),
    'christmas': dict(NEON, lead='glock+bell', arp='celesta', bpm=88, step=0.16, drums='sleigh_soft'),
    'stats':     dict(NEON, lead='bell', arp='bell', bpm=124, step=0.11, drums='pulse',
                      sixteenths=True, hits=True),
    'breaking':  dict(NEON, lead='bell', arp='pluck', bpm=112, step=0.12, drums='tick',
                      pickup=['A4', 'A4', 'A4']),
    'launch':    dict(NEON, lead='bell+glock', arp='bell', bpm=116, step=0.13, drums='light'),
    'digest':    dict(NEON, lead='bell', arp='bell', bpm=96, step=0.16, drums='soft'),
    # everyday variations (Mohammad, 1 Oct 2026: the one jingle on every post
    # had gone stale). Same four notes and direction, so it still reads as
    # Digital Lounge; rhythm, voice, harmony and the closing chord change.
    'neon_b':    dict(NEON, chord=['D3', 'A3', 'D4', 'F#4', 'B4', 'E5'], lead='marimba',
                      arp='marimba', bpm=100, step=0.15, rhythm=[1, 1, 1.6]),
    'neon_c':    dict(NEON, chord=['D3', 'A3', 'C#4', 'F#4', 'A4', 'E5'], lead='vibes',
                      arp='vibes', bpm=88, step=0.18, harmony=['B4', 'D5', 'F#5', 'C#6']),
    'neon_d':    dict(NEON, lead='glock', arp='glock', bpm=104, step=0.12,
                      echo=True, drums='soft'),
    'neon_e':    dict(NEON, chord=['D3', 'A3', 'D4', 'G4', 'A4', 'E5'], lead='pluck+bell',
                      arp='pluck', bpm=96, step=0.14, rhythm=[0.75, 1.25, 1], roll=True),
}

# The everyday jingle rotates through these, one per post, so a run of posts
# never repeats the same sting; the occasion and post-type flavours stay fixed.
EVERYDAY = ['neon', 'neon_b', 'neon_c', 'neon_d', 'neon_e']


def rotate(key):
    """An everyday flavour picked from the post's own name, stable per post."""
    import zlib
    return EVERYDAY[zlib.crc32(str(key).encode()) % len(EVERYDAY)]


def _times(F, at0):
    """Motif note times: even steps, or the flavour's own rhythm."""
    gaps = F.get('rhythm', [1, 1, 1])
    out, t = [at0], at0
    for g in gaps:
        t += F['step'] * g
        out.append(t)
    return out


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


# ---- instruments ---------------------------------------------------------

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


def glock(freq, dur):
    """Glockenspiel: a pure tone with the bar's inharmonic partials."""
    t = t_(dur)
    x = (np.sin(2 * np.pi * freq * t)
         + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.12)
         + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / 0.05))
    return x * env(len(t), a=0.001, d=0.7, r=0.08)


def musicbox(freq, dur):
    """Music box tine, slightly out of tune and wavering: the Halloween voice."""
    t = t_(dur)
    wob = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    ph = 2 * np.pi * np.cumsum(freq * wob) / SR
    x = np.sin(ph) + 0.3 * np.sin(3.02 * ph) * np.exp(-t / 0.08)
    return x * env(len(t), a=0.001, d=0.45, r=0.08)


def marimba(freq, dur):
    """Wooden bar: a short FM knock with a fourth-partial ring."""
    t = t_(dur)
    mod = 1.4 * np.exp(-t / 0.05) * np.sin(2 * np.pi * freq * 4 * t)
    return np.sin(2 * np.pi * freq * t + mod) * env(len(t), a=0.002, d=0.35, r=0.08)


def vibes(freq, dur):
    """Vibraphone: a soft sine with the motor's slow tremolo."""
    t = t_(dur)
    trem = 1 - 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.0 * t))
    x = np.sin(2 * np.pi * freq * t) + 0.18 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t / 0.2)
    return x * trem * env(len(t), a=0.004, d=1.0, r=0.15)


def voice(name, freq, dur):
    if '+' in name:
        a, b = name.split('+')
        return voice(a, freq, dur) * 0.75 + voice(b, freq * 2, dur) * 0.2
    return {'bell': lambda: bell(freq, dur),
            'oud': lambda: pluck(freq, dur, bright=0.6),
            'qanun': lambda: pluck(freq, dur, bright=0.3),
            'pluck': lambda: pluck(freq, dur, bright=0.45),
            'glock': lambda: glock(freq, dur),
            'musicbox': lambda: musicbox(freq, dur),
            'celesta': lambda: bell(freq, dur, ratio=4.0, index=0.6),
            'marimba': lambda: marimba(freq, dur),
            'vibes': lambda: vibes(freq, dur)}[name]()


def warm(notes, dur, attack=0.05, decay=1.1):
    """Sine chord that fades on its own: the jingle's closing chord."""
    t = t_(dur)
    out = np.zeros(len(t))
    for nt in notes:
        f = hz(nt)
        out += np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    out /= max(1, len(notes))
    return out * np.minimum(1, t / attack) * np.exp(-t / decay)


def hold(notes, dur, attack=0.4, release=0.6):
    """Sustained sine chord for the bed: no saw buzz, no swell."""
    t = t_(dur)
    out = np.zeros(len(t))
    for nt in notes:
        f = hz(nt)
        out += np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)
    out /= max(1, len(notes))
    return out * np.minimum(1, t / attack) * np.clip((dur - t) / release, 0, 1)


def sub(freq, dur):
    t = t_(dur)
    f = freq * (1 + 0.6 * np.exp(-t / 0.05))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), a=0.002, d=0.5, r=0.1)


# ---- percussion, all tonal ----------------------------------------------

def _drop(f0, f1, tau, decay, dur):
    t = t_(dur)
    f = f1 + (f0 - f1) * np.exp(-t / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), a=0.001, d=decay, r=0.02)


def _mix(a, b):
    out = np.zeros(max(len(a), len(b)))
    out[:len(a)] += a
    out[:len(b)] += b
    return out


def kick():
    return _drop(150, 48, 0.03, 0.14, 0.4)


def dum():
    """Frame drum, low stroke."""
    return _mix(_drop(140, 78, 0.02, 0.2, 0.45), 0.2 * _drop(260, 200, 0.01, 0.05, 0.1))


def tak():
    """Frame drum, rim stroke: a short pitched knock."""
    t = t_(0.08)
    return np.sin(2 * np.pi * 520 * t + 1.5 * np.sin(2 * np.pi * 830 * t)) * env(len(t), a=0.0005, d=0.025, r=0.01)


def hat():
    """Metallic tick from inharmonic FM, not noise."""
    t = t_(0.06)
    return np.sin(2 * np.pi * 6200 * t + 3 * np.sin(2 * np.pi * 6200 * 1.41 * t)) * env(len(t), a=0.0005, d=0.012, r=0.01)


def sleigh():
    """A shake of small bells: three detuned metallic ticks."""
    out = np.zeros(int(0.12 * SR))
    for k, f in enumerate((5200, 6100, 7300)):
        t = t_(0.1)
        s = np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * f * 1.37 * t)) * env(len(t), a=0.0005, d=0.03, r=0.01)
        place(out, s * 0.5, k * 0.012)
    return out


# Per bar, as (instrument, position in eighths, level).
PATTERNS = {
    'daf_slow': [(dum, 0, 0.5), (tak, 3, 0.25), (tak, 5, 0.18)],
    'maqsum':   [(dum, 0, 0.55), (tak, 1, 0.3), (tak, 3, 0.3), (dum, 4, 0.5), (tak, 6, 0.3)],
    'sleigh_soft': [(sleigh, 0, 0.12), (sleigh, 4, 0.07)],
    'pulse':    [(kick, i, 0.6) for i in (0, 2, 4, 6)] + [(hat, i, 0.12) for i in (1, 3, 5, 7)],
    'tick':     [(kick, 0, 0.5), (kick, 4, 0.35)] + [(hat, i / 2, 0.08 if i % 4 else 0.13) for i in range(16)],
    'light':    [(kick, 0, 0.45), (kick, 4, 0.4), (tak, 2, 0.18), (tak, 6, 0.18)] + [(hat, i, 0.07) for i in (1, 3, 5, 7)],
    'soft':     [(kick, 0, 0.3), (kick, 4, 0.25), (hat, 2, 0.05), (hat, 6, 0.05)],
}


def place(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    end = min(len(buf), i + len(sig))
    buf[i:end] += sig[:end - i]


# ---- output --------------------------------------------------------------

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


def _stereo(y, mix=0.1):
    st = np.stack([y, y]).astype(np.float32)
    return Pedalboard([Chorus(rate_hz=0.3, depth=0.15, mix=mix)])(st, SR)


def _fx(room):
    return Pedalboard([HighpassFilter(35), LowpassFilter(9000),
                       Reverb(room_size=room, wet_level=0.28, dry_level=0.8),
                       Compressor(threshold_db=-16, ratio=2.5), Limiter(-1.0)])


# ---- jingle and bed ------------------------------------------------------

def beats(style):
    """(motif note times, chord time) in seconds from the jingle's start,
    so an end card can move on the notes."""
    F = FLAVOURS[style]
    step, at0 = F['step'], 0.1
    if F.get('pickup'):
        at0 += len(F['pickup']) * step * 0.8 + step * 0.4
    if F.get('roll'):
        at0 += 0.12
    ts = _times(F, at0)
    return ts, ts[-1] + step


def jingle(style, path):
    """About 3.5 s: optional pick-up, the motif, a chord that fades."""
    F = FLAVOURS[style]
    dur = 3.6
    buf = np.zeros(int(dur * SR))
    step = F['step']
    at0 = 0.1
    for k, nt in enumerate(F.get('pickup', [])):
        place(buf, voice('pluck', hz(nt), 0.25) * 0.5, at0 + k * step * 0.8)
    if F.get('pickup'):
        at0 += len(F['pickup']) * step * 0.8 + step * 0.4
    if F.get('roll'):                     # a quick strum of the chord's top into the motif
        for k, nt in enumerate(F['chord'][2:5]):
            place(buf, pluck(hz(nt), 0.4, bright=0.5) * 0.18, at0 + k * 0.035)
        at0 += 0.12
    ts = _times(F, at0)
    for k, nt in enumerate(F['motif']):
        at = ts[k]
        place(buf, voice(F['lead'], hz(nt), 1.2) * 0.7, at)
        if F.get('harmony'):
            place(buf, voice(F['lead'], hz(F['harmony'][k]), 1.2) * 0.38, at)
        if F['lead'] in ('bell', 'bell+glock'):
            place(buf, pluck(hz(nt) / 2, 0.8, bright=0.3) * 0.4, at)
        if F.get('hits'):
            place(buf, kick() * 0.5, at)
    hit = ts[-1] + step
    if F.get('echo'):                     # the last two notes answer, softer, after the chord lands
        for k, nt in enumerate(F['motif'][2:]):
            place(buf, voice(F['lead'], hz(nt), 0.9) * 0.22, hit + 0.32 + k * step)
    place(buf, warm(F['chord'], dur - hit) * 0.5, hit)
    place(buf, sub(hz('D2'), 1.0) * 0.55, hit)
    top = F['chord'][-1]
    place(buf, (glock(hz(top) * 2, 1.4) if 'glock' in F['lead'] else
                musicbox(hz(top) * 2, 1.4) if F['lead'] == 'musicbox' else
                bell(hz(top) * 2, 1.6, ratio=3.5, index=1.2)) * 0.2, hit + 0.02)
    drums = F.get('drums')
    if drums in ('daf_slow', 'maqsum'):
        place(buf, dum() * 0.6, hit)
        place(buf, tak() * 0.3, hit - step / 2)
    elif drums == 'sleigh_soft':
        place(buf, sleigh() * 0.15, hit)
    elif drums in ('pulse', 'tick', 'light'):
        place(buf, kick() * 0.7, hit)
    if F.get('drone'):
        place(buf, hold([F['drone'], F['drone'][0] + '3'], dur, attack=0.3, release=0.8) * 0.3, 0)
    y = _stereo(_fx(0.55)(buf.astype(np.float32), SR))
    fade = int(0.4 * SR)
    y[:, -fade:] *= np.linspace(1, 0, fade)
    return _write(y, path, loud=-14)


def bed(style, path, bars=16):
    """Seamless loop: held chords, a quiet arpeggio, the flavour's rhythm,
    and the motif every 8 bars (bars 5, 13, ...)."""
    F = FLAVOURS[style]
    beat = 60 / F['bpm']
    bar = 4 * beat
    length = bars * bar
    buf = np.zeros(int((length + 3.0) * SR))
    for b in range(bars):
        chord = F['prog'][(b // 2) % len(F['prog'])]
        at = b * bar
        if b % 2 == 0:
            place(buf, hold(chord, 2 * bar + 0.5) * 0.3, at)
            place(buf, sub(hz(chord[0]) / 2, 1.5) * 0.25, at)
        if F.get('sixteenths'):
            # climbing like a counter: up the chord and an octave over it
            order = [0, 1, 2, 3, 0, 1, 2, 3, 1, 2, 3, 0, 1, 2, 3, 3]
            for i, o in enumerate(order):
                f = hz(chord[o]) * (4 if i >= 8 and o == 0 else 2)
                place(buf, voice(F['arp'], f, 0.3) * (0.13 if i % 4 == 0 else 0.08), at + i * beat / 4)
        else:
            for e8 in range(8):
                nt = chord[[0, 1, 2, 3, 2, 1, 2, 3][e8]]
                place(buf, voice(F['arp'], hz(nt) * 2, 0.5) * (0.16 if e8 % 2 == 0 else 0.10),
                      at + e8 * beat / 2)
        for inst, pos, lvl in PATTERNS.get(F.get('drums'), []):
            place(buf, inst() * lvl, at + pos * beat / 2)
    for b0 in range(4, bars, 8):
        for k, nt in enumerate(F['motif']):
            place(buf, voice(F['lead'], hz(nt), 1.0) * 0.22, b0 * bar + k * beat / 2)
    if F.get('drone'):
        place(buf, hold([F['drone'], F['drone'][0] + '3'], length + 0.5, attack=1.0, release=0.5) * 0.18, 0)
    fx = Pedalboard([LowpassFilter(7000), HighpassFilter(40),
                     Reverb(room_size=0.7, wet_level=0.3, dry_level=0.7),
                     Compressor(threshold_db=-18, ratio=2), Limiter(-1.0)])
    y = _stereo(fx(buf.astype(np.float32), SR), mix=0.08)
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


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for s in FLAVOURS:
        jingle(s, f'{out}/digi-jingle-{s}.mp3')
        bed(s, f'{out}/digi-bed-{s}.wav')
        print(s)
