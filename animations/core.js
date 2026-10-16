// Shared building blocks for the two triangle animations: the common triangle
// size, palettes, seeded randomness, noise, shape sampling and drawing.

export const TRIANGLE_SIZE = 3.2; // side of every triangle, in CSS pixels
export const TAU = Math.PI * 2;

// Deep, almost black oranges, from shadow to light.
export const EMBER = ['#1d0d02', '#281203', '#341703', '#401c04', '#4d2205', '#5b2806'];
// The dragonfly's deep black.
export const INK = '#0b0908';

export const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
export const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
export const smooth = (t) => t * t * t * (t * (t * 6 - 15) + 10); // smootherstep on [0, 1]

// Turns angle `from` a fraction `k` of the short way towards `to`.
export function turn(from, to, k) {
  let d = to - from;
  d -= TAU * Math.round(d / TAU);
  return from + d * k;
}

// Mulberry32: small, fast and seedable.
export function random(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 3D simplex noise in [-1, 1], after Stefan Gustavson's public-domain reference.
const GRAD = [1, 1, 0, -1, 1, 0, 1, -1, 0, -1, -1, 0, 1, 0, 1, -1, 0, 1, 1, 0, -1, -1, 0, -1, 0, 1, 1, 0, -1, 1, 0, 1, -1, 0, -1, -1];

export function noise3(seed) {
  const rand = random(seed);
  const p = Array.from({ length: 256 }, (_, i) => i);
  for (let i = 255; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [p[i], p[j]] = [p[j], p[i]];
  }
  const perm = new Uint8Array(512);
  const mod = new Uint8Array(512);
  for (let i = 0; i < 512; i++) {
    perm[i] = p[i & 255];
    mod[i] = (perm[i] % 12) * 3;
  }
  const F = 1 / 3, G = 1 / 6;

  return (x, y, z) => {
    const s = (x + y + z) * F;
    const i = Math.floor(x + s), j = Math.floor(y + s), k = Math.floor(z + s);
    const t = (i + j + k) * G;
    const x0 = x - i + t, y0 = y - j + t, z0 = z - k + t;
    let i1, j1, k1, i2, j2, k2;
    if (x0 >= y0) {
      if (y0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 1; k2 = 0; }
      else if (x0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 0; k2 = 1; }
      else { i1 = 0; j1 = 0; k1 = 1; i2 = 1; j2 = 0; k2 = 1; }
    } else if (y0 < z0) { i1 = 0; j1 = 0; k1 = 1; i2 = 0; j2 = 1; k2 = 1; }
    else if (x0 < z0) { i1 = 0; j1 = 1; k1 = 0; i2 = 0; j2 = 1; k2 = 1; }
    else { i1 = 0; j1 = 1; k1 = 0; i2 = 1; j2 = 1; k2 = 0; }
    const x1 = x0 - i1 + G, y1 = y0 - j1 + G, z1 = z0 - k1 + G;
    const x2 = x0 - i2 + 2 * G, y2 = y0 - j2 + 2 * G, z2 = z0 - k2 + 2 * G;
    const x3 = x0 - 1 + 3 * G, y3 = y0 - 1 + 3 * G, z3 = z0 - 1 + 3 * G;
    const ii = i & 255, jj = j & 255, kk = k & 255;
    let n = 0, c, g;
    c = 0.6 - x0 * x0 - y0 * y0 - z0 * z0;
    if (c > 0) { g = mod[ii + perm[jj + perm[kk]]]; c *= c; n += c * c * (GRAD[g] * x0 + GRAD[g + 1] * y0 + GRAD[g + 2] * z0); }
    c = 0.6 - x1 * x1 - y1 * y1 - z1 * z1;
    if (c > 0) { g = mod[ii + i1 + perm[jj + j1 + perm[kk + k1]]]; c *= c; n += c * c * (GRAD[g] * x1 + GRAD[g + 1] * y1 + GRAD[g + 2] * z1); }
    c = 0.6 - x2 * x2 - y2 * y2 - z2 * z2;
    if (c > 0) { g = mod[ii + i2 + perm[jj + j2 + perm[kk + k2]]]; c *= c; n += c * c * (GRAD[g] * x2 + GRAD[g + 1] * y2 + GRAD[g + 2] * z2); }
    c = 0.6 - x3 * x3 - y3 * y3 - z3 * z3;
    if (c > 0) { g = mod[ii + 1 + perm[jj + 1 + perm[kk + 1]]]; c *= c; n += c * c * (GRAD[g] * x3 + GRAD[g + 1] * y3 + GRAD[g + 2] * z3); }
    return 32 * n;
  };
}

// Divergence-free flow from a noise field, which is what makes motion read as fluid.
export function curl(noise, x, y, z, out) {
  const e = 0.01;
  out[0] = (noise(x, y + e, z) - noise(x, y - e, z)) / (2 * e);
  out[1] = (noise(x - e, y, z) - noise(x + e, y, z)) / (2 * e);
  return out;
}

// Fills `el` with a canvas. `measure()` sizes it and calls `onResize(view)`,
// which happens again by itself whenever the element's size settles.
export function mountCanvas(el, onResize) {
  if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
  if (el.clientHeight < 2) el.style.aspectRatio = '1';
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none';
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  const view = { canvas, ctx, width: 0, height: 0, ratio: 1 };
  let timer = 0;

  const measure = () => {
    const ratio = Math.min(devicePixelRatio || 1, 2);
    const width = el.clientWidth, height = el.clientHeight;
    if (!width || !height) return;
    if (width === view.width && height === view.height && ratio === view.ratio) return;
    Object.assign(view, { width, height, ratio });
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
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

// Calls `tick(dt)` every animation frame while `el` is on screen.
export function animate(el, tick) {
  let raf = 0, last = 0;
  const loop = (now) => {
    const dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60;
    last = now;
    tick(dt);
    raf = requestAnimationFrame(loop);
  };
  const start = () => {
    if (!raf) {
      last = 0;
      raf = requestAnimationFrame(loop);
    }
  };
  const stop = () => {
    cancelAnimationFrame(raf);
    raf = 0;
  };
  const observer = new IntersectionObserver(([entry]) => (entry.isIntersecting ? start() : stop()));
  observer.observe(el);
  return {
    destroy() {
      stop();
      observer.disconnect();
    },
  };
}

// Paints `paint(g)`, drawn in shape units, into a w × h coverage mask at k mask pixels per unit.
export function rasterize(paint, w, h, k) {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const g = canvas.getContext('2d', { willReadFrequently: true });
  g.setTransform(k, 0, 0, k, 0, 0);
  g.fillStyle = g.strokeStyle = '#000';
  g.lineCap = g.lineJoin = 'round';
  paint(g);
  const rgba = g.getImageData(0, 0, w, h).data;
  const mask = new Uint8Array(w * h);
  for (let i = 0; i < mask.length; i++) mask[i] = rgba[i * 4 + 3] > 127 ? 1 : 0;
  return mask;
}

// Points on a jittered hexagonal lattice inside the mask, about `gap` mask pixels apart.
export function scatter(mask, w, h, gap, rand, jitter = 0.3) {
  const out = [];
  const row = gap * 0.8660254;
  const x0 = rand() * gap, y0 = rand() * row;
  for (let r = 0, y = y0; y < h; r++, y += row) {
    for (let x = x0 + (r & 1) * gap * 0.5; x < w; x += gap) {
      const px = x + (rand() - 0.5) * 2 * jitter * gap;
      const py = y + (rand() - 0.5) * 2 * jitter * row;
      const ix = Math.floor(px), iy = Math.floor(py);
      if (ix >= 0 && iy >= 0 && ix < w && iy < h && mask[iy * w + ix]) out.push(px, py);
    }
  }
  return out;
}

// Cells of a triangle tiling with side `a` mask pixels whose centres fall inside
// the mask, as [x, y, angle, ...]; angle points each triangle up or down.
export function tiling(mask, w, h, a, keep = () => true) {
  const out = [];
  const row = a * 0.8660254;
  for (let r = 0; r * row < h; r++) {
    for (let c = 0; (c * a) / 2 < w; c++) {
      const up = (r + c) % 2 === 0;
      const x = (c * a) / 2, y = r * row + (up ? (row * 2) / 3 : row / 3);
      const ix = Math.floor(x), iy = Math.floor(y);
      if (iy < h && mask[iy * w + ix] && keep(r, c)) out.push(x, y, up ? -Math.PI / 2 : Math.PI / 2);
    }
  }
  return out;
}

// Distance in mask pixels from every inside pixel to the nearest outside one.
export function insideDistance(mask, w, h) {
  const d = new Float32Array(w * h);
  for (let i = 0; i < d.length; i++) d[i] = mask[i] ? 1e9 : 0;
  const D = Math.SQRT2;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      if (!d[i]) continue;
      let v = d[i];
      v = Math.min(v, x > 0 ? d[i - 1] + 1 : 1);
      if (y > 0) {
        v = Math.min(v, d[i - w] + 1);
        if (x > 0) v = Math.min(v, d[i - w - 1] + D);
        if (x < w - 1) v = Math.min(v, d[i - w + 1] + D);
      } else v = Math.min(v, 1);
      d[i] = v;
    }
  }
  for (let y = h - 1; y >= 0; y--) {
    for (let x = w - 1; x >= 0; x--) {
      const i = y * w + x;
      if (!d[i]) continue;
      let v = d[i];
      v = Math.min(v, x < w - 1 ? d[i + 1] + 1 : 1);
      if (y < h - 1) {
        v = Math.min(v, d[i + w] + 1);
        if (x < w - 1) v = Math.min(v, d[i + w + 1] + D);
        if (x > 0) v = Math.min(v, d[i + w - 1] + D);
      } else v = Math.min(v, 1);
      d[i] = v;
    }
  }
  return d;
}

// Position along a Hilbert curve over a 1024 × 1024 grid. Sorting two point sets
// by it pairs up points in similar places, so shapes morph without tangling.
export function hilbert(x, y) {
  let d = 0;
  for (let s = 512; s > 0; s >>= 1) {
    const rx = (x & s) > 0 ? 1 : 0, ry = (y & s) > 0 ? 1 : 0;
    d += s * s * ((3 * rx) ^ ry);
    if (ry === 0) {
      if (rx === 1) {
        x = 1023 - x;
        y = 1023 - y;
      }
      const t = x;
      x = y;
      y = t;
    }
  }
  return d;
}

const C3 = Math.cos(TAU / 3), S3 = Math.sin(TAU / 3);

// Fills n triangles (centre x/y, rotation a, scale s) in one path per colour.
export function drawTriangles(ctx, n, x, y, a, s, colour, palette, size = TRIANGLE_SIZE) {
  const R = size / Math.sqrt(3);
  for (let c = 0; c < palette.length; c++) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      if (colour[i] !== c || s[i] < 0.04) continue;
      const r = R * s[i], ca = Math.cos(a[i]) * r, sa = Math.sin(a[i]) * r;
      const px = x[i], py = y[i];
      ctx.moveTo(px + ca, py + sa);
      ctx.lineTo(px + ca * C3 - sa * S3, py + ca * S3 + sa * C3);
      ctx.lineTo(px + ca * C3 + sa * S3, py - ca * S3 + sa * C3);
      ctx.closePath();
    }
    ctx.fillStyle = palette[c];
    ctx.fill();
  }
}
