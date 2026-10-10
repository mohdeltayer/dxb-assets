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
    'trailer':   'one continuous stretch of an official trailer with its own sound (the default)',
    'numbers':   'our own graphics: charts, figures, sales (bed under them)',
    'comparison': 'two states with labels and hard cuts: prices by country, specs, before and after (reel(..., cut=True))',
    'quote':     "the speaker's line leads, in «» right after the headline",
    'explainer': "the source's own figures step by step (patents, features)",
    'handson':   'his gameplay: natural colours, text after the action, numbered tips',
    'retro':     'on this day: the game on a real CRT photo, fact sheet then «هل تعلم؟» facts (retro_tv, 10 Oct 2026)',
}
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
