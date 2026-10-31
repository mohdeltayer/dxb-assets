#!/usr/bin/env python3
"""Admission: where a finished story goes in the queue, with breaking news as an explicit branch, and its latency
measured from detection (adv-20261030-promise-keeper, addendum_2251 item F, Mohammad 30 Oct 2026).

Two branches, chosen in one place (`admit`):

  normal    the earliest quarter hour at least LEAD minutes out (or the slot asked for) that keeps the spacing of
            "Constant coverage" against the format ledger's slots and passes formats.check (no third in a row, the
            card-led window, four a day). When no slot in the next day passes the caps, the earliest slot that keeps
            the spacing is given with the cap named: the gap rule over the caps is Mohammad's call, not this code's.
  breaking  verified, official, new or breaking news only (chip رسمي or عاجل, or certainty official): no spacing, no
            caps, no slot allocation. The slot is now; the checks the normal branch would have applied are printed
            as information and bind nothing. Asked for a rumour, a leak or a report, the branch refuses and the story
            is admitted on the normal branch with the reason.

Latency is measured from detection: the first time any of our systems saw the item. For a lead from the server
watch that is the item's `first_seen` in watch/breaking.json on the branch watch-digest (looked up by link); a lead
from elsewhere passes --detected-at. Every stage is stamped in newsroom/latency.jsonl (detected, admitted, rendered,
scheduled, published), and `report` gives minutes from detection per stage, so a breaking story is never timed from
when an editor started on it.

    python3 templates/admission.py admit --id ID --fmt split [--kind release] [--chip رسمي] [--breaking]
                                         [--url URL | --detected-at ISO] [--at SLOT_UTC] [--log]
    python3 templates/admission.py stamp ID EVENT [--at ISO]       events: detected admitted rendered scheduled published
    python3 templates/admission.py report [--days 7]
    python3 templates/admission.py detected URL                    first_seen of a watch item, from watch-digest

Admission never posts, schedules or renders: it answers where the story goes and records the times.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import formats as F  # noqa: E402

LATENCY = os.path.join(ROOT, 'newsroom', 'latency.jsonl')
EVENTS = ('detected', 'admitted', 'rendered', 'scheduled', 'published')
LEAD = 15                      # a normal story is queued at least 15 minutes out, at a quarter hour (rolling queue)
HORIZON_H = 24                 # how far ahead the normal branch looks for a slot that passes the caps
AUTO_GO_MAX = 3                # breaking-lane auto-go posts in any 24 hours (CLAUDE.md, "Breaking lane")
BREAKING_CHIPS = ('عاجل', 'رسمي')
NOT_BREAKING_CHIPS = ('تقرير', 'تسريب', 'شائعة')
OFFICIAL = ('official', 'confirmed')
WATCH_BRANCH = 'watch-digest'
WATCH_FILE = 'watch/breaking.json'


def utc(s):
    """ISO time to an aware UTC datetime; a time without an offset is UTC (the ledger's own times are UTC)."""
    if s is None or isinstance(s, datetime):
        return s
    s = str(s).strip().replace('Z', '+00:00')
    m = re.match(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d)(:\d\d)?(\.\d+)?([+-]\d\d:?\d\d)?$', s)
    if not m:
        raise ValueError('not an ISO time: %r' % s)
    off = m.group(4) or '+00:00'
    if ':' not in off:
        off = off[:3] + ':' + off[3:]
    return datetime.fromisoformat(m.group(1) + (m.group(2) or ':00') + off).astimezone(timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')


def dubai(t):
    return (t + timedelta(hours=4)).strftime('%a %H:%M') + ' Dubai'


# ---------------------------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------------------------
def norm_url(u):
    u = re.sub(r'#.*$', '', str(u or '').strip())
    u = re.sub(r'[?&](utm_[^=&]+|fbclid|gclid|si)=[^&]*', '', u)
    u = u.replace('://www.', '://').rstrip('/').rstrip('?&')
    return u.lower()


def watch_items(path=None):
    """Items of the server watch's breaking file: a local copy, or the branch watch-digest fetched shallow."""
    if path:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    else:
        subprocess.run(['git', '-C', ROOT, 'fetch', '-q', '--depth', '1', 'origin',
                        '+%s:refs/remotes/origin/%s' % (WATCH_BRANCH, WATCH_BRANCH)], capture_output=True, timeout=60)
        p = subprocess.run(['git', '-C', ROOT, 'show', 'origin/%s:%s' % (WATCH_BRANCH, WATCH_FILE)],
                           capture_output=True, text=True, timeout=60)
        if p.returncode:
            return []
        data = json.loads(p.stdout)
    return list(data.get('items') or []) + list(data.get('recent') or [])


def detected_at(url, items):
    """The watch's first sighting of this link (first_seen), or None. The earliest wins when it was seen twice."""
    key = norm_url(url)
    seen = [utc(i['first_seen']) for i in items if i.get('first_seen') and norm_url(i.get('url')) == key]
    return min(seen) if seen else None


# ---------------------------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------------------------
def breaking_branch(story):
    """(True, why) when the story takes the breaking branch, else (False, why). Only verified official news."""
    if not story.get('breaking'):
        return False, 'not asked for the breaking lane'
    chip = (story.get('chip') or '').strip()
    cert = (story.get('certainty') or '').strip().lower()
    if chip in NOT_BREAKING_CHIPS or cert in ('report', 'leak', 'rumour', 'rumor'):
        return False, 'the breaking lane is for verified official news only, not %s' % (chip or cert)
    if chip in BREAKING_CHIPS or cert in OFFICIAL:
        return True, 'verified official news (%s)' % (chip or cert)
    return False, 'breaking needs the chip عاجل or رسمي (or certainty official) after the Verifier'


def _slots():
    return sorted({F._at(e).replace(tzinfo=timezone.utc) for e in F._load() if F._at(e)})


def spacing_ok(t, slots):
    """Spacing of constant coverage against every queued or published slot (the band of the later post)."""
    for s in slots:
        later = max(s, t).replace(tzinfo=None)
        if abs((s - t).total_seconds()) / 60 < F.SPACING[F._band(later)]:
            return False
    return True


def quarter_after(t, minutes):
    t = t + timedelta(minutes=minutes)
    q = (t.minute // 15 + (1 if (t.minute % 15 or t.second or t.microsecond) else 0)) * 15
    return t.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=q)


def auto_go_used(now, log=None):
    rows = read_log(log)
    return sum(1 for r in rows if r.get('event') == 'admitted' and r.get('lane') == 'breaking' and r.get('auto_go')
               and now - utc(r['at']) < timedelta(hours=24))


def admit(story, now=None, slots=None, log=None):
    """The admission decision for one finished story. story: id, fmt, kind, chip, certainty, breaking (bool),
    detected_at (ISO), at (a slot asked for, UTC), auto_go (bool). Returns a dict; nothing is written."""
    now = utc(now) if now else datetime.now(timezone.utc)
    slots = _slots() if slots is None else sorted(utc(s) for s in slots)
    det = utc(story.get('detected_at')) if story.get('detected_at') else None
    out = {'id': story.get('id'), 'fmt': story.get('fmt'), 'decided_at': iso(now),
           'detected_at': iso(det) if det else None,
           'latency_min': round((now - det).total_seconds() / 60, 1) if det else None}
    fmt = story.get('fmt')
    if fmt and fmt not in F.FORMATS:
        raise ValueError('%s: not a format (%s)' % (fmt, ', '.join(F.FORMATS)))
    is_breaking, why = breaking_branch(story)

    # ---- the breaking branch: explicit, and the only place the bypass exists ------------------------------
    if is_breaking:
        info = []
        if not spacing_ok(now, slots):
            info.append('spacing')
        cap = F.check(fmt, iso(now)) if fmt else ''
        if cap:
            info.append('cap: ' + cap)
        used = auto_go_used(now, log)
        out.update(lane='breaking', slot=iso(now), slot_dubai=dubai(now), why=why,
                   bypassed=['spacing', 'format caps', 'slot allocation'],
                   would_have_blocked=info or None,
                   auto_go_left=max(0, AUTO_GO_MAX - used),
                   note=('auto-go allowed (%d of %d used in 24 h)' % (used, AUTO_GO_MAX) if used < AUTO_GO_MAX else
                         'auto-go cap reached (%d in 24 h): post only on Mohammad\'s go' % used))
        return out

    # ---- the normal branch -------------------------------------------------------------------------------
    start = quarter_after(now, LEAD)
    if story.get('at'):
        start = max(start, utc(story['at']))
    first_spaced, t = None, start
    while t < start + timedelta(hours=HORIZON_H):
        if spacing_ok(t, slots):
            first_spaced = first_spaced or t
            cap = F.check(fmt, iso(t)) if fmt else ''
            if not cap:
                out.update(lane='normal', slot=iso(t), slot_dubai=dubai(t), why=why if story.get('breaking') else
                           'rolling queue: earliest quarter hour with the spacing and the caps', caps=None)
                return out
        t += timedelta(minutes=15)
    t = first_spaced or start
    out.update(lane='normal', slot=iso(t), slot_dubai=dubai(t), why=why,
               caps=F.check(fmt, iso(t)) if fmt else None,
               note='no slot in the next %d h passes the caps; the earliest spaced slot is given with the cap named '
                    '(gap rule over caps is Mohammad\'s call)' % HORIZON_H)
    return out


# ---------------------------------------------------------------------------------------------
# Latency log
# ---------------------------------------------------------------------------------------------
def read_log(path=None):
    path = path or LATENCY
    rows = []
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return rows


def stamp(story_id, event, at=None, path=None, **extra):
    if event not in EVENTS:
        raise ValueError('%s: not an event (%s)' % (event, ', '.join(EVENTS)))
    row = {'id': story_id, 'event': event, 'at': iso(utc(at) if at else datetime.now(timezone.utc))}
    row.update({k: v for k, v in extra.items() if v is not None})
    path = path or LATENCY
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
    return row


def report(days=7, now=None, path=None):
    """Per story, minutes from detection to each later stage; and the median per stage for each lane."""
    now = utc(now) if now else datetime.now(timezone.utc)
    by = {}
    for r in read_log(path):
        try:
            t = utc(r['at'])
        except (KeyError, ValueError):
            continue
        s = by.setdefault(r.get('id'), {'lane': None, 'times': {}})
        s['times'].setdefault(r.get('event'), t)          # the first stamp of an event counts
        if r.get('lane'):
            s['lane'] = r['lane']
    stories = []
    for sid, s in by.items():
        det = s['times'].get('detected')
        if not det or now - det > timedelta(days=days):
            continue
        mins = {e: round((s['times'][e] - det).total_seconds() / 60, 1) for e in EVENTS[1:] if e in s['times']}
        stories.append({'id': sid, 'lane': s['lane'] or 'normal', 'detected': iso(det), 'minutes': mins})
    summary = {}
    for lane in sorted({x['lane'] for x in stories}):
        for e in EVENTS[1:]:
            v = sorted(x['minutes'][e] for x in stories if x['lane'] == lane and e in x['minutes'])
            if v:
                summary.setdefault(lane, {})[e] = {'n': len(v), 'median': v[len(v) // 2], 'max': v[-1]}
    return {'days': days, 'stories': sorted(stories, key=lambda x: x['detected']), 'summary': summary}


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description='Admission with an explicit breaking branch, latency from detection')
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('admit')
    a.add_argument('--id', required=True)
    a.add_argument('--fmt')
    a.add_argument('--kind')
    a.add_argument('--chip')
    a.add_argument('--certainty')
    a.add_argument('--breaking', action='store_true')
    a.add_argument('--auto-go', action='store_true', help='the post would go out on the 15-minute silence rule')
    a.add_argument('--url', help='the lead link: detection is its first_seen in the server watch')
    a.add_argument('--watch-file', help='a local breaking.json instead of the watch-digest branch')
    a.add_argument('--detected-at')
    a.add_argument('--at', help='a slot asked for (UTC)')
    a.add_argument('--now')
    a.add_argument('--log', action='store_true', help='stamp detected (when known) and admitted in the latency log')
    s = sub.add_parser('stamp')
    s.add_argument('id')
    s.add_argument('event', choices=EVENTS)
    s.add_argument('--at')
    s.add_argument('--lane')
    r = sub.add_parser('report')
    r.add_argument('--days', type=float, default=7)
    d = sub.add_parser('detected')
    d.add_argument('url')
    d.add_argument('--watch-file')
    x = ap.parse_args(argv)
    if x.cmd == 'admit':
        det = x.detected_at
        if not det and x.url:
            t = detected_at(x.url, watch_items(x.watch_file))
            det = iso(t) if t else None
        story = {'id': x.id, 'fmt': x.fmt, 'kind': x.kind, 'chip': x.chip, 'certainty': x.certainty,
                 'breaking': x.breaking, 'detected_at': det, 'at': x.at}
        dec = admit(story, x.now)
        if x.log:
            if det and not any(r.get('id') == x.id and r.get('event') == 'detected' for r in read_log()):
                stamp(x.id, 'detected', det, source='watch' if x.url and not x.detected_at else 'given')
            stamp(x.id, 'admitted', x.now, lane=dec['lane'], slot=dec['slot'],
                  auto_go=bool(x.auto_go and dec['lane'] == 'breaking') or None)
        print(json.dumps(dec, ensure_ascii=False, indent=1))
        if dec['lane'] == 'breaking' and dec['latency_min'] is None:
            print('admission: no detection time (pass --url of the watch item or --detected-at); latency unknown',
                  file=sys.stderr)
        return 0
    if x.cmd == 'stamp':
        print(json.dumps(stamp(x.id, x.event, x.at, lane=x.lane), ensure_ascii=False))
        return 0
    if x.cmd == 'report':
        rep = report(x.days)
        for lane, ev in rep['summary'].items():
            print('%s: ' % lane + '; '.join('%s median %.0f min (max %.0f, n %d)' % (e, v['median'], v['max'], v['n'])
                                            for e, v in ev.items()))
        for s_ in rep['stories']:
            print('  %-40s %-8s detected %s  %s' % (s_['id'][:40], s_['lane'], s_['detected'],
                                                    ' '.join('%s +%g' % kv for kv in s_['minutes'].items())))
        if not rep['stories']:
            print('no stories with a detection time in the last %g days' % x.days)
        return 0
    if x.cmd == 'detected':
        t = detected_at(x.url, watch_items(x.watch_file))
        print(iso(t) if t else 'not in the server watch (pass --detected-at from the first sighting)')
        return 0 if t else 1


if __name__ == '__main__':
    sys.exit(main())
