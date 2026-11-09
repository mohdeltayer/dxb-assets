"""Tests for scout_file.py (the Newsdesk file)."""
import datetime as dt, json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scout_file as S  # noqa: E402

GOOD = {'run_at': '2026-11-09T16:35:00Z', 'digest_seq': 233, 'digest_head': 233, 'emails_read': ['20:27 Dubai'],
        'leads': [{'rank': 1, 'title': 'A', 'primary_url': 'https://x.example/a', 'first_report': 'publisher, 9 Nov 14:00Z',
                   'arabic_coverage': False, 'footage_route': 'Steam trailer', 'decision': 'built', 'slot': '21:30 Dubai',
                   'publer_ids_last6': ['ig:abc123', 'x:def456', 'th:789abc'], 'story_id': 's'},
                  {'rank': 2, 'title': 'B', 'primary_url': 'https://x.example/b', 'first_report': 'outlet',
                   'arabic_coverage': True, 'footage_route': 'none', 'decision': 'rejected', 'reason': 'duplicate'}],
        'post_this_hour': '21:30 Dubai A', 'gap_min': 30}


class Scout(unittest.TestCase):
    def test_good(self):
        self.assertEqual(S.problems(GOOD, '20261109-2035.json'), [])

    def test_refusals(self):
        bad = json.loads(json.dumps(GOOD))
        bad['leads'][1]['reason'] = 'too old'
        bad['leads'][0]['publer_ids_last6'] = ['ig:6735aa11bb22cc33dd44ee55']
        bad['digest_seq'] = 231
        ps = S.problems(bad, 'run.json')
        self.assertEqual(len(ps), 4)

    def test_docs_last_48h(self):
        d = tempfile.mkdtemp()
        for n in ('20261109-2035.json', '20261101-1000.json'):
            json.dump(GOOD, open(os.path.join(d, n), 'w'))
        now = dt.datetime(2026, 11, 9, 17, 0, tzinfo=dt.timezone.utc)
        w = S.docs(d, now, existing={'20261101-1000': 1})
        self.assertEqual([(x['op'], x['doc_id']) for x in w], [('set', '20261109-2035'), ('delete', '20261101-1000')])


if __name__ == '__main__':
    unittest.main()
