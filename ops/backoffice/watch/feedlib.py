"""Finds and imports newsroom/watch_feeds.py and newsroom/watch_pages.py without changing them.

The service runs from a clone of dxb-assets (default ~/dxb-assets), so the source lists the news
desk edits arrive with the service's own `git pull`. WATCH_NEWSROOM points at another folder.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
NEWSROOM = os.environ.get('WATCH_NEWSROOM') or os.path.join(REPO, 'newsroom')

_mods = {}


def _load(name):
    if name not in _mods:
        if not os.path.isfile(os.path.join(NEWSROOM, name + '.py')):
            raise ImportError('%s.py not found in %s (git sparse-checkout add newsroom)' % (name, NEWSROOM))
        if NEWSROOM not in sys.path:
            sys.path.insert(0, NEWSROOM)
        _mods[name] = importlib.import_module(name)
    return _mods[name]


def watch_feeds():
    return _load('watch_feeds')


def watch_pages():
    return _load('watch_pages')
