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
