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


# ------------------------------------------------------------------ build-time lookup (Mohammad, 23 Nov 2026, item 1)
WIKIDATA = 'https://www.wikidata.org/w/api.php?'
ROLE_EN = {'ممثل': ('actor', 'actress'), 'ممثلة': ('actress', 'actor'), 'مخرج': ('director',), 'منتج': ('producer',),
           'رئيس': ('president', 'chair', 'chief executive', 'ceo', 'head'), 'رئيسة': ('president', 'chair', 'ceo', 'head'),
           'مصمم': ('designer',), 'مصممة': ('designer',), 'كاتب': ('writer', 'author'), 'كاتبة': ('writer', 'author'),
           'ملحن': ('composer',), 'مؤسس': ('founder',), 'مبتكر': ('designer', 'creator'), 'مدير': ('director', 'manager'),
           'مديرة': ('director', 'manager')}
MIN_CROP = 230              # px across: the 460 px window enlarges it at most 2x (reel.PERSON_MAX_ZOOM)


def _json(url):
    return json.loads(_get(url))


def _role_words(role):
    out = []
    for w in re.findall('[\u0621-\u064A]+', str(role or '')):
        w = w[2:] if w.startswith('ال') else w
        out += list(ROLE_EN.get(w, ()))
    return out


def _wikidata_person(name, role=None):
    """(qid, label, description, P18 file) for the one human Wikidata finds for `name` (Arabic or Latin); when several
    humans match, the one whose English description names the role («actor», «chair» ...); otherwise None, never a
    guess between two people."""
    import urllib.parse
    lang = 'ar' if re.search('[\u0621-\u064A]', name) else 'en'
    hits = _json(WIKIDATA + urllib.parse.urlencode({'action': 'wbsearchentities', 'search': name, 'language': lang,
                                                     'uselang': 'en', 'type': 'item', 'limit': 7, 'format': 'json'}))
    ids = [h['id'] for h in hits.get('search', [])]
    if not ids:
        return None
    ents = _json(WIKIDATA + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(ids), 'format': 'json',
                                                     'props': 'claims|descriptions|labels', 'languages': 'en'}))['entities']
    humans = []
    for q in ids:
        e = ents.get(q) or {}
        cl = e.get('claims', {})
        if not any(c.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id') == 'Q5' for c in cl.get('P31', [])):
            continue
        img = next((c['mainsnak']['datavalue']['value'] for c in cl.get('P18', []) if c.get('mainsnak', {}).get('datavalue')), None)
        desc = (e.get('descriptions', {}).get('en') or {}).get('value', '')
        label = (e.get('labels', {}).get('en') or {}).get('value', '')
        humans.append((q, label, desc, img))
    if not humans:
        return None
    words = _role_words(role)
    if len(humans) > 1:
        fit = [h for h in humans if words and any(w in h[2].lower() for w in words)]
        if len(fit) != 1:
            return None
        return fit[0]
    h = humans[0]
    if words and h[2] and not any(w in h[2].lower() for w in words):
        return None                                    # one human, but not the role the story names: not risked
    return h


def _face_crop(im):
    """Head and shoulders around the largest face (OpenCV's frontal-face cascade), cut to the window's 460:540; None when
    no face is found or the crop would be under MIN_CROP px across."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    g = cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2GRAY)
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = cas.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(max(40, im.width // 20),) * 2)
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    cw = min(im.width, int(w * 2.8))
    ch = min(im.height, int(cw * 540 / 460))
    cw = int(ch * 460 / 540)
    if cw < MIN_CROP:
        return None
    cx, top = x + w / 2, y - 0.75 * h
    x0 = int(min(max(cx - cw / 2, 0), im.width - cw))
    y0 = int(min(max(top, 0), im.height - ch))
    return im.crop((x0, y0, x0 + cw, y0 + ch))


def resolve(name, role=None, latin=None, path=None):
    """Build-time lookup for a person not in the library: Wikidata's portrait (P18, on Wikimedia Commons) with a licence
    on LICENCES_OK, cropped to head and shoulders around the face, saved as live/people/<key>.jpg and added to the
    register with its source, licence, author and on-screen credit. (key, entry) or None. Never social media, fan edits or
    AI likenesses: only the Commons file Wikidata links to the person."""
    import io
    import urllib.parse
    from PIL import Image
    try:
        hit = _wikidata_person(latin or name, role)
        if not hit and latin and name and name != latin:
            hit = _wikidata_person(name, role)
    except Exception as ex:                             # noqa: BLE001
        print(f'people: lookup of {latin or name!r} failed ({ex})', flush=True)
        return None
    if not hit or not hit[3]:
        return None
    qid, label, desc, fname = hit
    try:
        q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'titles': 'File:' + fname, 'prop': 'imageinfo',
                                    'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1280})
        ii = list(_json(COMMONS + q)['query']['pages'].values())[0]['imageinfo'][0]
        m = ii.get('extmetadata', {})
        clean = lambda s: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()
        lic = clean(m.get('LicenseShortName', {}).get('value'))
        if not any(lic.startswith(x) for x in LICENCES_OK):
            print(f'people: {label}: licence {lic!r} not on the list', flush=True)
            return None
        raw = _get(ii['thumburl'] if ii.get('width', 0) > 1280 and ii.get('thumburl') else ii['url'])
    except Exception as ex:                             # noqa: BLE001
        print(f'people: {label}: Commons file not read ({ex})', flush=True)
        return None
    im = _face_crop(Image.open(io.BytesIO(raw)).convert('RGB'))
    if im is None:
        print(f'people: {label}: no face found, or the face is too small to crop', flush=True)
        return None
    key = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-') or qid.lower()
    out = os.path.join(ROOT, 'live', 'people', key + '.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.thumbnail((LONG_SIDE, LONG_SIDE))
    im.save(out, quality=90)
    author = clean(m.get('Artist', {}).get('value'))[:80]
    if not author or 'unknown' in author.lower():
        author = None
    entry = {'name_latin': label, 'aliases': [name] if name and name != label else [], 'photo': f'live/people/{key}.jpg',
             'source': 'Wikimedia Commons (Wikidata portrait)', 'wikidata': qid, 'description': desc,
             'commons_title': 'File:' + fname, 'source_url': ii.get('descriptionurl'), 'licence': lic,
             'licence_url': clean(m.get('LicenseUrl', {}).get('value')) or None, 'author': author,
             'derivative': 'cropped to head and shoulders', 'size': list(im.size), 'focus': [0.5, 0.42],
             'credit_ar': (f'الصورة: {author}، ويكيميديا كومنز، {lic}' if author else f'الصورة: ويكيميديا كومنز، {lic}'),
             'added': 'build time'}
    add(key, entry, path)
    print(f'people: {label} ({qid}, {desc}) added from Commons, {lic}, by {author}', flush=True)
    return key, entry


def add(key, entry, path=None):
    """Writes one entry into the register (merging with whatever is there now)."""
    path = path or REGISTER
    try:
        with open(path, encoding='utf-8') as f:
            reg = json.load(f)
    except (OSError, ValueError):
        reg = {'people': {}}
    reg.setdefault('people', {})[key] = entry
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)


def main(argv):
    if argv and argv[0] == 'resolve':
        print(json.dumps(resolve(argv[1], argv[2] if len(argv) > 2 else None), ensure_ascii=False, indent=1))
        return 0
    if argv and argv[0] == 'merge':                     # slip.yml: an entry built on the runner into today's register
        e = json.load(open(argv[1], encoding='utf-8'))
        add(e['key'], e['entry'])
        return 0
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
