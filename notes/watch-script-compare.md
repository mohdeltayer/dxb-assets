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
