"""Trailer news shows the new trailer (Mohammad, 28 Nov 2026)."""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import newfootage as NF   # noqa: E402


class Dates(unittest.TestCase):
    def test_steam_stamp(self):
        u = 'https://video.akamai.steamstatic.com/store_trailers/1030300/970174968/f2c5/1755841475/hls_264_master.m3u8?t=1764916585'
        self.assertEqual(NF._ts_in_path(u), dt.date(2025, 8, 22))

    def test_dated_url(self):
        self.assertEqual(NF._date_in_path('https://assets.ign.com/videos/zencoder/2025/05/06/3840/x.mp4'), dt.date(2025, 5, 6))

    def test_published(self):
        self.assertEqual(NF.file_date({'published': '2026-11-27'})[0], dt.date(2026, 11, 27))


class Kind(unittest.TestCase):
    def test_update_and_words(self):
        self.assertTrue(NF.about_new({'kind_news': 'update'}))
        self.assertTrue(NF.about_new({'headline': 'توسعة مجانية جديدة'}))
        self.assertFalse(NF.about_new({'kind_news': 'sales', 'headline': 'مبيعات اليابان'}))


class Fix(unittest.TestCase):
    def job(self):
        return {'name': 'x', 'story': '2026-11-27-x', 'kind_news': 'update',
                'footage': [{'file': 'old.mp4', 'published': '2025-08-22'}],
                'shots': [['old.mp4', 3.0, 3.8, None], ['old.mp4', 9.0, 2.5, None]],
                'credits': [[0, 1, 'المصدر: Famitsu · اللقطات: صفحة اللعبة على Steam', {}]], 'track': ['old.mp4', 3.0]}

    def test_stale(self):
        self.assertEqual([f for f, _d, _h in NF.stale(self.job())], ['old.mp4'])
        j = self.job()
        j['footage'][0]['published'] = '2026-11-27'
        self.assertEqual(NF.stale(j), [])

    def test_stills_step(self):
        j = self.job()
        NF.stills = lambda job, story, upath, n=3: [('x-newart-0.jpg', 'https://example.com/a')]
        steps = []
        self.assertEqual(NF.fix(j, '/tmp', None, None, lambda *a: steps.append(a)), 'b')
        self.assertTrue(all(sh[0] == 'x-newart-0.jpg' and sh[1] is None for sh in j['shots']))
        self.assertIn('صورة رسمية للمحتوى الجديد', j['credits'][0][2])
        self.assertTrue(j['credits'][0][2].startswith('المصدر: Famitsu'))
        self.assertIsNone(j['track'])

    def test_old_named(self):
        j = self.job()
        NF.stills = lambda job, story, upath, n=3: []
        self.assertEqual(NF.fix(j, '/tmp', None, None), 'c')
        self.assertIn('من اللعبة الأساسية', j['credits'][0][2])
        self.assertEqual(j['shots'][0][0], 'old.mp4')


if __name__ == '__main__':
    unittest.main()
