"""One key per game (Mohammad, 23 Nov 2026, variety fix item 3): «GTA VI», «Grand Theft Auto VI» and «GTA 6» are the same
game. The cover ledger, the curated stretches and the slip all use key(name).

    python3 templates/gamekey.py "Grand Theft Auto VI"     -> gta vi
"""
import re
import sys
import unicodedata

ALIASES = {
    'gta vi': ('gta vi', 'gta 6', 'gtavi', 'gta6', 'grand theft auto vi', 'grand theft auto 6'),
    'gta v': ('gta v', 'gta 5', 'grand theft auto v', 'grand theft auto 5'),
    'red dead redemption 2': ('rdr2', 'rdr 2', 'red dead redemption ii'),
    'the legend of zelda: ocarina of time': ('ocarina of time', 'zelda ocarina of time', 'the legend of zelda ocarina of time'),
}
ROMAN = {'1': 'i', '2': 'ii', '3': 'iii', '4': 'iv', '5': 'v', '6': 'vi', '7': 'vii', '8': 'viii', '9': 'ix', '10': 'x'}


def _clean(name):
    t = str(name or '').replace('™', '').replace('®', '').replace('©', '')
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[‐-―:–—]', ' ', t)
    t = re.sub(r'[^a-z0-9+ ]+', ' ', t)
    return ' '.join(t.split())


def key(name):
    """The game's one key: a listed alias wins; otherwise the cleaned name with a trailing number written as a Roman
    numeral (so «Final Fantasy 7» and «Final Fantasy VII» meet). None for an empty name."""
    t = _clean(name)
    if not t:
        return None
    for k, al in ALIASES.items():
        if t == _clean(k) or t in (_clean(a) for a in al):
            return k
    words = t.split()
    if words and words[-1] in ROMAN:
        words[-1] = ROMAN[words[-1]]
    t = ' '.join(words)
    for k, al in ALIASES.items():                       # a numeral rewrite can land on an alias (gta 6 -> gta vi)
        if t == _clean(k) or t in (_clean(a) for a in al):
            return k
    return t


if __name__ == '__main__':
    print(key(' '.join(sys.argv[1:])))
