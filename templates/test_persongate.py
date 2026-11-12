"""Tests for adv-20261111-person-stories-gate: people stories show the person; report is a label, not a kind.

    python3 templates/test_persongate.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buildgate as BG  # noqa: E402
import formats  # noqa: E402
import qc  # noqa: E402

HARADA = {'name': 'كاتسوهيرو هارادا', 'role': 'منتج سلسلة TEKKEN', 'photo_source': 'Bandai Namco press site'}


class Gate(unittest.TestCase):
    def test_story_needs_the_key(self):
        p = BG.person_problems({'kind_news': 'update'}, {'game': 'TEKKEN 8'})
        self.assertTrue(any('subject_person' in x for x in p))
        self.assertEqual(BG.person_problems({'kind_news': 'update'}, {'game': 'TEKKEN 8', 'subject_person': None}), [])

    def test_harada_case_refused(self):
        story = {'game': 'TEKKEN 8', 'subject_person': HARADA}
        p = BG.person_problems({'kind_news': 'report'}, story)
        self.assertTrue(any('label' in x for x in p))                 # report is a label
        self.assertTrue(any(x.startswith('person:') for x in p))      # no person entry
        self.assertTrue(any('"subject_person"' in x and 'copied' in x for x in p))

    def test_person_on_frame_zero_passes(self):
        story = {'game': 'TEKKEN 8', 'subject_person': HARADA}
        job = {'kind_news': 'quote', 'subject_person': HARADA,
               'person': [['harada.jpg', HARADA['name'], HARADA['role'], 0.0, 3.5, {}]]}
        self.assertEqual(BG.person_problems(job, story), [])
        late = dict(job, person=[['harada.jpg', HARADA['name'], HARADA['role'], 1.2, 3.5, {}]])
        self.assertTrue(any('frame 0' in x for x in BG.person_problems(late, story)))

    def test_no_photo_needs_searched(self):
        story = {'game': 'TEKKEN 8', 'subject_person': HARADA}
        job = {'kind_news': 'quote', 'subject_person': HARADA, 'person_photo': 'none',
               'person': [['tekken8-key-art.jpg', HARADA['name'], HARADA['role'], 0.0, 3.5, {}]]}
        self.assertTrue(any('searched' in x for x in BG.person_problems(job, story)))
        self.assertEqual(BG.person_problems(dict(job, searched=['Bandai Namco press site', 'Wikimedia Commons']), story), [])

    def test_quote_kind_needs_a_person_without_subject(self):
        p = BG.person_problems({'kind_news': 'quote'}, {'game': 'X', 'subject_person': None})
        self.assertTrue(any(x.startswith('person:') for x in p))

    def test_report_allowed_for_industry_story(self):
        self.assertEqual(BG.person_problems({'kind_news': 'report'}, {'game': '', 'subject_person': None}), [])

    def test_bad_subject_shape(self):
        p = BG.person_problems({'kind_news': 'update'}, {'game': 'X', 'subject_person': {'name': 'A'}})
        self.assertTrue(any('all three' in x for x in p))


class Pick(unittest.TestCase):
    def test_report_refused_for_one_game(self):
        with self.assertRaises(ValueError):
            formats.pick('report', single_game=True)
        self.assertIn(formats.pick('people'), ('trailer', 'quote'))


class QC(unittest.TestCase):
    def test_person_shown(self):
        self.assertEqual(qc.person_shown({'kind_news': 'update'}), 'n/a')
        self.assertIs(qc.person_shown({'kind_news': 'quote'}), False)
        self.assertIs(qc.person_shown({'subject_person': HARADA, 'person': [['a.jpg', 'n', 'r', 0.0, 3, {}]]}), True)
        self.assertIs(qc.person_shown({'subject_person': HARADA, 'person': [['a.jpg', 'n', 'r', 2.0, 3, {}]]}), False)


if __name__ == '__main__':
    unittest.main()
