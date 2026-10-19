"""04 DNA: the double helix, drawn as a precise textbook engraving.

Right-handed B-DNA on a diagonal: two sugar-phosphate backbones as flat
ribbons of constant width wound on one cylinder, at constant radius and
pitch; ten base pairs a turn as evenly spaced bars across the helix, each
split at its middle (one base from each strand); the strands offset round
the helix so a wide (major) and a narrow (minor) groove repeat identically
every turn. Modelled in 3D and drawn front to back with a depth test. The
far side of each ribbon, seen through the helix, carries even parallel
hatching; the near side is left clean. Both strands end square at the same
base pair. Sure, low-wobble lines without lifts: the set's diagram hand
(see 03 RNA, its pair).
"""

import math

from pen import Pen, dist, lerp, inside, length, resample

pen = Pen(seed=404)

# ---------------------------------------------------------------- 3D helpers


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def mul(v, k):
    return tuple(c * k for c in v)


def norm(v):
    L = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / L for c in v)


def lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


class Depth:
    """Occluders with depth: a 2D polygon, its depth (z, larger is nearer) and a tag.
    A point is hidden when it falls inside a nearer polygon not excused by its tag."""

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

    def runs(self, pts3, skip=None, eps=0.8, step=1.2, force=(), minlen=3.0, ids=None):
        """Visible runs of a 3D polyline, as lists of (x, y, z). With `ids` (a number per
        point, such as its sample index), skip is asked about (tag, id) for each point."""
        fine, fid = [], []
        for i in range(len(pts3) - 1):
            a, b = pts3[i], pts3[i + 1]
            n = max(1, int(dist(a, b) / step))
            for j in range(n):
                fine.append(lerp3(a, b, j / n))
                fid.append(ids[i] + (ids[i + 1] - ids[i]) * j / n if ids else None)
        fine.append(pts3[-1])
        fid.append(ids[-1] if ids else None)
        out, cur = [], []
        for p, q in zip(fine, fid):
            hid = any(bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3] and inside(p[:2], poly) for poly, bb in force)
            sk = skip if q is None else (lambda t, q=q: skip(t, q))
            if not hid and not self.hidden(p[:2], p[2], sk, eps):
                cur.append(p)
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return [r for r in out if length([q[:2] for q in r]) > minlen]


# ---------------------------------------------------------------- the sure line


def ink(pts3, wz, hand=0.2, seg=26.0):
    """A sure line through 3D points: a faint slow wobble, no lifts, and a weight
    that follows depth smoothly (wz maps z to a weight)."""
    pts = [p[:2] for p in pts3]
    total = length(pts)
    if total < 1.0:
        return
    n = max(2, int(total / 1.5))
    fine, zs = [], []
    # resample in step with the depths
    acc = [0.0]
    for i in range(1, len(pts)):
        acc.append(acc[-1] + dist(pts[i - 1], pts[i]))
    j = 0
    for k in range(n + 1):
        s = total * k / n
        while j < len(pts) - 2 and acc[j + 1] < s:
            j += 1
        t = (s - acc[j]) / ((acc[j + 1] - acc[j]) or 1)
        fine.append(lerp(pts[j], pts[j + 1], t))
        zs.append(pts3[j][2] + (pts3[j + 1][2] - pts3[j][2]) * t)
    if hand > 0:
        ph, fq = pen.r(0, 6.3), pen.r(0.005, 0.01)
        moved = []
        for k, p in enumerate(fine):
            s = total * k / n
            a, b = fine[max(0, k - 1)], fine[min(n, k + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            off = hand * math.sin(s * fq * 2 * math.pi + ph) * min(1.0, s / 10, (total - s) / 10)
            moved.append((p[0] + dy / L * off, p[1] - dx / L * off))
        fine = moved
    m = max(1, int(round(total / seg)))
    for q in range(m):
        k0, k1 = n * q // m, n * (q + 1) // m
        piece = fine[k0:k1 + 1]
        if len(piece) >= 2:
            pen.raw(piece, wz(sum(zs[k0:k1 + 1]) / (k1 - k0 + 1)))


def zw(lo, hi):
    """Weight from depth: lo at the back of the helix, hi at its front."""
    return lambda z: lo + (hi - lo) * max(0.0, min(1.0, (z / R + 1) / 2))


# ---------------------------------------------------------------- the helix

AXA = math.radians(-46)                     # the axis runs up to the right
A = (math.cos(AXA), math.sin(AXA))          # up the helix, in the picture
X = (-A[1], A[0])                           # across it, down to the right
CEN = (500, 500)
PITCH = 368.0                               # one turn along the axis
R = 116.0                                   # backbone radius
HW = 14.0                                   # half width of a ribbon
BP_PER_TURN = 10
TURNS = 2.5
DELTA = math.radians(132)                   # strand b leads strand a round the helix: minor groove 132 deg
K = -2 * math.pi / PITCH                    # right-handed: theta falls as u rises (z toward us)
PHI = math.radians(114)                     # strand a's angle at the lower end: each end has one
                                            # strand in front and the other straight behind it
BAR = 'bar'                                 # a base pair as a rod (one heavy line) or an outlined bar
RT = 1.8 if BAR == 'rod' else 5.0          # half thickness of a base pair, along the axis
U_LO, U_HI = -TURNS * PITCH / 2, TURNS * PITCH / 2


def pos(u, th, r=R):
    """3D point (x, y, z) at axis position u, angle th, radius r; z is toward us."""
    return (CEN[0] + A[0] * u + X[0] * r * math.cos(th),
            CEN[1] + A[1] * u + X[1] * r * math.cos(th),
            r * math.sin(th))


def theta(tag, u):
    return PHI + (DELTA if tag == 'b' else 0.0) + K * (u - U_LO)


def frame(u, th):
    """Ribbon centre, unit half-width vector W (in the cylinder's surface, square across
    the strand) and the outward normal N."""
    c = pos(u, th)
    a3 = (A[0], A[1], 0.0)
    e_th = (-math.sin(th) * X[0], -math.sin(th) * X[1], math.cos(th))
    W = norm(add(mul(a3, -R * K), e_th))
    N = (math.cos(th) * X[0], math.cos(th) * X[1], math.sin(th))
    return c, W, N


EXT = 60.0                                  # sampled a little past each end, then cut square


def strand(tag):
    n = int((U_HI - U_LO + 2 * EXT) / 1.2)
    S = []
    for i in range(n + 1):
        u = U_LO - EXT + (U_HI - U_LO + 2 * EXT) * i / n
        th = theta(tag, u)
        c, W, N = frame(u, th)
        S.append(dict(u=u, th=th, c=c, W=W, N=N, e1=add(c, mul(W, HW)), e2=add(c, mul(W, -HW)), i=i))
    return S


def span(S, key):
    """Indices of the first and last points of an edge, each on its cut line."""
    idx = [k for k, smp in enumerate(S) if not smp.get('cut_' + key)]
    return idx[0] - 1, idx[-1] + 1


strands = {'a': strand('a'), 'b': strand('b')}

# Both strands end at the same height, each cut square across its own ribbon as it lies in
# the picture: points past the cut are pulled back onto it, so the ribbon ends on one straight
# line. With PHI as set, at each end one strand lies in front and the other straight behind it.


def cut_end(S, uend, sgn):
    j = min(range(len(S)), key=lambda k: abs(S[k]['u'] - uend))
    p, q = S[j - 3]['c'], S[j + 3]['c']
    t = norm((q[0] - p[0], q[1] - p[1]))
    t = (t[0] * sgn, t[1] * sgn)
    ce = S[j]['c']
    for smp in S:
        if abs(smp['u'] - uend) > EXT + 20:
            continue
        for key in ('e1', 'e2', 'c'):
            e = smp[key]
            s = (e[0] - ce[0]) * t[0] + (e[1] - ce[1]) * t[1]
            if s > 0:
                smp[key] = (e[0] - t[0] * s, e[1] - t[1] * s, e[2])
                smp['cut_' + key] = True


for uend, sgn in ((U_LO, -1), (U_HI, 1)):
    for S in strands.values():
        cut_end(S, uend, sgn)


depth = Depth()
QSTEP = 3
quads = {'a': [], 'b': []}
for tag, S in strands.items():
    for i in range(0, len(S) - 1, QSTEP):
        p, q = S[i], S[min(len(S) - 1, i + QSTEP)]
        if all(x.get('cut_e1') and x.get('cut_e2') for x in (p, q)):
            continue                        # past the end: nothing left of the ribbon here
        poly3 = [p['e1'], q['e1'], q['e2'], p['e2']]
        poly = [c[:2] for c in poly3]
        z = sum(c[2] for c in poly3) / 4
        depth.add(poly, z, (tag, i))
        xs = [c[0] for c in poly]
        ys = [c[1] for c in poly]
        quads[tag].append((i, poly, (min(xs), min(ys), max(xs), max(ys))))

# ---------------------------------------------------------------- base pairs

RISE = PITCH / BP_PER_TURN
NBP = int(round(TURNS * BP_PER_TURN))
GAP = 4.0                                   # half the gap where the two bases of a pair meet
a3 = (A[0], A[1], 0.0)
pairs = []
for k in range(NBP):
    u = U_LO + RISE * (k + 0.5)
    pa, pb = pos(u, theta('a', u)), pos(u, theta('b', u))
    m = lerp3(pa, pb, 0.5)
    d = norm(tuple(y - x for x, y in zip(pa, pb)))
    halves = []
    for s, e in ((pa, add(m, mul(d, -GAP))), (pb, add(m, mul(d, GAP)))):
        halves.append([add(s, mul(a3, RT)), add(e, mul(a3, RT)), add(e, mul(a3, -RT)), add(s, mul(a3, -RT))])
    pairs.append((u, halves))
    for h, quad in enumerate(halves):
        nseg = 6
        for j in range(nseg):
            c0 = lerp3(quad[0], quad[1], j / nseg)
            c1 = lerp3(quad[0], quad[1], (j + 1) / nseg)
            c2 = lerp3(quad[3], quad[2], (j + 1) / nseg)
            c3 = lerp3(quad[3], quad[2], j / nseg)
            depth.add([c0[:2], c1[:2], c2[:2], c3[:2]], (c0[2] + c1[2] + c2[2] + c3[2]) / 4, ('p', k))


def root_band(tag, u):
    """The patch of ribbon a base is fixed to: the bar is tucked under it, front or back."""
    S = strands[tag]
    i = (u - S[0]['u']) / (S[-1]['u'] - S[0]['u']) * (len(S) - 1)
    return [(poly, bb) for j, poly, bb in quads[tag] if abs(j - i) <= 14]


def own(tag, i, win):
    return lambda t: t is not None and t[0] == tag and abs(t[1] - i) <= win


def draw3(pts3, wz, skip=None, eps=0.8, force=(), hand=0.2, minlen=3.0, ids=None):
    for run in depth.runs(pts3, skip, eps, force=force, minlen=minlen, ids=ids):
        ink(run, wz, hand=hand)


# ---------------------------------------------------------------- ribbon edges and ends

EDGE = zw(1.7, 2.7)
for tag, S in strands.items():
    for key in ('e1', 'e2'):
        k_lo, k_hi = span(S, key)
        # each point is spared only by the bit of its own ribbon around it
        draw3([c[key] for c in S[k_lo:k_hi + 1]], EDGE, lambda t, q, tag=tag: t is not None and t[0] == tag and abs(t[1] - q) <= 16,
              eps=1.0, ids=[c['i'] for c in S[k_lo:k_hi + 1]])
    for end in (0, 1):
        # the cut, from where one edge meets it to where the other does
        ends = [S[span(S, key)[end]][key] for key in ('e1', 'e2')]
        i = span(S, 'e1')[end]
        draw3(ends, zw(1.8, 2.5), own(tag, i, 12), eps=1.0, hand=0.1)

# ---------------------------------------------------------------- shading: the far side of each ribbon

HSP = 6.0                                    # even spacing along the ribbon, in the picture
for tag, S in strands.items():
    last = None
    for i in range(1, len(S) - 1):
        smp = S[i]
        if smp['N'][2] > -0.06 or smp.get('cut_e1') or smp.get('cut_e2'):
            last = None
            continue
        a, b = lerp3(smp['e1'], smp['e2'], 0.1), lerp3(smp['e1'], smp['e2'], 0.9)
        # the next stroke comes once both its ends are a full space on from the last one's
        if last is not None and min(dist(a, last[0]), dist(b, last[1])) < HSP:
            continue
        last = (a, b)
        if dist(a, b) < 5:
            continue
        draw3([a, b], lambda z: 1.0, own(tag, i, 8), eps=1.0, hand=0.1, minlen=3.5)

# ---------------------------------------------------------------- the base pairs

for k, (u, halves) in enumerate(pairs):
    for tag, q in zip(('a', 'b'), halves):
        force = root_band(tag, u)
        skip = (lambda t, k=k: t is not None and t[0] == 'p' and t[1] == k)
        kw = dict(skip=skip, eps=0.6, force=force, minlen=4.0, hand=0.12)
        if BAR == 'rod':
            kw['eps'] = 3.0
            draw3([lerp3(q[0], q[3], 0.5), lerp3(q[1], q[2], 0.5)], zw(2.2, 2.9), **kw)
        else:
            w = zw(1.4, 2.0)
            draw3([q[0], q[1]], w, **kw)
            draw3([q[3], q[2]], w, **kw)
            draw3([q[1], q[2]], w, **kw)

# centre the drawing in the square
xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
SCALE = 1.035
pen.strokes = [([((x - cx) * SCALE + 500, (y - cy) * SCALE + 500) for x, y in p], w) for p, w in pen.strokes]
print('pairs', len(pairs))
pen.save('../04-dna.svg', mirror=False)
pen.report()
