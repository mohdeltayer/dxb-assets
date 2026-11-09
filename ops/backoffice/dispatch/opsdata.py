"""opsdata.py: the operations data the inbox mirror writes into the inbox (card adv-20261108-stories-tab, addendum_0710
and the card body). Called through dispatch.py: feed, published, stale, stories. Python 3 standard library only.

The Claude task reads Publer (its MCP tools) and the inbox (ArtifactData), saves the results as JSON files, and these
functions turn them into documents; the task then writes the documents with ArtifactData. Nothing here reads the
network or writes anywhere but the --out file. The output files hold Publer post ids cut to their last six
characters only, and they go to the private inbox, never into a repository file.

  feed       ops/feed: {last_post, last_post_at, next_slot, next_slot_at, gap_min, gap_rule_min, posts_today,
             bank_ready, alarms[], written_at}
  published  the `published` collection: one document per Reel published in the last 48 hours, its three platform
             posts grouped (id = the Publer post id's last six characters)
  stale      write-backs closing cards with no update for 7 days (status done, outcome 'auto-closed, stale')
  stories    the `stories` collection: one document per open story (board handoffs to Production 2 and commitments
             rows), closed ones kept 3 days, then deleted
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'keeper'))
import keeper as K  # noqa: E402  (parse_time reads every slot form the desks write)

DUBAI = timezone(timedelta(hours=4))
CHANNELS = {'instagram': 'instagram', 'x (twitter)': 'x', 'x': 'x', 'twitter': 'x', 'threads': 'threads'}
PLAT_ORDER = ('instagram', 'x', 'threads')
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
GROUP_MIN = 5            # the three platform posts of one Reel go out within a few minutes
PUBLISHED_H = 48
STALE_DAYS = 7
STORY_KEEP_DAYS = 3
DUE_MIN = 60             # addendum_2106: handoff to scheduled post under 60 minutes
P2 = re.compile(r'production[\s_-]*2', re.I)
CARD_ID = re.compile(r'\b(?:adv|prod)-20\d{6}-[a-z0-9-]+', re.I)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None


def dubai_hm(dt):
    return dt.astimezone(DUBAI).strftime('%H:%M') if dt else None


def cut(s, n):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def load(path, default=None):
    if not path:
        return default
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------------------------------------
# Publer exports (list_publer_posts or get_recent_posts saved as JSON)
# ---------------------------------------------------------------------------------------------
_WHEN = re.compile(r'^(?:[A-Za-z]{3},\s*)?([A-Za-z]{3})[a-z]*\s+(\d\d?)(?:,?\s+(\d{4}))?\s+at\s+(\d\d?):(\d\d)\s*(AM|PM)?\s*'
                   r'(?:UTC|GMT)?\s*([+-]\d\d?(?::?\d\d)?)?$', re.I)


def parse_when(s, now):
    """Publer's 'Sun, Nov 8 at 7:17 AM UTC+4', or any ISO / Dubai form keeper.parse_time reads."""
    if not s:
        return None
    m = _WHEN.match(str(s).strip())
    if m and m.group(1).title() in MONTHS:
        mo, day = MONTHS.index(m.group(1).title()) + 1, int(m.group(2))
        h, mi = int(m.group(4)), int(m.group(5))
        if m.group(6):
            h = h % 12 + (12 if m.group(6).upper() == 'PM' else 0)
        tz = m.group(7) or '+4'
        sign = -1 if tz.startswith('-') else 1
        hh, _, mm = tz.lstrip('+-').partition(':')
        if not mm and len(hh) > 2:
            hh, mm = hh[:2], hh[2:]
        off = timezone(sign * timedelta(hours=int(hh), minutes=int(mm or 0)))
        if m.group(3):
            years = [int(m.group(3))]
        else:
            years = [now.year - 1, now.year, now.year + 1]
        cands = [datetime(y, mo, day, h, mi, tzinfo=off) for y in years]
        return min(cands, key=lambda d: abs((d - now).total_seconds())).astimezone(timezone.utc)
    return K.parse_time(s)


def publer_posts(doc):
    """The post list of a saved Publer result ({posts: [...]}, a list, or nothing), duplicates removed (a paged
    list_publer_posts answer repeats posts: 200 rows held 75 posts on 9 Nov)."""
    if isinstance(doc, dict):
        doc = doc.get('posts') or []
    if not isinstance(doc, list):
        return []
    seen, out = set(), []
    for p in doc:
        if not isinstance(p, dict):
            continue
        ref = p.get('ref') if isinstance(p.get('ref'), dict) else {}
        key = p.get('published_url') or ref.get('id') or (p.get('channel'), p.get('when'), (p.get('caption') or '')[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def group_reels(posts, now):
    """One group per Reel: posts with the same labels whose times lie within GROUP_MIN minutes, one per platform."""
    rows = []
    for p in posts:
        t = parse_when(p.get('when') or p.get('scheduled_at') or p.get('published_at'), now)
        if t is None:
            continue
        ch = CHANNELS.get(str(p.get('channel') or p.get('network') or '').strip().lower(), str(p.get('channel') or '').lower())
        rows.append((t, ch, p))
    rows.sort(key=lambda r: (r[0], PLAT_ORDER.index(r[1]) if r[1] in PLAT_ORDER else 9))
    groups = []
    for t, ch, p in rows:
        labels = sorted(str(x) for x in (p.get('labels') or []))
        g = next((g for g in reversed(groups) if (t - g['start']).total_seconds() <= GROUP_MIN * 60
                  and g['labels'] == labels and ch not in g['posts']), None)
        if g is None:
            g = {'start': t, 'labels': labels, 'posts': {}}
            groups.append(g)
        g['posts'][ch] = (t, p)
    return groups


def _label(labels, prefix):
    for x in labels:
        if x.startswith(prefix + ':'):
            return x.split(':', 1)[1]
    return None


def _slug6(url):
    s = re.sub(r'[^A-Za-z0-9]', '', (url or '').rstrip('/').rsplit('/', 1)[-1])
    return s[-6:] if s else None


def group_id(g):
    """The Publer post id's last six characters (Instagram first); a post the export gave without an id falls back to
    'u' and the last six of its post link, so the document id stays stable across runs."""
    for ch in PLAT_ORDER + tuple(k for k in g['posts'] if k not in PLAT_ORDER):
        if ch in g['posts']:
            ref = g['posts'][ch][1].get('ref')
            pid = ref.get('id') if isinstance(ref, dict) else None
            if pid:
                return str(pid)[-6:]
    for ch in PLAT_ORDER:
        if ch in g['posts']:
            s = _slug6(g['posts'][ch][1].get('published_url'))
            if s:
                return 'u' + s
    return 'u' + g['start'].strftime('%m%d%H%M')


def group_title(g, n=140):
    for ch in PLAT_ORDER:
        if ch in g['posts']:
            cap = (g['posts'][ch][1].get('caption') or '').strip()
            if cap:
                return cut(cap.split('\n', 1)[0], n)
    return '(no caption)'


def group_doc(g):
    labels = g['labels']
    plats = [c for c in PLAT_ORDER if c in g['posts']] + sorted(c for c in g['posts'] if c not in PLAT_ORDER)
    links = {c: g['posts'][c][1].get('published_url') for c in plats if g['posts'][c][1].get('published_url')}
    d = {'title': group_title(g), 'published_at': iso(g['start']), 'platforms': plats,
         'chip': _label(labels, 'chip') or '', 'template': _label(labels, 'tpl') or '',
         'sound': _label(labels, 'sound') or '', 'skin': _label(labels, 'skin') or '',
         'genre': _label(labels, 'genre') or '', 'links': links, 'source': 'publer (inbox mirror)'}
    series = _label(labels, 'series')
    if series:
        d['series'] = series
    return d


# ---------------------------------------------------------------------------------------------
# published
# ---------------------------------------------------------------------------------------------
def published_docs(publer, now, hours=PUBLISHED_H, existing=None):
    """[{doc_id, data, if_version?}]: Reels published in the last `hours`. `existing` ({doc_id: (version, data)}):
    a Reel already recorded under another id (production's own rows, matched by a post link) is skipped; one recorded
    under the same id is rewritten with its version."""
    existing = existing or {}
    links_seen = {}
    for did, (ver, data) in existing.items():
        for u in ((data or {}).get('links') or {}).values():
            links_seen[u] = did
    out = []
    for g in group_reels(publer_posts(publer), now):
        if g['start'] > now or (now - g['start']).total_seconds() > hours * 3600:
            continue
        doc = group_doc(g)
        did = group_id(g)
        other = next((links_seen[u] for u in doc['links'].values() if u in links_seen and links_seen[u] != did), None)
        if other:
            continue
        e = {'doc_id': did, 'data': doc}
        if did in existing:
            if existing[did][1] == doc:
                continue
            e['if_version'] = existing[did][0]
        out.append(e)
    out.sort(key=lambda e: e['data']['published_at'])
    return out


# ---------------------------------------------------------------------------------------------
# feed
# ---------------------------------------------------------------------------------------------
def gap_rule(now):
    return 120 if now.astimezone(DUBAI).hour < 8 else 60


def feed_doc(keeper_status, commitments, scheduled, published, now):
    """The ops/feed document. Last post from Publer's published list (else the keeper's published rows); next slot from
    Publer's scheduled list (else the commitments rows scheduled ahead); bank and alarms from the keeper's status."""
    ks = keeper_status if isinstance(keeper_status, dict) else {}
    pub = [g for g in group_reels(publer_posts(published), now) if g['start'] <= now]
    last_at, last_t = None, None
    if pub:
        g = max(pub, key=lambda g: g['start'])
        last_at, last_t = g['start'], group_title(g, 90)
    for r in ks.get('rows') or []:
        if isinstance(r, dict) and r.get('stage') == 'published':
            t = K.parse_time(r.get('slot'))
            if t and t <= now and (last_at is None or t > last_at):
                last_at, last_t = t, cut(r.get('title'), 90)
    nxt = None
    for g in group_reels(publer_posts(scheduled), now):
        if g['start'] > now and (nxt is None or g['start'] < nxt[0]):
            nxt = (g['start'], group_title(g, 60))
    if nxt is None:
        for r in K.rows_of(commitments or {}):
            t = K.parse_time(r.get('slot'))
            st = ' '.join(str(r.get(k) or '') for k in ('status', 'note')).lower()
            if t and t > now and not r.get('held_by_mohammad') and 'scheduled' in st and 'dropped' not in st:
                if nxt is None or t < nxt[0]:
                    nxt = (t, cut(r.get('title'), 60))
    day0 = now.astimezone(DUBAI).replace(hour=0, minute=0, second=0, microsecond=0)
    alarms = []
    for a in ks.get('alarms_now') or []:
        t = a.get('title') if isinstance(a, dict) else a
        if t and t not in alarms:
            alarms.append(cut(t, 160))
    return {
        'last_post': last_t, 'last_post_at': iso(last_at),
        'next_slot': ('%s Dubai · %s' % (dubai_hm(nxt[0]), nxt[1])) if nxt else None,
        'next_slot_at': iso(nxt[0]) if nxt else None,
        'gap_min': int((now - last_at).total_seconds() // 60) if last_at else None,
        'gap_rule_min': gap_rule(now),
        'posts_today': sum(1 for g in pub if g['start'] >= day0),
        'bank_ready': ks.get('bank_ready'),
        'alarms': alarms,
        'keeper_at': ks.get('generated_at'),
        'written_at': iso(now),
    }


# ---------------------------------------------------------------------------------------------
# stale cards
# ---------------------------------------------------------------------------------------------
def last_touch(d):
    ans = d.get('answer') if isinstance(d.get('answer'), dict) else {}
    ts = [K.parse_time(x) for x in (d.get('updated_at'), ans.get('at'), d.get('picked_up_at'), d.get('created_at'))]
    ts = [t for t in ts if t]
    return max(ts) if ts else None


def stale_writebacks(items_dir, now, days=STALE_DAYS):
    """[{id, fields}] for every card not done whose last update is older than `days` (addendum_0710 step 8)."""
    out = []
    for name in sorted(os.listdir(items_dir)):
        if not name.endswith('.json') or name == 'index.json':
            continue
        d = load(os.path.join(items_dir, name))
        if not isinstance(d, dict):
            continue
        if str(d.get('status') or 'open').lower() == 'done':
            continue
        t = last_touch(d)
        if t is None or (now - t).total_seconds() <= days * 86400:
            continue
        out.append({'id': str(d.get('id') or name[:-5]),
                    'fields': {'status': 'done', 'outcome': 'auto-closed, stale', 'updated_at': iso(now)}})
    return out


# ---------------------------------------------------------------------------------------------
# stories
# ---------------------------------------------------------------------------------------------
_SCHED = re.compile(r'scheduled\s+(?:for\s+|at\s+)?((?:[A-Za-z]{3},?\s+)?(?:\d\d?\s+[A-Za-z]{3}\s+)?\d\d?:\d\d\s*Dubai)', re.I)


def _text(h):
    return ' '.join(str(h.get(k) or '') for k in ('done', 'next', 'evidence', 'outcome'))


def _card_of(*texts):
    for t in texts:
        m = CARD_ID.search(str(t or ''))
        if m:
            return m.group(0)
    return None


def handoff_story(h, hs, now):
    hid, at = h['id'], K.parse_time(h.get('at'))
    later = [x for x in hs if isinstance(x, dict) and P2.search(str(x.get('from', ''))) and x is not h
             and hid in ' '.join(str(x.get(k, '')) for k in ('id', 'done', 'next', 'evidence', 'ack'))
             and (K.parse_time(x.get('at')) or at) >= at]
    later.sort(key=lambda x: K.parse_time(x.get('at')) or at)
    state, since, slot, closed = 'waiting_pickup', at, None, None
    if h.get('acknowledged_at') or h.get('acknowledged_by'):
        state, since = 'building', K.parse_time(h.get('acknowledged_at')) or at
    for x in later:
        tx, t = _text(x), K.parse_time(x.get('at')) or at
        seg = tx[max(0, tx.find(hid) - 40):] if hid in tx else tx
        low = seg.lower()
        if re.search(r'\b(declined|dropped)\b', low):
            state, since, closed = 'dropped', t, t
        elif re.search(r'\bpublished\b', low):
            state, since, closed = 'published', t, t
        elif 'scheduled' in low:
            state, since = 'scheduled', t
            m = _SCHED.search(seg)
            slot = m.group(1) if m else slot
        elif state == 'waiting_pickup':
            state, since = 'building', t
    oc = str(h.get('outcome') or '').lower()
    if oc and state not in ('dropped', 'published'):
        if re.search(r'\b(declined|dropped)\b', oc):
            state, closed = 'dropped', K.parse_time(h.get('acknowledged_at')) or since
        elif 'published' in oc:
            state, closed = 'published', K.parse_time(h.get('acknowledged_at')) or since
    due = K.parse_time(h.get('due')) or (at + timedelta(minutes=DUE_MIN))
    held = h.get('held_by_mohammad')
    if held is None:
        held = bool(re.search(r'studio', str(h.get('from', '')), re.I))
    return {
        'title': cut(h.get('title') or h.get('done'), 140), 'kind': 'handoff',
        'from': h.get('from'), 'to': h.get('to'), 'state': state, 'since': iso(since),
        'slot': slot, 'due': iso(due), 'due_dubai': dubai_hm(due), 'held': bool(held),
        'publer_ids_last6': [], 'evidence': cut(h.get('evidence'), 200),
        'card': _card_of(hid, h.get('evidence'), h.get('done')), 'closed_at': iso(closed),
    }


def row_story(r, ks_rows, pub_groups, now):
    slot = K.parse_time(r.get('slot'))
    k = ks_rows.get(r.get('id')) or {}
    stage = str(k.get('stage') or '').lower()
    dl = K.delivery_of(r)
    states = {d.get('state') for d in dl.values()}
    st = ' '.join(str(r.get(x) or '') for x in ('status', 'note')).lower()
    match = [g for g in pub_groups if slot and abs((g['start'] - slot).total_seconds()) <= 10 * 60]
    ids = [group_id(g) for g in match]
    closed = None
    if re.search(r'\b(dropped|cancelled|canceled|pulled|deleted)\b', st) or stage in ('dropped', 'cancelled'):
        state, closed = 'dropped', slot
    elif stage == 'published' or (states and states <= {'published'}) or match:
        state = 'published'
        closed = (match[0]['start'] if match else slot)
    elif stage in ('scheduled', 'publication unconfirmed') or 'scheduled' in states or 'scheduled' in st:
        state = 'scheduled'
    elif stage in ('queued', 'claimed', 'ready', 'rendered', 'qc_passed', 'building') or r.get('job'):
        state = 'building'
    else:
        state = 'waiting_pickup'
    return {
        'title': cut(r.get('title'), 140), 'kind': r.get('kind') or 'post', 'from': 'commitments',
        'to': None, 'platforms': K.platforms_of(r), 'state': state,
        'since': iso(K.parse_time(r.get('logged')) or slot), 'slot': (K.dubai(slot) if slot else r.get('slot')),
        'due': iso(slot), 'due_dubai': dubai_hm(slot), 'held': bool(r.get('held_by_mohammad')),
        'publer_ids_last6': ids, 'evidence': cut(r.get('evidence') or r.get('status'), 200),
        'card': _card_of(r.get('card'), r.get('note'), r.get('evidence')), 'closed_at': iso(closed),
    }


def stories_docs(board, commitments, now, keeper_status=None, published=None, existing=None, keep_days=STORY_KEEP_DAYS):
    """[{op, doc_id, data?, if_version?}]: one set per story (open, or closed within keep_days), one delete per
    existing document closed for longer, or no longer listed and older than keep_days. Stories: handoffs addressed to
    Production 2 from anyone else (with a time) written within keep_days, and commitments rows whose slot is within
    the last 48 hours (the Publer read) or ahead."""
    existing = existing or {}
    hs = [h for h in (board or {}).get('handoffs', []) if isinstance(h, dict)]
    horizon = now - timedelta(days=keep_days)
    docs = {}
    for h in hs:
        at = K.parse_time(h.get('at'))
        if not h.get('id') or not at or not P2.search(str(h.get('to', ''))) or P2.search(str(h.get('from', ''))):
            continue
        if at < horizon:
            continue
        docs[h['id']] = handoff_story(h, hs, now)
    ks_rows = {r.get('id'): r for r in ((keeper_status or {}).get('rows') or []) if isinstance(r, dict)}
    pub_groups = group_reels(publer_posts(published), now) if published else []
    row_from = now - timedelta(hours=PUBLISHED_H)     # rows inside the window the Publer read can confirm
    for r in K.rows_of(commitments or {}):
        slot = K.parse_time(r.get('slot'))
        if not r.get('id') or not slot or slot < row_from or r['id'] in docs:
            continue
        docs[r['id']] = row_story(r, ks_rows, pub_groups, now)
    out = []
    for did, d in sorted(docs.items(), key=lambda kv: kv[1].get('since') or ''):
        closed = K.parse_time(d.get('closed_at'))
        if closed and closed < horizon:
            if did in existing:
                out.append({'op': 'delete', 'doc_id': did, 'if_version': existing[did][0]})
            continue
        old = existing.get(did)
        if old and old[1] == d:
            continue
        e = {'op': 'set', 'doc_id': did, 'data': d}
        if old:
            e['if_version'] = old[0]
        out.append(e)
    for did, (ver, data) in existing.items():
        if did in docs:
            continue
        t = K.parse_time((data or {}).get('closed_at')) or K.parse_time((data or {}).get('since'))
        if t is None or t < horizon:
            out.append({'op': 'delete', 'doc_id': did, 'if_version': ver})
    return out


def load_existing(path):
    """{doc_id: (version, data)} from a JSON file {doc_id: {"version": n, "data": {...}}} or a folder of
    ArtifactData out_dir files (<doc_id>.json, the document itself) with an optional versions.json {doc_id: n}."""
    if not path:
        return {}
    if os.path.isdir(path):
        vers = load(os.path.join(path, 'versions.json'), {}) or {}
        out = {}
        for name in os.listdir(path):
            if name.endswith('.json') and name != 'versions.json':
                did = name[:-5]
                out[did] = (vers.get(did), load(os.path.join(path, name)))
        return out
    d = load(path, {}) or {}
    return {k: (v.get('version'), v.get('data')) for k, v in d.items() if isinstance(v, dict)}
