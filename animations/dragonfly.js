// A deep black dragonfly drawn in tiny dashes, like the evolution animation,
// that beats its wings and does nothing else. It is modelled in 3D and seen a
// little from the side: rings of dashes wrap its body like the hatching of a
// pen drawing, dashes trace and shade its wings, and the wings swing about
// their roots as it flies.
//
//   import { mountDragonfly } from './animations/dragonfly.js';
//   mountDragonfly(document.getElementById('dragonfly'));

import { triangleSize, INK, TAU, random, clamp, smooth, reducedMotion, mountCanvas, animate } from './core.js';

// A dash for a screen's pixel ratio, in CSS pixels: the same as the evolution's (sketch.js).
function dashSize(ratio) {
  const length = triangleSize(ratio) * 1.15;
  return { length, width: Math.max(1 / ratio, length * 0.27) };
}

const DISTANCE = 400; // camera distance in model units, for a gentle perspective
// Towards the light and half-way to the eye, in camera space (x right, y up, z to the viewer).
const LIGHT = unit([-0.45, 0.6, 0.66]);
const HALF = unit([LIGHT[0], LIGHT[1], LIGHT[2] + 1]);

// Wing beats: beats a second; swing either side of the middle (radians) for
// the hind and fore wings; how far above flat the middle is; how far the
// forewings lag the hindwings, as a share of a beat; and how far each wing
// twists about its span, leading edge down on the way down and up on the way up.
const BEAT = 1.5, SWING = [0.5, 0.44], RAISE = 0.1, LAG = 0.25, TWIST = 0.3;

// ---------------------------------------------------------------------------
// The model. Units: about 100 from head to tail. +y points to the head, +x to
// the dragonfly's right and +z up out of its back; the thorax sits about the origin.

const SEGMENTS = [2.4, 6.0, 8.6, 8.4, 8.4, 8.2, 7.8, 6.6, 5.0, 3.4]; // abdomen, S1 to S10
const GIRTH = [3.0, 3.25, 1.95, 1.8, 1.85, 1.9, 2.0, 2.1, 2.0, 1.7]; // radius at each segment's middle
const ABDOMEN = SEGMENTS.reduce((a, b) => a + b, 0);
const MIDDLES = [], JOINTS = [];
for (let y = 0, k = 0; k < SEGMENTS.length; y += SEGMENTS[k++]) {
  MIDDLES.push(y + SEGMENTS[k] / 2);
  if (k) JOINTS.push(y);
}

// The abdomen leaves the back of the thorax and droops a little towards the tail.
const spine = (u) => [0, -4.5 - u * ABDOMEN, 0.6 - 3 * u * u];

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
  r *= 1 - 0.14 * Math.exp(-((near / 0.7) ** 2)); // pinched where segments meet
  const end = ABDOMEN - d;
  if (end < 1.4) r *= Math.sqrt(Math.max(0, 1 - (1 - end / 1.4) ** 2)); // rounded tip
  return r;
}

// Body parts as surfaces. Each is hatched with rings of dashes around its
// first axis; `layer` orders parts from the back, and a part hides whatever
// of the parts behind it lies inside it.
function bodyParts() {
  const eye = (x) => ellipsoid([x * 2.9, 14.4, 2.3], [[x * 4.6, 0, 0], [0, 5.4, 0.8], [0, -0.9, 5.1]]);
  // Pale lines left in the hatching: where the abdomen's segments meet, and
  // the two sutures that run down the thorax's flank.
  const joint = (p) => JOINTS.some((j) => Math.abs(-4.5 - p[1] - j) < 0.12);
  const suture = (p) => Math.abs(p[0]) > 1.4 && [-1.7, 1.5].some((k) => Math.abs(0.891 * (p[1] - 1.4) + 0.453 * (p[2] - 0.4) - k) < 0.2);
  return [
    { layer: 0, surface: tube(spine, girth, 1.08), skip: joint },
    { layer: 0, surface: ellipsoid([0, -11.6, -2.6], [[0, 2.4, 0], [1.1, 0, 0], [0, 0, 1.3]]) }, // genital lobe under S2
    // The thorax leans back: legs at the front of its underside, wings on top behind.
    { layer: 2, surface: ellipsoid([0, 1.4, 0.4], [[0, 7.0, 0], [5.7, 0, 0], [0, -3.2, 6.3]]), skip: suture },
    { layer: 2, surface: ellipsoid([0, 9.4, 0.3], [[0, 1.9, 0], [2.8, 0, 0], [0, 0, 2.4]]) }, // prothorax
    { layer: 3, surface: ellipsoid([0, 18.7, -0.5], [[0, 2.2, 0], [3.7, 0, 0], [0, 0.4, 3.3]]) }, // face
    { layer: 3, surface: ellipsoid([0, 19.3, -3.6], [[0, 1.2, 0], [2.4, 0, 0], [0, 0, 1.2]]) }, // upper lip
    { layer: 3, surface: ellipsoid([0, 16.6, -4.3], [[0, 2.0, 0], [2.5, 0, 0], [0, 0, 1.3]]) }, // mouthparts
    { layer: 4, surface: eye(-1) },
    { layer: 4, surface: eye(1) },
  ];
}

// Thin parts drawn as lines of dashes: legs folded under the thorax as in
// flight, with spines on their shins; the antennae; and the tail's claspers.
function limbs() {
  const out = [];
  const legs = [
    // hip, knee, ankle, claw: the front pair reaches forward under the head,
    // the others fold back under the thorax
    [[1.0, 8.6, -1.6], [1.8, 11.4, -3.8], [1.4, 9.0, -5.6], [1.5, 11.0, -6.3]],
    [[1.4, 5.2, -4.2], [2.6, 8.2, -6.2], [2.2, 4.4, -7.9], [2.3, 6.6, -8.7]],
    [[1.6, 2.2, -5.2], [3.0, 5.4, -7.4], [2.6, 0.6, -9.2], [2.7, 3.0, -10.2]],
  ];
  for (const x of [-1, 1]) {
    for (const leg of legs) {
      const pts = leg.map(([a, b, c]) => [x * a, b, c]);
      out.push({ pts: pts.slice(0, 2), rows: 2 }); // thigh
      out.push({ pts: pts.slice(1, 3), rows: 1, spines: true }); // shin
      out.push({ pts: pts.slice(2), rows: 1 }); // foot
    }
    out.push({ pts: [[x * 0.9, 19.2, 1.6], [x * 1.3, 20.6, 3.0], [x * 1.6, 21.6, 3.6]], rows: 1 }); // antenna
  }
  const end = spine(1);
  for (const x of [-1, 1]) out.push({ pts: [[x * 0.4, end[1] + 0.6, end[2] + 0.5], [x * 0.9, end[1] - 2.6, end[2] + 0.7], [x * 1.1, end[1] - 5.6, end[2] + 0.4]], rows: 2 }); // upper claspers
  out.push({ pts: [[0, end[1] + 0.4, end[2] - 0.6], [0, end[1] - 2.2, end[2] - 0.9], [0, end[1] - 3.6, end[2] - 0.4]], rows: 1 }); // lower clasper
  return out;
}

// Wings, in fractions of their length (s, root to tip) and chord (c, from the
// leading edge back). Veins of rank 0 always show; higher ranks only once the
// wing is wide enough in dashes to hold them.
const RADIUS = [[0, 0.2], [0.08, 0.1], [0.25, 0.075], [0.47, 0.085], [0.7, 0.08], [0.8, 0.085], [0.9, 0.11], [0.96, 0.16], [0.99, 0.22]];
const SECTOR = [[0.02, 0.27], [0.12, 0.2], [0.3, 0.19], [0.5, 0.2], [0.7, 0.23], [0.85, 0.27], [0.95, 0.31], [0.995, 0.34]];
const R45 = [[0.22, 0.2], [0.36, 0.3], [0.5, 0.42], [0.62, 0.6], [0.72, 0.8], [0.77, 0.98]];
const IR2 = [[0.36, 0.21], [0.52, 0.29], [0.66, 0.38], [0.78, 0.5], [0.88, 0.64], [0.93, 0.74]];

const FOREWING = {
  root: [2.3, 0.9, 6.0], length: 65, chord: 13, sweep: 0.1, dihedral: 0.04,
  lead: [[0, 0.16], [0.03, 0.07], [0.1, 0.015], [0.25, 0], [0.47, 0.012], [0.65, 0.006], [0.82, 0.012], [0.91, 0.032], [0.965, 0.08], [0.993, 0.16], [1, 0.25]],
  trail: [[1, 0.25], [0.994, 0.36], [0.97, 0.5], [0.92, 0.64], [0.84, 0.77], [0.72, 0.88], [0.56, 0.96], [0.4, 0.99], [0.26, 0.94], [0.15, 0.8], [0.08, 0.6], [0.035, 0.42], [0, 0.3]],
  veins: [
    { rank: 0, pts: SECTOR },
    { rank: 0, pts: [[0.47, 0.012], [0.47, 0.2]] }, // nodus
    { rank: 1, pts: RADIUS },
    { rank: 1, pts: R45 },
    { rank: 1, pts: [[0.03, 0.36], [0.12, 0.4], [0.22, 0.5], [0.32, 0.66], [0.4, 0.9], [0.42, 1.02]] }, // media
    { rank: 2, pts: IR2 },
    { rank: 2, pts: [[0.04, 0.46], [0.1, 0.56], [0.16, 0.72], [0.22, 0.9], [0.25, 1.0]] }, // cubitus
    { rank: 2, pts: [[0.11, 0.42], [0.2, 0.47], [0.14, 0.62], [0.11, 0.42]] }, // discoidal triangle
  ],
  stigma: [[0.785, 0.01], [0.885, 0.022], [0.882, 0.115], [0.782, 0.105]],
};

const HINDWING = {
  root: [2.3, -4.1, 5.6], length: 63, chord: 12.6, sweep: -0.09, dihedral: 0.03,
  lead: [[0, 0.14], [0.03, 0.06], [0.1, 0.012], [0.25, 0], [0.45, 0.012], [0.65, 0.006], [0.82, 0.012], [0.91, 0.032], [0.965, 0.08], [0.993, 0.16], [1, 0.25]],
  trail: [[1, 0.25], [0.994, 0.36], [0.97, 0.49], [0.92, 0.62], [0.84, 0.73], [0.72, 0.83], [0.58, 0.9], [0.46, 0.95], [0.36, 1.03], [0.26, 1.16], [0.17, 1.28], [0.1, 1.33], [0.05, 1.26], [0.02, 1.0], [0, 0.5]],
  veins: [
    { rank: 0, pts: SECTOR },
    { rank: 0, pts: [[0.45, 0.012], [0.45, 0.2]] }, // nodus
    { rank: 1, pts: RADIUS },
    { rank: 1, pts: R45 },
    { rank: 1, pts: [[0.03, 0.34], [0.14, 0.4], [0.26, 0.52], [0.38, 0.7], [0.46, 0.92], [0.49, 1.02]] }, // media
    { rank: 1, pts: [[0.04, 0.48], [0.1, 0.62], [0.17, 0.82], [0.24, 1.0], [0.3, 1.14]] }, // cubitus
    { rank: 2, pts: IR2 },
    { rank: 2, pts: [[0.02, 0.6], [0.05, 0.8], [0.09, 1.05], [0.12, 1.34]] }, // anal vein
    { rank: 2, pts: [[0.06, 0.72], [0.13, 0.78], [0.18, 0.92], [0.12, 1.02], [0.07, 0.95], [0.06, 0.72]] }, // anal loop
  ],
  stigma: [[0.785, 0.01], [0.88, 0.022], [0.877, 0.11], [0.782, 0.1]],
};

// The four wings, and which pair (hind 0, fore 1) each belongs to.
const WINGS = [
  { spec: HINDWING, side: -1, pair: 0 },
  { spec: HINDWING, side: 1, pair: 0 },
  { spec: FOREWING, side: -1, pair: 1 },
  { spec: FOREWING, side: 1, pair: 1 },
];

// A wing's root and its axes: S along the span, C back along the chord, N up
// out of it, and the hinge it swings about.
function wingFrame({ spec, side }) {
  const { sweep, dihedral } = spec;
  const S = [side * Math.cos(sweep) * Math.cos(dihedral), Math.sin(sweep) * Math.cos(dihedral), Math.sin(dihedral)];
  const C = [side * Math.sin(sweep), -Math.cos(sweep), 0];
  let N = cross(S, C);
  if (N[2] < 0) N = scaled(N, -1);
  const root = [side * spec.root[0], spec.root[1], spec.root[2]];
  return { root, side, S, C, N, hinge: unit(cross(S, N)) };
}

// ---------------------------------------------------------------------------

export function mountDragonfly(el, options = {}) {
  const o = { rotate: -1.2, tilt: 0.12, roll: 0.85, fit: 0.97, seed: 3, ...options };
  const calm = reducedMotion();
  const frames = WINGS.map(wingFrame);
  const parts = bodyParts();
  // Model to camera: rolled to show the left flank, turned in the picture plane, tipped back.
  const G = mul(rotX(-o.tilt), mul(rotZ(-o.rotate), rotY(o.roll)));

  let scale = 1, ox = 0, oy = 0, dash = dashSize(1), half = 1;
  let body = null; // the still body, as one path in canvas pixels
  let wings = []; // per wing: dash centres and half dashes in model units
  let clock = 0;

  const surface = mountCanvas(el, build);
  const loop = animate(el, tick);
  surface.measure();

  function build(view) {
    // Fit the dragonfly, with its wings anywhere in their beat, into the element.
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const extend = (q) => {
      const k = DISTANCE / (DISTANCE - q[2]);
      x0 = Math.min(x0, q[0] * k); x1 = Math.max(x1, q[0] * k);
      y0 = Math.min(y0, q[1] * k); y1 = Math.max(y1, q[1] * k);
    };
    for (const part of parts) for (let u = 0; u <= 1; u += 1 / 12) for (let v = 0; v < 1; v += 1 / 12) extend(apply(G, part.surface.at(u, v)));
    for (const limb of limbs()) for (const p of limb.pts) extend(apply(G, p));
    WINGS.forEach((w, i) => {
      for (const angle of [RAISE - SWING[w.pair], RAISE, RAISE + SWING[w.pair]]) {
        const [M, T] = rig(i, angle);
        for (const [s, c] of w.spec.lead.concat(w.spec.trail)) extend(add(apply(M, wingPoint(frames[i], s * w.spec.length, c * w.spec.chord)), T));
      }
    });
    scale = Math.min(view.width / (x1 - x0), view.height / (y1 - y0)) * o.fit;
    ox = view.width / 2 - ((x0 + x1) / 2) * scale;
    oy = view.height / 2 + ((y0 + y1) / 2) * scale;
    dash = dashSize(view.ratio);
    half = (dash.length / scale) * 0.45; // half a dash, in model units
    sample();
    draw();
  }

  // Model point to canvas pixels, through rotation M and shift T.
  function project(M, T, p) {
    const x = M[0] * p[0] + M[1] * p[1] + M[2] * p[2] + T[0];
    const y = M[3] * p[0] + M[4] * p[1] + M[5] * p[2] + T[1];
    const z = M[6] * p[0] + M[7] * p[1] + M[8] * p[2] + T[2];
    const k = (DISTANCE / (DISTANCE - z)) * scale;
    return [ox + x * k, oy - y * k];
  }

  // A wing's rotation and shift, model to camera: twisted `twist` about its
  // span, then swung `angle` about its hinge.
  function rig(i, angle, twist = 0) {
    const f = frames[i], R = mul(axisAngle(f.hinge, angle), axisAngle(f.S, twist * -f.side));
    return [mul(G, R), apply(G, sub(f.root, apply(R, f.root)))];
  }

  // Lays the dashes: the still body once, as a path; the wings as dashes to
  // turn with them every frame.
  function sample() {
    const rand = random(o.seed);
    const L = half / 0.45; // a dash's length in model units
    const T0 = [0, 0, 0];
    body = new Path2D();
    // Like a hand's, every dash is a little longer or shorter than the next.
    const stroke = (p, dir) => {
      const h = half * (0.85 + 0.3 * rand());
      const a = project(G, T0, add(p, scaled(dir, -h))), b = project(G, T0, add(p, scaled(dir, h)));
      body.moveTo(a[0], a[1]);
      body.lineTo(b[0], b[1]);
    };

    // The body: rings of dashes around each part, thinned where the light
    // catches it, as an engraver leaves a highlight.
    parts.forEach((part, index) => {
      hatch(part.surface, L * 0.17, L * 1.0, rand, (p, dir, nrm) => {
        const n = apply(G, nrm);
        if (n[2] < 0.02) return; // facing away
        for (let j = 0; j < parts.length; j++) {
          if (j !== index && parts[j].layer >= part.layer && parts[j].surface.inside(p, parts[j].layer === part.layer ? L * 0.3 : 0)) return;
        }
        if (part.skip && part.skip(p)) return;
        const gloss = Math.max(0, dot(n, HALF)) ** 16;
        if (rand() < 0.5 * smooth(clamp((gloss - 0.35) / 0.5, 0, 1))) return;
        stroke(p, dir);
      });
    });
    for (const limb of limbs()) {
      const path = smoothPath(limb.pts, 4);
      for (let r = 0; r < limb.rows; r++) {
        const lift = (r - (limb.rows - 1) / 2) * L * 0.4;
        walk(path, L * 1.1, L * 0.55 + r * L * 0.5, (p, t) => {
          const side = unit(cross(t, [0, 0, 1]));
          stroke(add(p, scaled(side, lift)), t);
        });
      }
      // Short spines along the shins.
      if (limb.spines) {
        walk(path, L * 2.2, L * 1.1, (p, t) => {
          const out = unit(add(cross(t, [Math.sign(p[0]), 0, 0]), [0, 0, -0.3]));
          stroke(add(p, scaled(out, half * 0.8)), out);
        });
      }
    }

    // The wings, worked out flat and then placed on each wing.
    const thorax = parts.filter((part) => part.layer === 2);
    wings = WINGS.map((w, i) => {
      const f = frames[i], centres = [], dirs = [];
      wingDashes(w.spec, L, rand, (s, c, ds, dc) => {
        const p = wingPoint(f, s, c);
        if (thorax.some((part) => part.surface.inside(p))) return;
        centres.push(...p);
        // A half dash: its direction, a little uneven in length.
        dirs.push(...scaled(unit(add(scaled(f.S, ds), scaled(f.C, dc))), half * (0.85 + 0.3 * rand())));
      });
      return { p: Float32Array.from(centres), d: Float32Array.from(dirs) };
    });
  }

  // Without motion, the drawing made on every resize, wings spread, stands.
  function tick(dt) {
    if (!body || calm) return;
    clock += dt;
    draw();
  }

  function draw() {
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = INK;
    ctx.lineWidth = dash.width;
    ctx.lineCap = 'butt';
    // Wings on the far side go behind the body, the near ones in front. A wing
    // seen edge on would clot into a black blade, so it fades as it turns away.
    const near = [], far = [];
    WINGS.forEach((w, i) => {
      const phase = TAU * (BEAT * clock - (w.pair ? LAG : 0));
      const [M, T] = calm ? rig(i, RAISE) : rig(i, RAISE + SWING[w.pair] * Math.sin(phase), TWIST * Math.cos(phase));
      const N = frames[i].N, facing = Math.abs(M[6] * N[0] + M[7] * N[1] + M[8] * N[2]);
      const path = new Path2D();
      const { p, d } = wings[i];
      for (let j = 0; j < p.length; j += 3) {
        const a = project(M, T, [p[j] - d[j], p[j + 1] - d[j + 1], p[j + 2] - d[j + 2]]);
        const b = project(M, T, [p[j] + d[j], p[j + 1] + d[j + 1], p[j + 2] + d[j + 2]]);
        path.moveTo(a[0], a[1]);
        path.lineTo(b[0], b[1]);
      }
      (M[6] * w.side > 0 ? near : far).push([path, 0.3 + 0.7 * smooth(clamp(facing / 0.45, 0, 1))]);
    });
    const wingsOf = (list) => {
      for (const [path, alpha] of list) {
        ctx.globalAlpha = alpha;
        ctx.stroke(path);
      }
      ctx.globalAlpha = 1;
    };
    wingsOf(far);
    ctx.stroke(body);
    wingsOf(near);
  }

  return {
    // Runs the animation forward by `seconds` at once (for previews and tests).
    advance(seconds) {
      clock += seconds;
      draw();
    },
    destroy() {
      loop.destroy();
      surface.destroy();
    },
  };
}

// ---------------------------------------------------------------------------
// Surfaces. `at(u, v)` gives a point for u in [0, 1] from end to end and v in
// [0, 1) around; `out(p, u)` points outwards; `inside(p, depth)` tests whether
// p lies at least `depth` (roughly) inside.

// An ellipsoid centred at c whose three axes are the columns given, the first
// running from end to end.
function ellipsoid(c, axes) {
  const [A, B, C] = axes, M = [A[0], B[0], C[0], A[1], B[1], C[1], A[2], B[2], C[2]], inv = invert(M);
  const lengths = axes.map((v) => Math.hypot(...v));
  return {
    at(u, v) {
      const t = u * Math.PI, q = v * TAU, s = Math.sin(t);
      return add(c, apply(M, [Math.cos(t), s * Math.cos(q), s * Math.sin(q)]));
    },
    out: (p) => apply(transpose(inv), apply(inv, sub(p, c))), // the gradient, outwards
    inside(p, depth = 0) {
      const q = apply(inv, sub(p, c)), shrink = 1 - depth / Math.min(...lengths);
      return q[0] * q[0] + q[1] * q[1] + q[2] * q[2] < shrink * shrink;
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

// Wraps a surface in rings of dashes, like the hatching of a pen drawing:
// rings `gap` apart from end to end, dashes about `step` apart around each.
// Calls emit(point, direction around, outward normal) for each dash.
function hatch(surface, gap, step, rand, emit) {
  const N = 160, len = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) {
    let d = 0;
    for (const v of [0, 0.25, 0.5, 0.75]) d += Math.hypot(...sub(surface.at(i / N, v), surface.at((i - 1) / N, v)));
    len[i] = len[i - 1] + d / 4;
  }
  const total = len[N];
  const uAt = (s) => {
    let i = 1;
    while (i < N && len[i] < s) i++;
    return (i - 1 + (s - len[i - 1]) / (len[i] - len[i - 1] || 1)) / N;
  };
  const rings = Math.max(1, Math.round(total / gap)), hh = total / rings;
  const M = 96, ring = new Float64Array(M + 1);
  for (let b = 0; b < rings; b++) {
    const u = uAt((b + 0.5) * hh);
    // Even steps of length around the ring, however unevenly v runs.
    for (let k = 1, prev = surface.at(u, 0); k <= M; k++) {
      const next = surface.at(u, k / M);
      ring[k] = ring[k - 1] + Math.hypot(...sub(next, prev));
      prev = next;
    }
    const round = ring[M], count = Math.max(1, Math.round(round / step)), shift = rand();
    for (let j = 0; j < count; j++) {
      const l = ((j + shift) * round) / count;
      let k = 1;
      while (k < M && ring[k] < l) k++;
      const v = (k - 1 + (l - ring[k - 1]) / (ring[k] - ring[k - 1] || 1)) / M;
      const p = surface.at(u, v), e = 1e-3;
      const along = unit(sub(surface.at(Math.min(1, u + e), v), surface.at(Math.max(0, u - e), v)));
      const dv = sub(surface.at(u, v + e), surface.at(u, v - e));
      const around = unit(sub(dv, scaled(along, dot(dv, along))));
      let nrm = cross(around, along);
      if (dot(nrm, surface.out(p, u)) < 0) nrm = scaled(nrm, -1);
      emit(p, around, nrm);
    }
  }
}

// Calls `visit(point, unit tangent)` every `step` along a polyline (2D or 3D),
// starting `offset` in.
function walk(path, step, offset, visit) {
  let need = offset;
  for (let i = 1; i < path.length; i++) {
    const a = path[i - 1], b = path[i], d = b.map((v, j) => v - a[j]), l = Math.hypot(...d);
    if (!l) continue;
    while (need <= l) {
      visit(a.map((v, j) => v + (d[j] * need) / l), d.map((v) => v / l));
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

// Emits a wing's dashes as (s, c, ds, dc): a dash centre and the direction it
// lies along, for dashes `L` long. Bolder parts come first and win where two
// would crowd each other: the stigma, the leading edge, the veins, the
// trailing edge, then a hatching of the membrane across the wing.
function wingDashes(spec, L, rand, emit) {
  const W = spec.chord, length = spec.length;
  const { lead, trail, outline } = wingOutline(spec);
  const widest = Math.max(...outline.map(([s]) => (chordAt(trail, s) ?? 0) - (chordAt(lead, s) ?? 0)));
  const rank = widest / L < 7 ? 0 : widest / L < 11 ? 1 : 2;

  const cells = new Map();
  const crowded = (s, c, gap) => {
    const i = Math.floor(s / L), j = Math.floor(c / L);
    for (let di = -1; di <= 1; di++) {
      for (let dj = -1; dj <= 1; dj++) {
        for (const [ps, pc] of cells.get(`${i + di},${j + dj}`) || []) if ((ps - s) ** 2 + (pc - c) ** 2 < gap * gap) return true;
      }
    }
    return false;
  };
  const put = (s, c, ds, dc, gap) => {
    if (!insidePolygon(outline, s, c) || crowded(s, c, gap)) return;
    const k = `${Math.floor(s / L)},${Math.floor(c / L)}`;
    (cells.get(k) || cells.set(k, []).get(k)).push([s, c]);
    emit(s, c, ds, dc);
  };
  // Rows of dashes along a line, `offsets` across it (positive towards the
  // trailing edge for lines that run root to tip).
  const along = (poly, offsets, gap = L * 0.36) => {
    offsets.forEach((off, r) => {
      walk(poly, L * 1.12, L * (0.56 + 0.5 * r), (p, t) => put(p[0] - t[1] * off, p[1] + t[0] * off, t[0], t[1], gap));
    });
  };

  // The pterostigma, solid.
  const stigma = spec.stigma.map(([s, c]) => [s * length, c * W]);
  const s0 = Math.min(...stigma.map((p) => p[0])), s1 = Math.max(...stigma.map((p) => p[0]));
  for (let c = 0; c < W * 0.13; c += L * 0.36) {
    walk([[s0, c], [s1, c]], L * 1.12, L * 0.56 * (1 + (Math.round(c / (L * 0.36)) & 1)), (p) => insidePolygon(stigma, p[0], p[1]) && put(p[0], p[1], 1, 0, L * 0.3));
  }
  along(lead, [L * 0.3, L * 0.68, L * 1.06]); // the leading edge, bold
  for (const v of spec.veins.filter((vein) => vein.rank <= rank)) along(smoothPath(v.pts.map(([s, c]) => [s * length, c * W]), 6), v.rank ? [-L * 0.15, L * 0.15] : [-L * 0.3, 0, L * 0.3]);
  along(trail.slice().reverse(), [-L * 0.25, -L * 0.6]); // the trailing edge

  // The membrane: dashes across the wing, the way its cross veins run, thinning
  // out towards the root so the wing's base doesn't clot when seen edge on.
  const rowGap = L;
  for (let s = rowGap / 2; s < length; s += rowGap) {
    const c0 = chordAt(lead, s), c1 = chordAt(trail, s);
    if (c0 == null || c1 == null) continue;
    const shift = rand() * L * 1.35, keep = smooth(clamp((s / length - 0.05) / 0.15, 0, 1));
    for (let c = c0 + shift; c < c1; c += L * 1.35) if (rand() < keep) put(s + (rand() - 0.5) * L * 0.2, c, 0, 1, L * 0.45);
  }
}

// ---------------------------------------------------------------------------
// Vectors and 3 × 3 matrices (row by row).

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
function transpose(M) { return [M[0], M[3], M[6], M[1], M[4], M[7], M[2], M[5], M[8]]; }
function invert(M) {
  const [a, b, c, d, e, f, g, h, i] = M;
  const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g, det = a * A + b * B + c * C;
  return [A / det, -(b * i - c * h) / det, (b * f - c * e) / det, B / det, (a * i - c * g) / det, -(a * f - c * d) / det, C / det, -(a * h - b * g) / det, (a * e - b * d) / det];
}
function rotX(a) { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, -s, 0, s, c]; }
function rotY(a) { const c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; }
function rotZ(a) { const c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
function axisAngle(k, a) {
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c, [x, y, z] = k;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}
