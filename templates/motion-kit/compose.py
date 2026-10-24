"""Motion kit pilot (advisor memo, 24 Oct 2026): lay kit moments over a finished Reel and build the demo.

    python3 compose.py sample <base.mp4> <job.json> <photo> <out.mp4>
    python3 compose.py demo <photo> <out.mp4>

Each kit moment is a HyperFrames composition whose background is the Reel's own frames for that span, so
the insert is laid over the Reel opaque with a hard cut at each end and nothing moves at the joins. Only the
kit element is new. reel.py and the live render path are not touched; this runs on the pilot branch only.
The Dubai font comes from DUBAI_FONTS (never committed); HF_CLI points at the pinned HyperFrames 0.8.143.
"""
import html, json, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, X = 30, 0.4                       # reel.py's frame rate and crossfade
GSAP = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'
LATIN = re.compile(r"\(?[A-Za-z0-9][A-Za-z0-9 .:'&%+\-]*[A-Za-z0-9%]\)?|\(?[A-Za-z0-9]\)?")
TIMES = []


def text(s):
    """Escape, keep each Latin run (with its brackets) in one isolated nowrap span, \\n to <br />."""
    out = []
    for line in s.split('\n'):
        e = html.escape(line)
        out.append(LATIN.sub(lambda m: f'<bdi class="nb">{m.group(0)}</bdi>', e))
    return '<br />'.join(out)


def page(body, js, dur, css_extra=''):
    kit_css = open(os.path.join(HERE, 'kit.css')).read()
    kit_js = open(os.path.join(HERE, 'kit.js')).read()
    return f"""<!doctype html>
<html lang="ar" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="{GSAP}"></script>
    <style>
{kit_css}
{css_extra}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1080" data-height="1920">
{body}
    </div>
    <script>
{kit_js}
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{js}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def workdir(name):
    w = tempfile.mkdtemp(prefix=f'mk-{name}-')
    os.makedirs(os.path.join(w, 'fonts'))
    fonts = os.environ.get('DUBAI_FONTS', '/root/fonts-private/dubai')
    for wt in ('Regular', 'Medium', 'Bold'):
        src = os.path.join(fonts, f'Dubai-{wt}.ttf')
        if os.path.exists(src):
            shutil.copy(src, os.path.join(w, 'fonts'))
        else:
            print(f'compose: Dubai-{wt}.ttf missing, the fallback font shows (preview only)', flush=True)
    json.dump({'name': name}, open(os.path.join(w, 'meta.json'), 'w'))
    json.dump({}, open(os.path.join(w, 'hyperframes.json'), 'w'))
    return w


def render(work, out, label):
    cli = os.environ.get('HF_CLI', 'hyperframes')
    t = time.time()
    subprocess.run([cli, 'render', work, '-o', out, '-q', 'delivery', '-f', str(FPS), '--quiet'], check=True)
    TIMES.append({'piece': label, 'render_secs': round(time.time() - t, 1)})
    return out


def segment(video, t0, dur, out):
    """The Reel's own frames for [t0, t0 + dur], frame-exact, dense keyframes so HyperFrames seeks cleanly."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-ss', f'{t0:.3f}', '-t', f'{dur:.3f}', '-an',
                    '-r', str(FPS), '-g', str(FPS), '-keyint_min', str(FPS), '-c:v', 'libx264', '-crf', '10',
                    '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], check=True)
    return out


def overlay(video, ins, t0, dur, out):
    """Opaque, hard cut at each end; the Reel's audio copied."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', ins, '-filter_complex',
                    f'[1:v]trim=0:{dur:.3f},setpts=PTS-STARTPTS+{t0:.3f}/TB[ov];[0:v][ov]overlay=0:0:eof_action=pass[v]',
                    '-map', '[v]', '-map', '0:a?', '-c:a', 'copy', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                    '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out], check=True)
    return out


def snap(t):
    return round(t * FPS) / FPS


# a. photo box over the Reel -------------------------------------------------------------------------------
def photobox(base, t0, dur, photo, name, role, credit, focus, accent):
    w = workdir('photobox')
    segment(base, t0, dur, os.path.join(w, 'bg.mp4'))
    shutil.copy(photo, os.path.join(w, 'photo' + os.path.splitext(photo)[1]))
    pf = 'photo' + os.path.splitext(photo)[1]
    D = f'data-start="0" data-duration="{dur:.3f}"'
    body = f"""      <video id="bg" class="clip" {D} data-media-start="0" muted src="bg.mp4"></video>
      <div class="pbox clip" {D}>
        <div class="pclip" id="pclip">
          <img src="{pf}" style="object-position: {focus[0] * 100:.0f}% {focus[1] * 100:.0f}%" />
          <div class="pshade"></div>
          <div class="pplate" id="pplate"><div class="pname">{text(name)}</div><div class="prole">{text(role)}</div>{f'<div class="pcred">{text(credit)}</div>' if credit else ''}</div>
        </div>
        <svg width="460" height="540"><rect id="pframe" x="1.5" y="1.5" width="457" height="537" rx="22" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000" /></svg>
      </div>"""
    js = f"""      const sIn = KIT.photoBox(tl, {{ box: '#pclip', frame: '#pframe', plate: '#pplate' }}, 0.0);
      KIT.photoBoxOut(tl, {{ box: '#pclip', frame: '#pframe', plate: '#pplate' }}, {dur - 0.3:.3f});"""
    open(os.path.join(w, 'index.html'), 'w').write(page(body, js, dur, f':root {{ --accent: {accent}; }}'))
    return w, [(t0 + 0.0, 'open')]


# b + c. number with an XP bar over the Reel ----------------------------------------------------------------
def number(base, t0, dur, value, unit, label, note, pct, accent):
    w = workdir('number')
    segment(base, t0, dur, os.path.join(w, 'bg.mp4'))
    D = f'data-start="0" data-duration="{dur:.3f}"'
    body = f"""      <video id="bg" class="clip" {D} data-media-start="0" muted src="bg.mp4"></video>
      <div id="dim" class="dim clip" {D}></div>
      <div id="card" class="ncard clip" {D}>
        <div class="nlabel">{text(label)}</div>
        <div id="nfig" class="nfig"><span id="nval">0</span><span class="u">{html.escape(unit)}</span></div>
        <div class="nbar"><div id="nfill" class="nfill"><div id="nglint" class="nglint"></div></div></div>
        <div class="nnote">{text(note)}</div>
      </div>"""
    js = f"""      tl.to('#dim', {{ opacity: 1, duration: 0.2, ease: 'none' }}, 0);
      KIT.triWipeIn(tl, '#card', 0.05);
      const sc = KIT.countUp(tl, {{ el: '#nval', wrap: '#nfig' }}, 0.42, {value});
      KIT.xpBar(tl, {{ fill: '#nfill', glint: '#nglint' }}, 0.42, {pct});
      KIT.triWipeOut(tl, '#card', {dur - 0.32:.3f});
      tl.to('#dim', {{ opacity: 0, duration: 0.22, ease: 'none' }}, {dur - 0.3:.3f});"""
    open(os.path.join(w, 'index.html'), 'w').write(page(body, js, dur, f':root {{ --accent: {accent}; }}'))
    blips = [(t0 + 0.05, 'wipe'), (t0 + 0.47, 'tick'), (t0 + 0.57, 'tick'), (t0 + 0.69, 'tick'), (t0 + 0.87, 'settle')]
    return w, blips


def sample(base, job_path, photo, out):
    """The Helldivers 3 sample: the base Reel (no person window, no 95% line) with two kit moments, the photo
    box over 0 to 7.4 s (the published Reel's person window) and the 95% figure with its bar over shots 8 to 10,
    cleared 2 s before the end card so the close stays a picture."""
    job = json.load(open(job_path))
    secs = [s[2] for s in job['shots']]
    starts = [0.0]
    for s in secs[:-1]:
        starts.append(starts[-1] + s - X)
    accent = {'cold': '#28b6f6', 'stylized': '#a5a3ff', 'playful': '#3ddcb4', 'spectacle': '#ffb547',
              'emerald': '#3ddc97', 'gold': '#f5c542'}.get(job['theme'], '#28b6f6')   # ig_ar.ACCENTS
    blips, cur = [], base
    tmp = tempfile.mkdtemp(prefix='mk-sample-')
    # moment 1: the photo box (the published Reel showed the person 0.0 to 7.4 s)
    pb_dur = snap(7.4)
    w, b = photobox(cur, 0.0, pb_dur, photo, 'جوهان بيليستيدت', 'المدير الإبداعي في أروهيد (Arrowhead)',
                    'الصورة: أروهيد', (0.5, 0.3), accent)
    ins = render(w, os.path.join(tmp, 'pb.mp4'), 'photobox (7.4 s)')
    cur = overlay(cur, ins, 0.0, pb_dur, os.path.join(tmp, 'r1.mp4')); blips += b
    # moment 2: the number card over shots 8 to 10, ending 2 s before the end card
    t0 = snap(starts[8])
    end = starts[10] + secs[10]
    dur = snap(end - t0 - 2.0)
    w, b = number(cur, t0, dur, 95, '%', 'من فريق أروهيد', 'يعمل على Helldivers 2', 95, accent)
    ins = render(w, os.path.join(tmp, 'nb.mp4'), f'number and bar ({dur:.1f} s)')
    cur = overlay(cur, ins, t0, dur, os.path.join(tmp, 'r2.mp4')); blips += b
    sys.path.insert(0, HERE)
    import blips as B
    B.mix(cur, blips, out)
    print('compose: moments', json.dumps({'photobox': [0.0, pb_dur], 'number': [round(t0, 3), dur]}), flush=True)
    return out


# the demo: every element alone, in order, on a moving house ground -----------------------------------------
def demo(photo, out):
    dur = 14.0
    w = workdir('demo')
    pf = 'photo' + os.path.splitext(photo)[1]
    shutil.copy(photo, os.path.join(w, pf))
    D = f'data-start="0" data-duration="{dur:.3f}"'
    seg = lambda a, b: f'data-start="{a}" data-duration="{b - a:.2f}"'
    body = f"""      <div class="clip" {D} style="position:absolute;inset:0;background:radial-gradient(120% 80% at 30% 20%, #2a2870 0%, #141332 60%)"></div>
      <div id="tag" class="clip" {D} style="position:absolute;top:1500px;right:96px;font-weight:500;font-size:34px;color:#c9c8e6"></div>
      <div class="pbox clip" {seg(0, 2.8)}>
        <div class="pclip" id="pclip">
          <img src="{pf}" style="object-position: 50% 30%" />
          <div class="pshade"></div>
          <div class="pplate" id="pplate"><div class="pname">{text('جوهان بيليستيدت')}</div><div class="prole">{text('المدير الإبداعي في أروهيد (Arrowhead)')}</div></div>
        </div>
        <svg width="460" height="540"><rect id="pframe" x="1.5" y="1.5" width="457" height="537" rx="22" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000" /></svg>
      </div>
      <div id="card" class="ncard clip" {seg(2.8, 7.4)}>
        <div class="nlabel">{text('من فريق أروهيد')}</div>
        <div id="nfig" class="nfig"><span id="nval">0</span><span class="u">%</span></div>
        <div class="nbar"><div id="nfill" class="nfill"><div id="nglint" class="nglint"></div></div></div>
        <div class="nnote">{text('يعمل على Helldivers 2')}</div>
      </div>
      <div id="chip" class="kchip clip" {seg(7.4, 9.6)}>رسمي</div>
      <div id="chiphead" class="clip" {seg(7.4, 9.6)} style="position:absolute;top:432px;right:170px;width:814px;text-align:right;font-weight:700;font-size:60px;line-height:1.28">{text('عنوان الخبر كما هو اليوم')}</div>
      <div id="banner" class="kbanner clip" {seg(9.6, 12.2)}>
        <svg class="kicon" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="none" stroke="#28b6f6" stroke-width="4"/><path d="M25 19 L47 32 L25 45 Z" fill="#28b6f6"/></svg>
        <div><div class="ktitle">{text('رقم قياسي')}</div><div class="ksub">{text('مثال: إنجاز حقيقي فقط')}</div></div>
      </div>
      <div id="wipecard" class="ncard clip" {seg(12.2, 14.0)} style="top:820px">
        <div class="nlabel">{text('انتقال البطاقة')}</div>
        <div class="nnote">{text('مسح عبر مثلث التشغيل')}</div>
      </div>"""
    labels = [(0.0, 'أ. صندوق الصورة'), (2.8, 'ب، ج. الرقم والشريط'), (7.4, 'د. الشارة'),
              (9.6, 'هـ. شريط الإنجاز'), (12.2, 'و. انتقال البطاقة')]
    js = '\n'.join(f"      tl.set('#tag', {{ textContent: {json.dumps(l, ensure_ascii=False)} }}, {t});" for t, l in labels)
    js += """
      KIT.photoBox(tl, { box: '#pclip', frame: '#pframe', plate: '#pplate' }, 0.2);
      KIT.photoBoxOut(tl, { box: '#pclip', frame: '#pframe', plate: '#pplate' }, 2.45);
      KIT.triWipeIn(tl, '#card', 2.85);
      KIT.countUp(tl, { el: '#nval', wrap: '#nfig' }, 3.25, 95);
      KIT.xpBar(tl, { fill: '#nfill', glint: '#nglint' }, 3.25, 95);
      KIT.triWipeOut(tl, '#card', 7.0);
      KIT.chipPress(tl, '#chip', 7.6);
      KIT.unlockBanner(tl, '#banner', 9.8, 1.5);
      KIT.triWipeIn(tl, '#wipecard', 12.4);"""
    open(os.path.join(w, 'index.html'), 'w').write(page(body, js, dur))
    raw = render(w, os.path.join(w, 'demo-raw.mp4'), 'demo (14 s)')
    silent = os.path.join(w, 'demo-silent.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo',
                    '-t', f'{dur}', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', silent], check=True)
    sys.path.insert(0, HERE)
    import blips as B
    moments = [(0.2, 'open'), (2.85, 'wipe'), (3.3, 'tick'), (3.4, 'tick'), (3.52, 'tick'), (3.7, 'settle'),
               (7.72, 'press'), (9.8, 'unlock'), (12.4, 'wipe')]
    return mix_on_silence(B, silent, moments, out)


def mix_on_silence(B, video, moments, out):
    """blips.mix scales to the track's peak; on a silent track scale to a fixed quiet level instead."""
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vn', '-ac', '2', '-ar', str(B.SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    for t, kind in moments:
        b = B.KINDS[kind]()
        b = (b / np.abs(b).max() * 0.25).astype(np.float32)
        o = int(round(t * B.SR)); n = min(len(b), len(a) - o)
        if n > 0:
            a[o:o + n] += b[:n, None]
    f = out + '.f32'; a.tofile(f)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-f', 'f32le', '-ar', str(B.SR), '-ac', '2', '-i', f,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', out], check=True)
    os.remove(f)
    return out


def side_by_side(left, right, out):
    """Today's Reel left, the kit right, each at half size, the kit's sound."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', left, '-i', right, '-filter_complex',
                    '[0:v]scale=540:960,setsar=1[a];[1:v]scale=540:960,setsar=1[b];[a][b]hstack=inputs=2,format=yuv420p[v]',
                    '-map', '[v]', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium',
                    '-c:a', 'aac', '-movflags', '+faststart', out], check=True)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'sample':
        sample(a[1], a[2], a[3], a[4])
    elif a[0] == 'demo':
        demo(a[1], a[2])
    elif a[0] == 'sbs':
        side_by_side(a[1], a[2], a[3])
    if TIMES:
        tf = os.environ.get('MK_TIMES')
        if tf:
            d = json.load(open(tf)) if os.path.exists(tf) else []
            json.dump(d + TIMES, open(tf, 'w'), indent=1, ensure_ascii=False)
        print('compose: render times', json.dumps(TIMES, ensure_ascii=False), flush=True)
