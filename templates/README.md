# DXB-KNIGHT card templates

Locked 18 September 2026. Files live in `templates/` on the shelf:
`cards.py`, `crest-tint.png`, `crest-source.png`, `Inter.ttf`.

## Restoring after a sandbox reset

```bash
mkdir -p /home/claude/fonts
cd /home/claude
B=https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/templates
curl -sL -o cards.py       $B/cards.py
curl -sL -o crest-tint.png $B/crest-tint.png
curl -sL -o fonts/Inter.ttf $B/Inter.ttf
```

Images used in cards must be uploaded to the chat first. The sandbox cannot
reach Gematsu, Nintendo Everything or any press site, only GitHub.

## The theme

Canvas 1600 x 2000 (4:5, the tallest X shows uncropped)
Ground `#160C33`, tiles `#201440`, ink `#FFFDFA`, subtitle `#C6BAEB`
Accents cycle: orange, blue, green, pink, violet, gold, teal
Type: Inter variable. Headers 96/800, titles 86/800, body 46/400

Footer is identical on every card: crest and DXB-KNIGHT left, source centred,
date right, all at 28px on one baseline. Date format `Sep 17, 2026`.

## The five templates

### roundup — showcase recaps, max 4 items
```python
cards.roundup(header, subheader, items, date, source, out)
# items: [(title, subtitle, date_label, image_filename or None), ...]
```
More than four items means two cards. Put `1 of 2` in the subheader.

### single — one announcement, art across the top
```python
cards.single(kicker, title, lines, release, image, date, source, out, accent=0)
# lines: list of paragraphs
```

### charts — weekly sales
```python
cards.charts(header, subheader, rows, hardware, date, source, out)
# rows: [(rank, platform, title, week_number, None), ...]  max 10
# hardware: [(label, number), ...]
```

### compare — two things side by side
```python
cards.compare(header, subheader, left, right, date, source, out)
# left/right: {'label','price','sub','rows':[...], 'image': optional}
```
If one side has an image both columns get an art panel. Spec rows shrink
their type to fit rather than overflowing.

### quote — a statement someone made
```python
cards.quote(header, text, attribution, context, date, source, out,
            accent=3, image=None)
```
The quote grows to fill the space it has. Keep it under 15 words for
copyright, and it reads better short anyway.

## Rules that produced this

Phone first. Fandom's cards work because the type is around 6% of the frame
width. Ours was 1.9% and vanished in a timeline. Titles are now 5.4%.

Four items maximum. Seven at readable size will not fit.

The footer never changes. That consistency is what makes a series read as a
publication rather than a set of posts.
