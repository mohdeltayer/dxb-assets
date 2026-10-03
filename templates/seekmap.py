"""Contact sheet of a clip at the times reel.py will actually seek to.

    python3 templates/seekmap.py <file in uploads> <from> <to> [step]

Writes seekmap-<file>-<from>.jpg in the current folder, each frame labelled
with its seek time. Pick shots from this sheet, not from a sheet labelled
with presentation times: Steam trailer downloads (HLS) start their picture
2 to 3 seconds in, and stripping the sound shifts the start again, so on
3 Oct 2026 shots picked from pts-labelled sheets landed on title cards.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw

U = '/mnt/user-data/uploads/'


def seekmap(f, a, b, step=1.5, width=150, cols=12):
    ims, t = [], a
    tmp = f'/tmp/seekmap-{os.getpid()}.png'
    while t <= b:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', U + f, '-frames:v', '1',
                        '-vf', f'scale={width}:-2', tmp], check=True)
        im = Image.open(tmp).convert('RGB')
        ImageDraw.Draw(im).text((3, 3), f'{t:g}', fill=(255, 255, 0))
        ims.append(im); t += step
    os.remove(tmp)
    h = ims[0].size[1]; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (width * cols, h * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * width, (i // cols) * h))
    out = f'seekmap-{os.path.splitext(f)[0]}-{a:g}.jpg'
    sheet.save(out); return out


if __name__ == '__main__':
    a = sys.argv[1:]
    print(seekmap(a[0], float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 1.5))
