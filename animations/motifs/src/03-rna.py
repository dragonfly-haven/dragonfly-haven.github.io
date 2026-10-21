"""03 RNA: one strand folded on itself, as an engraver would draw a physical model of it.

The same model and hand as 04 DNA, so 03 reads as one strand and 04 as the double
helix. A single sugar-phosphate backbone as a solid round tube, its bases as flat
slabs standing out of it. The strand runs from a 5' stub up a short stem of eight
base pairs, an A-form helix (eleven pairs a turn: wider and more compact than 04's
B-form, its pairs tilted), rounds a loop of five unpaired bases over the top pair,
comes back down the stem and leaves its foot as a loose single-stranded 3' tail,
its bases turned gently along it. Modelled in 3D and drawn with a depth test; light
from the upper left, contour hatching along the tube on its shadow side, crossed in
the broad shadows, parallel strokes on the slabs' dark faces.
"""

import math

from pen import Pen, dist, lerp, length, resample

pen = Pen(seed=303)

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



# ---------------------------------------------------------------- 3D curve helpers


def resample3(pts, step):
    out = [pts[0]]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.sqrt(dot(sub(b, a), sub(b, a)))
        s = step - carry
        while s <= L:
            out.append(lerp3(a, b, s / L))
            s += step
        carry = L - (s - step)
    if dist(out[-1][:2], pts[-1][:2]) > step * 0.3:
        out.append(pts[-1])
    return out


def smooth3(pts, k, passes=2):
    for _ in range(passes):
        n = len(pts)
        new = []
        for i in range(n):
            j0, j1 = max(0, i - k), min(n - 1, i + k)
            h = min(i - j0, j1 - i)            # symmetric window: the ends stay put
            seg = pts[i - h:i + h + 1]
            new.append(tuple(sum(c) / len(seg) for c in zip(*seg)))
        pts = new
    return pts


def hermite(p0, m0, p1, m1, n=40):
    out = []
    for j in range(n + 1):
        t = j / n
        h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        out.append(add(mul(p0, h00), mul(m0, h10), mul(p1, h01), mul(m1, h11)))
    return out


def rot(v, axis, a):
    """v turned by a about the unit axis (Rodrigues)."""
    return add(mul(v, math.cos(a)), mul(cross(axis, v), math.sin(a)), mul(axis, dot(axis, v) * (1 - math.cos(a))))


# ---------------------------------------------------------------- the stem: A-form

AXA = math.radians(-62)                     # the stem rises up to the right in the picture
TILT = math.radians(4)                      # its upper end turned a little away from us
A3 = norm((math.cos(AXA) * math.cos(TILT), math.sin(AXA) * math.cos(TILT), -math.sin(TILT)))
X3 = norm((-math.sin(AXA), math.cos(AXA), 0.0))
Y3 = norm(cross(A3, X3))
if Y3[2] < 0:
    Y3 = mul(Y3, -1)
R = 118.0                                   # wider than B (04 has 100) ...
PITCH = 308.0                               # ... and more compact: 11 pairs a turn, 2.8 A each
BP_PER_TURN = 11.0
RISE = PITCH / BP_PER_TURN
K = -2 * math.pi / PITCH                    # right-handed, as 04
RT = 16.0                                   # the backbone tube, as 04
NSTEM = 8                                   # base pairs in the stem
DZ = 34.0                                   # a pair's partner on strand 2 sits this much higher: tilted pairs
DELTA = math.radians(155)                   # strand 2 round from strand 1 at one height
SEP = DELTA + K * DZ                        # the angle a pair spans round the axis
U_TOP = (NSTEM - 1) * RISE
PHI = math.radians(90) - SEP / 2 - K * U_TOP   # the top pair lies square to our view, the loop above it
O = (-150.0, 170.0, 0.0)                    # the foot of the stem's axis


def hpos(u, th, r=R):
    return add(O, mul(A3, u), mul(X3, r * math.cos(th)), mul(Y3, r * math.sin(th)))


def s1(u):
    return hpos(u, PHI + K * u)


def s2(u):
    return hpos(u, PHI + DELTA + K * u)


def dfd(f, u, sg=1):
    return norm(sub(f(u + 0.5 * sg), f(u - 0.5 * sg)))


# ---------------------------------------------------------------- the whole strand, 5' to 3'

E = 26.0                                    # the strand runs on a little past the end pairs
# 5' end: one unpaired nucleotide below the stem
p5 = s1(-E)
t5 = dfd(s1, -E)
stub = hermite(add(p5, mul(t5, -40), mul(A3, -40), mul(X3, -12)), mul(norm(add(t5, mul(A3, 0.4))), 70), p5, mul(t5, 70), 20)
up = [s1(u) for u in [(-E) + j * 2.0 for j in range(int((U_TOP + 2 * E) / 2.0) + 1)]]
# the loop over the top pair
P1, T1 = s1(U_TOP + E), dfd(s1, U_TOP + E)
P2, T2 = s2(U_TOP + DZ + E), dfd(s2, U_TOP + DZ + E, -1)
mid_top = lerp3(P1, P2, 0.5)
LOOP_H = 150.0
PM = add(mid_top, mul(A3, LOOP_H), mul(Y3, 25))
TM = mul(norm(sub(P2, P1)), 190)
loop = hermite(P1, mul(T1, 170), PM, TM, 40)[1:] + hermite(PM, TM, P2, mul(T2, 170), 40)[1:]
down = [s2(u) for u in [U_TOP + DZ + E - j * 2.0 for j in range(int((U_TOP + 2 * E) / 2.0) + 1)]]
# the 3' tail: out of the stem's foot, round to the right in one long easy sweep
pe = down[-1]
te = dfd(s2, DZ - E, -1)
TAIL = [add(O, q) for q in ((60, 250, 50), (260, 330, 30), (470, 270, 0), (610, 120, -20), (660, -60, -30))]
tail = hermite(pe, mul(te, 160), TAIL[0], mul(norm(sub(TAIL[1], pe)), 220), 30)[1:]
for a, b, c0, c1 in zip(TAIL, TAIL[1:], [None] + TAIL, TAIL[2:] + [None]):
    ma = mul(sub(b, c0 if c0 else a), 0.5 if c0 else 1.0)
    mb = mul(sub(c1 if c1 else b, a), 0.5 if c1 else 1.0)
    tail += hermite(a, ma, b, mb, 30)[1:]
rough = stub + up[1:] + loop + down[1:] + tail
C = smooth3(resample3(rough, 1.4), 6)
NC = len(C)

# arc length along it
SARC = [0.0]
for a, b in zip(C, C[1:]):
    SARC.append(SARC[-1] + math.sqrt(dot(sub(b, a), sub(b, a))))


def nearest(p, lo=0, hi=None):
    hi = NC if hi is None else hi
    return min(range(lo, hi), key=lambda i: dot(sub(C[i], p), sub(C[i], p)))


# ---------------------------------------------------------------- the tube

def tube():
    out = []
    for i, c in enumerate(C):
        t = norm(sub(C[min(NC - 1, i + 2)], C[max(0, i - 2)]))
        v = view(c)
        m = norm(cross(t, v))
        w = norm(sub(v, mul(t, dot(v, t))))
        out.append(dict(c=c, t=t, m=m, w=w, i=i))
    return out


def surf(smp, o):
    n = add(mul(smp['m'], o), mul(smp['w'], math.sqrt(max(0.0, 1 - o * o))))
    return add(smp['c'], mul(n, RT)), n


HALO = 3.0


def occ(smp, o):
    p, n = surf(smp, o)
    q = proj(add(smp['c'], mul(n, RT + HALO)))
    return (q[0], q[1], proj(p)[2])


def cap_dir(smp, sg):
    n2 = norm(cross(view(smp['c']), smp['m']))
    return n2 if dot(n2, smp['t']) * sg > 0 else mul(n2, -1)


S = tube()
for i in range(0, NC - 3, 3):
    p, q = S[i], S[i + 3]
    for kind, fn in (('t', lambda smp, o: proj(surf(smp, o)[0])), ('h', occ)):
        rails = [[fn(smp, o) for o in (-1.0, -0.5, 0.0, 0.5, 1.0)] for smp in (p, q)]
        for j in range(4):
            depth.quad(rails[0][j], rails[1][j], rails[1][j + 1], rails[0][j + 1], (kind, 'r', i))
for smp, sg in ((S[0], -1), (S[-1], 1)):
    e = cap_dir(smp, sg)
    front = proj(add(smp['c'], mul(smp['w'], RT)))
    rim = [proj(add(smp['c'], mul(smp['m'], (RT + HALO) * math.cos(math.pi * j / 12)),
                    mul(e, (RT + HALO) * math.sin(math.pi * j / 12)))) for j in range(13)]
    for a, b in zip(rim, rim[1:]):
        depth.add(front, a, b, ('h', 'r', smp['i']))

# ---------------------------------------------------------------- the bases

SLAB_T = 6.0                                # as 04
SLAB_W = 17.0
GAP = 2.0
SEQ1 = 'GGCAUCGC'                           # the stem's 5' side, foot to top
PAIR = {'G': 'C', 'C': 'G', 'A': 'U', 'U': 'A'}
LOOP_SEQ = 'GAAAU'
TAIL_SEQ = 'ACCUAGUCA'
REACH = {True: 92.0, False: 76.0}           # an unpaired purine reaches further than a pyrimidine


def purine(b):
    return b in 'AG'


slabs = []                                  # (k, corners, dd, wv, tv)


def box(a0, a1, wv, tv):
    cs = []
    for end in (a0, a1):
        for sw in (-1, 1):
            for st in (-1, 1):
                cs.append(add(end, mul(wv, sw * SLAB_W), mul(tv, st * SLAB_T)))
    slabs.append((len(slabs), cs, norm(sub(a1, a0)), wv, tv))


# the stem's pairs: two slabs meeting end to end, the purine the longer
stem_idx = []
for k in range(NSTEM):
    u = k * RISE
    pa, pb = s1(u), s2(u + DZ)
    stem_idx += [nearest(pa), nearest(pb)]
    f = 0.5 + (0.08 if purine(SEQ1[k]) else -0.08)
    m = lerp3(pa, pb, f)
    d = norm(sub(pb, pa))
    wv = norm(cross(A3, d))
    tv = norm(cross(d, wv))
    for s0, dd in ((pa, d), (pb, mul(d, -1))):
        box(add(s0, mul(dd, RT * 0.4)), add(m, mul(dd, -GAP)), wv, tv)


def single(i, b, roll):
    """An unpaired base standing out of the tube at sample i, toward b, turned by roll about itself."""
    c, t = S[i]['c'], S[i]['t']
    dd = norm(sub(b, mul(t, dot(b, t))))
    tv0 = norm(sub(t, mul(dd, dot(t, dd))))
    wv0 = cross(dd, tv0)
    tv = add(mul(tv0, math.cos(roll)), mul(wv0, math.sin(roll)))
    wv = cross(dd, tv)
    return dd, wv, tv


# loop bases, evenly along the loop, pointing in toward its middle
i_top1, i_top2 = stem_idx[-2], stem_idx[-1]
QC = add(mid_top, mul(A3, LOOP_H * 0.42))
for j, b in enumerate(LOOP_SEQ):
    s = SARC[i_top1] + (SARC[i_top2] - SARC[i_top1]) * (j + 1) / (len(LOOP_SEQ) + 1)
    i = min(range(i_top1, i_top2), key=lambda q: abs(SARC[q] - s))
    dd, wv, tv = single(i, sub(QC, S[i]['c']), math.radians(25 * math.sin(1.3 * j + 0.4)))
    c = S[i]['c']
    box(add(c, mul(dd, RT * 0.4)), add(c, mul(dd, REACH[purine(b)] * 0.86)), wv, tv)

# the 5' nucleotide on its stub, and the 3' tail's bases, outward, turning gently along it
i5 = stem_idx[0]
i_end2 = stem_idx[1]
SP_NT = 64.0
singles = [(nearest(s1(-E - 30), 0, i5), 'A', mul(A3, -1), 0.0)]
s = SARC[i_end2] + SP_NT
j = 0
while s < SARC[-1] - 30 and j < len(TAIL_SEQ):
    i = min(range(i_end2, NC), key=lambda q: abs(SARC[q] - s))
    t = S[i]['t']
    out = norm(cross(t, (0, 0, 1)))         # across the strand in the picture ...
    if dot(out, sub(S[i]['c'], add(O, (330, 0, 0)))) < 0:
        out = mul(out, -1)                  # ... to the outside of its sweep
    out = rot(out, t, math.radians(38 * math.sin(0.9 * j + 0.3)))
    singles.append((i, TAIL_SEQ[j], out, math.radians(30 * math.cos(0.8 * j))))
    s += SP_NT
    j += 1
for i, b, direction, roll in singles:
    dd, wv, tv = single(i, direction, roll)
    c = S[i]['c']
    box(add(c, mul(dd, RT * 0.4)), add(c, mul(dd, REACH[purine(b)])), wv, tv)

FACES = [((0, 1, 3, 2), 'root'), ((4, 6, 7, 5), 'tip'), ((0, 4, 5, 1), 'w-'), ((2, 3, 7, 6), 'w+'),
         ((0, 2, 6, 4), 't-'), ((1, 5, 7, 3), 't+')]


def face_normal(name, dd, wv, tv):
    return {'root': mul(dd, -1), 'tip': dd, 'w-': mul(wv, -1), 'w+': wv, 't-': mul(tv, -1), 't+': tv}[name]


for k, cs, dd, wv, tv in slabs:
    P = [proj(c) for c in cs]
    for idx, name in FACES:
        depth.quad(P[idx[0]], P[idx[1]], P[idx[2]], P[idx[3]], ('s', k, 0))
    G = []
    for j, c in enumerate(cs):
        sw, st = (1 if j & 2 else -1), (1 if j & 1 else -1)
        q = proj(add(c, mul(wv, sw * HALO), mul(tv, st * HALO)))
        G.append((q[0], q[1], proj(c)[2]))
    for idx, name in FACES:
        depth.quad(G[idx[0]], G[idx[1]], G[idx[2]], G[idx[3]], ('g', k, 0))

# ---------------------------------------------------------------- drawing: the tube

ZS = [c[2] for c in C]
ZLO, ZHI = min(ZS) - RT, max(ZS) + RT


def lit(n):
    return max(0.0, dot(n, LIGHT))


def tz(lo, hi):
    return lambda z: lo + (hi - lo) * max(0.0, min(1.0, (z - ZLO) / (ZHI - ZLO)))


def own_tube(t, q):
    return t is not None and t[1] == 'r' and (
        (t[0] == 'h' and abs(t[2] - q) <= 60) or (t[0] == 't' and abs(t[2] - q) <= 9))


ids = [s['i'] for s in S]
for o in (-1.0, 1.0):
    draw([proj(surf(s, o)[0]) for s in S], tz(1.8, 2.7), own_tube, ids=ids)
for smp, sg in ((S[0], -1), (S[-1], 1)):
    e = cap_dir(smp, sg)
    pts = [proj(add(smp['c'], mul(smp['m'], RT * math.cos(math.pi * j / 16)), mul(e, RT * math.sin(math.pi * j / 16))))
           for j in range(17)]
    draw(pts, tz(1.8, 2.6), own_tube, ids=[smp['i']] * len(pts))
ease = int(RT * 0.9 / 1.4)
for o in (-0.7, -0.35, 0.0, 0.35, 0.7):
    run, rid = [], []
    for s in S[ease // 2:-(ease // 2)] + [None]:
        dark = 0.0
        if s is not None:
            p, n = surf(s, o)
            dark = 1 - lit(n)
        if dark > 0.52:
            wt = 0.85 + 1.5 * min(1.0, (dark - 0.52) / 0.4) ** 1.5
            wt = 0.85 + (wt - 0.85) * (0.55 if abs(o) > 0.7 else 1.0)
            fade = min(s['i'], NC - 1 - s['i']) / ease
            if fade < 1:
                wt = 0.7 + (wt - 0.7) * max(0.0, fade)
            run.append(proj(p) + (wt,))
            rid.append(s['i'])
        else:
            if len(run) > 3:
                draw(run, None, own_tube, ids=rid, hand=0.15)
            run, rid = [], []
RING = 7.5
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
            arc.append(proj(p) + (0.7 + 0.35 * min(1.0, (dark - 0.86) / 0.2),))
            aid.append(s['i'])
        elif len(arc) > 2:
            break
    if len(arc) > 2 and length([q[:2] for q in arc]) > 11:
        draw(arc, None, own_tube, ids=aid, hand=0.08)
        run_len = 0.0

# ---------------------------------------------------------------- drawing: the bases

SIDES = {'t-': ((0, 4), (2, 6)), 't+': ((1, 5), (3, 7)), 'w-': ((0, 4), (1, 5)), 'w+': ((2, 6), (3, 7))}


def own_slab(k):
    return lambda t: t is not None and t[0] in 'sg' and t[1] == k


for k, cs, dd, wv, tv in slabs:
    P = [proj(c) for c in cs]
    v = view(lerp3(cs[0], cs[7], 0.5))
    edges = {}
    for idx, name in FACES:
        n = face_normal(name, dd, wv, tv)
        if dot(n, v) <= 0.02:
            continue
        for j in range(4):
            e = tuple(sorted((idx[j], idx[(j + 1) % 4])))
            edges[e] = edges.get(e, 0) + 1
        dark = 1 - lit(n)
        if dark > 0.45 and name in SIDES:
            (p0, p1), (q0, q1) = SIDES[name]
            sp = 5.5 if dark > 0.7 else 8.0
            span = dist(proj(cs[p0])[:2], proj(cs[q0])[:2])
            nl = int(span / sp)
            for j in range(1, nl + 1):
                f = j / (nl + 1)
                a, b = lerp3(cs[p0], cs[q0], f), lerp3(cs[p1], cs[q1], f)
                a, b = lerp3(a, b, 0.06), lerp3(a, b, 0.94)
                draw([proj(a), proj(b)], 0.9 + 0.8 * (dark - 0.45), own_slab(k), hand=0.1, eps=0.8)
    for (i, j), cnt in edges.items():
        draw([P[i], P[j]], tz(1.2, 1.9), own_slab(k), hand=0.1, eps=0.8)

# ---------------------------------------------------------------- frame it

xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
SCALE = 1.12                                # as 04: the same tube on the page
NUDGE = (0.0, 0.0)
pen.strokes = [([((x - cx) * SCALE + 500 + NUDGE[0], (y - cy) * SCALE + 500 + NUDGE[1]) for x, y in p], w)
               for p, w in pen.strokes]
pen.save('../03-rna.svg', mirror=False)
pen.report()
