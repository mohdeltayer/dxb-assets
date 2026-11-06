# READ FIRST (Production 2 and every fresh session)

Raw file, no clone: `https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/<path>`

## 1. Read before any build
- `newsroom/reel-check.md`, `newsroom/editorial-memory.md` (your story type), `newsroom/names-ar.md`
- `STYLE.md` (rules in force, one page) and `arabic/house-glossary.md`
- `CLAUDE.md`, these headings: "Full-screen format for everything" (inside "Two accounts"), "Full frame, never a box in a
  blurred fill", "Verification without delay", "Verify against primary sources", "Story brief and editorial memory",
  "Desk board", "Publishing through Publer", "Trailer audio split, live", "Music-only trailer sound, opt-in"
- `newsroom/delegation.md`: "Task cards" (Director, Footage, Render lanes, Publer post, Pre-publish gate),
  "Promises first", "Full-frame check", "Hourly watch and the breaking lane"
- dxb-queue branch `desk`, `desk/board.md` (first and last thing every run)
- Cards (from the cards-in-git cutover, see the board): dxb-queue branch `main`, `cards/index.json` at the start of every
  run and `cards/<id>.json` when acting on one; write status with `python3 ops/cards.py set <id> progress="..."` (dxb-queue)

## 2. Files without a full clone
```
git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git
cd dxb-assets && git sparse-checkout set templates jobs newsroom ops arabic
```
Add `notes` or `.claude` only when needed. One old file: `git show <rev>:<path>`.

## 3. Exemplar job files (accepted by Mohammad, last two weeks): `ops/exemplars/`
- `fortnite-treasure-hunters-one-piece-november-1.json` (trailer): the rebuild after his hold. The game's own official
  trailer in one stretch in source order, full frame at the 2x cap between solid bands, headline in the band and never
  over a face, credit on every shot, and our bed with the reason written down (narration under every line).
- `suda51-travis-touchdown-will-return-famitsu.json` (interview, people): the news tidbit as a short attributed quote,
  role words and names per the list, a licensed photo box with its credit in the first 3.4 s, and known background
  kept to one line.
- `oot-road-ep7-princess-and-the-desert-man.json` (series episode, «الطريق إلى Ocarina»): the series intro, one
  spoken story cut into beats, each page shown alone before its line, scene music named in the note, and every
  waiver explained after a look at the frames.

## 4. A build, step by step (each step is checked: render_job refuses a job that skipped one)
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
5. Director check on the strip, dense and sheet (Director card, delegation.md), then
   `python3 templates/presubmit.py director <story> PASS <out.mp4> --job <your copy of the job>` (the gate runs again
   on the job; its "out" must be this file).
6. Per platform: `presubmit.py intent <commitment> <platform> <story> <out.mp4>` (refuses without a director PASS
   with a passed checklist for this exact file, and refuses a second submit), then `submit_publer_posts`, then `presubmit.py result ...
   scheduled|failed`. A failed or timed-out submit: look the post up in Publer before anything else.
7. Records: the `newsroom/commitments.json` row, `python3 templates/formats.py add`; after publishing,
   `presubmit.py published <commitment> <story> --links <ig> <x> <threads> --queue <dxb-queue clone>` (story file,
   newsroom/published.jsonl, heartbeat), then push both repos.
8. Board: one handoff on `desk/board.md` and `desk/board.json`: "built and scheduled: <story>, <slot>".
   Keep at least 3 finished undated Reels in `newsroom/evergreen.md` (Status "ready"); the keeper flags fewer.

## 5. Never
- Clone dxb-assets in full (33 GB), or run `git log --stat`, `-p` or blame (each pulls media blobs).
- Post without the ledger and Publer check, or past a hold, a deadline answer, or the gate.
- Add our effects over footage, or put trailer sound from another moment under a shot.
- Use stills for a trailer, reveal, update or gameplay story when official footage exists.
- Use a blurred fill, put a headline over a face, or print tokens or IDs in any file, card or log.
