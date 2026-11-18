"""Footage library per game (adv-20261118-templates-never-refuse B, Mohammad 18 Nov 2026).

Every Reel that renders on the server adds its footage to `assets/footage-library.json`: the source item exactly as the
job fetched it (a Steam trailer, an official URL), the handle it came from (steam:<appid> or the official page), the
games it belongs to, and the stretches the Reel used (start, seconds, focus): proven files and proven clean stretches.
Every session and the server read it first:
  - footage.resolve(handle) puts the library's proven files for that handle ahead of a fresh resolve;
  - render_job's picture ladder takes a proven stretch of the same file before an evenly spaced guess when the shot read
    finds nothing (or does not finish);
  - a session builds a job from `python3 templates/footlib.py game <words>` instead of looking for footage again.

    python3 templates/footlib.py record <job.json> [qc.json]   add a rendered job (the render workflow, after the render)
    python3 templates/footlib.py seed [jobs/done]              add every job under jobs/done (first fill)
    python3 templates/footlib.py game <words>                  proven files for a game
    python3 templates/footlib.py handle <steam:appid | url>    proven files for a footage handle
Nothing private goes in: public source addresses, file names, times. A file whose Reel failed qc for a hard stop (decode)
is not recorded.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, 'assets', 'footage-library.json')
KEEP_STRETCHES = 40
VIDEO = ('.mp4', '.mov', '.mkv', '.webm', '.m4v')


def load(path=LIB):
    try:
        return json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return {'files': {}}


def save(lib, path=LIB):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(lib, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)


def item_key(item):
    """One key per source video: Steam app and trailer name, else the URL, else the committed file."""
    if item.get('steam'):
        return f"steam:{item['steam']}:{item.get('trailer') or item.get('file')}"
    return item.get('url') or item.get('repo') or item.get('file')


def handles(item, job):
    out = set()
    if item.get('steam'):
        out.add(f"steam:{item['steam']}")
    for k in ('footage_source', 'footage_handle'):
        if job.get(k):
            out.add(str(job[k]))
    if item.get('page'):
        out.add(item['page'])
    return sorted(out)


def games(job):
    g = job.get('game') or []
    g = [g] if isinstance(g, str) else list(g)
    for k in ('story', 'name'):
        if job.get(k):
            g.append(str(job[k]))
    return sorted(set(g))


def record(job, qc=None, lib=None, now=None):
    """Add a rendered job's footage and the stretches it used. Returns the keys touched."""
    if qc and any(f.get('check') == 'decode' for f in qc.get('findings') or []):
        return []
    own = lib is None
    lib = lib if lib is not None else load()
    files = lib.setdefault('files', {})
    at = (now or dt.datetime.now(dt.timezone.utc)).strftime('%Y-%m-%dT%H:%M:%SZ')
    by_file = {it.get('file'): it for it in job.get('footage') or [] if it.get('file')}
    touched = []
    for f, it in by_file.items():
        if not str(f).lower().endswith(VIDEO):
            continue
        key = item_key(it)
        e = files.setdefault(key, {'item': {k: v for k, v in it.items() if k not in ('start', 'seconds')},
                                   'handles': [], 'games': [], 'stretches': [], 'reels': [], 'added': at})
        e['handles'] = sorted(set(e['handles']) | set(handles(it, job)))
        e['games'] = sorted(set(e['games']) | set(games(job)))
        for sh in job.get('shots') or []:
            if isinstance(sh, list) and len(sh) > 2 and sh[0] == f and isinstance(sh[1], (int, float)):
                s = [round(float(sh[1]), 2), round(float(sh[2]), 2), sh[3] if len(sh) > 3 else None]
                if s[:2] not in [x[:2] for x in e['stretches']]:
                    e['stretches'].append(s)
        e['stretches'] = sorted(e['stretches'], key=lambda x: x[0])[-KEEP_STRETCHES:]
        if job.get('name') and job['name'] not in e['reels']:
            e['reels'].append(job['name'])
        e['last_used'] = at
        touched.append(key)
    if own:
        save(lib)
    return touched


def _match_words(words, e):
    hay = ' '.join(e.get('games', []) + [str(e['item'].get('trailer') or ''), str(e['item'].get('file') or '')]).lower()
    return all(w.lower() in hay for w in words)


def for_game(words, lib=None):
    lib = lib or load()
    return [dict(e, key=k) for k, e in lib.get('files', {}).items() if _match_words(words, e)]


def for_handle(handle, lib=None):
    """Proven files for a footage handle (steam:<appid>, a bare appid, a Steam store URL, or an official page)."""
    lib = lib or load()
    h = str(handle).strip()
    m = re.fullmatch(r'(?:steam:)?(\d{3,10})', h) or re.search(r'store\.steampowered\.com/app/(\d+)', h)
    keys = {f'steam:{m.group(1)}'} if m else {h, h.rstrip('/')}
    return [dict(e, key=k) for k, e in lib.get('files', {}).items()
            if keys & {x.rstrip('/') for x in e.get('handles', [])} | keys & set(e.get('handles', []))]


def stretches_for_file(f, lib=None, job=None):
    """Proven [start, secs, focus] stretches of a source video: by the source itself (Steam app and trailer, or URL)
    when the job's footage item for file f is given, else by the file name."""
    lib = lib or load()
    item = next((it for it in (job or {}).get('footage') or [] if it.get('file') == f), None)
    if item and item_key(item) in lib.get('files', {}):
        return sorted(lib['files'][item_key(item)].get('stretches', []), key=lambda x: x[0])
    out = []
    for e in lib.get('files', {}).values():
        if e['item'].get('file') == f:
            out += e.get('stretches', [])
    return sorted(out, key=lambda x: x[0])


def candidates(handle, lib=None):
    """footage.resolve candidates from the library: proven, decode clean (a decode failure is never recorded)."""
    out = []
    for e in sorted(for_handle(handle, lib), key=lambda e: -len(e.get('reels', []))):
        out.append({'job': dict(e['item']), 'name': e['item'].get('trailer') or e['item'].get('file'),
                    'decode_clean': True, 'library': True, 'proven_reels': len(e.get('reels', [])),
                    'stretches': len(e.get('stretches', []))})
    return out


def seed(folder, lib=None):
    import glob
    lib = lib if lib is not None else load()
    n = 0
    for p in sorted(glob.glob(os.path.join(folder, '*.json'))):
        try:
            n += len(record(json.load(open(p, encoding='utf-8')), lib=lib))
        except (OSError, ValueError):
            continue
    return n, lib


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    if argv[0] == 'record':
        qc = json.load(open(argv[2], encoding='utf-8')) if len(argv) > 2 and os.path.exists(argv[2]) else None
        print('footlib: recorded ' + ', '.join(record(json.load(open(argv[1], encoding='utf-8')), qc)) or 'nothing')
    elif argv[0] == 'seed':
        n, lib = seed(argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(HERE), 'jobs', 'done'))
        save(lib)
        print(f"footlib: {n} file records, {len(lib['files'])} files in the library")
    elif argv[0] in ('game', 'handle'):
        rows = for_game(argv[1:]) if argv[0] == 'game' else for_handle(argv[1])
        print(json.dumps([{k: r[k] for k in ('key', 'item', 'games', 'stretches', 'reels')} for r in rows],
                         ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
