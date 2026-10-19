// Renders evolution motifs to PNG for review: as pen lines, and as the
// site's engine draws them, in dashes, at standard (1x) and sharp (2x) screens.
//
//   node animations/motifs/tools/render.mjs <out dir> <svg>... [--box 700] [--line 1000] [--facing]
//
// For each drawing NN-slug.svg it writes, into <out dir>:
//   NN-slug.png       black pen lines on ivory, 1000 px (facing right, as drawn,
//                     unless --facing keeps the page's mirroring)
//   NN-slug-1x.png    the engine's dashes in a 700 px box on a standard screen
//   NN-slug-2x.png    the same box on a sharp screen (1400 px image)
// With --sheet, it also writes sheet.png: every drawing as pen lines, as faced.
//
// Needs Playwright (installed globally here) and Chromium.

import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, resolve, relative, basename, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  ({ chromium } = require('/opt/node22/lib/node_modules/playwright'));
}

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../..'); // the site folder

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  if (i < 0) return fallback;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
};
const has = (name) => {
  const i = args.indexOf(`--${name}`);
  if (i < 0) return false;
  args.splice(i, 1);
  return true;
};
const box = Number(flag('box', 700));
const lineSize = Number(flag('line', 1000));
const facing = has('facing');
const sheet = has('sheet');
const only = flag('only', 'line,1x,2x').split(',');
const [outDir, ...svgs] = args;
if (!outDir || !svgs.length) {
  console.error('usage: render.mjs <out dir> <svg>... [--box 700] [--line 1000] [--facing] [--sheet] [--only line,1x,2x]');
  process.exit(1);
}
await mkdir(outDir, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2' };
const files = new Map(); // extra files served from outside the site folder
const server = createServer(async (req, res) => {
  const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const file = files.get(path) || join(root, path);
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end();
  }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

// Each SVG is served under /_svg/<n>/<name>, wherever it lives.
const urls = svgs.map((svg, n) => {
  const url = `/_svg/${n}/${basename(svg)}`;
  files.set(url, resolve(svg));
  return url;
});

const browser = await chromium.launch();
const ivory = '#fffdf6';

async function lines(svgPath, out, size, keepMirror) {
  let text = await readFile(svgPath, 'utf8');
  if (!keepMirror) text = text.replace(/<g transform="matrix\(-1 0 0 1 1000 0\)">/, '<g>');
  const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
  await page.setContent(`<style>html,body{margin:0;background:${ivory}}svg{width:${size}px;height:${size}px;display:block}</style>${text}`);
  await page.screenshot({ path: out });
  await page.close();
}

async function dashes(urlList, out, ratio, perRow = 1) {
  const n = urlList.length, cols = Math.min(perRow, n), rows = Math.ceil(n / cols);
  const page = await browser.newPage({ viewport: { width: box * cols, height: box * rows }, deviceScaleFactor: ratio });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  const list = urlList.map((u) => '../../..' + u).join(',');
  await page.goto(`${base}/animations/motifs/tools/still.html?box=${box}&files=${encodeURIComponent(list)}`);
  await page.waitForFunction(() => document.body.dataset.done === '1', null, { timeout: 120000 });
  await page.waitForTimeout(300);
  if (errors.length) console.error('page errors:', errors.join('\n'));
  await page.screenshot({ path: out });
  await page.close();
}

for (let i = 0; i < svgs.length; i++) {
  const name = basename(svgs[i], '.svg');
  if (only.includes('line')) await lines(svgs[i], join(outDir, `${name}.png`), lineSize, facing);
  if (only.includes('1x')) await dashes([urls[i]], join(outDir, `${name}-1x.png`), 1);
  if (only.includes('2x')) await dashes([urls[i]], join(outDir, `${name}-2x.png`), 2);
  console.log('rendered', name);
}

if (sheet) {
  // pen lines as faced on the page, seven across
  const cell = 280, cols = 7, rows = Math.ceil(svgs.length / cols);
  const cells = await Promise.all(svgs.map(async (svg) => {
    const text = await readFile(svg, 'utf8');
    return `<figure><div class="img">${text}</div><figcaption>${basename(svg, '.svg').replace(/^(\d+)-/, '$1 · ').replace(/-/g, ' ')}</figcaption></figure>`;
  }));
  const page = await browser.newPage({ viewport: { width: cols * (cell + 16) + 16, height: rows * (cell + 46) + 16 }, deviceScaleFactor: 1.5 });
  await page.setContent(`<style>
    html,body{margin:0;background:#efe9dc;font:15px Georgia,serif;color:#2b2a27}
    .g{display:grid;grid-template-columns:repeat(${cols},${cell}px);gap:16px;padding:16px}
    figure{margin:0} .img{background:${ivory};width:${cell}px;height:${cell}px;border:1px solid #d9d2c3;box-sizing:border-box}
    svg{width:100%;height:100%;display:block} figcaption{margin-top:6px}
  </style><div class="g">${cells.join('')}</div>`);
  await page.screenshot({ path: join(outDir, 'sheet.png'), fullPage: true });
  await page.close();
  console.log('rendered sheet');
}

await browser.close();
server.close();
