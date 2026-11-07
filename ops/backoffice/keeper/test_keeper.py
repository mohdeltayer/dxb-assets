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
                self.assertEqual(len(f.read().splitlines()), 10)  # the line, coverage, the six, bank (5 Nov), publer (7 Nov)

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

    def test_unreadable_commitments(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_tick(d, commitments=os.path.join(d, 'missing.json'))
            self.assertEqual(p.returncode, 2)
            self.assertIn('unreadable', p.stdout)


class Compare(unittest.TestCase):
    """addendum_0615: the server's keeper checks GitHub's."""

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


if __name__ == '__main__':
    unittest.main(verbosity=1)


class Desk(unittest.TestCase):
    """Desk alarms (prod-20261102-build-status-json)."""

    def setUp(self):
        import tempfile
        self.t = tempfile.TemporaryDirectory()
        self.d = self.t.name

    def tearDown(self):
        self.t.cleanup()

    def files(self, started=False, release=False, last_watch='2026-11-06T00:30Z'):
        board = os.path.join(self.d, 'board.json')
        h = [{'id': 'build-20261106-started'}] if started else [{'id': 'other'}]
        with open(board, 'w') as f:
            json.dump({'handoffs': h}, f)
        rel = os.path.join(self.d, 'releases')
        os.makedirs(rel, exist_ok=True)
        if release:
            open(os.path.join(rel, '2026-11-06.md'), 'w').close()
        runs = os.path.join(self.d, 'runs.jsonl')
        with open(runs, 'w') as f:
            f.write(json.dumps({'at': last_watch, 'run': 'hourly-watch'}) + '\n')
        return board, rel, runs

    def test_quiet_before_the_times(self):
        b, r, w = self.files()
        lines, alarms = K.desk_checks(K.parse_time('2026-11-05T21:10Z'), b, r, w)   # 01:10 Dubai
        self.assertEqual(alarms, [])
        self.assertTrue(any('missing' in l for l in lines))

    def test_started_and_release_alarms(self):
        b, r, w = self.files(last_watch='2026-11-06T00:00Z')
        _, a1 = K.desk_checks(K.parse_time('2026-11-05T21:25Z'), b, r, w)            # 01:25 Dubai
        self.assertEqual([x['key'].split('|')[1] for x in a1], ['started'])
        _, a2 = K.desk_checks(K.parse_time('2026-11-06T00:20Z'), b, r, w)            # 04:20 Dubai
        self.assertEqual(sorted(x['key'].split('|')[1] for x in a2), ['release', 'started'])

    def test_present_means_no_alarm(self):
        b, r, w = self.files(started=True, release=True, last_watch='2026-11-06T00:00Z')
        _, a = K.desk_checks(K.parse_time('2026-11-06T00:20Z'), b, r, w)
        self.assertEqual(a, [])

    def test_watch_gap_once(self):
        b, r, w = self.files(started=True, release=True, last_watch='2026-11-06T06:00Z')
        _, a = K.desk_checks(K.parse_time('2026-11-06T07:40Z'), None, None, w)      # 100 min
        self.assertEqual(len(a), 1)
        state = {}
        os.environ['KEEPER_NTFY'] = 'off'
        r1, _ = K.raise_desk(a, state, K.parse_time('2026-11-06T07:40Z'))
        r2, _ = K.raise_desk(a, state, K.parse_time('2026-11-06T07:45Z'))
        self.assertEqual((len(r1), len(r2)), (1, 0))

    def test_stale_log_never_pages(self):
        b, r, w = self.files(started=True, release=True, last_watch='2026-11-05T00:02Z')
        lines, a = K.desk_checks(K.parse_time('2026-11-06T07:40Z'), None, None, w)
        self.assertEqual(a, [])
        self.assertTrue(any('stale' in l for l in lines))

    def test_not_asked_is_silent(self):
        self.assertEqual(K.desk_checks(K.parse_time('2026-11-06T00:20Z')), ([], []))



class FakeReader:
    def __init__(self, posts):
        self.posts = posts

    def fetch(self, start, end):
        return list(self.posts)


def row(i, slot, **kw):
    r = {'id': i, 'title': i, 'kind': 'post', 'slot': slot, 'platforms': ['instagram', 'x', 'threads'],
         'fallback': 'bank-piece', 'held_by_mohammad': False}
    r.update(kw)
    return r


class Evidence(unittest.TestCase):
    """adv-20261107-keeper-blind-and-lost-submit items 2, 3, 5 and 6 (with the 07:30Z and 13:10Z corrections)."""
    def setUp(self):
        os.environ['KEEPER_NTFY'] = 'off'

    def test_publer_confirms_a_post_production_never_logged(self):
        rows = [row('dr', '2026-11-01T15:00+04:00')]            # 11:00Z; now 12:00Z: slot passed, no production entry
        posts = [{'network': n, 'state': 'published', 'at': K.parse_time('2026-11-01T11:00:30Z'), 'id': 'p' + n,
                  'link': ''} for n in ('instagram', 'x', 'threads')]
        state = {}
        ev, line, last = K.read_publer(rows, state, NOW, FakeReader(posts))
        a = by_id(K.summarise(rows, NOW, 'alarm-only', ev))['dr']
        self.assertEqual(a['stage'], 'published')
        self.assertEqual(a['alarm'], 'evidence-gap')             # yellow, not 'missed'
        self.assertIn('publer: read', line)
        self.assertEqual(last, K.parse_time('2026-11-01T11:00:30Z'))
        self.assertIn('dr|x', state['publer_ids'])               # ids kept in the private state only
        self.assertEqual(K.alarm_message(a)['priority'], 'default')

    def test_missing_needs_two_reads_ten_minutes_apart(self):
        rows = [row('lost', '2026-11-01T15:30+04:00')]          # 11:30Z, slot passed by 30 min at NOW
        state = {}
        ev, _, _ = K.read_publer(rows, state, NOW, FakeReader([]))
        a = by_id(K.summarise(rows, NOW, 'alarm-only', ev))['lost']
        self.assertEqual(a['stage'], 'slot passed, Publer read once')
        self.assertIsNone(a['alarm'])
        later = K.parse_time('2026-11-01T12:11:00Z')
        ev, _, _ = K.read_publer(rows, state, later, FakeReader([]))
        a = by_id(K.summarise(rows, later, 'alarm-only', ev))['lost']
        self.assertEqual(a['alarm'], 'missed')

    def test_a_post_that_shows_up_clears_the_miss(self):
        rows = [row('late', '2026-11-01T15:30+04:00')]
        state = {}
        K.read_publer(rows, state, NOW, FakeReader([]))
        posts = [{'network': n, 'state': 'scheduled', 'at': K.parse_time('2026-11-01T11:30:00Z'), 'id': n, 'link': ''}
                 for n in ('instagram', 'x', 'threads')]
        ev, _, _ = K.read_publer(rows, state, K.parse_time('2026-11-01T12:11:00Z'), FakeReader(posts))
        self.assertFalse(ev['late']['confirmed_missing'])
        self.assertEqual(state['publer_miss'], {})

    def test_no_key_changes_nothing(self):
        os.environ['KEEPER_PUBLER_KEY_FILE'] = '/nonexistent/publer.key'
        try:
            ev, line, last = K.read_publer([row('x1', '2026-11-01T15:30+04:00')], {}, NOW)
        finally:
            del os.environ['KEEPER_PUBLER_KEY_FILE']
        self.assertEqual(ev, {})
        self.assertIn('no key file', line)
        a = by_id(K.summarise([row('x1', '2026-11-01T15:30+04:00')], NOW, 'alarm-only', ev))['x1']
        self.assertEqual(a['alarm'], 'missed')                   # production evidence only, as before

    def test_read_failure_never_prints_the_key(self):
        class Bad:
            def fetch(self, a, b):
                raise RuntimeError('401 for key ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        ev, line, _ = K.read_publer([row('x2', '2026-11-01T16:30+04:00')], {}, NOW, Bad())
        self.assertEqual(ev, {})
        self.assertNotIn('ABCDEFGHIJKLMNOPQRSTUVWXYZ', line)

    def test_claimed_slot_with_no_post_twenty_minutes_before(self):
        rows = [row('c1', '2026-11-01T16:18+04:00', production='claimed', claimed_by=':30 session'),
                row('c2', '2026-11-01T16:18+04:00')]
        a = by_id(K.summarise(rows, NOW, 'alarm-only'))
        self.assertEqual(a['c1']['alarm'], 'claim')
        self.assertIn('release it with a board line', a['c1']['note'])
        self.assertIsNone(a['c2']['alarm'])

    def test_coverage_day_and_night(self):
        last = K.parse_time('2026-11-01T10:30:00Z')                # 14:30 Dubai
        line, gap, over = K.coverage(last, NOW)                     # 16:00 Dubai: 90 min, day limit 60
        self.assertTrue(over)
        self.assertIn('no-build is not an allowed outcome', line)
        night = K.parse_time('2026-11-01T23:00:00Z')                # 03:00 Dubai
        self.assertFalse(K.coverage(K.parse_time('2026-11-01T21:30:00Z'), night)[2])   # 90 min, night limit 120
        self.assertTrue(K.coverage(K.parse_time('2026-11-01T20:30:00Z'), night)[2])    # 150 min

    def test_bank_floor_is_six(self):
        self.assertEqual(K.BANK_MIN, 6)


class Formats(unittest.TestCase):
    """7 Nov audit: Production 2 writes slots as '2026-11-07 12:15 Dubai'; 36 rows were unreadable."""
    def test_dubai_slot_form(self):
        self.assertEqual(K.parse_time('2026-11-07 12:15 Dubai'), K.parse_time('2026-11-07T08:15:00Z'))
        self.assertEqual(K.parse_time('2026-11-07 06:40 Dubai (T0, published at once)'), K.parse_time('2026-11-07T02:40:00Z'))

    def test_old_rows_never_page(self):
        os.environ['KEEPER_NTFY'] = 'off'
        rows = [row('old', '2026-11-01T03:00+04:00'), row('live', '2026-11-01T15:40+04:00')]   # 23:00Z the day before; 11:40Z
        st = K.summarise(rows, NOW, 'alarm-only')
        raised, _ = K.raise_alarms(st, {}, NOW)
        self.assertEqual([a['key'].split('|')[0] for a in raised], ['live'])

    def test_scheduled_slot_that_passed_counts_for_coverage(self):
        rows = [row('s', '2026-11-01T15:30+04:00', status='submitted to Publer 3/3; in the scheduled list')]
        st = K.summarise(rows, NOW, 'alarm-only')
        self.assertEqual(K.last_published(st['rows'], rows, None, NOW), K.parse_time('2026-11-01T11:30:00Z'))
