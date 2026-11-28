# Work order, Sun 29 Nov 01:27 Dubai

Production 2: execute this work order top to bottom. Clear the alarms first, then pick up what the last run left unfinished, then the orders (T0 first), then the handoffs oldest first, then the scout (fresh digest with the forced refspec; carried leads first), then fill the next slot under the caps. Report each item on the board with evidence: "wo <generated_at> item <n>: <outcome> (evidence)".

Posts read from: commitments, format ledger, submissions and published logs (no server Publer read).

## 1. Alarms to clear first
1. ALARM serverpost-ready: schedule ffxv-10th-anniversary-square-enix-famitsu at Sat 28 Nov 20:45 Dubai through the Publer connector: instagram Sat 28 Nov 20:45 Dubai; x Sat 28 Nov 20:45 Dubai; threads Sat 28 Nov 20:45 Dubai (texts and labels in the story file; check Publer first (scheduled and the last 48 hours published, publercheck.py), schedule through the Publer connector at the slot with the labels (each network at its time in "networks"; X and Threads with the story's reel_x and reel_threads when a quick post went out), then serverpost.py scheduled). Clears with: serverpost.py scheduled <story> --slot <ISO> after the submit reads complete.
2. ALARM serverpost-ready: schedule subnautica-2-tar-trek-dec-1-steam at Sat 28 Nov 22:00 Dubai through the Publer connector: instagram Sat 28 Nov 22:00 Dubai; x Sat 28 Nov 22:00 Dubai; threads Sat 28 Nov 22:00 Dubai (texts and labels in the story file; check Publer first (scheduled and the last 48 hours published, publercheck.py), schedule through the Publer connector at the slot with the labels (each network at its time in "networks"; X and Threads with the story's reel_x and reel_threads when a quick post went out), then serverpost.py scheduled). Clears with: serverpost.py scheduled <story> --slot <ISO> after the submit reads complete.
3. ALARM serverpost-held: warframe-tau-gameplay-trailer-dec-9-gonintendo held by the server: second factual_error verdict on the fixed Reel: held, never posted with a known wrong fact or graphic content; Mohammad decides. Clears with: a director file with job_patch or pass, or Mohammad decides.
4. ALARM serverpost-ready: schedule warframe-tau-gameplay-trailer-dec-9-gonintendo at Sun 29 Nov 00:00 Dubai through the Publer connector: instagram Sun 29 Nov 00:00 Dubai; x Sun 29 Nov 00:00 Dubai; threads Sun 29 Nov 00:00 Dubai (texts and labels in the story file; fix render of factual_error landed (warframe-tau-gameplay-trailer-dec-9-gonintendo-reel-v2.mp4); scheduled as fixed; check Publer first (scheduled and the last 48 hours published, publercheck.py), schedule through the Publer connector at the slot with the labels (each network at its time in "networks"; X and Threads with the story's reel_x and reel_threads when a quick post went out), then serverpost.py scheduled). Clears with: serverpost.py scheduled <story> --slot <ISO> after the submit reads complete.
5. ALARM serverpost-ready: schedule gta-vi-all-achievements-152-hours-xbox-destructoid at Sun 29 Nov 01:00 Dubai through the Publer connector: instagram Sun 29 Nov 01:00 Dubai; x Sun 29 Nov 01:00 Dubai; threads Sun 29 Nov 01:00 Dubai (texts and labels in the story file; check Publer first (scheduled and the last 48 hours published, publercheck.py), schedule through the Publer connector at the slot with the labels (each network at its time in "networks"; X and Threads with the story's reel_x and reel_threads when a quick post went out), then serverpost.py scheduled). Clears with: serverpost.py scheduled <story> --slot <ISO> after the submit reads complete.

## 1a. Notes (not alarms; act when the story allows)
- unacked: handoff director-20261128-silksong-sea-of-sorrow-v2 to Production 2 unacknowledged 1260 min (from Production 1 at 04:26). Clears with: this run's board line: ack: director-20261128-silksong-sea-of-sorrow-v2 (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- mirror: inbox mirror export is 997 min old (desk/mirror.json Sat 28 Nov 08:49 Dubai). Clears with: Production 1: run the inbox mirror task.
- publer: keeper coverage stale: no Publer read in 15 min (the server sent no Publer read; server pass Sun 29 Nov 01:27 Dubai). Clears with: Production 1: check dxb-keeper.timer and /etc/dxb-keeper/publer.key on dxb-render-1 (backoffice-install keeper).
- director fix render: warframe-tau-gameplay-trailer-dec-9-gonintendo rendering once more (factual_error: Retitle as footage from Warframe before the Tau update and credit the footage as earlier trailers, not the Tau trailer.), then scheduled. Clears with: the new Reel lands and the server schedules it.

## 1b. Unfinished from the last run (pick up first)
none

## 2. Mohammad's orders (T0 first)
none

## 3. Open handoffs to Production 2 (oldest first)
6. release-20261127-shot-rules (from Production 1, Fri 27 Nov 11:22 Dubai): dispatch gta-vi-no-chainsaw-katana-rockstar-vgc on main; shorten the Silent Hill headline Due Fri 27 Nov 12:22 Dubai, OVERDUE; NOT acknowledged.
7. fix-20261127-render-lane (from Production 1, Fri 27 Nov 21:03 Dubai): fix the chainsaw job lines to 9 shots and dispatch render-live; dispatch slip.yml for every slip pushed Due Fri 27 Nov 22:03 Dubai, OVERDUE; NOT acknowledged.
8. director-20261128-silksong-sea-of-sorrow-v2 (from Production 1, Sat 28 Nov 04:26 Dubai): Director verdict on v2 (not by Production 1); on pass schedule 28 Nov 20:00 Dubai, three networks, labels as listed Due Sat 28 Nov 05:26 Dubai, OVERDUE; NOT acknowledged.

## 4. Digest and the scout
9. Digest head: seq 977 at Sun 29 Nov 00:52 Dubai, 35 min old. Read it with git fetch -q origin +watch-digest:refs/remotes/origin/watch-digest and print "digest seq read: N (branch head N)".
10. Scout first (Haiku, at most five leads, rejection reasons: no_source, denied, harmful_or_out_of_scope, duplicate). The orders and handoffs above are not scout leads to judge: build them from the source they name. Coverage over caution (r4): search for each story itself (a web search, the outlet it came from, the press wires); a credible outlet is a source (تقرير), an official video or press release a primary; no_source only after that search, confirmed by the editor. Carried from no recent run: no leads carried
   - scout verdict lines: not read on the server (no server read)

## 5. Next slot
11. next slot: OVERDUE, nothing since Fri 27 Nov 21:30 Dubai (gap limit 60 min passed at 22:30)

## 6. Caps
12. Evergreen: allowed.
13. Numbers: allowed.
14. Card-led window: 0 of the last 5 card-led (at most 2 in 6); last templates trailer, trailer, trailer.

## 7. Last five renders, minutes per stage (for information)
none read

## 8. Names to review (written in Latin on screen; add an Arabic form to newsroom/names-ar.md)
- Siliconera (2026-11-25-witchbrook-gone-gold-siliconera)
- Chucklefish (2026-11-25-witchbrook-gone-gold-siliconera)
- Mike Booth (2026-11-26-4-loop-closed-beta-dec-10-gamespark)
- Unsolved Hunts (2026-11-26-ac-black-flag-resynced-treasure-hunt-games-press)
- DeadPixel Studios (2026-11-26-croaked-free-demo-nov-27-steam-games-press)
- Pond Loop (2026-11-26-croaked-free-demo-nov-27-steam-games-press)
- Team Cherry (2026-11-26-hollow-knight-silksong-cherry-time-nov-27-nintendo-everything)
- Low Orbit Games (2026-11-26-orion-space-4x-early-access-dec-14-games-press)
- Feardemic (2026-11-26-retail-hell-consoles-gematsu)
- LEAP Game Studios (2026-11-26-retail-hell-consoles-gematsu)
- Kusa Games (2026-11-26-split-brain-samsara-launch-steam-games-press)
- GT Planet (2026-11-27-gta-vi-car-physics-gran-turismo-pro-push-square)
- Lewis Bentley (2026-11-27-gta-vi-car-physics-gran-turismo-pro-push-square)
- Rockstar (2026-11-27-gta-vi-car-physics-gran-turismo-pro-push-square)
- Rob Nelson (2026-11-27-gta-vi-no-chainsaw-katana-rockstar-vgc)
- GameSpark (2026-11-27-iron-sirocco-mech-survivor-announced-gamespark)
- Konami (2026-11-27-silent-hill-f-2-72-off-steam-black-friday-famitsu)
- Archetype Entertainment (2026-11-28-exodus-pc-requirements-saudi-gamer)
- KINDA (2026-11-28-fumes-kinda-rally-update-gamespark)
- Destructoid (2026-11-28-gta-vi-all-achievements-152-hours-xbox-destructoid)
- Nexon (2026-11-28-maplestory-overdrive-dec-9-damage-cap-automaton)
- GamingTrend (2026-11-28-professor-layton-new-world-of-steam-finished-dec-1-event-gamingtrend)
- LEVEL5 (2026-11-28-professor-layton-new-world-of-steam-finished-dec-1-event-gamingtrend)
- QuizKnock (2026-11-28-professor-layton-new-world-of-steam-finished-dec-1-event-gamingtrend)
- Toru Minegishi (2026-11-28-tomodachi-life-living-the-dream-soundtrack-nintendo-music-nintendo-life)
