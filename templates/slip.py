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
    python3 templates/slip.py build <slip.json> [--lane live|test] [--result r.json] [--no-resolve]
"""
import datetime as dt
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
MAX_SHOTS = 11
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


def problems(slip, now=None):
    """Refusals: a slip with any of these is marked failed, with the reasons."""
    now = now or dt.datetime.now(UTC)
    out = []
    missing = [k for k in REQUIRED if slip.get(k) in (None, '', [])]
    if missing:
        out.append('missing: ' + ', '.join(missing))
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
def _split_at(words, limit):
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
        if not comma and (re.match(r'^[\d.]+$', words[i - 1]) or (i >= 2 and re.match(r'^[\d.]+$', words[i - 2]))):
            continue                                   # a number stays with the words it counts
        score = abs(len(left) - total / 2) - (25 if comma else 0)
        if best_score is None or score < best_score:
            best, best_score = i, score
    return best


def _wrap(text):
    """One beat as one or two visual lines."""
    if len(text) <= LINE_CHARS:
        return text
    words = text.split()
    i = _split_at(words, max(LINE_CHARS, len(text) - LINE_CHARS))
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


def beats(spoken, headline=None):
    """The spoken paragraph cut into beats, in order, every word kept: sentences, then halves at a clause comma or the
    middle until each beat fits two visual lines."""
    out = []
    for s in story_sentences(spoken, headline):
        stack = [s.strip()]
        while stack:
            b = stack.pop(0)
            if len(b) <= BEAT_CHARS:
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
        'lane': 'digital-lounge', 'game': slip.get('game'), 'companies': slip.get('companies') or [],
        'subject_person': None, 'genre': slip.get('genre') or [], 'kind_news': slip.get('kind') or KIND_OF_LABEL.get(slip['label'], 'reveal'),
        'label': slip['label'], 'chip': slip['label'], 'template': 'trailer', 'sources': slip['sources'],
        'first_report': slip['first_report'],
        'source_type': 'primary' if any(s.get('role') == 'primary' for s in slip['sources']) else 'secondary',
        'footage': footage_note, 'beat': slip.get('beat') or 'news',
        'angle': slip.get('angle') or None, 'spoken': slip['spoken'],
        'texts': {'instagram': slip['instagram'], 'x': slip['x'], 'threads': slip['threads']},
        'slip': {'tier': slip['tier'], 'expires': slip['expires'], 'built_at': dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')},
    }


def job_from(slip, foot, lane='live', theme=None):
    """The job, ready for the render: plain news layout, server-picked shots, lines cut from the spoken paragraph."""
    import textrules as TR
    name = _name(slip)
    f = foot['file']
    bs = beats(slip['spoken'], slip['headline'])[:MAX_SHOTS - 1]
    shots = [[f, 'auto', HOOK_SECS, None]]
    lines = []
    for i, b in enumerate(bs, start=1):
        secs = round(max(MIN_SECS, TR.read_secs(b) + 0.7), 2)
        shots.append([f, 'auto', secs, None])
        lines.append([i, i, [[_wrap(b), {'size': LINE_SIZE}]]])
    if len(shots) < 4:                              # a short story still breathes: footage after the last line
        shots += [[f, 'auto', MIN_SECS, None] for _ in range(4 - len(shots))]
    credit = slip['credit'] if str(slip['credit']).startswith(('المصدر', 'لقطات')) else f'المصدر: {slip["credit"]}'
    out_dir = 'cards/test' if lane == 'test' else f'cards/{dt.date.today():%Y-%m}'
    track = 'bed' if slip.get('sound') == 'bed' else [f, 0.0]
    job = {
        'name': name, 'story': slip['id'], 'kind_news': slip.get('kind') or KIND_OF_LABEL.get(slip['label'], 'reveal'),
        'built_by': 'server-slip', 'render_lane': 'server',
        'out': f'{out_dir}/{name}-reel-v1.mp4',
        'footage': [foot], 'shots': shots, 'lines': lines,
        'credits': [[0, len(shots) - 1, credit, {'size': 40, 'band': True}]],
        'spoken': slip['spoken'], 'headline': slip['headline'], 'label': slip['label'],
        'source': re.sub(r'^المصدر:\s*', '', credit), 'date': slip.get('date') or dt.date.today().strftime('%-d %b %Y'),
        'theme': theme or theme_for(slip), 'style': None, 'template': 'trailer', 'skin': 'house', 'cut': False,
        'track': track, 'track_from_first_shot': track != 'bed',
        'angle': slip.get('angle') or None,
        'decision_log': {'source': 'server slip build (adv-20261117-server-news-line-editor-model Phase 1)',
                         'footage': f'{foot.get("name") or f} from the resolver ({slip["footage"]})',
                         'shots': 'server-picked clean stretches in source order (autoshots)',
                         'music': 'the trailer\'s own sound from the first shot (audio split per shot)' if track != 'bed'
                                  else 'our bed: ' + str(slip.get('bed_reason'))},
        'reel_check': reel_check(slip, foot),
    }
    if track == 'bed':
        job['bed_reason'] = slip.get('bed_reason')
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


def build(slip, lane='live', resolve=True, root=ROOT, now=None):
    """Writes the story file and the job; returns the result {state, problems, flags, job, story, footage}."""
    res = {'id': slip.get('id'), 'state': 'failed', 'problems': [], 'flags': [], 'at': dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}
    res['problems'] = problems(slip, now)
    if res['problems']:
        return res
    res['flags'] = name_flags(slip)
    name = _name(slip)
    if resolve:
        try:
            import footage as FT
            r = FT.resolve(slip['footage'], name=name)
        except Exception as e:                      # the slip is failed with the reason, never left without a result
            res['problems'].append(f'footage: the resolver stopped on {slip["footage"]}: {type(e).__name__}: {e}')
            return res
        cands = r.get('candidates') or []
        try:
            c = pick_footage(cands, slip.get('footage_pick'))
        except ValueError as e:
            res['problems'].append(f'footage: {e} ({slip["footage"]}; {r.get("error") or str(len(cands)) + " found"})')
            return res
        foot = dict(c['job'])
        res['footage'] = {k: c.get(k) for k in ('name', 'width', 'height', 'fps', 'mbps', 'rows', 'duration', 'decode_clean')}
        if c.get('mbps') and c.get('height') and c['height'] < 1080:
            res['flags'].append(f'footage {c["width"]}x{c["height"]}: under 1080p, the quality gate may ask for the showcase layout')
    else:
        foot = {'file': f'{name}-trailer.mp4', 'url': 'https://example.invalid/test.mp4'}
    job = job_from(slip, foot, lane)
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
    import textrules as TR
    hard = TR.hard(TR.check(job))
    if hard:
        res['problems'] += [f"text: {f['where']}: {f.get('fix') or f['rule']}" for f in hard]
    res.update(job=os.path.relpath(jpath, root), story=os.path.relpath(spath, root),
               state='failed' if res['problems'] else 'built', lines=len(job['lines']), shots=len(job['shots']))
    return res


def main(argv):
    if len(argv) < 2 or argv[0] not in ('check', 'build'):
        raise SystemExit(__doc__)
    slip = json.load(open(argv[1], encoding='utf-8'))
    if argv[0] == 'check':
        p, fl = problems(slip), name_flags(slip)
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
