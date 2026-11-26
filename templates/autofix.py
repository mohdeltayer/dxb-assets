"""The server fixes the job itself instead of refusing it (adv-20261117-gates-fix-not-refuse, item B; Mohammad,
17 Nov 2026, 05:54 Dubai: "let's focus on the server fix now").

Overnight on 16 to 17 Nov Production 2 built 3 Reels in 10 hours: the gates refused one mechanical fault per pass and
every refusal cost a model round trip. Here the server applies the mechanical fix itself, records it, and refuses only
when no fix exists, with the reason.

Shots (on the server's own copy, through templates/shotgate.py):
  - a shot that crosses a scene cut is trimmed to the longer clean side of the cut;
  - a shot that starts before the picture or sits on a letterbox takes the nearest clean start of the same length;
  - a shot whose subject leaves the 9:16 window is trimmed to its longest safe length (at least MIN_SHOT s);
  - a shot whose subject is cut by the edge (or that cannot be trimmed) takes the focus that keeps the subject inside
    at every sample, else the nearest clean stretch of the same source within SHIFT s;
  - time a trim takes away goes to the next shot (or the one before) when that shot stays clean with it.
Text:
  - the mechanical text faults of item H (textrules.fix: glued prefix, percent and plus signs);
  - a line that enters while the headline band is up: the shot before it is lengthened to the earliest allowed start;
  - a credit too wide for the safe zone: one size down at a time to CREDIT_MIN, then two lines.

Every change is a dict {where, rule, what, before, after}; the render writes them to qc.json under `autofixed` and the
fixed job back to main (render-live). `"autofix": false` in a job turns all of it off.

    python3 templates/autofix.py text <job.json> [--dry] [--log fixes.json]      text fixes (needs the Dubai font for credits)
    python3 templates/autofix.py shots <job.json> [--dry] [--log fixes.json]     shot fixes (fetches the footage)
    python3 templates/autofix.py keep <job.json> <qc.json>                       the fixed job into the Reel's qc.json
"""
import copy
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MIN_SHOT = 1.0            # no shot is trimmed shorter than this
SHIFT = 5.0               # a subject shot may move this far in its source to find a clean stretch
SHIFT_STEP = 0.5
ROUNDS = 3                # shot passes; each pass re-reads every shot the last one changed
CREDIT_MIN = 30           # px: a credit is never set smaller than this
CREDIT_STEP = 2
HEAD_PAD = 0.05           # s past the headline's clear time a moved line enters
BUDGET = 300              # s of shot attempts per job; past it the gate refuses what is left (render step: 15 min)

LOG = []


def enabled(job):
    return job.get('autofix', True) is not False and job.get('kind') not in ('famitsu', 'breaking')


def _note(where, rule, what, before=None, after=None):
    d = {'where': where, 'rule': rule, 'what': what}
    if before is not None:
        d['before'] = before
    if after is not None:
        d['after'] = after
    LOG.append(d)
    print(f'autofix: {where}: {rule}: {what}', flush=True)
    return d


# ---------------------------------------------------------------- text


def text(job, font=True):
    """Text fixes in place. Returns the list of changes made."""
    n0 = len(LOG)
    if job.get('kind') != 'famitsu':               # drip-fed lines cut again as sentences, every template, breaking
        import linecut as LC                       # included (Mohammad, 23 Nov 2026)
        for c in LC.merge_job(job):
            _note(c['where'], 'lines', c['what'], c['before'], c['after'])
    if not enabled(job):
        return LOG[n0:]
    import textrules as TR
    new, ch = TR.fix(job)
    if ch:
        job.clear(); job.update(new)
        for c in ch:
            _note(c['where'], 'text', c['what'], c['before'], c['after'])
    head(job)
    if font:
        credits(job)
    return LOG[n0:]


def head(job):
    """A line group that enters while the headline is still up: lengthen the shot before it so the group's first shot
    starts at the earliest allowed time (textrules.HEAD_CLEAR). A group on shot 0 always enters at 3.6 s."""
    import textrules as TR
    if not enabled(job) or job.get('layout') == 'showcase':
        return False
    changed = False
    for _ in range(4):
        starts, _end = TR._timeline(job)
        moved = False
        for g in job.get('lines') or []:
            try:
                a = int(g[0])
            except (TypeError, ValueError, IndexError):
                continue
            if not a or a >= len(starts):
                continue
            t0 = starts[a] + 0.25
            persist = TR._persist_head_spans(job, starts, _end)
            if t0 >= TR.HEAD_CLEAR - 0.005 or any(p <= t0 < q for p, q in persist):
                continue
            need = round(TR.HEAD_CLEAR - t0 + HEAD_PAD, 2)
            sh = job['shots'][a - 1]
            old = float(sh[2])
            sh[2] = round(old + need, 2)
            _note(f'shot {a - 1}', 'head_overlap', f'lengthened {old:.2f} to {sh[2]:.2f} s so the line on shot {a} '
                  f'enters at {TR.HEAD_CLEAR + HEAD_PAD:.2f} s, after the headline clears', old, sh[2])
            moved = changed = True
            break
        if not moved:
            break
    return changed


def _credit_fits(text_, size, opt):
    import reel
    import tempfile
    d = tempfile.mkdtemp(prefix='afc-')
    try:
        reel.credit_layer(text_, f'{d}/c.png', size=size, band=opt.get('band', False), low=opt.get('low', False))
        return True
    except ValueError as e:
        if 'safe zone' in str(e) or 'opens on' in str(e):
            return False
        raise
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def _two_lines(t):
    """The credit split at the space nearest its middle where both halves open on an Arabic word; a middot at the
    break is dropped. None when there is no such space."""
    import reel
    words = t.split(' ')
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]).rstrip(' ·'), ' '.join(words[k:]).lstrip(' ·')
        if not a or not b:
            continue
        if not reel._arabic(a.lstrip('«"“‏')[0]) or not reel._arabic(b.lstrip('«"“‏')[0]):
            continue
        if reel.GLUED.search(a) or reel.GLUED.search(b):
            continue
        score = abs(len(a) - len(b)) - (1000 if words[k - 1].endswith('·') or words[k].startswith('·') else 0)
        if best is None or score < best[0]:
            best = (score, a + '\n' + b)
    return best[1] if best else None


def credits(job):
    """A credit wider than the safe zone: one size down at a time to CREDIT_MIN, then two lines at the original size
    and down again. Needs the Dubai font (the server); without it nothing is changed."""
    import fast_ar as FA
    if not os.path.exists(FA.FONTS + 'Dubai-Medium.ttf'):
        return False
    changed = False
    for i, c in enumerate(job.get('credits') or [], 1):
        if not (isinstance(c, list) and len(c) > 2 and isinstance(c[2], str)):
            continue
        opt = c[3] if len(c) > 3 and isinstance(c[3], dict) else {}
        size = int(opt.get('size', 36))
        if '\n' not in c[2] and _credit_fits(c[2], size, opt):
            continue
        # The credit ladder (Mohammad, 21 Nov 2026, templates/creditfit.py): full form on one line, Latin names only,
        # short names, primary source and footage owner, smaller type, and only then two lines.
        import creditfit
        import reel
        from PIL import Image, ImageDraw
        import fast_ar as FA2
        import ig_ar as G2
        probe = ImageDraw.Draw(Image.new('L', (reel.W, 10)))
        got = creditfit.fit(c[2], size, lambda r, s: probe.textlength(r, font=FA2.F('Medium', s), **G2.AR),
                            reel.W - reel.R - reel.L, min_size=CREDIT_MIN)
        if got is None or ('\n'.join(got['rows']) == c[2] and got['size'] == size):
            continue                       # no fix (the text check refuses it with the reason), or nothing to change
        fixed = ('\n'.join(got['rows']), got['size'])
        if not _credit_fits(fixed[0], fixed[1], opt):
            continue
        before = {'text': c[2], 'size': size}
        if len(c) > 3 and isinstance(c[3], dict):
            c[3]['size'] = fixed[1]
        else:
            while len(c) < 3:
                c.append('')
            c[3:] = [{'size': fixed[1]}]
        c[2] = fixed[0]
        _note(f'credit {i}', 'credit_width', 'set ' + ('on two lines' if '\n' in fixed[0] else 'one line') +
              f' at {fixed[1]} px (was {size} px, too wide for the safe zone)', before, {'text': fixed[0], 'size': fixed[1]})
        changed = True
    return changed


# ---------------------------------------------------------------- shots


def _rows(job):
    import render_job as RJ
    import reel
    rows = RJ.clean_nudge(job, job['shots'])
    for sh in rows:
        f, st, secs = sh[0], sh[1], sh[2]
        if (len(sh) > 3 and sh[3] is None and isinstance(st, (int, float)) and isinstance(f, str)
                and not f.endswith(('.png', '.jpg', '.jpeg', '.webp')) and os.path.exists(RJ.C.U + f)):
            sh[3] = [list(k) for k in reel.autofocus(f, st, secs)]
    return rows


def _one(job, sh):
    """The shot gate's problems for one shot, read alone (its index is 0 in what comes back)."""
    import shotgate as SG
    row = [list(sh)]
    tp, _ = SG.timing_problems(job, row)
    return tp + SG.drift_problems(job, row) + SG.frame_problems(job, row)


def _aim(p):
    """The static focus (0 left to 1 right) that keeps the tracked subject most inside the window at every sample, if
    that keeps it inside by the gate's measure; else None."""
    import shotgate as SG
    share, track = p.get('share'), p.get('track') or []
    if not share or not track or share >= 0.999:
        return None
    best = None
    for k in range(0, 101):
        x = k / 100
        left = x * (1 - share)
        win = (left, left + share)
        worst = min(SG._inside((b[1], b[2]), win) for b in track)
        if best is None or worst > best[0] + 1e-6 or (abs(worst - best[0]) < 1e-6 and abs(x - 0.5) < abs(best[1] - 0.5)):
            best = (worst, x)
    if best and best[0] >= SG.DRIFT_INSIDE + 0.1:
        return round(best[1], 2)
    return None


def _is_footage(sh):
    f, st = sh[0], sh[1]
    return isinstance(f, str) and isinstance(st, (int, float)) and not f.endswith(('.png', '.jpg', '.jpeg', '.webp')) \
        and '-gfx-' not in f and not f.startswith('numgfx')


def _is_still(sh):
    return isinstance(sh[0], str) and sh[0].lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))


def _fill(job, i, lost, tried):
    """Give `lost` seconds to the next shot, else the one before, when it stays clean with them."""
    if lost < 0.05:
        return
    sh = job['shots']
    for j in (i + 1, i - 1):
        if not (0 <= j < len(sh)) or j in tried:
            continue
        cand = list(sh[j])
        cand[2] = round(float(cand[2]) + lost, 2)
        if _is_still(cand) or (_is_footage(cand) and not _one(job, cand)):
            _note(f'shot {j}', 'fill', f'lengthened {float(sh[j][2]):.2f} to {cand[2]:.2f} s to keep the time shot {i} '
                  'gave up', float(sh[j][2]), cand[2])
            sh[j][2] = cand[2]
            return
    _note(f'shot {i}', 'fill', f'{lost:.2f} s shorter in all: no neighbouring shot stays clean with the time')


def _attempts(p, sh):
    f, st, secs = sh[0], float(sh[1]), float(sh[2])
    fo = sh[3] if len(sh) > 3 else None
    out = []
    if p['rule'] == 'shot_timing':
        cut = p.get('cut_at')
        if cut is not None:
            before = round(cut - st - 0.04, 2)
            after = round(st + secs - cut - 0.04, 2)
            for side in sorted([('before', before), ('after', after)], key=lambda x: -x[1]):
                if side[1] >= MIN_SHOT and side[0] == 'before':
                    out.append(('trim', [f, st, before, fo], f'trimmed to {before:.2f} s, the clean part before the '
                                f'scene cut at {cut:.2f} s'))
                elif side[1] >= MIN_SHOT:
                    out.append(('trim', [f, round(cut + 0.04, 2), after, fo], f'starts after the scene cut at {cut:.2f} s '
                                f'and keeps {after:.2f} s'))
        cs = p.get('clean_start')
        if cs is not None:
            out.append(('shift', [f, cs, secs, fo], f'moved from {st:.2f} to {cs:.2f} s, the nearest clean start of the '
                        f'same {secs:.2f} s'))
    elif p['rule'] == 'subject_unseen':
        return []                          # stylised art the detector cannot see: the showcase, no guessing (26 Nov)
    elif p['rule'] == 'shot_long':
        safe = p.get('safe_secs') or 4.0
        if secs > safe:
            out.append(('trim', [f, st, safe, fo], f'trimmed from {secs:.2f} to {safe:.2f} s: no shot over 4 s unless it '
                        'moves with its subject in the window (crop fix, 26 Nov 2026)'))
    elif p['rule'] in ('subject_empty', 'subject_text_cut'):
        for x in (0.5, 0.3, 0.7):  # re-aim the window first, then another stretch
            if fo is None or (not isinstance(fo, list) and abs(float(fo) - x) > 0.01) or isinstance(fo, list):
                out.append(('focus', [f, st, secs, x], f'focus {json.dumps(fo)} to {x}: re-aimed (crop fix, 26 Nov 2026)'))
        k = 1.0                            # whole seconds, up to 3 s: each candidate reads frames, the detector and OCR
        while k <= 3.0 + 1e-6:
            for s in (round(st + k, 2), round(st - k, 2)):
                if s >= 0:
                    out.append(('shift', [f, s, secs, fo], f'moved from {st:.2f} to {s:.2f} s, the nearest stretch with '
                                'a subject in the window and no cut text (crop fix)'))
            k += 1.0
    else:
        safe = p.get('safe_secs')
        if p['rule'] == 'subject_drift' and safe is not None and safe >= MIN_SHOT:
            out.append(('trim', [f, st, safe, fo], f'trimmed to {safe:.2f} s, its longest safe length before the subject '
                        'leaves the 9:16 window'))
        x = _aim(p)
        if x is not None:
            out.append(('focus', [f, st, secs, x], f'focus {json.dumps(fo)} to {x}: the subject stays inside the window'))
        k = SHIFT_STEP
        while k <= SHIFT + 1e-6:
            for s in (round(st + k, 2), round(st - k, 2)):
                if s >= 0:
                    out.append(('shift', [f, s, secs, fo], f'moved from {st:.2f} to {s:.2f} s, the nearest stretch of the '
                                'same source with the subject inside'))
            k += SHIFT_STEP
    return out


CROP_RULES = ('subject_empty', 'subject_text_cut')
CROP_BUDGET = 45           # s per job for the crop fix's re-aim and shift reads; past it the shot takes the showcase
CROP_KEEP = 2              # candidates that read clean are confirmed with the full gate, at most this many
_CROP_SPENT = [0.0]


def _crop_screen(job, tries, t_start):
    """The crop fix's candidates (re-aims, then shifts) read together: one frame read and one detector pass for all of
    them (shotgate.frame_problems batches), then only the first CROP_KEEP clean ones go to the full gate. Past
    CROP_BUDGET s in the job, none: the shot falls to the showcase (render_job.gate_ladder)."""
    import shotgate as SG
    if _CROP_SPENT[0] >= CROP_BUDGET or not tries:
        return []
    t0 = time.time()
    try:
        cands = [list(c) for _k, c, _w in tries]
        bad = {int(p['where'].split()[1]) for p in SG.frame_problems(job, cands)}   # the full gate confirms timing
    finally:
        _CROP_SPENT[0] += time.time() - t0
    return [t for n, t in enumerate(tries) if n not in bad][:CROP_KEEP]


def shots(job):
    """Shot fixes in place, on the server's copy of the footage. Returns the problems no fix could clear (the gate
    refuses those)."""
    import shotgate as SG
    if not enabled(job):
        return SG.problems(job, _rows(job))
    left, t_start = [], time.time()
    for rnd in range(ROUNDS):
        rows = _rows(job)
        probs = SG.problems(job, rows)
        if not probs:
            return []
        progress = False
        done = set()
        left = []
        for p in probs:
            i = int(p['where'].split()[1])
            if i in done:
                continue
            done.add(i)
            sh = job['shots'][i]
            fixed = False
            tries = _attempts(p, rows[i])
            if p['rule'] in CROP_RULES:            # crop fix: every candidate read in one detector pass, under a budget
                tries = _crop_screen(job, tries, t_start)
            for kind, cand, what in tries:
                if time.time() - t_start > BUDGET:
                    break
                if len(cand) > 3 and cand[3] is None and len(sh) <= 3:
                    cand = cand[:3]
                if not _one(job, cand):
                    before = list(sh)
                    old = float(sh[2])
                    sh[:] = list(cand) + list(sh[4:])
                    _note(f'shot {i}', p['rule'], what, before, list(sh))
                    if kind == 'trim':
                        _fill(job, i, round(old - float(sh[2]), 2), done)
                    fixed = progress = True
                    break
            if not fixed:
                left.append(p)
        if not progress:
            break
        if head(job):                       # a trim can pull a line under the headline: move it back out
            continue
    rows = _rows(job)
    left = SG.problems(job, rows)
    for p in left:
        p['autofix'] = 'no fix: ' + ('no trim, focus or clean stretch within %.0f s keeps it clean' % SHIFT
                                     if p['rule'] != 'shot_timing' else 'no clean part of the shot and no clean start')
    return left


_SAVED = [0]


def save_log(path):
    """Append the changes not yet saved to `path` (a JSON list shared by the text and render steps)."""
    new_, _SAVED[0] = LOG[_SAVED[0]:], len(LOG)
    if not new_:
        return
    old = []
    if path and os.path.exists(path):
        try:
            old = json.load(open(path, encoding='utf-8'))
        except (ValueError, OSError):
            old = []
    if path:
        json.dump(old + new_, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def keep(job_path, qc_path):
    """The job as the server fixed and rendered it, stored in the Reel's qc.json (`job_after_autofix`)."""
    q = json.load(open(qc_path, encoding='utf-8'))
    q['job_after_autofix'] = json.load(open(job_path, encoding='utf-8'))
    json.dump(q, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main(argv):
    if len(argv) == 3 and argv[0] == 'keep':
        keep(argv[1], argv[2])
        return 0
    if len(argv) < 2 or argv[0] not in ('text', 'shots'):
        raise SystemExit(__doc__)
    path = argv[1]
    job = json.load(open(path, encoding='utf-8'))
    orig = copy.deepcopy(job)
    if argv[0] == 'text':
        text(job)
        left = []
    else:
        import render_job as RJ
        for item in job.get('footage', []):
            RJ.fetch(item)
        left = shots(job)
        for p in left:
            print('shotgate: ' + p['detail'] + ' (' + p.get('autofix', '') + ')')
    if '--log' in argv:
        save_log(argv[argv.index('--log') + 1])
    if job != orig and '--dry' not in argv:
        json.dump(job, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'autofix: {len(LOG)} change(s) written to {path}')
    else:
        print(f'autofix: {len(LOG)} change(s)' + (' (dry run, job not written)' if '--dry' in argv else ''))
    return 1 if left else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
