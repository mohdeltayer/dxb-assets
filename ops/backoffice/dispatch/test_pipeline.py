"""Tests for pipeline.py (release 2026-11-10 r3)."""
import datetime as dt
import unittest

import pipeline as P

BOARD = {'handoffs': [{'id': 'h1'}, {'id': 'h2'}]}


class Pipeline(unittest.TestCase):
    def test_rows_only_from_handoffs_or_stories(self):
        with self.assertRaises(ValueError):
            P.upsert({}, 'made-up', 'building', board=BOARD)
        r = P.upsert({}, 'h1', 'claimed', board=BOARD)
        self.assertEqual(r['state'], 'claimed')

    def test_forward_only_and_close(self):
        d = {}
        P.upsert(d, 'h1', 'building', '2026-11-09T16:00:00Z', board=BOARD)
        with self.assertRaises(ValueError):
            P.upsert(d, 'h1', 'claimed', board=BOARD)
        P.upsert(d, 'h1', 'published', '2026-11-09T17:00:00Z', evidence='Publer 6735aa11bb22cc33dd44ee55 read', board=BOARD)
        r = d['rows'][0]
        self.assertEqual(r['closed_at'], '2026-11-09T17:00:00Z')
        self.assertNotIn('6735aa', r['evidence'])
        with self.assertRaises(ValueError):
            P.upsert(d, 'h1', 'building', board=BOARD)

    def test_supersede_and_prune(self):
        d = {}
        P.upsert(d, 'h1', 'building', '2026-11-05T10:00:00Z', board=BOARD)
        P.upsert(d, 'h2', 'building', '2026-11-05T11:00:00Z', supersedes='h1', board=BOARD)
        self.assertEqual(d['rows'][0]['state'], 'superseded')
        now = dt.datetime(2026, 11, 9, 12, tzinfo=dt.timezone.utc)
        w = P.docs(d, {}, now, {'h1': 1, 'gone': 1})
        ids = {(x['op'], x['doc_id']) for x in w}
        self.assertIn(('set', 'h2'), ids)
        self.assertIn(('delete', 'h1'), ids)        # closed over three days ago
        self.assertIn(('delete', 'gone'), ids)


if __name__ == '__main__':
    unittest.main()
