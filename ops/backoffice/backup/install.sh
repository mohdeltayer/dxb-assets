#!/usr/bin/env bash
# install.sh: set up the nightly backup mirror for the user running it.
# Run AS the dxbbackup user (no sudo, no root):
#   sudo -iu dxbbackup ~/dxb-assets/ops/backoffice/backup/install.sh
# It copies the four systemd user units to ~/.config/systemd/user/, reloads the
# user manager, enables both timers and creates ~/mirror/{git,snapshots,state}.
# Safe to run again. Needs `loginctl enable-linger dxbbackup` done once by root.
set -euo pipefail

HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
UNIT_DIR=${DXB_BACKUP_UNIT_DIR:-$HOME/.config/systemd/user}
ROOT=${DXB_BACKUP_ROOT:-$HOME/mirror}
ETC=${DXB_BACKUP_ETC:-/etc/dxb-backup}
UNITS=(dxb-backup.service dxb-backup.timer dxb-backup-check.service dxb-backup-check.timer)

if [[ $(id -u) -eq 0 ]]; then
  echo "install.sh: run this as the dxbbackup user, not root (sudo -iu dxbbackup ...)." >&2
  exit 1
fi
if [[ $(id -un) == runner ]]; then
  echo "install.sh: this must not run as 'runner'. Use the dxbbackup user." >&2
  exit 1
fi

missing=()
for t in git rsync curl flock pgrep systemctl; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
if ((${#missing[@]})); then
  echo "install.sh: missing tools: ${missing[*]}" >&2
  echo "As root: apt-get install -y git rsync curl util-linux procps" >&2
  exit 1
fi

# A shell reached through sudo -iu often has no user-manager session variables.
if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then
  XDG_RUNTIME_DIR=/run/user/$(id -u)
  export XDG_RUNTIME_DIR
fi
if [[ ! -S $XDG_RUNTIME_DIR/bus && -z ${DXB_BACKUP_NO_SYSTEMD:-} ]]; then
  echo "install.sh: no systemd user manager for $(id -un) (no $XDG_RUNTIME_DIR/bus)." >&2
  echo "Root must run once:  loginctl enable-linger $(id -un)   then run install.sh again." >&2
  exit 1
fi
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}

mkdir -p "$UNIT_DIR" "$ROOT/git" "$ROOT/snapshots" "$ROOT/state"
chmod 700 "$ROOT" "$ROOT/state"
chmod +x "$HERE/mirror.sh" "$HERE/install.sh" 2>/dev/null || true
for u in "${UNITS[@]}"; do
  install -m 0644 "$HERE/$u" "$UNIT_DIR/$u"
done
# The heartbeat check counts a missing first success from the install time.
[[ -f $ROOT/state/installed-at ]] || date +%s >"$ROOT/state/installed-at"

if [[ -z ${DXB_BACKUP_NO_SYSTEMD:-} ]]; then
  systemctl --user daemon-reload
  systemctl --user enable --now dxb-backup.timer dxb-backup-check.timer
  systemctl --user list-timers 'dxb-backup*' --no-pager || true
fi

for f in github-token ntfy-topic; do
  if [[ -r $ETC/$f ]]; then
    echo "ok: $ETC/$f is readable by $(id -un)"
  else
    echo "TODO (root): $ETC/$f is missing or not readable by $(id -un); see README.md, one-time root steps"
  fi
done
cat <<EOT

Installed. Folders: $ROOT/{git,snapshots,state}
Next:
  $HERE/mirror.sh status
  systemctl --user start --no-block dxb-backup.service     # first mirror now (hours for dxb-assets)
  tail -f $ROOT/state/backup.log
  $HERE/mirror.sh restore-test                             # after the first run
EOT
