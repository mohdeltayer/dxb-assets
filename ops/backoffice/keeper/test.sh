#!/usr/bin/env bash
# test.sh: the keeper's unit tests, then one server pass in a throw-away home with pushes off (KEEPER_NTFY=off),
# against the clone's commitments and GitHub's keeper-status. Touches nothing outside the temp folder.
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
PY=${KEEPER_PYTHON:-python3}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/dxb-keeper-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
"$PY" -m unittest discover -s "$HERE" 2>&1 | tail -3
KEEPER_HOME=$TMP KEEPER_NTFY=off "$HERE/server_tick.sh"; rc=$?
echo "=== exit $rc"
echo "=== status.txt"; cat "$TMP/status.txt" 2>/dev/null
echo "=== compare.txt"; cat "$TMP/compare.txt" 2>/dev/null
exit $rc
