# «الطريق إلى GTA VI»: episode plan and series ledger (studio-gta-vi-series, Mohammad 8 Nov 2026)

Series rules: the request is on the dxb-queue board as handoff `studio-gta-vi-series` (verbatim). It replaces
«الطريق إلى Ocarina», which is closed. One episode a day at the evening peak (about 20:00 Dubai; Thursday 18:00 and
Friday 20:00 are Publer's best Instagram windows), scheduled by the posting lane under the cadence rules; news and the
bank come first in a contested hour. The studio builds and hands each finished job over on the board; it never schedules.

Launch date, the only source of the countdown: **19 November 2026**, PS5 and Xbox Series X|S.
- Rockstar Games, rockstargames.com/VI, read 8 Nov 2026 03:40Z: "Coming November 19, 2026"; "Pre-Load Begins November 10".
- Take-Two, "Reports Results for Fiscal First Quarter 2027", 7 Aug 2026: "Grand Theft Auto VI | PS5, Xbox Series X|S |
  November 19, 2026". Take-Two reports fiscal Q2 2027 on Mon 9 Nov 2026 (call 21:30Z): re-read it for episode 2 onward.
- Pre-load conflict: Take-Two's pre-order release (24 Jun 2026) said digital pre-load from 12 Nov; Rockstar's newer
  Newswire article (3 Nov 2026) and the GTA VI page say 10 Nov. Rockstar's newer statement stands.
`templates/gta_intro.py` holds the date as `LAUNCH`; a job's `"intro": {"series": "gtavi", "days": N, "episode": E,
"date": "YYYY-MM-DD"}` is refused unless N is the count from its Dubai date. Never type the number from memory.

## Fixed identity (not counted in the ledger)
- Intro, about 2.9 s (`templates/gta_intro.py`): chip «الحلقة N» (amber), title «الطريق إلى GTA VI» in the spectacle
  theme's azure to amber, «باقي N يومًا» (agreement per days_line), Rockstar's launch trailer 25.15 to 27.18 s (the
  skyline at sunset, then Lucia and Jason in the convertible) at 0.75x as a band, «المصدر: روكستار غيمز (Rockstar Games)»,
  our own sound: sonic.py flavour `gtavi` (the house motif D F# A E on a warm 80s poly synth, nothing licensed).
- Outro: the same end card as every Reel (outro.py).
- Everything between is the episode's own material. Episode beds, where a bed is needed (numbers, timelines), use the
  `gtavi` flavour's arrangement (synth80, synth, synth80, epiano); footage episodes keep the trailer's own sound.

## Plan

| # | Dubai date | Days | Subject | Family / template | Status |
|---|---|---|---|---|---|
| 1 | Sun 8 Nov | 11 | Why this launch matters: the series in Take-Two's own numbers (GTA V lifetime units, years since its launch, the gap since GTA IV) | numbers, clipcard on Rockstar footage | rendering (server) |
| 2 | Mon 9 Nov | 10 | Trailer 1 read closely: what each shot confirms | trailer breakdown | to research |
| 3 | Tue 10 Nov | 9 | Vice City then and now: Vice City (2002) against 2026 Leonida, Rockstar footage both sides, both halves labelled | comparison, hard cuts | to research (needs Rockstar's own Vice City footage) |
| 4 | Wed 11 Nov | 8 | Lucia, Jason and the cast Rockstar has named | people beat sheet, official art | to research |
| 5 | Thu 12 Nov | 7 | Trailer 2 read closely | trailer breakdown | to research |
| 6 | Fri 13 Nov | 6 | Confirmed against rumour (رسمي / تقرير / شائعة), nothing leaked or datamined shown | explainer | to research |
| 7 | Sat 14 Nov | 5 | Editions, pre-orders, Gulf prices read from PS Store and Xbox UAE and Saudi (AED with the dirham sign, SAR as shown) | WHERE AND HOW MUCH frame | prices read the day before |
| 8 | Sun 15 Nov | 4 | Platforms at launch and exactly what Rockstar has said about PC | split | to research |
| 9 | Mon 16 Nov | 3 | The long road: release gaps across the series and this game's delays, dated from Rockstar's announcements | timeline | to research |
| 10 | Tue 17 Nov | 2 | Launch week in the Gulf: midnight events as announced, the regional rating as the authorities state it | split | to research |
| 11 | Wed 18 Nov | 1 | Review scores at the embargo (reviewscores) or the first hours: preload times in Dubai time, size, day-one patch | reviewscores or split | embargo time to confirm |
| 12 | Thu 19 Nov | 0 | Launch day, out now, WHERE AND HOW MUCH with the Gulf prices | release beat sheet | launch day |

## Sources (official only)
- **L**: Rockstar launch trailer, 15 Oct 2026 (PlayStation-branded copy on IGN, 90.0 s, 3840x2160 and 1920x1080 MP4,
  `https://assets.ign.com/videos/mediaconvert/2026/10/15/<width>/5a1ba86e-5f70-46c6-be76-e83223a908cc-1792069737.mp4`;
  decode clean; the first 2 s and last 4 s are PlayStation and ESRB slates, never used). Intro: L 25.15 to 27.18 s.
- Trailer 1 and Trailer 2: plain-MP4 routes to find (IGN video pages, Rockstar's press site); YouTube refuses the server.

## Ledger: shots and sound per episode
Rule (as the Ocarina series): no shot and no audio stretch in two episodes. Check a new episode's shot list and track
against this table before its shot sheet; add its row once final. Times are seek seconds in the named source.

| # | Shots (source: start to end) | Sound (source: stretch) |
|---|---|---|
| intro | L 25.15 to 27.18 (fixed, every episode) | gtavi jingle (fixed) |
| 1 | L 54.55 to 56.35; L 66.45 to 67.85; L 2.2 to 5.8 (card 1 ground); L 46.35 to 50.65; L 6.4 to 10.0 (card 2 ground); L 67.9 to 69.25; L 73.2 to 75.6 | L music stem from 28.7 for 16.0 s (music_only) |
