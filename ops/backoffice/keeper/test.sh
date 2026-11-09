#!/usr/bin/env bash
# test.sh: the keeper's unit tests, then one server pass in a throw-away home with pushes off (KEEPER_NTFY=off),
# against the clone's commitments and GitHub's keeper-status. Touches nothing outside the temp folder.
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
PY=${KEEPER_PYTHON:-python3}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/dxb-keeper-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
"$PY" -m unittest discover -s "$HERE" 2>&1 | tail -3
KEEPER_HOME=$TMP KEEPER_NTFY=off KEEPER_DISPATCH=off "$HERE/server_tick.sh"; rc=$?
echo "=== exit $rc"
echo "=== status.txt"; cat "$TMP/status.txt" 2>/dev/null
echo "=== compare.txt"; cat "$TMP/compare.txt" 2>/dev/null
# what the timer would send GitHub (build 10 Nov 2026): the Publer line, the code revision, the post count; no ids
echo "=== server-summary"; "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); print('code', d.get('code'), '|', d.get('publer'), '| publer_read_at', d.get('publer_read_at'), '| posts', None if d.get('posts') is None else len(d['posts']))" "$TMP/server-summary.json" 2>/dev/null || echo "no server-summary.json"
if [ -r "${KEEPER_DISPATCH_TOKEN_FILE:-/etc/dxb-watch/github-token}" ]; then echo "dispatch token file: readable"; else echo "dispatch token file: NOT readable (the timer cannot wake keeper.yml)"; fi
exit $rc
