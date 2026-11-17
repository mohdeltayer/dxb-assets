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


class Segment(unittest.TestCase):
    def test_segment_bounds(self):
        import decodecheck as DC
        self.assertEqual(DC._segment(3.7, [0, 2.9, 4.9]), (2.9, 4.9))
        self.assertEqual(DC._segment(6.0, [0, 2.9, 4.9]), (4.9, None))


class AutoShots(unittest.TestCase):
    def setUp(self):
        AF.LOG[:] = []

    def reader(self, f):
        return {'duration': 60.0, 'picture_start': 1.5,
                'shots': [{'start': 2.0, 'end': 9.0, 'focus': 0.9}, {'start': 12.0, 'end': 20.0, 'focus': 0.5},
                          {'start': 25.0, 'end': 26.5, 'focus': 0.5}, {'start': 30.0, 'end': 45.0, 'focus': 0.45},
                          {'start': 50.0, 'end': 58.0, 'focus': 0.55}]}

    def test_auto_expands_and_fills_in_source_order(self):
        import autoshots as AS
        j = {'footage': [{'file': 't.mp4'}], 'shots': 'auto', 'lines': [[1, 1, ['a']], [2, 2, ['b']], [3, 3, ['c']]]}
        AS.expand(j)
        self.assertEqual(len(j['shots']), 4)
        self.assertEqual(j['shots'][0][2], AS.HOOK_SECS)
        self.assertEqual(AS.fill(j, self.reader), [])
        starts = [s[1] for s in j['shots']]
        self.assertEqual(starts, sorted(starts))
        for s in j['shots']:                                   # inside a clean stretch, whole length
            self.assertTrue(any(r['start'] <= s[1] and s[1] + s[2] <= r['end'] for r in self.reader('t')['shots']))
        self.assertNotIn('shots_auto', j)
        self.assertTrue(all(x['rule'] == 'auto_shots' for x in AF.LOG))

    def test_one_slot_in_a_written_list(self):
        import autoshots as AS
        j = {'footage': [{'file': 't.mp4'}], 'shots': [['t.mp4', 12.5, 3.0, 0.5], ['t-gfx-1.png', None, 3.0, None],
                                                      ['t.mp4', 'auto', 4.0, None]]}
        AS.expand(j)
        self.assertEqual(j['shots_auto'], [2])
        self.assertEqual(AS.fill(j, self.reader), [])
        self.assertEqual(j['shots'][0][1], 12.5)                # hand-timed shots stay
        self.assertIsInstance(j['shots'][2][1], float)

    def test_refused_when_nothing_is_long_enough(self):
        import autoshots as AS
        j = {'footage': [{'file': 't.mp4'}], 'shots': [['t.mp4', 'auto', 20.0, None]]}
        AS.expand(j)
        left = AS.fill(j, self.reader)
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]['rule'], 'auto_shots')


if __name__ == '__main__':
    unittest.main()
