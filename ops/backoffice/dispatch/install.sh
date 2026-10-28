#!/usr/bin/env bash
# install.sh: set up the desk dispatcher for the user running it.
# Run AS the dxbbackup user (no sudo, no root):
#   sudo -iu dxbbackup ~/dxb-assets/ops/backoffice/dispatch/install.sh
# It copies the two systemd user units to ~/.config/systemd/user/, reloads the user manager,
# enables the 5-minute timer and creates ~/backoffice/dispatch. It needs no new token and no new
# file: it reads the two root-owned files the backup mirror already uses. Safe to run again.
# Needs `loginctl enable-linger dxbbackup` done once by root (the backup card's root steps).
set -euo pipefail

HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
UNIT_DIR=${DISPATCH_UNIT_DIR:-$HOME/.config/systemd/user}
DHOME=${DISPATCH_HOME:-$HOME/backoffice/dispatch}
ETC=${DXB_BACKUP_ETC:-/etc/dxb-backup}
UNITS=(dxb-dispatch.service dxb-dispatch.timer)

if [[ $(id -u) -eq 0 ]]; then
  echo "install.sh: run this as the dxbbackup user, not root (sudo -iu dxbbackup ...)." >&2
  exit 1
fi
if [[ $(id -un) == runner ]]; then
  echo "install.sh: this must not run as 'runner'. Use the dxbbackup user." >&2
  exit 1
fi

missing=()
for t in python3 systemctl; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
if ((${#missing[@]})); then
  echo "install.sh: missing tools: ${missing[*]}" >&2
  echo "As root: apt-get install -y python3 systemd" >&2
  exit 1
fi
python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1])' "$HERE/dispatch.py"

# A shell reached through sudo -iu often has no user-manager session variables.
if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then
  XDG_RUNTIME_DIR=/run/user/$(id -u)
  export XDG_RUNTIME_DIR
fi
if [[ ! -S $XDG_RUNTIME_DIR/bus && -z ${DISPATCH_NO_SYSTEMD:-} ]]; then
  echo "install.sh: no systemd user manager for $(id -un) (no $XDG_RUNTIME_DIR/bus)." >&2
  echo "Root must run once:  loginctl enable-linger $(id -un)   then run install.sh again." >&2
  exit 1
fi
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}

mkdir -p "$UNIT_DIR" "$DHOME"
chmod 700 "$DHOME"
chmod +x "$HERE/dispatch.py" "$HERE/install.sh" "$HERE/test.sh" 2>/dev/null || true
for u in "${UNITS[@]}"; do
  install -m 0644 "$HERE/$u" "$UNIT_DIR/$u"
done

if [[ -z ${DISPATCH_NO_SYSTEMD:-} ]]; then
  systemctl --user daemon-reload
  systemctl --user enable --now dxb-dispatch.timer
  systemctl --user list-timers 'dxb-dispatch*' --no-pager || true
fi

for f in github-token ntfy-topic; do
  if [[ -r $ETC/$f ]]; then
    echo "ok: $ETC/$f is readable by $(id -un)"
  else
    echo "TODO (root): $ETC/$f is missing or not readable by $(id -un); see ../backup/README.md, one-time root steps"
  fi
done
cat <<EOT

Installed. Data: $DHOME  (state.json, heartbeat, dispatch.log, mirror.json, evidence.json)
Next:
  $HERE/dispatch.py status
  systemctl --user start dxb-dispatch.service      # one pass now (the first one only records a baseline)
  tail -f $DHOME/dispatch.log
EOT
