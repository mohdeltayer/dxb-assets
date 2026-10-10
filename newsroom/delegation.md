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

**Internal scout (sonnet).** A second check on the email scout. For the
window since the last review slot, read these primaries directly: PlayStation
Blog, Xbox Wire, Nintendo news (nintendo.com/us/whatsnew and Nintendo's own
X-free pages), Steam news for the week's big titles, Famitsu and Gematsu
(Japan), IGN Middle East Arabic, True Gaming, Saudi Gamer, Tbreak, and Sony,
Nintendo and Xbox UAE and Saudi pages (store, support, prices). Then read the
email digests for the same window (do not mark them read). Return three
lists, one line per story with its primary URL and time: found by both, only
found internally (gaps in the email scout), only in the digests. Flag anything
that looks like breaking news at the top. No social media scraping, no logins.

**Footage (sonnet).** For a named game: list its Steam trailers
(`templates/trailer.py`), Nintendo store `publicId`s under its own nsuid, or
IGN MP4s; fetch the asked-for ones to uploads; make `seekmap.py` sheets.
Look for the publisher's own vertical (9:16) cut first (press kits, media sites), then a 4K copy,
then 1080p. Return file names, sizes, resolutions, durations and sheet paths. No YouTube or
social-media downloaders.

**Render (sonnet).** Given a batch folder with `copyNN.py`, `renderNN.py` and
the main session's five-line brief per Reel (angle, format, cover frame, sound,
key shot; CLAUDE.md "Creative brief and formats"): `check`, then `sheet`, then `draft`, then `strip`, and stop there with the
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
`postsListTool`, `ledger.py sync`, push dxb-assets. Then `git rm` the media (not
the .json files) from the folders that now have receipt.json and push that too. Return the post ids and states.

**Publish check (haiku).** `postsListTool` for the given window: report each
post's state and error. Then `newsroom/ledger.py sync`, commit and push
dxb-assets. Return one line per post.

**Housekeeping (haiku).** Commit and push leftover changes in dxb-assets
(ledgers, story files, cards); never touch dxb-queue.
Disk cleanup runs daily on its own (`newsroom/disk_cleanup.sh`, 02:47 Dubai);
run it by hand when free space drops under about 4 GB.

## Review slots (Mohammad, 5 Oct 2026)

He reviews at four fixed times, Dubai time: **06:30, 10:00, 14:00, 17:30**.
A trigger wakes the main session about 35 minutes before each slot:
1. Launch in parallel: the Digest digest card (all unread digests) and the
   Internal scout card (window since the previous slot).
2. Main session: merge both lists, run `ledger.py find`, verify the
   candidates against their primaries, decide lanes, chips, themes, accounts
   and proposed times, and note anything the email scout missed.
3. At the slot: send him the ranked shortlist (and, at 17:30 on Thursdays,
   Famitsu), ask for takes on DXB-KNIGHT items, and mark the covered digests
   read. A thin window gets a one-line "nothing worth posting" instead.
4. On his green light, build (Footage, Render, Drafts cards in parallel), and
   bring the Reels back for his "go"; then the Publish card.

Between slots he is only interrupted for genuine breaking news (عاجل level).

**Event slots.** Shows agreed one at a time from `newsroom/events.md`
(Nintendo Direct, State of Play, The Game Awards and the like, once the
date and time are confirmed): propose to him a pre-show slot (what to
expect, time in Dubai), live coverage during the show (announcements
captured as they land and checked against the official page before
posting), and a wrap-up slot after it; set one-off triggers only after he
agrees each one.
