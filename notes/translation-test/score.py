"""Score engine outputs against set.json. usage: score.py <engine>=<outputs.json> ...  (outputs: {id: arabic})"""
import json, re, sys, os
D = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f'{D}/set.json'))
def grade(item, ar):
    if item['fail'] and re.search(item['fail'], ar): return 'FAIL'
    if item['pass'] and re.search(item['pass'], ar): return 'PASS'
    return 'PASS' if not item['pass'] else 'MISS'
cols = [a.split('=', 1) for a in sys.argv[1:]]
outs = {n: json.load(open(p)) for n, p in cols}
tot = {n: {'PASS': 0, 'FAIL': 0, 'MISS': 0} for n in outs}
print('| test | ' + ' | '.join(outs) + ' |\n|---|' + '---|' * len(outs))
for it in S:
    row = []
    for n, o in outs.items():
        g = grade(it, o.get(it['id'], '')); tot[n][g] += 1; row.append(g)
    print(f"| {it['id']} | " + ' | '.join(row) + ' |')
print()
for n, t in tot.items(): print(f"{n}: {t['PASS']} pass, {t['FAIL']} fail, {t['MISS']} miss (neither term) of {len(S)}")
