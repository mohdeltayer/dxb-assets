"""Franchise sound library (Mohammad, 21 Nov 2026; audit of 21 Nov, item 2, step c of the sound ladder).

For each recurring series, one or two music stretches fans recognise, taken only from that publisher's own official
trailers for the series (Capcom's Mega Man trailers for Mega Man): never soundtrack rips, fan uploads, YouTube, or
another company's arrangement (Super Smash Bros.). The music is split out of the trailer with Cocktail Fork (the same
model as the trailer audio split), kept in the permanent library under live/sound/franchise/, and every stretch has a
rights-register entry: franchise, publisher, source trailer and URL, the seconds taken, the measured music share and
leftover. A Reel that lays one is labelled sound:franchise.

The sound ladder (render_job.audio_split): (a) the trailer's own audio, split, speech dropped; (b) that trailer's music
stem alone; (c) the franchise theme from this library; (d) our bed. Our bed comes first only for stories with no game.

    python3 templates/franchise.py match "<game title>"          the franchise key, or nothing
    python3 templates/franchise.py build <key> [<key> ...]       on a runner with COCKTAIL_DIR: fetch, split, store, register
    python3 templates/franchise.py list                          the register
New series: add a FRANCHISES row the second time it appears in the news, then build it.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
REGISTER = os.path.join(HERE, 'assets', 'franchise-sound.json')
LIB = 'live/sound/franchise'
STRETCH = 24.0            # seconds per stretch: a Reel body is 15 to 35 s; longer bodies take both stretches in turn
STEP = 3.0
SKIP_HEAD, SKIP_TAIL = 3.0, 10.0      # a trailer's first seconds and its end slate are not the theme
MUSIC_MIN = 60.0          # % of the stretch's energy that is music
LEAK_MAX = 5.0
READ_MAX = 180.0          # seconds of a trailer read

# key: (title pattern, publisher, official source for templates/footage.py, trailer name prefix or None)
FRANCHISES = {
    'mega-man':        (r'\bmega ?man\b|\brockman\b', 'Capcom', 'steam:4223290', '07_MMDO_PV01'),
    'zelda':           (r'\bzelda\b|ocarina of time|breath of the wild|tears of the kingdom', 'Nintendo',
                        'https://www.nintendo.com/us/store/products/the-legend-of-zelda-ocarina-of-time-switch-2/', None),
    'mario':           (r'\bmario\b', 'Nintendo',
                        'https://www.nintendo.com/us/store/products/super-mario-galaxy-plus-super-mario-galaxy-2-switch/', None),
    'pokemon':         (r'pok[eé]mon', 'The Pokémon Company',
                        'https://www.nintendo.com/us/store/products/pokemon-legends-z-a-switch-2/', None),
    'final-fantasy':   (r'final fantasy|\bff ?(?:vii|xvi|xiv|7|16|14)\b', 'Square Enix', 'steam:2909400', None),
    'persona':         (r'\bpersona\b', 'Atlus', 'steam:2649560', 'Persona 6'),
    'monster-hunter':  (r'monster hunter', 'Capcom', 'steam:2246340', None),
    'resident-evil':   (r'resident evil|biohazard', 'Capcom', 'steam:2050650', None),
    'sonic':           (r'\bsonic\b', 'Sega', 'steam:2486820', 'Launch Trailer'),
    'metal-gear':      (r'metal gear', 'Konami', 'steam:2417610', None),
    'gta':             (r'grand theft auto|\bgta\b', 'Rockstar Games', 'repo:live/2026-11-20/gta6-launch-1080.mp4', None),
    'xenoblade':       (r'xenoblade', 'Nintendo',
                        'https://www.nintendo.com/us/store/products/xenoblade-chronicles-3-switch/', None),
}


def match(game):
    """The franchise key for a game title, or None."""
    g = str(game or '').lower()
    for key, (pat, *_rest) in FRANCHISES.items():
        if re.search(pat, g):
            return key
    return None


def register():
    try:
        return json.load(open(REGISTER))
    except (OSError, ValueError):
        return {'about': 'Franchise sound library and rights register (Mohammad, 21 Nov 2026): music stems split from the '
                         "publisher's own official trailers only; one entry per stretch.", 'stretches': []}


def stretches(key):
    return [e for e in register().get('stretches', []) if e.get('franchise') == key and e.get('file')]


def pick(job):
    """(franchise key, [stretch entries]) for the job's game, or (None, [])."""
    key = match(job.get('game') or job.get('game_short'))
    if not key:
        return None, []
    return key, stretches(key)


# ---------------------------------------------------------------------------------------------------------- build
def _source(key):
    pat, pub, src, prefix = FRANCHISES[key]
    if src.startswith('repo:'):
        return {'file': f'franchise-{key}.mp4', 'repo': src[5:]}, src[5:], pub
    import footage as FT
    r = FT.resolve(src, name=f'franchise-{key}', do_check=False, max_n=8)
    cands = r.get('candidates', []) if isinstance(r, dict) else r
    jobs = [c for c in cands if isinstance(c, dict) and c.get('job')]
    if prefix:
        jobs = [c for c in jobs if str(c['job'].get('trailer') or c.get('name') or '').startswith(prefix)] or jobs
    if not jobs:
        raise ValueError(f'{key}: no official video on {src}')
    c = jobs[0]
    item = dict(c['job'])
    item['file'] = f'franchise-{key}.mp4'
    where = item.get('url') or f"steam:{item.get('steam')}:{item.get('trailer')}"
    return item, where, pub


UPLOADS = os.environ.get('DXB_UPLOADS', '/tmp/franchise-uploads')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'


def _fetch(item):
    """The trailer into UPLOADS: a Steam trailer (HLS), an official URL, or a file committed to this repo."""
    import shutil
    import urllib.request
    os.makedirs(UPLOADS, exist_ok=True)
    dst = os.path.join(UPLOADS, item['file'])
    if os.path.exists(dst):
        return dst
    if 'steam' in item:
        import trailer
        hls = [t['hls'] for t in trailer.steam_trailers(item['steam']) if t['name'].startswith(item.get('trailer') or '')]
        if not hls:
            raise ValueError(f"no Steam trailer {item.get('trailer')!r} on app {item['steam']}")
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', hls[0], '-t', str(READ_MAX + SKIP_HEAD),
                        '-c', 'copy', dst], check=True, timeout=900)
    elif 'url' in item:
        hdr = {'User-Agent': UA}
        if item.get('referer'):
            hdr['Referer'] = item['referer']
        with urllib.request.urlopen(urllib.request.Request(item['url'], headers=hdr), timeout=300) as r, \
                open(dst + '.part', 'wb') as f:
            shutil.copyfileobj(r, f)
        os.replace(dst + '.part', dst)
    elif 'repo' in item:
        src = os.path.join(ROOT, item['repo'])
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            with open(dst, 'wb') as f:
                subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + item['repo']], stdout=f, check=True)
    return dst


def build(key):
    """Fetch the official trailer, split its music, keep the two best stretches, write the register."""
    import numpy as np
    import soundfile as sf
    import tracksplit as TS
    item, where, pub = _source(key)
    path = _fetch(item)
    dur = min(TS._dur(path), READ_MAX)
    t0, t1 = SKIP_HEAD, max(SKIP_HEAD + STRETCH, dur - SKIP_TAIL)
    mix = TS._audio(path, t0, t1 - t0)
    sep = TS._Cocktail()
    stems = sep(mix)
    music = stems['music']
    sr = TS.SR
    wins = []
    t = 0.0
    while t + STRETCH <= (t1 - t0) + 1e-6:
        a, b = int(t * sr), int((t + STRETCH) * sr)
        e_mix, e_mus = TS._energy(mix[:, a:b]), TS._energy(music[:, a:b])
        share = 100.0 * e_mus / max(e_mix, 1e-12)
        wins.append((share, e_mus, t))
        t += STEP
    if not wins:
        raise ValueError(f'{key}: the trailer is shorter than one stretch')
    med = float(np.median([w[1] for w in wins]))
    good = sorted([w for w in wins if w[0] >= MUSIC_MIN and w[1] >= med], key=lambda w: (-w[0], -w[1]))
    chosen = []
    for w in good:
        if all(abs(w[2] - c[2]) >= STRETCH for c in chosen):
            chosen.append(w)
        if len(chosen) == 2:
            break
    reg = register()
    reg['stretches'] = [e for e in reg.get('stretches', []) if e.get('franchise') != key]
    os.makedirs(os.path.join(ROOT, LIB), exist_ok=True)
    out = []
    for n, (share, _e, t) in enumerate(chosen, 1):
        a, b = int(t * sr), int((t + STRETCH) * sr)
        seg = TS._fade(music[:, a:b].copy(), 0.3, 0.8)
        leak = sep(seg)
        leak_pct = 100.0 * (TS._energy(leak['speech']) + TS._energy(leak['sfx'])) / max(TS._energy(seg), 1e-12)
        if leak_pct > LEAK_MAX:
            print(f'franchise: {key} stretch at {t0 + t:.1f} s: leftover {leak_pct:.1f}% over {LEAK_MAX}%, skipped')
            continue
        wav = os.path.join(UPLOADS, f'franchise-{key}-{n}.wav')
        sf.write(wav, seg.T, sr)
        rel = f'{LIB}/{key}-{n}.m4a'
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                        os.path.join(ROOT, rel)], check=True)
        e = {'franchise': key, 'n': n, 'file': rel, 'publisher': pub, 'source_trailer': where,
             'source_start': round(t0 + t, 2), 'secs': STRETCH, 'music_pct': round(share, 1),
             'leak_pct': round(leak_pct, 1), 'split': 'Cocktail Fork (MERL, MIT) music stem',
             'rights': f"music from {pub}'s own official trailer, used under the same terms as the trailer footage we "
                       'credit on screen; never a soundtrack rip, fan upload, YouTube copy or another company\'s arrangement',
             'recognisable': 'unverified: chosen by music share; a person listens before it is relied on',
             'added': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        reg['stretches'].append(e)
        out.append(e)
        print(f"franchise: {key} {n}: {where} at {e['source_start']} s, music {e['music_pct']}%, leftover "
              f"{e['leak_pct']}% -> {rel}", flush=True)
    if not out:
        print(f'franchise: {key}: no stretch reached music {MUSIC_MIN}% with leftover under {LEAK_MAX}% '
              f'(best {max(w[0] for w in wins):.1f}%)', flush=True)
    json.dump(reg, open(REGISTER, 'w'), indent=1, ensure_ascii=False)
    return out


# ------------------------------------------------------------------------------------------------------- lay it
def lay(job, video, why):
    """Step c: the franchise stretch under the body at the old body's level, the end card and its jingle as rendered.
    Returns the record, or None when the game has no franchise stretch (the ladder goes on to our bed)."""
    import numpy as np
    import tracksplit as TS
    key, ents = pick(job)
    if not ents:
        return None
    total = TS._dur(video)
    body = max(0.5, total - TS.CARD)
    old = TS._audio(video, 0, total)
    nb = int(round(body * TS.SR))
    parts = []
    start = sum(map(ord, os.path.basename(job.get('out') or job.get('name') or ''))) % len(ents)
    order = ents[start:] + ents[:start]
    for e in order * 4:                          # both stretches in turn, crossfaded, for a long body
        src = os.path.join(ROOT, e['file'])
        if not os.path.exists(src):                # outside a sparse checkout: from the commit, else from GitHub
            os.makedirs(os.path.dirname(src), exist_ok=True)
            with open(src + '.tmp', 'wb') as fh:
                r = subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + e['file']], stdout=fh)
            if r.returncode != 0:
                import urllib.request
                urllib.request.urlretrieve('https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/' + e['file'],
                                           src + '.tmp')
            os.replace(src + '.tmp', src)
        parts.append(TS._audio(src, 0, e['secs']))
        if sum(p.shape[1] for p in parts) >= nb:
            break
    xf = int(0.8 * TS.SR)
    music = parts[0]
    for p in parts[1:]:
        ramp = np.linspace(0, 1, xf)
        head = music[:, :-xf]
        mid = music[:, -xf:] * (1 - ramp) + p[:, :xf] * ramp
        music = np.concatenate([head, mid, p[:, xf:]], axis=1)
    music = np.pad(music[:, :nb], ((0, 0), (0, max(0, nb - music.shape[1]))))
    music = TS._fade(music, 0.3, 0.8)
    music *= 10 ** ((TS._db(old[:, :nb]) - TS._db(music)) / 20)
    full = np.concatenate([music, old[:, nb:]], axis=1)
    full /= max(1.0, float(np.abs(full).max()) / 0.98)
    import soundfile as sf
    wav = os.path.splitext(video)[0] + '-franchise.wav'
    tmp = os.path.splitext(video)[0] + '-franchise.mp4'
    sf.write(wav, full.T, TS.SR)
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', tmp], check=True)
    os.replace(tmp, video)
    os.remove(wav)
    used = [e['file'] for e in order[:len(parts)]]
    print(f'render_job: sound ladder c: franchise theme {key} ({", ".join(used)}): {why}', flush=True)
    return {'franchise': key, 'files': used, 'why': why}


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] == 'match':
        print(match(' '.join(argv[1:])) or '')
        return 0
    if argv[0] == 'list':
        for e in register().get('stretches', []):
            print(f"{e['franchise']:<15} {e['n']} {e['file']:<40} {e['publisher']:<20} {e['source_trailer']} "
                  f"@{e['source_start']} music {e['music_pct']}% leak {e['leak_pct']}%")
        return 0
    if argv[0] == 'build':
        bad = 0
        for key in argv[1:] or list(FRANCHISES):
            try:
                build(key)
            except Exception as e:               # noqa: BLE001  one franchise failing never stops the others
                bad += 1
                print(f'franchise: {key} FAILED: {e}', flush=True)
        return 1 if bad == len(argv[1:] or FRANCHISES) else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
