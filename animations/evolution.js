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
// their whole journey. Changes overlap like a relay: each sweeps across a form,
// and the next sets off before the last has quite landed, so the flow never stops.

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
  sweep: 0.36, // share of the time between changes that one takes to sweep across a form
  rest: 0.7, // share of that sweep each part of a form rests; under 1, the next change sets off before the last has landed
  ramp: 0.2, // share of each flight spent speeding up, and again slowing down; triangles cruise in between
  swirl: 5.5, // units of swirl in mid flight
  twist: 0.4, // radians a form spirals about the centre in mid change, turning each way in turn
  breath: 0.45, // units of drift at rest
  ripple: 0.5, // units a slow ripple moves every form by, so none ever stands still
  freq: 1 / 70, // swirl features per unit
  spin: 0.012, // radians per second the dust turns
  sway: 0.14, // radians the forms turn in depth, slowly back and forth
  depth: 14, // units a form's full height stands out of the page
};

const DEFAULTS = {
  speed: 1.4, // how fast it all plays (changes, rests, dust); the times here are at speed 1
  move: 3.6, // seconds from one change setting off to the next
  hold: 0, // extra seconds each part of a form rests
  fit: 0.94, // share of the shorter side the stage fills
  size: null, // triangle side in CSS px; by default as fine as the screen allows
  gap: 1.12, // closest spacing of triangles, in triangle sizes
  start: 0,
  still: null, // a stage to draw once, without motion
  gpu: true, // false draws on a 2D canvas, as where WebGL2 is missing
  seed: 1,
  onStage: null,
};

const STRIDE = 20; // floats per triangle in a planned change, see evolution-gl.js
const MIN_FLIGHT = 0.4; // shortest flight, as a share of the time between changes
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
  let N = 0, cur = null, seeds = null, moves = [], job = null, ready = null, sampler = null;
  let target = o.start, last = o.start, phase = 'wait', t = 0, clock = 0, paused = false;

  // With the GPU, its context and shaders are set up over the first frames
  // (see setup), so mounting costs the page almost nothing.
  let gpu = null, gpuAge = 0, wantGpu = !flat && o.gpu !== false;
  let surface = mountCanvas(el, build, wantGpu ? { context: 'webgl2', attributes: { antialias: true, premultipliedAlpha: true }, defer: true } : undefined);
  const loop = o.still == null ? animate(el, tick) : null;
  surface.measure();

  // Sizes everything to the canvas and queues the stages for sampling, which
  // happens a little per frame so a fresh page stays responsive.
  function build(view) {
    const unit = (Math.min(view.width, view.height) * o.fit) / 200; // CSS px per stage unit
    const tri = o.size || triangleSize(view.ratio); // triangle side, CSS px
    // Without the GPU, wider gaps mean fewer triangles, which keeps the frame rate up.
    const spacing = tri * o.gap * (wantGpu || flat ? 1 : 1.45); // CSS px between triangle centres
    const g = 2.2; // lattice spacing in mask pixels
    const S = Math.round(clamp((200 * unit * g) / spacing, 160, 720)); // mask size
    const sites = (S / g) ** 2 / 0.866;
    frame = { view, unit, tri, S, k: S / 200, g, N: Math.round(sites * 0.32), dust: Math.round(sites * 0.065) };
    samples = new Map();
    queue = o.still == null ? STAGES.map((_, s) => (o.start + s) % STAGES.length) : [o.still];
    N = 0;
    moves = [];
    job = ready = sampler = null;
    phase = 'wait';
    if (o.still != null) {
      prepare(Infinity);
      const p = samples.get(o.still);
      drawStatic([[p, 1]]);
    }
  }

  // Samples queued stages for about `budget` ms, a slice of a stage at a time.
  function prepare(budget) {
    const t0 = performance.now();
    do {
      if (!sampler) {
        if (!queue.length) return;
        const s = queue.shift();
        sampler = { s, steps: sample(STAGES[s], random(o.seed + s * 101)) };
      }
      const step = sampler.steps.next();
      if (step.done) {
        samples.set(sampler.s, step.value);
        sampler = null;
      }
    } while (performance.now() - t0 < budget);
  }

  // Sets up the GPU: the context on the first frame, after the page has
  // painted, then the shaders, which build in the background. True once it
  // can draw (or when it isn't used); falls back to 2D if it can't.
  function setup() {
    if (!wantGpu) return true;
    if (!gpu) {
      const gl = surface.acquire();
      gpu = gl && createRenderer(gl, GOLD);
      gpuAge = 0;
      return gpu ? false : fallback();
    }
    // Give the build a few frames before asking: where the browser can't
    // tell without waiting, asking waits for the build to finish.
    if (gpuAge++ < 3) return false;
    if (gpu.ready) return true;
    return gpu.failed ? fallback() : false;
  }

  function fallback() {
    wantGpu = false;
    gpu = null;
    surface.destroy();
    surface = mountCanvas(el, build);
    surface.measure();
    return true;
  }

  // Stipples one stage: lattice points kept where the painted density beats an
  // ordered-dither threshold, each with a colour, a height and a resting angle.
  // A generator that pauses between its heavier steps.
  function* sample(stage, rnd) {
    const { S, k, g } = frame;
    const alpha = rasterize(stage.paint, S, S, k, true);
    yield;
    const cover = new Uint8Array(S * S);
    for (let i = 0; i < cover.length; i++) cover[i] = alpha[i] > 24 ? 1 : 0;
    const inside = insideDistance(cover, S, S);
    yield;
    // Height, in stage units: painted, or rounding over `bevel` units in from the outline.
    const height = new Float32Array(S * S);
    if (stage.relief) {
      const painted = rasterize(stage.relief, S, S, k, true);
      for (let i = 0; i < height.length; i++) height[i] = (painted[i] / 255) * RELIEF;
      yield;
    } else {
      const bevel = (stage.bevel ?? 7) * k;
      for (let i = 0; i < height.length; i++) {
        const h = Math.min(inside[i], bevel) / bevel;
        height[i] = Math.sqrt(1 - (1 - h) * (1 - h)) * (bevel / k);
      }
    }
    yield;
    const lit = stage.light === false ? null : light(height, S, k);
    yield;
    const row = g * 0.8660254;
    const cand = [];
    for (let r = 0; r * row < S; r++) {
      if (r % 64 === 63) yield;
      for (let c = 0; (c + 0.5) * g < S; c++) {
        const x = (c + (r & 1) * 0.5 + (rnd() - 0.5) * 0.6) * g, y = (r + (rnd() - 0.5) * 0.6) * row;
        const ix = Math.floor(x), iy = Math.floor(y);
        if (ix < 0 || iy < 0 || ix >= S || iy >= S) continue;
        const i = iy * S + ix, a = alpha[i] / 255;
        if (a < 0.03) continue;
        const shade = lit ? lit[i] : 0.6;
        // Shadowed sides are stippled denser, and solid outlines are kept crisp.
        let density = a * (0.48 + 0.52 * (1 - shade));
        if (a > 0.5 && inside[i] < g * 1.6) density = Math.max(density, a * 0.92);
        const threshold = (c * 0.7548776662 + r * 0.5698402910) % 1;
        if (density > threshold) cand.push([x, y, i, shade, threshold / density]);
      }
    }
    // Keep room for dust: the faintest points go first when a stage is too dense.
    const cap = frame.N - Math.round(frame.dust * 0.5);
    if (cand.length > cap) cand.sort((a, b) => a[4] - b[4]).length = cap;
    yield;

    const n = cand.length;
    const p = { n, x: new Float32Array(n), y: new Float32Array(n), z: new Float32Array(n), c: new Uint8Array(n), a: new Float32Array(n) };
    const align = stage.align || 0;
    cand.forEach(([x, y, i, shade], j) => {
      p.x[j] = x / k - 100;
      p.y[j] = y / k - 100;
      p.z[j] = height[i] / 20;
      p.c[j] = clamp(Math.floor((shade * 0.86 + rnd() * 0.2) * 7), 0, 6);
      // Near the outline triangles follow its grain; deeper in they lie as they fall.
      const ix = i % S;
      const gx = inside[Math.min(i + 2, i - ix + S - 1)] - inside[Math.max(i - 2, i - ix)];
      const gy = inside[Math.min(i + 2 * S, (S - 1) * S + ix)] - inside[Math.max(i - 2 * S, ix)];
      const grain = Math.atan2(gy, gx) + Math.PI / 2 + (rnd() - 0.5) * 0.7;
      const edge = clamp(1.4 - inside[i] / (g * 3), 0, 1);
      p.a[j] = turn(turn(rnd() * TAU, grain, edge), -Math.PI / 2, align);
    });
    yield;
    // Places for dust: a faint galaxy that gathers close around the form like an aura.
    const out = new Uint8Array(S * S);
    for (let i = 0; i < out.length; i++) out[i] = cover[i] ? 0 : 1;
    const away = insideDistance(out, S, S);
    yield;
    const pool = frame.dust * 2;
    p.dust = new Float32Array(pool * 2);
    for (let j = 0; j < pool; j++) {
      if (j % 3000 === 2999) yield;
      let x, y;
      for (let tries = 0; tries < 40; tries++) {
        [x, y] = galaxy(rnd);
        const ix = Math.floor((x + 100) * k), iy = Math.floor((y + 100) * k);
        const d = ix >= 0 && iy >= 0 && ix < S && iy < S ? away[iy * S + ix] / k : 99;
        if (d > 6 && rnd() < 0.45 + 0.55 * Math.exp(-(d - 6) / 16)) break;
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

  const period = () => o.move + o.hold; // seconds from one change setting off to the next
  const width = () => MOTION.sweep * o.move; // seconds a change takes to sweep across a form
  const pause = () => MOTION.rest * width() + o.hold; // seconds each part of a form rests

  // Sets when each triangle of a layout will set off in the change that
  // leaves it towards stage `s`: when that change's sweep reaches it, from a
  // side that turns with every stage. Dust sets off at random.
  function sweep(l, s, rnd) {
    const W = width(), dir = s * 2.39996 + 0.7, dx = Math.cos(dir), dy = Math.sin(dir);
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < N; i++) {
      if (l.w[i]) continue;
      const v = l.x[i] * dx + l.y[i] * dy;
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    for (let i = 0; i < N; i++) {
      l.d[i] = l.w[i] ? W * rnd() : W * (((l.x[i] * dx + l.y[i] * dy - lo) / (hi - lo || 1)) * 0.8 + rnd() * 0.2);
    }
  }

  // Plans the change to stage `s`, pairing every triangle with a place in it.
  // A generator, so the work can be spread over the frames of the change before.
  function* planning(s) {
    const rnd = random(o.seed + s * 977 + Math.round(clock * 10));
    const next = arrange(s, rnd);
    const [ax, ay] = positions(cur, clock), [bx, by] = positions(next, clock);
    const match = yield* pairing(ax, ay, bx, by);
    const after = layout(N); // where each triangle rests once it has landed
    for (let i = 0; i < N; i++) {
      const j = match[i];
      for (const key of 'xyzwsca') after[key][i] = next[key][j];
    }
    yield;
    // Each triangle sets off when this change's sweep reaches it, and lands in
    // the order it will set off in the next change, a little before it does:
    // so every part of a form rests the same short while, the next change
    // sweeps in before this one has quite landed, and the flow never stops.
    sweep(after, (s + 1) % STAGES.length, rnd);
    const P = period(), lead = pause();
    const data = new Float32Array(N * STRIDE), arrive = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      const j = match[i], at = i * STRIDE;
      arrive[i] = Math.max(P + after.d[i] - lead, cur.d[i] + MIN_FLIGHT * P);
      data[at] = cur.x[i]; data[at + 1] = cur.y[i]; data[at + 2] = cur.z[i]; data[at + 3] = cur.w[i];
      data[at + 4] = next.x[j]; data[at + 5] = next.y[j]; data[at + 6] = next.z[j]; data[at + 7] = next.w[j];
      data[at + 8] = cur.s[i]; data[at + 9] = next.s[j]; data[at + 10] = cur.c[i]; data[at + 11] = next.c[j];
      data[at + 12] = cur.a[i]; data[at + 13] = next.a[j]; data[at + 14] = seeds[i];
      data[at + 16] = cur.d[i]; data[at + 17] = arrive[i];
    }
    return { stage: s, data, arrive, after };
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

  // Sets a planned change off at clock time S (with reduced motion, just the change of stage).
  function startMove(move, S) {
    if (!calm && moves.length && o.onStage) o.onStage(target, STAGES[target].name); // the stage at its fullest
    last = target;
    target = move.stage;
    if (calm) {
      phase = 'move';
      t = 0;
      return;
    }
    const P = period(), data = move.data;
    for (let i = 0; i < N; i++) {
      const at = i * STRIDE;
      // A triangle shows in this change from when it landed in the last one,
      // and never sets off before that.
      const shown = Math.max(cur.arrive[i] - S, -1e6);
      const depart = Math.max(data[at + 16], shown);
      const arrive = Math.max(move.arrive[i], depart + MIN_FLIGHT * P);
      data[at + 16] = depart;
      data[at + 17] = arrive;
      data[at + 18] = shown;
      move.after.arrive[i] = S + arrive;
    }
    move.S = S;
    move.twist = MOTION.twist * (move.stage % 2 ? 1 : -1);
    // The newest change takes the buffer the oldest one used.
    const newest = moves[moves.length - 1];
    move.slot = newest ? 1 - newest.slot : 0;
    if (gpu) gpu.load(move.slot, data, N);
    moves = newest ? [newest, move] : [move];
    cur = move.after;
    phase = 'run';
  }

  function tick(dt, render = true) {
    if (!frame) return;
    if (!setup()) {
      prepare(6); // sample stages while the GPU gets ready
      return;
    }
    if (queue.length || sampler) prepare(phase === 'run' ? 4 : 8);
    if (phase === 'wait') {
      if (!samples.has(target)) return render && draw();
      start();
    }
    if (phase === 'plan') {
      // A change started out of turn (the first one, or a jump) is planned a slice per frame too.
      if (job) ready = work(8);
      if (!ready) return render && draw();
      startMove(ready, clock);
      ready = null;
    }
    if (!paused) {
      // Reduced motion keeps its own slow pace.
      const step = calm ? dt : dt * o.speed;
      t += step;
      clock += step;
      if (calm) {
        if (phase === 'move' && t >= CROSSFADE) {
          phase = 'hold';
          t = 0;
          if (o.onStage) o.onStage(target, STAGES[target].name);
        } else if (phase === 'hold' && t >= 8) startMove({ stage: (target + 1) % STAGES.length }, clock);
      } else {
        // The next change is planned while this one plays, and sets off on time.
        const next = (target + 1) % STAGES.length, current = moves[moves.length - 1];
        if (!ready && !job && samples.has(next)) job = planning(next);
        if (job) ready = work(4);
        if (ready && clock >= current.S + period()) {
          startMove(ready, Math.max(current.S + period(), clock - step));
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
      cur.d[i] = width() * rand();
    }
    ready = null;
    if (calm) return startMove({ stage: target }, clock);
    job = planning(target);
    phase = 'plan';
  }

  function draw() {
    const { view } = frame;
    if (calm) {
      if (phase === 'wait') return;
      const f = phase === 'move' ? smooth(clamp(t / CROSSFADE, 0, 1)) : 1;
      return drawStatic(f < 1 ? [[samples.get(last), 1 - f], [samples.get(target), f]] : [[samples.get(target), 1]]);
    }
    // The newest change, and the one before it until its last triangles have landed.
    const batches = moves.map((m, k) => ({
      slot: m.slot,
      u_time: clock - m.S,
      u_retired: k < moves.length - 1 ? 1 : 0,
      u_twist: m.twist,
    }));
    if (gpu) {
      gpu.draw(view, {
        u_clock: clock,
        u_step: o.speed / 60,
        u_ramp: MOTION.ramp,
        u_swirl: MOTION.swirl,
        u_breath: MOTION.breath,
        u_ripple: MOTION.ripple,
        u_freq: MOTION.freq,
        u_spin: MOTION.spin,
        u_yaw: MOTION.sway * Math.sin(clock * 0.11),
        u_depth: MOTION.depth,
        u_centre: [view.width / 2, view.height / 2],
        u_view: [view.width, view.height],
        u_scale: frame.unit,
        u_size: frame.tri / Math.sqrt(3),
      }, batches);
      return;
    }
    drawMoving(batches);
  }

  // The same journey as the GPU's, worked out here when WebGL2 isn't available.
  const cpu = { x: null, y: null, a: null, s: null, c: null, px: null, py: null };
  function drawMoving(batches) {
    const { ctx, width: w, height: h } = surface.view;
    ctx.clearRect(0, 0, w, h);
    if (!N || !moves.length) return;
    if (!cpu.x || cpu.x.length !== N) for (const key in cpu) cpu[key] = key === 'c' ? new Uint8Array(N) : new Float32Array(N);
    const unit = frame.unit, cx = w / 2, cy = h / 2;
    cpu.s.fill(0);
    batches.forEach(({ u_time: local, u_retired: retired, u_twist: twist }, k) => {
      const data = moves[k].data;
      for (let i = 0; i < N; i++) {
        const d = i * STRIDE;
        if (local < data[d + 18] || (retired && local >= data[d + 17])) continue;
        const u = clamp((local - data[d + 16]) / Math.max(data[d + 17] - data[d + 16], 0.001), 0, 1), e = ease(u);
        place(data, d, clock);
        const fx = at[0], fy = at[1];
        place(data, d + 4, clock);
        let x = fx + (at[0] - fx) * e, y = fy + (at[1] - fy) * e;
        curl(noise, x * MOTION.freq, y * MOTION.freq, clock * 0.08, c2);
        const mid = Math.sin(Math.PI * u), amp = MOTION.breath + MOTION.swirl * mid;
        x += c2[0] * amp;
        y += c2[1] * amp;
        // a slow ripple runs through every form, so even a finished one never stands still
        const wx = Math.sin(y * 0.11 + clock * 1.3) * MOTION.ripple, wy = Math.sin(x * 0.13 - clock * 1.1) * MOTION.ripple;
        x += wx;
        y += wy;
        const a = (twist * mid) / (1 + (x * x + y * y) / 3600);
        const tx = x * Math.cos(a) - y * Math.sin(a);
        y = cy + (x * Math.sin(a) + y * Math.cos(a)) * unit;
        x = cx + tx * unit;
        const vx = x - cpu.px[i], vy = y - cpu.py[i], rest = turn(data[d + 12], data[d + 13], e);
        cpu.a[i] = vx * vx + vy * vy > 0.04 ? turn(cpu.a[i], Math.atan2(vy, vx), 0.3) : turn(cpu.a[i], rest, 0.08);
        cpu.px[i] = cpu.x[i] = x;
        cpu.py[i] = cpu.y[i] = y;
        cpu.s[i] = data[d + 8] + (data[d + 9] - data[d + 8]) * e;
        cpu.c[i] = u < 0.5 ? data[d + 10] : data[d + 11];
      }
    });
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
      if (!samples.has(s)) samples.set(s, finish(sample(STAGES[s], random(o.seed + s * 101))));
      ready = null;
      if (calm) return startMove({ stage: s }, clock);
      job = planning(s);
      phase = 'plan';
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

// Runs a generator to its end and returns what it returns.
function finish(steps) {
  for (;;) {
    const step = steps.next();
    if (step.done) return step.value;
  }
}

// Where every triangle rests, and how: x, y (or radius and angle for dust),
// height, dust flag, size, colour and angle; plus when it sets off in the
// change that leaves this layout (d, seconds from that change's start) and
// when it landed here (arrive, clock seconds).
function layout(n) {
  const f = () => new Float32Array(n);
  return { x: f(), y: f(), z: f(), w: f(), s: f(), c: new Uint8Array(n), a: f(), d: f(), arrive: new Float64Array(n).fill(-Infinity) };
}

// Speeds up over the first `ramp` of a flight, cruises, and slows down over the last.
function ease(u) {
  const a = MOTION.ramp, v = 1 / (1 - a);
  if (u < a) return (v * u * u) / (2 * a);
  if (u > 1 - a) return 1 - (v * (1 - u) * (1 - u)) / (2 * a);
  return v * (u - a / 2);
}

// Where each triangle of a layout is at `clock`, in stage units (dust has orbited on).
function positions(l, clock) {
  const n = l.x.length, x = new Float32Array(n), y = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    if (l.w[i]) {
      const a = l.y[i] + MOTION.spin * clock;
      x[i] = Math.cos(a) * l.x[i];
      y[i] = Math.sin(a) * l.x[i];
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
