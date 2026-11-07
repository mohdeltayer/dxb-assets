"""desk_audit tests: the DEAD line (adv-20261107-keeper-blind-and-lost-submit, item 7)."""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_audit as DA  # noqa: E402

NOW = dt.datetime(2026, 11, 7, 14, 0, tzinfo=dt.timezone.utc)
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


if __name__ == '__main__':
    unittest.main()
