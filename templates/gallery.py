"""The templates gallery's data: cards/gallery.json (build 9 Nov 2026).

One entry per Reel template in formats.TEMPLATES: its family, what it is, its opening beat, the news kinds that map to
it, how often it ran in the last 30 days (format ledger), and its latest examples with the Reel, strip and sheet as
public URLs (dxb-assets is public). A layouts entry describes the two footage layouts (fill, showcase). Examples are
matched from the format ledger's story names to the Reels under cards/ by name; an entry without a match keeps its
name and date only. No Publer ids, no tokens.

    python3 templates/gallery.py [out]      writes cards/gallery.json (reads the tree with git ls-tree, no blobs)
"""
import datetime, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import formats as F  # noqa: E402

RAW = 'https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/'
PER = 3


def tree(ref='HEAD'):
    try:
        out = subprocess.check_output(['git', '-C', ROOT, 'ls-tree', '-r', '--name-only', ref, 'cards/'], text=True)
    except subprocess.CalledProcessError:
        return []
    return [p for p in out.split('\n') if p]


def reels(paths):
    """{base name: {'reel': path, 'strip': path, 'sheet': path}} for the newest version of each Reel."""
    out = {}
    for p in sorted(paths):
        m = re.match(r'cards/\d{4}-\d{2}/(.+?)-reel-v(\d+)\.mp4$', p)
        if m:
            base, v = m.group(1), int(m.group(2))
            if base not in out or v >= out[base]['v']:
                d = os.path.dirname(p)
                out[base] = {'v': v, 'reel': p, 'strip': f'{d}/{base}-strip.jpg', 'sheet': f'{d}/{base}-sheet.jpg'}
    have = set(paths)
    for e in out.values():
        for k in ('strip', 'sheet'):
            if e[k] not in have:
                e[k] = None
    return out


def match(story, found):
    name = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', story)
    if name in found:
        return found[name]
    words = set(name.split('-'))
    best, score = None, 0.0
    for base, e in found.items():
        b = set(base.split('-'))
        s = len(words & b) / max(1, len(words | b))
        if s > score:
            best, score = e, s
    return best if score >= 0.6 else None


def build(ref='HEAD', now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    ledger = json.load(open(os.path.join(HERE, 'assets', 'format-ledger.json')))
    found = reels(tree(ref))
    since = (now - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%MZ')
    kinds = {}
    for k, ts in F.NEWS_MAP.items():
        for t in ts:
            kinds.setdefault(t, []).append(k)
    family = {t: fam for fam, ts in F.FAMILIES.items() for t in ts}
    out = []
    for t, what in F.TEMPLATES.items():
        rows = [e for e in ledger if e.get('format') == t]
        ex = []
        for e in sorted(rows, key=lambda e: e.get('at', ''), reverse=True):
            m = match(e.get('name', ''), found)
            item = {'story': e.get('name'), 'at': e.get('at'), 'skin': e.get('skin')}
            if m:
                item.update({k: RAW + m[k] for k in ('reel', 'strip', 'sheet') if m.get(k)})
            ex.append(item)
            if len([x for x in ex if 'reel' in x]) >= PER or len(ex) >= PER * 3:
                break
        ex = ([x for x in ex if 'reel' in x] + [x for x in ex if 'reel' not in x])[:PER]
        out.append({'template': t, 'family': family.get(t, 'other'), 'what': what, 'opener': F.OPENERS.get(t),
                    'kinds': sorted(kinds.get(t, [])), 'runs_30d': sum(1 for e in rows if e.get('at', '') >= since),
                    'last_run': max((e.get('at', '') for e in rows), default=None), 'examples': ex})
    layouts = [
        {'layout': 'fill', 'what': 'the default: 16:9 footage fills 9:16, cropped to the subject (up to 2x); headline '
                                   'on the soft band over the picture for 3.5 s, lines low on the picture'},
        {'layout': 'showcase', 'what': 'trailer news, or a source that fails the quality gate enlarged: the footage '
                                       'uncropped at its own width between two bands on the flat ground; chip and '
                                       'headline in the top band all the way; lines, key facts and credit as text in '
                                       'the bottom band; never an empty band, never a blur; "layout": "showcase" with '
                                       '"showcase_reason" (9 Nov 2026)'},
    ]
    return {'generated_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'templates': out, 'layouts': layouts,
            'rules': {'card_led_max': f'{F.CARD_MAX} in {F.WINDOW}', 'day_max': F.DAY_MAX,
                      'no_third_in_a_row': True}}


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'cards', 'gallery.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = build(os.environ.get('GALLERY_REF', 'HEAD'))
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f"gallery: {len(data['templates'])} templates, "
          f"{sum(1 for t in data['templates'] for x in t['examples'] if 'reel' in x)} examples with a Reel -> {path}")
