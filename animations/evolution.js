// Evolution in triangles: thousands of tiny, almost black orange triangles that
// flow from one stage of evolution to the next, from organic matter to AI.
//
//   import { mountEvolution } from './animations/evolution.js';
//   mountEvolution(document.getElementById('evolution'), { style: 'flow' });

import {
  TRIANGLE_SIZE, EMBER, TAU, random, noise3, curl, clamp, smooth, turn, reducedMotion,
  mountCanvas, animate, rasterize, scatter, insideDistance, hilbert, drawTriangles,
} from './core.js';
import { STAGES } from './stages.js';

export { STAGES };

export const STYLES = {
  // Solid, softly lit forms; triangles glide to the next form along swirling paths.
  flow: { sample: 'fill', motion: 'glide', swirl: 0.11, spread: 0.8 },
  // Each form dissolves into a flock that streams around before it settles again.
  murmur: { sample: 'fill', motion: 'flock', spread: 0.5 },
  // Forms drawn in contour lines, like an engraving; the lines unspool into the next form.
  contour: { sample: 'contour', motion: 'glide', swirl: 0.06, spread: 1.2 },
};

const FAINT = 0.22; // density of faint areas (bells, cytoplasm) relative to solid ones

export function mountEvolution(el, options = {}) {
  const o = { style: 'flow', hold: 2.6, move: 2.8, fit: 0.94, gap: 1.45, spare: 'hide', start: 0, still: null, seed: 1, onStage: null, ...options };
  const style = STYLES[o.style] || STYLES.flow;
  const calm = reducedMotion();
  const noise = noise3(o.seed);
  const rand = random(o.seed * 7919);
  const c2 = [0, 0];

  let stages = [], n = 0, scale = 1;
  let X, Y, A, S, C, VX, VY, from, delay;
  let target = o.start, phase = 'move', t = 0, clock = 0, paused = false;

  const surface = mountCanvas(el, build);
  const loop = o.still == null ? animate(el, tick) : null;
  surface.measure();

  function build(view) {
    scale = Math.min(view.width, view.height) * o.fit;
    const ox = (view.width - scale) / 2, oy = (view.height - scale) / 2;
    const size = Math.round(clamp(scale / 1.25, 160, 640)); // mask resolution
    const k = size / 200, px = scale / size;
    const gap = (TRIANGLE_SIZE * o.gap) / px;
    const which = o.still == null ? STAGES.map((_, s) => s) : [o.still];
    const sampled = which.map((s) => sample(STAGES[s], size, k, gap, random(o.seed + s * 101)));
    n = Math.max(...sampled.map((p) => p.x.length));
    const span = Math.max(view.width, view.height);
    const arranged = sampled.map((p, j) => arrange(p, ox, oy, px, span, view, random(o.seed + which[j] * 211)));

    X = new Float32Array(n); Y = new Float32Array(n); A = new Float32Array(n); S = new Float32Array(n);
    C = new Uint8Array(n); VX = new Float32Array(n); VY = new Float32Array(n); delay = new Float32Array(n);

    if (o.still != null) {
      const p = arranged[0];
      X.set(p.x); Y.set(p.y); A.set(p.a); S.set(p.s); C.set(p.c);
      draw();
      return;
    }
    stages = arranged;
    // Start scattered and invisible, then condense into the first form.
    for (let i = 0; i < n; i++) {
      const r = Math.sqrt(rand()) * scale * 0.55, a = rand() * TAU;
      X[i] = view.width / 2 + Math.cos(a) * r;
      Y[i] = view.height / 2 + Math.sin(a) * r;
      A[i] = rand() * TAU;
    }
    begin(target);
    if (calm) settle();
  }

  // Samples one stage into points (in mask pixels) with a colour and a resting angle.
  function sample(stage, size, k, gap, rnd) {
    const dense = rasterize(stage.paint, size, size, k);
    const faint = stage.faint ? rasterize(stage.faint, size, size, k) : null;
    if (faint) for (let i = 0; i < faint.length; i++) if (dense[i]) faint[i] = 0;
    const p = { x: [], y: [], c: [], a: [] };
    const align = stage.align || 0;
    const add = (x, y, c, a) => {
      p.x.push(x); p.y.push(y); p.c.push(c); p.a.push(turn(a, -Math.PI / 2, align));
    };
    if (style.sample === 'contour') {
      for (const [x, y, line, angle] of contour(dense, size, gap, rnd)) {
        add(x, y, clamp(Math.round(1 + line * 0.8 + rnd() - 0.5), 0, EMBER.length - 1), angle);
      }
    } else {
      const union = faint ? dense.map((v, i) => v | faint[i]) : dense;
      const dist = insideDistance(union, size, size);
      const pts = scatter(dense, size, size, gap, rnd, 0.32);
      for (let i = 0; i < pts.length; i += 2) add(pts[i], pts[i + 1], tone(dist, size, pts[i], pts[i + 1], size * 0.06, rnd), rnd() * TAU);
    }
    if (faint) {
      const pts = scatter(faint, size, size, gap / Math.sqrt(FAINT), rnd, 0.4);
      for (let i = 0; i < pts.length; i += 2) add(pts[i], pts[i + 1], 2, rnd() * TAU);
    }
    return p;
  }

  // Pads a stage to n points and sorts them along a Hilbert curve, so particle i
  // always travels between nearby regions of consecutive forms.
  function arrange(p, ox, oy, px, span, view, rnd) {
    const m = p.x.length;
    const tx = new Float32Array(n), ty = new Float32Array(n), ta = new Float32Array(n), ts = new Float32Array(n), tc = new Uint8Array(n);
    for (let j = 0; j < n; j++) {
      if (j < m) {
        tx[j] = ox + p.x[j] * px; ty[j] = oy + p.y[j] * px; ta[j] = p.a[j]; ts[j] = 1; tc[j] = p.c[j];
      } else if (o.spare === 'dust') {
        tx[j] = rnd() * view.width; ty[j] = rnd() * view.height; ta[j] = rnd() * TAU; ts[j] = 0.42; tc[j] = 0;
      } else {
        const q = Math.floor(rnd() * m);
        tx[j] = tx[q] + (rnd() - 0.5) * 3; ty[j] = ty[q] + (rnd() - 0.5) * 3; ta[j] = ta[q]; ts[j] = 0; tc[j] = tc[q];
      }
    }
    const key = new Float64Array(n);
    for (let j = 0; j < n; j++) {
      key[j] = hilbert(clamp(Math.floor((tx[j] / span) * 1024), 0, 1023), clamp(Math.floor((ty[j] / span) * 1024), 0, 1023));
    }
    const order = Array.from({ length: n }, (_, j) => j).sort((a, b) => key[a] - key[b]);
    const out = { x: new Float32Array(n), y: new Float32Array(n), a: new Float32Array(n), s: new Float32Array(n), c: new Uint8Array(n) };
    order.forEach((j, i) => {
      out.x[i] = tx[j]; out.y[i] = ty[j]; out.a[i] = ta[j]; out.s[i] = ts[j]; out.c[i] = tc[j];
    });
    return out;
  }

  // Starts the move from wherever the triangles are now to stage `index`.
  function begin(index) {
    target = index;
    from = { x: X.slice(), y: Y.slice(), a: A.slice(), s: S.slice(), c: C.slice() };
    // The change sweeps across the form, from a side that turns with every stage.
    const dir = index * 2.39996 + 0.7, dx = Math.cos(dir), dy = Math.sin(dir);
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < n; i++) {
      const p = from.x[i] * dx + from.y[i] * dy;
      delay[i] = p;
      if (p < lo) lo = p;
      if (p > hi) hi = p;
    }
    for (let i = 0; i < n; i++) delay[i] = style.spread * (((delay[i] - lo) / (hi - lo || 1)) * 0.8 + rand() * 0.2);
    phase = 'move';
    t = 0;
  }

  // With reduced motion, forms simply appear in place.
  function settle() {
    const B = stages[target];
    X.set(B.x); Y.set(B.y); A.set(B.a); S.set(B.s); C.set(B.c);
    phase = 'hold';
    t = 0;
  }

  function tick(dt) {
    if (!stages.length) return;
    if (!paused) {
      t += dt;
      clock += dt;
      if (phase === 'move' && t >= o.move) {
        phase = 'hold';
        t = 0;
        if (o.onStage) o.onStage(target, STAGES[target].name);
      } else if (phase === 'hold' && t >= (calm ? o.hold + o.move : o.hold)) {
        begin((target + 1) % STAGES.length);
        if (calm) {
          settle();
          if (o.onStage) o.onStage(target, STAGES[target].name);
        }
      }
    }
    if (calm) {
      draw();
      return;
    }
    if (style.motion === 'flock') flock(dt);
    else glide();
    draw();
  }

  function glide() {
    const B = stages[target];
    const moving = phase === 'move';
    const T = moving ? t / o.move : 1;
    const f = 2.6 / scale, z = clock * 0.08;
    const swirl = style.swirl * scale * 0.5, breath = 0.0035 * scale;
    for (let i = 0; i < n; i++) {
      const u = moving ? clamp(T * (1 + style.spread) - delay[i], 0, 1) : 1;
      const e = smooth(u);
      let x = from.x[i] + (B.x[i] - from.x[i]) * e;
      let y = from.y[i] + (B.y[i] - from.y[i]) * e;
      curl(noise, x * f, y * f, z, c2);
      const amp = breath + swirl * Math.sin(Math.PI * u);
      x += c2[0] * amp;
      y += c2[1] * amp;
      orient(i, x - X[i], y - Y[i], u < 0.5 ? from.a[i] : B.a[i]);
      X[i] = x;
      Y[i] = y;
      S[i] = from.s[i] + (B.s[i] - from.s[i]) * e;
      C[i] = u < 0.5 ? from.c[i] : B.c[i];
    }
  }

  function flock(dt) {
    const B = stages[target];
    const { width, height } = surface.view;
    const moving = phase === 'move';
    const T = moving ? t / o.move : 1;
    const f = 1.3 / scale, z = clock * 0.12;
    const steps = 2, h = dt / steps;
    const cx = width / 2, cy = height / 2, reach = scale * 0.5;
    for (let i = 0; i < n; i++) {
      const u = moving ? clamp(T * (1 + style.spread) - delay[i], 0, 1) : 1;
      const free = moving ? smooth(clamp(u / 0.15, 0, 1)) * (1 - smooth(clamp((u - 0.45) / 0.35, 0, 1))) : 0;
      const tx = u > 0 ? B.x[i] : from.x[i], ty = u > 0 ? B.y[i] : from.y[i];
      const K = 70 + (2.5 - 70) * free, damp = 2 * Math.sqrt(70) * (1 - free) + 1.4 * free;
      curl(noise, X[i] * f, Y[i] * f, z, c2);
      const F = (0.06 + 0.24 * free) * scale;
      const x0 = X[i], y0 = Y[i];
      for (let s = 0; s < steps; s++) {
        // a soft wall keeps the flock inside the frame
        const dx = X[i] - cx, dy = Y[i] - cy, d = Math.hypot(dx, dy), over = Math.max(0, d - reach) * 30 / (d || 1);
        VX[i] += (K * (tx - X[i]) - damp * VX[i] + c2[0] * F - dx * over) * h;
        VY[i] += (K * (ty - Y[i]) - damp * VY[i] + c2[1] * F - dy * over) * h;
        X[i] += VX[i] * h;
        Y[i] += VY[i] * h;
      }
      orient(i, X[i] - x0, Y[i] - y0, u < 0.5 ? from.a[i] : B.a[i]);
      const e = smooth(u);
      S[i] = from.s[i] + (B.s[i] - from.s[i]) * e;
      C[i] = u < 0.5 ? from.c[i] : B.c[i];
    }
  }

  // Moving triangles point where they are going; resting ones turn to their stage's angle.
  function orient(i, vx, vy, rest) {
    const speed = vx * vx + vy * vy;
    if (speed > 0.02) A[i] = turn(A[i], Math.atan2(vy, vx), Math.min(0.35, speed * 0.5));
    else A[i] = turn(A[i], rest, 0.06);
  }

  function draw() {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    drawTriangles(ctx, n, X, Y, A, S, C, EMBER);
  }

  return {
    get stage() {
      return target;
    },
    go(index) {
      if (!stages.length) return;
      begin(((index % STAGES.length) + STAGES.length) % STAGES.length);
      if (calm) settle();
    },
    pause() {
      paused = true;
    },
    play() {
      paused = false;
    },
    // Runs the animation forward by `seconds` at once (for previews and tests).
    advance(seconds) {
      for (let s = 0; s < seconds; s += 1 / 60) tick(1 / 60);
    },
    destroy() {
      if (loop) loop.destroy();
      surface.destroy();
    },
  };
}

// Light from the upper left on a softly bevelled version of the shape.
function tone(dist, size, x, y, bevel, rand) {
  const ix = clamp(Math.round(x), 2, size - 3), iy = clamp(Math.round(y), 2, size - 3), i = iy * size + ix;
  const h = (j) => {
    const t = Math.min(dist[j], bevel) / bevel;
    return Math.sqrt(1 - (1 - t) * (1 - t));
  };
  const gx = ((h(i + 2) - h(i - 2)) / 4) * bevel, gy = ((h(i + 2 * size) - h(i - 2 * size)) / 4) * bevel;
  const lit = (0.55 * gx + 0.62 * gy + 0.56) / Math.hypot(gx, gy, 1);
  return clamp(Math.floor(((lit + 0.2) / 1.2) * EMBER.length + (rand() - 0.5) * 1.2), 0, EMBER.length - 1);
}

// Points along the shape's inner contour lines, as [x, y, line, angle along the line].
function contour(mask, size, gap, rand) {
  const dist = blur(insideDistance(mask, size, size), mask, size);
  const L = gap * 1.2;
  const cand = [];
  for (let y = 2; y < size - 2; y++) {
    for (let x = 2; x < size - 2; x++) {
      const i = y * size + x, d = dist[i];
      if (!mask[i] || d < 0.3) continue;
      const f = d / L - 0.5, line = Math.round(f);
      if (line < 0 || Math.abs(f - line) * L > 0.55) continue;
      const angle = Math.atan2(dist[i + 2 * size] - dist[i - 2 * size], dist[i + 2] - dist[i - 2]) + Math.PI / 2;
      cand.push([x + rand() - 0.5, y + rand() - 0.5, line, angle]);
    }
  }
  for (let i = cand.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [cand[i], cand[j]] = [cand[j], cand[i]];
  }
  // Keep about one point every `gap` along each line.
  const r = gap * 0.92, cols = Math.ceil(size / r) + 1, grid = new Map(), out = [];
  for (const p of cand) {
    const gx = Math.floor(p[0] / r), gy = Math.floor(p[1] / r);
    let free = true;
    for (let yy = gy - 1; yy <= gy + 1 && free; yy++) {
      for (let xx = gx - 1; xx <= gx + 1 && free; xx++) {
        const near = grid.get(yy * cols + xx);
        if (near) for (const q of near) if ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < r * r) free = false;
      }
    }
    if (!free) continue;
    out.push(p);
    const cell = gy * cols + gx;
    if (!grid.has(cell)) grid.set(cell, []);
    grid.get(cell).push(p);
  }
  return out;
}

// Two passes of a 3 × 3 box blur inside the mask, so contour lines curve instead of stepping.
function blur(src, mask, size) {
  let a = src, b = new Float32Array(src.length);
  for (let pass = 0; pass < 2; pass++) {
    for (let y = 1; y < size - 1; y++) {
      for (let x = 1; x < size - 1; x++) {
        const i = y * size + x;
        b[i] = mask[i] ? (a[i - size - 1] + a[i - size] + a[i - size + 1] + a[i - 1] + a[i] + a[i + 1] + a[i + size - 1] + a[i + size] + a[i + size + 1]) / 9 : 0;
      }
    }
    [a, b] = [b, a];
  }
  return a;
}
