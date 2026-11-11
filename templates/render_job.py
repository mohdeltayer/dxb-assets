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
               + (['-headers', hdr] if hdr else []) + ['-i', item['url'], '-t', str(item['seconds']),
               '-c', 'copy', dst + '.part.mp4'])
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
                gs = job.get('ground_still')      # the game's key art behind the card, blurred and dimmed (9 Nov 2026)
                NG.slide(C.U + f, secs, job.get('ground_theme', job['theme']), C.U + clip,
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
        raise SystemExit(f'render_job: {e}')


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
        raise SystemExit('render_job: ' + '; '.join(problems))
    return style


def check(job):
    if job.get('kind') == 'breaking':
        return BK.check(job)
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
    first_frame_check(job)
    cover_picture_check(job)
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
        n = 0
        for a, b, texts in job['lines']:
            for x in texts:
                n += 1
                text, kw = (x, {}) if isinstance(x, str) else (x[0], x[1] if len(x) > 1 else {})
                if show:
                    kw = dict({k: v for k, v in kw.items() if k not in ('top', 'lift', 'size', 'step', 'shade')},
                              size=reel.SHOW_LINE[0], step=reel.SHOW_LINE[1], lift=lift)
                elif job.get('strip') and 'lift' not in kw:
                    kw = dict(kw, lift=reel.STRIP_LIFT) if hasattr(reel, 'STRIP_LIFT') else kw
                _do(f'line {n}', reel.line_layer, text, f'{tmp}/l.png', skin=skin, **kw)
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
        for i, c in enumerate(job.get('credits') or [], 1):
            _do(f'credit {i}', reel.credit_layer, c[2], f'{tmp}/c.png')
        if job.get('intro') is not None:       # the series intro's title and days line (Dubai font)
            OI = _intro_mod(job['intro'])
            if job['intro'].get('series') == 'gtavi':
                _do('intro', OI.layers, job['intro']['days'], tmp, job['intro']['episode'])
            else:
                _do('intro', OI.layers, job['intro']['days'], tmp)
        for x in job.get('person') or []:          # needs the photo in uploads: fetched like footage before this runs
            o = x[5] if len(x) > 5 else {}
            if os.path.exists(C.U + x[0]):
                _do('person', reel.person_layer, x[0], x[1], x[2], f'{tmp}/p.png', job['theme'],
                    focus=tuple(o.get('focus', (0.5, 0.33))), credit=o.get('credit'))
        _do('gfx', gfx, job, tmp)
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)
    if errs and collect is None:
        raise ValueError(text_report(errs))


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
    if job.get('music_only') and not rec.get('applied'):   # asked for no effects: never ship the trailer's own mix instead
        raise ValueError('music_only: the music stem could not be separated cleanly (' + str(rec.get('reason')) + '); '
                         'use another stretch or track "bed"')
    import sfxplan as SF                       # a fallback on a track under other moments' shots fails the job
    try:
        SF.guard(job, rec, starts)
    except ValueError:
        _times_note(job, 'audio_split', rec)
        raise
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
    reel.CLEAN_MAP = job.get('clean_map')       # pre-render map (templates/prerender.py); None changes nothing
    quality(job)
    for item in job.get('footage', []):
        fetch(item)
    gfx(job)
    source_check(job)
    fetched = time.time() - t0
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    dp_plan, DP_folder = design_plan(job) if not draft else (None, None)
    DP_apart = None
    if DP_folder:
        import designpass as DP
        DP_apart = DP.apart_spec(dp_plan, DP_folder)
    tup = lambda v: v if v is None or isinstance(v, str) else tuple(tuple(x) if isinstance(x, list) else x for x in v)
    style = look(job)
    done = reel.reel(shots(job, draft), job['headline'], job['label'], place(job), job['source'], job['date'], out,
                     theme=job['theme'], style=style, sound=job.get('sound'), country=job.get('country'),
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
    if not draft:
        spans = gfx_spans(job)                 # our own cards are exempt from the smear flag (item E)
        if job.get('intro') is not None:       # the fixed series intro was looked at once; a passing truck's straight
            OI = _intro_mod(job['intro'])      # edges behind Lucia trip the flag at 0.9 s (GTA VI ep 2, 11 Nov 2026)
            lead = float(getattr(OI, 'SECS', 3.0))   # the intro sits ahead of the body, so card spans move by its length
            spans = [(a + lead, b + lead, r) for a, b, r in spans] + [(0.0, lead, 'series intro (fixed, checked once)')]
        if spans:
            print('smear check: exempt ' + ', '.join(f'{a:.2f} to {b:.2f} s' for a, b, _ in spans) + ' (our own cards)', flush=True)
        DC.check(video, [w for w in job.get('block_ok', []) if len(w) == 3] + spans)   # stops before anything is committed
        import fillcheck as FC                 # no empty band at any second, read on the Reel that ships (9 Nov 2026)
        st_, end_ = _starts(job)
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
    print(f"render_job: {job['name']} done in {time.time() - t0:.0f} s (fetch {fetched:.0f} s): {video}", flush=True)
    return video


if __name__ == '__main__':
    step, path = sys.argv[1], sys.argv[2]
    job = json.load(open(path))
    if step in ('check', 'run'):
        import buildgate                        # ledger, story file, lane, reel-check before anything (adv-20261105-p2-audit-fixes)
        buildgate.enforce(path, job)
    if step == 'check':
        print(job['name'], 'ok, clip %.1f s' % check(job))
    elif step == 'text':
        import buildgate                        # the gate's findings join the text findings: one pass lists every error
        gate_path = os.environ.get('PRERENDER_SRC') or path   # prerender copies the job to a temp folder; the gate
        errs = [{'where': 'build gate', 'rule': 'gate', 'text': '', 'fix': '', 'detail': p}   # reads its repo path
                for p in buildgate.problems(gate_path, job)]
        try:
            textcheck(job, collect=errs)
        except Exception as e:             # anything unforeseen still reports with the rest
            errs.append({'where': 'text check', 'rule': 'error', 'text': '', 'fix': '', 'detail': f'{type(e).__name__}: {e}'})
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
