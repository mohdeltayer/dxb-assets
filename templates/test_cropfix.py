"""Crop fix (Mohammad, 26 Nov 2026): stylised games, empty frames, cut text, long shots; autofixes, not refusals."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shotgate as SG
import autofix as AF


class Stylised(unittest.TestCase):
    def test_names(self):
        self.assertTrue(SG.stylised({'game': 'DRAGON QUEST MONSTERS: The Withered World'}))
        self.assertTrue(SG.stylised({'game': 'Pokémon Champions'}))
        self.assertTrue(SG.stylised({'genre': ['anime', 'fighting']}))
        self.assertFalse(SG.stylised({'game': 'Ghost of Tsushima', 'genre': ['open world']}))
        self.assertFalse(SG.stylised({'game': 'Mario Kart World', 'stylised': False}))


class Attempts(unittest.TestCase):
    sh = ['x.mp4', 10.0, 5.0, None]

    def test_unseen_goes_to_showcase(self):
        self.assertEqual(AF._attempts({'rule': 'subject_unseen'}, self.sh), [])

    def test_long_trims_to_four(self):
        a = AF._attempts({'rule': 'shot_long', 'safe_secs': 4.0}, self.sh)
        self.assertEqual(a[0][0], 'trim'); self.assertEqual(a[0][1][2], 4.0)

    def test_empty_reaims_then_shifts(self):
        a = AF._attempts({'rule': 'subject_empty'}, self.sh)
        kinds = [k for k, *_ in a]
        self.assertEqual(kinds[0], 'focus'); self.assertIn('shift', kinds)
        self.assertLessEqual(max(abs(c[1] - 10.0) for k, c, _ in a if k == 'shift'), AF.SHIFT + 1e-6)

    def test_text_cut_reaims(self):
        a = AF._attempts({'rule': 'subject_text_cut'}, ['x.mp4', 10.0, 3.0, 0.25])
        self.assertTrue(any(k == 'focus' and c[3] == 0.5 for k, c, _ in a))


if __name__ == '__main__':
    unittest.main()
