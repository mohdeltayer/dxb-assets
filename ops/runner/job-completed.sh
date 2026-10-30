#!/usr/bin/env bash
# After every job on dxb-render-1: the Dubai fonts and per-job scratch go, whatever the job did. Never fails the job.
# The runner runs hooks with bash -e -o pipefail, so every command here must not return non-zero
# (pkill returns 1 when nothing matches, which stopped the hook and marked passing jobs failed, 26 Oct).
# Installed by .github/workflows/runner-hook.yml (same content as scripts/runner-setup.sh on ops/self-hosted-runner, 6e11bcc).
set +e
t="${RUNNER_TEMP:-}"
if [ -n "$t" ] && [ -d "$t" ]; then rm -rf "$t/dubai-fonts" "$t/dxb-fonts" "$t/uploads" "$t/out" 2>/dev/null || true; fi
pkill -u "$(id -u)" -f 'runner_stats.py loop' 2>/dev/null || true
exit 0
