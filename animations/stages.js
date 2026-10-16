// The twenty stages of the evolution animation, from organic matter to AI.
//
// Each stage paints a density map into a 200 × 200 unit box: black, where the
// opacity says how densely triangles gather, so faint fills read as
// translucent and partial cuts as engraved grooves. The engine lights every
// form from the upper left, rounding it over `bevel` units in from its edge,
// or along a painted height map (`relief`, opacity = height) where a truer
// shape matters, such as a sphere. `align` (0 to 1) is how strictly the
// triangles line up at rest: loosely for life, in ranks for machines.
//
// Neighbouring stages share their layout so each grows out of the one before:
// the early ones turn about the centre like the dust around them, the animals
// walk or swim to the left, and the last three keep the same head.

import { TAU, random } from './core.js';

const disc = (g, x, y, r) => {
  g.beginPath();
  g.arc(x, y, r, 0, TAU);
  g.fill();
};
const oval = (g, x, y, rx, ry, rot = 0) => {
  g.beginPath();
  g.ellipse(x, y, rx, ry, rot, 0, TAU);
  g.fill();
};
const ring = (g, x, y, r, w) => {
  g.lineWidth = w;
  g.beginPath();
  g.arc(x, y, r, 0, TAU);
  g.stroke();
};
const fill = (g, d) => g.fill(typeof d === 'string' ? new Path2D(d) : d);
const trace = (g, d, w) => {
  g.lineWidth = w;
  g.stroke(typeof d === 'string' ? new Path2D(d) : d);
};

function line(g, w, ...p) {
  g.lineWidth = w;
  g.beginPath();
  g.moveTo(p[0], p[1]);
  for (let i = 2; i < p.length; i += 2) g.lineTo(p[i], p[i + 1]);
  g.stroke();
}

// Erases what `paint` draws: fully for gaps and holes, partly (a < 1) for grooves.
function cut(g, paint, a = 1) {
  g.save();
  g.globalCompositeOperation = 'destination-out';
  g.globalAlpha = a;
  paint();
  g.restore();
}

// Paints at a lower density, for translucent parts.
function faint(g, a, paint) {
  g.save();
  g.globalAlpha *= a;
  paint();
  g.restore();
}

// Keeps whatever `paint` draws inside a path.
function within(g, path, paint) {
  g.save();
  g.clip(typeof path === 'string' ? new Path2D(path) : path);
  paint();
  g.restore();
}

// A soft blob, densest (a) at its centre and fading out by radius r.
function soft(g, x, y, r, a) {
  const grad = g.createRadialGradient(x, y, 0, x, y, r);
  grad.addColorStop(0, `rgba(0,0,0,${a})`);
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.save();
  g.fillStyle = grad;
  disc(g, x, y, r);
  g.restore();
}

// The moon in the upper right of the late animal stages, waning as they go:
// `lit` is the share of its disc in light, from 1 (full) towards 0.
const MOON = [156, 36, 15];
function moon(g, lit) {
  const [x, y, r] = MOON;
  g.save();
  g.beginPath();
  g.arc(x, y, r, 0, TAU);
  g.clip();
  faint(g, 0.62, () => disc(g, x, y, r));
  // the shadowed part, a disc slid off to the lower left, keeps only a faint glow
  cut(g, () => disc(g, x - r * 2.05 * lit, y + r * 0.3 * lit, r * 1.04), 0.88);
  cut(g, () => {
    for (const [dx, dy, cr] of [[-4, -5, 3.2], [5, 2, 2.4], [-1, 7, 1.8], [7, -7, 1.5]]) disc(g, x + dx, y + dy, cr);
  }, 0.4);
  g.restore();
}

// Relief: a hemisphere over radius r, `top` high at its centre (full opacity is
// RELIEF units high, so by default a dome is as high as it is wide).
export const RELIEF = 40;
function dome(g, x, y, r, top = Math.min(1, r / RELIEF)) {
  const grad = g.createRadialGradient(x, y, 0, x, y, r);
  for (const [s, h] of [[0, 1], [0.4, 0.92], [0.6, 0.8], [0.75, 0.66], [0.87, 0.49], [0.95, 0.31], [1, 0]]) {
    grad.addColorStop(s, `rgba(0,0,0,${h * top})`);
  }
  g.save();
  g.fillStyle = grad;
  disc(g, x, y, r);
  g.restore();
}

// A smooth curve through points (Catmull-Rom), with position and direction
// at any fraction of its length.
function along(pts) {
  const dense = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[Math.max(i - 1, 0)], b = pts[i], c = pts[i + 1], d = pts[Math.min(i + 2, pts.length - 1)];
    for (let s = 0; s < 12; s++) {
      const t = s / 12, t2 = t * t, t3 = t2 * t;
      const f = (k) => 0.5 * (2 * b[k] + (c[k] - a[k]) * t + (2 * a[k] - 5 * b[k] + 4 * c[k] - d[k]) * t2 + (3 * b[k] - a[k] - 3 * c[k] + d[k]) * t3);
      dense.push([f(0), f(1)]);
    }
  }
  dense.push(pts[pts.length - 1]);
  const acc = [0];
  for (let i = 1; i < dense.length; i++) acc.push(acc[i - 1] + Math.hypot(dense[i][0] - dense[i - 1][0], dense[i][1] - dense[i - 1][1]));
  const total = acc[acc.length - 1];
  return {
    total,
    at(f) {
      const d = f * total;
      let j = 0;
      while (j < dense.length - 2 && acc[j + 1] < d) j++;
      const seg = acc[j + 1] - acc[j] || 1, t = Math.min(1, Math.max(0, (d - acc[j]) / seg));
      const [x0, y0] = dense[j], [x1, y1] = dense[j + 1];
      return [x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, (x1 - x0) / seg, (y1 - y0) / seg];
    },
  };
}

// A limb, tail or body along a curve; `r` is a radius or a function of the length fraction.
function tube(g, pts, r) {
  const path = Array.isArray(pts) ? along(pts) : pts;
  const radius = typeof r === 'function' ? r : () => r;
  const steps = Math.max(2, Math.ceil(path.total / 0.4));
  g.beginPath();
  for (let s = 0; s <= steps; s++) {
    const f = s / steps, [x, y] = path.at(f), rr = Math.max(0.2, radius(f));
    g.moveTo(x + rr, y);
    g.arc(x, y, rr, 0, TAU);
  }
  g.fill();
}
const taper = (r0, r1) => (f) => r0 + (r1 - r0) * f;

// Mirrors whatever `paint` draws across the vertical centre line.
function mirrored(g, paint) {
  paint();
  g.save();
  g.translate(200, 0);
  g.scale(-1, 1);
  paint();
  g.restore();
}

// Turns whatever `paint` draws about the centre of the box.
function turned(g, angle, paint) {
  g.save();
  g.translate(100, 100);
  g.rotate(angle);
  g.translate(-100, -100);
  paint();
  g.restore();
}

// A ball-and-stick molecule: [x, y, radius] atoms, bonds as pairs of atom indices.
function molecule(g, atoms, bonds, w = 1.5) {
  for (const [a, b] of bonds) line(g, w, atoms[a][0], atoms[a][1], atoms[b][0], atoms[b][1]);
  for (const [x, y, r] of atoms) disc(g, x, y, r);
}

// Delaunay triangulation (Bowyer-Watson) of [[x, y], ...], as index triples.
function delaunay(pts) {
  const all = pts.concat([[-2000, -2000], [2200, -2000], [100, 2200]]);
  const n = pts.length;
  const circle = (t) => {
    const [a, b, c] = t.map((i) => all[i]);
    const d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]));
    const sa = a[0] ** 2 + a[1] ** 2, sb = b[0] ** 2 + b[1] ** 2, sc = c[0] ** 2 + c[1] ** 2;
    const x = (sa * (b[1] - c[1]) + sb * (c[1] - a[1]) + sc * (a[1] - b[1])) / d;
    const y = (sa * (c[0] - b[0]) + sb * (a[0] - c[0]) + sc * (b[0] - a[0])) / d;
    return [x, y, (a[0] - x) ** 2 + (a[1] - y) ** 2];
  };
  let tris = [[n, n + 1, n + 2]];
  for (let i = 0; i < n; i++) {
    const [px, py] = all[i];
    const bad = tris.filter((t) => {
      const [x, y, r2] = circle(t);
      return (px - x) ** 2 + (py - y) ** 2 < r2;
    });
    const edges = [];
    for (const t of bad) {
      for (const [a, b] of [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]]) {
        if (!bad.some((u) => u !== t && u.includes(a) && u.includes(b))) edges.push([a, b]);
      }
    }
    tris = tris.filter((t) => !bad.includes(t)).concat(edges.map(([a, b]) => [a, b, i]));
  }
  return tris.filter((t) => t.every((i) => i < n));
}

function inside(poly, x, y) {
  let hit = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

// The head in profile, facing left, that the last three stages share.
const HEAD = [
  [104, 18], [82, 23], [66, 36], [58, 54], [57, 70], [52, 83], [42, 99], [50, 106], [54, 110], [50, 118],
  [55, 124], [50, 130], [56, 140], [54, 150], [66, 160], [88, 162], [94, 186], [142, 186], [138, 160],
  [148, 138], [160, 110], [162, 80], [152, 48], [132, 26],
];
const headPath = () => {
  const p = new Path2D();
  HEAD.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y)));
  p.closePath();
  return p;
};

// The skin of that head: faint, with a crisp outline, an eye and an ear.
function head(g, skin = 0.13) {
  faint(g, skin, () => fill(g, headPath()));
  g.lineJoin = 'round';
  trace(g, headPath(), 1.6);
  disc(g, 70, 79, 2.2);
  faint(g, 0.7, () => trace(g, 'M 120 86 C 130 82, 134 96, 128 106 C 124 112, 118 108, 120 102', 1.3));
}

// The brain, frontal lobe to the left, sitting in that head's skull.
const CEREBRUM = 'M 28 104 C 22 62, 60 30, 104 30 C 150 30, 178 58, 174 98 C 172 120, 156 130, 136 128 C 120 140, 96 142, 78 132 C 58 136, 32 128, 28 104 Z';
function brain(g) {
  g.save();
  g.translate(109, 78);
  g.scale(0.56, 0.56);
  g.translate(-100, -88);
  tube(g, [[122, 132], [120, 156], [118, 190]], taper(9, 7));
  oval(g, 142, 138, 25, 15, -0.12);
  cut(g, () => {
    for (let j = 0; j < 3; j++) trace(g, `M ${124 + j * 2} ${132 + j * 6} Q 142 ${128 + j * 7} ${164 - j * 2} ${132 + j * 6}`, 2.2);
    fill(g, 'M 26 104 C 20 60, 60 28, 104 28 C 152 28, 180 58, 176 98 C 174 122, 158 132, 136 130 C 120 142, 96 144, 78 134 C 58 138, 30 130, 26 104 Z');
  });
  fill(g, CEREBRUM);
  cut(g, () => {
    trace(g, 'M 56 118 C 80 104, 108 100, 140 98', 4);
    trace(g, 'M 116 32 C 106 56, 116 72, 102 98', 3.6);
    [
      'M 40 84 C 50 76, 56 90, 66 80 S 80 62, 88 70', 'M 52 56 C 62 62, 70 48, 82 54 S 94 46, 100 40',
      'M 74 92 C 80 84, 90 92, 96 82', 'M 128 40 C 132 52, 144 46, 148 58 S 160 66, 164 78',
      'M 124 70 C 132 64, 140 76, 150 70 S 162 84, 170 92', 'M 118 84 C 124 92, 134 84, 140 92',
      'M 70 124 C 80 114, 92 126, 104 116 S 120 120, 128 112', 'M 36 102 C 44 96, 50 108, 58 102',
      'M 150 104 C 156 110, 162 104, 168 110', 'M 60 70 C 64 64, 72 70, 76 64', 'M 136 56 C 140 62, 132 66, 138 72',
    ].forEach((d) => trace(g, d, 3));
  }, 0.85);
  g.restore();
}

function jellyBell() {
  const p = new Path2D('M 44 84 C 44 22, 156 22, 156 84');
  for (let k = 0; k < 10; k++) p.quadraticCurveTo(156 - k * 11.2 - 5.6, 90, 156 - (k + 1) * 11.2, 84);
  p.closePath();
  return p;
}

function cellWall() {
  const p = new Path2D();
  for (let i = 0; i <= 160; i++) {
    const a = (i / 160) * TAU;
    const r = 1 + 0.035 * Math.sin(3 * a + 0.6) + 0.025 * Math.sin(5 * a + 2.1);
    const x = 100 + Math.cos(a) * 74 * r, y = 101 + Math.sin(a) * 66 * r;
    if (i) p.lineTo(x, y);
    else p.moveTo(x, y);
  }
  p.closePath();
  return p;
}

const FISH = 'M 28 100 C 44 76, 76 64, 108 68 C 130 71, 144 86, 150 94 L 150 104 C 144 112, 130 124, 108 128 C 76 132, 44 124, 28 100 Z';

export const STAGES = [
  {
    name: 'Organic matter',
    // A young galaxy of organic matter: a bright core and clumped spiral arms
    // that follow the same spiral as the dust turning around every stage.
    paint(g) {
      const rand = random(3);
      // a bright heart in a small bulge
      soft(g, 100, 100, 26, 0.85);
      soft(g, 100, 100, 10, 1);
      for (let arm = 0; arm < 4; arm++) {
        const main = arm % 2 === 0, base = (arm * Math.PI) / 2;
        for (let i = 0; i < (main ? 300 : 110); i++) {
          const t = rand() ** 0.9, r = 11 + t * 80;
          const a = base + Math.log(r / 10) * 2.1 + (rand() - 0.5) * (0.16 + t * 0.2) * (main ? 1 : 1.6);
          const x = 100 + Math.cos(a) * r, y = 100 + Math.sin(a) * r * 0.92;
          soft(g, x, y, (main ? 1.5 : 1.1) + rand() * rand() * 3.5, (main ? 0.55 : 0.35) + rand() * 0.4);
          // knots where stars and matter gather
          if (rand() < 0.3) disc(g, x + (rand() - 0.5) * 6, y + (rand() - 0.5) * 6, 0.6 + rand() * 0.9);
          if (rand() < 0.05) soft(g, x, y, 2.4, 1);
        }
      }
      // dark lanes along the inner edge of the main arms
      cut(g, () => {
        for (const base of [0, Math.PI]) {
          g.beginPath();
          for (let r = 16; r < 70; r += 2) {
            const a = base + Math.log(r / 10) * 2.1 - 0.32;
            g.lineTo(100 + Math.cos(a) * r, 100 + Math.sin(a) * r * 0.92);
          }
          g.lineWidth = 2.2;
          g.stroke();
        }
      }, 0.6);
    },
    relief(g) {
      dome(g, 100, 100, 30);
    },
  },
  {
    name: 'Molecules',
    // Molecules condense along the same arms: a nucleotide at the heart,
    // water, a sugar ring and amino acids drifting outwards.
    paint(g) {
      const hex = (cx, cy, R, n = 6, start = -Math.PI / 2) => Array.from({ length: n }, (_, k) => [cx + R * Math.cos(start + (k * TAU) / n), cy + R * Math.sin(start + (k * TAU) / n), 2.6]);
      // the nucleotide: base, sugar and phosphate
      const A = hex(82, 92, 11), B = hex(82 + 11 * Math.sqrt(3), 92, 11), S = hex(124, 116, 9.5, 5);
      const atoms = [...A, ...B, ...S, [82, 70, 3.6], [62, 104, 3.6], [126, 77, 2.6], [144, 104, 2.6], [151, 90, 3.6], [156, 76, 4.8], [171, 70, 3.6], [148, 64, 3.6], [166, 89, 3.6], [132, 136, 3.6], [112, 136, 3.6]];
      const cycle = (o, n) => Array.from({ length: n }, (_, k) => [o + k, o + ((k + 1) % n)]);
      const bonds = [...cycle(0, 6), ...cycle(6, 6), ...cycle(12, 5), [0, 17], [4, 18], [7, 19], [8, 16], [13, 20], [20, 21], [21, 22], [22, 23], [22, 24], [22, 25], [14, 26], [15, 27]];
      molecule(g, atoms, bonds, 1.5);
      g.lineWidth = 1.3;
      g.beginPath();
      g.arc(B[0][0], 92, 5.5, 0, TAU);
      g.stroke();
      // smaller molecules strung along the spiral arms
      const place = (r, arm, draw) => {
        const a = arm + Math.log(r / 10) * 2.1;
        g.save();
        g.translate(100 + Math.cos(a) * r, 100 + Math.sin(a) * r * 0.92);
        g.rotate(a);
        draw();
        g.restore();
      };
      const water = () => molecule(g, [[0, 0, 3.4], [-5.5, 4.2, 2.2], [5.5, 4.2, 2.2]], [[0, 1], [0, 2]]);
      const glycine = () => molecule(g, [[-12, 0, 3], [-6, -4, 2.4], [0, 0, 2.4], [6, -4, 2.4], [6, -11, 3], [12, 0, 3], [-6, -10, 1.8]], [[0, 1], [1, 2], [2, 3], [3, 4], [3, 5], [1, 6]]);
      const benzene = () => {
        const b = hex(0, 0, 8);
        molecule(g, b.concat(b.map(([x, y]) => [x * 1.75, y * 1.75, 1.6])), [...cycle(0, 6), [0, 6], [1, 7], [2, 8], [3, 9], [4, 10], [5, 11]], 1.3);
      };
      const chain = () => molecule(g, [[-15, 2, 2.6], [-9, -2, 2.6], [-3, 2, 2.6], [3, -2, 2.6], [9, 2, 2.6], [15, -2, 3.2]], [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]]);
      place(50, Math.PI, glycine);
      place(70, Math.PI, water);
      place(84, Math.PI + 0.25, chain);
      place(56, 0.15, benzene);
      place(80, 0, water);
      place(66, Math.PI / 2, water);
      place(78, (3 * Math.PI) / 2, glycine);
      place(42, (3 * Math.PI) / 2 + 0.3, water);
    },
  },
  {
    name: 'Replicators',
    // A strand of RNA copying itself: the lower half already paired, loose
    // building blocks spiralling in to pair with the upper half.
    paint(g) {
      const rand = random(5);
      const strand = along([[96, 16], [84, 40], [92, 66], [108, 90], [112, 116], [100, 140], [92, 164], [102, 186]]);
      tube(g, strand, 1.9);
      const partner = [];
      for (let f = 0.02; f < 0.99; f += 0.032) {
        const [x, y, dx, dy] = strand.at(f), nx = dy, ny = -dx; // to the strand's right
        if (f > 0.45) {
          line(g, 1.3, x, y, x + nx * 11, y + ny * 11);
          partner.push([x + nx * 12, y + ny * 12]);
        } else {
          line(g, 1.3, x, y, x + nx * 5, y + ny * 5);
          // a building block on its way in
          const d = 14 + rand() * 18, s = (rand() - 0.5) * 0.9;
          const bx = x + nx * d + dx * s * 8, by = y + ny * d + dy * s * 8;
          line(g, 1.2, bx, by, bx - nx * 4.5, by - ny * 4.5);
          disc(g, bx + nx * 1.2, by + ny * 1.2, 2);
        }
      }
      tube(g, partner, 1.9);
      for (let i = 0; i < 26; i++) {
        const a = rand() * TAU, r = 30 + rand() * 55;
        const x = 100 + Math.cos(a) * r, y = 100 + Math.sin(a) * r;
        line(g, 1.1, x, y, x + Math.cos(a + 1.8) * 4.5, y + Math.sin(a + 1.8) * 4.5);
        disc(g, x, y, 1.7);
      }
    },
  },
  {
    name: 'DNA',
    // The double helix, its near strand standing out in front of the far one.
    paint(g) {
      g.translate(100, 100);
      g.rotate(-0.32);
      const A = 25, L = 72;
      for (let y = -88; y <= 88; y += 4.6) {
        const x = A * Math.sin((y / L) * TAU), near = (Math.cos((y / L) * TAU) + 1) / 2;
        if (Math.abs(x) < 3) continue;
        faint(g, 0.55 + near * 0.45, () => {
          line(g, 1.6, x * 0.94, y, 0.8 * Math.sign(x), y);
          line(g, 1.6, -x * 0.94, y, -0.8 * Math.sign(x), y);
        });
      }
      for (const side of [1, -1]) {
        for (let y = -96; y < 96; y += 0.8) {
          const p = (y / L) * TAU, q = ((y + 0.8) / L) * TAU, near = (side * Math.cos(p) + 1) / 2;
          faint(g, 0.6 + near * 0.4, () => line(g, 2.4 + near * 3, side * A * Math.sin(p), y, side * A * Math.sin(q), y + 0.8));
        }
      }
    },
    relief(g) {
      g.translate(100, 100);
      g.rotate(-0.32);
      for (const side of [1, -1]) {
        for (let y = -96; y < 96; y += 0.8) {
          const p = (y / 72) * TAU, near = (side * Math.cos(p) + 1) / 2;
          faint(g, 0.25 + near * 0.75, () => disc(g, side * 25 * Math.sin(p), y, 2.4 + near * 3));
        }
      }
    },
  },
  {
    name: 'Protocell',
    // A bubble of membrane around coiled strands: the first inside and outside.
    paint(g) {
      faint(g, 0.1, () => disc(g, 100, 100, 58));
      ring(g, 100, 100, 63, 2.6);
      ring(g, 100, 100, 57.5, 2.6);
      for (const [x, y, r, turns] of [[86, 88, 15, 2.6], [118, 112, 12, 2.2], [92, 124, 9, 1.8]]) {
        const pts = [];
        for (let a = 0; a < turns * TAU; a += 0.2) pts.push([x + Math.cos(a) * r * (0.35 + a / (turns * TAU) * 0.65), y + Math.sin(a) * r * (0.35 + a / (turns * TAU) * 0.65)]);
        tube(g, pts, 1.2);
      }
      for (const [x, y, r] of [[132, 80, 6], [66, 120, 5], [116, 66, 3.6], [140, 128, 4]]) ring(g, x, y, r, 1.6);
      const rand = random(8);
      for (let i = 0; i < 40; i++) {
        const a = rand() * TAU, r = rand() * 50;
        disc(g, 100 + Math.cos(a) * r, 100 + Math.sin(a) * r, 0.8 + rand() * 0.8);
      }
    },
    relief(g) {
      dome(g, 100, 100, 64);
    },
  },
  {
    name: 'Bacterium',
    // A rod-shaped cell with its coiled chromosome, hairs, and long whips.
    paint(g) {
      turned(g, -0.42, () => {
        const rand = random(6);
        for (const [dy, ph, len] of [[-6, 0, 74], [2, 1.4, 86], [8, 2.6, 66]]) {
          const pts = [];
          for (let s = 0; s <= len; s += 2) pts.push([150 + s, 100 + dy + Math.sin(s / 6 + ph) * 5 * Math.min(1, s / 12) + s * dy * 0.02]);
          tube(g, pts, (f) => 1.1 - f * 0.5);
        }
        for (let i = 0; i < 26; i++) {
          const top = i % 2, x = 62 + (i >> 1) * 6.2 + rand() * 2;
          line(g, 0.9, x, top ? 78 : 122, x + (rand() - 0.5) * 4, top ? 70 - rand() * 4 : 130 + rand() * 4);
        }
        g.beginPath();
        g.roundRect(42, 77, 112, 46, 23);
        g.fill();
        cut(g, () => {
          g.beginPath();
          g.roundRect(46.5, 81.5, 103, 37, 18.5);
          g.fill();
        }, 0.5);
        const coil = [];
        for (let a = 0; a < 26; a += 0.15) coil.push([70 + a * 2.2 + Math.sin(a * 2.3) * 4, 100 + Math.cos(a * 1.7) * 9 + Math.sin(a * 0.9) * 3]);
        tube(g, coil, 0.9);
        for (let i = 0; i < 30; i++) disc(g, 54 + rand() * 92, 86 + rand() * 28, 0.9);
      });
    },
    bevel: 20,
  },
  {
    name: 'Cell with a nucleus',
    // A cell like a small world: nucleus, power plants, folded membranes.
    paint(g) {
      faint(g, 0.12, () => fill(g, cellWall()));
      g.lineWidth = 3;
      g.stroke(cellWall());
      faint(g, 0.55, () => disc(g, 88, 96, 22));
      ring(g, 88, 96, 22, 2.2);
      disc(g, 92, 92, 7.5);
      cut(g, () => {
        for (let a = 0; a < TAU; a += TAU / 18) disc(g, 88 + Math.cos(a) * 22, 96 + Math.sin(a) * 22, 0.9);
      });
      for (const d of ['M 58 116 C 50 94, 58 70, 80 62', 'M 54 104 C 50 86, 60 70, 74 64', 'M 66 128 C 76 134, 94 136, 108 128', 'M 70 136 C 82 142, 100 142, 112 134']) trace(g, d, 1.6);
      for (let j = 0; j < 5; j++) {
        g.lineWidth = 2;
        g.beginPath();
        g.arc(152, 120, 6 + j * 4.2, Math.PI * 0.72, Math.PI * 1.48);
        g.stroke();
      }
      for (const [x, y, a] of [[132, 70, 0.4], [62, 144, -0.3], [118, 150, 0.9], [150, 92, 1.6]]) {
        g.save();
        g.translate(x, y);
        g.rotate(a);
        oval(g, 0, 0, 11, 5.4);
        cut(g, () => line(g, 1.2, -7, 0, -4.5, -3, -1.5, 3, 1.5, -3, 4.5, 3, 7, 0));
        g.restore();
      }
      for (const [x, y, r] of [[160, 72, 4.5], [40, 96, 4], [106, 62, 3], [164, 140, 3.5], [126, 132, 2.6]]) ring(g, x, y, r, 1.5);
    },
    relief(g) {
      dome(g, 100, 101, 74);
      dome(g, 88, 96, 23, 0.6);
    },
  },
  {
    name: 'Many cells',
    // A hollow ball of cells, the first body, round like a little moon.
    paint(g) {
      for (const c of blastula()) {
        cut(g, () => disc(g, c.x, c.y, c.r + 0.9));
        faint(g, 0.7 + 0.3 * c.z, () => disc(g, c.x, c.y, c.r));
        cut(g, () => disc(g, c.x + c.r * 0.18, c.y - c.r * 0.12, c.r * 0.28), 0.7);
      }
    },
    relief(g) {
      // each cell bulges from the ball's own curve, with a dip between neighbours
      for (const c of blastula()) dome(g, c.x, c.y, c.r, Math.min(1, Math.max(0, c.z) * 0.75 + c.r / RELIEF));
    },
  },
  {
    name: 'Jellyfish',
    // A translucent bell with its canals, frilled arms and trailing tentacles.
    paint(g) {
      faint(g, 0.2, () => fill(g, jellyBell()));
      g.lineWidth = 2.2;
      g.stroke(jellyBell());
      for (let k = 0; k <= 8; k++) {
        const x = 50 + k * 12.5;
        faint(g, 0.8, () => trace(g, `M 100 34 Q ${100 + (x - 100) * 0.55} 50 ${x} 86`, 1));
      }
      for (const [x, y] of [[78, 62], [94, 54], [106, 54], [122, 62]]) ring(g, x, y, 5.5, 1.8);
      for (const [x0, ph] of [[88, 0], [96, 1.6], [104, 3.1], [112, 4.4]]) {
        const pts = [];
        for (let i = 0; i <= 9; i++) pts.push([x0 + Math.sin(i * 0.9 + ph) * 5 + (x0 - 100) * i * 0.05, 88 + i * 9.5]);
        tube(g, pts, (f) => 3.2 - f * 1.6 + Math.sin(f * 44 + ph) * 1.1);
      }
      for (let k = 0; k < 16; k++) {
        const x0 = 47 + k * 7, pts = [];
        for (let i = 0; i <= 12; i++) pts.push([x0 + Math.sin(i * 0.62 + k * 0.9) * 4.5 + (x0 - 100) * i * 0.016, 88 + i * 8.6]);
        tube(g, pts, (f) => 0.85 - f * 0.35);
      }
    },
    relief(g) {
      g.save();
      g.scale(1, 1.15);
      dome(g, 100, 74, 58);
      g.restore();
    },
  },
  {
    name: 'Trilobite',
    // An armoured crawler of the first seas, turned towards the upper left.
    paint(g) {
      turned(g, -0.32, () => {
        fill(g, 'M 46 78 C 46 42, 70 26, 100 26 C 130 26, 154 42, 154 78 L 162 122 L 146 82 L 54 82 L 38 122 Z');
        for (let j = 0; j < 11; j++) {
          const y0 = 85 + j * 5.7, w = 45 - j * 2.1;
          fill(g, `M ${100 - w} ${y0 + 1.6} L ${100 - w + 4} ${y0} L ${100 + w - 4} ${y0} L ${100 + w} ${y0 + 1.6} L ${100 + w - 3} ${y0 + 4.6} L ${100 - w + 3} ${y0 + 4.6} Z`);
        }
        fill(g, 'M 72 150 C 72 166, 86 176, 100 176 C 114 176, 128 166, 128 150 Z');
        cut(g, () => {
          trace(g, 'M 88 81 C 86 62, 90 40, 100 38 C 110 40, 114 62, 112 81', 1.6);
          trace(g, 'M 66 60 C 70 52, 78 52, 80 60', 1.6);
          trace(g, 'M 134 60 C 130 52, 122 52, 120 60', 1.6);
          line(g, 1.6, 87, 85, 90, 166);
          line(g, 1.6, 113, 85, 110, 166);
          for (let j = 0; j < 4; j++) trace(g, `M ${80 + j * 2} ${155 + j * 5} Q 100 ${159 + j * 5} ${120 - j * 2} ${155 + j * 5}`, 1.2);
        });
        // engraved: the shield's border and the pleural furrows
        cut(g, () => {
          trace(g, 'M 52 80 C 52 46, 72 32, 100 32 C 128 32, 148 46, 148 80', 1.2);
          for (let j = 0; j < 11; j++) {
            const y = 87.3 + j * 5.7, w = 43 - j * 2.1;
            line(g, 0.9, 100 - w, y, 87, y - 0.6);
            line(g, 0.9, 113, y - 0.6, 100 + w, y);
          }
        }, 0.6);
      });
    },
    bevel: 6,
  },
  {
    name: 'Fish',
    // Scaled and finned, swimming left, where every animal after it walks.
    paint(g) {
      faint(g, 0.6, () => {
        fill(g, 'M 144 94 L 186 60 Q 170 99 186 138 L 144 104 Z');
        fill(g, 'M 76 70 C 88 46, 108 40, 124 44 C 116 56, 114 66, 116 74 Z');
        fill(g, 'M 104 126 C 110 140, 122 146, 132 144 C 126 136, 124 128, 124 122 Z');
        fill(g, 'M 72 128 C 74 140, 82 146, 90 146 C 88 138, 88 132, 88 128 Z');
      });
      for (const [x, y] of [[184, 63], [181, 74], [177, 86], [174, 99], [177, 112], [181, 124], [184, 135]]) line(g, 1, 148, 99, x, y);
      for (const [x, y] of [[88, 52], [96, 47], [104, 44], [112, 43], [120, 44]]) line(g, 0.9, x + 2, 70, x, y);
      for (const [x, y] of [[110, 140], [118, 144], [126, 144]]) line(g, 0.9, x - 2, 126, x, y);
      fill(g, FISH);
      within(g, FISH, () => {
        cut(g, () => {
          for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 13; c++) {
              const x = 62 + c * 7 + (r % 2) * 3.5, y = 74 + r * 6.2;
              g.lineWidth = 0.9;
              g.beginPath();
              g.arc(x, y, 4.4, -1.2, 1.2);
              g.stroke();
            }
          }
        }, 0.5);
      });
      cut(g, () => {
        trace(g, 'M 62 106 C 72 116, 84 122, 96 122 C 88 114, 80 108, 66 102 Z', 1.3);
        trace(g, 'M 58 78 C 66 90, 66 110, 58 122', 1.8);
        trace(g, 'M 62 94 C 90 90, 120 92, 148 99', 0.9);
        ring(g, 44, 94, 5, 1.4);
        line(g, 1.3, 28, 101, 37, 104);
        disc(g, 42.5, 92.5, 1);
      });
    },
    bevel: 12,
  },
  {
    name: 'Four legs',
    // An early four-legged animal leaving the water, long tail behind it.
    paint(g) {
      const toes = (x, y, a0) => {
        for (let t = 0; t < 4; t++) {
          const a = a0 + t * 0.32;
          line(g, 1.2, x, y, x + Math.cos(a) * 6, y + Math.sin(a) * 6);
        }
      };
      // a walking gait: one front and the opposite hind leg reach forward
      faint(g, 0.65, () => {
        tube(g, [[82, 112], [90, 125], [96, 139]], taper(3.6, 2.4));
        toes(96, 139, Math.PI * 0.45);
        tube(g, [[124, 114], [116, 126], [108, 139]], taper(4.4, 2.6));
        toes(108, 139, Math.PI * 0.6);
      });
      const spine = [[26, 106], [44, 102], [62, 104], [84, 106], [106, 106], [128, 108], [150, 112], [172, 116], [196, 122]];
      tube(g, spine, (f) => {
        if (f < 0.12) return 6 + (f / 0.12) * 5;
        if (f < 0.18) return 9.5;
        if (f < 0.52) return 10 + Math.sin(((f - 0.18) / 0.34) * Math.PI) * 1.6;
        return Math.max(0.6, 9.5 * Math.pow(1 - (f - 0.52) / 0.48, 1.05));
      });
      faint(g, 0.45, () => fill(g, 'M 140 104 C 156 96, 176 102, 196 116 C 176 110, 158 108, 140 112 Z'));
      fill(g, 'M 20 108 C 24 100, 38 95, 54 96 L 62 114 C 48 118, 32 116, 20 110 Z');
      tube(g, [[70, 112], [58, 124], [50, 138]], taper(4.4, 2.8));
      toes(50, 138, Math.PI * 0.6);
      tube(g, [[134, 114], [146, 126], [156, 138]], taper(5, 3));
      toes(156, 138, Math.PI * 0.42);
      cut(g, () => {
        trace(g, 'M 21 109 C 32 112, 46 112, 58 108', 1.2);
        ring(g, 44, 101, 3.2, 1);
        for (let x = 74; x < 140; x += 7) line(g, 0.8, x, 98, x + 2, 112);
      }, 0.8);
      disc(g, 44, 101, 1.6);
    },
    bevel: 8,
  },
  {
    name: 'Dinosaur',
    // A great hunter in profile, while a falling star crosses the sky.
    paint(g) {
      faint(g, 0.7, () => {
        tube(g, [[132, 100], [138, 124]], taper(12, 8));
        tube(g, [[138, 124], [150, 150]], taper(6, 4));
        tube(g, [[150, 152], [134, 160]], 3);
      });
      tube(g, [[136, 86], [158, 82], [178, 80], [198, 76]], taper(15, 0.8));
      oval(g, 114, 92, 32, 24, 0.15);
      tube(g, [[66, 64], [80, 74], [94, 84]], taper(12, 15));
      fill(g, 'M 16 66 C 18 58, 28 52, 44 50 C 56 48, 66 50, 72 56 L 76 70 C 70 78, 62 82, 50 84 C 38 86, 26 82, 18 76 Z');
      cut(g, () => {
        tube(g, [[118, 112], [114, 126]], 16.5);
        tube(g, [[114, 126], [124, 154]], taper(8.5, 6));
      });
      tube(g, [[118, 100], [114, 126]], taper(15, 9));
      tube(g, [[114, 126], [124, 154]], taper(7, 4.5));
      tube(g, [[124, 156], [106, 164]], taper(3.6, 2.4));
      tube(g, [[92, 100], [88, 108], [80, 112]], taper(2.6, 1.6));
      cut(g, () => {
        trace(g, 'M 18 72 C 32 74, 48 74, 68 69', 1.4);
        ring(g, 54, 58, 2.6, 1.1);
        for (let x = 22; x < 64; x += 4.5) line(g, 0.8, x, 73, x + 1, 76.5);
        for (let i = 0; i < 6; i++) trace(g, `M ${98 + i * 7} ${76 + i * 0.5} q 3 10 0 22`, 0.8);
      }, 0.85);
      disc(g, 54, 58, 1.4);
      // the falling star
      soft(g, 170, 28, 4.5, 1);
      disc(g, 170, 28, 1.8);
      faint(g, 0.35, () => tube(g, [[171, 27], [184, 15], [198, 4]], taper(1.8, 0.3)));
    },
    bevel: 9,
  },
  {
    name: 'Bird',
    // The dinosaurs' heirs: a bird flying to the left, both wings raised in a V.
    paint(g) {
      // the near wing rises up and back; the far one, mirrored, up and forward behind it
      const wing = () => {
        fill(g, 'M 95 108 C 103 92, 117 72, 133 53 L 154 67 C 142 83, 130 100, 120 113 Z');
        // primaries fanning from the wrist, overlapping at the base, parted at the tips
        [[145, 14], [153, 13], [161, 15], [168, 19], [174, 25], [178, 33], [180, 42], [180, 52]].forEach(([x, y], k) => tube(g, [[133 + k * 2.6, 55 + k * 1.7], [x, y]], taper(4, 1.2)));
        // secondaries along the trailing edge
        for (let k = 0; k < 6; k++) disc(g, 121 + k * 6, 110 - k * 8.4, 4.4);
      };
      faint(g, 0.6, () => {
        g.save();
        g.translate(196, -4);
        g.scale(-1, 1);
        wing();
        g.restore();
      });
      fill(g, 'M 128 106 L 160 99 L 156 110 L 161 121 L 128 117 Z');
      oval(g, 100, 112, 31, 11, -0.04);
      disc(g, 68, 106, 8.2);
      fill(g, 'M 61 103 L 47 107.5 L 61 110 Z');
      wing();
      cut(g, () => {
        for (let r = 0; r < 3; r++) for (let k = 0; k < 6; k++) {
          g.lineWidth = 0.8;
          g.beginPath();
          g.arc(108 + r * 5 + k * 4, 102 - k * 8.6 - r * 2.5, 3.4, 0.2, Math.PI - 0.2);
          g.stroke();
        }
        for (let x = 134; x < 158; x += 4.5) line(g, 0.7, 130, 111, x, 104 + (x - 134) * 0.2);
        ring(g, 66, 104, 2.2, 0.9);
      }, 0.6);
      disc(g, 66, 104, 1.2);
      line(g, 1.2, 104, 122, 110, 129);
    },
    bevel: 7,
  },
  {
    name: 'Mammal',
    // A wolf on the move: warm blood, fur and a long stride.
    paint(g) {
      const leg = (pts, r0, r1, paw) => {
        tube(g, pts, taper(r0, r1));
        oval(g, paw[0], paw[1], 4.2, 2, 0);
      };
      faint(g, 0.7, () => {
        leg([[82, 110], [86, 134], [88, 158]], 4.6, 2.8, [86, 160]);
        leg([[146, 104], [152, 128], [148, 146], [152, 158]], 6, 2.8, [150, 160]);
      });
      tube(g, [[146, 92], [164, 104], [176, 122], [180, 140]], (f) => 4 + Math.sin(f * Math.PI) * 4.5);
      oval(g, 108, 98, 40, 17, 0.03);
      oval(g, 74, 100, 16, 18, 0.2);
      tube(g, [[72, 90], [58, 76], [48, 70]], taper(11, 9));
      disc(g, 44, 70, 10);
      tube(g, [[38, 73], [22, 80]], taper(5.5, 2.6));
      fill(g, 'M 40 62 L 44 46 L 52 60 Z');
      fill(g, 'M 48 62 L 56 48 L 58 64 Z');
      cut(g, () => {
        tube(g, [[70, 112], [66, 136]], 7);
        tube(g, [[136, 104], [142, 128]], 9);
      });
      leg([[70, 108], [66, 134], [64, 158]], 5, 3, [62, 160]);
      leg([[136, 100], [142, 126], [134, 144], [136, 158]], 7, 3, [134, 160]);
      cut(g, () => {
        for (let i = 0; i < 26; i++) {
          const x = 72 + (i % 13) * 6.4, y = 88 + Math.floor(i / 13) * 14;
          line(g, 0.7, x, y, x + 4, y + 5);
        }
        line(g, 0.9, 22, 81, 34, 78);
        ring(g, 43, 67, 2, 0.9);
      }, 0.55);
      disc(g, 43, 67, 1.1);
      disc(g, 21.5, 79, 1.4);
      moon(g, 1);
    },
    bevel: 8,
  },
  {
    name: 'Ape',
    // Knuckles down, head forward: one step from standing.
    paint(g) {
      faint(g, 0.7, () => {
        tube(g, [[94, 92], [92, 126], [94, 160]], taper(6, 5));
        oval(g, 94, 163, 7, 4);
        tube(g, [[124, 112], [136, 140], [124, 160]], taper(7.5, 5.5));
        oval(g, 120, 163, 10, 4);
      });
      oval(g, 110, 96, 38, 25, 0.28);
      tube(g, [[70, 76], [86, 88]], 10);
      disc(g, 64, 68, 15);
      oval(g, 51, 76, 11, 9, 0.2);
      oval(g, 58, 59, 11.5, 4.5, 0.12);
      cut(g, () => {
        tube(g, [[80, 104], [74, 124], [70, 160]], taper(9, 8));
        tube(g, [[146, 124], [154, 138], [146, 160]], taper(11, 8));
      });
      tube(g, [[84, 84], [74, 122], [70, 158]], taper(7, 5.5));
      oval(g, 68, 162, 8.5, 4.5);
      tube(g, [[136, 108], [154, 136], [146, 158]], taper(9, 6));
      oval(g, 140, 162, 12, 4.5);
      cut(g, () => {
        trace(g, 'M 70 50 C 82 54, 86 68, 82 84', 1.8);
        trace(g, 'M 44 82 C 48 84, 54 84, 58 82', 1.3);
        for (let i = 0; i < 30; i++) {
          const x = 86 + (i % 10) * 6, y = 82 + Math.floor(i / 10) * 9 + (i % 10) * 1.6;
          line(g, 0.7, x, y, x + 3, y + 5);
        }
      }, 0.6);
      cut(g, () => disc(g, 58, 66, 2));
      disc(g, 58, 66, 1);
      disc(g, 76, 68, 4.5);
      moon(g, 0.55);
    },
    bevel: 9,
  },
  {
    name: 'Human',
    // Upright at last, striding on.
    paint(g) {
      faint(g, 0.7, () => {
        tube(g, [[102, 56], [90, 80], [82, 100]], taper(4.6, 4));
        disc(g, 81, 103, 4.4);
        tube(g, [[104, 104], [114, 140], [124, 172]], taper(7, 5));
        tube(g, [[122, 175], [134, 177]], 3.2);
      });
      fill(g, 'M 86 50 C 92 45, 110 45, 114 51 L 110 104 C 104 111, 94 111, 90 104 Z');
      tube(g, [[97, 38], [99, 50]], 5);
      disc(g, 95, 29, 12);
      cut(g, () => {
        tube(g, [[100, 60], [108, 80], [118, 100]], 6.4);
        tube(g, [[97, 112], [84, 140], [78, 176]], taper(9, 7.4));
      });
      tube(g, [[98, 56], [108, 80], [118, 100]], taper(4.6, 4));
      disc(g, 119, 103, 4.4);
      tube(g, [[97, 104], [84, 140], [78, 174]], taper(7.5, 5.5));
      tube(g, [[80, 178], [66, 179]], 3.2);
      cut(g, () => {
        trace(g, 'M 90 64 C 96 70, 104 70, 110 64', 0.9);
        trace(g, 'M 92 84 C 98 88, 104 88, 108 84', 0.9);
      }, 0.5);
      moon(g, 0.22);
    },
    bevel: 6,
  },
  {
    name: 'Mind',
    // The same head from here on: first holding a living brain.
    paint(g) {
      head(g);
      brain(g);
    },
    bevel: 8,
  },
  {
    name: 'Machine',
    align: 0.85,
    // The brain rebuilt as circuitry: a processor where it sat, its traces
    // branching through the skull and a bus running down the neck like a spine.
    paint(g) {
      head(g, 0.05);
      const rand = random(19);
      const [cx, cy] = [110, 74];
      const room = (x, y) => inside(HEAD, x, y) && inside(HEAD, x + 3, y) && inside(HEAD, x - 3, y) && inside(HEAD, x, y + 3) && inside(HEAD, x, y - 3);
      for (let k = 0; k < 4; k++) {
        const out = [[0, -1], [1, 0], [0, 1], [-1, 0]][k], side = [out[1], -out[0]];
        for (let i = 0; i < 7; i++) {
          // out from a pin, then on in 45 degree turns, to a via
          const along = -13.5 + i * 4.5;
          let x = cx + out[0] * 16 + side[0] * along, y = cy + out[1] * 16 + side[1] * along;
          g.fillRect(x - 0.9 - out[0] * 2, y - 0.9 - out[1] * 2, 1.8 + Math.abs(out[0]) * 2, 1.8 + Math.abs(out[1]) * 2);
          const pts = [[x, y]];
          let dir = out;
          const spread = Math.sign(along) || 1;
          for (let step = 0; step < 7; step++) {
            const len = (step ? 5 : 3 + Math.abs(along) * 0.6) + rand() * 9;
            const nx = x + dir[0] * len, ny = y + dir[1] * len;
            if (!room(nx, ny)) break;
            x = nx;
            y = ny;
            pts.push([x, y]);
            const diag = [out[0] + side[0] * spread, out[1] + side[1] * spread];
            const l = Math.hypot(diag[0], diag[1]);
            dir = dir === out && rand() < 0.75 ? [diag[0] / l, diag[1] / l] : out;
          }
          if (pts.length > 1) {
            line(g, 1.3, ...pts.flat());
            ring(g, x, y, 1.9, 1.1);
          }
        }
      }
      // the bus down the neck
      for (let j = 0; j < 5; j++) line(g, 1.2, cx - 6 + j * 3, cy + 16, cx - 6 + j * 3, 118, 104 + j * 4.6, 150, 104 + j * 4.6, 186);
      g.beginPath();
      g.roundRect(cx - 15, cy - 15, 30, 30, 2.5);
      g.fill();
      cut(g, () => {
        g.lineWidth = 1.2;
        g.beginPath();
        g.roundRect(cx - 9, cy - 9, 18, 18, 1.5);
        g.stroke();
        disc(g, cx - 11.5, cy - 11.5, 1.5);
        for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) disc(g, cx - 4.5 + i * 3, cy - 4.5 + j * 3, 0.7);
      });
      // a few components on the board
      for (let i = 0; i < 16; i++) {
        let x, y, tries = 0;
        do {
          x = 62 + rand() * 96;
          y = 28 + rand() * 140;
        } while ((!room(x, y) || Math.hypot(x - cx, y - cy) < 28) && ++tries < 50);
        const w = 3 + rand() * 5, h = 2 + rand() * 3, turn = rand() < 0.5;
        faint(g, 0.85, () => g.fillRect(x - (turn ? h : w) / 2, y - (turn ? w : h) / 2, turn ? h : w, turn ? w : h));
      }
    },
    bevel: 4,
  },
  {
    name: 'AI',
    align: 1,
    // The mind as pure geometry: a mesh of nodes and edges, reaching out into the stars.
    paint(g) {
      const pts = meshPoints();
      const edges = new Set();
      for (const t of delaunay(pts)) {
        const cx = (pts[t[0]][0] + pts[t[1]][0] + pts[t[2]][0]) / 3, cy = (pts[t[0]][1] + pts[t[1]][1] + pts[t[2]][1]) / 3;
        if (!inside(HEAD, cx, cy)) continue;
        for (const [a, b] of [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]]) edges.add(a < b ? `${a},${b}` : `${b},${a}`);
      }
      for (const e of edges) {
        const [a, b] = e.split(',').map(Number);
        line(g, 1.1, pts[a][0], pts[a][1], pts[b][0], pts[b][1]);
      }
      // a few threads out to nodes beyond the head
      for (const [from, x, y] of [[0, 120, 4], [22, 186, 30], [21, 194, 92], [20, 184, 150], [23, 170, 10]]) {
        faint(g, 0.6, () => line(g, 0.9, HEAD[from][0], HEAD[from][1], x, y));
        disc(g, x, y, 2.2);
      }
      pts.forEach(([x, y], i) => disc(g, x, y, i < HEAD.length ? 2.2 : 2.8));
    },
    // the nodes catch the light like small stars; the edges lie flat
    relief(g) {
      meshPoints().forEach(([x, y], i) => dome(g, x, y, i < HEAD.length ? 2.6 : 3.2, 0.12));
    },
  },
];

// The nodes of the AI's mesh: the head's outline, then points spread inside it.
function meshPoints() {
  const rand = random(20);
  const pts = HEAD.slice();
  for (let tries = 0; pts.length < HEAD.length + 46 && tries < 4000; tries++) {
    const x = 50 + rand() * 112, y = 22 + rand() * 162;
    if (inside(HEAD, x, y) && pts.every(([px, py]) => Math.hypot(px - x, py - y) > 12)) pts.push([x, y]);
  }
  return pts;
}

// The cells of a hollow ball, back to front, each with its place on the sphere (z, 1 = nearest).
function blastula() {
  const cells = [], n = 64, R = 62;
  for (let i = 0; i < n; i++) {
    const y = 1 - (2 * (i + 0.5)) / n, r = Math.sqrt(1 - y * y), a = i * 2.39996;
    const v = [Math.cos(a) * r, y, Math.sin(a) * r];
    // tilt the ball a little towards the light
    const ty = v[1] * Math.cos(0.5) - v[2] * Math.sin(0.5), tz = v[1] * Math.sin(0.5) + v[2] * Math.cos(0.5);
    if (tz < -0.15) continue;
    cells.push({ x: 100 + v[0] * R, y: 100 + ty * R, z: tz, r: 12.5 * (0.75 + 0.25 * Math.max(0, tz)) });
  }
  return cells.sort((a, b) => a.z - b.z);
}
