"""Template by story kind, skin by genre, franchise by game (audit of 21 Nov 2026, items 1 and 3; advisor, agreed with
Mohammad).

Of the 42 Reels published 19 to 21 Nov, 37 were trailer Reels and all 42 wore the house skin: the slip lane wrote
"template": "trailer" and "skin": "house" into every job. The slip now states its kind and the server picks:

  numbers   sales, scores, charts, player counts, financial results   -> template numbers (a figure card on the
                                                                          game's own moving footage, between footage)
  person    interview, quote, hire, departure                         -> template people (photo window with name
                                                                          plate on frame 0, then the story on footage)
  debate    readers argue (a closing question)                        -> template debate (hook and fact, one view
                                                                          per beat, the question last)
  trailer   reveal, date, delay, update, deal, free release, launch   -> template trailer

A slip with no kind, or a generic one (news, report, business), is classified from its text; nothing here ever fails a
job: an unclear story is a trailer Reel. Explicit specific kinds win (sales, results, players, quote, people, cast,
controversy); the person and numbers signals in the text win over a generic or trailer kind, because editors wrote
"reveal" on interviews (Persona 6's producer, 20 Nov).

    import storykind as SK
    SK.classify(slip)          -> ('numbers' | 'person' | 'debate' | 'trailer', reason)
    SK.figure(slip)            -> {'value', 'label', 'note'} or None   (the card's figure, read from the slip's text)
    SK.person(slip)            -> {'name', 'role'} or None              (the plate's two rows, both opening in Arabic)
    SK.skin_for(genre, game)   -> ('scifi' | 'fantasy' | 'house', reason)

    python3 templates/storykind.py <slip.json> [...]     prints the class, figure, person and skin of each slip
"""
import json
import re
import sys

TEMPLATE_OF = {'numbers': 'numbers', 'person': 'people', 'debate': 'debate', 'trailer': 'trailer'}

# formats.NEWS_MAP kinds (and the slip's own words) to the four classes. None: a generic kind, read the text.
KIND_CLASS = {
    'sales': 'numbers', 'results': 'numbers', 'players': 'numbers', 'reviews': 'numbers', 'scores': 'numbers',
    'charts': 'numbers', 'chart': 'numbers', 'famitsu': 'numbers', 'top': 'numbers', 'numbers': 'numbers',
    'quote': 'person', 'people': 'person', 'person': 'person', 'cast': 'person', 'interview': 'person',
    'hire': 'person', 'departure': 'person', 'layoffs': None,
    'controversy': 'debate', 'debate': 'debate',
    'reveal': 'trailer', 'launch': 'trailer', 'date': 'trailer', 'delay': 'trailer', 'update': 'trailer',
    'price': 'trailer', 'deal': 'trailer', 'free': 'trailer', 'expansion': 'trailer', 'crossover': 'trailer',
    'preorder': 'trailer', 'beta': 'trailer', 'event': 'trailer', 'edition': 'trailer',
    'news': None, 'report': None, 'business': None, None: None, '': None,
}
EXPLICIT = ('numbers', 'person', 'debate')

DIGIT = r'\d[\d,.]*'
SCALE = ('مليار', 'مليون', 'ألف', 'آلاف')
UNITS = ('دولار', 'يورو', 'ين', 'درهم', 'ريال', 'جنيه', 'نسخة', 'نسخ', 'لاعب', 'لاعبًا', 'لاعبا', 'مستخدم', 'مراجعة',
         'تقييم', 'تقييمًا', 'بالمئة', 'بالمائة', '%')
NUM_WORDS = ('مبيعات', 'مبيعًا', 'مبيعا', 'باعت', 'بيعت', 'بيع', 'إيرادات', 'الإيرادات', 'أرباح', 'خسارة', 'حجوزات',
             'الحجوزات', 'نتائج', 'إنفاق', 'الإنفاق', 'لاعب', 'لاعبين', 'اللاعبين', 'متزامن', 'تقييم', 'التقييم',
             'ميتاكريتيك', 'الأكثر مبيعًا', 'تصدرت', 'تتصدر', 'الصدارة', 'فاميتسو', 'المركز الأول', 'قائمة', 'نسخة', 'نسخ', 'تحميل')
ROLES = ('المخرج', 'مخرج', 'المنتج', 'منتج', 'المنتج العام', 'الرئيس التنفيذي', 'رئيس', 'رئيسة', 'المؤسس', 'مؤسس',
         'المؤسس المشارك', 'مصمم', 'مصممة', 'كاتب', 'كاتبة', 'الكاتب', 'الكاتبة', 'الملحن', 'ملحن', 'مبتكر', 'مبتكرة',
         'المدير', 'مدير', 'مديرة', 'نائب الرئيس', 'الممثل', 'الممثلة', 'ممثل', 'ممثلة', 'المطور', 'رسام', 'الرسام')
SPEECH = ('قال', 'قالت', 'يقول', 'تقول', 'صرّح', 'صرح', 'صرّحت', 'أكد', 'أكدت', 'كشف', 'كشفت', 'نقل', 'مقابلة',
          'حوار', 'منشور', 'منشوره', 'منشورها', 'غادر', 'غادرت', 'يغادر', 'تغادر', 'انضم', 'انضمت', 'ينضم', 'تنضم',
          'استقال', 'استقالت', 'عُيّن', 'عين', 'عيّنت', 'يتقاعد', 'تقاعد', 'احتفل', 'احتفلت', '«')
QUESTION = ('برأيك', 'ما رأيك', 'شاركنا رأيك', 'هل تتفق', 'أيّ', 'أي التقييمين')

LABELS = (('خسارة', 'الخسارة'), ('أرباح', 'الأرباح'), ('حجوزات', 'الحجوزات'), ('إيرادات', 'الإيرادات'),
          ('إنفاق', 'الإنفاق'), ('مبيعات', 'المبيعات'), ('باعت', 'المبيعات'), ('بيعت', 'المبيعات'),
          ('متزامن', 'اللاعبون في وقت واحد'), ('لاعب', 'اللاعبون'), ('تقييم', 'التقييم'), ('نسخة', 'المبيعات'),
          ('نسخ', 'المبيعات'), ('تحميل', 'التحميلات'))


def _text(slip):
    return ' '.join(str(slip.get(k) or '') for k in ('headline', 'spoken')).replace('\n', ' ')


def _sentences(text):
    import textrules as _TR                    # never inside a name or an abbreviation (25 Nov 2026)
    return [s.strip() for s in _TR.split_sentences(text, keep=True) if s.strip()]


def _has(text, words):
    return any(re.search(r'(?:^|[\s«(،,.:و])' + re.escape(w) + r'(?=$|[\s»)،,.:؛])', text) or (w in ('«', '%') and w in text)
               for w in words)


def _figures(text):
    """Figures with a scale or unit word after them: '3.79 مليار دولار', '254.5 مليون يورو', '100,000 نسخة'."""
    out = []
    for m in re.finditer(r'(' + DIGIT + r')\s*((?:' + '|'.join(SCALE) + r')(?=$|[\s،,.])\s*)?((?:' + '|'.join(re.escape(u) for u in UNITS)
                         + r')(?=$|[\s،,.؛)»]))?', text):
        num, scale, unit = m.group(1).rstrip('.,'), (m.group(2) or '').strip(), (m.group(3) or '').strip()
        if scale or unit:
            out.append((m.start(), num, scale, unit))
    return out


def numbers_signal(slip):
    text = _text(slip)
    head = str(slip.get('headline') or '').replace('\n', ' ')
    figs = _figures(text)
    money_or_count = [f for f in figs if f[3] not in ('بالمئة', 'بالمائة', '%') or f[2]]
    words = _has(text, NUM_WORDS)
    if _figures(head) and (words or any(f[2] for f in _figures(head))):
        return True, 'a figure in the headline (' + ' '.join(x for x in _figures(head)[0][1:] if x) + ')'
    if words and money_or_count and _has(head, NUM_WORDS):
        return True, 'a sales or results word in the headline and a figure in the story'
    return False, ''


def person_signal(slip):
    head = str(slip.get('headline') or '').replace('\n', ' ')
    sents = _sentences(str(slip.get('spoken') or ''))
    first = sents[0] if sents else ''
    lead = head + ' ' + first
    role = next((r for r in sorted(ROLES, key=len, reverse=True) if _has(lead, (r,))), None)
    if not role:
        return False, ''
    if _has(str(slip.get('spoken') or ''), SPEECH) or '«' in str(slip.get('spoken') or ''):
        return True, f'a person is the subject: «{role}» in the headline or first sentence, with what they said or did'
    return False, ''


def classify(slip):
    """(class, reason). Never raises: anything unclear is a trailer Reel."""
    try:
        kind = str(slip.get('kind') or '').strip().lower()
        k = KIND_CLASS.get(kind, 'trailer' if kind else None)
        spoken = str(slip.get('spoken') or '')
        if k == 'debate' or (k is None and _has(spoken.split('.')[-1] if spoken else '', QUESTION) and 'برأيك' in spoken):
            return 'debate', f'kind {kind or "none"}' + ('' if k == 'debate' else ': a closing question to the reader')
        if k in EXPLICIT:
            return k, f'kind {kind}'
        p, pr = person_signal(slip)
        if p:
            return 'person', pr + (f' (kind {kind} read from the text)' if kind else '')
        n, nr = numbers_signal(slip)
        if n:
            return 'numbers', nr + (f' (kind {kind} read from the text)' if kind else '')
        if k == 'trailer':
            return 'trailer', f'kind {kind}'
        return 'trailer', f'kind {kind or "none"}: no figure or person leads the story, so a plain announcement'
    except Exception as e:                       # noqa: BLE001  never fail a job on the classifier
        return 'trailer', f'classifier error, trailer kept: {e}'


def figure(slip):
    """The card's figure: the first figure in the headline, else in the story; value is the number with its scale word,
    note the unit, label the sales or results word that names it. None when there is no figure."""
    if slip.get('figure'):
        f = dict(slip['figure'])
        return {'value': str(f.get('value')), 'label': f.get('label'), 'note': f.get('note')}
    head = str(slip.get('headline') or '').replace('\n', ' ')
    text = _text(slip)
    figs = _figures(head) or [f for f in _figures(text) if f[2] or f[3] not in ('بالمئة', 'بالمائة', '%')] or _figures(text)
    if not figs:
        return None
    if _has(text, ('ميتاكريتيك', 'تقييم', 'التقييم', 'النقاد')) and not _has(text, ('مبيعات', 'باعت', 'إيرادات')):
        sc = re.search(r'(?<![\d.])(\d{1,3}(?:\.\d)?)(?![\d.,])', head)
        if sc:
            return {'value': sc.group(1), 'label': 'التقييم', 'note': None}
    pos, num, scale, unit = figs[0]
    src = head if _figures(head) else text
    before = src[max(0, pos - 60):pos]
    label = None
    for w, lab in LABELS:
        if w in before or w in src[pos:pos + 40]:
            label = lab
            break
    if not label:
        for w, lab in LABELS:
            if w in text:
                label = lab
                break
    value = f'{num} {scale}'.strip()
    note = unit if unit and unit not in ('%',) else None
    if unit in ('%',):
        value, note = num, 'بالمئة'
    if note in ('لاعبًا', 'لاعبا'):
        note = 'لاعب'
    return {'value': value, 'label': label, 'note': note}


NAME = r'([A-Z][\w.\'-]+(?:\s+[A-Z][\w.\'-]+){0,3})'
STOP = r'(?=\s+(?:قال|قالت|أن|إن|احتفل|احتفلت|غادر|غادرت|يغادر|تغادر|ينضم|تنضم|في\s+يو|عن)\b|[،,.:؛«]|$)'


def _plate_name(ar, latin):
    """People Reels without the person (Mohammad, 22 Nov 2026, item 3): the plate always names the person; the Arabic
    form only when names-ar lists them, else the Latin as given."""
    try:
        import slip as _S
        table = _S._names_table()
    except Exception:                                   # noqa: BLE001
        table = {}
    known = table.get((latin or '').strip().lower())
    if known:
        return known
    return (latin or ar or '').strip()


def person(slip):
    """{'name', 'role'}: the plate's two rows. Row one is the person: their Arabic name, or the role word with a Latin
    name («مصمم الألعاب Masahiro Sakurai»), or the role alone when no name is given; row two is the role as the story
    words it («رئيسة السرد في لعبة Clair Obscur»), never a game the person did not make (the CD Projekt co-CEO talking
    about GTA VI is not «لعبة GTA VI»). Both rows open on an Arabic word. The slip's own "person" wins."""
    if isinstance(slip.get('person'), dict) and slip['person'].get('name'):
        p = slip['person']
        return {'name': p['name'], 'role': p.get('role') or '', 'photo': p.get('photo'), 'credit': p.get('credit'),
                'focus': p.get('focus')}
    text = str(slip.get('spoken') or '') + ' . ' + str(slip.get('headline') or '').replace('\n', ' ')
    for r in sorted(ROLES, key=len, reverse=True):
        for m in re.finditer(r'(?:^|[\s«(،,.])' + re.escape(r) + r'(?=[\s،,.])', text):
            tail = text[m.end():m.end() + 120]
            mq = re.match(r'((?:\s+(?!في\b|لعبة\b|استوديو\b|شركة\b)[^\sA-Za-z،,.]+)?)\s+' + NAME, tail)
            if mq:                                                   # «مصمم الألعاب Masahiro Sakurai»
                return {'name': _plate_name(None, mq.group(2)), 'role': (r + mq.group(1)).strip(), 'latin': mq.group(2)}
            ph = re.match(r'(.{0,70}?)' + STOP, tail)
            role = (r + (ph.group(1) if ph else '')).strip()
            role = re.sub(r'\s+', ' ', role)
            after = tail[ph.end():] if ph else ''
            ma = re.match(r'\s*[،,]\s*(?:([ء-ي][^\s(،,]*(?:\s+[ء-ي][^\s(،,]*){0,3})\s*\(\s*)?' + NAME,
                          after)
            if ma:                                                   # «منتج لعبة X، كاتسوهيرو هارادا (Katsuhiro Harada)،»
                return {'name': _plate_name(ma.group(1), ma.group(2)), 'role': role, 'latin': ma.group(2)}
            head = text[max(0, m.start() - 50):m.start()]
            mb = re.search(r'([^\s،,.]+(?:\s+[^\s،,.]+)?)\s*[،,]\s*$', head)  # «جينيفر سفيدبيرغ-ين، رئيسة السرد»
            if mb:
                who = re.sub(r'^(?:غادرت|غادر|قال|قالت|أكد|أكدت|انضم|انضمت|أن|إن)\s+', '', mb.group(1).strip())
                if who and re.match(r'[\u0621-\u064A]', who) and who.split()[0] not in ('أن', 'إن', 'التي', 'الذي'):
                    return {'name': who, 'role': role}
            return {'name': role, 'role': ''}
    return None


# ---------------------------------------------------------------------------------------------- skin by genre
# skins.KITS are the two built kits (scifi, fantasy); military, horror, anime, retro, sports and cosy wait for theirs, so
# their genres take the house look. Single-game stories only; multi-game, industry, business and our series stay house.
SCIFI = ('sci-fi', 'scifi', 'science fiction', 'cyberpunk', 'space', 'mecha', 'futuristic', 'space sim', 'hero shooter')
FANTASY = ('rpg', 'jrpg', 'action rpg', 'fantasy', 'soulslike', 'souls-like', 'mmorpg', 'metroidvania', 'dungeon crawler',
           'arpg')
HOUSE_KINDS = ('business', 'results', 'sales', 'hardware', 'policy', 'weekly', 'gamepass', 'lineup', 'top', 'recap',
               'famitsu', 'awards')


def skin_for(genre, game=None, kind=None, label=None):
    """(kit, reason). Footage of one game wears its genre's kit; the house look is the fallback."""
    if label == 'عاجل':
        return 'house', 'عاجل keeps its crimson house look'
    if kind in HOUSE_KINDS and not game:
        return 'house', f'kind {kind} with no single game'
    if not game:
        return 'house', 'no single game in the story'
    gs = [str(g).strip().lower() for g in (genre if isinstance(genre, (list, tuple)) else [genre]) if g]
    if not gs:
        return 'house', 'no genre on the story'
    for g in gs:                                  # the primary genre decides; the second only when the first is neutral
        if g in SCIFI or any(w in g for w in ('sci-fi', 'cyber', 'space')):
            return 'scifi', f'genre {g}'
        if g in FANTASY or any(w in g for w in ('rpg', 'fantasy', 'souls')):
            return 'fantasy', f'genre {g}'
    return 'house', f'genre {gs[0]}: its kit is not built yet (skins.KITS scifi, fantasy)'


def report(slip):
    c, why = classify(slip)
    out = {'class': c, 'template': TEMPLATE_OF[c], 'why': why}
    if c == 'numbers':
        out['figure'] = figure(slip)
    if c == 'person':
        out['person'] = person(slip)
    out['skin'] = skin_for(slip.get('genre'), slip.get('game'), slip.get('kind'), slip.get('label'))
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        s = json.load(open(p))
        print(p.split('/')[-1], json.dumps(report(s), ensure_ascii=False))
