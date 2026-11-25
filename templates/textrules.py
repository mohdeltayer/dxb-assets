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

adv-20261115-one-render-server-checks (Mohammad 15 Nov 2026; every 15 Nov Reel rendered three times with qc pass):
head_overlap (A): a story line that enters before the headline band clears (the head layer fades out from HEAD_CLEAR,
  3.30 s; reel.py's head_secs 3.5 less its 0.2 s fade). Trafficity v1 (line 1 at 2.60 s) and v2 (2.90 s) were sent back
  for it; v3 (3.31 s) passed. The fix names the earliest start and how much longer the shots before it must be. The
  showcase layout (its headline stays in its own band) and the shots a "persist" head covers are not checked.
spoken (Mohammad, same day: lines that do not connect because they are cut from the fact list): the job carries
  "spoken", the story as one paragraph of 2 to 3 Arabic sentences, and the on-screen lines, read in order, are that
  paragraph: every word of every line is found in it, in order (a word may be left out, none may be added, and the
  lines may not jump back). spoken_missing when the key is absent or not 2 to 3 sentences; spoken_order otherwise.
"""
import json
import re
import sys

ARABIC = re.compile('[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
GLUED = re.compile('[ء-يـ][A-Za-z0-9]')
# a % or + touching a digit or a Latin letter, on either side
# House words (arabic/house-glossary.md, newsroom/names-ar.md section 2). A physical, boxed or retail copy of a game is
# «نسخة مطبوعة», never «ورقية» or «ورقيًا», which read as a paper edition (Mohammad, 18 Nov 2026, after the Sea of Stars
# Reel of 17 Nov). Matches the word with or without ال and a one-letter prefix (و ب ل ف), and the tanwin forms.
PAPER = re.compile('(?<![\u0621-\u064A])[وبلفك]{0,2}(?:ال)?ورقي(?:ة|ه|ًا|اً|ا|ات)?(?![\u0621-\u064A])')
# «النسخة المادية» is not the house form either (Mohammad, 23 Nov 2026: inKONBINI v2 used it): «النسخة المطبوعة» is the only
# form for a physical edition. Caught only beside a copy word, so «مادية» in its other senses stays free.
MATERIAL = re.compile('(?<![\u0621-\u064A])[وبلفك]{0,2}(?:ال)?نسخ(?:ة|ه|تها|ته|تين|تان)?\\s+(?:ال)?مادي(?:ة|ه)(?![\u0621-\u064A])')
MATERIAL_FIX = ('a physical edition is «النسخة المطبوعة» («نسخة مطبوعة»، «بنسخة مطبوعة ورقمية»), the only form; never «النسخة '
                'المادية» (Mohammad, 23 Nov 2026)')
PAPER_FIX = ('a physical copy of a game is «نسخة مطبوعة» («النسخة المطبوعة»، «تصدر في نسخة مطبوعة»), never «ورقية» or '
             '«ورقيًا», which read as a paper edition; a story really about paper waives it with "paper_ok": "<reason>"')


def house_words(where, text, out, job=None):
    """The glossary's refused words in one text (hard findings)."""
    if job and len(str(job.get('paper_ok') or '').strip()) >= 10:
        return
    for m in PAPER.finditer(str(text or '')):
        out.append({'where': where, 'rule': 'house_word', 'text': m.group(0), 'fix': PAPER_FIX})
    for m in MATERIAL.finditer(str(text or '')):
        out.append({'where': where, 'rule': 'house_word', 'text': m.group(0), 'fix': MATERIAL_FIX})


SIGN = re.compile(r'(?:(?<=[0-9A-Za-z])[%+٪])|(?:[%+٪](?=[0-9A-Za-z]))')
LEAD = '«"“‏( '
HEAD_CHARS = 22          # estimate: «لعبة Warhammer Survivors» (24) did not fit one line at 100 px on 10 Nov
HEAD_LINES = 2
LINES_MAX, LINES_STRIP = 3, 2
CPS, FLOOR, FIND = 14, 2.2, 0.5   # reel.read_secs: 14 characters a second plus half a second, 2.2 s at least
HEAD_SECS = 3.5          # reel.reel(head_secs=3.5): the head layer runs 0 to 3.5 s ...
HEAD_CLEAR = 3.3         # ... and fades out over its last 0.2 s: a line may enter from here
SPOKEN_MIN, SPOKEN_MAX = 2, 3
TATWEEL_DIACRITICS = re.compile('[ـً-ْٰ]')
SENT_END = re.compile(r'[.!؟?]+(?=\s|$)')


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


def _persist_head_spans(job, starts, end):
    """The seconds a "persist" head keeps the headline up on purpose (render_job.persist_overlay)."""
    out = []
    for rng in ((job.get('persist') or {}).get('head') or []):
        try:
            a, b = int(rng[0]), int(rng[1])
        except (TypeError, ValueError, IndexError):
            continue
        if a < len(starts):
            out.append((starts[a], starts[b + 1] if b + 1 < len(starts) else end))
    return out


def head_problems(job):
    """Item A: no story line enters while the headline band is still up (it fades out from HEAD_CLEAR)."""
    if job.get('layout') == 'showcase' or job.get('kind') in ('famitsu', 'breaking'):
        return []
    starts, end = _timeline(job)
    if not starts:
        return []
    persist = _persist_head_spans(job, starts, end)
    out, n = [], 0
    for g in job.get('lines') or []:
        try:
            a, texts = int(g[0]), g[2]
        except (TypeError, ValueError, IndexError):
            continue
        tx = [t for t, _ in _texts(texts)]
        if not tx or a >= len(starts):
            n += len(tx)
            continue
        t0 = starts[a] + (0.25 if a else 3.6)
        n += 1
        if t0 < HEAD_CLEAR - 0.005 and not any(p <= t0 < q for p, q in persist):
            need = HEAD_CLEAR - t0 + 0.01
            if a:
                fix = (f'it enters at {t0:.2f} s, under the headline (which fades out from {HEAD_CLEAR:.2f} s); the '
                       f'earliest allowed start is {HEAD_CLEAR:.2f} s: lengthen shot{"s 0 to" if a > 1 else ""} '
                       f'{a - 1 if a > 1 else 0} by {need:.2f} s in all'
                       + (f' (shot 0 to at least {float(job["shots"][0][2]) + need:.2f} s)' if a == 1 else '')
                       + ', or start this group on a later shot')
            else:
                fix = f'it enters at {t0:.2f} s; the earliest allowed start is {HEAD_CLEAR:.2f} s'
            out.append({'where': f'line {n}', 'rule': 'head_overlap', 'text': tx[0].split('\n')[0], 'fix': fix})
        n += len(tx) - 1
    return out


def _tokens(text, keep=False):
    """Words for the spoken-paragraph match: no diacritics or tatweel, alef forms and ة/ى folded, punctuation and
    brackets dropped, a leading و or ف taken off (the line may start a clause the paragraph joins with و). With
    keep=True each word comes as (folded, as written)."""
    out = []
    for raw in re.sub(r'[«»"“”()\[\]،,:;.!؟?…\-–—|]', ' ', str(text)).split():
        t = TATWEEL_DIACRITICS.sub('', raw)
        w = re.sub('[إأآٱ]', 'ا', t).replace('ة', 'ه').replace('ى', 'ي').lower()
        if len(w) > 1 and w[0] in 'وف' and (len(w) > 2 and ARABIC.match(w[1]) or re.match('[a-z0-9]', w[1])):
            w = w[1:]
        if not w or w in ('و', 'ف'):
            continue
        out.append((w, raw) if keep else w)
    return out


# Server fix (Mohammad, 25 Nov 2026, after the 24 to 25 Nov outage: «Mario Bros. Circuit 2» was split at "Bros." and the
# next line opened on "Circuit 2", so the Mario Kart World 1.9.0 slip was refused twice). A full stop is not a sentence end
# after a known abbreviation or a single Latin letter, nor when a lowercase letter, a digit or another Latin word follows a
# Latin word (the same name). A decimal or version number (1.9.0) has no space after its points and never splits.
ABBREV = {'bros', 'dr', 'st', 'no', 'vol', 'mr', 'mrs', 'ms', 'jr', 'sr', 'inc', 'ltd', 'co', 'corp', 'vs', 'ver', 'ep',
          'pt', 'feat', 'mt', 'ft', 'ave', 'approx', 'dept', 'est', 'fig', 'gen', 'lt', 'prof', 'rev', 'ed', 'eds', 'jan',
          'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec', 'u.s', 'e.g', 'i.e', 'etc'}
LATIN_TOKEN = re.compile(r'^[«"“(]*[A-Za-z0-9]')


def _sentence_end(t, i, j):
    """True when the marks t[i:j] end a sentence (see ABBREV above)."""
    if not t[i:j].startswith('.') or '.' != t[i:j][-1] and len(t[i:j]) > 1:
        return True
    prev = (re.search(r'(\S+)$', t[:i]) or [None, ''])[1]
    nxt = (re.match(r'\s*(\S+)', t[j:]) or [None, ''])[1]
    pw = re.sub(r'^[«"“(]+', '', prev).lower()
    if re.fullmatch(r'[A-Za-z]', pw) or pw in ABBREV:
        return False
    if nxt and (re.match(r'[«"“(]*[a-z0-9]', nxt)):
        return False
    if nxt and LATIN_TOKEN.match(prev) and LATIN_TOKEN.match(nxt):
        return False
    return True


def split_sentences(text, keep=False):
    """The paragraph cut into sentences at . ! ? or ؟ followed by a space or the end, never inside a name or an
    abbreviation (_sentence_end). keep=True keeps each sentence's closing marks."""
    t, out, start = str(text or ''), [], 0
    for m in SENT_END.finditer(t):
        if not _sentence_end(t, m.start(), m.end()):
            continue
        piece = t[start:m.end() if keep else m.start()].strip()
        if piece:
            out.append(piece)
        start = m.end()
    rest = t[start:].strip()
    if rest:
        out.append(rest)
    return out


def spoken_sentences(text):
    """The paragraph's sentences: ended by . ! ? or ؟, each at least two words (split_sentences: never inside a name)."""
    parts = [p.strip() for p in split_sentences(text) if p.strip()]
    return [p for p in parts if len(p.split()) >= 2]


def spoken_problems(job):
    """The spoken paragraph exists (2 to 3 sentences, Arabic first) and the lines, in order, are that paragraph."""
    if job.get('kind') == 'famitsu':
        return []
    lines = [t for g in (job.get('lines') or []) if isinstance(g, (list, tuple)) and len(g) > 2 for t, _ in _texts(g[2])]
    if not lines:
        return []
    sp = job.get('spoken')
    if not isinstance(sp, str) or not sp.strip():
        return [{'where': 'spoken', 'rule': 'spoken_missing', 'text': '',
                 'fix': 'write "spoken": the story as one paragraph of 2 to 3 Arabic sentences told to a friend, then cut '
                        'the lines from it in order (Mohammad, 15 Nov 2026)'}]
    out = []
    sents = spoken_sentences(sp)
    if not SPOKEN_MIN <= len(sents) <= SPOKEN_MAX:
        out.append({'where': 'spoken', 'rule': 'spoken_missing', 'text': sp[:80],
                    'fix': f'{len(sents)} sentence{"" if len(sents) == 1 else "s"}: the paragraph is {SPOKEN_MIN} to '
                           f'{SPOKEN_MAX} sentences, each ending on a full stop'})
    if not _first_ok(sp):
        out.append({'where': 'spoken', 'rule': 'latin_first', 'text': sp[:40],
                    'fix': 'open the paragraph on an Arabic word'})
    para = _tokens(sp)
    k = 0
    for i, line in enumerate(lines, 1):
        words = _tokens(line, keep=True)
        miss, j = [], k
        for w, raw in words:
            try:
                j = para.index(w, j) + 1
            except ValueError:
                miss.append((w, raw))
        if miss:
            back = [raw for w, raw in miss if w in para[:k]]
            miss = [raw for _, raw in miss]
            why = ('these words come earlier in the paragraph than the line before: ' + ' '.join(back)) if back else \
                  ('these words are not in the paragraph: ' + ' '.join(miss))
            out.append({'where': f'line {i}', 'rule': 'spoken_order', 'text': line.replace('\n', ' '),
                        'fix': why + '; the lines, read in order, are the spoken paragraph (a word may be left out, '
                               'none added): rewrite the line from the paragraph, or the paragraph to carry it'})
        else:
            k = j
    return out


def check(job):
    """Every font-free text problem in the job, as a list of findings (empty when clean)."""
    out = []
    if job.get('kind') == 'famitsu':
        return out
    head = job.get('headline')
    if head is not None:
        _text_rules('headline', head, out)
        mc = re.match(r'^\s*(' + '|'.join(CHIP_WORDS) + r')\s*[:：]', str(head))
        chip = str(job.get('label') or job.get('chip') or '').strip()
        if mc and (mc.group(1) == chip or mc.group(1) == 'حصري'):   # the server drops it when the rest opens on Arabic
            out.append({'where': 'headline', 'rule': 'chip_word', 'text': head,
                        'fix': f'the chip already says «{mc.group(1)}»: drop «{mc.group(1)}:» and open the headline on an '
                               'Arabic word (22 Nov 2026)'})
        parts = str(head).split('\n')
        latin = bool(re.search('[A-Za-z]', str(head)))
        if len(parts) > HEAD_MAX_LINES:                 # fix() joins and shortens these (25 Nov 2026)
            out.append({'where': 'headline', 'rule': 'headline_long', 'text': head, 'hard': True,
                        'fix': f'{len(parts)} lines: at most {HEAD_MAX_LINES}; the server shortens it (textrules.fix)'})
        elif len(parts) > HEAD_LINES:
            out.append({'where': 'headline', 'rule': 'headline_long', 'text': head,
                        'fix': f'{len(parts)} lines: the live path sets three lines at 60 px (estimate)'})
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
    for where, text in _all_texts(job):
        house_words(where, text, out, job)
    out += head_problems(job)
    out += game_name_problems(job)                      # Burning Sword case, 19 Nov 2026 (hard)
    out += unknown_name_problems(job)
    out += [f for f in spoken_problems(job) if not (job.get('_gate_spoken') and f['rule'] == 'spoken_missing')]
    return out


# ---------------------------------------------------------------------------------------------------------------
# Burning Sword case (Mohammad, 19 Nov 2026): hard stops under "unreadable text". The 19 Nov Reel's headline read
# «لعبة سيوف ووشيا\nوصلت للوصول المبكر» with no game name, and its line wrote the game in Arabic letters, «بيرنينغ سورد
# (Burning Sword)», a pair names-ar did not know. Three rules, each hard:
#   game_headline     a story about one game (the story's "game" field, or the job's, is one name): the headline carries
#                     that name exactly as written there (line breaks read as spaces)
#   arabic_game_name  the game's name written in Arabic letters, on screen or in the post texts: a «Arabic (Latin)» pair
#                     whose Latin is the game's name or part of it, or Arabic words whose consonants spell the name's
#                     words in order (two consecutive words for a name of two words or more; one word of four
#                     consonants or more for a one-word name)
#   name_unknown      a «Arabic (Latin)» pair in the headline or a line whose Latin is not in newsroom/names-ar.md or the
#                     glossary (the slip's "name not in names-ar" flag, now a stop on screen)
STOP_WORDS = {'the', 'of', 'a', 'an', 'and', 'in', 'on', 'to', 'for', 'edition', 'remastered', 'remake', 'deluxe', 'ii',
              'iii', 'iv', 'vi', 'vii', 'viii', 'ix', 'xi', 'xii', 'hd', 'dx', 'ex'}
LAT_CLASS = {'b': 'b', 'p': 'b', 't': 't', 'd': 'd', 's': 's', 'z': 's', 'x': 'ks', 'c': 'k', 'k': 'k', 'q': 'k',
             'g': 'k', 'j': 'k', 'f': 'f', 'v': 'f', 'l': 'l', 'm': 'm', 'n': 'n', 'r': 'r'}
AR_CLASS = {'ب': 'b', 'پ': 'b', 'ت': 't', 'ط': 't', 'ث': 's', 'د': 'd', 'ض': 'd', 'ذ': 'd', 'س': 's', 'ص': 's', 'ز': 's',
            'ش': 's', 'ظ': 'd', 'ك': 'k', 'ق': 'k', 'غ': 'k', 'ج': 'k', 'گ': 'k', 'خ': 'k', 'ف': 'f', 'ڤ': 'f',
            'ل': 'l', 'م': 'm', 'ن': 'n', 'ر': 'r'}
AR_WORD = re.compile('[\u0621-\u064A\u0640\u064B-\u0652\u06A4\u06AF\u067E]+')
AR_PREFIX = ('وال', 'بال', 'لل', 'فال', 'ال', 'و', 'ب', 'ل', 'ف')
ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))


def _squash(seq):
    out = []
    for ch in seq:
        if not out or out[-1] != ch:
            out.append(ch)
    return ''.join(out)


def lat_skel(word):
    w = re.sub('[^a-z]', '', word.lower())
    w = w.replace('ph', 'f').replace('ck', 'k').replace('sh', 's').replace('ch', 's').replace('th', 's')
    return _squash(''.join(LAT_CLASS.get(ch, '') for ch in w))


def ar_skel(word):
    w = TATWEEL_DIACRITICS.sub('', word)
    return _squash(''.join(AR_CLASS.get(ch, '') for ch in w))


def _ar_variants(word):
    """The word's skeleton, and the skeleton with a common prefix taken off."""
    out = {ar_skel(word)}
    for p in AR_PREFIX:
        if word.startswith(p) and len(word) - len(p) >= 3:
            out.add(ar_skel(word[len(p):]))
    return out


def game_short_of(job):
    """Short forms the story declares for its game ("game_short": "GTA VI" or a list), from the job or the story file."""
    g = job.get('game_short')
    if g is None and job.get('story'):
        try:
            s = json.load(open(__import__('os').path.join(ROOT, 'newsroom', 'stories', str(job['story']) + '.json'),
                               encoding='utf-8'))
            g = s.get('game_short')
        except (OSError, ValueError):
            g = None
    g = [g] if isinstance(g, str) else (g or [])
    return [x.strip() for x in g if isinstance(x, str) and len(x.strip()) >= 3]


def game_of(job):
    """The one game a story is about: the job's "game", else its story file's; None for a list or several games."""
    g = job.get('game')
    if g is None and job.get('story'):
        try:
            s = json.load(open(__import__('os').path.join(ROOT, 'newsroom', 'stories', str(job['story']) + '.json'),
                               encoding='utf-8'))
            g = s.get('game')
        except (OSError, ValueError):
            g = None
    if isinstance(g, list):
        g = g[0] if len(g) == 1 else None
    return g.strip() if isinstance(g, str) and g.strip() else None


def _norm_space(t):
    return ' '.join(str(t or '').split())


def game_name_problems(job, game=None):
    """game_headline and arabic_game_name findings for one job (hard)."""
    game = game or game_of(job)
    out = []
    if not game or job.get('kind') == 'famitsu' or job.get('template') == 'list':
        return out
    head = job.get('headline')
    if head is not None and not any(n in _norm_space(head) for n in [game] + game_short_of(job)):
        out.append({'where': 'headline', 'rule': 'game_headline', 'text': _norm_space(head), 'hard': True,
                    'fix': f'a story about one game names it in the headline exactly as in the story\'s "game" field: '
                           f'«{game}» (an Arabic word first, then the name; break the line before the name if it is long), '
                           'or a short form the story declares in "game_short" (for example "GTA VI")'})
    words = [w for w in re.findall('[A-Za-z0-9]+', game) if w.lower() not in STOP_WORDS]
    skels = [lat_skel(w) for w in words]
    keys = [(w, k) for w, k in zip(words, skels) if len(k) >= 3]
    texts = list(_all_texts(job))
    for k_, v in (job.get('post_texts') or {}).items():
        if isinstance(v, str):
            texts.append((f'texts {k_}', v))
    gl = game.lower()
    try:
        import slip as _S
        pairs = _S.BRACKET
    except Exception:                                   # noqa: BLE001
        pairs = None
    for where, text in texts:
        text = str(text or '')
        hit = None
        if pairs is not None:
            for ar, la in pairs.findall(text):
                lal = la.strip().lower()
                if lal and (lal in gl or gl in lal or any(w.lower() in lal.split() for w, _ in keys)):
                    hit = f'{ar.strip()} ({la.strip()})'
                    break
        if hit is None and keys:
            toks = AR_WORD.findall(text)
            vs = [_ar_variants(t) for t in toks]
            need = 2 if len(keys) >= 2 else 1
            for i in range(len(toks)):
                if need == 1:
                    if len(keys[0][1]) >= 4 and keys[0][1] in vs[i]:
                        hit = toks[i]
                        break
                else:
                    for j in range(len(keys) - 1):
                        if i + 1 < len(toks) and keys[j][1] in vs[i] and keys[j + 1][1] in vs[i + 1]:
                            hit = toks[i] + ' ' + toks[i + 1]
                            break
                    if hit:
                        break
        if hit:
            out.append({'where': where, 'rule': 'arabic_game_name', 'text': hit, 'hard': True,
                        'fix': f'game names stay in Latin letters, as the publisher writes them: «{game}», never in '
                               'Arabic letters (names-ar rule; Burning Sword case, 19 Nov 2026)'})
    return out


def unknown_name_problems(job, table=None):
    """name_unknown: a «Arabic (Latin)» pair in the headline or a line that names-ar and the glossary do not list."""
    try:
        import slip as _S
    except Exception:                                   # noqa: BLE001
        return []
    table = _S._names_table() if table is None else table
    if not table:                                       # names-ar not on this checkout: never flag every name
        print('text check: names-ar.md not found; name_unknown not checked', flush=True)
        return []
    out = []
    for where, text in _all_texts(job):
        if not (where == 'headline' or where.startswith('line ')):
            continue
        for ar, la in _S.BRACKET.findall(str(text or '')):
            key = la.strip().lower()
            if key and key not in table:
                out.append({'where': where, 'rule': 'name_unknown', 'text': f'{ar.strip()} ({la.strip()})', 'hard': True,
                            'fix': f'«{la.strip()}» is not in newsroom/names-ar.md: add it there (Arabic form agreed) before '
                                   'the render, or, for a game, write it in Latin letters only'})
    return out


def _all_texts(job):
    """Every text a job puts on screen or in a post: headline, lines, strip, credits, card texts, spoken, post texts."""
    yield 'headline', job.get('headline') or ''
    n = 0
    for grp in job.get('lines') or []:
        if isinstance(grp, (list, tuple)) and len(grp) >= 3:
            for text, _ in _texts(grp[2]):
                n += 1
                yield f'line {n}', text
    for i, it in enumerate(job.get('strip') or [], 1):
        if isinstance(it, (list, tuple)):
            for x in it[:2]:
                if isinstance(x, str):
                    yield f'strip {i}', x
    for i, c in enumerate(job.get('credits') or [], 1):
        if isinstance(c, (list, tuple)) and len(c) > 2:
            yield f'credit {i}', c[2]
    for i, g in enumerate(job.get('gfx') or [], 1):
        if isinstance(g, dict):
            for k, v in g.items():
                if isinstance(v, str):
                    yield f'gfx {i} {k}', v
    if job.get('spoken'):
        yield 'spoken', job['spoken']
    for k, v in (job.get('texts') or {}).items():
        if isinstance(v, str):
            yield f'texts {k}', v


def hard(findings):
    """Findings that stop: everything except the headline-length estimates (the server's font check decides those)."""
    return [f for f in findings if f['rule'] != 'headline_long' or f.get('hard')]


PCT_WORD = ' بالمئة'


def _fix_text(t):
    """Mechanical fixes only (item H): a space after an Arabic prefix glued to a Latin word or digit, a percent sign
    spelt out, a plus sign dropped. Returns (new text, [what changed])."""
    out, ch = t, []
    new = re.sub(r'([\u0621-\u064A\u0640])([A-Za-z0-9])', r'\1 \2', out)
    if new != out:
        ch.append('space after a glued prefix'); out = new
    new = re.sub(r'(\d)\s*[%٪]', lambda m: m.group(1) + PCT_WORD, out)
    new = re.sub(r'[%٪]\s*(\d+(?:[.,]\d+)?)', lambda m: m.group(1) + PCT_WORD, new)
    if new != out:
        ch.append('percent sign spelt out'); out = new
    new = re.sub(r'(?<=[0-9A-Za-z])\+|\+(?=[0-9A-Za-z])', '', out)
    if new != out:
        ch.append('plus sign dropped'); out = new
    return out, ch


def latin_unknown_names(text, table):
    """Names rule correction (Mohammad and advisor, 21 Nov 2026): a «Arabic (Latin)» pair whose Latin names-ar and the
    glossary do not list is written in Latin letters as given, never refused, so no unvetted Arabic spelling goes on
    screen. The Arabic form is the last words before the bracket, as many as the Latin has (lead words such as «صحيفة»
    or «موقع» stay). A pair that opens a visual line keeps its Arabic, so the line still opens on an Arabic word.
    Returns (new text, [latin names rewritten], [latin names left])."""
    import slip as _S
    out, done, left = [], [], []
    pos = 0
    flat = text.replace('\n', ' ')                      # a wrap inside the name («ذي\nإندبندنت (The Independent)»)
    for m in _S.BRACKET.finditer(flat):
        ar, la = m.group(1), m.group(2).strip()
        if la.lower() in table:
            continue
        words = ar.split()
        k = max(1, min(len(words), len(la.split()), 3))
        while k > 1 and (words[-k] in _S.NAME_LEAD or words[-k].startswith('ال')):   # a role or lead word stays
            k -= 1
        span = flat[m.start(1):m.end(1)]
        cut = 0
        for _ in range(len(words) - k):                  # skip the words before the name, as the original spaces them
            cut = span.index(' ', cut) + 1
            while span[cut:cut + 1] == ' ':
                cut += 1
        start = m.start(1) + cut
        line_start = text.rfind('\n', 0, start) + 1
        if not text[line_start:start].strip():          # the pair opens the line: keep its Arabic, flag it
            left.append(la)
            continue
        out.append(text[pos:start] + la)
        pos = m.end()
        done.append(la)
    out.append(text[pos:])
    return ''.join(out), done, left


CHIP_WORDS = ('تقرير', 'رسمي', 'حصري', 'عاجل', 'شائعة', 'تسريب', 'جديد', 'تحديث', 'تأجيل')


def headline_without_chip(job):
    """People Reels without the person (Mohammad, 22 Nov 2026, item 4): the headline never repeats the chip word. A
    leading «تقرير:», «رسمي:», «حصري:» (and the other chip words) is dropped when the job's chip says it; «حصري» goes
    whenever it leads, since it is never a chip of its own. None when nothing changes."""
    head = job.get('headline')
    if not isinstance(head, str):
        return None
    chip = str(job.get('label') or job.get('chip') or '').strip()
    m = re.match(r'^\s*(' + '|'.join(CHIP_WORDS) + r')\s*[:：]\s*', head)
    if not m or (m.group(1) != chip and m.group(1) != 'حصري'):
        return None
    rest = head[m.end():]
    first = rest.strip().lstrip('«"“')[:1]
    if not first or not re.match('[\u0621-\u064A]', first):   # it would open on a Latin word or a digit (a hard stop):
        return None                                            # left for the writer (chip_word in the text check)
    return rest


def headline_with_game(job):
    """The headline with the game's name put in (Names rule correction, 21 Nov 2026): a one-game story whose headline does
    not name it gets «لعبة <short form or name>» as its first line; the type steps down (reel.head_layer's soft path,
    three lines down to 60 px). None when the headline already names it or the story is not about one game."""
    if job.get('kind') == 'famitsu' or job.get('template') == 'list':
        return None
    game = game_of(job)
    head = job.get('headline')
    if not game or not isinstance(head, str):
        return None
    names = [game] + game_short_of(job)
    if any(n in _norm_space(head) for n in names):
        return None
    short = (game_short_of(job) or [game])[0]
    return f'لعبة {short}\n{head.strip()}'

# ----------------------------------------------------------------------------------- autofix, never a refusal (25 Nov 2026)
HEAD_CHARS_60 = 36             # estimate at the 60 px floor: about 36 characters a line with a Latin name
HEAD_MAX_LINES = 3             # the live path sets a headline on three lines at 60 px at most
NEWS_WORDS = ('تحديث', 'تأجيل', 'موعد', 'سعر', 'إطلاق', 'صدور', 'تصدر', 'متوفرة', 'عرض', 'إعلان', 'توسعة', 'إضافة',
              'خصم', 'مجانا', 'مجانًا', 'مجانية', 'تسريب', 'موسم', 'مبيعات', 'نسخة', 'إلغاء', 'نسخ')
PLATFORM_RE = re.compile(r'\s*(?:على|لجهاز|لأجهزة|عبر|في)\s+(?:متجر\s+)?(?:(?:Nintendo\s+)?Switch(?:\s*2)?|PS[45]|'
                         r'PlayStation\s*[45]?|Xbox(?:\s+Series\s+X\|?S)?|Steam|PC|الحاسب|الحاسوب|سويتش(?:\s*2)?)'
                         r'(?:\s*(?:،|و)\s*(?:(?:Nintendo\s+)?Switch(?:\s*2)?|PS[45]|Xbox(?:\s+Series\s+X\|?S)?|Steam|PC|الحاسب))*')
SOURCE_RE = re.compile(r'\s*[،,]?\s*(?:حسب|بحسب|وفق|وفقا ل|نقلا عن|عن)\s+[^\n،,]*$')


def _visual_ok(line):
    return _first_ok(line)


def arabic_first(text, names=()):
    """Every visual line opens on an Arabic word, by rewrapping and never by refusing (Mohammad, 25 Nov 2026):
    1. a later line that opens on a Latin word takes its leading Latin run back onto the line before (the break moves
       to the next Arabic word);
    2. a first line (or a line that cannot be rewrapped) that opens on the game's name gets «لعبة» before it;
    3. otherwise the first Arabic word after the Latin run moves to the front of the line («Warhammer تصدر ...» becomes
       «تصدر Warhammer ...»).
    Returns (text, [what changed])."""
    if not isinstance(text, str) or not text.strip():
        return text, []
    lines, what = text.split('\n'), []
    i = 1
    while i < len(lines):
        if not _visual_ok(lines[i]) and _visual_ok(lines[i - 1]):
            w = lines[i].split()
            k = next((n for n, x in enumerate(w) if ARABIC.match(x.lstrip(LEAD)[:1] or 'a')), None)
            if k is None:                               # nothing Arabic left: join the two lines
                lines[i - 1] = lines[i - 1].rstrip() + ' ' + lines[i].strip()
                del lines[i]
                what.append('a Latin-only line joined to the line before')
                continue
            lines[i - 1] = lines[i - 1].rstrip() + ' ' + ' '.join(w[:k])
            lines[i] = ' '.join(w[k:])
            what.append('rewrapped: the line break moved so the line opens on an Arabic word')
        i += 1
    for i, ln in enumerate(lines):
        if _visual_ok(ln):
            continue
        body = ln.strip()
        nm = next((n for n in names if n and body.lstrip(LEAD).startswith(n)), None)
        if nm:
            lines[i] = 'لعبة ' + body
            what.append('«لعبة» put before the game name')
            continue
        w = body.split()
        k = next((n for n, x in enumerate(w) if ARABIC.match(x.lstrip(LEAD)[:1] or 'a')), None)
        if k:
            lines[i] = ' '.join([w[k]] + w[:k] + w[k + 1:])
            what.append(f'the Arabic word «{w[k]}» moved to the front of the line')
        elif names:
            lines[i] = 'لعبة ' + body
            what.append('«لعبة» put before a Latin-only line')
    return '\n'.join(lines), what


def carry_across(texts, join=True):
    """A list of on-screen lines, in order, where no line opens on a Latin word: the last word of the line before moves
    down with it (so «لعبة» stays with its game name: «تدعم لعبة» | «Ghost of Tsushima ...» becomes «تدعم» merged into
    «تدعم لعبة Ghost of Tsushima ...»); a line left with fewer than two words joins the next. No word is added or
    dropped (the spoken-order check reads the same words). Returns (texts, [what changed]). 25 Nov 2026."""
    out, what = [t for t in texts], []
    k = 1
    while k < len(out):
        nxt = out[k]
        if nxt is None or _first_ok(nxt.split('\n')[0]):
            k += 1
            continue
        prev = (out[k - 1] or '').replace('\n', ' ').split()
        if not prev:
            k += 1
            continue
        if len(prev) <= 2 and join:                     # a line of one or two words joins the next whole
            out[k] = ' '.join(prev) + ' ' + nxt.replace('\n', ' ')
            del out[k - 1]
            what.append('a short line joined the next, which opened on a Latin word')
            continue
        if len(prev) == 1:                              # the count must hold (render): the Latin run goes up instead
            w = nxt.replace('\n', ' ').split()
            a = next((n for n, x in enumerate(w) if ARABIC.match(x.lstrip(LEAD)[:1] or 'a')), None)
            if a:
                out[k - 1] = ' '.join(prev + w[:a])
                out[k] = ' '.join(w[a:])
                what.append('the Latin run moved up to the line before')
            k += 1
            continue
        out[k - 1] = ' '.join(prev[:-1])
        out[k] = prev[-1] + ' ' + nxt.replace('\n', ' ')
        what.append(f'«{prev[-1]}» moved down so the line opens on an Arabic word')
        k += 1
    return out, what


_PUNCT = '،,.:;؛«»()"\'' + chr(0x061F)


def _bare(w):
    return w.strip(_PUNCT)


def keep_names(texts, names=None):
    """A multi-word Arabic name is never split across two on-screen lines (Mohammad's bank, 25 Nov 2026: Elden Ring
    Nightreign read «... من فروم» | «سوفتوير (FromSoftware)، ...»). The names are the Arabic forms of names-ar.md and the
    glossary, plus every «Arabic (Latin)» pair in the lines themselves; the split part of a name moves down to the next
    line. A line left with fewer than two words joins the next. No word is added or dropped. Returns (texts, what)."""
    if names is None:
        try:
            import slip as _S
            names = set(_S._names_table().values())
            joined = ' '.join(str(t or '').replace('\n', ' ') for t in texts)
            names |= {ar.strip() for ar, _ in _S.BRACKET.findall(joined)}
        except Exception:                               # noqa: BLE001
            names = set()
    forms = sorted({tuple(_bare(w) for w in str(n).split() if _bare(w)) for n in names}, key=len, reverse=True)
    forms = [f for f in forms if len(f) >= 2]
    out, what = [t for t in texts], []
    for k in range(1, len(out)):
        if out[k - 1] is None or out[k] is None:
            continue
        prev, nxt = out[k - 1].replace('\n', ' ').split(), out[k].replace('\n', ' ').split()
        if not prev or not nxt:
            continue
        moved = 0
        for f in forms:
            for cut in range(1, len(f)):
                head, tail = f[:cut], f[cut:]
                pw = [_bare(w) for w in prev[-cut:]]
                nw = [_bare(w) for w in nxt[:len(tail)]]
                # a prefix glued on the first word (من، و، ب، ل) still counts: «وفروم»
                if len(pw) == cut and nw == list(tail) and (pw[1:] == list(head[1:])) and (
                        pw[0] == head[0] or (pw[0].endswith(head[0]) and len(pw[0]) - len(head[0]) <= 2)):
                    moved = cut
                    break
            if moved:
                break
        if not moved:
            continue
        if len(prev) - moved < 2:                       # too little left: the whole line joins the next
            out[k] = ' '.join(prev + nxt)
            out[k - 1] = ''
            what.append('a short line joined the next to keep a name whole')
            continue
        out[k - 1] = ' '.join(prev[:-moved])
        out[k] = ' '.join(prev[-moved:] + nxt)
        what.append(f'«{" ".join(prev[-moved:])}» moved down to keep the name whole')
    if any(t == '' for t in out):
        out = [t for t in out if t != '']
    return out, what


def _est_lines(head, per=HEAD_CHARS_60):
    parts = [p for p in str(head).split('\n') if p.strip()]
    return sum(max(1, -(-len(p) // per)) for p in parts)


def shorten_headline(head, names=()):
    """A headline too long for three lines at 60 px is shortened, never refused (Mohammad, 25 Nov 2026): the platform
    and source words go first; if it is still too long, it becomes the news word and the game's name («تحديث Mario Kart
    World»). Returns (headline, [what changed])."""
    if not isinstance(head, str):
        return head, []
    what, h = [], head
    if len([p for p in h.split('\n') if p.strip()]) > HEAD_MAX_LINES:
        h = ' '.join(p.strip() for p in h.split('\n') if p.strip())
        what.append(f'more than {HEAD_MAX_LINES} lines joined')
    if _est_lines(h) <= HEAD_MAX_LINES and len(h.split('\n')) <= HEAD_MAX_LINES:
        return h, what
    for rx, why in ((PLATFORM_RE, 'platform words dropped'), (SOURCE_RE, 'source words dropped')):
        new = '\n'.join(re.sub(r'\s{2,}', ' ', rx.sub('', p)).strip() for p in h.split('\n'))
        new = '\n'.join(p for p in new.split('\n') if p.strip())
        if new != h and new.strip():
            h = new
            what.append(why)
        if _est_lines(h) <= HEAD_MAX_LINES:
            return h, what
    flat = ' '.join(h.split())
    word = next((w for w in flat.split() if w.strip('،,.:') in NEWS_WORDS), None) or 'جديد'
    game = next((n for n in names if n), None)
    if game:
        h = f'{word.strip("،,.:")} {game}'
        what.append('cut to the news word and the game name')
    else:
        ws, out = flat.split(), []
        for w in ws:
            if len(' '.join(out + [w])) > HEAD_CHARS_60 * HEAD_MAX_LINES:
                break
            out.append(w)
        h = ' '.join(out)
        what.append('cut to the words that fit three lines')
    return h, what



def fix(job):
    """The job with its mechanical text faults fixed, and [(where, before, after, what)]. Since 25 Nov 2026 (Mohammad,
    after the 24 to 25 Nov outage) it also rewraps a line that opens on a Latin word (arabic_first) and shortens a
    headline too long for three lines at 60 px (shorten_headline): those are fixed, never refused. Reading time is the
    render's (the shot under a short line grows)."""
    import copy
    j, changes = copy.deepcopy(job), []

    def one(where, t):
        new, ch = _fix_text(t)
        if ch:
            changes.append({'where': where, 'before': t, 'after': new, 'what': ', '.join(ch)})
        return new
    if isinstance(j.get('headline'), str):
        j['headline'] = one('headline', j['headline'])
    h = headline_without_chip(j)                         # the chip word is not repeated (22 Nov 2026)
    if h:
        changes.append({'where': 'headline', 'before': j['headline'], 'after': h, 'what': 'chip word dropped from the headline'})
        j['headline'] = h
    h = headline_with_game(j)                            # the game's name put in, never a refusal (21 Nov 2026)
    if h:
        changes.append({'where': 'headline', 'before': j['headline'], 'after': h, 'what': 'game name put in the headline'})
        j['headline'] = h
    try:                                                 # unknown names written in Latin letters (21 Nov 2026)
        import slip as _S
        table = _S._names_table()
    except Exception:                                    # noqa: BLE001
        table = {}
    review = list(j.get('names_to_review') or [])
    if table:
        def lat(where, t):
            new, done, left = latin_unknown_names(t, table)
            for la in done + left:
                if la not in review:
                    review.append(la)
            if new != t:
                changes.append({'where': where, 'before': t, 'after': new,
                                'what': 'names not in names-ar written in Latin: ' + ', '.join(done)})
            return new
        if isinstance(j.get('headline'), str):
            j['headline'] = lat('headline', j['headline'])
        if isinstance(j.get('spoken'), str):
            j['spoken'] = lat('spoken', j['spoken'])
        for grp in j.get('lines') or []:
            if isinstance(grp, list) and len(grp) >= 3:
                for k, x in enumerate(grp[2]):
                    if isinstance(x, str):
                        grp[2][k] = lat('line', x)
                    elif isinstance(x, list) and x and isinstance(x[0], str):
                        x[0] = lat('line', x[0])
    if review:
        j['names_to_review'] = review
    names = [n for n in ([game_of(j)] + game_short_of(j)) if n]       # 25 Nov 2026: autofix, never a refusal
    if isinstance(j.get('headline'), str):
        h, w = shorten_headline(j['headline'], game_short_of(j) + ([game_of(j)] if game_of(j) else []))
        if w:
            changes.append({'where': 'headline', 'before': j['headline'], 'after': h, 'what': '; '.join(w)})
            j['headline'] = h
        h, w = arabic_first(j['headline'], names)
        if w:
            changes.append({'where': 'headline', 'before': j['headline'], 'after': h, 'what': '; '.join(w)})
            j['headline'] = h
    slots = []                                           # every line's text, in order, for the cross-line carry
    for grp in j.get('lines') or []:
        if isinstance(grp, list) and len(grp) >= 3:
            for k, x in enumerate(grp[2]):
                if isinstance(x, str) or (isinstance(x, list) and x and isinstance(x[0], str)):
                    slots.append((grp, k))
    texts = [g[2][k] if isinstance(g[2][k], str) else g[2][k][0] for g, k in slots]
    carried, cw = carry_across(texts, join=False)
    kept, kw = keep_names(carried)
    if kw and len(kept) == len(carried):
        carried, cw = kept, cw + kw
    if cw and len(carried) == len(texts):
        for (g, k), t_old, t_new in zip(slots, texts, carried):
            if t_new != t_old:
                try:                                     # rewrap at the line's own size (linecut breaks phrases right)
                    import linecut as _LC
                    sz = g[2][k][1].get('size') if isinstance(g[2][k], list) and len(g[2][k]) > 1 \
                        and isinstance(g[2][k][1], dict) else None
                    t_new = _LC.wrap(t_new, sz or _LC.SIZES[0])
                except Exception:                        # noqa: BLE001
                    pass
                changes.append({'where': 'lines', 'before': t_old, 'after': t_new, 'what': '; '.join(cw)})
                if isinstance(g[2][k], str):
                    g[2][k] = t_new
                else:
                    g[2][k][0] = t_new
    m = 0
    for grp in j.get('lines') or []:
        if not isinstance(grp, list) or len(grp) < 3:
            continue
        for k, x in enumerate(grp[2]):
            m += 1
            t0 = x if isinstance(x, str) else (x[0] if isinstance(x, list) and x and isinstance(x[0], str) else None)
            if t0 is None:
                continue
            new, w = arabic_first(t0, names)
            if w:
                changes.append({'where': f'line {m}', 'before': t0, 'after': new, 'what': '; '.join(w)})
                if isinstance(x, str):
                    grp[2][k] = new
                else:
                    x[0] = new
    for i, c in enumerate(j.get('credits') or [], 1):
        if isinstance(c, list) and len(c) > 2 and isinstance(c[2], str):
            new, w = arabic_first(c[2], names)
            if w:
                changes.append({'where': f'credit {i}', 'before': c[2], 'after': new, 'what': '; '.join(w)})
                c[2] = new
    n = 0
    for grp in j.get('lines') or []:
        if not isinstance(grp, list) or len(grp) < 3:
            continue
        for k, x in enumerate(grp[2]):
            n += 1
            if isinstance(x, str):
                grp[2][k] = one(f'line {n}', x)
            elif isinstance(x, list) and x and isinstance(x[0], str):
                x[0] = one(f'line {n}', x[0])
    for i, it in enumerate(j.get('strip') or [], 1):
        if isinstance(it, list) and it:
            if isinstance(it[0], str):
                it[0] = one(f'strip {i}', it[0])
            if len(it) > 1 and isinstance(it[1], str):
                it[1] = one(f'strip {i}', it[1])
    for i, c in enumerate(j.get('credits') or [], 1):
        if isinstance(c, list) and len(c) > 2 and isinstance(c[2], str):
            c[2] = one(f'credit {i}', c[2])
    for i, g in enumerate(j.get('gfx') or [], 1):
        if isinstance(g, dict):
            for k in ('title', 'headline', 'line', 'note', 'caption', 'label'):
                if isinstance(g.get(k), str):
                    g[k] = one(f'gfx {i} {k}', g[k])
    return j, changes


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
    if a[0] == 'fix':                         # textrules.py fix <job> <changes.json>: rewrites the job in place
        job = json.load(open(a[1], encoding='utf-8'))
        import autoshots
        autoshots.expand(job)                # "shots": "auto" (gates-fix C): lengths only, no footage
        new, ch = fix(job)
        if ch:
            json.dump(new, open(a[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if len(a) > 2:
            json.dump(ch, open(a[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        for c in ch:
            print(f"autofix: {c['where']}: {c['what']}: {c['before']!r} -> {c['after']!r}")
        print(f'autofix: {len(ch)} change(s)')
        sys.exit(0 if ch else 3)
    job = json.load(open(a[0], encoding='utf-8'))
    fs = check(job)
    print(report(fs))
    if '--json' in a:
        json.dump(fs, open(a[a.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(1 if hard(fs) else 0)
