"""Usage numbers for the morning digest card (adv-20261030-save-claude-usage point 5, Mohammad 30 Oct 2026).

    python3 newsroom/usage_report.py [days=3] [--reels 2026-10-29=21,2026-10-28=24,...] [--transcript file.jsonl]

Per UTC day, for the last `days` full days plus today so far, numbers only:
  turns      Claude turns in the ops session: user-role entries in the session transcript that start a turn
             (Mohammad's messages, scheduled triggers, notifications, helper hand-backs), not tool results
  reels      Reels published that day, passed with --reels from the Inbox `published` collection (the session
             reads it with ArtifactData; the format ledger dates entries by when they were added, not the slot)
  per_reel   turns / reels
  helpers    helper agents launched that day (Agent tool calls in the transcript)
  gh_min     GitHub-hosted runner minutes in dxb-assets and dxb-queue (run start to last update, so a run that
             waited on a concurrency group counts its wait; an upper bound)
  srv_min    self-hosted (dxb-render-1) minutes, same measure: runs of the workflows whose runs-on names
             self-hosted (SELF_HOSTED below, from .github/workflows)
The transcript path defaults to the newest .jsonl in ~/.claude/projects/-home-user/. GitHub numbers come from the
Actions REST API through the session proxy (no token is printed or stored).
"""
import collections, datetime as dt, glob, json, os, subprocess, sys

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OPTS = dict(zip(sys.argv[1::1], sys.argv[2::1]))
DAYS = int(ARGS[0]) if ARGS and ARGS[0].isdigit() else 3
SELF_HOSTED = {'backoffice-install.yml', 'event-capture.yml', 'event-diag.yml', 'prerender.yml', 'render-breaking.yml',
               'render-live.yml', 'runner-hook.yml', 'server-check.yml', 'watch-digest.yml'}
HERE = os.path.dirname(os.path.abspath(__file__))
REPOS = ['mohdeltayer/dxb-assets', 'mohdeltayer/dxb-queue']


def transcript():
    if OPTS.get('--transcript'):
        return OPTS['--transcript']
    fs = glob.glob(os.path.expanduser('~/.claude/projects/-home-user/*.jsonl'))
    return max(fs, key=os.path.getmtime)


def claude(days):
    turns, helpers = collections.Counter(), collections.Counter()
    with open(transcript()) as f:
        for line in f:
            if '"type":"user"' not in line and '"type":"assistant"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            day = (d.get('timestamp') or '')[:10]
            if day not in days:
                continue
            content = (d.get('message') or {}).get('content')
            if d.get('type') == 'user':
                if isinstance(content, list) and content and isinstance(content[0], dict) \
                        and content[0].get('type') == 'tool_result':
                    continue
                turns[day] += 1
            elif isinstance(content, list):
                helpers[day] += sum(1 for c in content if isinstance(c, dict) and c.get('type') == 'tool_use'
                                    and c.get('name') == 'Agent')
    return turns, helpers


def reels():
    out = collections.Counter()
    for pair in (OPTS.get('--reels') or '').split(','):
        if '=' in pair:
            d, n = pair.split('=')
            out[d.strip()] = int(n)
    return out


def api(path):
    out = subprocess.run(['curl', '-s', '--max-time', '30', 'https://api.github.com' + path],
                         capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except ValueError:
        return {}


def minutes(days):
    gh, srv = collections.Counter(), collections.Counter()
    since = min(days)
    for repo in REPOS:
        page = 1
        while True:
            runs = api(f'/repos/{repo}/actions/runs?per_page=100&page={page}&created=>={since}').get('workflow_runs', [])
            for run in runs:
                a, b = run.get('run_started_at'), run.get('updated_at')
                if not a or not b or a[:10] not in days:
                    continue
                m = (dt.datetime.fromisoformat(b.replace('Z', '+00:00'))
                     - dt.datetime.fromisoformat(a.replace('Z', '+00:00'))).total_seconds() / 60
                wf = os.path.basename(run.get('path') or '')
                (srv if repo.endswith('dxb-assets') and wf in SELF_HOSTED else gh)[a[:10]] += m
            if len(runs) < 100 or page >= 10:
                break
            page += 1
    return gh, srv


def main():
    now = dt.datetime.utcnow()
    days = [(now - dt.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(DAYS, -1, -1)]
    turns, helpers = claude(set(days))
    r = reels()
    gh, srv = minutes(set(days))
    print('day (UTC)   turns  reels  turns/reel  helpers  gh_min  srv_min')
    for d in days:
        pr = f'{turns[d] / r[d]:.1f}' if r[d] else '-'
        tag = ' (so far)' if d == days[-1] else ''
        print(f'{d}  {turns[d]:5d}  {r[d]:5d}  {pr:>10}  {helpers[d]:7d}  {gh[d]:6.0f}  {srv[d]:7.0f}{tag}')


if __name__ == '__main__':
    main()
