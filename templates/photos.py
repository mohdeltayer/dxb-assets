"""Photo sets for TikTok's photo mode (Mohammad, 3 Oct 2026: TikTok prompted
"post photos to get more views" while every API-posted video sat near 0).

A swipe-through set, 1080x1920 PNGs, built from our own graphics: a cover
that asks the question, one slide per entry with the box art full bleed and
the numbers over it, an optional hardware slide, and an end slide with the
mark. Posted by hand from his phone, not through Postiz.

    python3 photos.py            # renders the 21-27 Sep Famitsu week as a draft

Text stays inside the Reels safe zone (TikTok's caption and buttons cover
the same edges). Every Arabic line starts with an Arabic word; English
titles sit on their own line, as on the Famitsu cards.
"""
import os
from PIL import Image, ImageDraw, ImageFilter
import fast_ar as A, ig_ar as G, reel
import sales_reel as S

W, H = 1080, 1920
R, L = G.SAFE_RIGHT, G.SAFE_LEFT
TOP, BOTTOM = G.SAFE_TOP, G.SAFE_BOTTOM
PLATFORM = {'Switch2': 'Nintendo Switch 2', 'Switch': 'Nintendo Switch', 'PS5': 'PS5', 'PS4': 'PS4',
            'XSX': 'Xbox Series X|S'}
HW_NAME = {'Switch 2': 'Nintendo Switch 2', 'Switch': 'Nintendo Switch', 'Xbox Series': 'Xbox Series X|S'}
RANK = {1: 'الأول', 2: 'الثاني', 3: 'الثالث', 4: 'الرابع', 5: 'الخامس', 6: 'السادس', 7: 'السابع',
        8: 'الثامن', 9: 'التاسع', 10: 'العاشر'}


def _fill(art, dim=0.55, blur=40):
    """The art blurred to fill 9:16, darkened so white type holds."""
    im = Image.open(art).convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(im, Image.new('RGB', (W, H), A.GROUND), dim).convert('RGBA')


def _glow_text(im, draw):
    """Draw with `draw(d)` on a transparent layer, then lay a soft ground
    glow under it so text reads on any art."""
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw(ImageDraw.Draw(t))
    a = t.getchannel('A')
    glow = Image.new('RGBA', (W, H), A.GROUND + (0,))
    glow.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(12)).point(lambda v: min(255, v * 2)))
    im.alpha_composite(glow); im.alpha_composite(t)


def _art_box(im, art, top, max_h, max_w=W - 2 * 120):
    """The box art, whole, centred, with rounded corners and a shadow."""
    b = S.trim(art)
    s = min(max_w / b.width, max_h / b.height)
    b = b.resize((round(b.width * s), round(b.height * s)), Image.LANCZOS)
    x = (W - b.width) // 2
    m = Image.new('L', b.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, b.width - 1, b.height - 1], 22, fill=255)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sm = Image.new('L', (W, H), 0); sm.paste(m, (x + 10, top + 18))
    sh.putalpha(sm.filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.7)))
    im.alpha_composite(sh)
    im.paste(b.convert('RGB'), (x, top), m)
    return top + b.height


def _fit(d, text, weight, size, room, low=40, **kw):
    while d.textlength(text, font=A.F(weight, size), **kw) > room and size > low:
        size -= 2
    return A.F(weight, size)


def cover(question, sub, date, arts, out, source='فاميتسو (Famitsu)', theme='gold', label='أرقام'):
    """The question, the week, and the week's box art in a row; the answer is
    in the picture but not named, so the swipe still pays off."""
    G._ACC = G.ACCENTS[theme]
    im = _fill(arts[0], dim=0.7)
    tmp = out + '.head.png'
    reel.head_layer(question, label, tmp, source, date, vivid=True, theme=theme, seed=7, style='glow')
    im.alpha_composite(Image.open(tmp)); os.remove(tmp)
    # the week's box art in two rows (3 then 2), right to left in rank order
    rows_ = [arts[:3], arts[3:]] if len(arts) > 3 else [arts]
    y, gap, bh = 700, 22, 300
    for row_ in rows_:
        boxes = [S.trim(a_) for a_ in row_]
        h = bh
        while True:
            rs = [b_.resize((max(1, round(b_.width * h / b_.height)), h), Image.LANCZOS) for b_ in boxes]
            total = sum(b_.width for b_ in rs) + gap * (len(rs) - 1)
            if total <= W - 120 or h <= 160:
                break
            h -= 10
        x = W - (W - total) // 2
        for b_ in rs:
            m = Image.new('L', b_.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, b_.width - 1, b_.height - 1], 16, fill=255)
            im.paste(b_.convert('RGB'), (x - b_.width, y), m)
            x -= b_.width + gap
        y += h + gap
    prompt_y = y + 150
    _glow_text(im, lambda d: d.text((W - R, y + 40), sub, font=A.F('Medium', 44), fill=A.INK, anchor='rm', **G.AR))
    _glow_text(im, lambda d: d.text((W - R, prompt_y), 'اسحب لمعرفة الترتيب', font=A.F('Bold', 46),
                                    fill=G._ACC, anchor='rs', **G.AR))
    im.convert('RGB').save(out); return out


def entry(row, out, theme='gold'):
    """One chart entry: rank, the box art, title and platform, then this
    week's copies, the total, and the movement."""
    G._ACC = G.ACCENTS[theme]
    im = _fill(row['art'])
    acc = G._ACC

    def top(d):
        d.text((W - R, TOP + 40), f'المركز {RANK[row["rank"]]}', font=A.F('Bold', 64), fill=acc, anchor='rm', **G.AR)
        if row.get('new'):
            mv = 'دخول جديد'
        elif row.get('was'):
            mv = f'كانت في المركز {RANK.get(row["was"], row["was"])}' if row['was'] != row['rank'] else 'في المركز نفسه'
        else:
            mv = ''
        if mv:
            d.text((W - R, TOP + 120), mv, font=A.F('Medium', 40), fill=A.BODY, anchor='rm', **G.AR)
    _glow_text(im, top)
    end = _art_box(im, row['art'], TOP + 190, 640, W - 160)

    def body(d):
        y = end + 60
        f = _fit(d, row['title'], 'Bold', 60, W - L - R)
        d.text((W - R, y), row['title'], font=f, fill=A.INK, anchor='ra')
        y += 90
        d.text((W - R, y), f'على {PLATFORM.get(row["plat"], row["plat"])}', font=A.F('Medium', 42), fill=A.BODY,
               anchor='ra', **G.AR)
        y += 110
        # two figures side by side: this week (right), since launch (left)
        cols = [('هذا الأسبوع', row['week']), ('منذ الإطلاق', row['life'])]
        if row.get('new') or row['life'] == row['week']:
            cols = cols[:1]
        cw = (W - L - R) // 2
        for i, (lab, n) in enumerate(cols):
            xr = W - R - i * cw
            d.text((xr, y), lab, font=A.F('Medium', 38), fill=A.BODY, anchor='ra', **G.AR)
            d.text((xr, y + 56), f'{n:,}', font=A.F('Bold', 92), fill=acc if i == 0 else A.INK, anchor='ra')
        d.text((W - R, y + 190), 'نسخة مبيعة في متاجر اليابان', font=A.F('Medium', 34), fill=A.BODY, anchor='ra', **G.AR)
    _glow_text(im, body)
    im.convert('RGB').save(out); return out


def hardware(rows, sub, out, theme='gold', title='مبيعات الأجهزة'):
    """The week's consoles, largest first, on the brand ground with the
    theme's waves."""
    G._ACC = G.ACCENTS[theme]
    im = Image.new('RGBA', (W, H), A.GROUND + (255,))
    reel._colour(im, 700, theme, 11, 'bold')
    acc = G._ACC

    def draw(d):
        d.text((W - R, TOP + 60), title, font=A.F('Bold', 76), fill=A.INK, anchor='rm', **G.AR)
        d.text((W - R, TOP + 150), sub, font=A.F('Medium', 40), fill=A.BODY, anchor='rm', **G.AR)
        d.text((W - R, TOP + 215), 'وحدة مبيعة في اليابان', font=A.F('Medium', 36), fill=A.BODY, anchor='rm', **G.AR)
        y = TOP + 330
        top_n = max(r['week'] for r in rows)
        for r in sorted(rows, key=lambda r: -r['week']):
            d.text((W - R, y), HW_NAME.get(r['name'], r['name']), font=_fit(d, HW_NAME.get(r['name'], r['name']), 'Bold', 56, W - L - R - 260), fill=A.INK, anchor='ra')
            d.text((L, y), f'{r["week"]:,}', font=A.F('Bold', 56), fill=acc, anchor='la')
            bar = int((W - L - R) * r['week'] / top_n)
            d.rounded_rectangle([W - R - bar, y + 86, W - R, y + 104], 9, fill=acc)
            if r.get('last'):
                ch = (r['week'] - r['last']) / r['last'] * 100
                word = 'ارتفاع' if ch >= 0 else 'تراجع'
                d.text((W - R, y + 124), f'{word} بنسبة {abs(ch):.0f} في المئة عن الأسبوع السابق', font=A.F('Medium', 34),
                       fill=A.BODY, anchor='ra', **G.AR)
            y += 220
    _glow_text(im, draw)
    im.convert('RGB').save(out); return out


def end_slide(out, line='أرقام اليابان كل أسبوع', theme='gold'):
    """The mark, the name and the handle."""
    G._ACC = G.ACCENTS[theme]
    im = Image.new('RGBA', (W, H), A.GROUND + (255,))
    reel._colour(im, 600, theme, 5, 'glow')
    mark = Image.open(os.path.join(os.path.dirname(__file__), 'digi-mark.jpg')).convert('RGB').resize((300, 300), Image.LANCZOS)
    m = Image.new('L', (300, 300), 0); ImageDraw.Draw(m).ellipse([0, 0, 299, 299], fill=255)
    im.paste(mark, ((W - 300) // 2, 640), m)

    def draw(d):
        d.text((W // 2, 1040), 'ديجيتال لاونج', font=A.F('Bold', 80), fill=A.INK, anchor='mm', **G.AR)
        d.text((W // 2, 1130), 'أخبار الألعاب', font=A.F('Medium', 48), fill=A.BODY, anchor='mm', **G.AR)
        d.text((W // 2, 1250), line, font=A.F('Bold', 52), fill=G._ACC, anchor='mm', **G.AR)
        d.text((W // 2, 1350), '@the_digilounge', font=A.F('Medium', 40), fill=A.BODY, anchor='mm')
    _glow_text(im, draw)
    im.convert('RGB').save(out); return out


def famitsu_set(rows, hw, week, date, outdir, question='من تصدّر مبيعات الألعاب في اليابان هذا الأسبوع؟', n=5, theme='gold'):
    """Cover, entries n..1 (a countdown), hardware, end. Returns the paths in
    posting order."""
    os.makedirs(outdir, exist_ok=True)
    top = sorted(rows, key=lambda r: r['rank'])[:n]
    seen, arts = set(), []
    for r in top:
        if r['art'] not in seen:
            seen.add(r['art']); arts.append(r['art'])
    paths = [cover(question, week, date, arts, f'{outdir}/01-cover.png', theme=theme)]
    for i, r in enumerate(reversed(top)):
        paths.append(entry(r, f'{outdir}/{i + 2:02d}-rank{r["rank"]}.png', theme=theme))
    if hw:
        paths.append(hardware(hw, week, f'{outdir}/{len(paths) + 1:02d}-hardware.png', theme=theme))
    paths.append(end_slide(f'{outdir}/{len(paths) + 1:02d}-end.png', theme=theme))
    return paths
