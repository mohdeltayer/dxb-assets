"""The footage scan never hangs a render (20 Nov 2026): capped in a child, the job comes back or stays as it was."""
import os, sys, tempfile, time, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scanproxy as SP
import autoshots as AS


def _slow(job):
    time.sleep(30)
    job['changed'] = True


def _quick(job):
    job['shots'][0][1] = 12.5


class Scan(unittest.TestCase):
    def test_cap_stops_and_keeps_job(self):
        up = tempfile.mkdtemp()
        job = {'shots': [['a.mp4', 3.0, 2.2, None]]}
        t = time.time()
        self.assertFalse(SP.capped(_slow, job, uploads=up, secs=2))
        self.assertLess(time.time() - t, 10)
        self.assertNotIn('changed', job)

    def test_finished_scan_returns_job(self):
        up = tempfile.mkdtemp()
        job = {'shots': [['a.mp4', 3.0, 2.2, None]]}
        self.assertTrue(SP.capped(_quick, job, uploads=up, secs=20))
        self.assertEqual(job['shots'][0][1], 12.5)
        self.assertFalse(os.path.exists(os.path.join(up, 'scanproxy')))

    def test_cap_for(self):
        self.assertEqual(SP.cap_for({'shots': [['a.mp4', 0, 2]]}), 180)
        self.assertEqual(SP.cap_for({'shots': [['a.mp4', 0, 2], ['b.mp4', 0, 2]]}), 300)
        self.assertEqual(SP.cap_for({'shots': [[f'{i}.mp4', 0, 2] for i in range(5)]}), 300)

    def test_stale_slots_keep_typed_starts(self):
        job = {'shots': [['a.mp4', 26.45, 3.8, None], ['a.mp4', 0.0, 2.2, None], ['a.mp4', 'auto', 2.2, None]],
               'shots_auto': [0, 1]}
        self.assertEqual(AS.expand(job), [1, 2])
        self.assertEqual(job['shots'][0][1], 26.45)
        job2 = {'shots': [['a.mp4', 26.45, 3.8, None]], 'shots_auto': [0]}
        self.assertEqual(AS.expand(job2), [])
        self.assertNotIn('shots_auto', job2)


if __name__ == '__main__':
    unittest.main()
