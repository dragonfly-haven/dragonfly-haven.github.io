"""03 RNA: one strand folded back on itself into a hairpin, as an engraver would draw a
physical model of it.

The same model and hand as 04 DNA, so 03 reads as one strand and 04 as the double helix:
a single sugar-phosphate backbone as a solid round tube, its bases as thin flat slabs
standing out of it. From its 5' end at the lower right the strand comes as a loose
single-stranded tail, a gentle S with seven bases along it, evenly spaced as they stand,
whose angles open out round the bend and then rise steadily toward the tip, up into the
foot of an upright stem of eight base pairs: an A-form helix (A', twelve pairs a turn),
wider than 04's B-form, its pairs tilted, the purine of each pair the longer slab, with
one front crossing (the two pairs behind it left out, the back strand showing through
there). From the top pair the strand goes straight on round a low dome a little narrower
than the stem, flaring into it: three bases stacked on its 5' side as if the stem went
on, two near the crown pointing in and down, one flipped out on the 3' side, the middle
clear. Then it comes back down the stem as the other strand and is cut square at its 3'
end, a short stub on the left of the foot. Modelled in 3D and drawn with a depth test,
each base stopping at the backbone's outline where it plugs in and the far side of the
stem drawn lighter; light from the upper left, contour lines along the tube on its shadow
side, a few cross strokes under the bends, the slabs' dark faces lined, the cut ends
shown as cut.
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


def bend_on(p0, t0, t1, r, L, step=1.0):
    """From p0 along t0, turning at radius r onto t1, then straight on along t1 for L."""
    t0, t1 = norm(t0), norm(t1)
    ax = norm(cross(t0, t1))
    ang = math.acos(max(-1.0, min(1.0, dot(t0, t1))))
    n = max(2, int(r * ang / step))
    out, p = [p0], p0
    for j in range(n):
        p = add(p, mul(rot(t0, ax, ang * (j + 0.5) / n), r * ang / n))
        out.append(p)
    m = max(2, int(L / step))
    return out + [add(p, mul(t1, L * (j + 1) / m)) for j in range(m)]


# ---------------------------------------------------------------- the stem: A-form

AXA = math.radians(-88)                     # the stem stands upright, the head at the top
TILT = math.radians(4)                      # its upper end turned a little away from us
A3 = norm((math.cos(AXA) * math.cos(TILT), math.sin(AXA) * math.cos(TILT), -math.sin(TILT)))
X3 = norm((-math.sin(AXA), math.cos(AXA), 0.0))     # across the stem, to the right
Y3 = norm(cross(A3, X3))
if Y3[2] < 0:
    Y3 = mul(Y3, -1)
R = 118.0                                   # wider than B (04 has 100) ...
RISE = 33.0                                 # ... with 12 pairs a turn (A'-form)
BP_PER_TURN = 12.0
PITCH = RISE * BP_PER_TURN
K = -2 * math.pi / PITCH                    # right-handed, as 04
RT = 16.0                                   # the backbone tube, as 04
NSTEM = 8                                   # base pairs: 210 degrees of turn, so the foot pair and
                                            # the top pair both lie across the picture and the stem
                                            # shows one front crossing
DZ = 20.0                                   # a pair's partner on strand 2 sits this much higher: tilted pairs
DELTA = math.radians(205)                   # strand 2 round from strand 1 at one height
SEP = DELTA + K * DZ                        # the angle a pair spans round the axis
U_TOP = (NSTEM - 1) * RISE
PHI = math.radians(15)                      # strand 1 at the foot pair: on the front, to the right;
                                            # strand 2 there behind, to the left; at the top pair the
                                            # two stand at the stem's left and right edges
O = (0.0, 150.0, 0.0)                       # the foot of the stem's axis
# the head: a low dome straight off the top pair, a little narrower than the stem, its crown
# set a touch to the left and its right side further from us (coordinates across, up from the
# top pair, toward us, relative to the stem's axis)
HEAD_PTS = ((-110, 52, 34), (-94, 104, 18), (-60, 144, 2), (-10, 162, -10), (40, 150, -20), (76, 108, -28), (104, 50, -30))
# the 5' tail: drooping off the stem's foot the way the strand leaves the helix, round under
# the foot and away to the right (offsets from where it leaves the helix: right, down, toward us)
TAIL_PTS = ((-30, 54, 36), (-10, 112, 26), (52, 156, 12), (146, 172, 0), (234, 184, -8), (304, 200, -14))


def hpos(u, th, r=R):
    return add(O, mul(A3, u), mul(X3, r * math.cos(th)), mul(Y3, r * math.sin(th)))


def s1(u):
    return hpos(u, PHI + K * u)


def s2(u):
    return hpos(u, PHI + DELTA + K * u)


def dfd(f, u, sg=1):
    return norm(sub(f(u + 0.5 * sg), f(u - 0.5 * sg)))


def spline(pts, m0, m1, n=30):
    """A smooth curve through pts, leaving the first along m0 and reaching the last along m1."""
    out = [pts[0]]
    for j in range(len(pts) - 1):
        a, b = pts[j], pts[j + 1]
        ma = m0 if j == 0 else mul(sub(b, pts[j - 1]), 0.5)
        mb = m1 if j == len(pts) - 2 else mul(sub(pts[j + 2], a), 0.5)
        out += hermite(a, ma, b, mb, n)[1:]
    return out


# ---------------------------------------------------------------- the whole strand, 5' to 3'

E = 18.0                                    # the 5' strand runs on past the foot pair, then leaves
ET = 6.0                                    # at the top it runs on this little past the top pair ...
ET1 = -10.0                                 # ... on the 5' side it leaves a little below it, near the stem's
                                            # edge, so the dome's left side runs on from the helix in one convex curve
# the 5' tail, built outward from the foot and then turned round to run 5' to 3'
p5 = s1(-E)
t5 = mul(dfd(s1, -E), -1)                   # outward, toward the 5' end
TAIL = [add(p5, q) for q in TAIL_PTS]
tail = hermite(p5, mul(t5, 70), TAIL[0], mul(norm(sub(TAIL[1], p5)), 90), 30)
tail += spline(TAIL, mul(norm(sub(TAIL[1], p5)), 90), mul(sub(TAIL[-1], TAIL[-2]), 1.0))[1:]
tail = tail[::-1]
up = [s1(u) for u in [(-E) + j * 2.0 for j in range(int((U_TOP + E + ET1) / 2.0) + 1)]]
# the head: the strand leaves the top pair and goes straight on round a low dome and back
# down into the stem, the dome's foot as wide as the top pair
P1, T1 = s1(U_TOP + ET1), dfd(s1, U_TOP + ET1)
P2, T2 = s2(U_TOP + DZ + ET), dfd(s2, U_TOP + DZ + ET, -1)
HB = add(O, mul(A3, U_TOP))                 # the head's points are measured from here
HEAD = [add(HB, mul(X3, x), mul(A3, h), mul(Y3, z)) for x, h, z in HEAD_PTS]
# (each end leaves along the helix turned up toward the dome, so it bends once, into the dome;
# the right side comes down onto the 3' strand nearly in its own line, so the tube there stays
# one even thickness round into the stem)
loop = spline([P1] + HEAD + [P2], mul(norm(add(T1, mul(A3, 1.2))), 45), mul(norm(add(T2, mul(A3, -0.4))), 45))[1:]
down = [s2(u) for u in [U_TOP + DZ + ET - j * 2.0 for j in range(int((U_TOP + ET) / 2.0) + 1)]]
# the 3' end: a short stub hanging off the foot on the left, cut square; it leaves the helix in a
# smooth turn, no tighter than the helix's own turn at the stem's edge, then runs straight
pe, te = down[-1], dfd(s2, DZ, -1)
stub = bend_on(pe, te, norm(add(mul(A3, -1), mul(X3, -0.3))), 50.0, 18.0)
rough = tail + up[1:] + loop + down[1:] + stub[1:]
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


def cut_rim(smp, r=RT, n=32):
    """The rim of the square cut at a tube's end, from one side round the front (j = 0 .. n/2)
    and on round the back."""
    return [add(smp['c'], mul(smp['m'], r * math.cos(2 * math.pi * j / n)), mul(smp['w'], r * math.sin(2 * math.pi * j / n)))
            for j in range(n + 1)]


S = tube()
for i in range(0, NC - 3, 3):
    p, q = S[i], S[i + 3]
    for kind, fn in (('t', lambda smp, o: proj(surf(smp, o)[0])), ('h', occ)):
        rails = [[fn(smp, o) for o in (-1.0, -0.5, 0.0, 0.5, 1.0)] for smp in (p, q)]
        for j in range(4):
            depth.quad(rails[0][j], rails[1][j], rails[1][j + 1], rails[0][j + 1], (kind, 'r', i))
for smp in (S[0], S[-1]):                   # the cut faces, as discs
    cen = proj(smp['c'])
    rim = [proj(p) for p in cut_rim(smp, RT + HALO)]
    for a, b in zip(rim, rim[1:]):
        depth.add(cen, a, b, ('h', 'r', smp['i']))

# ---------------------------------------------------------------- the bases

SLAB_T = 6.0                                # as 04
SLAB_W = 17.0
GAP = 0.0                                   # a pair's two bases meet end to end, one line between
SEQ1 = 'GGCAUCCG'                           # the stem's 5' side, foot to top
PAIR = {'G': 'C', 'C': 'G', 'A': 'U', 'U': 'A'}
TAIL_SEQ = 'ACUAGCU'
REACH = {True: 80.0, False: 66.0}           # an unpaired purine reaches further than a pyrimidine
LOOP_REACH = {True: 64.0, False: 54.0}      # the loop's are shorter


def purine(b):
    return b in 'AG'


slabs = []                                  # (k, corners, dd, wv, tv)
PARTNER = {}                                # a stem slab's other half


def box(a0, a1, wv, tv):
    cs = []
    for end in (a0, a1):
        for sw in (-1, 1):
            for st in (-1, 1):
                cs.append(add(end, mul(wv, sw * SLAB_W), mul(tv, st * SLAB_T)))
    slabs.append((len(slabs), cs, norm(sub(a1, a0)), wv, tv))


# the stem's pairs: two slabs meeting end to end, the purine the longer. The two in the middle,
# behind the front crossing, are left out: the front strand would hide nearly all of them and
# leave only broken pieces, so the back strand shows there instead
NO_PAIR = (3, 4)
stem_idx = []
for k in range(NSTEM):
    u = k * RISE
    pa, pb = s1(u), s2(u + DZ)
    stem_idx += [nearest(pa), nearest(pb)]
    if k in NO_PAIR:
        continue
    f = 0.5 + (0.08 if purine(SEQ1[k]) else -0.08)
    m = lerp3(pa, pb, f)
    d = norm(sub(pb, pa))
    wv = norm(cross(A3, d))
    tv = norm(cross(d, wv))
    for s0, dd in ((pa, d), (pb, mul(d, -1))):
        box(add(s0, mul(dd, RT * 0.4)), add(m, mul(dd, -GAP)), wv, tv)
    PARTNER[len(slabs) - 2], PARTNER[len(slabs) - 1] = len(slabs) - 1, len(slabs) - 2


def single(i, b, roll):
    """An unpaired base standing out of the tube at sample i toward b: a thin flat slab, stacked
    along the strand (its thin side along it), its broad side turned to us, rolled a touch."""
    c, t = S[i]['c'], S[i]['t']
    dd = norm(b)
    tv0 = norm(sub(t, mul(dd, dot(t, dd))))
    wv0 = cross(dd, tv0)
    tv = add(mul(tv0, math.cos(roll)), mul(wv0, math.sin(roll)))
    wv = cross(dd, tv)
    return dd, wv, tv


ROLL = math.radians(8)                      # the same small roll on most unpaired bases: lit alike


def height(p):
    return dot(sub(p, HB), A3)


# the head's bases, unevenly placed: on its 5' side three stacked on the top pair as if the stem
# went on, two near the crown pointing in and down, one flipped out on the 3' side; the middle clear
i_top1, i_top2 = stem_idx[-2], stem_idx[-1]
i_l0, i_l1 = nearest(P1, i_top1, i_top2), nearest(P2, i_top1, i_top2)
d_top = norm(sub(s2(U_TOP + DZ), s1(U_TOP)))
wv_top = norm(cross(A3, d_top))
tv_top = norm(cross(d_top, wv_top))
for k, b in enumerate('GAA'):
    i = min(range(i_l0, (i_l0 + i_l1) // 2), key=lambda q: abs(height(C[q]) - 0.9 * RISE * (k + 1)))
    c = S[i]['c']
    box(add(c, mul(d_top, RT * 0.4)), add(c, mul(d_top, LOOP_REACH[purine(b)])), wv_top, tv_top)
HI = add(HB, mul(A3, 70), mul(X3, -20))     # a point inside the head, low
for f, b, out, turn in ((0.50, 'U', False, 0), (0.67, 'C', False, 0), (0.84, 'A', True, 30)):
    s = SARC[i_l0] + (SARC[i_l1] - SARC[i_l0]) * f
    i = min(range(i_l0, i_l1), key=lambda q: abs(SARC[q] - s))
    c = S[i]['c']
    d = norm(sub(c, HI)) if out else norm(add(norm(sub(HI, c)), mul(A3, -1.0)))   # in ones lean down
    dd, wv, tv = single(i, rot(d, norm(cross(X3, A3)), math.radians(turn)), ROLL)
    box(add(c, mul(dd, RT * 0.4)), add(c, mul(dd, LOOP_REACH[purine(b)] * (0.88 if out else 1.0))), wv, tv)

# the tail's bases, all along it from near the foot, on the side away from the stem (to the
# right going down, on top going out), evenly spaced as they stand: their middles as far apart
# round the bend, where they close up like a fan, as along the straight. Their angle to the
# strand opens out round the bend, then on the straight rises steadily from a lean toward the
# 5' end to nearly upright at the tip; all rolled so they are lit alike
i5 = stem_idx[0]
PA = [0.0]                                  # arc length along the strand in the picture, from the 5' end
for a, b in zip(C, C[1:]):
    PA.append(PA[-1] + dist(proj(a)[:2], proj(b)[:2]))
TAIL_REL = (135, 112, 86, 55, 63, 72, 80)   # each base's angle to the strand toward the 5' end, in the picture
TAIL_ROLL = (-70, -20, -25, -25, -26, -30, -30)   # each rolled so that it is lit alike: its broad side to us and
                                            # light, its thin side away from the light dark, with one line
TIP_GAP = 45.0                              # the last base this far from the 5' end, in the picture


def tail_dir(j, i):
    a, b = proj(C[min(i5, i + 3)]), proj(C[max(0, i - 3)])
    ang = math.atan2(b[1] - a[1], b[0] - a[0]) - math.radians(TAIL_REL[j])    # turned up from the strand
    return (math.cos(ang), math.sin(ang), 0.0), REACH[purine(TAIL_SEQ[::-1][j])]


def tail_mid(j, i):
    dd, L = tail_dir(j, i)
    return proj(add(C[i], mul(dd, (RT * 0.4 + L) / 2)))[:2]


def tail_place(D):
    at = [min(range(0, i5), key=lambda q: abs(SARC[q] - (SARC[i5] - 75.0)))]
    m = tail_mid(0, at[0])
    for j in range(1, len(TAIL_SEQ)):
        i = at[-1] - 1
        while i > 0 and dist(tail_mid(j, i), m) < D:
            i -= 1
        at.append(i)
        m = tail_mid(j, i)
    return at


lo_d, hi_d = 30.0, 120.0                    # the widest even spacing that still fits
for _ in range(30):
    D = (lo_d + hi_d) / 2
    if PA[tail_place(D)[-1]] >= TIP_GAP:
        lo_d = D
    else:
        hi_d = D
TAIL_AT = tail_place(lo_d)
for j, i in enumerate(TAIL_AT):
    b, L = tail_dir(j, i)
    dd, wv, tv = single(i, b, math.radians(TAIL_ROLL[j]))
    c = S[i]['c']
    box(add(c, mul(dd, RT * 0.4)), add(c, mul(dd, L)), wv, tv)

FACES = [((0, 1, 3, 2), 'root'), ((4, 6, 7, 5), 'tip'), ((0, 4, 5, 1), 'w-'), ((2, 3, 7, 6), 'w+'),
         ((0, 2, 6, 4), 't-'), ((1, 5, 7, 3), 't+')]


def face_normal(name, dd, wv, tv):
    return {'root': mul(dd, -1), 'tip': dd, 'w-': mul(wv, -1), 'w+': wv, 't-': mul(tv, -1), 't+': tv}[name]


# where each base plugs into the backbone: there the backbone is drawn whole over the base's
# root, and the base's lines stop exactly at the backbone's outline
NROOT = 45                                  # backbone samples either side of a base's root ...
NBAND = 70                                  # ... and further, where a base runs into its backbone at a slant
ROOT = {k: nearest(lerp3(cs[0], cs[3], 0.5)) for k, cs, dd, wv, tv in slabs}


def root_clip(k):
    """True for a picture point inside the backbone near the base's root."""
    i0 = ROOT[k]
    band = []
    for i in range(max(0, i0 - NBAND), min(NC, i0 + NBAND + 1)):
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


def far(z):
    """Lines on the far side of the stem, seen through it, are drawn lighter."""
    return 1.0 - 0.35 * max(0.0, min(1.0, (-0.3 * R - (z + 8.0)) / (0.6 * R)))


def tz(lo, hi):
    return lambda z: (lo + (hi - lo) * max(0.0, min(1.0, (z - ZLO) / (ZHI - ZLO)))) * far(z)


def own_tube(t, q):
    # its own surface close by, its own halo, and the bases where they plug into it (with the
    # halo of a pair's other half there, so the outline runs on unbroken past the pair's end)
    return t is not None and (
        (t[1] == 'r' and ((t[0] == 'h' and abs(t[2] - q) <= 60) or (t[0] == 't' and abs(t[2] - q) <= 9))) or
        (t[0] in 'sg' and abs(ROOT[t[1]] - q) <= NBAND) or
        (t[0] == 'g' and t[1] in PARTNER and abs(ROOT[PARTNER[t[1]]] - q) <= NBAND))


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


OPEN = 0.2                                  # a cut face turned to us at least this much shows its whole rim


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
        pts = rim if facing > OPEN else rim[:17]
        draw([proj(p) for p in pts], tzf(1.6, 2.4), own, ids=[smp['i']] * len(pts), hand=0.1)
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
                wt = 0.8 + 1.05 * min(1.0, (dark - 0.44) / 0.48) ** 1.5
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


draw_tube(S, own_tube, tz)

# ---------------------------------------------------------------- drawing: the bases

SIDES = {'t-': ((0, 4), (2, 6)), 't+': ((1, 5), (3, 7)), 'w-': ((0, 4), (1, 5)), 'w+': ((2, 6), (3, 7))}


def own_slab(k):
    # itself, its partner's halo (the two meet end to end), and the backbone's halo at its root
    pk, i0 = PARTNER.get(k), ROOT[k]
    return lambda t: t is not None and (
        (t[0] in 'sg' and (t[1] == k or (t[0] == 'g' and t[1] == pk))) or
        (t[0] == 'h' and t[1] == 'r' and abs(t[2] - i0) <= NROOT))


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
    for f in fr:                            # (a stroke left as a short piece in a corner is left out)
        a, b = lerp3(cs[p0], cs[q0], f), lerp3(cs[p1], cs[q1], f)
        draw([proj(a), proj(b)], wt, own, hand=0.0, eps=0.8, clip=clip, minlen=0.4 * dist(proj(a)[:2], proj(b)[:2]))


def face_width(P, idx):
    """A face's width on the page, square to its longest side."""
    q = [P[j][:2] for j in idx]
    area = abs(sum(q[j][0] * q[(j + 1) % 4][1] - q[(j + 1) % 4][0] * q[j][1] for j in range(4))) / 2
    return area / (max(dist(q[j], q[(j + 1) % 4]) for j in range(4)) or 1.0)


NARROW = 3.5                                # a face seen nearly edge-on is left out: no doubled lines
for k, cs, dd, wv, tv in slabs:
    P = [proj(c) for c in cs]
    v = view(lerp3(cs[0], cs[7], 0.5))
    own, clip, paired = own_slab(k), root_clip(k), k in PARTNER
    edges, broad = {}, (0.0, None)
    for idx, name in FACES:
        n = face_normal(name, dd, wv, tv)
        fw = face_width(P, idx)
        if (paired and name == 'tip') or dot(n, v) <= 0.02 or fw < NARROW:
            continue
        for j in range(4):
            e = tuple(sorted((idx[j], idx[(j + 1) % 4])))
            edges[e] = edges.get(e, 0) + 1
            if e[0] >= 4 and name in SIDES and fw > broad[0]:
                broad = (fw, e)             # where a pair meets: one straight line across its broadest face
        dark = 1 - lit(n)
        if dark > 0.45 and name in SIDES:
            face_strokes(cs, name, dark, lerp3(cs[0], cs[7], 0.5)[2] < O[2] - 0.3 * R, own, clip)
    for (i, j), cnt in edges.items():
        if paired and i >= 4 and j >= 4 and (PARTNER[k] < k or (i, j) != broad[1]):
            continue                        # the line where the pair meets, drawn once
        draw([P[i], P[j]], tz(1.2, 1.9), own, hand=0.0, eps=0.8, clip=clip)

# ---------------------------------------------------------------- frame it

xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
SCALE = 1.265                               # the backbone tube a little heavier than 04's, the figure filling the frame
WSCALE = 1.1                                # the lines scaled up with the figure (as drawn for 04 at 1.15)
NUDGE = (40.0, 0.0)                         # the head and stem are the heavier part
pen.strokes = [([((x - cx) * SCALE + 500 + NUDGE[0], (y - cy) * SCALE + 500 + NUDGE[1]) for x, y in p], min(3.0, w * WSCALE))
               for p, w in pen.strokes]
pen.save('../03-rna.svg', mirror=False)
pen.report()
