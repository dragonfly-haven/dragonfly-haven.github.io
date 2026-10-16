// Evolution in sketches: a sequence of pen drawings, from an organic molecule
// to a neural net, drawn in tiny dark yellow dashes laid along their strokes,
// which stream from one drawing into the next.
//
//   import { mountEvolution } from './animations/sketch.js';
//   mountEvolution(document.getElementById('evolution'));
//
// The drawings are stroke-only SVGs listed in motifs/manifest.json. Each is
// read into polylines (svg.js) and dashes are laid along every stroke: more,
// thicker and darker ones where the pen pressed harder. A slowly turning field
// of dust surrounds them. Before every change the dashes of one drawing are
// paired with places in the next so that each travels a short way, and the GPU
// (sketch-gl.js) draws their whole flight.

import { random, noise3, curl, clamp, smooth, reducedMotion, triangleSize, mountCanvas, animate, insideDistance } from './core.js';
import { readSketch } from './svg.js';
import { createRenderer } from './sketch-gl.js';

// Dark yellows: the heaviest lines first, the palest dust last.
export const YELLOW = ['#574800', '#6a5800', '#7d6700', '#907700', '#a38700', '#b69700', '#c9a702', '#dcb812'];

// How everything moves. Lengths are in stage units; a drawing is 200 units across.
const MOTION = {
  spread: 0.85, // how much of a move the change takes to sweep across the drawing
  swirl: 5.5, // units of swirl in mid flight
  twist: 0.4, // radians a drawing spirals about the centre in mid change, each way in turn
  breath: 0.3, // units of drift at rest
  freq: 1 / 70, // swirl features per unit
  spin: 0.012, // radians per second the dust turns
};

const DEFAULTS = {
  motifs: new URL('./motifs/manifest.json', import.meta.url).href, // a manifest, or motifs already loaded
  hold: 2.6, // seconds each drawing rests
  move: 3.8, // seconds each change takes
  fit: 0.94, // share of the shorter side a drawing fills
  dash: null, // dash length in CSS px; by default as fine as the screen allows
  start: 0,
  still: null, // a drawing to show once, without motion
  gpu: true, // false draws on a 2D canvas, as where WebGL2 is missing
  seed: 1,
  onStage: null, // called with (index, title) as each drawing settles
  dusk: 1.6, // seconds the last drawing rests as drifting dust before the first gathers again; 0 to skip
};

const STRIDE = 16; // floats per dash in a planned move, see sketch-gl.js
const CAP = 52000; // most dashes in one drawing; denser drawings get wider gaps
const CROSSFADE = 1.5; // seconds, between drawings when reduced motion is preferred
const GRID = 50; // cells across the stage, for keeping dust off the drawing

// Loads the drawings a manifest lists, in order, as [{ title, slug, hold, sketch }].
export async function loadMotifs(url = DEFAULTS.motifs) {
  const base = new URL(url, document.baseURI);
  const manifest = await (await fetch(base)).json();
  const list = (Array.isArray(manifest) ? manifest : manifest.motifs || manifest.items || [])
    .map((m, i) => ({ ...m, order: m.order ?? i + 1 }))
    .sort((a, b) => a.order - b.order);
  return Promise.all(list.map(async (m) => {
    const file = m.file || m.svg || m.src || `${String(m.order).padStart(2, '0')}-${m.slug}.svg`;
    const text = await (await fetch(new URL(file, base))).text();
    // `hold` is how long the drawing rests, relative to the others
    return { title: m.title || m.slug, slug: m.slug, hold: Number(m.hold) > 0 ? Number(m.hold) : 1, sketch: readSketch(text) };
  }));
}

export function mountEvolution(el, options = {}) {
  const o = { ...DEFAULTS, ...options };
  const calm = reducedMotion(); // then drawings crossfade in place instead of moving
  const flat = calm || o.still != null; // drawn on a plain 2D canvas
  const rand = random(o.seed * 7919);
  const noise = noise3(o.seed);
  const c2 = [0, 0];

  let motifs = null;
  let frame = null; // sizes for the current canvas
  let queue = [], samples = new Map();
  let N = 0, dust = 0, cur = null, seeds = null, data = null, job = null, ready = null, swirl = 1;
  let target = o.start, last = o.start, phase = 'wait', t = 0, clock = 0, paused = false, frames = 0;

  let gpu = null;
  const wantGpu = !flat && o.gpu !== false;
  let surface = mountCanvas(el, build, wantGpu ? { context: 'webgl2', attributes: { antialias: true, premultipliedAlpha: true } } : undefined);
  if (wantGpu) {
    gpu = surface.view.ctx && createRenderer(surface.view.ctx, YELLOW);
    if (!gpu) {
      surface.destroy();
      surface = mountCanvas(el, build);
    }
  }
  const loop = o.still == null ? animate(el, tick) : null;
  const loaded = (Array.isArray(o.motifs) ? Promise.resolve(o.motifs) : loadMotifs(o.motifs)).then((list) => {
    motifs = list;
    if (frame) build(frame.view);
    return list;
  });
  loaded.catch((error) => console.warn('Evolution sketches: could not load the drawings.', error));
  surface.measure();

  // Sizes everything to the canvas and queues the drawings for sampling, which
  // happens a little per frame so a fresh page stays responsive.
  function build(view) {
    const unit = (Math.min(view.width, view.height) * o.fit) / 200; // CSS px per stage unit
    const dash = o.dash || triangleSize(view.ratio) * 1.15; // dash length, CSS px
    // Without the GPU, longer gaps mean fewer dashes, which keeps the frame rate up.
    frame = { view, unit, dash, width: Math.max(1 / view.ratio, dash * 0.27), gap: gpu || flat ? 1 : 1.6 };
    samples = new Map();
    N = 0;
    job = ready = null;
    phase = 'wait';
    if (!motifs) return;
    target = last = ((target % motifs.length) + motifs.length) % motifs.length;
    queue = o.still == null ? motifs.map((_, s) => (target + s) % motifs.length) : [o.still];
    if (o.still != null) {
      prepare(Infinity);
      drawStatic([[samples.get(o.still), 1]]);
    }
  }

  // Samples queued drawings for up to `budget` ms.
  function prepare(budget) {
    const t0 = performance.now();
    while (queue.length && performance.now() - t0 < budget) {
      const s = queue.shift();
      samples.set(s, sample(motifs[s].sketch, random(o.seed + s * 101)));
    }
  }

  // Lays dashes along every stroke of a drawing; a drawing too dense for CAP
  // dashes is laid again with proportionally wider gaps.
  function sample(sketch, rnd) {
    const scale = 200 / Math.max(sketch.width, sketch.height);
    for (let spread = 1; ; ) {
      const p = lay(sketch, scale, (frame.dash * frame.gap * spread) / frame.unit, rnd);
      if (p.n <= CAP || spread > 8) return withDust(p, rnd);
      spread *= (p.n / CAP) * 1.02;
    }
  }

  // Places for dust around a drawing: a faint galaxy that gathers close to the
  // drawing like an aura but keeps off its lines.
  function withDust(p, rnd) {
    const cell = 200 / GRID, taken = new Uint8Array(GRID * GRID);
    for (let j = 0; j < p.n; j++) {
      const gx = Math.floor((p.x[j] + 100) / cell), gy = Math.floor((p.y[j] + 100) / cell);
      if (gx >= 0 && gy >= 0 && gx < GRID && gy < GRID) taken[gy * GRID + gx] = 1;
    }
    const free = taken.map((v) => 1 - v);
    const away = insideDistance(free, GRID, GRID); // in cells
    const pool = 6000;
    p.dust = new Float32Array(pool * 2);
    for (let j = 0; j < pool; j++) {
      let x, y;
      for (let tries = 0; tries < 40; tries++) {
        [x, y] = galaxy(rnd);
        const gx = Math.floor((x + 100) / cell), gy = Math.floor((y + 100) / cell);
        const d = gx >= 0 && gy >= 0 && gx < GRID && gy < GRID ? away[gy * GRID + gx] * cell : 99;
        if (d > 5 && rnd() < 0.45 + 0.55 * Math.exp(-(d - 5) / 16)) break;
      }
      p.dust[j * 2] = x;
      p.dust[j * 2 + 1] = y;
    }
    return p;
  }

  // Lays out a drawing for all N dashes: its own, a halo of dust around it, and
  // any dashes left over hidden among its lines.
  function arrange(s, rnd) {
    if (s === motifs.length) return scattered(rnd);
    const p = samples.get(s);
    const m = p.n, motes = Math.min(N - m, dust), out = layout(N), pool = p.dust.length / 2;
    for (let j = 0; j < N; j++) {
      if (j < m) {
        out.x[j] = p.x[j]; out.y[j] = p.y[j]; out.z[j] = p.z[j]; out.w[j] = 0;
        out.s[j] = p.s[j]; out.c[j] = p.c[j]; out.a[j] = p.a[j];
      } else if (j < m + motes) {
        const q = Math.floor(rnd() * pool), x = p.dust[q * 2], y = p.dust[q * 2 + 1];
        out.x[j] = Math.hypot(x, y);
        out.y[j] = Math.atan2(y, x) - MOTION.spin * clock;
        out.z[j] = 0.6;
        out.w[j] = 1;
        // mostly short motes, with the odd longer streak of a star
        const star = rnd() < 0.04;
        out.s[j] = star ? 1 + rnd() * 0.5 : 0.35 + rnd() * 0.4;
        out.c[j] = star ? 7 : 5 + Math.floor(rnd() * 3);
        out.a[j] = 0;
      } else {
        const q = Math.floor(rnd() * m);
        out.x[j] = p.x[q]; out.y[j] = p.y[q]; out.z[j] = p.z[q]; out.w[j] = 0;
        out.s[j] = 0; out.c[j] = p.c[q]; out.a[j] = p.a[q];
      }
    }
    return out;
  }

  // Every dash as drifting dust, between the last drawing and the first.
  function scattered(rnd) {
    const out = layout(N);
    for (let j = 0; j < N; j++) {
      const [x, y] = galaxy(rnd);
      out.x[j] = Math.hypot(x, y) * (1 + rnd() * 0.15);
      out.y[j] = Math.atan2(y, x) - MOTION.spin * clock;
      out.z[j] = 0.6;
      out.w[j] = 1;
      const star = rnd() < 0.04;
      out.s[j] = star ? 1 + rnd() * 0.5 : 0.35 + rnd() * 0.45;
      out.c[j] = star ? 7 : 4 + Math.floor(rnd() * 4);
    }
    return out;
  }

  // Plans the move to drawing `s`, pairing every dash with a place in it.
  // A generator, so the work can be spread over the frames of a pause.
  function* planning(s) {
    const next = arrange(s, random(o.seed + s * 977 + Math.round(clock * 10)));
    const [ax, ay] = positions(cur), [bx, by] = positions(next);
    const match = yield* pairing(ax, ay, bx, by);
    // The change sweeps across from a side that turns with every drawing.
    const dir = s * 2.39996 + 0.7, dx = Math.cos(dir), dy = Math.sin(dir);
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < N; i++) {
      const v = ax[i] * dx + ay[i] * dy;
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    const d = new Float32Array(N * STRIDE);
    const after = layout(N); // where each dash rests once the move is done
    let travel = 0;
    for (let i = 0; i < N; i++) {
      const j = match[i], at = i * STRIDE;
      travel += Math.hypot(bx[j] - ax[i], by[j] - ay[i]);
      const sweep = cur.w[i] && next.w[j] ? rand() : ((ax[i] * dx + ay[i] * dy - lo) / (hi - lo || 1)) * 0.8 + rand() * 0.2;
      d[at] = cur.x[i]; d[at + 1] = cur.y[i]; d[at + 2] = cur.z[i]; d[at + 3] = cur.w[i];
      d[at + 4] = next.x[j]; d[at + 5] = next.y[j]; d[at + 6] = next.z[j]; d[at + 7] = next.w[j];
      d[at + 8] = cur.s[i]; d[at + 9] = next.s[j]; d[at + 10] = cur.c[i]; d[at + 11] = next.c[j];
      d[at + 12] = MOTION.spread * sweep; d[at + 13] = seeds[i]; d[at + 14] = cur.a[i]; d[at + 15] = next.a[j];
      for (const key of 'xyzwsca') after[key][i] = next[key][j];
    }
    // Drawings that rhyme barely move, so they melt into each other calmly;
    // far-apart ones get the full swirl.
    return { stage: s, data: d, after, swirl: clamp(travel / N / 32, 0.3, 1.1) };
  }

  // Works on a plan for up to `budget` ms; returns the move once it is ready.
  function work(budget) {
    const t0 = performance.now();
    for (;;) {
      const step = job.next();
      if (step.done) {
        job = null;
        return step.value;
      }
      if (performance.now() - t0 > budget) return null;
    }
  }

  // Starts a planned move (with reduced motion, just the change of drawing).
  function begin(move) {
    last = target;
    target = move.stage;
    phase = 'move';
    t = 0;
    if (calm) return;
    data = move.data;
    cur = move.after;
    swirl = move.swirl;
    if (gpu) gpu.load(data, N);
  }

  function tick(dt, render = true) {
    if (!frame || !motifs) return;
    if (queue.length) prepare(8);
    if (phase === 'wait') {
      if (queue.length || !samples.size) return render && draw();
      start();
    }
    if (!paused) {
      t += dt;
      clock += dt;
      if (phase === 'move' && t >= (calm ? CROSSFADE : o.move)) {
        phase = 'hold';
        t = 0;
        if (o.onStage) o.onStage(target, motifs[target]?.title ?? '');
      } else if (phase === 'hold') {
        const next = following(target);
        if (!ready && !job) {
          if (calm) ready = { stage: next };
          else job = planning(next);
        }
        if (job) ready = work(5);
        if (ready && t >= (calm ? 8 : rest(target))) {
          begin(ready);
          ready = null;
        }
      }
    }
    // While a drawing rests it moves slowly, so every other frame is enough.
    if (render && (phase !== 'hold' || (frames++ & 1) === 0)) draw();
  }

  // The stop after `s`: the next drawing, or after the last one a spell of
  // drifting dust (stop motifs.length) from which the first gathers again.
  function following(s) {
    const M = motifs.length;
    if (s >= M) return 0;
    return s === M - 1 && o.dusk > 0 && !calm ? M : (s + 1) % M;
  }

  // How long stop `s` rests: the drawing's own share of the hold, or the dust's spell.
  function rest(s) {
    if (s >= motifs.length) return o.dusk;
    const weight = Number(motifs[s].hold);
    return o.hold * (weight > 0 ? weight : 1);
  }

  // The first move: from scattered, invisible dust into the first drawing.
  function start() {
    let most = 0;
    for (const p of samples.values()) most = Math.max(most, p.n);
    dust = clamp(Math.round(most * 0.08), 400, 4000);
    N = most + dust;
    seeds = Float32Array.from({ length: N }, () => rand());
    cur = layout(N);
    for (let i = 0; i < N; i++) {
      const [x, y] = galaxy(rand);
      cur.x[i] = Math.hypot(x, y) * 1.15;
      cur.y[i] = Math.atan2(y, x);
      cur.z[i] = 0.6;
      cur.w[i] = 1;
      cur.c[i] = 6;
    }
    ready = null;
    if (calm) return begin({ stage: target });
    job = planning(target);
    begin(work(Infinity));
  }

  function draw() {
    const { view } = frame;
    if (calm) {
      if (phase === 'wait') return;
      const f = phase === 'move' ? smooth(clamp(t / CROSSFADE, 0, 1)) : 1;
      return drawStatic(f < 1 ? [[samples.get(last), 1 - f], [samples.get(target), f]] : [[samples.get(target), 1]]);
    }
    const progress = phase === 'move' ? t / o.move : phase === 'hold' ? 1 + t / rest(target) : 0;
    if (gpu) {
      gpu.draw(view, {
        u_progress: progress,
        u_previous: phase === 'move' ? Math.max(0, (t - 1 / 60) / o.move) : progress,
        u_clock: clock,
        u_step: 1 / 60,
        u_spread: MOTION.spread,
        u_swirl: MOTION.swirl * swirl,
        u_breath: MOTION.breath,
        u_freq: MOTION.freq,
        u_twist: MOTION.twist * swirl * (target % 2 ? 1 : -1),
        u_spin: MOTION.spin,
        u_centre: [view.width / 2, view.height / 2],
        u_view: [view.width, view.height],
        u_scale: frame.unit,
        u_length: frame.dash / 2,
        u_width: frame.width / 2,
      });
      return;
    }
    drawMoving(progress);
  }

  // The same flight as the GPU's, worked out here when WebGL2 isn't available.
  const cpu = { x: null, y: null, a: null, s: null, z: null, c: null, px: null, py: null };
  function drawMoving(progress) {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    if (!data) return;
    if (!cpu.x || cpu.x.length !== N) for (const key in cpu) cpu[key] = key === 'c' ? new Uint8Array(N) : new Float32Array(N);
    const unit = frame.unit, cx = width / 2, cy = height / 2, twist = MOTION.twist * swirl * (target % 2 ? 1 : -1);
    for (let i = 0; i < N; i++) {
      const d = i * STRIDE;
      const u = clamp(progress * (1 + MOTION.spread) - data[d + 12], 0, 1), e = smooth(u);
      place(data, d, clock);
      const fx = at[0], fy = at[1];
      place(data, d + 4, clock);
      let x = fx + (at[0] - fx) * e, y = fy + (at[1] - fy) * e;
      curl(noise, x * MOTION.freq, y * MOTION.freq, clock * 0.08, c2);
      const flight = Math.sin(Math.PI * u), amp = MOTION.breath + MOTION.swirl * swirl * flight;
      x += c2[0] * amp;
      y += c2[1] * amp;
      const a = (twist * flight) / (1 + (x * x + y * y) / 3600);
      const rx = x * Math.cos(a) - y * Math.sin(a);
      y = cy + (x * Math.sin(a) + y * Math.cos(a)) * unit;
      x = cx + rx * unit;
      const dust = (u < 0.5 ? data[d + 3] : data[d + 7]) > 0.5;
      const rest = dust ? Math.atan2(y - cy, x - cx) + Math.PI / 2 : data[d + 14] + halfTurn(data[d + 15] - data[d + 14]) * e;
      const vx = x - cpu.px[i], vy = y - cpu.py[i];
      cpu.a[i] = vx * vx + vy * vy > 0.04 ? cpu.a[i] + halfTurn(Math.atan2(vy, vx) - cpu.a[i]) * 0.3 : cpu.a[i] + halfTurn(rest - cpu.a[i]) * 0.1;
      cpu.px[i] = cpu.x[i] = x;
      cpu.py[i] = cpu.y[i] = y;
      cpu.s[i] = data[d + 8] + (data[d + 9] - data[d + 8]) * e;
      cpu.z[i] = data[d + 2] + (data[d + 6] - data[d + 2]) * e;
      cpu.c[i] = u < 0.5 ? data[d + 10] : data[d + 11];
    }
    drawDashes(ctx, N, cpu, frame.dash, frame.width);
  }

  // Draws drawings held still, each at an opacity: [[sample, alpha], ...].
  function drawStatic(layers) {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    for (const [p, alpha] of layers) {
      if (!p) continue;
      const still = {
        x: Float32Array.from(p.x, (v) => width / 2 + v * frame.unit),
        y: Float32Array.from(p.y, (v) => height / 2 + v * frame.unit),
        a: p.a, z: p.z, c: p.c, s: p.s,
      };
      ctx.globalAlpha = alpha;
      drawDashes(ctx, p.n, still, frame.dash, frame.width);
    }
    ctx.globalAlpha = 1;
  }

  return {
    loaded,
    get stage() {
      return target;
    },
    get titles() {
      return motifs ? motifs.map((m) => m.title) : [];
    },
    go(index) {
      if (!N || !motifs) return;
      const s = ((index % motifs.length) + motifs.length) % motifs.length;
      if (!samples.has(s)) samples.set(s, sample(motifs[s].sketch, random(o.seed + s * 101)));
      ready = null;
      if (calm) return begin({ stage: s });
      job = planning(s);
      begin(work(Infinity));
    },
    pause() {
      paused = true;
    },
    play() {
      paused = false;
    },
    // Runs the animation forward by `seconds` at once (for previews and tests).
    advance(seconds) {
      for (let s = 0; s < seconds; s += 1 / 60) tick(1 / 60, false);
      if (frame && motifs) draw();
    },
    destroy() {
      if (loop) loop.destroy();
      surface.destroy();
    },
  };
}

// Dashes along every stroke of a drawing, `step` stage units apart on its lightest lines.
function lay(sketch, scale, step, rnd) {
  const cx = sketch.width / 2, cy = sketch.height / 2;
  const x = [], y = [], a = [], z = [], s = [], c = [];
  for (const { points, weight } of sketch.lines) {
    const w = clamp(weight, 0.5, 4);
    // heavier lines: bolder, darker and slightly closer dashes, always with gaps between
    const gap = step * clamp(1.4 - 0.08 * (w - 1), 1.18, 1.5);
    const thick = 0.75 + 0.45 * (w - 1);
    const shade = clamp(4.3 - 0.9 * (w - 1), 0, 6);
    // a little unevenness, as from a hand: fine lines wobble, every dash differs in length
    const wobble = w < 1.6 ? 0.22 : 0;
    const put = (px, py, angle) => {
      const off = (rnd() - 0.5) * wobble;
      x.push(px - Math.sin(angle) * off);
      y.push(py + Math.cos(angle) * off);
      a.push(angle + (rnd() - 0.5) * 0.12);
      z.push(thick);
      s.push(0.8 + rnd() * 0.4);
      c.push(clamp(Math.round(shade + (rnd() - 0.5) * 1.2), 0, 6));
    };
    let along = rnd() * gap, total = 0, placed = 0;
    for (let i = 2; i < points.length; i += 2) {
      const x0 = (points[i - 2] - cx) * scale, y0 = (points[i - 1] - cy) * scale;
      const x1 = (points[i] - cx) * scale, y1 = (points[i + 1] - cy) * scale;
      const len = Math.hypot(x1 - x0, y1 - y0);
      if (!len) continue;
      const angle = Math.atan2(y1 - y0, x1 - x0);
      while (along <= total + len) {
        const t = (along - total) / len;
        put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, angle);
        placed++;
        along += gap * (0.9 + rnd() * 0.2);
      }
      total += len;
    }
    // a stroke too short for its spacing still gets a dash, across its ends
    if (!placed && total > gap * 0.25) {
      const n = points.length;
      const x0 = (points[0] - cx) * scale, y0 = (points[1] - cy) * scale, x1 = (points[n - 2] - cx) * scale, y1 = (points[n - 1] - cy) * scale;
      put((x0 + x1) / 2, (y0 + y1) / 2, Math.atan2(y1 - y0, x1 - x0));
    }
  }
  return { n: x.length, x: Float32Array.from(x), y: Float32Array.from(y), a: Float32Array.from(a), z: Float32Array.from(z), s: Float32Array.from(s), c: Uint8Array.from(c) };
}

// Fills dashes (centre x/y, angle a, length factor s, thickness z, colour c) in one path per colour.
function drawDashes(ctx, n, d, length, width) {
  const L = length / 2, W = width / 2;
  for (let k = 0; k < YELLOW.length; k++) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      if (d.c[i] !== k || d.s[i] < 0.02) continue;
      const ux = Math.cos(d.a[i]) * L * d.s[i], uy = Math.sin(d.a[i]) * L * d.s[i];
      const vx = -Math.sin(d.a[i]) * W * d.z[i], vy = Math.cos(d.a[i]) * W * d.z[i];
      const px = d.x[i], py = d.y[i];
      ctx.moveTo(px - ux - vx, py - uy - vy);
      ctx.lineTo(px + ux - vx, py + uy - vy);
      ctx.lineTo(px + ux + vx, py + uy + vy);
      ctx.lineTo(px - ux + vx, py - uy + vy);
      ctx.closePath();
    }
    ctx.fillStyle = YELLOW[k];
    ctx.fill();
  }
}

// A dash looks the same turned half way round, so angles only matter modulo pi.
function halfTurn(d) {
  return d - Math.PI * Math.floor(d / Math.PI + 0.5);
}

function layout(n) {
  const f = () => new Float32Array(n);
  return { x: f(), y: f(), z: f(), w: f(), s: f(), c: new Uint8Array(n), a: f() };
}

// Where each dash of a layout is now, in stage units.
function positions(l) {
  const n = l.x.length, x = new Float32Array(n), y = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    if (l.w[i]) {
      x[i] = Math.cos(l.y[i]) * l.x[i];
      y[i] = Math.sin(l.y[i]) * l.x[i];
    } else {
      x[i] = l.x[i];
      y[i] = l.y[i];
    }
  }
  return [x, y];
}

// Where one end of a planned move is at a moment, into `at`: drawings stay put, dust orbits.
const at = [0, 0];
function place(d, i, clock) {
  if (d[i + 3] < 0.5) {
    at[0] = d[i];
    at[1] = d[i + 1];
  } else {
    const a = d[i + 1] + MOTION.spin * clock;
    at[0] = Math.cos(a) * d[i];
    at[1] = Math.sin(a) * d[i];
  }
}

// A point of a faint two-armed galaxy, in stage units from the centre.
function galaxy(rnd) {
  const r = 12 + -Math.log(1 - rnd() * 0.97) * 34;
  const arm = rnd() < 0.5 ? 0 : Math.PI;
  const a = arm + Math.log(r / 10) * 2.1 + (rnd() - 0.5) * (0.9 + r / 90);
  const rr = Math.min(r, 128) * (0.94 + rnd() * 0.12);
  return [Math.cos(a) * rr, Math.sin(a) * rr * 0.92];
}

// Pairs two equal-sized point sets so nearby points go to nearby places, a
// quick stand-in for optimal transport: both sets are halved again and again
// across their widest direction, and matching halves are paired. A generator
// that pauses every so often; it returns match, where a[i] pairs with b[match[i]].
function* pairing(ax, ay, bx, by) {
  const n = ax.length;
  const A = new Int32Array(n), B = new Int32Array(n), match = new Int32Array(n);
  for (let i = 0; i < n; i++) A[i] = B[i] = i;
  // every point's position across, down and along both diagonals
  const pa = [ax, ay, new Float32Array(n), new Float32Array(n)], pb = [bx, by, new Float32Array(n), new Float32Array(n)];
  for (let i = 0; i < n; i++) {
    pa[2][i] = ax[i] + ay[i];
    pa[3][i] = ax[i] - ay[i];
    pb[2][i] = bx[i] + by[i];
    pb[3][i] = bx[i] - by[i];
  }
  const reach = [1, 1, Math.SQRT1_2, Math.SQRT1_2];
  const stack = new Int32Array(256);
  let top = 0, done = 0;
  stack[top++] = 0;
  stack[top++] = n;
  while (top) {
    const hi = stack[--top], lo = stack[--top];
    if (hi - lo === 1) {
      match[A[lo]] = B[lo];
      continue;
    }
    // let the page breathe now and then
    done += hi - lo;
    if (done > 6000) {
      done = 0;
      yield;
    }
    let best = 0, widest = -1;
    for (let d = 0; d < 4; d++) {
      const ka = pa[d], kb = pb[d];
      let min = Infinity, max = -Infinity;
      for (let i = lo; i < hi; i++) {
        const va = ka[A[i]], vb = kb[B[i]];
        if (va < min) min = va;
        if (va > max) max = va;
        if (vb < min) min = vb;
        if (vb > max) max = vb;
      }
      if ((max - min) * reach[d] > widest) {
        widest = (max - min) * reach[d];
        best = d;
      }
    }
    const mid = (lo + hi) >> 1;
    select(A, pa[best], lo, hi, mid);
    select(B, pb[best], lo, hi, mid);
    stack[top++] = lo;
    stack[top++] = mid;
    stack[top++] = mid;
    stack[top++] = hi;
  }
  return match;
}

// Reorders idx[lo..hi) so idx[k] holds the k-th smallest key, smaller keys before it.
function select(idx, key, lo, hi, k) {
  let l = lo, r = hi - 1;
  while (r > l) {
    const pivot = key[idx[(l + r) >> 1]];
    let i = l, j = r;
    while (i <= j) {
      while (key[idx[i]] < pivot) i++;
      while (key[idx[j]] > pivot) j--;
      if (i <= j) {
        const swap = idx[i];
        idx[i] = idx[j];
        idx[j] = swap;
        i++;
        j--;
      }
    }
    if (k <= j) r = j;
    else if (k >= i) l = i;
    else break;
  }
}
