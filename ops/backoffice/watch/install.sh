#!/usr/bin/env bash
# install.sh: set up the mechanical watch for the user running it (the runner user).
# Run AS that user, no sudo, no root:
#   ~/dxb-assets/ops/backoffice/watch/install.sh
# It makes ~/backoffice/watch/{state,out}, a Python venv with PyYAML, makes sure the clone has
# newsroom/ (the source lists are imported from there), copies four systemd user units to
# ~/.config/systemd/user/ with the repo path filled in, reloads the user manager and enables
# both timers. Safe to run again. Nothing is read from the network except pip's PyYAML and git.
# Needs `loginctl enable-linger <user>` done once by root (Mohammad has this in hand).
set -euo pipefail

HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
REPO=$(cd "$HERE/../../.." && pwd)
WHOME=${WATCH_HOME:-$HOME/backoffice/watch}
UNIT_DIR=${WATCH_UNIT_DIR:-$HOME/.config/systemd/user}
TOKEN=${WATCH_TOKEN_FILE:-/etc/dxb-watch/github-token}
UNITS=(dxb-watch-poll.service dxb-watch-poll.timer dxb-watch-digest.service dxb-watch-digest.timer)
# --fast-only (promise keeper addendum F, 31 Oct 2026): only the 5-minute poll of the selected official sources, with
# WATCH_PUSH=off in its unit (detection times on the server's clock; GitHub's jobs publish). The full timers above stay
# off; --fast-disable stops it again.
FAST=""
case "${1:-}" in
  '') ;;
  --fast-only) FAST=on; UNITS=(dxb-watch-fast.service dxb-watch-fast.timer) ;;
  --fast-disable) FAST=off; UNITS=(dxb-watch-fast.service dxb-watch-fast.timer) ;;
  *) echo "usage: install.sh [--fast-only | --fast-disable]" >&2; exit 2 ;;
esac

if [[ $(id -u) -eq 0 ]]; then
  echo "install.sh: run this as the runner user, not root." >&2; exit 1
fi
missing=()
for t in git python3 pgrep systemctl; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
if ((${#missing[@]})); then
  echo "install.sh: missing tools: ${missing[*]}" >&2
  echo "As root: apt-get install -y git python3 python3-venv procps" >&2; exit 1
fi
python3 -c 'import venv, ensurepip' 2>/dev/null || { echo "install.sh: python3-venv is missing. As root: apt-get install -y python3-venv" >&2; exit 1; }

# The scripts import newsroom/watch_feeds.py and newsroom/watch_pages.py from this clone.
if [[ ! -f $REPO/newsroom/watch_feeds.py ]]; then
  if [[ -d $REPO/.git ]] && git -C "$REPO" sparse-checkout list >/dev/null 2>&1; then
    git -C "$REPO" sparse-checkout add newsroom
  fi
fi
[[ -f $REPO/newsroom/watch_feeds.py ]] || { echo "install.sh: $REPO/newsroom/watch_feeds.py is missing (git -C $REPO sparse-checkout add newsroom)" >&2; exit 1; }

mkdir -p "$WHOME/state" "$WHOME/out" "$UNIT_DIR"
chmod 700 "$WHOME"
if [[ ! -x $WHOME/venv/bin/python ]]; then
  python3 -m venv "$WHOME/venv"
fi
"$WHOME/venv/bin/pip" install -q --disable-pip-version-check -r "$HERE/requirements.txt"
chmod +x "$HERE/watch.py" "$HERE/install.sh" "$HERE/test.sh" 2>/dev/null || true
"$WHOME/venv/bin/python" -c 'import ast, sys; [ast.parse(open(f, encoding="utf-8").read(), f) for f in sys.argv[1:]]' "$HERE"/*.py

# Units name %h/dxb-assets; fill in the real path when the clone lives elsewhere.
for u in "${UNITS[@]}"; do
  sed "s|%h/dxb-assets/ops/backoffice/watch|$HERE|g; s|%h/backoffice/watch|$WHOME|g" "$HERE/$u" >"$UNIT_DIR/$u"
  chmod 0644 "$UNIT_DIR/$u"
done

# systemd user manager: a shell reached through sudo -iu often lacks the session variables.
if [[ -z ${WATCH_NO_SYSTEMD:-} ]]; then
  if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then XDG_RUNTIME_DIR=/run/user/$(id -u); export XDG_RUNTIME_DIR; fi
  if [[ ! -S $XDG_RUNTIME_DIR/bus ]]; then
    echo "install.sh: no systemd user manager for $(id -un) (no $XDG_RUNTIME_DIR/bus)." >&2
    echo "Root must run once:  loginctl enable-linger $(id -un)   then run install.sh again." >&2; exit 1
  fi
  export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
  systemctl --user daemon-reload
  if [[ $FAST == on ]]; then
    systemctl --user enable --now dxb-watch-fast.timer
    systemctl --user start dxb-watch-fast.service || true      # the first pass now
  elif [[ $FAST == off ]]; then
    systemctl --user disable --now dxb-watch-fast.timer || true
  else
    systemctl --user enable --now dxb-watch-poll.timer dxb-watch-digest.timer
  fi
  systemctl --user list-timers 'dxb-watch*' --no-pager || true
fi

if [[ -r $TOKEN ]]; then
  echo "ok: $TOKEN is readable by $(id -un)"
else
  echo "TODO (root): $TOKEN is missing or not readable by $(id -un); see README.md, the one root step."
  echo "Until then polling works and digests are written to $WHOME/out, but nothing is handed over and nothing is marked handed over."
fi
cat <<EOT

Installed. Data: $WHOME  (watch.db, out/, state/, handoff/)
Next:
  $WHOME/venv/bin/python $HERE/watch.py sources        # what is read, how often, which are breaking
  $WHOME/venv/bin/python $HERE/watch.py status
  systemctl --user start dxb-watch-poll.service        # the first pass now (baseline: nothing is handed over)
EOT
