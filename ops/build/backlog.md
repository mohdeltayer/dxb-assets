# Build desk backlog

The build desk's working list (BUILD.md section 2). One entry per item: its card, where it stands, what is
left, how it is tested, and what it waits on. Moved here on 28 Oct 2026 (Mohammad, step 2 of
adv-20261028-three-desks): "Move the open build items ... to the build queue; today's background helpers may
finish what they started." The generated `desk/build-queue.md` (dxb-queue, branch desk) lists the cards; this
file lists the work inside them.

States: WAITS (on Mohammad or a root step), READY (can start tonight), IN PROGRESS (branch named), PARKED.

## Order from 28 Oct night (adv-20261028-use-the-server, approved by Mohammad 13:09Z)
Work that puts load on dxb-render-1 comes first. Tonight's build night (from 01:00 Dubai):
1. B2, T0 on moving footage (first).
2. B1, pre-render checks switched on at the 04:00 release for every job, "Go live" (server first, GitHub only
   when the server is busy or down).
3. B5's dispatcher install (tonight, as soon as the backup files exist; if the root steps are not done,
   install under the runner user with its own read-token request card instead of waiting).
4. B7, prepared trailers, next after the dispatcher, ahead of monitoring (B5's rest) and analytics (B6).
5. Lane A fresh news (T1) onto dxb-render-1 with the 5-minute GitHub fallback: proposed in the 48-hour lane
   report (29 Oct 10:40Z) with the numbers, if it shows no server-caused failures; Mohammad decides there.
   T0 stays GitHub-first until the server has a priority rule (tonight's Indie World Reels render on GitHub).
6. Every release note carries one line: server minutes of work in the last 24 hours (renders, pre-render,
   prepared trailers, services) and the share of the day's Reels that touched the server.
Unchanged: B8 (Ocarina) keeps its date pressure (episode due 29 Oct 21:00 Dubai); B3, B4, B6, B9 to B11
after these; the test gate, the release window and BUILD.md apply.

## B1. Pre-render checks: go live
- Card: adv-20261027-build-until-thursday item 1; readiness card prod-20261027-prerender-readiness (open:
  "Go live", "Go live, warnings only" or "Not yet").
- Built and on main (live path unchanged): `templates/prerender.py`, `cleanmap.py`, `prerender_ci.py`,
  `.github/workflows/prerender.yml`; `clean_map`, `clean_nudge` and `prerender_ok` job keys.
- Answer: "Go live" (Mohammad, advisor chat 13:09Z, adv-20261028-use-the-server): live at the 04:00 release
  for every job, on dxb-render-1 first, GitHub when the server is busy or down.
- Left: run prerender automatically before a routine render job is committed (blocking), or
  as notes only ("warnings only"); record retries per Reel and first-commit-to-receipt time for the Tuesday
  audit (before: 1.25 renders per Reel, median 10.3 min, `newsroom/render_retries.py`).
- State: READY (go live at the 04:00 release, 29 Oct).

## B2. T0 breaking path, and a distinctive عاجل look
- Card: adv-20261027-build-until-thursday item 2; side by side prod-20261027-t0-side-by-side (answered
  with a note, no choice: "عاجل should attract attention a bit differently to make it distinctive").
- Built and on main: `templates/breaking.py` (`"kind": "breaking"`), `reel.PROFILES['breaking']`,
  `"profile"` passed by render_job.py, `.github/workflows/render-breaking.yml` (server first, GitHub when busy).
- First (adv-20261028-use-the-server): the T0 input is ONE official moving clip (a trailer stretch, an X
  video post, an eShop or Steam trailer), 6 to 12 s, with headline, one line, date and platforms, source and
  the breaking bed; a still only as a short full-bleed beat inside it (stills are not a Reel after the deleted
  logo Reel). Under 60 s render on a warm server. Morning side-by-side card on two of tonight's Indie World
  reveals (what was posted against the T0 version; production's posted Reels are in cards/2026-10/,
  T0 log in the Indie World report card).
- Then: design a more distinctive عاجل look within the brand (crimson stays; no pink): for example a
  pulsing crimson band, a stronger chip press, the breaking sting; one sample card to Mohammad with the
  current T0 look beside it on a real recent story, with timings. Go-live choice still open after that.
- Test: the gate in BUILD.md; T0 render under 60 s on a warm server, whole job under 2 min.
- State: READY.

## B3. Urgency tiers at triage
- Card: adv-20261027-build-until-thursday item 3. Not started.
- Spec: every story gets T0 (minutes), T1 (within the hour), T2 (same day, slot known) or T3 (evergreen),
  with a default by story kind; the tier picks lane and profile (T0 breaking path; T1 standard on the
  server; T2 and T3 quality profile on the server). T0 never waits for slot, cadence, gap rule or caps; the
  queue shifts around it. Drop-down rule: a T1 to T3 render that would miss its slot drops to the standard
  profile and, if needed, to GitHub. Tier shown on review cards and in the Published tab tags.
- Deliverable: kind-to-tier defaults (`formats.py` or a small `tiers.py`), a `"tier"` job key, the routing,
  and a readiness card with one day of tier assignments for Mohammad to sanity-check.
- State: READY.

## B4. Quality profile for T2 and T3
- Card: adv-20261027-build-until-thursday item 4. Not started.
- Spec: slower two-pass encode at the same file size; two-pass loudness levelling with a true-peak check;
  automatic checks on the finished MP4 (blockdetect, blurdetect, freezedetect, blackdetect, silencedetect,
  astats); a failed output check stops the upload and drops to the standard profile rather than missing
  the slot.
- Deliverable: `PROFILES['quality']`, the output-check step, a side-by-side card on three Reels (standard
  against quality) with timings and file sizes. Licences in the rights register before live use
  (ffmpeg-normalize MIT, media toolbox card E1).
- State: READY (after B3, or alongside if B3's routing is stubbed).

## B5. Back office 2: monitoring and the status clerk (with the dispatcher)
- Cards: adv-20261027-back-office service 2; adv-20261025-status-clerk; dispatcher from
  adv-20261028-three-desks part A (built: `ops/backoffice/dispatch/`, tests 76/76; readiness card
  prod-20261028-dispatcher-readiness).
- Left: uptime checks on the runner service, the stall check, Publer reachability and disk space, alerting
  to the existing ntfy topic; move the stall check and the status clerk onto the server as scheduled
  scripts (the clerk's progress lines come from Actions evidence, as the dispatcher already reads them);
  install the dispatcher once Mohammad's backup root steps are done (`prod-20261027-backup-root-steps`).
- Deliverable: one readiness card for the service before it goes live.
- State: WAITS for the dispatcher install (root steps); the monitoring part is READY.

## B6. Back office 3: analytics store
- Card: adv-20261027-back-office service 3. Not started.
- Spec: nightly pull from Publer (and Instagram insights where the key allows) into a small database on the
  server: per post, template, hook style, posting hour, platform; views, reach, retention, saves, shares,
  comments. Weekly summary card every Friday. Needs a read key: if Publer's media-only key cannot read
  analytics, ask Mohammad for the narrowest key in one card (no posting or deleting rights).
- State: READY to design; may WAIT on a key.

## B7. Back office 4: prepared trailers
- Card: adv-20261027-back-office service 4. Not started.
- Spec: for every trailer the watch flags, fetch the best official source (official channels only, no
  logins, no third-party downloaders), run the source checks, cut into shots (PySceneDetect), map faces
  (YuNet) and subjects (NanoDet or YOLOX, the approved swap away from YOLO), detect burnt-in text, split the
  audio once (Cocktail Fork), store keyed by trailer with cleanup after 7 days and a 40 GB disk floor. The
  render uses a prepared asset when one exists and falls back to today's path when not. Licences recorded
  before live use. Depends on back office 1 (the watch) being live.
- Order: NEXT after the dispatcher install (adv-20261028-use-the-server), ahead of B5 monitoring and B6.
  Readiness card with disk and CPU numbers and two examples.
- State: WAITS on the watch go-live (back office 1, finishing in the day session).

## B8. Road to Ocarina: story-beat template, Mohammad's five points
- Card: adv-20261027-road-to-ocarina (episodes stay with ops); preview card
  prod-20261028-ocarina-ep6-preview (answered 28 Oct 03:13Z with five points).
- Built: `templates/storybeat.py` (picture track of framed cards on a blurred ground), `ocarina_intro.py`.
- Left (template side): 1. join the agreed series intro and medley ahead of each episode; 2. a one-word beat
  always sits over a picture, never an empty ground; 3. no flash when words are added (the word-by-word
  reveal must not flicker or re-draw the line); 5. a storybook look: the text written on a page, the camera
  moving from one part of the page to the next while the scenes play. Point 4 (storyteller narration) is
  writing, so ops does it in the episode script.
- Deadline: episode 6 posts 29 Oct 21:00 Dubai (17:00Z). If the template is not released at 04:00 Dubai on
  29 Oct, see the note on the BUILD.md card for what happens to episode 6.
- Test: the gate, plus episode 6 re-rendered from the branch and its strip looked at against the five points.
- State: READY (needs the first build night).

## Not moved (stay where they are)
- Back office 1, the watch go-live (`prod-20261027-backoffice-watch-readiness`): started in the day session
  on 28 Oct 03:50Z; finishes there.
## B9. YOLO swap: Apache-2.0 detector for autofocus (moved 28 Oct, Mohammad's note on prod-20261028-build-md)
- Card: prod-20261025-yolo-licence, answer "Swap (side-by-side first)".
- Left: OpenCV Zoo detector (YOLOX or NanoDet, Apache-2.0) with YuNet (MIT) for faces, through the installed
  OpenCV; side-by-side crops on three recent Reels to Mohammad before it replaces YOLO; YOLO stays until then.
- State: READY.

## B10. The Game Awards co-stream live package (moved 28 Oct; due 31 Oct)
- Plan: notes/tga-costream-plan.md (OBS scenes in templates/live/: starting-soon with countdown, BRB,
  right-to-left lower-third ticker in Dubai, corner mark, end card; ticker fed from the hourly watch).
- Deadline: drafts to Mohammad by 31 Oct.
- State: READY.

## B11. Media toolbox tests E1 to E5 (moved 28 Oct)
- Card trail: advisor memo of 25 Oct (CLAUDE.md "Media toolbox, step 1"), test 1 card posted 26 Oct.
- Left, in order, one card each: E1 ffmpeg output checks plus two-pass loudnorm; E2 best official source
  (yt-dlp, no login, result to Mohammad under the 28 Sep rule); E3 PaddleOCR; E4 PySceneDetect; E5
  HyperFrames' own checks.
- State: READY.

## B12. True X live threads (logged 28 Oct, adv-20261028-indie-world-live-thread)
- Publer composes X thread replies only together with the root post, so a live thread on X (replies added as
  announcements land) needs X's own API. Tonight's Indie World runs on X as numbered posts quoting the root.
- Scope: X API reply-to-own-post for show nights, keys requested by card, no posting rights beyond replies.
- State: PARKED until after the order in "Order from 28 Oct night".
