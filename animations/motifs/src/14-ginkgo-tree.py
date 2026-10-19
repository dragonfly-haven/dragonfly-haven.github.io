"""14 - Ginkgo tree: an old Ginkgo biloba, trunk, limbs, crown of fan leaves on
spur shoots, and its roots spreading in a cut-away of the soil below the ground.

Drawn facing right (the tree has no facing; the light comes from the upper left
as drawn) and saved mirrored for the page.

The big limbs are laid out by hand; the finer branches grow from them into the
crown by space colonisation (they reach toward points scattered through the
clumps of the crown), and the leaves sit in tufts on spur shoots along them.
"""

import math
from collections import defaultdict

import numpy as np

from pen import Pen, catmull, resample, lerp, dist, inside, scanlines, ellipse_pts

pen = Pen(seed=1414)
R = pen.r
G = pen.g

LIGHT = (-0.55, -0.83)  # towards the light (upper left)
GROUND = 712


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


# ---------------------------------------------------------------- crown: clumps

# the crown is a loose dome of clumps (centre, rx, ry, density, turn), drawn
# out along the limbs that carry them, the outer ones fullest
LOBES = [  # outer clumps at the ends of the limbs
    ((180, 420), 80, 38, 1.0, -0.08), ((204, 314), 72, 46, 1.0, -0.35), ((276, 204), 80, 56, 1.0, 0.95),
    ((398, 130), 64, 42, 1.0, 0.65), ((506, 104), 52, 62, 1.0, 0.0), ((648, 150), 70, 44, 1.0, -0.6),
    ((760, 226), 78, 52, 1.0, -0.75), ((844, 332), 66, 46, 1.0, 0.12), ((834, 430), 78, 36, 1.0, 0.05),
    # and ones along the limbs inside the crown, a little thinner
    ((372, 298), 58, 38, 0.8, 0.75), ((640, 304), 62, 36, 0.8, -0.75), ((520, 206), 40, 56, 0.8, 0.0),
    ((300, 410), 60, 30, 0.7, -0.2), ((714, 404), 60, 30, 0.7, 0.2), ((436, 226), 44, 30, 0.7, 0.6),
    ((594, 380), 34, 26, 0.6, -0.6), ((405, 385), 34, 26, 0.6, 0.6),
]
N_OUTER = 9
ENV_C = (505, 290)


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
    gx = (p[0] - ENV_C[0]) / 380.0
    gy = (p[1] - ENV_C[1]) / 220.0
    return 0.7 * best + 0.45 * (gx * -LIGHT[0] + gy * -LIGHT[1])


def in_crown(p, pad=1.0):
    return any(lobe_q(p, lobe, pad) < 1 for lobe in LOBES)


# ---------------------------------------------------------------- skeleton

class Branch:
    def __init__(self, pts, rads, order, parent=None):
        self.pts = pts
        self.rads = rads
        self.order = order
        self.parent = parent
        self.children = []
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


TRUNK_TOP = 474

L1 = limb([(484, 508), (468, 470), (446, 432), (424, 400), (390, 362), (350, 324), (318, 286), (290, 242), (264, 202), (248, 170)], 24, 2.4, 0, power=1.1)
L2 = limb([(500, 500), (503, 450), (508, 400), (520, 350), (524, 300), (516, 246), (512, 190), (504, 136), (500, 86)], 26, 2.2, 0, power=1.0)
L3 = limb([(514, 508), (536, 470), (566, 436), (604, 400), (640, 362), (668, 328), (710, 290), (748, 254), (782, 216)], 22, 2.4, 0, power=1.1)
L4 = limb([(480, 556), (446, 530), (404, 504), (356, 482), (306, 468), (256, 454), (210, 442), (170, 438), (136, 448)], 16, 2.0, 0, power=0.9)
L5 = limb([(518, 540), (556, 514), (600, 492), (652, 472), (706, 456), (760, 442), (806, 434), (846, 436), (878, 450)], 15, 2.0, 0, power=0.9)
L6 = limb([(522, 318), (570, 280), (622, 236), (664, 196), (700, 160)], 11, 2.2, 1, L2)
L7 = limb([(515, 228), (472, 196), (428, 166), (394, 132)], 9, 2.0, 1, L2)
L8 = limb([(384, 352), (338, 346), (284, 338), (230, 318), (188, 300)], 10, 2.0, 1, L1)
L9 = limb([(650, 352), (704, 346), (760, 330), (812, 322), (852, 338)], 10, 2.0, 1, L3)
L10 = limb([(318, 284), (307, 246), (299, 208), (295, 172)], 7, 1.8, 1, L1)
L11 = limb([(716, 288), (721, 248), (717, 208), (705, 170)], 7, 1.8, 1, L3)
MAIN = [L1, L2, L3, L4, L5]
HAND = list(branches)

# ---- space colonisation from the limbs into the clumps
rng = np.random.default_rng(1414)
att = []
for (cx, cy), rx, ry, dens, rot in LOBES:
    n = int(rx * ry / 23 * dens)
    c, s_ = math.cos(rot), math.sin(rot)
    for _ in range(n):
        # soft-edged: most within the rim, some a little beyond
        a = rng.uniform(0, 2 * math.pi)
        rho = math.sqrt(rng.uniform(0, 1)) * (1.0 if rng.uniform() < 0.85 else rng.uniform(1.0, 1.22))
        u, v = rho * math.cos(a) * rx, rho * math.sin(a) * ry
        att.append((cx + u * c - v * s_, cy + u * s_ + v * c))
att = np.array(att)

seed_pts, seed_ref, seed_dir = [], [], []
for b in HAND:
    n = len(b.pts)
    t0 = 0.4 if b in MAIN else 0.15
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
        i += int(R(7, 11))
    # the limb's tip carries on as a shoot
    seed_pts.append(b.pts[-1])
    seed_ref.append((b, n - 1))
    seed_dir.append(np.array(tangents(b.pts)[-1]))

nodes = [np.array(p, float) for p in seed_pts]
parent = [-1] * len(nodes)
ndir = list(seed_dir)
is_seed = [True] * len(nodes)

D, DI, DK = 7.0, 70.0, 13.0
nkids = [0] * len(nodes)
for it in range(120):
    if len(att) == 0:
        break
    P = np.array(nodes)
    d = np.linalg.norm(att[:, None, :] - P[None, :, :], axis=2)
    near = d.argmin(axis=1)
    dmin = d[np.arange(len(att)), near]
    pull = defaultdict(lambda: np.zeros(2))
    cnt = defaultdict(int)
    for a_i in np.nonzero(dmin < DI)[0]:
        k = near[a_i]
        v = att[a_i] - P[k]
        pull[k] = pull[k] + v / (np.linalg.norm(v) + 1e-9)
        cnt[k] += 1
    grown = 0
    for k, v in pull.items():
        if is_seed[k] and nkids[k] >= 1:
            continue
        if nkids[k] >= 2:
            continue
        v = v / (np.linalg.norm(v) + 1e-9)
        if is_seed[k]:
            v = 0.35 * v + 0.65 * ndir[k]
        v = v + np.array([0.0, -0.15]) + 0.6 * ndir[k]
        v = v / (np.linalg.norm(v) + 1e-9)
        if v[1] > 0.45:  # ginkgo shoots do not hang
            v[1] = 0.45
            v = v / (np.linalg.norm(v) + 1e-9)
        q = P[k] + D * v
        nodes.append(q)
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

# pipe model radii
rad = [0.0] * N
for k in reversed(range(N)):
    if is_seed[k]:
        continue
    ch = children[k]
    if not ch:
        rad[k] = 0.7
    else:
        rad[k] = sum(rad[c] ** 2.3 for c in ch) ** (1 / 2.3)

# chains into branches: the thickest child carries a branch on
gen_branches = []


pending = []
for k in range(N):
    if is_seed[k]:
        for c in children[k]:
            pending.append((c, seed_ref[k][0], None, None))

raw = []
while pending:
    c, pb, gidx, at_i = pending.pop()
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
            pending.append((c2, None, me, None))
        k = ch[0]
    raw[me] = (pts, rs, pb, gidx)

# smooth and make Branch objects
made = []
for pts, rs, pb, gidx in raw:
    if len(pts) < 3:
        made.append(None)
        continue
    # light smoothing of the node path
    sm = [pts[0]]
    for i in range(1, len(pts) - 1):
        sm.append(((pts[i - 1][0] + 2 * pts[i][0] + pts[i + 1][0]) / 4, (pts[i - 1][1] + 2 * pts[i][1] + pts[i + 1][1]) / 4))
    sm.append(pts[-1])
    fine = catmull(sm, step=3)
    # radii resampled along
    rr = []
    for i in range(len(fine)):
        t = i / max(1, len(fine) - 1)
        j = t * (len(rs) - 1)
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
    if out[0] * tg_[0] + out[1] * tg_[1] < 0.2 or R() > 0.45:
        continue
    d = norm((tg_[0] * 0.55 + out[0] * 0.45, tg_[1] * 0.55 + out[1] * 0.45 - 0.12))
    a = math.atan2(d[1], d[0])
    pts = [tip]
    cur = tip
    for k in range(int(R(20, 40) / 4)):
        a += G(0.04)
        cur = (cur[0] + 4 * math.cos(a), cur[1] + 4 * math.sin(a))
        if cur[1] < 40 or not (60 < cur[0] < 940):
            break
        pts.append(cur)
    if len(pts) < 3:
        continue
    sh = Branch(pts, [0.7] * len(pts), 3, b)
    sh.shoot = True
    branches.append(sh)

# ---------------------------------------------------------------- foliage

leaves = []
leaf_grid = defaultdict(list)


def leaf_shape(S, a, r, pet, half, notch, squash, sq_ang, wav):
    """A ginkgo leaf: petiole from spur S at angle a, fan blade of radius r."""
    loc = []
    cl = (r * 0.97 * math.cos(-half), r * 0.97 * math.sin(-half))
    for k in range(4):
        u = k / 4
        bow = math.sin(math.pi * u) * r * 0.05
        loc.append((cl[0] * u, cl[1] * u + bow))
    m = 9
    for k in range(m * 2 + 1):
        th = -half + 2 * half * k / (2 * m)
        rr = r * (1.0 + wav[k % len(wav)] * 0.035)
        rr *= 1 - notch * max(0.0, 1 - abs(th) / 0.13)
        dn = abs(th) / max(0.01, half)
        if dn > 0.8:
            rr *= 1 - (dn - 0.8) * 0.3
        loc.append((rr * math.cos(th), rr * math.sin(th)))
    cr = (r * 0.97 * math.cos(half), r * 0.97 * math.sin(half))
    for k in range(1, 5):
        u = 1 - k / 4
        bow = math.sin(math.pi * u) * r * 0.05
        loc.append((cr[0] * u, cr[1] * u - bow))
    cs, sn = math.cos(sq_ang), math.sin(sq_ang)

    def sq(pt):
        x, y = pt
        u = x * cs + y * sn
        v = -x * sn + y * cs
        u *= squash
        return (u * cs - v * sn, u * sn + v * cs)
    B = (S[0] + pet * math.cos(a), S[1] + pet * math.sin(a))
    ca, sa = math.cos(a), math.sin(a)

    def place(pt):
        x, y = sq(pt)
        return (B[0] + x * ca - y * sa, B[1] + x * sa + y * ca)
    outline = [place(p) for p in loc]
    stroke = [S, B] + outline[1:]
    centre = place((r * 0.6, 0))
    return stroke, outline, B, centre, place


def try_leaf(S, a, r, pet, big=False, w=1.0, force=False, gap=0.5):
    half = R(0.72, 1.0) if not big else R(0.85, 1.0)
    notch = R(0.2, 0.26) if big else (R(0.1, 0.2) if R() < 0.7 else R(0.0, 0.05))
    squash = R(0.62, 1.0) if not big else R(0.8, 1.0)
    sq_ang = R(0, math.pi)
    wav = [G(1) for _ in range(5)]
    stroke, poly, B, centre, place = leaf_shape(S, a, r, pet, half, notch, squash, sq_ang, wav)
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
        nv = 6
        for k in range(nv):
            th = -half * 0.84 + 2 * half * 0.84 * k / (nv - 1)
            p0 = place((r * 0.2 * math.cos(th * 0.6), r * 0.2 * math.sin(th * 0.6)))
            p1 = place((r * 0.86 * math.cos(th), r * 0.86 * math.sin(th)))
            veins.append([p0, p1])
    lf = dict(stroke=stroke, poly=poly, centre=centre, w=w, veins=veins, big=big, r=r, a=a, place=place, half=half)
    leaves.append(lf)
    return lf


# a few nearer, larger leaves: sprigs at the ends of the low limbs
extra_twigs = []
NEAR = [  # limb, main direction of the sprig, of its leaves, count
    (L4, 2.5, 2.2, 3),
    (L5, 0.55, 0.85, 3),
]
for b, ta, a, n in NEAR:
    tip = b.pts[-1]
    S = (tip[0] + 16 * math.cos(ta), tip[1] + 16 * math.sin(ta))
    extra_twigs.append(catmull([tip, lerp(tip, S, 0.5), S], step=2))
    for k in range(n):
        aa = a + (k - (n - 1) / 2) * 0.7 + G(0.06)
        try_leaf(S, aa, R(25, 28), R(18, 22), big=True, w=1.3, force=True)

spurs = []
for b in branches:
    L = b.length()
    if b in HAND:
        t0 = 0.6 if b in MAIN else 0.4
    else:
        t0 = 0.12
    t = t0
    side = 1 if R() < 0.5 else -1
    ts = tangents(b.pts)
    while t <= 1.0:
        i = min(len(b.pts) - 1, int(t * (len(b.pts) - 1)))
        if b.rads[i] < 3.0:
            p = b.pts[i]
            tg = ts[i]
            nrm = (tg[1] * side, -tg[0] * side)
            spurs.append((p, nrm, tg, getattr(b, 'shoot', False)))
        side = -side
        t += R(9, 13) / max(L, 1)
    spurs.append((b.pts[-1], ts[-1], ts[-1], getattr(b, 'shoot', False)))

order = list(range(len(spurs)))
pen.rng.shuffle(order)
for si in order:
    p, nrm, tg, shoot = spurs[si]
    if not shoot and not in_crown(p, 1.15):
        continue
    n = int(R(2, 4.5)) if shoot else int(R(2.6, 6))
    base = math.atan2(nrm[1] * 0.75 + tg[1] * 0.45 - 0.3, nrm[0] * 0.75 + tg[0] * 0.45)
    for k in range(n):
        a = base + (k - (n - 1) / 2) * R(0.55, 0.8) + G(0.18)
        try_leaf(p, a, R(7.0, 9.6), R(4.5, 7.5), w=1.0, gap=0.46)

print('leaves', len(leaves), 'branches', len(branches), 'nodes', N)

# leaf weight and shade
for lf in leaves:
    c = lf['centre']
    s = lobe_shadow(c)
    lf['shade'] = s
    if lf['big']:
        continue
    edge = not in_crown(c, 0.86)
    lf['w'] = 1.0 + (0.25 if edge else 0.0) + (0.2 if s > 0.25 else 0.0)

# ---------------------------------------------------------------- draw the crown

leaf_occ = Occ(20)
for lf in leaves:
    ink(lf['stroke'], lf['w'], [leaf_occ], hand=0.25, lift=0.06, piece=(30, 90))
    for v in lf['veins']:
        ink(v, 0.72, [leaf_occ], hand=0.1, lift=0.0, piece=(60, 90))
    leaf_occ.add(lf['poly'])
for tw in extra_twigs:
    ink(tw, 1.3, [leaf_occ], hand=0.3)

for b in branches:
    b.poly_ = b.poly()

# trunk outline, as an occluder for the limbs that leave it
def trunk_edges():
    ys = list(range(GROUND + 6, TRUNK_TOP - 1, -3))
    left, right = [], []
    wl = wave(2.2, (0.01, 0.025))
    wr = wave(2.2, (0.01, 0.025))
    for y in ys:
        t = (GROUND - y) / (GROUND - TRUNK_TOP)
        cx = 503 - 10 * t + 3 * math.sin(t * 3.2)
        hw = 43 + 6 * (1 - t) + 3 * t ** 3
        flare = 36 * max(0.0, 1 - (GROUND - y) / 75) ** 2.2
        left.append((cx - hw - flare * 1.05 + wl(y), y))
        right.append((cx + hw + flare + wr(y), y))
    return left, right


trunk_left, trunk_right = trunk_edges()
TRUNK_POLY = trunk_left + trunk_right[::-1]

branch_occ = Occ(24)
idx_of = {}
TRUNK_IDX = branch_occ.add(TRUNK_POLY, 'trunk')
for b in branches:
    if max(b.rads) > 2.0:
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


def draw_branch(b):
    big = max(b.rads) > 2.0
    if not big:
        ink(b.pts, 0.85 + 0.15 * b.rads[0], [leaf_occ], hand=0.35)
        return
    skip = ALL - related(b)
    occs, skips = [leaf_occ, branch_occ], [None, skip]
    ts = tangents(b.pts)
    for side in (1, -1):
        edge = var_offset(b.pts, b.rads, side)
        tg = ts[len(ts) // 3]
        nrm = (tg[1] * side, -tg[0] * side)
        shadow = (nrm[0] * LIGHT[0] + nrm[1] * LIGHT[1]) < 0
        r0 = b.rads[0]
        w = min(2.2, 1.05 + 0.045 * r0) + (0.2 if shadow else 0.0)
        n = len(edge)
        cut = max(2, n // 3)
        ink(edge[:cut + 1], w, occs, skips, hand=0.5)
        ink(edge[cut:], max(0.9, w * 0.78), occs, skips, hand=0.45)
    if b.rads[0] < 5:
        return
    n = len(b.pts)
    # lines along the limb on its shadow side, as the light falls off round it
    sides = []
    for i in range(n):
        n1 = (ts[i][1], -ts[i][0])
        sides.append(1 if (n1[0] * LIGHT[0] + n1[1] * LIGHT[1]) < 0 else -1)
    for k in (1, 2, 3):
        run = []
        for i in range(n):
            r = b.rads[i]
            if r < 5 * k + 2.5:
                break
            off = (r - 5 * k) * sides[i]
            run.append((b.pts[i][0] + ts[i][1] * off, b.pts[i][1] - ts[i][0] * off))
        if len(run) > 3:
            ink(run, 0.84 - 0.03 * k, occs, skips, hand=0.35, lift=0.3, piece=(10, 34))
    # long bark fissures along the limb
    for f in range(int(b.rads[0] / 4.5)):
        u = R(-0.7, 0.75)
        s0 = R(0.0, 0.45)
        s1 = min(1.0, s0 + R(0.12, 0.3))
        i0, i1 = int(s0 * (n - 1)), int(s1 * (n - 1))
        if i1 - i0 < 4 or b.rads[i1] < 4.5:
            continue
        seg = [(b.pts[i][0] + ts[i][1] * b.rads[i] * (u + 0.1 * math.sin(i * 0.3)), b.pts[i][1] - ts[i][0] * b.rads[i] * (u + 0.1 * math.sin(i * 0.3))) for i in range(i0, i1)]
        ink(seg, R(0.8, 1.0), occs, skips, hand=0.5)


for b in sorted(branches, key=lambda b: -b.order):
    draw_branch(b)

# shade between the leaves on the shadow side of each clump (the sky gaps stay white)
cover = set()
for lf in leaves:
    xs = [p[0] for p in lf['poly']]
    ys = [p[1] for p in lf['poly']]
    for i in range(int((min(xs) - 5) // 6), int((max(xs) + 5) // 6) + 1):
        for j in range(int((min(ys) - 5) // 6), int((max(ys) + 5) // 6) + 1):
            cover.add((i, j))
box = [(60, 30), (950, 30), (950, 520), (60, 520)]
for p0, p1 in scanlines(box, 50, 5.2, R()):
    run = []
    runs = []
    for p in resample([p0, p1], 1.5):
        ok = (int(p[0] // 6), int(p[1] // 6)) in cover and in_crown(p, 1.05) and lobe_shadow(p) + G(0.06) > 0.2
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
    i = min(len(trunk_left) - 1, max(0, int((GROUND + 6 - y) / 3)))
    a, b = trunk_left[i], trunk_right[i]
    return (a[0] + (b[0] - a[0]) * u, y)


# fissured bark: long ridges that wander and jog, part and meet; more of them,
# heavier and unbroken, toward the shadow side
lanes = 14
for k in range(lanes):
    u0 = 0.04 + 0.92 * (k + G(0.15)) / (lanes - 1)
    y = GROUND + 6 - R(0, 20)
    wv = wave(0.025, (0.01, 0.025))
    while y > TRUNK_TOP + 8:
        y1 = max(TRUNK_TOP + 2, y - R(24, 70))
        pts = []
        yy = y
        jog = G(0.025)
        while yy >= y1:
            f = (y - yy) / max(1, y - y1)
            u = min(0.975, max(0.025, u0 + wv(yy) + jog * f))
            pts.append(trunk_x(u, yy))
            yy -= 3
        lit = u0 < 0.4
        if len(pts) > 3 and not (lit and R() < 0.3):
            w = 0.78 + 0.55 * u0 + G(0.06)
            ink(pts, w, hand=0.45, lift=0.3 if lit else 0.12)
        u0 = min(0.97, max(0.03, u0 + jog))
        y = y1 - R(2, 9)

# the shadow side: fine lines between the ridges
for k in range(6):
    u0 = 0.62 + 0.36 * (k + 0.5) / 6 + G(0.008)
    y = GROUND + 2 - R(0, 16)
    while y > TRUNK_TOP + 10:
        y1 = max(TRUNK_TOP + 4, y - R(16, 44))
        pts = [trunk_x(u0 + 0.01 * math.sin(yy * 0.05), yy) for yy in range(int(y), int(y1), -3)]
        if len(pts) > 2:
            ink(pts, R(0.72, 0.8), hand=0.3, lift=0.2, piece=(10, 30))
        y = y1 - R(4, 12)
# the crown's shade on the top of the trunk and the crotch
for p0, p1 in scanlines(TRUNK_POLY, 62, 5.4, R()):
    # from the right edge in, further the higher up
    if p0[0] > p1[0]:
        p0, p1 = p1, p0
    m = lerp(p0, p1, 0.5)
    reach = 1.0 - (m[1] - TRUNK_TOP) / 110 + G(0.06)
    if reach <= 0.12:
        continue
    q0 = lerp(p1, p0, min(1.0, reach))
    ink([q0, p1], R(0.72, 0.8), hand=0.25, lift=0.25, piece=(10, 30))

# ---------------------------------------------------------------- ground and roots

trunk_occ = Occ(30)
trunk_occ.add(TRUNK_POLY)

wg = wave(2.0, (0.004, 0.012))
ground = [(x, GROUND + wg(x)) for x in range(92, 910, 4)]
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


R1 = root([(452, 700), (404, 724), (336, 744), (262, 758), (192, 768), (126, 782)], 17, 1.0)
R2 = root([(472, 706), (444, 742), (404, 788), (358, 834), (322, 878)], 13, 1.0)
R3 = root([(502, 708), (503, 760), (497, 818), (500, 874), (494, 928)], 15, 1.0)
R4 = root([(532, 706), (566, 744), (610, 790), (654, 838), (684, 884)], 13, 1.0)
R5 = root([(556, 700), (610, 722), (690, 740), (776, 752), (876, 768)], 17, 1.0)
# second-order roots, then fine ones
SUB = [
    (R1, [(330, 746), (300, 772), (262, 800), (226, 820)], 5.5),
    (R1, [(220, 763), (196, 786), (178, 812)], 3.5),
    (R2, [(400, 792), (370, 800), (330, 802)], 4.0),
    (R3, [(500, 812), (520, 846), (544, 880)], 4.5),
    (R3, [(498, 860), (478, 890), (466, 918)], 3.0),
    (R4, [(612, 792), (648, 800), (690, 812)], 4.0),
    (R5, [(700, 742), (730, 772), (766, 800), (800, 818)], 5.5),
    (R5, [(800, 755), (820, 780), (836, 808)], 3.5),
]
for par, ctrl, r0 in SUB:
    root(ctrl, r0, 0.8, par)

fine_roots = []
for rb in list(roots):
    n = len(rb.pts)
    ts = tangents(rb.pts)
    side = 1
    for t in (0.55, 0.75, 0.92):
        i = int(t * (n - 1))
        p = rb.pts[i]
        a = math.atan2(ts[i][1], ts[i][0]) + side * R(0.5, 0.9)
        if math.sin(a) < 0.15:
            a = math.atan2(0.3, math.cos(a))
        pts = [p]
        cur = p
        for k in range(int(R(14, 30) / 3)):
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
        for o in (R1, R2, R3, R4, R5):
            if o is not rb:
                rel.add(ridx[o])
    skip = RALL - rel
    occs, skips = [root_occ, trunk_occ], [skip, None]
    if rb.parent is None:
        occs, skips = [root_occ], [skip]
    big = rb.rads[0] > 6
    ts = tangents(rb.pts)
    tm = ts[len(ts) // 3]
    low = 1 if tm[0] < 0 else -1  # the side of travel that lies below
    for side in (1, -1):
        edge = var_offset(rb.pts, rb.rads, side)
        w = (1.4 if big else 1.1) if side == low else (1.15 if big else 0.95)
        ink(edge, w, occs, skips, hand=0.5, taper=0.2)
    # shade the underside with lines along the root
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

# the root collar above the ground: the flare meets the roots
# soil: a few light strata and stones, fading downward and outward
for k in range(70):
    y = GROUND + 12 + (R() ** 1.3) * 215
    x = R(120, 880)
    spread = 1 - abs(x - 500) / 430 - (y - GROUND) / 320
    if spread < R(0, 0.45):
        continue
    ln = R(12, 36)
    ink([(x, y), (x + ln, y + G(1.0))], R(0.72, 0.8), [root_occ, trunk_occ], hand=0.3)

# the odd stone: angular pebbles, shaded below
stones = 0
for k in range(60):
    if stones >= 11:
        break
    y = GROUND + 24 + R() ** 1.1 * 175
    x = R(170, 830)
    rx = R(5, 12) if R() < 0.4 else R(3.5, 6)
    if abs(x - 500) / 380 + (y - GROUND) / 250 > 1.0:
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

for k in range(12):
    x = R(110, 890)
    if 400 < x < 610:
        continue
    y = GROUND + wg(x)
    for j in range(3):
        a = -math.pi / 2 + G(0.35)
        h = R(5, 10)
        ink([(x + j * 2, y), (x + j * 2 + h * math.cos(a), y + h * math.sin(a))], 0.72, hand=0.2)

pen.save('../14-ginkgo-tree.svg', mirror=True)
pen.report()
