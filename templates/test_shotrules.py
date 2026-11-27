"""Shot rules (Mohammad, 27 Nov 2026): blocked stretches, shot matches line, fill not band. Autofix only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocked as B          # noqa: E402
import subjectmatch as SM    # noqa: E402

LAUNCH = {'file': 'gta6-launch-master.mp4', 'repo': 'live/2026-11-20/gta6-launch-1080.mp4'}


def job(shots, footage=None, **kw):
    j = {'game': 'Grand Theft Auto VI', 'footage': footage or [dict(LAUNCH)], 'shots': shots, 'headline': 'x', 'lines': []}
    j.update(kw)
    return j


class Ledger(unittest.TestCase):
    def test_launch_copy_resolves(self):
        k, off = B.key_for(job([]), 'gta6-launch-master.mp4')
        self.assertEqual((k, off), ('gtavi-launch-trailer', 0.0))

    def test_stream_copy_offset(self):
        j = job([], [{'file': 'gtavi-trailer-2-from-120.mp4', 'stream': True, 'start': 120.0,
                      'url': 'https://media-rockstargames-com.akamaized.net/VI/downloads/videos/GTAVI_Trailer_2/GTAVI_Trailer_2.mp4'}])
        k, off = B.key_for(j, 'gtavi-trailer-2-from-120.mp4')
        self.assertEqual((k, off), ('gtavi-trailer-2', 120.0))
        rs = B.ranges(j, 'gtavi-trailer-2-from-120.mp4')
        self.assertTrue(any(a < 3.5 < b for a, b, _ in rs))          # the bed kiss at 122.8 s is 2.8 s into the copy

    def test_shower_hit(self):
        j = job([])
        self.assertTrue(B.hit(j, 'gta6-launch-master.mp4', 42.8, 2.2))   # car-physics Reel, 27 Nov
        self.assertIsNone(B.hit(j, 'gta6-launch-master.mp4', 50.3, 2.2))

    def test_unknown_file(self):
        self.assertEqual(B.ranges(job([], [{'file': 'other.mp4'}]), 'other.mp4'), [])

    def test_split(self):
        out = B.split([{'start': 30.0, 'end': 50.0}], [(36.0, 39.0, 'x'), (43.2, 47.0, 'y')])
        self.assertEqual([(s['start'], s['end']) for s in out], [(30.0, 36.0), (39.0, 43.2), (47.0, 50.0)])


class Clear(unittest.TestCase):
    def test_moves_off_and_keeps_others(self):
        shots = [['gta6-launch-master.mp4', 57.15, 2.4, None], ['gta6-launch-master.mp4', 42.8, 2.2, None],
                 ['gta6-launch-master.mp4', 36.55, 2.2, None], ['gta6-launch-master.mp4', 50.3, 2.2, None]]
        j = job(shots)
        steps = []
        moved = B.clear(j, dur_of=lambda f: 89.0, frame_ok=None, ladder=lambda *a: steps.append(a))
        self.assertEqual(moved, [1, 2])
        for sh in j['shots']:
            self.assertIsNone(B.hit(j, sh[0], sh[1], sh[2]), sh)
        self.assertEqual(j['shots'][0][1], 57.15)
        self.assertTrue(all(s[0] == 'picture' for s in steps))

    def test_never_refuses_when_nothing_free(self):
        j = job([['gta6-launch-master.mp4', 43.5, 2.0, None]])
        moved = B.clear(j, dur_of=lambda f: 0.0, frame_ok=lambda *a: (False, 'x'))
        self.assertEqual(moved, [0])
        self.assertIsNone(B.hit(j, *j['shots'][0][:3]))

    def test_still_fallback(self):
        j = job([['gta6-launch-master.mp4', 43.5, 2.0, None]], [dict(LAUNCH), {'file': 'gta-key-art.jpg'}])
        B.clear(j, dur_of=lambda f: 0.0, frame_ok=lambda *a: (False, 'x'))
        self.assertEqual(j['shots'][0][0], 'gta-key-art.jpg')


class Words(unittest.TestCase):
    def test_vehicle(self):
        cls, named = SM.wants('فيزياء القيادة في اللعبة', {})
        self.assertIn('vehicle', cls)

    def test_named(self):
        _c, subj = __import__('variety').curated('GTA VI')
        cls, named = SM.wants('لوسيا تقود السيارة', subj)
        self.assertIn('lucia', named)
        self.assertIn('vehicle', cls)

    def test_none(self):
        self.assertEqual(SM.wants('روكستار تؤكد الموعد', {}), (set(), set()))

    def test_line_text(self):
        j = {'headline': 'H', 'lines': [[1, 2, [['سطر', {}]]]]}
        self.assertEqual(SM.line_text(j, 0), 'H')
        self.assertEqual(SM.line_text(j, 2), 'سطر')

    def test_curated_has_no_blocked(self):
        cur, _ = __import__('variety').curated('GTA VI')
        for s in cur:
            self.assertIsNone(B.hit({}, s['file'], float(s['start']), float(s['secs'])), s['label'])


if __name__ == '__main__':
    unittest.main()
