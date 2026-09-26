# Working on DXB-KNIGHT

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

- DXB-KNIGHT (@DXBNIN), English: Mohammad's personal voice, in the Genki
  or Daniel Ahmed mould. General games news and takes, Gulf sprinkled in.
- The Digital Lounge, Arabic: a full Arabic games outlet, "the regional
  IGN" and Mohammad's first entrance into that market. It covers the whole
  games slate for Arabic readers, not only regional news, in an outlet
  voice (more news, more volume, no first person). Regional stories lead
  more often here than on DXB-KNIGHT because its readers are in the region.

Arabic posts are written for Arabic readers, never translated from the
English post. The two brands never share a mark; their palettes are kin
(Mohammad, 26 Sep 2026). What tells a Digital Lounge card apart is the
indigo ground, the play mark, Dubai type and the right-to-left footer.
No pink or magenta anywhere on it: to a Gulf reader it reads as girlish
or for kids (Mohammad, 26 Sep 2026).

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
@the_digilounge on X (display name DIGI-ديجي until 26 Sep, joined Jan 2024; 19
followers and 1,565 posts as of 24 Sep 2026). Connected to Postiz on
26 Sep 2026 as integration `cmuifxrd70mbdo80y235utthm` (DXB-KNIGHT is
`cmtk7cltp0030my0yj6glcyru`); check the id on every Arabic job.json.

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

There is no scheduled sweep and no Routine. Mohammad asks when he wants
one, at no fixed cadence, so "unread" has to mean "not yet worked
through" or the request has no edge. After reporting on a sweep, mark the
digests just covered as read with `update_message`
(`removeLabels: ["unread"]`), so the next sweep starts from genuinely new
sheets rather than re-reading the day.

Come back with a ranked shortlist, not a summary of every item. For each
candidate give the verification status, and the template, background,
accent and label already chosen — then ask for his take. He supplies the
take and the art; everything else should be decided before he reads it.

## Verify against primary sources

The digest is a lead sheet, not proof. Check claims independently before
they go on a card — it has had real errors (it named "Romancing SaGa 4
Destiny United" for what is *Romancing SaGa 3: Destinies Unite*).

Attribute a company's own numbers to the company: "Capcom says", not a
bare figure.

Network: Mohammad opened the environment's network access on 23 Sep 2026.
Press sites, Steam, PlayStation Blog, Nintendo and their image CDNs now
load, so read primaries and fetch art directly. Google Patents, pbs.twimg.com
and news.xbox.com refuse automated requests at their end; use a press
article that carries the same image. Say plainly when something is
corroborated by search rather than read from the primary.

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

## Two lanes: fast and card

The fast lane posts breaking news within minutes, on `templates/fast.py`:
the image or clip full bleed in a 1600x900 (16:9) frame, a chip on the
media, an accent rule, and the same footer as every full card (crest and
DXB-KNIGHT left, source centre, date right). No headline and no kicker on
the card. Here the post text carries the facts, attributed ("Xbox says",
"per Windows Central"), because the card deliberately does not. Speed never
excuses an unverified claim: name the source in the text.

The card lane is the considered `flex.py` card with his take, posted later
as a reply to his own fast post so it inherits that post's audience. The
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
  تأجيل DELAYED (مؤجل), السعر PRICE (سعر), تجربة HANDS ON (انطباعات).
- Card: تجربة HANDS ON (انطباعات), رأي OPINION, حوار INTERVIEW (مقابلة),
  تحليل ANALYSIS, أرقام STATS (إحصائيات), إنجاز MILESTONE (رقم قياسي),
  التقييمات REVIEWS (المراجعات), تحديث UPDATE, فعالية EVENT (حدث),
  ملخص RECAP, مقارنة VS (ضد).
- No GULF chip on Arabic. A regional story names its country instead:
  الإمارات, السعودية, قطر, الكويت, البحرين, عُمان, and the wider Arab world
  the same way (مصر, الأردن, المغرب). Bright indigo `#5552E0` with ink
  text, beside the news chip, never azure. Same test as GULF: only when
  the country is the story, not because a global launch includes it.
- The same ladder and BREAKING rule apply: عاجل is rare, most news is جديد.

In every sweep, each shortlisted item comes with its lane and chip already
chosen. Minutes old and the image tells it: fast. Needs his take, numbers
or context: card. Big: fast now, card later as a reply to the fast post.

## Publishing

Cards render to `cards/YYYY-MM/`, source art to `live/YYYY-MM-DD/`.

Posting is irreversible: pushing `queue/**` to *any* branch of dxb-queue
fires the publisher, because `publish.yml` has no branch filter. Never
queue without explicit say-so, and dry-run `publish.py` with `DRY_RUN=1`
first to confirm which folders will post.
