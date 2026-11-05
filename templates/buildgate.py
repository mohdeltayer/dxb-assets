"""Build gate: the steps a Reel job must show before any render (adv-20261105-p2-audit-fixes, 5 Nov 2026).

Production 2's audit of 5 Nov found jobs rendered with no ledger search, no reel-check, no story file and no lane
chosen. This gate turns those steps into refusals. render_job.py runs it first for `check`, `text` and `run`, so the
pre-render check, render.yml, render-live.yml and render-breaking.yml all stop on it before any footage is fetched.

A job must carry:
  "story":       the story id; newsroom/stories/<id>.json must exist and hold
                   - "ledger_find": written by `python3 newsroom/ledger.py find <words> --record <id>`
                   - "sources": at least one entry with a "url"
                   - "first_report": where and when the story was first reported (text with a time)
                   - "source_type": "primary" or "secondary"
                   - "footage": what the Reel shows; stills must say why ("stills: <reason and sources tried>")
                   - "lane" (the account lane, as today) and "beat"
  "render_lane": "server" (the default: dxb-render-1, jobs/live/ and render-live.yml, or jobs/breaking/) or
                 "hosted" (GitHub's runner through jobs/render/ and render.yml) with "lane_reason"
  "reel_check":  newsroom/reel-check.md filled in, at least MIN_LINES answers, none of them "no": either a list of
                 {"line", "answer": "yes" | "n/a", "evidence"} or a dict {line: "yes: evidence" | "n/a: why"}

Jobs under jobs/test/ (examples and test renders) are not gated. There is no switch to turn the gate off.

    python3 templates/buildgate.py jobs/live/<name>.json      # prints the refusals, exit 1 when there are any
"""
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
STORIES = REPO / 'newsroom' / 'stories'
MIN_LINES = 8
STORY_FIELDS = ('first_report', 'source_type', 'footage', 'lane', 'beat')
SERVER_DIRS = ('jobs/live/', 'jobs/breaking/', 'jobs/prerender/')
HOSTED_DIRS = ('jobs/render/', 'jobs/breaking/', 'jobs/prerender/')


def _rel(path):
    p = pathlib.Path(path).resolve()
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return str(path).replace(os.sep, '/').lstrip('./')


def _answers(rc):
    """(answer, line) pairs from either reel_check shape."""
    if isinstance(rc, dict):
        for line, v in rc.items():
            yield (str(v.get('answer', '')) if isinstance(v, dict) else str(v)), str(line)
    elif isinstance(rc, list):
        for item in rc:
            if isinstance(item, dict):
                yield str(item.get('answer', '')), str(item.get('line', '?'))
            else:
                yield str(item), '?'


def problems(path, job):
    """The list of refusals for this job file (empty when it may render)."""
    rel = _rel(path)
    if rel.startswith('jobs/test/'):
        return []
    out = []

    lane = job.get('render_lane')
    if lane not in ('server', 'hosted'):
        out.append('render_lane missing: set "render_lane": "server" (default; jobs/live/ and render-live.yml) '
                   'or "hosted" with "lane_reason"')
    elif lane == 'server' and not rel.startswith(SERVER_DIRS):
        out.append(f'render_lane server: the job belongs in jobs/live/ (dispatch render-live.yml), not {rel}')
    elif lane == 'hosted':
        if not str(job.get('lane_reason') or '').strip():
            out.append('render_lane hosted needs "lane_reason" (why not the server)')
        if not rel.startswith(HOSTED_DIRS):
            out.append(f'render_lane hosted: the job belongs in jobs/render/, not {rel}')

    sid = job.get('story')
    if not sid:
        out.append('story missing: set "story": "<story id>" and write newsroom/stories/<id>.json first')
    else:
        f = STORIES / f'{sid}.json'
        if not f.exists():
            out.append(f'story file missing: newsroom/stories/{sid}.json')
        else:
            try:
                s = json.loads(f.read_text())
            except ValueError as e:
                s = {}
                out.append(f'story file unreadable: {e}')
            if not s.get('ledger_find'):
                out.append(f'no ledger search recorded: python3 newsroom/ledger.py find <words> --record {sid}')
            if not any(isinstance(x, dict) and x.get('url') for x in s.get('sources') or []):
                out.append('story file: no source with a url')
            for k in STORY_FIELDS:
                if not str(s.get(k) or '').strip():
                    out.append(f'story file: "{k}" missing')
            if s.get('source_type') and s.get('source_type') not in ('primary', 'secondary'):
                out.append('story file: "source_type" must be primary or secondary')
            fo = str(s.get('footage') or '').strip().lower()
            if fo.startswith('stills') and len(fo) < 20:
                out.append('story file: stills need the reason and the footage sources tried')

    rc = job.get('reel_check')
    if not rc:
        out.append('reel_check missing: fill newsroom/reel-check.md into the job as "reel_check"')
    else:
        pairs = list(_answers(rc))
        if len(pairs) < MIN_LINES:
            out.append(f'reel_check has {len(pairs)} answers; at least {MIN_LINES} lines of reel-check.md')
        noes = [line for a, line in pairs if a.strip().lower().startswith('no')]
        blank = [line for a, line in pairs if not a.strip()]
        if noes:
            out.append('reel_check answered no: ' + '; '.join(noes[:5]))
        if blank:
            out.append(f'reel_check has {len(blank)} unanswered lines')
    return out


def enforce(path, job):
    p = problems(path, job)
    if p:
        raise SystemExit('build gate refused ' + _rel(path) + ':\n  - ' + '\n  - '.join(p))
    if not _rel(path).startswith('jobs/test/'):
        print(f'build gate: ok ({job.get("render_lane")} lane, story {job.get("story")})', flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    job = json.load(open(path))
    p = problems(path, job)
    for line in p:
        print('refused:', line)
    if not p:
        print('build gate: ok')
    sys.exit(1 if p else 0)
