"""Tests for keeper.py: every rung of the ladder, alarm dedup across passes, and the seven shadow scenarios of
adv-20261030-promise-keeper addendum H simulated on fixtures (the live shadow runs come after the release)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import keeper as K  # noqa: E402

FIX = os.path.join(HERE, 'fixtures', 'commitments.json')
NOW = K.parse_time('2026-11-01T12:00:00Z')


def rows():
    with open(FIX, encoding='utf-8') as f:
        return json.load(f)['rows']


def by_id(status):
    return {a['id']: a for a in status['rows']}


class Ladder(unittest.TestCase):
    def setUp(self):
        os.environ['KEEPER_NTFY'] = 'off'
        self.s = K.summarise(rows(), NOW, 'alarm-only')
        self.a = by_id(self.s)

    def test_times(self):
        self.assertEqual(K.parse_time('2026-11-01T16:00+04:00'), NOW)
        self.assertEqual(K.parse_time('2026-11-01T16:00'), NOW)           # no offset: Dubai
        self.assertEqual(K.parse_time('2026-11-01T12:00:00Z').tzinfo, timezone.utc)
        self.assertIsNone(K.parse_time('tonight'))

    def test_rungs(self):
        self.assertEqual(self.a['ahead']['stage'], 'ahead')
        self.assertTrue(self.a['t90']['stage'].startswith('T-90'))
        self.assertTrue(self.a['t45']['stage'].startswith('T-45'))
        self.assertTrue(self.a['t15']['stage'].startswith('T-15'))
        self.assertEqual(self.a['t15']['alarm'], 'at-risk')
        self.assertEqual(self.a['missed']['stage'], 'slot passed, not scheduled')
        self.assertEqual(self.a['missed']['would_apply'], 'bank-piece')
        self.assertIn('alarm-only', self.a['missed']['note'])

    def test_held_and_scheduled_are_quiet(self):
        for k in ('held', 'sched', 'legacy', 'ahead', 't90'):
            self.assertIsNone(self.a[k]['alarm'], k)

    def test_legacy_free_text(self):
        self.assertEqual(set(self.a['legacy']['delivery'].values()), {'scheduled'})

    def test_blocked_stays_monitored(self):
        self.assertEqual(self.a['t15']['production'], 'blocked')
        self.assertIn('current template', self.a['t15']['note'])
        self.assertEqual(self.a['t15']['commitment'], 'at_risk')

    def test_delivery_exceptions(self):
        self.assertEqual(self.a['timeout']['alarm'], 'delivery')
        self.assertIn('never resubmit blind', self.a['timeout']['note'])
        self.assertEqual(self.a['xfail']['alarm'], 'delivery')
        self.assertIn('x failed', self.a['xfail']['note'])
        self.assertEqual(self.a['xfail']['delivery']['instagram'], 'scheduled')   # one failure never touches the others
        self.assertEqual(self.a['unconf']['alarm'], 'unconfirmed')

    def test_fulfilled_and_moved(self):
        self.assertEqual(self.a['ontime']['commitment'], 'fulfilled_on_time')
        self.assertEqual(self.a['moved']['commitment'], 'fulfilled_late')       # original_due_at is never forgotten

    def test_bad_row(self):
        self.assertEqual(self.a['noslot']['alarm'], 'bad-row')

    def test_counts_and_six(self):
        self.assertEqual(self.s['overdue'], 1)                                  # 'missed' only
        self.assertTrue(self.s['line'].startswith('overdue commitments: 1, at risk: '))
        self.assertEqual(len(self.s['six']), 6)
        self.assertIn('timeout instagram', self.s['six'][2])
        self.assertIn('xfail x', self.s['six'][3])
        self.assertIn('moved', self.s['six'][5])                               # published, not logged
        self.assertNotIn('ontime', self.s['six'][5])


class Passes(unittest.TestCase):
    def run_tick(self, out, commitments=FIX, now='2026-11-01T12:00:00Z'):
        env = dict(os.environ, KEEPER_NTFY='off')
        return subprocess.run([sys.executable, os.path.join(HERE, 'keeper.py'), 'tick', '--commitments', commitments,
                               '--out', out, '--now', now], capture_output=True, text=True, env=env)

    def test_dedup_across_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = self.run_tick(d)
            self.assertEqual(p1.returncode, 0, p1.stderr)
            n1 = p1.stdout.count('alarm:')
            self.assertGreater(n1, 3)
            p2 = self.run_tick(d, now='2026-11-01T12:01:00Z')
            self.assertEqual(p2.stdout.count('alarm:'), 0, p2.stdout)           # same rungs: no second alarm
            with open(os.path.join(d, 'status.txt'), encoding='utf-8') as f:
                self.assertEqual(len(f.read().splitlines()), 7)

    def test_next_rung_alarms_again(self):
        with tempfile.TemporaryDirectory() as d:
            self.run_tick(d)
            p = self.run_tick(d, now='2026-11-01T12:15:00Z')                    # t15's slot passes: now 'missed'
            self.assertIn('Missed slot: Template release delayed', p.stdout)

    # Addendum H, simulated.
    def test_h1_editor_busy(self):
        a = by_id(K.summarise(rows(), K.parse_time('2026-11-01T12:30:00Z'), 'alarm-only'))['t45']
        self.assertEqual(a['alarm'], 'at-risk')                                # nobody scheduled it: the keeper says so

    def test_h2_template_release_delayed(self):
        a = by_id(K.summarise(rows(), NOW, 'alarm-only'))['t15']
        self.assertIn('current template', a['note'])

    def test_h3_fresh_session_no_repo(self):
        with tempfile.TemporaryDirectory() as d:                               # no state, no log: a cold start
            p = self.run_tick(d)
            self.assertEqual(p.returncode, 0)
            self.assertIn('Fresh session, no repo', p.stdout)

    def test_h4_publer_timeout(self):
        a = by_id(K.summarise(rows(), NOW, 'alarm-only'))['timeout']
        self.assertEqual(a['delivery']['instagram'], 'uncertain')
        self.assertEqual(a['alarm'], 'delivery')

    def test_h5_shared_database_unavailable(self):
        s = K.summarise(rows(), NOW, 'alarm-only')                             # the keeper never reads the inbox
        self.assertIn('not read by the keeper', s['six'][1])

    def test_h6_known_bad_composition(self):
        a = by_id(K.summarise(rows(), NOW, 'alarm-only'))['badqc']
        self.assertEqual(a['production'], 'rejected')
        self.assertEqual(a['commitment'], 'at_risk')

    def test_h7_restart_near_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            self.run_tick(d, now='2026-11-01T11:58:00Z')
            p = self.run_tick(d, now='2026-11-01T12:00:00Z')                   # restart: state survives on disk
            self.assertNotIn('At risk: Template release delayed', p.stdout)
            with open(os.path.join(d, 'state.json'), encoding='utf-8') as f:
                self.assertTrue(any(k.startswith('t15|at-risk') for k in json.load(f)['sent']))

    # addendum_0615: the server's keeper checks GitHub's.
    def test_compare_agree_stale_unreadable(self):
        mine = {'generated_at': '2026-11-01T12:00:00Z', 'line': 'overdue commitments: 0, at risk: 1', 'overdue': 0,
                'at_risk': 1, 'commitments_sha': 'abc'}
        st = {}
        line, alarm = K.compare(mine, dict(mine, generated_at='2026-11-01T11:57:00Z'), st, NOW)
        self.assertIn('agrees', line)
        self.assertIsNone(alarm)
        line, alarm = K.compare(mine, dict(mine, generated_at='2026-11-01T11:30:00Z'), st, NOW)
        self.assertEqual(alarm['title'], 'Keeper check: GitHub keeper stale')
        line, alarm = K.compare(mine, dict(mine, generated_at='2026-11-01T11:30:00Z'), st, NOW)
        self.assertIsNone(alarm)                                               # once an hour
        line, alarm = K.compare(mine, None, st, NOW)
        self.assertEqual(alarm['title'], 'Keeper check: GitHub status unreadable')

    def test_compare_disagreement_needs_two_passes(self):
        mine = {'generated_at': '2026-11-01T12:00:00Z', 'line': 'overdue commitments: 1, at risk: 0', 'overdue': 1,
                'at_risk': 0, 'commitments_sha': 'abc'}
        theirs = dict(mine, generated_at='2026-11-01T11:58:00Z', line='overdue commitments: 0, at risk: 0', overdue=0)
        st = {}
        line, alarm = K.compare(mine, theirs, st, NOW)
        self.assertIsNone(alarm)
        self.assertIn('once', line)
        line, alarm = K.compare(mine, theirs, st, K.parse_time('2026-11-01T12:05:00Z'))
        self.assertEqual(alarm['title'], 'Keepers disagree')
        other = dict(theirs, commitments_sha='def')                           # different inputs: not comparable
        self.assertIn('agrees', K.compare(mine, other, {}, NOW)[0])

    def test_unreadable_commitments(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_tick(d, commitments=os.path.join(d, 'missing.json'))
            self.assertEqual(p.returncode, 2)
            self.assertIn('unreadable', p.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=1)
