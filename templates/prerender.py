"""Pre-render footage checks (advisor card adv-20261027-build-until-thursday, item 1, approved by Mohammad, 27 Oct 2026).

Today the runner renders a job and only then fails on our own checks, and the retries are most of the gap between the
first job commit and the receipt. This reads the same footage the render will read, BEFORE the job is committed to
jobs/render/, and says which shots sit on a bad stretch and where the nearest clean start is.

    python3 templates/prerender.py <job.json> [--write] [--out report.json] [--no-ocr] [--no-check] [--ci]
    python3 templates/prerender.py embed <job.json> <map.json>     # put a clean_map from a CI log into a job file

Exit 0: no shot overlaps a bad interval and no job-level problem. Exit 1: production fixes the shot list first.

What it looks at (every footage shot's source stretch, start to start + secs, read 0.3 s either side as well):
  black      whole-file luma pass (ffmpeg signalstats): frames at video-range black (YAVG <= 22) and the fade ramp into
             or out of them; the v1 Don't Nod Reel had black frames at 18.8 s and from 46.37 s
  frozen     ffmpeg freezedetect, 0.6 s or longer (a held logo or a slate)
  smear      decodecheck.smear_times, the blocky smear of a damaged download
  endcard    OCR words of ratings, copyright and calls to action (rating, ESRB, PEGI, "all rights reserved",
             subscribe, ...), and a dark frame with writing in it near the end of the file
  cut-text   two or more words that the 9:16 window cuts at its edge (reel.edge_text; one word is soft)
  text       any other readable text inside the window (soft: a HUD is text too), but hard on the first frame of the
             first shot, which is the grid tile
  blocky     decodecheck.block_ratio on a shot enlarged past reel.MAX_ZOOM, unless blocky_ok waives it
and, as job problems rather than intervals: a letterboxed clip under 960 rows, a bare lowres_ok, a shot past the end
of its file, a source that will not decode twice, and the lines-too-fast / timeline / speech checks of
render_job.check (skipped with --no-check). A low bitrate is a warning, as in reel.quality_gate.

Hard findings go in the map; soft ones only in the report. A hard interval someone has looked at is waived in the job
with `prerender_ok`: [[file, t0, t1, reason]] (source seconds, a reason of at least 5 characters).

The map (templates/cleanmap.py has the format) is the job's `clean_map` key. reel.py and render_job.py read it when it
is there: reel.quality_gate stops a shot that overlaps a bad interval and names the suggested start; `"clean_nudge":
true` in the job moves such a shot to that start instead. Without the key nothing changes.

Cost on the 4-core server: one pass over each source for luma (about 10 s per minute of 1080p60), about 1.5 s per OCR
sample (two a second), the smear read and the block read as in the render. Tools: ffmpeg, tesseract, numpy, Pillow.
"""
import concurrent.futures as cf
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

os.environ.setdefault('OMP_THREAD_LIMIT', '1')        # tesseract threads: one per process, the pool provides the rest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cleanmap as CM                                   # noqa: E402
import decodecheck as DC                                # noqa: E402

MARGIN = 0.3          # seconds read either side of a shot's stretch
OCR_STEP = 0.5        # seconds between OCR samples
BLACK_Y = 22          # mean luma at or under this (video-range black is 16) is a black frame
FREEZE_MIN = 0.6      # a freeze this long or longer is bad
NEAR = 6.0            # seconds around each shot kept in the map from the whole-file luma pass
GRID_SECS = 0.6       # text this soon after the first shot's start is on the grid tile
ENDCARD = re.compile(r'^(rating|rated|ratings|esrb|pegi|usk|cero|classification|copyright|copyrights|rights|reserved|'
                     r'subscribe|trademark|trademarks|licensed|wishlist|presents|presented|www|http|https|follow)$', re.I)


def _dur(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


# ---------------------------------------------------------------- whole-file luma pass: black, fades, frozen

def luma_scan(path):
    """(black intervals, frozen intervals, duration): one pass over the file at 320 px. Black is a frame at video-range
    black; a fade ramp into or out of it is added (a steady rise or fall, never a cut: a jump of 25 or more levels in
    one frame ends it)."""
    import numpy as np
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', path, '-an', '-vf',
                        'scale=320:-2,freezedetect=n=0.003:d=0.4,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-',
                        '-f', 'null', '-'], capture_output=True, text=True)
    ts, ys, pts = [], [], None
    for ln in r.stdout.splitlines():
        m = re.search(r'pts_time:([\d.]+)', ln)
        if m:
            pts = float(m.group(1))
        m = re.search(r'YAVG=([\d.]+)', ln)
        if m and pts is not None:
            ts.append(pts); ys.append(float(m.group(1)))
    dur = _dur(path)
    fps = DC.probe(path)[2]
    dt = 1.0 / fps if fps else 1 / 30
    y = np.array(ys)
    n = len(y)
    black = []
    i = 0
    while i < n:
        if y[i] <= BLACK_Y:
            j = i
            while j < n and y[j] <= BLACK_Y:
                j += 1
            a, b = i, j                                   # frames a..b-1 are black
            reason = 'black'
            while b < n - 1 and y[b] - y[b - 1] < 25 and y[min(b + 4, n - 1)] - y[b] >= 1.5:   # fade in: still rising
                b += 1; reason = 'black+fade'
            while a > 0 and y[a] - y[a - 1] < 25 and y[a - 1] - y[max(a - 5, 0)] >= 1.5 and y[a - 1] - y[a] >= 0:   # fade out
                a -= 1; reason = 'black+fade'
            black.append((round(ts[a], 2), round(min(dur, ts[b - 1] + dt), 2), reason))
            i = j
        else:
            i += 1
    black = CM.merge(black, gap=0.25)
    frozen, start = [], None
    for ln in r.stderr.splitlines():
        m = re.search(r'freeze_start: ([\d.]+)', ln)
        if m:
            start = float(m.group(1))
        m = re.search(r'freeze_end: ([\d.]+)', ln)
        if m and start is not None:
            frozen.append((start, float(m.group(1)), 'frozen')); start = None
    if start is not None:
        frozen.append((start, dur, 'frozen'))
    keep = []
    for a, b, rs in frozen:
        if b - a < FREEZE_MIN:
            continue
        under = sum(max(0.0, min(b, y2) - max(a, x)) for x, y2, _ in black)
        if under < 0.7 * (b - a):                          # a black stretch is frozen too; one reason is enough
            keep.append((round(a, 2), round(b, 2), rs))
    return black, keep, dur


# ---------------------------------------------------------------- one shot: OCR, smear, block ratio

def _times(s, d, dur):
    lo, hi = max(0.0, s - MARGIN), min(dur - 0.05, s + d + MARGIN)
    ts, t = [], lo
    while t < hi:
        ts.append(round(t, 2)); t += OCR_STEP
    ts.append(round(hi, 2))
    return ts


def ocr_shot(path, f, s, d, fo, dur, first=False, ocr=True):
    """(hard, soft) intervals [(a, b, reason)] from tesseract on the frames of one stretch, read at the 9:16 window
    the shot will use. `first` is the first shot of the Reel (its first frame is the grid tile)."""
    import reel
    from PIL import ImageStat
    if not ocr:
        return [], []
    try:
        bars = reel._bars(path, s, d)[0]
        srcw, srch = reel._src_size(path)
    except Exception as e:                                   # noqa: BLE001
        return [(s, s + d, f'unreadable: {e}')], []
    hard, soft = [], []
    tail = dur - min(10.0, 0.15 * dur)
    half = OCR_STEP / 2
    for t in _times(s, d, dur):
        try:
            full = reel._frame(path, t, 1280)
        except SystemExit:
            hard.append((t, t + half, 'no picture'))
            continue
        boxes = reel._word_boxes(full, 60)
        if boxes is None:
            return hard, soft                                # no tesseract: the caller says so
        k = full.width / srcw
        x0, _y0, x1, _y1 = reel._window(bars, srcw, srch, reel._fo_at(fo, min(max(t - s, 0.0), d), d))
        x0, x1 = x0 * k, x1 * k
        inside = [w for w, l, tp, r, bt in boxes if x0 <= l and r <= x1]
        cut = [w for w, l, tp, r, bt in boxes if l < x0 < r or l < x1 < r]
        ends = [w for w, *_ in boxes if ENDCARD.match(w)]
        a, b = round(t - half, 2), round(t + half, 2)
        if ends:
            hard.append((a, b, 'endcard "' + ' '.join(ends[:3]) + '"'))
        elif t >= tail and boxes and ImageStat.Stat(full.convert('L')).mean[0] < 40:
            hard.append((a, b, 'endcard: dark frame with writing near the end'))
        if len(set(cut)) >= 2:
            hard.append((a, b, 'cut-text "' + ' '.join(dict.fromkeys(cut))[:40] + '"'))
        elif cut:
            soft.append((a, b, 'cut-text "' + cut[0] + '"'))
        if inside:
            row = (a, b, 'text "' + ' '.join(dict.fromkeys(inside))[:40] + '"')
            (hard if first and t - s < GRID_SECS else soft).append(row)
    return hard, soft


def smear_shot(path, s, d):
    out = []
    lo = max(0.0, s - 1.0)
    for a, b, peak in DC.smear_times(path, lo, d + (s - lo) + 1.0):
        if b > s - MARGIN and a < s + d + MARGIN:
            out.append((round(a, 2), round(b, 2), f'smear (peak {peak})'))
    return out


def deep_shot(f, s, d, fo, dur, job, first=False, ocr=True):
    """Everything that needs the frames of one stretch: (hard, soft, quality). `quality` is reel.source_quality's row."""
    import reel
    import render_job as RJ
    path = RJ.C.U + f
    hard, soft = ocr_shot(path, f, s, d, fo, dur, first, ocr)
    hard += smear_shot(path, s, d)
    q = reel.source_quality([(f, s, d, fo)]).get(0) or {}
    if q.get('blocky') and not reel._waived(f, s, job.get('blocky_ok')):
        hard.append((s, s + d, f'blocky (block ratio peak {q["block"][1]}, enlarged {q["zoom"]}x)'))
    return hard, soft, q


# ---------------------------------------------------------------- the job

def _waiver(job):
    return [w for w in job.get('prerender_ok', []) if len(w) >= 4 and len(str(w[3]).strip()) >= 5]


def _apply_waivers(f, iv, waive):
    keep, waived = [], []
    for a, b, r in iv:
        w = next((w for w in waive if w[0] == f and w[1] < b and w[2] > a), None)
        (waived if w else keep).append((a, b, r))
    return keep, waived


def analyse(job, ocr=True, check=True, workers=None, verify=True):
    import reel
    import render_job as RJ
    job = {k: v for k, v in job.items() if k not in ('clean_map', 'clean_nudge')}   # the raw shot list, not a stale map's
    T = {}
    t0 = time.time()
    problems = []
    for item in job.get('footage', []):
        try:
            RJ.fetch(item)
        except Exception as e:                               # noqa: BLE001
            problems.append(f"fetch {item['file']}: {e}")
    T['fetch'] = round(time.time() - t0, 1)
    shots = RJ.shots(job, build=False)
    foot = [(i, f, s, d, fo) for i, (f, s, d, fo) in enumerate(shots) if s is not None and reel._footage(f)]
    files = sorted({f for _, f, *_ in foot})
    waive = _waiver(job)
    workers = workers or min(4, os.cpu_count() or 2)
    warnings = []
    if ocr and not shutil.which('tesseract'):
        ocr = False
        warnings.append('tesseract missing: text, end-card and cut-text checks skipped (apt-get install -y tesseract-ocr)')

    t0 = time.time()
    luma, meta, info = {}, {}, {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {f: ex.submit(luma_scan, RJ.C.U + f) for f in files}
        for f, fu in futs.items():
            try:
                luma[f] = fu.result()
            except Exception as e:                           # noqa: BLE001
                problems.append(f'{f}: the luma pass failed: {e}')
                luma[f] = ([], [], _dur(RJ.C.U + f))
    T['luma'] = round(time.time() - t0, 1)
    for f in files:
        w, h, fps, bps = DC.probe(RJ.C.U + f)
        meta[f] = {'size': f'{w}x{h}', 'fps': round(fps, 2), 'mbps': round(bps / 1e6, 1), 'dur': round(luma[f][2], 2),
                   'flags': [x for x in (DC.bitrate_flag(RJ.C.U + f),) if x]}

    t0 = time.time()
    deep = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {i: ex.submit(deep_shot, f, s, d, fo, luma[f][2], job, i == 0, ocr) for i, f, s, d, fo in foot}
        for i, fu in futs.items():
            try:
                deep[i] = fu.result()
            except Exception as e:                           # noqa: BLE001
                deep[i] = ([], [], {})
                problems.append(f'shot {i}: the frame pass failed: {type(e).__name__}: {e}')
    T['frames'] = round(time.time() - t0, 1)

    # one hard list per file: the luma pass plus what the frame passes found
    bad = {f: list(luma[f][0]) + list(luma[f][1]) for f in files}
    soft = {}
    scanned = {f: [] for f in files}
    for i, f, s, d, fo in foot:
        h, sf, q = deep[i]
        bad[f] += h
        soft.setdefault(i, []).extend(sf)
        scanned[f].append([round(max(0, s - MARGIN), 2), round(min(luma[f][2], s + d + MARGIN), 2)])
        if s + d > luma[f][2] + 0.05:
            bad[f].append((luma[f][2], s + d, 'past the end of the file'))
        try:                                                 # letterbox rows and the lowres reason, as quality_gate
            reason = reel.lowres_reason(job.get('lowres_ok'))
        except ValueError as e:
            reason = None
            if str(e) not in problems:
                problems.append(str(e))
        if q and q.get('rows', 9999) < reel.MIN_SRC_H and not reason:
            problems.append(f'shot {i} {f} at {s}: only {q["rows"]} rows of picture (bars cut), enlarged {q["zoom"]}x; '
                            'find a 4K or unletterboxed copy, or name the copies checked in lowres_ok')
    waived = {}
    for f in files:
        bad[f] = CM.merge(bad[f], gap=0.1)
        bad[f], waived[f] = _apply_waivers(f, bad[f], waive)

    report_shots, suggest = [], {}
    used = {f: [(s, s + d, f'used by shot {i}') for i, ff, s, d, _ in foot if ff == f] for f in files}   # a moved shot never lands on another's footage
    for i, f, s, d, fo in foot:
        exact = CM.overlaps(bad[f], s, s + d)
        near = [x for x in CM.overlaps(bad[f], s - MARGIN, s + d + MARGIN, tol=0.0) if x not in exact]
        row = {'i': i, 'file': f, 'start': s, 'secs': d, 'hard': [list(x) for x in exact], 'near': [list(x) for x in near],
               'soft': [list(x) for x in soft.get(i, [])], 'suggest': None, 'note': None, 'q': deep[i][2]}
        if exact:
            t0 = time.time()
            others = [u for u in used[f] if u[2] != f'used by shot {i}']
            for c in CM.candidates(CM.merge(bad[f] + others), luma[f][2], s, d):
                if not verify:
                    row['suggest'] = c; break
                h2, s2, q2 = deep_shot(f, c, d, fo, luma[f][2], job, False, ocr)
                h2, _ = _apply_waivers(f, h2, waive)
                if not CM.overlaps(h2, c - MARGIN, c + d + MARGIN, tol=0.0):
                    row['suggest'] = c
                    scanned[f].append([round(max(0, c - MARGIN), 2), round(min(luma[f][2], c + d + MARGIN), 2)])
                    break
                bad[f] = CM.merge(bad[f] + h2, gap=0.1)
            T['suggest'] = round(T.get('suggest', 0) + time.time() - t0, 1)
            if row['suggest'] is None:
                near_w = CM.longest_near(CM.merge(bad[f] + others), luma[f][2], s)
                row['note'] = ('no clean window of %.2f s in the file; nearest clean: ' % d
                               + (', '.join(f'{a:.2f} to {b:.2f} s ({n:.2f} s)' for a, b, n in near_w) or 'none')
                               + '; shorten the shot or use another trailer')
            else:
                suggest[f'{f}@{s}'] = row['suggest']
                used[f].append((row['suggest'], row['suggest'] + d, f'used by shot {i}'))
        report_shots.append(row)

    if check:
        t0 = time.time()
        try:
            RJ.check(job)
        except Exception as e:                               # noqa: BLE001
            problems.append(f'render_job check: {e}')
        T['check'] = round(time.time() - t0, 1)

    cmap = {'v': 1, 'made': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'sources': {}, 'suggest': suggest}
    for f in files:
        spans = [(a, b) for _, ff, s, d, _ in foot if ff == f for a, b in [(s - NEAR, s + d + NEAR)]]
        keep = [[round(a, 2), round(b, 2), r] for a, b, r in bad[f]
                if any(a < y and b > x for x, y in spans) or any(a < y2 and b > x2 for x2, y2 in scanned[f])]
        sc = sorted(scanned[f])
        mg = []
        for a, b in sc:
            if mg and a <= mg[-1][1]:
                mg[-1][1] = max(mg[-1][1], b)
            else:
                mg.append([a, b])
        cmap['sources'][f] = {'dur': meta[f]['dur'], 'scanned': mg, 'bad': keep}
    ok = not problems and not any(r['hard'] for r in report_shots)
    return {'job': job.get('name'), 'ok': ok, 'secs': T, 'problems': problems, 'warnings': warnings, 'shots': report_shots, 'sources': meta,
            'waived': {f: [list(x) for x in v] for f, v in waived.items() if v}, 'map': cmap}


def summary(rep):
    out = [f"prerender {rep['job']}: " + ('CLEAN' if rep['ok'] else 'NOT CLEAN') +
           '   (' + ', '.join(f'{k} {v} s' for k, v in rep['secs'].items()) + ')']
    for f, m in rep['sources'].items():
        out.append(f"  source {f}: {m['size']} {m['fps']} fps {m['mbps']} Mbps, {m['dur']} s" + ''.join(f'; WARN {x}' for x in m['flags']))
    for r in rep['shots']:
        tag = 'FAIL' if r['hard'] else ('near' if r['near'] else 'ok')
        out.append(f"  shot {r['i']:>2} {r['file']} {r['start']} +{r['secs']} s  {tag}")
        for a, b, why in r['hard']:
            out.append(f'      {a:.2f} to {b:.2f} s  {why}')
        for a, b, why in r['near']:
            out.append(f'      within 0.3 s: {a:.2f} to {b:.2f} s  {why}')
        if r['hard']:
            out.append(f"      nearest clean start with the same length: {r['suggest']}" if r['suggest'] is not None else f"      {r['note']}")
        for a, b, why in r['soft'][:4]:
            out.append(f'      warn {a:.2f} to {b:.2f} s  {why}')
        if len(r['soft']) > 4:
            out.append(f"      warn ... and {len(r['soft']) - 4} more soft findings")
    for w in rep.get('warnings', []):
        out.append('  WARN ' + w)
    for p in rep['problems']:
        out.append('  PROBLEM ' + p.replace('\n', '\n          '))
    for f, v in rep.get('waived', {}).items():
        out.append(f'  waived on {f}: ' + ', '.join(f'{a:.2f} to {b:.2f} {r}' for a, b, r in v))
    return '\n'.join(out)


def embed(job_path, cmap):
    job = json.load(open(job_path))
    job['clean_map'] = cmap
    json.dump(job, open(job_path, 'w'), ensure_ascii=False, indent=1)


def main(argv):
    if len(argv) >= 4 and argv[1] == 'embed':
        embed(argv[2], json.load(open(argv[3]))); print('clean_map embedded in', argv[2]); return 0
    path = argv[1]
    job = json.load(open(path))
    if job.get('kind') == 'famitsu' or 'shots' not in job:
        print(f"prerender {job.get('name')}: not a footage job, nothing to read"); return 0
    opt = lambda k: k in argv[2:]                                     # noqa: E731
    rep = analyse(job, ocr=not opt('--no-ocr'), check=not opt('--no-check'), verify=not opt('--no-verify'))
    text = summary(rep)
    print(text)
    mapjson = json.dumps(rep['map'], ensure_ascii=False, separators=(',', ':'))
    if opt('--ci'):
        print('::prerender-map-begin::'); print(mapjson); print('::prerender-map-end::')
        sm = os.environ.get('GITHUB_STEP_SUMMARY')
        if sm:
            with open(sm, 'a') as fh:
                fh.write('### prerender ' + str(rep['job']) + '\n```\n' + text + '\n```\n<details><summary>clean_map (for prerender.py embed)</summary>\n\n```json\n'
                         + mapjson + '\n```\n</details>\n')
    if '--out' in argv:
        json.dump(rep, open(argv[argv.index('--out') + 1], 'w'), ensure_ascii=False, indent=1, default=str)
    if opt('--write'):
        embed(path, rep['map']); print('clean_map written into', path)
    return 0 if rep['ok'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
