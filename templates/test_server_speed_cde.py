"""adv-20261117-server-speed-for-p2 C, D, E: the job stays on main after a render, minutes per stage, unfinished work.

    python3 templates/test_server_speed_cde.py
"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'ops', 'backoffice', 'keeper'), os.path.join(ROOT, 'ops', 'backoffice', 'dispatch')]

import jobpath  # noqa: E402
import stagetimes as ST  # noqa: E402
import incomplete as INC  # noqa: E402
import workorder as WO  # noqa: E402

UTC = dt.timezone.utc

ENTRY = {'name': 'x-reel-v1.mp4', 'story': 'x', 'finished_at': '2026-11-17T18:03Z', 'runner': 'selfhosted',
         'stages': {'checks': 17.5, 'montage': 71.0, 'text': 119.9, 'audio': 1.8, 'outro': 42.9},
         'pipeline': {'fetch': 30.0, 'shots': 120.0, 'checks': 12.0, 'render': 300.0, 'after': 60.0},
         'queue_wait_secs': 6, 'setup_min': 0.5, 'job_secs': 540}


class C_JobStays(unittest.TestCase):
    def test_done_folder_resolves_and_prefers_done(self):
        with tempfile.TemporaryDirectory() as d:
            for sub in ('jobs/done', 'jobs/live'):
                os.makedirs(os.path.join(d, sub))
            open(os.path.join(d, 'jobs/done/a.json'), 'w').write('{}')
            self.assertEqual(jobpath.resolve('done', 'a', root=d), 'jobs/done/a.json')
            open(os.path.join(d, 'jobs/live/a.json'), 'w').write('{}')    # a re-render's new version beside the old
            self.assertEqual(jobpath.resolve('done', 'a', root=d), 'jobs/done/a.json')
            self.assertEqual(jobpath.resolve('done', 'jobs/done/a.json', root=d), 'jobs/done/a.json')
            with self.assertRaises(ValueError):                              # live still refuses a done path
                jobpath.resolve('live', 'jobs/done/a.json', root=d)

    def test_director_finds_the_job_from_qc(self):
        import presubmit as P
        real = P.REPO
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, 'jobs/done'))
            open(os.path.join(d, 'jobs/done/story-x.json'), 'w').write('{}')
            P.REPO = __import__('pathlib').Path(d)
            try:
                self.assertTrue(P.find_job(None, {'job_path': 'jobs/done/story-x.json'}).endswith('jobs/done/story-x.json'))
                self.assertTrue(P.find_job(None, {'name': 'story-x'}).endswith('jobs/done/story-x.json'))
                self.assertTrue(P.find_job('story-x', None).endswith('jobs/done/story-x.json'))
                self.assertEqual(P.find_job('nope.json', None), 'nope.json')       # left to the checklist to refuse
                self.assertIsNone(P.find_job(None, None))
            finally:
                P.REPO = real

    def test_workflows_move_the_job(self):
        for wf in ('render.yml', 'render-live.yml'):
            s = open(os.path.join(ROOT, '.github', 'workflows', wf)).read()
            self.assertIn('jobs/done/$(basename "$JOB")', s, wf)
            self.assertIn('git add --sparse -f "$JOB_DONE"', s, wf)
            self.assertIn('-m "job: $JOB_DONE"', s, wf)


class D_StageTimes(unittest.TestCase):
    def test_minutes_split(self):
        m = ST.minutes(ENTRY)
        self.assertEqual(m['queue'], 0.1)
        self.assertEqual(m['fetch'], 0.5)
        self.assertEqual(m['shots'], 2.0)
        self.assertEqual(m['checks'], round((12 + 17.5) / 60, 2))           # gate checks plus reel()'s own checks
        self.assertEqual(m['render'], round((300 - 17.5) / 60, 2))
        self.assertEqual(m['after'], 1.0)
        self.assertEqual(m['job'], 9.0)
        self.assertEqual(ST.slowest(m), 'render')
        self.assertTrue(ST.line(ENTRY).startswith('stages (min): queue 0.1, setup 0.5, fetch 0.5, shots 2.0'))

    def test_older_entry_and_empty(self):
        old = {'stages': {'checks': 6, 'montage': 60, 'text': 60}}
        self.assertEqual(ST.minutes(old), {'checks': 0.1, 'render': 2.0})
        self.assertEqual(ST.line({}), 'stages (min): not measured')

    def test_qc_and_upload(self):
        with tempfile.TemporaryDirectory() as d:
            qc = os.path.join(d, 'x-qc.json')
            json.dump({'verdict': 'pass'}, open(qc, 'w'))
            ST.write_qc(qc, ENTRY)
            self.assertEqual(json.load(open(qc))['stage_minutes']['shots'], 2.0)
            times = os.path.join(d, 'rt.json')
            json.dump([dict(ENTRY, story='y'), dict(ENTRY)], open(times, 'w'))
            m = ST.add_upload('x', 42, times, qc)
            self.assertEqual(m['upload'], 0.7)
            led = json.load(open(times))
            self.assertNotIn('upload_secs', led[0])
            self.assertEqual(led[1]['upload_secs'], 42.0)
            self.assertEqual(json.load(open(qc))['stage_minutes']['upload'], 0.7)
            self.assertIsNone(ST.add_upload('missing', 1, times))

    def test_last_lines(self):
        led = [{'name': 'no-story'}] + [dict(ENTRY, story='s%d' % i) for i in range(7)]
        rows = ST.last(5, led)
        self.assertEqual([r['story'] for r in rows], ['s2', 's3', 's4', 's5', 's6'])

    def test_cli_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'e.json')
            json.dump(ENTRY, open(p, 'w'))
            r = subprocess.run([sys.executable, os.path.join(HERE, 'stagetimes.py'), 'line', p], capture_output=True,
                               text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn('render 4.7', r.stdout)

    def test_render_job_records_pipeline(self):
        s = open(os.path.join(HERE, 'render_job.py')).read()
        self.assertIn("_times_note(job, 'pipeline', pipe)", s)
        self.assertIn("print('render_job: pipeline: '", s)


class E_Unfinished(unittest.TestCase):
    def test_open_replace_close(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, 'desk', 'incomplete.json')
            t0 = dt.datetime(2026, 11, 17, 6, 11, tzinfo=UTC)
            INC.open_row(f, 'rpg-maker-u2u', 'read qc.json, Director, Publer', job='jobs/live/rpg-maker.json',
                         run='44029299671', now=t0)
            INC.open_row(f, 'rpg-maker-u2u', 'Director, then Publer', run='44029299671', now=t0 + dt.timedelta(minutes=30))
            rows = INC.open_rows(INC.load(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['next'], 'Director, then Publer')
            self.assertEqual(rows[0]['first_at'], '2026-11-17T06:11:00Z')        # age counts from the first hand-off
            INC.close_row(f, 'rpg-maker-u2u', 'published 10:15 Dubai', now=t0 + dt.timedelta(hours=1))
            self.assertEqual(INC.open_rows(INC.load(f)), [])
            with self.assertRaises(SystemExit):
                INC.close_row(f, 'rpg-maker-u2u', 'again')

    def test_refuses_ids_links_and_bad_fields(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, 'incomplete.json')
            for kw in ({'nxt': 'post https://x.com/a/status/1'}, {'nxt': 'retry 6afc9dda28222636cbb95dc8'},
                       {'nxt': 'go', 'job': 'cards/x.json'}, {'nxt': 'go', 'run': 'abc'}, {'nxt': ''}):
                with self.assertRaises(SystemExit):
                    INC.open_row(f, 'story', **kw)
            with self.assertRaises(SystemExit):
                INC.open_row(f, 'bad story', 'go')

    def test_work_order_section_and_alarm(self):
        now = dt.datetime(2026, 11, 17, 9, 0, tzinfo=UTC)
        inc = {'rows': [{'story': 'rpg-maker-u2u', 'state': 'open', 'next': 'Director, then Publer',
                         'job': 'jobs/live/rpg-maker.json', 'run': '44029299671', 'at': '2026-11-17T06:11:00Z'},
                        {'story': 'splatoon-raiders', 'state': 'open', 'next': 'render from the resolver footage',
                         'at': '2026-11-17T08:30:00Z'},
                        {'story': 'old', 'state': 'closed', 'next': 'x', 'at': '2026-11-17T01:00:00Z'}]}
        wo = WO.build({}, now, [], times=[dict(ENTRY)], incomplete=inc)
        self.assertEqual([r['story'] for r in wo['unfinished']], ['rpg-maker-u2u', 'splatoon-raiders'])
        kinds = [a['kind'] for a in wo['notes']]                          # a note since 18 Nov (templates-never-refuse D)
        self.assertEqual(kinds.count('incomplete'), 1)                     # 169 min old; the 30-min one is not late
        md = WO.markdown(wo)
        self.assertIn('## 1b. Unfinished from the last run (pick up first)', md)
        self.assertIn('render run 44029299671', md)                         # an Actions run id is not scrubbed
        self.assertLess(md.index('## 1b.'), md.index("## 2. Mohammad's orders"))
        self.assertIn('## 7. Last five renders, minutes per stage', md)
        self.assertIn('slowest render', md)

    def test_work_order_without_file(self):
        wo = WO.build({}, dt.datetime(2026, 11, 17, 9, 0, tzinfo=UTC), [])
        md = WO.markdown(wo)
        self.assertIn('## 1b. Unfinished from the last run (pick up first)\nnone', md)
        self.assertIn('## 7. Last five renders, minutes per stage (for information)\nnone read', md)

    def test_keeper_reads_the_file(self):
        s = open(os.path.join(ROOT, '.github', 'workflows', 'keeper.yml')).read()
        self.assertIn('desk/incomplete.json?ref=desk', s)
        self.assertIn('${INCOMPLETE_ARG:-}', s)


if __name__ == '__main__':
    unittest.main()
