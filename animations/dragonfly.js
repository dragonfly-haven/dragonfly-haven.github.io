// A deep black dragonfly drawn in tiny dashes, like the evolution animation.
// It is modelled in 3D and seen from straight above: rings of dashes wrap its
// body like the hatching of a pen drawing, and dashes trace its wings, with
// more of their veins and cells the more pixels it is drawn with, so it stays
// clean at any size and on any screen. It keeps still until the pointer is
// over it, or over the link it sits in, or that link has keyboard focus; then
// it beats its wings as a hovering dragonfly does, and settles again afterwards.
// Its form can be varied (see FORM).
//
//   import { mountDragonfly } from './animations/dragonfly.js';
//   mountDragonfly(document.getElementById('dragonfly'));

import { triangleSize, INK, TAU, random, clamp, smooth, reducedMotion, animate } from './core.js';

// A dash for a screen's pixel ratio, in CSS pixels: the same as the evolution's (sketch.js).
function dashSize(ratio) {
  const length = triangleSize(ratio) * 1.15;
  return { length, width: Math.max(1 / ratio, length * 0.27) };
}

const DISTANCE = 400; // camera distance in model units, for a gentle perspective
// Towards the light and half-way to the eye, in camera space (x right, y up, z to the viewer).
const LIGHT = unit([-0.45, 0.6, 0.66]);
const HALF = unit([LIGHT[0], LIGHT[1], LIGHT[2] + 1]);

// The wing beat of a hovering dragonfly (after Norberg 1975, Rüppell 1989 and
// Wang & Russell 2007). The hind and fore wings beat in counterstroke, half a
// beat apart. Each sweeps down and forward, then up and back, in a stroke
// plane tipped forward from the vertical; it is held nearly flat on the
// downstroke and turns its leading edge up to slice back on the upstroke,
// turning just before each reversal and more towards its tip. Dragonflies beat
// 30 to 40 times a second; this is slowed so that the eye can follow it.
const BEAT = 8; // beats a second
const AMPLITUDE = [0.56, 0.6]; // radians either side of the middle of the stroke, hind and fore
const MIDDLE = 0.08; // the middle of the stroke, and the wings at rest, above flat
const LEAD = 0.5; // how far the hindwings lead the forewings, as a share of a beat
const STROKE = 0.5; // how far the stroke plane tips forward from the vertical, radians
const PITCH = [-0.12, 0.7]; // the pitch on the downstroke and on the upstroke, radians, leading edge up
const ADVANCE = 0.35; // how early the wing turns before each reversal, radians of phase
const TWIST = (f) => 0.3 + 0.7 * f; // the share of the pitch at a fraction f of the way to the tip

// Wing dashes come in three weights: the leading edge and pterostigma, the
// veins and trailing edge, and the cells between them.
const WEIGHTS = [1.45, 1, 0.75];
// So that a wing always shows its veins and lace, it is drawn with as many
// dashes across a forewing as FINE, finer than the body's dashes if need be,
// but none shorter than MIN_DASH device pixels. Where its dashes would be
// shorter than LINE_DASH device pixels, too short for the gaps between them to
// show, as on most screens that aren't high-resolution, the wing is drawn in
// fine unbroken lines instead, with the veins a little and the lace well
// lighter than the outline (LINE_TONES), the way light shows through a wing.
const FINE = 7, MIN_DASH = 2.4, LINE_DASH = 3.2;
const LINE_WEIGHTS = [1.15, 0.9, 0.75], LINE_TONES = [1, 0.9, 0.6];

// ---------------------------------------------------------------------------
// The model. Units: about 100 from head to tail. +y points to the head, +x to
// the dragonfly's right and +z up out of its back; the thorax sits about the origin.

// The dragonfly's form, as on the page. Options to mountDragonfly can vary any
// of it, as the alternatives in dragonflies.html do.
const FORM = {
  tail: 1, // length of the abdomen
  girth: 1, // its thickness
  flat: 1, // its width over its depth: above 1, broad and flat as in skimmers
  club: 0, // how much it swells towards its end, as in clubtails
  eyes: 1, // size of the eyes
  eyeGap: 0, // how far apart they sit
  wing: 1, // length of the wings
  chord: 1, // their breadth
  flare: 1, // how far the base of the hindwings flares back
  sweep: [-0.17, 0.16], // how far the hind and fore wings sweep back or forward
  dihedral: [0.03, 0.04], // and rise from their roots
  weight: 1, // thickness of the dashes
  cell: 3.2, // size of the cells in the wings, in dash lengths
  texture: 'cells', // what fills the wings between their veins: 'cells', 'cross' or 'hatch'
};

const SEGMENTS = [2.4, 6.0, 8.6, 8.4, 8.4, 8.2, 7.8, 6.6, 5.0, 3.4]; // abdomen, S1 to S10
const GIRTH = [3.0, 3.25, 1.95, 1.8, 1.85, 1.9, 2.0, 2.1, 2.0, 1.7]; // radius at each segment's middle

// The dragonfly of a given form: its body parts, its thin parts and its wings.
function model(f) {
  const segments = SEGMENTS.map((s) => s * f.tail);
  const abdomen = segments.reduce((a, b) => a + b, 0);
  const middles = [], joints = [];
  for (let y = 0, k = 0; k < segments.length; y += segments[k++]) {
    middles.push(y + segments[k] / 2);
    if (k) joints.push(y);
  }

  // The abdomen leaves the back of the thorax and droops a little towards the tail.
  const spine = (u) => [0, -4.5 - u * abdomen, 0.6 - 3 * u * u];
  const girth = (u) => {
    const d = u * abdomen;
    let r = GIRTH[0];
    if (d >= middles[9]) r = GIRTH[9];
    else if (d > middles[0]) {
      let k = 0;
      while (middles[k + 1] < d) k++;
      r = GIRTH[k] + (GIRTH[k + 1] - GIRTH[k]) * smooth((d - middles[k]) / (middles[k + 1] - middles[k]));
    }
    let near = Infinity;
    for (const j of joints) near = Math.min(near, Math.abs(d - j));
    r *= 1 - 0.14 * Math.exp(-((near / 0.7) ** 2)); // pinched where segments meet
    if (f.club) r *= 1 + f.club * Math.exp(-(((d - middles[7]) / (segments[7] * 1.4)) ** 2)); // a club about S8
    const end = abdomen - d;
    if (end < 1.4) r *= Math.sqrt(Math.max(0, 1 - (1 - end / 1.4) ** 2)); // rounded tip
    return r * f.girth * f.flat;
  };

  // Body parts as surfaces. Each is hatched with rings of dashes around its
  // first axis; `layer` orders parts from the back, and a part hides whatever
  // of the parts behind it lies inside it.
  const e = f.eyes;
  const eye = (x) => ellipsoid([x * (2.9 + f.eyeGap), 14.4, 2.3], [[x * 4.6 * e, 0, 0], [0, 5.4 * e, 0.8 * e], [0, -0.9 * e, 5.1 * e]]);
  // Pale lines left in the hatching: where the abdomen's segments meet, and
  // the two sutures that run down the thorax's flank.
  const joint = (p) => joints.some((j) => Math.abs(-4.5 - p[1] - j) < 0.12);
  const suture = (p) => Math.abs(p[0]) > 1.4 && [-1.7, 1.5].some((k) => Math.abs(0.891 * (p[1] - 1.4) + 0.453 * (p[2] - 0.4) - k) < 0.2);
  const parts = [
    { layer: 0, surface: tube(spine, girth, 1.08 / f.flat), skip: joint },
    { layer: 0, surface: ellipsoid([0, -4.5 - 7.1 * f.tail, -2.6], [[0, 2.4, 0], [1.1, 0, 0], [0, 0, 1.3]]) }, // genital lobe under S2
    // The thorax leans back: legs at the front of its underside, wings on top behind.
    { layer: 2, surface: ellipsoid([0, 1.4, 0.4], [[0, 7.0, 0], [5.7, 0, 0], [0, -3.2, 6.3]]), skip: suture },
    { layer: 2, surface: ellipsoid([0, 9.4, 0.3], [[0, 1.9, 0], [2.8, 0, 0], [0, 0, 2.4]]) }, // prothorax
    { layer: 3, surface: ellipsoid([0, 18.7, -0.5], [[0, 2.2, 0], [3.7, 0, 0], [0, 0.4, 3.3]]) }, // face
    { layer: 3, surface: ellipsoid([0, 19.3, -3.6], [[0, 1.2, 0], [2.4, 0, 0], [0, 0, 1.2]]) }, // upper lip
    { layer: 3, surface: ellipsoid([0, 16.6, -4.3], [[0, 2.0, 0], [2.5, 0, 0], [0, 0, 1.3]]) }, // mouthparts
    { layer: 4, surface: eye(-1) },
    { layer: 4, surface: eye(1) },
  ];

  // The wings, scaled and swept as the form asks; the hindwings' base flares
  // back by stretching whatever lies behind the main chord.
  const flare = (pts) => (f.flare === 1 ? pts : pts.map(([s, c]) => [s, c > 1 ? 1 + (c - 1) * f.flare : c]));
  const shaped = (spec, pair) => ({
    ...spec,
    length: spec.length * f.wing,
    chord: spec.chord * f.chord,
    sweep: f.sweep[pair],
    dihedral: f.dihedral[pair],
    trail: pair ? spec.trail : flare(spec.trail),
    veins: pair ? spec.veins : spec.veins.map((v) => ({ ...v, pts: flare(v.pts) })),
  });
  const hind = shaped(HINDWING, 0), fore = shaped(FOREWING, 1);
  const wings = [
    { spec: hind, side: -1, pair: 0 },
    { spec: hind, side: 1, pair: 0 },
    { spec: fore, side: -1, pair: 1 },
    { spec: fore, side: 1, pair: 1 },
  ];

  return { parts, limbs: limbs(spine(1)), wings, frames: wings.map(wingFrame) };
}

// Thin parts drawn as lines of dashes: legs folded under the thorax as in
// flight, with spines on their shins; the antennae; and the tail's claspers,
// at the end of the abdomen.
function limbs(end) {
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
  for (const x of [-1, 1]) out.push({ pts: [[x * 0.4, end[1] + 0.6, end[2] + 0.5], [x * 0.9, end[1] - 2.6, end[2] + 0.7], [x * 1.1, end[1] - 5.6, end[2] + 0.4]], rows: 2 }); // upper claspers
  out.push({ pts: [[0, end[1] + 0.4, end[2] - 0.6], [0, end[1] - 2.2, end[2] - 0.9], [0, end[1] - 3.6, end[2] - 0.4]], rows: 1 }); // lower clasper
  return out;
}

// Wings, in fractions of their length (s, root to tip) and chord (c, from the
// leading edge back). Veins of rank 0 show first; higher ranks only once the
// wing is wide enough in dashes to hold them.
const RADIUS = [[0, 0.2], [0.08, 0.1], [0.25, 0.075], [0.47, 0.085], [0.7, 0.08], [0.8, 0.085], [0.9, 0.11], [0.96, 0.16], [0.99, 0.22]];
const SECTOR = [[0.02, 0.27], [0.12, 0.2], [0.3, 0.19], [0.5, 0.2], [0.7, 0.23], [0.85, 0.27], [0.95, 0.31], [0.995, 0.34]];
const R45 = [[0.22, 0.2], [0.36, 0.3], [0.5, 0.42], [0.62, 0.6], [0.72, 0.8], [0.77, 0.98]];
const IR2 = [[0.36, 0.21], [0.52, 0.29], [0.66, 0.38], [0.78, 0.5], [0.88, 0.64], [0.93, 0.74]];

const FOREWING = {
  root: [2.3, 0.9, 6.0], length: 65, chord: 13,
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
  stigma: [0.79, 0.885], // the pterostigma, between these fractions of the length
};

const HINDWING = {
  root: [2.3, -4.1, 5.6], length: 63, chord: 12.6,
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
  stigma: [0.79, 0.88],
};

// A wing's root and its axes: S along the span, C back along the chord and K,
// which C turns towards when the wing pitches about S; and the axis of its
// stroke, the hinge across its root tipped forward so that the wing sweeps
// down and forward, then up and back.
function wingFrame({ spec, side }) {
  const { sweep, dihedral } = spec;
  const S = [side * Math.cos(sweep) * Math.cos(dihedral), Math.sin(sweep) * Math.cos(dihedral), Math.sin(dihedral)];
  const C = [side * Math.sin(sweep), -Math.cos(sweep), 0];
  const K = cross(S, C);
  const N = K[2] < 0 ? scaled(K, -1) : K; // up out of the wing
  const hinge = unit(cross(S, N));
  const stroke = unit(sub(scaled(hinge, Math.cos(STROKE)), [0, 0, side * Math.sin(STROKE)]));
  const root = [side * spec.root[0], spec.root[1], spec.root[2]];
  return { root, side, S, C, K, stroke };
}

// ---------------------------------------------------------------------------

export function mountDragonfly(el, options = {}) {
  // `beat: true` keeps it beating its wings, for previews; any key of FORM varies its form.
  const o = { rotate: -0.7, tilt: 0, roll: 0, fit: 0.97, seed: 3, beat: false, ...FORM, ...options };
  const calm = reducedMotion();
  const { parts, limbs, wings, frames } = model(o);
  // Model to camera: turned in the picture plane; it can also be rolled to show a flank and tipped back.
  const G = mul(rotX(-o.tilt), mul(rotZ(-o.rotate), rotY(o.roll)));
  const towards = [G[6], G[7], G[8]]; // towards the viewer, in model space

  let scale = 1, ox = 0, oy = 0, dash = dashSize(1), half = 1, wingWidth = 1, lines = false;
  let body = null; // the still body, as one path in canvas pixels
  let strokes = []; // per wing and weight: its dashes, or short pieces of line, as (s, c, ds, dc, half length) in the wing's plane
  let job = null; // a layout under way
  // The beat: its clock, how strongly the wings beat now (0 still, 1 full), and
  // what keeps them beating; the frame loop runs only while they move.
  let clock = 0, swing = 0, hovered = false, focused = false, loop = null;
  const beating = () => !calm && (o.beat || hovered || focused);

  const surface = mountSurface(el, build);
  // It fades in once its first layout is ready, rather than popping in.
  if (!calm) surface.view.canvas.style.cssText += ';opacity:0;transition:opacity 0.3s';
  surface.measure();

  // Hovering with a mouse or pen, or keyboard focus on the link, starts the beat;
  // on touch screens it stays still.
  const host = el.closest('a, button') || el;
  const wake = () => beating() && !loop && (loop = animate(el, tick));
  const events = {
    pointerenter: (e) => e.pointerType !== 'touch' && ((hovered = true), wake()),
    pointerleave: () => (hovered = false),
    focusin: () => ((focused = true), wake()),
    focusout: () => (focused = false),
  };
  for (const [type, handler] of Object.entries(events)) host.addEventListener(type, handler);
  wake();

  // A layout is made a few milliseconds at a time while the page is otherwise
  // idle, so it never holds up a fresh page's first frames, and drawn once done.
  function build(view) {
    body = null;
    const next = (job = layout(view));
    const idle = window.requestIdleCallback ? (f) => requestIdleCallback(f, { timeout: 100 }) : (f) => setTimeout(() => f({ timeRemaining: () => 6 }), 1);
    const slice = (deadline) => {
      if (job !== next) return; // a newer layout took its place
      const until = performance.now() + clamp(deadline.timeRemaining(), 2, 6);
      while (performance.now() < until) if (next.next().done) return show();
      idle(slice);
    };
    idle(slice);
  }

  // Finishes any layout under way at once (for previews and tests).
  function flush() {
    if (!job) return;
    while (!job.next().done);
    show();
  }

  function show() {
    job = null;
    draw();
    surface.view.canvas.style.opacity = 1;
  }

  // A wing's flap (up from flat) and pitch (leading edge up), in radians, now.
  function pose(pair, at = clock, amount = swing) {
    const phase = TAU * (BEAT * at - (pair ? LEAD : 0));
    const turn = Math.tanh(3 * Math.cos(phase + ADVANCE)) / Math.tanh(3);
    return [MIDDLE + amount * AMPLITUDE[pair] * Math.sin(phase), amount * ((PITCH[0] + PITCH[1]) / 2 + ((PITCH[1] - PITCH[0]) / 2) * turn)];
  }

  // A wing flapped by `flap`, in camera space: its root, and where its axes S,
  // C and K point.
  function rig(i, flap) {
    const f = frames[i], M = mul(G, axisAngle(f.stroke, flap));
    return { T: apply(G, f.root), S: apply(M, f.S), C: apply(M, f.C), K: apply(M, f.K), M };
  }

  // A point (s, c) of wing i in camera space, pitched by `pitch`.
  function wingAt(r, i, s, c, pitch, length) {
    const a = pitch * frames[i].side * TWIST(s / length), ca = Math.cos(a), sa = Math.sin(a);
    return [0, 1, 2].map((k) => r.T[k] + r.S[k] * s + (r.C[k] * ca + r.K[k] * sa) * c);
  }

  function* layout(view) {
    // Fit the dragonfly, with its wings anywhere in their beat, into the element.
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const extend = (q) => {
      const k = DISTANCE / (DISTANCE - q[2]);
      x0 = Math.min(x0, q[0] * k); x1 = Math.max(x1, q[0] * k);
      y0 = Math.min(y0, q[1] * k); y1 = Math.max(y1, q[1] * k);
    };
    for (const part of parts) for (let u = 0; u <= 1; u += 1 / 12) for (let v = 0; v < 1; v += 1 / 12) extend(apply(G, part.surface.at(u, v)));
    for (const limb of limbs) for (const p of limb.pts) extend(apply(G, p));
    wings.forEach((w, i) => {
      const { length, chord } = w.spec;
      const outline = w.spec.lead.concat(w.spec.trail).map(([s, c]) => [s * length, c * chord]);
      for (let k = 0; k < 16; k++) {
        const [flap, pitch] = pose(w.pair, k / 16 / BEAT, 1);
        const r = rig(i, flap);
        for (const [s, c] of outline) extend(wingAt(r, i, s, c, pitch, length));
      }
    });
    scale = Math.min(view.width / (x1 - x0), view.height / (y1 - y0)) * o.fit;
    ox = view.width / 2 - ((x0 + x1) / 2) * scale;
    oy = view.height / 2 + ((y0 + y1) / 2) * scale;
    dash = dashSize(view.ratio);
    half = (dash.length / scale) * 0.45; // half a dash, in model units
    yield;
    yield* sample();
  }

  // Model point to canvas pixels, through rotation M and shift T.
  function project(M, T, p) {
    const x = M[0] * p[0] + M[1] * p[1] + M[2] * p[2] + T[0];
    const y = M[3] * p[0] + M[4] * p[1] + M[5] * p[2] + T[1];
    const z = M[6] * p[0] + M[7] * p[1] + M[8] * p[2] + T[2];
    const k = (DISTANCE / (DISTANCE - z)) * scale;
    return [ox + x * k, oy - y * k];
  }

  // Lays the dashes: the still body once, as a path; the wings as dashes in
  // their own planes, to be flapped and pitched every frame.
  function* sample() {
    const rand = random(o.seed);
    const L = half / 0.45; // a dash's length in model units
    // On a small emblem a dash grows long for the body's girth and fuzzes its
    // outline, so the body keeps its dashes to a length that suits it.
    const B = Math.min(L, 2.6);
    const T0 = [0, 0, 0];
    const path = new Path2D();
    // Like a hand's, every dash is a little longer or shorter than the next.
    const stroke = (p, dir) => {
      const h = B * 0.45 * (0.85 + 0.3 * rand());
      const a = project(G, T0, add(p, scaled(dir, -h))), b = project(G, T0, add(p, scaled(dir, h)));
      path.moveTo(a[0], a[1]);
      path.lineTo(b[0], b[1]);
    };

    // The body: rings of dashes around each part, thinned where the light
    // catches it, as an engraver leaves a highlight.
    for (const [index, part] of parts.entries()) {
      yield* hatch(part.surface, B * 0.17, B * 1.0, rand, (p, dir, nrm) => {
        const n = apply(G, nrm);
        if (n[2] < 0.02) return; // facing away
        for (let j = 0; j < parts.length; j++) {
          if (j !== index && parts[j].layer >= part.layer && parts[j].surface.inside(p, parts[j].layer === part.layer ? B * 0.3 : 0)) return;
        }
        if (part.skip && part.skip(p)) return;
        const gloss = Math.max(0, dot(n, HALF)) ** 16;
        if (rand() < 0.5 * smooth(clamp((gloss - 0.35) / 0.5, 0, 1))) return;
        stroke(p, dir);
      });
    }
    // Legs, antennae and claspers, leaving out what the body hides: from above,
    // most of the legs are tucked out of sight under it.
    const hidden = (p) => {
      for (let t = 1; t < 16; t += 1.5) {
        const q = add(p, scaled(towards, t));
        if (parts.some((part) => part.surface.inside(q))) return true;
      }
      return false;
    };
    for (const limb of limbs) {
      const line = smoothPath(limb.pts, 4);
      for (let r = 0; r < limb.rows; r++) {
        const lift = (r - (limb.rows - 1) / 2) * B * 0.4;
        walk(line, B * 1.1, B * 0.55 + r * B * 0.5, (p, t) => {
          const side = unit(cross(t, [0, 0, 1]));
          const q = add(p, scaled(side, lift));
          if (!hidden(q)) stroke(q, t);
        });
      }
      // Short spines along the shins.
      if (limb.spines) {
        walk(line, B * 2.2, B * 1.1, (p, t) => {
          const out = unit(add(cross(t, [Math.sign(p[0]), 0, 0]), [0, 0, -0.3]));
          const q = add(p, scaled(out, B * 0.36));
          if (!hidden(q)) stroke(q, out);
        });
      }
    }

    yield;

    // The wings, worked out flat in their own planes, all four with the same
    // dashes: finer than the body's while a forewing is narrow, so that the
    // veins and lace always show, and as thin as the screen draws cleanly.
    const thorax = parts.filter((part) => part.layer === 2);
    const chord = FOREWING.chord * o.chord, ratio = surface.view.ratio;
    const Lw = clamp(chord / FINE, MIN_DASH / (scale * ratio), L); // a wing dash's length in model units
    const detail = chord / Lw;
    wingWidth = Math.max(1 / ratio, Math.min(dash.width, Lw * scale * 0.27));
    lines = Lw * scale * ratio < LINE_DASH;
    const laid = [];
    for (const [i, w] of wings.entries()) {
      const f = frames[i], weights = WEIGHTS.map(() => []);
      yield* wingDashes(w.spec, Lw, detail, lines, rand, o.texture, o.cell, (s, c, ds, dc, weight, h) => {
        if (thorax.some((part) => part.surface.inside(add(f.root, add(scaled(f.S, s), scaled(f.C, c)))))) return;
        weights[weight].push(s, c, ds, dc, h ?? Lw * 0.45 * (0.85 + 0.3 * rand()));
      });
      laid.push(weights.map((d) => Float32Array.from(d)));
      yield;
    }
    body = path;
    strokes = laid;
  }

  // The wings swing into their beat quickly and settle more slowly, and once
  // they rest the loop stops.
  function tick(dt) {
    if (!body) return;
    // A late frame (the page busy elsewhere) moves the wings on by no more than a
    // short step, so they slow for a moment rather than jump.
    dt = Math.min(dt, 1 / 30);
    const on = beating();
    swing = on ? Math.min(1, swing + dt / 0.15) : Math.max(0, swing - dt / 0.4);
    clock += dt;
    draw();
    if (!on && swing === 0 && loop) {
      // Stopped once this frame is over, as it has already asked for the next.
      const done = loop;
      loop = null;
      clock = 0;
      queueMicrotask(() => done.destroy());
    }
  }

  function draw() {
    if (!body) return;
    const { ctx, width, height } = surface.view;
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = INK;
    ctx.lineCap = 'butt';
    // Wings rising towards the viewer go over the body, the others under it.
    // Seen edge on, a wing would clot into a black blade, so it fades as it
    // turns away.
    const near = [], far = [];
    wings.forEach((w, i) => {
      const [flap, pitch] = pose(w.pair);
      const r = rig(i, flap), side = frames[i].side, length = w.spec.length;
      const am = pitch * side * TWIST(0.6);
      const facing = Math.abs(r.K[2] * Math.cos(am) - r.C[2] * Math.sin(am));
      const paths = strokes[i].map((d) => {
        const p = new Path2D();
        for (let j = 0; j < d.length; j += 5) {
          const s = d[j], c = d[j + 1], h = d[j + 4];
          const a = pitch * side * TWIST(s / length), ca = Math.cos(a), sa = Math.sin(a);
          // The chord, turned by the pitch; the dash's centre; and half the dash.
          const vx = r.C[0] * ca + r.K[0] * sa, vy = r.C[1] * ca + r.K[1] * sa, vz = r.C[2] * ca + r.K[2] * sa;
          const px = r.T[0] + r.S[0] * s + vx * c, py = r.T[1] + r.S[1] * s + vy * c, pz = r.T[2] + r.S[2] * s + vz * c;
          const hx = (r.S[0] * d[j + 2] + vx * d[j + 3]) * h, hy = (r.S[1] * d[j + 2] + vy * d[j + 3]) * h, hz = (r.S[2] * d[j + 2] + vz * d[j + 3]) * h;
          const k0 = (DISTANCE / (DISTANCE - pz + hz)) * scale, k1 = (DISTANCE / (DISTANCE - pz - hz)) * scale;
          p.moveTo(ox + (px - hx) * k0, oy - (py - hy) * k0);
          p.lineTo(ox + (px + hx) * k1, oy - (py + hy) * k1);
        }
        return p;
      });
      (r.M[6] * side > 0 ? near : far).push([paths, 0.3 + 0.7 * smooth(clamp(facing / 0.45, 0, 1))]);
    });
    const wingsOf = (list) => {
      for (const [paths, alpha] of list) {
        ctx.globalAlpha = alpha;
        paths.forEach((p, weight) => {
          ctx.globalAlpha = alpha * (lines ? LINE_TONES[weight] : 1);
          ctx.lineWidth = wingWidth * o.weight * (lines ? LINE_WEIGHTS : WEIGHTS)[weight];
          ctx.stroke(p);
        });
      }
      ctx.globalAlpha = 1;
    };
    wingsOf(far);
    ctx.lineWidth = dash.width * o.weight;
    ctx.stroke(body);
    wingsOf(near);
  }

  return {
    // Runs the beat forward by `seconds` at once (for previews and tests).
    advance(seconds) {
      flush();
      if (beating()) swing = 1;
      clock += seconds;
      draw();
    },
    destroy() {
      if (loop) loop.destroy();
      for (const [type, handler] of Object.entries(events)) host.removeEventListener(type, handler);
      surface.destroy();
    },
  };
}

// Fills `el` with a canvas drawn at the screen's full pixel ratio (up to 3),
// in whole device pixels so that nothing is resampled. `measure()` sizes it
// and calls `onResize(view)`, which happens again by itself whenever the
// element's size or the screen's pixel ratio changes.
function mountSurface(el, onResize) {
  if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
  if (el.clientHeight < 2) el.style.aspectRatio = '1';
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:absolute;left:0;top:0;display:block;pointer-events:none';
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  const view = { canvas, ctx, width: 0, height: 0, ratio: 1 };
  let timer = 0, media = null;

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
  const later = () => {
    clearTimeout(timer);
    timer = setTimeout(measure, 200);
  };
  const observer = new ResizeObserver(later);
  observer.observe(el);
  // Moving the window to another screen, or zooming, changes the pixel ratio.
  const watch = () => {
    media?.removeEventListener('change', onRatio);
    media = matchMedia(`(resolution: ${devicePixelRatio || 1}dppx)`);
    media.addEventListener('change', onRatio);
  };
  const onRatio = () => {
    watch();
    later();
  };
  watch();

  return {
    view,
    measure,
    destroy() {
      observer.disconnect();
      media?.removeEventListener('change', onRatio);
      clearTimeout(timer);
      canvas.remove();
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
  // The spine, its sideways and upward directions and the radius, worked out
  // once at many points along it and blended between them.
  const K = 400;
  const table = Array.from({ length: K + 1 }, (_, i) => {
    const u = i / K, t = unit(sub(path(Math.min(1, u + 1e-3)), path(Math.max(0, u - 1e-3))));
    const side = unit(cross(t, [0, 0, 1]));
    return [...path(u), ...side, ...cross(side, t), radius(u)];
  });
  const samples = Array.from({ length: 121 }, (_, i) => i / 120);
  return {
    at(u, v) {
      const f = clamp(u, 0, 1) * K, i = Math.min(K - 1, Math.floor(f)), w = f - i, A = table[i], B = table[i + 1];
      const g = (k) => A[k] + (B[k] - A[k]) * w;
      const q = v * TAU, r = g(9), x = Math.cos(q) * r, y = Math.sin(q) * r * flat;
      return [g(0) + g(3) * x + g(6) * y, g(1) + g(4) * x + g(7) * y, g(2) + g(5) * x + g(8) * y];
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
// Calls emit(point, direction around, outward normal) for each dash, and
// yields every few rings so the work can be spread out.
function* hatch(surface, gap, step, rand, emit) {
  const N = 80, len = new Float64Array(N + 1);
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
  const M = 32, ring = new Float64Array(M + 1);
  for (let b = 0; b < rings; b++) {
    if (b % 8 === 7) yield;
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

// Emits a wing's dashes as (s, c, ds, dc, weight): a dash centre, the
// direction it lies along and its weight (see WEIGHTS), for dashes `L` long.
// With `lines`, it emits short pieces of unbroken line instead, each with its
// half length as a sixth argument. It always draws the outline and
// pterostigma, the main veins and the texture between them; `detail`, how
// many dashes fit across a forewing, decides how many rows make up the edges
// and veins and how many of the smaller veins show, so that a small wing stays
// a clean drawing. Bolder parts come first and win where two would crowd each
// other. The texture is one of
//   'cells': a lace of small cells, `cell` dash lengths across, as most of a real wing is;
//   'cross': cross veins running across the wing like the rungs of a ladder;
//   'hatch': short dashes scattered across the wing, the way cross veins run.
// Yields between parts so the work can be spread out.
function* wingDashes(spec, L, detail, lines, rand, texture, cell, emit) {
  const W = spec.chord, length = spec.length;
  const { lead, trail, outline } = wingOutline(spec);
  const widest = Math.max(...outline.map(([s]) => (chordAt(trail, s) ?? 0) - (chordAt(lead, s) ?? 0)));
  const rank = detail < 5 ? 0 : detail < 8 ? 1 : 2;

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
  const put = (s, c, ds, dc, weight, gap) => {
    if (!insidePolygon(outline, s, c) || crowded(s, c, gap)) return;
    const k = `${Math.floor(s / L)},${Math.floor(c / L)}`;
    (cells.get(k) || cells.set(k, []).get(k)).push([s, c]);
    emit(s, c, ds, dc, weight);
  };
  // Rows of dashes along a line, at `offsets` across it (positive towards the
  // trailing edge for lines that run root to tip), of the given weights; or,
  // with `lines`, unbroken rows, kept within the wing unless on its edge.
  const along = (poly, offsets, weights, gap = L * 0.36, step = L * 1.12) => {
    offsets.forEach((off, r) => {
      if (!lines) {
        walk(poly, step, step / 2 + L * 0.5 * r, (p, t) => put(p[0] - t[1] * off, p[1] + t[0] * off, t[0], t[1], weights[r], gap));
        return;
      }
      const row = poly.map((p, i) => {
        const a = poly[Math.max(0, i - 1)], b = poly[Math.min(poly.length - 1, i + 1)], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        return [p[0] - ((b[1] - a[1]) / l) * off, p[1] + ((b[0] - a[0]) / l) * off];
      });
      for (let i = 1; i < row.length; i++) piece(row[i - 1], row[i], weights[r], !off);
    });
  };
  // A piece of unbroken line from p to q, if its middle lies within the wing.
  const piece = (p, q, weight, edge = false) => {
    const dx = q[0] - p[0], dy = q[1] - p[1], l = Math.hypot(dx, dy), ms = (p[0] + q[0]) / 2, mc = (p[1] + q[1]) / 2;
    if (l > 1e-6 && (edge || insidePolygon(outline, ms, mc))) emit(ms, mc, dx / l, dy / l, weight, l / 2 + L * 0.02);
  };

  // The leading edge, bold, with the pterostigma near the tip: rows packed
  // tight under the edge, so that it reads as a dark mark.
  const edge = detail < 4 ? [L * 0.3] : detail < 7 ? [L * 0.3, L * 0.68] : [L * 0.3, L * 0.68, L * 1.06];
  const [a, b] = spec.stigma.map((f) => f * length), under = edge[edge.length - 1];
  const block = detail < 4 ? [0.38] : detail < 7 ? [0.3, 0.6] : [0.24, 0.46, 0.68, 0.9];
  along(lead.filter(([s]) => s >= a && s <= b), block.map((k) => under + L * k), block.map(() => 0), L * 0.16, L * 0.92);
  yield;
  along(lead, edge, [0, 1, 1]);
  yield;
  for (const v of spec.veins.filter((vein) => vein.rank <= rank)) {
    const rows = v.rank || detail < 6 ? [0] : detail < 9 ? [-L * 0.17, L * 0.17] : [-L * 0.3, 0, L * 0.3];
    along(smoothPath(v.pts.map(([s, c]) => [s * length, c * W]), 6), rows, [1, 1, 1]);
    yield;
  }
  along(trail.slice().reverse(), detail < 7 ? [-L * 0.25] : [-L * 0.25, -L * 0.6], [1, 1]); // the trailing edge
  yield;

  // The texture thins out towards the root, so the wing's base doesn't clot
  // when seen edge on.
  const keep = (s) => smooth(clamp((s / length - 0.05) / 0.15, 0, 1));
  if (texture === 'hatch') {
    for (let s = L / 2; s < length; s += L) {
      const c0 = chordAt(lead, s), c1 = chordAt(trail, s);
      if (c0 == null || c1 == null) continue;
      const shift = rand() * L * 1.35, k = keep(s);
      for (let c = c0 + shift; c < c1; c += L * 1.35) if (rand() < k) put(s + (rand() - 0.5) * L * 0.2, c, 0, 1, 2, L * 0.45);
    }
  } else if (texture === 'cross') {
    for (let s = L * 0.8; s < length; s += L * 1.6) {
      const c0 = chordAt(lead, s), c1 = chordAt(trail, s);
      if (c0 == null || c1 == null || rand() > keep(s)) continue;
      const lean = (rand() - 0.5) * 0.25;
      for (let c = c0 + L * (0.6 + 0.4 * rand()); c < c1 - L * 0.3; c += L * 1.08) put(s + lean * (c - c0), c, lean, 1, 2, L * 0.4);
    }
  } else {
    // While the wing is only a few dashes across, fewer, larger cells.
    const size = L * cell * (detail < 6 ? 1.3 : 1);
    for (const [p, q] of yield* cellEdges(lead, trail, length, widest, size, rand)) {
      if (keep((p[0] + q[0]) / 2) <= 0.5) continue;
      if (!lines) {
        walk([p, q], L * 1.08, L * 0.54, (pt, t) => put(pt[0], pt[1], t[0], t[1], 2, L * 0.4));
        continue;
      }
      // An edge as unbroken line, in short pieces so that it stops at the wing's outline.
      const n = Math.max(1, Math.ceil(Math.hypot(q[0] - p[0], q[1] - p[1]) / (L * 0.5)));
      for (let k = 0; k < n; k++) {
        const at = (t) => [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t];
        piece(at(k / n), at((k + 1) / n), 2);
      }
    }
  }
}

// The edges of a wing's cells, as segments [[s, c], [s, c]]: the edges of the
// Voronoi diagram of seeds about `cell` apart, laid in rows that follow the
// wing from root to tip. Yields now and then, and returns the edges.
function* cellEdges(lead, trail, length, widest, cell, rand) {
  const rows = Math.max(2, Math.round(widest / (cell * 0.87))), seeds = [];
  for (let j = -1; j <= rows; j++) {
    for (let s = ((j & 1) * cell) / 2; s <= length; s += cell) {
      const ps = clamp(s + (rand() - 0.5) * cell * 0.4, 0, length);
      const c0 = chordAt(lead, ps), c1 = chordAt(trail, ps);
      if (c0 == null || c1 == null) continue;
      const f = (j + 0.5 + (j < 0 || j === rows ? 0 : (rand() - 0.5) * 0.3)) / rows;
      seeds.push([ps, c0 + f * (c1 - c0)]);
    }
  }
  const edges = [];
  for (let i = 0; i < seeds.length; i++) {
    if (i % 24 === 23) yield;
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
  return edges;
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
