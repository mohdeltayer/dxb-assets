"""Feed half of the hourly watch (Mohammad, 12 Oct 2026: "yes" to reading the
official feeds directly after five sources had been refusing the watcher).

Reads every RSS/Atom feed in FEEDS with a browser user agent (Xbox Wire refuses
a bare script request but serves its feed to a browser), compares each item
with newsroom/watch-seen.json, appends the new ones, and prints them one per
line: published (UTC), source, title, URL. Then a "failed:" line for feeds that
did not load, so the watch report says what it could not read.

    python3 newsroom/watch_feeds.py            # check and record
    python3 newsroom/watch_feeds.py --dry-run  # check only, record nothing

Pages with no feed (Capcom, Bandai Namco, EA, Ubisoft, Riot, Konami JP topics,
Square Enix HD, Famitsu, TGA, Nintendo US whatsnew) stay with the Watcher
agent. Google News entries are a backstop for sites that refuse us (Rockstar,
Epic/Fortnite, Blizzard, Sega): they lag by hours and carry Google's redirect
link, so the Verifier opens the real page before anything is used. Official X
posts come through Gaming Watch, not here.
"""
import json, os, sys, datetime as dt, email.utils, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, 'watch-seen.json')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def gnews(site):
    q = urllib.parse.quote(f'site:{site} when:1d')
    return f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'


FEEDS = [
    ('PlayStation Blog', 'https://blog.playstation.com/feed/'),
    ('Xbox Wire', 'https://news.xbox.com/en-us/feed/'),
    ('Nintendo Japan', 'https://www.nintendo.com/jp/topics/c/feed/rss/'),
    ('Take-Two', 'https://ir.take2games.com/rss/news-releases.xml'),
    ('Atlus', 'https://atlus.com/feed/'),
    ('Bungie', 'https://www.bungie.net/en/rss/News'),
    ('Gematsu', 'https://www.gematsu.com/feed'),
    ('Rockstar (Google News)', gnews('rockstargames.com/newswire')),
    ('Blizzard (Google News)', gnews('news.blizzard.com')),
    ('Fortnite (Google News)', gnews('fortnite.com/news')),
    ('Sega (Google News)', gnews('sega.com')),
    ('Square Enix (Google News)', gnews('square-enix-games.com')),
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def when(s):
    if not s:
        return ''
    try:
        t = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
        except ValueError:
            return ''
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')


def items(raw, base=''):
    root = ET.fromstring(raw)
    out = []
    for it in root.iter():
        tag = it.tag.rsplit('}', 1)[-1]
        if tag not in ('item', 'entry'):
            continue
        f = {c.tag.rsplit('}', 1)[-1]: c for c in it}
        title = (f['title'].text or '').strip() if 'title' in f else ''
        link = ''
        if 'link' in f:
            link = (f['link'].text or '').strip() or f['link'].get('href', '')
        date = next((f[k].text for k in ('pubDate', 'published', 'updated', 'date') if k in f and f[k].text), '')
        if link.startswith('/'):
            link = base + link
        if title and link:
            out.append((when(date), title, link))
    return out


def main(dry):
    seen = json.load(open(SEEN))
    urls = {e['url'] for e in seen}
    titles = {(e.get('source'), e.get('title')) for e in seen}
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).strftime('%Y-%m-%dT%H:%MZ')
    new, failed = [], []
    for src, url in FEEDS:
        try:
            got = items(fetch(url), '{0.scheme}://{0.netloc}'.format(urllib.parse.urlparse(url)))
        except Exception as e:
            failed.append(f'{src} ({type(e).__name__}: {str(e)[:60]})')
            continue
        for pub, title, link in got[:15]:
            if link in urls or (src, title) in titles:
                continue
            if 'Google News' in src and (title.lstrip().startswith('-') or len(title.split(' - ')[0].split()) < 3):
                continue   # store, cart and section pages, not news
            urls.add(link); titles.add((src, title))
            new.append(dict(url=link, title=title, source=src, published=pub, first_seen=now))
    if new and not dry:
        json.dump(seen + new, open(SEEN, 'w'), ensure_ascii=False, indent=1)
    shown = [e for e in new if not e['published'] or e['published'] >= recent]   # older items are recorded, not reported
    for e in sorted(shown, key=lambda e: e['published'], reverse=True):
        print(f"{e['published'] or 'no time'} | {e['source']} | {e['title']} | {e['url']}")
    if not shown:
        print('nothing new from feeds')
    print('failed: ' + ('; '.join(failed) if failed else 'none'))


if __name__ == '__main__':
    main('--dry-run' in sys.argv)
