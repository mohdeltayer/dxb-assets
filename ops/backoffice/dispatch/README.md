# Desk dispatcher for dxb-render-1 (back office)

A script, not an agent: it routes every inbox card to a desk, notices evidence that someone picked
the card up, and sends Mohammad an ntfy alert when a card is late. No Claude tokens are used in the
loop. It runs as the `dxbbackup` user from a user-level systemd timer, every 5 minutes, at nice 10
and idle I/O priority. It reads the inbox as a mirror file; it never touches the inbox, the queue,
the render workflow or the publish flow.

**Status: in the repo only. Nothing is installed, nothing is live.**

## What it does

1. Reads `desk/mirror.json` from the `desk` branch of `mohdeltayer/dxb-queue` (GitHub contents API).
2. Reads the evidence: commits on `main` of `dxb-assets` and `dxb-queue` (last 8 days, up to 5 pages
   of 100) and the 50 latest Actions runs of `dxb-assets`.
3. Decides, for every card, its desk, when it started, when it is due, whether someone picked it up,
   and whether it is late.
4. Sends at most one ntfy message per group per pass: late, new for you, new for ops, stale mirror.
5. Keeps `state.json`, a `heartbeat` and a one-line-per-pass `dispatch.log` in `~/backoffice/dispatch`.

Offline, the same decisions are available as `plan` (queue files and write-backs for the Claude task)
and `sample` (the messages a pass would send now).

## Data flow

```
inbox database
  -> scheduled Claude task, hourly:  dispatch.py mirror <items> <out.json>
     commits desk/mirror.json to the orphan branch `desk` of dxb-queue
     (the branch holds only desk/ files, never queue/**, so the publisher never sees it)
  -> dxb-render-1, every 5 minutes:  dispatch.py tick
     reads desk/mirror.json + commits + runs, alerts by ntfy
  -> the same Claude task, next hour:  dispatch.py evidence + plan
     applies desk/writeback.json to the cards and commits desk/ops-queue.md and desk/build-queue.md
```

The mirror holds only: id, from, to, kind, title (160 characters), status, created_at, updated_at,
answer_at, answer_choice (40), picked_up_at, progress (200), has_outcome (true or false, never the
text), desk, late_at. Never body, memo, notes, links, images, video or options.

## Desks and routing

| Desk | What | Due |
|---|---|---|
| `ops` | news, holds, deletes, posts, T0, breaking, schedule, stories, previews, rumours, series, slots | 30 minutes after the card reached production (`DISPATCH_OPS_MIN`) |
| `build` | templates, profiles, checks, tools, the server, workflows, scripts, pipelines, skills, back office, pilots, kits, skins, inserts, renders, backups, watch, standing instructions | the end of the next build night: the first 00:00 UTC (04:00 Dubai) after the start (`DISPATCH_BUILD_END_UTC`) |
| `mohammad` | waiting on him | no pick-up due; he is told once |

Order of the rules (`infer_desk`):

1. An explicit `desk` on the card wins.
2. Production cards: `open` means waiting on Mohammad. `answered` returns to production, and the
   desk is inferred from the title (default ops).
3. Advisor cards of kind decision or question addressed to Mohammad go to `mohammad`.
4. Everything else is scored from the title: `BUILD_TERMS` and `OPS_TERMS` at the top of
   `dispatch.py` hold weighted word starts. Build wins only on a strictly higher score; a tie or no
   match goes to ops (it alerts sooner, which is the safe mistake). The lists are module-level
   constants; checked by eye against the 143 real cards on 28 Oct.

Doubtful by nature (title words point both ways): the Overwatch x Stellar Blade card that also set a
standing rule goes to ops (the story is today's), "Standing rule: answer the 'why'..." goes to build
(a rule for the director checklist). Put `desk` on the card when it matters.

An FYI that Mohammad answered with "Seen" asks nothing of any desk and is never queued or alerted.

## Pick-up and late

The start is the answer time for an answered production card, and the later of created and answered
for an advisor card. A card is picked up when any of these holds:

* status `done`, or an outcome is set;
* `picked_up_at` is at or after the start (2 minutes of slack);
* `progress` is not empty and `updated_at` is at or after the start (2 minutes of slack);
* a commit in `dxb-assets` or `dxb-queue` at or after the start has the card id in its subject.

Late means: not picked up and past the due time. Only cards whose start is within the last 7 days
(`DISPATCH_LOOKBACK_DAYS`) are alerted; older ones are listed in the queue files as BACKLOG. The first
run with an empty state records every card as seen and sends no "new" messages (late alerts still
apply). Actions runs that name a card id, or whose commit names it, are added to the evidence line
but do not count as pick-up on their own.

## Alerts

| Group | Priority, tag | Line | Limit |
|---|---|---|---|
| late | high, warning | `LATE <desk>: <title, 70> (<id>), due HH:MM Dubai` (the date is added when it is not today) | the same card once an hour |
| new for you | default, inbox | `<kind>: <title> (<id>)` per new open mohammad-desk card | once per card and desk |
| new for ops | low, ops | same, for new ops-desk cards | once per card and desk |
| stale mirror | default, warning | `dispatcher: inbox mirror is N h old` | once an hour, when older than `DISPATCH_STALE_H` (3) |

Build-desk cards get no ntfy; `build-queue.md` carries them. A message shows 12 lines and then
"and N more". A card that comes back to production after Mohammad answers is new for ops once more.
If the mirror cannot be fetched, the pass logs it, still runs the stale check and exits 0.

## One-time root steps (Mohammad)

None new. The dispatcher reads `/etc/dxb-backup/github-token` and `/etc/dxb-backup/ntfy-topic`, the
two files the backup mirror's root steps create (`../backup/README.md`). The token needs Contents
read on `dxb-queue` (the `desk` branch) and `dxb-assets`; it already has both. The ntfy topic is the
backup's. `install.sh` says which of the two files the user cannot read yet.

The `desk` branch is created by the Claude task on its first export (an orphan branch with
`desk/mirror.json` only).

## Install (as dxbbackup, through root's sudo)

If the backup bootstrap has run, `~dxbbackup/dxb-assets` exists already:

```
sudo -iu dxbbackup bash -c 'cd ~/dxb-assets && git pull --ff-only && ops/backoffice/dispatch/install.sh'
```

From nothing (same shape as the backup's bootstrap, sparse checkout including ops/backoffice):

```
sudo -iu dxbbackup bash -c 'git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git ~/dxb-assets && cd ~/dxb-assets && git sparse-checkout set ops/backoffice && ops/backoffice/dispatch/install.sh'
```

`install.sh` refuses root and `runner`, checks python3 and systemctl, copies the two units to
`~/.config/systemd/user/`, reloads the user manager, enables `dxb-dispatch.timer` and creates
`~/backoffice/dispatch`. It stops with a clear message if linger is off. Safe to run again. The
nightly backup run keeps `~/dxb-assets` current with `git pull`, so script changes arrive by
themselves; changed unit files need `install.sh` once more.

## Day to day

```
sudo -iu dxbbackup
~/dxb-assets/ops/backoffice/dispatch/dispatch.py status        # last tick, mirror age, cards per desk and state
tail -f ~/backoffice/dispatch/dispatch.log
systemctl --user start dxb-dispatch.service                     # one pass now
~/dxb-assets/ops/backoffice/dispatch/dispatch.py sample --mirror ~/backoffice/dispatch/mirror.json \
  --evidence ~/backoffice/dispatch/evidence.json                # what a pass would send, treating all cards as new
~/dxb-assets/ops/backoffice/dispatch/test.sh                    # the tests, in a throw-away home
```

| Command | What |
|---|---|
| `dispatch.py mirror <items_dir> <out.json>` | sanitized mirror of exported cards |
| `dispatch.py evidence --git DIR [--git DIR] [--ref REF] [--since-days 8]` | commits as JSON (`origin/main` by default; `git log --format` only, never `--stat`, so a partial clone downloads no blobs) |
| `dispatch.py plan --mirror M --evidence E [--now ISO] --out DIR` | `ops-queue.md`, `build-queue.md`, `writeback.json` |
| `dispatch.py tick` | the server pass |
| `dispatch.py sample --mirror M [--evidence E] [--now ISO]` | print the ntfy messages, send nothing |
| `dispatch.py status` | last tick, mirror age, counts, last alerts, whether the token and topic files are readable (never their content) |

Write-backs (`writeback.json`, a list of `{id, fields}`) only ever propose what is missing: `desk`
(not for a production card that is still open, whose desk changes when he answers), `picked_up_at`
(the evidence time), `progress` ("evidence: repo sha subject", from a commit), `late_at` (the due
time). Done cards are left alone.

Optional non-secret overrides go in `~/backoffice/dispatch/dispatch.env` (read by the service):
`DISPATCH_OPS_MIN`, `DISPATCH_BUILD_END_UTC`, `DISPATCH_STALE_H`, `DISPATCH_LOOKBACK_DAYS`,
`DISPATCH_REPO`, `DISPATCH_BRANCH`, `DISPATCH_PATH`. For tests: `DISPATCH_HOME`,
`DISPATCH_MIRROR_FILE`, `DISPATCH_EVIDENCE_FILE`, `DISPATCH_NOW`, `DISPATCH_NTFY=off` (print instead
of send), `DISPATCH_NTFY_URL`, `DISPATCH_API`, `DISPATCH_TOKEN_FILE`, `DISPATCH_TOPIC_FILE`.

## Limits

* Card fields (`picked_up_at`, `progress`, `late_at`, `desk`) reach the cards at the export cadence
  (hourly), not every 5 minutes. A desk that works inside the hour is seen through its commits at once,
  through its card fields at the next export.
* A commit counts as pick-up only if its subject contains the card id. Desks have to put the id in
  commit subjects (`... (prod-20261028-indie-world-reminder-preview)`); a commit about the same work
  without the id does not help.
* The server sees a new card only after the next export, so "new for you" can lag by up to an hour.
* If a commits call fails, the last good copy of that repo's commits is used and the failure is
  logged; a first-ever failure leaves cards without commit evidence for that pass.
* GitHub's API answers up to 5,000 requests an hour for the token. A pass makes about 5 to 8 calls
  (the mirror, up to 5 pages of commits on two repos, the runs), so 12 passes an hour stay far inside
  it. Anonymous reads (60 an hour) are only a fallback for the public `dxb-assets`, tried when the
  token is missing or refused; the private branch needs the token.
* Lateness is mechanical. A card answered in chat and never written back to the inbox still shows as
  late until its fields are filled.

## Safety

* Python 3 standard library only; no network except `api.github.com` and `ntfy.sh`.
* The token is read from its file and sent in an Authorization header; the ntfy topic is read from
  its file and used in the URL. Neither is printed or logged: error text is scrubbed of token shapes
  (`ghp_`, `github_pat_`, `Bearer ...`) and of the exact secret values before it reaches the log, and
  the log of a send carries only the title and the line count.
* `NoNewPrivileges=yes`; a lock file keeps passes from overlapping; every state file is written
  atomically and `~/backoffice/dispatch` is mode 700.
* `test.sh` checks desk inference, the 30-minute and build-night limits, pick-up by commit subject,
  by `picked_up_at` and by progress, done cards, the hourly de-duplication, the baseline run, new-card
  messages, the stale-mirror alert, the 12-line cap, the real send path against a local stand-in, and
  that no secret string reaches the log, state or status.
