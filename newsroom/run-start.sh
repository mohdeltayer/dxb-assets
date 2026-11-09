#!/usr/bin/env bash
# Every hourly run, first three reads, then the digest head (audit faults 1, 2, 5; Mohammad 9 Nov 2026).
# 1 keeper line, 2 board (desk branch, last handoffs), 3 cards/index.json (dxb-queue main), 4 digest head sha and seq.
set -u
cd "$(git rev-parse --show-toplevel)"
echo "== run-start $(date -u +%Y-%m-%dT%H:%MZ)"
git fetch -q --depth 1 origin +keeper-status:refs/remotes/origin/keeper-status && git show origin/keeper-status:keeper/status.txt | head -2
Q=${DXBQ:-/tmp/dqm}
[ -d "$Q/.git" ] || git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/mohdeltayer/dxb-queue.git "$Q"
git -C "$Q" fetch -q --depth 1 origin +desk:refs/remotes/origin/desk +main:refs/remotes/origin/main
echo "-- board (last 5 handoff ids, unacknowledged to Production 2)"
git -C "$Q" show origin/desk:desk/board.json | python3 -c "
import json,sys;b=json.load(sys.stdin);h=b['handoffs'];print([x['id'] for x in h[-5:]])
u=[x['id'] for x in h if 'Production 2' in str(x.get('to')) and not x.get('acknowledged_by')];print('unacknowledged to Production 2:',len(u),u[:6])"
echo "-- cards/index.json"
git -C "$Q" show origin/main:cards/index.json | python3 -c "import json,sys;d=json.load(sys.stdin);print('generated',d.get('generated_at'),'count',d.get('count'))"
echo "-- digest head"
git fetch -q origin +watch-digest:refs/remotes/origin/watch-digest
LOCAL=$(git rev-parse origin/watch-digest); REMOTE=$(git ls-remote origin watch-digest | cut -f1)
echo "fetched head ${LOCAL:0:12}  ls-remote head ${REMOTE:0:12}  $([ "$LOCAL" = "$REMOTE" ] && echo MATCH || echo MISMATCH-refetch)"
git show origin/watch-digest:watch/digest.json | python3 -c "
import json,sys,datetime as d;x=json.load(sys.stdin);t=d.datetime.strptime(x['generated_at'],'%Y-%m-%dT%H:%M:%SZ');print('seq',x['seq'],'generated',x['generated_at'],'age_min',int((d.datetime.utcnow()-t).total_seconds()//60))"
