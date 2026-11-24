# READ FIRST (Production 2 and every fresh session)

Raw file, no clone: `https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/<path>`

## 1. What a run reads (Mohammad, 24 Nov 2026: runs stopped "on context budget" with the board at 285 KB and CLAUDE.md at 315 KB)
Every Production 2 run reads these four, and only these, at the start:
- this file, `ops/READ-FIRST.md`
- `STYLE.md`
- `CLAUDE.md` (the slim rules in force, about 30 KB; the full dated history is `docs/history.md`: never read it whole,
  open one section by its heading only when a task needs it)
- dxb-queue branch `desk`, `desk/board.md` (trimmed every day at 04:00 Dubai to the last 24 hours, under 30 KB; first and
  last thing every run; older lines in `desk/archive/`, read only when a handoff points there)
Open anything else only at the step that needs it, and only the part it needs: the story type's entries in
`newsroom/editorial-memory.md` and its items in `newsroom/reel-check.md` when writing the brief; `arabic/house-glossary.md`
and `newsroom/names-ar.md` when writing Arabic; the Director card in `newsroom/delegation.md` when acting as Director; an
exemplar in `ops/exemplars/` when unsure of a template. Do not read whole digests, release notes, render logs or
render-times.json; use `grep` or the work order's summary.

## 2. Files without a full clone
```
git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git
cd dxb-assets && git sparse-checkout set templates jobs newsroom ops arabic
```
Add `notes` or `.claude` only when needed. One old file: `git show <rev>:<path>`.

## 3. Exemplar job files (accepted by Mohammad, last two weeks): `ops/exemplars/`
- `silver-palace-december-14.json` (split, the default layout): a 16:9 official gameplay trailer filling 9:16, cropped to
  the subject (enlargement under 2x), headline and lines on the soft band over the picture, the fact strip low, a credit
  on every shot, the trailer's own sound. Every 16:9 trailer or gameplay Reel looks like this.
- `fortnite-treasure-hunters-one-piece-november-1.json` (trailer): the WEAK-SOURCE EXCEPTION, not the default. The only
  official copy was 1280x720, so it cannot fill 9:16 inside the 2x cap: full frame at the cap between solid bands, the
  headline in the band, the sources tried named in `lowres_ok`. Credit on every shot, our bed with the reason written
  down (narration under every line). The band layout without a named weak source is refused after the headline
  (templates/fillcheck.py, adv-20261107-band-layout-drift); a band holding only a credit line is empty space.
- `suda51-travis-touchdown-will-return-famitsu.json` (interview, people): the news tidbit as a short attributed quote,
  role words and names per the list, a licensed photo box with its credit in the first 3.4 s, and known background
  kept to one line.
- `oot-road-ep7-princess-and-the-desert-man.json` (series episode, «الطريق إلى Ocarina»): the series intro, one
  spoken story cut into beats, each page shown alone before its line, scene music named in the note, and every
  waiver explained after a look at the frames.

## 4. A build, step by step (each step is checked: render_job refuses a job that skipped one)
First line of every run (adv-20261107-keeper-blind-and-lost-submit, 7 Nov 2026): the keeper's line and its coverage
line, `git fetch -q --depth 1 origin +keeper-status:refs/remotes/origin/keeper-status && git show
origin/keeper-status:keeper/status.txt | head -2`. When it reads `coverage: GAP`, the run ends with a scheduled submit
or a banked piece queued: no-build is not an allowed outcome. A run that ends empty writes `FAILED RUN` on the board
with each lead it rejected and why. Slots: the :30 session owns even-hour slots, the :35 session odd-hour slots; a
claimed slot that will not be delivered is released by a board line within 20 minutes (the keeper alarms on a claimed
slot with no post 20 minutes before it).
0. Digest, always fresh from GitHub, never from a file on disk:
   `git fetch -q --depth 1 origin +watch-digest:refs/remotes/origin/watch-digest && git show origin/watch-digest:watch/digest.json`
   (or https://raw.githubusercontent.com/mohdeltayer/dxb-assets/watch-digest/watch/digest.json); check `generated_at`.
1. Story file `newsroom/stories/<date>-<slug>.json` with `sources` (url), `first_report`, `source_type` (primary or
   secondary), `footage` (stills: why, and the footage sources tried), `lane`, `beat`; then
   `python3 newsroom/ledger.py find <words> --record <story id>` and the Publer list for the last 7 days.
   Read the backstory pages it touches: `python3 newsroom/context.py match <story id>` (newsroom/context/).
   What is new: `python3 newsroom/whatsnew.py packet <story id>` (primary text kept local, summary into the story file;
   needs `python3 -m pip install trafilatura==2.3.1 dateparser==1.5.0`). Write the angle from its "new" sentences.
2. Gate: primary read, chip on the ladder, `gate HH:MMZ` in the story file.
3. Job file with `"story"`, `"render_lane": "server"` (default), `"reel_check"` filled from reel-check.md and a
   `"decision_log"` (per beat: shot and alternatives, crop, music and why); a stills Reel also needs `"stills_reason":
   {"why": sales|business|people|delay|outage|no_footage, "tried": [sources]}`. Keep a local copy of the job.
   Every footage shot (anything that is not our "-gfx-" card) sits inside a "credits" range, «المصدر: ...».
   `python3 templates/buildgate.py <job>` then `python3 templates/render_job.py check <job>`.
4. Render on the server: the job in `jobs/live/<name>.json`, then workflow_dispatch `render-live.yml` with input `job`.
   GitHub's runner only with `"render_lane": "hosted"` and a `"lane_reason"`: the job in `jobs/render/` (render.yml,
   input `job`; a run with no job named is refused). Breaking: `render-breaking.yml` with `job` and `lane`.
   Done when `cards/YYYY-MM/<name>-reel-vN-publer.json` lands on main with the mp4, strip, sheet and dense.
5. Director check on the strip, dense and sheet (Director card, delegation.md). The verdict is a plain file, never a
   command (Mohammad, 23 and 24 Nov 2026: `presubmit.py director` was refused by the safety filter in the 23 Nov runs and
   again at 21:26Z, so finished Reels sat unscheduled): the Director agent writes `jobs/director/<job name>.json`
   (story, out, verdict pass or fix, reason and the one fix, reasons, job_patch for factual_error, unclear_text or
   graphic, at, by; format and example in jobs/director/README.md) and commits and pushes it. NEVER run
   `presubmit.py director`, `intent`, `result`, `line` or `published`: they are retired from Production 2's flow.
6. Scheduling goes through the server step (server-post.yml reads the director file on every keeper tick: pass
   schedules, fix renders once more, no file 20 minutes after the render schedules anyway). Until the server has its
   Publer posting key it writes the Reel "ready" and the work order shows it as alarm serverpost-ready with the slot. For
   each one: read Publer (scheduled, and published for 48 hours) and run `python3 templates/publercheck.py posts <file>
   --story <story id>` (exit 1: skip it, note it on the board); then submit_publer_posts on Instagram (Reel), X and
   Threads at that minute with the story file's texts and the labels in the alarm (story:<job name> included), then
   get_publer_job_status until complete, then `python3 templates/serverpost.py scheduled <story> --slot <ISO>` (a record
   of what was done, not an approval). Publer is the only record of what is scheduled and posted (23 Nov 2026).
   A failed or timed-out submit: read the job status, then look the post up in Publer twice 10 minutes apart before
   anything else; never submit again on one empty list. No Publer ids in any file.
6b. Quick posts (split by platform, 24 Nov 2026): X and Threads get an image card for every verified story, Instagram
   gets the Reel. For a T0 story dispatch `quick-post.yml` (input story = the story id) the moment the story file is
   committed, before the Reel. Each quickpost-ready alarm on the work order: Publer check as above, then
   submit_publer_posts on X and on Threads (post_type photo, media_url the card's raw dxb-assets URL, the slot and the
   labels in the alarm, texts quick_x or x on X and quick_threads or threads on Threads), job status, then `python3
   templates/quickpost.py scheduled <story> --slot <ISO>`. A serverpost-ready alarm lists each network's own time: the
   Reel's X and Threads post uses the story's reel_x and reel_threads. Write reel_x and reel_threads in every story or
   slip (a first line about what the video shows, different from the quick post), or the Reel goes to Instagram only.
7. Records: `python3 templates/formats.py add`; nothing else is needed after publishing (Publer is the record).
8. Board: one handoff on `desk/board.md` and `desk/board.json`: "scheduled: <story>, <slot Dubai>, job status complete
   HH:MMZ on <platforms>" (no id suffixes needed).
   Keep at least 6 finished undated Reels (ops/cadence.json buffer_target) as Publer drafts labelled kind:evergreen, listed in `newsroom/evergreen.md` (Status "ready"); fewer is a keeper alarm, and a
   run that builds no news builds a bank piece (the idle card's bank step is mandatory then).

## 5. Never
- Clone dxb-assets in full (33 GB), or run `git log --stat`, `-p` or blame (each pulls media blobs).
- Post without the ledger and Publer check, or past a hold, a deadline answer, or the gate.
- Add our effects over footage, or put trailer sound from another moment under a shot.
- Use stills for a trailer, reveal, update or gameplay story when official footage exists.
- Use a blurred fill, put a headline over a face, or print tokens or IDs in any file, card or log.
