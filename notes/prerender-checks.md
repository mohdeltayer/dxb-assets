# Pre-render footage checks (advisor card adv-20261027-build-until-thursday, item 1)

Branch `build/prerender-checks` (not merged). Goal: most render retries come from footage the runner rejects, or that
review rejects after the render. Read the footage before the job is committed, say which shots sit on a bad stretch,
and where the nearest clean start is.

## What was built

| piece | file |
|---|---|
| the checker | `templates/prerender.py` (`python3 templates/prerender.py <job.json> [--write] [--out f] [--no-ocr] [--no-check] [--ci]`; `embed <job> <map>`) |
| the map format and its helpers (pure Python, no heavy imports) | `templates/cleanmap.py` |
| reader in the render path | `reel.CLEAN_MAP` + a block at the end of `reel.quality_gate`; `render_job.check/run` set it from the job; `render_job.clean_nudge` |
| CI | `.github/workflows/prerender.yml` (dispatch only) + `templates/prerender_ci.py` (gate and stand-down) |
| measurement | `newsroom/render_retries.py` (`python3 newsroom/render_retries.py 3 [--causes]`) |

### What it flags

Every footage shot's source stretch, start to start + secs, read 0.3 s either side as well. Exit 1 when any shot's exact
span overlaps a hard interval or a job-level problem exists; a hard interval only inside the 0.3 s margin is printed
`near` and does not fail.

| reason | how | severity |
|---|---|---|
| `black`, `black+fade` | whole-file ffmpeg `signalstats` luma pass at 320 px: a frame at video-range black (YAVG <= 22), plus the rising or falling ramp into it (a cut of 25 levels or more ends the ramp) | hard |
| `frozen` | ffmpeg `freezedetect` (n 0.003), 0.6 s or longer, not already black | hard |
| `smear` | `decodecheck.smear_times` on the stretch with 1 s of context | hard |
| `blocky` | `decodecheck.block_ratio` through `reel.source_quality`, shots enlarged past 2x, unless `blocky_ok` waives | hard |
| `endcard "..."` | tesseract words rating, ESRB, PEGI, USK, CERO, copyright, rights, reserved, subscribe, trademark, licensed, presents, wishlist, www, http, follow; or a dark frame (mean luma under 40) with writing in the last 10 s (or 15%) of the file | hard |
| `cut-text` | two or more distinct words that cross the 9:16 window's edge (`reel._word_boxes`, the sheet's rule); one word is soft | hard / soft |
| `text` | any readable word inside the window (a HUD is text too); hard only in the first 0.6 s of the first shot (the grid tile) | soft / hard |
| `lowbit` | `decodecheck.bitrate_flag` | warning, as in `quality_gate` |
| job problems | under 960 rows of picture without a valid `lowres_ok`; a bare `lowres_ok`; a shot past the end of its file; a shot whose file is not in uploads; a source that will not decode twice; `render_job.check` (timeline, lines too fast, speech under the track) unless `--no-check` | hard |

The OCR reads one frame every 0.5 s at 1280 px, at the window each shot will actually use (`reel._window` with the
shot's focus). The `(c)` sign is lost by the sheet's letters-only filter, so only the words above are matched.

### What it suggests

For a failing shot: the nearest start with the same length that is clear of every hard interval by 0.15 s, not on another
shot's footage from the same file, and (verified) clean on the same frame checks (OCR, smear, block ratio) over
start - 0.3 to end + 0.3. Up to four candidates are tried. It also offers the longest clean piece of the shot itself
("keep the clean part: start X, N s") when that is 1.2 s or longer, and says so plainly when the file has no clean
window that long.

### The map, and reading it

`clean_map` in the job (not a sibling file: `render.yml` takes any `jobs/render/*.json` as a job). Hard intervals only
(about 1 KB), the stretches it deep-checked, and the verified suggestions:
`prerender.py <job> --write` puts it in the job; from a CI log use `prerender.py embed <job> <map.json>`.
A waived interval stays out of the map: `prerender_ok` [[file, t0, t1, reason of 5+ characters]] waives any reason;
the job's existing `block_ok` waives a smear whose start lies in it.

With `clean_map` in the job: `reel.quality_gate` (run by `render_job.check` and by `reel()` before the montage) adds
`clean map (prerender): shot N file at S for D s: a to b s black+fade; prerender suggests starting at X` to its error,
and prints a note for a shot the map did not cover (the shot list changed). `"clean_nudge": true` moves such a shot to the
verified start instead (`render_job.clean_nudge`, applied wherever `shots()` is read, so the sheet and the render agree).
Without `clean_map` nothing in `reel.py` or `render_job.py` runs differently: `CLEAN_MAP` is None, `clean_nudge` returns
its input, and `cleanmap` is never imported.

### Workflow

`.github/workflows/prerender.yml`, `workflow_dispatch` only, from main only, `contents: read` + `actions: read`.
`gh workflow run prerender.yml --ref main -f job=jobs/prerender/<name>.json [-f ref=<branch or sha>] [-f wait=300]`.
Put the file in `jobs/prerender/` (render.yml watches `jobs/render/*.json` only), on main or on a scratch branch.

- `server`: `runs-on: [self-hosted, dxb-render]`. Code from main; the job file alone is read from `ref` with
  `git show` (data, never run), so a branch cannot run code on the server. Dubai font from `dxb-fonts` into a temp
  folder for `render_job.py text` (continue-on-error; skipped with a note when absent), deleted at the end; footage into a
  temp uploads folder, deleted at the end. Then `prerender.py --ci`.
- `gate` (ubuntu-latest, up to `wait` seconds): watches the `server` job through the run's own job records
  (`prerender_ci.py gate`). Still queued after 5 minutes: `fallback=true`.
- `fallback` (ubuntu-latest): the same steps with ffmpeg, tesseract and pip installed as `render.yml` does.
- A server that picks the job up late stands down when the fallback has run (`prerender_ci.py yielded`). A server job that
  never gets a runner stays queued until the server returns or the next dispatch for the same file cancels the run
  (concurrency, cancel-in-progress: the workflow only reads). The result is in the job summary and the log between
  `::prerender-map-begin::` and `::prerender-map-end::`; nothing else is uploaded.
- The workflow cannot be dispatched until it is on main (GitHub only lists dispatchable workflows from the default
  branch); it was not run on Actions from this branch. `actionlint` is clean except its unknown label `dxb-render`.

## Baseline (git history only, `newsroom/render_retries.py`, last 3 days to 27 Oct 2026 14:55Z)

24 Reels with a Publer receipt (the receipt commit exists from 26 Oct, so 7 days gives the same 24):

| measure | value |
|---|---|
| job commits per Reel (versions pushed) | mean 2.25 |
| retries per Reel (job commits - 1) | mean 1.25; 15 of 24 had at least one; worst 4 (Don't Nod) |
| first job commit to first receipt | median 10.3 min, mean 18.1, worst 60.9 (Golden Joystick), best 4.2 |
| no retry (n=9) | median 6.2 min |
| with a retry (n=15) | median 23.8 min |

Retries are a floor: a re-dispatch without a change and a failed run leave no commit. `--causes` lists the 30 retry
commits with their subjects. Read by hand: 16 touch the footage (smear flags and their waivers 7: Golden Joystick,
Castle Doom, Honkai, Division, Street Fighter v3, Pokemon UNITE, Library of Ruina; black frames and fades 2: Don't Nod;
a dark flicker, a letterboxed shot, trailer call-outs, an item card, runner copies offset onto title cards 5: Steam
Scream x2, Street Fighter v2, Scramble Knights, Silent Hill; two are output-only smear waivers on Castle Doom and Golden
Joystick that a source read cannot predict), and 14 are text, timing, strip or spelling fixes (Call of Duty x2, Type-0 x3,
Honkai x2, Division, Don't Nod x2, Steam Scream, Steam most-wishlisted x2, PAYDAY), which the text and timeline checks
in the same workflow now run before the commit.

## Validation (this container, 4 cores, other jobs running, so timings are upper-ish)

### (a) Don't Nod union job cuts, footage `dn-aphelion.mp4`, `dn-lostrecords.mp4`

v1 job (7c67d04, the one rendered at 63c4895), 2 min 34 s: NOT CLEAN.
- shot 0 (12.0 +3.6): `11.11 to 13.68 black+fade`: the shot opens inside a fade up from black. Nearest clean start 7.36.
- shot 1 (16.0 +1.6): `16.25 to 17.18 black+fade`.
- shot 2 (18.0 +1.0): `18.80 to 19.80 black+fade`: the black frames at source 18.8 s the review found.
- shot 5 (46.0 +1.1): `46.38 to 47.51 black`: the black from 46.37 s the review found. Nearest clean start 45.13.
- shot 8 (8.0 +3.2): runs 0.09 s into the same fade at 11.11.
- shot 7 (70.2 +2.3): a smear read at 72.60 to 73.30, within 0.3 s, `near`.

Three renders and two job-fix commits (659fa02, 4e58d4c) went by before the Reel was scheduled; every one of them was found by
eye. The shot 0 and shot 1 findings are not in what the review fixed: the Reel scheduled for 15:30Z (job 4e58d4c, v2,
`cards/2026-10/dont-nod-union-job-cuts-reel-v2.mp4`) opens at mean luma 40 (the fade up from black under the headline) and
has a near-black frame at 3.62 s (YAVG 18; checked by eye: the headline and strip over black). Both come from the source at
11.7 to 13.7 s and 16.25 to 16.5 s. Prerender on the 4e58d4c job: shots 0, 1 and 8 FAIL, shots 2 and 5 `near`.

Timings: fetch and full decode 26 s, luma 31 s (two files in parallel), frame passes 44 s, suggestions 46 s.

### (b) Pokemon UNITE end of service (job 9b355a5, failed on the runner with the source smear flag)

v1 (4fe8044^), 3 min 19 s: NOT CLEAN. `shot 1 unite-emp.mp4 12.05 +1.8: 13.82 to 13.98 s smear (peak 18.2)`; nearest clean start
14.13, or keep the clean part: start 12.05, 1.77 s. The runner failed at 13.7 to 14.1 s on the same stretch; the fix
(4fe8044) trimmed the shot to 1.55 s and waived 13.7 to 14.1 in `block_ok`. v2 (4fe8044): CLEAN, the smear listed as waived.

The 659fa02 job (the version the card names), 2 min: shots 0 (12.0, `11.11 to 13.68 black+fade`, or keep 13.68 +1.92 s), 1 and 8 FAIL;
shots 2 (18.0 +0.75, black from 18.80) and 5 (45.5 +0.8, black from 46.38) pass with `near`: the black-frame trim of that
commit left 0.05 s and 0.08 s of margin. The v1 black frames (18.8 s, 46.37 s) are the intervals above.

### (c) Golden Joystick nominees v1 (cdb51ca; its retry d97dd25 was "waive the source smear flag"; 3 job commits and one finished render over 61 minutes)

`--no-check`, 2 min 55 s: NOT CLEAN. shot 0 (43.0 +3.3): `45.73 to 46.27 smear (peak 26.1)`, the flag d97dd25 waived after the
runner failed (a clean cut and an iris wipe); shot 4 (23.0 +2.7): `25.05 to 25.38 black+fade`; shot 12 (63.5 +2.6):
`65.95 to 66.65 endcard: dark frame with writing near the end`. Looking at the smear before the first commit and waiving it
in `block_ok` then is the saving here; the output-stage smear of the third retry (the Big Walk cut) is not something a source
read can predict.

### Cost, per job

Fetch and full decode 14 to 34 s (what the render does too; on the server the footage is not kept between runs, so the
render fetches again: a shared footage cache under `$DXB_CACHE` would save that and is not done), luma pass 24 to 68 s
(whole file, parallel over files), frame passes (OCR, smear, block ratio) 42 to 92 s, suggestions 7 to 81 s and only for a failing
shot, `render_job.check` 6 to 35 s (the 35 s is faster-whisper reading the track). 2 to 3.5 minutes in all on this shared
4-core container; it runs while the Arabic and the story file are written, against a render of about 4.5 minutes per retry.
`--no-ocr` and `--no-check` shorten it.

## Not done, limits

- The workflow was not dispatched (it must be on main first); `gate`/`yielded` logic was checked by reading, not by a run.
- Card-led shots on `ground_footage`, `person` photos, `-gfx-` cards and stills are not read; the track's stretch is read only
  for speech (`render_job.check`), not for effects-heavy audio.
- OCR is tesseract at 0.5 s: a text flash shorter than that, a small logo and stylised type can be missed, and a HUD in
  gameplay is reported as a soft `text` finding (no failure). `cut-text` and `endcard` can be false positives on dark scenes
  with writing; waive with `prerender_ok` after looking.
- The output-stage smear flag (decodecheck on the finished Reel) and the Steam HLS copy that differs between downloads
  (Silent Hill) are not predictable from the source; pinning the judged stretch under `live/` is still the answer there.
- No change to `render.yml`, `render-live.yml`, publishing, Publer, dxb-queue, the inbox, or any job file on main.
- New system packages: none on the server (ffmpeg, tesseract, python are in `runner-setup.sh`); the GitHub fallback installs
  them as `render.yml` does. On a fresh container: `apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-eng`.
