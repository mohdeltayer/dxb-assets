"""Tests for adv-20261115-one-render-server-checks (items A to F and the spoken paragraph):
python3 -m unittest templates/test_onerender_checks.py (from the repo root). B and D run on a synthetic trailer made
with ffmpeg here (a busy stretch, a hard cut, a calm stretch, a letterboxed tail, and a copy whose video starts late);
C needs the YOLO detector and is tested on the server with the real jobs (the release note has the runs)."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import textrules as TR      # noqa: E402
import buildgate as BG      # noqa: E402
import presubmit as PS      # noqa: E402
import qc as QC             # noqa: E402

TRAF = {'name': 't', 'cut': False, 'headline': 'تصدر اليوم Trafficity\nلعبة مدن تحديها الزحام',
        'shots': [['f.mp4', 23.5, 2.25, 0.4], ['f.mp4', 19.3, 1.2, 0.7], ['f.mp4', 0.8, 3.25, 0.3],
                  ['f.mp4', 15.8, 3.2, 0.8], ['f.mp4', 56.8, 3.6, 0.6]],
        'lines': [[2, 2, ['ترسم فيها الطرق بأي زاوية']], [3, 3, ['تختار كل سيارة أسرع طريق']],
                  [4, 4, ['كلما كبرت مدينتك احتاجت طرقًا أكبر']]],
        'spoken': 'تصدر اليوم Trafficity، وهي لعبة مدن تحديها الزحام. ترسم فيها الطرق بأي زاوية، وتختار كل سيارة أسرع '
                  'طريق. وكلما كبرت مدينتك، احتاجت طرقًا أكبر.'}


def rules(job, prefix):
    return [f for f in TR.check(job) if f['rule'].startswith(prefix)]


class HeadClear(unittest.TestCase):
    def test_v2_refused_v3_passes(self):
        self.assertTrue(rules(TRAF, 'head_overlap'))           # line 1 at 2.90 s (the Trafficity v2 timing)
        f = rules(TRAF, 'head_overlap')[0]
        self.assertIn('3.30', f['fix'])
        self.assertIn('lengthen', f['fix'])
        v3 = json.loads(json.dumps(TRAF))
        v3['shots'][0][2], v3['shots'][1][2] = 2.35, 1.51   # the v3 job: line 1 at 3.31 s
        self.assertEqual(rules(v3, 'head_overlap'), [])

    def test_line_on_first_shot_and_exemptions(self):
        j = dict(TRAF, lines=[[0, 4, ['ترسم فيها الطرق بأي زاوية']]])
        self.assertEqual(rules(j, 'head_overlap'), [])     # a line on shot 0 enters at 3.6 s
        self.assertEqual(rules(dict(TRAF, layout='showcase'), 'head_overlap'), [])
        self.assertEqual(rules(dict(TRAF, persist={'head': [[0, 2]]}), 'head_overlap'), [])


class Spoken(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(rules(TRAF, 'spoken'), [])

    def test_missing_and_count(self):
        j = dict(TRAF); j.pop('spoken')
        self.assertEqual([f['rule'] for f in rules(j, 'spoken')], ['spoken_missing'])
        self.assertTrue(BG.spoken_gate(j))
        self.assertEqual(BG.spoken_gate(TRAF), [])
        one = dict(TRAF, spoken='ترسم فيها الطرق بأي زاوية وتختار كل سيارة أسرع طريق وكلما كبرت مدينتك احتاجت طرقًا أكبر.')
        self.assertIn('spoken_missing', [f['rule'] for f in rules(one, 'spoken')])

    def test_order_and_added_word(self):
        sw = json.loads(json.dumps(TRAF)); sw['lines'][0], sw['lines'][1] = sw['lines'][1], sw['lines'][0]
        self.assertEqual([f['rule'] for f in rules(sw, 'spoken')], ['spoken_order'])
        add = json.loads(json.dumps(TRAF)); add['lines'][0][2] = ['ترسم فيها الطرق بأي زاوية مجانًا']
        f = rules(add, 'spoken')
        self.assertEqual(len(f), 1)
        self.assertIn('مجانًا', f[0]['fix'])

    def test_dropped_word_and_joined_latin(self):
        j = dict(TRAF, lines=[[2, 2, ['ترسم الطرق بأي زاوية']], [3, 3, ['و تختار كل سيارة أسرع طريق']]])
        self.assertEqual(rules(j, 'spoken'), [])            # a word left out, a و split off: still the paragraph
        rp = {'lines': [[0, 0, ['وتصل أيضًا إلى PS5\nو Xbox Series X|S']]],
              'spoken': 'تصدر اللعبة يوم الثلاثاء. وتصل أيضًا إلى PS5 وXbox Series X|S.'}
        self.assertEqual(rules(rp, 'spoken'), [])


class Director(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        d = pathlib.Path(self.t.name)
        self.keep = (PS.STORIES, PS.REPO, PS.qc_of, PS.blob)
        PS.STORIES, PS.REPO = d, d
        PS.blob = lambda out: 'b' * 40
        (d / 's1.json').write_text(json.dumps({'id': 's1'}))
        self.qc = {'verdict': 'pass', 'look_frames': ['a', 'b', 'c']}
        PS.qc_of = lambda out: dict(self.qc)

    def tearDown(self):
        PS.STORIES, PS.REPO, PS.qc_of, PS.blob = self.keep
        self.t.cleanup()

    def test_one_hard_sendback(self):
        out = 'cards/2026-11/x-reel-v1.mp4'
        with self.assertRaises(SystemExit):                 # no reason
            PS.director('s1', 'FIX', out, 'line 1 under the headline', by='dir')
        with self.assertRaises(SystemExit):                 # not a hard reason
            PS.director('s1', 'FIX', out, 'taste', by='dir', reason='taste')
        PS.director('s1', 'FIX', out, 'the bus, not the submarine', by='dir', reason='wrong_subject')
        qc = json.loads((pathlib.Path(self.t.name) / 'cards/2026-11/x-qc.json').read_text())
        self.assertEqual(qc['director_sendbacks'][0]['reason'], 'wrong_subject')
        s = json.loads((pathlib.Path(self.t.name) / 's1.json').read_text())
        self.assertEqual(len(s['director_sendbacks']), 1)
        with self.assertRaises(SystemExit) as e:            # no third render
            PS.director('s1', 'FIX', 'cards/2026-11/x-reel-v2.mp4', 'again', by='dir', reason='graphic')
        self.assertIn('no third render', str(e.exception))

    def test_qc_fail_needs_no_reason(self):
        self.qc = {'verdict': 'fail'}
        PS.director('s1', 'FIX', 'cards/2026-11/y-reel-v1.mp4', 'server failed it', by='dir')


class Rerender(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = self.t.name

    def tearDown(self):
        self.t.cleanup()

    def story(self, s):
        json.dump(s, open(os.path.join(self.d, 's1.json'), 'w'))

    def test_pass_is_final(self):
        job = {'story': 's1', 'name': 'x'}
        self.story({'director_check': {'verdict': 'PASS', 'qc': 'pass', 'at': '2026-11-15T07:00:00Z', 'out': 'o'}})
        self.assertIsNotNone(QC.rerender_problem(job, self.d))
        job['rerender'] = {'reason': 'source_changed', 'note': 'the publisher moved the date'}
        self.assertIsNone(QC.rerender_problem(job, self.d))

    def test_fresh_story_renders(self):
        self.story({})
        self.assertIsNone(QC.rerender_problem({'story': 's1', 'name': 'x'}, self.d))


def _ff(*a):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *a], check=True)


@unittest.skipUnless(subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode == 0, 'needs ffmpeg')
class ServerCopy(unittest.TestCase):
    """B and D on a synthetic trailer: 0-4 s busy (testsrc2), cut, 4-8 s calm grey, cut, 8-10 s letterboxed."""

    @classmethod
    def setUpClass(cls):
        import cards as C
        cls.t = tempfile.TemporaryDirectory()
        cls.keep = C.U
        C.U = cls.t.name + '/'
        _ff('-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=30:duration=4',
            '-f', 'lavfi', '-i', 'color=c=0x606060:size=640x360:rate=30:duration=4',
            '-f', 'lavfi', '-i', 'testsrc2=size=640x200:rate=30:duration=2',
            '-filter_complex', '[2:v]pad=640:360:0:80:black[lb];[0:v][1:v][lb]concat=n=3:v=1[v]', '-map', '[v]',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', C.U + 'syn.mp4')
        _ff('-i', C.U + 'syn.mp4', '-c', 'copy', '-output_ts_offset', '1.5', C.U + 'late.mp4')

    @classmethod
    def tearDownClass(cls):
        import cards as C
        C.U = cls.keep
        cls.t.cleanup()

    def test_timing(self):
        import shotgate as SG
        shots = [['syn.mp4', 1.0, 2.0, 0.5], ['syn.mp4', 3.0, 2.0, 0.5], ['syn.mp4', 8.2, 1.5, 0.5],
                 ['late.mp4', 0.5, 2.0, 0.5]]
        p, _ = SG.timing_problems({'name': 'x'}, shots)
        where = {x['where']: x['detail'] for x in p}
        self.assertNotIn('shot 0', where)
        self.assertIn('scene cut', where['shot 1'])
        self.assertIn('nearest clean start', where['shot 1'])
        self.assertIn('letterboxed', where['shot 2'])
        self.assertIn('before the picture', where['shot 3'])
        waived = SG.timing_problems({'name': 'x', 'cut_ok': [['syn.mp4', 3.0, 'looked: a match cut']]}, shots[1:2])[0]
        self.assertEqual(waived, [])

    def test_ground_pick_calm(self):
        import shotgate as SG
        seek, best, named = SG.ground_pick('syn.mp4', 0.0, 8.0, 2.0)
        self.assertGreaterEqual(seek, 4.0)                 # the calm grey, not the moving test pattern
        self.assertLess(best, named)


class Sendbacks(unittest.TestCase):
    def test_card_at_threshold(self):
        sys.path.insert(0, str(HERE.parent / 'ops'))
        import sendbacks as SB
        rows = [{'reason': 'wrong_subject', 'out': f'cards/2026-11/r{i}-reel-v1.mp4', 'note': 'n'} for i in range(3)]
        rows.append({'reason': 'graphic', 'out': 'cards/2026-11/g-reel-v1.mp4'})
        c = SB.card(SB.summary(rows))
        self.assertIsNotNone(c)
        self.assertIn('wrong_subject', c['body'])
        self.assertNotIn('graphic:', c['body'])
        self.assertIsNone(SB.card(SB.summary(rows[:2])))


if __name__ == '__main__':
    unittest.main()
