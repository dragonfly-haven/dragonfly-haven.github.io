#!/usr/bin/env python3
"""19 Neanderthals: two Neanderthals at a hearth under a rock overhang.

A standing man holding a spear tipped with a Levallois point set in resin, and a
squatting woman knapping a flint core with a hammerstone, face each other
across a fire of crossed branches in a ring of stones. Both are built from a
skeleton of joints (hip, knee, ankle, shoulder, elbow, wrist) with limb
contours swelling for the muscles, and with Neanderthal proportions: big
long-low heads (one heavy brow bar, large projecting nose and mid-face, no
chin, occipital bun), short necks, deep barrel chests, short forearms and
shins, thick limbs, broad feet with toes. Clothing is draped hide only, the
man's wrap rolled over a knotted thong.

Every body part is a closed outline with a depth (z). An outline is hidden
where a part in front of it covers it, or where it runs inside a part it is
joined to (so a thigh flows into a hip without a seam). Outlines are heavy
where they bound the figure against the empty ground and lighter where they
cross another part. Skin is modelled engraver-fashion: regular rows of short
slanted strokes in from the side away from the fire, every other row running
on into the half-tone, crossed in the deepest shadow; hides carry rows of
short hairs and fur at their edges.

Run from this folder: python3 19-neanderthals.py   (writes ../19-neanderthals.svg)
"""

import math

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, scanlines

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


# ------------------------------------------------------------------ hatching that models skin

def keep_prob(u, full, fade, light):
    """How likely a hatch stroke is kept at u (0 = deepest shadow, 1 = lit side)."""
    if u < full:
        return 1.0
    if u < fade:
        return 1.0 - (u - full) / (fade - full) * (1.0 - light)
    return light


def skin(part, limb, t0, t1, side='b', depth=0.45, row=5.8, ang=0.3, ln=(9, 15), gap=(2, 3.5), w=0.72,
         wob=0.18, ends=0.12, cross=0.0, ext=1.0):
    """Engraver's hatching on the shadow side of a limb: regular rows of strokes
    from the shadow edge in toward the middle, slanted a little along the limb,
    the inner edge of the band wavering softly. With cross, a second slant
    crosses the deepest part of the shadow."""
    sg = -1 if side == 'b' else 1
    rows = max(1, int(limb.L * (t1 - t0) / row))
    ph = pen.r(0, 6.3)
    for layer, (a0, dep) in enumerate(((ang, depth), (-ang - 0.55, depth * cross))):
        if dep <= 0:
            continue
        for k in range(rows):
            t = t0 + (t1 - t0) * (k + 0.5 + pen.g(0.04)) / rows
            e = 1.0
            if ends:
                e = max(0.0, min(1.0, (t - t0) / ((t1 - t0) * ends), (t1 - t) / ((t1 - t0) * ends)))
            i = limb.idx(t)
            nn = limb.n[i]
            d = limb.along(t)
            inward = (-sg * nn[0], -sg * nn[1])
            a = a0 + pen.g(0.03)
            ca, sa = math.cos(a), math.sin(a)
            dv = (inward[0] * ca + d[0] * sa, inward[1] * ca + d[1] * sa)
            W = prof(limb.wa, t) + prof(limb.wb, t)
            D = W * dep * (1 + wob * math.sin(ph + k * 0.55 + layer * 2)) * (0.35 + 0.65 * e)
            if layer == 0 and k % 2 == 0:
                D *= ext
            q = limb.pt(t, sg * 0.985)
            proj = 0.0
            while proj < D:
                L = min(pen.r(*ln), (D - proj) / ca + 1.5)
                if L < 3:
                    break
                e_ = (q[0] + dv[0] * L, q[1] + dv[1] * L)
                m = lerp(q, e_, 0.5)
                b = pen.g(0.6)
                part.add(catmull([q, (m[0] - dv[1] * b, m[1] + dv[0] * b), e_], step=1.5),
                         w=w * pen.r(0.92, 1.08), hand=0.1, lift=0)
                g = pen.r(*gap)
                q = (e_[0] + dv[0] * g, e_[1] + dv[1] * g)
                proj += (L + g) * ca


def edge_shade(part, edge, inward, depth=12, every=5.5, ang=0.3, w=0.72, keep=1.0):
    """A band of short parallel strokes in from an edge (a cast shadow, a hollow)."""
    pts = resample(edge, every)
    nrm = normals(pts)
    ph = pen.r(0, 6.3)
    for k, (p, n) in enumerate(zip(pts, nrm)):
        if pen.rng.random() > keep:
            continue
        dx, dy = n[0] * inward, n[1] * inward
        c, s = math.cos(ang), math.sin(ang)
        dx, dy = dx * c - dy * s, dx * s + dy * c
        L = depth * (0.75 + 0.25 * math.sin(ph + k * 0.6)) * pen.r(0.85, 1.1)
        part.add([(p[0] - dx * 1.5, p[1] - dy * 1.5), (p[0] + dx * L, p[1] + dy * L)], w=w * pen.r(0.92, 1.08),
                 hand=0.1, lift=0)


def chaikin(pts, n=2):
    """Cuts the corners of a closed polygon, leaving it faceted but not sharp."""
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out += [lerp(a, b, 0.25), lerp(a, b, 0.75)]
        pts = out
    return resample(pts + [pts[0]], 1.5)[:-1]


def field(part, poly, angle, spacing, prob, ln=(6, 11), gap=(2.5, 5), w=0.72, bow=0.8, clip=True):
    """Short broken hatching over a region, each stroke kept with prob(its middle)."""
    for p0, p1 in scanlines(poly, angle, spacing, pen.r()):
        L = dist(p0, p1)
        if L < 3:
            continue
        dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        s = pen.r(0, 4)
        while s < L:
            ln_ = min(pen.r(*ln), L - s)
            if ln_ > 2.5:
                a = (p0[0] + dx * s, p0[1] + dy * s)
                e = (p0[0] + dx * (s + ln_), p0[1] + dy * (s + ln_))
                m = lerp(a, e, 0.5)
                if pen.rng.random() < prob(m):
                    b = pen.g(bow)
                    part.add(catmull([a, (m[0] - dy * b, m[1] + dx * b), e], step=1.5), w=w * pen.r(0.9, 1.1),
                             hand=0.15, lift=0, clip=clip)
            s += ln_ + pen.r(*gap)


def capsule(F, name, pts, r, z, joins=(), w=1.6, taper=0.9):
    """A finger or thumb: a rounded tube along pts."""
    L = Limb(pts, wa=[(0, r), (1, r * taper)], wb=[(0, r), (1, r * taper)], cap0=1.0, cap1=1.0)
    return F.part(name, L.poly, z, w=w, joins=joins), L


# ------------------------------------------------------------------ the Neanderthal head

# Profiles facing right, in head heights, ear canal at the origin, y down.
# Long low vault with an occipital bun, a low sloping forehead, a heavy
# brow ridge jutting over the eyes, a big projecting nose and mid-face, a long
# upper lip, no chin. The man's brow bar and face jut further than the woman's.
VAULT = [
    (-0.30, 0.16), (-0.38, 0.06), (-0.455, -0.02), (-0.525, -0.10), (-0.55, -0.19),
    (-0.515, -0.30), (-0.43, -0.395), (-0.28, -0.47), (-0.08, -0.505), (0.12, -0.497),
    (0.28, -0.458), (0.40, -0.392), (0.462, -0.330)]
JAW = [(0.300, 0.434), (0.225, 0.424), (0.10, 0.38), (-0.10, 0.28), (-0.22, 0.22)]
FACE_F = [
    (0.500, -0.284), (0.528, -0.266), (0.566, -0.246), (0.600, -0.208), (0.604, -0.168), (0.584, -0.140),
    (0.556, -0.126), (0.548, -0.108), (0.580, -0.064), (0.630, -0.004), (0.676, 0.054), (0.704, 0.094),
    (0.706, 0.120), (0.688, 0.136), (0.645, 0.145), (0.612, 0.152), (0.617, 0.186), (0.622, 0.214),
    (0.607, 0.233), (0.612, 0.252), (0.598, 0.275), (0.566, 0.305), (0.530, 0.348), (0.494, 0.392),
    (0.452, 0.422), (0.390, 0.436)]
FACE_M = [
    (0.498, -0.292), (0.532, -0.282), (0.580, -0.266), (0.622, -0.234), (0.640, -0.196), (0.632, -0.162),
    (0.606, -0.146), (0.582, -0.140), (0.600, -0.104), (0.656, -0.030), (0.714, 0.036), (0.758, 0.086),
    (0.764, 0.120), (0.742, 0.142), (0.694, 0.152), (0.650, 0.156), (0.654, 0.188), (0.658, 0.214),
    (0.642, 0.234), (0.647, 0.254), (0.630, 0.281), (0.594, 0.315), (0.552, 0.357), (0.508, 0.398),
    (0.460, 0.426), (0.392, 0.438)]

FEAT_M = dict(
    brow_lo=[(0.38, -0.170), (0.47, -0.180), (0.56, -0.168), (0.625, -0.152)],
    brow_hi=[(0.40, -0.268), (0.48, -0.282), (0.56, -0.270)],
    eye=(0.512, -0.104), orbit=(0.43, 0.60),
    wing=[(0.732, 0.066), (0.704, 0.084), (0.696, 0.116), (0.712, 0.138)],
    nostril=[(0.724, 0.134), (0.706, 0.128), (0.688, 0.134)],
    fold=[(0.668, 0.050), (0.640, 0.112), (0.638, 0.175), (0.654, 0.222)],
    mouth=[(0.642, 0.234), (0.612, 0.239), (0.578, 0.245)],
    cheek=[(0.50, -0.04), (0.46, 0.025), (0.40, 0.065)],
    beard=[(0.10, 0.22), (0.20, 0.33), (0.33, 0.40), (0.46, 0.415), (0.56, 0.37), (0.63, 0.30)],
    region=[(0.05, -0.21), (0.36, -0.215), (0.47, -0.13), (0.53, -0.02), (0.62, 0.07), (0.64, 0.22),
            (0.60, 0.33), (0.48, 0.43), (0.30, 0.44), (0.14, 0.39), (0.05, 0.22), (0.03, 0.0)],
    front=0.62)
FEAT_F = dict(
    brow_lo=[(0.37, -0.160), (0.45, -0.180), (0.53, -0.180), (0.588, -0.165)],
    brow_hi=[(0.41, -0.275), (0.47, -0.282), (0.523, -0.268)],
    eye=(0.488, -0.096), orbit=(0.405, 0.56),
    wing=[(0.640, 0.074), (0.618, 0.090), (0.612, 0.115), (0.626, 0.134)],
    nostril=[(0.668, 0.129), (0.650, 0.123), (0.634, 0.129)],
    fold=[(0.590, 0.058), (0.570, 0.115), (0.572, 0.175), (0.588, 0.222)],
    mouth=[(0.607, 0.233), (0.58, 0.238), (0.546, 0.247)],
    cheek=[(0.45, -0.04), (0.41, 0.025), (0.35, 0.065)],
    region=[(0.05, -0.21), (0.34, -0.21), (0.44, -0.13), (0.49, -0.02), (0.56, 0.07), (0.58, 0.22),
            (0.55, 0.32), (0.45, 0.42), (0.30, 0.44), (0.14, 0.39), (0.05, 0.22), (0.03, 0.0)],
    front=0.56)

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
        self.ft = FEAT_F if female else FEAT_M
        prof_pts = VAULT + (FACE_F if female else FACE_M) + JAW
        throat = prof_pts.index((0.225, 0.424))
        ctrl = self.P(prof_pts)
        poly = closed(ctrl, step=1.5)
        self.part = F.part('head', poly, z, w=2.2, outline=[catmull(ctrl[0:throat + 1], step=1.5)], joins=('neck',))
        outer, line = HAIR_F if female else HAIR_M
        self.outer = rag(self.P(outer), 0.8, 8)
        self.line = catmull(self.P(line), step=2.0)
        # the hair's edge is drawn as overlapping locks, not as one line
        self.hair = F.part('hair', self.outer + self.line[::-1][1:-1], z - 0.3, w=2.0, outline=[])
        self.details()

    def P(self, pts):
        c, s = math.cos(self.tilt), math.sin(self.tilt)
        return [(self.ear[0] + (x * c - y * s) * self.h, self.ear[1] + (x * s + y * c) * self.h) for x, y in pts]

    def inv(self, p):
        c, s = math.cos(self.tilt), math.sin(self.tilt)
        dx, dy = p[0] - self.ear[0], p[1] - self.ear[1]
        return ((dx * c + dy * s) / self.h, (-dx * s + dy * c) / self.h)

    def C(self, pts, step=1.0):
        return catmull(self.P(pts), step=step)

    def details(self):
        hd, hair, h, ft = self.part, self.hair, self.h, self.ft
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
        for k in range(4 if not self.female else 6):
            a = self.P([(-0.42 + 0.03 * k, 0.24 + 0.03 * k)])[0] if not self.female else self.P([(-0.46 + 0.02 * k, 0.55 + 0.04 * k)])[0]
            b = (a[0] + pen.r(-3, 3), a[1] + pen.r(12, 20))
            hair.add(catmull([a, lerp(a, b, 0.5), b], step=1.5), w=pen.r(0.9, 1.2), clip=False, hand=0.4)

        # the brow ridge: one heavy bar, its lower margin over the eye, the step above
        hd.add(self.C(ft['brow_lo']), w=2.1, hand=0.2)
        hd.add(self.C(ft['brow_hi']), w=1.1, hand=0.2)
        x0, x1 = ft['orbit']
        k = 0
        while x0 + k * 0.022 < x1:
            u = x0 + k * 0.022
            hd.add(self.C([(u, -0.166), (u - 0.006, -0.145), (u - 0.016, -0.128)]), w=0.75, hand=0.1)
            k += 1
        # the eye under it: lid fold, a heavy upper lid over the iris, lower lid
        ex, ey = ft['eye']
        hd.add(self.C([(ex - 0.032, ey - 0.030), (ex + 0.004, ey - 0.040), (ex + 0.036, ey - 0.030)]), w=0.95, hand=0.1)
        hd.add(self.C([(ex - 0.038, ey - 0.004), (ex - 0.004, ey - 0.020), (ex + 0.034, ey - 0.008)]), w=1.7, hand=0.1)
        hd.add(self.C([(ex - 0.030, ey + 0.010), (ex + 0.004, ey + 0.017), (ex + 0.030, ey + 0.003)]), w=0.85, hand=0.1)
        e = self.P([(ex + 0.004, ey - 0.006)])[0]
        hd.add(blot_pts(e[0], e[1], 0.016 * h, w=1.4), w=1.4, clip=False, hand=0, lift=0, piece=(400, 800))
        # big nose: the wing, the nostril, the fold down to the mouth
        hd.add(self.C(ft['wing']), w=1.25, hand=0.1)
        hd.add(self.C(ft['nostril']), w=1.0, hand=0.1)
        hd.add(self.C(ft['fold']), w=0.85, hand=0.2)
        hd.add(self.C(ft['mouth']), w=1.2, hand=0.1)
        hd.add(self.C(ft['cheek']), w=0.8, hand=0.2)
        hd.add(self.C([(0.05, 0.13), (0.085, 0.27), (0.15, 0.35), (0.26, 0.395), (0.36, 0.41)]), w=0.95, hand=0.2)
        # the ear
        ear = self.P([(0.0, -0.01)])[0]
        rot = self.tilt - 0.2
        hd.add(ellipse_pts(ear[0], ear[1], 0.064 * h, 0.118 * h, rot, -2.2, 2.4, step=1.0), w=1.3, hand=0.1)
        hd.add(ellipse_pts(ear[0] - 0.006 * h, ear[1] + 0.005 * h, 0.03 * h, 0.07 * h, rot, -1.5, 1.7, step=1.0), w=0.9, hand=0.1)
        # modelling: the side of the face in short hatching, dark toward the ear and jaw,
        # thinning out toward the lit face; the eye, ear and profile left clean
        front = ft['front']

        def prob(p):
            x, y = self.inv(p)
            if (x / 0.085) ** 2 + ((y + 0.01) / 0.14) ** 2 < 1:
                return 0.0
            if abs(x - ex) < 0.06 and abs(y - ey) < 0.04:
                return 0.0
            # the side plane of the face, behind the line from the brow's outer
            # corner down over the cheekbone to the angle of the jaw
            lim = 0.36 - 0.10 * max(0.0, y) / 0.4 + (0.05 if y < -0.05 else 0.0)
            if y > 0.30:
                lim = 0.30 + (y - 0.30) * 1.5          # the shadow under the jaw
            return keep_prob((x - 0.06) / max(0.05, lim - 0.06), 0.35, 1.0, 0.0)
        field(hd, self.P(ft['region']), math.degrees(self.tilt) + 70, 5.4, prob, ln=(7, 13), gap=(2, 3.5), bow=0.4)
        # a hollow under the cheekbone and the shadow under the lower lip
        hd.add(self.C([(ft['cheek'][0][0] - 0.03, 0.10), (ft['cheek'][0][0] - 0.06, 0.18), (ft['cheek'][0][0] - 0.07, 0.26)]),
               w=0.75, hand=0.2)
        mx, my = ft['mouth'][0]
        for k in range(3):
            hd.add(self.C([(mx - 0.025 - k * 0.018, my + 0.035), (mx - 0.032 - k * 0.018, my + 0.06)]), w=0.72, hand=0)
        if not self.female:
            # a short beard along the jaw that leaves the receding chin clear
            base = self.C(ft['beard'], 2.0)
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


def foot(F, name, ankle, z, scale=1.0, joins=(), shade=1.0):
    """A broad bare foot in profile, toes to the right, sole on the ground (y 860):
    heel and Achilles tendon, ankle bone, instep, separate toes, a nail on the big toe."""
    ax, ay = ankle
    S = lambda pts: [(ax + x * scale, ay + y * (0.4 + 0.6 * scale)) for x, y in pts]
    poly = closed(S([(-13, -4), (-17, 8), (-22, 20), (-20, 29), (-12, 33.5), (8, 34.5), (34, 34.5), (54, 33.5),
                     (60, 34.5), (64, 31.5), (67, 34.5), (72, 33.5), (75, 30.5), (79, 33), (84, 30), (84, 24),
                     (77, 20), (62, 17), (42, 9), (22, -1), (8, -6)]), step=1.2)
    p = F.part(name, poly, z, joins=joins)
    p.add(catmull(S([(64, 31), (61, 27), (57, 25)]), step=1.0), w=0.85)              # toe creases
    p.add(catmull(S([(75, 30), (72, 25), (68, 23)]), step=1.0), w=0.85)
    p.add(catmull(S([(76, 21), (80, 23), (83, 27)]), step=1.0), w=0.85)              # big toe nail
    p.add(catmull(S([(-2, 1), (5, 6), (12, 4)]), step=1.0), w=0.95)                 # ankle bone
    p.add(catmull(S([(-12, -2), (-14, 10), (-17, 20)]), step=1.0), w=0.8)           # Achilles tendon
    field(p, poly, -55, 5.6, lambda q: keep_prob((q[0] - (ax - 22 * scale)) / (90 * scale), 0.2, 0.55, 0.08 * shade)
          if q[1] < 858 else 0.0, ln=(5, 8))
    return p


# ------------------------------------------------------------------ figure A: standing man with a spear

def man():
    F = Figure('A.')
    head = Head(F, (302, 214), 110, 0.13, z=2.8)

    neck = F.part('neck', closed([(262, 222), (300, 246), (321, 262), (325, 282), (330, 302), (300, 314), (256, 300),
                                  (244, 270), (250, 240)]), 5, joins=('head', 'torso'))
    # the torso: a deep barrel chest, convex from the collarbone round to the belly
    torso = F.part('torso', closed([
        (250, 262), (232, 292), (222, 334), (222, 384), (232, 432), (240, 462), (236, 492), (230, 520),
        (240, 548), (262, 562), (300, 562), (328, 540), (344, 508), (352, 478), (361, 452), (369, 424),
        (373, 394), (371, 364), (361, 336), (345, 314), (326, 302), (306, 298)]), 8, joins=('neck', 'thighN', 'thighF'))

    # near arm: shoulder (288, 312), elbow (304, 432), wrist (384, 410); a short forearm
    ua = Limb([(287, 310), (292, 368), (304, 432)],
              wa=[(0, 25), (0.13, 32), (0.36, 25), (0.62, 29), (0.9, 23), (1, 21)],
              wb=[(0, 27), (0.2, 34), (0.45, 31), (0.8, 24), (1, 22)], cap0=0.7, cap1=0.4)
    uarm = F.part('uarm', ua.poly, 2, joins=('farm', 'elbow'))
    elbow = F.part('elbow', blob(306, 430, 23, 22), 1.9, joins=('uarm', 'farm'))
    fa = Limb([(302, 433), (345, 426), (390, 408)],
              wa=[(0, 24), (0.3, 27), (0.75, 19), (1, 15.5)],
              wb=[(0, 25), (0.25, 25), (0.75, 18), (1, 15.5)], cap0=0.5, cap1=0.3)
    farm = F.part('farm', fa.poly, 1.5, joins=('uarm', 'fist', 'elbow'))
    # the fist round the shaft: back of the hand, four fingers curled across the
    # front of the shaft, the thumb pressed over them; the shaft shows above and below
    G = lambda pts: [(410 + x * 1.12, 407 + y * 1.12) for x, y in pts]
    fist = F.part('fist', closed(G([(-24, -12), (-14, -17), (-2, -19.5), (8, -20.5), (16, -18.5), (20.5, -13.5),
                                    (19, -9.5), (21.5, -5), (21, 0.5), (19, 3), (21, 7), (19.5, 11), (17.5, 13),
                                    (18, 16), (14, 19.5), (2, 20.5), (-10, 18.5), (-22, 13)]), step=1.0), 0.5,
                  w=2.0, joins=('farm', 'thumb'))
    for y0, y1 in ((-9.5, -10.5), (3, 2), (13, 12.5)):
        fist.add(catmull(G([(19, y0), (10, y1), (1, y1 + 0.5)]), step=1.0), w=1.0)
    for y in (-14, -4, 7, 16):
        fist.add(catmull(G([(-4, y - 3), (-2, y), (-4, y + 3)]), step=1.0), w=0.8)       # finger roots
    thumb, _ = capsule(F, 'thumb', G([(-14, -15), (-2, -12), (10, -6)]), 5.0 * 1.12, 0.45, joins=('fist',), w=1.7)
    thumb.add(catmull(G([(5, -10), (9, -8), (10.5, -4)]), step=1.0), w=0.85)          # nail
    field(fist, fist.poly, 70, 5.5, lambda q: keep_prob((q[1] - 399) / 26, 0.0, 0.6, 0.0) if q[0] < 418 else 0.0,
          ln=(5, 8))

    # legs: the near one a step forward with the knee easy, the far one back and
    # straight under the weight; long heavy thighs, short shins, thick calves and ankles
    th = Limb([(290, 468), (310, 596), (336, 712)],
              wa=[(0, 52), (0.38, 57), (0.7, 44), (0.9, 30), (1, 28)],
              wb=[(0, 50), (0.3, 47), (0.75, 35), (1, 30)], cap0=0.5, cap1=0.6)
    thighN = F.part('thighN', th.poly, 6.2, joins=('torso', 'shinN', 'kneeN', 'patN'))
    sh = Limb([(336, 712), (334, 772), (326, 830)],
              wa=[(0, 28), (0.12, 24.5), (0.3, 26.5), (1, 19)],
              wb=[(0, 29), (0.28, 43), (0.6, 35), (1, 20)], cap0=0.6, cap1=0.5)
    shinN = F.part('shinN', sh.poly, 6.1, joins=('thighN', 'footN', 'kneeN', 'patN'))
    kneeN = F.part('kneeN', blob(331, 712, 28, 26), 6.05, joins=('thighN', 'shinN', 'patN'))
    patN = F.part('patN', blob(360, 707, 9.5, 13, 0.15), 6.04, joins=('thighN', 'shinN', 'kneeN'))
    footN = foot(F, 'footN', (326, 829), 6.0, joins=('shinN',))
    th2 = Limb([(278, 468), (270, 596), (260, 712)],
               wa=[(0, 48), (0.4, 45), (0.85, 33), (1, 29)],
               wb=[(0, 48), (0.3, 45), (0.8, 33), (1, 28)], cap0=0.5, cap1=0.6)
    thighF = F.part('thighF', th2.poly, 9.2, joins=('torso', 'shinF', 'kneeF'))
    sh2 = Limb([(260, 712), (250, 772), (236, 830)],
               wa=[(0, 27), (0.12, 24), (0.3, 25.5), (1, 18)],
               wb=[(0, 28), (0.28, 41), (0.6, 33), (1, 19)], cap0=0.6, cap1=0.5)
    shinF = F.part('shinF', sh2.poly, 9.1, joins=('thighF', 'footF', 'kneeF'))
    kneeF = F.part('kneeF', blob(258, 712, 27, 26), 9.05, joins=('thighF', 'shinF'))
    footF = foot(F, 'footF', (236, 829), 9.0, scale=0.97, joins=('shinF',), shade=4.0)

    # hide cape over the shoulders, open in front, hanging behind to the thighs
    back = rag([(324, 298), (306, 291), (284, 285), (264, 272), (248, 266), (230, 284), (213, 330), (203, 400),
                (195, 470), (187, 540), (181, 600), (177, 640)], 0.5, 14)
    hem = rag([(177, 640), (196, 652), (214, 646), (230, 662), (246, 652), (262, 648)], 1.5, 7)
    near = rag([(262, 648), (264, 590), (263, 520), (261, 450), (262, 392), (267, 342), (279, 312), (296, 301),
                (312, 300), (324, 298)], 0.4, 14)
    cape = F.part('cape', back + hem[1:] + near[1:-1], 3, w=2.0)
    # a short hide wrap round the hips: its top rolled down over a thong that is
    # knotted in front, the two ends hanging
    wtop = rag([(236, 446), (262, 443), (290, 446), (318, 441), (352, 442)], 1.0, 9)
    wfront = catmull([(352, 442), (356, 470), (358, 496), (357, 512)], step=2.0)
    whem = rag([(357, 512), (342, 526), (322, 532), (304, 528), (286, 538), (266, 534), (244, 530)], 1.6, 7)
    wback = catmull([(244, 530), (237, 500), (234, 474), (236, 446)], step=2.0)
    wrap = F.part('wrap', wtop + wfront[1:] + whem[1:] + wback[1:-1], 4.5, w=1.9)
    fold = rag([(236, 466), (254, 473), (272, 467), (292, 475), (312, 468), (330, 474)], 0.8, 8)
    wrap.add(fold, w=1.4)
    edge_shade(wrap, fold, -1, depth=7, every=5.0, ang=0.2)            # the roll's shadow on the wrap below
    for x0, x1 in ((246, 256), (282, 290), (318, 326)):                # the thong where the roll sags
        y0 = 470.5 + (x0 - 236) * 0.01
        wrap.add([(x0, y0), (x1, y0 + 0.5)], w=1.2, hand=0.1)
        wrap.add([(x0, y0 + 3.5), (x1, y0 + 4)], w=0.9, hand=0.1)
    knot = F.part('knot', blob(332, 469, 7, 4.6, -0.35), 4.3, w=1.4, joins=('knot2',))
    knot2 = F.part('knot2', blob(345, 470, 7, 4.6, 0.35), 4.25, w=1.4, joins=('knot',))
    knot.add([(338.5, 465), (338.5, 474)], w=1.0)
    for x0, L, sw in ((335, 38, -1), (342, 30, 1)):                     # the ends, as narrow thongs
        c = catmull([(x0, 474), (x0 + sw * 2, 474 + L * 0.5), (x0 + sw * 1 - 2, 474 + L)], step=1.5)
        nn = normals(c)
        for o in (-1.4, 1.4):
            knot.add([(p[0] + n[0] * o, p[1] + n[1] * o) for p, n in zip(c, nn)], w=0.95, clip=False, hand=0.1)
        knot.add([(c[-1][0] - 1.6, c[-1][1]), (c[-1][0] + 1.6, c[-1][1] + 0.5)], w=0.9, clip=False)

    # modelling: hatching on the side away from the fire
    skin(uarm, ua, 0.08, 1.0, 'b', depth=0.5, cross=0.45, ext=1.45)
    skin(farm, fa, 0.05, 0.95, 'b', depth=0.45, ang=-0.3, ext=1.5)
    uarm.add(catmull([(276, 326), (290, 318), (306, 320), (318, 330)], step=1.5), w=0.9)   # deltoid
    uarm.add(catmull([(318, 360), (322, 386), (320, 410)], step=1.5), w=0.8)              # biceps
    farm.add(catmull([(318, 420), (338, 414), (356, 410)], step=1.5), w=0.8)              # the forearm's muscle
    skin(thighN, th, 0.3, 0.97, 'b', depth=0.42, ext=1.4, ang=0.55)
    skin(shinN, sh, 0.06, 1.0, 'b', depth=0.45, ext=1.4, ang=0.45)
    skin(shinN, sh, 0.0, 0.3, 'b', depth=0.3, cross=1.0, ang=0.1)        # the hollow behind the knee
    edge_shade(thighN, whem, 1, depth=10, every=5.2)                       # under the wrap's hem
    kneeN.add(catmull([(346, 694), (352, 706), (348, 720)], step=1.0), w=0.85)          # the knee cap
    kneeN.add(catmull([(350, 726), (354, 738), (356, 752)], step=1.0), w=0.75)          # tendon below it
    skin(thighF, th2, 0.3, 1.0, 'b', depth=0.75, cross=0.35)
    skin(shinF, sh2, 0.0, 1.0, 'b', depth=0.75, cross=0.35)
    # torso: a shadow cast by the arm across the barrel chest, the chest's lower
    # edge where it turns under to the belly, the back in shadow at the cape's edge
    torso.add(catmull([(328, 306), (314, 303), (300, 305)], step=1.0), w=0.9)          # collarbone
    edge_shade(torso, ua.A, 1, depth=13, every=5.4, ang=-0.25)
    # the barrel turning away under the chest toward the belly
    edge_shade(torso, catmull([(340, 311), (356, 326), (367, 348), (372, 372), (372, 396), (366, 420), (358, 442),
                               (350, 456)], step=1.5), -1, depth=10, every=5.4, ang=0.15, keep=0.92)
    torso.add(catmull([(330, 330), (340, 352), (346, 372)], step=1.5), w=0.75)             # the chest's edge
    # neck: muscle from behind the ear to the notch, shadow under the jaw
    neck.add(catmull([(300, 240), (312, 272), (326, 298)], step=1.5), w=0.85)
    field(neck, neck.poly, 75, 5.4, lambda q: keep_prob((q[0] - 262) / 50, 0.3, 1.0, 0.0), ln=(7, 12), gap=(2, 3.5))
    # cape: hair of the hide in rows down the drape, dense at the back; fur at the hem
    eb = sub(back, 0.12, 1.0)
    en = sub(near[::-1], 0.08, 1.0)
    fur(cape, en, eb, [0.12, 0.30, 0.48], keep=0.45)
    fur(cape, en, eb, [0.62, 0.72, 0.80, 0.87, 0.94], keep=0.85)
    drape(cape, en, eb, [0.4, 0.68], w=1.0, piece=(40, 120), keep=0.7, t0=0.15)
    fur_edge(cape, hem, inward=1, ln=(5, 9))
    fur_edge(cape, sub(back, 0.25, 1.0), every=11, ln=(3, 6), inward=-1, keep=0.6)
    # wrap: hair of the hide hanging down, denser toward the back
    wl = catmull([(240, 482), (238, 505), (246, 528)], step=2.0)
    wr = catmull([(352, 480), (356, 500), (356, 512)], step=2.0)
    fur(wrap, wl, wr, [0.06, 0.18, 0.30], keep=0.85, piece=(5, 10))
    fur(wrap, wl, wr, [0.45, 0.62], keep=0.5, piece=(5, 10))
    fur_edge(wrap, whem, inward=1, ln=(5, 9))
    fur_edge(wrap, wtop, every=9, ln=(2, 4), inward=-1, keep=0.6)
    return F


def add_spear(F, grip):
    """The spear: a wooden shaft through the fist, a triangular Levallois point
    set in a lump of resin and bound with sinew."""
    phi = 0.012
    d = (math.sin(phi), math.cos(phi))
    top = (grip[0] - d[0] * (grip[1] - 106) / d[1], 106)
    n = (-d[1], d[0])
    S = lambda s, w: (top[0] + d[0] * s + n[0] * w, top[1] + d[1] * s + n[1] * w)
    length = (858 - 106) / d[1]
    shaft = F.part('shaft', [S(60, -4.6), S(length - 2, -4.8), S(length, 0), S(length - 2, 4.8), S(60, 4.6)], 0.8, w=1.7)
    edge_l = [S(0, 0)] + [S(s, -s * 0.255 + pen.g(0.4)) for s in (8, 16, 24, 32, 40)] + [S(47, -12)]
    edge_r = [S(47, 12)] + [S(s, s * 0.245 + pen.g(0.4)) for s in (40, 32, 24, 16, 8)]
    point = F.part('point', edge_l + [S(53, -10), S(53, 10)] + edge_r, 0.7, w=1.7)
    for s0, w0, sg in ((10, -2.5, 1), (22, -5.5, 1), (34, -8.5, 1), (16, 4, -1), (28, 7, -1), (40, 10, -1)):
        point.add(catmull([S(s0, w0), S(s0 + 5, w0 * 0.35), S(s0 + 11, w0 * 0.2 * sg)], step=1.0), w=0.8, hand=0)
    resin = F.part('resin', closed([S(46, -9), S(56, -10), S(72, -8.5), S(84, -5.5), S(86, 0), S(84, 5.5), S(72, 8.5),
                                    S(56, 10), S(46, 9)], step=1.0), 0.75, w=1.5)
    for k in range(8):
        s0 = 52 + k * 3.8
        resin.add([S(s0, -9.5), S(s0 + 5, 9.5)], w=0.95, hand=0)
    for k in range(3):
        s0 = 58 + k * 7
        resin.add([S(s0 + 5, -9), S(s0, 9)], w=0.8, hand=0)
    for s0, s1, w0 in ((120, 170, 1.5), (260, 300, -1.8), (470, 520, 1.2), (640, 690, -1.0)):
        shaft.add([S(s0, w0), S(s1, w0 * 0.8)], w=0.75)


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
              wa=[(0, 28), (0.12, 26), (0.55, 20), (1, 17)],
              wb=[(0, 28), (0.3, 37), (0.65, 29), (1, 17)], cap0=0.6, cap1=0.5)
    shinN = F.part('shinN', sh.poly, 6.2, joins=('footN', 'kneeN'))
    kneeN = F.part('kneeN', blob(300, 708, 26, 25), 6.0, joins=('thighN', 'shinN'))
    footN = foot(F, 'footN', (206, 826), 6.1, scale=0.95, joins=('shinN',))
    footF = foot(F, 'footF', (220, 822), 9.0, scale=0.93, shade=4.0)
    # hip wrap over the buttocks
    whem = rag([(240, 712), (222, 738), (190, 758), (160, 778), (130, 796), (106, 800)], 1.3, 7)
    wrap = F.part('wrap', [(104, 712), (170, 706), (240, 690)] + whem + [(96, 780), (96, 748)], 6.3, w=1.9)

    # near arm: elbow on the thigh, forearm across the knee, the core held in front
    ua = Limb([(234, 590), (258, 642), (278, 690)],
              wa=[(0, 25), (0.3, 27), (1, 21)], wb=[(0, 25), (0.4, 26), (1, 21)], cap0=0.8, cap1=0.5)
    uarm = F.part('uarm', ua.poly, 3.5, joins=('farm', 'elbow'))
    elbow = F.part('elbow', blob(279, 692, 20, 19), 1.6, joins=('uarm', 'farm'))
    fa = Limb([(279, 694), (316, 704), (350, 714)],
              wa=[(0, 21), (0.3, 22), (0.8, 15.5), (1, 14)],
              wb=[(0, 21), (0.3, 21), (0.8, 14.5), (1, 13.5)], cap0=0.5, cap1=0.3)
    farm = F.part('farm', fa.poly, 1.5, joins=('uarm', 'hand', 'elbow'))
    # the core hand: palm up under the core, two fingers curled up its front, the thumb on top
    hand = F.part('hand', closed([(344, 702), (358, 704), (374, 706), (390, 706), (402, 704), (409, 708), (411, 717),
                                  (405, 726), (391, 732), (372, 734), (356, 733), (345, 727)], step=1.0), 1.05, w=2.0,
                  joins=('farm', 'fing1', 'fing2'))
    hand.add(catmull([(352, 729), (370, 734), (388, 731)], step=1.0), w=0.75)
    fing1, _ = capsule(F, 'fing1', [(397, 727), (409, 717), (413, 700)], 5.2, 0.95, joins=('hand',), w=1.7)
    fing2, _ = capsule(F, 'fing2', [(388, 731), (402, 727), (409, 714)], 4.8, 0.97, joins=('hand',), w=1.6)
    fing1.add(catmull([(410, 703), (415, 706)], step=1.0), w=0.8)
    fing1.add(catmull([(404, 721), (409, 725)], step=1.0), w=0.75)
    thumb, _ = capsule(F, 'thumb', [(360, 707), (368, 697), (378, 690)], 5.3, 0.9, w=1.7, taper=0.8)
    thumb.add(catmull([(372, 690), (376, 694), (381, 692)], step=1.0), w=0.8)
    thumb.add(catmull([(363, 700), (366, 704)], step=1.0), w=0.75)
    edge_shade(hand, [(404, 708), (380, 707), (356, 705)], 1, depth=6, every=5.0, ang=0.2)   # under the core
    # the flint core: a lumpy nodule, its upper face knapped into flake scars
    # (facets between ridges, rippled round the points where they were struck),
    # the chalky cortex left on its underside
    cx, cy = 385, 690
    angs = (180, 218, 254, 290, 326, 0, 40, 90, 140)
    rim = [(cx + 27 * math.cos(math.radians(v)) * pen.r(0.94, 1.05), cy + 17 * math.sin(math.radians(v)) * pen.r(0.94, 1.05))
           for v in angs]
    core = F.part('core', chaikin(rim, 2), 1.0, w=1.9)
    tops = [(cx - 15, cy - 15), (cx - 2, cy - 17.5), (cx + 11, cy - 15.5), (cx + 22, cy - 9)]
    for (x0, y0) in tops[:3]:
        core.add(catmull([(x0 + 6, y0 - 1), (x0 + 6.5, y0 + 8), (x0 + 8.5, y0 + 18)], step=1.0), w=0.85, hand=0)   # ridge
    for (x0, y0), (x1, y1) in zip([(cx - 26, cy - 6)] + tops[:-1], tops):
        mx, my = (x0 + x1) / 2, min(y0, y1)
        for r in (4.5, 9.0):                                                   # ripples round the strike
            core.add(ellipse_pts(mx, my + 1, r * 0.9, r * 0.8, 0, 0.35, math.pi - 0.35, step=1.0), w=0.72, hand=0)
    field(core, core.poly, 15, 5.0, lambda q: 1.0 if q[1] > cy + 5 else 0.0, ln=(6, 10))
    for k in range(6):
        p = (cx + pen.r(-18, 16), cy + pen.r(2, 6))
        core.add(ellipse_pts(p[0], p[1], 0.7, 0.7, step=0.5), w=0.9, hand=0, lift=0)       # cortex
    # far arm: forearm raised from under the shawl, the hammerstone held in its
    # fist, the stone's striking end jutting out below the thumb toward the core
    fa2 = Limb([(268, 660), (302, 648), (334, 636)],
               wa=[(0, 20), (0.3, 21), (0.8, 14.5), (1, 13.5)],
               wb=[(0, 20), (0.3, 20), (0.8, 14), (1, 13)], cap0=0.5, cap1=0.3)
    farm2 = F.part('farm2', fa2.poly, 3.6, joins=('hand2',))
    hand2 = F.part('hand2', closed([(330, 626), (338, 618), (350, 613), (362, 614), (371, 620), (376, 630), (375, 641),
                                    (369, 650), (358, 655), (345, 653), (335, 646), (329, 637)], step=1.0), 2.9, w=2.0,
                   joins=('farm2',))
    for y0 in (623, 633, 643):                                                   # the curled fingers
        hand2.add(catmull([(374 - abs(y0 - 633) * 0.15, y0 - 1), (366, y0 + 0.5), (358, y0 + 1.5)], step=1.0), w=0.95)
    hand2.add(catmull([(352, 616), (348, 624), (350, 632)], step=1.0), w=0.75)    # knuckle
    sp_ = [(377 + 18 * math.cos(math.radians(v)) * pen.r(0.9, 1.05), 654 + 13.5 * math.sin(math.radians(v)) * pen.r(0.9, 1.05))
           for v in (0, 50, 100, 150, 200, 250, 300)]
    stone = F.part('stone', chaikin(sp_, 2), 2.95, w=1.9)
    field(stone, stone.poly, 20, 5.0, lambda q: keep_prob((664 - q[1]) / 12, 0.0, 1.0, 0.0), ln=(5, 9))
    stone.add(catmull([(380, 646), (388, 644), (394, 648)], step=1.0), w=0.8)
    thumb2, _ = capsule(F, 'thumb2', [(350, 618), (365, 622), (380, 634)], 4.6, 2.85, w=1.6, taper=0.85)
    thumb2.add(catmull([(375, 629), (380, 632), (381, 637)], step=1.0), w=0.8)
    field(hand2, hand2.poly, 65, 5.4, lambda q: keep_prob((q[0] - 330) / 30, 0.3, 1.0, 0.0), ln=(5, 9))
    # a flake flying from the strike
    fl = F.part('flake', [(414, 664), (430, 655), (434, 659), (418, 669)], 0.5, w=1.3)
    for k in range(2):
        fl.add([(400 - k * 4, 671 + k * 6), (408 - k * 4, 668 + k * 6)], w=0.8, clip=False)

    # hide shawl over the shoulders and back, the forearms coming out in front
    back = rag([(272, 580), (250, 566), (228, 556), (206, 556), (178, 574), (150, 606), (126, 650), (108, 700),
                (100, 728)], 0.5, 14)
    hem = rag([(100, 728), (130, 724), (165, 712), (200, 698), (235, 684), (262, 674), (286, 668)], 1.4, 7)
    front = rag([(286, 668), (291, 645), (289, 620), (283, 600), (277, 588), (272, 580)], 0.4, 12)
    shawl = F.part('shawl', back + hem[1:] + front[1:-1], 3.2, w=2.0)

    # modelling
    skin(thighN, th, 0.0, 0.92, 'b', depth=0.5, cross=0.4, ang=-0.3, ext=1.4)
    skin(shinN, sh, 0.06, 1.0, 'b', depth=0.5, ext=1.45)
    skin(shinN, sh, 0.0, 0.32, 'b', depth=0.3, cross=1.0, ang=0.1)
    kneeN.add(catmull([(316, 692), (324, 704), (322, 718)], step=1.0), w=0.9)
    skin(farm, fa, 0.05, 0.92, 'b', depth=0.5, ang=-0.3, ext=1.4)
    skin(farm2, fa2, 0.05, 0.95, 'b', depth=0.5, ang=-0.3, ext=1.4)
    skin(uarm, ua, 0.45, 1.0, 'b', depth=0.5, ext=1.4)
    edge_shade(thighN, fa.B, -1, depth=9, every=5.2, ang=0.3)        # the forearm's shadow on the knee
    neck.add(catmull([(250, 556), (262, 580), (272, 596)], step=1.5), w=0.85)
    field(neck, neck.poly, 70, 5.4, lambda q: keep_prob((q[1] - 566) / 36, 0.3, 1.0, 0.0), ln=(7, 12), gap=(2, 3.5))
    # shawl and wrap
    eb = sub(back, 0.15, 1.0)
    ef = sub(front[::-1], 0.05, 1.0)
    fur(shawl, ef, eb, [0.12, 0.28, 0.44], keep=0.45)
    fur(shawl, ef, eb, [0.58, 0.68, 0.77, 0.85, 0.92, 0.98], keep=0.85)
    drape(shawl, ef, eb, [0.36, 0.62], w=1.0, piece=(40, 120), keep=0.7, t0=0.1)
    fur_edge(shawl, hem, inward=1, ln=(5, 9))
    fur_edge(shawl, sub(back, 0.2, 1.0), every=11, ln=(3, 6), inward=-1, keep=0.6)
    w1 = catmull([(104, 716), (100, 760), (108, 798)], step=2.0)
    w2 = catmull([(236, 696), (226, 724), (210, 748)], step=2.0)
    fur(wrap, w1, w2, [0.08, 0.2, 0.32], keep=0.85)
    fur(wrap, w1, w2, [0.48, 0.66], keep=0.45)
    fur_edge(wrap, whem, inward=1, ln=(5, 9))
    return F


# ------------------------------------------------------------------ the hearth

def hearth(cx=510, cy=842):
    F = Figure('H.')
    # a ring of rough stones, the far ones smaller and behind the fire; the near
    # ones turn their shadowed faces to us
    angs = [200, 228, 256, 284, 312, 340, 10, 38, 66, 90, 114, 142, 170]
    for k, ang in enumerate(angs):
        a = math.radians(ang + pen.g(3))
        x, y = cx + 92 * math.cos(a), cy + 21 * math.sin(a)
        nearer = math.sin(a) > 0.15
        rx, ry = (pen.r(21, 26), pen.r(12, 15.5)) if nearer else (pen.r(15, 20), pen.r(9, 12))
        n = int(pen.r(5, 7.99))
        vs = []
        for i in range(n):
            t = math.pi + i * 2 * math.pi / n + pen.r(-0.3, 0.3)
            rr = pen.r(0.8, 1.12)
            vx, vy = math.cos(t) * rx * rr, math.sin(t) * ry * rr
            vs.append((x + vx, y - ry * 0.45 + min(vy, ry * 0.55)))
        poly = chaikin(vs, 1)
        z = (1.0 - 0.01 * math.sin(a)) if nearer else 6.0 + 0.01 * k
        st = F.part(f'stone{k}', poly, z, w=1.7)
        top = min(p[1] for p in poly)
        if nearer:
            field(st, poly, 25 + pen.g(10), 5.0, lambda q, top=top: 1.0 if q[1] > top + 6 else 0.0, ln=(6, 11))
            st.add([lerp(vs[0], vs[1], 0.3), (x + pen.g(3), top + 5)], w=0.8)
        else:
            field(st, poly, 30, 5.2, lambda q, x=x: 1.0 if q[0] < x - 4 else 0.0, ln=(5, 9))
    # fuel: two branches crossed in the hearth, their ends sticking out of the
    # fire, the inner parts charred
    for k, (p0, p1, w0, z) in enumerate((((392, 852), (612, 790), 7.5, 3.5), ((630, 852), (412, 794), 7.0, 3.6))):
        d = ((p1[0] - p0[0]) / dist(p0, p1), (p1[1] - p0[1]) / dist(p0, p1))
        n = (-d[1], d[0])
        side1 = [(p0[0] + n[0] * w0, p0[1] + n[1] * w0), (p1[0] + n[0] * w0 * 0.75, p1[1] + n[1] * w0 * 0.75)]
        side2 = [(p1[0] - n[0] * w0 * 0.75, p1[1] - n[1] * w0 * 0.75), (p0[0] - n[0] * w0, p0[1] - n[1] * w0)]
        cap1 = [(p1[0] + d[0] * 2.5, p1[1] + d[1] * 2.5)]
        poly = side1 + cap1 + side2
        stick = F.part(f'stick{k}', poly, z, w=1.6)
        stick.add(ellipse_pts(p0[0], p0[1], 2.5, w0 * 0.95, math.atan2(d[1], d[0]), step=1.0), w=1.1, clip=False)
        for s0, s1, o in ((0.04, 0.3, 0.35), (0.22, 0.5, -0.4), (0.7, 0.96, 0.25)):          # bark
            a, b = lerp(p0, p1, s0), lerp(p0, p1, s1)
            stick.add([(a[0] + n[0] * w0 * o, a[1] + n[1] * w0 * o), (b[0] + n[0] * w0 * o, b[1] + n[1] * w0 * o)], w=0.8)
        for s in [0.36 + 0.035 * j for j in range(14)]:                                     # char
            q = lerp(p0, p1, s)
            stick.add([(q[0] - n[0] * w0, q[1] - n[1] * w0), (q[0] + d[0] * 3 + n[0] * w0, q[1] + d[1] * 3 + n[1] * w0)],
                      w=0.8)
        kn = lerp(p0, p1, 0.12)                                                              # a twig stub
        stick.add([(kn[0] - n[0] * w0, kn[1] - n[1] * w0), (kn[0] - n[0] * (w0 + 8) + d[0] * 5, kn[1] - n[1] * (w0 + 8) + d[1] * 5)],
                  w=1.2, clip=False)

    def flame(bx, by, H, W, lean, z, name, sway=0.0, lick=0.0, ph=0.0):
        """A tongue of flame round a swaying spine, its sides rippling, a smaller
        tongue licking off one side, a nested inner tongue."""
        def spine(u):
            return (bx + lean * u * u + sway * math.sin(u * math.pi * 1.4 + ph) * u, by - H * u)

        def hw(u, side):
            w = W / 2 * (1 - u) ** 0.8 * (1 + 0.35 * math.sin(math.pi * u))
            w *= 1 + 0.08 * math.sin(u * 17 + ph + side * 2.1)
            if lick and side == (1 if lick > 0 else -1):
                w += abs(lick) * math.exp(-((u - 0.5) / 0.08) ** 2) - abs(lick) * 0.6 * math.exp(-((u - 0.64) / 0.05) ** 2)
            return max(0.0, w)

        def edge(side, f=1.0, u1=1.0):
            out = []
            for i in range(41):
                u = u1 * i / 40
                p, p2 = spine(u), spine(min(1.0, u + 0.01))
                d = (p2[0] - p[0], p2[1] - p[1])
                L = math.hypot(*d) or 1
                n = (-d[1] / L, d[0] / L)
                w = hw(u / u1, side) * f
                out.append((p[0] + n[0] * w * side, p[1] + n[1] * w * side))
            return out
        left, right = edge(1), edge(-1)
        pts = catmull(left + right[::-1][1:], step=1.5)
        p = F.part(name, pts, z, w=1.7, outline=[pts])
        for f, u1, wt in ((0.52, 0.66, 1.1), (0.26, 0.36, 0.9)):
            inner = edge(1, f, u1) + edge(-1, f, u1)[::-1][1:]
            p.add(catmull(inner, step=1.5), w=wt)
        field(p, pts, 88, 5.5, lambda q: keep_prob((by - q[1]) / (H * 0.3), 0.15, 1.0, 0.0), ln=(5, 9))
        return p

    flame(cx, cy - 8, 150, 62, -14, 2.0, 'flame0', sway=7, lick=9, ph=0.3)
    flame(cx - 36, cy - 6, 100, 42, -22, 2.2, 'flame1', sway=5, lick=-6, ph=2.0)
    flame(cx + 36, cy - 6, 116, 44, 16, 2.1, 'flame2', sway=-6, lick=7, ph=4.1)
    flame(cx - 64, cy - 3, 56, 26, -14, 2.3, 'flame3', sway=3, ph=1.0)
    flame(cx + 64, cy - 3, 64, 28, 12, 2.3, 'flame4', sway=-3, ph=5.0)
    for x, y in ((cx - 30, 640), (cx + 22, 622), (cx + 6, 600), (cx + 44, 652), (cx - 50, 668)):
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


# ------------------------------------------------------------------ the rock shelter

def shelter():
    """The lip of a rock overhang coming in from the corner over her, its face
    shaded toward the lip, strata and cracks fading out into the corner."""
    lip = rag([(556, 56), (586, 82), (618, 96), (650, 106), (668, 124), (700, 140), (730, 150), (752, 176),
               (790, 190), (828, 204), (850, 226), (884, 240), (914, 254), (934, 276), (958, 296)], 1.6, 9)
    face = rag([(574, 50), (604, 70), (640, 86), (672, 100), (710, 120), (740, 132), (768, 158), (806, 170),
                (846, 188), (870, 208), (904, 222), (934, 238), (962, 262)], 1.2, 9)
    pen.line(lip, w=2.3, lift=0.15)
    for seg in broken(face, (40, 120), (4, 10), 0.95):
        pen.line(seg, w=1.3)
    # the narrow face of the lip, in shadow
    for k in range(48):
        t = (k + 0.5) / 48
        a, b = at(lip, t), at(face, t)
        if dist(a, b) > 4:
            pen.line([lerp(a, b, 0.08), lerp(a, b, 0.92 - pen.r(0, 0.2))], w=0.75, hand=0.2, lift=0)
    # the rock above: strata following the lip, broken and fading into the corner
    region = face + [(980, 240), (982, 30), (580, 28)]
    lipr = resample(face, 6)

    def d_lip(q):
        return min(dist(q, p) for p in lipr)

    tone = Part('rock', closed(region, step=3.0), 0)
    tone.finish()
    field(tone, region, 32, 6.5, lambda q: keep_prob(d_lip(q) / 105, 0.12, 1.0, 0.0) * (0.0 if q[0] > 975 else 1.0),
          ln=(7, 14), gap=(3, 7), clip=False)
    for off, keep in ((26, 0.8), (58, 0.55), (96, 0.3)):
        st = [(x + off * 0.25, y - off) for x, y in face]
        st = [p for p in st if p[1] > 24 and p[0] < 970]
        for seg in broken(st, (20, 60), (8, 30), keep):
            tone.add(seg, w=1.0 if off < 60 else 0.85, clip=False)
    for x0 in (640, 742, 836, 912):                                           # cracks up from the lip
        p = at(face, (x0 - 574) / 390)
        pts = [p, (p[0] + pen.r(-4, 4), p[1] - pen.r(12, 18)), (p[0] + pen.r(-8, 8), p[1] - pen.r(28, 40))]
        tone.add(pts, w=1.1, clip=False, hand=0.6)
    for pts, w, clip, kw in tone.strokes:
        args = dict(hand=0.4, lift=0.05, piece=(40, 120))
        args.update(kw)
        pen.line(pts, w=max(0.72, w), occlude=False, **args)


shelter()

# smoke: wisps rising from the flames and drifting toward the overhang,
# spreading and twisting as they go
for k, (off, ph, top) in enumerate(((-1.6, 0.0, 0.86), (-0.5, 1.3, 1.0), (0.6, 2.4, 0.94), (1.6, 3.9, 0.8))):
    pts = []
    for i in range(90):
        u = i / 89
        y = 652 - u * 390
        x = 506 + u * u * 140 + off * (2 + 26 * u) + (3 + 15 * u) * math.sin(u * 9.5 + ph)
        pts.append((x, y))
    pts = sub(pts, 0.03 * k, top)
    for seg in broken(pts, (30, 80), (5, 12), 0.9):
        pen.line(seg, w=0.9 if abs(off) < 1 else 0.8, hand=0.3, lift=0, occlude=False)


# ground: cast shadows away from the fire, a few strokes of earth, flint flakes
def ground_hatch(x0, x1, y, rows, spacing=5.5):
    for k in range(rows):
        yy = y + k * spacing
        shrink = (x1 - x0) * (0.06 + 0.07 * k)
        a, b = x0 + shrink + pen.r(-6, 6), x1 - shrink * 0.6 + pen.r(-6, 6)
        if b - a > 8:
            pen.line([(a, yy), (b, yy)], w=0.8, hand=0.4, lift=0.15, piece=(15, 40))


ground_hatch(140, 370, 863, 4)
ground_hatch(620, 920, 863, 4)
for x0, x1, y in ((90, 160, 880), (380, 440, 872), (580, 640, 878), (420, 520, 900), (700, 800, 902),
                  (210, 300, 905), (880, 950, 884), (620, 680, 920)):
    pen.line([(x0, y), (x1, y)], w=0.9, hand=0.5, lift=0.3, piece=(12, 30))
for x, y, s, r in ((622, 870, 8, 0.3), (640, 882, 7, 1.4), (656, 871, 7, 2.2), (668, 888, 6, 0.9),
                   (608, 886, 6, 2.8), (684, 876, 5, 1.9)):
    n = 3 + int(pen.r(0, 2.99))
    pts = []
    for i in range(n):
        a = r + i * 2 * math.pi / n + pen.r(-0.4, 0.4)
        rr = s * pen.r(0.6, 1.2)
        pts.append((x + rr * math.cos(a), y + rr * 0.55 * math.sin(a)))
    pen.line(pts + [pts[0]], w=1.1, hand=0, lift=0)
    pen.line([pts[0], lerp(pts[1], pts[-1], 0.5)], w=0.75, hand=0, lift=0)

pen.save('../19-neanderthals.svg', mirror=True)
pen.report()
