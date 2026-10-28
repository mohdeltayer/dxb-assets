# Working on DXB-KNIGHT

**Rules in force at a glance: `STYLE.md`** (one page, 13 Oct 2026). This file
is the full dated history; when a rule changes, update both in the same commit.

## What the account is for

DXB-KNIGHT covers games in general and the Gulf in particular. The model
is Genki on Japan or Daniel Ahmed on China and Asia: a regional specialism
that runs through a general feed, not a filter every post must pass.

The regional side is the reason the account exists: shed light on what is
happening in the Gulf games scene, the studios, events, publishers,
investment, pricing and players that the wider press rarely covers, and be
one of the few outlets that puts that information out there whether or not
it trends. Global stories are covered on their merits, without forcing a
Gulf angle onto them.

In practice the Gulf is sprinkled in, and grows gradually (Mohammad,
24 Sep 2026): the more the feed leans on the region, the less the wider
audience engages, so general games coverage leads and builds the audience
the regional stories then reach.
- Rank sweeps on general interest first. Include a Gulf story when it is
  strong enough to interest a general games reader, and frame it as a
  games story first (the game, the studio, the money), the region second.
- Aim for a regional story now and then, not a quota. When a sweep has
  none worth posting, say so; do not invent one.
- Gulf stories are sourced from the region (regional press, companies,
  official bodies, Arabic sources) wherever possible, not only from
  Western outlets rewriting them.
- Global stories carry no Gulf angle unless the region is actually part of
  the story.

## Desks and the release window (Mohammad, 28 Oct 2026, adv-20261028-three-desks)

This session is the operations desk and does news only: watch, verify, write
(both Arabic skills, the pre-publish gate), render through job files, the
director QA, schedule and post in Publer, slot checks, pinned and source
comments, answer-the-why, the inbox cards that come with the news (previews,
story decisions, heads-ups), the morning digest and the evergreen bank.

It does not build. No changes to tools, templates, render code, checks,
profiles, workflows, the server's services, or the technical parts of these
instructions, and no work on build cards (desk "build"): the dispatcher routes
those to the nightly build desk, which follows BUILD.md. When ops finds a bug
in released code it writes a build card (the failure, the job, the log line)
and works around it inside its own lane (another template, a simpler job, the
fallback card), never by patching code.

Release window: 04:00 Dubai (00:00Z), once a day. Nothing that changes the
system reaches main outside it, except a security fix or a T0 instruction from
Mohammad. Ops's working data is not a release item and keeps flowing as now:
story files, render job files (`jobs/render/`), footage under `live/`, the
format, style, bed and ground ledgers, watch-seen, digests-covered, the
evergreen bank, the inbox. Ops reads the release note at the 05:30 Dubai
checkup and may revert a release merge on its own when a slot is at risk (one
line in dxb-queue `ops/change-log.md` and an fyi card); it never patches one.
Until the build desk's scheduled task exists, ops performs the 04:00 merge of
items Mohammad has approved, merge only.

How the render chain, its checks and the tools work, and the build and pilot
history that used to sit in this file: `ops/build/system-history.md`. Retired
platforms and publishing routes (Postiz, Business Suite, TikTok, Snapchat,
the YouTube Shorts runs, Instagram still cards): `notes/standing-history.md`.
Both were moved word for word on the release that trimmed this file; nothing
was deleted.

## Growth: content, not tricks (Mohammad, 26 Sep 2026)

After a one-week audit of @DXBNIN (Grok, 19 to 26 Sep; figures spot-checked
against X), these are agreed:

- DXB-KNIGHT is a voice from the region talking outward about the whole
  games slate, in the Genki mould. The Gulf side is small because the
  market is small; that is expected, not a problem to fix. The Arabic
  account is the one aimed at the region.
- Grow through the quality of the content and how it is presented. No
  piggybacking: never post a card under someone else's post, no
  follow/unfollow games, no reply bait. A reply under another account is
  fine when it adds something real (a number, a comparison, first-hand
  detail), is plain text, and Mohammad chooses to post it.
- Hero posts (the FFXIV-on-Switch-2 shape: his setup, native video, one
  verdict) go out when they are ready, not on a schedule. Longer capture
  is the next step (the Switch 2 clip limit is 30 seconds).
- Analysis cards go out while the topic is live, not as overnight filler.
- Re-audit weekly with the same Grok prompt and compare.

Open, not agreed: spacing of scheduled cards. The audit found the 03:00 to
08:00 Dubai clusters weakest (median 21 views, 8 posts, 25 to 26 Sep).

## Two accounts (from 24 Sep 2026)

**Resumed (Mohammad, 26 Sep 2026).** The hold set on 24 Sep is lifted.
Every story DXB-KNIGHT posts also goes out on The Digital Lounge, and the
Arabic side runs at a higher cadence on top of that: the Arabic games
space is thin and the account is small, so volume is how it gets found.
Sweeps therefore shortlist more for Arabic than for English, including
stories DXB-KNIGHT passes on. Same story, not same text: each account's
post is written for its own readers.

Balance shifts toward Arabic (Mohammad, 27 Sep 2026): Digital Lounge
posts more, DXB-KNIGHT posts less, in line with the growth points above.
In sweeps that means:
- DXB-KNIGHT gets fewer, stronger posts: his takes, hero posts, analysis
  cards while the topic is live, and fast posts only for stories a general
  games reader would stop for. Minor news, calendars and roundups are not
  shortlisted for it.
- Digital Lounge takes everything DXB-KNIGHT posts plus the minor news,
  release calendars, Game Pass and store lists and regional items.
- When in doubt, a story goes Arabic-only rather than both.
- Digital Lounge first, Instagram above all (Mohammad, 10 Oct 2026: "focus
  on the digital [lounge], both the Instagram and the X, especially the
  Instagram part, as it's getting a lot of views"). Effort goes to Digital
  Lounge Reels before DXB-KNIGHT cards: each review slot builds as many
  verified Digital Lounge stories as the window holds, and Reel quality
  (cover tile, footage, sound, readable lines) comes before speed.
- DXB-KNIGHT on hold, option B (Mohammad, 10 Oct 2026, from 11 Oct; the
  two posts queued for 10 Oct evening went out as planned): no routine
  DXB-KNIGHT production. Sweeps and review slots shortlist for Digital
  Lounge only: no fast posts, no analysis cards, no evening slot planning,
  and no "ask for his take" step for DXB-KNIGHT. He can still post a hero
  piece or a take when he has one; build it when he brings it. The account,
  its rules below and its Postiz connection stay as they are, so the hold
  lifts without new work. The time goes to more Digital Lounge Reels.
- The exception runs the other way for opinion (Mohammad, 27 Sep 2026):
  DXB-KNIGHT is his personal account, Digital Lounge and Instagram are
  news. A piece built on his take (analysis, a history angle, a verdict)
  is DXB-KNIGHT only, even when Digital Lounge already ran the news.
- Timing follows each account's readers (Mohammad, 27 Sep 2026):
  DXB-KNIGHT writes for an international, largely American audience, so
  its slots aim at Europe's afternoon and the US morning (about 17:00 to
  21:00 Dubai, 09:00 to 13:00 US Eastern); Digital Lounge and Instagram
  run in Gulf waking hours.
  Day and evening split (Mohammad, 28 Sep 2026, from X Active times for
  the last 28 days; `analytics/dxb-knight.md`): Digital Lounge works the
  daytime, 08:00 to 21:00 Dubai; DXB-KNIGHT works the evening, 19:00 to
  23:00 Dubai (11:00 to 15:00 US Eastern), the day's main post around
  20:00 to 21:00, strongest pieces Wednesday to Friday, and Friday may
  run to about 01:00. Breaking news still goes when it breaks. Recheck
  against the scout's weekly packs.
- Each account keeps its own cadence (Mohammad, 27 Sep 2026). DXB-KNIGHT
  never waits for Digital Lounge or the other way round: two or three
  posts across the accounts at the same minute is fine, even on different
  topics. The only pairing is Digital Lounge X with Digital Lounge
  Instagram, which post each story together.

Digital Lounge is meant to become the Arabic games news source that does
not exist yet (Mohammad, 27 Sep 2026), an official-feeling news cycle for
Arabic readers; DXB-KNIGHT's Gulf posts showed the appetite is there. So
its cadence is aggressive: every verified story that fits the scope goes
out on it, the same morning, minutes apart when several are ready, and
sweeps look for more Arabic-only items (store and price news, release
dates, updates, regional and official announcements) rather than fewer.

Digital Lounge posts round the clock (Mohammad, 12 Oct 2026: "I know
there are peak hours but having some news day and date around the clock
will attract more followers and will distinguish it in comparison with
other Arabic outlets"). A verified story he has said go to goes out as soon
as it is built, night included, rather than waiting for 08:00; peak hours
(08:00 to 21:00 Dubai, from 28 Sep) still get the strongest pieces. Propose
times earliest first. The breaking lane's auto-go hours below are
unchanged.

Timing differs too (Mohammad, 27 Sep 2026): Arabic games coverage is
thin, so Digital Lounge does not follow DXB-KNIGHT's spacing. Its posts
can run close together and go out as soon as they are ready in waking
hours for the Gulf, rather than being held for a slot or spread hours
apart.

Both languages are prepared together (Mohammad, 26 Sep 2026): every
shortlisted story comes with its English and Arabic post text and card
side by side, and he approves them as a pair. The Digital Lounge took X
Premium on 26 Sep 2026, so long posts are fine on both accounts. Postiz
caches a channel's profile (name, picture, Premium) from when it was
connected: after a change on X it rejects long posts with "post is too
long" until Mohammad reconnects the channel. The id stayed the same when
he did.

- DXB-KNIGHT (@DXBNIN), English: Mohammad's personal voice, in the Genki
  or Daniel Ahmed mould. General games news and takes, Gulf sprinkled in.
- The Digital Lounge, Arabic: a full Arabic games outlet, "the regional
  IGN" and Mohammad's first entrance into that market. It covers the whole
  games slate for Arabic readers, not only regional news, in an outlet
  voice (more news, more volume, no first person). Regional stories lead
  more often here than on DXB-KNIGHT because its readers are in the region.

Arabic posts are written for Arabic readers, never translated from the
English post. Names in Arabic posts (Mohammad, 26 Sep 2026):
- Games, series, characters and platforms stay in English only, as the
  publisher writes them: The Witcher 3: Wild Hunt Remastered, Dr. Eggman,
  PS5, Xbox Series X|S, Nintendo Switch 2, Steam.
- Companies, studios, outlets and people carry both forms, Arabic then
  the Latin in brackets, at the first mention: "أعلنت شركة نينتيندو
  (Nintendo) أن", ريميدي (Remedy), بيور إكس بوكس (Pure Xbox), تاكايوكي
  كاواساكي (Takayuki Kawasaki). Later mentions use the Arabic alone.
- Cards follow the same rule where there is room and keep the Arabic
  alone where there is not: `fast_ar` drops the bracket itself when the
  source would crowd the footer.
- Reels carry the Latin too (Mohammad, 4 Oct 2026: "add the English for
  companies because some are hard to read"): the first on-screen mention
  of a company, studio or outlet in a Reel's headline or lines takes the
  bracket, «جاجكس (Jagex)», «بوليفوني ديجيتال (Polyphony Digital)». Later
  mentions use the Arabic alone. Set the break so the bracket stays on the
  line with its name, and keep the visual line starting with an Arabic word.

Arabic writing (Mohammad, 27 Sep 2026): two passes on every Arabic post.
1. Write with the `arabic-games-film-editor` skill (his upload): meaning,
   attribution chains, hedges, technical terms.
2. Check with the `arabic-writing` skill (ahmeddabak/claude-arabic-writing,
   MIT, commit 7001831): grammar, hamza, ة/ه, ى/ي, agreement, collocations,
   punctuation and its machine-translation smell test.
Grammar review (Mohammad, 1 Oct 2026): the check in pass 2 now runs as the
`arabic-grammar-review` stage on the finished text. It takes نحو and صرف from
`perfect-arabic` (alialsaudi/perfect-arabic, MIT, commit 78fdade, a summary of
النحو الوافي), spelling and punctuation from `arabic-writing`'s
orthography.md, and keeps style apart: the smell test and collocations are
suggestions only. It returns `corrected_text`, `required_edits` (original,
proposed, class, category, explanation, a reference only when the file was
opened), `optional_style_suggestions` and `uncertain_cases`. Smallest fix
only; correct text comes back unchanged; valid alternatives, absent
diacritics and digits are never errors; problems inside a quotation are
flagged, not rewritten. Both outside skills are community-maintained, not
authorities: lines found wrong are in the stage's
`references/known-issues.md`. Required edits are applied before he sees the
pair; suggestions and uncertain cases go to him with the drafts. Tested on
1 Oct against 39 posts (`notes/arabic-review-test-2026-10-01.md`). It never
queues: posting still needs his times and his "go".
Resources first, every time (Mohammad, 29 Sep 2026, after a review found
grammar slips in that morning's posts): before writing any Arabic, in every
batch and every session, load both skills fresh, read the glossary and the
`arabic-writing` references the text touches (grammar.md for agreement and
numbers, conventions.md for prices and dates), and only then write. Never
work from memory of the rules. Live posts are not changed afterwards unless
he asks.
Both live in `.claude/skills/`. The house glossary `arabic/house-glossary.md`
overrides both (names above, no first person, Western digits). Add every
correction he makes to the glossary. DeepL stays the alternative when needed; it
translates only (no Arabic rewriting) and its output still needs the
house rules applied.
DeepL both ways, and its alternatives (Mohammad, 15 Oct 2026, after the
Ocarina foil cover post said ما دام المخزون متوفرًا where Arab retail says
حتى نفاد الكمية: "DeepL usually has multiple suggestions so please go through
them and pick the right words"). The back-check (Arabic to English) confirms
meaning only, and it passed that phrase as "whilst stocks last". So every
batch also runs a forward pass. The whole story goes to DeepL in one piece,
not sentence by sentence (Mohammad, 15 Oct 2026: "Add the full story in DeepL
and not sentence by sentence"; a proper translation needs the context), and
its Arabic is read against ours as a whole post. On top of that, the stock
phrases, product and retail terms, dates and prices are each sent in English
phrased two to four ways ("while supplies last", "while stocks last", "until
sold out", "in limited quantities"). The DeepL connector returns one Arabic
rendering per request and DeepL Write has no Arabic, so the phrasings are the
alternatives. Compare them with our wording, pick the term an Arab reader
expects (countable products take الكمية, bulk goods المخزون), then spell-check
the pick: DeepL itself wrote نفاذ for نفاد twice on 15 Oct. The choice and the
alternatives go in the draft notes. Test of both methods on 20 glossary terms:
`notes/translation-engine-test-2026-10-15.md` (whole stories read better as one
piece but did not pick better terms, and added a misspelled Ubisoft and an
Arabic-lettered Nintendo Switch 2, so its names are checked against the house rules).

Text direction (Mohammad, 27 Sep 2026): X and Instagram take a post's
direction from its first word, so every Arabic post, paragraph and line
starts with an Arabic word, never an English name or a hashtag in Latin.
Write "تصل DYNASTY WARRIORS 3", not "DYNASTY WARRIORS 3 تصل", and lead the
hashtag line with #ألعاب #أخبار_الألعاب. Read every paragraph's first
word before queuing.

The two brands never share a mark; their palettes are kin
(Mohammad, 26 Sep 2026). What tells a Digital Lounge card apart is the
indigo ground, the play mark, Dubai type and the right-to-left footer.
No pink or magenta anywhere on it: to a Gulf reader it reads as girlish
or for kids (Mohammad, 26 Sep 2026). That rule is for the brand's own
colours only, its themes, chips, wave lines, footer and end card; game
footage and official art may be pink and stay in (Mohammad, 4 Oct 2026).

Settled 26 Sep 2026: the name is Digital Lounge, ديجيتال لاونج (display
name "ديجيتال لاونج | أخبار الألعاب"), and it stays; renaming on the spot
is what held it back before, so changes wait for data. Scope is games
only: news, hardware, the business, the Gulf and Arab scene, esports when
big or regional. No AI, phones or general tech, and film or TV only for a
game adaptation gamers are talking about; mixing topics scattered its
audience before. Each brand has its own name, mark and fonts;
the layouts, chips and workflow are shared and restyled per brand (the
Arabic fast card is the same frame, mirrored right to left). Every
shortlisted story in a sweep gets a lane per account (for example: fast on
both; card on DXB-KNIGHT only; Digital Lounge only). The Digital Lounge is
@the_digilounge on X, Instagram and Threads, all three posted through
Publer (see "Publishing through Publer"). YouTube runs
the original-material lane below; TikTok is dropped (1 Oct) and Snapchat
paused (9 Oct). The earlier Postiz integrations, TikTok, Snapchat, Instagram
Stories and YouTube Shorts rules are in `notes/standing-history.md`.
YouTube lane for original material (advisor trial, 17 Oct 2026, agreed with
Mohammad): original material only (Famitsu weekly, numbers Reels, list pieces,
the Gulf price roundup, retro and his handson), never trailer Reels; a YouTube
cut under 35 seconds; the title opens on an Arabic word with the game or the
news word in its first five words and passes the grammar stage; judged after
two weeks against the 140-view baseline in `newsroom/experiments.md` (full
memo in the history file).
Threads (Mohammad, 4 Oct and 10 Oct 2026): every Digital Lounge story goes to
Threads at the same time as its X and Instagram posts, carrying the short X
text and the same Reel; no hashtags; 500 characters a post.

Full-screen format for everything (Mohammad, 1 Oct 2026, after the Ocarina
of Time post): every Digital Lounge story is now one 9:16 video built with
`templates/reel.py`, and the same file goes to X, Instagram, TikTok and
YouTube. Empty space is gone: no footer, no panel, no blurred fill.
- The footage fills the frame and keeps its own sound. Cut only stretches
  without speech (check word timings with faster-whisper), and run the
  shots in their source order: jumping back and forth through a trailer
  made its music jump (the Zelda v3 complaint).
  One continuous stretch is the standard (Mohammad, 6 Oct 2026, from the
  Fandom and GameSpot Reels he sent: "match the images with the footage"):
  a single stretch of one official trailer, picture and its own sound
  together, with our headline and lines on top as now. The 9:16 crop aims
  at the subject of each scene: `reel.autofocus(file, start, dur)` finds
  the cuts and returns a per-scene focus to pass as the shot's focus
  (a manual `(offset, focus)` entry overrides one scene). The stretch has
  no burnt-in subtitles, title cards, logo slate or black tail under our
  lines; Galactic Racer v4 and Monster Hunter Rise v3 were the first.
- Top, for about 3.5 seconds: chip, a large headline, and a credit line
  (accent rule, source · date) on a soft band. The first frame is the grid
  tile.
- Shots that work vertically (Mohammad, 12 Oct 2026: "focus on the main
  event... select things that make sense for someone who watches it
  vertically"). Some Reels looked right while others showed the side of a
  character, or half a first-person view (a gun and an empty half frame).
  Pick shots whose subject fits a 9:16 column: a face, a character or
  creature standing centred, a vehicle head-on, a close-up of the thing
  the line is about. Skip wide two-shots, subjects at the frame's edge and
  first-person gameplay with the weapon off to one side; when only those
  exist, use stills or our own graphics. On the shot sheet, judge every
  frame as the cropped vertical a phone shows, not the 16:9 source.
- Nothing graphic in a Reel (Mohammad, 12 Oct 2026: "an open account for
  everyone"). Any game may be covered, mature-rated included, but the
  footage carries no blood, gore, dismemberment, finishing kills or sexual
  content. For a violent game, cut to story beats, characters, places and
  some shooting without the extreme moments (a Resident Evil Reel can show
  a gun raised and a creature in shadow, not the wound). Check every frame
  of the shot sheet and the finished strip for it; if a trailer has no
  clean stretch, use its other trailers, official stills or our graphics.
- Stand-in footage is named on screen (Mohammad, 13 Oct 2026, review
  priority 3): when the footage is not of the story's subject (Fortnite
  footage over Epic's unshown Disney shooter, Dragon Quest VII over Horii's
  AI game), the Reel carries a small credit, «لقطات من Fortnite»:
  `reel(..., credits=[(first_shot, last_shot, text)])`, under the safe top
  (or above the safe bottom when the lines sit at the top).
- Wrapped lines are checked (13 Oct 2026, review priority 4): reel.py stops
  when any visual line of the headline, a story line or a credit opens on a
  Latin word, a digit or a bracket (`rtl_starts`). On 13 Oct three headlines
  wrapped that way and were caught only by eye.
  A sign at the end of a Latin name or a number flips to the far side in
  right-to-left text (22 and 23 Oct: a card read «43%+», a headline «+New
  Game»), and the check does not catch it: spell it out or drop the sign
  (New Game Plus; «43%» with no plus) on screen and in the post text.
  An Arabic prefix written straight onto a Latin name flips too (24 Oct: ARMS
  v3 drew «لـSwitch 2» as «Switch 2لـ»): on screen write «لجهاز Switch 2»,
  «وسلسلة Zelda» or put a space after the prefix. `rtl_starts` now stops on it
  (`reel.GLUED`); post text is unaffected.
  The container has no Dubai font, so wraps are only caught on the runner:
  keep a headline line under about 26 characters at 60 when it carries a
  Latin name.
- Say what a name is (Mohammad, 2 Oct 2026, after the Miami HEAT Reel):
  many viewers only watch, so the on-screen text identifies any name an
  Arab gamer may not know, at its first appearance (headline or first
  line): «فريق ميامي هيت لكرة السلة», not «ميامي هيت» alone; the same in
  the X post and the caption. Teams, YouTubers, regulators, small studios
  and outlets get their label; Sony, Nintendo and the like do not.
- Then the story itself, not a summary, cut into short sentences that run
  one after another low in the frame: white Dubai Bold 70 with an indigo
  outline and soft shadow, no plate (the Netflix MENA look), right-aligned
  so it does not read as dialogue. One or two lines, three at most; set
  breaks by hand so a phrase never splits (لا stays with its verb). Each
  sentence sits on the shot it describes. Above a game's lower-third UI
  (note panels and the like) the sentence moves to the top.
- Everything stays in the Reels safe zone; `reel.py` stops on a line or
  price that would leave it.
- Headline, lines and pace (Mohammad, 3 Oct 2026, after the Steam Deck
  Reel went by too fast; until his own voice carries the Reels):
  - The headline is a hook: the most surprising fact or the stakes, in
    news words, not a label («اسم رمزي يشعل…» is a label). Never louder
    than the source: a rumour still reads as one.
  - The lines tell the story with its facts (who, what, the number, when,
    what is not confirmed), not slogans. Four to six lines is normal.
  - Every line stays up long enough to read once: `reel.read_secs`, about
    14 characters a second plus half a second, 2.2 s at least. `reel.py`
    checks before it encodes and stops on a line that is too fast.
  - Short of footage, add related official footage rather than speeding
    the lines up: the game's other trailers, the series, the platform or
    the company's own clips.
  - Letterboxed clips are cropped to the picture automatically, and a clip
    left with under 700 rows stops the render (`lowres_ok=True` only when
    there is no other copy). On 3 Oct the Steam Deck Reel went out with
    black bands from letterboxed Valve clips.
  - Trailer audio stays (Mohammad, 3 Oct 2026, after a batch of eight
    went out muted with the background music under them: "none of these
    has actual trailer audio"). Never mute footage to swap in a bed. When
    a trailer has dialogue, run one continuous stretch of its own audio
    under the cuts (so the music does not jump) and either keep a stretch
    without speech, subtitle what is said, or strip the voices and keep
    its music and effects. The bed stays for stills and our own graphics.
    In code: `reel(..., track=(file, start))` runs one stretch of that
    file's sound under the whole cut; `track=(file, start, 'music')` strips
    the voices first (demucs two-stem, cached as `<name>-music.wav` in
    uploads; set `DEMUCS_PY` to a Python with demucs installed). Lines are
    also checked against the safe zone before the encode.
    The sound has to be good, not just the trailer's (Mohammad, 6 Oct
    2026, after the Monster Hunter Rise Reel ran a montage of repeated
    roars and the Supermassive Reel carried odd effects through a
    voice-stripped track): use a stretch of the trailer's own music, or a
    part of the trailer where its music and effects sound right. A stretch
    of only roars, slates or effects is not usable, and a voice-stripped
    track that leaves artefacts is not either. When no stretch is good,
    use our own sound: a `sonic.py` bed whose flavour matches the story's
    tone (or a new flavour made for it), with the jingle on the end card.
    Listen-check the chosen stretch before the render: name what plays
    under the cut (music, effects, voices) in the draft notes.
    Music, not effects (Mohammad, 6 Oct 2026, after the Galactic Racer
    Reel ran a gameplay stretch thick with engines and impacts: "the star
    wars one sounds noisy"): the stretch has to be the trailer's music
    leading, such as a score passage or the logo fanfare, not gameplay audio
    where effects sit on top of it. Measure it before choosing (tonal
    music against noisy effects, and voices) and send him the stretch when
    unsure; if every stretch is effects-heavy, use our bed.
    Voices are fine (Mohammad, 6 Oct 2026: "it's okay to feature that
    part of the clip with voices"; replaced 21 Oct 2026 by "No speech under
    story lines", see "Framing and speech"): a stretch where dialogue runs over the
    score can play as it is. Prefer that to stripping the voices, which
    leaves artefacts; `'music'` mode is a last resort.
  - Pick shot times from `templates/seekmap.py` (frames labelled with the
    seek time reel.py uses), never from a sheet labelled with timestamps:
    Steam trailer downloads start their picture 2 to 3 seconds in, and on
    3 Oct shots picked that way landed on title cards. Then look at the
    finished Reel's frames before showing it.
  - Check before rendering, draft before the real encode (Mohammad,
    4 Oct 2026, option 3: fewer re-renders rather than more agents or
    sessions; everything stays in this session). On 3 Oct Nagoshi and
    Micron each rendered four times over title cards, pink and a busy HUD.
    1. `reel.shotsheet(shots, sheet.jpg)`: first, middle and last frame of
       every shot in one sheet, about 20 s; it flags near-black frames
       (title cards on black, fades). Fix the shot list until the sheet is
       clean. Pink in the footage is no longer flagged (4 Oct 2026: the
       no-pink rule covers our colours, not the games).
    2. `reel(..., draft=True)`: ultrafast, low quality, no end card, written
       as <name>-draft.mp4, about 2.5 minutes against 7 to 10 for the real
       encode. `reel.strip(video, strip.jpg)` lays its frames out.
    3. The real render once the draft is clean, then `strip` again.
- Creative brief and formats (Mohammad, 10 Oct 2026, adapted from an
  outside "creative director" prompt; its gameplay styles, fast beat cuts,
  regrading of publisher footage, comedy style and added music were left
  out). Before the shot sheet, every Reel gets a brief in its draft
  notes: the angle and hook (and which kind of hook: number, question or
  surprise), the format and its opening beat, the cover frame, what plays
  under it (trailer music, voices or our bed), the one shot the key fact
  lands on, and the total seconds before the end card (advisor, 14 Oct
  2026: a sixth line; 12 to 20 s is the target). Formats (`templates/formats.py`): trailer (one continuous stretch, the
  default), numbers (our own graphics), comparison (two labelled states with
  hard cuts, `reel(..., cut=True)`: prices by country, specs, before and
  after), quote (the speaker's line leads), explainer (the source's own
  figures) and handson (his gameplay: natural colours, text after the
  action, numbered tips). No more than two Reels in a row share a format
  (`formats.py check`, then `add` after the render), and each shortlisted
  story names its format. On trailer Reels a strong shot may breathe a
  second or two with no line after the headline; reading pace, line limits
  and the headline on the first frame stay as they are. The line carrying
  the number or the news lands on the most striking shot.
- Templates and scenarios (Mohammad, 14 Oct 2026, 04:52 Dubai, after the
  Shogun 2 Reel: "I like the style of showing part clip and then adding an
  info graph or a screen but this started appearing nearly for every reel.
  In some cases I would like to see the video while reading the news on
  screen. In some cases the information is shown twice... How about making
  various reel templates and scenarios and which templates can be used with
  the type of news. Plus when adding a video we need to think very clearly
  what is on screen and how we convey the information instead of just a
  random clip."). The format ledger confirmed it: of the ten Reels before
  his message, eight were clip-then-card or card-only. From 14 Oct:
  - One fact, one place. A fact lives on a card or in a line, never both.
    Over a card the line is a frame of at most one visual line («هذا ما
    يدفعه اللاعب في الخليج», «الخصم ينتهي الثلاثاء»), or there is no line
    and the card holds the beat alone for its reading time. On the Shogun 2
    Reel the card said 149 AED and 149 SR and the line under it said the
    same again; never again.
  - The template is chosen per story from `templates/formats.py`
    (`TEMPLATES`, and `NEWS_MAP` from the kind of news to the templates
    that fit it), named in the brief, and the ledger keeps consecutive
    Reels apart as before. The set:
    - `trailer`: official footage runs the whole Reel with its own sound;
      the lines ride on it and the news is read while the video plays; no
      card at all. The headline carries the key fact. For launches, dates,
      reveals, updates and anything with a trailer that shows the news.
    - `split`: footage runs the whole Reel and a slim fact strip (date,
      price, platforms; two or three items at most) stays pinned low in
      the safe zone while the lines narrate on the picture above it. The
      strip is the card; the lines never repeat it. For a launch with a
      price, a dated event, a sale with a deadline. New in `reel.py`
      (`strip=[(label, value), ...]`), first used 14 Oct.
    - `clipcard`: footage for the hook and the story, one card at the key
      beat (the price table, the date, the figure), then back to footage.
      One card, not three; the card holds the beat alone or under a frame
      line. For store prices across regions, a figure with a comparison.
    - `numbers`: our graphics on the living ground for the whole Reel,
      only when there is no footage worth showing: sales charts, financial
      results, rankings. The lines are the story; the charts are the data.
    - `comparison`, `quote`, `explainer`, `handson`, `retro`: as before.
      A quote Reel still shows what the speaker talked about once the
      quote has landed, not their portrait for the whole Reel.
  - Every shot has a reason. The brief's shot list says, per line, what
    the viewer sees and why it is that frame («السطر عن سعر النسخة الكاملة:
    اللقطة هي شاشة محتويات النسخة»; «السطر عن الكاميرا الجديدة: لقطة
    تُظهر الكاميرا تدور حول المقاتل»). A shot with no reason beyond "it is
    from the trailer" is replaced by one that shows the line, by the
    publisher's own screen of the thing, or by our graphic for it. The
    shot sheet is judged against those reasons, not only for black frames
    and crops.
  - Footage first. When a trailer, gameplay or the publisher's own video
    exists, `trailer` or `split` comes before any card template; cards are
    for facts the footage cannot show (prices, dates, numbers), and even
    then `split` keeps the picture running.
  - The Sifu Reel of 14 Oct 05:00 Dubai went out under the old shape (card
    plus a line reading it) because it was already in Postiz when he wrote.
  - Two families (advisor, 14 Oct 2026, 12:30 Dubai): footage-led (`trailer`,
    `split`, `clipcard`, `handson`, and `comparison`) and card-led (`numbers`,
    `explainer`, `quote`, `retro`). Besides "no third in a row", card-led
    Reels are at most one in three over the last six: `formats.py check`
    refuses a third card-led Reel in a window of six (`FAMILIES`, `WINDOW`,
    `CARD_MAX`), and `pick` moves to the kind's next template. `NEWS_MAP` is
    unchanged. Over a split strip a story line is at most two visual lines
    (`reel.py` stops on a third). Applies from the next Reel after Valve
    Index; the four that followed it that morning (numbers, clipcard,
    explainer, split) went out before the rule and sit in the window.
- Grid tile (advisor, 19 Oct 2026, agreed with Mohammad, from his profile
  screenshot: 189.7K views in 30 days, the grid judged appealing and
  readable). 1. Instagram's Reels icon covers the top right of every grid
  tile, where the chip sat: the chip row is 60 px lower (`reel.CHIP_DROP`,
  `HEAD_TOP`), the headline and the persistent mark with it, and
  `head_layer` stops when any chip or text pixel falls in the 140 px square
  at the top right of the first frame's 3:4 window (x 940 to 1080, y 240 to
  380; `grid_corner_clear`). First used on the Kojima Edgerunners Reel of
  19 Oct; check each first frame cropped to 3:4. 2. The first frame never
  shows a trailer's slate, title card or publisher text (the Rockstar tile
  showed "GAMES PRESENTS" behind the headline): `shotsheet` reads the first
  shot's first frame with tesseract (`_words`; `apt-get install -y
  tesseract-ocr` in a new container, it warns when missing) and flags any
  text with the first clean seek time after it (`first_clean`); move the
  shot's start there. 3. Nothing else on the cover changes: headline, band,
  colour variety and the Ocarina series card stay.
- Grid tile headlines (advisor, 24 Oct 2026, approved by Mohammad in the inbox
  08:14Z). From his profile screenshot: the headline was a thin strip, about a
  fifteenth of the tile, read like a caption and faded on bright frames; the
  BioWare debate tile was a mostly empty purple frame with a small question.
  1. Designed covers, once the Publer custom-cover test works: a 3:4 cover per
     Reel, the headline about twice today's size cut to 3 to 5 words, on a soft
     dark band, the game's key image or the person's face behind it, the chip in
     its usual place. The full headline stays in the first frame and the caption.
  2. Until covers work, the first frame: the headline about 1.5 times larger
     (`reel.HEAD_SIZE` 100, was 66), at most two short lines (`HEAD_LINES`),
     never below `HEAD_MIN` 72 (only a full game name that cannot be cut, such
     as Phantom Blade Zero, shrinks it that far; any other headline that does
     not fit is cut to fewer words; `head_layer` stops), inside the safe zone and the grid
     corner rule; the soft dark band behind it is stronger (`HEAD_BAND` 225, was
     190) with a wider glow behind the type, so pale skies and white scenes hold.
     The person box moves down to clear the taller head (`PERSON_BOX` y 750,
     h 490). Applies from ARMS v4 (24 Oct).
     A break set by hand in the headline («\n») is now kept (`ig_ar._wrap`),
     as story lines already did; the two-line balancing runs only on headlines
     without one and never splits before a Latin name. At 100 px the old
     wrapping put «Final Fantasy XIV» and «Phantom Blade Zero» alone at the
     start of line 2 and the text check refused them (24 Oct).
  3. Debate pieces and other card-led Reels: the cover or first frame shows a
     strong recognisable image (a character or the game's key art) with the
     question large; never a mostly empty ground with small text.
  4. Kept: the layout, chip top right and headline below in the same place on
     every tile.
  5. The director QA judges every first frame (and cover) cropped to 3:4 at
     phone grid size: can the headline be read without zooming?
- Hook rule for every Reel (advisor, 24 Oct 2026, approved by Mohammad in the
  inbox 09:02Z). Case: the BioWare debate Reel, 122 views, average watch 4 s,
  67% skip, steady drop from 0 to 31 s, opened on a question over an empty
  purple frame.
  1. The first frame stops the scroll, on every Reel (news, numbers, people,
     debate, evergreen): something recognisable (a famous character, not the
     studio logo; a face; the product; the game's most iconic shot), moving,
     with the most striking fact in a few news words, never louder than the
     source («30 عامًا من Mass Effect وDragon Age... انتهت»). Name what people
     know first (the game or character before the studio). A question never
     opens a Reel; in a debate piece it comes after the hook and the fact. Read
     at grid size (grid tile memo).
  2. A new reason to keep watching every few seconds: each beat a new strong
     image of a different recognisable subject plus one new fact or view; no
     beat repeats the previous image; a payoff in the second half (the number,
     the twist, the answer, the strongest shot).
  3. No length cap: the story decides the length; cut only beats that add
     nothing (the 12 to 20 s target is a guide, not a cap).
  4. The debate recipe is corrected on the advisor's board (hook, fact, views,
     question last); every other recipe keeps its structure with rule 1 for its
     opening beat.
  5. The Tuesday audit reports skip rate and average watch time per Reel (Publer
     insights once they sync, or Instagram) next to template and opening type,
     and names the week's weakest openings.
  6. Director QA adds: would someone scrolling stop on this first frame? If
     not, fix it before scheduling. First applied to the next-week releases list
     of 24 Oct (v2: «أربع ألعاب تصدر الأسبوع المقبل» over Phantom Blade Zero's
     hero instead of the label «أبرز إصدارات الأسبوع المقبل»).
- Beat sheets (advisor, 24 Oct 2026, approved by Mohammad 09:08Z). Every brief
  starts from its family's beat sheet on the advisor board «Beat sheets: nine
  story families»; FIXED beats keep their structure, FROM THE STORY beats come
  from the news; timings are a guide, the story decides the length. Across all
  families: the hook slot is a recognisable face or character, a passionate
  fanbase, or a surprising fact or deadline, never a question, a label or the
  studio before the game; a WHERE AND HOW MUCH frame for product, announcement,
  release and deals stories (every platform as a logo on screen, the price
  beside each, AED when local or USD marked, the date; unknowns said, «لم
  يُعلن السعر بعد»; held 2 to 3 s); one focus at a time; a new image and fact
  every few seconds; a payoff in the second half; event kits prepared before
  predictable events (The Game Awards, Directs, State of Play, big launches).
  Families: 1 product showcase (hero with name, two or three close-ups, features
  one at a time, WHERE AND HOW MUCH, hero again); 2 announcement (iconic shot and
  striking fact, trailer plays with no text, what was revealed, the surprise
  detail, WHERE AND HOW MUCH, strongest shot); 3 numbers (iconic shot and figure
  in words, figure counts up, split one bar at a time, context, payoff for
  players, source line); 4 people (face and what they did, photo box alone, the
  story, a detail or quote, their best-known work); 5 setback (the game and the
  fact, what changed on a strip, the stated reason attributed, what is unchanged
  or what to do, calm close); 6 leak or rumour (game and claim with the
  certainty chip, who says it, the details claimed, what is not confirmed, never
  louder than the source); 7 release (best gameplay and out now, what you do in
  it, reviews or players if strong, WHERE AND HOW MUCH with Arabic support, best
  closing shot); 8 debate (character and striking fact, the fact, one view per
  beat on a new image, the question last; options to Mohammad first); 9 fun or
  oddity (the oddity, setup, twist, reaction, light close). The brief names its
  family.
- Design pass after the beat sheets (advisor, 24 Oct 2026, approved by Mohammad
  09:15Z). Graphics change once; identity (indigo, play mark, Dubai, chip
  position, end card) and the 100 px headline stay.
  1. WHERE AND HOW MUCH frame as a HyperFrames insert (limited-use memo, falls
     back to the current strip): platform logos in a row (two rows past four) on
     equal plates, the price under each in Dubai Bold, the date on one line
     beneath; dirham sign left of local prices, dollars marked, one price for all
     shown once centred; unknowns stated; «بالعربية» badge when it applies; logos
     press in one after another (under 0.5 s each), then hold still 2 to 3 s;
     footage keeps moving behind, dimmed.
  2. Platform logo library in `templates/assets/platforms/` with sources noted,
     official single-colour (white) marks from the holders' press or brand pages:
     PS5, PS4, Xbox Series X|S, Xbox One, Nintendo Switch 2, Nintendo Switch,
     Steam, Epic Games Store, PC (Windows), Mac, App Store, Google Play, Xbox Game
     Pass, PlayStation Plus, Nintendo Switch Online, Meta Quest; used only to
     identify platforms.
  3. Chips about 1.3 times their size in the same place (grid-corner rule
     holds); split strip values a step larger, labels stay smaller; story lines
     unchanged.
  4. Motion kit placed by family: photo box (people), count-up and XP-bar split
     (numbers), chip press (every Reel), unlock banner (records), play-triangle
     transition (card to card), quiet UI blips never over speech; one or two kit
     moments per Reel at most.
  5. Three samples on real recent stories (a product showcase, a release with the
     frame, a people story) go to Mohammad's inbox as one card with the videos,
     beside the published versions, with render times. Roll-out to live Reels
     only after his approval; the breaking profile keeps the simplest version.
     Built in idle time; news comes first.
  6. Rolled out (Mohammad, 24 Oct 2026, inbox 19:21Z: "Roll out"). Live from
     the merge of `rollout/design-pass` the same evening. Every Reel: chips at
     type 50 (75 px, `reel.CHIP_SIZE`), the strip 172 px tall with values at 64,
     56, 48 or 44 and columns sized to their content. Opt-in per job, on the
     runner (`templates/designpass.py`): `"frame": {"shot", "offset", "secs"
     (3 to 6), "data": {"platforms": [{"logo", "prices": [[region, value]]}],
     "price_all", "date", "note", "arabic"}}` (a value is a string, `["aed",
     "239"]` for the dirham sign, or `{"unknown": ...}`) and `"kit": ["chip" |
     "photobox"]` (photobox needs `person[0]` opening at 0 and opens on frame 0
     with no wipe); `"kit_quiet": [[t0, t1]]` keeps blips out of voiced
     seconds, `"blips": false` turns them off. The frame counts as a kit moment,
     two at most; it sits after the headline, clear of lines, credits and the
     person window, and the strip is off while it shows. Breaking profile and
     عاجل skip both. Each piece has 300 s; on failure reel.py's own layer is
     laid back and the story never waits (`design_pass` in render-times.json).
     HyperFrames 0.8.143 installs only for a job that needs it. Parity on the
     Elden Ring v3 job: 689 frames and 22.988 s as published, audio identical;
     only the chip, headline position, strip values and lines (12 px higher)
     differ. The first three live Reels with a frame or kit moment go to
     Mohammad as previews before scheduling, then the rolling queue.
- Strips and sheets go into git (advisor, 14 Oct 2026): every final render
  commits its `<name>-strip.jpg` (the finished Reel's frames) and
  `<name>-sheet.jpg` (the shot sheet) to `cards/YYYY-MM/` beside the mp4, in
  the same ledger commit. Applies from the GT7 Spec IV Reel of 14 Oct; the
  strips of valve-index-sunset, total-war-shogun-2-complete-edition and
  ps-store-three-sony-games-missing were committed that day too.
- Autofocus (14 Oct 2026) centres the 9:16 window on the subject of each scene and
  pans with it; the shot sheet draws the window, and `render_job.py focus`
  writes the judged focus into the job so the runner keeps the framing.
- `edition` template (advisor, 14 Oct 2026), for special and collector's
  editions, bundles, limited consoles, accessories and tier contents: a 3.5 s
  trailer hook with the headline, then the contents one at a time on the
  numgfx living ground as publisher press-render cut-outs (hero item first and
  largest), each drifting in from the right with a soft shadow, name in Dubai
  Bold 64 and an optional one-line note in Medium 44 body colour, 2.5 to 3 s
  each, four to six items; then one composition frame of every item with the
  price strip pinned low (price, date, where; strip only, never in a line);
  2 s of footage under the closing line; end card. Trailer music runs under
  the whole Reel; gold theme for premium editions, otherwise the story's
  theme; chip رسمي or السعر. In reel.py a `products=[(png, name, note)]` shot
  type on the numgfx ground with drift and shadow, and the composition frame;
  cut-outs from press kits with backgrounds removed in the build step; the
  fallback is the publisher's photos unmasked, else the story stays on
  `split`. In `formats.py` it joins FORMATS and NEWS_MAP (kind `edition`:
  `['edition', 'split']`), card-led family. First draft to Mohammad before use.
- Best-practice pass (advisor, 14 Oct 2026; applies from the next Reel after
  each lands, 1 to 4 first):
  1. Hook first: the footage moves from frame one under the chip and the
     headline; the credit line (accent rule, source · date) enters at 2 s
     (`reel.CREDIT_AT`, its own layer); the headline is written as a hook (a
     number, a question or the surprise), never a label.
  2. Persistent mark: the play mark at 48 px, 50% opacity, top left inside
     the safe zone on the chip row's empty end, through the whole Reel
     (`reel.mark_layer`; `MARK_PERSIST`, `MARK_PX`, `MARK_ALPHA`).
  3. End card trimmed to 2 s (`outro.CARD`, was 3.6): the notes, chord and
     name all land by 1.6 s and the jingle's ring fades over the last half
     second; the last story line runs to the end of the clip and may land
     over the mark through the crossfade.
  4. Length target 12 to 20 s of story before the end card (`reel.LENGTH`):
     four lines is the normal case, six only when the story needs them.
     reel() prints `length_note` at the check step, and the brief states
     the total seconds.
  5. The opening beat varies by template (`formats.OPENERS`, printed by
     `formats.py check`): quote on the quote, numbers on the number alone,
     edition on the hero item, trailer on the strongest moving shot, and
     so on. The brief names it.
  6. Captions: the game's name and the news word (صدرت، تأجيل، السعر، تقرير
     and the like) sit in the first five words, in the Arabic caption and
     in any English line (the caption task card in `newsroom/delegation.md`).
  7. Weekly views next to the template in the format ledger: Mohammad sends
     the Instagram numbers Tuesday morning before the audit; `formats.py
     views <name> <n>` records them and `formats.py templates` gives the
     median per template (`analytics/reel-views.md`).
- Advisor memos, 14 Oct 2026 evening session (template audit onward;
  approved by Mohammad, recorded 14 Oct 2026):
  A. Template audit fixes. 1. A `price` story with more than three facts
  is never `split`: the brief states the item count and `formats.pick(kind,
  facts=)` reads it. 2. No template more than four times in one day, any
  family (`formats.DAY_MAX`; the ledger now dates each entry), on top of
  the family cap and the no-third-in-a-row rule. 3. The format ledger's
  `views` column, filled weekly from his Instagram numbers (Tuesday
  morning before the audit; `analytics/reel-views.md`). 4. `handson` and
  `edition` are the named exceptions to the 12 to 20 s target
  (`formats.LENGTH_EXEMPT`); every other template states its total
  seconds in the brief.
  B. Decisions. 5. New templates `stills` (three or four official images
  filling 9:16, lines on them, the bed under; footage-led; built on
  `reel.stills_clips`) and `list` (N items at 2 to 2.5 s each on their own
  art, rank or date on a small plate, progress cue "n/N", one line per
  item at most, mosaic cover, closing frame of all tiles; card-led). Game
  Pass waves, leaving-soon, line-ups, awards, top fives, show recaps and
  weekly releases map to `list`. 6. `NEWS_MAP['report']` is
  `['trailer', 'clipcard']`: a card only when the claim has a figure or a
  table. 7. `comparison` has no split-frame option: hard cuts only, and a
  figure sits in the state's label plate, never in a line. 8. `edition`
  goes ahead as specified on 14 Oct; first draft to Mohammad.
  C. New news kinds, batch 1. 9. `NEWS_MAP`: delay [split, trailer];
  preorder [split]; free [split]; shutdown [split, explainer]; reviews
  [clipcard, numbers]; awards [list]; esports [split, numbers];
  controversy [quote, clipcard]; recap [list]; weekly [list]; adaptation
  [trailer, stills]; mods [trailer, with the stand-in credit naming the
  creator, and the creator's permission when the footage is theirs];
  hardware_price [comparison]. 10. Kind `arabic` [split]: strip items
  الواجهة · الترجمة · الدبلجة as they apply, and the chip «بالعربية» in
  bright indigo beside the news chip, placed like a country chip
  (`fast_ar.COUNTRIES`). 11. `tribute`, a variant of stills
  (`reel(..., tribute=True)`): cold theme, wave lines off, no chip, name
  and dates as the headline, lines in body grey, slow dissolves instead
  of push-ins, a calm bed (neon_c), the end card with the mark and no
  jingle (`outro.append(..., quiet=True)`). 12. عاجل is a skin on any
  template, not a kind: crimson and the breaking bed, applied from the
  chip in reel.py. 13. A closing question line only on stories readers
  argue about (`formats.QUESTION_ALLOWED`), never on launches or prices.
  D. Stills and attention. 14. Stills are the last resort: before a
  stills Reel the build step looks for motion in this order: older
  trailers of the game or series, the platform's or publisher's own clips
  and dev diaries, the store page's video, his capture of the game, the
  source page recorded as video, our graphics in motion. Stand-in footage
  is credited as now. 15. A stills Reel is cut, not panned: subject
  cut-outs on a parallax ground where the art allows
  (`stills_clips(..., cutout=True)`, the backdrop removed in the build
  step), otherwise a slow push-in of 2 to 4% per image and a hard cut on
  the bed's beat (`cut=True`); three or four images, 3 s each, 12 to 14 s
  in all, four lines; neighbouring images differ in kind (art, screen,
  face). 16. Every Reel changes on screen every 3 to 4 s (a cut, a line,
  a strip, a number; `reel.pace_note` warns at the check step) and names
  a turn in the brief with the second it lands on. Lines enter on cuts.
  Word-by-word reveal only on the key line (`reel(..., reveal=<line>)`).
  17. The last two seconds before the end card are a picture, never a
  card (`reel.close_note` warns). 18. Formats to spec when the news
  brings them: trailer breakdown, timeline, map (labels, no borders),
  interview clip, versus, by the numbers, countdown. Weekly series with a
  fixed sting and chip colour: Gulf prices (day to be set), morning recap
  «ماذا فاتك», Sunday releases «هذا الأسبوع», Famitsu.
  E. New news kinds, batch 2. 19. `NEWS_MAP`: layoffs [quote, stills];
  acquisition [explainer]; results [numbers]; players [split]; policy
  [explainer]; leaving [list]; crossover [trailer]; expansion [split];
  beta [split]; crossplay [comparison]; performance [comparison]; remake
  [comparison, trailer]; rating_leak [clipcard, re-checked before
  queuing]; firmware [explainer]; format [explainer]; cast [quote];
  soundtrack [edition, split]; community_record [handson, permission and
  on-screen credit required]; watch_guide [split, times in Gulf time];
  breach [explainer, the عاجل skin only on official confirmation, never
  methods or third-party claims]. 20. Judgement rules, not templates
  (`formats.JUDGEMENT`): bans and censorship carry the official decision
  and the publisher's response only, no commentary, chip رسمي or تقرير;
  regional investment and government programmes take the business
  templates, the country chip only when the country is the story. 21. The
  scenario for every kind (cover, where the facts live, key shot and
  reason, sound) is on the advisor canvas "Digital Lounge Reel
  Templates", board "Scenarios by news kind"; a brief for a story of that
  kind starts from it.
- Rendering (ops use; the chain itself belongs to the build desk). A Reel
  renders on the GitHub runner from a job file: commit
  `jobs/render/<name>.json` (format and keys in `templates/render_job.py`),
  after `render_job.py check` (timeline, reading and pace) and
  `render_job.py focus` (the focus judged on the shot sheet). The runner
  commits the mp4, strip, sheet and dense strip to `cards/YYYY-MM/`, uploads
  the Reel to Publer and deletes the job file; a failed job keeps its file and
  its log names the check that stopped it (read the step times before calling
  a run hung; never under 15 minutes). Fix the job, not the code, and
  recommit. Breaking stories use the breaking profile. Timings, caches,
  safeguards and the runner's setup: `ops/build/system-history.md`.
- Review of the Xbox Nano Reel, the first under the hook band (advisor,
  14 Oct 2026):
  1. Ten seconds on one still (0 to 10 s) broke the 3 to 4 s change rule.
     Before accepting a still for a hardware story, run the motion-search
     order (the publisher's clip, the store page's video, our graphics in
     motion); when a still is all there is, cut to a second angle at 3.5 s,
     the angle the line names (the pocket for the pocket line). `reel.py`
     now stops on a pace warning unless `pace_ok=True` is passed with the
     reason in the brief.
  2. When a card is up on a split Reel, the strip hides for the card's
     duration (reel.py does this) or the card absorbs its items as its last
     rows; never card, framing line and strip stacked. A card's attribution
     line is at least 40 px (`numgfx.MIN_TEXT`) or moves to the credit line.
  3. A line about a store page gets the store page as its shot (the
     pre-order page cropped to the markets row for the Gulf line), not the
     hero still again: `templates/pageshot.py <url> <out.png> --clip
     x,y,w,h` (headless Chromium) makes the still.
  4. Ledger entries record what went out: a split with a card is logged as
     `clipcard`, so the day and family caps read it correctly (the Nano
     entry was corrected).
  5. For the breaking profile, the hook band and the persistent mark are
     confirmed from a phone screenshot of the first 2 s on the next
     breaking Reel, since the strip cannot show a 48 px mark; the publish
     check asks Mohammad for it.
- Numbers Reels have a living ground (Mohammad, 12 Oct 2026: once the
  title went, the charts sat on "a big purple background" and the sales
  Reels felt stale). Our graphics are drawn on a transparent canvas
  (`numgfx.canvas()`) and `numgfx.shots([(png, secs)], theme, name)` lays
  them over the indigo ground with faint wave lines in the theme's colours
  drifting slowly sideways for the whole Reel: a little stronger at the top
  and bottom, faint behind the chart and the story lines, one clock across
  the slides so crossfades never double the lines. Never a flat ground
  behind a chart again. First sample: the Resident Evil box office Reel
  (`resident-evil-film-record-reel-v2.mp4`, not posted).
- Windows hold clips, grounds vary (Mohammad, 14 Oct 2026, 09:50 Dubai,
  after the GBA Nintendo Classics Reel: "Some reels have images like the nso
  one. For next one if we can small clips in the same place of the image
  windows it would've been interesting. The background colors for info
  graphs text is mostly the same with the same subtle animation I think we
  might need to add variety without loosing the ability to read.").
  - A framed window on our ground (a game screen, box art, a product shot)
    plays a short clip when footage exists, with its own sound off and the
    bed under it, instead of a still: `numgfx.window(clip, box, start,
    secs)` lays the footage inside the frame, pixel-crisp at integer scale
    for retro screens. Stills stay only where no footage reaches us through
    an allowed route (the GBA Reel: Nintendo's clip was on X and YouTube only).
  - The living ground has styles that rotate like the band styles
    (`numgfx.GROUNDS`, ledger `templates/assets/ground-ledger.json`): the
    waves as before, a soft theme glow, a diagonal two-tone wash, a fine
    dotted grid, angled or denser waves, and a blurred official still of the
    story behind the chart (dimmed as on the Instagram cards). No two
    consecutive numbers Reels share a ground, and every ground keeps the
    text readable: the chart's text area is checked for contrast (the ground
    behind the type stays at or below the indigo's brightness) before the
    render.
- Numbers wear their game (advisor, 20 Oct 2026; Mohammad on the GTA 6
  pre-orders Reel: "looks a bit generic, adding a logo or a theme close to
  the game is more attractive"):
  1. A numbers card about one game sits on that game's official key art or
     a trailer frame, blurred and dimmed (the `still` ground), never the
     plain indigo. `numgfx.shots(..., still=<art>)` now always takes the
     `still` ground when an image is given, ahead of the rotation; the
     contrast check behind the type still runs and dims harder when needed.
  2. The game's official logo sits on a plate above the main figure
     (`numgfx.put_logo(canvas, logo_png, box=LOGO_BOX, theme=)`: the logo
     centred on a plate cut to the box, indigo at 78%, edge in the theme
     accent; the default box, y 690 to 890, clears the headline). The first
     frame, the grid tile, shows logo, figure and headline together.
  3. The accent takes the theme nearest the game's own palette (spectacle
     for GTA's sunsets, cold for sci-fi, playful for Nintendo, emerald and
     so on); gold stays for multi-game charts and milestones. Our colours
     never go pink; the game art behind may.
  4. Footage first still holds for numbers stories: when the game has
     official footage the template is `clipcard` (trailer hook, one card
     with the figure, back to footage), not `numbers`
     (`formats.pick(kind, footage=True)` swaps it). `numbers` alone is for
     stories with no footage: Famitsu-style charts, company results,
     multi-game rankings.
  5. Multi-game charts keep the rotating living ground and put each game's
     art or box shot beside its row, as `sales_full` already does.
- Text cut by the crop and moving grounds (advisor, 20 Oct 2026). The shot
  sheet flags any printed text, logo or subtitle whose box crosses the 9:16
  window's edge (`cut-text`): drop the shot for a nearby one, or, when the text
  is the point, rebuild it as a vertical card in the game's style. Card-led
  templates sit on the game's own footage, dimmed and slightly blurred, never
  the flat indigo, and nothing is static in the first 3 s. Game skins (sci-fi,
  fantasy, house with footage behind) are a pilot owned by the build desk; no
  live Reel uses a kit until Mohammad's verdict (`ops/build/system-history.md`).
- Damaged source footage (advisor, 21 Oct 2026). The Battlefield 1 turns 10
  Reel (published 21 Oct 01:45Z) carried decode damage from 5.3 to 6.3 s, the
  planes-over-the-battlefield shot: a blocky white and black smear of the
  previous cockpit shot over the new scene, healing a second later. Our text
  was clean, so it came in with the footage (the IGN 1080p download, damaged
  at that scene cut). The shot sheet's single seeked frame skipped it; the
  strip showed it in two frames and it was missed. Mohammad deleted the live
  posts; v2 was re-rendered from fresh copies and queued as the same story
  with the same text (not an update: the error was ours). Corrections #8.
  1. Every source file, on download: decoded in full once (`ffmpeg -v error
     -i <file> -f null -`). Any error line: download once more (and remove
     its picture-pass cache clips); a second damaged copy means another copy
     or dropping the shots from the damaged stretch. Never build shots from a
     file that reports errors. "decode clean" per source in the draft notes.
  2. Every finished Reel, before queuing: the same full decode on the final
     mp4, and the blocky-smear flag (`templates/decodecheck.py`: long
     straight edges in the picture area, read clear of our headline, lines
     and strip, jumping above 12 and to four times the footage within 1.5 s
     either side for 8 frames or more; it reads the v1 Reel at 5.33 to 6.10 s
     and passes clean Reels; pixel-art bars, low-poly art and burnt-in title
     cards still flag, and a person who has looked waives the stretch with
     `block_ok` and the reason). The same flag runs on each shot's source
     stretch before the render. `decodecheck.py <mp4> --strip out.jpg` runs
     both and writes a 4-frames-a-second strip, so the first second of every
     shot, where this damage shows, is looked at.
  3. The runner: `render_job.py run` does 1 on every fetched source and 2 on
     the source stretches and the output, and fails the job before anything
     is committed; it also writes `<name>-dense.jpg` (the 4 fps strip),
     committed beside the strip and sheet.
- Source quality checks (Mohammad, 24 Oct 2026, inbox 16:26Z, after the ARMS
  check). The ARMS soundtrack Reel (v4) broke up at 12.2 to 12.9 s: Nintendo's
  only copy is 1280x720 at about 2.6 Mbps, enlarged 2.7x, and its own
  compression blocks became big squares in a fast camera swing. The decode and
  smear checks look for broken video, not a valid but weak source, and the 2x
  cap was waived with `lowres_ok` with no record of which better copies were
  looked for. Three checks, in `reel.quality_gate` (run by `render_job.py
  check` and by reel() before the montage) and on the shot sheet:
  1. Bitrate floor: a source under 5 Mbps at 1080p or 3 Mbps at 720p is
     flagged `lowbit` in the check output and on the sheet; a flag, not a stop.
     Other sizes scale on (height / 1080) ** 1.26 (0.63 in pixels, from the two
     approved points), held at 5 Mbps above 1080p (a larger source is enlarged
     less), lower for a source narrower than 16:9 by the share of its width the
     9:16 window keeps, and lower under 30 fps by fps / 30
     (`decodecheck.bitrate_floor`). On 24 Oct: Steam 1080p trailers 4.7 to 6.0
     Mbps pass (24 fps floor 4.0), IGN 1440p30 5.3 and 4K60 15 pass, IGN's Ys
     VIII 1080p at 3.8 and every Nintendo store 720p trailer (2.5 to 2.6) flag.
  2. Block check: every footage shot enlarged past 2x (`reel.MAX_ZOOM`) has its
     source stretch read at its own size for the 8x8 block-edge ratio (luma
     step across 8-pixel boundaries over the step elsewhere,
     `decodecheck.block_ratio`); the peak of a 0.2 s rolling mean above 1.5
     (`decodecheck.BLOCK_MAX`) is `blocky` on the sheet and stops the render
     unless the job waives that shot: `"blocky_ok": [[file, start, reason]]`,
     start being the shot's own start, after someone has looked at the frames.
     ARMS v4: the hoop swing read median 1.41, peak 1.56 (stops); its other
     shots peaked 1.15 to 1.45; Steam and IGN 1080p stretches read 1.05 to
     1.31. About 1 s per 3 s shot of 720p; shots at 2x or less are not read.
  3. `lowres_ok` names the copies checked: a string ("IGN, Nintendo store,
     publisher press site, Steam: none above 720p"), a list of the sources, or
     `{"searched": [...], "result": "..."}`; a bare true stops the render with
     the reason to write, in job files and in reel(), montage, cached_shot and
     edition on the container alike. The reason is printed in the check output.
  `block_ok` stays the waiver for the smear check (decode damage).
- Framing and speech (advisor, 21 Oct 2026, agreed with Mohammad).
  1. Faces, no side-on centring: autofocus also measures each face's turn
     (yaw) on the frames it already samples, with a face-landmark model on CPU
     (MediaPipe face landmarker). Front and three-quarter faces are preferred;
     a face in full profile is flagged "profile" on the shot sheet. A profile
     shot that is still the right shot is framed with look room: the face off
     centre, the empty space on the side the character looks towards; if the
     9:16 window cannot give that room, the shot is replaced. `render_job.py
     focus` writes the judged focus into the job file as now, so the runner
     keeps the framing.
  2. (Superseded the same evening by "Director review, and voiced clips
     allowed" below; kept as history.) No speech under story lines (replaces "Voices are fine", 6 Oct). Reason
     (Mohammad, 21 Oct): with English speech playing and Arabic text on screen,
     viewers read the text as a subtitle of the speech, and when it does not
     match it feels wrong. The audio under the headline and story lines is
     music (score, logo fanfare, music-led passages) with no audible speech or
     narration. The stretch is chosen with the transcriber: no words inside it
     (faster-whisper word timings, checked before the render), and the track's
     start and its fade before the end card fall in pauses. Speech only when
     the speech is the news (a director's statement, a quote Reel, an interview
     clip): then the on-screen Arabic is a faithful translation of exactly what
     is said, timed to it, in subtitle position, with no separate story line
     over it. No music-only stretch in the trailer: another official trailer or
     clip of the game, then our bed (`track='bed'`); demucs voice stripping is
     the last resort and only with no audible artefacts. One continuous stretch
     per Reel whenever trailer audio is used; never each shot's own sound when
     it carries voices.
  3. Checks before queuing: the shot sheet shows the "profile" flags, each
     fixed or justified in the brief; the finished Reel's audio is transcribed,
     and any English word under a story line, or a word cut off at the start,
     the end or a cut, stops the post (except a quote or interview Reel under
     2). The draft notes name what plays under the cut, as now, plus "speech:
     none" or "speech: quote, subtitled".
  4. First applied 21 Oct about 17:10Z: three Reels already queued carried
     narration under their lines (Escape from Playtime 17:45Z, Stellaris 19:15Z,
     Switch Sports Resort 20:15Z) and were re-rendered on our bed; Escape from
     Playtime's scheduled posts were pulled from Postiz first. DON'T NOD (17:15Z)
     also carried speech but went out as queued: it was due in under three
     minutes, and a re-render would have taken it past 24 hours from its first
     report. Live posts stay as they are unless Mohammad asks.
- Director review, and voiced clips allowed (advisor, 21 Oct 2026, agreed with
  Mohammad; supersedes point 2 of "Framing and speech"). Our bed is not the
  default. Mohammad: "I don't want every video to have our music, it's ok to
  use voiced clips but cut into something coherent."
  1. Audio order, decided per Reel by the director: a. the trailer's own
     sound, music-led or voiced, as one continuous stretch; b. our bed only
     when the footage has no usable sound (silent clips, stills, our graphics)
     or no coherent stretch exists. Re-renders made onto our bed under the
     earlier rule and not yet published (Escape from Playtime v2, Stellaris v2,
     Switch Sports Resort v3) are reviewed by the director, and the trailer
     sound comes back where a coherent stretch exists.
  2. Voiced stretches are coherent, not cut: whole sentences only; the stretch
     starts at a sentence start or in a pause and ends after a sentence ends
     (faster-whisper word timings); no word cut at a shot change, since the
     audio runs as one stretch under the cuts. Story lines appear in the pauses
     between sentences, not on top of speech. When the speech is the news (a
     statement, a quote, a narrator stating the feature the story is about),
     it gets a faithful Arabic subtitle in subtitle position, timed to the
     words, and no separate story line runs at the same time. The headline may
     sit over speech in the first 3.5 s.
  3. The director step: a separate agent, after the draft render and before
     the real encode (on the runner lane, after the render and before queuing),
     watches the Reel as a viewer: the strip at 4 frames a second, the
     transcript with sentence boundaries, the face-direction flags and the
     crop-edge text flags. It writes an edit decision in the draft notes:
     audio (trailer music / voiced, which sentences / our bed, and why); lines
     (where each lands, pause or shot, any to re-time); shots (any to replace
     or reframe: profile, cut text, weak shot); verdict (pass, or the list of
     fixes). The build applies the fixes and the director looks again. It may
     send a Reel back twice; after that it passes with a note, or the story
     moves to a simpler template. Task card: "Director" in
     `newsroom/delegation.md`.
  4. Limit: the director judges audio from the transcript and measurements
     (speech against music, loudness), not by ear; when unsure how a passage
     feels, it says so in the preview note to Mohammad.
  5. Unchanged from the 21 Oct memo: face direction and look room, the
     crop-edge text flag, the decode and blockiness checks. The pre-queue
     transcription stays, read against the director's decision: speech the
     director placed in pauses or subtitled passes (`speech_director` in the
     draft spec); speech under a story line still stops the post.
  6. First applied 21 Oct about 19:10Z: Stellaris v2 (19:15Z) was due in
     minutes and went out on our bed; Escape from Playtime and Switch Sports
     Resort went to the director; BioWare (19:45Z, breaking) stayed on our
     bed, since its footage crosses two trailers and no one stretch fits both.
     The director restored trailer music on both (Escape from Playtime v3 on the
     reveal trailer's score, Switch Sports Resort v4 on the overview montage),
     but the session stalled after a container restart and both went out at
     20:45Z and 21:45Z in their bed versions; v3 and v4 stay in `cards/`.
- Trailer sound is the default (advisor, 23 Oct 2026, from Mohammad: "A lot of
  news has the channel tune instead of the trailer... the background music
  should be used in certain news pieces like Famitsu but not nearly
  everything"). On 22 Oct, FFXIV, Once Human and Capcom went out on our bed
  although a trailer was available. This tightens "Director review, and voiced
  clips allowed" and relaxes the 6 Oct "Music, not effects" line.
  1. Our bed belongs only to: Famitsu and other sales charts, numbers Reels and
     our own graphics; stills Reels and footage with no sound of its own; retro
     and on-this-day pieces (retro flavour) and tribute (calm bed); breaking
     news only when its footage is silent or unusable. Every other Reel with
     official footage uses the footage's own sound.
  2. Keeping the trailer sound on a footage Reel: narration or dialogue is not
     a reason to drop it. Build around it: whole sentences only, a faithful
     Arabic subtitle when the speech carries the news, story lines in the
     pauses (director rule, 21 Oct). Prefer a music-led stretch when one
     exists; when narration runs through the whole trailer, take the stretch
     where the speech is complete and relevant, and subtitle it. Effects-led
     gameplay audio is fine when it is clean and not harsh; only harsh or
     noisy effects (constant explosions, engines, screams) rule a stretch out.
     When one trailer has no usable stretch, try the game's other official
     trailers and clips before our bed.
  3. Our bed on a footage Reel needs a reason, and only after step 2 fails: the
     story file names each trailer checked and why it was unusable, and the
     director signs it off. The preview to Mohammad says "our bed" in its first
     line, so he can object before it posts.
  4. The Tuesday audit counts Reels by sound (trailer, voiced and subtitled, our
     bed); our bed on a footage Reel should be the rare exception.
  5. Posts published on 22 Oct stay as they are. The two Reels still scheduled
     that night (Dragon Ball Xenoverse 3, PlayStation Pulse) already ran on
     trailer music, so nothing was re-rendered.
- Trailer news shows the trailer (advisor, 26 Oct 2026, approved by Mohammad;
  his words, 07:00 Dubai: people want to see the trailer itself). When the news
  is a trailer or teaser:
  1. The Reel shows that trailer. No stand-in footage from other games or older
     trailers in its place. When there is no collab or new trailer, only key art,
     the Reel uses the official art with motion, not another game's footage.
  2. A credit on screen while it plays («المصدر: الحساب الرسمي لـ Overwatch»),
     plus the caption credit as usual.
  3. The official file: the publisher's YouTube, press site, Steam, or the
     official X post's video. If the only copy is on X, fetch that official
     video; no reposts or fan uploads.
  4. When 16:9 does not sit well in 9:16 (text cut, wide shots, a crop above 2x
     on a weak source): the trailer-showcase layout, allowed for trailer news
     only: the trailer at its own width in the middle, our headline above, the
     credit and key facts below, over a dimmed, blurred, moving copy of the same
     trailer.
  5. The trailer's own sound (audio split rules apply).
  6. The director check asks: trailer news, is it the actual trailer?
  First case: Stellar Blade's NieR:Automata vignette for the Switch 2 edition
  (26 Oct). The Overwatch x Stellar Blade EVE Protocol Reel, built on both games'
  launch trailers, was pulled to drafts before its 09:00 Dubai slot and rebuilt
  on the key art.
- People stories show the person (advisor, 23 Oct 2026, from Mohammad). The
  Shigeru Miyamoto honour Reel ran Super Mario clips and music (good) but never
  showed Miyamoto, so viewers could not tell the story was about him.
  1. Applies to any story where a person is the news: awards and honours,
     appointments and departures, interviews and quotes, retirements,
     tributes, a creator's new project.
  2. The person's official photo appears with the line that names them within
     the first 3 to 4 seconds: a framed window over the running footage with a
     name plate giving the role («شيغيرو مياموتو، مبتكر Mario وZelda»), then
     back to full footage; the footage's own sound keeps playing. An optional
     second appearance at the closing line when the Reel runs long. The cover
     (the first frame until custom covers work) shows the person and the game
     together. The quote template keeps its own speaker card.
  3. Photo sources, in order: the company's press site or press kit; the
     awarding body's or organiser's own release photo; a properly licensed
     image (Wikimedia Commons with its licence), credited on screen. Never
     social-media crops, fan edits or AI-made likenesses. No usable photo: the
     brief says so and the Reel uses the person's best-known work with the
     name plate.
  4. The brief lists each person in the story with their photo source; the
     director checks the face is visible, not cropped, and readable at phone
     size.
  In code: `reel(..., person=[(photo, name, role, t0, t1, {'focus': (x, y),
  'credit': text})])`, or `"person"` in a job file (the photo fetched like
  footage). `reel.person_layer` draws the window (`PERSON_BOX`, 460x540, right
  of centre between the credit line and the story lines, edged in the theme
  accent) with the plate in its lower part (name Bold, role Medium in body
  colour, an optional «الصورة: ...» credit); every plate line opens on an
  Arabic word, and a photo enlarged past 2x into the window stops the render.
  Live posts (the Miyamoto Reel) stay as they are unless Mohammad asks.
- Director QA format (advisor, 23 Oct 2026, agreed with Mohammad). Adds structure
  to the director step (21 Oct). The format is borrowed from the video-qa skill
  in universal-video-skills (MIT) as reference only; that pack is not loaded as
  a skill, since it is about generating AI video and our rules use official
  footage only.
  1. Per shot, a short checklist with a frame as evidence: for every shot in the
     draft, one frame (the shot's middle, plus its first frame if a line enters
     there), checked for framing (subject visible in the 9:16 crop, no side-on
     face without look room, no cut text at the edges), text (line readable at
     phone size, inside the safe zone, first word Arabic, on screen long
     enough), picture (no decode damage or blockiness, no title card or slate,
     nothing graphic), sound (what plays under this shot: music, voiced and
     subtitled, or our bed; no word cut at the cut) and reason (the shot shows
     what its line says).
  2. Written verdict: each shot PASS, or FIX with the one change needed; the
     Reel PASS, or the list of fixes. After fixes, the director looks again at
     the changed shots only. Saved in the story file's draft notes as a compact
     table (shot, time, verdict, note); the frames are the strip or sheet
     already committed, so no extra files.
  3. Reel-level checks, once per Reel: first frame and cover readable as a grid
     tile; total length against the template target; something changes on
     screen every 3 to 4 seconds; the last two seconds before the end card are
     a picture; the sound choice matches the trailer-sound rule (23 Oct), our
     bed only with its stated reason.
  4. Limits: two rounds of fixes at most, then pass with a note or move the
     story to a simpler template, as now. The director judges sound from the
     transcript and measurements, not by ear, and says so when unsure.
- Scenario recipes (advisor, 24 Oct 2026). Each brief starts from the matching
  recipe on the advisor's "Scenario recipes, second by second" board and writes
  the focus second by second: one line per beat, the seconds and the one thing
  the viewer looks at then (the headline, the person window, a story line, the
  figure, a strip, a picture that breathes). One focus at a time on screen: no
  story line while the person window or a card is opening, no strip coming in
  under a new line, no headline sharing its seconds with anything but the
  footage. The director QA reads the strip against that timeline and sends back
  any second where two things compete. Six recipes on the board (hardware
  reveal, trailer drop, person in the news, numbers, delay, debate), copied
  with production's kind-to-recipe mapping in `notes/scenario-recipes.md`; a
  story no recipe fits writes its own focus on the same principles and says
  so. Mohammad's voiceover relaxes the rule: face and name may stay while he
  speaks. First applied to the Aonuma Reel (v4, recipe 3: headline alone,
  then the photo box alone, then the lines), which had not posted.
  Face on the cover (Mohammad, 24 Oct 2026, inbox, over recipe 3's headline-alone
  opening): on people stories the person's photo box and name plate are already
  open on frame 0 beside the headline, so the grid tile shows face, name and
  headline together (the 23 Oct people rule); the box steps aside at 3.5 s and
  the story lines start after it. The box opens without an animation on the
  cover. Aonuma (09:30 Dubai, 24 Oct) was scheduled before the answer and went
  out with the headline-only cover.
- UAE prices take the Central Bank's dirham symbol, left of the digits.
- Stills get the same frame: each image fills 9:16 and pans slowly across,
  three or four official images per story, with the flavour's bed under
  them. Avoid images carrying someone else's watermark (Game Informer's
  GTA VI screens) and low-resolution art that would be upscaled 3x.
  Stills move smoothly (18 Oct 2026): `stills_clips` renders at 4x and scales
  down, so pushes and pans do not judder; a stills picture takes about 40 s of
  render per image (detail in `ops/build/system-history.md`).
- His voice over a Reel (2 Oct 2026, for the Fire Emblem 30-hour review):
  `reel(..., voice=<read processed with templates/voice.py>)` plays the
  read over the footage; the footage's own sound drops about 18 dB while
  he speaks and comes back in the pauses (`duck_db`). The shots must last
  at least as long as the read, and the on-screen lines follow what he
  says. Recording rules: `notes/voice-guide.md`.
- The end card (outro.py) follows as before.
- Footage sharpness (Mohammad, 2 Oct 2026: some trailers looked soft). A
  16:9 trailer has to be enlarged to fill 9:16: 1.78x from 1080p, about
  2.4x from a letterboxed one, and Steam trailers stop at 1080p. Prefer a
  4K copy when one exists (IGN's MP4s run up to 3840 wide; press kits),
  which fills the frame with no enlargement, and avoid letterboxed
  trailers when another cut exists. `reel.py` gives every Reel the standard picture finish (Mohammad,
  12 Oct 2026, after a three-way TEKKEN test of today's look, a filter
  chain and an AI upscaler: "make the filters standard for every Reel"):
  a light denoise before the enlargement, lanczos, contrast-adaptive
  sharpening (`cas`, lighter on 4K), a touch of contrast and colour, and
  a fine moving grain that reads as detail on a phone. Footage and
  official stills get it; our own graphics (numgfx) stay clean;
  `reel.FINISH = False` turns it off.
  Source order (Mohammad, 6 Oct 2026, after GameSpot's Ace Combat 8 Reel
  looked cleaner than ours: it was Bandai Namco's own 9:16 cut, nothing
  cropped or enlarged, while ours cropped a 1080p trailer and enlarged a
  608px strip 1.78x): 1. the publisher's own vertical cut (press kits,
  media sites, or a file he sends; no social-media downloaders), 2. a 4K
  trailer, 3. a 1080p trailer, choosing close-ups and centred subjects
  that survive the crop. Each Reel's draft notes say which kind of source
  it used.
  Enlargement cap (Mohammad, 12 Oct 2026, on image quality, after the
  letterboxed Street Fighter trailer went out enlarged 2.4x): `reel.MAX_ZOOM`
  is 2.0. The shot sheet prints each shot's enlargement (`x1.8`) and flags
  `soft` above it, and the render stops on a clip with under 960 rows of
  picture or a still enlarged past 2x. `lowres_ok=True` only when no 4K,
  publisher or unletterboxed copy exists, said in the draft notes.
  Full quality to every platform (12 Oct 2026): Instagram gets the same
  file as X and Threads, not a smaller "phone" copy. The 47 MB DOOM Reel's
  "Instagram Video download failed" was a one-off: the 73 MB TEKKEN 8 Reel
  posted the same morning, and Reels up to 92 MB have gone through. On that
  error, retry the same file once; only a second failure gets a smaller copy.

Instagram: every Digital Lounge story goes to Instagram as a Reel at the same
time as its X post (the still-card rules of 27 to 30 Sep are in
`notes/standing-history.md`). Reels safe zone: x 96 to 910, y 285 to 1480.
Vivid look on Reels (Mohammad, 2 Oct 2026; approved the same evening, "the new colourful look is perfect", so it is the standard for every Reel and overrides "the chip stays azure" for Reels):
"something similar to DXB-KNIGHT in terms of the chip, multiple themes",
because one colour had run for a while. `reel.py` now defaults to
`vivid=True`: the news chip takes the story's theme accent (cold azure,
stylized periwinkle, playful mint, spectacle amber) instead of azure on
every story, and the banner's wave lines run in the theme's colours across
the top band behind the headline. Country chips stay bright indigo; no pink
in our themes (official art that is pink stays; 4 Oct 2026). `vivid=False` restores
the azure-only look. Pick a theme per story so a run of posts varies.
More variations (Mohammad, 2 Oct 2026: "Honestly, I like them all"):
- Four styles for the top band (`STYLES` in reel.py): `lines` (the first
  look), `bold` (thicker, denser waves), `glow` (a soft wash of the two
  theme colours) and `frame` (the top lines plus fainter waves rising from
  the bottom for the whole clip). `style=None` rotates them through
  `templates/assets/style-ledger.json` like the beds, so no two posts in a
  row share a style; a re-render keeps its style. Pass `style=` to choose.
- Three more themes (fast_ar.THEMES, ig_ar.ACCENTS): `emerald` (teal to
  lime) for general news as a change from blue, `gold` for numbers and
  milestones (أرقام، إنجاز), and `crimson` (red into amber, never pink) for
  عاجل only, so breaking news stands out when it comes.
- Daily disk cleanup (Mohammad, 7 Oct 2026, after the disk allowance ran
  out mid-render that morning): a Routine runs `newsroom/disk_cleanup.sh`
  every day at 02:47 Dubai. It removes render temp folders left in /tmp,
  scratchpad batch folders untouched for 3 days, fetched footage and audio
  in uploads untouched for 3 days (images and his own recordings stay),
  and re-clones dxb-queue shallow once its history passes 1 GB. It does
  nothing while a render or a publish is running, or while dxb-queue has
  unpushed work. `--dry-run` lists what it would remove.
  Slim clone (Mohammad, 25 Oct 2026, inbox: "Re-clone slim"): after the cleanup
  left 616 MB free, dxb-assets was re-cloned at 03:50Z as a shallow, partial,
  sparse clone (`--depth 1 --filter=blob:none --sparse`, checked out: templates,
  jobs, newsroom, notes, arabic, analytics, art, .claude, .github): 27 MB in place
  of 24 GB (20 GB of history plus 4 GB of cards), free space 24 GB. `cards/` and
  `live/` are not on disk; `git show HEAD:cards/...` fetches a file on demand,
  and renders run on the runner. The pilot worktrees were removed (their branches
  are on GitHub). In a new container, clone the same way.
  Keep it slim (25 Oct 2026): a history command that reads file contents
  (`git log --stat` or `-p`, `git show` of old commits, blame) makes the partial
  clone download every media blob it touches; one `git log --stat` over the job
  files pulled the clone back to 20 GB by 04:20Z and left 3 GB free. Read history
  with `git log --format` (no stat), single files with `git show <rev>:<path>`, and
  wider history from GitHub. If `.git` grows past a few GB, re-clone the same way
  once everything is pushed (done 05:15Z).
- Reels only (Mohammad, 30 Sep 2026): still cards on Instagram reach 1 to
  3 views where Reels reach about 1,000 (the WARDOGS Reel: 96% non-followers,
  mostly from the Reels tab), so every Digital Lounge Instagram post is a
  Reel. A story with footage uses the footage; one with only a still gets a
  still Reel: the art as an 8 second clip (`-loop 1 -t 8`, padded to 16:9)
  passed as `video` with `audio=False`, so the bed plays under it and the
  jingle end card follows. `focus` (0 left to 1 right) aims the full-screen
  cover at the subject or logo, because the cover is the grid tile.
  One image is not enough when more exist (Mohammad, 30 Sep 2026): gather
  every official still for the story (publisher blog, Steam screenshots,
  store page, press kit) and pass three or four through
  `ig_ar.slideshow(images, name, seconds=8)`, which crossfades them into
  one 16:9 clip for `video`; the first image is the cover. Trim a
  letterboxed still's bars first. A single still is the fallback only
  when the story has one image.
  X keeps its still and video cards.
- Caption: the first line is a hook that differs from the card headline
  (only about two lines show before "more"), with the game's name and the
  news word in its first five words (advisor, 14 Oct 2026), then the full
  story with the same checked facts, then #ألعاب #أخبار_الألعاب followed by 2 story hashtags (Arabic tags
  first, so the line reads right to left).
  Hashtags for discovery (Mohammad, 28 Sep 2026: make sure they are
  there where they help people find the account). Instagram caps a post
  at 5 hashtags, and TikTok and YouTube Shorts work best with 3 to 5, so
  every Instagram caption, TikTok caption and YouTube description ends
  with exactly those 4: #ألعاب #أخبار_الألعاب, then the game and the
  platform or series as written by the publisher (#WARDOGS #Steam).
  Search on TikTok and Instagram also reads the words, so the game's name
  sits in the first two lines of the caption. X posts, on both
  accounts, carry no hashtags: X has said they are no longer needed
  (Mohammad, 28 Sep 2026). The video platforms keep them. Before queuing, and before reusing
  an older caption, check that its last line starts with #ألعاب (on
  28 Sep three TikTok backfills went out with an older, English-first
  hashtag line).
  No links (not clickable). Same Arabic rules and two passes as X.
  The caption stands alone: it names the game by the second sentence and
  never leans on the card for its subject (27 Sep 2026: swapping in a new
  hook left three captions saying "the game" with no name). Read every
  caption back in Postiz after queuing.
  The first post, Fire Emblem (Reel), went live on 27 Sep 2026 at 15:40.

Brand kit (Mohammad, 26 Sep 2026):
- Mark: the existing azure play button on an indigo radial ground,
  `templates/digi-mark.jpg` (400x400, from his upload). It stays.
- Palette, sampled from the mark and the old banner: ground `#141332`,
  panel `#1E1D4A`, edge `#3F3DA8`, azure `#28B6F6`, bright indigo
  `#5552E0`, ink `#F4F3FF`, body `#C9C8E6`. Azure carries chips (ground
  text on azure) and the rule under the media.
- Font: Dubai (Light, Regular, Medium, Bold) for Arabic and Latin. Its
  EULA allows commercial use but forbids redistribution and this repo is
  public, so the TTFs never go in git: they live in
  `/root/fonts-private/dubai/`, which a new container does not have. Ask
  Mohammad to upload `dubai.zip` again and unzip it there.
- Banner: the old wave lines redrawn, bright indigo left to azure right,
  with the name in Dubai on a dark plate
  (`live/2026-09-26/digital-lounge/digi3-banner.png`, sent 26 Sep).
- Fast card: `templates/fast_ar.py`, `fast_ar(media, date, source, out,
  label=None, country=None, crop=False, video=...)`. Same frame as
  `fast.py` (both call `fast.compose`), mirrored right to left. `date` in
  the English form, printed as "26 سبتمبر 2026" in Western digits;
  `source` as the Arabic reader knows it. It refuses any chip or country
  outside the agreed lists.
- Footer: the banner's wave lines behind it, subtle (Mohammad, 26 Sep
  2026), varied by `theme`, picked per story like DXB-KNIGHT's accent:
  cold indigo to azure (sci-fi, horror, hardware, business), stylized
  indigo to periwinkle (RPG, fantasy, anime, story-led), playful azure to
  mint (platformers, party, sports), spectacle azure to amber
  (blockbusters, film and TV). Chip and rule stay azure on every theme.
  No blend may pass through pink: indigo into amber does, so spectacle
  starts from azure.
- Video first (Mohammad, 27 Sep 2026): Arabic games video is rare, so a
  Digital Lounge story with an official trailer goes out as a video card.
  `templates/trailer.py`: `steam_trailers(appid)` lists Steam trailers,
  `fetch(hls, name, start, seconds)` saves a stretch to uploads,
  `transcribe(name)` returns timed English lines (faster-whisper small;
  `pip install faster-whisper` in a new container, the model downloads on
  first use). Arabic subtitles: `fast_ar(..., video=..., subtitles=[(start,
  end, text)], sub_bottom=None)`, Dubai Bold on a dark band above the chip
  row; raise `sub_bottom` (about 700) when the clip has its own subtitles.
  Trailers not on Steam (28 Sep 2026): YouTube now asks for a sign-in
  (yt-dlp refused), and third-party "YouTube downloader" sites are not
  used (they route around that check). IGN's video pages
  (ign.com/videos/<slug>) link the official trailers as plain MP4 files
  on assets.ign.com (1280 to 3840 wide, no IGN logo on the Fortnite
  trailer); publisher sites such as playstation.com also host product
  clips on gmedia.playstation.com. Nintendo's US store product pages
  (nintendo.com/us/store/products/<game>/) list their trailers as
  `publicId` values under /store/software/switch2/<nsuid>/Video/, which
  download as `https://assets.nintendo.com/video/upload<publicId>.mp4`
  (29 Sep 2026: the Star Fox Battle Mode trailer, 1280x720, after IGN had
  no copy); the first `nsuid` on the page is the game's own. Check the first and last seconds for
  ratings cards, end slates and anyone else's logo before cutting.
  Footage keeps its own sound (Mohammad, 30 Sep 2026): when the video is
  footage (a trailer, gameplay, his capture), its original audio plays and
  no bed is added under it; the bed is only for clips with no sound and for
  our own graphics (charts). `audio=True` is the default in `ig_ar`,
  `fast_ar`, `fast` and `short.clip`. Speech in the kept sound gets Arabic
  subtitles of what is said (the band below), so a voiced trailer costs a
  transcript; pick a stretch without talking when time is short.
  The subtitle band is for speech only (Mohammad, 28 Sep 2026): facts
  shown in it read as someone talking. A clip without speech gets no
  band text; the facts stay in the headline, panel and caption.
  The transcript is a draft: check it against on-screen text or the
  official source before writing the Arabic (on 27 Sep it heard "I think"
  where the screen said "They say"), then write the Arabic with both
  Arabic skills. Subtitles carry what was said, never more. His own
  gameplay with Arabic captions is the third step, once the YoloBox Ultra
  capture is running.
- Sound (Mohammad, 28 Sep 2026): `templates/sonic.py` synthesises the
  Digital Lounge jingle and a quiet background bed from the same four
  notes, so the music is original. Every flavour keeps the motif's shape
  and changes mode, instruments, tempo and rhythm (`FLAVOURS`): `neon`
  (D F# A E, bells) is the everyday one; `hijaz` (D Eb F# A, oud-like
  string) the regional one. Occasions: `ramadan`, `eid` (hijaz),
  `halloween`, `christmas` (calmed after the first cut was distracting).
  Post types: `stats` (sales charts such as Famitsu, meant to be
  exciting), `breaking`, `launch`, `digest`. No noise swell, no saw pad
  (both read as a whoosh or a plane); percussion is tonal, never noise.
  `python3 sonic.py <dir>` renders them all; `under(video, bed, out,
  jingle_path=...)` puts a bed under a clip with no sound of its own.
  Audition set in `live/2026-09-28/audio/set/`.
  Background bed variations (Mohammad, 1 Oct 2026: the one bed under every
  still Reel had gone stale; the jingle itself stays `neon` everywhere):
  `neon_b` marimba over D A Bm G with a light beat, `neon_c` vibraphone on
  two major-seventh chords at a slower quarter-note pace, `neon_d`
  glockenspiel over D Em G A, `neon_e` plucked strings over Bm G D A, a
  minor-leaning loop. Each keeps the motif every 8 bars. `reel.py`,
  `ig_ar` and `short` rotate `sonic.EVERYDAY` for clips with no sound
  (`sonic.rotate(<file name>)`): each new post takes the bed rested
  longest, from the ledger in `templates/assets/bed-ledger.json`, so no
  bed repeats until all five have played (Mohammad, 1 Oct 2026: use the
  variations for variety); a re-render keeps its bed. Footage still keeps
  its own sound. Launch, breaking and stats keep their own flavour.
  Beds evolve (Mohammad, 14 Oct 2026, 12:40 Dubai, from the Fire Emblem
  "Obelisk Chamber" mashup he sent as the reference: "something similar
  depending on the news type and subtle change in videos that are long so
  the background music doesn't become noisy"). The reference keeps one
  theme, one tempo, one key and one loudness for five minutes and changes
  only the arrangement, about every 50 to 60 seconds with a crossfade; its
  audio is Nintendo's and is not used, only that shape. `sonic.PALETTES`
  are arrangements of our own motif (bells, mallets, piano, e-piano,
  strings, synth, chip, oud, qanun, musicbox, celesta; new voices `piano`,
  `epiano`, `flute` and a `strings` pad of detuned sines, never a saw), and
  `sonic.ARRANGE` gives each flavour the cycle it moves through, the first
  palette being the flavour's old look (everyday neon: bells, piano,
  strings, mallets, e-piano; stats: synth, chip, bells; launch: bells,
  synth, mallets; digest: piano, strings, bells, e-piano; breaking: synth,
  piano; hijaz: oud, qanun, strings; retro stays chip only). `sonic.bed(
  style, path, secs=)` (`arrange`) builds a bed for the clip's length: a new
  palette every `SECTION` (8) bars, each change a one-bar overlap in which
  the old palette fades out as the new fades in, every section balanced to
  the same level, the motif still surfacing at bar 5 of each 8. A clip
  shorter than a section hears one palette, as before. `outro.append`
  takes it for every silent clip (`outro.evolving_bed(style, secs)`,
  cached by style and seconds), and reel.py and ig_ar.py pass the rotated
  everyday bed through it. The 16-bar loops stay for anything that asks
  for `bed()` without `secs`. Audition: `live/2026-10-14/audio/evolve/`
  (60 s beds and the Epic educators Reel re-laid as a demo); his verdict
  pending.
  Retro sound (Mohammad, 11 Oct 2026: "a little bit 8-bit or retro like an
  NES game"): "on this day" release anniversaries and other stories that are
  plainly retro (an old game, an old console, a look back) end on the
  `retro` flavour, the same motif on an NES-style pulse lead, triangle bass
  and a frame-speed chord arpeggio, dry; its bed plays under retro Reels with
  no sound of their own. The «في مثل هذا اليوم» chip picks it in `reel.py`
  (`ig_ar.SOUNDS`); elsewhere pass `sound='retro'` or `outro.append(...,
  style='retro')`. Not for the «الطريق إلى Ocarina» series or other coverage
  of new releases and remakes, which keep the everyday sound. Retro audition:
  `live/2026-10-11/audio/retro/`.
  On-this-day Reels are built with `templates/retro.py` (11 Oct 2026: the
  game plays on a real CRT, then a fact sheet and the facts one at a time).
  Mohammad, 11 Oct: bigger type in the lower half, and the console's own
  colours on pixel-edged blocks beside each row and each fact (`CONSOLES`:
  N64 red, yellow, green, blue and so on; no pink, so PlayStation takes its
  logo colours). Add a console there before its first post. Palettes
  (11 Oct): Atari 2600 (big in the Middle East in the 70s and 80s), NES and
  Famicom kept apart (grey and red against cream, maroon and gold), Master
  System, SNES and Super Famicom, Mega Drive, Game Boy, N64, PlayStation,
  Saturn, Dreamcast, GBA, PS2, GameCube, Xbox. The «في مثل هذا اليوم» chip
  and the wave lines follow the console too, not gold (Mohammad, 11 Oct: the
  gold did not blend): `SKINS` borrows each machine's own look for the chip
  (Atari woodgrain, NES charcoal with the red band, Famicom gold plate, Game
  Boy green screen) and an artifact beside it (controller buttons, the Super
  Famicom diamond, PlayStation's face buttons, the Dreamcast swirl).
  The ground follows the console as well (Mohammad, 11 Oct 2026): a dark
  tone of the machine (Famicom maroon, Game Boy green, Atari walnut, PS2
  blue-black) replaces the indigo on these Reels only; the end card keeps
  the Digital Lounge indigo and mark.
  Closer to the box art (Mohammad, 11 Oct, from the 1989 Game Boy box):
  Game Boy is black with yellow and orange rays, a brushed-silver chip in
  dark grey type and electric-blue, yellow and orange blocks; NES and Mega
  Drive get their black boxes' fine grey grid, Atari its woodgrain, PS2 its
  blue lines. Those patterns stay above the TV and below the safe floor, and
  replace the wave lines there. No wave pair blends red into blue (the
  middle reads magenta).
  Handhelds (Mohammad, 11 Oct 2026: "Gameboy, Game Gear back drop will be
  a desk and not TV"): Game Boy, Game Gear and GBA stories play on a desk
  scene, never the CRT. The scene (Mohammad, 11 Oct 2026: "placed on a
  table to echo 80s 90s style surrounded by stuff that released on that
  era like a Walkman"): the scout's flat lay with a cassette, sunglasses
  and a pocket watch (`scene-desk-4`) for now, his front-on Game Boy shot
  (uploads/retro-gameboy-front.webp) upright on it, never slanted, the
  footage on its own screen in the DMG greens. A proper period flat lay
  (Walkman, cassettes, floppy disks) is on the scout's list. Game Gear and
  GBA need their own product shot in `HANDHELDS` first; `retro.render`
  stops until then.
  White ground is allowed, not the default (Mohammad, 11 Oct 2026): a console
  whose box is white (Dreamcast, PAL Master System; `light` in `SKINS`) may
  take `light=True` on a story when it helps, and the type turns dark.
  Layout after his review (11 Oct): the TV keeps its first size and
  framing; type is larger and fitted to the width (date 84, title up to 66,
  sheet values up to 62, facts up to 70, shrinking to the floor); the sheet
  drops the game row (the title says it); the box art stands on the cabinet
  left of the TV. On a dark ground the photo fades in under the title as
  first approved; on a white ground it appears only below the title
  (`FADE_LIGHT`), because the wall under dark type read messy, and the wash
  before the first row is full. The console's lettering colour (`type` in
  `SKINS`: Mega Drive gold, Game Boy blue, Dreamcast orange, Xbox green and
  so on) carries the title line when it reads on the ground (contrast 3:1),
  otherwise plain ink. Review every frame as an art director before
  sending.
  Retro rooms (the 70s den, the three.js and path-traced dens, rooms per era)
  are parked until Mohammad brings them back; their build notes are in
  `ops/build/system-history.md`. Everyday audition:
  `live/2026-10-01/audio/`. On posts: every Reel
  ends on the jingle (see the end card below); X video cards and stills
  carry no added sound yet. The sound is a Digital Lounge mark;
  DXB-KNIGHT does not use it.
  National days are not part of the news set: some readers take them as
  political and it could cost the account. If Mohammad ever decides on a
  UAE National Day card with the anthem in these instruments, it is his
  call per year, and the rules on using and arranging the anthem are
  checked first.
- Reel end card (Mohammad, 28 Sep 2026: every Digital Lounge Reel, so
  every TikTok and Short too): `templates/outro.py`, applied by `ig_ar`
  itself. The clip fades into the play mark, each jingle note lights one
  platform (X, Instagram, TikTok, YouTube, right to left), and the name,
  "أخبار الألعاب" and @the_digilounge come up on the final chord; nothing
  zooms or pans. It adds 2 seconds (advisor, 14 Oct 2026; 3.6 until then). Reel footers drop the handle
  (the card carries it); stills keep it. Sound: a trailer kept with
  `audio=True` plays its own sound, faded out before the card, and gets
  nothing added but the jingle; a clip with no sound gets the flavour's
  bed under it. The flavour follows the chip (`SOUNDS` in ig_ar.py: عاجل
  breaking, متوفر الآن launch, أرقام stats, otherwise neon); pass
  `sound='ramadan'` and the like for occasions. `outro=False` renders a
  Reel without it.
- Stills, not animation (Mohammad, 26 Sep 2026). `animate=6` exists (a
  seamless 6 second MP4 loop, only the footer lines drift) but is not
  used: cards post as stills unless he asks for motion on a story.

## The Game Awards co-stream (advisor decision, 14 Oct 2026)

Digital Lounge co-streams The Game Awards on Thursday 10 Dec 2026 (Peacock
Theater; past years 17:00 Pacific, 05:00 Friday Dubai; the time is confirmed
when announced) on YouTube, with Mohammad's voice and no face, Instagram
carrying the clips. The YouTube drop of 1 Oct covers posted Shorts, not this
live stream. No YoloBox purchase before the Awards: OBS on a laptop with
window capture and a USB mic.
- Build by 31 Oct: a live brand package in the Reel look as OBS scenes:
  starting-soon with a countdown, BRB, a right-to-left lower-third ticker in
  Dubai, the corner mark, an end card (`templates/live/`, planned).
- Two unlisted dry runs in November on the next showcases, the second with
  the ticker fed from the hourly watch.
- Countdown Reels from 3 Dec; the announcement Reel on 9 Dec with the Dubai
  time.
- The clip routine is designed first: timestamps noted live, five to eight
  Reels cut from 06:30 Friday under `list`, `trailer` and `numbers`.
- Judged at the 16 Dec audit on peak live viewers, replay views and the clip
  Reels against normal Reels; play streams and hardware are decided then.
- The Awards are in `newsroom/events.md`; its co-stream policy is read the
  week before (a check-in is set for 3 Dec). Plan and checklist:
  `notes/tga-costream-plan.md`.

## «الطريق إلى Ocarina» (Mohammad, 11 Oct 2026)

A Digital Lounge spotlight series running up to the Switch 2 launch of The
Legend of Zelda: Ocarina of Time on 5 Nov 2026. Few Arabic outlets cover it,
so the aim is to bring the region's attention to a major upcoming release
for as long as possible, drawing in new fans. It is coverage of a new
game told through its history, not a retro piece: every episode opens on
the series intro (`templates/ocarina_intro.py <days>`, his Triforce Medley upload and «باقي N
يومًا»; never يتبقى) and keeps the everyday sound, never the 8-bit retro
flavour. The 23 Nov anniversary of the original belongs to the series too.
Episode 1 (why it matters) is queued for 13 Oct 18:00 Dubai.

Mini documentary (advisor, 19 Oct 2026, agreed with Mohammad: "change the
content, not the intro or the outro... so it looks like a mini, well-designed
documentary"). Found in the first five: episodes 3, 4 and 5 all run trailer
A's score from 26.0 s and episode 1 ran trailer A's opening from 5.0 s, so
the same music returned episode after episode; the Hyrule Field shot with the
castle appears in episodes 1 and 4; only 4 and 5 opened on the series intro.
1. Fixed identity: every episode opens on the series intro
   (`ocarina_intro.py`, «باقي N يومًا») and closes on the same outro.
   Episodes 1 to 3 stay as posted.
2. Everything between is built around the episode's subject, with its own
   material and its own sound: a character or hero gets that character's
   reveal footage mixed with official artwork, the lines saying who they are;
   music has the piece described heard (the presentation's stretch where it
   plays); a mechanic is shown in action, the N64 original next to the
   Switch 2 version; history or making-of uses archive material, official
   artwork and the source's own figures; places and the world take the
   official map as a guided piece (web-style motion, below).
3. Series ledger: `notes/ocarina-series.md` records each episode's shots and
   audio stretch. No shot and no audio stretch appears in two episodes;
   check a new episode's shot list and track against it before the render.
4. Episode 5 (Z-targeting, Tue 20 Oct) is rebuilt on a stretch no earlier
   episode used (combat or targeting music from Aonuma's presentation) with
   its shots checked against the ledger; had there been no time, it would
   have posted as built and the rule started at episode 6.

## HyperFrames inserts in live Reels, limited use (advisor, 24 Oct 2026, agreed with Mohammad)

Pass 2 of the pilot was approved (the GTA 6 numbers card and the Oshima character card,
`notes/hyperframes-pilot.md`). HyperFrames may now be used in live Reels for a limited set of
pieces, rendered as inserts; reel.py stays the backbone.
1. What may use it: numbers cards (count-ups, platform or region splits, rankings) on the game's
   own footage; rebuilt character, fact or UI cards in the game's style (the Oshima case, crop-cut
   text rebuilt vertically). Nothing else for now: footage, story lines, sound, the end card and
   transitions stay in reel.py; skins and transitions in HyperFrames come later, by separate memo.
2. How it joins: a job asks for `"insert": [{"piece": "numbers" | "charcard", "shot": N, "data":
   {...}}]` (format in `templates/hfinsert.py` and `render_job.py`). Shot N is a `-gfx-` card from
   `gfx`, which reel.py renders as today; the runner then builds the piece from the data as a static
   composition, renders it (1080x1920, 30 fps, the Dubai font copied in from the private repo and
   never kept) and lays it over that shot's span of the finished Reel, opaque, with a hard cut at each
   end, running 0.2 s past the span (not into the end card); the numbers piece counts up from zero and
   clears its own type over its last 0.35 s, so the cut back goes from its footage to the next shot.
   The Reel's audio is copied, so its single stretch runs under it. (Fades of 0.4 s and 0.1 s at the
   edges showed the fallback card through the insert, two cards half-faded; 24 Oct.) Jobs without the
   key render exactly as before; render.yml installs HyperFrames only for a job that has one.
3. Safety: a failed insert, or one past 5 minutes, leaves the shot's numgfx card in place and is
   noted (the render log and `hf_insert` in render-times.json); the story is never held. Breaking
   news never waits for an insert: the breaking profile uses the current cards. HyperFrames is pinned
   to 0.8.143; upgrades only by memo after a test.
4. Quality: every insert goes through the director QA (readable at phone size, safe zone, first
   frame, Arabic order, contrast over the footage). From pass 2: the hand-over between two cards is
   quick (0.2 s out, then 0.25 s in), so two half-faded cards are never on screen together.
5. Roll-out: the first three live Reels with an insert go to Mohammad as a preview before they are
   scheduled in Publer; after his OK on those, they follow the normal rolling queue. Each use is
   recorded in the format ledger (note "hf insert") and in render-times.json, for the Tuesday audit.
6. Merged 24 Oct 2026 after a parity test on the runner. One job without an insert (GTA 6, fixed
   IGN sources) was rendered on today's code twice and on the new code once: frame count and length
   identical; the only differences are the moving grain and the audio encode, and two runs of the old
   code differ from each other exactly as much (blurred PSNR at worst 42.8 dB on the same frame; the
   new render's audio is bit-identical to the second old run). Steam HLS sources vary per download, so
   a re-render of a published Reel cannot match it frame for frame. Insert test v4 on the runner: the
   insert rendered in 76 s, entry, hand-over and exit clean (`notes/hyperframes-pilot.md`).

## Digital Lounge motion kit (approved 24 Oct 2026)

All seven elements were approved (Mohammad, 24 Oct, inbox, "Approve all"). Ops
uses them only through the job file's `"kit"` key and the design-pass rules
(one or two kit moments per Reel, on the element that matters, never on the
breaking profile); the photo box opens on frame 0 when it is on the cover; the
director QA asks "does this motion help reading?" and removes any moment that
does not. The pilot, the blocks and their build notes are the build desk's
(`ops/build/system-history.md`).

## Trailer audio split, live (Mohammad, 24 Oct 2026, inbox 16:26Z: Adopt Cocktail Fork)

Problem (24 Oct): a trailer's soundtrack is one mixed track, so when a Reel reorders or holds shots
its effects land on shots they do not belong to (a sword clash while people sit and talk). Test on
three published Reels (Shogun 2, Cyberpunk x Witcher gear, Phantom Blade Zero unlock time; branch
`pilot/audio-split`, workflow `audio-split-test`): MERL Cocktail Fork split each Reel in 10 to 15 s
on the 4-core runner and left 14 to 21% effects in its music by the other tool's judgement; BandIt
Plus took 9 to 14 minutes and left 18 to 40%, and its weights are CC BY-NC 4.0, so test only.
Cocktail Fork's code and weights are MIT. Mohammad adopted Cocktail Fork.
1. What runs: a runner job whose `track` is a stretch of trailer audio is rendered as before, then
   `templates/tracksplit.py` rebuilds the body sound: the trailer's music stem runs continuously
   under the whole Reel (faded as the track was); each footage shot gets back only its own effects
   stem, from the same source moment as its picture, 3 dB under the music; stills, graphics and cards
   get none; dialogue is not put back. The end card and its jingle stay as rendered, the body keeps
   the old body's level, and the new sound is muxed onto the same picture (video stream copy). The
   decode and smear checks then read the Reel that ships.
2. Not split (today's audio, unchanged): our bed or no track, stills, numbers and silent footage;
   speech that is the news (`speech_ok`, or `"speech_keep": true` in the job for a voiced or
   subtitled Reel without speech_ok); a skin kit with its sting; the breaking profile and the عاجل
   chip (speed first; the install alone is about 10 s); `"audio_split": false`; the container
   (COCKTAIL_DIR unset).
3. Fallback, never a hold: the split fails, passes 300 s, or the music stem is not clean (a second
   Cocktail Fork pass still hears more than 5% of the music stem's energy as effects or speech, the
   test Reels measured 0.2 to 0.9%; or music is under 40% of the track stretch, an effects-led stretch;
   the test Reels measured 57 to 79%): the Reel keeps today's audio. The render log prints `render_job:
   audio split:` with the outcome and reason, and render-times.json keeps it as `audio_split`.
4. Install: render.yml installs it only for a job that needs it (`tracksplit.py need <job>`), from
   merlresearch/cocktail-fork-separation at commit 19b3de8 (mrx.py and the default checkpoint), with
   the weights in the Actions cache, never in git; a failed install leaves the Reel on today's audio.
5. Director QA adds one check (Director card and QA format in `newsroom/delegation.md`): every sound
   heard matches what is on screen; the music track is clean. A mismatch fails the Reel.
6. Parity test on the runner, 24 Oct: Dead by Daylight on our bed (no track) rendered as before, 555
   frames and 18.52 s like the published v3, audio correlation 0.9999 (encoder noise only). Shogun 2
   on its trailer track: split applied (music 58.1% of the track, leftover 0.8%, 15 s to separate, 21 s
   in all), 669 frames and 22.32 s like the published v4, end card sound identical, decode and smear
   checks clean, its loudness envelope following the test's rebuild (0.95) and not the published mix
   (0.56). Both test Reels were deleted from `cards/` after the check; neither was for posting.
   Cost: about 21 s of render per split Reel and about 10 s of install, far inside the 45-minute
   fresh-reveal target.

## Explainers from the source's own drawings (trial, 27 Sep 2026)

For "how does it work" stories (patents, hardware, new features),
`templates/explainer.py` steps through the source's own figures, one step
per figure, drawing left and step text right, 1600x900 with the
DXB-KNIGHT footer. Motion is limited to what the figures show: `ring`
pulses on a part, `slide` lifts a drawn object out and moves it into
place, `path` runs dots along the figure's own arrows. No AI-generated
visuals of hardware (they invent parts readers take as real); if one is
ever used, label it an illustration. Mohammad liked the tap-to-pay trial
(`cards/2026-09/sony-tap-to-pay-explainer-trial-v2.mp4`); it has not been
posted, and using the format on a story is his call.

## Always ask for Mohammad's take before building a card

DXB-KNIGHT is not a wire service. Before rendering any card, ask what he
thinks of the story — whether he has played it, what he made of it, what
he would tell a reader that the source does not say.

His answer decides the background mode:

- he gives a take -> `voiced` (purple), and his line goes in the copy
- he has none, or it is pure reporting -> `reported` (navy)

Ask before rendering, not after. A card built without asking is a card
that reports someone else's story in his name.

The same goes for fast posts (Mohammad, 25 Sep 2026): before queuing a
batch, ask whether he wants his view on any of them. A post that has gone
to Postiz can only be edited or deleted by him in the app, so his input
has to come before the push, or as a reply once it is live.

## Art goes on top

`single` is the template with the art panel at the top, and it is the
default for a story with an image. `quote` puts media *under* the quote,
so it is not the way to put a picture on a card.

`gulf=True` and the gold GULF chip exist only on `single`, so a regional
story built as a `quote` silently loses the Gulf marker.

When the template choice is not obvious, ask rather than guess.

## Japan sales: two cards, one post

Famitsu's weekly physical sales go out as fast as possible after Famitsu
posts them (usually Thursday 22:00 JST, 17:00 Dubai; holiday weeks move,
and each article ends with the next date, "次回は...に掲載予定").
`templates/famitsu.py <this week url> <out-stem> <date> <last week url>`
reads Famitsu's own articles, not Gematsu's rewrite, and renders a software
top 10 card and a hardware card for the same post, with week-on-week change
(green up, red down; red is kept out of the row colours for that reason). An untranslated title stops
the run: add the publisher's English name to `TITLES`. Chip STATS, cold,
reported unless Mohammad gives a take.
Digital Lounge sales Reel (approved by Mohammad, 5 Oct 2026; replaces
`sales_reel` and `short.chart`, whose rows on a flat ground left bare bands):
`templates/sales_full.py`, `reel(rows, week_label, date, out, hardware=hw)`.
It opens on the question over a mosaic of the top four, counts down 10 to 1
with each game's official screenshot full frame and panning (the rank, box
art, title, platform, last week's place and the two figures over a soft band
low in the frame), then the hardware slide: every console opens on last
week's number in last week's order and counts to this week's, the rows
re-sorting live so one that overtakes slides up, with the console's own
product shot on the right (`templates/assets/consoles/`). Each row takes
`shot=(screenshot, (from, to))`: the publisher's store page, Steam or a press
kit, 1920 wide where one exists, letterbox bars cropped, logos and text kept
out of the pan. On Nintendo's store pages keep only the `publicId`s under the
game's own nsuid (the first one on the page); the others belong to related
products. Speed agreed as is (5 Oct). First used for 21 to 27 Sep
(`cards/2026-10/famitsu-sep21-27-full-reel-v2.mp4`).
Timing (Mohammad, 8 Oct 2026): the sales post goes out immediately after
Famitsu releases the numbers, not held for a slot. Watch the chart page
from about 16:45 Dubai on Thursdays (or the date the last article names),
have the screenshots and box art for the likely top 10 gathered before
then, and render and bring the Reel to him the moment the article is up.

## The lookout is its own format

The pinned month-ahead (`templates/ahead.py`) is not a flex.py card and
`roundup` is not the way to build one. Six tiles, every tile naming its
platforms the same way, notes on a second line, dates verified against
primaries because it sits pinned for a month. It renders as a still and,
with `ahead_video`, as a looping MP4 where the title glyph flickers.
Theme and glyph change with the month; the geometry never does.

## The agreed sheet is canonical

The card system sheet dated 20 Sep 2026 is the source of truth for the
canvas, the type sizes, the palette and the argument names. `flex.py`
already matches it exactly. Where `templates/README.md` disagrees with the
sheet, the sheet wins.

## Hero media: contain by default, crop only when nothing is lost

The sheet says hero media is contained, never cropped, with roundup row
thumbnails the one exception. In practice a crop to fill the panel is fine
when nothing important is lost and the frame does not look distracting or
compromised.

Contain it when a crop would cut a face, a logo or headline text. When in
doubt contain, and say what the trade-off was.

## Logos need plating

Wordmarks are far wider than either media box (`single` 1460x860,
`quote` 1460x620), so passing one raw stretches it and leaves bars.
Centre the logo on a plate cut to the box aspect exactly, then pass the
plate as `media`.

## Read every unread digest, not just the latest

The scout at `dxbknight-digest@agentmail.to` files hourly and each sheet
carries only what is new in its window, explicitly dropping what earlier
hours already filed. Reading only the newest email misses whole stories:
a piece that lands at 15:00 appears once and never again.

Sweep all unread digests before recommending anything.

Review slots (Mohammad, 5 Oct 2026, replacing sweeps on request only): he
reviews at 06:30, 10:00, 14:00 and 17:30 Dubai. A trigger wakes the session
about 35 minutes before each, the digests and an internal scout (a second,
independent read of the primaries) run in parallel, and the shortlist is in
front of him at the slot; the routine is in `newsroom/delegation.md`. Shows
(Nintendo Direct, The Game Awards and the like) get event slots agreed one
at a time once their time is confirmed. "Unread" still means "not yet worked
through", and he can still ask for a sweep at any time. After reporting on a sweep, record the
digests just covered in `newsroom/digests-covered.json` (`covered_through`,
the newest digest's time), so the next sweep starts from genuinely new
sheets rather than re-reading the day. The digest inbox is read only, never
written to (Mohammad, 13 Oct 2026: marking digests read with `update_message`
sent him an approval prompt each time).

Speculation for reach (Mohammad, 11 Oct 2026: "post all 3, we can label
unconfirmed ones as unconfirmed or rumours. I want more people to view the
channel and balance news and speculation to generate hype"). Digital Lounge
shortlists rumours, leaks and single-outlet reports alongside confirmed
news, as long as each is labelled for what it is: the chip on the ladder
(شائعة، تسريب، تقرير), the headline never louder than the source, and the
text naming who claims it and what is not confirmed. Skip only what is
harmful or explicit (leaked explicit material, hacking threats, doxxing).
The breaking lane's auto-go stays for confirmed official news only.

Date a story from its first report, not from the relay (Mohammad, 17 Oct
2026, after the 16:08Z watch offered the Ocarina of Time remake beating GTA 6
on Amazon pre-orders as a Sunday post: "a couple of days old from Japanese and
western accounts. That's what I'm trying to tackle with this account, be up to
date"). Arabic outlets usually rewrite English and Japanese stories a day or
two late, and the scout's AGE labels and the watch's outlet times are the
relay's time. So:
- An Arabic outlet is never a lead on its own. Before a story first seen in an
  Arabic outlet (IGN ME Arabic, True Gaming, Saudi Gamer, VGA4A, Arab Hardware,
  the digest's Arabic items) is shortlisted, find its first report anywhere
  (the primary, Japanese and English outlets, the forum or post it came from)
  and date the story from that. `watch_feeds.py` marks Arabic-only groups
  "AR RELAY: date it from the first report".
- The same holds for any rewrite: the age of a story is the age of its
  earliest source, and the shortlist line gives that time.
- Older than 24 hours at its first report and not yet posted: drop it, unless
  something new has landed since (a figure, a statement, a date) or it is
  regional news the wider press missed. Say which in the shortlist.
- Being first in Arabic is the point: an English or Japanese story goes on the
  list as soon as the watch or the scout finds it, without waiting for an
  Arabic outlet to carry it.

Sources and names (advisor, 17 Oct 2026, agreed with Mohammad; from the Phantom
Blade Zero director Reel, where an X reader asked «وش مصدرك؟» and the on-screen
line read «قالها سولفريم (Soulframe)»):
1. People are labelled by role at first mention, on screen and in the text:
   «المخرج سولفريم ليانغ (Soulframe Liang)», never a bare name. A name that is
   also a game, studio or product (Soulframe is a Digital Extremes game) always
   takes the role word. The brief lists each person with their role, and the
   grammar stage checks it as a house rule.
2. The X and Threads text names the source for every quote, report, rumour,
   leak or interview, in a few words («لموقع PCGamesN», «حسب بلومبرغ
   (Bloomberg)»), even when the Reel already shows it. Official announcements
   name the company, as before.
3. A reader's question about a source is answered from the story file's
   primary: the outlet, the date, and the link on X and Threads (links are
   fine there); on Instagram the outlet and the date only, no link. The reply
   is drafted for Mohammad to post (Postiz cannot reply to a live post).

Culturally sensitive details (advisor, 21 Oct 2026, from Mohammad). The game
and its news always run; only the sensitive detail is left out or kept general.
Nothing is skipped because of it.
1. LGBTQ content in games: the general word, never the specific type
   («الزواج»، «العلاقات العاطفية»، «خيارات العلاقات»، «الشخصيات»), with no
   description of what kind of marriage, romance or identity, everywhere:
   headline, on-screen lines, caption, X and Threads text, hashtags. The rest
   of the story runs as normal (release, price, platforms, features, sales); a
   feature list carries it in its general form («خيارات العلاقات»، «نظام
   الزواج»), and when the general form is the whole news (an update adding
   romance options) it is reported in that form. Footage: shots that do not
   show it explicitly, as with the no-gore rule. General, never false: never
   swap in a different specific detail, never deny it. A ban or refused rating
   in the region quotes the authority's own wording («محتوى لا يتوافق مع معايير
   التصنيف المحلية») and adds nothing, never a different reason than the real one.
2. Evolution and religiously sensitive themes (Ancestors and the like): neutral
   and factual, a description of the product attributed to the developer
   («تدور اللعبة حول... حسب وصف الاستوديو»). Never sounding for or against; no
   first person and no claim stated as fact (not «أسلافنا», not «رحلة الإنسان
   الأول»); if the theme must be named, «مستوحاة من نظرية التطور», no judgement.
   Headlines lead with the news (platforms, date, price, update), never the
   theme. Comments: no arguing about belief; a reply, when needed, only says we
   report game news, drafted for Mohammad as now. The same approach covers
   religion, politics and real-world conflicts depicted in games.
3. Every brief carries a "sensitive" line: none, or which rule applies and how
   the wording handles it, checked before the build. The grammar stage checks
   the final Arabic against 1 and 2 as a house rule.
4. Live posts stay as they are unless Mohammad asks.

Legal, piracy, hacking and leak-enforcement stories (advisor, 26 Oct 2026,
approved by Mohammad; his words, 11:30 Dubai: as an outlet aiming to be
official, we report unbiased and never promote or encourage illegal activity).
Covers takedowns, lawsuits, piracy, jailbreaks, cheats, hacks and leak
enforcement.
1. Neutral and factual: report what the company and the law did, attributed;
   no cheering for either side and no leaker's framing («نينتندو غاضبة»).
2. Never promote or encourage illegal activity: no how-to, no tool names
   beyond what the context needs, no tool links, and never the leaked or
   extracted material itself (not even blurred).
3. Sound: our channel music bed by default, not trailer sound (an exception to
   "Trailer sound is the default", 23 Oct).
4. Official footage only (the company's own trailers, art and clips).
5. The director check asks: neutral wording, nothing leaked or extracted on
   screen, no how-to, our bed.
First case: Nintendo's copyright takedowns of posts showing datamined Switch 2
content (26 Oct): verified against the Lumen database or a major outlet before
it runs as fact, otherwise تقرير attributed with «لم تعلّق نينتندو»; Peach large
on the first frame from official footage; preview to Mohammad before
scheduling. A weekend explainer on hacking, cheating, piracy and AI across all
major platforms follows as a first of its kind: outline and options to him
before building.

Variety (Mohammad, 5 Oct 2026, after a run of Witcher and RuneScape posts:
"I've been posting about it for a while now"): a game or series that went out
in the last few days does not come back in a shortlist unless there is real
news (a launch, a date, a big number, an official announcement), and a
slot's picks are spread across different games and publishers.

Come back with a ranked shortlist, not a summary of every item. For each
candidate give the verification status, and the template, background,
accent and label already chosen — then ask for his take. He supplies the
take and the art; everything else should be decided before he reads it.

Scout additive trial (28 Sep to 4 Oct 2026; prompt in
`notes/scout-optimize-prompt.md`, audit in
`notes/scout-source-audit-2026-09-28.md`). The scout's existing map is
unchanged; on top it reads platform feeds, Arabic outlets (IGN ME
Arabic, True Gaming, Saudi Gamer, VGA4A), Japanese feeds, and overnight
only Gulf official sources and store prices. Digests now carry a "From new
sources" heading at the end (sweep it like the rest), "Outlet report"
where no primary was found (verify before use), and AGE labels from the
primary's time. Its no-refile ledger starts incomplete (Sep 21 to 22
missing), so refiles can still slip through in the first days. Store
prices come in the currency the store returns (Xbox and PS Store UAE in
USD, Xbox Saudi in SAR); never convert. The trial report arrives in the
digest inbox on or after 5 Oct.

## Wider monitoring: anime, mobile, football (advisor, 21 Oct 2026, agreed with Mohammad)

Principle: no genre quotas and no targets. The aim is that the watch sees
everything that matters to Gulf players; whether a story runs is decided by its
news value, as now.

1. New sources for the hourly watch and the scout, each as an official news
   page or feed (production confirms the URL is readable and dates its items;
   any that block automated reads are skipped and noted in
   `newsroom/watch_feeds.py`):
   - Anime-licensed and anime-style games: Bandai Namco Entertainment news,
     Aniplex games, Spike Chunsoft, Anime News Network (game news and press
     releases), Crunchyroll Games, Manga Productions (Saudi; Grendizer,
     regional angle).
   - HoYoverse: official news for Genshin Impact, Honkai: Star Rail and
     Zenless Zone Zero (version updates with trailers about every six weeks).
   - Mobile: PUBG Mobile, Free Fire (Garena), Call of Duty: Mobile, Supercell
     (Clash of Clans, Clash Royale, Brawl Stars), Roblox newsroom.
   - Football: EA SPORTS FC news, eFootball (Konami) news.
   Same rules as every source: verify against the primary, date from the first
   report; the variety rules and the verification gate apply.
2. Calendar (`newsroom/events.md`), confirmed dates only: HoYoverse version
   releases and their livestreams; Jump Festa (December) anime game reveals;
   Bandai Namco fighting game DLC waves when announced; EA FC and eFootball
   season updates.
3. Genre visibility, not quotas: every story file carries a "genre" field
   (shooter, open world, RPG, family, fighting, horror, racing, sports,
   strategy/sim, indie, live service/MMO, mobile, anime, industry/hardware,
   regional/esports; one primary, optional second, as `"genre": [primary,
   second]`). The Tuesday audit adds one line, stories per genre that week, for
   information only: it shows blind spots in the sources and never forces a
   story.
4. Presentation: anime-licensed and anime-style stories use the anime/stylised
   skin once the kits are past the pilot. Mobile stories follow the same quality
   bar: official footage, vertical-friendly shots, no filler. A routine event or
   patch without real news is not a story.

## Verify against primary sources

The digest is a lead sheet, not proof. Check claims independently before
they go on a card — it has had real errors (it named "Romancing SaGa 4
Destiny United" for what is *Romancing SaGa 3: Destinies Unite*).

Attribute a company's own numbers to the company: "Capcom says", not a
bare figure.

Re-check before queuing (Mohammad, 13 Oct 2026, review priority 2): any
تقرير, شائعة or تسريب story is searched again right before it goes to queue/,
and the approval note records what was found; a denial stops it. Since 18 Oct
every post goes through the pre-publish gate below ("Verification without
delay"). Every
correction is listed in `newsroom/corrections.md`, open until his decision
is written there.

Network: Mohammad opened the environment's network access on 23 Sep 2026.
Press sites, Steam, PlayStation Blog, Nintendo and their image CDNs now
load, so read primaries and fetch art directly. Google Patents, pbs.twimg.com
and news.xbox.com refuse automated requests at their end; use a press
article that carries the same image. Say plainly when something is
corroborated by search rather than read from the primary.

## Verification without delay (advisor, 18 Oct 2026, agreed with Mohammad)

Avoid corrections by verifying harder, never by waiting: news is never held
for official confirmation, and a change at the source after we publish is an
update, not a correction. From a review of the seven cases in
`newsroom/corrections.md`: one changed at the source after publishing (#4),
five carried information we could have caught before publishing (#2, #3, #5,
#6, #7), one was wording (#1).

The pre-publish gate (fast, two exits, never a wait):
1. Before every post, check all sources for the latest: the primary if one
   exists (publisher, platform holder, store page, the company's own post),
   the outlets that reported it, and a news search for a denial, update or
   new date. Time box: 10 minutes for normal news, 5 for the breaking lane.
   The approval note records what was checked and when (`gate HH:MMZ: ...`).
2. Exit A, confirmed: the primary confirms every fact on screen. Publish as
   جديد or رسمي. Dates, times, prices, deadlines and figures come from the
   primary itself, never from an outlet or aggregator; if the publisher and
   a store disagree, use the publisher's and state the time zone.
3. Exit B, not yet confirmed: no primary within the time box, but the story
   is reported. Publish now, labelled on the ladder: تقرير (a credible
   outlet reports it), تسريب (leaked material), شائعة (anonymous or social
   claims). The text names who reports it and carries «لم تؤكد [الشركة]
   الخبر بعد». Never wait for official confirmation to publish.
4. Read the whole primary when there is one: look for "Update",
   "Correction", "Editor's note" or a changed date on the page, and compare
   a chart against its text when both exist.
5. Queued ahead: a post queued more than six hours ahead goes through the
   gate again within the hour before it publishes; a dated story built more
   than 12 hours before its slot is rechecked in full.
6. Production may delete its own scheduled, unpublished post in Postiz when
   the gate fails, then requeue the fixed or relabelled version with a
   preview to Mohammad. Published posts are deleted only by Mohammad.

Updates, not corrections:
7. When the source changes after we publish (official confirmation of a
   تقرير, a denial, an extension, a new date, a clarification, the source's
   own fix), the follow-up is an update post: chip تحديث, or رسمي when it
   confirms an earlier تقرير; what the source now says, attributed; no
   "correction" wording. The original stays unless Mohammad deletes it.
8. Honesty boundary: an update never states or implies that the source
   changed when the error was ours alone (a misread figure, a wrong name, a
   translation slip, a change at the source that we missed before posting).
   Those are fixed by deleting and reposting within the first hour; after
   that, Mohammad decides.
9. Each case gets a line in `newsroom/corrections.md` with its cause (gate
   skipped, secondary used for a primary fact, primary read incompletely,
   could not pull, long build-to-publish gap, source changed) and the
   control that covers it, reviewed at the Tuesday audit.
10. Open cases become update posts or replies under rule 7, each with
    Mohammad's go: #2 Xbox's denial, #5 trial extended to 20 Oct, #6
    Activision's 23 Oct with the US time note, #7 Blizzard moved the test to
    21 Oct; #4 is already covered by the 17 Oct follow-up.
This replaces the narrower queue-time re-check of 13 Oct (reports, leaks and
rumours only): the gate runs on every post.

## Newsroom workflow (Mohammad, 2 Oct 2026)

After reviewing an outside newsroom brief, he approved these additions;
the detail is in `newsroom/README.md`. They add to the rules above and
change nothing already in Postiz.
- Story ledger, `newsroom/stories/` via `newsroom/ledger.py`: run `find`
  before shortlisting (a hit is an update, follow-up or duplicate, never
  a new story), keep each story's source chain, claims with their status,
  drafts and versions there, and `sync` after queuing.
- Every shortlisted story reaches him as a short approval card
  (`ledger.py card`): source, ✓ and ? claims, why it matters, lane, chip,
  time and text per account, media, what changed. "Source?" gets the
  primary, the original reporter and the exact claim.
- Preflight in dxb-queue: `publish.py` refuses any folder that fails
  `.github/scripts/preflight.py` (account, future time, text rules, video
  Instagram accepts, and an approval marker matching the folder). The
  marker is written with `preflight.py approve` only after his "go" for
  that version; any later edit needs his eyes again.
- Verification rules, the corrections routine, the events calendar
  (`newsroom/events.md`, confirmed dates only), the experiments log and
  the capability list live in `newsroom/`. Scout changes wait for the
  trial report (`notes/scout-proposals-2026-10-05.md`).
- Not adopted: the brief's colours, a points-based priority score,
  5-minute polling, Instagram carousels. Still his call: X first and the
  Reel later for breaking Digital Lounge news (today X and Instagram post
  together), and text-only DXB-KNIGHT posts when art is not ready (today
  every post carries a card).

## Editorial and director skills (Mohammad, 24 Oct 2026)

Two skills are the judgement layer on top of the repo rules: load
`games-news-editor` for every triage, ranking and scheduling decision (sweeps,
review slots, the hourly watch, the rolling queue, report spacing and gaps),
and `reel-director` for every brief, build and review (shot lists, sound,
framing, pacing, the director QA). CLAUDE.md and STYLE.md stay the authority
on exact numbers and wording; where a skill and a repo rule differ, the repo
rule wins and the difference is raised with Mohammad.

## Mohammad's inbox (advisor, 24 Oct 2026, agreed with Mohammad)

Anything that needs Mohammad goes to his inbox page, not only into the chat,
so it never gets buried while work continues:
https://claude.ai/artifact/AwcHX88eyTrUAL9pc4j4AW
1. What goes in: previews needing his OK, debate pieces and first-of-their-kind
   formats (options first), questions production cannot settle, decisions with
   a deadline, memos waiting for his reply, and short heads-ups he should know
   (failures, a dropped story, a correction). Routine news still runs end to
   end without him.
2. Posting (ArtifactData, collection `items`, one document per item, id
   `prod-YYYYMMDD-short-name`): `from` "production"; `kind` "approval",
   "decision", "question" or "fyi"; `title` (one line, what is needed); `body`
   (the context in a few lines, Arabic or English); `options` (button labels;
   approval defaults to Approve / Reject, fyi to Seen); optional `deadline`
   (ISO time a default kicks in) and `default_action`; optional `link` (a
   strip, a Reel, a Publer post); `created_at`; `status` "open". Then a push
   notification with the title, so his phone shows it.
3. Answers: read the inbox at every hourly watch, before any deadline and
   whenever a story is finished. An item with status "answered" carries
   `answer.choice` and `answer.note`: act on it, then update the item to
   status "done" with `outcome` (one line on what was done), the write pinned
   to the version read. No answer by the deadline: apply `default_action` and
   mark it done with outcome "default applied".
4. Tidy: one item per decision, never a repeat of an item still open; done
   items older than 14 days are deleted; no tokens, IDs or private data in an
   item. Items from the advisor (`from` "advisor") are his; production only
   reads them.
5. Complete cards (advisor, 24 Oct 2026, approved by Mohammad in the inbox):
   he decides from the card alone, without opening links, chats or the repo.
   Every card carries `summary` (one line, what he is deciding), `body` (the
   facts that matter), the thing itself embedded (a Reel or draft: the mp4, or
   a cut under 20 MB, uploaded to the inbox's asset store with its id in
   `video`; frames or a strip: up to 6 image ids in `images`; text to approve:
   the exact text in `memo` with `memo_label`), `options` as objects
   `{label, effect}` saying what each tap does, and `deadline` and
   `default_action` as before. A link is an extra, never the only way to see
   the content. Upload: read the inbox once with the Artifact tool, then
   publish to its URL with `asset: true` and the file; store the returned ids.
   Advisor memos arrive as items `from` "advisor", `to` "production": when he
   approves one, production applies it as if he had pasted it, records it here
   and in STYLE.md, and marks the item done; a change or note is followed.

6. Status board (advisor, 25 Oct 2026, approved by Mohammad, 19:49 Dubai). The inbox page has a
   Status tab built from the cards. On every card addressed to production and every production card
   Mohammad has answered: when work starts, set `picked_up_at` (ISO time) and `progress` (one short
   line: "building the Reel", "waiting on render", "checking the source"); update `progress` when the
   step changes; when finished, status "done", `outcome` and `updated_at`; when production decides not
   to do it, status "done" with an outcome saying why. A card answered or sent more than 30 minutes ago
   without `picked_up_at` shows in red as "not acknowledged". The hourly watch's inbox step sets these.

## Delegation (Mohammad, 5 Oct 2026)

To save tokens the main session acts as the editor and hands repeated
production work to cheaper subagents (sonnet or haiku) using the task cards
in `newsroom/delegation.md`: digest reading, footage fetching, renders,
snap and phone copies, drafts and preflight, grammar review, publish checks
and housekeeping, and, once he has said "go", the publishing steps. He talks
only to the main session, which keeps story choice, verification, the Arabic
writing, judging frames and everything said to him, and hands work off in
parallel so it can move to the next point. Nothing is queued without his "go".

## No em dashes

Mohammad does not use the em dash. Not in post text, not in card copy,
not in a kicker. Use a comma, a full stop or the middot the footer
already uses. This applies to anything that carries his name, not just
the words he writes himself.

## The post text and the card never say the same thing

The card carries the detail. The post text is the hook that makes someone
stop and open it. Never paste the card copy into the post, or a version of
it — if the post already tells the story, the card is decoration and there
is no reason to look at it.

Write the post for attention and tone: the drama, the stakes, the reason to
care. Leave every fact, quote, number and name to the card. If a line could
sit in either, it belongs in the card.

## Post text: no mould (Mohammad, 24 Sep 2026)

By 24 Sep every fast post had the same four beats: hook line, "X says"
facts, a caveat ("The catch:"), a closing question. Read in a row on the
timeline they looked templated. Pick the shape per story instead:

- One line: out-now posts and dates. The card carries the rest.
  "BeamNG.drive hits PS5 on October 19. No mods at launch."
- Number first: when the figure is the story. "$399.99. No game included."
- Quote first: when someone said something sharp, let the quote lead.
- His take first: on voiced posts his view opens, the facts follow.
- Full breakdown: only when the detail is the point (refund rules,
  eligibility windows).

Closing questions are occasional, only when readers would genuinely want
to answer; most posts end on a fact or his view. Attribute once, where it
reads naturally, not "X says" in every paragraph. Never reuse an opener or
closer within the same evening, and let length vary from one line to a
few paragraphs. Before queuing a batch, read the posts back to back and
rewrite any two that share a shape.

## Short X posts on both accounts (Mohammad, 5 Oct 2026)

X showed impressions but no plays, likes or follows on Digital Lounge, and
people scrolled past. From 5 Oct every X post, DXB-KNIGHT and Digital
Lounge alike, is short: one or two lines that hook (the stake, the number,
the quote), and the video or card carries the rest. Digital Lounge's full
story stays in the Reel and the Instagram caption; Threads takes the short
X text. On DXB-KNIGHT this tightens the fast lane below: the post still
attributes its claim ("per Digital Foundry"), in the fewest words.
Vertical Reels stay on X: X now plays 9:16 large in the timeline and in its
swipe-through video feed (his Fandom example, 5 Oct), so no 16:9 cut. The
first frame carries a readable title because X autoplays muted. A one-week
test from the RuneScape series post (4 Oct, 20:45), judged about 11 Oct in
`newsroom/experiments.md`.

## Two lanes: fast and card

The fast lane posts breaking news within minutes, on `templates/fast.py`:
the image or clip full bleed in a 1600x900 (16:9) frame, a chip on the
media, an accent rule, and the same footer as every full card (crest and
DXB-KNIGHT left, source centre, date right). No headline and no kicker on
the card. Here the post text carries the facts, attributed ("Xbox says",
"per Windows Central"), because the card deliberately does not. Speed never
excuses an unverified claim: name the source in the text.

The card lane is the considered `flex.py` card with his take, posted later
as a reply to his own fast post so it inherits that post's audience.
A reply goes out with its post: job.json takes `"thread": [{"content":
"<p>..</p>", "media": ["reply.mp4"]}]` and `publish.py` sends each item as a
reply under the post (27 Sep 2026; the first, the tap-to-pay explainer
under the 18:30 DXB-KNIGHT post, appeared on X as a reply). A post already in Postiz cannot gain a
reply from here; he deletes it and the post goes again with its thread. The
"post text and card never say the same thing" rule applies to this lane.

Alt text is dropped (Mohammad, 23 Sep 2026). The Postiz Public API has no
alt-text field, so it never reached X; the composer is the only route and
not worth the manual step. Do not write alt text into job.json.

## Chips: agreed 23 Sep 2026

Fast-lane chips say what happened and how sure we are. Card-lane chips say
what kind of piece it is. Background already says whose voice it is, so no
chip repeats that.

- Fast: BREAKING, JUST IN, OFFICIAL, REPORT, LEAK, RUMOUR, FIRST LOOK,
  OUT NOW, DELAYED, PRICE, HANDS ON. `fast.py` refuses anything else.
  HANDS ON (Mohammad, 26 Sep 2026) is for a fast post led by his own
  play time, when no news chip fits and JUST IN would oversell it.
- Card: HANDS ON, OPINION, INTERVIEW, ANALYSIS, STATS, MILESTONE, REVIEWS,
  UPDATE, EVENT, RECAP, VS.
- GULF (gold) rides beside either, on `single` and `fast` only. Use it for
  stories that are about the region (Gulf studios, events, pricing, retail).
  Do not angle a global launch on whether it reaches the Gulf: Mohammad
  judges that by the company's real regional presence, not the launch list.

The chip never claims more certainty than the sourcing has: RUMOUR, REPORT,
OFFICIAL is a ladder. BREAKING is for unscheduled, major, confirmed news,
once or twice a week at most; most news is JUST IN. Retired: NEWS, and
topic words used as chips (SWITCH 2, MAP, DESIGN, SAID, a city name).

Arabic chips (Mohammad, 26 Sep 2026). Use the pick; switch to the
alternative in brackets only when he asks for it on a given story.

- Fast: عاجل BREAKING, جديد JUST IN (الآن, وصل للتو), رسمي OFFICIAL,
  تقرير REPORT (حسب تقارير), تسريب LEAK, شائعة RUMOUR (إشاعة),
  نظرة أولى FIRST LOOK (أول نظرة), متوفر الآن OUT NOW (متاح الآن, صدر),
  تأجيل DELAYED (مؤجل), السعر PRICE (سعر), نظرة أولى HANDS ON (انطباعات).
- Card: نظرة أولى HANDS ON (انطباعات), رأي OPINION, حوار INTERVIEW (مقابلة),
  تحليل ANALYSIS, أرقام STATS (إحصائيات), إنجاز MILESTONE (رقم قياسي),
  التقييمات REVIEWS (المراجعات), تحديث UPDATE, فعالية EVENT (حدث),
  ملخص RECAP, مقارنة VS (ضد).
- No GULF chip on Arabic. A regional story names its country instead:
  الإمارات, السعودية, قطر, الكويت, البحرين, عُمان, and the wider Arab world
  the same way (مصر, الأردن, المغرب). Bright indigo `#5552E0` with ink
  text, beside the news chip, never azure. Same test as GULF: only when
  the country is the story, not because a global launch includes it.
- The same ladder and BREAKING rule apply: عاجل is rare, most news is جديد.
- HANDS ON is نظرة أولى (Mohammad, 26 Sep 2026), better for an early look
  or preview; تجربة reads as a test or trial, and انطباعات is the fallback.
  It shares the word with FIRST LOOK, which is fine: both are an early look.

In every sweep, each shortlisted item comes with its lane and chip already
chosen. Minutes old and the image tells it: fast. Needs his take, numbers
or context: card. Big: fast now, card later as a reply to the fast post.

## Postiz and the Business Suite batches (22 Oct 2026, history)

Postiz shut down on 22 Oct 2026 after the breach at its host; publish.yml in
dxb-queue carries `if: false` and the Postiz connector and API are not used.
The Business Suite batches that bridged the gap ended when Publer took over the
same day. Both memos are in `notes/standing-history.md`.

## Publishing through Publer (advisor, 22 and 23 Oct 2026, agreed with Mohammad)

Replaces the Business Suite batches above. Postiz stays off; its secret and
code are removed after one clean day on Publer.
- 22 Oct: Publer (Business plan, workspace "The Digi-Lounge", shown in UTC+4)
  holds Digital Lounge Instagram, Threads and X, and production posts through
  the connector. Every Reel goes to all three at the same minute: Instagram as
  a Reel with the caption, X with the short text, Threads with the Threads
  text. One `submit_publer_posts` call per account (a call shares one account
  set); the video is uploaded once from its public dxb-assets URL and reused.
  The gate runs before scheduling, spacing and variety as in "Constant
  coverage". After each slot all three are checked as Published; a failed
  post is rescheduled once, then reported with Publer's reason. Story files
  say "scheduled in Publer HH:MMZ" with the platforms; the format ledger takes
  the slot. No IDs or tokens in public files or logs.
  First post (MW4 maps, 15:30Z): Instagram and X published; Threads failed and
  every Threads action returned "Authentication failed. Please reauthorize
  this account" until Mohammad reconnected Threads a second time (16:51Z);
  from then all three posted. The Publer posting and read tools are on the
  allow list in `.claude/settings.json`; the delete tools stay on ask.
- 23 Oct, using Publer further:
  1. Labels on every post: template (trailer, split, clipcard, numbers, ...),
     skin (house, scifi, fantasy), sound (trailer, voiced-subtitled, our bed)
     and genre from the story file. `list_publer_labels` first, and reuse the
     existing spelling (a label is created the first time a post uses it).
  2. The advisor pulls last week's views, reach and shares per Reel from
     Publer each Tuesday and fills the format ledger's views column; Mohammad
     no longer sends numbers by hand.
  3. Weekend windows. Publer's best times for Instagram (last 30 days, read
     23 Oct): Thursday 18:00 (score 16,609) and Friday 20:00 (10,203) lead,
     then Wednesday 12:00 (6,560). The workspace shows times in UTC+4, Dubai.
     The day's strongest non-urgent Reels are held for Thursday 17:00 to 21:00
     and Friday 19:00 to 22:00 Dubai. Breaking news and fresh reveals still go
     at once; constant coverage unchanged.
  4. Source in a follow-up: on X one reply under the post with the source link
     (`follow_up_comments`); on Instagram one comment with the source in a
     short Arabic line («المصدر: ...»), no link; on Threads the source line
     stays in the text.
  5. Custom Reel cover, test first: a designed 3:4 cover (headline, the game's
     key art, our chip) as the Reel's thumbnail. Publer's API takes it as an
     extra entry in `media[].thumbnails` with `default_thumbnail`, but the
     connector's submit tool does not pass media thumbnails (network_options
     cannot override media), so the test needs the Publer API key for covers
     only, or Mohammad setting covers by hand in the app for key Reels. Once
     covers work, the grid-tile rules move from the first frame to the cover.
  6. Trial Reels for pilots only (game-skin kits, mood music, new templates),
     `trial_reel: "MANUAL"`; news never goes out as a trial.
  7. Location tag on Instagram Reels, "Dubai, United Arab Emirates", for two
     weeks; reach is compared at that audit, kept or dropped.
  8. Mohammad switches on Publer's email alerts for failed posts (Settings,
     Notifications); production still confirms each slot.
  9. Not used: RSS automation, AI captions, recycling or recurring news posts,
     spintax, AutoShare.
  10. Waiting on Mohammad: which Arabic games outlets to track as competitors,
      and a Linkie (link in bio) page with source links per Reel.

## Publishing

Cards render to `cards/YYYY-MM/`, source art to `live/YYYY-MM-DD/`.

Every time a schedule is shown (drafts, confirmations, what is queued),
each post names its account: DXB-KNIGHT, Digital Lounge, or both
(Mohammad, 27 Sep 2026). Never a bare time and title.

Approval is not a go (Mohammad, 28 Sep 2026): "as soon as possible" means
schedule tighter, not post now. Every post, Digital Lounge included, goes
to the queue only with a time he has seen and a "go" from him; propose
the times with the drafts. (On 28 Sep a PS5 Pro set went out immediately
on a misread and he deleted it.)

Silence on a built batch (Mohammad, 12 Oct 2026: "if I didn't say go
half an hour before the first draft time go ahead immediately"). Once he
has asked for a batch to be built and its drafts and times are in front of
him, no reply by 30 minutes before the first proposed time is his go: the
batch is approved (note "go: no reply 30 minutes before first time") and
queued at once, retimed to the next half hour if a slot has passed. It
covers only batches he asked for, never a bare shortlist, a story he
turned down, or DXB-KNIGHT.

Rolling queue (Mohammad, 13 Oct 2026, in two steps: "rolling with 15
minute", then, after the first story still waited on his pick: "putting it
on me will cause delays... sharing a list and picking a number highlights
priority but doesn't mean we remain idle. We will work on a queue system
with phases and agents handling parts so we ensure organic updating and not
just spamming reels"). From 13 Oct evening Digital Lounge runs as a queue:
- Phases, each with its own agent: intake (the hourly watch and the scout
  digests feed every candidate into the queue), verify (the Verifier finds
  the primary and sets the chip on the ladder), rank (the editor orders by
  news value, freshness and variety), build (footage, our graphics, the
  Arabic, render, drafts, preflight; one render at a time, the rest
  overlapping), schedule (the next free slot under the cadence below),
  publish check, strip and ledger.
- His pick is priority, not permission. The ranked list goes to him at the
  review slots as information; a number moves a story to the front, "skip
  N" drops it, "hold" holds. No reply means the queue runs as ranked. The
  head start applies to every verified story, not only the top two.
- Each finished story is queued for the next quarter hour at least 15
  minutes out (approval note "go: rolling queue; preview sent HH:MMZ") and
  its preview goes to him at the same time; "hold" or "fix" in that window
  stops it. Once in Postiz, only he can pull it.
- Cadence: spacing and gaps, no daily cap (see "Constant coverage" below,
  16 Oct 2026; it replaced the 13 Oct numbers of 30 minutes by day, 90
  overnight and about 12 a day). No two consecutive posts on the same game
  or publisher; no more than two in a row in the same format; reports and
  rumours never more than one post in three, each re-checked right before
  queuing, a denial stops it.
- The quality steps do not change: brief, shot sheet, draft render, frame
  checks, both Arabic skills, grammar review, DeepL back-check, preflight.
- Unchanged: a story he turned down never posts; the breaking lane keeps
  its own rules below and jumps the queue; DXB-KNIGHT stays on hold. The
  30-minute silence rule above still covers a batch he asks for by hand.
The GTA 6 PC report was the first story under this model: 42 minutes from
his pick to queue; the Laufey box followed 75 minutes later with no pick.

Breaking lane (Mohammad, 11 Oct 2026: "even if I'm not available, you
either can ping me, and if I don't reply, you can take like 15 minutes and
basically post it. And this is only for new news or breaking news"). An
hourly watcher reads the official sources and a separate verifier checks
what is new (`newsroom/delegation.md`, "Hourly watch"). For a verified,
official, new or breaking Digital Lounge story, the drafts are built, he is
pinged, and if he has not replied 15 minutes later the post is queued with
the approval note "auto-go: no reply in 15 minutes". This is the only
exception to "approval is not a go". Never for rumours, leaks, single-outlet
reports, routine items, DXB-KNIGHT or anything he turned down; auto-posting
runs round the clock from 16 Oct 2026 (was 08:00 to 23:00 Dubai; see
"Overnight cadence" below), at most three in any 24 hours.

Expansion passes and DLC go out on announcement (Mohammad, 15 Oct 2026:
"Expansion pass and these kind of news can be published fast as soon as
it's announced. There is an official trailer"). When a publisher officially
announces an expansion pass, a DLC wave, a season or a similar add-on, and
there is an official trailer or footage, the story is built at once and
queued at the next quarter hour at least 15 minutes out, its preview sent at
the same time; his message is the go for this kind, so it does not wait for
a review slot or a pick. It keeps the spacing of "Constant coverage" below.
Rumoured or leaked DLC stays on the normal ladder. First used on Fire
Emblem: Fortune's Weave's Expansion Pass, 15 Oct.

Overnight cadence (advisor, 16 Oct 2026, agreed with Mohammad at 02:50
Dubai). Mohammad now reads the Digital Lounge feed as a viewer and deletes
anything he does not like, so there is a check after publishing as well as
before it, and the night can be used more.
1. Quiet-hours work. Whenever no story is being built, in this order (the
   idle card in `newsroom/delegation.md`):
   a. Fetch footage and warm the picture cache (`reel.warm_cache`) for every
      dated story on the next day's calendar: launches, embargo lifts,
      Famitsu Thursday, shows.
   b. Pre-build a shell Reel for anything due at a known time: footage, shot
      list, strip layout and the Arabic for everything except the final
      fact, so only the fact, the text pass and the encode remain when the
      news lands.
   c. Bank evergreen pieces (Ocarina episodes, retro, list, explainer), each
      ready to queue.
2. Overnight posting uses real news. Every verified story that lands
   overnight is queued at the overnight spacing (at least 60 minutes from
   00:00 to 08:00 since 16 Oct; was 90 from 23:00), not only evergreen pieces.
   The strongest pieces of the day still go to 08:00 to 21:00. Morning queues
   are spread out: no more than one post per 30 minutes, and none bunched
   before 08:00 because the night was left empty.
3. Breaking-lane auto-go runs round the clock (was 08:00 to 23:00) for
   verified, official, new or breaking news only. Rumours, leaks and
   single-outlet reports never auto-go at any hour. The cap stays at three
   auto-go posts a day, counted over 24 hours.
4. Morning digest. By 07:30 Dubai, one message to Mohammad listing every post
   published since 23:00, one line each (time, title, template, chip) with
   the path of its strip in `cards/`, so his check takes two minutes.
5. Deleting and correcting. He may delete a post he dislikes at any time. A
   wrong fact found more than an hour after publishing gets a correction Reel
   (as with Alinea) rather than a silent deletion; the corrections routine in
   `newsroom/corrections.md` is unchanged.

Constant coverage (advisor, 16 Oct 2026; Mohammad: "I want constant
coverage"). Replaces the daily cap of about 12 posts and items 1 to 4 of
the "empty afternoon" fix sent earlier that day. On 16 Oct nothing posted
from 12:00 to 18:45 Dubai while eleven finished Reels waited for Saturday
and Sunday.
1. No daily cap. The limits are spacing and gaps, in Dubai time:
   - Minimum spacing: 30 minutes between posts from 08:00 to 24:00, 60
     minutes from 00:00 to 08:00 (by the hour of the later post). Breaking
     news may break the spacing, as before.
   - Maximum gap: never more than 60 minutes without a post from 08:00 to
     24:00, never more than 2 hours from 00:00 to 08:00 (by the hour the gap
     starts).
2. A finished Reel takes the earliest free slot under the spacing rule. It
   is never held for a later day unless the approval note gives a reason
   (embargo, dated launch, Mohammad's hold). An «الطريق إلى Ocarina» episode
   is dated by its «باقي N يومًا» count.
3. Gap filling, in order, when no new story is ready for the next slot: a
   verified story still in the build queue (built first), then a banked
   evergreen piece (Ocarina, retro, list, explainer). The bank keeps at least
   6 ready Reels at all times; quiet hours top it up.
4. Gap alarm: the hourly watch runs `python3 templates/formats.py gaps 2`
   (from the format ledger's slots); if a gap or spacing rule would break in
   the next two hours its commit says so, and the next finished Reel or a
   banked piece is queued into it. `formats.py gaps <hours> [start UTC]`
   checks any window.
5. Unchanged: variety rules (no two in a row on one game or publisher, no
   third in a row on one template, card-led at most one in three over six,
   four per template per Dubai day; `formats.py check <fmt> [slot UTC]` now
   counts the Dubai day and reads the ledger in time order up to the slot),
   reports and rumours at most one post in three, re-check before queuing,
   all quality steps.
6. 16 Oct: the Reels queued for 17 and 18 Oct moved forward with his go
   (deleted in Postiz and requeued, note "go: Mohammad, constant coverage
   16 Oct"): nine into 18:45 to 23:00 Dubai, Nintendo repair prices and
   Where the Seeds Fall to 08:00 and 08:30 Saturday. Asked that evening,
   he put the gap rule over the four-per-template cap for that one night
   (trailers and splits had already reached it).
7. 17 Oct, 14:30 Dubai: trailer, split and clipcard had each reached four on
   Saturday and the card-led window was full, so nothing could fill 14:30 to
   00:00 Dubai. Asked, he said "Fill it": for that afternoon the gap rule
   wins over the per-template caps (four a day, card-led two in six). No
   third in a row on one template, no two in a row on one game or publisher,
   and reports at most one in three still hold.
8. 23 Oct, about 14:20Z (18:20 Dubai): trailer, split, clipcard, comparison and
   quote had reached four, and the card-led window was full, so 19:30 to 24:00
   Dubai could not be filled. Asked, he said "Fill it tonight, gap rule over
   caps": for that evening the gap rule wins over the per-template and card-led
   caps; no third in a row on one template, no two in a row on one game or
   publisher, and reports at most one in three still hold.
9. 24 Oct, inbox 10:19Z (Saturday, news thin; trailer and split at their caps,
   card-led window full): "Fill it tonight". Same terms as 8, until 24:00 Dubai.

Posting is irreversible: pushing `queue/**` to *any* branch of dxb-queue
fires the publisher, because `publish.yml` has no branch filter. Never
queue without explicit say-so, and dry-run `publish.py` with `DRY_RUN=1`
first to confirm which folders will post.
Since 2 Oct 2026 the dry run also runs preflight, so a folder without a
current approval marker shows as FAILED there before anything is pushed.
After a batch's first slot, check its posts read PUBLISHED in Postiz
(`postsListTool`), not just that the receipts came back: a receipt only
means Postiz accepted the post. On 3 Oct 2026 ten due posts sat in QUEUE
for 40 minutes and went out only when Mohammad refreshed the posts view
in the Postiz app, and the 07:00 Steam Deck X post ended in ERROR.
Posted folders keep only job.json and receipt.json (Mohammad, 5 Oct 2026):
once a batch's receipts are in, its media is removed from dxb-queue in the
next commit (the Reels stay in dxb-assets). The publish checkout had grown
to 12.5 minutes with 4.4 GB of posted video; never strip a folder that has
no receipt.json, and never push while a publish run is in progress.
A failed publish run is never re-run (10 Oct 2026): "Re-run failed jobs"
checks out the original commit, from before the receipts were recorded,
so it would post every folder of the batch again. Pull, dry-run on the
latest main to see which folders still lack a receipt, then start a fresh
run with workflow_dispatch on main.
A weekly workflow in dxb-queue (`.github/workflows/cleanup.yml`, Sunday
03:00 Dubai, also runnable by hand) does the same as a backstop; it shares
the publisher's concurrency group, so it never runs during a publish.
