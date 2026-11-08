"""Self-tests for the «الطريق إلى GTA VI» kit (studio-gta-vi-series, 8 Nov 2026): the countdown is computed from the
launch date, never typed; the job key is checked; the intro dispatch leaves Ocarina as it was; the new sound flavour
exists and leaves the others alone.   python3 templates/test_gta_intro.py"""
import os, sys, unittest, datetime, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gta_intro as G


class Countdown(unittest.TestCase):
    def test_launch_date(self):
        self.assertEqual(G.LAUNCH, datetime.date(2026, 11, 19))

    def test_days(self):
        self.assertEqual(G.days_for('2026-11-08'), 11)
        self.assertEqual(G.days_for('2026-11-18'), 1)
        self.assertEqual(G.days_for('2026-11-19'), 0)

    def test_days_line(self):
        self.assertEqual(G.days_line(11), 'باقي 11 يومًا')
        self.assertEqual(G.days_line(10), 'باقي 10 أيام')
        self.assertEqual(G.days_line(2), 'باقي يومان')
        self.assertEqual(G.days_line(1), 'باقي يوم واحد')
        self.assertEqual(G.days_line(0), 'متوفرة الآن')


class JobKey(unittest.TestCase):
    ok = {'series': 'gtavi', 'days': 11, 'episode': 1, 'date': '2026-11-08'}

    def test_ok(self):
        G.check(dict(self.ok))

    def test_typed_count_refused(self):
        with self.assertRaises(ValueError):
            G.check(dict(self.ok, days=12))

    def test_no_date_refused(self):
        bad = dict(self.ok); bad.pop('date')
        with self.assertRaises(ValueError):
            G.check(bad)

    def test_episode_range(self):
        with self.assertRaises(ValueError):
            G.check(dict(self.ok, episode=13))

    def test_after_launch_refused(self):
        with self.assertRaises(ValueError):
            G.check(dict(self.ok, date='2026-11-20', days=-1))


class Dispatch(unittest.TestCase):
    def test_modules(self):
        import render_job as R
        self.assertEqual(R._intro_mod({'series': 'gtavi'}).__name__, 'gta_intro')
        self.assertEqual(R._intro_mod({'series': 'ocarina', 'days': 3}).__name__, 'ocarina_intro')


class Sound(unittest.TestCase):
    def test_flavour(self):
        import sonic
        self.assertIn('gtavi', sonic.FLAVOURS)
        self.assertEqual(sonic.FLAVOURS['gtavi']['motif'], sonic.NEON['motif'])     # our own motif
        with tempfile.TemporaryDirectory() as d:
            sonic.jingle('gtavi', f'{d}/j.wav')
            self.assertGreater(os.path.getsize(f'{d}/j.wav'), 100000)


class Join(unittest.TestCase):
    def test_fallback_encode(self):
        """A stream-copy join that does not decode clean is joined again with one encode (8 Nov episode 1 failure)."""
        import subprocess, decodecheck
        with tempfile.TemporaryDirectory() as d:
            for n, secs in (('a', 1), ('b', 2)):
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=s=320x568:r=30:d={secs}',
                                '-f', 'lavfi', '-i', f'sine=d={secs}:sample_rate=48000', '-ac', '2', '-c:v', 'libx264',
                                '-preset', 'ultrafast', '-c:a', 'aac', f'{d}/{n}.mp4'], check=True)
            real, calls = decodecheck.decode_errors, []
            def fake(p, *a, **k):
                calls.append(p)
                return ['dts error'] if len(calls) == 1 else real(p, *a, **k)
            decodecheck.decode_errors = fake
            try:
                G.join(f'{d}/a.mp4', f'{d}/b.mp4', f'{d}/j.mp4')
            finally:
                decodecheck.decode_errors = real
            self.assertEqual(G.JOINED['mode'], 'encode')
            self.assertEqual(real(f'{d}/j.mp4'), [])
            n = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                                'stream=nb_read_frames', '-of', 'csv=p=0', f'{d}/j.mp4'], capture_output=True, text=True).stdout
            self.assertEqual(int(n), 90)


if __name__ == '__main__':
    unittest.main(verbosity=1)
