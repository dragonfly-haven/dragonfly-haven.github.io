"""04 DNA: the double helix as an engraver would draw a physical model of it.

Right-handed B-DNA, ten and a half base pairs a turn, a little over two turns
on a diagonal, its upper end turned a little away from us (mild perspective).
The two sugar-phosphate backbones are solid round tubes wound on one
cylinder, offset round it so a narrow (minor) and a wide (major) groove
repeat every turn. The bases are flat slabs, two to a pair, meeting near the
middle; the pair planes lie square across the axis, so as the helix turns a
slab is seen as a bar, or tipped to show its face. Modelled in 3D and drawn
with a depth test, near parts over far ones. Shading as in 05 and 07: light
from the upper left, contour hatching along each tube on its shadow side,
heavier in the core of the shadow, parallel strokes on the slabs' dark faces.
"""

import math

from pen import Pen, dist, lerp, length, resample

pen = Pen(seed=404)

# ---------------------------------------------------------------- 3D helpers


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(v, k):
    return tuple(c * k for c in v)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(v):
    L = math.sqrt(dot(v, v)) or 1.0
    return tuple(c / L for c in v)


def lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ---------------------------------------------------------------- camera

FOCAL = 2600.0                              # eye distance: mild perspective
EYE = (0.0, 0.0, FOCAL)                     # x right, y down, z toward us


def proj(p):
    """Picture point (x, y) and depth z (larger is nearer) of a model point."""
    k = FOCAL / (FOCAL - p[2])
    return (500 + p[0] * k, 500 + p[1] * k, p[2])


def view(p):
    return norm(sub(EYE, p))


LIGHT = norm((-0.5, -0.62, 0.6))            # from the upper left, a little in front

# ---------------------------------------------------------------- depth test (triangles)


class Depth:
    """Triangles in the picture with a depth at each corner; a point is hidden when a
    triangle over it is nearer there (interpolated), unless its tag is excused."""

    def __init__(self, cell=30):
        self.cell = cell
        self.grid = {}
        self.tris = []

    def add(self, a, b, c, tag):
        xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
        bb = (min(xs), min(ys), max(xs), max(ys))
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-6:
            return
        k = len(self.tris)
        self.tris.append((a, b, c, det, bb, tag))
        s = self.cell
        for gx in range(int(bb[0] // s), int(bb[2] // s) + 1):
            for gy in range(int(bb[1] // s), int(bb[3] // s) + 1):
                self.grid.setdefault((gx, gy), []).append(k)

    def quad(self, a, b, c, d, tag):
        self.add(a, b, c, tag)
        self.add(a, c, d, tag)

    def hidden(self, p, skip=None, eps=1.0):
        s = self.cell
        for k in self.grid.get((int(p[0] // s), int(p[1] // s)), ()):
            a, b, c, det, bb, tag = self.tris[k]
            if not (bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3]):
                continue
            l1 = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / det
            l2 = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / det
            l3 = 1 - l1 - l2
            if l1 < -1e-9 or l2 < -1e-9 or l3 < -1e-9:
                continue
            z = l1 * a[2] + l2 * b[2] + l3 * c[2]
            if z > p[2] + eps and not (skip and skip(tag)):
                return True
        return False

    def runs(self, pts, skip=None, eps=1.0, step=1.2, minlen=3.0, ids=None):
        """Visible runs of a projected polyline (points (x, y, z)). With ids, skip is
        asked about (tag, id) at each point."""
        fine, fid = [], []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
            for j in range(n):
                fine.append(lerp3(a, b, j / n))
                fid.append(None if ids is None else ids[i] + (ids[i + 1] - ids[i]) * j / n)
        fine.append(pts[-1])
        fid.append(None if ids is None else ids[-1])
        out, cur = [], []
        for p, q in zip(fine, fid):
            sk = skip if q is None or skip is None else (lambda t, q=q: skip(t, q))
            if not self.hidden(p, sk, eps):
                cur.append(p)
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return [r for r in out if length([x[:2] for x in r]) > minlen]


depth = Depth()

# ---------------------------------------------------------------- the sure line


def ink(pts, w, hand=0.25, seg=24.0):
    """A sure line through projected points: a faint slow wobble, no lifts, and a weight
    w(z) that may follow depth; with w None each point carries its own weight (x, y, z, w)."""
    p2 = [q[:2] for q in pts]
    total = length(p2)
    if total < 1.0:
        return
    n = max(2, int(total / 1.5))
    acc = [0.0]
    for i in range(1, len(p2)):
        acc.append(acc[-1] + dist(p2[i - 1], p2[i]))
    fine, zs, wl = [], [], []
    j = 0
    for k in range(n + 1):
        s = total * k / n
        while j < len(p2) - 2 and acc[j + 1] < s:
            j += 1
        t = (s - acc[j]) / ((acc[j + 1] - acc[j]) or 1)
        fine.append(lerp(p2[j], p2[j + 1], t))
        zs.append(pts[j][2] + (pts[j + 1][2] - pts[j][2]) * t)
        if len(pts[j]) > 3:
            wl.append(pts[j][3] + (pts[j + 1][3] - pts[j][3]) * t)
    if hand > 0:
        ph, fq = pen.r(0, 6.3), pen.r(0.006, 0.012)
        moved = []
        for k, p in enumerate(fine):
            s = total * k / n
            a, b = fine[max(0, k - 1)], fine[min(n, k + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            off = hand * math.sin(s * fq * 2 * math.pi + ph) * min(1.0, s / 8, (total - s) / 8)
            moved.append((p[0] + dy / L * off, p[1] - dx / L * off))
        fine = moved
    m = max(1, int(round(total / seg)))
    for q in range(m):
        k0, k1 = n * q // m, n * (q + 1) // m
        piece = fine[k0:k1 + 1]
        if len(piece) >= 2:
            z = sum(zs[k0:k1 + 1]) / (k1 - k0 + 1)
            if w is None:
                ww = sum(wl[k0:k1 + 1]) / (k1 - k0 + 1)      # the weight rides on the points
            elif callable(w):
                ww = w(z)
            else:
                ww = w
            pen.raw(piece, max(0.6, min(3.0, ww)))


def draw(pts, w, skip=None, eps=1.0, hand=0.25, minlen=3.0, ids=None):
    for run in depth.runs(pts, skip, eps, minlen=minlen, ids=ids):
        ink(run, w, hand=hand)


# ---------------------------------------------------------------- the helix

AXA = math.radians(-44)                     # the axis runs up to the right in the picture
TILT = math.radians(5)                      # and its upper end turns away from us
A3 = norm((math.cos(AXA) * math.cos(TILT), math.sin(AXA) * math.cos(TILT), -math.sin(TILT)))
X3 = norm((-math.sin(AXA), math.cos(AXA), 0.0))        # across the axis, down to the right
Y3 = norm(cross(A3, X3))
if Y3[2] < 0:
    Y3 = mul(Y3, -1)                        # round the helix toward us
R = 100.0                                   # backbone radius (about 10 A)
PITCH = 357.0                               # one turn (about 36 A)
BP_PER_TURN = 10.5
TURNS = 2.25
RT = 16.0                                   # radius of a backbone tube
DELTA = math.radians(140)                   # strand b round from strand a across the minor groove
K = -2 * math.pi / PITCH                    # right-handed (checked: the near strands rise to the right)
U_LO, U_HI = -TURNS * PITCH / 2, TURNS * PITCH / 2
PHI = math.radians(100)                     # strand a's angle at the lower end
RISE = PITCH / BP_PER_TURN
NBP = int(TURNS * BP_PER_TURN)
U0 = (U_HI + U_LO) / 2 - RISE * (NBP - 1) / 2   # the pairs sit centred along the length


def pos(u, th, r=R):
    return add(mul(A3, u), mul(X3, r * math.cos(th)), mul(Y3, r * math.sin(th)))


def theta(tag, u):
    return PHI + (DELTA if tag == 'b' else 0.0) + K * (u - U_LO)


# ---------------------------------------------------------------- backbone tubes


def tube(tag):
    """Samples along a backbone: centre, tangent, and the frame of its visible half."""
    out = []
    u = U_LO
    du = 0.7
    while u <= U_HI + 1e-6:
        c = pos(u, theta(tag, u))
        t = norm(sub(pos(u + 0.5, theta(tag, u + 0.5)), pos(u - 0.5, theta(tag, u - 0.5))))
        v = view(c)
        m = norm(cross(t, v))               # across the tube, in the picture
        w = norm(sub(v, mul(t, dot(v, t))))  # the side of the tube facing us
        out.append(dict(u=u, c=c, t=t, m=m, w=w, i=len(out)))
        u += du
    return out


def surf(smp, o):
    """The tube's visible surface point at o (-1 .. 1 across it) and its normal."""
    n = add(mul(smp['m'], o), mul(smp['w'], math.sqrt(max(0.0, 1 - o * o))))
    return add(smp['c'], mul(n, RT)), n


HALO = 3.0                                  # a hair of white where a near part crosses a far one


def occ(smp, o):
    """An occluding point: the surface's depth, but a little wider than the tube."""
    p, n = surf(smp, o)
    q = proj(add(smp['c'], mul(n, RT + HALO)))
    return (q[0], q[1], proj(p)[2])


def cap_dir(smp, sg):
    """In the plane square to the view: the way out of the tube's end."""
    n2 = norm(cross(view(smp['c']), smp['m']))
    return n2 if dot(n2, smp['t']) * sg > 0 else mul(n2, -1)


tubes = {'a': tube('a'), 'b': tube('b')}
for tag, S in tubes.items():
    for i in range(0, len(S) - 3, 3):
        p, q = S[i], S[i + 3]
        # the tube itself (it may hide its own far side where it bends), and a halo a
        # little wider that only other parts see
        for kind, fn in (('t', lambda smp, o: proj(surf(smp, o)[0])), ('h', occ)):
            rails = [[fn(smp, o) for o in (-1.0, -0.5, 0.0, 0.5, 1.0)] for smp in (p, q)]
            for j in range(4):
                depth.quad(rails[0][j], rails[1][j], rails[1][j + 1], rails[0][j + 1], (kind, tag, i))
    # the round ends: a fan over the half disc that shows beyond the tube
    for smp, sg in ((S[0], -1), (S[-1], 1)):
        e = cap_dir(smp, sg)
        front = proj(add(smp['c'], mul(smp['w'], RT)))
        rim = [proj(add(smp['c'], mul(smp['m'], (RT + HALO) * math.cos(math.pi * j / 12)),
                        mul(e, (RT + HALO) * math.sin(math.pi * j / 12)))) for j in range(13)]
        for a, b in zip(rim, rim[1:]):
            depth.add(front, a, b, ('h', tag, smp['i']))

# ---------------------------------------------------------------- base slabs

SLAB_T = 6.0                                # half thickness, along the axis
SLAB_W = 17.0                               # half width, across the pair's length
GAP = 2.0                                   # half the gap where the two bases of a pair meet
SEQ = 'ATGCGTACCATGGCTAGCATTGC'               # strand a, 5' to 3' up the helix (any fixed sequence)
slabs = []                                  # (k, h, corners 8 x 3D)
for k in range(NBP):
    u = U0 + RISE * k
    pa, pb = pos(u, theta('a', u)), pos(u, theta('b', u))
    # a purine (A, G: two rings) reaches further across than its pyrimidine partner
    m = lerp3(pa, pb, 0.5 + (0.08 if SEQ[k % len(SEQ)] in 'AG' else -0.08))
    d = norm(sub(pb, pa))
    wv = norm(cross(A3, d))
    for h, (s0, e0, dd) in enumerate(((pa, m, d), (pb, m, mul(d, -1)))):
        a0 = add(s0, mul(dd, RT * 0.4))
        a1 = add(e0, mul(dd, -GAP))
        corners = []
        for end in (a0, a1):
            for sw in (-1, 1):
                for st in (-1, 1):
                    corners.append(add(end, mul(wv, sw * SLAB_W), mul(A3, st * SLAB_T)))
        slabs.append((k, h, corners, dd, wv))

# faces of a slab as corner indices (corners: end(0/1) x w(-/+) x t(-/+))
FACES = [((0, 1, 3, 2), 'root'), ((4, 6, 7, 5), 'tip'), ((0, 4, 5, 1), 'w-'), ((2, 3, 7, 6), 'w+'),
         ((0, 2, 6, 4), 't-'), ((1, 5, 7, 3), 't+')]


def face_normal(name, dd, wv):
    return {'root': mul(dd, -1), 'tip': dd, 'w-': mul(wv, -1), 'w+': wv, 't-': mul(A3, -1), 't+': A3}[name]


for k, h, cs, dd, wv in slabs:
    P = [proj(c) for c in cs]
    for idx, name in FACES:
        depth.quad(P[idx[0]], P[idx[1]], P[idx[2]], P[idx[3]], ('s', k, h))
    # its halo: a little wider and thicker, not longer (the pair's two halves meet end to end)
    G = []
    for j, c in enumerate(cs):
        sw, st = (1 if j & 2 else -1), (1 if j & 1 else -1)
        q = proj(add(c, mul(wv, sw * HALO), mul(A3, st * HALO)))
        G.append((q[0], q[1], proj(c)[2]))
    for idx, name in FACES:
        depth.quad(G[idx[0]], G[idx[1]], G[idx[2]], G[idx[3]], ('g', k, h))

# ---------------------------------------------------------------- drawing: the tubes


def lit(n):
    return max(0.0, dot(n, LIGHT))


def tz(lo, hi):
    """Weight from depth: lo at the back of the helix, hi at its front."""
    return lambda z: lo + (hi - lo) * max(0.0, min(1.0, (z / (R + RT) + 1) / 2))


def own_tube(tag):
    return lambda t, q: t is not None and t[1] == tag and (t[0] == 'h' or (t[0] == 't' and abs(t[2] - q) <= 9))


for tag, S in tubes.items():
    ids = [s['i'] for s in S]
    # the two silhouettes
    for o in (-1.0, 1.0):
        draw([proj(surf(s, o)[0]) for s in S], tz(1.8, 2.7), own_tube(tag), ids=ids)
    # round ends
    for smp, sg in ((S[0], -1), (S[-1], 1)):
        e = cap_dir(smp, sg)
        pts = []
        for j in range(17):
            f = math.pi * j / 16
            p = add(smp['c'], mul(smp['m'], RT * math.cos(f)), mul(e, RT * math.sin(f)))
            pts.append(proj(p))
        draw(pts, tz(1.8, 2.6), own_tube(tag), ids=[smp['i']] * len(pts))
    # contour hatching along the tube on its shadow side: lines at fixed places across
    # it, each drawn where the surface there is dark enough, heavier in the core shadow
    ease = int(RT * 0.9 / 1.4)              # samples over which the hatching thins out at an end
    for o in (-0.7, -0.35, 0.0, 0.35, 0.7):     # 0.35 x RT apart: at least 5.6 in the picture
        run, rid = [], []
        for s in S[ease // 2:-(ease // 2)] + [None]:
            dark = 0.0
            if s is not None:
                p, n = surf(s, o)
                dark = 1 - lit(n)
            if dark > 0.52:
                wt = 0.85 + 1.5 * min(1.0, (dark - 0.52) / 0.4) ** 1.5
                wt = 0.85 + (wt - 0.85) * (0.55 if abs(o) > 0.7 else 1.0)   # reflected light at the rim
                fade = min(s['i'], len(S) - 1 - s['i']) / ease                # thinning toward an end
                if fade < 1:
                    wt = 0.7 + (wt - 0.7) * max(0.0, fade)
                run.append(proj(p) + (wt,))
                rid.append(s['i'])
            else:
                if len(run) > 3:
                    draw(run, None, own_tube(tag), ids=rid, hand=0.15)
                run, rid = [], []

    # in the core of the shadow, short contour strokes round the tube, crossing the lines
    # along it (as in the darkest band of 05), every RING units along its middle
    RING = 6.5
    run_len, last = 0.0, None
    for s in S[ease:-ease]:
        cp = proj(s['c'])
        if last is not None:
            run_len += dist(cp[:2], last[:2])
        last = cp
        if run_len < RING:
            continue
        arc, aid = [], []
        for j in range(25):
            o = -1 + 2 * j / 24
            p, n = surf(s, o)
            dark = 1 - lit(n)
            if dark > 0.86 and abs(o) < 0.88:
                arc.append(proj(p) + (0.75 + 0.5 * min(1.0, (dark - 0.86) / 0.2),))
                aid.append(s['i'])
            elif len(arc) > 2:
                break
        if len(arc) > 2 and length([q[:2] for q in arc]) > 11:      # only where the shadow is broad
            draw(arc, None, own_tube(tag), ids=aid, hand=0.08)
            run_len = 0.0

# ---------------------------------------------------------------- drawing: the slabs


# the long sides of the faces that run along a slab: strokes go from one to the other
SIDES = {'t-': ((0, 4), (2, 6)), 't+': ((1, 5), (3, 7)), 'w-': ((0, 4), (1, 5)), 'w+': ((2, 6), (3, 7))}


def own_slab(k, h):
    return lambda t: t is not None and t[0] in 'sg' and t[1] == k and t[2] == h


for k, h, cs, dd, wv in slabs:
    P = [proj(c) for c in cs]
    centre = lerp3(cs[0], cs[7], 0.5)
    v = view(centre)
    edges = {}
    for idx, name in FACES:
        n = face_normal(name, dd, wv)
        if dot(n, v) <= 0.02:
            continue
        for j in range(4):
            e = tuple(sorted((idx[j], idx[(j + 1) % 4])))
            edges[e] = edges.get(e, 0) + 1
        # shade the face with even strokes along the slab, as dark as it is turned from the light
        dark = 1 - lit(n)
        if dark > 0.45 and name in SIDES:
            (p0, p1), (q0, q1) = SIDES[name]
            sp = 5.5 if dark > 0.7 else 8.0
            span = dist(proj(cs[p0])[:2], proj(cs[q0])[:2])
            nl = int(span / sp)
            for j in range(1, nl + 1):
                f = j / (nl + 1)
                s0, s1 = lerp3(cs[p0], cs[q0], f), lerp3(cs[p1], cs[q1], f)
                s0, s1 = lerp3(s0, s1, 0.06), lerp3(s0, s1, 0.94)
                draw([proj(s0), proj(s1)], 0.9 + 0.8 * (dark - 0.45), own_slab(k, h), hand=0.1, eps=0.8)
    for (i, j), cnt in edges.items():
        draw([P[i], P[j]], tz(1.2, 1.9), own_slab(k, h), hand=0.1, eps=0.8)

# ---------------------------------------------------------------- frame it

xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
SCALE = 1.12
pen.strokes = [([((x - cx) * SCALE + 500, (y - cy) * SCALE + 500) for x, y in p], w) for p, w in pen.strokes]
print('pairs', NBP)
pen.save('../04-dna.svg', mirror=False)
pen.report()
