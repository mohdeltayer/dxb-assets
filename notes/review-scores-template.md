# Review-scores template (studio, adv-20261104-review-scores-template, Mohammad 4 Nov 2026)

Built on branch `studio/review-scores` by Production 1 (studio). Released by the build desk; Production 2 uses it from
the next review story. First subject: The Legend of Zelda: Ocarina of Time on Switch 2 (reviews 4 Nov, launch 5 Nov).

## Pieces

| Piece | Where |
|---|---|
| Template entry, family (card-led), opener, `NEWS_MAP['reviews']` first choice | `templates/formats.py` (`reviewscores`) |
| Cards: `scores` (the spread), `verdict` (one outlet: score, liked, disliked), `totals` (Metacritic and OpenCritic with the read time) | `templates/cardgfx.py` (`KINDS`) |
| Data fetch: Metacritic and OpenCritic totals and the outlet list, read-only, cached, timestamped | `templates/reviewscores.py` |
| Job check: totals read from the pages and under 180 minutes old, every row on its own scale with a date, quotes 15 words at most with the original kept | `reviewscores.check_job`, called by `render_job.check` for `"template": "reviewscores"` |
| Chip | «التقييمات» (the agreed card chip, CLAUDE.md 26 Sep; `fast_ar.CARD_PICKS`) |
| Filled example | `jobs/test/ocarina-of-time-review-scores-example.json` (test only, never copied to jobs/render as is) |

Theme: the story's theme as usual (playful for Nintendo); the cards take `ground_theme` and sit on the game's own
moving footage (`ground_footage`, or per card `["x-gfx-a.png", [file, start], secs, null]`), never a flat ground.

## Story beats

1. HOOK (about 3.5 s): the game's strongest moving shot; the headline carries the critics' number (the average, or the
   highest or lowest score), never a question first (hook rule, 24 Oct). Example: «متوسط 96 من النقاد\nلنسخة Ocarina الجديدة».
2. THE SPREAD (about 6 s): `scores` card, 4 to 6 outlets by relevance: the big international ones plus every
   Arabic-language outlet that scored it. Each row: outlet in Arabic then the Latin in brackets, the score exactly as the
   outlet printed it (9/10, 5/5, 95/100, or its word: Saudi Gamer's «أسطورية»), and «في 4 نوفمبر».
3. THE VARIATION (about 6 s each): two `verdict` cards, one high and one low (or one unscored with a clear verdict):
   the outlet, «بقلم» and the reviewer, the score, then «ما أعجبه» and «ما انتقده», each a short faithful excerpt in «»,
   15 words at most. Excerpts, never the review.
4. THE TOTALS (about 5 s): `totals` card: Metacritic score and its review count; OpenCritic top critic average, the
   number of top critics and the percent who recommend it; the read time in Dubai time; «والعدد يزداد» while it is fresh.
5. PAYOFF (about 4 s): footage, one line: what it means for players here (worth it at launch, wait for a patch,
   divisive), or the pointer to the full reviews in the pinned comment. It never repeats a card's fact.

Length: about 29 s (no cap since 24 Oct; every card holds its own reading time). No story line over a card: the card is
the beat (one fact, one place).

## How to build one

    python3 templates/reviewscores.py find "<game name>"                 # the Metacritic slug for the right platform
    python3 templates/reviewscores.py fetch --mc <slug> --oc <id>/<slug>  # OpenCritic id and slug from the game's url
    python3 templates/reviewscores.py show uploads/cache/reviews/<slug>.json

Copy `read_at` into `review_scores.totals_read_at`, the totals into `review_scores` and the `totals` card, and pick the
spread and the two verdicts from the list (`own` is the outlet's printed score; check it on the outlet's page when the
scale is a word or a medal). Read the two reviews you quote: the liked and disliked lines come from the review text, not
the aggregator snippet. The job is refused when the totals are over 180 minutes old: fetch again right before the render.

## Rules (from the card)

- Scores on each outlet's own scale, never converted. Metacritic's 0 to 100 list is used for coverage only.
- Metacritic and OpenCritic numbers only from their pages, read at build time, timestamp in the job.
- User scores never shown unless the story is about them.
- Credit on every footage shot; outlet names as text (no logos unless licensed).
- Numbers cards over official footage, not stills-only.
- A sign after a number flips in right-to-left text: «100 بالمئة», not «100%» (22 Oct rule).
- Sound: the game's footage sound when a speech-free or music-led stretch covers the Reel; otherwise our bed, as for
  numbers Reels (trailer-sound rule, 23 Oct, point 1). The Ocarina Overview trailer is narrated almost end to end
  (longest speech-free stretch 24.8 s), so the example uses the bed.

## Checklist lines for newsroom/reel-check.md (story type REVIEWS, with NUMBERS)

To fold into `newsroom/reel-check.md` when the build desk creates it (adv-20261102-reel-checklist), under the story-type
rules, each yes/no with evidence:

- REVIEWS: every outlet named in Arabic and Latin at first mention (evidence: the rows).
- REVIEWS: every score on the outlet's own scale as printed, a word kept as a word (evidence: the review urls).
- REVIEWS: every review dated (evidence: the rows).
- REVIEWS: every quote attributed to the outlet and the reviewer, a faithful excerpt of 15 words or fewer, original
  wording kept in the job (evidence: `review_scores.verdicts`).
- REVIEWS: Metacritic and OpenCritic totals from `reviewscores.py`, with `totals_read_at` under 180 minutes old at render
  time, and the read time on the totals card (evidence: the cache file and its `read_at`).
- REVIEWS: no user score unless the story is about it (evidence: the cards).
- NUMBERS: figure, period, source, comparison on screen (here: the score, the read time, the aggregator, high and low).

## Names list (outlets, as on screen at first mention)

| Outlet | On screen | Note |
|---|---|---|
| IGN | آي جي إن (IGN) | as on 31 earlier stories |
| Eurogamer | يوروغيمر (Eurogamer) | غ for G, as فيوز غيمز; يوروجيمر also appeared earlier |
| Nintendo Life | نينتيندو لايف (Nintendo Life) | glossary (house spelling of نينتيندو) |
| VGC | في جي سي (VGC) | as on 21 earlier stories |
| Saudi Gamer | سعودي جيمر (Saudi Gamer) | the site's own Arabic name |
| RPG Site | آر بي جي سايت (RPG Site) | new |
| Metacritic | ميتاكريتيك (Metacritic) | as on 6 earlier stories (ميتاكريتك also appeared) |
| OpenCritic | أوبن كريتيك (OpenCritic) | as used before |
| GamesRadar+ | جيمز رادار (GamesRadar+) | new; the + stays in the Latin only |

## Ocarina example: what was read (4 Nov 2026, 13:05Z)

- Metacritic (Switch 2 page, `the-legend-of-zelda-ocarina-of-time-2026`): 96 from 81 critic reviews, 80 positive.
- OpenCritic (21344): top critic average 96 (95.6), 100 percent recommend, 17 top critics, 30 reviews, tier Mighty.
- Spread: IGN 9/10 (Logan Plant), Eurogamer 5/5 (Christian Donlan), Nintendo Life 9/10 (Oliver Reynolds), VGC 5/5
  (Andy Robinson), Saudi Gamer «أسطورية», the top of its five words (عصام الشهوان; OpenCritic records it as 5/5).
- High: Saudi Gamer, liked «هذه تجربة ساحرة تنضح بالأفكار وبروح المغامرة», criticised «انخفاض الدقة يجعل الصورة أحيانًا
  غير ثابتة» (both quoted from the Arabic review as written).
- Low: RPG Site 8/10, the lowest on both aggregators (Scott White, with Alex Donaldson): liked "quite possibly the most
  visually striking title on the Switch 2 platform yet", criticised "WHY IS THERE ONLY A SINGLE SAVE SLOT?!".
- RPG Site lines in Arabic: «ربما اللعبة الأكثر إبهارًا بصريًا على Switch 2 حتى الآن» and «لماذا لا توجد سوى خانة حفظ واحدة؟!». DeepL
  forward (whole phrase, 4 Nov) gave «اللعبة الأكثر إثارة للإعجاب من الناحية البصرية» and «خانة حفظ واحدة»; its back-check read the
  first draft «أكثر ألعاب Switch 2» as plural, so the singular «اللعبة الأكثر» is used. A live job still runs the grammar stage.

## Not done here

- Rendered with the Dubai font: the container has no font, so the cards were laid out with a wide stand-in (DejaVu
  Sans) and a draft render; the build desk renders the example on the runner as its test.
- OpenCritic's search needs an API key, so `fetch` takes the id from the game's OpenCritic url (found by hand once per
  game). Metacritic's slug comes from `find`.
- `music_only` trailer audio with speech_check reading the music stem (a later build item, if wanted).
