"""Cross-Reel variety (audit of 21 Nov 2026, item 6; advisor, agreed with Mohammad).

Six GTA VI Reels on 20 and 21 Nov opened on the same few seconds of Rockstar's launch trailer. Two ledgers fix it:

  - openers: per game, the source moment each Reel opened on (the hook shot). A new Reel of the same game never opens
    within OPENER_GAP seconds of an opener used in the last OPENER_DAYS days.
  - covers: a 64-bit difference hash of every Reel's cover (the hook frame as the 9:16 window crops it). A new cover
    must differ from the last COVER_LAST covers on the grid by at least COVER_MIN_BITS bits.

autoshots.fill asks hook_ok() before it settles the hook slot and tries the next clean stretch when it fails; the
render writes the Reel's entry ($RUNNER_TEMP/cover.json) and the workflow adds it to templates/assets/cover-ledger.json
in the render commit, like the look and bed ledgers. Several clean stretches per game come from the shot read itself:
every Reel takes its slots from different stretches (autoshots), and the footage library keeps up to 40 per source.

    python3 templates/variety.py add <cover.json>       append to the ledger (the render workflow)
    python3 templates/variety.py show [game words]      the last covers and openers
"""
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'assets', 'cover-ledger.json')
OPENER_DAYS = 14
OPENER_GAP = 4.0          # seconds of source either side of a recent opener that a new hook may not start in
COVER_LAST = 6
COVER_MIN_BITS = 12       # of 64: a smaller distance reads as the same picture on the grid
KEEP = 300


def load():
    try:
        return json.load(open(LEDGER, encoding='utf-8'))
    except (OSError, ValueError):
        return {'about': 'Cover and opener ledger (audit 21 Nov 2026, item 6): one entry per rendered Reel.',
                'entries': []}


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _parse(t):
    try:
        return dt.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def source_key(job, f):
    """The footage library's key for file f (the Steam trailer or the official URL), else the file name."""
    try:
        import footlib
        item = next((it for it in job.get('footage') or [] if it.get('file') == f), None)
        return footlib.item_key(item) if item else f
    except Exception:                            # noqa: BLE001
        return f


def game_of(job):
    """One key per game (23 Nov 2026, item 3): GTA VI, Grand Theft Auto VI and GTA 6 meet (templates/gamekey.py)."""
    import gamekey
    return gamekey.key(job.get('game') or job.get('game_short'))


def _gk(name):
    import gamekey
    return gamekey.key(name)


CURATED = os.path.join(HERE, 'assets', 'game-stretches.json')


def curated(game):
    """The game's curated, labelled stretches (templates/assets/game-stretches.json), each with its file's url; [] when
    the game has none. `same` lists repo copies on the same timeline (a 1080p cut of the 4K master), so a job that
    already carries one uses it instead of fetching the master."""
    try:
        g = json.load(open(CURATED, encoding='utf-8')).get('games', {}).get(_gk(game) or '')
    except (OSError, ValueError):
        g = None
    if not g:
        return [], {}
    out = []
    try:                                         # never a blocked stretch (shot rules, 27 Nov 2026)
        import blocked as _B
    except Exception:                            # noqa: BLE001
        _B = None
    for s in g.get('stretches') or []:
        fi = (g.get('files') or {}).get(s['file'], {})
        if _B and _B.hit({}, s['file'], float(s['start']), float(s.get('secs') or 2.0)):
            room = min([a for a, b, _r in _B.ranges({}, s['file']) if b > float(s['start'])] + [1e9]) - float(s['start'])
            if room < 2.0:                       # starts in or just before a blocked stretch: not offered
                continue
            s = dict(s, secs=round(room - 0.05, 2))   # ends before it
        if fi.get('url'):
            out.append(dict(s, url=fi['url'], same=list(fi.get('same') or [])))
    return out, g.get('subjects') or {}


def story_score(stretch, text, subjects, people_story):
    """How well a stretch matches the story (23 Nov 2026, item 5): a named subject the story names (Jason, Lucia, Vice
    City) counts 3; for a story about a person or an event, a person, a crowd or the city counts 1."""
    t = str(text or '').lower()
    sc = 0.0
    for tag in stretch.get('tags') or []:
        words = subjects.get(tag)
        if words and any(w.lower() in t for w in words):
            sc += 3
    if people_story and set(stretch.get('tags') or []) & {'person', 'people', 'crowd', 'city', 'vice city'}:
        sc += 1
    return sc


def frame_hash(path, t, focus=None, boxed=False):
    """dHash of the frame at t as the grid shows it: cropped to the 9:16 window around focus (0 to 1 across the frame),
    or, for the 16:9 boxed (showcase) layout, the whole picture in its box (23 Nov 2026, item 4); None on failure."""
    try:
        from PIL import Image
        import io
        out = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0.0, t):.2f}', '-i', path,
                              '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                             capture_output=True, timeout=30).stdout
        im = Image.open(io.BytesIO(out)).convert('L')
        w, h = im.size
        cw = min(w, int(h * 9 / 16))
        fx = 0.5 if not isinstance(focus, (int, float)) else float(focus)
        x0 = int(min(max(fx * w - cw / 2, 0), w - cw))
        im = (im if boxed else im.crop((x0, 0, x0 + cw, h))).resize((9, 8))
        px = list(im.getdata())
        bits = 0
        for r in range(8):
            for c in range(8):
                bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
        return bits
    except Exception:                            # noqa: BLE001
        return None


def _focus(fo):
    if isinstance(fo, (int, float)):
        return fo
    if isinstance(fo, list) and fo and isinstance(fo[0], list) and len(fo[0]) > 1:
        return fo[0][1]
    return None


def hook_ok(job, f, path, st, fo=None, led=None, now=None):
    """(True, '') or (False, reason) for a hook at source second st of file f."""
    led = led if led is not None else load()
    now = now or _now()
    ents = led.get('entries') or []
    key, game = source_key(job, f), game_of(job)
    for e in ents:
        t = _parse(e.get('at'))
        if not t or (now - t).days >= OPENER_DAYS or e.get('name') == job.get('name'):
            continue
        op = e.get('opener') or []
        if game and _gk(e.get('game')) == game and len(op) == 2 and op[0] == key and abs(float(op[1]) - st) < OPENER_GAP:
            return False, f"opener {st:.1f} s was used by {e.get('name')} at {float(op[1]):.1f} s within {OPENER_DAYS} days"
    h = frame_hash(path, st + 0.2, _focus(fo), boxed=job.get('layout') == 'showcase')
    if h is None:
        return True, ''
    for e in [x for x in ents if x.get('name') != job.get('name')][-COVER_LAST:]:
        if e.get('hash') is None:
            continue
        d = bin(int(e['hash']) ^ h).count('1')
        if d < COVER_MIN_BITS:
            return False, f"cover at {st:.1f} s is {d} bits from {e.get('name')}'s cover (under {COVER_MIN_BITS})"
    return True, ''


def entry(job, uploads):
    """The ledger entry for a settled job (the first footage shot), or None."""
    for sh in job.get('shots') or []:
        if isinstance(sh, list) and len(sh) > 2 and isinstance(sh[1], (int, float)) and not str(sh[0]).endswith('.png'):
            path = os.path.join(uploads, sh[0])
            return {'name': job.get('name'), 'game': game_of(job), 'at': _now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'opener': [source_key(job, sh[0]), round(float(sh[1]), 2)],
                    'hash': frame_hash(path, float(sh[1]) + 0.2, _focus(sh[3] if len(sh) > 3 else None),
                                       boxed=job.get('layout') == 'showcase'),
                    'layout': job.get('layout') or 'crop'}
        if isinstance(sh, list) and str(sh[0]).endswith('.png'):
            return None                          # a card cover: nothing to compare
    return None


def add(path):
    e = json.load(open(path, encoding='utf-8'))
    led = load()
    led['entries'] = [x for x in led.get('entries', []) if x.get('name') != e.get('name')] + [e]
    led['entries'] = led['entries'][-KEEP:]
    json.dump(led, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"variety: {e.get('name')} opener {e.get('opener')} added")


def main(argv):
    if argv[:1] == ['add'] and len(argv) == 2:
        add(argv[1])
        return 0
    if argv[:1] == ['show']:
        words = ' '.join(argv[1:]).lower()
        for e in load().get('entries', [])[-30:]:
            if not words or words in str(e.get('game') or ''):
                print(e.get('at'), e.get('name'), e.get('game'), e.get('opener'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
