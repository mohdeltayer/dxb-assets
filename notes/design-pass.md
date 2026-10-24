# Design pass: three samples (24 Oct 2026)

Advisor memo "Design pass after the beat sheets" (24 Oct 2026, approved by Mohammad 09:15Z). Pilot only, on the
branch `pilot/design-pass`, never merged without his approval. Nothing live changed: main's reel.py,
render_job.py, render.yml, Publer and the queue are untouched, and nothing from here is posted or scheduled.

## What was built

On the pilot branch only:
- `templates/reel.py`: `CHIP_SIZE` 50 (was 38: the chip 75 px high, was 57; same top and right edge, the headline
  moves down 18 px); `STRIP_VALUE_SIZES` (64, 56, 48, 44) (was 56, 48, 44); `STRIP_H` 172 (was 160); strip columns
  sized to their own label and value, the room left shared equally (were equal thirds); `DP_CHIP_DIR` draws the chip
  row on its own layer (same pixels) so the kit can press it. `templates/ig_ar.py`: `_head(..., chip_size=38)`,
  unchanged for everything that does not pass it.
- `templates/design-pass/compose.py`: rebuilds a published Reel from its own job file (recovered from git), then
  lays the kit moments over the Reel's own frames as HyperFrames compositions with hard cuts, adds the blips, makes
  the side by side with the published Reel and the QA frames. `templates/design-pass/kit/` is a copy of the approved
  kit (`pilot/motion-kit` 703826b: kit.js, kit.css, blips.py).
- The WHERE AND HOW MUCH frame (`frame_piece`): platform logos on equal plates in a row (two rows past four), the
  price under each logo in Dubai Bold 74 with a small region label, the Central Bank dirham symbol left of the digits
  (`assets/dirham-symbol-mask.png`, digit height), other currencies as written («225 ريالًا», «19.99 دولارًا»), one
  price for all once and centred (`price_all`), unknowns as text («لم يُعلن السعر بعد», «الموعد لاحقًا»), the date
  on one line beneath, an optional note line, the «بالعربية» badge in bright indigo. Each plate presses in like the
  chip (in at 112%, under to 94%, settled at 0.3 s), 0.3 s apart; the date and note rise in; then everything holds
  still until the last 0.3 s, which clear it back to the footage. The footage keeps moving behind under a 62% indigo
  dim. The piece stops when it would hold still for under 2 s. Unsourced logos (Xbox One, Mac, App Store, Meta Quest)
  are text plates in Dubai Bold.
- `.github/workflows/design-pass-pilot.yml`: pushes to this branch only (never jobs/render/*.json, never main), own
  concurrency group, waits while any render.yml run is queued or running, the Dubai font cloned into a temp folder
  and deleted, never committed, uploaded or printed.

## The three samples (published left, design pass right)

| Sample | Story (published) | What changed | Kit moments |
|---|---|---|---|
| A. Product showcase, family 1 | PlayStation Pulse, no Gulf launch (22 Oct, split) | Chip 1.3x and its press; strip on the new layout; headline at the 100 px grid size | chip press |
| B. Release with the frame, family 7 | Phantom Blade Zero, launch date and Gulf prices (22 Oct, split) | The strip and the first line (date and platforms) replaced by the frame, 5.9 to 9.9 s: PS5 «الإمارات» 239 with the dirham sign; Steam «الإمارات» 219 and «السعودية» 225 ريالًا; «تصل في 29 أكتوبر»; «وعلى Epic Games Store أيضًا»; held still 7.1 to 9.6 s (2.5 s). Chip 1.3x and its press | chip press, logo press |
| C. People story, family 4 | Eiji Aonuma, French arts and letters honour (24 Oct, trailer; published with the headline-only cover) | The kit's photo box open on frame 0 beside the headline (face, name, role, photo credit; no triangle wipe), stepping aside with the kit's exit as the headline leaves at 3.5 s; story lines after it as published. Chip 1.3x and its press | chip press, photo box |

Facts, platforms, prices, dates and line wording are the published ones. Two wording changes were forced by rules
that came after these Reels posted:
- Headlines at the 24 Oct grid size (100 px, never under 72, two lines). PS Pulse's «سماعة PlayStation Pulse تصل
  في نوفمبر / لكن ليس إلى الخليج بعد» does not fit at 72; it became «سماعة PlayStation Pulse / لا موعد لها في الخليج
  بعد» (the caption's own «لا موعد لها في الخليج بعد»; the date stays in the strip). Phantom Blade Zero's «أسبوع على
  Phantom Blade Zero / وهذا سعرها في الإمارات والسعودية» and the shorter «... وهذا سعرها في الخليج» do not fit; it
  became «موعد Phantom Blade Zero / وسعرها في الخليج» (the frame carries both). Aonuma's fits as published.
- The 24 Oct glued-prefix rule: PS Pulse's line «وBluetooth» became «و Bluetooth» (the rule's own fix).
New on-screen Arabic: «تصل في 29 أكتوبر» (from the published line), «وعلى Epic Games Store أيضًا» (Epic was in the
published line; its price is not in the story file, so it has no plate of its own rather than an invented price or
a false «لم يُعلن»), region labels «الإمارات» and «السعودية» (from the published strip). Every line opens on an
Arabic word.

## Per element: what changed and the reading problem it solves

| Element | Change | Reading problem |
|---|---|---|
| WHERE AND HOW MUCH frame | Logos on equal plates, price under each, date beneath, held still 2.5 s | The strip packed platform, country and price into one short label per column («الإمارات · Steam»); a viewer had to read three labels to learn where the game is. Logos are recognised at a glance, the price sits under the logo it belongs to, and the dirham sign reads as UAE without a word |
| Logo press | Each plate presses in, 0.3 s apart | The eye goes plate to plate in reading order (right to left) instead of meeting the whole table at once; motion ends 1.2 s in, before the price is read |
| Chips 1.3x | 75 px chip, Dubai Bold 50 | At grid size the 57 px chip (جديد، رسمي، تقرير) was a small coloured dot; it is now legible on the 3:4 tile (QA crops at 300 x 400) |
| Chip press | Rests on frame 0, presses once at 0.25 s (94%, a small bounce, settled at 0.55 s) | Frame 0 keeps the chip for the grid tile; the press passes the eye over the certainty word before the headline |
| Photo box on frame 0 | Open on the cover, no wipe; the kit's exit as the headline leaves | The grid tile shows face, name and headline together (Mohammad, 24 Oct); a viewer knows who the story is about before it starts |
| Strip values | Columns sized to their content; sizes up to 64 | Equal thirds held long values a size down; see "What did not work" |
| Blips | Press, logo press, photo box exit, 14 dB under the Reel's peak, skipped inside a job's speech windows | Sound-on viewers hear the fact land; Phantom Blade Zero's blips (6.17, 6.47 s) fall in the pause between its two voiced sentences |

## Render time (runner, 4 cores, HyperFrames 0.8.143)

| Sample | Fetch | Reel (reel.py) | Kit moments (HyperFrames) | Compose total | Whole sample |
|---|---|---|---|---|---|
| A. PS Pulse | 16 s | 157 s | cover 3.6 s: 23.7 s | 48 s | 244 s |
| B. Phantom Blade Zero | 28 s | 158 s | cover 3.6 s: 24.9 s; frame 4.0 s: 24.4 s | 134 s | 357 s |
| C. Aonuma | 10 s | 163 s | cover 3.7 s: 21.9 s | 66 s | 276 s |
| Frame layout demo | | | two 4.6 s pieces: 9.6 s and 9.2 s | | |

The whole job, setup included, took 16 min 24 s (run 40114391729). Each kit moment adds about 25 s of HyperFrames
render plus 20 to 40 s of overlay and audio passes; the frame adds about a minute and a half to a Reel in all.

## Outputs (this branch)

- `templates/design-pass/out/design-pass-all-sbs.mp4`: the three side by sides one after another, 63.6 s, 18.6 MB
  (the inbox card's video).
- `design-pass-ps-pulse-sbs.mp4` (3.0 MB), `design-pass-pbz-sbs.mp4` (9.2 MB), `design-pass-aonuma-sbs.mp4` (8.3 MB).
- `out/qa/`: per sample the first frame, the first frame cropped 3:4 at phone grid size, the top band, the chip
  press frame by frame, a 4 fps dense strip; the frame held (B); the photo box at 3 s and after it (C); two layout
  tests of the frame on the house ground (`frame-demo-*`, labelled «مثال للتخطيط، ليس خبرًا», not a story): five
  platforms in two rows with one price for all, the «بالعربية» badge and «الموعد لاحقًا»; two plates with
  «لم يُعلن السعر بعد» and a text plate (Mac).

## QA (director checks on the frames)

- Arabic order and first words: right in every frame; the plates read PS5 then Steam right to left; «225 ريالًا»
  and «تصل في 29 أكتوبر» keep their numbers in place; Latin names held whole (`<bdi>`).
- Safe zone: the frame, chips, photo box and lines sit inside x 96 to 910, y 285 to 1480.
- Grid corner (x 940 to 1080, y 240 to 380 on frame 0): clear on all three; the chip's right edge is at x 910 and
  its 2% bounce stays under 915.
- Contrast: the frame's plates are 86% indigo on a 62% dim; the photo box keeps its dark plate; the headline band is
  unchanged.
- Nothing moves while text is read: the logo press ends 1.2 s into the frame and it then holds 2.5 s still; the chip
  settles by 0.55 s, before the headline is read; the photo box does not move on the cover.
- No pink in our colours: theme accents only (spectacle amber, stylised periwinkle, cold azure), bright indigo badge.
- Decode clean on every output.

## What did not work, and open points

- Strip values on the PS Pulse sample did not get larger. The published strip was already at 56 px, the old top size;
  the next step, 64, needs about 860 px for «99.99 دولار · 19 نوفمبر · 29 أكتوبر» with the current padding and the
  strip is 814 px wide (the safe zone). Equal columns would have dropped it to 48; the new sized columns keep 56. To
  get 64 on three-item strips: narrower padding (20 px, tight against the rules), two items, or a shorter value
  («99.99$»). Two-item strips and shorter values should reach 64 with the sized columns (not rendered in these samples). The strip is 12 px taller and the chip larger, so the
  sample still shows those.
- Fix rounds used: two (round 1: the side by side title overflowed and the strip padding; round 2: the sized
  columns). A third render was not made, per the two-round limit.
- Combined video: the first combine came out at 20.3 MB and was re-cut to 18.6 MB.
- Lengths: Aonuma runs 21.3 s before the end card, as published (the target is a guide).
- Live roll-out would need: the frame as a `hfinsert` piece (job key, fallback to the strip, 5-minute limit), the
  chip layer and press in the live path (today it is composed after the render), and the breaking profile keeping
  only the chip press or nothing.
