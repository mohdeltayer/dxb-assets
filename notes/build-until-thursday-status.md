# Build until Thursday: status (27 Oct 2026, advisor card adv-20261027-build-until-thursday)

Two branches built by helpers were reviewed, checked for parity and merged into main. Nothing here changes the live
path: `render.yml` (push of `jobs/render/*.json`), `render-live.yml`, `publer-upload.yml` and the Publer upload code are
untouched, and `jobs/test/` is not matched by any trigger (`render.yml` watches `jobs/render/*.json` only).

## Review changes

- `build/t0-breaking`: the «عاجل» label no longer selects the `breaking` profile. `render_job.profile_of` returns a
  profile only when the job carries `"profile": "breaking"`; the code stays, gated behind the explicit key. Docstring and
  `notes/t0-breaking.md` updated.
- `prerender.yml` guard (both jobs) accepts `jobs/test/<name>.json` as well as render, live and prerender.
- `.github/actions/t0-render`: the hosted lane's ffmpeg install is three short attempts (60 s update, 75 s install each)
  instead of one 150 s attempt, after a stalled mirror download lost the first Warhorse test (below).
- Merge conflict: `render_job.check()` (clean-map line from prerender, breaking branch from T0): both kept, breaking first.

## Parity (`render_job.py check`, footage in uploads)

Jobs from main history: Don't Nod union job cuts (659fa02), The Division 50 million agents (ad651e4), Nintendo Indie World
Oct 28 (7e6e994), run from a folder outside `jobs/render/`. Output compared byte for byte with main's on main, on each
branch and on the merged tree: identical for all three (`ok, clip 18.4 s`, `ok, clip 15.0 s`, `ok, clip 14.6 s` with
`speech: none`). A «عاجل» job without `profile` gets `None` from `profile_of`.

## Test runs (dispatched on main after the merge)

| Run | Lane | Result | Timings |
| --- | --- | --- | --- |
| prerender, Don't Nod v1 (`jobs/test/dont-nod-v1-prerender.json`) | server (dxb-render, 8 cores) | ran, reported NOT CLEAN (exit 1 by design); job then marked failed by the server's job-completed hook (below) | whole run 3 min 38 s; fetch 76 s, luma 31 s, frames 43 s, suggest 35 s, check 10 s |
| render-breaking, Pokemon UNITE T0 | hosted (server busy) | success, card committed | route 10 s, setup 34 s, render 21 s, whole run 84 s; 1.5 GB peak memory |
| render-breaking, Warhorse T0, first try | hosted (server busy) | failed in Tools: ffmpeg download stalled past the 150 s timeout | 3 min; fixed (above) |
| render-breaking, Warhorse T0, second try | server (idle) | rendered and committed; job marked failed only by the server's job-completed hook | setup 20 s, render 49 s (caches warm 16 s, compose 20 s), whole run 2 min; 1.4 GB peak memory |

Prerender finding on Don't Nod v1: shots 0, 1 and 8 sit on black and fade frames (11.1 to 13.7 s, 16.3 to 17.2 s of the
Aphelion trailer), shots 2, 5 and 7 are within 0.3 s of black or a smear, with a clean start suggested for each. This is
the kind of fault the map is meant to catch before a job is committed. For comparison, the standard Warhorse Reel took 232 s on the GitHub runner and
the standard Pokemon UNITE Reel 114 s render, 183 s job.

Outputs (committed by the runs, in `cards/2026-10/`): `pokemon-unite-end-of-service-t0-reel-v1.mp4`, `-strip.jpg`,
`-sheet.jpg`, `-dense.jpg`; and the same four for `warhorse-cyberattack-t0`. The prerender summary is the run's log
(it commits nothing); its clean map is printed between `::prerender-map-begin::` and `::prerender-map-end::`.

## Needs Mohammad

- The self-hosted server's `job-completed.sh` hook exits 1 when `pkill` finds nothing, so every server job ends red after
  its work succeeded (the two server runs above). The fix is already on `ops/self-hosted-runner` (6e11bcc) but is not on
  main and not yet installed on the server; until it is, a red server run needs its log read, not a re-run.
- The T0 and pre-render items still need his look at the cards (strips above) before anything goes live.
