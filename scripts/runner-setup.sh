#!/usr/bin/env bash
# DXB render server: one-time setup for a self-hosted GitHub Actions runner (advisor memo, 26 Oct 2026,
# approved by Mohammad). Target: Ubuntu 24.04, x86_64 (Hetzner AX, 8 cores, 64 GB). Run as root:
#
#   curl -fsSLo runner-setup.sh https://raw.githubusercontent.com/mohdeltayer/dxb-assets/ops/self-hosted-runner/scripts/runner-setup.sh \
#     && sudo bash runner-setup.sh
#
# (read it first if you like; it is plain bash). It can be run again: finished parts are skipped or refreshed,
# and the runner is registered only once. `sudo bash runner-setup.sh check` prints the state of the box and exits.
#
# What it installs, mirroring .github/workflows/render.yml step for step (same tools, same pins):
#   - ffmpeg and tesseract (apt), libsndfile
#   - Python 3.11 venv (uv fetches the interpreter; the system python3 is the fallback) with torch and torchvision
#     (CPU wheels, a matching pair), pillow, numpy, soundfile, pedalboard, ultralytics, opencv-python-headless,
#     pyloudnorm 0.1.1. mediapipe and faster-whisper are NOT installed: render.yml does not have them either,
#     so framing and speech checks behave exactly as on the GitHub runner.
#   - YOLOv8n weights (autofocus) and the Cocktail Fork audio-split model, pinned to render.yml's commit
#   - Node 22 and HyperFrames 0.8.143 with its Chromium (inserts and the design pass)
#   - the Actions runner as a systemd service under the non-root user `runner`, labels self-hosted, linux, x64
#     (added by GitHub as Linux, X64) and dxb-render
#   - ufw (SSH only, nothing else inbound) and unattended security upgrades
#
# What it does NOT do:
#   - Fonts. The Dubai fonts are never stored here: each job clones them from the private dxb-fonts repo with the
#     FONTS_TOKEN secret into its own temp folder and deletes them at the end, as render.yml does. A job-completed
#     hook sweeps them again if a job dies.
#   - Secrets. The runner registration token is typed at the prompt (hidden), handed to config.sh through the
#     environment of that one process, and never written to a file, a log or the repo. It expires after one hour.
#   - Touch sshd. If password logins are on, it says so; turning them off is your call.
#
# Layout:  /home/runner/actions-runner  the runner      /home/runner/venv   the Python environment
#          /var/cache/dxb-render        warm cache: models, cocktail-fork, tracksplit-stems, hf (HyperFrames), pip, npm
set -Eeuo pipefail
umask 022

REPO_URL="https://github.com/mohdeltayer/dxb-assets"
RUNNER_USER="runner"
RUNNER_HOME="/home/${RUNNER_USER}"
RUNNER_NAME="${RUNNER_NAME:-dxb-render-1}"
RUNNER_LABELS="dxb-render"
RUNNER_DIR="${RUNNER_HOME}/actions-runner"
VENV="${RUNNER_HOME}/venv"
CACHE="/var/cache/dxb-render"
PY_VERSION="${PY_VERSION:-3.11}"                       # render.yml: setup-python 3.11
NODE_MAJOR="22"                                        # render.yml: setup-node 22
HF_VERSION="0.8.143"                                   # HyperFrames, pinned (render.yml)
COCKTAIL_SHA="19b3de827ebc4bfb014570cf92dd32b4ee3b6921" # merlresearch/cocktail-fork-separation (render.yml)
AUTO_REBOOT="${AUTO_REBOOT:-}"                         # e.g. AUTO_REBOOT=03:30 to let security updates reboot the box (UTC); empty: never

log()  { printf '\n[%s] %s\n' "$(date -u +%T)" "$*"; }
warn() { printf '\n[%s] WARNING: %s\n' "$(date -u +%T)" "$*" >&2; WARNINGS+=("$*"); }
die()  { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
WARNINGS=()
trap 'echo "setup stopped at line ${LINENO} (exit $?). It is safe to run it again." >&2' ERR

as_runner() { sudo -H -u "${RUNNER_USER}" env "PIP_CACHE_DIR=${CACHE}/pip" "npm_config_cache=${CACHE}/npm" "HOME=${RUNNER_HOME}" "$@"; }

[ "$(id -u)" -eq 0 ] || die "run as root: sudo bash $0"
cd /     # the runner user must be able to read the working directory it inherits

# ---------------------------------------------------------------------------------------------------- check mode
check() {
  export PYTHONDONTWRITEBYTECODE=1        # root must not leave .pyc files in the runner's venv
  echo "== dxb-render check =="
  for c in ffmpeg tesseract node npm jq git ufw; do printf '%-10s %s\n' "$c" "$(command -v "$c" >/dev/null && "$c" --version 2>&1 | head -1 || echo MISSING)"; done
  [ -x "${VENV}/bin/python" ] && "${VENV}/bin/python" -c "import sys; print('python    ', sys.version.split()[0])" || echo "python     MISSING (${VENV})"
  [ -x "${VENV}/bin/python" ] && "${VENV}/bin/python" - <<'PY' || true
import importlib
for m in ('torch', 'torchvision', 'PIL', 'numpy', 'soundfile', 'pedalboard', 'ultralytics', 'cv2', 'pyloudnorm'):
    try:
        mod = importlib.import_module(m); print('%-10s %s' % (m, getattr(mod, '__version__', 'ok')))
    except Exception as e:
        print('%-10s MISSING (%s)' % (m, e))
PY
  for f in "${CACHE}/models/yolov8n.pt" "${CACHE}/cocktail-fork/${COCKTAIL_SHA}/mrx.py" \
           "${CACHE}/cocktail-fork/${COCKTAIL_SHA}/checkpoints/default_mrx_pre_trained_weights.pth" "${CACHE}/hf/node_modules/.bin/hyperframes"; do
    [ -s "$f" ] && echo "ok         $f" || echo "MISSING    $f"
  done
  ufw status 2>/dev/null | head -8 || true
  systemctl list-units --type=service --no-legend 'actions.runner.*' 2>/dev/null || true
  df -h / "${CACHE}" 2>/dev/null | sed 's/^/disk       /'
  free -g | sed 's/^/mem        /'
}
if [ "${1:-}" = "check" ]; then check; exit 0; fi

# ---------------------------------------------------------------------------------------------------- 0. the box
. /etc/os-release
[ "${ID:-}" = "ubuntu" ] && [ "${VERSION_ID:-}" = "24.04" ] || [ "${FORCE:-}" = "1" ] || die "built for Ubuntu 24.04 (this is ${PRETTY_NAME:-unknown}); FORCE=1 to try anyway"
[ "$(uname -m)" = "x86_64" ] || die "x86_64 only (the runner labels and the wheels assume it)"
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
APT=(apt-get -o DPkg::Lock::Timeout=300 -o Acquire::Retries=3 -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold -y -q)
log "box: ${PRETTY_NAME}, $(nproc) cores, $(free -g | awk '/Mem:/{print $2}') GB memory"

# ---------------------------------------------------------------------------------------------------- 1. packages
log "apt: base tools, ffmpeg, tesseract, browser libraries"
"${APT[@]}" update
# Chromium (HyperFrames) needs these on 24.04 (t64 names); ffmpeg and tesseract are what render.yml installs
"${APT[@]}" install --no-install-recommends \
  ca-certificates curl gnupg git jq unzip xz-utils ufw unattended-upgrades \
  ffmpeg tesseract-ocr tesseract-ocr-eng libsndfile1 \
  python3 python3-venv python3-pip \
  fonts-liberation libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64 libpango-1.0-0 libcairo2 libx11-6 \
  libxcb1 libxext6 libglib2.0-0t64 libdbus-1-3 libxshmfence1 \
  libatomic1
command -v ffmpeg >/dev/null && command -v tesseract >/dev/null || die "ffmpeg or tesseract did not install"

if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" != "${NODE_MAJOR}" ]; then
  log "node ${NODE_MAJOR} (NodeSource apt repository, signed)"
  install -d -m 0755 /etc/apt/keyrings
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor --yes -o /etc/apt/keyrings/nodesource.gpg
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" > /etc/apt/sources.list.d/nodesource.list
  "${APT[@]}" update
  "${APT[@]}" install --no-install-recommends nodejs
fi
node --version

# ---------------------------------------------------------------------------------------------------- 2. security
log "unattended security upgrades"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
{
  echo '// DXB render server: security pocket only (the Ubuntu default), no surprise major upgrades.'
  echo 'Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";'
  echo 'Unattended-Upgrade::Remove-Unused-Dependencies "true";'
  if [ -n "${AUTO_REBOOT}" ]; then
    echo 'Unattended-Upgrade::Automatic-Reboot "true";'
    echo 'Unattended-Upgrade::Automatic-Reboot-WithUsers "true";'
    echo "Unattended-Upgrade::Automatic-Reboot-Time \"${AUTO_REBOOT}\";"
  else
    echo '// No automatic reboot: a reboot in the middle of a render loses that job. Check /var/run/reboot-required now and then.'
    echo 'Unattended-Upgrade::Automatic-Reboot "false";'
  fi
} > /etc/apt/apt.conf.d/52dxb-unattended
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true

log "firewall: ufw, SSH only"
SSH_PORTS="$( (sshd -T 2>/dev/null | awk '$1=="port"{print $2}') || true)"
[ -n "${SSH_PORTS}" ] || SSH_PORTS=22
ufw --force reset >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
for p in ${SSH_PORTS}; do ufw limit "${p}/tcp" comment 'ssh' >/dev/null; done
ufw logging low >/dev/null
ufw --force enable >/dev/null
ufw status verbose | sed -n 1,12p
if sshd -T 2>/dev/null | grep -qi '^passwordauthentication yes'; then
  warn "SSH still accepts passwords. Use key-only logins (PasswordAuthentication no) once your key works; not changed here to avoid a lockout."
fi

# ---------------------------------------------------------------------------------------------------- 3. the user and the cache
if ! id "${RUNNER_USER}" >/dev/null 2>&1; then
  log "user ${RUNNER_USER} (no password, no sudo)"
  useradd --create-home --shell /bin/bash --comment "GitHub Actions render runner" "${RUNNER_USER}"
fi
passwd -l "${RUNNER_USER}" >/dev/null 2>&1 || true
if id -nG "${RUNNER_USER}" | tr ' ' '\n' | grep -qxE 'sudo|admin|docker'; then
  warn "${RUNNER_USER} is in a privileged group (sudo/admin/docker). The runner executes workflow code: take it out."
fi
install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0755 "${CACHE}" "${CACHE}/models" "${CACHE}/cocktail-fork" \
  "${CACHE}/tracksplit-stems" "${CACHE}/hf" "${CACHE}/pip" "${CACHE}/npm"

# ---------------------------------------------------------------------------------------------------- 4. Python
if [ ! -x "${VENV}/bin/python" ]; then
  log "python ${PY_VERSION} venv at ${VENV}"
  BOOT="$(mktemp -d)"; chmod 0755 "${BOOT}"
  python3 -m venv "${BOOT}/uv" && "${BOOT}/uv/bin/pip" install -q uv \
    && as_runner "${BOOT}/uv/bin/uv" venv --seed --python "${PY_VERSION}" --managed-python "${VENV}" \
    || { warn "could not fetch Python ${PY_VERSION} with uv; using the system python3 ($(python3 -V)). Parity with the GitHub runner is looser."; rm -rf "${VENV}"; as_runner python3 -m venv "${VENV}"; }
  rm -rf "${BOOT}"
fi
chown -R "${RUNNER_USER}:${RUNNER_USER}" "${VENV}"
PY="${VENV}/bin/python"
log "python packages (as render.yml: a matching torch and torchvision pair from the CPU index, then the rest)"
as_runner "${PY}" -m pip install -q --upgrade pip
as_runner "${PY}" -m pip install -q --timeout 60 --retries 3 torch torchvision --index-url https://download.pytorch.org/whl/cpu
as_runner "${PY}" -m pip install -q --timeout 60 --retries 3 pillow numpy soundfile pedalboard ultralytics opencv-python-headless pyloudnorm==0.1.1
as_runner "${PY}" -m pip freeze > "${CACHE}/pip-freeze.txt"
"${PY}" -V

log "YOLOv8n weights (autofocus) in ${CACHE}/models"
as_runner env "W=${CACHE}/models/yolov8n.pt" "${PY}" - <<'PY'
import os, numpy as np
from ultralytics import YOLO
from ultralytics.utils.downloads import attempt_download_asset
w = os.environ['W']
if not os.path.exists(w):
    attempt_download_asset(w)
YOLO(w).predict(np.zeros((360, 640, 3), np.uint8), imgsz=640, device='cpu', verbose=False)   # torch and torchvision agree?
print('yolo ready')
PY

log "Cocktail Fork audio split ${COCKTAIL_SHA:0:7} in ${CACHE}/cocktail-fork"
if as_runner env "D=${CACHE}/cocktail-fork/${COCKTAIL_SHA}" "SHA=${COCKTAIL_SHA}" bash -s <<'SH'
set -e
mkdir -p "$D/checkpoints"
[ -s "$D/mrx.py" ] || curl -sSfL --retry 3 -o "$D/mrx.py" "https://raw.githubusercontent.com/merlresearch/cocktail-fork-separation/$SHA/mrx.py"
w="$D/checkpoints/default_mrx_pre_trained_weights.pth"
[ -s "$w" ] || curl -sSfL --retry 3 -o "$w" "https://media.githubusercontent.com/media/merlresearch/cocktail-fork-separation/$SHA/checkpoints/default_mrx_pre_trained_weights.pth"
SH
then
  as_runner env "D=${CACHE}/cocktail-fork/${COCKTAIL_SHA}" "${PY}" -c "import sys, os, torch; d = os.environ['D']; sys.path.insert(0, d); import mrx; m = mrx.MRX(); m.load_state_dict(torch.load(d + '/checkpoints/default_mrx_pre_trained_weights.pth', map_location='cpu', weights_only=True)); print('cocktail fork ready')" \
    || warn "Cocktail Fork did not load; jobs on a trailer track keep today's audio (render.yml's own fallback)."
else
  warn "Cocktail Fork download failed; jobs on a trailer track keep today's audio."
fi

# ---------------------------------------------------------------------------------------------------- 5. HyperFrames
log "HyperFrames ${HF_VERSION} and its browser (inserts and the design pass)"
if as_runner bash -s <<SH
set -e
cd "${CACHE}/hf"
[ -f package.json ] || echo '{"name":"dxb-hf","private":true}' > package.json
npm i -s --no-audit --no-fund hyperframes@${HF_VERSION}
./node_modules/.bin/hyperframes browser ensure
SH
then
  CHROME="$(find "${RUNNER_HOME}/.cache" "${CACHE}/hf" -type f \( -name chrome -o -name chrome-headless-shell -o -name headless_shell \) 2>/dev/null | head -1 || true)"
  if [ -n "${CHROME}" ]; then
    MISSING="$(ldd "${CHROME}" 2>/dev/null | awk '/not found/{print $1}' | tr '\n' ' ')"
    [ -z "${MISSING}" ] && echo "browser ok: ${CHROME}" || warn "browser libraries missing: ${MISSING}"
  else
    warn "could not find the HyperFrames browser binary to check its libraries; the first insert job will show."
  fi
else
  warn "HyperFrames install failed; jobs with an insert or design pass fall back exactly as on the GitHub runner."
fi

# ---------------------------------------------------------------------------------------------------- 6. the runner
install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0755 "${RUNNER_DIR}" "${RUNNER_HOME}/hooks"
cat > "${RUNNER_HOME}/hooks/job-completed.sh" <<'EOF'
#!/usr/bin/env bash
# After every job: the Dubai fonts and per-job scratch go, whatever the job did. Never fails the job.
t="${RUNNER_TEMP:-}"
if [ -n "$t" ] && [ -d "$t" ]; then rm -rf "$t/dubai-fonts" "$t/dxb-fonts" "$t/uploads" "$t/out" 2>/dev/null; fi
pkill -u "$(id -u)" -f 'runner_stats.py loop' 2>/dev/null
exit 0
EOF
chown "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_HOME}/hooks/job-completed.sh"; chmod 0755 "${RUNNER_HOME}/hooks/job-completed.sh"

if [ -f "${RUNNER_DIR}/.runner" ]; then
  log "runner already registered here; leaving the registration alone"
else
  log "download the Actions runner"
  if [ -n "${RUNNER_VERSION:-}" ]; then REL="https://api.github.com/repos/actions/runner/releases/tags/v${RUNNER_VERSION#v}"; else REL="https://api.github.com/repos/actions/runner/releases/latest"; fi
  META="$(curl -fsSL "${REL}")"
  TAG="$(jq -r .tag_name <<<"${META}")"; VER="${TAG#v}"
  SHA256="$(jq -r .body <<<"${META}" | sed -n 's/.*<!-- BEGIN SHA linux-x64 -->\([0-9a-f]\{64\}\)<!-- END SHA linux-x64 -->.*/\1/p' | head -1)"
  [ -n "${SHA256}" ] || die "could not read the published checksum for runner ${TAG}; not installing an unverified download"
  TGZ="$(mktemp --suffix=.tar.gz)"
  curl -fsSL -o "${TGZ}" "https://github.com/actions/runner/releases/download/${TAG}/actions-runner-linux-x64-${VER}.tar.gz"
  echo "${SHA256}  ${TGZ}" | sha256sum -c - >/dev/null || die "runner download failed its checksum"
  tar -xzf "${TGZ}" -C "${RUNNER_DIR}" && rm -f "${TGZ}"
  chown -R "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_DIR}"
  echo "runner ${TAG}, checksum ok"

  echo
  echo "Registration token: GitHub, ${REPO_URL##https://github.com/} > Settings > Actions > Runners > New self-hosted runner (valid for one hour)."
  echo "Paste it below. Nothing is shown and nothing is saved."
  [ -r /dev/tty ] || die "needs a terminal to ask for the token (run it from an SSH session, not a pipe)"
  IFS= read -rsp "Token: " REG_TOKEN </dev/tty; echo
  [ -n "${REG_TOKEN}" ] || die "no token given"
  export ACTIONS_RUNNER_INPUT_TOKEN="${REG_TOKEN}"        # read by config.sh from its environment, never from argv
  unset REG_TOKEN
  log "register the runner as ${RUNNER_NAME} (labels: ${RUNNER_LABELS})"
  if ! sudo -H -u "${RUNNER_USER}" --preserve-env=ACTIONS_RUNNER_INPUT_TOKEN bash -c \
       "cd '${RUNNER_DIR}' && ./config.sh --unattended --replace --url '${REPO_URL}' --name '${RUNNER_NAME}' --labels '${RUNNER_LABELS}' --work _work"; then
    unset ACTIONS_RUNNER_INPUT_TOKEN
    die "registration failed (expired or mistyped token?). Run the script again with a fresh token."
  fi
  unset ACTIONS_RUNNER_INPUT_TOKEN
fi

# the runner's environment: where the tools live. The workflow has the same defaults if this file is not read.
ENVF="${RUNNER_DIR}/.env"
touch "${ENVF}"
sed -i '/^DXB_CACHE=/d;/^DXB_VENV=/d;/^ACTIONS_RUNNER_HOOK_JOB_COMPLETED=/d;/^LANG=/d' "${ENVF}"
{
  echo "DXB_CACHE=${CACHE}"
  echo "DXB_VENV=${VENV}"
  echo "LANG=C.UTF-8"
  echo "ACTIONS_RUNNER_HOOK_JOB_COMPLETED=${RUNNER_HOME}/hooks/job-completed.sh"
} >> "${ENVF}"
chown "${RUNNER_USER}:${RUNNER_USER}" "${ENVF}"

log "systemd service"
cd "${RUNNER_DIR}"
if [ ! -f .service ]; then ./svc.sh install "${RUNNER_USER}"; fi
UNIT="$(cat .service)"
install -d "/etc/systemd/system/${UNIT}.d"
cat > "/etc/systemd/system/${UNIT}.d/dxb.conf" <<'EOF'
[Service]
Restart=always
RestartSec=15
NoNewPrivileges=yes
EOF
systemctl daemon-reload
if systemctl is-active --quiet "${UNIT}"; then
  echo "service ${UNIT} is already running; not restarting it (a render may be in progress). When idle: systemctl restart ${UNIT}"
else
  ./svc.sh start >/dev/null 2>&1 || systemctl restart "${UNIT}"
fi
sleep 3
systemctl is-active --quiet "${UNIT}" && echo "service ${UNIT}: active" || warn "service ${UNIT} is not active; see: journalctl -u ${UNIT} -n 50"

# daily: age out stems nobody has touched for two weeks (tracksplit.py also caps the folder at 800 MB)
cat > /etc/cron.daily/dxb-render-prune <<EOF
#!/bin/sh
find ${CACHE}/tracksplit-stems -type f -mtime +14 -delete 2>/dev/null
find ${RUNNER_DIR}/_work/_temp -mindepth 1 -maxdepth 1 -mtime +1 -exec rm -rf {} + 2>/dev/null
exit 0
EOF
chmod 0755 /etc/cron.daily/dxb-render-prune

# ---------------------------------------------------------------------------------------------------- done
check
echo
if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo "Warnings:"; printf '  - %s\n' "${WARNINGS[@]}"; echo
fi
[ -f /var/run/reboot-required ] && echo "A reboot is pending (kernel update). Reboot when no render is running."
cat <<EOF
Done. In GitHub (${REPO_URL}) please confirm:
  - Settings > Actions > Runners: ${RUNNER_NAME} shows Idle with labels self-hosted, Linux, X64, dxb-render.
  - Settings > Actions > General > Fork pull request workflows: "Require approval for all outside collaborators".
  - The default workflow permission stays read-only. No workflow that runs on this server may use pull_request triggers.
  - The repo is public: the server only runs workflows pushed to main by you. Keep it that way.
EOF
