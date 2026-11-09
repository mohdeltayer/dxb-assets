"""Tests for workorder.py (build 10 Nov 2026, adv-20261109-coordination-in-code)."""
import datetime as dt, json, os, tempfile, unittest

import workorder as W

NOW = W.t('2026-11-09T16:52:00Z')          # 20:52 Dubai


def h(i, frm, to, at, done='', nxt='', ev=''):
    return {'id': i, 'from': frm, 'to': to, 'at': at, 'done': done, 'next': nxt, 'evidence': ev, 'must_not_repeat': ''}


def post(at, tpl, kind='news', state='scheduled'):
    return {'at': W.t(at), 'state': state, 'labels': {'tpl:' + tpl, 'kind:' + kind}, 'networks': {'x': state}}


class Handoffs(unittest.TestCase):
    def board(self):
        return {'handoffs': [
            h('t0-story', 'Production 1 (studio)', 'Production 2', '2026-11-09T11:57:00Z', 'T0 shadow drop', 'build now'),
            h('acked', 'Production 1 (studio)', 'Production 2', '2026-11-09T15:00:00Z', 'a story', 'due 21:30 Dubai'),
            h('p2-ack', 'production-2', 'all', '2026-11-09T15:10:00Z', 'ack: acked (building, target 21:30 Dubai)'),
            h('closed', 'Production 1 (studio)', 'Production 2', '2026-11-09T12:00:00Z', 'x'),
            h('p2-close', 'production-2', 'all', '2026-11-09T12:30:00Z', 'ack: closed (scheduled 17:15 Dubai)'),
            h('old', 'Production 1 (studio)', 'Production 2', '2026-11-08T12:00:00Z', 'old'),
            h('studio-sup', 'Production 1 (studio)', 'all', '2026-11-08T13:00:00Z', 'old is superseded by t0-story'),
            h('notice', 'Production 1 (build desk)', 'all', '2026-11-09T16:00:00Z', 'released'),
        ]}

    def test_open_and_due(self):
        o = {x['id']: x for x in W.open_handoffs(self.board(), NOW)}
        self.assertEqual(set(o), {'t0-story', 'acked'})
        self.assertTrue(o['t0-story']['t0'])
        self.assertEqual(o['t0-story']['due'], '2026-11-09T11:57:00Z')
        self.assertTrue(o['acked']['acked'])
        self.assertEqual(o['acked']['due'], '2026-11-09T17:30:00Z')       # due 21:30 Dubai

    def test_unacked_alarm_after_20_min(self):
        a = [x for x in W.hop_alarms(self.board(), NOW, []) if x['kind'] == 'unacked']
        self.assertEqual([x['key'] for x in a], ['hop|unacked|t0-story'])

    def test_no_line_by_50(self):
        b = {'handoffs': [h('p2', 'production-2', 'all', '2026-11-09T15:40:00Z', 'run')]}
        kinds = [x['kind'] for x in W.hop_alarms(b, NOW, [])]
        self.assertIn('no-line', kinds)
        b['handoffs'].append(h('p2b', 'production-2', 'all', '2026-11-09T16:40:00Z', 'run'))
        self.assertNotIn('no-line', [x['kind'] for x in W.hop_alarms(b, NOW, [])])
        early = W.t('2026-11-09T16:45:00Z')       # 20:45 Dubai: before :50
        b['handoffs'].pop()
        self.assertNotIn('no-line', [x['kind'] for x in W.hop_alarms(b, early, [])])

    def test_scheduled_line_needs_ids(self):
        b = {'handoffs': [h('s1', 'production-2', 'all', '2026-11-09T16:30:00Z', 'scheduled: story at 20:45 Dubai, 3/3'),
                          h('s2', 'production-2', 'all', '2026-11-09T16:31:00Z',
                            'scheduled: story at 21:15 Dubai, 3/3, ids 6735aa11bb22cc33dd44ee55 6735aa11bb22cc33dd44ee56 '
                            '6735aa11bb22cc33dd44ee57')]}
        keys = [x['key'] for x in W.hop_alarms(b, NOW, []) if x['kind'] == 'no-ids']
        self.assertEqual(keys, ['hop|no-ids|s1'])

    def test_mirror_and_publer(self):
        a = W.hop_alarms({'handoffs': []}, NOW, [], mirror={'generated_at': '2026-11-09T13:50:00Z'},
                         server={'publer_read_at': '2026-11-09T16:30:00Z'})
        kinds = [x['kind'] for x in a]
        self.assertIn('mirror', kinds)
        self.assertIn('publer', kinds)
        a = W.hop_alarms({'handoffs': []}, NOW, [], mirror={'generated_at': '2026-11-09T16:00:00Z'},
                         server={'publer_read_at': '2026-11-09T16:45:00Z'})
        self.assertEqual([x['kind'] for x in a], [])


class Caps(unittest.TestCase):
    def test_third_in_a_row_and_evergreen(self):
        ps = [post('2026-11-09T15:30:00Z', 'split'), post('2026-11-09T16:00:00Z', 'split'),
              post('2026-11-09T16:30:00Z', 'split'),
              post('2026-11-09T17:00:00Z', 'trailer', 'evergreen'), post('2026-11-09T17:30:00Z', 'quote', 'evergreen')]
        why = [b['why'] for b in W.cap_breaches(ps, NOW)]
        self.assertIn('third split in a row', why)
        self.assertIn('two evergreen posts in a row', why)
        self.assertTrue(any(w.startswith('evergreen 30 min after') for w in why))

    def test_caps_now(self):
        ps = [post('2026-11-09T15:00:00Z', 'trailer'), post('2026-11-09T16:00:00Z', 'list', 'evergreen')]
        c = W.caps(ps, NOW)
        self.assertFalse(c['evergreen_allowed'])
        self.assertEqual(c['evergreen_reopens'], 'after the next news post')
        ps.append(post('2026-11-09T16:30:00Z', 'trailer'))
        c = W.caps(ps, NOW)
        self.assertFalse(c['evergreen_allowed'])
        self.assertEqual(c['evergreen_reopens'], '2026-11-09T19:00:00Z')    # 3 hours after the 20:00 Dubai evergreen
        overnight = W.t('2026-11-09T21:30:00Z')                              # 01:30 Dubai
        self.assertTrue(W.caps(ps, overnight)['evergreen_allowed'])

    def test_numbers_and_card_window(self):
        ps = [post('2026-11-09T14:00:00Z', 'numbers'), post('2026-11-09T15:00:00Z', 'trailer'),
              post('2026-11-09T16:00:00Z', 'quote')]
        c = W.caps(ps, NOW)
        self.assertFalse(c['numbers_allowed'])
        self.assertFalse(c['card_led_allowed'])


class NextSlot(unittest.TestCase):
    def test_walks_scheduled_posts(self):
        ps = [post('2026-11-09T16:30:00Z', 'trailer', state='published'), post('2026-11-09T17:15:00Z', 'split')]
        n = W.next_slot(ps, NOW)
        self.assertEqual(n['covered_until'], '2026-11-09T17:15:00Z')
        self.assertEqual(n['due_by'], '2026-11-09T18:15:00Z')
        self.assertFalse(n['overdue'])

    def test_overdue(self):
        n = W.next_slot([post('2026-11-09T15:00:00Z', 'trailer', state='published')], NOW)
        self.assertTrue(n['overdue'])


class Scrub(unittest.TestCase):
    def test_no_ids_or_post_links(self):
        s = W.scrub('ids 6735aa11bb22cc33dd44ee55 and https://www.instagram.com/reel/abc and 1234567890123')
        self.assertNotIn('6735aa', s)
        self.assertNotIn('instagram.com', s)
        self.assertNotIn('1234567890123', s)


class Run(unittest.TestCase):
    def test_writes_hourly_from_25(self):
        d = tempfile.mkdtemp()
        b = os.path.join(d, 'b.json')
        json.dump({'handoffs': [h('x', 'Production 1 (studio)', 'Production 2', '2026-11-09T16:00:00Z', 'go')]}, open(b, 'w'))
        args = lambda now, force=False: type('A', (), dict(board=b, orders=None, mirror=None, digest=None, digests=None,
                                                          server=None, commitments=None, ledger=None, now=now,
                                                          state=None, out=d, force=force))
        _, wrote = W.run(args('2026-11-09T16:26:00Z'))           # 20:26 Dubai, nothing yet: written
        self.assertTrue(wrote)
        _, wrote = W.run(args('2026-11-09T16:36:00Z'))           # same hour: kept
        self.assertFalse(wrote)
        _, wrote = W.run(args('2026-11-09T17:10:00Z'))           # 21:10 Dubai: before :25, last at 20:26: kept
        self.assertFalse(wrote)
        _, wrote = W.run(args('2026-11-09T17:27:00Z'))           # 21:27 Dubai: the next hour's order
        self.assertTrue(wrote)
        md = open(os.path.join(d, 'work-order.md')).read()
        self.assertIn('## 1. Alarms to clear first', md)
        self.assertIn('x (from Production 1 (studio)', md)
        self.assertTrue(os.path.exists(os.path.join(d, 'hop.json')))


if __name__ == '__main__':
    unittest.main()
