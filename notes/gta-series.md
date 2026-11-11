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
| 1 | Sun 8 Nov | 11 | Why this launch matters: the series in Take-Two's own numbers (GTA V lifetime units, years since its launch, the gap since GTA IV) | numbers, clipcard on Rockstar footage | built v3, director PASS; handed to Production 2 for 8 Nov ~20:00 Dubai |
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
| 1 | L 54.55 to 56.35; L 20.65 to 22.05; L 2.2 to 5.8 (card 1 ground); L 46.35 to 50.65; L 6.4 to 10.0 (card 2 ground); L 67.9 to 69.25; L 74.0 to 75.9 | L music stem from 28.7 for 15.5 s (music_only) |

## Batch of 11 Nov 2026 (studio order, Mohammad): episodes 2 to 9, one a day at 20:00 Dubai, 12 to 19 Nov

This plan replaces the 8 Nov plan above from episode 2 on (episodes 2 to 12 of that plan were never built; episode 1 ran
8 Nov). Countdown from gta_intro.LAUNCH (19 Nov 2026). Footage: Rockstar's own masters (Launch Trailer `Lm` and the
Extended Look `XL`, read by stream), Trailers 1 and 2 (`T1`, `T2`, IGN 3840 copies), PlayStation's PS5 features
trailer, the Pre-Load Now and cover art videos, the Trilogy Definitive Edition trailer (2021) and the GTA V trailer
(2014). Sources: newsroom/context/gta-vi.md and gta-series-history.md; prices and store times re-read on the day.

| # | Dubai date | Days | Subject | Template |
|---|---|---|---|---|
| 2 | Thu 12 Nov | 7 | Leonida's six places, from Rockstar's own descriptions | trailer |
| 3 | Fri 13 Nov | 6 | Jason and Lucia, from Rockstar's character pages | trailer |
| 4 | Sat 14 Nov | 5 | The three trailers, least to most surprising | trailer |
| 5 | Sun 15 Nov | 4 | From GTA III to GTA VI (years from Take-Two's filings) | trailer, our bed |
| 6 | Mon 16 Nov | 3 | What you can do: the Extended Look's activities; PS5 controller features | trailer |
| 7 | Tue 17 Nov | 2 | Editions, Gulf prices (WHERE AND HOW MUCH frame), pre-load | split |
| 8 | Wed 18 Nov | 1 | The unlock hour in the UAE and Saudi Arabia (PS Store), Xbox hour not given | trailer |
| 9 | Thu 19 Nov | 0 | Out now; the series closes | trailer |

No numbers card in the batch (the order allows at most one). Music: Mohammad listed seven subjects for eight slots; the
eighth is the gameplay episode (6). A music episode was not built: no official score file is published.

Ledger rows (shots and sound; times are seek seconds in the named source):

| # | Shots | Sound |
|---|---|---|
| 2 | T1 11.4 to 14.7; T1 31.1 to 32.5; still rs-vice-city-03.jpg; T1 39.9 to 41.2; still rs-leonida-keys-01.jpg; T1 36 to 37.2; T1 19 to 21.6; still rs-grassrivers-05.jpg; still rs-port-gellhorn-06.jpg; still rs-ambrosia-04.jpg; still rs-mount-kalaga-national-park-04.jpg; T1 23.4 to 24.7; still rs-vice-city-15.jpg | T1 music stem from 11.4 (music_only) |
| 3 | Lm 26.45 to 27.75; T2 63.3 to 66.3; T2 115.2 to 118; Lucia clip 0 to 1.5; T2 27.4 to 31.2; Jason clip 0 to 1; T2 66.4 to 69.5; T2 98.4 to 99.5; T2 152.6 to 156 | T1 music stem from 45 (music_only) |
| 4 | T2 35.7 to 37.6; Lm 33.3 to 34.9; Lm 12.4 to 15.4; T2 51.05 to 51.8; T2 6.6 to 8.3; T2 8.55 to 9.45; T2 83.3 to 85.8; T2 52.6 to 55.9; T1 3.6 to 6.4; T1 61 to 63.5; T1 45.4 to 46.5; T1 70.4 to 72.5; T1 10.3 to 11.2; T1 27.4 to 28.8; still rs-vice-city-11.jpg | T2 music stem from 117.3 (music_only) |
| 5 | V14 15.4 to 17; V14 38.4 to 39.9; TRI 11.8 to 14.2; TRI 28.4 to 30.2; TRI 16.4 to 19.4; TRI 34.6 to 36.2; TRI 4 to 5.4; TRI 21.05 to 22.85; TRI 44.55 to 45.4; V14 24.6 to 26.55; V14 29.35 to 30.55; V14 44.7 to 46.2; XL 992.8 to 995.9; XL 995.9 to 999.2 | our gtavi bed |
| 6 | XL 1037 to 1038.9; XL 1030 to 1032.8; XL 1062 to 1064.55; XL 1064.55 to 1067.45; XL 1086.1 to 1089.5; XL 1033.05 to 1035.9; PS5 19.4 to 23; PS5 34.45 to 35.7; still rs-vice-city-17.jpg | PS5 music stem from 3 (music_only) |
| 7 | PL 11.25 to 12.6; XL 776 to 777.5; XL 758 to 761; XL 770 to 772.6; XL 765 to 769.6; XL 782.3 to 785.9 | COV music stem from 7.5 (music_only) |
| 8 | XL 1208 to 1211.3; XL 1211.3 to 1213.95; XL 1214.05 to 1215.65; XL 1545 to 1548.4; XL 1231.4 to 1232.7; still rs-vice-city-08.jpg; still rs-vice-city-27.jpg | Lm music stem from 3 (music_only) |
| 9 | T2 149.3 to 150.65; Lm 3.5 to 4.85; T2 147.4 to 148.4; T2 138.6 to 139.5; T2 134.55 to 137.3; T2 118.85 to 119.65; T2 141.85 to 143.6; Lm 70 to 71.4; Lm 71.4 to 72.4; XL 1551 to 1552.35; Lm 18.4 to 19.4; still rs-vice-city-10.jpg | Lm music stem from 44.5 (music_only) |
