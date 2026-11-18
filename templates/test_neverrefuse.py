"""Templates never refuse (adv-20261118-templates-never-refuse A): only the four hard stops stop."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import softgate as SG
import reel
import render_job as RJ


class Soft(unittest.TestCase):
    def setUp(self):
        SG.WARNINGS.clear(); SG.LADDER.clear()

    def test_text_hard(self):
        self.assertTrue(SG.text_hard({'rule': 'latin_first'}))
        self.assertTrue(SG.text_hard({'rule': 'font_check', 'detail': 'line runs out of the safe zone: x'}))
        self.assertFalse(SG.text_hard({'rule': 'reading'}))
        self.assertFalse(SG.text_hard({'rule': 'line_count'}))
        self.assertFalse(SG.text_hard({'rule': 'gate', 'detail': 'reel_check missing'}))

    def test_reel_soft_warns(self):
        reel.SOFT = False
        with self.assertRaises(ValueError):
            reel._soft('x', 'boom')
        reel.SOFT = True
        try:
            reel._soft('x', 'boom')
            self.assertEqual(SG.WARNINGS[-1]['stage'], 'x')
            reel.check_reading([('نص طويل جدا جدا جدا جدا جدا جدا', 0.0, 0.5, {})], 0.5)
            self.assertEqual(SG.WARNINGS[-1]['stage'], 'reading')
            self.assertTrue(reel.lowres_reason(True))
        finally:
            reel.SOFT = False

    def test_strict_keeps_refusals(self):
        self.assertFalse(SG.soft({'strict': True}))
        with self.assertRaises(SystemExit):
            SG.guarded('x', lambda: (_ for _ in ()).throw(SystemExit('no')), job={'strict': True})
        self.assertIsNone(SG.guarded('x', lambda: (_ for _ in ()).throw(SystemExit('no')), job={}))

    def test_gate_ladder_letterbox_to_showcase(self):
        job = {'shots': [['a.mp4', 5.0, 3.0, None], ['a.mp4', 9.0, 3.0, None]], 'template': 'trailer'}
        RJ.gate_ladder(job, [{'where': 'shot 0', 'rule': 'shot_timing',
                              'detail': 'shot 0 (a.mp4 5.00 s): is letterboxed on this stretch (800 of 1080 rows of picture)'},
                             {'where': 'shot 1', 'rule': 'subject_drift', 'detail': 'shot 1: the subject leaves the window'}])
        self.assertEqual(job['layout'], 'showcase')
        self.assertTrue(job['letterbox_ok'] and job['drift_ok'])
        self.assertEqual([l['step'] for l in SG.LADDER], ['a', 'a', 'b'])

    def test_gate_ladder_cards_keep_crop(self):
        job = {'shots': [['a.mp4', 5.0, 3.0, None]], 'gfx': [{'file': 'x'}]}
        RJ.gate_ladder(job, [{'where': 'shot 0', 'rule': 'shot_timing', 'detail': 'is letterboxed; crosses the trailer\'s scene cut at 6.0 s'}])
        self.assertNotIn('layout', job)
        self.assertTrue(job['letterbox_ok'] and job['cut_ok'])

    def test_fix_reading_extends(self):
        job = {'shots': [['a.mp4', 0.0, 3.6, None], ['a.mp4', 5.0, 1.0, None]],
               'lines': [[1, 1, ['هذا سطر طويل جدا لا يمكن قراءته في ثانية واحدة أبدا']]]}
        n = SG.fix_reading(job, RJ._starts, RJ.place, reel.read_secs)
        self.assertGreaterEqual(n, 1)
        st, end = RJ._starts(job)
        reel.SOFT = False
        try:
            reel.check_reading(RJ.place(job)(st, end), end)     # no longer too fast
        finally:
            reel.SOFT = False
        self.assertEqual(SG.LADDER[0]['kind'], 'text')

    def test_fact_flag_is_hard(self):
        self.assertEqual(SG.fact_flag({'fact_flag': 'the date is wrong'}), 'the date is wrong')
        self.assertEqual(SG.fact_flag({}), '')

    def test_qc_soft_findings_are_warnings(self):
        import qc
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, 'r.log')
            open(log, 'w').write('length 9.0 s before the end card\nclose: the last 2 s are a card\n'
                                 'softgate: ladder: {"kind": "picture", "slot": 0, "step": "b", "why": "x"}\n')
            out = qc.write({'name': 'x', 'template': 'trailer'}, os.path.join(d, 'x.mp4'), os.path.join(d, 'q.json'), log=log)
            self.assertEqual(out['verdict'], 'pass')
            self.assertEqual({w['stage'] for w in out['warnings']}, {'length', 'close'})
            self.assertEqual(out['ladder'][0]['step'], 'b')
            log2 = os.path.join(d, 'r2.log')
            open(log2, 'w').write('collision: line 2 over the card text\n')
            self.assertEqual(qc.write({'name': 'x'}, os.path.join(d, 'x.mp4'), os.path.join(d, 'q2.json'), log=log2)['verdict'], 'fail')
            strict = qc.write({'name': 'x', 'strict': True}, os.path.join(d, 'x.mp4'), os.path.join(d, 'q3.json'), log=log)
            self.assertEqual(strict['verdict'], 'fail')

    def test_look_picks_free_theme(self):
        import looks
        keep = looks.last
        looks.last = lambda n=2, exclude=None: [{'name': 'a', 'theme': 'cold', 'style': 'lines'},
                                                {'name': 'b', 'theme': 'cold', 'style': 'bold'}]
        try:
            job = {'name': 'z', 'theme': 'cold', 'style': 'glow'}
            RJ.look(job)
            self.assertNotEqual(job['theme'], 'cold')
            with self.assertRaises(SystemExit):
                RJ.look({'name': 'z', 'theme': 'cold', 'style': 'glow', 'strict': True})
        finally:
            looks.last = keep


class Library(unittest.TestCase):
    def test_record_and_lookup(self):
        import footlib as FL
        lib = {'files': {}}
        job = {'name': 'a', 'story': 's', 'footage': [{'file': 'a-t.mp4', 'steam': 730, 'trailer': 'Launch'}],
               'shots': [['a-t.mp4', 6.5, 2.2, 0.5], ['a-t.mp4', 12.0, 3.0, None]]}
        FL.record(job, lib=lib)
        self.assertEqual(len(FL.for_handle('steam:730', lib)), 1)
        self.assertEqual(len(FL.for_handle('730', lib)), 1)
        other = {'footage': [{'file': 'b-t.mp4', 'steam': 730, 'trailer': 'Launch'}]}
        self.assertEqual([x[0] for x in FL.stretches_for_file('b-t.mp4', lib, other)], [6.5, 12.0])
        self.assertTrue(FL.candidates('steam:730', lib)[0]['library'])
        self.assertEqual(FL.record(job, {'findings': [{'check': 'decode'}]}, lib=lib), [])


if __name__ == '__main__':
    unittest.main()
