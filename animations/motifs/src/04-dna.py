"""04 DNA: the double helix as a twisted ladder.

Two sugar-phosphate backbones as flat ribbons wound on a cylinder (right-
handed B-DNA, about ten base pairs a turn, the strands offset so the major
and minor grooves alternate), base-pair rungs between them, set on a
diagonal. Modelled in 3D and drawn front to back with a depth test, so the
near ribbon hides what lies behind it. The inner face of each ribbon, seen
where it turns away behind the helix, is shaded with hatching across the band.
Both strands stop at the same height, cut square across the ribbon just
past the last pair, so the ladder simply ends. Drawn in the same ribbon language as 03 RNA.
"""

import math

from pen import Pen, dist, lerp, inside, length

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

    def runs(self, pts, zs, skip=None, eps=0.8, step=1.5, force=(), minlen=3.5):
        """Visible runs of a 2D polyline whose points carry depths zs.
        Polygons in `force` hide whatever falls inside them, whatever its depth."""
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
            hid = any(bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3] and inside(p, poly) for poly, bb in force)
            if not hid and not self.hidden(p, z, skip, eps):
                cur.append(p)
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return [r for r in out if length(r) > minlen]


# ---------------------------------------------------------------- the helix

AXA = math.radians(-46)                     # axis runs up to the right
A = (math.cos(AXA), math.sin(AXA))          # up the helix, in the picture
X = (-A[1], A[0])                           # across it, to the right of A
CEN = (500, 500)
PITCH = 368.0                               # one turn along the axis
R = 116.0                                   # backbone radius
HW = 16.0                                   # half width of a ribbon (as in 03)
BP_PER_TURN = 10.0
DELTA = math.radians(132)                   # angle between the strands across the minor groove
K = -2 * math.pi / PITCH                    # right-handed: dtheta/du
END_DEG = 90.0
TUCK_USE = {('a', 1)}                       # which strand ends are tucked behind the other ribbon
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
    W = norm(add(mul(a3, -R * K), e_th))
    N = (math.cos(th) * X[0], math.cos(th) * X[1], math.sin(th))
    return c, W, N


# both strands end at the same height, just past the last pair, each cut square across
# its own ribbon as it lies in the picture (so no end is drawn to a point)
U_LO = -1.25 * PITCH
U_HI = 1.25 * PITCH
END_TH = math.radians(END_DEG)                # where strand a ends at the lower end, round the helix
THETA0 = END_TH - K * U_LO
PHASE = {'a': 0.0, 'b': DELTA}
EXT = 34.0                                    # sampled a little past the ends, then cut


def strand(tag):
    """Samples along one backbone ribbon, a little past its ends."""
    u0, u1 = U_LO - EXT, U_HI + EXT
    n = int((u1 - u0) / 1.6) + 1
    S = []
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        th = THETA0 + PHASE[tag] + K * u
        c, W, N = frame(u, th)
        S.append(dict(u=u, th=th, c=c, W=W, N=N, e1=add(c, mul(W, HW)), e2=add(c, mul(W, -HW)), i=i, tag=tag))
    return S


strands = {'a': strand('a'), 'b': strand('b')}


def cut_planes(S, ends):
    """The two end cuts of a strand: (point, direction along the strand) in the picture."""
    out = []
    for uend, sgn in ((ends[0], 1), (ends[1], -1)):
        j = min(range(len(S)), key=lambda k: abs(S[k]['u'] - uend))
        p, q = S[max(0, j - 4)]['c'], S[min(len(S) - 1, j + 4)]['c']
        t = (q[0] - p[0], q[1] - p[1])
        L = math.hypot(*t) or 1
        out.append((S[j]['c'], (sgn * t[0] / L, sgn * t[1] / L), uend))
    return out


def ax(p):
    """Position of a point along the helix axis."""
    return (p[0] - CEN[0]) * A[0] + (p[1] - CEN[1]) * A[1]


def side(p, cut):
    """Signed distance past a cut (negative: cut away); the cut line acts near its own end,
    and everything well past the end is cut away."""
    c, t, uend = cut
    beyond = (ax(p) - uend) * (1 if t[0] * A[0] + t[1] * A[1] > 0 else -1)
    if beyond > 70:
        return 1.0
    if beyond < -70:
        return -1.0
    return (p[0] - c[0]) * t[0] + (p[1] - c[1]) * t[1]


ENDS = {'a': [U_LO, U_HI], 'b': [U_LO, U_HI]}
CUTS = {tag: cut_planes(S, ENDS[tag]) for tag, S in strands.items()}


def keep_side(tag, p):
    return all(side(p, cut) >= 0 for cut in CUTS[tag])


def cut_runs(tag, pts3):
    """A 3D polyline cut to the strand's own ends."""
    out, cur = [], []
    for i, p in enumerate(pts3):
        if i:
            q = pts3[i - 1]
            for cut in CUTS[tag]:
                dq, dp = side(q, cut), side(p, cut)
                if dq * dp < 0:
                    x = lerp3(q, p, dq / (dq - dp))
                    if cur:
                        cur.append(x)
                        out.append(cur)
                        cur = []
                    else:
                        cur = [x]
        if keep_side(tag, p):
            cur.append(p)
    if cur:
        out.append(cur)
    return [r for r in out if len(r) > 1]


def cut_poly(tag, poly3):
    pts = list(poly3)
    for cut in CUTS[tag]:
        if not pts:
            break
        res = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            dp, dq = side(p, cut), side(q, cut)
            if dp >= 0:
                res.append(p)
            if (dp >= 0) != (dq >= 0):
                res.append(lerp3(p, q, dp / (dp - dq)))
        pts = res
    return pts


QSTEP = 3


def ribbon_quads(tag):
    """A ribbon as small quads: (index, 2D polygon, depth)."""
    S = strands[tag]
    out = []
    for i in range(0, len(S) - QSTEP, QSTEP):
        p, q = S[i], S[i + QSTEP]
        poly3 = cut_poly(tag, [p['e1'], q['e1'], q['e2'], p['e2']])
        if len(poly3) >= 3:
            out.append((i, [c[:2] for c in poly3], sum(c[2] for c in poly3) / len(poly3)))
    return out


def cap_points(tag, cut):
    """Points along a strand's cut end (and the last bit of each edge), with depths."""
    S = strands[tag]
    hits = []
    for key in ('e1', 'e2'):
        pts = [s[key] for s in S]
        for i in range(1, len(pts)):
            dq, dp = side(pts[i - 1], cut), side(pts[i], cut)
            if dq * dp < 0 and abs(S[i]['u'] - cut[2]) < EXT + 20:
                hits.append((lerp3(pts[i - 1], pts[i], dq / (dq - dp)), i, key))
                break
    if len(hits) < 2:
        return None
    a, b = hits[0][0], hits[1][0]
    out = [p for p in over3(a, b, 3.0, 3.0)]
    out += [lerp3(a, b, k / 8) for k in range(9)]
    for x, i, key in hits:
        # a few units back along each edge, into the ribbon
        for back in (1, 2, 3, 4):
            j = i - back if cut[1][0] * (S[i]['c'][0] - S[i - 1]['c'][0]) + cut[1][1] * (S[i]['c'][1] - S[i - 1]['c'][1]) > 0 else i + back
            if 0 <= j < len(S):
                out.append(S[j][key])
    return out


# A strand whose cut end would stand out from behind the other strand's near ribbon ends
# a little earlier instead, its end tucked out of sight behind that ribbon.
TUCK = {}
for tag, other in (('a', 'b'), ('b', 'a')):
    probe = Depth()
    for i, poly, z in ribbon_quads(other):
        probe.add(poly, z, (other, i))
    for e, sgn in ((0, 1), (1, -1)):
        start = ENDS[tag][e]
        best, score = None, 0.9
        for step in range(1, 170):
            u = start + sgn * step
            pts = cap_points(tag, cut_planes(strands[tag], [u, u])[e])
            if pts:
                hid = sum(probe.hidden(p[:2], p[2], None, 1.0) for p in pts) / len(pts)
                if hid > score:
                    best, score = u, hid
        TUCK[(tag, e)] = best
print('tuck', {k: (round(v) if v is not None else None) for k, v in TUCK.items()})
for (tag, e), u in TUCK.items():
    if u is not None and (tag, e) in TUCK_USE:
        ENDS[tag][e] = u
CUTS = {tag: cut_planes(S, ENDS[tag]) for tag, S in strands.items()}

depth = Depth()
quads = {'a': [], 'b': []}
for tag in strands:
    for i, poly, z in ribbon_quads(tag):
        depth.add(poly, z, (tag, i))
        xs = [c[0] for c in poly]
        ys = [c[1] for c in poly]
        quads[tag].append((i, poly, (min(xs), min(ys), max(xs), max(ys))))

# rungs: base pairs as two pegs meeting near the middle, only where both strands run
RISE = PITCH / BP_PER_TURN
RT = 7.0  # half thickness of a rung, along the axis (as the pegs of 03)
lo, hi = U_LO + RT + 4, U_HI - RT - 4
BOTH = (max(ENDS['a'][0], ENDS['b'][0]) + RT + 4, min(ENDS['a'][1], ENDS['b'][1]) - RT - 4)
nbp = int(round((hi - lo) / RISE)) + 1
u_first = lo
RISE = (hi - lo) / (nbp - 1)
rungs = []
for k in range(nbp):
    u = u_first + k * RISE
    tha = THETA0 + K * u
    pa, pb = pos(u, tha), pos(u, tha + DELTA)
    f = 0.56 if (k * 7 + 3) % 5 < 2 else 0.44   # purine with pyrimidine, either way round
    if BOTH[0] <= u <= BOTH[1]:                 # only where both strands still run
        rungs.append((u, pa, pb, f))

def rung_quads(pa, pb, f):
    """The two pegs of a rung as 3D quads (corner points), meeting with a small gap."""
    a3 = (A[0], A[1], 0.0)
    m = lerp3(pa, pb, f)
    d = norm(tuple(b - a for a, b in zip(pa, pb)))
    m1 = add(m, mul(d, -2.2))
    m2 = add(m, mul(d, 2.2))
    out = []
    for s, e in ((pa, m1), (pb, m2)):
        out.append([add(s, mul(a3, RT)), add(e, mul(a3, RT)), add(e, mul(a3, -RT)), add(s, mul(a3, -RT))])
    return out


for k, (u, pa, pb, f) in enumerate(rungs):
    for quad in rung_quads(pa, pb, f):
        # split along the peg so depth stays local
        n = 6
        for m in range(n):
            t0, t1 = m / n, (m + 1) / n
            c0 = lerp3(quad[0], quad[1], t0)
            c1 = lerp3(quad[0], quad[1], t1)
            c2 = lerp3(quad[3], quad[2], t1)
            c3 = lerp3(quad[3], quad[2], t0)
            depth.add([c0[:2], c1[:2], c2[:2], c3[:2]], (c0[2] + c1[2] + c2[2] + c3[2]) / 4, ('r', k))


def skip_own(tag, i, win):
    def f(t):
        return t is not None and t[0] == tag and abs(t[1] - i) <= win
    return f


def draw3(pts3, w, skip=None, eps=0.8, hand=1.0, force=(), minlen=3.5, **kw):
    pts = [p[:2] for p in pts3]
    zs = [p[2] for p in pts3]
    for run in depth.runs(pts, zs, skip, eps, force=force, minlen=minlen):
        pen.line(run, w=w, hand=hand, occlude=False, **kw)


def zweight(z, lo, hi):
    t = max(0.0, min(1.0, (z / R + 1) / 2))
    return lo + (hi - lo) * t


# ---------------------------------------------------------------- ribbon edges

for tag, S in strands.items():
    for key in ('e1', 'e2'):
        # in chunks, so the weight follows depth (nearer is heavier)
        for k0 in range(0, len(S) - 1, 40):
            chunk = S[k0:k0 + 41]
            i0, i1 = chunk[0]['i'], chunk[-1]['i']

            def skip(t, tag=tag, i0=i0, i1=i1):
                return t is not None and t[0] == tag and i0 - 7 <= t[1] <= i1 + 7
            for run in cut_runs(tag, [c[key] for c in chunk]):
                zm = sum(p[2] for p in run) / len(run)
                draw3(run, zweight(zm, 1.75, 2.55), skip, eps=1.0, hand=0.9)
    # the cut ends: where the two edges meet each cut
    for cut in CUTS[tag]:
        hits = []
        for key in ('e1', 'e2'):
            pts = [s[key] for s in S]
            for i in range(1, len(pts)):
                dq, dp = side(pts[i - 1], cut), side(pts[i], cut)
                if dq * dp < 0 and abs(S[i]['u'] - cut[2]) < EXT + 20:
                    hits.append((lerp3(pts[i - 1], pts[i], dq / (dq - dp)), i))
                    break
        if len(hits) == 2:
            i = (hits[0][1] + hits[1][1]) // 2
            draw3(over3(hits[0][0], hits[1][0], 2.0, 2.5), 2.1, skip_own(tag, i, 14), eps=1.0, hand=0.3)

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


for tag, S in strands.items():
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
        if smp['N'][2] <= 0:
            sp = 7.0 + 1.6 * abs(smp['N'][2])           # the inner face: an even, open tone
        else:
            sp = 9.5 - 4.0 * min(1.0, (sh - 0.3) / 0.6)  # 5.5 .. 9.5
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
        for run in cut_runs(tag, [lerp3(a, b, s0), lerp3(a, b, s1)]):
            draw3(run, pen.r(0.85, 1.05), skip_own(tag, i, 9), eps=1.0, hand=0.3, lift=0.04, piece=(40, 120), minlen=4.5)

# ---------------------------------------------------------------- rungs


def root_band(tag, u):
    """The patch of ribbon a rung is fixed to: the rung stops at its inner edge."""
    S = strands[tag]
    i = (u - S[0]['u']) / (S[-1]['u'] - S[0]['u']) * (len(S) - 1)
    return [(poly, bb) for j, poly, bb in quads[tag] if abs(j - i) <= 16]


for k, (u, pa, pb, f) in enumerate(rungs):
    for tag, q in zip(('a', 'b'), rung_quads(pa, pb, f)):
        zm = sum(c[2] for c in q) / 4
        w = zweight(zm, 1.45, 1.95)
        force = root_band(tag, u)

        def skip(t, k=k):
            return t is not None and t[0] == 'r' and t[1] == k
        # the two long sides and the meeting end; the root is tucked under the ribbon
        kw = dict(skip=skip, eps=0.6, force=force, minlen=5.0)
        draw3([q[0], q[1]], w, hand=0.5, **kw)
        draw3([q[3], q[2]], w * 1.1, hand=0.5, **kw)
        draw3(over3(q[1], q[2], pen.r(0.3, 1.6), pen.r(0.3, 1.6)), w * 0.9, hand=0.2, lift=0, **kw)
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
            draw3([c0, c1], pen.r(1.0, 1.2), hand=0.2, lift=0, **kw)
            t += sp + pen.r(-0.2, 0.3)

# centre the drawing in the square
xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
pen.strokes = [([(x - cx + 500, y - cy + 500) for x, y in p], w) for p, w in pen.strokes]
print('pairs', len(rungs))
pen.save('../04-dna.svg', mirror=False)
pen.report()
