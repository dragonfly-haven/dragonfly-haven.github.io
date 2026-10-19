#!/usr/bin/env python3
"""01 Galaxy: a spiral galaxy wrapped in gas and dust, seen at a slant.

The disc is tipped about 56 degrees and turned so its long axis rises to the
right. A bright compact core sits in a rounder bulge, wound with the tight
spiral of the inner disc; an inner dust lane crosses in front of the bulge on
the near side. Two grand-design arms (logarithmic spirals, pitch 21 degrees)
sweep out from it, each a bundle of flowing lines with a hard inner edge, a
dark dust lane hatched along that edge, and a gassy outer side (a contour of a
noisy density field). Billowing star-forming clouds sit along the arms, round
billows heaped on one another, shaded on their far side and trailing wisps,
with young star clusters beside them. Faint flow lines fill the disc between
the arms, gas wisps trail off the arm tips, and stars are scattered over the
field.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw

from pen import Pen, catmull, ellipse_pts, resample, length, dist, lerp

pen = Pen(seed=101)
rng = random.Random(2024)


def R(lo=0.0, hi=1.0):
    return lo + (hi - lo) * rng.random()


def G(s=1.0):
    return rng.gauss(0, s)


# ---------------------------------------------------------------- the view

CX, CY = 500.0, 500.0
Q = 0.6                         # cos(inclination): the disc tipped ~53 degrees
PHI = math.radians(-27)         # the long axis rises to the right
cP, sP = math.cos(PHI), math.sin(PHI)
LIGHT = (-0.55, -0.83)          # billows are lit from up and to the left


def proj(u, v):
    """Disc-plane point to the page."""
    y = v * Q
    return (CX + u * cP - y * sP, CY + u * sP + y * cP)


def unproj(x, y):
    """Page point back to the disc plane (as if it lay in the disc)."""
    dx, dy = x - CX, y - CY
    u = dx * cP + dy * sP
    yy = -dx * sP + dy * cP
    return (u, yy / Q)


def near(p):
    return unproj(*p)[1] > 0


def tilt(x, y, cx=CX, cy=CY):
    """A point of a frame aligned with the galaxy's long axis to the page."""
    return (cx + x * cP - y * sP, cy + x * sP + y * cP)


# ---------------------------------------------------------------- masks

S = 2  # mask pixels per unit


class Mask:
    def __init__(self):
        self.img = Image.new('L', (1000 * S, 1000 * S), 0)
        self.draw = ImageDraw.Draw(self.img)
        self._a = None

    def add(self, poly):
        self.draw.polygon([(x * S, y * S) for x, y in poly], fill=255)
        self._a = None

    def arr(self):
        if self._a is None:
            self._a = np.array(self.img) > 0
        return self._a

    def __call__(self, p):
        x, y = int(p[0] * S), int(p[1] * S)
        if 0 <= x < 1000 * S and 0 <= y < 1000 * S:
            return bool(self.arr()[y, x])
        return False


ARMS = Mask()      # arm bands with their dust lanes: the interarm flow stops there
LANE = Mask()      # the inner dust lane crossing the bulge
BULGE = Mask()     # bulge silhouette: the disc's lines stop at it
CLOUD = Mask()     # star-forming clouds: what lies behind them stops at their edge


def ink(pts, w, block=None, hand=0.6, lift=0.08, piece=(22, 70), taper=0.0, minlen=2.0):
    """A stroke, cut where block(point) holds."""
    fine = resample(pts, 1.0)
    runs, cur = [], []
    for p in fine:
        ok = 3 <= p[0] <= 997 and 3 <= p[1] <= 997 and not (block and block(p))
        if ok:
            cur.append(p)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    for run in runs:
        if len(run) > 1 and length(run) >= minlen:
            pen.line(run, w=w, hand=hand, lift=lift, piece=piece, taper=taper, occlude=False)


def chop(pts, lo, hi, glo, ghi, keep=1.0):
    """A polyline broken into pieces lo..hi long with gaps glo..ghi, as a quick hand draws."""
    fine = resample(pts, 1.0)
    n = len(fine)
    out = []
    i = int(R(0, hi * 0.5))
    while i < n - 1:
        j = min(n - 1, i + int(R(lo, hi)))
        if j - i >= 2 and rng.random() < keep:
            out.append(fine[i:j + 1])
        i = j + int(R(glo, ghi))
    return out


def runs_where(pts, pred):
    segs, cur = [], []
    for p in pts:
        if pred(p):
            cur.append(p)
        elif cur:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return [q for q in segs if len(q) > 2]


def dot(x, y, r=1.4, w=1.2):
    pen.dot(x, y, r=r, w=w)


def sparkle(x, y, L, w=1.3, rot=0.0, diag=0.35):
    """A four-pointed star: two tapered crossing strokes, shorter faint diagonals."""
    for k in range(2):
        a = rot + k * math.pi / 2
        Lk = L * (1.0 if k == 0 else 0.8)
        p0 = (x - math.cos(a) * Lk, y - math.sin(a) * Lk)
        p1 = (x + math.cos(a) * Lk, y + math.sin(a) * Lk)
        pen.line([p0, (x, y), p1], w=w, hand=0, lift=0, piece=(2.5, 4), taper=0.92, occlude=False)
    if diag:
        for k in range(2):
            a = rot + math.pi / 4 + k * math.pi / 2
            Ld = L * diag
            p0 = (x - math.cos(a) * Ld, y - math.sin(a) * Ld)
            p1 = (x + math.cos(a) * Ld, y + math.sin(a) * Ld)
            pen.line([p0, p1], w=w * 0.6, hand=0, lift=0, piece=(2, 3), taper=0.9, occlude=False)
    dot(x, y, r=1.2, w=w)


# ---------------------------------------------------------------- the arms

K = math.tan(math.radians(21))
R0 = 55.0


class Arm:
    def __init__(self, th0, T, wscale, seed):
        self.th0, self.T, self.ws = th0, T, wscale
        r = random.Random(seed)
        self.ph = [r.uniform(0, 6.3) for _ in range(8)]

    def r(self, t):
        return R0 * np.exp(K * t)

    def W(self, t):
        """Arm width in the disc plane (works on arrays too)."""
        u = np.clip(np.asarray(t, dtype=float) / self.T, 0.0, 1.0)
        base = 26 + 165 * u ** 0.5 * (1 - u) ** 0.4
        return self.ws * base * (1 + 0.1 * np.sin(3.1 * t + self.ph[0]) + 0.06 * np.sin(7.3 * t + self.ph[1]))

    def wob(self, t, k):
        return math.sin(2.3 * t + self.ph[2] + k * 1.7) * 0.6 + math.sin(5.9 * t + self.ph[3] + k * 2.9) * 0.4

    def plane(self, t, d):
        th = self.th0 + t
        rr = float(self.r(t)) + d
        return (rr * math.cos(th), rr * math.sin(th))

    def P(self, t, d):
        return proj(*self.plane(t, d))

    def d_in(self, t):
        return -0.38 * self.W(t)

    def d_out(self, t):
        return 0.62 * self.W(t)

    def D(self, t):
        """Width of the dust lane along the inner edge."""
        u = t / self.T
        if u > 0.92:
            return 0.0
        return (10 + 38 * math.sin(math.pi * min(1.0, u / 0.92)) ** 0.6) * (1 + 0.2 * math.sin(4.3 * t + self.ph[4]))

    def ts(self, t0, t1, step=2.0):
        out = []
        t = t0
        while t < t1:
            out.append(t)
            t += step / (float(self.r(t)) * 1.07)
        out.append(t1)
        return out

    def at(self, t, f, wob=0.0, k=0):
        di, do = self.d_in(t), self.d_out(t)
        return self.P(t, di + f * (do - di) + wob * self.W(t) * self.wob(t, k))

    def rail(self, f, t0, t1, wob=0.0, k=0, step=2.0):
        """A line along the arm at fraction f across it (0 inner edge, 1 outer edge)."""
        return [self.at(t, f, wob, k) for t in self.ts(t0, t1, step)]

    def lane_rail(self, t0, t1, extra=0.0):
        return [self.P(t, self.d_in(t) - self.D(t) * (1 + extra)) for t in self.ts(t0, t1)]

    def band(self):
        a = [self.P(t, self.d_in(t) - self.D(t) - 4) for t in self.ts(0, self.T)]
        b = [self.P(t, self.d_out(t) + 4) for t in self.ts(0, self.T)]
        return a + b[::-1]

    def coords(self, U, V):
        """Arm parameter t and radial offset d for disc-plane points (arrays)."""
        r = np.hypot(U, V)
        base = np.mod(np.arctan2(V, U) - self.th0, 2 * np.pi)
        best_t = np.full(U.shape, np.nan)
        best_d = np.full(U.shape, np.inf)
        for n in range(-1, 3):
            t = base + 2 * np.pi * n
            d = r - R0 * np.exp(K * t)
            ok = (t > -1.0) & (t < self.T + 1.5) & (np.abs(d) < np.abs(best_d))
            best_t = np.where(ok, t, best_t)
            best_d = np.where(ok, d, best_d)
        return best_t, best_d


ALPHA = math.radians(195)
ARM = [Arm(ALPHA, 5.36, 1.3, 5), Arm(ALPHA + math.pi, 5.22, 1.24, 9)]

BA, BB = 84.0, 66.0      # bulge silhouette semi-axes on the page
BULGE.add(ellipse_pts(CX, CY, BA, BB, PHI, step=1.5))
for arm in ARM:
    ARMS.add(arm.band())

# ---------------------------------------------------------------- the gas envelope: a noisy density field

GS = 2.0
gx = np.arange(0, 1000 + GS, GS)
GX, GY = np.meshgrid(gx, gx)
dx0, dy0 = GX - CX, GY - CY
GU = dx0 * cP + dy0 * sP
GV = (-dx0 * sP + dy0 * cP) / Q


def smooth_noise(n_waves, scale, seed):
    r = np.random.default_rng(seed)
    out = np.zeros_like(GX)
    for _ in range(n_waves):
        a = r.uniform(0, np.pi)
        f = r.uniform(0.6, 1.4) / scale
        out += np.sin((GX * np.cos(a) + GY * np.sin(a)) * f * 2 * np.pi + r.uniform(0, 6.3))
    return out / math.sqrt(n_waves / 2)


def sig(x):
    return 1 / (1 + np.exp(-x))


FIELD = np.zeros_like(GX)
ECOORD = np.full(GX.shape, np.nan)
for k, arm in enumerate(ARM):
    t, d = arm.coords(GU, GV)
    tt = np.clip(t, 0, arm.T)
    W = arm.W(tt)
    e = (d + 0.38 * W) / W
    nz = smooth_noise(9, 60, 11 + k) + 0.25 * smooth_noise(9, 30, 31 + k)
    body = sig((1.02 + 0.09 * nz - e) * 10) * sig((e + 0.05) * 25)
    along = sig((t - 0.25) * 4) * sig((arm.T * 0.97 - t) * 3)
    body = np.where(np.isfinite(t), body * along, 0)
    FIELD = np.maximum(FIELD, body)
    closer = np.isfinite(t) & (np.abs(e - 0.5) < np.abs(np.nan_to_num(ECOORD, nan=99) - 0.5))
    ECOORD = np.where(closer, e, ECOORD)


def contours(F, level, x0=0.0, y0=0.0, step=None):
    """Marching squares: polylines where F crosses level (page units)."""
    step = GS if step is None else step
    B = F > level
    c = (B[:-1, :-1].astype(np.uint8) | (B[:-1, 1:].astype(np.uint8) << 1)
         | (B[1:, 1:].astype(np.uint8) << 2) | (B[1:, :-1].astype(np.uint8) << 3))
    ii, jj = np.nonzero((c != 0) & (c != 15))

    def pt(edge):
        kind, i, j = edge
        if kind == 'h':
            a, b = F[i, j], F[i, j + 1]
            return (x0 + (j + (level - a) / (b - a)) * step, y0 + i * step)
        a, b = F[i, j], F[i + 1, j]
        return (x0 + j * step, y0 + (i + (level - a) / (b - a)) * step)

    adj = {}

    def link(a, b):
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    segs = {1: 'lt', 2: 'tr', 3: 'lr', 4: 'rb', 6: 'tb', 7: 'lb', 8: 'bl', 9: 'tb',
            11: 'rb', 12: 'rl', 13: 'tr', 14: 'lt'}
    for i, j in zip(ii.tolist(), jj.tolist()):
        code = int(c[i, j])
        E = {'t': ('h', i, j), 'r': ('v', i, j + 1), 'b': ('h', i + 1, j), 'l': ('v', i, j)}
        if code in (5, 10):
            centre = (F[i, j] + F[i, j + 1] + F[i + 1, j + 1] + F[i + 1, j]) / 4 > level
            if code == 5:
                pairs = ['lb', 'tr'] if centre else ['lt', 'rb']
            else:
                pairs = ['tl', 'rb'] if centre else ['tr', 'bl']
        else:
            pairs = [segs[code]]
        for pr in pairs:
            link(E[pr[0]], E[pr[1]])
    seen = set()
    lines = []
    for start in list(adj):
        if start in seen:
            continue
        cur, prev = start, None
        while True:
            nb = [x for x in adj[cur] if x != prev]
            if len(adj[cur]) < 2 or not nb:
                break
            prev, cur = cur, nb[0]
            if cur == start:
                break
        chain = [cur]
        seen.add(cur)
        prev = None
        while True:
            nb = [x for x in adj[chain[-1]] if x != prev and x not in seen]
            if not nb:
                if len(chain) > 2 and chain[0] in adj[chain[-1]]:
                    chain.append(chain[0])
                break
            prev = chain[-1]
            chain.append(nb[0])
            seen.add(nb[0])
        lines.append([pt(e) for e in chain])
    return lines


def smooth(pts, n=2):
    for _ in range(n):
        if len(pts) < 3:
            return pts
        q = [pts[0]] + [((pts[i - 1][0] + 2 * pts[i][0] + pts[i + 1][0]) / 4,
                         (pts[i - 1][1] + 2 * pts[i][1] + pts[i + 1][1]) / 4) for i in range(1, len(pts) - 1)] + [pts[-1]]
        pts = q
    return pts


def e_at(p):
    j, i = int(round(p[0] / GS)), int(round(p[1] / GS))
    if 0 <= i < FIELD.shape[0] and 0 <= j < FIELD.shape[1]:
        return ECOORD[i, j]
    return float('nan')


# ---------------------------------------------------------------- star-forming clouds (front of everything)


def nebula(arm, u, ec, scale=1.0):
    """A star-forming cloud on the arm: a heap of round billows rising out of it."""
    tc = u * arm.T
    Wp = float(arm.W(tc))
    dc = -0.38 * Wp + ec * Wp
    c = arm.P(tc, dc)
    p2 = arm.P(tc + 0.03, dc)
    rot = math.atan2(p2[1] - c[1], p2[0] - c[0])
    cr, sr = math.cos(rot), math.sin(rot)
    pout = arm.P(tc, dc + 10)
    ox, oy = pout[0] - c[0], pout[1] - c[1]
    fore = math.hypot(ox, oy) / 10
    ox, oy = ox / (fore * 10), oy / (fore * 10)
    Lc = (0.4 * Wp + 24) * scale
    H = (0.26 * Wp * max(0.85, fore) + 15) * scale
    bil = []
    n = min(rng.choice([7, 8, 9]), max(4, int(round(Lc / (H * 0.36)))))
    for i in range(n):
        a = (i / (n - 1) - 0.5) * Lc * 0.9 + G(Lc * 0.03)
        taper = max(0.0, 1 - (2 * a / Lc) ** 2)
        r = H * (0.2 + 0.26 * taper) * R(0.8, 1.2)
        b = R(-0.1, 0.2) * H + 0.25 * H * taper
        bil.append([c[0] + cr * a + ox * b, c[1] + sr * a + oy * b, r])
    # a second tier heaped on the middle
    for _ in range(rng.choice([3, 4, 4, 5])):
        a = G(Lc * 0.2)
        taper = max(0.0, 1 - (2 * a / Lc) ** 2)
        r = H * R(0.22, 0.36) * (0.6 + 0.4 * taper)
        b = H * R(0.5, 0.8) * taper
        bil.append([c[0] + cr * a + ox * b, c[1] + sr * a + oy * b, r])
    # depth: the low ones (in the arm) in front, those heaped on top behind
    for bb in bil:
        bb.append((bb[0] - c[0]) * ox + (bb[1] - c[1]) * oy)
    bil.sort(key=lambda bb: bb[3])          # front first
    ph = [(R(0, 6.3), R(0, 6.3)) for _ in bil]
    m = max(bb[2] for bb in bil) * 1.3 + 4
    x0 = min(bb[0] - bb[2] for bb in bil) - m
    y0 = min(bb[1] - bb[2] for bb in bil) - m
    x1 = max(bb[0] + bb[2] for bb in bil) + m
    y1 = max(bb[1] + bb[2] for bb in bil) + m
    step = 1.0
    LX, LY = np.meshgrid(np.arange(x0, x1, step), np.arange(y0, y1, step))
    F = np.full(LX.shape, -9.0)
    OWN = np.zeros(LX.shape, dtype=int)
    for i, (bx, by, r, _) in enumerate(bil):
        th = np.arctan2(LY - by, LX - bx)
        rr = r * (1 + 0.035 * np.sin(3 * th + ph[i][0]) + 0.025 * np.sin(5 * th + ph[i][1]))
        f = 1 - np.hypot(LX - bx, LY - by) / rr
        OWN = np.where(f > F, i, OWN)
        F = np.maximum(F, f)
    return dict(c=c, rot=rot, Lc=Lc, H=H, bil=bil, ph=ph, F=F, OWN=OWN, x0=x0, y0=y0, step=step,
                out=(ox, oy), arm=arm, tc=tc)


def nb_idx(nb, p):
    j = int(round((p[0] - nb['x0']) / nb['step']))
    i = int(round((p[1] - nb['y0']) / nb['step']))
    if 0 <= i < nb['F'].shape[0] and 0 <= j < nb['F'].shape[1]:
        return i, j
    return None


def nb_F(nb, p):
    ij = nb_idx(nb, p)
    return float(nb['F'][ij]) if ij else -9.0


def billow_r(nb, i, th):
    bx, by, r, _ = nb['bil'][i]
    a, b = nb['ph'][i]
    return r * (1 + 0.035 * math.sin(3 * th + a) + 0.025 * math.sin(5 * th + b))


def inside_billow(nb, i, p):
    bx, by, r, _ = nb['bil'][i]
    th = math.atan2(p[1] - by, p[0] - bx)
    return math.hypot(p[0] - bx, p[1] - by) < billow_r(nb, i, th)


def normal_facing(cx, cy, p):
    nx, ny = p[0] - cx, p[1] - cy
    L = math.hypot(nx, ny) or 1
    return (nx * LIGHT[0] + ny * LIGHT[1]) / L


def draw_nebula(nb):
    blk = lambda p: CLOUD(p) or BULGE(p)
    bil = nb['bil']
    sil = [smooth(l, 1) for l in contours(nb['F'], 0.0, nb['x0'], nb['y0'], nb['step'])]
    sil = [l for l in sil if length(l) > 12]

    def owner(p):
        ij = nb_idx(nb, p)
        return int(nb['OWN'][ij]) if ij else 0

    # the silhouette: heavy on the shadow side, light (and here and there lost) where the light falls
    for line in sil:
        pts = resample(line, 2.0)
        i = 0
        while i < len(pts) - 1:
            j = min(len(pts) - 1, i + rng.randint(5, 9))
            seg = pts[i:j + 1]
            o = owner(seg[len(seg) // 2])
            f = sum(normal_facing(bil[o][0], bil[o][1], p) for p in seg) / len(seg)
            if f > 0.5 and rng.random() < 0.4:
                i = j + 1
                continue
            w = 1.3 if f > 0.35 else (2.05 if f < -0.25 else 1.65)
            ink(seg, w, block=blk, hand=0.25, lift=0.0, piece=(30, 60))
            i = j
        # shading that echoes the silhouette inside it, on the shadow side
        for k in range(1, 4):
            off = 5.0 * k
            thr = 0.05 - 0.22 * k
            moved = []
            for p in pts:
                o = owner(p)
                bx, by = bil[o][0], bil[o][1]
                L = math.hypot(p[0] - bx, p[1] - by) or 1
                q = (p[0] - (p[0] - bx) / L * off, p[1] - (p[1] - by) / L * off)
                moved.append((q, normal_facing(bx, by, p), o))
            good = lambda mm: mm[1] < thr and nb_F(nb, mm[0]) > 0.03 and owner(mm[0]) == mm[2]
            for run in runs_where(moved, good):
                run = smooth([mm[0] for mm in run], 2)
                if length(run) > 5:
                    ink(run, 0.72, block=blk, hand=0.15, lift=0.0, piece=(25, 50), taper=0.3)
    # inner billow edges: where a front billow swells over one behind it, its upper rim shows
    for i, (bx, by, r, _) in enumerate(bil):
        pts = []
        N = max(30, int(r * 4))
        for k in range(N + 1):
            th = 2 * math.pi * k / N
            rr = billow_r(nb, i, th) - 0.5
            pts.append((bx + rr * math.cos(th), by + rr * math.sin(th)))

        def shows(p, i=i, bx=bx, by=by):
            if normal_facing(bx, by, p) < -0.45:
                return False
            if any(inside_billow(nb, k2, p) for k2 in range(i)):   # hidden by one in front
                return False
            return any(inside_billow(nb, k2, p) for k2 in range(i + 1, len(bil)))  # over one behind
        for run in runs_where(pts, shows):
            if length(run) > 6:
                ink(run, 1.15, block=blk, hand=0.2, lift=0.0, piece=(20, 40), taper=0.3)
        # and each billow's own shading, a crescent or two on its far side
        for k in (1, 2):
            if r - 5.0 * k < 3:
                break
            arc = []
            for kk in range(N + 1):
                th = 2 * math.pi * kk / N
                rr = billow_r(nb, i, th) - 5.0 * k
                arc.append((bx + LIGHT[0] * 1.5 * k + rr * math.cos(th), by + LIGHT[1] * 1.5 * k + rr * math.sin(th)))
            ok = lambda p, k=k, bx=bx, by=by, i=i: (normal_facing(bx, by, p) < -0.15 - 0.3 * k
                                                    and not any(inside_billow(nb, k2, p) for k2 in range(i)))
            for run in runs_where(arc, ok):
                if length(run) > 5:
                    ink(run, 0.7, block=blk, hand=0.15, lift=0.0, piece=(20, 40), taper=0.35)
    for line in sil:
        if len(line) > 3 and dist(line[0], line[-1]) < 3:
            CLOUD.add(line)


nebulae = []
for u, ec, sc in [(0.31, 0.55, 0.65), (0.48, 0.55, 1.1), (0.62, 0.6, 1.05), (0.75, 0.5, 1.0),
                  (0.87, 0.58, 0.8)]:
    nebulae.append(nebula(ARM[0], u + G(0.01), ec, sc))
for u, ec, sc in [(0.35, 0.55, 0.7), (0.51, 0.6, 1.1), (0.65, 0.5, 1.05), (0.78, 0.58, 0.95),
                  (0.9, 0.5, 0.75)]:
    nebulae.append(nebula(ARM[1], u + G(0.01), ec, sc))

for nb in sorted(nebulae, key=lambda nb: -nb['c'][1]):
    draw_nebula(nb)
    c, rot, Lc = nb['c'], nb['rot'], nb['Lc']
    # wisps streaming off along the arm
    for sgn in (1, -1):
        for _ in range(rng.choice([1, 1, 2])):
            a = rot + (0 if sgn > 0 else math.pi) + G(0.12)
            p0 = (c[0] + math.cos(a) * Lc * 0.42, c[1] + math.sin(a) * Lc * 0.42)
            L = Lc * R(0.5, 0.9)
            curl = rng.choice([-1, 1]) * R(0.2, 0.6)
            pts = [p0]
            for j in range(1, 6):
                aa = a + curl * j / 5
                pts.append((pts[-1][0] + math.cos(aa) * L / 5, pts[-1][1] + math.sin(aa) * L / 5))
            ink(catmull(pts, step=2), R(0.85, 1.1), block=lambda p: CLOUD(p) or BULGE(p), hand=0.3, taper=0.75,
                piece=(6, 12))
    # the young star that lights it
    big = max(nb['bil'][:3], key=lambda b: b[2])
    sparkle(big[0] + G(2), big[1] + G(2), min(9, big[2] * 0.45), w=1.1, rot=R(-0.2, 0.2), diag=0)

# ---------------------------------------------------------------- dust lanes


def lane_hatch(arm, t0, t1, spacing, skew, w, block=None, layer=0):
    """Hatching across the dust lane, from its ragged inner border to the arm's hard edge."""
    ts = arm.ts(t0, t1, 0.5)
    mid = [arm.P(t, arm.d_in(t) - arm.D(t) * 0.5) for t in ts]
    acc = [0.0]
    for i in range(1, len(mid)):
        acc.append(acc[-1] + dist(mid[i - 1], mid[i]))
    s = R(0, spacing)
    j = 0
    while s < acc[-1]:
        while j < len(acc) - 1 and acc[j + 1] < s:
            j += 1
        t = ts[j]
        Dt = arm.D(t)
        if Dt > 2:
            dep = R(0.7, 1.15) if layer == 0 else R(0.35, 0.65)
            dt = skew / float(arm.r(t))
            a = arm.P(t - dt, arm.d_in(t) - Dt * dep)
            b = arm.P(t + dt * 0.3, arm.d_in(t) + 1.0)
            ink([a, b], w * R(0.9, 1.1), block=block, hand=0.3, lift=0.0, piece=(60, 120), minlen=3)
        s += spacing * R(0.94, 1.06)
    pen.hatch_spacings.append(spacing)


def lane_block(p):
    return BULGE(p) or CLOUD(p)


for k, arm in enumerate(ARM):
    T = arm.T
    lane_hatch(arm, 0.0, 0.92 * T, 5.5, 13.0, 0.92, block=lane_block)
    lane_hatch(arm, 0.05 * T, 0.8 * T, 6.5, -16.0, 0.8, block=lane_block, layer=1)
    for seg in chop(arm.lane_rail(0.02 * T, 0.9 * T, extra=0.1), 30, 110, 6, 22, keep=0.8):
        ink(seg, 1.0, block=lane_block, hand=0.8, lift=0.1)

# the inner dust lane, crossing in front of the bulge on the near side
lane_in, lane_out = [], []
for i in range(121):
    th = math.radians(-8 + 196 * i / 120)
    r1 = 60 + 3 * math.sin(3 * th + 1)
    r2 = 75 + 4 * math.sin(2 * th + 2)
    lane_in.append(proj(r1 * math.cos(th), r1 * math.sin(th)))
    lane_out.append(proj(r2 * math.cos(th), r2 * math.sin(th)))
LANE.add(lane_in + lane_out[::-1])
acc = 0.0
for i in range(1, len(lane_in)):
    acc += dist(lane_in[i - 1], lane_in[i])
    if acc >= 5.6:
        acc = R(-0.3, 0.3)
        j = min(len(lane_out) - 1, i + 2)
        ink([lane_out[j], lane_in[i]], 0.85, hand=0.2, lift=0.0, minlen=2)
for seg in chop(lane_in, 60, 160, 3, 8):
    ink(seg, 1.5, hand=0.3)
for seg in chop(lane_out, 30, 90, 5, 14, keep=0.85):
    ink(seg, 0.95, hand=0.5)

# ---------------------------------------------------------------- bulge and core


def bulge_block(p):
    return LANE(p) or CLOUD(p)


KW = math.tan(math.radians(23))
QW = 0.72
NW = 7
for i in range(NW):
    th0 = ALPHA + 2 * math.pi * i / NW + R(-0.12, 0.12)
    r_s = R(7, 13)
    r_e = R(76, 86)
    pts = []
    th = 0.0
    while True:
        rr = r_s * math.exp(KW * th)
        if rr > r_e:
            break
        pts.append(tilt(rr * math.cos(th0 + th), rr * math.sin(th0 + th) * QW))
        th += 1.5 / rr
    for seg in chop(pts, 70, 240, 3, 7, keep=1.0):
        rr = math.hypot(seg[len(seg) // 2][0] - CX, seg[len(seg) // 2][1] - CY)
        w = 2.5 - 1.1 * min(1.0, rr / 80)
        ink(seg, w, block=bulge_block, hand=0.4, lift=0.05)

# the nucleus wound tightest: short heavy turns close about it
for i in range(5):
    th0 = ALPHA + 2 * math.pi * i / 5 + R(-0.1, 0.1)
    pts = []
    th = 0.0
    r_s = R(8.5, 10.5)
    while True:
        rr = r_s * math.exp(math.tan(math.radians(18)) * th)
        if rr > R(26, 34):
            break
        pts.append(tilt(rr * math.cos(th0 + th), rr * math.sin(th0 + th) * QW))
        th += 1.0 / rr
    ink(pts, 2.3, block=bulge_block, hand=0.2, lift=0.0, piece=(10, 20), taper=0.35)

# the bulge's rim, where it rises behind the near disc and before the far disc
for rr, w, fr in [(70, 1.1, 0.42), (84, 1.6, 0.5)]:
    a0 = math.pi * 1.0 + R(-0.2, 0.2)
    pts = ellipse_pts(CX, CY, rr, rr * BB / BA, PHI, a0, a0 + 2 * math.pi * fr, step=1.5)
    for seg in chop(pts, 50, 140, 5, 14, keep=0.95):
        ink(seg, w, block=bulge_block, hand=0.5)

ink(ellipse_pts(CX, CY, 6.0, 5.0, PHI, 0, 2 * math.pi + 0.3, step=0.6), 2.2, hand=0, lift=0, piece=(8, 14))
pen.blot(CX, CY, 2.4, 2.0, rot=PHI, w=1.6)
sparkle(CX, CY, 36, w=1.7, rot=PHI, diag=0.0)

for _ in range(70):
    rr = 82 * (R() ** 0.8)
    a = R(0, 2 * math.pi)
    p = tilt(rr * math.cos(a), rr * math.sin(a) * (BB / BA))
    if rr > 14 and not bulge_block(p):
        dot(p[0], p[1], r=R(0.8, 1.2), w=1.0)

# ---------------------------------------------------------------- the arms' gassy outer side


def disc_block(p):
    return BULGE(p) or CLOUD(p)


for line in contours(FIELD, 0.5):
    line = smooth(line, 2)
    if length(line) < 10:
        continue
    for sgm in runs_where(resample(line, 2.0), lambda p: np.isfinite(e_at(p)) and e_at(p) > 0.45):
        for piece in chop(sgm, 50, 180, 4, 14, keep=0.92):
            ink(piece, 1.45, block=disc_block, hand=0.5)

# ---------------------------------------------------------------- the arms' flowing lines

for k, arm in enumerate(ARM):
    T = arm.T
    for seg in chop(arm.rail(0.0, 0.0, 0.93 * T, wob=0.015, k=0), 100, 320, 3, 8):
        ink(seg, 2.45, block=disc_block, hand=0.5, lift=0.04, piece=(30, 80))
    for seg in chop(arm.rail(0.05, 0.08 * T, 0.88 * T, wob=0.02, k=1), 50, 160, 8, 30, keep=0.9):
        ink(seg, 1.75, block=disc_block, hand=0.7)
    n = 15
    for i in range(n):
        f = 0.1 + 0.84 * (i / (n - 1)) ** 1.1
        t0 = T * R(0.0, 0.06) + T * 0.05 * f
        t1 = T * (0.98 - 0.12 * f ** 1.5 - R(0, 0.05))
        w = 1.55 - 0.5 * f
        keep = 0.95 - 0.25 * f
        for seg in chop(arm.rail(f, t0, t1, wob=0.045, k=i + 2), 70, 240, 3, 12, keep=keep):
            ink(seg, w * R(0.9, 1.1), block=disc_block, hand=0.7)
    # spurs feathering off the outer side into the gap between the arms
    for u in [0.32, 0.45, 0.56, 0.66, 0.78]:
        t = u * T + G(0.06)
        pts = [arm.P(t + j * 0.02, arm.d_out(t) * 0.9 + j * float(arm.W(t)) * 0.05) for j in range(10)]
        ink(pts, 0.85, block=disc_block, hand=0.6, taper=0.6)
    # the arm's tip unravels into wisps of gas
    for j in range(7):
        t0 = 0.84 * T + R(-0.05, 0.05)
        f = R(0.0, 1.0)
        pts = []
        tt = t0
        drift = R(-0.4, 1.2)
        tend = T + R(0.1, 0.35)
        while tt < tend:
            tc = min(tt, T)
            d = arm.d_in(tc) + f * (arm.d_out(tc) - arm.d_in(tc)) + drift * (tt - t0) * 40
            pts.append(arm.P(tt, d))
            tt += 2.0 / (float(arm.r(tt)) * 1.07)
        ink(pts, R(0.8, 1.15), block=disc_block, hand=1.0, taper=0.6)

# ---------------------------------------------------------------- the disc between the arms


def gap_block(p):
    return BULGE(p) or ARMS(p) or CLOUD(p)


for i in range(20):
    th0 = 2 * math.pi * i / 20 + R(-0.08, 0.08)
    pts = []
    t = 0.0
    while True:
        rr = 75 * math.exp(K * t)
        if rr > 390:
            break
        a = th0 + t
        pts.append(proj(rr * math.cos(a), rr * math.sin(a)))
        t += 2.0 / rr
    for seg in chop(pts, 18, 55, 14, 50, keep=0.6):
        ink(seg, 0.65, block=gap_block, hand=0.6)

# ---------------------------------------------------------------- stars and clusters

# young clusters beside the clouds and strung along the arms
for nb in nebulae:
    c, rot, r0 = nb['c'], nb['rot'], nb['Lc'] * 0.3
    if rng.random() < 0.8:
        a = rot + rng.choice([0.4, -0.4, math.pi - 0.4, math.pi + 0.4])
        q0 = (c[0] + math.cos(a) * r0 * 2.0, c[1] + math.sin(a) * r0 * 1.8)
        for j in range(rng.choice([4, 5, 6, 7])):
            q = (q0[0] + G(4.0), q0[1] + G(3.0))
            if not CLOUD(q):
                dot(q[0], q[1], r=R(0.8, 1.6) if j else 1.9, w=1.25)
for arm in ARM:
    for _ in range(10):
        t = R(0.15, 0.95) * arm.T
        c = arm.at(t, R(0.1, 0.8))
        if disc_block(c):
            continue
        for j in range(rng.choice([4, 5, 6, 8])):
            q = (c[0] + G(4.0), c[1] + G(3.0))
            if not CLOUD(q):
                dot(q[0], q[1], r=R(0.8, 1.6) if j else 1.9, w=1.25)

for _ in range(220):
    rr = 450 * math.sqrt(R(0.04, 1.0)) ** 1.15
    a = R(0, 2 * math.pi)
    p = proj(rr * math.cos(a), rr * math.sin(a))
    if BULGE(p) or CLOUD(p):
        continue
    dot(p[0], p[1], r=R(0.8, 1.3), w=R(0.9, 1.15))


def in_disc(p, pad=0.0):
    u, v = unproj(*p)
    return math.hypot(u, v) < 450 + pad


placed = []
for _ in range(400):
    if len(placed) >= 60:
        break
    p = (R(25, 975), R(25, 975))
    if in_disc(p, 30) or any(dist(p, q) < 45 for q in placed):
        continue
    placed.append(p)
    dot(p[0], p[1], r=R(0.9, 1.6), w=R(1.0, 1.3))
for p, L in [((88, 110), 18), ((880, 92), 14), ((835, 880), 16), ((150, 860), 12),
             ((610, 950), 9), ((60, 520), 9), ((945, 470), 10), ((395, 60), 9)]:
    sparkle(p[0], p[1], L, w=1.3, rot=R(-0.1, 0.1), diag=0.3)

# the set's finest line is 0.6
pen.strokes = [(p, max(0.6, w)) for p, w in pen.strokes]
pen.save('../01-galaxy.svg', mirror=False)
pen.report()
