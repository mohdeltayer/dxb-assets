#!/usr/bin/env bash
# test.sh: the prepare service's own tests. Offline by default: every Python file compiles, then the unit tests run
# on synthetic clips made with ffmpeg testsrc, in a throw-away folder. Touches nothing outside it.
#   ops/backoffice/prepare/test.sh                      # offline (the gate's self-test)
#   ops/backoffice/prepare/test.sh --online [appid]     # also prepares one real Steam trailer into a temp store
# PREPARE_PYTHON picks the interpreter (the installed venv: ~/backoffice/prepare/venv/bin/python).
# PREPARE_MODELS points at the model cache, so the detector test runs when the models are there.
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
PY=${PREPARE_PYTHON:-python3}
[[ -x $HOME/backoffice/prepare/venv/bin/python && -z ${PREPARE_PYTHON:-} ]] && PY=$HOME/backoffice/prepare/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
rc=0

echo "=== compile"
"$PY" -c 'import ast, sys; [ast.parse(open(f, encoding="utf-8").read(), f) for f in sys.argv[1:]]; print("ok", len(sys.argv) - 1, "files")' "$HERE"/*.py || rc=1
echo "=== imports"
(cd "$HERE" && "$PY" -c 'import prepare, acquire, analyse; print("ok")') || rc=1
echo "=== tools"
"$PY" - <<'EOF'
import importlib, shutil
for m in ('numpy', 'cv2', 'scenedetect', 'librosa', 'yaml'):
    try:
        print(f'{m:12} {getattr(importlib.import_module(m), "__version__", "?")}')
    except ImportError:
        print(f'{m:12} MISSING')
for t in ('ffmpeg', 'ffprobe', 'tesseract', 'pgrep'):
    print(f'{t:12} {"ok" if shutil.which(t) else "MISSING"}')
EOF
echo "=== unit tests"
[[ -n ${PREPARE_MODELS:-} ]] || export PREPARE_MODELS=$(cd "$HERE" && "$PY" -c 'import analyse; print(analyse.model_dir())' 2>/dev/null)
echo "models: ${PREPARE_MODELS:-none}"
start=$(date +%s)
ULOG=$(mktemp "${TMPDIR:-/tmp}/dxb-prepare-unit.XXXXXX")
(cd "$HERE" && "$PY" test_prepare.py) >"$ULOG" 2>&1; urc=$?
grep -v -E 'RuntimeWarning|den = |ret = ' "$ULOG"; rm -f "$ULOG"
[[ $urc -eq 0 ]] || rc=1
echo "=== unit tests: exit $urc in $(( $(date +%s) - start ))s"

if [[ ${1:-} == --online ]]; then
  APP=${2:-1091500}
  TMP=$(mktemp -d "${TMPDIR:-/tmp}/dxb-prepare-online.XXXXXX")
  trap 'rm -rf "$TMP"' EXIT
  echo "=== online: Steam app $APP into $TMP"
  PREPARE_HOME=$TMP/home PREPARE_STORE=$TMP/store PREPARE_RENDER_CHECK=off PREPARE_FLOOR_GB=${PREPARE_FLOOR_GB:-1} \
    "$PY" "$HERE/prepare.py" one "$APP" --name online-test 2>&1 | grep -v -E 'RuntimeWarning|den = |ret = ' || rc=1
  for m in "$TMP"/store/*/manifest.json; do
    [[ -f $m ]] || { echo "no manifest"; rc=1; continue; }
    "$PY" - "$m" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))
print('status', m['status'], '| source', m['source']['method'], m['source'].get('steam', {}).get('trailer'))
print('probe', m['probe'])
print('checks', {k: v for k, v in m['checks'].items()})
print('summary', m.get('summary'))
print('timings', m['timings'], 'cpu_s', m['cpu_s'], 'bytes', m['bytes'])
EOF
  done
fi
echo "=== test.sh exit $rc"
exit $rc
