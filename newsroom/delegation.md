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

**Digest digest (sonnet).** Read every digest in
dxbknight-digest@agentmail.to newer than `covered_through` in
`newsroom/digests-covered.json`, oldest first. Return one line per item: age
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
social-media downloaders. Stills are the last resort (advisor, 14 Oct 2026): before a
stills Reel, look for motion in this order and report what each step found: older
trailers of the game or series; the platform's or publisher's own clips and dev
diaries; the store page's video; his capture of the game; the source page recorded as
video (Playwright); our graphics in motion. Only then the official images, three or
four, neighbouring ones different in kind (art, screen, face), with their sizes.
A hardware story is no exception (14 Oct review): a single press still needs a
second angle by 3.5 s, and a line about a store page gets the page itself as a
still, cropped to the row the line is about (`templates/pageshot.py <url>
<out.png> --clip x,y,w,h`).

**Render (sonnet).** Given a batch folder with `copyNN.py`, `renderNN.py` and
the main session's brief per Reel (the news kind and its scenario from the
advisor canvas "Digital Lounge Reel Templates", board "Scenarios by news kind";
angle and hook kind, template from `formats.py pick` with the brief's fact
count and its opening beat from `formats.py check`, cover frame, sound, key
shot, the named turn and the second it lands on, the total seconds before the
end card (12 to 20 s target, advisor 14 Oct 2026; handson and edition exempt),
and one reason per line saying what the viewer sees and why it shows that line; CLAUDE.md "Creative brief and formats" and
"Templates and scenarios", 14 Oct): `check`, then `sheet`, then `draft`, then `strip`, and stop there with the
paths. A line over a card must be at most one visual line of framing or
absent (one fact, one place); report any line that repeats its card. Report
the `length`, `pace` and `close` lines reel.py prints at `check` when they warn,
and the `render times` line the final render prints (seconds per stage: checks,
montage, text, audio, outro; advisor, 14 Oct 2026: recorded for the next ten
Reels in `templates/assets/render-times.json`, before and after the one-encode
chain). A breaking-lane Reel renders with `profile='breaking'` and skips the
draft step.
On the strip, confirm the mark sits top left for the whole Reel, the credit
line is absent on the first frame and present from 2 s, and the end card is
2 s (advisor, 14 Oct 2026). After the main session clears the draft: `final`, `strip`,
copy that final strip and the shot sheet to `cards/YYYY-MM/<name>-strip.jpg`
and `<name>-sheet.jpg` (advisor, 14 Oct 2026: both go into git in the same
ledger commit as the mp4),
`outro.snap_cut` per Reel, 2-pass phone copies over 30 MB
(`vb = 27*8192/dur - 192`, `-passlogfile` before the output), two renders at a
time at most. Return paths and any error verbatim.

**Evening pre-fetch (sonnet), about 22:00 Dubai.** For every dated story in
`newsroom/events.md` due the next day (and the next Famitsu Thursday): fetch
the footage and official images through the allowed routes, make the seekmap
sheets, and run `reel.warm_cache(shots)` on the likely stretches so the picture
pass is cached under `uploads/cache/` before the day (advisor, 14 Oct 2026, rule
6). Report what is cached and what has no footage route yet.

**Idle card, quiet hours (main session plus Footage and Render cards; advisor,
16 Oct 2026).** Whenever no story is being built, work down this list:
1. Fetch footage and warm the picture cache (`reel.warm_cache`) for every dated
   story on the next day's calendar (`newsroom/events.md`: launches, embargo
   lifts, Famitsu Thursday, shows), as in the evening pre-fetch card.
2. Pre-build a shell Reel for anything due at a known time: footage, seekmap
   and shot list, strip layout, and the Arabic (both skills, grammar review)
   for everything except the final fact, kept in its batch folder with a
   `SHELL` note naming the missing fact. When the news lands, only the fact,
   the text pass and the encode remain.
3. Bank evergreen pieces (Ocarina episodes, retro on-this-day, list,
   explainer), each rendered and ready to queue, listed in
   `newsroom/evergreen.md` with what would date it.
Real news always comes first: every verified story landing 23:00 to 08:00
Dubai is built and queued at the 90-minute overnight spacing; mornings stay at
one post per 30 minutes at most, none bunched before 08:00.

**Morning digest (main session), by 07:30 Dubai.** One message to Mohammad
listing every post published since 23:00 Dubai, one line each: time (Dubai),
title, template, chip, and the strip path in `cards/YYYY-MM/`. Built from
`postsListTool` (PUBLISHED only) and the format ledger. A post he deletes is
recorded in its ledger story; a wrong fact found more than an hour after
publishing gets a correction Reel (`newsroom/corrections.md`), never a silent
deletion.

**Drafts (haiku).** Run `jobsNN.py`, then
`preflight.py --no-approval` on each new draft folder, and `ledgerNN.py`.
Return the preflight lines.

**Grammar review (sonnet).** The `arabic-grammar-review` stage on a given
text file, report only, no edits.

**Caption check (haiku).** Given a batch's `copyNN.py`: for every Instagram
caption (hook + story) and X text, report whether the game's name and the
news word (صدرت، تأجيل، السعر، تقرير، تحديث، رسمي and the like) both sit in the
first five words of the first line, in the Arabic and in any English line
(advisor, 14 Oct 2026); whether the first word of every paragraph is Arabic;
whether the last caption line starts with #ألعاب #أخبار_الألعاب and carries
exactly four tags; and the character counts (2200 Instagram, 500 Threads).
Report only; the main session rewrites.

**Weekly views (haiku), Tuesday morning before the audit.** Given the
Instagram views Mohammad sends per Reel: `python3 templates/formats.py views
<reel name> <views>` for each, then `formats.py templates` for the median per
template; append the table to `analytics/reel-views.md` with the date and
commit (advisor, 14 Oct 2026).

**Publish (haiku), only after his "go".** Before this card runs, the main session
re-checks any تقرير, شائعة or تسريب story (newsroom/corrections.md, queue-time
re-check) and puts the result in the approval note. Given the exact draft folders, times and
his approval note: `preflight.py approve` each, `git mv` to queue, `DRY_RUN=1
publish.py` and confirm it lists exactly those folders (stop and report if not),
push to dxb-queue main, wait for the receipts commit, read the captions back with
`postsListTool`, `ledger.py sync`, push dxb-assets. Then `git rm` the media (not
the .json files) from the folders that now have receipt.json and push that too. Return the post ids and states.

**Publish check (haiku).** `postsListTool` for the given window: report each
post's state; on the next breaking-lane Reel also ask Mohammad (one line) for a
phone screenshot of its first 2 s, to confirm the hook band and the 48 px mark
that the strip cannot show (advisor review, 14 Oct 2026). Then: report each
post's state and error. Then `newsroom/ledger.py sync`, commit and push
dxb-assets. Return one line per post.

**Housekeeping (haiku).** Commit and push leftover changes in dxb-assets
(ledgers, story files, cards); never touch dxb-queue.
Disk cleanup runs daily on its own (`newsroom/disk_cleanup.sh`, 02:47 Dubai);
run it by hand when free space drops under about 4 GB.
Posted Reels stay out of the working tree (14 Oct 2026, after the disk filled
mid-render with 7.5 GB of October mp4s checked out): dxb-assets uses a
non-cone sparse checkout that excludes `cards/2026-09/` and
`cards/2026-10/*.mp4`; every file stays in git. Before a new render is
committed, re-include it by name so `git add` takes it:
`git sparse-checkout add '/cards/2026-10/<name>*'` (its strip and sheet
jpgs are not excluded). A new month gets its own `!/cards/YYYY-MM/*.mp4`
line once its first Reels are posted.

## Review slots (Mohammad, 5 Oct 2026)

He reviews at four fixed times, Dubai time: **06:30, 10:00, 14:00, 17:30**.
A trigger wakes the main session about 35 minutes before each slot:
1. Launch in parallel: the Digest digest card (all digests since `covered_through`) and the
   Internal scout card (window since the previous slot).
2. Main session: merge both lists, run `ledger.py find`, verify the
   candidates against their primaries, decide lanes, chips, themes, accounts
   and proposed times, and note anything the email scout missed.
3. At the slot: send him the ranked shortlist (and, at 17:30 on Thursdays,
   Famitsu), ask for takes on DXB-KNIGHT items, and mark the covered digests
   read. A thin window gets a one-line "nothing worth posting" instead.
4. The queue runs without his pick (rolling queue, 13 Oct 2026). Every
   verified story is built in rank order (Footage, Render, Drafts cards in
   parallel, one render at a time); as each passes preflight, approve it
   with the note "go: rolling queue; preview sent HH:MMZ", queue it for the
   next free slot under the cadence rules (next quarter hour, at least 15
   minutes out, 30 minutes after the previous post in 08:00 to 23:00 Dubai,
   90 overnight, no two in a row on one game or publisher), push (Publish
   card), commit the Reel to dxb-assets together with its `<name>-strip.jpg`
   and `<name>-sheet.jpg` in the same ledger commit (advisor, 14 Oct 2026),
   and send him the preview with that time. His number moves a story
   to the front, "skip N" drops it, "hold" holds; silence runs the queue.

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
pages that have no feed: Nintendo US whatsnew (nintendo.com/us/whatsnew/; the old press page is gone), Steam
news for the top sellers, Capcom (capcom.co.jp IR news), Square Enix
(www.hd.square-enix.com/eng/news/; without www it refuses), Bandai Namco (bandainamcoent.com/news),
Konami (konami.com/games/jp/ja/topics/; the English news page is gone),
EA, Ubisoft, Riot, thegameawards.com/news, Famitsu (famitsu.com front page; /news/ is gone), and the regional
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
fresh, grammar review, DeepL back-check and forward pass), Reel, drafts, preflight. Then
ping him (PushNotification, one line: the story and the proposed time) and
set a 15-minute send_later. If he answers, follow his answer. If he has
not replied when it fires, approve with the note "auto-go: no reply in 15
minutes (breaking lane, Mohammad 11 Oct 2026)" and queue it a few minutes
out, then the publish check as usual, and tell him what went out.
Limits: Digital Lounge only; official, verified news only (never a
rumour, leak or single-outlet report, at any hour); auto-posting was 08:00 to 23:00
Dubai until 16 Oct 2026; from then round the clock (advisor, 16 Oct 2026,
agreed with Mohammad), so a story found overnight is pinged, built and
auto-goes after 15 minutes like any other, spaced at least 90 minutes from
the previous post between 23:00 and 08:00; at most three auto-posts in any
24 hours; a story he has turned down is never auto-posted.
