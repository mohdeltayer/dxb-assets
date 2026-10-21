"""Feed half of the hourly watch (Mohammad, 12 Oct 2026: "yes" to reading the
official feeds directly after five sources had been refusing the watcher).

Reads every RSS/Atom feed in FEEDS with a browser user agent (Xbox Wire refuses
a bare script request but serves its feed to a browser), compares each item
with newsroom/watch-seen.json, appends the new ones, and prints them one per
line: published (UTC), source, title, URL. Then a "failed:" line for feeds that
did not load, so the watch report says what it could not read.

    python3 newsroom/watch_feeds.py            # check and record
    python3 newsroom/watch_feeds.py --dry-run  # check only, record nothing

Pages with no feed (Capcom, Ubisoft, Riot, Konami JP topics, Square Enix HD,
Famitsu, TGA, Nintendo US whatsnew) stay with the Watcher agent. A few official
pages with no feed but a readable list or data endpoint are read here by a small
parser named in the source's third field (the Bandai Namco and EA SPORTS FC news
pages, HoYoLAB, PUBG Mobile, Supercell and the others under "Wider monitoring"
below); a parser that finds nothing reports the source as failed, so a changed
page shows in the "failed:" line instead of reading as quiet. Google News entries are a backstop for sites that refuse us (Rockstar,
Epic/Fortnite, Blizzard, Sega): they lag by hours and carry Google's redirect
link, so the Verifier opens the real page before anything is used. Official X
posts come through Gaming Watch, not here.
"""
import json, os, re, sys, html, hashlib, datetime as dt, email.utils, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, 'watch-seen.json')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def gnews(site):
    q = urllib.parse.quote(f'site:{site} when:1d')
    return f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'


# Parsers for official pages that have no feed (advisor memo, 21 Oct 2026, "Wider
# monitoring: anime, mobile, football"). Each takes the raw bytes and the site root
# and returns [(published, title, link)] like items(). Most of these pages carry a
# date but no time, so those items read 00:00Z of their day; the Verifier dates the
# story from the page itself. An empty result raises, so a changed page lands in
# the "failed:" line.
def day(s, fmt):
    return when(dt.datetime.strptime(s.strip(), fmt).strftime('%Y-%m-%d'))


def found(out):
    if not out:
        raise ValueError('no items found, page changed?')
    return out


def bandai(raw, base=''):
    # bandainamcoent.com/news: server-rendered cards, "Oct 1, 2026"
    out = []
    for m in re.finditer(r'<a class="card-link" href="(/news/[^"]+)">(.*?)</a>', raw.decode('utf-8', 'replace'), re.S):
        t = re.search(r'class="card__title">([^<]+)<', m.group(2))
        d = re.search(r'class="card__date">([^<]+)<', m.group(2))
        if t and d:
            out.append((day(d.group(1), '%b %d, %Y'), html.unescape(t.group(1).strip()), base + m.group(1)))
    return found(out)


def hoyolab(raw, base=''):
    # HoYoLAB's official news list: created_at is a Unix timestamp
    out = []
    for it in json.loads(raw)['data']['list']:
        p = it['post']
        out.append((dt.datetime.fromtimestamp(p['created_at'], dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
                    p['subject'].strip(), 'https://www.hoyolab.com/article/' + p['post_id']))
    return found(out)


def supercell(raw, base=''):
    # supercell.com/en/news: the page's __NEXT_DATA__ carries the list, "2026-10-21"
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', raw.decode('utf-8', 'replace'), re.S)
    out = [(when(a['publishDate']), a['title'].strip(), base + a['linkUrl'])
           for a in json.loads(m.group(1))['props']['pageProps']['articles']] if m else []
    return found(out)


def freefire(raw, base=''):
    # ff.garena.com/en/news: server-rendered list, "15/09/2026"
    out = []
    for m in re.finditer(r'<li id="\d+" class="news-item.*?href="([^"]+)".*?class="news-time"[^>]*>([^<]+)</span>.*?<h4 class="news-title"[^>]*>([^<]+)</h4>', raw.decode('utf-8', 'replace'), re.S):
        out.append((day(m.group(2), '%d/%m/%Y'), html.unescape(m.group(3).strip()), base + m.group(1)))
    return found(out)


def codm(raw, base=''):
    # callofduty.com/blog/mobile: blog cards tagged by game, "October 07, 2026"
    out = []
    for m in re.finditer(r'<div class="blog-card-item[^"]*"\s+data-game="([^"]*)"[^>]*>(.*?)(?=<div class="blog-card-item|$)', raw.decode('utf-8', 'replace'), re.S):
        d = re.search(r'data-date="([^"]+)"', m.group(2))
        t = re.search(r'<div class="title"[^>]*>\s*<a href="([^"]+)">\s*(.*?)\s*</a>', m.group(2), re.S)
        if d and t and 'cod-mobile' in m.group(1).split(','):
            out.append((day(d.group(1), '%B %d, %Y'), html.unescape(re.sub(r'\s+', ' ', t.group(2))), base + t.group(1)))
    return found(out)


def easportsfc(raw, base=''):
    # ea.com/games/ea-sports-fc/news: card grid, "October 19, 2026"
    out = []
    for m in re.finditer(r'<a href="([^"]+)" class="HeadlessButton_container[^"]*"[^>]*>(.*?)</a>', raw.decode('utf-8', 'replace'), re.S):
        d = re.search(r'>([A-Z][a-z]+ \d{1,2}, \d{4})</span>', m.group(2))
        t = re.search(r'LineClamp_container[^>]*>([^<]+)</span>', m.group(2))
        if d and t:
            out.append((day(d.group(1), '%B %d, %Y'), html.unescape(t.group(1).strip()), base + m.group(1)))
    return found(out)


def efootball(raw, base=''):
    # konami.com/efootball/en/topic/news/list: the list sits in the page as JSON.
    # beginDate has no zone; read as UTC (Konami does not say), the Verifier checks.
    s = raw.decode('utf-8', 'replace')
    i = s.find('newsData:')
    data = json.JSONDecoder().raw_decode(s, s.index('[', i))[0] if i >= 0 else []
    return found([(when(n['beginDate']), n['title'].strip(), f"{base}/efootball/en/topic/news/{n['id']}") for n in data])


def mangaproductions(raw, base=''):
    # manga.com.sa/news (mangaproductions.com is now an unrelated site): "June 24, 2026"
    out = []
    for m in re.finditer(r'<a v-if="!status.updated" href="([^"]+)".*?archiveListItem__date">\s*([^<]+?)\s*</div><h3 class="archiveListItem__title">([^<]+)</h3>', raw.decode('utf-8', 'replace'), re.S):
        out.append((day(m.group(2), '%B %d, %Y'), html.unescape(m.group(3).strip()), m.group(1)))
    return found(out)


def pubgmobile(raw, base=''):
    # the news page's own list service; createTime is ISO
    out = []
    for n in json.loads(raw)['data']['data']['list']:
        out.append((when(n['createTime']), n['title'].strip(), f"https://www.pubgmobile.com/en-US/news-detail.shtml?gid={n['groupId']}&pid={n['_id']}"))
    return found(out)


def pubg_request():
    # The list is a signed POST (md5 of service, function and body, computed by the
    # page's own script from public values), so this source is a ready Request.
    body = json.dumps({'userId': '1', 'sectionType': '3', 'contentPlat': 'h5', 'type': ['3', '4', '5', '6'], 'lang': ['en'],
                       'sortBy': 'timeDesc', 'offset': 0, 'limit': 15, 'sectionId': ['91088'], 'use_default_lang': False}, separators=(',', ':'))
    sign = hashlib.md5(('service=PUBGMOBILE&fn=GETPUBGMSECTION&body=' + body).encode()).hexdigest()
    return urllib.request.Request(
        'https://publicfaas.vasdgame.com/hw/backendapi/?namespace=Faas&fn=getPubgmSection&useSign=1&service=pubgmobile'
        '&pdr_appid=3157&env=prod&cluster=sg&sign=' + sign, data=body.encode(),
        headers={'Content-Type': 'application/json', 'X-PANDORA-ENV': 'PROD'})


def hoyolab_url(gid, kind):
    # kind 1 = notices (updates, maintenance), 3 = info (version news, trailers); 2 = reward events, left out
    return f'https://bbs-api-os.hoyolab.com/community/post/wapi/getNewsList?gids={gid}&page_size=12&type={kind}'


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
    # Wider monitoring: anime, mobile, football (advisor memo, 21 Oct 2026). Official
    # pages and feeds; the Verifier finds the primary and dates the story from the
    # first report as for every source. All English editions.
    ('Bandai Namco Entertainment', 'https://www.bandainamcoent.com/news', bandai),
    ('Spike Chunsoft', 'https://spike-chunsoft.com/feed/'),
    ('Manga Productions', 'https://manga.com.sa/news/', mangaproductions),
    ('Genshin Impact (HoYoverse)', hoyolab_url(2, 1), hoyolab),
    ('Genshin Impact (HoYoverse)', hoyolab_url(2, 3), hoyolab),
    ('Honkai: Star Rail (HoYoverse)', hoyolab_url(6, 1), hoyolab),
    ('Honkai: Star Rail (HoYoverse)', hoyolab_url(6, 3), hoyolab),
    ('Zenless Zone Zero (HoYoverse)', hoyolab_url(8, 1), hoyolab),
    ('Zenless Zone Zero (HoYoverse)', hoyolab_url(8, 3), hoyolab),
    ('PUBG Mobile', pubg_request(), pubgmobile),
    ('Free Fire (Garena)', 'https://ff.garena.com/en/news/', freefire),
    ('Call of Duty: Mobile', 'https://www.callofduty.com/blog/mobile', codm),
    ('Supercell', 'https://supercell.com/en/news/', supercell),
    ('EA SPORTS FC', 'https://www.ea.com/games/ea-sports-fc/news', easportsfc),
    ('eFootball (Konami)', 'https://www.konami.com/efootball/en/topic/news/list', efootball),
    # Skipped on 21 Oct 2026, nothing added for them (re-test when this list is next reviewed):
    # - Anime News Network: every feed URL (news/rss.xml, all/rss.xml, newsfeed/rss.xml, pr/rss.xml)
    #   answers 403 "Security check" to a script, even with a browser user agent.
    # - Crunchyroll Games and News: games.crunchyroll.com does not resolve through the proxy and
    #   crunchyroll.com/games answers a Cloudflare 403; crunchyroll.com/news is a client-side
    #   shell (the same 14 KB page for any path under /news, no feed, no data endpoint found).
    # - Aniplex (aniplex.co.jp, aniplexusa.com, game.aniplex.co.jp): every host answered 503 with an
    #   emergency-maintenance page on 21 Oct, so no feed could be tested; try again later.
    # - Roblox newsroom (about.roblox.com/newsroom; corp.roblox.com redirects there): the list
    #   carries no date (only /YYYY/MM/ in the URL), the date sits in each article page, and the
    #   only machine list is a 27 MB sitemap whose lastmod is the site's rebuild time. ir.roblox.com
    #   press releases sit behind a Cloudflare 403.
    # - Bandai Namco Europe (en.bandainamcoent.eu): 503 to a script; the .com news page above is read.
    # - mangaproductions.com now redirects to an unrelated site (MangaOasis); Manga Productions'
    #   own site is manga.com.sa, read above.
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
    req = url if isinstance(url, urllib.request.Request) else urllib.request.Request(url)   # a source may be a ready Request (POST)
    for k, v in {'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, text/xml, */*'}.items():
        if not req.has_header(k):
            req.add_header(k, v)
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
    src, url, *parser = feed   # an optional third field names the parser for pages that are not RSS or Atom
    try:
        full = url.full_url if isinstance(url, urllib.request.Request) else url
        return src, (parser[0] if parser else items)(fetch(url), '{0.scheme}://{0.netloc}'.format(urllib.parse.urlparse(full))), None
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
