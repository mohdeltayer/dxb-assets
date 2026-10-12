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

## Hourly watch and the breaking lane (Mohammad, 11 Oct 2026)

He wants Digital Lounge on top of the latest news even when he is away.
The official-source check is split in two, and runs every hour. It never
skips (Mohammad, 12 Oct 2026, after it skipped five runs during renders):
the Watcher and Verifier are background helpers that only read the web, so
they launch at once even mid-render or mid-slot; only building a Reel for
what they find waits for the current render, and a breaking story is
pinged to him straight away.

**Watcher (haiku).** Reads only the official sources below, compares every
item with `newsroom/watch-seen.json` (url, title, first seen), adds the new
ones to it, and returns only items first seen this hour, one line each:
time (UTC), source, headline, URL. Nothing new returns "nothing new".
No judging, no verifying, no social media, no logins.
When watch-seen.json is empty (the first run) it records everything it
sees and reports only items published in the last two hours.
Feeds first (Mohammad, 12 Oct 2026, after five sources refused the
watcher): the Watcher starts by running `python3 newsroom/watch_feeds.py`,
which reads every official RSS feed with a browser user agent, records new
items in watch-seen.json and prints the ones from the last two days, plus a
"failed:" line. Feeds: PlayStation Blog, Xbox Wire (serves a browser, not a
bare script), Nintendo Japan, Take-Two investor news, Atlus, Bungie,
Gematsu, and Google News backstops for the sites that refuse us (Rockstar,
Blizzard, Fortnite, Sega, Square Enix games; hours late, Google redirect
links, so the Verifier opens the real page). Then the Watcher reads the
pages that have no feed: Nintendo US whatsnew and Nintendo press, Steam
news for the top sellers, Capcom (capcom.co.jp IR news), Square Enix
(hd.square-enix.com/eng/news/), Bandai Namco (bandainamcoent.com/news),
Konami (konami.com/games/jp/ja/topics/; the English news page is gone),
EA, Ubisoft, Riot, thegameawards.com/news, Famitsu, and the regional
official pages (PS Store UAE and Saudi, UAE gaming bodies). Use a browser
user agent for every page. Sega's site rate-limits us and the Saudi
Esports Federation and GEA sites refuse us: those, Rockstar and
Epic/Fortnite are covered on X by Gaming Watch (below).

Outlets (Mohammad, 12 Oct 2026: "add resources from large blog posts
especially ones that update quickly"): the same script reads 31 outlet
feeds (IGN, GameSpot, Eurogamer, VGC, Kotaku, Polygon, PC Gamer, RPS, The
Verge, Push Square, Pure Xbox, Nintendo Life, Insider Gaming,
GamesIndustry.biz, Game File, Siliconera, Destructoid, Game Informer,
GamesRadar, Dexerto, TheGamer, Gamekult, Gematsu, Automaton and 4Gamer in
Japanese, and the Arabic outlets IGN Middle East, True Gaming, Saudi Gamer,
VGA4A and Arab Hardware). It groups the same story across outlets and prints
each with the number of outlets that ran it in the last 24 hours, most
covered first; guides, puzzles and deals are dropped, and single-outlet
items stop at 25 a run. The main session reads the list and passes only the
candidates to the Verifier. Outlets are leads, never proof: the Verifier
finds the company's own words. A story only outlets carry is a تقرير for a
review slot, never the breaking lane; the Arabic outlets also show what the
competition already ran.

**Verifier (sonnet).** Given the watcher's new items, for each one: open
the primary and quote the claim, run `ledger.py find` with at least two
keywords plus a grep of `stories/`, and grade it:
- BREAKING: unscheduled, major, confirmed by the company itself (a
  surprise reveal, a release date, a delay, a price change, a shutdown,
  a big number, a studio closure, a major regional announcement);
- NEW: confirmed official news worth a Digital Lounge post today;
- SKIP: routine (sales, minor patches, merch), already in the ledger,
  rumour, leak or a single outlet's report.
Return BREAKING and NEW items with the quoted primary, the ledger result
and why it matters. Never posts or drafts.
X-only claims (Mohammad, 11 Oct 2026): the external scout, Gaming Watch
(gamingwatch@agentmail.to), can read X. Email it from
dxbknight-digest@agentmail.to with the account, the claim and what to
quote (exact text, URL, time, linked page); its reply lands in the digest
inbox, and the next hourly run reads it. An X post by the company or person
itself counts as the primary once its text is quoted verbatim.

**Main session.** On BREAKING or NEW: brief, footage, Arabic (both skills
fresh, grammar review, DeepL back-check), Reel, drafts, preflight. Then
ping him (PushNotification, one line: the story and the proposed time) and
set a 15-minute send_later. If he answers, follow his answer. If he has
not replied when it fires, approve with the note "auto-go: no reply in 15
minutes (breaking lane, Mohammad 11 Oct 2026)" and queue it a few minutes
out, then the publish check as usual, and tell him what went out.
Limits: Digital Lounge only; official, verified news only (never a
rumour, leak or single-outlet report); auto-posting only 08:00 to 23:00
Dubai, and a story found overnight is built and held for his go or for
08:00 with the same 15-minute ping at 07:45; at most three auto-posts a
day; a story he has turned down is never auto-posted.
