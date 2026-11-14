# Work order, Sat 14 Nov 21:27 Dubai

Production 2: execute this work order top to bottom. Clear the alarms first, then the orders (T0 first), then the handoffs oldest first, then the scout (fresh digest with the forced refspec; carried leads first), then fill the next slot under the caps. Report each item on the board with evidence: "wo <generated_at> item <n>: <outcome> (evidence)".

Posts read from: commitments and format ledger.

## 1. Alarms to clear first
1. ALARM unacked: handoff p1-20261114-nintendo-6-2-billion-claimed to Production 2 unacknowledged 258 min (from production-1 at 17:08). Clears with: this run's board line: ack: p1-20261114-nintendo-6-2-billion-claimed (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
2. ALARM unacked: handoff p1-20261114-nintendo-6-2-billion-posted to Production 2 unacknowledged 222 min (from production-1 at 17:45). Clears with: this run's board line: ack: p1-20261114-nintendo-6-2-billion-posted (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
3. ALARM unacked: handoff p1-20261114-gtavi-ep4-regate to Production 2 unacknowledged 221 min (from production-1 at 17:46). Clears with: this run's board line: ack: p1-20261114-gtavi-ep4-regate (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
4. ALARM unacked: handoff p1-20261114-gtavi-ep4-published to Production 2 unacknowledged 81 min (from production-1 at 20:05). Clears with: this run's board line: ack: p1-20261114-gtavi-ep4-published (scheduled HH:MM Dubai | building, target HH:MM | declined: reason).
5. ALARM publer: keeper coverage stale: no Publer read in 15 min (the server sent no Publer read; server pass Sat 14 Nov 21:27 Dubai). Clears with: Production 1: check dxb-keeper.timer and /etc/dxb-keeper/publer.key on dxb-render-1 (backoffice-install keeper).
6. ALARM dispatches: Reel blood-of-dawnwalker-update-1-2-new-game-plus-20261114 took 3 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
7. ALARM dispatches: Reel epic-free-games-alien-isolation-mark-of-the-deep-nov-19-20261114 took 3 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
8. ALARM dispatches: Reel forest-escape-last-train-rainbow-location-november-14 took 6 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
9. ALARM dispatches: Reel forza-horizon-6-roadmap-series-8-9-20261114 took 5 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
10. ALARM dispatches: Reel hela-of-mice-and-magic-dec-1-20261114 took 3 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
11. ALARM dispatches: Reel lol-esports-2027-worlds-nagoya-first-stand-all-in-20261114 took 5 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
12. ALARM dispatches: Reel mitsuda-dragon-quest-end-for-now-blog took 3 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
13. ALARM dispatches: Reel ps5-qssr-spider-man-2-control-resonant-november-13 took 5 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
14. ALARM dispatches: Reel queens-domain-200k-sales-two-weeks-20261114 took 4 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
15. ALARM dispatches: Reel rob-run-365k-concurrent-steam-20261114 took 6 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
16. ALARM dispatches: Reel spirit-crossing-launch-november-16 took 5 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
17. ALARM dispatches: Reel super-meat-boy-again-plus-announced-november-14 took 4 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.
18. ALARM dispatches: Reel where-winds-meet-anniversary-beyond-20261114 took 3 renders in 24 hours (target 1): run textrules.py and prerender mode text before dispatching, and take shots from prerender mode shots. Clears with: the next render of a story passes in one dispatch.

## 2. Mohammad's orders (T0 first)
none

## 3. Open handoffs to Production 2 (oldest first)
19. p1-20261111-gta-batch-slots (from production-1, Wed 11 Nov 21:31 Dubai): Production 2: leave 16:00Z free on 12 to 19 Nov; ack this line. Due Wed 11 Nov 22:31 Dubai, OVERDUE; NOT acknowledged.
20. p1-20261111-gate-frame-credit (from production-1, Wed 11 Nov 22:06 Dubai): Jobs with a frame: put credits on the shots either side of the frame shot, and cut the frame shot to the frame's length. Due Wed 11 Nov 23:06 Dubai, OVERDUE; NOT acknowledged.
21. p1-20261111-bethesda-rerender (from production-1, Wed 11 Nov 22:13 Dubai): Production 2: expect the Bethesda render commit on main; schedule it as you planned. Nothing to redo on your side. Due Wed 11 Nov 23:13 Dubai, OVERDUE; NOT acknowledged.
22. p1-20261111-bethesda-rerender-result (from production-1, Wed 11 Nov 22:15 Dubai): Production 2 fixes the job file and dispatches it; the runner then has GTA renders queued ahead (about 8 min each) Due Wed 11 Nov 23:15 Dubai, OVERDUE; NOT acknowledged.
23. p1-20261111-gtavi-ep2-scheduled (from production-1, Wed 11 Nov 22:21 Dubai): news lane leaves 20:00 Dubai free 12 to 19 Nov; episodes 3 to 9 follow as each passes the director Due Wed 11 Nov 23:21 Dubai, OVERDUE; NOT acknowledged.
24. p1-20261111-gtavi-ep8-scheduled (from production-1, Thu 12 Nov 00:55 Dubai): news lane leaves 18 Nov 20:00 Dubai free; re-gated on its day before 20:00 Dubai Due Thu 12 Nov 01:55 Dubai, OVERDUE; NOT acknowledged.
25. p1-20261111-actions-outage (from production-1, Thu 12 Nov 01:00 Dubai): Production 2: any news render dispatched now will sit queued or fail at startup; re-dispatch after githubstatus shows Actions operational. The GTA renders go first in the queue only for ep3 (slot 13 Nov 20:00 Dubai); news may go ahead of ep4 to ep9 Due Thu 12 Nov 02:00 Dubai, OVERDUE; NOT acknowledged.
26. p1-20261111-gtavi-ep6-scheduled (from production-1, Thu 12 Nov 01:40 Dubai): News lane leaves 16 Nov 20:00 Dubai free; re-gate on the day before 20:00 (series rule 5) Due Thu 12 Nov 02:40 Dubai, OVERDUE; NOT acknowledged.
27. p1-20261111-gtavi-ep7-scheduled (from production-1, Thu 12 Nov 02:22 Dubai): News lane leaves 17 Nov 20:00 Dubai free; re-read every price on the day before 20:00 (series rule 5) Due Thu 12 Nov 03:22 Dubai, OVERDUE; NOT acknowledged.
28. p1-20261111-gtavi-ep9-scheduled (from production-1, Thu 12 Nov 02:35 Dubai): News lane leaves 19 Nov 20:00 Dubai free; on 19 Nov re-read rockstargames.com/VI before 20:00 (the page must say it is out; hold on any change, series rule 5) Due Thu 12 Nov 03:35 Dubai, OVERDUE; NOT acknowledged.
29. p1-20261111-gtavi-ep5-scheduled (from production-1, Thu 12 Nov 02:42 Dubai): News lane leaves 15 Nov 20:00 Dubai free; re-gate on the day before 20:00 (series rule 5) Due Thu 12 Nov 03:42 Dubai, OVERDUE; NOT acknowledged.
30. p1-20261111-gtavi-ep3-scheduled (from production-1, Thu 12 Nov 03:19 Dubai): news lane leaves 13 Nov 20:00 Dubai free; re-gate on the day before 20:00 (series rule 5) Due Thu 12 Nov 04:19 Dubai, OVERDUE; NOT acknowledged.
31. p1-20261112-gtavi-ep4-scheduled (from production-1, Thu 12 Nov 04:09 Dubai): news lane leaves 20:00 Dubai free 12 to 19 Nov; re-gate each on its day before 20:00 (series rule 5) Due Thu 12 Nov 05:09 Dubai, OVERDUE; NOT acknowledged.
32. p1-20261112-release-r1 (from production-1, Thu 12 Nov 17:20 Dubai): Production 2: rebuild any numbers/list job in flight with footage behind the cards (ground_footage) or fewer card seconds; footage Reels under 12 s need another beat; ops/production-setup.md line 11 Due Thu 12 Nov 18:20 Dubai, OVERDUE; NOT acknowledged.
33. p1-20261112-release-r2 (from production-1, Thu 12 Nov 17:21 Dubai): Production 2: add subject_person to every story file you build from now (null for most); new kind people (trailer or quote); ops/production-setup.md line 12 Due Thu 12 Nov 18:21 Dubai, OVERDUE; NOT acknowledged.
34. p1-20261112-release-r3 (from production-1, Thu 12 Nov 17:23 Dubai): Production 2: jobs in flight without a track get one from their trailer, or a bed_reason; ops/production-setup.md line 13 Due Thu 12 Nov 18:23 Dubai, OVERDUE; NOT acknowledged.
35. p1-20261112-release-r4 (from production-1, Thu 12 Nov 17:24 Dubai): Mohammad (root, dxb-render-1): install /etc/dxb-scout/agentmail.key (three lines in ops/build/releases/2026-11-12-r4.md); Production 2: ops/production-setup.md line 14 Due Thu 12 Nov 18:24 Dubai, OVERDUE; NOT acknowledged.
36. p1-20261112-gtavi-ep2-regate (from production-1, Thu 12 Nov 17:25 Dubai): Production 1: slot check 16:03Z; Production 2: keep 20:00 Dubai free Due Thu 12 Nov 18:25 Dubai, OVERDUE; NOT acknowledged.
37. p1-20261112-gtavi-ep2-published (from production-1, Thu 12 Nov 20:11 Dubai): ep3 re-gate fires before 20:00 Dubai 13 Nov; 20:00 Dubai stays free for the series through 19 Nov Due Thu 12 Nov 21:11 Dubai, OVERDUE; NOT acknowledged.
38. p1-20261113-gtavi-ep3-regate (from production-1, Fri 13 Nov 17:41 Dubai): slot check at 16:04Z from this session; Production 2: if your Publer works, confirm the three ep3 posts still read scheduled for 20:00 Dubai Due Fri 13 Nov 18:41 Dubai, OVERDUE; NOT acknowledged.
39. p1-20261113-gtavi-ep3-published (from production-1, Fri 13 Nov 20:15 Dubai): ep4 re-gate fires 13:00Z on 14 Nov; 20:00 Dubai stays free for the series through 19 Nov Due Fri 13 Nov 21:15 Dubai, OVERDUE; NOT acknowledged.
40. p1-20261113-albw-nso-badge-published (from production-1, Fri 13 Nov 20:15 Dubai): none Due Fri 13 Nov 21:15 Dubai, OVERDUE; NOT acknowledged.
41. p1-20261114-nintendo-6-2-billion-claimed (from production-1, Sat 14 Nov 17:08 Dubai): Production 2: skip this story and keep it out of your slots; the posted line follows Due Sat 14 Nov 18:08 Dubai, OVERDUE; NOT acknowledged.
42. p1-20261114-nintendo-6-2-billion-posted (from production-1, Sat 14 Nov 17:45 Dubai): Production 2: none. Story closed; any follow-up only with new figures from Nintendo. Due Sat 14 Nov 18:45 Dubai, OVERDUE; NOT acknowledged.
43. p1-20261114-gtavi-ep4-regate (from production-1, Sat 14 Nov 17:46 Dubai): Production 2: keep 20:00 Dubai free; slot check 16:03Z by Production 1. Due Sat 14 Nov 18:46 Dubai, OVERDUE; NOT acknowledged.
44. p1-20261114-gtavi-ep4-published (from production-1, Sat 14 Nov 20:05 Dubai): Production 2: none. Next episode ep5 tomorrow 20:00 Dubai (re-gate 13:00Z). Due Sat 14 Nov 21:05 Dubai, OVERDUE; NOT acknowledged.

## 4. Digest and the scout
45. Digest head: seq 478 at Sat 14 Nov 20:52 Dubai, 35 min old. Read it with git fetch -q origin +watch-digest:refs/remotes/origin/watch-digest and print "digest seq read: N (branch head N)".
46. Scout first (Haiku, at most five leads, rejection reasons: no_source, denied, harmful_or_out_of_scope, duplicate). The orders and handoffs above are not scout leads to judge: build them from the source they name. Coverage over caution (r4): search for each story itself (a web search, the outlet it came from, the press wires); a credible outlet is a source (تقرير), an official video or press release a primary; no_source only after that search, confirmed by the editor. Carried from no recent run: no leads carried
   - scout verdict lines: not read on the server (no server read)

## 5. Next slot
47. next slot: due by Sun 15 Nov 00:15 Dubai (covered until 23:15); earliest 23:45 under the spacing

## 6. Caps
48. Evergreen: allowed; by day evergreen only fills a gap no news can fill, after a logged news search beyond the digest.
49. Numbers: allowed.
50. Card-led window: 0 of the last 5 card-led (at most 2 in 6); last templates stills, stills, split.
