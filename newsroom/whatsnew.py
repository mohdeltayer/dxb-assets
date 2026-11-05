"""What is new: the story packet (adv-20261102-story-brief, part 1; sources addendum B of 2 Nov).

For a story file with a primary url: read the primary page's clean text (trafilatura), find the dates in it
(dateparser: English, Japanese, Arabic), split it into sentences and mark each one against what we already hold on
the same subjects (the ledger's titles, claims and why lines of the stories that touch the same backstory pages):

  posted    close to a story we already published (a repeat needs something new, or it is dropped)
  known     close to a ledger claim of a story we did not post
  new       nothing close: the facts the angle should come from

Matching is by meaning when sentence-transformers and the model in WHATSNEW_MODEL are installed on the machine
(opt-in: the model's licence is recorded on the card before it is installed), else by word overlap (the default
tonight; numbers and names weigh most). The primary's full text is a publisher's text: it stays in the local packet
folder (WHATSNEW_DIR, default ~/.cache/dxb-packets), never in this public repository. The story file gets only the
summary: counts, the dates found, the closest stories, the packet path on that machine, and the time read.

    python3 newsroom/whatsnew.py packet <story id> [--url <primary url>] [--top 8]

Licences (read from each package's metadata, 5 Nov 2026): trafilatura 2.3.1 Apache-2.0; dateparser 1.5.0
BSD-3-Clause; sentence-transformers 6.2.0 Apache-2.0 (code only; a model's weights carry their own licence).
"""
import datetime
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
STORIES = ROOT / 'stories'
PACKETS = pathlib.Path(os.environ.get('WHATSNEW_DIR', pathlib.Path.home() / '.cache' / 'dxb-packets'))
MODEL = os.environ.get('WHATSNEW_MODEL')          # e.g. a multilingual MiniLM, once its licence is recorded
CLOSE = 0.55                                      # word-overlap score at which a sentence counts as already held
CLOSE_SEM = 0.78                                  # cosine for the meaning matcher
STOP = set('a an the of to in on for and or but is are was were be been by with as at from that this it its into '
           'will would can could has have had not no new also than then their there they he she we you our your '
           'about after before more most over up out which who what when where how all any some'.split())

sys.path.insert(0, str(ROOT))
import context  # noqa: E402


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load(sid):
    f = STORIES / f'{sid}.json'
    s = json.loads(f.read_text())
    s.setdefault('id', sid)
    return f, s


def primary_url(s):
    srcs = [x for x in s.get('sources') or [] if isinstance(x, dict) and x.get('url')]
    prim = [x for x in srcs if str(x.get('role', '')).lower().startswith('primary')]
    return (prim or srcs or [{}])[0].get('url')


def fetch_text(url):
    import trafilatura
    raw = trafilatura.fetch_url(url)
    if not raw:
        raise SystemExit(f'whatsnew: the primary did not load: {url}')
    text = trafilatura.extract(raw, include_comments=False, include_tables=True, favor_precision=True)
    if not text:
        raise SystemExit(f'whatsnew: no article text found at {url}')
    return text


def sentences(text):
    parts = re.split(r'(?<=[.!?。！？؟])\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def dates_in(text):
    try:
        from dateparser.search import search_dates
    except ImportError:
        return []
    found = search_dates(text, languages=['en', 'ja', 'ar'],
                         settings={'PREFER_DATES_FROM': 'past', 'RETURN_AS_TIMEZONE_AWARE': False,
                                   'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'DMY'}) or []
    out = []
    for phrase, dt in found:
        if not re.search(r'(19|20)\d\d|\d{4}年|\d+月\d+日', phrase):   # a year or a Japanese date in the phrase itself
            continue                                     # ("May 3", "today" and the like are too loose to keep)
        d = dt.strftime('%Y-%m-%d')
        if (phrase, d) not in out:
            out.append((phrase, d))
    return out[:20]


def words(t):
    toks = re.findall(r'[\w$€£¥%.,]+', t.lower())
    out = set()
    for w in toks:
        w = w.strip('.,')
        if w and w not in STOP and len(w) > 1:
            out.add(w)
    return out


def overlap(a, b):
    """Containment of a's main words in b, with numbers counted twice (a figure is the news)."""
    wa, wb = words(a), words(b)
    if not wa:
        return 0.0
    num = lambda w: any(c.isdigit() for c in w)
    weight = lambda ws: sum(2 if num(w) else 1 for w in ws)
    return weight(wa & wb) / weight(wa)


def corpus(s):
    """[(text, story id, posted)] from every ledger story touching the same backstory pages (or the same game)."""
    pages = set(context.matches(s))
    game = str(s.get('game') or '').lower()
    out = []
    for o in context.stories():
        if o['id'] == s['id']:
            continue
        if not (pages & set(context.matches(o)) or (game and str(o.get('game') or '').lower() == game)):
            continue
        posted = context.posted(o)
        texts = [o.get('title') or '', o.get('why') or '']
        texts += [c.get('text', '') for c in o.get('claims') or [] if isinstance(c, dict)]
        out += [(t, o['id'], posted) for t in texts if len(str(t)) > 15]
    return out


def mark(sents, known):
    """[(sentence, verdict, score, story id)] by meaning when the model is installed, else by word overlap."""
    if MODEL and known:
        try:
            from sentence_transformers import SentenceTransformer, util
            m = SentenceTransformer(MODEL, device='cpu')
            a = m.encode(sents, convert_to_tensor=True, normalize_embeddings=True)
            b = m.encode([k[0] for k in known], convert_to_tensor=True, normalize_embeddings=True)
            sim = util.cos_sim(a, b)
            out = []
            for i, snt in enumerate(sents):
                j = int(sim[i].argmax())
                sc = float(sim[i][j])
                v = ('posted' if known[j][2] else 'known') if sc >= CLOSE_SEM else 'new'
                out.append((snt, v, round(sc, 2), known[j][1] if v != 'new' else None))
            return out, 'meaning (' + MODEL + ')'
        except Exception as e:                                   # fall back, say so
            print(f'whatsnew: meaning matcher unavailable ({type(e).__name__}); word overlap used', file=sys.stderr)
    out = []
    for snt in sents:
        best = max(((overlap(snt, k[0]), k) for k in known), default=(0.0, None), key=lambda x: x[0])
        sc, k = best
        v = ('posted' if k[2] else 'known') if k and sc >= CLOSE else 'new'
        out.append((snt, v, round(sc, 2), k[1] if v != 'new' else None))
    return out, 'word overlap'


def packet(sid, url=None, top=8):
    f, s = load(sid)
    url = url or primary_url(s)
    if not url:
        raise SystemExit(f'whatsnew: {sid} has no source url; pass --url')
    text = fetch_text(url)
    sents = sentences(text)
    marked, how = mark(sents, corpus(s))
    PACKETS.mkdir(parents=True, exist_ok=True)
    pk = PACKETS / f'{sid}.md'
    lines = [f'# Packet: {sid}', f'primary: {url}', f'read: {now()}', f'matcher: {how}', '', '## Sentences']
    lines += [f'- [{v}{" " + str(sc) if v != "new" else ""}{" " + k if k else ""}] {snt}' for snt, v, sc, k in marked]
    lines += ['', '## Full text (publisher\'s; local only, never committed)', text]
    pk.write_text('\n'.join(lines) + '\n')
    counts = {v: sum(1 for m in marked if m[1] == v) for v in ('new', 'known', 'posted')}
    closest = sorted({k for _, v, _, k in marked if k}, key=lambda k: -sum(1 for m in marked if m[3] == k))[:5]
    s['whats_new'] = {'read_at': now(), 'url': url, 'matcher': how, 'sentences': len(marked), 'counts': counts,
                      'dates_found': [f'{ph.strip()} -> {d}' for ph, d in dates_in(text)][:10], 'closest_stories': closest,
                      'packet': str(pk), 'context_pages': [f'newsroom/context/{p}.md' for p in context.matches(s)]}
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n')
    print(f'{sid}: {len(marked)} sentences: {counts["new"]} new, {counts["known"]} known, {counts["posted"]} posted '
          f'({how}); packet {pk}')
    for snt, v, sc, k in [m for m in marked if m[1] == 'new'][:top]:
        print('  new:', snt[:160])
    if counts['posted'] and not counts['new']:
        print('  nothing new against our posts: an update needs a new fact, or the story is dropped')
    return s['whats_new']


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'packet':
        u = a[a.index('--url') + 1] if '--url' in a else None
        t = int(a[a.index('--top') + 1]) if '--top' in a else 8
        packet(a[1], u, t)
    else:
        raise SystemExit(__doc__)
