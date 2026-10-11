// Render the den: every frame from window.renderAt(t) in headless Chromium, then ffmpeg.
//   node render.mjs <outdir> [fps=30] [seconds=10] [scale=1] [only=<t>]
// Writes frames/0000.png..., quad.json (the screen's corners in frame pixels) and, unless only= is given,
// room-loop.mp4 (H.264, yuv420p, CRF 16). Serves this folder over http so the module script loads.
import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFile, mkdir, writeFile } from 'fs/promises';
import { execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [out = 'out', fps = '30', seconds = '10', scale = '1', only] = process.argv.slice(2);
const FPS = +fps, SEC = +seconds, N = Math.round(FPS * SEC);
await mkdir(path.join(out, 'frames'), { recursive: true });

const srv = createServer(async (req, res) => {
  try { const f = path.join(here, decodeURIComponent(req.url.split('?')[0].replace(/^\//, '') || 'room.html'));
    const body = await readFile(f); res.writeHead(200, { 'content-type': f.endsWith('.js') ? 'text/javascript' : 'text/html' }); res.end(body); }
  catch (e) { res.writeHead(404); res.end(); }
}).listen(0);
const port = srv.address().port;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080 * +scale, height: 1920 * +scale }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(`http://127.0.0.1:${port}/room.html?t=0&scale=${scale}`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
const quad = await page.evaluate(() => window.screenQuad());
await writeFile(path.join(out, 'quad.json'), JSON.stringify({ quad, fps: FPS, seconds: SEC, scale: +scale }));
console.log('screen quad', JSON.stringify(quad));

async function frame(t, file) {
  await page.evaluate(t => window.renderAt(t), t);
  const data = await page.evaluate(() => document.querySelector('canvas').toDataURL('image/png'));
  await writeFile(file, Buffer.from(data.split(',')[1], 'base64'));
}
const t0 = Date.now();
if (only !== undefined) { await frame(+only, path.join(out, `t${only}.png`)); console.log('one frame', (Date.now() - t0) / 1000, 's'); }
else {
  for (let i = 0; i < N; i++) { await frame(i / FPS, path.join(out, 'frames', String(i).padStart(4, '0') + '.png'));
    if (i % 30 === 0) console.log('frame', i, 'of', N, ((Date.now() - t0) / 1000).toFixed(0), 's'); }
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(FPS), '-i', path.join(out, 'frames', '%04d.png'),
    '-vf', `scale=1080:1920:flags=lanczos,format=yuv420p`, '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '16',
    '-r', String(FPS), '-movflags', '+faststart', path.join(out, 'room-loop.mp4')]);
  console.log('wrote', path.join(out, 'room-loop.mp4'), 'in', ((Date.now() - t0) / 1000).toFixed(0), 's');
}
await browser.close(); srv.close();
