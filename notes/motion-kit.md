# Digital Lounge motion kit: pilot results (24 Oct 2026)

Advisor memo of 24 Oct 2026, agreed with Mohammad (CLAUDE.md, "Digital Lounge motion kit: pilot").
Branch `pilot/motion-kit` only: nothing posted, nothing in reel.py, render_job.py, render.yml or the live path.

## What was built

`templates/motion-kit/` on the pilot branch:
- `kit.js`: one KIT object of reusable GSAP blocks, each added to a paused timeline at a time `t` and returning the
  times its sound blips land on. Same timings on every skin.
- `kit.css`: the look as tokens (ground, accent, plate, radius). A skin swaps the tokens only, never the motion.
- `blips.py`: tiny UI sounds from our four-note motif (D, F#, A, E), mixed 14 dB under the Reel's own peak.
- `compose.py`: builds a HyperFrames composition per kit moment, renders it on the Reel's own frames
  (frame-exact segment as background, so the joins are seamless), lays it back with hard cuts and adds the blips.
  `demo`, `sample` and `sbs` commands.
- `.github/workflows/motion-kit-pilot.yml`: its own workflow and concurrency group, push to the pilot branch only,
  never triggered by jobs/render/*.json. Fonts cloned into a temp folder and deleted, never committed.

## The elements, and the reading problem each one solves

| Element | Motion (all under 0.5 s) | Reading problem it solves |
|---|---|---|
| a. Photo box | play-triangle wipe 0.35 s, frame draws 0.3 s, name plate rises 0.25 s | On people stories the eye has to find a face it does not know. The wipe opens from the centre of the box, so the eye lands on the face before the name, and the plate arrives last, once the face has been seen. |
| b. Number count | 0 to the figure in 0.45 s, then a 4% pop over 0.2 s | A static figure reads as decoration and is often skipped. The count marks it as the fact and settles in under half a second, so it is readable from the first held frame. |
| c. XP bar | fills to the share in 0.45 s, one glint 0.25 s | A percentage alone needs mental arithmetic; the bar shows the share at a glance, and the single glint ends the motion so the card is still while it is read. |
| d. Chip press | in at 112%, under to 94%, settles at 100%, 0.3 s | The chip (جديد، رسمي، تقرير) says how sure the story is; the press makes the eye pass over it once before the headline. |
| e. Unlock banner | slides in from the top 0.3 s, holds 1.5 s, out 0.25 s | Only for real records and milestones: it says "this is a record" in one glance, so a line does not have to. Not used in the sample (Helldivers is not a record). |
| f. Card transition | the play-triangle wipe in and out, 0.35 s and 0.26 s | Tells the viewer a card starts and ends, so a card never reads as a frozen frame of the footage. |
| g. Sound | tick, settle, open, press, unlock, wipe; 40 to 160 ms, tonal, never noise | Marks the moment the fact lands for viewers with sound on; 14 dB under the Reel, so never over speech. |

## Sample Reel

The published Helldivers 3 Reel (23 Oct) re-rendered on the runner without its person window and without the 95%
line (`templates/motion-kit/base-job.json`, `cards/2026-10/mk-helldivers-base-reel-v1.mp4`), then two kit moments
over it:
1. Photo box, 0 to 7.4 s: Johan Pilestedt, «المدير الإبداعي في أروهيد (Arrowhead)», his studio photo credited.
2. Number card with the bar on the closing shots (8 to 10), 95% «من فريق أروهيد» «يعمل على Helldivers 2»,
   ending 2 s before the end card so the last two seconds stay a picture.

Outputs (pilot branch, `templates/motion-kit/out/`):
- `mk-demo-v1.mp4`: every element on the house ground, one after another, labelled أ to و.
- `mk-helldivers-kit-v1.mp4`: the sample with the kit.
- `mk-helldivers-sbs-v1.mp4`: side by side, the published Reel (left) and the kit version (right), with the kit's sound.

## Render times (runner, 4 cores, HyperFrames 0.8.143)

| Piece | Seconds of video | Render |
|---|---|---|
| Demo | 14 s | 23.0 s |
| Photo box over the Reel | 7.4 s | 42.8 s |
| Number and bar card | 2.8 s | 19.1 s |
| Base Reel (reel.py, no kit) | 20.8 s | 169 s whole job |

Two kit moments add about a minute to a Reel on the runner. Container: the demo took 28.5 s with the fallback font.

## Findings from the frames

- Every element settles inside 0.5 s and nothing moves while a line is up; text is fully readable on the first
  settled frame (4 fps strips).
- Joins are clean: the kit is composed over the Reel's own frames, so there is no fade of two cards and no jump.
- Photo box from 0 s: the first frame, the grid tile, shows the small play triangle in the middle of the box instead
  of the face. Either the box is already open on frame 0 (the wipe only when it starts after the cover) or it opens
  at 0.4 s. Recommended: open on frame 0, since the cover should show the person (people rule, 23 Oct).
- The number card holds 2.5 s at rest, enough for the label, figure and note (about 30 characters).
- Arabic shaping and the right-to-left plate lines were right in every frame; the Dubai font lived only in the
  composition's temp folder.

## Decision needed (Mohammad, element by element)

a. photo box, b. number count, c. XP bar, d. chip press, e. unlock banner, f. card transition, g. sound.
Approved elements join the HyperFrames inserts under the 24 Oct limited-use memo, with the same fallback and the
director QA check "does this motion help reading?". The breaking profile keeps only d and b, or nothing.
