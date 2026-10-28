# Build desk backlog

The build desk's working list (BUILD.md section 2). One entry per item: its card, where it stands, what is
left, how it is tested, and what it waits on. Moved here on 28 Oct 2026 (Mohammad, step 2 of
adv-20261028-three-desks): "Move the open build items ... to the build queue; today's background helpers may
finish what they started." The generated `desk/build-queue.md` (dxb-queue, branch desk) lists the cards; this
file lists the work inside them.

States: WAITS (on Mohammad or a root step), READY (can start tonight), IN PROGRESS (branch named), PARKED.

## B1. Pre-render checks: go live
- Card: adv-20261027-build-until-thursday item 1; readiness card prod-20261027-prerender-readiness (open:
  "Go live", "Go live, warnings only" or "Not yet").
- Built and on main (live path unchanged): `templates/prerender.py`, `cleanmap.py`, `prerender_ci.py`,
  `.github/workflows/prerender.yml`; `clean_map`, `clean_nudge` and `prerender_ok` job keys.
- Left: on "Go live", run prerender automatically before a routine render job is committed (blocking), or
  as notes only ("warnings only"); record retries per Reel and first-commit-to-receipt time for the Tuesday
  audit (before: 1.25 renders per Reel, median 10.3 min, `newsroom/render_retries.py`).
- State: WAITS on Mohammad's answer.

## B2. T0 breaking path, and a distinctive عاجل look
- Card: adv-20261027-build-until-thursday item 2; side by side prod-20261027-t0-side-by-side (answered
  with a note, no choice: "عاجل should attract attention a bit differently to make it distinctive").
- Built and on main: `templates/breaking.py` (`"kind": "breaking"`), `reel.PROFILES['breaking']`,
  `"profile"` passed by render_job.py, `.github/workflows/render-breaking.yml` (server first, GitHub when busy).
- Left: design a more distinctive عاجل look within the brand (crimson stays; no pink): for example a
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
- Not named in the move, still open: the YOLO swap (prod-20261025-yolo-licence, "Swap, side-by-side first"),
  the TGA co-stream live package (due 31 Oct), media toolbox tests E1 to E5. They move here if Mohammad says so.
