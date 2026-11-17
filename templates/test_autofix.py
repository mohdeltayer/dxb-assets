"""Tests for templates/autofix.py (adv-20261117-gates-fix-not-refuse B). Footage-free: the shot gate is stubbed."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autofix as AF  # noqa: E402
import textrules as TR  # noqa: E402


class Aim(unittest.TestCase):
    def test_subject_right_of_centre_gets_focus(self):
        p = {'share': 0.316, 'track': [[0.1, 0.62, 0.80], [1.5, 0.64, 0.82], [2.9, 0.66, 0.84]]}
        x = AF._aim(p)
        self.assertIsNotNone(x)
        left = x * (1 - 0.316)
        self.assertLessEqual(left, 0.66)
        self.assertGreaterEqual(left + 0.316, 0.80)

    def test_subject_crossing_the_frame_has_no_static_focus(self):
        self.assertIsNone(AF._aim({'share': 0.316, 'track': [[0.1, 0.02, 0.12], [2.9, 0.86, 0.96]]}))


class Credits(unittest.TestCase):
    def test_split_prefers_middot(self):
        t = 'المصدر: حساب اللعبة على X · بيور إكس بوكس (Pure Xbox)'
        self.assertEqual(AF._two_lines(t), 'المصدر: حساب اللعبة على X\nبيور إكس بوكس (Pure Xbox)')

    def test_split_never_opens_a_line_on_latin(self):
        two = AF._two_lines('المصدر: إكس بوكس واير (Xbox Wire)')
        for row in two.split('\n'):
            self.assertRegex(row[0], '[؀-ۿ]')


class Head(unittest.TestCase):
    def setUp(self):
        AF.LOG[:] = []

    def job(self):
        return {'name': 't', 'shots': [['a.mp4', 0, 2.0, 0.5], ['a.mp4', 3, 3.0, 0.5], ['a.mp4', 7, 3.0, 0.5]],
                'lines': [[1, 1, ['السطر الأول هنا']], [2, 2, ['السطر الثاني هنا']]], 'headline': 'عنوان'}

    def test_line_under_headline_moves_to_earliest_start(self):
        j = self.job()
        self.assertTrue(TR.head_problems(j))
        self.assertTrue(AF.head(j))
        self.assertEqual(TR.head_problems(j), [])
        starts, _ = TR._timeline(j)
        self.assertGreaterEqual(starts[1] + 0.25, TR.HEAD_CLEAR)
        self.assertEqual(AF.LOG[0]['rule'], 'head_overlap')

    def test_off_switch(self):
        j = dict(self.job(), autofix=False)
        self.assertFalse(AF.head(j))


class Attempts(unittest.TestCase):
    def test_cut_trims_to_longer_clean_side(self):
        p = {'rule': 'shot_timing', 'cut_at': 11.0, 'clean_start': None}
        a = AF._attempts(p, ['f.mp4', 10.0, 3.0, 0.5])
        self.assertEqual(a[0][0], 'trim')
        self.assertEqual(a[0][1][1:3], [11.04, 1.96])     # after the cut: 1.96 s, longer than 0.96 s before it

    def test_drift_trims_first_then_focus_then_shift(self):
        p = {'rule': 'subject_drift', 'safe_secs': 2.8, 'share': 0.316, 'track': [[0.1, 0.4, 0.5]]}
        kinds = [k for k, _, _ in AF._attempts(p, ['f.mp4', 33.0, 3.0, 0.5])]
        self.assertEqual(kinds[:2], ['trim', 'focus'])
        self.assertIn('shift', kinds)

    def test_short_safe_length_is_not_a_trim(self):
        p = {'rule': 'subject_drift', 'safe_secs': 0.4, 'share': 0.316, 'track': [[0.1, 0.0, 0.9]]}
        kinds = [k for k, _, _ in AF._attempts(p, ['f.mp4', 39.8, 2.0, 0.5])]
        self.assertNotIn('trim', kinds)


class Log(unittest.TestCase):
    def test_save_appends_each_change_once(self):
        AF.LOG[:] = []; AF._SAVED[0] = 0
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'a.json')
        AF._note('shot 1', 'x', 'one')
        AF.save_log(p); AF.save_log(p)
        AF._note('shot 2', 'x', 'two')
        AF.save_log(p)
        self.assertEqual([x['what'] for x in json.load(open(p))], ['one', 'two'])


if __name__ == '__main__':
    unittest.main()
