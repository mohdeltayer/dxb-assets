"""Render one Reel from a job file (render runner, advisor, 20 Oct 2026).

The main session writes jobs/render/<name>.json and commits it; the render
workflow (.github/workflows/render.yml) runs `python3 templates/render_job.py
run jobs/render/<name>.json` on a GitHub runner, one job per file, and commits
the mp4, strip and sheet to cards/YYYY-MM/. The same command works on the
container, which stays the fallback.

The job file is public (the repo and the Actions logs are): it carries only
what reel() needs and where to fetch the footage. Never a token, a Postiz id or
unreleased material.

    {
      "name": "cyberpunk-2077-edgerunners-2-update-october-22",
      "out": "cards/2026-10/cyberpunk-2077-edgerunners-2-update-october-22-reel-v1.mp4",
      "footage": [{"file": "cp-er-trailer.mp4", "steam": 1091500, "trailer": "046_CP_ER", "start": 0, "seconds": 120},
                  {"file": "art.jpg", "url": "https://..."}],
      "shots": [["cp-er-trailer.mp4", 12.0, 1.7, null], ...],     # file in uploads, start, seconds, focus (null: autofocus)
      "lines": [[2, 3, [["text", {"size": 54}]]], ...],            # reel.by_shot groups: first shot, last shot, sentences
      "headline": "...", "label": "رسمي", "source": "...", "date": "20 Oct 2026",
      "theme": "spectacle", "style": "lines", "template": "split",
      "strip": [["الموعد", "22 أكتوبر"]], "credits": [[0, 9, "..."]],
      "track": ["cp-er-trailer.mp4", 12.0], "cut": true,                 # or "bed"; a stretch is checked for speech
      "speech_ok": [[3.0, 7.5, "director's statement, subtitled"]],      # only for a quote or interview Reel (Reel time)
      "speech_keep": true,                                           # speech is the news without speech_ok: no audio split
      "audio_split": false,                                          # opt out of the trailer audio split (tracksplit.py)
      "profile": "breaking",                                         # reel.PROFILES (T0, 27 Oct 2026): no picture finish, no demucs,
                                                                     # veryfast crf 20; opt-in only: a «عاجل» label does NOT select it
      "kind": "breaking",                                            # the T0 breaking card (templates/breaking.py): one image, one
                                                                     # headline, one line, no footage shots; its job format is in that module
      "sound": null, "country": null, "pace_ok": false,
      "lowres_ok": "IGN, Nintendo store, publisher press site, Steam: none above 720p",   # never a bare true (below)
      "blocky_ok": [["arms-1.mp4", 28.0, "frames 28.0 to 30.6 looked at, phone size: blocks not visible"]],
      "ground_theme": "gold",                                        # for -gfx- graphics on the living ground
      "ground_footage": ["cp-er-trailer.mp4", 40.0],                 # card-led: the game's trailer behind the cards, moving
                                                                     # (a -gfx- shot may name its own: [png, [file, start], secs, null])
      "skin": "house",                                               # game skins pilot: house, scifi or fantasy (format ledger)
      "person": [["miyamoto.jpg", "شيغيرو مياموتو", "مبتكر Mario وZelda", 0.4, 3.8,      # people stories show the person
                  {"focus": [0.5, 0.3], "credit": null}]],                      # (23 Oct 2026); photo fetched as footage
      "gfx": [{"file": "x-gfx-fps.png", "kind": "fact", "label": "الأداء",   # cards drawn here with the Dubai font; a UAE price as ["aed", "25.20"]
               "value": "حتى 120", "note": "إطارًا في الثانية"}],             # (cardgfx.py), then laid on the ground
      "insert": [{"piece": "numbers", "shot": 3, "data": {...}}],    # HyperFrames over a -gfx- shot (24 Oct 2026):
                                                                     # templates/hfinsert.py; the card stays if it fails
      "frame": {"shot": 2, "offset": 0.25, "secs": 4.0,             # design pass (24 Oct 2026, templates/designpass.py):
                "data": {"platforms": [{"logo": "ps5",               # the WHERE AND HOW MUCH frame over that shot,
                                        "prices": [["الإمارات", ["aed", "239"]]]},   # replacing the strip, which
                                       {"logo": "steam", "prices": [["السعودية", "225 ريالًا"]]}],   # comes back if
                         "price_all": null, "date": "تصل في 29 أكتوبر",            # the frame fails; no story line,
                         "note": null, "arabic": false}},                          # credit or person in its span
      "kit": ["chip"],                                               # kit moments: chip (the press), photobox (the
                                                                     # first person window, t0 0, open on the cover)
      "kit_quiet": [[0.0, 3.4]],                                     # Reel seconds with voices: no blip there
      "blips": false                                                 # no UI blips on this Reel
    }

`style` (and `sound` for a Reel with no footage sound) are chosen by the main
session when it writes the job (reel.pick_style / sonic.rotate), so the
rotation ledgers stay in its commits and parallel runner jobs never fight
over them. A graphic shot (`-gfx-` in its name) is fetched like footage and
laid on the living ground (numgfx.slide), as in the batch render scripts.

    python3 templates/render_job.py run   <job.json> [--draft]   # fetch, render, strip, sheet
    python3 templates/render_job.py check <job.json>              # timeline, reading pace and speech in the track
    python3 templates/render_job.py focus <job.json>              # fill null focus from autofocus, before the sheet

Design pass (advisor memo of 24 Oct 2026, rolled out after Mohammad's "Roll out", 24 Oct 19:21Z; templates/
designpass.py has the full format): chips are 1.3 times their old size and split strip values a step larger on every
Reel (reel.CHIP_SIZE, STRIP_VALUE_SIZES, STRIP_H). `frame` and `kit` opt a job in to the HyperFrames pieces:
  - `frame`: {"shot", "offset" (s after the shot's start, default 0.25), "secs" (3 to 6, default 4), "data":
    {"platforms": [{"logo": slug in templates/assets/platforms, "prices": [[region or null, value]]}],
    "price_all", "date", "note", "arabic"}}; a value is "225 ريالًا", ["aed", "239"] (dirham sign) or
    {"unknown": "لم يُعلن السعر بعد"}. Its span must lie after the headline and clear of story lines, credits
    and person windows; the strip is left off while the frame shows its facts, and laid back if it fails.
  - `kit`: up to two of "chip" and "photobox" (photobox needs person[0] opening at 0); the frame counts as one
    moment, so a frame takes one kit moment at most. Extra or invalid moments are dropped with a note.
  - `kit_quiet` [[t0, t1]] and `speech_ok` windows keep the blips off voices; `speech_keep` without kit_quiet
    means no blips; `"blips": false` turns them off.
  The breaking profile (`"profile": "breaking"`) and the عاجل chip skip both. Each piece renders under 5 minutes or
  that part stays as reel.py drew it; the story is never held. Log: `render_job: design pass:`; render-times.json:
  `design_pass`. Without the keys, or without a HyperFrames CLI, the Reel renders as before.

Pre-render map (27 Oct 2026, templates/prerender.py; format in templates/cleanmap.py): `python3 templates/prerender.py <job>`
reads the job's footage before the job is committed and lists shots that sit on black frames, fades, frozen stretches,
a damaged-download smear, end cards or cut text, with the nearest clean start. `--write` (or `prerender.py embed`) puts
the result in the job as `clean_map`; with it, reel.quality_gate stops a shot that overlaps a bad interval, and
`"clean_nudge": true` moves such a shot to the verified start instead. `prerender_ok` [[file, t0, t1, reason]] waives an
interval someone has looked at. A job without `clean_map` renders exactly as before.

Focus is resolved on the container before the shot sheet (`focus`), so the job
carries the crop that was judged; a null left in the job is autofocused on the
runner, which may pick another subject.

Source quality (Mohammad, 24 Oct 2026, inbox 16:26Z, after the ARMS check; reel.quality_gate, run by `check` and by
reel() before the montage):
  - Bitrate floor: a source under 5 Mbps at 1080p, 3 Mbps at 720p (decodecheck.bitrate_floor scales it for other
    sizes and frame rates) is printed `lowbit` and flagged on the shot sheet. It does not stop the render.
  - Block check: a footage shot enlarged past 2x (reel.MAX_ZOOM) has its source stretch read for the 8x8 block-edge
    ratio; a peak above 1.5 (decodecheck.BLOCK_MAX) is `blocky` and stops the render unless `blocky_ok` names the
    shot as [file, start, reason], start being the shot's own start, after someone has looked at the frames.
  - `lowres_ok` names the copies searched: a string ("IGN, Nintendo store, publisher press site, Steam: none above
    720p"), a list of the sources, or {"searched": [...], "result": "..."}. A bare true stops the render.
`block_ok` stays the waiver for the smear check (decode damage), a different thing.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards as C, reel, numgfx as NG, trailer, decodecheck as DC, cardgfx as CG, breaking as BK   # noqa: E402

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'


def fetch(item):
    """One footage or art item into uploads, unless it is already there. Video is decoded in full once
    (advisor, 21 Oct 2026, after the Battlefield 1 Reel carried a damaged IGN download): any error line means one
    fresh download, and a second damaged copy stops the job. Never build shots from a file that reports errors."""
    dst = C.U + item['file']
    if os.path.exists(dst) and not item.get('_retry'):
        _decode_ok(item, dst)
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    _download(item, dst)
    _decode_ok(item, dst)
    return dst


def _decode_ok(item, dst):
    if os.path.splitext(dst)[1].lower() in reel.STILL or dst.endswith('.png'):
        return
    errs = DC.decode_errors(dst)
    if not errs:
        print(f"decode clean: {item['file']}", flush=True)
        return
    if item.get('_retry'):
        raise ValueError(f"{item['file']}: still damaged after a fresh download ({len(errs)} errors, first: {errs[0]}); "
                         'use another copy or drop the shots from the damaged stretch')
    print(f"decode errors in {item['file']} ({len(errs)}, first: {errs[0]}); downloading again", flush=True)
    os.remove(dst)
    for cached in _cache_for(dst):
        os.remove(cached)
    fetch(dict(item, _retry=True))


def _cache_for(src):
    """Picture-pass clips built from this file (reel.cached_shot names carry the file's stem)."""
    d = os.path.join(C.U, 'cache')
    stem = os.path.splitext(os.path.basename(src))[0]
    return [os.path.join(d, f) for f in os.listdir(d) if stem in f] if os.path.isdir(d) else []


def _download(item, dst):
    if 'steam' in item:
        # `trailer_id` (the number in the HLS path) picks one of several trailers sharing a name (Half-Life 2 has two)
        hls = [t['hls'] for t in trailer.steam_trailers(item['steam']) if t['name'].startswith(item['trailer'])
               and ('trailer_id' not in item or f"/{item['trailer_id']}/" in t['hls'])]
        if not hls:
            raise ValueError(f"{item['file']}: no Steam trailer starting {item['trailer']!r} on app {item['steam']}")
        stem = os.path.splitext(item['file'])[0]
        got = C.U + trailer.fetch(hls[0], stem, item.get('start', 0), item.get('seconds', 120))
        if os.path.abspath(got) != os.path.abspath(dst):
            shutil.move(got, dst)
    elif 'url' in item:
        hdr = {'User-Agent': UA}
        if item.get('referer'):                   # IGN's asset hosts refuse requests without their own referer
            hdr['Referer'] = item['referer']
        req = urllib.request.Request(item['url'], headers=hdr)
        with urllib.request.urlopen(req, timeout=120) as r, open(dst + '.part', 'wb') as f:
            shutil.copyfileobj(r, f)
        os.replace(dst + '.part', dst)
        if 'start' in item or 'seconds' in item:   # keep only the stretch the job names, so shot times match
            cut = dst + '.cut' + os.path.splitext(dst)[1]
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(item.get('start', 0)), '-i', dst]
                           + (['-t', str(item['seconds'])] if 'seconds' in item else []) + ['-c', 'copy', cut], check=True)
            os.replace(cut, dst)
    elif 'repo' in item:                          # a graphic or still committed to this repo (live/YYYY-MM-DD/...)
        src = os.path.join(ROOT, item['repo'])
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:                                     # outside the runner's sparse checkout: read it from the commit
            with open(dst, 'wb') as f:
                subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + item['repo']], stdout=f, check=True)
    else:
        raise ValueError(f"{item['file']}: footage needs steam, url or repo")


_NUDGED = set()


def clean_nudge(job, rows):
    """Pre-render map (templates/prerender.py): with `"clean_nudge": true` and a `clean_map` in the job, a footage shot
    whose span overlaps a bad interval starts at the start prerender verified instead (same length, same focus). Any
    other job gets `rows` back untouched."""
    cm = job.get('clean_map')
    if not (cm and job.get('clean_nudge')):
        return rows
    import cleanmap as CM
    out, moved = CM.nudge(cm, [tuple(r) for r in rows])
    for i, old, new in moved:
        if (job.get('name'), i, old) not in _NUDGED:
            _NUDGED.add((job.get('name'), i, old))
            print(f'render_job: clean map: shot {i} moved from {old} s to {new} s (clean_nudge)', flush=True)
    return [list(r) for r in out] if moved else rows


def shots(job, draft=False, build=True):
    """The job's shots as reel() takes them: autofocus where focus is null, graphics on the living ground."""
    out, t = [], 0.0
    rows = clean_nudge(job, job['shots'])
    for i, (f, start, secs, fo) in enumerate(rows):
        if f.endswith('.png') and '-gfx-' in f:
            clip = f"{NG.SUB}/{job['name']}-{i}.mp4"
            if build:
                os.makedirs(C.U + NG.SUB, exist_ok=True)
                gf = job.get('ground_footage')    # [file, start]: the game's own trailer behind the card (advisor, 20 Oct 2026)
                if isinstance(start, list):       # per card: ["x-gfx-a.png", [file, start], secs, null] (multi-game numbers)
                    gf = start
                NG.slide(C.U + f, secs, job.get('ground_theme', job['theme']), C.U + clip,
                         seed=sum(map(ord, job['name'])), t0=t, fast=draft,
                         footage=(C.U + gf[0], gf[1]) if gf else None)
            out.append((clip, 0.0, secs, 0.5))
        elif os.path.splitext(f)[1].lower() in reel.STILL:   # an official still: (art, null, secs, [from, to]) pans
            out.append((f, None, secs, tuple(fo) if isinstance(fo, list) else (0.5 if fo is None else fo)))
        else:
            if fo is None and build:
                fo = reel.autofocus(f, start, secs)
            if isinstance(fo, list):              # [[offset, focus], ...] from a job file
                fo = [tuple(k) for k in fo]
            out.append((f, start, secs, 0.5 if fo is None else fo))
        t += secs - reel.X
    return out


def focus(job, path):
    """Fill every null focus with reel.autofocus and write the job back, so the
    runner crops exactly what the shot sheet was judged on (20 Oct 2026: on the
    first runner test, autofocus there chose other subjects on three shots)."""
    if job.get('kind') == 'breaking':          # one image, framed by the job's own focus (breaking.py)
        return job
    for item in job.get('footage', []):
        fetch(item)
    for sh in job['shots']:
        if sh[3] is None and not (sh[0].endswith('.png') and '-gfx-' in sh[0]) and os.path.splitext(sh[0])[1].lower() not in reel.STILL:
            sh[3] = [list(k) for k in reel.autofocus(sh[0], sh[1], sh[2])]
    json.dump(job, open(path, 'w'), ensure_ascii=False, indent=1)
    return job


def strip_items(job):
    """[(label, value)] for reel's strip; a value written as ["aed", "185"] in JSON becomes the ('aed', '185') price tuple."""
    return [(l, tuple(v) if isinstance(v, list) else v) for l, v in job['strip']]


def place(job):
    return reel.by_shot([(a, b, [tuple(x) if isinstance(x, list) else x for x in texts]) for a, b, texts in job['lines']])


def profile_of(job):
    """reel()'s profile for a job (T0, 27 Oct 2026): "profile" exactly as written in the job, opt-in only. A job without
    the key, the «عاجل» label included, renders the standard way, exactly as before (Mohammad has not yet seen the
    breaking profile on a live Reel; the label default was removed in review the same day). "standard" or null is the
    standard render."""
    p = job.get('profile')
    if p in (None, 'standard'):
        return None
    if p not in reel.PROFILES:
        raise ValueError(f'profile {p!r}: one of {", ".join(reel.PROFILES)} or "standard"')
    return p


def check(job):
    if job.get('kind') == 'breaking':
        return BK.check(job)
    reel.CLEAN_MAP = job.get('clean_map')       # pre-render map (templates/prerender.py); None changes nothing
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        # the runner stops on a letterboxed or small clip, a blocky enlarged shot or a bare lowres_ok; catch it here
        # first (source quality, 24 Oct 2026); bitrate flags are printed. Shots not in uploads are skipped.
        reel.quality_gate(shots(job, build=False), job.get('lowres_ok'), job.get('blocky_ok'))
        st, end = reel.timeline(shots(job, build=False))
        reel.check_reading(place(job)(st, end), end)
    finally:
        reel.X = keep
    speech_check(job, end)
    if job.get('kit') or job.get('frame'):     # what the design pass will do, or drop, on the runner
        import designpass as DP
        keep = reel.X
        if job.get('cut'):
            reel.X = 0.04
        try:
            st, end2 = reel.timeline(shots(job, build=False))
            p = DP.plan(job, st, end2, place(job)(st, end2))
        finally:
            reel.X = keep
        print(f"design pass: moments {p['moments']}, frame {'at %.2f s for %.1f s' % (p['frame']['at'], p['frame']['secs']) if p['frame'] else 'none'}"
              + ''.join(f'; {n}' for n in p['notes']), flush=True)
    return end


def speech_check(job, end):
    """No speech under the lines (advisor, 21 Oct 2026): the track's stretch of trailer sound is transcribed over the
    Reel's length before the render, and any word, or a start or fade-out that is not in a pause, stops the job. A quote
    or interview Reel names its subtitled speech as speech_ok [[t0, t1, reason]] in Reel time. Skipped with a notice
    when the source is not in uploads or faster-whisper is missing (the runner)."""
    tr = job.get('track')
    if not isinstance(tr, list) or len(tr) < 2 or not isinstance(tr[0], str):
        return
    f, start = tr[0], float(tr[1])
    if len(tr) > 2 and tr[2] == 'music':          # voices stripped: read what will actually play
        f = os.path.splitext(f)[0] + '-music.wav'
    if not os.path.exists(C.U + f):
        print(f'speech check: {f} not in uploads, skipped', flush=True)
        return
    try:
        import speechcheck as SC
        heard = SC.stretch(f, start, end)
    except ImportError as e:
        print(f'speech check: skipped ({e})', flush=True)
        return
    ok = [w for w in job.get('speech_ok', []) if len(w) == 3]
    bad = [(a - start, b - start, w) for a, b, w in heard
           if not any(t0 <= a - start and b - start <= t1 for t0, t1, _ in ok)]
    edges = [what for what, fine in (('starts', heard.head_pause), ('fades out', heard.tail_pause)) if not fine]
    if bad or edges:
        raise ValueError(f'{f} from {start} s: ' + '; '.join(
            ([f'speech under the lines at ' + ', '.join(f'{a:.2f} to {b:.2f} s "{w}"' for a, b, w in bad[:12])
              + (f' and {len(bad) - 12} more' if len(bad) > 12 else '') + ' (Reel time)'] if bad else [])
            + [f'the track {e} on a word' for e in edges])
            + '; choose a music-only stretch (speechcheck.py --stretch), another trailer, or track "bed"; '
              'for a quote Reel pass speech_ok=[[t0, t1, reason]]')
    print(f'speech check: {f} from {start} s for {end:.1f} s, speech: ' + ('inside speech_ok only' if heard else 'none'), flush=True)


def textcheck(job):
    """Headline, lines, strip and credits drawn alone, so a line that wraps onto a Latin word or
    leaves the safe zone stops in seconds (needs the Dubai font: the runner runs it first)."""
    if job.get('kind') == 'famitsu':           # sales_full draws its own rows; nothing to pre-check here
        return
    if job.get('kind') == 'breaking':
        return BK.textcheck(job)
    import tempfile
    tmp = tempfile.mkdtemp(prefix='textcheck-')
    try:
        skin = job.get('skin') if job.get('skin') in reel.SK.KITS and job.get('label') != 'عاجل' else None
        reel.head_layer(job['headline'], job['label'], f'{tmp}/h.png', job['source'], job['date'], job.get('country'),
                        hs=job.get('head_size', reel.HEAD_SIZE), skin=skin)
        for a, b, texts in job['lines']:
            for x in texts:
                text, kw = (x, {}) if isinstance(x, str) else (x[0], x[1] if len(x) > 1 else {})
                if job.get('strip') and 'lift' not in kw:
                    kw = dict(kw, lift=reel.STRIP_LIFT) if hasattr(reel, 'STRIP_LIFT') else kw
                reel.line_layer(text, f'{tmp}/l.png', skin=skin, **kw)
        if job.get('strip'):
            # the same one-fact-one-place check reel() runs, so a repeat fails here in seconds
            reel.strip_check(strip_items(job), [(x if isinstance(x, str) else x[0], 0, 0, {} if isinstance(x, str) else (x[1] if len(x) > 1 else {}))
                                                for _, _, texts in job['lines'] for x in texts])
            reel.strip_layer(strip_items(job), f'{tmp}/s.png', job['theme'], skin=skin)
        for c in job.get('credits') or []:
            reel.credit_layer(c[2], f'{tmp}/c.png')
        for x in job.get('person') or []:          # needs the photo in uploads: fetched like footage before this runs
            o = x[5] if len(x) > 5 else {}
            if os.path.exists(C.U + x[0]):
                reel.person_layer(x[0], x[1], x[2], f'{tmp}/p.png', job['theme'], focus=tuple(o.get('focus', (0.5, 0.33))),
                                  credit=o.get('credit'))
        gfx(job, tmp)
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


def gfx(job, where=None):
    """The job's cards (`gfx`), drawn with the Dubai font: into uploads before the render, or into
    `where` for the text check, so a card that does not fit stops in seconds."""
    for item in job.get('gfx', []):
        CG.build(item, os.path.join(where, item['file']) if where else C.U + item['file'], job.get('ground_theme', job['theme']))


def source_check(job):
    """Every footage shot's stretch read for a blocky smear before it is used (the damage in a download sits on its
    own scene cut). block_ok entries [file, t0, t1, reason] waive a stretch a person has looked at."""
    waive = [w for w in job.get('block_ok', []) if len(w) == 4]
    bad = []
    for f, start, secs, _ in clean_nudge(job, job['shots']):
        if start is None or os.path.splitext(f)[1].lower() in reel.STILL or f.endswith('.png'):
            continue
        lo = max(0.0, start - 1.0)                 # read with context, report only what the shot uses
        for a, b, peak in DC.smear_times(C.U + f, lo, secs + (start - lo) + 1.0):
            if b <= start or a >= start + secs:
                continue
            if not any(w[0] == f and w[1] <= a <= w[2] for w in waive):
                bad.append(f'{f} {a:.2f} to {b:.2f} s (peak {peak})')
    if bad:
        raise ValueError('blocky smear in the source: ' + '; '.join(bad) + '; re-fetch it, use another copy, '
                         'or after looking pass block_ok=[[file, t0, t1, reason]]')


def famitsu(job, draft=False):
    """Famitsu weekly sales Reel (sales_full.reel) on the runner, for when the container has no Dubai font (22 Oct
    2026). `rows` and `hardware` are what sales_full.reel takes, with `shot` [file, [from, to]] and `art` naming files
    in uploads that `footage` fetches (screenshots and box art by URL); `week_label`, `date`, optional `hook`,
    `lowres_ok` and `block_ok`. The sheet lays out every screenshot with its pan."""
    import sales_full as SF
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
    rows = []
    for r in job['rows']:
        r = dict(r, shot=(C.U + r['shot'][0], tuple(r['shot'][1])))
        if r.get('art'):
            r['art'] = C.U + r['art']
        rows.append(r)
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    extra = {'hook': job['hook']} if job.get('hook') else {}
    video = SF.reel(rows, job['week_label'], job['date'], out, hardware=job.get('hardware', ()), draft=draft,
                    lowres_ok=job.get('lowres_ok', False), **extra)[0]
    base = re.sub(r'-reel-v\d+$', '', os.path.splitext(out)[0])
    if not draft:
        DC.check(video, [w for w in job.get('block_ok', []) if len(w) == 3])
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        reel.shotsheet([(r['shot'][0], None, 2.0, tuple(r['shot'][1])) for r in job['rows']], base + '-sheet.jpg')
    print(f"render_job: {job['name']} (famitsu) done in {time.time() - t0:.0f} s: {video}", flush=True)
    return video


def inserts(job, video):
    """HyperFrames inserts (advisor, 24 Oct 2026): laid over the finished Reel at their graphic shots; a failure or
    a render past hfinsert.TIMEOUT keeps the current card and is noted here and in render-times.json."""
    import hfinsert as HI
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, _ = reel.timeline(shots(job, build=False))
        recs = HI.apply(job, video, starts)
    finally:
        reel.X = keep
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):   # entries are named after the output file
                e['hf_insert'] = recs
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with the insert: {e}', flush=True)
    for r in recs:
        print(f"render_job: hf insert on shot {r['shot']}: {'ok' if r.get('ok') else 'FAILED, current card kept'} "
              f"({r['render_secs']} s){'' if r.get('ok') else ': ' + r['error']}", flush=True)
    return recs


def audio_split(job, video):
    """Trailer audio split (Mohammad, 24 Oct 2026, inbox 16:26Z): a job on a trailer track gets the trailer's music
    under the whole Reel and each shot's own effects (templates/tracksplit.py). Anything that fails, runs long or
    measures unclean keeps today's audio; the outcome is printed and kept in render-times.json as `audio_split`."""
    import tracksplit as TS
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, _ = reel.timeline(shots(job, build=False))
        xf = reel.X
    finally:
        reel.X = keep
    rec = TS.apply(job, video, starts, xf, C.U)
    print('render_job: audio split: ' + ('applied' if rec.get('applied') else 'not applied, audio as rendered') +
          ''.join(f'; {k} {rec[k]}' for k in ('reason', 'music_pct', 'leak_pct', 'cache', 'separate_secs', 'secs') if k in rec), flush=True)
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):
                e['audio_split'] = rec
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with the audio split: {e}', flush=True)
    return rec


def _times_note(job, key, value):
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):   # entries are named after the output file
                e[key] = value
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with {key}: {e}', flush=True)


def design_plan(job):
    """(plan, apart folder) for the design pass, or (None, None) when the job does not ask for it, is breaking, or
    HyperFrames is not installed (then the Reel renders exactly as before; the reason is printed)."""
    import designpass as DP
    if not (job.get('kit') or job.get('frame')):
        return None, None
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, end = reel.timeline(shots(job, build=False))
        lines = place(job)(starts, end)
    finally:
        reel.X = keep
    p = DP.plan(job, starts, end, lines)
    if not DP.hf_cli() and (p['moments'] or p['frame']):
        p['notes'].append('HyperFrames CLI not installed: rendered as before')
        p['moments'], p['frame'] = [], None
    for n in p['notes']:
        print(f'render_job: design pass: {n}', flush=True)
    if not (p['moments'] or p['frame']):
        return p, None
    import tempfile
    return p, tempfile.mkdtemp(prefix='dpass-apart-')


def design_pass(job, video, p, folder):
    """The design pass's pieces over the finished Reel (designpass.apply); parts that fail stay as reel.py drew them."""
    import designpass as DP
    try:
        rec = DP.apply(job, video, p, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    for r in rec['pieces']:
        print(f"render_job: design pass {r['piece']}: {'ok' if r.get('ok') else 'FAILED, kept as reel.py drew it'} "
              f"({r['render_secs']} s){'' if r.get('ok') else ': ' + r['error']}", flush=True)
    print(f"render_job: design pass laid back from reel.py: {rec['laid_back'] or 'nothing'}", flush=True)
    return rec


def breaking(job, draft=False):
    """The T0 breaking card (templates/breaking.py): fetch the one image, build the card, then the same checks and
    strips as every Reel. There is no shot sheet (no footage shots): `<name>-sheet.jpg` is the source image with the
    9:16 window drawn on it, so the commit step finds the same files."""
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
    fetched = time.time() - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    video = BK.render(job, out, draft=draft)
    stem = os.path.splitext(out)[0]
    base = re.sub(r'-reel-v\d+$', '', stem)
    if not draft:
        DC.check(video, [])                    # decode errors and the blocky-smear flag on the Reel that ships
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        BK.sheet(job, base + '-sheet.jpg')
    print(f"render_job: {job['name']} done in {time.time() - t0:.0f} s (fetch {fetched:.0f} s): {video}", flush=True)
    return video


def run(job, draft=False):
    if job.get('kind') == 'famitsu':
        return famitsu(job, draft)
    if job.get('kind') == 'breaking':
        return breaking(job, draft)
    t0 = time.time()
    reel.CLEAN_MAP = job.get('clean_map')       # pre-render map (templates/prerender.py); None changes nothing
    for item in job.get('footage', []):
        fetch(item)
    gfx(job)
    source_check(job)
    fetched = time.time() - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    dp_plan, DP_folder = design_plan(job) if not draft else (None, None)
    DP_apart = None
    if DP_folder:
        import designpass as DP
        DP_apart = DP.apart_spec(dp_plan, DP_folder)
    tup = lambda v: v if v is None or isinstance(v, str) else tuple(tuple(x) if isinstance(x, list) else x for x in v)
    done = reel.reel(shots(job, draft), job['headline'], job['label'], place(job), job['source'], job['date'], out,
                     theme=job['theme'], style=job.get('style'), sound=job.get('sound'), country=job.get('country'),
                     head_size=job.get('head_size', reel.HEAD_SIZE), draft=draft, track=tup(job.get('track')), cut=job.get('cut', False),
                     credits=[tuple(c) for c in job['credits']] if job.get('credits') else None,
                     strip=strip_items(job) if job.get('strip') else None,
                     template=job.get('template'), pace_ok=job.get('pace_ok', False), lowres_ok=job.get('lowres_ok', False),
                     skin=job.get('skin'), person=[tuple(x) for x in job['person']] if job.get('person') else None,
                     blocky_ok=job.get('blocky_ok'), apart=DP_apart, profile=profile_of(job),
                     reveal=job.get('reveal'))   # word-by-word reveal on the key line (story-beat twist, 28 Oct 2026)
    video = done[0] if isinstance(done, (list, tuple)) else done
    dp = design_pass(job, video, dp_plan, DP_folder) if DP_folder else None
    if job.get('insert') and not draft:
        inserts(job, video)
    if not draft:
        audio_split(job, video)                 # before the decode checks, so they read the Reel that ships
    if dp:
        import designpass as DP
        DP.mix_blips(job, video, dp)            # after the audio split, which rebuilds the body sound
        dp.pop('blip_plan', None)
        _times_note(job, 'design_pass', dp)
        print('render_job: design pass: ' + json.dumps({k: dp[k] for k in ('secs', 'blips', 'notes') if k in dp},
                                                      ensure_ascii=False), flush=True)
    stem = os.path.splitext(out)[0]
    base = re.sub(r'-reel-v\d+$', '', stem)   # matches the workflow's ${stem%-reel-v*}, so v2 and later commit too
    if not draft:
        DC.check(video, [w for w in job.get('block_ok', []) if len(w) == 3])   # stops before anything is committed
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        reel.shotsheet([s for s in shots(job, build=False) if not s[0].startswith(NG.SUB + '/')], base + '-sheet.jpg')
    print(f"render_job: {job['name']} done in {time.time() - t0:.0f} s (fetch {fetched:.0f} s): {video}", flush=True)
    return video


if __name__ == '__main__':
    step, path = sys.argv[1], sys.argv[2]
    job = json.load(open(path))
    if step == 'check':
        print(job['name'], 'ok, clip %.1f s' % check(job))
    elif step == 'text':
        textcheck(job); print(job['name'], 'text ok')
    elif step == 'focus':
        focus(job, path); print(job['name'], 'focus written')
    elif step == 'run':
        run(job, draft='--draft' in sys.argv[3:])
    else:
        raise SystemExit(f'unknown step {step!r}: run, check or focus')
