"""The Game Awards 2026 nominees event kit (Mohammad, 15 Nov 2026).

The show reads its nominees live on Tue 17 Nov at 09:00 PT (21:00 Dubai). Everything that does not depend on the names
is prepared here ahead of time: each likely Game of the Year nominee's official trailer, its clean shots (read by the
server's shots mode, jobs/prerender/tga-2026-pool-*.json), its credit, its title as the publisher writes it and a box
tile for the most-nominated card. On the night only the names (and, for the second Reel, the counts) are typed in, in
the order The Game Awards reads them, from the official stream or thegameawards.com only.

    python3 templates/tgakit.py list                                  the candidates and whether each has its shots
    python3 templates/tgakit.py shots <shots.json> [...]              merge a shots read (prerender mode shots) into the kit
    python3 templates/tgakit.py add <key> --title T --credit C (--steam APP:PREFIX | --url URL) --tile NAME
                                                                      a nominee outside the pool (then run its shots read)
    python3 templates/tgakit.py goty <key,key,...> [--hook KEY] [--out jobs/live/tga-2026-goty-nominees.json]
    python3 templates/tgakit.py most <key:count,key:count,...> [--out jobs/live/tga-2026-most-nominated.json]
    python3 templates/tgakit.py cat <slug> <key|Name::note::tile,...> [--ground KEY] [--title AR]   X and Threads, one category
    python3 templates/tgakit.py main <slug,slug,...> [--hook KEY]     Instagram, the main categories in one Reel

`goty` writes the list Reel: the headline over the first nominee's footage, then each nominee on its own trailer with its
name as the line and «المرشح n من N · المصدر: ...» as the credit, then the ceremony date on a closing picture; our bed.
`most` writes the clipcard: a hook on the leader's footage, its name, the ranking card (3 to 5 rows, counts only there),
the ceremony date on the leader's footage again. Both print the X, Threads and Instagram texts beside the job, and both
refuse a key that has no shots yet. Nothing here posts or renders.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'newsroom', 'kits', 'tga-2026.json')
SOURCE = 'ذا غيم أووردز (The Game Awards)'
SOURCE_URL = 'https://thegameawards.com/nominees'
CEREMONY = 'يُعلن الفائز في حفل 10 ديسمبر'          # thegameawards.com: "TGA Returns December 10, 2026" (read 15 Nov)
ITEM_SECS = 3.0
HOOK_SECS = 3.6
CLOSE_SECS = 3.0


def load():
    return json.load(open(KIT, encoding='utf-8'))


def save(kit):
    with open(KIT, 'w', encoding='utf-8') as fh:
        json.dump(kit, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


def _stretches(read):
    """Clean stretches of one file's shots read, longest first, each [start, secs, focus]."""
    out = []
    for s in read.get('shots', []):
        secs = min(float(s['end'] - s['start']) if s.get('end') else float(s.get('secs') or 0), 6.0)   # a long title needs > 4 s
        out.append([round(float(s['start']), 2), round(secs, 2), s.get('focus')])
    return out


def merge_shots(kit, reads):
    """item: the longest clean stretch of at least ITEM_SECS nearest the trailer's middle; hook and close: the next two
    distinct stretches (the hook only matters for the first nominee, the close for the first and the leader)."""
    by_file = {c['footage']['file']: k for k, c in kit['candidates'].items()}
    for r in reads:
        k = by_file.get(r.get('file'))
        if not k:
            print(f'tgakit: {r.get("file")} is not in the kit; skipped')
            continue
        st = _stretches(r)
        dur = float(r.get('duration') or 120)
        ok = [s for s in st if s[1] >= ITEM_SECS] or sorted(st, key=lambda s: -s[1])[:1]
        if not ok:
            print(f'tgakit: {k}: no clean stretch at all: read another official trailer')
            kit['candidates'][k]['shots'] = None
            continue
        ok.sort(key=lambda s: abs(s[0] + s[1] / 2 - dur / 2))
        item = ok[0]
        rest = [s for s in ok[1:] if abs(s[0] - item[0]) > 4]
        hook = rest[0] if rest else None
        close = rest[1] if len(rest) > 1 else None
        kit['candidates'][k]['shots'] = {'item': item, 'hook': hook, 'close': close, 'stretches': st,
                                         'picture_start': r.get('picture_start'), 'decode_clean': r.get('decode_clean'),
                                         'read': f"{len(st)} clean stretches, {len(r.get('rejected', []))} rejected"}
        print(f'tgakit: {k}: item {item[0]} s ({item[1]} s), hook {hook and hook[0]}, close {close and close[0]}'
              + ('' if r.get('decode_clean', True) else '  DECODE NOT CLEAN'))
    return kit


def _need(kit, keys, roles):
    c = kit['candidates']
    bad = [k for k in keys if k not in c]
    if bad:
        raise SystemExit(f'tgakit: not in the kit: {", ".join(bad)}. Add each with `tgakit.py add` and run its shots read')
    for k in keys:
        sh = c[k].get('shots') or {}
        miss = [r for r in roles(k) if not sh.get(r)]
        if miss:
            raise SystemExit(f'tgakit: {k} has no {"/".join(miss)} shot yet (run the prerender shots read, then `shots`)')


def _read(text):
    """reel.read_secs plus the line's entry: the shot a line sits on lasts this long at least."""
    return max(2.2, 0.5 + len(text.replace('\n', ' ')) / 14) + 0.45


def _shot(c, role, secs, line=None):
    s = c['shots'][role]
    if line and role == 'item' and s[1] < _read(line):          # a longer clean stretch that holds the line, if any
        fit = [x for x in c['shots'].get('stretches', []) if x[1] >= _read(line)]
        if fit:
            s = max(fit, key=lambda x: x[1])
    if line:                                                     # at least the reading time; up to `secs` when the stretch allows
        secs = max(round(_read(line), 2), min(secs, s[1]))
        if secs > s[1] + 1e-6:
            raise SystemExit(f"tgakit: {c['title']}: the line needs {secs} s and the clean stretch at {s[0]} s is {s[1]} s; "
                             'pick a longer stretch from the shots read (kit file) or shorten the line')
    return [c['footage']['file'], s[0], min(secs, s[1]), None]   # focus null: the render's autofocus (YOLO) frames it


def _base(name, story, template, kind):
    return {'name': name, 'story': story, 'kind_news': kind, 'built_by': 'production-1', 'render_lane': 'server',
            'out': f'cards/2026-11/{name}-reel-v1.mp4', 'label': 'رسمي', 'source': SOURCE, 'date': '17 Nov 2026',
            'theme': 'gold', 'style': None, 'template': template, 'skin': 'house', 'cut': True, 'track': 'bed',
            'bed_reason': ('several games in one Reel, each on its own official trailer: no single trailer stretch runs '
                           'under all of them, and cutting each trailer\'s own sound at every cut would jump; our bed '
                           'under the whole cut (event kit, 15 Nov)'),
            'genre': ['industry/hardware'], 'platform': 'multi', 'beat': 'event', 'subject_person': None,
            'sensitive': 'none'}


def _lowres(c, keys):
    """lowres_ok for the job: each chosen nominee whose only official copy is under 960 rows names the copies checked
    (kit field `lowres_ok`, reel.lowres_reason); None when every source is large enough."""
    why = [f"{c[k]['title']}: {c[k]['lowres_ok']}" for k in keys if c[k].get('lowres_ok')]
    return '; '.join(why) or None


def _reel_check(names, when):
    return {
        'SOURCE: primary read in full': f'yes: names read from the official stream and {SOURCE_URL} at {when}',
        'SOURCE: not already posted': 'yes: ledger find recorded in the story file; the 14 Nov watch-guide lead was released unbuilt',
        'SOURCE: age': 'yes: announced tonight, posted at once (T0)',
        'ANGLE: hook, why now, what it means, payoff': 'yes: in the story file angle',
        'STORY TYPE: EVENT': 'yes: the ceremony date (10 Dec) on the closing line; Dubai time not announced yet, so not stated',
        'STORY: one spoken paragraph first': 'yes: "spoken" in the job, lines cut from it in order',
        'STORY: names match names-ar.md': 'yes: games in English as the publishers write them; ذا غيم أووردز (The Game Awards) added to names-ar.md 15 Nov',
        'SOUND: our bed with reason': 'yes: bed_reason in the job',
        'PICTURE: footage first, official trailers': 'yes: every nominee on its own official trailer: ' + ', '.join(names),
        'PICTURE: credit on every clip': 'yes: one credit per shot naming the publisher, with the n of N counter',
        'PICTURE: nothing graphic': 'yes: stretches read by the server shots mode; the director looks once at the frames',
    }


def goty(kit, keys, when='TODO time read (Z)', hook=None):
    """`hook` (a key among the nominees): whose hook and close shots open and close the Reel; default the first read.
    The dry run of 17 Nov showed Resident Evil Requiem's hook near black under the headline: on the night the cover takes
    the nominee whose hook stops the scroll, while the nominees keep the order read."""
    hook = hook or keys[0]
    if hook not in keys:
        raise SystemExit(f'tgakit: --hook {hook} is not one of the nominees given')
    _need(kit, keys, lambda k: ('item', 'hook', 'close') if k == hook else ('item',))
    c = kit['candidates']
    n = len(keys)
    first = c[hook]
    shots = [_shot(first, 'hook', HOOK_SECS)]
    lines, credits = [], [[0, 0, f"المصدر: {first['credit']}"]]
    for i, k in enumerate(keys, 1):
        shots.append(_shot(c[k], 'item', ITEM_SECS, c[k]['line']))
        lines.append([i, i, [[c[k]['line'], {'size': 54}]]])
        credits.append([i, i, f"المرشح {i} من {n} · المصدر: {c[k]['credit']}"])
    shots.append(_shot(first, 'close', CLOSE_SECS, CEREMONY))
    lines.append([n + 1, n + 1, [[CEREMONY, {'size': 54}]]])
    credits.append([n + 1, n + 1, f"المصدر: {first['credit']}"])
    names = [c[k]['title'] for k in keys]
    spoken = (f'أعلن حفل {SOURCE} المرشحين لجائزة لعبة العام 2026، وهم '
              + ' و'.join(c[k]['line'] for k in keys) + '. و' + CEREMONY + '.')
    job = _base('tga-2026-goty-nominees', '2026-11-17-tga-2026-goty-nominees', 'list', 'awards')
    footage = [c[k]['footage'] for k in keys]
    job.update({'footage': footage, 'shots': shots, 'lines': lines, 'credits': credits,
                'headline': 'المرشحون لجائزة\nلعبة العام 2026', 'spoken': spoken,
                'ground_footage': [first['footage']['file'], first['shots']['hook'][0]],
                'reel_check': _reel_check(names, when),
                'lowres_ok': _lowres(c, keys),
                'decision_log': {'hook': f"{first['title']} under the headline" + (' (first nominee read)' if hook == keys[0] else ' (--hook: the strongest opening shot; nominees in the order read)'),
                                 'items': 'one clean stretch per nominee from the server shots read, nearest the trailer middle',
                                 'close': f"{first['title']} again for the closing picture", 'music': 'our bed (bed_reason)'}})
    if not job['lowres_ok']:
        job.pop('lowres_ok')
    x = (f'هذه الألعاب المرشحة لجائزة لعبة العام في {SOURCE} 2026، ويُعلن الفائز في حفل 10 ديسمبر.')
    ig = (f'المرشحون لجائزة لعبة العام في {SOURCE} 2026.\n\n'
          'أعلن الحفل قائمة المرشحين لجائزة لعبة العام: '
          + '، و'.join(names) + '.\n\nويُعلن الفائز في حفل 10 ديسمبر.\n\n#ألعاب #أخبار_الألعاب #TheGameAwards #GOTY')
    return job, {'x': x, 'threads': x + f'\n\nالمصدر: {SOURCE}', 'instagram': ig,
                 'pinned': f'المصدر: الموقع الرسمي لحفل {SOURCE}'}


def most(kit, pairs, when='TODO time read (Z)'):
    keys = [k for k, _ in pairs]
    if not 3 <= len(pairs) <= 5:
        raise SystemExit('tgakit: the ranking card holds 3 to 5 games (6 rows run into the story lines; server text check 15 Nov)')
    _need(kit, keys[:1], lambda k: ('hook', 'item', 'close'))
    _need(kit, keys, lambda k: ())
    c = kit['candidates']
    lead = c[keys[0]]
    rows = []
    for rank, (k, n) in enumerate(pairs, 1):
        rows.append({'rank': str(rank), 'name': c[k]['title'], 'value': str(n), 'unit': 'ترشيحات' if 3 <= int(n) <= 10 else 'ترشيحًا',
                     'image': c[k]['tile'], 'n': int(n)})
    gfx = 'tga-2026-most-nominated-gfx-ranking.png'
    shots = [_shot(lead, 'hook', HOOK_SECS), _shot(lead, 'item', ITEM_SECS, f"تتصدر {lead['line']}"), [gfx, None, 5.0, None],
             _shot(lead, 'close', CLOSE_SECS, 'ويُعلن الفائزون في حفل 10 ديسمبر')]
    line1 = f"تتصدر {lead['line']}"
    job = _base('tga-2026-most-nominated', '2026-11-17-tga-2026-most-nominated', 'clipcard', 'results')
    job.update({'footage': [lead['footage']], 'shots': shots,
                'lines': [[1, 1, [[line1, {'size': 54}]]], [3, 3, [['ويُعلن الفائزون في حفل 10 ديسمبر', {'size': 54}]]]],
                'credits': [[0, 1, f"المصدر: {lead['credit']}"], [2, 2, f'المصدر: {SOURCE}'], [3, 3, f"المصدر: {lead['credit']}"]],
                'headline': 'الأكثر ترشيحًا\nفي ذا غيم أووردز 2026',
                'spoken': f'{line1} القائمة بأكبر عدد من الترشيحات في {SOURCE} 2026. ويُعلن الفائزون في حفل 10 ديسمبر.',
                'gfx': [{'file': gfx, 'kind': 'ranking', 'rows': rows, 'animate': True}],
                'pace_ok': ('the 5 s ranking card is animated: its rows enter one by one, about 0.55 s each from the last rank '
                            'up, so the longest still stretch on it is under 3 s; the pace check reads the card as one still '
                            '(dry run 17 Nov, render run 1217)'),
                'ground_footage': [lead['footage']['file'], lead['shots']['item'][0]],
                'reel_check': _reel_check([c[k]['title'] for k in keys], when),
                'lowres_ok': _lowres(c, keys[:1]),
                'decision_log': {'hook': f"{lead['title']} (most nominations)", 'card': 'ranking, counts only on the card',
                                 'close': f"{lead['title']} again", 'music': 'our bed (bed_reason)'}})
    if not job['lowres_ok']:
        job.pop('lowres_ok')
    x = f"تتصدر {lead['line']} ترشيحات {SOURCE} 2026 بـ{rows[0]['value']} {rows[0]['unit']}، حسب القائمة الرسمية."
    return job, {'x': x, 'threads': x + f'\n\nالمصدر: {SOURCE}',
                 'instagram': (f"{lead['line']} هي الأكثر ترشيحًا في {SOURCE} 2026.\n\n"
                               + '\n'.join(f"لعبة {r['name']}: {r['value']} {r['unit']}" for r in rows)
                               + '\n\nويُعلن الفائزون في حفل 10 ديسمبر.\n\n#ألعاب #أخبار_الألعاب #TheGameAwards #GOTY')}


# ------------------------------------------------- event style (Mohammad, 17 Nov 2026): X and Threads get one short
# video per category as each is ready; Instagram gets one combined Reel of the main categories plus the GOTY Reel.
CATEGORIES = {          # The Game Awards' category names in Arabic (titles of the card and the headline)
    'direction': 'أفضل إخراج للعبة', 'narrative': 'أفضل سرد قصصي', 'art': 'أفضل إخراج فني',
    'score': 'أفضل موسيقى', 'audio': 'أفضل تصميم صوتي', 'performance': 'أفضل أداء تمثيلي',
    'accessibility': 'الابتكار في إمكانية الوصول', 'impact': 'ألعاب ذات أثر', 'ongoing': 'أفضل لعبة مستمرة',
    'community': 'أفضل دعم للمجتمع', 'indie': 'أفضل لعبة مستقلة', 'debut': 'أفضل أول لعبة مستقلة',
    'mobile': 'أفضل لعبة للهواتف', 'vr': 'أفضل لعبة واقع افتراضي أو معزز', 'action': 'أفضل لعبة أكشن',
    'actionadventure': 'أفضل لعبة أكشن ومغامرات', 'rpg': 'أفضل لعبة تقمص أدوار', 'fighting': 'أفضل لعبة قتال',
    'family': 'أفضل لعبة عائلية', 'simstrategy': 'أفضل لعبة محاكاة أو استراتيجية',
    'sportsracing': 'أفضل لعبة رياضة أو سباقات', 'multiplayer': 'أفضل لعبة متعددة اللاعبين', 'adaptation': 'أفضل اقتباس',
    'anticipated': 'اللعبة الأكثر ترقبًا',
}
ROW_STEP = 0.55          # cardgfx.ROW_STEP: one nominee row every this many seconds, in the order read


def _rows(kit, spec):
    """'key,key,Name::note::tile,...' -> (rows for the card, kit keys among them). A kit key takes its title, studio
    credit and tile; any other nominee is written as the show reads it, with an optional note (the game, for a
    performance) and tile."""
    c = kit['candidates']
    rows, keys = [], []
    for item in [x.strip() for x in spec.split(',') if x.strip()]:
        if item in c:
            rows.append({'name': c[item]['title'], 'note': c[item]['credit'], 'image': c[item].get('tile')})
            keys.append(item)
        else:
            parts = item.split('::')
            r = {'name': parts[0].strip()}
            if len(parts) > 1 and parts[1].strip():
                r['note'] = parts[1].strip()
            if len(parts) > 2 and parts[2].strip():
                r['image'] = parts[2].strip()
            rows.append(r)
    if not 3 <= len(rows) <= 6:
        raise SystemExit(f'tgakit: a category card holds 3 to 6 nominees, not {len(rows)}')
    return rows, keys


def _card_secs(n):
    return round(ROW_STEP * (n - 1) + 3.2, 2)        # the rows come in one by one, then the full list holds 3 s


def _fill_roles(kit, key):
    """A nominee read with only its item stretch (short trailers): the hook and close take its other clean stretches,
    longest first, never the item's own moment. Nothing changes when the read already has them."""
    sh = kit['candidates'][key].get('shots') or {}
    if not sh.get('item'):
        return
    used = [sh['item'][0]] + [sh[r][0] for r in ('hook', 'close') if sh.get(r)]
    spare = sorted([x for x in sh.get('stretches', []) if all(abs(x[0] - u) > 4 for u in used)], key=lambda x: -x[1])
    for r in ('close', 'hook'):                      # the close carries the ceremony line: it takes the longest
        if not sh.get(r) and spare:
            sh[r] = spare.pop(0)


def category(kit, slug, spec, ground=None, title=None, when='TODO time read (Z)'):
    """The X and Threads video for one category: the category over a nominee's footage, the nominees card on the same
    game's moving footage (rows in the order read), the ceremony date on a closing picture. `ground` is a kit key whose
    footage carries it: by default the first nominee that is in the kit (refused when none is: add one with `add`)."""
    title = title or CATEGORIES.get(slug)
    if not title:
        raise SystemExit(f'tgakit: no Arabic name for category {slug}; pass --title')
    rows, keys = _rows(kit, spec)
    if not ground:                                   # the first nominee read whose footage has all three stretches
        full = [k for k in keys if all((kit['candidates'][k].get('shots') or {}).get(r) for r in ('hook', 'item', 'close'))]
        ground = full[0] if full else (keys[0] if keys else None)
    if ground:
        _fill_roles(kit, ground)
    if not ground:
        raise SystemExit(f'tgakit: {slug}: no nominee is in the kit; pass --ground <key> (a nominee\'s footage) or add one')
    _need(kit, [ground], lambda k: ('hook', 'item', 'close'))
    c = kit['candidates']
    g = c[ground]
    name = f'tga-2026-cat-{slug}'
    gfx = f'{name}-gfx-nominees.png'
    secs = _card_secs(len(rows))
    shots = [_shot(g, 'hook', HOOK_SECS), [gfx, [g['footage']['file'], g['shots']['item'][0]], secs, None],
             _shot(g, 'close', CLOSE_SECS, CEREMONY)]
    credits = [[0, 0, f"المصدر: {g['credit']}"], [1, 1, f"القائمة: {SOURCE} · اللقطات: {g['credit']}"],
               [2, 2, f"المصدر: {g['credit']}"]]
    job = _base(name, f'2026-11-17-{name}', 'list', 'awards')
    job.update({'footage': [g['footage']], 'shots': shots, 'credits': credits,
                'lines': [[2, 2, [[CEREMONY, {'size': 54}]]]],
                'headline': f'المرشحون لجائزة\n{title}',
                'spoken': f'أعلن حفل {SOURCE} المرشحين لجائزة {title} لعام 2026. و{CEREMONY}.',
                'gfx': [{'file': gfx, 'kind': 'nominees', 'title': title, 'rows': rows, 'animate': True}],
                'ground_footage': [g['footage']['file'], g['shots']['item'][0]],
                'ground_seek': 'fixed',          # the card sits on the clean stretch the shots read passed (no burnt-in text)
                'pace_ok': (f'the {secs} s nominees card is animated: its rows enter one by one, {ROW_STEP} s apart, in the '
                            'order read, then the full list holds 3 s to be read'),
                'reel_check': _reel_check([r['name'] for r in rows], when),
                'decision_log': {'hook': f"{g['title']} (a nominee in this category) under the headline",
                                 'card': 'the nominees in the order read, names as the show writes them, no ranking',
                                 'close': f"{g['title']} again", 'music': 'our bed (bed_reason)'}})
    job['bed_reason'] = ('an awards category: the list card over one nominee\'s footage, our bed under the whole cut as '
                         'on every Reel of the event kit (15 Nov)')
    lr = _lowres(c, [ground])
    if lr:
        job['lowres_ok'] = lr
    names = [r['name'] for r in rows]
    x = (f'المرشحون لجائزة {title} في {SOURCE} 2026: ' + '، '.join(names) + '.')
    kit.setdefault('categories', {})[slug] = {'title': title, 'rows': rows, 'ground': ground, 'read_at': when}
    save(kit)
    return job, {'x': x, 'threads': x + f'\n\nالمصدر: {SOURCE}'}


def combined(kit, slugs, when='TODO time read (Z)', hook=None):
    """The Instagram Reel of the main categories: a hook over the first category's footage, then one nominees card per
    category, each on one of its own nominees' moving footage, then the ceremony date. Built from the categories already
    written with `cat` (the same rows, so the two never disagree)."""
    cats = kit.get('categories') or {}
    miss = [s for s in slugs if s not in cats]
    if miss:
        raise SystemExit(f'tgakit: write these categories with `cat` first: {", ".join(miss)}')
    if not 2 <= len(slugs) <= 8:
        raise SystemExit('tgakit: the combined Reel holds 2 to 8 categories')
    c = kit['candidates']
    for s_ in slugs:
        _fill_roles(kit, cats[s_]['ground'])
    if hook:                                          # the cover: a nominee whose opening shot stops the scroll
        _need(kit, [hook], lambda k: ())
        _fill_roles(kit, hook)
        _need(kit, [hook], lambda k: ('hook', 'close'))
    first = c[hook or cats[slugs[0]]['ground']]
    name = 'tga-2026-main-categories'
    shots = [_shot(first, 'hook', HOOK_SECS)]
    credits = [[0, 0, f"المصدر: {first['credit']}"]]
    gfx, footage, seen = [], [first['footage']], {first['footage']['file']}
    for i, s in enumerate(slugs, 1):
        cat = cats[s]
        g = c[cat['ground']]
        if g['footage']['file'] not in seen:
            footage.append(g['footage'])
            seen.add(g['footage']['file'])
        f = f'{name}-gfx-{s}.png'
        gfx.append({'file': f, 'kind': 'nominees', 'title': cat['title'], 'rows': cat['rows'], 'animate': True})
        shots.append([f, [g['footage']['file'], g['shots']['item'][0]], _card_secs(len(cat['rows'])), None])
        credits.append([i, i, f"القائمة: {SOURCE} · اللقطات: {g['credit']}"])
    n = len(slugs)
    shots.append(_shot(first, 'close', CLOSE_SECS, 'ويُعلن الفائزون في حفل 10 ديسمبر'))
    credits.append([n + 1, n + 1, f"المصدر: {first['credit']}"])
    job = _base(name, f'2026-11-17-{name}', 'list', 'awards')
    job.update({'footage': footage, 'shots': shots, 'credits': credits, 'gfx': gfx,
                'ground_footage': shots[1][1],
                'ground_seek': 'fixed',          # each card on its game's clean item stretch (no burnt-in text)
                'lines': [[n + 1, n + 1, [['ويُعلن الفائزون في حفل 10 ديسمبر', {'size': 54}]]]],
                'headline': 'أبرز ترشيحات\nذا غيم أووردز 2026',
                'spoken': (f'أعلن حفل {SOURCE} المرشحين لجوائز 2026، وهذه أبرز الفئات. ويُعلن الفائزون في حفل 10 ديسمبر.'),
                'pace_ok': ('each nominees card is animated: its rows enter one by one, '
                            f'{ROW_STEP} s apart, then the full list holds 3 s; every card sits on a different game\'s footage'),
                'reel_check': _reel_check([cats[s]['title'] for s in slugs], when),
                'decision_log': {'hook': f"{first['title']} under the headline",
                                 'cards': 'one card per category, rows as read, each on one of its own nominees\' footage',
                                 'music': 'our bed (bed_reason)'}})
    lr = _lowres(c, list({cats[s]['ground'] for s in slugs}))
    if lr:
        job['lowres_ok'] = lr
    body = '\n\n'.join(f"{cats[s]['title']}: " + '، '.join(r['name'] for r in cats[s]['rows']) + '.' for s in slugs)
    ig = (f'أبرز ترشيحات {SOURCE} 2026.\n\nأعلن الحفل قوائم المرشحين، وهذه أبرز الفئات:\n\n{body}\n\n'
          'ويُعلن الفائزون في حفل 10 ديسمبر.\n\n#ألعاب #أخبار_الألعاب #TheGameAwards #GOTY')
    return job, {'instagram': ig, 'pinned': f'المصدر: الموقع الرسمي لحفل {SOURCE}'}


def _story(job, title_en):
    """A story file for a category job, cloned from the GOTY story (same source, label and angle shape)."""
    base = os.path.join(ROOT, 'newsroom', 'stories', '2026-11-17-tga-2026-goty-nominees.json')
    p = os.path.join(ROOT, 'newsroom', 'stories', job['story'] + '.json')
    if os.path.exists(p):
        return p
    st = json.load(open(base, encoding='utf-8'))
    st.update({'id': job['story'], 'title': f'The Game Awards 2026: {title_en} nominees (event style)',
               'template': 'list', 'kind': 'awards'})
    st['angle'] = dict(st.get('angle') or {}, hook=f'the nominees for {title_en}, named the moment The Game Awards reads them')
    st['notes'] = list(st.get('notes') or []) + ['Event style (Mohammad, 17 Nov 2026): X and Threads get one video per '
                                                 'category as each is ready; Instagram gets the combined main-categories '
                                                 'Reel and the GOTY Reel']
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(st, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    return p


def _write(job, texts, out):
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(job, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    side = out.replace('.json', '-texts.json').replace('jobs/live/', 'jobs/prerender/')
    with open(side, 'w', encoding='utf-8') as fh:
        json.dump(texts, fh, ensure_ascii=False, indent=1)
    print(f'tgakit: wrote {out} and {side}')
    for k, v in texts.items():
        print(f'--- {k}\n{v}')


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    kit = load()
    cmd, rest = argv[0], argv[1:]
    out = rest[rest.index('--out') + 1] if '--out' in rest else None
    when = rest[rest.index('--when') + 1] if '--when' in rest else 'TODO time read (Z)'
    if cmd == 'list':
        for k, c in kit['candidates'].items():
            sh = c.get('shots') or {}
            print(f"{k:12} {c['title'][:40]:40} item {sh.get('item')} hook {bool(sh.get('hook'))} close {bool(sh.get('close'))}")
    elif cmd == 'shots':
        reads = []
        for p in rest:
            d = json.load(open(p, encoding='utf-8'))
            reads += d if isinstance(d, list) else [d]
        save(merge_shots(kit, reads))
    elif cmd == 'add':
        a = dict(zip(rest[1::2], rest[2::2]))
        k = rest[0]
        foot = {'file': f'tga26-{k}.mp4'}
        if '--steam' in a:
            app, pre = a['--steam'].split(':', 1)
            foot.update(steam=int(app), trailer=pre, start=0, seconds=240)
        else:
            foot['url'] = a['--url']
        kit['candidates'][k] = {'title': a['--title'], 'line': f"لعبة {a['--title']}", 'credit': a['--credit'],
                                'tile': a.get('--tile'), 'footage': foot, 'shots': None}
        save(kit)
        print(f'tgakit: added {k}; run its shots read next')
    elif cmd == 'goty':
        keys = [k.strip() for k in rest[0].split(',') if k.strip()]
        job, texts = goty(kit, keys, when, rest[rest.index('--hook') + 1] if '--hook' in rest else None)
        _write(job, texts, out or os.path.join(ROOT, 'jobs', 'live', 'tga-2026-goty-nominees.json'))
    elif cmd == 'most':
        pairs = [(p.split(':')[0].strip(), int(p.split(':')[1])) for p in rest[0].split(',')]
        job, texts = most(kit, pairs, when)
        _write(job, texts, out or os.path.join(ROOT, 'jobs', 'live', 'tga-2026-most-nominated.json'))
    elif cmd == 'cat':
        slug = rest[0]
        opt = lambda k: rest[rest.index(k) + 1] if k in rest else None
        job, texts = category(kit, slug, rest[1], opt('--ground'), opt('--title'), when)
        _story(job, slug)
        _write(job, texts, out or os.path.join(ROOT, 'jobs', 'live', job['name'] + '.json'))
    elif cmd == 'main':
        slugs = [k.strip() for k in rest[0].split(',') if k.strip()]
        job, texts = combined(kit, slugs, when, rest[rest.index('--hook') + 1] if '--hook' in rest else None)
        _story(job, 'main categories')
        _write(job, texts, out or os.path.join(ROOT, 'jobs', 'live', job['name'] + '.json'))
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
