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
import json, os, re, sys, datetime as dt, email.utils, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, 'watch-seen.json')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def gnews(site):
    q = urllib.parse.quote(f'site:{site} when:1d')
    return f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'


OFFICIAL = [
    ('PlayStation Blog', 'https://blog.playstation.com/feed/'),
    ('Xbox Wire', 'https://news.xbox.com/en-us/feed/'),
    ('Nintendo Japan', 'https://www.nintendo.com/jp/topics/c/feed/rss/'),
    ('Take-Two', 'https://ir.take2games.com/rss/news-releases.xml'),
    ('Atlus', 'https://atlus.com/feed/'),
    ('Bungie', 'https://www.bungie.net/en/rss/News'),
    ('Rockstar (Google News)', gnews('rockstargames.com/newswire')),
    ('Blizzard (Google News)', gnews('news.blizzard.com')),
    ('Fortnite (Google News)', gnews('fortnite.com/news')),
    ('Sega (Google News)', gnews('sega.com')),
    ('Square Enix (Google News)', gnews('square-enix-games.com')),
]

# Outlets (Mohammad, 12 Oct 2026: "add resources from large blog posts especially
# ones that update quickly"). Leads, not proof: the Verifier finds the primary,
# an outlet-only story is a تقرير for a review slot, never the breaking lane.
OUTLETS = [
    ('IGN', 'https://feeds.feedburner.com/ign/news'),
    ('GameSpot', 'https://www.gamespot.com/feeds/news/'),
    ('Eurogamer', 'https://www.eurogamer.net/feed/news'),
    ('VGC', 'https://www.videogameschronicle.com/category/news/feed/'),
    ('Kotaku', 'https://kotaku.com/rss'),
    ('Polygon', 'https://www.polygon.com/rss/news/index.xml'),
    ('PC Gamer', 'https://www.pcgamer.com/rss/'),
    ('Rock Paper Shotgun', 'https://www.rockpapershotgun.com/feed/news'),
    ('The Verge', 'https://www.theverge.com/rss/games/index.xml'),
    ('Push Square', 'https://www.pushsquare.com/feeds/latest'),
    ('Pure Xbox', 'https://www.purexbox.com/feeds/latest'),
    ('Nintendo Life', 'https://www.nintendolife.com/feeds/latest'),
    ('Insider Gaming', 'https://insider-gaming.com/feed/'),
    ('GamesIndustry.biz', 'https://www.gamesindustry.biz/feed'),
    ('Game File', 'https://www.gamefile.news/feed'),
    ('Siliconera', 'https://www.siliconera.com/feed/'),
    ('Destructoid', 'https://www.destructoid.com/feed/'),
    ('Game Informer', 'https://www.gameinformer.com/news.xml'),
    ('GamesRadar', 'https://www.gamesradar.com/feeds/articletype/news/'),
    ('Dexerto', 'https://www.dexerto.com/gaming/feed/'),
    ('TheGamer', 'https://www.thegamer.com/feed/'),
    ('Gamekult (FR)', 'https://www.gamekult.com/feed.xml'),
    ('Gematsu', 'https://www.gematsu.com/feed'),
    ('Automaton (JP)', 'https://automaton-media.com/feed/'),
    ('4Gamer (JP)', 'https://www.4gamer.net/rss/index.xml'),
    ('IGN Middle East (AR)', 'https://me.ign.com/ar/feed.xml'),
    ('IGN Middle East (EN)', 'https://me.ign.com/en/feed.xml'),
    ('True Gaming (AR)', 'https://www.true-gaming.net/home/feed/'),
    ('Saudi Gamer (AR)', 'https://www.saudigamer.com/feed/'),
    ('VGA4A (AR)', 'https://www.vga4a.com/feed/'),
    ('Arab Hardware (AR)', 'https://arabhardware.net/feed'),
]
OUTLET_NAMES = {n for n, _ in OUTLETS}

STOP = set('''the a an and or of to in on for with at by from is are be as its it this that new now how why
what who will can has have after before over into out up more first all just your you our their his her
game games gaming update trailer reveals revealed announced announces review reviews report reportedly
says said gets get launch launches release releases date out coming here every one two vs'''.split())


JUNK = re.compile(r'wordle|connections hint|hints and answer|sbc solution|best (players|builds?|loadouts?|settings)|\bcodes?\b|how to |guide|walkthrough|deals?\b|\bsale\b.*\b(off|\$)|tier list|quiz|best places|where to (find|farm)|poll: vote', re.I)


def words(t):
    return {w for w in re.findall(r"[0-9a-z\u0600-\u06ff]+", t.lower().replace("'s", '')) if len(w) > 2 and w not in STOP}


def same(a, b):
    k = len(a & b)
    return k >= 3 and k >= 0.4 * min(len(a), len(b))


def cluster(entries):
    groups = []
    for e in entries:
        w = words(e['title'])
        for g in groups:
            if any(same(w, x) for x in g['w']):
                g['items'].append(e); g['w'].append(w); break
        else:
            groups.append(dict(items=[e], w=[w]))
    return groups


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


def load(feed):
    src, url = feed
    try:
        return src, items(fetch(url), '{0.scheme}://{0.netloc}'.format(urllib.parse.urlparse(url))), None
    except Exception as e:
        return src, [], f'{src} ({type(e).__name__}: {str(e)[:60]})'


def main(dry):
    seen = json.load(open(SEEN))
    urls = {e['url'] for e in seen}
    titles = {(e.get('source'), e.get('title')) for e in seen}
    T = dt.datetime.now(dt.timezone.utc)
    now = T.strftime('%Y-%m-%dT%H:%MZ')
    recent = (T - dt.timedelta(days=2)).strftime('%Y-%m-%dT%H:%MZ')
    day = (T - dt.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%MZ')
    new, junk, failed = [], [], []
    with ThreadPoolExecutor(12) as ex:
        results = list(ex.map(load, OFFICIAL + OUTLETS))
    for src, got, err in results:
        if err:
            failed.append(err); continue
        for pub, title, link in got[:30]:
            if link in urls or (src, title) in titles:
                continue
            if 'Google News' in src and (title.lstrip().startswith('-') or len(title.split(' - ')[0].split()) < 3 or 'Shop' in title):
                continue   # store, cart and section pages, not news
            urls.add(link); titles.add((src, title))
            e = dict(url=link, title=title, source=src, published=pub, first_seen=now)
            if src in OUTLET_NAMES and JUNK.search(title):
                junk.append(e); continue   # guides, puzzles and deals: recorded as seen, never reported
            new.append(e)
    if (new or junk) and not dry:
        keep = (T - dt.timedelta(days=30)).strftime('%Y-%m-%dT%H:%MZ')   # the file stays small; a month is plenty to dedupe
        json.dump([e for e in seen if e.get('first_seen', now) >= keep] + new + junk, open(SEEN, 'w'), ensure_ascii=False, indent=1)
    shown = [e for e in new if not e['published'] or e['published'] >= recent]   # older items are recorded, not reported
    off = [e for e in shown if e['source'] not in OUTLET_NAMES]
    print('OFFICIAL')
    for e in sorted(off, key=lambda e: e['published'], reverse=True):
        print(f"{e['published'] or 'no time'} | {e['source']} | {e['title']} | {e['url']}")
    if not off:
        print('nothing new')
    # outlets: one line per story, with every outlet that ran it in the last 24 hours
    fresh = {e['url'] for e in shown if e['source'] in OUTLET_NAMES}
    pool = [e for e in seen + new if e.get('source') in OUTLET_NAMES and (e.get('published') or e['first_seen']) >= day and not JUNK.search(e['title'])]
    groups = [g for g in cluster(sorted(pool, key=lambda e: e.get('published') or '')) if any(e['url'] in fresh for e in g['items'])]
    groups.sort(key=lambda g: (-len({e['source'] for e in g['items']}), max(e.get('published') or '' for e in g['items'])), reverse=False)
    groups.sort(key=lambda g: max(e.get('published') or '' for e in g['items']), reverse=True)
    groups.sort(key=lambda g: len({e['source'] for e in g['items']}), reverse=True)
    print(f'OUTLETS ({len(groups)} stories with something new; count = outlets carrying it in 24 h)')
    singles = 0
    for g in groups:
        srcs = sorted({e['source'] for e in g['items']}); f = g['items'][0]
        if len(srcs) == 1:
            singles += 1
            if singles > 25:
                continue   # one outlet only: the newest 25 are enough for a lead sheet
        relay = ' | AR RELAY: date it from the first report' if all(x.endswith('(AR)') for x in srcs) else ''   # Mohammad, 17 Oct
        print(f"{len(srcs)} | {f['published'] or 'no time'} | {f['title']} | {', '.join(srcs)} | {f['url']}{relay}")
    print('failed: ' + ('; '.join(failed) if failed else 'none'))


if __name__ == '__main__':
    main('--dry-run' in sys.argv)
