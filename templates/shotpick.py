"""Server shot picker (adv-20261110-one-render-per-reel, item C, Mohammad 10 Nov 2026).

On 10 Nov the Warhammer Survivors shots crossed the trailer's burnt-in text cards (22.5 s, 43.3 s), found by eye after
picking. The session picked shots from frames it viewed; the server now reads the whole trailer once and writes the clean
stretches, in source order, each with its focus, so the session takes shots from the list instead of viewing frames.

    python3 templates/shotpick.py file <uploads file> [--out shots.json]
    python3 templates/shotpick.py job <job.json> [--out shots.json]     every footage file of the job (fetched first)

A stretch is clean when, inside its scene (the trailer's own cuts), it has: no black frame or fade, no frozen picture,
no smear, no end card, no text inside the 9:16 window at the scene's focus and no cut text at its edges (tesseract every
0.5 s), on a file that decodes clean. Stretches under MIN_SECS are dropped; each comes with `secs` (at most MAX_SECS,
from the stretch's start) and its `focus` (reel.autofocus: the largest person, vehicle or animal, or saliency).
Output, per file: {"file", "duration", "picture_start", "decode_clean", "shots": [{"start", "end", "secs", "focus",
"scene"}], "rejected": [{"start", "end", "why"}], "cuts": [...]}. Since 15 Nov (adv-20261115-one-render-server-checks,
item B) every time is on the server's own copy: nothing before the picture start (the video's start_time), stretches
inside one scene only, and a letterboxed scene rejected ("letterboxed, N of M rows"); t0make takes its shot times
from here, and templates/shotgate.py refuses a job whose shots break these rules before the render. The job takes a shot as [file, start, secs, focus]. The prerender workflow runs
it with mode `shots` and prints SHOTS_JSON lines; nothing is committed.
"""
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MIN_SECS = 1.6
MAX_SECS = 4.0
PAD = 0.15            # seconds kept clear either side of a bad interval
# The fast read (adv-20261117-server-speed-for-p2 A, 17 Nov 2026): RPG Maker's shots:auto read took about 13 minutes in
# the render step. The slow read seeked every OCR frame and every autofocus frame with its own ffmpeg (about 170 seeks
# and 400 frame reads, many read twice where scenes overlap) on a 95 s trailer. The fast read decodes the file once at
# READ_W wide and two frames a second, reads each frame with tesseract once (in parallel), hands the same frames to
# autofocus and runs the smear check in chunks of CHUNK seconds with the scene cuts. BUDGET caps one file's read;
# a frame not read by then rejects its stretch ("not read in time"), so the read never passes the cap and never
# offers an unread stretch. Results are cached per file, size and READ_VER. A label burnt into the whole trailer, which
# tesseract reads on some frames and misses on others (Forza, 17 Nov: "IN-ENGINE FOOTAGE"), is found across the file
# (LABEL_SHARE of its frames, in one place) and rejects every scene whose 9:16 window covers it.
READ_W = 1280        # the full read's OCR width: the small "IN-ENGINE FOOTAGE" label reads no worse
BUDGET = 55.0         # seconds per file: three trailers stay inside the card's 3 minutes
CHUNK = 15.0
READ_VER = 'r1'
LABEL_SHARE = 0.2     # a word read on this share of a file's frames, in one place, is a label on the whole trailer
LABEL_POS = 0.06      # "one place": its centre within this share of the frame across readings
LAST = {}             # file -> seconds the last read took (render_job puts it in qc.json)


def _focus_value(fo):
    if isinstance(fo, (int, float)):
        return round(float(fo), 3)
    for k in ('mean', 'focus', 'x'):
        v = getattr(fo, k, None)
        if isinstance(v, (int, float)):
            return round(float(v), 3)
    try:
        return round(float(fo), 3)
    except (TypeError, ValueError):
        return 0.5


def _subtract(a, b, bad):
    """[a, b] minus the bad intervals (each widened by PAD)."""
    pieces = [(a, b)]
    for x, y, _ in sorted(bad):
        x, y = x - PAD, y + PAD
        nxt = []
        for p, q in pieces:
            if y <= p or x >= q:
                nxt.append((p, q))
                continue
            if x > p:
                nxt.append((p, x))
            if y < q:
                nxt.append((y, q))
        pieces = nxt
    return pieces


def _cache_key(f):
    import cards as C
    path = C.U + f
    return os.path.join(C.U, 'cache', f'shotpick-{READ_VER}-{os.path.basename(f)}-{os.path.getsize(path)}.json')


def pick(f, ocr=True, workers=None, fast=True, budget=None, cache=True):
    """The clean stretches of one file. fast (the default) is the one-pass read; fast=False the old per-scene read."""
    t0 = time.time()
    key = None
    if cache:
        try:
            key = _cache_key(f)
        except (ImportError, OSError, AttributeError):
            key = None
        if key and os.path.exists(key):
            r = json.load(open(key, encoding='utf-8'))
            LAST[f] = 0.0
            r['read_secs'] = 0.0
            r['cached'] = True
            return r
    r = (_pick_fast(f, ocr, workers, BUDGET if budget is None else budget) if fast else _pick_slow(f, ocr, workers))
    r['read_secs'] = round(time.time() - t0, 1)
    r['read'] = 'fast' if fast else 'full'
    LAST[f] = r['read_secs']
    if key and not r.get('incomplete'):
        os.makedirs(os.path.dirname(key), exist_ok=True)
        json.dump(r, open(key, 'w', encoding='utf-8'), ensure_ascii=False)
    return r


def _one_decode(path, tmp, step, thresh=0.2):
    """One ffmpeg decode of the file for three reads: the luma and freeze pass (prerender.luma_scan's filter), the scene
    cuts (reel.scenes' filter) and every `step` seconds as a READ_W-wide jpeg. Returns (black, frozen, dur, cuts,
    {time: jpeg})."""
    import prerender as PR
    fc = (f'[0:v]split=3[a][b][c];[a]{PR.LUMA_VF}[ao];[b]select=\'gt(scene,{thresh})\',showinfo[bo];'
          f'[c]fps=1/{step}:round=down,scale={READ_W}:-2[co]')
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-y', '-i', path, '-filter_complex', fc,
                        '-map', '[ao]', '-f', 'null', '-', '-map', '[bo]', '-f', 'null', '-',
                        '-map', '[co]', '-q:v', '3', f'{tmp}/f%05d.jpg'], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('shotpick: one-pass decode failed: ' + r.stderr.strip()[-300:])
    show = [l for l in r.stderr.splitlines() if 'Parsed_showinfo' in l and 'pts_time:' in l]
    black, frozen, dur = PR.luma_parse(path, r.stdout, '\n'.join(l for l in r.stderr.splitlines() if 'Parsed_showinfo' not in l))
    cuts = [0.0]
    for c in sorted(float(l.split('pts_time:')[1].split()[0]) for l in show):
        if c - cuts[-1] >= 0.5:
            cuts.append(round(c, 3))
    frames = {}
    for n in sorted(os.listdir(tmp)):
        if n.startswith('f') and n.endswith('.jpg'):
            frames[round((int(n[1:6]) - 1) * step, 2)] = os.path.join(tmp, n)
    return black, frozen, dur, cuts, frames


def _pick_fast(f, ocr, workers, budget):
    import decodecheck as DC
    import prerender as PR
    import reel
    import render_job as RJ
    import shotgate as SG
    from PIL import Image, ImageStat
    path = RJ.C.U + f
    t0 = time.time()
    deadline = t0 + budget
    nw = workers or max(2, (os.cpu_count() or 4))
    step = PR.OCR_STEP
    tmp = tempfile.mkdtemp(prefix='shotpick-')
    try:
        with cf.ThreadPoolExecutor(max_workers=2) as ex:      # the decode check and the one read decode, at once
            j_err = ex.submit(DC.decode_errors, path)
            j_one = ex.submit(_one_decode, path, tmp, step)
            errs, (black, frozen, dur, cuts, frames) = j_err.result(), j_one.result()
        stage = {'decode': round(time.time() - t0, 1)}
        info = SG.read(f)
        v0 = info['picture_start']
        times = sorted(frames)

        def nearest(t):
            if not times:
                return None
            import bisect
            i = bisect.bisect_left(times, t)
            c = [x for x in times[max(0, i - 1):i + 1]]
            return min(c, key=lambda x: abs(x - t))

        boxes = {}

        def read_one(t):
            if time.time() > deadline:
                return t, None
            im = Image.open(frames[t])
            b = reel._word_boxes(im, 60) if ocr else []
            return t, (b, im.width, ImageStat.Stat(im.convert('L')).mean[0] if b else 255)

        srcw, srch0 = reel._src_size(path)

        def grab(t, bars, out):                                  # autofocus frames from the same decode
            n = nearest(t)
            im = Image.open(frames[n]).convert('RGB')
            if bars:
                w_, h_, x_, y_ = [int(v) for v in bars.split('crop=')[1].split(',')[0].split(':')[:4]]
                k = im.width / srcw
                im = im.crop((round(x_ * k), round(y_ * k), round((x_ + w_) * k), round((y_ + h_) * k)))
            im.resize((640, max(2, round(640 * im.height / im.width)))).save(out)
            return n

        bounds = cuts[1:] + [dur]
        long_ = [(a, b) for a, b in zip(cuts, bounds) if b - a >= MIN_SECS]   # only these can hold a shot
        need = [t for t in times if any(a - 1.0 <= t <= b + 1.0 for a, b in long_)]
        def smear_all():                                     # the smear check, in chunks, each frame in its scene
            out_ = []
            starts = list(cuts)
            lo = 0.0
            while lo < dur:
                hi = min(dur, lo + CHUNK)
                if not any(x < hi and y > lo for x, y in long_):   # only short scenes here: nothing to offer
                    lo = hi
                    continue
                if time.time() > deadline:
                    out_.append((lo, dur, 'not read in time'))
                    break
                c = [x - lo for x in starts if lo < x < hi]
                for x, y, peak in DC.smear_times(path, lo, hi - lo + 0.5, cuts=[0.0] + c):
                    out_.append((round(x, 2), round(y, 2), f'smear (peak {peak})'))
                lo = hi
            return out_

        with cf.ThreadPoolExecutor(max_workers=nw + 1) as ex:
            j_smear = ex.submit(smear_all)
            j_ocr = [ex.submit(read_one, t) for t in need]
            try:
                fo = reel.autofocus(f, 0.0, dur, grab=grab, cuts=cuts, min_scene=MIN_SECS)
            except Exception as e:                               # noqa: BLE001
                print(f'shotpick: autofocus failed on {f} ({e}); centre focus', flush=True)
                fo = [(0.0, 0.5)]
            stage['autofocus'] = round(time.time() - t0, 1)
            for j in j_ocr:
                t, got = j.result()
                boxes[t] = got
            stage['ocr'] = round(time.time() - t0, 1)
            smear = j_smear.result()
        unread = sum(1 for v in boxes.values() if v is None)
        times = need

        def read(t):
            n = nearest(t)
            return None if n is None else boxes.get(n)

        labels = _labels(boxes)                                # Forza, 17 Nov: "IN-ENGINE FOOTAGE" on every frame
        offs = [(float(o), _focus_value(v)) for o, v in fo] or [(0.0, 0.5)]
        look_min = getattr(reel, 'LOOK_MIN', 0.3)
        side_on = {round(float(o), 3): room for o, _side, room in getattr(fo, 'profile', []) if room < look_min}
        scenes = [(o, offs[i + 1][0] if i + 1 < len(offs) else dur, v) for i, (o, v) in enumerate(offs)]
        stage['smear'] = round(time.time() - t0, 1)
        bars_memo = {}

        def bars_of(a, b):                                    # one cropdetect per scene, shared by OCR and letterbox
            k = (a, b)
            if k not in bars_memo:
                a2 = max(a, v0)
                bars_memo[k] = reel._bars(path, max(0.0, a2), max(0.3, min(3.0, b - a2)))
            return bars_memo[k]

        def one(k):
            a, b, v = scenes[k]
            if b - a < MIN_SECS:                               # too short for a shot: not read
                return k, [(a, b, f'scene under {MIN_SECS} s')]
            bad = [(x, y, r) for x, y, r in black + frozen + smear if y > a and x < b]
            hard, soft = PR.ocr_shot(path, f, a, b - a, v, dur, first=False, ocr=ocr, read=read, bars=bars_of(a, b))
            txt = [s_ for s_ in soft if s_[2].startswith(('text', 'cut-text'))]
            bad += hard + txt
            if labels:
                bl = bars_of(a, b)[0]
                srcw_, srch_ = srcw, info['height'] or srch0
                for word, (x0l, x1l) in labels.items():
                    for q in (0.1, 0.5, 0.9):              # the window at three points of the scene (it may pan)
                        wx0, _wy0, wx1, _wy1 = reel._window(bl, srcw_, srch_, reel._fo_at(v, (b - a) * q, b - a))
                        lx0, lx1 = x0l * srcw_, x1l * srcw_
                        if lx1 > wx0 and lx0 < wx1:
                            bad.append((a, b, f'trailer label "{word}" in the window'))
                            break
            if a < v0:
                bad.append((a, min(b, v0), f'before the picture ({v0:.2f} s on this copy)'))
            rows, boxed = SG._letterbox_rows(f, max(a, v0), min(3.0, b - max(a, v0)), info['height'], bars=bars_of(a, b))
            if boxed:
                bad.append((a, b, f'letterboxed, {rows} of {info["height"]} rows'))
            if round(a, 3) in side_on:
                bad.append((a, b, f'profile face, {side_on[round(a, 3)]:.0%} look room'))
            return k, bad

        with cf.ThreadPoolExecutor(max_workers=nw) as ex:
            results = dict(ex.map(one, range(len(scenes))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = _collect(f, dur, v0, scenes, results, errs)
    stage['scenes'] = round(time.time() - t0, 1)
    out['stages'] = stage
    if unread or any(r == 'not read in time' for _x, _y, r in smear):
        out['incomplete'] = f'{unread} of {len(times)} frames not read in {budget:.0f} s'
    return out


def _labels(boxes):
    """{word: (x0, x1) as shares of the frame width} for words read on LABEL_SHARE of the read frames in one place."""
    read = [v for v in boxes.values() if v and v[0] is not None]
    if len(read) < 8:
        return {}
    seen = {}
    for b, w, _l in read:
        for word, l, _t, r, _bt in b or []:
            seen.setdefault(word.upper(), []).append((l / w, r / w))
    out = {}
    for word, xs in seen.items():
        if len(word) < 4 or len(xs) < LABEL_SHARE * len(read):
            continue
        cs = sorted((p + q) / 2 for p, q in xs)
        med = cs[len(cs) // 2]
        near = [(p, q) for p, q in xs if abs((p + q) / 2 - med) <= LABEL_POS]
        if len(near) >= LABEL_SHARE * len(read):
            out[word] = (min(p for p, _ in near), max(q for _, q in near))
    return out


def _collect(f, dur, v0, scenes, results, errs):
    out_shots, rejected = [], []
    for k, (a, b, v) in enumerate(scenes):
        bad = results[k]
        for x, y, r in bad:
            rejected.append({'start': round(max(a, x), 2), 'end': round(min(b, y), 2), 'why': r, 'scene': k})
        for p, q in _subtract(a, b, bad):
            if q - p >= MIN_SECS:
                out_shots.append({'start': round(p, 2), 'end': round(q, 2), 'secs': round(min(MAX_SECS, q - p), 2),
                                  'focus': v, 'scene': k})
    return {'file': f, 'duration': round(dur, 2), 'picture_start': v0, 'cuts': [round(a, 2) for a, _b, _v in scenes[1:]],
            'decode_clean': not errs, 'decode_errors': len(errs), 'shots': out_shots, 'rejected': rejected}


def _pick_slow(f, ocr=True, workers=None):
    import decodecheck as DC
    import prerender as PR
    import reel
    import render_job as RJ
    path = RJ.C.U + f
    errs = DC.decode_errors(path)
    black, frozen, dur = PR.luma_scan(path)
    try:
        fo = reel.autofocus(f, 0.0, dur)
    except Exception as e:                                   # noqa: BLE001
        print(f'shotpick: autofocus failed on {f} ({e}); centre focus', flush=True)
        fo = [(0.0, 0.5)]
    offs = [(float(o), _focus_value(v)) for o, v in fo] or [(0.0, 0.5)]
    import shotgate as SG
    info = SG.read(f)
    v0 = info['picture_start']
    look_min = getattr(reel, 'LOOK_MIN', 0.3)
    side_on = {round(float(o), 3): room for o, _side, room in getattr(fo, 'profile', []) if room < look_min}
    scenes = [(o, offs[i + 1][0] if i + 1 < len(offs) else dur, v) for i, (o, v) in enumerate(offs)]

    def one(k):
        a, b, v = scenes[k]
        bad = [(x, y, r) for x, y, r in black + frozen if y > a and x < b]
        hard, soft = PR.ocr_shot(path, f, a, b - a, v, dur, first=False, ocr=ocr)
        bad += hard + [s for s in soft if s[2].startswith(('text', 'cut-text'))]
        bad += PR.smear_shot(path, a, b - a)
        if a < v0:                               # before the picture on this copy (Duck, 15 Nov: video from 1.52 s)
            bad.append((a, min(b, v0), f'before the picture ({v0:.2f} s on this copy)'))
        rows, boxed = SG._letterbox_rows(f, max(a, v0), min(3.0, b - max(a, v0)), info['height'])
        if boxed:
            bad.append((a, b, f'letterboxed, {rows} of {info["height"]} rows'))
        if round(a, 3) in side_on:              # a profile face the 9:16 window cannot give look room (21 Oct rule)
            bad.append((a, b, f'profile face, {side_on[round(a, 3)]:.0%} look room'))
        return k, bad

    with cf.ThreadPoolExecutor(max_workers=workers or max(2, (os.cpu_count() or 4) - 1)) as ex:
        results = dict(ex.map(one, range(len(scenes))))
    return _collect(f, dur, v0, scenes, results, errs)

def summary(r):
    return (f"shots: {r['file']}: {len(r['shots'])} clean stretches over {r['duration']} s, "
            f"{len(r['rejected'])} rejected, decode {'clean' if r['decode_clean'] else 'ERRORS'}, "
            f"read {r.get('read_secs', '?')} s" + (' (cached)' if r.get('cached') else '')
            + (f", INCOMPLETE: {r['incomplete']}" if r.get('incomplete') else ''))


def main(argv):
    if len(argv) < 2 or argv[0] not in ('file', 'job'):
        raise SystemExit(__doc__)
    out = argv[argv.index('--out') + 1] if '--out' in argv else None
    files = []
    if argv[0] == 'file':
        files = [argv[1]]
    else:
        import reel
        import render_job as RJ
        job = json.load(open(argv[1], encoding='utf-8'))
        for item in job.get('footage', []):
            RJ.fetch(item)
            if os.path.splitext(item['file'])[1].lower() not in reel.STILL and not item['file'].endswith('.png'):
                files.append(item['file'])
    res = []
    for f in files:
        r = pick(f)
        res.append(r)
        print(summary(r), flush=True)
        print('SHOTS_JSON: ' + json.dumps(r, ensure_ascii=False), flush=True)
    if out:
        json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
