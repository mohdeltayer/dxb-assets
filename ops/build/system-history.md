# System history: build and pilot notes moved out of CLAUDE.md

The build desk's reference. These sections were moved word for word out of CLAUDE.md when the operations
desk's instructions were trimmed to news only (adv-20261028-three-desks, step 3). They describe how the
render chain, its checks, the tools and the pilots were built and why. Rules that still bind the operations
desk stay in CLAUDE.md as short pointers.

<!-- moved from CLAUDE.md lines 832 to 839 (28 Oct 2026 version), word for word -->
- Autofocus aims at a subject (advisor, 14 Oct 2026): `reel.autofocus` runs a
  small object detector (YOLOv8n on CPU) on three frames per scene and centres
  the 9:16 window on the largest person, vehicle or animal; the spectral
  saliency stays as the fallback when nothing is detected. Each scene returns
  two keyframes (the subject at 25% and 75% of the scene) so the window pans
  with a moving subject, and `reel.shotsheet` draws the crop window on the full
  16:9 frame next to each cropped frame. First draft goes to Mohammad before
  use; applies from the next Reel after it lands.

<!-- moved from CLAUDE.md lines 963 to 1114 (28 Oct 2026 version), word for word -->
- Render time (advisor, 14 Oct 2026):
  1. The final encode is `-preset medium -crf 18` (`reel.FINAL_ENC`; was
     slow, 15) in reel.py, numgfx.py, edition.py and outro.py's per-Reel
     pass; `-preset slow` stays only for the cached end-card masters.
     Instagram re-encodes to about 5 Mbps, so the difference is not
     visible after upload.
  2. One encode per Reel: the montage and the text pass write lossless
     intermediates (`reel.INTER_ENC`, `-preset ultrafast -qp 0`, mkv with
     pcm sound; a near-lossless crf 8 when the disk has under 3 GB free),
     the track and voice steps copy the video, and only `outro.append`
     encodes.
  3. The picture pass (bars, denoise, enlarge, cas, grade) is cached per
     (file, start, duration, focus) under `uploads/cache/` as
     `<key>.mkv` (`reel.cached_shot`); the montage takes the cached clip
     as a plain input, so a text or strip change re-burns the text over
     the cache. The daily cleanup removes cache clips untouched for 3
     days like other fetched footage.
  4. End cards are rendered once per (sound, theme, quiet, platforms) as
     a master (`outro.card_master`, in `~/.cache/digi-sound/`, preset
     slow, with the jingle and a 0.3 s fade in from the ground) and joined
     to the body with the concat demuxer, no re-encode. The body's final
     encode ends on a 0.3 s fade to the ground in place of the old
     crossfade.
  5. Breaking profile for the breaking lane (`reel(..., profile=
     'breaking')`, `reel.PROFILES`): trailer template, FINISH off, no
     demucs (a 'music' track falls back to the plain stretch), the final
     encode `-preset veryfast -crf 20`, no draft step; target under 2
     minutes.
  6. For dated stories in `newsroom/events.md`, the footage is fetched and
     the picture pass cached the evening before (`reel.warm_cache(shots)`;
     the evening pre-fetch card in `newsroom/delegation.md`).
  7. If slot batches still queue behind one render, renders move to a
     GitHub Actions workflow in dxb-queue (one job per story, in
     parallel). Cost before switching: about 8 to 12 Actions minutes per
     Reel on the 2-core runner (the free tier's 2,000 minutes a month
     covers about 170 Reels; a paid minute is $0.008, so a 12-post day is
     about $1), plus the Dubai font as an encrypted secret because it
     cannot go in the public repo, and the footage uploaded with the job.
     Not switched; measured first.
  Measure before and after: every render appends its seconds per stage
  (checks, montage, text, audio, outro) to
  `templates/assets/render-times.json`, and the render task card records
  them for the next ten Reels. Baseline, the Xbox Nano Reel (18.6 s, a
  still, a graphic and a still) on the old chain, is in the same file.
- Render runner (advisor, 20 Oct 2026, agreed with Mohammad; supersedes point
  7 above): routine renders move to GitHub Actions in dxb-assets to add
  capacity. dxb-assets is public, so the standard Linux runners are free with
  no minute limit (4 cores, to be confirmed on the first run). The 2016
  MacBook Pro (dual-core i5, 8 GB) is about as fast as the container and may
  serve later as a second slot. Nothing already running changes until the
  test in 6 passes, and the container stays the fallback.
  1. Set up by Mohammad on 20 Oct: Actions allowed for all actions; the
     repo's default workflow permission stays read-only; the private repo
     mohdeltayer/dxb-fonts holds `dubai.zip` (the same archive as
     `/root/fonts-private/dubai/`, not loose TTFs); a fine-grained token
     "render-fonts" (dxb-fonts only, Contents read-only, no expiry) is the
     dxb-assets secret `FONTS_TOKEN`. Rotate it if anything else ever needs it.
  2. Fonts: never committed, never uploaded as an artifact, never printed.
     The workflow clones dxb-fonts with `FONTS_TOKEN` into a temp folder
     outside the workspace, unzips `dubai.zip` there, points `DUBAI_FONTS`
     (read by `fast_ar.FONTS`) at it and deletes it at the end.
  3. `.github/workflows/render.yml` declares `permissions: contents: write`
     itself, so it is the only workflow that can commit back. Triggers: a push
     to main of `jobs/render/*.json`, or workflow_dispatch; never
     pull_request. One matrix job per job file: checkout (sparse, templates and
     jobs), fonts, ffmpeg, tesseract and the Python packages (YOLO included),
     footage fetched from the job's URLs, `templates/render_job.py run`, then
     one commit with the mp4, strip and sheet in `cards/YYYY-MM/`, the run's
     render-times entry (`runner: actions`, cores, whole-job seconds) and the
     job file deleted; it rebases and retries when parallel jobs race.
  4. The job file (`jobs/render/<name>.json`, format in `render_job.py`)
     carries everything reel() needs: footage (a Steam trailer by app and
     name prefix, a direct URL, or a file committed under `live/`), shots
     with times and focus, the by_shot line groups, headline, label, source,
     date, theme, style, template, strip, credits, track, cut. The main
     session picks `style` (and `sound` for silent footage) when it writes
     the job, so the rotation ledgers stay in its commits. No tokens, Postiz
     IDs or unreleased material: the repo and the Actions logs are public.
     `render_job.py check <job>` runs the timeline and reading checks first.
  5. Flow: the main session commits a job file and moves to the next story; it
     queues the Reel once the render commit lands and the strip is checked,
     as now.
  6. First test before any switch: re-render one published Reel on the runner
     (the Cyberpunk 2077 Edgerunners 2 update, container render 10:54Z, 94.8
     s), compare look and timing with the container's version, record the
     minutes in render-times.json, report to Mohammad. Only then do routine
     renders move. If Actions is down or a run fails, render on the container.
  7. Test result, 20 Oct 2026, 15:21Z (`cards/2026-10/cyberpunk-2077-edgerunners-
     2-update-october-22-runner-*`): the runner has 4 cores. Length identical
     (20.561 s), and headline, lines, strip, credit, chip, theme, style and
     end card match the published Reel frame for frame. Render 153 s on the
     runner from a cold cache (montage 43, text 60, outro 48) against 95 s on
     the container, whose picture cache and end-card master were already warm
     from the sheet and draft; the whole job took 214 s with the footage
     fetch and autofocus, about 5 minutes with setup. Gain: renders run in
     parallel, one runner per job, and the container stays free. One
     difference: the crop on three shots, because the runner's autofocus
     (YOLO) chose other subjects. So the job file carries the focus judged on
     the shot sheet: `render_job.py focus <job>` fills every null focus on the
     container before the sheet, and the runner only autofocuses what is left
     null. A first run failed at the font step (`dubai.zip` holds lowercase
     `.ttf` only); fixed.
  8. First job (advisor memo, 20 Oct 2026, received about 16:40Z; it
     replaces the re-render test of 6): the first runner job is a real new
     routine story with footage, not a re-render; while it renders, the next
     story renders on the container, two Reels at once. The runner's Reel is
     committed as usual and sent to Mohammad, and held: not scheduled in
     Postiz until he approves; after his OK it goes out under the normal
     rules. Fallback: if the runner job fails or passes 15 minutes, the same
     story renders on the container, and the failure and its log line are
     noted (no secrets). Both lanes go to render-times.json: story, lane
     (runner or container), queued at, finished at, render minutes, and setup
     minutes on the runner (`RENDER_LANE`, `RENDER_QUEUED_AT`; the workflow
     adds `setup_min` and `job_secs`). Breaking renders stay on the
     container. State when it arrived: the re-render test had already run
     (15:21Z) and three runner Reels were already queued under the rolling
     queue (ARC Raiders 16:45Z, Game Pass wave 2 17:15Z, Ace Combat 8
     17:45Z); once in Postiz only Mohammad can pull them, and he was told at
     16:41Z. The container has no Dubai font since the reset, so points 2
     and 4 (render on the container) wait for `dubai.zip`; until then the
     runner is the only lane. From Mortal Shell II on, runner Reels are held
     for his OK.
     Reminder (advisor, 20 Oct 2026): every runner Reel is held for his OK
     until he says the runner is trusted; the story file's approved line
     reads "held for Mohammad (runner)" until his OK is recorded. ARC Raiders
     (16:45Z) went out on "go: rolling queue" without that hold; Game Pass
     wave 2 and Ace Combat 8 were already in Postiz too (he was told; only he
     can pull them).
     Hold lifted (Mohammad, 20 Oct 2026, about 17:17Z: "lift the runner
     hold", after his OK on Mortal Shell II): the runner is trusted. Runner
     Reels now go out under the normal rules (rolling queue, preview at
     queuing, breaking lane as written), with no separate hold; the story
     file's approved line carries the usual note.
  9. Runner hang (23 Oct 2026, 00:30 to 02:00Z): five runs sat silent in the
     Tools step at `apt-get install` until cancelled or timed out, most
     likely a fresh VM's apt timers holding the dpkg lock. render.yml now
     stops the apt timers, gives dpkg a lock timeout, skips installs already
     present, shows apt's output, stamps each install with the time, and
     times the step out at 10 minutes. A hang shows as a Tools step past 3
     minutes: cancel, then start a fresh run on main (workflow_dispatch with
     the job), not a re-run of the old commit's workflow.
  10. Safeguards (Mohammad, 26 Oct 2026, inbox: "Add all five", from the render-facts card):
     peak memory and disk are sampled during every render (`templates/runner_stats.py`) and added
     to its render-times entry (`peak_mem_mb`, `peak_disk_mb` and the totals); the Render step
     times out at 15 minutes; a job that dies with no error from our own steps (its last step,
     "Failure marker", never ran) and committed nothing is re-dispatched once with `retry=1` by
     the `retry` job (`templates/render_retry.py`, the only job with `actions: write`), never
     twice; one run per job file at a time (job-level concurrency, `cancel-in-progress: false`),
     so a second dispatch waits instead of cancelling; separated audio stems are cached per
     trailer stretch (`SPLIT_CACHE`, keyed on the decoded samples and the model commit, 800 MB
     cap). Production reads a run's step times before cancelling it, and never calls a render
     hung under 15 minutes.

<!-- moved from CLAUDE.md lines 1195 to 1255 (28 Oct 2026 version), word for word -->
- Game skins, footage behind text, rebuilt cards (advisor, 20 Oct 2026). The
  picture comes from the game, and it moves: a single-game story wears the
  game's look; the house theme is for news across several games or the
  industry.
  1. Text cut by the crop: `reel.shotsheet` reads every sheet frame with
     tesseract (`reel.edge_text`) and flags any printed text, logo or subtitle
     whose box crosses the 9:16 window's edge (`cut-text`, outlined in red on
     the sheet). Text that does not matter: drop the shot for a nearby one
     (Scramble Knights v2, 20 Oct: the outfit screen's button bar and the
     "Strength +1" pop-ups). Text that is the point (the Edgerunners 2 Oshima
     card): rebuild it as a vertical card in the game's own style (colours,
     label shapes, rules, type spacing), labels in Arabic (الاسم · يؤديه),
     names in English, animated the way the game's or show's UI moves, run or
     cut against the matching trailer shot. Flagged frames are marked on the
     sheet before queuing.
  2. No flat backgrounds: card-led templates (numbers, quote, explainer,
     edition, list) sit on the game's own trailer footage, dimmed and slightly
     blurred, always moving, never the flat indigo. Nothing static in the
     first 3 s of any Reel. No footage at all: key art split into layers with
     parallax, or animated type through the web-motion setup. The house look
     stays on the end card, the chips and the tribute variant.
  3. Game skins: eight genre kits (sci-fi/cyberpunk, fantasy,
     military/realistic, horror (never gore), anime/stylised, retro pixel,
     sports/racing, cosy/Nintendo-bright), each with colour tokens, plate and
     frame shapes, a text entrance, a cut transition and a short sound sting,
     built as web-motion (HTML) themes. Franchise skins on top of a kit for
     series covered often (Cyberpunk, Zelda, GTA, Pokemon, Final Fantasy, Call
     of Duty); a franchise earns one after three or four stories. Pick: one
     game is the story, its franchise skin, else its genre kit; multi-game
     lists, releases of the week, awards, industry, business, hardware,
     platform policy and our own series take the house theme, with footage or
     motion behind it.
  4. Never changes on any skin: Arabic type stays Dubai; the mark, the chip
     position, the safe zone (x 96 to 910, y 285 to 1480) and the end card on
     the jingle stay fixed, so the grid reads as one channel; عاجل stays
     crimson; inspired by the game's look, never a pixel copy of its UI or
     logo, and official logos only from press kits, to identify the game.
  5. Pilot first: three are built (sci-fi kit, fantasy kit, and the house
     theme with footage behind) and used on the next stories that fit. The
     format ledger logs each Reel's skin (`formats.py add <name> <fmt>
     [skin]`, `formats.SKINS`). After two weeks, views are compared with the
     two weeks before; the other six kits wait for that result. Nothing in the
     live pipeline changes for stories outside the pilot until then (the
     crop-edge text flag in 1 is a sheet check, applied to every Reel). The
     container has no Dubai font since the reset, so the HTML themes render on
     the runner or once `dubai.zip` is back.
  6. Built 20 Oct (commits 6fba31e, 4ae1e37): `templates/skins.py` with the
     kit tokens in `templates/web/skins/{scifi,fantasy,house}.css`;
     `reel(..., skin='scifi'|'fantasy')` or `"skin"` in a job file (house or
     no key is today's look; any other kit name stops the render). A kit
     changes the top-band decoration, a plate behind chip and headline, the
     split strip's plate, the story lines' outline, the shot-to-shot cut
     (sci-fi digital break-up; fantasy dissolve with a warm light leak), the
     line entrance (sci-fi fast slide; fantasy slow rise) and a sting at the
     first line (synth blip; harp-like pluck). The headline stays still (the
     first frame is the grid tile). With no skin the layers match the old code
     pixel for pixel. Card scripts still have to call `skins.plate(im, box,
     kit)` themselves. The house theme with footage behind is numgfx's
     `footage` ground (`ground_footage` in a job). Side-by-sides went to
     Mohammad at 19:16Z with a note that the sci-fi break-up looks heavy; no
     live Reel uses a kit until his verdict.

<!-- moved from CLAUDE.md lines 1542 to 1556 (28 Oct 2026 version), word for word -->
  Stills move smoothly (advisor, 18 Oct 2026; Mohammad: "some of the stills
  feel shaky"): zoompan and crop place a picture in whole pixels, so a 3% push
  or a slow pan at 1080x1920 stood still for about 11 frames and then jumped
  2 px (pans alternated 6 and 4 px steps). `stills_clips` now scales each image
  to 4x the frame (4320x7680), runs zoompan there and scales down to 1080x1920
  with lanczos; still pans inside `montage` pan at 4x and scale down last
  (`reel.SUB`). The picture finish (cas, grade, moving grain) runs after the
  downscale, so the grain is not magnified; stills_clips gained the finish it
  had been missing. Clip names carry `STILLS_VER` (s4), so clips from before
  the fix are re-rendered, never reused. Checked on the Pokopia Reel (v1 old,
  v2 new): per-frame motion on the push-in went from 7 jumps of about 2 px to
  an even 0.04 px a frame, and the pan from 6/4 px alternation to an even
  5.05 px. Cost: about 40 s of render per 3 s still on this CPU (a seven-image
  stills Reel took 6.5 minutes against about 2.5; the stills step is not in
  render-times.json, which starts at reel()).

<!-- moved from CLAUDE.md lines 1596 to 1601 (28 Oct 2026 version), word for word -->
  AI upscaling tested, not adopted (12 Oct 2026): `templates/upscale.py`
  runs Real-ESRGAN x2 on the cropped window (weights in `/root/models`, not
  in git). On the Street Fighter trailer it cleaned compression grain but
  added little real detail, and on this CPU-only container it takes about
  30 seconds a frame, hours for one Reel. Better sources come first; it may
  still help a still (one frame) when no larger image exists.

<!-- moved from CLAUDE.md lines 1676 to 1677 (28 Oct 2026 version), word for word -->
- Housekeeping: reel.py and outro.py delete their temp folders after a
  render (81 leftover folders filled the disk on 2 Oct).

<!-- moved from CLAUDE.md lines 1922 to 1963 (28 Oct 2026 version), word for word -->
  The den (Mohammad, 11 Oct 2026, from his references, which were AI
  renders and a collector's photo and so could not be used themselves):
  the default TV scene is now a real 70s den (Unsplash J_30KpjyTgk:
  wallpaper, a lamp, a wood-cased Philips on a stand), full bleed, with the
  footage mapped onto the tube in perspective (`ROOMS`, ffmpeg
  `perspective`) and scrims of the console's ground over the title band
  and the sheet; no wave lines or box patterns on it. `scene='cabinet'`
  keeps the cut-out TV. He may still replace the room if it does not
  click. No licensed poster art in any room. The Game Boy desk stays the
  cassette flat lay until he picks the route (a licence-clear cartridges
  photo from the scout, or Firefly-made surroundings around the real
  device, his call); `DESKS['carts']` is a prepared alternative.
  The den built in code (Mohammad, 11 Oct 2026, from the "Lights on, one
  by one" prompt pack he sent): `scene='room3d'` is the second option, a
  three.js room in `templates/room3d/room.html` (deterministic
  `renderAt(t)`, seeded randomness, whole cycles per 8 s loop, fixed
  camera so the screen's corners stay put), rendered by `render.mjs` in
  headless Chromium to `templates/assets/retro/room3d-loop.mp4` and
  `room3d-quad.json`; retro.py loops it under the warped footage with
  lighter scrims (0.62 top, 0.84 bottom). Nothing in it is licensed from
  anyone: plain boxes on the shelves, our own geometric prints, no logos.
  Method and numbers: `notes/retro-room-3d.md`.
  The den path-traced (Mohammad, 11 Oct 2026: "how do we make it look
  photorealistic", then "Go"): `templates/room3d/den_cycles.py` builds the
  same kind of room in Blender Cycles (the `bpy` module) from Poly Haven
  CC0 models and textures, with our own lamp, shelf and blind (moonlight
  stripes on the wall). `scene='room3d', room3d='cycles'` uses it. Brand
  marks on a downloaded model are painted out of its texture before it is
  used (the set's VTECH plate). First version is a held still, sent as a
  test; flicker comes after his verdict. Which room a story uses is his
  call per post.
  Rooms per era, later (Mohammad, 12 Oct 2026, after the path-traced test:
  "Nice. Not for now since we want to go back to news"): several rooms,
  each matching its console's era, colourful and fun. The 70s den suits
  Atari only (the 70s looked like that, less playful). For the 80s and
  90s machines the vibe is his two references (a kid's bedroom: shag rug,
  bean bag, posters wall to wall, VHS and cartridge shelves, a desk lamp,
  a lava lamp, a starry ceiling, cereal and a controller on the bed or
  rug, warm light against the TV's glow). The references themselves carry
  licensed art (film posters, Nintendo, Nike), so the rooms recreate the
  mood with our own posters and props, no brands, as in `den_cycles.py`.
  News comes first; this waits until he brings it back. Everyday audition:

<!-- moved from CLAUDE.md lines 2050 to 2114 (28 Oct 2026 version), word for word -->
## Web-style motion graphics (pilot, advisor, 19 Oct 2026, agreed with Mohammad)

Modern web-style animation, written in HTML, CSS and JavaScript and rendered
frame by frame to video in headless Chromium (the room3d route: a
deterministic `renderAt(t)`, Remotion-style), in the Digital Lounge palette
and the Dubai font, laid over or between footage. Browsers also shape Arabic
and right-to-left text better than the image library.
1. A reusable library, each piece built once and cached like the end-card
   masters: the outro first (two or three variants that rotate), then the fact
   strip, number counters and charts, list tiles, chips, and the explainer
   rings and highlights.
2. Bespoke pieces for special stories. First candidate: an Ocarina "world"
   episode on the official map: the camera moves across it, each region
   lights up with its name, then it zooms into Hyrule Castle to show the new
   artwork with the town around it beside the original, where castle and town
   square were separate. Later: a box opening for edition stories, a mechanic
   shown step by step.
3. Pilot order: (a) the outro in the new style, side by side with the current
   one, for Mohammad's verdict; (b) one bespoke piece, the map, if a coming
   Ocarina episode fits it.
4. Rules: readable at phone size before it looks fancy; the safe zone and
   reading pace apply; renders run on the Mac once it is live (browser
   rendering is slow on the 2-core container). Nothing replaces the current
   pieces until he approves the side-by-side.
5. Built 19 Oct: `templates/web/outro.html` (three variants on `?v=`: `aurora`, `lines`, `kinetic`; theme accent,
   the jingle's note and chord times from `sonic.beats`) and `templates/web/render.mjs <page> <out.mp4> <secs>
   [query]` (headless Chromium, one screenshot per frame, /fonts/ served from the private Dubai folder,
   Playwright from room3d's node_modules through a `node_modules` link). About 15 to 50 s a card on the
   container. The side-by-side with the current card went to Mohammad on 19 Oct
   (`live/2026-10-19/web-outro/`); his verdict is pending.

## HyperFrames pilot, isolated from the live pipeline (advisor, 23 Oct 2026, agreed with Mohammad)

HyperFrames (heygen-com/hyperframes, Apache 2.0) is an HTML-to-video framework:
compositions in HTML with GSAP, CSS or Lottie, rendered frame by frame in headless
Chrome and encoded with FFmpeg, with about 450 ready blocks (transitions, titles,
kinetic type, captions, counters, charts, maps). It fits the web-motion route above.
Pilot only.
0. Nothing live is touched: no changes to reel.py, render_job.py, render.yml, the job
   file format, the publish flow or Publer scheduling. All pilot work sits in
   `templates/hyperframes/` on the branch `pilot/hyperframes`, merged to main only
   after Mohammad approves. Renders run on the container, or on the runner through a
   separate workflow (workflow_dispatch only, its own concurrency group, one job at a
   time), never triggered by jobs/render/*.json and never ahead of a news render.
   Pilot work only in idle time; a news story in the queue always comes first.
   Nothing from the pilot is posted or scheduled.
1. Setup: the HyperFrames skills (compose, CLI, registry) for the session; not its
   media skill for AI voiceover, avatars or stock music (footage official, voice
   Mohammad's, music under our sound rules). Frame 1080x1920; the Dubai font from the
   private font folder as in the web-motion setup, never committed; our palette,
   chips and safe zone (x 96 to 910, y 285 to 1480).
2. Two pieces: a. a numbers card that counts up (GTA 6 pre-orders or Famitsu figures)
   on the game's own footage, dimmed and moving, with the game's logo plate; b. a
   rebuilt character card in the sci-fi skin, Oshima style: labels in Arabic (الاسم ·
   يؤديه), names in English, animated the way the show's UI moves, ending on the
   matching trailer shot. Arabic right-to-left rendering and line breaks checked
   carefully.
3. Each rendered next to our current version of the same piece; both side by sides go
   to Mohammad and the advisor with render time (container and/or runner) and any
   problems (Arabic shaping, fonts, file size); the result goes in
   `notes/hyperframes-pilot.md`.
4. Mohammad decides. If approved, a separate memo covers HyperFrames blocks for cards,
   transitions and skins in live Reels; if not, the branch stays unmerged and nothing
   changes. Pass 2 was approved on 24 Oct 2026: see "HyperFrames inserts in live Reels".


<!-- moved from CLAUDE.md lines 2152 to 2199 (28 Oct 2026 version), word for word -->
## Digital Lounge motion kit: pilot (advisor, 24 Oct 2026, agreed with Mohammad)

Goal: a small set of animated elements that move the same way in every Reel, so
the channel is recognisable and the news is easier to read. Mohammad: not
annoying; motion is there to help reading and give identity. Built in
HyperFrames, isolated like the earlier pilot.
1. The test every piece passes: it helps the viewer read or notice the key fact
   (the number, the person, the chip, the record), or it is cut as decoration.
   Each animation under 0.5 s; nothing moves while text is being read, and the
   text is fully readable the moment it settles. One or two kit moments per Reel
   at most, on the element that matters, never on every line. No flashing, no
   shaking, no constant looping motion.
2. The kit, our own design inspired by game UI, not copied from any console or
   game: a. photo box: a quick wipe shaped like our play triangle opens it, a thin
   frame draws around it, the name plate slides in beneath (role label per the
   people rule); b. number: counts up with a soft tick and settles with a small
   scale pop (under 5%); c. bar: fills like an XP bar with one short glint at the
   end; d. chip: presses in like a controller button with one small bounce;
   e. record or milestone: a short "unlocked" style banner slides in from the top
   for about 1.5 s, then out, only for real records and milestones; f. card
   transition: a quick wipe through the play triangle; g. sound: tiny UI blips
   built from our four-note motif, mixed well under the trailer or bed, never
   over speech.
3. Consistency: the same movements on every Reel; game skins change only the
   colours and plate shapes (sci-fi neon, fantasy gold, house indigo), never the
   motion. Safe zone, Dubai font, Arabic-first lines, chip position and end card
   unchanged. The breaking profile uses only the chip press and the number
   count, or nothing, so speed comes first.
4. Pilot: isolated on the branch `pilot/motion-kit`, idle time only, nothing
   posted, no change to reel.py or the live render path. Each element is built as
   a reusable HyperFrames block; one sample Reel uses two of them (for example
   the photo box and the number count) and is rendered again without the kit;
   the side by side goes to Mohammad and the advisor with render times and a
   short note per element on the reading problem it solves; results in
   `notes/motion-kit.md`.
5. After the pilot Mohammad approves or drops each element on its own. Approved
   elements join the HyperFrames inserts under the 24 Oct limited-use memo, with
   the same fallback and director QA, and the director QA adds one check: "does
   this motion help reading?" Any kit moment that does not is removed.
6. Approved (Mohammad, 24 Oct 2026, inbox, "Approve all"): all seven elements
   (a to g), with the photo box opening on frame 0 instead of the play-triangle
   wipe when it is on the cover, so the grid tile never shows a small triangle.
   They join the HyperFrames inserts under the limited-use memo (fallback to the
   numgfx card, 5-minute limit, director QA with the reading check). Built from
   `pilot/motion-kit` into `templates/hyperframes/` as insert pieces in idle
   time; the first three live Reels with a kit moment go to Mohammad as
   previews before scheduling, as with the first inserts.


<!-- moved from CLAUDE.md lines 2240 to 2291 (28 Oct 2026 version), word for word -->
## Media toolbox, step 1 (advisor, 25 Oct 2026, approved by Mohammad in the inbox 01:08Z)

Mohammad, 24 Oct 21:52 and 21:55 Dubai: the ARMS v5 Reel still looked bad, so it is dropped, and he
wants proper graphics and audio tools in one place. He approved the media toolbox plan (project doc
`claude/media-toolbox.md`) on 25 Oct 05:07 Dubai; this is its first step.
A. ARMS is dropped: no third ARMS post. Mohammad deletes v5 himself after test 1 (Instagram in the app,
   X and Threads through Publer); production deletes nothing. No ARMS item was left in the queue
   (Publer checked 03:18Z, 25 Oct).
B. Toolbox rules:
   - Every tool is an automatic step inside render.yml or a connector production already has; no
     manual steps for Mohammad.
   - Free first; a paid tool only when the free one fails the side-by-side test.
   - The commercial-use licence is checked and recorded before live use, for the code and the model
     weights separately.
   - Every tool has a fallback: if it fails or looks worse, the Reel builds as today.
   - Nothing goes live without side-by-side samples approved by Mohammad.
   - Render time stays inside the 45-minute fresh-reveal target; expensive work runs on sampled
     frames or once per asset and is cached, not on every output frame.
C. Test 1, on the ARMS footage (Nintendo's 720p copy), the hoop swing (12.2 to 12.9 s) and one calm
   shot: 1. the video tool's deblocking filter alone; 2. Real-ESRGAN to 1080p (the exact weight file's
   licence confirmed; time per Reel on the 4-core runner); 3. deblock plus Real-ESRGAN; 4. the
   OpenVisualCloud Video Super-Resolution Library (BSD-3, CPU RAISR), timed; 5. a framed layout: the
   trailer at its own width in a box, enlarged no more than 1.5x, over a dimmed, blurred, moving copy
   of the same footage, with our headline and chip. One card: published v4, then the five versions
   side by side, with render times and a recommendation for the standard weak-source fallback. Test
   only; nothing posts.
D. Answered in the same card: whether any enhancer or upscaler is already in the render and why it
   did not help ARMS; whether production can call the Adobe connector tools (generative expand,
   background removal, Enhance Speech) from its session automatically; Real-ESRGAN and RAISR time per
   Reel; where production looks for trailer footage, whether it uses yt-dlp to take the best official
   copy (the publisher's YouTube channel included), and whether a 1080p or 4K official ARMS trailer
   was on Nintendo's YouTube channel. Better sources come before any enhancement.
E. Next tests, each its own card, in this order (free, commercial-use licences): 1. ffmpeg
   blockdetect, blurdetect, freezedetect, blackdetect, silencedetect and astats on the final mp4 (stills
   and fades from the manifest exempt), plus two-pass loudnorm with a true-peak check (ffmpeg-normalize,
   MIT); 2. best source first: the yt-dlp Python package (Unlicense) picking the best official format,
   official press-kit or direct URLs as the alternative, no interactive logins; 3. PaddleOCR
   (Apache-2.0) with PP-OCRv5_mobile_det and arabic_PP-OCRv5_mobile_rec only, to find burnt-in text
   before cropping and to read our Arabic back from decoded output frames; 4. PySceneDetect (BSD-3)
   for shot boundaries (adaptive, minimum shot length); 5. HyperFrames' own checks (`npx hyperframes
   check --json --strict --at-transitions --frame-check --no-browser-gpu`, `npx hyperframes beats --json`
   on the local music only; browserSkipped:true counts as a failed check). Later, only after these:
   Adobe generative expand and background removal; BiRefNet Lite (the official MIT checkpoint only,
   never rembg's default model); faster-whisper small INT8 for subtitling voiced lines; OpenCV Zoo
   NanoDet (Apache-2.0) and YuNet (MIT) for reframing; DBS-BSRNN-DnR (Apache-2.0) only if Cocktail
   Fork disappoints; Topaz only if the free upscalers fail, with a cost estimate first. Skipped:
   auto-vertical-reframe and FrameShift (licences unverified, YOLO weights), Video2X (needs a GPU),
   stock Demucs (unclear weight licence, wrong stems).
   Note on E2: the 28 Sep rule stands until Mohammad says otherwise: YouTube asks for a sign-in and
   yt-dlp was refused then; any yt-dlp test uses no login and no third-party downloader, and its result
   goes to him on the card.


