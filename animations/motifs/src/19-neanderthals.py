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




# ------------------------------------------------------------------ bodies built in three dimensions
#
# Each figure is first a skeleton: joints placed in centimetres in the
# figure's own frame (u to its right, v up from the ground, w forward), with
# Neanderthal bone lengths. The view turns the figure toward us by a yaw and
# looks down on it a little (pitch), and projects it onto the page. The trunk
# is lofted through cross-sections (width and depth at each height), so its
# outline and its cross-contour hatching come from the solid; limbs are swept
# round the projected bones with muscle profiles in centimetres.

def vadd(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vsub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vmul(a, k):
    return tuple(x * k for x in a)


def vdot(a, b):
    return sum(x * y for x, y in zip(a, b))


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    L = vlen(a) or 1.0
    return vmul(a, 1.0 / L)


def vlerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def ik(S, H, a, b, pole):
    """Two bones of lengths a and b from S reaching for H: where the middle
    joint goes, bent toward the pole direction."""
    d = vsub(H, S)
    D = min(vlen(d), a + b - 0.05)
    dr = vnorm(d)
    x = (a * a - b * b + D * D) / (2 * D)
    h = math.sqrt(max(0.0, a * a - x * x))
    perp = vnorm(vsub(pole, vmul(dr, vdot(pole, dr))))
    return vadd(S, vadd(vmul(dr, x), vmul(perp, h)))


def reach(S, d, L):
    """The end of a bone of length L from S in direction d."""
    return vadd(S, vmul(vnorm(d), L))


class View:
    def __init__(self, ox, oy, s, yaw, pitch=0.12):
        self.ox, self.oy, self.s = ox, oy, s
        self.c, self.sn = math.cos(yaw), math.sin(yaw)
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)

    def D(self, p):
        """Depth in cm, larger is farther from us."""
        u, v, w = p
        return -w * self.sn + u * self.c

    def P(self, p):
        u, v, w = p
        x = w * self.c + u * self.sn
        d = -w * self.sn + u * self.c
        return (self.ox + self.s * x, self.oy - self.s * (v * self.cp + d * self.sp))

    def Ps(self, pts):
        return [self.P(p) for p in pts]

    def facing(self, n):
        """How much a surface normal faces us (positive: visible)."""
        u, v, w = n
        d = -w * self.sn + u * self.c
        return -(d * self.cp - v * self.sp)


def cr1(vals, t):
    """Catmull-Rom through evenly spaced values, t in 0..len-1."""
    n = len(vals)
    i = max(0, min(n - 2, int(t)))
    f = t - i
    p0, p1, p2, p3 = vals[max(0, i - 1)], vals[i], vals[i + 1], vals[min(n - 1, i + 2)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


class Trunk:
    """A trunk lofted through cross-sections. keys run from the bottom up:
    (h, a, bf, bb, ex) = height along the spine above its base, half-width,
    front and back half-depths, squareness (2 = ellipse, larger = boxier).
    The spine runs from base along the unit vector up (it may lean)."""

    def __init__(self, view, base, up, keys, step=0.7):
        self.view, self.base, self.up = view, base, vnorm(up)
        hs = [k[0] for k in keys]
        self.secs = []
        h = hs[0]
        while h <= hs[-1] + 1e-6:
            # index into the keys (they need not be evenly spaced)
            j = max(0, min(len(hs) - 2, max(i for i in range(len(hs) - 1) if hs[i] <= h + 1e-9)))
            t = j + (h - hs[j]) / (hs[j + 1] - hs[j])
            sec = [h] + [cr1([k[m] for k in keys], t) for m in range(1, 5)]
            self.secs.append(sec)
            h += step
        # frame: forward is w turned by the lean
        f = (0.0, 0.0, 1.0)
        self.fw = vnorm(vsub(f, vmul(self.up, vdot(f, self.up))))
        self.rt = (1.0, 0.0, 0.0)

    def centre(self, h):
        return vadd(self.base, vmul(self.up, h))

    def point(self, sec, phi):
        h, a, bf, bb, ex = sec
        s_, c_ = math.sin(phi), math.cos(phi)
        u = a * math.copysign(abs(s_) ** (2 / ex), s_)
        w = (bf if c_ >= 0 else bb) * math.copysign(abs(c_) ** (2 / ex), c_)
        return vadd(self.centre(h), vadd(vmul(self.rt, u), vmul(self.fw, w)))

    def normal(self, sec, phi):
        h, a, bf, bb, ex = sec
        b = bf if math.cos(phi) >= 0 else bb
        s_, c_ = math.sin(phi), math.cos(phi)
        # the gradient of |u/a|^ex + |w/b|^ex at the point
        nu = math.copysign(abs(s_) ** (2 - 2 / ex) if s_ else 0.0, s_) / a
        nw = math.copysign(abs(c_) ** (2 - 2 / ex) if c_ else 0.0, c_) / b
        return vnorm(vadd(vmul(self.rt, nu), vmul(self.fw, nw)))

    def ring(self, sec, n=120):
        return [(2 * math.pi * k / n) for k in range(n)]

    def silhouette(self):
        left, right = [], []
        P = self.view.P
        for sec in self.secs:
            pts = [P(self.point(sec, phi)) for phi in self.ring(sec)]
            left.append(min(pts, key=lambda q: q[0]))
            right.append(max(pts, key=lambda q: q[0]))
        return left, right

    def poly(self):
        left, right = self.silhouette()
        P = self.view.P
        bot = [P(self.point(self.secs[0], phi)) for phi in self.ring(self.secs[0], 60)]
        top = [P(self.point(self.secs[-1], phi)) for phi in self.ring(self.secs[-1], 60)]
        # the lower arc of the bottom ring, the upper arc of the top ring
        bot = sorted([q for q in bot if q[1] >= lerp(left[0], right[0], 0.5)[1] - 0.5], key=lambda q: q[0])
        top = sorted([q for q in top if q[1] <= lerp(left[-1], right[-1], 0.5)[1] + 0.5], key=lambda q: -q[0])
        return left[::-1] + bot + right + top

    def rows(self, part, light, spacing=6.0, thr=0.42, mid=0.62, ln=(10, 22), gap=(2, 4), w=0.72, h0=None, h1=None,
             keep=None):
        """Cross-contour hatching: the visible arc of every section a row apart,
        inked where it turns away from the light; every other row runs on into
        the half-tone."""
        view = self.view
        dh = spacing / (view.s * view.cp)
        h = (h0 if h0 is not None else self.secs[0][0]) + pen.r(0, dh)
        top = h1 if h1 is not None else self.secs[-1][0]
        k = 0
        hs = [s[0] for s in self.secs]
        while h < top:
            i = min(range(len(hs)), key=lambda j: abs(hs[j] - h))
            sec = self.secs[i]
            lim = thr if k % 2 else mid
            run, runs = [], []
            for phi in [2 * math.pi * m / 240 for m in range(240)]:
                n = self.normal(sec, phi)
                p3 = self.point(sec, phi)
                ok = view.facing(n) > 0.05 and vdot(n, light) < lim and (keep is None or keep(p3, n))
                if ok:
                    run.append(view.P(p3))
                elif run:
                    runs.append(run)
                    run = []
            if run:
                runs.append(run)
            for r in runs:
                if len(r) < 2:
                    continue
                r = sorted(r, key=lambda q: q[0])
                for seg in broken(r, ln, gap, 1.0):
                    part.add(seg, w=w * pen.r(0.92, 1.08), hand=0.1, lift=0)
            h += dh
            k += 1

    def at(self, h, phi):
        """The page point on the surface at height h along the spine and angle phi."""
        hs = [s[0] for s in self.secs]
        i = min(range(len(hs)), key=lambda j: abs(hs[j] - h))
        return self.view.P(self.point(self.secs[i], phi))

    def curve(self, pts):
        """A surface curve through (h, phi) pairs, on the page."""
        return catmull([self.at(h, phi) for h, phi in pts], step=1.5)


def limb(F, name, view, joints, wa, wb, z=None, cap0=0.6, cap1=0.6, w=2.2, joins=()):
    """A limb swept round projected bones; widths are in cm."""
    s = view.s
    pts = view.Ps(joints)
    L = Limb(pts, [(t, x * s) for t, x in wa], [(t, x * s) for t, x in wb], cap0, cap1)
    if z is None:
        z = sum(view.D(p) for p in joints) / len(joints)
    return F.part(name, L.poly, z, w=w, joins=joins), L


def joint_blob(F, name, view, p, r, z=None, joins=(), ry=None, rot=0.0):
    c = view.P(p)
    return F.part(name, blob(c[0], c[1], r * view.s, (ry or r) * view.s, rot), view.D(p) if z is None else z,
                  joins=joins)


# ------------------------------------------------------------------ the Neanderthal head
#
# Profiles in centimetres, ear canal at the origin, x forward, y down. A long
# low vault with an occipital bun behind; a low sloping forehead running into
# a heavy rounded brow ridge (its arch over the eye drawn as a separate heavy
# line, so the continuous double arch reads); a big projecting mid-face with a
# broad, tall nose; a long convex upper lip over the large front teeth; a
# receding chin with no chin point; a broad jaw. Head about 23.5 cm from crown
# to chin and 24 cm from occiput to nose tip.

PROF_M = [
    (-7.2, 5.0), (-8.6, 2.6), (-9.8, 0.6), (-10.6, -1.8), (-10.8, -3.6), (-10.2, -5.9), (-8.6, -8.1), (-6.1, -9.9),
    (-3.0, -10.9), (0.0, -11.2), (3.0, -10.8), (5.6, -9.6), (7.7, -7.9), (9.1, -6.3), (10.1, -5.1), (10.95, -4.3),
    (11.45, -3.45), (11.4, -2.6), (10.9, -2.05), (10.15, -1.75), (10.55, -0.9), (11.6, 0.5), (12.7, 1.8), (13.6, 2.9),
    (13.75, 3.65), (13.35, 4.3), (12.5, 4.6), (11.75, 4.75), (11.95, 5.6), (12.1, 6.5), (11.6, 7.25), (11.75, 7.85),
    (11.5, 8.7), (10.75, 9.5), (10.3, 10.4), (9.6, 11.4), (8.5, 12.3), (7.1, 12.8), (5.6, 12.85), (4.4, 12.9)]
PROF_F = [
    (-7.0, 4.8), (-8.4, 2.5), (-9.6, 0.5), (-10.2, -1.8), (-10.3, -3.6), (-9.7, -5.9), (-8.1, -8.1), (-5.8, -9.9),
    (-2.8, -10.95), (0.0, -11.25), (3.0, -10.85), (5.5, -9.7), (7.4, -8.1), (8.6, -6.6), (9.2, -5.4), (9.8, -4.6),
    (10.2, -3.7), (10.2, -2.9), (9.85, -2.3), (9.45, -2.0), (9.85, -1.0), (10.7, 0.5), (11.6, 1.8), (12.35, 2.8),
    (12.45, 3.5), (12.1, 4.05), (11.5, 4.3), (10.9, 4.45), (11.05, 5.35), (11.15, 6.2), (10.75, 6.95), (10.9, 7.5),
    (10.7, 8.25), (10.0, 9.0), (9.5, 9.9), (8.9, 10.9), (8.0, 11.7), (6.8, 12.15), (5.4, 12.3), (4.3, 12.4)]
JAW_M = [(4.4, 12.9), (2.8, 12.2), (1.3, 10.9), (0.4, 9.2), (-1.2, 6.2), (-4.0, 5.3), (-7.2, 5.0)]
JAW_F = [(4.3, 12.4), (2.8, 11.7), (1.4, 10.5), (0.5, 8.9), (-1.1, 6.0), (-3.9, 5.1), (-7.0, 4.8)]

FEAT = {
    'M': dict(
        brow=[(6.2, -1.4), (6.9, -2.3), (8.0, -2.9), (9.3, -3.0), (10.4, -2.6), (10.95, -2.2)],
        sulcus=[(6.9, -4.5), (8.2, -5.1), (9.5, -5.3)],
        eye=(8.75, -0.85), cheek=[(8.2, 1.0), (7.4, 2.4), (6.2, 3.8)],
        ala=[(11.4, 2.2), (10.75, 2.9), (10.6, 3.9), (11.1, 4.5), (11.85, 4.6)],
        nostril=[(12.8, 4.35), (12.2, 4.0), (11.5, 4.2)],
        fold=[(10.7, 4.1), (10.5, 5.2), (10.6, 6.2)],
        mouth=[(11.6, 7.25), (11.0, 7.38), (10.3, 7.5)],
        temple=[(1.8, -0.5), (3.8, -0.2), (5.8, 0.2)],
        hairline=(7.0, -8.6), front=10.4, beard=True),
    'F': dict(
        brow=[(6.2, -1.5), (6.8, -2.2), (7.7, -2.6), (8.7, -2.65), (9.5, -2.35), (9.9, -2.15)],
        sulcus=[(6.8, -4.2), (7.9, -4.6), (9.0, -4.7)],
        eye=(8.2, -0.95), cheek=[(7.9, 1.0), (7.1, 2.3), (6.0, 3.6)],
        ala=[(10.6, 2.3), (10.15, 2.85), (10.1, 3.65), (10.5, 4.15), (11.0, 4.3)],
        nostril=[(11.85, 4.05), (11.3, 3.8), (10.75, 3.95)],
        fold=[(10.15, 3.8), (9.9, 5.0), (9.95, 6.3), (10.2, 7.2)],
        mouth=[(10.75, 6.95), (10.2, 7.05), (9.6, 7.15)],
        temple=[(1.8, -0.5), (3.8, -0.2), (5.6, 0.2)],
        hairline=(6.8, -8.7), front=9.8, beard=False),
}


class Head:
    """A head in profile at the ear point on the page, s units per cm, turned
    by tilt (positive tips the face down)."""

    def __init__(self, F, ear, s, tilt, z, sex='M', hair=None):
        self.ear, self.s, self.tilt, self.sex = ear, s, tilt, sex
        self.ft = FEAT[sex]
        prof_ = PROF_M if sex == 'M' else PROF_F
        jaw = JAW_M if sex == 'M' else JAW_F
        ctrl = self.P(prof_)
        outline = catmull(ctrl, step=1.2)
        poly = outline + catmull(self.P(jaw), step=1.5)[1:-1]
        self.part = F.part('head', poly, z, w=2.2, outline=[outline], joins=('neck',))
        self.z = z
        self.F = F
        self.details()

    def P(self, pts):
        c, s_ = math.cos(self.tilt), math.sin(self.tilt)
        return [(self.ear[0] + (x * c - y * s_) * self.s, self.ear[1] + (x * s_ + y * c) * self.s) for x, y in pts]

    def p(self, x, y):
        return self.P([(x, y)])[0]

    def inv(self, q):
        c, s_ = math.cos(self.tilt), math.sin(self.tilt)
        dx, dy = (q[0] - self.ear[0]) / self.s, (q[1] - self.ear[1]) / self.s
        return (dx * c + dy * s_, -dx * s_ + dy * c)

    def C(self, pts, step=1.0):
        return catmull(self.P(pts), step=step)

    def details(self):
        hd, ft, s = self.part, self.ft, self.s
        # the brow ridge: the near arch over the eye as one heavy line running
        # forward into the bulge of the glabella, the hollow above it lighter
        hd.add(self.C(ft['brow']), w=2.0, hand=0.15)
        hd.add(self.C(ft['sulcus']), w=0.9, hand=0.2)
        bx = [p[0] for p in ft['brow']]
        for k in range(9):
            u = bx[1] + (bx[-2] - bx[1]) * (k + 0.5) / 9
            yb = -2.6 - 0.15 * math.sin(math.pi * (k + 0.5) / 9)
            hd.add(self.C([(u, yb + 0.25), (u - 0.1, yb + 0.6), (u - 0.25, yb + 0.95)]), w=0.72, hand=0.05)
        # the eye deep under it: crease, heavy upper lid, lower lid, iris
        ex, ey = ft['eye']
        hd.add(self.C([(ex - 0.95, ey - 0.55), (ex, ey - 0.9), (ex + 0.85, ey - 0.6)]), w=0.9, hand=0.05)
        hd.add(self.C([(ex - 1.05, ey - 0.05), (ex - 0.1, ey - 0.45), (ex + 0.8, ey - 0.1)]), w=1.6, hand=0.05)
        hd.add(self.C([(ex - 0.85, ey + 0.32), (ex, ey + 0.48), (ex + 0.7, ey + 0.2)]), w=0.85, hand=0.05)
        e = self.p(ex + 0.2, ey - 0.12)
        hd.add(blot_pts(e[0], e[1], 0.3 * s, w=1.3), w=1.3, clip=False, hand=0, lift=0, piece=(400, 800))
        hd.add(self.C([(ex - 0.5, ey + 1.05), (ex + 0.2, ey + 1.15), (ex + 0.9, ey + 0.9)]), w=0.75, hand=0.1)
        # the big nose: wing, nostril, the fold down past the mouth
        hd.add(self.C(ft['ala']), w=1.25, hand=0.1)
        hd.add(self.C(ft['nostril']), w=1.0, hand=0.1)
        hd.add(self.C(ft['fold']), w=0.85, hand=0.15)
        hd.add(self.C(ft['mouth']), w=1.2, hand=0.1)
        m0 = ft['mouth'][-1]
        hd.add(self.C([m0, (m0[0] - 0.25, m0[1] + 0.3)]), w=0.9, hand=0)
        hd.add(self.C(ft['cheek']), w=0.75, hand=0.15)
        # the jaw's edge against the neck, and the angle of the jaw
        jaw = JAW_M if self.sex == 'M' else JAW_F
        hd.add(self.C(jaw[:5]), w=1.3, hand=0.1)
        # the ear: rim, inner fold, the tragus and the lobe
        ec = self.p(-0.4, -0.6)
        rot = self.tilt - 0.25
        hd.add(ellipse_pts(ec[0], ec[1], 1.95 * s, 3.3 * s, rot, -2.4, 2.5, step=1.0), w=1.3, hand=0.1)
        hd.add(ellipse_pts(ec[0] - 0.15 * s, ec[1] + 0.1 * s, 1.15 * s, 2.3 * s, rot, -1.8, 1.9, step=1.0), w=0.9, hand=0.1)
        hd.add(self.C([(0.75, -0.6), (1.05, -0.1), (0.8, 0.45)]), w=0.9, hand=0.05)
        hd.add(self.C([(-0.9, 2.0), (-0.2, 2.75), (0.6, 2.5)]), w=0.85, hand=0.05)
        # modelling: the side plane of the face hatched from the ear forward to
        # the line from the brow's outer end over the cheek to the jaw's angle,
        # under the jaw, and in the hollow under the brow
        lite = 0.55 if self.sex == 'F' else 1.0

        def prob(q):
            x, y = self.inv(q)
            if ((x + 0.4) / 2.3) ** 2 + ((y + 0.6) / 3.7) ** 2 < 1:
                return 0.0
            if abs(x - ex) < 1.3 and abs(y - ey) < 0.8:
                return 0.0
            lim = 6.2 - 1.5 * max(0.0, y) / 9.0 + (0.8 if y < -0.5 else 0.0)
            if y > 9.0:
                lim = 5.0 + (y - 9.0) * 1.6
            return keep_prob((x - 0.6) / max(0.5, lim - 0.6), 0.35, 1.0, 0.0) * lite
        region = self.P([(0.4, -6.0), (5.6, -6.6), (7.0, -2.0), (8.6, 0.6), (9.6, 3.0), (10.4, 9.0), (8.8, 12.3),
                         (4.5, 12.8), (1.0, 10.8), (0.0, 6.0), (0.2, 0.0)])
        field(hd, region, math.degrees(self.tilt) + 72, 5.4, prob, ln=(8, 14), gap=(2, 3.5), bow=0.3)

    def hair_lines(self, outer, scalp, n, z_off=-0.3, w=0.85, edge_w=1.7, wave=0.32, tip=(0.7, 1.5), tuft=(2.0, 3.4)):
        """Hair as lines. The mass runs between the scalp line (hairline, round
        the ear, down the nape) and its outer edge, both drawn front to back.
        The outer edge is a run of overlapping tufts, each ending in a point
        that trails back; inside, wavy strands gathered in locks follow the fall."""
        F, s = self.F, self.s
        outer_c = catmull(self.P(outer), step=1.5)
        scalp_c = catmull(self.P(scalp), step=1.5)
        poly = outer_c + scalp_c[::-1][1:-1]
        hair = F.part('hair', poly, self.z + z_off, w=edge_w, outline=[])
        test = resample(poly + [poly[0]], 2.0)
        pts = resample(outer_c, 1.5)
        nrm = normals(pts)
        m = pts[len(pts) // 2]
        o = (m[0] + nrm[len(pts) // 2][0] * 4, m[1] + nrm[len(pts) // 2][1] * 4)
        sg = -1 if inside(o, test) else 1                        # the normal's sign that points out of the hair
        i = 0
        while i < len(pts) - 4:
            j = min(len(pts) - 1, i + max(4, int(pen.r(*tuft) * s / 1.5)))
            a_, b_ = pts[i], pts[j]
            nb = (nrm[j][0] * sg, nrm[j][1] * sg)
            d = unit(pts[max(0, j - 2)], b_)
            tl = pen.r(*tip) * s
            mid = pts[(i + j) // 2]
            nm = (nrm[(i + j) // 2][0] * sg, nrm[(i + j) // 2][1] * sg)
            bul = pen.r(0.15, 0.45) * s
            T = (b_[0] + nb[0] * tl * 0.55 + d[0] * tl, b_[1] + nb[1] * tl * 0.55 + d[1] * tl)
            if j >= len(pts) - 1:
                T = (b_[0] + d[0] * tl, b_[1] + d[1] * tl)
            curve = catmull([a_, (mid[0] + nm[0] * bul, mid[1] + nm[1] * bul), T], step=1.2)
            hair.add(curve, w=edge_w * pen.r(0.88, 1.05), clip=False, hand=0.15, lift=0, piece=(80, 160))
            i = max(i + 3, j - int(0.5 * s / 1.5))
        # strands in locks, waving a little, each lock with its own phase
        nl = max(3, n // 3)
        for k in range(nl):
            fr0 = 0.06 + 0.88 * (k + 0.5) / nl
            ph = pen.r(0, 6.3)
            lam = pen.r(3.5, 6.0) * s
            amp = wave * s * pen.r(0.6, 1.2)
            for dfr in (-0.022, 0.0, 0.024):
                fr = min(0.97, max(0.03, fr0 + dfr + pen.g(0.006)))
                c = flow(scalp_c, outer_c, fr)
                c = resample(sub(c, pen.r(0.0, 0.07), pen.r(0.88, 1.0)), 1.5)
                if len(c) < 4:
                    continue
                cn = normals(c)
                L = 0.0
                wv = []
                for q, (p_, nn) in enumerate(zip(c, cn)):
                    if q:
                        L += dist(c[q - 1], p_)
                    e = amp * math.sin(ph + 2 * math.pi * L / lam) * min(1.0, L / (2 * s))
                    wv.append((p_[0] + nn[0] * e, p_[1] + nn[1] * e))
                for seg in broken(wv, piece=(30, 90), gap=(3, 7), keep=0.96):
                    hair.add(seg, w=w * pen.r(0.9, 1.1), hand=0.15, lift=0, piece=(40, 100))
        return hair

    def beard(self, region, direction, spacing=0.62, ln=(1.0, 1.9), w=0.8, keep=None):
        """A sparse beard of short curling hairs inside a region (head cm),
        flowing by direction(x, y) -> angle in the head's frame."""
        xs = [p[0] for p in region]
        ys = [p[1] for p in region]
        reg = resample(region + [region[0]], 0.3)
        y = min(ys) + pen.r(0, spacing)
        row = 0
        while y < max(ys):
            x = min(xs) + (spacing * 0.5 if row % 2 else 0.0) + pen.r(0, 0.2)
            while x < max(xs):
                q = (x + pen.g(0.12), y + pen.g(0.12))
                if inside(q, reg) and (keep is None or pen.rng.random() < keep(*q)):
                    a = direction(*q) + pen.g(0.18)
                    L = pen.r(*ln)
                    cu = pen.g(0.35)
                    p1 = (q[0] + math.cos(a) * L * 0.5, q[1] + math.sin(a) * L * 0.5)
                    p2 = (q[0] + math.cos(a + cu) * L, q[1] + math.sin(a + cu) * L)
                    self.part.add(self.C([q, p1, p2], 0.8), w=w * pen.r(0.9, 1.1), clip=False, hand=0.1, lift=0)
                x += spacing
            y += spacing * 0.85
            row += 1


# ------------------------------------------------------------------ hands and feet, drawn in centimetres

DEG = math.pi / 180
SC = 4.375                          # units per centimetre: the man's 160 cm is 700 units


class Tpl:
    """A template drawn in centimetres: x along a direction on the page, y across it."""

    def __init__(self, o, ang, s=SC, flip=False):
        self.o, self.c, self.sn, self.s, self.f = o, math.cos(ang), math.sin(ang), s, (-1 if flip else 1)

    def __call__(self, pts):
        o, c, sn, s, f = self.o, self.c, self.sn, self.s, self.f
        return [(o[0] + s * (x * c - y * f * sn), o[1] + s * (x * sn + y * f * c)) for x, y in pts]

    def p(self, x, y):
        return self([(x, y)])[0]

    def C(self, pts, step=1.0):
        return catmull(self(pts), step=step)

    def inv(self, q):
        dx, dy = (q[0] - self.o[0]) / self.s, (q[1] - self.o[1]) / self.s
        return (dx * self.c + dy * self.sn, (-dx * self.sn + dy * self.c) * self.f)


def tube(F, name, T, pts, r, z, joins=(), w=1.5, cap0=1.0, cap1=1.0):
    """A finger or toe: a tube through points in template cm, r = [(t, radius in cm)]."""
    rr = [(t, x * T.s) for t, x in r]
    L = Limb(T(pts), rr, rr, cap0, cap1)
    return F.part(name, L.poly, z, w=w, joins=joins), L


def unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    L = math.hypot(*d) or 1.0
    return (d[0] / L, d[1] / L)


def nail(part, T, a, b, wd=0.55, back=1.6, w=0.85, side=0.0):
    """A nail on the last joint a->b of a finger or toe (template cm), seen from above."""
    d = unit(a, b)
    n = (-d[1], d[0])
    o = (n[0] * side, n[1] * side)
    B = (b[0] - d[0] * back + o[0], b[1] - d[1] * back + o[1])
    E = (b[0] - d[0] * 0.3 + o[0], b[1] - d[1] * 0.3 + o[1])
    pts = [(B[0] + n[0] * wd, B[1] + n[1] * wd), (E[0] + n[0] * wd * 0.85, E[1] + n[1] * wd * 0.85),
           (E[0] + d[0] * 0.2, E[1] + d[1] * 0.2), (E[0] - n[0] * wd * 0.85, E[1] - n[1] * wd * 0.85),
           (B[0] - n[0] * wd, B[1] - n[1] * wd)]
    part.add(T.C(pts, 0.8), w=w, hand=0.05)


def creases(part, T, p, d, r, k=2, w=0.75, gap=0.32):
    """Skin folds across a finger at a joint p (direction d along the finger)."""
    n = (-d[1], d[0])
    for j in range(k):
        o = (j - (k - 1) / 2) * gap
        c = (p[0] + d[0] * o, p[1] + d[1] * o)
        part.add(T.C([(c[0] + n[0] * r * 0.7, c[1] + n[1] * r * 0.7), (c[0] + d[0] * 0.15, c[1] + d[1] * 0.15),
                      (c[0] - n[0] * r * 0.7, c[1] - n[1] * r * 0.7)], 0.8), w=w, hand=0.05)


def shade_by(part, T, ang, fn, spacing=5.2, ln=(5, 9)):
    """Hatching over a part, kept by a function of the template coordinates."""
    field(part, part.poly, math.degrees(math.atan2(T.sn, T.c)) + ang, spacing, lambda q: fn(*T.inv(q)), ln=ln,
          gap=(2, 3.5), bow=0.3)


def hand_hang(F, tag, wrist, ang, z, s=SC, flip=False, joins=()):
    """A broad hand hanging relaxed, seen from the back and the thumb side: four
    loosely curled fingers with wide tips, a long strong thumb in front."""
    T = Tpl(wrist, ang, s, flip)
    back = F.part(tag, closed(T([(-0.8, -3.0), (3.4, -3.5), (7.2, -3.8), (8.9, -2.1), (9.5, 0.2), (9.2, 2.3),
                                 (7.6, 3.5), (4.6, 3.6), (1.6, 3.2), (-0.8, 3.0)]), step=1.0), z, w=1.9, joins=joins)
    fing = [((8.5, 2.3), (12.5, 3.0), (14.9, 4.2), (16.5, 5.5), 1.06),
            ((9.0, 0.2), (13.4, 0.7), (16.1, 2.1), (17.7, 3.7), 1.1),
            ((8.5, -1.8), (12.7, -1.6), (15.2, -0.4), (16.7, 1.1), 1.04),
            ((7.2, -3.3), (10.5, -3.4), (12.6, -2.6), (13.9, -1.5), 0.93)]
    names = []
    for i, (K, P, D, Tp, r) in enumerate(fing):
        nm = f'{tag}f{i}'
        names.append(nm)
        f, Lf = tube(F, nm, T, [K, P, D, Tp], [(0, r), (0.45, r * 0.95), (0.8, r * 0.93), (1, r * 1.0)],
                     z - 0.4 + 0.1 * i, joins=(tag,), w=1.5)
        creases(f, T, P, unit(K, P), r, k=2)
        creases(f, T, D, unit(P, D), r * 0.9, k=1)
        nail(f, T, D, Tp, wd=0.5 * r, back=1.5)
        shade_by(f, T, 70, lambda x, y: keep_prob((y + 3.8) / 7.0, 0.1, 0.55, 0.0))
    th, Lt = tube(F, f'{tag}th', T, [(1.0, 2.5), (4.8, 4.8), (7.8, 5.8), (10.3, 6.0)],
                  [(0, 1.75), (0.35, 1.38), (0.7, 1.26), (1, 1.28)], z - 0.5, joins=(tag,), w=1.6)
    creases(th, T, (7.8, 5.8), unit((4.8, 4.8), (7.8, 5.8)), 1.26, k=2)
    nail(th, T, (7.8, 5.8), (10.3, 6.0), wd=0.6, back=1.7, side=-0.35)
    back.joins |= {F.tag + n for n in names} | {F.tag + tag + 'th'}
    # the knuckles, the tendons fanning to them, the shadow toward the little finger
    for K in [f[0] for f in fing[:3]]:
        back.add(T.C([(K[0] - 1.0, K[1] - 0.9), (K[0] - 0.35, K[1]), (K[0] - 1.0, K[1] + 0.9)], 0.8), w=0.9, hand=0.05)
    for y0, y1 in ((0.9, 2.1), (-0.3, 0.1), (-1.6, -1.8)):
        for seg in broken(T.C([(0.6, y0 * 0.6), (4.0, (y0 + y1) / 2), (7.6, y1)]), (14, 24), (4, 6)):
            back.add(seg, w=0.72, hand=0.1)
    shade_by(back, T, 70, lambda x, y: keep_prob((y + 3.6) / 6.5, 0.2, 0.7, 0.0))
    return back


def fist_shaft(F, tag, c, z, s=SC, joins=()):
    """The right hand round an upright shaft, from the thumb side: four fingers
    curled across the front of the shaft one above another, their middle joints
    rounded at the left, the strong thumb wrapped over the index finger; the
    back of the hand behind the shaft, the wrist below at the left."""
    T = Tpl(c, 0, s)
    palm = F.part(tag, closed(T([(-3.4, 6.6), (-0.6, 7.4), (2.4, 6.4), (4.4, 4.3), (5.0, 1.0), (4.9, -2.2),
                                 (4.3, -4.6), (2.2, -5.5), (-1.4, -5.3), (-4.2, -4.3), (-4.7, -0.8), (-4.6, 3.2)]),
                                step=1.0), z, w=1.9, joins=joins)
    rolls = [(-3.3, 1.12), (-1.15, 1.12), (1.0, 1.08), (3.05, 0.98)]
    names = []
    for i, (y, r) in enumerate(rolls):
        nm = f'{tag}r{i}'
        names.append(nm)
        x0 = -3.6 + 0.25 * i
        f, Lf = tube(F, nm, T, [(4.0, y - 0.15), (0.6, y), (x0, y + 0.2)], [(0, r), (1, r * 1.02)], z - 0.2 - 0.05 * i,
                     w=1.5, cap0=0.3)
        # the middle joint's knuckle, the fingertip tucked in and its nail
        f.add(T.C([(x0 + 0.9, y - r * 0.8), (x0 + 0.4, y + 0.1), (x0 + 0.9, y + r * 0.85)], 0.8), w=0.85, hand=0.05)
        f.add(T.C([(2.0, y + r * 0.2), (2.9, y + 0.1 * r), (3.6, y + r * 0.45)], 0.8), w=0.8, hand=0.05)
    th, Lt = tube(F, f'{tag}th', T, [(-2.6, 6.2), (-4.2, 1.4), (-3.4, -3.0), (-0.6, -4.6), (2.0, -4.2)],
                  [(0, 1.7), (0.3, 1.45), (0.7, 1.3), (1, 1.32)], z - 0.5, joins=(tag,), w=1.6)
    nail(th, T, (-0.6, -4.6), (2.0, -4.2), wd=0.62, back=1.7)
    creases(th, T, (-3.4, -3.0), unit((-4.2, 1.4), (-3.4, -3.0)), 1.3, k=2)
    palm.joins |= {F.tag + tag + 'th'}
    for p in [palm] + [q for q in F.parts if q.name in {F.tag + n for n in names}]:
        shade_by(p, T, -70, lambda x, y: keep_prob((x + 1.0) / 6.0, 0.0, 0.5, 0.0) if y > -3.8 else 0.0)
    return palm


def hand_core(F, tag, wrist, ang, z, s=SC, flip=False, joins=(), thumb_behind=False):
    """A hand palm up on the knee holding the flint core: the core sits in the
    palm, the fingers curl up round its far end, the thumb's tip on its top."""
    T = Tpl(wrist, ang, s, flip)
    palm = F.part(tag, closed(T([(-0.6, -2.6), (3.0, -2.9), (6.5, -2.6), (9.4, -1.6), (10.3, 0.4), (9.4, 1.9),
                                 (5.5, 2.4), (2.0, 2.4), (-0.6, 2.4)]), step=1.0), z, w=1.9, joins=joins)
    names = []
    for i, (pts, r) in enumerate((([(9.0, -0.3), (12.0, -1.6), (12.9, -4.2), (12.0, -6.0)], 1.06),
                                  ([(9.3, 0.9), (12.6, 0.0), (13.9, -2.6), (13.3, -4.6)], 1.08),
                                  ([(9.0, 1.9), (12.0, 1.4), (13.4, -0.6), (13.2, -2.4)], 1.0))):
        nm = f'{tag}f{i}'
        names.append(nm)
        f, Lf = tube(F, nm, T, pts, [(0, r), (1, r * 1.04)], z - 0.1 + 0.15 * i, joins=(tag,), w=1.5)
        creases(f, T, pts[1], unit(pts[0], pts[1]), r, k=2)
        nail(f, T, pts[2], pts[3], wd=0.5, back=1.5, side=0.25)
    th, Lt = tube(F, f'{tag}th', T, [(1.0, -2.0), (4.2, -4.0), (6.4, -5.8), (8.4, -7.0)],
                  [(0, 1.75), (0.4, 1.38), (1, 1.28)], z + (0.5 if thumb_behind else -0.6), joins=(tag,), w=1.6)
    nail(th, T, (6.4, -5.8), (8.4, -7.0), wd=0.6, back=1.6, side=-0.3)
    creases(th, T, (6.4, -5.8), unit((4.2, -4.0), (6.4, -5.8)), 1.3, k=2)
    palm.joins |= {F.tag + n for n in names} | {F.tag + tag + 'th'}
    shade_by(palm, T, 60, lambda x, y: keep_prob((2.4 - y) / 4.5, 0.25, 0.8, 0.0))
    # the core: a flint nodule worked round its edge, flake scars on its face,
    # the striking platform on top, a remnant of white cortex at the back
    core_c = T([(4.2, -3.2), (4.0, -6.0), (5.6, -8.6), (8.6, -9.6), (11.4, -8.4), (12.6, -5.8), (11.8, -3.2),
                (8.0, -2.6)])
    core = F.part('core', chaikin(core_c, 2), z - 0.3, w=1.9)
    for pts in ([(5.6, -8.6), (7.4, -6.6), (7.6, -3.4)], [(8.6, -9.6), (9.2, -7.2), (11.8, -5.0)],
                [(7.4, -6.6), (9.2, -7.2)], [(4.2, -5.0), (5.8, -5.6), (7.4, -6.6)], [(9.2, -7.2), (9.4, -4.2), (11.6, -3.4)]):
        core.add(T.C(pts, 0.8), w=1.0, hand=0.05)
    for k in range(4):                                        # ripples in the flake scars
        t = 0.3 + 0.17 * k
        a, b = lerp((5.4, -4.4), (6.6, -7.6), t), lerp((8.2, -3.6), (8.4, -7.0), t)
        core.add(T.C([a, lerp(a, b, 0.5), b], 0.8), w=0.75, hand=0.15)
    for k in range(3):
        t = 0.25 + 0.22 * k
        a, b = lerp((9.8, -7.6), (12.0, -6.0), t), lerp((9.6, -5.0), (11.6, -3.8), t)
        core.add(T.C([a, b], 0.8), w=0.75, hand=0.15)
    shade_by(core, T, 35, lambda x, y: 1.0 if x < 6.0 or y > -4.2 else 0.0, spacing=5.0, ln=(4, 7))
    return palm, core, T


def fist_hammer(F, tag, wrist, ang, z, s=SC, flip=False, joins=()):
    """A fist round a hammerstone, seen from the thumb side: knuckles along the
    top, curled fingers below, the thumb pressed on the stone, and the round
    cobble standing out of the grip toward the core."""
    T = Tpl(wrist, ang, s, flip)
    palm = F.part(tag, closed(T([(-0.6, -2.9), (3.4, -3.3), (7.2, -3.4), (9.6, -2.6), (10.6, -0.4), (10.2, 2.2),
                                 (8.4, 3.6), (4.8, 3.6), (1.6, 3.2), (-0.6, 2.8)]), step=1.0), z, w=1.9, joins=joins)
    names = []
    for i, (y, r) in enumerate(((-1.9, 1.08), (0.2, 1.1), (2.2, 1.04))):
        nm = f'{tag}r{i}'
        names.append(nm)
        f, Lf = tube(F, nm, T, [(8.6, y - 0.3), (10.9, y + 0.4), (10.2, y + 2.4), (8.2, y + 2.6)],
                     [(0, r), (1, r * 1.03)], z - 0.15 - 0.05 * i, w=1.5, cap0=0.3)
        creases(f, T, (10.9, y + 0.4), unit((8.6, y - 0.3), (10.9, y + 0.4)), r, k=2)
    stone = F.part(tag + 'stone', blob(*T.p(10.0, 6.4), 4.0 * s, 3.1 * s, math.atan2(T.sn, T.c) * 1 + 0.5), z + 0.2,
                   w=1.9)
    th, Lt = tube(F, f'{tag}th', T, [(1.2, 2.6), (4.4, 4.4), (6.8, 5.6), (8.6, 6.4)],
                  [(0, 1.75), (0.4, 1.38), (1, 1.3)], z - 0.6, joins=(tag,), w=1.6)
    nail(th, T, (6.8, 5.6), (8.6, 6.4), wd=0.6, back=1.6, side=-0.3)
    palm.joins |= {F.tag + tag + 'th'}
    for K in ((8.6, -2.2), (9.0, 0.0), (8.8, 2.0)):
        palm.add(T.C([(K[0] - 1.0, K[1] - 0.9), (K[0] - 0.3, K[1]), (K[0] - 1.0, K[1] + 0.9)], 0.8), w=0.9, hand=0.05)
    shade_by(palm, T, 70, lambda x, y: keep_prob((3.6 - y) / 6.5, 0.15, 0.7, 0.0))
    # the cobble: smooth and round, a battered spot where it strikes
    sc = T.p(10.0, 6.4)
    shade_by(stone, T, 20, lambda x, y: 1.0 if y > 7.6 else 0.0, spacing=5.0, ln=(4, 7))
    for k in range(5):
        a = pen.r(0, 6.3)
        q = T.p(11.6 + 0.6 * math.cos(a), 9.0 + 0.5 * math.sin(a))
        stone.add([q, (q[0] + 1.2, q[1] + 0.8)], w=0.9, hand=0)
    return palm, stone, T


# feet: drawn in centimetres from the ankle joint, toes to the right, the ground 7.5 below
FOOT_LAT = [(1.8, -5.5), (4.6, -2.9), (8.4, -0.8), (12.2, 1.0), (15.6, 2.4), (18.4, 3.0), (20.3, 3.4), (21.5, 4.1),
            (22.2, 5.3), (22.1, 6.7), (21.4, 7.5), (20.6, 7.55), (20.15, 7.1), (19.6, 7.55), (18.6, 7.6), (18.15, 7.15),
            (17.6, 7.6), (16.6, 7.6), (16.15, 7.2), (15.6, 7.6), (14.7, 7.6), (14.3, 7.3), (13.9, 7.6),
            (8.0, 7.6), (3.0, 7.65), (-2.0, 7.5), (-4.2, 6.9), (-5.3, 5.4), (-5.6, 3.4), (-5.0, 1.0), (-4.0, -2.0),
            (-3.4, -5.5)]
FOOT_MED = [(1.8, -5.5), (4.8, -2.7), (8.8, -0.5), (12.6, 1.2), (15.6, 2.4), (17.8, 3.0), (19.6, 3.4), (20.9, 4.2),
            (21.6, 5.4), (21.4, 6.8), (20.4, 7.5), (18.0, 7.6), (12.0, 7.6), (6.0, 7.6), (1.0, 7.6), (-2.0, 7.6),
            (-4.4, 7.0), (-5.6, 5.2), (-5.6, 3.0), (-5.0, 0.6), (-4.0, -2.2), (-3.4, -5.5)]


def foot_lat(F, name, ankle, z, s=SC, kx=0.95, joins=(), shade=1.0):
    """A broad bare foot from the outer side, turned a little toward us: heel and
    Achilles tendon, the outer ankle bone, the instep, a row of five toes."""
    T = Tpl(ankle, 0, s)
    S = lambda pts: [(x * kx, y) for x, y in pts]
    p = F.part(name, closed(T(S(FOOT_LAT)), step=1.0), z, w=2.1, joins=joins)
    p.add(T.C(S([(-0.8, -1.8), (0.6, -2.0), (1.6, -0.6), (0.6, 0.8), (-0.6, 0.4)])), w=1.0, hand=0.05)  # ankle bone
    p.add(T.C(S([(-3.4, -5.0), (-4.0, -1.6), (-4.4, 1.6)])), w=0.85, hand=0.1)                          # Achilles
    p.add(T.C(S([(6.4, 7.2), (7.6, 6.4), (9.0, 6.7)])), w=0.85, hand=0.05)                               # 5th metatarsal
    tops = [(13.9, 15.6, 6.15), (15.6, 17.6, 5.75), (17.6, 19.6, 5.35), (19.6, 20.6, 4.9)]
    for x0, x1, yt in tops:                                                                             # the toes' tops
        p.add(T.C(S([(x0 - 0.1, 7.2), (x0 + 0.1, yt + 0.4), ((x0 + x1) / 2, yt), (x1 - 0.2, yt + 0.25)])), w=0.95,
              hand=0.05)
        p.add(T.C(S([((x0 + x1) / 2 - 0.5, yt + 0.35), ((x0 + x1) / 2 + 0.3, yt + 0.25),
                     ((x0 + x1) / 2 + 0.5, yt + 0.8)])), w=0.75, hand=0.05)                              # nails
    p.add(T.C(S([(20.2, 4.2), (21.1, 4.25), (21.4, 4.9)])), w=0.85, hand=0.05)                         # big toe nail
    for x0, y0, x1, y1 in ((3.8, -3.0, 15.0, 2.6), (4.6, -2.4, 18.6, 3.4)):                            # tendons
        for seg in broken(T.C(S([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 0.1), (x1, y1)])), (12, 22), (4, 7)):
            p.add(seg, w=0.72, hand=0.1)
    field(p, p.poly, -55, 5.4, lambda q: (1.0 if T.inv(q)[1] > 4.2 - 0.12 * T.inv(q)[0] else
                                            0.35 * shade if T.inv(q)[0] < -2.0 else 0.0), ln=(5, 8))
    return p


def foot_med(F, name, ankle, z, s=SC, kx=0.95, joins=(), shade=1.0):
    """A broad bare foot from the inner side, turned a little toward us: the
    heel, the inner ankle bone, the arch over the outer edge's shadow, the
    ball and the big toe, the lesser toes just showing beyond it."""
    T = Tpl(ankle, 0, s)
    S = lambda pts: [(x * kx, y) for x, y in pts]
    toes = F.part(name + 't', closed(T(S([(18.8, 3.4), (19.6, 2.7), (20.8, 2.8), (21.7, 3.5), (22.3, 4.6), (21.6, 5.6),
                                         (19.8, 5.2)])), step=1.0), z + 0.2, w=1.6)
    toes.add(T.C(S([(20.6, 2.8), (21.0, 3.6), (21.5, 4.6)])), w=0.8, hand=0.05)
    p = F.part(name, closed(T(S(FOOT_MED)), step=1.0), z, w=2.1, joins=joins)
    p.add(T.C(S([(-0.4, -2.6), (1.4, -2.9), (2.6, -1.2), (1.4, 0.4), (-0.2, -0.2)])), w=1.0, hand=0.05)  # ankle bone
    p.add(T.C(S([(-3.4, -5.0), (-4.0, -1.6), (-4.6, 1.8)])), w=0.85, hand=0.1)
    arch = T.C(S([(17.0, 7.3), (14.0, 6.5), (10.0, 6.0), (5.6, 6.2), (1.6, 7.0), (-0.6, 7.4)]))
    p.add(arch, w=1.1, hand=0.05)
    p.add(T.C(S([(15.6, 6.9), (16.6, 5.9), (17.8, 5.6)])), w=0.85, hand=0.05)                           # ball
    p.add(T.C(S([(17.8, 7.5), (18.2, 6.2), (19.0, 5.4)])), w=0.85, hand=0.05)                           # big toe joint
    p.add(T.C(S([(19.4, 3.9), (20.4, 3.95), (20.9, 4.6)])), w=0.85, hand=0.05)                         # nail
    for seg in broken(T.C(S([(4.4, -2.4), (11.0, 0.4), (17.0, 2.7)])), (12, 22), (4, 7)):
        p.add(seg, w=0.72, hand=0.1)
    edge_shade(p, arch, -1 if True else 1, depth=5, every=5.2, ang=0.1)
    field(p, p.poly, -55, 5.4, lambda q: 0.5 * shade if T.inv(q)[0] < -1.5 else 0.0, ln=(5, 8))
    return p


def foot_tuck(F, name, ankle, z, s=SC, k=0.93, joins=()):
    """The foot of a kneeling leg, seen from the outer side: up on its toes
    under the body, the heel raised, the toes bent forward flat on the ground."""
    T = Tpl(ankle, 0.0, s)
    S = lambda pts: [(x * k, y * k) for x, y in pts]
    g = 11.0 / k
    p = F.part(name, closed(T(S([(2.4, -3.0), (4.0, 0.5), (5.6, 4.0), (6.9, 7.2), (8.7, g - 1.9), (10.0, g - 0.9),
                                 (10.1, g - 0.1), (7.0, g), (3.6, g), (1.6, g - 0.8), (-0.6, g - 3.4), (-2.4, 4.4),
                                 (-3.8, 1.0), (-4.6, -1.8), (-4.2, -4.0), (-2.8, -5.4)])), step=1.0), z, w=2.0, joins=joins)
    p.add(T.C(S([(-0.9, -1.4), (0.6, -1.8), (1.5, -0.3), (0.4, 0.9), (-0.8, 0.3)])), w=0.95, hand=0.05)    # ankle bone
    p.add(T.C(S([(-2.8, -5.0), (-3.4, -2.0), (-3.6, 0.6)])), w=0.85, hand=0.1)                            # Achilles
    p.add(T.C(S([(3.4, g - 0.2), (4.6, g - 1.3), (6.6, g - 1.9), (8.6, g - 1.8)])), w=0.85, hand=0.05)      # toes' crease
    for x0 in (6.4, 7.6, 8.8):                                                                            # the toes
        p.add(T.C(S([(x0, g - 1.7), (x0 + 0.5, g - 0.9), (x0 + 0.4, g - 0.1)])), w=0.8, hand=0.05)
    p.add(T.C(S([(9.2, g - 1.7), (9.8, g - 1.3), (9.9, g - 0.7)])), w=0.8, hand=0.05)                     # nail
    field(p, p.poly, 60, 5.4, lambda q: 1.0 if T.inv(q)[0] < 0.6 + 0.25 * T.inv(q)[1] else 0.15, ln=(5, 8))
    return p


def ring_pts(c, a, bf, bb, ex, n=120, rt=(1.0, 0.0, 0.0), fw=(0.0, 0.0, 1.0), sag=None):
    """Points round a horizontal section (with its outward normals), phi from the back round by the left."""
    out = []
    for k in range(n):
        phi = 2 * math.pi * k / n - math.pi
        s_, c_ = math.sin(phi), math.cos(phi)
        b = bf if c_ >= 0 else bb
        u = a * math.copysign(abs(s_) ** (2 / ex), s_)
        w = b * math.copysign(abs(c_) ** (2 / ex), c_)
        nu = math.copysign(abs(s_) ** (2 - 2 / ex) if s_ else 0.0, s_) / a
        nw = math.copysign(abs(c_) ** (2 - 2 / ex) if c_ else 0.0, c_) / b
        p = vadd(c, vadd(vmul(rt, u), vmul(fw, w)))
        if sag:
            p = vadd(p, (0.0, -sag(phi), 0.0))
        out.append((phi, p, vnorm(vadd(vmul(rt, nu), vmul(fw, nw)))))
    return out


def near_arc(V, ring, extra=1):
    """The part of a ring that faces us, as page points from left to right."""
    vis = [V.facing(nn) > 0 for _, _, nn in ring]
    n = len(ring)
    i0 = next(i for i in range(n) if not vis[i] and vis[(i + 1) % n])
    idx = []
    for k in range(1 - extra, n):
        i = (i0 + k) % n
        if k > extra and not vis[i]:
            idx.append(i)
            break
        idx.append(i)
    arc = [V.P(ring[i][1]) for i in idx]
    return arc if arc[0][0] < arc[-1][0] else arc[::-1]


def ring_at(c, a, bf, bb, ex, phi, rt=(1.0, 0.0, 0.0), fw=(0.0, 0.0, 1.0), sag=None):
    s_, c_ = math.sin(phi), math.cos(phi)
    b = bf if c_ >= 0 else bb
    u = a * math.copysign(abs(s_) ** (2 / ex), s_)
    w = b * math.copysign(abs(c_) ** (2 / ex), c_)
    p = vadd(c, vadd(vmul(rt, u), vmul(fw, w)))
    return vadd(p, (0.0, -sag(phi), 0.0)) if sag else p


def lacing(part, a_pts, b_pts, w=1.0):
    """A thong laced across a slit: holes along each edge, the thong crossing between them."""
    for p in a_pts + b_pts:
        part.add(ellipse_pts(p[0], p[1], 1.2, 1.2, 0, step=0.7), w=0.8, clip=False, hand=0, lift=0)
    for i in range(len(a_pts) - 1):
        part.add([a_pts[i], b_pts[i + 1]], w=w, clip=False, hand=0.1)
        part.add([b_pts[i], a_pts[i + 1]], w=w * 0.9, clip=False, hand=0.1)


def thong_ends(part, p, ends, w=1.2):
    """A knot of thong at p with its ends hanging (offsets in page units)."""
    part.add(ellipse_pts(p[0], p[1], 3.2, 2.4, 0.3, step=0.8), w=1.3, clip=False, hand=0.05, lift=0)
    part.add([(p[0] - 2.0, p[1] - 1.2), (p[0] + 1.6, p[1] + 1.6)], w=0.85, clip=False, hand=0)
    for d in ends:
        pts = catmull([p, (p[0] + d[0] * 0.45 + 1.0, p[1] + d[1] * 0.5), (p[0] + d[0], p[1] + d[1])], step=1.0)
        part.add(pts, w=w, clip=False, hand=0.1)
        e = pts[-1]
        part.add([(e[0] - 1.2, e[1] + 0.6), (e[0] + 1.3, e[1] - 0.5)], w=0.85, clip=False, hand=0)



def frange(a, b, step):
    out, x = [], a
    while x <= b + 1e-9:
        out.append(x)
        x += step
    return out


def band_pt(V, c0, k0, c1, k1, f, phi, sag0=None, sag1=None, rt=(1.0, 0.0, 0.0), fw=(0.0, 0.0, 1.0)):
    """A point on a hide band between two rings, f of the way from the top ring down to the hem."""
    a = ring_at(c0, *k0, phi, rt=rt, fw=fw, sag=sag0)
    b = ring_at(c1, *k1, phi, rt=rt, fw=fw, sag=sag1)
    return V.P(vlerp(a, b, f))


def limb_lines(part, L, specs, w=0.85):
    """Anatomy lines on a limb, each a list of (t along, s across) points."""
    for pts in specs:
        part.add(catmull([L.pt(t, s) for t, s in pts], step=1.2), w=w, hand=0.1)


# ------------------------------------------------------------------ figure A: the man with the spear

def man(ox=236):
    F = Figure('A.')
    V = View(ox, 880, SC, 42 * DEG, 0.12)
    P = V.P
    Lt = vnorm((0.3, 0.1, 1.0))
    # the skeleton, in centimetres: 160 cm tall, short shins and forearms, the
    # weight on the near leg, the far foot a step forward under the spear
    hipN, hipF = (-9.0, 82.0, -1.0), (9.0, 82.0, 1.0)
    knN, knF = (-9.5, 40.5, -4.0), (10.5, 40.8, 8.0)
    anN, anF = (-9.5, 7.5, -8.0), (11.0, 7.5, 6.0)
    shN, shF = (-18.0, 127.0, -1.5), (18.0, 127.0, -1.5)
    elN, wrN = (-22.0, 97.0, -2.5), (-21.5, 74.5, 3.0)
    elF, wrF = (23.0, 99.5, 10.0), (17.5, 113.0, 28.5)

    # the trunk: a broad pelvis, little waist, a deep barrel of a chest, wide shoulders
    keys = [(0, 15.5, 8.5, 11, 2.4), (6, 18, 9.5, 12.5, 2.4), (12, 17.5, 10.5, 12, 2.3), (18, 16, 11.5, 10.5, 2.2),
            (23, 15.5, 11.5, 10, 2.2), (29, 16.5, 12.5, 10.5, 2.2), (36, 17.5, 13.5, 11, 2.2),
            (42, 18, 13.5, 11.5, 2.2), (48, 18.5, 12, 11, 2.3), (53, 19, 9.5, 10, 2.5), (56, 14.5, 7.5, 8, 2.3),
            (59, 8.5, 6, 6.5, 2.0)]
    Tr = Trunk(V, (0.0, 76.0, 0.0), (0.0, 1.0, 0.0), keys)
    torso = F.part('torso', Tr.poly(), 0, w=2.2, joins=('neck', 'thighN', 'thighF'))
    Tr.rows(torso, Lt, spacing=5.8, thr=0.36, mid=0.58, ln=(10, 22), gap=(2, 4), h0=14)
    # collarbones, the chest muscles' lower edges, nipples, the breastbone, the
    # rib arch and the belly's midline, the navel, the saw-toothed serratus
    for pts, wt in (([(54.6, 0.04), (55.0, -0.35), (54.4, -0.75), (53.5, -1.1), (52.8, -1.3)], 1.2),
                    ([(54.6, 0.04), (55.0, 0.35), (54.4, 0.75), (53.6, 1.05)], 1.05),
                    ([(45.5, -1.3), (41.8, -1.05), (39.6, -0.72), (39.3, -0.38), (40.6, -0.06)], 1.1),
                    ([(40.6, 0.06), (39.5, 0.38), (39.9, 0.72), (42.0, 1.0)], 1.0)):
        torso.add(Tr.curve(pts), w=wt, hand=0.1)
    for pec in ([(45.5, -1.3), (41.8, -1.05), (39.6, -0.72), (39.3, -0.38), (40.6, -0.06)],
                [(40.6, 0.06), (39.5, 0.38), (39.9, 0.72)]):
        edge_shade(torso, Tr.curve(pec), -1, depth=6.5, every=5.4, ang=0.15)
    for ph in (-0.6, 0.62):
        c = Tr.at(42.3, ph)
        torso.add(ellipse_pts(c[0], c[1], 2.0, 1.6, 0, step=0.7), w=0.85, hand=0, lift=0)
    for pts, wt in (([(53.5, 0.0), (47.0, 0.0), (42.0, 0.0)], 0.75), ([(37.0, -0.04), (33.5, -0.32), (30.0, -0.66), (27.6, -1.0)], 0.8),
                    ([(37.0, 0.04), (33.5, 0.32), (30.6, 0.6)], 0.75), ([(36.0, 0.0), (29.0, 0.0), (21.6, 0.0)], 0.72)):
        for seg in broken(Tr.curve(pts), (16, 40), (4, 8)):
            torso.add(seg, w=wt, hand=0.1)
    c = Tr.at(19.2, 0.0)
    torso.add(catmull([(c[0] - 3.2, c[1] - 1.0), (c[0], c[1] + 1.8), (c[0] + 3.0, c[1] - 0.8)], step=0.8), w=1.0, hand=0)
    for h in (36.8, 34.0, 31.2):
        torso.add(Tr.curve([(h + 0.7, -1.24), (h - 0.5, -1.02)]), w=0.85, hand=0.1)

    # arms: big deltoids, thick upper arms, short heavy forearms
    uaN, LuaN = limb(F, 'uarmN', V, [shN, vlerp(shN, elN, 0.5), elN],
                     [(0, 5.6), (0.14, 6.3), (0.42, 5.3), (0.62, 5.4), (0.86, 4.5), (1, 4.3)],
                     [(0, 5.8), (0.2, 6.3), (0.45, 5.8), (0.72, 4.9), (1, 4.6)], z=-15, cap0=0.75, cap1=0.5,
                     joins=('elbowN', 'farmN'))
    elbN = joint_blob(F, 'elbowN', V, vadd(elN, (0, 0, -0.6)), 4.5, z=-15.6, joins=('uarmN', 'farmN'))
    faN, LfaN = limb(F, 'farmN', V, [elN, vlerp(elN, wrN, 0.5), wrN],
                     [(0, 4.5), (0.22, 4.9), (0.6, 3.8), (1, 2.9)],
                     [(0, 4.4), (0.25, 4.5), (0.7, 3.3), (1, 2.8)], z=-16.5, cap0=0.5, cap1=0.3,
                     joins=('uarmN', 'elbowN', 'handN'))
    pw, pe = P(wrN), P(elN)
    hand_hang(F, 'handN', pw, math.atan2(pw[1] - pe[1], pw[0] - pe[0]) - 0.1, -18, flip=True, joins=('farmN',))
    skin(uaN, LuaN, 0.08, 1.0, 'b', depth=0.46, cross=0.4, ext=1.45)
    skin(faN, LfaN, 0.04, 0.96, 'b', depth=0.44, ext=1.45, ang=-0.25)
    limb_lines(uaN, LuaN, [[(0.04, 0.72), (0.24, 0.5), (0.47, 0.08)],          # the deltoid's front edge
                           [(0.1, -0.78), (0.3, -0.48), (0.47, -0.02)],          # and its back edge
                           [(0.52, -0.2), (0.74, -0.3), (0.94, -0.22)]], w=0.9)  # biceps from triceps
    limb_lines(faN, LfaN, [[(0.06, 0.35), (0.34, 0.18), (0.66, 0.02)],          # the long supinator
                           [(0.72, -0.5), (0.86, -0.4), (0.97, -0.5)]], w=0.85)  # the wrist bone
    elbN.add(catmull([LuaN.pt(0.97, -0.75), LfaN.pt(0.03, -0.9), LfaN.pt(0.1, -0.7)], step=1.0), w=0.9)
    edge_shade(torso, LuaN.A, 1, depth=7, every=5.6, ang=-0.2, keep=0.75)      # the arm's shadow on the chest

    uaF, LuaF = limb(F, 'uarmF', V, [shF, vlerp(shF, elF, 0.5), elF],
                     [(0, 5.6), (0.2, 6.0), (0.5, 5.4), (1, 4.4)],
                     [(0, 5.8), (0.2, 6.2), (0.5, 5.6), (1, 4.6)], z=12, cap0=0.75, cap1=0.5,
                     joins=('elbowF', 'farmF'))
    elbF = joint_blob(F, 'elbowF', V, elF, 4.4, z=10, joins=('uarmF', 'farmF'))
    pwF = P(wrF)
    gx, gy = pwF[0] + 1.6 * SC, pwF[1] - 6.8 * SC              # the shaft's axis at the middle of the fist
    faF, LfaF = limb(F, 'farmF', V, [elF, vlerp(elF, wrF, 0.5), wrF],
                     [(0, 4.4), (0.25, 4.6), (0.65, 3.7), (1, 3.0)],
                     [(0, 4.3), (0.25, 4.4), (0.7, 3.4), (1, 2.9)], z=2, cap0=0.5, cap1=0.5,
                     joins=('uarmF', 'elbowF', 'fistF'))
    fist_shaft(F, 'fistF', (gx, gy), -10, joins=('farmF',))
    skin(uaF, LuaF, 0.0, 1.0, 'b', depth=0.6, cross=0.4)
    skin(faF, LfaF, 0.0, 0.95, 'b', depth=0.5, ext=1.3)
    limb_lines(faF, LfaF, [[(0.08, 0.3), (0.4, 0.12), (0.75, 0.0)]], w=0.85)

    # legs: long heavy thighs, short shins with thick calves, broad knees and ankles
    thN, LthN = limb(F, 'thighN', V, [hipN, vlerp(hipN, knN, 0.5), knN],
                     [(0, 8.8), (0.3, 9.3), (0.65, 7.8), (0.9, 6.0), (1, 5.6)],
                     [(0, 8.6), (0.25, 8.3), (0.7, 6.6), (1, 5.8)], z=-5.5, cap0=0.5, cap1=0.6,
                     joins=('torso', 'kneeN', 'shinN', 'patN'))
    kneN = joint_blob(F, 'kneeN', V, knN, 5.9, z=-5.2, joins=('thighN', 'shinN', 'patN'), ry=5.6)
    patN = joint_blob(F, 'patN', V, vadd(knN, (-0.6, 1.0, 5.0)), 2.3, z=-5.7, joins=('thighN', 'shinN', 'kneeN'),
                      ry=3.0)
    shN_, LshN = limb(F, 'shinN', V, [knN, vlerp(knN, anN, 0.5), anN],
                      [(0, 5.4), (0.15, 5.0), (0.4, 4.7), (0.85, 3.4), (1, 3.3)],
                      [(0, 5.6), (0.25, 7.0), (0.5, 6.3), (0.85, 3.9), (1, 3.5)], z=-4.5, cap0=0.6, cap1=0.5,
                      joins=('kneeN', 'thighN', 'footN', 'patN'))
    foot_lat(F, 'footN', P(anN), -4.0, joins=('shinN',))
    thF, LthF = limb(F, 'thighF', V, [hipF, vlerp(hipF, knF, 0.5), knF],
                     [(0, 8.6), (0.3, 9.0), (0.65, 7.6), (0.9, 5.9), (1, 5.5)],
                     [(0, 8.4), (0.25, 8.1), (0.7, 6.5), (1, 5.7)], z=4.5, cap0=0.5, cap1=0.6,
                     joins=('torso', 'kneeF', 'shinF', 'patF'))
    kneF = joint_blob(F, 'kneeF', V, knF, 5.8, z=4.0, joins=('thighF', 'shinF', 'patF'), ry=5.5)
    patF = joint_blob(F, 'patF', V, vadd(knF, (-1.0, 1.0, 5.0)), 2.3, z=3.6, joins=('thighF', 'shinF', 'kneeF'),
                      ry=3.0)
    shF_, LshF = limb(F, 'shinF', V, [knF, vlerp(knF, anF, 0.5), anF],
                      [(0, 5.3), (0.15, 4.9), (0.4, 4.6), (0.85, 3.4), (1, 3.3)],
                      [(0, 5.5), (0.25, 6.9), (0.5, 6.2), (0.85, 3.9), (1, 3.5)], z=3.4, cap0=0.6, cap1=0.5,
                      joins=('kneeF', 'thighF', 'footF', 'patF'))
    foot_med(F, 'footF', P(anF), 3.2, joins=('shinF',))
    skin(thN, LthN, 0.3, 0.97, 'b', depth=0.4, ext=1.4, ang=0.5)
    skin(shN_, LshN, 0.06, 1.0, 'b', depth=0.44, ext=1.35, ang=0.4)
    skin(shN_, LshN, 0.0, 0.25, 'b', depth=0.3, cross=1.0, ang=0.1)
    skin(thF, LthF, 0.3, 1.0, 'b', depth=0.7, cross=0.35)
    skin(shF_, LshF, 0.0, 1.0, 'b', depth=0.7, cross=0.35)
    for L, part in ((LthN, thN), (LthF, thF)):
        limb_lines(part, L, [[(0.5, 0.15), (0.75, 0.05), (0.96, 0.2)]], w=0.85)              # the outer thigh muscle
    for L, part in ((LshN, shN_), (LshF, shF_)):
        limb_lines(part, L, [[(0.1, -0.25), (0.36, -0.12), (0.62, -0.35)],                    # the calf
                             [(0.05, 0.55), (0.14, 0.5), (0.24, 0.48)]], w=0.85)              # tendon below the kneecap

    # the head, turned to the fire; the short thick neck
    ear = P((0.0, 148.8, -1.5))
    head = Head(F, ear, SC, 0.06, -25, sex='M')
    hp = head.p
    neck = F.part('neck', closed([hp(4.2, 12.4), hp(1.6, 10.8), hp(-0.4, 7.8), hp(-3.4, 5.8), hp(-7.0, 5.0),
                                  hp(-8.8, 3.0), P((0.0, 133.0, -7.5)), P((-5.0, 129.0, -3.0)), P((-3.0, 128.5, 4.0)),
                                  P((0.0, 129.5, 7.5)), P((1.0, 131.0, 8.0))]), -1, w=2.2, joins=('head', 'torso'))
    neck.add(catmull([hp(-1.8, 3.4), hp(0.6, 8.0), P((-1.0, 133.0, 6.0)), P((0.0, 131.0, 8.0))], step=1.2), w=0.9)
    field(neck, neck.poly, 75, 5.4, lambda q: keep_prob((q[0] - hp(-6, 4)[0]) / (hp(4, 12)[0] - hp(-6, 4)[0]),
                                                           0.3, 0.9, 0.0), ln=(7, 12), gap=(2, 3.5))
    head.hair_lines([(7.6, -8.4), (6.0, -10.6), (3.0, -12.4), (-0.8, -13.1), (-4.8, -12.6), (-8.4, -11.0),
                     (-11.3, -8.2), (-12.7, -4.6), (-12.9, -0.8), (-12.3, 3.0), (-11.2, 6.6), (-10.2, 9.6)],
                    [(7.6, -8.4), (6.6, -7.4), (5.0, -6.6), (3.4, -5.6), (2.6, -4.4), (1.2, -4.9), (-0.6, -5.1),
                     (-2.5, -3.8), (-3.4, -1.4), (-3.6, 1.6), (-4.8, 4.6), (-6.8, 7.2), (-10.2, 9.6)], 33)
    head.beard([(2.7, -2.2), (3.6, 0.6), (5.2, 2.6), (6.6, 4.8), (7.8, 7.6), (8.4, 9.4), (7.8, 11.6), (6.6, 13.4),
                (4.6, 13.8), (2.2, 12.8), (0.6, 10.6), (0.2, 8.0), (1.6, 3.0), (2.0, 0.0)],
               lambda x, y: math.pi / 2 - 0.4 * max(0.0, min(1.0, (x - 2.0) / 5.0)), spacing=0.7)
    head.beard([(10.0, 4.9), (11.2, 5.2), (11.0, 6.4), (10.4, 7.2), (9.7, 6.8)], lambda x, y: math.pi / 2 + 0.5,
               spacing=0.55, ln=(0.8, 1.3))

    # the hide wrap round the hips: lapped at the front of the near side, laced
    # through holes in both edges and knotted at the top, the top turned over
    K0, C0 = (17.9, 12.6, 12.4, 2.3), (0.0, 91.0, 0.3)
    K1, C1 = (20.5, 14.8, 14.6, 2.2), (0.0, 63.5, 0.6)
    sag_t = lambda ph: 1.0 * math.cos(ph) + 0.4 * math.sin(3 * ph)
    sag_h = lambda ph: (1.6 * math.cos(2 * ph) + 0.7 * math.sin(5 * ph + 1) - 5.5 * math.exp(-((ph + 0.6) / 0.2) ** 2)
                        + 2.0 * math.exp(-((ph - 0.1) / 0.4) ** 2))
    WP = lambda f, ph: band_pt(V, C0, K0, C1, K1, f, ph, sag_t, sag_h)
    wtop = near_arc(V, ring_pts(C0, *K0, sag=sag_t))
    whem = rag(near_arc(V, ring_pts(C1, *K1, sag=sag_h))[::-1], 0.9, 7)
    wrap = F.part('wrap', resample(wtop, 2.0) + whem[1:-1], -11, w=2.0)
    roll = catmull([WP(0.075, ph) for ph in frange(-2.35, 0.7, 0.12)], step=1.5)
    wrap.add(roll, w=1.15, hand=0.15)
    edge_shade(wrap, roll, -1, depth=5, every=5.2, ang=0.1)
    lap = catmull([WP(f, -0.5 - 0.14 * f) for f in (0.07, 0.3, 0.55, 0.8, 1.0)], step=1.5)
    wrap.add(lap, w=1.6, hand=0.1)
    edge_shade(wrap, lap, 1, depth=5, every=5.0, ang=0.0)
    lacing(wrap, [WP(f, -0.47 - 0.14 * f) for f in (0.22, 0.44, 0.66)], [WP(f, -0.64 - 0.14 * f) for f in (0.22, 0.44, 0.66)])
    thong_ends(wrap, WP(0.1, -0.55), [(6, 26), (-2, 21)])
    for ph0, f0, f1 in ((-1.6, 0.12, 0.9), (-1.25, 0.16, 0.95), (-0.9, 0.2, 0.85), (-0.2, 0.14, 0.9), (0.08, 0.2, 0.96),
                        (0.36, 0.12, 0.8)):
        c = catmull([WP(f, ph0 + 0.07 * math.sin(f * 5 + ph0 * 3)) for f in (f0, (f0 + f1) / 2, f1)], step=1.5)
        for seg in broken(c, (24, 60), (5, 10), 0.9):
            wrap.add(seg, w=0.95)
    xs = [q[0] for q in wrap.poly]
    x0, x1 = min(xs), max(xs)
    field(wrap, wrap.poly, 62, 5.6, lambda q: keep_prob((q[0] - x0) / (x1 - x0), 0.12, 0.5, 0.0), ln=(7, 13))
    fur_edge(wrap, whem, every=6.5, ln=(4, 8), inward=1, keep=0.75)

    # the cape: a hide thrown back over the shoulders, tied at the throat,
    # hanging behind to the knees
    tie = P((0.0, 131.6, 10.0))
    frontN = [P((-6.0, 133.2, 7.8)), P((-12.0, 133.6, 4.2)), P((-17.5, 132.6, -0.8)), P((-22.0, 129.8, -5.2))]
    backN = rag([P((-22.0, 129.8, -5.2)), P((-24.6, 120.0, -9.0)), P((-25.2, 105.0, -11.5)), P((-25.0, 90.0, -14.0)),
                 P((-24.6, 75.0, -16.5)), P((-24.4, 62.0, -19.5)), P((-24.0, 50.0, -22.5))], 0.6, 12)
    hemC = rag([P((-24.0, 50.0, -22.5)), P((-16.0, 48.5, -25.5)), P((-6.0, 47.6, -26.5)), P((4.0, 48.5, -26.0)),
                P((14.0, 49.5, -23.5)), P((21.0, 51.0, -19.5))], 1.4, 7)
    farC = [P((24.0, 75.0, -14.0)), P((24.5, 105.0, -10.0)), P((23.5, 125.0, -6.0)), P((19.5, 132.6, -1.5)),
            P((12.0, 134.2, 3.2)), P((6.0, 133.4, 7.6))]
    cape = F.part('cape', [tie] + catmull(frontN, step=2.0) + backN[1:] + hemC[1:] + catmull(farC, step=2.0), 20, w=2.0)
    field(cape, cape.poly, 72, 5.6, lambda q: 0.85, ln=(9, 16))
    for u0 in (-23.0, -19.0, -13.0, -6.0):
        c = catmull([P((u0 * 0.95, 118.0, -10.5)), P((u0, 90.0, -14.5)), P((u0 * 1.02, 62.0, -20.0)),
                     P((u0 * 1.04, 50.0, -23.5))], step=1.5)
        for seg in broken(c, (40, 110), (6, 12), 0.9):
            cape.add(seg, w=1.0)
    fur_edge(cape, hemC, every=6.5, ln=(4, 8), inward=1, keep=0.75)
    fur_edge(cape, sub(backN, 0.3, 1.0), every=10, ln=(3, 6), inward=1, keep=0.6)
    collar = F.part('collar', closed([tie] + frontN + [P((-24.6, 124.5, -9.0)), P((-23.6, 120.5, -11.5)),
                                                       P((-18.5, 133.5, -11.0)), P((-10.0, 137.6, -10.0)),
                                                       P((-3.0, 139.2, -8.5)), P((0.0, 137.5, 0.0))], step=1.5),
                    -16.5, w=2.0, joins=('cape', 'collarF'))
    collarF = F.part('collarF', closed([tie, P((6.0, 133.4, 7.6)), P((12.0, 134.2, 3.2)), P((19.5, 132.6, -1.5)),
                                        P((22.5, 129.5, -5.5)), P((17.0, 136.5, -9.5)), P((7.0, 139.2, -8.5)),
                                        P((0.0, 137.5, 0.0))], step=1.5), -0.5, w=2.0, joins=('cape', 'collar'))
    fe = catmull(frontN, step=1.5)
    fur_edge(collar, fe, every=6.0, ln=(3, 6), inward=-1, keep=0.7)
    collar.add(offset_line(fe, 4.0), w=1.0, hand=0.1)                       # the edge's thickness
    field(collar, collar.poly, 70, 5.6, lambda q: keep_prob((q[0] - fe[-1][0]) / (tie[0] - fe[-1][0]), 0.2, 0.8, 0.1),
          ln=(7, 12))
    lacing(collar, [P((-3.4, 131.9, 9.4)), P((-3.8, 130.2, 9.6))], [P((3.4, 131.9, 9.4)), P((3.8, 130.2, 9.6))], w=1.1)
    thong_ends(collar, P((0.0, 129.4, 10.8)), [(4, 26), (-3, 21)])
    return F, V, Tr, head, (gx, gy)


def offset_line(pts, d):
    """A curve run parallel to pts, d units to its left."""
    pts = resample(pts, 2.0)
    nrm = normals(pts)
    return catmull([(p[0] + n[0] * d, p[1] + n[1] * d) for p, n in zip(pts, nrm)][1:-1], step=1.5)


def band_poly(V, rings):
    """The outline of a hide band lofted through rings (top first): the top
    ring's near arc, the rings' extremes down each side, the hem's near arc."""
    proj = [[V.P(p) for _, p, _ in r] for r in rings]
    left = [min(pp, key=lambda q: q[0]) for pp in proj[1:-1]]
    right = [max(pp, key=lambda q: q[0]) for pp in proj[1:-1]]
    top = near_arc(V, rings[0])
    hem = near_arc(V, rings[-1])
    return top, hem, top + right + hem[::-1] + left[::-1]


# ------------------------------------------------------------------ figure B: the woman knapping

def woman(cx=830):
    F = Figure('B.')
    V = View(0, 880, SC, 30 * DEG, 0.12)            # built facing right, then turned to face the fire
    P = V.P
    Lt = vnorm((0.2, 0.15, 1.0))
    lean = 18 * DEG
    up = (0.0, math.cos(lean), math.sin(lean))
    base = (0.0, 28.5, -1.0)
    keys = [(0, 16.5, 9, 12.5, 2.4), (5, 17.5, 9.5, 13, 2.4), (10, 16, 10, 11, 2.3), (16, 13.8, 9.5, 9.5, 2.2),
            (22, 14, 10, 9.5, 2.2), (28, 15.5, 11.5, 10, 2.2), (34, 16.5, 12, 10.5, 2.2), (40, 17, 10.5, 10, 2.3),
            (44, 17, 8, 9, 2.5), (47, 13, 6.5, 7, 2.3), (50, 8, 5.5, 6, 2.0)]
    Tr = Trunk(V, base, up, keys)
    rt, fw = (1.0, 0.0, 0.0), Tr.fw

    def T3(h, u=0.0, f=0.0):
        return vadd(vadd(base, vmul(up, h)), vadd((u, 0.0, 0.0), vmul(fw, f)))

    # kneeling on the near knee and sitting back toward that heel, the far
    # knee up; the core held on the far knee, the hammerstone raised over it
    hipN, hipF = (-9.0, 32.5, 0.5), (9.0, 32.5, 0.5)
    knN, anN = (-10.0, 5.5, 29.5), (-10.0, 11.0, -0.5)
    knF, anF = (10.0, 38.5, 39.5), (10.0, 7.5, 40.5)
    shN, shF = T3(44, -16), T3(44, 16)
    elF, wrF = (19.0, 44.0, 21.0), (11.0, 48.5, 40.5)
    wrN = (-2.0, 66.0, 41.0)
    elN = ik(shN, wrN, 28.0, 21.0, (-1.0, -0.3, 0.0))

    torso = F.part('torso', Tr.poly(), 0, w=2.2, joins=('neck', 'thighN', 'thighF'))
    Tr.rows(torso, Lt, spacing=5.8, thr=0.36, mid=0.58, ln=(10, 20), gap=(2, 4), h0=8, h1=34)

    thN, LthN = limb(F, 'thighN', V, [hipN, vlerp(hipN, knN, 0.5), knN],
                     [(0, 8.4), (0.3, 8.6), (0.7, 7.0), (1, 5.4)],
                     [(0, 8.6), (0.3, 8.2), (0.7, 6.4), (1, 5.4)], z=-15, cap0=0.5, cap1=0.6,
                     joins=('torso', 'kneeN', 'shinN'))
    kneN = joint_blob(F, 'kneeN', V, knN, 5.4, z=-15.5, joins=('thighN', 'shinN'), ry=5.2)
    shN_, LshN = limb(F, 'shinN', V, [knN, vlerp(knN, anN, 0.5), anN],
                      [(0, 4.8), (0.3, 4.4), (0.8, 3.4), (1, 3.1)],
                      [(0, 5.0), (0.3, 6.2), (0.6, 5.4), (1, 3.2)], z=-14, cap0=0.6, cap1=0.5,
                      joins=('kneeN', 'thighN', 'footN'))
    foot_tuck(F, 'footN', P(anN), -8.0, joins=('shinN',))
    thF, LthF = limb(F, 'thighF', V, [hipF, vlerp(hipF, knF, 0.5), knF],
                     [(0, 8.0), (0.3, 8.2), (0.7, 6.8), (1, 5.3)],
                     [(0, 8.4), (0.3, 8.0), (0.7, 6.4), (1, 5.4)], z=-1.8, cap0=0.5, cap1=0.6,
                     joins=('torso', 'kneeF', 'shinF'))
    kneF = joint_blob(F, 'kneeF', V, knF, 5.4, z=-11.0, joins=('thighF', 'shinF'), ry=5.4)
    shF_, LshF = limb(F, 'shinF', V, [knF, vlerp(knF, anF, 0.5), anF],
                      [(0, 4.9), (0.15, 4.6), (0.4, 4.4), (0.85, 3.2), (1, 3.1)],
                      [(0, 5.2), (0.25, 6.5), (0.5, 5.8), (0.85, 3.7), (1, 3.3)], z=-11.5, cap0=0.6, cap1=0.5,
                      joins=('kneeF', 'thighF', 'footF'))
    foot_med(F, 'footF', P(anF), -12.0, s=SC * 0.93, joins=('shinF',))
    skin(thN, LthN, 0.25, 1.0, 'b', depth=0.45, ext=1.4, ang=0.4)
    skin(shN_, LshN, 0.1, 1.0, 'a', depth=0.4, ext=1.3, ang=0.3)
    skin(thF, LthF, 0.35, 1.0, 'b', depth=0.5, ext=1.3, ang=0.4)
    skin(shF_, LshF, 0.06, 1.0, 'b', depth=0.45, ext=1.35, ang=0.4)
    limb_lines(shF_, LshF, [[(0.1, -0.25), (0.36, -0.12), (0.62, -0.35)], [(0.05, 0.55), (0.14, 0.5), (0.24, 0.48)]])
    limb_lines(shN_, LshN, [[(0.1, -0.3), (0.4, -0.15), (0.65, -0.35)]])
    limb_lines(thF, LthF, [[(0.45, -0.1), (0.7, -0.2), (0.92, -0.05)]])

    uaN, LuaN = limb(F, 'uarmN', V, [shN, vlerp(shN, elN, 0.5), elN],
                     [(0, 5.0), (0.15, 5.4), (0.5, 4.6), (1, 3.8)],
                     [(0, 5.2), (0.2, 5.4), (0.5, 4.9), (1, 4.0)], z=-30, cap0=0.75, cap1=0.5,
                     joins=('elbowN', 'farmN'))
    elbN = joint_blob(F, 'elbowN', V, elN, 3.9, z=-35.2, joins=('uarmN', 'farmN'))
    faN, LfaN = limb(F, 'farmN', V, [elN, vlerp(elN, wrN, 0.5), wrN],
                     [(0, 3.9), (0.25, 4.2), (0.65, 3.3), (1, 2.6)],
                     [(0, 3.8), (0.25, 4.0), (0.7, 3.0), (1, 2.5)], z=-35, cap0=0.5, cap1=0.3,
                     joins=('uarmN', 'elbowN', 'fistN'))
    pw, pe = P(wrN), P(elN)
    fist_hammer(F, 'fistN', pw, math.atan2(pw[1] - pe[1], pw[0] - pe[0]) + 0.1, -38, s=SC * 0.95,
                joins=('farmN',))
    skin(uaN, LuaN, 0.1, 1.0, 'b', depth=0.45, ext=1.4, ang=0.3)
    skin(faN, LfaN, 0.05, 0.95, 'b', depth=0.45, ext=1.4, ang=0.3)
    limb_lines(faN, LfaN, [[(0.06, 0.35), (0.34, 0.18), (0.66, 0.02)]])

    uaF, LuaF = limb(F, 'uarmF', V, [shF, vlerp(shF, elF, 0.5), elF],
                     [(0, 5.0), (0.2, 5.3), (0.5, 4.7), (1, 3.8)],
                     [(0, 5.2), (0.2, 5.4), (0.5, 4.9), (1, 4.0)], z=3, cap0=0.75, cap1=0.5,
                     joins=('elbowF', 'farmF'))
    elbF = joint_blob(F, 'elbowF', V, elF, 3.8, z=2.5, joins=('uarmF', 'farmF'))
    faF, LfaF = limb(F, 'farmF', V, [elF, vlerp(elF, wrF, 0.5), wrF],
                     [(0, 3.8), (0.25, 4.0), (0.65, 3.2), (1, 2.6)],
                     [(0, 3.7), (0.25, 3.9), (0.7, 3.0), (1, 2.5)], z=-6, cap0=0.5, cap1=0.3,
                     joins=('uarmF', 'elbowF', 'handF'))
    pw, pe = P(wrF), P(elF)
    hand_core(F, 'handF', pw, math.atan2(pw[1] - pe[1], pw[0] - pe[0]) - 0.15, -13, s=SC * 0.95, joins=('farmF',),
              thumb_behind=True)
    skin(faF, LfaF, 0.05, 0.95, 'b', depth=0.5, ext=1.3)

    # the head bowed over the work, on a short neck
    nb = T3(50)
    nt = vadd(nb, vmul((0.0, math.cos(34 * DEG), math.sin(34 * DEG)), 6.0))
    tilt = 0.55
    c_, s_ = math.cos(tilt), math.sin(tilt)
    q = P(nt)
    off = (-3.0 * c_ - 5.0 * s_, -3.0 * s_ + 5.0 * c_)
    ear = (q[0] - off[0] * SC, q[1] - off[1] * SC)
    head = Head(F, ear, SC, tilt, -34, sex='F')
    hp = head.p
    neck = F.part('neck', closed([hp(3.6, 11.8), hp(1.4, 10.2), hp(-0.4, 7.4), hp(-3.4, 5.6), hp(-6.8, 4.8),
                                  hp(-8.4, 2.8), P(T3(47, 0, -5.5)), P(T3(45, -6, 0)), P(T3(46, 0, 6.0)),
                                  P(T3(48, 0, 6.5))]), -1, w=2.2, joins=('head', 'torso'))
    hair = head.hair_lines([(7.2, -8.6), (5.2, -10.7), (2.3, -12.0), (-1.0, -12.4), (-4.8, -11.8), (-8.0, -10.0),
                            (-10.7, -7.1), (-11.8, -3.6), (-11.6, -0.4), (-10.8, 2.2)],
                           [(7.2, -8.6), (5.4, -7.8), (3.6, -6.2), (2.4, -4.6), (0.8, -4.9), (-1.0, -5.0), (-2.6, -3.6),
                            (-3.6, -1.4), (-5.4, 0.6), (-8.0, 1.8), (-10.8, 2.2)], 27, edge_w=1.6, wave=0.18,
                           tip=(0.2, 0.5), tuft=(2.6, 4.0))
    # the hair gathered at the nape in a thong, the tail hanging over the cape
    tq = hp(-10.6, 1.4)
    tail_l = [tq, (tq[0] - 1.6 * SC, tq[1] + 3.0 * SC), (tq[0] - 3.4 * SC, tq[1] + 7.0 * SC),
              (tq[0] - 4.2 * SC, tq[1] + 11.0 * SC), (tq[0] - 4.0 * SC, tq[1] + 14.5 * SC)]
    tail_r = [(tq[0] + 1.4 * SC, tq[1] + 0.6 * SC), (tq[0] + 0.4 * SC, tq[1] + 4.0 * SC),
              (tq[0] - 1.0 * SC, tq[1] + 7.6 * SC), (tq[0] - 2.0 * SC, tq[1] + 11.2 * SC), tail_l[-1]]
    tl, tr = catmull(tail_l, step=1.5), catmull(tail_r, step=1.5)
    tail = F.part('tail', tl + tr[::-1][1:-1], -34.5, w=1.6)
    for fr in (0.2, 0.4, 0.6, 0.8):
        c = flow(tl, tr, fr)
        for seg in broken(c, (30, 70), (3, 6)):
            tail.add(seg, w=0.85, hand=0.2)
    tie_a, tie_b = at(tl, 0.12), at(tr, 0.12)
    for k in range(3):
        d = k * 1.1 * SC
        tail.add([(tie_a[0] + d * 0.3, tie_a[1] + d), (tie_b[0] + d * 0.3, tie_b[1] + d)], w=1.3, clip=False, hand=0.05)

    # a short cape of hide over her shoulders and upper back, its hem trimmed with fur
    rings = [ring_pts(T3(49.5), 9.0, 7.5, 7.5, 2.2, rt=rt, fw=fw),
             ring_pts(T3(45.5), 19.5, 10.5, 11.0, 2.4, rt=rt, fw=fw),
             ring_pts(T3(31.0), 20.5, 15.5, 14.0, 2.2, rt=rt, fw=fw,
                      sag=lambda ph: 1.6 * math.cos(ph) * -1 + 0.8 * math.sin(4 * ph))]
    ctop, chem, cpoly = band_poly(V, rings)
    chem_r = rag(chem, 0.9, 7)
    cape = F.part('cape', ctop + [max(cpoly, key=lambda q: q[0])] + chem_r[::-1] + [min(cpoly, key=lambda q: q[0])],
                  -31, w=2.0)
    for ph0 in (-2.2, -1.75, -1.3, -0.85, -0.4):
        c = catmull([P(vlerp(ring_at(T3(49.5), 9.0, 7.5, 7.5, 2.2, ph0, rt=rt, fw=fw),
                             ring_at(T3(31.0), 20.5, 15.5, 14.0, 2.2, ph0 + 0.08, rt=rt, fw=fw), f))
                     for f in (0.15, 0.5, 0.95)], step=1.5)
        for seg in broken(c, (24, 60), (5, 10), 0.9):
            cape.add(seg, w=0.95)
    xs = [q[0] for q in cape.poly]
    x0, x1 = min(xs), max(xs)
    field(cape, cape.poly, 65, 5.6, lambda q: keep_prob((q[0] - x0) / (x1 - x0), 0.15, 0.6, 0.0), ln=(7, 13))
    fur_edge(cape, chem_r[::-1], every=6.0, ln=(4, 8), inward=1, keep=0.8)

    # the wrap round her hips, laced at the near side
    K0, C0 = (15.5, 11.5, 11.0, 2.3), T3(12)
    K1, C1 = (19.0, 13.0, 15.0, 2.2), T3(-3)
    sag_h = lambda ph: 1.4 * math.cos(2 * ph) + 0.5 * math.sin(5 * ph)
    WP = lambda f, ph: band_pt(V, C0, K0, C1, K1, f, ph, None, sag_h, rt=rt, fw=fw)
    wtop = near_arc(V, ring_pts(C0, *K0, rt=rt, fw=fw))
    whem = rag(near_arc(V, ring_pts(C1, *K1, rt=rt, fw=fw, sag=sag_h))[::-1], 0.8, 7)
    wrap = F.part('wrap', resample(wtop, 2.0) + whem[1:-1], -16, w=2.0)
    lap = catmull([WP(f, -1.25 - 0.1 * f) for f in (0.0, 0.3, 0.6, 1.0)], step=1.5)
    wrap.add(lap, w=1.5, hand=0.1)
    lacing(wrap, [WP(f, -1.2 - 0.1 * f) for f in (0.2, 0.45, 0.7)], [WP(f, -1.36 - 0.1 * f) for f in (0.2, 0.45, 0.7)])
    thong_ends(wrap, WP(0.06, -1.28), [(4, 20), (-3, 16)])
    for ph0 in (-2.0, -1.65, -0.9, -0.5, -0.1, 0.3):
        c = catmull([WP(f, ph0 + 0.06 * math.sin(f * 4 + ph0)) for f in (0.12, 0.5, 0.92)], step=1.5)
        for seg in broken(c, (20, 50), (5, 9), 0.9):
            wrap.add(seg, w=0.9)
    xs = [q[0] for q in wrap.poly]
    x0, x1 = min(xs), max(xs)
    field(wrap, wrap.poly, 60, 5.6, lambda q: keep_prob((q[0] - x0) / (x1 - x0), 0.15, 0.55, 0.0), ln=(7, 12))
    fur_edge(wrap, whem, every=6.5, ln=(4, 7), inward=1, keep=0.7)

    F.apply(lambda p: (cx - p[0], p[1]))
    return F, V, Tr, head
def add_spear(F, x, y_top, y_ground, z=-8.5):
    """The spear: a straight wooden shaft, a triangular Levallois point set in
    a lump of birch-tar resin and bound on with sinew."""
    phi = -0.012
    d = (math.sin(phi), math.cos(phi))
    top = (x - d[0] * 0, y_top)
    n = (-d[1], d[0])
    S = lambda s, w: (top[0] + d[0] * s + n[0] * w, top[1] + d[1] * s + n[1] * w)
    length = (y_ground - y_top) / d[1]
    shaft = F.part('shaft', [S(60, -5.0), S(length - 2, -5.4), S(length, 0), S(length - 2, 5.4), S(60, 5.0)], z, w=1.8)
    edge_l = [S(0, 0)] + [S(s, -s * 0.255 + pen.g(0.4)) for s in (8, 16, 24, 32, 40)] + [S(47, -12)]
    edge_r = [S(47, 12)] + [S(s, s * 0.245 + pen.g(0.4)) for s in (40, 32, 24, 16, 8)]
    point = F.part('point', edge_l + [S(53, -10), S(53, 10)] + edge_r, z - 0.2, w=1.8)
    for s0 in (7, 15, 23, 31, 39):                                     # retouch along the edges
        point.add(catmull([S(s0, -0.255 * s0), S(s0 + 4, -0.255 * (s0 + 4) + 2.8), S(s0 + 8, -0.255 * (s0 + 8))],
                          step=1.0), w=0.8, hand=0)
        point.add(catmull([S(s0 - 3, 0.245 * (s0 - 3)), S(s0 + 1, 0.245 * (s0 + 1) - 2.8), S(s0 + 5, 0.245 * (s0 + 5))],
                          step=1.0), w=0.8, hand=0)
    point.add(catmull([S(16, -4.1), S(27, 1.5), S(40, -2), S(46, -11)], step=1.0), w=0.85, hand=0)
    point.add(catmull([S(9, 2.2), S(20, -0.5), S(31, 7.6)], step=1.0), w=0.85, hand=0)
    resin = F.part('resin', closed([S(46, -9), S(56, -10), S(72, -8.5), S(84, -5.5), S(86, 0), S(84, 5.5), S(72, 8.5),
                                    S(56, 10), S(46, 9)], step=1.0), z - 0.1, w=1.6)
    for k in range(8):
        s0 = 52 + k * 3.8
        resin.add([S(s0, -9.5), S(s0 + 5, 9.5)], w=0.95, hand=0)
    for k in range(3):
        s0 = 58 + k * 7
        resin.add([S(s0 + 5, -9), S(s0, 9)], w=0.8, hand=0)
    for s0, s1, w0 in ((120, 170, 1.5), (260, 300, -1.8), (470, 520, 1.2), (640, 690, -1.0)):
        shaft.add([S(s0, w0), S(s1, w0 * 0.8)], w=0.75)

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
    for k, (p0, p1, w0, z) in enumerate((((cx - 98, cy + 7), (cx + 102, cy - 52), 7.5, 3.5),
                                         ((cx + 120, cy + 10), (cx - 96, cy - 48), 7.0, 3.6))):
        d = ((p1[0] - p0[0]) / dist(p0, p1), (p1[1] - p0[1]) / dist(p0, p1))
        n = (-d[1], d[0])
        w1 = w0 * 0.75
        Q = lambda c, s, o: (c[0] + d[0] * s + n[0] * o, c[1] + d[1] * s + n[1] * o)
        side1 = [Q(p0, 0, w0), Q(p1, 0, w1)]
        end1 = [Q(p1, 3, w1 * 0.4), Q(p1, -1.5, 0), Q(p1, 4, -w1 * 0.5)]               # burnt-through tip
        side2 = [Q(p1, 0, -w1), Q(p0, 0, -w0)]
        end0 = [Q(p0, -3, -w0 * 0.4), Q(p0, 2, -w0 * 0.05), Q(p0, -5, w0 * 0.5)]        # snapped end
        stick = F.part(f'stick{k}', side1 + end1 + side2 + end0, z, w=1.6)
        for o, L in ((-0.35, 9), (0.3, 13)):                                                 # splinters
            stick.add([Q(p0, 1, w0 * o), Q(p0, L, w0 * o * 0.7)], w=0.8)
        for s0, s1, o in ((0.06, 0.3, 0.35), (0.22, 0.5, -0.4), (0.7, 0.9, 0.25)):          # bark
            a, b = lerp(p0, p1, s0), lerp(p0, p1, s1)
            stick.add([(a[0] + n[0] * w0 * o, a[1] + n[1] * w0 * o), (b[0] + n[0] * w0 * o, b[1] + n[1] * w0 * o)], w=0.8)
        for s in [0.36 + 0.035 * j for j in range(18)]:                                     # char
            q = lerp(p0, p1, s)
            stick.add([(q[0] - n[0] * w0, q[1] - n[1] * w0), (q[0] + d[0] * 3 + n[0] * w0, q[1] + d[1] * 3 + n[1] * w0)],
                      w=0.8)
            if s > 0.86:
                stick.add([(q[0] + n[0] * w0, q[1] + n[1] * w0), (q[0] + d[0] * 3 - n[0] * w0, q[1] + d[1] * 3 - n[1] * w0)],
                          w=0.75)
        kn = lerp(p0, p1, 0.14)                                                              # a twig stub
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

    flame(cx + 2, cy - 8, 158, 62, 22, 2.0, 'flame0', sway=7, lick=9, ph=0.3)
    flame(cx - 38, cy - 6, 90, 40, 14, 2.2, 'flame1', sway=5, lick=-6, ph=2.0)
    flame(cx + 38, cy - 6, 124, 44, 28, 2.1, 'flame2', sway=-6, lick=7, ph=4.1)
    flame(cx - 66, cy - 3, 48, 24, 8, 2.3, 'flame3', sway=3, ph=1.0)
    flame(cx + 66, cy - 3, 78, 28, 22, 2.3, 'flame4', sway=-3, ph=5.0)
    flame(cx - 14, cy - 5, 66, 30, 14, 1.95, 'flame5', sway=3, ph=3.0)
    for x, y in ((cx - 30, cy - 202), (cx + 22, cy - 220), (cx + 6, cy - 242), (cx + 44, cy - 190), (cx - 50, cy - 174)):
        sp = F.part(f'spark{x}', blob(x, y, 1.0, 1.0), 0.5, w=1.0, outline=[])
        sp.add(blot_pts(x, y, 1.3, w=1.2), w=1.2, clip=False, hand=0, lift=0, piece=(400, 800))
    return F



# ------------------------------------------------------------------ assembly

A, VA, TrA, headA, grip = man(236)
add_spear(A, grip[0], 96, 886)
B, VB, TrB, headB = woman(830)
HF = hearth(485, 864)
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
    """The lip of a rock overhang running in from the top edge and out at the
    right edge, the narrow underside of the lip in shadow, the rock above it
    in straight hatching with strata and cracks, fading away from the lip."""
    lip_c = [(546, 0), (560, 36), (586, 70), (618, 90), (650, 104), (668, 122), (700, 138), (730, 150), (752, 174),
             (790, 188), (828, 204), (850, 224), (884, 238), (914, 252), (934, 274), (962, 292), (1000, 312)]
    face_c = [(566, 0), (578, 30), (604, 62), (640, 80), (672, 96), (710, 116), (740, 128), (768, 152), (806, 164),
              (846, 182), (870, 202), (904, 216), (934, 232), (962, 254), (1000, 274)]
    lip = rag(lip_c, 1.6, 9)
    face = rag(face_c, 1.2, 9)
    pen.line(lip, w=2.3, lift=0.15)
    for seg in broken(face, (40, 120), (4, 10), 0.95):
        pen.line(seg, w=1.3)
    # the narrow underside of the lip, in shadow
    for k in range(60):
        t = (k + 0.5) / 60
        a, b = at(lip, t), at(face, t)
        if dist(a, b) > 4:
            pen.line([lerp(a, b, 0.08), lerp(a, b, 0.92 - pen.r(0, 0.2))], w=0.75, hand=0.15, lift=0)
    # the rock above: straight hatching, dark along the lip and fading away from it
    region = face + [(1000, 0)]
    facer = resample(face, 6)

    def d_lip(q):
        return min(dist(q, p) for p in facer)
    for p0, p1 in scanlines(region, 32, 6.5, pen.r()):
        L = dist(p0, p1)
        if L < 4:
            continue
        dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        s = pen.r(0, 5)
        while s < L - 3:
            ln_ = min(pen.r(14, 30), L - s)
            m = (p0[0] + dx * (s + ln_ / 2), p0[1] + dy * (s + ln_ / 2))
            if pen.rng.random() < keep_prob(d_lip(m) / 110, 0.12, 1.0, 0.0):
                pen.line([(p0[0] + dx * s, p0[1] + dy * s), (p0[0] + dx * (s + ln_), p0[1] + dy * (s + ln_))],
                         w=0.75, hand=0.05, lift=0, occlude=False)
            s += ln_ + pen.r(3, 6)
    # strata following the lip, and cracks running up from it
    smooth_face = catmull(face_c, step=2.0)
    for off, keep in ((24, 0.8), (54, 0.55), (88, 0.3)):
        st = [(x + off * 0.25, y - off) for x, y in smooth_face]
        st = [p for p in st if 0 < p[1] and p[0] < 1000]
        for seg in broken(st, (24, 70), (8, 28), keep):
            pen.line(seg, w=1.0 if off < 50 else 0.85, hand=0.2, lift=0.05, occlude=False)
    for x0 in (640, 742, 836, 912):
        p = at(face, (x0 - 566) / 434)
        pts = [p, (p[0] + pen.r(-4, 4), p[1] - pen.r(12, 18)), (p[0] + pen.r(-8, 8), p[1] - pen.r(28, 40))]
        pen.line(pts, w=1.1, hand=0.6, lift=0.05, occlude=False)


shelter()

# smoke: wisps rising from the flames and drifting toward the overhang,
# spreading and twisting as they go
for k, (off, ph, top) in enumerate(((-1.6, 0.0, 0.86), (-0.5, 1.3, 1.0), (0.6, 2.4, 0.94), (1.6, 3.9, 0.8))):
    pts = []
    for i in range(90):
        u = i / 89
        y = 674 - u * 390
        x = 503 + u * u * 150 + off * (2 + 26 * u) + (3 + 15 * u) * math.sin(u * 9.5 + ph)
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


ground_hatch(120, 400, 885, 4)
ground_hatch(600, 930, 885, 4)
for x0, x1, y in ((70, 140, 902), (380, 430, 894), (570, 620, 900), (420, 520, 922), (700, 800, 924),
                  (210, 300, 927), (900, 960, 906), (620, 680, 942)):
    pen.line([(x0, y), (x1, y)], w=0.9, hand=0.5, lift=0.3, piece=(12, 30))
for x, y, s, r in ((598, 892, 8, 0.3), (614, 904, 7, 1.4), (630, 893, 7, 2.2), (642, 910, 6, 0.9),
                   (584, 908, 6, 2.8), (658, 898, 5, 1.9)):
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
