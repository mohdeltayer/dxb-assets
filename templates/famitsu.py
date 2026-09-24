"""Famitsu weekly Japan sales: parse Famitsu's own article, render two cards.

Famitsu posts the week's estimated physical sales (packages, download cards
and pre-installs) on famitsu.com, usually Thursday 22:00 JST (17:00 Dubai).
Holiday weeks move: the article ends with the next date ("次回は...に掲載予定").

    python3 templates/famitsu.py <this week url> <out-stem> <date> [last week url]

With last week's article the cards show week-on-week change: a percentage
for every hardware family and for every title that was in last week's top
10. Famitsu prints each title's previous rank but not its previous number,
so a title that climbed in from outside the top 10 shows its old rank.

Titles are translated through TITLES below. An unknown Japanese title stops
the run and names itself, so nothing goes out with a guessed English name:
add it (checked against the publisher's English name) and run again.
"""
import html
import re
import subprocess
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from PIL import Image, ImageDraw  # noqa: E402
import flex  # noqa: E402

# Japanese title as Famitsu prints it -> English title as the publisher uses it.
TITLES = {
    'リズム天国 ミラクルスターズ': 'Rhythm Heaven Groove',
    '鬼武者 Way of the Sword': 'Onimusha: Way of the Sword',
    'スプラトゥーン レイダース': 'Splatoon Raiders',
    'トモダチコレクション わくわく生活': 'Tomodachi Life: Living the Dream',
    '学校であった怖い話と晦-つきこもり': 'Kowai Hanashi & Tsukikomori',
    'Minecraft': 'Minecraft',
    'マリオカート ワールド': 'Mario Kart World',
    'ほの暮しの庭': 'Village in the Shade',
    '三國志14 with パワーアップキット Complete Edition':
        'Three Kingdoms XIV PK Complete Edition',
}

PLATFORMS = {'Switch2': 'NS2', 'Switch': 'NS', 'PS5': 'PS5', 'PS4': 'PS4',
             'XboxSeries': 'XBS'}

# Hardware lines grouped into families, in the order the card shows them.
FAMILIES = [
    ('Switch 2', ['Switch2']),
    ('Switch', ['Switch', 'Switch Lite', 'Switch（有機ELモデル）']),
    ('PS5', ['PS5', 'PS5 デジタル・エディション', 'PS5 Pro']),
    ('Xbox Series', ['Xbox Series X', 'Xbox Series X デジタルエディション',
                     'Xbox Series S']),
]
SHORT = {'Switch2': 'Switch 2', 'Switch（有機ELモデル）': 'OLED',
         'Switch Lite': 'Lite', 'Switch': 'Original',
         'PS5 デジタル・エディション': 'Digital', 'PS5 Pro': 'Pro',
         'PS5': 'Standard', 'Xbox Series X': 'Series X',
         'Xbox Series X デジタルエディション': 'Series X Digital',
         'Xbox Series S': 'Series S'}

# Week-on-week colours. Green is not in the sheet palette: up and down need
# to read at a glance, and every reader already knows green up, red down.
UP, DOWN = flex.hx('#3DDC97'), flex.ACCENTS['rose']

# The list cycle without rose: once red means "down", a red row or a red
# hardware number next to a green chip reads as a fall.
CYCLE = ('cyan', 'lavender', 'amber')


def jnum(s):
    """'100万45' -> 1000045, '96184' -> 96184."""
    s = s.replace(',', '')
    if '万' in s:
        hi, lo = s.split('万')
        return int(hi) * 10000 + (int(lo) if lo else 0)
    return int(s)


def fetch(url):
    raw = subprocess.run(['curl', '-sL', '-A', 'Mozilla/5.0', url],
                         capture_output=True, text=True, check=True).stdout
    body = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', '\n', body))
    return [ln.strip() for ln in text.split('\n') if ln.strip()]


def parse(lines):
    joined = '\n'.join(lines)
    period = re.search(r'集計期間は(\d+)年(\d+)月(\d+)日～(\d+)月(\d+)日', joined)
    nxt = re.search(r'次回は(\d+)月(\d+)日に掲載予定', joined)
    software = []
    for i, ln in enumerate(lines):
        m = re.match(r'(\d+)位（(.+?)）\s+(\S+)\s+(.+)$', ln)
        if not m:
            continue
        rank, prev, plat, jp = m.groups()
        week = jnum(re.match(r'([\d万]+)本', lines[i + 1]).group(1))
        life = jnum(re.search(r'累計([\d万]+)本', lines[i + 2]).group(1))
        was = re.match(r'前回(\d+)位', prev)
        software.append(dict(rank=int(rank), new=prev == '初登場', plat=plat,
                             jp=jp.strip(), week=week, life=life,
                             was=int(was.group(1)) if was else None))
    hardware = {}
    for ln in lines:
        m = re.match(r'(.+?)／(\d+)台（累計([\d万]+)台）', ln)
        if m:
            hardware[m.group(1)] = (int(m.group(2)), jnum(m.group(3)))
    return period, nxt, software, hardware


def english(jp):
    if jp not in TITLES:
        raise SystemExit(f'No English title for {jp!r}: add it to TITLES.')
    return TITLES[jp]


def families(hardware):
    out = []
    for name, keys in FAMILIES:
        models = [(k, *hardware[k]) for k in keys if k in hardware]
        if models:
            out.append((name, sum(m[1] for m in models), models))
    return out


def render(url, stem, date, prev_url=None, background='reported'):
    period, nxt, software, hardware = parse(fetch(url))
    y, m1, d1, m2, d2 = period.groups()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
              'Oct', 'Nov', 'Dec']
    def spanof(p):
        _, a, b, c, e = p.groups()
        return (f'{months[int(a) - 1]} {b}-{e}' if a == c else
                f'{months[int(a) - 1]} {b} to {months[int(c) - 1]} {e}')
    span = spanof(period)

    last_sw, last_hw, vs = {}, {}, None
    if prev_url:
        pperiod, _, psw, phw = parse(fetch(prev_url))
        last_sw = {(s['plat'], s['jp']): s['week'] for s in psw}
        last_hw = {name: week for name, week, _ in families(phw)}
        vs = spanof(pperiod)
    for s in software:
        s['last'] = last_sw.get((s['plat'], s['jp']))

    sub = f'{span}, {y} · physical + download cards'
    software_card(software, f'Software top 10 · {sub}', date,
                  f'{stem}-software.png', background, vs)
    hardware_card(hardware, last_hw, f'Hardware · {sub}', date,
                  f'{stem}-hardware.png', background, vs)
    return software, hardware, last_hw, nxt


def _canvas(header, subheader, background):
    bg, panel, panel2, edge = flex.ground(background)
    acc = flex.resolve('cold')
    im = Image.new('RGB', (flex.W, flex.H), bg)
    d = ImageDraw.Draw(im)
    flex.heading(d, header, subheader, 'stats', acc, bg)
    return im, d, bg, panel, panel2, edge, acc


def _fit(d, text, font, width):
    if d.textlength(text, font=font) <= width:
        return text
    while d.textlength(text + '...', font=font) > width:
        text = text[:-1]
    return text.rstrip() + '...'


def pct(now, before):
    return None if not before else round((now - before) * 100 / before)


def pill(d, x_right, cy, text, fill, ink, arrow=None, size=34):
    """A filled chip, right-aligned at x_right and centred on cy, with an
    optional drawn triangle (drawn, not a glyph, so no font can drop it).
    Returns the chip's left edge."""
    f = flex.F(size, 800)
    tw = d.textlength(text, font=f)
    tri = size * 0.62 if arrow else 0
    gap = 12 if arrow else 0
    w = 22 + tri + gap + tw + 22
    h = size + 22
    x0 = x_right - w
    d.rounded_rectangle([x0, cy - h / 2, x_right, cy + h / 2], radius=h / 2,
                        fill=fill)
    tx = x0 + 22
    if arrow:
        half = tri / 2
        top, bot = cy - tri * 0.45, cy + tri * 0.45
        pts = ([(tx, bot), (tx + tri, bot), (tx + half, top)] if arrow == 'up'
               else [(tx, top), (tx + tri, top), (tx + half, bot)])
        d.polygon(pts, fill=ink)
        tx += tri + gap
    d.text((tx, cy), text, font=f, fill=ink, anchor='lm')
    return x0


def change_pill(d, x_right, cy, change, bg, muted, size=34):
    if change is None:
        return None
    if change > 0:
        return pill(d, x_right, cy, f'{change}%', UP, bg, 'up', size)
    if change < 0:
        return pill(d, x_right, cy, f'{-change}%', DOWN, bg, 'down', size)
    return pill(d, x_right, cy, '0%', muted, bg, None, size)


def key(d, vs, bg, muted, extra=()):
    """The legend above the footer: what the chips are measured against.
    Arrows are drawn, like the chips, so no font can drop them."""
    F, M = flex.F, flex.M
    f = F(32, 600)
    cy, x, t = flex.H - 196, M, 26
    d.polygon([(x, cy + t * .45), (x + t, cy + t * .45), (x + t / 2, cy - t * .45)],
              fill=UP)
    x += t + 10
    d.polygon([(x, cy - t * .45), (x + t, cy - t * .45), (x + t / 2, cy + t * .45)],
              fill=DOWN)
    x += t + 18
    text = f'% change vs last week ({vs})'
    for mark, what in extra:
        text += f'  ·  {mark} {what}'
    d.text((x, cy), text, font=f, fill=muted, anchor='lm')


def software_card(software, subheader, date, out, background='reported',
                  vs=None):
    """Ten rows. Each carries a colour bar and rank in the list cycle, the
    week's number with the lifetime total under it, and, when last week is
    known, a change chip: the percentage for a title that was in last week's
    top 10, NEW for a debut, or its old rank for a climber from outside."""
    F, M, W = flex.F, flex.M, flex.W
    im, d, bg, panel, panel2, edge, acc = _canvas('Japan sales', subheader,
                                                  background)
    muted = flex.lift(flex.BODY, -0.30, bg)
    rf, pf, tf = F(48, 800), F(30, 700), F(46, 700)
    nf, lf = F(48, 800), F(30, 600)
    y, ROW, STEP = 380, 118, 128
    for i, s in enumerate(software[:10]):
        colour = flex.ACCENTS[CYCLE[i % len(CYCLE)]]
        d.rounded_rectangle([M, y, W - M, y + ROW], radius=16, fill=panel)
        d.rounded_rectangle([M + 18, y + 22, M + 28, y + ROW - 22], radius=5,
                            fill=colour)
        mid = y + ROW / 2
        d.text((M + 48, mid), f'{s["rank"]:02d}', font=rf, fill=colour,
               anchor='lm')
        d.text((M + 132, mid), PLATFORMS.get(s['plat'], s['plat']), font=pf,
               fill=muted, anchor='lm')

        chip_right = W - M - 290
        if s['new']:
            left = pill(d, chip_right, mid, 'NEW', acc, bg)
        elif vs and s['last']:
            left = change_pill(d, chip_right, mid, pct(s['week'], s['last']),
                               bg, muted)
        elif vs and s['was']:
            left = pill(d, chip_right, mid, f'was #{s["was"]}', panel2,
                        flex.BODY, 'up' if s['was'] > s['rank'] else 'down')
        else:
            left = None
        title_w = (left if left else W - M - 290) - (M + 236) - 30
        d.text((M + 236, mid), _fit(d, english(s['jp']), tf, title_w),
               font=tf, fill=flex.INK, anchor='lm')

        d.text((W - M - 30, mid - 18), f'{s["week"]:,}', font=nf,
               fill=flex.INK, anchor='rm')
        d.text((W - M - 30, mid + 30), f'{s["life"]:,} total', font=lf,
               fill=muted, anchor='rm')
        y += STEP
    if vs:
        extra = []
        if any(s['new'] for s in software[:10]):
            extra.append(('NEW', 'debut'))
        if any(not s['new'] and not s['last'] and s['was'] for s in software[:10]):
            extra.append(('was #', "last week's rank"))
        key(d, vs, bg, muted, extra)
    flex.footer(im, bg, 'Famitsu', date, edge).save(out)
    return out


def hardware_card(hardware, last, subheader, date, out, background='reported',
                  vs=None):
    """One block per family: the week's total in its colour, a change chip
    against last week, a bar against the week's leader, then the models
    with the family's lifetime total. Colours follow the list cycle by
    position, so they decorate the chart rather than stand for a platform."""
    F, M, W = flex.F, flex.M, flex.W
    im, d, bg, panel, panel2, edge, acc = _canvas('Japan sales', subheader,
                                                  background)
    muted = flex.lift(flex.BODY, -0.30, bg)
    fams = families(hardware)
    top = max(f[1] for f in fams) or 1
    y = 400
    for i, (name, week, models) in enumerate(fams):
        colour = flex.ACCENTS[CYCLE[i % len(CYCLE)]]
        h = 300 if len(models) > 1 else 220
        d.rounded_rectangle([M, y, W - M, y + h], radius=20, fill=panel)
        nf = F(64, 800)
        d.text((M + 40, y + 62), name, font=nf, fill=flex.INK, anchor='lm')
        num = f'{week:,}'
        d.text((W - M - 40, y + 62), num, font=nf, fill=colour, anchor='rm')
        change_pill(d, W - M - 40 - d.textlength(num, font=nf) - 28, y + 62,
                    pct(week, last.get(name)), bg, muted, size=36)
        bx0, bx1, by = M + 40, W - M - 40, y + 118
        d.rounded_rectangle([bx0, by, bx1, by + 22], radius=11, fill=panel2)
        fill = bx0 + max(22, int((bx1 - bx0) * week / top))
        d.rounded_rectangle([bx0, by, fill, by + 22], radius=11, fill=colour)
        life = sum(m[2] for m in models)
        if len(models) > 1:
            parts = ' · '.join(f'{SHORT.get(k, k)} {w:,}' for k, w, _ in models)
            d.text((M + 40, y + 190), parts, font=F(36, 600), fill=flex.BODY,
                   anchor='lm')
            d.text((M + 40, y + 248), f'{life:,} total', font=F(32, 600),
                   fill=muted, anchor='lm')
        else:
            d.text((M + 40, y + 180), f'{life:,} total', font=F(36, 600),
                   fill=muted, anchor='lm')
        y += h + 30
    if vs:
        key(d, vs, bg, muted)
    flex.footer(im, bg, 'Famitsu', date, edge).save(out)
    return out


if __name__ == '__main__':
    url, stem, date = sys.argv[1], sys.argv[2], sys.argv[3]
    prev = sys.argv[4] if len(sys.argv) > 4 else None
    sw, hw, last_hw, nxt = render(url, stem, date, prev)
    for s in sw:
        print(s['rank'], s['plat'], english(s['jp']), s['week'], s['life'],
              'NEW' if s['new'] else f'last {s["last"]} (was #{s["was"]})',
              pct(s['week'], s['last']))
    for name, week, _ in families(hw):
        print(name, week, 'last', last_hw.get(name), pct(week, last_hw.get(name)))
    if nxt:
        print('next Famitsu post:', '/'.join(nxt.groups()))
