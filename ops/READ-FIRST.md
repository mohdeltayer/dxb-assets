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

## 4. A build, step by step
1. Ledger `python3 newsroom/ledger.py find <game>`, then the Publer list for the last 7 days: no repeat without new facts.
2. Gate: primary read, chip on the ladder, `gate HH:MMZ` noted in the story file `newsroom/stories/<date>-<slug>.json`.
3. Job file `jobs/render/<name>.json`, with the angle lines and the filled `reel_check` first.
   Check it with `python3 templates/render_job.py check jobs/render/<name>.json` (or `templates/prerender.py`).
4. Render. News goes to lane A: push the job to main and `render.yml` runs it (manual run: workflow_dispatch with
   input `job`). Evergreen and series go to lane B: the job in `jobs/live/`, then workflow_dispatch `render-live.yml`
   with input `job` on dxb-render-1. Breaking goes to `render-breaking.yml` with inputs `job` (`jobs/breaking/...`)
   and `lane`. Done when `cards/YYYY-MM/<name>-reel-vN-publer.json` lands on main with the mp4, strip, sheet and dense.
5. Director check: the strip, dense and sheet against the job (Director card, delegation.md), one table per shot,
   PASS or FIX. A FIX means a re-render.
6. Publer: the media is already uploaded by the render; then one `submit_publer_posts` per account at the same
   minute: Instagram reel with caption and labels, X with the short text, Threads with its text, source follow-ups.
7. Records: the `newsroom/commitments.json` row, the story file ("scheduled in Publer HH:MMZ"), and the format ledger
   (`python3 templates/formats.py add`). After publishing: all three read Published, the Inbox `published` entry,
   and the preview card closed.
8. Board: one handoff on `desk/board.md` and `desk/board.json` in one commit to `desk`: "built and scheduled: <story>, <slot>".

## 5. Never
- Clone dxb-assets in full (33 GB), or run `git log --stat`, `-p` or blame (each pulls media blobs).
- Post without the ledger and Publer check, or past a hold, a deadline answer, or the gate.
- Add our effects over footage, or put trailer sound from another moment under a shot.
- Use stills for a trailer, reveal, update or gameplay story when official footage exists.
- Use a blurred fill, put a headline over a face, or print tokens or IDs in any file, card or log.
