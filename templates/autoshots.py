"""The server picks the shot times (adv-20261117-gates-fix-not-refuse C).

A job may leave the shot times to the server in two ways:
  "shots": "auto"                        every shot; "auto_shots": {"count": N, "secs": S, "files": [..]} is optional
                                         (count defaults to one shot for the headline plus one per line group, at least
                                         4; secs to 3.0, the first shot 3.5 so line 1 waits for the headline; files to
                                         every video in "footage", taken in turn)
  [file, "auto", secs, focus]            one shot inside a written list (cards and hand-timed shots stay as written)

expand(job) runs first and needs no footage: it writes the shot list with start 0.0 in each automatic slot and lists
those slots in "shots_auto", so the text checks see the timeline (only the lengths matter there). fill(job) runs on the
server once the footage is fetched (shotpick's fast read since 17 Nov, adv-20261117-server-speed-for-p2 A: about 45 s
per 95 s trailer on 4 cores, the whole read capped at READ_CAP; cached per file, so a second dispatch reads nothing): templates/shotpick.py reads each file's clean stretches (after the picture start,
inside one scene, no black, frozen, smear, letterbox, burnt-in or cut text, no unframeable profile face), and each slot
takes, in source order, the stretch nearest its even share of the trailer that holds its length, preferring a centred
subject. Every choice is logged like the other fixes (autofix.LOG, rule auto_shots), so qc.json `autofixed` and the job
written back to main show the times picked. A slot with no clean stretch long enough is refused by name.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SECS = 3.0
HOOK_SECS = 3.5
MIN_COUNT = 4
CENTRE_WEIGHT = 0.5        # one unit of |focus - 0.5| weighs as half the trailer's length of drift from the target
VIDEO = ('.mp4', '.mov', '.mkv', '.webm', '.m4v')


def _videos(job):
    return [it['file'] for it in job.get('footage', []) if str(it.get('file', '')).lower().endswith(VIDEO)]


def expand(job):
    """Turn "auto" markers into numeric placeholders; returns the slots (also in job['shots_auto'])."""
    sh = job.get('shots')
    opts = job.get('auto_shots') or {}
    if sh == 'auto':
        files = opts.get('files') or _videos(job)
        if not files:
            raise SystemExit('autoshots: "shots": "auto" needs at least one video in "footage"')
        groups = len(job.get('lines') or [])
        n = int(opts.get('count') or max(MIN_COUNT, groups + 1))
        secs = float(opts.get('secs') or DEFAULT_SECS)
        job['shots'] = [[files[i % len(files)], 0.0, HOOK_SECS if i == 0 else secs, None] for i in range(n)]
        job['shots_auto'] = list(range(n))
        return job['shots_auto']
    if not isinstance(sh, list):
        return []
    # a slot named in an older shots_auto whose shot now has a typed start is the builder's choice, never re-picked
    # (20 Nov 2026: the GTA VI job's explicit starts were overwritten by a stale list from its first render)
    slots = [i for i in (job.get('shots_auto') or []) if isinstance(i, int) and i < len(sh) and isinstance(sh[i], list)
             and len(sh[i]) > 1 and sh[i][1] in (0, 0.0, None, 'auto')]
    for i, s in enumerate(sh):
        if isinstance(s, list) and len(s) > 1 and s[1] == 'auto':
            s[1] = 0.0
            if len(s) < 3 or s[2] in (None, 'auto'):
                s[2:3] = [HOOK_SECS if i == 0 else DEFAULT_SECS]
            while len(s) < 4:
                s.append(None)
            if i not in slots:
                slots.append(i)
    if slots:
        job['shots_auto'] = sorted(slots)
    else:
        job.pop('shots_auto', None)
    return slots


MIN_SECS = 2.0            # a shot shortened to fit a free clean stretch keeps at least this long
READ_CAP = 180.0          # seconds for the whole read of up to three trailers (adv-20261117-server-speed-for-p2 A)
DECODE_EST = 18.0         # a file's one decode, which the budget cannot stop: never give a file less than this plus 10 s
READ = {}                 # file -> the shotpick result of this fill (render_job reports the seconds)


def _gaps(a, b, used):
    """The free pieces of [a, b] once the used ranges are taken out."""
    out, lo = [], a
    for x, y in sorted(used):
        if y <= lo or x >= b:
            continue
        if x > lo:
            out.append((lo, min(x, b)))
        lo = max(lo, y)
    if lo < b:
        out.append((lo, b))
    return out


def _free(st, secs, used):
    return all(st + secs <= a + 1e-6 or st >= b - 1e-6 for a, b in used)


def _choose(stretches, secs, target, after, dur, used=()):
    """The start nearest `target` (not before `after`) inside a clean stretch, overlapping no shot already placed."""
    best, score = None, None
    for s in stretches:
        lo, hi = max(s['start'], after), s['end'] - secs
        if hi < lo:
            continue
        cands = {round(min(max(target, lo), hi), 2), round(lo, 2)} | {round(b, 2) for _a, b in used if lo <= b <= hi}
        for st in sorted(cands):
            if not _free(st, secs, used):
                continue
            sc = abs(st - target) / max(dur, 1.0) + CENTRE_WEIGHT * abs(float(s.get('focus') or 0.5) - 0.5)
            if score is None or sc < score:
                best, score = (st, s.get('focus')), sc
    return best


def _varied_hook(job, f, stretches, secs, dur, v0, used, got):
    """The hook slot's start, moved to another clean stretch when it would reopen a recent opener of the same game or
    repeat one of the last covers on the grid (templates/variety.py); the first pick when nothing else passes."""
    try:
        import variety
        import cards as C
        led = variety.load()
        ok, why = variety.hook_ok(job, f, C.U + f, got[0], got[1], led)
        if ok:
            return got
        tried = 0
        for s in sorted(stretches, key=lambda s: abs(s['start'] - got[0]), reverse=True):
            alt = _choose([s], secs, s['start'] + 0.3, v0, dur, used)
            if not alt or abs(alt[0] - got[0]) < variety.OPENER_GAP:
                continue
            tried += 1
            ok2, _ = variety.hook_ok(job, f, C.U + f, alt[0], alt[1], led)
            if ok2:
                import autofix as AF
                AF._note('shot 0', 'variety', f'hook moved {got[0]:.2f} -> {alt[0]:.2f} s: {why}')
                return alt
            if tried >= 8:
                break
    except Exception:                            # noqa: BLE001  variety never holds a Reel
        pass
    return got


def fill(job, reader=None):
    """Pick a start and focus for every slot in job['shots_auto']. reader(file) -> shotpick.pick(file) result."""
    slots = [i for i in job.get('shots_auto') or [] if i < len(job.get('shots') or [])]
    if not slots:
        return []
    if reader is None:
        import time
        import shotpick as SP
        files = list(dict.fromkeys(job['shots'][i][0] for i in slots))
        files += [x for x in _videos(job) if x not in files]
        t_end = time.time() + READ_CAP

        def reader(f):                                       # the fast read, cached per file (shotpick.pick); the
            left_ = max(1, len([x for x in files if x not in READ]))   # whole read stays inside READ_CAP
            budget = max(DECODE_EST + 10.0, (t_end - time.time()) / left_)   # the file's whole read, decode included
            READ[f] = SP.pick(f, budget=budget)
            return READ[f]
    import autofix as AF
    by_file = {}
    for i in slots:
        by_file.setdefault(job['shots'][i][0], []).append(i)
    used = {}                                                # file -> [(start, end)] already on screen
    for k, sh in enumerate(job['shots']):
        if k not in slots and isinstance(sh[1], (int, float)) and isinstance(sh[0], str):
            used.setdefault(sh[0], []).append((float(sh[1]), float(sh[1]) + float(sh[2])))
    reads = {}

    def read(f):
        if f not in reads:
            r = reader(f)
            st = sorted(r.get('shots') or [], key=lambda s: s['start'])
            try:                                             # blocked stretches never offered (27 Nov 2026)
                import blocked as B
                st = B.split(st, B.ranges(job, f))
            except Exception:                                # noqa: BLE001
                pass
            dur = float(r.get('duration') or 0) or max([s['end'] for s in st] or [1.0])
            reads[f] = (st, dur, float(r.get('picture_start') or 0.0))
        return reads[f]
    def place(i, src, st, fo, secs, note=''):
        sh = job['shots'][i]
        sh[0], sh[1] = src, st
        if float(sh[2]) != secs:
            sh[2] = round(secs, 2)
        if sh[3] is None and fo is not None:
            sh[3] = [[0.0, fo]]
        used.setdefault(src, []).append((st, st + secs))
        AF._note(f'shot {i}', 'auto_shots', f'{src} at {st:.2f} s for {secs:.1f} s, focus {fo}' + note)

    waiting = []                                             # pass 1: each file serves its own slots, in source order
    for f, idx in by_file.items():
        stretches, dur, v0 = read(f)
        after = v0
        for k, i in enumerate(idx):
            secs = float(job['shots'][i][2])
            target = v0 + (dur - v0) * (k + 0.5) / len(idx)
            u = used.setdefault(f, [])
            got = _choose(stretches, secs, max(target, after), after, dur, u) or _choose(stretches, secs, target, v0, dur, u)
            if got is None:
                waiting.append((i, f))
                continue
            if i == 0:                                       # the hook is the cover: new opener, new cover (21 Nov, item 6)
                got = _varied_hook(job, f, stretches, secs, dur, v0, u, got)
            place(i, f, got[0], got[1], secs)
            after = got[0] + secs
    left = []
    for i, f in waiting:                                     # pass 2: the job's other footage; pass 3: a shorter shot
        secs = float(job['shots'][i][2])
        done = False
        for g in [f] + [x for x in _videos(job) if x != f]:
            if g == f:
                continue
            st2, dur2, v02 = read(g)
            got = _choose(st2, secs, v02 + (dur2 - v02) / 2, v02, dur2, used.setdefault(g, []))
            if got is not None:
                place(i, g, got[0], got[1], secs, f' (nothing free in {f})')
                done = True
                break
        if not done:
            best = None
            for g in [f] + [x for x in _videos(job) if x != f]:
                st2, dur2, v02 = read(g)
                for s in st2:
                    for lo, hi in _gaps(s['start'], s['end'], used.setdefault(g, [])):
                        ln = min(secs, hi - lo)
                        if ln >= MIN_SECS and (best is None or ln > best[3]):
                            best = (g, round(lo, 2), s.get('focus'), round(ln, 2))
            if best:
                place(i, best[0], best[1], best[2], best[3], f' (shortened from {secs:.1f} s: no free clean stretch that long)')
                done = True
        if not done:
            stretches = read(f)[0]
            left.append({'shot': i, 'rule': 'auto_shots', 'detail': f'shot {i}: no free clean stretch of {MIN_SECS:.1f} s or more',
                         'autofix': f'{len(stretches)} clean stretches read in {f}, none free in any footage; add footage'})
    job['shots_auto'] = [s['shot'] for s in left]
    if not job['shots_auto']:
        job.pop('shots_auto')
    return left
