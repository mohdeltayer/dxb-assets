"""Speech checks (advisor, 21 Oct 2026, "Framing and speech" 2 and 3: no speech under story lines). With English
speech playing and Arabic lines on screen, viewers read the lines as subtitles of the speech, so the sound under the
headline and lines is music with no audible words, and the track starts and fades out in pauses.

stretch(file, start, secs)   words heard in a stretch of a source file (in uploads, or a path), before the render:
                             [(start s, end s, word)] in source time, with `head_pause` and `tail_pause` False when a
                             word sits within EDGE of the stretch's start or end (read with CTX seconds either side,
                             so a word running across the edge counts)
heard(mp4, card=None)        words heard in a finished Reel before its end card (the last outro.CARD seconds)
check(mp4, allow=(), card=None)
                             [(start, end, word, why)] for every word before the end card outside the allow windows
                             [(t0, t1, reason)] (a quote or interview Reel, where the speech is the news, subtitled),
                             and for every word cut off at the start of the audio or at the end card, allowed or not

faster-whisper, small model, CPU, int8, English, VAD on, word timings, plus a pass without VAD or a set language
for singing (SUNG); segments below LOGPROB_MIN are dropped as hallucinations (`pip install faster-whisper`; the model
downloads on first use). Without it the functions raise ImportError and callers skip with a notice. Word times can
drift by up to a second or so between runs; read them as where to listen, not to the frame.

    python3 templates/speechcheck.py <reel.mp4> [--card <secs>] [--allow t0 t1 reason]   # "speech: none" or exit 1
    python3 templates/speechcheck.py --stretch <file> <start> <secs>                      # words in a source stretch
"""
import os, subprocess, sys, tempfile

MODEL = 'small'
EDGE = 0.3       # a word this close to a stretch's start or end means the edge is not in a pause
CTX = 1.0        # seconds read either side of a source stretch, so words crossing its edges are heard whole
LOGPROB_MIN = -0.8   # segments decoded less surely are whisper hearing words in music ("Thank you for watching!",
                     # "Music", "BYE!" read -1.1 to -1.5 on clean Reels); speech and singing read -0.2 to -0.55
SUNG = True      # a second pass with no VAD and no set language: the VAD drops singing (the Cry Me opening's
                 # Japanese lyrics went unheard) and the English pass misses other languages
_whisper = None


def _model():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel(MODEL, device='cpu', compute_type='int8')
    return _whisper


def _path(f):
    if os.path.exists(f):
        return f
    import cards as C
    return C.U + f


def _dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout.strip() or 0)


def _pass(wav, off, **kw):
    segs, _ = _model().transcribe(wav, word_timestamps=True, **kw)
    return [(round(off + w.start, 2), round(off + w.end, 2), w.word.strip()) for s in segs if s.avg_logprob >= LOGPROB_MIN
            for w in (s.words or []) if any(ch.isalpha() for ch in w.word) and not w.word.strip().startswith(('[', '(', '♪'))]


def words(path, start=0.0, secs=None):
    """[(start s, end s, word)] heard in `path` from `start` for `secs` (all of it when None), in the file's own
    time: English speech (VAD on), then, with SUNG, singing and other languages the VAD drops."""
    tmp = tempfile.mktemp(suffix='.wav')
    try:
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{start:.3f}', '-i', path]
                       + (['-t', f'{secs:.3f}'] if secs else []) + ['-vn', '-ac', '1', '-ar', '16000', tmp], check=True)
        got = _pass(tmp, start, language='en', vad_filter=True)
        if SUNG:
            more = _pass(tmp, start, vad_filter=False, condition_on_previous_text=False)
            got += [w for w in more if not any(a < w[1] and w[0] < b for a, b, _ in got)]
        return sorted(got)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


class Heard(list):
    """stretch()'s words, plus `head_pause` and `tail_pause`: whether the stretch starts and ends in a pause."""
    head_pause = tail_pause = True


def stretch(f, start, secs):
    """Words inside a source stretch (a track candidate), read with CTX seconds of context either side."""
    lo = max(0.0, start - CTX)
    got = words(_path(f), lo, secs + (start - lo) + CTX)
    out = Heard(w for w in got if w[1] > start and w[0] < start + secs)
    near = lambda t: [w for w in got if w[0] - EDGE < t < w[1] + EDGE]
    out.head_pause, out.tail_pause = not near(start), not near(start + secs)
    return out


def heard(mp4, card=None):
    """Words heard in a finished Reel before its end card; `card` is the card's start (default: the last
    outro.CARD seconds; pass the clip length for a draft, which has no card)."""
    if card is None:
        from outro import CARD
        card = _dur(mp4) - CARD
    return [w for w in words(mp4, 0.0, None) if w[0] < card], card


def check(mp4, allow=(), card=None):
    """[(start, end, word, why)]: every word before the end card outside the allow windows, and every word
    cut off at the start of the audio or running into the end card (those stop the post even inside a window)."""
    got, card = heard(mp4, card)
    bad = []
    for a, b, w in got:
        if a < EDGE:
            bad.append((a, b, w, 'cut off at the start'))
        elif b > card - EDGE:
            bad.append((a, b, w, 'cut off at the end card'))
        elif not any(t0 <= a and b <= t1 for t0, t1, *_ in allow):
            bad.append((a, b, w, 'speech under the lines'))
    return bad


def _say(ws):
    return ', '.join(f'{a:.2f}-{b:.2f} "{w}"' for a, b, w, *_ in ws)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--stretch':
        f, s, d = args[1], float(args[2]), float(args[3])
        ws = stretch(f, s, d)
        print('speech:', 'none' if not ws else f'{len(ws)} words: ' + _say(ws))
        print('start in a pause:', 'yes' if ws.head_pause else 'no', '| end in a pause:', 'yes' if ws.tail_pause else 'no')
        sys.exit(0 if not ws and ws.head_pause and ws.tail_pause else 1)
    p = args[0]
    card = float(args[args.index('--card') + 1]) if '--card' in args else None
    allow = []
    for i, a in enumerate(args):
        if a == '--allow':
            allow.append((float(args[i + 1]), float(args[i + 2]), args[i + 3]))
    bad = check(p, allow, card)
    if not bad:
        print('speech: none' if not allow else 'speech: only inside the allowed windows')
        sys.exit(0)
    for a, b, w, why in bad:
        print(f'{a:6.2f} to {b:6.2f} s  {w!r}  ({why})')
    sys.exit(1)
