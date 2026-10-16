"""Reel formats and the format ledger (Mohammad, 10 Oct 2026).

Every Digital Lounge Reel is one of these formats, chosen in its creative
brief before the shot sheet. No more than two Reels in a row share a format
unless the story demands it; the ledger keeps the order they went out in.

    python3 formats.py                      # the last ten, newest last
    python3 formats.py check numbers        # a third in a row, or a third card-led Reel in six?
    python3 formats.py add <reel name> trailer
    python3 formats.py views <reel name> 1840   # weekly Instagram views next to the template (Tuesday, 14 Oct 2026)
    python3 formats.py templates                # median views per template
"""
import json, os, sys

FORMATS = {
    'trailer':   'official footage runs the whole Reel with its own sound; the lines ride on the picture; no card (the default when a trailer exists)',
    'split':     'footage runs the whole Reel with a slim pinned fact strip (date, price, platforms; 2 or 3 items) low in the safe zone; the lines never repeat the strip (reel(..., strip=[...]), 14 Oct 2026)',
    'clipcard':  'footage for the hook and story, ONE card at the key beat (price table, date, figure), then footage again; the card holds its beat alone or under a one-line frame',
    'numbers':   'our own graphics on the living ground for the whole Reel, only when no footage shows the news: sales charts, results, rankings',
    'comparison': 'two states with labels and hard cuts: prices by country, specs, before and after (reel(..., cut=True))',
    'quote':     "the speaker's line leads, in «» right after the headline; then footage of what they talked about",
    'explainer': "the source's own figures or screens step by step (patents, features, store pages)",
    'handson':   'his gameplay: natural colours, text after the action, numbered tips',
    'retro':     'on this day: the game on a real CRT photo, fact sheet then «هل تعلم؟» facts (retro_tv, 10 Oct 2026)',
    'edition':   'special and collector\'s editions, bundles, limited consoles, accessories, tier contents: trailer hook, each item as a press-render cut-out drifting onto the living ground, one composition frame with the price strip, footage close (edition.py, 14 Oct 2026)',
    'stills':    'three or four official images filling 9:16, cut not panned (subject cut-outs on a parallax ground where the art allows, else a 2 to 4% push-in), hard cuts on the bed, 3 s each, 12 to 14 s, four lines, neighbouring images differ in kind; the last resort after every motion source (reel.stills_clips, advisor 14 Oct 2026)',
    'list':      'N items at 2 to 2.5 s each on their own art, rank or date on a small plate, progress cue n/N, one line per item at most, mosaic cover, closing frame of all tiles: Game Pass waves, leaving-soon, line-ups, awards, top fives, show recaps, weekly releases (advisor 14 Oct 2026)',
}
#: `tribute` is a variant of stills (reel(..., tribute=True)): cold, wave lines off, no chip, name and dates as the headline, lines
#: in body grey, slow dissolves, calm bed, end card with the mark and no jingle. `عاجل` is a skin on any template, not a kind:
#: crimson theme and the breaking bed (reel.py applies it from the chip).
SKINS = {'عاجل': dict(theme='crimson', sound='breaking')}
#: Templates outside the 12 to 20 s length target (advisor, 14 Oct 2026): every other template states its total in the brief.
LENGTH_EXEMPT = ('handson', 'edition')
#: No template more than DAY_MAX times in one day, any family (advisor, 14 Oct 2026).
DAY_MAX = 4
#: A closing question line is allowed only on stories readers argue about (advisor, 14 Oct 2026), never on launches or prices.
QUESTION_ALLOWED = ('controversy', 'reviews', 'quote', 'layoffs', 'policy', 'remake', 'adaptation', 'report', 'business')
#: The `arabic` kind's strip items, as they apply to the story.
ARABIC_STRIP = ('الواجهة', 'الترجمة', 'الدبلجة')
TEMPLATES = FORMATS

# The opening beat per template (advisor, 14 Oct 2026): what is on screen in the first second, under the chip and the
# hook headline. The footage moves from frame one; the credit line enters at 2 s (reel.CREDIT_AT).
OPENERS = {
    'trailer':    'the strongest shot of the stretch, moving from frame one, the headline over it',
    'split':      'the footage moving from frame one; the strip pins when the headline leaves',
    'clipcard':   'the footage hook, moving; the card comes only at the key beat',
    'numbers':    'the number alone, large, on the living ground; the chart builds after it',
    'comparison': 'the first state with its label; the second state is the cut',
    'quote':      'the quote itself in «», over the speaker or the thing they spoke of; the portrait never holds the whole Reel',
    'explainer':  "the source's first figure or screen, the part the story turns on ringed",
    'handson':    'the action, his play, before any text',
    'retro':      'the game running on the CRT, the date over it',
    'edition':    'the hero item: the trailer hook with the headline, then the hero cut-out first and largest',
    'stills':     'the strongest image, already pushing in, the headline over it; the first cut lands with the first line',
    'list':       'the mosaic of every item, the count in the headline; item 1 on the first cut',
}


def opener(fmt):
    return OPENERS.get(fmt, '')

# Two families (advisor, 14 Oct 2026): footage-led Reels run the picture the whole way; card-led Reels put our graphics,
# figures or a portrait on screen. Besides "no third in a row", card-led Reels are at most one in three over the last six.
FAMILIES = {
    'footage': ('trailer', 'split', 'clipcard', 'handson', 'stills'),
    'card':    ('numbers', 'explainer', 'quote', 'retro', 'edition', 'list'),
}
FAMILY = {fmt: fam for fam, fmts in FAMILIES.items() for fmt in fmts}
FAMILY['comparison'] = 'footage'   # two labelled states of the footage or store screens, hard cuts
WINDOW, CARD_MAX = 6, 2            # at most CARD_MAX card-led Reels in any WINDOW consecutive Reels

# Which templates fit which kind of news (Mohammad, 14 Oct 2026: "various reel templates and scenarios and which templates can
# be used with the type of news"). First is the default; the rest are the alternatives when the first would be a third in a row
# or the footage does not exist. A story with a trailer never starts from a card template.
NEWS_MAP = {
    'launch':        ['trailer', 'split'],            # out now, with a trailer; split when the price or platforms matter
    'date':          ['split', 'trailer'],            # a release date or an event date and time
    'reveal':        ['trailer'],                      # an announcement with footage
    'update':        ['trailer', 'clipcard'],         # a patch or a feature; clipcard when the patch notes are the point
    'price':         ['split', 'clipcard', 'comparison'],   # store prices, discounts, editions
    'sales':         ['numbers', 'clipcard'],         # sales figures, charts, rankings
    'business':      ['quote', 'explainer', 'numbers'],     # studios, deals, results, people
    'quote':         ['quote'],                        # someone said something
    'report':        ['trailer', 'clipcard'],         # a report or rumour on the game's footage; a card only when the claim has a figure or a table (advisor, 14 Oct)
    'hardware':      ['explainer', 'split'],          # devices, specs
    'event':         ['split', 'explainer'],          # a show, a tournament, a date card
    'handson':       ['handson'],
    'anniversary':   ['retro'],
    'edition':       ['edition', 'split'],            # a collector's or special edition, bundle, limited console, accessory, tier contents
    # Batch 1 (advisor, 14 Oct 2026, approved)
    'delay':         ['split', 'trailer'],
    'preorder':      ['split'],
    'free':          ['split'],                       # free weekends, giveaways, free-to-play switches
    'shutdown':      ['split', 'explainer'],
    'reviews':       ['clipcard', 'numbers'],
    'awards':        ['list'],
    'esports':       ['split', 'numbers'],
    'controversy':   ['quote', 'clipcard'],
    'recap':         ['list'],                        # show recaps
    'weekly':        ['list'],                        # the week's releases
    'gamepass':      ['list'],                        # Game Pass and PS Plus waves, store line-ups
    'lineup':        ['list'],
    'top':           ['list'],                        # top fives and rankings told as a list
    'adaptation':    ['trailer', 'stills'],           # film and TV of a game
    'mods':          ['trailer'],                     # with the stand-in credit naming the creator; the creator's permission when the footage is theirs
    'hardware_price': ['comparison'],
    'arabic':        ['split'],                       # Arabic support: strip items from ARABIC_STRIP as they apply, chip «بالعربية» beside the news chip
    # Batch 2 (advisor, 14 Oct 2026, approved)
    'layoffs':       ['quote', 'stills'],
    'acquisition':   ['explainer'],
    'results':       ['numbers'],
    'players':       ['split'],                       # player counts and milestones
    'policy':        ['explainer'],
    'leaving':       ['list'],                        # leaving Game Pass or PS Plus
    'crossover':     ['trailer'],
    'expansion':     ['split'],
    'beta':          ['split'],
    'crossplay':     ['comparison'],
    'performance':   ['comparison'],
    'remake':        ['comparison', 'trailer'],
    'rating_leak':   ['clipcard'],                    # re-checked right before queuing
    'firmware':      ['explainer'],
    'format':        ['explainer'],                   # a new format, service or feature explained
    'cast':          ['quote'],
    'soundtrack':    ['edition', 'split'],
    'community_record': ['handson'],                  # permission and on-screen credit required
    'watch_guide':   ['split'],                       # times in Gulf time
    'breach':        ['explainer'],                   # عاجل skin only on official confirmation; never methods or third-party claims
}
# Judgement rules, not templates (advisor, 14 Oct 2026): bans and censorship carry the official decision and the publisher's
# response only, no commentary, chip رسمي or تقرير; regional investment and government programmes take the business templates,
# the country chip only when the country is the story. The scenario for every kind (cover, where the facts live, key shot and
# reason, sound) is on the advisor canvas "Digital Lounge Reel Templates", board "Scenarios by news kind"; a brief starts from it.
JUDGEMENT = {
    'ban':        'official decision and publisher response only; no commentary; chip رسمي or تقرير',
    'investment': 'business templates (quote, explainer, numbers); country chip only when the country is the story',
}


def pick(kind, facts=None):
    """The template for a kind of news: its first choice unless the ledger refuses it (a third in a row, a third
    card-led Reel in six, or a fifth of the day). `facts` is the brief's item count: a price story with more than three
    facts can never be split (advisor, 14 Oct 2026)."""
    opts = list(NEWS_MAP[kind])
    if kind == 'price' and facts is not None and facts > 3:
        opts = [f for f in opts if f != 'split'] or ['clipcard']
    for fmt in opts:
        if not check(fmt):
            return fmt
    return opts[0]
LEDGER = os.path.join(os.path.dirname(__file__), 'assets', 'format-ledger.json')


def _load():
    try:
        return json.load(open(LEDGER))
    except (OSError, ValueError):
        return []


def add(name, fmt):
    if fmt not in FORMATS:
        raise ValueError(f'{fmt}: not a format ({", ".join(FORMATS)})')
    led = _load()
    old = next((e for e in led if e['name'] == name), {})
    led = [e for e in led if e['name'] != name]   # a re-render keeps its place and its views
    import datetime
    at = old.get('at') or datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')   # a re-render keeps its day
    led.append({'name': name, 'format': fmt, 'at': at, **({'views': old['views']} if 'views' in old else {})})
    json.dump(led[-200:], open(LEDGER, 'w'), indent=1)


def views(name, n):
    """Weekly views next to the template (advisor, 14 Oct 2026): Mohammad sends the numbers on Tuesday morning before the
    audit; `analytics/reel-views.md` says how they are read. Instagram's count for the Reel, as an integer."""
    led = _load()
    hit = [e for e in led if e['name'] == name]
    if not hit:
        raise ValueError(f'{name}: not in the format ledger')
    hit[0]['views'] = int(n)
    json.dump(led, open(LEDGER, 'w'), indent=1)


def by_template():
    """Median and count of the views recorded per template, newest 200 Reels."""
    import statistics
    seen = {}
    for e in _load():
        if 'views' in e:
            seen.setdefault(e['format'], []).append(e['views'])
    return {f: (statistics.median(v), len(v)) for f, v in seen.items()}


def _at(e):
    import datetime
    try:
        return datetime.datetime.strptime(e.get('at', '')[:16], '%Y-%m-%dT%H:%M')
    except ValueError:
        return None


def _dubai(t):
    import datetime
    return t + datetime.timedelta(hours=4)


def check(fmt, at=None):
    """Why fmt should not be next, or '' when it may: a third in a row, (card-led) a third card-led Reel in the
    last six (at most one in three), or a fifth of one template in the same Dubai day (constant coverage, 16 Oct
    2026: the day is Dubai's, not UTC's). `at` (UTC, 'YYYY-MM-DDTHH:MM') is the slot the Reel would take; the
    ledger is read in time order up to it, so a Reel moved into an earlier slot is checked where it lands."""
    import datetime
    t = datetime.datetime.strptime(at[:16], '%Y-%m-%dT%H:%M') if at else datetime.datetime.utcnow()
    before = sorted((e for e in _load() if _at(e) and _at(e) < t), key=_at)
    led = [e['format'] for e in before]
    last = led[-2:]
    if len(last) == 2 and all(f == fmt for f in last):
        return f'third {fmt} in a row'
    if FAMILY.get(fmt) == 'card':
        recent = led[-(WINDOW - 1):]
        cards = [f for f in recent if FAMILY.get(f) == 'card']
        if len(cards) >= CARD_MAX:
            return f'card-led would be {len(cards) + 1} of the last {len(recent) + 1} ({", ".join(cards)}); at most {CARD_MAX} in {WINDOW}'
    day = _dubai(t).date()
    n = sum(1 for e in _load() if e['format'] == fmt and _at(e) and _dubai(_at(e)).date() == day)
    if n >= DAY_MAX:
        return f'{fmt} already {n} times on Dubai day {day}; at most {DAY_MAX} a day, any family'
    return ''


#: Constant coverage (advisor, 16 Oct 2026; Mohammad: "I want constant coverage"). No daily cap; spacing and gaps
#: in Dubai time, by the hour of the later post: at least SPACING minutes between posts and never more than
#: MAX_GAP minutes without one; day is 08:00 to 24:00, night 00:00 to 08:00. Breaking news may break the spacing.
SPACING = {'day': 30, 'night': 60}
MAX_GAP = {'day': 60, 'night': 120}


def _band(t):
    return 'night' if _dubai(t).hour < 8 else 'day'


def gaps(hours=2, start=None):
    """Spacing and gap problems from `start` (UTC, default now) to `hours` ahead, from the ledger's slots. Each is
    one line (Dubai times). The hourly watch runs it and says so in its commit (gap alarm)."""
    import datetime
    t0 = datetime.datetime.strptime(start[:16], '%Y-%m-%dT%H:%M') if start else datetime.datetime.utcnow()
    t1 = t0 + datetime.timedelta(hours=hours)
    slots = sorted({_at(e) for e in _load() if _at(e)})
    prev = max([x for x in slots if x <= t0], default=None)
    out, cur = [], prev
    for x in [x for x in slots if t0 < x <= t1] + [t1]:
        if cur is not None:
            mins = (x - cur).total_seconds() / 60
            band, gband = _band(x), _band(cur)       # spacing by the later post's hour, the gap by where it starts
            d0, d1 = _dubai(cur).strftime('%H:%M'), _dubai(x).strftime('%H:%M')
            if x != t1 and mins < SPACING[band]:
                out.append(f'spacing: {d0} to {d1} Dubai is {mins:.0f} min ({band} minimum {SPACING[band]})')
            if mins > MAX_GAP[gband]:
                end = 'end of window' if x == t1 else f'{d1}'
                out.append(f'gap: nothing from {d0} to {end} Dubai, {mins:.0f} min ({gband} maximum {MAX_GAP[gband]})')
        cur = x
    return out


def family(fmt):
    return FAMILY.get(fmt, '?')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['add']:
        add(a[1], a[2]); print('ok')
    elif a[:1] == ['views']:                       # python3 formats.py views <reel name> <instagram views>
        views(a[1], a[2]); print('ok')
    elif a[:1] == ['templates']:                   # views per template, for the Tuesday audit
        for f, (med, n) in sorted(by_template().items(), key=lambda kv: -kv[1][0]):
            print(f'{f:<10} median {med:>8,.0f} views over {n} Reels')
    elif a[:1] == ['gaps']:                        # python3 formats.py gaps [hours] [start UTC]: the gap alarm
        g = gaps(float(a[1]) if len(a) > 1 else 2, a[2] if len(a) > 2 else None)
        print('\n'.join(g) if g else 'ok')
    elif a[:1] == ['check']:                       # python3 formats.py check <fmt> [slot UTC]
        why = check(a[1], a[2] if len(a) > 2 else None)
        print(f'{why}: pick another unless the story demands it' if why else 'ok')
        print(f'opens on: {opener(a[1])}')
    else:
        for e in _load()[-10:]:
            v = f"{e['views']:>7,}" if 'views' in e else '      -'
            print(f"{e['format']:<10} {family(e['format']):<7} {v}  {e['name']}")
