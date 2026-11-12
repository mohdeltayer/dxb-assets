"""Tests for the pre-submit step: python3 -m unittest templates/test_presubmit.py (from the repo root). No network:
the git blob lookup is replaced by a fixed id."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildgate as BG  # noqa: E402
import presubmit as PS  # noqa: E402

STORY = {'id': 's1', 'subject_person': None, 'sources': [{'url': 'https://example.com/a'}], 'first_report': 'post, 5 Nov 09:00Z',
         'source_type': 'primary', 'footage': 'official trailer', 'lane': 'digital-lounge', 'beat': 'trailer',
         'ledger_find': {'at': 'x', 'words': ['x'], 'hits': []}}
RC = [{'line': f'l{i}', 'answer': 'yes', 'evidence': 'e'} for i in range(9)]
OUT = 'cards/2026-11/x-reel-v1.mp4'
L = 'kind:news,tpl:x'


class Pre(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        d = pathlib.Path(self.t.name)
        self.keep = (PS.STORIES, PS.LOG, PS.PUBLISHED, PS.blob, BG.STORIES)
        PS.STORIES = BG.STORIES = d
        PS.LOG, PS.PUBLISHED = d / 'sub.jsonl', d / 'pub.jsonl'
        PS.blob = lambda out: 'b' * 40
        (d / 's1.json').write_text(json.dumps(STORY))
        (d / 'jobs' / 'live').mkdir(parents=True)
        self.job = d / 'jobs' / 'live' / 'job.json'
        self.good = {'story': 's1', 'render_lane': 'server', 'reel_check': RC, 'out': OUT, 'built_by': 'production-2'}

    def tearDown(self):
        PS.STORIES, PS.LOG, PS.PUBLISHED, PS.blob, BG.STORIES = self.keep
        self.t.cleanup()

    def write(self, job):
        self.job.write_text(json.dumps(job))
        return str(self.job)

    def test_pass_needs_job(self):
        with self.assertRaises(SystemExit):
            PS.director('s1', 'PASS', OUT)

    def test_pass_refused_on_a_no(self):
        bad = dict(self.good, reel_check=RC[:-1] + [{'line': 'credit', 'answer': 'no', 'evidence': ''}])
        with self.assertRaises(SystemExit):
            PS.director('s1', 'PASS', OUT, job=self.write(bad))

    def test_pass_refused_on_other_out(self):
        with self.assertRaises(SystemExit):
            PS.director('s1', 'PASS', OUT, job=self.write(dict(self.good, out='cards/2026-11/y.mp4')))

    def test_intent_after_pass_then_no_repeat(self):
        PS.director('s1', 'PASS', OUT, job=self.write(self.good), by='director-agent')
        PS.intent('c1', 'instagram', 's1', OUT, labels=L)
        with self.assertRaises(SystemExit):
            PS.intent('c1', 'instagram', 's1', OUT, labels=L)
        PS.result('c1', 'instagram', 'failed')
        PS.intent('c1', 'instagram', 's1', OUT, labels=L)

    def test_scheduled_needs_the_job_status(self):
        PS.director('s1', 'PASS', OUT, job=self.write(self.good), by='director-agent')
        PS.intent('c3', 'x', 's1', OUT, labels=L)
        with self.assertRaises(SystemExit):
            PS.result('c3', 'x', 'scheduled')                    # the list alone is not proof
        with self.assertRaises(SystemExit):
            PS.result('c3', 'x', 'scheduled', 'working')
        with self.assertRaises(SystemExit):
            PS.result('c3', 'x', 'scheduled', 'failed')
        PS.result('c3', 'x', 'scheduled', 'complete')
        last = PS.last_state('c3', 'x')
        self.assertEqual((last['state'], last['job_status']), ('scheduled', 'complete'))
        self.assertTrue(last['job_read_at'])

    def test_intent_refused_without_checklist(self):
        s = dict(STORY, director_check={'verdict': 'PASS', 'out': OUT, 'blob': 'b' * 40})
        (PS.STORIES / 's1.json').write_text(json.dumps(s))
        with self.assertRaises(SystemExit):
            PS.intent('c2', 'x', 's1', OUT, labels=L)

    # release 2026-11-10
    def test_director_must_not_be_the_builder(self):
        with self.assertRaises(SystemExit):
            PS.director('s1', 'PASS', OUT, job=self.write(self.good))                      # no --by
        with self.assertRaises(SystemExit):
            PS.director('s1', 'PASS', OUT, job=self.write(self.good), by='Production-2')   # the builder
        PS.director('s1', 'PASS', OUT, job=self.write(self.good), by='director-agent (haiku)')

    def test_labels(self):
        PS.director('s1', 'PASS', OUT, job=self.write(dict(self.good, template='trailer')), by='director-agent')
        for bad in (None, 'kind:news', 'tpl:trailer', 'kind:story,tpl:trailer', 'kind:news,tpl:split'):
            with self.assertRaises(SystemExit):
                PS.intent('c4', 'x', 's1', OUT, labels=bad)
        PS.intent('c4', 'x', 's1', OUT, labels='kind:news,tpl:trailer')

    def test_showcase_label(self):
        PS.director('s1', 'PASS', OUT, job=self.write(dict(self.good, template='trailer', layout='showcase', showcase_reason='the trailer itself is the news here')), by='d')
        with self.assertRaises(SystemExit):
            PS.intent('c5', 'x', 's1', OUT, labels='kind:news,tpl:trailer')
        PS.intent('c5', 'x', 's1', OUT, labels='kind:news,tpl:showcase')

    def test_evergreen_slot(self):
        PS.director('s1', 'PASS', OUT, job=self.write(dict(self.good, template='split', post_kind='evergreen', label='دليل')), by='d')
        with self.assertRaises(SystemExit):
            PS.intent('c6', 'x', 's1', OUT, labels='kind:news,tpl:split')          # the job is evergreen
        keep = PS.evergreen_slot_problems
        PS.evergreen_slot_problems = lambda slot: ['two evergreen posts in a row']
        with self.assertRaises(SystemExit):
            PS.intent('c6', 'x', 's1', OUT, labels='kind:evergreen,tpl:split', slot='2026-11-09T17:00:00Z')
        PS.evergreen_slot_problems = lambda slot: []
        PS.intent('c6', 'x', 's1', OUT, labels='kind:evergreen,tpl:split', slot='2026-11-09T17:00:00Z')
        PS.evergreen_slot_problems = keep

    def test_line_needs_job_status_and_ids(self):
        PS.director('s1', 'PASS', OUT, job=self.write(self.good), by='d')
        for p in PS.PLATFORMS:
            PS.intent('c7', p, 's1', OUT, labels=L)
        with self.assertRaises(SystemExit):
            PS.line('c7', ['ig:abc123', 'x:def456', 'th:789abc'])                    # no job status yet
        for p in PS.PLATFORMS:
            PS.result('c7', p, 'scheduled', 'complete')
        with self.assertRaises(SystemExit):
            PS.line('c7', ['ig:abc123', 'x:def456'])                                  # threads id missing
        with self.assertRaises(SystemExit):
            PS.line('c7', ['ig:6735aa11bb22cc33dd44ee55', 'x:def456', 'th:789abc'])  # a whole id, refused
        PS.line('c7', ['ig:abc123', 'x:def456', 'th:789abc'])


if __name__ == '__main__':
    unittest.main()
