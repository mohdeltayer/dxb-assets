"""Tests for qcrecord.py (adv-20261030-promise-keeper addendum D): the composition profiles and gate results on
synthetic layouts made with ffmpeg, and the binding of the record to the file, the text and the job.

    python3 -m unittest templates/test_qcrecord.py

The layouts are drawn small (540x960, 4 s) from a textured test source, so the suite runs in about a minute. Real
Reels were checked on the build branch: see ops/build/releases for the list and the readings.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qcrecord as Q  # noqa: E402

SRC = ("testsrc2=s=960x540:r=25:d=4[t];nullsrc=s=960x540:r=25:d=4,"
       "geq=lum='128+60*sin(X/12+T*3)*cos(Y/9)+40*random(1)':cb=128:cr=128[n];[t][n]blend=all_mode=overlay")
GROUND = 'color=c=0x141332:s=540x960:r=25:d=4'
LAYOUTS = {
    # name: filter graph after SRC (or a full graph when it holds the ground)
    'full': SRC + ',crop=304:540,scale=540:960',
    'boxblur': SRC + ',split[a][b];[a]scale=540:960,boxblur=15:2,eq=brightness=-0.3[bg];[b]scale=540:-2[fg];'
                     '[bg][fg]overlay=0:(H-h)/2',
    'rails': GROUND + '[g];' + SRC + ',scale=540:600[f];[g][f]overlay=0:260',
    'wide': GROUND + '[g];' + SRC + ',scale=540:304[f];[g][f]overlay=0:328',
    'small': GROUND + '[g];' + SRC + ',scale=270:152[f];[g][f]overlay=135:404',
    # our type on the picture: white strokes in an indigo outline inside the footage band
    'widetext': GROUND + '[g];' + SRC + ',scale=540:304[f];[g][f]overlay=0:328,'
                + ','.join('drawbox=x=%d:y=%d:w=%d:h=%d:color=0x141332:t=fill,drawbox=x=%d:y=%d:w=%d:h=%d:color=white:t=fill'
                           % (x - 3, y - 3, 14, 46, x, y, 8, 40) for y in (470, 520) for x in range(120, 420, 20)),
}


def have_ffmpeg():
    return shutil.which('ffmpeg') and shutil.which('ffprobe')


@unittest.skipUnless(have_ffmpeg(), 'ffmpeg not installed')
class Layouts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix='qc-test-')
        for name, graph in LAYOUTS.items():
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-filter_complex', graph, '-t', '4',
                            '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
                            os.path.join(cls.dir, name + '.mp4')], check=True)
        cls.recs = {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def v(self, name):
        return os.path.join(self.dir, name + '.mp4')

    def rec(self, name, **kw):
        key = (name, tuple(sorted(kw.items())))
        if key not in self.recs:
            self.recs[key] = Q.make(self.v(name), quiet=True, **kw)
        return self.recs[key]

    def test_full_frame_passes(self):
        r = self.rec('full')
        self.assertEqual(r['result'], 'PASS', r['reason'])
        self.assertTrue(all(s['area'] >= 0.95 for s in r['samples']))

    def test_box_in_blurred_fill_rejected(self):
        r = self.rec('boxblur')
        self.assertEqual(r['result'], 'REJECT', r['reason'])
        self.assertIn('blurred fill', r['reason'])

    def test_band_between_rails_passes_portrait_crop(self):
        r = self.rec('rails')                    # 540x600 of 960: 62% of the area, full width
        self.assertEqual(r['result'], 'PASS', r['reason'])

    def test_wide_band_repair_then_profile(self):
        r = self.rec('wide')                     # 32% of the area: not portrait_crop, but wide_preserve
        self.assertEqual((r['result'], r['repair']), ('REPAIR', 'profile:wide_preserve'), r['reason'])
        r2 = self.rec('wide', profile='wide_preserve', attempt=2)
        self.assertEqual(r2['result'], 'PASS', r2['reason'])

    def test_one_repair_only(self):
        r = self.rec('wide', attempt=2)          # a repaired file failing again falls back, never a second repair
        self.assertEqual(r['result'], 'FALLBACK')
        self.assertIsNone(r['repair'])

    def test_small_box_falls_back(self):
        r = self.rec('small')
        self.assertEqual(r['result'], 'FALLBACK', r['reason'])

    def test_text_on_footage_in_wide_preserve(self):
        r = self.rec('widetext', profile='wide_preserve')
        self.assertEqual((r['result'], r['repair']), ('REPAIR', 'text_to_rails'), r['reason'])
        clean = self.rec('wide', profile='wide_preserve')
        self.assertEqual(clean['result'], 'PASS', clean['reason'])

    def test_endcard_never_measured(self):
        r = self.rec('full')
        _, _, dur = Q.probe(self.v('full'))
        self.assertTrue(all(s['t'] < dur - Q.RULES['endcard_secs'] for s in r['samples']))

    def test_decode_errors_rejected(self):
        bad = os.path.join(self.dir, 'cut.mp4')
        with open(self.v('full'), 'rb') as f:
            data = f.read()
        with open(bad, 'wb') as f:
            f.write(data[:len(data) // 2])
        r = Q.make(bad, quiet=True)
        self.assertEqual(r['result'], 'REJECT')


@unittest.skipUnless(have_ffmpeg(), 'ffmpeg not installed')
class Binding(unittest.TestCase):
    JOB = {'name': 't', 'out': 'cards/test/t-reel-v1.mp4', 'headline': 'عنوان', 'label': 'رسمي', 'source': 'س',
           'date': '31 Oct 2026', 'theme': 'cold', 'note': 'prose',
           'footage': [{'file': 't.mp4', 'url': 'https://example.com/t.mp4'}],
           'shots': [['t.mp4', 1.0, 3.0, 0.5], ['t.mp4', 5.0, 3.0, 0.5]],
           'lines': [[1, 1, [['سطر', {}]]]], 'credits': [[0, 1, 'المصدر: س']]}

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix='qc-bind-')
        cls.video = os.path.join(cls.dir, 'x.mp4')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-filter_complex', LAYOUTS['full'], '-t', '4',
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', cls.video], check=True)
        cls.rec = Q.make(cls.video, job=cls.JOB, quiet=True)
        cls.post = {'caption': 'نص', 'x': 'قصير', 'threads': 'قصير'}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_record_fields(self):
        r = self.rec
        for k in ('video', 'text', 'manifest', 'template_rev', 'rules_rev', 'binding', 'result', 'profile'):
            self.assertIn(k, r)
        self.assertEqual(len(r['video']['sha256']), 64)
        self.assertEqual(r['video']['sha256'], Q.sha_file(self.video))
        self.assertIsNotNone(r['text']['screen_sha256'])
        self.assertIsNone(r['text']['post_sha256'])

    def test_valid(self):
        self.assertEqual(Q.verify(self.rec, video=self.video, job=self.JOB)[0], 'VALID')

    def test_video_edit_invalidates(self):
        other = os.path.join(self.dir, 'y.mp4')
        shutil.copy(self.video, other)
        with open(other, 'ab') as f:
            f.write(b'\0')
        state, why = Q.verify(self.rec, video=other)
        self.assertEqual(state, 'INVALID')
        self.assertIn('video changed since the check', why)

    def test_text_and_job_edits_invalidate(self):
        j = json.loads(json.dumps(self.JOB))
        j['headline'] = 'عنوان آخر'
        self.assertIn('on-screen text changed since the check', Q.verify(self.rec, video=self.video, job=j)[1])
        j = json.loads(json.dumps(self.JOB))
        j['shots'][0][1] = 2.0
        self.assertIn('job or assets changed since the check', Q.verify(self.rec, video=self.video, job=j)[1])
        j = json.loads(json.dumps(self.JOB))
        j['note'] = 'different prose'            # prose about the job is not what renders
        self.assertEqual(Q.verify(self.rec, video=self.video, job=j)[0], 'VALID')

    def test_forged_result_invalid(self):
        r = json.loads(json.dumps(self.rec))
        r['result'] = 'PASS' if r['result'] != 'PASS' else 'REJECT'
        self.assertEqual(Q.verify(r, video=self.video)[0], 'INVALID')

    def test_bind_then_gate(self):
        r = Q.bind(self.rec, self.video, self.post)
        self.assertEqual(Q.verify(r, video=self.video, post=self.post)[0], 'VALID')
        changed = dict(self.post, caption='نص آخر')
        self.assertEqual(Q.verify(r, video=self.video, post=changed)[0], 'INVALID')
        self.assertEqual(Q.verify(self.rec, video=self.video, post=self.post)[1], ['post text not bound: run bind'])
        f = Q.row_field(r, 'cards/test/x-qc.json')
        self.assertEqual(f['binding'], r['binding'])
        self.assertTrue(f['post_text_bound'])

    def test_gate_cli(self):
        rec = os.path.join(self.dir, 'x-qc.json')
        post = os.path.join(self.dir, 'post.json')
        Q._write(rec, self.rec)
        with open(post, 'w', encoding='utf-8') as f:
            json.dump(self.post, f, ensure_ascii=False)
        self.assertEqual(Q.main(['gate', rec, '--video', self.video, '--text', post]), 6)   # text not bound yet
        self.assertEqual(Q.main(['bind', rec, '--video', self.video, '--text', post]), 0)
        self.assertEqual(Q.main(['gate', rec, '--video', self.video, '--text', post]),
                         Q.EXIT[self.rec['result']])

    def test_stale_on_rules_change(self):
        r = json.loads(json.dumps(self.rec))
        r['rules_rev']['sha256'] = '0' * 64
        r['binding'] = Q.binding(r)
        self.assertEqual(Q.verify(r, video=self.video)[0], 'STALE')


class Timeline(unittest.TestCase):
    def test_matches_reel(self):
        shots = [['a.mp4', 0, 3.6, 0.5], ['a.mp4', 4, 2.4, 0.5], ['b.png', None, 3.2, 0.5]]
        starts, end, kinds = Q.timeline({'shots': shots})
        try:
            import reel
        except Exception:                       # reel needs the render stack; the arithmetic is checked anyway
            self.assertEqual([round(s, 3) for s in starts], [0.0, 3.2, 5.2])
            self.assertAlmostEqual(end, 8.4)
            return
        rs, re_ = reel.timeline([tuple(s) for s in shots])
        self.assertEqual([round(s, 6) for s in starts], [round(s, 6) for s in rs])
        self.assertAlmostEqual(end, re_)
        self.assertEqual(Q.RULES['crossfade'], reel.X)

    def test_graphic_shots_exempt(self):
        _, _, kinds = Q.timeline({'shots': [['x-gfx-a.png', 0, 3, None], ['a.mp4', 0, 3, 0.5]]})
        self.assertEqual(kinds, ['graphic', 'footage'])


if __name__ == '__main__':
    unittest.main()
