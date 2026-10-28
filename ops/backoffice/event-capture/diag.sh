#!/bin/bash
# Event capture diagnosis (Mohammad, 28 Oct 2026, after the Indie World shadow test read 0 frames).
# 1. The reader error lines from that test's capture.log (streamlink, yt-dlp, ffmpeg stderr; our own note lines left out).
# 2. streamlink and yt-dlp upgraded to the latest in the runner venv; Node put in the runner's home if yt-dlp asks for
#    a JavaScript runtime (no root, nothing system-wide).
# 3. One live YouTube stream and one live Twitch stream, each read for 60 s: frames saved at 1 fps, frames decoded at
#    the stream's own rate, and any bot or sign-in block YouTube shows. Test frames are deleted at the end.
# Posts nothing, commits nothing, uploads nothing, uses no secret. Env: VENV, CACHE.
set -u
R="$RUNNER_TEMP/diag"; mkdir -p "$R"; S="$GITHUB_STEP_SUMMARY"
say() { echo "$*"; echo "$*" >> "$S"; }
block() { echo '```' >> "$S"; cat >> "$S"; echo '```' >> "$S"; }

say "## 1. capture.log from the Indie World test"
LOGF="$CACHE/event-capture/2026-10-28-indie-world/capture.log"
if [ -f "$LOGF" ]; then
  say "Lines: $(wc -l < "$LOGF"). Reader errors (not our own HH:MM:SSZ notes), by count:"
  grep -vE '^[0-9]{2}:[0-9]{2}:[0-9]{2}Z ' "$LOGF" | sed -E 's/[0-9a-f]{16,}/<id>/g' | sort | uniq -c | sort -rn | head -40 | block
  say "First 25 error lines in order, with the note line before each run:"
  grep -nE -B1 -v '^[0-9]{2}:[0-9]{2}:[0-9]{2}Z ' "$LOGF" | head -25 | block
else
  say "capture.log not found at $LOGF"
fi

say "## 2. Tools"
{ echo "before: streamlink $("$VENV/bin/streamlink" --version 2>&1 | tail -1); yt-dlp $("$VENV/bin/yt-dlp" --version 2>&1)"; } | block
"$VENV/bin/python" -m pip install -q --timeout 90 -U pip >/dev/null 2>&1
"$VENV/bin/python" -m pip install -q --timeout 120 -U streamlink "yt-dlp[default]" 2>&1 | tail -5 | block
{ echo "after: streamlink $("$VENV/bin/streamlink" --version 2>&1 | tail -1); yt-dlp $("$VENV/bin/yt-dlp" --version 2>&1)"
  echo "node on PATH: $(command -v node || echo none); deno: $(command -v deno || echo none); ffmpeg: $(ffmpeg -version 2>&1 | head -1)"; } | block

# Live YouTube candidates: official channels that stream around the clock.
YTS=(https://www.youtube.com/@NASA/live https://www.youtube.com/@lofigirl/live https://www.youtube.com/@SkyNews/live https://www.youtube.com/@aljazeeraenglish/live)
yt_try() {  # $1 url, $2 extra args; prints the stream URL on stdout, stderr to $R/yt.err
  timeout 90 "$VENV/bin/yt-dlp" -v -g -f 'best[height<=1080]' $2 "$1" 2>"$R/yt.err" | head -1
}
JS=""; YT=""; YTU=""
for u in "${YTS[@]}"; do YTU="$u"; YT=$(yt_try "$u" ""); [ -n "$YT" ] && break; done
NEEDJS=no
grep -qiE 'javascript runtime|js runtime|No supported JavaScript|--js-runtimes|n challenge|nsig' "$R/yt.err" && NEEDJS=yes
say "### YouTube, before Node: $( [ -n "$YT" ] && echo "stream URL from $YTU" || echo "no stream URL" ); asks for a JS runtime: $NEEDJS"
grep -iE 'error|warning|sign in|bot|runtime|challenge|429|403' "$R/yt.err" | sed -E 's#https?://[^ ]*googlevideo[^ ]*#<url>#g' | sort | uniq -c | head -20 | block
if [ "$NEEDJS" = yes ] || [ -z "$YT" ]; then
  if [ ! -x "$HOME/node/bin/node" ]; then
    ver=$(curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | grep -oE 'node-v[0-9.]+-linux-x64\.tar\.xz' | head -1)
    curl -fsSL "https://nodejs.org/dist/latest-v22.x/$ver" -o "$R/node.tar.xz" \
      && curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | grep " $ver\$" | sed "s# $ver\$# $R/node.tar.xz#" | sha256sum -c - \
      && mkdir -p "$HOME/node" && tar -xJf "$R/node.tar.xz" -C "$HOME/node" --strip-components=1
  fi
  say "Node in the runner's home: $("$HOME/node/bin/node" --version 2>&1 || echo 'install failed') at $HOME/node/bin/node"
  JS="--js-runtimes node:$HOME/node/bin/node"
  for u in "${YTS[@]}"; do YTU="$u"; YT=$(yt_try "$u" "$JS"); [ -n "$YT" ] && break; done
  say "### YouTube, with Node: $( [ -n "$YT" ] && echo "stream URL from $YTU" || echo "no stream URL" )"
  grep -iE 'error|warning|sign in|bot|runtime|challenge|429|403' "$R/yt.err" | sed -E 's#https?://[^ ]*googlevideo[^ ]*#<url>#g' | sort | uniq -c | head -20 | block
fi
BOT=$(grep -ciE "sign in to confirm|not a bot|confirm you.re not|LOGIN_REQUIRED" "$R/yt.err")
say "YouTube bot or sign-in block lines in the last attempt: $BOT"

# Live Twitch: the top live stream right now (Twitch's public web query, the same one streamlink uses), plus Nintendo.
TW=$(curl -fsS -m 20 -H 'Client-ID: kimne78kx3ncx6brgo4mv6wki5h1ko' -H 'Content-Type: application/json' \
      -d '{"query":"query{streams(first:3){edges{node{broadcaster{login} game{name} viewersCount}}}}"}' https://gql.twitch.tv/gql \
      | "$VENV/bin/python" -c 'import sys,json; e=json.load(sys.stdin)["data"]["streams"]["edges"]; print(e[0]["node"]["broadcaster"]["login"]); print(" | ".join("%s (%s, %s viewers)"%(x["node"]["broadcaster"]["login"],(x["node"]["game"] or {}).get("name"),x["node"]["viewersCount"]) for x in e), file=sys.stderr)' 2>"$R/tw.top")
say "### Twitch live now: $(cat "$R/tw.top")"
timeout 60 "$VENV/bin/streamlink" --twitch-disable-ads https://www.twitch.tv/nintendo 2>&1 | tail -3 | sed 's/^/nintendo: /' | block

measure() {  # $1 label, $2 reader command (writes MPEG-TS to stdout)
  d="$R/$1"; mkdir -p "$d"; t0=$(date +%s.%N)
  timeout 70 bash -c "$2" 2>"$d/reader.err" | timeout 65 nice -n 19 ffmpeg -hide_banner -nostdin -progress "$d/prog.txt" -t 60 -i pipe:0 \
      -map 0:v:0 -vf fps=1 -q:v 3 "$d/f-%03d.jpg" -map 0:v:0 -f null - 2>"$d/ff.err"
  t1=$(date +%s.%N); jpg=$(ls "$d"/f-*.jpg 2>/dev/null | wc -l)
  dec=$(grep -oE '^frame=[0-9]+' "$d/prog.txt" 2>/dev/null | tail -1 | cut -d= -f2)
  info=$(grep -m1 -oE 'Video: [^,]+, [^,]+, [0-9]+x[0-9]+[^,]*, [^,]*fps' "$d/ff.err" || grep -m1 -oE 'Video: .*' "$d/ff.err" | cut -c1-120)
  wall=$(python3 -c "print(round($t1-$t0,1))")
  say "**$1**: ${jpg} frames saved at 1 fps over ${wall} s ($(python3 -c "print(round($jpg/$wall,2))") fps saved); ${dec:-0} frames decoded ($(python3 -c "print(round(${dec:-0}/$wall,1))") fps); stream: ${info:-unknown}"
  { tail -3 "$d/reader.err"; grep -iE 'error|invalid|denied|403' "$d/ff.err" | head -3; } | block
  rm -f "$d"/f-*.jpg
}
say "## 3. Live reads from the server (60 s each)"
if [ -n "$YT" ]; then
  measure youtube "ffmpeg -hide_banner -loglevel error -nostdin -i '$YT' -c copy -f mpegts pipe:1"
  measure youtube-ytdlp-pipe "'$VENV/bin/yt-dlp' -q $JS -f 'best[height<=1080]' -o - '$YTU'"
else
  say "**youtube**: no stream URL, nothing to read"
fi
if [ -n "$TW" ]; then
  measure "twitch-$TW" "'$VENV/bin/streamlink' --stdout --twitch-disable-ads https://www.twitch.tv/$TW best"
else
  say "**twitch**: no live channel found"
fi
say "Disk: $(df -h "$CACHE" | tail -1)"
