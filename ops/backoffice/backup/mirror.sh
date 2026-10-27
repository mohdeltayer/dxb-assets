#!/usr/bin/env bash
# mirror.sh: nightly backup mirror for the render server dxb-render-1.
#
# Modes:
#   nightly          update the git mirrors, export the small text files, take a
#                    hard-linked snapshot, prune to 14, write the heartbeat, tell ntfy.
#                    Skips (exit 75) while a render is active. A second timer run
#                    later in the night is a no-op if the first one succeeded.
#   full             the same, but forced (use after a manual "full" Backblaze run).
#   heartbeat-check  alert through ntfy when the last success is older than 26 h.
#   restore-test     clone dxb-queue from the mirror into a scratch folder, git fsck
#                    --full, compare HEAD and branches; prints result and time.
#   status           print what is there (mirrors, snapshots, last runs, free disk).
#
# Runs as the user dxbbackup (not runner). Reads two root-owned files, never
# prints or copies them: /etc/dxb-backup/github-token and /etc/dxb-backup/ntfy-topic.
# See README.md next to this file. Environment overrides exist for tests:
# DXB_BACKUP_ETC, DXB_BACKUP_ROOT, DXB_BACKUP_REPOS, DXB_BACKUP_NTFY=off, ...

set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=${SELF%/*}

ETC=${DXB_BACKUP_ETC:-/etc/dxb-backup}
ROOT=${DXB_BACKUP_ROOT:-$HOME/mirror}
GITDIR=$ROOT/git
SNAPDIR=$ROOT/snapshots
STATE=$ROOT/state
EXPORT=$STATE/export-build
LOG=$STATE/backup.log
TOKEN_FILE=$ETC/github-token
TOPIC_FILE=$ETC/ntfy-topic

FLOOR_GB=${DXB_BACKUP_FLOOR_GB:-40}          # hard floor: free space must stay above this
KEEP=${DXB_BACKUP_KEEP:-14}                  # snapshots kept
STALE_H=${DXB_BACKUP_STALE_HOURS:-26}        # heartbeat-check threshold
WAIT_MIN=${DXB_BACKUP_WAIT_MIN:-30}          # how long to wait for a render to end
POLL=${DXB_BACKUP_POLL:-30}                  # seconds between busy checks
GUARD_SECS=${DXB_BACKUP_GUARD_SECS:-15}      # seconds between free-space checks while git runs
RETRY_SLEEP=${DXB_BACKUP_RETRY_SLEEP:-30}
BUSY_RE=${DXB_BACKUP_BUSY_PATTERN:-'render_job\.py|Runner\.Worker'}
NTFY=${DXB_BACKUP_NTFY:-on}
NTFY_URL=${DXB_BACKUP_NTFY_URL:-https://ntfy.sh}
MAX_EXPORT_BYTES=${DXB_BACKUP_MAX_EXPORT_FILE:-5242880}
CONFIG_REPO=${DXB_BACKUP_CONFIG_REPO:-$HOME/dxb-assets}
UNIT_DIR=${DXB_BACKUP_UNIT_DIR:-$HOME/.config/systemd/user}
# name|url|fallback size in GB (used only to size the free-space check when the
# GitHub API cannot tell). Space-separated entries.
REPOS=${DXB_BACKUP_REPOS:-"dxb-assets|https://github.com/mohdeltayer/dxb-assets.git|30 dxb-queue|https://github.com/mohdeltayer/dxb-queue.git|5 dxb-fonts|https://github.com/mohdeltayer/dxb-fonts.git|1"}

GB=1073741824
FLOOR_B=$((FLOOR_GB * GB))
UNITS=(dxb-backup.service dxb-backup.timer dxb-backup-check.service dxb-backup-check.timer)

MODE=""
STEP="starting"
OUTCOME=""
SCRATCH=""
T_START=$SECONDS

# ---------------------------------------------------------------- logging

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
dubai_date() { TZ=Asia/Dubai date +%F; }
redact() { sed -E 's/(github_pat_|gh[pousr]_)[A-Za-z0-9_]+/\1[redacted]/g'; }

log() {
  local line
  line="$(ts) $*"
  printf '%s\n' "$line" | redact
  if [[ -d $STATE ]]; then printf '%s\n' "$line" | redact >>"$LOG"; fi
}

human() { # bytes -> 12.3G
  awk -v b="$1" 'BEGIN{ s="B K M G T"; split(s,u," "); i=1; while (b>=1024 && i<5) { b/=1024; i++ } printf (i==1 ? "%d%s" : "%.1f%s"), b, u[i] }'
}

avail_bytes() { df -P -B1 "$1" | awk 'NR==2{print $4}'; }

# ---------------------------------------------------------------- alerts

# notify <title> <body> [priority] [tags]. Topic only ever goes to curl on stdin.
notify() {
  local title=$1 body=$2 prio=${3:-default} tags=${4:-} topic out
  if [[ $NTFY == off ]]; then
    log "ntfy off: [$prio] $title: $body"
    return 0
  fi
  if [[ ! -r $TOPIC_FILE ]]; then
    log "ntfy: topic file not readable, alert NOT sent: $title: $body"
    return 1
  fi
  topic=$(tr -d '[:space:]' <"$TOPIC_FILE")
  if [[ -z $topic ]]; then
    log "ntfy: topic file is empty, alert NOT sent: $title: $body"
    return 1
  fi
  if out=$(printf 'url = "%s/%s"\n' "$NTFY_URL" "$topic" |
    curl -sS --max-time 20 -K - -o /dev/null \
      -H "Title: $title" -H "Priority: $prio" ${tags:+-H "Tags: $tags"} \
      -d "$body" 2>&1); then
    log "ntfy sent: $title"
  else
    log "ntfy: send failed (${out//$topic/[topic]}): $title"
    return 1
  fi
}

fail() { # fail <message>: alert and stop
  OUTCOME=failed
  log "FAILED ($STEP): $*"
  case $MODE in
    nightly | full) notify "dxb-render-1 backup FAILED" "$MODE: $* (step: $STEP). Log: ~dxbbackup/mirror/state/backup.log" high warning || true ;;
  esac
  exit 1
}

on_exit() {
  local rc=$?
  trap - EXIT
  jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
  if [[ -n $SCRATCH && -d $SCRATCH ]]; then rm -rf "$SCRATCH"; fi
  if ((rc != 0)) && [[ -z $OUTCOME ]]; then
    OUTCOME=failed
    log "FAILED ($STEP): unexpected error, exit $rc"
    case $MODE in
      nightly | full) notify "dxb-render-1 backup FAILED" "$MODE: unexpected error at step: $STEP (exit $rc). Log: ~dxbbackup/mirror/state/backup.log" high warning || true ;;
    esac
  fi
  case $MODE in
    nightly | full | heartbeat-check)
      if [[ -d $STATE ]]; then printf '%s %s %s exit=%s\n' "$(ts)" "$MODE" "${OUTCOME:-ok}" "$rc" >"$STATE/last-run"; fi
      ;;
  esac
  exit "$rc"
}

# ---------------------------------------------------------------- guards

need_tools() {
  local t missing=()
  for t in git rsync curl flock pgrep tar awk sed df find grep; do
    command -v "$t" >/dev/null 2>&1 || missing+=("$t")
  done
  if ((${#missing[@]})); then
    fail "missing tools: ${missing[*]} (root: apt-get install -y git rsync curl util-linux procps)"
  fi
}

setup_git_auth() {
  STEP="reading the GitHub token file"
  if [[ ! -e $TOKEN_FILE ]]; then
    fail "token file $TOKEN_FILE is missing. Root must create it (see README.md, one-time root steps)"
  fi
  if [[ ! -r $TOKEN_FILE ]]; then
    fail "token file $TOKEN_FILE exists but dxbbackup cannot read it (needs mode 0640, owner root, group dxbbackup)"
  fi
  if [[ -z $(tr -d '[:space:]' <"$TOKEN_FILE") ]]; then
    fail "token file $TOKEN_FILE is empty"
  fi
  # The credential helper reads the file when git asks. The environment carries
  # only the file's path, never the token; the token is not in any argv.
  export DXB_TOKEN_FILE=$TOKEN_FILE
  export GIT_TERMINAL_PROMPT=0
  export GIT_CONFIG_COUNT=2
  export GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0=
  export GIT_CONFIG_KEY_1=credential.https://github.com.helper
  # shellcheck disable=SC2016  # the helper is a shell snippet that git runs, not expanded here
  export GIT_CONFIG_VALUE_1='!f() { test "$1" = get || exit 0; echo username=x-access-token; printf "password=%s\n" "$(tr -d "[:space:]" <"$DXB_TOKEN_FILE")"; }; f'
}

busy() { pgrep -f -- "$BUSY_RE" >/dev/null 2>&1; }

wait_idle() { # returns 1 when a render is still active after WAIT_MIN
  local waited=0
  while busy; do
    if ((waited == 0)); then log "render active (process matching '$BUSY_RE'); waiting up to ${WAIT_MIN} min"; fi
    if ((waited >= WAIT_MIN * 60)); then return 1; fi
    sleep "$POLL"
    waited=$((waited + POLL))
  done
  return 0
}

skip_busy() {
  OUTCOME=skipped
  local d n=1
  d=$(dubai_date)
  if [[ -f $STATE/last-skip ]] && [[ $(cut -d' ' -f1 "$STATE/last-skip") == "$d" ]]; then
    n=$(($(cut -d' ' -f2 "$STATE/last-skip") + 1))
  fi
  printf '%s %s\n' "$d" "$n" >"$STATE/last-skip"
  log "SKIPPED ($STEP): a render is still active after ${WAIT_MIN} min; the timer retries later tonight"
  if ((n >= 2)); then
    notify "dxb-render-1 backup skipped twice" "Render kept the server busy on both tries tonight ($d). No new snapshot yet." default hourglass || true
  fi
  exit 75
}

floor_stop() { # floor_stop <what> <need bytes>
  local avail
  avail=$(avail_bytes "$ROOT")
  OUTCOME=floor
  log "STOPPED: free disk $(human "$avail") would drop under the ${FLOOR_GB} GB floor ($1, needs about $(human "$2"))"
  notify "dxb-render-1 backup STOPPED: disk floor" "Free $(human "$avail"), floor ${FLOOR_GB} GB, step: $1 (needs about $(human "$2")). Nothing more written." urgent rotating_light || true
  exit 3
}

check_floor() { # check_floor <need bytes> <what>
  local avail
  avail=$(avail_bytes "$ROOT")
  if ((avail - $1 < FLOOR_B)); then floor_stop "$2" "$1"; fi
}

# guarded <label> cmd...: run in the background; kill it and stop the whole run
# if free space falls under the floor while it writes.
guarded() {
  local label=$1 out pid rc=0 tick=0 killed=0
  shift
  out=$(mktemp "$STATE/cmd.XXXXXX")
  "$@" >"$out" 2>&1 &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    sleep 1
    tick=$((tick + 1))
    if ((tick >= GUARD_SECS)); then
      tick=0
      if (($(avail_bytes "$ROOT") < FLOOR_B)); then
        killed=1
        kill "$pid" 2>/dev/null || true
        break
      fi
    fi
  done
  wait "$pid" || rc=$?
  if [[ -s $out ]]; then redact <"$out" | tail -n 30 | sed "s/^/    [$label] /" >>"$LOG"; fi
  rm -f "$out"
  if ((killed)); then floor_stop "$label" 0; fi
  return "$rc"
}

retry() { # retry <tries> <label> cmd...
  local tries=$1 label=$2 i rc=0
  shift 2
  for ((i = 1; i <= tries; i++)); do
    rc=0
    guarded "$label" "$@" || rc=$?
    if ((rc == 0)); then return 0; fi
    log "$label failed (attempt $i of $tries, exit $rc)"
    if ((i < tries)); then sleep $((RETRY_SLEEP * i)); fi
  done
  return "$rc"
}

# ---------------------------------------------------------------- mirrors

estimate_bytes() { # estimate_bytes <url> <fallback gb>: size of a first clone, from the API when possible
  local url=${1%.git} gb=$2 kb=""
  if [[ $url =~ ^https://github\.com/([^/]+)/([^/]+)$ && -r $TOKEN_FILE ]]; then
    kb=$(printf 'header = "Authorization: Bearer %s"\n' "$(tr -d '[:space:]' <"$TOKEN_FILE")" |
      curl -sS --max-time 20 -K - -H 'Accept: application/vnd.github+json' \
        "https://api.github.com/repos/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}" 2>/dev/null |
      sed -nE 's/.*"size": *([0-9]+).*/\1/p' | head -n 1) || kb=""
  fi
  if [[ $kb =~ ^[0-9]+$ && $kb -gt 0 ]]; then
    echo $((kb * 1024 * 13 / 10 + GB))
  else
    echo $((gb * GB))
  fi
}

configure_mirror() {
  local d=$1
  git --git-dir="$d" config gc.auto 0              # never repack: snapshots hard-link the packs
  git --git-dir="$d" config receive.autogc false
  git --git-dir="$d" config transfer.unpackLimit 1 # keep every fetch as one immutable pack
  git --git-dir="$d" config fetch.unpackLimit 1
}

mirror_one() { # mirror_one <name> <url> <fallback gb>
  local name=$1 url=$2 gb=$3 need part d
  d=$GITDIR/$name.git
  if [[ -d $d ]]; then
    STEP="updating mirror $name"
    check_floor $((2 * GB)) "update $name"
    retry 3 "update $name" git --git-dir="$d" remote update --prune ||
      fail "git remote update --prune failed for $name three times (see log)"
    log "mirror $name updated"
  else
    STEP="first clone of $name"
    need=$(estimate_bytes "$url" "$gb")
    log "mirror $name: first clone, estimated size $(human "$need")"
    check_floor "$need" "first clone of $name"
    part=$GITDIR/.$name.git.partial
    rm -rf "$part"
    retry 2 "clone $name" git clone --mirror "$url" "$part" ||
      fail "git clone --mirror failed for $name twice (see log)"
    mv "$part" "$d"
    log "mirror $name cloned"
  fi
  configure_mirror "$d"
  git --git-dir="$d" rev-parse -q --verify HEAD >/dev/null || log "note: $name has no HEAD commit (empty repo?)"
}

# ---------------------------------------------------------------- export

# Secret check on staged files: the real token and topic values, plus common token shapes.
SECRET_RE='github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|xox[abprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'

drop_secret_files() { # drop_secret_files <dir>: remove files that hold a secret, list their names
  local dir=$1 f pf
  while IFS= read -r -d '' f; do
    log "export: left out (looks like a secret value, name only): ${f#"$EXPORT"/}"
    printf '%s\tsecret-pattern\n' "${f#"$EXPORT"/}" >>"$EXPORT/SKIPPED.txt"
    rm -f -- "$f"
  done < <(grep -rIlZE -e "$SECRET_RE" "$dir" 2>/dev/null || true)
  for pf in "$TOKEN_FILE" "$TOPIC_FILE"; do
    [[ -r $pf ]] || continue
    tr -d '[:space:]' <"$pf" >"$STATE/.pat.$$" || true
    [[ -s $STATE/.pat.$$ ]] || continue
    printf '\n' >>"$STATE/.pat.$$"
    while IFS= read -r -d '' f; do
      log "export: left out (holds a live secret value, name only): ${f#"$EXPORT"/}"
      printf '%s\tsecret-value\n' "${f#"$EXPORT"/}" >>"$EXPORT/SKIPPED.txt"
      rm -f -- "$f"
    done < <(grep -rIlZF -f "$STATE/.pat.$$" "$dir" 2>/dev/null || true)
    rm -f "$STATE/.pat.$$"
  done
}

export_repo() { # export_repo <name>
  local name=$1 m dest
  m=$GITDIR/$name.git
  dest=$EXPORT/$name
  local -a pats=() eargs=() paths=()
  local i n=0 big f head
  case $name in
    dxb-assets)
      pats=('^templates/assets/format-ledger\.json$' '^newsroom/corrections\.md$' '^cards/.*\.(json|md|csv|txt|ya?ml)$')
      ;;
    dxb-queue)
      pats=('^ops/.*\.(md|json|csv|txt|ya?ml)$' '^(queue|drafts)/.*/(job|receipt)\.json$' '^\.github/workflows/.*\.ya?ml$')
      ;;
    *)
      log "export $name: nothing exported (mirror only)"
      return 0
      ;;
  esac
  # rights and key registers (names and purposes only, the secret check below
  # drops any file that holds a value), and the Publer media index if there is one
  pats+=('(^|/)[^/]*(rights|key)[-_ ]?register[^/]*\.(md|json|csv|txt)$'
    '(^|/)[^/]*(publer[-_]?media|media[-_]?index)[^/]*\.(json|csv|md|txt)$')
  for i in "${pats[@]}"; do eargs+=(-e "$i"); done

  if ! head=$(git --git-dir="$m" rev-parse -q --verify HEAD); then
    log "export $name: no HEAD commit, nothing exported"
    return 0
  fi
  mkdir -p "$dest"
  mapfile -d '' -t paths < <(git --literal-pathspecs --git-dir="$m" ls-tree -r -z --name-only HEAD | grep -zE "${eargs[@]}" || true)
  n=${#paths[@]}
  for ((i = 0; i < n; i += 400)); do
    git --literal-pathspecs --git-dir="$m" archive --format=tar HEAD -- "${paths[@]:i:400}" | tar -x -C "$dest"
  done
  # size cap (media must never end up here; the mirror already holds it)
  while IFS= read -r -d '' big; do
    log "export: left out (over $(human "$MAX_EXPORT_BYTES")): ${big#"$EXPORT"/}"
    printf '%s\ttoo-large\n' "${big#"$EXPORT"/}" >>"$EXPORT/SKIPPED.txt"
    rm -f -- "$big"
  done < <(find "$dest" -type f -size +"${MAX_EXPORT_BYTES}"c -print0)
  drop_secret_files "$dest"
  f=$(find "$dest" -type f | wc -l)
  printf '%s\tHEAD %s\t%s files exported\n' "$name" "${head:0:12}" "$f" >>"$EXPORT/MANIFEST.txt"
  log "export $name: $f files from HEAD ${head:0:12}"
}

export_all() {
  STEP="exporting text files"
  rm -rf "$EXPORT"
  mkdir -p "$EXPORT"
  : >"$EXPORT/SKIPPED.txt"
  printf 'exported at %s from the mirrors (git archive of HEAD, no checkout)\n' "$(ts)" >"$EXPORT/MANIFEST.txt"
  local e name
  for e in $REPOS; do
    name=${e%%|*}
    [[ -d $GITDIR/$name.git ]] && export_repo "$name"
  done
}

# ---------------------------------------------------------------- snapshots

snapshot_names() { # complete snapshots, oldest first: YYYY-MM-DD, plus YYYY-MM-DD_HHMM for extra same-day runs
  find "$SNAPDIR" -mindepth 1 -maxdepth 1 -type d -regextype posix-extended -regex '.*/[0-9]{4}-[0-9]{2}-[0-9]{2}(_[0-9]{4})?' -printf '%f\n' | sort
}

make_snapshot() {
  STEP="taking the snapshot"
  check_floor "$GB" "snapshot"
  local name tmp prev e n d
  name=$(dubai_date)
  # a second run the same Dubai day (a full run) never replaces the night's
  # snapshot: it would lose the refs the first one still holds
  if [[ -d $SNAPDIR/$name ]]; then name=${name}_$(TZ=Asia/Dubai date +%H%M); fi
  tmp=$SNAPDIR/.incomplete-$name
  prev=$(snapshot_names | tail -n 1 || true)
  rm -rf "$tmp"
  mkdir -p "$tmp/refs"
  # Git files are immutable once written (gc is off), so the snapshot hard-links
  # them to the live mirror: a point-in-time view that costs only the new files.
  rsync -a --link-dest="$GITDIR/" \
    --exclude='FETCH_HEAD' --exclude='gc.log' --exclude='*.lock' --exclude='/.*.partial' \
    "$GITDIR/" "$tmp/git/"
  # Small exports link against the previous snapshot, unchanged files cost nothing.
  rsync -a ${prev:+--link-dest="$SNAPDIR/$prev/export/"} "$EXPORT/" "$tmp/export/"
  for e in $REPOS; do
    n=${e%%|*}
    d=$GITDIR/$n.git
    [[ -d $d ]] || continue
    git --git-dir="$d" for-each-ref --format='%(objectname) %(refname)' >"$tmp/refs/$n.txt"
  done
  {
    printf 'snapshot %s taken %s (mode %s)\n' "$name" "$(ts)" "$MODE"
    for e in $REPOS; do
      n=${e%%|*}
      [[ -d $GITDIR/$n.git ]] &&
        printf '%s HEAD %s, %s refs\n' "$n" "$(git --git-dir="$GITDIR/$n.git" rev-parse -q --verify HEAD || echo none)" "$(wc -l <"$tmp/refs/$n.txt")"
    done
  } >"$tmp/MANIFEST.txt"
  rm -rf "${SNAPDIR:?}/$name"
  mv "$tmp" "$SNAPDIR/$name"
  log "snapshot $name written"
}

prune_snapshots() { # keep every snapshot of the newest $KEEP Dubai days
  STEP="pruning old snapshots"
  local all n d
  local -a days=() keep=()
  find "$SNAPDIR" -mindepth 1 -maxdepth 1 -type d -name '.incomplete-*' -exec rm -rf {} + 2>/dev/null || true
  mapfile -t all < <(snapshot_names)
  mapfile -t days < <(printf '%s\n' "${all[@]:-}" | cut -c1-10 | sort -u)
  n=${#days[@]}
  if ((n > KEEP)); then
    keep=("${days[@]:n-KEEP}")
    for d in "${all[@]}"; do
      if ! printf '%s\n' "${keep[@]}" | grep -qx "${d:0:10}"; then
        rm -rf "${SNAPDIR:?}/$d"
        log "pruned snapshot $d"
      fi
    done
  fi
}

# ---------------------------------------------------------------- config repo

sync_units() { # copy changed unit files from the repo to ~/.config/systemd/user
  local u changed=0
  [[ $SELF_DIR == "$CONFIG_REPO"/* ]] || return 0
  mkdir -p "$UNIT_DIR"
  for u in "${UNITS[@]}"; do
    if [[ -f $SELF_DIR/$u ]] && ! cmp -s "$SELF_DIR/$u" "$UNIT_DIR/$u"; then
      cp -f "$SELF_DIR/$u" "$UNIT_DIR/$u"
      changed=1
      log "unit $u updated from the repo"
    fi
  done
  if ((changed)); then
    systemctl --user daemon-reload 2>/dev/null || log "note: systemctl --user daemon-reload failed"
    systemctl --user try-restart dxb-backup.timer dxb-backup-check.timer 2>/dev/null || true
  fi
}

self_update() {
  STEP="updating the config repo"
  if [[ ${DXB_BACKUP_SELF_UPDATE:-on} == off ]]; then return 0; fi
  if [[ ! -d $CONFIG_REPO/.git ]]; then
    log "config repo $CONFIG_REPO not found, skipping pull"
    return 0
  fi
  if timeout 300 git -C "$CONFIG_REPO" pull -q --ff-only >>"$LOG" 2>&1; then
    log "config repo pulled"
    sync_units
  else
    log "WARNING: git pull of $CONFIG_REPO failed; carrying on with the scripts on disk"
  fi
}

# ---------------------------------------------------------------- modes

write_heartbeat() { # write_heartbeat <summary>
  local now
  now=$(date +%s)
  printf '%s\n' "$now" >"$STATE/last-success-epoch.tmp" && mv "$STATE/last-success-epoch.tmp" "$STATE/last-success-epoch"
  printf '%s\n' "$(ts)" >"$STATE/last-success"
  dubai_date >"$STATE/last-success-date"
  printf '%s\n' "$1" >"$STATE/last-success-info"
  rm -f "$STATE/last-skip"
}

mode_nightly() { # also "full" with FORCE=1
  local force=${1:-0} e name url gb
  need_tools
  mkdir -p "$GITDIR" "$SNAPDIR" "$STATE"
  exec 9>"$STATE/lock"
  if ! flock -n 9; then
    OUTCOME=noop
    log "another backup run holds the lock; nothing to do"
    exit 0
  fi
  if [[ $force == 0 && -f $STATE/last-success-date && $(<"$STATE/last-success-date") == "$(dubai_date)" ]]; then
    OUTCOME=noop
    log "tonight's backup already succeeded ($(<"$STATE/last-success")); nothing to do"
    exit 0
  fi
  if [[ -f $LOG && $(stat -c %s "$LOG") -gt 2097152 ]]; then
    tail -n 5000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  fi
  log "=== $MODE start ==="
  setup_git_auth
  STEP="waiting for the render server to be idle"
  wait_idle || skip_busy
  self_update
  check_floor 0 "start"

  for e in $REPOS; do
    IFS='|' read -r name url gb <<<"$e"
    STEP="waiting for the render server to be idle ($name)"
    wait_idle || skip_busy
    mirror_one "$name" "$url" "${gb:-5}"
  done

  export_all
  make_snapshot
  prune_snapshots

  STEP="summary"
  local n_snap used avail msg secs
  n_snap=$(snapshot_names | wc -l)
  used=$(du -sb "$ROOT" | awk '{print $1}')
  avail=$(avail_bytes "$ROOT")
  secs=$((SECONDS - T_START))
  msg="$MODE $(dubai_date): $(wc -w <<<"$REPOS") mirrors, $n_snap snapshots, $(human "$used") used, $(human "$avail") free, $((secs / 60))m$((secs % 60))s"
  write_heartbeat "$msg"
  OUTCOME=ok
  log "OK: $msg"
  notify "dxb-render-1 backup OK" "$msg" low white_check_mark || true
}

mode_heartbeat_check() {
  MODE=heartbeat-check
  mkdir -p "$STATE"
  local now last base note age_h
  now=$(date +%s)
  if [[ -f $STATE/last-success-epoch ]]; then
    last=$(<"$STATE/last-success-epoch")
    note="last success $(<"$STATE/last-success")"
  elif [[ -f $STATE/installed-at ]]; then
    last=$(<"$STATE/installed-at")
    note="no backup has succeeded since install"
  else
    last=0
    note="no backup has ever succeeded and no install time is recorded"
  fi
  base=$last
  age_h=$(((now - base) / 3600))
  if ((now - base > STALE_H * 3600)); then
    OUTCOME=alert
    log "ALERT: $note; ${age_h} h ago (limit ${STALE_H} h)"
    notify "dxb-render-1 backup MISSED" "No successful backup mirror for ${age_h} h (limit ${STALE_H} h): $note. Check ~dxbbackup/mirror/state/backup.log." high warning
    exit 1
  fi
  OUTCOME=ok
  log "heartbeat ok: $note (${age_h} h ago)"
}

mode_restore_test() {
  local repo=${1:-dxb-queue} m c0 fsck_rc=0 head_m head_c res=PASS t0=$SECONDS
  m=$GITDIR/$repo.git
  [[ -d $m ]] || { echo "restore-test: no mirror at $m (run nightly first)"; OUTCOME=failed; exit 1; }
  mkdir -p "$STATE"
  SCRATCH=$(mktemp -d "$STATE/restore-test.XXXXXX")
  echo "restore-test: repo=$repo source=$m ($(du -sh "$m" | cut -f1) on disk)"
  c0=$SECONDS
  git clone -q --no-hardlinks "file://$m" "$SCRATCH/$repo"
  echo "clone: $((SECONDS - c0)) s, $(git -C "$SCRATCH/$repo" ls-files | wc -l) files checked out, $(du -sh "$SCRATCH/$repo" | cut -f1) with working tree"
  c0=$SECONDS
  git -C "$SCRATCH/$repo" fsck --full --no-dangling >"$SCRATCH/fsck.out" 2>&1 || fsck_rc=$?
  echo "fsck --full: exit $fsck_rc in $((SECONDS - c0)) s"
  if [[ -s $SCRATCH/fsck.out ]]; then sed 's/^/  fsck: /' "$SCRATCH/fsck.out" | head -n 10; fi
  ((fsck_rc == 0)) || res=FAIL
  head_m=$(git --git-dir="$m" rev-parse HEAD)
  head_c=$(git -C "$SCRATCH/$repo" rev-parse HEAD)
  if [[ $head_m == "$head_c" ]]; then echo "HEAD: clone and mirror agree (${head_m:0:12})"; else echo "HEAD: MISMATCH clone ${head_c:0:12} mirror ${head_m:0:12}"; res=FAIL; fi
  if diff <(git --git-dir="$m" for-each-ref --format='%(objectname) %(refname:strip=2)' refs/heads | sort) \
    <(git -C "$SCRATCH/$repo" for-each-ref --format='%(objectname) %(refname:strip=3)' refs/remotes/origin | grep -v ' HEAD$' | sort) >/dev/null; then
    echo "branches: all $(git --git-dir="$m" for-each-ref refs/heads | wc -l) branches match"
  else
    echo "branches: MISMATCH between clone and mirror"
    res=FAIL
  fi
  local snap
  snap=$(snapshot_names 2>/dev/null | tail -n 1 || true)
  if [[ -n $snap && -d $SNAPDIR/$snap/git/$repo.git ]]; then
    if [[ $(git --git-dir="$SNAPDIR/$snap/git/$repo.git" rev-parse HEAD 2>/dev/null) == "$head_m" ]]; then
      echo "snapshot $snap: holds the same HEAD"
    else
      echo "snapshot $snap: HEAD differs from the mirror (older snapshot, or a newer fetch since)"
    fi
  fi
  echo "restore-test $res: $repo, $((SECONDS - t0)) s in all"
  printf '%s %s %s %ss\n' "$(ts)" "$repo" "$res" "$((SECONDS - t0))" >"$STATE/last-restore-test"
  [[ $res == PASS ]]
}

mode_status() {
  local e n d snap last
  echo "dxb-backup status ($(ts))"
  echo "root:        $ROOT"
  echo "free disk:   $(human "$(avail_bytes "$(dirname "$ROOT")")") (floor ${FLOOR_GB} GB)"
  if [[ -d $ROOT ]]; then echo "used by all: $(du -sh "$ROOT" 2>/dev/null | cut -f1) (hard links counted once)"; fi
  if busy; then echo "render:      ACTIVE (a nightly run would wait)"; else echo "render:      idle"; fi
  for e in $REPOS; do
    n=${e%%|*}
    d=$GITDIR/$n.git
    if [[ -d $d ]]; then
      echo "mirror $n: $(du -sh "$d" | cut -f1), HEAD $(git --git-dir="$d" rev-parse -q --verify HEAD 2>/dev/null | cut -c1-12), $(git --git-dir="$d" for-each-ref | wc -l) refs"
    else
      echo "mirror $n: not cloned yet"
    fi
  done
  if [[ -d $SNAPDIR ]]; then
    echo "snapshots:   $(snapshot_names | wc -l) (keeps $KEEP days): $(snapshot_names | tr '\n' ' ')"
  fi
  last=none
  [[ -f $STATE/last-success ]] && last="$(<"$STATE/last-success") ($(<"$STATE/last-success-info"))"
  echo "last success: $last"
  [[ -f $STATE/last-run ]] && echo "last run:     $(<"$STATE/last-run")"
  [[ -f $STATE/last-restore-test ]] && echo "restore test: $(<"$STATE/last-restore-test")"
  [[ -r $TOKEN_FILE ]] && echo "token file:   readable" || echo "token file:   NOT readable ($TOKEN_FILE)"
  [[ -r $TOPIC_FILE ]] && echo "ntfy topic:   file readable" || echo "ntfy topic:   file NOT readable ($TOPIC_FILE)"
  systemctl --user list-timers 'dxb-backup*' --no-pager 2>/dev/null || true
}

usage() {
  sed -n '2,18p' "$SELF" | sed 's/^# \{0,1\}//'
}

main() {
  MODE=${1:-}
  case $MODE in
    nightly | full | heartbeat-check | restore-test | status) ;;
    -h | --help | help | "") usage; exit 0 ;;
    *) echo "unknown mode: $MODE" >&2; usage >&2; exit 2 ;;
  esac
  trap on_exit EXIT
  mkdir -p "$STATE"
  case $MODE in
    nightly) mode_nightly 0 ;;
    full) mode_nightly 1 ;;
    heartbeat-check) mode_heartbeat_check ;;
    restore-test) mode_restore_test "${2:-dxb-queue}" ;;
    status) mode_status ;;
  esac
}

main "$@"
