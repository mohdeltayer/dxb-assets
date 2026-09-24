"""Famitsu weekly Japan sales: parse Famitsu's own article, render two cards.

Famitsu posts the week's estimated physical sales (packages, download cards
and pre-installs) on famitsu.com, usually Thursday 22:00 JST (17:00 Dubai).
Holiday weeks move: the article ends with the next date ("次回は...に掲載予定").

    python3 templates/famitsu.py <famitsu article url> [out-stem]

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
        software.append(dict(rank=int(rank), new=prev == '初登場', plat=plat,
                             jp=jp.strip(), week=week, life=life))
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


def render(url, stem, date, background='reported'):
    period, nxt, software, hardware = parse(fetch(url))
    y, m1, d1, m2, d2 = period.groups()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
              'Oct', 'Nov', 'Dec']
    span = (f'{months[int(m1) - 1]} {d1}-{d2}' if m1 == m2 else
            f'{months[int(m1) - 1]} {d1} to {months[int(m2) - 1]} {d2}')

    sub = f'{span}, {y} · physical + download cards'
    software_card(software, f'Software top 10 · {sub}', date,
                  f'{stem}-software.png', background)
    hardware_card(hardware, f'Hardware · {sub}', date,
                  f'{stem}-hardware.png', background)
    return software, hardware, nxt


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


def software_card(software, subheader, date, out, background='reported'):
    """Ten rows, each with the week's number and, under it, the lifetime
    total or NEW for a first-week entry. The lifetime is the part Famitsu
    readers look for, and the combined `charts` card had no room for it."""
    F, M, W = flex.F, flex.M, flex.W
    im, d, bg, panel, panel2, edge, acc = _canvas('Japan sales', subheader,
                                                  background)
    muted = flex.lift(flex.BODY, -0.30, bg)
    rf, pf, tf = F(48, 800), F(30, 700), F(46, 700)
    nf, lf = F(48, 800), F(30, 600)
    y, ROW, STEP = 380, 118, 128
    for s in software[:10]:
        d.rounded_rectangle([M, y, W - M, y + ROW], radius=16, fill=panel)
        mid = y + ROW / 2
        d.text((M + 30, mid), f'{s["rank"]:02d}', font=rf, fill=flex.BODY,
               anchor='lm')
        d.text((M + 118, mid), PLATFORMS.get(s['plat'], s['plat']), font=pf,
               fill=muted, anchor='lm')
        d.text((M + 222, mid), _fit(d, english(s['jp']), tf, 900), font=tf,
               fill=flex.INK, anchor='lm')
        d.text((W - M - 30, mid - 18), f'{s["week"]:,}', font=nf,
               fill=flex.INK, anchor='rm')
        if s['new']:
            d.text((W - M - 30, mid + 30), 'NEW', font=F(30, 800), fill=acc,
                   anchor='rm')
        else:
            d.text((W - M - 30, mid + 30), f'{s["life"]:,} total', font=lf,
                   fill=muted, anchor='rm')
        y += STEP
    flex.footer(im, bg, 'Famitsu', date, edge).save(out)
    return out


def hardware_card(hardware, subheader, date, out, background='reported'):
    """One block per family: the week's total and a bar against the week's
    leader, then the models underneath with their lifetime numbers. One
    colour for every bar, for the same reason `charts` uses one: a colour
    per platform reads as a platform key."""
    F, M, W = flex.F, flex.M, flex.W
    im, d, bg, panel, panel2, edge, acc = _canvas('Japan sales', subheader,
                                                  background)
    muted = flex.lift(flex.BODY, -0.30, bg)
    fams = []
    for name, keys in FAMILIES:
        models = [(k, *hardware[k]) for k in keys if k in hardware]
        if models:
            fams.append((name, sum(m[1] for m in models), models))
    top = max(f[1] for f in fams) or 1
    SHORT = {'Switch2': 'Switch 2', 'Switch（有機ELモデル）': 'OLED',
             'Switch Lite': 'Lite', 'Switch': 'Original',
             'PS5 デジタル・エディション': 'Digital', 'PS5 Pro': 'Pro',
             'PS5': 'Standard', 'Xbox Series X': 'Series X',
             'Xbox Series X デジタルエディション': 'Series X Digital',
             'Xbox Series S': 'Series S'}
    y = 400
    for name, week, models in fams:
        h = 300 if len(models) > 1 else 220
        d.rounded_rectangle([M, y, W - M, y + h], radius=20, fill=panel)
        d.text((M + 40, y + 62), name, font=F(64, 800), fill=flex.INK,
               anchor='lm')
        d.text((W - M - 40, y + 62), f'{week:,}', font=F(64, 800), fill=acc,
               anchor='rm')
        bx0, bx1, by = M + 40, W - M - 40, y + 118
        d.rounded_rectangle([bx0, by, bx1, by + 22], radius=11, fill=panel2)
        fill = bx0 + max(22, int((bx1 - bx0) * week / top))
        d.rounded_rectangle([bx0, by, fill, by + 22], radius=11, fill=acc)
        if len(models) > 1:
            parts = ' · '.join(f'{SHORT.get(k, k)} {w:,}' for k, w, _ in models)
            d.text((M + 40, y + 190), parts, font=F(36, 600), fill=flex.BODY,
                   anchor='lm')
            life = sum(m[2] for m in models)
            d.text((M + 40, y + 248), f'{life:,} total', font=F(32, 600),
                   fill=muted, anchor='lm')
        else:
            d.text((M + 40, y + 180), f'{models[0][2]:,} total',
                   font=F(36, 600), fill=muted, anchor='lm')
        y += h + 30
    flex.footer(im, bg, 'Famitsu', date, edge).save(out)
    return out


if __name__ == '__main__':
    url = sys.argv[1]
    stem = sys.argv[2] if len(sys.argv) > 2 else 'famitsu'
    date = sys.argv[3] if len(sys.argv) > 3 else ''
    sw, hw, nxt = render(url, stem, date)
    for s in sw:
        print(s['rank'], s['plat'], english(s['jp']), s['week'], s['life'],
              'NEW' if s['new'] else '')
    for k, v in hw.items():
        print(k, *v)
    if nxt:
        print('next Famitsu post:', '/'.join(nxt.groups()))
