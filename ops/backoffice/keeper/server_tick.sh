#!/usr/bin/env bash
# server_tick.sh: one pass of the promise keeper on dxb-render-1, from its systemd user timer (dxb-keeper.timer, every
# 5 minutes; adv-20261030-promise-keeper addendum_0615: the server's timer is the clock, GitHub's keeper.yml the
# secondary). No Claude, no token: the repository is public, so the commitments and GitHub's own keeper status are
# read with plain fetches into the stable clone's remote refs (its working tree is never touched).
#   1. newsroom/commitments.json from origin/main (on a failed fetch the last copy is used, and its age is logged)
#   2. keeper.py tick: the ladder, the status files, one ntfy alarm per row and rung (topic file on the server)
#   3. keeper.py compare: the server's status against keeper-status on GitHub; disagreement or a stale GitHub keeper
#      alarms (a disagreement only when it holds on two passes)
# Output in ~/backoffice/keeper: status.txt (the line and the six lines), status.json, state.json, keeper.log,
# compare.txt. Nothing is pushed: sessions keep reading keeper-status; the server's own alarms go to the phone.
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
REPO=$(cd "$HERE/../../.." && pwd)
KHOME=${KEEPER_HOME:-$HOME/backoffice/keeper}
PY=${KEEPER_PYTHON:-python3}
mkdir -p "$KHOME"
export KEEPER_MODE=${KEEPER_MODE:-alarm-only}
export KEEPER_TOPIC_FILE=${KEEPER_TOPIC_FILE:-/etc/dxb-backup/ntfy-topic}
now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/main:refs/remotes/origin/main 2>/dev/null &&
   git -C "$REPO" show origin/main:newsroom/commitments.json > "$KHOME/commitments.json.new" 2>/dev/null; then
  mv "$KHOME/commitments.json.new" "$KHOME/commitments.json"
else
  rm -f "$KHOME/commitments.json.new"
  echo "$now fetch of main failed; using the last commitments copy" >> "$KHOME/keeper.log"
fi

"$PY" "$HERE/keeper.py" tick --commitments "$KHOME/commitments.json" --out "$KHOME"
rc=$?

if timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/keeper-status:refs/remotes/origin/keeper-status 2>/dev/null &&
   git -C "$REPO" show origin/keeper-status:keeper/status.json > "$KHOME/github-status.json" 2>/dev/null; then :; else
  rm -f "$KHOME/github-status.json"
fi
"$PY" "$HERE/keeper.py" compare --mine "$KHOME/status.json" --theirs "$KHOME/github-status.json" \
  --state "$KHOME/compare-state.json" --out "$KHOME/compare.txt" || true
exit $rc
