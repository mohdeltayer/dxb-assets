#!/usr/bin/env python3
"""Readiness check for the dxb-render server (run by .github/workflows/server-check.yml; dispatch only).

Each subcommand is one item of the check. It records PASS / FAIL / WARN / REVIEW / INFO to $SC_DIR/results.jsonl
and never raises, so one failure does not hide the rest; `summary` turns the lines into a table for the job summary.
Nothing here commits, pushes or uploads to Publer, and no token or font ever lands in the output.

    server_check.py init | fonts | imports | ffmpeg | hyperframes | split | tesseract | fetch | ldd | host |
                    render <rev> | summary
Environment (set by the workflow): RUNNER_TEMP, SC_DIR, DXB_CACHE, DUBAI_FONTS, DXB_UPLOADS, YOLO_WEIGHTS,
COCKTAIL_DIR, FONTS_TOKEN (fonts step only).
"""
import ast, base64, glob, json, os, re, shutil, subprocess, sys, tempfile, time, traceback, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATES = os.path.join(ROOT, 'templates')
TMP = os.environ.get('RUNNER_TEMP') or tempfile.gettempdir()
SC = os.environ.get('SC_DIR') or os.path.join(TMP, 'sc')
CACHE = os.environ.get('DXB_CACHE', '/var/cache/dxb-render')
RESULTS = os.path.join(SC, 'results.jsonl')
REPO = 'mohdeltayer/dxb-assets'
HF_VERSION = '0.8.143'
COCKTAIL_SHA = '19b3de827ebc4bfb014570cf92dd32b4ee3b6921'
ITEMS = {'imports': 'a. Python packages', 'ffmpeg': 'b. ffmpeg encoders and filters', 'hyperframes': 'c. HyperFrames and Arabic card',
         'split': 'd. Cocktail Fork audio split', 'tesseract': 'e. tesseract', 'fetch': 'f. fetch dxb-assets and dxb-fonts',
         'ldd': 'g. shared libraries (ldd)', 'host': 'h. host, user, permissions', 'render': 'i. full test render'}


def rec(item, status, summary, detail=''):
    os.makedirs(SC, exist_ok=True)
    with open(RESULTS, 'a') as f:
        f.write(json.dumps({'item': item, 'status': status, 'summary': summary, 'detail': detail[-6000:]}, ensure_ascii=False) + '\n')
    print(f'[{status}] {ITEMS.get(item, item)}: {summary}', flush=True)
    if detail:
        print(detail[-3000:], flush=True)


def guarded(item):
    def deco(fn):
        def run(*a):
            t = time.time()
            try:
                fn(*a)
            except Exception as e:          # one failing item never hides the rest
                rec(item, 'FAIL', f'{type(e).__name__}: {str(e)[:200]}', traceback.format_exc())
            print(f'({item}: {time.time() - t:.1f} s)', flush=True)
        return run
    return deco


def sh(cmd, timeout=120, env=None, cwd=None, input=None):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd, input=input)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def gh_env(token):
    """git credentials through the environment (never in a URL or a command line)."""
    b = base64.b64encode(f'x-access-token:{token}'.encode()).decode()
    return dict(os.environ, GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                GIT_CONFIG_VALUE_0=f'AUTHORIZATION: basic {b}', GIT_TERMINAL_PROMPT='0')


# ------------------------------------------------------------------------------------------------ init / fonts
def init():
    shutil.rmtree(SC, ignore_errors=True)
    os.makedirs(os.path.join(SC, 'artifacts'), exist_ok=True)
    print('check dir ready')


@guarded('fetch')
def fonts():
    """dxb-fonts with FONTS_TOKEN into DUBAI_FONTS (a temp folder), as render.yml does; the clone is deleted at once."""
    token, dst = os.environ.get('FONTS_TOKEN', ''), os.environ['DUBAI_FONTS']
    if not token:
        raise RuntimeError('FONTS_TOKEN is not available to this run')
    clone = os.path.join(TMP, 'dxb-fonts-check')
    shutil.rmtree(clone, ignore_errors=True)
    t = time.time()
    rc, out = sh(['git', 'clone', '-q', '--depth', '1', 'https://github.com/mohdeltayer/dxb-fonts.git', clone], 120, env=gh_env(token))
    if rc:
        raise RuntimeError('clone of dxb-fonts failed: ' + out.replace(token, '***')[-200:])
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(os.path.join(clone, 'dubai.zip')) as z:
        for n in z.namelist():
            if n.endswith('.ttf'):
                with open(os.path.join(dst, os.path.basename(n)), 'wb') as f:
                    f.write(z.read(n))
    shutil.rmtree(clone, ignore_errors=True)
    have = sorted(os.listdir(dst))
    miss = [w for w in ('Light', 'Regular', 'Medium', 'Bold') if f'Dubai-{w}.ttf' not in have]
    rec('fetch', 'FAIL' if miss else 'PASS', f'dxb-fonts cloned with FONTS_TOKEN in {time.time() - t:.1f} s; fonts in the job temp folder: {len(have)} files' +
        (f'; MISSING {miss}' if miss else ''), '')


@guarded('fetch')
def fetch():
    """dxb-assets: ls-remote and a sparse partial fetch with the runner's own access (the repo is public)."""
    t = time.time()
    rc, out = sh(['git', 'ls-remote', f'https://github.com/{REPO}', 'HEAD'], 60)
    head = out.split()[0][:8] if rc == 0 and out.strip() else None
    d = os.path.join(TMP, 'fetch-check')
    shutil.rmtree(d, ignore_errors=True)
    rc2, out2 = sh(['git', 'clone', '-q', '--depth', '1', '--filter=blob:none', '--sparse', f'https://github.com/{REPO}', d], 180)
    n = 0
    if rc2 == 0:
        sh(['git', '-C', d, 'sparse-checkout', 'set', 'templates/assets'], 60)
        n = sum(len(f) for _, _, f in os.walk(os.path.join(d, 'templates', 'assets')))
    shutil.rmtree(d, ignore_errors=True)
    ok = head and rc2 == 0 and n > 0
    rec('fetch', 'PASS' if ok else 'FAIL', f'dxb-assets ls-remote HEAD {head or "failed"}, sparse partial clone {"ok" if rc2 == 0 else "failed"} ({n} files in templates/assets) in {time.time() - t:.1f} s',
        '' if ok else out2[-300:])


# ------------------------------------------------------------------------------------------------ a. imports
REQUIRED = ['PIL', 'numpy', 'soundfile', 'pedalboard', 'ultralytics', 'cv2', 'torch', 'torchvision', 'pyloudnorm']


def _closure():
    """Third-party top-level modules imported by render_job.py and every template module it reaches (lazy imports too)."""
    local = {os.path.splitext(f)[0] for f in os.listdir(TEMPLATES) if f.endswith('.py')}
    kit = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(TEMPLATES, 'hyperframes', 'kit')) if f.endswith('.py')} if os.path.isdir(os.path.join(TEMPLATES, 'hyperframes', 'kit')) else set()
    seen, todo, third = set(), ['render_job', 'runner_stats', 'decodecheck', 'tracksplit', 'designpass', 'hfinsert'], {}
    while todo:
        m = todo.pop()
        if m in seen or m not in local:
            continue
        seen.add(m)
        try:
            tree = ast.parse(open(os.path.join(TEMPLATES, m + '.py'), encoding='utf8').read())
        except Exception:
            continue
        for n in ast.walk(tree):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module] if isinstance(n, ast.ImportFrom) and n.module and not n.level else []
            for full in names:
                top = full.split('.')[0]
                if top in local:
                    todo.append(top)
                elif top in kit:
                    pass
                elif top not in sys.stdlib_module_names:
                    third.setdefault(top, set()).add(m)
    return sorted(seen), third


@guarded('imports')
def imports():
    import importlib, importlib.metadata as md
    mods, third = _closure()
    rows, missing_req, missing_other = [], [], []
    dist = md.packages_distributions()
    for name in sorted(set(REQUIRED) | set(third) | {'mediapipe'}):   # mediapipe: reel.py's face model child process, not installed by render.yml either
        if name in ('mrx',):
            continue
        try:
            m = importlib.import_module(name)
            ver = getattr(m, '__version__', None) or next((md.version(d) for d in dist.get(name, [])), '?')
            rows.append(f'ok      {name} {ver}   (used by {", ".join(sorted(third.get(name, {"render.yml list"})))})')
        except Exception as e:
            first = (str(e).splitlines() or [''])[0][:160]
            rows.append(f'MISSING {name}: {type(e).__name__}: {first}   (used by {", ".join(sorted(third.get(name, {"render.yml list"})))})')
            (missing_req if name in REQUIRED else missing_other).append(name)
    # functional smoke: the pair has to agree (nms), pedalboard has to run, YOLO has to predict
    smoke = []
    try:
        import torch, torchvision
        torchvision.ops.nms(torch.tensor([[0., 0, 10, 10], [1, 1, 11, 11]]), torch.tensor([.9, .8]), .5)
        smoke.append(f'torch {torch.__version__} + torchvision {torchvision.__version__}: nms ok, {torch.get_num_threads()} threads')
    except Exception as e:
        smoke.append(f'torch/torchvision smoke FAILED: {e}')
        missing_req.append('torch-smoke')
    try:
        import numpy as np, pedalboard
        pedalboard.Pedalboard([pedalboard.Reverb()])(np.zeros((2, 4410), np.float32), 44100)
        smoke.append('pedalboard: processes audio ok')
    except Exception as e:
        smoke.append(f'pedalboard smoke FAILED: {e}')
        missing_req.append('pedalboard-smoke')
    try:
        import numpy as np
        from ultralytics import YOLO
        w = os.environ.get('YOLO_WEIGHTS', os.path.join(CACHE, 'models', 'yolov8n.pt'))
        YOLO(w).predict(np.zeros((360, 640, 3), np.uint8), imgsz=640, device='cpu', verbose=False)
        smoke.append(f'YOLO (autofocus): weights {os.path.getsize(w) // 1024} KB load and predict ok')
    except Exception as e:
        smoke.append(f'YOLO smoke FAILED: {str(e)[:200]}')
        missing_req.append('yolo-smoke')
    detail = '\n'.join(rows + [''] + smoke + ['', 'template modules reached from render_job.py: ' + ', '.join(mods)])
    if missing_req:
        rec('imports', 'FAIL', f'missing or broken: {", ".join(missing_req)}', detail)
    elif missing_other:
        rec('imports', 'WARN', f'render.yml set all ok; optional modules absent (also absent on the GitHub runner): {", ".join(missing_other)}', detail)
    else:
        rec('imports', 'PASS', f'{len(rows)} packages import; torch/torchvision, pedalboard and YOLO smoke ok', detail)


# ------------------------------------------------------------------------------------------------ b. ffmpeg
ENCODERS = ['libx264', 'aac', 'pcm_s16le', 'pcm_f32le', 'libmp3lame']
FILTERS = ('zoompan cas perspective scale crop cropdetect subtitles drawtext overlay xfade acrossfade amix adelay alimiter loudnorm hqdn3d '
           'unsharp eq noise gblur boxblur colorchannelmixer tile select concat fade afade trim atrim setpts asetpts fps pad format volume '
           'aformat anullsrc color split apad aresample ebur128 blackdetect freezedetect silencedetect astats').split()


@guarded('ffmpeg')
def ffmpeg():
    out = []
    for b in ('ffmpeg', 'ffprobe'):
        rc, v = sh([b, '-version'])
        out.append(v.splitlines()[0] if rc == 0 else f'{b} MISSING')
    conf = sh(['ffmpeg', '-version'])[1]
    libs = {l: f'--enable-{l}' in conf for l in ('libx264', 'libass', 'libfreetype', 'libfontconfig', 'libmp3lame', 'gpl')}
    enc = sh(['ffmpeg', '-hide_banner', '-encoders'])[1]
    flt = sh(['ffmpeg', '-hide_banner', '-filters'])[1]
    mux = sh(['ffmpeg', '-hide_banner', '-muxers'])[1]
    dem = sh(['ffmpeg', '-hide_banner', '-demuxers'])[1]
    pro = sh(['ffmpeg', '-hide_banner', '-protocols'])[1]
    miss = []
    lines = []
    for e in ENCODERS:
        ok = bool(re.search(rf'\s{e}\s', enc))
        lines.append(f'{"present" if ok else "MISSING"}  encoder {e}')
        if not ok:
            miss.append('encoder ' + e)
    for f in FILTERS:
        ok = bool(re.search(rf'\s{f}\s', flt))
        lines.append(f'{"present" if ok else "MISSING"}  filter {f}')
        if not ok:
            miss.append('filter ' + f)
    for kind, text, names in (('muxer', mux, ['mp4', 'matroska', 'wav', 'null']), ('demuxer', dem, ['mov', 'matroska', 'hls', 'wav', 'image2']), ('protocol', pro, ['https', 'file', 'pipe'])):
        for n in names:
            ok = bool(re.search(rf'\s{n}\b', text))
            lines.append(f'{"present" if ok else "MISSING"}  {kind} {n}')
            if not ok:
                miss.append(f'{kind} {n}')
    lines.append('build: ' + ', '.join(f'{k}={"yes" if v else "NO"}' for k, v in libs.items()))
    # a real chain through the filters the Reels lean on, encoded with libx264 + aac like the final pass
    out_mp4 = os.path.join(TMP, 'ffmpeg-smoke.mp4')
    vf = ("zoompan=z='min(zoom+0.0015,1.1)':d=1:s=540x960:fps=30,scale=1080:1920:flags=lanczos,cas=0.3,unsharp=5:5:0.4,hqdn3d=2:1:3:3,"
          "eq=contrast=1.05,noise=alls=3:allf=t,gblur=sigma=1,perspective=x0=0:y0=0:x1=W:y1=0:x2=0:y2=H:x3=W:y3=H,format=yuv420p")
    rc, o = sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=540x960:rate=30:duration=1', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
                '-vf', vf, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st=0.5:d=0.5', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', '-shortest', out_mp4], 120)
    chain_ok = rc == 0 and os.path.exists(out_mp4)
    lines.append('filter chain smoke (zoompan, lanczos, cas, unsharp, hqdn3d, eq, noise, gblur, perspective, loudnorm, libx264, aac): ' + ('ok' if chain_ok else 'FAILED ' + o[-300:]))
    # subtitles / drawtext need libass and freetype; an actual drawtext run proves the font path
    font = next(iter(glob.glob('/usr/share/fonts/truetype/**/*.ttf', recursive=True)), None)
    if font:
        rc, o = sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:d=0.2', '-vf', f"drawtext=fontfile={font}:text=test:fontsize=40:fontcolor=white", '-f', 'null', '-'], 60)
        lines.append('drawtext smoke: ' + ('ok' if rc == 0 else 'FAILED ' + o[-200:]))
        chain_ok = chain_ok and rc == 0
    else:
        lines.append('drawtext smoke: no system font found (fonts-liberation / noto-core expected); skipped')
    for f in (out_mp4,):
        if os.path.exists(f):
            os.remove(f)
    detail = '\n'.join(out + lines)
    if miss or not chain_ok or not libs['libx264'] or not libs['libass']:
        rec('ffmpeg', 'FAIL', f'missing: {", ".join(miss) or "none"}; chain {"ok" if chain_ok else "FAILED"}; libass {libs["libass"]}', detail)
    else:
        rec('ffmpeg', 'PASS', f'{out[0].split(" Copyright")[0]}: {len(ENCODERS)} encoders, {len(FILTERS)} filters, muxers, hls and https present; chain ok', detail)


# ------------------------------------------------------------------------------------------------ c. HyperFrames
CARD = """<!doctype html>
<html lang="ar" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face { font-family: "Dubai"; font-weight: 400; src: url("fonts/Dubai-Regular.ttf"); }
@font-face { font-family: "Dubai"; font-weight: 700; src: url("fonts/Dubai-Bold.ttf"); }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #141332; }
#root { position: relative; width: 1080px; height: 1920px; font-family: "Dubai", "DejaVu Sans", sans-serif; direction: rtl; color: #f4f3ff; }
.clip { position: absolute; right: 96px; width: 888px; text-align: right; }
#a { top: 500px; font-weight: 700; font-size: 84px; line-height: 1.3; }
#b { top: 820px; font-weight: 400; font-size: 56px; line-height: 1.4; color: #c9c8e6; }
#c { top: 1050px; font-weight: 700; font-size: 70px; }
#bar { top: 460px; height: 10px; background: #28b6f6; }
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1.5" data-width="1080" data-height="1920">
<div id="bar" class="clip" data-start="0" data-duration="1.5"></div>
<div id="a" class="clip" data-start="0" data-duration="1.5">هدية مجانية اليوم<br>للاعبي Helldivers 2</div>
<div id="b" class="clip" data-start="0" data-duration="1.5">ديجيتال لاونج | أخبار الألعاب<br>تصل فجر الثلاثاء بتوقيت الإمارات</div>
<div id="c" class="clip" data-start="0" data-duration="1.5">السعر 199 درهم، PS5 وXbox</div>
</div>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
tl.fromTo("#bar", { opacity: 0 }, { opacity: 1, duration: 0.2 }, 0);
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>
"""


@guarded('hyperframes')
def hyperframes():
    hf = os.path.join(CACHE, 'hf')
    cli = os.path.join(hf, 'node_modules', '.bin', 'hyperframes')
    notes = []
    if not os.path.exists(cli):
        os.makedirs(hf, exist_ok=True)
        if not os.path.exists(os.path.join(hf, 'package.json')):
            open(os.path.join(hf, 'package.json'), 'w').write('{"name":"dxb-hf","private":true}')
        rc, o = sh(['npm', 'i', '-s', '--no-audit', '--no-fund', f'hyperframes@{HF_VERSION}'], 300, cwd=hf)
        notes.append(f'npm install: rc {rc} {o[-200:]}')
    try:
        ver = json.load(open(os.path.join(hf, 'node_modules', 'hyperframes', 'package.json')))['version']
    except Exception:
        ver = None
    notes.append(f'hyperframes version {ver} (pinned {HF_VERSION})')
    t = time.time()
    rc, o = sh([cli, 'browser', 'ensure'], 360)
    notes.append(f'browser ensure rc {rc} in {time.time() - t:.0f} s: {o.strip()[-300:]}')
    if ver != HF_VERSION or rc:
        rec('hyperframes', 'FAIL', f'version {ver}, browser ensure rc {rc}', '\n'.join(notes))
        return
    work = tempfile.mkdtemp(prefix='hfcard-', dir=TMP)
    try:
        os.makedirs(os.path.join(work, 'fonts'))
        fdir = os.environ.get('DUBAI_FONTS', '')
        for w in ('Regular', 'Bold'):
            shutil.copy(os.path.join(fdir, f'Dubai-{w}.ttf'), os.path.join(work, 'fonts'))
        open(os.path.join(work, 'index.html'), 'w', encoding='utf8').write(CARD)
        json.dump({'id': 'card', 'name': 'card'}, open(os.path.join(work, 'meta.json'), 'w'))
        t = time.time()
        rc, o = sh([cli, 'render', work, '-o', os.path.join(work, 'card.mp4'), '-q', 'delivery', '-f', '30', '--quiet'], 300)
        rsecs = time.time() - t
        notes.append(f'render rc {rc} in {rsecs:.0f} s {o.strip()[-300:]}')
        if rc or not os.path.exists(os.path.join(work, 'card.mp4')):
            rec('hyperframes', 'FAIL', f'test card render failed (rc {rc})', '\n'.join(notes))
            return
        png = os.path.join(SC, 'artifacts', 'hf-test-card.png')
        sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', '1.0', '-i', os.path.join(work, 'card.mp4'), '-frames:v', '1', png], 60)
    finally:
        shutil.rmtree(work, ignore_errors=True)         # the fonts copied for the card go with it
    from PIL import Image
    im = Image.open(png).convert('RGB')
    px = im.load()
    w, h = im.size
    bg = px[5, 5]
    ink = [(x, y) for y in range(0, h, 3) for x in range(0, w, 3) if sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 200]
    bbox = (min(x for x, _ in ink), min(y for _, y in ink), max(x for x, _ in ink), max(y for _, y in ink)) if ink else None
    ocr = 'tesseract not available'
    rc, langs = sh(['tesseract', '--list-langs'])
    lang = 'ara+eng' if re.search(r'^ara$', langs, re.M) else 'eng'
    rc, o = sh(['tesseract', png, '-', '-l', lang, '--psm', '6'], 120)
    ocr = f'tesseract -l {lang}: ' + ' | '.join(l for l in o.splitlines() if l.strip())[:300]
    notes.append(f'frame {w}x{h}, ink samples {len(ink)}, ink bbox {bbox}')
    notes.append(ocr)
    ok = bool(ink) and bbox and (bbox[3] - bbox[1]) > 300
    rec('hyperframes', 'PASS' if ok else 'FAIL', f'{HF_VERSION} installed, browser ready, Arabic Dubai test card rendered in {rsecs:.0f} s, frame saved; ink spans {(bbox[3] - bbox[1]) if bbox else 0} px tall ({ocr[:80]})', '\n'.join(notes))
    rec('hyperframes', 'REVIEW', 'right-to-left shaping (joined letters, Latin names and digits in order) needs a human look at the workflow artifact server-check-hf-test-card', '')


# ------------------------------------------------------------------------------------------------ d. audio split
def repo_file(path, dst):
    """A committed file (live/...): from the checkout if present, else read from the commit (partial clone fetches the blob)."""
    src = os.path.join(ROOT, path)
    if os.path.exists(src):
        shutil.copy(src, dst)
    else:
        with open(dst, 'wb') as f:
            subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + path], stdout=f, check=True, timeout=300)


@guarded('split')
def split():
    cdir = os.environ.get('COCKTAIL_DIR', '')
    if not cdir or not os.path.exists(os.path.join(cdir, 'mrx.py')):
        raise RuntimeError('COCKTAIL_DIR not set or mrx.py absent (the install step failed)')
    d = tempfile.mkdtemp(prefix='split-', dir=TMP)
    try:
        mp4 = os.path.join(d, 'hd2-launch.mp4')
        t = time.time()
        repo_file('live/2026-10-26/hd2-launch.mp4', mp4)
        fetch_s = time.time() - t
        sys.path.insert(0, TEMPLATES)
        os.environ.pop('SPLIT_CACHE', None)               # a cold run: no stem cache
        import numpy as np, tracksplit as TS
        t = time.time()
        sep = TS._Cocktail()
        load_s = time.time() - t
        dur = TS._dur(mp4)
        start = max(0.0, min(20.0, dur - 10.0))
        a = TS._audio(mp4, start, 10.0)
        t = time.time()
        st = sep(a)
        sep_s = time.time() - t
        e = {k: TS._energy(v) for k, v in st.items()}
        tot = sum(e.values()) + 1e-12
        t = time.time()
        again = sep(st['music'])
        ea = {k: TS._energy(v) for k, v in again.items()}
        leak = 100 * (ea['sfx'] + ea['speech']) / (sum(ea.values()) + 1e-12)
        lines = [f'clip: hd2-launch.mp4 {start:.0f} s to {start + 10:.0f} s of {dur:.0f} s (blob fetch {fetch_s:.1f} s)',
                 f'model load {load_s:.1f} s, separation of 10 s of audio {sep_s:.1f} s, second pass (music stem) {time.time() - t:.1f} s, torch threads {sep.torch.get_num_threads()}',
                 'input level %.1f dBFS(rms)' % TS._db(a)] + \
                ['stem %-6s %6.1f dB   %4.1f %% of energy' % (k, TS._db(v), 100 * e[k] / tot) for k, v in st.items()] + \
                [f'leftover effects+speech in the music stem on a second pass: {leak:.1f} % (limit {TS.LEAK_MAX} %), music share {100 * e["music"] / tot:.1f} % (min {TS.MUSIC_MIN} %)']
        clean = leak <= TS.LEAK_MAX and 100 * e['music'] / tot >= TS.MUSIC_MIN
        rec('split', 'PASS', f'10 s separated in {sep_s:.1f} s (model load {load_s:.1f} s); music {100 * e["music"] / tot:.0f} %, leftover {leak:.1f} %'
            + ('' if clean else ' (this stretch would not pass the cleanliness gate; the machine is fine)'), '\n'.join(lines))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ e. tesseract
@guarded('tesseract')
def tesseract():
    from PIL import Image, ImageDraw, ImageFont
    rc, v = sh(['tesseract', '--version'])
    langs = [l.strip() for l in sh(['tesseract', '--list-langs'])[1].splitlines()[1:] if l.strip()]
    d = tempfile.mkdtemp(prefix='tess-', dir=TMP)
    try:
        font = None
        for p in [os.path.join(os.environ.get('DUBAI_FONTS', ''), 'Dubai-Bold.ttf')] + glob.glob('/usr/share/fonts/**/*.ttf', recursive=True)[:1]:
            if os.path.exists(p):
                font = ImageFont.truetype(p, 90)
                break
        im = Image.new('RGB', (1400, 300), 'black')
        ImageDraw.Draw(im).text((40, 90), 'HELLDIVERS 2 LIBERTY DAY', fill='white', font=font)
        a = os.path.join(d, 'a.png')
        im.save(a)
        rc, o = sh(['tesseract', a, '-', '--psm', '7'])
        ok_synth = 'LIBERTY' in o.upper()
        mp4 = os.path.join(d, 'f.mp4')
        repo_file('live/2026-10-26/hd2-launch.mp4', mp4)
        fr = os.path.join(d, 'f.png')
        sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', '5', '-i', mp4, '-frames:v', '1', fr], 60)
        rc2, o2 = sh(['tesseract', fr, '-', '--psm', '11'])
        words = [w for w in re.findall(r'[A-Za-z]{3,}', o2)]
        rec('tesseract', 'PASS' if ok_synth and rc == 0 else 'FAIL', f'{v.splitlines()[0]}; langs {",".join(langs)}; synthetic frame read "{o.strip()}"; trailer frame at 5 s: {len(words)} words',
            'ara traineddata ' + ('present' if 'ara' in langs else 'ABSENT (tesseract-ocr-ara not installed; Arabic OCR checks are skipped)') + '\nsample words: ' + ' '.join(words[:20]))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ g. ldd
PKG = {
    'libatomic.so.1': 'libatomic1', 'libgomp.so.1': 'libgomp1', 'libsndfile.so.1': 'libsndfile1', 'libGL.so.1': 'libgl1', 'libGLX.so.0': 'libglx0',
    'libGLdispatch.so.0': 'libglvnd0', 'libEGL.so.1': 'libegl1', 'libGLESv2.so.2': 'libgles2', 'libglib-2.0.so.0': 'libglib2.0-0t64',
    'libgthread-2.0.so.0': 'libglib2.0-0t64', 'libgobject-2.0.so.0': 'libglib2.0-0t64', 'libgio-2.0.so.0': 'libglib2.0-0t64',
    'libSM.so.6': 'libsm6', 'libICE.so.6': 'libice6', 'libXext.so.6': 'libxext6', 'libXrender.so.1': 'libxrender1', 'libX11.so.6': 'libx11-6',
    'libxcb.so.1': 'libxcb1', 'libstdc++.so.6': 'libstdc++6', 'libgfortran.so.5': 'libgfortran5', 'libquadmath.so.0': 'libquadmath0',
    'libnss3.so': 'libnss3', 'libnssutil3.so': 'libnss3', 'libsmime3.so': 'libnss3', 'libnspr4.so': 'libnspr4', 'libatk-1.0.so.0': 'libatk1.0-0t64',
    'libatk-bridge-2.0.so.0': 'libatk-bridge2.0-0t64', 'libatspi.so.0': 'libatspi2.0-0t64', 'libcups.so.2': 'libcups2t64', 'libdrm.so.2': 'libdrm2',
    'libxkbcommon.so.0': 'libxkbcommon0', 'libXcomposite.so.1': 'libxcomposite1', 'libXdamage.so.1': 'libxdamage1', 'libXfixes.so.3': 'libxfixes3',
    'libXrandr.so.2': 'libxrandr2', 'libgbm.so.1': 'libgbm1', 'libpango-1.0.so.0': 'libpango-1.0-0', 'libpangocairo-1.0.so.0': 'libpangocairo-1.0-0',
    'libcairo.so.2': 'libcairo2', 'libasound.so.2': 'libasound2t64', 'libdbus-1.so.3': 'libdbus-1-3', 'libxshmfence.so.1': 'libxshmfence1',
    'libfontconfig.so.1': 'libfontconfig1', 'libfreetype.so.6': 'libfreetype6', 'libexpat.so.1': 'libexpat1', 'libudev.so.1': 'libudev1',
    'libgtk-3.so.0': 'libgtk-3-0t64', 'libgdk-3.so.0': 'libgtk-3-0t64', 'libgdk_pixbuf-2.0.so.0': 'libgdk-pixbuf-2.0-0', 'libXtst.so.6': 'libxtst6',
    'libXi.so.6': 'libxi6', 'libXcursor.so.1': 'libxcursor1', 'libvulkan.so.1': 'libvulkan1', 'libxml2.so.2': 'libxml2', 'libz.so.1': 'zlib1g',
    'libbz2.so.1.0': 'libbz2-1.0', 'liblzma.so.5': 'liblzma5', 'libpng16.so.16': 'libpng16-16t64', 'libjpeg.so.8': 'libjpeg-turbo8',
    'libtiff.so.6': 'libtiff6', 'libwebp.so.7': 'libwebp7', 'libopenblas.so.0': 'libopenblas0', 'libfribidi.so.0': 'libfribidi0',
    'libharfbuzz.so.0': 'libharfbuzz0b', 'libthai.so.0': 'libthai0', 'libpixman-1.so.0': 'libpixman-1-0', 'libxcb-render.so.0': 'libxcb-render0',
    'libxcb-shm.so.0': 'libxcb-shm0', 'libXau.so.6': 'libxau6', 'libXdmcp.so.6': 'libxdmcp6', 'libffi.so.8': 'libffi8', 'libuuid.so.1': 'libuuid1',
    'libleptonica.so.6': 'libleptonica6', 'libtesseract.so.5': 'libtesseract5', 'libpulse.so.0': 'libpulse0', 'libopus.so.0': 'libopus0',
    'libva.so.2': 'libva2', 'libvdpau.so.1': 'libvdpau1', 'libcuda.so.1': '(NVIDIA driver: not needed on a CPU box; a CPU wheel should not ask for it)',
}


def _find_chrome():
    roots = [os.path.expanduser('~/.cache'), os.path.join(CACHE, 'hf')]
    for r in roots:
        for dp, dn, fn in os.walk(r):
            for f in fn:
                if f in ('chrome', 'chrome-headless-shell', 'headless_shell') and os.access(os.path.join(dp, f), os.X_OK):
                    return os.path.join(dp, f)
    return None


@guarded('ldd')
def ldd():
    import sysconfig
    sp = {sysconfig.get_paths()['purelib'], sysconfig.get_paths()['platlib']}
    targets = []
    for root in sp:
        for dp, dn, fn in os.walk(root):
            targets += [os.path.join(dp, f) for f in fn if f.endswith('.so') or '.so.' in f]
    bins = [shutil.which(b) for b in ('ffmpeg', 'ffprobe', 'tesseract', 'node', 'git')] + [_find_chrome()]
    targets += [b for b in bins if b]
    missing, scanned, err = {}, 0, 0
    # wheels find their sibling libraries through python's import order, not RPATH (torchvision needs torch/lib, auditwheel
    # libs sit in <pkg>.libs): put every package library folder on the path so only genuinely missing SYSTEM libraries show
    libdirs = sorted({os.path.dirname(t) for t in targets if any(t.startswith(r) for r in sp)})
    lenv = dict(os.environ, LD_LIBRARY_PATH=':'.join(libdirs))
    for f in targets:
        rc, o = sh(['ldd', f], 30, env=lenv)
        if rc != 0 and 'not a dynamic executable' not in o and 'statically linked' not in o:
            err += 1
        scanned += 1
        for m in re.finditer(r'^\s*(\S+) => not found', o, re.M):
            missing.setdefault(m.group(1), []).append(os.path.relpath(f, next((r for r in sp if f.startswith(r)), '/')) if any(f.startswith(r) for r in sp) else f)
    chrome = bins[-1]
    lines = [f'scanned {scanned} files ({len(targets) - len([b for b in bins if b])} in the venv, binaries: ' + ', '.join(os.path.basename(b) for b in bins if b) + ')']
    if not chrome:
        lines.append('HyperFrames chrome binary NOT FOUND under ~/.cache or the hf cache (run item c first)')
    for lib in sorted(missing):
        files = sorted(set(missing[lib]))
        lines.append(f'NOT FOUND {lib}  ->  apt package: {PKG.get(lib, "unmapped (look up on packages.ubuntu.com, noble contents)")}   needed by {len(files)} file(s), e.g. {", ".join(files[:3])}')
    if missing:
        pk = sorted({PKG.get(l, f'?{l}') for l in missing})
        lines.append('apt install: ' + ' '.join(pk))
        rec('ldd', 'FAIL', f'{len(missing)} libraries not found: {", ".join(sorted(missing))}', '\n'.join(lines))
    else:
        rec('ldd', 'PASS' if chrome else 'WARN', f'no "not found" in {scanned} files' + ('' if chrome else '; chrome binary was not located'), '\n'.join(lines))


# ------------------------------------------------------------------------------------------------ h. host
@guarded('host')
def host():
    ws = os.getcwd()
    lines = [f'nproc {os.cpu_count()}', sh(['uname', '-sr'])[1].strip(), sh(['free', '-m'])[1].rstrip(), 'load ' + open('/proc/loadavg').read().strip()]
    for p in (ws, CACHE, TMP):
        lines.append(sh(['df', '-h', '--output=target,size,used,avail,pcent', p])[1].splitlines()[-1] + f'   ({p})')
    lines.append('id: ' + sh(['id'])[1].strip())
    lines.append('ulimit -n ' + sh(['bash', '-c', 'ulimit -n'])[1].strip())
    rc, o = sh(['sudo', '-n', 'true'], 10)
    sudo = rc == 0
    lines.append(f'sudo -n true: rc {rc} ({"passwordless sudo WORKS" if sudo else "no sudo, as intended"}) {o.strip()[:100]}')
    bad = []
    for d in [CACHE] + [os.path.join(CACHE, x) for x in ('models', 'cocktail-fork', 'tracksplit-stems', 'hf', 'pip', 'npm')] + [ws, TMP, os.environ.get('DXB_UPLOADS', TMP)]:
        if not os.path.isdir(d):
            lines.append(f'{d}: MISSING')
            bad.append(d)
            continue
        st = os.stat(d)
        w = os.access(d, os.W_OK)
        lines.append(f'{d}: owner uid {st.st_uid}, mode {oct(st.st_mode)[-3:]}, writable by this user: {w}')
        if not w:
            bad.append(d)
    root = os.getuid() == 0
    status = 'FAIL' if (bad or root) else ('WARN' if sudo else 'PASS')
    rec('host', status, f'{os.cpu_count()} cores, {sh(["free", "-g"])[1].split()[7]} GB memory, user uid {os.getuid()}{" (ROOT)" if root else ""}, sudo {"works" if sudo else "denied"}, ' +
        (f'not writable/missing: {bad}' if bad else 'cache and work dirs writable'), '\n'.join(lines))


# ------------------------------------------------------------------------------------------------ i. full render
@guarded('render')
def render(rev):
    t_all = time.time()
    path = 'jobs/render/helldivers-2-liberty-day-free-rifle.json'
    sh(['git', 'fetch', '-q', '--depth=1', '--filter=blob:none', 'origin', rev], 120, cwd=ROOT)
    rc, o = sh(['git', 'show', f'{rev}:{path}'], 120, cwd=ROOT)
    if rc:
        raise RuntimeError(f'could not read {path} at {rev}: {o[-200:]}')
    job = json.loads(o)
    orig = job['out']
    job['name'] = 'server-check-hd2'
    job['out'] = 'cards/2026-10/server-check-hd2-reel-v1.mp4'
    jpath = os.path.join(TMP, 'server-check-hd2.json')
    json.dump(job, open(jpath, 'w'), ensure_ascii=False)
    times = os.path.join(TEMPLATES, 'assets', 'render-times.json')
    gh = next((e for e in reversed(json.load(open(times))) if e.get('name') == os.path.basename(orig)), None)   # the GitHub run, before this one is appended
    env = dict(os.environ, RENDER_LANE='selfhosted-check', PYTHONUNBUFFERED='1')
    stats = os.path.join(TMP, 'runner-stats.json')
    stat = os.path.join(TEMPLATES, 'runner_stats.py')
    sh([sys.executable, stat, 'start', stats])
    t = time.time()
    p = subprocess.run([sys.executable, os.path.join(TEMPLATES, 'render_job.py'), 'run', jpath], cwd=ROOT, env=env, timeout=1500,
                       capture_output=True, text=True)
    wall = time.time() - t
    log = (p.stdout + p.stderr)
    print(log[-2500:])
    sh([sys.executable, stat, 'stop', stats])
    e = {}
    try:
        e = next(x for x in reversed(json.load(open(times))) if x.get('name') == 'server-check-hd2-reel-v1.mp4')
        json.dump(e, open(os.path.join(TMP, 'rt-entry.json'), 'w'))
        sh([sys.executable, stat, 'merge', stats, os.path.join(TMP, 'rt-entry.json')])
        e = json.load(open(os.path.join(TMP, 'rt-entry.json')))
    except Exception:
        pass
    decodes = re.findall(r'decode clean: (\S+)', log)
    out_mp4 = os.path.join(ROOT, job['out'])
    base = os.path.join(ROOT, re.sub(r'-reel-v\d+\.mp4$', '', job['out']))
    art = os.path.join(SC, 'artifacts', 'render')
    os.makedirs(art, exist_ok=True)
    for f in (out_mp4, base + '-strip.jpg'):
        if os.path.exists(f):
            shutil.copy(f, art)
    probe = ''
    if os.path.exists(out_mp4):
        probe = sh(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,width,height:format=duration,size', '-of', 'csv=p=0', out_mp4])[1].strip()

    def cell(d, *ks):
        for k in ks:
            d = (d or {}).get(k) if isinstance(d, dict) else None
        return '-' if d is None else d
    rows = [('cores', cell(gh, 'cores'), os.cpu_count()), ('checks s', cell(gh, 'stages', 'checks'), cell(e, 'stages', 'checks')),
            ('montage s', cell(gh, 'stages', 'montage'), cell(e, 'stages', 'montage')), ('text s', cell(gh, 'stages', 'text'), cell(e, 'stages', 'text')),
            ('audio s', cell(gh, 'stages', 'audio'), cell(e, 'stages', 'audio')), ('encode (outro) s', cell(gh, 'stages', 'outro'), cell(e, 'stages', 'outro')),
            ('render total s', cell(gh, 'total'), cell(e, 'total')), ('render step wall s (incl. fetch, autofocus, checks)', cell(gh, 'job_secs'), round(wall)),
            ('audio split', cell(gh, 'audio_split', 'reason'), cell(e, 'audio_split', 'reason') if e.get('audio_split') else 'none (track is our bed)'),
            ('peak memory MB', cell(gh, 'peak_mem_mb'), cell(e, 'peak_mem_mb')), ('memory total MB', cell(gh, 'mem_total_mb'), cell(e, 'mem_total_mb')),
            ('peak disk MB', cell(gh, 'peak_disk_mb'), cell(e, 'peak_disk_mb'))]
    table = '| | GitHub run (v3, runner) | dxb-render-1 |\n|---|---|---|\n' + '\n'.join(f'| {a} | {b} | {c} |' for a, b, c in rows)
    open(os.path.join(SC, 'render-compare.md'), 'w').write(table + f'\n\noutput: {probe}\n')
    ok = p.returncode == 0 and os.path.exists(out_mp4)
    rec('render', 'PASS' if ok else 'FAIL', f'Helldivers 2 Liberty Day test render {"ok" if ok else "FAILED (rc %s)" % p.returncode}: render step {wall:.0f} s on dxb-render-1 vs {cell(gh, "job_secs")} s on GitHub; peak memory {cell(e, "peak_mem_mb")} MB; output {probe}',
        ('' if ok else log[-1500:]) + '\n' + table + f'\ndecode-clean sources: {decodes}\nlog tail:\n' + log[-800:])
    for f in glob.glob(base + '*') + [out_mp4, jpath]:
        try:
            os.remove(f)
        except OSError:
            pass


# ------------------------------------------------------------------------------------------------ summary
def summary():
    rows = []
    try:
        rows = [json.loads(l) for l in open(RESULTS)]
    except OSError:
        pass
    order = list(ITEMS)
    rows.sort(key=lambda r: (order.index(r['item']) if r['item'] in order else 99))
    seen = {r['item'] for r in rows}
    skipped_render = os.environ.get('RENDER_INPUT') == 'false'
    lines = ['## dxb-render server check', '', '| Item | Result | Summary |', '|---|---|---|']
    for r in rows:
        lines.append(f"| {ITEMS.get(r['item'], r['item'])} | **{r['status']}** | {r['summary'].replace('|', '/')} |")
    for k in order:
        if k not in seen and k == 'render' and skipped_render:
            lines.append(f'| {ITEMS[k]} | **SKIPPED** | render=false |')
        elif k not in seen:
            lines.append(f'| {ITEMS[k]} | **NOT RUN** | the step did not report (failed before it could, or was skipped) |')
    fails = [r for r in rows if r['status'] == 'FAIL'] + [{'item': k} for k in order if k not in seen and not (k == 'render' and skipped_render)]
    lines += ['', f'**Overall: {"FAIL, " + str(len(fails)) + " item(s) need attention" if fails else "PASS (REVIEW items need a human look)"}**', '']
    cmp_ = os.path.join(SC, 'render-compare.md')
    if os.path.exists(cmp_):
        lines += ['### Test render, side by side', open(cmp_).read(), '']
    for r in rows:
        if r['detail'].strip():
            lines += [f"<details><summary>{ITEMS.get(r['item'], r['item'])}: {r['status']}</summary>", '', '```', r['detail'].strip()[:5000], '```', '</details>', '']
    md = '\n'.join(lines)
    out = os.environ.get('GITHUB_STEP_SUMMARY')
    if out:
        open(out, 'a').write(md + '\n')
    print(md)


def verdict():
    """The last step: exit 1 when any item failed or never reported, so the run is red in the Actions list; then the check dir goes."""
    rows = []
    try:
        rows = [json.loads(l) for l in open(RESULTS)]
    except OSError:
        pass
    seen = {r['item'] for r in rows}
    skipped_render = os.environ.get('RENDER_INPUT') == 'false'
    bad = [r['item'] for r in rows if r['status'] == 'FAIL'] + [k for k in ITEMS if k not in seen and not (k == 'render' and skipped_render)]
    shutil.rmtree(SC, ignore_errors=True)
    if bad:
        print('items failed or did not report: ' + ', '.join(sorted(set(bad))))
        sys.exit(1)
    print('no item failed')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    fn = {'init': init, 'fonts': fonts, 'imports': imports, 'ffmpeg': ffmpeg, 'hyperframes': hyperframes, 'split': split, 'tesseract': tesseract,
          'fetch': fetch, 'ldd': ldd, 'host': host, 'render': render, 'summary': summary, 'verdict': verdict}.get(cmd)
    if not fn:
        raise SystemExit(__doc__)
    fn(*sys.argv[2:])
    sys.exit(0)
