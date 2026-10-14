"""Reel formats and the format ledger (Mohammad, 10 Oct 2026).

Every Digital Lounge Reel is one of these formats, chosen in its creative
brief before the shot sheet. No more than two Reels in a row share a format
unless the story demands it; the ledger keeps the order they went out in.

    python3 formats.py                      # the last ten, newest last
    python3 formats.py check numbers        # a third in a row, or a third card-led Reel in six?
    python3 formats.py add <reel name> trailer
    python3 formats.py views <reel name> 1840   # weekly Instagram views next to the template (Tuesday, 14 Oct 2026)
    python3 formats.py templates                # median views per template
"""
import json, os, sys

FORMATS = {
    'trailer':   'official footage runs the whole Reel with its own sound; the lines ride on the picture; no card (the default when a trailer exists)',
    'split':     'footage runs the whole Reel with a slim pinned fact strip (date, price, platforms; 2 or 3 items) low in the safe zone; the lines never repeat the strip (reel(..., strip=[...]), 14 Oct 2026)',
    'clipcard':  'footage for the hook and story, ONE card at the key beat (price table, date, figure), then footage again; the card holds its beat alone or under a one-line frame',
    'numbers':   'our own graphics on the living ground for the whole Reel, only when no footage shows the news: sales charts, results, rankings',
    'comparison': 'two states with labels and hard cuts: prices by country, specs, before and after (reel(..., cut=True))',
    'quote':     "the speaker's line leads, in «» right after the headline; then footage of what they talked about",
    'explainer': "the source's own figures or screens step by step (patents, features, store pages)",
    'handson':   'his gameplay: natural colours, text after the action, numbered tips',
    'retro':     'on this day: the game on a real CRT photo, fact sheet then «هل تعلم؟» facts (retro_tv, 10 Oct 2026)',
    'edition':   'special and collector\'s editions, bundles, limited consoles, accessories, tier contents: trailer hook, each item as a press-render cut-out drifting onto the living ground, one composition frame with the price strip, footage close (edition.py, 14 Oct 2026)',
}
TEMPLATES = FORMATS

# The opening beat per template (advisor, 14 Oct 2026): what is on screen in the first second, under the chip and the
# hook headline. The footage moves from frame one; the credit line enters at 2 s (reel.CREDIT_AT).
OPENERS = {
    'trailer':    'the strongest shot of the stretch, moving from frame one, the headline over it',
    'split':      'the footage moving from frame one; the strip pins when the headline leaves',
    'clipcard':   'the footage hook, moving; the card comes only at the key beat',
    'numbers':    'the number alone, large, on the living ground; the chart builds after it',
    'comparison': 'the first state with its label; the second state is the cut',
    'quote':      'the quote itself in «», over the speaker or the thing they spoke of; the portrait never holds the whole Reel',
    'explainer':  "the source's first figure or screen, the part the story turns on ringed",
    'handson':    'the action, his play, before any text',
    'retro':      'the game running on the CRT, the date over it',
    'edition':    'the hero item: the trailer hook with the headline, then the hero cut-out first and largest',
}


def opener(fmt):
    return OPENERS.get(fmt, '')

# Two families (advisor, 14 Oct 2026): footage-led Reels run the picture the whole way; card-led Reels put our graphics,
# figures or a portrait on screen. Besides "no third in a row", card-led Reels are at most one in three over the last six.
FAMILIES = {
    'footage': ('trailer', 'split', 'clipcard', 'handson'),
    'card':    ('numbers', 'explainer', 'quote', 'retro', 'edition'),
}
FAMILY = {fmt: fam for fam, fmts in FAMILIES.items() for fmt in fmts}
FAMILY['comparison'] = 'footage'   # two labelled states of the footage or store screens, hard cuts
WINDOW, CARD_MAX = 6, 2            # at most CARD_MAX card-led Reels in any WINDOW consecutive Reels

# Which templates fit which kind of news (Mohammad, 14 Oct 2026: "various reel templates and scenarios and which templates can
# be used with the type of news"). First is the default; the rest are the alternatives when the first would be a third in a row
# or the footage does not exist. A story with a trailer never starts from a card template.
NEWS_MAP = {
    'launch':        ['trailer', 'split'],            # out now, with a trailer; split when the price or platforms matter
    'date':          ['split', 'trailer'],            # a release date or an event date and time
    'reveal':        ['trailer'],                      # an announcement with footage
    'update':        ['trailer', 'clipcard'],         # a patch or a feature; clipcard when the patch notes are the point
    'price':         ['split', 'clipcard', 'comparison'],   # store prices, discounts, editions
    'sales':         ['numbers', 'clipcard'],         # sales figures, charts, rankings
    'business':      ['quote', 'explainer', 'numbers'],     # studios, deals, results, people
    'quote':         ['quote'],                        # someone said something
    'report':        ['clipcard', 'trailer'],         # a report or rumour: the footage of the game, one card for the claim
    'hardware':      ['explainer', 'split'],          # devices, specs
    'event':         ['split', 'explainer'],          # a show, a tournament, a date card
    'handson':       ['handson'],
    'anniversary':   ['retro'],
    'edition':       ['edition', 'split'],            # a collector's or special edition, bundle, limited console, accessory, tier contents
}


def pick(kind):
    """The template for a kind of news: its first choice unless the ledger refuses it (a third in a row, or a third
    card-led Reel in six)."""
    for fmt in NEWS_MAP[kind]:
        if not check(fmt):
            return fmt
    return NEWS_MAP[kind][0]
LEDGER = os.path.join(os.path.dirname(__file__), 'assets', 'format-ledger.json')


def _load():
    try:
        return json.load(open(LEDGER))
    except (OSError, ValueError):
        return []


def add(name, fmt):
    if fmt not in FORMATS:
        raise ValueError(f'{fmt}: not a format ({", ".join(FORMATS)})')
    led = _load()
    old = next((e for e in led if e['name'] == name), {})
    led = [e for e in led if e['name'] != name]   # a re-render keeps its place and its views
    led.append({'name': name, 'format': fmt, **({'views': old['views']} if 'views' in old else {})})
    json.dump(led[-200:], open(LEDGER, 'w'), indent=1)


def views(name, n):
    """Weekly views next to the template (advisor, 14 Oct 2026): Mohammad sends the numbers on Tuesday morning before the
    audit; `analytics/reel-views.md` says how they are read. Instagram's count for the Reel, as an integer."""
    led = _load()
    hit = [e for e in led if e['name'] == name]
    if not hit:
        raise ValueError(f'{name}: not in the format ledger')
    hit[0]['views'] = int(n)
    json.dump(led, open(LEDGER, 'w'), indent=1)


def by_template():
    """Median and count of the views recorded per template, newest 200 Reels."""
    import statistics
    seen = {}
    for e in _load():
        if 'views' in e:
            seen.setdefault(e['format'], []).append(e['views'])
    return {f: (statistics.median(v), len(v)) for f, v in seen.items()}


def check(fmt):
    """Why fmt should not be next, or '' when it may: a third in a row, or (card-led) a third card-led Reel in the
    last six (at most one in three)."""
    led = [e['format'] for e in _load()]
    last = led[-2:]
    if len(last) == 2 and all(f == fmt for f in last):
        return f'third {fmt} in a row'
    if FAMILY.get(fmt) == 'card':
        recent = led[-(WINDOW - 1):]
        cards = [f for f in recent if FAMILY.get(f) == 'card']
        if len(cards) >= CARD_MAX:
            return f'card-led would be {len(cards) + 1} of the last {len(recent) + 1} ({", ".join(cards)}); at most {CARD_MAX} in {WINDOW}'
    return ''


def family(fmt):
    return FAMILY.get(fmt, '?')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['add']:
        add(a[1], a[2]); print('ok')
    elif a[:1] == ['views']:                       # python3 formats.py views <reel name> <instagram views>
        views(a[1], a[2]); print('ok')
    elif a[:1] == ['templates']:                   # views per template, for the Tuesday audit
        for f, (med, n) in sorted(by_template().items(), key=lambda kv: -kv[1][0]):
            print(f'{f:<10} median {med:>8,.0f} views over {n} Reels')
    elif a[:1] == ['check']:
        why = check(a[1])
        print(f'{why}: pick another unless the story demands it' if why else 'ok')
        print(f'opens on: {opener(a[1])}')
    else:
        for e in _load()[-10:]:
            v = f"{e['views']:>7,}" if 'views' in e else '      -'
            print(f"{e['format']:<10} {family(e['format']):<7} {v}  {e['name']}")
