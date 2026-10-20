# Digital Lounge: the rules in force (20 Oct 2026)

One page of what applies today. CLAUDE.md is the full, dated history and wins
on detail; each line here names its section there. Anything listed under
"Not in force" is history, not a rule. Update this page in the same commit
as any change to a rule (Mohammad, 13 Oct 2026, review priority 1).

## Accounts

- **Live:** Digital Lounge on X, Instagram and Threads. Every story goes to all
  three at the same time with the same Reel (CLAUDE.md "Threads",
  "Instagram").
- **The Game Awards, 10 Dec:** a YouTube co-stream with Mohammad's voice, no
  face, OBS on a laptop; brand package as OBS scenes by 31 Oct, two unlisted
  dry runs in November, countdown Reels from 3 Dec, clip Reels from 06:30
  Friday; judged at the 16 Dec audit (CLAUDE.md "The Game Awards co-stream").
- **On hold:** DXB-KNIGHT, option B from 11 Oct. There is no routine
  production; a hero piece or a take is built only when Mohammad brings one
  ("Two accounts").

## Editorial

- **Scope:** games only, the whole slate, regional stories when they are the
  story. Outlet voice, no first person ("Settled 26 Sep").
- **Sources:**
  - Verify every claim against its primary, and attribute a company's
    numbers to the company.
  - Outlets are leads, not proof. Ten articles citing one report are one
    source.
  - People take their role at first mention, on screen and in text
    («المخرج سولفريم ليانغ»), never a bare name, above all when the name is
    also a game or studio. X and Threads name the source of every quote,
    report, rumour, leak or interview in a few words («لموقع PCGamesN»).
    Reader questions about a source get the primary: outlet, date and link
    (no link on Instagram) (17 Oct).
  - A story's age is its first report anywhere, not the relay's. Arabic
    outlets rewrite a day or two late: date from the origin, and drop a story
    over 24 hours old at its origin unless something new has landed (17 Oct).
  - Pre-publish gate on every post (18 Oct): primary, reporting outlets and a
    news search for a denial or new date, 10 minutes (5 on the breaking lane),
    recorded in the approval note. Confirmed by the primary: جديد or رسمي, with
    dates, prices and figures from the primary only (publisher over store, time
    zone stated). Not confirmed: publish now as تقرير / تسريب / شائعة with who
    reports it and «لم تؤكد [الشركة] الخبر بعد»; never wait. Read the whole
    primary (Update, Editor's note, chart against text). Queued over 6 h ahead:
    gate again in the last hour; built over 12 h before its slot: full recheck.
  - A change at the source after we publish is an update (تحديث, or رسمي
    confirming a تقرير), never "correction" wording; our own slips are deleted
    and reposted within the hour, then Mohammad decides. Each case is logged in
    corrections.md with cause and control.
  - (README §4; "Verify against primary sources")
- **Chip ladder:** رسمي / تقرير / تسريب / شائعة, with جديد for most news and
  عاجل rarely.
  - The chip matches the weakest claim, and the headline is never louder
    than the source.
  - Rumours and leaks are welcome when labelled; harmful or explicit
    material is skipped ("Speculation for reach").
- **Re-check before queuing:** any تقرير, شائعة or تسريب is searched again just
  before it is queued, and the approval note records the result
  (newsroom/corrections.md).
- **Corrections:** Mohammad is told at once and decides; live posts change
  only on his word. Every case is listed in newsroom/corrections.md.
- **Stand-in footage is named on screen.** When the footage is not of the
  story's subject, credit it with
  `reel(..., credits=[(first, last, 'لقطات من Fortnite')])`.

## Arabic

- **Process, every batch:**
  1. Load both skills fresh and read the house glossary.
  2. Write with arabic-games-film-editor.
  3. Run the arabic-grammar-review stage.
  4. DeepL both ways: the back-check (meaning), and a forward pass of the
     whole story in one piece (never sentence by sentence), read against
     ours; stock phrases, retail terms, dates and prices also go phrased two
     to four ways in English to pick the term Arab readers expect;
     spell-check the pick and keep names to the house rules.
     Countable products take الكمية (حتى نفاد الكمية), bulk goods المخزون.
  - (CLAUDE.md "Arabic writing")
- **Names:**
  - Games, series and platforms stay in English.
  - Companies, studios, outlets and people are written in Arabic with the
    Latin in brackets at first mention, on screen too.
  - Say what an unfamiliar name is («استوديو…», «صانع المحتوى…»).
- **Direction:** every post, paragraph and on-screen line opens on an Arabic
  word. reel.py now stops when a wrapped headline or story line opens on
  Latin, a digit or a bracket (13 Oct).
- **Numbers and punctuation:**
  - Western digits.
  - The dirham symbol goes left of the price.
  - No em dashes anywhere.

## The Reel (templates/reel.py)

- **Frame:**
  - 9:16, footage full frame; nothing graphic.
  - Shots whose subject fits a vertical crop.
  - Enlargement capped at 2x; the standard picture finish on footage.
  - Source order: the publisher's vertical cut, then 4K, then 1080p.
  - Our own graphics sit on the moving numgfx ground, whose style rotates
    (waves, glow, wash, grid, blurred still) so consecutive numbers Reels
    differ, with the text area checked for contrast (14 Oct).
  - Numbers wear their game (20 Oct): a one-game card sits on its blurred
    key art (`still` ground) with its plated logo above the figure
    (`numgfx.put_logo`), so the grid tile shows logo, figure and headline;
    the accent is the theme nearest the game's palette, gold only for
    multi-game charts and milestones. A game with footage takes `clipcard`,
    not `numbers` (`formats.pick(..., footage=True)`); multi-game charts
    keep the living ground with each game's art beside its row.
  - A framed window on the ground plays a clip when footage exists, not a
    still (14 Oct).
- **Text:**
  - The chip and headline sit at the top for about 3.5 s; the first frame is
    the grid tile.
  - Grid tile (19 Oct): the chip row sits 60 px lower so Instagram's Reels
    icon never covers it, and nothing is drawn in the 140 px square at the
    top right of the 3:4 window (reel.py stops); the first frame carries no
    slate, title card or publisher text (`shotsheet` reads it and names the
    first clean frame) (CLAUDE.md "Grid tile").
  - Then 4 to 6 lines of the actual story: white Dubai Bold with an indigo
    outline, right-aligned, 1 to 3 visual lines each.
  - Each line stays up for its reading time (`read_secs`); the safe zone is
    x 96 to 910, y 285 to 1480.
  - Lines move to the top over a game's lower-third UI.
  - Hook first (14 Oct): the footage moves from frame one under the chip and
    headline, the credit line enters at 2 s, and the headline is a hook (a
    number, a question, the surprise), never a label.
  - The play mark, 48 px at 50%, sits top left in the safe zone for the whole
    Reel (14 Oct).
  - 12 to 20 s of story before the end card; four lines is normal, six only
    when needed; the brief states the total (14 Oct).
- **Sound:**
  - One continuous stretch of the trailer's own music, with voices allowed.
  - Our bed under stills, graphics or noisy stretches; never mute footage to
    add a bed.
  - Beds evolve (14 Oct): one motif, tempo and level, the arrangement
    changing every 8 bars with a one-bar crossfade (`sonic.ARRANGE`), so a
    long Reel's music moves without getting louder or busier; the cycle
    follows the news type (everyday, stats, launch, digest, breaking,
    hijaz; retro stays chip).
  - The jingle and end card always close the Reel; the card is 2 s (14 Oct).
- **Templates (14 Oct):** the template is chosen per story from
  templates/formats.py (`NEWS_MAP`): `trailer` (footage all the way, lines
  on the picture, no card), `split` (footage all the way plus a slim pinned
  fact strip), `clipcard` (footage, one card at the key beat, footage),
  `numbers` (our graphics only, when no footage shows the news; a game
  with footage takes `clipcard`, 20 Oct), and
  `comparison`, `quote`, `explainer`, `handson`, `retro`.
  - Footage first: a story with a trailer takes `trailer` or `split` before
    any card template.
  - One fact, one place: a fact is on a card or in a line, never both; over
    a card the line is at most one visual line of framing, or absent.
  - Every shot has a reason, written per line in the brief: what the viewer
    sees and why it shows that line.
  - Two families: footage-led (`trailer`, `split`, `clipcard`, `handson`,
    `comparison`) and card-led (`numbers`, `explainer`, `quote`, `retro`).
    No third in a row, and card-led at most one in three over the last six
    (`formats.py check`). Over a split strip a line is two visual lines at
    most.
- **Variety:**
  - Themes per story; band styles rotate through the ledger.
  - No more than two Reels in a row share a template.
  - The opening beat follows the template (`formats.OPENERS`, 14 Oct): quote
    on the quote, numbers on the number alone, edition on the hero item.
  - No template more than four times a day; a price story with more than
    three facts is never split; handson and edition are the only templates
    outside the 12 to 20 s target (advisor memos, 14 Oct evening).
  - New templates `stills` (footage-led, the last resort after every motion
    source: cut not panned, 3 s an image, 12 to 14 s) and `list` (card-led:
    N items on their own art, n/N cue, mosaic cover); `tribute` is a stills
    variant (no chip, no waves, grey lines, quiet end card); عاجل is a skin
    (crimson, breaking bed) on any template. NEWS_MAP carries about fifty
    kinds now (CLAUDE.md "Advisor memos, 14 Oct 2026 evening session");
    the brief starts from the advisor canvas scenario for the kind.
  - Something changes on screen every 3 to 4 s (reel.py stops on a pace
    warning unless the brief gives a reason), lines enter on cuts, the
    word-by-word reveal is for the key line only, and the last two seconds
    before the end card are a picture, never a card.
  - A still is never ten seconds alone: a second angle at 3.5 s, the one the
    line names; a store-page line gets the page as its shot (pageshot.py).
  - Stills push and pan at 4x the frame and scale down last, the finish after
    the downscale, so the motion is sub-pixel and does not judder (18 Oct;
    CLAUDE.md "Stills move smoothly").
  - On a split Reel the strip hides under a card; card type is 40 px or
    more; the ledger logs a split with a card as clipcard (14 Oct review).
  - A closing question only on stories readers argue about, never on a
    launch or a price.
  - Weekly Instagram views are recorded next to each Reel's template
    (`formats.py views`, Tuesday morning from Mohammad's numbers, 14 Oct).
  - Landing (14 Oct, first draft to Mohammad before use): `edition` (editions,
    bundles, limited consoles: press-render cut-outs drifting onto the living
    ground, then one composition frame with the price strip; card-led) and a
    subject-detecting `autofocus` (YOLOv8n, two keyframes per scene, crop
    window drawn on the shot sheet).
  - The retro sound is for on-this-day pieces only.
- **«الطريق إلى Ocarina» (19 Oct):** a mini documentary. The series intro
  opens and the same outro closes every episode; between them, material and
  sound built for the episode's subject (a character's reveal footage and
  art, the music piece itself, the mechanic N64 beside Switch 2, archive and
  figures for history, the official map for places). No shot and no audio
  stretch in two episodes: `notes/ocarina-series.md` keeps the ledger
  (CLAUDE.md "Mini documentary").
- **Web-style motion (pilot, 19 Oct):** HTML/CSS/JS pieces rendered frame by
  frame in headless Chromium, palette and Dubai: the outro first (two or
  three rotating variants) side by side with the current one for Mohammad's
  verdict, then an Ocarina map piece. Readable at phone size first; safe
  zone and reading pace apply; renders on the Mac once live; nothing
  replaces a current piece until he approves (CLAUDE.md "Web-style motion
  graphics").
- **Process:**
  1. A six-line brief (angle and hook kind, template and opening beat, cover,
     sound, key shot, total seconds).
  2. `shotsheet`.
  3. `draft`, then `strip`, looked at frame by frame.
  4. `final`, then `strip` again; the final strip and the shot sheet are
     committed to `cards/YYYY-MM/` as `<name>-strip.jpg` and
     `<name>-sheet.jpg` with the mp4 (14 Oct).
  - Render time (14 Oct): one real encode per Reel at medium/18, lossless
    intermediates, the picture pass cached per shot under uploads/cache,
    end-card masters joined by concat; the breaking lane renders on the
    `breaking` profile (no finish, veryfast/20, no draft); dated stories
    have their footage cached the evening before; seconds per stage go to
    `templates/assets/render-times.json`.
  - Render runner (20 Oct): routine renders go to GitHub Actions
    (`render.yml`, one job per `jobs/render/<name>.json`, run by
    `templates/render_job.py`; fonts from dxb-fonts through `FONTS_TOKEN`,
    never committed or logged). The job carries the focus judged on the
    sheet (`render_job.py focus` before the sheet). Tested on the Cyberpunk
    re-render (same length and text, 4 cores, 214 s a job) and reported to
    Mohammad; the container is the fallback. Advisor memo of 20 Oct: a
    runner Reel is held for his OK before it is scheduled; the container
    renders the next story at the same time and takes over a runner job that
    fails or passes 15 minutes; breaking stays on the container; both lanes
    log story, lane, queued, finished, render and setup minutes.
    Runner hold lifted (Mohammad, 20 Oct, about 17:17Z): runner Reels
    follow the normal rolling-queue rules.
  - (CLAUDE.md "Full-screen format", "Creative brief and formats")

## Platforms

- **X:** one or two lines that hook, with no hashtags; the Reel carries the
  story ("Short X posts").
- **Arabic-support stories:** kind `arabic`, split strip (الواجهة · الترجمة ·
  الدبلجة as they apply) and the chip «بالعربية» beside the news chip (14 Oct).
- **Instagram:**
  - Reels only; the same full-quality file as X.
  - Caption: a hook that differs from the headline, with the game's name and
    the news word in the first five words (14 Oct), then the full story,
    then exactly #ألعاب #أخبار_الألعاب plus two story tags.
  - Under 2200 characters, no links.
  - On an upload error, retry the same file once.
- **Threads:** the short X text, no hashtags, 500 characters at most.

## Timing and approval

- **When:**
  - Round the clock, earliest times first; the strongest pieces go in peak
    hours, 08:00 to 21:00 Dubai.
  - Review slots at 06:30, 10:00, 14:00 and 17:30. Famitsu goes out the
    moment it is published.
- **Approval:**
  - Nothing is queued without his go.
  - Rolling queue (13 Oct): his pick is priority, not permission. Every
    verified story is built in rank order and queued for the next quarter
    hour at least 15 minutes out, preview sent at the same time; "hold" or
    "fix" in that window stops it; "skip N" drops a story.
  - Constant coverage (16 Oct; replaces the 13 Oct cadence and the daily
    cap): no daily cap. Spacing at least 30 minutes 08:00 to 24:00 Dubai, 60
    minutes 00:00 to 08:00 (breaking news may break it); never more than 60
    minutes without a post 08:00 to 24:00, 2 hours 00:00 to 08:00. A
    finished Reel takes the earliest free slot unless the approval note
    gives a reason (embargo, dated launch, his hold). Gaps are filled from
    the build queue first, then the bank of evergreen Reels (at least 6
    ready at all times). The hourly watch runs `formats.py gaps 2` and says
    so in its commit. Variety unchanged: no two in a row on one game or
    publisher, no third on one template, card-led one in three over six,
    four per template per Dubai day; reports and rumours at most one in
    three and re-checked before queuing. CLAUDE.md, "Constant coverage".
  - Silence rule (batches he asks for outside a slot): no reply 30 minutes
    before the first time counts as a go.
- **Breaking lane:**
  - Verified official news only; never rumours, leaks or single-outlet
    reports, at any hour.
  - 15-minute auto-go round the clock (16 Oct; was 08:00 to 23:00), at most
    three in any 24 hours.
- **Overnight (advisor, 16 Oct, agreed with Mohammad 02:50 Dubai; he now
  reads the feed as a viewer and deletes what he does not like):**
  - Every verified story landing overnight is queued at the overnight
    spacing (60 minutes, 00:00 to 08:00, since 16 Oct), real news and not
    only evergreen. The strongest pieces
    still go 08:00 to 21:00.
  - Mornings are spread out: at most one post per 30 minutes, none bunched
    before 08:00.
  - Quiet hours, when nothing is being built: warm footage and cache for the
    next day's dated stories, pre-build shell Reels for anything due at a
    known time, then bank evergreen pieces (idle card, `delegation.md`).
  - Morning digest by 07:30: every post since 23:00, one line each (time,
    title, template, chip, strip path).
  - He may delete any post. A wrong fact found more than an hour after
    publishing gets a correction Reel, not a silent deletion
    (`newsroom/corrections.md`).
  CLAUDE.md, "Overnight cadence", after the breaking lane.
- **Expansion passes and DLC (15 Oct):** an official add-on announcement with
  official footage is built at once and queued at the next quarter hour (15
  minutes out, preview sent), any hour; his 15 Oct message is the go.
  Constant-coverage spacing applies. CLAUDE.md, after the breaking lane.
- **Before every push:**
  - Preflight and `DRY_RUN=1`; no push while a publish run is in progress.
  - Never re-run a failed publish.
  - Check PUBLISHED after the slot, then strip posted media.

## YouTube lane (trial from 17 Oct 2026)

- Original material only: Famitsu weekly, numbers, list, Gulf prices, retro,
  his handson. Never trailer Reels.
- A YouTube cut under 35 s (Famitsu: top five plus hardware). Title opens on an
  Arabic word, game or news word in the first five words, grammar-checked.
- The next two originals go through Postiz; hundreds of views in 48 hours keeps
  the lane on Postiz at one or two a day, near zero makes it manual (he uploads
  from his phone). Judged after two weeks against 140 views.
- job.json: `"original": "<kind>"`, `"type": "public"`, `"selfDeclaredMadeForKids":
  "no"`; preflight checks all of it.

## Not in force (history only)

- Cadence of 13 Oct (30 minutes by day, 90 overnight, about 12 posts a day)
  and the daily cap: replaced by constant coverage, 16 Oct.
- **Dropped or paused platforms:**
  - TikTok: dropped 1 Oct, along with every rule sending Reels or Shorts
    there. YouTube was dropped the same day and came back on 17 Oct for
    original material only (see the YouTube lane above).
  - Snapchat: paused 9 Oct.
  - DXB-KNIGHT routine production: on hold from 11 Oct.
- **Retired formats:**
  - Still cards and `ig_ar` cards on Instagram, replaced by Reels on 30 Sep.
  - `short.py` Shorts, and `sales_reel` / `short.chart`, replaced by
    `sales_full.py`.
  - 16:9 cuts for X.
- **Superseded settings:**
  - The azure-only chip, replaced by the vivid themes on 2 Oct.
  - The fixed 46/33 Reel text sizes.
