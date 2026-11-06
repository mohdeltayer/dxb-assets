"""Tests for the build gate: python3 -m unittest templates/test_buildgate.py (from the repo root)."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildgate as BG  # noqa: E402

STORY = {'id': 's1', 'sources': [{'role': 'primary', 'url': 'https://example.com/a'}],
         'first_report': 'Publisher post, 5 Nov 09:00Z', 'source_type': 'primary',
         'footage': 'official trailer, Steam app 1', 'lane': 'digital-lounge', 'beat': 'trailer',
         'ledger_find': {'at': '2026-11-05T19:00:00Z', 'words': ['x'], 'hits': []}}
RC = [{'line': f'line {i}', 'answer': 'yes', 'evidence': 'e'} for i in range(10)]


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.keep = BG.STORIES
        BG.STORIES = pathlib.Path(self.tmp.name)
        (BG.STORIES / 's1.json').write_text(json.dumps(STORY))

    def tearDown(self):
        BG.STORIES = self.keep
        self.tmp.cleanup()

    def job(self, **kw):
        j = {'name': 'x', 'story': 's1', 'render_lane': 'server', 'reel_check': RC}
        j.update(kw)
        return {k: v for k, v in j.items() if v is not None}

    def test_good_server_job_passes(self):
        self.assertEqual(BG.problems('jobs/live/x.json', self.job()), [])

    def test_hosted_needs_reason_and_folder(self):
        p = BG.problems('jobs/live/x.json', self.job(render_lane='hosted'))
        self.assertTrue(any('lane_reason' in x for x in p) and any('jobs/render' in x for x in p))
        self.assertEqual(BG.problems('jobs/render/x.json', self.job(render_lane='hosted', lane_reason='server down')), [])

    def test_server_lane_in_jobs_render_refused(self):
        self.assertTrue(any('jobs/live' in x for x in BG.problems('jobs/render/x.json', self.job())))

    def test_missing_lane_story_reel_check(self):
        p = BG.problems('jobs/live/x.json', {'name': 'x'})
        self.assertEqual(len(p), 3)

    def test_no_ledger_find(self):
        s = dict(STORY); s.pop('ledger_find')
        (BG.STORIES / 's1.json').write_text(json.dumps(s))
        self.assertTrue(any('ledger.py find' in x for x in BG.problems('jobs/live/x.json', self.job())))

    def test_story_fields(self):
        s = dict(STORY); s.pop('first_report'); s['footage'] = 'stills'; s['source_type'] = 'blog'
        (BG.STORIES / 's1.json').write_text(json.dumps(s))
        p = BG.problems('jobs/live/x.json', self.job())
        self.assertTrue(any('first_report' in x for x in p))
        self.assertTrue(any('source_type' in x for x in p))
        self.assertTrue(any('stills need' in x for x in p))

    def test_reel_check_no_and_short(self):
        rc = RC[:3] + [{'line': 'credit on every clip', 'answer': 'no'}]
        p = BG.problems('jobs/live/x.json', self.job(reel_check=rc))
        self.assertTrue(any('answered no' in x for x in p) and any('at least' in x for x in p))
        d = {f'l{i}': 'yes: e' for i in range(9)}
        d['footage first'] = 'no: stills'
        self.assertTrue(any('answered no' in x for x in BG.problems('jobs/live/x.json', self.job(reel_check=d))))

    def test_test_jobs_not_gated(self):
        self.assertEqual(BG.problems('jobs/test/x.json', {'name': 'x'}), [])


if __name__ == '__main__':
    unittest.main()


class Stills(unittest.TestCase):
    def test_detection(self):
        self.assertTrue(BG.is_stills_job({'template': 'stills'}))
        self.assertTrue(BG.is_stills_job({'shots': [['a.jpg', 0, 3, None], ['card-gfx-1.png', 0, 2, None]]}))
        self.assertFalse(BG.is_stills_job({'shots': [['a.jpg', 0, 3, None], ['t.mp4', 1, 3, None]]}))
        self.assertFalse(BG.is_stills_job({'template': 'storybeat', 'shots': [['p.png', 0, 3, None]]}))
        self.assertFalse(BG.is_stills_job({'kind': 'famitsu'}))

    def test_reason_rules(self):
        j = {'template': 'stills'}
        self.assertTrue(BG.stills_problems(j))
        self.assertEqual(BG.stills_problems(dict(j, stills_reason={'why': 'sales', 'tried': []})), [])
        self.assertTrue(BG.stills_problems(dict(j, stills_reason={'why': 'no_footage', 'tried': []})))
        self.assertEqual(BG.stills_problems(dict(j, stills_reason={'why': 'no_footage',
                                                                  'tried': ['Steam app 1: no trailer']})), [])
        self.assertTrue(BG.stills_problems(dict(j, stills_reason={'why': 'looks nice'})))

    def test_decision_log_is_report_only(self):
        self.assertTrue(BG.notes({}))
        self.assertEqual(BG.notes({'decision_log': [{'beat': 1}]}), [])


class Credits(unittest.TestCase):
    SH = [['t.mp4', 0, 3, None], ['card-gfx-1.png', 0, 2, None], ['t.mp4', 5, 3, None]]

    def test_uncovered_footage_refused(self):
        p = BG.credit_problems({'shots': self.SH, 'credits': [[0, 0, 'المصدر: نينتيندو (Nintendo)']]})
        self.assertTrue(p and ' 2 ' in p[0])

    def test_gfx_needs_no_credit(self):
        self.assertEqual(BG.credit_problems({'shots': self.SH, 'credits': [[0, 0, 'المصدر: أ'], [2, 2, 'المصدر: أ']]}), [])

    def test_no_credits_at_all(self):
        self.assertTrue(BG.credit_problems({'shots': self.SH}))
        self.assertEqual(BG.credit_problems({'kind': 'breaking', 'shots': self.SH}), [])

    def test_badge_only_is_a_note(self):
        j = {'shots': self.SH, 'credits': [[0, 2, 'الطريق إلى Ocarina · الحلقة 7']], 'decision_log': [1]}
        self.assertEqual(BG.credit_problems(j), [])
        self.assertTrue(any('name no source' in n for n in BG.notes(j)))
