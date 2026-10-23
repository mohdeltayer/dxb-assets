# HyperFrames pilot: results (23 Oct 2026)

Advisor memo of 23 Oct 2026, agreed with Mohammad. Pilot only, on the branch `pilot/hyperframes`; nothing
live was touched (reel.py, render_job.py, render.yml, the job format, Publer: unchanged). Nothing from the
pilot is posted or scheduled. Mohammad decides; until then the branch stays unmerged.

## What was built

HyperFrames 0.8.143 (Apache 2.0; pinned to a release over two weeks old), compositions in HTML with GSAP
3.14.2, 1080x1920 at 30 fps, rendered frame by frame in headless Chrome and encoded with FFmpeg.

| Piece | Folder | Compared with | Length |
|---|---|---|---|
| a. Numbers card counting up on the game's own footage, dimmed and moving, with the GTA VI logo plate | `templates/hyperframes/gta6-numbers/` | `cards/2026-10/gta-6-pre-orders-sensor-tower-estimate-reel-v1.mp4` (20 Oct, numgfx on the flat indigo ground) | 9.0 s |
| b. Edgerunners 2 character card rebuilt vertically in a sci-fi skin, Oshima style: labels Arabic (الاسم · تاريخ الميلاد · فصيلة الدم · الدور · يؤديه), names English, a HUD readout with a digital break-up | `templates/hyperframes/oshima-card/` | `cards/2026-10/cyberpunk-edgerunners-2-kojima-reel-v1.mp4` (19 Oct, CD PROJEKT RED's card cut by the 9:16 crop: "RTHDAY", "eo Kojima") | 8.0 s |

Facts and wording are the published stories' own (Sensor Tower via GI.biz for a; CD PROJEKT RED's two
announcement images for b). Side-by-sides: `templates/hyperframes/out/sbs-gta6-numbers.mp4`,
`templates/hyperframes/out/sbs-oshima-card.mp4` (published Reel left, pilot right, no sound).

## Render time

| Piece | Container (4 cores, fallback font) | Runner (4 cores, Dubai) | File |
|---|---|---|---|
| a. GTA 6 numbers (9 s, with a video layer) | 43 s | 48.7 s | 5.6 MB |
| b. Oshima card (8 s, stills and CSS) | 23 s | 20.1 s | 4.5 MB |

The whole runner job, setup included (font clone, Node, HyperFrames and Chrome Headless Shell install,
asset fetch, both renders, commit), took 2 min 04 s (run 40013385876). For comparison, a full Reel on the
render runner takes about 2.5 to 5 minutes. HyperFrames pieces are short, so in a live Reel they would be
rendered as layers or inserts and joined, not as the whole Reel.

## What worked

- Arabic shaping and right-to-left order come from the browser: every line joins correctly in Dubai, and
  mixed lines keep the right order with no manual work. The figure reads «6.08 مليون» with the number on
  the right, as Arabic outlets set it; the published card has the number on the left.
- Latin names inside Arabic lines are held together with `<bdi>` and `white-space: nowrap`, so a wrapped
  line never opens on a Latin word, a digit or a bracket (the 13 Oct rule). In the first local test the
  "2" of "Edgerunners 2" wrapped onto its own hidden line until this was added.
- Count-ups, bar fills, slide-ins and the break-up cut are a few lines of GSAP each, and the frame is the
  same on every render (no randomness, no clock).
- The game's footage behind the card is a plain `<video>` with a CSS blur and dim; the footage moves for the
  whole piece, as the 20 Oct "no flat backgrounds" memo asks.
- The Dubai font stays private: it is cloned into the runner's temp folder, copied beside a temp copy of the
  composition, and deleted at the end. Nothing font-related is in git or in an artifact.

## Problems and limits found

1. Layout bugs come from CSS, not from the tool: a shared `inset: 0` rule stretched the chip and the cards
   in the first draft; fixed in minutes once seen. Every piece needs a snapshot check, as our shot sheets do.
2. The container has no Dubai font since the reset, so local previews use a fallback font with different
   widths; final wraps can only be judged on the runner, as with reel.py today.
3. `workflow_dispatch` only runs from the default branch, so the pilot workflow starts on a push to this
   branch's pilot files instead. It is still never triggered by `jobs/render/*.json`, has its own
   concurrency group (`hyperframes-pilot`) and commits only to `pilot/hyperframes`.
4. Piece b was meant to end on the matching Edgerunners 2 trailer shot. No plain MP4 of the trailer was
   reachable (IGN pages 404; YouTube is not used), so it ends on CD PROJEKT RED's official anime portrait,
   shown inside the window at 1.7x (contained, so the 2x cap holds).
5. Design trade-off on b: the published Reel shows Kojima's photo full frame, which is more cinematic; the
   pilot frames it in a window to give the card room, so the photo is smaller but every word reads. A live
   version could open full frame and shrink into the window as the card arrives.
6. Pieces carry no sound yet (the pilot is picture only); in a Reel they would sit on the trailer's sound or
   our bed under the existing rules.
7. The HyperFrames AI-media skills (voiceover, avatars, stock music) were not used, as the memo says. The
   authoring skills were not installed into the session either; the CLI's own docs (`hyperframes docs`)
   and lint, check and snapshot commands were enough for two pieces.

## For Mohammad's decision

If approved, a separate memo would cover where HyperFrames fits: cards, counters, character and fact cards,
transitions and the skins, rendered as inserts on the runner and joined into the reel.py output. If not, the
branch stays unmerged and nothing changes.
