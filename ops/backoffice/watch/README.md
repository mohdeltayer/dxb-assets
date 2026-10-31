# Mechanical watch for dxb-render-1 (back office service 1)

A script, not an agent: it reads the official sources and the outlet feeds every few minutes, keeps
what is new in SQLite, and hands the news desk a short digest every hour, and at once for sources
marked `breaking`. No Claude tokens are used anywhere in the loop. It runs as the `runner` user
from user-level systemd timers, at nice 10, and narrows itself while a render is active.

**Status (29 Oct 2026): live through `.github/workflows/watch-digest.yml`.** The server has no key for
dxb-watch or dxb-queue, so an hourly Actions job on the dxb-render runner (cron :52) runs `watch.py digest`
with `WATCH_PUSH=external` (files written to `~/backoffice/watch/out` and marked handed over) and
force-pushes them, without the `summary` text, to `watch/` on the branch `watch-digest` of dxb-assets
(adv-20261029-server-watch-publish-now, Mohammad: "Public branch, titles+links"). The systemd timers below
(5-minute polls, a push of its own) are not installed; with them the breaking lines would arrive within
minutes rather than at :52. Today's hourly watch
(`newsroom/watch_feeds.py`, `watch_pages.py`, the Watcher and the Gaming Watch digest) is untouched
and keeps running; this service has its own SQLite ledger and never writes `watch-seen.json`.

**Five-minute poll of the selected official sources (31 Oct 2026, promise keeper addendum F).**
`.github/workflows/watch-fast.yml` runs `watch.py poll --only-breaking` on the dxb-render runner every 5 minutes (GitHub's
clock, the server's poll), and when something new was handed over it replaces `watch/breaking.json` and `breaking.txt`
on `watch-digest` (the digest files stay). The selected sources are the `breaking: true` ones. It steps aside when a job
is already queued for the runner, holds it for about 30 seconds otherwise, and has its own concurrency group. Each item's
`first_seen` is the detection time `templates/admission.py` measures breaking latency from. The user timers stay the
target once root has run `loginctl enable-linger runner` and the server has a push key.

## What it reads (100 sources, 15 of them breaking; `watch.py sources` lists them)

| Group | Count | Read every | Breaking | Where the list lives |
|---|---|---|---|---|
| Official feeds (PlayStation Blog, Xbox Wire, Nintendo Japan, Take-Two, Atlus, Bungie, Spike Chunsoft, Steam Deck news) | 8 | 5 min (PS Blog and Xbox Wire 3, Steam Deck 15) | PS Blog, Xbox Wire, Nintendo Japan, Take-Two, Bungie | `newsroom/watch_feeds.py` `OFFICIAL` |
| Official pages and APIs read by a parser (Bandai Namco, Manga Productions, HoYoLAB x6, PUBG Mobile, Free Fire, CoD Mobile, Supercell, EA SPORTS FC, eFootball) | 14 | 15 min | no | same file, parser functions |
| Google News backstops (Rockstar, Blizzard, Fortnite, Sega, Square Enix) | 5 | 30 min | no | same file |
| Official pages with no feed (Nintendo US, Capcom IR, Square Enix HD, Bandai Namco, EA, Ubisoft, Riot, The Game Awards, Famitsu) | 9 | 15 min | Nintendo US, The Game Awards | `newsroom/watch_pages.py` `PAGES` |
| Official YouTube channel feeds (`youtube.com/feeds/videos.xml?channel_id=`, a plain RSS read, no downloads) | 20 | 5 min for PlayStation, Xbox, Nintendo of America, Rockstar; else 15 | those four | `sources.yaml` `extra` |
| Official X accounts, through X's public embedded timeline (experimental, see below) | 5 | 15 min | four of them | `sources.yaml` `extra` |
| Outlet feeds (the 31 of `OUTLETS`, plus Steam hub, Denfaminicogamer, Game*Spark, TweakTown, Tbreak, Nintendo Everything, GoNintendo, GamingOnLinux) | 39 | 10 min (GamingOnLinux 15) | never | `OUTLETS` and `sources.yaml` |

The imported lists are read with the code they already hold, so adding a feed to `watch_feeds.py`
reaches the service at its next `git pull` (the hourly digest run pulls first). `sources.yaml` only
sets cadence, the `breaking` flags (`imported.overrides`), sources it alone defines (`extra`), and
sources known not to work (`imported.disabled`, today Konami JP). A source that fails is backed off
(x2 per failure, up to x8) and listed in the digest's `failed:` line after two failures in a row.

`breaking: true` means "a first-party source whose new item the desk wants within minutes", not "this
is breaking news": the Verifier still grades it, and outlets are never breaking.

### What it does not cover (also printed in every digest, `not covered:`)

* Official X accounts other than the five above. X has no public page that works without login except
  the embedded-timeline page (`syndication.twitter.com/srv/timeline-profile/screen-name/<handle>`).
  It is an unofficial endpoint: X can change or block it, it lags the live timeline by minutes, retweets
  are skipped, and it rate-limits hard. In the 27 Oct test five accounts read and parsed fine, then every
  request answered HTTP 429 for 15+ minutes (the test host shares an egress address, so the server may do
  better). The reader is covered by a synthetic-page test only; watch the `failed:` line for a day and,
  if X keeps refusing, switch it off with `kinds: {x_embed: false}`. The Gaming Watch digest stays the
  route for X.
* Konami JP topics (script-drawn list), Konami / EA / Activision YouTube (empty channel feeds), Epic,
  Sony Group press and GitHub releases (403 to scripts), the Saudi Esports Federation, GEA and UAE gaming
  bodies, and store prices (PS Store, Xbox and Steam regional prices are a separate job, scout audit
  section 6).
* It does not verify, judge, rank or write anything. A digest line is a lead with a link; the Watcher,
  Verifier and main session work as before.

## How it works

```
timer 5 min  -> watch.py poll    reads the sources that are due (ETag/gzip, 8 at a time, 8 s gap for X),
                                 stores new items, and if a breaking source has something new, pushes
                                 breaking.json at once (retried next tick if the push fails)
timer :52    -> watch.py digest  git pull of the clone, one more poll, then the hourly digest push
```

* **Dedup**: per source, on the normalised URL (no fragment, tracking parameters or trailing slash) and
  on the title, the same two tests as `watch_feeds.py`. Guides, puzzles and deals on outlet feeds are
  stored as `junk` and never reported. Google News store and cart pages are skipped.
* **First read of a source** records everything as `baseline` (never handed over) except items published
  in the last `first_poll_window_h` (2) hours, so a new source cannot flood the desk. Items first
  published more than 2 days ago are recorded, not reported (as `watch_feeds.py`).
* **Stored per item**: title, link, published time (UTC, minute), `first_seen` (UTC, second), source,
  kind, a 400-character summary of the item's own text, and media links found in the item (feed
  `media:content`, `media:thumbnail`, `enclosure`, `<img>` in the body, YouTube thumbnail, the video's
  watch URL, and for X the images and the best MP4). No file is downloaded.
* **Render pause**: before each pass `pgrep -f 'render_job\.py|Runner\.Worker'`. While a render is
  active the pass reads only the `breaking` sources (about fifteen GETs at nice 10, a few CPU-seconds),
  because a 15-minute render would otherwise hold every first-party item back for the full 15 minutes.
  `WATCH_PAUSE_ALL=1` makes it a full pause (poll exits 75, the digest is built from what is stored).
  This is a decision to confirm; it is one environment variable to flip.
* **Priority**: `Nice=10`, idle IO class, 4-minute (poll) and 8-minute (digest) timeouts, one pass at a
  time (a lock file), no ports, no inbound anything.

## How the main session reads the digest

The main session works in a cloud container with git access to dxb-assets and dxb-queue, so the server
pushes a few small files to a branch and the session reads them with git or the GitHub file tool.

Options weighed:

| Route | Verdict |
|---|---|
| (a) commit to dxb-queue, branch `watch-digest` | Works, and the session already has the repo. Two costs found: `gitleaks.yml` runs on **every push to any branch**, so about 30 to 60 pushes a day would be 30 to 60 Actions runs a day (roughly 1,000 to 1,800 minutes a month of a private repo's 2,000 free) and a false positive on scraped text fails a run and emails Mohammad; and the server would hold a write token on the repo whose `publish.yml` posts to social media (it is path-filtered to `queue/**`, so a push to `watch-digest` does not fire it, but a leaked token could write a `queue/` folder). Fallback, not the default. |
| (a') commit to a **separate private repo `mohdeltayer/dxb-watch`** (recommended, the default in `sources.yaml`) | Same mechanism, no workflows (a push costs no minutes and fires nothing), and a token scoped to that one repo cannot touch the publisher, the queue or the code. The main session adds the repo with `add_repo` (read access is enough). Needs one more repo from Mohammad. |
| (b) the inbox artifact database | Needs a claude.ai credential the server cannot hold. Not possible. |
| (c) the render workflows in dxb-assets | dxb-assets is public (scraped content must not go there) and the render workflow is not a scheduler. Not suitable. |

Never in dxb-assets: it is public.

**To use dxb-queue instead**: set `WATCH_REMOTE=https://github.com/mohdeltayer/dxb-queue.git`,
`WATCH_BRANCH=watch-digest`, `WATCH_EMPTY_PUSH_H=3` in `~/backoffice/watch/watch.env`, and give the token
Contents read and write on dxb-queue. The empty-hour heartbeat then goes out every 3 hours, which keeps
gitleaks to about 24 runs a day (the history is squashed to one commit a week either way).

### The files (branch `main` of dxb-watch, or the chosen branch)

| File | When it changes | Content |
|---|---|---|
| `digest.json`, `digest.txt` | every hour (:52), even with nothing new (the heartbeat) | `official` (items), `outlets` (stories grouped across outlets, with the number of outlets and every outlet's link), `failed`, `not_covered`, `watcher` health. `digest.txt` has the line shapes of `watch_feeds.py`: `OFFICIAL`, `OUTLETS (N stories ...)`, `failed:`, and `AR RELAY` marking |
| `breaking.json`, `breaking.txt` | at once when a breaking source has something new, and with every hourly push | `items`: first handed over in this push (`breaking_seq == seq`); `recent`: handed over in the last 24 hours; `watcher` health |

Every push carries `seq` (it only goes up) and `generated_at`. Each item has `id`, `source`,
`source_kind`, `title`, `url`, `published`, `first_seen`, `summary`, `media` (`[{"type": "image" |
"video" | "audio", "url"}]`), `breaking_source`, and `breaking_seq` or `digest_seq`.

The hourly watch's steps, in order:

1. Read `digest.json` and `breaking.json` (either `git fetch --depth 1 origin main && git show
   origin/main:digest.json`, or `get_file_contents` for the two files).
2. **Is the watcher alive?** If `generated_at` is older than 2 hours, or `watcher.last_poll_at` is
   older than 15 minutes, put "mechanical watch down" in the report and fall back to running
   `watch_feeds.py` and `watch_pages.py` as today.
3. Take the items with `breaking_seq` above the highest `seq` already processed (keep that number in
   the run's commit message or in `newsroom/digests-covered.json`) and hand them to the Verifier at
   once; do the same with `official` and `outlets` of a digest with a `seq` not yet processed.
4. Report `failed` and `not_covered` as the watch report does now.

A missed read loses nothing: breaking items stay in `recent` for 24 hours, and the hourly digest is
rebuilt from the store, not from what the last push held. Items are marked handed over only after the
push succeeded, so a failed push is retried by the next tick.

## The one root step, and what Mohammad does outside the server

Mohammad (not root): create the private repo `mohdeltayer/dxb-watch` (empty, no workflows, nothing in
it), and a fine-grained personal access token named `dxb-watch-push`: owner `mohdeltayer`, repository
`dxb-watch` only, permission Contents read and write (Metadata read comes with it), with an expiry date.
Add it to `ops/key-register.md` in dxb-queue (name, purpose, where it lives, rights, expiry; never the
value). Give the main session read access to the repo (`add_repo`).

Root, once, on dxb-render-1 (linger for `runner` is already agreed; `apt` only if a tool is missing):

```
apt-get install -y git python3 python3-venv procps
loginctl enable-linger runner
install -d -m 0750 -o root -g runner /etc/dxb-watch
install -m 0640 -o root -g runner /dev/null /etc/dxb-watch/github-token
nano /etc/dxb-watch/github-token       # paste the token on one line, save
ls -l /etc/dxb-watch                   # -rw-r----- root runner
```

The token is read by git itself from that file through a credential helper; it appears in no command
line, no environment dump, no log (error text is filtered for token shapes), and it is never in the repo.
Until the file exists the service still polls and writes digests to `~/backoffice/watch/out/`, but
pushes nothing and marks nothing handed over.

## Install (as runner, no sudo)

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git ~/dxb-assets   # if not there yet
cd ~/dxb-assets && git sparse-checkout add ops/backoffice newsroom
~/dxb-assets/ops/backoffice/watch/install.sh
```

`install.sh` makes `~/backoffice/watch/{state,out}`, a venv with PyYAML, copies the four user units to
`~/.config/systemd/user/` (filling in the clone's path), reloads the user manager, enables both timers
and checks the token file. Safe to run again. The first pass (`systemctl --user start
dxb-watch-poll.service`) records the baseline and hands nothing over. If dxb-assets goes private, the
hourly `git pull` needs a read token: point `WATCH_PULL_TOKEN_FILE` at one in `watch.env`.

Day to day: `watch.py status` (store, last handoffs, failing sources, token, render state),
`watch.py sources`, `journalctl --user -u dxb-watch-poll -u dxb-watch-digest -n 50`.

## Cost, measured on 27 Oct 2026 (this container, 100 sources, one full pass from an empty store)

* **CPU**: 6 to 7 CPU-seconds and 50 MB peak memory for a full pass of every source; 9 s wall when X is
  off, about 40 s with the X gaps. The timer reads only due sources: about 550 reads an hour, roughly
  35 CPU-seconds an hour, around 1% of one core, at nice 10. An hourly digest adds under a second.
* **Network**: 10.5 MB decoded for the full first pass (31 of 100 sources answered 304 on a second
  pass); at the scheduled rates about 35 MB an hour decoded, much less on the wire (gzip, ETag), well
  under 1 GB a day.
* **Disk**: the SQLite file was 1.8 MB with 1,550 items. Growth is about 1 to 2 MB a day; items are kept
  60 days and poll rows 7 days, so the file settles around 100 MB at most. The hand-over clone is under
  1 MB (squashed to one commit a week). `~/backoffice/watch` is the only place it writes.
* **GitHub**: on dxb-watch, no Actions; on dxb-queue, one gitleaks run per push (see above).

## Test

`ops/backoffice/watch/test.sh` runs one poll plus the digest against the real feeds in a throw-away
HOME with the push step off (`WATCH_PUSH=off`), prints the first 15 lines of the digest, the poll line,
the DB size and the failed feeds, and deletes everything. It needs PyYAML (`python3 -c 'import
yaml'`, or `WATCH_PYTHON=~/backoffice/watch/venv/bin/python`). The push path was tested separately
against a local bare repository: first push, update, a failed push (items stay pending), a skipped
quiet hour and the weekly squash.

## Environment overrides

`WATCH_HOME`, `WATCH_CONFIG`, `WATCH_NEWSROOM`, `WATCH_PUSH=off`, `WATCH_REMOTE`, `WATCH_BRANCH`,
`WATCH_TOKEN_FILE`, `WATCH_EMPTY_PUSH_H`, `WATCH_FIRST_WINDOW_H`, `WATCH_PAUSE_ALL=1`,
`WATCH_RENDER_CHECK=off`, `WATCH_BUSY_PATTERN`, `WATCH_SELF_UPDATE=off`, `WATCH_PULL_TOKEN_FILE`,
`WATCH_JOBS`. Put the non-secret ones in `~/backoffice/watch/watch.env` (the units read it if present).

## Known limits

* The unit files were checked for syntax by eye and installed by `install.sh` in a test HOME, but not
  loaded by a systemd user manager (the container has none); the first `systemctl --user` run on the
  server is the real test.
* Items without a time (the page-link sources) read as "no time"; the Verifier dates them from the page.
* Day-only dates (several parser pages) read as 00:00 UTC of their day, as in `watch_feeds.py`.
* The Steam hub feed mixes developer posts with press articles, so it is read as an outlet (a lead).
