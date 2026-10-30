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
For an item the digest found in an Arabic outlet, give the time of its first
report anywhere (primary, English or Japanese outlet, forum) beside the
relay's time (Mohammad, 17 Oct 2026).

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
For anything first seen in an Arabic outlet, find and give its first report's
time; over 24 hours old at the origin goes under "stale relay", not in the
lists (Mohammad, 17 Oct 2026).

**Director (advisor, 21 Oct 2026; model by tier from 25 Oct, Phase 1 step 4).** Model: sonnet for routine
and evergreen Reels; opus for fresh reveals, anything with speech (voiced or subtitled), debates and the
first Reel of a new format or template. The story file records it as `"director_model"`, so the week's
quality can be compared. A separate agent, after the draft
render (or the runner render) and before the real encode or queuing. Inputs:
the job file, the source footage in uploads, the Reel's 4 fps strip
(`decodecheck.py <mp4> --strip`, or the runner's `<name>-dense.jpg`), the
transcript with sentence boundaries (`templates/speechcheck.py --stretch <file>
<start> <secs>`; its lyrics pass can hallucinate on music, so weigh isolated
low-confidence words), the face-direction ("profile") and crop-edge text flags
from `reel.shotsheet`, and loudness and music-against-speech measurements
(ffmpeg ebur128, astats). Audio order: the trailer's own sound, music-led or
voiced, as one continuous stretch; our bed only for silent footage, stills, our
graphics, or when no coherent stretch exists. Trailer sound is the default
(advisor, 23 Oct 2026): narration is no reason to drop it (whole sentences,
subtitled when it is the news, lines in the pauses); clean effects-led gameplay
audio passes, only harsh effects (constant explosions, engines, screams) fail a
stretch; before approving our bed on a footage Reel, check the game's other
official trailers and clips, list each one checked and why it failed in the
decision, and say so plainly. Our bed stays the norm only for sales charts,
numbers Reels, our graphics, stills, silent footage, retro, tribute, and
breaking news with silent or unusable footage. A bed it approves on footage
means the preview to Mohammad opens with "our bed". Voiced stretches: whole
sentences, start at a sentence start or in a pause, end after a sentence ends;
story lines land in pauses, never on speech (the headline may sit over speech
in the first 3.5 s); speech that is the news gets an exact Arabic subtitle with
no story line over it. Writes the edit decision in the draft notes, one line
each: audio (trailer music / voiced, which sentences, start..end / our bed, and
why), lines (where each lands, pause or shot, with times; any to re-time),
shots (any to replace or reframe), verdict (pass, or the list of fixes), unsure
(how a passage may feel, for the preview note). It may write the fixed job file
to the scratchpad and must show it passes `render_job.py check`; it never
edits the Arabic, commits, pushes or queues. Up to two send-backs; then pass
with a note, or the story moves to a simpler template. A voiced track it
approves goes into the job as `"speech_ok": "<reason>"` and into the draft spec
as `"speech_director": "<decision>"`, so the pre-queue transcription reads the
speech against its decision instead of stopping on it.
Trailer audio split (Mohammad, 24 Oct 2026, inbox 16:26Z; CLAUDE.md "Trailer
audio split, live"): on a job with a trailer track the runner plays the
trailer's music stem under the whole Reel and puts back only each shot's own
effects. The director reads the runner log line `render_job: audio split:` (or
`audio_split` in render-times.json) and checks: every sound heard matches what
is on screen (an effect only on its own picture: a clash on the clash, an
explosion on the explosion, nothing over people sitting and talking); the music
track is clean (no leftover effects, voices, or watery or broken sound). A
mismatch fails the Reel. When the split was not applied (its reason is logged),
the Reel carries today's mixed track and the same check applies to it: a
mismatch there means another stretch, another trailer, or our bed with its
reason. A voiced or subtitled Reel the director approves keeps its speech by
`speech_ok` (or `"speech_keep": true`), which skips the split.
Trailer news (advisor, 26 Oct 2026): when the news is a trailer or teaser, the
director asks "is it the actual trailer?". Stand-in footage from other games or
older trailers in its place is a send-back; with only key art, the official art
with motion. The on-screen credit runs while the trailer plays, and the
trailer-showcase layout is allowed when 9:16 cuts the trailer badly.
People stories (advisor, 23 Oct 2026): when a person is the news, the director
checks the person's photo window appears with the line that names them within
the first 3 to 4 s, the face is visible, not cropped by the window or the plate,
and readable at phone size, the name plate gives the role, the photo source in
the brief is on the allowed list (press kit, awarding body, licensed and
credited), and the first frame shows the person and the game together; a
missing person window on such a story is a send-back.
Legal, piracy, hacking and leak-enforcement stories (advisor, 26 Oct 2026;
CLAUDE.md section of that name): the director checks the wording is neutral and
attributed (no side taken, no leaker's framing), nothing leaked or extracted is
on screen (not even blurred), there is no how-to or tool link, the footage is
official, and the sound is our channel bed; any miss is a send-back.
Answer the why (advisor card adv-20261027-answer-the-why, approved by Mohammad
27 Oct 2026, 19:43 Dubai, after the Pokémon UNITE comments asked "for good or an
update?" and "why?"). Every Reel, above all shutdowns, delays, price changes,
layoffs, removals and bans: (1) the reason, attributed when the company gave one;
when it gave none, the Reel or the caption says so in plain words («لم تعلن الشركة
سبب الإغلاق» or the like); never a guessed reason, never context dressed as the
reason; (2) what it means for players, answered from the primary: is it final, until
when can I play, what happens to purchases and progress, which regions; (3) scope:
which regions the announcement covers, and when the primary is regional (a Japanese
account only) the text says so instead of implying a worldwide decision; (4) the
pinned source comment carries the reason line and the key dates. Director question
before upload: "What will the first comment ask?" If the Reel does not answer it,
add a line or a card; a miss is a send-back.
Lines as one paragraph (advisor card adv-20261029-lines-as-one-paragraph, approved by
Mohammad 29 Oct 2026, 06:01 Dubai; STYLE.md, The Reel). Read the headline and every line in
order as one text, aloud: if nobody would say it that way, it goes back. Checks: the subject
is named before any pronoun refers to it; no line opens on «و» unless it continues the line
before within 3 s; in-game terms explained or replaced with plain words; a comparison Reel
labels both halves on screen. The read-aloud text goes in the story file (`read_aloud`).
QA format (advisor, 23 Oct 2026; CLAUDE.md "Director QA format"). For every
shot, pull one frame (the shot's middle, plus its first frame when a line
enters there) and check: framing (subject in the 9:16 crop, no side-on face
without look room, no cut text at the edges); text (readable at phone size,
inside the safe zone, first word Arabic, up long enough); picture (no decode
damage or blockiness, no title card or slate, nothing graphic); sound (what
plays under the shot: music, voiced and subtitled, or our bed; no word cut at
the cut; every sound heard matches what is on screen, the music track is
clean); reason (the shot shows what its line says). Return a compact table,
one row per shot: shot, time (Reel seconds and source seconds), PASS or FIX
with the one change needed. Then the Reel-level checks once: cover as a grid
tile, length against the template target, a change every 3 to 4 s, the last
2 s a picture, sound per the trailer-sound rule (our bed only with its stated
reason), the audio split's outcome (applied, or why not) and the check that
every sound heard matches what is on screen and the music track is clean. Verdict: PASS, or the list of fixes. On a second look, check the
changed shots only (plus the Reel-level line). The main session pastes the
table into the story file's draft notes (`director_qa`); the evidence is the
committed strip and sheet, no extra files. Two rounds of fixes at most.

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
advisor canvas "Digital Lounge Reel Templates", board "Scenarios by news kind",
and its recipe from the board "Scenario recipes, second by second" with the
focus written second by second, one focus at a time on screen (24 Oct 2026);
angle and hook kind, template from `formats.py pick` with the brief's fact
count and its opening beat from `formats.py check`, cover frame, sound, key
shot, the named turn and the second it lands on, the total seconds before the
end card (12 to 20 s target, advisor 14 Oct 2026; handson and edition exempt),
and one reason per line saying what the viewer sees and why it shows that line, and the "sensitive" line: none, or which rule of CLAUDE.md "Culturally sensitive details" applies and how the wording and shots handle it (21 Oct 2026); CLAUDE.md "Creative brief and formats" and
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

**Render lanes (advisor card adv-20261027-two-lanes, approved by Mohammad 27 Oct 2026, 14:29 Dubai).**
Two lanes run at the same time; the main session assigns and never waits on a render.
- Lane A, news (unchanged): the job file goes to `jobs/render/`, the push starts render.yml on GitHub.
  Breaking stories are always lane A. The main session watches for the `-publer.json` receipt with a
  background poll (no agent needed).
- Lane B, evergreen and non-urgent (lists, watch guides, series pieces, weekend pieces, reserve-bank
  items): the job file goes to `jobs/live/` and render-live.yml is dispatched on dxb-render-1
  (`runs-on: [self-hosted, dxb-render]`), same checks, same Publer upload.
- **Lane B render helper (haiku), one per lane-B job.** Dispatches render-live.yml with the job,
  watches the run, and falls back to GitHub by moving the job file to `jobs/render/` (git mv, commit,
  push) when the server has not started the run within 5 minutes, or when the run fails for a server
  reason (runner lost, tools, fonts, checkout, disk, footage fetch, timeout). A QA failure from
  render_job.py or decodecheck is never a fallback: it is reported back with the error line. Done when
  the `-publer.json` receipt is on main; limit 30 minutes. Reports lane, dispatch, start and end time,
  render seconds, receipt, any error. The main session writes the fallback into the card it sends.
- Measure for 48 hours from 27 Oct 10:40Z, then one card: per lane, Reels, median and slowest job
  time, setup time, failures and fallbacks, peak memory and disk on the server, and any two lane-B
  renders at once. Nothing moves lane A off GitHub until Mohammad decides after that card.
- Quiet hours: refill the evergreen bank in lane B (most-wishlisted, release calendar, series).

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
Real news always comes first: every verified story landing overnight is
built and queued at the overnight spacing (60 minutes, 00:00 to 08:00 Dubai;
constant coverage, 16 Oct 2026); mornings stay at one post per 30 minutes at
most, none bunched before 08:00.
The bank keeps at least 6 ready Reels at all times (constant coverage): when
`newsroom/evergreen.md` lists fewer, step 3 comes before steps 1 and 2 unless
a dated story is due within 12 hours.

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
Also (17 Oct 2026): every person named carries a role word at first mention in
the Reel lines, the caption and the X text; and the X and Threads text names
the source (outlet or company) for any quote, report, rumour, leak or
interview.
Report only; the main session rewrites.

**Source reply (haiku).** When a reader asks for the source («وش مصدرك؟»,
«المصدر؟»), read the story file's primary and draft one Arabic line for
Mohammad to post: outlet, date and link on X and Threads; outlet and date only
on Instagram. Never a source that is not in the story file.

**Weekly views (haiku), Tuesday morning before the audit.** From 23 Oct the
numbers come from Publer, not from Mohammad: last week's views, reach and
shares per Reel (`get_post_insights` / `export_publer_analytics`), then
`python3 templates/formats.py views <reel name> <views>` for each, then
`formats.py templates` for the median per template; append the table to
`analytics/reel-views.md` with the date and commit (advisor, 14 Oct 2026; Publer
source 23 Oct 2026).

**Publer post (main session; advisor, 22 and 23 Oct 2026).** Per Reel, after
the gate: upload the mp4 once from its public dxb-assets URL
(`upload_publer_media_from_url`), then one `submit_publer_posts` call per
account at the same minute: Instagram `post_type: "reel"` with the caption and
`location: "Dubai, United Arab Emirates"`, X `video` with the short text,
Threads `video` with the Threads text. Every post takes the labels template,
skin, sound (trailer / voiced-subtitled / our bed) and genre
(`list_publer_labels` first, same spelling; the first post, Valve HLX on 22 Oct,
set the form `tpl:trailer`, `skin:house`, `sound:trailer` / `sound:voiced` /
`sound:bed`, `genre:shooter`). If Publer's location lookup fails (22 Oct: "undefined
method [] for nil" for both "Dubai, United Arab Emirates" and "Dubai"), post
without it and note it in the story file. Source follow-up: X a reply with
the source link, Instagram a comment «المصدر: ...» with no link
(`follow_up_comments`); Threads keeps the source in its text. Strongest
non-urgent Reels wait for Thursday 17:00 to 21:00 or Friday 19:00 to 22:00
Dubai. After the slot, `list_publer_posts` shows all three Published; a
failure is rescheduled once, then reported with Publer's reason. Once all
three read Published, write the slot to dxb-queue `ops/heartbeat.json`
(`last_published` UTC, `story`, `checked_at`) and push it: the stall alarm
(dxb-queue `stall-alarm.yml`, 25 Oct 2026) pages Mohammad when it is over
3 hours old between 08:00 and 02:00 Dubai. In the same step (adv-20261030-close-published-cards,
Mohammad 30 Oct 2026): write the Inbox `published` entry (doc id = story id; title, chip,
template, sound, platforms, links, published_at UTC, route) and close the story's preview card
(status done, outcome with the Dubai time, the platforms and the Instagram link); a card whose
deadline passed with the default applied closes the same way. Story file:
"scheduled in Publer HH:MMZ" with the platforms; ledger slot. No IDs or tokens
in public files.
Then `python3 newsroom/ledger.py genres 7` for the audit's one line, stories
per genre that week: information only, it shows blind spots in the sources and
never forces a story (advisor, 21 Oct 2026). Every new story file carries
`"genre": [primary]` or `[primary, second]` from `ledger.GENRES`.
The audit also counts the week's Reels by sound: trailer, voiced and
subtitled, our bed (from each story file's sound note). Our bed on a footage
Reel should be the rare exception; list each one with its reason (advisor,
23 Oct 2026).

**Pre-publish gate (main session, every post; advisor, 18 Oct 2026).** Time box
10 minutes, 5 on the breaking lane, never a wait. Check the primary (read the whole
page: Update, Correction, Editor's note, a changed date; chart against text), the
outlets that reported it, and a news search for a denial, update or new date. Exit A:
the primary confirms every on-screen fact, chip جديد or رسمي, and every date, time,
price and figure is the primary's (publisher over store, time zone stated). Exit B: no
primary in the time box, publish now as تقرير / تسريب / شائعة, the text names who
reports it and carries «لم تؤكد [الشركة] الخبر بعد». Record `gate HH:MMZ: <what was
checked, what was found>` in the approval note. Posts queued more than 6 h ahead are
gated again within the hour before they publish (set a send_later when queuing); a
dated story built more than 12 h before its slot is rechecked in full. If the gate
fails on a scheduled, unpublished post, delete it in Postiz (`deletePostTool`),
requeue the fixed or relabelled version and send Mohammad the preview; published
posts are his to delete.

**Publish (haiku), only after his "go".** Before this card runs, the main session
runs the pre-publish gate above and puts the result in the approval note. Given the exact draft folders, times and
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

**Server watch first (advisor card adv-20261029-watch-reads-server-first,
approved by Mohammad 29 Oct 2026, 19:13 Dubai; from the 20:07 Dubai run).**
The mechanical watch on dxb-render-1 (`ops/backoffice/watch/`) reads the 100
sources; the hourly run reads its list instead of launching helpers by habit.
Quiet hours start no helper at all. This replaces "launch the Watcher every
run" below; the breaking lane, auto-go, constant coverage, spacing and the
gap alarm are unchanged.
1. Read the server watch's new items for the last hour: `watch/digest.json`
   and `watch/breaking.json` on the branch `watch-digest` of dxb-assets
   (`git fetch -q --depth 1 origin +watch-digest:refs/remotes/origin/watch-digest
   && git show origin/watch-digest:watch/digest.json`). If `generated_at` is
   more than 50 minutes old (GitHub held back the :52 schedule on its first
   day), dispatch `watch-digest.yml` on main and read again after it lands
   (about 2 minutes). Since 29 Oct (adv-20261029-server-watch-
   publish-now, Mohammad: "Public branch, titles+links"), the workflow
   `watch-digest.yml` runs the watch's digest on the dxb-render server at :52
   and force-pushes those files there: titles, links, times, sources and media
   links only, no outlet text (dxb-assets is public). The 60-day item store
   stays on the server. The server has no key for dxb-queue or a private repo;
   if Mohammad later creates dxb-watch and its token, the output can move
   there. Process only items with a `seq` above the last one handled (kept as
   `server_seq` in `newsroom/digests-covered.json`; for breaking items, the
   `recent` list with `breaking_seq` above it). Fallback only when the
   digest's `generated_at` is more than 90 minutes old or the branch cannot
   be read: run `python3 newsroom/watch_feeds.py` and `python3
   newsroom/watch_pages.py` yourself (seconds, no tokens) and treat what
   they print as new as the list; say "server watch not read: <why>" in the
   commit. Not running either script and not launching the Watcher is the
   normal case once the server list is read.
2. Nothing new, or only items already seen or already posted (`ledger.py
   find`): run the gap alarm, commit watch-seen, stop. No helper, no
   Verifier, no message.
3. Something new: triage it yourself in one pass. Start the Verifier
   (sonnet) only for items that could be Digital Lounge posts, one Verifier
   for the batch. Start the Watcher (haiku) only for the official pages the
   server watch cannot read (list below), or for pages `watch_pages.py`
   prints under "needs a look:" in the fallback.
   Pages the server watch cannot read (its `not covered:` line, 28 Oct):
   Konami JP topics (konami.com/games/jp/ja/topics/), Sony Group press, PS
   Store UAE and Saudi, UAE gaming bodies. Epic, the Saudi Esports
   Federation and GEA stay with Gaming Watch on X. When the server starts
   reading one of these, drop it from this list.
4. Log every run, one JSON line in `newsroom/helper-runs.jsonl`: `at` (UTC),
   `list` ("server seq N, generated HH:MMZ" or "fallback: <why>"), `new_items`, `helpers`
   (list of `{"role", "model", "count"}`, empty when none), `reason`. The
   Friday usage review and the first release note after the change report
   helper runs per day before and after. Before (estimate from this week's
   watch commits, the old prompt launched the Watcher every run): about 24
   Watcher (haiku) runs a day, and a Verifier (sonnet) on about one run in
   four, about 6 a day.
The "Inbox mirror for the desk dispatcher" hourly task ends the day the
server dispatcher is installed; production disables it that day and says so
in the release note.

Every run also reads Mohammad's inbox (`items` on
https://claude.ai/artifact/AwcHX88eyTrUAL9pc4j4AW, CLAUDE.md "Mohammad's
inbox", 24 Oct 2026): act on answered production items and mark them done
with their outcome; apply the default of any item past its deadline. A
breaking ping goes into the inbox as an approval item too, deadline 15
minutes out, default "auto-go".
Read every item, not only production's (24 Oct 2026, after two approved
advisor memos waited about 90 minutes and a "pause" answer went unseen for
76 minutes, across a context compaction): query the whole `items`
collection and act on (a) every item with status "answered", whoever wrote
it, and (b) every item `from` "advisor" with `to` "production" that is not
"done". An answered advisor memo addressed to production is applied first,
before any build or scheduling in that run, and a stop or pause answer
takes effect before anything else. The same full read runs before every
Publer submit and after every context compaction, so a summary never
stands in for the inbox. The run's commit names each item it acted on.
Status board (advisor, 25 Oct 2026): each item the run starts on gets
`picked_up_at` and a one-line `progress`; `progress` is updated when the step
changes; a finished item gets status "done", `outcome` and `updated_at`, and
one production decides not to do gets "done" with the reason. Any answered or
advisor item older than 30 minutes without `picked_up_at` is picked up in
this run, before anything else.

Triage of the OUTLETS list (Mohammad, 17 Oct 2026): a group marked "AR RELAY"
is dated from its first report anywhere before it is considered; over 24 hours
old at the origin and not posted, it is dropped unless something new landed.

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

**Gap alarm (main session, every run; constant coverage, 16 Oct 2026).**
Run `python3 templates/formats.py gaps 2` from dxb-assets. It reads the slots
in the format ledger and prints any spacing or gap rule that would break in
the next two hours (Dubai time: at least 30 minutes between posts 08:00 to
24:00 and 60 minutes 00:00 to 08:00; never more than 60 minutes without a
post by day, 2 hours by night). Put its lines in the watch-seen commit
message ("gap alarm: ..."), then queue the next finished Reel into the gap,
or, with none ready, a banked piece from `newsroom/evergreen.md`, at the
earliest slot the spacing allows, preview sent at the same time. "ok" means
nothing to do.

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
auto-goes after 15 minutes like any other, at the constant-coverage spacing
(60 minutes from the previous post between 00:00 and 08:00 Dubai, 30 by day;
breaking news may break it); at most three auto-posts in any 24 hours; a story he has turned down is never auto-posted.
