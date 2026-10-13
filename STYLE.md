# Digital Lounge: the rules in force (13 Oct 2026)

One page of what applies today. CLAUDE.md is the full, dated history and wins
on detail; each line here names its section there. Anything listed under
"Not in force" is history, not a rule. Update this page in the same commit
as any change to a rule (Mohammad, 13 Oct 2026, review priority 1).

## Accounts

- **Live:** Digital Lounge on X, Instagram and Threads. Every story goes to all
  three at the same time with the same Reel (CLAUDE.md "Threads",
  "Instagram").
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
  4. DeepL back-check.
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
  - Our own graphics sit on the moving numgfx ground.
- **Text:**
  - The chip and headline sit at the top for about 3.5 s; the first frame is
    the grid tile.
  - Then 4 to 6 lines of the actual story: white Dubai Bold with an indigo
    outline, right-aligned, 1 to 3 visual lines each.
  - Each line stays up for its reading time (`read_secs`); the safe zone is
    x 96 to 910, y 285 to 1480.
  - Lines move to the top over a game's lower-third UI.
- **Sound:**
  - One continuous stretch of the trailer's own music, with voices allowed.
  - Our bed under stills, graphics or noisy stretches; never mute footage to
    add a bed.
  - The jingle and end card always close the Reel.
- **Variety:**
  - Themes per story; band styles rotate through the ledger.
  - Formats come from templates/formats.py, with no more than two of the
    same in a row.
  - The retro sound is for on-this-day pieces only.
- **Process:**
  1. A five-line brief.
  2. `shotsheet`.
  3. `draft`, then `strip`, looked at frame by frame.
  4. `final`, then `strip` again.
  - (CLAUDE.md "Full-screen format", "Creative brief and formats")

## Platforms

- **X:** one or two lines that hook, with no hashtags; the Reel carries the
  story ("Short X posts").
- **Instagram:**
  - Reels only; the same full-quality file as X.
  - Caption: a hook that differs from the headline, then the full story,
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
  - Silence rule: no reply 30 minutes before the first time of a batch he
    asked for counts as a go.
- **Breaking lane:**
  - Verified official news only.
  - 15-minute auto-go, 08:00 to 23:00, at most three a day.
- **Before every push:**
  - Preflight and `DRY_RUN=1`; no push while a publish run is in progress.
  - Never re-run a failed publish.
  - Check PUBLISHED after the slot, then strip posted media.

## Not in force (history only)

- **Dropped or paused platforms:**
  - TikTok and YouTube: dropped 1 Oct, along with every rule sending Reels
    or Shorts there.
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
