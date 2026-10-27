#!/usr/bin/env bash
# test.sh: one poll pass against the real feeds in a throw-away HOME, push step off, then the
# digest it would hand over. Touches nothing outside the temp folder (and does not git pull).
#   ops/backoffice/watch/test.sh            # prints the digest, poll time, DB size, failed feeds
#   WATCH_FIRST_WINDOW_H=6 ops/backoffice/watch/test.sh   # count items of the last 6 h as new on the first pass
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
TMP=$(mktemp -d "${TMPDIR:-/tmp}/dxb-watch-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
export WATCH_HOME=$TMP/watch WATCH_PUSH=off WATCH_SELF_UPDATE=off
export WATCH_FIRST_WINDOW_H=${WATCH_FIRST_WINDOW_H:-3}
PY=${WATCH_PYTHON:-python3}
mkdir -p "$WATCH_HOME"
start=$(date +%s)
"$PY" "$HERE/watch.py" digest >"$TMP/run.log" 2>&1; rc=$?
secs=$(( $(date +%s) - start ))
echo "=== exit $rc, whole pass (poll + digest) ${secs}s"
echo "=== digest (first 15 lines)"; head -15 "$WATCH_HOME/out/digest.txt" | cut -c1-240
echo "=== digest.txt lines: $(wc -l <"$WATCH_HOME/out/digest.txt"), digest.json $(wc -c <"$WATCH_HOME/out/digest.json") bytes"
echo "=== poll line"; grep -E 'poll:' "$TMP/run.log"
echo "=== failed feeds"; grep -E '^[0-9:]+Z +failed:' "$TMP/run.log" || echo none
echo "=== DB size: $(du -k "$WATCH_HOME/watch.db" | cut -f1) KB"
"$PY" "$HERE/watch.py" status 2>&1 | sed -n 1,5p
