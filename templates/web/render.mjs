// Render a web piece frame by frame: window.renderAt(t) in headless Chromium, a PNG screenshot per frame, then ffmpeg.
//   node render.mjs <page.html> <out.mp4> <seconds> [query] [fps=30]
// Serves this folder, /fonts/ from /root/fonts-private/dubai (never in git) and /mark.jpg from the templates folder.
// Same route as room3d/render.mjs (CLAUDE.md "Web-style motion graphics", pilot 19 Oct 2026).
import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFile, mkdir, rm } from 'fs/promises';
import { execFileSync } from 'child_process';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [pageName, out, seconds, query = '', fps = '30'] = process.argv.slice(2);
const FPS = +fps, N = Math.round(FPS * +seconds);
const FONTS = process.env.DUBAI_FONTS || '/root/fonts-private/dubai';
const TYPES = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.ttf': 'font/ttf', '.jpg': 'image/jpeg', '.png': 'image/png', '.html': 'text/html', '.svg': 'image/svg+xml', '.json': 'application/json' };
const srv = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  let f = u.startsWith('/fonts/') ? path.join(FONTS, path.basename(u)) : u === '/mark.jpg' ? path.join(here, '..', 'digi-mark.jpg') : path.join(here, u.replace(/^\//, ''));
  try { const body = await readFile(f); res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); res.end(body); }
  catch (e) { res.writeHead(404); res.end(); }
}).listen(0);
const port = srv.address().port;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(`http://127.0.0.1:${port}/${pageName}?${query}`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
const tmp = path.join(os.tmpdir(), 'web-' + process.pid); await mkdir(tmp, { recursive: true });
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  await page.evaluate(t => window.renderAt(t), i / FPS);
  await page.screenshot({ path: path.join(tmp, String(i).padStart(4, '0') + '.png'), type: 'png' });
}
execFileSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(FPS), '-i', path.join(tmp, '%04d.png'), '-c:v', 'libx264',
  '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), out]);
await rm(tmp, { recursive: true, force: true });
console.log('wrote', out, N, 'frames in', ((Date.now() - t0) / 1000).toFixed(1), 's');
await browser.close(); srv.close();
