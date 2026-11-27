"""Render one Reel from a job file (render runner, advisor, 20 Oct 2026).

The main session writes jobs/render/<name>.json and commits it; the render
workflow (.github/workflows/render.yml) runs `python3 templates/render_job.py
run jobs/render/<name>.json` on a GitHub runner, one job per file, and commits
the mp4, strip and sheet to cards/YYYY-MM/. The same command works on the
container, which stays the fallback.

The job file is public (the repo and the Actions logs are): it carries only
what reel() needs and where to fetch the footage. Never a token, a Postiz id or
unreleased material.

    {
      "name": "cyberpunk-2077-edgerunners-2-update-october-22",
      "out": "cards/2026-10/cyberpunk-2077-edgerunners-2-update-october-22-reel-v1.mp4",
      "footage": [{"file": "cp-er-trailer.mp4", "steam": 1091500, "trailer": "046_CP_ER", "start": 0, "seconds": 120},
                  {"file": "art.jpg", "url": "https://..."}],
      "shots": [["cp-er-trailer.mp4", 12.0, 1.7, null], ...],     # file in uploads, start, seconds, focus (null: autofocus)
      "lines": [[2, 3, [["text", {"size": 54}]]], ...],            # reel.by_shot groups: first shot, last shot, sentences
      "headline": "...", "label": "رسمي", "source": "...", "date": "20 Oct 2026",
      "theme": "spectacle", "style": "lines", "template": "split",
      "strip": [["الموعد", "22 أكتوبر"]], "credits": [[0, 9, "..."]],
      "track": ["cp-er-trailer.mp4", 12.0], "cut": true,                 # or "bed"; a stretch is checked for speech
      "speech_ok": [[3.0, 7.5, "director's statement, subtitled"]],      # only for a quote or interview Reel (Reel time)
      "speech_keep": true,                                           # speech is the news without speech_ok: no audio split
      "audio_split": false,                                          # opt out of the trailer audio split (tracksplit.py)
      "profile": "breaking",                                         # reel.PROFILES (T0, 27 Oct 2026): no picture finish, no demucs,
                                                                     # veryfast crf 20; opt-in only: a «عاجل» label does NOT select it
      "kind": "breaking",                                            # the T0 breaking card (templates/breaking.py): one image, one
                                                                     # headline, one line, no footage shots; its job format is in that module
      "sound": null, "country": null, "pace_ok": false,
      "lowres_ok": "IGN, Nintendo store, publisher press site, Steam: none above 720p",   # never a bare true (below)
      "blocky_ok": [["arms-1.mp4", 28.0, "frames 28.0 to 30.6 looked at, phone size: blocks not visible"]],
      "ground_theme": "gold",                                        # for -gfx- graphics on the living ground
      "ground_footage": ["cp-er-trailer.mp4", 40.0],                 # card-led: the game's trailer behind the cards, moving
                                                                     # (a -gfx- shot may name its own: [png, [file, start], secs, null])
      "ground_still": "gta6-key-art.jpg",                            # or the game's key art behind the cards (numgfx 'still'); a card
                                                                     # on the plain ground needs "ground": "rotate" + "ground_reason"
      "layout": "showcase",                                          # trailer news or a weak source only (9 Nov 2026): the footage at
      "showcase_reason": "the news is the trailer itself: Trailer 3", # its own width between the bands, headline up all the way,
                                                                     # lines, strip (as key facts) and credits as text below it
      "skin": "house",                                               # game skins pilot: house, scifi or fantasy (format ledger)
      "person": [["miyamoto.jpg", "شيغيرو مياموتو", "مبتكر Mario وZelda", 0.4, 3.8,      # people stories show the person
                  {"focus": [0.5, 0.3], "credit": null}]],                      # (23 Oct 2026); photo fetched as footage
      "gfx": [{"file": "x-gfx-fps.png", "kind": "fact", "label": "الأداء",   # cards drawn here with the Dubai font; a UAE price as ["aed", "25.20"]
               "value": "حتى 120", "note": "إطارًا في الثانية"}],             # (cardgfx.py), then laid on the ground
      "insert": [{"piece": "numbers", "shot": 3, "data": {...}}],    # HyperFrames over a -gfx- shot (24 Oct 2026):
                                                                     # templates/hfinsert.py; the card stays if it fails
      "frame": {"shot": 2, "offset": 0.25, "secs": 4.0,             # design pass (24 Oct 2026, templates/designpass.py):
                "data": {"platforms": [{"logo": "ps5",               # the WHERE AND HOW MUCH frame over that shot,
                                        "prices": [["الإمارات", ["aed", "239"]]]},   # replacing the strip, which
                                       {"logo": "steam", "prices": [["السعودية", "225 ريالًا"]]}],   # comes back if
                         "price_all": null, "date": "تصل في 29 أكتوبر",            # the frame fails; no story line,
                         "note": null, "arabic": false}},                          # credit or person in its span
      "kit": ["chip"],                                               # kit moments: chip (the press), photobox (the
                                                                     # first person window, t0 0, open on the cover)
      "kit_quiet": [[0.0, 3.4]],                                     # Reel seconds with voices: no blip there
      "blips": false                                                 # no UI blips on this Reel
    }

`style` (and `sound` for a Reel with no footage sound) are chosen by the main
session when it writes the job (reel.pick_style / sonic.rotate), so the
rotation ledgers stay in its commits and parallel runner jobs never fight
over them. A graphic shot (`-gfx-` in its name) is fetched like footage and
laid on the living ground (numgfx.slide), as in the batch render scripts.

    python3 templates/render_job.py run   <job.json> [--draft]   # fetch, render, strip, sheet
    python3 templates/render_job.py check <job.json>              # timeline, reading pace and speech in the track
    python3 templates/render_job.py focus <job.json>              # fill null focus from autofocus, before the sheet

Design pass (advisor memo of 24 Oct 2026, rolled out after Mohammad's "Roll out", 24 Oct 19:21Z; templates/
designpass.py has the full format): chips are 1.3 times their old size and split strip values a step larger on every
Reel (reel.CHIP_SIZE, STRIP_VALUE_SIZES, STRIP_H). `frame` and `kit` opt a job in to the HyperFrames pieces:
  - `frame`: {"shot", "offset" (s after the shot's start, default 0.25), "secs" (3 to 6, default 4), "data":
    {"platforms": [{"logo": slug in templates/assets/platforms, "prices": [[region or null, value]]}],
    "price_all", "date", "note", "arabic"}}; a value is "225 ريالًا", ["aed", "239"] (dirham sign) or
    {"unknown": "لم يُعلن السعر بعد"}. Its span must lie after the headline and clear of story lines, credits
    and person windows; the strip is left off while the frame shows its facts, and laid back if it fails.
  - `kit`: up to two of "chip" and "photobox" (photobox needs person[0] opening at 0); the frame counts as one
    moment, so a frame takes one kit moment at most. Extra or invalid moments are dropped with a note.
  - `kit_quiet` [[t0, t1]] and `speech_ok` windows keep the blips off voices; `speech_keep` without kit_quiet
    means no blips; `"blips": false` turns them off.
  The breaking profile (`"profile": "breaking"`) and the عاجل chip skip both. Each piece renders under 5 minutes or
  that part stays as reel.py drew it; the story is never held. Log: `render_job: design pass:`; render-times.json:
  `design_pass`. Without the keys, or without a HyperFrames CLI, the Reel renders as before.

Pre-render map (27 Oct 2026, templates/prerender.py; format in templates/cleanmap.py): `python3 templates/prerender.py <job>`
reads the job's footage before the job is committed and lists shots that sit on black frames, fades, frozen stretches,
a damaged-download smear, end cards or cut text, with the nearest clean start. `--write` (or `prerender.py embed`) puts
the result in the job as `clean_map`; with it, reel.quality_gate stops a shot that overlaps a bad interval, and
`"clean_nudge": true` moves such a shot to the verified start instead. `prerender_ok` [[file, t0, t1, reason]] waives an
interval someone has looked at. A job without `clean_map` renders exactly as before.

Road to Ocarina, story-beat episodes (B8, Mohammad's points on the episode 6 preview, build desk 29 Oct 2026):
  - `"intro": {"series": "gtavi", "days": N, "episode": E, "date": "YYYY-MM-DD"}` (8 Nov 2026): the «الطريق إلى GTA VI»
    intro (templates/gta_intro.py), joined the same way; days must equal the count from date to the launch date in
    gta_intro.LAUNCH, or check() stops the job.
  - `"intro": {"series": "ocarina", "days": N}`: the series intro (templates/ocarina_intro.py, «باقي N يومًا» over his
    Triforce Medley) is rendered here, where the Dubai font is, and joined ahead of the finished Reel (end card
    included) with the concat demuxer, no re-encode; the Reel keeps its own sound after it (our bed on story-beat
    episodes). The strips and checks read the joined file. Without the key nothing changes.
  - `"page_motion": {"track": <picture-track file>, "moves": [[t, pre, post, dx, dy], ...]}`: what storybeat.py prints
    as `motion` for a "look": "storybook" picture track (t in track seconds). The moves are mapped onto the cut through
    the shots taken from that file, and reel.py moves each story line with its page during the camera's glides. A line
    on screen across a move stops `check`. Without the key nothing changes.
  - `reveal`: the word-by-word reveal no longer flashes (reel.reveal_layers: the words already up stay put).

Focus is resolved on the container before the shot sheet (`focus`), so the job
carries the crop that was judged; a null left in the job is autofocused on the
runner, which may pick another subject.

Source quality (Mohammad, 24 Oct 2026, inbox 16:26Z, after the ARMS check; reel.quality_gate, run by `check` and by
reel() before the montage):
  - Bitrate floor: a source under 5 Mbps at 1080p, 3 Mbps at 720p (decodecheck.bitrate_floor scales it for other
    sizes and frame rates) is printed `lowbit` and flagged on the shot sheet. It does not stop the render.
  - Block check: a footage shot enlarged past 2x (reel.MAX_ZOOM) has its source stretch read for the 8x8 block-edge
    ratio; a peak above 1.5 (decodecheck.BLOCK_MAX) is `blocky` and stops the render unless `blocky_ok` names the
    shot as [file, start, reason], start being the shot's own start, after someone has looked at the frames.
  - `lowres_ok` names the copies searched: a string ("IGN, Nintendo store, publisher press site, Steam: none above
    720p"), a list of the sources, or {"searched": [...], "result": "..."}. A bare true stops the render.
`block_ok` stays the waiver for the smear check (decode damage), a different thing.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards as C, reel, numgfx as NG, trailer, decodecheck as DC, cardgfx as CG, breaking as BK   # noqa: E402

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'


def fetch(item):
    """One footage or art item into uploads, unless it is already there. Video is decoded in full once
    (advisor, 21 Oct 2026, after the Battlefield 1 Reel carried a damaged IGN download): any error line means one
    fresh download, and a second damaged copy stops the job. Never build shots from a file that reports errors."""
    dst = C.U + item['file']
    if os.path.exists(dst) and not item.get('_retry'):
        _decode_ok(item, dst)
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    _download(item, dst)
    _decode_ok(item, dst)
    return dst


def _decode_ok(item, dst):
    if os.path.splitext(dst)[1].lower() in reel.STILL or dst.endswith('.png'):
        return
    errs = DC.decode_errors(dst)
    if not errs:
        print(f"decode clean: {item['file']}", flush=True)
        return
    if item.get('_retry'):
        raise ValueError(f"{item['file']}: still damaged after a fresh download ({len(errs)} errors, first: {errs[0]}); "
                         'use another copy or drop the shots from the damaged stretch')
    print(f"decode errors in {item['file']} ({len(errs)}, first: {errs[0]}); downloading again", flush=True)
    os.remove(dst)
    for cached in _cache_for(dst):
        os.remove(cached)
    fetch(dict(item, _retry=True))


def _cache_for(src):
    """Picture-pass clips built from this file (reel.cached_shot names carry the file's stem)."""
    d = os.path.join(C.U, 'cache')
    stem = os.path.splitext(os.path.basename(src))[0]
    return [os.path.join(d, f) for f in os.listdir(d) if stem in f] if os.path.isdir(d) else []


def _download(item, dst):
    if 'steam' in item:
        # `trailer_id` (the number in the HLS path) picks one of several trailers sharing a name (Half-Life 2 has two)
        hls = [t['hls'] for t in trailer.steam_trailers(item['steam']) if t['name'].startswith(item['trailer'])
               and ('trailer_id' not in item or f"/{item['trailer_id']}/" in t['hls'])]
        if not hls:
            raise ValueError(f"{item['file']}: no Steam trailer starting {item['trailer']!r} on app {item['steam']}")
        stem = os.path.splitext(item['file'])[0]
        got = C.U + trailer.fetch(hls[0], stem, item.get('start', 0), item.get('seconds', 120))
        if os.path.abspath(got) != os.path.abspath(dst):
            shutil.move(got, dst)
    elif 'url' in item and item.get('stream'):
        # "stream": true (GTA VI batch, 11 Nov 2026): read only the named stretch over HTTP range requests, for a master
        # too large to download whole (Rockstar's Extended Look is 14 GB; 20 s of it reads in about 2 s). Needs "seconds".
        if 'seconds' not in item:
            raise ValueError(f"{item['file']}: \"stream\" needs \"seconds\" (and \"start\", default 0)")
        hdr = f'Referer: {item["referer"]}\r\n' if item.get('referer') else ''
        cmd = (['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(item.get('start', 0)), '-user_agent', UA]
               + (['-headers', hdr] if hdr else []) + ['-i', item['url'], '-t', str(item['seconds'])]
               + (['-map', '0:v:0', '-map', '0:a:0?', '-vf', f"scale=-2:{int(item['scale'])}", '-c:v', 'libx264',
                   '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'copy']
                  if item.get('scale') else ['-c', 'copy']) + [dst + '.part.mp4'])
        # "scale": a 4K master read at that height (the hook stretch, 23 Nov 2026), as the launch trailer's 1080p cut
        for attempt in range(3):                  # a range read can end early ("Stream ends prematurely"); try again
            try:
                subprocess.run(cmd, check=True, timeout=600)
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if attempt == 2:
                    raise
                print(f"stream read of {item['file']} failed, attempt {attempt + 1}; trying again", flush=True)
                time.sleep(5)
        os.replace(dst + '.part.mp4', dst)
    elif 'url' in item:
        hdr = {'User-Agent': UA}
        if item.get('referer'):                   # IGN's asset hosts refuse requests without their own referer
            hdr['Referer'] = item['referer']
        req = urllib.request.Request(item['url'], headers=hdr)
        with urllib.request.urlopen(req, timeout=120) as r, open(dst + '.part', 'wb') as f:
            shutil.copyfileobj(r, f)
        os.replace(dst + '.part', dst)
        if 'start' in item or 'seconds' in item:   # keep only the stretch the job names, so shot times match
            cut = dst + '.cut' + os.path.splitext(dst)[1]
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(item.get('start', 0)), '-i', dst]
                           + (['-t', str(item['seconds'])] if 'seconds' in item else []) + ['-c', 'copy', cut], check=True)
            os.replace(cut, dst)
    elif 'frame_of' in item:                      # a still of the game's footage for the people window when the slip had
        src = C.U + item['frame_of'][0]           # no official photo (audit 21 Nov 2026, item 1): a bright, non-black frame
        dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                                   capture_output=True, text=True, check=True).stdout or 0)
        at = item['frame_of'][1] if len(item['frame_of']) > 1 and item['frame_of'][1] is not None else None
        from PIL import Image, ImageStat
        for t in ([at] if at is not None else []) + [dur * k for k in (0.35, 0.5, 0.62, 0.25, 0.75)]:
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1',
                            '-q:v', '2', dst], check=True)
            lum = ImageStat.Stat(Image.open(dst).convert('L')).mean[0] / 255
            if 0.12 <= lum <= 0.85:
                break
    elif 'repo' in item:                          # a graphic or still committed to this repo (live/YYYY-MM-DD/...)
        src = os.path.join(ROOT, item['repo'])
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:                                     # outside the runner's sparse checkout: read it from the commit
            with open(dst, 'wb') as f:
                subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + item['repo']], stdout=f, check=True)
    else:
        raise ValueError(f"{item['file']}: footage needs steam, url or repo")


_NUDGED = set()


def clean_nudge(job, rows):
    """Pre-render map (templates/prerender.py): with `"clean_nudge": true` and a `clean_map` in the job, a footage shot
    whose span overlaps a bad interval starts at the start prerender verified instead (same length, same focus). Any
    other job gets `rows` back untouched."""
    cm = job.get('clean_map')
    if not (cm and job.get('clean_nudge')):
        return rows
    import cleanmap as CM
    out, moved = CM.nudge(cm, [tuple(r) for r in rows])
    for i, old, new in moved:
        if (job.get('name'), i, old) not in _NUDGED:
            _NUDGED.add((job.get('name'), i, old))
            print(f'render_job: clean map: shot {i} moved from {old} s to {new} s (clean_nudge)', flush=True)
    return [list(r) for r in out] if moved else rows


def shots(job, draft=False, build=True):
    """The job's shots as reel() takes them: autofocus where focus is null, graphics on the living ground."""
    out, t = [], 0.0
    reel.NOBARS.update(job.get('nobars', []))   # files whose dark edges are picture, not letterbox (a framed picture track)
    rows = clean_nudge(job, job['shots'])
    for i, (f, start, secs, fo) in enumerate(rows):
        if f.endswith('.png') and '-gfx-' in f:
            clip = f"{NG.SUB}/{job['name']}-{i}.mp4"
            if build:
                os.makedirs(C.U + NG.SUB, exist_ok=True)
                gf = job.get('ground_footage')    # [file, start]: the game's own trailer behind the card (advisor, 20 Oct 2026)
                if isinstance(start, list):       # per card: ["x-gfx-a.png", [file, start], secs, null] (multi-game numbers)
                    gf = start
                if gf and job.get('ground_seek') != 'fixed' and not draft:   # D: the calmest window of the named stretch
                    import shotgate as SG          # (adv-20261115-one-render-server-checks, 15 Nov 2026)
                    span = float(gf[2]) if len(gf) > 2 else SG.GROUND_SPAN
                    seek, sc, named = SG.ground_pick(gf[0], float(gf[1]), span, secs, t0=t)
                    print(f"render_job: ground for card {i} ({f}): {gf[0]} at {seek:.2f} s, the calmest {secs:.1f} s of "
                          f"{float(gf[1]):.2f} to {float(gf[1]) + span:.2f} s (busy {sc}, the seek as written "
                          f"{float(gf[1]) + t:.2f} s: {named})", flush=True)
                    gf = [gf[0], seek - t]
                gs = job.get('ground_still')      # the game's key art behind the card, blurred and dimmed (9 Nov 2026)
                src = card_stages(job, f, secs)   # the figure counts up, rows come in (on in numbers and list, 12 Nov 2026)
                NG.slide(src, secs, job.get('ground_theme', job['theme']), C.U + clip,
                         seed=sum(map(ord, job['name'])), t0=t, fast=draft,
                         footage=(C.U + gf[0], gf[1]) if gf else None,
                         still=C.U + gs if gs and not gf else None)
            out.append((clip, 0.0, secs, 0.5))
        elif job.get('template') == 'stills' and os.path.splitext(f)[1].lower() in reel.STILL and not isinstance(fo, list):
            # the stills template (formats.py, 14 Oct 2026): a 3% push-in clip per image, hard cuts (job "cut": true);
            # fo is the crop position 0 (left) to 1 (right). Only jobs with template "stills" take this path.
            if build:
                clip = reel.stills_clips([f], f"{job['name']}-{i}", secs, focus=0.5 if fo is None else fo, fast=draft)[0][0]
            else:
                clip = f"{reel.STILLS}/{job['name']}-{i}-still-0-{reel.STILLS_VER}.mp4"
            out.append((clip, 0.0, secs, 0.5))
        elif os.path.splitext(f)[1].lower() in reel.STILL:   # an official still: (art, null, secs, [from, to]) pans
            out.append((f, None, secs, tuple(fo) if isinstance(fo, list) else (0.5 if fo is None else fo)))
        else:
            if fo is None and build:
                fo = reel.autofocus(f, start, secs)
            if isinstance(fo, list):              # [[offset, focus], ...] from a job file
                fo = [tuple(k) for k in fo]
            out.append((f, start, secs, 0.5 if fo is None else fo))
        t += secs - reel.X
    return out


def card_stages(job, f, secs):
    """The -gfx- shot `f` as numgfx.slide takes it: the card's file in uploads, or its stages [(png, from second)] when
    the card moves (cardgfx.animated: on by default in the numbers and list templates; adv-20261112-qc-notes-become-
    failures item 4). The stages are drawn next to the card in uploads; the card itself is the last stage."""
    items = {g.get('file'): g for g in job.get('gfx') or []}
    item = items.get(f)
    if not item or job.get('profile') == 'breaking' or not CG.animated(item, job):
        return C.U + f
    start = 0
    names = [str(sh[0]) for sh in job.get('shots') or []]
    i = names.index(f) if f in names else 0
    prev = items.get(names[i - 1]) if i else None     # a countdown split over two cards carries on from the first
    if item.get('kind') == 'ranking' and prev and prev.get('kind') == 'ranking' and prev.get('rows') == item.get('rows'):
        start = int(prev.get('show') or len(prev['rows']))
    st = CG.stages(item, C.U + f, job.get('ground_theme', job['theme']), secs, start=start)
    if st:
        print(f"render_job: card {f}: {len(st)} stages ({'rows in' if item.get('kind') == 'ranking' else 'count-up'})",
              flush=True)
    return st or C.U + f


def sound_for(job, out, draft=False):
    """(sound for reel(), the label qc.json records) (adv-20261112-sound-by-code item 3). With a trailer track the
    footage carries its own sound (the job's `sound` only names the end card's flavour, as before): "trailer", or
    "trailer-voiced" when its speech is kept. With no track the server picks the bed: the chip's flavour from
    ig_ar.SOUNDS (عاجل breaking, متوفر الآن launch, أرقام stats, retro), the tribute's calm neon_c, an occasion or retro
    flavour the job names; otherwise the everyday bed rested longest in templates/assets/bed-ledger.json, whatever the
    job says (an everyday bed is never left to the default). The ledger entry is written to $RUNNER_TEMP/bed.json for the
    commit step, which appends it to the fresh ledger; a draft takes no ledger entry."""
    import ig_ar as _G
    import sonic as _S
    tr = job.get('track')
    if tr and tr != 'bed':
        voiced = bool(job.get('speech_ok') or job.get('speech_keep'))
        return job.get('sound'), 'trailer-voiced' if voiced else 'trailer'
    named = job.get('sound')
    if job.get('tribute'):
        pick = named or 'neon_c'
    elif _G.SOUNDS.get(job.get('label')):
        pick = _G.SOUNDS[job['label']]
    elif named and named not in _S.EVERYDAY:
        pick = named
    elif draft:
        pick = 'neon'
    else:
        pick = _S.rotate(os.path.basename(out))
        if os.environ.get('RUNNER_TEMP'):
            json.dump([os.path.basename(out), pick], open(os.path.join(os.environ['RUNNER_TEMP'], 'bed.json'), 'w'))
    why = str(job.get('bed_reason') or '').strip()
    return pick, f'bed:{pick}' + (f' ({why})' if why else '')


def focus(job, path):
    """Fill every null focus with reel.autofocus and write the job back, so the
    runner crops exactly what the shot sheet was judged on (20 Oct 2026: on the
    first runner test, autofocus there chose other subjects on three shots)."""
    if job.get('kind') == 'breaking':          # one image, framed by the job's own focus (breaking.py)
        return job
    for item in job.get('footage', []):
        fetch(item)
    for sh in job['shots']:
        if sh[3] is None and not (sh[0].endswith('.png') and '-gfx-' in sh[0]) and os.path.splitext(sh[0])[1].lower() not in reel.STILL:
            sh[3] = [list(k) for k in reel.autofocus(sh[0], sh[1], sh[2])]
    json.dump(job, open(path, 'w'), ensure_ascii=False, indent=1)
    return job


def strip_items(job):
    """[(label, value)] for reel's strip; a value written as ["aed", "185"] in JSON becomes the ('aed', '185') price tuple."""
    return [(l, tuple(v) if isinstance(v, list) else v) for l, v in job['strip']]


def place(job):
    return reel.by_shot([(a, b, [tuple(x) if isinstance(x, list) else x for x in texts]) for a, b, texts in job['lines']],
                        first=0.0 if job.get('layout') == 'showcase' else 3.6)


def profile_of(job):
    """reel()'s profile for a job (T0, 27 Oct 2026): "profile" exactly as written in the job, opt-in only. A job without
    the key, the «عاجل» label included, renders the standard way, exactly as before (Mohammad has not yet seen the
    breaking profile on a live Reel; the label default was removed in review the same day). "standard" or null is the
    standard render."""
    p = job.get('profile')
    if p in (None, 'standard'):
        return None
    if p not in reel.PROFILES:
        raise ValueError(f'profile {p!r}: one of {", ".join(reel.PROFILES)} or "standard"')
    return p


def page_moves(job, starts):
    """The job's `page_motion` (storybeat.py's `motion`, track seconds) as reel()'s `page`: [(t, pre, post, dx, dy)] in
    Reel seconds, through the shots cut from the picture track. A move at no shot of that file is dropped, with a note."""
    pm = job.get('page_motion')
    if not pm:
        return None
    rows = clean_nudge(job, job['shots'])
    out = []
    for t, pre, post, dx, dy in pm['moves']:
        hit = None
        for i, (f, s0, secs, _) in enumerate(rows):
            if f != pm['track'] or s0 is None or i >= len(starts):
                continue
            if abs(t - s0) < 0.02:
                hit = (i, s0)
                break
            if hit is None and s0 < t < s0 + secs:
                hit = (i, s0)
        if hit is None:
            print(f'render_job: page move at {t} s of {pm["track"]} is in no shot; dropped', flush=True)
            continue
        out.append((round(starts[hit[0]] + t - hit[1], 3), float(pre), float(post), dx, dy))
    return out


def _starts(job):
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        return reel.timeline(shots(job, build=False))
    finally:
        reel.X = keep


GFX_SMEAR_PAD = 1.0          # seconds either side of our own card: its crossfade, and the smear flag reads 1 s windows


def gfx_spans(job):
    """[(t0, t1, reason)] in Reel time for each of our own -gfx- cards and its crossfades (adv-20261110-one-render-per-
    reel, item E). The smear check reads long straight edges; our pixel-art and price cards are made of them, so the flag
    on the Warhammer Survivors card crossfade (12.0 to 12.7 s) was waived by hand. These spans are exempt from the
    smear flag on the finished Reel; decode errors are never exempt."""
    try:
        st, _end = _starts(job)
    except Exception:                            # noqa: BLE001
        return []
    out = []
    for i, sh in enumerate(job.get('shots') or []):
        if i < len(st) and str(sh[0]).endswith('.png') and '-gfx-' in str(sh[0]):
            out.append((round(max(0.0, st[i] - GFX_SMEAR_PAD), 2), round(st[i] + float(sh[2]) + GFX_SMEAR_PAD, 2),
                        'our own card and its crossfade'))
    return out


def showcase_of(job):
    """The showcase reason of a job with "layout": "showcase" (reel.showcase_reason stops a missing or bare one), else
    None. Any other layout value stops: there is one."""
    lay = job.get('layout')
    if lay in (None, '', 'fill'):
        if job.get('showcase_reason'):
            raise SystemExit('render_job: showcase_reason without "layout": "showcase"')
        return None
    if lay != 'showcase':
        raise SystemExit(f'render_job: layout {lay!r}: "showcase" or none')
    try:
        return reel.showcase_reason(job.get('showcase_reason') or True)
    except ValueError as e:
        import softgate as SG_
        if not SG_.soft(job):
            raise SystemExit(f'render_job: {e}')
        why = 'the source fails the quality gate in a full-frame crop (picture ladder step b, set by the server)'
        SG_.warn('showcase', f'{e}; the server named the reason itself: {why}')
        return reel.showcase_reason(why)


def series(job):
    """A series episode (a job with a series intro, gtavi or ocarina) keeps the series' own look and is outside the
    rotation, like Famitsu: a batch of episodes renders back to back in one theme (GTA VI batch, 11 Nov 2026)."""
    return isinstance(job.get('intro'), dict) and bool(job['intro'].get('series'))


def look(job):
    """Theme and style for this render on the live path (no three in a row, 9 Nov 2026): the job's style, or the rested
    one when that would make three in a row (looks.py); a theme that would make three in a row stops here."""
    import looks
    if job.get('kind') in ('breaking', 'famitsu') or job.get('skin') not in (None, 'house') or series(job):
        return job.get('style')
    style, problems = looks.resolve(job)
    if problems:
        import softgate as SG_
        if not SG_.soft(job):
            raise SystemExit('render_job: ' + '; '.join(problems))
        prev = looks.last(2, exclude=job.get('name'))
        new = looks.rested('theme', prev, {job.get('theme')}) or 'emerald'
        SG_.warn('look', '; '.join(problems) + f'; rendering with theme {new}, the one rested longest')
        job['theme'] = new
    return style


def check(job, collect=None):
    """Every pre-render check. Raises at the first failure; with `collect` (a list) each failing stage is appended there
    as a string and the rest still run, so one pass reports everything (adv-20261117-gates-fix-not-refuse A)."""
    if job.get('kind') == 'breaking':
        return BK.check(job)
    import softgate as SG_
    if SG_.soft(job):                          # never refuse (card A): every stage runs, refusals become warnings
        reel.SOFT = True
        if SG_.fact_flag(job):
            msg = f'fact flag in the brief: {SG_.fact_flag(job)}'
            if collect is None:
                raise SystemExit('render_job: ' + msg)
            collect.append(msg)
        return _check_all(job, collect if collect is not None else [])
    if collect is not None:
        return _check_all(job, collect)
    look(job)
    if job.get('intro') is not None:
        _intro_mod(job['intro']).check(job['intro'])
    if job.get('template') == 'reviewscores':  # totals read from the pages and recent, own-scale scores, short quotes
        import reviewscores as RS             # (adv-20261104-review-scores-template, 4 Nov 2026)
        errs = RS.check_job(job)
        if errs:
            raise SystemExit('render_job: review scores: ' + '; '.join(errs))
    reel.CLEAN_MAP = job.get('clean_map')       # pre-render map (templates/prerender.py); None changes nothing
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        # the runner stops on a letterboxed or small clip, a blocky enlarged shot or a bare lowres_ok; catch it here
        # first (source quality, 24 Oct 2026); bitrate flags are printed. Shots not in uploads are skipped.
        show = showcase_of(job)               # a showcase job names its reason; nothing is enlarged to fill (9 Nov 2026)
        reel.quality_gate(shots(job, build=False), job.get('lowres_ok'), job.get('blocky_ok'), boxed=bool(show))
        st, end = reel.timeline(shots(job, build=False))
        reel.check_reading(place(job)(st, end), end)
    finally:
        reel.X = keep
    if job.get('page_motion'):                 # a line across a page move stops here (storybook look, B8)
        lines = place(job)(st, end)
        reel.page_positions([[(f'l{i}', a, min(z, end))] for i, (_, a, z, _) in enumerate(lines)], page_moves(job, st))
        print(f"page motion: {len(page_moves(job, st))} moves on the cut", flush=True)
    speech_check(job, end)
    if job.get('kind') != 'breaking':
        shot_gate(job)                          # B and C (adv-20261115-one-render-server-checks)
    first_frame_check(job)
    cover_picture_check(job)
    card_art_check(job)
    import fillcheck as FC                     # footage full frame, never a box in a blurred fill (adv-20261030-one-piece-fortnite-hold)
    FC.check(job, C.U, st)
    import sfxplan as SF                       # sound effects match the picture (adv-20261030-sfx-mismatch, 30 Oct 2026)
    SF.check(job, st, place(job)(st, end), profile_of(job))
    if job.get('kit') or job.get('frame'):     # what the design pass will do, or drop, on the runner
        import designpass as DP
        keep = reel.X
        if job.get('cut'):
            reel.X = 0.04
        try:
            st, end2 = reel.timeline(shots(job, build=False))
            p = DP.plan(job, st, end2, place(job)(st, end2))
        finally:
            reel.X = keep
        print(f"design pass: moments {p['moments']}, frame {'at %.2f s for %.1f s' % (p['frame']['at'], p['frame']['secs']) if p['frame'] else 'none'}"
              + ''.join(f'; {n}' for n in p['notes']), flush=True)
    return end


def _check_all(job, errs):
    """check() stage by stage, every failure kept (item A)."""
    import softgate as SG_

    def stage(name, fn, *a):
        try:
            return fn(*a)
        except (Exception, SystemExit) as e:   # noqa: BLE001
            if SG_.soft(job):                  # never refuse (card A): a warning, the Reel ships
                SG_.warn(name, f'{type(e).__name__}: {e}')
            else:
                errs.append(f'{name}: {e}')
            return None
    stage('look', look, job)
    if job.get('intro') is not None:
        stage('intro', lambda: _intro_mod(job['intro']).check(job['intro']))
    if job.get('template') == 'reviewscores':
        import reviewscores as RS
        for e in RS.check_job(job) or []:
            (SG_.warn('review scores', e) if SG_.soft(job) else errs.append('review scores: ' + e))
    reel.CLEAN_MAP = job.get('clean_map')
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        show = showcase_of(job)
        stage('source quality', reel.quality_gate, shots(job, build=False), job.get('lowres_ok'), job.get('blocky_ok'), bool(show))
        st, end = reel.timeline(shots(job, build=False))
        stage('reading', reel.check_reading, place(job)(st, end), end)
    finally:
        reel.X = keep
    stage('speech', speech_check, job, end)
    stage('shot gate', shot_gate, job)        # applies its fixes first; refuses only what it could not fix
    st, end = _starts(job)                     # the fixes may have changed the timeline
    stage('first frame', first_frame_check, job)
    stage('cover', cover_picture_check, job)
    stage('card art', card_art_check, job)
    import fillcheck as FC
    stage('fill', FC.check, job, C.U, st)
    stage('trailer news', trailer_news_report, job)   # new trailer, DLC, update: footage dated after the news (28 Nov)
    import sfxplan as SF
    stage('sound effects', SF.check, job, st, place(job)(st, end), profile_of(job))
    return end


def auto_shots(job):
    """Fill every automatic shot slot (templates/autoshots.py) from the clean stretches of the fetched footage."""
    import autoshots as AS
    AS.expand(job)
    if not job.get('shots_auto'):
        return
    import autofix as AF
    import time as _t
    n0 = len(AF.LOG)
    t0 = _t.time()
    try:
        try:
            left = AS.fill(job)
        except (Exception, SystemExit) as e:   # noqa: BLE001  (17 Nov: an IndexError in the read stopped a render)
            import softgate as SG_
            if not SG_.soft(job):
                raise
            SG_.warn('shot read', f'{type(e).__name__}: {e}; every automatic slot falls back to evenly spaced shots')
            left = [{'shot': i, 'detail': f'shot {i}: shot read failed', 'autofix': 'evenly spaced fallback'}
                    for i in job.get('shots_auto') or []]
    finally:                                   # adv-20261117-server-speed-for-p2 A: the read's seconds go to qc.json
        rd = {'secs': round(_t.time() - t0, 1),
              'files': {f: {'secs': r.get('read_secs'), 'cached': bool(r.get('cached')), 'stages': r.get('stages'),
                            'incomplete': r.get('incomplete')} for f, r in AS.READ.items()}}
        print('render_job: shot read: ' + json.dumps(rd), flush=True)
    if len(AF.LOG) > n0:
        AF.save_log(os.environ.get('AUTOFIX_JSON'))
        if os.environ.get('AUTOFIX_JOB'):
            json.dump(job, open(os.environ['AUTOFIX_JOB'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for p in left:
        print('autoshots: ' + p['detail'] + ' (' + p['autofix'] + ')', flush=True)
    if left:
        import softgate as SG_
        if not SG_.soft(job):
            raise SystemExit(f'autoshots: {len(left)} shot slot{"s" if len(left) > 1 else ""} with no clean stretch (above)')
        auto_fallback(job, [p['shot'] for p in left])
        # no clean stretch for a slot: the whole frame instead of a guessed crop (Mohammad, 20 Nov 2026, 22:20), but only
        # for a source that cannot fill 9:16 at up to 2x (fill, not band: Mohammad, 27 Nov 2026, shot rule 3)
        band_or_fill(job, f'the shot scan found no clean stretch for {len(left)} slot(s)')
    print(f'autoshots: {len(AF.LOG) - n0} shot time(s) picked on the server', flush=True)


def _video_dur(f):
    try:
        return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                                              'csv=p=0', C.U + f], text=True).strip())
    except (subprocess.CalledProcessError, ValueError, OSError):
        return 0.0


RESPREAD_OVERLAP = 0.5      # seconds two shots of one file may share before the later one is moved


FILL_ROWS = 960            # a 16:9 source with this many picture rows fills 1920 at 2x (reel.MAX_ZOOM)


def can_fill(job):
    """True when every footage video of the job can fill 9:16 at up to 2x: picture rows of FILL_ROWS or more after the
    letterbox, at least as wide as 16:9 is tall (shot rule 3, 27 Nov 2026)."""
    vids = [it['file'] for it in job.get('footage') or [] if str(it.get('file', '')).lower().endswith(('.mp4', '.mov', '.mkv', '.webm', '.m4v'))]
    if not vids:
        return False
    try:
        import shotgate as SG
        for f in vids:
            w, h = reel._src_size(C.U + f)
            rows, boxed = SG._letterbox_rows(f, 5.0, 2.0, h)
            if (rows if boxed else h) < FILL_ROWS or w < (rows if boxed else h) * 1.7:
                return False
        return True
    except Exception:                          # noqa: BLE001  no read: the old fallback
        return False


def band_or_fill(job, why):
    """Fill, not band (Mohammad, 27 Nov 2026, shot rule 3): the GTA VI car-physics Reel took the band layout because
    the scan stopped at its cap, although its 1080p trailer fills 9:16 at 1.78x. The showcase (band) layout is for a
    source that cannot fill; one that can keeps the crop and its shots (from the library or evenly spaced, each moved off
    black, slates and blocked stretches)."""
    import softgate as SG_
    if can_fill(job):
        SG_.ladder('picture', 'reel', 'a', f'fill, not band: {why}, but the source fills 9:16 at up to 2x; crop kept')
        return False
    return SG_.showcase_fallback(job, why)


def shot_rules(job):
    """Shot rules (Mohammad, 27 Nov 2026): the shot matches its line (templates/subjectmatch.py), then no blocked
    stretch on screen (templates/blocked.py). Autofix only; each step is on the picture ladder."""
    import softgate as SG_
    import blocked as B
    import autoshots as AS
    if job.get('blocked_add'):                 # a director's or builder's fix: the stretch joins the ledger now
        B.add(job['blocked_add'])
    reads = dict(AS.READ)
    for it in job.get('footage') or []:        # the end slate and ratings card: no frame read needed (27 Nov 2026)
        f = it.get('file', '')
        if str(f).lower().endswith(('.mp4', '.mov', '.mkv', '.webm', '.m4v')) and not it.get('stream'):
            d = _video_dur(f)
            if d > TAIL_SKIP + 6:
                B.EXTRA[f] = [(d - TAIL_SKIP, d + 1.0, 'end slate')]
    try:
        import subjectmatch as SM
        SG_.guarded('shot matches line', SM.run, job, C.U, reads, frame_clean, _video_dur, SG_.ladder)
    except ImportError:
        pass
    first = list(job['shots'][0]) if job.get('shots') and isinstance(job['shots'][0], list) else None

    def prefer(f, i):
        try:
            import subjectmatch as SM
            import variety
            cur, subjects = variety.curated(job.get('game') or job.get('game_short'))
            cls, named = SM.wants(SM.line_text(job, i), subjects)
            out = []
            for s_ in cur:
                if B.romance(s_):
                    continue
                it = next((x for x in job.get('footage') or [] if x.get('file') == f and (x.get('url') == s_['url']
                           or (x.get('repo') and x['repo'] in (s_.get('same') or [])))), None)
                tags = set(s_.get('tags') or [])
                if it and (tags & named or any(SM.TAG_CLASS.get(t) in cls for t in tags) or tags & {'action', 'car', 'city'}):
                    off = float(it.get('start') or 0.0) if it.get('stream') else 0.0
                    out.append((float(s_['start']) - off, s_.get('focus')))
            return out
        except Exception:                      # noqa: BLE001
            return []
    B.clear(job, _video_dur, frame_clean, reads, prefer, SG_.ladder)
    if first and job.get('shots') and job['shots'][0] != first:
        track_from_first_shot(job)             # the trailer sound follows the new first shot


def trailer_news_report(job):
    """render_job.check: footage older than the announcement on trailer news (Mohammad, 28 Nov 2026). Printed only; the
    autofix (trailer_news) runs in the render. Never a refusal."""
    try:
        import newfootage as NF
        old = NF.stale(job)
    except Exception as e:                     # noqa: BLE001
        print(f'trailer news: not checked ({e})', flush=True)
        return
    for f, d, how in old:
        print(f'trailer news: {f} is from {d} ({how}), older than the story: the render takes the new trailer, '
              'official stills of the new content, or credits it as the base game', flush=True)


def trailer_news(job):
    """Trailer news shows the new trailer (Mohammad, 28 Nov 2026; templates/newfootage.py): footage older than the
    announcement is replaced by the new trailer, else official stills of the new content, else credited as the base
    game. Runs before the shot scan."""
    import newfootage as NF
    import softgate as SG_
    story = None
    p = os.path.join(ROOT, 'newsroom', 'stories', str(job.get('story') or '') + '.json')
    if os.path.exists(p):
        try:
            story = json.load(open(p, encoding='utf-8'))
        except ValueError:
            story = None
    step = NF.fix(job, C.U, story, fetch, SG_.ladder, SG_.warn)
    if step:
        print(f'render_job: trailer news: step {step}', flush=True)
    return step


def respread(job):
    """Never the same moment twice (Mohammad, 20 Nov 2026): Ace Combat 8 rendered twelve shots at 3.07 s and GTA VI CDPR
    fourteen at 0.0 s, after a capped scan left every automatic slot on its file's picture start. A footage shot that
    repeats or overlaps (more than RESPREAD_OVERLAP) a shot already placed on the same file moves to the evenly spaced
    position on that file furthest from every shot already placed; when the file has no free room, it moves to the job's
    other footage videos the same way. Logged on the picture ladder; shots the builder spread out are never touched."""
    import softgate as SG_
    shots = job.get('shots') or []
    vids = [it['file'] for it in job.get('footage') or [] if str(it.get('file', '')).lower().endswith(('.mp4', '.mov', '.mkv', '.webm', '.m4v'))]
    if not vids:
        return []
    durs = {}

    def dur(f):
        if f not in durs:
            durs[f] = _video_dur(f) or 0.0
        return durs[f]

    placed = {}
    moved = []
    for i, sh in enumerate(shots):
        if not (isinstance(sh, list) and len(sh) > 2 and sh[0] in vids and isinstance(sh[1], (int, float))):
            continue
        a, b = float(sh[1]), float(sh[1]) + float(sh[2])
        if any(min(b, y) - max(a, x) > RESPREAD_OVERLAP or abs(a - x) < 0.05 for x, y in placed.get(sh[0], [])):
            moved.append(i)
        else:
            placed.setdefault(sh[0], []).append((a, b))
    if not moved:
        return []
    import autoshots as AS
    out = []
    for i in moved:
        sh = shots[i]
        secs = float(sh[2])
        best = None
        spare = None                            # the first free moment anywhere, used only when no file has a clean one
        for f in [sh[0]] + [v for v in vids if v != sh[0]]:
            d = dur(f)
            r = AS.READ.get(f) or {}
            v0 = float(r.get('picture_start') or min([x for x, _ in placed.get(f, [])] or [0.0]))
            hi = d - 0.4 - secs
            if d <= 0 or hi <= v0 + 0.3:
                continue
            taken = placed.get(f, [])
            cands = [v0 + 0.3 + (hi - v0 - 0.3) * k / 23 for k in range(24)]
            free = [c for c in cands if all(min(c + secs, y) - max(c, x) <= 0 for x, y in taken)]
            if free:
                free.sort(key=lambda c: -min([abs(c - x) for x, _ in taken] or [d]))
                spare = spare or (f, round(free[0], 2))
                c = next((c for c in free[:16] if frame_clean(f, c, secs, d)[0]), None)   # 21 Nov: never onto black or a slate
                if c is not None:
                    best = (f, round(c, 2))
                    break                       # else the job's other footage before a blind moment (Persona 6 teaser)
        best = best or spare
        if not best:
            continue
        f, st = best
        sh[0], sh[1] = f, st
        if len(sh) > 3:
            sh[3] = None                        # the old focus was for another moment; autofocus picks the new one
        placed.setdefault(f, []).append((st, st + secs))
        for key in ('cut_ok', 'drift_ok'):
            job.setdefault(key, []).append([f, st, 'never the same moment twice: respread after the scan'])
        SG_.ladder('picture', i, 'a', f'{f} at {st} s: moved off a repeated moment (respread)')
        out.append(i)
    if out:
        print(f'render_job: respread: {len(out)} repeated shot(s) moved to free moments: {out}', flush=True)
    return out


TAIL_SKIP = 9.0             # a trailer's last seconds are its end slate and ratings card (audit 21 Nov, item 5)
FRAME_BUDGET = 30.0         # seconds of frame checks per job; past it the fallbacks pick as before (Ace Combat 8 replay time)
_FRAME_SPENT = [0.0]


def frame_clean(f, st, secs, dur=None):
    """(True, '') when two frames of the stretch are a picture: not near-black, not blown out, not a flat card, not the
    end slate, and without two or more printed words in the 9:16 window (tesseract, when installed). The cheap check the
    blind fallbacks (auto_fallback, respread) never had: 17 extra renders on 18 to 21 Nov were shots on black fades,
    slates, logos, end cards and text cards (audit 21 Nov 2026, item 5, cause 1)."""
    if _FRAME_SPENT[0] >= FRAME_BUDGET:
        return True, 'not checked: frame check budget spent'
    t_start = time.time()
    try:
        return _frame_clean(f, st, secs, dur)
    finally:
        _FRAME_SPENT[0] += time.time() - t_start


def _frame_clean(f, st, secs, dur=None):
    try:
        from PIL import Image, ImageStat
        import io
        path = C.U + f
        dur = dur or _video_dur(f) or 0.0
        if dur and st + secs > dur - TAIL_SKIP:
            return False, 'end slate'
        for n, t in enumerate((st + 0.25, st + max(0.3, secs - 0.3))):
            out = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.2f}', '-i', path, '-frames:v', '1',
                                  '-vf', 'scale=480:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                                 capture_output=True, timeout=20).stdout
            im = Image.open(io.BytesIO(out)).convert('L')
            st_ = ImageStat.Stat(im)
            mean, sd = st_.mean[0] / 255, st_.stddev[0] / 255
            if mean < 0.08:
                return False, f'near-black at {t:.1f} s'
            if mean > 0.9:
                return False, f'white at {t:.1f} s'
            if sd < 0.05:
                return False, f'flat card at {t:.1f} s'
            if n == 1 and shutil.which('tesseract'):   # printed text on the second frame only: one OCR per moment
                w, h = im.size
                cw = int(h * 9 / 16)
                crop = im.crop(((w - cw) // 2, 0, (w + cw) // 2, h)).resize((cw * 2, h * 2))
                buf = io.BytesIO()
                crop.save(buf, 'PNG')
                txt = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '11'], input=buf.getvalue(),
                                     capture_output=True, timeout=20).stdout.decode('utf-8', 'ignore')
                words = [x for x in re.findall(r'[A-Za-z]{3,}', txt)]
                if len(words) >= 2:
                    return False, f'printed text at {t:.1f} s ({" ".join(words[:3])})'
        return True, ''
    except Exception as e:                      # noqa: BLE001  a check that cannot run never blocks the shot
        return True, f'not checked: {e}'


def clean_near(f, st, secs, v0, dur, taken=()):
    """st, or the nearest start within 12 s (2 s steps, either side) whose stretch passes frame_clean and overlaps no
    shot already placed; st itself when none does (the shot gate and the ladder still run after)."""
    def free(c):
        return all(c + secs <= a or c >= b for a, b in taken)
    for off in [0] + [s * k for k in range(2, 13, 2) for s in (1, -1)]:
        c = st + off
        if c < v0 + 0.3 or (dur and c + secs > dur - 0.4) or not free(c):
            continue
        ok, why = frame_clean(f, c, secs, dur)
        if ok:
            if off:
                print(f'render_job: fallback shot {f} moved {st:.2f} -> {c:.2f} s (frame check)', flush=True)
            return c
    return st


SHADE_LUMA = 0.60          # mean brightness of the lines' band in the source above which a line takes the soft shade


def auto_shade(job):
    """A story line over bright or flat footage gets reel.line_layer's soft indigo shade, in the job, before the render
    (audit 21 Nov 2026, item 5, cause 3: the Burning Sword price line on bright fire and Expelled from Paradise's pale
    art each took a second render). The band read is the lines' place in the 9:16 window (57 to 77% of the height),
    two frames per line, on the line's first shot. Lines the builder set (top, shade, showcase) are left alone."""
    from PIL import Image, ImageStat
    import io
    shots_ = job.get('shots') or []
    done = []
    for g, (a, b, texts) in enumerate(job.get('lines') or []):
        if not (isinstance(a, int) and a < len(shots_)):
            continue
        sh = shots_[a]
        if not (isinstance(sh, list) and len(sh) > 2 and isinstance(sh[1], (int, float)) and not str(sh[0]).endswith('.png')):
            continue
        lum = []
        for t in (float(sh[1]) + 0.3, float(sh[1]) + max(0.4, float(sh[2]) - 0.3)):
            out = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.2f}', '-i', C.U + sh[0], '-frames:v', '1',
                                  '-vf', 'scale=480:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                                 capture_output=True, timeout=20).stdout
            if not out:
                continue
            im = Image.open(io.BytesIO(out)).convert('L')
            w, h = im.size
            cw = int(h * 9 / 16)
            band = im.crop(((w - cw) // 2, int(h * 0.57), (w + cw) // 2, int(h * 0.77)))
            lum.append(ImageStat.Stat(band).mean[0] / 255)
        if not lum or max(lum) < SHADE_LUMA:
            continue
        for k, x in enumerate(texts):
            if isinstance(x, str):
                texts[k] = x = [x, {}]
            kw = x[1] if len(x) > 1 else {}
            if len(x) < 2:
                x.append(kw)
            if any(kw.get(q) for q in ('top', 'shade')):
                continue
            kw['shade'] = True
            done.append(g)
    if done:
        import softgate as SG_
        SG_.ladder('text', 'reel', 'a', f'soft shade under line group(s) {sorted(set(done))}: bright footage behind them')
        print(f'render_job: line shade: groups {sorted(set(done))} over bright footage take the soft shade', flush=True)
    return done


def auto_fallback(job, slots):
    """Never refuse (card A): an automatic slot the read could not fill takes an evenly spaced stretch of its file,
    after the picture start, clear of the stretches already used, with the clean-stretch checks waived (picture ladder
    step a, a crop; the shot gate then moves a letterboxed or drifting shot down the ladder)."""
    import softgate as SG_
    import autoshots as AS
    by_file = {}
    for i in slots:
        by_file.setdefault(job['shots'][i][0], []).append(i)
    for f, idx in by_file.items():
        r = AS.READ.get(f) or {}
        v0 = float(r.get('picture_start') or 0.0)
        dur = float(r.get('duration') or 0) or _video_dur(f) or (v0 + 10.0 * len(idx))
        try:                                   # proven stretches of this file from the footage library first (card B)
            import footlib
            proven = [x for x in footlib.stretches_for_file(f, job=job) if x[0] >= v0]
        except Exception:                      # noqa: BLE001
            proven = []
        taken = [(float(s[1]), float(s[1]) + float(s[2])) for s in job['shots'] if s[0] == f and isinstance(s[1], (int, float))]
        for k, i in enumerate(idx):
            sh = job['shots'][i]
            secs = float(sh[2])
            pick = next((p for p in proven if p[1] >= secs - 0.3 and not any(a < p[0] + secs and p[0] < b for a, b in taken)
                         and frame_clean(f, p[0], secs, dur)[0]), None)   # a proven stretch is checked too (Clair, 21 Nov)
            if pick:
                sh[1] = pick[0]
                if len(sh) > 3 and sh[3] is None and pick[2] is not None:
                    sh[3] = pick[2]
                taken.append((pick[0], pick[0] + secs))
                SG_.ladder('picture', i, 'a', f'{f} at {pick[0]} s: a proven stretch from the footage library')
                continue
            st = v0 + 0.3 + (max(0.0, dur - v0 - 0.6 - secs)) * (k + 0.5) / len(idx)
            st = clean_near(f, st, secs, v0, dur, taken)          # off black, flat cards and the end slate (21 Nov)
            taken.append((st, st + secs))
            sh[1] = round(st, 2)
            for key in ('cut_ok', 'drift_ok'):
                job.setdefault(key, []).append([f, sh[1], 'never refuse: no clean stretch read, evenly spaced fallback'])
            SG_.ladder('picture', i, 'a', f'{f} at {sh[1]} s for {secs} s: no clean stretch read, evenly spaced crop')
    job.pop('shots_auto', None)


def scan(job):
    """The footage scan (auto_shots, track_from_first_shot, shot_gate) can never hang the render (Mohammad, 20 Nov
    2026): in soft mode it runs capped, at 3 minutes per footage source, on 720p proxies of large files
    (templates/scanproxy.py). When the cap is hit the job keeps its shots as written, and automatic slots are filled
    from the footage library or evenly spaced (auto_fallback). Strict jobs (tests) run the scan as before. Returns the
    time the shots were settled (stage minutes)."""
    import softgate as SG_

    def _all(j):
        auto_shots(j)
        track_from_first_shot(j)
        globals()['_T_SHOTS'] = time.time()
        shot_gate(j)

    if not SG_.soft(job):
        auto_shots(job)
        track_from_first_shot(job)
        t = time.time()
        shot_gate(job)
        return t
    import scanproxy
    import autoshots as AS
    import shotgate as SG
    if SG.stylised(job) and SG_.showcase_ok(job):   # crop fix (26 Nov 2026): stylised art the detector cannot frame
        SG_.showcase_fallback(job, 'stylised art: the person, vehicle and animal detector cannot frame its characters '
                                   '(crop fix, 26 Nov 2026)')
    t0 = time.time()
    if scanproxy.capped(_all, job):
        return t0 + (time.time() - t0) / 2      # the child's own split is in the log; the stage keeps its total
    SG_.warn('shot scan', f'footage scan stopped at its cap ({scanproxy.cap_for(job)} s); shots as written, '
             'automatic slots from the footage library or evenly spaced')
    AS.expand(job)
    slots = [i for i in job.get('shots_auto') or [] if i < len(job.get('shots') or [])]
    if slots:
        auto_fallback(job, slots)
        band_or_fill(job, 'the shot scan found no clean stretch before its cap')
        SG_.ladder('picture', 'reel', 'a', f'scan cap: {len(slots)} automatic slot(s) from the library or evenly spaced')
    track_from_first_shot(job)
    return time.time()


PEOPLE_KINDS = ('people', 'quote', 'cast', 'interview', 'event', 'debate')
HOOK_EXTRA_FILES = 2   # at most two stretches read from other trailers for the hook (range reads, a few seconds each)
HOOK_LEAD = 1.0        # seconds read before the hook stretch
HOOK_TAIL = 6.0        # seconds read past the Reel's length, for the track's fade
HOOK_FETCH_SCORE = 3                       # only a named subject (Jason, Lucia) is worth fetching another trailer


def hook_pick(job):
    """The hook shot (the cover) after the shots are settled (Mohammad, 23 Nov 2026, variety fix items 1 and 5):
      story: a curated stretch that matches the story (the person it names, a crowd, the city) when one passes the cover
             and opener ledger;
      keep:  the hook as picked when it passes and nothing matches the story better;
      a:     another stretch of the same file: its curated stretches, the library's proven stretches, then evenly
             spaced clean points;
      b:     another official trailer of the same game in the curated library;
      c:     an official still or key art with motion, when the library lists one for the game;
      d:     a different layout (the 16:9 boxed showcase, hashed as the grid shows it).
    Never the same shot again: each step's candidate must pass variety.hook_ok. The step taken is written to the render
    log and qc.json (softgate ladder, kind hook)."""
    import softgate as SG_
    import variety
    shots = job.get('shots') or []
    if not shots or not isinstance(shots[0], list) or not isinstance(shots[0][1], (int, float)) \
            or str(shots[0][0]).lower().endswith(tuple(reel.STILL) + ('.png',)):
        return
    sh0 = shots[0]
    need = float(sh0[2])
    led = variety.load()
    cur, subjects = variety.curated(job.get('game') or job.get('game_short'))
    text = ' '.join(str(x) for x in (job.get('headline'), job.get('spoken'), (job.get('subject_person') or {}).get('name'),
                                       ' '.join(str(p[1]) for p in job.get('person') or [] if len(p) > 1)) if x)
    people_story = job.get('template') == 'people' or job.get('kind_news') in PEOPLE_KINDS or bool(job.get('subject_person'))
    extra = [0]
    reel_secs = sum(float(x[2]) for x in shots if isinstance(x, list) and len(x) > 2
                    and isinstance(x[2], (int, float)))

    def held(s):                               # the job already carries this file (or a copy on its timeline)
        return next((it['file'] for it in job.get('footage') or [] if it.get('file') and
                     (it.get('url') == s['url'] or (it.get('repo') and it['repo'] in (s.get('same') or [])))), None)

    def file_for(s):
        """(file, offset): the job's own copy when it holds one (offset 0); otherwise only the stretch the hook needs,
        read over HTTP range requests ("stream", as the GTA VI batch does), long enough to carry the trailer track
        under the whole Reel. A 4K master is 0.8 to 1.5 GB whole; the McQueen replay of 23 Nov ran out of its 15 minutes
        fetching Trailer 2."""
        f = held(s)
        if f:
            return f, 0.0
        if extra[0] >= HOOK_EXTRA_FILES:
            return None, 0.0
        st0 = max(0.0, float(s['start']) - HOOK_LEAD)
        item = {'file': f"{s['file']}-from-{st0:g}.mp4", 'url': s['url'], 'stream': True, 'start': round(st0, 2),
                'seconds': round(reel_secs + HOOK_TAIL, 1), 'scale': 1080, 'note': f"hook: {s['file']} read from {st0:g} s"}
        try:
            fetch(item)
        except Exception as e:                 # noqa: BLE001
            print(f"render_job: hook: {s['url']} not read ({e})", flush=True)
            return None, 0.0
        extra[0] += 1
        job.setdefault('footage', []).append(item)
        return item['file'], st0

    def free(f, st):
        return not any(isinstance(s, list) and s is not sh0 and s[0] == f and isinstance(s[1], (int, float))
                       and s[1] < st + need and st < s[1] + float(s[2]) for s in shots)

    def passes(f, st, fo):
        if not free(f, st):
            return False
        ok, _ = variety.hook_ok(job, f, C.U + f, st, fo, led)
        return ok

    def take(f, st, fo, step, why):
        sh0[0], sh0[1] = f, round(float(st), 2)
        if fo is not None:
            sh0[3] = [[0.0, fo]] if not isinstance(fo, list) else fo
        SG_.ladder('hook', 0, step, why)
        print(f'render_job: hook step {step}: {why}', flush=True)
        return True

    import hashlib
    turn = int(hashlib.md5(str(job.get('name')).encode()).hexdigest(), 16)

    def spread(xs):                            # each Reel starts its list at its own place: two Reels rendered at once
        xs = list(xs)                          # (and not yet in each other's ledger) still land on different stretches
        return xs[turn % len(xs):] + xs[:turn % len(xs)] if xs else xs

    def curated_fits(s):
        return s['start'] + need <= float((s.get('scene') or [0, s['start'] + s['secs']])[1]) - 0.15

    if people_story or text:                   # story: what the story is about, before any generic stretch
        ranked = sorted(((variety.story_score(s, text, subjects, people_story), not held(s), i, s)
                         for i, s in enumerate(spread(cur))), key=lambda x: (-x[0], x[1], x[2]))
        for sc, _far, _i, s in ranked:          # equal matches: a file the job already has first (no 4K fetch)
            if sc <= 0:
                break
            if not curated_fits(s):
                continue
            if _far and sc < HOOK_FETCH_SCORE:     # a generic match (a crowd, the city) never costs a second trailer
                continue
            f, off = file_for(s)
            if f and passes(f, s['start'] - off, s.get('focus')):
                return take(f, s['start'] - off, s.get('focus'), 'story', f"{s['label']} ({s['file']} at {s['start']} s), "
                            f"matches the story (score {sc:g})")
    ok, why = variety.hook_ok(job, sh0[0], C.U + sh0[0], float(sh0[1]), sh0[3] if len(sh0) > 3 else None, led)
    if ok:
        return False
    f0 = sh0[0]
    for s in spread([s for s in cur if held(s) == f0 and curated_fits(s)]):              # a: the same file
        if passes(f0, s['start'], s.get('focus')):
            return take(f0, s['start'], s.get('focus'), 'a', f"another stretch of the same file: {s['label']} at "
                        f"{s['start']} s ({why})")
    try:
        import footlib
        proven = footlib.stretches_for_file(f0, job=job)
    except Exception:                          # noqa: BLE001
        proven = []
    for p in spread(proven):
        if p[1] >= need - 0.3 and passes(f0, p[0], p[2]):
            return take(f0, p[0], p[2], 'a', f'another stretch of the same file: library stretch at {p[0]} s ({why})')
    dur = _video_dur(f0) or 0.0
    for k in range(8):
        st = 0.5 + (max(0.0, dur - 1.0 - need)) * (k + 0.5) / 8
        if frame_clean(f0, st, need, dur)[0] and passes(f0, st, None):
            return take(f0, st, None, 'a', f'another stretch of the same file: clean point at {st:.2f} s ({why})')
    for s in spread([s for s in cur if held(s) != f0 and curated_fits(s)]):              # b: another official trailer
        f, off = file_for(s)
        if f and passes(f, s['start'] - off, s.get('focus')):
            return take(f, s['start'] - off, s.get('focus'), 'b', f"another official trailer: {s['label']} ({s['file']} at "
                        f"{s['start']} s) ({why})")
    SG_.ladder('hook', 0, 'c', 'no official still or key art with motion listed for this game; next step')
    blockers = [k for k in SG_.SHOWCASE_BLOCKERS if job.get(k)]
    if not blockers and job.get('layout') != 'showcase':                               # d: a different layout
        job['layout'] = 'showcase'
        job.setdefault('showcase_reason', 'variety: every crop of the available hooks repeats a recent cover on the grid '
                                          '(23 Nov 2026 hook order, step d)')
        SG_.ladder('hook', 0, 'd', f'different layout: the 16:9 boxed showcase ({why})')
        return True
    SG_.ladder('hook', 0, 'none', f'no step passed ({why}); the hook stays' + (f' (showcase blocked by {blockers})' if blockers else ''))
    return False


def track_from_first_shot(job):
    """A slip job (templates/slip.py) leaves its trailer track's start to the server: once the shots are picked, the
    track runs from the first footage shot's source second, on that shot's file (adv-20261117-server-news-line-editor-
    model, Phase 1). Nothing changes for a job without "track_from_first_shot"."""
    if not job.get('track_from_first_shot') or not isinstance(job.get('track'), list):
        return
    for s in job.get('shots') or []:
        if isinstance(s, list) and len(s) > 1 and isinstance(s[1], (int, float)) and not str(s[0]).endswith('.png'):
            job['track'] = [s[0], float(s[1])] + list(job['track'][2:])
            print(f'render_job: track from the first shot: {s[0]} at {float(s[1]):.2f} s', flush=True)
            return


def shot_gate(job):
    """adv-20261115-one-render-server-checks items B and C (templates/shotgate.py): every footage shot starts after the
    picture on the server's copy, stays inside one scene, is not letterboxed, and keeps its subject inside the 9:16
    window. A shot whose focus is null is autofocused first (as the build would), so the window checked is the one the
    Reel uses. Every problem is listed at once; the job stops before anything is built."""
    import shotgate as SG
    if job.get('kind') in ('famitsu', 'breaking') or profile_of(job) == 'breaking':
        return
    import autofix as AF                       # the server fixes what it can before it refuses (adv-20261117-gates-fix-not-refuse B)
    if AF.enabled(job):
        n0 = len(AF.LOG)
        left = AF.shots(job)
        if len(AF.LOG) > n0:
            AF.save_log(os.environ.get('AUTOFIX_JSON'))
            if os.environ.get('AUTOFIX_JOB'):  # the fixed job, written back to main by the workflow
                json.dump(job, open(os.environ['AUTOFIX_JOB'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        for p in left:
            print('shotgate: ' + p['detail'] + ' (' + p.get('autofix', 'no fix') + ')', flush=True)
        if left:
            print('SHOTGATE_JSON: ' + json.dumps({'job': job.get('name'), 'ok': False, 'problems': left}, ensure_ascii=False),
                  flush=True)
            import softgate as SG_
            if SG_.soft(job):
                gate_ladder(job, left)
                return
            raise SystemExit(f'shotgate: {len(left)} shot problem{"s" if len(left) > 1 else ""} the server could not fix '
                             '(above), each with what it tried')
        print('shotgate: shots clean on the server copy (picture start, scene cuts, letterbox, subject drift)', flush=True)
        return
    rows = clean_nudge(job, job['shots'])
    for sh in rows:
        f, st, secs = sh[0], sh[1], sh[2]
        if (len(sh) > 3 and sh[3] is None and isinstance(st, (int, float)) and isinstance(f, str)
                and not f.endswith(('.png', '.jpg', '.jpeg', '.webp')) and os.path.exists(C.U + f)):
            sh[3] = [list(k) for k in reel.autofocus(f, st, secs)]
    import softgate as SG_
    if SG_.soft(job):
        left = SG_.guarded('shot gate', SG.problems, job, rows) or []
        if left:
            gate_ladder(job, left)
        return
    SG.enforce(job, rows)


from softgate import SHOWCASE_BLOCKERS   # noqa: E402  (the 16:9 fallback lives in softgate, 20 Nov 2026)


def gate_ladder(job, left):
    """Never refuse (card A): a shot the gate could not fix moves down the picture ladder. Letterboxed or low-row
    footage takes the showcase layout (step b) when nothing in the job rules it out; every other problem (a scene cut,
    drift, a subject cut by the edge) keeps a crop with the check waived (step a). Each slot is logged."""
    import softgate as SG_
    letterbox = drift = False
    for p in left:
        i = p.get('shot')
        if i is None and str(p.get('where', '')).startswith('shot '):
            try:
                i = int(str(p['where']).split()[1])
            except (IndexError, ValueError):
                i = None
        d = str(p.get('detail', '')) + ' ' + str(p.get('rule', ''))
        sh = job['shots'][i] if isinstance(i, int) and i < len(job.get('shots') or []) else None
        if sh is None:
            SG_.warn('shot gate', d)
            continue
        if p.get('rule') == 'shot_long':       # crop fix (26 Nov 2026): a long shot no trim could fix is a warning only
            SG_.warn('shot gate', d, shot=i)
            continue
        f, st = sh[0], sh[1]
        if 'before the picture' in d and isinstance(p.get('picture_start'), (int, float)):
            sh[1] = st = round(float(p['picture_start']) + 0.05, 2)   # a shot that opens before the picture starts on it
        kinds = [k for k, hit in (('letterbox', 'letterbox' in d), ('cut', 'scene cut' in d),
                                  ('drift', 'subject_' in d)) if hit] or ['drift']
        for kind in kinds:
            key = {'letterbox': 'letterbox_ok', 'cut': 'cut_ok', 'drift': 'drift_ok'}[kind]
            job.setdefault(key, []).append([f, st, 'never refuse: ' + d[:120]])
        letterbox = letterbox or 'letterbox' in kinds
        SG_.warn('shot gate', d, shot=i)
        SG_.ladder('picture', i, 'a', ', '.join(kinds) + ': kept as a crop, check waived')
        drift = drift or 'drift' in kinds
    if letterbox and SG_.showcase_ok(job):
        job['layout'] = 'showcase'
        job['showcase_reason'] = ('the source is letterboxed and fails the quality gate in a full-frame crop '
                                  '(picture ladder step b, set by the server)')
        SG_.ladder('picture', 'reel', 'b', 'letterboxed footage: showcase layout, the trailer at its own width')
    elif drift:                                 # a subject the 9:16 crop loses: show the whole frame (20 Nov 2026)
        SG_.showcase_fallback(job, 'the subject leaves or is cut by the 9:16 window')


FALLBACK_AFTER = 3         # renders of one story in 24 hours before the next one takes the 16:9 fallback (Mohammad, 20 Nov 2026)


def tries_ladder(job, story=None):
    """Mohammad, 20 Nov 2026 ("Eight is a lot... If it does it 3 times and doesn't work, it activates the fallback"):
    after FALLBACK_AFTER renders of the same story in the last 24 hours (render-times.json, as jobsha counts dispatches),
    the next render takes the showcase layout instead of another crop. Returns the reason when it moved the job."""
    import softgate as SG_
    import jobsha
    if not SG_.soft(job) or not SG_.showcase_ok(job):
        return None
    name = story or job.get('story') or job.get('name')
    if not name:
        return None
    done = jobsha.count(str(name), jobsha._entries()) - 1
    if done < FALLBACK_AFTER:
        return None
    why = f'{done} renders of this story in 24 hours did not get it through (trailer crop tried {done} times)'
    print('tries: ' + why, flush=True)
    return why if SG_.showcase_fallback(job, why) else None


CONTENT_WORDS = 2          # readable words in one cropped frame that count as burnt-in text (a subtitle, a credit card)
CONTENT_SECS = 60          # the whole read; a slow read is a warning, never a hold


def content_ladder(job):
    """The 16:9 fallback (Mohammad, 20 Nov 2026: "if the render fails because of what's happening in the reel in the
    background, it can go to 16:9 and just use the empty spaces for the news or text"). Two cropped vertical frames of
    every footage shot (a third and two thirds in) are read with tesseract; a frame with CONTENT_WORDS readable words or
    more inside the 9:16 window (the trailer's subtitles, a staff credit, a title card), in the first shot (the grid tile)
    or in two frames anywhere (one logo frame alone does not count), moves the job to the showcase layout, where the trailer runs at its own width and our headline and lines sit in the bands. Only for jobs that may
    take it (softgate.showcase_ok); without tesseract, or past CONTENT_SECS, it is a warning and the crop stays."""
    import softgate as SG_
    if not SG_.soft(job) or not SG_.showcase_ok(job):
        return None
    t0, hits = time.time(), []
    for i, sh in enumerate(job.get('shots') or []):
        if not (isinstance(sh, (list, tuple)) and len(sh) >= 3 and isinstance(sh[0], str)
                and isinstance(sh[1], (int, float)) and isinstance(sh[2], (int, float))):
            continue
        f, st, du = sh[0], float(sh[1]), float(sh[2])
        if '-gfx-' in f or os.path.splitext(f)[1].lower() in ('.png', '.jpg', '.jpeg', '.webp') or not os.path.exists(C.U + f):
            continue
        fo = sh[3] if len(sh) > 3 else None
        for t in (st + du / 3, st + 2 * du / 3):
            if time.time() - t0 > CONTENT_SECS:
                SG_.warn('content', f'burnt-in text read stopped after {CONTENT_SECS} s at shot {i}; the crop stays')
                return None
            try:
                words = reel._words(reel._vert(f, st, du, fo, t))
            except Exception as e:             # a frame that cannot be read is a warning, never a hold
                SG_.warn('content', f'shot {i} at {t:.2f} s: {e}')
                continue
            if words is None:
                SG_.warn('content', 'tesseract missing: burnt-in text not read; the crop stays')
                return None
            words = [w for w in words if sum(ch.isalnum() for ch in w) >= 2]
            if len(words) >= CONTENT_WORDS:
                hits.append(f'shot {i} at {t:.1f} s ({" ".join(words[:6])})')
                print('content: burnt-in text in ' + hits[-1], flush=True)
                if i == 0 or len(hits) >= 2:     # the grid tile, or text in two frames: not a one-off logo
                    why = 'burnt-in text in ' + '; '.join(hits)
                    return why if SG_.showcase_fallback(job, why, slot=i) else None
    print(f'content: no burnt-in text in the 9:16 window ({time.time() - t0:.0f} s)', flush=True)
    return None


def first_frame_check(job):
    """A footage shot that ends before its file's first video frame has no picture at all, and the montage's xfade then
    waits for it forever (Romero v2, 30 Oct 2026: three runner runs hung 15 minutes on an Empire of Sin shot cut from
    0.8 s for 1.6 s, the file's video starting at 2.84 s). Stop it here; a shot that starts before the first frame
    but runs past it is printed, since it loses its opening."""
    for i, sh in enumerate(job.get('shots') or []):
        f, st, du = sh[0], sh[1], sh[2]
        path = C.U + str(f)
        if st is None or not os.path.exists(path) or os.path.splitext(f)[1].lower() in ('.jpg', '.jpeg', '.png', '.webp'):
            continue
        try:
            v0 = float(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                                'stream=start_time', '-of', 'csv=p=0', path], text=True).strip() or 0)
        except (subprocess.CalledProcessError, ValueError):
            continue
        if st + du <= v0 + 0.05:
            import softgate as SG_
            if SG_.soft(job):
                sh[1] = round(v0 + 0.05, 2)
                SG_.ladder('picture', i, 'a', f'{f}: shot ended before the first video frame ({v0:.2f} s); moved to {sh[1]} s')
                continue
            raise ValueError(f'shot {i} {f} from {st} s for {du} s ends before the first video frame ({v0:.2f} s): '
                             f'no picture, the montage would hang; start it at {v0:.2f} s or later')
        if st < v0 - 0.05:
            print(f'first frame: shot {i} {f} starts at {st} s, the video at {v0:.2f} s; its first '
                  f'{v0 - st:.2f} s are lost', flush=True)


PLATE_FLAT = 0.72          # share of a still cover's pixels with no detail above which it is a plate on a plain ground


def cover_picture_check(job):
    """adv-20261108-numbers-cards-grid item 2 (build 9 Nov 2026): a still that opens the Reel is a picture (key art, a
    trailer frame), never a logo plate or a figure on the plain ground. Read at a quarter of 9:16: when over PLATE_FLAT
    of its pixels have no detail, the render stops."""
    sh = (job.get('shots') or [None])[0]
    if not sh or os.path.splitext(str(sh[0]))[1].lower() not in ('.jpg', '.jpeg', '.png', '.webp') or '-gfx-' in str(sh[0]):
        return None
    path = C.U + str(sh[0])
    if not os.path.exists(path):
        return None
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(path).convert('L')
    im = im.resize((270, max(1, round(im.height * 270 / im.width))))
    g = np.asarray(im.filter(ImageFilter.FIND_EDGES), dtype=np.float32)[1:-1, 1:-1]
    flat = float((g < 6).mean())
    print(f'cover picture: {sh[0]}: {flat:.0%} of it has no detail', flush=True)
    if flat > PLATE_FLAT:
        raise ValueError(f'cover: {sh[0]} is {flat:.0%} flat, a plate or a figure on a plain ground; open on footage, '
                         'key art or a trailer frame (adv-20261108-numbers-cards-grid)')
    return flat


ART_MIN_SIDE = 720         # the still ground's art: its short side at least this (a store thumbnail blurred full-bleed is mush)
LOGO_CLEAR = 0.05          # a logo is a cut-out: at least this share of it transparent, else it is a picture on a white plate


def _asset(path):
    """A job's asset path: in uploads, as given (the runner's working directory is the repo root), or under the repo."""
    for p in (C.U + str(path), str(path), os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), str(path))):
        if os.path.exists(p):
            return p
    return None


def card_art_check(job):
    """adv-20261112-qc-notes-become-failures item 5 (the Roblox Saudi games Reel, 12 Nov 2026): a numbers Reel with no
    footage wears the game's art full-bleed and blurred (the still ground), never a thumbnail on a white plate over the
    plain ground. The still ground's art has a short side of ART_MIN_SIDE or more; a logofact's logo is a cut-out (at
    least LOGO_CLEAR of it transparent), not a game tile or a photo on the white plate. Files not on disk are skipped."""
    from PIL import Image
    import numpy as np
    errs = []
    gs = job.get('ground_still')
    p = _asset(gs) if gs and not job.get('ground_footage') else None
    if p:
        with Image.open(p) as im:
            w, h = im.size
        if min(w, h) < ART_MIN_SIDE:
            errs.append(f'ground_still {gs} is {w}x{h}, a thumbnail: blurred full-bleed it is a smear; give the game\'s key '
                        f'art with a short side of {ART_MIN_SIDE} px or more (store hero, press kit, Steam library hero), '
                        'or "ground_footage" (its trailer)')
    for g in job.get('gfx') or []:
        if g.get('kind') != 'logofact' or not g.get('logo'):
            continue
        p = _asset(g['logo'])
        if not p:
            continue
        a = np.asarray(Image.open(p).convert('RGBA'))[..., 3]
        clear = float((a < 16).mean())
        if clear < LOGO_CLEAR:
            errs.append(f"card {g.get('file')}: logo {g['logo']} has no transparent edge ({clear:.0%} clear), a game tile or "
                        'a photo on the white plate; use the official logo as a cut-out PNG (press kit, store page), or the '
                        'fact card with the art behind it on the still ground')
    if errs:
        raise ValueError('card art: ' + '; '.join(errs))


def speech_check(job, end):
    """No speech under the lines (advisor, 21 Oct 2026): the track's stretch of trailer sound is transcribed over the
    Reel's length before the render, and any word, or a start or fade-out that is not in a pause, stops the job. A quote
    or interview Reel names its subtitled speech as speech_ok [[t0, t1, reason]] in Reel time. Skipped with a notice
    when the source is not in uploads or faster-whisper is missing (the runner)."""
    tr = job.get('track')
    if not isinstance(tr, list) or len(tr) < 2 or not isinstance(tr[0], str):
        return
    f, start = tr[0], float(tr[1])
    if len(tr) > 2 and tr[2] == 'music':          # voices stripped: read what will actually play
        f = os.path.splitext(f)[0] + '-music.wav'
    if not os.path.exists(C.U + f):
        print(f'speech check: {f} not in uploads, skipped', flush=True)
        return
    try:
        import speechcheck as SC
        heard = SC.stretch(f, start, end)
    except ImportError as e:
        print(f'speech check: skipped ({e})', flush=True)
        return
    ok = [w for w in job.get('speech_ok', []) if len(w) == 3]
    bad = [(a - start, b - start, w) for a, b, w in heard
           if not any(t0 <= a - start and b - start <= t1 for t0, t1, _ in ok)]
    edges = [what for what, fine in (('starts', heard.head_pause), ('fades out', heard.tail_pause)) if not fine]
    if bad or edges:
        raise ValueError(f'{f} from {start} s: ' + '; '.join(
            ([f'speech under the lines at ' + ', '.join(f'{a:.2f} to {b:.2f} s "{w}"' for a, b, w in bad[:12])
              + (f' and {len(bad) - 12} more' if len(bad) > 12 else '') + ' (Reel time)'] if bad else [])
            + [f'the track {e} on a word' for e in edges])
            + '; choose a music-only stretch (speechcheck.py --stretch), another trailer, or track "bed"; '
              'for a quote Reel pass speech_ok=[[t0, t1, reason]]')
    print(f'speech check: {f} from {start} s for {end:.1f} s, speech: ' + ('inside speech_ok only' if heard else 'none'), flush=True)


def textcheck(job, collect=None):
    """Headline, lines, strip and credits drawn alone, so a line that wraps onto a Latin word or
    leaves the safe zone stops in seconds (needs the Dubai font: the runner runs it first).
    Every error in one pass (adv-20261110-one-render-per-reel, item A): the font-free rules (textrules.py) first, then
    each drawn piece on its own, each failure added to the list instead of stopping at the first. Raises ValueError with
    all of them, or, with `collect` (a list), appends them there and returns."""
    if job.get('kind') == 'famitsu':           # sales_full draws its own rows; nothing to pre-check here
        return
    if job.get('kind') == 'breaking':
        return BK.textcheck(job)
    import tempfile
    import textrules as TR
    errs = [] if collect is None else collect
    for f in TR.hard(TR.check(job)):
        errs.append({'where': f['where'], 'rule': f['rule'], 'text': f['text'], 'fix': f['fix']})

    def _do(where, fn, *a, **kw):
        try:
            return fn(*a, **kw)
        except (ValueError, SystemExit, OSError) as e:
            msg = str(e)
            if not any(x.get('detail') == msg for x in errs):
                errs.append({'where': where, 'rule': 'font_check', 'text': '', 'fix': '', 'detail': msg})
            return None
    import fast_ar as _FA
    if not os.path.exists(_FA.FONTS + 'Dubai-Bold.ttf'):   # the session: the font-free rules only, the rest on the server
        for f in TR.check(job):
            if f not in TR.hard([f]):
                print(f"text check (estimate): {f['where']}: {f['text']!r} -> {f['fix']}", flush=True)
        print('text check: no Dubai font here, so the drawn checks (wraps, safe zone, cards) run on the server; '
              'dispatch prerender.yml with mode text for them (10 to 20 s, no footage)', flush=True)
        if errs and collect is None:
            raise ValueError(text_report(errs))
        return
    tmp = tempfile.mkdtemp(prefix='textcheck-')
    try:
        skin = job.get('skin') if job.get('skin') in reel.SK.KITS and job.get('label') != 'عاجل' else None
        _do('headline', reel.head_layer, job['headline'], job['label'], f'{tmp}/h.png', job['source'], job['date'],
            job.get('country'), hs=job.get('head_size', reel.HEAD_SIZE), skin=skin)
        show = showcase_of(job)                # the showcase draws its lines, facts and credits in the bottom band
        if show:
            try:
                lift = reel.showcase_box(reel.HEAD_GEOM['end'], bool(job.get('strip')), fit=job.get('showcase_fit') or 'wide')[4]
            except ValueError:
                lift = reel.showcase_box(reel.HEAD_GEOM['end'], bool(job.get('strip')))[4]
        n, drawn = 0, []
        for a, b, texts in job['lines']:
            for x in texts:
                n += 1
                text, kw = (x, {}) if isinstance(x, str) else (x[0], x[1] if len(x) > 1 else {})
                if show:
                    kw = dict({k: v for k, v in kw.items() if k not in ('top', 'lift', 'size', 'step', 'shade')},
                              size=reel.SHOW_LINE[0], step=reel.SHOW_LINE[1], lift=lift)
                elif job.get('strip') and 'lift' not in kw:
                    kw = dict(kw, lift=reel.STRIP_LIFT) if hasattr(reel, 'STRIP_LIFT') else kw
                geo = {}
                if _do(f'line {n}', reel.line_layer, text, f'{tmp}/l{n}.png', skin=skin, geometry=geo, **kw) is not None:
                    drawn.append((n, a, b, text, f'{tmp}/l{n}.png', len(geo.get('lines') or [])))
        if show:
            if job.get('strip'):
                _do('strip', reel.facts_layer, strip_items(job), f'{tmp}/f.png')
            for i, c in enumerate(job.get('credits') or [], 1):
                _do(f'credit {i}', reel.credit_layer, c[2], f'{tmp}/c.png', size=reel.SHOW_CREDIT, y=reel.SHOW_CREDIT_Y)
        elif job.get('strip'):
            # the same one-fact-one-place check reel() runs, so a repeat fails here in seconds
            _do('strip', reel.strip_check, strip_items(job), [(x if isinstance(x, str) else x[0], 0, 0, {} if isinstance(x, str) else (x[1] if len(x) > 1 else {}))
                                                for _, _, texts in job['lines'] for x in texts])
            _do('strip', reel.strip_layer, strip_items(job), f'{tmp}/s.png', job['theme'], skin=skin)
        if not show:                           # drawn at the size the render uses (credit_specs: opt size, band)
            for i, c in enumerate(job.get('credits') or [], 1):
                o = c[3] if len(c) > 3 and isinstance(c[3], dict) else {}
                _do(f'credit {i}', reel.credit_layer, c[2], f'{tmp}/c.png', size=o.get('size', 36), band=o.get('band', False),
                    low=o.get('low', False))
        if job.get('intro') is not None:       # the series intro's title and days line (Dubai font)
            OI = _intro_mod(job['intro'])
            if job['intro'].get('series') == 'gtavi':
                _do('intro', OI.layers, job['intro']['days'], tmp, job['intro']['episode'])
            else:
                _do('intro', OI.layers, job['intro']['days'], tmp)
        for x in job.get('person') or []:          # needs the photo in uploads: fetched like footage before this runs
            o = x[5] if len(x) > 5 else {}
            if not x[0] or os.path.exists(C.U + x[0]):   # no photo: the name card (22 Nov 2026)
                _do('person', reel.person_layer, x[0], x[1], x[2], f'{tmp}/p.png', job['theme'],
                    focus=tuple(o.get('focus', (0.5, 0.33))), credit=o.get('credit'))
        _do('gfx', gfx, job, tmp)
        for p in card_line_problems(job, drawn, tmp):
            errs.append({'where': p['where'], 'rule': 'card_line', 'text': p['text'], 'fix': '', 'detail': p['detail']})
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)
    if errs and collect is None:
        raise ValueError(text_report(errs))


def _alpha_box(path, cut=40):
    """(x0, y0, x1, y1) of a layer's visible pixels, or None."""
    from PIL import Image as _I
    a = _I.open(path).convert('RGBA').getchannel('A').point(lambda v: 255 if v > cut else 0)
    return a.getbbox()


def card_line_problems(job, drawn, where):
    """One fact, one place (14 Oct 2026), enforced (adv-20261112-qc-notes-become-failures item 1): a story line over one of
    our cards is one visual line at most and sits clear of the card's text box, or it is dropped. `drawn` is
    [(n, first shot, last shot, text, layer png, visual lines)] from the text check; the cards are drawn in `where`.
    Shots under a HyperFrames insert are left out (the insert covers the Reel's own lines and card)."""
    covered = set()
    for ins in job.get('insert') or []:
        sh = ins.get('shot')
        i0, i1 = (sh, sh) if isinstance(sh, int) else (int(sh[0]), int(sh[1]))
        covered.update(range(i0, i1 + 1))
    out = []
    for n, a, b, text, layer, nlines in drawn:
        cards = [job['shots'][i][0] for i in range(a, b + 1) if i < len(job['shots']) and i not in covered
                 and job['shots'][i][0].endswith('.png') and '-gfx-' in job['shots'][i][0]]
        if not cards:
            continue
        short = text.replace('\n', ' / ')
        if nlines > 1:
            out.append({'where': f'line {n}', 'text': short, 'detail': f'over a card a story line is one visual line '
                        f'at most ({nlines} here); shorten it or drop it (one fact, one place)'})
        lb = _alpha_box(layer) if os.path.exists(layer) else None
        for c in cards:
            cp = os.path.join(where, c)
            cb = _alpha_box(cp) if os.path.exists(cp) else None
            if not (lb and cb):
                continue
            pad = 8
            if lb[0] < cb[2] + pad and cb[0] < lb[2] + pad and lb[1] < cb[3] + pad and cb[1] < lb[3] + pad:
                out.append({'where': f'line {n}', 'text': short, 'detail': f'collision: the line (y {lb[1]} to {lb[3]}) '
                            f'is drawn over the card {c} (its text box y {cb[1]} to {cb[3]}); move the line to a footage '
                            'shot, drop it, or use a card that leaves the line band clear'})
                break
    return out


def text_report(errs):
    """One block naming every text error (render_job.py text prints it; the JSON goes with --json)."""
    return 'text check: %d problem%s\n' % (len(errs), '' if len(errs) == 1 else 's') + '\n'.join(
        f"  - {e['where']}: {e['rule']}: " + (e.get('detail') or f"{e['text']!r} -> {e['fix']}") for e in errs)


def gfx(job, where=None):
    """The job's cards (`gfx`), drawn with the Dubai font: into uploads before the render, or into
    `where` for the text check, so a card that does not fit stops in seconds."""
    for item in job.get('gfx', []):
        CG.build(item, os.path.join(where, item['file']) if where else C.U + item['file'], job.get('ground_theme', job['theme']))


def source_check(job):
    """Every footage shot's stretch read for a blocky smear before it is used (the damage in a download sits on its
    own scene cut). block_ok entries [file, t0, t1, reason] waive a stretch a person has looked at."""
    waive = [w for w in job.get('block_ok', []) if len(w) == 4]
    bad = []
    for f, start, secs, _ in clean_nudge(job, job['shots']):
        if start is None or os.path.splitext(f)[1].lower() in reel.STILL or f.endswith('.png'):
            continue
        lo = max(0.0, start - 1.0)                 # read with context, report only what the shot uses
        for a, b, peak in DC.smear_times(C.U + f, lo, secs + (start - lo) + 1.0):
            if b <= start or a >= start + secs:
                continue
            if not any(w[0] == f and w[1] <= a <= w[2] for w in waive):
                bad.append(f'{f} {a:.2f} to {b:.2f} s (peak {peak})')
    if bad:
        import softgate as SG_
        if SG_.soft(job):
            SG_.warn('source smear', 'blocky smear in the source: ' + '; '.join(bad))
            return
        raise ValueError('blocky smear in the source: ' + '; '.join(bad) + '; re-fetch it, use another copy, '
                         'or after looking pass block_ok=[[file, t0, t1, reason]]')


def famitsu(job, draft=False):
    """Famitsu weekly sales Reel (sales_full.reel) on the runner, for when the container has no Dubai font (22 Oct
    2026). `rows` and `hardware` are what sales_full.reel takes, with `shot` [file, [from, to]] and `art` naming files
    in uploads that `footage` fetches (screenshots and box art by URL); `week_label`, `date`, optional `hook`,
    `lowres_ok` and `block_ok`. The sheet lays out every screenshot with its pan."""
    import sales_full as SF
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
    rows = []
    for r in job['rows']:
        r = dict(r, shot=(C.U + r['shot'][0], tuple(r['shot'][1])))
        if r.get('art'):
            r['art'] = C.U + r['art']
        rows.append(r)
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    extra = {'hook': job['hook']} if job.get('hook') else {}
    video = SF.reel(rows, job['week_label'], job['date'], out, hardware=job.get('hardware', ()), draft=draft,
                    lowres_ok=job.get('lowres_ok', False), **extra)[0]
    base = re.sub(r'-reel-v\d+$', '', os.path.splitext(out)[0])
    if not draft:
        DC.check(video, [w for w in job.get('block_ok', []) if len(w) == 3])
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        reel.shotsheet([(r['shot'][0], None, 2.0, tuple(r['shot'][1])) for r in job['rows']], base + '-sheet.jpg')
    print(f"render_job: {job['name']} (famitsu) done in {time.time() - t0:.0f} s: {video}", flush=True)
    return video


def inserts(job, video):
    """HyperFrames inserts (advisor, 24 Oct 2026): laid over the finished Reel at their graphic shots; a failure or
    a render past hfinsert.TIMEOUT keeps the current card and is noted here and in render-times.json."""
    import hfinsert as HI
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, _ = reel.timeline(shots(job, build=False))
        recs = HI.apply(job, video, starts)
    finally:
        reel.X = keep
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):   # entries are named after the output file
                e['hf_insert'] = recs
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with the insert: {e}', flush=True)
    for r in recs:
        print(f"render_job: hf insert on shot {r['shot']}: {'ok' if r.get('ok') else 'FAILED, current card kept'} "
              f"({r['render_secs']} s){'' if r.get('ok') else ': ' + r['error']}", flush=True)
    return recs


def audio_split(job, video):
    """Trailer audio split (Mohammad, 24 Oct 2026, inbox 16:26Z): a job on a trailer track gets the trailer's music
    under the whole Reel and each shot's own effects (templates/tracksplit.py). Anything that fails, runs long or
    measures unclean keeps today's audio; the outcome is printed and kept in render-times.json as `audio_split`."""
    import tracksplit as TS
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, _ = reel.timeline(shots(job, build=False))
        xf = reel.X
    finally:
        reel.X = keep
    rec = TS.apply(job, video, starts, xf, C.U)
    print('render_job: audio split: ' + ('applied' if rec.get('applied') else 'not applied, audio as rendered') +
          ''.join(f'; {k} {rec[k]}' for k in ('reason', 'music_pct', 'leak_pct', 'cache', 'separate_secs', 'secs') if k in rec), flush=True)
    import softgate as SG_
    if job.get('music_only') and not rec.get('applied') and SG_.soft(job):   # music stem failed: franchise, then our bed
        rec = sound_ladder(job, video, starts, xf, rec, f"music stem not clean: {rec.get('reason')}", tried_b=True)
        _times_note(job, 'audio_split', rec)
        return rec
    if job.get('music_only') and not rec.get('applied'):   # asked for no effects: never ship the trailer's own mix instead
        raise ValueError('music_only: the music stem could not be separated cleanly (' + str(rec.get('reason')) + '); '
                         'use another stretch or track "bed"')
    import sfxplan as SF                       # a fallback on a track under other moments' shots fails the job
    try:
        SF.guard(job, rec, starts)
    except ValueError as e:
        if job.get('split_fallback') not in ('bed', 'ladder') and not SG_.soft(job):
            _times_note(job, 'audio_split', rec)
            raise
        rec = sound_ladder(job, video, starts, xf, rec, f'{e}')
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):
                e['audio_split'] = rec
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with the audio split: {e}', flush=True)
    return rec


def sound_ladder(job, video, starts, xf, rec, why, tried_b=False):
    """The sound ladder (audit of 21 Nov 2026, item 2; Mohammad): sound follows the game, not the template. (a) the
    trailer's own audio, split, speech dropped, already tried by audio_split; (b) that trailer's music stem alone under
    the whole body (music_only: no 40% music floor, the stem must still be clean); (c) the franchise theme from the
    library (templates/franchise.py), for a game in a known series; (d) our bed. Each step is in qc.json's ladder and
    the render log's sound line (qc.sound_of), so the Publer label reads sound:trailer, sound:franchise or sound:bed."""
    import softgate as SG_
    import tracksplit as TS
    # (b) differs from (a) only by the 40% music floor; when (a) measured the stem itself as unclean, (b) would measure the
    # same stem again (37 s on Ace Combat 8's replay) and fail the same way, so it runs only after a floor refusal
    floor = 'of the track (<' in str(rec.get('reason') or '')
    if not tried_b and floor and isinstance(job.get('track'), (list, tuple)):
        rb = TS.apply(dict(job, music_only=True), video, starts, xf, C.U)
        print('render_job: sound ladder b (music only): ' + ('applied' if rb.get('applied') else 'not applied') +
              ''.join(f'; {k} {rb[k]}' for k in ('reason', 'music_pct', 'leak_pct', 'secs') if k in rb), flush=True)
        if rb.get('applied'):
            SG_.ladder('sound', 'reel', 'b', f"{why}; the trailer's music stem alone (leftover {rb.get('leak_pct')}%)")
            print(f"render_job: sound: trailer-music (ladder b: {why})", flush=True)
            return dict(rb, ladder='b', step_a=rec)
        rec = dict(rec, step_b=rb)
    try:
        import franchise as FR
        rc = FR.lay(job, video, why)
    except Exception as e:                       # noqa: BLE001  a library that fails never holds the Reel
        rc = None
        print(f'render_job: sound ladder c (franchise) failed: {e}', flush=True)
    if rc:
        SG_.ladder('sound', 'reel', 'c', f"{why}; franchise theme {rc['franchise']}")
        print(f"render_job: sound: franchise:{rc['franchise']} ({why})", flush=True)
        return dict(rec, fallback='franchise:' + rc['franchise'], franchise=rc, ladder='c')
    SG_.ladder('sound', 'reel', 'd', f'{why}; our bed')
    rec = dict(rec, ladder='d')
    rec['fallback'] = bed_under(job, video, f"trailer sound refused: {rec.get('reason')}")
    print(f'render_job: audio split fallback: our bed ({why}); {rec["fallback"]}', flush=True)
    return rec


def bed_under(job, video, why):
    """The body sound replaced by our rotated everyday bed, at the old body's level; the end card and its jingle stay
    as rendered (tracksplit.CARD). For jobs that ask for it with "split_fallback": "bed" (story slips, Phase 1 of
    adv-20261117-server-news-line-editor-model): an automatic line never holds a story on a sound refusal, it ships on
    our bed with the measured reason, which qc.json carries as the sound."""
    import numpy as np, soundfile as sf
    import tracksplit as TS
    import sonic as _S
    import outro as _O
    pick = _S.rotate(os.path.basename(job['out']))
    if os.environ.get('RUNNER_TEMP'):
        json.dump([os.path.basename(job['out']), pick], open(os.path.join(os.environ['RUNNER_TEMP'], 'bed.json'), 'w'))
    total = TS._dur(video)
    body = max(0.5, total - TS.CARD)
    old = TS._audio(video, 0, total)
    nb = int(round(body * TS.SR))
    bed, sr = sf.read(_O.evolving_bed(pick, body + 0.5), dtype='float32', always_2d=True)
    bed = bed.T
    if sr != TS.SR:                              # resample by interpolation; the bed is tonal and slow
        x = np.linspace(0, bed.shape[1] - 1, int(bed.shape[1] * TS.SR / sr))
        bed = np.stack([np.interp(x, np.arange(bed.shape[1]), ch) for ch in bed])
    if bed.shape[0] == 1:
        bed = np.vstack([bed, bed])
    bed = bed[:2, :nb]
    bed = np.pad(bed, ((0, 0), (0, max(0, nb - bed.shape[1]))))
    bed = TS._fade(bed, 0.3, 0.6)
    bed *= 10 ** ((TS._db(old[:, :nb]) - TS._db(bed)) / 20)
    full = np.concatenate([bed, old[:, nb:]], axis=1)
    full /= max(1.0, float(np.abs(full).max()) / 0.98)
    wav = os.path.splitext(video)[0] + '-bed.wav'
    tmp = os.path.splitext(video)[0] + '-bed.mp4'
    sf.write(wav, full.T, TS.SR, subtype='PCM_16')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2', '-shortest',
                    '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, video)
    os.remove(wav)
    job['track'], job['sound'], job['bed_reason'] = 'bed', pick, why
    print(f'render_job: sound: bed:{pick} ({why})', flush=True)
    return f'bed:{pick}'


def _times_note(job, key, value):
    try:
        led = json.load(open(reel.TIMES))
        for e in reversed(led):
            if e.get('name') == os.path.basename(job['out']):   # entries are named after the output file
                e[key] = value
                break
        json.dump(led, open(reel.TIMES, 'w'), indent=1)
    except (OSError, ValueError) as e:
        print(f'render_job: render-times not updated with {key}: {e}', flush=True)


def lifeless_note(job, video):
    """Lifeless score of the finished Reel (adv-20261102-borrow-openmontage, part 1): report only, never a stop.
    Printed as `render_job: lifeless:` and kept in render-times.json as `lifeless`."""
    try:
        import lifeless as LF
        r = LF.score(video, storybook=job.get('template') == 'storybeat')
        r['over'] = r['score'] >= LF.REPAIR_AT
        print('render_job: lifeless: ' + json.dumps(r), flush=True)
        _times_note(job, 'lifeless', r)
    except Exception as e:                      # report only: a failure here never touches the Reel
        print(f'render_job: lifeless: not measured ({type(e).__name__}: {e})', flush=True)


def design_plan(job):
    """(plan, apart folder) for the design pass, or (None, None) when the job does not ask for it, is breaking, or
    HyperFrames is not installed (then the Reel renders exactly as before; the reason is printed)."""
    import designpass as DP
    if not (job.get('kit') or job.get('frame')):
        return None, None
    keep = reel.X
    if job.get('cut'):
        reel.X = 0.04
    try:
        starts, end = reel.timeline(shots(job, build=False))
        lines = place(job)(starts, end)
    finally:
        reel.X = keep
    p = DP.plan(job, starts, end, lines)
    if not DP.hf_cli() and (p['moments'] or p['frame']):
        p['notes'].append('HyperFrames CLI not installed: rendered as before')
        p['moments'], p['frame'] = [], None
    for n in p['notes']:
        print(f'render_job: design pass: {n}', flush=True)
    if not (p['moments'] or p['frame']):
        return p, None
    import tempfile
    return p, tempfile.mkdtemp(prefix='dpass-apart-')


def design_pass(job, video, p, folder):
    """The design pass's pieces over the finished Reel (designpass.apply); parts that fail stay as reel.py drew them."""
    import designpass as DP
    try:
        rec = DP.apply(job, video, p, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    for r in rec['pieces']:
        print(f"render_job: design pass {r['piece']}: {'ok' if r.get('ok') else 'FAILED, kept as reel.py drew it'} "
              f"({r['render_secs']} s){'' if r.get('ok') else ': ' + r['error']}", flush=True)
    print(f"render_job: design pass laid back from reel.py: {rec['laid_back'] or 'nothing'}", flush=True)
    return rec


def _intro_mod(spec):
    """The series intro module for a job's `intro` key: ocarina (templates/ocarina_intro.py, the default, as before)
    or gtavi (templates/gta_intro.py, «الطريق إلى GTA VI», studio-gta-vi-series, 8 Nov 2026)."""
    if isinstance(spec, dict) and spec.get('series') == 'gtavi':
        import gta_intro
        return gta_intro
    import ocarina_intro
    return ocarina_intro


def intro(job, video):
    """The series intro joined ahead of the finished Reel (B8): rendered at the Reel's final encode, concat, no re-encode."""
    import tempfile
    OI = _intro_mod(job['intro'])
    t0 = time.time()
    d = tempfile.mkdtemp(prefix='intro-')
    try:
        if job['intro'].get('series') == 'gtavi':
            OI.join(OI.intro(job['intro']['days'], f'{d}/intro.mp4', episode=job['intro']['episode'], final=True), video, video)
        else:
            OI.join(OI.intro(job['intro']['days'], f'{d}/intro.mp4', final=True), video, video)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if job['intro'].get('series') == 'gtavi':
        music = f"our gtavi flavour (sonic.py); join: {OI.JOINED['mode']}"
    else:
        music = 'his upload' if os.path.exists(OI.SRC) else 'the published intro (assets/ocarina/intro-medley.flac)'
    print(f"render_job: series intro joined ({OI.days_line(job['intro']['days'])}, medley from {music}) in {time.time() - t0:.0f} s",
          flush=True)
    _times_note(job, 'intro', {'days': job['intro']['days'], 'secs': round(time.time() - t0, 1)})


def breaking(job, draft=False):
    """The T0 breaking card (templates/breaking.py): fetch the one image, build the card, then the same checks and
    strips as every Reel. There is no shot sheet (no footage shots): `<name>-sheet.jpg` is the source image with the
    9:16 window drawn on it, so the commit step finds the same files."""
    t0 = time.time()
    for item in job.get('footage', []):
        fetch(item)
    fetched = time.time() - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    video = BK.render(job, out, draft=draft)
    stem = os.path.splitext(out)[0]
    base = re.sub(r'-reel-v\d+$', '', stem)
    if not draft:
        DC.check(video, [])                    # decode errors and the blocky-smear flag on the Reel that ships
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        BK.sheet(job, base + '-sheet.jpg')
    print(f"render_job: {job['name']} done in {time.time() - t0:.0f} s (fetch {fetched:.0f} s): {video}", flush=True)
    return video


def gfx_sheet(job, out):
    """A contact sheet of the job's cards (no footage shots to sheet): each card on the indigo ground, in shot order."""
    from PIL import Image
    cards = [sh[0] for sh in job['shots'] if sh[0].endswith('.png') and '-gfx-' in sh[0]]
    k = len(cards)
    cols = min(4, k)
    rows = -(-k // cols)
    tw, th = 270, 480
    sheet = Image.new('RGB', (cols * tw, rows * th), (20, 19, 50))
    for i, f in enumerate(cards):
        im = Image.open(C.U + f).convert('RGBA').resize((tw, th))
        bg = Image.new('RGBA', (tw, th), (20, 19, 50, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out, quality=88)



def persist_overlay(job, video, out):
    """Layers baked over finished showcase shots (8 Nov 2026): the showcase layout keeps the chip and headline in its top
    band, and its lines in the bottom band, for the whole shot, but reel.py shows the headline for 3.5 s and lines only
    after it. `"persist": {"head": [[first_shot, last_shot], ...], "lines": [[shot, text], ...]}`: reel.head_layer's own
    chip and headline (same size, place and style, cropped to the band above the picture) laid over those shots, and
    the given lines (reel.line_layer, same style) over the named shots. Only where reel.py shows no text of its own."""
    import tempfile
    spec = job['persist']
    starts, total = _starts(job)
    n = len(starts)
    span = lambda a, b: (starts[a], starts[b + 1] if b + 1 < n else total)
    tmp = tempfile.mkdtemp(prefix='persist-')
    try:
        hs = job.get('head_size', reel.HEAD_SIZE)
        head = reel.head_layer(job['headline'], job['label'], f'{tmp}/h.png', job['source'], job['date'], job.get('country'),
                               hs=hs, hst=hs + 20, vivid=True, theme=job['theme'], seed=sum(map(ord, out)),
                               style=job.get('style'), meta_path=f'{tmp}/m.png', skin=job.get('skin'))
        band = spec.get('band_h', 676)
        cmd = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', video]
        flt, last, k = [], '0:v', 1
        if spec.get('head'):
            cmd += ['-loop', '1', '-i', head]
            flt.append(f'[{k}:v]crop=1080:{band}:0:0[hd]')
            en = '+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in (span(*x) for x in spec['head']))
            flt.append(f"[{last}][hd]overlay=0:0:enable='{en}'[v{k}]")
            last, k = f'v{k}', k + 1
        for shot, text in spec.get('lines', []):
            reel.line_layer(text, f'{tmp}/l{k}.png', skin=job.get('skin'), size=spec.get('line_size', 54))
            cmd += ['-loop', '1', '-i', f'{tmp}/l{k}.png']
            a, b = span(shot, shot)
            flt.append(f"[{last}][{k}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{k}]")
            last, k = f'v{k}', k + 1
        tmpv = f'{tmp}/out.mp4'
        cmd += ['-filter_complex', ';'.join(flt), '-map', f'[{last}]', '-map', '0:a?', '-c:v', 'libx264'] + reel.FINAL_ENC + \
               ['-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest', tmpv]
        subprocess.run(cmd, check=True)
        os.replace(tmpv, video)
        print(f"render_job: persist overlay laid: head {spec.get('head')}, lines {[x[0] for x in spec.get('lines', [])]}", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def quality(job):
    """The picture-quality setting for this render (adv-20261110-picture-quality-on-server): the job's "quality"
    ("hq" or "base"), else DXB_QUALITY, else base. hq: the final encode at reel.HQ_ENC and the weak-source path;
    the breaking profile and drafts always keep today's settings."""
    q = job.get('quality') or os.environ.get('DXB_QUALITY') or 'base'
    if q not in ('hq', 'base'):
        raise ValueError(f'quality {q!r}: "hq" or "base"')
    if profile_of(job) or job.get('label') == 'عاجل':
        q = 'base'
    reel.QUALITY = q
    if q == 'hq':
        reel.FINAL_ENC = list(reel.HQ_ENC)
    print(f'render_job: quality {q} (final encode {" ".join(reel.FINAL_ENC)}; weak-source path '
          f'{"on, raisr " + ("available" if reel.has_raisr() else "not installed: deblock only") if q == "hq" else "off"})',
          flush=True)
    return q


def run(job, draft=False):
    if job.get('kind') == 'famitsu':
        return famitsu(job, draft)
    if job.get('kind') == 'breaking':
        return breaking(job, draft)
    t0 = time.time()
    import softgate as SG_
    reel.SOFT = SG_.soft(job)                   # templates never refuse (adv-20261118-templates-never-refuse A)
    if SG_.fact_flag(job):                      # hard stop 1 of 4: a wrong fact flagged by the brief
        raise SystemExit(f'render_job: fact flag in the brief: {SG_.fact_flag(job)}')
    reel.CLEAN_MAP = job.get('clean_map')       # pre-render map (templates/prerender.py); None changes nothing
    quality(job)
    for item in job.get('footage', []):
        fetch(item)
    gfx(job)
    t_fetch = time.time()                       # stage times (adv-20261117-server-speed-for-p2 D, templates/stagetimes.py)
    source_check(job)
    t_src = time.time()
    if SG_.soft(job):
        first_frame_check(job)                  # a shot ending before the picture moves onto it (never a hang)
    try:                                        # a mature trailer the ledger does not know is scanned once (27 Nov 2026)
        import blocked as B_
        B_.scan_new(job, C.U, SG_.warn)
    except Exception as e:                      # noqa: BLE001  never a hold
        SG_.warn('blocked scan', f'{type(e).__name__}: {e}')
    if job.get('kind') not in ('famitsu',):
        SG_.guarded('trailer news', trailer_news, job)   # the new trailer, never old footage as the new one (28 Nov 2026)
    t_shots = scan(job)                         # auto shots, track, shot gate: capped, on 720p proxies (20 Nov 2026)
    if SG_.soft(job):
        respread(job)                           # never the same moment twice (20 Nov 2026, Ace Combat 8: 12 shots at 3.07 s)
    if SG_.soft(job) and job.get('kind') not in ('breaking', 'famitsu') and profile_of(job) != 'breaking':
        SG_.guarded('hook', hook_pick, job)     # story first, then a new cover (Mohammad, 23 Nov 2026)
        track_from_first_shot(job)
    SG_.guarded('shot rules', shot_rules, job)   # shot matches line, nothing intimate beyond a kiss (27 Nov 2026)
    if SG_.soft(job) and job.get('kind') not in ('breaking', 'famitsu'):
        SG_.guarded('line shade', auto_shade, job)   # a line over bright footage gets the soft shade (21 Nov, item 5)
    if os.environ.get('RUNNER_TEMP') and job.get('kind') not in ('breaking', 'famitsu'):
        try:                                    # the cover and opener ledger (audit 21 Nov 2026, item 6)
            import variety
            ve = variety.entry(job, C.U)
            if ve:
                json.dump(ve, open(os.path.join(os.environ['RUNNER_TEMP'], 'cover.json'), 'w'), ensure_ascii=False)
        except Exception as e:                  # noqa: BLE001  a ledger never holds a Reel
            print(f'render_job: cover ledger entry not written: {e}', flush=True)
    if job.get('kind') != 'breaking' and profile_of(job) != 'breaking':
        SG_.guarded('tries', tries_ladder, job)         # three renders that did not get through: 16:9 (20 Nov 2026)
        SG_.guarded('content', content_ladder, job)     # the 16:9 fallback for burnt-in text (20 Nov 2026)
    if SG_.soft(job) and job.get('kind') != 'breaking':
        SG_.guarded('reading fix', SG_.fix_reading, job, _starts, place, reel.read_secs)   # text ladder: extend the Reel
        if job.get('lines') and job.get('shots'):
            st_r, end_r = _starts(job)
            SG_.guarded('reading', reel.check_reading, place(job)(st_r, end_r), end_r)
    t_gate = time.time()
    fetched = t_fetch - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    dp_plan, DP_folder = design_plan(job) if not draft else (None, None)
    DP_apart = None
    if DP_folder:
        import designpass as DP
        DP_apart = DP.apart_spec(dp_plan, DP_folder)
    tup = lambda v: v if v is None or isinstance(v, str) else tuple(tuple(x) if isinstance(x, list) else x for x in v)
    style = look(job)
    snd, snd_label = sound_for(job, out, draft)
    print(f'render_job: sound: {snd_label}', flush=True)
    done = reel.reel(shots(job, draft), job['headline'], job['label'], place(job), job['source'], job['date'], out,
                     theme=job['theme'], style=style, sound=snd, country=job.get('country'),
                     head_size=job.get('head_size', reel.HEAD_SIZE), draft=draft, track=tup(job.get('track')), cut=job.get('cut', False),
                     credits=[tuple(c) for c in job['credits']] if job.get('credits') else None,
                     strip=strip_items(job) if job.get('strip') else None,
                     template=job.get('template'), pace_ok=job.get('pace_ok', False), lowres_ok=job.get('lowres_ok', False),
                     skin=job.get('skin'), person=[tuple(x) for x in job['person']] if job.get('person') else None,
                     blocky_ok=job.get('blocky_ok'), apart=DP_apart, profile=profile_of(job),
                     reveal=job.get('reveal'),   # word-by-word reveal on the key line (story-beat twist, 28 Oct 2026)
                     page=page_moves(job, _starts(job)[0]) if job.get('page_motion') else None,   # storybook (B8)
                     showcase=showcase_of(job), showcase_fit=job.get('showcase_fit'), showcase_bg=job.get('showcase_bg', 'blur'))   # trailer at its own width between the bands (9 Nov 2026)
    video = done[0] if isinstance(done, (list, tuple)) else done
    if job.get('persist') and not draft:
        persist_overlay(job, video, out)
    dp = design_pass(job, video, dp_plan, DP_folder) if DP_folder else None
    if job.get('insert') and not draft:
        inserts(job, video)
    if not draft:
        audio_split(job, video)                 # before the decode checks, so they read the Reel that ships
    if dp:
        import designpass as DP
        DP.mix_blips(job, video, dp)            # after the audio split, which rebuilds the body sound
        dp.pop('blip_plan', None)
        _times_note(job, 'design_pass', dp)
        print('render_job: design pass: ' + json.dumps({k: dp[k] for k in ('secs', 'blips', 'notes') if k in dp},
                                                      ensure_ascii=False), flush=True)
    if job.get('intro') is not None and not draft:
        intro(job, video)                       # after the sound is final, before the checks read the file
    stem = os.path.splitext(out)[0]
    base = re.sub(r'-reel-v\d+$', '', stem)   # matches the workflow's ${stem%-reel-v*}, so v2 and later commit too
    t_render = time.time()
    if not draft:
        spans = gfx_spans(job)                 # our own cards are exempt from the smear flag (item E)
        if job.get('intro') is not None:       # the fixed series intro was looked at once; a passing truck's straight
            OI = _intro_mod(job['intro'])      # edges behind Lucia trip the flag at 0.9 s (GTA VI ep 2, 11 Nov 2026)
            lead = float(getattr(OI, 'SECS', 3.0))   # the intro sits ahead of the body, so card spans move by its length
            spans = [(a + lead, b + lead, r) for a, b, r in spans] + [(0.0, lead, 'series intro (fixed, checked once)')]
        if spans:
            print('smear check: exempt ' + ', '.join(f'{a:.2f} to {b:.2f} s' for a, b, _ in spans) + ' (our own cards)', flush=True)
        st_, body_ = _starts(job)
        cuts = list(st_) + [body_]             # each frame measured against its own shot, the end card its own (item D)
        if job.get('intro') is not None:
            cuts = [0.0] + [c + lead for c in cuts]
        if SG_.soft(job):                      # hard stop 4 of 4: the finished Reel must decode; a smear is a warning
            errs_ = DC.decode_errors(video)
            if errs_:
                raise ValueError(f'{video}: decode errors ({len(errs_)}), first: {errs_[0]}')
            SG_.guarded('smear', DC.check, video, [w for w in job.get('block_ok', []) if len(w) == 3] + spans, cuts=cuts)
        else:
            DC.check(video, [w for w in job.get('block_ok', []) if len(w) == 3] + spans, cuts=cuts)   # stops before anything is committed
        import fillcheck as FC                 # no empty band at any second, read on the Reel that ships (9 Nov 2026)
        st_, end_ = _starts(job)
        if SG_.soft(job):
            SG_.guarded('fill', FC.empty_bands, video, job, st_, end_, C.U)
        else:
            FC.empty_bands(video, job, st_, end_, C.U)
        import looks
        if job.get('kind') not in ('breaking', 'famitsu') and not series(job):
            looks.record(job, style or reel.pick_style(out))
        DC.dense_strip(video, base + '-dense.jpg')
        reel.strip(video, base + '-strip.jpg')
        footage_shots = [s for s in shots(job, build=False) if not s[0].startswith(NG.SUB + '/')]
        if footage_shots:
            reel.shotsheet(footage_shots, base + '-sheet.jpg')
        else:                                   # a numbers Reel of our own cards only (8 Nov 2026): the sheet is the cards
            gfx_sheet(job, base + '-sheet.jpg')
        lifeless_note(job, video)
    pipe = {'fetch': round(fetched, 1), 'shots': round(t_shots - t_src, 1),
            'checks': round((t_src - t_fetch) + (t_gate - t_shots), 1), 'render': round(t_render - t_gate, 1),
            'after': round(time.time() - t_render, 1)}
    if not draft:
        _times_note(job, 'pipeline', pipe)
    print('render_job: pipeline: ' + json.dumps(pipe), flush=True)
    if not draft:
        _times_note(job, 'softgate', {'warnings': len(SG_.WARNINGS), 'ladder': SG_.LADDER})
    print(f"render_job: {job['name']} done in {time.time() - t0:.0f} s (fetch {fetched:.0f} s): {video}", flush=True)
    return video


if __name__ == '__main__':
    step, path = sys.argv[1], sys.argv[2]
    job = json.load(open(path))
    import autoshots as AS                      # "shots": "auto" and [file, "auto", secs, focus] (gates-fix C)
    AS.expand(job)
    if step in ('check', 'run'):
        import buildgate                        # ledger, story file, lane, reel-check before anything (adv-20261105-p2-audit-fixes)
        import softgate as SG_
        if SG_.soft(job):                       # never refuse (card A): the gate's findings are warnings
            for p_ in buildgate.problems(path, job):
                SG_.warn('build gate', p_)
        else:
            buildgate.enforce(path, job)
    if step == 'check':
        print(job['name'], 'ok, clip %.1f s' % check(job))
    elif step == 'text':
        if '--fix' in sys.argv[3:]:            # the mechanical fixes first, written back to the job file (item B)
            import autofix as AF
            before = json.dumps(job, sort_keys=True)
            AF.text(job)
            if AF.LOG:
                AF.save_log(os.environ.get('AUTOFIX_JSON'))
                if '--dry' not in sys.argv[3:] and json.dumps(job, sort_keys=True) != before:
                    json.dump(job, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                    print(f'autofix: {len(AF.LOG)} text fix(es) written to {path}', flush=True)
        import buildgate                        # the gate's findings join the text findings: one pass lists every error
        gate_path = os.environ.get('PRERENDER_SRC') or path   # prerender copies the job to a temp folder; the gate
        errs = [{'where': 'build gate', 'rule': 'gate', 'text': '', 'fix': '', 'detail': p}   # reads its repo path
                for p in buildgate.problems(gate_path, job)]
        if any(str(e.get('detail', '')).startswith('spoken: ') for e in errs):
            job = dict(job, _gate_spoken=True)   # the gate already lists the missing paragraph; the text check skips it
        try:
            textcheck(job, collect=errs)
        except Exception as e:             # anything unforeseen still reports with the rest
            errs.append({'where': 'text check', 'rule': 'error', 'text': '', 'fix': '', 'detail': f'{type(e).__name__}: {e}'})
        import softgate as SG_
        if SG_.soft(job):                       # never refuse (card A): only unreadable text stops (safe zone, bidi)
            for e in [e for e in errs if not SG_.text_hard(e)]:
                SG_.warn('text', f"{e.get('where')}: {e.get('rule')}: {e.get('text') or ''} {e.get('detail') or e.get('fix') or ''}".strip())
            errs = [e for e in errs if SG_.text_hard(e)]
        if '--json' in sys.argv[3:]:
            out = sys.argv[sys.argv.index('--json') + 1]
            json.dump({'job': job.get('name'), 'ok': not errs, 'problems': errs}, open(out, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
        if errs:
            print(text_report(errs))
            print('TEXTCHECK_JSON: ' + json.dumps({'job': job.get('name'), 'ok': False, 'problems': errs}, ensure_ascii=False))
            sys.exit(1)
        print(job['name'], 'text ok')
        print('TEXTCHECK_JSON: ' + json.dumps({'job': job.get('name'), 'ok': True, 'problems': []}))
    elif step == 'focus':
        focus(job, path); print(job['name'], 'focus written')
    elif step == 'run':
        run(job, draft='--draft' in sys.argv[3:])
    else:
        raise SystemExit(f'unknown step {step!r}: run, check or focus')
