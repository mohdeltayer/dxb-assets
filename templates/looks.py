"""Theme and style rotation on the live path (build 9 Nov 2026, Mohammad: "theme and style rotation verified on the live
path with a no-three-in-a-row check").

What was found: the jobs Production 2 writes carry their own `style`, so reel.pick_style's ledger never turns for
them, and the server's render commits no ledger. The six Reels before 9 Nov 07:00 Dubai read, in order: lines, bold,
glow, glow, glow, lines (three glows in a row); themes emerald, playful, cold, playful, cold, spectacle.

The check: every render on the live path (render_job check and run) reads the last two Reels in LEDGER, by time.
 - Style: a job style (or the ledger's pick) that both of the last two share is swapped for the style rested longest
   among the others, and the swap is printed. Style is rotation only, so a news render never waits on it.
 - Theme: a theme both of the last two share stops the render at check (the theme follows the game's palette, so the
   session picks the next nearest one); the error names the themes still free.
After a render that ships, render_job records {name, theme, style, at}; the render workflows commit LEDGER with the Reel.
Breaking (T0) and Famitsu renders are neither checked nor recorded; a game skin keeps its own look.

    python3 looks.py last [n]          the last n looks (default 6)
    python3 looks.py add <entry.json>  append an entry (the render workflows, after a fresh checkout)
"""
import datetime, json, os, sys

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'look-ledger.json')
STYLES = ('lines', 'bold', 'glow', 'frame')       # reel.STYLES
THEMES = ('cold', 'stylized', 'playful', 'spectacle', 'emerald', 'gold')   # crimson is the عاجل skin only
KEEP = 400


def _load():
    try:
        return json.load(open(LEDGER))
    except (OSError, ValueError):
        return []


def _key(name):
    return os.path.basename(str(name)).rsplit('-reel-v', 1)[0].replace('.json', '')


def last(n=2, exclude=None):
    """The last n entries by time, a re-render of `exclude` (the same story) left out."""
    ex = _key(exclude) if exclude else None
    rows = [e for e in _load() if _key(e.get('name', '')) != ex]
    return sorted(rows, key=lambda e: e.get('at', ''))[-n:]


def rested(kind, prev, avoid):
    """The style (or theme) used longest ago among those not in `avoid`."""
    pool = STYLES if kind == 'style' else THEMES
    order = [e.get(kind) for e in sorted(_load(), key=lambda e: e.get('at', ''))]
    when = {x: max([i for i, v in enumerate(order) if v == x], default=-1) for x in pool if x not in avoid}
    return min(when, key=lambda x: when[x]) if when else None


def resolve(job):
    """(style to render with, problems). The style keeps the job's unless it would be the third in a row."""
    prev = last(2, exclude=job.get('name'))
    style = job.get('style')
    if style is None:
        import reel                              # the ledger pick reel.reel would make (kept on a re-render)
        style = reel.pick_style(os.path.join('cards', job.get('out', job.get('name', 'x'))))
    problems = []
    if len(prev) == 2 and prev[0].get('style') == prev[1].get('style') == style:
        new = rested('style', prev, {style})
        print(f'looks: style {style} would be the third in a row ({prev[0]["name"]}, {prev[1]["name"]}); '
              f'rendering with {new}, the one rested longest', flush=True)
        style = new
    theme = job.get('theme')
    if theme != 'crimson' and len(prev) == 2 and prev[0].get('theme') == prev[1].get('theme') == theme:
        free = [t for t in THEMES if t != theme]
        problems.append(f'theme {theme} would be the third in a row ({prev[0]["name"]}, {prev[1]["name"]}); pick the '
                        f'next nearest to the game\'s palette from {", ".join(free)} (no three in a row, 9 Nov 2026)')
    return style, problems


def record(job, style, at=None):
    entry = {'name': _key(job.get('out') or job.get('name')), 'theme': job.get('theme'), 'style': style,
             'at': at or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    add(entry)
    if os.environ.get('LOOK_ENTRY'):             # the render workflows add it again after their fresh checkout
        json.dump(entry, open(os.environ['LOOK_ENTRY'], 'w'), ensure_ascii=False)
    return entry


def add(entry):
    rows = [e for e in _load() if not (_key(e.get('name', '')) == _key(entry['name']))]   # a re-render replaces its row
    rows.append(entry)
    rows = sorted(rows, key=lambda e: e.get('at', ''))[-KEEP:]
    with open(LEDGER, 'w') as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'last'
    if cmd == 'last':
        for e in last(int(sys.argv[2]) if len(sys.argv) > 2 else 6):
            print(e.get('at'), e.get('theme'), e.get('style'), e.get('name'))
    elif cmd == 'add':
        add(json.load(open(sys.argv[2])))
    else:
        raise SystemExit('looks.py last [n] | add <entry.json>')
