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
        base = 26 + 165 * u ** 0.5 * (1 - u) ** 0.3
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
UCOORD = np.full(GX.shape, np.nan)
for k, arm in enumerate(ARM):
    t, d = arm.coords(GU, GV)
    tt = np.clip(t, 0, arm.T)
    W = arm.W(tt)
    e = (d + 0.38 * W) / W
    nz = smooth_noise(9, 60, 11 + k) + 0.25 * smooth_noise(9, 30, 31 + k)
    body = sig((1.02 + 0.065 * nz - e) * 10) * sig((e + 0.05) * 25)
    along = sig((t - 0.25) * 4) * sig((arm.T * 0.97 - t) * 3)
    body = np.where(np.isfinite(t), body * along, 0)
    FIELD = np.maximum(FIELD, body)
    closer = np.isfinite(t) & (np.abs(e - 0.5) < np.abs(np.nan_to_num(ECOORD, nan=99) - 0.5))
    ECOORD = np.where(closer, e, ECOORD)
    UCOORD = np.where(closer, t / arm.T, UCOORD)


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


def u_at(p):
    j, i = int(round(p[0] / GS)), int(round(p[1] / GS))
    if 0 <= i < FIELD.shape[0] and 0 <= j < FIELD.shape[1]:
        return UCOORD[i, j]
    return float('nan')


def e_at(p):
    j, i = int(round(p[0] / GS)), int(round(p[1] / GS))
    if 0 <= i < FIELD.shape[0] and 0 <= j < FIELD.shape[1]:
        return ECOORD[i, j]
    return float('nan')


# ---------------------------------------------------------------- star-forming knots on the arms' outer edges


def fine_noise(LX, LY, scale, seed, n=8):
    q = np.random.default_rng(seed)
    out = np.zeros_like(LX)
    for _ in range(n):
        a = q.uniform(0, np.pi)
        f = q.uniform(0.7, 1.3) / scale
        out += np.sin((LX * np.cos(a) + LY * np.sin(a)) * f * 2 * np.pi + q.uniform(0, 6.3))
    return out / math.sqrt(n / 2)


def knot(arm, u, ec, size):
    """A glowing knot of gas on the arm's outer edge: a clumpy density field with frilled edges."""
    tc = u * arm.T
    Wp = float(arm.W(tc))
    dc = -0.38 * Wp + ec * Wp
    c = arm.P(tc, dc)
    p2 = arm.P(tc + 0.03, dc)
    rot = math.atan2(p2[1] - c[1], p2[0] - c[0])
    cr, sr = math.cos(rot), math.sin(rot)
    pw = dist(arm.P(tc, arm.d_in(tc)), arm.P(tc, arm.d_out(tc)))
    Hk = size * max(0.65, min(1.1, pw / 85))
    Lk = Hk * R(1.3, 1.6)
    blobs = []
    n = rng.choice([6, 7, 8])
    for i in range(n):
        a = (i / (n - 1) - 0.5) * Lk * 0.75 + G(Lk * 0.05)
        taper = max(0.0, 1 - (2 * a / Lk) ** 2)
        b = G(Hk * 0.2)
        s = Hk * R(0.22, 0.36) * (0.7 + 0.3 * taper)
        blobs.append((c[0] + cr * a - sr * b, c[1] + sr * a + cr * b, s, R(0.8, 1.1)))
    m = 3.2 * max(bb[2] for bb in blobs)
    x0 = min(bb[0] for bb in blobs) - m
    y0 = min(bb[1] for bb in blobs) - m
    x1 = max(bb[0] for bb in blobs) + m
    y1 = max(bb[1] for bb in blobs) + m
    LX, LY = np.meshgrid(np.arange(x0, x1, 1.0), np.arange(y0, y1, 1.0))
    F = np.zeros_like(LX)
    for bx, by, s, amp in blobs:
        F += amp * np.exp(-0.5 * ((LX - bx) ** 2 + (LY - by) ** 2) / (s * s))
    F *= 1 + 0.26 * fine_noise(LX, LY, 11, rng.randrange(10 ** 6))
    F /= F.max()
    star = max(blobs, key=lambda bb: bb[2] * bb[3])
    return dict(c=c, rot=rot, F=F, x0=x0, y0=y0, x1=x1, y1=y1, star=(star[0], star[1]), size=Hk)


def kval(kn, p):
    j = int(round(p[0] - kn['x0']))
    i = int(round(p[1] - kn['y0']))
    if 0 <= i < kn['F'].shape[0] and 0 <= j < kn['F'].shape[1]:
        return float(kn['F'][i, j])
    return 0.0


K_EDGE, K_CORE, K_HEART = 0.18, 0.42, 0.7


def knot_hatch(kn, angle, spacing, w, lo, full, glow):
    """Hatching inside a knot, whole where the gas is thick, breaking into dashes as it thins out."""
    a = angle
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cx, cy = (kn['x0'] + kn['x1']) / 2, (kn['y0'] + kn['y1']) / 2
    half = math.hypot(kn['x1'] - kn['x0'], kn['y1'] - kn['y0']) / 2
    sx, sy = kn['star']
    o = -half + R(0, spacing)
    while o < half:
        oo = o + G(0.1 * spacing)
        cur = []
        s_ = -half
        chunk_left, chunk_on = 0, False
        while s_ <= half:
            p = (cx + dx * s_ + nx * oo, cy + dy * s_ + ny * oo)
            v = kval(kn, p)
            inside = v > lo and math.hypot(p[0] - sx, p[1] - sy) > glow
            if inside:
                if chunk_left <= 0:
                    d = 1.0 if full <= lo else min(1.0, (v - lo) / (full - lo))
                    chunk_on = d >= 1.0 or rng.random() < d ** 0.7
                    chunk_left = R(3, 8)
                chunk_left -= 1
            if inside and chunk_on:
                cur.append(p)
            elif cur:
                if len(cur) > 2:
                    ink(cur, w * R(0.9, 1.1), block=BULGE, hand=0.2, lift=0.0, piece=(30, 60))
                cur = []
            s_ += 1.0
        if len(cur) > 2:
            ink(cur, w * R(0.9, 1.1), block=BULGE, hand=0.2, lift=0.0, piece=(30, 60))
        o += spacing
    pen.hatch_spacings.append(spacing)


def draw_knot(kn):
    rot = kn['rot']
    # the frilled edge, broken and fine
    for line in contours(kn['F'], K_EDGE, kn['x0'], kn['y0'], 1.0):
        line = smooth(line, 3)
        if length(line) < 30:
            continue
        for seg in chop(line, 18, 55, 4, 10, keep=0.85):
            ink(seg, R(1.15, 1.4), block=BULGE, hand=0.2, lift=0.0, piece=(10, 25))
    # hatching that thins outward, cross-hatched in the thick heart, open round the star
    glow = 6.0 + kn['size'] * 0.1
    knot_hatch(kn, rot + math.radians(58), 5.3, 0.92, K_EDGE + 0.02, K_CORE, glow)
    knot_hatch(kn, rot - math.radians(38), 6.5, 0.8, K_HEART, K_HEART, glow)
    # stipple: the gas thinning into the arm round it
    placed = []
    for _ in range(int(kn['size'] * 12)):
        p = (R(kn['x0'], kn['x1']), R(kn['y0'], kn['y1']))
        v = kval(kn, p)
        if 0.06 < v < K_EDGE + 0.12 and rng.random() < (v / (K_EDGE + 0.12)) ** 1.3:
            if all(dist(p, q) > 4.5 for q in placed):
                placed.append(p)
                dot(p[0], p[1], r=R(0.75, 1.1), w=1.0)
    sx, sy = kn['star']
    sparkle(sx, sy, min(10.5, 5 + kn['size'] * 0.18), w=1.25, rot=R(-0.2, 0.2), diag=0)


def star_cluster(c, n, spread, big=1.9):
    placed = []
    for j in range(n):
        for _ in range(8):
            q = (c[0] + G(spread), c[1] + G(spread * 0.75))
            if all(dist(q, p) > 3.2 for p in placed):
                placed.append(q)
                dot(q[0], q[1], r=big if j == 0 else R(0.8, 1.5), w=1.25)
                break


knots = [knot(ARM[0], 0.45, 0.8, 60), knot(ARM[1], 0.56, 0.8, 62), knot(ARM[0], 0.67, 0.8, 64),
         knot(ARM[1], 0.77, 0.78, 58), knot(ARM[0], 0.87, 0.76, 46), knot(ARM[1], 0.91, 0.74, 42)]
_n0 = len(pen.strokes)
for kn in knots:
    draw_knot(kn)
del pen.strokes[_n0:]      # superseded by the lens-shaped knots drawn last
# the smallest knots are only their clusters of young stars
for arm, u, ec in [(ARM[0], 0.3, 0.9), (ARM[1], 0.35, 0.9), (ARM[0], 0.57, 0.85), (ARM[1], 0.66, 0.85)]:
    t = u * arm.T
    star_cluster(arm.at(t, ec), rng.choice([7, 8, 9]), 5.5)

# ---- the knots as drawn: irregular lenses stretched along the arm, hatched with the flow

krng = random.Random(4242)


def KR(lo=0.0, hi=1.0):
    return lo + (hi - lo) * krng.random()


def kchop(pts, lo, hi, glo, ghi, keep=1.0):
    fine = resample(pts, 1.0)
    n = len(fine)
    out = []
    i = int(KR(0, hi * 0.5))
    while i < n - 1:
        j = min(n - 1, i + int(KR(lo, hi)))
        if j - i >= 2 and krng.random() < keep:
            out.append(fine[i:j + 1])
        i = j + int(KR(glo, ghi))
    return out


def lens_knot(arm, u, ec, scale):
    tc = u * arm.T
    W = float(arm.W(tc))
    dc = -0.38 * W + ec * W
    Hp = 0.36 * W * scale                 # across the arm, in the disc plane
    Lp = Hp * KR(2.0, 2.4)                # along it
    rr = float(arm.r(tc)) * 1.07
    dt = (Lp / 2) / rr
    corners = [arm.P(tc + a * dt * 1.5, dc + b * Hp * 0.9) for a in (-1, -0.5, 0, 0.5, 1) for b in (-1, 1)]
    x0 = min(p[0] for p in corners) - 10
    y0 = min(p[1] for p in corners) - 10
    x1 = max(p[0] for p in corners) + 10
    y1 = max(p[1] for p in corners) + 10
    LX, LY = np.meshgrid(np.arange(x0, x1, 1.0), np.arange(y0, y1, 1.0))
    ddx, ddy = LX - CX, LY - CY
    U = ddx * cP + ddy * sP
    V = (-ddx * sP + ddy * cP) / Q
    t, d = arm.coords(U, V)
    st = (t - tc) * rr / (Lp / 2)
    sd = (d - dc) / (Hp / 2)
    width = np.clip(1 - st ** 2, 0, None) ** 0.6
    F = 1 - (sd / np.maximum(width, 0.08)) ** 2 - 0.25 * st ** 2
    F = np.where(np.isfinite(F), F, -9.0)
    F += 0.22 * fine_noise(LX, LY, 13, krng.randrange(10 ** 6)) + 0.07 * fine_noise(LX, LY, 6, krng.randrange(10 ** 6))
    fore = dist(arm.P(tc, dc), arm.P(tc, dc + 10)) / 10
    star = arm.P(tc + KR(-0.15, 0.15) * dt, dc + KR(-0.1, 0.1) * Hp)
    return dict(arm=arm, tc=tc, dc=dc, Hp=Hp, Lp=Lp, dt=dt, F=F, x0=x0, y0=y0, x1=x1, y1=y1,
                fore=fore, star=star)


LENSES = [lens_knot(ARM[0], 0.45, 0.78, 1.0), lens_knot(ARM[1], 0.56, 0.78, 1.0),
          lens_knot(ARM[0], 0.67, 0.78, 1.05), lens_knot(ARM[1], 0.77, 0.76, 0.95),
          lens_knot(ARM[0], 0.87, 0.74, 0.8), lens_knot(ARM[1], 0.91, 0.72, 0.75)]


def lens_val(kn, p):
    if not (kn['x0'] <= p[0] < kn['x1'] - 1 and kn['y0'] <= p[1] < kn['y1'] - 1):
        return -9.0
    return float(kn['F'][int(p[1] - kn['y0']), int(p[0] - kn['x0'])])


def in_lens(p, level=0.25):
    return any(lens_val(kn, p) > level for kn in LENSES)


def draw_lens(kn):
    arm, tc, dc, Hp, dt = kn['arm'], kn['tc'], kn['dc'], kn['Hp'], kn['dt']
    sx, sy = kn['star']
    glow = 9.0 + 0.1 * Hp * kn['fore']
    # the edge: broken, irregular, fine
    for line in contours(kn['F'], 0.0, kn['x0'], kn['y0'], 1.0):
        line = smooth(line, 3)
        if length(line) < 40:
            continue
        for seg in kchop(line, 20, 60, 4, 10, keep=0.88):
            ink(seg, KR(1.25, 1.5), block=BULGE, hand=0.2, lift=0.0, piece=(10, 25))
    # hatching that runs with the arm, whole in the body, breaking into dashes outward,
    # thinning again round the star so the heart glows
    step = 5.2 / kn['fore']
    d = dc - Hp * 0.7 + KR(0, step)
    while d < dc + Hp * 0.7:
        pts = [arm.P(t, d) for t in arm.ts(tc - 1.3 * dt, tc + 1.3 * dt, 1.0)]
        cur, left, on = [], 0, False
        for p in pts:
            v = lens_val(kn, p)
            inside = v > 0.02 and math.hypot(p[0] - sx, p[1] - sy) > glow
            if inside:
                if left <= 0:
                    dens = min(1.0, v / 0.3) * max(0.45, 1 - 0.5 * max(0.0, (v - 0.55) / 0.45))
                    on = dens >= 0.97 or krng.random() < dens ** 0.8
                    left = KR(4, 10)
                left -= 1
            if inside and on:
                cur.append(p)
            elif cur:
                if len(cur) > 2:
                    ink(cur, 0.95 * KR(0.9, 1.1), block=BULGE, hand=0.25, lift=0.0, piece=(30, 60))
                cur = []
        if len(cur) > 2:
            ink(cur, 0.95 * KR(0.9, 1.1), block=BULGE, hand=0.25, lift=0.0, piece=(30, 60))
        d += step
    pen.hatch_spacings.append(5.2)
    # stipple: the gas thinning into the arm round it
    placed = []
    for _ in range(int(Hp * 6)):
        p = (KR(kn['x0'], kn['x1']), KR(kn['y0'], kn['y1']))
        v = lens_val(kn, p)
        if -0.45 < v < 0.0 and krng.random() < ((v + 0.45) / 0.45) ** 1.5:
            if all(dist(p, q) > 4.5 for q in placed):
                placed.append(p)
                pen.dot(p[0], p[1], r=KR(0.75, 1.1), w=1.0)
    L = min(11.0, 6.0 + Hp * 0.06)
    for k in range(2):
        a = KR(-0.2, 0.2) + k * math.pi / 2
        Lk = L * (1.0 if k == 0 else 0.8)
        pen.line([(sx - math.cos(a) * Lk, sy - math.sin(a) * Lk), (sx, sy), (sx + math.cos(a) * Lk, sy + math.sin(a) * Lk)],
                 w=1.25, hand=0, lift=0, piece=(2.5, 4), taper=0.92, occlude=False)
    pen.dot(sx, sy, r=1.2, w=1.25)


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
    r_s = R(37, 46)
    r_e = R(76, 86)
    pts = []
    th = 0.0
    while True:
        rr = r_s * math.exp(KW * th)
        if rr > r_e:
            break
        pts.append(tilt(rr * math.cos(th0 + th), rr * math.sin(th0 + th) * QW))
        th += 1.5 / rr
    for seg in chop(pts, 50, 200, 3, 8, keep=1.0):
        rr = math.hypot(seg[len(seg) // 2][0] - CX, seg[len(seg) // 2][1] - CY)
        w = 2.2 - 0.9 * min(1.0, rr / 80)
        ink(seg, w, block=bulge_block, hand=0.4, lift=0.05)

# the nucleus: a small white oval of bare paper, ringed by short rays and a few dense arcs
NR = 13
for i in range(NR):
    a = 2 * math.pi * (i + R(-0.15, 0.15)) / NR
    r0 = 9.5
    r1 = r0 + (R(9, 12) if i % 2 == 0 else R(5, 7.5))
    p0 = tilt(r0 * math.cos(a), r0 * math.sin(a) * QW)
    p1 = tilt(r1 * math.cos(a), r1 * math.sin(a) * QW)
    pen.line([p0, p1], w=R(1.15, 1.4), hand=0, lift=0, piece=(3, 5), taper=0.5, occlude=False)
for rr, w in [(25, 1.55), (30, 1.4), (35.5, 1.25)]:
    a0 = R(0, 2 * math.pi)
    span = R(0.55, 0.75) * 2 * math.pi
    pts = [tilt(rr * math.cos(a0 + span * k / 200), rr * math.sin(a0 + span * k / 200) * QW) for k in range(201)]
    for seg in chop(pts, 30, 90, 4, 10, keep=1.0):
        ink(seg, w, block=bulge_block, hand=0.2, lift=0.0)

# the bulge's rim, where it rises behind the near disc and before the far disc
for rr, w, fr in [(70, 1.1, 0.42), (84, 1.6, 0.5)]:
    a0 = math.pi * 1.0 + R(-0.2, 0.2)
    pts = ellipse_pts(CX, CY, rr, rr * BB / BA, PHI, a0, a0 + 2 * math.pi * fr, step=1.5)
    for seg in chop(pts, 50, 140, 5, 14, keep=0.95):
        ink(seg, w, block=bulge_block, hand=0.5)


for _ in range(70):
    rr = 82 * (R() ** 0.8)
    a = R(0, 2 * math.pi)
    p = tilt(rr * math.cos(a), rr * math.sin(a) * (BB / BA))
    if rr > 40 and not bulge_block(p):
        dot(p[0], p[1], r=R(0.8, 1.2), w=1.0)

# ---------------------------------------------------------------- the arms' gassy outer side


def disc_block(p):
    return BULGE(p) or CLOUD(p)


def env_block(p):
    if disc_block(p) or in_lens(p, -0.1):
        return True
    u = u_at(p)
    if np.isfinite(u) and u > 0.88:
        return True
    if 190 < p[0] < 248 and 512 < p[1] < 568:     # the left lobe, in dashes
        return int((p[0] + p[1]) // 6) % 2 == 0
    return False


for line in contours(FIELD, 0.5):
    line = smooth(line, 3)
    closed = dist(line[0], line[-1]) < 3
    if length(line) < 60 or (closed and length(line) < 500):
        continue
    for sgm in runs_where(resample(line, 2.0), lambda p: np.isfinite(e_at(p)) and 0.85 < e_at(p) < 1.2):
        if length(sgm) < 40:
            continue
        for piece in chop(sgm, 50, 180, 4, 14, keep=0.92):
            ink(piece, 1.45, block=env_block, hand=0.5)

# ---------------------------------------------------------------- the arms' flowing lines


def flow_block(p):
    return disc_block(p) or in_lens(p)


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
        t1 = T * (0.99 - 0.08 * f ** 1.5 - R(0, 0.04))
        w = 1.55 - 0.5 * f
        keep = 0.95 - 0.25 * f
        ta, tb = min(t1, 0.74 * T), min(t1, 0.87 * T)
        for seg in chop(arm.rail(f, t0, ta, wob=0.045, k=i + 2), 70, 240, 3, 12, keep=keep):
            ink(seg, w * R(0.9, 1.1), block=flow_block, hand=0.7)
        # toward the tip the lines break into dashes, and the dashes into stars
        if tb > ta:
            for seg in chop(arm.rail(f, ta, tb, wob=0.045, k=i + 2), 25, 70, 5, 14, keep=keep * 0.95):
                ink(seg, w * 0.9 * R(0.9, 1.1), block=flow_block, hand=0.7)
        if t1 > tb:
            for seg in chop(arm.rail(f, tb, t1, wob=0.045, k=i + 2), 8, 24, 7, 18, keep=keep * 0.8):
                ink(seg, w * 0.8 * R(0.9, 1.1), block=flow_block, hand=0.5)
    # the arm's tip unravels into wisps of gas
    for j in range(7):
        t0 = 0.84 * T + R(-0.05, 0.05)
        f = R(0.0, 1.0)
        pts = []
        tt = t0
        drift = R(-0.4, 1.2)
        tend = T + R(0.1, 0.35)
        while tt < tend:
            tc = min(tt, 0.92 * T)       # past the steep taper at the very tip, so no hooks
            d = arm.d_in(tc) + f * (arm.d_out(tc) - arm.d_in(tc)) + drift * 0.35 * (tt - t0) * 40
            pts.append(arm.P(tt, d))
            tt += 2.0 / (float(arm.r(tt)) * 1.07)
        for seg in chop(pts, 8, 26, 6, 16, keep=0.8):
            ink(seg, R(0.8, 1.05), block=disc_block, hand=0.3)
    # small clusters strung along the tail, where the arm fades into stars
    for u in [0.84, 0.92, 0.99, 1.04]:
        t = u * T + G(0.01)
        tc = min(t, T)
        c = arm.P(t, arm.d_in(tc) + R(0.3, 0.7) * (arm.d_out(tc) - arm.d_in(tc)))
        star_cluster(c, rng.choice([5, 6, 7]), 4.5, big=1.7)

# ---------------------------------------------------------------- the disc between the arms


def gap_block(p):
    return BULGE(p) or ARMS(p) or CLOUD(p)


GAPS = [(380, 330), (640, 640)]


def rim_block(p):
    e = e_at(p)
    return gap_block(p) or any(dist(p, g) < 120 for g in GAPS) or (np.isfinite(e) and -0.6 < e < 1.7)


for rr in [385, 420]:
    a0 = R(0, 2 * math.pi)
    ph1, ph2 = R(0, 6.3), R(0, 6.3)
    pts = []
    for k in range(901):
        th = a0 + 2 * math.pi * k / 900
        r_ = rr * (1 + 0.05 * math.sin(2 * th + ph1) + 0.03 * math.sin(5 * th + ph2))
        pts.append(proj(r_ * math.cos(th), r_ * math.sin(th)))
    for seg in chop(pts, 15, 50, 20, 70, keep=0.5):
        ink(seg, 0.7, block=rim_block, hand=0.6)

# ---------------------------------------------------------------- stars and clusters

# young clusters strung along the arms
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
    if BULGE(p) or CLOUD(p) or (any(dist(p, g) < 110 for g in GAPS) and rng.random() < 0.7):
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

for kn in LENSES:
    draw_lens(kn)

# the set's finest line is 0.6
pen.strokes = [(p, max(0.6, w)) for p, w in pen.strokes]
pen.save('../01-galaxy.svg', mirror=False)
pen.report()
