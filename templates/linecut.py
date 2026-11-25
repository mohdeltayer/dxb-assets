#!/usr/bin/env python3
"""Story lines are sentences, not drip-fed pieces (Mohammad, 23 Nov 2026).

Case: a viewer asked «ليش تكتب كلمة بكلمة وتتأخر» under the Rayman Legends Retold Reel. The slip lane had cut two spoken
sentences into nine on-screen pieces of 2 to 5 words, one per pair of shots, and split «نينتيندو إفريثينغ» across two
screens. The rules, for every template:
1. A line is a full sentence or a full clause, up to two visual lines. Cut only at the end of a sentence or at a comma;
   never inside a name (an Arabic name with its Latin in brackets), a Latin run (Switch 2, Rayman Legends Retold), a number
   with its unit (23.4 غيغابايت) or a phrase (a preposition or particle stays with the word after it).
2. Lines are not tied to shots: one line stays up across as many shots as its reading time needs.
3. A Reel has 3 to 6 lines; more pieces are packed into sentences before the render (the type steps 54, 48, 44 px down
   before a paragraph is called too long).
4. A line under 5 words that is not the last is merged with the next.
5. Word-by-word reveal stays off, except the one key line a job asks for ("reveal").

    cut(spoken, headline=None)     -> (lines [(text, size)], problems)   the slip lane
    merge_job(job)                 -> [changes]                           the render's autofix, in place, for any job
"""
import re

ARABIC = re.compile('[ء-ي]')
LATIN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.:&\'+-]*[,.:;!?]?$|^\d[\d.,]*%?$')
NO_BREAK_AFTER = {'في', 'على', 'من', 'إلى', 'عن', 'مع', 'بعد', 'قبل', 'حتى', 'منذ', 'عبر', 'دون', 'بين', 'حول', 'لدى',
                  'عند', 'أو', 'و', 'ثم', 'التي', 'الذي', 'الذين', 'هما', 'هي', 'هو', 'لا', 'لم', 'لن', 'قد', 'أن', 'إن',
                  'كل', 'بعض', 'بسعر', 'بمستوى', 'نحو', 'موقع', 'شركة', 'استوديو', 'لعبة', 'ألعاب', 'سلسلة', 'جهاز',
                  'منصة', 'متجر', 'بحسب', 'حسب', 'وفق', 'ذكر', 'قال', 'قالت', 'أعلن', 'أعلنت', 'يبلغ', 'تبلغ', 'بلغ',
                  'بلغت', 'وهو', 'وهي', 'أكبر', 'أول', 'آخر'}
BASE_SIZE = 54
SIZES = (54, 48, 44, 40)
ROOM = 1080 - 170 - 96    # the line's width in px: ig_ar.SAFE_LEFT to the like column (reel.line_layer)
_FONTS = {}
BASE_CHARS = 30          # one visual line at 54 px (slip.LINE_CHARS); scales with the size
MIN_WORDS = 5
MIN_LINES, MAX_LINES = 3, 6


def chars_at(size):
    return int(BASE_CHARS * BASE_SIZE / size)


def _tokens(text):
    return [w for w in str(text or '').split() if w]


def units(text, soft=True):
    """Words grouped into pieces that never break: a name with its brackets, a Latin run, a number with its unit, and
    (soft=True, for cuts between on-screen lines) a particle with the word after it. Wrapping inside one line uses the
    hard units only."""
    w = _tokens(text)
    # 1. brackets: «(Nintendo Everything)» and the Arabic words of the name before it (as many as the Latin words, 3 at most)
    groups, i = [], 0
    while i < len(w):
        if w[i].startswith('('):
            j = i
            while j < len(w) and not w[j].rstrip('،,.:؛').endswith(')'):
                j += 1
            j = min(j, len(w) - 1)
            n = min(3, j - i + 1)
            take = []
            while groups and len(take) < n and ARABIC.match(groups[-1][-1]) and len(groups[-1]) == 1 and \
                    not groups[-1][0].endswith(('،', ',', '.')):
                take = groups.pop() + take
            groups.append(take + w[i:j + 1])
            i = j + 1
            continue
        groups.append([w[i]])
        i += 1
    # 2. Latin runs and numbers with the word after them (a unit or a counted noun)
    out = []
    for g in groups:
        if out and len(g) == 1 and LATIN.match(g[0]) and LATIN.match(out[-1][-1]) and not out[-1][-1].endswith(('،', ',')):
            out[-1] += g
            continue
        if out and len(out[-1]) == 1 and re.match(r'^\d[\d.,]*%?$', out[-1][-1]) and ARABIC.match(g[0]) and \
                g[0].rstrip('،,.') not in NO_BREAK_AFTER:      # «23.4 غيغابايت», never the 2 of «Switch 2» with «في»
            out[-1] += g
            continue
        out.append(list(g))
    if not soft:
        return [' '.join(g) for g in out]
    # 3. particles and the nouns that introduce a name stay with what follows
    res = []
    for g in out:
        if res and res[-1][-1].rstrip('،,') in NO_BREAK_AFTER and not res[-1][-1].endswith(('،', ',')):
            res[-1] += g
        else:
            res.append(g)
    return [' '.join(g) for g in res]


def visual(text, size):
    """The text wrapped at `size` into visual lines (greedy on units, every visual line opening on an Arabic word where
    it can)."""
    cap = chars_at(size)
    lines, cur = [], ''
    for u in units(text, soft=False):
        cand = (cur + ' ' + u).strip()
        if cur and len(cand) > cap:
            lines.append(cur)
            cur = u
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def _px(text, size):
    """The drawn width with the Dubai font, as reel.line_layer measures it, or None where the font is not installed (the
    slip lane, the container): then the character estimate decides and the render's text step re-checks with the font."""
    if size not in _FONTS:
        try:
            import fast_ar as A
            from PIL import Image, ImageDraw
            _FONTS[size] = (A.F('Bold', size), ImageDraw.Draw(Image.new('L', (8, 8))), A.AR)
        except Exception:                               # noqa: BLE001
            _FONTS[size] = None
    f = _FONTS[size]
    if not f:
        return None
    try:
        return f[1].textlength(text, font=f[0], **f[2])
    except Exception:                                   # noqa: BLE001  no raqm layout: plain measure
        return f[1].textlength(text, font=f[0])


def _ok_line(x, size, hard):
    w = _px(x, size)
    if w is not None:
        return w <= ROOM
    return len(x) <= chars_at(size) + 3 or (x in hard and len(x) <= chars_at(size) * 1.4)


def fits(text, size):
    """True when the text sits on one visual line, or on two split at a hard-unit boundary with the second opening on an
    Arabic word. A visual line that is one name unit alone («نينتيندو إفريثينغ (Nintendo Everything)») may run to 1.4
    times the estimate: the render steps its type down to fit (reel.LINE_FLOOR)."""
    t = ' '.join(_tokens(text))
    us = units(t, soft=False)
    hard = set(us)
    if _ok_line(t, size, hard):
        return True
    for i in range(1, len(us)):
        a, b = ' '.join(us[:i]), ' '.join(us[i:])
        if ARABIC.match(b) and _ok_line(a, size, hard) and _ok_line(b, size, hard):
            return True
    return False


def wrap(text, size):
    """Two visual lines balanced at a unit boundary, the second opening on an Arabic word."""
    w = _px(text, size)
    if (w is not None and w <= ROOM * 0.85) or (w is None and len(text) <= chars_at(size)):
        return text
    us = units(text, soft=False)
    best, score = None, None
    for i in range(1, len(us)):
        a, b = ' '.join(us[:i]), ' '.join(us[i:])
        if not ARABIC.match(b):
            continue
        hard = set(us)
        s = abs(len(a) - len(b)) + (0 if _ok_line(a, size, hard) and _ok_line(b, size, hard) else 100)
        last = us[i - 1].split()[-1]
        s += -12 if last.endswith(('،', ',')) else (15 if last in NO_BREAK_AFTER else 0)
        if score is None or s < score:
            best, score = (a, b), s
    return text if not best else best[0] + '\n' + best[1]


def clauses(sentence):
    """A sentence cut at its commas (the comma stays with the clause before it)."""
    out, cur = [], []
    for w in _tokens(sentence):
        cur.append(w)
        if w.endswith(('،', ',')):
            out.append(' '.join(cur))
            cur = []
    if cur:
        out.append(' '.join(cur))
    return out


def _split_long(clause, size):
    """A clause longer than two visual lines, halved at a unit boundary (never inside a name, number or phrase)."""
    us = units(clause)
    if any(not fits(u, size) for u in us):
        us = units(clause, soft=False)
    if len(us) < 2:
        return [clause]
    best, score = None, None
    for i in range(1, len(us)):
        a, b = ' '.join(us[:i]), ' '.join(us[i:])
        if not ARABIC.match(b):
            continue
        s = abs(len(a) - len(b))
        if score is None or s < score:
            best, score = (a, b), s
    if not best:
        return [clause]
    out = []
    for part in best:
        out += _split_long(part, size) if not fits(part, size) else [part]
    return out


def _best_split(sentence, size):
    """The sentence as the fewest lines that fit, cut only between soft units (never inside a name, a number with its
    unit or a phrase), preferring cuts after a comma, then pieces of 5 words or more, then even lengths."""
    us = units(sentence)
    if any(not fits(u, size) for u in us):
        us = units(sentence, soft=False)
    n = len(us)
    INF = (10 ** 9,)
    best = [INF] * (n + 1)
    back = [None] * (n + 1)
    best[0] = (0, 0)
    for j in range(1, n + 1):
        for i in range(j):
            if best[i] == INF:
                continue
            piece = ' '.join(us[i:j])
            if not fits(piece, size) and j - i > 1:
                continue
            pen = 0
            if j < n and not us[j - 1].endswith(('،', ',')):
                pen += 30                                  # a cut that is not at a comma
            if nwords(piece) < MIN_WORDS and n > 1:
                pen += 200                                 # a short piece (rule 4)
            pen += abs(len(piece) - chars_at(size) * 1.6) // 4
            cand = (best[i][0] + 1, best[i][1] + pen)
            if cand < best[j]:
                best[j], back[j] = cand, i
    out, j = [], n
    while j > 0:
        i = back[j]
        out.append(' '.join(us[i:j]))
        j = i
    return out[::-1]


def _pack(sentences, size):
    """[(line, sentence index)]: each sentence as its best lines; a whole short sentence may then share a line with the
    one before (the merge step)."""
    lines = []
    for si, s in enumerate(sentences):
        lines += [(x, si) for x in _best_split(s, size)]
    return lines


def nwords(t):
    return len(_tokens(t))


def _merge_short(lines, size):
    """A line under MIN_WORDS joins a neighbour: its own sentence's next line, else its own sentence's line before, else
    the next line, else the line before; whichever still fits two visual lines. The last line may stay short when
    nothing fits it."""
    out = list(lines)
    i = 0
    while i < len(out):
        t, si = out[i]
        if nwords(t) >= MIN_WORDS or len(out) == 1:
            i += 1
            continue
        opts = []
        if i + 1 < len(out) and out[i + 1][1] == si:
            opts.append('next')
        if i > 0 and out[i - 1][1] == si:
            opts.append('prev')
        if i + 1 < len(out):
            opts.append('next')
        if i > 0:
            opts.append('prev')
        done = False
        for o in opts:
            if o == 'next' and fits(t + ' ' + out[i + 1][0], size):
                out[i:i + 2] = [(t + ' ' + out[i + 1][0], si)]
                done = True
                break
            if o == 'prev' and fits(out[i - 1][0] + ' ' + t, size):
                out[i - 1:i + 1] = [(out[i - 1][0] + ' ' + t, out[i - 1][1])]
                i -= 1
                done = True
                break
        if not done:
            i += 1
    return [x for x, _ in out]


def cut(sentences, size_from=None):
    """[(text, size)] for a list of spoken sentences, and the problems. Steps the size down until 6 lines hold it."""
    if isinstance(sentences, str):
        import textrules as TR
        sentences = [s for s in TR.spoken_sentences(sentences) if s.strip()]
    tries = []
    for size in [s for s in SIZES if not size_from or s <= size_from] or [SIZES[-1]]:
        lines = _merge_short(_pack(sentences, size), size)
        tries.append((lines, size, all(fits(x, size) for x in lines)))
    readable = [x for x in tries if x[1] >= 44]
    best = next(((l, z) for l, z, ok in readable if ok and len(l) <= MAX_LINES), None)
    if best is None:                       # 6 lines will not hold it: the fewest lines that fit, at the largest size
        ok = [(l, z) for l, z, f in readable if f]
        if ok:
            fewest = min(len(l) for l, _ in ok)
            best = next((l, z) for l, z in ok if len(l) == fewest)
    if best is None:                       # 40 px only for a name that fits nowhere larger (reel.LINE_FLOOR)
        best = next(((l, z) for l, z, f in tries if f), (tries[-1][0], tries[-1][1]))
    lines, size = best
    probs = []
    if len(lines) > MAX_LINES:
        probs.append(f'the spoken paragraph makes {len(lines)} lines at {size} px; a Reel holds {MAX_LINES}: shorten it '
                     '(one fact per sentence, the rest in the caption)')
    over = [x for x in lines if not fits(x, size)]
    if over:
        probs.append('a line runs past two visual lines (' + over[0][:40] + '...): shorten its clause')
    import textrules as TR                 # 25 Nov 2026: no line opens on a Latin word; «لعبة» stays with its name
    lines, _ = TR.carry_across(lines)
    lines, _ = TR.keep_names(lines)        # 25 Nov 2026: «فروم سوفتوير» never split across two lines
    return [(wrap(x, size), size) for x in lines], probs


# ---------------------------------------------------------------------------------------------- the render (any job)
def _group_text(grp):
    """(text, opts) for a line group with one text item, else None (multi-item groups are left alone)."""
    if not (isinstance(grp, list) and len(grp) >= 3 and isinstance(grp[2], list) and len(grp[2]) == 1):
        return None
    x = grp[2][0]
    if isinstance(x, str):
        return x, {}
    if isinstance(x, list) and x and isinstance(x[0], str):
        return x[0], dict(x[1]) if len(x) > 1 and isinstance(x[1], dict) else {}
    return None


def _same_place(o1, o2):
    keys = ('top', 'y', 'position', 'subtitle', 'quote', 'speaker', 'align')
    return all(o1.get(k) == o2.get(k) for k in keys)


def _split_name(a, b):
    """True when a cut between two lines falls inside a name or a number with its unit."""
    tb = _tokens(b)
    if not tb:
        return False
    head = ' '.join(tb[:4])
    if re.match(r'^(?:[ء-ي]+\s+){0,2}\(', head) and not a.rstrip().endswith(('،', ',', '.')):
        return True                                   # «... نينتيندو» | «إفريثينغ (Nintendo Everything) ...»
    ta = _tokens(a)
    if ta and re.match(r'^\d[\d.,]*%?$', ta[-1]) and ARABIC.match(tb[0]):
        return True                                   # «23.4» | «غيغابايت»
    if ta and ta[-1].rstrip('،,') in NO_BREAK_AFTER and not ta[-1].endswith(('،', ',')):
        return True
    return False


def _is_card(sh):
    return isinstance(sh, list) and sh and '-gfx-' in str(sh[0])


def _secs(sh):
    try:
        return float(sh[2])
    except (TypeError, ValueError, IndexError):
        return 2.5


def _bad(texts, sizes=None):
    """Why a run of lines breaks the rules, or None."""
    for k, x in enumerate(texts):
        size = (sizes or [BASE_SIZE] * len(texts))[k]
        if _px(x, size) is not None and not fits(x, size):
            return f'line {k + 1} does not fit two visual lines at {size} px'
    for k in range(len(texts) - 1):
        if nwords(texts[k]) < MIN_WORDS:
            return f'line {k + 1} is under {MIN_WORDS} words'
        if _split_name(texts[k], texts[k + 1]):
            return f'lines {k + 1} and {k + 2} cut a name, a number or a phrase'
    if len(texts) > MAX_LINES:
        return f'{len(texts)} lines (a Reel holds {MAX_LINES})'
    return None


def _spread(lines, shots, a, z):
    """Shot spans for the new lines over shots a..z, by reading time, each line one shot at least, boundaries on cuts."""
    import textrules as TR
    n = len(lines)
    ids = list(range(a, z + 1))
    if len(ids) < n:
        return None
    dur = [_secs(shots[i]) for i in ids]
    need = [TR.read_secs(t.replace('\n', ' ')) for t in lines]
    total, want = sum(dur), sum(need)
    spans, k, acc_t = [], 0, 0.0
    for li in range(n):
        acc_t += need[li] / want * total
        start = k
        if li == n - 1:
            end = len(ids) - 1
        else:
            end, run = start, sum(dur[:start + 1])
            while end + 1 < len(ids) - (n - 1 - li) and run + dur[end + 1] / 2 <= acc_t:
                end += 1
                run += dur[end]
        spans.append((ids[start], ids[end]))
        k = end + 1
    return spans


def _norm(w):
    return re.sub(r'[^\w\u0621-\u064A]', '', w).lower()


def _from_spoken(spoken, texts):
    """The stretch of the spoken paragraph the run's words come from, with its own punctuation (the full stops the cut
    pieces dropped), or None when the words are not one stretch of it."""
    sp = _tokens(spoken)
    want = [_norm(w) for w in _tokens(' '.join(texts)) if _norm(w)]
    if not sp or not want:
        return None
    norm = [_norm(w) for w in sp]
    for st in range(len(sp)):
        k, m = st, 0
        while k < len(sp) and m < len(want):
            if not norm[k]:
                k += 1
                continue
            if norm[k] != want[m]:
                break
            k += 1
            m += 1
        if m == len(want):
            return ' '.join(sp[st:k])
    return None


def merge_job(job):
    """Rules 1 to 4 on any job's story lines, in place: a run of consecutive one-item line groups in the same place (no
    card inside it) that drip-feeds (a line under 5 words before the last, a cut inside a name, a number or a phrase, or
    more than 6 lines) is cut again from its joined text with cut(), and the new lines are spread over the same shots by
    reading time, so one line stays up as the shots change under it. "lines_ok" in a job waives it. Returns the changes."""
    lines, shots = job.get('lines'), job.get('shots') or []
    if not isinstance(lines, list) or len(lines) < 2 or job.get('lines_ok') or job.get('reveal'):
        return []
    import textrules as TR
    changes, i = [], 0
    while i < len(lines):
        g = _group_text(lines[i])
        if not g:
            i += 1
            continue
        j = i
        while j + 1 < len(lines):
            h = _group_text(lines[j + 1])
            if not h or not _same_place(g[1], h[1]):
                break
            if any(_is_card(shots[k]) for k in range(lines[j][1] + 1, lines[j + 1][0]) if 0 <= k < len(shots)):
                break
            j += 1
        run = lines[i:j + 1]
        texts = [_group_text(x)[0].replace('\n', ' ') for x in run]
        sizes = [int(_group_text(x)[1].get('size') or BASE_SIZE) for x in run]
        why = _bad(texts, sizes) if len(run) > 1 or _px('ا', BASE_SIZE) is not None else None
        if why:
            joined = _from_spoken(job.get('spoken'), texts) or ' '.join(texts)
            sents = [x for x in TR.spoken_sentences(joined) if x.strip()] or [joined]
            size0 = int(g[1].get('size') or BASE_SIZE)
            new, probs = cut(sents, size_from=size0)
            over = [x for x in probs if 'two visual lines' in x]
            spans = _spread([t for t, _ in new], shots, run[0][0], run[-1][1]) if not over else None
            if spans and (len(new) < len(run) or 'does not fit' in why):
                if probs:
                    why += '; ' + '; '.join(probs)
                groups = []
                for (t, size), (a, b) in zip(new, spans):
                    o = dict(g[1])
                    o['size'] = size
                    groups.append([a, b, [[t, o]]] + list(run[0][3:]))
                changes.append({'where': f'lines {i + 1}-{j + 1}', 'what': f'{why}: cut again as {len(new)} full '
                                'sentences or clauses across the same shots (23 Nov 2026)', 'before': texts,
                                'after': [t for t, _ in new]})
                lines[i:j + 1] = groups
                i += len(groups)
                continue
        i = j + 1
    return changes


if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) > 1:
        j = json.load(open(sys.argv[1], encoding='utf-8'))
        before = [(g[0], g[1], _group_text(g)[0] if _group_text(g) else g[2]) for g in j.get('lines') or []]
        ch = merge_job(j)
        print('before:')
        for x in before:
            print('  ', x)
        print('after:')
        for g in j.get('lines') or []:
            print('  ', g[0], g[1], _group_text(g)[0] if _group_text(g) else g[2])
        print(len(ch), 'change(s)')
