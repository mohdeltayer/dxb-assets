"""Tests for the backstory pages: python3 -m unittest newsroom/test_context.py (no network)."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import context as C  # noqa: E402


class Ctx(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        d = pathlib.Path(self.t.name)
        self.keep = (C.STORIES, C.PAGES)
        C.STORIES, C.PAGES = d / 's', d / 'p'
        C.STORIES.mkdir(); C.PAGES.mkdir()
        (C.STORIES / '2026-11-05-zelda-x.json').write_text(json.dumps(
            {'id': '2026-11-05-zelda-x', 'title': 'Ocarina of Time out now', 'game': 'The Legend of Zelda: Ocarina of Time',
             'companies': ['Nintendo'], 'chip': 'رسمي', 'template': 'trailer', 'status': 'published'}))
        (C.PAGES / 'zelda.md').write_text('# The Legend of Zelda\n\n## Log (one line per published post, added by presubmit.py published)\n')

    def tearDown(self):
        C.STORIES, C.PAGES = self.keep
        self.t.cleanup()

    def test_match(self):
        s = json.loads((C.STORIES / '2026-11-05-zelda-x.json').read_text())
        self.assertEqual(set(C.matches(s)), {'zelda', 'nintendo'})

    def test_append_once(self):
        self.assertEqual(C.append('2026-11-05-zelda-x'), ['zelda'])      # no nintendo page here
        self.assertEqual(C.append('2026-11-05-zelda-x'), [])
        self.assertEqual((C.PAGES / 'zelda.md').read_text().count('2026-11-05-zelda-x'), 1)

    def test_label_guard(self):
        self.assertTrue(C.label_ok('Capcom', 'Capcom'))
        self.assertFalse(C.label_ok('Capcom', 'Konami'))


if __name__ == '__main__':
    unittest.main()
