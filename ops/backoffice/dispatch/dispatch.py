#!/usr/bin/env python3
"""dispatch.py: the desk dispatcher for the newsroom inbox (back office, no AI).

The inbox holds cards. Some cards are never picked up. This script routes every card to a desk,
looks for evidence that someone started work, and alerts Mohammad through ntfy when a card is late.
It cannot read the inbox database, so a scheduled Claude task exports the cards (hourly) to a
private repo file and applies the write-backs this script computes. Python 3 standard library only.

Subcommands
  mirror <items_dir> <out.json>        sanitized mirror of the cards (no bodies, memos, links, media)
  evidence --git DIR [--git DIR ...]   commits of local clones, last N days, as JSON
  plan --mirror M --evidence E --out D ops-queue.md, build-queue.md and writeback.json
  tick                                 the server pass (every 5 minutes): fetch, decide, alert
  sample --mirror M [--evidence E]     print the ntfy messages a tick would send now, send nothing
  status                               last tick, mirror age, counts per desk and state, readability

Desks: ops (news, today), build (nightly), mohammad (waiting on him).
Environment (all optional): DISPATCH_HOME, DISPATCH_REPO, DISPATCH_BRANCH, DISPATCH_PATH,
DISPATCH_MIRROR_FILE, DISPATCH_EVIDENCE_FILE, DISPATCH_TOKEN_FILE, DISPATCH_TOPIC_FILE,
DISPATCH_NTFY (off = print instead of send), DISPATCH_NTFY_URL, DISPATCH_API, DISPATCH_NOW,
DISPATCH_OPS_MIN, DISPATCH_BUILD_END_UTC, DISPATCH_STALE_H, DISPATCH_LOOKBACK_DAYS.
The token and the topic are read from their files, sent, and never printed or logged.
"""
import argparse
import base64
import fcntl
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DESKS = ('ops', 'build', 'mohammad')
DUBAI = timezone(timedelta(hours=4))

# ---------------------------------------------------------------------------------------------
# Desk inference. Simple scoring on the card title: every term that appears (as the start of a
# word) adds its weight to the build score or the ops score. Build wins only when its score is
# strictly higher; a tie, or no match at all, goes to ops (news and today's work are the default,
# and an ops card is alerted sooner, which is the safe mistake). Terms are regex fragments matched
# at a word start, so "check" also catches "checks" and "build" catches "building" (not "built").
# ---------------------------------------------------------------------------------------------
BUILD_TERMS = [
    (r'back office', 3), (r'claude\.md', 3), (r'style\.md', 3), (r'toolbox', 2), (r'dispatcher', 2),
    (r'standing rule', 1), (r'build item', 2), (r'phase', 2), (r'rule', 1), (r'design', 1), (r'grid', 1),
    (r'beat sheet', 1), (r'audit', 1), (r'test', 1), (r'disk', 1), (r'container', 1), (r'key', 1),
    (r'token', 1), (r'dxb-(?:assets|queue|render)', 1), (r'template', 1), (r'profile', 1), (r'check', 1), (r'tool', 1),
    (r'server', 1), (r'workflow', 1), (r'runner', 1), (r'render', 1), (r'pipeline', 1),
    (r'script', 1), (r'backup', 1), (r'watch(?![- ]?guide)', 1), (r'desk', 1), (r'pilot', 1),
    (r'kit', 1), (r'skin', 1), (r'insert', 1), (r'install', 1), (r'build', 1), (r'skill', 1),
    (r'lane', 1), (r'github', 1), (r'inventory', 1), (r'repositor', 1),
    (r'safeguard', 1), (r'security', 1), (r'licen[cs]e', 1), (r'yolo', 1), (r'agent', 1),
    (r'inbox', 1), (r'status board', 1), (r'key register', 1),
]
OPS_TERMS = [
    (r'news', 1), (r'hold', 1), (r'delet', 1), (r'post', 1), (r't0\b', 1), (r'break', 1),
    (r'schedul', 1), (r'stor(?:y|ies)', 1), (r'preview', 1), (r'rumou?r', 1), (r'report', 1),
    (r'series', 1), (r'episode', 1), (r'slot', 1), (r'pinned comment', 1), (r'comment', 1),
    (r'reminder', 1), (r'takedown', 1), (r'trailer', 1), (r'review\b', 1), (r'digest', 1),
    (r'tonight', 1), (r'today', 1), (r'leak', 1), (r'queue', 1),
    (r'\d{1,2}:\d\d review', 3),      # the slot reviews ("14:00 review: ...") are news work
]
_BUILD_RE = [(re.compile(r'(?<![a-z0-9])(?:%s)' % t), w) for t, w in BUILD_TERMS]
_OPS_RE = [(re.compile(r'(?<![a-z0-9])(?:%s)' % t), w) for t, w in OPS_TERMS]


def keyword_scores(title):
    t = (title or '').lower()
    return (sum(w for rx, w in _BUILD_RE if rx.search(t)),
            sum(w for rx, w in _OPS_RE if rx.search(t)))


def keyword_desk(title):
    b, o = keyword_scores(title)
    return 'build' if b > o else 'ops'


def infer_desk(card):
    """Which desk holds this card now. An explicit desk on the card wins."""
    d = (card.get('desk') or '').strip().lower()
    if d in DESKS:
        return d
    frm = (card.get('from') or '').strip().lower()
    status = (card.get('status') or '').strip().lower()
    if frm == 'production':
        # Open: waiting on Mohammad. Answered (or done): it came back to production.
        if status == 'open':
            return 'mohammad'
        return keyword_desk(card.get('title'))
    # Advisor cards (and anything else): decisions and questions for Mohammad are his;
    # the rest is work for production, split by what the card is about.
    if (card.get('kind') or '').lower() in ('decision', 'question') and \
            (card.get('to') or '').strip().lower() == 'mohammad':
        return 'mohammad'
    return keyword_desk(card.get('title'))


# ---------------------------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------------------------
_TS = re.compile(r'^(\d{4})-(\d\d)-(\d\d)(?:[T ](\d\d):(\d\d)(?::(\d\d)(?:\.\d+)?)?)?\s*(Z|[+-]\d\d:?\d\d)?$')


def parse_ts(s):
    if not s or not isinstance(s, str):
        return None
    m = _TS.match(s.strip())
    if not m:
        return None
    y, mo, d, h, mi, se, tz = m.groups()
    try:
        dt = datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0), int(se or 0), tzinfo=timezone.utc)
    except ValueError:
        return None
    if tz and tz != 'Z':
        sign = 1 if tz[0] == '+' else -1
        digits = tz[1:].replace(':', '')
        dt -= sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
    return dt


def iso(dt):
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def utc_str(dt):
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%MZ')


def dubai_str(dt):
    """HH:MM Dubai, with the day when it differs from the UTC date."""
    d = dt.astimezone(DUBAI)
    s = d.strftime('%H:%M') + ' Dubai'
    if d.date() != dt.astimezone(timezone.utc).date():
        s += ' ' + d.strftime('%d %b')
    return s


def get_now(arg=None):
    v = arg or os.environ.get('DISPATCH_NOW')
    if v:
        dt = parse_ts(v)
        if dt is None:
            sys.exit('dispatch: cannot read the time "%s"' % v)
        return dt
    return datetime.now(timezone.utc)


def cut(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


# ---------------------------------------------------------------------------------------------
# Config (environment) and secrets
# ---------------------------------------------------------------------------------------------
def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def config():
    be = os.environ.get('DISPATCH_BUILD_END_UTC', '00:00')
    m = re.match(r'^(\d{1,2}):(\d\d)$', be)
    hh, mm = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    return {
        'home': os.environ.get('DISPATCH_HOME') or os.path.expanduser('~/backoffice/dispatch'),
        'ops_min': env_int('DISPATCH_OPS_MIN', 30),
        'build_end': (hh, mm),
        'stale_h': env_int('DISPATCH_STALE_H', 3),
        'lookback_days': env_int('DISPATCH_LOOKBACK_DAYS', 7),
        'token_file': os.environ.get('DISPATCH_TOKEN_FILE', '/etc/dxb-backup/github-token'),
        'topic_file': os.environ.get('DISPATCH_TOPIC_FILE', '/etc/dxb-backup/ntfy-topic'),
        'repo': os.environ.get('DISPATCH_REPO', 'mohdeltayer/dxb-queue'),
        'branch': os.environ.get('DISPATCH_BRANCH', 'desk'),
        'path': os.environ.get('DISPATCH_PATH', 'desk/mirror.json'),
        'api': os.environ.get('DISPATCH_API', 'https://api.github.com').rstrip('/'),
        'ntfy_url': os.environ.get('DISPATCH_NTFY_URL', 'https://ntfy.sh').rstrip('/'),
        'evidence_repos': ['mohdeltayer/dxb-assets', 'mohdeltayer/dxb-queue'],
        'runs_repo': 'mohdeltayer/dxb-assets',
    }


TOKEN_RE = re.compile(r'(ghp_|github_pat_|gho_|ghs_|ghu_|ghr_)[A-Za-z0-9_]+|[Bb]earer\s+\S+')


def read_secret(path):
    """The file's content on one line, or None. Never printed."""
    try:
        with open(path, encoding='utf-8') as f:
            v = re.sub(r'\s+', '', f.read())
        return v or None
    except OSError:
        return None


def readable(path):
    return os.access(path, os.R_OK)


class Scrubber:
    """Removes token shapes and the exact secret values from any text before it is logged."""

    def __init__(self, *secrets):
        self.secrets = [s for s in secrets if s]

    def __call__(self, text):
        text = TOKEN_RE.sub('<token>', str(text or ''))
        for s in self.secrets:
            text = text.replace(s, '<secret>')
        return text


# ---------------------------------------------------------------------------------------------
# mirror: sanitize the cards
# ---------------------------------------------------------------------------------------------
def _s(v):
    return v.strip() if isinstance(v, str) else ('' if v is None else str(v))


def _line(v, n):
    return cut(_s(v), n)


def sanitize_card(card_id, d):
    ans = d.get('answer') if isinstance(d.get('answer'), dict) else {}
    desk = _s(d.get('desk')).lower()
    return {
        'id': card_id,
        'from': _s(d.get('from')).lower() or None,
        'to': _s(d.get('to')) or None,
        'kind': _s(d.get('kind')).lower() or None,
        'title': _line(d.get('title'), 160),
        'status': _s(d.get('status')).lower() or None,
        'created_at': _s(d.get('created_at')) or None,
        'updated_at': _s(d.get('updated_at')) or None,
        'answer_at': _s(ans.get('at')) or None,
        'answer_choice': _line(ans.get('choice'), 40) or None,
        'picked_up_at': _s(d.get('picked_up_at')) or None,
        'progress': _line(d.get('progress'), 200) or None,
        'has_outcome': bool(_s(d.get('outcome'))),
        'desk': desk if desk in DESKS else None,
        'late_at': _s(d.get('late_at')) or None,
    }


def write_atomic(path, text):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = path + '.tmp.%d' % os.getpid()
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + '\n'


def cmd_mirror(args):
    src = args.items_dir
    cards = []
    skipped = 0
    for name in sorted(os.listdir(src)):
        if not name.endswith('.json'):
            continue
        try:
            with open(os.path.join(src, name), encoding='utf-8') as f:
                d = json.load(f)
        except (OSError, ValueError):
            skipped += 1
            continue
        if not isinstance(d, dict):
            skipped += 1
            continue
        cid = _s(d.get('id')) or name[:-5]
        cards.append(sanitize_card(cid, d))
    cards.sort(key=lambda c: (c['created_at'] or '', c['id']))
    now = get_now(args.now)
    # One card per line keeps the file's git diffs readable.
    body = ',\n'.join(' ' + json.dumps(c, ensure_ascii=False) for c in cards)
    text = '{"generated_at": %s, "cards": [\n%s\n]}\n' % (json.dumps(iso(now)), body)
    write_atomic(args.out, text)
    print('mirror: %d cards written to %s%s' % (len(cards), args.out, (' (%d unreadable files skipped)' % skipped) if skipped else ''))
    return 0


def load_mirror(path):
    with open(path, encoding='utf-8') as f:
        m = json.load(f)
    if not isinstance(m, dict) or not isinstance(m.get('cards'), list):
        raise ValueError('mirror has no cards list')
    return m


# ---------------------------------------------------------------------------------------------
# evidence: commits from local clones
# ---------------------------------------------------------------------------------------------
def repo_name(gitdir):
    p = subprocess.run(['git', '-C', gitdir, 'remote', 'get-url', 'origin'], capture_output=True, text=True)
    m = re.search(r'[/:]([^/:]+?)(?:\.git)?/?$', p.stdout.strip()) if p.returncode == 0 else None
    return m.group(1) if m else os.path.basename(os.path.abspath(gitdir))


def cmd_evidence(args):
    now = get_now(args.now)
    since = iso(now - timedelta(days=args.since_days))
    if args.api:
        # The Claude task's container: a slim clone has no history, so read it from the API with the
        # session's own token (GH_TOKEN or GITHUB_TOKEN). Never printed.
        cfg = config()
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN') or ''
        commits = []
        for repo in cfg['evidence_repos']:
            commits += fetch_commits(cfg, repo, since, token)
        commits.sort(key=lambda c: c['at'])
        out = {'commits': commits, 'runs': fetch_runs(cfg, token)}
        sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
        return 0
    if not args.git:
        sys.stderr.write('evidence: give --git <repo_dir> or --api\n')
        return 2
    refs = args.ref or ['origin/main']
    commits, seen = [], set()
    for gd in args.git:
        name = repo_name(gd)
        for ref in refs:
            # --format only: no --stat or -p, which would make a partial clone download blobs.
            p = subprocess.run(['git', '-C', gd, 'log', '--format=%H%x09%cI%x09%s', '--since=' + since, ref],
                               capture_output=True, text=True)
            if p.returncode != 0:
                sys.stderr.write('evidence: %s %s: %s\n' % (name, ref, cut(p.stderr, 160)))
                continue
            for line in p.stdout.splitlines():
                parts = line.split('\t', 2)
                if len(parts) < 3 or (name, parts[0]) in seen:
                    continue
                at = parse_ts(parts[1])
                if at is None:
                    continue
                seen.add((name, parts[0]))
                commits.append({'repo': name, 'sha': parts[0], 'at': iso(at), 'subject': parts[2]})
    commits.sort(key=lambda c: c['at'])
    sys.stdout.write(json.dumps({'commits': commits, 'runs': []}, ensure_ascii=False, indent=1) + '\n')
    return 0


def load_evidence(path):
    if not path:
        return {'commits': [], 'runs': []}
    with open(path, encoding='utf-8') as f:
        e = json.load(f)
    return {'commits': e.get('commits') or [], 'runs': e.get('runs') or []}


# ---------------------------------------------------------------------------------------------
# Analysis: desk, start, due, pick-up, late (shared by plan, tick, sample, status)
# ---------------------------------------------------------------------------------------------
PICK_SLACK = timedelta(minutes=2)


def id_in_subject(card_id, subject):
    """The card id as a whole token: not glued to more id characters on either side."""
    return re.search(r'(?<![A-Za-z0-9-])%s(?![A-Za-z0-9]|-[A-Za-z0-9])' % re.escape(card_id), subject or '', re.I) is not None


def start_time(c):
    created, ans = parse_ts(c.get('created_at')), parse_ts(c.get('answer_at'))
    if (c.get('from') or '') == 'production':
        if c.get('status') == 'answered':
            return ans or parse_ts(c.get('updated_at')) or created
        return created
    times = [t for t in (created, ans) if t]
    return max(times) if times else None


def next_build_end(start, hh, mm):
    cand = start.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return cand if cand > start else cand + timedelta(days=1)


def needs_no_action(c):
    """An FYI that Mohammad answered with 'Seen' asks nothing of any desk."""
    return (c.get('kind') == 'fyi' and (c.get('answer_choice') or '').strip().lower() == 'seen') \
        or (c.get('status') == 'answered' and (c.get('from') or '') == 'advisor' and
            infer_desk(c) == 'mohammad')


def analyze(cards, evidence, now, cfg):
    commits = sorted(evidence.get('commits') or [], key=lambda c: c.get('at') or '')
    runs = evidence.get('runs') or []
    lookback = now - timedelta(days=cfg['lookback_days'])
    out = []
    for c in cards:
        cid = c['id']
        desk = infer_desk(c)
        status = c.get('status')
        r = {'id': cid, 'card': c, 'desk': desk, 'start': None, 'due': None, 'picked': False,
             'late': False, 'backlog': False, 'evidence': [], 'pick_time': None, 'commit': None}
        r['done'] = status == 'done'
        r['noaction'] = (not r['done']) and needs_no_action(c)
        if r['done'] or r['noaction']:
            r['state'] = 'DONE'
            out.append(r)
            continue
        if desk == 'mohammad':
            r['state'] = 'WAITING' if status == 'open' else 'DONE'
            out.append(r)
            continue
        start = start_time(c)
        r['start'] = start
        if start is None:
            r['state'] = 'NEW'
            out.append(r)
            continue
        if desk == 'ops':
            r['due'] = start + timedelta(minutes=cfg['ops_min'])
        else:
            r['due'] = next_build_end(start, *cfg['build_end'])

        floor = start - PICK_SLACK
        upd = parse_ts(c.get('updated_at'))
        times = []   # (time, text), the evidence in the order it is trusted for write-back
        mine = [k for k in commits if id_in_subject(cid, k.get('subject'))
                and (parse_ts(k.get('at')) or floor) >= start]
        for k in mine:
            r['evidence'].append('commit %s %s "%s"' % (k.get('repo'), (k.get('sha') or '')[:7], cut(k.get('subject'), 60)))
        if mine:
            first = mine[0]
            r['commit'] = first
            times.append(parse_ts(first.get('at')))
        shas = {k.get('sha') for k in mine}
        for run in runs:
            if id_in_subject(cid, run.get('display_title')) or run.get('head_sha') in shas:
                r['evidence'].append('run %s %s%s' % (run.get('name') or 'workflow', run.get('status') or '?',
                                                      (' ' + run['conclusion']) if run.get('conclusion') else ''))
        pk = parse_ts(c.get('picked_up_at'))
        valid_pk = pk is not None and pk >= floor
        if valid_pk:
            r['evidence'].append('picked_up_at %s' % utc_str(pk))
            times.append(pk)
        if c.get('progress') and upd is not None and upd >= floor:
            r['evidence'].append('progress "%s" at %s' % (cut(c['progress'], 50), utc_str(upd)))
            times.append(upd)
        if c.get('has_outcome'):
            r['evidence'].append('outcome set')
            times.append(upd or start)
        r['valid_pk'] = valid_pk
        picked = bool(times)
        r['picked'] = picked
        r['pick_time'] = min(t for t in times if t) if picked else None
        in_window = start >= lookback
        if not picked and now > r['due']:
            if in_window:
                r['late'] = True
            else:
                r['backlog'] = True
        r['state'] = 'PICKED UP' if picked else ('LATE' if r['late'] else ('BACKLOG' if r['backlog'] else 'NEW'))
        out.append(r)
    return out


def writeback(results):
    """Fields the Claude task should apply to the cards; only what is missing is ever proposed."""
    out = []
    for r in results:
        c = r['card']
        if r['done'] or r['noaction']:
            continue
        f = {}
        # A production card that is open sits with Mohammad only until he answers, so its desk is
        # not written down; every other card keeps the desk it was routed to.
        dynamic = (c.get('from') == 'production' and c.get('status') == 'open')
        if not c.get('desk') and not dynamic:
            f['desk'] = r['desk']
        if r['desk'] in ('ops', 'build') and r['picked'] and not r.get('valid_pk') and r['pick_time']:
            f['picked_up_at'] = iso(r['pick_time'])
        if r['commit'] and not c.get('progress'):
            k = r['commit']
            f['progress'] = 'evidence: %s %s %s' % (k.get('repo'), (k.get('sha') or '')[:7], cut(k.get('subject'), 80))
        if r['late'] and not c.get('late_at'):
            f['late_at'] = iso(r['due'])
        if f:
            out.append({'id': r['id'], 'fields': f})
    return out


STATE_ORDER = {'LATE': 0, 'NEW': 1, 'PICKED UP': 2, 'BACKLOG': 3}


def queue_markdown(desk, results, now):
    rows = [r for r in results if r['desk'] == desk and r['state'] in STATE_ORDER]
    rows.sort(key=lambda r: (STATE_ORDER[r['state']], r['due'] or now, r['id']))
    counts = {}
    for r in rows:
        counts[r['state']] = counts.get(r['state'], 0) + 1
    label = {'ops': 'Ops desk (news and today\'s work)', 'build': 'Build desk (nightly)'}[desk]
    rule = ('due 30 minutes after the card reached production' if desk == 'ops'
            else 'due at the end of the next build night (04:00 Dubai)')
    lines = ['# %s queue' % label, '',
             'Generated %s by the dispatcher. Cards not done: %d (%s); %s.' % (
                 utc_str(now), len(rows), ', '.join('%d %s' % (v, k) for k, v in sorted(counts.items(), key=lambda kv: STATE_ORDER[kv[0]])) or 'none', rule),
             'Put the card id in commit subjects: that is what counts as pick-up. BACKLOG is older than the lookback and never alerts.', '']
    if not rows:
        lines.append('Nothing waiting.')
    for r in rows:
        due = '%s (%s)' % (utc_str(r['due']), dubai_str(r['due'])) if r['due'] else 'n/a'
        ev = '; '.join(r['evidence']) if r['evidence'] else 'none'
        lines.append('- %s | %s | %s | due %s | evidence: %s' % (r['state'], r['id'], cut(r['card'].get('title'), 100), due, ev))
    return '\n'.join(lines) + '\n'


def summary_counts(results):
    counts = {}
    for r in results:
        k = (r['desk'], r['state'])
        counts[k] = counts.get(k, 0) + 1
    return counts


def format_counts(counts):
    lines = []
    for desk in DESKS:
        parts = ['%s %d' % (st, n) for (d, st), n in sorted(counts.items()) if d == desk]
        lines.append('  %-9s %s' % (desk, ', '.join(parts) or '-'))
    return '\n'.join(lines)


def cmd_plan(args):
    cfg = config()
    now = get_now(args.now)
    cards = load_mirror(args.mirror)['cards']
    results = analyze(cards, load_evidence(args.evidence), now, cfg)
    os.makedirs(args.out, exist_ok=True)
    write_atomic(os.path.join(args.out, 'ops-queue.md'), queue_markdown('ops', results, now))
    write_atomic(os.path.join(args.out, 'build-queue.md'), queue_markdown('build', results, now))
    wb = writeback(results)
    write_atomic(os.path.join(args.out, 'writeback.json'), dump_json(wb))
    print('plan: %d cards, %d write-backs in %s' % (len(cards), len(wb), args.out))
    print(format_counts(summary_counts(results)))
    return 0


# ---------------------------------------------------------------------------------------------
# ntfy messages (shared by tick and sample)
# ---------------------------------------------------------------------------------------------
MAX_LINES = 12
REALERT = timedelta(hours=1)


def capped(lines):
    if len(lines) <= MAX_LINES:
        return lines
    return lines[:MAX_LINES] + ['and %d more' % (len(lines) - MAX_LINES)]


def due_hm(due, now):
    """HH:MM Dubai; the Dubai date is added when the due time is not today (Dubai)."""
    d = due.astimezone(DUBAI)
    s = d.strftime('%H:%M') + ' Dubai'
    if d.date() != now.astimezone(DUBAI).date():
        s += ' ' + d.strftime('%d %b')
    return s


def late_line(r, now):
    return 'LATE %s: %s (%s), due %s' % (r['desk'], cut(r['card'].get('title'), 70), r['id'], due_hm(r['due'], now))


def new_line(r):
    return '%s: %s (%s)' % (r['card'].get('kind') or 'card', cut(r['card'].get('title'), 70), r['id'])


def build_messages(results, state, now, mirror_generated, baseline, stale_h):
    """-> (messages, silent_keys). A message: group, title, priority, tags, lines, ids/keys it covers.

    `state` is the persistent state (or an empty one for `sample`); nothing in it is changed here.
    """
    late, new_you, new_ops, silent = [], [], [], []
    for r in results:
        if r['done'] or r['noaction']:
            continue
        if r['late']:
            last = parse_ts(state.get('last_alert', {}).get(r['id']))
            if last is None or now - last >= REALERT:
                late.append(r)
        key = '%s|%s' % (r['id'], r['desk'])
        if key in state.get('notified', {}):
            continue
        if baseline or r['desk'] == 'build':
            silent.append(key)            # build cards are in the build queue file, not on the phone
        elif r['desk'] == 'mohammad' and r['card'].get('status') == 'open':
            new_you.append(r)
        elif r['desk'] == 'ops':
            new_ops.append(r)
        else:
            silent.append(key)
    msgs = []
    if late:
        late.sort(key=lambda r: r['due'])
        msgs.append({'group': 'late', 'title': 'Inbox: %d late' % len(late), 'priority': 'high', 'tags': 'warning',
                     'lines': capped([late_line(r, now) for r in late]), 'ids': [r['id'] for r in late], 'keys': []})
    if new_you:
        msgs.append({'group': 'new_you', 'title': 'Inbox: %d new for you' % len(new_you), 'priority': 'default',
                     'tags': 'inbox', 'lines': capped([new_line(r) for r in new_you]), 'ids': [],
                     'keys': ['%s|%s' % (r['id'], r['desk']) for r in new_you]})
    if new_ops:
        msgs.append({'group': 'new_ops', 'title': 'Inbox: %d new for ops' % len(new_ops), 'priority': 'low',
                     'tags': 'ops', 'lines': capped([new_line(r) for r in new_ops]), 'ids': [],
                     'keys': ['%s|%s' % (r['id'], r['desk']) for r in new_ops]})
    gen = parse_ts(mirror_generated)
    age_h = (now - gen).total_seconds() / 3600 if gen else None
    if age_h is None or age_h > stale_h:
        last = parse_ts(state.get('last_stale'))
        if last is None or now - last >= REALERT:
            line = ('dispatcher: inbox mirror is %d h old' % int(age_h)) if age_h is not None \
                else 'dispatcher: inbox mirror has no readable time'
            msgs.append({'group': 'stale', 'title': 'Inbox: mirror stale', 'priority': 'default', 'tags': 'warning',
                         'lines': [line], 'ids': [], 'keys': []})
    return msgs, silent


def render_message(m):
    return '--- ntfy [%s] tags=%s title=%s\n%s' % (m['priority'], m['tags'], m['title'], '\n'.join(m['lines']))


def cmd_sample(args):
    cfg = config()
    now = get_now(args.now)
    m = load_mirror(args.mirror)
    results = analyze(m['cards'], load_evidence(args.evidence), now, cfg)
    msgs, _ = build_messages(results, {}, now, m.get('generated_at'), False, cfg['stale_h'])
    if not msgs:
        print('(no messages: nothing is late, new or stale)')
    for msg in msgs:
        print(render_message(msg))
    return 0


# ---------------------------------------------------------------------------------------------
# tick: the server pass
# ---------------------------------------------------------------------------------------------
class ApiError(Exception):
    pass


def http_get(url, token, accept='application/vnd.github+json', timeout=30):
    """GET with the token if there is one; on 401 or 403 retry once without it (public repos)."""
    def once(tok):
        hdr = {'Accept': accept, 'User-Agent': 'dxb-dispatch', 'X-GitHub-Api-Version': '2022-11-28'}
        if tok:
            hdr['Authorization'] = 'Bearer ' + tok
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=timeout) as resp:
            return resp.read()
    try:
        return once(token)
    except urllib.error.HTTPError as e:
        if token and e.code in (401, 403):
            try:
                return once(None)
            except urllib.error.HTTPError as e2:
                raise ApiError('HTTP %d from %s' % (e2.code, urllib.parse.urlsplit(url).path))
            except (urllib.error.URLError, OSError) as e2:
                raise ApiError('network error: %s' % e2)
        raise ApiError('HTTP %d from %s' % (e.code, urllib.parse.urlsplit(url).path))
    except (urllib.error.URLError, OSError) as e:
        raise ApiError('network error: %s' % e)


def fetch_mirror(cfg, token):
    path = os.environ.get('DISPATCH_MIRROR_FILE')
    if path:
        return load_mirror(path)
    url = '%s/repos/%s/contents/%s?ref=%s' % (cfg['api'], cfg['repo'], urllib.parse.quote(cfg['path']),
                                              urllib.parse.quote(cfg['branch']))
    raw = http_get(url, token, accept='application/vnd.github.raw+json')
    try:
        m = json.loads(raw.decode('utf-8'))
    except ValueError:
        raise ApiError('mirror is not JSON')
    if isinstance(m, dict) and 'content' in m and 'cards' not in m:      # JSON envelope instead of raw
        m = json.loads(base64.b64decode(m['content']).decode('utf-8'))
    if not isinstance(m, dict) or not isinstance(m.get('cards'), list):
        raise ApiError('mirror has no cards list')
    return m


def fetch_commits(cfg, repo, since, token):
    out = []
    short = repo.split('/')[-1]
    for page in range(1, 6):
        url = '%s/repos/%s/commits?sha=main&since=%s&per_page=100&page=%d' % (cfg['api'], repo, urllib.parse.quote(since), page)
        data = json.loads(http_get(url, token).decode('utf-8'))
        if not isinstance(data, list):
            raise ApiError('unexpected commits answer for %s' % short)
        for c in data:
            cm = c.get('commit') or {}
            at = parse_ts(((cm.get('committer') or {}).get('date')))
            if at is None:
                continue
            out.append({'repo': short, 'sha': c.get('sha') or '', 'at': iso(at),
                        'subject': (cm.get('message') or '').split('\n', 1)[0]})
        if len(data) < 100:
            break
    return out


def fetch_runs(cfg, token):
    url = '%s/repos/%s/actions/runs?per_page=50' % (cfg['api'], cfg['runs_repo'])
    data = json.loads(http_get(url, token).decode('utf-8'))
    out = []
    for r in (data.get('workflow_runs') or []) if isinstance(data, dict) else []:
        out.append({'name': os.path.basename(r.get('path') or '') or r.get('name') or 'workflow',
                    'display_title': r.get('display_title') or '', 'head_sha': r.get('head_sha') or '',
                    'status': r.get('status'), 'conclusion': r.get('conclusion'),
                    'at': r.get('created_at')})
    return out


def read_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class Log:
    def __init__(self, home, scrub):
        self.path = os.path.join(home, 'dispatch.log')
        self.scrub = scrub

    def line(self, now, text):
        try:
            if os.path.exists(self.path) and os.path.getsize(self.path) > 1_000_000:
                os.replace(self.path, self.path + '.1')
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write('%s %s\n' % (iso(now), self.scrub(text)))
        except OSError:
            pass


def ntfy_send(cfg, msg, scrub, log, now):
    """Send one message. Returns True when sent (or printed when DISPATCH_NTFY=off)."""
    if os.environ.get('DISPATCH_NTFY', 'on').lower() == 'off':
        print(render_message(msg))
        log.line(now, 'ntfy off: [%s] %s (%d lines)' % (msg['priority'], msg['title'], len(msg['lines'])))
        return True
    topic = read_secret(cfg['topic_file'])
    if not topic:
        log.line(now, 'ntfy: topic file not readable or empty, alert NOT sent: %s' % msg['title'])
        return False
    req = urllib.request.Request('%s/%s' % (cfg['ntfy_url'], topic), data='\n'.join(msg['lines']).encode('utf-8'),
                                 headers={'Title': msg['title'], 'Priority': msg['priority'], 'Tags': msg['tags'],
                                          'User-Agent': 'dxb-dispatch'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
        log.line(now, 'ntfy sent: %s (%d lines)' % (msg['title'], len(msg['lines'])))
        return True
    except (urllib.error.URLError, OSError) as e:
        text = str(e).replace(topic, '[topic]')
        log.line(now, 'ntfy: send failed (%s): %s' % (scrub(text), msg['title']))
        return False


def cmd_tick(args):
    cfg = config()
    now = get_now()
    home = cfg['home']
    os.makedirs(home, exist_ok=True)
    os.chmod(home, 0o700)
    token = read_secret(cfg['token_file'])
    topic = read_secret(cfg['topic_file'])
    scrub = Scrubber(token, topic)
    log = Log(home, scrub)

    lock = open(os.path.join(home, 'lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log.line(now, 'tick skipped: the previous pass is still running')
        return 0

    state = read_json(os.path.join(home, 'state.json'), {})
    state.setdefault('seen', {})
    state.setdefault('notified', {})
    state.setdefault('last_alert', {})
    state.setdefault('alerts', [])
    state.setdefault('first_tick', iso(now))
    baseline = not state.get('baselined')

    # 1. the mirror
    mirror, fail = None, None
    try:
        mirror = fetch_mirror(cfg, token)
    except (ApiError, OSError, ValueError) as e:
        fail = scrub(e)
        log.line(now, 'mirror fetch failed: %s' % fail)
    results = []
    cards_n = 0
    if mirror is not None:
        state['mirror_generated_at'] = mirror.get('generated_at')
        state['mirror_fetched_at'] = iso(now)
        write_atomic(os.path.join(home, 'mirror.json'), json.dumps(mirror, ensure_ascii=False))
        cards = mirror['cards']
        cards_n = len(cards)

        # 2. the evidence
        evidence = fetch_evidence(cfg, token, now, home, scrub, log)
        write_atomic(os.path.join(home, 'evidence.json'), json.dumps(evidence, ensure_ascii=False))
        results = analyze(cards, evidence, now, cfg)
        for r in results:
            state['seen'].setdefault(r['id'], iso(now))

    # 3. decide and alert (a failed fetch still gets the stale-mirror check)
    gen = state.get('mirror_generated_at') or state['first_tick']
    msgs, silent = build_messages(results, state, now, gen, baseline and mirror is not None, cfg['stale_h'])
    sent = []
    for m in msgs:
        if ntfy_send(cfg, m, scrub, log, now):
            sent.append(m['group'])
            state['alerts'].append({'at': iso(now), 'group': m['group'], 'title': m['title'], 'lines': len(m['lines'])})
            for cid in m['ids']:
                state['last_alert'][cid] = iso(now)
            for k in m['keys']:
                state['notified'][k] = iso(now)
            if m['group'] == 'stale':
                state['last_stale'] = iso(now)
    if mirror is not None:
        for k in silent:
            state['notified'][k] = iso(now)
        state['baselined'] = True
        ids = {r['id'] for r in results}
        state['seen'] = {k: v for k, v in state['seen'].items() if k in ids}
        state['last_alert'] = {k: v for k, v in state['last_alert'].items() if k in ids}
    state['alerts'] = state['alerts'][-20:]
    state['last_tick'] = iso(now)
    write_atomic(os.path.join(home, 'state.json'), dump_json(state))

    if mirror is not None:
        write_atomic(os.path.join(home, 'heartbeat'), iso(now) + '\n')
        counts = summary_counts(results)
        n = lambda d, st: counts.get((d, st), 0)
        age = ''
        g = parse_ts(mirror.get('generated_at'))
        if g:
            age = ' mirror_age=%.1fh' % ((now - g).total_seconds() / 3600)
        log.line(now, 'tick ok cards=%d ops(new=%d picked=%d late=%d) build(new=%d picked=%d late=%d) mohammad=%d%s%s alerts=%s' % (
            cards_n, n('ops', 'NEW'), n('ops', 'PICKED UP'), n('ops', 'LATE'), n('build', 'NEW'), n('build', 'PICKED UP'),
            n('build', 'LATE'), n('mohammad', 'WAITING'), age, ' baseline' if baseline else '', ','.join(sent) or 'none'))
    else:
        log.line(now, 'tick done without a mirror alerts=%s' % (','.join(sent) or 'none'))
    return 0


def fetch_evidence(cfg, token, now, home, scrub, log):
    path = os.environ.get('DISPATCH_EVIDENCE_FILE')
    if path:
        return load_evidence(path)
    since = iso(now - timedelta(days=8))
    cached = read_json(os.path.join(home, 'evidence.json'), {'commits': [], 'runs': []})
    commits, runs = [], []
    for repo in cfg['evidence_repos']:
        short = repo.split('/')[-1]
        try:
            commits += fetch_commits(cfg, repo, since, token)
        except (ApiError, ValueError, OSError) as e:
            log.line(now, 'commits of %s failed, using the last good copy: %s' % (short, scrub(e)))
            commits += [c for c in cached.get('commits', []) if c.get('repo') == short]
    try:
        runs = fetch_runs(cfg, token)
    except (ApiError, ValueError, OSError) as e:
        log.line(now, 'actions runs failed, using the last good copy: %s' % scrub(e))
        runs = cached.get('runs', [])
    return {'commits': commits, 'runs': runs}


# ---------------------------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------------------------
def cmd_status(args):
    cfg = config()
    home = cfg['home']
    now = get_now()
    state = read_json(os.path.join(home, 'state.json'), {})
    hb = (open(os.path.join(home, 'heartbeat'), encoding='utf-8').read().strip()
          if os.path.exists(os.path.join(home, 'heartbeat')) else None)
    print('home: %s' % home)
    last = parse_ts(hb)
    print('last good tick: %s%s' % (hb or 'never', (' (%d min ago)' % ((now - last).total_seconds() // 60)) if last else ''))
    gen = parse_ts(state.get('mirror_generated_at'))
    print('mirror generated: %s%s' % (state.get('mirror_generated_at') or 'unknown',
                                      (' (%.1f h old)' % ((now - gen).total_seconds() / 3600)) if gen else ''))
    mirror = read_json(os.path.join(home, 'mirror.json'), None)
    if mirror and isinstance(mirror.get('cards'), list):
        results = analyze(mirror['cards'], load_evidence(os.path.join(home, 'evidence.json')) if os.path.exists(os.path.join(home, 'evidence.json')) else {'commits': [], 'runs': []}, now, cfg)
        print('cards: %d' % len(results))
        print('per desk and state:')
        print(format_counts(summary_counts(results)))
    else:
        print('cards: no mirror copy yet')
    print('last alerts:')
    for a in state.get('alerts', [])[-5:] or []:
        print('  %s  %s (%d lines)' % (a.get('at'), a.get('title'), a.get('lines', 0)))
    if not state.get('alerts'):
        print('  none')
    print('github token file: %s' % ('readable' if readable(cfg['token_file']) else 'NOT readable'))
    print('ntfy topic file:   %s' % ('readable' if readable(cfg['topic_file']) else 'NOT readable'))
    return 0


# ---------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(prog='dispatch.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('mirror')
    p.add_argument('items_dir')
    p.add_argument('out')
    p.add_argument('--now')
    p.set_defaults(fn=cmd_mirror)
    p = sub.add_parser('evidence')
    p.add_argument('--git', action='append')
    p.add_argument('--api', action='store_true')
    p.add_argument('--ref', action='append')
    p.add_argument('--since-days', type=int, default=8)
    p.add_argument('--now')
    p.set_defaults(fn=cmd_evidence)
    p = sub.add_parser('plan')
    p.add_argument('--mirror', required=True)
    p.add_argument('--evidence')
    p.add_argument('--now')
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser('tick')
    p.set_defaults(fn=cmd_tick)
    p = sub.add_parser('sample')
    p.add_argument('--mirror', required=True)
    p.add_argument('--evidence')
    p.add_argument('--now')
    p.set_defaults(fn=cmd_sample)
    p = sub.add_parser('status')
    p.set_defaults(fn=cmd_status)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    sys.exit(main())
