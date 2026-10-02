"""Mohammad's voice preset: one raw recording in, a broadcast-ready read out.

Draft agreed in principle on 2 Oct 2026: a fixed setting he records to, so
every voiceover comes out the same. The target is the Emirati news host he
shared (notes/voice-reference-2026-10-02.md): formal Arabic, about 100
words a minute, half-second pauses between phrases, lean lows, smooth top,
even level, a faint room tone instead of dead silence.

    python voice.py <raw recording> <out stem> [--rebuild] [--keep-pauses]

writes <out stem>.wav (48 kHz) and .m4a and prints a report against the
host. The steps, in order:

1. Clean: AI denoise (resemble-enhance). --rebuild runs its enhancer
   instead (studio rebuild, stronger, can colour the voice).
2. Mouth: lip smacks, swallows and breaths between phrases down 30 dB with
   soft ramps; short clicks inside words softened (adeclick).
3. Pauses: head and tail trimmed to 0.25 s; a gap of 0.3 to 0.75 s becomes
   0.45 s (a phrase), a longer one 0.75 s (a sentence); shorter gaps stay.
   --keep-pauses skips this.
4. Tone: broadcast v3 (cut boom and boxiness, soften the top, de-ess,
   compress 5:1), then -16 LUFS, true peak -1.5 dB.
5. Room tone: a faint low noise 30 dB under the voice through the pauses.

Environment (a new container has none of this): a venv made with
--system-site-packages, numpy 2.2 inside it (the system numpy is mixed),
librosa and soundfile; resemble-enhance installed system-wide with its
weights in its model_repo; the deepspeed stub in voice_stubs/ on the path
(this file adds it).
"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'voice_stubs'))
SR = 48000
TONE = ('highpass=f=110,lowshelf=f=220:g=-8,equalizer=f=300:t=q:w=1.0:g=-4,'
        'equalizer=f=480:t=q:w=1.0:g=-1.5,equalizer=f=1000:t=q:w=1.4:g=-1.5,'
        'highshelf=f=2000:g=-6,equalizer=f=7000:t=q:w=1.0:g=-6,deesser=i=0.4:m=0.5:f=0.5,'
        'acompressor=threshold=-30dB:ratio=5:attack=4:release=90:makeup=3,'
        'loudnorm=I=-16:TP=-1.5:LRA=6')
PHRASE, SENTENCE, EDGE = 0.45, 0.75, 0.25
ROOM_DB = -30                                   # room tone under the voice
# The host, measured on 2 Oct 2026 (bands relative to 630 to 1250 Hz)
HOST = dict(bands=[-8.1, -4.3, 2.7, 0.0, -7.8, -14.3, -25.2, -35.5], crest=7.2,
            phrase_pause=0.45, wpm=102)
BANDS = [(80, 160), (160, 315), (315, 630), (630, 1250), (1250, 2500),
         (2500, 5000), (5000, 10000), (10000, 16000)]


def ff(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', *args], check=True)


def read48(path):
    tmp = tempfile.mktemp(suffix='.wav')
    ff('-i', path, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_f32le', tmp)
    x, _ = sf.read(tmp, dtype='float32'); os.remove(tmp)
    return x


def clean(x, rebuild=False):
    import torch
    import resemble_enhance.enhancer.inference as I
    from resemble_enhance.enhancer.download import REPO_DIR
    I.download = lambda: REPO_DIR / 'enhancer_stage2'
    w = torch.from_numpy(x)
    if rebuild:
        y, sr = I.enhance(w, SR, 'cpu', nfe=64, solver='midpoint', lambd=0.9, tau=0.5)
    else:
        y, sr = I.denoise(w, SR, 'cpu')
    y = y.cpu().numpy().astype('float32')
    if sr != SR:
        import librosa
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    return y


def speech_mask(x, thr_db=20, min_run=0.15, pre=0.08, post=0.14):
    """10 ms frames; speech is within 20 dB of the loud end, runs of 150 ms
    or more, padded so word edges and breath tails into words survive."""
    hop = SR // 100; n = len(x) // hop
    r = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))
    db = 20 * np.log10(r + 1e-9)
    on = np.convolve(db, np.ones(5) / 5, 'same') > np.percentile(db, 95) - thr_db
    m = np.zeros(n, bool); i = 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            if (j - i) * 0.01 >= min_run:
                m[max(0, i - int(pre * 100)):min(n, j + int(post * 100))] = True
            i = j
        else:
            i += 1
    return m, hop


def mouth(x, gap_db=-30, ramp=0.03):
    m, hop = speech_mask(x)
    g = np.where(m, 1.0, 10 ** (gap_db / 20)); k = int(ramp * 100) * 2 + 1
    g = np.convolve(g, np.ones(k) / k, 'same')
    gs = np.pad(np.repeat(g, hop), (0, len(x) - len(m) * hop), 'edge')
    tmp = tempfile.mktemp(suffix='.wav'); out = tmp + '.dc.wav'
    sf.write(tmp, x * gs, SR)
    ff('-i', tmp, '-af', 'adeclick=w=20:o=75:t=4', '-c:a', 'pcm_f32le', out)
    y, _ = sf.read(out, dtype='float32'); os.remove(tmp); os.remove(out)
    return y


def runs(m):
    out, i = [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]:
                j += 1
            out.append((i, j)); i = j
        else:
            i += 1
    return out


def pauses(x):
    """Rebuild the read with house pauses; returns audio and the old and new gaps."""
    m, hop = speech_mask(x)
    segs = runs(m)
    if not segs:
        return x, [], []
    fade = int(0.01 * SR); ramp = np.linspace(0, 1, fade, dtype='float32')
    parts = [np.zeros(int(EDGE * SR), 'float32')]; old, new = [], []
    for k, (a, b) in enumerate(segs):
        s = x[a * hop:b * hop].copy()
        s[:fade] *= ramp; s[-fade:] *= ramp[::-1]
        parts.append(s)
        if k + 1 < len(segs):
            g = (segs[k + 1][0] - b) / 100
            t = g if g < 0.3 else PHRASE if g <= SENTENCE else SENTENCE
            old.append(round(g, 2)); new.append(round(t, 2))
            parts.append(np.zeros(int(t * SR), 'float32'))
    parts.append(np.zeros(int(EDGE * SR), 'float32'))
    return np.concatenate(parts), old, new


def finish(x, out_wav):
    tmp = tempfile.mktemp(suffix='.wav'); toned = tmp + '.t.wav'
    sf.write(tmp, x, SR)
    ff('-i', tmp, '-af', TONE, '-ar', str(SR), '-c:a', 'pcm_f32le', toned)
    y, _ = sf.read(toned, dtype='float32'); os.remove(tmp); os.remove(toned)
    m, hop = speech_mask(y)
    level = np.sqrt(np.mean(y[:len(m) * hop].reshape(-1, hop)[m] ** 2))
    rng = np.random.default_rng(7)
    noise = np.cumsum(rng.standard_normal(len(y)).astype('float32'))   # brown: low and soft
    noise -= np.convolve(noise, np.ones(4801) / 4801, 'same')          # no drift
    noise *= level * 10 ** (ROOM_DB / 20) / (np.sqrt(np.mean(noise ** 2)) + 1e-12)
    y = y + noise
    peak = np.max(np.abs(y))
    if peak > 10 ** (-1.5 / 20):
        y *= 10 ** (-1.5 / 20) / peak
    sf.write(out_wav, y, SR, subtype='PCM_24')
    return y


def report(y, old, new):
    import librosa
    m, hop = speech_mask(y)
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=hop)) ** 2
    n = min(S.shape[1], len(m)); P = S[:, :n][:, m[:n]].mean(axis=1)
    f = librosa.fft_frequencies(sr=SR, n_fft=4096)
    b = [10 * np.log10(P[(f >= lo) & (f < hi)].sum() + 1e-12) for lo, hi in BANDS]
    bands = [round(float(v - b[3]), 1) for v in b]
    fr = y[:len(m) * hop].reshape(-1, hop)[m]
    crest = float(np.median(20 * np.log10(np.abs(fr).max(axis=1) / (np.sqrt((fr ** 2).mean(axis=1)) + 1e-9))))
    r = dict(bands=bands, host_bands=HOST['bands'], crest=round(crest, 1), host_crest=HOST['crest'],
             pauses_before=old, pauses_after=new, host_phrase_pause=HOST['phrase_pause'])
    print('tone vs host (dB per band, 80 Hz to 16 kHz):')
    for (lo, hi), a, h in zip(BANDS, bands, HOST['bands']):
        print(f'  {lo:>5}-{hi:<5} you {a:+6.1f}  host {h:+6.1f}')
    print(f'crest {crest:.1f} dB (host {HOST["crest"]}); pauses {old} -> {new}')
    return r


def run(src, stem, rebuild=False, keep_pauses=False):
    x = read48(src)
    x = clean(x, rebuild)
    x = mouth(x)
    old, new = [], []
    if not keep_pauses:
        x, old, new = pauses(x)
    y = finish(x, stem + '.wav')
    ff('-i', stem + '.wav', '-c:a', 'aac', '-b:a', '192k', stem + '.m4a')
    r = report(y, old, new)
    json.dump(r, open(stem + '.json', 'w'), indent=1)
    return stem + '.wav'


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    run(args[0], args[1], rebuild='--rebuild' in sys.argv, keep_pauses='--keep-pauses' in sys.argv)
