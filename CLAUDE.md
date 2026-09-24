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

## Always ask for Mohammad's take before building a card

DXB-KNIGHT is not a wire service. Before rendering any card, ask what he
thinks of the story — whether he has played it, what he made of it, what
he would tell a reader that the source does not say.

His answer decides the background mode:

- he gives a take -> `voiced` (purple), and his line goes in the copy
- he has none, or it is pure reporting -> `reported` (navy)

Ask before rendering, not after. A card built without asking is a card
that reports someone else's story in his name.

## Art goes on top

`single` is the template with the art panel at the top, and it is the
default for a story with an image. `quote` puts media *under* the quote,
so it is not the way to put a picture on a card.

`gulf=True` and the gold GULF chip exist only on `single`, so a regional
story built as a `quote` silently loses the Gulf marker.

When the template choice is not obvious, ask rather than guess.

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
  OUT NOW, DELAYED, PRICE. `fast.py` refuses anything else.
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

In every sweep, each shortlisted item comes with its lane and chip already
chosen. Minutes old and the image tells it: fast. Needs his take, numbers
or context: card. Big: fast now, card later as a reply to the fast post.

## Publishing

Cards render to `cards/YYYY-MM/`, source art to `live/YYYY-MM-DD/`.

Posting is irreversible: pushing `queue/**` to *any* branch of dxb-queue
fires the publisher, because `publish.yml` has no branch filter. Never
queue without explicit say-so, and dry-run `publish.py` with `DRY_RUN=1`
first to confirm which folders will post.
