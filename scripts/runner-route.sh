#!/usr/bin/env bash
# Where should a render run? (advisor memo, 26 Oct 2026, fallback design; no token beyond the job's own GITHUB_TOKEN.)
#
# Run in a small job on a GitHub-hosted runner. It dispatches .github/workflows/runner-probe.yml (a one-second job
# that needs the dxb-render server), and waits up to WAIT seconds (default 300) for that job to start:
#   started in time  -> lane=self-hosted   the server is online and free; the render can go there
#   not started      -> lane=hosted        offline, or busy for over five minutes; it cancels the probe run (so a
#                                          server that comes back later finds nothing queued) and the render runs
#                                          on GitHub's machine
#   anything odd     -> lane=hosted        the API failing never leaves a render without a place to run
# Writes lane, wait_secs and reason to $GITHUB_OUTPUT (and a line to the job summary). Never exits non-zero.
#
# Needs: gh and jq (on GitHub's runners), GH_TOKEN = the job's GITHUB_TOKEN with `actions: write` (dispatch and
# cancel; the retry job in render.yml already holds the same permission), GITHUB_REPOSITORY, GITHUB_RUN_ID.
set -uo pipefail
WAIT="${WAIT:-300}"; STEP="${STEP:-5}"
repo="${GITHUB_REPOSITORY:?}"; wf="runner-probe.yml"; ref="${PROBE_REF:-main}"
id="${GITHUB_RUN_ID:-0}-${GITHUB_RUN_ATTEMPT:-1}-${RANDOM}"
t0=$(date +%s)

out() {  # lane wait reason
  echo "route: lane=$1 wait=${2}s ($3)"
  { echo "lane=$1"; echo "wait_secs=$2"; echo "reason=$3"; } >> "${GITHUB_OUTPUT:-/dev/null}"
  [ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "Render lane: **$1** (probe wait ${2}s, $3)" >> "$GITHUB_STEP_SUMMARY"
  exit 0
}
elapsed() { echo $(( $(date +%s) - t0 )); }

gh api -X POST "repos/$repo/actions/workflows/$wf/dispatches" -f "ref=$ref" -f "inputs[id]=$id" >/dev/null 2>&1 \
  || out hosted "$(elapsed)" "could not start the probe"

rid=""
while [ -z "$rid" ] && [ "$(elapsed)" -lt 60 ]; do
  sleep 3
  rid=$(gh api "repos/$repo/actions/workflows/$wf/runs?event=workflow_dispatch&per_page=30" \
        --jq ".workflow_runs[] | select(.display_title == \"probe $id\") | .id" 2>/dev/null | head -1)
done
[ -n "$rid" ] || out hosted "$(elapsed)" "probe run not found"

while :; do
  job=$(gh api "repos/$repo/actions/runs/$rid/jobs" --jq '.jobs[0] | [.status, .created_at, .started_at] | @tsv' 2>/dev/null || true)
  status=$(cut -f1 <<<"$job")
  if [ "$status" = "in_progress" ] || [ "$status" = "completed" ]; then
    c=$(date -d "$(cut -f2 <<<"$job")" +%s 2>/dev/null || echo "$t0"); s=$(date -d "$(cut -f3 <<<"$job")" +%s 2>/dev/null || date +%s)
    out self-hosted "$(( s - c ))" "server picked up the probe"
  fi
  if [ "$(elapsed)" -ge "$WAIT" ]; then
    gh api -X POST "repos/$repo/actions/runs/$rid/cancel" >/dev/null 2>&1 || true
    out hosted "$(elapsed)" "no start within ${WAIT}s: server offline or busy"
  fi
  sleep "$STEP"
done
