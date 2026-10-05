# Delegation: who does what (Mohammad, 5 Oct 2026)

To save tokens, the main session is the editor: it decides, writes the Arabic,
judges the frames and talks to Mohammad. Repeated production work goes to a
cheaper subagent (Agent tool with `model`), which works only from the task card
below and the files it names, and reports back in a few lines.

Mohammad talks only to the main session. Helpers never message him and never
decide anything he has not approved. Once he has said "go" for a set of posts
and their times, the main session may hand the publishing steps to a helper
(Publish card below) and move on; helpers run in parallel where the work
allows. Nothing is queued without his "go".

## Kept by the main session
- Choosing stories, verifying against primaries, lanes, chips, times.
- Writing the Arabic (both skills, glossary, references) and reading the review.
- Looking at shot sheets, draft strips and final strips, and deciding fixes.
- Everything said to Mohammad, and deciding what is ready to publish.

## Task cards

**Digest digest (sonnet).** Read every unread digest in
dxbknight-digest@agentmail.to, oldest first. Return one line per item: age
label, headline, primary URL, status, and whether the ledger has it
(`python3 newsroom/ledger.py find "<keyword>"`). Do not mark anything read.

**Footage (sonnet).** For a named game: list its Steam trailers
(`templates/trailer.py`), Nintendo store `publicId`s under its own nsuid, or
IGN MP4s; fetch the asked-for ones to uploads; make `seekmap.py` sheets.
Return file names, sizes, durations and sheet paths. No YouTube downloaders.

**Render (sonnet).** Given a batch folder with `copyNN.py` and `renderNN.py`:
`check`, then `sheet`, then `draft`, then `strip`, and stop there with the
paths. After the main session clears the draft: `final`, `strip`,
`outro.snap_cut` per Reel, 2-pass phone copies over 30 MB
(`vb = 27*8192/dur - 192`, `-passlogfile` before the output), two renders at a
time at most. Return paths and any error verbatim.

**Drafts (haiku).** Run `jobsNN.py`, then
`preflight.py --no-approval` on each new draft folder, and `ledgerNN.py`.
Return the preflight lines.

**Grammar review (sonnet).** The `arabic-grammar-review` stage on a given
text file, report only, no edits.

**Publish (haiku), only after his "go".** Given the exact draft folders, times and
his approval note: `preflight.py approve` each, `git mv` to queue, `DRY_RUN=1
publish.py` and confirm it lists exactly those folders (stop and report if not),
push to dxb-queue main, wait for the receipts commit, read the captions back with
`postsListTool`, `ledger.py sync`, push dxb-assets. Return the post ids and states.

**Publish check (haiku).** `postsListTool` for the given window: report each
post's state and error. Then `newsroom/ledger.py sync`, commit and push
dxb-assets. Return one line per post.

**Housekeeping (haiku).** Commit and push leftover changes in dxb-assets
(ledgers, story files, cards); never touch dxb-queue.
