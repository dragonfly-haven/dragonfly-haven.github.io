// A coelacanth, Latimeria chalumnae, drawn in tiny dashes like the dragonfly.
// It is modelled in 3D and seen from the side, a little from above and from
// in front: rings of dashes wrap its body like the hatching of a pen drawing,
// thinned where the light falls on it, broken by the edges of its scales and
// left out in the pale spots by which coelacanths know one another. Its eight
// fins are fans of rays in dashes; six of them grow from fleshy, scaled lobes.
// It hangs in the water as coelacanths drift, paddling with its paired fins in
// the diagonal gait of a walking tetrapod (Fricke and others, Nature 1987),
// while its second dorsal and anal fins scull together and its tail waves.
//
//   import { mountCoelacanth } from './animations/coelacanth.js';
//   mountCoelacanth(document.getElementById('coelacanth'));

import { triangleSize, INK, TAU, random, clamp, smooth, reducedMotion, animate } from './core.js';

// A dash for a screen's pixel ratio, in CSS pixels: the same as the dragonfly's.
function dashSize(ratio) {
  const length = triangleSize(ratio) * 1.15;
  return { length, width: Math.max(1 / ratio, length * 0.27) };
}

const DISTANCE = 400; // camera distance in model units, for a gentle perspective
// Towards the light and half-way to the eye, in camera space (x right, y up, z to the viewer).
const LIGHT = unit([-0.45, 0.6, 0.66]);
const HALF = unit([LIGHT[0], LIGHT[1], LIGHT[2] + 1]);

// The fish's form and its drawing; options to mountCoelacanth can vary any of it.
const FORM = {
  yaw: 0.32, // how far it turns its head towards the viewer, radians
  tilt: 0.16, // how far it is seen from above
  rotate: 0, // turned in the picture plane, anticlockwise
  flip: false, // facing right instead of left
  fit: 0.96,
  seed: 7,
  weight: 1, // thickness of the dashes
  ink: 1, // how dark the body is in shadow, 0 to 1
  light: 0.42, // how much the light pales it
  rings: 0.42, // gap between the body's rings of dashes, in dash lengths
  spots: 1, // how many pale spots, as a share of the usual
  speed: 1, // of the fins' beat
};

// ---------------------------------------------------------------------------
// The model. Units: 100 from the tip of the snout to the tip of the tail; a
// station `a` counts along it. +x runs to the tail, +y up and +z out of the
// fish's left side, which faces the viewer; the fish lies about the origin.

// The side view: at each station, the height of the back and of the belly
// above and below the line, and the body's half width.
const OUTLINE = [
  [0, 3.6, -4.6, 4.6],
  [4, 6.2, -7.2, 5.3],
  [8, 8.3, -8.9, 6.0],
  [13, 9.9, -10.2, 6.6],
  [18, 11.3, -11.2, 7.1],
  [24, 12.4, -12.1, 7.4],
  [30, 13.2, -12.8, 7.5],
  [36, 13.5, -13.1, 7.3],
  [42, 13.2, -13.0, 7.0],
  [48, 12.6, -12.6, 6.6],
  [54, 11.8, -11.9, 6.1],
  [60, 10.6, -10.8, 5.4],
  [66, 9.0, -9.2, 4.6],
  [71, 7.6, -7.8, 3.9],
  [76, 6.2, -6.4, 3.2],
  [82, 4.6, -4.8, 2.4],
  [88, 3.2, -3.3, 1.7],
  [93, 2.1, -2.2, 1.2],
  [97, 1.4, -1.45, 0.85],
  [100, 0.85, -0.9, 0.5],
];
const NOSE = 4.2, TIP = 1.2; // how far the snout and the tail's tip round off

// The head: the eye; the gape of the mouth; the hind edge of the gill cover,
// behind which the scales begin; and the bony plates of the cheek, as lines of
// stations and heights.
const EYE = { a: 8.4, y: 2.7, r: 2.3 };
const MOUTH = [[0.5, -2.3], [3, -3.7], [6.5, -5.0], [10.5, -6.3], [12.6, -7.0]];
const GILL = [[18.6, 11.2], [21.2, 7.6], [23.0, 2.4], [23.4, -2.8], [22.4, -7.6], [20.2, -10.9]];
const CHEEK = [
  [[4.6, -0.6], [8.2, -1.6], [12.2, -0.6], [13.6, 2.4], [13.0, 6.8]], // under and behind the eye
  [[13.6, 2.4], [17.4, 3.0], [21.6, 4.2]],
  [[12.2, -0.6], [14.8, -4.0], [15.6, -8.6]],
];

// The fins. Lobed fins grow from a scaled lobe, with rays around its far half
// like a paddle: `at` the station and height of the root, `angle` the way it
// points in side view (radians up from the tail-ward line), `out` how far it
// stands off the flank, `length` of the whole fin, `lobe` of the lobe and `r`
// its radius at root and tip, `wide` how far the rays reach either side.
const LOBED = {
  pectoral: { at: [25.2, -4.0], angle: -0.62, out: 0.4, length: 17.5, lobe: 8.8, r: [2.3, 1.0], wide: [2.9, 3.8], rays: 34 },
  pelvic: { at: [46.4, -10.6], angle: -0.72, out: 0.32, length: 13, lobe: 6.2, r: [1.9, 0.85], wide: [2.3, 3.1], rays: 28 },
  dorsal: { at: [58.2, 'top'], angle: 0.7, out: 0, length: 12.5, lobe: 5.6, r: [2.1, 0.95], wide: [3.4, 3.4], rays: 30 },
  anal: { at: [59.6, 'bottom'], angle: -0.7, out: 0, length: 12.5, lobe: 5.6, r: [2.1, 0.95], wide: [3.4, 3.4], rays: 30 },
};
// Fans of rays that stand in the fish's middle plane: from a run of stations
// along its back or belly (`from`, `to`, on `edge`) out to a rim (side view).
const FANS = {
  // The first dorsal fin: stiff, spined rays, its membrane notched between them.
  spines: { edge: 'top', from: 33.6, to: 39.6, rim: [[36.2, 26.6], [38.7, 26.8], [41.0, 25.3], [42.8, 22.7], [44.0, 19.6], [44.5, 16.8], [44.0, 14.6]], rays: 9, notch: 0.86, bold: true },
  // The tail: an upper and a lower lobe, and the little lobe between them at the tip.
  upper: { edge: 'top', from: 70.6, to: 92.4, rim: [[70.6, 'edge'], [74.6, 10.4], [79.6, 13.4], [84.4, 15.2], [87.6, 15.3], [90.0, 12.6], [91.6, 7.6], [92.4, 'edge']], rays: 28 },
  lower: { edge: 'bottom', from: 70.6, to: 92.4, rim: [[70.6, 'edge'], [74.6, -10.7], [79.6, -13.7], [84.4, -15.5], [87.6, -15.6], [90.0, -12.9], [91.6, -7.9], [92.4, 'edge']], rays: 28 },
  tassel: { edge: 'top', from: 92.8, to: 99.8, rim: [[92.8, 'edge'], [94.4, 3.9], [97.4, 3.8], [100.2, 2.5], [102.0, 0.1]], rays: 13 },
  tassel2: { edge: 'bottom', from: 92.8, to: 99.8, rim: [[92.8, 'edge'], [94.4, -4.0], [97.4, -3.9], [100.2, -2.6], [102.0, -0.2]], rays: 13 },
};

// The beat. The paired fins paddle in counterstroke, the left pectoral with
// the right pelvic and the other two half a beat later, sweeping forward and
// out, then back and in, and feathering as they turn; the second dorsal and
// anal fins swing from side to side together; the tail waves, slowest of all.
// The tips trail their roots, so the fins bend as they beat.
const PADDLE = { period: 2.6, swing: 0.42, spread: 0.2, feather: 0.55, lag: 1.1 };
const SCULL = { period: 1.9, swing: 0.5, lag: 1.2 };
const WAVE = { period: 3.2, amplitude: 2.4, wavelength: 34 };
const LEVELS = 16; // steps from root to tip in which a fin's bend is worked out each frame

// ---------------------------------------------------------------------------

export function mountCoelacanth(el, options = {}) {
  const o = { ...FORM, ...options };
  const calm = reducedMotion();
  const body = bodyShape();
  // Model to camera: turned to show a little of the head and back, mirrored
  // to face right if asked, then turned in the picture plane.
  const G = mul(rotZ(o.rotate), mul([o.flip ? -1 : 1, 0, 0, 0, 1, 0, 0, 0, 1], mul(rotX(o.tilt), rotY(o.yaw))));
  const fins = makeFins(body, o);

  let lay = null, clock = 0, loop = null, playing = !calm;
  const surface = mountSurface(el, (view) => {
    lay = layout(view);
    draw();
  });
  surface.measure();
  if (!calm) loop = animate(el, (dt) => {
    if (!playing) return;
    clock += Math.min(dt, 1 / 30) * o.speed;
    draw();
  });

  // Where the fish sits in the canvas, its still body drawn once into a
  // canvas of its own, its outline as a mask, and each fin's dashes.
  function layout(view) {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const extend = (q) => {
      const k = DISTANCE / (DISTANCE - q[2]);
      x0 = Math.min(x0, q[0] * k); x1 = Math.max(x1, q[0] * k);
      y0 = Math.min(y0, q[1] * k); y1 = Math.max(y1, q[1] * k);
    };
    for (let a = 0; a <= 100; a += 0.5) for (let v = 0; v < 1; v += 1 / 24) extend(apply(G, body.at(a, v * TAU)));
    for (let k = 0; k < 12; k++) for (const fin of fins) for (const p of fin.reach(k / 12)) extend(apply(G, p));
    const { width, height, ratio } = view;
    const scale = Math.min(width / (x1 - x0), height / (y1 - y0)) * o.fit;
    const next = {
      width, height, ratio, scale,
      ox: width / 2 - ((x0 + x1) / 2) * scale,
      oy: height / 2 + ((y0 + y1) / 2) * scale,
      dash: dashSize(ratio),
      G,
    };
    const L = next.dash.length / scale; // a dash's length in model units
    const rand = random(o.seed);
    const project = (p) => {
      const q = apply(G, p), k = (DISTANCE / (DISTANCE - q[2])) * scale;
      return [next.ox + q[0] * k, next.oy - q[1] * k];
    };
    next.body = drawBody(body, G, o, L, project, rand, next);
    next.mask = drawMask(body, project, next);
    next.fins = fins.map((fin) => fin.sample(L, rand, G));
    return next;
  }

  function draw() {
    if (!lay) return;
    const { ctx, canvas, width, height, ratio } = surface.view;
    const kx = (ratio * width) / lay.width, ky = (ratio * height) / lay.height;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(kx, 0, 0, ky, 0, 0);
    ctx.strokeStyle = ctx.fillStyle = INK;
    ctx.lineCap = 'butt';
    ctx.lineJoin = 'round';
    const t = clock;
    const poses = fins.map((fin) => fin.pose(t, G));
    // The fins on the far side, then the body over them, hiding what it covers.
    fins.forEach((fin, i) => fin.far && drawFin(ctx, lay, fin, lay.fins[i], poses[i]));
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'destination-out';
    ctx.drawImage(lay.mask, 0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = 'source-over';
    ctx.drawImage(lay.body, 0, 0, canvas.width, canvas.height);
    ctx.setTransform(kx, 0, 0, ky, 0, 0);
    // Then the fins in the middle plane and on the near side, each clearing
    // the body behind it.
    fins.forEach((fin, i) => !fin.far && drawFin(ctx, lay, fin, lay.fins[i], poses[i]));
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  return {
    // Holds the fins still, or lets them beat again; and sets how fast they beat.
    pause() {
      playing = false;
    },
    play() {
      playing = !calm;
    },
    setSpeed(speed) {
      o.speed = speed;
    },
    // Runs the fins on by `seconds` at once (for previews and tests).
    advance(seconds) {
      clock += seconds;
      draw();
    },
    destroy() {
      if (loop) loop.destroy();
      surface.destroy();
    },
  };
}

// ---------------------------------------------------------------------------
// The body: its shape, its dashes and its outline.

function bodyShape() {
  const col = (k) => monotone(OUTLINE.map((r) => r[0]), OUTLINE.map((r) => r[k]));
  const top = col(1), bottom = col(2), half = col(3);
  const round = (a) => {
    const n = 1 - clamp(a / NOSE, 0, 1), t = 1 - clamp((100 - a) / TIP, 0, 1);
    return Math.sqrt(Math.max(0, 1 - n * n)) * Math.sqrt(Math.max(0, 1 - t * t));
  };
  const RES = 20, N = 100 * RES;
  const tab = (f) => {
    const t = new Float64Array(N + 1);
    for (let i = 0; i <= N; i++) t[i] = f(i / RES);
    return (a) => {
      const x = clamp(a, 0, 100) * RES, i = Math.min(N - 1, Math.floor(x)), k = x - i;
      return t[i] + (t[i + 1] - t[i]) * k;
    };
  };
  const yc = tab((a) => (top(a) + bottom(a)) / 2);
  const h = tab((a) => ((top(a) - bottom(a)) / 2) * round(a));
  const w = tab((a) => half(a) * round(a));
  // Each scale's size follows the body's girth, so the scales shrink towards the tail.
  const girth = (a) => Math.max(0.6, (h(a) + w(a)) / 2);
  const sig = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) sig[i] = sig[i - 1] + 1 / RES / girth((i - 0.5) / RES);
  const sigma = (a) => {
    const x = clamp(a, 0, 100) * RES, i = Math.min(N - 1, Math.floor(x));
    return sig[i] + (sig[i + 1] - sig[i]) * (x - i);
  };
  return {
    yc, h, w, girth, sigma,
    top: (a) => yc(a) + h(a),
    bottom: (a) => yc(a) - h(a),
    // The point at station a, angle θ round from the top towards the viewer.
    at: (a, q) => [a - 50, yc(a) + h(a) * Math.cos(q), w(a) * Math.sin(q)],
  };
}

function drawBody(body, G, o, L, project, rand, next) {
  const path = new Path2D(), thin = new Path2D();
  const stroke = (into, p, dir, len = 1) => {
    const hl = L * 0.45 * len * (0.85 + 0.3 * rand());
    const a = project(add(p, scaled(dir, -hl))), b = project(add(p, scaled(dir, hl)));
    into.moveTo(a[0], a[1]);
    into.lineTo(b[0], b[1]);
  };
  const spots = makeSpots(body, random(o.seed + 1), o.spots);
  const gap = Math.max(0.1, L * 0.42); // half the width of a pale line
  const eye = eyeFrame(body);

  // The scales lie in a quincunx, ROWS of them round the body, staggered
  // along it; each overlaps the one behind it, so its hind edge shows.
  const ROWS = 28, D = TAU / ROWS, RS = 0.72;
  const scaleEdge = (a, q) => {
    const size = body.girth(a) * D;
    if (size < L * 4.5) return false;
    const s = body.sigma(a) / D, t = q / D, j0 = Math.floor(t);
    let best = Infinity, bestD = 0;
    for (let j = j0 - 1; j <= j0 + 2; j++) {
      const off = (j & 1) * 0.5, i0 = Math.floor(s - off);
      for (let i = i0 - 1; i <= i0 + 2; i++) {
        const d = Math.hypot(s - i - off, t - j);
        if (d < RS && i + off < best) {
          best = i + off;
          bestD = d;
        }
      }
    }
    return RS - bestD < gap / size;
  };
  const gillAt = (y) => lineAt(GILL, y);
  const near = (pts, a, y, width) => distanceTo(pts, a, y) < width;

  hatch((u, v) => body.at(u * 100, v * TAU), (p, u) => sub(p, [u * 100 - 50, body.yc(u * 100), 0]), L * o.rings, L * 1.12, rand, (p, dir, nrm, u, v) => {
    const n = apply(G, nrm);
    if (n[2] < 0.02) return; // facing away
    const a = u * 100, q = v * TAU, y = p[1], side = p[2] > 0;
    if (side) {
      const de = Math.hypot(a - EYE.a, y - EYE.y);
      if (de < EYE.r * 1.16 + gap) return;
      if (near(MOUTH, a, y, gap * 1.1)) return;
      if (near(GILL, a, y, gap)) return;
      if (CHEEK.some((line) => near(line, a, y, gap * 0.8))) return;
    }
    if (a > gillAt(y) + gap && scaleEdge(a, q)) return;
    if (rand() < spotAt(spots, body, a, q, L)) return;
    const diffuse = Math.max(0, dot(n, LIGHT));
    const gloss = Math.max(0, dot(n, HALF)) ** 14;
    const ink = o.ink - o.light * diffuse ** 2 - 0.55 * smooth(clamp((gloss - 0.3) / 0.5, 0, 1));
    if (rand() > ink) return;
    stroke(path, p, dir);
  });

  // The eye: a black pupil in rings of dashes, with a glint, inside a paler iris and a rim.
  const { c, e1, e2, nrm } = eye;
  const on = (x, y) => add(c, add(add(scaled(e1, x), scaled(e2, y)), scaled(nrm, 0.5 * (1 - (x * x + y * y) / (EYE.r * EYE.r)))));
  const pupil = EYE.r * 0.56, glint = [-pupil * 0.36, pupil * 0.38];
  for (let r = L * 0.25; r < pupil; r += L * 0.3) {
    const count = Math.max(3, Math.round((TAU * r) / (L * 0.95))), shift = rand();
    for (let k = 0; k < count; k++) {
      const q = ((k + shift) / count) * TAU, x = r * Math.cos(q), y = r * Math.sin(q);
      if (Math.hypot(x - glint[0], y - glint[1]) < pupil * 0.3) continue;
      stroke(path, on(x, y), unit(add(scaled(e1, -Math.sin(q)), scaled(e2, Math.cos(q)))));
    }
  }
  for (let r = pupil + L * 0.55; r < EYE.r * 0.9; r += L * 0.55) {
    const count = Math.round((TAU * r) / (L * 0.9));
    for (let k = 0; k < count; k++) {
      const q = ((k + rand()) / count) * TAU;
      if (rand() < 0.45) continue;
      stroke(thin, on(r * Math.cos(q), r * Math.sin(q)), unit(add(scaled(e1, Math.cos(q)), scaled(e2, Math.sin(q)))), 0.7);
    }
  }
  {
    const r = EYE.r, count = Math.round((TAU * r) / (L * 1.05));
    for (let k = 0; k < count; k++) {
      const q = (k / count) * TAU;
      stroke(path, on(r * Math.cos(q), r * Math.sin(q)), unit(add(scaled(e1, -Math.sin(q)), scaled(e2, Math.cos(q)))));
    }
  }

  const canvas = document.createElement('canvas');
  canvas.width = Math.round(next.width * next.ratio);
  canvas.height = Math.round(next.height * next.ratio);
  const g = canvas.getContext('2d');
  g.setTransform(next.ratio, 0, 0, next.ratio, 0, 0);
  g.strokeStyle = INK;
  g.lineCap = 'butt';
  g.lineWidth = next.dash.width * o.weight;
  g.stroke(path);
  g.lineWidth = next.dash.width * o.weight * 0.7;
  g.stroke(thin);
  return canvas;
}

// The body's outline, filled: what it hides of the fins on its far side.
function drawMask(body, project, next) {
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(next.width * next.ratio);
  canvas.height = Math.round(next.height * next.ratio);
  const g = canvas.getContext('2d');
  g.setTransform(next.ratio, 0, 0, next.ratio, 0, 0);
  g.fillStyle = '#000';
  const step = 0.6 / next.scale;
  for (let a = 0; a <= 100; a += step) {
    g.beginPath();
    for (let k = 0; k < 48; k++) {
      const p = project(body.at(a, (k / 48) * TAU));
      if (k) g.lineTo(p[0], p[1]);
      else g.moveTo(p[0], p[1]);
    }
    g.fill();
  }
  return canvas;
}

// Where the eye sits on the head, and the plane it lies in.
function eyeFrame(body) {
  const { a, y } = EYE;
  const q = Math.acos(clamp((y - body.yc(a)) / body.h(a), -1, 1));
  const c = body.at(a, q);
  const e = 0.01;
  const da = sub(body.at(a + e, q), body.at(a - e, q)), dq = sub(body.at(a, q + e), body.at(a, q - e));
  let nrm = unit(cross(dq, da));
  if (nrm[2] < 0) nrm = scaled(nrm, -1);
  const e1 = unit(sub(da, scaled(nrm, dot(da, nrm))));
  const e2 = cross(nrm, e1);
  return { c, e1: e1[0] < 0 ? scaled(e1, -1) : e1, e2: e2[1] < 0 ? scaled(e2, -1) : e2, nrm };
}

// The pale spots, scattered over the body, irregular and each its own shape.
function makeSpots(body, rand, amount) {
  const spots = [];
  const want = Math.round(64 * amount);
  for (let tries = 0; tries < 6000 && spots.length < want; tries++) {
    const a = 2 + rand() * 90, q = rand() * TAU, R = body.girth(a);
    const r = (0.55 + rand() * rand() * 1.7) * clamp(R / 9, 0.45, 1.1);
    const clear = spots.every((s) => {
      const t = wrap(q - s.q) * R;
      return Math.hypot(a - s.a, t) > (r + s.r) * 1.6 + 1.2;
    });
    if (!clear) continue;
    spots.push({ a, q, r, k: [rand() * TAU, rand() * TAU, rand() * TAU], e: [0.3 * rand(), 0.2 * rand(), 0.12 * rand()], stretch: 0.7 + 0.6 * rand() });
  }
  return spots;
}

// How surely a point at station a, angle θ, is pale: 1 inside a spot, 0 well outside.
function spotAt(spots, body, a, q, L) {
  const R = body.girth(a);
  let most = 0;
  for (const s of spots) {
    const da = (a - s.a) / s.stretch;
    if (Math.abs(da) > s.r * 2.5) continue;
    const dt = wrap(q - s.q) * R;
    const d = Math.hypot(da, dt), ang = Math.atan2(dt, da);
    const edge = s.r * (1 + s.e[0] * Math.cos(2 * ang + s.k[0]) + s.e[1] * Math.cos(3 * ang + s.k[1]) + s.e[2] * Math.cos(5 * ang + s.k[2]));
    const soft = Math.max(L * 0.6, 0.15);
    most = Math.max(most, clamp((edge - d) / soft + 0.5, 0, 1));
  }
  return most;
}

// ---------------------------------------------------------------------------
// The fins. Each is laid out once in its own frame and posed every frame.

function makeFins(body, o) {
  const fins = [];
  const paddle = (name, far, phase) => fins.push(lobedFin(body, LOBED[name], far, phase, PADDLE));
  // The diagonal gait: the near pectoral with the far pelvic, the far pectoral with the near pelvic.
  paddle('pectoral', true, 0.5);
  paddle('pelvic', true, 0);
  fins.push(fanFin(body, FANS.spines, 0.1));
  fins.push(fanFin(body, FANS.upper, 0));
  fins.push(fanFin(body, FANS.lower, 0));
  fins.push(fanFin(body, FANS.tassel, 0));
  fins.push(fanFin(body, FANS.tassel2, 0));
  fins.push(lobedFin(body, LOBED.dorsal, false, 0, SCULL));
  fins.push(lobedFin(body, LOBED.anal, false, 0, SCULL));
  paddle('pelvic', false, 0.5);
  paddle('pectoral', false, 0);
  return fins;
}

// A lobed fin in its own frame: s along it from the root, c across it in its
// plane and n out of its plane.
function lobedFin(body, spec, far, phase, beat) {
  const { length: F, lobe: Ls, r: [r0, r1], wide, angle, out } = spec;
  const [a, at] = spec.at;
  // The root, on the body's surface.
  let root;
  if (at === 'top') root = [a - 50, body.top(a) - 0.4, 0];
  else if (at === 'bottom') root = [a - 50, body.bottom(a) + 0.4, 0];
  else {
    const q = Math.acos(clamp((at - body.yc(a)) / body.h(a), -1, 1));
    root = body.at(a, q);
    root = sub(root, scaled(unit([0, 0, 1]), 0.4));
  }
  const side = out !== 0 || (at !== 'top' && at !== 'bottom');
  const S = unit([Math.cos(angle) * Math.cos(out), Math.sin(angle) * Math.cos(out), Math.sin(out)]);
  const N = unit(side ? sub([0, 0, 1], scaled(S, S[2])) : [0, 0, 1]);
  const C = cross(N, S);
  const R0 = [S[0], C[0], N[0], S[1], C[1], N[1], S[2], C[2], N[2]]; // columns s, c, n
  // The lobe's radius along it, rounding off at its tip.
  const radius = (s) => {
    const r = r0 + (r1 - r0) * clamp(s / Ls, 0, 1), cap = Ls - r1 * 1.4;
    return s <= cap ? r : r * Math.sqrt(Math.max(0, 1 - ((s - cap) / (Ls - cap)) ** 2));
  };
  // The paddle: a rounded outline round the lobe's far part, from where the
  // rays begin on its lead side, round the fin's tip, back to its trail side.
  const first = Ls * 0.3, begin = -Ls * 0.1, mid = (begin + F) / 2, A = (F - begin) / 2;
  const reachAt = (s, k) => {
    const x = Math.abs((s - mid) / A);
    return x >= 1 ? 0 : wide[k] * (1 - x ** 2.4) ** (1 / 2.4);
  };
  const rim = [];
  for (let k = 0; k <= 40; k++) {
    const s = first + ((F - first) * k) / 40;
    rim.push([s, -reachAt(s, 0)]);
  }
  for (let k = 40; k >= 0; k--) {
    const s = first + ((F - first) * k) / 40;
    rim.push([s, reachAt(s, 1)]);
  }
  // The rays: evenly spaced round the rim, each from the lobe's edge.
  const lengths = [0];
  for (let k = 1; k < rim.length; k++) lengths.push(lengths[k - 1] + Math.hypot(rim[k][0] - rim[k - 1][0], rim[k][1] - rim[k - 1][1]));
  const total = lengths[lengths.length - 1];
  const rimAt = (d) => {
    let k = 1;
    while (k < lengths.length - 1 && lengths[k] < d) k++;
    const f = (d - lengths[k - 1]) / (lengths[k] - lengths[k - 1] || 1);
    return [rim[k - 1][0] + (rim[k][0] - rim[k - 1][0]) * f, rim[k - 1][1] + (rim[k][1] - rim[k - 1][1]) * f];
  };
  const rays = [];
  for (let k = 0; k < spec.rays; k++) {
    const f = (k + 0.5) / spec.rays;
    const tip = rimAt(f * total);
    const g = f < 0.5 ? f / 0.5 : (1 - f) / 0.5; // 0 where the rays begin, 1 at the fin's tip
    const s = first + (Ls - first) * g ** 0.8, c = (f < 0.5 ? -1 : 1) * radius(s) * 0.85;
    rays.push([[s, c], tip]);
  }
  const outline = [];
  // What it clears of the body behind it: all but the lobe's root, which grows from the body.
  const clearFrom = r0 * 0.7;
  for (let s = clearFrom; s < first; s += 0.5) outline.push([s, -radius(s)]);
  outline.push(...rim);
  for (let s = first; s > clearFrom; s -= 0.5) outline.push([s, radius(s)]);

  const pose = (t, G) => {
    const p = TAU * (t / beat.period + phase);
    const M = [];
    for (let l = 0; l <= LEVELS; l++) {
      const q = p - beat.lag * (l / LEVELS);
      let W;
      if (beat === PADDLE) {
        // Forward and out, back and in: the tip sweeps a loop; it feathers as it turns.
        const sw = -beat.swing * Math.sin(q), sp = beat.spread * Math.cos(q), fe = beat.feather * Math.cos(q + 0.4);
        const spreadAxis = unit(cross(S, [0, 0, 1]));
        W = mul(rotZ(sw), mul(axisAngle(spreadAxis, sp), mul(R0, rotX(fe))));
      } else {
        // From side to side about the body's long axis, a little back and forth.
        W = mul(rotX(beat.swing * Math.sin(q)), mul(rotZ(0.08 * Math.cos(q) * Math.sign(angle)), R0));
      }
      const CM = mul(G, far ? mul([1, 0, 0, 0, 1, 0, 0, 0, -1], W) : W);
      M.push(CM);
    }
    const T = apply(G, far ? [root[0], root[1], -root[2]] : root);
    return { M, T };
  };

  // The farthest the fin reaches, at a share k of its beat, in model space.
  const reach = (k) => {
    const p = k * beat.period;
    const { M } = pose(p, [1, 0, 0, 0, 1, 0, 0, 0, 1]);
    const base = far ? [root[0], root[1], -root[2]] : root;
    return outline.filter((_, i) => i % 4 === 0).map(([s, c]) => add(base, apply(M[levelOf(s)], [s, c, 0])));
  };
  const levelOf = (s) => clamp(Math.round((s / F) * LEVELS), 0, LEVELS);

  // Laid out in dashes for dashes `L` long.
  const sample = (L, rand, G) => {
    const lines = [], membrane = [], lobe = [];
    const dashAlong = (into, a, b, step, len, drop = 0) => {
      walk([a, b], step, step * (0.3 + 0.4 * rand()), (p, t) => {
        if (rand() < drop) return;
        const h = L * 0.45 * len * (0.85 + 0.3 * rand());
        into.push(p[0] - t[0] * h, p[1] - t[1] * h, levelOf(p[0] - t[0] * h), p[0] + t[0] * h, p[1] + t[1] * h, levelOf(p[0] + t[0] * h));
      });
    };
    for (const [from, to] of rays) dashAlong(lines, from, to, L * 1.08, 1);
    // Fine membrane between the rays, along them.
    for (let k = 0; k < rays.length - 1; k++) {
      const [a0, b0] = rays[k], [a1, b1] = rays[k + 1];
      const wideBy = Math.hypot(b1[0] - b0[0], b1[1] - b0[1]);
      const n = Math.max(0, Math.floor(wideBy / (L * 0.8)));
      for (let m = 1; m <= n; m++) {
        const f = m / (n + 1), mix = (u, w) => [u[0] + (w[0] - u[0]) * f, u[1] + (w[1] - u[1]) * f];
        dashAlong(membrane, mix(a0, a1), mix(b0, b1), L * 1.25, 0.8, 0.15);
      }
    }
    // The lobe: rings of dashes round it, thinned where the light falls.
    hatch(
      (u, v) => {
        const s = -0.3 + u * (Ls + 0.3), r = radius(s), q = v * TAU;
        return [s, r * Math.cos(q), 0.72 * r * Math.sin(q)];
      },
      (p) => [0, p[1], p[2]],
      L * 0.55,
      L * 1.1,
      rand,
      (p, dir, nrm) => {
        const n = apply(G, apply(R0, nrm));
        const diffuse = Math.max(0, dot(n, LIGHT));
        if (rand() > 1 - 0.45 * diffuse ** 2) return;
        const h = L * 0.45 * (0.85 + 0.3 * rand());
        const a = sub(p, scaled(dir, h)), b = add(p, scaled(dir, h));
        lobe.push(a[0], a[1], a[2], b[0], b[1], b[2], nrm[0], nrm[1], nrm[2], levelOf(p[0]));
      },
    );
    return {
      lines: Float32Array.from(lines),
      membrane: Float32Array.from(membrane),
      lobe: Float32Array.from(lobe),
      outline: outline.map(([s, c]) => [s, c, levelOf(s)]),
      axis: [[clearFrom + r0 * 0.4, 0, levelOf(clearFrom)], [Ls * 0.8, 0, levelOf(Ls * 0.8)]],
      lobeWidth: r0 * 1.9,
    };
  };

  return { kind: 'lobed', far, pose, reach, sample, clear: !far };
}

// A fan of rays in the fish's middle plane, waving from side to side.
function fanFin(body, spec, phase) {
  const edgeY = (a) => (spec.edge === 'top' ? body.top(a) - 0.25 : body.bottom(a) + 0.25);
  const rimPts = spec.rim.map(([a, y]) => [a - 50, y === 'edge' ? edgeY(a) : y]);
  const rim = smoothPath(rimPts, 10);
  const lengths = [0];
  for (let k = 1; k < rim.length; k++) lengths.push(lengths[k - 1] + Math.hypot(rim[k][0] - rim[k - 1][0], rim[k][1] - rim[k - 1][1]));
  const total = lengths[lengths.length - 1];
  const rimAt = (d) => {
    let k = 1;
    while (k < lengths.length - 1 && lengths[k] < d) k++;
    const f = (d - lengths[k - 1]) / (lengths[k] - lengths[k - 1] || 1);
    return [rim[k - 1][0] + (rim[k][0] - rim[k - 1][0]) * f, rim[k - 1][1] + (rim[k][1] - rim[k - 1][1]) * f];
  };
  const rays = [];
  for (let k = 0; k < spec.rays; k++) {
    const f = spec.rim[0][1] === 'edge' ? (k + 1) / (spec.rays + 1) : k / (spec.rays - 1);
    const a = spec.from + (spec.to - spec.from) * f;
    rays.push([[a - 50, edgeY(a)], rimAt(f * total)]);
  }
  const outline = [[spec.from - 50, edgeY(spec.from)], ...rim, [spec.to - 50, edgeY(spec.to)]];

  // Each point sways out of the middle plane by a wave that runs back along the
  // fish, growing towards the fin's rim.
  const k = TAU / WAVE.wavelength;
  const sway = (x, f, t) => WAVE.amplitude * (spec.bold ? 0.25 : 1) * f ** 1.5 * Math.sin(TAU * (t / WAVE.period + phase) - k * (x + 50));

  const pose = (t) => ({ t });
  const reach = (kk) => outline.map(([x, y]) => [x, y, sway(x, 1, kk * WAVE.period)]);
  const sample = (L, rand) => {
    const lines = [], membrane = [];
    const along = (into, a, b, step, len, stop = 1, drop = 0) => {
      const total = Math.hypot(b[0] - a[0], b[1] - a[1]);
      walk([a, b], step, step * (0.3 + 0.4 * rand()), (p, t) => {
        if (rand() < drop) return;
        const h = L * 0.45 * len * (0.85 + 0.3 * rand());
        const f0 = Math.hypot(p[0] - a[0], p[1] - a[1]) / total;
        if (f0 > stop) return;
        const fa = clamp(f0 - h / total, 0, 1), fb = clamp(f0 + h / total, 0, 1);
        into.push(p[0] - t[0] * h, p[1] - t[1] * h, fa, p[0] + t[0] * h, p[1] + t[1] * h, fb);
      });
    };
    for (const [a, b] of rays) {
      // Stiff spines are drawn in two rows of dashes.
      if (!spec.bold) {
        along(lines, a, b, L * 1.08, 1);
        continue;
      }
      const l = Math.hypot(b[0] - a[0], b[1] - a[1]), nx = (-(b[1] - a[1]) / l) * L * 0.28, ny = ((b[0] - a[0]) / l) * L * 0.28;
      for (const k of [-1, 1]) along(lines, [a[0] + nx * k, a[1] + ny * k], [b[0] + nx * k, b[1] + ny * k], L * 1.08, 1);
    }
    for (let m = 0; m < rays.length - 1; m++) {
      const [a0, b0] = rays[m], [a1, b1] = rays[m + 1];
      const n = Math.max(0, Math.floor(Math.hypot(b1[0] - b0[0], b1[1] - b0[1]) / (L * 0.8)));
      for (let j = 1; j <= n; j++) {
        const f = j / (n + 1), mix = (u, w) => [u[0] + (w[0] - u[0]) * f, u[1] + (w[1] - u[1]) * f];
        // The first dorsal's membrane stops short between its spines.
        const stop = spec.notch ? spec.notch + (1 - spec.notch) * (1 - Math.sin(Math.PI * f)) : 1;
        along(membrane, mix(a0, a1), mix(b0, b1), L * 1.25, 0.8, stop, 0.15);
      }
    }
    return { lines: Float32Array.from(lines), membrane: Float32Array.from(membrane), sway };
  };
  return { kind: 'fan', far: false, pose, reach, sample, clear: false, bold: spec.bold };
}

// Strokes a fin as it is posed now.
function drawFin(ctx, lay, fin, dashes, pose) {
  const { scale, ox, oy, dash } = lay;
  const width = dash.width;
  const toScreen = (q, out) => {
    const k = (DISTANCE / (DISTANCE - q[2])) * scale;
    out[0] = ox + q[0] * k;
    out[1] = oy - q[1] * k;
    return out;
  };
  const A = [0, 0], B = [0, 0];
  if (fin.kind === 'fan') {
    const t = pose.t;
    const G = lay.G;
    const strokeAll = (arr, w) => {
      ctx.lineWidth = width * w;
      ctx.beginPath();
      for (let i = 0; i < arr.length; i += 6) {
        toScreen(apply(G, [arr[i], arr[i + 1], dashes.sway(arr[i], arr[i + 2], t)]), A);
        toScreen(apply(G, [arr[i + 3], arr[i + 4], dashes.sway(arr[i + 3], arr[i + 5], t)]), B);
        ctx.moveTo(A[0], A[1]);
        ctx.lineTo(B[0], B[1]);
      }
      ctx.stroke();
    };
    strokeAll(dashes.lines, 1.1);
    strokeAll(dashes.membrane, 0.75);
    return;
  }
  const { M, T } = pose;
  const place = (s, c, n, l, out) => {
    const m = M[l];
    return toScreen([T[0] + m[0] * s + m[1] * c + m[2] * n, T[1] + m[3] * s + m[4] * c + m[5] * n, T[2] + m[6] * s + m[7] * c + m[8] * n], out);
  };
  if (fin.clear) {
    // Clears the body behind the fin, with a hair of margin, so it reads in front.
    const outline = new Path2D();
    dashes.outline.forEach(([s, c, l], i) => {
      place(s, c, 0, l, A);
      if (i) outline.lineTo(A[0], A[1]);
      else outline.moveTo(A[0], A[1]);
    });
    outline.closePath();
    const [p, q] = dashes.axis;
    place(p[0], 0, 0, p[2], A);
    place(q[0], 0, 0, q[2], B);
    ctx.globalCompositeOperation = 'destination-out';
    ctx.fill(outline);
    ctx.lineWidth = width * 2.2;
    ctx.stroke(outline);
    ctx.lineWidth = dashes.lobeWidth * scale + width * 2;
    ctx.beginPath();
    ctx.moveTo(A[0], A[1]);
    ctx.lineTo(B[0], B[1]);
    ctx.stroke();
    ctx.globalCompositeOperation = 'source-over';
  }
  const strokeAll = (arr, w) => {
    ctx.lineWidth = width * w;
    ctx.beginPath();
    for (let i = 0; i < arr.length; i += 6) {
      place(arr[i], arr[i + 1], 0, arr[i + 2], A);
      place(arr[i + 3], arr[i + 4], 0, arr[i + 5], B);
      ctx.moveTo(A[0], A[1]);
      ctx.lineTo(B[0], B[1]);
    }
    ctx.stroke();
  };
  strokeAll(dashes.lines, 1.1);
  strokeAll(dashes.membrane, 0.75);
  // The lobe, leaving out its far side.
  const arr = dashes.lobe;
  ctx.lineWidth = width;
  ctx.beginPath();
  for (let i = 0; i < arr.length; i += 10) {
    const m = M[arr[i + 9]];
    if (m[6] * arr[i + 6] + m[7] * arr[i + 7] + m[8] * arr[i + 8] < 0.02) continue;
    place(arr[i], arr[i + 1], arr[i + 2], arr[i + 9], A);
    place(arr[i + 3], arr[i + 4], arr[i + 5], arr[i + 9], B);
    ctx.moveTo(A[0], A[1]);
    ctx.lineTo(B[0], B[1]);
  }
  ctx.stroke();
}

// ---------------------------------------------------------------------------
// Drawing helpers.

// Fills `el` with a canvas drawn at the screen's full pixel ratio (up to 3),
// in whole device pixels so that nothing is resampled; as the dragonfly's.
function mountSurface(el, onResize) {
  if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
  if (el.clientHeight < 2) el.style.aspectRatio = '2';
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:absolute;left:0;top:0;display:block;pointer-events:none';
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  const view = { canvas, ctx, width: 0, height: 0, ratio: 1 };
  let timer = 0;
  const measure = () => {
    const ratio = clamp(devicePixelRatio || 1, 1, 3);
    const w = Math.round(el.clientWidth * ratio), h = Math.round(el.clientHeight * ratio);
    if (!w || !h) return;
    if (w === canvas.width && h === canvas.height && ratio === view.ratio) return;
    canvas.width = w;
    canvas.height = h;
    canvas.style.width = `${w / ratio}px`;
    canvas.style.height = `${h / ratio}px`;
    Object.assign(view, { width: w / ratio, height: h / ratio, ratio });
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    onResize(view);
  };
  const observer = new ResizeObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(measure, 200);
  });
  observer.observe(el);
  return {
    view,
    measure,
    destroy() {
      observer.disconnect();
      clearTimeout(timer);
      canvas.remove();
    },
  };
}

// Wraps a surface at(u, v) in rings of dashes, like the hatching of a pen
// drawing: rings `gap` apart from end to end, dashes about `step` apart round
// each. Calls emit(point, direction round, outward normal, u, v) for each.
function hatch(at, out, gap, step, rand, emit) {
  const N = 1200, len = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) {
    let d = 0;
    for (const v of [0, 0.25, 0.5, 0.75]) d += Math.hypot(...sub(at(i / N, v), at((i - 1) / N, v)));
    len[i] = len[i - 1] + d / 4;
  }
  const total = len[N];
  const uAt = (s) => {
    let i = 1;
    while (i < N && len[i] < s) i++;
    return (i - 1 + (s - len[i - 1]) / (len[i] - len[i - 1] || 1)) / N;
  };
  const rings = Math.max(1, Math.round(total / gap)), hh = total / rings;
  const M = 48, ring = new Float64Array(M + 1);
  for (let b = 0; b < rings; b++) {
    const u = uAt((b + 0.5) * hh);
    for (let k = 1, prev = at(u, 0); k <= M; k++) {
      const next = at(u, k / M);
      ring[k] = ring[k - 1] + Math.hypot(...sub(next, prev));
      prev = next;
    }
    const round = ring[M], count = Math.max(1, Math.round(round / step)), shift = rand();
    for (let j = 0; j < count; j++) {
      const l = ((j + shift) * round) / count;
      let k = 1;
      while (k < M && ring[k] < l) k++;
      const v = (k - 1 + (l - ring[k - 1]) / (ring[k] - ring[k - 1] || 1)) / M;
      const p = at(u, v), e = 1e-3;
      const along = unit(sub(at(Math.min(1, u + e), v), at(Math.max(0, u - e), v)));
      const dv = sub(at(u, v + e), at(u, v - e));
      const around = unit(sub(dv, scaled(along, dot(dv, along))));
      let nrm = cross(around, along);
      if (dot(nrm, out(p, u)) < 0) nrm = scaled(nrm, -1);
      emit(p, around, unit(nrm), u, v);
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

// A smooth curve through (xs, ys) that never overshoots them (Fritsch and Carlson).
function monotone(xs, ys) {
  const n = xs.length, d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  m[0] = d[0];
  m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (!d[i]) {
      m[i] = m[i + 1] = 0;
      continue;
    }
    const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) {
      const t = 3 / Math.sqrt(s);
      m[i] = t * a * d[i];
      m[i + 1] = t * b * d[i];
    }
  }
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0;
    while (xs[i + 1] < x) i++;
    const h = xs[i + 1] - xs[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
  };
}

// The station of a line of (station, height) points at height y, held at its ends.
function lineAt(pts, y) {
  for (let i = 1; i < pts.length; i++) {
    const [a0, y0] = pts[i - 1], [a1, y1] = pts[i];
    if ((y - y0) * (y - y1) <= 0 && y0 !== y1) return a0 + ((a1 - a0) * (y - y0)) / (y1 - y0);
  }
  return y > pts[0][1] ? pts[0][0] : pts[pts.length - 1][0];
}

// The distance from (x, y) to a polyline.
function distanceTo(pts, x, y) {
  let best = Infinity;
  for (let i = 1; i < pts.length; i++) {
    const [ax, ay] = pts[i - 1], [bx, by] = pts[i], dx = bx - ax, dy = by - ay;
    const t = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1);
    best = Math.min(best, Math.hypot(x - ax - dx * t, y - ay - dy * t));
  }
  return best;
}

const wrap = (q) => q - TAU * Math.round(q / TAU);

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
function rotX(a) { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, -s, 0, s, c]; }
function rotY(a) { const c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; }
function rotZ(a) { const c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
function axisAngle(k, a) {
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c, [x, y, z] = k;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}
