"""04 DNA: the double helix as an engraver would draw a physical model of it.

Right-handed B-DNA, ten and a half base pairs a turn, a little over two turns
on a diagonal, its upper end turned a little away from us (mild perspective).
The two sugar-phosphate backbones are solid round tubes wound on one
cylinder, offset round it so a narrow (minor) and a wide (major) groove
repeat every turn. The bases are flat slabs, two to a pair, meeting near the
middle; the pair planes lie square across the axis, so as the helix turns a
slab is seen as a bar, or tipped to show its face. Modelled in 3D and drawn
with a depth test, near parts over far ones, a hair of white where they cross;
each slab stops at its backbone's outline where it plugs in, and the backbone's lines
run on unbroken over it, and the far side, seen through the helix, is drawn lighter.
Shading as in 05 and 07: light from the upper left, contour lines along each
tube on its shadow side, heavier in the core of the shadow, a few cross strokes
under each bend, the slabs' dark faces lined. Both strands are cut square, away
from the turns, like a cut length of a model.
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

    def runs(self, pts, skip=None, eps=1.0, step=1.2, minlen=3.0, ids=None, clip=None):
        """Visible runs of a projected polyline (points (x, y, z)). With ids, skip is
        asked about (tag, id) at each point; clip hides a point outright."""
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
            if not self.hidden(p, sk, eps) and not (clip and clip(p)):
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
    # the weight, piece by piece along the line; neighbouring pieces of nearly the same weight
    # are kept as one stroke, so the line is laid in as few, long strokes as it can be
    m = max(1, int(round(total / seg)))
    groups = []
    for q in range(m):
        k0, k1 = n * q // m, n * (q + 1) // m
        z = sum(zs[k0:k1 + 1]) / (k1 - k0 + 1)
        if w is None:
            ww = sum(wl[k0:k1 + 1]) / (k1 - k0 + 1)      # the weight rides on the points
        elif callable(w):
            ww = w(z)
        else:
            ww = w
        if groups and abs(ww - groups[-1][2] / groups[-1][3]) < 0.22:
            groups[-1][1] = k1
            groups[-1][2] += ww
            groups[-1][3] += 1
        else:
            groups.append([k0, k1, ww, 1])
    for k0, k1, wsum, cnt in groups:
        piece = fine[k0:k1 + 1]
        if len(piece) >= 2:
            pen.raw(piece, max(0.6, min(3.0, wsum / cnt)))


def draw(pts, w, skip=None, eps=1.0, hand=0.25, minlen=3.0, ids=None, clip=None):
    for run in depth.runs(pts, skip, eps, minlen=minlen, ids=ids, clip=clip):
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
RT = 16.0                                   # radius of a backbone tube
DELTA = math.radians(140)                   # strand b round from strand a across the minor groove
K = -2 * math.pi / PITCH                    # right-handed (checked: the near strands rise to the right)
PHI = math.radians(100)                     # strand a's angle at u = 0
RISE = PITCH / BP_PER_TURN


def u_at(tag, deg, near):
    """The height nearest `near` where a strand stands at the angle deg round the axis."""
    base = PHI + (DELTA if tag == 'b' else 0.0)
    n = round((K * near - (math.radians(deg) - base)) / (2 * math.pi))
    return (math.radians(deg) - base + 2 * math.pi * n) / K


# The strands are cut away from the edges where they turn round (0 and 180 degrees), so
# no end hooks round a turn. Strand a, in front at both ends, starts on the front a little
# before the axis (112) and ends on the front a little past it (70), each cut turned
# nearly square to us. Strand b starts square with a, straight behind it (252), and ends
# at the back, behind the pairs (250).
U_LO = u_at('a', 112, -380)
U_HI = u_at('a', 70, U_LO + 760)
RANGE = {'a': (U_LO, U_HI), 'b': (U_LO, u_at('b', 250, U_HI - 40))}
MARGIN = 13.0                               # the end pairs sit this far inside the cuts
P_LO, P_HI = RANGE['b'][0] + MARGIN, RANGE['b'][1] - 2.4 * MARGIN   # b's top cut is oblique to the pairs
NBP = int((P_HI - P_LO) / RISE) + 1
U0 = (P_HI + P_LO) / 2 - RISE * (NBP - 1) / 2   # the pairs sit centred along the length


def pos(u, th, r=R):
    return add(mul(A3, u), mul(X3, r * math.cos(th)), mul(Y3, r * math.sin(th)))


def theta(tag, u):
    return PHI + (DELTA if tag == 'b' else 0.0) + K * u


# ---------------------------------------------------------------- backbone tubes


def tube(tag):
    """Samples along a backbone: centre, tangent, and the frame of its visible half."""
    out = []
    lo, hi = RANGE[tag]
    n = int(round((hi - lo) / 0.7))
    for j in range(n + 1):
        u = lo + (hi - lo) * j / n
        c = pos(u, theta(tag, u))
        t = norm(sub(pos(u + 0.5, theta(tag, u + 0.5)), pos(u - 0.5, theta(tag, u - 0.5))))
        v = view(c)
        m = norm(cross(t, v))               # across the tube, in the picture
        w = norm(sub(v, mul(t, dot(v, t))))  # the side of the tube facing us
        out.append(dict(u=u, c=c, t=t, m=m, w=w, i=len(out)))
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


def cut_rim(smp, r=RT, n=32):
    """The rim of the square cut at a tube's end, from one side round the front (j = 0 .. n/2)
    and on round the back."""
    return [add(smp['c'], mul(smp['m'], r * math.cos(2 * math.pi * j / n)), mul(smp['w'], r * math.sin(2 * math.pi * j / n)))
            for j in range(n + 1)]


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
    # the cut faces, as discs
    for smp in (S[0], S[-1]):
        cen = proj(smp['c'])
        rim = [proj(p) for p in cut_rim(smp, RT + HALO)]
        for a, b in zip(rim, rim[1:]):
            depth.add(cen, a, b, ('h', tag, smp['i']))

# ---------------------------------------------------------------- base slabs

SLAB_T = 6.0                                # half thickness, along the axis
SLAB_W = 17.0                               # half width, across the pair's length
GAP = 0.0                                   # the two bases of a pair meet end to end, one line between
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

# where each slab plugs into its backbone: there the backbone is drawn whole over the slab's
# root, and the slab's lines stop exactly at the backbone's outline
NROOT = 45                                  # backbone samples either side of a slab's root
ROOT = {}
for k, h, cs, dd, wv in slabs:
    S = tubes['ab'[h]]
    r0 = lerp3(cs[0], cs[3], 0.5)
    ROOT[(k, h)] = min(range(len(S)), key=lambda i: dot(sub(S[i]['c'], r0), sub(S[i]['c'], r0)))


def root_clip(k, h):
    """True for a picture point inside the slab's own backbone near its root."""
    S, i0 = tubes['ab'[h]], ROOT[(k, h)]
    band = []
    for i in range(max(0, i0 - NROOT), min(len(S), i0 + NROOT + 1)):
        c = proj(S[i]['c'])[:2]
        band.append((c, dist(c, proj(surf(S[i], 1.0)[0])[:2])))

    def clip(p):
        for (a, ra), (b, rb) in zip(band, band[1:]):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L2 = ex * ex + ey * ey or 1.0
            t = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / L2))
            if math.hypot(p[0] - a[0] - ex * t, p[1] - a[1] - ey * t) < ra + (rb - ra) * t:
                return True
        return False
    return clip

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


def far(z):
    """Lines on the far side of the helix, seen through it, are drawn lighter."""
    return 1.0 - 0.35 * max(0.0, min(1.0, (-0.3 * R - z) / (0.6 * R)))


def tz(lo, hi):
    """Weight from depth: lo at the back of the helix, hi at its front; eased on the far side."""
    return lambda z: (lo + (hi - lo) * max(0.0, min(1.0, (z / (R + RT) + 1) / 2))) * far(z)


def own_tube(tag):
    # its own surface close by, its own halo, and its own slabs (a slab reaches its own
    # backbone only where it plugs into it)
    return lambda t, q: t is not None and (
        (t[1] == tag and (t[0] == 'h' or (t[0] == 't' and abs(t[2] - q) <= 9))) or
        (t[0] in 'sg' and 'ab'[t[2]] == tag))


RAILS = (-0.725, -0.435, -0.145, 0.145, 0.435, 0.725)   # 0.29 x RT apart: over 5 on the page
BEND_R = 46.0                               # a bend: the tube's path in the picture turns tighter than this
RING = 7.5                                  # cross strokes this far apart along a bend
CROSS = 0.4                                 # a cross stroke's reach in from the outline (o, across the tube)


def bend_radius(S, i, k=8):
    a, b, c = proj(S[max(0, i - k)]['c']), proj(S[i]['c']), proj(S[min(len(S) - 1, i + k)]['c'])
    area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
    if area < 1e-6:
        return 1e9
    return dist(a[:2], b[:2]) * dist(b[:2], c[:2]) * dist(a[:2], c[:2]) / (4 * area)


def unkink(run, rid, k=3, max_turn=0.45):
    """A contour line split where it would double back on itself round a bend tighter than
    the tube is thick; the bit round the bend is left out, so it ends cleanly either side."""
    n = len(run)
    bad = [False] * n
    for i in range(k, n - k):
        a, b, c = run[i - k], run[i], run[i + k]
        t1, t2 = math.atan2(b[1] - a[1], b[0] - a[0]), math.atan2(c[1] - b[1], c[0] - b[0])
        if abs((t2 - t1 + math.pi) % (2 * math.pi) - math.pi) > max_turn:
            for j in range(max(0, i - 2 * k), min(n, i + 2 * k + 1)):
                bad[j] = True
    out, cur, cid = [], [], []
    for p, q, b in zip(run + [None], rid + [None], bad + [True]):
        if b:
            if len(cur) > 3:
                out.append((cur, cid))
            cur, cid = [], []
        else:
            cur.append(p)
            cid.append(q)
    return out


OPEN = 0.15                                 # a cut face turned to us at least this much shows its whole rim,
                                            # as a thin ellipse (strand b's top cut, a little turned to us)


def draw_tube(S, own, tzf):
    """A backbone tube: its two silhouettes, the square cuts at its ends, contour lines along
    it on the shadow side, and a few cross strokes in the core shadow under each bend."""
    ids = [s['i'] for s in S]
    for o in (-1.0, 1.0):
        draw([proj(surf(s, o)[0]) for s in S], tzf(1.8, 2.7), own, ids=ids)
    # the cuts: the rim round the front; where the cut face is turned to us the whole rim,
    # and the face hatched straight across if it is turned from the light
    for smp, sg in ((S[0], -1), (S[-1], 1)):
        fn = mul(smp['t'], sg)
        facing = dot(fn, view(smp['c']))
        rim = cut_rim(smp)
        # (the rim runs right up to a base in front of it; its back half, where it shows, finer)
        for pts, wf in ((rim[:17], tzf(1.6, 2.4)), (rim[16:] if facing > OPEN else [], tzf(1.0, 1.5))):
            if pts:
                draw([proj(p) for p in pts], wf, lambda t, q: own(t, q) or (t is not None and t[0] == 'g'),
                     ids=[smp['i']] * len(pts), hand=0.1)
        dark = 1 - lit(fn)
        if facing > OPEN and dark > 0.4:
            c = smp['c']
            Lw = dist(proj(add(c, mul(smp['w'], RT)))[:2], proj(c)[:2])
            nl = min(4, int(2 * Lw / 5.5) - 1)
            for j in range(1, nl + 1):
                y = -1 + 2 * j / (nl + 1)
                h = math.sqrt(1 - y * y) * 0.8
                a = add(c, mul(smp['w'], RT * y), mul(smp['m'], -RT * h))
                b = add(c, mul(smp['w'], RT * y), mul(smp['m'], RT * h))
                draw([proj(a), proj(b)], 0.75 + 0.4 * (dark - 0.4), own, ids=[smp['i']] * 2, hand=0.05)
    # contour lines along the tube at fixed places across it, each drawn where the surface
    # there is dark enough, heavier in the core shadow, eased at the rim (reflected light)
    for o in RAILS:
        run, rid = [], []
        for s in S + [None]:
            dark = 0.0
            if s is not None:
                p, n = surf(s, o)
                dark = 1 - lit(n)
            if dark > 0.44:
                wt = 0.8 + 1.15 * min(1.0, (dark - 0.44) / 0.48) ** 1.5
                wt = 0.8 + (wt - 0.8) * (0.55 if abs(o) > 0.7 else 1.0)
                run.append(proj(p) + (wt * far(p[2]),))
                rid.append(s['i'])
            else:
                for piece, pid in unkink(run, rid):
                    draw(piece, None, own, ids=pid, hand=0.15, minlen=8.0)
                run, rid = [], []
    # cross strokes round the tube in the core shadow on the underside of each bend:
    # two short ones, either side of the bend's tightest point, none near the ends
    cands = []
    run_len, last = 0.0, None
    for s in S[40:-40]:
        cp = proj(s['c'])
        if last is not None:
            run_len += dist(cp[:2], last[:2])
        last = cp
        if run_len < RING:
            continue
        rb = bend_radius(S, s['i'])
        if rb > BEND_R:
            continue
        arc, ao = [], []
        for j in range(49):
            o = -1 + 2 * j / 48
            p, n = surf(s, o)
            dark = 1 - lit(n)
            if dark > 0.86 and abs(o) < 0.92:
                arc.append(proj(p) + (0.7 + 0.35 * min(1.0, (dark - 0.86) / 0.2),))
                ao.append(o)
            elif len(arc) > 4:
                break
        if len(arc) > 4 and length([q[:2] for q in arc]) > 11:
            # kept short: from the shadow's edge at the outline a little way in, so it crosses
            # a contour line or so and makes no grid with them
            if abs(ao[-1]) > abs(ao[0]):
                arc, ao = arc[::-1], ao[::-1]
            if abs(ao[0]) > 0.8:
                keep = [q for q, o in zip(arc, ao) if abs(o - ao[0]) <= CROSS]
                cands.append((s['i'], rb, keep, [s['i']] * len(keep)))
                run_len = 0.0
    groups = []
    for cnd in cands:
        if groups and cnd[0] - groups[-1][-1][0] < 30:
            groups[-1].append(cnd)
        else:
            groups.append([cnd])
    for g in groups:
        if len(g) < 3:
            continue
        core = min(g, key=lambda q: q[1])[0]
        for i, rb, arc, aid in sorted(g, key=lambda q: abs(q[0] - core))[:3:2]:   # two, one apart
            draw(arc, None, own, ids=aid, hand=0.08)


for tag, S in tubes.items():
    draw_tube(S, own_tube(tag), tz)

# ---------------------------------------------------------------- drawing: the slabs


# the long sides of the faces that run along a slab: strokes go from one to the other
SIDES = {'t-': ((0, 4), (2, 6)), 't+': ((1, 5), (3, 7)), 'w-': ((0, 4), (1, 5)), 'w+': ((2, 6), (3, 7))}


def own_slab(k, h):
    # itself, its partner's halo (the two meet end to end), and its backbone's halo
    tag = 'ab'[h]
    return lambda t: t is not None and (
        (t[0] in 'sg' and t[1] == k and (t[2] == h or t[0] == 'g')) or (t[0] == 'h' and t[1] == tag))


def face_strokes(cs, name, dark, far, own, clip):
    """Even strokes along a slab's dark side face: two or three that stay parallel and at
    least 5 apart, else one heavier line down its middle; fewer on the far side."""
    (p0, p1), (q0, q1) = SIDES[name]
    # the face's width on the page square to its long edges (a face seen slantwise is narrow
    # there however long its short edges look)
    P0, P1, Q0, Q1 = (proj(cs[j])[:2] for j in (p0, p1, q0, q1))
    ex, ey = P1[0] - P0[0], P1[1] - P0[1]
    L = math.hypot(ex, ey) or 1.0
    spa = abs(ex * (Q0[1] - P0[1]) - ey * (Q0[0] - P0[0])) / L
    spb = abs(ex * (Q1[1] - P1[1]) - ey * (Q1[0] - P1[0])) / L
    lo, hi = min(spa, spb), max(spa, spb)
    if not far and lo >= 16.5 and hi <= 1.3 * lo:
        fr, wt = [1 / 3, 2 / 3], 0.9 + 0.3 * (dark - 0.45)
    elif lo >= 7.0 and dark > (0.8 if far else 0.6):     # room for it clear of the edges
        fr, wt = [0.5], (0.95 if far else 1.0)
    else:
        return
    for f in fr:
        a, b = lerp3(cs[p0], cs[q0], f), lerp3(cs[p1], cs[q1], f)
        draw([proj(a), proj(b)], wt, own, hand=0.0, eps=0.8, clip=clip)


def face_width(P, idx):
    """A face's width on the page, square to its longest side."""
    q = [P[j][:2] for j in idx]
    area = abs(sum(q[j][0] * q[(j + 1) % 4][1] - q[(j + 1) % 4][0] * q[j][1] for j in range(4))) / 2
    return area / (max(dist(q[j], q[(j + 1) % 4]) for j in range(4)) or 1.0)


NARROW = 3.5                                # a face seen nearly edge-on is left out: no doubled lines ...
THIN = 2.1                                  # ... but on the pairs turned most toward us of those seen only as
                                            # bars, a broad face down to this is drawn as one fine line, its far
                                            # edge, so they read as plates too


def broad_width(k, h, cs, dd, wv):
    """The page width of a slab's broad face (along the axis) where it is turned to us."""
    P, v = [proj(c) for c in cs], view(lerp3(cs[0], cs[7], 0.5))
    return max([face_width(P, idx) for idx, name in FACES if name[0] == 't' and len(name) == 2 and
                dot(face_normal(name, dd, wv), v) > 0.02] + [0.0])


PLATE = set()                               # the pairs whose broad faces are drawn as fine lines
for k in range(NBP):
    ws = [broad_width(*sl) for sl in slabs if sl[0] == k]
    if min(ws) >= THIN and min(ws) < NARROW:
        PLATE.add(k)
for k, h, cs, dd, wv in slabs:
    P = [proj(c) for c in cs]
    centre = lerp3(cs[0], cs[7], 0.5)
    v = view(centre)
    own, clip = own_slab(k, h), root_clip(k, h)
    edges, broad, thin = {}, (0.0, None), []
    for idx, name in FACES:
        n = face_normal(name, dd, wv)
        fw = face_width(P, idx)
        if name == 'tip' or dot(n, v) <= 0.02:
            continue
        if k in PLATE and name[0] == 't' and len(name) == 2:
            thin.append(SIDES[name])        # both halves of the pair alike
            continue
        if fw < NARROW:
            continue
        for j in range(4):
            e = tuple(sorted((idx[j], idx[(j + 1) % 4])))
            edges[e] = edges.get(e, 0) + 1
            if e[0] >= 4 and name in SIDES and fw > broad[0]:
                broad = (fw, e)             # where the pair meets: one straight line across its broadest face
        # shade the face with even strokes along the slab, as dark as it is turned from the light
        dark = 1 - lit(n)
        if dark > 0.45 and name in SIDES:
            face_strokes(cs, name, dark, centre[2] < -0.3 * R, own, clip)
    for (i, j), cnt in edges.items():
        if i >= 4 and j >= 4 and (h == 1 or (i, j) != broad[1]):
            continue                        # the line where the pair meets, drawn once
        draw([P[i], P[j]], tz(1.2, 1.9), own, hand=0.0, eps=0.8, clip=clip)
    for side in thin:                       # a narrow broad face: only its far long edge, fine
        for i, j in side:
            if (i, j) not in edges:
                draw([P[i], P[j]], lambda z: 0.65 * far(z), own, hand=0.0, eps=0.8, clip=clip)

# ---------------------------------------------------------------- frame it

xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
SCALE = 1.18                                # the backbone tube about 19 wide on the page in 03 and 04
pen.strokes = [([((x - cx) * SCALE + 500, (y - cy) * SCALE + 500) for x, y in p], w) for p, w in pen.strokes]
print('pairs', NBP)
pen.save('../04-dna.svg', mirror=False)
pen.report()
