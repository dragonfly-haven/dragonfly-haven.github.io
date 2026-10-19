"""14 - Ginkgo tree: an old Ginkgo biloba, trunk, limbs, crown of fan leaves on
spur shoots, and its roots spreading in a cut-away of the soil below the ground.

Drawn facing right (the tree has no facing; the light comes from the upper left
as drawn) and saved mirrored for the page.

A ginkgo keeps its leader: one stem runs up through the crown, and the limbs
leave it at different heights, rising, the long ones low. They are laid out by
hand; the finer shoots grow from them into the clumps of the crown by space
colonisation, and the leaves sit in tufts on spur shoots along them. A few
nearer sprigs show the leaf itself: a fan on its own long stalk, with the notch.
"""

import math
from collections import defaultdict

import numpy as np

from pen import Pen, catmull, resample, lerp, dist, inside, scanlines, length, clip_segments

pen = Pen(seed=1414)
R = pen.r
G = pen.g

LIGHT = (-0.55, -0.83)  # towards the light (upper left)
GROUND = 778

# ---------------------------------------------------------------- helpers

def norm(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def ang_dir(a):
    return (math.cos(a), math.sin(a))


def tangents(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        out.append(norm((b[0] - a[0], b[1] - a[1])))
    return out


def var_offset(pts, rads, side):
    """Polyline offset by a varying radius; side +1 left of travel, -1 right (y down)."""
    ts = tangents(pts)
    return [(p[0] + t[1] * r * side, p[1] - t[0] * r * side) for p, t, r in zip(pts, ts, rads)]


def wave(amp=1.0, f=(0.01, 0.03)):
    """A smooth 1-D noise function."""
    comps = [(R(*f), R(0, 6.3), R(0.5, 1.0)) for _ in range(3)]
    tot = sum(c[2] for c in comps)

    def fn(s):
        return amp * sum(a * math.sin(s * fr * 2 * math.pi + ph) for fr, ph, a in comps) / tot
    return fn


class Occ:
    """Polygons that hide what is drawn after them, bucketed on a grid."""

    def __init__(self, cell=20):
        self.cell = cell
        self.grid = defaultdict(list)
        self.polys = []

    def add(self, poly, tag=None):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        bb = (min(xs), min(ys), max(xs), max(ys))
        idx = len(self.polys)
        self.polys.append((poly, bb, tag))
        c = self.cell
        for i in range(int(bb[0] // c), int(bb[2] // c) + 1):
            for j in range(int(bb[1] // c), int(bb[3] // c) + 1):
                self.grid[(i, j)].append(idx)
        return idx

    def hit(self, p, skip=None):
        c = self.cell
        for idx in self.grid.get((int(p[0] // c), int(p[1] // c)), ()):
            if skip is not None and idx in skip:
                continue
            poly, bb, tag = self.polys[idx]
            if bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3] and inside(p, poly):
                return True
        return False


def visible_runs(pts, occs, step=1.2, skips=None):
    fine = resample(pts, step)
    runs, cur = [], []
    for p in fine:
        hid = False
        for k, o in enumerate(occs):
            if o.hit(p, skips[k] if skips else None):
                hid = True
                break
        if hid:
            if cur:
                runs.append(cur)
                cur = []
        else:
            cur.append(p)
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1 and (len(r) - 1) * step > 1.5]


def ink(pts, w, occs=(), skips=None, **kw):
    """Draws a stroke, hidden where any occluder covers it."""
    if occs:
        for run in visible_runs(pts, occs, skips=skips):
            pen.line(run, w=w, occlude=False, **kw)
    else:
        pen.line(pts, w=w, occlude=False, **kw)


# ---------------------------------------------------------------- skeleton

class Branch:
    def __init__(self, pts, rads, order, parent=None):
        self.pts = pts
        self.rads = rads
        self.order = order
        self.parent = parent
        self.children = []
        self.need = -1  # how far along it must be drawn (twigs)
        self.first = 10 ** 6  # where its first leaves are
        if parent is not None:
            parent.children.append(self)

    def poly(self):
        a = var_offset(self.pts, self.rads, 1)
        b = var_offset(self.pts, self.rads, -1)
        return a + b[::-1]

    def length(self):
        return sum(dist(self.pts[i], self.pts[i + 1]) for i in range(len(self.pts) - 1))


def taper(n, r0, r1, power=1.0):
    return [r1 + (r0 - r1) * (1 - k / max(1, n - 1)) ** power for k in range(n)]


branches = []


def limb(ctrl, r0, r1, order, parent=None, power=0.9):
    pts = resample(catmull(ctrl, step=2), 4)
    b = Branch(pts, taper(len(pts), r0, r1, power), order, parent)
    branches.append(b)
    return b


TRUNK_TOP = 590

# the leader runs on up through the crown
L0 = limb([(498, 650), (496, 590), (500, 520), (507, 452), (503, 392), (497, 330), (504, 262),
           (500, 196), (494, 132), (500, 80), (497, 40)], 40, 1.8, 0, power=1.8)
# limbs at different heights, rising and a little crooked; the longest low on the left
LA = limb([(484, 630), (444, 604), (402, 582), (364, 548), (326, 528), (296, 500), (266, 486), (246, 466)], 19, 2.2, 0, power=1.0)
LB = limb([(516, 586), (552, 566), (586, 532), (626, 514), (658, 488), (684, 476)], 13, 2.0, 0, power=1.0)
LC = limb([(494, 514), (458, 486), (426, 440), (390, 410), (364, 366), (338, 340), (322, 306)], 12, 2.0, 1, L0)
LD = limb([(506, 456), (552, 432), (596, 392), (648, 370), (690, 334), (730, 320), (762, 298)], 12, 2.0, 1, L0)
LE = limb([(500, 386), (472, 352), (436, 326), (420, 284), (400, 258), (392, 230)], 9, 1.8, 1, L0)
LF = limb([(500, 334), (536, 306), (562, 270), (596, 244), (610, 214)], 7.5, 1.8, 1, L0)
LG = limb([(502, 252), (474, 230), (456, 196), (432, 172)], 6.5, 1.6, 1, L0)
LK = limb([(502, 266), (528, 224), (542, 184), (564, 128)], 7, 1.6, 1, L0)  # a second, younger leader
LJ = limb([(497, 150), (480, 130), (470, 104)], 4, 1.4, 1, L0)
MAIN = [L0, LA, LB]
HAND = list(branches)


def point_on(b, t):
    i = min(len(b.pts) - 1, max(0, int(t * (len(b.pts) - 1))))
    return i, b.pts[i], tangents(b.pts)[i]


# ---------------------------------------------------------------- crown: clumps

def lobe_on(b, t, rx, ry, dens, lift=0.3):
    """A clump drawn out along a limb, sitting a little above it."""
    _, p, tg = point_on(b, t)
    rot = math.atan2(tg[1], tg[0])
    return ((p[0], p[1] - ry * lift), rx, ry, dens, rot)


LOBES = [  # outer clumps, overlapping into a lumpy crown taller than wide
    ((296, 498), 78, 48, 1.0, 0.6), ((652, 488), 64, 42, 1.0, -0.6),
    ((356, 362), 70, 52, 1.0, 0.95), ((704, 338), 76, 50, 1.0, -0.5),
    ((410, 250), 62, 46, 1.0, 1.0), ((604, 240), 60, 46, 1.0, -0.9),
    ((446, 160), 54, 40, 1.0, 0.9), ((562, 132), 50, 42, 1.0, -1.2),
    ((502, 78), 42, 52, 1.0, -1.57),
    # thinner ones further in, along the limbs and the stem
    ((505, 330), 38, 60, 0.7, -1.57), ((504, 215), 34, 46, 0.7, -1.57),
    ((400, 556), 40, 26, 0.6, 0.6), ((600, 410), 40, 28, 0.6, -0.6), ((430, 440), 34, 26, 0.5, 0.9),
]
N_OUTER = 9
ENV_C = (505, 300)


def lobe_q(p, lobe, pad=1.0):
    """Normalised distance of p from a clump's centre (1 on its rim)."""
    (cx, cy), rx, ry, _, rot = lobe
    c, s = math.cos(rot), math.sin(rot)
    x, y = p[0] - cx, p[1] - cy
    u, v = (x * c + y * s) / (rx * pad), (-x * s + y * c) / (ry * pad)
    return math.sqrt(u * u + v * v)


def lobe_shadow(p):
    """How far into shadow a point of the crown is: -1 lit .. 1 dark."""
    best, bq = 0.0, 9.0
    for lobe in LOBES:
        q = lobe_q(p, lobe)
        if q < bq:
            bq = q
            (cx, cy) = lobe[0]
            d = norm((p[0] - cx, p[1] - cy))
            best = q * (d[0] * -LIGHT[0] + d[1] * -LIGHT[1])
    gx = (p[0] - ENV_C[0]) / 270.0
    gy = (p[1] - ENV_C[1]) / 260.0
    return 0.7 * best + 0.4 * (gx * -LIGHT[0] + gy * -LIGHT[1])


def in_crown(p, pad=1.0):
    return any(lobe_q(p, lobe, pad) < 1 for lobe in LOBES)


# ---- space colonisation from the limbs into the clumps
rng = np.random.default_rng(1414)
att = []
for (cx, cy), rx, ry, dens, rot in LOBES:
    n = int(rx * ry / 18 * dens)
    c, s_ = math.cos(rot), math.sin(rot)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rho = math.sqrt(rng.uniform(0, 1)) * (1.0 if rng.uniform() < 0.85 else rng.uniform(1.0, 1.2))
        u, v = rho * math.cos(a) * rx, rho * math.sin(a) * ry
        att.append((cx + u * c - v * s_, cy + u * s_ + v * c))
att = np.array(att)

seed_pts, seed_ref, seed_dir = [], [], []
for b in HAND:
    n = len(b.pts)
    t0 = 0.16 if b is L0 else (0.4 if b in MAIN else 0.2)
    side = 1 if R() < 0.5 else -1
    i = int(t0 * (n - 1))
    while i < n:
        tg = tangents(b.pts)[i]
        a = math.atan2(tg[1], tg[0]) + side * R(0.6, 1.0)
        d = ang_dir(a)
        if d[1] > 0.3:  # shoots leave a limb rising or level
            a = math.atan2(0.3, d[0])
        seed_pts.append(b.pts[i])
        seed_ref.append((b, i))
        seed_dir.append(np.array(ang_dir(a)))
        side = -side
        i += int(R(5, 8))
    seed_pts.append(b.pts[-1])
    seed_ref.append((b, n - 1))
    seed_dir.append(np.array(tangents(b.pts)[-1]))

nodes = [np.array(p, float) for p in seed_pts]
parent = [-1] * len(nodes)
ndir = list(seed_dir)
is_seed = [True] * len(nodes)
nkids = [0] * len(nodes)

D, DI, DK = 7.0, 70.0, 13.0
for it in range(120):
    if len(att) == 0:
        break
    P = np.array(nodes)
    d = np.linalg.norm(att[:, None, :] - P[None, :, :], axis=2)
    near = d.argmin(axis=1)
    dmin = d[np.arange(len(att)), near]
    pull = defaultdict(lambda: np.zeros(2))
    for a_i in np.nonzero(dmin < DI)[0]:
        k = near[a_i]
        v = att[a_i] - P[k]
        pull[k] = pull[k] + v / (np.linalg.norm(v) + 1e-9)
    grown = 0
    for k, v in pull.items():
        if (is_seed[k] and nkids[k] >= 2) or nkids[k] >= 2:
            continue
        v = v / (np.linalg.norm(v) + 1e-9)
        if is_seed[k]:
            v = 0.35 * v + 0.65 * ndir[k]
        v = v + np.array([0.0, -0.15]) + 0.6 * ndir[k]
        v = v / (np.linalg.norm(v) + 1e-9)
        if v[1] > 0.45:  # ginkgo shoots do not hang
            v[1] = 0.45
            v = v / (np.linalg.norm(v) + 1e-9)
        nodes.append(P[k] + D * v)
        parent.append(k)
        nkids[k] += 1
        nkids.append(0)
        ndir.append(v)
        is_seed.append(False)
        grown += 1
    P = np.array(nodes)
    d = np.linalg.norm(att[:, None, :] - P[None, :, :], axis=2)
    att = att[d.min(axis=1) > DK]
    if grown == 0:
        break

N = len(nodes)
children = defaultdict(list)
for k in range(N):
    if parent[k] >= 0:
        children[parent[k]].append(k)

rad = [0.0] * N  # pipe model
for k in reversed(range(N)):
    if is_seed[k]:
        continue
    ch = children[k]
    rad[k] = 0.7 if not ch else sum(rad[c] ** 2.3 for c in ch) ** (1 / 2.3)

# chains into shoots: the thickest child carries a shoot on
pending = []
for k in range(N):
    if is_seed[k]:
        for c in children[k]:
            pending.append((c, seed_ref[k][0], None))
raw = []
while pending:
    c, pb, gidx = pending.pop()
    me = len(raw)
    raw.append(None)
    pts, rs = [], []
    k = c
    if parent[k] >= 0:
        pts.append(tuple(nodes[parent[k]]))
        rs.append(rad[k] if is_seed[parent[k]] else rad[parent[k]])
    while True:
        pts.append(tuple(nodes[k]))
        rs.append(rad[k])
        ch = children[k]
        if not ch:
            break
        ch = sorted(ch, key=lambda c2: -rad[c2])
        for c2 in ch[1:]:
            pending.append((c2, None, me))
        k = ch[0]
    raw[me] = (pts, rs, pb, gidx)

gen_branches = []
made = []
for pts, rs, pb, gidx in raw:
    if len(pts) < 3:
        made.append(None)
        continue
    sm = [pts[0]]
    for i in range(1, len(pts) - 1):
        sm.append(((pts[i - 1][0] + 2 * pts[i][0] + pts[i + 1][0]) / 4, (pts[i - 1][1] + 2 * pts[i][1] + pts[i + 1][1]) / 4))
    sm.append(pts[-1])
    fine = catmull(sm, step=3)
    rr = []
    for i in range(len(fine)):
        j = i / max(1, len(fine) - 1) * (len(rs) - 1)
        j0 = int(j)
        j1 = min(len(rs) - 1, j0 + 1)
        rr.append(min(9.0, rs[j0] + (rs[j1] - rs[j0]) * (j - j0)) * 0.9)
    made.append(Branch(fine, rr, 2))
for (pts, rs, pb, gidx), b in zip(raw, made):
    if b is None:
        continue
    par = pb if pb is not None else (made[gidx] if gidx is not None else None)
    if par is not None:
        b.parent = par
        par.children.append(b)
    branches.append(b)
    gen_branches.append(b)

# long shoots: here and there a young shoot reaches out past the clumps
for b in list(gen_branches):
    tip = b.pts[-1]
    tg_ = tangents(b.pts)[-1]
    best = None
    for li, lobe in enumerate(LOBES[:N_OUTER]):
        q = lobe_q(tip, lobe)
        if q < 1.3 and (best is None or q < best[0]):
            best = (q, li)
    if best is None or best[0] < 0.6:
        continue
    c = LOBES[best[1]][0]
    out = norm((tip[0] - c[0], tip[1] - c[1]))
    if out[0] * tg_[0] + out[1] * tg_[1] < 0.2 or R() > 0.4:
        continue
    d = norm((tg_[0] * 0.55 + out[0] * 0.45, tg_[1] * 0.55 + out[1] * 0.45 - 0.12))
    a = math.atan2(d[1], d[0])
    pts = [tip]
    cur = tip
    for k in range(int(R(18, 34) / 4)):
        a += G(0.04)
        cur = (cur[0] + 4 * math.cos(a), cur[1] + 4 * math.sin(a))
        if cur[1] < 30 or not (80 < cur[0] < 920):
            break
        pts.append(cur)
    if len(pts) < 3:
        continue
    sh = Branch(pts, [0.7] * len(pts), 3, b)
    sh.shoot = True
    branches.append(sh)
    gen_branches.append(sh)

# ---------------------------------------------------------------- leaves

leaves = []
leaf_grid = defaultdict(list)


def blade(B, a, r, half, notch, squash=1.0, sq_ang=0.0, wav=None, wedge=0.3):
    """A ginkgo blade from its base B along angle a: a fan of radius r, wedge-
    shaped at the base (the sides curve out), the notch in the outer edge.
    Returns the outline (closed, starting and ending at B) and a placer."""
    wav = wav or [0.0]
    loc = []
    for k in range(7):  # one side, base to corner
        u = k / 6
        th = -half * (wedge + (1 - wedge) * u ** 1.7)
        loc.append((r * 0.95 * u * math.cos(th), r * 0.95 * u * math.sin(th)))
    m = 10
    for k in range(1, 2 * m):  # the outer edge
        th = -half + 2 * half * k / (2 * m)
        rr = r * (1.0 + wav[k % len(wav)] * 0.03)
        rr *= 1 - notch * max(0.0, 1 - abs(th) / 0.12)
        dn = abs(th) / max(0.01, half)
        if dn > 0.78:
            rr *= 1 - (dn - 0.78) * 0.22
        loc.append((rr * math.cos(th), rr * math.sin(th)))
    for k in range(6, -1, -1):  # the other side, corner to base
        u = k / 6
        th = half * (wedge + (1 - wedge) * u ** 1.7)
        loc.append((r * 0.95 * u * math.cos(th), r * 0.95 * u * math.sin(th)))
    cs, sn = math.cos(sq_ang), math.sin(sq_ang)
    ca, sa = math.cos(a), math.sin(a)

    def place(pt):
        x, y = pt
        u = x * cs + y * sn
        v = -x * sn + y * cs
        u *= squash
        x, y = u * cs - v * sn, u * sn + v * cs
        return (B[0] + x * ca - y * sa, B[1] + x * sa + y * ca)
    return [place(p) for p in loc], place


def add_leaf(petiole, a, r, big=False, force=False, gap=0.6):
    """A leaf at the end of a stalk (a polyline from the spur); None if crowded."""
    B = petiole[-1]
    half = R(0.75, 1.0) if not big else R(0.92, 1.06)
    notch = R(0.22, 0.28) if big else (R(0.12, 0.22) if R() < 0.75 else R(0.0, 0.05))
    squash = R(0.62, 1.0) if not big else R(0.72, 1.0)
    outline, place = blade(B, a, r, half, notch, squash, R(0, math.pi), [G(1) for _ in range(5)], 0.42 if big else 0.55)
    centre = place((r * 0.6, 0))
    gx, gy = int(centre[0] // 12), int(centre[1] // 12)
    if not force:
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for c2, r2 in leaf_grid[(i, j)]:
                    if dist(c2, centre) < gap * (r + r2):
                        return None
    leaf_grid[(gx, gy)].append((centre, r))
    veins = []
    if big:
        # the veins fork as they fan out: four from the base, each parting in two
        for k in range(4):
            e0 = half * 0.88 * (-1 + 2 * (2 * k) / 7)
            e1 = half * 0.88 * (-1 + 2 * (2 * k + 1) / 7)
            fa = (e0 + e1) / 2 * 0.55
            p0 = place((r * 0.07, 0))
            fk = place((r * 0.5 * math.cos(fa), r * 0.5 * math.sin(fa)))
            veins.append(catmull([p0, place((r * 0.25 * math.cos(fa * 0.6), r * 0.25 * math.sin(fa * 0.6))), fk], step=2))
            for e in (e0, e1):
                q = place((r * 0.9 * math.cos(e), r * 0.9 * math.sin(e)))
                m = place((r * 0.7 * math.cos((e + fa) / 2), r * 0.7 * math.sin((e + fa) / 2)))
                veins.append(catmull([fk, m, q], step=2))
    lf = dict(petiole=petiole, poly=outline, centre=centre, veins=veins, big=big, r=r, w=1.0)
    leaves.append(lf)
    return lf


# ---- nearer sprigs: a knobby spur shoot, its leaves each on its own thin stalk
sprig_marks = []  # strokes for the shoot and spur, drawn in front


def sprig(b, t, stalk_a, stalk_len, specs):
    """specs: (angle, radius, stalk length as a share of the radius) per leaf."""
    _, p0, _ = point_on(b, t)
    K0 = (p0[0] + stalk_len * math.cos(stalk_a), p0[1] + stalk_len * math.sin(stalk_a))
    mid = lerp(p0, K0, 0.5)
    bend = (mid[0] + 4 * math.cos(stalk_a + 1.57), mid[1] + 4 * math.sin(stalk_a + 1.57))
    sprig_marks.append((catmull([p0, bend, K0], step=2), 1.25))
    # the spur: a short stout knob, ringed with old leaf scars
    K1 = (K0[0] + 8 * math.cos(stalk_a), K0[1] + 8 * math.sin(stalk_a))
    nx, ny = -math.sin(stalk_a), math.cos(stalk_a)
    for side in (1, -1):
        sprig_marks.append(([(K0[0] + nx * 1.8 * side, K0[1] + ny * 1.8 * side),
                             (K1[0] + nx * 2.4 * side, K1[1] + ny * 2.4 * side)], 1.2))
    for f in (0.35, 0.7):
        c = lerp(K0, K1, f)
        sprig_marks.append(([(c[0] - nx * 2.6, c[1] - ny * 2.6), (c[0] + nx * 2.6, c[1] + ny * 2.6)], 0.8))
    sprig_marks.append(([(K1[0] - nx * 2.4, K1[1] - ny * 2.4), (K1[0] + nx * 2.4, K1[1] + ny * 2.4)], 1.0))
    n = len(specs)
    for k, (a, r, pf) in enumerate(specs):
        f = k - (n - 1) / 2
        S = (K1[0] + nx * f * 1.2, K1[1] + ny * f * 1.2)
        pet = r * pf
        Bp = (S[0] + pet * math.cos(a), S[1] + pet * math.sin(a))
        m = lerp(S, Bp, 0.5)
        m = (m[0], m[1] + 2.0)  # stalks sag a little
        add_leaf(catmull([S, m, Bp], step=2), a, r, big=True, force=True)


# one hanging under the crown left of the stem, one high on the right, a small one up on the left
sprig(LA, 0.6, 1.95, 18, [(0.95, 21, 1.25), (1.6, 25, 1.7), (2.3, 22, 1.3), (2.95, 18, 1.15)])
sprig(LD, 0.97, -0.6, 30, [(-1.3, 19, 1.3), (-0.5, 22, 1.65), (0.25, 18, 1.25)])
sprig(LE, 0.97, 3.6, 20, [(2.95, 14, 1.2), (3.65, 16, 1.55), (4.35, 13, 1.2)])
N_BIG = len(leaves)

# ---- the small leaves, in tufts on the spur shoots
spurs = []
for b in branches:
    L = b.length()
    if b in HAND:
        t0 = 0.3 if b is L0 else (0.55 if b in MAIN else 0.4)
    else:
        t0 = 0.1
    t = t0
    side = 1 if R() < 0.5 else -1
    ts = tangents(b.pts)
    while t <= 1.0:
        i = min(len(b.pts) - 1, int(t * (len(b.pts) - 1)))
        if b.rads[i] < 3.0:
            tg = ts[i]
            spurs.append((b, i, (tg[1] * side, -tg[0] * side), tg))
        side = -side
        t += R(8, 12) / max(L, 1)
    spurs.append((b, len(b.pts) - 1, ts[-1], ts[-1]))

order = list(range(len(spurs)))
pen.rng.shuffle(order)
for si in order:
    b, i, nrm, tg = spurs[si]
    p = b.pts[i]
    shoot = getattr(b, 'shoot', False)
    if not shoot and not in_crown(p, 1.12):
        continue
    n = int(R(2, 4.6))
    base = math.atan2(nrm[1] * 0.75 + tg[1] * 0.45 - 0.3, nrm[0] * 0.75 + tg[0] * 0.45)
    got = False
    for k in range(n):
        a = base + (k - (n - 1) / 2) * R(0.85, 1.05) + G(0.12)
        r = R(7.0, 9.2)
        pet = r * R(0.6, 0.85)
        Bp = (p[0] + pet * math.cos(a), p[1] + pet * math.sin(a))
        if add_leaf([p, Bp], a + G(0.1), r, gap=0.47):
            got = True
    if got:
        b.need = max(b.need, i)
        b.first = min(b.first, i)

print('leaves', len(leaves), 'branches', len(branches), 'nodes', N)

# a shoot is drawn as far as its last leaf, or the last shoot growing from it
for b in reversed(gen_branches):
    if b.need < 0 or b.parent is None or b.parent in HAND:
        continue
    q = b.pts[0]
    pp = b.parent.pts
    j = min(range(len(pp)), key=lambda k: dist(pp[k], q))
    b.parent.need = max(b.parent.need, j)
    b.parent.first = min(b.parent.first, j)

# leaf weights: fine inside the clumps, bold only at their outer edges
for lf in leaves:
    c = lf['centre']
    s = lobe_shadow(c)
    lf['shade'] = s
    if lf['big']:
        lf['w'] = 1.35
        continue
    edge = not in_crown(c, 0.8)
    lf['w'] = 1.2 if edge else (0.95 if s > 0.25 else 0.82)

# ---------------------------------------------------------------- draw the crown

leaf_occ = Occ(20)
for pts, w in sprig_marks:
    ink(pts, w, hand=0.2, lift=0.0)
for lf in leaves:
    pw = 1.0 if lf['big'] else lf['w']
    ink(lf['petiole'], pw, [leaf_occ], hand=0.15, lift=0.0, piece=(30, 90))
    ink(lf['poly'], lf['w'], [leaf_occ], hand=0.25, lift=0.05, piece=(30, 90))
    for v in lf['veins']:
        ink(v, 0.72, [leaf_occ], hand=0.1, lift=0.0, piece=(60, 90))
    leaf_occ.add(lf['poly'])

for b in branches:
    b.poly_ = b.poly()


def trunk_edges():
    ys = list(range(GROUND + 6, TRUNK_TOP - 1, -3))
    left, right = [], []
    wl = wave(2.0, (0.01, 0.025))
    wr = wave(2.0, (0.01, 0.025))
    for y in ys:
        t = (GROUND - y) / (GROUND - TRUNK_TOP)
        cx = 500 - 3 * t + 2 * math.sin(t * 3.2)
        hw = 46 - 10 * t
        flare = 34 * max(0.0, 1 - (GROUND - y) / 70) ** 2.2
        left.append((cx - hw - flare * 1.05 + wl(y), y))
        right.append((cx + hw + flare + wr(y), y))
    return left, right


trunk_left, trunk_right = trunk_edges()
TRUNK_POLY = trunk_left + trunk_right[::-1]

branch_occ = Occ(24)
idx_of = {}
TRUNK_IDX = branch_occ.add(TRUNK_POLY, 'trunk')
for b in branches:
    if b in HAND:
        idx_of[b] = branch_occ.add(b.poly_, b)
ALL = set(range(len(branch_occ.polys)))


def related(b):
    rel = set()
    if b in MAIN:
        rel.add(TRUNK_IDX)
        for m in MAIN:
            if m is not b:
                rel.add(idx_of[m])
    if b.parent is not None and b.parent in idx_of:
        rel.add(idx_of[b.parent])
    for c in b.children:
        if c in idx_of:
            rel.add(idx_of[c])
    return rel


def draw_limb(b):
    skip = ALL - related(b)
    occs, skips = [leaf_occ, branch_occ], [None, skip]
    ts = tangents(b.pts)
    for side in (1, -1):
        edge = var_offset(b.pts, b.rads, side)
        tg = ts[len(ts) // 3]
        nrm = (tg[1] * side, -tg[0] * side)
        shadow = (nrm[0] * LIGHT[0] + nrm[1] * LIGHT[1]) < 0
        w = min(2.2, 1.1 + 0.035 * b.rads[0]) + (0.2 if shadow else 0.0)
        n = len(edge)
        cut = max(2, n // 3)
        ink(edge[:cut + 1], w, occs, skips, hand=0.5)
        ink(edge[cut:], max(0.95, w * 0.78), occs, skips, hand=0.45)
    if b.rads[0] < 5:
        return
    n = len(b.pts)
    # lines along the limb on its shadow side, 5 apart, counted in from the edge
    sides = []
    for i in range(n):
        n1 = (ts[i][1], -ts[i][0])
        sides.append(1 if (n1[0] * LIGHT[0] + n1[1] * LIGHT[1]) < 0 else -1)
    for k in (1, 2, 3):
        run = []
        for i in range(n):
            r = b.rads[i]
            if r < 5 * k + 2.5:
                if run:
                    break
                continue
            off = (r - 5 * k) * sides[i]
            run.append((b.pts[i][0] + ts[i][1] * off, b.pts[i][1] - ts[i][0] * off))
        if len(run) > 3:
            ink(run, 0.84 - 0.03 * k, occs, skips, hand=0.35, lift=0.3, piece=(10, 34))
    # bark fissures along the limb
    for f in range(int(b.rads[0] / 4.5)):
        u = R(-0.6, 0.65)
        s0 = R(0.0, 0.5)
        s1 = min(1.0, s0 + R(0.08, 0.2))
        i0, i1 = int(s0 * (n - 1)), int(s1 * (n - 1))
        if i1 - i0 < 4 or b.rads[i1] < 5:
            continue
        seg = [(b.pts[i][0] + ts[i][1] * b.rads[i] * u, b.pts[i][1] - ts[i][0] * b.rads[i] * u) for i in range(i0, i1)]
        ink(seg, R(0.78, 0.92), occs, skips, hand=0.5, lift=0.25)


def draw_twig(b):
    if b.need < 1:
        return
    i0 = 0
    if b.first < 10 ** 6 and length(b.pts[:b.first + 1]) > 30:
        i0 = max(0, b.first - 4)  # no long bare stalks across the sky
    pts = b.pts[i0:b.need + 1]
    if len(pts) < 2:
        return
    w = min(1.25, 0.85 + 0.18 * b.rads[i0])
    ink(pts, w, [leaf_occ], hand=0.3, taper=0.35)


for b in branches:
    if b not in HAND:
        draw_twig(b)
for b in sorted(HAND, key=lambda b: -b.order):
    draw_limb(b)

# shade between the leaves on the shadow side of each clump (the sky gaps stay white)
cover = set()
for lf in leaves:
    if lf['big']:
        continue
    xs = [p[0] for p in lf['poly']]
    ys = [p[1] for p in lf['poly']]
    for i in range(int((min(xs) - 2) // 6), int((max(xs) + 2) // 6) + 1):
        for j in range(int((min(ys) - 2) // 6), int((max(ys) + 2) // 6) + 1):
            cover.add((i, j))
box = [(120, 10), (880, 10), (880, 620), (120, 620)]
for p0, p1 in scanlines(box, 50, 5.4, R()):
    run, runs = [], []
    for p in resample([p0, p1], 1.5):
        ok = (int(p[0] // 6), int(p[1] // 6)) in cover and in_crown(p, 1.0) and lobe_shadow(p) + G(0.06) > 0.18
        if ok:
            run.append(p)
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    for rn in runs:
        if len(rn) > 2:
            ink(rn, R(0.72, 0.8), [leaf_occ, branch_occ], hand=0.2, lift=0.1, piece=(12, 40))

# ---------------------------------------------------------------- trunk

limb_occ = Occ(24)
for b in MAIN:
    limb_occ.add(b.poly_)
ink(trunk_left, 2.3, [limb_occ], hand=0.8)
ink(trunk_right, 2.6, [limb_occ], hand=0.8)


def trunk_x(u, y):
    if y < TRUNK_TOP:  # up into the leader
        i = min(range(len(L0.pts)), key=lambda k: abs(L0.pts[k][1] - y))
        r = L0.rads[i]
        return (L0.pts[i][0] - r + 2 * r * u, y)
    i = min(len(trunk_left) - 1, max(0, int((GROUND + 6 - y) / 3)))
    a, b = trunk_left[i], trunk_right[i]
    return (a[0] + (b[0] - a[0]) * u, y)


def on_stem(p):
    if p[1] >= TRUNK_TOP:
        return not inside(p, LA.poly_)
    return inside(p, L0.poly_) and not inside(p, LA.poly_) and not inside(p, LB.poly_)


# fissured bark: ridges that wander and jog, part and meet; more of them toward the shadow side
lanes = 13
for k in range(lanes):
    u0 = 0.05 + 0.9 * (k + G(0.15)) / (lanes - 1)
    y = GROUND + 6 - R(0, 20)
    wv = wave(0.025, (0.01, 0.025))
    while y > TRUNK_TOP - 50:
        y1 = max(TRUNK_TOP - 56, y - R(18, 52))
        pts = []
        yy = y
        jog = G(0.025)
        while yy >= y1:
            f = (y - yy) / max(1, y - y1)
            u = min(0.975, max(0.025, u0 + wv(yy) + jog * f))
            pts.append(trunk_x(u, yy))
            yy -= 3
        lit = u0 < 0.4
        if len(pts) > 3 and not (lit and R() < 0.35):
            for run in clip_segments(pts, on_stem):
                ink(run, 0.76 + 0.3 * u0 + G(0.05), hand=0.45, lift=0.25)
        u0 = min(0.97, max(0.03, u0 + jog))
        y = y1 - R(3, 11)

# the shadow side: fine lines between the ridges
for k in range(6):
    u0 = 0.62 + 0.36 * (k + 0.5) / 6 + G(0.008)
    y = GROUND + 2 - R(0, 16)
    while y > TRUNK_TOP + 8:
        y1 = max(TRUNK_TOP + 2, y - R(16, 44))
        pts = [trunk_x(u0 + 0.01 * math.sin(yy * 0.05), yy) for yy in range(int(y), int(y1), -3)]
        if len(pts) > 2:
            ink(pts, R(0.72, 0.8), hand=0.3, lift=0.2, piece=(10, 30))
        y = y1 - R(4, 12)

# the crown's shade on the top of the trunk
for p0, p1 in scanlines(TRUNK_POLY, 62, 5.4, R()):
    if p0[0] > p1[0]:
        p0, p1 = p1, p0
    m = lerp(p0, p1, 0.5)
    reach = 1.0 - (m[1] - TRUNK_TOP) / 90 + G(0.06)
    if reach <= 0.12:
        continue
    ink([lerp(p1, p0, min(1.0, reach)), p1], R(0.72, 0.8), hand=0.25, lift=0.25, piece=(10, 30))

# ---------------------------------------------------------------- ground and roots

trunk_occ = Occ(30)
trunk_occ.add(TRUNK_POLY)

wg = wave(2.0, (0.004, 0.012))
ground = [(x, GROUND + wg(x)) for x in range(160, 842, 4)]
ink(ground, 1.8, [trunk_occ], hand=0.7)

roots = []


def root(ctrl, r0, r1, parent=None, power=1.3):
    pts = resample(catmull(ctrl, step=2), 4)
    b = Branch(pts, taper(len(pts), r0, r1, power), 0)
    b.parent = parent
    if parent is not None:
        parent.children.append(b)
    roots.append(b)
    return b


# the left roots run out long and shallow, the right ones deeper and shorter
R1 = root([(456, 768), (410, 788), (350, 806), (290, 820), (236, 836), (196, 852)], 15, 1.0)
R2 = root([(474, 772), (450, 810), (424, 854), (404, 902)], 11, 1.0)
R3 = root([(500, 774), (506, 828), (500, 880), (506, 934)], 13, 1.0)
R4 = root([(530, 772), (570, 808), (610, 850), (636, 900)], 12, 1.0)
R5 = root([(550, 766), (602, 782), (660, 796), (712, 816), (748, 840)], 12, 1.0)
MAIN_ROOTS = [R1, R2, R3, R4, R5]
SUB = [
    (R1, [(350, 806), (324, 832), (300, 864)], 4.5),
    (R1, [(258, 830), (236, 858), (226, 884)], 3.0),
    (R2, [(432, 842), (408, 850), (374, 850)], 3.5),
    (R3, [(502, 866), (526, 894), (546, 920)], 3.5),
    (R4, [(600, 838), (636, 846), (674, 862)], 4.0),
    (R5, [(662, 798), (684, 824), (700, 854)], 3.5),
]
for par, ctrl, r0 in SUB:
    root(ctrl, r0, 0.8, par)

fine_roots = []
for rb in list(roots):
    n = len(rb.pts)
    ts = tangents(rb.pts)
    side = 1
    for t in (0.55, 0.78, 0.94):
        i = int(t * (n - 1))
        p = rb.pts[i]
        a = math.atan2(ts[i][1], ts[i][0]) + side * R(0.5, 0.9)
        if math.sin(a) < 0.15:
            a = math.atan2(0.3, math.cos(a))
        pts = [p]
        cur = p
        for k in range(int(R(12, 26) / 3)):
            a += G(0.15)
            cur = (cur[0] + 3 * math.cos(a), cur[1] + 3 * math.sin(a))
            pts.append(cur)
        fine_roots.append(pts)
        side = -side

root_occ = Occ(24)
ridx = {}
for rb in roots:
    rb.poly_ = rb.poly()
    ridx[rb] = root_occ.add(rb.poly_)
RALL = set(range(len(root_occ.polys)))

for rb in roots:
    rel = set()
    if rb.parent in ridx:
        rel.add(ridx[rb.parent])
    for c in rb.children:
        rel.add(ridx[c])
    if rb.parent is None:
        for o in MAIN_ROOTS:
            if o is not rb:
                rel.add(ridx[o])
    skip = RALL - rel
    occs, skips = ([root_occ], [skip]) if rb.parent is None else ([root_occ, trunk_occ], [skip, None])
    big = rb.rads[0] > 6
    ts = tangents(rb.pts)
    tm = ts[len(ts) // 3]
    low = 1 if tm[0] < 0 else -1  # the side of travel that lies below
    for side in (1, -1):
        edge = var_offset(rb.pts, rb.rads, side)
        if side == low:
            w = 1.25 if big else 1.0
        else:
            w = 0.95 if big else 0.85
            if rb.parent is None:
                edge = edge[5:]  # by the collar, one line is enough
        ink(edge, w, occs, skips, hand=0.5, taper=0.2)
    for k in (1, 2):
        run = []
        for i in range(len(rb.pts)):
            r = rb.rads[i]
            if r < 5 * k + 2.5:
                break
            sgn = 1 if ts[i][0] < 0 else -1
            off = (r - 5 * k) * sgn
            run.append((rb.pts[i][0] + ts[i][1] * off, rb.pts[i][1] - ts[i][0] * off))
        if len(run) > 3:
            ink(run, 0.74, occs, skips, hand=0.3, lift=0.3, piece=(10, 30))
for pts in fine_roots:
    ink(pts, 0.85, [root_occ], hand=0.3, taper=0.15)

# soil: a few light strata, fading downward and outward
for k in range(60):
    y = GROUND + 12 + (R() ** 1.3) * 175
    x = R(180, 810)
    spread = 1 - abs(x - 495) / 340 - (y - GROUND) / 260
    if spread < R(0, 0.45):
        continue
    ln = R(12, 32)
    ink([(x, y), (x + ln, y + G(1.0))], R(0.72, 0.8), [root_occ, trunk_occ], hand=0.3)

# the odd stone: angular pebbles, shaded below
stones = 0
for k in range(80):
    if stones >= 7:
        break
    y = GROUND + 22 + R() ** 1.1 * 140
    x = R(220, 780)
    rx = R(5, 11) if R() < 0.45 else R(3.5, 6)
    if abs(x - 495) / 300 + (y - GROUND) / 200 > 1.0:
        continue
    if any(root_occ.hit((x + dx, y + dy)) for dx in (-rx - 4, 0, rx + 4) for dy in (-rx - 4, 0, rx + 4)):
        continue
    nv = int(R(6, 9))
    a0 = R(0, 6.3)
    ctrl = []
    for j in range(nv):
        a = a0 + 2 * math.pi * j / nv + G(0.15)
        rr = rx * R(0.75, 1.1)
        ctrl.append((x + rr * math.cos(a), y + rr * 0.68 * math.sin(a)))
    outline = catmull(ctrl, closed=True, step=1.5)
    ink(outline + outline[1:4], 1.15, hand=0.3, lift=0.0)
    if rx > 6.5:
        for p0, p1 in scanlines(outline, 25, 5.0, R()):
            m = lerp(p0, p1, 0.5)
            if (m[1] - y) / (rx * 0.68) + (m[0] - x) / rx * 0.4 > 0.15:
                ink([lerp(p0, p1, 0.15), lerp(p0, p1, 0.85)], 0.72, hand=0.1, lift=0.0)
    stones += 1

for k in range(10):
    x = R(180, 820)
    if 410 < x < 595:
        continue
    y = GROUND + wg(x)
    for j in range(3):
        a = -math.pi / 2 + G(0.35)
        h = R(5, 10)
        ink([(x + j * 2, y), (x + j * 2 + h * math.cos(a), y + h * math.sin(a))], 0.72, hand=0.2)

pen.save('../14-ginkgo-tree.svg', mirror=True)
pen.report()
