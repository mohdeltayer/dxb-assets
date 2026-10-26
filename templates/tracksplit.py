"""Trailer audio split (Mohammad, 24 Oct 2026, inbox 16:26Z: "Adopt Cocktail Fork").

A trailer's soundtrack is one mixed track. When a Reel reorders or holds shots, the track's
effects (sword clashes, explosions) land on shots they do not belong to. For a job whose `track`
is a stretch of trailer audio, the finished Reel's body sound is rebuilt after reel() has run:

  - MERL Cocktail Fork (MIT code and weights, pinned in render.yml, weights in the Actions
    cache) splits the track stretch and every footage shot's own stretch into speech, music and
    effects;
  - the trailer's music stem runs continuously under the whole body, faded as reel._track and
    outro.append fade the track today;
  - each footage shot gets back only its own effects, from the same source moment as its
    picture, SFX_DB under the music; stills, graphics and cards get none;
  - dialogue is not put back. Jobs where speech is the news (`speech_ok`, or `"speech_keep":
    true`) keep today's voiced or subtitled track untouched;
  - the body is matched to the old body's level, the end card's jingle is kept as it was, and the
    new sound is muxed onto the same picture (video stream copy).

Never holds a story. The Reel keeps today's audio, and the render log and render-times.json say so
(`audio_split`), when: Cocktail Fork is not installed (COCKTAIL_DIR unset, e.g. on the container),
the split fails or takes over TIMEOUT seconds, or the music stem is not clean enough:
  - LEAK_MAX: a second Cocktail Fork pass over the music stem still finds more than 5% of its
    energy as effects or speech (the test Reels measured 0.2 to 0.9%), or
  - MUSIC_MIN: the music stem carries under 40% of the track stretch's energy (an effects-led
    stretch; the test Reels measured 57 to 79%).
Stem cache (26 Oct 2026, "Add all five", safeguard 5): with SPLIT_CACHE set (render.yml, saved and restored by the
Actions cache like the weights, one entry per job file) every separation is stored as <key>.npy, the key being a hash
of the model commit, the sample rate, the input gain target and the exact decoded samples handed to the model. The
samples carry the source file's content, the start and the length in one, so a re-render of the same stretch from the
same footage skips the ~20 s of separation, and any change to the file, the stretch or the model is a miss that
separates exactly as before. The second pass over the music stem is cached the same way. Unset (the container), a
failed read or a failed write: no cache, today's behaviour. The record gains `cache: {hit, miss}`.
Skipped (today's audio, no split) for: our bed or no track, speech kept, a skin kit with its
sting (pilot), the breaking profile or the عاجل chip (speed first), and `"audio_split": false`.

    python3 tracksplit.py need <job.json>      # exit 0 when the job needs the split (render.yml installs it then)
    python3 tracksplit.py mix <spec.json>      # the child process render_job runs under a timeout
"""
import hashlib, json, os, subprocess, sys, tempfile, time

SR = 44100
CARD = 2.0                 # outro.CARD: the end card and its jingle stay as rendered
PAD = 1.0                  # context either side of every separated stretch
MERGE_GAP = 4.0            # stretches of one file closer than this are separated as one
SFX_DB = -3.0              # each shot's own effects, a little under the music (as in the 24 Oct test)
TIMEOUT = 300              # seconds for the whole split; past it the Reel keeps today's audio
LEAK_MAX = 5.0             # % of the music stem's energy a second pass still hears as effects or speech
MUSIC_MIN = 40.0           # % of the track stretch's energy that must be music
STILL = ('.jpg', '.jpeg', '.png', '.webp')
CACHE_VER = 'v1'           # bump when _Cocktail.__call__ changes what it returns for the same samples
CACHE_MAX_MB = 800         # the oldest stems go first past this, so one job's cache stays small
HERE = os.path.dirname(os.path.abspath(__file__))


def applies(job, installed=None):
    """(True, '') when the job's sound should be split, else (False, reason). `installed=False` skips the
    COCKTAIL_DIR check (render.yml asks before installing)."""
    tr = job.get('track')
    if not isinstance(tr, (list, tuple)) or len(tr) < 2 or not isinstance(tr[0], str):
        return False, 'no trailer track (our bed or each shot\'s own sound)'
    if job.get('audio_split') is False:
        return False, 'job sets audio_split false'
    if job.get('speech_ok') or job.get('speech_keep'):
        return False, 'speech is the news (speech_ok / speech_keep): voiced track kept'
    if job.get('profile') == 'breaking' or job.get('label') == 'عاجل':
        return False, 'breaking: speed first'
    if job.get('skin') not in (None, 'house'):
        return False, f"skin {job.get('skin')}: its sting is mixed into the body, kept as rendered"
    if installed is not False and not os.environ.get('COCKTAIL_DIR'):
        return False, 'Cocktail Fork not installed here (COCKTAIL_DIR unset)'
    return True, ''


def apply(job, video, starts, xfade, uploads):
    """Rebuild `video`'s body sound in place; returns the record for render-times.json."""
    ok, why = applies(job)
    if not ok:
        return {'applied': False, 'reason': why}
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix='tracksplit-')
    spec = {'video': video, 'out': f'{tmp}/split.mp4', 'result': f'{tmp}/result.json', 'xfade': xfade,
            'track': [uploads + job['track'][0], float(job['track'][1])],
            'shots': [[uploads + f, float(s), float(d), st] if _footage(f, s) else None
                      for (f, s, d, _), st in zip(job['shots'], starts)],
            'durations': [float(sh[2]) for sh in job['shots']], 'starts': list(starts)}
    json.dump(spec, open(f'{tmp}/spec.json', 'w'))
    rec = {'applied': False, 'tool': 'cocktail-fork'}
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), 'mix', f'{tmp}/spec.json'],
                           timeout=TIMEOUT, capture_output=True, text=True)
        if os.path.exists(spec['result']):
            rec.update(json.load(open(spec['result'])))
        if p.returncode != 0:
            rec['reason'] = 'split failed: ' + (p.stderr.strip().splitlines() or ['no output'])[-1][:300]
        elif rec.get('clean') and os.path.exists(spec['out']):
            os.replace(spec['out'], video)
            rec['applied'] = True
        elif 'reason' not in rec:
            rec['reason'] = 'no output'
    except subprocess.TimeoutExpired:
        rec['reason'] = f'split took over {TIMEOUT} s'
    except Exception as e:                       # never hold a story on the split
        rec['reason'] = f'split failed: {e}'[:300]
    finally:
        subprocess.run(['rm', '-rf', tmp])
    rec['secs'] = round(time.time() - t0, 1)
    return rec


def _footage(f, start):
    return start is not None and not (f.endswith('.png') and '-gfx-' in f) and os.path.splitext(f)[1].lower() not in STILL


# ---------------------------------------------------------------- the child process

_HAS_AUDIO = {}


def _has_audio(path):
    if path not in _HAS_AUDIO:
        _HAS_AUDIO[path] = bool(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries',
                                                'stream=index', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())
    return _HAS_AUDIO[path]


def _audio(path, start, secs):
    import numpy as np
    if not _has_audio(path):                     # a silent clip (SteamOS, 24 Oct): no effects of its own, not a failure
        return np.zeros((2, int(round(secs * SR))), dtype=np.float32)
    out = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0.0, start):.3f}', '-t', f'{secs:.3f}', '-i', path,
                          '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(out, dtype=np.float32).reshape(-1, 2).T.copy()
    a = np.pad(a, ((0, 0), (int(round(max(0.0, -start) * SR)), 0)))
    n = int(round(secs * SR))
    return np.pad(a, ((0, 0), (0, max(0, n - a.shape[1]))))[:, :n]


def _dur(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                capture_output=True, text=True, check=True).stdout)


def _fade(a, fin, fout):
    import numpy as np
    a = a.copy()
    n = a.shape[1]
    i, o = min(n, int(fin * SR)), min(n, int(fout * SR))
    if i:
        a[:, :i] *= np.linspace(0, 1, i)
    if o:
        a[:, n - o:] *= np.linspace(1, 0, o)
    return a


def _energy(a):
    import numpy as np
    return float(np.mean(a.astype(np.float64) ** 2))


def _db(a):
    import numpy as np
    return float(10 * np.log10(_energy(a) + 1e-12))


class _Cocktail:
    def __init__(self):
        import torch
        sys.path.insert(0, os.environ['COCKTAIL_DIR'])
        from mrx import MRX
        torch.set_num_threads(os.cpu_count() or 4)
        self.torch = torch
        self.model = MRX().eval()
        w = os.path.join(os.environ['COCKTAIL_DIR'], 'checkpoints', 'default_mrx_pre_trained_weights.pth')
        self.model.load_state_dict(torch.load(w, map_location='cpu', weights_only=True))
        # the model commit is the folder name render.yml installs into (.../cocktail-fork/<sha>)
        self.commit = os.path.basename(os.environ['COCKTAIL_DIR'].rstrip('/'))
        self.cache = os.environ.get('SPLIT_CACHE') or None
        self.hits = self.misses = 0

    def _path(self, mix):
        import numpy as np
        h = hashlib.blake2b(digest_size=20)
        h.update(f'{CACHE_VER}|{self.commit}|{SR}|-27.0|{mix.dtype}|{mix.shape}'.encode())
        h.update(np.ascontiguousarray(mix).tobytes())
        return os.path.join(self.cache, h.hexdigest() + '.npy')

    def _load(self, path, n):
        import numpy as np
        try:
            y = np.load(path)
            if y.ndim == 3 and y.shape[0] == 3 and y.shape[2] == n:
                os.utime(path)                   # a hit keeps the entry young for the prune below
                return y
        except Exception:
            pass
        return None

    def _store(self, path, y):
        import numpy as np
        try:
            os.makedirs(self.cache, exist_ok=True)
            files = sorted(((os.path.getmtime(f), os.path.getsize(f), f) for f in
                            (os.path.join(self.cache, n) for n in os.listdir(self.cache)) if f.endswith('.npy')))
            total = sum(sz for _, sz, _ in files) + y.nbytes
            for _, sz, f in files:               # the oldest first, until the cache is back under its cap
                if total <= CACHE_MAX_MB * 1024 * 1024:
                    break
                os.remove(f)
                total -= sz
            tmp = path + '.tmp'
            with open(tmp, 'wb') as f:
                np.save(f, y)
            os.replace(tmp, path)
            if os.environ.get('SPLIT_CACHE_NEW'):    # tells render.yml there is something new to save
                open(os.environ['SPLIT_CACHE_NEW'], 'w').close()
        except Exception:
            pass                                 # a cache that cannot be written is not a failure

    def __call__(self, mix):
        """(2, n) -> stems; the repo's separate_soundtrack with its -27 LUFS input gain, consistency 'pass'."""
        import numpy as np, pyloudnorm
        path = y = None
        if self.cache:
            try:
                path = self._path(mix)
                y = self._load(path, mix.shape[1])
            except Exception:
                path = y = None
        if y is not None:
            self.hits += 1
        else:
            self.misses += 1
            lufs = pyloudnorm.Meter(SR).integrated_loudness(mix.T.astype(np.float64))
            gain = 10 ** ((-27.0 - lufs) / 20) if np.isfinite(lufs) else 1.0
            with self.torch.no_grad():
                y = (self.model(self.torch.tensor(mix, dtype=self.torch.float32) * gain) / gain).numpy()
            if path:
                self._store(path, y)
        return {'music': y[0], 'speech': y[1], 'sfx': y[2]}     # dnr_dataset.SOURCE_NAMES order


def mix(spec):
    import numpy as np, soundfile as sf
    res = {'clean': False}
    t0 = time.time()
    sep = _Cocktail()
    video, (tf, ts), x = spec['video'], spec['track'], spec['xfade']
    body = _dur(video) - CARD
    # every stretch the mix needs, per source file, merged and padded
    need = {tf: [(ts, ts + body)]}
    for sh in spec['shots']:
        if sh:
            need.setdefault(sh[0], []).append((sh[1], sh[1] + sh[2]))
    cache, secs_in = {}, 0.0
    for f, iv in need.items():
        merged = []
        for a, b in sorted(iv):
            a, b = a - PAD, b + PAD
            if merged and a <= merged[-1][1] + MERGE_GAP:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        cache[f] = []
        for a, b in merged:
            cache[f].append(((a, b), sep(_audio(f, a, b - a))))
            secs_in += b - a

    def stems(f, a, secs):
        for (lo, hi), st in cache[f]:
            if lo <= a + 1e-6 and a + secs <= hi + 1e-6:
                i, n = int(round((a - lo) * SR)), int(round(secs * SR))
                return {k: np.pad(v[:, i:i + n], ((0, 0), (0, max(0, n - v[:, i:i + n].shape[1])))) for k, v in st.items()}
        raise KeyError(f'{f} {a}+{secs} not separated')

    trk = stems(tf, ts, body)
    res.update(separate_secs=round(time.time() - t0, 1), audio_secs=round(secs_in, 1))
    e = {k: _energy(v) for k, v in trk.items()}
    res['music_pct'] = round(100 * e['music'] / (sum(e.values()) + 1e-12), 1)
    again = sep(trk['music'])                                   # what a second pass still hears in the music
    ea = {k: _energy(v) for k, v in again.items()}
    res['leak_pct'] = round(100 * (ea['sfx'] + ea['speech']) / (sum(ea.values()) + 1e-12), 1)
    res['thresholds'] = {'leak_max_pct': LEAK_MAX, 'music_min_pct': MUSIC_MIN}
    if sep.cache:
        res['cache'] = {'hit': sep.hits, 'miss': sep.misses}
    if res['leak_pct'] > LEAK_MAX or res['music_pct'] < MUSIC_MIN:
        res['reason'] = (f"music stem not clean (leftover {res['leak_pct']}% > {LEAK_MAX}%)" if res['leak_pct'] > LEAK_MAX
                         else f"music only {res['music_pct']}% of the track (< {MUSIC_MIN}%)")
        json.dump(res, open(spec['result'], 'w'))
        return
    music = _fade(trk['music'], 0.3, 0.6)
    sfx = np.zeros_like(music)
    g, edge = 10 ** (SFX_DB / 20), (x if x > 0.1 else 0.03)
    shots = 0
    for sh, st, d in zip(spec['shots'], spec['starts'], spec['durations']):
        a0, n = int(round(st * SR)), int(round(min(d, body - st) * SR))
        if not sh or n <= 0:
            continue
        own = _fade(stems(sh[0], sh[1], n / SR)['sfx'], edge, edge) * g
        sfx[:, a0:a0 + own.shape[1]] += own[:, :sfx.shape[1] - a0]
        shots += 1
    new = music + _fade(sfx, 0.0, 0.6)
    old = _audio(video, 0, _dur(video))
    nb = int(round(body * SR))
    new *= 10 ** ((_db(old[:, :nb]) - _db(new)) / 20)            # the old body's level
    full = np.concatenate([new, old[:, nb:]], axis=1)            # the end card's jingle as rendered
    full /= max(1.0, float(np.abs(full).max()) / 0.98)
    wav = os.path.splitext(spec['out'])[0] + '.wav'
    sf.write(wav, full.T, SR, subtype='PCM_16')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2', '-shortest',
                    '-movflags', '+faststart', spec['out']], check=True)
    res.update(clean=True, effects_shots=shots, mix_secs=round(time.time() - t0 - res['separate_secs'], 1))
    json.dump(res, open(spec['result'], 'w'))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'mix':
        mix(json.load(open(sys.argv[2])))
    elif len(sys.argv) == 3 and sys.argv[1] == 'need':
        ok, why = applies(json.load(open(sys.argv[2])), installed=False)
        print('audio split: ' + ('needed' if ok else 'not needed, ' + why))
        sys.exit(0 if ok else 1)
    else:
        raise SystemExit('usage: tracksplit.py need <job.json> | mix <spec.json>')
