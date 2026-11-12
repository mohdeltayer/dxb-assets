"""Job scaffold (adv-20261110-one-render-per-reel, item D, Mohammad 10 Nov 2026).

On 10 Nov trailer and split were at their daily cap, so the Warhammer Survivors Reel became a clipcard and the session had
to read how a card shot is declared. This writes a job that is valid in shape for the template `formats.pick` returns,
the card shot and its ground included, so the session fills only the headline, the lines, the strip or card values and
the chip, and never writes a job's structure by hand.

    python3 templates/t0make.py <kind> <name> --story <story id> --source "<Arabic source>" \
        --trailer steam:<appid>:<trailer name prefix> | --trailer <https url> \
        [--shots shots.json] [--theme cold] [--label "متوفر الآن"] [--date "10 Nov 2026"] [--out jobs/live/<name>.json]

<kind> is a formats.NEWS_MAP kind (launch, date, reveal, price, report, delay, ...). --shots is the prerender `shots`
mode's output (shotpick.py): up to SHOTS clean stretches spread through the trailer in source order, each with its
focus. Without it the job carries no shots and says to run the shots mode first. Every text the session must write is
TODO, which the text rules refuse (a Latin-first line), so a scaffold can never render unfilled.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SHOTS = 7
CARD_SECS = 3.0
CARD_LED = ('numbers', 'explainer', 'quote', 'edition', 'list', 'reviewscores')
WITH_CARD = ('clipcard',) + CARD_LED
LABEL = {'launch': 'متوفر الآن', 'delay': 'تأجيل', 'price': 'السعر', 'report': 'تقرير', 'leak': 'تسريب',
         'rumour': 'شائعة', 'reviews': 'التقييمات', 'results': 'أرقام', 'update': 'تحديث'}
TODO = 'TODO'


def _footage(trailer, name):
    m = re.match(r'^steam:(\d+):(.+)$', trailer or '')
    if m:
        return {'file': f'{name}-trailer.mp4', 'steam': int(m.group(1)), 'trailer': m.group(2), 'start': 0, 'seconds': 240}
    if (trailer or '').startswith('https://'):
        return {'file': f'{name}-trailer.mp4', 'url': trailer}
    raise SystemExit('t0make: --trailer is steam:<appid>:<trailer name prefix> or an https url')


def _spread(stretches, n):
    """n stretches spread evenly through the list (already in source order)."""
    if len(stretches) <= n:
        return stretches
    step = (len(stretches) - 1) / (n - 1)
    return [stretches[round(i * step)] for i in range(n)]


def make(kind, name, story, source, trailer, shots_json=None, theme='cold', label=None, date=None):
    import formats
    if kind not in formats.NEWS_MAP:
        raise SystemExit(f't0make: kind {kind!r}: one of {", ".join(sorted(formats.NEWS_MAP))}')
    sf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'newsroom', 'stories', f'{story}.json')
    st = json.load(open(sf, encoding='utf-8')) if story and os.path.exists(sf) else {}
    if story and 'subject_person' not in st:
        raise SystemExit(f't0make: the story file needs "subject_person": null, or {{"name", "role", "photo_source"}} '
                         f'when a person is the subject ({sf}; adv-20261111-person-stories-gate)')
    sp = st.get('subject_person')
    import buildgate
    try:
        template = formats.pick(kind, footage=True, single_game=buildgate.single_game(st) or bool(sp))
    except ValueError as e:
        raise SystemExit(f't0make: {e}')
    foot = _footage(trailer, name)
    f = foot['file']
    shots, note = [], None
    if shots_json:
        data = json.load(open(shots_json, encoding='utf-8'))
        rows = data[0] if isinstance(data, list) else data
        picked = _spread(rows.get('shots') or [], SHOTS)
        shots = [[f, s['start'], s['secs'], [[0.0, s['focus']]]] for s in picked]
    else:
        note = 'no shots: run prerender.yml with mode shots on this job, then t0make again with --shots'
    gfx = []
    card_at = None
    if template in WITH_CARD and shots:
        card_at = min(3, len(shots))                       # after the hook and the story, before the payoff
        card = f'{name}-gfx-1.png'
        shots.insert(card_at, [card, None, CARD_SECS, None])
        gfx.append({'file': card, 'kind': 'fact', 'label': TODO, 'value': TODO, 'note': TODO})
    n = len(shots)
    foot_idx = [i for i, s in enumerate(shots) if not str(s[0]).endswith('.png')]
    lines = []
    for i in foot_idx[1:]:                                 # shot 0 carries the headline; one beat per footage shot after it
        lines.append([i, i, [TODO]])
    credits = []
    if foot_idx:                                           # every footage shot carries the source credit (30 Oct rule)
        runs, start = [], foot_idx[0]
        for a, b in zip(foot_idx, foot_idx[1:] + [None]):
            if b != a + 1:
                runs.append((start, a)); start = b
        credits = [[a, b, f'المصدر: {source}', {'size': 40, 'band': True}] for a, b in runs]
    job = {
        'name': name, 'story': story, 'kind_news': kind, 'built_by': 'production-2', 'render_lane': 'server',
        'out': f'cards/{dt.date.today():%Y-%m}/{name}-reel-v1.mp4',
        'footage': [foot], 'shots': shots, 'lines': lines, 'credits': credits,
        'headline': TODO, 'label': label or LABEL.get(kind, 'جديد'), 'source': source,
        'date': date or dt.date.today().strftime('%-d %b %Y'), 'theme': theme, 'style': None,
        'template': template, 'skin': 'house', 'cut': False,
        'track': [f, shots[foot_idx[0]][1]] if foot_idx else 'bed',
    }
    if sp or kind in buildgate.PERSON_KINDS:              # people stories show the person on frame 0 (23 Oct, 11 Nov)
        job['subject_person'] = sp
        job['person'] = [[TODO + ' (photo file in footage, or their best-known work with person_photo none)',
                          (sp or {}).get('name') or TODO, (sp or {}).get('role') or TODO, 0.0, 3.5,
                          {'credit': TODO}]]
    if template == 'split':
        job['strip'] = [[TODO, TODO], [TODO, TODO]]
    if gfx:
        job['gfx'] = gfx
        job['ground_footage'] = [f, shots[foot_idx[min(1, len(foot_idx) - 1)]][1]]
    if note:
        job['_todo'] = note
    return job, template, note


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    kind, name = argv[0], argv[1]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    if not re.match(r'^[a-z0-9][a-z0-9-]{2,120}$', name):
        raise SystemExit('t0make: name in lowercase letters, digits and dashes')
    for k in ('--story', '--source', '--trailer'):
        if k not in argv:
            raise SystemExit(f't0make: {k} is required')
    job, template, note = make(kind, name, opt('--story'), opt('--source'), opt('--trailer'), opt('--shots'),
                               opt('--theme', 'cold'), opt('--label'), opt('--date'))
    out = opt('--out', f'jobs/live/{name}.json')
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    json.dump(job, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(out, 'a').write('\n')
    print(f't0make: {out}: template {template}, {len(job["shots"])} shots'
          + (f', card at shot {next(i for i, s in enumerate(job["shots"]) if str(s[0]).endswith(".png"))}' if job.get('gfx') else ''))
    if note:
        print('t0make: ' + note)
    print('t0make: fill every TODO (headline, lines, ' + ('strip, ' if job.get('strip') else '')
          + ('card, ' if job.get('gfx') else '') + 'label if needed), then python3 templates/textrules.py ' + out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
