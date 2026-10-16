// A deep black dragonfly built from the same tiny triangles as the evolution
// animation. It is modelled in 3D: the triangles tile its rounded body and its
// veined wings, catch the light as it hovers, and start out as glossy round
// shapes that crystallise into the sharp-edged dragonfly.
//
//   import { mountDragonfly } from './animations/dragonfly.js';
//   mountDragonfly(document.getElementById('dragonfly'), { style: 'crystallise' });

import { triangleSize, TAU, random, noise3, curl, clamp, smooth, reducedMotion, mountCanvas, animate } from './core.js';

export const DRAGONFLY_STYLES = {
  // Round shapes crack into triangles in a wave from the body outwards. Hovering softens it again.
  crystallise: { order: 'centre', swirl: 0, sharpen: false, loop: false },
  // Round shapes burst into triangles that swirl into place, then melt back, over and over.
  shatter: { order: 'random', swirl: 0.12, sharpen: false, loop: true },
  // Round shapes break into round dots that drift into place and then sharpen into triangles.
  sharpen: { order: 'centre', swirl: 0.03, sharpen: true, loop: true },
};

const SQRT3 = Math.sqrt(3);
const PITCH = 1.05; // spacing of the triangle tiling, in triangle sides; the rest shows as fine seams
const DISTANCE = 400; // camera distance in model units, for a gentle perspective
// Towards the light and the half-way vector, in camera space (x right, y up, z to the viewer).
const LIGHT = unit([-0.42, 0.62, 0.66]);
const HALF = unit([LIGHT[0], LIGHT[1], LIGHT[2] + 1]);

// Deep warm blacks that rise to graphite where a facet catches the light.
const TONES = ['#060504', '#0a0807', '#0f0d0b', '#15120f', '#1c1814', '#24201b', '#2e2822', '#39322b', '#463e35', '#564d43', '#6c6256', '#8a7f72', '#b0a598'];
// The wing membrane, a faint warm film.
const FILM = [0.06, 0.09, 0.13, 0.18, 0.24, 0.31, 0.39, 0.48].map((alpha) => `rgba(20,16,12,${alpha})`);
const PALETTE = TONES.concat(FILM);
const SEAM = '#2b2620'; // between the shell's triangles
const SHELL = 0, VEIN = 1, MEMBRANE = 2, EYE = 3; // kinds of triangle

// ---------------------------------------------------------------------------
// The model. Units: about 100 from head to tail. +y points to the head, +x to
// the dragonfly's right and +z out of its back; the thorax sits at the origin.

const SEGMENTS = [2.4, 6.2, 8.4, 8.4, 8.4, 8.4, 8.0, 7.0, 5.4, 3.8]; // abdomen, S1 to S10
const GIRTH = [3.4, 3.35, 2.25, 1.95, 2.0, 2.05, 2.2, 2.4, 2.4, 2.0]; // radius at each segment's middle
const ABDOMEN_START = -5.5;
const ABDOMEN = SEGMENTS.reduce((a, b) => a + b, 0);
const MIDDLES = [], JOINTS = [];
for (let y = 0, k = 0; k < SEGMENTS.length; y += SEGMENTS[k++]) {
  MIDDLES.push(y + SEGMENTS[k] / 2);
  if (k) JOINTS.push(y);
}

const spine = (u) => [0, ABDOMEN_START - u * ABDOMEN, 0.5 - 2.4 * u * u];

function girth(u) {
  const d = u * ABDOMEN;
  let r = GIRTH[0];
  if (d >= MIDDLES[9]) r = GIRTH[9];
  else if (d > MIDDLES[0]) {
    let k = 0;
    while (MIDDLES[k + 1] < d) k++;
    r = GIRTH[k] + (GIRTH[k + 1] - GIRTH[k]) * smooth((d - MIDDLES[k]) / (MIDDLES[k + 1] - MIDDLES[k]));
  }
  let near = Infinity;
  for (const j of JOINTS) near = Math.min(near, Math.abs(d - j));
  r *= 1 - 0.13 * Math.exp(-((near / 0.75) ** 2)); // pinched where segments meet
  const end = ABDOMEN - d;
  if (end < 1.6) r *= Math.sqrt(Math.max(0, 1 - (1 - end / 1.6) ** 2)); // rounded tip
  return r;
}

// Body parts, drawn in `layer` order from the back (0) to the front.
function bodyParts() {
  const eye = (x) => ({ group: x < 0 ? 'eyeL' : 'eyeR', layer: 5, kind: EYE, surface: ellipsoid([x * 3.0, 13.9, 2.2], [x * 0.8, 0.3, 0.52], [0, 0, 1], [5.2, 5.2, 4.9]) });
  return [
    { group: 'abdomen', layer: 0, surface: tube(spine, girth, 0.94) },
    { group: 'thorax', layer: 3, surface: ellipsoid([0, -0.4, 0.6], [0, 1, 0], [1, 0, 0], [8.4, 6.0, 5.4]) },
    { group: 'thorax', layer: 3, surface: ellipsoid([0, 8.9, 0.9], [0, 1, 0], [1, 0, 0], [1.9, 3.0, 2.3]) },
    { group: 'face', layer: 4, surface: ellipsoid([0, 18.3, 0.2], [0, 1, 0], [1, 0, 0], [2.4, 3.9, 3.0]) },
    eye(-1),
    eye(1),
  ];
}

// The tail's claspers, as thin lines of triangles.
function claspers() {
  const end = spine(1);
  return [-1, 1].map((x) => [[x * 0.45, end[1] + 0.4, end[2] + 0.2], [x * 0.9, end[1] - 2.4, end[2] + 0.35], [x * 1.4, end[1] - 5.2, end[2] + 0.4]]);
}

// The round dragonfly: glossy beads and spheres for the body.
function spheres() {
  const out = [];
  const add = (c, r, group, layer) => out.push({ c, r, group, layer });
  add([-3.0, 13.9, 2.2], 5.1, 'eyeL', 5);
  add([3.0, 13.9, 2.2], 5.1, 'eyeR', 5);
  add([0, 17.4, -0.3], 2.7, 'face', 4);
  add([0, 8.9, 0.9], 2.4, 'thorax', 3);
  add([0, 3.4, 0.8], 5.0, 'thorax', 3);
  add([0, -3.6, 0.8], 5.2, 'thorax', 3);
  add([-3.4, -0.2, 0.4], 3.4, 'thorax', 3);
  add([3.4, -0.2, 0.4], 3.4, 'thorax', 3);
  // A string of beads down the abdomen.
  for (let d = 2.6; d < ABDOMEN - 0.5;) {
    const u = d / ABDOMEN, r = girth(u) * 1.08 + 0.15;
    add(spine(u), r, 'abdomen', 0);
    d += Math.max(1.4, r * 1.55);
  }
  for (const line of claspers()) add(line[1], 0.85, 'abdomen', 0);
  return out;
}

// Wings, in fractions of their length (s, root to tip) and chord (c, from the
// leading edge back). Veins of rank 0 always show; higher ranks only once the
// wing is wide enough in triangles to hold them.
const RADIUS = [[0, 0.2], [0.08, 0.1], [0.25, 0.075], [0.47, 0.085], [0.7, 0.08], [0.8, 0.085], [0.9, 0.11], [0.96, 0.16], [0.99, 0.22]];
const SECTOR = [[0.02, 0.27], [0.12, 0.2], [0.3, 0.19], [0.5, 0.2], [0.7, 0.23], [0.85, 0.27], [0.95, 0.31], [0.995, 0.34]];
const SUBCOSTA = [[0, 0.18], [0.12, 0.05], [0.3, 0.035], [0.47, 0.012]];
const R45 = [[0.22, 0.2], [0.36, 0.3], [0.5, 0.42], [0.62, 0.6], [0.72, 0.8], [0.77, 0.98]];
const IR2 = [[0.36, 0.21], [0.52, 0.29], [0.66, 0.38], [0.78, 0.5], [0.88, 0.64], [0.93, 0.74]];

const FOREWING = {
  root: [2.6, 2.4, 4.0], length: 65, chord: 13, sweep: 0.1, dihedral: 0.09,
  lead: [[0, 0.16], [0.03, 0.07], [0.1, 0.015], [0.25, 0], [0.47, 0.012], [0.65, 0.006], [0.82, 0.012], [0.91, 0.032], [0.965, 0.08], [0.993, 0.16], [1, 0.25]],
  trail: [[1, 0.25], [0.994, 0.36], [0.97, 0.5], [0.92, 0.64], [0.84, 0.77], [0.72, 0.88], [0.56, 0.96], [0.4, 0.99], [0.26, 0.94], [0.15, 0.8], [0.08, 0.6], [0.035, 0.42], [0, 0.3]],
  veins: [
    { rank: 0, long: true, pts: SECTOR },
    { rank: 0, pts: [[0.47, 0.012], [0.47, 0.2]] }, // nodus
    { rank: 1, long: true, pts: RADIUS },
    { rank: 1, long: true, pts: R45 },
    { rank: 1, long: true, pts: [[0.03, 0.36], [0.12, 0.4], [0.22, 0.5], [0.32, 0.66], [0.4, 0.9], [0.42, 1.02]] }, // media
    { rank: 2, long: true, pts: IR2 },
    { rank: 2, long: true, pts: [[0.04, 0.46], [0.1, 0.56], [0.16, 0.72], [0.22, 0.9], [0.25, 1.0]] }, // cubitus
    { rank: 2, pts: [[0.065, 0.2], [0.07, 0.52]] }, // arculus
    { rank: 2, pts: [[0.11, 0.42], [0.2, 0.47], [0.14, 0.62], [0.11, 0.42]] }, // discoidal triangle
    { rank: 3, long: true, pts: SUBCOSTA },
    { rank: 3, long: true, pts: [[0.3, 0.55], [0.4, 0.7], [0.5, 0.86], [0.55, 0.99]] },
  ],
  stigma: [[0.8, 0.012], [0.875, 0.02], [0.872, 0.095], [0.797, 0.088]],
};

const HINDWING = {
  root: [2.6, -3.8, 3.8], length: 63, chord: 12.6, sweep: -0.09, dihedral: 0.08,
  lead: [[0, 0.14], [0.03, 0.06], [0.1, 0.012], [0.25, 0], [0.45, 0.012], [0.65, 0.006], [0.82, 0.012], [0.91, 0.032], [0.965, 0.08], [0.993, 0.16], [1, 0.25]],
  trail: [[1, 0.25], [0.994, 0.36], [0.97, 0.49], [0.92, 0.62], [0.84, 0.73], [0.72, 0.83], [0.58, 0.9], [0.46, 0.95], [0.36, 1.03], [0.26, 1.16], [0.17, 1.28], [0.1, 1.33], [0.05, 1.26], [0.02, 1.0], [0, 0.5]],
  veins: [
    { rank: 0, long: true, pts: SECTOR },
    { rank: 0, pts: [[0.45, 0.012], [0.45, 0.2]] }, // nodus
    { rank: 1, long: true, pts: RADIUS },
    { rank: 1, long: true, pts: R45 },
    { rank: 1, long: true, pts: [[0.03, 0.34], [0.14, 0.4], [0.26, 0.52], [0.38, 0.7], [0.46, 0.92], [0.49, 1.02]] }, // media
    { rank: 1, long: true, pts: [[0.04, 0.48], [0.1, 0.62], [0.17, 0.82], [0.24, 1.0], [0.3, 1.14]] }, // cubitus
    { rank: 2, long: true, pts: IR2 },
    { rank: 2, long: true, pts: [[0.02, 0.6], [0.05, 0.8], [0.09, 1.05], [0.12, 1.34]] }, // anal vein
    { rank: 2, pts: [[0.065, 0.2], [0.07, 0.5]] }, // arculus
    { rank: 3, pts: [[0.06, 0.72], [0.13, 0.78], [0.18, 0.92], [0.12, 1.02], [0.07, 0.95], [0.06, 0.72]] }, // anal loop
    { rank: 3, long: true, pts: SUBCOSTA },
  ],
  stigma: [[0.8, 0.012], [0.87, 0.02], [0.868, 0.09], [0.797, 0.084]],
};

// The four wings: which spec, which side, which rig (for flapping) and layer.
const WINGS = [
  { spec: HINDWING, side: -1, group: 'lh', layer: 1 },
  { spec: HINDWING, side: 1, group: 'rh', layer: 1 },
  { spec: FOREWING, side: -1, group: 'lf', layer: 2 },
  { spec: FOREWING, side: 1, group: 'rf', layer: 2 },
];

function wingFrame({ spec, side }) {
  const { sweep, dihedral } = spec;
  const S = [side * Math.cos(sweep) * Math.cos(dihedral), Math.sin(sweep) * Math.cos(dihedral), Math.sin(dihedral)];
  const C = [side * Math.sin(sweep), -Math.cos(sweep), 0];
  let N = cross(S, C);
  if (N[2] < 0) N = scaled(N, -1);
  const root = [side * spec.root[0], spec.root[1], spec.root[2]];
  return { root, S, C, N, hinge: unit(cross(S, N)) };
}

// ---------------------------------------------------------------------------

export function mountDragonfly(el, options = {}) {
  const o = {
    style: 'crystallise', rotate: -0.7, tilt: 0.42, fit: 0.97, duration: 2.6, delay: 0.9,
    hover: true, loop: null, seed: 3, motion: 1, film: 0, cell: 3.2, ...options,
  };
  const style = DRAGONFLY_STYLES[o.style] || DRAGONFLY_STYLES.crystallise;
  const loops = o.loop ?? style.loop;
  const calm = reducedMotion();
  const noise = noise3(o.seed);
  const frames = WINGS.map(wingFrame);
  const parts = bodyParts();
  const c2 = [0, 0];

  let tri = null, n = 0, beads = [], rings = [];
  let scale = 1, ox = 0, oy = 0, side = 1;
  // P runs from 0 (round) to 1 (sharp) and heads for `goal` once `wait` runs out.
  let P = calm ? 1 : 0, goal = 1, wait = o.delay, clock = 0, hovered = false;
  // Now and then the wings beat a few times, as if to hold position.
  const flutter = random(o.seed + 17);
  let burst = 5 + flutter() * 4, odd = false;

  // Per-frame rig transforms, model to camera: 0 is the body, 1 to 4 the wings.
  const rigM = new Float32Array(5 * 9), rigT = new Float32Array(5 * 3);

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

  // The pose at rest, model to camera: turned in the picture plane, then tilted.
  function basePose(yaw = 0, pitch = 0, roll = 0) {
    return mul(rotX(-o.tilt), mul(rotZ(-o.rotate + yaw), mul(rotX(pitch), rotY(roll))));
  }

  function build(view) {
    // Fit the sharp dragonfly at rest into the element; the round one is about as big.
    const G = basePose();
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const extend = (p, r = 0) => {
      const q = apply(G, p), k = DISTANCE / (DISTANCE - q[2]);
      x0 = Math.min(x0, (q[0] - r) * k); x1 = Math.max(x1, (q[0] + r) * k);
      y0 = Math.min(y0, (q[1] - r) * k); y1 = Math.max(y1, (q[1] + r) * k);
    };
    for (const part of parts) for (let u = 0; u <= 1; u += 1 / 12) for (let v = 0; v < 1; v += 1 / 12) extend(part.surface.at(u, v));
    for (const [w, f] of WINGS.map((w, i) => [w, frames[i]])) {
      for (const [s, c] of w.spec.lead.concat(w.spec.trail)) extend(wingPoint(f, s * w.spec.length, c * w.spec.chord));
    }
    const margin = 1.02; // room for hovering
    scale = Math.min(view.width / (x1 - x0), view.height / (y1 - y0)) * (o.fit / margin);
    ox = view.width / 2 - ((x0 + x1) / 2) * scale;
    oy = view.height / 2 + ((y0 + y1) / 2) * scale;
    side = triangleSize(view.ratio) / scale; // a triangle's side in model units
    sample();
  }

  // Tiles the body and wings with triangles, and gives each one a place to
  // start from in one of the round shapes of the same body part.
  function sample() {
    const rand = random(o.seed);
    const a = side * PITCH; // side of the tiling
    const items = [];

    // Body: band after band of triangles around each part.
    parts.forEach((part, index) => {
      mesh(part.surface, a, rand, (p, e1, e2, nrm) => {
        if (nrm[2] < -0.6) return; // never seen from above
        // Hidden inside a part drawn over it. Parts drawn together cut each other
        // only a little way in, leaving a fine seam.
        for (let j = 0; j < parts.length; j++) {
          if (j === index || parts[j].layer < part.layer) continue;
          if (parts[j].surface.inside(p, parts[j].layer === part.layer ? a * 0.45 : 0)) return;
        }
        items.push({ p, e1, e2, n: nrm, kind: part.kind ?? SHELL, rig: 0, layer: part.layer, group: part.group });
      });
    });
    for (const line of claspers()) {
      threadLine(smoothPath(line, 6), a * 1.05, (p, e1, nrm) => items.push({ p, e1, e2: cross(nrm, e1), n: nrm, kind: SHELL, rig: 0, layer: 0, group: 'abdomen' }));
    }

    // Wings: veins, cells and the pterostigma; and for the round dragonfly,
    // a ring in each cell.
    const thorax = parts.filter((part) => part.group === 'thorax');
    beads = spheres();
    rings = [];
    WINGS.forEach((w, i) => {
      const f = frames[i];
      const cells = wingTriangles(w.spec, a, o, rand, (s, c, ds, dc, kind, bias) => {
        const p = wingPoint(f, s, c);
        if (thorax.some((part) => part.surface.inside(p))) return;
        const e1 = unit(add(scaled(f.S, ds), scaled(f.C, dc)));
        items.push({ p, e1, e2: cross(f.N, e1), n: f.N, kind, bias, rig: i + 1, layer: w.layer, group: w.group });
      });
      for (const c of cells) rings.push({ c: wingPoint(f, c.s, c.c), r: c.r, rig: i + 1, layer: w.layer, group: w.group, S: f.S, C: f.C });
    });
    const shapes = beads.concat(rings);
    const reach = Math.max(...shapes.map((s) => Math.hypot(...s.c)));
    for (const s of shapes) s.delay = style.order === 'centre' ? (Math.hypot(...s.c) / reach) * 0.9 + rand() * 0.1 : rand();

    // Start each triangle at the nearest round shape of its own part.
    const byGroup = new Map();
    for (const s of shapes) (byGroup.get(s.group) || byGroup.set(s.group, []).get(s.group)).push(s);
    n = items.length;
    tri = {
      p: new Float32Array(n * 3), e1: new Float32Array(n * 3), e2: new Float32Array(n * 3), ng: new Float32Array(n * 3), ns: new Float32Array(n * 3),
      s: new Float32Array(n * 3), q0: new Float32Array(n * 4), q1: new Float32Array(n * 4),
      delay: new Float32Array(n), lag: new Float32Array(n), rig: new Uint8Array(n), layer: new Uint8Array(n), kind: new Uint8Array(n), bias: new Int8Array(n),
    };
    items.forEach((t, i) => {
      const owners = byGroup.get(t.group);
      let best = owners[0], bd = Infinity;
      for (const s of owners) {
        const d = s.S ? Math.abs(Math.hypot(...sub(t.p, s.c)) - s.r) : Math.hypot(...sub(t.p, s.c)) - s.r;
        if (d < bd) {
          bd = d;
          best = s;
        }
      }
      let start;
      if (best.S) {
        // On the ring, where it comes nearest.
        const d = sub(t.p, best.c), u = dot(d, best.S), v = dot(d, best.C), l = Math.hypot(u, v) || 1;
        start = add(best.c, add(scaled(best.S, (u / l) * best.r), scaled(best.C, (v / l) * best.r)));
      } else start = add(best.c, scaled(unit(sub(t.p, best.c)), best.r * 0.8));
      const jitter = [0.18, 0.3, 0.5, 0.1][t.kind];
      const ns = unit(add(t.n, scaled(unit([rand() - 0.5, rand() - 0.5, rand() - 0.5]), jitter * rand())));
      tri.p.set(t.p, i * 3); tri.e1.set(t.e1, i * 3); tri.e2.set(t.e2, i * 3); tri.ng.set(t.n, i * 3); tri.ns.set(ns, i * 3);
      tri.s.set(start, i * 3);
      tri.q0.set(randomQuat(rand), i * 4);
      tri.q1.set(quatFromBasis(t.e1, t.e2, t.n), i * 4);
      tri.delay[i] = best.delay;
      tri.lag[i] = rand() * 0.15;
      tri.rig[i] = t.rig;
      tri.layer[i] = t.layer;
      tri.kind[i] = t.kind;
      tri.bias[i] = t.bias || 0;
    });
  }

  function tick(dt, render = true) {
    if (!tri) return;
    clock += dt;
    // While it only hovers, every other frame is enough.
    const settled = P === goal && wait <= 0 && clock < burst - 0.1;
    if (settled && (odd = !odd)) render = false;
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
    }
    if (render) draw();
  }

  // Hovering: the dragonfly sways and bobs a little, its wings shiver and now
  // and then beat a few times.
  function pose() {
    const m = calm ? 0 : o.motion, t = clock;
    if (t > burst + 1) burst = t + 7 + flutter() * 6;
    const since = t - burst, beats = since > 0 && since < 0.9 ? Math.sin((Math.PI * since) / 0.9) ** 2 : 0;
    const yaw = m * (0.02 * Math.sin(t * TAU * 0.13) + 0.008 * Math.sin(t * TAU * 0.31 + 1));
    const pitch = m * 0.018 * Math.sin(t * TAU * 0.17 + 2);
    const roll = m * 0.035 * Math.sin(t * TAU * 0.11 + 0.5);
    const bob = m * 0.6 * Math.sin(t * TAU * 0.23);
    const G = basePose(yaw, pitch, roll);
    const lift = apply(G, [0, 0, bob]);
    rigM.set(G, 0);
    rigT.set(lift, 0);
    frames.forEach((f, i) => {
      const phase = i < 2 ? 0.9 : 0;
      const beat = m * (0.05 * Math.sin(t * TAU * 0.6 + phase) + 0.2 * beats * Math.sin(since * TAU * 4.5 + phase * 2));
      const R = axisAngle(f.hinge, beat);
      const M = mul(G, R);
      const T = add(apply(G, sub(f.root, apply(R, f.root))), lift);
      rigM.set(M, (i + 1) * 9);
      rigT.set(T, (i + 1) * 3);
    });
  }

  function draw() {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    pose();
    const span = 1.15; // per-shape stagger, as a share of the whole change
    const R = side / SQRT3; // a triangle's circumradius, in model units
    const paths = Array.from({ length: 6 }, () => []);
    const path = (layer, tone) => paths[layer][tone] || (paths[layer][tone] = new Path2D());
    // Settled shell triangles sit on a slightly larger dark copy of themselves, so
    // the seams between them read as fine dark lines and the body stays deep black.
    const under = Array.from({ length: 6 }, () => new Path2D()), grow = PITCH * 1.04;
    const f = 3 / 100, z = clock * 0.2;
    const q = [0, 0, 0, 0], E1 = [0, 0, 0], E2 = [0, 0, 0], NS = [0, 0, 0], corner = new Float64Array(6);

    for (let i = 0; i < n; i++) {
      const u = clamp(P * (1 + span + 0.15) - tri.delay[i] * span - tri.lag[i], 0, 1);
      const size = smooth(clamp(u / 0.3, 0, 1));
      if (size < 0.03) continue;
      const i3 = i * 3, rig = tri.rig[i], kind = tri.kind[i];
      let x, y, zz, e1x, e1y, e1z, e2x, e2y, e2z, nx, ny, nz;
      if (u >= 1) {
        x = tri.p[i3]; y = tri.p[i3 + 1]; zz = tri.p[i3 + 2];
        e1x = tri.e1[i3]; e1y = tri.e1[i3 + 1]; e1z = tri.e1[i3 + 2];
        e2x = tri.e2[i3]; e2y = tri.e2[i3 + 1]; e2z = tri.e2[i3 + 2];
        nx = tri.ns[i3]; ny = tri.ns[i3 + 1]; nz = tri.ns[i3 + 2];
      } else {
        const m = smooth(clamp((u - 0.1) / 0.9, 0, 1));
        x = tri.s[i3] + (tri.p[i3] - tri.s[i3]) * m;
        y = tri.s[i3 + 1] + (tri.p[i3 + 1] - tri.s[i3 + 1]) * m;
        zz = tri.s[i3 + 2] + (tri.p[i3 + 2] - tri.s[i3 + 2]) * m;
        if (style.swirl) {
          curl(noise, x * f, y * f, z, c2);
          const amp = style.swirl * 100 * Math.sin(Math.PI * m) * 0.5;
          x += c2[0] * amp;
          y += c2[1] * amp;
        }
        nlerp(tri.q0, tri.q1, i * 4, m, q);
        basis(q, E1, E2, NS);
        e1x = E1[0]; e1y = E1[1]; e1z = E1[2];
        e2x = E2[0]; e2y = E2[1]; e2z = E2[2];
        // Keep the facet's own tilt as it turns into place.
        nx = NS[0] + tri.ns[i3] - tri.ng[i3];
        ny = NS[1] + tri.ns[i3 + 1] - tri.ng[i3 + 1];
        nz = NS[2] + tri.ns[i3 + 2] - tri.ng[i3 + 2];
      }
      const M = rigM, k9 = rig * 9, T = rig * 3;
      const cx = M[k9] * x + M[k9 + 1] * y + M[k9 + 2] * zz + rigT[T];
      const cy = M[k9 + 3] * x + M[k9 + 4] * y + M[k9 + 5] * zz + rigT[T + 1];
      const cz = M[k9 + 6] * x + M[k9 + 7] * y + M[k9 + 8] * zz + rigT[T + 2];
      const ax = M[k9] * e1x + M[k9 + 1] * e1y + M[k9 + 2] * e1z;
      const ay = M[k9 + 3] * e1x + M[k9 + 4] * e1y + M[k9 + 5] * e1z;
      const az = M[k9 + 6] * e1x + M[k9 + 7] * e1y + M[k9 + 8] * e1z;
      const bx = M[k9] * e2x + M[k9 + 1] * e2y + M[k9 + 2] * e2z;
      const by = M[k9 + 3] * e2x + M[k9 + 4] * e2y + M[k9 + 5] * e2z;
      const bz = M[k9 + 6] * e2x + M[k9 + 7] * e2y + M[k9 + 8] * e2z;
      let sx = M[k9] * nx + M[k9 + 1] * ny + M[k9 + 2] * nz;
      let sy = M[k9 + 3] * nx + M[k9 + 4] * ny + M[k9 + 5] * nz;
      let sz = M[k9 + 6] * nx + M[k9 + 7] * ny + M[k9 + 8] * nz;
      // A settled facet of the shell that faces away is hidden.
      const solid = kind === SHELL || kind === EYE;
      if (solid && u >= 1 && ax * by - ay * bx < -0.08) continue;
      if (!solid && sz < 0) {
        sx = -sx; sy = -sy; sz = -sz;
      }
      const l = Math.hypot(sx, sy, sz) || 1;
      const tone = shade(sx / l, sy / l, sz / l, kind, tri.bias[i]);
      const p = path(tri.layer[i], tone);
      const r = R * size;
      for (let v = 0; v < 3; v++) {
        const cs = v === 0 ? 1 : -0.5, sn = v === 0 ? 0 : v === 1 ? 0.8660254 : -0.8660254;
        const px = cx + (ax * cs + bx * sn) * r, py = cy + (ay * cs + by * sn) * r, pz = cz + (az * cs + bz * sn) * r;
        const kk = (DISTANCE / (DISTANCE - pz)) * scale;
        corner[v * 2] = ox + px * kk;
        corner[v * 2 + 1] = oy - py * kk;
      }
      // In the sharpen style, triangles arrive as round dots and only then sharpen.
      const round = style.sharpen && u < 1 ? 1 - smooth(clamp((u - 0.55) / 0.45, 0, 1)) : 0;
      roundedTriangle(p, corner, round);
      if (solid && u >= 1) {
        const mx = (corner[0] + corner[2] + corner[4]) / 3, my = (corner[1] + corner[3] + corner[5]) / 3;
        for (let v = 0; v < 6; v += 2) {
          corner[v] = mx + (corner[v] - mx) * grow;
          corner[v + 1] = my + (corner[v + 1] - my) * grow;
        }
        roundedTriangle(under[tri.layer[i]], corner, 0);
      }
    }

    for (let layer = 0; layer < 6; layer++) {
      drawRound(ctx, layer, span);
      ctx.fillStyle = SEAM;
      ctx.fill(under[layer]);
      const row = paths[layer];
      for (let t = 0; t < PALETTE.length; t++) {
        if (!row[t]) continue;
        ctx.fillStyle = PALETTE[t];
        ctx.fill(row[t]);
      }
    }
  }

  // The round shapes of one layer, shrinking or thinning away as they break up.
  function drawRound(ctx, layer, span) {
    const base = new Path2D(), soft = new Path2D(), sheen = new Path2D(), glint = new Path2D();
    let any = false;
    // Highlights sit towards the light, as seen on the canvas.
    const ll = Math.hypot(LIGHT[0], LIGHT[1]), dx = LIGHT[0] / ll, dy = -LIGHT[1] / ll;
    for (const b of beads) {
      if (b.layer !== layer) continue;
      const u = clamp(P * (1 + span) - b.delay * span, 0, 1);
      const grow = 1 - smooth(clamp(u / 0.45, 0, 1));
      if (grow < 0.02) continue;
      const [X, Y, k] = project(0, b.c);
      const r = b.r * k * scale * grow;
      disc(base, X, Y, r);
      disc(soft, X + dx * r * 0.2, Y + dy * r * 0.2, r * 0.66);
      disc(sheen, X + dx * r * 0.38, Y + dy * r * 0.38, r * 0.34);
      disc(glint, X + dx * r * 0.55, Y + dy * r * 0.55, r * 0.11);
      any = true;
    }
    const ring = new Path2D();
    for (const c of rings) {
      if (c.layer !== layer) continue;
      const u = clamp(P * (1 + span) - c.delay * span, 0, 1);
      const thin = 1 - smooth(clamp(u / 0.35, 0, 1));
      if (thin < 0.04) continue;
      const w = side * 0.34 * thin, r = c.r * (1 + 0.12 * (1 - thin));
      loopPath(ring, c, r + w / 2, false);
      loopPath(ring, c, Math.max(0, r - w / 2), true);
      any = true;
    }
    if (!any) return;
    ctx.fillStyle = TONES[1];
    ctx.fill(ring);
    ctx.fill(base);
    ctx.fillStyle = TONES[3];
    ctx.fill(soft);
    ctx.fillStyle = TONES[6];
    ctx.fill(sheen);
    ctx.fillStyle = TONES[11];
    ctx.fill(glint);
  }

  // A ring in its wing's plane, as a polygon.
  function loopPath(p, c, r, reverse) {
    const M = rigM, k9 = c.rig * 9, T = c.rig * 3;
    const steps = 20;
    for (let j = 0; j <= steps; j++) {
      const a = ((reverse ? steps - j : j) / steps) * TAU;
      const q = add(c.c, add(scaled(c.S, Math.cos(a) * r), scaled(c.C, Math.sin(a) * r)));
      const cx = M[k9] * q[0] + M[k9 + 1] * q[1] + M[k9 + 2] * q[2] + rigT[T];
      const cy = M[k9 + 3] * q[0] + M[k9 + 4] * q[1] + M[k9 + 5] * q[2] + rigT[T + 1];
      const cz = M[k9 + 6] * q[0] + M[k9 + 7] * q[1] + M[k9 + 8] * q[2] + rigT[T + 2];
      const k = (DISTANCE / (DISTANCE - cz)) * scale;
      if (j) p.lineTo(ox + cx * k, oy - cy * k);
      else p.moveTo(ox + cx * k, oy - cy * k);
    }
    p.closePath();
  }

  // Model point on a rig to canvas pixels, plus the perspective factor.
  function project(rig, p) {
    const M = rigM, k9 = rig * 9, T = rig * 3;
    const cx = M[k9] * p[0] + M[k9 + 1] * p[1] + M[k9 + 2] * p[2] + rigT[T];
    const cy = M[k9 + 3] * p[0] + M[k9 + 4] * p[1] + M[k9 + 5] * p[2] + rigT[T + 1];
    const cz = M[k9 + 6] * p[0] + M[k9 + 7] * p[1] + M[k9 + 8] * p[2] + rigT[T + 2];
    const k = DISTANCE / (DISTANCE - cz);
    return [ox + cx * k * scale, oy - cy * k * scale, k];
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
      for (let s = 0; s < seconds; s += 1 / 60) tick(1 / 60, false);
      draw();
    },
    destroy() {
      loop.destroy();
      surface.destroy();
    },
  };
}

// How bright a facet looks: a little diffuse light and a sharp gloss for the
// shell and veins, a glassy glint for the eyes and a faint sheen for the
// membrane. Returns a PALETTE index.
function shade(nx, ny, nz, kind, bias = 0) {
  const d = Math.max(0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]);
  const h = Math.max(0, nx * HALF[0] + ny * HALF[1] + nz * HALF[2]);
  if (kind === MEMBRANE) return TONES.length + clamp(Math.floor(h ** 6 * 3) + bias, 0, FILM.length - 1);
  const gloss = kind === SHELL ? 0.9 * h ** 30 : kind === EYE ? 1.1 * h ** 70 + 0.25 * h ** 6 : 0.55 * h ** 18;
  const I = 0.01 + 0.12 * d + gloss;
  return clamp(Math.round(I * (TONES.length - 1)) + bias, 0, TONES.length - 1);
}

// A triangle through three corners [x0, y0, x1, y1, x2, y2] whose corners can be
// rounded all the way to its inscribed circle (round = 1).
function roundedTriangle(p, v, round) {
  if (round < 0.02) {
    p.moveTo(v[0], v[1]);
    p.lineTo(v[2], v[3]);
    p.lineTo(v[4], v[5]);
    p.closePath();
    return;
  }
  const a = Math.hypot(v[2] - v[4], v[3] - v[5]), b = Math.hypot(v[4] - v[0], v[5] - v[1]), c = Math.hypot(v[0] - v[2], v[1] - v[3]);
  const s = (a + b + c) / 2, inradius = Math.sqrt(Math.max(0, ((s - a) * (s - b) * (s - c)) / (s || 1)));
  const rho = Math.min(round, 0.98) * inradius;
  p.moveTo((v[4] + v[0]) / 2, (v[5] + v[1]) / 2);
  p.arcTo(v[0], v[1], v[2], v[3], rho);
  p.arcTo(v[2], v[3], v[4], v[5], rho);
  p.arcTo(v[4], v[5], v[0], v[1], rho);
  p.closePath();
}

function disc(p, x, y, r) {
  p.moveTo(x + r, y);
  p.arc(x, y, r, 0, TAU);
}

// ---------------------------------------------------------------------------
// Surfaces. `at(u, v)` gives a point for u in [0, 1] from end to end and v in
// [0, 1) around; `out(p, u)` points outwards; `inside(p)` tests a point.

// An ellipsoid with radii r along `axis`, `side` and the third direction.
function ellipsoid(c, axis, side, r) {
  const a = unit(axis), b = unit(sub(side, scaled(a, dot(side, a)))), w = cross(a, b);
  return {
    at(u, v) {
      const t = u * Math.PI, q = v * TAU, ca = Math.cos(t) * r[0], s = Math.sin(t);
      const cb = Math.cos(q) * r[1] * s, sw = Math.sin(q) * r[2] * s;
      return [c[0] + a[0] * ca + b[0] * cb + w[0] * sw, c[1] + a[1] * ca + b[1] * cb + w[1] * sw, c[2] + a[2] * ca + b[2] * cb + w[2] * sw];
    },
    out: (p) => sub(p, c),
    // Whether p lies inside, at least `depth` below the surface (roughly).
    inside(p, depth = 0) {
      const d = sub(p, c);
      return (dot(d, a) / (r[0] - depth)) ** 2 + (dot(d, b) / (r[1] - depth)) ** 2 + (dot(d, w) / (r[2] - depth)) ** 2 < 1;
    },
  };
}

function tube(path, radius, flat = 1) {
  const frame = (u) => {
    const t = unit(sub(path(Math.min(1, u + 1e-3)), path(Math.max(0, u - 1e-3))));
    const side = unit(cross(t, [0, 0, 1]));
    return [side, cross(side, t)];
  };
  const samples = Array.from({ length: 121 }, (_, i) => i / 120);
  return {
    at(u, v) {
      const p = path(u), [s, up] = frame(u), r = radius(u), q = v * TAU;
      const x = Math.cos(q) * r, y = Math.sin(q) * r * flat;
      return [p[0] + s[0] * x + up[0] * y, p[1] + s[1] * x + up[1] * y, p[2] + s[2] * x + up[2] * y];
    },
    out: (p, u) => sub(p, path(u)),
    inside(p, depth = 0) {
      for (const u of samples) {
        const q = path(u), r = radius(u) - depth;
        if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 < r * r) return true;
      }
      return false;
    },
  };
}

// Tiles a surface with triangles of side `a`: bands from end to end, each a
// ring of triangles pointing alternately along and against the band.
function mesh(surface, a, rand, emit) {
  const h = (a * SQRT3) / 2;
  const N = 160, len = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) {
    let d = 0;
    for (const v of [0, 0.25, 0.5, 0.75]) d += Math.hypot(...sub(surface.at(i / N, v), surface.at((i - 1) / N, v)));
    len[i] = len[i - 1] + d / 4;
  }
  const total = len[N];
  const uAt = (s) => {
    s = clamp(s, 0, total);
    let i = 1;
    while (i < N && len[i] < s) i++;
    return (i - 1 + (s - len[i - 1]) / (len[i] - len[i - 1] || 1)) / N;
  };
  const bands = Math.max(1, Math.round(total / h)), hh = total / bands;
  const M = 96, ring = new Float64Array(M + 1);
  for (let b = 0; b < bands; b++) {
    const um = uAt((b + 0.5) * hh);
    // Even steps of length around the band, however unevenly v runs.
    for (let k = 1, prev = surface.at(um, 0); k <= M; k++) {
      const next = surface.at(um, k / M);
      ring[k] = ring[k - 1] + Math.hypot(...sub(next, prev));
      prev = next;
    }
    const round = ring[M], count = Math.round(round / a);
    const vAt = (l) => {
      l = ((l % round) + round) % round;
      let k = 1;
      while (k < M && ring[k] < l) k++;
      return (k - 1 + (l - ring[k - 1]) / (ring[k] - ring[k - 1] || 1)) / M;
    };
    const shift = rand();
    if (count < 1) {
      place(surface, um, shift, true, emit);
      continue;
    }
    for (let k = 0; k < 2 * count; k++) {
      const up = k % 2 === 0;
      place(surface, uAt((b + 0.5) * hh + (up ? -hh / 6 : hh / 6)), vAt(((k / 2 + shift) * round) / count), up, emit);
    }
  }
}

function place(surface, u, v, up, emit) {
  const e = 1e-3;
  const p = surface.at(u, v);
  const du = sub(surface.at(Math.min(1, u + e), v), surface.at(Math.max(0, u - e), v));
  const dv = sub(surface.at(u, v + e), surface.at(u, v - e));
  const along = unit(du);
  let around = unit(sub(dv, scaled(along, dot(dv, along))));
  let nrm = cross(around, along);
  if (dot(nrm, surface.out(p, u)) < 0) {
    around = scaled(around, -1);
    nrm = scaled(nrm, -1);
  }
  // Apex along the band for "up" triangles, against it for the others.
  emit(p, up ? along : scaled(along, -1), up ? scaled(around, -1) : around, nrm);
}

// Triangles in single file along a 3D path, pointing along it, facing up.
function threadLine(path, step, emit) {
  walk(path, step, step / 2, (p, t) => {
    const nrm = unit(sub([0, 0, 1], scaled(t, t[2])));
    emit(p, t, nrm);
  });
}

// Calls `visit(point, unit tangent, index)` every `step` along a polyline (2D or
// 3D), starting `offset` in.
function walk(path, step, offset, visit) {
  let need = offset, k = 0;
  for (let i = 1; i < path.length; i++) {
    const a = path[i - 1], b = path[i], d = b.map((v, j) => v - a[j]), l = Math.hypot(...d);
    if (!l) continue;
    while (need <= l) {
      visit(a.map((v, j) => v + (d[j] * need) / l), d.map((v) => v / l), k++);
      need += step;
    }
    need -= l;
  }
}

// Catmull-Rom through points (2D or 3D), `per` steps per span.
function smoothPath(pts, per = 6) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let j = 0; j < per; j++) {
      const t = j / per, t2 = t * t, t3 = t2 * t;
      out.push(p1.map((_, d) => 0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3)));
    }
  }
  out.push(pts[pts.length - 1].slice());
  return out;
}

// ---------------------------------------------------------------------------
// Wings, worked out in the wing's own plane: s along the span and c back along
// the chord, both in model units.

function wingPoint(f, s, c) {
  return add(f.root, add(scaled(f.S, s), scaled(f.C, c)));
}

function wingOutline(spec) {
  const L = spec.length, W = spec.chord;
  const toUnits = (pts) => pts.map(([s, c]) => [s * L, c * W]);
  const lead = smoothPath(toUnits(spec.lead), 8);
  const trail = smoothPath(toUnits(spec.trail), 8);
  return { lead, trail, outline: lead.concat(trail.slice(1, -1)) };
}

// The chord position of a polyline at span s, if it reaches that far.
function chordAt(poly, s) {
  for (let i = 1; i < poly.length; i++) {
    const [s0, c0] = poly[i - 1], [s1, c1] = poly[i];
    if ((s - s0) * (s - s1) <= 0 && s0 !== s1) return c0 + ((c1 - c0) * (s - s0)) / (s1 - s0);
  }
  return null;
}

function insidePolygon(poly, x, y) {
  let hit = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

function edgeDistance(poly, x, y) {
  let best = Infinity;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [ax, ay] = poly[j], [bx, by] = poly[i];
    const dx = bx - ax, dy = by - ay, l = dx * dx + dy * dy || 1;
    const t = clamp(((x - ax) * dx + (y - ay) * dy) / l, 0, 1);
    best = Math.min(best, Math.hypot(x - ax - dx * t, y - ay - dy * t));
  }
  return best;
}

// Emits a wing's triangles as (s, c, ds, dc, kind, bias): (ds, dc) is where the
// apex points and bias lightens (+) or darkens (-) its tone. Earlier, bolder
// parts win where two would overlap.
function wingTriangles(spec, a, { film, cell }, rand, emit) {
  const L = spec.length, W = spec.chord;
  const { lead, trail, outline } = wingOutline(spec);
  const h = (a * SQRT3) / 2;
  const widest = Math.max(...outline.map(([s]) => (chordAt(trail, s) ?? 0) - (chordAt(lead, s) ?? 0)));
  const across = widest / a;
  const rank = across < 5 ? 0 : across < 8 ? 1 : across < 11 ? 2 : 3;

  const cells = new Map();
  const taken = (s, c, gap) => {
    const i = Math.floor(s / a), j = Math.floor(c / a);
    for (let di = -1; di <= 1; di++) {
      for (let dj = -1; dj <= 1; dj++) {
        for (const [ps, pc] of cells.get(`${i + di},${j + dj}`) || []) if ((ps - s) ** 2 + (pc - c) ** 2 < gap * gap) return true;
      }
    }
    return false;
  };
  const put = (s, c, ds, dc, kind, bias = 0, gap = a * 0.8) => {
    if (!insidePolygon(outline, s, c) || taken(s, c, gap)) return;
    const k = `${Math.floor(s / a)},${Math.floor(c / a)}`;
    (cells.get(k) || cells.set(k, []).get(k)).push([s, c]);
    emit(s, c, ds, dc, kind, bias);
  };

  // A band of triangles alternately pointing in and out, along a vein or
  // (with `inward` set) just inside an edge.
  const band = (poly, bias = 0, inward = 0) => {
    walk(poly, a / 2, a / 4, (p, t, k) => {
      const nx = -t[1] * (inward || 1), ny = t[0] * (inward || 1);
      const up = k % 2 === 0, off = (inward ? h / 2 : 0) + (up ? -h / 6 : h / 6);
      put(p[0] + nx * off, p[1] + ny * off, up ? nx : -nx, up ? ny : -ny, VEIN, bias, a * 0.45);
    });
  };
  // Triangles in single file along a vein.
  const thread = (poly, bias = 0, step = a * 1.0, gap = a * 0.8) => walk(poly, step, step / 2, (p, t) => put(p[0], p[1], t[0], t[1], VEIN, bias, gap));
  // A solid patch.
  const fill = (poly, bias = 0) => {
    const s0 = Math.min(...poly.map((p) => p[0])), s1 = Math.max(...poly.map((p) => p[0]));
    const c0 = Math.min(...poly.map((p) => p[1])), c1 = Math.max(...poly.map((p) => p[1]));
    for (let r = 0, c = c0; c <= c1 + h; r++, c += h) {
      for (let k = 0, s = s0 + ((r & 1) * a) / 2; s <= s1 + a; k++, s += a / 2) {
        const up = (k & 1) === 0, cc = c + (up ? -h / 6 : h / 6);
        if (insidePolygon(poly, s, cc)) put(s, cc, 0, up ? 1 : -1, VEIN, bias, a * 0.45);
      }
    }
  };

  fill(spec.stigma.map(([s, c]) => [s * L, c * W]), -1);
  band(lead, 0, 1); // the leading edge: costa and radius together
  const veins = spec.veins.filter((v) => v.rank <= rank).map((v) => ({ ...v, poly: smoothPath(v.pts.map(([s, c]) => [s * L, c * W]), 6) }));
  for (const v of veins) thread(v.poly, 0, a * 0.72, a * 0.62);
  thread(trail.slice().reverse(), 0, a * 0.72, a * 0.62);

  // The cells between the veins, as the edges of a Voronoi diagram of jittered seeds.
  const { edges, seeds } = cellEdges(lead, trail, L, widest, a * cell, rand);
  for (const [p, q] of edges) thread([p, q], 1, a * 0.8, a * 0.7);

  // The root, where the wing joins the thorax.
  fill(outline.filter(([s]) => s < L * 0.05).concat([[L * 0.05, chordAt(trail, L * 0.05)], [L * 0.05, chordAt(lead, L * 0.05)]]));

  // The membrane: a film of fainter triangles between the veins, `film` from 0 (clear) to 1 (smoky).
  if (film > 0) {
    const g = a * (2.2 - film * 0.9), row = g * 0.866;
    for (let r = 0, c = -W * 0.1; c < W * 1.5; r++, c += row) {
      for (let s = ((r & 1) * g) / 2; s < L; s += g) {
        const ang = rand() * TAU;
        put(s + (rand() - 0.5) * g * 0.4, c + (rand() - 0.5) * row * 0.4, Math.cos(ang), Math.sin(ang), MEMBRANE, Math.round(film * 4), a * 0.85);
      }
    }
  }

  // Round cells for the round dragonfly: one inside each cell of the wing,
  // and smaller ones in the gaps where cells meet.
  const round = [];
  const fit = (s, c, most) => {
    if (!insidePolygon(outline, s, c)) return 0;
    let r = Math.min(most, edgeDistance(outline, s, c) - a * 0.3);
    for (const q of round) r = Math.min(r, Math.hypot(q.s - s, q.c - c) - q.r - a * 0.3);
    return r;
  };
  for (const [s, c] of seeds) {
    let most = Infinity;
    for (const [qs, qc] of seeds) if (qs !== s || qc !== c) most = Math.min(most, Math.hypot(qs - s, qc - c) / 2 - a * 0.25);
    const r = fit(s, c, most * (0.72 + 0.28 * rand()));
    if (r > a * 0.5) round.push({ s, c, r });
  }
  for (const [p, q] of edges) {
    for (const [s, c] of [p, q]) {
      const r = fit(s, c, a * 1.6);
      if (r > a * 0.4) round.push({ s, c, r });
    }
  }
  return round;
}

// Edges of the Voronoi cells of seeds laid in rows that follow the wing from
// root to tip, about `cell` apart, as [[s, c], [s, c]] segments.
function cellEdges(lead, trail, L, widest, cell, rand) {
  const rows = Math.max(2, Math.round(widest / (cell * 0.87))), seeds = [];
  for (let j = -1; j <= rows; j++) {
    for (let s = ((j & 1) * cell) / 2; s <= L; s += cell) {
      const ps = clamp(s + (rand() - 0.5) * cell * 0.4, 0, L);
      const c0 = chordAt(lead, ps), c1 = chordAt(trail, ps);
      if (c0 == null || c1 == null) continue;
      const f = (j + 0.5 + (j < 0 || j === rows ? 0 : (rand() - 0.5) * 0.3)) / rows;
      seeds.push([ps, c0 + f * (c1 - c0)]);
    }
  }
  const edges = [];
  for (let i = 0; i < seeds.length; i++) {
    const [ax, ay] = seeds[i];
    for (let j = i + 1; j < seeds.length; j++) {
      const [bx, by] = seeds[j], dx = bx - ax, dy = by - ay, d2 = dx * dx + dy * dy;
      if (d2 > (cell * 2) ** 2) continue;
      // The bisector of i and j, cut back to where no other seed is nearer.
      const mx = (ax + bx) / 2, my = (ay + by) / 2, l = Math.sqrt(d2), tx = -dy / l, ty = dx / l;
      let t0 = -cell * 2, t1 = cell * 2;
      for (let k = 0; k < seeds.length && t0 < t1; k++) {
        if (k === i || k === j) continue;
        const [kx, ky] = seeds[k];
        if ((kx - mx) ** 2 + (ky - my) ** 2 > (cell * 2.5) ** 2) continue;
        const ex = kx - ax, ey = ky - ay;
        const base = 2 * (mx * ex + my * ey), slope = 2 * (tx * ex + ty * ey), limit = kx * kx + ky * ky - ax * ax - ay * ay;
        if (Math.abs(slope) < 1e-9) {
          if (base > limit) t1 = t0;
        } else if (slope > 0) t1 = Math.min(t1, (limit - base) / slope);
        else t0 = Math.max(t0, (limit - base) / slope);
      }
      if (t1 - t0 > 1e-6) edges.push([[mx + tx * t0, my + ty * t0], [mx + tx * t1, my + ty * t1]]);
    }
  }
  return { edges, seeds };
}

// ---------------------------------------------------------------------------
// Vectors, 3 × 3 matrices (row by row) and quaternions [w, x, y, z].

function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function scaled(a, k) { return [a[0] * k, a[1] * k, a[2] * k]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function unit(a) { return scaled(a, 1 / (Math.hypot(a[0], a[1], a[2]) || 1)); }

function mul(A, B) {
  const C = new Array(9);
  for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) C[r * 3 + c] = A[r * 3] * B[c] + A[r * 3 + 1] * B[3 + c] + A[r * 3 + 2] * B[6 + c];
  return C;
}
function apply(M, p) {
  return [M[0] * p[0] + M[1] * p[1] + M[2] * p[2], M[3] * p[0] + M[4] * p[1] + M[5] * p[2], M[6] * p[0] + M[7] * p[1] + M[8] * p[2]];
}
function rotX(a) { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, -s, 0, s, c]; }
function rotY(a) { const c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; }
function rotZ(a) { const c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
function axisAngle(k, a) {
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c, [x, y, z] = k;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}

// The rotation taking the x, y and z axes to e1, e2 and n.
function quatFromBasis(e1, e2, n) {
  const m00 = e1[0], m10 = e1[1], m20 = e1[2], m01 = e2[0], m11 = e2[1], m21 = e2[2], m02 = n[0], m12 = n[1], m22 = n[2];
  const tr = m00 + m11 + m22;
  if (tr > 0) {
    const S = Math.sqrt(tr + 1) * 2;
    return [0.25 * S, (m21 - m12) / S, (m02 - m20) / S, (m10 - m01) / S];
  }
  if (m00 > m11 && m00 > m22) {
    const S = Math.sqrt(1 + m00 - m11 - m22) * 2;
    return [(m21 - m12) / S, 0.25 * S, (m01 + m10) / S, (m02 + m20) / S];
  }
  if (m11 > m22) {
    const S = Math.sqrt(1 + m11 - m00 - m22) * 2;
    return [(m02 - m20) / S, (m01 + m10) / S, 0.25 * S, (m12 + m21) / S];
  }
  const S = Math.sqrt(1 + m22 - m00 - m11) * 2;
  return [(m10 - m01) / S, (m02 + m20) / S, (m12 + m21) / S, 0.25 * S];
}

function randomQuat(rand) {
  const u1 = rand(), u2 = rand() * TAU, u3 = rand() * TAU;
  const a = Math.sqrt(1 - u1), b = Math.sqrt(u1);
  return [a * Math.sin(u2), a * Math.cos(u2), b * Math.sin(u3), b * Math.cos(u3)];
}

// Normalised blend of two stored quaternions, the short way round.
function nlerp(q0, q1, i, t, out) {
  const sgn = q0[i] * q1[i] + q0[i + 1] * q1[i + 1] + q0[i + 2] * q1[i + 2] + q0[i + 3] * q1[i + 3] < 0 ? -1 : 1;
  let l = 0;
  for (let k = 0; k < 4; k++) {
    out[k] = q0[i + k] * (1 - t) + sgn * q1[i + k] * t;
    l += out[k] * out[k];
  }
  l = 1 / Math.sqrt(l || 1);
  for (let k = 0; k < 4; k++) out[k] *= l;
  return out;
}

function basis([w, x, y, z], e1, e2, n) {
  e1[0] = 1 - 2 * (y * y + z * z); e1[1] = 2 * (x * y + w * z); e1[2] = 2 * (x * z - w * y);
  e2[0] = 2 * (x * y - w * z); e2[1] = 1 - 2 * (x * x + z * z); e2[2] = 2 * (y * z + w * x);
  n[0] = 2 * (x * z + w * y); n[1] = 2 * (y * z - w * x); n[2] = 1 - 2 * (x * x + y * y);
}
