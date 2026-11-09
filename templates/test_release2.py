"""Tests for build 9 Nov release 2: python3 -m unittest templates/test_release2.py (from the repo root; DUBAI_FONTS may
point at stand-in fonts). The showcase layout's look is checked on a draft render, not here."""
import json, os, pathlib, sys, tempfile, unittest

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildgate as BG  # noqa: E402
import fillcheck as FC  # noqa: E402
import looks  # noqa: E402
import reel  # noqa: E402


class Showcase(unittest.TestCase):
    def test_reason(self):
        self.assertIsNone(reel.showcase_reason(None))
        for bad in (True, 'trailer', 'it looks nicer this way today'):
            with self.assertRaises(ValueError):
                reel.showcase_reason(bad)
        self.assertTrue(reel.showcase_reason('the news is the trailer itself: Trailer 3'))
        self.assertTrue(reel.showcase_reason('720p only: IGN, publisher site, Steam checked'))

    def test_box_fits_between_bands(self):
        x, y, w, h, lift = reel.showcase_box(560, facts=True)
        self.assertLessEqual(w, reel.W)
        self.assertEqual(x, (reel.W - w) // 2)
        self.assertGreaterEqual(y, 560 + reel.SHOW_GAP)
        self.assertAlmostEqual(w / h, 16 / 9, delta=0.02)
        last = reel.G.SAFE_BOTTOM - 40 - lift
        self.assertLess(y + h, last - reel.SHOW_LINE[1] - reel.SHOW_LINE[0] + 1)   # picture above two lines
        with self.assertRaises(ValueError):
            reel.showcase_box(900, facts=True)                                     # a three-line headline leaves no room

    def test_quality_gate_boxed_skips_enlargement(self):
        self.assertEqual(reel.quality_gate([], None, None, boxed=True), {})


class Looks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.keep = looks.LEDGER
        looks.LEDGER = os.path.join(self.tmp.name, 'l.json')
        rows = [{'name': 'a', 'theme': 'cold', 'style': 'glow', 'at': '2026-11-09T01:00:00Z'},
                {'name': 'b', 'theme': 'cold', 'style': 'glow', 'at': '2026-11-09T02:00:00Z'}]
        json.dump(rows, open(looks.LEDGER, 'w'))

    def tearDown(self):
        looks.LEDGER = self.keep
        self.tmp.cleanup()

    def test_third_style_is_swapped(self):
        style, problems = looks.resolve({'name': 'c', 'theme': 'playful', 'style': 'glow'})
        self.assertNotEqual(style, 'glow')
        self.assertEqual(problems, [])

    def test_third_theme_stops(self):
        _, problems = looks.resolve({'name': 'c', 'theme': 'cold', 'style': 'bold'})
        self.assertTrue(problems and 'third in a row' in problems[0])

    def test_rerender_replaces_its_row(self):
        looks.record({'out': 'cards/2026-11/b-reel-v2.mp4', 'theme': 'gold'}, 'lines', at='2026-11-09T03:00:00Z')
        rows = json.load(open(looks.LEDGER))
        self.assertEqual([r['name'] for r in rows], ['a', 'b'])
        self.assertEqual(rows[-1]['theme'], 'gold')


class Gate(unittest.TestCase):
    def test_numbers_ground(self):
        sh = [['x-gfx-a.png', 0, 3, None], ['t.mp4', 1, 3, None]]
        self.assertTrue(BG.ground_problems({'shots': sh}))
        self.assertEqual(BG.ground_problems({'shots': sh, 'ground_still': 'art.jpg'}), [])
        self.assertEqual(BG.ground_problems({'shots': sh, 'ground_footage': ['t.mp4', 4]}), [])
        self.assertTrue(BG.ground_problems({'shots': sh, 'ground': 'rotate'}))
        self.assertTrue(BG.ground_problems({'shots': sh, 'ground': 'rotate', 'ground_reason': 'ten games, one chart each'}))  # refused since 10 Nov

    def test_plate_cover(self):
        self.assertTrue(BG.plate_cover_problems({'shots': [['gta6-logo-plate.png', None, 3, None]]}))
        self.assertEqual(BG.plate_cover_problems({'shots': [['gta6-key-art.jpg', None, 3, None]]}), [])

    def test_cover_still_ground_counts(self):
        self.assertEqual(BG.cover_problems({'shots': [['x-gfx-a.png', 0, 3, None]], 'ground_still': 'a.jpg'}), [])

    def test_layout(self):
        self.assertTrue(BG.layout_problems({'layout': 'showcase'}))
        self.assertEqual(BG.layout_problems({'layout': 'showcase', 'showcase_reason': 'the news is the trailer itself: Trailer 3'}), [])


class EmptyBand(unittest.TestCase):
    def test_empty_run(self):
        img = np.full((480, 270), 20, np.float32)          # all flat ground
        rng = np.random.default_rng(1)
        img[100:250] = rng.integers(0, 255, (150, 270))    # picture rows 400 to 1000
        h, top = FC.empty_run(img)
        self.assertEqual(top, 1000)                         # from the picture's bottom to the safe bottom
        self.assertEqual(h, 1480 - 1000)
        img[260:360:6] = rng.integers(0, 255, (17, 270))   # text rows every 24 px in the bottom band
        self.assertLessEqual(FC.empty_run(img)[0], FC.EMPTY_MAX)

    def test_persisted(self):
        self.assertTrue(FC._persisted({'persist': {'head': [[0, 3]]}}, 2))
        self.assertFalse(FC._persisted({'persist': {'head': [[0, 1]]}}, 2))
        self.assertFalse(FC._persisted({}, 0))


if __name__ == '__main__':
    unittest.main()
