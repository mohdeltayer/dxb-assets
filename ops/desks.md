# Desks (adv-20261104-desk-manifest)

Every desk, the scheduled tasks it must have, its housekeeping, preflight, alarms and the files it reads each run.
`desks.json` holds the same content for scripts; edit both together. A change to a desk's duties is made here first, by an approved card. A desk that moves accounts is not done until the desk audit passes for it.

## Preflight standard (every task on both accounts and every server job)

disk (under 5 GB: clean first; under 2 GB: alarm on the board and stop); repo at origin/main; board readable; then the started line.
Requests for Mohammad go to the board's questions list, never only in a run summary.

## Daily desk audit

`python3 ops/desk_audit.py --board <dxb-queue>/desk/board.json --runs newsroom/helper-runs.jsonl` compares this
manifest with the board's started lines and the watch log. The morning digest puts its lines at the top of the
card and adds a board question for each MISSING line; the keeper runs it on the server once it carries it
(build night 5 to 6 Nov, with the 01:20 and 04:15 alarms).

## Production 2 newsroom (Production 2)

Duties: posting lane (build, schedule, publish); hourly watch; review preps 06:30, 10:00, 14:00, 17:30 Dubai.
- Task: hourly watch, hourly at :07 Dubai, fresh, automatic approval, evidence: newsroom/helper-runs.jsonl line within 90 minutes
- Task: review prep 06:30, 05:55 Dubai, fresh, automatic approval, evidence: shortlist card or board line by 06:30
- Task: review prep 10:00, 09:25 Dubai, fresh, automatic approval, evidence: shortlist card or board line by 10:00
- Task: review prep 14:00, 13:25 Dubai, fresh, automatic approval, evidence: shortlist card or board line by 14:00
- Task: review prep 17:30, 16:55 Dubai, fresh, automatic approval, evidence: shortlist card or board line by 17:30
- Task: posting session :30 (even-hour slots), hourly, fresh, evidence: board handoff or helper-runs line each run; DEAD in the desk audit after 2 silent runs
- Task: posting session :35 (odd-hour slots), hourly, fresh, evidence: board handoff or helper-runs line each run; DEAD in the desk audit after 2 silent runs
- Slot rule (adv-20261107-keeper-blind-and-lost-submit, 7 Nov 2026): the :30 session owns even-hour slots, the :35 session odd-hour slots; a claimed slot not delivered is released by a board line within 20 minutes; the keeper alarms on a claimed slot with no post 20 minutes before it.
- Submit evidence: a submit is done when get_publer_job_status reads complete and `presubmit.py result ... --job-status complete` is recorded; the board line quotes it. Publer's list lags; the keeper calls a post missing only when two reads 10 minutes apart agree. No Publer ids in public files.
- Coverage: every run's first line is the keeper's coverage line; past 60 minutes by day or 120 by night without a published post, the run ends with a scheduled submit or a banked piece; an empty run writes FAILED RUN on the board with the leads it rejected.
- Bank floor: 6 ready Reels in newsroom/evergreen.md; under it is a keeper alarm, and the idle card's bank step is mandatory in any run that builds nothing.
- Housekeeping: disk cleanup: MISSING (never carried over when posting moved to Production 2 (its disk filled overnight 3 to 4 Nov); Production 2 to add a daily task running newsroom/disk_cleanup.sh, or a preflight clean in every fresh task)
- Preflight: disk (under 5 GB: clean first; under 2 GB: alarm on the board and stop); repo at origin/main; board readable; then the started line; Publer answers (list_publer_posts)
- Alarm: keeper: 90 minutes without a Production 2 watch run (planned, build night 5 to 6 Nov)
- Alarm: gap alarm: formats.py gaps 2 in every watch
- Reads each run: dxb-queue desk/board.md, CLAUDE.md, STYLE.md, newsroom/delegation.md, newsroom/editorial-memory.md (story type), newsroom/commitments.json
- GAP: task names, schedules and approval mode not visible from Production 1; Production 2 to confirm its rows here

## Production 1 studio (Production 1)

Duties: templates, themes, series specs on a branch, on Mohammad's request; live builds only on his direct order.
- Housekeeping: disk cleanup: retired 3 Nov (Mohammad) (sessions are fresh or slim clones; the morning digest and build preflight clean when under 5 GB)
- Preflight: disk (under 5 GB: clean first; under 2 GB: alarm on the board and stop); repo at origin/main; board readable; then the started line
- Reads each run: dxb-queue desk/board.md, CLAUDE.md, STYLE.md

## Build desk (Production 1)

Duties: nightly build 01:07 to 03:45 Dubai, release 04:00; BUILD.md gate.
- Task: Build desk nightly (fresh), 01:07 Dubai daily, fresh, automatic approval, started line build-{date}-started by 01:20 Dubai, status: FAILING: fired 3, 4 and 5 Nov, ended after 39 to 67 s with no started line
- Task: Build desk nightly (01:07 Dubai), 01:07 Dubai daily, bound, automatic approval, started line build-{date}-started by 01:20 Dubai, status: fallback; did the work on 5 Nov; stays on until the fresh task writes its own line
- Housekeeping: disk: preflight clean under 5 GB
- Preflight: disk (under 5 GB: clean first; under 2 GB: alarm on the board and stop); repo at origin/main; board readable; then the started line; dxb-render-1 reachable (last self-hosted run); no render running
- Alarm: keeper: 01:20 Dubai no started line (planned, 5 to 6 Nov)
- Alarm: keeper: 04:15 Dubai no release note (planned)
- Reads each run: BUILD.md, dxb-queue desk/board.md, desk/build-queue.md, ops/build/backlog.md, ops/build/releases/ (newest)

## Morning digest (Production 1)

Duties: Inbox card prod-YYYYMMDD-morning-digest by 07:30 Dubai; desk audit line at its top (from ops/desk_audit.py).
- Task: Morning digest (fresh), 07:12 Dubai daily, fresh, automatic approval, started line digest-{date}-started by 07:20 Dubai, status: FAILING: 4 Nov ran 39 s with no started line; the bound task posted the card
- Task: Morning digest for Mohammad (07:30 Dubai), 07:12 Dubai daily, bound, automatic approval, started line digest-{date}-started by 07:30 Dubai, status: fallback
- Preflight: disk (under 5 GB: clean first; under 2 GB: alarm on the board and stop); repo at origin/main; board readable; then the started line; Publer answers; Inbox reads
- Alarm: none yet: the desk audit reports a missing card at 07:45
- Reads each run: dxb-queue desk/board.md, CLAUDE.md, STYLE.md, ops/desks.json

## Inbox mirror (Production 1)

- Task: Inbox mirror for the desk dispatcher, hourly at :48, bound, automatic approval, evidence: commit 'Inbox mirror' on dxb-queue desk within 2 hours
- Preflight: dxb-assets at origin/main; desk branch clones
- Reads each run: ops/backoffice/dispatch

## Advisor daily status (Production 1 (Claude Desktop, Mohammad's Mac))

- Task: Daily project status (07:45 Dubai), 07:45 Dubai, one-shot re-armed daily, bound (desktop)
- Reads each run: Inbox items updated in 24 h, board questions

## Server keeper (dxb-render-1 (runner user) and GitHub)

- Task: dxb-keeper.timer, every 5 minutes, systemd
- Task: keeper.yml, GitHub schedule, workflow
- Preflight: server-check.yml
- Alarm: slot with no evidence 60 minutes ahead (alarm-only)
- Evidence (7 Nov 2026): on the server, Publer's own scheduled and published posts (posts-scope key file /etc/dxb-keeper/publer.key) matched by network and slot time; a post production did not log is a yellow evidence-gap alarm; missing only after two reads 10 minutes apart. Ids stay in the server's private state.
- Alarm: claimed slot with no post 20 minutes before it; coverage gap (60 min by day, 120 by night; pushed by keeper.yml); bank under 6 ready Reels (keeper.yml, once a day)

## Server watch (dxb-render-1)

- Task: watch-digest.yml, hourly at :52 (GitHub holds it back; sessions dispatch it when over 50 minutes old), workflow (self-hosted)
- Task: dxb-watch-poll / dxb-watch-digest services, systemd, systemd
- Source order: 1 server digest; 2 dispatch watch-digest.yml when over 50 minutes old; 3 when still over 90 minutes: watch_feeds.py and watch_pages.py locally plus the latest Grok digests as a lead list (never a source; Mohammad 4 Nov 17:31)

## Phase 1 prepare (dxb-render-1)

- Task: dxb-prepare.service timer, systemd

## Server backup (dxb-render-1 (dxbbackup user))

- Task: dxb-backup.service and dxb-backup-check.service, systemd
