#!/bin/bash
# Daily disk cleanup for the session container (Mohammad, 7 Oct 2026).
# Usage: disk_cleanup.sh [--dry-run]
# Removes only what can be fetched or rebuilt again:
#   1. render temp folders left in /tmp (older than 2 hours)
#   2. scratchpad working folders untouched for 3 days (tools kept)
#   3. source footage and audio in uploads untouched for 3 days
#      (images, fonts and his own recordings kept)
#   4. dxb-queue git history: re-cloned shallow when .git passes 1 GB
#      (posted video lives on in GitHub and the Reels in dxb-assets)
# Stops without deleting anything while a render or a publish is running.
set -u
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
LOG=()
rmx() { local sz; sz=$(du -sm "$1" 2>/dev/null | cut -f1); LOG+=("${sz:-0}M $1"); [ $DRY = 1 ] || rm -rf "$1"; }

before=$(df -m / | awk 'NR==2{print $4}')

if pgrep -f 'reel|render|ffmpeg|demucs|sales_full|outro|whisper' >/dev/null; then
  echo "skipped: a render is running"; pgrep -af 'reel|render|ffmpeg|demucs' | cut -c1-100; exit 0
fi

# 1. /tmp render leftovers
for d in $(find /tmp -maxdepth 1 -mindepth 1 -type d -mmin +120 \
    \( -name 'dlsubs*' -o -name 'dxbfast*' -o -name 'full*' -o -name 'short*' \
       -o -name 'reel*' -o -name 'outro*' -o -name 'ig*' -o -name 'tmp*' \
       -o -name 'photos*' -o -name 'snap*' \)); do rmx "$d"; done

# 2. scratchpad working folders
KEEP='^(tts|plug|arabic-skill|fonts|stubs|pipdl|clone|voice|voice2)$'
for S in /tmp/claude-0/*/*/scratchpad; do
  [ -d "$S" ] || continue
  for d in "$S"/*/; do
    d=${d%/}; n=$(basename "$d")
    [[ $n =~ $KEEP ]] && continue
    [ -z "$(find "$d" -newermt '3 days ago' -print -quit 2>/dev/null)" ] && rmx "$d"
  done
done

# 3. uploads: fetched footage and audio only
U=/mnt/user-data/uploads
if [ -d $U ]; then
  while IFS= read -r f; do rmx "$f"; done < <(find $U -type f -mtime +2 \
    \( -iname '*.mp4' -o -iname '*.webm' -o -iname '*.ts' -o -iname '*.mkv' \
       -o -iname '*.mov' -o -iname '*.m4a' -o -iname '*.wav' -o -iname '*.m3u8' \) \
    ! -iname '*voice*' ! -iname '*read*' ! -iname '*capture*' ! -iname '*gameplay*' \
    ! -iname '*yolo*' ! -iname '*mohammad*' ! -iname '*phone*')
fi

# 4. dxb-queue shallow re-clone
Q=/home/user/dxb-queue
if [ -d $Q/.git ] && [ "$(du -sm $Q/.git | cut -f1)" -gt 1024 ]; then
  run=$(gh api "repos/mohdeltayer/dxb-queue/actions/runs?per_page=3" --jq '[.workflow_runs[]|select(.status!="completed")]|length' 2>/dev/null)
  git -C $Q fetch -q origin main 2>/dev/null
  if [ "${run:-1}" != "0" ]; then echo "dxb-queue: publish run in progress, re-clone skipped"
  elif [ -n "$(git -C $Q status --porcelain)" ] || [ "$(git -C $Q rev-list --count origin/main..HEAD)" != "0" ]; then
    echo "dxb-queue: local changes or unpushed commits, re-clone skipped"
  else
    url=$(git -C $Q remote get-url origin)
    LOG+=("$(du -sm $Q/.git | cut -f1)M $Q/.git (shallow re-clone)")
    if [ $DRY = 0 ]; then
      git clone -q --depth 1 --branch main "$url" $Q.new && rm -rf $Q && mv $Q.new $Q \
        || { echo "dxb-queue re-clone failed; old clone kept"; rm -rf $Q.new; }
    fi
  fi
fi

after=$(df -m / | awk 'NR==2{print $4}')
printf '%s\n' "${LOG[@]}" | sort -rn | head -40
echo "items: ${#LOG[@]}  dry-run: $DRY  free before: ${before}M  after: ${after}M"
