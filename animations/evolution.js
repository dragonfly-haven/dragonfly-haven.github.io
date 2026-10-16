// Evolution in triangles: tens of thousands of tiny, deep golden triangles that
// flow from one stage of evolution to the next, from cosmic dust to AI.
//
//   import { mountEvolution } from './animations/evolution.js';
//   mountEvolution(document.getElementById('evolution'));
//
// Each stage is painted as a density map (stages.js), stippled into triangles,
// lit as if it had volume, and set in a slowly turning field of golden dust.
// Before every change the triangles of one stage are paired with places in the
// next so that each travels a short way, and the GPU (evolution-gl.js) draws
// their whole journey.

import {
  TAU, random, noise3, curl, clamp, smooth, turn, reducedMotion, triangleSize,
  mountCanvas, animate, rasterize, insideDistance, drawTriangles,
} from './core.js';
import { STAGES, RELIEF } from './stages.js';
import { createRenderer } from './evolution-gl.js';

export { STAGES };

// From deep umber shadows to luminous gold.
export const GOLD = ['#1a1206', '#2a1d07', '#3d2a08', '#523909', '#6a4a0b', '#845d0e', '#a07314', '#bd8c22'];

// How everything moves. Lengths are in stage units; a stage is 200 units across.
const MOTION = {
  spread: 0.85, // how much of a move the change takes to sweep across the form
  swirl: 5.5, // units of swirl in mid flight
  twist: 0.4, // radians a form spirals about the centre in mid change, turning each way in turn
  breath: 0.45, // units of drift at rest
  freq: 1 / 70, // swirl features per unit
  spin: 0.012, // radians per second the dust turns
  sway: 0.14, // radians the forms turn in depth, slowly back and forth
  depth: 14, // units a form's full height stands out of the page
};

const DEFAULTS = {
  hold: 2.6, // seconds each stage rests
  move: 3.8, // seconds each change takes
  fit: 0.94, // share of the shorter side the stage fills
  size: null, // triangle side in CSS px; by default as fine as the screen allows
  gap: 1.12, // closest spacing of triangles, in triangle sizes
  start: 0,
  still: null, // a stage to draw once, without motion
  gpu: true, // false draws on a 2D canvas, as where WebGL2 is missing
  seed: 1,
  onStage: null,
};

const STRIDE = 16; // floats per triangle in a planned move, see evolution-gl.js
const CROSSFADE = 1.5; // seconds, between stages when reduced motion is preferred

export function mountEvolution(el, options = {}) {
  const o = { ...DEFAULTS, ...options };
  const calm = reducedMotion(); // then stages crossfade in place instead of moving
  const flat = calm || o.still != null; // drawn on a plain 2D canvas
  const rand = random(o.seed * 7919);
  const noise = noise3(o.seed);
  const c2 = [0, 0];

  let frame = null; // sizes for the current canvas
  let queue = [], samples = new Map();
  let N = 0, cur = null, seeds = null, data = null, ready = null;
  let target = o.start, last = o.start, phase = 'wait', t = 0, clock = 0, paused = false;

  let gpu = null;
  const wantGpu = !flat && o.gpu !== false;
  let surface = mountCanvas(el, build, wantGpu ? { context: 'webgl2', attributes: { antialias: true, premultipliedAlpha: true } } : undefined);
  if (wantGpu) {
    gpu = surface.view.ctx && createRenderer(surface.view.ctx, GOLD);
    if (!gpu) {
      surface.destroy();
      surface = mountCanvas(el, build);
    }
  }
  const loop = o.still == null ? animate(el, tick) : null;
  surface.measure();

  // Sizes everything to the canvas and queues the stages for sampling, which
  // happens a little per frame so a fresh page stays responsive.
  function build(view) {
    const unit = (Math.min(view.width, view.height) * o.fit) / 200; // CSS px per stage unit
    const tri = o.size || triangleSize(view.ratio); // triangle side, CSS px
    // Without the GPU, wider gaps mean fewer triangles, which keeps the frame rate up.
    const spacing = tri * o.gap * (gpu || flat ? 1 : 1.45); // CSS px between triangle centres
    const g = 2.2; // lattice spacing in mask pixels
    const S = Math.round(clamp((200 * unit * g) / spacing, 160, 720)); // mask size
    const sites = (S / g) ** 2 / 0.866;
    frame = { view, unit, tri, S, k: S / 200, g, N: Math.round(sites * 0.3), dust: Math.round(sites * 0.045) };
    samples = new Map();
    queue = o.still == null ? STAGES.map((_, s) => (o.start + s) % STAGES.length) : [o.still];
    N = 0;
    phase = 'wait';
    if (o.still != null) {
      prepare(Infinity);
      const p = samples.get(o.still);
      drawStatic([[p, 1]]);
    }
  }

  // Samples queued stages for up to `budget` ms.
  function prepare(budget) {
    const t0 = performance.now();
    while (queue.length && performance.now() - t0 < budget) {
      const s = queue.shift();
      samples.set(s, sample(STAGES[s], random(o.seed + s * 101)));
    }
  }

  // Stipples one stage: lattice points kept where the painted density beats an
  // ordered-dither threshold, each with a colour, a height and a resting angle.
  function sample(stage, rnd) {
    const { S, k, g } = frame;
    const alpha = rasterize(stage.paint, S, S, k, true);
    const cover = new Uint8Array(S * S);
    for (let i = 0; i < cover.length; i++) cover[i] = alpha[i] > 24 ? 1 : 0;
    const inside = insideDistance(cover, S, S);
    // Height, in stage units: painted, or rounding over `bevel` units in from the outline.
    const height = new Float32Array(S * S);
    if (stage.relief) {
      const painted = rasterize(stage.relief, S, S, k, true);
      for (let i = 0; i < height.length; i++) height[i] = (painted[i] / 255) * RELIEF;
    } else {
      const bevel = (stage.bevel ?? 7) * k;
      for (let i = 0; i < height.length; i++) {
        const h = Math.min(inside[i], bevel) / bevel;
        height[i] = Math.sqrt(1 - (1 - h) * (1 - h)) * (bevel / k);
      }
    }
    const lit = stage.light === false ? null : light(height, S, k);
    const row = g * 0.8660254;
    const cand = [];
    for (let r = 0; r * row < S; r++) {
      for (let c = 0; (c + 0.5) * g < S; c++) {
        const x = (c + (r & 1) * 0.5 + (rnd() - 0.5) * 0.6) * g, y = (r + (rnd() - 0.5) * 0.6) * row;
        const ix = Math.floor(x), iy = Math.floor(y);
        if (ix < 0 || iy < 0 || ix >= S || iy >= S) continue;
        const i = iy * S + ix, a = alpha[i] / 255;
        if (a < 0.03) continue;
        const shade = lit ? lit[i] : 0.6;
        // Shadowed sides are stippled denser, and the outline is kept crisp.
        let density = a * (0.48 + 0.52 * (1 - shade));
        if (inside[i] < g * 1.6) density = Math.max(density, a * 0.92);
        const threshold = (c * 0.7548776662 + r * 0.5698402910) % 1;
        if (density > threshold) cand.push([x, y, i, shade, threshold / density]);
      }
    }
    // Keep room for dust: the faintest points go first when a stage is too dense.
    const cap = frame.N - Math.round(frame.dust * 0.5);
    if (cand.length > cap) cand.sort((a, b) => a[4] - b[4]).length = cap;

    const n = cand.length;
    const p = { n, x: new Float32Array(n), y: new Float32Array(n), z: new Float32Array(n), c: new Uint8Array(n), a: new Float32Array(n) };
    const align = stage.align || 0;
    cand.forEach(([x, y, i, shade], j) => {
      p.x[j] = x / k - 100;
      p.y[j] = y / k - 100;
      p.z[j] = height[i] / 20;
      p.c[j] = clamp(Math.floor((shade * 0.86 + rnd() * 0.2) * 7), 0, 6);
      p.a[j] = turn(rnd() * TAU, -Math.PI / 2, align);
    });
    // Places for dust: a faint galaxy that gathers close around the form like an aura.
    const out = new Uint8Array(S * S);
    for (let i = 0; i < out.length; i++) out[i] = cover[i] ? 0 : 1;
    const away = insideDistance(out, S, S);
    const pool = frame.dust * 2;
    p.dust = new Float32Array(pool * 2);
    for (let j = 0; j < pool; j++) {
      let x, y;
      for (let tries = 0; tries < 40; tries++) {
        [x, y] = galaxy(rnd);
        const ix = Math.floor((x + 100) * k), iy = Math.floor((y + 100) * k);
        const d = ix >= 0 && iy >= 0 && ix < S && iy < S ? away[iy * S + ix] / k : 99;
        if (d > 3 && rnd() < 0.3 + 0.7 * Math.exp(-(d - 3) / 18)) break;
      }
      p.dust[j * 2] = x;
      p.dust[j * 2 + 1] = y;
    }
    return p;
  }

  // Lays out a stage for all N triangles: the form, a halo of dust around it,
  // and any triangles left over hidden inside the form.
  function arrange(s, rnd) {
    const p = samples.get(s);
    const m = p.n, dust = Math.min(N - m, frame.dust), out = layout(N);
    const pool = p.dust.length / 2;
    for (let j = 0; j < N; j++) {
      if (j < m) {
        out.x[j] = p.x[j]; out.y[j] = p.y[j]; out.z[j] = p.z[j]; out.w[j] = 0;
        out.s[j] = 1; out.c[j] = p.c[j]; out.a[j] = p.a[j];
      } else if (j < m + dust) {
        const q = Math.floor(rnd() * pool), x = p.dust[q * 2], y = p.dust[q * 2 + 1];
        out.x[j] = Math.hypot(x, y);
        out.y[j] = Math.atan2(y, x) - MOTION.spin * clock;
        out.z[j] = (rnd() * 2 - 1) * 4;
        out.w[j] = 1;
        // mostly fine dust, with the odd brighter star
        const star = rnd() < 0.035;
        out.s[j] = star ? 0.95 + rnd() * 0.35 : 0.32 + rnd() * 0.42;
        out.c[j] = star ? 7 : 5 + Math.floor(rnd() * 3);
        out.a[j] = rnd() * TAU;
      } else {
        const q = Math.floor(rnd() * m);
        out.x[j] = p.x[q]; out.y[j] = p.y[q]; out.z[j] = p.z[q]; out.w[j] = 0;
        out.s[j] = 0; out.c[j] = p.c[q]; out.a[j] = p.a[q];
      }
    }
    return out;
  }

  // Plans the move to stage `s`: pairs every triangle with a place in it.
  function plan(s) {
    const next = arrange(s, random(o.seed + s * 977 + Math.round(clock * 10)));
    const [ax, ay] = positions(cur), [bx, by] = positions(next);
    const match = pair(ax, ay, bx, by);
    // The change sweeps across from a side that turns with every stage.
    const dir = s * 2.39996 + 0.7, dx = Math.cos(dir), dy = Math.sin(dir);
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < N; i++) {
      const v = ax[i] * dx + ay[i] * dy;
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    const d = new Float32Array(N * STRIDE);
    for (let i = 0; i < N; i++) {
      const j = match[i], at = i * STRIDE;
      const sweep = cur.w[i] && next.w[j] ? rand() : ((ax[i] * dx + ay[i] * dy - lo) / (hi - lo || 1)) * 0.8 + rand() * 0.2;
      d.set([cur.x[i], cur.y[i], cur.z[i], cur.w[i], next.x[j], next.y[j], next.z[j], next.w[j],
        cur.s[i], next.s[j], cur.c[i], next.c[j], MOTION.spread * sweep, seeds[i], cur.a[i], next.a[j]], at);
    }
    // Afterwards each triangle rests where this move takes it.
    const after = layout(N);
    for (let i = 0; i < N; i++) {
      const j = match[i];
      for (const key of 'xyzwsca') after[key][i] = next[key][j];
    }
    return { stage: s, data: d, after };
  }

  // Starts a planned move.
  function begin(move) {
    last = target;
    target = move.stage;
    data = move.data;
    cur = move.after;
    if (gpu) gpu.load(data, N);
    phase = 'move';
    t = 0;
  }

  function tick(dt, render = true) {
    if (!frame) return;
    if (queue.length) prepare(8);
    if (phase === 'wait') {
      if (!samples.has(target)) return render && draw();
      start();
    }
    if (!paused) {
      t += dt;
      clock += dt;
      if (phase === 'move' && t >= (calm ? CROSSFADE : o.move)) {
        phase = 'hold';
        t = 0;
        if (o.onStage) o.onStage(target, STAGES[target].name);
      } else if (phase === 'hold') {
        const next = (target + 1) % STAGES.length;
        if (!ready && samples.has(next)) ready = plan(next);
        if (ready && t >= (calm ? 8 : o.hold)) {
          begin(ready);
          ready = null;
        }
      }
    }
    if (render) draw();
  }

  // The first move: from scattered, invisible dust into the first stage.
  function start() {
    N = frame.N;
    seeds = Float32Array.from({ length: N }, () => rand());
    cur = layout(N);
    for (let i = 0; i < N; i++) {
      const [x, y] = galaxy(rand);
      cur.x[i] = Math.hypot(x, y) * 1.15;
      cur.y[i] = Math.atan2(y, x);
      cur.z[i] = (rand() * 2 - 1) * 4;
      cur.w[i] = 1;
      cur.a[i] = rand() * TAU;
      cur.c[i] = 6;
    }
    ready = null;
    begin(plan(target));
  }

  function draw() {
    const { view } = frame;
    const progress = phase === 'move' ? t / o.move : 1 + t / Math.max(o.hold, 0.001);
    if (calm) {
      if (phase === 'wait') return;
      const f = phase === 'move' ? smooth(clamp(t / CROSSFADE, 0, 1)) : 1;
      return drawStatic(f < 1 ? [[samples.get(last), 1 - f], [samples.get(target), f]] : [[samples.get(target), 1]]);
    }
    if (gpu) {
      const yaw = MOTION.sway * Math.sin(clock * 0.11);
      gpu.draw(view, {
        u_progress: phase === 'wait' ? 0 : progress,
        u_previous: phase === 'move' ? Math.max(0, (t - 1 / 60) / o.move) : progress,
        u_clock: clock,
        u_step: 1 / 60,
        u_spread: MOTION.spread,
        u_swirl: MOTION.swirl,
        u_breath: MOTION.breath,
        u_freq: MOTION.freq,
        u_twist: MOTION.twist * (target % 2 ? 1 : -1),
        u_spin: MOTION.spin,
        u_yaw: yaw,
        u_depth: MOTION.depth,
        u_centre: [view.width / 2, view.height / 2],
        u_view: [view.width, view.height],
        u_scale: frame.unit,
        u_size: frame.tri / Math.sqrt(3),
      });
      return;
    }
    drawMoving(progress);
  }

  // The same journey as the GPU's, worked out here when WebGL2 isn't available.
  const cpu = { x: null, y: null, a: null, s: null, c: null, px: null, py: null };
  function drawMoving(progress) {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    if (!data) return;
    if (!cpu.x || cpu.x.length !== N) for (const key in cpu) cpu[key] = key === 'c' ? new Uint8Array(N) : new Float32Array(N);
    const u0 = frame.unit, cx = width / 2, cy = height / 2;
    for (let i = 0; i < N; i++) {
      const d = i * STRIDE;
      const u = clamp(progress * (1 + MOTION.spread) - data[d + 12], 0, 1), e = smooth(u);
      place(data, d, clock);
      const fx = at[0], fy = at[1];
      place(data, d + 4, clock);
      let x = fx + (at[0] - fx) * e, y = fy + (at[1] - fy) * e;
      curl(noise, x * MOTION.freq, y * MOTION.freq, clock * 0.08, c2);
      const flight = Math.sin(Math.PI * u), amp = MOTION.breath + MOTION.swirl * flight;
      x += c2[0] * amp;
      y += c2[1] * amp;
      const a = (MOTION.twist * (target % 2 ? 1 : -1) * flight) / (1 + (x * x + y * y) / 3600);
      const tx = x * Math.cos(a) - y * Math.sin(a);
      y = cy + (x * Math.sin(a) + y * Math.cos(a)) * u0;
      x = cx + tx * u0;
      const vx = x - cpu.px[i], vy = y - cpu.py[i], rest = turn(data[d + 14], data[d + 15], e);
      cpu.a[i] = vx * vx + vy * vy > 0.04 ? turn(cpu.a[i], Math.atan2(vy, vx), 0.3) : turn(cpu.a[i], rest, 0.08);
      cpu.px[i] = cpu.x[i] = x;
      cpu.py[i] = cpu.y[i] = y;
      cpu.s[i] = data[d + 8] + (data[d + 9] - data[d + 8]) * e;
      cpu.c[i] = u < 0.5 ? data[d + 10] : data[d + 11];
    }
    drawTriangles(ctx, N, cpu.x, cpu.y, cpu.a, cpu.s, cpu.c, GOLD, frame.tri);
  }

  // Draws stages held still, each at an opacity: [[sample, alpha], ...].
  function drawStatic(layers) {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    for (const [p, alpha] of layers) {
      if (!p) continue;
      const x = Float32Array.from(p.x, (v) => width / 2 + v * frame.unit);
      const y = Float32Array.from(p.y, (v) => height / 2 + v * frame.unit);
      ctx.globalAlpha = alpha;
      drawTriangles(ctx, p.n, x, y, p.a, new Float32Array(p.n).fill(1), p.c, GOLD, frame.tri);
    }
    ctx.globalAlpha = 1;
  }

  return {
    get stage() {
      return target;
    },
    go(index) {
      if (!N) return;
      const s = ((index % STAGES.length) + STAGES.length) % STAGES.length;
      if (!samples.has(s)) samples.set(s, sample(STAGES[s], random(o.seed + s * 101)));
      ready = null;
      begin(plan(s));
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
      draw();
    },
    destroy() {
      if (loop) loop.destroy();
      surface.destroy();
    },
  };
}

function layout(n) {
  const f = () => new Float32Array(n);
  return { x: f(), y: f(), z: f(), w: f(), s: f(), c: new Uint8Array(n), a: f() };
}

// Where each triangle of a layout is now, in stage units.
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

// Where one end of a planned move is at a moment, into `at`: forms stay put, dust orbits.
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

// Light from the upper left on a height map (stage units), 0 in shadow to 1 fully lit.
function light(height, S, k) {
  const out = new Float32Array(S * S);
  for (let y = 2; y < S - 2; y++) {
    for (let x = 2; x < S - 2; x++) {
      const i = y * S + x;
      const gx = (height[i + 2] - height[i - 2]) / (4 / k), gy = (height[i + 2 * S] - height[i - 2 * S]) / (4 / k);
      const lit = (0.55 * gx + 0.62 * gy + 0.56) / Math.hypot(gx, gy, 1);
      out[i] = clamp((lit + 0.25) / 1.25, 0, 1);
    }
  }
  return out;
}

// Pairs two equal-sized point sets so nearby points go to nearby places, a
// quick stand-in for optimal transport: both sets are halved again and again
// across their widest direction, and matching halves are paired.
function pair(ax, ay, bx, by) {
  const n = ax.length;
  const A = new Int32Array(n), B = new Int32Array(n), match = new Int32Array(n);
  for (let i = 0; i < n; i++) A[i] = B[i] = i;
  const ka = new Float32Array(n), kb = new Float32Array(n);
  const dirs = [[1, 0], [0, 1], [0.7071, 0.7071], [0.7071, -0.7071]];
  const stack = [0, n];
  while (stack.length) {
    const hi = stack.pop(), lo = stack.pop();
    if (hi - lo === 1) {
      match[A[lo]] = B[lo];
      continue;
    }
    if (hi - lo < 1) continue;
    let best = 0, widest = -1;
    for (let d = 0; d < 4; d++) {
      const [dx, dy] = dirs[d];
      let min = Infinity, max = -Infinity;
      for (let i = lo; i < hi; i++) {
        const va = ax[A[i]] * dx + ay[A[i]] * dy, vb = bx[B[i]] * dx + by[B[i]] * dy;
        min = Math.min(min, va, vb);
        max = Math.max(max, va, vb);
      }
      if (max - min > widest) {
        widest = max - min;
        best = d;
      }
    }
    const [dx, dy] = dirs[best];
    for (let i = lo; i < hi; i++) {
      ka[A[i]] = ax[A[i]] * dx + ay[A[i]] * dy;
      kb[B[i]] = bx[B[i]] * dx + by[B[i]] * dy;
    }
    const mid = (lo + hi) >> 1;
    select(A, ka, lo, hi, mid);
    select(B, kb, lo, hi, mid);
    stack.push(lo, mid, mid, hi);
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
