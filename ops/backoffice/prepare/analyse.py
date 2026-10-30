"""Source checks and shot map for a prepared asset. Each step is timed and may fail on its own: a missing tool or
model is written into the manifest as `skipped: <why>`, never a crash, except the decode check, whose result decides
whether the asset is usable at all.

Steps, in the order prepare.py runs them:
  probe      size, frame rate, bit rate, duration, audio stream (templates/decodecheck.probe)
  decode     every frame decoded once (decodecheck.decode_errors)
  bitrate    the 24 Oct floor (decodecheck.bitrate_flag)
  smear      blocky decode smear (decodecheck.smear_times), read in short windows so memory stays small
  scenes     shot boundaries: PySceneDetect AdaptiveDetector (BSD-3), ffmpeg's scene score as the fallback
  frames     four frames per scene (just after the cut, 25%, 50%, 75%) read once, in order
  faces      YuNet (OpenCV Zoo, MIT) on each frame; a yaw proxy from its five landmarks flags side-on faces
  subjects   NanoDet-Plus m 416 (OpenCV Zoo, Apache-2.0) on each frame: people, vehicles, animals
  text       tesseract on the cut frame and the middle frame: burnt-in text, slates, title cards
  blocks     the 8x8 block-edge ratio (decodecheck.block_ratio) for scenes the 9:16 crop enlarges past 2x
  focus      a suggested 9:16 focus per scene (0 left to 1 right, reel._window's meaning), with two keyframes
  sheet      one contact sheet, a tile per scene with the suggested window drawn, for the shot-choice comparison
  beats      tempo and beat times of the asset's sound (librosa, ISC), cached
  split      optional: Cocktail Fork stems via templates/tracksplit.py when COCKTAIL_DIR is set and PREPARE_SPLIT=on
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'templates'))
import decodecheck as DC  # noqa: E402  (numpy only; shared with the render path)

MIN_SHOT = 0.5                 # seconds: shorter cuts merge into the shot before (PySceneDetect min_scene_len)
MAX_SCENES = int(os.environ.get('PREPARE_MAX_SCENES') or 150)
SMEAR_FRAMES = 360             # frames per smear window (about 190 MB of float32 at 480x270)
FACE_SCORE, SUBJ_SCORE = 0.7, 0.4
PROFILE_RATIO = 0.45           # |nose offset| / eye distance above this reads as side-on (approximation)
TEXT_CONF, TEXT_LETTERS = 70, 3    # reel._words' bar for the first frame; texture reads as 3-letter junk under 70
DARK = 24                      # luma: rows under this are letterbox bars; a frame whose mean is under 18 is black
ZOOM_MAX = 2.0                 # reel.MAX_ZOOM: block ratio is read only past this
OUT_W, OUT_H = 1080, 1920
COCO = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
        'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
        'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
        'hair drier', 'toothbrush')
SUBJECTS = {'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'}

# Models: official OpenCV Zoo files, fetched by install.sh (or `prepare.py models`) into the model cache, never git.
MODELS = {
    'yunet': {'file': 'face_detection_yunet_2023mar.onnx', 'licence': 'MIT (OpenCV Zoo face_detection_yunet)',
              'sha256': '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4',
              'urls': ['https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx',
                       'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/'
                       'face_detection_yunet_2023mar.onnx']},
    'nanodet': {'file': 'object_detection_nanodet_2022nov.onnx',
                'licence': 'Apache-2.0 (OpenCV Zoo object_detection_nanodet)',
                'sha256': '4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186',
                'urls': ['https://huggingface.co/opencv/object_detection_nanodet/resolve/main/'
                         'object_detection_nanodet_2022nov.onnx',
                         'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/object_detection_nanodet/'
                         'object_detection_nanodet_2022nov.onnx']},
}


def model_dir():
    d = os.environ.get('PREPARE_MODELS')
    if d:
        return d
    cache = os.environ.get('DXB_CACHE') or '/var/cache/dxb-render'
    if os.path.isdir(cache) and os.access(cache, os.W_OK):
        return os.path.join(cache, 'models', 'opencv-zoo')
    return os.path.join(os.environ.get('PREPARE_HOME') or os.path.expanduser('~/backoffice/prepare'), 'models')


def model_path(name):
    p = os.path.join(model_dir(), MODELS[name]['file'])
    return p if os.path.exists(p) else None


def fetch_models(log=print):
    """Download the two models from their official mirrors, sha256-checked. Returns {name: path or error}."""
    d = model_dir()
    os.makedirs(d, exist_ok=True)
    out = {}
    for name, m in MODELS.items():
        dst = os.path.join(d, m['file'])
        if os.path.exists(dst) and _sha256(dst) == m['sha256']:
            out[name] = dst
            continue
        err = 'no url answered'
        for u in m['urls']:
            p = subprocess.run(['curl', '-sSfL', '--max-time', '180', '-o', dst + '.part', u], capture_output=True,
                               text=True)
            if p.returncode == 0 and _sha256(dst + '.part') == m['sha256']:
                os.replace(dst + '.part', dst)
                out[name] = dst
                log(f'model {name}: {m["file"]} ({m["licence"]})')
                break
            err = f'{u.split("/")[2]}: ' + ('sha256 mismatch' if p.returncode == 0 else p.stderr.strip()[:120])
        else:
            if os.path.exists(dst + '.part'):
                os.remove(dst + '.part')
            out[name] = 'error: ' + err
    return out


def _sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ probe, decode, bitrate, smear

def probe(path):
    w, h, fps, bps = DC.probe(path)
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json',
                        path], capture_output=True, text=True)
    j = json.loads(r.stdout or '{}')
    kinds = [s.get('codec_type') for s in j.get('streams') or []]
    dur = float((j.get('format') or {}).get('duration') or 0)
    return {'w': w, 'h': h, 'fps': round(fps, 3), 'bps': int(bps), 'duration': round(dur, 3),
            'audio': 'audio' in kinds, 'video': 'video' in kinds}


def decode(path):
    errs = DC.decode_errors(path)
    return {'clean': not errs, 'errors': len(errs), 'first': errs[0][:200] if errs else None}


def smear(path, duration, fps):
    """decodecheck.smear_times over windows of SMEAR_FRAMES with LOCAL overlap, merged."""
    win = max(4.0, SMEAR_FRAMES / max(1.0, fps))
    pad = DC.LOCAL + 0.5
    found, t = [], 0.0
    while t < duration:
        s0 = max(0.0, t - pad)
        for a, b, p in DC.smear_times(path, s0 or None, win + (t - s0) + pad):
            if t <= a < t + win and not any(abs(a - x[0]) < 0.05 for x in found):
                found.append((a, b, p))
        t += win
    return [list(x) for x in sorted(found)]


# ------------------------------------------------------------------ scenes

def scenes(path, fps, duration):
    """[(start, end)] in seconds; PySceneDetect when installed, ffmpeg's scene score otherwise."""
    try:
        from scenedetect import AdaptiveDetector, detect
        min_len = max(2, round(MIN_SHOT * (fps or 30)))
        found = detect(path, AdaptiveDetector(min_scene_len=min_len), show_progress=False)
        out = [(round(a.get_seconds(), 3), round(b.get_seconds(), 3)) for a, b in found]
        tool = 'pyscenedetect'
    except ImportError:
        out, tool = _ffmpeg_scenes(path, duration), 'ffmpeg-scene'
    if not out:
        out = [(0.0, round(duration, 3))]
    return out[:MAX_SCENES], tool


def _ffmpeg_scenes(path, duration):
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', path, '-an', '-vf',
                        "scale=320:-2,select='gt(scene,0.35)',showinfo", '-f', 'null', '-'],
                       capture_output=True, text=True)
    cuts = [float(m.group(1)) for m in re.finditer(r'pts_time:([0-9.]+)', p.stderr)]
    cuts = [c for c in cuts if c > MIN_SHOT]
    merged = []
    for c in cuts:
        if not merged or c - merged[-1] >= MIN_SHOT:
            merged.append(c)
    edges = [0.0] + merged + [duration]
    return [(round(a, 3), round(b, 3)) for a, b in zip(edges, edges[1:]) if b - a > 0.05]


# ------------------------------------------------------------------ frames

def sample_times(sc):
    out = []
    for a, b in sc:
        d = b - a
        out.append([round(a + min(0.1, d / 4), 3), round(a + d * 0.25, 3), round(a + d * 0.5, 3),
                    round(a + d * 0.75, 3)])
    return out


def iter_frames(path, want, max_w=1280):
    """(t, BGR frame no wider than max_w) for each time in the sorted list `want`, in order, read in one pass with
    OpenCV; ffmpeg seeks for any time the pass did not reach. Frames are never all held at once."""
    want = sorted(set(want))
    i = 0
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            while i < len(want):
                if not cap.grab():
                    break
                t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if t + 1e-3 < want[i]:
                    continue
                ok, fr = cap.retrieve()
                if ok and fr.shape[1] > max_w:
                    fr = cv2.resize(fr, (max_w, round(fr.shape[0] * max_w / fr.shape[1])), interpolation=cv2.INTER_AREA)
                while i < len(want) and t + 1e-3 >= want[i]:
                    if ok:
                        yield want[i], fr
                    i += 1
            cap.release()
    except ImportError:
        pass
    for t in want[i:]:
        fr = _ffmpeg_frame(path, t, max_w)
        if fr is not None:
            yield t, fr


def _ffmpeg_frame(path, t, max_w=1280):
    w, h = DC.probe(path)[:2]
    if w > max_w:
        w, h = max_w, round(h * max_w / w / 2) * 2
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1', '-vf',
                        f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    if len(p.stdout) != w * h * 3:
        return None
    return np.frombuffer(p.stdout, np.uint8).reshape(h, w, 3)


def picture_box(frames):
    """(x, y, w, h) of the picture inside letterbox bars, from the scene's frames (rows and columns that ever pass DARK)."""
    if not frames:
        return None
    g = np.max(np.stack([f.max(axis=2) for f in frames]), axis=0)
    rows = np.where(g.max(axis=1) > DARK)[0]
    cols = np.where(g.max(axis=0) > DARK)[0]
    H, W = g.shape
    if not len(rows) or not len(cols):
        return [0, 0, W, H]
    y0, y1, x0, x1 = int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1
    if y0 < 8 and H - y1 < 8:
        y0, y1 = 0, H
    if x0 < 8 and W - x1 < 8:
        x0, x1 = 0, W
    # Bars are symmetric (a letterbox top and bottom, a pillarbox left and right); a dark corner or a dark half of
    # a scene is picture, not bars, so anything lopsided or very small is taken as the whole frame.
    if abs(y0 - (H - y1)) > 0.06 * H:
        y0, y1 = 0, H
    if abs(x0 - (W - x1)) > 0.06 * W:
        x0, x1 = 0, W
    if (y1 - y0) < H * 0.3 or (x1 - x0) < W * 0.3:
        return [0, 0, W, H]
    return [x0, y0, x1 - x0, y1 - y0]


# ------------------------------------------------------------------ detectors

class Detectors:
    def __init__(self):
        self.notes = {}
        self.face = self.det = None
        try:
            import cv2
            self.cv2 = cv2
        except ImportError:
            self.cv2 = None
            self.notes['opencv'] = 'skipped: opencv not installed'
            return
        yp, npth = model_path('yunet'), model_path('nanodet')
        if yp:
            try:
                self.face = cv2.FaceDetectorYN.create(yp, '', (640, 360), FACE_SCORE, 0.3, 50)
            except Exception as e:  # noqa: BLE001
                self.notes['faces'] = f'skipped: YuNet did not load ({type(e).__name__})'
        else:
            self.notes['faces'] = f'skipped: no YuNet model in {model_dir()} (prepare.py models)'
        if npth:
            try:
                self.det = cv2.dnn.readNet(npth)
            except Exception as e:  # noqa: BLE001
                self.notes['subjects'] = f'skipped: NanoDet did not load ({type(e).__name__})'
        else:
            self.notes['subjects'] = f'skipped: no NanoDet model in {model_dir()} (prepare.py models)'

    def faces(self, fr):
        if self.face is None:
            return None
        H, W = fr.shape[:2]
        k = 640 / W
        small = self.cv2.resize(fr, (640, max(2, round(H * k))))
        self.face.setInputSize((small.shape[1], small.shape[0]))
        _, f = self.face.detect(small)
        out = []
        for r in (f if f is not None else []):
            x, y, w, h = (float(v) / k for v in r[:4])
            rex, lex, nx = r[4] / k, r[6] / k, r[8] / k
            eye = abs(lex - rex)
            yaw = (nx - (rex + lex) / 2) / max(1.0, eye)
            prof = bool(abs(yaw) > PROFILE_RATIO or eye < 0.25 * w)
            out.append({'box': [round(x), round(y), round(w), round(h)], 'score': round(float(r[14]), 2),
                        'yaw_proxy': round(float(yaw), 2), 'profile': prof})
        return out

    def subjects(self, fr):
        if self.det is None:
            return None
        cv2 = self.cv2
        H, W = fr.shape[:2]
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        s = 416 / max(H, W)
        nh, nw = max(1, round(H * s)), max(1, round(W * s))
        img = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        top, left = (416 - nh) // 2, (416 - nw) // 2
        img = cv2.copyMakeBorder(img, top, 416 - nh - top, left, 416 - nw - left, cv2.BORDER_CONSTANT, value=0)
        x = (img.astype(np.float32) - np.array([103.53, 116.28, 123.675], np.float32)) / \
            np.array([57.375, 57.12, 58.395], np.float32)
        self.det.setInput(cv2.dnn.blobFromImage(x))
        outs = self.det.forward(self.det.getUnconnectedOutLayersNames())
        return [dict(d, box=[round((d['box'][0] - left) / s), round((d['box'][1] - top) / s),
                             round(d['box'][2] / s), round(d['box'][3] / s)])
                for d in nanodet_decode(outs)]


def nanodet_decode(outs, thresh=SUBJ_SCORE, iou=0.6, size=416, reg_max=7):
    """NanoDet-Plus outputs to [{'label', 'score', 'box': [x, y, w, h]}] in the 416 input. The outputs are paired by
    shape, not by order (OpenCV 4 and 5 list them differently): class maps are (n, 80), box maps (n, 32)."""
    import cv2
    cls = {o.reshape(-1, o.shape[-1]).shape[0]: o.reshape(-1, o.shape[-1]) for o in outs if o.shape[-1] == 80}
    reg = {o.reshape(-1, o.shape[-1]).shape[0]: o.reshape(-1, o.shape[-1]) for o in outs
           if o.shape[-1] == 4 * (reg_max + 1)}
    proj = np.arange(reg_max + 1, dtype=np.float32)
    boxes, scores, labels = [], [], []
    for n, c in cls.items():
        if n not in reg:
            continue
        side = int(round(n ** 0.5))
        stride = size / side
        ys, xs = np.mgrid[0:side, 0:side]
        cx = (xs.ravel() * stride + 0.5 * (stride - 1))
        cy = (ys.ravel() * stride + 0.5 * (stride - 1))
        r = reg[n].reshape(-1, reg_max + 1)
        e = np.exp(r - r.max(axis=1, keepdims=True))
        dist = ((e / e.sum(axis=1, keepdims=True)) @ proj).reshape(-1, 4) * stride
        x1, y1 = np.clip(cx - dist[:, 0], 0, size), np.clip(cy - dist[:, 1], 0, size)
        x2, y2 = np.clip(cx + dist[:, 2], 0, size), np.clip(cy + dist[:, 3], 0, size)
        lab, sc = c.argmax(axis=1), c.max(axis=1)
        keep = sc >= thresh
        boxes += np.column_stack([x1, y1, x2 - x1, y2 - y1])[keep].tolist()
        scores += sc[keep].tolist()
        labels += lab[keep].tolist()
    if not boxes:
        return []
    idx = cv2.dnn.NMSBoxes(boxes, scores, thresh, iou)
    idx = np.array(idx).reshape(-1)
    out = [{'label': COCO[labels[i]] if labels[i] < len(COCO) else str(labels[i]), 'score': round(float(scores[i]), 2),
            'box': [float(v) for v in boxes[i]]} for i in idx]
    return sorted(out, key=lambda d: -d['score'])[:8]


def tesseract_words(fr):
    """[(word, [x, y, w, h])] tesseract reads in a frame (at least TEXT_LETTERS letters, conf >= TEXT_CONF); None
    without the tesseract binary. Read at 1280 wide, boxes in source pixels."""
    if not shutil.which('tesseract'):
        return None
    import cv2
    H, W = fr.shape[:2]
    k = 1280 / W if W > 1280 else 1.0
    img = cv2.resize(fr, (round(W * k), round(H * k))) if k != 1.0 else fr
    with tempfile.TemporaryDirectory(prefix='prep-ocr-') as td:
        p = os.path.join(td, 'f.png')
        cv2.imwrite(p, img)
        # OMP_THREAD_LIMIT=1: tesseract's OpenMP threads spin against each other; on the 4-core container one
        # frame took 13 s with the default and 0.3 s with one thread (29 Oct 2026)
        r = subprocess.run(['tesseract', p, 'stdout', '--psm', '11', 'tsv'], capture_output=True, text=True,
                           timeout=60, env=dict(os.environ, OMP_THREAD_LIMIT='1'))
    out = []
    for line in r.stdout.splitlines()[1:]:
        c = line.split('\t')
        if len(c) == 12 and c[11].strip():
            try:
                conf = float(c[10])
            except ValueError:
                continue
            word = ''.join(ch for ch in c[11] if ch.isalpha())
            if conf >= TEXT_CONF and len(word) >= TEXT_LETTERS:
                l, t, w, h = (int(int(v) / k) for v in c[6:10])
                out.append((c[11].strip(), [l, t, w, h]))
    return out


# ------------------------------------------------------------------ focus

def focus_for(box, pic):
    """reel._window's focus (0 left to 1 right) that centres a 9:16 window on box (x, y, w, h) inside picture pic."""
    px, py, pw, ph = pic
    ww = ph * OUT_W / OUT_H
    if pw <= ww:
        return 0.5
    cx = box[0] + box[2] / 2
    return round(min(1.0, max(0.0, (cx - px - ww / 2) / (pw - ww))), 3)


def window_x(focus, pic):
    px, py, pw, ph = pic
    ww = ph * OUT_W / OUT_H
    x0 = px + (pw - ww) * min(1, max(0, focus))
    return x0, x0 + ww


def pick_subject(fd):
    """The box the window should hold: the largest face, else the largest person, vehicle or animal."""
    faces = fd.get('faces') or []
    if faces:
        b = max(faces, key=lambda f: f['box'][2] * f['box'][3])
        return b['box'], 'face'
    subs = [s for s in fd.get('subjects') or [] if s['label'] in SUBJECTS]
    if subs:
        b = max(subs, key=lambda s: s['box'][2] * s['box'][3])
        return b['box'], 'subject:' + b['label']
    return None, None


# ------------------------------------------------------------------ the shot map

def _scale_box(b, k):
    return [round(v * k) for v in b]


def shot_map(path, info, log=print, busy=None):
    """Scenes with frames, faces, subjects, text, blocks and focus, in source pixels. Frames are read once, in order,
    at most 1280 wide, and each scene is analysed as soon as its four frames are in, so memory stays at one scene.
    `busy()` is called between scenes (render pause) and may raise to stop. Returns (scenes, tool notes, timings,
    thumbnails for the contact sheet)."""
    import cv2
    tm = {}
    t0 = time.time()
    sc, tool = scenes(path, info['fps'], info['duration'])
    tm['scenes'] = round(time.time() - t0, 2)
    notes = {'scenes': tool}
    times = sample_times(sc)
    need = {}
    for i, ts in enumerate(times):
        for j, t in enumerate(ts):
            need.setdefault(t, []).append((i, j))
    det = Detectors()
    notes.update(det.notes)
    acc = {'frames': 0.0, 'faces': 0.0, 'subjects': 0.0, 'text': 0.0, 'blocks': 0.0}
    state = {'ocr_missing': False}
    out, thumbs = [], {}

    def timed(label, fn, *a):
        x = time.time()
        try:
            return fn(*a)
        finally:
            acc[label] += time.time() - x

    def process(i, frs):
        if busy:
            busy()
        a, b = sc[i]
        ts = times[i]
        got = [f for f in frs if f is not None]
        k = info['w'] / got[0].shape[1] if got else 1.0
        pb = picture_box(got)
        pic = _scale_box(pb, k) if pb else [0, 0, info['w'], info['h']]
        if pb and pb[0] + pb[2] >= got[0].shape[1] - 1:      # rounding: a full-width picture stays full width
            pic[2] = info['w'] - pic[0]
        if pb and pb[1] + pb[3] >= got[0].shape[0] - 1:
            pic[3] = info['h'] - pic[1]
        zoom = round(OUT_H / max(1, pic[3]), 2)
        fl = []
        for j, (t, fr) in enumerate(zip(ts, frs)):
            if fr is None:
                fl.append({'t': t, 'missing': True})
                continue
            fd = {'t': t, 'black': bool(fr.mean() < 18)}
            if not fd['black']:
                f_ = timed('faces', det.faces, fr)
                fd['faces'] = None if f_ is None else [dict(x, box=_scale_box(x['box'], k)) for x in f_]
                s_ = timed('subjects', det.subjects, fr)
                fd['subjects'] = None if s_ is None else [dict(x, box=_scale_box(x['box'], k)) for x in s_]
                if j in (0, 2):
                    w = timed('text', tesseract_words, fr)
                    if w is None:
                        state['ocr_missing'] = True
                    else:
                        fd['text'] = [{'word': a_, 'box': _scale_box(b_, k)} for a_, b_ in w[:20]]
            fl.append(fd)
        if frs[2] is not None:
            th = frs[2]
            thumbs[i] = cv2.resize(th, (320, max(2, round(th.shape[0] * 320 / th.shape[1]))),
                                   interpolation=cv2.INTER_AREA)
        # focus: subject at 25% and 75% (two keyframes, as reel.autofocus), the scene's focus their mean
        keys = []
        for j, frac in ((1, 0.25), (3, 0.75)):
            fd = fl[j]
            box, why = pick_subject(fd) if not fd.get('missing') else (None, None)
            if box:
                keys.append([frac, focus_for(box, pic), why])
        focus = round(sum(x[1] for x in keys) / len(keys), 3) if keys else None
        x0, x1 = window_x(focus if focus is not None else 0.5, pic)
        words = [w for fd in fl for w in fd.get('text') or []]
        if len(words) < 2 and not any(sum(ch.isalpha() for ch in w['word']) >= 5 for w in words):
            words = []                      # one short word is texture tesseract misread, not burnt-in text
        cut = [w['word'] for w in words if w['box'][0] < x0 < w['box'][0] + w['box'][2]
               or w['box'][0] < x1 < w['box'][0] + w['box'][2]]
        first_text = [w['word'] for w in fl[0].get('text') or []]
        entry = {'i': i, 'start': a, 'end': b, 'secs': round(b - a, 3), 'picture': pic, 'zoom': zoom,
                 'focus': focus, 'focus_keys': [[x[0], x[1]] for x in keys], 'focus_from': keys[0][2] if keys else None,
                 'faces': max((len(fd.get('faces') or []) for fd in fl), default=0),
                 'profile': any(f['profile'] for fd in fl for f in fd.get('faces') or []),
                 'subjects': sorted({s['label'] for fd in fl for s in fd.get('subjects') or []}),
                 'text': bool(words), 'text_words': sorted({w['word'] for w in words})[:12],
                 'text_on_cut_frame': first_text[:8], 'cut_text': sorted(set(cut))[:8],
                 'black': sum(1 for fd in fl if fd.get('black')), 'frames': fl}
        if zoom > ZOOM_MAX and entry['black'] < len(fl):
            mid, dur = (a + b) / 2, min(2.0, b - a)
            crop = (pic[2], pic[3], pic[0], pic[1]) if pic[3] < info['h'] or pic[2] < info['w'] else None
            med, peak, n = timed('blocks', DC.block_ratio, path, max(a, mid - dur / 2), dur, crop)
            entry['block'] = {'median': med, 'peak': peak, 'frames': n, 'blocky': peak > DC.BLOCK_MAX}
        else:
            entry['block'] = f'not read (enlarged {zoom}x, at most {ZOOM_MAX}x)'
        out.append(entry)

    last = [max(ts) for ts in times]
    buf = {}
    nxt = 0
    gen = iter_frames(path, list(need))
    while True:
        x = time.time()
        try:
            t, fr = next(gen)
        except StopIteration:
            acc['frames'] += time.time() - x
            break
        acc['frames'] += time.time() - x
        for i, j in need[t]:
            buf.setdefault(i, [None] * 4)[j] = fr
        while nxt < len(sc) and t + 1e-6 >= last[nxt]:
            process(nxt, buf.pop(nxt, [None] * 4))
            nxt += 1
    while nxt < len(sc):
        process(nxt, buf.pop(nxt, [None] * 4))
        nxt += 1
    if state['ocr_missing']:
        notes['text'] = 'skipped: tesseract not installed (apt-get install -y tesseract-ocr)'
    tm.update({k_: round(v, 2) for k_, v in acc.items()})
    return out, notes, tm, thumbs


def contact_sheet(path_out, scenes_, thumbs, src_w, cols=6):
    """One tile per scene (its middle frame), the suggested 9:16 window outlined, scene number and time on it."""
    try:
        import cv2
    except ImportError:
        return None
    tiles = []
    for s in scenes_:
        im = thumbs.get(s['i'])
        if im is None:
            continue
        im = im.copy()
        k = im.shape[1] / src_w
        x0, x1 = window_x(s['focus'] if s['focus'] is not None else 0.5, s['picture'])
        y0, y1 = s['picture'][1], s['picture'][1] + s['picture'][3]
        col = (80, 220, 80) if s['focus'] is not None else (160, 160, 160)
        cv2.rectangle(im, (round(x0 * k), round(y0 * k)), (round(x1 * k) - 1, round(y1 * k) - 1), col, 2)
        tag = f"{s['i']} {s['start']:.1f}s" + (' T' if s['text'] else '') + (' P' if s['profile'] else '')
        cv2.rectangle(im, (0, 0), (len(tag) * 9 + 6, 18), (0, 0, 0), -1)
        cv2.putText(im, tag, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    if not tiles:
        return None
    th = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, th - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=0) for t in tiles]
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(path_out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return path_out


# ------------------------------------------------------------------ beats (librosa) and split (Cocktail Fork)

def beats(path, cache_dir, max_secs=600):
    """{'tempo', 'beats': [s], 'n', 'secs', 'cached'} for an audio or video file, cached by content hash. None when
    librosa is missing or the file has no sound."""
    try:
        import librosa
    except ImportError:
        return None
    key = _sha256(path)[:20] + '-' + librosa.__version__
    os.makedirs(cache_dir, exist_ok=True)
    cp = os.path.join(cache_dir, key + '.json')
    if os.path.exists(cp):
        with open(cp) as f:
            d = json.load(f)
        d['cached'] = True
        return d
    y, sr = _load_audio(path, 22050, max_secs)
    if y is None or not len(y):
        return None
    tempo, bt = librosa.beat.beat_track(y=y, sr=sr, units='time')
    tempo = float(np.atleast_1d(tempo)[0])
    d = {'file': os.path.basename(path), 'tempo': round(tempo, 2), 'beats': [round(float(b), 3) for b in bt],
         'n': int(len(bt)), 'secs': round(len(y) / sr, 2), 'librosa': librosa.__version__}
    with open(cp + '.tmp', 'w') as f:
        json.dump(d, f)
    os.replace(cp + '.tmp', cp)
    d['cached'] = False
    return d


def _load_audio(path, sr, max_secs):
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-t', str(max_secs), '-vn', '-ac', '1', '-ar',
                        str(sr), '-f', 'f32le', '-'], capture_output=True)
    if p.returncode or not p.stdout:
        return None, sr
    return np.frombuffer(p.stdout, np.float32).copy(), sr


def split_audio(src, outdir, timeout=300, max_secs=180):
    """Cocktail Fork stems (music, speech, sfx as FLAC) and their energy shares, in a child process under a timeout.
    Only when COCKTAIL_DIR is set and PREPARE_SPLIT=on; otherwise a 'skipped' string."""
    if os.environ.get('PREPARE_SPLIT') != 'on':
        return 'skipped: PREPARE_SPLIT is not on'
    if not os.environ.get('COCKTAIL_DIR'):
        return 'skipped: COCKTAIL_DIR unset (Cocktail Fork not installed for this user)'
    if not os.path.exists(os.path.join(REPO, 'templates', 'tracksplit.py')):
        return 'skipped: templates/tracksplit.py missing from the clone'
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), '_split', src, outdir, str(max_secs)],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f'failed: over {timeout} s'
    if p.returncode:
        return 'failed: ' + (p.stderr.strip().splitlines() or ['?'])[-1][:200]
    d = json.loads(p.stdout.strip().splitlines()[-1])
    d['secs_taken'] = round(time.time() - t0, 1)
    return d


def _split_child(src, outdir, max_secs):
    import tracksplit as TS
    a = TS._audio(src, 0.0, min(float(max_secs), TS._dur(src)))
    stems = TS._Cocktail()(a)
    tot = sum(TS._energy(v) for v in stems.values()) or 1e-12
    out = {'secs': round(a.shape[1] / TS.SR, 2), 'commit': os.path.basename(os.environ['COCKTAIL_DIR'].rstrip('/'))}
    for k, v in stems.items():
        dst = os.path.join(outdir, f'stem-{k}.flac')
        raw = np.ascontiguousarray(v.T.astype(np.float32)).tobytes()
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(TS.SR), '-ac',
                        str(v.shape[0]), '-i', '-', '-c:a', 'flac', '-sample_fmt', 's16', dst], input=raw, check=True)
        out[k] = {'file': os.path.basename(dst), 'share': round(100 * TS._energy(v) / tot, 1)}
    print(json.dumps(out))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '_split':
    _split_child(sys.argv[2], sys.argv[3], sys.argv[4])
