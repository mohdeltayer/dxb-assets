"""Trailer audio split test (advisor memo, 24 Oct 2026, approved by Mohammad). Pilot only.

A trailer's soundtrack is one mixed track. When a Reel reorders or holds shots, the track's
effects (sword clashes, explosions) and voices land on shots they do not belong to. This test
splits the trailer audio into speech, music and effects with two open-source separators and
rebuilds each Reel's sound from the trailer's music alone, with each shot's own effects put back
under that shot (so a clash is only heard on the clash). Dialogue is not put back: our story
lines are not subtitles of it.

Nothing here touches the live pipeline (reel.py, render_job.py, render.yml, job files). It reads
copies of three published Reels' job files (jobs/), fetches their footage the way render_job.py
does, and lays the new sound on the published Reel's picture (stream copy, no re-render).

    python split_test.py run <out_dir> jobs/<name>.json ...   # fetch, separate (both tools), mix, measure
    python split_test.py preview <out_dir> <tool> <names...>  # published then rebuilt, labelled, small

Tools (paths from the environment, set by .github/workflows/audio-split-test.yml):
  cocktail  MERL Cocktail Fork MRX (COCKTAIL_DIR, checkpoints/default_mrx_pre_trained_weights.pth)
  bandit    BandIt Plus in ZFTurbo Music-Source-Separation-Training (MSST_DIR, BANDIT_CKPT, BANDIT_CFG)
"""
import json, os, subprocess, sys, time

import numpy as np
import soundfile as sf

SR = 44100
CARD = 2.0                  # outro.CARD: the end card and its jingle, kept from the published Reel
PAD = 1.0                   # context either side of every separated stretch
MERGE_GAP = 4.0             # stretches of one file closer than this are separated as one
SFX_GAIN_DB = -3.0          # each shot's own effects sit a little under the music
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
UP = os.environ.get('DXB_UPLOADS', '/tmp/uploads').rstrip('/') + '/'
STILL = ('.jpg', '.jpeg', '.png', '.webp')


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


# ---------------------------------------------------------------- footage, as render_job.fetch does it

def steam_hls(appid, prefix, tid=None):
    import urllib.request
    url = f'https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en'
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
        data = next(iter(json.load(r).values())).get('data', {})
    hls = [m.get('hls_h264') for m in data.get('movies', []) if m['name'].strip().startswith(prefix)
           and (tid is None or f'/{tid}/' in (m.get('hls_h264') or ''))]
    if not hls or not hls[0]:
        raise ValueError(f'no Steam trailer starting {prefix!r} on app {appid}')
    return hls[0]


def fetch(item):
    dst = UP + item['file']
    if os.path.exists(dst):
        return dst
    os.makedirs(UP, exist_ok=True)
    if os.path.splitext(dst)[1].lower() in STILL:
        return None                                           # stills carry no sound
    if 'steam' in item:
        src = steam_hls(item['steam'], item['trailer'], item.get('trailer_id'))
        sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(item.get('start', 0)), '-i', src,
            '-t', str(item.get('seconds', 120)), '-c', 'copy', dst])
    elif 'url' in item:
        hdr = ['-H', f'User-Agent: {UA}'] + (['-H', f"Referer: {item['referer']}"] if item.get('referer') else [])
        sh(['curl', '-sSfL', '--retry', '3', '--max-time', '300'] + hdr + ['-o', dst + '.part', item['url']])
        os.replace(dst + '.part', dst)
        if 'start' in item or 'seconds' in item:
            cut = dst + '.cut.mp4'
            sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(item.get('start', 0)), '-i', dst]
               + (['-t', str(item['seconds'])] if 'seconds' in item else []) + ['-c', 'copy', cut])
            os.replace(cut, dst)
    else:
        return None                                           # repo items are stills or graphics here
    return dst


def audio(path, start, secs):
    """Float32 stereo at 44.1 kHz, `secs` long from `start` (input seek, as reel._track does)."""
    out = sh(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0.0, start):.3f}', '-t', f'{secs:.3f}', '-i', path,
              '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    a = np.frombuffer(out, dtype=np.float32).reshape(-1, 2).T.copy()
    lead = int(round(max(0.0, -start) * SR))                 # a stretch asked from before 0 s starts with silence
    a = np.pad(a, ((0, 0), (lead, 0)))
    n = int(round(secs * SR))
    return np.pad(a, ((0, 0), (0, max(0, n - a.shape[1]))))[:, :n]


def duration(path):
    return float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                    capture_output=True, text=True).stdout)


# ---------------------------------------------------------------- separators

class Cocktail:
    name = 'cocktail'

    def __init__(self):
        import torch
        d = os.environ['COCKTAIL_DIR']
        sys.path.insert(0, d)
        from mrx import MRX
        self.torch = torch
        self.model = MRX().eval()
        self.model.load_state_dict(torch.load(os.path.join(d, 'checkpoints', 'default_mrx_pre_trained_weights.pth'),
                                              map_location='cpu'))

    def __call__(self, mix):
        """mix (2, n) -> {'speech','music','sfx'} (2, n); the repo's separate_soundtrack with its -27 LUFS input gain."""
        import pyloudnorm
        torch = self.torch
        x = torch.tensor(mix, dtype=torch.float32)
        lufs = pyloudnorm.Meter(SR).integrated_loudness(mix.T.astype(np.float64))
        gain = 10 ** ((-27.0 - lufs) / 20) if np.isfinite(lufs) else 1.0
        with torch.no_grad():
            y = self.model(x * gain) / gain                    # [music, speech, sfx] per dnr_dataset.SOURCE_NAMES
        y = y.numpy()
        return {'music': y[0], 'speech': y[1], 'sfx': y[2]}


class Bandit:
    name = 'bandit'

    def __init__(self):
        import torch
        sys.path.insert(0, os.environ['MSST_DIR'])
        from utils.settings import get_model_from_config
        from utils.model_utils import demix
        self.torch, self.demix = torch, demix
        self.model, self.config = get_model_from_config('bandit', os.environ['BANDIT_CFG'])
        sd = torch.load(os.environ['BANDIT_CKPT'], map_location='cpu', weights_only=False)
        for k in ('state', 'state_dict', 'model_state_dict'):
            if isinstance(sd, dict) and k in sd:
                sd = sd[k]
        self.model.load_state_dict(sd)
        self.model.eval()
        self.config.training.use_amp = False                  # CPU: no autocast

    def __call__(self, mix):
        y = self.demix(self.config, self.model, mix.astype(np.float32), self.torch.device('cpu'), model_type='bandit')
        return {'music': y['music'], 'speech': y['speech'], 'sfx': y['effects']}


# ---------------------------------------------------------------- the Reel's timeline

def timeline(job):
    """reel.timeline: shot starts in Reel time and the body's length (crossfade X, 0.04 s on hard cuts)."""
    x = 0.04 if job.get('cut') else 0.4
    starts, t = [0.0], job['shots'][0][2]
    for s in job['shots'][1:]:
        starts.append(t - x)
        t = t - x + s[2]
    return starts, t, x


def is_footage(shot):
    f, start = shot[0], shot[1]
    return start is not None and not (f.endswith('.png') and '-gfx-' in f) and os.path.splitext(f)[1].lower() not in STILL


def spans(job, end):
    """Per source file, the merged stretches the test needs (the track and every footage shot), padded."""
    need = {}
    tr = job['track']
    need.setdefault(tr[0], []).append((float(tr[1]), float(tr[1]) + end))
    for s in job['shots']:
        if is_footage(s):
            need.setdefault(s[0], []).append((float(s[1]), float(s[1]) + float(s[2])))
    out = {}
    for f, iv in need.items():
        iv.sort()
        merged = []
        for a, b in iv:
            a, b = a - PAD, b + PAD
            if merged and a <= merged[-1][1] + MERGE_GAP:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        out[f] = merged
    return out


def stems_at(cache, f, a, secs):
    """Stems of file f from a for secs, cut out of the separated stretch that holds it."""
    for (lo, hi), st in cache[f]:
        if lo <= a + 1e-6 and a + secs <= hi + 1e-6:
            i = int(round((a - lo) * SR))
            n = int(round(secs * SR))
            return {k: np.pad(v[:, i:i + n], ((0, 0), (0, max(0, n - v[:, i:i + n].shape[1])))) for k, v in st.items()}
    raise KeyError(f'{f} {a}+{secs} not separated')


def rms_db(a):
    return float(10 * np.log10(np.mean(a.astype(np.float64) ** 2) + 1e-12))


def fade(a, fin, fout):
    a = a.copy()
    n = a.shape[1]
    i, o = min(n, int(fin * SR)), min(n, int(fout * SR))
    if i:
        a[:, :i] *= np.linspace(0, 1, i)
    if o:
        a[:, n - o:] *= np.linspace(1, 0, o)
    return a


def lag(ref, got, max_s=3.0):
    """Seconds by which `got` is late against `ref` (mono 8 kHz cross-correlation)."""
    def mono8(x):
        m = x.mean(0)
        return m[::5][: int(12 * SR / 5)]
    r, g = mono8(ref), mono8(got)
    n = len(r) + len(g)
    c = np.fft.irfft(np.fft.rfft(g, n) * np.conj(np.fft.rfft(r, n)), n)
    k = int(max_s * SR / 5)
    cand = np.concatenate([c[:k], c[-k:]])
    idx = int(np.argmax(cand))
    shift = idx if idx < k else idx - 2 * k
    peak = float(cand[idx] / (np.linalg.norm(r) * np.linalg.norm(g) + 1e-9))
    return shift * 5 / SR, peak


# ---------------------------------------------------------------- whisper, for words left in a music stem

_W = None


def words(a):
    global _W
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if _W is None:
        _W = WhisperModel('base', device='cpu', compute_type='int8')
    mono16 = a.mean(0)[::1]
    import scipy.signal as ss
    mono16 = ss.resample_poly(mono16, 160, 441).astype(np.float32)
    segs, _ = _W.transcribe(mono16, language='en', vad_filter=True, word_timestamps=True)
    got = []
    for s in segs:
        if s.no_speech_prob > 0.6:
            continue
        got += [w.word.strip() for w in (s.words or []) if w.probability > 0.5]
    return got


# ---------------------------------------------------------------- one Reel

def run_reel(job, tools, out_dir):
    name = job['name']
    pub = os.path.join(os.environ.get('REPO', '.'), job['out'])
    rec = {'name': name, 'published': job['out'], 'track': job['track'], 'shots': job['shots']}
    t0 = time.time()
    files = {}
    for item in job.get('footage', []):
        p = fetch(item)
        if p:
            files[item['file']] = p
    rec['fetch_secs'] = round(time.time() - t0, 1)
    starts, end, x = timeline(job)
    pdur = duration(pub)
    rec.update(body_secs=round(end, 3), published_secs=round(pdur, 3), crossfade=x)
    if abs(pdur - CARD - end) > 0.15:
        print(f'{name}: published {pdur:.2f} s against body {end:.2f} + card {CARD}; using the published body', flush=True)
    body = pdur - CARD
    published = audio(pub, 0, pdur)

    # the fetched track against the published Reel's sound: the same download offset applies to that file's shots
    tf, ts = job['track'][0], float(job['track'][1])
    nominal = audio(files[tf], ts, min(12.0, body))
    off, peak = lag(published[:, : nominal.shape[1]], nominal)
    rec['track_offset_secs'], rec['track_match'] = round(off, 3), round(peak, 3)
    shift = {tf: off if peak > 0.3 else 0.0}
    print(f'{name}: track offset {off:+.3f} s (match {peak:.2f})', flush=True)

    need = spans(job, body)
    rec['tools'] = {}
    for tool in tools:
        t1 = time.time()
        cache, secs_in = {}, 0.0
        for f, ivs in need.items():
            cache[f] = []
            for lo, hi in ivs:
                lo2, hi2 = lo + shift.get(f, 0.0), hi + shift.get(f, 0.0)
                mix = audio(files[f], lo2, hi2 - lo2)
                secs_in += hi2 - lo2
                cache[f].append(((lo2, hi2), tool(mix)))
        sep = time.time() - t1
        t2 = time.time()
        # music: one continuous stretch of the track's music stem, faded as reel._track and outro.append fade it
        trk = stems_at(cache, tf, ts + shift[tf], body)
        music = fade(trk['music'], 0.3, 0.6)
        # effects: each footage shot gets its own effects, from its own source time, under its own picture
        sfx = np.zeros_like(music)
        g = 10 ** (SFX_GAIN_DB / 20)
        shot_rows = []
        for i, (s, st) in enumerate(zip(job['shots'], starts)):
            row = {'shot': i, 'reel_from': round(st, 2), 'reel_to': round(min(body, st + s[2]), 2)}
            a0, n = int(round(st * SR)), int(round(min(s[2], body - st) * SR))
            old = trk['sfx'][:, a0:a0 + n]
            row['old_sfx_db'] = round(rms_db(old), 1) if old.size else None
            if is_footage(s) and n > 0:
                own = stems_at(cache, s[0], float(s[1]) + shift.get(s[0], 0.0), n / SR)['sfx']
                own = fade(own, x if x > 0.1 else 0.03, x if x > 0.1 else 0.03) * g
                sfx[:, a0:a0 + own.shape[1]] += own
                row['new_sfx_db'] = round(rms_db(own), 1)
            else:
                row['new_sfx_db'] = None
            shot_rows.append(row)
        sfx = fade(sfx, 0.0, 0.6)
        mixed = music + sfx
        # loudness: the new body at the published body's level (RMS), never clipping
        pb = published[:, : mixed.shape[1]]
        mixed *= 10 ** ((rms_db(pb) - rms_db(mixed)) / 20)
        tail = published[:, int(round(body * SR)):]
        full = np.concatenate([mixed, tail], axis=1)
        full /= max(1.0, float(np.abs(full).max()) / 0.98)
        wav = f'{out_dir}/{name}-{tool.name}.wav'
        sf.write(wav, full.T, SR, subtype='PCM_16')
        sf.write(f'{out_dir}/{name}-{tool.name}-music.wav', trk['music'].T, SR, subtype='PCM_16')
        mp4 = f'{out_dir}/{name}-{tool.name}.mp4'
        sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', pub, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4])
        mixsecs = time.time() - t2
        e = {k: float(np.mean(trk[k].astype(np.float64) ** 2)) for k in ('music', 'speech', 'sfx')}
        s_all = sum(e.values()) + 1e-12
        rec['tools'][tool.name] = {
            'separate_secs': round(sep, 1), 'audio_secs_separated': round(secs_in, 1), 'mix_secs': round(mixsecs, 1),
            'track_share_pct': {k: round(100 * v / s_all, 1) for k, v in e.items()},
            'shots': shot_rows, 'mp4': os.path.basename(mp4)}
        print(f'{name} {tool.name}: separated {secs_in:.1f} s of audio in {sep:.1f} s, mix {mixsecs:.1f} s', flush=True)
    rec['_music'] = {t.name: f'{out_dir}/{name}-{t.name}-music.wav' for t in tools}
    rec['_track_mix'] = audio(files[tf], ts + shift[tf], body)
    return rec


def crosscheck(rec, tools):
    """Each tool's music stem is separated again by the other tool: the share that tool hears as speech or
    effects is the leak left in the music. Whisper lists any words still audible in it."""
    by = {t.name: t for t in tools}
    out = {}
    for t in tools:
        m, _ = sf.read(rec['_music'][t.name], dtype='float32')
        m = m.T
        res = {}
        for judge in tools:
            st = judge(m)
            e = {k: float(np.mean(v.astype(np.float64) ** 2)) for k, v in st.items()}
            tot = sum(e.values()) + 1e-12
            res[f'leak_by_{judge.name}_pct'] = {'speech': round(100 * e['speech'] / tot, 1), 'sfx': round(100 * e['sfx'] / tot, 1)}
        w = words(m)
        res['words_in_music'] = None if w is None else len(w)
        res['words_sample'] = None if w is None else ' '.join(w[:12])
        out[t.name] = res
    w = words(rec['_track_mix'])
    rec['words_in_published_track'] = None if w is None else len(w)
    return out


def main_run(out_dir, paths):
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    os.makedirs(out_dir, exist_ok=True)
    t = time.time(); tools = []; loads = {}
    for cls in (Cocktail, Bandit):
        t1 = time.time()
        tools.append(cls())
        loads[cls.name] = round(time.time() - t1, 1)
        print(f'{cls.name}: model loaded in {loads[cls.name]} s', flush=True)
    summary = {'runner_cores': os.cpu_count(), 'model_load_secs': loads, 'reels': []}
    for p in paths:
        job = json.load(open(p))
        rec = run_reel(job, tools, out_dir)
        t1 = time.time()
        rec['crosscheck'] = crosscheck(rec, tools)
        rec['crosscheck_secs'] = round(time.time() - t1, 1)
        rec.pop('_music'); rec.pop('_track_mix')
        summary['reels'].append(rec)
        json.dump(summary, open(f'{out_dir}/results.json', 'w'), indent=1, ensure_ascii=False)
    summary['total_secs'] = round(time.time() - t, 1)
    json.dump(summary, open(f'{out_dir}/results.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False)[:6000])


# ---------------------------------------------------------------- the card's video

def preview(out_dir, tool, names):
    """Published then rebuilt for each Reel, 540x960, a plain label at the top; small enough for the inbox."""
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    parts = []
    for n in names:
        pub = os.path.join(os.environ.get('REPO', '.'), json.load(open(os.path.join(os.environ.get('JOBS_DIR', 'jobs'), n + '.json')))['out'])
        for src, lab in ((pub, 'PUBLISHED: mixed trailer track'), (f'{out_dir}/{n}-{tool}.mp4', 'NEW: trailer music + each shot\'s own effects')):
            o = f'{out_dir}/_p{len(parts)}.mp4'
            dt = (f",drawbox=x=0:y=0:w=iw:h=64:color=black@0.75:t=fill,drawtext=fontfile={font}:text='{lab}':"
                  f"fontcolor=white:fontsize=24:x=(w-text_w)/2:y=20") if os.path.exists(font) else ''
            sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-vf', f'scale=540:960,fps=30{dt},format=yuv420p',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '30', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2', o])
            parts.append(o)
    lst = f'{out_dir}/_p.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    out = f'{out_dir}/preview-{tool}.mp4'
    sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', out])
    for p in parts + [lst]:
        os.remove(p)
    print(out, round(os.path.getsize(out) / 1e6, 1), 'MB')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        main_run(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == 'preview':
        preview(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        raise SystemExit('run or preview')
