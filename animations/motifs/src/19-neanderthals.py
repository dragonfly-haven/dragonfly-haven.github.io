#!/usr/bin/env python3
"""19 Neanderthals: two Neanderthals at a small hearth.

A standing man with a hafted wooden spear and a squatting woman knapping a
flint core face each other across a small fire. Both are built from a
skeleton of joints (hip, knee, ankle, shoulder, elbow, wrist) with limb
contours swelling for the muscles, and with Neanderthal proportions: big
long-low heads (heavy brow ridge, large projecting nose and mid-face, no
chin, occipital bun), short necks, deep barrel chests, short forearms and
shins, thick limbs, broad feet. Clothing is draped hide only.

Every body part is a closed outline with a depth (z). An outline is hidden
where a part in front of it covers it, or where it runs inside a part it is
joined to (so a thigh flows into a hip without a seam). Outlines are heavy
where they bound the figure against the empty ground and lighter where they
cross another part. Shading is cross-contour hatching laid across each limb
from its shadow side (the side away from the fire), and drape lines along
the hides.

Run from this folder: python3 19-neanderthals.py   (writes ../19-neanderthals.svg)
"""

import math

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside

pen = Pen(seed=1907)


# ------------------------------------------------------------------ helpers

def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def prof(st, t):
    """A width profile: stations (t, w), eased between."""
    if t <= st[0][0]:
        return st[0][1]
    for (t0, w0), (t1, w1) in zip(st, st[1:]):
        if t <= t1:
            return w0 + (w1 - w0) * smooth((t - t0) / (t1 - t0) if t1 > t0 else 0)
    return st[-1][1]


def plen(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def tparams(pts):
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + dist(pts[i - 1], pts[i]))
    T = s[-1] or 1
    return [v / T for v in s]


def normals(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((dy / L, -dx / L))
    return out


def sub(pts, t0, t1):
    """The part of a polyline between fractions t0..t1 of its length."""
    pts = resample(pts, 1.5)
    ts = tparams(pts)
    return [p for p, t in zip(pts, ts) if t0 <= t <= t1]


def at(pts, t):
    ts = tparams(pts)
    for i in range(1, len(pts)):
        if ts[i] >= t:
            u = (t - ts[i - 1]) / ((ts[i] - ts[i - 1]) or 1)
            return lerp(pts[i - 1], pts[i], u)
    return pts[-1]


def closed(ctrl, step=2.0):
    return catmull(ctrl, closed=True, step=step)[:-1]


def blob(cx, cy, rx, ry, rot=0.0):
    return ellipse_pts(cx, cy, rx, ry, rot, step=2.0)[:-1]


def rag(ctrl, amp, step=10.0):
    """A curve through control points, roughened a little (hide edges)."""
    pts = resample(catmull(ctrl, step=2.0), step)
    nrm = normals(pts)
    out = []
    for i, (p, n) in enumerate(zip(pts, nrm)):
        e = 0 if i in (0, len(pts) - 1) else pen.g(amp)
        out.append((p[0] + n[0] * e, p[1] + n[1] * e))
    return catmull(out, step=2.0)


def flow(e1, e2, fr, n=80):
    """A curve between two edges running the same way, at fraction fr from e1 to e2."""
    A = resample(e1, max(0.5, plen(e1) / n))
    B = resample(e2, max(0.5, plen(e2) / n))
    m = min(len(A), len(B))
    A = [A[int(i * (len(A) - 1) / (m - 1))] for i in range(m)]
    B = [B[int(i * (len(B) - 1) / (m - 1))] for i in range(m)]
    return [lerp(a, b, fr) for a, b in zip(A, B)]


def broken(pts, piece=(18, 45), gap=(3, 8), keep=1.0):
    """A line broken into pieces with small gaps (strands, drape lines)."""
    pts = resample(pts, 1.5)
    s = [0.0]
    for k in range(1, len(pts)):
        s.append(s[-1] + dist(pts[k - 1], pts[k]))
    out = []
    i = int(pen.r(0, 4))
    while i < len(pts) - 1:
        want = pen.r(*piece)
        j = i + 1
        while j < len(pts) - 1 and s[j] - s[i] < want:
            j += 1
        if pen.rng.random() < keep:
            out.append(pts[i:j + 1])
        g = pen.r(*gap)
        k = j
        while k < len(pts) - 1 and s[k] - s[j] < g:
            k += 1
        i = k
    return [o for o in out if len(o) > 1]


def blot_pts(cx, cy, r, w=1.6):
    """A solid spot as a tight spiral (like pen.blot), as one stroke."""
    turns = max(1.0, r / (w * 0.75))
    n = int(turns * 40)
    pts = []
    for k in range(n + 1):
        u = k / n
        a = u * turns * 2 * math.pi
        pts.append((cx + r * u * math.cos(a), cy + r * u * math.sin(a)))
    pts += ellipse_pts(cx, cy, r, r, 0, turns * 2 * math.pi, turns * 2 * math.pi + 2 * math.pi, step=0.8)
    return pts


# ------------------------------------------------------------------ parts

class Part:
    """A closed outline at a depth z (smaller is nearer), with strokes inside it."""

    def __init__(self, name, poly, z, w=2.2, outline=None, joins=()):
        self.name = name
        self.poly = list(poly)
        self.z = z
        self.w = w                      # outline weight against the empty ground
        self.inner_w = None             # outline weight where it crosses another part
        self.outline = outline if outline is not None else [self.poly + [self.poly[0]]]
        self.joins = set(joins)         # parts it flows into (no seam inside them)
        self.strokes = []               # (pts, w, clip, kw)

    def add(self, pts, w=0.8, clip=True, **kw):
        if len(pts) >= 2:
            self.strokes.append((list(pts), w, clip, kw))

    def apply(self, f):
        self.poly = [f(p) for p in self.poly]
        self.outline = [[f(p) for p in ol] for ol in self.outline]
        self.strokes = [([f(p) for p in pts], w, c, kw) for pts, w, c, kw in self.strokes]

    def finish(self):
        xs = [p[0] for p in self.poly]
        ys = [p[1] for p in self.poly]
        self.bb = (min(xs), min(ys), max(xs), max(ys))
        self.test = resample(self.poly + [self.poly[0]], 2.5)

    def has(self, p):
        x0, y0, x1, y1 = self.bb
        if p[0] < x0 or p[0] > x1 or p[1] < y0 or p[1] > y1:
            return False
        return inside(p, self.test)


class Figure:
    def __init__(self, tag=''):
        self.tag = tag
        self.parts = []

    def part(self, name, poly, z, **kw):
        p = Part(self.tag + name, poly, z, **kw)
        p.joins = {self.tag + j for j in p.joins}
        self.parts.append(p)
        return p

    def apply(self, f):
        for p in self.parts:
            p.apply(f)


class Limb:
    """A limb segment round an axis through joints, with widths on side a
    (left of travel) and side b (right of travel), as profiles over 0..1."""

    def __init__(self, joints, wa, wb, cap0=0.6, cap1=0.6):
        self.axis = resample(catmull(joints, step=1.5), 2.0)
        self.t = tparams(self.axis)
        self.n = normals(self.axis)
        self.L = plen(self.axis)
        self.wa, self.wb = wa, wb
        self.A = [(p[0] + n[0] * prof(wa, t), p[1] + n[1] * prof(wa, t)) for p, n, t in zip(self.axis, self.n, self.t)]
        self.B = [(p[0] - n[0] * prof(wb, t), p[1] - n[1] * prof(wb, t)) for p, n, t in zip(self.axis, self.n, self.t)]
        self.poly = self.A + self._cap(-1, cap1) + self.B[::-1] + self._cap(0, cap0)

    def _cap(self, i, k):
        p, n = self.axis[i], self.n[i]
        d = (-n[1], n[0]) if i else (n[1], -n[0])
        wa, wb = prof(self.wa, self.t[i]), prof(self.wb, self.t[i])
        r = (wa + wb) / 2 * k
        out = []
        for j in range(1, 12):
            th = math.pi * j / 12
            cw = math.cos(th) if i else -math.cos(th)
            w = wa if cw > 0 else wb
            out.append((p[0] + n[0] * w * cw + d[0] * r * math.sin(th), p[1] + n[1] * w * cw + d[1] * r * math.sin(th)))
        return out

    def idx(self, t):
        return min(len(self.axis) - 1, max(0, int(round(t * (len(self.axis) - 1)))))

    def pt(self, t, s):
        """Point at t along, s across (-1 = side b edge, +1 = side a edge)."""
        i = self.idx(t)
        p, n = self.axis[i], self.n[i]
        w = prof(self.wa, t) if s >= 0 else prof(self.wb, t)
        return (p[0] + n[0] * w * s, p[1] + n[1] * w * s)

    def along(self, t):
        n = self.n[self.idx(t)]
        return (-n[1], n[0])

    def xhatch(self, part, t0, t1, spacing=6.0, side='b', frac=(0.35, 0.5), bow=2.5, w=0.7, fade=0.25):
        """Cross-contour shading: strokes across the limb from one edge, bowed along it."""
        n = max(1, int(self.L * (t1 - t0) / spacing))
        sg = -1 if side == 'b' else 1
        for k in range(n):
            t = t0 + (t1 - t0) * (k + 0.5 + pen.g(0.1)) / n
            f = pen.r(*frac)
            if fade:
                e = min(1.0, (t - t0) / ((t1 - t0) * fade + 1e-9), (t1 - t) / ((t1 - t0) * fade + 1e-9))
                f *= 0.45 + 0.55 * max(0.0, e)
            p0 = self.pt(t, sg * 1.02)
            p1 = self.pt(t, sg * (1 - 2 * f))
            d = self.along(t)
            m = lerp(p0, p1, 0.5)
            m = (m[0] + d[0] * bow, m[1] + d[1] * bow)
            part.add(catmull([p0, m, p1], step=2.0), w=w * pen.r(0.9, 1.1))

    def shade(self, part, t0, t1, side='b', n=3, spacing=5.5, w=0.7, taper=0.16, piece=(22, 60)):
        """Modelling along the limb: n lines inside one edge, following it,
        each shorter than the last, so the shadow thins toward the lit side."""
        sg = -1 if side == 'b' else 1
        prf = self.wb if side == 'b' else self.wa
        for k in range(n):
            inset = (k + 0.7) * spacing + pen.g(0.4)
            a = t0 + (t1 - t0) * taper * k * pen.r(0.8, 1.2)
            b = t1 - (t1 - t0) * taper * k * pen.r(0.5, 0.9)
            if b - a < 0.04:
                continue
            pts = []
            for i in range(41):
                t = a + (b - a) * i / 40
                j = self.idx(t)
                p, nn = self.axis[j], self.n[j]
                d = max(1.0, prof(prf, t) - inset)
                pts.append((p[0] + nn[0] * d * sg, p[1] + nn[1] * d * sg))
            for seg in broken(pts, piece, (3, 7), 0.95):
                part.add(seg, w=w * pen.r(0.9, 1.1))


def fur(part, e1, e2, frs, piece=(6, 14), gap=(3, 7), keep=0.85, w=0.72, t0=0.0, t1=1.0):
    """Hide texture: rows of short hairs between two edges of a hide, each
    hair nudged and turned a little so the rows do not read as dashed lines."""
    for fr in frs:
        c = sub(flow(e1, e2, fr), t0 + pen.r(0, 0.04), t1 - pen.r(0, 0.04))
        for seg in broken(c, piece, gap, keep):
            if len(seg) < 2:
                continue
            a, b = seg[0], seg[-1]
            m = lerp(a, b, 0.5)
            ang = pen.g(0.16)
            off = pen.g(1.2)
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            c_, s_ = math.cos(ang), math.sin(ang)
            def rot(p):
                x, y = p[0] - m[0], p[1] - m[1]
                return (m[0] + x * c_ - y * s_ + nx * off, m[1] + x * s_ + y * c_ + ny * off)
            part.add([rot(p) for p in seg], w=w * pen.r(0.85, 1.15), hand=0.2, lift=0)


def drape(part, e1, e2, frs, w=0.72, piece=(24, 70), gap=(4, 10), keep=0.92, t0=0.0, t1=1.0):
    """Lines along a hide, between two of its edges (both running the same way)."""
    for fr in frs:
        c = flow(e1, e2, fr)
        c = sub(c, t0 + pen.r(0, 0.05), t1 - pen.r(0, 0.05))
        for seg in broken(c, piece, gap, keep):
            part.add(seg, w=w * pen.r(0.9, 1.1))


def fur_edge(part, edge, every=6.0, ln=(4, 8), w=0.75, inward=1, keep=0.8):
    """Short hairs along a hide's edge."""
    pts = resample(edge, every)
    nrm = normals(pts)
    for p, n in zip(pts[1:-1], nrm[1:-1]):
        if pen.rng.random() > keep:
            continue
        L = pen.r(*ln)
        a = pen.g(0.25)
        dx, dy = n[0] * math.cos(a) - n[1] * math.sin(a), n[0] * math.sin(a) + n[1] * math.cos(a)
        part.add([(p[0] - dx * 1.5 * inward, p[1] - dy * 1.5 * inward), (p[0] + dx * L * inward, p[1] + dy * L * inward)],
                 w=w, clip=False, hand=0.2)


# ------------------------------------------------------------------ the Neanderthal head

# Profile facing right, in head heights, ear canal at the origin, y down.
# Long low vault with an occipital bun, a low sloping forehead, a heavy
# brow ridge (torus) jutting over the eyes, a big projecting nose and
# mid-face, a long upper lip, no chin.
HEAD = [
    (-0.30, 0.16), (-0.38, 0.06), (-0.455, -0.02), (-0.525, -0.10), (-0.55, -0.19),
    (-0.515, -0.30), (-0.43, -0.395), (-0.28, -0.47), (-0.08, -0.505), (0.12, -0.497),
    (0.28, -0.458), (0.40, -0.392), (0.462, -0.330), (0.500, -0.284), (0.528, -0.266),
    (0.566, -0.246), (0.600, -0.208), (0.604, -0.168), (0.584, -0.140), (0.556, -0.126),
    (0.548, -0.108), (0.580, -0.064), (0.630, -0.004), (0.676, 0.054), (0.704, 0.094),
    (0.706, 0.120), (0.688, 0.136), (0.645, 0.145), (0.612, 0.152), (0.617, 0.186),
    (0.622, 0.214), (0.607, 0.233), (0.612, 0.252), (0.598, 0.275), (0.566, 0.305),
    (0.530, 0.348), (0.494, 0.392), (0.452, 0.422), (0.390, 0.436), (0.300, 0.434),
    (0.225, 0.424), (0.10, 0.38), (-0.10, 0.28), (-0.22, 0.22),
]
I_THROAT = 40

HAIR_M = (
    [(0.40, -0.392), (0.34, -0.452), (0.22, -0.512), (0.02, -0.548), (-0.18, -0.540), (-0.37, -0.484),
     (-0.52, -0.38), (-0.600, -0.23), (-0.612, -0.08), (-0.57, 0.06), (-0.50, 0.17), (-0.45, 0.27), (-0.40, 0.34)],
    [(0.40, -0.392), (0.30, -0.345), (0.19, -0.275), (0.09, -0.195), (0.0, -0.160), (-0.08, -0.110),
     (-0.14, 0.0), (-0.20, 0.12), (-0.28, 0.25), (-0.40, 0.34)])
HAIR_F = (
    [(0.40, -0.392), (0.33, -0.462), (0.20, -0.522), (0.0, -0.556), (-0.20, -0.546), (-0.39, -0.487),
     (-0.535, -0.38), (-0.618, -0.22), (-0.630, -0.06), (-0.592, 0.10), (-0.54, 0.26), (-0.49, 0.42),
     (-0.44, 0.57), (-0.40, 0.70)],
    [(0.40, -0.392), (0.30, -0.345), (0.18, -0.275), (0.08, -0.205), (-0.02, -0.165), (-0.10, -0.09),
     (-0.16, 0.04), (-0.21, 0.19), (-0.26, 0.34), (-0.30, 0.49), (-0.35, 0.61), (-0.40, 0.70)])


class Head:
    def __init__(self, F, ear, h, tilt, z, female=False):
        self.ear, self.h, self.tilt, self.female = ear, h, tilt, female
        ctrl = self.P(HEAD)
        poly = closed(ctrl, step=1.5)
        self.part = F.part('head', poly, z, w=2.2, outline=[catmull(ctrl[0:I_THROAT + 1], step=1.5)], joins=('neck',))
        outer, line = HAIR_F if female else HAIR_M
        self.outer = rag(self.P(outer), 0.8, 8)
        self.line = catmull(self.P(line), step=2.0)
        # the hair's edge is drawn as overlapping locks, not as one line
        self.hair = F.part('hair', self.outer + self.line[::-1][1:-1], z - 0.3, w=2.0, outline=[])
        self.details()

    def P(self, pts):
        c, s = math.cos(self.tilt), math.sin(self.tilt)
        return [(self.ear[0] + (x * c - y * s) * self.h, self.ear[1] + (x * s + y * c) * self.h) for x, y in pts]

    def C(self, pts, step=1.0):
        return catmull(self.P(pts), step=step)

    def details(self):
        hd, hair, h = self.part, self.hair, self.h
        # the hair's edge: locks overlapping, ends flicked out a little
        for seg in broken(self.outer, piece=(10, 26), gap=(-3, 0.5)):
            if len(seg) > 2:
                a, b = seg[-2], seg[-1]
                d = (b[0] - a[0], b[1] - a[1])
                L = math.hypot(*d) or 1
                n = (d[1] / L, -d[0] / L)
                flick = pen.r(0.5, 2.5)
                seg = seg[:-1] + [(b[0] + n[0] * flick, b[1] + n[1] * flick)]
            hair.add(seg, w=pen.r(1.55, 1.95), clip=False, hand=0.2, lift=0, piece=(60, 90))
        # tousled strands inside, following the hair back over the vault
        n = 8 if self.female else 7
        for k in range(n):
            fr = (k + 0.35 + pen.g(0.07)) / n
            c = flow(self.outer, self.line, fr)
            for seg in broken(c, piece=(8, 22), gap=(2.5, 6), keep=0.9):
                m = len(seg) // 2
                bend = pen.g(1.2)
                if len(seg) > 4:
                    a, b = seg[0], seg[-1]
                    L = dist(a, b) or 1
                    nn = ((b[1] - a[1]) / L, -(b[0] - a[0]) / L)
                    seg = catmull([a, (seg[m][0] + nn[0] * bend, seg[m][1] + nn[1] * bend), b], step=1.5)
                hair.add(seg, w=pen.r(0.75, 0.95), hand=0.3, lift=0, piece=(30, 80))
        # loose ends at the nape
        for k in range(4 if not self.female else 6):
            a = self.P([(-0.42 + 0.03 * k, 0.24 + 0.03 * k)])[0] if not self.female else self.P([(-0.46 + 0.02 * k, 0.55 + 0.04 * k)])[0]
            b = (a[0] + pen.r(-3, 3), a[1] + pen.r(12, 20))
            hair.add(catmull([a, lerp(a, b, 0.5), b], step=1.5), w=pen.r(0.9, 1.2), clip=False, hand=0.4)

        # brow ridge: its lower margin over the eye, the step above it
        hd.add(self.C([(0.37, -0.160), (0.45, -0.180), (0.53, -0.180), (0.588, -0.165)]), w=1.8, hand=0.2)
        hd.add(self.C([(0.41, -0.275), (0.47, -0.282), (0.523, -0.268)]), w=0.9, hand=0.2)
        for k in range(4):
            u = 0.44 + k * 0.035
            hd.add(self.C([(u, -0.262), (u + 0.02, -0.250)]), w=0.7, hand=0.1)
        # the orbit, deep in the brow's shadow
        for k in range(6):
            u = 0.405 + k * 0.03
            hd.add(self.C([(u, -0.163), (u - 0.008, -0.132), (u - 0.020, -0.108)]), w=0.75, hand=0.1)
        # the eye
        hd.add(self.C([(0.448, -0.106), (0.478, -0.114), (0.508, -0.102)]), w=1.25, hand=0.1)
        hd.add(self.C([(0.455, -0.079), (0.482, -0.075), (0.507, -0.093)]), w=0.8, hand=0.1)
        e = self.P([(0.485, -0.095)])[0]
        hd.add(blot_pts(e[0], e[1], 0.018 * h, w=1.5), w=1.5, clip=False, hand=0, lift=0, piece=(400, 800))
        # big nose: the wing, the nostril, the fold down to the mouth
        hd.add(self.C([(0.640, 0.074), (0.618, 0.090), (0.612, 0.115), (0.626, 0.134)]), w=1.2, hand=0.1)
        hd.add(self.C([(0.668, 0.129), (0.650, 0.123), (0.634, 0.129)]), w=1.0, hand=0.1)
        hd.add(self.C([(0.590, 0.058), (0.570, 0.115), (0.572, 0.175), (0.588, 0.222)]), w=0.85, hand=0.2)
        # mouth
        hd.add(self.C([(0.607, 0.233), (0.58, 0.238), (0.546, 0.247)]), w=1.2, hand=0.1)
        # cheekbone, jaw from below the ear to the chin
        hd.add(self.C([(0.45, -0.04), (0.41, 0.025), (0.35, 0.065)]), w=0.8, hand=0.2)
        hd.add(self.C([(0.05, 0.13), (0.085, 0.27), (0.15, 0.35), (0.26, 0.395), (0.36, 0.41)]), w=0.95, hand=0.2)
        # shading: under the cheekbone toward the jaw, the temple in front of the ear
        for k in range(4):
            u = 0.12 + k * 0.045
            hd.add(self.C([(u + 0.04, 0.13 + k * 0.01), (u + 0.02, 0.20 + k * 0.01), (u, 0.27)]), w=0.68, hand=0.2)
        # the ear
        ear = self.P([(0.0, -0.01)])[0]
        rot = self.tilt - 0.2
        hd.add(ellipse_pts(ear[0], ear[1], 0.064 * h, 0.118 * h, rot, -2.2, 2.4, step=1.0), w=1.3, hand=0.1)
        hd.add(ellipse_pts(ear[0] - 0.006 * h, ear[1] + 0.005 * h, 0.03 * h, 0.07 * h, rot, -1.5, 1.7, step=1.0), w=0.9, hand=0.1)
        if not self.female:
            # a short beard along the jaw that leaves the receding chin clear
            base = self.C([(0.10, 0.22), (0.20, 0.33), (0.33, 0.40), (0.45, 0.405), (0.53, 0.35), (0.58, 0.29)], 2.0)
            for k in range(30):
                u = (k + pen.r(0, 1)) / 30
                p = at(base, u)
                ang = self.tilt + 1.25 - u * 0.75 + pen.g(0.15)
                L = pen.r(4, 8)
                hd.add([p, (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)], w=0.8, clip=False, hand=0.1)


def lean_fn(pivot, ang, y0, y1):
    """Bends a figure forward above a height: no turn below y0, the full angle above y1."""
    def f(p):
        a = ang * smooth((y0 - p[1]) / (y0 - y1))
        c, s = math.cos(a), math.sin(a)
        dx, dy = p[0] - pivot[0], p[1] - pivot[1]
        return (pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c)
    return f


def foot(F, name, ankle, z, scale=1.0, joins=()):
    """A broad bare foot in profile, toes to the right, sole on the ground (y 860)."""
    ax, ay = ankle
    S = lambda pts: [(ax + x * scale, 860 - (860 - (ay + y)) * 1.0) for x, y in pts]
    poly = closed(S([(-18, 12), (-20, 26), (-18, 33), (8, 35), (52, 35), (72, 32), (76, 27), (70, 22), (58, 19),
                     (34, 10), (16, -2), (-12, -2)]), step=1.5)
    p = F.part(name, poly, z, joins=joins)
    p.add(catmull(S([(50, 22), (57, 28), (56, 34)]), step=1.0), w=0.85)            # big toe
    for dx in (61, 66):
        p.add(catmull(S([(dx, 24), (dx + 3, 29), (dx + 2, 34)]), step=1.0), w=0.8)
    p.add(catmull(S([(66, 20), (70, 22.5), (73, 26)]), step=1.0), w=0.8)            # toenail
    p.add(catmull(S([(-2, 2), (5, 7), (12, 5)]), step=1.0), w=0.9)                 # ankle bone
    p.add(catmull(S([(-12, 30), (14, 33), (44, 33)]), step=1.5), w=0.7)            # sole edge
    return p


# ------------------------------------------------------------------ figure A: standing man with a spear

def man():
    F = Figure('A.')
    head = Head(F, (302, 214), 110, 0.13, z=2.8)

    neck = F.part('neck', closed([(262, 222), (300, 246), (321, 262), (325, 282), (330, 302), (300, 314), (256, 300),
                                  (244, 270), (250, 240)]), 5, joins=('head', 'torso'))
    torso = F.part('torso', closed([
        (250, 262), (232, 292), (222, 334), (222, 384), (232, 432), (240, 462), (236, 492), (226, 528),
        (232, 566), (256, 590), (300, 590), (326, 552), (342, 508), (352, 466), (360, 430), (367, 394),
        (368, 358), (358, 324), (338, 302), (306, 298)]), 8, joins=('neck', 'thighN', 'thighF'))

    # near arm: shoulder (288, 312), elbow (304, 432), wrist (384, 410); a short forearm
    ua = Limb([(287, 310), (294, 368), (304, 432)],
              wa=[(0, 28), (0.2, 34), (0.6, 29), (1, 24)],
              wb=[(0, 30), (0.3, 34), (0.7, 29), (1, 26)], cap0=0.55, cap1=0.4)
    uarm = F.part('uarm', ua.poly, 2, joins=('farm', 'elbow'))
    elbow = F.part('elbow', blob(306, 430, 23, 22), 1.9, joins=('uarm', 'farm'))
    fa = Limb([(302, 433), (342, 426), (384, 409)],
              wa=[(0, 24), (0.3, 27), (0.75, 19), (1, 15.5)],
              wb=[(0, 25), (0.25, 25), (0.75, 18), (1, 15.5)], cap0=0.5, cap1=0.3)
    farm = F.part('farm', fa.poly, 1.5, joins=('uarm', 'fist', 'elbow'))
    G = lambda pts: [(404 + (x - 404) * 1.18, 408 + (y - 408) * 1.18) for x, y in pts]
    fist = F.part('fist', closed(G([(380, 397), (394, 390), (410, 388), (420, 389), (426, 397), (427, 407), (426, 417),
                                    (420, 426), (406, 429), (392, 426), (382, 421)]), step=1.5), 0.5, w=2.0, joins=('farm',))
    fist.add(catmull(G([(411, 391), (413, 408), (412, 425)]), step=1.0), w=1.0)
    for y in (398, 407, 416):
        fist.add(catmull(G([(413, y - 1), (419, y + 1), (426, y)]), step=1.0), w=1.0)
    fist.add(catmull(G([(393, 395), (404, 394), (414, 398), (420, 401)]), step=1.0), w=1.1)
    fist.add(catmull(G([(386, 412), (396, 418), (404, 426)]), step=1.0), w=0.8)

    # legs: the near one a step forward, knee easy; the far one back, carrying the weight
    th = Limb([(290, 468), (307, 590), (326, 680)],
              wa=[(0, 50), (0.4, 48), (0.85, 35), (1, 32)],
              wb=[(0, 50), (0.3, 46), (0.8, 33), (1, 30)], cap0=0.5, cap1=0.6)
    thighN = F.part('thighN', th.poly, 6.2, joins=('torso', 'shinN', 'kneeN'))
    sh = Limb([(326, 680), (326, 758), (318, 826)],
              wa=[(0, 30), (0.12, 28), (0.55, 21), (1, 17)],
              wb=[(0, 29), (0.3, 40), (0.6, 32), (1, 17)], cap0=0.6, cap1=0.5)
    shinN = F.part('shinN', sh.poly, 6.1, joins=('thighN', 'footN', 'kneeN'))
    kneeN = F.part('kneeN', blob(327, 680, 29, 27), 6.05, joins=('thighN', 'shinN'))
    footN = foot(F, 'footN', (318, 825), 6.0, joins=('shinN',))
    th2 = Limb([(278, 468), (274, 590), (264, 682)],
               wa=[(0, 48), (0.4, 45), (0.85, 33), (1, 30)],
               wb=[(0, 48), (0.3, 44), (0.8, 31), (1, 28)], cap0=0.5, cap1=0.6)
    thighF = F.part('thighF', th2.poly, 9.2, joins=('torso', 'shinF', 'kneeF'))
    sh2 = Limb([(264, 682), (252, 760), (236, 826)],
               wa=[(0, 28), (0.12, 26), (0.55, 20), (1, 16)],
               wb=[(0, 28), (0.3, 38), (0.6, 30), (1, 16)], cap0=0.6, cap1=0.5)
    shinF = F.part('shinF', sh2.poly, 9.1, joins=('thighF', 'footF', 'kneeF'))
    kneeF = F.part('kneeF', blob(264, 682, 27, 26), 9.05, joins=('thighF', 'shinF'))
    footF = foot(F, 'footF', (237, 825), 9.0, scale=0.97, joins=('shinF',))

    # hide cape over the shoulders, open in front, hanging behind to the thighs
    back = rag([(324, 298), (306, 291), (284, 285), (264, 272), (248, 266), (230, 284), (213, 330), (203, 400),
                (195, 470), (187, 540), (181, 600), (177, 640)], 0.5, 14)
    hem = rag([(177, 640), (196, 652), (214, 646), (230, 662), (246, 652), (262, 648)], 1.5, 7)
    near = rag([(262, 648), (264, 590), (263, 520), (261, 450), (262, 392), (267, 342), (279, 312), (296, 301),
                (312, 300), (324, 298)], 0.4, 14)
    cape = F.part('cape', back + hem[1:] + near[1:-1], 3, w=2.0)
    # hide wrap round the hips to mid-thigh, tied with a thong
    wtop = catmull([(236, 460), (270, 458), (310, 456), (350, 452)], step=2.0)
    wfront = catmull([(350, 452), (356, 490), (359, 530), (358, 566)], step=2.0)
    whem = rag([(358, 566), (342, 590), (320, 600), (302, 595), (284, 606), (264, 601), (246, 598)], 1.4, 7)
    wback = catmull([(246, 598), (238, 560), (234, 510), (236, 460)], step=2.0)
    wrap = F.part('wrap', wtop + wfront[1:] + whem[1:] + wback[1:-1], 4.5, w=1.9)

    # shading: skin modelled along each limb on the side away from the fire
    ua.shade(uarm, 0.08, 0.98, 'b', n=5, taper=0.12)
    ua.shade(uarm, 0.25, 0.9, 'a', n=2, taper=0.2)
    fa.shade(farm, 0.0, 0.85, 'b', n=4, taper=0.12)
    fa.shade(farm, 0.1, 0.7, 'a', n=1)
    uarm.add(catmull([(276, 326), (290, 318), (306, 320), (318, 330)], step=1.5), w=0.9)   # deltoid
    uarm.add(catmull([(312, 352), (318, 384), (316, 412)], step=1.5), w=0.85)         # biceps
    farm.add(catmull([(322, 419), (346, 413), (366, 408)], step=1.5), w=0.8)          # forearm muscle
    th.shade(thighN, 0.45, 0.98, 'b', n=5, taper=0.12)
    th.shade(thighN, 0.55, 0.95, 'a', n=2, taper=0.2)
    sh.shade(shinN, 0.0, 0.95, 'b', n=5, taper=0.12)
    sh.shade(shinN, 0.1, 0.85, 'a', n=1)
    sh.xhatch(shinN, 0.02, 0.22, spacing=6.0, side='b', frac=(0.2, 0.3), bow=2)       # hollow behind the knee
    shinN.add(catmull([(336, 712), (336, 760), (327, 806)], step=1.0), w=0.85)        # shin bone
    kneeN.add(catmull([(340, 668), (348, 680), (344, 694)], step=1.0), w=0.9)         # knee cap
    th2.shade(thighF, 0.45, 0.98, 'b', n=5, taper=0.08)
    sh2.shade(shinF, 0.0, 0.95, 'b', n=5, taper=0.08)
    sh2.shade(shinF, 0.05, 0.9, 'a', n=3, taper=0.1)
    th2.shade(thighF, 0.5, 0.95, 'a', n=3, taper=0.1)
    # torso: the deep barrel chest, modelled toward the back
    torso.add(catmull([(318, 338), (340, 354), (362, 352)], step=1.5), w=1.0)          # pectoral
    torso.add(catmull([(322, 404), (344, 416), (364, 410)], step=1.5), w=0.8)          # lower ribs
    torso.add(catmull([(340, 438), (354, 448)], step=1.5), w=0.75)                     # belly
    front = catmull([(358, 326), (366, 358), (366, 394), (359, 430), (352, 452)], step=2.0)
    for k in range(2):
        e2 = sub([(x - 6.0 * (k + 0.8), y) for x, y in front], 0.15 + 0.15 * k, 0.9 - 0.1 * k)
        for seg in broken(e2, (22, 60), (3, 7)):
            torso.add(seg, w=0.7)
    edge = catmull([(266, 456), (264, 410), (266, 360), (276, 322)], step=2.0)
    for k in range(4):
        e2 = [(x + 6.0 * (k + 0.8), y) for x, y in edge]
        e2 = sub(e2, 0.05 + 0.12 * k, 0.95 - 0.08 * k)
        for seg in broken(e2, (22, 60), (3, 7)):
            torso.add(seg, w=0.72)
    # neck: muscle from behind the ear to the notch, shadow under the jaw
    neck.add(catmull([(300, 240), (312, 272), (326, 298)], step=1.5), w=0.85)
    for k in range(4):
        x = 302 + k * 5.5
        neck.add([(x, 262 + k * 1.5), (x + 3, 286 + k * 2)], w=0.7)
    # cape: hair of the hide in rows down the drape, denser at the back; fur at the hem
    eb = sub(back, 0.12, 1.0)
    en = sub(near[::-1], 0.08, 1.0)
    fur(cape, en, eb, [0.10, 0.22, 0.34, 0.45, 0.55, 0.64, 0.72, 0.80, 0.87, 0.94], keep=0.8)
    drape(cape, en, eb, [0.5, 0.78], w=1.0, piece=(40, 120), keep=0.6, t0=0.15)
    fur_edge(cape, hem, inward=1)
    fur_edge(cape, sub(back, 0.25, 1.0), every=11, ln=(3, 6), inward=-1, keep=0.6)
    # wrap: hair of the hide hanging down, the thong round the waist
    wl = catmull([(240, 466), (238, 530), (246, 596)], step=2.0)
    wr = catmull([(352, 462), (356, 520), (356, 566)], step=2.0)
    fur(wrap, wl, wr, [0.06, 0.16, 0.26, 0.36, 0.46, 0.56, 0.66], keep=0.8, t0=0.05)
    wrap.add(catmull([(236, 468), (290, 466), (352, 461)], step=2.0), w=1.2)
    wrap.add(catmull([(346, 464), (350, 482), (346, 500)], step=1.5), w=1.0)          # thong end
    wrap.add(catmull([(352, 464), (358, 480), (356, 494)], step=1.5), w=1.0)
    fur_edge(wrap, whem, inward=1)
    return F


def add_spear(F, grip):
    """The spear: a wooden shaft through the fist, a stone point hafted with sinew."""
    phi = 0.045
    d = (math.sin(phi), math.cos(phi))
    top = (grip[0] - d[0] * (grip[1] - 106) / d[1], 106)
    n = (-d[1], d[0])
    S = lambda s, w: (top[0] + d[0] * s + n[0] * w, top[1] + d[1] * s + n[1] * w)
    length = (858 - 106) / d[1]
    shaft = F.part('shaft', [S(58, -4.6), S(length - 2, -4.8), S(length, 0), S(length - 2, 4.8), S(58, 4.6)], 0.8, w=1.7)
    point = F.part('point', closed([S(0, 0), S(14, -5), S(30, -9.5), S(44, -10), S(58, -5.5), S(62, 0),
                                    S(58, 5.5), S(44, 10), S(30, 9.5), S(14, 5)], step=1.0), 0.7, w=1.7)
    point.add([S(3, 0.5), S(30, -0.5), S(56, 0.3)], w=0.9)
    for s0, w0 in ((16, -5), (28, -8), (40, -8.5), (22, 6), (35, 8.5)):
        point.add(catmull([S(s0, w0), S(s0 + 6, w0 * 0.45), S(s0 + 10, 0)], step=1.0), w=0.8)
    bind = F.part('bind', [S(50, -6.5), S(80, -6), S(80, 6), S(50, 6.5)], 0.6, w=1.4)
    for k in range(7):
        s0 = 52 + k * 4
        bind.add([S(s0, -6.5), S(s0 + 3.5, 6.5)], w=1.0, hand=0)
    for s0, s1, w0 in ((120, 170, 1.5), (260, 300, -1.8), (470, 520, 1.2), (640, 690, -1.0)):
        shaft.add([S(s0, w0), S(s1, w0 * 0.8)], w=0.7)


# ------------------------------------------------------------------ figure B: squatting woman knapping flint

def woman():
    F = Figure('B.')
    head = Head(F, (258, 528), 100, 0.30, z=2.8, female=True)
    neck = F.part('neck', closed([(222, 528), (250, 556), (268, 570), (276, 598), (250, 610), (205, 584), (202, 556),
                                  (212, 534)]), 5, joins=('head', 'torso'))
    torso = F.part('torso', closed([
        (208, 560), (180, 582), (152, 615), (128, 660), (110, 710), (100, 752), (98, 780), (110, 796), (140, 798),
        (190, 768), (240, 728), (272, 702), (288, 668), (290, 630), (280, 602), (262, 586), (238, 574)]), 8,
        joins=('neck', 'thighN'))

    # near leg in a deep squat: hip (135, 742), knee (300, 708), ankle (206, 828)
    th = Limb([(135, 742), (218, 730), (300, 708)],
              wa=[(0, 43), (0.5, 39), (0.9, 31), (1, 29)],
              wb=[(0, 43), (0.5, 36), (1, 28)], cap0=0.5, cap1=0.7)
    thighN = F.part('thighN', th.poly, 6.5, joins=('torso', 'kneeN'))
    sh = Limb([(300, 708), (252, 770), (206, 828)],
              wa=[(0, 28), (0.12, 26), (0.55, 20), (1, 15.5)],
              wb=[(0, 28), (0.3, 36), (0.65, 28), (1, 15.5)], cap0=0.6, cap1=0.5)
    shinN = F.part('shinN', sh.poly, 6.2, joins=('footN', 'kneeN'))
    kneeN = F.part('kneeN', blob(300, 708, 26, 25), 6.0, joins=('thighN', 'shinN'))
    footN = foot(F, 'footN', (206, 826), 6.1, scale=0.95, joins=('shinN',))
    footF = foot(F, 'footF', (220, 822), 9.0, scale=0.93)
    # hip wrap over the buttocks
    whem = rag([(240, 712), (222, 738), (190, 758), (160, 778), (130, 796), (106, 800)], 1.3, 7)
    wrap = F.part('wrap', [(104, 712), (170, 706), (240, 690)] + whem + [(96, 780), (96, 748)], 6.3, w=1.9)

    # near arm: elbow on the thigh, forearm across the knee, the core cupped in front
    ua = Limb([(234, 590), (258, 642), (278, 690)],
              wa=[(0, 25), (0.3, 27), (1, 21)], wb=[(0, 25), (0.4, 26), (1, 21)], cap0=0.8, cap1=0.5)
    uarm = F.part('uarm', ua.poly, 3.5, joins=('farm', 'elbow'))
    elbow = F.part('elbow', blob(279, 692, 20, 19), 1.6, joins=('uarm', 'farm'))
    fa = Limb([(279, 694), (316, 704), (350, 714)],
              wa=[(0, 21), (0.3, 22), (0.8, 15.5), (1, 14)],
              wb=[(0, 21), (0.3, 21), (0.8, 14.5), (1, 13.5)], cap0=0.5, cap1=0.3)
    farm = F.part('farm', fa.poly, 1.5, joins=('uarm', 'hand', 'elbow'))
    hand = F.part('hand', closed([(344, 702), (356, 703), (368, 710), (384, 711), (396, 705), (402, 698), (408, 700),
                                  (411, 710), (406, 723), (394, 733), (374, 737), (356, 734), (344, 727)], step=1.0),
                  1.0, w=2.0, joins=('farm',))
    hand.add(catmull([(392, 716), (399, 725), (395, 733)], step=1.0), w=0.95)
    hand.add(catmull([(401, 710), (407, 717), (405, 726)], step=1.0), w=0.95)
    hand.add(catmull([(352, 726), (370, 733), (388, 731)], step=1.0), w=0.75)
    thumb = F.part('thumb', closed([(354, 707), (360, 697), (370, 690), (381, 688), (383, 694), (374, 700), (364, 710)],
                                   step=1.0), 0.9, w=1.5)
    thumb.add(catmull([(375, 690), (377, 695)], step=1.0), w=0.8)
    # the flint core: an angular nodule, its face taken down in flat flake scars
    core = F.part('core', [(360, 700), (363, 687), (375, 678), (394, 676), (407, 683), (411, 696), (403, 707), (381, 711)],
                  1.2, w=1.8)
    core.add([(369, 683), (386, 692), (408, 690)], w=0.9, hand=0)
    core.add([(386, 692), (393, 677)], w=0.9, hand=0)
    core.add([(386, 692), (378, 710)], w=0.8, hand=0)
    for k in range(2):
        core.add(catmull([(391 + k * 5, 697 + k * 2), (396 + k * 5, 700 + k * 2), (401 + k * 4, 698 + k * 2)], step=1.0),
                 w=0.7, hand=0)
    # far arm: forearm raised from under the shawl, the hammerstone poised over the core
    fa2 = Limb([(268, 660), (302, 648), (336, 636)],
               wa=[(0, 20), (0.3, 21), (0.8, 14.5), (1, 13.5)],
               wb=[(0, 20), (0.3, 20), (0.8, 14), (1, 13)], cap0=0.5, cap1=0.3)
    farm2 = F.part('farm2', fa2.poly, 3.6, joins=('hand2',))
    hand2 = F.part('hand2', closed([(330, 628), (342, 620), (356, 618), (367, 623), (372, 633), (368, 644), (355, 649),
                                    (341, 647), (332, 639)], step=1.0), 2.9, w=2.0, joins=('farm2',))
    hand2.add(catmull([(354, 620), (364, 626), (369, 636)], step=1.0), w=1.0)
    for y in (631, 639):
        hand2.add(catmull([(359, y - 1), (365, y + 1), (370, y)], step=1.0), w=0.9)
    hand2.add(catmull([(340, 624), (350, 628), (360, 627)], step=1.0), w=0.85)
    stone = F.part('stone', closed([(350, 644), (362, 638), (378, 639), (390, 647), (390, 659), (378, 666), (360, 664),
                                    (351, 655)], step=1.0), 2.95, w=1.9)
    for k in range(3):
        stone.add(catmull([(362 + k * 8, 659 - k), (368 + k * 7, 663), (374 + k * 5, 662)], step=1.0), w=0.72)
    thumb2 = F.part('thumb2', closed([(338, 642), (350, 645), (362, 649), (368, 654), (364, 658), (352, 655), (340, 650)],
                                     step=1.0), 2.85, w=1.5)
    # a flake flying from the strike
    fl = F.part('flake', [(414, 664), (424, 659), (428, 667), (419, 672)], 0.5, w=1.3)
    for k in range(2):
        fl.add([(404 - k * 3, 672 + k * 6), (410 - k * 3, 669 + k * 6)], w=0.8, clip=False)

    # hide shawl over the shoulders and back, the forearms coming out in front
    back = rag([(272, 580), (250, 566), (228, 556), (206, 556), (178, 574), (150, 606), (126, 650), (108, 700),
                (100, 728)], 0.5, 14)
    hem = rag([(100, 728), (130, 724), (165, 712), (200, 698), (235, 684), (262, 674), (286, 668)], 1.4, 7)
    front = rag([(286, 668), (291, 645), (289, 620), (283, 600), (277, 588), (272, 580)], 0.4, 12)
    shawl = F.part('shawl', back + hem[1:] + front[1:-1], 3.2, w=2.0)

    # shading
    th.shade(thighN, 0.0, 0.92, 'b', n=5, taper=0.1)
    th.shade(thighN, 0.35, 0.9, 'a', n=2, taper=0.2)
    sh.shade(shinN, 0.05, 0.95, 'b', n=5, taper=0.1)
    sh.shade(shinN, 0.15, 0.85, 'a', n=1)
    shinN.add(catmull([(286, 738), (262, 772), (234, 808)], step=1.5), w=0.85)
    kneeN.add(catmull([(316, 692), (324, 704), (322, 718)], step=1.0), w=0.9)
    fa.shade(farm, 0.0, 0.85, 'b', n=3)
    fa2.shade(farm2, 0.0, 0.9, 'b', n=3)
    ua.shade(uarm, 0.5, 1.0, 'b', n=2)
    # shawl and wrap
    eb = sub(back, 0.15, 1.0)
    ef = sub(front[::-1], 0.05, 1.0)
    fur(shawl, ef, eb, [0.10, 0.21, 0.32, 0.42, 0.51, 0.60, 0.68, 0.76, 0.84, 0.91, 0.97], keep=0.8)
    drape(shawl, ef, eb, [0.55, 0.85], w=1.0, piece=(40, 120), keep=0.6, t0=0.1)
    fur_edge(shawl, hem, inward=1)
    fur_edge(shawl, sub(back, 0.2, 1.0), every=11, ln=(3, 6), inward=-1, keep=0.6)
    w1 = catmull([(104, 716), (100, 760), (108, 798)], step=2.0)
    w2 = catmull([(236, 696), (226, 724), (210, 748)], step=2.0)
    fur(wrap, w1, w2, [0.08, 0.2, 0.32, 0.44, 0.56, 0.68], keep=0.8)
    fur_edge(wrap, whem, inward=1)
    return F


# ------------------------------------------------------------------ the hearth

def hearth():
    F = Figure('H.')
    cx, cy = 505, 838
    for k, ang in enumerate((200, 245, 290, 335, 20, 65, 110, 155)):
        a = math.radians(ang)
        x, y = cx + 68 * math.cos(a), cy + 15 * math.sin(a)
        front = math.sin(a) > 0
        rx, ry = (pen.r(15, 19), pen.r(9, 11)) if front else (pen.r(12, 15), pen.r(7, 9))
        poly = closed([(x + rx * math.cos(t) * pen.r(0.8, 1.12), y - ry * 0.6 + ry * math.sin(t) * pen.r(0.8, 1.12))
                       for t in [i * math.pi / 3.5 + pen.r(-0.2, 0.2) for i in range(7)]], step=1.5)
        st = F.part(f'stone{k}', poly, 1.0 if front else 6.0, w=1.7)
        st.add(catmull([(x - rx * 0.6, y + ry * 0.05), (x, y + ry * 0.3), (x + rx * 0.7, y)], step=1.0), w=0.75)
    # wood: two sticks crossed in the hearth
    for k, (p0, p1, w0) in enumerate((((452, 840), (552, 816), 5.5), ((560, 838), (460, 816), 5.0))):
        d = ((p1[0] - p0[0]) / dist(p0, p1), (p1[1] - p0[1]) / dist(p0, p1))
        n = (-d[1], d[0])
        poly = [(p0[0] + n[0] * w0, p0[1] + n[1] * w0), (p1[0] + n[0] * w0, p1[1] + n[1] * w0),
                (p1[0] + d[0] * 3, p1[1] + d[1] * 3), (p1[0] - n[0] * w0, p1[1] - n[1] * w0),
                (p0[0] - n[0] * w0, p0[1] - n[1] * w0)]
        stick = F.part(f'stick{k}', poly, 3.0 + k * 0.5, w=1.5)
        for s in (0.2, 0.5, 0.8):
            q = lerp(p0, p1, s)
            stick.add([(q[0] - n[0] * w0, q[1] - n[1] * w0), (q[0] + d[0] * 4 + n[0] * w0 * 0.2, q[1] + d[1] * 4)], w=0.7)

    def flame(bx, by, H, W, lean, z, name):
        ctrl = [(bx - W / 2, by), (bx - W * 0.56, by - H * 0.22), (bx - W * 0.42, by - H * 0.48),
                (bx - W * 0.12 + lean * 0.4, by - H * 0.74), (bx + lean, by - H),
                (bx + W * 0.16 + lean * 0.55, by - H * 0.70), (bx + W * 0.42, by - H * 0.45),
                (bx + W * 0.52, by - H * 0.18), (bx + W / 2, by)]
        pts = catmull(ctrl, step=1.5)
        p = F.part(name, pts, z, w=1.6, outline=[pts])
        inner = [(bx - W * 0.22, by - 2), (bx - W * 0.25, by - H * 0.3), (bx - W * 0.05 + lean * 0.2, by - H * 0.55),
                 (bx + lean * 0.5 + W * 0.05, by - H * 0.62), (bx + W * 0.15, by - H * 0.35), (bx + W * 0.2, by - 2)]
        p.add(catmull(inner, step=1.5), w=1.0)
        return p

    flame(505, 830, 104, 46, -6, 2.0, 'flame0')
    flame(480, 832, 62, 30, -12, 2.2, 'flame1')
    flame(531, 832, 70, 30, 9, 2.1, 'flame2')
    for x, y in ((486, 708), (522, 694), (507, 672), (534, 720), (474, 732)):
        sp = F.part(f'spark{x}', blob(x, y, 1.0, 1.0), 0.5, w=1.0, outline=[])
        sp.add(blot_pts(x, y, 1.3, w=1.2), w=1.2, clip=False, hand=0, lift=0, piece=(400, 800))
    return F


def settle(p):
    y = p[1]
    dy = 16 if y <= 505 else (16 * (690 - y) / 185 if y < 690 else 0)
    return (p[0], y + dy)


A = man()
A.apply(settle)
A.apply(lean_fn((290, 520), 0.06, 520, 420))
fist = [p for p in A.parts if p.name == 'A.fist'][0]
add_spear(A, (sum(p[0] for p in fist.poly) / len(fist.poly) + 2, sum(p[1] for p in fist.poly) / len(fist.poly)))
B = woman()
HF = hearth()

AX = -40
BS, BC = 0.96, 1000
A.apply(lambda p: (p[0] + AX, p[1]))
# she is mirrored to face the fire, a touch smaller, on the same ground
B.apply(lambda p: (BC - p[0] * BS, 858 - (858 - p[1]) * BS))
parts = A.parts + B.parts + HF.parts
for p in parts:
    p.finish()


def runs_of(pts, keep):
    fine = resample(pts, 1.5)
    runs, cur = [], []
    for q in fine:
        if keep(q):
            cur.append(q)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def render(parts):
    for P in parts:
        front = [Q for Q in parts if Q is not P and (Q.z < P.z or Q.name in P.joins)]
        cover = [Q for Q in parts if Q is not P and Q.z < P.z]
        others = [Q for Q in parts if Q is not P and Q.name.split('.')[0] == P.name.split('.')[0]]
        for ol in P.outline:
            for run in runs_of(ol, lambda q: not any(Q.has(q) for Q in front)):
                # heavy where the outline meets empty ground, lighter across other parts
                nrm = normals(run)
                kinds = []
                for q, n in zip(run, nrm):
                    a = (q[0] + n[0] * 4, q[1] + n[1] * 4)
                    b = (q[0] - n[0] * 4, q[1] - n[1] * 4)
                    o = b if P.has(a) else a
                    kinds.append(any(Q.has(o) for Q in others))
                seg, k0 = [run[0]], kinds[0]
                for q, k in zip(run[1:], kinds[1:]):
                    seg.append(q)
                    if k != k0 and len(seg) > 6:
                        pen.line(seg, w=(P.inner_w or P.w * 0.7) if k0 else P.w, occlude=False)
                        seg, k0 = [q], k
                if len(seg) > 1:
                    pen.line(seg, w=(P.inner_w or P.w * 0.7) if k0 else P.w, occlude=False)
        for pts, w, clip, kw in P.strokes:
            if clip:
                keep = lambda q: P.has(q) and not any(Q.has(q) for Q in cover)
            else:
                keep = lambda q: not any(Q.has(q) for Q in cover)
            for run in runs_of(pts, keep):
                args = dict(hand=0.4, lift=0.05, piece=(40, 120))
                args.update(kw)
                pen.line(run, w=max(0.72, w), occlude=False, **args)


render(parts)


# smoke: a thin plume of wavy lines rising from the flames and drifting off, widening as it goes
for k in range(4):
    pts = []
    off = (k - 1.5) * 1.0
    for i in range(60):
        u = i / 59
        y = 706 - u * 310
        spread = off * (3 + 16 * u)
        x = 500 + spread + 10 * math.sin(u * 9.0 + k * 0.5) * (0.3 + u) + u * u * 110
        pts.append((x, y))
    pts = sub(pts, 0.0, 1.0 - 0.12 * abs(off))
    for seg in broken(pts, (16, 44), (5, 14), 0.8):
        pen.line(seg, w=0.85 if k in (1, 2) else 0.75, hand=0.3, lift=0, occlude=False)


# ground: cast shadows away from the fire, a few strokes of earth, flint flakes
def ground_hatch(x0, x1, y, rows, spacing=5.5):
    for k in range(rows):
        yy = y + k * spacing
        shrink = (x1 - x0) * (0.06 + 0.07 * k)
        a, b = x0 + shrink + pen.r(-6, 6), x1 - shrink * 0.6 + pen.r(-6, 6)
        if b - a > 8:
            pen.line([(a, yy), (b, yy)], w=0.8, hand=0.4, lift=0.15, piece=(15, 40))


ground_hatch(140, 360, 862, 4)
ground_hatch(610, 920, 862, 4)
for x0, x1, y in ((90, 160, 880), (380, 470, 868), (560, 640, 874), (420, 520, 900), (700, 800, 902),
                  (210, 300, 905), (880, 950, 884), (620, 680, 920)):
    pen.line([(x0, y), (x1, y)], w=0.9, hand=0.5, lift=0.3, piece=(12, 30))
for x, y, s, r in ((566, 866, 8, 0.3), (584, 878, 6, 1.4), (600, 868, 7, 2.2), (614, 884, 5, 0.9), (552, 884, 6, 2.8)):
    pts = [(x + s * math.cos(r + a), y + s * 0.6 * math.sin(r + a)) for a in (0, 2.0, 3.6, 5.0)]
    pen.line(pts + [pts[0]], w=1.0, hand=0, lift=0)
    pen.line([pts[0], lerp(pts[2], pts[1], 0.5)], w=0.7, hand=0, lift=0)

pen.save('../19-neanderthals.svg', mirror=True)
pen.report()
