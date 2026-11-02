#!/usr/bin/env bash
# install.sh: the promise keeper's 5-minute timer on dxb-render-1, for the user running it (the runner user).
#   ~/dxb-assets/ops/backoffice/keeper/install.sh             # install and start the timer (alarm-only)
#   ~/dxb-assets/ops/backoffice/keeper/install.sh --disable   # stop and disable the timer; its files stay
# Copies dxb-keeper.service and .timer to ~/.config/systemd/user/ with the clone's path filled in, reloads the user
# manager, enables the timer and runs one pass at once. stdlib Python only: no venv, no pip. Needs the systemd user
# manager (root ran `loginctl enable-linger runner` on 30 Oct 2026). Safe to run again.
set -euo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
KHOME=${KEEPER_HOME:-$HOME/backoffice/keeper}
UNIT_DIR=${KEEPER_UNIT_DIR:-$HOME/.config/systemd/user}
UNITS=(dxb-keeper.service dxb-keeper.timer)
MODE=enable
case "${1:-}" in
  '') ;;
  --disable) MODE=disable ;;
  *) echo "usage: install.sh [--disable]" >&2; exit 2 ;;
esac
if [[ $(id -u) -eq 0 ]]; then echo "install.sh: run this as the runner user, not root." >&2; exit 1; fi
for t in git python3 systemctl; do command -v "$t" >/dev/null 2>&1 || { echo "install.sh: $t missing" >&2; exit 1; }; done
python3 -c 'import ast, sys; [ast.parse(open(f, encoding="utf-8").read(), f) for f in sys.argv[1:]]' "$HERE"/*.py
mkdir -p "$KHOME" "$UNIT_DIR"
chmod 700 "$KHOME"
chmod +x "$HERE/server_tick.sh" "$HERE/install.sh" "$HERE/test.sh" 2>/dev/null || true
for u in "${UNITS[@]}"; do
  sed "s|%h/dxb-assets/ops/backoffice/keeper|$HERE|g; s|%h/backoffice/keeper|$KHOME|g" "$HERE/$u" > "$UNIT_DIR/$u"
  chmod 0644 "$UNIT_DIR/$u"
done
if [[ -n ${KEEPER_NO_SYSTEMD:-} ]]; then echo "units written to $UNIT_DIR (KEEPER_NO_SYSTEMD: systemd not touched)"; exit 0; fi
if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then XDG_RUNTIME_DIR=/run/user/$(id -u); export XDG_RUNTIME_DIR; fi
if [[ ! -S $XDG_RUNTIME_DIR/bus ]]; then
  echo "install.sh: no systemd user manager for $(id -un) (no $XDG_RUNTIME_DIR/bus). Root: loginctl enable-linger $(id -un)" >&2
  exit 1
fi
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
systemctl --user daemon-reload
if [[ $MODE == disable ]]; then
  systemctl --user disable --now dxb-keeper.timer || true
  echo "dxb-keeper.timer stopped and disabled; $KHOME kept"; exit 0
fi
systemctl --user enable --now dxb-keeper.timer
systemctl --user start dxb-keeper.service || true      # the first pass now, not in five minutes
systemctl --user list-timers 'dxb-keeper*' --no-pager || true
if [[ -r ${KEEPER_TOPIC_FILE:-/etc/dxb-backup/ntfy-topic} ]]; then echo "ntfy topic file: readable"; else
  echo "ntfy topic file: not readable by $(id -un); alarms stay in $KHOME/status.txt and keeper.log"; fi
echo "first line: $(head -1 "$KHOME/status.txt" 2>/dev/null || echo 'no pass yet')"
echo "compare:    $(cat "$KHOME/compare.txt" 2>/dev/null || echo 'no compare yet')"
