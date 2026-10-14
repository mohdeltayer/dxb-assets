"""Reel formats and the format ledger (Mohammad, 10 Oct 2026).

Every Digital Lounge Reel is one of these formats, chosen in its creative
brief before the shot sheet. No more than two Reels in a row share a format
unless the story demands it; the ledger keeps the order they went out in.

    python3 formats.py                      # the last ten, newest last
    python3 formats.py check numbers        # would this be a third in a row?
    python3 formats.py add <reel name> trailer
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
}
TEMPLATES = FORMATS

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
}


def pick(kind):
    """The template for a kind of news: its first choice unless that would be a third in a row."""
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
    led = [e for e in _load() if e['name'] != name]   # a re-render keeps its place
    led.append({'name': name, 'format': fmt})
    json.dump(led[-200:], open(LEDGER, 'w'), indent=1)


def check(fmt):
    """True when fmt would be a third in a row."""
    last = [e['format'] for e in _load()[-2:]]
    return len(last) == 2 and all(f == fmt for f in last)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['add']:
        add(a[1], a[2]); print('ok')
    elif a[:1] == ['check']:
        print('third in a row: pick another unless the story demands it' if check(a[1]) else 'ok')
    else:
        for e in _load()[-10:]:
            print(e['format'], e['name'])
