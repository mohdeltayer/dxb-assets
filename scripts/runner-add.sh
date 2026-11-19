#!/usr/bin/env bash
# Add one more GitHub Actions runner instance on the dxb-render server (Mohammad, 19 Nov 2026: "the server was bought to
# render several Reels at once"). The first instance (dxb-render-1) came from scripts/runner-setup.sh on the
# ops/self-hosted-runner branch, which also installed every tool, the venv and the warm cache; extra instances share
# all of that and only need their own runner folder and service. Run as root, once per instance:
#
#   curl -fsSLo runner-add.sh https://raw.githubusercontent.com/mohdeltayer/dxb-assets/main/scripts/runner-add.sh
#   sudo bash runner-add.sh dxb-render-1b      # second render slot
#   sudo bash runner-add.sh dxb-render-1c      # spare: T0, breaking, reads and checks never wait
#
# Each run asks for a registration token (repository Settings, Actions, Runners, New self-hosted runner: the token
# in the ./config.sh line). It is typed at a hidden prompt, passed to config.sh in that one process's environment, never
# written to a file or log, and expires after an hour. Labels: dxb-render, as the first instance. Running it again for
# a name that is already registered does nothing. `sudo bash runner-add.sh check` lists the instances and their state.
set -Eeuo pipefail
umask 022

REPO_URL="https://github.com/mohdeltayer/dxb-assets"
RUNNER_USER="runner"
RUNNER_HOME="/home/${RUNNER_USER}"
FIRST="${RUNNER_HOME}/actions-runner"
LABELS="dxb-render"

[ "$(id -u)" = 0 ] || { echo "run as root (sudo bash runner-add.sh <name>)"; exit 1; }
[ -x "${FIRST}/config.sh" ] || { echo "no first runner at ${FIRST}; run scripts/runner-setup.sh first"; exit 1; }

if [ "${1:-}" = check ] || [ -z "${1:-}" ]; then
  for d in "${RUNNER_HOME}"/actions-runner*; do
    n=$(sed -n 's/.*"agentName": *"\([^"]*\)".*/\1/p' "$d/.runner" 2>/dev/null | head -1)
    s=$(systemctl list-units --type=service --no-legend 2>/dev/null | awk '/actions.runner/ {print $1, $4}' | grep -F "${n:-none}" || true)
    echo "${d}: ${n:-not registered} ${s:-(no service)}"
  done
  echo "cores $(nproc), memory $(free -g | awk '/Mem:/{print $2}') GB, disk free $(df -h "${RUNNER_HOME}" | awk 'NR==2{print $4}')"
  exit 0
fi

NAME="$1"
printf '%s' "$NAME" | grep -Eq '^dxb-render-[A-Za-z0-9-]+$' || { echo "name must look like dxb-render-1b"; exit 1; }
DIR="${RUNNER_HOME}/actions-runner-${NAME#dxb-render-}"
if [ -f "${DIR}/.runner" ]; then echo "${NAME} is already registered in ${DIR}"; exit 0; fi

tarball=$(ls -t "${FIRST}"/actions-runner-linux-x64-*.tar.gz 2>/dev/null | head -1 || true)
install -d -o "$RUNNER_USER" -g "$RUNNER_USER" "$DIR"
if [ -n "$tarball" ]; then
  sudo -u "$RUNNER_USER" tar xzf "$tarball" -C "$DIR"
else                                                     # no tarball kept: copy the first instance's binaries
  sudo -u "$RUNNER_USER" bash -c "cd '${FIRST}' && tar cf - --exclude=_work --exclude=_diag --exclude=.runner \
    --exclude=.credentials --exclude=.credentials_rsaparams --exclude=.service . | tar xf - -C '${DIR}'"
fi

read -r -s -p "Registration token for ${NAME} (hidden): " TOKEN; echo
[ -n "$TOKEN" ] || { echo "no token"; exit 1; }
sudo -u "$RUNNER_USER" env RUNNER_TOKEN="$TOKEN" bash -c "cd '${DIR}' && ./config.sh --url '${REPO_URL}' \
  --token \"\$RUNNER_TOKEN\" --name '${NAME}' --labels '${LABELS}' --work _work --unattended --replace"
unset TOKEN

# The first instance's job-completed hook (font sweep) applies to every instance.
if [ -f "${FIRST}/.env" ] && grep -q ACTIONS_RUNNER_HOOK_JOB_COMPLETED "${FIRST}/.env"; then
  grep ACTIONS_RUNNER_HOOK_JOB_COMPLETED "${FIRST}/.env" | sudo -u "$RUNNER_USER" tee -a "${DIR}/.env" >/dev/null
fi
cd "$DIR" && ./svc.sh install "$RUNNER_USER" && ./svc.sh start
echo "${NAME} registered and started. Then set runners/render_slots/t0_reserve in templates/assets/server-lanes.json."
