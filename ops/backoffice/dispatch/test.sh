#!/usr/bin/env bash
# test.sh: the dispatcher on synthetic cards and evidence, in a throw-away DISPATCH_HOME, with
# DISPATCH_NTFY=off (messages are printed, nothing is sent) and DISPATCH_MIRROR_FILE (no network).
# Touches nothing outside the temp folder. Exit 0 when every assertion holds.
#   ops/backoffice/dispatch/test.sh
set -uo pipefail
HERE=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
TMP=$(mktemp -d "${TMPDIR:-/tmp}/dxb-dispatch-test.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
D="$HERE/dispatch.py"
export PYTHONDONTWRITEBYTECODE=1
PY=${DISPATCH_PYTHON:-python3}

export DISPATCH_HOME=$TMP/home DISPATCH_NTFY=off DISPATCH_MIRROR_FILE=$TMP/mirror.json
export DISPATCH_EVIDENCE_FILE=$TMP/ev.json DISPATCH_TOKEN_FILE=$TMP/token DISPATCH_TOPIC_FILE=$TMP/topic
SECRET_TOKEN=ghp_TESTSECRETabcdef0123456789
SECRET_TOPIC=testtopicsecretxyz987
printf '%s\n' "$SECRET_TOKEN" >"$TMP/token"
printf '%s\n' "$SECRET_TOPIC" >"$TMP/topic"

pass=0; fail=0
ok()   { pass=$((pass + 1)); echo "ok   $1"; }
bad()  { fail=$((fail + 1)); echo "FAIL $1"; }
has()  { if grep -qF -- "$2" <<<"$1"; then ok "$3"; else bad "$3 (missing: $2)"; fi; }
hasnt() { if grep -qF -- "$2" <<<"$1"; then bad "$3 (found: $2)"; else ok "$3"; fi; }

# --- fixtures: python writes mirror.json and ev.json for a stage -----------------------------
cat >"$TMP/fx.py" <<'PYEOF'
import json, sys
stage, gen = sys.argv[1], sys.argv[2]
def card(i, frm, kind, status, title, created, answer=None, **kw):
    c = {'id': i, 'from': frm, 'to': None, 'kind': kind, 'title': title, 'status': status, 'created_at': created,
         'updated_at': None, 'answer_at': answer, 'answer_choice': 'Approve' if answer else None,
         'picked_up_at': None, 'progress': None, 'has_outcome': False, 'desk': None, 'late_at': None}
    c.update(kw)
    return c
P, A = 'production', 'advisor'
cards = [
    card('prod-t-ops-late', P, 'approval', 'answered', 'Post the Alpha story', '2026-10-28T09:00:00Z', '2026-10-28T11:20:00Z'),
    card('prod-t-ops-fresh', P, 'approval', 'answered', 'Post the Beta story', '2026-10-28T09:00:00Z', '2026-10-28T11:45:00Z'),
    card('prod-t-commit', P, 'approval', 'answered', 'Post the Gamma story', '2026-10-28T09:00:00Z', '2026-10-28T10:00:00Z'),
    card('prod-t-pickedup', P, 'approval', 'answered', 'Post the Delta story', '2026-10-28T09:00:00Z', '2026-10-28T10:00:00Z', picked_up_at='2026-10-28T10:10:00Z'),
    card('prod-t-progress', P, 'approval', 'answered', 'Post the Epsilon story', '2026-10-28T09:00:00Z', '2026-10-28T10:00:00Z', progress='building', updated_at='2026-10-28T10:15:00Z'),
    card('prod-t-staleprogress', P, 'approval', 'answered', 'Post the Zeta story', '2026-10-28T09:00:00Z', '2026-10-28T10:00:00Z', progress='old note', updated_at='2026-10-28T09:00:00Z'),
    card('prod-t-outcome', P, 'approval', 'answered', 'Post the Eta story', '2026-10-28T09:00:00Z', '2026-10-28T10:00:00Z', has_outcome=True, updated_at='2026-10-28T10:30:00Z'),
    card('adv-t-build-late', A, 'approval', 'open', 'New template for the render pipeline', '2026-10-27T10:00:00Z', to='production'),
    card('adv-t-build-fresh', A, 'approval', 'open', 'New template for the render pipeline, part two', '2026-10-28T01:00:00Z', to='production'),
    card('prod-t-done', P, 'approval', 'done', 'Post the Theta story', '2026-10-27T09:00:00Z', '2026-10-27T10:00:00Z', has_outcome=True),
    card('adv-t-done-old', A, 'approval', 'done', 'Post the Iota story', '2026-10-27T09:00:00Z', to='production'),
    card('prod-t-open', P, 'decision', 'open', 'Kappa preview: yes or no?', '2026-10-28T11:50:00Z'),
    card('adv-t-backlog', A, 'approval', 'open', 'Post the Lambda story', '2026-10-10T09:00:00Z', to='production'),
    card('prod-t-seen', P, 'fyi', 'answered', 'Morning digest', '2026-10-28T08:00:00Z', '2026-10-28T08:30:00Z', answer_choice='Seen'),
]
if stage == 'more':
    cards.append(card('adv-t-new-ops', A, 'approval', 'open', 'Post the Mu story', '2026-10-28T13:00:00Z', to='production'))
    cards.append(card('prod-t-new-you', P, 'decision', 'open', 'Nu preview: yes or no?', '2026-10-28T13:00:00Z'))
json.dump({'generated_at': gen, 'cards': cards}, open(sys.argv[3], 'w'))
json.dump({'commits': [
    {'repo': 'dxb-assets', 'sha': 'abc1234def5678', 'at': '2026-10-28T10:20:00Z', 'subject': 'Gamma story built (prod-t-commit)'},
    {'repo': 'dxb-assets', 'sha': '9999999aaaaaaa', 'at': '2026-10-28T09:50:00Z', 'subject': 'before the answer: prod-t-ops-late'},
    {'repo': 'dxb-queue', 'sha': '7777777bbbbbbb', 'at': '2026-10-28T11:30:00Z', 'subject': 'prod-t-ops-late-v2 is a different id'},
], 'runs': [{'name': 'render.yml', 'display_title': 'render prod-t-commit', 'head_sha': 'abc1234def5678', 'status': 'completed', 'conclusion': 'success'}]},
    open(sys.argv[4], 'w'))
PYEOF
fx() { "$PY" "$TMP/fx.py" "$1" "$2" "$TMP/mirror.json" "$TMP/ev.json"; }

NOW=2026-10-28T12:00:00Z

echo "== desk inference"
"$PY" -I - "$HERE" <<'PYEOF' && ok "desk inference" || bad "desk inference"
import sys
sys.path.insert(0, sys.argv[1])
import dispatch as d
def adv(t, kind='approval', to='production'): return {'from': 'advisor', 'kind': kind, 'to': to, 'title': t, 'status': 'answered'}
def prod(t, status): return {'from': 'production', 'kind': 'approval', 'to': 'mohammad', 'title': t, 'status': status}
cases = [
    (adv('Three desks and a 04:00 release window: ops (news only), build desk (nightly), dispatcher (script)'), 'build'),
    (adv("Post today as a rumour: 'Switch 2 Lite could use Samsung's new 8LPU+ chip process'"), 'ops'),
    (adv('Series: الطريق إلى Ocarina of Time, 8 daily episodes 29 Oct to 5 Nov, story-beat template, built now'), 'ops'),
    (adv('Back office on dxb-render-1: watch, monitoring, analytics, prepared trailers'), 'build'),
    (adv('Build until Thursday: pre-render checks, T0 breaking path, urgency tiers, T2/T3 quality profile'), 'build'),
    (adv('T0 now: Nintendo Indie World Showcase, Wed 28 Oct 18:00 Dubai'), 'ops'),
    (adv("Standing rule: answer the 'why' and the 'what happens to me' on every Reel"), 'build'),
    (adv('Which skin for the new pilot?', 'decision', 'Mohammad'), 'mohammad'),
    (adv('Which skin for the new pilot?', 'decision', 'production'), 'build'),
    (prod('Preview: Indie World reminder, 17:00 Dubai tomorrow', 'open'), 'mohammad'),
    (prod('Preview: Indie World reminder, 17:00 Dubai tomorrow', 'answered'), 'ops'),
    (prod('Back office 1, mechanical watch: built and tested; go live on dxb-render-1?', 'answered'), 'build'),
    (dict(prod('Anything', 'open'), desk='ops'), 'ops'),
    (dict(adv('Post the story'), desk='build'), 'build'),
    (dict(adv('Which skin?', 'decision', 'mohammad'), desk='ops'), 'ops'),
]
bad = [(c['title'], want, d.infer_desk(c)) for c, want in cases if d.infer_desk(c) != want]
for b in bad: print('  desk mismatch:', b)
sys.exit(1 if bad else 0)
PYEOF

echo "== mirror keeps only the allowed fields"
mkdir -p "$TMP/items"
cat >"$TMP/items/prod-x-1.json" <<'JEOF'
{"from":"production","to":"mohammad","kind":"approval","title":"A title","status":"answered","created_at":"2026-10-28T01:00:00Z","body":"SECRETBODY","memo":"SECRETMEMO","link":"https://x","images":["a"],"video":"v","options":[{"label":"x"}],"outcome":"done it","answer":{"at":"2026-10-28T02:00:00Z","choice":"Go","note":"SECRETNOTE"},"desk":"Ops"}
JEOF
"$PY" "$D" mirror "$TMP/items" "$TMP/m-out.json" --now "$NOW" >/dev/null
out=$(cat "$TMP/m-out.json")
hasnt "$out" SECRET "mirror drops body, memo and notes"
hasnt "$out" '"link"' "mirror drops links"
has "$out" '"has_outcome": true' "mirror flags outcome without its text"
has "$out" '"desk": "ops"' "mirror keeps the desk"
"$PY" -I -c 'import json,sys; c=json.load(open(sys.argv[1]))["cards"][0]; want={"id","from","to","kind","title","status","created_at","updated_at","answer_at","answer_choice","picked_up_at","progress","has_outcome","desk","late_at"}; sys.exit(0 if set(c)==want and c["id"]=="prod-x-1" else 1)' "$TMP/m-out.json" && ok "mirror field set is exact" || bad "mirror field set is exact"

echo "== lateness (sample, no state)"
fx base 2026-10-28T11:30:00Z
s=$("$PY" "$D" sample --mirror "$TMP/mirror.json" --evidence "$TMP/ev.json" --now "$NOW")
has "$s" "prod-t-ops-late" "ops card 40 minutes old is late"
hasnt "$s" "prod-t-ops-fresh), due" "ops card 15 minutes old is not late"
has "$s" "prod-t-staleprogress" "progress older than the start does not count as pick-up"
has "$s" "adv-t-build-late" "build card is late after 00:00 UTC"
hasnt "$s" "adv-t-build-fresh), due" "build card made after 00:00 UTC is due the next day"
hasnt "$s" "prod-t-commit), due" "pick-up by commit subject"
hasnt "$s" "prod-t-pickedup), due" "pick-up by picked_up_at"
hasnt "$s" "prod-t-progress), due" "pick-up by progress and updated_at"
hasnt "$s" "prod-t-outcome), due" "pick-up by outcome"
hasnt "$s" "prod-t-done" "done cards never alert"
hasnt "$s" "adv-t-done-old" "done advisor cards never alert"
hasnt "$s" "adv-t-backlog), due" "cards older than the lookback are never alerted"
hasnt "$s" "prod-t-seen" "an FYI answered Seen asks nothing"
has "$s" "LATE ops: Post the Alpha story (prod-t-ops-late), due 15:50 Dubai" "late line format with the due time in Dubai"
has "$s" "Inbox: " "message title"
has "$s" "new for you" "sample treats every card as new (mohammad)"
has "$s" "new for ops" "sample treats every card as new (ops)"
hasnt "$s" "adv-t-build-late (new" "build cards get no new-card message"

echo "== lateness boundary: 30 minutes exactly is not late, 31 is"
s=$("$PY" "$D" sample --mirror "$TMP/mirror.json" --evidence "$TMP/ev.json" --now 2026-10-28T11:50:00Z)
hasnt "$s" "prod-t-ops-late), due" "ops not late at exactly 30 minutes"
s=$("$PY" "$D" sample --mirror "$TMP/mirror.json" --evidence "$TMP/ev.json" --now 2026-10-28T11:51:00Z)
has "$s" "prod-t-ops-late" "ops late at 31 minutes"
s=$("$PY" "$D" sample --mirror "$TMP/mirror.json" --evidence "$TMP/ev.json" --now 2026-10-27T23:59:00Z)
hasnt "$s" "adv-t-build-late), due" "build not late before 00:00 UTC"

echo "== plan and write-back"
"$PY" "$D" plan --mirror "$TMP/mirror.json" --evidence "$TMP/ev.json" --now "$NOW" --out "$TMP/plan" >/dev/null
q=$(cat "$TMP/plan/ops-queue.md"); b=$(cat "$TMP/plan/build-queue.md"); w=$(cat "$TMP/plan/writeback.json")
has "$q" "LATE | prod-t-ops-late" "ops queue lists the late card"
has "$q" "PICKED UP | prod-t-commit" "ops queue lists the picked-up card with evidence"
has "$q" "commit dxb-assets abc1234" "queue evidence names the commit"
has "$q" "run render.yml completed success" "queue evidence names the Actions run"
has "$q" "BACKLOG | adv-t-backlog" "old unpicked cards are listed as backlog"
hasnt "$q" "prod-t-done" "queue files skip done cards"
has "$b" "LATE | adv-t-build-late" "build queue lists the late card"
has "$b" "(04:00 Dubai" "build queue shows the Dubai due time"
"$PY" -I - "$TMP/plan/writeback.json" <<'PYEOF' && ok "write-back content" || bad "write-back content"
import json, sys
wb = {w['id']: w['fields'] for w in json.load(open(sys.argv[1]))}
c = wb['prod-t-commit']
assert c['picked_up_at'] == '2026-10-28T10:20:00Z', c
assert c['progress'].startswith('evidence: dxb-assets abc1234 '), c
assert c['desk'] == 'ops', c
assert wb['prod-t-ops-late']['late_at'] == '2026-10-28T11:50:00Z', wb['prod-t-ops-late']
assert 'picked_up_at' not in wb['prod-t-pickedup'], wb['prod-t-pickedup']   # it already has a valid one
assert 'progress' not in wb['prod-t-ops-late'] and 'picked_up_at' not in wb['prod-t-ops-late']
assert 'prod-t-open' not in wb, 'an open production card keeps no desk written down'
assert 'prod-t-done' not in wb and 'prod-t-seen' not in wb
assert wb['adv-t-build-late']['desk'] == 'build'
assert 'late_at' not in wb.get('adv-t-backlog', {}), 'backlog is not marked late'
PYEOF

echo "== tick: baseline, dedupe, new cards, stale mirror"
export DISPATCH_NOW=$NOW
fx base 2026-10-28T11:55:00Z
t1=$("$PY" "$D" tick); rc=$?
[[ $rc -eq 0 ]] && ok "tick exits 0" || bad "tick exits 0 (rc=$rc)"
has "$t1" "Inbox: " "first run still sends late alerts"
has "$t1" "prod-t-ops-late" "first run late alert names the card"
hasnt "$t1" "new for you" "baseline: no NEW for mohammad cards"
hasnt "$t1" "new for ops" "baseline: no NEW for ops cards"
[[ -s $DISPATCH_HOME/heartbeat ]] && ok "heartbeat written" || bad "heartbeat written"

export DISPATCH_NOW=2026-10-28T12:05:00Z
fx base 2026-10-28T12:00:00Z
t2=$("$PY" "$D" tick)
hasnt "$t2" "prod-t-ops-late" "same late card is not alerted again within the hour"
hasnt "$t2" "LATE" "no late message five minutes later"

export DISPATCH_NOW=2026-10-28T13:01:00Z
fx base 2026-10-28T13:00:00Z
t3=$("$PY" "$D" tick)
has "$t3" "prod-t-ops-late" "late card is alerted again after an hour"
has "$t3" "prod-t-ops-fresh" "a card that became late is added"

export DISPATCH_NOW=2026-10-28T13:05:00Z
fx more 2026-10-28T13:04:00Z
t4=$("$PY" "$D" tick)
has "$t4" "adv-t-new-ops" "new ops card is announced"
has "$t4" "Inbox: 1 new for ops" "new for ops title"
has "$t4" "prod-t-new-you" "new mohammad card is announced"
has "$t4" "Inbox: 1 new for you" "new for you title"
hasnt "$t4" "LATE" "late alerts stay quiet inside the hour"
export DISPATCH_NOW=2026-10-28T13:10:00Z
t5=$("$PY" "$D" tick)
hasnt "$t5" "new for" "a new card is announced once"

export DISPATCH_NOW=2026-10-28T13:20:00Z
fx more 2026-10-28T09:00:00Z
t6=$("$PY" "$D" tick)
has "$t6" "dispatcher: inbox mirror is 4 h old" "stale mirror alert"
export DISPATCH_NOW=2026-10-28T13:30:00Z
t7=$("$PY" "$D" tick)
hasnt "$t7" "dispatcher: inbox mirror" "stale alert at most once an hour"

echo "== a failed fetch still runs the stale check, and leaks nothing"
unset DISPATCH_MIRROR_FILE DISPATCH_EVIDENCE_FILE
export DISPATCH_API=http://127.0.0.1:9 DISPATCH_NOW=2026-10-28T14:25:00Z
t8=$("$PY" "$D" tick 2>&1); rc=$?
[[ $rc -eq 0 ]] && ok "failed fetch exits 0" || bad "failed fetch exits 0 (rc=$rc)"
has "$t8" "dispatcher: inbox mirror is 5 h old" "stale check runs when the fetch failed"
has "$(cat "$DISPATCH_HOME/dispatch.log")" "mirror fetch failed" "fetch failure is logged"
export DISPATCH_MIRROR_FILE=$TMP/mirror.json DISPATCH_EVIDENCE_FILE=$TMP/ev.json
unset DISPATCH_API

echo "== lock: a running pass blocks a second one"
(
  exec 9>"$DISPATCH_HOME/lock"
  flock -n 9 || exit 1
  export DISPATCH_NOW=2026-10-28T14:30:00Z
  "$PY" "$D" tick >/dev/null
  grep -q "previous pass is still running" "$DISPATCH_HOME/dispatch.log"
) && ok "overlapping pass is skipped" || bad "overlapping pass is skipped"

echo "== message cap: 12 lines and 'and N more'"
"$PY" -I - "$TMP/mirror-many.json" <<'PYEOF'
import json, sys
cards = [{'id': 'prod-many-%02d' % i, 'from': 'production', 'to': None, 'kind': 'approval', 'title': 'Post story %d' % i,
          'status': 'answered', 'created_at': '2026-10-28T08:00:00Z', 'updated_at': None, 'answer_at': '2026-10-28T09:00:00Z',
          'answer_choice': 'Approve', 'picked_up_at': None, 'progress': None, 'has_outcome': False, 'desk': None, 'late_at': None}
         for i in range(15)]
json.dump({'generated_at': '2026-10-28T11:55:00Z', 'cards': cards}, open(sys.argv[1], 'w'))
PYEOF
s=$("$PY" "$D" sample --mirror "$TMP/mirror-many.json" --now "$NOW")
has "$s" "Inbox: 15 late" "late title counts every card"
has "$s" "and 3 more" "late message is capped at 12 lines"
[[ $(grep -c '^LATE ops' <<<"$s") -eq 12 ]] && ok "exactly 12 late lines" || bad "exactly 12 late lines"

echo "== the real send path (a local stand-in for ntfy)"
cat >"$TMP/srv.py" <<'PYEOF'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n).decode('utf-8')
        with open(sys.argv[2], 'a', encoding='utf-8') as f:
            f.write('PATH %s\nTITLE %s\nPRIO %s\nTAGS %s\nBODY %s\n' % (self.path, self.headers.get('Title'), self.headers.get('Priority'), self.headers.get('Tags'), body))
        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
    def log_message(self, *a): pass
http.server.HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
PYEOF
PORT=$((20000 + RANDOM % 20000))
"$PY" "$TMP/srv.py" "$PORT" "$TMP/got.txt" & SRV=$!
sleep 1
fx base 2026-10-28T11:55:00Z
(
  export DISPATCH_HOME=$TMP/home2 DISPATCH_NTFY=on DISPATCH_NTFY_URL=http://127.0.0.1:$PORT DISPATCH_NOW=$NOW
  "$PY" "$D" tick >/dev/null
)
kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null
got=$(cat "$TMP/got.txt" 2>/dev/null)
has "$got" "PATH /$SECRET_TOPIC" "the topic goes in the URL path"
has "$got" "TITLE Inbox: " "the title goes in a header"
has "$got" "PRIO high" "late alerts are high priority"
has "$got" "prod-t-ops-late" "the body carries the lines"
hasnt "$(cat "$TMP/home2/dispatch.log")" "$SECRET_TOPIC" "the log of a real send has no topic"
grep -q "ntfy sent: Inbox: " "$TMP/home2/dispatch.log" && ok "the send is logged without its body" || bad "the send is logged"

echo "== status and secrets"
st=$("$PY" "$D" status); rc=$?
[[ $rc -eq 0 ]] && ok "status exits 0" || bad "status exits 0"
has "$st" "github token file: readable" "status reports the token file as readable"
has "$st" "ntfy topic file:   readable" "status reports the topic file as readable"
hasnt "$st" "$SECRET_TOKEN" "status never prints the token"
hasnt "$st" "$SECRET_TOPIC" "status never prints the topic"
leak=$(grep -rlF -e "$SECRET_TOKEN" -e "$SECRET_TOPIC" "$DISPATCH_HOME" "$TMP/home2" 2>/dev/null || true)
[[ -z $leak ]] && ok "no secret in the state, log or caches" || bad "secret found in: $leak"
"$PY" -I - "$HERE" "$SECRET_TOKEN" <<'PYEOF' && ok "scrubber removes token shapes and the exact value" || bad "scrubber"
import sys
sys.path.insert(0, sys.argv[1])
import dispatch as d
s = d.Scrubber('hidden-value-123')
t = s('HTTP 401 Bearer abc123 ghp_AAAA1111 github_pat_BBBB2222 and hidden-value-123 done')
assert 'abc123' not in t and 'ghp_AAAA' not in t and 'github_pat_BBBB' not in t and 'hidden-value-123' not in t, t
PYEOF
log=$(cat "$DISPATCH_HOME/dispatch.log")
hasnt "$log" "$SECRET_TOKEN" "log has no token"
hasnt "$log" "$SECRET_TOPIC" "log has no topic"

echo
echo "passed: $pass, failed: $fail"
[[ $fail -eq 0 ]]
