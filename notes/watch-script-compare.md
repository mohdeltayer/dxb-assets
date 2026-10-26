# Page watch: script beside the Watcher (25 Oct 2026)

Advisor Phase 1 step 5. `newsroom/watch_pages.py` reads the 10 no-feed official pages each hourly watch,
next to the Watcher (haiku). Each run: what the Watcher found on those pages, what the script found, and
any miss either way. The switch (Watcher reads only the script's "needs a look" pages) happens only if
the script caught everything the Watcher did by the end of the day.

Baseline 10:59Z: 205 article links recorded (Famitsu 63, Square Enix HD 40, Nintendo US 30, Capcom IR 23,
EA 21, Riot 9, Ubisoft 8, Bandai Namco 7, The Game Awards 3). Konami JP is drawn by script (1 link):
"needs a look", so the Watcher keeps reading it.

| Watch (UTC) | Watcher, page items | Script items | Missed by script | Missed by Watcher |
|---|---|---|---|---|
| 11:23 | none new on the 10 pages (Konami read by eye: 1 static link) | 2 Famitsu articles new to its store (Kindle Gundam sale; Nintendo Museum restaurant preview, published 14 Oct): not news, both skipped | none | none (the two Famitsu links were already in watch-seen.json) |
Fix after 11:23: Square Enix pattern matched year archive pages (/eng/news/2026/); now PDF releases only (the Watcher's note). Year-page entries dropped from page-watch-seen.json.
| 11:59 | (Watcher not re-run this hour; script only) | none new; Konami needs a look | n/a | n/a |
| 2026-10-25 13:09Z | script: 3 new (Famitsu: Blue Archive publisher to Nexon, FRONTIER PC sale, Famitsu 40th fest update); needs a look: Konami JP (1 link, drawn by script) | Watcher (haiku): the same 2 Famitsu items (Blue Archive publisher, PC sale), not the Famitsu 40th fest update (a September article URL); could not read Square Enix HD or TGA (lists drawn by script), which the script read without a flag; Konami as the script. Agree on news; the script covered more pages |
| 2026-10-25 14:08Z | script: nothing new; Konami needs a look | Watcher (haiku): repeated the 13:09Z Famitsu items as new (it does not see the script's page-watch-seen.json) and flagged Bandai Namco's ONE PIECE Grand Gourmet launch (dated 23 Oct, posted twice) and the Xenoverse 2 link data (in this morning's post); no real news missed by the script |
| 2026-10-25 15:26Z | script: nothing official; Konami page needs a look | Watcher (haiku): nothing new; Konami page has no list | agree |
| 2026-10-25T20:08Z | feeds: 14 outlet stories, 0 official; pages: nothing new (Konami JP layout note) | nothing to post: Wo Long 2 combat (AR relay of ChinaJoy/TGS interviews, old), Look Outside, FragPunk Farlands, Arkane Lyon and Xbox COO rumours (AR relays) |
| 2026-10-25T20:15Z | Gaming Watch 23:41 Dubai digest read | Shenmue (already scheduled 21:00Z); Tomb Raider LoA TR30 sneak peek dropped (footage on X only, no allowed copy; the game already posted 06:00Z today); CoD film quote (posted 24 Oct); Arkane Lyon Schreier post ~52 h old, no company statement |
| 2026-10-25T21:08Z | feeds: 7 outlet stories, 1 official (Square Enix manga page, not games) | nothing to post: GTA 6 at El Clásico (VGA4A only, no first report found; morning review candidate if verified), Tomb Raider TR30 footage (X only), BioWare actors' comments, GTA 6 buildings (AR relay) |
| 2026-10-25T22:08Z | feeds: 7 outlet stories, 0 official; no new Gaming Watch digest | nothing to post: Mass Effect leak squadmate (posted), Phantom Blade Zero launch trailer (AR relay, PBZ unlock posted 24 Oct), film and TV items, Weekly 4Gamer roundup |
| 2026-10-25T23:08Z | feeds: 4 outlet stories, 1 official (Square Enix FF Resonance help page) | nothing to post: PBZ launch trailer relays, MW4 guides, CD PROJEKT mod-makers relay (AR) |
| 2026-10-26T00:08Z | feeds: 6 outlet stories, 0 official; HoYoverse HSR feed reset | nothing to post: Phantom Blade Zero launch trailer (posted 22 Oct with Gulf prices; unlock time 24 Oct), film and TV items, 4Gamer BioWare column |
| 2026-10-26T01:08Z | feeds: 1 outlet story, 1 official (eFootball live update notice, routine) ; Pure Xbox 403 | nothing to post |
| 2026-10-26T02:08Z | feeds: 2 outlet stories, 1 official (eFootball site maintenance, routine) | Sonic 3M already building; Elden Ring film budget (posted 24 Oct) |
| 2026-10-26T02:50Z | note | text check gap: a headline line opening on «و» + space + Latin name («و Stellar Blade في 4 نوفمبر») rendered in the wrong order on the runner; rtl_starts passed it. Workaround: open the line on a full Arabic word («مع»). Worth adding to reel.GLUED / rtl_starts. |
