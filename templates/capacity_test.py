"""Server capacity test: two renders alone, then together (Mohammad, 19 Nov 2026). Run by server-capacity-test.yml.

    python3 templates/capacity_test.py <job a> <job b> <work dir>

Each render runs `render_job.py run jobs/done/<name>.json` in its own copy of templates, jobs, newsroom and arabic,
with its own fresh DXB_UPLOADS (footage fetched again, picture-pass cache cold), so the solo and the paired runs do the
same work. Phases: A alone, B alone, A and B started together. For every render: wall seconds and the peak memory of
its own process tree (summed RSS, sampled every 2 s); for every phase: the server's peak memory used and peak disk
used (runner_stats.py). Prints `CAPACITY_JSON: {...}` and writes the same to the step summary. Commits nothing.
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.sysconf('SC_PAGE_SIZE')


def tree_rss_mb(pgid):
    total = 0
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            stat = open(f'/proc/{pid}/stat').read()
            fields = stat.rsplit(')', 1)[1].split()
            if int(fields[2]) != pgid:          # field 5 of /proc/pid/stat: process group
                continue
            total += int(open(f'/proc/{pid}/statm').read().split()[1]) * PAGE
        except (OSError, ValueError, IndexError):
            continue
    return total // (1024 * 1024)


def workspace(base, tag):
    ws = os.path.join(base, tag)
    shutil.rmtree(ws, ignore_errors=True)
    os.makedirs(ws)
    for d in ('templates', 'jobs', 'newsroom', 'arabic'):
        if os.path.isdir(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(ws, d), symlinks=True)
    os.makedirs(os.path.join(ws, 'uploads'))
    return ws


def launch(base, tag, name):
    ws = workspace(base, tag)
    env = dict(os.environ, DXB_UPLOADS=os.path.join(ws, 'uploads'))
    log = open(os.path.join(base, f'{tag}.log'), 'w')
    p = subprocess.Popen([sys.executable, 'templates/render_job.py', 'run', f'jobs/done/{name}.json'], cwd=ws, env=env,
                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    return {'tag': tag, 'job': name, 'p': p, 't0': time.time(), 'peak_mb': 0, 'log': log.name}


def phase(base, label, names):
    stats = os.path.join(base, f'{label}-stats.json')
    subprocess.run([sys.executable, os.path.join(HERE, 'runner_stats.py'), 'start', stats], cwd=base)
    runs = [launch(base, f'{label}-{i}', n) for i, n in enumerate(names)]
    done = threading.Event()

    def sample():
        while not done.is_set():
            for r in runs:
                if r['p'].poll() is None:
                    r['peak_mb'] = max(r['peak_mb'], tree_rss_mb(r['p'].pid))
            time.sleep(2)
    th = threading.Thread(target=sample, daemon=True)
    th.start()
    for r in runs:
        r['rc'] = r['p'].wait()
        r['secs'] = round(time.time() - r['t0'], 1)
    done.set()
    th.join()
    subprocess.run([sys.executable, os.path.join(HERE, 'runner_stats.py'), 'stop', stats], cwd=base)
    st = json.load(open(stats)) if os.path.exists(stats) else {}
    out = {'phase': label, 'renders': [{'job': r['job'], 'secs': r['secs'], 'peak_tree_mb': r['peak_mb'], 'rc': r['rc']}
                                       for r in runs],
           'server_peak_mem_mb': st.get('peak_mem_mb'), 'server_mem_start_mb': st.get('mem_start_mb'),
           'mem_total_mb': st.get('mem_total_mb'), 'server_peak_disk_mb': st.get('peak_disk_mb'),
           'disk_start_mb': st.get('disk_start_mb'), 'min_disk_free_mb': st.get('min_disk_free_mb')}
    for r in runs:
        if r['rc'] != 0:
            print(f'--- {r["tag"]} ({r["job"]}) failed, last lines:')
            print(''.join(open(r['log']).readlines()[-25:]))
    print(json.dumps(out), flush=True)
    for r in runs:                              # free the disk before the next phase
        shutil.rmtree(os.path.join(base, r['tag']), ignore_errors=True)
    return out


def main(a, b, base):
    os.makedirs(base, exist_ok=True)
    res = [phase(base, 'solo-a', [a]), phase(base, 'solo-b', [b]), phase(base, 'pair', [a, b])]
    solo = {r['renders'][0]['job']: r['renders'][0]['secs'] for r in res[:2]}
    ratio = {x['job']: round(x['secs'] / solo[x['job']], 2) for x in res[2]['renders'] if solo.get(x['job'])}
    summary = {'cores': os.cpu_count(), 'phases': res, 'pair_over_solo': ratio,
               'pass_1_5x': all(v <= 1.5 for v in ratio.values()) and all(x['rc'] == 0 for p in res for x in p['renders'])}
    print('CAPACITY_JSON: ' + json.dumps(summary), flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write('## Server capacity test\n\n| phase | job | minutes | tree peak MB | server peak mem MB | server peak disk MB |\n'
                    '|---|---|---|---|---|---|\n')
            for p in res:
                for x in p['renders']:
                    f.write(f"| {p['phase']} | {x['job']} | {x['secs'] / 60:.2f} | {x['peak_tree_mb']} | "
                            f"{p['server_peak_mem_mb']} of {p['mem_total_mb']} | {p['server_peak_disk_mb']} |\n")
            f.write(f"\npaired over solo: {ratio}; within 1.5x: {summary['pass_1_5x']}\n")
    return 0 if summary['pass_1_5x'] else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:4]))
