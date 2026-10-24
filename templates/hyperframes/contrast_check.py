"""HyperFrames pilot, design pass 2 (24 Oct 2026): the contrast check behind the type.

Renders snapshots of a copy of a piece with the named type layers hidden, then reads the ground behind each
text box: the brightest 5% of its pixels against the white of our type must still give a WCAG contrast of
4.5:1 or more. Usage (HF = the hyperframes CLI):
    python3 contrast_check.py <piece dir> <times,comma> <hide css selector> <name:x0,y0,x1,y1> ...
"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HF = os.environ.get('HF', 'hyperframes')
INK = (244, 243, 255)


def lum(rgb):
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def main(piece, times, hide, boxes):
    tmp = tempfile.mkdtemp(prefix='hfcc-')
    work = os.path.join(tmp, 'piece')
    shutil.copytree(piece, work, symlinks=True)
    html = os.path.join(work, 'index.html')
    s = open(html, encoding='utf8').read()
    s = s.replace('</style>', f'{hide} {{ visibility: hidden !important; }}\n    </style>', 1)
    open(html, 'w', encoding='utf8').write(s)
    out = os.path.join(tmp, 'snap')
    subprocess.run([HF, 'snapshot', work, '--at', times, '--no-end', '-o', out, '--describe', 'false'],
                   check=True, capture_output=True)
    li = lum(INK)
    worst = 99
    for f in sorted(x for x in os.listdir(out) if x.startswith('frame-')):
        im = np.array(Image.open(os.path.join(out, f)).convert('RGB'))
        row = []
        for b in boxes:
            name, xy = b.split(':')
            x0, y0, x1, y1 = map(int, xy.split(','))
            l = lum(im[y0:y1, x0:x1].reshape(-1, 3))
            p95 = float(np.percentile(l, 95))
            ratio = (li + 0.05) / (p95 + 0.05)
            worst = min(worst, ratio)
            row.append(f'{name} {ratio:.1f}:1')
        print(f.replace('.png', ''), '  '.join(row))
    shutil.rmtree(tmp)
    print('worst', f'{worst:.1f}:1', 'PASS' if worst >= 4.5 else 'FAIL (needs 4.5:1)')
    return 0 if worst >= 4.5 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]))
