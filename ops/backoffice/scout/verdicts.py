"""Scout verdict lines onto the work order (adv-20261111-scout-verdicts-on-work-order, Mohammad 11 Nov 2026).

Since the 23:48 Dubai digest of 10 Nov the Grok scout (Gaming Watch, dxbknight-digest@agentmail.to) adds, after Status,
to every NEW item that is not minor: VERDICT (CONFIRMED, PARTLY, NOT CONFIRMED, DENIED), LABEL (رسمي, تقرير, شائعة),
FACTS (fact | supporting sentence | OK or WRONG, separated by semicolons on one line), FOOTAGE, NOT CONFIRMED.

The scout is a lead, not proof. On dxb-render-1 this reads the digest inbox (read only: it never marks, moves or sends),
parses each item, opens its Primary link and checks that the names, dates and numbers of each FACT are on the page:

  source_confirmed   the page opened and every fact's numbers and most of its names were found
  source_unreadable  paywall, X, 403, a page with no text
  mismatch           the page opened and these facts were not found (listed)

Label rule: never stronger than the scout's LABEL; رسمي stays only when source_confirmed on a company page (the item's
Primary, not an outlet), else it becomes تقرير. A scout CONFIRMED on a page the server could not open counts as تقرير.
DENIED leads are listed as denied, never built. Items with no verdict lines pass through as today (not listed here).

    python3 ops/backoffice/scout/verdicts.py parse <digest.txt>
    python3 ops/backoffice/scout/verdicts.py run --key-file /etc/dxb-scout/agentmail.key --out <leads.json> [--hours 3]

The key file is root-owned and readable by the runner user (install lines in the release note); it is read, never
printed. No key file: the run says so and writes nothing.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

INBOX = 'dxbknight-digest@agentmail.to'
API = 'https://api.agentmail.to/v0'
UA = 'Mozilla/5.0 (X11; Linux x86_64) dxb-render scout-check'
LADDER = {'شائعة': 0, 'تسريب': 0, 'تقرير': 1, 'رسمي': 2}
UNREADABLE_HOSTS = ('x.com', 'twitter.com', 'youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com', 'facebook.com')
OUTLETS = ('ign.com', 'gamespot.com', 'pcgamer.com', 'eurogamer.net', 'vgc.', 'videogameschronicle.com', 'kotaku.com',
           'polygon.com', 'theverge.com', 'gamesindustry.biz', 'nintendolife.com', 'pushsquare.com', 'purexbox.com',
           'nintendoeverything.com', 'gematsu.com', 'dualshockers.com', 'thegamer.com', 'gamerant.com', 'dexerto.com',
           'insider-gaming.com', 'bloomberg.com', 'reuters.com', 'cnbc.com', 'vooks.net', 'automaton-media.com',
           '4gamer.net', 'famitsu.com', 'gamespark.jp', 'denfaminicogamer.jp', 'arabgamenews.com', 'truegaming.net',
           'saudigamer.com', 'vga4a.com', 'tbreak.com', 'rockpapershotgun.com', 'windowscentral.com', 'theguardian.com')
FIELDS = ('Claim', 'Primary', 'Outlet report', 'Who else', 'Status', 'VERDICT', 'LABEL', 'FACTS', 'FOOTAGE',
          'NOT CONFIRMED', 'Why it might matter', 'Age')
HEAD = re.compile(r'^(SAME_DAY|NEW|AGE|BREAKING|UPDATE)\s+-\s+(.+?)\s*$')


def parse(text):
    """Every item of one digest: {'tag', 'headline', 'minor', <field>: value}. Lines that are not "Field: value" join the
    previous field."""
    items, cur, last = [], None, None
    for raw in (text or '').splitlines():
        ln = raw.strip()
        m = HEAD.match(ln)
        if m:
            cur = {'tag': m.group(1), 'headline': m.group(2), 'minor': '(minor' in m.group(2)}
            items.append(cur)
            last = None
            continue
        if cur is None or not ln:
            if not ln:
                last = None
            continue
        f = next((k for k in FIELDS if re.match(r'%s\s*:' % re.escape(k), ln, re.I)), None)
        if f:
            cur[f] = ln.split(':', 1)[1].strip()
            last = f
        elif last:
            cur[last] += ' ' + ln
    return items


def facts_of(item):
    """FACTS as [{'fact', 'sentence', 'ok'}]: "fact | sentence | OK" separated by semicolons."""
    out = []
    for part in re.split(r';\s*(?=[^|;]+\|)', item.get('FACTS') or ''):
        bits = [b.strip() for b in part.split('|')]
        if bits and bits[0]:
            out.append({'fact': bits[0], 'sentence': bits[1] if len(bits) > 1 else '',
                        'ok': (bits[2].upper().startswith('OK') if len(bits) > 2 else None)})
    return out


def has_verdict(item):
    return bool(item.get('VERDICT') or item.get('LABEL') or item.get('FACTS'))


def first_url(s):
    m = re.search(r'https?://\S+', s or '')
    return m.group(0).rstrip('.,;)') if m else None


def host(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix('www.')
    except (ValueError, AttributeError):
        return ''


def is_company(url):
    """A company page: not an outlet, not a social post."""
    h = host(url)
    return bool(h) and not any(o in h for o in OUTLETS) and not any(h.endswith(s) for s in UNREADABLE_HOSTS)


def fetch_text(url, timeout=20):
    """The page as plain text, or None when it cannot be read (an error, a social post, under 400 characters)."""
    if not url or any(host(url).endswith(s) for s in UNREADABLE_HOSTS):
        return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en,ar;q=0.8,ja;q=0.6'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(3_000_000).decode(r.headers.get_content_charset() or 'utf-8', errors='replace')
    except (urllib.error.URLError, OSError, ValueError):
        return None
    raw = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', ' ', raw)
    txt = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', raw))
    txt = re.sub(r'\s+', ' ', txt)
    return txt if len(txt) >= 400 else None


MONTHS = ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
          'november', 'december')
STOP = {'The', 'This', 'That', 'And', 'For', 'With', 'From', 'Its', 'Their', 'They', 'Says', 'Said', 'New'}


def _norm(s):
    return re.sub(r'\s+', ' ', s.lower().replace(',', ''))


def fact_found(fact, page):
    """Every number of the fact on the page (thousands commas ignored), and at least half its names (capitalised words
    of 3 letters or more, months included)."""
    p = _norm(page)
    nums = [n.replace(',', '') for n in re.findall(r'\d[\d,]*(?:\.\d+)?', fact)]
    names = [w for w in re.findall(r"\b[A-Z][\w'&-]{2,}", fact) if w not in STOP]
    if any(n not in p for n in nums):
        return False
    if names:
        hit = sum(1 for w in names if w.lower() in p)
        return hit * 2 >= len(names)
    return bool(nums)


def check(item, fetch=fetch_text):
    """{'result', 'missing', 'url'} for one item: its Primary link first, else the outlet report."""
    url = first_url(item.get('Primary')) or first_url(item.get('Outlet report'))
    page = fetch(url) if url else None
    if not page:
        return {'result': 'source_unreadable', 'missing': [], 'url': url}
    facts = facts_of(item)
    missing = [f['fact'] for f in facts if not fact_found(f['fact'], page)]
    return {'result': 'mismatch' if missing else 'source_confirmed', 'missing': missing, 'url': url}


def label_for(item, chk):
    """The label to build with: never stronger than the scout's; رسمي only when confirmed on a company page."""
    scout = (item.get('LABEL') or '').strip()
    scout = next((k for k in LADDER if k in scout), 'تقرير')
    if 'DENIED' in (item.get('VERDICT') or '').upper():
        return None
    company = bool(first_url(item.get('Primary'))) and is_company(chk.get('url') or '')
    if scout == 'رسمي' and not (chk['result'] == 'source_confirmed' and company):
        return 'تقرير'
    return scout


def lead(item, chk, digest_at=None):
    lab = label_for(item, chk)
    return {'headline': item.get('headline', '')[:160], 'tag': item.get('tag'), 'digest_at': digest_at,
            'link': chk.get('url'), 'verdict': (item.get('VERDICT') or '').strip()[:40],
            'scout_label': (item.get('LABEL') or '').strip()[:20], 'label': lab, 'denied': lab is None,
            'result': chk['result'], 'missing': [m[:120] for m in chk['missing']][:5],
            'facts': [f['fact'][:160] for f in facts_of(item)][:6],
            'footage': first_url(item.get('FOOTAGE')) or (item.get('FOOTAGE') or '')[:160],
            'not_confirmed': (item.get('NOT CONFIRMED') or '')[:200]}


# ---------- the digest inbox (read only) ----------
def _get(path, key, params=None):
    url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + key, 'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def digests(key, hours=3, now=None):
    """[(timestamp, text)] of the digests received in the last `hours` (read only; nothing is marked)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    after = (now - dt.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    box = urllib.parse.quote(INBOX)
    lst = _get(f'/inboxes/{box}/messages', key, {'limit': 10, 'after': after})
    out = []
    for m in lst.get('messages') or []:
        if not str(m.get('subject') or '').startswith('DXB digest'):
            continue
        full = _get(f"/inboxes/{box}/messages/{urllib.parse.quote(m['message_id'] if 'message_id' in m else m['messageId'])}", key)
        out.append((m.get('timestamp'), full.get('extracted_text') or full.get('text') or ''))
    return out


def run(key_file, out, hours=3, fetch=fetch_text, source=None):
    """Read, parse, check and write the leads (newest digest first). `source` replaces the inbox for tests."""
    if source is None:
        if not os.access(key_file, os.R_OK):
            print(f'scout verdicts: key file {key_file} not readable; nothing read (install lines in the release note)')
            return None
        key = open(key_file).read().strip()
        try:
            source = digests(key, hours)
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f'scout verdicts: inbox read failed ({type(e).__name__}); nothing written')
            return None
    leads, seen = [], set()
    for at, text in sorted(source, key=lambda x: str(x[0]), reverse=True):
        for it in parse(text):
            if not has_verdict(it) or it['headline'] in seen:
                continue
            seen.add(it['headline'])
            leads.append(lead(it, check(it, fetch), at))
    day = dt.datetime.now(dt.timezone(dt.timedelta(hours=4))).strftime('%Y-%m-%d')
    doc = {'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'leads': leads,
           'measure': {'day_dubai': day, 'source_confirmed': sum(1 for x in leads if x['result'] == 'source_confirmed'),
                       'leads': len(leads)}}
    json.dump(doc, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"scout verdicts: {len(leads)} leads, {doc['measure']['source_confirmed']} source_confirmed")
    return doc


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[:1] == ['parse'] and len(a) > 1:
        for it in parse(open(a[1], encoding='utf-8').read()):
            print(json.dumps({k: v for k, v in it.items()}, ensure_ascii=False))
    elif a[:1] == ['run']:
        run(opt('--key-file', '/etc/dxb-scout/agentmail.key'), opt('--out', 'scout-leads.json'), float(opt('--hours', 3)))
    else:
        raise SystemExit(__doc__)
