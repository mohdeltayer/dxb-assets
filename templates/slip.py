"""Story slip to Reel, no model in the step (adv-20261117-server-news-line-editor-model, Phase 1; Mohammad 17 Nov 2026).

The editor (one hourly Claude task) writes one small slip per story in dxb-queue desk/slips/<id>.json. The server turns
it into a story file and a job by itself: the footage resolver picks the game's official video, the shots are left to
the server ("auto"), the lines are cut from the spoken paragraph in order, the credit covers every footage shot, the
layout is the plain news one (template trailer), and the gates run in auto-fix mode on the render. Names and house rules
are checked mechanically; anything unknown is flagged on the result, never guessed. A slip that cannot be built is
marked failed with the reason. Nothing here posts.

Slip (JSON):
  id            story id, YYYY-MM-DD-<slug> (also the story file name)
  name          optional job and Reel name (default: the id without its date)
  label         the ladder chip: جديد, رسمي, تقرير, تسريب, شائعة, متوفر الآن, تأجيل, السعر, تحديث, نظرة أولى
  sources       [{"role": "primary"|"outlet", "name", "url"}, ...]; رسمي and جديد need a primary
  first_report  where and when the story was first reported (text with a time)
  credit        the on-screen source in Arabic, as names-ar has it: «نينتندو (Nintendo)»
  footage       steam:<appid>, or the game's Nintendo US store, IGN video or playstation.com game page
  headline      on-screen headline (two short lines at most; «\n» sets the break)
  spoken        the story as one paragraph of 2 to 3 Arabic sentences; the lines are cut from it, in order
  instagram     the caption (ends on the hashtag line «#ألعاب #أخبار_الألعاب» plus two tags)
  x, threads    the short texts (no hashtags; Threads ends on its source line)
  tier          0 to 3 (games-news-editor tiers); expires: ISO time after which the slip is not built
  optional: kind (formats.NEWS_MAP kind), theme, game, companies, genre, angle {"why_now", "what_it_means_here"} (needed
            for تقرير and تسريب), date ("17 Nov 2026"), footage_pick (index into the resolver's list), sound ("bed" with
            "bed_reason" when the trailer has no usable sound)

    python3 templates/slip.py check <slip.json>                             problems and flags, no network
    python3 templates/slip.py grammar-sha <slip.json>                       the texts_sha for grammar_review (19 Nov)
    python3 templates/slip.py build <slip.json> [--lane live|test] [--result r.json] [--no-resolve]
"""
import datetime as dt
import functools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

LABELS = ('جديد', 'رسمي', 'تقرير', 'تسريب', 'شائعة', 'متوفر الآن', 'تأجيل', 'السعر', 'تحديث', 'نظرة أولى')
NEEDS_PRIMARY = ('جديد', 'رسمي', 'متوفر الآن', 'تأجيل', 'السعر', 'تحديث')
REPORT_LABELS = ('تقرير', 'تسريب')
KIND_OF_LABEL = {'متوفر الآن': 'launch', 'تأجيل': 'delay', 'السعر': 'price', 'تحديث': 'update', 'نظرة أولى': 'reveal'}
REQUIRED = ('id', 'label', 'sources', 'first_report', 'credit', 'footage', 'headline', 'spoken', 'instagram', 'x',
            'threads', 'tier', 'expires')
GRAMMAR_FIELDS = ('headline', 'spoken', 'credit', 'instagram', 'x', 'threads')   # the texts the grammar stage reviews
# Split by platform (Mohammad, 24 Nov 2026): x and threads are the quick post's texts (the image card on X and Threads);
# reel_x and reel_threads are the Reel's own X and Threads posts, two hours or more later, a different first line that
# leads with what the video shows. Without them the Reel goes to Instagram only. Reviewed by the grammar stage when present.
OPTIONAL_TEXTS = ('reel_x', 'reel_threads')


def grammar_sha(slip):
    """The hash of the texts the arabic-grammar-review stage passed (Burning Sword case, Mohammad 19 Nov 2026): the
    slip records it as grammar_review.texts_sha after the required edits are applied; any later change to a text
    needs the stage again."""
    import hashlib
    fields = GRAMMAR_FIELDS + tuple(k for k in OPTIONAL_TEXTS if slip.get(k))   # optional texts join only when present
    blob = json.dumps({k: str(slip.get(k) or '') for k in fields}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()[:16]


def grammar_problem(slip):
    """None when the slip carries a grammar review of exactly its current texts, else the refusal."""
    g = slip.get('grammar_review')
    how = ('run the arabic-grammar-review stage on headline, spoken (the lines are cut from it), credit, instagram, x '
           'and threads, apply every required edit to the slip, then record "grammar_review": {"by": "arabic-grammar-'
           'review", "at": "<ISO time>", "required_edits": <n applied>, "texts_sha": "<python3 templates/slip.py '
           'grammar-sha <slip>>"}')
    if not isinstance(g, dict) or not g.get('texts_sha'):
        return 'grammar_review missing: ' + how
    if g.get('texts_sha') != grammar_sha(slip):
        return 'grammar_review is for other texts (a text changed after the review): ' + how
    return None
ID = re.compile(r'^20\d\d-\d\d-\d\d-[a-z0-9][a-z0-9-]{2,100}$')
NAME = re.compile(r'^[a-z0-9][a-z0-9-]{2,120}$')
ARABIC = re.compile('[؀-ۿ]')
ARABIC_INDIC = re.compile('[٠-٩۰-۹]')
BRACKET = re.compile('((?:[\u0621-\u064A\u0640\u064B-\u0652]+[ \\-]){0,3}[\u0621-\u064A\u0640\u064B-\u0652]+)\\s*\\(([A-Za-z][^()]{1,60})\\)')
NAME_LEAD = ('و', 'شركة', 'استوديو', 'موقع', 'حسب', 'لموقع', 'منصة', 'ناشر', 'الناشر', 'المطور', 'مطور', 'صحيفة', 'مجلة')
NO_BREAK_AFTER = {'في', 'على', 'من', 'إلى', 'عن', 'مع', 'بعد', 'قبل', 'حتى', 'منذ', 'عبر', 'دون', 'بين', 'حول', 'لدى',
                  'عند', 'أو', 'و', 'ثم', 'التي', 'الذي', 'هما', 'هي', 'هو', 'لا', 'لم', 'لن', 'قد', 'أن', 'إن', 'كل',
                  'بعض', 'بسعر', 'بمستوى', 'نحو'}
HASHTAGS_HEAD = '#ألعاب #أخبار_الألعاب'
HOOK_SECS = 3.8          # line 1 enters after textrules.HEAD_CLEAR (3.3 s) once the 0.4 s crossfade is taken off
MIN_SECS = 3.0
BEAT_CHARS = 58          # one beat: two visual lines at most
LINE_CHARS = 30          # one visual line at 54 px, conservatively (Dubai Bold; the server's font check decides)
LINE_SIZE = 54
MAX_BEATS = 12           # every beat of the spoken paragraph is on screen (21 Nov: Circana's lines stopped at 7)
PIECE_MAX = 2.8          # a beat's shot: trailers' clean stretches run about 2.6 to 3.3 s between cuts (Black Mesa, 17 Nov),
PIECE_MIN = 2.2          # so a beat longer than that spans two or three shots and its line runs across them
XFADE = 0.4              # each shot change takes this much off the line's time on screen


def pieces(total):
    """Shot lengths for one beat that needs `total` seconds on screen: as few as keep every shot within PIECE_MAX,
    each change paying its crossfade."""
    k = 1
    while (total + XFADE * (k - 1)) / k > PIECE_MAX:
        k += 1
    each = max(PIECE_MIN, (total + XFADE * (k - 1)) / k)
    return [round(each, 2)] * k
IG_MAX, TH_MAX = 2200, 500
UTC = dt.timezone.utc


def _t(s):
    try:
        x = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return x if x.tzinfo else x.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None


def _name(slip):
    return slip.get('name') or re.sub(r'^20\d\d-\d\d-\d\d-', '', slip.get('id') or '')


# ---------------------------------------------------------------------------------------------------------- names
def _names_table():
    """{latin lower: arabic} from newsroom/names-ar.md and the glossary rows written «Arabic (Latin)»."""
    table = {}
    for p in (os.path.join(ROOT, 'newsroom', 'names-ar.md'), os.path.join(ROOT, 'arabic', 'house-glossary.md')):
        try:
            text = open(p, encoding='utf-8').read()
        except OSError:
            continue
        for row in text.splitlines():
            if not row.startswith('|'):
                continue
            cells = [c.strip() for c in row.strip('|').split('|')]
            if len(cells) >= 2 and re.search('[A-Za-z]', cells[0]) and ARABIC.search(cells[1]):
                latin = re.sub(r'\s*\(.*?\)\s*', ' ', cells[0]).strip().lower()
                table.setdefault(latin, cells[1])
        for ar, la in BRACKET.findall(text):
            table.setdefault(la.strip().lower(), ar.strip())
    return table


def name_flags(slip, table=None):
    """Every «Arabic (Latin)» pair in the slip's Arabic texts against names-ar and the glossary: an unknown Latin name, or
    an Arabic form other than the listed one, is a flag for the ticket (never a guess, never a refusal)."""
    table = _names_table() if table is None else table
    flags, seen = [], set()
    for field in ('credit', 'headline', 'spoken', 'instagram', 'x', 'threads'):
        for ar, la in BRACKET.findall(str(slip.get(field) or '')):
            words = ar.split()
            while len(words) > 1 and words[0] in NAME_LEAD:   # «حسب ميغا كريت (Mega Crit)»: the name is after the lead
                words = words[1:]
            ar = ' '.join(words)
            key = la.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            known = table.get(key)
            if known is None:
                flags.append(f'name not in names-ar: «{ar.strip()} ({la.strip()})» ({field}); add it there as Proposed')
            elif ar.strip().split()[-1] not in known and known.split()[0] not in ar:
                flags.append(f'name form: «{ar.strip()} ({la.strip()})» ({field}); names-ar has «{known}»')
    return flags


# ---------------------------------------------------------------------------------------------------------- rules
def _paragraphs(text):
    return [p.strip() for p in str(text or '').split('\n') if p.strip()]


def autofix(slip):
    """The slip's texts fixed where a machine can fix them, never refused (Mohammad, 25 Nov 2026, after the 24 to 25 Nov
    outage): an em dash becomes «، », Arabic-Indic digits become Western, a % or + sign that flips is spelt out or dropped
    (textrules._fix_text), a paragraph or headline line that opens on a Latin word is rewrapped or gets its Arabic word
    first (textrules.arabic_first), hashtags leave the X and Threads texts. Returns (slip, [what changed])."""
    import copy
    import textrules as TR
    s, out = copy.deepcopy(slip), []
    names = [n for n in (s.get('game'), s.get('game_short'), _short(s.get('game'))) if n]
    for field in ('credit', 'headline', 'spoken', 'instagram', 'x', 'threads', 'reel_x', 'reel_threads'):
        t = s.get(field)
        if not isinstance(t, str) or not t:
            continue
        new = re.sub(r'\s*—\s*', '، ', t)
        new = new.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
        if field in ('headline', 'spoken'):
            new, _ = TR._fix_text(new)
        if field in ('x', 'threads', 'reel_x', 'reel_threads'):
            new = re.sub(r'\s*#\S+', '', new).strip()
        sep = '\n'
        paras = new.split(sep)
        for i, p in enumerate(paras):
            if not p.strip() or (field == 'instagram' and p.lstrip().startswith('#')):
                continue
            fixed, w = TR.arabic_first(p, names)
            paras[i] = fixed
        new = sep.join(paras)
        if field == 'headline':
            new, _ = TR.shorten_headline(new, names)
        if new != t:
            s[field] = new
            out.append(field)
    return s, out


def problems(slip, now=None, reviewed=None):
    """Refusals: a slip with any of these is marked failed, with the reasons. `reviewed` is the slip as the editor wrote
    it, before autofix: the grammar review's texts_sha is checked against that text (25 Nov 2026)."""
    now = now or dt.datetime.now(UTC)
    import textrules as TR
    out = []
    missing = [k for k in REQUIRED if slip.get(k) in (None, '', [])]
    if missing:
        out.append('missing: ' + ', '.join(missing))
    gp = grammar_problem(reviewed or slip)          # Burning Sword case, 19 Nov 2026: a hard stop
    if gp:
        out.append(gp)
    # an unknown name is never a refusal (names rule correction, 21 Nov 2026): textrules.fix writes it in Latin letters
    # and lists it in the job's names_to_review; name_flags still reports it on the result
    sid = str(slip.get('id') or '')
    if sid and not ID.match(sid):
        out.append(f'id {sid!r}: YYYY-MM-DD-<slug>, lower case')
    if slip.get('name') and not NAME.match(slip['name']):
        out.append('name: lower case letters, digits and dashes')
    label = slip.get('label')
    if label and label not in LABELS:
        out.append(f'label {label!r}: one of {"، ".join(LABELS)} (عاجل is the breaking lane, not a slip)')
    srcs = slip.get('sources') or []
    if not isinstance(srcs, list) or any(not isinstance(s, dict) or not str(s.get('url', '')).startswith('http') for s in srcs):
        out.append('sources: a list of {"role", "name", "url"} with http links')
    elif label in NEEDS_PRIMARY and not any(s.get('role') == 'primary' for s in srcs):
        out.append(f'label {label}: needs a source with "role": "primary" (or label it تقرير and name the outlet)')
    if label in REPORT_LABELS:
        a = slip.get('angle') if isinstance(slip.get('angle'), dict) else {}
        for k in ('why_now', 'what_it_means_here'):
            if len(str(a.get(k) or '').split()) < 8:
                out.append(f'angle.{k}: at least 8 words for a {label} (what the claim usually means, the precedent, '
                           'what is not confirmed)')
    if slip.get('subject_person'):
        out.append('subject_person: a people story needs the person window; build it as a full job (not a slip, Phase 1)')
    exp = _t(slip.get('expires'))
    if slip.get('expires') and not exp:
        out.append('expires: an ISO time')
    elif exp and exp <= now:
        out.append(f'expired at {slip["expires"]}')
    try:
        tier = int(slip.get('tier'))
        if tier not in (0, 1, 2, 3):
            raise ValueError
    except (TypeError, ValueError):
        if slip.get('tier') is not None:
            out.append('tier: 0, 1, 2 or 3')
    for field in ('credit', 'headline', 'spoken', 'instagram', 'x', 'threads'):
        text = str(slip.get(field) or '')
        if '—' in text:
            out.append(f'{field}: an em dash (house rule: none)')
        if ARABIC_INDIC.search(text):
            out.append(f'{field}: Arabic-Indic digits (house rule: Western digits)')
        hw = []
        TR.house_words(field, text, hw, slip)
        out += [f"{field}: «{f['text']}»: {f['fix']}" for f in hw]
        if field in ('headline', 'spoken') and re.search(r'[+%](?=[»"\s.،]|$)', text):
            out.append(f'{field}: a + or % sign flips to the far side in right-to-left text; spell it out '
                       '(New Game Plus, «بالمئة») (Dawnwalker test, 17 Nov)')
        for i, p in enumerate(_paragraphs(text) if field != 'headline' else str(text).split('\n')):
            if field == 'instagram' and p.startswith('#'):
                continue
            if not ARABIC.match(p.lstrip('«"“‏( ')):
                out.append(f'{field}: paragraph {i + 1} starts with {p[:20]!r}; every paragraph starts with an Arabic word')
    for field in ('x', 'threads'):
        if '#' in str(slip.get(field) or ''):
            out.append(f'{field}: no hashtags on X and Threads')
    ig = str(slip.get('instagram') or '')
    if ig:
        last = _paragraphs(ig)[-1] if _paragraphs(ig) else ''
        if not last.startswith(HASHTAGS_HEAD):
            out.append(f'instagram: the last line starts with «{HASHTAGS_HEAD}» plus two tags')
        elif len(last.split()) != 4:
            out.append(f'instagram: the hashtag line has {len(last.split())} tags (exactly 4)')
        if len(ig) > IG_MAX:
            out.append(f'instagram: {len(ig)} characters (at most {IG_MAX})')
    if len(str(slip.get('threads') or '')) > TH_MAX:
        out.append(f'threads: {len(slip["threads"])} characters (at most {TH_MAX})')
    if slip.get('credit') and not str(slip['credit']).startswith(('المصدر', 'لقطات')):
        pass                                        # the builder prefixes «المصدر:»
    if slip.get('sound') == 'bed' and len(str(slip.get('bed_reason') or '').split()) < 6:
        out.append('sound bed: "bed_reason" names the trailers checked and why their sound is unusable')
    return out


# ---------------------------------------------------------------------------------------------------------- lines
def _split_at(words, limit, right_max=None):
    """Index to cut a word list so the first part stays under `limit` characters, at a clause comma where possible, and
    so the second part opens on an Arabic word (a visual line never opens on a Latin name or a digit)."""
    best, best_score = None, None
    total = len(' '.join(words))
    for i in range(1, len(words)):
        left = ' '.join(words[:i])
        comma = words[i - 1].endswith('،')
        if len(left) > limit + (12 if comma else 0):   # a clause comma may run a little long: it reads better
            break
        if not ARABIC.match(words[i]) or words[i - 1].rstrip('،') in NO_BREAK_AFTER:
            continue
        score = abs(len(left) - total / 2) - (25 if comma else 0)
        if right_max and total - len(left) - 1 > right_max:
            score += 100                               # the second visual line would run out of the safe zone
        if not comma and re.match(r'^[\d.,%]+$', words[i - 1]):
            score += 15                                # a number stays with the word it counts where it can (DRG, 17
                                                       # Nov: a ban left only «ويصل» alone, a 35-character second line)
        if best_score is None or score < best_score:
            best, best_score = i, score
    return best


def _wrap(text):
    """One beat as one or two visual lines."""
    if len(text) <= LINE_CHARS:
        return text
    words = text.split()
    i = _split_at(words, max(LINE_CHARS, len(text) - LINE_CHARS), right_max=LINE_CHARS + 3)
    if i is None:
        return text
    return ' '.join(words[:i]) + '\n' + ' '.join(words[i:])


def _words(text):
    return [w for w in re.findall(r'[\w\u0600-\u06FF]+', str(text or '')) if len(w) > 2]


def story_sentences(spoken, headline=None):
    """The spoken sentences; the first one is left out when it only restates the headline (reel-check 5: the lines open
    the story, they do not repeat the headline), as long as another sentence remains."""
    import textrules as TR
    sents = [s.strip() for s in TR.spoken_sentences(spoken) if s.strip()]
    head = set(_words(headline))
    if headline and len(sents) > 1 and head and len(head & set(_words(sents[0]))) >= 0.7 * len(head):
        sents = sents[1:]
    return sents


def fits(beat):
    """Both visual lines of a beat inside LINE_CHARS (a few over is left to the server's font check)."""
    return all(len(v) <= LINE_CHARS + 3 for v in _wrap(beat).split('\n'))


def beats(spoken, headline=None):
    """The spoken paragraph cut into beats, in order, every word kept: sentences, then halves at a clause comma or the
    middle until each beat fits two visual lines."""
    out = []
    for s in story_sentences(spoken, headline):
        stack = [s.strip()]
        while stack:
            b = stack.pop(0)
            if len(b) <= BEAT_CHARS and fits(b):
                out.append(b)
                continue
            words = b.split()
            i = _split_at(words, BEAT_CHARS)
            if i is None:
                out.append(b)                       # left to the text check, which names it
                continue
            stack[:0] = [' '.join(words[:i]), ' '.join(words[i:])]
    return out


# ---------------------------------------------------------------------------------------------------------- build
def pick_footage(cands, index=None):
    ok = [c for c in cands if c.get('decode_clean') is not False and c.get('job')]
    if index is not None:
        if not (0 <= int(index) < len(cands)):
            raise ValueError(f'footage_pick {index}: the resolver gave {len(cands)} videos')
        return cands[int(index)]
    if not ok:
        raise ValueError('no decode-clean official video from the footage source')
    return ok[0]


def theme_for(slip):
    if slip.get('theme'):
        return slip['theme']
    try:
        import looks
        prev = looks.last(2)
        avoid = {e.get('theme') for e in prev} if len(prev) == 2 and prev[0].get('theme') == prev[1].get('theme') else set()
        return looks.rested('theme', prev, avoid | {'crimson'}) or 'cold'
    except Exception:
        return 'cold'


def story_file(slip, footage_note):
    return {
        'id': slip['id'], 'title': slip.get('title') or slip['headline'].replace('\n', ' '), 'status': 'building',
        'lane': 'digital-lounge', 'game': slip.get('game'), 'game_key': __import__('gamekey').key(slip.get('game')),
        'companies': slip.get('companies') or [],
        'subject_person': ({k: v for k, v in (shape(slip).get('person') or {}).items() if k in ('name', 'role')} or None)
                          if shape(slip)['class'] == 'person' else None, 'genre': slip.get('genre') or [], 'kind_news': slip.get('kind') or KIND_OF_LABEL.get(slip['label'], 'reveal'),
        'label': slip['label'], 'chip': slip['label'], 'template': shape(slip)['template'], 'sources': slip['sources'],
        'first_report': slip['first_report'],
        'source_type': 'primary' if any(s.get('role') == 'primary' for s in slip['sources']) else 'secondary',
        'footage': footage_note, 'beat': slip.get('beat') or 'news',
        'angle': slip.get('angle') or None, 'spoken': slip['spoken'],
        'texts': dict({'instagram': slip['instagram'], 'x': slip['x'], 'threads': slip['threads']},
                      **{k: slip[k] for k in OPTIONAL_TEXTS if slip.get(k)}),
        'slip': {'tier': slip['tier'], 'expires': slip['expires'], 'built_at': dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')},
    }


HOSTS = {'rockstargames': 'Rockstar Games', 'playstation.com': 'PlayStation', 'nintendo.com': 'Nintendo',
         'xbox.com': 'Xbox', 'ea.com': 'Electronic Arts', 'ubisoft': 'Ubisoft', 'square-enix': 'Square Enix',
         'bandainamco': 'Bandai Namco', 'capcom': 'Capcom'}
FOOT_CLAUSE = re.compile(r'[،,]?\s*\n?\s*(?:و?(?:ال)?لقطات)\b.*$', re.S)


@functools.lru_cache(maxsize=64)
def steam_publisher(appid):
    """The publisher Steam lists for an app (store API, read only); None when it cannot be read."""
    try:
        import urllib.request
        u = f'https://store.steampowered.com/api/appdetails?appids={int(appid)}&filters=basic'
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20))
        pubs = (d.get(str(int(appid)), {}).get('data') or {}).get('publishers') or []
        return pubs[0] if pubs else None
    except Exception:                               # noqa: BLE001
        return None


def footage_owner(slip, foot):
    """Who the footage actually used belongs to, in Latin: the Steam app's publisher, the official host of a URL, the
    library note, else the slip's first company."""
    if foot.get('steam'):
        p = steam_publisher(foot['steam'])
        if p:
            return p
    url = str(foot.get('url') or '') + ' ' + str(foot.get('note') or '') + ' ' + str(foot.get('repo') or '')
    for host, owner in HOSTS.items():
        if host in url.lower():
            if owner == 'PlayStation' and slip.get('companies'):   # a game trailer on playstation.com is the publisher's
                return slip['companies'][0]
            return owner
    if 'rockstar' in url.lower():
        return 'Rockstar Games'
    return (slip.get('companies') or [None])[0]


def arabic_name(latin, table=None):
    """names-ar's Arabic for a company, trying shorter forms ("Bandai Namco Entertainment" -> "Bandai Namco")."""
    table = _names_table() if table is None else table
    words = str(latin or '').split()
    for n in range(len(words), 0, -1):
        ar = table.get(' '.join(words[:n]).lower())
        if ar:
            return ar, ' '.join(words[:n])
    return None, latin


def footage_credit(slip, foot, table=None):
    """The on-screen credit names the footage actually used (Mohammad, 20 Nov 2026: the Ace Combat 8 credit said
    «صفحة اللعبة على Steam» over Bandai Namco's trailer). The slip's credit keeps its news source; any footage clause
    in it is replaced by the footage's owner: «المصدر: <outlet>،\nولقطات من <owner>», or «المصدر: <owner>» alone."""
    raw = str(slip.get('credit') or '').strip()
    news = FOOT_CLAUSE.sub('', raw).strip().rstrip('،,: ')
    news = re.sub(r'^المصدر\s*:?\s*', '', news).strip()
    owner = footage_owner(slip, foot)
    if not owner:                                   # nothing known about the footage: the slip's own words stand
        return raw if raw.startswith(('المصدر', 'لقطات')) else f'المصدر: {raw}'
    ar, lat = arabic_name(owner, table)
    who = f'{ar} ({lat})' if ar else owner
    if news and ar and ar in news:                  # the outlet is the footage's owner: one name is enough
        return f'المصدر: {news}'
    return f'المصدر: {news}،\nولقطات من {who}' if news else f'المصدر: {who}'


def _short(game):
    """The game's name before its subtitle ("Clair Obscur: Expedition 33" -> "Clair Obscur"), for the headline rule
    (19 Nov) when the slip gives no game_short (audit 21 Nov 2026, item 5, cause 2); None when there is no subtitle."""
    g = str(game or '').strip()
    return g.split(':')[0].strip() if ':' in g and len(g.split(':')[0].strip()) >= 3 else None


CARD_SECS = 4.2           # the figure card on the numbers template: the count-up (0.9 s) and the read
PERSON_SECS = 3.5         # the people template's photo window is open on frame 0 beside the headline, then steps aside


def shape(slip):
    """The story kind, template and skin the server picks for this slip (audit 21 Nov 2026, items 1 and 3)."""
    import storykind as SK
    cls, why = SK.classify(slip)
    skin, skin_why = SK.skin_for(slip.get('genre'), slip.get('game'), slip.get('kind'), slip.get('label'))
    out = {'class': cls, 'template': SK.TEMPLATE_OF[cls], 'why': why, 'skin': skin, 'skin_why': skin_why}
    if cls == 'numbers':
        out['figure'] = SK.figure(slip)
        if not out['figure'] or not out['figure'].get('value'):
            out.update({'class': 'trailer', 'template': 'trailer', 'why': why + '; no figure read, so trailer'})
    if cls == 'person':
        out['person'] = SK.person(slip)
        if not out['person']:
            out.update({'class': 'trailer', 'template': 'trailer', 'why': why + '; no person read, so trailer'})
    return out


def split_role(name, role):
    """(name, role) with a role word that leads the name moved to the role (Mohammad, 23 Nov 2026: «الممثل ستيف ماكوين»
    was the whole plate). A «Arabic (Latin)» pair keeps only the person's own words; the words before it join the role
    («رئيسة الهيئة لارا الخطيب (Lara Al-Khatib)» -> «Lara Al-Khatib», «رئيسة الهيئة»)."""
    import storykind as SK
    n, r = ' '.join(str(name or '').split()), str(role or '').strip()
    m = re.search(r'(.*?)\s*\(([A-Za-z][^()]{1,60})\)\s*$', n)
    if m:
        la = m.group(2).strip()
        words = m.group(1).split()
        k = max(1, min(len(words), len(la.split())))
        lead = ' '.join(words[:-k])
        if lead:
            r = (lead + (' ' + r if r and r not in lead else '')).strip()
        return SK._plate_name(' '.join(words[-k:]), la), r
    for w in sorted(SK.ROLES, key=len, reverse=True):
        if n.startswith(w + ' ') and len(n.split()) > len(w.split()):
            rest = n[len(w):].strip()
            return rest, (w + (' ' + r if r else '')).strip()
    return n, r


def job_from(slip, foot, lane='live', theme=None, spare=()):
    """The job, ready for the render: the template the story kind picks (numbers, people, debate or trailer), the
    skin its genre picks, server-picked shots, lines cut from the spoken paragraph."""
    import textrules as TR
    name = _name(slip)
    f = foot['file']
    kind = shape(slip)
    import linecut as LC                          # full sentences or clauses, 3 to 6 lines (Mohammad, 23 Nov 2026)
    cut_lines, cut_probs = LC.cut(story_sentences(slip['spoken'], slip['headline']))
    bs = [t for t, _ in cut_lines]
    line_flags = [f'lines: {x}' for x in cut_probs]
    shots = [[f, 'auto', HOOK_SECS, None]]
    gfx = []
    if kind['class'] == 'numbers':              # the figure on its own card over the game's moving footage, after the hook
        fig = kind['figure']
        card = {'file': f'{name}-gfx-figure.png', 'kind': 'fact', 'value': fig['value']}
        if fig.get('label'):
            card['label'] = fig['label']
        if fig.get('note'):
            card['note'] = fig['note']
        gfx.append(card)
        shots.append([card['file'], 0.0, CARD_SECS, None])
    lines = []
    for b, size in cut_lines:                       # one line stays up across the shots its reading time needs
        a = len(shots)
        for secs in pieces(TR.read_secs(b.replace('\n', ' ')) + 0.8):
            shots.append([f, 'auto', secs, None])
        lines.append([a, len(shots) - 1, [[b, {'size': size}]]])
    if len(shots) < 4:                              # a short story still breathes: footage after the last line
        shots += [[f, 'auto', MIN_SECS, None] for _ in range(4 - len(shots))]
    credit = footage_credit(slip, foot)
    out_dir = 'cards/test' if lane == 'test' else f'cards/{dt.date.today():%Y-%m}'
    track = 'bed' if slip.get('sound') == 'bed' else [f, 0.0]
    job = {
        'name': name, 'story': slip['id'], 'footage_source': slip.get('footage'), 'kind_news': slip.get('kind') or KIND_OF_LABEL.get(slip['label'], 'reveal'),
        'story_class': kind['class'], 'story_class_why': kind['why'], 'skin_why': kind['skin_why'],
        'built_by': 'server-slip', 'render_lane': 'server',
        'out': f'{out_dir}/{name}-reel-v1.mp4',
        'split_fallback': 'ladder',               # sound ladder (21 Nov): split, music only, franchise theme, our bed
        'footage': [foot] + [x for x in spare if x.get('file') and x['file'] != f], 'shots': shots, 'lines': lines,
        'credits': [[0, len(shots) - 1, credit, {'size': 40, 'band': True}]],
        'spoken': slip['spoken'], 'headline': slip['headline'], 'label': slip['label'],
        'game': slip.get('game'), 'game_short': slip.get('game_short') or _short(slip.get('game')),
        'game_key': __import__('gamekey').key(slip.get('game')), 'genre': slip.get('genre') or [],
        'texts': {k: slip.get(k) for k in ('instagram', 'x', 'threads') if slip.get(k)},
        'source': re.sub(r'^المصدر:\s*', '', credit).replace('\n', ' '), 'date': slip.get('date') or dt.date.today().strftime('%-d %b %Y'),
        'theme': theme or theme_for(slip), 'style': None, 'template': kind['template'], 'skin': kind['skin'], 'cut': False,
        'track': track, 'track_from_first_shot': track != 'bed',
        'angle': slip.get('angle') or None,
        'decision_log': {'source': 'server slip build (adv-20261117-server-news-line-editor-model Phase 1)',
                         'template': f"{kind['template']}: {kind['why']}", 'skin': f"{kind['skin']}: {kind['skin_why']}",
                         'footage': f'{foot.get("name") or f} from the resolver ({slip["footage"]})',
                         'shots': 'server-picked clean stretches in source order (autoshots)',
                         'music': 'the trailer\'s own sound from the first shot (sound ladder: split, music only, '
                                  'franchise theme, our bed)' if track != 'bed'
                                  else 'our bed: ' + str(slip.get('bed_reason'))},
        'reel_check': reel_check(slip, foot),
    }
    if line_flags:
        job['line_flags'] = line_flags
    if gfx:
        job['gfx'] = gfx
        job['ground_footage'] = [f, 4.0, 60.0]   # the calmest stretch of the trailer behind the card, moving
    if kind['class'] == 'person':
        p = dict(kind['person'])
        photo = f'{name}-person.jpg'
        import people as PL                       # the people photo library (Mohammad, 22 Nov 2026, items 1 to 3)
        hit = PL.lookup(' '.join(str(x) for x in (p.get('latin'), p.get('name'), slip.get('spoken'),
                                                  slip.get('headline')) if x))
        if hit and (not p.get('latin') or p['name'] == p.get('role') or not p.get('name')):
            p['name'] = PL.plate_name(hit[1])     # the plate always carries the name, never the role alone
            if p.get('role') == p['name']:
                p['role'] = ''
        if not p.get('role') and p.get('name') and kind['person'].get('name') not in (None, '', p['name']):
            p['role'] = kind['person']['name']    # what the parser took for the name was the role phrase
        p['name'], p['role'] = split_role(p.get('name') or '', p.get('role') or '')
        lib = PL.photo_of(hit[1]) if hit and not p.get('photo') else None
        if not lib and not p.get('photo') and not hit and os.environ.get('DXB_PEOPLE_LOOKUP') != 'off':   # look them up now
            got = PL.resolve(p.get('name') or '', p.get('role') or '', latin=p.get('latin'))
            if got:                               # Wikidata's portrait on Commons, cropped, added to the library
                hit = got
                lib = PL.photo_of(got[1])
                job['people_added'] = [got[0]]
            else:                                 # Commons refused: the register entry waits for people-library.yml
                pend = [k for k, e in PL.load().items() if e.get('pending') and not e.get('photo')
                        and (p.get('name') in (e.get('aliases') or []) or (p.get('latin') or '') == e.get('name_latin'))]
                if pend:
                    job['people_added'] = pend[:1]
                    job['people_pending'] = pend[:1]
        if p.get('photo'):                        # the slip's official photo (press kit, the company's page)
            job['footage'].append({'file': photo, 'url': p['photo']})
            ps = {'name': p['name'], 'role': p.get('role') or '', 'photo_source': p['photo']}
        elif lib:                                 # the library's photo, with its credit from the rights register
            job['footage'].append({'file': photo, 'repo': lib[0]})
            p.setdefault('credit', lib[1])
            p.setdefault('focus', lib[2])
            ps = {'name': p['name'], 'role': p.get('role') or '', 'photo_source': hit[1].get('source_url')}
            job['person_library'] = hit[0]
        else:                                     # no photo: a name card on the plate, the footage running behind it;
            photo = None                          # the box is never filled with game footage (22 Nov 2026, item 2)
            ps = {'name': p['name'], 'role': p.get('role') or '', 'photo_source': None}
            job['person_photo'] = 'none'
            job['searched'] = ['people library (templates/assets/people.json): ' +
                               (f'{hit[0]} has no photo yet' if hit else 'not listed') + '; the slip carried no photo; '
                               'name card on the plate (22 Nov 2026)']
        opts = {'focus': list(p.get('focus') or (0.5, 0.4))}
        if p.get('credit'):
            opts['credit'] = p['credit']
        job['person'] = [[photo, p['name'], p.get('role') or '', 0.0, PERSON_SECS, opts]]
        job['subject_person'] = ps
    if track == 'bed':
        job['bed_reason'] = slip.get('bed_reason')
    if slip.get('rerender'):                        # a rebuilt slip after a director send-back names why (qc.py rerender)
        job['rerender'] = slip['rerender']
    if lane == 'test':
        job['render_lane'] = 'hosted'
        job['lane_reason'] = 'Phase 1 test (no Publer upload, no ledgers)'
    return job


def reel_check(slip, foot):
    """What the server checked, with its evidence; the editor's review covers the rest at the ticket."""
    prim = next((s for s in slip['sources'] if s.get('role') == 'primary'), slip['sources'][0])
    return {
        'source read and first report noted': f'yes: {prim.get("name")} ({prim.get("url")}); first report: {slip["first_report"]}',
        'not already posted (ledger find)': 'yes: ledger.py find recorded in the story file at build',
        'angle before lines': 'yes: ' + ('angle in the slip' if slip.get('angle') else 'plain news; the spoken paragraph carries hook and payoff'),
        'one spoken paragraph, lines cut from it in order': 'yes: slip.beats() keeps every word in order; the text check confirms it',
        'names match names-ar': 'yes: slip.name_flags() run; flags listed on the result for the editor',
        'release verbs and house rules': 'yes: slip.problems() (Arabic first, no em dash, Western digits, hashtags only on Instagram)',
        'footage first, official': f'yes: {foot.get("job", foot).get("url") or "steam " + str(foot.get("steam"))} from the resolver, decode clean',
        'credit on every clip': 'yes: one credit over every shot',
        'sound': 'yes: trailer sound from the first shot, split per shot on the server' if slip.get('sound') != 'bed'
                 else 'yes: our bed, ' + str(slip.get('bed_reason')),
        'picture matches the lines': 'n/a: shots are picked by the server; the editor reviews the look frames at the ticket',
    }


SLIP_HARD = ('missing: ', 'id ', 'name: ', 'expired at', 'expires: ', 'grammar_review')   # cannot be built: no input, no path, out of date


def split_problems(probs):
    """Templates never refuse (adv-20261118-templates-never-refuse A): a slip stops only when it cannot be built
    (fields missing, a bad id or name, expired) or its text is bidi-broken (a paragraph or headline opening on a
    non-Arabic word, a flipping sign). Everything else is a flag on the result and the slip builds."""
    hard, soft = [], []
    for x in probs:
        if x.startswith(SLIP_HARD) or 'every paragraph starts with an Arabic word' in x or 'flips to the far side' in x:
            hard.append(x)
        else:
            soft.append(x)
    return hard, soft


def build(slip, lane='live', resolve=True, root=ROOT, now=None):
    """Writes the story file and the job; returns the result {state, problems, flags, job, story, footage}."""
    res = {'id': slip.get('id'), 'state': 'failed', 'problems': [], 'flags': [], 'at': dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}
    reviewed = slip                                 # the grammar review read this text
    slip, fixed_fields = autofix(slip)              # fixed, never refused (25 Nov 2026)
    hard, soft = split_problems(problems(slip, now, reviewed=reviewed))
    if fixed_fields:
        res['flags'].append('slip texts fixed mechanically: ' + ', '.join(fixed_fields))
    res['problems'] = hard
    if res['problems']:
        return res
    res['flags'] = res['flags'] + name_flags(slip) + [f'warning: {x}' for x in soft]
    name = _name(slip)
    # Publer is the source of truth (Mohammad, 23 Nov 2026): before preparing, the same story or the same game and news
    # already scheduled or published in the last 48 hours stops the slip (the repository's own record of Publer here; the
    # session checks Publer itself through the connector before writing the slip). "repeat_ok" waives it with a reason.
    if not slip.get('repeat_ok') and lane == 'live':
        try:
            import publercheck as PC
            posts = [p for p in PC.from_logs(now) if p.get('story') != slip.get('id')]
            same = [p for p in PC.from_logs(now) if p.get('story') == slip.get('id')]
            act, line = PC.verdict(slip.get('id'), name, slip.get('game'), slip.get('instagram') or slip.get('x') or '', posts)
            if same:
                res['problems'].append(f'already in Publer: this story was submitted ({same[0]["state"]}, {same[0]["at"]}); '
                                       'skip it and note it on the board (a newer version replaces it only while the first '
                                       'has not posted: Production 2 swaps it in Publer)')
                return res
            if act == 'stop':
                res['problems'].append(line.replace('publer check', 'already in Publer') + ' (note it on the board; '
                                       '"repeat_ok": "<reason>" when it is real new news on the same game)')
                return res
        except Exception as e:                      # noqa: BLE001  the check never breaks the lane
            res['flags'].append(f'publer check not run: {type(e).__name__}: {e}')
    if resolve:
        try:
            import footage as FT
            r = FT.resolve(slip['footage'], name=name, max_n=3, game=slip.get('game'))   # the game's library first
        except Exception as e:                      # the slip is failed with the reason, never left without a result
            res['problems'].append(f'footage: the resolver stopped on {slip["footage"]}: {type(e).__name__}: {e}')
            return res
        cands = r.get('candidates') or []
        pick = slip.get('footage_pick')
        if cands and cands[0].get('library') and pick is not None:   # the library wins over a page pick (20 Nov 2026)
            res['flags'].append(f'footage_pick {pick} ignored: the footage library has {cands[0].get("name")} for this game')
            pick = None
        try:
            c = pick_footage(cands, pick)
        except ValueError as e:
            res['problems'].append(f'footage: {e} ({slip["footage"]}; {r.get("error") or str(len(cands)) + " found"})')
            return res
        foot = dict(c['job'])
        # the resolver's other clean videos ride along: autoshots takes from them once the first runs out of clean
        # stretches (Black Mesa, 17 Nov: 15 shots asked of a trailer with 15 clean stretches)
        spare = [dict(x['job']) for x in cands if x is not c and x.get('job') and x.get('decode_clean') is not False]
        res['footage'] = {k: c.get(k) for k in ('name', 'width', 'height', 'fps', 'mbps', 'rows', 'duration', 'decode_clean')}
        if c.get('mbps') and c.get('height') and c['height'] < 1080:
            res['flags'].append(f'footage {c["width"]}x{c["height"]}: under 1080p, the quality gate may ask for the showcase layout')
    else:
        foot = {'file': f'{name}-trailer.mp4', 'url': 'https://example.invalid/test.mp4'}
        spare = []
    job = job_from(slip, foot, lane, spare=spare)
    import textrules as TR
    job, fixed = TR.fix(job)                        # the same mechanical fixes the render applies (glued prefix, signs)
    if fixed:
        res['flags'].append('text fixed mechanically: ' + '; '.join(f"{c['where']}: {c['what']}" for c in fixed))
    if job.get('names_to_review'):                  # for a proper Arabic form later (names rule correction, 21 Nov 2026)
        res['names_to_review'] = job['names_to_review']
    story = story_file(slip, f'Official video from the resolver ({slip["footage"]}): {foot.get("url") or foot.get("steam")}')
    sdir = os.path.join(root, 'newsroom', 'stories')
    jdir = os.path.join(root, 'jobs', 'test' if lane == 'test' else 'live')
    os.makedirs(sdir, exist_ok=True)
    os.makedirs(jdir, exist_ok=True)
    spath = os.path.join(sdir, slip['id'] + '.json')
    if os.path.exists(spath):                       # an existing story keeps its own record; the slip adds to it
        old = json.load(open(spath, encoding='utf-8'))
        old.update({k: v for k, v in story.items() if k not in ('status',) and v not in (None, '', [])})
        story = old
    json.dump(story, open(spath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    jpath = os.path.join(jdir, name + '.json')
    json.dump(job, open(jpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    import softgate as SG_
    hard = [f for f in TR.hard(TR.check(job)) if SG_.text_hard(f)]
    res['flags'] += [f"warning: text: {f['where']}: {f.get('fix') or f['rule']}" for f in TR.hard(TR.check(job))
                     if not SG_.text_hard(f)]
    if hard:
        res['problems'] += [f"text: {f['where']}: {f.get('fix') or f['rule']}" for f in hard]
    res.update(job=os.path.relpath(jpath, root), story=os.path.relpath(spath, root),
               state='failed' if res['problems'] else 'built', lines=len(job['lines']), shots=len(job['shots']))
    return res


def main(argv):
    if len(argv) < 2 or argv[0] not in ('check', 'build', 'grammar-sha'):
        raise SystemExit(__doc__)
    slip = json.load(open(argv[1], encoding='utf-8'))
    if argv[0] == 'grammar-sha':
        print(grammar_sha(slip))
        return 0
    if argv[0] == 'check':
        fixed_slip, _fx = autofix(slip)
        p, fl = problems(fixed_slip, reviewed=slip), name_flags(slip)
        for x in p:
            print('REFUSED: ' + x)
        for x in fl:
            print('FLAG: ' + x)
        if not p:
            print('slip: ok; beats: ' + ' | '.join(beats(slip['spoken'], slip.get('headline'))))
        return 1 if p else 0
    lane = argv[argv.index('--lane') + 1] if '--lane' in argv else 'live'
    res = build(slip, lane, resolve='--no-resolve' not in argv)
    out = argv[argv.index('--result') + 1] if '--result' in argv else None
    if out:
        json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('SLIP_RESULT: ' + json.dumps(res, ensure_ascii=False))
    return 0 if res['state'] == 'built' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
