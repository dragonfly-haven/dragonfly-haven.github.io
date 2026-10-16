// The twenty stages of the evolution animation, from organic matter to AI.
// Each stage paints its silhouette into a 200 × 200 unit box. `faint` paints
// areas that are filled more sparsely (bells, cytoplasm), and `align` (0 to 1)
// is how strongly the triangles line up at rest: loose for life, ordered for machines.

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
const fill = (g, d) => g.fill(new Path2D(d));
const trace = (g, d, w) => {
  g.lineWidth = w;
  g.stroke(new Path2D(d));
};

function line(g, w, ...p) {
  g.lineWidth = w;
  g.beginPath();
  g.moveTo(p[0], p[1]);
  for (let i = 2; i < p.length; i += 2) g.lineTo(p[i], p[i + 1]);
  g.stroke();
}

// Erases whatever `paint` draws: gaps, holes and grooves.
function cut(g, paint) {
  g.save();
  g.globalCompositeOperation = 'destination-out';
  paint();
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
  const steps = Math.max(2, Math.ceil(path.total / 0.5));
  g.beginPath();
  for (let s = 0; s <= steps; s++) {
    const f = s / steps, [x, y] = path.at(f), rr = Math.max(0.2, radius(f));
    g.moveTo(x + rr, y);
    g.arc(x, y, rr, 0, TAU);
  }
  g.fill();
}
const taper = (r0, r1) => (f) => r0 + (r1 - r0) * f;

// Mirrors everything `paint` draws across the vertical centre line.
function mirrored(g, paint) {
  paint();
  g.save();
  g.translate(200, 0);
  g.scale(-1, 1);
  paint();
  g.restore();
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

// A head in profile, facing left, as an outline and a few landmarks inside it.
const HEAD = [
  [104, 18], [82, 23], [66, 36], [58, 54], [57, 70], [52, 83], [42, 99], [50, 106], [54, 110], [50, 118],
  [55, 124], [50, 130], [56, 140], [54, 150], [66, 160], [88, 162], [94, 186], [142, 186], [138, 160],
  [148, 138], [160, 110], [162, 80], [152, 48], [132, 26],
];
const FACE = [
  [72, 80], [78, 66], [84, 98], [74, 116], [66, 127], [90, 142], [118, 98], [122, 84], [116, 112],
  [98, 70], [86, 44], [112, 40], [134, 54], [142, 80], [144, 108], [116, 150], [118, 172], [104, 158],
  [100, 96], [98, 122], [128, 128], [120, 62],
];

function jellyBell() {
  const p = new Path2D('M 46 86 C 46 26, 154 26, 154 86');
  for (let k = 0; k < 8; k++) p.quadraticCurveTo(154 - k * 13.5 - 6.75, 93, 154 - (k + 1) * 13.5, 86);
  p.closePath();
  return p;
}

// A softly irregular oval membrane.
function cellWall() {
  const p = new Path2D();
  for (let i = 0; i <= 160; i++) {
    const a = (i / 160) * TAU;
    const r = 1 + 0.04 * Math.sin(3 * a + 0.6) + 0.03 * Math.sin(5 * a + 2.1);
    const x = 100 + Math.cos(a) * 76 * r, y = 102 + Math.sin(a) * 62 * r;
    if (i) p.lineTo(x, y);
    else p.moveTo(x, y);
  }
  p.closePath();
  return p;
}

export const STAGES = [
  {
    name: 'Organic matter',
    paint(g) {
      const rand = random(3);
      for (let i = 0; i < 240; i++) {
        const arm = i % 3, t = Math.pow(rand(), 0.75);
        const a = (arm * TAU) / 3 + t * 3.4 + (rand() - 0.5) * 0.9;
        const r = 8 + t * 80 + (rand() - 0.5) * 10;
        disc(g, 100 + Math.cos(a) * r, 100 + Math.sin(a) * r * 0.84, 1.3 + rand() * rand() * 4.2);
      }
    },
  },
  {
    name: 'Molecules',
    paint(g) {
      const ringAt = (cx, cy, R, n, start) => Array.from({ length: n }, (_, k) => [cx + R * Math.cos(start + (k * TAU) / n), cy + R * Math.sin(start + (k * TAU) / n)]);
      const A = ringAt(54, 92, 17, 6, -Math.PI / 2);
      const B = ringAt(54 + 17 * Math.sqrt(3), 92, 17, 6, -Math.PI / 2);
      const S = ringAt(128, 126, 14, 5, -Math.PI / 2);
      const bonds = [];
      for (const r of [A, B, S]) r.forEach((p, i) => bonds.push([p, r[(i + 1) % r.length]]));
      const O1 = [54, 56], N1 = [24, 112], C1 = [114, 74], C2 = [158, 110], O2 = [164, 90], P = [170, 70];
      const OP = [[189, 64], [158, 52], [184, 86]], O3 = [146, 156], O4 = [110, 156];
      bonds.push([A[4], N1], [B[1], C1], [B[2], S[4]], [S[1], C2], [C2, O2], [O2, P], [S[2], O3], [S[3], O4], ...OP.map((o) => [P, o]));
      for (const [[x0, y0], [x1, y1]] of bonds) line(g, 3, x0, y0, x1, y1);
      // a double bond up to the oxygen
      for (const o of [-2.6, 2.6]) line(g, 2.4, A[0][0] + o, A[0][1], O1[0] + o, O1[1] + 4);
      ring(g, B[0][0], 92, 8.5, 2.2);
      for (const [x, y] of [...A, ...B, ...S, C1, C2]) disc(g, x, y, 3.4);
      for (const [x, y] of [O1, N1, O2, O3, O4, ...OP]) disc(g, x, y, 5.4);
      disc(g, P[0], P[1], 7);
    },
  },
  {
    name: 'Replicators',
    paint(g) {
      const wave = (x) => Math.sin(x / 8) * 1.6;
      // the parent double strand
      const top = [], bottom = [];
      for (let x = 12; x <= 90; x += 2) {
        top.push(x, 89 + wave(x));
        bottom.push(x, 111 + wave(x));
      }
      line(g, 4, ...top);
      line(g, 4, ...bottom);
      for (let x = 16; x <= 86; x += 7) line(g, 2.6, x, 89 + wave(x), x, 111 + wave(x));
      // it unzips into two arms, and each arm templates a new partner strand
      const rand = random(5);
      for (const side of [-1, 1]) {
        const p0 = [90, 100 + side * 11 + wave(90)], p1 = [124, 100 + side * 16], p2 = [184, 100 + side * 68];
        const at = (t) => {
          const u = 1 - t;
          return [u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]];
        };
        const inward = (t) => {
          const dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]);
          const dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]);
          const l = Math.hypot(dx, dy);
          let nx = -dy / l, ny = dx / l;
          if (Math.sign(ny) !== -side) {
            nx = -nx;
            ny = -ny;
          }
          return [nx, ny];
        };
        const arm = [];
        for (let t = 0; t <= 1.0001; t += 0.02) arm.push(...at(t));
        line(g, 4, ...arm);
        const partner = [];
        for (let t = 0.06; t <= 1; t += 0.072) {
          const [x, y] = at(t), [nx, ny] = inward(t);
          if (t < 0.56) {
            line(g, 2.6, x, y, x + nx * 13, y + ny * 13);
            partner.push(x + nx * 13, y + ny * 13);
          } else {
            line(g, 2.6, x, y, x + nx * 6, y + ny * 6);
            // loose building blocks drifting in to pair up
            const d = 16 + rand() * 8, a = (rand() - 0.5) * 0.8;
            const bx = x + nx * d, by = y + ny * d;
            const sx = Math.cos(a) * nx - Math.sin(a) * ny, sy = Math.sin(a) * nx + Math.cos(a) * ny;
            line(g, 2.4, bx, by, bx + sx * 6, by + sy * 6);
            disc(g, bx + sx * 7.5, by + sy * 7.5, 2.6);
          }
        }
        line(g, 4, ...partner);
      }
    },
  },
  {
    name: 'DNA',
    paint(g) {
      g.translate(100, 100);
      g.rotate(-0.42);
      const A = 24, L = 74;
      for (let y = -86; y <= 86; y += 6.4) {
        const x = A * Math.sin((y / L) * TAU);
        if (Math.abs(x) > 4) line(g, 2.4, x, y, -x, y);
      }
      for (const side of [1, -1]) {
        for (let y = -94; y < 94; y += 1) {
          const p = (y / L) * TAU, q = ((y + 1) / L) * TAU;
          const near = (side * Math.cos(p) + 1) / 2;
          line(g, 3 + near * 3.6, side * A * Math.sin(p), y, side * A * Math.sin(q), y + 1);
        }
      }
    },
  },
  {
    name: 'Protocell',
    paint(g) {
      ring(g, 100, 100, 66, 3.4);
      ring(g, 100, 100, 59.5, 3.4);
      trace(g, 'M 64 96 C 72 80, 88 108, 98 92 S 116 78, 130 96', 3.2);
      trace(g, 'M 78 128 C 90 116, 104 138, 120 124', 3.2);
      trace(g, 'M 84 64 C 96 74, 106 58, 120 68', 3.2);
      ring(g, 136, 120, 7, 2.4);
      ring(g, 68, 126, 5.5, 2.4);
      for (const [x, y] of [[104, 108], [60, 78], [140, 76], [112, 148], [54, 106], [96, 146]]) disc(g, x, y, 2.6);
    },
  },
  {
    name: 'Bacterium',
    paint(g) {
      g.translate(100, 100);
      g.rotate(-0.36);
      g.translate(-100, -100);
      const tail = [];
      for (let x = 148; x <= 196; x += 1) tail.push(x, 100 + Math.sin((x - 148) / 5.5) * 6 * Math.min(1, (x - 148) / 10));
      line(g, 3, ...tail);
      for (let x = 72; x <= 128; x += 11) {
        line(g, 1.6, x, 80, x + 2, 70);
        line(g, 1.6, x + 5, 120, x + 3, 130);
      }
      for (const a of [2.5, 2.9, 3.3, 3.7]) line(g, 1.6, 66 + Math.cos(a) * 20, 100 + Math.sin(a) * 20, 66 + Math.cos(a) * 30, 100 + Math.sin(a) * 30);
      g.beginPath();
      g.roundRect(44, 78, 108, 44, 22);
      g.fill();
      cut(g, () => {
        g.lineWidth = 2;
        g.beginPath();
        g.roundRect(50, 84, 96, 32, 16);
        g.stroke();
        trace(g, 'M 66 100 C 76 92, 84 108, 96 99 S 116 92, 130 102', 2.2);
      });
    },
  },
  {
    name: 'Cell with a nucleus',
    paint(g) {
      g.lineWidth = 4.5;
      g.stroke(cellWall());
      // nucleus with its envelope and nucleolus
      ring(g, 86, 96, 23, 4.5);
      disc(g, 90, 92, 8);
      for (const [x, y] of [[76, 104], [96, 108], [74, 88], [100, 86]]) disc(g, x, y, 2.2);
      // endoplasmic reticulum hugging the nucleus
      trace(g, 'M 58 112 C 50 92, 58 70, 78 62', 2.4);
      trace(g, 'M 66 126 C 74 132, 92 134, 106 126', 2.4);
      // golgi stack
      for (let j = 0; j < 4; j++) {
        g.lineWidth = 3;
        g.beginPath();
        g.arc(150, 118, 8 + j * 5.5, Math.PI * 0.75, Math.PI * 1.45);
        g.stroke();
      }
      // mitochondria
      for (const [x, y, a] of [[134, 70, 0.4], [64, 140, -0.3], [118, 146, 0.9]]) {
        g.save();
        g.translate(x, y);
        g.rotate(a);
        oval(g, 0, 0, 12, 6);
        cut(g, () => line(g, 1.6, -7.5, 0, -4.5, -3.2, -1.5, 3.2, 1.5, -3.2, 4.5, 3.2, 7.5, 0));
        g.restore();
      }
      for (const [x, y, r] of [[156, 82, 5], [44, 96, 4.5], [104, 60, 3.5], [160, 140, 3.5]]) ring(g, x, y, r, 2.2);
    },
  },
  {
    name: 'Many cells',
    paint(g) {
      ring(g, 100, 100, 70, 2.6);
      const cells = [[100, 100]];
      for (let k = 0; k < 6; k++) cells.push([100 + 40 * Math.cos((k * Math.PI) / 3 + 0.3), 100 + 40 * Math.sin((k * Math.PI) / 3 + 0.3)]);
      for (const [x, y] of cells) disc(g, x, y, 18.4);
      cut(g, () => cells.forEach(([x, y]) => disc(g, x + 3, y - 2, 4.2)));
    },
  },
  {
    name: 'Jellyfish',
    paint(g) {
      g.lineWidth = 3.2;
      g.stroke(jellyBell());
      for (const [x, y] of [[80, 64], [100, 56], [120, 64]]) ring(g, x, y, 6.5, 2.4);
      for (const [x0, ph] of [[88, 0], [96, 1.6], [104, 3.1], [112, 4.4]]) {
        const pts = [];
        for (let i = 0; i <= 8; i++) pts.push([x0 + Math.sin(i * 0.9 + ph) * 5 + (x0 - 100) * i * 0.05, 86 + i * 10]);
        tube(g, pts, (f) => 3.4 - f * 1.6 + Math.sin(f * 40 + ph) * 1.1);
      }
      for (let k = 0; k < 11; k++) {
        const x0 = 52 + k * 9.6, pts = [];
        for (let i = 0; i <= 10; i++) pts.push([x0 + Math.sin(i * 0.7 + k) * 4 + (x0 - 100) * i * 0.012, 88 + i * 9.5]);
        tube(g, pts, (f) => 1.2 - f * 0.4);
      }
    },
    faint(g) {
      g.fill(jellyBell());
    },
  },
  {
    name: 'Trilobite',
    paint(g) {
      fill(g, 'M 46 78 C 46 42, 70 26, 100 26 C 130 26, 154 42, 154 78 L 162 122 L 146 82 L 54 82 L 38 122 Z');
      for (let j = 0; j < 9; j++) {
        const y0 = 86 + j * 7, w = 44 - j * 2.4;
        fill(g, `M ${100 - w} ${y0 + 2} L ${100 - w + 4} ${y0} L ${100 + w - 4} ${y0} L ${100 + w} ${y0 + 2} L ${100 + w - 3} ${y0 + 5.2} L ${100 - w + 3} ${y0 + 5.2} Z`);
      }
      fill(g, 'M 72 150 C 72 166, 86 176, 100 176 C 114 176, 128 166, 128 150 Z');
      cut(g, () => {
        trace(g, 'M 88 80 C 86 62, 90 40, 100 38 C 110 40, 114 62, 112 80', 2.2);
        trace(g, 'M 66 60 C 70 52, 78 52, 80 60', 2.2);
        trace(g, 'M 134 60 C 130 52, 122 52, 120 60', 2.2);
        line(g, 2.2, 87, 86, 90, 164);
        line(g, 2.2, 113, 86, 110, 164);
        for (let j = 0; j < 3; j++) trace(g, `M ${80 + j * 2} ${156 + j * 6} Q 100 ${160 + j * 6} ${120 - j * 2} ${156 + j * 6}`, 1.6);
      });
    },
  },
  {
    name: 'Fish',
    paint(g) {
      fill(g, 'M 28 100 C 44 76, 76 64, 108 68 C 130 71, 144 86, 150 94 L 150 104 C 144 112, 130 124, 108 128 C 76 132, 44 124, 28 100 Z');
      fill(g, 'M 144 94 L 186 60 Q 170 99 186 138 L 144 104 Z');
      fill(g, 'M 76 70 C 88 46, 108 40, 124 44 C 116 56, 114 66, 116 74 Z');
      fill(g, 'M 104 126 C 110 140, 122 146, 132 144 C 126 136, 124 128, 124 122 Z');
      fill(g, 'M 72 128 C 74 140, 82 146, 90 146 C 88 138, 88 132, 88 128 Z');
      cut(g, () => {
        trace(g, 'M 62 106 C 72 116, 84 122, 96 122 C 88 114, 80 108, 66 102 Z', 1.8);
        trace(g, 'M 58 78 C 66 90, 66 110, 58 122', 2.2);
        ring(g, 44, 94, 5, 1.8);
        line(g, 1.6, 28, 101, 37, 104);
        for (const [x, y] of [[180, 70], [175, 85], [172, 99], [175, 113], [180, 128]]) line(g, 1.2, 152, 99, x, y);
      });
    },
  },
  {
    name: 'Four legs',
    paint(g) {
      const spine = along([[58, 20], [64, 44], [80, 70], [96, 96], [104, 120], [100, 144], [86, 164], [66, 176], [44, 178], [28, 168]]);
      tube(g, spine, (f) => {
        if (f < 0.035) return 5 + (f / 0.035) * 6;
        if (f < 0.1) return 11;
        if (f < 0.14) return 11 - (f - 0.1) * 60;
        if (f < 0.46) return 8.6 + Math.sin(((f - 0.14) / 0.32) * Math.PI) * 2.4;
        return Math.max(0.7, 8.6 * Math.pow(1 - (f - 0.46) / 0.54, 1.1));
      });
      for (const [f, hind] of [[0.2, false], [0.46, true]]) {
        for (const side of [-1, 1]) {
          const [x, y, dx, dy] = spine.at(f);
          const nx = -dy * side, ny = dx * side, back = hind ? -1 : 1;
          const kx = x + nx * 16 - dx * 2 * back, ky = y + ny * 16 - dy * 2 * back;
          const fx = kx + nx * 3 + dx * 10 * back, fy = ky + ny * 3 + dy * 10 * back;
          tube(g, [[x, y], [kx, ky], [fx, fy]], taper(4.2, 2.6));
          const base = Math.atan2(fy - ky, fx - kx);
          for (let t = 0; t < 4; t++) {
            const a = base - 0.9 + t * 0.6;
            line(g, 2.2, fx, fy, fx + Math.cos(a) * 6, fy + Math.sin(a) * 6);
          }
        }
      }
      const [hx, hy, hdx, hdy] = spine.at(0.065);
      disc(g, hx - hdy * 9.5, hy + hdx * 9.5, 3.4);
      disc(g, hx + hdy * 9.5, hy - hdx * 9.5, 3.4);
    },
  },
  {
    name: 'Dinosaur',
    paint(g) {
      tube(g, [[100, 124], [102, 148], [106, 170]], taper(6.4, 5.4));
      tube(g, [[146, 118], [150, 146], [154, 170]], taper(7.4, 6));
      oval(g, 114, 106, 46, 29, -0.06);
      tube(g, [[150, 104], [172, 114], [186, 126], [198, 146]], taper(14, 0.8));
      tube(g, [[84, 98], [66, 74], [54, 50], [44, 34]], taper(15, 6));
      oval(g, 38, 30, 10.5, 6.5, -0.25);
      cut(g, () => {
        tube(g, [[86, 134], [86, 148], [84, 174]], taper(9.6, 8.4));
        tube(g, [[132, 134], [134, 148], [136, 174]], taper(10.6, 8.4));
        disc(g, 34, 28, 1.6);
      });
      tube(g, [[86, 112], [86, 146], [84, 170]], taper(7.6, 6.4));
      tube(g, [[132, 112], [134, 146], [136, 170]], taper(8.6, 6.4));
    },
  },
  {
    name: 'Bird',
    paint(g) {
      mirrored(g, () => {
        fill(g, 'M 96 90 C 82 78, 66 68, 50 66 L 44 96 C 60 104, 80 110, 96 112 Z');
        [[6, 60], [8, 71], [12, 82], [18, 92], [27, 101], [37, 107]].forEach(([x, y], k) => tube(g, [[52, 70 + k * 4.6], [x, y]], taper(4.2, 1.4)));
        for (let k = 0; k < 5; k++) disc(g, 50 + k * 9, 104 + k * 1.8, 5);
      });
      oval(g, 100, 102, 10, 24);
      disc(g, 100, 74, 8.5);
      fill(g, 'M 95 69 L 105 69 L 100 57 Z');
      fill(g, 'M 92 120 L 108 120 L 122 152 Q 100 160 78 152 Z');
    },
  },
  {
    name: 'Mammal',
    paint(g) {
      tube(g, [[156, 124], [176, 130], [190, 116], [194, 96], [188, 82]], taper(3.2, 1));
      tube(g, [[142, 136], [150, 150], [146, 162]], taper(7, 3.5));
      oval(g, 144, 164, 9, 3.2);
      tube(g, [[86, 140], [84, 162]], taper(4.5, 3.2));
      oval(g, 80, 164, 6.5, 2.8);
      oval(g, 118, 122, 44, 30, -0.06);
      fill(g, 'M 98 100 C 84 90, 64 94, 50 106 C 42 112, 32 118, 24 122 C 32 130, 50 134, 66 134 C 82 134, 96 128, 102 120 Z');
      disc(g, 88, 92, 11);
      cut(g, () => {
        trace(g, 'M 98 98 C 92 108, 78 106, 76 96', 2);
        oval(g, 85, 96, 4.5, 6, 0.4);
        disc(g, 62, 110, 3.2);
      });
      line(g, 1.4, 36, 119, 14, 110);
      line(g, 1.4, 36, 123, 12, 124);
      line(g, 1.4, 38, 126, 16, 136);
    },
  },
  {
    name: 'Ape',
    paint(g) {
      tube(g, [[94, 92], [92, 126], [94, 160]], taper(6, 5));
      oval(g, 94, 163, 7, 4);
      tube(g, [[124, 112], [136, 140], [124, 160]], taper(7.5, 5.5));
      oval(g, 120, 163, 10, 4);
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
        trace(g, 'M 70 50 C 82 54, 86 68, 82 84', 2.2);
        disc(g, 58, 66, 2);
        trace(g, 'M 44 82 C 48 84, 54 84, 58 82', 1.6);
      });
      disc(g, 76, 68, 4.5);
    },
  },
  {
    name: 'Human',
    paint(g) {
      tube(g, [[102, 56], [90, 80], [82, 100]], taper(4.6, 4));
      disc(g, 81, 103, 4.4);
      tube(g, [[104, 104], [114, 140], [124, 172]], taper(7, 5));
      tube(g, [[122, 175], [134, 177]], 3.2);
      fill(g, 'M 86 50 C 92 45, 110 45, 114 51 L 110 104 C 104 111, 94 111, 90 104 Z');
      tube(g, [[97, 38], [99, 50]], 5);
      disc(g, 95, 29, 12);
      cut(g, () => {
        tube(g, [[100, 60], [108, 80], [118, 100]], 6.6);
        tube(g, [[97, 112], [84, 140], [78, 176]], taper(9.2, 7.5));
      });
      tube(g, [[98, 56], [108, 80], [118, 100]], taper(4.6, 4));
      disc(g, 119, 103, 4.4);
      tube(g, [[97, 104], [84, 140], [78, 174]], taper(7.5, 5.5));
      tube(g, [[80, 178], [66, 179]], 3.2);
    },
  },
  {
    name: 'Mind',
    align: 0.2,
    paint(g) {
      tube(g, [[120, 132], [118, 156], [114, 178]], taper(8, 6));
      oval(g, 142, 138, 25, 15, -0.12);
      cut(g, () => {
        for (let j = 0; j < 3; j++) trace(g, `M ${124 + j * 2} ${132 + j * 6} Q 142 ${128 + j * 7} ${164 - j * 2} ${132 + j * 6}`, 1.6);
      });
      cut(g, () => fill(g, 'M 26 104 C 20 60, 60 28, 104 28 C 152 28, 180 58, 176 98 C 174 122, 158 132, 136 130 C 120 142, 96 144, 78 134 C 58 138, 30 130, 26 104 Z'));
      fill(g, 'M 28 104 C 22 62, 60 30, 104 30 C 150 30, 178 58, 174 98 C 172 120, 156 130, 136 128 C 120 140, 96 142, 78 132 C 58 136, 32 128, 28 104 Z');
      cut(g, () => {
        trace(g, 'M 56 118 C 80 104, 108 100, 140 98', 2.8);
        trace(g, 'M 116 32 C 106 56, 116 72, 102 98', 2.6);
        [
          'M 40 84 C 50 76, 56 90, 66 80 S 80 62, 88 70',
          'M 52 56 C 62 62, 70 48, 82 54 S 94 46, 100 40',
          'M 74 92 C 80 84, 90 92, 96 82',
          'M 128 40 C 132 52, 144 46, 148 58 S 160 66, 164 78',
          'M 124 70 C 132 64, 140 76, 150 70 S 162 84, 170 92',
          'M 118 84 C 124 92, 134 84, 140 92',
          'M 70 124 C 80 114, 92 126, 104 116 S 120 120, 128 112',
          'M 36 102 C 44 96, 50 108, 58 102',
          'M 150 104 C 156 110, 162 104, 168 110',
        ].forEach((d) => trace(g, d, 2.2));
      });
    },
  },
  {
    name: 'Machine',
    align: 0.85,
    paint(g) {
      for (let side = 0; side < 4; side++) {
        g.save();
        g.translate(100, 100);
        g.rotate((side * Math.PI) / 2);
        g.translate(-100, -100);
        for (let k = 0; k < 7; k++) {
          const x = 70 + k * 10, out = x - 100, bend = out * 0.5;
          const len = 8 + ((k * 7 + side * 3) % 4) * 6;
          const ey = 48 - Math.abs(bend) - len;
          g.fillRect(x - 2, 54, 4, 10);
          line(g, 2.2, x, 54, x, 48, x + bend, 48 - Math.abs(bend), x + bend, ey);
          disc(g, x + bend, ey, 3.4);
          cut(g, () => disc(g, x + bend, ey, 1.5));
        }
        g.restore();
      }
      g.beginPath();
      g.roundRect(62, 62, 76, 76, 5);
      g.fill();
      cut(g, () => {
        g.lineWidth = 2;
        g.beginPath();
        g.roundRect(74, 74, 52, 52, 3);
        g.stroke();
        disc(g, 70.5, 70.5, 3);
      });
    },
  },
  {
    name: 'AI',
    align: 1,
    // A mind rebuilt as geometry: the human head as a mesh of nodes and edges.
    paint(g) {
      const pts = HEAD.concat(FACE);
      const edges = new Set();
      for (const t of delaunay(pts)) {
        const cx = (pts[t[0]][0] + pts[t[1]][0] + pts[t[2]][0]) / 3, cy = (pts[t[0]][1] + pts[t[1]][1] + pts[t[2]][1]) / 3;
        if (!inside(HEAD, cx, cy)) continue;
        for (const [a, b] of [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]]) edges.add(a < b ? `${a},${b}` : `${b},${a}`);
      }
      for (const e of edges) {
        const [a, b] = e.split(',').map(Number);
        line(g, 2, pts[a][0], pts[a][1], pts[b][0], pts[b][1]);
      }
      pts.forEach(([x, y], i) => disc(g, x, y, i < HEAD.length ? 3 : 4));
    },
  },
];
