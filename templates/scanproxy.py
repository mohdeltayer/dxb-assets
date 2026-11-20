"""The footage scan can never hang a render (Mohammad, 20 Nov 2026, after every live job of the day ran 15.5 minutes
and hit the Render step's timeout: the shot gate and its auto-fix rounds re-read frames and scene cuts from Rockstar's
4K 70 Mbps launch-trailer master for 14 minutes with no cap).

Two things, used by render_job.run around the scan (auto_shots, track_from_first_shot, shot_gate):
  proxies(job)      a 720p proxy of every large footage file (taller than 1080 rows or over 25 Mbps), built once under
                    <uploads>/scanproxy/ with the same timeline (timestamps copied, audio stream copied), and a link to
                    every other upload, so the scan reads small files with the same seek times. The render itself
                    always reads the original. A proxy that cannot be built in PROXY_SECS leaves that file as it is.
  capped(fn, job)   runs fn(job) in a forked child with cards.U pointed at the proxy folder, at most CAP_PER_SOURCE
                    seconds per footage source (CAP_MIN to CAP_MAX). When it finishes, the job as the child left it
                    comes back. When it does not, the child's process group is killed, the job is left as it was before
                    the scan, and False comes back: the caller then fills automatic slots from the footage library or
                    evenly spaced shots (render_job.auto_fallback). A scan that does not finish never fails the job.
"""
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time

CAP_PER_SOURCE = 180       # seconds of scan per footage source (release 2026-11-18 r1: the shot read's 3 minutes)
CAP_MIN, CAP_MAX = 180, 540
PROXY_SECS = 150           # building one proxy; past this the scan reads the original
PROXY_H = 720
BIG_H, BIG_MBPS = 1080, 25.0


def _probe(path):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                              'stream=height,bit_rate:format=bit_rate', '-of', 'json', path],
                             capture_output=True, text=True, timeout=30).stdout
        d = json.loads(out or '{}')
        st = (d.get('streams') or [{}])[0]
        br = st.get('bit_rate') or (d.get('format') or {}).get('bit_rate') or 0
        return int(st.get('height') or 0), float(br or 0) / 1e6
    except (subprocess.SubprocessError, ValueError, OSError):
        return 0, 0.0


def _videos(job):
    out = []
    for sh in job.get('shots') or []:
        if isinstance(sh, (list, tuple)) and sh and isinstance(sh[0], str) \
                and not sh[0].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and '-gfx-' not in sh[0]:
            if sh[0] not in out:
                out.append(sh[0])
    for it in job.get('footage') or []:
        f = it.get('file') if isinstance(it, dict) else None
        if f and not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and f not in out:
            out.append(f)
    return out


def big(path):
    h, mbps = _probe(path)
    return h > BIG_H or mbps > BIG_MBPS


def proxies(job, uploads):
    """The proxy folder (a mirror of uploads: proxies for large files, links for the rest), or None."""
    root = os.path.join(uploads.rstrip('/'), 'scanproxy')
    made = []
    try:
        os.makedirs(root, exist_ok=True)
        for name in os.listdir(uploads):
            src, dst = os.path.join(uploads, name), os.path.join(root, name)
            if name == 'scanproxy' or os.path.lexists(dst):
                continue
            os.symlink(src, dst)
        for f in _videos(job):
            src = os.path.join(uploads, f)
            dst = os.path.join(root, f)
            if not os.path.isfile(src) or not big(src):
                continue
            tmp = dst + '.part.mp4'
            t0 = time.time()
            try:
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-copyts', '-i', src, '-map', '0:v:0',
                                '-map', '0:a:0?', '-vf', f'scale=-2:{PROXY_H}', '-c:v', 'libx264', '-preset', 'ultrafast',
                                '-crf', '28', '-c:a', 'copy', tmp], check=True, timeout=PROXY_SECS)
                if os.path.lexists(dst):
                    os.remove(dst)
                os.replace(tmp, dst)
                made.append(f)
                print(f'scanproxy: {f}: {PROXY_H}p proxy for the scan in {time.time() - t0:.0f} s', flush=True)
            except (subprocess.SubprocessError, OSError) as e:
                if os.path.exists(tmp):
                    os.remove(tmp)
                print(f'scanproxy: {f}: no proxy ({type(e).__name__}); the scan reads the original', flush=True)
    except OSError as e:
        print(f'scanproxy: no proxy folder ({e}); the scan reads the originals', flush=True)
        return None
    return root


def cap_for(job):
    n = max(1, len(_videos(job)))
    return max(CAP_MIN, min(CAP_MAX, CAP_PER_SOURCE * n))


def capped(fn, job, uploads=None, secs=None):
    """Run fn(job) in a child with at most `secs` (default cap_for(job)). True when it finished (job updated in place
    from the child's result), False when it was stopped or failed (job untouched)."""
    import cards as C
    secs = secs or cap_for(job)
    uploads = uploads or C.U
    root = proxies(job, uploads) if os.path.isdir(uploads) else None
    fd, res = tempfile.mkstemp(suffix='.json', prefix='scan-')
    os.close(fd)
    pid = os.fork()
    if pid == 0:                                   # child: its own process group, so a timeout takes ffmpeg with it
        code = 1
        try:
            os.setpgid(0, 0)
            if root:
                C.U = root.rstrip('/') + '/'
            fn(job)
            with open(res, 'w', encoding='utf-8') as f:
                json.dump({'job': job}, f, ensure_ascii=False)
            code = 0
        except SystemExit as e:
            print(f'scanproxy: scan stopped: {e}', flush=True)
        except BaseException as e:                 # noqa: BLE001
            print(f'scanproxy: scan error: {type(e).__name__}: {e}', flush=True)
        finally:
            import sys
            sys.stdout.flush()
            os._exit(code)
    t0, done = time.time(), None
    while time.time() - t0 < secs:
        p, status = os.waitpid(pid, os.WNOHANG)
        if p:
            done = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
            break
        time.sleep(0.5)
    if done is None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pid, sig)
            except ProcessLookupError:
                break
            time.sleep(1.0)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        print(f'scanproxy: scan stopped at its cap of {secs:.0f} s; the render goes on with the shots as written '
              '(automatic slots from the footage library or evenly spaced)', flush=True)
    ok = done == 0 and os.path.getsize(res) > 0
    if ok:
        back = json.load(open(res, encoding='utf-8'))['job']
        job.clear()
        job.update(back)
    os.remove(res)
    if root:
        shutil.rmtree(root, ignore_errors=True)
    return ok
