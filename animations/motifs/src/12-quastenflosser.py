"""12 Quastenflosser: a lobe-finned tetrapodomorph (after Tiktaalik, Late Devonian)
heaving its front half out of a shallow puddle onto a muddy bank.

Flattened, crocodile-like head with the eyes on top and no gill cover (a short
neck instead), heavy rhombic scales, a broad chest tapering to a slim tail with a
fringe of fin rays, and fleshy lobed fins: the pectoral bent back at the elbow,
its outer part flexed and pressed on the mud, rays fringing its trailing and
outer edge. The rear third still lies in the water, ripples spreading where it
breaks the surface. Drawn facing right; saved mirrored to face the text.
"""

import math
import sys

import numpy as np

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, clip_segments

pen = Pen(seed=1212)
R, G = pen.r, pen.g
DEBUG = 'debug' in sys.argv


# ---------------------------------------------------------------- helpers

class Curve:
    """A polyline with arc-length lookup: at(t), normal(t) for t in 0..1."""

    def __init__(self, pts, step=1.0):
        self.p = np.array(resample(list(pts), step), dtype=float)
        d = np.hypot(*np.diff(self.p, axis=0).T)
        self.s = np.concatenate([[0.0], np.cumsum(d)])
        self.L = float(self.s[-1])

    def at(self, t):
        s = min(max(t, 0.0), 1.0) * self.L
        return (float(np.interp(s, self.s, self.p[:, 0])), float(np.interp(s, self.s, self.p[:, 1])))

    def tangent(self, t, h=0.006):
        a, b = self.at(t - h), self.at(t + h)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    def normal(self, t):
        """Unit normal to the left of travel (up, for a curve running right)."""
        tx, ty = self.tangent(t)
        return ty, -tx


def poly_clip_below(poly, yfun):
    """Keeps the part of a polygon above (smaller y than) the curve y = yfun(x)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ia, ib = a[1] < yfun(a[0]), b[1] < yfun(b[0])
        if ia:
            out.append(a)
        if ia != ib:
            lo, hi = 0.0, 1.0
            for _ in range(20):
                m = (lo + hi) / 2
                p = lerp(a, b, m)
                if (p[1] < yfun(p[0])) == ia:
                    lo = m
                else:
                    hi = m
            out.append(lerp(a, b, (lo + hi) / 2))
    return out


def stroke(pts, w=1.2, **kw):
    pen.line(pts, w=w, **kw)


def runs(pts, keep):
    return clip_segments(pts, keep)


def ALL(p):
    return True


def band(center, widths, n=140):
    """Both edges of a limb of varying width around a centre line (left = left of travel)."""
    c = Curve(center, step=0.8)
    left, right = [], []
    for k in range(n + 1):
        t = k / n
        w = float(np.interp(t, np.linspace(0, 1, len(widths)), widths)) / 2
        x, y = c.at(t)
        nx, ny = c.normal(t)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return c, left, right


# ---------------------------------------------------------------- body plan

SPINE = Curve(catmull([(156, 711), (198, 714), (244, 714), (292, 704), (344, 687), (404, 661), (461, 627), (517, 591),
                       (571, 557), (621, 527), (667, 502), (707, 483), (740, 470)], step=2.0), step=1.0)

# half-depths (back, belly) along the spine, by x: a broad chest tapering to a slim tail
HX = [156, 190, 240, 300, 360, 420, 480, 540, 600, 650, 695, 720, 740]
HD = [1.5, 5, 10, 18, 27, 36, 45, 52, 58, 60, 57, 51, 46]
HV = [1.5, 6, 12, 22, 33, 44, 55, 66, 74, 76, 68, 60, 53]


def depth(t):
    x = SPINE.at(t)[0]
    return float(np.interp(x, HX, HD)), float(np.interp(x, HX, HV))


def body(t, v):
    """A point on the flank: t along the body (0 tail tip, 1 neck), v from -1 (belly) to 1 (back)."""
    x, y = SPINE.at(t)
    nx, ny = SPINE.normal(t)
    hd, hv = depth(t)
    d = v * (hd if v > 0 else hv)
    return (x + nx * d, y + ny * d)


def t_at_x(x):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        if SPINE.at(m)[0] < x:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


DORSAL = [body(k / 600, 1.0) for k in range(601)]
VENTRAL = [body(k / 600, -1.0) for k in range(601)]
V_X = [p[0] for p in VENTRAL]
V_Y = [p[1] for p in VENTRAL]


def belly_y(x):
    return float(np.interp(x, V_X, V_Y))


# ---------------------------------------------------------------- water

WATER_X = [156, 196, 240, 300, 350, 390, 420, 436]
WATER_V = [0.9, 0.2, -0.3, -0.36, -0.45, -0.62, -0.85, -1.0]


def v_water(t):
    """The waterline across the flank: the tail lies awash, the belly leaves the water at the shore."""
    return float(np.interp(SPINE.at(t)[0], WATER_X, WATER_V))


T_SHORE = t_at_x(WATER_X[-1])
WL = [body(t, v_water(t)) for t in np.linspace(0, T_SHORE, 500)]
WL_X = [p[0] for p in WL]
WL_Y = [p[1] for p in WL]


def water_y(x):
    if x < WL_X[0]:
        return WL_Y[0] - (WL_X[0] - x) * 0.5
    if x > WL_X[-1]:
        return WL_Y[-1] + (x - WL_X[-1]) * 0.6
    return float(np.interp(x, WL_X, WL_Y))


def dry(p):
    return p[1] < water_y(p[0]) - 0.3


def wet(p):
    return not dry(p)


def ink(pts, w, faint=0.6, **kw):
    """A stroke on the animal: firm above the water, faint and broken below it."""
    for run in runs(pts, dry):
        if len(run) > 1:
            pen.line(run, w=w, **kw)
    for run in runs(pts, wet):
        if len(run) > 2 and faint and R() < 0.8:
            pen.line(run, w=faint, hand=0.8, lift=0.55, piece=(4, 10))


# ---------------------------------------------------------------- the ground

# the bank rises out of the water; the belly lies on it, then the chest is propped above it
GROUND = [(436, 726), (452, 706)] + [(x, belly_y(x) + 2.5) for x in (472, 500, 530, 560, 588)] + \
         [(625, 603), (680, 600), (760, 597), (850, 592), (930, 586), (990, 580)]
GROUND_C = catmull(GROUND, step=2.0)


def ground_y(x):
    return float(np.interp(x, [p[0] for p in GROUND_C], [p[1] for p in GROUND_C]))


# ---------------------------------------------------------------- the head frame: u forward from the back of the skull, v up

H_ORIGIN = (754.0, 466.0)
H_ANGLE = math.radians(8.0)
H_V = 1.28
H_U = 1.08
H_DIR = (math.cos(H_ANGLE), -math.sin(H_ANGLE))
H_UP = (H_DIR[1], -H_DIR[0])


def hp(u, v):
    v = v * H_V
    u = u * H_U
    return (H_ORIGIN[0] + u * H_DIR[0] + v * H_UP[0], H_ORIGIN[1] + u * H_DIR[1] + v * H_UP[1])


def hc(pts, step=1.5):
    return catmull([hp(u, v) for u, v in pts], step=step)


SKULL_TOP = [(0, 37), (24, 39.5), (52, 41), (68, 43), (77, 47.5), (88, 49.5), (99, 47.5), (108, 42),
             (134, 37), (160, 30), (182, 21.5), (197, 12), (205, 2), (204, -5)]
LIP = [(204, -5), (190, -9), (160, -12), (125, -14.5), (90, -16.5), (58, -18), (36, -18.5)]
JAW = [(201, -9), (186, -16), (158, -23.5), (122, -30), (86, -36), (52, -41), (24, -44), (6, -44.5)]


def lip_v(u):
    return float(np.interp(u, [0, 36, 58, 90, 125, 160, 190, 204], [-17, -18.5, -18, -16.5, -14.5, -12, -9, -5]))


def jaw_v(u):
    return float(np.interp(u, [0, 6, 24, 52, 86, 122, 158, 186, 201], [-44, -44.5, -44, -41, -36, -30, -23.5, -16, -9]))


def top_v(u):
    return float(np.interp(u, [p[0] for p in SKULL_TOP[:-1]], [p[1] for p in SKULL_TOP[:-1]]))


HEAD_TOP = hc(SKULL_TOP)
UPPER_LIP = hc(LIP)
JAW_LOW = hc(JAW)

# the neck flows from the back into the skull roof, and from the chest into the throat
NT0, NB0 = DORSAL[-1], VENTRAL[-1]
NECK_TOP = catmull([DORSAL[-14], NT0, lerp(NT0, hp(0, 37), 0.5), hp(0, 37), hp(14, 38.5)], step=1.5)[8:-10]
NECK_BOT = catmull([VENTRAL[-14], NB0, lerp(NB0, hp(6, -44.5), 0.55), hp(6, -44.5), hp(20, -44)], step=1.5)[8:-10]

SILHOUETTE = DORSAL + NECK_TOP + HEAD_TOP[1:] + JAW_LOW[::-1] + NECK_BOT[::-1] + VENTRAL[::-1]

if DEBUG:
    for x in (436, 470, 500, 540, 600, 650, 690, 720):
        t = t_at_x(x)
        print(x, 'spine', [round(c) for c in SPINE.at(t)], 'belly', [round(c) for c in body(t, -1)],
              'back', [round(c) for c in body(t, 1)], 'ground', round(ground_y(x)))
    print('snout', hp(205, 0), 'jaw', hp(6, -44.5))


# ---------------------------------------------------------------- fins

def rays(bases, tips, w=0.8, keep=ALL, bow=0.6, margin_w=1.1, faint=False):
    """Fin rays from each base to its tip, slightly bowed, and the fringed margin through the tips."""
    def draw(pts, ww, **kw):
        if faint:
            ink(pts, ww, faint=0.62, **kw)
        else:
            for run in runs(pts, keep):
                if len(run) > 1:
                    pen.line(run, w=ww, **kw)
    for a, b in zip(bases, tips):
        if dist(a, b) < 2.5:
            continue
        m = lerp(a, b, 0.5)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        bb = G(bow)
        m = (m[0] - dy / L * bb, m[1] + dx / L * bb)
        draw(catmull([lerp(a, b, 0.04), m, b], step=1.2), w * R(0.9, 1.1), hand=0.15, lift=0.03, piece=(14, 40))
    draw(catmull(tips, step=1.0), margin_w, hand=0.4, lift=0.3, piece=(4, 12))


def limb_shade(left, right, f0, f1, spacing=4.8, w=0.85, keep=ALL, t0=0.0, t1=1.0):
    """Shade strokes across a limb, from fraction f0 to f1 of the way from its left to its right edge."""
    c = Curve(left, step=1.0)
    n = max(1, int(c.L * (t1 - t0) / spacing))
    N = len(left) - 1
    for k in range(n):
        t = t0 + (t1 - t0) * (k + 0.5 + G(0.1)) / n
        i = min(N, max(0, int(t * N)))
        a = lerp(left[i], right[i], f0 + G(0.03))
        b = lerp(left[i], right[i], f1)
        for run in runs([a, lerp(a, b, 0.5), b], keep):
            if len(run) > 1:
                pen.line(run, w=w * R(0.9, 1.1), hand=0.15, lift=0)


def limb_scales(left, right, f0, f1, size=11.0, w=0.75, keep=ALL, t0=0.08, t1=0.9):
    """Small scales on a fin lobe: short arcs, staggered in rows."""
    c = Curve(left, step=1.0)
    n = max(1, int(c.L * (t1 - t0) / size))
    N = len(left) - 1
    rows = max(1, int((f1 - f0) * dist(left[N // 2], right[N // 2]) / (size * 0.7)))
    for j in range(n):
        for r in range(rows):
            t = t0 + (t1 - t0) * (j + 0.5 + (0.5 if r % 2 else 0)) / n
            if t > t1:
                continue
            i = min(N, int(t * N))
            i2 = min(N, i + max(1, int(N * size * 0.28 / c.L)))
            f = f0 + (f1 - f0) * (r + 0.5) / rows
            p0 = lerp(left[i], right[i], f - 0.07)
            pm = lerp(left[i2], right[i2], f)
            p1 = lerp(left[i], right[i], f + 0.07)
            for run in runs(catmull([p0, pm, p1], step=1.0), keep):
                if len(run) > 1:
                    pen.line(run, w=w * R(0.9, 1.1), hand=0.1, lift=0)


def paired(post, ant, n=120):
    """Two edges of a lobe resampled to matching points (left = front edge, right = hind edge)."""
    a, b = Curve(ant, step=0.6), Curve(post, step=0.6)
    return [a.at(k / n) for k in range(n + 1)], [b.at(k / n) for k in range(n + 1)]


SH = body(t_at_x(692), -0.62)


def pectoral(shift=(0, 0), scale=1.0, weight=1.0, front=True):
    """The pectoral fin, a fleshy lobe: back from the shoulder to the elbow, then forward and down
    to the wrist, its outer part flexed flat on the mud. Rays fringe its hind edge and splay
    forward from its end over the mud."""
    ox, oy = SH[0] + shift[0], SH[1] + shift[1]
    scale *= 1.2
    sy_ = (ground_y(ox + 40 * scale) + shift[1] - oy - 1.0) / 72.0

    def P(dx, dy):
        return (ox + dx * scale, oy + dy * sy_)

    POST = catmull([P(-24, -4), P(-33, 12), P(-37, 30), P(-31, 46), P(-15, 58.5), P(4, 67), P(28, 71.5), P(48, 72.5),
                    P(62, 70.5)], step=1.0)
    ANT = catmull([P(22, -2), P(15, 14), P(9, 28), P(11, 40), P(21, 49.5), P(36, 56.5), P(51, 62), P(62, 70.5)], step=1.0)
    left, right = paired(POST, ANT)
    N = len(left) - 1
    ground = lambda x: ground_y(x) + shift[1]

    # the fringe on the hind edge, elbow to wrist: rays leaning toward the wrist, longer toward it
    pc = Curve(POST, step=0.5)
    bases, tips = [], []
    u0, u1 = 0.3, 0.66
    nr = int((u1 - u0) * pc.L / 3.4)
    for k in range(nr):
        u = u0 + (u1 - u0) * (k + 0.5) / nr
        a = pc.at(u)
        nx, ny = pc.normal(u)          # left of travel along the hind edge: outward, away from the lobe
        tx, ty = pc.tangent(u)
        Lr = (8 + 12 * (k / nr)) * R(0.9, 1.1) * scale
        d = (nx * 0.62 + tx * 0.78, ny * 0.62 + ty * 0.78)
        b = (a[0] + d[0] * Lr, a[1] + d[1] * Lr)
        b = (b[0], min(b[1], ground(b[0]) - 0.5))
        bases.append(a)
        tips.append(b)
    # the fan over the mud, from the flexed outer part: seen low, so flattened
    ac = Curve(ANT, step=0.5)
    fan_b, fan_t = [], []
    C = P(38, 66)
    a0 = 0.5
    nf = int((1 - a0) * ac.L / 2.5)
    for k in range(nf):
        u = (k + 0.5) / nf
        a = ac.at(a0 + (1 - a0) * u)
        phi = math.radians(-58 + 100 * u)
        Lx, Ly = (60 - 8 * u) * scale * R(0.96, 1.04), 24 * scale * R(0.96, 1.04)
        b = (C[0] + math.cos(phi) * Lx, C[1] + math.sin(phi) * Ly)
        # some rays start a little out from the lobe, so their roots do not run solid
        fan_b.append(lerp(a, b, 0.22 + 0.1 * R()) if k % 3 == 1 else a)
        fan_t.append(b)
    # and a few short rays round the end, on the near side
    for k in range(5):
        a = pc.at(0.86 + 0.13 * k / 5)
        b = (a[0] + 4 + 3 * k, a[1] + 7 - k * 0.6)
        fan_b.append(a)
        fan_t.append(b)
    fan_t_margin = fan_t[:nf]

    def draw_rays():
        rays(fan_b[:nf], fan_t_margin, w=0.7 * weight, margin_w=1.05 * weight)
        rays(fan_b[nf:], fan_t[nf:], w=0.8 * weight, margin_w=0.8 * weight)
        rays(bases, tips, w=0.8 * weight, margin_w=1.05 * weight)

    if not front:
        # the far fin: only its fan shows, spread on the mud beyond the near one
        rays(fan_b[:nf], fan_t_margin, w=0.8 * weight, margin_w=1.05 * weight)
        return []
    draw_rays()
    # the lobe
    stroke(ANT, w=2.0 * weight, hand=0.5, lift=0.03)
    stroke(POST, w=2.5 * weight, hand=0.5, lift=0.03)
    # its root on the chest
    stroke(catmull([P(-24, -4), P(-10, -16), P(8, -17), P(22, -2)], step=1.0), w=1.4 * weight, hand=0.4, lift=0.12)
    # the hind half and the underside in shadow; the lit front with small scales
    limb_shade(left, right, 0.45, 0.97, w=0.95 * weight, t0=0.02, t1=0.97)
    limb_shade(left, right, 0.72, 0.97, w=0.95 * weight, t0=0.04, t1=0.92, spacing=4.8)
    limb_scales(left, right, 0.24, 0.42, size=12.0, w=0.75 * weight, t0=0.06, t1=0.78)
    # the lobe is flattened: the edge of its upper face runs along the front, and curved strokes wrap
    # across the pale front from that edge, so it reads as a fleshy paddle rather than an arm
    stroke([lerp(left[i], right[i], 0.27) for i in range(int(N * 0.1), int(N * 0.62))], w=0.8 * weight, hand=0.3,
           lift=0.3, piece=(8, 22))
    for t in (0.1, 0.19, 0.31, 0.45, 0.6, 0.74):
        t += G(0.012)
        i = min(N, int(t * N))
        i2 = min(N, i + int(N * 0.03))
        f = R(0.2, 0.3)
        a, m, b = left[i], lerp(left[i2], right[i2], f * 0.5), lerp(left[i], right[i], f)
        stroke(catmull([lerp(a, b, 0.1), m, b], step=1.0), w=0.78 * weight * R(0.9, 1.1), hand=0.1, lift=0)
    # the elbow's crease, on the inside of the bend
    stroke(catmull([P(8, 29), P(0, 33), P(-9, 40)], step=1.0), w=1.0 * weight, hand=0.2, lift=0)
    lobe = POST + ANT[::-1]
    return [lobe, POST[int(len(POST) * u0):int(len(POST) * u1)] + tips[::-1], ANT[int(len(ANT) * a0):] + fan_t_margin[::-1]]


# ---------------------------------------------------------------- 1. near pectoral fin (in front of everything)

for poly in pectoral():
    pen.occlude(poly)


# ---------------------------------------------------------------- 2. near pelvic fin, robust, swept back at the waterline

def pelvic():
    P0 = body(t_at_x(474), -0.6)

    def P(dx, dy):
        return (P0[0] + dx * 1.3, P0[1] + dy * 1.25)

    # a stout lobe swept back along the flank, its end down at the water
    ANT = catmull([P(14, -2), P(9, 14), P(-2, 27), P(-20, 36), P(-38, 41), P(-50, 42)], step=1.0)  # lower, leading edge
    POST = catmull([P(-16, -8), P(-25, 2), P(-36, 12), P(-46, 21), P(-53, 28)], step=1.0)          # upper, trailing edge
    CAP = catmull([P(-53, 28), P(-59, 35), P(-50, 42)], step=0.8)                                   # its rounded end
    left, right = paired(POST, ANT)
    # rays fringe the trailing edge and splay back from the end
    pc = Curve(POST, step=0.5)
    bases, tips = [], []
    nr = int(pc.L * 0.75 / 3.2)
    for k in range(nr):
        u = 0.25 + 0.75 * (k + 0.5) / nr
        a = pc.at(u)
        nx, ny = pc.normal(u)
        tx, ty = pc.tangent(u)
        Lr = (10 + 22 * u) * R(0.9, 1.08)
        d = (-nx * 0.55 + tx * 0.83, -ny * 0.55 + ty * 0.83)
        bases.append(a)
        tips.append((a[0] + d[0] * Lr, a[1] + d[1] * Lr))
    cc = Curve(CAP, step=0.5)
    for k in range(12):
        u = (k + 0.5) / 12
        a = cc.at(u)
        ang = math.radians(150 + 55 * u)
        L = 26 * R(0.92, 1.06)
        bases.append(a)
        tips.append((a[0] + math.cos(ang) * L, a[1] - math.sin(ang) * L * 0.8))
    rays(bases, tips, w=0.8, faint=True)
    ink(ANT, w=2.2, faint=0.7, hand=0.5, lift=0.03)
    ink(POST, w=1.9, faint=0.7, hand=0.5, lift=0.03)
    ink(CAP, w=1.8, faint=0.7, hand=0.3, lift=0)
    limb_shade(left, right, 0.02, 0.5, w=0.9, t0=0.06, t1=0.95, keep=dry)
    limb_scales(left, right, 0.55, 0.92, size=8.5, w=0.72, t0=0.1, t1=0.8, keep=dry)
    return [POST + CAP[1:-1] + ANT[::-1], POST + tips[:nr][::-1], CAP + tips[nr:][::-1]]


for poly in pelvic():
    pen.occlude(poly_clip_below(poly, lambda x: water_y(x) + 6))


# ---------------------------------------------------------------- 3. head

stroke(HEAD_TOP, w=2.4, lift=0.08)
stroke(UPPER_LIP, w=1.7, lift=0.06)
stroke(JAW_LOW, w=2.6, lift=0.06)
stroke(NECK_TOP, w=2.4, lift=0.04)
stroke(NECK_BOT, w=2.7, lift=0.04)

# eye, high on the flat skull in a raised socket
EYE = hp(88, 37.5)
pen.ellipse(EYE[0], EYE[1], 13.0, 10.0, rot=-H_ANGLE, w=1.7)
pen.ellipse(EYE[0] + 0.6, EYE[1] + 0.6, 8.2, 6.6, rot=-H_ANGLE, w=1.0)
pen.blot(EYE[0] + 1.6, EYE[1] + 0.8, 4.5, 4.0, w=1.8)
# the near edge of the flat skull roof; the roof lit, with a few sutures between its plates
stroke(hc([(-8, 32.5), (30, 34.5), (64, 35)], step=1.0), w=1.0, hand=0.4)
stroke(hc([(114, 35), (140, 31), (164, 24.5), (184, 16), (197, 7)], step=1.0), w=1.0, hand=0.4)
for (u, v0, v1) in [(22, 34.5, 39.5), (46, 35, 41), (130, 32.5, 37.5), (158, 26, 30.5)]:
    stroke([hp(u, v0), hp(u + 2.5, v1)], w=0.8, hand=0.2, lift=0)
# spiracle slit at the back corner of the roof; nostril
stroke(hc([(6, 29.5), (13, 31), (20, 29.5)], step=0.7), w=1.6, hand=0.1)
EN = hp(191, 1.5)
pen.ellipse(EN[0], EN[1], 3.2, 2.1, rot=-H_ANGLE + 0.3, w=1.0)

stroke(hc([(68, 29), (78, 25), (90, 24), (102, 26), (110, 30.5)], step=1.0), w=1.1, hand=0.3)
# the cheek: bony plates, each hatched in its own direction, darker low on the head; the maxilla a
# dark band along the lip
def plate(pts, angle, spacing, w, skip=0.0, shrink=(0.04, 0.14)):
    poly = [hp(u, v) for u, v in catmull(pts, closed=True, step=2.0)]
    pen.hatch(poly, angle=angle - math.degrees(H_ANGLE), spacing=spacing, w=w, skip=skip, shrink=shrink, hand=0.3)


MAX_TOP = lambda u: lip_v(u) + 8.5
plate([(4, 28.5), (26, 30), (52, 28), (56, 16), (48, MAX_TOP(48) + 1), (24, MAX_TOP(24) + 1), (2, MAX_TOP(2) + 1),
       (-4, 10)], 62, 5.0, 1.05)                                               # squamosal, behind the eye
plate([(60, 16), (72, 21), (90, 22), (106, 20), (118, 14), (116, MAX_TOP(116) + 1), (88, MAX_TOP(88) + 1),
       (58, MAX_TOP(58) + 1)], -55, 5.0, 0.98)                                 # jugal, under the eye
plate([(124, 22), (146, 24), (170, 17), (184, 8), (180, MAX_TOP(180) + 1), (150, MAX_TOP(150) + 1),
       (124, MAX_TOP(124) + 1)], 40, 6.0, 0.78, skip=0.15)                     # lacrimal, before the eye
# sutures between them
for pts in ([(56, 28), (56, 16), (50, MAX_TOP(50))],
            [(118, 24), (120, 14), (120, MAX_TOP(120))]):
    stroke(hc(pts, step=1.0), w=0.85, hand=0.3, lift=0.15)
# the maxilla: short strokes across the strip above the lip, irregular in length and spacing
u = 4.0
while u < 188:
    if R() > 0.12:
        top = lip_v(u) + 1.6 + (MAX_TOP(u) - 0.8 - lip_v(u) - 1.6) * R(0.4, 1.0)
        stroke([hp(u + 0.8, top), hp(u - 0.8, lip_v(u) + 1.6)], w=0.9 * R(0.85, 1.12), hand=0.1, lift=0)
    u += R(3.6, 6.6)
# the lower jaw dark underneath: strokes across it, a long line low along it
# each stroke rises from the jaw's lower edge as it runs forward, slanting along the curve
u = -16.0
while u < 192:
    du = R(16, 24)
    f_end = R(0.55, 0.88)
    if not (u < 0 and R() > 1 + u / 18):
        pts = []
        for q in range(9):
            uq = min(196.0, u + du * q / 8)
            uc = max(uq, 0.0)
            lo, hi = jaw_v(uc), lip_v(uc)
            pts.append(hp(uq, lo + 1.0 + (hi - lo - 1.0) * f_end * q / 8))
        stroke(pts, w=1.1 * R(0.9, 1.1), hand=0.15, lift=0.04, piece=(30, 60))
    u += R(6.0, 7.4)
pen.line([hp(u, jaw_v(u) + 5.0) for u in np.linspace(4, 186, 80)], w=1.05, hand=0.3, lift=0.25, piece=(10, 30))
# the neck: strokes across it, from the back of the skull to the first scales, darker below
NECK_U = Curve(NECK_TOP, step=0.5)
NECK_L = Curve(NECK_BOT, step=0.5)
for k in range(5):
    f = (k + 0.5) / 5
    a = lerp(DORSAL[-1], hp(0, 37), f)
    b = lerp(VENTRAL[-1], hp(6, -44.5), f)
    a = lerp(a, b, 0.3 + 0.25 * R())
    stroke([a, lerp(a, b, 0.5), lerp(a, b, 0.96)], w=0.7 + 0.15 * R(), hand=0.3, lift=0.1, piece=(20, 40))
    if k % 2:
        c = lerp(lerp(DORSAL[-1], hp(0, 37), f), b, 0.08)
        stroke([c, lerp(c, b, 0.18)], w=0.8, hand=0.2, lift=0)
# throat and the underside of the neck in shadow, carried on from the jaw
for k in range(8):
    u = -4 - k * 4.8
    stroke([hp(u, jaw_v(0) - 2 + k * 0.6), hp(u + 2.0, jaw_v(0) + 16 - k * 0.8)], w=0.95, hand=0.2, lift=0)
# bony pitting on the roof and cheek
for (u, v) in [(10, 36), (34, 37), (56, 38), (124, 34), (146, 29), (170, 21), (186, 12),
               (140, 10), (160, 6), (176, 2)]:
    p = hp(u + G(1.2), v + G(1.0))
    pen.dot(p[0], p[1], r=0.7, w=0.75)
# sensory canal pores along the jaw
for p in resample(hc([(180, -14.5), (150, -20.5), (118, -26), (84, -31), (50, -35.5), (20, -38)], step=1.0), 8.0):
    pen.dot(p[0], p[1], r=0.8, w=0.75)
# teeth along the upper jaw, uneven, with three larger fangs near the snout tip
lip = Curve(UPPER_LIP, step=0.5)
FANGS = [(0.045, 9.0), (0.105, 10.5), (0.175, 8.0)]
teeth = list(FANGS)
t = 0.03
while t < 0.92:
    if all(abs(t - ft) > 0.028 for ft, _ in FANGS) and R() > 0.1:
        teeth.append((t, R(2.4, 5.4)))
    t += R(0.035, 0.07)
dx, dy = -H_UP[0], -H_UP[1]
for t, L in teeth:
    x, y = lip.at(t)
    hw = 2.2 if L > 7 else 1.5
    stroke([(x - hw * H_DIR[0], y - hw * H_DIR[1]), (x + dx * L + 0.6 * H_DIR[0], y + dy * L + 0.6 * H_DIR[1]),
            (x + hw * H_DIR[0], y + hw * H_DIR[1])], w=1.05 if L > 7 else 0.95, hand=0, lift=0)


# ---------------------------------------------------------------- 4. trunk and tail

# contours: heavy, the belly heaviest
ink(DORSAL[80:], w=2.4, lift=0.06)
ink(DORSAL[:86], w=1.5, taper=0.4, lift=0.06, faint=0.0)
ink(VENTRAL[70:], w=2.9, lift=0.04)
ink(VENTRAL[:76], w=1.5, taper=0.4, lift=0.06)

# ---- rhombic scales in rows along the body, their hind margins slanting in oblique rows. Rows are
# lines of constant theta; each scale is a parallelogram whose hind margin is a short heavy stroke.
ts = np.linspace(0, 1, 1001)
hs = np.array([sum(depth(t)) / 2 for t in ts])
sig = np.concatenate([[0.0], np.cumsum(np.diff(ts) * SPINE.L / np.maximum(hs[1:], 7.0))])


def t_of_sigma(s):
    return float(np.interp(s, sig, ts))


def flank(s, th):
    return body(t_of_sigma(s), math.sin(th * math.pi / 2) * 0.985)


NROWS = 14
DELTA = 0.32
SLANT = 0.32 * DELTA
SIG_LO = float(np.interp(t_at_x(250), ts, sig))
SIG_HI = float(np.interp(1.0, ts, sig))


def tone(th, s):
    """Light falls from above: the back pale, the lower flank and belly in a dark band."""
    base = 0.62 - 0.56 * th
    if s > SIG_HI - 2.4 and th < 0.4:
        base += 0.15 * min(1.0, (s - SIG_HI + 2.4) / 1.2)
    return min(1.0, max(0.0, base))


def in_scales(s, th):
    return SIG_LO <= s <= SIG_HI + 0.02 and -1.0 <= th <= 1.0


def lat(a, b, n=6):
    pts = []
    for q in range(n + 1):
        s_, th = lerp(a, b, q / n)
        if in_scales(s_, th):
            pts.append(flank(s_, th))
    return pts


def scale_ink(pts, w):
    for run in runs(pts, dry):
        if len(run) > 2 and dist(run[0], run[-1]) > 1.8:
            pen.line(run, w=w * R(0.92, 1.08), hand=0.15, lift=0, piece=(40, 80))


for k in range(NROWS):
    th0 = -1 + 2 * k / NROWS
    th1 = -1 + 2 * (k + 1) / NROWS
    thm = (th0 + th1) / 2
    shift = (k % 2) * DELTA * 0.5
    j0 = int((SIG_LO - shift) / DELTA) - 1
    j1 = int((SIG_HI - shift) / DELTA) + 2
    back = max(0.0, (thm - 0.15) / 0.85)
    for j in range(j0, j1):
        s0 = j * DELTA + shift
        tailf = max(0.0, 1 - (s0 - SIG_LO) / (0.32 * (SIG_HI - SIG_LO)))
        loose = min(1.0, max(back, 0.9 * tailf))
        s0 += G(0.012 + 0.035 * loose)
        tn = tone(thm, s0)
        fade = min(1.0, (s0 - SIG_LO) / (2.0 * DELTA)) * min(1.0, (SIG_HI + 0.25 - s0) / 0.4)
        if R() > fade or R() < 0.3 * loose:
            continue
        if R() < 0.75 * loose:
            # a loose scale: only its hind edge, as a short tick, sometimes with a smaller one before it
            a, b = (s0, th0), (s0 + SLANT, th1)
            f0, f1 = R(0.08, 0.3), R(0.65, 0.92)
            scale_ink(lat(lerp(a, b, f0), lerp(a, b, f1)), (0.9 + 1.7 * tn) * R(0.8, 1.0))
            if R() < 0.4 * loose:
                h0_ = R(0.25, 0.45)
                a2, b2 = (s0 + DELTA * 0.5, th0), (s0 + DELTA * 0.5 + SLANT, th1)
                scale_ink(lat(lerp(a2, b2, h0_), lerp(a2, b2, h0_ + 0.4)), 0.75 + 1.2 * tn)
            continue
        # hind margin: from the row's lower edge up to its upper edge, leaning forward
        a, b = (s0, th0), (s0 + SLANT, th1)
        a_, b_ = lerp(a, b, 0.06), lerp(a, b, 0.94)
        if tn < 0.15 and R() < 0.35:
            continue
        w_m = 0.9 + 1.7 * tn
        scale_ink(lat(a_, b_), w_m)
        # the lower edge of the scale, along the row, lighter
        if tn > 0.2 or R() < 0.5:
            c0, c1 = (s0 + 0.12 * DELTA, th0), (s0 + 0.88 * DELTA, th0)
            scale_ink(lat(c0, c1, 8), 0.65 + 0.95 * tn)
        # shade: strokes behind the margin, parallel to it, about 4.6 apart, more of them lower down
        span = dist(flank(s0, thm), flank(s0 + DELTA, thm))
        n_in = min(int(tn * 4.6), int(span / 4.1) - 1)
        for i in range(1, n_in + 1):
            f = i * 4.1 / span * DELTA
            aa, bb = (s0 + f, th0), (s0 + f + SLANT, th1)
            scale_ink(lat(lerp(aa, bb, 0.12), lerp(aa, bb, 0.9)), 0.66 + 0.75 * tn)

# on the slim tail beyond the scales: lines along it, darker below
for v, w_ in ((-0.72, 0.95), (-0.4, 0.8), (-0.05, 0.7), (0.35, 0.62)):
    pts = [body(t, v) for t in np.linspace(0.03, t_of_sigma(SIG_LO + 1.5 * DELTA), 90)]
    ink(pts, w=w_, faint=0.0, hand=0.4, lift=0.3, piece=(8, 24))

# lateral line along the mid-flank
for p in resample([body(t, 0.24) for t in np.linspace(0.2, 0.99, 300)], 12.0):
    if dry(p):
        pen.dot(p[0], p[1], r=1.0, w=0.9)


# ---- the tail fin: a fringe of rays above and below the tail; body and fin together taper evenly to a
# point behind the tip, so there is no paddle
TAIL_TIP = body(0, 0)
TX, TY = SPINE.tangent(0.004)
TAIL_END = (TAIL_TIP[0] - TX * 54, TAIL_TIP[1] - TY * 54 + 1)


def fringe(sign, t0, hmax, spacing=4.4, lean_k=0.42):
    """The fin along the dorsal (sign 1) or ventral (sign -1) edge of the tail, from t0 to the tip: it
    rises from the body, is tallest early on and tapers toward the tip, its rays leaning back a little."""
    def fin_h(t):
        x = 1 - t / t0                                # 0 where the fin starts, 1 at the tip
        r = min(1.0, x / 0.3)
        return hmax * r * r * (3 - 2 * r) * (1 - 0.7 * x ** 1.3)

    def margin(t):
        p = body(t, sign)
        nx, ny = SPINE.normal(t)
        tx, ty = SPINE.tangent(t)
        h = fin_h(t)
        return (p[0] + nx * h * sign - tx * h * lean_k, p[1] + ny * h * sign - ty * h * lean_k)

    n = 40
    edge = [margin(t0 * (1 - k / n)) for k in range(n + 1)]
    nx, ny = SPINE.normal(0.004)
    tx, ty = SPINE.tangent(0.004)
    d_end = dist(TAIL_TIP, TAIL_END)
    h_end = fin_h(0)
    r1 = (TAIL_TIP[0] - tx * d_end * 0.5 + nx * sign * h_end * 0.75, TAIL_TIP[1] - ty * d_end * 0.5 + ny * sign * h_end * 0.75)
    edge = catmull(edge[::2] + [r1, TAIL_END], step=1.0)
    L_body = sum(dist(body(t0 * k / 80, sign), body(t0 * (k + 1) / 80, sign)) for k in range(80))
    nr = int(L_body / spacing)
    for i in range(nr):
        t = t0 * (1 - (i + 0.5 + G(0.12)) / nr)
        a, b = body(t, sign * 0.97), margin(t)
        if dist(a, b) > 2.5:
            b = lerp(a, b, R(0.86, 1.0))
            m = lerp(a, b, 0.5)
            m = (m[0] - tx * 0.8, m[1] - ty * 0.8)
            ink(catmull([a, m, b], step=1.0), w=0.8 * R(0.88, 1.1), faint=0.0, hand=0.15, lift=0.04,
                piece=(12, 40))
    for k in range(1, 6):
        a = lerp(TAIL_TIP, TAIL_END, 0.13 * k)
        b = Curve(edge[-int(len(edge) * 0.3):], step=1.0).at(0.16 * k)
        ink([a, b], w=0.75, faint=0.0, hand=0.15, lift=0)
    ink(edge, w=1.15, faint=0.7 if sign > 0 else 0.0, hand=0.4, lift=0.25, piece=(8, 24))
    return [body(t, sign * 0.5) for t in np.linspace(t0, 0, 30)] + edge


TAIL_FINS = [fringe(1, t_at_x(372), 18), fringe(-1, t_at_x(330), 16)]


# ---- the waterline across the flank, with a thin lip of water against it
for run in runs(WL, ALL):
    stroke(run, w=1.8, hand=0.4, lift=0.12, piece=(10, 30))
WLC = Curve(WL, step=1.0)
for k in range(34):
    x, y = WLC.at(0.015 + k * 0.029)
    y += R(3.0, 4.5)
    stroke([(x - R(5, 9), y), (x + R(5, 9), y + G(0.4))], w=1.0, hand=0.3, lift=0)


# the animal hides what lies behind it, above the water
pen.occlude(poly_clip_below(SILHOUETTE, water_y))
for poly in TAIL_FINS:
    pen.occlude(poly_clip_below(poly, water_y))


# ---------------------------------------------------------------- 5. far pectoral fin (behind)

pectoral(shift=(22, -6), scale=0.95, weight=0.8, front=False)

N_FISH = len(pen.strokes)


# ---------------------------------------------------------------- 6. the puddle

PUDDLE = catmull([(84, 716), (112, 680), (180, 655), (270, 646), (370, 646), (440, 662), (470, 700), (462, 742),
                  (410, 780), (310, 800), (200, 800), (118, 782), (88, 752)], closed=True, step=2.0)
P_C, P_R = (280.0, 722.0), (205.0, 84.0)


def in_water(p):
    if not inside(p, PUDDLE):
        return False
    return p[0] < 436 or p[1] > ground_y(p[0]) + 1


ANIMAL = [SILHOUETTE] + TAIL_FINS


def off_animal(p):
    return in_water(p) and not any(inside(p, a) for a in ANIMAL)


RIPPLES = []
for x, radii in ((196, [(26, 6), (48, 10)]), (316, [(40, 8), (70, 13), (100, 18)]),
                 (418, [(34, 7), (60, 12)])):
    t = t_at_x(x)
    cx, cy = body(t, v_water(t))
    RIPPLES.append((cx, cy + 3, radii))


def near_ripple(p):
    return any(abs(((p[0] - cx) / rx) ** 2 + ((p[1] - cy - i * 1.5) / ry) ** 2 - 1) < 0.25
               for cx, cy, radii in RIPPLES for i, (rx, ry) in enumerate(radii))


for (cx, cy, radii) in RIPPLES:
    for i, (rx, ry) in enumerate(radii):
        for run in runs(ellipse_pts(cx + G(2), cy + i * 1.5, rx, ry, 0.0, 0, 2 * math.pi, step=2.0), off_animal):
            if len(run) > 2:
                pen.line(run, w=max(0.8, 1.45 - i * 0.25), hand=0.6, lift=0.3 + i * 0.12, piece=(6, 20))

# level strokes of the water: dense near the fish and over the sunken tail, thinning out to the edges
y = 648.0
while y < 802:
    x = 86 + R(0, 18)
    while x < 474:
        L = R(12, 34)
        p0, p1 = (x, y + G(0.5)), (x + L, y + G(0.5))
        mid = lerp(p0, p1, 0.5)
        rr = ((mid[0] - P_C[0]) / P_R[0]) ** 2 + ((mid[1] - P_C[1]) / P_R[1]) ** 2
        over = any(inside(mid, a) for a in ANIMAL)
        if in_water(p0) and in_water(p1) and not near_ripple(mid) and \
                R() < (1.0 if over else 0.95 * (1 - rr) + 0.25):
            stroke([p0, p1], w=1.25 if over else (0.72 if rr > 0.45 else 0.88), hand=0.3, lift=0)
        x += L + (R(2, 6) if over else R(6, 22))
    y += R(5.4, 6.6)
# the far shore, a broken line behind the water
for seg in ([(112, 672), (150, 658), (196, 650)], [(220, 647), (290, 643), (360, 645)]):
    stroke(catmull(seg, step=2.0), w=1.0, hand=0.6, lift=0.35, piece=(8, 22))


# ---------------------------------------------------------------- 7. the muddy bank

stroke(GROUND_C, w=2.1, lift=0.1)
# the bank's face below its lip: hatching that fades downward
x = 452.0
while x < 985:
    y0 = ground_y(x) + 3
    if R() > 0.15:
        L = R(8, 20) * (1.0 if R() < 0.7 else 1.5)
        stroke([(x, y0 + R(0, 2)), (x - L * 0.3, y0 + L)], w=0.8, hand=0.2, lift=0)
        if R() < 0.45:
            y1 = y0 + L + R(6, 18)
            stroke([(x + R(-3, 3), y1), (x - 3 + R(-3, 3), y1 + R(5, 12))], w=0.7, hand=0.2, lift=0)
    x += R(5.5, 8.0)
x = 640.0
while x < 985:
    y0 = ground_y(x) + 2.5
    if R() < 0.8:
        stroke([(x, y0), (x - 2.5, y0 + R(5, 10))], w=0.9, hand=0.1, lift=0)
    x += R(4.8, 6.4)
x = 466.0
while x < 640:
    y0 = ground_y(x) + 2.5
    L = R(10, 22) * (1.25 if x < 600 else 0.8)
    stroke([(x, y0), (x - L * 0.35, y0 + L)], w=1.0, hand=0.2, lift=0)
    x += R(4.6, 5.6)
# the mud under the chest and fins, darker in their shadow
for k in range(30):
    x = 580 + k * 5.6 + G(1)
    y = ground_y(x) - 1.5
    stroke([(x, y), (x + R(8, 14), y - 1.0)], w=0.9, hand=0.2, lift=0)
for (x, r) in [(560, 2.2), (612, 1.6), (870, 2.0), (912, 1.5), (956, 2.2), (520, 1.4)]:
    pen.ellipse(x, ground_y(x) + 7 + r, r * 1.4, r, w=0.9)


# ---------------------------------------------------------------- 8. a hint of early land plants

def sprig(x, y, h, lean, w=1.0, levels=3):
    """A tiny leafless, forking stem (rhyniophyte-like) with sporangia at its tips."""
    def branch(p, ang, L, d):
        q = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)
        mid = lerp(p, q, 0.5)
        stroke(catmull([p, (mid[0] + G(1.0), mid[1]), q], step=1.0), w=w * (0.75 + 0.1 * d), hand=0.2, lift=0)
        if d <= 1:
            pen.ellipse(q[0] + math.cos(ang) * 2, q[1] + math.sin(ang) * 2, 1.8, 2.8, rot=ang + math.pi / 2, w=0.8)
            return
        for da in (-0.38, 0.34):
            branch(q, ang + da + G(0.08), L * R(0.62, 0.78), d - 1)
    branch((x, y), -math.pi / 2 + lean, h * 0.45, levels)


for (x, y, h, lean) in [(150, 657, 36, -0.1), (163, 654, 26, 0.15), (139, 661, 20, -0.2)]:
    sprig(x, y, h, lean)
for (x, dy, h, lean) in [(940, 0, 42, 0.12), (954, 1, 30, -0.12)]:
    sprig(x, ground_y(x) + dy, h, lean)


# ---------------------------------------------------------------- place it in the square

# weight: the animal carries the darkest ink; the water and the bank stay a step lighter
pen.strokes = [(p, min(3.0, 0.22 + w * 1.33) if i < N_FISH else min(2.6, 0.08 + w * 1.08))
               for i, (p, w) in enumerate(pen.strokes)]

fx = [x for p, _ in pen.strokes[:N_FISH] for x, _ in p]
SC = 830 / (max(fx) - min(fx))
cx = (min(fx) + max(fx)) / 2 - 8
ys = [y for p, _ in pen.strokes for _, y in p]
cy = (min(ys) + max(ys)) / 2
pen.strokes = [([(500 + (x - cx) * SC, 505 + (y - cy) * SC) for x, y in p], w) for p, w in pen.strokes]
inside_sq = lambda p: all(15 < x < 985 for x, _ in p)
pen.strokes = [(p, w) for p, w in pen.strokes if inside_sq(p)] + \
    [([(x, y) for x, y in p if 15 < x < 985], w) for p, w in pen.strokes
     if not inside_sq(p) and sum(1 for x, _ in p if 15 < x < 985) > 1]
pen.strokes = [(p, max(0.6, w)) for p, w in pen.strokes]  # the set's finest line is 0.6

if DEBUG:
    print('scale', SC)
pen.save('../12-quastenflosser.svg', mirror=True)
pen.report()
