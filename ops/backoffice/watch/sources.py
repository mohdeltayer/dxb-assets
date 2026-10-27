"""Builds the list of sources: the imported lists plus sources.yaml, with cadence and breaking flags."""
import hashlib
import os
import re
import urllib.request

import yaml

import feedlib

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.environ.get('WATCH_CONFIG') or os.path.join(HERE, 'sources.yaml')


class Source:
    def __init__(self, id, name, kind, url, reader, interval_min, breaking=False, origin='', request=None,
                 pattern=None, minimum=0):
        self.id, self.name, self.kind, self.url, self.reader = id, name, kind, url, reader
        self.interval_min, self.breaking, self.origin = int(interval_min), bool(breaking), origin
        self.request = request          # a ready urllib Request (POST sources), else the URL is fetched
        self.pattern, self.minimum = pattern, minimum

    @property
    def target(self):
        return self.request if self.request is not None else self.url


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:40]


def sid(name, url):
    return '%s-%s' % (slug(name), hashlib.sha1(url.encode()).hexdigest()[:6])


def load_config(path=None):
    with open(path or CONFIG, encoding='utf-8') as f:
        return yaml.safe_load(f)


def build(cfg=None):
    cfg = cfg or load_config()
    d = cfg.get('defaults', {})
    imp = cfg.get('imported', {})
    over = imp.get('overrides', {})
    off = set(imp.get('disabled', []))
    out = []

    def apply(name, interval, breaking=None):
        o = over.get(name, {})
        return o.get('interval_min', interval or d.get('interval_min', 15)), o.get('breaking', d.get('breaking', False) if breaking is None else breaking)

    wf = feedlib.watch_feeds()
    g = imp.get('watch_feeds', {})
    for entry in wf.OFFICIAL:
        name, target, *parser = entry
        if name in off:
            continue
        req = target if isinstance(target, urllib.request.Request) else None
        url = req.full_url if req else target
        if 'Google News' in name:
            kind, grp = 'gnews', g.get('gnews', {})
        elif parser:
            kind, grp = 'official', g.get('parsed_pages', {})
        else:
            kind, grp = 'official', g.get('official', {})
        iv, br = apply(name, grp.get('interval_min'))
        out.append(Source(sid(name, url), name, kind, url, parser[0] if parser else 'feed', iv, br, 'watch_feeds', request=req))
    for name, url in wf.OUTLETS:
        if name in off:
            continue
        iv, _ = apply(name, g.get('outlets', {}).get('interval_min'))
        out.append(Source(sid(name, url), name, 'outlet', url, 'feed', iv, False, 'watch_feeds'))

    wp = feedlib.watch_pages()
    pg = imp.get('watch_pages', {})
    for name, page, pattern, minimum in wp.PAGES:
        if name in off:
            continue
        iv, br = apply(name, pg.get('interval_min'))
        out.append(Source(sid(name, page), name, 'page', page, 'page', iv, br, 'watch_pages', pattern=pattern, minimum=minimum))

    kinds = cfg.get('kinds', {})
    for e in cfg.get('extra', []):
        kind = e['kind']
        if kind == 'youtube':
            if not kinds.get('youtube', True):
                continue
            url, reader = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + e['channel_id'], 'youtube'
        elif kind == 'x':
            if not kinds.get('x_embed', True):
                continue
            url, reader = 'https://syndication.twitter.com/srv/timeline-profile/screen-name/' + e['handle'], 'x'
        else:
            url, reader = e['url'], 'feed'
        out.append(Source(e.get('id') or sid(e['name'], url), e['name'], kind, url, reader,
                          e.get('interval_min', d.get('interval_min', 15)), e.get('breaking', False), 'config'))
        if e.get('enabled') is False:
            out.pop()
    ids = [s.id for s in out]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError('duplicate source ids: %s' % sorted(dup))
    return out
