"""Official trailers and their speech, for video cards.

`steam_trailers(appid)` lists a game's Steam trailers; `fetch` saves a
stretch of one into the uploads folder the card templates read from;
`transcribe` returns the spoken lines with timings (faster-whisper, small
model, English by default) so they can be written into Arabic subtitles.
Trailer speech is what the publisher said: subtitles carry it faithfully
and never add to it.
"""
import json
import subprocess
import urllib.request

import cards as C

UA = {'User-Agent': 'Mozilla/5.0'}


def steam_trailers(appid):
    url = f'https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en'
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        d = json.load(r)
    data = next(iter(d.values())).get('data', {})
    return [{'name': m['name'].strip(), 'hls': m.get('hls_h264'),
             'thumb': m.get('thumbnail'), 'highlight': m.get('highlight')}
            for m in data.get('movies', [])]


def fetch(hls, name, start=0, seconds=30):
    """Save `seconds` of a trailer from `start` as uploads/<name>.mp4."""
    out = f'{C.U}{name}.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', hls,
           '-t', str(seconds), '-c', 'copy', out]
    subprocess.run(cmd, check=True)
    return name + '.mp4'


def transcribe(name, language='en', model='small'):
    """[(start, end, text)] for a file in uploads."""
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(C.U + name, language=language, vad_filter=True)
    return [(round(s.start, 2), round(s.end, 2), s.text.strip()) for s in segs]
