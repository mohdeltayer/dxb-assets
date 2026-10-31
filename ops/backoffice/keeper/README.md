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

Server route (later): once root has run `loginctl enable-linger runner`, the same `keeper.py tick` can run from a user
timer on dxb-render-1; the push needs a token that can write this repository's `keeper-status` branch.
