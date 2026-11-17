"""Coverage from production's own logs (adv-20261117-gates-fix-not-refuse F)."""
import datetime as dt, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workorder as W  # noqa: E402
import keeper as K  # noqa: E402
UTC = dt.timezone.utc


def jl(rows):
    f = tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False)
    for r in rows:
        f.write(json.dumps(r) + '\n')
    f.close()
    return f.name


class Logs(unittest.TestCase):
    def test_x_link_time(self):
        t = W.x_time('https://x.com/1748744375616643072/status/2118131742368297225')
        self.assertEqual((t.year, t.month, t.day), (2026, 11, 5))   # the post time, not the 9 Nov record time

    def test_slot_counts_once_scheduled(self):
        s = jl([{'commitment': 'c1', 'platform': 'x', 'state': 'intent', 'slot': '2026-11-17T01:05:00Z', 'labels': 'kind:news'},
                {'commitment': 'c1', 'platform': 'x', 'state': 'scheduled', 'slot': '2026-11-17T01:05:00Z'},
                {'commitment': 'c2', 'platform': 'x', 'state': 'intent', 'slot': '2026-11-17T02:05:00Z'}])
        ps = W.posts_from_logs(s, None)
        self.assertEqual([p['commitment'] for p in ps], ['c1'])

    def test_keeper_last_and_coverage(self):
        s = jl([{'commitment': 'c1', 'platform': 'x', 'state': 'scheduled', 'slot': '2026-11-17T00:05:00Z'},
                {'commitment': 'c3', 'platform': 'x', 'state': 'scheduled', 'slot': '2026-11-17T09:00:00Z'}])
        now = dt.datetime(2026, 11, 17, 0, 35, tzinfo=UTC)
        last = K.logs_last(s, None, now)
        self.assertEqual(last, dt.datetime(2026, 11, 17, 0, 5, tzinfo=UTC))    # the future slot does not count
        self.assertNotIn('GAP', K.coverage(last, now)[0])

    def test_merge_same_reel(self):
        a = {'at': dt.datetime(2026, 11, 17, 1, 0, tzinfo=UTC), 'state': 'scheduled', 'labels': {'kind:news'}}
        b = {'at': dt.datetime(2026, 11, 17, 1, 1, tzinfo=UTC), 'state': 'published', 'labels': {'tpl:split'}}
        m = W.merge_posts([a], [b])
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0]['state'], 'published')


if __name__ == '__main__':
    unittest.main()
