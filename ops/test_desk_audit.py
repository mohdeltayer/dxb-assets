"""desk_audit tests: the DEAD line (adv-20261107-keeper-blind-and-lost-submit, item 7)."""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_audit as DA  # noqa: E402

NOW = dt.datetime(2026, 11, 7, 14, 0, tzinfo=dt.timezone.utc)
DA.ACK_FROM = '2026-11-07T00:00:00Z'
DESKS = {'desks': [{'name': 'Production 2 newsroom', 'tasks': [
    {'name': 'posting session :30', 'period_min': 60, 'dead_after_runs': 2, 'board_from': '^Production 2$'},
    {'name': 'posting session :35', 'period_min': 60, 'dead_after_runs': 2, 'board_from': ':35', 'runs_match': ':35'}]}]}


class Dead(unittest.TestCase):
    def test_silent_session_is_dead_and_listed_first(self):
        board = {'handoffs': [{'from': 'Production 2', 'at': '2026-11-07T04:50:00Z'},
                              {'from': 'Production 2 (hourly digest session, :35)', 'at': '2026-11-07T13:36:00Z'}]}
        out = DA.audit(DESKS, board, [], NOW)
        self.assertTrue(out[0].startswith('DEAD Production 2 newsroom: posting session :30: silent for 9 runs'))
        self.assertFalse(any(':35' in l and l.startswith('DEAD') for l in out))

    def test_helper_runs_count_as_evidence(self):
        board = {'handoffs': []}
        runs = [{'at': '2026-11-07T13:50Z', 'run': 'hourly 13:35Z'}]
        out = DA.audit(DESKS, board, runs, NOW)
        self.assertFalse(any(':35' in l and l.startswith('DEAD') for l in out))
        self.assertTrue(any(l.startswith('DEAD') and ':30: no run on record' in l for l in out))



class Acks(unittest.TestCase):
    """8 Nov 2026: handoffs to Production 2 are acknowledged by id in its next run's board line."""
    def board(self, ack_text):
        hs = [{'id': 'studio-x-built', 'from': 'Production 1 (studio)', 'to': 'Production 2', 'at': '2026-11-07T11:00:00Z'},
              {'id': 'build-20261107-started', 'from': 'Production 1 (build desk)', 'to': 'all', 'at': '2026-11-07T10:00:00Z'},
              {'id': 'p2-run', 'from': 'Production 2 (hourly digest session, :35)', 'at': '2026-11-07T12:50:00Z',
               'done': ack_text}]
        return {'handoffs': hs}

    def test_unacked_is_listed(self):
        out = DA.audit({'desks': []}, self.board('hourly check, nothing new'), [], NOW)
        self.assertTrue(any(l.startswith('UNACKED Production 2: studio-x-built') for l in out), out)
        self.assertFalse(any('build-20261107-started' in l for l in out))     # to 'all': a notice

    def test_ack_by_id_clears_it(self):
        out = DA.audit({'desks': []}, self.board('ack: studio-x-built (scheduled 20:30 Dubai)'), [], NOW)
        self.assertFalse(any(l.startswith('UNACKED') for l in out), out)

    def test_young_handoff_not_listed(self):
        b = self.board('nothing')
        b['handoffs'][0]['at'] = '2026-11-07T13:30:00Z'
        self.assertFalse(any(l.startswith('UNACKED') for l in DA.audit({'desks': []}, b, [], NOW)))


class DecisionStalls(unittest.TestCase):
    def test_decision_without_citation_flagged(self):
        b = {'handoffs': [{'id': 'p2-a', 'from': 'Production 2', 'at': '2026-11-07T06:35:00Z',
                           'done': 'FAILED RUN; I need your decision on where to source bank pieces'}]}
        out = DA.audit({'desks': []}, b, [], NOW)
        self.assertTrue(any(l.startswith('NOT-FOLLOWING-RULES Production 2: p2-a') for l in out), out)

    def test_cited_decision_passes(self):
        b = {'handoffs': [{'id': 'p2-b', 'from': 'Production 2', 'at': '2026-11-07T06:35:00Z',
                           'done': 'decision needed: CLAUDE.md Constant coverage 3 does not cover a Sunday cap breach'}]}
        self.assertFalse(any(l.startswith('NOT-FOLLOWING') for l in DA.audit({'desks': []}, b, [], NOW)))


class NineNov(unittest.TestCase):
    """9 Nov (adv-20261108-stories-tab addendum_0545): the 04:35 and 05:35 Dubai runs, as written on the board."""
    NOW = dt.datetime(2026, 11, 9, 3, 30, tzinfo=dt.timezone.utc)
    RUN_0435 = {'id': 'p2-20261109-0036z-no-lead-0435', 'from': 'production-2', 'to': 'production-2',
                'at': '2026-11-09T00:36Z', 'done': '04:35 Dubai check: Server digest still seq 207 (17:52Z).',
                'next': "05:35 and 06:35 checks; FM27 blocked on Mohammad's footage choice)"}
    RUN_0535 = {'id': 'p2-20261109-0143z-blood-bowl-rejected', 'from': 'production-2', 'to': 'production-2',
                'at': '2026-11-09T01:45Z', 'done': '05:35 Dubai check: Server digest still seq 207 (17:52Z).',
                'next': '06:35 check; open question stale-lead rule q-20261109-stale-sourcing',
                'must_not_repeat': 'Blood Bowl delay only as a late report if Mohammad answers the stale-lead question'}
    HIST = [(DA._t('2026-11-08T%02d:52:05Z' % h), s) for h, s in ((21, 212), (22, 213), (23, 214))] + \
           [(DA._t('2026-11-09T00:52:05Z'), 215), (DA._t('2026-11-09T01:52:05Z'), 216)]

    def test_decision_stalls_of_both_runs_flagged(self):
        out = DA.audit({'desks': []}, {'handoffs': [self.RUN_0435, self.RUN_0535]}, [], self.NOW)
        flagged = [l.split(': ')[1].split()[0] for l in out if l.startswith('NOT-FOLLOWING-RULES')]
        self.assertEqual(flagged, ['p2-20261109-0036z-no-lead-0435', 'p2-20261109-0143z-blood-bowl-rejected'])

    def test_stale_digest_against_the_branch_history(self):
        out = DA.audit({'desks': []}, {'handoffs': [self.RUN_0435, self.RUN_0535]}, [], self.NOW, self.HIST)
        st = [l for l in out if l.startswith('STALE-DIGEST')]
        self.assertEqual(len(st), 2, out)
        self.assertIn('read digest seq 207, the branch head was 214', st[0])     # 00:16Z: 23:52Z digest
        self.assertIn('read digest seq 207, the branch head was 215', st[1])     # 01:25Z: 00:52Z digest

    def test_new_line_form_and_a_fresh_read_pass(self):
        ok = {'id': 'p2-ok', 'from': 'production-2', 'at': '2026-11-09T02:40Z', 'done': 'digest seq read: 216 (branch head 216)'}
        bad = {'id': 'p2-bad', 'from': 'production-2', 'at': '2026-11-09T02:40Z', 'done': 'digest seq read: 215 (branch head 216)'}
        out = DA.audit({'desks': []}, {'handoffs': [ok, bad]}, [], self.NOW, [])
        self.assertEqual([l.split(': ')[1].split()[0] for l in out if l.startswith('STALE')], ['p2-bad'])
        late = {'id': 'p2-late', 'from': 'production-2', 'at': '2026-11-09T02:00Z', 'done': 'digest seq read: 215'}
        self.assertFalse(any(l.startswith('STALE') for l in DA.audit({'desks': []}, {'handoffs': [late]}, [], self.NOW, self.HIST)),
                         'the 01:52Z digest landed while that run was writing')

    def test_history_from_a_folder(self):
        import json, tempfile
        t = tempfile.mkdtemp()
        for at, s in self.HIST:
            with open(os.path.join(t, '%d.json' % s), 'w') as f:
                json.dump({'seq': s, 'generated_at': at.strftime('%Y-%m-%dT%H:%M:%SZ')}, f)
        self.assertEqual(DA.digest_history(t), self.HIST)

    def test_production_dash_2_acks_count(self):
        hs = [{'id': 'studio-y', 'from': 'Production 1 (studio)', 'to': 'Production 2', 'at': '2026-11-09T00:00:00Z'},
              {'id': 'p2', 'from': 'production-2', 'to': 'all', 'at': '2026-11-09T01:55Z', 'done': 'Acknowledged studio-y'}]
        self.assertFalse(any(l.startswith('UNACKED') for l in DA.audit({'desks': []}, {'handoffs': hs}, [], self.NOW)))


if __name__ == '__main__':
    unittest.main()
