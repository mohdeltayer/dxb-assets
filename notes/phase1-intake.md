# Phase 1 INTAKE: the server prepares stories before anyone asks

Card adv-20261029-server-handover (approved by Mohammad): dxb-render-1 becomes the pipeline in four gated phases.
Phase 1 is INTAKE. This note covers its first increment, built 29 Oct 2026 on `build/2026-10-29-phase1-intake`
(backlog B7, prepared trailers; the watch go-live; event capture later). Nothing here changes a render, a job file, a
ledger or a post.

## What runs where

| Where | What | When | State after tonight |
|---|---|---|---|
| dxb-render-1, user `runner`, user-level systemd | the watch (`ops/backoffice/watch/`): official sources and outlets into `~/backoffice/watch/watch.db`, digest pushed to dxb-watch | poll every 5 min, digest at :52 | built and tested since 27 Oct; installed by the main session after the release with `backoffice-install.yml`, `service=watch` |
| same | prepare (`ops/backoffice/prepare/`): watch items above the threshold into prepared assets in `/var/cache/dxb-render/prepared/` | every 10 min at :03, nice 10, idle IO | in the repo; installed with the timer OFF, started on Mohammad's go (`enable=true`) |
| same, as an Actions job | renders (render.yml, render-live, render-breaking) | on job commits | unchanged; prepare and the watch stand aside while one runs |
| GitHub, dispatch only, main only | `backoffice-install.yml`: install.sh, then test.sh, then unit status, as the runner user | by hand from the main session | new tonight |
| the main session (cloud container) | reads the watch digest from dxb-watch; writes job files | hourly watch, rolling queue | unchanged tonight; reading prepared assets needs the hand-over below |

Nothing listens on a port. Nothing runs as root. Everything is rebuilt from git by `install.sh`; the only state is the
SQLite files, the prepared store and the model cache, all disposable.

## Data flow

```
official feeds / YouTube channels / pages
   -> watch.py poll           watch.db items (title, url, media links, source kind, first_seen, breaking)
   -> prepare.py from-watch   score >= 4 (official 2, video link 2, trailer word 1, Steam link 1, breaking 1),
                              2 items a tick, each once
   -> acquire.plan/fetch      1 publisher file -> 2 press asset -> 3 Steam -> (4 live, 5 YouTube: refuse)
   -> analyse                 decode, bitrate floor, smear, scenes, faces, subjects, text, blocks, focus, sheet, beats
   -> /var/cache/dxb-render/prepared/<key>/  source.mp4, manifest.json, sheet.jpg, beats.json
   -> ~/backoffice/prepare/timings.jsonl     one line per asset for the 2 Nov gate
   -> (later) render_job.py   uses the prepared file and shot map when a job names it
```

### How render_job.py would pick up a prepared asset (phase 2; not changed tonight)

1. The job's footage item gains one optional key: `{"file": "x.mp4", "steam": 2221490, "trailer": "Launch Trailer",
   "trailer_id": 9, "start": 12, "seconds": 40, "prepared": "<key>"}`. The manifest's
   `source.steam.render_job_footage` already holds the steam, trailer and trailer_id values to paste.
2. `render_job.fetch`: when `prepared` is set and `$DXB_CACHE/prepared/<key>/manifest.json` reads `status: ready`,
   its `source.url` matches the item (same Steam trailer id, or the same URL) and `source.mp4` exists, the stretch is
   cut from the local file (`-ss start -t seconds -c copy`, as the URL path does today) instead of downloaded. The
   manifest's clean decode stands in for the download's decode check, and the log line says so. Anything missing,
   expired or different: today's download, unchanged. That is the fallback and the parity case.
3. `render_job.py focus`: a null focus whose shot starts inside a prepared scene takes that scene's `focus_keys` as a
   Pan, instead of running YOLO. The shot sheet shows prepared flags (`text`, `cut_text`, `profile`, `blocky`) beside
   its own.
4. Prerender (`prerender.py`) can read the manifest's per-scene text and black frames instead of OCRing again.
5. Gated like any render change: parity on three published jobs without the key, a feature job with it, off by
   default (the key), release note.

### Hand-over to the main session (built 29 Oct, build desk)

The main session works in a cloud container and cannot read the server's disk, and footage must not go into
dxb-assets (public) or an Actions artifact of a public repo. So after every tick that changed the store, prepare
pushes `prepared/index.json` (one entry per asset of the last 7 days: key, game, status, the watch item and its first
seen time, source method and page, Steam trailer and whether it is likely the announced one, rights basis and credit,
probe, flags, scene summary, focus found, timings) and `prepared/sheets/<key>.jpg` (the contact sheet of each ready
asset) to the private dxb-watch repo, branch `prepared` (`handover.py`). The branch is replaced by one commit each
time (force push), so expired sheets go and the repo stays small; the watch's `main` branch is never touched (the
code refuses it). It reuses the watch's remote, token file and push plumbing (`handoff.git_env`); the watch's own
code is unchanged and no new secret is needed. Query strings are stripped from every URL and no server path leaves
the server. `prepare.py handover [--force]` runs it by hand; `PREPARE_HANDOFF=off` writes
`~/backoffice/prepare/handover/out` only. Source files stay on the server; the render job reaches them by key
(phase 2). The main session reads it with `git clone --depth 1 --branch prepared` of dxb-watch once the repo is
attached to its session.

## Disk and CPU

Measured in this container (4 cores, shared with another agent's render the whole time, so these are upper bounds):

| Asset | Source | Wall | CPU | Size | Biggest steps |
|---|---|---|---|---|---|
| Cyberpunk 2077 Steam trailer, 81 s, 1920x1080 30 fps, 5.6 Mbps | Steam HLS | 169 s | 254 CPU-s | 59 MB | smear 41 s, text 39 s, subjects 22 s, scenes 21 s, frames 16 s, decode 10 s |
| synthetic 9 s, 1280x720 | local | 21 s | about 30 CPU-s | 1.6 MB | text, smear |
| Kitsune: The Journey of Adashino, 60 s (watch item: Nintendo of America announcement) | Steam, by title search | 137 s | 170 CPU-s | 44 MB | smear 33 s, text 25 s, scenes 15 s, decode 10 s, fetch 15 s |
| Slime Rancher 2, 58 s (watch item: Nintendo of America) | Steam, by title search | 171 s | 254 CPU-s | 42 MB | |
| Spirit Crossing, 60 s (watch item: Nintendo of America) | Steam, by title search | 236 s | 303 CPU-s | 44 MB | |

The last three are a real `from-watch --max 6` run on a watch ledger built in the container from the live feeds
(29 Oct 13:17Z): the top six items were all Nintendo of America YouTube trailers; three found their game on Steam by
exact name and were prepared, then the fourth stopped at the (test) disk floor as designed, because the shared
container disk had fallen to 1.5 GB. Two of the three Steam trailers chosen were older trailers of the same game
(`name_match` 0.0, `item_trailer: unknown`), which matters for "trailer news shows the trailer" (26 Oct rule): the
manifest says so, and the brief must not treat such an asset as the announced trailer. The smear check flagged the
stylised glitch transitions of the Kitsune PV (scenes 9, 10, 31 on its sheet): recorded, never a stop here.

Rule of thumb: about 3 CPU-seconds and 0.75 MB per second of 1080p trailer (4K: about 2 MB/s). Tesseract runs with
`OMP_THREAD_LIMIT=1`: with its default threads one frame took 13 s here, with one thread 0.3 s.

Volume, from a real watch pass in this container (29 Oct, 13:15Z, 24-hour window): 655 items, 59 above the threshold,
almost all official YouTube channel uploads (Nintendo of America, Xbox, PlayStation), with duplicates across channels
(Witchbrook on Xbox and PlayStation; the dedup by source stream prepares it once). Assuming about 40 unique trailers a
day reach a source and average 100 s:

* CPU: 40 x 300 CPU-s = about 3.3 CPU-hours a day, about 3.5% of a 4-core server's day, all at nice 10 and paused
  whenever a render runs.
* Disk: 40 x 75 MB = 3 GB a day, about 21 GB at the 7-day expiry; the 80 GB store cap and the 40 GB free-space floor
  bound it either way. Models 4 MB, venv about 670 MB, beat cache negligible.
* Network: the same 3 GB a day down, from Steam's CDN and publishers' hosts.

Most YouTube-only items will end `refused` (step 5 is off) unless the game is on Steam under the exact name in the
title; the manifests and the `seen` table will show the real share in the first days. That share is the main input to
the YouTube decision (media toolbox E2).

## Shadow plan for the 3-day gate (to Monday 2 Nov)

1. Day 0 (after Mohammad's go): `backoffice-install.yml service=prepare enable=true`. The watch must be live first.
2. Days 1 to 3, shadow: prepare runs; render jobs are written exactly as today (no `prepared` key exists yet). Every
   prepared asset logs its timings and its watch item's `first_seen`.
3. For each Reel ops builds in those days whose trailer was prepared, ops notes in the story file: assignment time
   (story picked), job commit time, and whether it read the prepared sheet when choosing shots (once the hand-over
   exists; until then the build desk pulls the sheets for the card). Reels without a prepared asset are the control.
4. Gate card on Mon 2 Nov: median time from assignment to job commit with and without a prepared asset; for three
   Reels, the shots ops chose next to the prepared scene map (contact sheet, suggested focus, text and profile
   flags) and the published strip; prepare's own numbers (assets a day, refused share and why, CPU minutes, disk,
   paused ticks, any tick that ran while a render ran).
5. Pass: no render slowed or failed because of prepare, disk never under the floor, and a measurable gain or a clear
   path to one (phase 2 pick-up). Fail: the timer goes off (`enable=disable`), the files stay for the next attempt.

## Licences (full table in ops/rights-register.md)

PySceneDetect BSD-3-Clause; OpenCV Apache-2.0; YuNet MIT and NanoDet-Plus Apache-2.0 (OpenCV Zoo, official files,
sha256-pinned); librosa ISC; numpy BSD-3; PyYAML MIT; tesseract Apache-2.0; streamlink BSD-2 (step 4, not used by
prepare yet); Cocktail Fork MIT (optional). YOLOv8 is not used here.

## Not done tonight

Steps 4 (Twitch) and 5 (YouTube) refuse; render_job pick-up; PaddleOCR; the
Cocktail Fork split was not run (no torch in the container); the units have not been loaded by a real user manager.
