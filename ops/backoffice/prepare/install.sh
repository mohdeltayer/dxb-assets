#!/usr/bin/env bash
# install.sh: set up the prepared-trailers service for the user running it (the runner user). No sudo, no root.
#   ~/dxb-assets/ops/backoffice/prepare/install.sh            # install; the timer stays OFF
#   ~/dxb-assets/ops/backoffice/prepare/install.sh --enable   # install and start the 10-minute timer (Mohammad's go)
#   ~/dxb-assets/ops/backoffice/prepare/install.sh --disable  # stop and disable the timer; files and assets stay
# It makes ~/backoffice/prepare/{state,beats}, a venv with requirements.txt, fetches the two OpenCV Zoo models
# (official mirrors, sha256-checked) into the model cache, makes sure the clone has templates/ (decodecheck.py is
# shared with the render path), copies the two user units with the repo path filled in and reloads the user manager.
# Safe to run again. Needs `loginctl enable-linger <user>` (done for runner on 27 Oct) for the timer to run.
set -euo pipefail

HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
REPO=$(cd "$HERE/../../.." && pwd)
PHOME=${PREPARE_HOME:-$HOME/backoffice/prepare}
UNIT_DIR=${PREPARE_UNIT_DIR:-$HOME/.config/systemd/user}
UNITS=(dxb-prepare.service dxb-prepare.timer)
MODE=install
case "${1:-}" in
  --enable) MODE=enable ;;
  --disable) MODE=disable ;;
  '') ;;
  *) echo "usage: install.sh [--enable | --disable]" >&2; exit 2 ;;
esac

if [[ $(id -u) -eq 0 ]] && ! [[ -n ${PREPARE_NO_SYSTEMD:-} && ${PREPARE_INSTALL_TEST:-} == 1 ]]; then
  # (the container test runs as root with PREPARE_NO_SYSTEMD=1 PREPARE_INSTALL_TEST=1 and a temp PREPARE_HOME)
  echo "install.sh: run this as the runner user, not root." >&2; exit 1
fi

user_manager() {
  [[ -n ${PREPARE_NO_SYSTEMD:-} ]] && return 1
  if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then XDG_RUNTIME_DIR=/run/user/$(id -u); export XDG_RUNTIME_DIR; fi
  if [[ ! -S $XDG_RUNTIME_DIR/bus ]]; then
    echo "install.sh: no systemd user manager for $(id -un) (no $XDG_RUNTIME_DIR/bus)." >&2
    echo "Root must run once:  loginctl enable-linger $(id -un)   then run install.sh again." >&2
    exit 1
  fi
  export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
}

if [[ $MODE == disable ]]; then
  user_manager && { systemctl --user disable --now dxb-prepare.timer || true; systemctl --user list-timers 'dxb-*' --no-pager || true; }
  echo "dxb-prepare.timer disabled. Prepared assets and the ledger stay in place."
  exit 0
fi

missing=()
for t in python3 ffmpeg ffprobe pgrep curl; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
[[ -n ${PREPARE_NO_SYSTEMD:-} ]] || command -v systemctl >/dev/null 2>&1 || missing+=(systemctl)
if ((${#missing[@]})); then
  echo "install.sh: missing tools: ${missing[*]}" >&2
  echo "As root: apt-get install -y python3 python3-venv ffmpeg procps curl" >&2; exit 1
fi
python3 -c 'import venv, ensurepip' 2>/dev/null || { echo "install.sh: python3-venv is missing. As root: apt-get install -y python3-venv" >&2; exit 1; }
command -v tesseract >/dev/null 2>&1 || echo "note: tesseract is missing, burnt-in text will be skipped (as root: apt-get install -y tesseract-ocr)"

# decodecheck.py (and tracksplit.py) come from templates/ of this clone.
if [[ ! -f $REPO/templates/decodecheck.py ]]; then
  if [[ -d $REPO/.git ]] && git -C "$REPO" sparse-checkout list >/dev/null 2>&1; then
    git -C "$REPO" sparse-checkout add templates
  fi
fi
[[ -f $REPO/templates/decodecheck.py ]] || { echo "install.sh: $REPO/templates/decodecheck.py is missing (git -C $REPO sparse-checkout add templates)" >&2; exit 1; }

mkdir -p "$PHOME/state" "$PHOME/beats" "$UNIT_DIR"
chmod 700 "$PHOME"
if [[ ! -x $PHOME/venv/bin/python ]]; then
  python3 -m venv "$PHOME/venv"
fi
"$PHOME/venv/bin/pip" install -q --disable-pip-version-check -r "$HERE/requirements.txt"
chmod +x "$HERE/prepare.py" "$HERE/install.sh" "$HERE/test.sh" 2>/dev/null || true
"$PHOME/venv/bin/python" -c 'import ast, sys; [ast.parse(open(f, encoding="utf-8").read(), f) for f in sys.argv[1:]]' "$HERE"/*.py
PREPARE_HOME=$PHOME "$PHOME/venv/bin/python" "$HERE/prepare.py" models

# Units name %h/dxb-assets; fill in the real path when the clone lives elsewhere.
for u in "${UNITS[@]}"; do
  sed "s|%h/dxb-assets/ops/backoffice/prepare|$HERE|g; s|%h/backoffice/prepare|$PHOME|g" "$HERE/$u" >"$UNIT_DIR/$u"
  chmod 0644 "$UNIT_DIR/$u"
done

if user_manager; then
  systemctl --user daemon-reload
  if [[ $MODE == enable ]]; then
    systemctl --user enable --now dxb-prepare.timer
    echo "dxb-prepare.timer ENABLED (every 10 minutes, nice 10)."
  else
    echo "Installed with the timer OFF (no --enable). Start it after Mohammad's go: install.sh --enable"
  fi
  systemctl --user list-timers 'dxb-*' --no-pager || true
fi

PREPARE_HOME=$PHOME "$PHOME/venv/bin/python" "$HERE/prepare.py" status || true
cat <<EOT

Data: $PHOME (prepare.db, timings.jsonl, beats/), assets in the store printed above.
Next:
  $PHOME/venv/bin/python $HERE/prepare.py from-watch --dry-run     # what the watch would hand over now
  $PHOME/venv/bin/python $HERE/prepare.py one <steam appid> --name <name>   # one by hand
  journalctl --user -u dxb-prepare -n 50
EOT
