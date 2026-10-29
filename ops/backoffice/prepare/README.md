# Prepared trailers on dxb-render-1 (back office service 4, phase 1 INTAKE)

A script, not an agent. Every 10 minutes it reads the mechanical watch's ledger, takes the items that point at a
trailer from a first-party source, fetches the best official copy in the agreed order, runs the source checks once,
maps the shots, faces, subjects and burnt-in text, and stores the result with its rights record. A render can then
start from a checked file and a shot map instead of a download. No Claude tokens, no posting, no Publer, no secrets.

Card: adv-20261029-server-handover (phase 1 INTAKE), backlog B7. Built 29 Oct 2026 on
`build/2026-10-29-phase1-intake`. **Status: in the repo only; the timer is OFF until Mohammad's go.** Design note:
`notes/phase1-intake.md`. Rights: `ops/rights-register.md` and `rights.yaml` here.

## What it does with one item

```
watch.db item (score >= 4)  ->  plan: candidates in order 1 publisher file, 2 press asset, 3 Steam, 4 live, 5 YouTube
                            ->  fetch the first that works (4 and 5 refuse cleanly today)
                            ->  probe, full decode (one re-fetch on errors; a second damaged copy is kept as
                                "damaged" with no source file), bitrate floor, smear windows
                            ->  scenes (PySceneDetect AdaptiveDetector, 0.5 s minimum shot)
                            ->  4 frames a scene: YuNet faces (side-on flag), NanoDet subjects, tesseract text on the
                                cut frame and the middle frame, letterbox, block ratio when the 9:16 crop passes 2x,
                                a suggested focus with two keyframes (reel._window's meaning: 0 left, 1 right)
                            ->  contact sheet, beat grid of the trailer's sound (librosa), optional Cocktail Fork stems
                            ->  <store>/<key>/{source.mp4, manifest.json, sheet.jpg, beats.json}
```

The **threshold** (`score` in prepare.py, `PREPARE_MIN_SCORE`, default 4): official source (official, youtube, x or
page kinds of the watch) 2; a video link in the item (its media, a YouTube or Twitch link, an .mp4) 2; a trailer
word in the title (trailer, teaser, reveal, gameplay, announce, launch, showcase, PV, トレーラー ...) 1; a Steam
store link 1; a breaking source 1. An item with no video link, trailer word or Steam link never passes. Outlet and
Google News items never pass on their own (no official point). At most `PREPARE_MAX_ITEMS` (2) items a tick, highest
score then newest; each item is tried once (`seen` table), whatever the outcome.

**Acquisition** (`acquire.py`): step 1 takes an .mp4/.mov/.m4v linked from the item's own page only when its host
belongs to a publisher in `rights.yaml` (or is a generic CDN and the page is the publisher's own); step 2 follows at
most three links to a publisher's press-asset host and takes video files there; step 3 takes the Steam app linked
from the page or summary, else one Steam store search on the title's game name (exact name match only), and picks the
trailer whose name shares most words with the item's title (ties: the newest); steps 4 and 5 are recorded and refuse.
YouTube, Twitch and X pages are never read. No logins, no cookies, no third-party downloaders.

**Rights**: every manifest carries `rights` (publisher, basis, terms, credit line, excerpt-only, on-screen credit,
music flag, `rights_review` for unreviewed publishers) plus the embargo and music sentences found on the page, for a
person to read. A file from a host no publisher entry claims is never taken at steps 1 and 2.

## The manifest (version 1)

`source` (step, method, page, exact URL, fetch time, bytes; for Steam the appid, trailer name and id and the
`render_job_footage` entry a job file would use), `attempts` (each step tried and why it was refused), `rights`,
`watch` (the item, its score and reasons), `probe`, `checks` (decode, bitrate flag, smear stretches), `scenes` (start,
end, picture box, zoom, focus and keyframes, faces, profile, subjects, text words, text on the cut frame, words the
suggested window would cut, block ratio, per-frame detail), `summary`, `audio` (beats, split), `tools` (versions and
model files), `timings` per step, `cpu_s`, `bytes`. Every asset also adds one line to `~/backoffice/prepare/
timings.jsonl` (the 2 Nov gate compares time from assignment to job commit with and without a prepared asset).

## Commands

```
prepare.py one 1091500 --name cp2077 [--title "Launch Trailer"]   # a Steam app by hand
prepare.py one https://news.ubisoft.com/... --name x              # a page: steps 1 to 3 in order
prepare.py one ~/in/vertical-cut.mp4 --name x --rights sega --page "<where it came from>"   # a file that was sent
prepare.py from-watch [--dry-run] [--max N]                       # what the timer runs
prepare.py cleanup [--dry-run] | status | list [--all] | show <key> | models | beats [files or folders]
```

Exit codes: 0 done or nothing to do, 1 failure, 75 paused for a render or held by the disk floor (the unit treats
75 as success).

## Hand-over to the news desk

After each tick that changed the store, `handover.py` pushes `prepared/index.json` and the contact sheets of ready
assets to the private dxb-watch repo, branch `prepared` (one commit, force-pushed; never the watch's `main`). It uses
the watch's remote and token file from `../watch/sources.yaml` and the watch's push helper; no footage, no server
paths and no URL query strings leave the server. A failed push is logged and retried on the next change; it never
fails the tick. `prepare.py handover --force` pushes by hand; `PREPARE_HANDOFF=off` writes
`~/backoffice/prepare/handover/out` only (the tests run that way).

## Server rules it keeps

* Runs as the `runner` user from a user-level timer (`dxb-prepare.timer`, every 10 minutes at :03), at nice 10 and
  idle IO, one tick at a time (lock file). No ports, no root, nothing hand-configured: `install.sh` builds it all
  from this folder.
* **Renders always win**: a tick that starts while `render_job.py` or a `Runner.Worker` is running exits 75 at once;
  a render that starts mid-asset makes it wait between steps (15 s checks) for up to `PREPARE_PAUSE_WAIT` (600 s),
  then give up the tick (the half-written folder is removed by the next cleanup). Note that every Actions job on the
  runner is a `Runner.Worker`, so prepare also stands aside for event capture and server checks.
* **Disk**: assets older than 7 days (`PREPARE_KEEP_DAYS`) are deleted; while free space is under 40 GB
  (`PREPARE_FLOOR_GB`) or the store is over 80 GB (`PREPARE_MAX_STORE_GB`) the oldest assets older than an hour go
  first, and no new fetch starts unless about 0.6 GB would still leave the floor. Only folders in the store are
  touched.
* Store: `/var/cache/dxb-render/prepared/<key>/` when that cache is writable (where render jobs on the server can read
  it), else `~/backoffice/prepare/assets/`. Models: `/var/cache/dxb-render/models/opencv-zoo/`. Neither is in git.

## Install (as runner, no sudo), after Mohammad's go

From main, through the workflow (preferred): `gh workflow run backoffice-install.yml --ref main -f service=prepare`
installs with the timer OFF and runs test.sh; `-f enable=true` starts the timer; `-f enable=disable` stops it.
By hand: `~/dxb-assets/ops/backoffice/prepare/install.sh [--enable | --disable]`.

## Test

`ops/backoffice/prepare/test.sh` compiles every file and runs `test_prepare.py` offline on synthetic clips (28 tests:
threshold and order, the digest fallback, acquisition order and host rules, refusals for steps 4 and 5, rights
records and the register, Steam trailer choice and fetch from a local stream, a full asset, a damaged source, the
publisher-file path end to end, one trailer seen on two channels prepared once, NanoDet decoding, letterbox, detectors when the models are cached, 7-day expiry,
the disk floor, the render pause, the lock and the beat cache). `test.sh --online [appid]` also prepares one real
Steam trailer into a temp store.

## Known limits

* Faces use YuNet's five landmarks for a yaw proxy (nose offset over eye distance), not MediaPipe's landmarker as
  reel.autofocus does; it flags side-on faces, it does not measure the angle.
* NanoDet sees COCO classes: game characters that are not human-shaped (creatures, mechs) are often missed or
  misnamed ("kite", "umbrella"); the focus uses only people, vehicles and animals and falls back to none.
* tesseract reads Latin text; Arabic and Japanese title cards need PaddleOCR (media toolbox E3, later).
* The Steam search takes a result only when its store name is exactly the game name at the head of the title
  ("Kitsune: The Journey of Adashino – Announcement Trailer" needs a store app named "Kitsune: The Journey of
  Adashino"); a game listed under another name is missed, not guessed. A new trailer not yet on Steam yields an
  older Steam trailer of the same game (`name_match` in the manifest says how well the trailer names agreed).
* Cocktail Fork stems run only with `PREPARE_SPLIT=on` and `COCKTAIL_DIR` set; not run in this container (no torch).
* The units were checked by `install.sh` in a temp home without a user manager; the first `systemctl --user` run on
  the server is the real test, as with the watch.
