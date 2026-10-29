"""Offline unit tests for the prepare service (run by test.sh). Synthetic clips come from ffmpeg's testsrc; no network.
Every path lives in a temp folder; PREPARE_RENDER_CHECK=off except in the pause test."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

TMP = tempfile.mkdtemp(prefix='dxb-prepare-unit-')
os.environ.update({'PREPARE_HOME': os.path.join(TMP, 'home'), 'PREPARE_STORE': os.path.join(TMP, 'store'),
                   'PREPARE_RENDER_CHECK': 'off', 'PREPARE_HANDOFF': 'off', 'PREPARE_FLOOR_GB': '0', 'PREPARE_STEAM_SEARCH': 'off',
                   'PREPARE_WATCH_DB': os.path.join(TMP, 'watch.db'),
                   'PREPARE_WATCH_DIGEST': os.path.join(TMP, 'digest.json')})
os.environ.setdefault('PREPARE_MODELS', os.path.join(TMP, 'models'))
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)

import acquire as AQ    # noqa: E402
import analyse as AN    # noqa: E402
import prepare as PR    # noqa: E402
import handover as HO   # noqa: E402

RIGHTS = AQ.load_rights()


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y'] + list(args), check=True)


def make_clip(path, text=True):
    """Three scenes (testsrc2, a dark-blue card with burnt-in text, smptebars) with a sine tone, 1280x720 at 24 fps."""
    mid = "color=c=0x203040:size=1280x720:rate=24:duration=3"
    if text:
        mid += ",drawtext=text='OFFICIAL TRAILER PRESENTS':fontsize=72:fontcolor=white:x=(w-tw)/2:y=(h-th)/2"
    ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=1280x720:rate=24:duration=3', '-f', 'lavfi', '-i', mid,
           '-f', 'lavfi', '-i', 'smptebars=size=1280x720:rate=24:duration=3', '-f', 'lavfi', '-i',
           'sine=frequency=440:duration=9', '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]',
           '-map', '[v]', '-map', '3:a', '-c:v', 'libx264', '-b:v', '4M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', path)
    return path


CLIP = None


def clip():
    global CLIP
    if CLIP is None:
        CLIP = make_clip(os.path.join(TMP, 'clip.mp4'))
    return CLIP


def fake_http(pages):
    def get(url, max_bytes=0, timeout=0):
        if url not in pages:
            raise OSError('404 ' + url)
        return url, 'text/html', pages[url].encode()
    return get


def iso(delta_h=0):
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=delta_h)).strftime('%Y-%m-%dT%H:%M:%SZ')


class Reset(unittest.TestCase):
    def setUp(self):
        for d in (os.environ['PREPARE_HOME'], os.environ['PREPARE_STORE']):
            shutil.rmtree(d, ignore_errors=True)
        for f in (os.environ['PREPARE_WATCH_DB'], os.environ['PREPARE_WATCH_DIGEST']):
            if os.path.exists(f):
                os.remove(f)
        self._saved = {}

    def patch(self, mod, name, value):
        self._saved.setdefault((mod, name), getattr(mod, name))
        setattr(mod, name, value)

    def tearDown(self):
        for (mod, name), v in self._saved.items():
            setattr(mod, name, v)


# ------------------------------------------------------------------ the watch and the threshold

class WatchPick(Reset):
    def make_db(self, rows):
        c = sqlite3.connect(os.environ['PREPARE_WATCH_DB'])
        with open(os.path.join(REPO, 'ops', 'backoffice', 'watch', 'schema.sql')) as f:
            c.executescript(f.read())
        c.execute("INSERT INTO sources (id, name, kind, url, interval_min) VALUES ('s', 'S', 'official', 'u', 5)")
        for i, r in enumerate(rows, 1):
            c.execute('INSERT INTO items (id, source_id, source, kind, title, url, url_key, first_seen, summary, media, '
                      'breaking, baseline, junk) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                      (i, 's', r.get('source', 'S'), r['kind'], r['title'], r['url'], r['url'] + str(i),
                       r.get('first_seen', iso(1)), r.get('summary', ''), json.dumps(r.get('media', [])),
                       r.get('breaking', 0), r.get('baseline', 0), r.get('junk', 0)))
        c.commit()
        c.close()

    def test_threshold_and_order(self):
        yt = 'https://www.youtube.com/watch?v=abc'
        self.make_db([
            {'kind': 'youtube', 'title': 'Game A - Launch Trailer', 'url': yt, 'media': [{'type': 'video', 'url': yt}]},
            {'kind': 'outlet', 'title': 'Game B trailer reaction', 'url': 'https://outlet.example/b',
             'media': [{'type': 'video', 'url': yt}]},
            {'kind': 'official', 'title': 'Quarterly results', 'url': 'https://ir.example/q', 'breaking': 1},
            {'kind': 'youtube', 'title': 'Baseline trailer', 'url': yt + '1', 'baseline': 1,
             'media': [{'type': 'video', 'url': yt + '1'}]},
            {'kind': 'youtube', 'title': 'Junk trailer', 'url': yt + '2', 'junk': 1},
            {'kind': 'youtube', 'title': 'Old trailer', 'url': yt + '3', 'first_seen': iso(48),
             'media': [{'type': 'video', 'url': yt + '3'}]},
            {'kind': 'page', 'title': 'Game C announce', 'url': 'https://news.ubisoft.com/c', 'first_seen': iso(0.5),
             'summary': 'Wishlist https://store.steampowered.com/app/12345/Game_C/'},
        ])
        items, src = PR.watch_items(24)
        self.assertEqual(src, 'watch.db')
        self.assertEqual(len(items), 4)                       # baseline, junk and old are not read
        c = PR.db()
        chosen, total = PR.pick(items, c, 4, 5)
        self.assertEqual([x[2]['title'] for x in chosen], ['Game A - Launch Trailer', 'Game C announce'])
        self.assertEqual(chosen[0][0], 5)                    # official 2 + video 2 + trailer word 1
        self.assertIn('steam link', chosen[1][3])
        c.execute("INSERT INTO seen VALUES (?, 5, 'ready', '', 'k', ?)", (chosen[0][2]['watch_item'], iso()))
        c.commit()
        chosen2, _ = PR.pick(items, c, 4, 5)
        self.assertEqual([x[2]['title'] for x in chosen2], ['Game C announce'])

    def test_no_video_signal_never_passes(self):
        p, why = PR.score({'kind': 'official', 'title': 'Earnings call', 'url': 'https://x.example', 'breaking': 1})
        self.assertLessEqual(p, 1)

    def test_digest_fallback(self):
        with open(os.environ['PREPARE_WATCH_DIGEST'], 'w') as f:
            json.dump({'official': [{'id': 7, 'source': 'Xbox Wire', 'source_kind': 'official', 'title': 'X reveal trailer',
                                     'url': 'https://news.xbox.com/x', 'first_seen': iso(1), 'summary': '',
                                     'media': [{'type': 'video', 'url': 'https://news.xbox.com/x.mp4'}]}]}, f)
        items, src = PR.watch_items(24)
        self.assertEqual(src, 'digest.json')
        self.assertEqual(items[0]['watch_item'], 'watch:7')
        self.assertGreaterEqual(PR.score(items[0])[0], 4)

    def test_dry_run_command(self):
        self.make_db([{'kind': 'youtube', 'title': 'Game A - Trailer', 'url': 'https://youtu.be/x',
                       'media': [{'type': 'video', 'url': 'https://youtu.be/x'}]}])
        r = subprocess.run([sys.executable, os.path.join(HERE, 'prepare.py'), 'from-watch', '--dry-run'],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('1 above score 4', r.stdout)


# ------------------------------------------------------------------ acquisition order and rights

UBI_PAGE = """<html><body>
<a href="https://staticctf.ubisoft.com/kit/trailer_1080p.mp4">Download</a>
<video src="https://evil.example.com/rip.mp4"></video>
<a href="https://press.square-enix.com/kit/123">Press kit</a>
<a href="https://store.steampowered.com/app/2221490/">Steam</a>
<a href="https://www.youtube.com/watch?v=zzz">Watch</a>
<a href="https://www.twitch.tv/ubisoft">Live</a>
<p>This trailer is under embargo until 16:00 CET on 30 October.</p>
<p>Please note the music in this trailer is not cleared for use outside the trailer.</p>
</body></html>"""
SQEX_PAGE = '<a href="/files/kit/trailer-4k.mp4">4K</a>'


class Acquisition(Reset):
    def test_order_and_hosts(self):
        http = fake_http({'https://news.ubisoft.com/en-us/article/1': UBI_PAGE,
                          'https://press.square-enix.com/kit/123': SQEX_PAGE})
        cands, notes, pn = AQ.plan({'url': 'https://news.ubisoft.com/en-us/article/1', 'title': 'T'}, RIGHTS, http,
                                   steam_lookup=False)
        self.assertEqual([c['step'] for c in cands], [1, 2, 3, 4, 5])
        self.assertEqual(cands[0]['url'], 'https://staticctf.ubisoft.com/kit/trailer_1080p.mp4')
        self.assertEqual(cands[0]['publisher'], 'ubisoft')
        self.assertEqual(cands[1]['url'], 'https://press.square-enix.com/files/kit/trailer-4k.mp4')
        self.assertEqual(cands[1]['publisher'], 'square-enix')
        self.assertEqual(cands[2]['appid'], 2221490)
        self.assertTrue(any('evil.example.com' in n for n in notes))
        self.assertIn('embargo', pn['embargo'])
        self.assertIn('music', pn['music'])

    def test_cdn_only_from_publisher_page(self):
        self.assertEqual(AQ.accept_publisher_file(RIGHTS, 'https://d1.cloudfront.net/t.mp4', 'https://www.sega.com/news'),
                         'sega')
        self.assertIsNone(AQ.accept_publisher_file(RIGHTS, 'https://d1.cloudfront.net/t.mp4', 'https://www.ign.com/x'))
        self.assertIsNone(AQ.accept_publisher_file(RIGHTS, 'https://notubisoft.com/t.mp4', None))

    def test_youtube_and_twitch_refuse(self):
        for step in (4, 5):
            with self.assertRaises(AQ.Refused):
                AQ.fetch({'step': step, 'method': AQ.STEPS[step], 'url': 'https://x'}, os.path.join(TMP, 'n.mp4'),
                         RIGHTS)

    def test_youtube_page_is_never_read(self):
        def boom(*a, **k):
            raise AssertionError('YouTube page read')
        cands, _, _ = AQ.plan({'url': 'https://www.youtube.com/watch?v=1', 'title': 'x'}, RIGHTS, boom,
                              steam_lookup=False)
        self.assertEqual([c['step'] for c in cands], [5])

    def test_rights_records(self):
        n = AQ.rights_record(RIGHTS, 'nintendo')
        self.assertTrue(n['excerpt_only'] and n['on_screen_credit'])
        self.assertEqual(n['basis'], 'fan guidelines')
        cap = AQ.rights_record(RIGHTS, AQ.publisher_for_steam(RIGHTS, ['CAPCOM Co., Ltd.']))
        self.assertEqual(cap['register_key'], 'capcom')
        self.assertTrue(cap['music_flag'] and cap['rights_review'])
        unk = AQ.rights_record(RIGHTS, None, ['Tiny Indie'])
        self.assertEqual(unk['basis'], 'unreviewed')
        self.assertTrue(unk['rights_review'])
        self.assertEqual(AQ.rights_record(RIGHTS, 'square-enix')['basis'], 'press grant')
        self.assertIn('Ubisoft', AQ.rights_record(RIGHTS, 'ubisoft')['music_flag'])

    def test_register_lists_every_publisher(self):
        with open(os.path.join(REPO, 'ops', 'rights-register.md'), encoding='utf-8') as f:
            reg = f.read()
        for key, p in RIGHTS['publishers'].items():
            self.assertIn(p['name'], reg, key)
            self.assertIn(p['basis'], reg, key)

    def test_choose_movie(self):
        mv = [{'id': 10, 'name': 'Announcement Trailer', 'hls': 'a'}, {'id': 30, 'name': 'Launch Trailer', 'hls': 'b'},
              {'id': 20, 'name': 'Gameplay Overview', 'hls': 'c'}]
        self.assertEqual(AQ.choose_movie(mv, 'Game - Launch Trailer')[0]['id'], 30)
        self.assertEqual(AQ.choose_movie(mv, 'Game - Gameplay Overview')[0]['id'], 20)
        self.assertEqual(AQ.choose_movie(mv, 'Something else')[0]['id'], 30)     # no overlap: the newest

    def test_steam_search_needs_a_name_match(self):
        body = json.dumps({'items': [{'id': 99, 'name': 'Other Game'}, {'id': 5, 'name': 'Space Game'}]})
        http = lambda url, *a, **k: (url, 'application/json', body.encode())  # noqa: E731
        self.assertEqual(AQ.steam_search('Space Game - Launch Trailer | PS5', http), 5)
        self.assertIsNone(AQ.steam_search('Unrelated - Trailer', http))

    def test_steam_fetch_with_local_stream(self):
        self.patch(AQ, 'steam_app', lambda appid, http=None: {
            'appid': appid, 'name': 'Space Game', 'publishers': ['SEGA'],
            'movies': [{'id': 7, 'name': 'Launch Trailer', 'hls': clip(), 'highlight': True}]})
        dst = os.path.join(TMP, 'steam.mp4')
        src, rec = AQ.fetch({'step': 3, 'method': 'steam', 'appid': 5, 'page': 'p'}, dst, RIGHTS, 'Launch Trailer')
        self.assertTrue(os.path.getsize(dst) > 100000)
        self.assertEqual(src['steam']['render_job_footage'], {'steam': 5, 'trailer': 'Launch Trailer', 'trailer_id': 7})
        self.assertEqual(rec['register_key'], 'sega')

    def test_links_and_appids(self):
        ls = AQ.links('<a href="/a.mp4">x</a> see https://store.steampowered.com/app/42/X', 'https://sega.com/n/')
        self.assertIn('https://sega.com/a.mp4', ls)
        self.assertEqual(AQ.steam_appids(' '.join(ls)), [42])


# ------------------------------------------------------------------ analysis and the stored asset

class Asset(Reset):
    def test_local_synthetic_asset(self):
        c = PR.db()
        st, key, detail = PR.prepare_item({'local': clip(), 'publisher': 'sega', 'page': 'test'}, 'Synthetic', RIGHTS, c)
        self.assertEqual(st, 'ready', detail)
        d = os.path.join(os.environ['PREPARE_STORE'], key)
        with open(os.path.join(d, 'manifest.json')) as f:
            m = json.load(f)
        self.assertTrue(m['checks']['decode']['clean'])
        self.assertGreaterEqual(len(m['scenes']), 2)
        self.assertEqual(m['rights']['register_key'], 'sega')
        for k in ('probe', 'decode', 'smear', 'scenes', 'frames', 'faces', 'subjects', 'text', 'blocks', 'total'):
            self.assertIn(k, m['timings'])
        self.assertTrue(os.path.exists(os.path.join(d, 'sheet.jpg')))
        self.assertTrue(os.path.exists(os.path.join(d, 'source.mp4')))
        if shutil.which('tesseract'):
            words = {w for s in m['scenes'] for w in s['text_words']}
            self.assertTrue({'OFFICIAL', 'TRAILER'} & words, words)
        with open(os.path.join(os.environ['PREPARE_HOME'], 'timings.jsonl')) as f:
            self.assertEqual(json.loads(f.readline())['key'], key)
        self.assertEqual(PR.prepare_item({'local': clip(), 'publisher': 'sega'}, 'Synthetic', RIGHTS, c)[0], 'exists')

    def test_damaged_source(self):
        bad = os.path.join(TMP, 'bad.mp4')
        shutil.copy(clip(), bad)
        with open(bad, 'r+b') as f:
            f.seek(400000)
            f.write(os.urandom(300000))
        c = PR.db()
        st, key, detail = PR.prepare_item({'local': bad, 'publisher': 'sega'}, 'Damaged', RIGHTS, c)
        self.assertEqual(st, 'damaged', detail)
        d = os.path.join(os.environ['PREPARE_STORE'], key)
        self.assertFalse(os.path.exists(os.path.join(d, 'source.mp4')))   # never kept for shots
        with open(os.path.join(d, 'manifest.json')) as f:
            self.assertGreater(json.load(f)['checks']['decode']['errors'], 0)

    def test_publisher_file_end_to_end(self):
        page = 'https://www.sega.com/news/x'
        self.patch(AQ, 'http_get', fake_http({page: '<a href="https://cdn.sega.com/t.mp4">t</a> embargo until Friday.'}))

        def stream(url, dst, max_bytes, timeout=60):
            self.assertEqual(url, 'https://cdn.sega.com/t.mp4')
            shutil.copy(clip(), dst)
            return os.path.getsize(dst), 'video/mp4'
        self.patch(AQ, 'http_stream', stream)
        c = PR.db()
        st, key, _ = PR.prepare_item({'url': page, 'title': 'X trailer'}, 'Sega X', RIGHTS, c)
        self.assertEqual(st, 'ready')
        with open(os.path.join(os.environ['PREPARE_STORE'], key, 'manifest.json')) as f:
            m = json.load(f)
        self.assertEqual(m['source']['method'], 'publisher_file')
        self.assertEqual(m['source']['url'], 'https://cdn.sega.com/t.mp4')
        self.assertEqual(m['source']['page'], page)
        self.assertIn('embargo', m['rights']['embargo'])

    def test_duplicate_source(self):
        """The same trailer seen on two channels (Witchbrook on Xbox and PlayStation) is prepared once."""
        self.patch(AQ, 'steam_app', lambda appid, http=None: {
            'appid': appid, 'name': 'W', 'publishers': ['Tiny Indie'],
            'movies': [{'id': 9, 'name': 'Release Date Trailer', 'hls': clip(), 'highlight': True}]})
        self.patch(AQ, 'plan', lambda item, rights, http=None, steam_lookup=True: (
            [{'step': 3, 'method': 'steam', 'appid': 5, 'page': 'p'}], [], {'embargo': None, 'music': None}))
        c = PR.db()
        a = PR.prepare_item({'url': 'https://www.youtube.com/watch?v=1', 'title': 'W - Release Date Trailer'},
                            'From Xbox', RIGHTS, c)
        b = PR.prepare_item({'url': 'https://www.youtube.com/watch?v=2', 'title': 'W - Release Date Trailer | PS5'},
                            'From PlayStation', RIGHTS, c)
        self.assertEqual(a[0], 'ready')
        self.assertEqual(b[:2], ('duplicate', a[1]))
        with open(os.path.join(os.environ['PREPARE_STORE'], a[1], 'manifest.json')) as f:
            m = json.load(f)
        self.assertTrue(m['rights']['rights_review'])                       # unknown publisher: flagged
        self.assertEqual(m['source']['steam']['render_job_footage']['trailer_id'], 9)   # no stream path: movie id
        self.assertEqual(AQ.stream_id('https://video.akamai.steamstatic.com/store_trailers/2065580/759929/9153d1/'
                                      '1751070739/hls_264_master.m3u8?t=1'), 759929)

    def test_only_refusals_recorded(self):
        c = PR.db()
        st, key, detail = PR.prepare_item({'url': 'https://www.youtube.com/watch?v=q', 'title': 'q'}, 'YT', RIGHTS, c)
        self.assertEqual(st, 'refused')
        self.assertIn('YouTube fallback is off', detail)
        self.assertFalse(os.path.exists(os.path.join(os.environ['PREPARE_STORE'], key)))

    def test_focus_and_nanodet_decode(self):
        self.assertEqual(AN.focus_for([860, 400, 200, 200], [0, 0, 1920, 1080]), 0.5)
        self.assertEqual(AN.focus_for([1800, 400, 100, 200], [0, 0, 1920, 1080]), 1.0)
        self.assertEqual(AN.focus_for([0, 400, 100, 200], [0, 0, 1920, 1080]), 0.0)
        import numpy as np
        cls = [np.zeros((1, n, 80), np.float32) for n in (2704, 676, 169)]
        reg = [np.zeros((1, n, 32), np.float32) for n in (2704, 676, 169)]
        cls[1][0, 13 * 26 + 13, 0] = 0.9                   # stride 16, cell (13, 13): a person near the centre
        reg[1][0, 13 * 26 + 13, :] = np.tile(np.eye(8)[4] * 20, 4)     # distance 4 * 16 = 64 px each side
        out = AN.nanodet_decode([cls[0], cls[1], cls[2], reg[0], reg[1], reg[2]])
        self.assertEqual(out[0]['label'], 'person')
        x, y, w, h = out[0]['box']
        self.assertAlmostEqual(w, 128, delta=2)
        self.assertAlmostEqual(x + w / 2, 13 * 16 + 7.5, delta=2)

    def test_picture_box(self):
        import numpy as np
        f = np.zeros((720, 1280, 3), np.uint8)
        f[90:630] = 120
        self.assertEqual(AN.picture_box([f]), [0, 90, 1280, 540])
        self.assertEqual(AN.picture_box([np.zeros((720, 1280, 3), np.uint8)]), [0, 0, 1280, 720])

    @unittest.skipUnless(AN.model_path('yunet') and AN.model_path('nanodet'), 'models not in the cache')
    def test_detectors_load(self):
        import numpy as np
        d = AN.Detectors()
        fr = np.full((720, 1280, 3), 90, np.uint8)
        self.assertEqual(d.faces(fr), [])
        self.assertIsInstance(d.subjects(fr), list)


# ------------------------------------------------------------------ disk, cleanup, pause, beats

class Housekeeping(Reset):
    def fake_asset(self, name, age_h):
        d = os.path.join(os.environ['PREPARE_STORE'], name)
        os.makedirs(d)
        with open(os.path.join(d, 'manifest.json'), 'w') as f:
            json.dump({'created_at': iso(age_h)}, f)
        with open(os.path.join(d, 'source.mp4'), 'wb') as f:
            f.write(b'0' * 1000)
        if name.endswith('.partial'):
            t = time.time() - age_h * 3600
            os.utime(d, (t, t))
        return d

    def test_expiry(self):
        self.fake_asset('old', 8 * 24)
        self.fake_asset('young', 24)
        self.fake_asset('half.partial', 3)
        gone = dict(PR.cleanup())
        self.assertIn('old', gone)
        self.assertIn('half.partial', gone)
        self.assertNotIn('young', gone)
        self.assertTrue(os.path.isdir(os.path.join(os.environ['PREPARE_STORE'], 'young')))

    def test_floor_evicts_oldest_first_but_not_new(self):
        self.fake_asset('a', 50)
        self.fake_asset('b', 30)
        self.fake_asset('fresh', 0.2)
        self.patch(PR, 'free_gb', lambda p: 10.0)
        os.environ['PREPARE_FLOOR_GB'] = '40'
        try:
            gone = [n for n, _ in PR.cleanup()]
        finally:
            os.environ['PREPARE_FLOOR_GB'] = '0'
        self.assertEqual(gone, ['a', 'b'])
        self.assertTrue(os.path.isdir(os.path.join(os.environ['PREPARE_STORE'], 'fresh')))

    def test_floor_blocks_fetch(self):
        self.patch(PR, 'free_gb', lambda p: 5.0)
        os.environ['PREPARE_FLOOR_GB'] = '40'

        def never(*a, **k):
            raise AssertionError('fetched under the floor')
        self.patch(AQ, 'fetch', never)
        self.patch(AQ, 'plan', lambda *a, **k: ([{'step': 1, 'method': 'publisher_file', 'url': 'u'}], [],
                                                {'embargo': None, 'music': None}))
        try:
            st, _, detail = PR.prepare_item({'url': 'https://www.sega.com/x'}, 'Floor', RIGHTS, PR.db())
        finally:
            os.environ['PREPARE_FLOOR_GB'] = '0'
        self.assertEqual(st, 'disk-floor', detail)

    def test_render_pause(self):
        marker = 'dxbprepare-fake-render-%d' % os.getpid()
        p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)', marker])
        try:
            time.sleep(0.3)
            env = dict(os.environ, PREPARE_BUSY_PATTERN=marker)
            env.pop('PREPARE_RENDER_CHECK')
            r = subprocess.run([sys.executable, os.path.join(HERE, 'prepare.py'), 'from-watch'], env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, PR.PAUSED, r.stdout + r.stderr)
            self.assertIn('paused', r.stdout)
            os.environ['PREPARE_BUSY_PATTERN'] = marker
            os.environ.pop('PREPARE_RENDER_CHECK')
            self.patch(PR, 'BUSY', marker)
            with self.assertRaises(PR.Paused):
                PR.wait_idle(max_wait=0)
        finally:
            os.environ['PREPARE_RENDER_CHECK'] = 'off'
            os.environ.pop('PREPARE_BUSY_PATTERN', None)
            p.kill()
            p.wait()

    def test_lock(self):
        with PR.lock() as a:
            self.assertTrue(a)
            r = subprocess.run([sys.executable, os.path.join(HERE, 'prepare.py'), 'from-watch'], capture_output=True,
                               text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn('another pass is running', r.stdout)

    def test_beats_cached(self):
        try:
            import librosa  # noqa: F401
        except ImportError:
            self.skipTest('librosa not installed')
        import numpy as np
        sr, bpm = 22050, 120
        y = np.zeros(sr * 12, np.float32)
        click = np.sin(2 * np.pi * 1000 * np.arange(int(0.03 * sr)) / sr).astype(np.float32)
        for t in np.arange(0, 12, 60 / bpm):
            i = int(t * sr)
            y[i:i + len(click)] += click
        wav = os.path.join(TMP, 'bed.wav')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-',
                        wav], input=y.tobytes(), check=True)
        cache = os.path.join(TMP, 'beats')
        b = AN.beats(wav, cache)
        self.assertFalse(b['cached'])
        self.assertTrue(any(abs(b['tempo'] - k * bpm) < 4 for k in (0.5, 1, 2)), b['tempo'])
        self.assertGreater(b['n'], 10)
        self.assertTrue(AN.beats(wav, cache)['cached'])


class Handover(Reset):
    """The index and sheets that go to dxb-watch (branch prepared): content, no local paths, unchanged-skip, push."""

    def logs(self):
        out = []
        return out, (lambda *a: out.append(' '.join(str(x) for x in a)))

    def test_index_and_sheets_dry(self):
        c = PR.db()
        st, key, _ = PR.prepare_item({'local': clip(), 'publisher': 'sega', 'page': 'https://www.sega.com/p?sig=x'},
                                     'Synthetic', RIGHTS, c)
        self.assertEqual(st, 'ready')
        PR.put_asset(c, key='refused-one', name='YouTube only', status='refused', request='u', created_at=iso(),
                     detail='youtube: step 5 is off')
        if True:   # PREPARE_HANDOFF=off for the whole suite: nothing is ever pushed by a test
            _, log = self.logs()
            home = os.environ['PREPARE_HOME']
            self.assertEqual(HO.run(c, os.environ['PREPARE_STORE'], home, iso(), log), 'dry')
            out = os.path.join(home, 'handover', 'out', 'prepared')
            with open(os.path.join(out, 'index.json')) as f:
                idx = json.load(f)
            self.assertEqual((idx['assets'], idx['ready']), (2, 1))
            e = next(x for x in idx['entries'] if x['key'] == key)
            self.assertEqual(e['rights']['register_key'], 'sega')
            self.assertEqual(e['sheet'], f'prepared/sheets/{key}.jpg')
            self.assertTrue(os.path.exists(os.path.join(out, 'sheets', key + '.jpg')))
            self.assertIn('scenes', e['summary'])
            text = json.dumps(idx)
            self.assertNotIn(os.environ['PREPARE_STORE'], text)          # no server paths leave the server
            self.assertNotIn(TMP, text)
            self.assertNotIn('?sig=', text)                               # no signed query strings
            r = next(x for x in idx['entries'] if x['key'] == 'refused-one')
            self.assertEqual(r['status'], 'refused')
            # nothing changed: no second write and no push
            c.execute("INSERT OR REPLACE INTO meta VALUES ('handover_digest', ?)",
                      (HO.digest(HO.build(os.environ['PREPARE_STORE'],
                                          [dict(x) for x in c.execute('SELECT * FROM assets ORDER BY created_at DESC')])[0]),))
            c.commit()
            self.assertEqual(HO.run(c, os.environ['PREPARE_STORE'], home, iso(), log), 'unchanged')

    def test_never_the_watch_branch(self):
        os.environ['PREPARE_HANDOFF_BRANCH'] = 'main'
        try:
            with self.assertRaises(ValueError):
                HO.config()
        finally:
            os.environ.pop('PREPARE_HANDOFF_BRANCH', None)

    def test_push_replaces_the_branch(self):
        bare = os.path.join(TMP, 'remote.git')
        shutil.rmtree(bare, ignore_errors=True)
        subprocess.run(['git', 'init', '-q', '--bare', bare], check=True)
        tok = os.path.join(TMP, 'token')
        with open(tok, 'w') as f:
            f.write('not-a-token')
        h = {'remote': bare, 'branch': 'prepared', 'token_file': tok}
        work = os.path.join(TMP, 'ho-clone')
        HO.push(work, {'prepared/index.json': b'{}\n', 'prepared/sheets/old.jpg': b'x'}, 'first', h)
        HO.push(work, {'prepared/index.json': b'{"a": 1}\n'}, 'second', h)
        ls = subprocess.run(['git', '--git-dir', bare, 'ls-tree', '-r', '--name-only', 'prepared'],
                            capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(ls, ['prepared/index.json'])                     # the expired sheet is gone
        n = subprocess.run(['git', '--git-dir', bare, 'rev-list', '--count', 'prepared'],
                           capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(n, '1')                                          # always one commit
        heads = subprocess.run(['git', '--git-dir', bare, 'for-each-ref', '--format=%(refname)'],
                               capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(heads, ['refs/heads/prepared'])                  # nothing else touched


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
