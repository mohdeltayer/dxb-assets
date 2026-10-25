#!/usr/bin/env python3
"""The no-feed official pages of the hourly watch, as a script (advisor Phase 1 step 5, 25 Oct 2026).

    python3 newsroom/watch_pages.py            # prints new items and pages that need a look
    python3 newsroom/watch_pages.py --baseline # records what is there now, prints nothing new

Reads each page with a browser user agent, keeps the links that look like articles (one pattern per
site), compares them with newsroom/page-watch-seen.json and prints only links not seen before, one line
each: source, title, URL. A page that fails, or yields far fewer article links than it usually does
(a layout change or a page drawn by script), goes under "needs a look:" so the Watcher (haiku) reads only
those. Runs beside the Watcher until the switch is agreed; it never writes watch-seen.json.
"""
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, 'page-watch-seen.json')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/130.0 Safari/537.36')

# name, page, article-link pattern (matched against the absolute URL), minimum links expected
PAGES = [
    ('Nintendo US', 'https://www.nintendo.com/us/whatsnew/', r'nintendo\.com/us/whatsnew/[^/?#]+/?$', 5),
    ('Capcom IR', 'https://www.capcom.co.jp/ir/english/news/', r'capcom\.co\.jp/ir/english/news/html/e\d+\.html$', 5),
    ('Square Enix HD', 'https://www.hd.square-enix.com/eng/news/', r'hd\.square-enix\.com/eng/news/pdf/[^/]+\.pdf$', 3),
    ('Bandai Namco', 'https://www.bandainamcoent.com/news', r'bandainamcoent\.com/news/[a-z0-9-]+$', 3),
    ('Konami JP', 'https://www.konami.com/games/jp/ja/topics/', r'konami\.com/games/jp/ja/topics/\d+/?$', 3),
    ('EA', 'https://www.ea.com/news', r'ea\.com/news/[a-z0-9-]+$', 5),
    ('Ubisoft', 'https://news.ubisoft.com/en-us/', r'news\.ubisoft\.com/en-us/article/[A-Za-z0-9]+/[a-z0-9-]+$', 3),
    ('Riot', 'https://www.riotgames.com/en/news', r'riotgames\.com/en/news/[a-z0-9-]+$', 5),
    ('The Game Awards', 'https://thegameawards.com/news', r'thegameawards\.com/news/[a-z0-9-]+$', 3),
    ('Famitsu', 'https://www.famitsu.com/', r'famitsu\.com/article/\d{6}/\d+$', 10),
]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href, self._text = dict(attrs).get('href'), []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            self.out.append((self._href, ' '.join(' '.join(self._text).split())))
            self._href = None


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', 'replace')


def articles(page, pattern):
    p = Links()
    p.feed(fetch(page))
    found = {}
    for href, text in p.out:
        if not href:
            continue
        url = urljoin(page, html.unescape(href)).split('#')[0]
        if re.search(pattern, url):
            title = text or url.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ')
            if len(title) > len(found.get(url, '')):
                found[url] = title[:160]
    return found


def main(baseline=False):
    seen = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    new, look = [], []
    for name, page, pattern, minimum in PAGES:
        try:
            found = articles(page, pattern)
        except Exception as e:  # noqa: BLE001 - every failure is reported, none stops the run
            look.append(f'{name}: fetch failed ({type(e).__name__}) {page}')
            continue
        if len(found) < minimum:
            look.append(f'{name}: {len(found)} article links (expected {minimum}+), layout changed or drawn by script {page}')
        for url, title in found.items():
            if url not in seen:
                seen[url] = {'source': name, 'title': title, 'first_seen': now}
                if not baseline:
                    new.append(f'{now} {name}: {title} {url}')
    json.dump(seen, open(SEEN, 'w'), indent=1, ensure_ascii=False)
    print('\n'.join(new) if new else 'nothing new')
    if look:
        print('needs a look:\n' + '\n'.join(look))


if __name__ == '__main__':
    main('--baseline' in sys.argv)
