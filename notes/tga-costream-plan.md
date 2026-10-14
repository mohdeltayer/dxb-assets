# The Game Awards co-stream, 10 Dec 2026 (advisor decision, 14 Oct 2026)

Digital Lounge co-streams The Game Awards on YouTube with Mohammad's voice and
no face; Instagram carries the clips. Past years ran at 17:00 Pacific, which is
05:00 on Friday 11 Dec in Dubai; the time is confirmed from thegameawards.com
when announced. No YoloBox before the Awards: OBS on a laptop with window
capture of the official stream and a USB mic.

## Clip routine (designed first)

During the show a live log is kept in the batch folder, one line per
announcement as it lands: `HH:MM:SS Dubai | game | kind (reveal, date, trailer,
award, shadow drop) | platforms and date as shown | trailer seen (yes/no)`.
The hourly watch keeps running; the Verifier checks the official pages for each
announcement (publisher site, Steam page, press release) before anything posts.

From 06:30 Friday, five to eight Reels in this order of priority, each on the
normal quality steps (brief, sheet, draft, grammar review, DeepL, preflight):
1. `list`: the winners (Game of the Year and the main categories), N items on
   their own art, n/N cue, mosaic cover. Kind `awards`.
2. `trailer`: the three to five biggest reveals, each on its own official
   trailer (IGN MP4s, publisher CDNs; never YouTube). Kinds `reveal`, `date`.
3. `numbers`: the night by the numbers (awards per publisher, the GOTY vote,
   the viewing figure when the organisers publish it). Kind `results`.
4. One Gulf angle only if the region is in the show (a Saudi or UAE studio on
   stage, a regional nominee), as a normal story, never forced.
Cadence as usual: at least 30 minutes between posts, no third template in a
row, card-led at most one in three; the clips are spread across the Friday.

## Build by 31 Oct: the live brand package

OBS scenes in the Reel look (indigo ground, play mark, Dubai type, theme wave
lines; no pink), rendered from the templates so the stream matches the Reels:
- Starting soon: the mark, «يبدأ البث بعد» and a countdown to the show's
  Dubai time; the everyday bed under it.
- BRB: «نعود بعد قليل» on the living ground.
- Lower-third ticker: right to left, Dubai Bold, fed from a text file the
  hourly watch writes (headline · source), one line at a time, Arabic first.
- Corner mark: the play mark, small, top right of the stream frame, always on.
- End card: the Reel end card (mark, name, handle, the jingle).
Deliverable: `templates/live/` (the scene PNGs, loops and the ticker feeder)
and an OBS scene collection he imports. First drafts to Mohammad before use.

## Dry runs

Two unlisted YouTube dry runs in November on the next showcases (the events
calendar names them as they are confirmed); the second with the ticker fed
live from the hourly watch. Each is judged on: audio level and clarity, the
lower third's readability at 1080p, the delay between the official stream and
ours, and whether the clip log can be kept while talking.

## Reels around the show

- Countdown Reels from 3 Dec (one a day or every other day, `numbers` or
  `split`, the Dubai time on the strip).
- Announcement Reel on 9 Dec with the Dubai time and the YouTube link read
  aloud (links are not clickable in captions).

## Judgement

At the 16 Dec audit: peak live viewers, replay views, and the clip Reels
against normal Reels of the same week. Play streams and any hardware (YoloBox,
capture card) are decided then, not before.

## Policy

The Game Awards' co-stream policy is read the week before (check-in 3 Dec)
and followed as written: what may be rebroadcast, with what delay, whether
monetisation is allowed, and the attribution it asks for.
