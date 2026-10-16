// Reads a stroke-only SVG drawing into polylines, each with its line weight,
// in the drawing's own units with the viewBox origin at 0, 0.
//
//   const { width, height, lines } = readSketch(svgText);
//   // lines: [{ points: [x0, y0, x1, y1, ...], weight }]
//
// Paths (every command, arcs included), lines, polylines, polygons, rects,
// circles and ellipses are read, through nested groups and their transforms.
// Curves are flattened to within `tolerance` units.

const SKIP = new Set(['defs', 'clipPath', 'mask', 'symbol', 'marker', 'pattern', 'title', 'desc', 'metadata', 'style', 'text']);

export function readSketch(text, tolerance = 1) {
  const svg = new DOMParser().parseFromString(text, 'image/svg+xml').documentElement;
  if (svg.localName !== 'svg') throw new Error('Not an SVG drawing');
  const box = (svg.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number);
  const [bx, by, width, height] = box.length === 4 && box.every(Number.isFinite)
    ? box
    : [0, 0, parseFloat(svg.getAttribute('width')) || 1000, parseFloat(svg.getAttribute('height')) || 1000];
  const lines = [];

  const walk = (el, matrix, weight, stroke) => {
    for (const child of el.children) {
      const tag = child.localName;
      if (SKIP.has(tag) || style(child, 'display') === 'none' || style(child, 'visibility') === 'hidden') continue;
      const own = transform(child.getAttribute('transform'));
      const m = own ? multiply(matrix, own) : matrix;
      const w = parseFloat(style(child, 'stroke-width') ?? weight);
      const s = style(child, 'stroke') ?? stroke;
      if (tag === 'g' || tag === 'svg' || tag === 'a') {
        walk(child, m, w, s);
        continue;
      }
      if (s === 'none') continue;
      const scale = Math.sqrt(Math.abs(m[0] * m[3] - m[1] * m[2]));
      for (const pts of shape(child, tolerance)) {
        if (pts.length < 4) continue;
        for (let i = 0; i < pts.length; i += 2) {
          const x = pts[i], y = pts[i + 1];
          pts[i] = m[0] * x + m[2] * y + m[4];
          pts[i + 1] = m[1] * x + m[3] * y + m[5];
        }
        lines.push({ points: pts, weight: (Number.isFinite(w) ? w : 1) * scale });
      }
    }
  };
  walk(svg, [1, 0, 0, 1, -bx, -by], 1, 'black');
  return { width, height, lines };
}

// An attribute, or the same property set in the element's style attribute.
function style(el, name) {
  const css = el.getAttribute('style');
  if (css) {
    const match = new RegExp(`(?:^|;)\\s*${name}\\s*:\\s*([^;]+)`).exec(css);
    if (match) return match[1].trim();
  }
  return el.getAttribute(name) ?? undefined;
}

// Polylines, as flat [x, y, ...] arrays in the element's own units.
function shape(el, tol) {
  const n = (name) => parseFloat(el.getAttribute(name)) || 0;
  switch (el.localName) {
    case 'path':
      return path(el.getAttribute('d') || '', tol);
    case 'line':
      return [[n('x1'), n('y1'), n('x2'), n('y2')]];
    case 'polyline':
    case 'polygon': {
      const pts = (el.getAttribute('points') || '').trim().split(/[\s,]+/).map(Number).filter(Number.isFinite);
      if (el.localName === 'polygon' && pts.length >= 4) pts.push(pts[0], pts[1]);
      return [pts];
    }
    case 'rect': {
      const x = n('x'), y = n('y'), w = n('width'), h = n('height');
      return [[x, y, x + w, y, x + w, y + h, x, y + h, x, y]];
    }
    case 'circle':
      return [ellipse(n('cx'), n('cy'), n('r'), n('r'), tol)];
    case 'ellipse':
      return [ellipse(n('cx'), n('cy'), n('rx'), n('ry'), tol)];
    default:
      return [];
  }
}

function ellipse(cx, cy, rx, ry, tol) {
  const steps = Math.min(720, Math.max(12, Math.ceil((Math.PI * 2 * Math.max(rx, ry)) / tol)));
  const pts = [];
  for (let k = 0; k <= steps; k++) {
    const a = (k / steps) * Math.PI * 2;
    pts.push(cx + Math.cos(a) * rx, cy + Math.sin(a) * ry);
  }
  return pts;
}

const NUMBER = /[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/y;

// Every SVG path command, flattened into one polyline per subpath.
function path(d, tol) {
  const out = [];
  let i = 0, cmd = '', last = '';
  let x = 0, y = 0, sx = 0, sy = 0, cx = 0, cy = 0, line = null;
  const skip = () => {
    while (i < d.length && (d[i] === ' ' || d[i] === ',' || d[i] === '\n' || d[i] === '\t' || d[i] === '\r')) i++;
  };
  const num = () => {
    skip();
    NUMBER.lastIndex = i;
    const m = NUMBER.exec(d);
    if (!m) throw new Error(`Bad number in path at ${i}`);
    i = NUMBER.lastIndex;
    return parseFloat(m[0]);
  };
  const flag = () => {
    skip();
    return d[i++] === '1';
  };
  const to = (px, py) => {
    if (!line) {
      line = [x, y];
      out.push(line);
    }
    line.push(px, py);
  };
  const steps = (len) => Math.min(256, Math.max(1, Math.ceil(len / tol)));

  for (skip(); i < d.length; skip()) {
    if (/[a-zA-Z]/.test(d[i])) cmd = d[i++];
    else if (!cmd) throw new Error('Path without a command');
    const rel = cmd >= 'a', C = cmd.toUpperCase();
    const ox = rel ? x : 0, oy = rel ? y : 0;
    switch (C) {
      case 'M':
        x = sx = num() + ox;
        y = sy = num() + oy;
        line = [x, y];
        out.push(line);
        cmd = rel ? 'l' : 'L'; // more pairs after a move are lines
        break;
      case 'L':
        x = num() + ox;
        y = num() + oy;
        to(x, y);
        break;
      case 'H':
        x = num() + ox;
        to(x, y);
        break;
      case 'V':
        y = num() + oy;
        to(x, y);
        break;
      case 'C':
      case 'S': {
        let x1, y1;
        if (C === 'C') {
          x1 = num() + ox;
          y1 = num() + oy;
        } else {
          x1 = last === 'C' || last === 'S' ? 2 * x - cx : x;
          y1 = last === 'C' || last === 'S' ? 2 * y - cy : y;
        }
        const x2 = num() + ox, y2 = num() + oy, x3 = num() + ox, y3 = num() + oy;
        const n = steps(Math.hypot(x1 - x, y1 - y) + Math.hypot(x2 - x1, y2 - y1) + Math.hypot(x3 - x2, y3 - y2));
        for (let k = 1; k <= n; k++) {
          const t = k / n, u = 1 - t;
          to(u * u * u * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3, u * u * u * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3);
        }
        cx = x2;
        cy = y2;
        x = x3;
        y = y3;
        break;
      }
      case 'Q':
      case 'T': {
        let x1, y1;
        if (C === 'Q') {
          x1 = num() + ox;
          y1 = num() + oy;
        } else {
          x1 = last === 'Q' || last === 'T' ? 2 * x - cx : x;
          y1 = last === 'Q' || last === 'T' ? 2 * y - cy : y;
        }
        const x2 = num() + ox, y2 = num() + oy;
        const n = steps(Math.hypot(x1 - x, y1 - y) + Math.hypot(x2 - x1, y2 - y1));
        for (let k = 1; k <= n; k++) {
          const t = k / n, u = 1 - t;
          to(u * u * x + 2 * u * t * x1 + t * t * x2, u * u * y + 2 * u * t * y1 + t * t * y2);
        }
        cx = x1;
        cy = y1;
        x = x2;
        y = y2;
        break;
      }
      case 'A': {
        const rx = num(), ry = num(), rot = num(), large = flag(), sweep = flag();
        const x2 = num() + ox, y2 = num() + oy;
        for (const [px, py] of arc(x, y, rx, ry, (rot * Math.PI) / 180, large, sweep, x2, y2, tol)) to(px, py);
        x = x2;
        y = y2;
        break;
      }
      case 'Z':
        to(sx, sy);
        x = sx;
        y = sy;
        line = null;
        break;
      default:
        throw new Error(`Unknown path command ${cmd}`);
    }
    last = C;
  }
  return out;
}

// An elliptical arc as points, by the SVG spec's centre parameterisation.
function arc(x1, y1, rx, ry, phi, large, sweep, x2, y2, tol) {
  rx = Math.abs(rx);
  ry = Math.abs(ry);
  if (!rx || !ry || (x1 === x2 && y1 === y2)) return [[x2, y2]];
  const cos = Math.cos(phi), sin = Math.sin(phi);
  const dx = (x1 - x2) / 2, dy = (y1 - y2) / 2;
  const xp = cos * dx + sin * dy, yp = -sin * dx + cos * dy;
  const grow = (xp * xp) / (rx * rx) + (yp * yp) / (ry * ry);
  if (grow > 1) {
    rx *= Math.sqrt(grow);
    ry *= Math.sqrt(grow);
  }
  const num = rx * rx * ry * ry - rx * rx * yp * yp - ry * ry * xp * xp;
  const den = rx * rx * yp * yp + ry * ry * xp * xp;
  const k = (large === sweep ? -1 : 1) * Math.sqrt(Math.max(0, num / den));
  const cxp = (k * rx * yp) / ry, cyp = (-k * ry * xp) / rx;
  const cx = cos * cxp - sin * cyp + (x1 + x2) / 2, cy = sin * cxp + cos * cyp + (y1 + y2) / 2;
  const angle = (ux, uy, vx, vy) => Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy);
  const t1 = angle(1, 0, (xp - cxp) / rx, (yp - cyp) / ry);
  let dt = angle((xp - cxp) / rx, (yp - cyp) / ry, (-xp - cxp) / rx, (-yp - cyp) / ry);
  if (!sweep && dt > 0) dt -= Math.PI * 2;
  else if (sweep && dt < 0) dt += Math.PI * 2;
  const n = Math.min(512, Math.max(2, Math.ceil((Math.abs(dt) * Math.max(rx, ry)) / tol)));
  const pts = [];
  for (let s = 1; s <= n; s++) {
    const t = t1 + (dt * s) / n;
    pts.push([cx + rx * Math.cos(t) * cos - ry * Math.sin(t) * sin, cy + rx * Math.cos(t) * sin + ry * Math.sin(t) * cos]);
  }
  return pts;
}

// A transform attribute as a matrix [a, b, c, d, e, f], or null.
function transform(text) {
  if (!text) return null;
  let m = [1, 0, 0, 1, 0, 0];
  for (const [, name, args] of text.matchAll(/(\w+)\s*\(([^)]*)\)/g)) {
    const v = args.trim().split(/[\s,]+/).map(Number);
    const r = ((v[0] || 0) * Math.PI) / 180;
    const next = {
      matrix: v,
      translate: [1, 0, 0, 1, v[0] || 0, v[1] || 0],
      scale: [v[0] ?? 1, 0, 0, v[1] ?? v[0] ?? 1, 0, 0],
      rotate: [Math.cos(r), Math.sin(r), -Math.sin(r), Math.cos(r), 0, 0],
      skewX: [1, 0, Math.tan(r), 1, 0, 0],
      skewY: [1, Math.tan(r), 0, 1, 0, 0],
    }[name];
    if (!next) continue;
    if (name === 'rotate' && v.length === 3) {
      m = multiply(m, [1, 0, 0, 1, v[1], v[2]]);
      m = multiply(m, next);
      m = multiply(m, [1, 0, 0, 1, -v[1], -v[2]]);
    } else m = multiply(m, next);
  }
  return m;
}

// m after n: applies n first.
function multiply(m, n) {
  return [
    m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
    m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
    m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5],
  ];
}
