"""Templates never refuse (adv-20261118-templates-never-refuse A, Mohammad 18 Nov 2026, 18:06 Dubai).

Four hard stops are left on the slip lane and render-live; everything else is a warning in the log and qc.json, and the
Reel ships:
  fact        a wrong fact flagged by the brief ("fact_flag" in the job or its story file, non-empty)
  graphic     graphic content (the director's send-back reason, unchanged)
  text        unreadable text: a line outside the safe zone, or bidi-broken (a Latin, digit or bracket first on a visual
              line, an Arabic prefix glued to a Latin word, a flipping sign)
  decode      a video that does not decode (a source twice, or the finished Reel)

What used to refuse now falls down a ladder, logged per slot:
  picture  a crop (fill inside the 2x cap) > b band/showcase layout > c stills > d graphics card
  sound    a trailer's own sound > b its music stem > c our bed
  text     re-time or shrink a line, else extend the Reel (never refused for reading time)
A check that times out or errors is a warning; an unfinished shot read never reports "0 clean stretches".

The log lines `softgate: warning: {...}` and `softgate: ladder: {...}` are read by qc.py into `warnings` and `ladder`.
`"strict": true` in a job keeps the old refusals (tests only).

Regression rule (card A): a new check runs on the last 20 Reels before it goes live, and no new check is added for two
weeks from 18 Nov 2026 (until 2 Dec 2026).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WARNINGS = []
LADDER = []
HARD = ('fact', 'graphic', 'text', 'decode')
TEXT_HARD = ('latin_first', 'glued', 'sign',       # bidi-broken
             'game_headline', 'arabic_game_name', 'name_unknown')   # Burning Sword case, 19 Nov 2026
TEXT_HARD_WORDS = ('safe zone', 'not an Arabic word', 'glues an Arabic prefix', 'grid tile corner')
FREEZE_UNTIL = '2026-12-02'


def soft(job):
    return not (isinstance(job, dict) and job.get('strict'))


def warn(stage, detail, **kw):
    row = {'stage': stage, 'detail': str(detail)[:600], **kw}
    WARNINGS.append(row)
    print('softgate: warning: ' + json.dumps(row, ensure_ascii=False), flush=True)
    return row


def ladder(kind, slot, step, why):
    """kind picture|sound|text; slot a shot index, a line, or 'reel'; step a|b|c|d."""
    row = {'kind': kind, 'slot': slot, 'step': step, 'why': str(why)[:300]}
    LADDER.append(row)
    print('softgate: ladder: ' + json.dumps(row, ensure_ascii=False), flush=True)
    return row


def guarded(stage, fn, *a, job=None, **kw):
    """Run a check; in soft mode any refusal, timeout or error becomes a warning and None comes back."""
    if job is not None and not soft(job):
        return fn(*a, **kw)
    try:
        return fn(*a, **kw)
    except (Exception, SystemExit) as e:   # noqa: BLE001
        warn(stage, f'{type(e).__name__}: {e}')
        return None


def text_hard(finding):
    """A text finding that still stops: bidi-broken or outside the safe zone."""
    if finding.get('rule') in TEXT_HARD:
        return True
    d = ' '.join(str(finding.get(k) or '') for k in ('detail', 'text', 'fix'))
    return finding.get('rule') in ('font_check', 'card_line', 'error') and any(w in d for w in TEXT_HARD_WORDS)


def fact_flag(job):
    """The brief's wrong-fact flag, from the job or its story file; '' when none."""
    f = job.get('fact_flag')
    if f:
        return str(f)
    sid = job.get('story')
    if sid:
        p = os.path.join(os.path.dirname(HERE), 'newsroom', 'stories', f'{sid}.json')
        try:
            s = json.load(open(p, encoding='utf-8'))
            if s.get('fact_flag'):
                return str(s['fact_flag'])
        except (OSError, ValueError):
            pass
    return ''


def fix_reading(job, starts_fn, place_fn, read_secs, rounds=6):
    """Text ladder: a line on screen for less than its reading time gets the deficit added to the last shot under it
    (the Reel grows). Returns the number of shots lengthened."""
    n = 0
    for _ in range(rounds):
        st, end = starts_fn(job)
        lines = place_fn(job)(st, end)
        moved = False
        for k, (text, a, z, _) in enumerate(lines):
            z = min(z, end, lines[k + 1][1] if k + 1 < len(lines) else end)
            need = read_secs(text)
            if z - a >= need - 0.05:
                continue
            # the shot the line ends on: the latest shot starting before z
            idx = max([i for i, s in enumerate(st) if s < z - 0.01] or [len(st) - 1])
            sh = job['shots'][idx]
            add = round(need - (z - a) + 0.1, 2)
            sh[2] = round(float(sh[2]) + add, 2)
            ladder('text', f'line {k + 1}', 'a', f'{z - a:.1f} s of {need:.1f} s: shot {idx} lengthened by {add} s')
            n += 1
            moved = True
            break
        if not moved:
            break
    return n


def summary():
    return {'warnings': WARNINGS, 'ladder': LADDER}


def from_log(lines):
    """qc.py: the warnings and ladder steps of a render log."""
    w, l = [], []
    for ln in lines:
        s = ln.strip()
        for tag, dst in (('softgate: warning: ', w), ('softgate: ladder: ', l)):
            if s.startswith(tag):
                try:
                    dst.append(json.loads(s[len(tag):]))
                except ValueError:
                    pass
    return w, l


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'log':
        w, l = from_log(open(sys.argv[2], encoding='utf-8', errors='replace'))
        print(json.dumps({'warnings': w, 'ladder': l}, ensure_ascii=False, indent=1))
    else:
        print(__doc__)
