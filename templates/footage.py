"""Footage resolver (adv-20261117-server-speed-for-p2 B, Mohammad 17 Nov 2026).

Case: on 17 Nov Splatoon Raiders lost a run because its footage address came from a related product on Nintendo's US
page (another nsuid), and the Director sent it back. The model hunted for addresses by reading pages. Now the server
returns them: given a game, the official footage with its job entry, duration, size, bitrate, letterbox and a full
decode check, in one dispatch (prerender.yml mode `footage`), written as FOOTAGE_JSON in the log and footage.json in
the run summary. The model copies a `job` entry into its job's "footage" as it is.

    python3 templates/footage.py <source> [--name <file stem>] [--max N] [--out footage.json] [--no-check]

<source> is one of (nothing else is read):
  steam:<appid> or a store.steampowered.com/app/<appid> URL     the app's Steam trailers (HLS, 1080p)
  https://www.nintendo.com/us/store/products/<slug>/              the product's OWN gallery videos only: the product
                                                                  is the page's own (its analytics product, else the
                                                                  Product whose urlKey is the slug), and only publicIds
                                                                  under its nsuid are kept, never a related product's
  https://www.ign.com/videos/<slug>                               the page's own video (the first one it names), its
                                                                  widest MP4 (IGN serves 640 to 3840 wide)
  https://www.playstation.com/<locale>/games/<slug>/              the page's gmedia.playstation.com MP4 clips

Per candidate: {"name", "kind", "job": {footage entry}, "duration", "width", "height", "fps", "mbps", "rows" (picture
rows after the letterbox crop), "letterboxed", "decode_clean" (true/false, or null when not checked), "note"}.
Ordered best first: not letterboxed, decode clean, larger, longer. Read-only: nothing is committed or posted.
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
MAX = 6               # candidates checked per source
CHECK_SECS = 240      # whole decode check budget; candidates past it carry decode_clean null
HOSTS = ('store.steampowered.com', 'www.nintendo.com', 'www.ign.com', 'www.playstation.com')


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def _slug(url):
    return [p for p in urllib.parse.urlparse(url).path.split('/') if p][-1]


def _stem(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60] or 'footage'


def classify(source):
    """('steam', appid) | ('nintendo', url) | ('ign', url) | ('playstation', url); anything else is refused."""
    s = source.strip()
    m = re.fullmatch(r'steam:(\d{1,10})', s) or re.fullmatch(r'\d{3,10}', s)
    if m:
        return 'steam', m.group(1) if m.groups() else m.group(0)
    u = urllib.parse.urlparse(s)
    if u.scheme != 'https' or u.netloc not in HOSTS:
        raise SystemExit(f'footage: not an allowed source: {source!r} (steam:<appid>, or https on {", ".join(HOSTS)})')
    if u.netloc == 'store.steampowered.com':
        m = re.match(r'/app/(\d+)', u.path)
        if not m:
            raise SystemExit('footage: a Steam URL must be /app/<appid>')
        return 'steam', m.group(1)
    if u.netloc == 'www.nintendo.com':
        if not re.match(r'/[a-z]{2}(-[a-z]{2})?/store/products/[A-Za-z0-9._-]+/?$', u.path):
            raise SystemExit('footage: a Nintendo URL must be a store product page (/us/store/products/<slug>/)')
        return 'nintendo', s
    if u.netloc == 'www.ign.com':
        if not re.match(r'/videos/[A-Za-z0-9._-]+/?$', u.path):
            raise SystemExit('footage: an IGN URL must be a video page (/videos/<slug>)')
        return 'ign', s
    return 'playstation', s


# ---------------------------------------------------------------------------------------------------------- sources

def steam(appid, name):
    import trailer
    out = []
    for t in trailer.steam_trailers(appid)[:MAX]:
        if not t.get('hls'):
            continue
        tid = re.search(r'/(\d+)/', t['hls'])
        stem = f"{name}-{_stem(t['name'])}"
        job = {'file': stem + '.mp4', 'steam': int(appid), 'trailer': t['name'], 'start': 0, 'seconds': 120}
        if tid:
            job['trailer_id'] = tid.group(1)
        out.append({'name': t['name'], 'kind': 'steam', 'probe': t['hls'], 'job': job})
    return out


def nintendo_own(html, url):
    """(nsuid, product name, [publicId]) of the page's own product: never a related product's videos."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit('footage: the Nintendo page has no product data (__NEXT_DATA__)')
    data = json.loads(m.group(1))
    pp = data.get('props', {}).get('pageProps', {})
    own = (pp.get('analytics') or {}).get('product') or {}
    nsuid, name = own.get('nsuid'), own.get('name')
    slug = _slug(url)
    apollo = pp.get('initialApolloState') or {}
    prod = None
    for k, v in apollo.items():
        if not (k.startswith('Product') and isinstance(v, dict)):
            continue
        if (nsuid and v.get('nsuid') == nsuid) or (not nsuid and v.get('urlKey') == slug):
            prod = v
            break
    if prod is None:
        raise SystemExit(f'footage: the Nintendo page names no product of its own (slug {slug})')
    nsuid = nsuid or prod.get('nsuid')
    name = name or prod.get('name')
    vids = [g['publicId'] for g in (prod.get('productGallery') or [])
            if isinstance(g, dict) and g.get('resourceType') == 'video' and f'/{nsuid}/' in g.get('publicId', '')]
    return nsuid, name, vids


def nintendo(url, name):
    nsuid, pname, vids = nintendo_own(_get(url), url)
    out = []
    for i, pid in enumerate(vids[:MAX]):
        src = f'https://assets.nintendo.com/video/upload{pid}.mp4'
        out.append({'name': f'{pname} gallery video {i + 1}', 'kind': 'nintendo', 'probe': src, 'nsuid': nsuid,
                    'job': {'file': f'{name}-nintendo-{i + 1}.mp4', 'url': src}})
    if not out:
        print(f'footage: {pname} (nsuid {nsuid}) has no video in its own gallery', flush=True)
    return out


def ign(url, name):
    html = _get(url)
    mp4s = re.findall(r'https://assets\.ign\.com/videos/zencoder/[0-9/]+/(\d+)/([0-9a-f-]+-\d+)\.mp4', html)
    if not mp4s:
        return []
    own = mp4s[0][1]                              # the page's own video is the first one it names
    widths = sorted({int(w) for w, v in mp4s if v == own})
    best = max(widths)
    src = next(f'https://assets.ign.com/videos/zencoder/{p}/{best}/{own}.mp4'
               for p in re.findall(r'https://assets\.ign\.com/videos/zencoder/([0-9/]+?)/\d+/' + re.escape(own), html)[:1])
    title = re.search(r'<title>([^<]+)</title>', html)
    return [{'name': (title.group(1).split('|')[0].strip() if title else _slug(url)), 'kind': 'ign', 'probe': src,
             'widths': widths, 'job': {'file': f'{name}-ign.mp4', 'url': src, 'referer': 'https://www.ign.com/'}}]


def playstation(url, name):
    html = _get(url)
    urls = list(dict.fromkeys(re.findall(r'https://gmedia\.playstation\.com/[^"\'\\\s]+?\.mp4', html)))
    slug = _slug(url)
    urls = [u for u in urls if f'/{slug}/' in u] or urls        # the page's own game first; hardware clips drop
    urls = [u for u in urls if '-mobile-' not in u] or urls     # the desktop cut is the full frame
    return [{'name': os.path.basename(u), 'kind': 'playstation', 'probe': u,
             'job': {'file': f'{name}-ps-{i + 1}.mp4', 'url': u}} for i, u in enumerate(urls[:MAX])]


# ----------------------------------------------------------------------------------------------------------- checks

def probe(src, referer=None):
    hdr = ['-headers', f'Referer: {referer}\r\n'] if referer else []
    r = subprocess.run(['ffprobe', '-v', 'error', '-user_agent', UA] + hdr + ['-show_entries',
                        'format=duration,bit_rate:stream=codec_type,width,height,r_frame_rate,bit_rate', '-of', 'json', src],
                       capture_output=True, text=True, timeout=90)
    d = json.loads(r.stdout or '{}')
    v = [s for s in d.get('streams', []) if s.get('codec_type') == 'video']
    v = max(v, key=lambda s: (s.get('height') or 0)) if v else {}
    fmt = d.get('format', {})
    n, dd = (str(v.get('r_frame_rate') or '0/1').split('/') + ['1'])[:2]
    br = float(v.get('bit_rate') or fmt.get('bit_rate') or 0)
    return {'duration': round(float(fmt.get('duration') or 0), 2), 'width': v.get('width'), 'height': v.get('height'),
            'fps': round(float(n) / float(dd or 1), 2) if float(dd or 1) else None, 'mbps': round(br / 1e6, 2) if br else None}


def check(c, tmp, deadline):
    """Download the candidate once (Steam: the first 120 s of the HLS, as render_job fetches it), decode it in full,
    read the letterbox at three points and its bitrate."""
    import decodecheck as DC
    import reel
    p = probe(c['probe'], c['job'].get('referer'))
    c.update(p)
    if time.time() > deadline:
        c['decode_clean'], c['note'] = None, 'not downloaded: the check budget ran out'
        return c
    dst = os.path.join(tmp, c['job']['file'])
    try:
        if c['kind'] == 'steam':
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', c['probe'], '-t', '120', '-c', 'copy', dst],
                           check=True, timeout=300)
        else:
            hdr = {'User-Agent': UA}
            if c['job'].get('referer'):
                hdr['Referer'] = c['job']['referer']
            with urllib.request.urlopen(urllib.request.Request(c['probe'], headers=hdr), timeout=300) as r, \
                    open(dst, 'wb') as fh:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    fh.write(b)
    except Exception as e:                                      # noqa: BLE001
        c['decode_clean'], c['note'] = None, f'download failed: {str(e)[:120]}'
        return c
    c['size_mb'] = round(os.path.getsize(dst) / 1e6, 1)
    q = probe(dst)
    c.update({k: v for k, v in q.items() if v})
    try:                                          # the source quality floor the render uses (24 Oct 2026)
        import decodecheck as DC0
        c['lowbit'] = bool(c.get('mbps') and c['mbps'] < DC0.bitrate_floor(c['width'], c['height'], c.get('fps') or 30))
    except Exception:                                           # noqa: BLE001
        pass
    if not c.get('mbps') and c.get('duration'):
        c['mbps'] = round(os.path.getsize(dst) * 8 / c['duration'] / 1e6, 2)
    errs = DC.decode_errors(dst)
    c['decode_clean'] = not errs
    if errs:
        c['note'] = f'{len(errs)} decode errors, first: {errs[0][:100]}'
    rows = []
    dur = c.get('duration') or 0
    for t in (0.2, 0.5, 0.8):
        try:
            rows.append(reel._bars(dst, max(0.0, dur * t), 2.0)[1])
        except Exception:                                       # noqa: BLE001
            pass
    h = c.get('height') or 0
    if rows:
        c['rows'] = min(rows)
        c['letterboxed'] = bool(h and c['rows'] < h - max(8, 0.03 * h))
    os.remove(dst)
    return c


def resolve(source, name=None, do_check=True, max_n=None):
    global MAX
    if max_n:
        MAX = int(max_n)
    kind, arg = classify(source)
    name = _stem(name or (f'steam-{arg}' if kind == 'steam' else _slug(arg)))
    cands = {'steam': steam, 'nintendo': nintendo, 'ign': ign, 'playstation': playstation}[kind](arg, name)
    deadline = time.time() + CHECK_SECS
    if do_check and cands:
        tmp = tempfile.mkdtemp(prefix='footage-')
        try:
            with cf.ThreadPoolExecutor(max_workers=3) as ex:
                cands = list(ex.map(lambda c: check(c, tmp, deadline), cands))
        finally:
            subprocess.run(['rm', '-rf', tmp])
    else:
        for c in cands:
            c.update(probe(c['probe'], c['job'].get('referer')))
            c['decode_clean'] = None
    for c in cands:
        c.pop('probe', None)
    cands.sort(key=lambda c: (bool(c.get('letterboxed')), c.get('decode_clean') is False, -(c.get('height') or 0),
                              -(c.get('duration') or 0)))
    return {'source': source, 'kind': kind, 'candidates': cands,
            **({'nsuid': cands[0].get('nsuid')} if kind == 'nintendo' and cands else {})}


def summary(r):
    lines = [f"footage: {r['source']} ({r['kind']}): {len(r['candidates'])} candidate(s)"]
    for c in r['candidates']:
        lines.append(f"  {c['job']['file']}: {c.get('width')}x{c.get('height')} {c.get('fps')} fps {c.get('duration')} s "
                     f"{c.get('mbps')} Mbps{' LOWBIT' if c.get('lowbit') else ''}, rows {c.get('rows')}{' LETTERBOXED' if c.get('letterboxed') else ''}, decode "
                     f"{ {True: 'clean', False: 'ERRORS', None: 'not checked'}[c.get('decode_clean')] }  {c['name']}")
    return '\n'.join(lines)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        raise SystemExit(__doc__)
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None          # noqa: E731
    r = resolve(argv[0], opt('--name'), '--no-check' not in argv, opt('--max'))
    print(summary(r), flush=True)
    print('FOOTAGE_JSON: ' + json.dumps(r, ensure_ascii=False), flush=True)
    if opt('--out'):
        json.dump(r, open(opt('--out'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 0 if r['candidates'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
