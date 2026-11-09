"""The Newsdesk file: one per Production 2 run (adv-20261109-coordination-in-code, addendum 20:25 Dubai, 9 Nov 2026).

Mohammad's focus is the news and the post timeline: what was approved and what was rejected. Every Production 2 run
writes newsroom/scout/<YYYYMMDD-HHMM>.json (the run's start, Dubai time) and commits it with its board line; the inbox
mirror copies the last 48 hours into the inbox's `leads` collection (one document per run) for the Newsdesk tab.

    {"run_at": ISO, "digest_seq": N, "digest_head": N, "emails_read": ["HH:MM Dubai", ...],
     "leads": [{"rank": 1, "title": "...", "primary_url": "https://...", "first_report": "where and when",
                "arabic_coverage": false, "footage_route": "Steam trailer | press clip | none", "decision":
                "built|carried|rejected|ordered", "reason": "no_source|denied|harmful_or_out_of_scope|duplicate"
                (only and always when rejected), "slot": "HH:MM Dubai" or null, "publer_ids_last6": ["ig:abc123", ...]
                or [], "story_id": "..." or null,
                "handoff": "<board handoff or order id>" (a lead Mohammad ordered or the studio handed over; never rejected),
                "searched": ["search: <query>", "<outlet or site read>", ...] (no_source: 3 or more, one a web search),
                "confirmed_by": "editor" (no_source and denied: the editor's own check, not the scout's),
                "waiting_for": "..." (carried: what the next run decides on)}],
     "post_this_hour": "HH:MM Dubai title" or null, "gap_min": N or null}

    python3 newsroom/scout_file.py check <file>...      refusals, exit 1 when any
    python3 newsroom/scout_file.py new                  a blank file for this run (prints its path)
"""
import datetime as dt, json, os, re, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, 'scout')
DECISIONS = ('built', 'carried', 'rejected', 'ordered')
REASONS = ('no_source', 'denied', 'harmful_or_out_of_scope', 'duplicate')
DUBAI = dt.timezone(dt.timedelta(hours=4))
NAME = re.compile(r'^\d{8}-\d{4}\.json$')
ID6 = re.compile(r'^(?:ig|x|th):[0-9A-Za-z]{6}$')

# Coverage over caution (Mohammad, 9 Nov 2026 evening: "It could've checked Nintendo Everything to verify"; release
# 2026-11-10 r4). Sources that count, by host; newsroom/sources.md is the list in words.
PRIMARY_HOSTS = ('gamespress.com', 'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'cision.com',
                 'store.steampowered.com', 'steamcommunity.com', 'nintendo.com', 'nintendo.co.jp', 'playstation.com',
                 'blog.playstation.com', 'news.xbox.com', 'xbox.com', 'ea.com', 'ubisoft.com', 'capcom.com',
                 'square-enix.com', 'bandainamcoent.com', 'sega.com', 'konami.com', 'koeitecmo.com', 'rockstargames.com',
                 'take2games.com', 'activision.com', 'blizzard.com', 'epicgames.com', 'hoyoverse.com', 'youtube.com',
                 'youtu.be', 'x.com', 'twitter.com')
CREDIBLE_HOSTS = ('nintendoeverything.com', 'nintendolife.com', 'gematsu.com', 'videogameschronicle.com', 'ign.com',
                  'gamespot.com', 'eurogamer.net', 'pcgamer.com', 'polygon.com', 'theverge.com', 'kotaku.com',
                  'insider-gaming.com', 'bloomberg.com', 'reuters.com', 'famitsu.com', '4gamer.net', 'automaton-media.com',
                  'gamekult.com', 'pushsquare.com', 'purexbox.com', 'windowscentral.com', 'gamesindustry.biz',
                  'thegamebusiness.com', 'rockpapershotgun.com', 'digitalfoundry.net', 'siliconera.com', 'vgc.com',
                  'destructoid.com', 'gamesradar.com', 'dualshockers.com', 'axios.com', 'nikkei.com',
                  'gamerant.com', 'pockettactics.com', 'dexerto.com', 'videogamer.com', 'tweaktown.com', 'pcgamesn.com')
# Phrases that are not rejection reasons (desk audit flags them too).
NOT_REASONS = re.compile(r'single[- ]outlet|no primary read|no written primary|only in (?:the |a )?(?:youtube )?video|'
                         r'arabic[- ]only|held for (?:a |the )?(?:statement|trace)|not on (?:the )?newsroom', re.I)


def host_kind(url):
    """'primary', 'credible' or None for a URL's host."""
    try:
        h = (urlparse(str(url)).hostname or '').lower()
    except ValueError:
        return None
    match = lambda hosts: any(h == x or h.endswith('.' + x) for x in hosts)
    return 'primary' if match(PRIMARY_HOSTS) else 'credible' if match(CREDIBLE_HOSTS) else None


def problems(doc, name=None):
    out = []
    if name and not NAME.match(os.path.basename(name)):
        out.append(f'file name: newsroom/scout/<YYYYMMDD-HHMM>.json (Dubai), not {os.path.basename(name)}')
    if not isinstance(doc, dict):
        return out + ['not a JSON object']
    for k in ('run_at', 'digest_seq', 'digest_head', 'emails_read', 'leads'):
        if k not in doc:
            out.append(f'"{k}" missing')
    if isinstance(doc.get('digest_seq'), int) and isinstance(doc.get('digest_head'), int) and doc['digest_seq'] < doc['digest_head']:
        out.append(f'digest_seq {doc["digest_seq"]} is below the branch head {doc["digest_head"]}: read the head')
    leads = doc.get('leads') or []
    if len(leads) > 5:
        out.append(f'{len(leads)} leads: the scout returns at most five')
    for i, l in enumerate(leads, 1):
        w = f'lead {i}'
        if not isinstance(l, dict):
            out.append(f'{w}: not an object'); continue
        for k in ('rank', 'title', 'primary_url', 'first_report', 'arabic_coverage', 'footage_route', 'decision'):
            if k not in l:
                out.append(f'{w}: "{k}" missing')
        if l.get('decision') not in DECISIONS:
            out.append(f'{w}: decision is one of {", ".join(DECISIONS)}')
        if l.get('decision') == 'rejected' and l.get('reason') not in REASONS:
            out.append(f'{w}: rejected needs reason one of {", ".join(REASONS)} (age, relay and no trailer are not reasons)')
        if l.get('decision') != 'rejected' and l.get('reason'):
            out.append(f'{w}: a reason only goes with rejected')
        if l.get('primary_url') and not str(l['primary_url']).startswith('http'):
            out.append(f'{w}: primary_url is a link')
        if l.get('handoff') and l.get('decision') == 'rejected':
            out.append(f'{w}: {l["handoff"]} was ordered or handed over: the scout never rejects it; build it from the '
                       'source the handoff names (only Mohammad drops an order)')
        if l.get('decision') == 'rejected' and l.get('reason') == 'no_source':
            kinds = [host_kind(u) for u in [l.get('primary_url')] + list(l.get('sources') or []) if u]
            if any(kinds):
                out.append(f'{w}: no_source with a {"primary" if "primary" in kinds else "credible outlet"} link in hand: '
                           'a primary is رسمي/جديد, a credible outlet is تقرير; build it')
            searched = [str(x) for x in l.get('searched') or []]
            if len(searched) < 3 or not any(x.lower().startswith('search:') for x in searched):
                out.append(f'{w}: no_source needs "searched" with 3 or more places, one a web search for the story '
                           'itself ("search: <game> <claim>"); a newsroom front page that does not show it proves nothing')
        if l.get('decision') == 'rejected' and l.get('reason') in ('no_source', 'denied') and l.get('confirmed_by') != 'editor':
            out.append(f'{w}: {l.get("reason")} is confirmed by the editor\'s own check ("confirmed_by": "editor"); the '
                       'scout only proposes it')
        if l.get('decision') == 'carried' and not l.get('waiting_for'):
            out.append(f'{w}: carried needs "waiting_for" (what the next run decides on); no silent holds')
        for k in ('reason_note', 'angle', 'note'):
            m = NOT_REASONS.search(str(l.get(k) or '')) if l.get('decision') == 'rejected' else None
            if m:
                out.append(f'{w}: "{m.group(0)}" is not a reason: a credible outlet is a source (تقرير), an official '
                           'video is a primary')
                break
        for x in l.get('publer_ids_last6') or []:
            if not ID6.match(str(x)):
                out.append(f'{w}: publer_ids_last6 entries are ig:/x:/th: plus the last six characters, never a whole id')
    return out


def new(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    path = os.path.join(DIR, now.astimezone(DUBAI).strftime('%Y%m%d-%H%M') + '.json')
    os.makedirs(DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'run_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'digest_seq': None, 'digest_head': None,
                       'emails_read': [], 'leads': [], 'post_this_hour': None, 'gap_min': None}, f, indent=1)
            f.write('\n')
    return path


def docs(folder, now, hours=48, existing=None):
    """Writes for the inbox's `leads` collection: one document per run file of the last `hours`."""
    out, keep = [], set()
    for n in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not NAME.match(n):
            continue
        try:
            t = dt.datetime.strptime(n[:13], '%Y%m%d-%H%M').replace(tzinfo=DUBAI)
        except ValueError:
            continue
        if now - t > dt.timedelta(hours=hours):
            continue
        try:
            d = json.load(open(os.path.join(folder, n), encoding='utf-8'))
        except (OSError, ValueError):
            continue
        d['problems'] = problems(d, n)
        keep.add(n[:-5])
        out.append({'op': 'set', 'doc_id': n[:-5], 'data': d})
    for k in existing or {}:
        if k not in keep:
            out.append({'op': 'delete', 'doc_id': k})
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['new']:
        print(new())
    elif a[:1] == ['check'] and a[1:]:
        bad = 0
        for f in a[1:]:
            ps = problems(json.load(open(f, encoding='utf-8')), f)
            bad += len(ps)
            print(f'{f}: ' + ('ok' if not ps else '\n  - ' + '\n  - '.join(ps)))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['docs'] and len(a) >= 3:
        ex = {}
        if len(a) > 3 and os.path.isdir(a[3]):
            ex = {n[:-5]: 1 for n in os.listdir(a[3]) if n.endswith('.json')}
        w = docs(a[1], dt.datetime.now(dt.timezone.utc), existing=ex)
        json.dump(w, open(a[2], 'w'), ensure_ascii=False, indent=1)
        print(f'leads docs: {len(w)} writes')
    else:
        raise SystemExit(__doc__)
