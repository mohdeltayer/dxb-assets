# Scenario recipes, second by second (advisor, 24 Oct 2026)

Copy of the board "Scenario recipes, second by second" on the advisor canvas "Digital Lounge Reel
Templates". The board is the source; this copy is for briefs and render agents. Each beat names the
one thing the viewer looks at (the eye).

Principles:
- One focus at a time. Show it, let it land, then the next. A name plate never arrives with a story line.
- One idea per frame. Each shot shows one thing: the port, the button, the face, the number. A frame
  that needs two lines to explain is split.
- Breathing space. Fewer, larger elements; empty space is part of the design.
- Motion settles before reading. Animations finish (under 0.5 s), then text is read. Nothing moves
  under a line being read.
- Voiceover changes the rule. When Mohammad's voice carries the story, face and name may share the
  screen while he speaks.

## 1. Hardware or product reveal (Apple-style showcase)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | Hero shot: the console turning slowly on our dark ground, headline above. Nothing else. | the product |
| 3.5 to 7 | Detail 1: slow push-in on one detail (the ports); one short label after the push settles. | the detail, then its label |
| 7 to 10.5 | Detail 2: the controller; buttons highlight one by one with a soft ring, each named briefly. | each button in turn |
| 10.5 to 14 | Detail 3: the feature the story is about (size, finish, screen). | the feature |
| 14 to 18 | Price and date: the product small, the price large with the dirham sign, the date beneath. | the price |
| 18 to 20 | Closing picture, then the end card. | |

## 2. Trailer drop or fresh reveal (the trailer is the star)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | Strongest moving shot, chip and headline (the hook); the trailer's own sound from frame one. | headline over motion |
| 3.5 to 8 | The trailer plays. No line. Let it breathe. | the footage |
| 8 to 12 | Line 1 on the shot that shows it (what was revealed), entering on a cut. | the line |
| 12 to 16 | Line 2: date, platforms or what is not confirmed; or a split strip if there is a price. | the line or strip |
| 16 to 20 | Best closing shot with the music peak; no new text in the last 2 s. | the picture |

## 3. Person in the news (face first, news second)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | Headline over the person's best-known work, the photo box and name plate already open beside it (the cover: face, name, headline). Amended by Mohammad, 24 Oct (inbox: "Face on the cover"); the board's version opened on the headline alone and brought the box in at 3.5. | face, name and headline |
| 3.5 to 4 | The photo steps aside. | |
| 4 to 14 | Story lines on footage of their work, one at a time. | each line |
| 14 to 18 | Closing: their most recognisable work, the final line. | the line, then the picture |
| voiceover | With Mohammad's voice, the face and name stay while he speaks; lines follow the voice. | |

## 4. Numbers and sales (the number is the hero)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | Game footage, logo plate, headline with the hook figure in words. | headline |
| 3.5 to 7 | The figure counts up large in the centre, then settles; the label under it appears after. | the number |
| 7 to 11 | The split (platforms, regions): bars fill one at a time. | each bar |
| 11 to 15 | What it means: one framing line (a record, a comparison) on footage. | the line |
| 15 to 18 | Source note small, closing footage. | |

## 5. Delay or date change (calm, factual)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | The game's hero shot, chip تأجيل, headline with the new date. | headline |
| 3.5 to 7 | Strip: new date, previous date, platforms; footage keeps running above. | the strip |
| 7 to 11 | The stated reason, on footage of what the studio says needs time. | the line |
| 11 to 15 | What is unchanged or promised, in the studio's words. | the line |
| 15 to 18 | Closing shot, no drama in music or text. | |

## 6. Debate piece (points of view, the viewer decides)
| Seconds | Beat | Eye |
|---|---|---|
| 0 to 3.5 | The fact as a question («لعبة بسعر 80 دولارًا: هل يستحق؟») over the game's footage. | the question |
| 3.5 to 7 | The fact itself: the price or number large, sourced. | the fact |
| 7 to 15 | Two or three points of view, one per beat, each labelled as what people say. Never our opinion. | one view at a time |
| 15 to 18 | The question back to the viewer: «وأنت، ما رأيك؟» | the question |
| rule | First of its kind or debate: options to Mohammad before it posts. | |

## Which recipe (production's mapping from formats.NEWS_MAP kinds; the board names the stories, not the kinds)
- 1 hardware: hardware, hardware_price, edition, accessories.
- 2 trailer drop: reveal, trailer, launch, update, expansion, crossover, adaptation, remake, dlc.
- 3 person: people stories (awards, honours, appointments, departures, interviews, quotes, tributes); `quote`, `cast`.
- 4 numbers: results, sales, famitsu, players, reviews, records, milestones.
- 5 delay: delay, date changes, shutdown dates.
- 6 debate: controversy and price debates (`formats.QUESTION_ALLOWED`); options to Mohammad first.
- None fits (store prices, lists, retro, explainers): the brief writes its own second-by-second focus on the same principles and says so.

In the brief, the focus is written per beat: `0.0-3.5 headline over motion · 3.5-6.0 photo box alone · ...`.
