"""Burning Sword case (Mohammad, 19 Nov 2026): game name in the headline, no Arabic-lettered game name, no unknown name."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textrules as T
import softgate as SG


def job(headline, line, game='Burning Sword: Death Sun', **kw):
    j = {'name': 't', 'headline': headline, 'lines': [[1, 1, [[line, {}]]]], 'game': game,
         'spoken': line + '. جملة ثانية هنا.', 'shots': [['a.mp4', 0, 4, None], ['a.mp4', 5, 4, None]]}
    j.update(kw)
    return j


def rules(j):
    return {f['rule'] for f in T.check(j) if f['rule'] in ('game_headline', 'arabic_game_name', 'name_unknown')}


class Burning(unittest.TestCase):
    def test_the_case(self):
        r = rules(job('لعبة سيوف ووشيا\nوصلت للوصول المبكر', 'لعبة القتال بيرنينغ سورد (Burning Sword) وصلت'))
        self.assertEqual(r, {'game_headline', 'arabic_game_name', 'name_unknown'})

    def test_clean(self):
        self.assertEqual(rules(job('وصلت لعبة\nBurning Sword: Death Sun', 'لعبة القتال بالسيوف وصلت الوصول المبكر')), set())

    def test_arabic_letters_without_bracket(self):
        self.assertIn('arabic_game_name', rules(job('وصلت لعبة\nBurning Sword: Death Sun', 'لعبة بيرنينغ سورد وصلت')))

    def test_short_form(self):
        j = job('متوسط 99 للعبة GTA VI', 'نص', game='Grand Theft Auto VI')
        self.assertIn('game_headline', rules(j))
        self.assertNotIn('game_headline', rules(dict(j, game_short='GTA VI')))

    def test_no_game_field(self):
        self.assertEqual(rules(job('عنوان', 'نص', game=None)), set())

    def test_hard(self):
        for r in ('game_headline', 'arabic_game_name', 'name_unknown'):
            self.assertTrue(SG.text_hard({'rule': r}))


if __name__ == '__main__':
    unittest.main()
