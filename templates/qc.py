"""Server quality control, one verdict per Reel (adv-20261110-one-render-per-reel, item H, Mohammad 10 Nov 2026, 17:27
Dubai).

After every server render the workflow writes <name>-qc.json beside the Reel: "pass" or "fail" and every finding in one
list, so the session opens a Reel only when qc says fail and then gets the whole list. Mechanical text faults (a glued
prefix, a flipping % or +) are fixed by the server itself before the render (textrules.fix) and listed here as
`autofixed`; a Latin-first line, length or reading time is never changed by the server.

    python3 templates/qc.py write <job.json> <out.mp4> <qc.json> [--autofix changes.json] [--log render.log]
    python3 templates/qc.py fail <job.json> <qc.json> --log render.log      the verdict of a render that stopped

The findings come from the checks the render already ran (text rules and drawn text, safe zone, first frame and grid
corner, fill, decode and smear, sound against picture, length, pace, credits, burnt-in text, lifeless score): a render
that reaches the commit passed every hard check, so its verdict is pass with the soft notes; a render that stopped is
fail with the error lines of its log. The pass then goes to the director helper once, and on to scheduling.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

NOTE = re.compile(r'^(?:source quality|first frame|cover picture|speech check|design pass|render_job: (?:audio split|lifeless|design pass)'
                  r'|smear check|weak-source path|text check \(estimate\)|pace|length|close|autofocus: profile)[: ].*', re.I)
ERR = re.compile(r'(?:Error|ValueError|SystemExit|refused|FAILED|text check: \d+ problem|  - )', re.I)


def _log_lines(path):
    try:
        return [ln.rstrip('\n') for ln in open(path, encoding='utf-8', errors='replace')]
    except OSError:
        return []


def _times(name):
    try:
        d = json.load(open(os.path.join(HERE, 'assets', 'render-times.json'), encoding='utf-8'))
        rows = [e for e in d if isinstance(e, dict) and str(e.get('name', '')).startswith(name)]
        return rows[-1] if rows else {}
    except (OSError, ValueError):
        return {}


def write(job, out, qc_path, autofix=None, log=None):
    import textrules as TR
    notes = [ln.strip() for ln in _log_lines(log) if NOTE.match(ln.strip())] if log else []
    soft = [f for f in TR.check(job) if f not in TR.hard([f])]
    t = _times(os.path.basename(out))
    d = {'name': job.get('name'), 'out': out, 'verdict': 'pass',
         'at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'findings': [], 'notes': notes[:60] + [f"estimate: {f['where']}: {f['fix']}" for f in soft],
         'autofixed': autofix or [], 'job_sha': os.environ.get('JOB_SHA'),
         'dispatches': int(os.environ['DISPATCHES']) if os.environ.get('DISPATCHES', '').isdigit() else None,
         'source_summary': t.get('source_summary'), 'quality': t.get('quality'), 'final_enc': t.get('final_enc')}
    json.dump(d, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


def fail(job, qc_path, log=None):
    lines = _log_lines(log) if log else []
    found = []
    for ln in lines:
        s = ln.strip()
        if s.startswith('TEXTCHECK_JSON: '):
            try:
                found += [dict(p, check='text') for p in json.loads(s[len('TEXTCHECK_JSON: '):]).get('problems', [])]
            except ValueError:
                pass
        elif ERR.search(s) and len(found) < 80 and not s.startswith('TEXTCHECK_JSON'):
            found.append({'check': 'render', 'detail': s[:400]})
    d = {'name': job.get('name'), 'verdict': 'fail', 'at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'findings': found, 'job_sha': os.environ.get('JOB_SHA')}
    json.dump(d, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    if a[:1] == ['write'] and len(a) >= 4:
        fx = json.load(open(opt('--autofix'), encoding='utf-8')) if opt('--autofix') and os.path.exists(opt('--autofix')) else []
        r = write(json.load(open(a[1], encoding='utf-8')), a[2], a[3], fx, opt('--log'))
        print(f"qc: {r['name']}: {r['verdict']}, {len(r['autofixed'])} autofixed, {len(r['notes'])} notes")
    elif a[:1] == ['fail'] and len(a) >= 3:
        r = fail(json.load(open(a[1], encoding='utf-8')), a[2], opt('--log'))
        print(f"qc: {r['name']}: fail, {len(r['findings'])} findings")
        print('QC_JSON: ' + json.dumps(r, ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
