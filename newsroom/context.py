"""Backstory pages, newsroom/context/<slug>.md (adv-20261102-story-brief, part 2; sources addendum A of 2 Nov).

One page per franchise, company, platform or person we cover often, under 40 lines: facts from Wikidata (CC0, facts
only, each with its property, the item id and the retrieval date; never Wikipedia prose), then our own Reels on it
from the story ledger (date, chip, template, title), newest first. A brief reads the pages matching its story before
the angle is written; presubmit.py published appends one line to every matching page.

    python3 newsroom/context.py seed [slug ...]      # (re)write pages: Wikidata facts and our Reels from the ledger
    python3 newsroom/context.py match <story id>     # the pages a story touches
    python3 newsroom/context.py append <story id>    # one line on each matching page (presubmit.py published does it)
    python3 newsroom/context.py list

Entities live in ENTITIES below: slug, title, kind, the Wikidata item (checked by hand when added) and the patterns
that match a story's game, companies or title. Add one when a subject reaches about four stories. No network at
append or match; seed reads Wikidata only.
"""
import datetime
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
STORIES = ROOT / 'stories'
PAGES = ROOT / 'context'
MAX_REELS = 18
UA = 'dxb-context-seed/1.0 (games newsroom backstory pages; facts only)'

# slug: (title, kind, wikidata item, patterns). The items were entered on 5 Nov 2026 while the Wikidata query service
# was refusing requests (outage rate limit), so none is confirmed yet: `seed` writes facts only when the item's own
# English label matches the title (label_ok), and otherwise writes a line asking for the item to be checked. A wrong
# item is fixed here, never by editing a page.
ENTITIES = {
    'zelda':               ('The Legend of Zelda', 'series', 'Q12393', [r'\bzelda\b', r'ocarina']),
    'grand-theft-auto':    ('Grand Theft Auto', 'series', 'Q216995', [r'grand theft auto', r'\bgta\b']),
    'call-of-duty':        ('Call of Duty', 'series', 'Q209868', [r'call of duty', r'\bcod\b', r'modern warfare']),
    'final-fantasy':       ('Final Fantasy', 'series', 'Q16881', [r'final fantasy', r'\bffxiv\b', r'\bff7\b']),
    'cyberpunk':           ('Cyberpunk 2077', 'game', 'Q3182559', [r'cyberpunk']),
    'phantom-blade-zero':  ('Phantom Blade Zero', 'game', None, [r'phantom blade']),
    'arc-raiders':         ('ARC Raiders', 'game', None, [r'arc raiders']),
    'warcraft':            ('Warcraft', 'series', 'Q1131413', [r'warcraft']),
    'castlevania':         ('Castlevania', 'series', 'Q1050150', [r'castlevania']),
    'gears-of-war':        ('Gears of War', 'series', 'Q1194869', [r'gears of war', r'\bgears\b']),
    'warframe':            ('Warframe', 'game', 'Q3088546', [r'warframe']),
    'fortnite':            ('Fortnite', 'game', 'Q16247957', [r'fortnite']),
    'battlefield':         ('Battlefield', 'series', 'Q807542', [r'battlefield']),
    'sonic':               ('Sonic the Hedgehog', 'series', 'Q1132836', [r'\bsonic\b']),
    'street-fighter':      ('Street Fighter', 'series', 'Q1059431', [r'street fighter']),
    'apex-legends':        ('Apex Legends', 'game', 'Q61699386', [r'apex legends']),
    'the-witcher':         ('The Witcher', 'series', 'Q1199478', [r'witcher']),
    'pokemon':             ('Pokémon', 'series', 'Q864', [r'pok[eé]mon']),
    'helldivers':          ('Helldivers', 'series', None, [r'helldivers']),
    'palworld':            ('Palworld', 'game', 'Q117181003', [r'palworld']),
    'nintendo':            ('Nintendo', 'company', 'Q8093', [r'nintendo']),
    'playstation':         ('PlayStation (Sony Interactive Entertainment)', 'company', 'Q1146472',
                            [r'playstation', r'\bps5\b', r'\bsony\b', r'state of play']),
    'xbox':                ('Xbox (Microsoft Gaming)', 'company', None, [r'\bxbox\b', r'game pass', r'microsoft']),
    'capcom':              ('Capcom', 'company', 'Q14569', [r'capcom', r'resident evil', r'monster hunter',
                                                             r'onimusha', r'pragmata']),
    'kojima-productions':  ('Kojima Productions', 'company', 'Q2251958', [r'kojima', r'death stranding']),
    'grasshopper':         ('Grasshopper Manufacture', 'company', 'Q1543767', [r'grasshopper', r'suda ?51',
                                                                               r'no more heroes']),
    'square-enix':         ('Square Enix', 'company', 'Q207784', [r'square enix', r'dragon quest']),
}

# Wikidata properties shown on a page (label, property).
PROPS = [('developer', 'P178'), ('publisher', 'P123'), ('founded', 'P571'), ('first released', 'P577'),
         ('headquarters', 'P159'), ('parent organisation', 'P749'), ('founded by', 'P112'), ('genre', 'P136'),
         ('platform', 'P400')]


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')


def stories():
    for f in sorted(STORIES.glob('*.json')):
        try:
            s = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(s, dict):
            s.setdefault('id', f.stem)
            yield s


def haystack(s):
    comp = s.get('companies') or []
    comp = ' '.join(comp) if isinstance(comp, list) else str(comp)
    return ' '.join(str(x) for x in (s.get('game') or '', comp, s.get('title') or '', s.get('id') or '')).lower()


def matches(s):
    h = haystack(s)
    return [slug for slug, (_, _, _, pats) in ENTITIES.items() if any(re.search(p, h) for p in pats)]


def story_date(s):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', str(s.get('id') or ''))
    if m:
        return m.group(1)
    p = s.get('published')
    if isinstance(p, dict) and p.get('at'):
        return str(p['at'])[:10]
    return '????-??-??'


def posted(s):
    p = s.get('published')
    return bool(p) or str(s.get('status') or '').lower() in ('published', 'posted', 'scheduled')


def reel_line(s):
    bits = [story_date(s), s.get('chip') or '', s.get('template') or '']
    title = re.sub(r'\s+', ' ', str(s.get('title') or s.get('id'))).strip()
    return f"- {bits[0]} · {' · '.join(b for b in bits[1:] if b) or 'no chip'} · {title} (`{s['id']}`)"


def sparql(q):
    url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': q, 'format': 'json'})
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)['results']['bindings']


def facts_all(qids):
    """{qid: ([(label, value)], item label, item description)} for every item in ONE query (the query service may
    allow one request a minute); one retry after 65 s on a refusal."""
    vals = ' '.join(f'wdt:{p}' for _, p in PROPS)
    items = ' '.join(f'wd:{q}' for q in qids)
    q = f'''SELECT ?item ?itemLabel ?itemDescription ?p ?v ?vLabel WHERE {{
  VALUES ?item {{ {items} }}
  OPTIONAL {{ VALUES ?p {{ {vals} }} ?item ?p ?v . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}'''
    try:
        rows = sparql(q)
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        time.sleep(65)
        rows = sparql(q)
    meta, found = {}, {}
    for r in rows:
        qid = r['item']['value'].rsplit('/', 1)[-1]
        meta[qid] = (r.get('itemLabel', {}).get('value', ''), r.get('itemDescription', {}).get('value', ''))
        if 'v' not in r or 'p' not in r:
            continue
        prop = r['p']['value'].rsplit('/', 1)[-1]
        v = r.get('vLabel', {}).get('value') or r['v']['value']
        if re.match(r'\d{4}-\d{2}-\d{2}T', v):
            v = v[:10]
        lst = found.setdefault(qid, {}).setdefault(prop, [])
        if v not in lst:
            lst.append(v)
    out = {}
    for qid in qids:
        fs = []
        for lab, p in PROPS:
            vs = sorted(found.get(qid, {}).get(p, []))
            if not vs:
                continue
            if p in ('P577', 'P571'):
                vs = vs[:1]                   # the earliest date only
            fs.append((lab, ', '.join(vs[:4]) + (' and more' if len(vs) > 4 else '')))
        label, desc = meta.get(qid, ('', ''))
        out[qid] = (fs, label, desc)
    return out


def _words(t):
    return {w for w in re.findall(r'[a-z0-9]+', t.lower()) if w not in ('the', 'of', 'and', 'inc', 'co', 'ltd')}


def label_ok(title, label):
    """True when the Wikidata label and our title share their main words (guards against a wrong item id)."""
    a, b = _words(title.split('(')[0]), _words(label)
    return bool(a and b) and len(a & b) / max(1, min(len(a), len(b))) >= 0.5


def page(slug, facts_block, reels, total):
    title, kind, qid, _ = ENTITIES[slug]
    lines = [f'# {title}', '',
             f'Kind: {kind}. Backstory page (adv-20261102-story-brief part 2): facts from Wikidata, our Reels from the',
             'story ledger. Read before writing the angle of a story that touches it. Do not paste facts into a post',
             'without checking them against the story\'s own primary.', '', '## Facts']
    lines += facts_block
    lines += ['', f'## Our Reels ({total} in the ledger; newest {min(total, MAX_REELS)})']
    lines += reels or ['- none yet']
    lines += ['', '## Log (one line per published post, added by presubmit.py published)']
    return lines


def seed(slugs=None):
    PAGES.mkdir(exist_ok=True)
    allst = [s for s in stories()]
    slugs = slugs or list(ENTITIES)
    qids = [ENTITIES[s][2] for s in slugs if ENTITIES[s][2]]
    try:
        wd, err = (facts_all(qids) if qids else {}), None
    except Exception as e:                                      # network or service: the pages keep our Reels
        wd, err = {}, f'{type(e).__name__}'
    for slug in slugs:
        title, kind, qid, _ = ENTITIES[slug]
        if qid and qid in wd and label_ok(title, wd[qid][1]):
            fs, label, desc = wd[qid]
            fb = [f'- Wikidata item {qid}: {label} ({desc}); retrieved {today()}; CC0, facts only.']
            fb += [f'- {lab}: {v} (Wikidata {qid})' for lab, v in fs]
        elif qid and qid in wd:
            fb = [f'- Wikidata {qid} is "{wd[qid][1]}", not {title}: fix the item in newsroom/context.py ENTITIES.']
        elif qid:
            fb = [f'- Wikidata {qid}: not read on {today()} ({err or "no answer"}); seed again later.']
        else:
            fb = ['- No Wikidata item set yet (add it to ENTITIES after checking it by hand).']
        mine = [s for s in allst if slug in matches(s) and posted(s)]
        mine.sort(key=lambda s: (story_date(s), s['id']), reverse=True)
        f = PAGES / f'{slug}.md'
        old_log = []
        if f.exists():
            txt = f.read_text().splitlines()
            if '## Log (one line per published post, added by presubmit.py published)' in txt:
                old_log = txt[txt.index('## Log (one line per published post, added by presubmit.py published)') + 1:]
        lines = page(slug, fb, [reel_line(s) for s in mine[:MAX_REELS]], len(mine)) + old_log
        f.write_text('\n'.join(lines).rstrip() + '\n')
        print(f'{slug}: {fb[0][2:90]} | {len(fb) - 1} facts, {len(mine)} Reels')


def append(sid):
    f = STORIES / f'{sid}.json'
    s = json.loads(f.read_text())
    s.setdefault('id', sid)
    done = []
    for slug in matches(s):
        p = PAGES / f'{slug}.md'
        if not p.exists():
            continue
        line = reel_line(s)
        txt = p.read_text()
        if f'(`{sid}`)' in txt.split('## Log', 1)[-1]:
            continue
        p.write_text(txt.rstrip() + '\n' + line + '\n')
        done.append(slug)
    return done


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == 'seed':
        seed(a[1:] or None)
    elif a[0] == 'match' and len(a) == 2:
        s = json.loads((STORIES / f'{a[1]}.json').read_text())
        s.setdefault('id', a[1])
        for slug in matches(s):
            print(f'newsroom/context/{slug}.md' + ('' if (PAGES / f'{slug}.md').exists() else ' (no page yet)'))
    elif a[0] == 'append' and len(a) == 2:
        print('appended to: ' + (', '.join(append(a[1])) or 'no page'))
    elif a[0] == 'list':
        for slug, (t, k, q, _) in ENTITIES.items():
            print(f'{slug:20s} {k:8s} {q or "-":12s} {t}')
    else:
        raise SystemExit(__doc__)
