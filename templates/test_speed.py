"""adv-20261117-server-speed-for-p2 A and B: the fast read's label rule and the footage resolver's source rules."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import footage as FT  # noqa: E402
import shotpick as SP  # noqa: E402


def page(own_nsuid, related):
    apollo = {
        'Product:{"sku":"1"}': {'__typename': 'Product', 'nsuid': related, 'urlKey': 'other-game-switch-2',
                                'productGallery': [{'publicId': f'/store/software/switch2/{related}/Video/aaa',
                                                    'resourceType': 'video'}]},
        'Product:{"sku":"2"}': {'__typename': 'Product', 'nsuid': own_nsuid, 'urlKey': 'the-game-switch-2',
                                'name': 'The Game',
                                'productGallery': [{'publicId': f'/store/software/switch2/{own_nsuid}/Video/bbb',
                                                    'resourceType': 'video'},
                                                   {'publicId': f'/store/software/switch2/{own_nsuid}/Image/ccc',
                                                    'resourceType': 'image'}]}}
    data = {'props': {'pageProps': {'analytics': {'product': {'nsuid': own_nsuid, 'name': 'The Game'}},
                                    'initialApolloState': apollo}}}
    return '<html><script id="__NEXT_DATA__" type="application/json">' + json.dumps(data) + '</script></html>'


class Resolver(unittest.TestCase):
    URL = 'https://www.nintendo.com/us/store/products/the-game-switch-2/'

    def test_nintendo_takes_the_pages_own_product_only(self):
        nsuid, name, vids = FT.nintendo_own(page('70010000000002', '70010000000001'), self.URL)
        self.assertEqual(nsuid, '70010000000002')
        self.assertEqual(vids, ['/store/software/switch2/70010000000002/Video/bbb'])   # no related video, no image

    def test_nintendo_falls_back_to_the_slug(self):
        html = page('70010000000002', '70010000000001').replace('"analytics": {"product": {"nsuid": "70010000000002", "name": "The Game"}}, ', '')
        self.assertEqual(FT.nintendo_own(html, self.URL)[0], '70010000000002')

    def test_sources_allowed(self):
        self.assertEqual(FT.classify('steam:4856440'), ('steam', '4856440'))
        self.assertEqual(FT.classify('https://store.steampowered.com/app/4856440/RPG/')[0], 'steam')
        self.assertEqual(FT.classify(self.URL)[0], 'nintendo')
        self.assertEqual(FT.classify('https://www.ign.com/videos/some-trailer')[0], 'ign')
        self.assertEqual(FT.classify('https://www.playstation.com/en-us/games/x/')[0], 'playstation')
        for bad in ('https://example.com/x', 'http://www.ign.com/videos/x', 'https://www.ign.com/articles/x',
                    'https://www.nintendo.com/us/whatsnew/x/', 'file:///etc/passwd', 'steam:abc'):
            with self.assertRaises(SystemExit):
                FT.classify(bad)


class Labels(unittest.TestCase):
    def test_a_word_in_one_place_on_many_frames_is_a_label(self):
        box = (['FOOTAGE', 600, 1000, 680, 1020],)
        boxes = {t / 2: ([tuple(box[0])] if t % 2 == 0 else [], 1280, 100) for t in range(20)}
        self.assertIn('FOOTAGE', SP._labels(boxes))

    def test_a_word_seen_once_is_not(self):
        boxes = {t / 2: ([('TITLE', 100, 100, 300, 140)] if t == 3 else [], 1280, 100) for t in range(20)}
        self.assertEqual(SP._labels(boxes), {})

    def test_a_word_moving_around_is_not(self):
        boxes = {t / 2: ([('SCORE', 60 * t, 100, 60 * t + 50, 120)], 1280, 100) for t in range(20)}
        self.assertEqual(SP._labels(boxes), {})


if __name__ == '__main__':
    unittest.main()
