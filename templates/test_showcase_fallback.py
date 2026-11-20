"""The 16:9 fallback (Mohammad, 20 Nov 2026): footage that clashes with our text goes to the showcase layout."""
import json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import softgate as SG
import reel
import render_job as RJ
import presubmit as PS

JOB = lambda **kw: {'shots': [['t.mp4', 5.0, 3.0, None], ['t.mp4', 9.0, 3.0, None]], 'template': 'trailer', **kw}


class Fallback(unittest.TestCase):
    def setUp(self):
        SG.WARNINGS.clear(); SG.LADDER.clear()

    def test_ok_and_blockers(self):
        self.assertTrue(SG.showcase_ok(JOB()))
        for kw in ({'gfx': [{'file': 'x'}]}, {'person': [['p.jpg']]}, {'template': 'numbers'}, {'layout': 'showcase'},
                   {'showcase_fallback': False}, {'kind': 'breaking'}, {'intro': {'series': 'gtavi'}}):
            self.assertFalse(SG.showcase_ok(JOB(**kw)), kw)

    def test_reason_accepted(self):
        j = JOB()
        self.assertTrue(SG.showcase_fallback(j, 'burnt-in text in shot 0'))
        self.assertEqual(j['layout'], 'showcase')
        self.assertTrue(reel.showcase_reason(j['showcase_reason']))
        self.assertEqual(SG.LADDER[-1]['step'], 'b')

    def test_drift_goes_showcase(self):
        j = JOB()
        RJ.gate_ladder(j, [{'where': 'shot 1', 'rule': 'subject_drift', 'detail': 'shot 1: the subject leaves the window'}])
        self.assertEqual(j['layout'], 'showcase')
        self.assertTrue(j['drift_ok'])

    def test_scene_cut_keeps_crop(self):
        j = JOB()
        RJ.gate_ladder(j, [{'where': 'shot 0', 'rule': 'shot_timing', 'detail': "crosses the trailer's scene cut at 6.0 s"}])
        self.assertNotIn('layout', j)

    def test_burnt_in_text(self):
        d = tempfile.mkdtemp() + '/'
        open(d + 't.mp4', 'wb').close()
        j = JOB()
        with mock.patch.object(RJ.C, 'U', d), mock.patch.object(reel, '_vert', lambda *a, **k: None), \
                mock.patch.object(reel, '_words', lambda im: ['Koyama', 'Hirokazu']):
            why = RJ.content_ladder(j)
        self.assertIn('burnt-in text in shot 0', why)
        self.assertEqual(j['layout'], 'showcase')

    def test_one_logo_frame_keeps_crop(self):
        d = tempfile.mkdtemp() + '/'
        open(d + 't.mp4', 'wb').close()
        j = JOB()
        seen = []
        def words(im):
            seen.append(1)
            return ['NINTENDO', 'SWITCH'] if len(seen) == 3 else []      # shot 1, first frame only
        with mock.patch.object(RJ.C, 'U', d), mock.patch.object(reel, '_vert', lambda *a, **k: None), \
                mock.patch.object(reel, '_words', words):
            self.assertIsNone(RJ.content_ladder(j))
        self.assertNotIn('layout', j)

    def test_clean_and_no_tesseract(self):
        d = tempfile.mkdtemp() + '/'
        open(d + 't.mp4', 'wb').close()
        for words in ([], ['a'], None):
            j = JOB()
            with mock.patch.object(RJ.C, 'U', d), mock.patch.object(reel, '_vert', lambda *a, **k: None), \
                    mock.patch.object(reel, '_words', lambda im, w=words: w):
                self.assertIsNone(RJ.content_ladder(j))
            self.assertNotIn('layout', j)

    def test_three_tries_then_fallback(self):
        import jobsha, datetime as dt
        now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        for n, moved in ((2, False), (3, True)):
            j = JOB(name='witch-on-the-holy-night')
            rows = [{'story': 'witch-on-the-holy-night', 'finished_at': now}] * n
            with mock.patch.object(jobsha, '_entries', lambda rows=rows: rows):
                RJ.tries_ladder(j)
            self.assertEqual(j.get('layout') == 'showcase', moved, n)

    def test_director_sendback_moves_job(self):
        f = tempfile.mktemp(suffix='.json')
        json.dump(JOB(), open(f, 'w'))
        why = PS.to_showcase(f, 'unreadable_text', 'subtitles under the lines')
        self.assertIn('director send-back unreadable_text', why)
        self.assertEqual(json.load(open(f))['layout'], 'showcase')
        json.dump(JOB(gfx=[{'file': 'x'}]), open(f, 'w'))
        self.assertIsNone(PS.to_showcase(f, 'wrong_subject'))


if __name__ == '__main__':
    unittest.main()
