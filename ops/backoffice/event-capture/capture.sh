#!/bin/bash
# Event capture shadow test (adv-20261028-event-capture, Mohammad 28 Oct 2026). Reads a live show stream directly
# (no browser, no login) and saves one frame per second plus scene-cut frames to a folder on the server for the
# build desk. Posts nothing, commits nothing, uploads nothing, OCRs nothing. Low priority (nice 19, ionice idle).
# Env: TWITCH_URL, YT_URL, START_UTC (HH:MM), END_UTC (HH:MM), SWITCH_UTC (HH:MM: no frames from Twitch by then,
#      switch to YouTube), OUT (folder), VENV (python venv with streamlink and yt-dlp).
set -u
mkdir -p "$OUT/fps" "$OUT/cuts"; LOG="$OUT/capture.log"; : > "$LOG"
note() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$LOG"; }
secs_to() { echo $(( $(date -u -d "today $1" +%s) - $(date -u +%s) )); }
w=$(secs_to "$START_UTC"); [ "$w" -gt 0 ] && { note "waiting ${w}s for $START_UTC"; sleep "$w"; }
src=twitch; n=0
while [ "$(secs_to "$END_UTC")" -gt 5 ]; do
  left=$(secs_to "$END_UTC")
  fps_n=$(ls "$OUT/fps" | wc -l)
  if [ "$src" = twitch ] && [ "$fps_n" -eq 0 ] && [ "$(secs_to "$SWITCH_UTC")" -le 0 ]; then
    src=youtube; note "no frames from Twitch by $SWITCH_UTC: switching to YouTube"
  fi
  n=$((n+1)); start=$(printf '%05d' $(( fps_n + 1 )))
  note "attempt $n source $src (${left}s left, frames so far $fps_n)"
  ff=(nice -n 19 ionice -c3 ffmpeg -hide_banner -loglevel error -nostdin -i pipe:0
      -map 0:v:0 -vf fps=1 -q:v 3 -start_number "$start" "$OUT/fps/$src-%05d.jpg"
      -map 0:v:0 -vf "select='gt(scene,0.35)',scale=1280:-2" -fps_mode vfr -q:v 3 -start_number "$start" "$OUT/cuts/$src-$n-%05d.jpg")
  if [ "$src" = twitch ]; then
    timeout "$left" "$VENV/bin/streamlink" --stdout --twitch-disable-ads "$TWITCH_URL" best 2>>"$LOG" | timeout "$left" "${ff[@]}" 2>>"$LOG"
  else
    hls=$(timeout 60 "$VENV/bin/yt-dlp" -q --no-warnings -g -f 'best[height<=1080]' "$YT_URL" 2>>"$LOG" | head -1)
    if [ -n "$hls" ]; then
      timeout "$left" nice -n 19 ffmpeg -hide_banner -loglevel error -nostdin -i "$hls" -c copy -f mpegts pipe:1 2>>"$LOG" | timeout "$left" "${ff[@]}" 2>>"$LOG"
    else
      note "yt-dlp gave no stream URL"
    fi
  fi
  note "reader ended (exit ${PIPESTATUS[*]:-?})"
  [ "$(secs_to "$END_UTC")" -gt 20 ] && sleep 15
done
fps_n=$(ls "$OUT/fps" | wc -l); cut_n=$(ls "$OUT/cuts" | wc -l)
note "done: $fps_n frames at 1 fps, $cut_n scene-cut frames, attempts $n, last source $src, folder $OUT, $(du -sh "$OUT" | cut -f1)"
