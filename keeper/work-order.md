# Work order, Sat 21 Nov 22:27 Dubai

Production 2: execute this work order top to bottom. Clear the alarms first, then pick up what the last run left unfinished, then the orders (T0 first), then the handoffs oldest first, then the scout (fresh digest with the forced refspec; carried leads first), then fill the next slot under the caps. Report each item on the board with evidence: "wo <generated_at> item <n>: <outcome> (evidence)".

Posts read from: commitments, format ledger, submissions and published logs (no server Publer read).

## 1. Alarms to clear first
none

## 1a. Notes (not alarms; act when the story allows)
- unacked: handoff p1-20261120-no-rejection-rule to Production 2 unacknowledged 1367 min (from Production 1 (build, Mohammad order 22:20 Dubai) at 23:40). Clears with: this run's board line: ack: p1-20261120-no-rejection-rule (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- unacked: handoff build-20261121-started to Production 2 unacknowledged 1271 min (from Production 1 (build desk, bound) at 01:16). Clears with: this run's board line: ack: build-20261121-started (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- unacked: handoff p1-20261121-gta-vi-user-score-debate to Production 2 unacknowledged 924 min (from Production 1 at 07:03). Clears with: this run's board line: ack: p1-20261121-gta-vi-user-score-debate (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- unacked: handoff digest-20261121-posted to Production 2 unacknowledged 905 min (from Production 1 (morning digest, bound) at 07:22). Clears with: this run's board line: ack: digest-20261121-posted (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- unacked: handoff p1-20261121-credit-ladder to Production 2 unacknowledged 825 min (from Production 1 (build, Mohammad order 21 Nov) at 08:42). Clears with: this run's board line: ack: p1-20261121-credit-ladder (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
- caps: post Sat 21 Nov 21:30 Dubai (scheduled, trailer, news) is outside the caps: third trailer in a row. Clears with: move or replace the post if it is still scheduled; if it went out, say why on the board.
- caps: post Sat 21 Nov 21:30 Dubai (scheduled, trailer, news) is outside the caps: trailer 8 times on Dubai day 2026-11-21 (at most 4). Clears with: move or replace the post if it is still scheduled; if it went out, say why on the board.
- mirror: inbox mirror export is 518 min old (desk/mirror.json Sat 21 Nov 13:49 Dubai). Clears with: Production 1: run the inbox mirror task.
- publer: keeper coverage stale: no Publer read in 15 min (the server sent no Publer read; server pass Sat 21 Nov 22:27 Dubai). Clears with: Production 1: check dxb-keeper.timer and /etc/dxb-keeper/publer.key on dxb-render-1 (backoffice-install keeper).

## 1b. Unfinished from the last run (pick up first)
none

## 2. Mohammad's orders (T0 first)
none

## 3. Open handoffs to Production 2 (oldest first)
1. p1-20261119-names-hard-stops (from Production 1 (build), Thu 19 Nov 06:38 Dubai): Production 2: before every job or slip, put the game's name in Latin in the headline, never in Arabic letters, add new outlets and studios to names-ar first, and run the grammar stage on slips. Replay: 19 of the last 20 Reels would have stopped under these rules. Due Thu 19 Nov 07:38 Dubai, OVERDUE; NOT acknowledged.
2. digest-20261119-posted (from Production 1 (morning digest, bound), Thu 19 Nov 07:22 Dubai): none for Production 2; desk audit lines unchanged (disk cleanup question already open) Due Thu 19 Nov 08:22 Dubai, OVERDUE; NOT acknowledged.
3. p1-20261119-gta-series-closed (from production-1, Thu 19 Nov 20:05 Dubai): 20:00 Dubai is free for news from 20 Nov Due Thu 19 Nov 21:05 Dubai, OVERDUE; NOT acknowledged.
4. build-20261120-started (from Production 1 (build desk, bound), Fri 20 Nov 01:16 Dubai): none tonight; Mohammad to retire or rewrite this bound task (question below) Due Fri 20 Nov 02:16 Dubai, OVERDUE; NOT acknowledged.
5. digest-20261120-posted (from Production 1 (morning digest, bound), Fri 20 Nov 07:22 Dubai): Production 2: overnight gaps 23:04 to 02:03 and 03:04 to 07:30 Dubai (spacing rule); audit lines unchanged Due Fri 20 Nov 08:22 Dubai, OVERDUE; NOT acknowledged.
6. p1-20261120-showcase-fallback (from Production 1 (build, Mohammad order), Fri 20 Nov 12:45 Dubai): Production 2: Witch on the Holy Night: set "layout": "showcase" with a showcase_reason naming the clash (subtitles and credit card), render once, then build Girls' Frontline: Blue Covenant and the sourced items rejected this morning (FF14 first); keep 30-minute spacing Due Fri 20 Nov 13:45 Dubai, OVERDUE; NOT acknowledged.
7. p1-20261120-lane-revert (from Production 1 (build, Mohammad order), Fri 20 Nov 16:20 Dubai): Production 2: do not dispatch more renders of these two until Production 1 writes "lane restored". Found: a job carrying a leftover "shots_auto" list has its explicit shot times overwritten by the server; remove that key when you write explicit shots (fixed on the GTA VI job).... Due Fri 20 Nov 17:20 Dubai, OVERDUE; NOT acknowledged.
8. p1-20261120-lane-restored (from Production 1 (build, Mohammad order), Fri 20 Nov 17:50 Dubai): Production 2: dispatch renders as normal. Keep credits short when a job may fall to the showcase layout (the GTA credit 'المصدر: في جي سي (VGC)، ولقطات من روكستار (Rockstar Games)' ran out of the band). Server has one runner instance, so the second job overflows to GitHub runn... Due Fri 20 Nov 18:50 Dubai, OVERDUE; NOT acknowledged.
9. p1-20261120-slip-lane-headline (from Production 1 (build, Mohammad order), Fri 20 Nov 21:05 Dubai): Production 2: do not hand-edit these two jobs. Production 1 merges after the replay (last 10 jobs/done plus both slip jobs on the branch), re-dispatches both as the slip lane wrote them, and writes 'automatic lane restored' here only when both pass. Due Fri 20 Nov 22:05 Dubai, OVERDUE; NOT acknowledged.
10. p1-20261120-automatic-lane-restored (from Production 1 (build, Mohammad order), Fri 20 Nov 21:20 Dubai): Production 2: both Reels are yours to judge and schedule. Look first: the GTA VI CDPR Reel's picture is the PlayStation page's generic ident (abstract cubes and light, no GTA VI footage at all), and Ace Combat 8 sits on the 30th anniversary emblem for most of its length with o... Due Fri 20 Nov 22:20 Dubai, OVERDUE; NOT acknowledged.
11. p1-20261120-no-rejection-rule (from Production 1 (build, Mohammad order 22:20 Dubai), Fri 20 Nov 23:40 Dubai): Production 2: slips build as written; a slip's footage_pick is ignored when the library has the game; the credit field keeps only the news source, the footage clause is written by the server. Send a Reel back only for an untrue text or text an Arab reader cannot follow (or gra... Due Sat 21 Nov 00:40 Dubai, OVERDUE; NOT acknowledged.
12. build-20261121-started (from Production 1 (build desk, bound), Sat 21 Nov 01:16 Dubai): none tonight; question q-20261120-bound-build-desk (retire or rewrite this bound task) still open for Mohammad Due Sat 21 Nov 02:16 Dubai, OVERDUE; NOT acknowledged.
13. p1-20261121-gta-vi-user-score-debate (from Production 1, Sat 21 Nov 07:03 Dubai): if approved by 10:30 Dubai Production 1 schedules it at 11:00 Dubai (IG, X, Threads); otherwise in the 23:00 to 01:00 window tonight, not 20:00. Production 2: keep 10:30 to 11:30 Dubai free of other GTA VI posts Due Sat 21 Nov 08:03 Dubai, OVERDUE; NOT acknowledged.
14. digest-20261121-posted (from Production 1 (morning digest, bound), Sat 21 Nov 07:22 Dubai): Production 2: fill the gap now; decide on the Denfaminicogamer user score Reel (the debate Reel waits for Mohammad for 11:00) Due Sat 21 Nov 08:22 Dubai, OVERDUE; NOT acknowledged.
15. p1-20261121-credit-ladder (from Production 1 (build, Mohammad order 21 Nov), Sat 21 Nov 08:42 Dubai): write credits as before (Arabic then Latin in brackets); the server shortens them. Add a short name to names-ar section 4 when a long name first needs one Due Sat 21 Nov 09:42 Dubai, OVERDUE; NOT acknowledged.

## 4. Digest and the scout
16. Digest head: seq 725 at Sat 21 Nov 21:52 Dubai, 35 min old. Read it with git fetch -q origin +watch-digest:refs/remotes/origin/watch-digest and print "digest seq read: N (branch head N)".
17. Scout first (Haiku, at most five leads, rejection reasons: no_source, denied, harmful_or_out_of_scope, duplicate). The orders and handoffs above are not scout leads to judge: build them from the source they name. Coverage over caution (r4): search for each story itself (a web search, the outlet it came from, the press wires); a credible outlet is a source (تقرير), an official video or press release a primary; no_source only after that search, confirmed by the editor. Carried from no recent run: no leads carried
   - scout verdict lines: not read on the server (no server read)

## 5. Next slot
18. next slot: due by Sat 21 Nov 23:30 Dubai (covered until 22:30); earliest 23:00 under the spacing

## 6. Caps
19. Evergreen: allowed; by day evergreen only fills a gap no news can fill, after a logged news search beyond the digest.
20. Numbers: allowed.
21. Card-led window: 1 of the last 5 card-led (at most 2 in 6); last templates trailer, showcase, numbers.

## 7. Last five renders, minutes per stage (for information)
none read

## 8. Names to review (written in Latin on screen; add an Arabic form to newsroom/names-ar.md)
- The Independent (2026-11-21-gta-vi-downing-street-british-success-story-independent)
