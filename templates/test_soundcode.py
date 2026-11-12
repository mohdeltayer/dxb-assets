"""Tests for adv-20261112-sound-by-code: trailer sound by default, the bed picked on the server.

    python3 templates/test_soundcode.py
"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'ops', 'backoffice', 'keeper'))

import buildgate as BG  # noqa: E402
import qc  # noqa: E402

FOOT = {'shots': [['tr.mp4', 3.0, 3.0, None], ['tr.mp4', 9.0, 3.0, None]], 'template': 'trailer', 'kind_news': 'update'}


class Gate(unittest.TestCase):
    def test_footage_without_track_refused(self):
        self.assertTrue(BG.sound_problems(dict(FOOT)))
        self.assertTrue(BG.sound_problems(dict(FOOT, track='bed')))

    def test_track_or_reason_or_exempt_passes(self):
        self.assertEqual(BG.sound_problems(dict(FOOT, track=['tr.mp4', 3.0])), [])
        self.assertEqual(BG.sound_problems(dict(FOOT, bed_reason='launch and gameplay trailers both narrated end to end')), [])
        self.assertTrue(BG.sound_problems(dict(FOOT, bed_reason='no')))
        self.assertEqual(BG.sound_problems(dict(FOOT, template='stills')), [])
        self.assertEqual(BG.sound_problems(dict(FOOT, kind_news='sales')), [])
        self.assertEqual(BG.sound_problems(dict(FOOT, legal=True)), [])

    def test_cards_only_job_is_not_footage(self):
        self.assertEqual(BG.sound_problems({'shots': [['x-gfx-a.png', None, 3, None], ['art.jpg', None, 3, None]]}), [])


class Server(unittest.TestCase):
    def setUp(self):
        import render_job as RJ
        import sonic
        self.RJ, self.S = RJ, sonic
        self.tmp = tempfile.mkdtemp()
        self.keep = os.environ.get('RUNNER_TEMP')
        os.environ['RUNNER_TEMP'] = self.tmp
        self.led = os.path.join(HERE, 'assets', 'bed-ledger.json')
        self.saved = open(self.led).read() if os.path.exists(self.led) else None

    def tearDown(self):
        if self.saved is not None:
            open(self.led, 'w').write(self.saved)
        if self.keep is None:
            os.environ.pop('RUNNER_TEMP', None)
        else:
            os.environ['RUNNER_TEMP'] = self.keep

    def test_trailer(self):
        self.assertEqual(self.RJ.sound_for(dict(FOOT, track=['tr.mp4', 3.0]), 'x.mp4')[1], 'trailer')
        self.assertEqual(self.RJ.sound_for(dict(FOOT, track=['tr.mp4', 3.0], speech_keep=True), 'x.mp4')[1], 'trailer-voiced')

    def test_everyday_bed_rotates_whatever_the_job_says(self):
        a = self.RJ.sound_for({'sound': 'neon_c', 'label': 'جديد'}, 'cards/2026-11/qct-one-reel-v1.mp4')
        b = self.RJ.sound_for({'sound': 'neon_c', 'label': 'جديد'}, 'cards/2026-11/qct-two-reel-v1.mp4')
        self.assertIn(a[0], self.S.EVERYDAY)
        self.assertNotEqual(a[0], b[0])                       # rested longest first: two new posts never share a bed
        self.assertEqual(json.load(open(os.path.join(self.tmp, 'bed.json')))[0], 'qct-two-reel-v1.mp4')

    def test_chip_and_named_flavours(self):
        self.assertEqual(self.RJ.sound_for({'label': 'أرقام'}, 'y.mp4')[0], 'stats')
        self.assertEqual(self.RJ.sound_for({'label': 'جديد', 'sound': 'retro'}, 'y.mp4')[0], 'retro')
        self.assertEqual(self.RJ.sound_for({'label': 'جديد', 'tribute': True}, 'y.mp4')[0], 'neon_c')

    def test_ledger_add(self):
        p = os.path.join(self.tmp, 'b.json')
        json.dump(['qct-three-reel-v1.mp4', 'neon_d'], open(p, 'w'))
        self.S.ledger_add(p)
        self.assertEqual(json.load(open(self.led))[-1], ['qct-three-reel-v1.mp4', 'neon_d'])


class QCAndAlarm(unittest.TestCase):
    def test_sound_of_reads_the_log(self):
        d = tempfile.mkdtemp()
        log = os.path.join(d, 'r.log')
        open(log, 'w').write('x\nrender_job: sound: bed:neon_b\n')
        self.assertEqual(qc.sound_of({}, log), 'bed:neon_b')
        self.assertEqual(qc.sound_of(dict(FOOT, track=['tr.mp4', 3])), 'trailer')

    def test_three_beds_in_a_row_alarm(self):
        import workorder as W
        now = dt.datetime(2026, 11, 12, 14, 0, tzinfo=dt.timezone.utc)
        at = (now - dt.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        bed = [{'story': f's{i}', 'footage': True, 'sound': 'bed:neon', 'finished_at': at} for i in range(3)]
        self.assertEqual(len(W.bed_alarms(bed, now)), 1)
        self.assertEqual(W.bed_alarms(bed[:2] + [dict(bed[2], sound='trailer')], now), [])
        self.assertEqual(W.bed_alarms(bed + [{'story': 'chart', 'footage': False, 'sound': 'bed:stats', 'finished_at': at}], now)[0]['kind'], 'bed')


if __name__ == '__main__':
    unittest.main()
