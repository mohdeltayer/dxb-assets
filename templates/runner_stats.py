"""Peak memory and disk during the render step (render runner, 26 Oct 2026, safeguard 1, "Add all five").

A render that dies on the runner leaves no trace of how close it came to the VM's limits (7 GB of memory, a
shared disk). render.yml starts this sampler before `render_job.py run` and stops it after, and the figures go
into that run's render-times.json entry: `peak_mem_mb` (used = total less available, from /proc/meminfo),
`mem_total_mb`, `mem_start_mb`, `peak_disk_mb` (used on the workspace's filesystem), `disk_start_mb`,
`disk_total_mb`, `min_disk_free_mb`, and `peak_tmp_mb` when /tmp is a different filesystem. A run that fails
still prints the line (render.yml stops the sampler on exit), so the log shows it.

Never fails a job: every command exits 0, a sample that cannot be read is skipped, and the sampler ends itself
after LIFE seconds if nobody stops it.

    python3 runner_stats.py start <stats.json>                 # detached sampler, every EVERY seconds
    python3 runner_stats.py stop  <stats.json>                 # ends it, prints one line (idempotent)
    python3 runner_stats.py merge <stats.json> <entry.json>    # adds the figures to a render-times entry
"""
import json, os, shutil, signal, subprocess, sys, tempfile, time

EVERY = 2.0
LIFE = 25 * 60             # the render step is cut at 15 minutes; this only catches a sampler nobody stopped
MB = 1024 * 1024
KEYS = ('mem_total_mb', 'mem_start_mb', 'peak_mem_mb', 'disk_total_mb', 'disk_start_mb', 'peak_disk_mb',
        'min_disk_free_mb', 'peak_tmp_mb')


def _mem():
    m = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k, _, v = line.partition(':')
            m[k] = int(v.split()[0])
    return (m['MemTotal'] - m['MemAvailable']) // 1024, m['MemTotal'] // 1024


def _disk(path):
    u = shutil.disk_usage(path)
    return u.used // MB, u.total // MB, u.free // MB


def _save(path, st):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(st, f)
    os.replace(tmp, path)


def loop(path):
    stop = []
    signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
    ws, tmp = os.getcwd(), tempfile.gettempdir()
    try:
        own_tmp = os.stat(ws).st_dev != os.stat(tmp).st_dev
    except OSError:
        own_tmp = False
    st = {}
    end = time.time() + LIFE
    while not stop and time.time() < end:
        try:
            used, total = _mem()
            st['mem_total_mb'] = total
            st.setdefault('mem_start_mb', used)
            st['peak_mem_mb'] = max(st.get('peak_mem_mb', 0), used)
        except Exception:
            pass
        try:
            used, total, free = _disk(ws)
            st['disk_total_mb'] = total
            st.setdefault('disk_start_mb', used)
            st['peak_disk_mb'] = max(st.get('peak_disk_mb', 0), used)
            st['min_disk_free_mb'] = min(st.get('min_disk_free_mb', free), free)
            if own_tmp:
                st['peak_tmp_mb'] = max(st.get('peak_tmp_mb', 0), _disk(tmp)[0])
        except Exception:
            pass
        try:
            _save(path, st)
        except Exception:
            pass
        time.sleep(EVERY)
    try:
        _save(path, st)
    except Exception:
        pass


def start(path):
    for p in (path, path + '.pid'):
        if os.path.exists(p):
            os.remove(p)
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), 'loop', path], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    with open(path + '.pid', 'w') as f:
        f.write(str(p.pid))


def stop(path):
    pf = path + '.pid'
    if not os.path.exists(pf):
        return
    pid = int(open(pf).read().strip())
    os.remove(pf)
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(30):                      # the sampler writes its last figures, then exits
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except OSError:
                break
    except OSError:
        pass
    st = json.load(open(path))
    print('runner_stats: peak memory %s of %s MB, peak disk %s of %s MB (started at %s, %s MB free at the lowest)%s' % (
        st.get('peak_mem_mb', '?'), st.get('mem_total_mb', '?'), st.get('peak_disk_mb', '?'), st.get('disk_total_mb', '?'),
        st.get('disk_start_mb', '?'), st.get('min_disk_free_mb', '?'),
        f", /tmp peak {st['peak_tmp_mb']} MB" if 'peak_tmp_mb' in st else ''), flush=True)


def merge(path, entry):
    st = json.load(open(path))
    e = json.load(open(entry))
    e.update({k: st[k] for k in KEYS if k in st})
    if os.environ.get('RENDER_RETRY') == '1':    # the automatic retry of a lost runner (render.yml, retry job)
        e['retry'] = True
    json.dump(e, open(entry, 'w'))


if __name__ == '__main__':
    try:
        cmd = sys.argv[1]
        if cmd == 'loop':
            loop(sys.argv[2])
        elif cmd == 'start':
            start(sys.argv[2])
        elif cmd == 'stop':
            stop(sys.argv[2])
        elif cmd == 'merge':
            merge(sys.argv[2], sys.argv[3])
        else:
            print('usage: runner_stats.py start|stop <stats.json> | merge <stats.json> <entry.json>')
    except Exception as e:                       # sampling must never fail a render
        print(f'runner_stats: {e}', flush=True)
    sys.exit(0)
