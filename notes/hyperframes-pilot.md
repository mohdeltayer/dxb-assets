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

## Design pass 2 (advisor, 24 Oct 2026, agreed with Mohammad)

Same rules as the pilot: branch `pilot/hyperframes` only, idle time only, nothing posted. Side-by-sides:
`templates/hyperframes/out/sbs-gta6-numbers-v2.mp4`, `templates/hyperframes/out/sbs-oshima-card-v2.mp4`
(published Reel left, pass 2 right, no sound); renders `*-hf-v2.mp4`, timings `out/render-times-v2.json`.

a. GTA 6 numbers card
- Uses the whole safe zone: chip at y 355, headline, logo plate (640 x 190 at y 640), the card at y 856 to
  1336 and the story line at y 1378, so the stack runs from 355 to about 1460 with no empty lower band.
- The figure is the hero: 205 px (the published card's figure is about 190 px; pass 1 was 140), still
  counting up, «6.08 مليون» with the number on the right; label in the accent at 58 px.
- The footage is dimmed less (brightness 0.72 and a 3 px blur, was 0.42 and 9 px), so the marina, the
  WELCOME sign and the boat read as GTA. Soft indigo bands sit only behind the headline and the line.
- Contrast check behind the type (`templates/hyperframes/contrast_check.py`: snapshots with the type
  hidden, the brightest 5% of the ground in each text box against our ink): headline 8.6:1 or better,
  line 12.0:1 or better over ten frames from 0 to 8.9 s (the bar is 4.5:1).
- Card 1 is gone (4.2 to 4.5 s) before card 2 arrives, so the two never overlap in one box. Platform bars
  are larger (50 px bars, 64 px percentages). Logo plate, count-up and bars kept.

b. Oshima character card
- Opens on CD PROJEKT RED's image full screen at 1.78x (under the 2x cap), framed as the published Reel
  framed it, with a light shade over the Reels UI zone only; the headline sits on a soft band.
- 0.95 to 1.75 s: the photo shrinks into the window. Done with transforms and a clip-path, not left/top:
  HyperFrames' lint flags layout tweens because they snap to whole pixels and stutter under frame-by-frame
  capture. The window is reframed hair to chin (the image at 0.95x there); pass 1 showed the face only
  from a smaller crop.
- The card is larger and lower: rows 76 px, labels 38 px, values 46 px, from y 1030 to 1476, the safe
  zone's floor, so there is no empty band under it. Arabic labels, English names, the yellow label style,
  the HUD readout, the break-up cut and the ending on the anime portrait kept.
- Grid corner (x 940 to 1080, y 240 to 380) on frame 0: photo only, no chip or text pixels.

Checked at phone size on snapshot sheets (fallback font in the container; wraps judged on the runner's
Dubai render) and on the runner output's frames.
