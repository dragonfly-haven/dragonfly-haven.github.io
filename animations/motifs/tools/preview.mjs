// Builds a self-contained preview page of the evolution drawings: the whole
// sequence in motion, as the site's engine plays it, and every drawing held
// still, marked passed or in progress. For publishing as an Artifact, which
// can't load the site's modules, so everything is inlined.
//
//   node animations/motifs/tools/preview.mjs <out.html> [esbuild binary]
//
// The esbuild binary defaults to `esbuild` on the PATH.

import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const motifsDir = join(here, '..');
const [out, esbuild = 'esbuild'] = process.argv.slice(2);
if (!out) {
  console.error('usage: preview.mjs <out.html> [esbuild binary]');
  process.exit(1);
}

const manifest = JSON.parse(await readFile(join(motifsDir, 'manifest.json'), 'utf8'));
const status = JSON.parse(await readFile(join(motifsDir, 'src/status.json'), 'utf8')).motifs;
const files = { galaxy: '01-galaxy.svg', endosymbiosis: '06-endosymbiosis.svg', neanderthals: '19-neanderthals.svg' };
const motifs = await Promise.all(manifest.motifs.map(async (m) => {
  const file = files[m.slug] || `${String(m.order).padStart(2, '0')}-${m.slug}.svg`;
  const text = (await readFile(join(motifsDir, file), 'utf8')).replace(/\n/g, '');
  return { title: m.title, slug: m.slug, hold: m.hold || 1, passed: !!(status[m.slug] && status[m.slug].passed), text };
}));
const passed = motifs.filter((m) => m.passed).length;

const bundle = execFileSync(esbuild, [join(here, 'preview-entry.js'), '--bundle', '--format=iife', '--target=es2020', '--charset=utf8', '--minify', '--define:import.meta.url="https://example.invalid/sketch.js"'], { encoding: 'utf8', maxBuffer: 64 << 20 });
const stamp = new Date().toISOString().slice(0, 16).replace('T', ', ') + ' UTC';

const page = `<title>Evolution Sketches Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap">
<style>
  /* One column like the site itself: the sequence large, then every drawing held still. */
  :root {
    --ivory: #fffdf6; /* the site's page */
    --ink: #2b2a27;
    --muted: #6e685d;
    --rule: #e6e0d2;
    --ochre: #7d6700; /* the engine's mid yellow, for marks */
    --serif: "EB Garamond", Garamond, Georgia, serif;
    color-scheme: light;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--ivory);
    color: var(--ink);
    font: 18px/1.5 var(--serif);
    padding-left: max(16px, env(safe-area-inset-left, 0px));
    padding-right: max(16px, env(safe-area-inset-right, 0px));
    padding-block: 1.5rem 4rem;
  }
  .wrap { max-width: 64rem; margin: 0 auto; display: grid; gap: 1.5rem; }
  header { display: grid; gap: 0.2rem; }
  h1 { font-weight: 400; font-size: 1.7rem; margin: 0; text-wrap: balance; }
  h2 { font-weight: 400; font-size: 1.3rem; margin: 1rem 0 0; }
  .note { color: var(--muted); margin: 0; max-width: 40rem; }
  .stage { width: min(100%, 72vh); aspect-ratio: 1; max-width: 100%; justify-self: center; position: relative; }
  .controls { display: flex; gap: 0.75rem; align-items: center; justify-content: center; flex-wrap: wrap; }
  .controls output { min-width: 13rem; text-align: center; font-size: 1.15rem; }
  button {
    font: inherit; color: var(--ink); background: transparent; cursor: pointer;
    border: 1px solid var(--rule); border-radius: 999px; padding: 0.15rem 0.9rem;
  }
  button:hover { border-color: var(--muted); }
  button:focus-visible, figure:focus-visible { outline: 2px solid var(--ochre); outline-offset: 2px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 13.5rem), 1fr)); gap: 1.25rem 1rem; }
  figure { margin: 0; cursor: pointer; display: grid; gap: 0.3rem; min-width: 0; }
  figure .still { aspect-ratio: 1; position: relative; border: 1px solid var(--rule); max-width: 100%; }
  figcaption { display: flex; justify-content: space-between; gap: 0.5rem; align-items: baseline; }
  .num { color: var(--muted); font-variant-numeric: tabular-nums; margin-right: 0.3rem; }
  .chip { font-size: 0.8rem; letter-spacing: 0.04em; color: var(--muted); white-space: nowrap; }
  .chip.passed { color: var(--ochre); }
  .chip.passed::before { content: "✓ "; }
</style>

<div class="wrap">
  <header>
    <h1>Evolution sketches</h1>
    <p class="note">${passed === motifs.length
      ? `All ${motifs.length} drawings as the page will play them; each has passed review.`
      : `A draft of the drawings as the page will play them, ${passed} of ${motifs.length} passed review.`} Built ${stamp}.</p>
  </header>
  <div class="stage" id="evolution"></div>
  <div class="controls">
    <button id="prev" aria-label="Previous drawing">‹</button>
    <output id="label">&nbsp;</output>
    <button id="next" aria-label="Next drawing">›</button>
    <button id="pause">Pause</button>
  </div>
  <h2>Every drawing, held still</h2>
  <div class="grid" id="sheet"></div>
</div>

<script>
${bundle.trim()}
</script>
<script>
const MOTIFS = ${JSON.stringify(motifs)};
const list = MOTIFS.map((m) => ({ title: m.title, slug: m.slug, hold: m.hold, text: m.text, sketch: null }));
const label = document.getElementById('label');
const name = (i) => (list[i] ? (i + 1) + '. ' + list[i].title : 'Drifting dust');
const evolution = window.mountEvolution(document.getElementById('evolution'), {
  motifs: list,
  onStage: (i) => (label.textContent = name(i)),
});
const show = () => (label.textContent = name(evolution.stage));
evolution.loaded.then(show);
const go = (i) => { evolution.go(i); show(); };
document.getElementById('prev').onclick = () => go(evolution.stage - 1);
document.getElementById('next').onclick = () => go(evolution.stage + 1);
const pause = document.getElementById('pause');
pause.onclick = () => {
  const playing = pause.textContent === 'Pause';
  playing ? evolution.pause() : evolution.play();
  pause.textContent = playing ? 'Play' : 'Pause';
};
const sheet = document.getElementById('sheet');
MOTIFS.forEach((m, i) => {
  const f = document.createElement('figure');
  f.tabIndex = 0;
  f.setAttribute('role', 'button');
  f.setAttribute('aria-label', 'Show ' + m.title + ' in the sequence');
  f.innerHTML = '<div class="still"></div><figcaption><span><span class="num">' + (i + 1) + '</span>' + m.title +
    '</span><span class="chip' + (m.passed ? ' passed' : '') + '">' + (m.passed ? 'passed' : 'in progress') + '</span></figcaption>';
  sheet.append(f);
  window.mountEvolution(f.querySelector('.still'), { motifs: list, still: i });
  const pick = () => { go(i); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  f.onclick = pick;
  f.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } };
});
</script>
`;
await writeFile(out, page);
console.log('wrote', out, (Buffer.byteLength(page) / 1e6).toFixed(2), 'MB,', passed, 'of 21 passed');
