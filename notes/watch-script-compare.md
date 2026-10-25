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
| 2026-10-25 13:09Z | script: 3 new (Famitsu: Blue Archive publisher to Nexon, FRONTIER PC sale, Famitsu 40th fest update); needs a look: Konami JP (1 link, drawn by script) | Watcher: running, row added when it returns |
