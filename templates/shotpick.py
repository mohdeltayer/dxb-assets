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
Output, per file: {"file", "duration", "decode_clean", "shots": [{"start", "end", "secs", "focus", "scene"}],
"rejected": [{"start", "end", "why"}]}. The job takes a shot as [file, start, secs, focus]. The prerender workflow runs
it with mode `shots` and prints SHOTS_JSON lines; nothing is committed.
"""
import concurrent.futures as cf
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MIN_SECS = 1.6
MAX_SECS = 4.0
PAD = 0.15            # seconds kept clear either side of a bad interval


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


def pick(f, ocr=True, workers=None):
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
    look_min = getattr(reel, 'LOOK_MIN', 0.3)
    side_on = {round(float(o), 3): room for o, _side, room in getattr(fo, 'profile', []) if room < look_min}
    scenes = [(o, offs[i + 1][0] if i + 1 < len(offs) else dur, v) for i, (o, v) in enumerate(offs)]

    def one(k):
        a, b, v = scenes[k]
        bad = [(x, y, r) for x, y, r in black + frozen if y > a and x < b]
        hard, soft = PR.ocr_shot(path, f, a, b - a, v, dur, first=False, ocr=ocr)
        bad += hard + [s for s in soft if s[2].startswith(('text', 'cut-text'))]
        bad += PR.smear_shot(path, a, b - a)
        if round(a, 3) in side_on:              # a profile face the 9:16 window cannot give look room (21 Oct rule)
            bad.append((a, b, f'profile face, {side_on[round(a, 3)]:.0%} look room'))
        return k, bad

    out_shots, rejected = [], []
    with cf.ThreadPoolExecutor(max_workers=workers or max(2, (os.cpu_count() or 4) - 1)) as ex:
        results = dict(ex.map(one, range(len(scenes))))
    for k, (a, b, v) in enumerate(scenes):
        bad = results[k]
        for x, y, r in bad:
            rejected.append({'start': round(max(a, x), 2), 'end': round(min(b, y), 2), 'why': r, 'scene': k})
        for p, q in _subtract(a, b, bad):
            if q - p >= MIN_SECS:
                out_shots.append({'start': round(p, 2), 'end': round(q, 2), 'secs': round(min(MAX_SECS, q - p), 2),
                                  'focus': v, 'scene': k})
    return {'file': f, 'duration': round(dur, 2), 'decode_clean': not errs,
            'decode_errors': len(errs), 'shots': out_shots, 'rejected': rejected}


def summary(r):
    return (f"shots: {r['file']}: {len(r['shots'])} clean stretches over {r['duration']} s, "
            f"{len(r['rejected'])} rejected, decode {'clean' if r['decode_clean'] else 'ERRORS'}")


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
