"""Server fix of 25 Nov 2026 (Mohammad, after the 24 to 25 Nov outage): text that can be fixed is fixed, never refused."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textrules as TR

MK = ('أعلنت نينتيندو (Nintendo) أن التحديث 1.9.0 للعبة Mario Kart World على Switch 2 صدر الآن، ويضيف ثمانية مسارات '
      'جديدة هي نسخ معاد تصميمها من مسارات سابقة، منها Mario Bros. Circuit 2 وDK Pass 2 وShy Guy Bazaar 2. ويضيف مسارين '
      'جديدين في جولة الإقصاء، ومزية إعادة العرض المحسنة التي تحفظ آخر سباقاتك. وقالت الشركة إن مزيدًا من المسارات قادم '
      'في تحديثات لاحقة.')


class Sentences(unittest.TestCase):
    def test_mario_kart(self):
        s = TR.spoken_sentences(MK)
        self.assertEqual(len(s), 3)
        self.assertIn('Mario Bros. Circuit 2', s[0])
        self.assertIn('1.9.0', s[0])

    def test_abbreviations(self):
        for t in ('قال Dr. Mario إن اللعبة رائعة. وتصدر غدا.', 'صدر Vol. 2 من السلسلة. وهو جديد.',
                  'يحتوي على No. 5 فقط. انتهى.'):
            self.assertEqual(len(TR.split_sentences(t)), 2, t)
        self.assertEqual(TR.split_sentences('نسخة St. Louis جاهزة.'), ['نسخة St. Louis جاهزة'])

    def test_real_end(self):
        self.assertEqual(len(TR.split_sentences('صدرت اللعبة اليوم. وسعرها 20 دولارًا.')), 2)


class Rewrap(unittest.TestCase):
    def test_game_first(self):
        t, w = TR.arabic_first('Warhammer Survivors تصدر', ['Warhammer Survivors'])
        self.assertTrue(t.startswith('لعبة '))

    def test_break_moves(self):
        t, _ = TR.arabic_first('أعلنت الشركة عن\nCircuit 2 وDK Pass 2 الجديدين')
        self.assertTrue(all(TR._first_ok(x) for x in t.split('\n')))

    def test_word_moves(self):
        t, _ = TR.arabic_first('Bloody Insurrection تصدر في 17 ديسمبر')
        self.assertTrue(t.startswith('تصدر '))


class Headline(unittest.TestCase):
    def test_shortened_not_refused(self):
        h = ('لعبة The Legend of Zelda: Ocarina of Time Master Quest Edition الجديدة تصدر على Nintendo Switch 2 وPS5 وXbox '
             'Series X|S وSteam في 5 ديسمبر مع نسخة مطبوعة خاصة وحزمة إضافات كبيرة حسب موقع نينتيندو لايف')
        job = {'headline': h, 'game': 'The Legend of Zelda: Ocarina of Time', 'lines': [], 'spoken': 'أ ب. ج د.'}
        new, ch = TR.fix(job)
        self.assertLessEqual(TR._est_lines(new['headline']), TR.HEAD_MAX_LINES)
        self.assertFalse([f for f in TR.hard(TR.check(new)) if f['rule'] in ('headline_long', 'latin_first')])

    def test_four_lines_joined(self):
        new, _ = TR.shorten_headline('أ\nب\nج\nد')
        self.assertLessEqual(len(new.split('\n')), TR.HEAD_MAX_LINES)


if __name__ == '__main__':
    unittest.main()


class Carry(unittest.TestCase):
    def test_game_word_moves_down(self):
        out, _ = TR.carry_across(['تدعم لعبة', "Ghost of Tsushima DIRECTOR'S CUT\nعلى الحاسب اللغة العربية", 'في الواجهة'])
        self.assertTrue(all(TR._first_ok(t.split('\n')[0]) for t in out))
        self.assertEqual(' '.join(' '.join(out).split()).count('لعبة'), 1)

    def test_fix_adds_no_word(self):
        job = {'headline': 'دليل', 'lines': [[0, 1, [['تدعم لعبة', {}]]], [2, 3, [["Ghost of Tsushima\nعلى الحاسب", {}]]]],
               'spoken': "تدعم لعبة Ghost of Tsushima على الحاسب. وهي جديدة.", 'game': 'Ghost of Tsushima'}
        new, _ = TR.fix(job)
        words = ' '.join(x[2][0][0] for x in new['lines']).split()
        self.assertEqual(words.count('لعبة'), 1)


class KeepNames(unittest.TestCase):
    def test_fromsoftware_not_split(self):
        out, what = TR.keep_names(['وهي مغامرة مستقلة في عالم ELDEN RING من فروم',
                                   'سوفتوير (FromSoftware)، وصدرت في 29 مايو 2025'])
        self.assertIn('فروم سوفتوير', out[1]); self.assertFalse(out[0].endswith('فروم'), out)
        self.assertTrue(what)
        self.assertEqual(' '.join(out).split(), ('وهي مغامرة مستقلة في عالم ELDEN RING من فروم '
                                                 'سوفتوير (FromSoftware)، وصدرت في 29 مايو 2025').split())

    def test_whole_name_untouched(self):
        t = ['تطورها شركة فروم سوفتوير (FromSoftware)', 'وتصدر في 2026']
        self.assertEqual(TR.keep_names(t)[0], t)


class FitLines(unittest.TestCase):
    def test_wide_line_steps_down(self):
        import linecut as LC
        old = LC._px
        LC._px = lambda t, z: len(t) * z * 0.45            # a stand-in for the font: wide Latin names
        try:
            j = {'lines': [[1, 2, [["تدعم لعبة Horizon Zero Dawn Remastered\nعلى الحاسب اللغة العربية", {'size': 54}]]]]}
            ch = []
            TR._fit_lines(j, ch)
            t, o = j['lines'][0][2][0]
            self.assertTrue(ch)
            self.assertTrue(all(len(p) * o['size'] * 0.45 <= LC.ROOM for p in t.split('\n')), (t, o))
            self.assertEqual(t.replace('\n', ' ').split(), "تدعم لعبة Horizon Zero Dawn Remastered على الحاسب اللغة العربية".split())
        finally:
            LC._px = old

    def test_no_font_no_change(self):
        j = {'lines': [[1, 2, [["سطر قصير", {'size': 54}]]]]}
        TR._fit_lines(j, [])
        self.assertEqual(j['lines'][0][2][0][0], "سطر قصير")
