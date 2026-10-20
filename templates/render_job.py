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
      "track": ["cp-er-trailer.mp4", 12.0], "cut": true,
      "sound": null, "country": null, "pace_ok": false, "lowres_ok": false,
      "ground_theme": "gold",                                        # for -gfx- graphics on the living ground
      "ground_footage": ["cp-er-trailer.mp4", 40.0],                 # card-led: the game's trailer behind the cards, moving
      "skin": "house"                                                # game skins pilot: house, scifi or fantasy (format ledger)
    }

`style` (and `sound` for a Reel with no footage sound) are chosen by the main
session when it writes the job (reel.pick_style / sonic.rotate), so the
rotation ledgers stay in its commits and parallel runner jobs never fight
over them. A graphic shot (`-gfx-` in its name) is fetched like footage and
laid on the living ground (numgfx.slide), as in the batch render scripts.

    python3 templates/render_job.py run   <job.json> [--draft]   # fetch, render, strip, sheet
    python3 templates/render_job.py check <job.json>              # timeline and reading pace only
    python3 templates/render_job.py focus <job.json>              # fill null focus from autofocus, before the sheet

Focus is resolved on the container before the shot sheet (`focus`), so the job
carries the crop that was judged; a null left in the job is autofocused on the
runner, which may pick another subject.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards as C, reel, numgfx as NG, trailer   # noqa: E402

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'


def fetch(item):
    """One footage or art item into uploads, unless it is already there."""
    dst = C.U + item['file']
    if os.path.exists(dst):
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if 'steam' in item:
        hls = {t['name']: t['hls'] for t in trailer.steam_trailers(item['steam'])}
        name = [n for n in hls if n.startswith(item['trailer'])]
        if not name:
            raise ValueError(f"{item['file']}: no Steam trailer starting {item['trailer']!r} on app {item['steam']}")
        stem = os.path.splitext(item['file'])[0]
        got = C.U + trailer.fetch(hls[name[0]], stem, item.get('start', 0), item.get('seconds', 120))
        if os.path.abspath(got) != os.path.abspath(dst):
            shutil.move(got, dst)
    elif 'url' in item:
        req = urllib.request.Request(item['url'], headers={'User-Agent': UA})
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
    return dst


def shots(job, draft=False, build=True):
    """The job's shots as reel() takes them: autofocus where focus is null, graphics on the living ground."""
    out, t = [], 0.0
    for i, (f, start, secs, fo) in enumerate(job['shots']):
        if f.endswith('.png') and '-gfx-' in f:
            clip = f"{NG.SUB}/{job['name']}-{i}.mp4"
            if build:
                os.makedirs(C.U + NG.SUB, exist_ok=True)
                gf = job.get('ground_footage')    # [file, start]: the game's own trailer behind the card (advisor, 20 Oct 2026)
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
    return end


def textcheck(job):
    """Headline, lines, strip and credits drawn alone, so a line that wraps onto a Latin word or
    leaves the safe zone stops in seconds (needs the Dubai font: the runner runs it first)."""
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
            reel.strip_layer(strip_items(job), f'{tmp}/s.png', job['theme'], skin=skin)
        for c in job.get('credits') or []:
            reel.credit_layer(c[2], f'{tmp}/c.png')
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


def run(job, draft=False):
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
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
                     skin=job.get('skin'))
    video = done[0] if isinstance(done, (list, tuple)) else done
    stem = os.path.splitext(out)[0]
    base = re.sub(r'-reel-v\d+$', '', stem)   # matches the workflow's ${stem%-reel-v*}, so v2 and later commit too
    if not draft:
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
