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

STORY = {'id': 's1', 'sources': [{'url': 'https://example.com/a'}], 'first_report': 'post, 5 Nov 09:00Z',
         'source_type': 'primary', 'footage': 'official trailer', 'lane': 'digital-lounge', 'beat': 'trailer',
         'ledger_find': {'at': 'x', 'words': ['x'], 'hits': []}}
RC = [{'line': f'l{i}', 'answer': 'yes', 'evidence': 'e'} for i in range(9)]
OUT = 'cards/2026-11/x-reel-v1.mp4'


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
        self.good = {'story': 's1', 'render_lane': 'server', 'reel_check': RC, 'out': OUT}

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
        PS.director('s1', 'PASS', OUT, job=self.write(self.good))
        PS.intent('c1', 'instagram', 's1', OUT)
        with self.assertRaises(SystemExit):
            PS.intent('c1', 'instagram', 's1', OUT)
        PS.result('c1', 'instagram', 'failed')
        PS.intent('c1', 'instagram', 's1', OUT)

    def test_intent_refused_without_checklist(self):
        s = dict(STORY, director_check={'verdict': 'PASS', 'out': OUT, 'blob': 'b' * 40})
        (PS.STORIES / 's1.json').write_text(json.dumps(s))
        with self.assertRaises(SystemExit):
            PS.intent('c2', 'x', 's1', OUT)


if __name__ == '__main__':
    unittest.main()
