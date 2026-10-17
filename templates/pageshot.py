"""A store or source page as a shot (advisor review, 14 Oct 2026, rule 3): a line
about a store page gets the page itself, cropped to the row the line is about.

    python3 pageshot.py <url> <out.png> [--clip x,y,w,h] [--width 1440] [--wait 2500] [--scale 2]

Headless Chromium (Playwright, pre-installed), a browser user agent, full-page
screenshot, then the crop. Pass the PNG as a still shot; it takes the standard
finish like official art. No social-media pages.
"""
import sys, time


def shot(url, out, clip=None, width=1440, wait=2500, height=2200, scale=1):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:   # the pinned headless shell is missing; use the pre-installed Chromium
            b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = b.new_page(viewport={'width': width, 'height': height}, device_scale_factor=scale,
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36')
        pg.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(wait / 1000)
        if clip:
            x, y, w, h = clip
            pg.screenshot(path=out, clip={'x': x, 'y': y, 'width': w, 'height': h})
        else:
            pg.screenshot(path=out, full_page=True)
        b.close()
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    clip = None; width = 1440; wait = 2500; scale = 1
    if '--clip' in a:
        clip = tuple(int(v) for v in a[a.index('--clip') + 1].split(','))
    if '--width' in a:
        width = int(a[a.index('--width') + 1])
    if '--wait' in a:
        wait = int(a[a.index('--wait') + 1])
    if '--scale' in a:   # device pixels per CSS pixel, for a crop that must fill 9:16 without passing 2x
        scale = float(a[a.index('--scale') + 1])
    print(shot(a[0], a[1], clip, width, wait, scale=scale))
