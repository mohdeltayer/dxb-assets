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
      "head_size": 64, "strip": [["الموعد", "22 أكتوبر"]], "credits": [[0, 9, "..."]],
      "track": ["cp-er-trailer.mp4", 12.0], "cut": true,                 # or "bed"; a stretch is checked for speech
      "speech_ok": [[3.0, 7.5, "director's statement, subtitled"]],      # only for a quote or interview Reel (Reel time)
      "sound": null, "country": null, "pace_ok": false, "lowres_ok": false,
      "ground_theme": "gold",                                        # for -gfx- graphics on the living ground
      "ground_footage": ["cp-er-trailer.mp4", 40.0],                 # card-led: the game's trailer behind the cards, moving
                                                                     # (a -gfx- shot may name its own: [png, [file, start], secs, null])
      "skin": "house",                                               # game skins pilot: house, scifi or fantasy (format ledger)
      "person": [["miyamoto.jpg", "شيغيرو مياموتو", "مبتكر Mario وZelda", 0.4, 3.8,      # people stories show the person
                  {"focus": [0.5, 0.3], "credit": null}]],                      # (23 Oct 2026); photo fetched as footage
      "gfx": [{"file": "x-gfx-fps.png", "kind": "fact", "label": "الأداء",   # cards drawn here with the Dubai font
               "value": "حتى 120", "note": "إطارًا في الثانية"}],             # (cardgfx.py), then laid on the ground
      "insert": [{"piece": "numbers", "shot": 3, "data": {...}}]     # HyperFrames over a -gfx- shot (24 Oct 2026):
                                                                     # templates/hfinsert.py; the card stays if it fails
    }

`style` (and `sound` for a Reel with no footage sound) are chosen by the main
session when it writes the job (reel.pick_style / sonic.rotate), so the
rotation ledgers stay in its commits and parallel runner jobs never fight
over them. A graphic shot (`-gfx-` in its name) is fetched like footage and
laid on the living ground (numgfx.slide), as in the batch render scripts.

    python3 templates/render_job.py run   <job.json> [--draft]   # fetch, render, strip, sheet
    python3 templates/render_job.py check <job.json>              # timeline, reading pace and speech in the track
    python3 templates/render_job.py focus <job.json>              # fill null focus from autofocus, before the sheet

Focus is resolved on the container before the shot sheet (`focus`), so the job
carries the crop that was judged; a null left in the job is autofocused on the
runner, which may pick another subject.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards as C, reel, numgfx as NG, trailer, decodecheck as DC, cardgfx as CG   # noqa: E402

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


def shots(job, draft=False, build=True):
    """The job's shots as reel() takes them: autofocus where focus is null, graphics on the living ground."""
    out, t = [], 0.0
    for i, (f, start, secs, fo) in enumerate(job['shots']):
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


def check(job):
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        for f, s, d, fo in shots(job, build=False):   # the runner stops on a letterboxed or small clip; catch it here first
            if s is not None and not f.startswith(NG.SUB + '/') and os.path.exists(C.U + f) and not job.get('lowres_ok'):
                rows = reel._bars(C.U + f, s, d)[1]
                if rows < reel.MIN_SRC_H:
                    raise ValueError(f'{f} at {s}: only {rows} rows of picture; find an unletterboxed or 4K copy, or set lowres_ok')
        st, end = reel.timeline(shots(job, build=False))
        reel.check_reading(place(job)(st, end), end)
    finally:
        reel.X = keep
    speech_check(job, end)
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
    import tempfile
    tmp = tempfile.mkdtemp(prefix='textcheck-')
    try:
        skin = job.get('skin') if job.get('skin') in reel.SK.KITS and job.get('label') != 'عاجل' else None
        reel.head_layer(job['headline'], job['label'], f'{tmp}/h.png', job['source'], job['date'], job.get('country'),
                        hs=job.get('head_size', 66), skin=skin)
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
    for f, start, secs, _ in job['shots']:
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


def run(job, draft=False):
    if job.get('kind') == 'famitsu':
        return famitsu(job, draft)
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
    gfx(job)
    source_check(job)
    fetched = time.time() - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tup = lambda v: v if v is None or isinstance(v, str) else tuple(tuple(x) if isinstance(x, list) else x for x in v)
    done = reel.reel(shots(job, draft), job['headline'], job['label'], place(job), job['source'], job['date'], out,
                     theme=job['theme'], style=job.get('style'), sound=job.get('sound'), country=job.get('country'),
                     head_size=job.get('head_size', 66), draft=draft, track=tup(job.get('track')), cut=job.get('cut', False),
                     credits=[tuple(c) for c in job['credits']] if job.get('credits') else None,
                     strip=strip_items(job) if job.get('strip') else None,
                     template=job.get('template'), pace_ok=job.get('pace_ok', False), lowres_ok=job.get('lowres_ok', False),
                     skin=job.get('skin'), person=[tuple(x) for x in job['person']] if job.get('person') else None)
    video = done[0] if isinstance(done, (list, tuple)) else done
    if job.get('insert') and not draft:
        inserts(job, video)
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
