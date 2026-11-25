# Working on Digital Lounge (and DXB-KNIGHT)

The rules in force on 24 Nov 2026, grouped by topic. The full dated history (every case, test, number and the reason
behind each rule) is unchanged in `docs/history.md`; a heading here names its section there in brackets. When a rule
changes, update this file, `STYLE.md` and `docs/history.md` in the same commit. Where this file and the history differ
on a detail, the history wins and the difference is raised with Mohammad. No em dashes anywhere, in posts, cards or notes.

Reading order for a production run: `ops/READ-FIRST.md`, `STYLE.md`, this file, dxb-queue `desk/board.md` (trimmed daily
to the last 24 hours). Open `docs/history.md` only for the section a task needs.

## 1. The accounts

- **Digital Lounge (ديجيتال لاونج)**, the Arabic games news outlet ("the regional IGN"): X @the_digilounge, Instagram,
  Threads. Every story goes to all three at the same minute with the same Reel. Outlet voice, no first person. Games only:
  news, hardware, business, the Gulf and Arab scene, esports when big or regional; film or TV only for a game adaptation
  gamers talk about; no AI, phones or general tech. National days are not covered. [Two accounts]
- **DXB-KNIGHT (@DXBNIN)**, Mohammad's English personal account: on hold (option B, 11 Oct). No routine production; a
  hero piece or a take is built only when he brings one, and an opinion piece is DXB-KNIGHT only. Its card rules (ask
  for his take first, `single` with art on top, chips, fast lane) are in the history. [Two accounts; Always ask; Chips]
- **Off:** TikTok (dropped 1 Oct), YouTube Shorts except the original-material lane below, Snapchat (paused 9 Oct),
  Postiz (shut down 22 Oct; never used again). Threads, X and Instagram run through Publer.
- **YouTube original-material lane** (trial from 17 Oct): our own data and graphics only (Famitsu, numbers, lists, Gulf
  prices, retro, his hands-on), a cut under 35 s, Arabic-first title; trailers never go to YouTube. [Two accounts,
  YouTube lane]
- **Mohammad's inbox** (https://claude.ai/artifact/AwcHX88eyTrUAL9pc4j4AW, collection `items`): information only since
  21 Nov (failures, corrections, a one-line note that a special piece is scheduled). Publer is the review screen: he gives
  feedback in the advisor chat; nothing waits for a tap. Cards carry what he needs to decide without opening links; the
  Status tab fields (`picked_up_at`, `progress`, `outcome`) are kept. No tokens or ids in an item; done items older than 14 days are deleted. An advisor memo he approves in the inbox is
  applied as if he had pasted it and recorded in CLAUDE.md, STYLE.md and docs/history.md. [Mohammad's inbox]

## 2. News and sources

**What we cover.** The whole games slate for Arabic readers, regional stories leading more often than on English
outlets, plus anime-style, HoYoverse, mobile (PUBG Mobile, Free Fire, CoD Mobile, Supercell, Roblox) and football (EA
SPORTS FC, eFootball). No quotas; news value decides. Every story file carries `genre` ([primary, second]). [Wider
monitoring]

**Speed and age.** Being first in Arabic is the point. A story is dated from its first report anywhere, not from the
relay; an Arabic outlet is never a lead on its own (trace it to the first report). A story the Arabic press has not
carried is still news at 24 to 48 hours (the text says when it broke). Older than that with nothing new: drop it, unless
it is regional news the wider press missed. [Read every unread digest; Evergreen spacing 3]

**Urgency tiers** (games-news-editor skill): T0 breaking (showcase announced with its time, shadow drop, official
date/delay/cancel of a major game, hardware price or reveal, closures, deaths) publishes the minute it passes the checks,
simplest template, never into a slot; a message from Mohammad starting "T0:" is breaking by definition. T1 fresh reveal
under 45 minutes. T2 routine in the rolling queue. T3 evergreen fills gaps. Expansion passes and DLC with an official
trailer go out on announcement. [Publishing; desk/board.md standing orders]

**The ladder and labels.** رسمي / جديد when the primary confirms every fact on screen; تقرير when a credible outlet
reports it (text names the outlet and «لم تؤكد [الشركة] الخبر بعد»); تسريب leaked material; شائعة anonymous or social.
Never louder than the source. عاجل is rare (once or twice a week at most); most news is جديد. A country chip
(الإمارات، السعودية ... in bright indigo) only when the country is the story. Reports, leaks and rumours are welcome for reach, at most one post in three, never in the
breaking lane. When in doubt, publish with the honest label; what the text states stays verified. [Speculation for
reach; When in doubt]

**What counts as a source** (9 Nov, r4). A primary is the company's site or store page, its official YouTube or X post
(an official video is a primary for what it shows and says), a press wire or a filing. One credible outlet is a source
(تقرير). The scout searches for each story itself; a newsroom front page that does not show it proves nothing. A lead is
rejected only for: no_source (after a search, with what was searched, confirmed by the editor), denied by the primary,
harmful_or_out_of_scope, duplicate with nothing new. Not reasons: single outlet, no written primary, the date only in a
video, a relay, waiting for a statement, under 48 hours with no Arabic coverage, no trailer, variety. Orders and
handoffs come before the scout and only Mohammad drops one. No silent holds: a carried lead names what it waits for and the next run decides it. Store prices stay in the
currency the store returns (Xbox and PS Store UAE in USD, Xbox Saudi in SAR), never converted. Lists:
`newsroom/sources.md`. [Coverage over caution; Scout additive trial]

**Excluded:** Al Jazeera and every affiliated outlet, institute or platform, on any topic, also through republishers.
[Verify against primary sources]

**The pre-publish gate** (every post): check the primary, the reporting outlets and a news search for a denial or update
(10 minutes; 5 on the breaking lane), note `gate HH:MMZ: ...` in the approval note. Dates, times, prices, deadlines and
figures come from the primary itself; publisher over store, with the time zone. Read the whole primary (Update,
Correction, changed date). A post queued more than six hours ahead is gated again within the hour before it publishes;
a dated story built more than 12 hours before its slot is rechecked in full. Attribute a company's numbers to the
company. A change at the source after we post is an update (chip تحديث, or رسمي confirming a تقرير), never "correction"
wording; our own error is deleted and reposted within the first hour, after that Mohammad decides; an update never states or
implies that the source changed when the error was ours. Live posts are never changed afterwards unless Mohammad asks. Every case gets a line
in `newsroom/corrections.md`. [Verification without delay]

**Beat sheet and focus.** Every brief names its family from the advisor board «Beat sheets: nine story families»
(product, announcement, numbers, people, setback, leak or rumour, release, debate, fun) and writes the focus second by
second from `notes/scenario-recipes.md`: one thing on screen at a time (no story line while the person window or a card
opens, no strip coming in under a new line). Product, announcement, release and deal stories get the WHERE AND HOW MUCH
frame (every platform as a logo, the price beside each in AED with the dirham sign or USD marked, the date, unknowns said
«لم يُعلن السعر بعد», held 2 to 3 s). A new image and a new fact every few seconds, a payoff in the second half; no length
cap (12 to 20 s of story is a guide; handson and edition are exempt). A closing question only on stories readers argue
about, never on launches or prices. Event kits are prepared before predictable shows (TGA, Directs, State of Play).
[Beat sheets; Scenario recipes; Hook rule; Advisor memos C 13]

**Story brief before lines.** Every job gets four lines first (hook: the one surprising thing; why now; what it means for
players here; payoff) plus the story-type items in `newsroom/reel-check.md` (interview: who, where, two or three short
attributed quotes; delay: old date, new date, reason or none; out now: platforms, AED price, what it is; numbers: figure,
period, source, comparison; trailer: what is new in the footage; people: who, role, the news; event: Dubai time, where to
watch). Read `newsroom/editorial-memory.md` for the story type; add an entry the same day for each hold, correction or
praise. [Story brief and editorial memory]

**Sources and names on screen.** People are labelled by role at first mention («المخرج ...»), always when the name is
also a game or studio. X and Threads text names the source of every quote, report, rumour, leak or interview in a few
words. A reader's "source?" is answered from the story file (outlet, date, and link on X and Threads; no link on
Instagram), drafted for Mohammad. [Sources and names]

**Sensitive details.** The game always runs; the detail stays general. LGBTQ content: the general word («الزواج»،
«العلاقات العاطفية»، «خيارات العلاقات») everywhere, shots that do not show it, never a false detail or a denial; a
regional ban quotes the authority's own wording. Evolution, religion, politics and real conflicts: neutral, attributed
(«حسب وصف الاستوديو»), no first person, headline leads with the news. Legal, piracy, hacking and leak enforcement:
neutral and attributed, no how-to, no tool names or links, never the leaked material, official footage only, our bed.
Bans and censorship carry the official decision and the publisher's response only, no commentary (chip رسمي or
تقرير). Mods and community records need the creator's permission and an on-screen credit. A breach takes the عاجل skin
only on official confirmation and never shows methods. Every brief carries a "sensitive" line. Nothing graphic (blood, gore, finishing kills, sexual content) in any Reel;
pixel-art and stylised hit effects are not gore. No AI-generated visuals of hardware or people; any AI image used is
labelled an illustration; never add an AI label to official footage to get past a platform flag. [Culturally sensitive details; Legal, piracy; Full-screen format]

**Variety.** A game or series posted in the last few days does not come back without real news; no two posts in a row on
one game or publisher; spread a slot's picks across publishers. [Variety]

**Scout and work order.** Every Production 2 run starts at the keeper's work order (keeper-status branch
`keeper/work-order.md`) and executes it top to bottom: alarms, Mohammad's orders (T0 first), open handoffs, the digest
head and the scout's carried leads, the next slot, the caps; then a Haiku scout reads the server digest, the Grok email
digests (dxbknight-digest@agentmail.to, read only, never mark read) and the official newsrooms, and returns up to five
ranked leads. Scout verdicts parsed by the server (source_confirmed, source_unreadable, mismatch, DENIED) are on the
work order; a source_confirmed lead is built without another search. Each run writes `newsroom/scout/<stamp>.json`
(`newsroom/scout_file.py`). An unfinished run writes a row in desk/incomplete.json; the next run picks it up first.
[The work order; News scout; Scout verdicts; Server speed C to E]

**Evergreen.** News first. Evergreen (`kind:evergreen`, chip دليل, approved openers in `newsroom/names-ar.md` section 3,
never a «ليست خبرًا جديدًا» line) runs overnight (00:00 to 07:00 Dubai) and by day only when no news is buildable and the
board shows the search beyond the digest with each rejected lead. Never two evergreen in a row; none within 3 hours of
the last between 08:00 and 24:00 Dubai (the slot stays empty). Quiet hours, in order: fetch footage and warm the picture cache for the next day's dated stories, pre-build shell Reels
for news due at a known time, bank evergreen pieces. The bank is `newsroom/evergreen.md`; a used piece is marked
`used <date>`; the bank floor counts undated ready pieces. [No plain indigo ground 2; Evergreen spacing; Rules into the
gate 2, 7]

**Series and events.** «الطريق إلى GTA VI» and «الطريق إلى Ocarina» episodes open on the series intro, never reuse a shot
or audio stretch from an earlier episode (ledgers in `notes/`), and sit outside the look rotation. Famitsu weekly sales:
`famitsu-weekly.yml` every Thursday from 16:15 Dubai builds the sales_full Reel; the Thursday 18:10 Dubai check-in writes
the texts and schedules it at least an hour after Production 2's single-game Famitsu Reel. The Game Awards co-stream
(10 Dec, YouTube, his voice, OBS): countdown Reels from 3 Dec, the announcement Reel on 9 Dec with the Dubai time, clip
Reels from 06:30 Friday; plan `notes/tga-costream-plan.md`, check-in set for 3 Dec. Confirmed dates only in `newsroom/events.md`. [Series sections; Japan sales; TGA]

## 3. Arabic

- Written for Arabic readers, never translated from English. Two passes on every text: write with
  `arabic-games-film-editor`, then the `arabic-grammar-review` stage (required edits applied before anything is
  scheduled; suggestions and uncertain cases noted). On the slip lane the slip carries `grammar_review` for exactly its
  current texts (`slip.py grammar-sha`); any text change needs the stage again. Load the skills, the glossary and the
  references the text touches fresh for every batch; never from memory. [Arabic writing; Burning Sword 4]
- `arabic/house-glossary.md` overrides both outside skills; every correction Mohammad makes goes into it. Names and
  spellings: `newsroom/names-ar.md`.
- Names: games, series, characters and platforms stay in English as the publisher writes them (never in Arabic letters;
  the text check stops a game spelt in Arabic). Companies, studios, outlets and people: Arabic then the Latin in brackets
  at first mention, Arabic alone after; a name names-ar does not list is written in Latin as given (never a refusal) and
  goes to `names_to_review`. Credits use the credit ladder (section 4). [Two accounts; Names rule correction]
- Direction: every post, paragraph and on-screen visual line starts with an Arabic word. No Arabic prefix glued to a Latin
  name on screen («لجهاز Switch 2», not «لـSwitch 2»); no sign at the end of a Latin name or number on screen or in post
  text («43%» without +; New Game Plus spelt out; % on screen as «بالمئة»). Hashtag lines lead with #ألعاب
  #أخبار_الألعاب.
- House words: release verbs (a release date takes تصدر; out now متوفرة الآن or صدرت اليوم; coming to a platform قادمة
  إلى / تصل إلى + platform; announced with no date أُعلن عن; an event or product launch تُطلق; never a bare تصل for a
  date). A physical edition is «النسخة المطبوعة» only («المادية»، «ورقية» are refused). «حتى نفاد الكمية» for countable
  stock. Western digits. AED prices with the Central Bank dirham sign left of the digits.
- Plain words: write for an Arab reader who knows no English genre words; a term a casual reader would not know (ووشيا)
  fails "does it make sense". Say what a name is at first appearance («فريق ميامي هيت لكرة السلة»). Lines are one spoken
  paragraph cut into beats; the subject is named before any pronoun; no line opens on و unless it continues the line
  before. [Burning Sword 5; Say what a name is; Lines are one spoken paragraph]
- DeepL: the whole story in one piece (forward), plus stock phrases, retail terms, dates and prices in two to four
  English phrasings; pick the term an Arab reader expects, spell-check it (DeepL wrote نفاذ for نفاد), note the choice.
  The back-check confirms meaning only. DeepL output still gets the house rules. [DeepL both ways]
- Never «يتبقى» in the Ocarina countdown: «باقي N يومًا».

## 4. Reels: templates, picture, text and sound

**One Reel per story**, 9:16, 1080x1920, the same file to Instagram (Reel), X and Threads. Safe zone x 96 to 910, y 285
to 1480. End card `outro.py` (2 s, mark, platforms, jingle) on every Reel. [Full-screen format; Reel end card]

**Templates are closed and never refuse** (18 Nov; frozen until Mohammad approves a card; no new checks before 2 Dec).
The builder takes the template, adds clip, music and text in their places. Four hard stops only: a wrong fact flagged by
the brief (`fact_flag`), graphic content, unreadable text (outside the safe zone; a Latin word, digit or bracket first on
a visual line; a glued prefix; a flipping sign; the game in Arabic letters), a video that does not decode. Everything
else is a warning with an automatic fallback (qc.json `warnings`, `ladder`). The regression rule: a new or tightened
check runs on the last 20 published Reels first; any change to reel.py, render_job.py or softgate.py passes the last 10
jobs in jobs/done on render-replay before it goes live. [Templates never refuse; The 16:9 fallback, replay rule]

**Text is fixed, never refused** (Mohammad, 25 Nov 2026, after the 24 to 25 Nov outage, 16 hours with almost nothing
posted): only the four hard stops refuse. `textrules.split_sentences` never splits on a full stop inside a name or an
abbreviation (Bros., Dr., St., No., Vol., a version like 1.9.0; a full stop followed by a lowercase letter, a digit, or
a Latin word after a Latin word is not a sentence end). `textrules.fix` (render) and `slip.autofix` (slip lane) rewrap a
line or paragraph that opens on a Latin word (the break moves, «لعبة» goes before the game name, or the first Arabic
word moves to the front), shorten a headline too long for three lines at 60 px (platform and source words first, then
the news word and the game name), and fix em dashes, Arabic-Indic digits, flipping signs and hashtags on X and Threads.
The grammar review's hash is checked against the editor's text, before autofix. [Text is fixed, never refused]

**Template by story kind** (21 Nov; the slip states its kind, `templates/storykind.py` picks): numbers (sales, scores,
charts, player counts, results) take the numbers template, a figure card counting up on the game's own moving footage
after the hook; people (interview, quote, hire, departure) take the people template; debate takes hook and fact, one
view per beat, the question last; reveal, date, delay, update, deal, free release and launch take trailer. Unclear: a
trailer Reel. Review roundups of one game take `reviewscores` (numbers fetched by `templates/reviewscores.py`, never
typed; totals read within 180 minutes). Editions and bundles take `edition`. T0 takes the simplest template. Formats and
caps: `templates/formats.py` (no template a third time in a row, card-led at most two in six, four per template per
Dubai day; the gap rule may override caps only on Mohammad's word). [Audit of 21 Nov 1; Review-scores; formats]

**Picture.**
- Footage first: official trailers, gameplay, the publisher's own clips (publisher vertical cut, 4K, then 1080p; never
  social downloaders, fan uploads or YouTube downloaders). Trailer news shows that trailer, credited. Stills only when
  no motion exists; stills move smoothly (4x zoompan). Stand-in footage is named on screen («لقطات من Fortnite»).
- Picture ladder: a crop to the subject inside the 2x enlargement cap; then the showcase layout (the 16:9 trailer full
  width in the middle, headline above for the whole Reel, lines, facts and credit below, the same footage blurred and
  moving behind; never a small box in a blur of itself on other layouts); then stills; then our card. The server takes the
  showcase on its own for letterboxed footage, burnt-in text under our text, a scan with no clean stretch, three renders
  of one story in 24 hours, or a Director picture fault. [Full frame; The 16:9 fallback; No rejection]
- Shots: picked from the server's shot read (`prerender.yml` mode shots, `"shots": "auto"`) or the footage library
  (`templates/footlib.py`, `templates/assets/game-stretches.json` for curated stretches), in source order, centred
  subjects that fit a 9:16 column, faces with look room, no title cards, slates, burnt-in subtitles or text cut by the crop,
  no shot repeated or overlapping (`render_job.respread`). Every beat says what must be seen and why that frame; footage
  is illustration unless it demonstrates the claim (a trailer never proves a frame rate or player count). Something
  changes every 3 to 4 s; the news line lands on the strongest shot; the last two seconds before the end card are a
  picture. [Every beat says what must be seen; Shots that work vertically]
- Cover variety: the hook may not repeat a recent opener or cover; the server goes down story stretch, another stretch,
  another trailer, key art with motion, showcase (`render_job.hook_pick`, `templates/variety.py`). Check the cover by eye:
  a library label can be wrong (24 Nov: "lowrider crew 15.5 s" was the title card; removed).
- No plain indigo ground behind any card: card-led Reels sit on the game's moving footage or key art, dimmed and credited;
  multi-game charts put each game's art beside its row. Numbers wear their game (official logo plate, theme near the
  game's palette). The end card keeps its indigo. [No plain indigo ground; Numbers wear their game]
- Skin by genre (`storykind.skin_for`): sci-fi kit for sci-fi, cyberpunk, space, mecha; fantasy kit for RPG, fantasy,
  soulslike, MMORPG, metroidvania; house for the rest, multi-game, business, hardware and عاجل. Look rotation
  (`templates/looks.py`) keeps styles and themes from a third in a row; series episodes are outside it. No pink or magenta
  in our own colours (game footage may be pink); عاجل is crimson.
- People stories show the person: the official photo (library `templates/assets/people.json`, then a build-time
  Wikidata/Commons lookup, credited with licence) in the window with the name and role on frame 0 beside the headline,
  stepping aside at 3.5 s; no photo: a lower-third name plate, never an empty box or a game frame. A person joins the
  library the second time they are in the news; after a slip leaves someone `pending`, run `people-library.yml`. Never social crops,
  fan edits or AI likenesses. [People Reels; People photo at build time]

**Text on screen.**
- Headlines sit in the safe band, never over a face or the subject of the shot. In a collaboration story the other
  side's footage is illustration only; the game's own official trailer leads. Avoid stills with someone else's watermark
  or low-resolution art that needs upscaling.
- Headline: a hook in news words (number, stakes or surprise; never a question first, never a label), never louder than
  the source, names the game for a one-game story (the server adds «لعبة <name>» if missing), at most two lines at 100 px
  stepping down to 60 (three lines only on the live fallback), never repeating the chip word. The first frame is the grid
  tile: recognisable subject, moving, readable at grid size, clear of the top-right 140 px corner of the 3:4 window.
- Lines: full sentences or clauses (`templates/linecut.py`), up to two visual lines each, 3 to 6 per Reel, cut only at a
  sentence end or comma, never inside a name, a Latin run, a number with its unit or a phrase; not tied to shots; each up
  long enough to read (`reel.read_secs`, about 14 characters a second plus 0.5 s, 2.2 s minimum); no line before the
  headline band clears. One fact, one place: never the same fact on a card and in a line; over one of our cards a line is
  one visual line at most and clear of the card's text. Every job carries `spoken`, the story as one paragraph of 2 to 3
  sentences; the lines are that paragraph. [Story lines are sentences; Headline rules]
- Credits: every clip that is not ours carries an on-screen credit while it shows. The source line under the headline
  carries source and date only; «لقطات من ...» is its own credit lower down. The credit ladder (`templates/creditfit.py`,
  `reel.source_forms`): full form, Latin names only, short names (names-ar section 4), primary source alone, date dropped,
  then 32, 30, 28 px, then two lines; measured on the rendered pixels; never dropped or off the frame. [Credit ladder;
  People photo at build time 2]

**Sound.**
- The footage's own sound by default. Ladder (`render_job.sound_ladder`): the trailer's audio split (Cocktail Fork: music
  stem under the whole Reel, each shot's own effects back, speech dropped); its music stem alone; the franchise theme
  from the franchise library (`templates/franchise.py`, publisher's own trailers only); our bed. Our bed first only for
  stories with no game (Famitsu chart), our graphics, stills, retro (8-bit flavour), tribute (calm bed) and legal stories.
  `"music_only": true` keeps only a clean music stem or fails. [Audit of 21 Nov 2; Trailer audio split; Music-only]
- Voiced stretches: whole sentences, story lines in the pauses, a faithful Arabic subtitle when the speech is the news.
  English speech under unrelated Arabic text reads as a wrong subtitle: avoid it.
- No added effects over footage; our effects belong to our graphics only (a card entering, a counter, the end card), one
  family per Reel. Beds come from `templates/sonic.py` (our own motif; rotated through the bed ledger; evolving palettes
  on long clips). [Sound effects match the picture; Sound]

**Director.** A separate agent, never the builder, looks once at the look frames and the strip and asks two things: is
the text true (factual_error), and does it make sense to an Arab reader (unclear_text); graphic content stays a stop.
It writes `jobs/director/<job>.json` (format in `jobs/director/README.md`) and pushes it; it never runs presubmit. A
picture fault is never a send-back: the server renders the showcase once and that version posts. [Director verdict is a
file; No rejection 2]

## 5. Publishing and Publer

- **Publer is the main storyboard** (23 Nov): the only record of what is scheduled and posted (workspace "The
  Digi-Lounge", UTC+4). The board, logs and story-file statuses are notes. Before preparing any story and again before
  every submit, read Publer's scheduled posts and the last 48 hours of published posts and run
  `python3 templates/publercheck.py posts <saved lists.json> --story <id>` (exit 0 prepare, 3 replace, 1 stop). Same story
  (label `story:<job>`) or same game and news: skip it and note it on the board. A v2 replaces v1 only while v1 has not
  posted (delete v1's scheduled posts, schedule v2 at v1's minute); if v1 posted, v2 is not posted. [Publer is the source
  of truth; Publer is the main storyboard]
- **Who schedules:** Production 2 is the posting lane. Production 1 never schedules a Production 2 story; it hands it over
  on the board (Mohammad's direct order overrides for that story). Special pieces (debates, first-of-their-kind, series)
  are scheduled at least 60 minutes ahead where timing allows, with a one-line inbox note.
- **How:** the server step (`templates/serverpost.py sweep`, `server-post.yml` on every keeper tick) schedules a Reel on
  a Director pass, renders once more on a fix, and schedules anyway 20 minutes after the render with no verdict. Until
  `PUBLER_POST_KEY` exists it writes the Reel "ready": the work order shows a serverpost-ready alarm with its slot, and
  Production 2 submits it with the connector: one `submit_publer_posts` call per account (Instagram as a Reel, X,
  Threads; accounts from `lookup_publer_accounts`, never written into files), same minute, story-file texts,
  `media_url` from the public dxb-assets raw URL, then `get_publer_job_status`, then `serverpost.py scheduled <story>
  --slot <ISO>`. No ids, keys or response bodies in the repository, logs or board.
- **Labels on every post:** `kind:<news|evergreen|series|breaking>`, `tpl:<template>` (tpl:showcase for the showcase),
  `skin:`, `sound:` (trailer, franchise, bed), `genre:`, `story:<job name>`; reuse existing spellings
  (`list_publer_labels`, `newsroom/publer-labels.md`).
- **Split by platform** (Mohammad, 24 Nov 2026): X and Threads get the quick post, Instagram gets the Reel. For every
  verified news story the server renders an image card with `templates/quickpost.py` (fast_ar: official key art, a Steam
  screenshot, a curated stretch of the game or a frame of its official trailer; our chip and footer, Dubai type, never
  another outlet's logo) in seconds (`quick-post.yml`; the slip lane starts it, the server tick picks up any verified
  story without one) and schedules it on X and Threads with the story's short text (`quick_x`/`x`, `quick_threads`/
  `threads`: one or two lines, the source named, no hashtags on X, the source line on Threads), labels `kind:quick
  tpl:quick story:<job>`. Publer check as for Reels. Quick posts are spaced `quick_spacing_min` (10) among themselves,
  apart from the Reel spacing, and do not count toward the Reel buffer, the ahead alert or the gap alarm. T0: the quick
  post first, within 10 minutes of detection (dispatch `quick-post.yml` at once; the server schedules it 2 minutes out).
  The Reel goes to Instagram as before and to X and Threads as its own post at least 2 hours after the quick post, with
  the story's `reel_x` and `reel_threads` (a different first line that leads with what the video shows; without them
  Instagram only); a quick post older than 24 hours keeps the Reel off X and Threads. A story with no quick post keeps
  the Reel on all three at one time. Without `PUBLER_POST_KEY` both are written ready (alarms quickpost-ready and
  serverpost-ready with each network's time) for the connector, then `quickpost.py scheduled` / `serverpost.py
  scheduled`. Switch: `ops/cadence.json` quick_live. [Split by platform]
- **Texts:** X and Threads short (one or two lines that hook, source named, no hashtags; Threads may add a source line).
  Instagram caption: a first-line hook that differs from the headline with the game's name and the news word in its first
  five words, the full story, then `#ألعاب #أخبار_الألعاب` and two story hashtags; no links; the caption stands alone and
  names the game by the second sentence. Source follow-up: one X reply with the source link; on Instagram the source in a
  short Arabic line, no link. Post text and the Reel never carry the same text word for word. [Caption; Publishing through
  Publer 4]
- **Cadence** (`ops/cadence.json`, read through `ops/cadence.py`; nothing hard-codes spacing): 30 minutes between posts by
  day, 60 at night (00:00 to 08:00 Dubai); never more than 60 minutes without a post by day or 2 hours at night; a
  finished Reel takes the earliest free slot unless the note gives a reason (embargo, dated launch, Mohammad's hold);
  the bank floor is 6 ready evergreen pieces (buffer_target); Mohammad is pushed when fewer than 2 Reels are scheduled
  ahead in Publer (08:00 to 24:00 Dubai). Breaking news may break the spacing. Strongest non-urgent
  Reels go to Thursday 17:00 to 21:00 and Friday 19:00 to 22:00 Dubai. Round the clock: verified news posts at night too.
  [Constant coverage; Overnight cadence; cadence]
- **After each slot** check all three posts read Published. Instagram gets the full-quality file (on "download failed"
  retry the same file once before a smaller copy). Captions stop at 2200 characters on Instagram, 500 on Threads; before
  reusing a caption, check its last line starts with #ألعاب. Trial Reels for pilots only, never news. Not used: RSS
  automation, AI captions, recycling, recurring posts, spintax, AutoShare.
- **Hard stops before posting:** never a known wrong fact, graphic content, unreadable text or a broken video. Published
  posts are deleted only by Mohammad; production may delete its own scheduled, unpublished post when the gate fails, then
  requeue. A failed post is rescheduled once, then reported with Publer's reason.
- **dxb-queue publish.yml stays disabled** (`if: false`); never push `queue/**` to any branch of dxb-queue.
- **Morning digest** by 07:30 Dubai: every post since 23:00, one line each, strip path in `cards/`.

## 6. Server, runs and safety

- **Rendering:** every Reel renders on the server (`render-live.yml` on the self-hosted dxb-render-1; two render slots
  once lanes 2 and 3 are registered; a job past the free slots overflows to the GitHub runner, `render.yml`, at once,
  `templates/assets/server-lanes.json`). The runner keeps its Python packages in a cache keyed on
  `templates/requirements-render.txt`; an install step that hangs past 5 minutes is re-dispatched once; a runner render
  that fails falls back to the server queue (render-live `lane=server`), never to nothing. Read a run's step times
  before cancelling it; never call a render hung under 15 minutes; never re-run an old run, dispatch a fresh one on main. Breaking renders: `render-breaking`. The container has no Dubai font: never
  commit the fonts (EULA), never print or upload them; the runner fetches `dubai.zip` from the private dxb-fonts repo with
  `FONTS_TOKEN`. [Render runner; Server lanes]
- **Jobs:** a job file in `jobs/live/<name>.json` (format in `render_job.py`) is dispatched by name; after the render it
  moves to `jobs/done/`. The slip lane (`slip.yml`, a slip in dxb-queue `desk/slips/`) builds story file and job with no
  model step. A third render of one story, or any render after a Director PASS, needs `"rerender": {"reason", "note"}`; the fourth in 24 hours takes the
  showcase. Target one dispatch per Reel: run `textrules.py <job>` locally and prerender mode text (all text faults at
  once) before dispatching. [One render per Reel; Story slip]
- **What the server writes:** `<name>-qc.json` (verdict, warnings, ladder, sound, stage minutes), strip, sheet, dense
  strip and look frames in `cards/YYYY-MM/`, a render-times entry; a qc fail never posts. Read the strip before
  scheduling.
- **Decode and source checks** (warnings except a decode failure): full decode of every source and of the finished Reel,
  smear check, bitrate floor, block check, `lowres_ok` names the copies searched. [Damaged source footage; Source quality]
- **Keeper** (dxb-render-1 timer every 10 minutes, keeper.yml): reads Publer, writes the work order hourly from :25
  Dubai, raises one work-order alarm, no post in the last 90 minutes by day (08:00 to 24:00 Dubai), plus serverpost-ready and
  incomplete-run rows; the other checks are notes. Promises whose slot is over 3 days old are cleared. Every scheduled session prints 'overdue commitments:
  N, at risk: M' and clears alarms first. [The work order; Promises; Templates never refuse D]
- **Desk board** (dxb-queue branch desk): `desk/board.md` and `board.json` (edited together). Read it first, write your
  handoff and one run line last. It holds roles, standing orders, open handoffs, questions and the last 24 hours of run
  lines (under 30 KB), trimmed daily at 04:00 Dubai by dxb-queue `boardtrim.yml`; older lines in `desk/archive/`.
  Digest lock before dispatching watch-digest.yml. [Desk board]
- **Repos and disk:** dxb-assets is public: no tokens, Publer or Postiz ids, keys, or unreleased material in it or its
  logs. Clone it shallow, partial and sparse (`--depth 1 --filter=blob:none --sparse`); never `git log --stat` or `-p`,
  `git show` of old commits or blame (they pull every media blob); read history with `git log --format`. Delete
  downloaded footage and finished renders at the end of a run.
- **Network:** press sites, Steam, PlayStation Blog, Nintendo and their CDNs load; Google Patents, pbs.twimg.com and
  news.xbox.com refuse automated reads (use a press article with the same image); YouTube needs a sign-in, so no
  yt-dlp logins or third-party downloaders. Say when a fact is corroborated by search rather than read from the primary.
- **Skills:** `games-news-editor` for triage, ranking and scheduling; `reel-director` for briefs, builds and reviews;
  the Arabic skills above. Repo rules win on numbers and wording.
- **Delegation:** the main session keeps story choice, verification, the Arabic, judging frames and everything said to
  Mohammad; repeated work goes to cheaper helpers with the task cards in `newsroom/delegation.md`.
- **Pilots off the live path:** HyperFrames inserts (pinned 0.8.143; numbers and character cards, fallback to numgfx),
  the motion kit, web-style motion and the design pass are live only as their memos say; other pilots stay on branches
  until Mohammad approves. Parked until he reopens them: server publishing beyond the ready flow, quick bites, tiers,
  Stories, DeepL on the server, other channels.
