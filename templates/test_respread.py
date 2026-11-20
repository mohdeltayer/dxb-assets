"""respread: never the same moment twice (20 Nov 2026, Ace Combat 8 and GTA VI CDPR)."""
import unittest
import render_job as RJ
import autoshots as AS


class Respread(unittest.TestCase):
    def setUp(self):
        self._dur = RJ._video_dur
        RJ._video_dur = lambda f: {'a.mp4': 120.0, 'b.mp4': 60.0, 'short.mp4': 8.0}.get(f, 0.0)
        AS.READ.clear()

    def tearDown(self):
        RJ._video_dur = self._dur

    def job(self, shots, files=('a.mp4',)):
        return {'footage': [{'file': f} for f in files], 'shots': shots}

    def test_repeated_moments_spread(self):
        j = self.job([['a.mp4', 20.43, 3.6, None]] + [['a.mp4', 3.07, 2.3, None] for _ in range(12)])
        moved = RJ.respread(j)
        self.assertEqual(len(moved), 11)
        starts = [s[1] for s in j['shots']]
        self.assertEqual(len(set(starts)), 13)
        iv = sorted((s[1], s[1] + s[2]) for s in j['shots'])
        for (a, b), (c, d) in zip(iv, iv[1:]):
            self.assertLessEqual(b - c, RJ.RESPREAD_OVERLAP)

    def test_spread_job_untouched(self):
        j = self.job([['a.mp4', 10, 2.5, None], ['a.mp4', 20, 2.5, None], ['a.mp4', 30, 2.5, None]])
        self.assertEqual(RJ.respread(j), [])
        self.assertEqual([s[1] for s in j['shots']], [10, 20, 30])

    def test_short_file_overflows_to_spare(self):
        j = self.job([['short.mp4', 0.5, 2.2, None]] + [['short.mp4', 0.5, 2.2, None] for _ in range(6)],
                     files=('short.mp4', 'b.mp4'))
        RJ.respread(j)
        keys = [(s[0], s[1]) for s in j['shots']]
        self.assertEqual(len(set(keys)), 7)
        self.assertIn('b.mp4', [s[0] for s in j['shots']])


if __name__ == '__main__':
    unittest.main()
