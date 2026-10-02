#!/usr/bin/env python3
"""The story ledger: one JSON file per story in newsroom/stories/.

It is the newsroom's memory across sessions. It answers "have we done
this already?" before a story is shortlisted, keeps the source chain and
the confirmed and unconfirmed claims, records which version Mohammad
approved and what posted where, and keeps corrections beside the
original. Sweeps read it; nothing here posts anything.

    python3 newsroom/ledger.py sync              # pick up new queue folders and receipts
    python3 newsroom/ledger.py find kena delay   # dedup check before shortlisting
    python3 newsroom/ledger.py card <story_id>   # the approval card
    python3 newsroom/ledger.py lags [days]       # where the time goes

Story fields (all optional except id and title):
  id, title, game, companies[], category, status, related[], notes
  sources[]   {role, name, url, time, via}
              role: primary | original_reporting | technical | outlet_report
                    | radar | rumour.  `via` names who it came through, so
                    ten outlets repeating one report stay one source.
  claims[]    {text, status, source}
              status: verified | reported | rumour | unverified | disputed
                      | contradicted
  why         one line: why it matters
  lanes       {"dxb": {lane, chip, time, text}, "dl": {lane, chip, time,
              headline, x, ig}}  the drafts as shown to him
  versions[]  {v, at, change}    a material change opens a new version
  posts[]     {folder, account, platform, date, postiz_id, approved}
  times       {source, digest, shortlisted, shown, go, posted}  ISO 8601
  media[]     {file, source_url, kind, fetched}
  corrections[] {at, published, now_known, source, accounts, proposed,
                 decision}
  metrics[]   {folder, at, views, likes, reposts, replies, saves, shares}
"""
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
STORIES = HERE / 'stories'
QUEUE = HERE.parent.parent / 'dxb-queue' / 'queue'
ACCOUNTS = {
    'cmtk7cltp0030my0yj6glcyru': ('DXB-KNIGHT', 'x'),
    'cmuifxrd70mbdo80y235utthm': ('Digital Lounge', 'x'),
    'cmujo38ww12j3o80ygi3webqt': ('Digital Lounge', 'instagram'),
    'cmuk0rett044oo80y3ycfes66': ('Digital Lounge', 'tiktok'),
    'cmuk20rj302oqpr0ygqzcdzch': ('Digital Lounge', 'youtube'),
}
SUFFIX = re.compile(r'(-(ar|ig|tt|yt|dxb|thread|retry|short|now|v\d+))+$')
DUBAI = datetime.timezone(datetime.timedelta(hours=4))


def load(sid):
    return json.loads((STORIES / f'{sid}.json').read_text())


def save(story):
    STORIES.mkdir(exist_ok=True)
    (STORIES / f'{story["id"]}.json').write_text(
        json.dumps(story, ensure_ascii=False, indent=1) + '\n')


def stories():
    for f in sorted(STORIES.glob('*.json')):
        yield json.loads(f.read_text())


def plain(content):
    text = re.sub(r'</p>|<br\s*/?>', '\n', content or '')
    return [p.strip() for p in re.sub(r'<[^>]+>', '', text).split('\n') if p.strip()]


def dubai(iso):
    if not iso:
        return '?'
    t = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return t.astimezone(DUBAI).strftime('%d %b %H:%M')


def sync():
    """Attach every queue folder to a story, creating stories for new ones."""
    by_folder = {}
    for s in stories():
        for p in s.get('posts', []):
            by_folder[p['folder']] = s['id']
    added, created = 0, 0
    for d in sorted(QUEUE.iterdir()) if QUEUE.is_dir() else []:
        job_f = d / 'job.json'
        if not job_f.exists():
            continue
        job = json.loads(job_f.read_text())
        receipt = json.loads((d / 'receipt.json').read_text()) if (d / 'receipt.json').exists() else {}
        resp = receipt.get('response') or [{}]
        post = {
            'folder': d.name,
            'account': ACCOUNTS.get(job['integration_id'], ('?', '?'))[0],
            'platform': ACCOUNTS.get(job['integration_id'], ('?', '?'))[1],
            'date': job['date'],
            'postiz_id': (resp[0] if isinstance(resp, list) and resp else {}).get('postId'),
            'sent_at': receipt.get('published_at'),
            'approved': (job.get('approved') or {}).get('note'),
        }
        if d.name in by_folder:
            s = load(by_folder[d.name])
            for i, p in enumerate(s['posts']):
                if p['folder'] == d.name and p != post:
                    s['posts'][i] = post
                    save(s)
            continue
        slug = SUFFIX.sub('', re.sub(r'^\d{4}-\d{2}-\d{2}-', '', d.name))
        day = job['date'][:10]
        sid = next((s['id'] for s in stories()
                    if s['id'].split('-', 3)[-1] == slug
                    and abs((datetime.date.fromisoformat(s['id'][:10])
                             - datetime.date.fromisoformat(day)).days) <= 3), None)
        if sid:
            s = load(sid)
        else:
            sid = f'{day}-{slug}'
            text = plain(job.get('content'))
            s = {'id': sid, 'title': text[0][:120] if text else slug, 'status': 'published',
                 'backfilled': True, 'posts': []}
            created += 1
        s['posts'].append(post)
        s['posts'].sort(key=lambda p: p['date'])
        s.setdefault('times', {})['posted'] = min(p['date'] for p in s['posts'])
        save(s)
        added += 1
    print(f'{created} new stories, {added} posts attached')


def find(words):
    """Stories whose title, game, folders or notes contain every word."""
    words = [w.lower() for w in words]
    hits = []
    for s in stories():
        hay = ' '.join([s['id'], s.get('title', ''), s.get('game', '') or '',
                        s.get('notes', '') or '',
                        ' '.join(p['folder'] for p in s.get('posts', []))]).lower()
        if all(w in hay for w in words):
            hits.append(s)
    for s in hits[-20:]:
        where = sorted({f'{p["account"]} {p["platform"]}' for p in s.get('posts', [])})
        print(f'{s["id"]}  [{s.get("status")}]  {s.get("title", "")[:70]}')
        if where:
            print(f'    posted: {", ".join(where)}, first {dubai(s.get("times", {}).get("posted"))} Dubai')
    if not hits:
        print('no match: new story')


MARK = {'verified': '✓', 'reported': '~', 'rumour': '?', 'unverified': '?',
        'disputed': '!', 'contradicted': '✗'}


def card(sid):
    """The approval card, as shown with the drafts."""
    s = load(sid)
    lanes = s.get('lanes', {})
    out = [f'{s.get("priority", "🟡")} {s.get("title")}']
    prim = [x for x in s.get('sources', []) if x.get('role') == 'primary']
    src = prim[0] if prim else (s.get('sources') or [{}])[0]
    if src:
        out.append(f'Source: {src.get("name", "?")} ({src.get("role", "?")}), {dubai(src.get("time"))} Dubai'
                   + (f', via {src["via"]}' if src.get('via') else ''))
    for c in s.get('claims', []):
        out.append(f'{MARK.get(c.get("status"), "?")} {c["text"]}'
                   + (f'  ({c["status"]}, {c.get("source")})' if c.get('status') != 'verified' else ''))
    if s.get('why'):
        out.append(f'Why it matters: {s["why"]}')
    for key, name in (('dxb', 'DXB-KNIGHT'), ('dl', 'Digital Lounge')):
        lane = lanes.get(key)
        if not lane:
            continue
        out.append(f'{name}: {lane.get("lane", "?")} · {lane.get("chip", "?")} · {lane.get("time", "time to propose")}')
        for field in ('headline', 'text', 'x', 'ig'):
            if lane.get(field):
                out.append(f'  {field}: {lane[field]}')
    if s.get('media'):
        out.append('Media: ' + ', '.join(m.get('kind', m.get('file', '?')) for m in s['media']))
    if len(s.get('versions', [])) > 1:
        out.append(f'Changed since v{s["versions"][-2]["v"]}: {s["versions"][-1]["change"]}')
    print('\n'.join(out))


def lags(days=7):
    """Median minutes between the stages, over recent stories with times."""
    cut = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    steps = [('source', 'digest'), ('digest', 'shortlisted'), ('shortlisted', 'go'), ('go', 'posted')]
    gaps = {s: [] for s in steps}
    for s in stories():
        t = s.get('times', {})
        for a, b in steps:
            if t.get(a) and t.get(b):
                ta = datetime.datetime.fromisoformat(t[a].replace('Z', '+00:00'))
                tb = datetime.datetime.fromisoformat(t[b].replace('Z', '+00:00'))
                if tb >= cut:
                    gaps[(a, b)].append((tb - ta).total_seconds() / 60)
    for (a, b), g in gaps.items():
        g.sort()
        med = f'{g[len(g) // 2]:.0f} min' if g else 'no data yet'
        print(f'{a:>11} → {b:<11} {med}  ({len(g)} stories)')


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:] or ['help']
    if cmd == 'sync':
        sync()
    elif cmd == 'find':
        find(rest)
    elif cmd == 'card':
        card(rest[0])
    elif cmd == 'lags':
        lags(int(rest[0]) if rest else 7)
    else:
        print(__doc__)
