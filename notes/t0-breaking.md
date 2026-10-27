# T0 breaking path (advisor card adv-20261027-build-until-thursday, item 2)

Branch `build/t0-breaking`. Nothing here changes render.yml, render-live.yml, publishing, Publer, dxb-queue or any live job file.

## What was built

1. **Profile passthrough** (`templates/render_job.py`, `profile_of`). `"profile"` is read from the job and handed to `reel.reel(profile=)`.
   A job whose label is «عاجل» defaults to `breaking` (no picture finish, no demucs, `-preset veryfast -crf 20`);
   `"profile": "standard"` opts out. A job with neither key and a different label gets `None`, exactly the call it made before.
   tracksplit.py and designpass.py already skipped breaking by label or profile.
2. **The T0 card** (`templates/breaking.py`, job `"kind": "breaking"`, format in its docstring). One image (a file, or the frame of a
   clip at a given second with the letterbox cropped), one headline, one line, credit line, chip, persistent mark, breaking bed
   (`sonic` flavour `breaking`) and the standard end card, all through the existing layer code (`reel.head_layer`, `line_layer`,
   `mark_layer`), so chip row, grid-corner rule, safe zone, Dubai type and crimson theme are the house ones. The image takes a 6% push
   over the whole clip and a wave plate drifts over it: nothing is static from frame one. Length 8 to 22 s before the 2 s end card
   (headline 0 to 3.5 s, credit at 2 s, the line from 3.6 s for its reading time plus 1.6 s).
   - Cached per theme (`breaking.parts`, `~/.cache/digi-sound/breaking-plate`, keyed on the theme's colours and `VER`, not on file
     times, so a fresh checkout or an Actions cache hit never rebuilds): wave mask, theme gradient, scrim. The drift is a crop
     expression over the cached mask. The end-card master and the bed come from `outro.card_master` and `outro.evolving_bed`;
     `python3 templates/breaking.py warm <job>|--all` builds them ahead (bed for the job's length and one second more, so
     `outro.append`'s ceil always hits).
   - Per story: the push (one `zoompan` at 2x, the only real per-frame work), PIL text layers, ONE ffmpeg pass (image, scrim, plate,
     text, each text layer cropped to its own box, stills decoded once and held with the loop filter), then `outro.append`'s single
     veryfast encode plus the cached end card. No montage pass, no separate text pass, no demucs, no shot sheet. The commit step's
     file set is kept: `-sheet.jpg` is the source picture with the 9:16 window at the start and end of the push and the
     enlargement, `-strip.jpg`, `-dense.jpg` and the decode and smear check run as for every Reel.
   - Gates kept: the 2x enlargement cap counts the push (past it the render stops unless `lowres_ok` names the copies searched),
     `rtl_starts` and the safe-zone checks via the layer code, `render_job.py text` and `check` know the kind.
3. **Routing** (`.github/workflows/render-breaking.yml`, composite `.github/actions/t0-render`, `templates/render_route.py`).
   dispatch only, main only, guard as render-live. `route` (hosted, seconds) asks the Actions API whether any run has a job on a
   `dxb-render` runner queued or in progress. Busy (or the API unreadable): `hosted` renders at once. Free: `server` is
   asked, and a hosted standby waits 25 s for the server job to start; if it did not (server offline) the standby claims the render
   and renders on GitHub; the server's first step stands down if GitHub already claimed. No concurrency group anywhere, so a second
   dispatch never waits behind the first (it finds the server busy and goes to GitHub). Both lanes run the same composite steps
   (fonts to a temp folder and deleted, text check, warm caches, render with `runner_stats`, commit back with the render-times
   entry, Publer media upload for `jobs/breaking/` only). GitHub lane installs only ffmpeg and pillow, numpy, pedalboard, soundfile
   (no torch, YOLO, tesseract) and restores `~/.cache/digi-sound` through actions/cache.

## How to dispatch

The workflow file must be on `main` before `gh workflow run` can find it (merge this branch first; production does the merge).

    gh workflow run render-breaking.yml --ref main -f job=jobs/test/warhorse-cyberattack-t0.json
    gh workflow run render-breaking.yml --ref main -f job=jobs/test/pokemon-unite-end-of-service-t0.json
    # production: -f job=jobs/breaking/<name>.json   (consumed; the Reel lands in Publer's media library)
    # -f lane=server|hosted forces a lane; default auto

Test jobs stay in `jobs/test/` and are never uploaded to Publer. Outputs land in `cards/2026-10/<name>-reel-v1.mp4` with strip, sheet
and dense strip. Run `python3 templates/render_job.py text <job>` first on a machine with the font; both test headlines and lines
were written to the measures of the standard jobs but could not be wrap-checked here (no Dubai font).

## Timings

Measured in the build container (4 cores, a stand-in font, a synthetic 1080p image, 8.3 s card plus the 2 s end card, warm caches
for the theme): checks 1.0 s, compose 15 to 25 s, outro 9 to 14 s, so render 26 to 41 s, whole job about 50 s with the decode check,
dense strip and strip. Cold caches add about 20 s (end-card master) and 2 s (bed) and 1 s (plate). The server has 8 cores, but the
push is single-threaded, so expect about the same; the other stages speed up.
Expected on the server, warm: render 30 to 40 s, whole job under 1.5 minutes with setup. Expected on GitHub, cold: about 1 minute of
setup (ffmpeg, pip, fonts clone) plus the route job (10 s) plus about 70 s of render with the master built, so 2.5 to 3 minutes; with
the cache restored about 2 minutes. Target met on a warm server (render under 60 s, job under 2 minutes), not yet proven on GitHub.
Standard Reels for comparison: 126 to 263 s render, 4 to 6 minutes whole job.

## Comparison plan (standard Reel vs T0)

For Warhorse and Pokémon UNITE, dispatch both test jobs on the server and, forced `-f lane=hosted`, on GitHub. Read from
render-times.json and the run summaries: route time, setup, stage seconds, whole job seconds, peak memory. Put each T0 Reel beside
the published standard Reel (frames from the strips; first frame as a 3:4 grid tile) and judge: is the first frame a scroll-stopper,
is the line readable at phone size, is the crop right (sheet), does the plate help or distract, is the breaking bed right.
Honest expectation: a T0 card is a holding Reel, one image and one line; the standard Reel with a trailer stretch is the better
product when 4 minutes are available. Use T0 when the story is minutes old and the standard path would take longer than the news stays fresh.

## Not done or not proven

- The workflows were not run (they need main and the server); YAML was syntax-checked only. `render_route.py` was run once with no token
  (falls back to the hosted lane as designed).
- No Dubai font here: layout checked with a stand-in font, so wrap and look need the first run's strip and sheet.
- The two test jobs take their picture from the official trailers' frames (times 10.0 s and 30.0 s, focus from the standard jobs);
  judge on the sheet and move them. A key-art file in `footage` with `"image": "<file>"` is the better source when one exists.
- A standard footage Reel on the breaking profile has a different picture-cache key (the finish is part of it): warm its cache under
  `reel.FINISH = False` or the first render pays for it.
- Rumours, leaks and single-outlet reports stay out of the breaking lane's auto-go; T0 changes the build, not the rules.
