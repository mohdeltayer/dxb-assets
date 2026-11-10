"""Tests for the one-render-per-Reel pieces (adv-20261110-one-render-per-reel A, B, C, G)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textrules as TR      # noqa: E402
import jobpath as JP        # noqa: E402
import jobsha as JS         # noqa: E402
import shotpick as SP       # noqa: E402

JOB = {'name': 'x', 'headline': 'لعبة Warhammer Survivors\nمتوفرة الآن', 'label': 'متوفر الآن',
       'shots': [['a.mp4', 0, 4.0, 0.5], ['a.mp4', 5, 3.0, 0.5], ['a.mp4', 9, 3.0, 0.5]],
       'lines': [[1, 1, ['على الحاسب وPS5']], [2, 2, ['خصم 10% حتى الأحد', 'Steam قبل أي منصة']]],
       'gfx': [{'note': 'بعد خصم الإطلاق 10%'}], 'credits': [[0, 2, 'المصدر: فوكس']]}


class Rules(unittest.TestCase):
    def test_all_errors_at_once(self):
        fs = TR.check(JOB)
        rules = sorted({(f['where'].split()[0], f['rule']) for f in fs})
        for want in [('headline', 'headline_long'), ('line', 'glued'), ('line', 'sign'), ('line', 'latin_first'),
                     ('gfx', 'sign'), ('line', 'reading')]:
            self.assertIn(want, rules)
        self.assertTrue(all(f['rule'] != 'headline_long' for f in TR.hard(fs)))   # an estimate never stops

    def test_clean(self):
        ok = dict(JOB, headline='متوفرة الآن', lines=[[1, 2, ['على الحاسب و PS5']]], gfx=[])
        self.assertEqual(TR.hard(TR.check(ok)), [])

    def test_strip_line_cap(self):
        j = dict(JOB, strip=[['السعر', '20 دولارًا']], lines=[[0, 2, ['سطر\nثان\nثالث']]], gfx=[])
        self.assertIn('line_count', {f['rule'] for f in TR.check(j)})


class Autofix(unittest.TestCase):
    def test_mechanical_only(self):
        new, ch = TR.fix(JOB)
        self.assertEqual({c['what'] for c in ch} >= {'space after a glued prefix', 'percent sign spelt out'}, True)
        rules = {f['rule'] for f in TR.hard(TR.check(new))}
        self.assertNotIn('glued', rules); self.assertNotIn('sign', rules)
        self.assertIn('latin_first', rules)          # a Latin-first line needs a writer, never the server


class Paths(unittest.TestCase):
    def test_name_or_path(self):
        d = tempfile.mkdtemp()
        os.makedirs(f'{d}/jobs/live'); open(f'{d}/jobs/live/a.json', 'w').write('{}')
        self.assertEqual(JP.resolve('live', 'a', d), 'jobs/live/a.json')
        self.assertEqual(JP.resolve('live', 'a.json', d), 'jobs/live/a.json')
        self.assertEqual(JP.resolve('live', 'jobs/live/a.json', d), 'jobs/live/a.json')
        for bad in ('../a', 'jobs/render/a.json', 'b'):
            with self.assertRaises(ValueError):
                JP.resolve('live', bad, d)


class Versions(unittest.TestCase):
    def test_older_version_refused(self):
        e = [{'story': 's', 'job_sha': 'aaa'}, {'story': 's', 'job_sha': 'bbb'}]
        self.assertIsNotNone(JS.check('s', 'aaa', e))
        self.assertIsNone(JS.check('s', 'bbb', e))
        self.assertIsNone(JS.check('s', 'ccc', e))
        self.assertEqual(JS.count('s', [{'story': 's'}] * 2), 3)


class Picker(unittest.TestCase):
    def test_subtract(self):
        self.assertEqual(SP._subtract(0, 10, [(2, 3, 'x')]), [(0, 1.85), (3.15, 10)])


if __name__ == '__main__':
    unittest.main()
