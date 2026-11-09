"""opsdata tests (adv-20261108-stories-tab): feed, published, stale, stories, on synthetic Publer exports, cards, board
and commitments. Run: python3 -m unittest discover -s ops/backoffice/dispatch -p 'test_*.py'"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import opsdata as O  # noqa: E402

NOW = datetime(2026, 11, 9, 3, 20, tzinfo=timezone.utc)       # 07:20 Dubai


def rd(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def post(ch, when, caption, labels, pid=None, url=None):
    p = {'ref': {'n': 0}, 'caption': caption, 'channel': ch, 'account': 'The DIGI-Lounge', 'format': 'Video',
         'status': 'Published', 'when': when, 'published_url': url or 'https://example.test/%s/%s' % (ch, caption[:4]),
         'labels': labels}
    if pid:
        p['ref']['id'] = pid
    return p


L1 = ['tpl:trailer', 'skin:house', 'sound:trailer', 'genre:shooter']
L2 = ['tpl:numbers', 'skin:house', 'sound:our bed', 'genre:industry/hardware']
PUBLISHED = {'posts': [
    post('Instagram', 'Mon, Nov 9 at 6:31 AM UTC+4', 'BONK story\nmore', L1, 'aaaaaaaaaaaaaaaaaa5dfd9d', 'https://ig.test/reel/AAA111/'),
    post('X (Twitter)', 'Mon, Nov 9 at 6:31 AM UTC+4', 'BONK short', L1, 'bbbbbbbbbbbbbbbbbbbbbbbb', 'https://x.test/status/9'),
    post('Threads', 'Mon, Nov 9 at 6:32 AM UTC+4', 'BONK threads', L1, None, 'https://th.test/post/CCC333'),
    post('Threads', 'Mon, Nov 9 at 6:32 AM UTC+4', 'BONK threads', L1, None, 'https://th.test/post/CCC333'),   # a repeat
    post('Instagram', 'Sun, Nov 8 at 11:31 PM UTC+4', 'Konami numbers', L2, None, 'https://ig.test/reel/Dffg0NYFDcc/'),
    post('Threads', 'Sun, Nov 8 at 11:32 PM UTC+4', 'Konami threads', L2, None, 'https://th.test/post/K2'),
    post('Instagram', 'Fri, Nov 6 at 10:00 AM UTC+4', 'Too old', L2, None, 'https://ig.test/reel/OLD/'),
]}
SCHEDULED = {'posts': [
    post('Instagram', 'Mon, Nov 9 at 8:30 AM UTC+4', 'Next one\nbody', L1, None, None),
    post('Instagram', 'Mon, Nov 9 at 10:00 AM UTC+4', 'Later one', L1, None, None),
]}
KEEPER = {'generated_at': '2026-11-09T03:15:00Z', 'bank_ready': 11, 'rows': [],
          'alarms_now': [{'title': 'Publication unconfirmed: BONK'}, {'title': 'Publication unconfirmed: BONK'}]}


class Publer(unittest.TestCase):
    def test_when_forms(self):
        self.assertEqual(O.iso(O.parse_when('Sun, Nov 8 at 7:17 AM UTC+4', NOW)), '2026-11-08T03:17:00Z')
        self.assertEqual(O.iso(O.parse_when('Sun, Nov 8 at 12:05 AM UTC+4', NOW)), '2026-11-07T20:05:00Z')
        self.assertEqual(O.iso(O.parse_when('Mon 09 Nov 06:30 Dubai (02:30Z)', NOW)), '2026-11-09T02:30:00Z')
        self.assertEqual(O.iso(O.parse_when('2026-11-09T02:30:00Z', NOW)), '2026-11-09T02:30:00Z')

    def test_groups_one_reel_per_three_posts_and_drops_repeats(self):
        g = O.group_reels(O.publer_posts(PUBLISHED), NOW)
        self.assertEqual([sorted(x['posts']) for x in g], [['instagram'], ['instagram', 'threads'],
                                                           ['instagram', 'threads', 'x']])


class Published(unittest.TestCase):
    def test_last_48_hours_ids_and_fields(self):
        docs = O.published_docs(PUBLISHED, NOW)
        self.assertEqual([d['doc_id'] for d in docs], ['uNYFDcc', '5dfd9d'])     # the six-day-old Reel is out
        b = docs[1]['data']
        self.assertEqual(b['platforms'], ['instagram', 'x', 'threads'])
        self.assertEqual((b['template'], b['sound'], b['title']), ('trailer', 'trailer', 'BONK story'))
        self.assertEqual(b['published_at'], '2026-11-09T02:31:00Z')
        self.assertNotIn('thumb', b)
        for d in docs:
            self.assertLessEqual(len(d['doc_id']), 7)

    def test_existing_rows_are_not_duplicated_and_same_id_is_pinned(self):
        ex = {'2026-11-08-konami': (1, {'links': {'instagram': 'https://ig.test/reel/Dffg0NYFDcc/'}}),
              '5dfd9d': (3, {'title': 'old'})}
        docs = O.published_docs(PUBLISHED, NOW, existing=ex)
        self.assertEqual([(d['doc_id'], d.get('if_version')) for d in docs], [('5dfd9d', 3)])
        same = {'5dfd9d': (4, O.published_docs(PUBLISHED, NOW)[1]['data'])}
        self.assertNotIn('5dfd9d', [d['doc_id'] for d in O.published_docs(PUBLISHED, NOW, existing=same)])


class Feed(unittest.TestCase):
    def test_feed_document(self):
        f = O.feed_doc(KEEPER, {'rows': []}, SCHEDULED, PUBLISHED, NOW)
        self.assertEqual(f['last_post'], 'BONK story')
        self.assertEqual(f['last_post_at'], '2026-11-09T02:31:00Z')
        self.assertEqual(f['gap_min'], 49)
        self.assertEqual(f['gap_rule_min'], 120)                    # 07:20 Dubai: the overnight rule until 08:00
        self.assertEqual(f['next_slot'], '08:30 Dubai · Next one')
        self.assertEqual(f['posts_today'], 1)                       # Konami was 8 Nov Dubai
        self.assertEqual(f['bank_ready'], 11)
        self.assertEqual(f['alarms'], ['Publication unconfirmed: BONK'])
        self.assertEqual(f['written_at'], '2026-11-09T03:20:00Z')

    def test_night_rule_and_commitments_fallback(self):
        night = datetime(2026, 11, 9, 1, 0, tzinfo=timezone.utc)   # 05:00 Dubai
        rows = {'rows': [{'id': 'r1', 'title': 'Row story', 'slot': 'Mon 09 Nov 06:30 Dubai (02:30Z)',
                          'status': 'scheduled in Publer for 06:30 Dubai', 'held_by_mohammad': False},
                         {'id': 'r2', 'title': 'Held', 'slot': 'Mon 09 Nov 06:00 Dubai', 'status': 'scheduled',
                          'held_by_mohammad': True}]}
        f = O.feed_doc({}, rows, None, None, night)
        self.assertEqual(f['gap_rule_min'], 120)
        self.assertEqual(O.feed_doc({}, rows, None, None, NOW.replace(hour=5))['gap_rule_min'], 60)   # 09:00 Dubai
        self.assertEqual(f['next_slot'], '06:30 Dubai · Row story')
        self.assertIsNone(f['last_post_at'])
        self.assertIsNone(f['bank_ready'])


class Stale(unittest.TestCase):
    def test_week_old_cards_close_done_ones_stay(self):
        t = tempfile.mkdtemp()
        cards = {'old-open': {'status': 'open', 'created_at': '2026-10-30T00:00:00Z'},
                 'old-answered-recent-answer': {'status': 'answered', 'created_at': '2026-10-20T00:00:00Z',
                                                'answer': {'at': '2026-11-05T00:00:00Z'}},
                 'old-done': {'status': 'done', 'created_at': '2026-10-01T00:00:00Z'},
                 'old-progress': {'status': 'answered', 'created_at': '2026-10-20T00:00:00Z',
                                  'updated_at': '2026-11-01T00:00:00Z'}}
        for k, v in cards.items():
            json.dump(dict(v, id=k), open(os.path.join(t, k + '.json'), 'w'))
        wb = O.stale_writebacks(t, NOW)
        self.assertEqual(sorted(w['id'] for w in wb), ['old-open', 'old-progress'])
        self.assertEqual(wb[0]['fields']['status'], 'done')
        self.assertEqual(wb[0]['fields']['outcome'], 'auto-closed, stale')


BOARD = {'handoffs': [
    {'id': 'mohammad-story', 'from': 'Production 1 (relaying Mohammad)', 'to': 'Production 2',
     'at': '2026-11-09T02:00:00Z', 'done': 'Mohammad wants this story', 'evidence': 'card adv-20261108-stories-tab'},
    {'id': 'studio-ep', 'from': 'Production 1 (studio)', 'to': 'Production 2', 'at': '2026-11-08T10:00:00Z',
     'done': 'episode built'},
    {'id': 'p2-ack', 'from': 'production-2', 'to': 'all', 'at': '2026-11-08T11:00:00Z',
     'done': 'ack: studio-ep (scheduled 20:00 Dubai)'},
    {'id': 'dropped-one', 'from': 'Production 1', 'to': 'Production 2', 'at': '2026-11-08T12:00:00Z', 'done': 'x',
     'acknowledged_at': '2026-11-09T01:55Z', 'outcome': 'dropped 9 Nov under the 24-hour rule'},
    {'id': 'notice', 'from': 'Production 1 (build desk)', 'to': 'all', 'at': '2026-11-09T01:00:00Z', 'done': 'n'},
    {'id': 'p2-self', 'from': 'production-2', 'to': 'production-2', 'at': '2026-11-09T01:00:00Z', 'done': 'n'},
    {'id': 'ancient', 'from': 'Production 1', 'to': 'Production 2', 'at': '2026-11-01T10:00:00Z', 'done': 'old'},
]}
COMMIT = {'rows': [
    {'id': 'bonk', 'title': 'BONK', 'kind': 'post', 'slot': 'Mon 09 Nov 06:30 Dubai (02:30Z)', 'job': 'jobs/live/b.json',
     'platforms': ['instagram', 'x', 'threads'], 'held_by_mohammad': False, 'status': 'scheduled in Publer',
     'card': 'Mohammad in chat, see adv-20261108-stories-tab'},
    {'id': 'future', 'title': 'Future', 'kind': 'post', 'slot': 'Mon 09 Nov 12:00 Dubai', 'job': 'jobs/live/f.json',
     'status': 'scheduled in Publer', 'held_by_mohammad': True},
    {'id': 'old-row', 'title': 'Old', 'slot': '2026-11-01T10:00+04:00', 'status': 'scheduled'},
]}


class Stories(unittest.TestCase):
    def writes(self, **kw):
        return {w['doc_id']: w for w in O.stories_docs(BOARD, COMMIT, NOW, keeper_status={}, published=PUBLISHED, **kw)}

    def test_states_due_held_and_ids(self):
        w = self.writes()
        self.assertEqual(sorted(w), ['bonk', 'dropped-one', 'future', 'mohammad-story', 'studio-ep'])
        m = w['mohammad-story']['data']
        self.assertEqual((m['state'], m['due'], m['due_dubai'], m['held']), ('waiting_pickup', '2026-11-09T03:00:00Z', '07:00', False))
        self.assertEqual(m['card'], 'adv-20261108-stories-tab')
        s = w['studio-ep']['data']
        self.assertEqual((s['state'], s['slot'], s['held']), ('scheduled', '20:00 Dubai', True))
        d = w['dropped-one']['data']
        self.assertEqual((d['state'], d['closed_at']), ('dropped', '2026-11-09T01:55:00Z'))
        b = w['bonk']['data']
        self.assertEqual((b['state'], b['publer_ids_last6'], b['card']), ('published', ['5dfd9d'], 'adv-20261108-stories-tab'))
        f = w['future']['data']
        self.assertEqual((f['state'], f['held']), ('scheduled', True))

    def test_closed_rows_deleted_after_three_days_and_unchanged_skipped(self):
        first = self.writes()
        ex = {'bonk': (2, first['bonk']['data']),
              'gone-closed': (5, {'state': 'published', 'closed_at': '2026-11-05T00:00:00Z'}),
              'gone-recent': (1, {'state': 'published', 'closed_at': '2026-11-08T00:00:00Z'})}
        w = self.writes(existing=ex)
        self.assertNotIn('bonk', w)                                    # unchanged: no write
        self.assertEqual((w['gone-closed']['op'], w['gone-closed']['if_version']), ('delete', 5))
        self.assertNotIn('gone-recent', w)                             # closed under 3 days ago: kept

    def test_cli_runs_end_to_end(self):
        t = tempfile.mkdtemp()
        for n, v in (('b', BOARD), ('c', COMMIT), ('p', PUBLISHED), ('s', SCHEDULED), ('k', KEEPER)):
            json.dump(v, open(os.path.join(t, n + '.json'), 'w'))
        D = [sys.executable, os.path.join(HERE, 'dispatch.py')]
        env = dict(os.environ, DISPATCH_NOW='2026-11-09T03:20:00Z')
        for args in (['feed', '--keeper', 'k', '--commitments', 'c', '--scheduled', 's', '--published', 'p', '--out', 'feed'],
                     ['published', '--posts', 'p', '--out', 'pub'], ['stale', '--items', t, '--out', 'st'],
                     ['stories', '--board', 'b', '--commitments', 'c', '--published', 'p', '--out', 'sto']):
            a = [x if x in ('feed', 'published', 'stale', 'stories') and i == 0 or x.startswith('--') or x == t
                 else os.path.join(t, x + '.json') for i, x in enumerate(args)]
            r = subprocess.run(D + a, capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(rd(os.path.join(t, 'feed.json')))['next_slot'], '08:30 Dubai · Next one')
        self.assertEqual(len(json.loads(rd(os.path.join(t, 'pub.json')))), 2)
        out = rd(os.path.join(t, 'sto.json')) + rd(os.path.join(t, 'pub.json'))
        self.assertNotIn('aaaaaaaaaaaa', out)                          # never a whole Publer id


if __name__ == '__main__':
    unittest.main()
