"""Clean-stretch map: pure helpers shared by templates/prerender.py (which writes it) and templates/reel.py (which
reads it). No heavy imports, so reel.py can load it lazily and a job without a map never touches it.

The map is the job's `clean_map` key (embedded by `prerender.py embed` / `--write`; a sibling file in jobs/render/
would be taken by render.yml as a job):

    {"v": 1, "made": "2026-10-27T15:04Z",
     "sources": {"dn-aphelion.mp4": {"dur": 60.73,
                                    "scanned": [[11.4, 15.9], ...],          # deep-checked ranges (text, smear, decode)
                                    "bad": [[16.26, 17.21, "black+fade"]]}}, # hard intervals only, source seconds
     "suggest": {"dn-aphelion.mp4@16.0": 17.7}}                              # verified nearest clean start, same length

Black, fade, frozen, smear, decode, end-card and cut-text intervals are in `bad`; the whole file's black and frozen
stretches within 6 s of any shot are there too, so a shot can be moved. Soft findings (text in the window) are only in
the prerender report. A reviewed interval is waived in the job with `prerender_ok` [[file, t0, t1, reason]] and left
out of the map.
"""

TOL = 0.02        # seconds: a boundary inside this does not count as an overlap (frame rounding)
GUARD = 0.15      # clean room asked either side of a suggested stretch


def merge(iv, gap=0.0):
    """[(a, b, reason)] sorted and merged where they touch or lie within `gap`; reasons joined with '+'."""
    out = []
    for a, b, r in sorted(iv, key=lambda x: (x[0], x[1])):
        if out and a <= out[-1][1] + gap:
            pa, pb, pr = out[-1]
            rs = pr.split('+')
            out[-1] = (pa, max(pb, b), '+'.join(rs + [x for x in r.split('+') if x not in rs]))
        else:
            out.append((a, b, r))
    return out


def overlaps(bad, a, b, tol=TOL):
    """The intervals of `bad` that cut into [a, b]."""
    return [(x, y, r) for x, y, r in bad if x < b - tol and y > a + tol]


def covered(scanned, a, b):
    return any(lo <= a + 1e-6 and b <= hi + 1e-6 for lo, hi in scanned)


def windows(bad, dur):
    """Clean windows (start, end) of a file of length `dur` between the intervals of `bad`."""
    out, t = [], 0.0
    for x, y, _ in merge(bad):
        if x > t:
            out.append((t, x))
        t = max(t, y)
    if dur > t:
        out.append((t, dur))
    return out


def candidates(bad, dur, s, d, guard=GUARD, limit=6):
    """Starts for a shot of length `d` that keep clear of `bad` by `guard`, nearest to `s` first. Several per window
    (nearest, window start, window end) so a caller that finds the first one wanting can try the next."""
    cand = []
    for w0, w1 in windows(bad, dur):
        lo, hi = w0 + (guard if w0 > 0 else 0.0), w1 - (guard if w1 < dur else 0.0) - d
        if hi < lo - 1e-6:
            continue
        for c in (min(max(s, lo), hi), lo, hi):
            c = round(c, 2)
            if lo - 1e-6 <= c <= hi + 1e-6 and c not in [x for x, _ in cand]:
                cand.append((c, abs(c - s)))
    cand.sort(key=lambda x: x[1])
    return [c for c, _ in cand[:limit]]


def longest_near(bad, dur, s, n=2):
    """The n clean windows (start, end, length) nearest to `s`, for the message when none is long enough."""
    ws = [(a, b, b - a) for a, b in windows(bad, dur) if b - a > 0.2]
    ws.sort(key=lambda w: min(abs(w[0] - s), abs(w[1] - s)))
    return ws[:n]


def shot_problems(cmap, shots):
    """Messages for footage shots whose span cuts into a hard interval of the map. `shots` are reel's
    (file, start, secs, focus). Shots the map does not cover are printed, not stopped (the job changed after the map)."""
    problems, notes = [], []
    for i, (f, s, d, _fo) in enumerate(shots):
        src = (cmap.get('sources') or {}).get(f)
        if s is None or src is None:
            continue
        hit = overlaps(src.get('bad', []), s, s + d)
        if hit:
            msg = f'shot {i} {f} at {s} for {d} s: ' + ', '.join(f'{x:.2f} to {y:.2f} s {r}' for x, y, r in hit)
            sug = (cmap.get('suggest') or {}).get(f'{f}@{s}')
            msg += f'; prerender suggests starting at {sug}' if sug is not None else '; no clean start was found (shorten it or use another trailer)'
            problems.append(msg)
        elif not covered(src.get('scanned', []), s, s + d):
            notes.append(f'shot {i} {f} at {s} for {d} s is outside the stretches prerender read; run prerender.py again')
    return problems, notes


def nudge(cmap, shots):
    """The shots with each hard-overlapping one moved to the map's suggested start (same length, same focus).
    Returns (shots, [(index, old, new)])."""
    out, moved = [], []
    for i, sh in enumerate(shots):
        f, s, d, fo = sh
        src = (cmap.get('sources') or {}).get(f)
        new = (cmap.get('suggest') or {}).get(f'{f}@{s}') if (src and s is not None and overlaps(src.get('bad', []), s, s + d)) else None
        if new is not None:
            out.append((f, new, d, fo)); moved.append((i, s, new))
        else:
            out.append(sh)
    return out, moved
