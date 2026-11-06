"""Build check-ins for Mohammad (adv-20261103-three-focus-areas, checkins_1805, 3 Nov 2026).

One short phone push when a build starts and when it is released or skipped, every night (and for the 16:00 studio
release), so he never has to ask. The keeper's alarms (01:20 no started line, 04:15 no release note) stay as the
fallback. No post text and no secrets in a message; the topic comes from the NTFY_TOPIC secret and is never printed.

    python3 ops/build/notify_build.py started "<items planned>"        # the build desk, after its started line
    python3 ops/build/notify_build.py release ops/build/releases/<date>.md
    python3 ops/build/notify_build.py test

Messages:
    Build started HH:MM Dubai: <items planned>
    Build released HH:MM Dubai: <items shipped>; skipped: <items>
    Build skipped HH:MM Dubai: <reason>                (a release note with nothing under "## Merged")
"""
import datetime
import os
import re
import sys
import urllib.request

DUBAI = datetime.timezone(datetime.timedelta(hours=4))
MAX = 400


def now_dubai():
    return datetime.datetime.now(DUBAI).strftime('%H:%M')


def cut(s, n=MAX):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def section(text, *names):
    """The top-level bullets of the first section whose heading starts with one of names."""
    out, on = [], False
    for line in text.splitlines():
        if line.startswith('## '):
            on = any(line[3:].strip().lower().startswith(n) for n in names)
            continue
        if on and line.startswith('- '):
            out.append(line[2:])
    return out


def item_name(bullet):
    """'Review-scores template (card adv-...): ...' -> 'Review-scores template'."""
    b = re.split(r'\s*[\(:]', bullet, 1)[0]
    return cut(b, 60)


def release_message(path):
    text = open(path, encoding='utf-8').read()
    merged = [item_name(b) for b in section(text, 'merged')]
    skipped = [item_name(b) for b in section(text, 'skipped', 'not done')]
    if not merged:
        why = skipped[0] if skipped else 'no item passed the test gate'
        return 'Build skipped %s Dubai: %s' % (now_dubai(), why)
    msg = 'Build released %s Dubai: %s' % (now_dubai(), '; '.join(merged))
    if skipped:
        msg += '; skipped: ' + ', '.join(skipped)
    return cut(msg)


def send(title, body):
    topic = os.environ.get('NTFY_TOPIC', '').strip()
    if os.environ.get('NOTIFY_DRY_RUN') or not topic:
        print('[dry run, no topic]' if not topic else '[dry run]', title, '|', body)
        return True
    url = os.environ.get('NTFY_URL', 'https://ntfy.sh').rstrip('/') + '/' + topic
    req = urllib.request.Request(url, data=body.encode('utf-8'),
                                 headers={'Title': title.encode('utf-8').decode('latin-1', 'ignore'),
                                          'Tags': 'hammer_and_wrench', 'User-Agent': 'dxb-build-notify'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
        print('sent:', title)
        return True
    except OSError as e:
        print('not sent:', type(e).__name__, str(e).replace(topic, '[topic]')[:120])
        return False


def main(a):
    if not a:
        raise SystemExit(__doc__)
    if a[0] == 'started':
        body = cut('Build started %s Dubai: %s' % (now_dubai(), ' '.join(a[1:]) or 'items from the build queue'))
        return send('Build started', body)
    if a[0] == 'release' and len(a) == 2:
        body = release_message(a[1])
        return send(body.split(' ', 2)[0] + ' ' + body.split(' ', 2)[1], body)
    if a[0] == 'test':
        return send('Build check-in test', 'Build check-in test %s Dubai: the started and release pushes work.' % now_dubai())
    raise SystemExit(__doc__)


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1:]) else 1)
