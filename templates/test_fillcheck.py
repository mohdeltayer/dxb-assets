"""Fill check tests (adv-20261030-one-piece-fortnite-hold, adv-20261107-band-layout-drift): synthetic picture tracks."""
import os
import subprocess
import tempfile
import unittest

import fillcheck as FC


def make(path, band=True, secs=8):
    """A 1080x1920 portrait clip: moving test footage, either at 1080x1200 under a flat indigo band (the band layout)
    or filling the frame."""
    if band:
        vf = 'scale=1080:1200,pad=1080:1920:0:720:color=0x141332'
    else:
        vf = 'scale=1080:1920'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=size=1280x720:rate=10:duration={secs}',
                    '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', path], check=True)


class Band(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        make(os.path.join(cls.d, 'band.mp4'), band=True)
        make(os.path.join(cls.d, 'full.mp4'), band=False)

    def job(self, f, **kw):
        j = {'template': 'trailer', 'shots': [[f, 0.0, 3.4, 0.5], [f, 3.4, 4.0, 0.5]]}
        j.update(kw)
        return j

    def test_band_after_headline_refused(self):
        with self.assertRaises(ValueError) as e:
            FC.check(self.job('band.mp4'), self.d)
        self.assertIn('band layout', str(e.exception))
        self.assertIn('shot 1', str(e.exception))

    def test_a_note_without_sources_does_not_count(self):
        with self.assertRaises(ValueError):
            FC.check(self.job('band.mp4', lowres_ok='1080p Steam trailer, crop enlargement 1.2x'), self.d)

    def test_weak_source_named_passes(self):
        FC.check(self.job('band.mp4', lowres_ok={'searched': ['IGN', 'publisher press site'], 'result': 'none above 720p'}), self.d)
        FC.check(self.job('band.mp4', lowres_ok='IGN, Nintendo store, Steam: none above 720p'), self.d)

    def test_band_only_under_the_headline_passes(self):
        FC.check({'template': 'trailer', 'shots': [['band.mp4', 0.0, 3.4, 0.5], ['full.mp4', 3.4, 4.0, 0.5]]}, self.d)

    def test_full_frame_passes(self):
        FC.check(self.job('full.mp4'), self.d)

    def test_fill_ok_and_storybeat(self):
        FC.check(self.job('band.mp4', fill_ok=[['band.mp4', 3.4, 'looked at the frames, page layout']]), self.d)
        FC.check(self.job('band.mp4', template='storybeat'), self.d)

    def test_weak_source_forms(self):
        self.assertIsNone(FC.weak_source(None))
        self.assertIsNone(FC.weak_source('1080p Steam trailer, crop enlargement 1.2x'))
        self.assertIsNone(FC.weak_source(['IGN']))
        self.assertTrue(FC.weak_source(['IGN', 'Steam']))
        self.assertTrue(FC.weak_source({'searched': ['IGN', 'Steam'], 'result': 'none above 720p'}))
        self.assertIsNone(FC.weak_source({'searched': ['IGN'], 'result': 'x'}))


if __name__ == '__main__':
    unittest.main()
