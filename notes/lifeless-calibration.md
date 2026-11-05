# Lifeless score: calibration (adv-20261102-borrow-openmontage, part 1)

Build night of 6 Nov 2026 (started 5 Nov 18:35Z). Score from `templates/lifeless.py` on the published files in `cards/`
(end card left out). Our own code from the idea only; nothing taken from OpenMontage (AGPLv3).

"liked": Reels Mohammad accepted, praised or chose as exemplars (`ops/exemplars/`, `newsroom/editorial-memory.md`).
"held": Reels he held or deleted (editorial memory). He has not named a list of ten liked Reels; this set is taken from
the records. The card asks for that list if it is not on record: it is asked on the board.

| set | Reel | score | still share | longest still (s) | cuts per 10 s | held under text | secs |
|---|---|---|---|---|---|---|---|
| liked | fortnite-treasure-hunters-one-piece-november-1-reel-v2 | 0.7 | 0.005 | 0.1 | 12.31 | 0.005 | 19.5 |
| liked | suda51-travis-touchdown-will-return-famitsu-reel-v1 | 9.4 | 0.098 | 1.2 | 9.79 | 0.0 | 19.4 |
| liked-storybook | oot-road-ep7-princess-and-the-desert-man-reel-v2 | 31.3 (storybook 25.9) | 0.378 | 3.4 | 3.26 | 0.004 | 46.0 |
| liked | death-stranding-isolations-teaser-t0-reel-v1 | 45.6 | 0.491 | 3.3 | 0.87 | 0.0 | 23.0 |
| liked | dark-souls-2-3-servers-down-reel-v1 | 0.0 | 0.0 | 0.0 | 7.41 | 0.0 | 21.6 |
| liked | dune-awakening-blood-and-ice-free-expansion-reel-v1 | 0.0 | 0.0 | 0.0 | 5.5 | 0.0 | 20.0 |
| liked | ocarina-of-time-review-scores-nov-4-reel-v2 | 12.6 | 0.117 | 1.6 | 7.57 | 0.049 | 48.9 |
| held | one-piece-fortnite-official-reel-v1 | 0.0 | 0.0 | 0.0 | 9.04 | 0.0 | 17.7 |
| held | zelda-ocarina-developers-interview-ask-the-developer-24-reel-v1 | 14.2 | 0.104 | 2.2 | 4.23 | 0.023 | 26.0 |
| held | nikke-pc-launcher-tampering-notice-nov-4-reel-v1 | 73.4 | 0.909 | 4.2 | 0.0 | 0.0 | 19.7 |
| held | unreal-engine-6-blueprints-removed-sweeney-tokyo-reel-v1 | 60.7 | 0.673 | 4.4 | 0.49 | 0.0 | 20.5 |
| held | macronix-exits-switch-rom-chips-nov-4-reel-v1 | 43.9 | 0.48 | 3.2 | 1.0 | 0.0 | 10.0 |
| held | ocarina-of-time-switch-2-unlock-time-nov-5-reel-v1 | 39.9 | 0.486 | 2.1 | 0.95 | 0.0 | 10.5 |

## Reading

- The held picture-poor Reels separate: the NIKKE and Unreal Engine 6 card-only Reels (73.4, 60.7), and the two
  single-image cards of 4 and 5 Nov, Macronix and the Ocarina unlock time (43.9, 39.9). Every accepted footage Reel
  scores 0 to 13.
- The score does not catch other holds and is not meant to: the One Piece blurred fill (0.0) is `fillcheck.py`'s, the
  Zelda interview's speech and drift (14.2) are the speech and motion rules'.
- Two accepted Reels sit high for a reason: the Death Stranding Isolations teaser (45.6) plays the official teaser as it
  is, with its own slow, held shots; the Ocarina episode 7 storybook (31.3, 25.9 with the storybook exception) holds
  each page alone before its line, as Mohammad asked on 31 Oct.
- held under text is near zero on every Reel: our text moves only on entry and exit now.
- The Indie World reminder (`nintendo-indie-world-oct-28-reel-v1`) was first picked as a held logo-stills Reel by
  mistake; it is the Silksong-footage reminder and scored 0.7. The held showcase Reel with the logo stills is not in
  this set.

## Proposal (after the three report-only days, Mohammad decides)

`REPAIR_AT = 38`: a score of 38 or more returns REPAIR at the director check. It would have stopped the four held
picture-poor Reels above and passed every accepted footage Reel except the Isolations teaser, which would need a
waiver written in the job (`"lifeless_ok": "official teaser played as it is"`). Storybook episodes are scored with
the stills share left out.

Until then the score is report only: render_job.py prints `render_job: lifeless:` after the decode checks and writes
`lifeless` (with `over` when the score reaches 38) to render-times.json. Nothing is refused.
