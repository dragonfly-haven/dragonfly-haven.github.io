"""04 DNA: the double helix as a twisted ladder.

Two sugar-phosphate backbones as flat ribbons wound on a cylinder (right-
handed B-DNA, about ten base pairs a turn, the strands offset so the major
and minor grooves alternate), base-pair rungs between them, set on a
diagonal. Modelled in 3D and drawn front to back with a depth test, so the
near ribbon hides what lies behind it. The inner face of each ribbon, seen
where it turns away behind the helix, is shaded with hatching across the band.
Drawn in the same ribbon language as 03 RNA.
"""

import math

from pen import Pen, resample, dist, lerp, inside, length

pen = Pen(seed=404)

# ---------------------------------------------------------------- 3D helpers


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def mul(v, k):
    return tuple(c * k for c in v)


def norm(v):
    L = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / L for c in v)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def over3(a, b, da, db):
    """A 3D segment run on past its ends by da and db (as measured in the picture)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return [lerp3(a, b, -da / L), lerp3(a, b, 1 + db / L)]


class Depth:
    """Occluders with depth: a 2D polygon, its depth (z, larger is nearer) and a tag.
    A point is hidden when it falls inside a nearer polygon not excluded by its tag."""

    def __init__(self, cell=40):
        self.cell = cell
        self.grid = {}
        self.items = []

    def add(self, poly, z, tag=None):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        bb = (min(xs), min(ys), max(xs), max(ys))
        k = len(self.items)
        self.items.append((poly, bb, z, tag))
        c = self.cell
        for gx in range(int(bb[0] // c), int(bb[2] // c) + 1):
            for gy in range(int(bb[1] // c), int(bb[3] // c) + 1):
                self.grid.setdefault((gx, gy), []).append(k)

    def hidden(self, p, z, skip=None, eps=0.8):
        c = self.cell
        for k in self.grid.get((int(p[0] // c), int(p[1] // c)), ()):
            poly, bb, zo, tag = self.items[k]
            if zo <= z + eps:
                continue
            if not (bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3]):
                continue
            if skip and skip(tag):
                continue
            if inside(p, poly):
                return True
        return False

    def runs(self, pts, zs, skip=None, eps=0.8, step=1.5):
        """Visible runs of a 2D polyline whose points carry depths zs."""
        fine, fz = [], []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(1, int(dist(a, b) / step))
            for j in range(n):
                t = j / n
                fine.append(lerp(a, b, t))
                fz.append(zs[i] + (zs[i + 1] - zs[i]) * t)
        fine.append(pts[-1])
        fz.append(zs[-1])
        out, cur = [], []
        for p, z in zip(fine, fz):
            sk = skip(p) if callable(skip) and getattr(skip, 'per_point', False) else skip
            if not self.hidden(p, z, sk, eps):
                cur.append(p)
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return [r for r in out if length(r) > 3.5]


# ---------------------------------------------------------------- the helix

CEN = (500, 500)
AXA = math.radians(-46)                     # axis runs up to the right
A = (math.cos(AXA), math.sin(AXA))          # up the helix, in the picture
X = (-A[1], A[0])                           # across it, to the right of A
PITCH = 368.0                               # one turn along the axis
R = 116.0                                   # backbone radius
HW = 16.0                                   # half width of a ribbon (as in 03)
U0, U1 = -470.0, 470.0                      # ends along the axis (about 2.55 turns)
BP_PER_TURN = 10.0
DELTA = math.radians(132)                   # angle between the strands across the minor groove
K = -2 * math.pi / PITCH                    # right-handed: dtheta/du
THETA0 = 0.35
LIGHT = norm((-0.55, -0.65, 0.55))          # from upper left, a little in front


def pos(u, th, r=R):
    """3D point (x, y, z) at axis position u, angle th, radius r."""
    x = CEN[0] + A[0] * u + X[0] * r * math.cos(th)
    y = CEN[1] + A[1] * u + X[1] * r * math.cos(th)
    return (x, y, r * math.sin(th))


def frame(u, th):
    """Ribbon centre, half-width vector W (in the cylinder's surface, across the strand),
    and the outward normal N, all 3D."""
    c = pos(u, th)
    a3 = (A[0], A[1], 0.0)
    e_th = (-math.sin(th) * X[0], -math.sin(th) * X[1], math.cos(th))
    rk = R * K
    W = norm(add(mul(a3, -rk), e_th))
    N = (math.cos(th) * X[0], math.cos(th) * X[1], math.sin(th))
    return c, W, N


def strand(phase, tag):
    """Samples along one backbone ribbon."""
    us = []
    u = U0 - 2 * HW
    while u < U1 + 2 * HW:
        us.append(u)
        u += 1.6
    S = []
    for i, u in enumerate(us):
        th = THETA0 + phase + K * u
        c, W, N = frame(u, th)
        e1 = add(c, mul(W, HW))
        e2 = add(c, mul(W, -HW))
        S.append(dict(u=u, th=th, c=c, W=W, N=N, e1=e1, e2=e2, i=i, tag=tag))
    return S



def ax(p):
    """Position of a point along the helix axis."""
    return (p[0] - CEN[0]) * A[0] + (p[1] - CEN[1]) * A[1]


def slab_runs(pts3):
    """A 3D polyline cut to the stretch of helix between the end planes (U0..U1)."""
    out, cur = [], []
    for i, p in enumerate(pts3):
        inside_ = U0 <= ax(p) <= U1
        if i:
            q = pts3[i - 1]
            aq, ap = ax(q), ax(p)
            for edge in (U0, U1):
                if (aq - edge) * (ap - edge) < 0:
                    t = (edge - aq) / (ap - aq)
                    x = lerp3(q, p, t)
                    if cur:
                        cur.append(x)
                        out.append(cur)
                        cur = []
                    else:
                        cur = [x]
        if inside_:
            cur.append(p)
    if cur:
        out.append(cur)
    return [r for r in out if len(r) > 1]


def clip_poly(poly3):
    """A 3D polygon clipped to the slab between the end planes (Sutherland-Hodgman)."""
    pts = list(poly3)
    for edge, keep in ((U0, lambda a: a >= U0), (U1, lambda a: a <= U1)):
        if not pts:
            break
        res = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            ap, aq = ax(p), ax(q)
            if keep(ap):
                res.append(p)
            if keep(ap) != keep(aq):
                res.append(lerp3(p, q, (edge - ap) / (aq - ap)))
        pts = res
    return pts


strands = [strand(0.0, 'a'), strand(DELTA, 'b')]
depth = Depth()

# occluders: each ribbon in small quads
QSTEP = 3
for S in strands:
    for i in range(0, len(S) - QSTEP, QSTEP):
        p, q = S[i], S[i + QSTEP]
        poly3 = clip_poly([p['e1'], q['e1'], q['e2'], p['e2']])
        if len(poly3) < 3:
            continue
        z = sum(c[2] for c in poly3) / len(poly3)
        depth.add([c[:2] for c in poly3], z, (p['tag'], i))

# rungs: base pairs as two pegs meeting near the middle
RISE = PITCH / BP_PER_TURN
rungs = []
nbp = int((U1 - U0 - RISE * 0.6) / RISE)
u_first = U0 + (U1 - U0 - (nbp - 1) * RISE) / 2
for k in range(nbp):
    u = u_first + k * RISE
    tha = THETA0 + K * u
    thb = tha + DELTA
    pa, pb = pos(u, tha), pos(u, thb)
    f = 0.56 if (k * 7 + 3) % 5 < 2 else 0.44   # purine with pyrimidine, either way round
    rungs.append((u, pa, pb, f))

RT = 7.0  # half thickness of a rung, along the axis (as the pegs of 03)


def rung_quads(pa, pb, f):
    """The two pegs of a rung as 3D quads (corner points), meeting with a small gap."""
    a3 = (A[0], A[1], 0.0)
    m = lerp3(pa, pb, f)
    d = norm(tuple(b - a for a, b in zip(pa, pb)))
    gap = 2.2
    m1 = add(m, mul(d, -gap))
    m2 = add(m, mul(d, gap))
    out = []
    for s, e in ((pa, m1), (pb, m2)):
        out.append([add(s, mul(a3, RT)), add(e, mul(a3, RT)), add(e, mul(a3, -RT)), add(s, mul(a3, -RT))])
    return out


for k, (u, pa, pb, f) in enumerate(rungs):
    for j, quad in enumerate(rung_quads(pa, pb, f)):
        # split along the peg so depth stays local
        n = 6
        for m in range(n):
            t0, t1 = m / n, (m + 1) / n
            c0 = lerp3(quad[0], quad[1], t0)
            c1 = lerp3(quad[0], quad[1], t1)
            c2 = lerp3(quad[3], quad[2], t1)
            c3 = lerp3(quad[3], quad[2], t0)
            z = (c0[2] + c1[2] + c2[2] + c3[2]) / 4
            depth.add([c0[:2], c1[:2], c2[:2], c3[:2]], z, ('r', k))


def skip_own(tag, i, win):
    def f(t):
        return t is not None and t[0] == tag and abs(t[1] - i) <= win
    return f


def draw3(pts3, w, skip=None, eps=0.8, hand=1.0, **kw):
    pts = [p[:2] for p in pts3]
    zs = [p[2] for p in pts3]
    for run in depth.runs(pts, zs, skip, eps):
        pen.line(run, w=w, hand=hand, occlude=False, **kw)


def zweight(z, lo, hi):
    t = max(0.0, min(1.0, (z / R + 1) / 2))
    return lo + (hi - lo) * t


# ---------------------------------------------------------------- ribbon edges

for S in strands:
    tag = S[0]['tag']
    for key in ('e1', 'e2'):
        # in chunks, so the weight follows depth (nearer is heavier)
        for k0 in range(0, len(S) - 1, 40):
            chunk = S[k0:k0 + 41]
            i0, i1 = chunk[0]['i'], chunk[-1]['i']

            def skip(t, tag=tag, i0=i0, i1=i1):
                return t is not None and t[0] == tag and i0 - 7 <= t[1] <= i1 + 7
            for run in slab_runs([c[key] for c in chunk]):
                zm = sum(p[2] for p in run) / len(run)
                draw3(run, zweight(zm, 1.75, 2.55), skip, eps=1.0, hand=0.9)
    # the cut ends, along the end planes
    for edge in (U0, U1):
        ends = []
        for key in ('e1', 'e2'):
            pts = [c[key] for c in S]
            for i in range(1, len(pts)):
                a0, a1 = ax(pts[i - 1]), ax(pts[i])
                if (a0 - edge) * (a1 - edge) <= 0 and a0 != a1:
                    ends.append((lerp3(pts[i - 1], pts[i], (edge - a0) / (a1 - a0)), i))
                    break
        if len(ends) == 2:
            i = (ends[0][1] + ends[1][1]) // 2
            draw3(over3(ends[0][0], ends[1][0], 2.0, 2.5), 2.0, skip_own(tag, i, 30), eps=1.0, hand=0.4)

# ---------------------------------------------------------------- ribbon shading

L2 = norm((LIGHT[0], LIGHT[1]))


def face_shade(smp):
    """0 (lit) .. 1 (dark) for the face of the ribbon we see at this sample."""
    N = smp['N']
    if N[2] <= 0:
        # the inner face, seen through the helix where the ribbon passes behind
        return 0.6 + 0.4 * (1 - abs(N[2]))
    # the outer face darkens as it turns away from us, more on the side away from the light
    away = max(0.0, -(N[0] * L2[0] + N[1] * L2[1]) / (math.hypot(N[0], N[1]) or 1))
    return (1 - N[2]) ** 1.2 * (0.55 + 0.75 * away)


for S in strands:
    tag = S[0]['tag']
    last = None
    acc = 0.0
    for i in range(1, len(S) - 1):
        smp = S[i]
        acc += dist(S[i - 1]['c'][:2], smp['c'][:2])
        sh = face_shade(smp)
        if sh < 0.3:
            last = None
            acc = 0.0
            continue
        sp = 9.5 - 4.0 * min(1.0, (sh - 0.3) / 0.6)   # 5.5 .. 9.5
        if acc < sp:
            continue
        a, b = smp['e1'], smp['e2']
        if dist(a[:2], b[:2]) < 5:
            continue
        if last is not None:
            if min(dist(a[:2], last[0][:2]), dist(b[:2], last[1][:2])) < 5.0:
                continue
        acc = 0.0
        last = (a, b)
        # lines stop short, as a hand does; light ones only part way across
        s0 = pen.r(0.04, 0.16)
        s1 = 1 - pen.r(0.04, 0.2) - (0.35 * pen.r() if sh < 0.5 else 0)
        p0, p1 = lerp3(a, b, s0), lerp3(a, b, s1)
        for run in slab_runs([p0, p1]):
            draw3(run, pen.r(0.85, 1.05), skip_own(tag, i, 9), eps=1.0, hand=0.3, lift=0.04, piece=(40, 120))

# ---------------------------------------------------------------- rungs

for k, (u, pa, pb, f) in enumerate(rungs):
    quads = rung_quads(pa, pb, f)
    for j, q in enumerate(quads):
        zm = sum(c[2] for c in q) / 4
        w = zweight(zm, 1.45, 1.95)

        def skip(t, k=k):
            return t is not None and t[0] == 'r' and t[1] == k
        # the two long sides, the meeting end, and the root where it shows on a ribbon behind
        draw3([q[0], q[1]], w, skip, eps=0.6, hand=0.5)
        draw3([q[3], q[2]], w * 1.1, skip, eps=0.6, hand=0.5)
        draw3(over3(q[1], q[2], pen.r(0.3, 1.6), pen.r(0.3, 1.6)), w * 0.9, skip, eps=0.6, hand=0.2, lift=0)
        if q[0][2] < -HW:
            draw3([q[0], q[3]], w * 0.8, skip, eps=0.6, hand=0.2, lift=0)
        # shaded with short slanted strokes across, as the pegs of 03
        L = dist(q[0][:2], q[1][:2])
        if L < 8:
            continue
        sp = 5.5
        slant = 0.45 * 2 * RT
        t = 3.5 + pen.r(0, 1.5)
        while t + slant < L - 3:
            u0, u1 = t / L, (t + slant) / L
            c0 = lerp3(lerp3(q[0], q[3], 0.14), lerp3(q[1], q[2], 0.14), u0)
            c1 = lerp3(lerp3(q[0], q[3], 0.86), lerp3(q[1], q[2], 0.86), u1)
            draw3([c0, c1], pen.r(0.9, 1.1), skip, eps=0.6, hand=0.2, lift=0)
            t += sp + pen.r(-0.2, 0.3)

pen.save('../04-dna.svg', mirror=False)
pen.report()
