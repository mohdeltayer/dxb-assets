"""The Newsdesk file: one per Production 2 run (adv-20261109-coordination-in-code, addendum 20:25 Dubai, 9 Nov 2026).

Mohammad's focus is the news and the post timeline: what was approved and what was rejected. Every Production 2 run
writes newsroom/scout/<YYYYMMDD-HHMM>.json (the run's start, Dubai time) and commits it with its board line; the inbox
mirror copies the last 48 hours into the inbox's `leads` collection (one document per run) for the Newsdesk tab.

    {"run_at": ISO, "digest_seq": N, "digest_head": N, "emails_read": ["HH:MM Dubai", ...],
     "leads": [{"rank": 1, "title": "...", "primary_url": "https://...", "first_report": "where and when",
                "arabic_coverage": false, "footage_route": "Steam trailer | press clip | none", "decision":
                "built|carried|rejected|ordered", "reason": "no_source|denied|harmful_or_out_of_scope|duplicate"
                (only and always when rejected), "slot": "HH:MM Dubai" or null, "publer_ids_last6": ["ig:abc123", ...]
                or [], "story_id": "..." or null}],
     "post_this_hour": "HH:MM Dubai title" or null, "gap_min": N or null}

    python3 newsroom/scout_file.py check <file>...      refusals, exit 1 when any
    python3 newsroom/scout_file.py new                  a blank file for this run (prints its path)
"""
import datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, 'scout')
DECISIONS = ('built', 'carried', 'rejected', 'ordered')
REASONS = ('no_source', 'denied', 'harmful_or_out_of_scope', 'duplicate')
DUBAI = dt.timezone(dt.timedelta(hours=4))
NAME = re.compile(r'^\d{8}-\d{4}\.json$')
ID6 = re.compile(r'^(?:ig|x|th):[0-9A-Za-z]{6}$')


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
