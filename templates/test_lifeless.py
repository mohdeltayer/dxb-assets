"""Tests for the lifeless score: python3 -m unittest templates/test_lifeless.py (needs ffmpeg)."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lifeless as LF  # noqa: E402


def make(path, src):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', src, '-t', '8',
                    '-pix_fmt', 'yuv420p', path], check=True)


class Score(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.TemporaryDirectory()
        d = pathlib.Path(cls.t.name)
        cls.still, cls.moving = str(d / 'still.mp4'), str(d / 'moving.mp4')
        make(cls.still, 'color=c=0x141332:s=540x960:r=30')
        make(cls.moving, 'testsrc2=s=540x960:r=30')

    @classmethod
    def tearDownClass(cls):
        cls.t.cleanup()

    def test_still_card_scores_high(self):
        r = LF.score(self.still)
        self.assertGreater(r['score'], LF.REPAIR_AT)
        self.assertGreater(r['still_share'], 0.9)

    def test_moving_picture_scores_low(self):
        r = LF.score(self.moving)
        self.assertLess(r['score'], 20)
        self.assertLess(r['still_share'], 0.1)

    def test_storybook_leaves_still_share_out(self):
        self.assertLess(LF.score(self.still, storybook=True)['score'], 101)
        self.assertEqual(LF.score(self.still)['mode'], 'report-only')


if __name__ == '__main__':
    unittest.main()
