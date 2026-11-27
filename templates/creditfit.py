"""The credit ladder (Mohammad, 21 Nov 2026): the on-screen source and footage credit on every Reel is never dropped,
never runs off the frame and never sits on other text. When it does not fit on one line in the safe zone, it is
shortened in this order, stopping at the first step that fits:

  1. full form, on one line: the credit as written (Arabic name then the Latin in brackets);
  2. Latin names only, no Arabic spelling, no brackets: «المصدر: Metacritic, Notebookcheck · اللقطات: Rockstar Games»;
  3. shorter official names from the short-name list in newsroom/names-ar.md («Rockstar Games» -> «Rockstar»);
  4. the primary source (the first named) and the footage owner only; other outlets are named in their own line;
  5. the type steps down to MIN_SIZE (the smallest readable credit);
  6. two lines (source / footage), from the given size down to MIN_SIZE.
Nothing fits: None, and the caller stops on it as unreadable text (a credit outside the safe zone). The opening word
stays Arabic (المصدر, اللقطات), so every row reads right to left. This overrides the Arabic-then-brackets naming rule for
credits only; lines, headlines and captions keep it.

    fit(text, size, measure) -> {'rows': [...], 'size': px, 'step': 1..6, 'form': one-line text} or None
    forms(text) -> [(step, one-line text), ...]   (steps 1 to 4, duplicates removed)

`measure(row, size)` returns the drawn width in px; reel.credit_layer and autofix.credits pass the Dubai font's.
`room` is the safe zone's width (reel.W - reel.R - reel.L).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_SIZE = 30            # px: never smaller (autofix.CREDIT_MIN)
STEP = 2
ARABIC = re.compile('[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
LATIN = re.compile('[A-Za-z]')
PAIR = re.compile(r'([^()،,]*?)\s*\(([^()]*[A-Za-z][^()]*)\)')
FOOT = re.compile(r'\s*[،,]?\s*(?:و\s*)?(?:ال)?لقطات(?:\s+من|\s*:)\s*')
SOURCE = re.compile(r'^\s*المصدر\s*:\s*')
LEADS = ('شركة ', 'موقع ', 'استوديو ', 'منصة ', 'صفحة ', 'الحساب الرسمي لـ ', 'الحساب الرسمي ل')
SEP_SOURCE, SEP_FOOT = 'المصدر: ', 'اللقطات: '
MIDDOT = ' · '

_TABLES = None


def _tables():
    """({arabic form: latin}, {latin lower: short latin}) from newsroom/names-ar.md: the name table rows and the
    '## Short names for credits' section (rows | Full | Short |)."""
    global _TABLES
    if _TABLES is not None:
        return _TABLES
    ar2la, short = {}, {}
    try:
        text = open(os.path.join(ROOT, 'newsroom', 'names-ar.md'), encoding='utf-8').read()
    except OSError:
        text = ''
    in_short = False
    for row in text.splitlines():
        if row.startswith('#'):
            in_short = 'short names for credits' in row.lower()
            continue
        if not row.startswith('|'):
            continue
        cells = [c.strip() for c in row.strip('|').split('|')]
        if len(cells) < 2 or set(cells[0]) <= set('-: '):
            continue
        if in_short:
            if LATIN.search(cells[0]) and LATIN.search(cells[1]):
                short[cells[0].lower()] = cells[1]
            continue
        if LATIN.search(cells[0]) and ARABIC.search(cells[1]):
            latin = re.sub(r'\s*\(.*?\)\s*', ' ', cells[0]).strip()
            for form in re.split(r'[،,;]|\bthen\b', re.sub(r'\(.*?\)', '', cells[1])):
                form = form.strip(' .')
                if form and ARABIC.search(form) and not LATIN.search(form) and len(form.split()) <= 5:
                    ar2la.setdefault(form, latin)
    _TABLES = (ar2la, short)
    return _TABLES


def _latin(name):
    """One name as Latin: the bracket of «Arabic (Latin)», a Latin name as it is, an Arabic form names-ar knows, or the
    Arabic as written when nothing is known (never guessed)."""
    name = name.strip(' .،,‏')
    m = PAIR.fullmatch(name)
    if m:
        return m.group(2).strip()
    if LATIN.search(name) and not ARABIC.search(name):
        return name
    ar2la, _ = _tables()
    bare = name
    for lead in LEADS:
        if bare.startswith(lead):
            bare = bare[len(lead):]
    return ar2la.get(bare) or ar2la.get(name) or name


def _names(part):
    """The names in one part of a credit, in order: split on commas, and on «و» before a name that is bracketed or
    known (never inside a name)."""
    ar2la, _ = _tables()
    out = []
    for chunk in re.split(r'\s*(?:[،,]|\bنقل[ًا]*\s+عن)\s*', part.strip(' .،,')):   # «A نقلًا عن B»: two names (27 Nov)
        pieces = [chunk]
        while True:
            last = pieces[-1]
            m = None
            for mm in re.finditer(r'\s+و(?=\S)', last):
                left, right = last[:mm.start()], last[mm.end():]
                head = right.split('(')[0].strip()
                if left.rstrip().endswith(')') or '(' in right or head in ar2la or not ARABIC.search(right[:1] or 'x'):
                    m = mm
                    break
            if not m:
                break
            pieces[-1:] = [last[:m.start()], last[m.end():]]
        out += [p.strip() for p in pieces if p.strip()]
    return out


def parse(text):
    """{'sources': [...], 'footage': [...]} for a credit written «المصدر: ...، ولقطات من ...» (or «اللقطات: ...»), or None
    for any other credit («الصورة: ...»), which keeps its words and only steps down in size or onto two lines."""
    t = ' '.join(str(text).split())
    src = SOURCE.match(t)
    foot = FOOT.search(t)
    if not src and not (foot and foot.start() == 0):
        return None
    if foot:
        s_part, f_part = t[:foot.start()], t[foot.end():]
    else:
        s_part, f_part = t, ''
    s_part = SOURCE.sub('', s_part)
    return {'sources': _names(s_part) if s_part.strip() else [], 'footage': _names(f_part) if f_part.strip() else []}


def _join(sources, footage):
    parts = []
    if sources:
        parts.append(SEP_SOURCE + ', '.join(sources))
    if footage:
        parts.append(SEP_FOOT + ', '.join(footage))
    return MIDDOT.join(parts)


def forms(text):
    """[(step, one-line text)] for steps 1 to 4, in order, without repeats."""
    full = ' '.join(str(text).split())
    out = [(1, full)]
    p = parse(text)
    tail = ''
    if not p and MIDDOT.strip() in full:                   # the showcase source row: «<outlet>‏ · ‏<date>» (27 Nov 2026)
        head, tail = [x.strip(' \u200f') for x in full.split(MIDDOT.strip(), 1)]
        p = parse('المصدر: ' + head) if head and tail else None
        tail = (MIDDOT + tail) if p else ''
    if p:
        _, short = _tables()
        la_s, la_f = [_latin(n) for n in p['sources']], [_latin(n) for n in p['footage']]
        out.append((2, _join(la_s, la_f)))
        sh = lambda n: short.get(n.lower(), n)
        sh_s, sh_f = [sh(n) for n in la_s], [sh(n) for n in la_f]
        out.append((3, _join(sh_s, sh_f)))
        if sh_f:                                           # 4 needs a footage owner to keep beside the source
            out.append((4, _join(sh_s[:1], sh_f)))
        elif tail and len(sh_s) > 1:                       # a source row: the primary source and the date
            out.append((4, _join(sh_s[:1], [])))
        if tail:
            out[1:] = [(st, f + tail) for st, f in out[1:]]
    seen, res = set(), []
    for step, f in out:
        if f and f not in seen:
            seen.add(f)
            res.append((step, f))
    return res


def _arabic_first(row):
    t = row.strip().lstrip('«"“‏( ')
    return bool(t) and bool(ARABIC.match(t[0]))


GLUED = re.compile('[ء-يـ][A-Za-z0-9]')


def _ok(rows, size, measure, room):
    return all(_arabic_first(r) and not GLUED.search(r) and measure(r, size) <= room for r in rows)


def _two(form):
    """The form on two rows: at the middot between source and footage, else at the space nearest the middle where both
    rows open on an Arabic word."""
    if MIDDOT in form:
        a, b = form.split(MIDDOT, 1)
        if _arabic_first(a) and _arabic_first(b):
            return [a.strip(), b.strip()]
    words = form.split(' ')
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]).rstrip(' ·،'), ' '.join(words[k:]).lstrip(' ·')
        if a and b and _arabic_first(a) and _arabic_first(b):
            score = abs(len(a) - len(b))
            if best is None or score < best[0]:
                best = (score, [a, b])
    return best[1] if best else None


def fit(text, size, measure, room, min_size=MIN_SIZE):
    """The first step of the ladder that fits, or None."""
    fs = forms(text)
    for step, f in fs:                                     # 1 to 4: one line at the given size
        if _ok([f], size, measure, room):
            return {'rows': [f], 'size': size, 'step': step, 'form': f}
    last = fs[-1][1]
    for s in range(size - STEP, min_size - 1, -STEP):      # 5: the shortest form, smaller type
        if _ok([last], s, measure, room):
            return {'rows': [last], 'size': s, 'step': 5, 'form': last}
    rows = _two(last)                                      # 6: two lines, the given size down
    if rows:
        for s in range(size, min_size - 1, -STEP):
            if _ok(rows, s, measure, room):
                return {'rows': rows, 'size': s, 'step': 6, 'form': last}
    return None


STEP_NAMES = {1: 'full form', 2: 'Latin names only', 3: 'short names', 4: 'primary source and footage owner',
              5: 'smaller type', 6: 'two lines'}
