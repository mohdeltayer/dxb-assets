"""People photo library (Mohammad, 22 Nov 2026, after the Pokken Tournament Reel showed a game frame in Harada's window).

A permanent set of official photos per person, each with its source and on-screen credit in the rights register
templates/assets/people.json; the photos live under live/people/<key>.jpg. Sources, in order: the company's press kit or
page, the event organiser's release photo, Wikimedia Commons with its licence. Never social-media crops, fan edits or
AI likenesses. A person joins the second time they are in the news (`python3 templates/people.py add ...` after the
photo is committed).

    python3 templates/people.py list            # every person, photo or not, with the licence
    python3 templates/people.py find <text>     # who the text names, if anyone in the register
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTER = os.path.join(HERE, 'assets', 'people.json')


def load(path=None):
    try:
        with open(path or REGISTER, encoding='utf-8') as f:
            return json.load(f).get('people', {})
    except (OSError, ValueError):
        return {}


def _forms(e):
    out = [e.get('name_latin') or ''] + list(e.get('aliases') or [])
    if e.get('name_ar'):
        out.append(e['name_ar'])
    return [x for x in out if x and len(x) > 3]


def lookup(text, people=None):
    """(key, entry) for the first register person the text names (Latin name, an alias or the Arabic name), else None.
    Latin forms match whole words, any case."""
    t = str(text or '')
    best = None
    for k, e in (people if people is not None else load()).items():
        for f in _forms(e):
            if re.search('[A-Za-z]', f):
                m = re.search(r'(?<![A-Za-z])' + re.escape(f) + r'(?![A-Za-z])', t, re.I)
            else:
                m = re.search(re.escape(f), t)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), k, e)
    return (best[1], best[2]) if best else None


def plate_name(entry, table=None):
    """The name on the plate (item 3): the Arabic form when names-ar lists the person, else the Latin as given."""
    la = entry.get('name_latin') or ''
    if table is None:
        try:
            sys.path.insert(0, HERE)
            import slip as _S
            table = _S._names_table()
        except Exception:                               # noqa: BLE001
            table = {}
    return table.get(la.lower()) or la


def photo_of(entry):
    """(repo path, credit, focus) when the person has a photo in the library, else None."""
    p = entry.get('photo')
    if not p:
        return None
    return p, entry.get('credit_ar'), tuple(entry.get('focus') or (0.5, 0.35))


COMMONS = 'https://commons.wikimedia.org/w/api.php?'
UA = {'User-Agent': 'dxb-people-library/1.0 (official photo library; one request at a time)'}
LONG_SIDE = 1600
LICENCES_OK = ('CC0', 'Public domain', 'PDM', 'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0', 'CC BY-SA 2.0', 'CC BY-SA 3.0',
               'CC BY-SA 4.0', 'CC BY-SA 3.0 de')


def _get(url, tries=6):
    import time
    import urllib.error
    import urllib.request
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def fetch(keys=None, path=None, gap=20):
    """Downloads every register photo that has a Commons file and no committed photo yet: a standard 1280 px thumbnail
    (Commons serves only listed sizes), its licence and author read from the file page, saved as live/people/<key>.jpg
    with the credit «الصورة: <author>، ويكيميديا كومنز، <licence>». A licence outside LICENCES_OK is refused."""
    import io
    import re as _re
    import time
    import urllib.parse
    from PIL import Image
    path = path or REGISTER
    with open(path, encoding='utf-8') as f:
        reg = json.load(f)
    done = []
    for k, e in reg['people'].items():
        if (keys and k not in keys) or not e.get('commons_title'):
            continue
        out = os.path.join(ROOT, 'live', 'people', k + '.jpg')
        if e.get('photo') and os.path.exists(out):
            continue
        q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'titles': e['commons_title'], 'prop': 'imageinfo',
                                    'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1280})
        try:
            ii = list(json.loads(_get(COMMONS + q))['query']['pages'].values())[0]['imageinfo'][0]
        except Exception as ex:                         # noqa: BLE001  refused or rate-limited: the next run takes it
            print(f'people: {k}: file page not read ({ex}); left for the next run', flush=True)
            continue
        m = ii.get('extmetadata', {})
        clean = lambda s: _re.sub(r'\s+', ' ', _re.sub(r'<[^>]+>', '', s or '')).strip()
        lic = clean(m.get('LicenseShortName', {}).get('value'))
        if not any(lic.startswith(x) for x in LICENCES_OK):
            print(f'people: {k}: licence {lic!r} not on the list; skipped', flush=True)
            continue
        time.sleep(gap)
        try:
            raw = _get(ii['thumburl'] if ii.get('width', 0) > 1280 and ii.get('thumburl') else ii['url'])
        except Exception as ex:                         # noqa: BLE001
            print(f'people: {k}: image not fetched ({ex}); left for the next run', flush=True)
            continue
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        if e.get('crop'):                               # head and shoulders from a full-length photo (fractions x0 y0 x1 y1)
            x0, y0, x1, y1 = e['crop']
            im = im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
            e['derivative'] = 'cropped to head and shoulders'
        im.thumbnail((LONG_SIDE, LONG_SIDE))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im.save(out, quality=90)
        author = clean(m.get('Artist', {}).get('value'))[:80] or 'unknown'
        e.update({'photo': f'live/people/{k}.jpg', 'source': 'Wikimedia Commons', 'source_url': ii.get('descriptionurl'),
                  'licence': lic, 'licence_url': clean(m.get('LicenseUrl', {}).get('value')) or None, 'author': author,
                  'size': list(im.size), 'credit_ar': f'الصورة: {author}، ويكيميديا كومنز، {lic}'})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(reg, f, ensure_ascii=False, indent=1)
        done.append(k)
        print(f'people: {k} {im.size} {lic} by {author}', flush=True)
        time.sleep(gap)
    return done


def main(argv):
    if argv and argv[0] == 'fetch':
        fetch(argv[1:] or None)
        return 0
    if not argv or argv[0] not in ('list', 'find'):
        print(__doc__)
        return 2
    ppl = load()
    if argv[0] == 'list':
        for k, e in sorted(ppl.items()):
            print(f"{k:16} {e.get('name_latin', ''):22} {'photo' if e.get('photo') else 'NO PHOTO':8} "
                  f"{e.get('licence') or '-':14} {e.get('source_url') or e.get('searched') or ''}")
        return 0
    hit = lookup(' '.join(argv[1:]), ppl)
    print(json.dumps(hit and {'key': hit[0], **hit[1]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
