"""The server picks the shot times (adv-20261117-gates-fix-not-refuse C).

A job may leave the shot times to the server in two ways:
  "shots": "auto"                        every shot; "auto_shots": {"count": N, "secs": S, "files": [..]} is optional
                                         (count defaults to one shot for the headline plus one per line group, at least
                                         4; secs to 3.0, the first shot 3.5 so line 1 waits for the headline; files to
                                         every video in "footage", taken in turn)
  [file, "auto", secs, focus]            one shot inside a written list (cards and hand-timed shots stay as written)

expand(job) runs first and needs no footage: it writes the shot list with start 0.0 in each automatic slot and lists
those slots in "shots_auto", so the text checks see the timeline (only the lengths matter there). fill(job) runs on the
server once the footage is fetched: templates/shotpick.py reads each file's clean stretches (after the picture start,
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
    slots = list(job.get('shots_auto') or [])
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
    return slots


def _choose(stretches, secs, target, after, dur):
    best, score = None, None
    for s in stretches:
        if s['end'] - max(s['start'], after) < secs:
            continue
        st = max(s['start'], after)
        st = min(max(st, target), s['end'] - secs)         # as near the target as the stretch allows
        sc = abs(st - target) / max(dur, 1.0) + CENTRE_WEIGHT * abs(float(s.get('focus') or 0.5) - 0.5)
        if score is None or sc < score:
            best, score = (round(st, 2), s.get('focus')), sc
    return best


def fill(job, reader=None):
    """Pick a start and focus for every slot in job['shots_auto']. reader(file) -> shotpick.pick(file) result."""
    slots = [i for i in job.get('shots_auto') or [] if i < len(job.get('shots') or [])]
    if not slots:
        return []
    if reader is None:
        import shotpick as SP
        cache = {}

        def reader(f):
            if f not in cache:
                cache[f] = SP.pick(f)
            return cache[f]
    import autofix as AF
    by_file = {}
    for i in slots:
        by_file.setdefault(job['shots'][i][0], []).append(i)
    left = []
    for f, idx in by_file.items():
        r = reader(f)
        stretches = sorted(r.get('shots') or [], key=lambda s: s['start'])
        dur = float(r.get('duration') or 0) or max([s['end'] for s in stretches] or [1.0])
        v0 = float(r.get('picture_start') or 0.0)
        after = v0
        for k, i in enumerate(idx):
            sh = job['shots'][i]
            secs = float(sh[2])
            target = v0 + (dur - v0) * (k + 0.5) / len(idx)
            got = _choose(stretches, secs, max(target, after), after, dur)
            if got is None:                                  # nothing after the last pick: any unused clean stretch
                got = _choose(stretches, secs, target, v0, dur)
            if got is None:
                left.append({'shot': i, 'rule': 'auto_shots', 'detail': f'shot {i}: no clean stretch of {secs:.1f} s in {f}',
                             'autofix': f'{len(stretches)} clean stretches read, the longest '
                                        f'{max([s["end"] - s["start"] for s in stretches] or [0]):.1f} s; shorten the shot or add footage'})
                continue
            st, fo = got
            sh[1] = st
            if sh[3] is None and fo is not None:
                sh[3] = [[0.0, fo]]
            after = st + secs
            AF._note(f'shot {i}', 'auto_shots', f'{f} at {st:.2f} s for {secs:.1f} s, focus {fo}')
    job['shots_auto'] = [s['shot'] for s in left]
    if not job['shots_auto']:
        job.pop('shots_auto')
    return left
