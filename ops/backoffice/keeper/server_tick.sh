#!/usr/bin/env bash
# server_tick.sh: one pass of the promise keeper on dxb-render-1, from its systemd user timer (dxb-keeper.timer, every
# 5 minutes; adv-20261030-promise-keeper addendum_0615: the server's timer is the clock, GitHub's keeper.yml the
# secondary). No Claude, no token: the repository is public, so the commitments and GitHub's own keeper status are
# read with plain fetches into the stable clone's remote refs (its working tree is never touched).
#   1. newsroom/commitments.json from origin/main (on a failed fetch the last copy is used, and its age is logged)
#   2. keeper.py tick: the ladder, the status files, one ntfy alarm per row and rung (topic file on the server)
#   3. keeper.py compare: the server's status against keeper-status on GitHub; disagreement or a stale GitHub keeper
#      alarms (a disagreement only when it holds on two passes)
#   4. (build 10 Nov 2026, adv-20261109-coordination-in-code) every 10 minutes and at :25 to :29: a repository_dispatch
#      `keeper-server` to dxb-assets carrying server-summary.json (its Publer read: times, networks, states, labels; no
#      ids, no links), so keeper.yml runs on this clock and writes the work order and the hop alarms. GitHub's own
#      */5 schedule ran keeper.yml only every 4 to 8 hours on 8 and 9 Nov. The token is the watch's (Contents write on
#      dxb-assets only), read by curl from a header file on stdin; KEEPER_DISPATCH=off turns this step off.
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
# Coverage and bank alarms push from GitHub's keeper.yml only (one push per gap); the server keeps them in its status.
export KEEPER_COVER_ALARMS=${KEEPER_COVER_ALARMS:-off}
# Publer as a second evidence source (adv-20261107-keeper-blind-and-lost-submit): the posts-scope key file, if readable.
export KEEPER_PUBLER_KEY_FILE=${KEEPER_PUBLER_KEY_FILE:-/etc/dxb-keeper/publer.key}
export KEEPER_CODE_REV=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown)
DISPATCH_TOKEN_FILE=${KEEPER_DISPATCH_TOKEN_FILE:-/etc/dxb-watch/github-token}
now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/main:refs/remotes/origin/main 2>/dev/null &&
   git -C "$REPO" show origin/main:newsroom/commitments.json > "$KHOME/commitments.json.new" 2>/dev/null; then
  mv "$KHOME/commitments.json.new" "$KHOME/commitments.json"
else
  rm -f "$KHOME/commitments.json.new"
  echo "$now fetch of main failed; using the last commitments copy" >> "$KHOME/keeper.log"
fi

# The watch's branch head for the coverage alarm (adv-20261108-stories-tab addendum_0545); a remote ref, the tree untouched.
DIGEST_ARG=()
if timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/watch-digest:refs/remotes/origin/watch-digest 2>/dev/null &&
   git -C "$REPO" show refs/remotes/origin/watch-digest:watch/digest.json > "$KHOME/watch-digest.json" 2>/dev/null; then
  DIGEST_ARG=(--digest "$KHOME/watch-digest.json")
fi

"$PY" "$HERE/keeper.py" tick --commitments "$KHOME/commitments.json" --out "$KHOME" "${DIGEST_ARG[@]}"
rc=$?

if timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/keeper-status:refs/remotes/origin/keeper-status 2>/dev/null &&
   git -C "$REPO" show origin/keeper-status:keeper/status.json > "$KHOME/github-status.json" 2>/dev/null; then :; else
  rm -f "$KHOME/github-status.json"
fi
"$PY" "$HERE/keeper.py" compare --mine "$KHOME/status.json" --theirs "$KHOME/github-status.json" \
  --state "$KHOME/compare-state.json" --out "$KHOME/compare.txt" || true

# 4. Wake keeper.yml on this clock (every 10 minutes, and at :25 to :29 for the :30 work order).
min=$((10#$(date -u +%M)))
if [ "${KEEPER_DISPATCH:-on}" != off ] && [ -s "$KHOME/server-summary.json" ] && { [ $((min % 10)) -lt 5 ] || { [ "$min" -ge 25 ] && [ "$min" -lt 30 ]; }; }; then
  if [ -r "$DISPATCH_TOKEN_FILE" ]; then
    "$PY" - "$KHOME/server-summary.json" > "$KHOME/dispatch-body.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps({'event_type': 'keeper-server', 'client_payload': {k: s.get(k) for k in
      ('generated_at', 'publer_read_at', 'publer', 'posts', 'code')}}))
PYEOF
    code=$(printf 'Authorization: Bearer %s\n' "$(tr -d '[:space:]' < "$DISPATCH_TOKEN_FILE")" |
      curl -sS -m 20 -o /dev/null -w '%{http_code}' -H @- -H 'Accept: application/vnd.github+json' \
        -X POST --data-binary @"$KHOME/dispatch-body.json" \
        https://api.github.com/repos/mohdeltayer/dxb-assets/dispatches 2>/dev/null || echo 000)
    echo "$now dispatch keeper-server: HTTP $code" >> "$KHOME/keeper.log"
  else
    echo "$now dispatch keeper-server: token file not readable; GitHub's keeper keeps its own schedule" >> "$KHOME/keeper.log"
  fi
fi
exit $rc
