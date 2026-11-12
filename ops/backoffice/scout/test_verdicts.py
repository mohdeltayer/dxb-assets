"""Tests for adv-20261111-scout-verdicts-on-work-order.

    python3 ops/backoffice/scout/test_verdicts.py
"""
import datetime as dt
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'keeper'))
import verdicts as V  # noqa: E402

DIGEST = """DXB hourly digest, Thu 12 Nov 2026, window 23:00 to 23:48 Dubai (GST)

PlayStation

NEW - Ghost of Yotei gets a PS5 Pro patch on 20 November
Claim: Sony says patch 1.20 adds a 60fps mode on PS5 Pro on 20 November.
Primary: https://blog.playstation.com/2026/11/12/ghost-of-yotei-update/
Status: confirmed by primary source
VERDICT: CONFIRMED
LABEL: رسمي
FACTS: Patch 1.20 on 20 November | "Patch 1.20 arrives November 20" | OK; 60fps mode on PS5 Pro | "a new 60fps mode for PS5 Pro" | OK
FOOTAGE: https://www.youtube.com/watch?v=abc
NOT CONFIRMED: Gulf store timing
Age: NEW (Sony 22:10 Dubai)

NEW - Fairgame$ reportedly cancelled
Claim: Bloomberg reports Sony cancelled Fairgame$.
Primary: https://www.bloomberg.com/news/articles/2026-11-11/fairgames
Status: reported by one outlet (paywalled)
VERDICT: CONFIRMED
LABEL: رسمي
FACTS: Fairgame$ cancelled | "Sony has cancelled Fairgame$" | OK
FOOTAGE: none
NOT CONFIRMED: Sony statement
Age: NEW

NEW - Studio denies Switch 2 port
Claim: X says a Switch 2 port is coming.
Outlet report: https://example-studio.com/news/statement
VERDICT: DENIED
LABEL: شائعة
FACTS: port denied | "no plans" | OK

SAME_DAY - Mega Man Legends rumour (minor)
Claim: a rumour.
Outlet report: https://x.com/i/status/1
Status: rumour
"""

SONY = ('<html><body><p>' + 'Ghost of Yotei patch notes. ' * 20 +
        'Patch 1.20 arrives November 20 with a new 60fps mode for PS5 Pro owners.</p></body></html>')


def fake_fetch(url):
    if 'playstation.com' in url:
        import re
        return re.sub(r'<[^>]+>', ' ', SONY)
    return None


class Parse(unittest.TestCase):
    def test_items_and_fields(self):
        items = V.parse(DIGEST)
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0]['VERDICT'], 'CONFIRMED')
        self.assertEqual(len(V.facts_of(items[0])), 2)
        self.assertFalse(V.has_verdict(items[3]))           # bare items pass through as today

    def test_check_and_labels(self):
        items = V.parse(DIGEST)
        c0 = V.check(items[0], fake_fetch)
        self.assertEqual(c0['result'], 'source_confirmed')
        self.assertEqual(V.label_for(items[0], c0), 'رسمي')     # company page, confirmed
        c1 = V.check(items[1], fake_fetch)
        self.assertEqual(c1['result'], 'source_unreadable')
        self.assertEqual(V.label_for(items[1], c1), 'تقرير')    # scout CONFIRMED on a page not opened
        self.assertIsNone(V.label_for(items[2], V.check(items[2], fake_fetch)))   # denied

    def test_mismatch(self):
        it = V.parse(DIGEST)[0]
        page = 'x ' * 300 + 'Patch 1.20 arrives November 21 with Ghost improvements'
        c = V.check(it, lambda u: page)
        self.assertEqual(c['result'], 'mismatch')
        self.assertEqual(V.label_for(it, c), 'تقرير')

    def test_never_stronger_than_the_scout(self):
        it = dict(V.parse(DIGEST)[0], LABEL='تقرير')
        self.assertEqual(V.label_for(it, V.check(it, fake_fetch)), 'تقرير')


class Run(unittest.TestCase):
    def test_run_and_work_order(self):
        out = os.path.join(tempfile.mkdtemp(), 'leads.json')
        doc = V.run(None, out, source=[('2026-11-12T19:48:00Z', DIGEST)], fetch=fake_fetch)
        self.assertEqual(len(doc['leads']), 3)
        self.assertEqual(doc['measure']['source_confirmed'], 1)
        import workorder as W
        now = dt.datetime(2026, 11, 12, 20, 0, tzinfo=dt.timezone.utc)
        wo = W.build({}, now, [], server={'scout': doc})
        md = W.markdown(wo)
        self.assertIn('LEAD Ghost of Yotei', md)
        self.assertIn('source_confirmed: build it', md)
        self.assertIn('DENIED (do not build)', md)
        self.assertIn('1 of 3 leads source_confirmed', md)

    def test_no_key(self):
        self.assertIsNone(V.run('/nonexistent/key', os.path.join(tempfile.mkdtemp(), 'x.json')))
        import workorder as W
        md = W.markdown(W.build({}, dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc), [], server={'scout': {'unavailable': 'key not installed'}}))
        self.assertIn('not read on the server (key not installed)', md)


if __name__ == '__main__':
    unittest.main()
