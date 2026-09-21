# DXB-KNIGHT card templates

`flex.py` is the card system. Files live in `templates/` on the shelf:
`flex.py`, `cards.py`, `crest-tint.png`, `crest-source.png`, `Inter.ttf`.

`cards.py` is retired as a template set but is still imported — see
[Legacy](#legacy-cardspy) at the end.

The agreed card system sheet (20 Sep 2026) is canonical. Where this file
and the sheet disagree, the sheet wins.

## Restoring after a sandbox reset

```bash
mkdir -p /home/claude/fonts
cd /home/claude
B=https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/templates
curl -sL -o flex.py         $B/flex.py
curl -sL -o cards.py        $B/cards.py    # flex.py imports it, see Legacy
curl -sL -o crest-tint.png  $B/crest-tint.png
curl -sL -o fonts/Inter.ttf $B/Inter.ttf
```

Images and clips used in cards must be uploaded to the chat first; they are
read from `/mnt/user-data/uploads/`. The sandbox cannot reach Gematsu,
Nintendo Everything or any press site, only GitHub.

## The frame

Canvas 1600 x 2000 (4:5, the tallest X shows uncropped). Margin 70. The
media panel is `(70, 110, 1530, 970)`.

Ink `#F7FAFC`, body `#D7E1EA`. Type is Inter variable: headers 96/800,
titles 106/800, kickers 44/800, body 54/450.

Footer is identical on every card: crest and DXB-KNIGHT left, source
centred, date right, all on one baseline at 30-32px, above a rule at
y=1850. Date format `Sep 17, 2026`.

Colour and effect are separate. A bright accent is a colour, glow is a
treatment, and one does not imply the other.

## Background modes

Background says **who is talking**.

| Mode | Colour | Use for |
|---|---|---|
| `reported` | navy `#111D29` | the default — news, other people's announcements |
| `voiced` | purple `#1D1440` | first person — our own hands-on, opinion, verdicts |

Pass a mode name, a colour name (`navy`, `purple`) or a raw RGB triple.

## Accent territories

Accent says **how the subject feels**. Pass the territory, not the colour —
the territory is the decision, the colour is the consequence.

| Territory | Colour | Use for |
|---|---|---|
| `cold` | cyan `#42D7FF` | sci-fi, horror, hardware, specs, business, legal |
| `stylized` | lavender `#BBA3FF` | fantasy, RPG, anime, mystery, story-led |
| `playful` | amber `#FFC03A` | platformers, party, fighting, sports, jokes |
| `spectacle` | rose `#FF4D6D` | blockbuster reveals, movies, TV, pop culture |

Spectacle carries a second colour, coral `#FF5C45`. Rose leads; pass
`accent='coral'` as the deliberate alternate when rose would sit next to
amber or vanish into pink artwork.

Each accent has a **support** colour, used for the kicker and the right-hand
column of `compare`. It is picked automatically and can be overridden with
`support=`:

    cyan -> lavender    lavender -> cyan    amber -> cyan
    rose -> amber       coral -> amber

Row separators in `roundup` and `charts` cycle cyan, lavender, amber, rose.
Coral is left out on purpose: stacked directly above or below amber, 34
degrees of hue is not enough.

### Treatments

`treatment` is the effect, on `single` and `roundup` only:

- `flat` — default, no effect
- `spotlight` — a graded wash lifting toward the accent
- `neon` — an illuminated edge on the panel, and on the `display` line

## The gulf chip

Gold `#FFD34E` is the Gulf chip and nothing else. Pass `gulf=True` on
`single` to add a gold `GULF` chip beside the label. It rides alongside
whatever accent the topic already earned rather than replacing it, so a
Gulf story keeps its territory.

Gold is reserved: passing it as a card accent raises `ValueError`. It sits
4 degrees from amber, so on a border the two stop being distinguishable.

## Label chips

Every template takes `label=`, a short filled chip in the accent colour with
background-coloured type, set upper case. On `single` it sits inside the
media panel, bottom left, with the GULF chip to its right when present. On
the other four it sits top right, level with the header.

Keep it to a word or two — `hands on`, `rumour`, `confirmed`, `sale`.

## The six templates

Every template returns the output path. All take `label=`, `background=`
and `accent=`.

### single — one story, media across the top
```python
flex.single(kicker, title, lines, label, media, date, source, out,
            background='reported', accent='cold', support=None,
            treatment='flat', display=None, gulf=False,
            video=None, clip_start=0, clip_seconds=6, audio=False)
```
The hero card. `lines` is a list of paragraphs. The panel image is
*contained* by default — the story's picture is the story. A crop to fill
the panel is fine when nothing important is lost and the frame does not
read as compromised; contain it when a crop would cut a face, a logo or
headline text. `display` is
an oversized word above the kicker, which the `neon` treatment lights.

The only template that takes `gulf` or `display`.

### roundup — showcase recaps, max 4 items
```python
flex.roundup(header, subheader, items, date, source, out, label=None,
             background='reported', accent='cold', treatment='flat')
# items: [(title, subtitle, date_label, image_filename or None), ...]
```
More than four items means two cards; put `1 of 2` in the subheader. Row
thumbnails are cropped, not contained — a row thumbnail only has to say
which game the row is about, and letterboxing four of them leaves the card
full of bars.

### charts — weekly sales
```python
flex.charts(header, subheader, rows, hardware, date, source, out, label=None,
            background='reported', accent='cold')
# rows: [(rank, platform, title, week_number, lifetime or None), ...] max 10
# hardware: [(label, number), ...]
```
A chart is always `cold`, never the platform that won the week. Otherwise
every chart card takes the colour of whoever is selling and the territory
stops meaning anything.

### compare — two things side by side
```python
flex.compare(header, subheader, left, right, date, source, out, label=None,
             background='reported', accent='cold', support=None)
# left/right: {'label','price','sub','rows': [str], 'image': optional}
```
The left column takes the accent, the right takes the support colour.
Neither means better: this is a comparison, not a verdict. If one side has
an image both columns get an art panel. Spec rows shrink their type to fit
rather than overflowing.

### quote — a statement someone made
```python
flex.quote(header, text, attribution, context, date, source, out,
           background='reported', accent='cold', media=None, label=None)
```
The quote grows to fill the space it has, so a short line lands large and a
long one stays readable. Keep it under 15 words for copyright, and it reads
better short anyway.

## Video on single()

`single` writes an MP4 instead of a PNG when `video=` is passed. Everything
else is identical, so a card can be switched between still and moving
without touching the copy.

| Argument | Meaning |
|---|---|
| `video` | a filename, or a list of `(filename, start, seconds)` for a sequence |
| `clip_start` | seconds into the clip to start, when `video` is a single filename |
| `clip_seconds` | how many seconds to take (default 6) |
| `audio` | `True` keeps sound, and only if *every* clip has an audio stream |

```python
flex.single(..., out='card.mp4', video='capture.mp4',
            clip_start=12, clip_seconds=8, audio=True)

flex.single(..., out='card.mp4', audio=True,
            video=[('a.mp4', 0, 4), ('b.mp4', 30, 5)])
```

`out` must end in `.mp4` or it raises. `media` is ignored when `video` is
set, but the panel shade is still laid down first so the letterbox bars
match a still card's backing.

Clips are *contained* and padded, matching how a still is placed — cropping
to fill would make video the one place the system throws away part of the
frame. Segments are cut, not crossfaded: on a panel this size a dissolve
reads as a smear. Mixed sources normalise to the panel before joining, so
portrait capture and 60fps landscape concatenate cleanly.

Chips and the panel border are drawn on a transparent layer riding above
the clip, so they read the same as on a still. Output is H.264, CRF 20,
30fps, faststart, scaled to 1080x1350, with AAC 128k when audio is kept.
Needs `ffmpeg` and `ffprobe` on PATH.

## The fit guard

Body copy on `single` steps down through 54, 52, 50 and 48 until it clears
`H - 190`, forty pixels above the footer rule. Each size is re-wrapped,
because smaller type fits more words per line and so changes the line count,
not just the step.

If it still does not fit at 48 the call raises `ValueError` naming the
overrun and how many lines to cut:

```
body copy overruns the footer by 104px at 48pt, the smallest body size:
cut about 2 lines of copy
```

That is deliberate. Copy running through the footer rule reads as a bug in
the template, and shrinking past 48 would undercut the type floor the system
is built on, so the overrun is handed back as an editorial problem.

### recap — a stats board
```python
flex.recap(kicker, hero, caption, rows, date, source, out, label=None,
           media=None, dim=0.30, plate=0.55,
           background='reported', accent='cold', gulf=False)
# rows: [(label, value), ...] max 6
```
Same wireframe as `single`: panel on top with the chip bottom left inside
it, figures below. `hero` is the lead number and `caption` says what it
counts; exactly one hero per card, so the ledger values stay in ink and only
the hero, the border and the chip carry the accent.

`rows` puts the label on the card margin and the value on the right margin,
the same pairing `charts` uses for its hardware lines.

With `media` the panel takes art. Without it the panel becomes a wash graded
toward the accent, which is the version for a card with no picture.

Art behind type is the one place the contain rule bends. `dim` is a light
left-weighted scrim over the panel, `plate` a translucent lozenge under the
figures only, sized from the text itself. Measure a new image rather than
trusting the defaults: a dark photo wants less, a bright one more.

This is not `charts`. `charts` is for hardware and software sales, ranked
rows with units. `recap` is for a handful of headline figures that are not a
ranking.

## Choosing

Background says who is talking. Accent says how the subject feels. The label
chip says what kind of piece it is. They are three separate decisions.

The subject decides, not the outlet. A business story about Nintendo is
`cold`, not `playful`.

A chart is always `cold`, never the platform that won the week.

Spectacle carries two. Rose leads; reach for coral when the card will sit
next to an amber one.

Unsure? `reported` + `cold` + `flat`. That is the house default.

## Rules that produced this

Phone first. Fandom's cards work because the type is around 6% of the frame
width. Ours was 1.9% and vanished in a timeline. Titles are now 5.4%.

Four items maximum. Seven at readable size will not fit.

The footer never changes. That consistency is what makes a series read as a
publication rather than a set of posts.

Media keeps its own colours. Nothing is tinted, overlaid or graded.

Hero media is contained rather than cropped, so the card does not throw
away part of the story's picture. Row thumbnails in a `roundup` are the
exception, and a crop that loses nothing is a judgement call, not a
violation.

## The lookout: ahead.py

The pinned month-ahead is not a flex.py card. It is its own format,
reproduced from the September original: a 1320x1389 canvas, a neon title,
a 2x3 grid of tiles with art on top, a big date, an event name and a sub,
and a footer for the timezone note. Six tiles, never more. `roundup` is
not the way to build one.

    ahead(['THE M@NTH', 'AHEAD.'], items, footer, out, theme='halloween')

`items` is up to six `(date, name, sub, image|None)`. `sub` is a string or
a `(platforms, note)` pair. **Every tile names its platforms in the same
form**, `PS5 · Xbox · Switch 2 · PC`, so a tile that says nothing does not
read as "not on it". Notes such as a demo date go on the second line.
Without an image the art panel is a graded wash in the tile's border
colour, which is the placeholder to review layout against.

`theme` picks palette and title font; the geometry never changes, so a new
month is a palette swap and six new items. `halloween` (October) and
`neon` (September's look) ship; add November as a dict.

A marker in the title, `@` by default, is drawn as a glyph in the same
stroke and glow as the letters, sized to the font's O. Halloween's glyph is
a jack-o'-lantern. Swap `_pumpkin` for something else when the month
changes.

**Video.** `ahead_video(..., seconds=8, fps=30, style='soft')` renders the
same card as a looping MP4 where only the glyph flickers; the letters never
dim. `soft` is a slow breath plus a few smooth dips to about half
brightness. `sharp` is a tube on its way out. First and last frames are
full brightness so the loop is seamless. Output is H.264 yuv420p, the odd
canvas height padded by one row. The still and the video render from the
same call arguments; keep both in `cards/`.

Title fonts (Bungee, Monoton, Righteous) are vendored under
`templates/fonts/`. The card system sheet does not list this format.

## Legacy: cards.py

The `cards.py` **templates are retired** — its five entry points
(`roundup`, `single`, `charts`, `compare`, `quote`) are superseded by the
`flex.py` versions above and should not be called for new cards. It ran the
violet ground `#160C33` and a seven-accent cycle keyed to platform
(`nintendo`, `playstation`, `xbox`, ...), which `flex.py` replaces with
territories keyed to how a subject feels.

**The file has to stay on the shelf.** `flex.py` does `import cards as C`
and uses it for:

| Import | What it does |
|---|---|
| `C.font` | the Inter variable-axis font loader |
| `C.wrap` | the greedy word wrapper every template measures with |
| `C.CREST` | the crest path the footer pastes |
| `C.U` | the uploads path media is read from |
| `C._fit`, `C._rounded` | crop-to-fill and rounded-corner paste helpers |

Deleting `cards.py` breaks `flex.py` on import. Restore both together.
