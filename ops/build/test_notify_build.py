"""python3 -m unittest ops/build/test_notify_build.py (no network)."""
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import notify_build as N  # noqa: E402


class Msg(unittest.TestCase):
    def note(self, text):
        f = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False)
        f.write(text); f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_released_with_skips(self):
        p = self.note('# R\n## Merged\n- Credit check (card x): stuff\n- Download automation: more\n'
                      '## Skipped\n- dxb-ops cutover (card y): waits\n')
        m = N.release_message(p)
        self.assertIn('Build released', m)
        self.assertIn('Credit check; Download automation', m)
        self.assertIn('skipped: dxb-ops cutover', m)

    def test_skipped_night(self):
        m = N.release_message(self.note('# R\n## Merged\n## Skipped\n- Everything: the server was down\n'))
        self.assertTrue(m.startswith('Build skipped'))
        self.assertIn('Everything', m)

    def test_dry_run_sends_nothing(self):
        os.environ['NOTIFY_DRY_RUN'] = '1'
        self.assertTrue(N.main(['test']))


if __name__ == '__main__':
    unittest.main()
