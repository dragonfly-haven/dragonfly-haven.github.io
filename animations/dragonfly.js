// A deep black dragonfly made of round shapes that turns into a sharp-edged
// dragonfly built from the same tiny triangles as the evolution animation.
//
//   import { mountDragonfly } from './animations/dragonfly.js';
//   mountDragonfly(document.getElementById('dragonfly'), { style: 'crystallise' });

import {
  TRIANGLE_SIZE, INK, TAU, random, noise3, curl, clamp, smooth, turn, reducedMotion,
  mountCanvas, animate, rasterize, tiling, insideDistance, hilbert,
} from './core.js';

export const DRAGONFLY_STYLES = {
  // Round shapes crack into triangles in a wave from the body outwards. Hovering softens it again.
  crystallise: { order: 'centre', swirl: 0, sharpen: false, loop: false },
  // Circles burst into triangles that swirl into place, then melt back, over and over.
  shatter: { order: 'random', swirl: 0.12, sharpen: false, loop: true },
  // Circles break into round dots that drift into place and then sharpen into triangles.
  sharpen: { order: 'centre', swirl: 0.03, sharpen: true, loop: true },
};

// Geometry, in units, head up. Only the left wings are drawn; the right ones are mirrored.
const CENTRE = [100, 88];
const ROOTS = [null, [93, 52], [107, 52], [93, 63], [107, 63]]; // where each wing pivots
const FORE = [[93, 48], [56, 42], [8, 43.5], [12, 50], [50, 57], [92, 56.5]];
const HIND = [[93, 59.5], [58, 61], [12, 65.5], [16, 73], [46, 80.5], [76, 77.5], [93, 67.5]];
const FORE_VEIN = [[93, 52], [42, 49], [11, 46.5]];
const HIND_VEIN = [[93, 63], [40, 67.5], [14, 69]];
const FORE_MARK = [[20, 43.1], [28, 42.7], [27.5, 45.4], [19.5, 45.8]];
const HIND_MARK = [[22, 64.6], [30, 64], [29.6, 66.8], [21.6, 67.4]];
const EYE = [[82.5, 22], [89, 15.5], [98, 17.5], [100, 26], [96.5, 33.5], [86, 32]];

const mirror = (pts) => pts.map(([x, y]) => [200 - x, y]);
const same = (pts) => pts;

function polygon(g, pts) {
  g.beginPath();
  pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
  g.closePath();
  g.fill();
}

function polyline(g, pts, w, closed = false) {
  g.lineWidth = w;
  g.beginPath();
  pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
  if (closed) g.closePath();
  g.stroke();
}

// The abdomen as one tapering blade, notched where its ten segments meet.
function abdomen() {
  const right = [];
  for (let j = 0; j < 10; j++) {
    const y = 71 + j * 8.8, w = 4.9 - j * 0.2;
    right.push([100 + w - 1.4, y], [100 + w + 0.3, y + 3]);
  }
  right.push([101.6, 159], [100, 160]);
  return right.concat(mirror(right).reverse());
}

// The sharp dragonfly, by part. `dense` areas are tiled solid, `sparse` ones
// (wing membranes) thinly; lines are kept at least about a lattice cell wide.
function wing(outline, vein, mark, flip) {
  return {
    dense(g, cell) {
      polyline(g, flip(outline), Math.max(1.6, cell * 0.85), true);
      polyline(g, flip(vein), Math.max(1.4, cell * 0.75));
      polygon(g, flip(mark));
    },
    sparse(g) {
      polygon(g, flip(outline));
    },
  };
}

const SHARP = [
  { group: 'eyeL', limb: 0, dense: (g) => polygon(g, EYE) },
  { group: 'eyeR', limb: 0, dense: (g) => polygon(g, mirror(EYE)) },
  { group: 'head', limb: 0, dense: (g) => polygon(g, [[100, 32], [105.5, 37.5], [100, 43], [94.5, 37.5]]) },
  { group: 'thorax', limb: 0, dense: (g) => polygon(g, [[100, 41], [109, 47], [109, 62], [100, 70], [91, 62], [91, 47]]) },
  {
    group: 'abdomen',
    limb: 0,
    dense(g) {
      polygon(g, abdomen());
      polygon(g, [[98.4, 156], [100, 158], [96, 166]]);
      polygon(g, [[101.6, 156], [100, 158], [104, 166]]);
    },
  },
  { group: 'lf', limb: 1, ...wing(FORE, FORE_VEIN, FORE_MARK, same) },
  { group: 'rf', limb: 2, ...wing(FORE, FORE_VEIN, FORE_MARK, mirror) },
  { group: 'lh', limb: 3, ...wing(HIND, HIND_VEIN, HIND_MARK, same) },
  { group: 'rh', limb: 4, ...wing(HIND, HIND_VEIN, HIND_MARK, mirror) },
];

// The round dragonfly: beads and discs for the body, wings packed with ring-shaped cells.
function roundShapes() {
  const out = [];
  const disc = (x, y, r, group) => out.push({ x, y, r, ring: false, group, limb: 0 });
  disc(90.5, 27, 9.8, 'eyeL');
  disc(109.5, 27, 9.8, 'eyeR');
  disc(100, 38.5, 6, 'head');
  disc(100, 50, 9.5, 'thorax');
  disc(100, 62.5, 8.2, 'thorax');
  for (let j = 0; j < 10; j++) disc(100, 74 + j * 8.8, 4.6 - j * 0.17, 'abdomen');
  disc(98.2, 160, 1.5, 'abdomen');
  disc(101.8, 160, 1.5, 'abdomen');
  const rand = random(9);
  const fore = pack((g) => {
    g.beginPath();
    g.ellipse(52, 49, 44, 7.8, -0.05, 0, TAU);
    g.fill();
  }, rand);
  const hind = pack((g) => {
    g.beginPath();
    g.ellipse(55, 67, 42, 9, 0.07, 0, TAU);
    g.fill();
    g.beginPath();
    g.ellipse(80, 66, 15, 10, 0.15, 0, TAU);
    g.fill();
  }, rand);
  for (const c of fore) out.push({ ...c, ring: true, group: 'lf', limb: 1 }, { ...c, x: 200 - c.x, ring: true, group: 'rf', limb: 2 });
  for (const c of hind) out.push({ ...c, ring: true, group: 'lh', limb: 3 }, { ...c, x: 200 - c.x, ring: true, group: 'rh', limb: 4 });
  return out;
}

// Packs circles into a shape, biggest first, like the cells of a wing.
function pack(paint, rand) {
  const k = 3, w = 600, h = 510;
  const mask = rasterize(paint, w, h, k);
  const dist = insideDistance(mask, w, h);
  const inside = [];
  for (let i = 0; i < mask.length; i++) if (mask[i]) inside.push(i);
  const circles = [];
  for (let misses = 0; misses < 40;) {
    let best = null;
    for (let c = 0; c < 40; c++) {
      const i = inside[Math.floor(rand() * inside.length)];
      const x = ((i % w) + 0.5) / k, y = (Math.floor(i / w) + 0.5) / k;
      let r = Math.min(dist[i] / k - 0.5, 4.4);
      for (const q of circles) {
        r = Math.min(r, Math.hypot(q.x - x, q.y - y) - q.r - 0.7);
        if (r < 1.5) break;
      }
      if (r >= 1.5 && (!best || r > best.r)) best = { x, y, r };
    }
    if (best) {
      circles.push(best);
      misses = 0;
    } else misses++;
  }
  return circles;
}

export function mountDragonfly(el, options = {}) {
  const o = { style: 'crystallise', rotate: -0.6, fit: 0.94, duration: 2.6, delay: 0.9, hover: true, loop: null, seed: 3, ...options };
  const style = DRAGONFLY_STYLES[o.style] || DRAGONFLY_STYLES.crystallise;
  const loops = o.loop ?? style.loop;
  const calm = reducedMotion();
  const noise = noise3(o.seed);
  const rand = random(o.seed);
  const circles = roundShapes();
  const c2 = [0, 0], at = [0, 0];

  let tri = null, n = 0, scale = 1, cx = 0, cy = 0;
  // P runs from 0 (round) to 1 (sharp) and heads for `goal` once `wait` runs out.
  let P = calm ? 1 : 0, goal = 1, wait = o.delay, clock = 0, hovered = false;

  const cos = Math.cos(o.rotate), sin = Math.sin(o.rotate);
  const flap = [0, 0, 0, 0, 0];

  const surface = mountCanvas(el, build);
  const loop = animate(el, tick);
  surface.measure();

  if (o.hover && !calm) {
    el.addEventListener('pointerenter', () => (hovered = true));
    el.addEventListener('pointerleave', () => {
      hovered = false;
      goal = 1;
      wait = 0.2;
    });
  }

  function build(view) {
    // Fit the turned dragonfly into the element.
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const extend = (x, y) => {
      const dx = x - CENTRE[0], dy = y - CENTRE[1];
      const rx = dx * cos - dy * sin, ry = dx * sin + dy * cos;
      x0 = Math.min(x0, rx); x1 = Math.max(x1, rx); y0 = Math.min(y0, ry); y1 = Math.max(y1, ry);
    };
    for (const pts of [FORE, HIND, mirror(FORE), mirror(HIND), EYE, mirror(EYE), [[100, 165]]]) for (const [x, y] of pts) extend(x, y);
    for (const c of circles) for (let a = 0; a < TAU; a += TAU / 8) extend(c.x + Math.cos(a) * c.r, c.y + Math.sin(a) * c.r);
    scale = Math.min(view.width / (x1 - x0), view.height / (y1 - y0)) * o.fit;
    cx = view.width / 2 - ((x0 + x1) / 2) * scale;
    cy = view.height / 2 - ((y0 + y1) / 2) * scale;
    sampleSharp();
  }

  // Tiles the sharp dragonfly with triangles and gives each one a starting
  // place inside one of the round shapes of the same body part.
  function sampleSharp() {
    const cell = (TRIANGLE_SIZE * 1.6) / scale; // lattice cell side, in units
    const k = 10 / cell; // mask pixels per unit
    const w = Math.ceil(200 * k), h = Math.ceil(170 * k);
    const seen = new Set();
    const items = [];
    for (const part of SHARP) {
      const dense = rasterize((g) => part.dense(g, cell), w, h, k);
      const sparse = part.sparse ? rasterize(part.sparse, w, h, k) : null;
      if (sparse) for (let i = 0; i < sparse.length; i++) if (dense[i]) sparse[i] = 0;
      const add = (pts) => {
        for (let i = 0; i < pts.length; i += 3) {
          const key = `${Math.round(pts[i] * 10)},${Math.round(pts[i + 1] * 10)}`;
          if (seen.has(key)) continue;
          seen.add(key);
          items.push({ x: pts[i] / k, y: pts[i + 1] / k, a: pts[i + 2], group: part.group, limb: part.limb });
        }
      };
      add(tiling(dense, w, h, cell * k));
      if (sparse) add(tiling(sparse, w, h, cell * k, (r, c) => (r + 2 * c) % 3 === 0));
    }

    // Share each part's triangles among its round shapes by size, then pair
    // starting slots with places along a Hilbert curve so nothing crosses far.
    const slots = [];
    for (const group of new Set(items.map((t) => t.group))) {
      const mine = items.filter((t) => t.group === group);
      const owners = circles.filter((c) => c.group === group);
      const weight = owners.map((c) => (c.ring ? c.r * 2.2 : c.r * c.r));
      const total = weight.reduce((a, b) => a + b, 0);
      const counts = weight.map((wt) => Math.floor((wt / total) * mine.length));
      let left = mine.length - counts.reduce((a, b) => a + b, 0);
      for (const i of weight.map((wt, i) => [wt, i]).sort((a, b) => b[0] - a[0]).map(([, i]) => i)) {
        if (left-- <= 0) break;
        counts[i]++;
      }
      const start = [];
      owners.forEach((c, i) => {
        const spin = rand() * TAU;
        for (let s = 0; s < counts[i]; s++) {
          if (c.ring) start.push([c.x + Math.cos(spin + (s * TAU) / counts[i]) * c.r, c.y + Math.sin(spin + (s * TAU) / counts[i]) * c.r, c]);
          else {
            const rr = c.r * 0.82 * Math.sqrt((s + 0.5) / counts[i]), a = spin + s * 2.39996;
            start.push([c.x + Math.cos(a) * rr, c.y + Math.sin(a) * rr, c]);
          }
        }
      });
      const key = ([x, y]) => hilbert(clamp(Math.floor((x / 200) * 1024), 0, 1023), clamp(Math.floor((y / 200) * 1024), 0, 1023));
      start.sort((a, b) => key(a) - key(b));
      mine.sort((a, b) => key([a.x, a.y]) - key([b.x, b.y]));
      mine.forEach((t, i) => slots.push({ ...t, sx: start[i][0], sy: start[i][1], owner: start[i][2] }));
    }

    // Order of change: from the body outwards, or at random.
    const reach = Math.max(...circles.map((c) => Math.hypot(c.x - 100, c.y - 56)));
    for (const c of circles) {
      c.delay = style.order === 'centre' ? (Math.hypot(c.x - 100, c.y - 56) / reach) * 0.9 + rand() * 0.1 : rand();
    }
    n = slots.length;
    tri = {
      sx: Float32Array.from(slots, (t) => t.sx), sy: Float32Array.from(slots, (t) => t.sy),
      tx: Float32Array.from(slots, (t) => t.x), ty: Float32Array.from(slots, (t) => t.y),
      a0: Float32Array.from(slots, () => rand() * TAU), a1: Float32Array.from(slots, (t) => t.a),
      limb: Uint8Array.from(slots, (t) => t.limb),
      delay: Float32Array.from(slots, (t) => t.owner.delay),
      lag: Float32Array.from(slots, () => rand() * 0.15),
    };
  }

  function tick(dt) {
    if (!tri) return;
    clock += dt;
    if (!calm) {
      if (hovered) {
        goal = 0;
        wait = 0;
      } else if (wait > 0) wait -= dt;
      else if (P === goal) {
        if (goal === 0) {
          goal = 1;
          wait = 1.6;
        } else if (loops) {
          goal = 0;
          wait = 6;
        }
      }
      if (wait <= 0 && P !== goal) {
        const step = dt / o.duration;
        P = goal > P ? Math.min(goal, P + step) : Math.max(goal, P - step);
      }
      // The wings shiver a little, fore and hind out of step.
      const beat = Math.sin(clock * TAU * 0.6) * 0.03, hindBeat = Math.sin(clock * TAU * 0.6 + 0.9) * 0.03;
      flap[1] = beat; flap[2] = -beat; flap[3] = hindBeat; flap[4] = -hindBeat;
    }
    draw();
  }

  // From dragonfly units to canvas pixels, with each wing turned about its root.
  function place(x, y, limb) {
    if (limb) {
      const [rx, ry] = ROOTS[limb], a = flap[limb], ca = Math.cos(a), sa = Math.sin(a);
      const dx = x - rx, dy = y - ry;
      x = rx + dx * ca - dy * sa;
      y = ry + dx * sa + dy * ca;
    }
    const dx = x - CENTRE[0], dy = y - CENTRE[1];
    at[0] = cx + (dx * cos - dy * sin) * scale;
    at[1] = cy + (dx * sin + dy * cos) * scale;
    return at;
  }

  function draw() {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = INK;
    const span = 1.15; // per-shape stagger, as a share of the whole change

    // Round shapes, shrinking or thinning away as they break up.
    ctx.beginPath();
    for (const c of circles) {
      const u = clamp(P * (1 + span) - c.delay * span, 0, 1);
      const [x, y] = place(c.x, c.y, c.limb);
      if (c.ring) {
        const w = Math.min(0.9, c.r * scale * 0.4) * (1 - smooth(clamp(u / 0.35, 0, 1)));
        if (w < 0.05) continue;
        const r = c.r * scale * (1 + 0.12 * smooth(clamp(u / 0.35, 0, 1)));
        ctx.moveTo(x + r + w / 2, y);
        ctx.arc(x, y, r + w / 2, 0, TAU);
        ctx.moveTo(x + r - w / 2, y);
        ctx.arc(x, y, Math.max(0, r - w / 2), 0, TAU, true);
      } else {
        const r = c.r * scale * (1 - smooth(clamp(u / 0.45, 0, 1)));
        if (r < 0.1) continue;
        ctx.moveTo(x + r, y);
        ctx.arc(x, y, r, 0, TAU);
      }
    }
    ctx.fill();

    // Triangles, leaving their round shape and settling into the sharp dragonfly.
    const R = TRIANGLE_SIZE / Math.sqrt(3);
    const f = 3 / 200, z = clock * 0.2;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const u = clamp(P * (1 + span + 0.15) - tri.delay[i] * span - tri.lag[i], 0, 1);
      const size = smooth(clamp(u / 0.3, 0, 1));
      if (size < 0.03) continue;
      const m = smooth(clamp((u - 0.1) / 0.9, 0, 1));
      let x = tri.sx[i] + (tri.tx[i] - tri.sx[i]) * m;
      let y = tri.sy[i] + (tri.ty[i] - tri.sy[i]) * m;
      if (style.swirl) {
        curl(noise, x * f, y * f, z, c2);
        const amp = style.swirl * 200 * Math.sin(Math.PI * m) * 0.5;
        x += c2[0] * amp;
        y += c2[1] * amp;
      }
      const [px, py] = place(x, y, tri.limb[i]);
      const a = turn(tri.a0[i], tri.a1[i], m) + o.rotate + flap[tri.limb[i]];
      const r = R * size;
      const round = style.sharpen ? 1 - smooth(clamp((u - 0.55) / 0.45, 0, 1)) : 0;
      triangle(ctx, px, py, a, r, round);
    }
    ctx.fill();
  }

  return {
    sharpen() {
      goal = 1;
      wait = 0;
    },
    soften() {
      goal = 0;
      wait = 0;
    },
    // Runs the animation forward by `seconds` at once (for previews and tests).
    advance(seconds) {
      for (let s = 0; s < seconds; s += 1 / 60) tick(1 / 60);
    },
    destroy() {
      loop.destroy();
      surface.destroy();
    },
  };
}

// An equilateral triangle (circumradius r) whose corners can be rounded all the
// way to its inscribed circle (round = 1).
function triangle(ctx, x, y, a, r, round) {
  const v = [0, 1, 2].map((k) => [x + Math.cos(a + (k * TAU) / 3) * r, y + Math.sin(a + (k * TAU) / 3) * r]);
  if (round < 0.02) {
    ctx.moveTo(v[0][0], v[0][1]);
    ctx.lineTo(v[1][0], v[1][1]);
    ctx.lineTo(v[2][0], v[2][1]);
    ctx.closePath();
    return;
  }
  const rho = Math.min(round, 0.98) * (r / 2);
  ctx.moveTo((v[2][0] + v[0][0]) / 2, (v[2][1] + v[0][1]) / 2);
  ctx.arcTo(v[0][0], v[0][1], v[1][0], v[1][1], rho);
  ctx.arcTo(v[1][0], v[1][1], v[2][0], v[2][1], rho);
  ctx.arcTo(v[2][0], v[2][1], v[0][0], v[0][1], rho);
  ctx.closePath();
}
