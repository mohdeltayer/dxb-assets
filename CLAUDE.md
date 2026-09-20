# Working on DXB-KNIGHT

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

Sweep all unread digests for the day before recommending anything.

## Verify against primary sources

The digest is a lead sheet, not proof. Check claims independently before
they go on a card — it has had real errors (it named "Romancing SaGa 4
Destiny United" for what is *Romancing SaGa 3: Destinies Unite*).

Attribute a company's own numbers to the company: "Capcom says", not a
bare figure.

Note: session egress policy usually blocks press domains, Steam and
publisher sites outright. WebSearch still works and is the fallback —
but say plainly when something is corroborated by search rather than
read from the primary.

## Publishing

Cards render to `cards/YYYY-MM/`, source art to `live/YYYY-MM-DD/`.

Posting is irreversible: pushing `queue/**` to *any* branch of dxb-queue
fires the publisher, because `publish.yml` has no branch filter. Never
queue without explicit say-so, and dry-run `publish.py` with `DRY_RUN=1`
first to confirm which folders will post.
