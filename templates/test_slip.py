"""Story slip to Reel (adv-20261117-server-news-line-editor-model, Phase 1).

    python3 templates/test_slip.py
"""
import os
os.environ.setdefault('DXB_PEOPLE_LOOKUP', 'off')   # no network in the tests
import copy
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import slip as S
import textrules as TRX  # noqa: E402
import textrules as TR  # noqa: E402

NOW = dt.datetime(2026, 11, 17, 20, 0, tzinfo=dt.timezone.utc)
BASE = {
    'id': '2026-11-17-test-game-update', 'label': 'رسمي',
    'sources': [{'role': 'primary', 'name': 'Steam news', 'url': 'https://store.steampowered.com/news/app/1'}],
    'first_report': 'Steam news 17 Nov 2026 10:00Z', 'credit': 'فالف (Valve)', 'footage': 'steam:1',
    'headline': 'تحديث كبير يصل\nإلى Test Game',
    'spoken': 'أطلق الاستوديو تحديثًا كبيرًا للعبة Test Game. يضيف التحديث خريطة جديدة وثلاثة أسلحة، '
              'ويصلح مشكلات الأداء على Steam Deck. والتحديث مجاني لكل من يملك اللعبة.',
    'instagram': 'تحديث كبير للعبة Test Game مع خريطة جديدة.\n\n#ألعاب #أخبار_الألعاب #TestGame #Steam',
    'x': 'تحديث كبير للعبة Test Game مع خريطة جديدة وثلاثة أسلحة.',
    'threads': 'تحديث كبير للعبة Test Game مع خريطة جديدة وثلاثة أسلحة.\n\nالمصدر: Steam',
    'tier': 2, 'expires': '2026-11-18T20:00:00Z',
}


def slip(**kw):
    s = copy.deepcopy(BASE)
    s.update(kw)
    if 'grammar_review' not in kw:              # reviewed texts by default (Burning Sword case, 19 Nov 2026)
        s['grammar_review'] = {'by': 'arabic-grammar-review', 'at': '2026-11-17T12:00:00Z', 'required_edits': 0,
                               'texts_sha': S.grammar_sha(s)}
    return s


class Problems(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(S.problems(slip(), NOW), [])

    def test_refusals(self):
        cases = {
            'missing': slip(spoken=''),
            'label': slip(label='عاجل'),
            'primary': slip(sources=[{'role': 'outlet', 'name': 'VGC', 'url': 'https://www.videogameschronicle.com/x'}]),
            'angle': slip(label='تقرير', sources=[{'role': 'outlet', 'name': 'VGC', 'url': 'https://x.com'}]),
            'expired': slip(expires='2026-11-17T19:00:00Z'),
            'em dash': slip(x='تحديث كبير — مجاني'),
            'Arabic-Indic': slip(x='تحديث في ١٧ نوفمبر'),
            'paragraph': slip(threads='Test Game تحديث'),
            'hashtag': slip(x='تحديث كبير #ألعاب'),
            'last line': slip(instagram='تحديث كبير للعبة Test Game.'),
            'person': slip(subject_person={'name': 'X'}),
            'tier': slip(tier=7),
            'paper': slip(x='تصدر Test Game في نسخة ورقية.'),
            'sign': slip(headline='صدرت «اللعبة الجديدة+»\nفي Test Game'),
        }
        for what, s in cases.items():
            self.assertTrue(S.problems(s, NOW), what)

    def test_grammar_review_is_a_hard_stop(self):
        s = slip()
        s['x'] = s['x'] + ' تعديل'                   # a text changed after the review
        self.assertTrue(any(p.startswith('grammar_review') for p in S.problems(s, NOW)))
        hard, _ = S.split_problems(S.problems(s, NOW))
        self.assertTrue(hard)
        self.assertTrue(any(p.startswith('grammar_review missing') for p in S.problems(slip(grammar_review=None), NOW)))

    def test_report_with_angle_passes(self):
        s = slip(label='تقرير', sources=[{'role': 'outlet', 'name': 'VGC', 'url': 'https://x.com'}],
                 angle={'why_now': 'the studio posted a teaser on its own account this morning before any statement',
                        'what_it_means_here': 'players in the Gulf would get it on the same day if the date holds true'})
        self.assertEqual(S.problems(s, NOW), [])


class Beats(unittest.TestCase):
    def test_every_word_in_order_and_two_lines(self):
        s = slip()
        bs = S.beats(s['spoken'], s['headline'])
        self.assertEqual(' '.join(bs).split(), ' '.join(S.story_sentences(s['spoken'], s['headline'])).split())
        for b in bs:
            self.assertLessEqual(len(b), S.BEAT_CHARS + 20)
            for vis in S._wrap(b).split('\n'):
                self.assertRegex(vis, '^[؀-ۿ]')   # a visual line opens on an Arabic word

    def test_wrap_balances_around_numbers(self):
        w = S._wrap('ويصل التحديث 1.2 بمستوى الخطورة Hazard 6')      # DRG, 17 Nov: was «ويصل» alone over 35 characters
        self.assertTrue(all(len(v) <= S.LINE_CHARS + 3 for v in w.split('\n')), w)
        self.assertTrue(S.fits('وتباع الإضافة على Steam بسعر 9.99 دولارات'))

    def test_headline_restatement_dropped(self):
        sp = 'تصدر Test Game في 28 يناير. وتضيف اللعبة طورًا جديدًا للعب الجماعي.'
        self.assertEqual(S.story_sentences(sp, 'تصدر Test Game\nفي 28 يناير'), ['وتضيف اللعبة طورًا جديدًا للعب الجماعي'])
        self.assertEqual(len(S.story_sentences('تصدر Test Game في 28 يناير.', 'تصدر Test Game\nفي 28 يناير')), 1)


class Job(unittest.TestCase):
    def test_job_shape_and_text_rules(self):
        j = S.job_from(slip(), {'file': 'tg-trailer.mp4', 'steam': 1}, 'live', theme='cold')
        self.assertEqual(j['template'], 'trailer')
        self.assertEqual(j['shots'][0][1:3], ['auto', S.HOOK_SECS])
        self.assertTrue(all(sh[1] == 'auto' for sh in j['shots']))
        self.assertEqual(j['credits'][0][:2], [0, len(j['shots']) - 1])
        self.assertTrue(j['credits'][0][2].startswith('المصدر: '))
        self.assertEqual(j['track'], ['tg-trailer.mp4', 0.0])
        self.assertTrue(j['track_from_first_shot'])
        self.assertGreaterEqual(len(j['reel_check']), 8)
        self.assertEqual(TR.hard(TR.check(j)), [])
        self.assertTrue(j['out'].startswith('cards/20'))
        t = S.job_from(slip(), {'file': 'tg-trailer.mp4', 'steam': 1}, 'test', theme='cold')
        self.assertTrue(t['out'].startswith('cards/test/'))

    def test_beats_span_short_shots(self):
        self.assertEqual(S.pieces(2.5), [2.5])
        self.assertEqual(len(S.pieces(4.9)), 2)
        for t in (2.0, 4.1, 4.9, 6.3, 9.0):
            p = S.pieces(t)
            self.assertTrue(all(S.PIECE_MIN <= x <= S.PIECE_MAX for x in p), (t, p))
            self.assertGreaterEqual(sum(p) - S.XFADE * (len(p) - 1), t - 0.05)
        j = S.job_from(slip(), {'file': 'tg-trailer.mp4', 'steam': 1}, 'live', theme='cold')
        self.assertTrue(all(sh[2] <= S.PIECE_MAX for sh in j['shots'][1:]))
        prev = 0
        for a, z, _ in j['lines']:                  # lines tile the shots after the hook, in order
            self.assertEqual(a, prev + 1)
            prev = z
        self.assertEqual(prev, len(j['shots']) - 1)

    def test_spare_footage_and_sound_fallback(self):
        j = S.job_from(slip(), {'file': 'a.mp4'}, 'test', theme='cold', spare=[{'file': 'b.mp4'}, {'file': 'a.mp4'}])
        self.assertEqual([x['file'] for x in j['footage']], ['a.mp4', 'b.mp4'])
        self.assertEqual(j['split_fallback'], 'ladder')
        import render_job as RJ
        self.assertTrue(callable(RJ.bed_under))

    def test_bed(self):
        j = S.job_from(slip(sound='bed', bed_reason='the only official trailer is voiced throughout over its score'),
                       {'file': 'tg-trailer.mp4', 'steam': 1}, 'live', theme='cold')
        self.assertEqual(j['track'], 'bed')
        self.assertFalse(j['track_from_first_shot'])

    def test_build_writes_story_and_job(self):
        with tempfile.TemporaryDirectory() as d:
            r = S.build(slip(), 'test', resolve=False, root=d, now=NOW)
            self.assertEqual(r['state'], 'built', r)
            st = json.load(open(os.path.join(d, r['story'])))
            self.assertEqual(st['source_type'], 'primary')
            self.assertEqual(st['template'], 'trailer')
            self.assertTrue(os.path.exists(os.path.join(d, r['job'])))
            # never refuse (adv-20261118-templates-never-refuse A): a wrong label is a warning, the slip builds
            warned = S.build(slip(label='عاجل'), 'test', resolve=False, root=d, now=NOW)
            self.assertEqual(warned['state'], 'built', warned)
            self.assertTrue(any(f.startswith('warning: label') for f in warned['flags']))
            bad = S.build(slip(headline='GTA VI تصدر اليوم'), 'test', resolve=False, root=d, now=NOW)
            self.assertEqual(bad['state'], 'built', bad)     # 25 Nov 2026: a Latin-first headline is fixed, not refused
            fixed = json.load(open(os.path.join(d, bad['job']), encoding='utf-8'))['headline']
            self.assertTrue(all(TRX._first_ok(x) for x in fixed.split('\n')), fixed)

    def test_pick_footage(self):
        c = [{'job': {'file': 'a'}, 'decode_clean': False}, {'job': {'file': 'b'}, 'decode_clean': True}]
        self.assertEqual(S.pick_footage(c)['job']['file'], 'b')
        with self.assertRaises(ValueError):
            S.pick_footage([{'job': {'file': 'a'}, 'decode_clean': False}])


class Names(unittest.TestCase):
    def test_flags(self):
        table = {'valve': 'فالف', 'nintendo': 'نينتندو'}
        s = slip(credit='نينتيندو (Nintendo)', x='أعلنت شركة زيبرا (Zebra Games) عن لعبة.')
        fl = S.name_flags(s, table)
        self.assertTrue(any('Zebra Games' in f and 'not in names-ar' in f for f in fl))
        self.assertFalse(any('Valve' in f for f in S.name_flags(slip(), table)))


class Track(unittest.TestCase):
    def test_render_job_sets_track_from_first_shot(self):
        import render_job as RJ
        j = {'track_from_first_shot': True, 'track': ['a.mp4', 0.0],
             'shots': [['x-gfx-1.png', None, 3, None], ['a.mp4', 12.5, 3.8, [[0, 0.5]]], ['a.mp4', 40.0, 3.0, None]]}
        RJ.track_from_first_shot(j)
        self.assertEqual(j['track'], ['a.mp4', 12.5])
        k = {'track': ['a.mp4', 3.0], 'shots': [['a.mp4', 9.0, 3, None]]}
        RJ.track_from_first_shot(k)
        self.assertEqual(k['track'], ['a.mp4', 3.0])


if __name__ == '__main__':
    unittest.main()


class Kind(unittest.TestCase):
    """Template by story kind, skin by genre (audit of 21 Nov 2026, items 1 and 3)."""

    def test_numbers_card_on_footage(self):
        s = slip()
        s.update(headline='لعبة GTA VI تحقق 3.79 مليار دولار\nفي يومها الأول', game='Grand Theft Auto VI', kind='news',
                 spoken='أعلنت روكستار (Rockstar Games) أن مبيعات لعبة GTA VI بلغت 3.79 مليار دولار في يومها الأول.')
        j = S.job_from(s, {'file': 'a.mp4'}, 'test', theme='cold')
        self.assertEqual(j['template'], 'numbers')
        self.assertEqual(j['gfx'][0]['value'], '3.79 مليار')
        self.assertEqual(j['shots'][1][0], j['gfx'][0]['file'])
        self.assertEqual(j['ground_footage'][0], 'a.mp4')

    def test_people_window_on_frame_zero(self):
        s = slip()
        s.update(headline='كاتبة قصة Clair Obscur\nتغادر استوديو اللعبة', game='Clair Obscur: Expedition 33', kind=None,
                 spoken='غادرت جينيفر سفيدبيرغ-ين، رئيسة السرد في لعبة Clair Obscur: Expedition 33، استوديو Sandfall '
                        'Interactive في يوليو. وقالت إنها أنهت عملها على اللعبة.')
        j = S.job_from(s, {'file': 'a.mp4'}, 'test', theme='cold')
        self.assertEqual(j['template'], 'people')
        self.assertEqual(j['person'][0][1], 'جينيفر سفيدبيرغ-ين')
        self.assertEqual(j['person'][0][3], 0.0)
        self.assertFalse(any(x.get('frame_of') for x in j['footage']))   # never a game frame (22 Nov 2026)
        self.assertIsNone(j['person'][0][0])                                # the name card
        self.assertEqual(j['person_photo'], 'none')

    def test_people_name_after_role_and_library(self):
        import people as PL
        s = slip()
        s.update(headline='تقرير: Pangoro كان الغائب\nعن Pokken Tournament', label='تقرير', game='Pokken Tournament',
                 kind='reveal',
                 spoken='ذكر موقع نينتيندو إفريثينغ (Nintendo Everything) أن منتج لعبة Pokken Tournament، كاتسوهيرو '
                        'هارادا (Katsuhiro Harada)، قال إن Pangoro هو الوحش الوحيد الذي أراد إضافته إلى اللعبة.')
        orig = PL.load
        PL.load = lambda path=None: {'harada': {'name_latin': 'Katsuhiro Harada', 'photo': 'live/people/harada.jpg',
                                                'credit_ar': 'الصورة: Kevin Paul، ويكيميديا كومنز، CC BY 4.0',
                                                'focus': [0.49, 0.32]}}
        try:
            j = S.job_from(s, {'file': 'a.mp4'}, 'test', theme='cold')
        finally:
            PL.load = orig
        self.assertEqual(j['template'], 'people')
        self.assertIn(j['person'][0][1], ('Katsuhiro Harada', 'كاتسوهيرو هارادا'))
        self.assertTrue(j['person'][0][2].startswith('منتج'))
        self.assertTrue(any(x.get('repo') == 'live/people/harada.jpg' for x in j['footage']))
        self.assertEqual(j['person'][0][5]['credit'], 'الصورة: Kevin Paul، ويكيميديا كومنز، CC BY 4.0')

    def test_split_role(self):
        self.assertEqual(S.split_role('الممثل ستيف ماكوين', ''), ('ستيف ماكوين', 'الممثل'))
        n, r = S.split_role('رئيسة الهيئة لارا الخطيب (Lara Al-Khatib)', '')
        self.assertEqual(n, 'Lara Al-Khatib')
        self.assertEqual(r, 'رئيسة الهيئة')
        self.assertEqual(S.split_role('Katsuhiro Harada', 'منتج لعبة Pokken Tournament'),
                         ('Katsuhiro Harada', 'منتج لعبة Pokken Tournament'))

    def test_source_line_forms(self):
        import creditfit as CF
        src = 'يوروغيمر (Eurogamer)، ولقطات من روكستار (Rockstar Games)'
        foot = CF.FOOT.search(src)
        self.assertTrue(foot)
        self.assertEqual(src[:foot.start()].rstrip(' ،,'), 'يوروغيمر (Eurogamer)')

    def test_game_key_and_story_hook(self):
        import gamekey
        import variety
        self.assertEqual({gamekey.key(n) for n in ('GTA VI', 'Grand Theft Auto VI', 'GTA 6', 'GTA VI™')}, {'gta vi'})
        cur, subj = variety.curated('Grand Theft Auto VI')
        self.assertGreaterEqual(len(cur), 20)
        best = max(cur, key=lambda s: variety.story_score(s, 'من ألهم شخصية جيسون في GTA VI؟', subj, True))
        self.assertIn('jason', best['tags'])

    def test_headline_drops_chip_word(self):
        import textrules as TR
        j, _ = TR.fix({'headline': 'تقرير: Pangoro كان الغائب\nعن Pokken Tournament', 'label': 'تقرير',
                       'game': 'Pokken Tournament'})
        self.assertTrue(j['headline'].startswith('تقرير:'))           # dropping it would open on «Pangoro»: the writer rewords
        j, _ = TR.fix({'headline': 'تقرير: الوحش Pangoro غاب\nعن Pokken Tournament', 'label': 'تقرير'})
        self.assertEqual(j['headline'], 'الوحش Pangoro غاب\nعن Pokken Tournament')
        j, _ = TR.fix({'headline': 'رسمي: موعد اللعبة', 'label': 'تقرير'})
        self.assertEqual(j['headline'], 'رسمي: موعد اللعبة')            # a different chip: left to the writer
        j, _ = TR.fix({'headline': 'حصري: موعد اللعبة', 'label': 'جديد'})
        self.assertEqual(j['headline'], 'موعد اللعبة')

    def test_plain_announcement_stays_trailer_and_never_fails(self):
        s = slip()
        s.update(kind='reveal')
        j = S.job_from(s, {'file': 'a.mp4'}, 'test', theme='cold')
        self.assertEqual(j['template'], 'trailer')
        import storykind as SK
        self.assertEqual(SK.classify({'spoken': None, 'headline': None})[0], 'trailer')

    def test_skin_by_genre(self):
        import storykind as SK
        self.assertEqual(SK.skin_for(['rpg'], 'Persona 6')[0], 'fantasy')
        self.assertEqual(SK.skin_for(['sci-fi'], 'The Ascent')[0], 'scifi')
        self.assertEqual(SK.skin_for(['open world'], 'Grand Theft Auto VI')[0], 'house')
        self.assertEqual(SK.skin_for(['rpg'], None)[0], 'house')


class Names(unittest.TestCase):
    """Names rule correction (21 Nov 2026): unknown names go Latin, the game goes into the headline, never a refusal."""

    def test_unknown_name_written_latin(self):
        import textrules as T
        self.assertEqual(T.latin_unknown_names('ذكرت صحيفة ذي\nإندبندنت (The Independent) أن', {})[0],
                         'ذكرت صحيفة The Independent أن')
        self.assertEqual(T.latin_unknown_names('قال المنتج كازو هيسا (Kazu Hisa Foo) إن', {})[0],
                         'قال المنتج Kazu Hisa Foo إن')
        self.assertEqual(T.latin_unknown_names('أكدت أتلس (Atlus) أن', {'atlus': 'أتلس'})[0], 'أكدت أتلس (Atlus) أن')

    def test_game_put_in_headline(self):
        import textrules as T
        j = {'headline': 'داونينغ ستريت: روكستار\nقصة نجاح بريطانية', 'game': 'Grand Theft Auto VI', 'game_short': 'GTA VI'}
        self.assertEqual(T.headline_with_game(j), 'لعبة GTA VI\nداونينغ ستريت: روكستار\nقصة نجاح بريطانية')
        j['headline'] = 'لعبة GTA VI تحقق رقمًا'
        self.assertIsNone(T.headline_with_game(j))
