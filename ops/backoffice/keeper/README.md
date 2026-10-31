# The promise keeper (adv-20261030-promise-keeper, addendum_2251)

A script, not an agent. Every 5 minutes `.github/workflows/keeper.yml` (GitHub's runners, not dxb-render-1) reads
`newsroom/commitments.json` from main and places every open promise on the ladder from its slot T:

| Rung | When | What the keeper says |
|---|---|---|
| ahead | before T-90 | nothing |
| T-90 | T-90 to T-45 | sources and the template path are decided now (no alarm) |
| T-45 | T-45 to T-30 | at risk: QC-ready or the fallback is committed |
| T-30 | T-30 to T-15 | at risk: submit now |
| T-15 | T-15 to T | ALARM "At risk": no evidence it is scheduled on every platform |
| slot passed | after T | ALARM "Missed slot", overdue; the row's fallback is recorded (alarm-only) |
| T+5 | scheduled but not confirmed published | ALARM "Publication unconfirmed": reconcile, never move silently |
| exception | any platform failed or uncertain | ALARM "Delivery exception": look the post up before any retry |

A blocked production state never takes a row off the ladder. Held rows are quiet. A row whose slot moved keeps
`original_due_at`, so a moved promise is fulfilled late, never on time.

Output, force-pushed as one commit to the branch `keeper-status`: `keeper/status.txt` (the line and the six lines),
`keeper/status.json` (rows), `keeper/state.json` (alarms already sent: one per row and rung), `keeper/keeper.log`.
ntfy push when the repository secret `NTFY_TOPIC` exists; otherwise the alarms live in the status branch only.

Mode: alarm-only. `KEEPER_MODE=fallback` (set in keeper.yml by a release after the seven shadow tests) only marks the
fallback as decided for ops; the keeper itself never posts.

    python3 ops/backoffice/keeper/keeper.py show                 # the ladder now, from the local file
    python3 ops/backoffice/keeper/keeper.py line                 # the one line, counted locally
    python3 -m unittest discover -s ops/backoffice/keeper        # tests, including addendum H simulated

Server route (addendum_0615, build desk 31 Oct 2026): the 5-minute clock is the server's. `dxb-keeper.timer` (a systemd
user timer of the runner user on dxb-render-1, every 5 minutes at :02, nice 10) runs `server_tick.sh`: it fetches
`newsroom/commitments.json` from main (public, no token; the stable clone's working tree is never touched), runs
`keeper.py tick` into `~/backoffice/keeper`, sends its alarms to the phone from the server (topic file
`/etc/dxb-backup/ntfy-topic`), then `keeper.py compare` reads GitHub's `keeper-status` and alarms when GitHub's keeper is
stale (its schedule delayed or dropped) or when the two disagree on the same commitments for two passes in a row.
GitHub cannot read the server (the server has no push key), so the comparison runs on the server; keeper.yml stays the
status sessions read. Install or stop through `backoffice-install.yml` (`-f service=keeper`, `-f enable=disable`).

    ~/dxb-assets/ops/backoffice/keeper/install.sh [--disable]     # as the runner user
    ops/backoffice/keeper/test.sh                                 # unit tests and one pass in a temp home, pushes off
