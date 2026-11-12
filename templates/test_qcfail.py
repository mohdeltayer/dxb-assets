"""Tests for adv-20261112-qc-notes-become-failures: what the server measures fails the Reel.

    python3 templates/test_qcfail.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import qc  # noqa: E402

LIFE_OVER = 'render_job: lifeless: ' + json.dumps({'score': 68.0, 'still_share': 0.882, 'longest_still': 6.4, 'over': True})
LIFE_OK = 'render_job: lifeless: ' + json.dumps({'score': 20.0, 'still_share': 0.1, 'longest_still': 1.0, 'over': False})


class Findings(unittest.TestCase):
    def test_roblox_notes_fail(self):
        f = qc.findings_from_notes({'template': 'numbers'}, [LIFE_OVER, 'close: the last 2 s are a card; end on a picture'])
        self.assertEqual(sorted(x['check'] for x in f), ['close', 'lifeless'])

    def test_lifeless_exempt_storybeat_and_tribute(self):
        self.assertEqual(qc.findings_from_notes({'template': 'storybeat'}, [LIFE_OVER]), [])
        self.assertEqual(qc.findings_from_notes({'template': 'stills', 'tribute': True}, [LIFE_OVER]), [])
        self.assertEqual(qc.findings_from_notes({'template': 'trailer'}, [LIFE_OK]), [])

    def test_length_under_12_fails_unless_exempt(self):
        n = ['length 9.8 s before the end card (target 12 to 20 s)']
        self.assertEqual([x['check'] for x in qc.findings_from_notes({'template': 'split'}, n)], ['length'])
        self.assertEqual(qc.findings_from_notes({'template': 'handson'}, n), [])
        self.assertEqual(qc.findings_from_notes({'template': 'trailer', 'profile': 'breaking'}, n), [])
        self.assertEqual(qc.findings_from_notes({'template': 'split'}, ['length 14.2 s before the end card']), [])

    def test_close_exempt_for_storybeat(self):
        self.assertEqual(qc.findings_from_notes({'template': 'storybeat'}, ['close: the last 2 s are a card']), [])


class CardLines(unittest.TestCase):
    def setUp(self):
        import render_job as RJ
        self.RJ = RJ
        self.d = tempfile.mkdtemp()
        card = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        ImageDraw.Draw(card).rectangle((100, 930, 900, 1470), fill=(255, 255, 255, 255))   # logofact plate to the floor
        card.save(f'{self.d}/x-gfx-a.png')
        line = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        ImageDraw.Draw(line).rectangle((200, 1300, 880, 1380), fill=(255, 255, 255, 255))
        line.save(f'{self.d}/l1.png')
        self.job = {'shots': [['t.mp4', 0, 3], ['x-gfx-a.png', 0, 3]]}

    def test_two_lines_over_a_card_and_collision(self):
        p = self.RJ.card_line_problems(self.job, [(1, 1, 1, 'سطر', f'{self.d}/l1.png', 2)], self.d)
        self.assertEqual(len(p), 2)
        self.assertTrue(p[1]['detail'].startswith('collision:'))

    def test_line_on_footage_is_fine(self):
        self.assertEqual(self.RJ.card_line_problems(self.job, [(1, 0, 0, 'سطر', f'{self.d}/l1.png', 2)], self.d), [])

    def test_insert_covers_the_card(self):
        job = dict(self.job, insert=[{'shot': 1}])
        self.assertEqual(self.RJ.card_line_problems(job, [(1, 1, 1, 'سطر', f'{self.d}/l1.png', 2)], self.d), [])


class Art(unittest.TestCase):
    def setUp(self):
        import render_job as RJ
        self.RJ = RJ
        self.d = tempfile.mkdtemp()
        Image.new('RGB', (768, 424), (90, 40, 40)).save(f'{self.d}/tile.png')
        Image.new('RGB', (1920, 1080), (90, 40, 40)).save(f'{self.d}/hero.png')
        logo = Image.new('RGBA', (600, 200), (0, 0, 0, 0))
        ImageDraw.Draw(logo).rectangle((50, 50, 550, 150), fill=(20, 20, 20, 255))
        logo.save(f'{self.d}/logo.png')

    def test_thumbnail_ground_refused(self):
        with self.assertRaises(ValueError):
            self.RJ.card_art_check({'ground_still': f'{self.d}/tile.png'})
        self.RJ.card_art_check({'ground_still': f'{self.d}/hero.png'})

    def test_tile_as_logo_refused(self):
        with self.assertRaises(ValueError):
            self.RJ.card_art_check({'gfx': [{'kind': 'logofact', 'file': 'a', 'logo': f'{self.d}/tile.png'}]})
        self.RJ.card_art_check({'gfx': [{'kind': 'logofact', 'file': 'a', 'logo': f'{self.d}/logo.png'}]})


class Motion(unittest.TestCase):
    def test_count_format(self):
        import cardgfx as CG
        self.assertEqual(CG._counted('50 مليون', 0.5), '25 مليون')
        self.assertEqual(CG._counted('1,234,567', 0.0), '0')
        self.assertEqual(CG._counted('81.51', 1.0), '81.51')
        for v in ('25 فبراير 2027', '2027', '9/10', '15:00', 'بلا رقم'):
            self.assertIsNone(CG._counted(v, 0.5), v)

    def test_on_by_default_in_numbers_and_list(self):
        import cardgfx as CG
        self.assertTrue(CG.animated({'kind': 'ranking'}, {'template': 'numbers'}))
        self.assertTrue(CG.animated({'kind': 'logofact'}, {'template': 'list'}))
        self.assertFalse(CG.animated({'kind': 'fact', 'animate': False}, {'template': 'numbers'}))
        self.assertFalse(CG.animated({'kind': 'fact'}, {'template': 'split'}))
        self.assertTrue(CG.animated({'kind': 'fact', 'animate': True}, {'template': 'split'}))

    def test_staged_slide_order(self):
        import numgfx as NG
        with self.assertRaises(ValueError):
            NG.slide([('a.png', 0.5)], 3.0, 'cold', '/dev/null')
        with self.assertRaises(ValueError):
            NG.slide([('a.png', 0.0), ('b.png', 3.5)], 3.0, 'cold', '/dev/null')


class Presubmit(unittest.TestCase):
    def test_pass_refused_on_qc_fail_and_needs_looked(self):
        import presubmit as P
        keep_story, keep_ck, keep_qc, keep_blob = P.story, P.checklist, P.qc_of, P.blob
        d = tempfile.mkdtemp()
        sf = __import__('pathlib').Path(d) / 's.json'
        sf.write_text('{}')
        try:
            P.story = lambda sid: (sf, {})
            P.checklist = lambda job, out: {'ok': True, 'problems': [], 'built_by': 'builder'}
            P.blob = lambda out: '0' * 40
            P.qc_of = lambda out: {'verdict': 'fail', 'findings': [{'check': 'lifeless', 'detail': 'x'}]}
            with self.assertRaises(SystemExit):
                P.director('s', 'PASS', 'cards/x-reel-v1.mp4', job='j.json', by='director')
            P.qc_of = lambda out: {'verdict': 'pass', 'look_frames': ['cards/x-look-1.jpg']}
            with self.assertRaises(SystemExit):
                P.director('s', 'PASS', 'cards/x-reel-v1.mp4', job='j.json', by='director')
            P.director('s', 'PASS', 'cards/x-reel-v1.mp4', job='j.json', by='director', looked='card on art, rows fill')
            self.assertEqual(json.loads(sf.read_text())['director_check']['qc'], 'pass')
            P.qc_of = lambda out: {'verdict': 'fail', 'findings': []}
            P.director('s', 'FIX', 'cards/x-reel-v1.mp4', job='j.json', by='director')
        finally:
            P.story, P.checklist, P.qc_of, P.blob = keep_story, keep_ck, keep_qc, keep_blob


if __name__ == '__main__':
    unittest.main()
