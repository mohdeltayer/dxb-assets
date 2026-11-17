"""Minutes per stage of one render (adv-20261117-server-speed-for-p2 D, Mohammad 17 Nov 2026).

Every render commit, its qc.json and its render-times.json entry carry the minutes per stage, so a slow stage shows up
without opening a log: queue wait, footage fetch, shot read, checks, render, upload. The work order prints the last five.

Where each number comes from:
  queue     the Actions job's started_at minus created_at (render-live: queue_wait_secs; the runner lane has none)
  setup     the workflow's own setup before the render step (setup_min)
  fetch     render_job.run: footage and cards fetched (pipeline.fetch)
  shots     the automatic shot read (pipeline.shots; 0 when the job named its own shots)
  checks    source checks and the shot gate before anything is built, plus reel()'s own check stage
  render    reel() montage, text, audio and outro, the design pass, inserts and the audio split (pipeline.render)
  after     the checks on the finished Reel: decode, smear, fill, strips and sheet (pipeline.after)
  upload    the Publer upload, added by the receipt step (`stagetimes.py upload`)

    python3 templates/stagetimes.py line   <render-time.json>                 one line for the commit message
    python3 templates/stagetimes.py qc     <qc.json> <render-time.json>        writes stage_minutes into qc.json
    python3 templates/stagetimes.py upload <story> <secs> [<qc.json>]         adds upload to the story's last entry
    python3 templates/stagetimes.py last   [n] [render-times.json]            the last n renders, one line each
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIMES = os.path.join(HERE, 'assets', 'render-times.json')
ORDER = ('queue', 'setup', 'fetch', 'shots', 'checks', 'render', 'after', 'upload')


def _m(secs):
    return None if secs is None else round(float(secs) / 60.0, 2)


def minutes(e):
    """Stage minutes of one render-times entry; a stage nobody measured is left out."""
    e = e or {}
    p = e.get('pipeline') or {}
    st = e.get('stages') or {}
    out = {}
    if e.get('queue_wait_secs') is not None:
        out['queue'] = _m(e['queue_wait_secs'])
    if e.get('setup_min') is not None:
        out['setup'] = round(float(e['setup_min']), 2)
    if p:
        out['fetch'] = _m(p.get('fetch'))
        out['shots'] = _m(p.get('shots', 0))
        out['checks'] = _m((p.get('checks') or 0) + (st.get('checks') or 0))
        out['render'] = _m(max(0.0, (p.get('render') or 0) - (st.get('checks') or 0)))
        out['after'] = _m(p.get('after'))
    elif st:                                     # famitsu, breaking and older entries: reel()'s own stages only
        out['checks'] = _m(st.get('checks'))
        out['render'] = _m(sum(v for k, v in st.items() if k != 'checks' and isinstance(v, (int, float))))
    if e.get('upload_secs') is not None:
        out['upload'] = _m(e['upload_secs'])
    if e.get('job_secs') is not None:
        out['job'] = _m(e['job_secs'])
    return {k: v for k, v in out.items() if v is not None}


def line(e):
    m = minutes(e)
    parts = ['%s %.1f' % (k, m[k]) for k in ORDER if k in m]
    if 'job' in m:
        parts.append('job %.1f' % m['job'])
    return 'stages (min): ' + (', '.join(parts) if parts else 'not measured')


def slowest(m):
    best = None
    for k in ORDER:
        if k in m and (best is None or m[k] > m[best]):
            best = k
    return best


def write_qc(qc_path, e):
    try:
        d = json.load(open(qc_path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    d['stage_minutes'] = minutes(e)
    json.dump(d, open(qc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d['stage_minutes']


def add_upload(story, secs, times=TIMES, qc_path=None):
    """The receipt step's upload seconds onto the story's last entry (and its qc.json when given)."""
    try:
        led = json.load(open(times, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    hit = None
    for e in reversed(led):
        if isinstance(e, dict) and e.get('story') == story:
            e['upload_secs'] = round(float(secs), 1)
            hit = e
            break
    if hit is None:
        return None
    json.dump(led, open(times, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if qc_path and os.path.exists(qc_path):
        write_qc(qc_path, hit)
    return minutes(hit)


def last(n=5, times=TIMES):
    """The last n renders that ran through a workflow (they carry `story`), newest last."""
    try:
        led = json.load(open(times, encoding='utf-8')) if isinstance(times, str) else (times or [])
    except (OSError, ValueError):
        return []
    rows = [e for e in led if isinstance(e, dict) and e.get('story')]
    return rows[-n:]


def last_lines(n=5, times=TIMES):
    out = []
    for e in last(n, times):
        m = minutes(e)
        s = slowest(m)
        out.append('%s %s (%s): %s%s' % ((e.get('finished_at') or e.get('at') or '?'), e.get('story'),
                                          e.get('runner') or e.get('lane') or '?', line(e)[len('stages (min): '):],
                                          '; slowest %s' % s if s else ''))
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == 'line' and len(a) == 2:
        print(line(json.load(open(a[1], encoding='utf-8'))))
    elif a[0] == 'qc' and len(a) == 3:
        print(json.dumps(write_qc(a[1], json.load(open(a[2], encoding='utf-8')))))
    elif a[0] == 'upload' and len(a) in (3, 4):
        print(json.dumps(add_upload(a[1], a[2], TIMES, a[3] if len(a) == 4 else None)))
    elif a[0] == 'last':
        n = int(a[1]) if len(a) > 1 else 5
        for ln in last_lines(n, a[2] if len(a) > 2 else TIMES):
            print(ln)
    else:
        raise SystemExit(__doc__)
