"""Text rules that need no font, every error in one pass (adv-20261110-one-render-per-reel, item A, Mohammad 10 Nov 2026).

The Warhammer Survivors Reel of 10 Nov took seven dispatches: the text check runs only on the server (the session has no
Dubai font), stops on the first error, and each error costs a dispatch. These rules read only the job's text, so they run
anywhere (the session included) in well under a second and report every problem at once. The server's font check
(render_job.py text) runs them first and then adds what only the font can tell (a wrap onto a Latin word, the safe zone).

    python3 templates/textrules.py <job.json> [--json out.json]     exit 1 when anything is found

Each finding: {"where": "headline" | "line 3" | "strip 2" | "credit 1" | "gfx 1", "rule": ..., "text": ..., "fix": ...}.
Rules: latin_first (a line opens on a Latin word, a digit or a bracket), glued (an Arabic prefix written onto a Latin word
or digit, «وPS5»), sign (% or + next to a digit or a Latin word flips in right-to-left text, «%10», «+New Game»),
headline_long (estimate: a headline line over HEAD_CHARS characters with a Latin name, or a headline needing more than
HEAD_LINES lines), line_count (a beat of more than 3 visual lines, or more than 2 over a split strip), reading (a line on
screen for less than its reading time), empty (an empty line or headline).
"""
import json
import re
import sys

ARABIC = re.compile('[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
GLUED = re.compile('[ء-يـ][A-Za-z0-9]')
# a % or + touching a digit or a Latin letter, on either side
SIGN = re.compile(r'(?:(?<=[0-9A-Za-z])[%+٪])|(?:[%+٪](?=[0-9A-Za-z]))')
LEAD = '«"“‏( '
HEAD_CHARS = 22          # estimate: «لعبة Warhammer Survivors» (24) did not fit one line at 100 px on 10 Nov
HEAD_LINES = 2
LINES_MAX, LINES_STRIP = 3, 2
CPS, FLOOR, FIND = 14, 2.2, 0.5   # reel.read_secs: 14 characters a second plus half a second, 2.2 s at least


def read_secs(text):
    return max(FLOOR, FIND + len(text.replace('\n', ' ').replace('|', ' ')) / CPS)


def _first_ok(line):
    t = line.strip().lstrip(LEAD)
    return not t or bool(ARABIC.match(t[0]))


def _text_rules(where, text, out):
    if not str(text).strip():
        out.append({'where': where, 'rule': 'empty', 'text': text, 'fix': 'write the line or drop it'})
        return
    for ln in str(text).split('\n'):
        if not _first_ok(ln):
            out.append({'where': where, 'rule': 'latin_first', 'text': ln,
                        'fix': 'open the line on an Arabic word («تصدر Warhammer...», not «Warhammer تصدر...»), or rebreak'})
        m = GLUED.search(ln)
        if m:
            out.append({'where': where, 'rule': 'glued', 'text': ln,
                        'fix': f'{m.group(0)!r} flips on screen: put a space after the prefix or a word between '
                               '(«و PS5», «ولجهاز PS5», «لجهاز Switch 2»)'})
        m = SIGN.search(ln)
        if m:
            out.append({'where': where, 'rule': 'sign', 'text': ln,
                        'fix': f'the {m.group(0)!r} flips to the far side in right-to-left text: spell it out '
                               '(«10 بالمئة», «New Game Plus») or drop it'})


def _texts(item):
    """A line group's texts as (text, opts)."""
    for x in item:
        if isinstance(x, str):
            yield x, {}
        elif isinstance(x, (list, tuple)) and x:
            yield str(x[0]), (x[1] if len(x) > 1 and isinstance(x[1], dict) else {})


def _timeline(job, overlap=0.4):
    """Shot starts and the cut's length, as reel.timeline builds them (reel.X = 0.4 s crossfade, 0.04 with cut)."""
    X = 0.04 if job.get('cut') else overlap
    sh = job.get('shots') or []
    if not sh:
        return [], 0.0
    starts, t = [0.0], float(sh[0][2])
    for s in sh[1:]:
        starts.append(t - X)
        t = t - X + float(s[2])
    return starts, t


def _placed(job):
    """[(text, a, z)] and the cut's end, as reel.by_shot places them: a group's sentences share equally the time from
    its first shot's start (0.25 s in, or 3.6 s on the first shot, 0 for the showcase layout) to the next shot."""
    starts, end = _timeline(job)
    if not starts:
        return None
    first = 0.0 if job.get('layout') == 'showcase' else 3.6
    out = []
    for g in job.get('lines') or []:
        try:
            a, b, texts = int(g[0]), int(g[1]), g[2]
        except (TypeError, ValueError, IndexError):
            continue
        if a >= len(starts):
            continue
        tx = [t for t, _ in _texts(texts)]
        if not tx:
            continue
        t0 = starts[a] + (0.25 if a else first)
        t1 = starts[b + 1] if b + 1 < len(starts) else end
        span = (t1 - t0) / len(tx)
        for i, x in enumerate(tx):
            out.append((x, t0 + i * span, t0 + (i + 1) * span))
    return out, end


def check(job):
    """Every font-free text problem in the job, as a list of findings (empty when clean)."""
    out = []
    if job.get('kind') == 'famitsu':
        return out
    head = job.get('headline')
    if head is not None:
        _text_rules('headline', head, out)
        parts = str(head).split('\n')
        latin = bool(re.search('[A-Za-z]', str(head)))
        if len(parts) > HEAD_LINES:
            out.append({'where': 'headline', 'rule': 'headline_long', 'text': head, 'hard': True,
                        'fix': f'{len(parts)} lines: at most {HEAD_LINES}; cut to fewer words'})
        elif latin:
            if len(parts) == 1 and len(parts[0]) > HEAD_CHARS * HEAD_LINES:
                out.append({'where': 'headline', 'rule': 'headline_long', 'text': head,
                            'fix': f'{len(parts[0])} characters with a Latin name: about {HEAD_CHARS * HEAD_LINES} fit '
                                   'in two lines at 100 px; cut it (estimate; the server font check is final)'})
            for p in parts if len(parts) > 1 else []:
                if len(p) > HEAD_CHARS:
                    out.append({'where': 'headline', 'rule': 'headline_long', 'text': p,
                                'fix': f'{len(p)} characters on one line with a Latin name: about {HEAD_CHARS} fit; '
                                       'cut or rebreak (estimate; the server font check is final)'})
    strip = bool(job.get('strip'))
    n = 0
    for gi, grp in enumerate(job.get('lines') or []):
        if not isinstance(grp, (list, tuple)) or len(grp) < 3:
            continue
        for text, opts in _texts(grp[2]):
            n += 1
            where = f'line {n}'
            _text_rules(where, text, out)
            vis = text.count('\n') + 1
            cap = LINES_STRIP if strip and job.get('layout') != 'showcase' else LINES_MAX
            if vis > cap:
                out.append({'where': where, 'rule': 'line_count', 'text': text,
                            'fix': f'{vis} visual lines: at most {cap}{" over the strip" if cap == LINES_STRIP else ""}; '
                                   'split into two beats'})
    for i, it in enumerate(job.get('strip') or [], 1):
        if isinstance(it, (list, tuple)) and it:
            _text_rules(f'strip {i}', it[0], out)
            if isinstance(it[1], str) if len(it) > 1 else False:
                m = SIGN.search(it[1])
                if m:
                    out.append({'where': f'strip {i}', 'rule': 'sign', 'text': it[1],
                                'fix': f'the {m.group(0)!r} flips: spell it out or drop it'})
    for i, c in enumerate(job.get('credits') or [], 1):
        if isinstance(c, (list, tuple)) and len(c) > 2:
            _text_rules(f'credit {i}', c[2], out)
    for i, g in enumerate(job.get('gfx') or [], 1):
        if isinstance(g, dict):
            for k in ('title', 'headline', 'line', 'note', 'caption'):
                if isinstance(g.get(k), str) and g[k].strip():
                    _text_rules(f'gfx {i} {k}', g[k], out)
    if not job.get('read_ok') and not job.get('voice'):   # a voiced Reel's lines follow the read
        placed = _placed(job)
        if placed:
            lines, end = placed
            for k, (text, a, z) in enumerate(lines):
                z = min(z, end, lines[k + 1][1] if k + 1 < len(lines) else end)
                need = read_secs(text)
                if z - a < need - 0.05:
                    out.append({'where': f'line {k + 1}', 'rule': 'reading', 'text': text.split('\n')[0],
                                'fix': f'on screen {z - a:.1f} s of the {need:.1f} s it needs: add {need - (z - a):.1f} s of '
                                       'related footage to its shots, shorten it, or move it'})
    return out


def hard(findings):
    """Findings that stop: everything except the headline-length estimates (the server's font check decides those)."""
    return [f for f in findings if f['rule'] != 'headline_long' or f.get('hard')]


def report(findings):
    if not findings:
        return 'text rules: clean'
    return 'text rules: %d problem%s\n' % (len(findings), '' if len(findings) == 1 else 's') + '\n'.join(
        f"  - {f['where']}: {f['rule']}{'' if f in hard(findings) else ' (estimate)'}: {f['text']!r} -> {f['fix']}"
        for f in findings)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    job = json.load(open(a[0], encoding='utf-8'))
    fs = check(job)
    print(report(fs))
    if '--json' in a:
        json.dump(fs, open(a[a.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(1 if hard(fs) else 0)
