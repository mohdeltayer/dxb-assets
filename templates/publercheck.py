#!/usr/bin/env python3
"""Publer is the source of truth (Mohammad, 23 Nov 2026, after inKONBINI posted twice).

Production 1 scheduled the inKONBINI Reel at 08:30Z through the connector; Production 2 scheduled the same story again at
09:30Z under its own commitment name, and presubmit only compared commitment names. Before any story is prepared, and
again just before every submit, Publer's scheduled posts and the last 48 hours of published posts are read for the same
story or the same game and news.

Matching (one function for the server, the slip lane and the sessions):
  - same story: the post carries the label story:<job name> (every submit adds it from 23 Nov), or its Reel is the same
    job name (any -reel-vN).
  - same news: the post names the same game (gamekey: GTA VI, Grand Theft Auto VI and GTA 6 meet) and its caption shares
    at least SAME_NEWS of the smaller set of words, names and numbers with ours. Measured on 23 Nov: inKONBINI v1 against
    v2 0.83; the day's different GTA VI stories (Jordan, Neuralink, memorial, McQueen, the album) 0.15 at most.
A match on a published post stops the story (skip it, note it on the board). A match on a scheduled post: the same story
in a newer version replaces it (rule 3: v2 replaces v1 only while v1 has not posted), anything else stops.

    python3 templates/publercheck.py posts <posts.json> --story <story id> [--game "<name>"] [--text "<caption>"]
        posts.json: the list_publer_posts results (scheduled, and published for 48 hours) saved as JSON; prints the
        verdict line for the board. Production 2 runs it on the connector's lists before preparing and before submitting.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SAME_NEWS = 0.45
WINDOW_H = 48
STOP = {'ذكر', 'موقع', 'المصدر', 'اللعبة', 'لعبة', 'اللقطات', 'صفحة', 'steam', 'الرسمي', 'العرض', 'تقرير', 'بحسب',
        'وبحسب', 'حسب', 'بيان', 'رسمي', 'الموقع', 'games', 'press', 'وفق', 'الناشر', 'نقلا', 'رسمية'}


def toks(s):
    s = re.sub(r'#\S+', '', str(s or ''))
    s = re.sub(r'https?://\S+', '', s)
    ar = set(re.findall(r'[ء-ي]{4,}', s))
    la = set(w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9]{2,}', s))
    nums = set(re.findall(r'\d[\d.,]*\d|\d', s))
    return (ar | la | nums) - STOP


def similarity(a, b):
    A, B = toks(a), toks(b)
    return len(A & B) / max(1, min(len(A), len(B)))


def game_in(game, text):
    """True when the caption names the game (its normalised key or one of its words of 4+ letters in order)."""
    if not game:
        return False
    try:
        import gamekey as GK
        g = GK.key(game)
        names = {game, g} | set(getattr(GK, 'ALIASES', {}).get(g, []) if isinstance(getattr(GK, 'ALIASES', None), dict) else [])
    except Exception:                                   # noqa: BLE001
        names = {game}
    low = str(text or '').lower()
    for n in names:
        n = str(n or '').strip().lower()
        if n and (n in low or n.replace(' ', '') in low.replace(' ', '')):
            return True
    return False


def job_of_media(name):
    return re.sub(r'-reel-v\d+\.mp4$', '', os.path.basename(str(name or '')))


def norm_post(p):
    """A Publer post from the API or from the connector's list: {id, state, at, text, labels, media}."""
    labels = []
    for l in p.get('labels') or []:
        labels.append(l.get('name') if isinstance(l, dict) else str(l))
    media = [m.get('name') or m.get('path') or '' for m in (p.get('media') or []) if isinstance(m, dict)]
    state = str(p.get('state') or p.get('status') or '').lower()
    return {'id': p.get('id') or (p.get('ref') or {}).get('id'), 'state': 'published' if 'publish' in state else state,
            'at': p.get('scheduled_at') or p.get('published_at') or p.get('at') or p.get('when'), 'text': p.get('text') or p.get('caption') or '',
            'labels': [x.strip() for x in labels if x], 'media': media,
            'network': p.get('network') or p.get('channel') or p.get('provider')}


def matches(story_id, job, game, text, posts):
    """[(kind, post)] for posts that are this story (kind 'story') or the same game and news (kind 'news')."""
    out = []
    lab = f'story:{job}' if job else None
    for p in (norm_post(x) for x in posts or []):
        same = (lab and lab in p['labels']) or (job and any(job_of_media(m) == job for m in p['media']))
        if same:
            out.append(('story', p))
            continue
        if game and game_in(game, p['text']) and similarity(text, p['text']) >= SAME_NEWS:
            out.append(('news', p))
    return out


def verdict(story_id, job, game, text, posts, version=None):
    """(action, line): 'prepare' (nothing in Publer), 'replace' (the same story only scheduled: v2 replaces v1),
    'stop' (published, or the same news under another story)."""
    m = matches(story_id, job, game, text, posts)
    if not m:
        return 'prepare', f'publer check: {story_id}: no scheduled or recent post of this story or news'
    pub = [p for k, p in m if p['state'] == 'published']
    other = [p for k, p in m if k == 'news']
    if pub:
        return 'stop', (f'publer check: {story_id}: already published ({pub[0]["network"]}, {pub[0]["at"]}); skip it, '
                        'a newer version is not posted (rule 3)')
    if other:
        return 'stop', (f'publer check: {story_id}: the same game and news is already scheduled ({other[0]["network"]}, '
                        f'{other[0]["at"]}); skip it')
    return 'replace', (f'publer check: {story_id}: scheduled and not posted yet ({len(m)} post(s), {m[0][1]["at"]}); the newer '
                       'version replaces it at the same time (rule 3)')


# ---------------------------------------------------------------------------------------------- local logs (no Publer)
def from_logs(now=None, hours=WINDOW_H):
    """Posts as the repository knows them (submissions, published, story files), for the slip lane, which has no Publer
    access: [{'state', 'at', 'text', 'labels', 'media', 'story', 'game'}]."""
    now = now or dt.datetime.now(dt.timezone.utc)
    seen, out = set(), []

    def t(s):
        try:
            x = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
            return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            return None
    for path in (os.path.join(REPO, 'newsroom', 'submissions.jsonl'), os.path.join(REPO, 'newsroom', 'published.jsonl')):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding='utf-8'):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            sid = r.get('story')
            if not sid or sid in seen or r.get('state', 'published') not in ('intent', 'scheduled', 'published'):
                continue
            at = t(r.get('slot') or r.get('at'))
            if not at or now - at > dt.timedelta(hours=hours):
                continue
            s = {}
            try:
                s = json.load(open(os.path.join(REPO, 'newsroom', 'stories', sid + '.json'), encoding='utf-8'))
            except (OSError, ValueError):
                pass
            seen.add(sid)
            job = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', sid)
            out.append({'state': 'published' if r.get('state') == 'published' or at <= now else 'scheduled',
                        'at': r.get('slot') or r.get('at'), 'text': ((s.get('texts') or {}).get('instagram') or
                                                                    (s.get('texts') or {}).get('x') or ''),
                        'labels': [f'story:{job}'], 'media': [], 'network': 'logs', 'story': sid, 'game': s.get('game')})
    return out


def main(argv):
    if argv and argv[0] == 'posts' and len(argv) > 1 and '--story' in argv:
        raw = json.load(open(argv[1], encoding='utf-8'))
        posts = raw.get('posts', raw) if isinstance(raw, dict) else raw
        sid = argv[argv.index('--story') + 1]
        s = {}
        try:
            s = json.load(open(os.path.join(REPO, 'newsroom', 'stories', sid + '.json'), encoding='utf-8'))
        except (OSError, ValueError):
            pass
        game = argv[argv.index('--game') + 1] if '--game' in argv else s.get('game')
        text = argv[argv.index('--text') + 1] if '--text' in argv else ((s.get('texts') or {}).get('instagram') or
                                                                       (s.get('texts') or {}).get('x') or '')
        job = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', sid)
        act, line = verdict(sid, job, game, text, posts)
        print(line)
        return 0 if act == 'prepare' else (3 if act == 'replace' else 1)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
