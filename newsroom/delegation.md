# Delegation: who does what (Mohammad, 5 Oct 2026)

To save tokens, the main session is the editor: it decides, writes the Arabic,
judges the frames and talks to Mohammad. Repeated production work goes to a
cheaper subagent (Agent tool with `model`), which works only from the task card
below and the files it names, and reports back in a few lines.

Helpers never queue, push to dxb-queue, approve, or message Mohammad. Posting
stays with the main session, after his "go", every time.

## Kept by the main session
- Choosing stories, verifying against primaries, lanes, chips, times.
- Writing the Arabic (both skills, glossary, references) and reading the review.
- Looking at shot sheets, draft strips and final strips, and deciding fixes.
- Approval, `git mv` to queue, dry run, push, and everything said to Mohammad.

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

**Publish check (haiku).** `postsListTool` for the given window: report each
post's state and error. Then `newsroom/ledger.py sync`, commit and push
dxb-assets. Return one line per post.

**Housekeeping (haiku).** Commit and push leftover changes in dxb-assets
(ledgers, story files, cards); never touch dxb-queue.
