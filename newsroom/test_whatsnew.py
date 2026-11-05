"""Tests for the what-is-new packet: python3 -m unittest newsroom/test_whatsnew.py (no network)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import whatsnew as W  # noqa: E402


class WN(unittest.TestCase):
    def test_overlap_weighs_numbers(self):
        self.assertGreater(W.overlap('Sales passed 4.7 million units', 'Astro Bot sales passed 4.7 million'), 0.7)
        self.assertLess(W.overlap('Sales passed 4.7 million units', 'Nintendo announced a Direct'), 0.3)

    def test_mark_posted_known_new(self):
        known = [('Astro Bot sales passed 4.7 million', 's1', True), ('Team Asobi hiring for a new project', 's2', False)]
        out, how = W.mark(['Astro Bot sales passed 4.7 million units worldwide',
                           'Team Asobi is hiring for a new project in Tokyo',
                           'A sequel was announced for 2027 on PS5'], known)
        self.assertEqual([v for _, v, _, _ in out], ['posted', 'known', 'new'])
        self.assertEqual(how, 'word overlap')

    def test_sentences(self):
        self.assertEqual(len(W.sentences('First sentence is long enough here. Second one is also long enough.\nok')), 2)


if __name__ == '__main__':
    unittest.main()
