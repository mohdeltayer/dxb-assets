"""Design pass in live Reels (advisor memo of 24 Oct 2026; Mohammad approved the three samples, "Roll out", 24 Oct
19:21Z). reel.py stays the backbone; this joins the runner path the way HyperFrames inserts do (hfinsert.py).

A job opts in with explicit keys; a job without them renders exactly as before:

    "frame": {"shot": 2, "offset": 0.25, "secs": 4.0,                    # the WHERE AND HOW MUCH frame
              "data": {"platforms": [{"logo": "ps5", "prices": [["الإمارات", ["aed", "239"]]]},
                                     {"logo": "steam", "prices": [["الإمارات", ["aed", "219"]],
                                                                  ["السعودية", "225 ريالًا"]]}],
                       "price_all": null, "date": "تصل في 29 أكتوبر", "note": null, "arabic": false}},
    "kit": ["chip"],                     # kit moments: "chip" (the chip press), "photobox" (the person's photo box,
                                         # open on frame 0 beside the headline, stepping aside as the headline leaves)
    "kit_quiet": [[0.0, 3.4]],           # optional: Reel seconds where voices play; no blip lands there
    "blips": false                       # optional: no UI blips on this Reel

The frame: platform logos on equal plates (two rows past four; templates/assets/platforms, unsourced marks as text
plates), the price under each in Dubai Bold (["aed", "239"] takes the Central Bank dirham sign left of the digits,
other currencies as written, {"unknown": "لم يُعلن السعر بعد"} for an unknown), one price for all once and centred
(`price_all`), the date on one line beneath, an optional note, the «بالعربية» badge (`arabic`). The plates press in
one after another, 0.3 s apart, then hold still 2 to 3 s; the footage keeps moving behind under a 62% indigo dim.
It is laid over [starts[shot] + offset, + secs] of the finished Reel, which must lie after the headline, before the
last 0.5 s of the clip and clear of story lines, credits and person windows (one focus at a time). The frame
replaces the split strip (one fact, one place): the strip is rendered on its own layer and laid back exactly as
drawn only if the frame fails.

Placement rules (memo, point 4, and the motion kit memo, point 1): at most two kit moments per Reel, and the frame
counts as one (its logo press), so a frame takes "chip" or "photobox", not both; extra moments are dropped with a
note. The breaking profile and the عاجل chip skip the kit and the frame (speed first). "photobox" needs the job's
first person window to open at 0 (`"person": [[photo, name, role, 0, 3.5, {...}]]`): on the cover it is open on
frame 0, with no triangle wipe (Mohammad, 24 Oct 2026), and leaves with the kit's exit at its end time.

Safety: each piece (the cover, the frame) renders under its own TIMEOUT; a failed piece, or one past 5 minutes,
leaves that part of the Reel as reel.py drew it (the chip, the person window and the strip laid back from the
layers reel.py wrote, with its fades). The story is never held. The outcome goes to the render log
(`render_job: design pass:`) and to render-times.json as `design_pass`. HyperFrames is pinned in hfinsert.HF_VERSION
and installed by render.yml only for a job that needs it; with no HyperFrames CLI the Reel renders as before.
Blips (kit/blips.py, the four-note motif) sit 14 dB under the Reel's peak and are mixed after the audio split, never
inside `speech_ok` or `kit_quiet` windows; a job with `speech_keep` (voices with no windows given) gets none.

    python3 designpass.py need <job.json>      # exit 0 when the job needs HyperFrames for the design pass
"""
import html, json, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, 'hyperframes', 'kit')
LOGOS = os.path.join(HERE, 'assets', 'platforms')
DIRHAM = os.path.join(HERE, 'assets', 'dirham-symbol-mask.png')
MOMENTS = ('chip', 'photobox')
MAX_MOMENTS = 2                   # one or two kit moments per Reel at most; the frame counts as one
TIMEOUT = 300                     # seconds per piece: past this the part stays as reel.py drew it
FPS = 30
GSAP = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'
LATIN = re.compile(r"\(?[A-Za-z0-9][A-Za-z0-9 :.,'&()+/|-]*[A-Za-z0-9)]|[A-Za-z]")
INK, BODY, INDIGO, GROUND = '#f4f3ff', '#c9c8e6', '#5552e0', '#141332'
SAFE = (96, 285, 910, 1480)       # x0, y0, x1, y1 (Reels safe zone)
TEXT_PLATES = {'xbox-one': 'Xbox One', 'mac': 'Mac', 'app-store': 'App Store', 'meta-quest': 'Meta Quest'}   # not sourced


# ------------------------------------------------------------------------------------------------- the plan
def breaking(job):
    return job.get('profile') == 'breaking' or job.get('label') == 'عاجل'


def wanted(job):
    """True when the job asks for any part of the design pass (and is not breaking)."""
    return bool((job.get('kit') or job.get('frame')) and not breaking(job))


def hf_cli():
    """The HyperFrames command, or None when it is not installed (the container; a failed install on the runner)."""
    cli = os.environ.get('HF_CLI')
    if cli:
        return cli if os.path.exists(cli) else None
    return shutil.which('hyperframes')


def plan(job, starts, end, lines, head_secs=3.5):
    """What runs for this job: {'moments': [...], 'frame': {..., 'at', 'secs'} | None, 'notes': [...]}.
    `starts`, `end` from reel.timeline, `lines` the placed story lines [(text, a, z, kw)]. Nothing here raises: what
    breaks a rule is dropped with a note and the Reel keeps reel.py's version of it."""
    notes, moments, fr = [], [], None
    if breaking(job):
        if job.get('kit') or job.get('frame'):
            notes.append('breaking (profile or عاجل): kit and frame skipped, speed first')
        return {'moments': [], 'frame': None, 'notes': notes}
    for m in job.get('kit') or []:
        if m not in MOMENTS:
            notes.append(f'kit moment {m!r} unknown here (live: {", ".join(MOMENTS)}); dropped')
        elif m in moments:
            continue
        elif m == 'chip' and not (job.get('label') or job.get('country')):
            notes.append('chip press: the job has no chip; dropped')
        elif m == 'photobox' and not (job.get('person') and float(job['person'][0][3]) == 0):
            notes.append('photobox: the first person window does not open at 0 (the cover); dropped')
        else:
            moments.append(m)
    f = job.get('frame')
    if f:
        try:
            i = int(f['shot'])
            a = round(round((starts[i] + float(f.get('offset', 0.25))) * FPS) / FPS, 3)
            secs = float(f.get('secs', 4.0))
            z = a + secs
            if not 3.0 <= secs <= 6.0:
                raise ValueError(f'secs {secs}: 3 to 6 s (2 to 3 s held still after the presses)')
            if a < head_secs:
                raise ValueError(f'starts at {a:.2f} s, under the headline (until {head_secs} s)')
            if z > end - 0.5:
                raise ValueError(f'ends at {z:.2f} s, into the last 0.5 s of the clip ({end:.2f} s)')
            busy = [t for t, la, lz, _ in lines if la < z and lz > a]
            busy += [p[1] for p in job.get('person') or [] if float(p[3]) < z and float(p[4]) > a]
            if busy:
                raise ValueError(f'a story line or person window is on screen in {a:.2f} to {z:.2f} s: {busy[0]!r} '
                                 '(one focus at a time: move the line off the frame\'s shot)')
            for c in job.get('credits') or []:
                ca = starts[c[0]]
                cz = starts[c[1] + 1] if c[1] + 1 < len(starts) else end
                if ca < z and cz > a:
                    raise ValueError(f'the credit {c[2]!r} runs under the frame')
            fr = dict(f, at=a, secs=secs)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            notes.append(f'frame dropped before the render: {e}')
    if fr and len(moments) > MAX_MOMENTS - 1:
        notes.append(f'the frame counts as a kit moment: {moments[MAX_MOMENTS - 1:]} dropped (one or two per Reel)')
        moments = moments[:MAX_MOMENTS - 1]
    if len(moments) > MAX_MOMENTS:
        notes.append(f'{moments[MAX_MOMENTS:]} dropped (one or two kit moments per Reel)')
        moments = moments[:MAX_MOMENTS]
    if fr and not job.get('strip'):
        notes.append('frame without a strip: if the frame fails, nothing carries its facts')
    return {'moments': moments, 'frame': fr, 'notes': notes}


def apart_spec(p, folder):
    """reel(apart=...) for a plan: which layers reel.py leaves out of the burn."""
    return {'dir': folder, 'chip': 'chip' in p['moments'], 'person': 'photobox' in p['moments'], 'strip': bool(p['frame'])}


# --------------------------------------------------------------------------------------------- page helpers
def text(s):
    """Escape; Latin and digit runs held together in one isolated nowrap span; \\n as a line break."""
    out = []
    for part in str(s).split('\n'):
        esc, pos, chunk = html.escape(part), 0, []
        for m in LATIN.finditer(esc):
            if not re.search('[A-Za-z0-9]', m.group(0)):
                continue
            chunk.append(esc[pos:m.start()]); chunk.append(f'<bdi class="nb">{m.group(0)}</bdi>'); pos = m.end()
        chunk.append(esc[pos:]); out.append(''.join(chunk))
    return '<br />'.join(out)


def arabic_first(s, what):
    """House rule: every visual line opens on an Arabic word (digits-first prices are values, not lines)."""
    for line in str(s).split('\n'):
        c = line.lstrip('«"“‏ ')[:1]
        if c and not ('؀' <= c <= 'ۿ'):
            raise ValueError(f'{what}: line opens on a non-Arabic character: {line}')


def accent(job):
    import ig_ar
    if job.get('skin') not in (None, 'house'):
        import skins
        c = skins.load(job['skin'])['accent']
    else:
        c = ig_ar.ACCENTS.get(job.get('theme'), ig_ar.ACCENTS['cold'])
    if isinstance(c, str):
        return c
    r, g, b = c[:3]
    return f'#{r:02x}{g:02x}{b:02x}'


def page(body, js, dur, css=''):
    kit_css = open(os.path.join(KIT, 'kit.css')).read()
    kit_js = open(os.path.join(KIT, 'kit.js')).read()
    return f"""<!doctype html>
<!-- generated by templates/designpass.py; not edited by hand -->
<html lang="ar" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="{GSAP}"></script>
    <style>
{kit_css}
      .clip {{ position: absolute; }}
{css}
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
    """A composition folder with the Dubai font copied in (never kept: removed after the render and in any case)."""
    w = tempfile.mkdtemp(prefix=f'dpass-{name}-')
    os.makedirs(os.path.join(w, 'fonts'))
    fonts = os.environ.get('DUBAI_FONTS', '/root/fonts-private/dubai').rstrip('/')
    for wt in ('Regular', 'Medium', 'Bold'):
        src = os.path.join(fonts, f'Dubai-{wt}.ttf')
        if not os.path.exists(src):
            raise FileNotFoundError(f'Dubai-{wt}.ttf missing: no piece is rendered on a fallback font')
        shutil.copy(src, os.path.join(w, 'fonts'))
    json.dump({'id': name, 'name': name}, open(os.path.join(w, 'meta.json'), 'w'))
    json.dump({}, open(os.path.join(w, 'hyperframes.json'), 'w'))
    return w


def ff(*a, timeout=None):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *a], check=True, timeout=timeout)


def segment(video, t0, dur, out):
    """The Reel's own frames for [t0, t0 + dur], frame-exact, dense keyframes so HyperFrames seeks cleanly."""
    ff('-ss', f'{t0:.3f}', '-i', video, '-t', f'{dur:.3f}', '-an', '-r', str(FPS), '-g', str(FPS), '-keyint_min',
       str(FPS), '-c:v', 'libx264', '-crf', '10', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out)
    return out


def hf_render(work, out, budget):
    subprocess.run([hf_cli() or 'hyperframes', 'render', work, '-o', out, '-q', 'delivery', '-f', str(FPS), '--quiet'],
                   check=True, timeout=budget)
    return out


# ----------------------------------------------------------------------------------------- the cover moment
def cover(job, base, man, moments, work, theme_accent):
    """Frame 0 to `dur`: the chip row back over the Reel (the same pixels reel.py drew), resting on frame 0 (the grid
    tile), pressing once at 0.25 s (down to 94%, a small bounce, settled within 0.3 s) and fading with the headline;
    the photo box (the job's first person window) open on frame 0 at reel.PERSON_BOX with no wipe, leaving with the
    kit's exit at the window's end. Returns (dur, blips)."""
    import cards as C
    head_secs = man['head_secs']
    lay = {x['what']: x for x in man['layers']}
    press_at = 0.25
    body, js, css, blips = '', [], f':root {{ --accent: {theme_accent}; }}\n', []
    pz = None
    if 'photobox' in moments:
        pz = lay['person']['segs'][0][1]
    dur = round(round((max(head_secs, pz or 0) + (0.2 if pz else 0.1)) * FPS) / FPS, 3)
    segment(base, 0, dur, os.path.join(work, 'bg.mp4'))
    D = f'data-start="0" data-duration="{dur:.3f}"'
    body += f'      <video id="bg" class="clip" {D} data-media-start="0" muted src="bg.mp4"></video>\n'
    if 'chip' in moments:
        x0, y0, x1, y1 = lay['chip']['box']
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        shutil.copy(lay['chip']['png'], os.path.join(work, 'chip.png'))
        body += (f'      <div class="clip" {D} style="inset:0">\n'
                 f'        <img id="chip" src="chip.png" style="position:absolute;left:0;top:0;width:1080px;height:1920px;'
                 f'transform-origin:{cx:.1f}px {cy:.1f}px" />\n      </div>\n')
        js += [f"      tl.to('#chip', {{ scale: 0.94, y: 2, duration: 0.12, ease: 'power2.in' }}, {press_at});",
               f"      tl.to('#chip', {{ scale: 1.02, y: 0, duration: 0.1, ease: 'power2.out' }}, {press_at + 0.12:.2f});",
               f"      tl.to('#chip', {{ scale: 1, duration: 0.08, ease: 'power1.inOut' }}, {press_at + 0.22:.2f});",
               f"      tl.to('#chip', {{ opacity: 0, duration: 0.2, ease: 'none' }}, {head_secs - 0.2:.2f});"]
        blips.append((press_at + 0.12, 'press'))
    if pz:
        photo, pname, role, _, _, *opt = job['person'][0]
        opt = opt[0] if opt else {}
        credit, focus = opt.get('credit'), opt.get('focus', (0.5, 0.33))
        for s in (pname, role) + ((credit,) if credit else ()):
            arabic_first(s, 'person plate')
        ext = os.path.splitext(photo)[1]
        shutil.copy(C.U + photo, os.path.join(work, 'photo' + ext))
        bx, by, bw, bh = lay['person']['box']
        css += (f'      .pbox {{ left: {bx}px; top: {by}px; width: {bw}px; height: {bh}px; }}\n'
                '      .pbox .pname { font-size: 46px; } .pbox .prole { font-size: 30px; } .pbox .pcred { font-size: 21px; }\n')
        body += f"""      <div class="pbox clip" {D}>
        <div class="pclip" id="pclip">
          <img src="photo{ext}" style="object-position: {focus[0] * 100:.0f}% {focus[1] * 100:.0f}%" />
          <div class="pshade"></div>
          <div class="pplate" id="pplate"><div class="pname">{text(pname)}</div><div class="prole">{text(role)}</div>{f'<div class="pcred">{text(credit)}</div>' if credit else ''}</div>
        </div>
        <svg width="{bw}" height="{bh}"><rect id="pframe" x="1.5" y="1.5" width="{bw - 3}" height="{bh - 3}" rx="22" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="0" /></svg>
      </div>
"""
        # open on frame 0, no wipe on the cover (Mohammad, 24 Oct 2026); the kit's own exit at the window's end
        js = ["      gsap.set('#pclip', { clipPath: KIT.RECT });"] + js + \
             [f"      KIT.photoBoxOut(tl, {{ box: '#pclip', frame: '#pframe', plate: '#pplate' }}, {pz - 0.2:.2f});"]
        blips.append((pz - 0.16, 'wipe'))
    open(os.path.join(work, 'index.html'), 'w', encoding='utf8').write(page(body, '\n'.join(js), dur, css))
    return dur, blips


# ------------------------------------------------------------------------------ the WHERE AND HOW MUCH frame
def _logo_html(slug, pw):
    if slug in TEXT_PLATES:
        return f'<div class="tplate"><bdi class="nb">{html.escape(TEXT_PLATES[slug])}</bdi></div>'
    from PIL import Image
    w, h = Image.open(os.path.join(LOGOS, slug + '.png')).size
    asp = w / h
    lh = 116 if asp < 1.6 else min(84, (pw - 70) / asp)     # square marks larger, wide lockups fitted to the plate
    return f'<img class="logo" src="logos/{slug}.png" style="height:{lh:.0f}px" />'


def _value_html(v):
    """['aed', '239'] -> the Central Bank dirham symbol left of the digits; {'unknown': text}; else text as written."""
    if isinstance(v, (list, tuple)) and v and v[0] == 'aed':
        return f'<span class="money"><img class="dh" src="dirham.png" /><span>{html.escape(str(v[1]))}</span></span>'
    if isinstance(v, dict) and v.get('unknown'):
        arabic_first(v['unknown'], 'frame unknown'); return f'<span class="unk">{text(v["unknown"])}</span>'
    return f'<span class="vtxt">{text(v)}</span>'


def frame_piece(d, dur):
    """Logos press in one after another (in at 112%, under to 94%, settled at 0.3 s; 0.3 s apart), the date and note
    rise in, then everything holds still; the last 0.3 s clear it back to the footage. Returns (body, js, css, press
    times, (settled, out_at))."""
    ps = d['platforms']
    n = len(ps)
    if not 1 <= n <= 8:
        raise ValueError('frame: one to eight platforms')
    rows = [ps] if n <= 4 else [ps[:(n + 1) // 2], ps[(n + 1) // 2:]]
    gap = 22
    per = max(len(r) for r in rows)
    pw = (SAFE[2] - SAFE[0] - gap * (per - 1)) / per
    nrows = max(len(p.get('prices', [])) for p in ps)
    for txt in [d['date']] + ([d['note']] if d.get('note') else []):
        arabic_first(txt, 'frame line')
    for p in ps:
        if p['logo'] not in TEXT_PLATES and not os.path.exists(os.path.join(LOGOS, p['logo'] + '.png')):
            raise ValueError(f"frame: no logo {p['logo']!r} in templates/assets/platforms")
        for region, _ in p.get('prices', []):
            if region:
                arabic_first(region, 'frame region')
    css = f"""
      #dim {{ inset: 0; background: rgba(20, 19, 50, 0.62); opacity: 0; }}
      #wf {{ left: {SAFE[0]}px; top: {SAFE[1]}px; width: {SAFE[2] - SAFE[0]}px; height: {SAFE[3] - SAFE[1]}px;
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 26px; }}
      .prow {{ display: flex; flex-direction: row; gap: {gap}px; justify-content: center; width: 100%; }}
      .plat {{ width: {pw:.0f}px; background: rgba(20, 19, 50, 0.86); border: 3px solid var(--accent); border-radius: 24px;
              display: flex; flex-direction: column; align-items: center; padding: 26px 18px 24px; opacity: 0;
              box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45); }}
      .lbox {{ height: 120px; display: flex; align-items: center; justify-content: center; width: 100%; }}
      .logo {{ display: block; max-width: 100%; }}
      .tplate {{ font-weight: 700; font-size: 52px; line-height: 1; color: {INK}; direction: ltr; }}
      .rule {{ width: 70%; height: 2px; background: var(--accent); opacity: .55; margin: 16px 0 6px; }}
      .pr {{ display: flex; flex-direction: column; align-items: center; margin-top: 10px; min-height: {118 if nrows else 0}px;
            justify-content: center; }}
      .reg {{ font-weight: 500; font-size: 32px; line-height: 1.2; color: {BODY}; }}
      .val {{ font-weight: 700; font-size: 74px; line-height: 1.1; color: {INK}; white-space: nowrap; }}
      .money {{ display: inline-flex; direction: ltr; align-items: baseline; gap: 0.16em; }}
      .dh {{ display: inline-block; height: 0.62em; width: auto; }}
      .vtxt {{ direction: rtl; }}
      .unk {{ font-weight: 500; font-size: 40px; color: {BODY}; white-space: normal; }}
      #all {{ font-weight: 700; font-size: 92px; line-height: 1.1; opacity: 0; }}
      #date {{ font-weight: 700; font-size: 58px; line-height: 1.2; color: {INK}; opacity: 0; text-shadow: 0 2px 12px rgba(20,19,50,.8); }}
      #note {{ font-weight: 500; font-size: 38px; line-height: 1.3; color: {BODY}; opacity: 0; margin-top: -10px;
              text-shadow: 0 2px 12px rgba(20,19,50,.8); }}
      #ar {{ align-self: flex-start; background: {INDIGO}; color: {INK}; font-weight: 700; font-size: 44px; height: 70px;
            line-height: 70px; padding: 0 26px; border-radius: 10px; opacity: 0; }}
"""
    body = ['      <div id="wf" class="clip" data-start="0" data-duration="%.3f">' % dur]
    if d.get('arabic'):
        body.append('        <div id="ar">بالعربية</div>')
    k = 0
    for r in rows:
        body.append('        <div class="prow">')
        for p in r:
            prices = ''.join(f'<div class="pr">{f"<div class=reg>{text(reg)}</div>" if reg else ""}'
                             f'<div class="val">{_value_html(v)}</div></div>' for reg, v in p.get('prices', []))
            body.append(f'          <div class="plat" id="p{k}"><div class="lbox">{_logo_html(p["logo"], pw)}</div>'
                        + (f'<div class="rule"></div>{prices}' if prices else '') + '</div>')
            k += 1
        body.append('        </div>')
    if d.get('price_all') is not None:
        body.append(f'        <div id="all" class="val">{_value_html(d["price_all"])}</div>')
    body.append(f'        <div id="date">{text(d["date"])}</div>')
    if d.get('note'):
        body.append(f'        <div id="note">{text(d["note"])}</div>')
    body.append('      </div>')
    js = ["      tl.to('#dim', { opacity: 1, duration: 0.2, ease: 'none' }, 0);"]
    press, t = [], 0.15
    if d.get('arabic'):
        js.append(f"      tl.fromTo('#ar', {{ scale: 1.12, y: -6, opacity: 0 }}, {{ scale: 0.94, y: 2, opacity: 1, duration: 0.12, ease: 'power2.in' }}, {t:.2f});")
        js.append(f"      tl.to('#ar', {{ scale: 1, y: 0, duration: 0.14, ease: 'power2.out' }}, {t + 0.12:.2f});")
    for i in range(n):
        js.append(f"      tl.fromTo('#p{i}', {{ scale: 1.12, y: -8, opacity: 0 }}, {{ scale: 0.94, y: 2, opacity: 1, duration: 0.12, ease: 'power2.in' }}, {t:.2f});")
        js.append(f"      tl.to('#p{i}', {{ scale: 1.02, y: 0, duration: 0.1, ease: 'power2.out' }}, {t + 0.12:.2f});")
        js.append(f"      tl.to('#p{i}', {{ scale: 1, duration: 0.08, ease: 'power1.inOut' }}, {t + 0.22:.2f});")
        press.append(t + 0.12)
        t += 0.3
    for el in (['#all'] if d.get('price_all') is not None else []) + ['#date'] + (['#note'] if d.get('note') else []):
        js.append(f"      tl.fromTo('{el}', {{ y: 14, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.25, ease: 'power3.out' }}, {t:.2f});")
        t += 0.08
    settled = t + 0.25
    out_at = dur - 0.3
    if out_at - settled < 2.0:
        raise ValueError(f'frame holds only {out_at - settled:.2f} s still; it needs 2 to 3 s for reading (more secs)')
    js.append(f"      tl.to('#wf', {{ opacity: 0, duration: 0.22, ease: 'power1.in' }}, {out_at:.2f});")
    js.append(f"      tl.to('#dim', {{ opacity: 0, duration: 0.28, ease: 'none' }}, {out_at:.2f});")
    return '\n'.join(body), '\n'.join(js), css, press, (settled, out_at)


def frame(base, fr, work, theme_accent):
    from PIL import Image
    t0, dur = fr['at'], fr['secs']
    segment(base, t0, dur, os.path.join(work, 'bg.mp4'))
    os.makedirs(os.path.join(work, 'logos'))
    for p in fr['data']['platforms']:
        if p['logo'] not in TEXT_PLATES and os.path.exists(os.path.join(LOGOS, p['logo'] + '.png')):
            shutil.copy(os.path.join(LOGOS, p['logo'] + '.png'), os.path.join(work, 'logos'))
    m = Image.open(DIRHAM).convert('L')        # the Central Bank symbol: white, its shape in the alpha channel
    sym = Image.new('RGBA', m.size, (244, 243, 255, 255)); sym.putalpha(m)
    sym.crop(m.getbbox()).save(os.path.join(work, 'dirham.png'))
    body, js, css, press, hold = frame_piece(fr['data'], dur)
    D = f'data-start="0" data-duration="{dur:.3f}"'
    body = (f'      <video id="bg" class="clip" {D} data-media-start="0" muted src="bg.mp4"></video>\n'
            f'      <div id="dim" class="clip" {D}></div>\n' + body)
    open(os.path.join(work, 'index.html'), 'w', encoding='utf8').write(
        page(body, js, dur, f':root {{ --accent: {theme_accent}; }}\n' + css))
    return [(t0 + p, 'press') for p in press], hold


# --------------------------------------------------------------------------------------------- composing
def _layer_filters(i, lay, end, lead):
    """Filters that lay one kept reel.py layer back exactly as reel.py's text pass did: alpha fade in over its
    fade time when it starts after 0, out over 0.2 s when it ends before the clip, and, as outro.append fades the
    body to the ground over its last `lead` s, the layer's colour fades to the ground there too."""
    out = []
    for k, (a, z, fd) in enumerate(lay['segs']):
        fin = f',fade=t=in:st={a:.2f}:d={fd}:alpha=1' if a > 0 else ''
        fout = f',fade=t=out:st={z - 0.2:.2f}:d=0.2:alpha=1' if z < end - 0.01 else ''
        out.append((f'[{i + k}:v]format=rgba{fin}{fout},fade=t=out:st={max(0, end - lead):.3f}:d={lead}:color={GROUND}'
                    f',trim=0:{end:.3f}', a, z))
    return out


def compose(video, man, pieces, keep_back, out):
    """One encode: the kept reel.py layers that no piece replaced, then the rendered pieces, opaque, hard cuts."""
    import outro, reel
    end = man['end']
    args, fc, n, pv = ['-i', video], [], 1, '0:v'
    for lay in keep_back:
        for _ in lay['segs']:
            args += ['-loop', '1', '-t', f'{end:.3f}', '-i', lay['png']]
        for k, (f, _, _) in enumerate(_layer_filters(n, lay, end, outro.LEAD)):
            fc += [f'{f}[k{n + k}]', f'[{pv}][k{n + k}]overlay=0:0:eof_action=pass[o{n + k}]']
            pv = f'o{n + k}'
        n += len(lay['segs'])
    for p in pieces:
        args += ['-i', p['mp4']]
        fc += [f"[{n}:v]trim=0:{p['secs']:.3f},setpts=PTS-STARTPTS+{p['at']:.3f}/TB[k{n}]",
               f'[{pv}][k{n}]overlay=0:0:eof_action=pass[o{n}]']
        pv = f'o{n}'
        n += 1
    if not fc:
        return video
    fc.append(f'[{pv}]format=yuv420p[v]')
    ff(*args, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '0:a?', '-c:a', 'copy', '-c:v', 'libx264',
       *reel.FINAL_ENC, '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out)
    return out


def apply(job, video, p, apart_dir):
    """The planned pieces over the finished Reel, in place. Returns the record for render-times.json."""
    t_all = time.time()
    man = json.load(open(os.path.join(apart_dir, 'apart.json')))
    lay = {x['what']: x for x in man['layers']}
    acc = accent(job)
    rec = {'hf': __import__('hfinsert').HF_VERSION, 'notes': list(p['notes']), 'pieces': [], 'blips': []}
    done, blips = [], []
    jobs = []
    if p['moments']:
        jobs.append(('cover', lambda w: cover(job, video, man, p['moments'], w, acc)))
    if p['frame']:
        jobs.append(('frame', lambda w: frame(video, p['frame'], w, acc)))
    replaced = set()
    for name, build in jobs:
        t = time.time()
        r = {'piece': name}
        work = tempfile.mkdtemp(prefix=f'dpass-{name}-')
        try:
            if not hf_cli():
                raise FileNotFoundError('HyperFrames CLI not installed')
            comp = workdir(name)
            shutil.rmtree(work); work = comp
            if name == 'cover':
                secs, b = build(work)
                at, r['moments'] = 0.0, list(p['moments'])
            else:
                b, hold = build(work)
                at, secs = p['frame']['at'], p['frame']['secs']
                r['still'] = [round(at + hold[0], 2), round(at + hold[1], 2)]
            left = TIMEOUT - (time.time() - t)
            if left <= 10:
                raise TimeoutError('no time left for the render')
            mp4 = os.path.join(tempfile.mkdtemp(prefix='dpass-out-'), f'{name}.mp4')
            hf_render(work, mp4, left)
            done.append({'mp4': mp4, 'at': at, 'secs': secs})
            blips += b
            if name == 'cover':
                replaced |= {w for w, m in (('chip', 'chip'), ('person', 'photobox')) if m in p['moments']}
            else:
                replaced.add('strip')        # the frame carries the strip's facts (one fact, one place)
            r.update(ok=True, at=round(at, 2), secs=round(secs, 2))
        except Exception as e:                   # the story is never held: this part stays as reel.py drew it
            r.update(ok=False, error=f'{type(e).__name__}: {str(e)[:300]}')
            print(f'designpass: {name} failed, kept as reel.py drew it: {r["error"]}', flush=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)   # the font copy never outlives the render
            r['render_secs'] = round(time.time() - t, 1)
        rec['pieces'].append(r)
    keep_back = [x for w, x in lay.items() if w not in replaced]
    tmp = video + '.dpass.mp4'
    try:
        compose(video, man, done, keep_back, tmp)
    except Exception as e:                       # the pieces could not be laid: lay back reel.py's layers alone
        rec['notes'].append(f'compose with pieces failed ({type(e).__name__}: {str(e)[:200]}); reel.py layers laid back')
        for r in rec['pieces']:
            r['ok'] = False
        done, blips = [], []
        compose(video, man, [], list(lay.values()), tmp)   # a failure here fails the job before anything is committed
    if os.path.exists(tmp):
        shutil.move(tmp, video)
    for d in done:
        shutil.rmtree(os.path.dirname(d['mp4']), ignore_errors=True)
    rec['blip_plan'] = [[round(t, 2), k] for t, k in sorted(blips)]
    rec['laid_back'] = [x['what'] for x in keep_back]
    rec['secs'] = round(time.time() - t_all, 1)
    return rec


def mix_blips(job, video, rec):
    """The kit's blips on the Reel's final sound (after the audio split), never inside speech: `speech_ok` and
    `kit_quiet` windows (0.15 s margin); none at all with `speech_keep` or `"blips": false`. A failure keeps the
    sound as it is."""
    plan_ = rec.get('blip_plan') or []
    if not plan_:
        return rec
    if job.get('blips') is False:
        rec['blips_note'] = 'job sets blips false'; return rec
    if job.get('speech_keep') and not job.get('kit_quiet'):
        rec['blips_note'] = 'speech_keep with no kit_quiet windows: no blips (never over speech)'; return rec
    quiet = [(float(w[0]), float(w[1])) for w in (job.get('speech_ok') or []) + (job.get('kit_quiet') or [])]
    heard = [(t, k) for t, k in plan_ if not any(a - 0.15 <= t <= b + 0.15 for a, b in quiet)]
    rec['blips_dropped_for_speech'] = [t for t, k in plan_ if any(a - 0.15 <= t <= b + 0.15 for a, b in quiet)]
    if not heard:
        return rec
    try:
        sys.path.insert(0, KIT)
        import blips as B
        tmp = video + '.blips.mp4'
        B.mix(video, heard, tmp)
        shutil.move(tmp, video)
        rec['blips'] = [t for t, _ in heard]
    except Exception as e:
        rec['blips_note'] = f'blips failed, sound kept: {type(e).__name__}: {str(e)[:200]}'
        print(f"designpass: {rec['blips_note']}", flush=True)
    return rec


if __name__ == '__main__':           # python3 designpass.py need <job.json>
    step, path = sys.argv[1:3]
    if step == 'need':
        sys.exit(0 if wanted(json.load(open(path))) else 1)
    raise SystemExit(f'unknown step {step!r}: need')
