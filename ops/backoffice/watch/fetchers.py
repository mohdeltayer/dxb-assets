"""Network and parsing for the mechanical watch: one conditional GET, and the readers that turn
a response into items {title, url, published, summary, media}.

Feeds, the parser pages of newsroom/watch_feeds.py and the article pages of
newsroom/watch_pages.py are read with the code those files already hold, so a fix to a parser
there reaches this service at its next `git pull`. What is new here: media links from feed
items, YouTube channel feeds, X's public embedded timeline, and ETag/gzip so a quiet feed costs
a few hundred bytes.
"""
import contextlib
import datetime as dt
import html
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib

import feedlib  # the imported newsroom modules, found by path

MAX_BYTES = 12_000_000
IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif')
VID_EXT = ('.mp4', '.webm', '.m3u8', '.mov', '.mkv')
AUD_EXT = ('.mp3', '.m4a', '.ogg', '.wav')


# Hosts that answer 429 to a burst: one request at a time, with a gap (seconds) between them.
HOST_GAP = {'syndication.twitter.com': 8.0}
_gate = {h: [threading.Lock(), 0.0] for h in HOST_GAP}


def polite(url):
    host = urllib.parse.urlparse(url if isinstance(url, str) else url.full_url).netloc
    g = _gate.get(host)
    if not g:
        return contextlib.nullcontext()
    return _Gap(g, HOST_GAP[host])


class _Gap:
    def __init__(self, g, gap):
        self.g, self.gap = g, gap

    def __enter__(self):
        self.g[0].acquire()
        wait = self.g[1] + self.gap - time.time()
        if wait > 0:
            time.sleep(wait)

    def __exit__(self, *exc):
        self.g[1] = time.time()
        self.g[0].release()


class Unchanged(Exception):
    """The server answered 304: nothing new since the last read."""


def http_get(target, etag=None, last_modified=None, timeout=25):
    """Return (body, etag, last_modified). Raises Unchanged on 304, urllib errors otherwise.

    `target` is a URL or a ready urllib Request (a POST source such as PUBG Mobile).
    """
    wf = feedlib.watch_feeds()
    req = target if isinstance(target, urllib.request.Request) else urllib.request.Request(target)
    for k, v in {'User-Agent': wf.UA, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, application/json, text/html, */*',
                 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9'}.items():
        if not req.has_header(k):
            req.add_header(k, v)
    if req.data is None:   # conditional reads only for plain GETs
        if etag and not req.has_header('If-none-match'):
            req.add_header('If-None-Match', etag)
        if last_modified and not req.has_header('If-modified-since'):
            req.add_header('If-Modified-Since', last_modified)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(MAX_BYTES + 1)
            enc = (r.headers.get('Content-Encoding') or '').lower()
            new_etag, new_lm = r.headers.get('ETag'), r.headers.get('Last-Modified')
    except urllib.error.HTTPError as e:
        if e.code == 304:
            raise Unchanged()
        raise
    if len(body) > MAX_BYTES:
        raise ValueError('response over %d bytes' % MAX_BYTES)
    if 'gzip' in enc:
        body = zlib.decompress(body, 47)
    elif 'deflate' in enc:
        try:
            body = zlib.decompress(body)
        except zlib.error:
            body = zlib.decompress(body, -15)
    return body, new_etag, new_lm


# ---------------------------------------------------------------- helpers

def local(tag):
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''


TAG_RE = re.compile(r'<[^>]+>')
IMG_RE = re.compile(r'<img\b[^>]*?\bsrc=["\']([^"\']+)["\']', re.I)


def clean_text(s, n=400):
    s = html.unescape(TAG_RE.sub(' ', s or ''))
    return re.sub(r'\s+', ' ', s).strip()[:n]


def media_type(url, hint=''):
    h, u = (hint or '').lower(), url.lower().split('?')[0]
    if h.startswith('image') or u.endswith(IMG_EXT):
        return 'image'
    if h.startswith('video') or u.endswith(VID_EXT):
        return 'video'
    if h.startswith('audio') or u.endswith(AUD_EXT):
        return 'audio'
    return ''


def add_media(out, url, hint='', base=''):
    url = (url or '').strip()
    if not url or url.startswith('data:'):
        return
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/') and base:
        url = base + url
    if not url.startswith('http'):
        return
    t = media_type(url, hint)
    if t and not any(m['url'] == url for m in out):
        out.append({'type': t, 'url': url})


def pick_link(el_children):
    """Atom carries several <link>; take the alternate one. RSS carries its URL as text."""
    best = ''
    for c in el_children:
        if local(c.tag) != 'link':
            continue
        href = c.get('href')
        if href:
            if c.get('rel') in (None, 'alternate'):
                return href.strip()
            best = best or href.strip()
        elif (c.text or '').strip():
            return c.text.strip()
    return best


# ---------------------------------------------------------------- readers

def read_feed(raw, base=''):
    """RSS 2.0, Atom and RSS 1.0 (rdf). Items with a title and a link only."""
    root = ET.fromstring(raw)
    if local(root.tag) not in ('rss', 'feed', 'RDF'):
        raise ValueError('not a feed (root <%s>)' % local(root.tag))
    wf = feedlib.watch_feeds()
    out = []
    for it in root.iter():
        if local(it.tag) not in ('item', 'entry'):
            continue
        kids = list(it)
        f = {}
        for c in kids:
            f.setdefault(local(c.tag), c)
        title = clean_text(''.join(f['title'].itertext()), 300) if 'title' in f else ''
        link = pick_link(kids)
        if link.startswith('/'):
            link = base + link
        date = next((f[k].text for k in ('pubDate', 'published', 'updated', 'date') if k in f and f[k].text), '')
        if not (title and link):
            continue
        media, summary = [], ''
        for c in kids:
            t = local(c.tag)
            if t in ('content', 'thumbnail', 'image') and c.get('url'):
                add_media(media, c.get('url'), c.get('type') or c.get('medium') or '', base)
            elif t == 'enclosure' and c.get('url'):
                add_media(media, c.get('url'), c.get('type') or '', base)
            elif t == 'group':   # YouTube's media:group
                for g in c:
                    if local(g.tag) in ('content', 'thumbnail') and g.get('url'):
                        add_media(media, g.get('url'), g.get('type') or '', base)
                    elif local(g.tag) == 'description' and not summary:
                        summary = clean_text(g.text)
        for k in ('encoded', 'content', 'description', 'summary'):
            if k in f:
                body = ''.join(f[k].itertext()) if len(f[k]) == 0 else ET.tostring(f[k], encoding='unicode')
                for m in IMG_RE.finditer(html.unescape(body)):
                    add_media(media, m.group(1), 'image', base)
                if not summary:
                    summary = clean_text(body)
        out.append(dict(title=title, url=link, published=wf.when(date), summary=summary, media=media[:6]))
    return out   # an empty feed is a quiet feed (a Google News search with no hits, a channel with no uploads)


def read_youtube(raw, base=''):
    items = read_feed(raw, base)
    for i in items:   # the watch page is the video; no file is downloaded here
        if 'watch?v=' in i['url'] and not any(m['type'] == 'video' for m in i['media']):
            i['media'].append({'type': 'video', 'url': i['url']})
    return items


def tuples_to_items(rows):
    """Parsers of watch_feeds.py return [(published, title, link)]."""
    return [dict(title=t, url=l, published=p, summary='', media=[]) for p, t, l in rows]


def read_page_links(raw, page, pattern, minimum):
    """The article links of a page that has no feed (newsroom/watch_pages.py PAGES)."""
    wp = feedlib.watch_pages()
    p = wp.Links()
    p.feed(raw.decode('utf-8', 'replace'))
    found = {}
    for href, text in p.out:
        if not href:
            continue
        url = urllib.parse.urljoin(page, html.unescape(href)).split('#')[0]
        if re.search(pattern, url):
            title = text or url.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ')
            if len(title) > len(found.get(url, '')):
                found[url] = title[:160]
    if len(found) < minimum:
        raise ValueError('%d article links (expected %d+), layout changed or drawn by script' % (len(found), minimum))
    return [dict(title=t, url=u, published='', summary='', media=[]) for u, t in found.items()]


X_DATE = '%a %b %d %H:%M:%S %z %Y'


def read_x_embed(raw, base=''):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', raw.decode('utf-8', 'replace'), re.S)
    if not m:
        raise ValueError('no timeline data (blocked or changed)')
    entries = json.loads(m.group(1))['props']['pageProps']['timeline']['entries']
    out = []
    for e in entries:
        t = (e.get('content') or {}).get('tweet') or {}
        text = (t.get('full_text') or t.get('text') or '').strip()
        link = t.get('permalink')
        if not (text and link) or text.startswith('RT @') or t.get('retweeted_status'):
            continue
        try:
            pub = dt.datetime.strptime(t['created_at'], X_DATE).astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
        except (KeyError, ValueError):
            pub = ''
        media = []
        for md in ((t.get('extended_entities') or {}).get('media') or (t.get('entities') or {}).get('media') or []):
            add_media(media, md.get('media_url_https'), 'image')
            mp4 = [v for v in (md.get('video_info') or {}).get('variants', []) if v.get('content_type') == 'video/mp4']
            if mp4:
                add_media(media, max(mp4, key=lambda v: v.get('bitrate', 0))['url'], 'video/mp4')
        text = html.unescape(re.sub(r'https://t\.co/\w+', '', text))
        title = re.sub(r'\s+', ' ', text).strip()[:240] or '(media only)'
        out.append(dict(title=title, url='https://x.com' + link, published=pub, summary=clean_text(text), media=media[:6]))
    if not out:
        raise ValueError('timeline has no posts')
    return out


def read_source(src, body):
    """Dispatch on the source's reader; returns a list of item dicts."""
    base = '{0.scheme}://{0.netloc}'.format(urllib.parse.urlparse(src.url))
    r = src.reader
    if r == 'feed':
        return read_feed(body, base)
    if r == 'youtube':
        return read_youtube(body, base)
    if r == 'x':
        return read_x_embed(body, base)
    if r == 'page':
        return read_page_links(body, src.url, src.pattern, src.minimum)
    if callable(r):   # a parser function of watch_feeds.py
        return tuples_to_items(r(body, base))
    raise ValueError('unknown reader %r' % (r,))


def error_text(e):
    if isinstance(e, urllib.error.HTTPError):
        return 'HTTP %d' % e.code
    if isinstance(e, (socket.timeout, TimeoutError)):
        return 'timeout'
    return '%s: %s' % (type(e).__name__, str(e)[:80])
