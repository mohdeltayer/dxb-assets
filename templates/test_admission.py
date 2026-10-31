"""Tests for admission.py (adv-20261030-promise-keeper addendum F): the explicit breaking branch, the normal branch's
spacing and caps, and latency measured from detection.

    python3 -m unittest templates/test_admission.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import admission as A  # noqa: E402
import formats as F  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='adm-')
        self.ledger = os.path.join(self.tmp, 'format-ledger.json')
        self.log = os.path.join(self.tmp, 'latency.jsonl')
        self._ledger, F.LEDGER = F.LEDGER, self.ledger
        self._lat, A.LATENCY = A.LATENCY, self.log
        # Saturday 31 Oct, Dubai day: posts at 10:00, 10:30 and 11:00 Dubai (06:00, 06:30, 07:00Z), two splits last
        self.write([('a', 'trailer', '2026-10-31T06:00Z'), ('b', 'split', '2026-10-31T06:30Z'),
                    ('c', 'split', '2026-10-31T07:00Z')])

    def tearDown(self):
        F.LEDGER, A.LATENCY = self._ledger, self._lat

    def write(self, rows):
        with open(self.ledger, 'w') as f:
            json.dump([{'name': n, 'format': fm, 'at': at} for n, fm, at in rows], f)


class Breaking(Base):
    def test_official_breaking_bypasses_everything(self):
        d = A.admit({'id': 's', 'fmt': 'split', 'chip': 'رسمي', 'breaking': True,
                     'detected_at': '2026-10-31T06:58Z'}, now='2026-10-31T07:05Z')
        self.assertEqual(d['lane'], 'breaking')
        self.assertEqual(d['slot'], '2026-10-31T07:05Z')                 # now: no slot allocation
        self.assertEqual(d['bypassed'], ['spacing', 'format caps', 'slot allocation'])
        self.assertIn('spacing', d['would_have_blocked'])                  # 5 min after the 07:00 post
        self.assertTrue(any('third split' in x for x in d['would_have_blocked']))
        self.assertEqual(d['latency_min'], 7.0)                            # from detection, not from the editor

    def test_rumour_leak_report_never_breaking(self):
        for chip in ('تقرير', 'تسريب', 'شائعة'):
            d = A.admit({'id': 's', 'fmt': 'trailer', 'chip': chip, 'breaking': True}, now='2026-10-31T07:05Z')
            self.assertEqual(d['lane'], 'normal', chip)
            self.assertIn('verified official news only', d['why'])

    def test_breaking_needs_a_verified_chip(self):
        d = A.admit({'id': 's', 'fmt': 'trailer', 'breaking': True}, now='2026-10-31T07:05Z')
        self.assertEqual(d['lane'], 'normal')
        d = A.admit({'id': 's', 'fmt': 'trailer', 'certainty': 'official', 'breaking': True}, now='2026-10-31T07:05Z')
        self.assertEqual(d['lane'], 'breaking')

    def test_auto_go_cap_counted(self):
        for i in range(3):
            A.stamp('b%d' % i, 'admitted', '2026-10-31T0%d:00Z' % (i + 1), lane='breaking', auto_go=True)
        d = A.admit({'id': 's', 'fmt': 'trailer', 'chip': 'عاجل', 'breaking': True}, now='2026-10-31T07:05Z')
        self.assertEqual(d['lane'], 'breaking')
        self.assertEqual(d['auto_go_left'], 0)
        self.assertIn('cap reached', d['note'])


class Normal(Base):
    def test_spacing_and_quarter_hour(self):
        d = A.admit({'id': 's', 'fmt': 'trailer'}, now='2026-10-31T07:05Z')
        self.assertEqual(d['lane'], 'normal')
        self.assertEqual(d['slot'], '2026-10-31T07:30Z')                   # 07:20 rounds to 07:30, 30 min after 07:00
        self.assertIsNone(d['caps'])

    def test_caps_named_not_overruled(self):
        d = A.admit({'id': 's', 'fmt': 'split'}, now='2026-10-31T07:05Z')   # a third split in a row, whenever
        self.assertEqual(d['slot'], '2026-10-31T07:30Z')
        self.assertIn('third split in a row', d['caps'])
        self.assertIn("Mohammad's call", d['note'])

    def test_night_spacing(self):
        self.write([('n', 'trailer', '2026-10-31T21:00Z')])                 # 01:00 Dubai, night: 60 minutes apart
        d = A.admit({'id': 's', 'fmt': 'split'}, now='2026-10-31T21:05Z')
        self.assertEqual(d['slot'], '2026-10-31T22:00Z')

    def test_asked_slot_respected(self):
        d = A.admit({'id': 's', 'fmt': 'trailer', 'at': '2026-10-31T12:00Z'}, now='2026-10-31T07:05Z')
        self.assertEqual(d['slot'], '2026-10-31T12:00Z')


class Latency(Base):
    def test_detected_from_watch(self):
        items = [{'url': 'https://www.youtube.com/watch?v=abc&utm_source=x', 'first_seen': '2026-10-31T06:10:05Z'},
                 {'url': 'https://youtube.com/watch?v=abc/', 'first_seen': '2026-10-31T06:40:00Z'}]
        self.assertEqual(A.iso(A.detected_at('https://www.youtube.com/watch?v=abc', items)), '2026-10-31T06:10Z')
        self.assertIsNone(A.detected_at('https://example.com/other', items))

    def test_report_from_detection(self):
        A.stamp('x', 'detected', '2026-10-31T06:10Z')
        A.stamp('x', 'admitted', '2026-10-31T06:22Z', lane='breaking')
        A.stamp('x', 'rendered', '2026-10-31T06:26Z')
        A.stamp('x', 'published', '2026-10-31T06:41Z')
        A.stamp('x', 'published', '2026-10-31T07:41Z')                      # a later stamp never moves the first
        A.stamp('y', 'detected', '2026-10-31T05:00Z')
        A.stamp('y', 'scheduled', '2026-10-31T06:00Z', lane='normal')
        r = A.report(days=1, now='2026-10-31T08:00Z')
        x = [s for s in r['stories'] if s['id'] == 'x'][0]
        self.assertEqual(x['minutes'], {'admitted': 12.0, 'rendered': 16.0, 'published': 31.0})
        self.assertEqual(r['summary']['breaking']['published']['median'], 31.0)
        self.assertEqual(r['summary']['normal']['scheduled']['median'], 60.0)

    def test_stamp_rejects_unknown_event(self):
        with self.assertRaises(ValueError):
            A.stamp('x', 'started')

    def test_cli_logs_detection_and_admission(self):
        watch = os.path.join(self.tmp, 'breaking.json')
        with open(watch, 'w') as f:
            json.dump({'items': [], 'recent': [{'url': 'https://blog.playstation.com/2026/10/31/x/',
                                                'first_seen': '2026-10-31T06:58:30Z'}]}, f)
        rc = A.main(['admit', '--id', 'ps', '--fmt', 'trailer', '--chip', 'رسمي', '--breaking', '--auto-go',
                     '--url', 'https://blog.playstation.com/2026/10/31/x', '--watch-file', watch,
                     '--now', '2026-10-31T07:05Z', '--log'])
        self.assertEqual(rc, 0)
        rows = A.read_log()
        self.assertEqual([r['event'] for r in rows], ['detected', 'admitted'])
        self.assertEqual(rows[0]['at'], '2026-10-31T06:58Z')
        self.assertEqual((rows[1]['lane'], rows[1]['auto_go']), ('breaking', True))


if __name__ == '__main__':
    unittest.main()
