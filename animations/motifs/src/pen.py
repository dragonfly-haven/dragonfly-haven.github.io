"""Pen: draws the evolution motifs as hand-inked strokes and writes them as SVG.

Every motif is a generator script next to this file (NN-slug.py) that builds a
drawing with a Pen and saves it to ../NN-slug.svg:

    from pen import Pen, catmull, ellipse_pts
    pen = Pen(seed=12)
    pen.line([(100, 500), (300, 420), (500, 470)], w=1.8)      # an inked stroke
    pen.hatch(outline, angle=35, spacing=7, w=0.8)             # shading
    pen.save('../12-quastenflosser.svg', mirror=True)          # 10-20 face the text
    pen.report()

The drawing space is 1000 x 1000, y down, subject facing right (mirror=True
flips it for the page). Strokes are black, 0.6-3 wide; the site's engine lays
its dashes along them, more and darker where a stroke is heavier, so weight is
the only shading there is besides hatching.

Rules the set keeps (see README.md): stroke-only, hatching instead of fills,
hatch lines at least 5 units apart, lines that read as lines at 1x.
"""

import math
import random

Point = tuple


# ---------------------------------------------------------------- geometry

def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def length(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(pts, step):
    """Points along a polyline, `step` apart (the last point kept)."""
    if len(pts) < 2:
        return list(pts)
    out = [pts[0]]
    carry = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = dist(a, b)
        if d == 0:
            continue
        t = step - carry
        while t <= d:
            out.append(lerp(a, b, t / d))
            t += step
        carry = d - (t - step)
    if dist(out[-1], pts[-1]) > step * 0.25:
        out.append(pts[-1])
    else:
        out[-1] = pts[-1]
    return out


def catmull(ctrl, closed=False, step=3.0, tension=0.5):
    """A smooth curve through control points (Catmull-Rom), as a polyline."""
    p = list(ctrl)
    if len(p) < 2:
        return p
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [(2 * p[0][0] - p[1][0], 2 * p[0][1] - p[1][1])] + p + [(2 * p[-1][0] - p[-2][0], 2 * p[-1][1] - p[-2][1])]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        n = max(2, int(dist(p1, p2) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                tension * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in range(2)))
    out.append(p[-2])
    return out


def bezier(p0, p1, p2, p3, step=3.0):
    """A cubic Bezier as a polyline."""
    n = max(2, int((dist(p0, p1) + dist(p1, p2) + dist(p2, p3)) / step))
    out = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def ellipse_pts(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=2 * math.pi, step=3.0):
    """An ellipse (or an arc of one, angles in radians) as a polyline."""
    n = max(8, int(abs(a1 - a0) * max(rx, ry) / step))
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def offset(pts, d):
    """A polyline shifted sideways by d (positive to the left of travel, y down)."""
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((pts[i][0] + dy / L * d, pts[i][1] - dx / L * d))
    return out


def transform(pts, dx=0.0, dy=0.0, scale=1.0, rot=0.0, origin=(0, 0)):
    """Points scaled and turned about `origin`, then moved."""
    c, s = math.cos(rot), math.sin(rot)
    ox, oy = origin
    return [(ox + ((x - ox) * c - (y - oy) * s) * scale + dx, oy + ((x - ox) * s + (y - oy) * c) * scale + dy) for x, y in pts]


def inside(pt, poly):
    """Even-odd point-in-polygon."""
    x, y = pt
    hit = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            if x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                hit = not hit
    return hit


def clip_segments(pts, keep):
    """Splits a polyline into the runs where keep(point) holds (resampled finely)."""
    fine = resample(pts, 1.5)
    runs, cur = [], []
    for p in fine:
        if keep(p):
            cur.append(p)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def scanlines(poly, angle_deg, spacing, phase=0.0):
    """Parallel chords of a polygon (even-odd), `spacing` apart, at an angle in degrees."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    # rotate the polygon so the lines run along x
    rp = [(x * c + y * s, -x * s + y * c) for x, y in poly]
    ys = [p[1] for p in rp]
    lo, hi = min(ys), max(ys)
    out = []
    y = lo + (phase % 1.0) * spacing + spacing * 0.5
    n = len(rp)
    while y < hi:
        xs = []
        for i in range(n):
            x0, y0 = rp[i]
            x1, y1 = rp[(i + 1) % n]
            if (y0 > y) != (y1 > y):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            p0 = (xs[k] * c - y * s, xs[k] * s + y * c)
            p1 = (xs[k + 1] * c - y * s, xs[k + 1] * s + y * c)
            out.append((p0, p1))
        y += spacing
    return out


# ---------------------------------------------------------------- the pen

class Pen:
    """Collects strokes as (points, width) and writes them as an SVG.

    Strokes go through a "hand": a gentle wobble, a weight that swells and
    thins, and the odd lift of the pen, so lines look inked rather than
    plotted. Occluders hide later strokes behind earlier shapes: draw front
    to back and add each front shape's outline with pen.occlude(poly).
    """

    def __init__(self, seed=1):
        self.rng = random.Random(seed)
        self.strokes = []
        self.occluders = []
        self.hatch_spacings = []

    # -- randomness
    def r(self, lo=0.0, hi=1.0):
        return lo + (hi - lo) * self.rng.random()

    def g(self, sigma=1.0):
        return self.rng.gauss(0, sigma)

    # -- occlusion
    def occlude(self, poly):
        self.occluders.append(list(poly))

    def visible(self, pts):
        if not self.occluders:
            return [list(pts)]
        return clip_segments(pts, lambda p: not any(inside(p, o) for o in self.occluders))

    # -- strokes
    def raw(self, pts, w=1.0):
        """A stroke exactly as given (no hand, no occlusion)."""
        pts = [(float(x), float(y)) for x, y in pts]
        if len(pts) >= 2 and length(pts) > 0.3:
            self.strokes.append((pts, float(w)))

    def line(self, pts, w=1.2, hand=1.0, lift=0.22, piece=(22, 70), taper=0.0, occlude=True):
        """An inked stroke along a polyline.

        w      weight (0.6 fine hatching ... 3 heavy contour)
        hand   wobble in units (0 for ruled lines)
        lift   chance of a tiny gap where the pen is lifted between pieces
        piece  range of piece lengths the stroke is split into, each with its own weight
        taper  0..1, how much the stroke thins toward both ends
        """
        runs = self.visible(pts) if occlude else [list(pts)]
        for run in runs:
            self._ink(run, w, hand, lift, piece, taper)

    def _ink(self, pts, w, hand, lift, piece, taper):
        total = length(pts)
        if total < 0.5:
            return
        step = max(0.4, min(3.0, total / 16))
        fine = resample(pts, step)
        if hand > 0 and len(fine) > 2:
            # low-frequency sideways wobble
            ph1, ph2 = self.r(0, 6.3), self.r(0, 6.3)
            f1, f2 = self.r(0.008, 0.02), self.r(0.03, 0.06)
            moved = []
            s = 0.0
            for i, p in enumerate(fine):
                if i:
                    s += dist(fine[i - 1], p)
                a = fine[max(0, i - 1)]
                b = fine[min(len(fine) - 1, i + 1)]
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy) or 1
                off = hand * (0.7 * math.sin(s * f1 * 2 * math.pi + ph1) + 0.3 * math.sin(s * f2 * 2 * math.pi + ph2))
                # ends stay put so joins meet
                ease = min(1.0, s / 12.0, (total - s) / 12.0)
                moved.append((p[0] + dy / L * off * ease, p[1] - dx / L * off * ease))
            fine = moved
        # split into pieces of varying weight, with the odd small lift
        i = 0
        s_at = [0.0]
        for k in range(1, len(fine)):
            s_at.append(s_at[-1] + dist(fine[k - 1], fine[k]))
        while i < len(fine) - 1:
            want = self.r(*piece)
            j = i + 1
            while j < len(fine) - 1 and s_at[j] - s_at[i] < want:
                j += 1
            seg = fine[i:j + 1]
            mid = (s_at[i] + s_at[j]) / 2
            tap = 1.0
            if taper > 0 and total > 0:
                u = mid / total
                tap = 1 - taper * (1 - math.sin(math.pi * u)) ** 1.5
            ww = max(0.6, min(3.2, w * tap * self.r(0.85, 1.15)))
            if len(seg) >= 2:
                self.strokes.append((seg, ww))
            if j < len(fine) - 1 and self.rng.random() < lift and w < 2.4:
                # lift the pen for a gap of about 1.5-3 units
                gap = self.r(1.5, 3.0)
                k = j
                while k < len(fine) - 1 and s_at[k] - s_at[j] < gap:
                    k += 1
                i = k
            else:
                i = j

    def curve(self, ctrl, w=1.2, closed=False, **kw):
        """An inked stroke through control points."""
        self.line(catmull(ctrl, closed=closed), w=w, **kw)

    def ellipse(self, cx, cy, rx, ry, rot=0.0, w=1.2, a0=None, a1=None, **kw):
        """An inked ellipse; a hand-drawn one starts at a random angle and overlaps a little."""
        if a0 is None:
            a0 = self.r(0, 2 * math.pi)
            a1 = a0 + 2 * math.pi + self.r(0.05, 0.25)
        self.line(ellipse_pts(cx, cy, rx, ry, rot, a0, a1), w=w, **kw)

    def hatch(self, poly, angle=35, spacing=7, w=0.8, jitter=0.15, shrink=(0.0, 0.12), skip=0.0, hand=0.4, curve=0.0, keep=None):
        """Parallel hatching inside a polygon.

        spacing  distance between lines (keep >= 5)
        jitter   share of spacing each line drifts by
        shrink   range of the share of each line's length left off its ends, as a hand stops short
        skip     chance a line is left out
        curve    a slight bow to each line, in units
        keep     optional predicate on a line's midpoint; lines failing it are dropped
        """
        self.hatch_spacings.append(spacing)
        for p0, p1 in scanlines(poly, angle, spacing, self.r()):
            if self.rng.random() < skip:
                continue
            L = dist(p0, p1)
            if L < 2:
                continue
            j = self.g(jitter * spacing)
            a = math.radians(angle)
            nx, ny = -math.sin(a), math.cos(a)
            p0 = (p0[0] + nx * j, p0[1] + ny * j)
            p1 = (p1[0] + nx * j, p1[1] + ny * j)
            t0 = self.r(*shrink)
            t1 = 1 - self.r(*shrink)
            if t1 <= t0:
                continue
            q0, q1 = lerp(p0, p1, t0), lerp(p0, p1, t1)
            mid = lerp(q0, q1, 0.5)
            if keep and not keep(mid):
                continue
            if curve:
                b = self.g(curve)
                m = (mid[0] + nx * b, mid[1] + ny * b)
                pts = catmull([q0, m, q1], step=2.5)
            else:
                pts = [q0, q1]
            self.line(pts, w=w * self.r(0.85, 1.15), hand=hand, lift=0.05, piece=(40, 120))

    def flow_hatch(self, rails_a, rails_b, n, w=0.8, t0=0.05, t1=0.95, hand=0.4, keep=None):
        """Hatching that follows form: n strokes across from rail a to rail b
        (two polylines running the same way), between parameters t0..t1 along them."""
        A, B = resample(rails_a, 1.0), resample(rails_b, 1.0)
        for k in range(n):
            t = t0 + (t1 - t0) * (k + 0.5 + self.g(0.15)) / n
            pa = A[min(len(A) - 1, int(t * (len(A) - 1)))]
            pb = B[min(len(B) - 1, int(t * (len(B) - 1)))]
            s0, s1 = self.r(0.0, 0.1), 1 - self.r(0.0, 0.1)
            q0, q1 = lerp(pa, pb, s0), lerp(pa, pb, s1)
            if keep and not keep(lerp(q0, q1, 0.5)):
                continue
            self.line([q0, q1], w=w * self.r(0.85, 1.15), hand=hand, lift=0.05, piece=(40, 120))

    def dot(self, x, y, r=1.6, w=1.4):
        """A small inked dot (a tiny closed loop, as pen dots are in this set)."""
        self.line(ellipse_pts(x, y, r, r * self.r(0.8, 1.0), self.r(0, 3.1), step=0.5), w=w, hand=0, lift=0)

    def blot(self, cx, cy, rx, ry=None, rot=0.0, w=2.0):
        """A solid black spot (an eye, a pupil): a tight spiral of heavy line."""
        ry = rx if ry is None else ry
        pts = []
        turns = max(1.0, max(rx, ry) / (w * 0.75))
        n = int(turns * 40)
        c, s = math.cos(rot), math.sin(rot)
        for k in range(n + 1):
            u = k / n
            a = u * turns * 2 * math.pi
            fx, fy = rx * u * math.cos(a), ry * u * math.sin(a)
            pts.append((cx + fx * c - fy * s, cy + fx * s + fy * c))
        pts += ellipse_pts(cx, cy, rx, ry, rot, turns * 2 * math.pi, turns * 2 * math.pi + 2 * math.pi, step=0.8)
        self.line(pts, w=w, hand=0, lift=0, piece=(400, 800))

    # -- output
    def save(self, path, mirror=False):
        """Writes the SVG; mirror=True flips it to face left (slots 10-20)."""
        out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">']
        if mirror:
            out.append('<g transform="matrix(-1 0 0 1 1000 0)">')
        for pts, w in self.strokes:
            d = 'M' + ' '.join(f'{_n(x)} {_n(y)}' if i else f'{_n(x)} {_n(y)}L' for i, (x, y) in enumerate(pts))
            d = d.replace('L ', 'L')
            out.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w, 2)}" stroke-linecap="round"/>')
        if mirror:
            out.append('</g>')
        out.append('</svg>')
        with open(path, 'w') as f:
            f.write('\n'.join(out) + '\n')

    def report(self):
        """Prints what the engine will make of the drawing."""
        n = len(self.strokes)
        total = sum(length(p) for p, _ in self.strokes)
        # dashes in a 900 px box on a 2x screen, the densest common case (engine CAP is 52000)
        unit = 900 * 0.94 / 1000  # px per drawing unit
        step2 = 1.7 * 1.15 / unit
        dashes = sum(length(p) / (step2 * max(0.85, min(1.5, 1.35 - 0.24 * (max(0.5, min(4, w)) - 1)))) for p, w in self.strokes)
        ws = [w for _, w in self.strokes] or [0]
        xs = [x for p, _ in self.strokes for x, _ in p] or [0]
        ys = [y for p, _ in self.strokes for _, y in p] or [0]
        tight = [s for s in self.hatch_spacings if s < 5]
        print(f'strokes {n}  ink length {total:.0f}  est. dashes (900px box, 2x) {dashes:.0f}  '
              f'weights {min(ws):.2f}-{max(ws):.2f}  bbox x {min(xs):.0f}-{max(xs):.0f} y {min(ys):.0f}-{max(ys):.0f}'
              + (f'  WARNING hatch spacing under 5: {sorted(set(tight))}' if tight else ''))


def _n(v, places=1):
    s = f'{v:.{places}f}'.rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'
