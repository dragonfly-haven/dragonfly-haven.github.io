"""12 Quastenflosser: a lobe-finned tetrapodomorph (after Tiktaalik, Late Devonian)
heaving its front half out of a shallow puddle onto a muddy bank.

Flattened, crocodile-like head with the eyes on top, a short neck where the gill
cover was lost, heavy rhombic scales, and fleshy lobed pectoral fins (a scaled,
muscular stalk ending in a fan of fin rays) propping the chest off the mud. The
rear half and the fringed tail still lie in the water, ripples spreading around.
Drawn facing right; saved mirrored to face the text.
"""

import math

import numpy as np

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, clip_segments

pen = Pen(seed=1207)
R, G = pen.r, pen.g


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

    def part(self, t0, t1, n=None):
        n = n or max(4, int(abs(t1 - t0) * self.L / 1.5))
        return [self.at(t0 + (t1 - t0) * k / n) for k in range(n + 1)]


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


# ---------------------------------------------------------------- body plan

SPINE = Curve(catmull([(212, 700), (268, 690), (328, 668), (388, 637), (455, 599), (522, 561),
                       (585, 526), (640, 494), (688, 469), (730, 451)], step=2.0), step=1.0)

# half-depths (back, belly) along the spine, by x
HX = [212, 224, 250, 290, 335, 388, 455, 522, 585, 640, 688, 712, 730]
HD = [2, 8, 15, 22, 29, 37, 44, 49, 53, 56, 52, 46, 41]
HV = [2, 9, 17, 25, 34, 44, 55, 62, 65, 63, 56, 51, 47]


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


T_PELVIC = t_at_x(440)
T_SHORE = t_at_x(410)

DORSAL = [body(k / 500, 1.0) for k in range(501)]
VENTRAL = [body(k / 500, -1.0) for k in range(501)]


# ---------------------------------------------------------------- water and ground

# the waterline on the body: the tail half under, the belly leaving the water at the shore
def v_water(t):
    hv = depth(t)[1]
    return -1.0


WL = [body(t, v_water(t)) for t in np.linspace(0, T_SHORE, 300)]
WL_X = [p[0] for p in WL]
WL_Y = [p[1] for p in WL]


def water_y(x):
    return float(np.interp(x, WL_X, WL_Y)) + 0.8 * math.sin(x / 11.0)


def dry(p):
    return True  # the puddle is shallow: the fish lies on it, nothing of it hidden under water


def wet(p):
    return not dry(p)


GROUND = [(414, 704), (450, 680), (500, 655), (550, 628), (600, 602), (640, 592), (700, 588), (780, 585),
          (870, 578), (985, 564)]


def ground_y(x):
    return float(np.interp(x, [p[0] for p in GROUND], [p[1] for p in GROUND]))


# ---- the head, drawn in its own frame: u forward from the back of the skull, v up
H_ORIGIN = (745.0, 446.0)
H_ANGLE = math.radians(11.0)
H_V = 1.28  # head depth stretch
H_U = 1.08  # head length stretch
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
JAW = [(201, -9), (186, -16), (158, -23.5), (122, -30), (86, -36), (52, -41), (24, -44), (6, -44)]

HEAD_TOP = hc(SKULL_TOP)
UPPER_LIP = hc(LIP)
JAW_LOW = hc(JAW)

# the neck: from the shoulders to the back of the skull, a little waisted
NT0, NB0 = DORSAL[-1], VENTRAL[-1]
NECK_TOP = catmull([NT0, (NT0[0] * 0.5 + hp(0, 37)[0] * 0.5, NT0[1] * 0.5 + hp(0, 37)[1] * 0.5 + 2.0), hp(0, 37)], step=1.5)
NECK_BOT = catmull([NB0, lerp(NB0, hp(6, -44), 0.5), hp(6, -44)], step=1.5)

SILHOUETTE = DORSAL + NECK_TOP[1:] + HEAD_TOP[1:] + JAW_LOW[::-1] + NECK_BOT[::-1][1:] + VENTRAL[::-1]


# ---------------------------------------------------------------- lobed fins

def band(center, widths, n=90):
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


def lobed_fin(center, widths, root_from, fan_edge, rays=16, weight=1.0, keep=ALL,
              w_out=1.9, scale=10.0, base_arc=None, side='right'):
    """A sarcopterygian fin: a scaled fleshy lobe along `center` (base first) whose
    distal part carries a fan of fin rays out to `fan_edge`. The fan grows from the
    lobe's `side` edge (from `root_from` along it) round its tip; `fan_edge` runs
    the same way. Returns the lobe and fan outlines as polygons."""
    c, left, right = band(center, widths)
    k0 = int(root_from * (len(right) - 1))
    end, pre = c.at(1.0), c.at(0.96)
    nose = (end[0] + (end[0] - pre[0]) * 1.6, end[1] + (end[1] - pre[1]) * 1.6)
    if side == 'right':
        tip_round = catmull([right[-1], nose, left[-1]], step=0.6)
        root_pts = right[k0:] + tip_round[1:]
    else:
        tip_round = catmull([left[-1], nose, right[-1]], step=0.6)
        root_pts = left[k0:] + tip_round[1:]
    root = Curve(root_pts, step=0.5)
    edge = Curve(fan_edge, step=0.5)
    # rays: fine, bowed a little, starting just off the lobe
    for i in range(rays):
        u = (i + 0.5) / rays
        a, b = root.at(u), edge.at(u)
        a = lerp(a, b, 0.05)
        m = lerp(a, b, 0.5)
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        bow = 1.2 + G(0.5)
        m = (m[0] + ty / L * bow, m[1] - tx / L * bow)
        for run in runs(catmull([a, m, b], step=1.2), keep):
            pen.line(run, w=0.75 * weight * R(0.9, 1.1), hand=0.25, lift=0.03, piece=(14, 40))
    # the fan's margin, finely frayed
    for run in runs(edge.part(0, 1), keep):
        pen.line(run, w=1.25 * weight, hand=0.5, lift=0.2, piece=(6, 16))
    # the lobe: front edge, hind edge, rounded end
    for s_, wt in ((left, w_out), (right, w_out * 0.9)):
        for run in runs(s_, keep):
            pen.line(run, w=wt * weight, hand=0.5, lift=0.05)
    for run in runs(tip_round, keep):
        pen.line(run, w=w_out * 0.8 * weight, hand=0.3, lift=0)
    if base_arc:
        for run in runs(catmull([left[0], base_arc, right[0]], step=1.0), keep):
            pen.line(run, w=1.1 * weight, hand=0.4, lift=0.15, piece=(8, 20))
    # small scales on the lobe: a light lattice of short strokes
    L = c.L
    for fam in (1, -1):
        for j in range(-8, int(L / scale) + 8):
            pts = []
            for q in range(25):
                v = -0.9 + 1.8 * q / 24
                t = (j * scale + fam * v * scale * 0.85) / L
                if 0.05 < t < 0.9:
                    x, y = c.at(t)
                    nx, ny = c.normal(t)
                    w = float(np.interp(t, np.linspace(0, 1, len(widths)), widths)) / 2
                    vv = math.sin(v * math.pi / 2)
                    pts.append((x + nx * w * vv, y + ny * w * vv))
                elif pts:
                    break
            if len(pts) > 2:
                for run in runs(pts, keep):
                    pen.line(run, w=0.72 * weight, hand=0.25, lift=0.35, piece=(5, 11))
    lobe_poly = left + tip_round[::-1][1:-1] + list(reversed(right))
    fan_poly = root_pts + list(reversed(fan_edge))
    return lobe_poly, fan_poly


# ---------------------------------------------------------------- 1. near pectoral fin (in front)

def prop_fin(S, E, W, widths, back, front, drop, rays=24, weight=1.0, keep=ALL, w_out=1.9, base_arc=None):
    """A lobed fin used as a prop: a scaled fleshy stalk from the shoulder S through
    E to W on the mud, ending in a fan of fin rays spread flat around W (from `back`
    units behind it to `front` units ahead, bulging `drop` units toward us)."""
    k1 = lerp(S, E, 0.55)
    k2 = lerp(E, W, 0.45)
    center = catmull([S, k1, lerp(lerp(k1, E, 0.6), lerp(E, k2, 0.4), 0.5), k2, W], step=1.0)
    c, left, right = band(center, widths)
    end, pre = c.at(1.0), c.at(0.95)
    nose = (end[0] + (end[0] - pre[0]) * 1.2, end[1] + (end[1] - pre[1]) * 1.2)
    tip_round = catmull([right[-1], nose, left[-1]], step=0.6)
    # fan root: hind edge of the stalk's last third, round the tip, up the front edge a little
    k0 = int(0.62 * (len(right) - 1))
    k1 = int(0.88 * (len(left) - 1))
    root_pts = right[k0:] + tip_round[1:-1] + list(reversed(left[k1:]))
    root = Curve(root_pts, step=0.5)
    gy = W[1] + 3
    margin = catmull([(W[0] - back, gy - 6), (W[0] - back * 0.7, gy + drop * 0.55), (W[0] - back * 0.2, gy + drop),
                      (W[0] + front * 0.35, gy + drop * 0.95), (W[0] + front * 0.8, gy + drop * 0.45), (W[0] + front, gy - 5)], step=1.0)
    edge = Curve(margin, step=0.5)
    for i in range(rays):
        u = (i + 0.5) / rays
        a, b = root.at(u), edge.at(u)
        a = lerp(a, b, 0.04)
        m = lerp(a, b, 0.5)
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        bow = 1.0 + G(0.5)
        m = (m[0] + ty / L * bow, m[1] - tx / L * bow)
        for run in runs(catmull([a, m, b], step=1.2), keep):
            pen.line(run, w=0.75 * weight * R(0.9, 1.1), hand=0.25, lift=0.03, piece=(14, 40))
    for run in runs(margin, keep):
        pen.line(run, w=1.25 * weight, hand=0.5, lift=0.2, piece=(6, 16))
    for s_, wt in ((left, w_out), (right, w_out * 0.92)):
        for run in runs(s_, keep):
            pen.line(run, w=wt * weight, hand=0.5, lift=0.05)
    for run in runs(tip_round, keep):
        pen.line(run, w=w_out * 0.7 * weight, hand=0.3, lift=0)
    if base_arc:
        for run in runs(catmull([left[0], base_arc, right[0]], step=1.0), keep):
            pen.line(run, w=0.95 * weight, hand=0.4, lift=0.25, piece=(8, 20))
    # small scales on the stalk
    L = c.L
    sc = 13.0
    for fam in (1, -1):
        for j in range(-8, int(L / sc) + 8):
            pts = []
            for q in range(25):
                v = -0.9 + 1.8 * q / 24
                t = (j * sc + fam * v * sc * 0.85) / L
                if 0.04 < t < 0.8:
                    x, y = c.at(t)
                    nx, ny = c.normal(t)
                    w = float(np.interp(t, np.linspace(0, 1, len(widths)), widths)) / 2
                    vv = math.sin(v * math.pi / 2)
                    pts.append((x + nx * w * vv, y + ny * w * vv))
                elif pts:
                    break
            if len(pts) > 2:
                for run in runs(pts, keep):
                    pen.line(run, w=0.66 * weight, hand=0.25, lift=0.45, piece=(5, 11))
    lobe_poly = left + tip_round[::-1][1:-1] + list(reversed(right))
    fan_poly = root_pts + list(reversed(margin))
    return lobe_poly, fan_poly


P_S, P_E, P_W = (701, 498), (690, 543), (712, 581)
P_WIDTHS = [52, 44, 34, 25]
for poly in prop_fin(P_S, P_E, P_W, P_WIDTHS, 54, 72, 19, rays=32, base_arc=(703, 468)):
    pen.occlude(poly)


# near pelvic fin on the slope: a smaller lobed fin, pressed back against the mud
PV = body(T_PELVIC, -0.55)
PV_C = catmull([PV, (PV[0] - 20, PV[1] + 13), (PV[0] - 38, PV[1] + 20)], step=1.0)
PV_FAN = catmull([(PV[0] - 12, PV[1] + 26), (PV[0] - 30, PV[1] + 35), (PV[0] - 52, PV[1] + 36), (PV[0] - 68, PV[1] + 28),
                  (PV[0] - 70, PV[1] + 17)], step=1.0)
for poly in lobed_fin(PV_C, [30, 24, 16], 0.3, PV_FAN, rays=16, weight=0.85, w_out=1.7, scale=9.0, side='left'):
    pen.occlude(poly)


# ---------------------------------------------------------------- 2. head

stroke(HEAD_TOP, w=2.4, lift=0.1)
stroke(UPPER_LIP, w=1.7, lift=0.08)
stroke(JAW_LOW, w=2.3, lift=0.08)
stroke(NECK_TOP, w=2.3, lift=0.05)
stroke(NECK_BOT, w=2.2, lift=0.05)

# near eye, high on the flat skull; the orbit rim rises above the roof line
EYE = hp(88, 37.5)
pen.ellipse(EYE[0], EYE[1], 13.0, 10.0, rot=-H_ANGLE, w=1.6)
pen.ellipse(EYE[0] + 0.6, EYE[1] + 0.6, 8.2, 6.6, rot=-H_ANGLE, w=1.0)
pen.blot(EYE[0] + 1.6, EYE[1] + 0.8, 4.5, 4.0, w=1.8)
# lid crease under the eye, and the near edge of the flat skull roof
stroke(hc([(70, 31.5), (78, 27.5), (90, 26.5), (102, 29), (108, 33.5)], step=1.0), w=0.9, hand=0.3)
stroke(hc([(8, 33), (30, 34.5), (60, 35.5)], step=1.0), w=0.95, hand=0.4)
stroke(hc([(116, 35), (140, 31), (164, 24.5), (184, 16), (197, 7)], step=1.0), w=0.95, hand=0.4)
# spiracle: a slit at the back corner of the skull roof
stroke(hc([(5, 29.5), (13, 31), (21, 29.5)], step=0.7), w=1.7, hand=0.1)
# nostril
EN = hp(191, 1.5)
pen.ellipse(EN[0], EN[1], 3.2, 2.1, rot=-H_ANGLE + 0.3, w=1.0)

# back edge of the skull roof and cheek (no gill cover behind it: the neck)
stroke(hc([(0, 37), (-2, 22), (-3, 6), (-2, -6)], step=1.0), w=1.5, lift=0.08, taper=0.4)
stroke(hc([(2, -24), (4, -33), (8, -41)], step=1.0), w=1.3, lift=0)
# cheek: one plate margin curving down behind the eye
stroke(hc([(64, 24), (56, 8), (46, -4), (34, -12)], step=1.0), w=0.8, hand=0.5, lift=0.3)
# infraorbital sensory canal: a row of pores under the eye
for p in resample(hc([(186, 4), (160, 8), (134, 13), (110, 17), (86, 18), (62, 16), (40, 12), (20, 4)], step=1.0), 7.5):
    pen.dot(p[0], p[1], r=0.85, w=0.8)
# mandibular canal along the lower jaw
for p in resample(hc([(180, -13.5), (150, -19.5), (118, -25), (84, -30), (50, -34.5)], step=1.0), 8.0):
    pen.dot(p[0], p[1], r=0.8, w=0.75)
# teeth: small cones along the upper jaw, with two fangs
lip = Curve(UPPER_LIP, step=0.5)
for k in range(17):
    t = 0.035 + k * 0.055
    if t > 0.93:
        break
    x, y = lip.at(t)
    L = 7.0 if k in (1, 5) else R(3.5, 4.8)
    dx, dy = -H_UP[0], -H_UP[1]
    stroke([(x - 1.6 * H_DIR[0], y - 1.6 * H_DIR[1]), (x + dx * L + 0.5 * H_DIR[0], y + dy * L + 0.5 * H_DIR[1]),
            (x + 1.6 * H_DIR[0], y + 1.6 * H_DIR[1])], w=0.9, hand=0, lift=0)
# the lower jaw rounded in shade: contour lines along it
for f, (u0, u1), wt in ((0.2, (14, 186), 0.8), (0.4, (24, 168), 0.72)):
    pts = []
    for u in np.linspace(u0, u1, 50):
        bot = float(np.interp(u, [2, 10, 24, 52, 86, 122, 158, 186, 201], [-42, -44.5, -44, -41, -36, -30, -23.5, -16, -9]))
        top = float(np.interp(u, [36, 58, 90, 125, 160, 190], [-18.5, -18, -16.5, -14.5, -12, -9]))
        if u < 36:
            top = -18.5 + (36 - u) * 0.1
        pts.append(hp(u, bot + (top - bot) * f))
    pen.line(pts, w=wt, hand=0.4, lift=0.25, piece=(10, 30))
# shade low on the cheek: short strokes rising from the lip, following the head
for k in range(15):
    u = 16 + k * 7.5 + G(1.0)
    if R() < 0.2:
        continue
    lo = float(np.interp(u, [36, 58, 90, 125], [-18.5, -18, -16.5, -14.5])) if u >= 36 else -18.5
    hi = lo + R(6, 11) * (1.0 - 0.4 * k / 15)
    stroke([hp(u + 2.5, lo + 2.5), hp(u - 2.0, hi)], w=0.62, hand=0.15, lift=0)

# bony pitting
for (u, v) in [(10, 8), (20, -12), (24, 12), (48, -8), (60, 4), (70, -10), (98, 6), (112, -6), (140, 2), (152, -6),
               (166, 4), (176, 10), (130, 22), (150, 20), (60, 26)]:
    p = hp(u + G(1.2), v + G(1.2))
    pen.dot(p[0], p[1], r=0.7, w=0.7)

# the neck: small folds where it bends, at top and bottom
for a, m, b in ((hp(-10, 33), hp(-13, 25), hp(-12, 17)), (hp(-12, -37), hp(-15, -30), hp(-14, -23))):
    stroke(catmull([a, m, b], step=1.0), w=0.8, hand=0.3, lift=0)


# ---------------------------------------------------------------- 3. trunk and tail

stroke(DORSAL[60:], w=2.4, lift=0.08)
stroke(DORSAL[:64], w=1.8, taper=0.5, lift=0.08)
for run in runs(VENTRAL, dry):
    stroke(run, w=2.3, lift=0.08)


# ---- rhombic scales: a lattice in (sigma, theta), sized with the body
ts = np.linspace(0, 1, 801)
hs = np.array([sum(depth(t)) / 2 for t in ts])
sig = np.concatenate([[0.0], np.cumsum(np.diff(ts) * SPINE.L / np.maximum(hs[1:], 5.0))])


def t_of_sigma(s):
    return float(np.interp(s, sig, ts))


def flank(s, th):
    return body(t_of_sigma(s), math.sin(th * math.pi / 2) * 0.985)


M = 5.0          # slant of the scale rows (edges at about 50 degrees to the body axis)
DELTA = 0.46     # scale length, in body half-depths
SIG_LO = float(np.interp(t_at_x(285), ts, sig))
SIG_HI = float(np.interp(0.985, ts, sig))
HB = DELTA / M * 2  # half a scale's height, in theta


def in_scales(s, th):
    return SIG_LO <= s <= SIG_HI and -1.0 <= th <= 1.0


KR = range(int(SIG_LO / DELTA) - 40, int(SIG_HI / DELTA) + 40)

# scale rows ("/": down and back from the back), drawn through, fading out high on the back
for k in KR:
    pts = []
    for q in range(61):
        th = -1 + 2 * q / 60
        s_ = k * DELTA + th * DELTA / HB
        if in_scales(s_, th):
            pts.append((s_, th))
    if len(pts) < 3:
        continue
    th_top = 0.6 + G(0.14)
    s_cut = SIG_LO + R(0.0, 3.0) * DELTA
    seg = [flank(s_, th) for s_, th in pts if th < th_top and s_ > s_cut]
    if len(seg) < 3:
        continue
    for run in runs(seg, dry):
        if len(run) > 3:
            pen.line(run, w=R(0.82, 0.95), hand=0.3, lift=0.12, piece=(12, 26), taper=0.2)

# the other edges ("\"), one scale at a time, lower down the flank only
for ka in KR:
    for kb in KR:
        s0 = (ka + kb) * DELTA / 2
        th0 = (kb - ka) * HB / 2
        if not (-1.3 < th0 < 0.6) or not (SIG_LO - DELTA < s0 < SIG_HI + DELTA):
            continue
        ds, dth = DELTA / 2, -HB / 2
        pts = []
        for q in range(9):
            f = 0.1 + 0.8 * q / 8
            s_, th = s0 + ds * f, th0 + dth * f
            if in_scales(s_, th):
                pts.append(flank(s_, th))
        if len(pts) < 3:
            continue
        thm = th0 + dth / 2
        if thm > 0.1 and R() < (thm - 0.1) * 2.6:
            continue
        if R() < 1.0 - (s0 - SIG_LO) / (3.5 * DELTA):
            continue
        for run in runs(pts, dry):
            if len(run) > 2 and dist(run[0], run[-1]) > 3:
                pen.line(run, w=0.78 * R(0.92, 1.08), hand=0.3, lift=0, piece=(30, 60))

# shade: in each scale low on the flank, a short stroke inside its lower edge
for ka in KR:
    for kb in KR:
        sc = (ka + kb) * DELTA / 2 + DELTA / 2
        thc = (kb - ka) * HB / 2
        if not (-0.98 < thc < -0.15) or not (SIG_LO + DELTA * 2.5 < sc < SIG_HI - DELTA * 0.5):
            continue
        bottom, front, cen = (sc, thc - HB / 2), (sc + DELTA / 2, thc), (sc, thc)
        for f, lim in ((0.3, -0.15), (0.58, -0.6)):
            if thc > lim:
                continue
            a_, b_ = lerp(bottom, cen, f), lerp(front, cen, f)
            a_, b_ = lerp(a_, b_, 0.12), lerp(a_, b_, 0.88)
            pa, pb = flank(*a_), flank(*b_)
            if dry(pa) and dry(pb) and dist(pa, pb) > 4:
                stroke([pa, pb], w=0.72, hand=0.15, lift=0)

# the body's roundness: broken contour lines along the belly, closer toward it, and one along the back
for v, w_, t0, t1 in ((-0.9, 0.75, 0.3, 0.97), (-0.78, 0.72, 0.34, 0.95), (-0.64, 0.7, 0.38, 0.92), (-0.5, 0.66, 0.45, 0.88),
                      (0.9, 0.7, 0.35, 0.9)):
    pts = [body(t, v) for t in np.linspace(t0 + R(0, 0.03), t1 - R(0, 0.03), 300)]
    pen.line(pts, w=w_, hand=0.4, lift=0.5, piece=(8, 28))

# lateral line pores
for p in resample([body(t, 0.22) for t in np.linspace(0.16, 0.97, 300)], 11.0):
    if dry(p):
        pen.dot(p[0], p[1], r=0.9, w=0.8)


# ---- tail fin: a lancet of rays above and below the tapering tail, the lower lobe dipping in the water
def caudal(sign, prof, n_rays, w_ray=0.75, w_edge=1.45):
    """One lobe of the tail fin: `prof` lists (t, height) from where the fin starts to the tail tip."""
    tip = body(0, 0)
    tx, ty = SPINE.tangent(0.02)
    E = (tip[0] - tx * 44, tip[1] - ty * 44 - sign * 1)
    ts_ = [p[0] for p in prof][::-1]
    hs_ = [p[1] for p in prof][::-1]

    def margin_at(t):
        h = float(np.interp(t, ts_, hs_))
        p = body(t, sign)
        nx, ny = SPINE.normal(t)
        tx_, ty_ = SPINE.tangent(t)
        return (p[0] + nx * h * sign - tx_ * h * 0.55, p[1] + ny * h * sign - ty_ * h * 0.55)

    t0 = prof[0][0]
    edge = [margin_at(t0 * k / 60) for k in range(60, -1, -1)]
    last = edge[-1]
    nx, ny = SPINE.normal(0.0)
    bulge = lerp(last, E, 0.55)
    bulge = (bulge[0] + nx * sign * 9 - tx * 4, bulge[1] + ny * sign * 9 - ty * 4)
    edge = catmull(edge[:-6:5] + [edge[-1], bulge, E], step=1.0)
    for i in range(n_rays):
        t = t0 * (1 - (i + 0.6) / n_rays)
        a = body(t, sign * 0.95)
        b = margin_at(t)
        if dist(a, b) < 3:
            continue
        m = lerp(a, b, 0.5)
        for run in runs([a, m, b], dry):
            pen.line(run, w=w_ray * R(0.88, 1.1), hand=0.2, lift=0.04, piece=(12, 40))
    # rays fanning from the very tip
    ec = Curve(edge, step=0.5)
    t_last = ec.L - dist(last, E) * 1.15
    for k in range(1, 7):
        b = ec.at((t_last + (ec.L - t_last) * k / 7) / ec.L)
        a = lerp(tip, E, 0.07 * k)
        for run in runs([a, b], dry):
            pen.line(run, w=w_ray * 0.9, hand=0.2, lift=0)
    for run in runs(edge, dry):
        pen.line(run, w=w_edge, hand=0.4, lift=0.1)
    for run in runs(edge, wet):
        pen.line(run, w=0.65, hand=0.8, lift=0.5, piece=(5, 12))
    spine_part = [body(t, sign * 0.5) for t in np.linspace(0, t0, 40)]
    return spine_part[::-1] + edge


T_C1, T_C2 = t_at_x(372), t_at_x(350)
CAUDAL = [caudal(1, [(T_C1, 0), (T_C1 * 0.75, 13), (T_C1 * 0.5, 27), (T_C1 * 0.28, 36), (T_C1 * 0.1, 34), (0.0, 26)], 30),
          caudal(-1, [(T_C2, 0), (T_C2 * 0.75, 15), (T_C2 * 0.5, 31), (T_C2 * 0.28, 40), (T_C2 * 0.1, 36), (0.0, 27)], 26)]


# everything of the animal above the water hides what lies behind it
pen.occlude(SILHOUETTE)
for poly in CAUDAL:
    pen.occlude(poly)


# ---------------------------------------------------------------- 4. far pectoral fin (behind)

F = (12, -7)
prop_fin((P_S[0] + F[0], P_S[1] + F[1]), (P_E[0] + F[0], P_E[1] + F[1]), (P_W[0] + F[0], P_W[1] + F[1]),
         P_WIDTHS, 50, 66, 14, rays=26, weight=0.78, w_out=1.7)


N_FISH = len(pen.strokes)

# ---------------------------------------------------------------- 5. water


# the puddle: no hard outline, just its level water lines fading out toward the edges
PUDDLE = catmull([(140, 715), (168, 680), (232, 656), (320, 642), (398, 640), (440, 676), (452, 718), (432, 760),
                  (362, 790), (272, 800), (192, 788), (150, 758)], closed=True, step=2.0)
P_CX, P_CY, P_RX, P_RY = 300.0, 722.0, 165.0, 80.0
RIPPLES = []
for t, radii, dy_ in ((0.0, [(62, 12), (96, 18)], 14), (0.2, [(66, 12), (104, 19), (142, 25)], 8), (T_SHORE * 0.95, [(40, 7), (68, 12)], 4)):
    cx, cy = body(t, -1.0)
    RIPPLES.append((cx, cy + dy_, radii))


def ripple(cx, cy, rx, ry, w, gaps):
    for run in runs(ellipse_pts(cx, cy, rx, ry, 0.0, 0, 2 * math.pi, step=2.0), lambda p: inside(p, PUDDLE)):
        pen.line(run, w=w, hand=0.6, lift=gaps, piece=(8, 26))


for (cx, cy, radii) in RIPPLES:
    for i, (rx, ry) in enumerate(radii):
        ripple(cx + G(3), cy + i * 1.5, rx, ry, w=max(0.7, 1.25 - i * 0.2), gaps=0.25 + i * 0.1)


def near_ripple(p):
    return any(abs(((p[0] - cx) / rx) ** 2 + ((p[1] - cy - i * 1.5) / ry) ** 2 - 1) < 0.2
               for cx, cy, radii in RIPPLES for i, (rx, ry) in enumerate(radii))


# little wavelets where the belly lies in the water, and its dark reflection
wl = Curve(WL, step=1.0)
for k in range(30):
    t = 0.40 + k * 0.025
    if t > 0.98:
        break
    x, y = wl.at(t)
    y += R(3, 5)
    stroke([(x - R(5, 9), y), (x + R(4, 9), y + G(0.5))], w=0.9, hand=0.3, lift=0)
    if R() < 0.7:
        y2 = y + R(5, 9)
        stroke([(x - R(3, 7), y2), (x + R(3, 7), y2 + G(0.5))], w=0.7, hand=0.3, lift=0)

# water surface: level strokes, denser near the fish, thinning out toward the edges
y = 646.0
while y < 800:
    x = 140 + R(0, 20)
    while x < 450:
        L = R(12, 34)
        p0, p1 = (x, y + G(0.6)), (x + L, y + G(0.6))
        mid = lerp(p0, p1, 0.5)
        rr = ((mid[0] - P_CX) / P_RX) ** 2 + ((mid[1] - P_CY) / P_RY) ** 2
        if inside(p0, PUDDLE) and inside(p1, PUDDLE) and not near_ripple(mid) and R() < 0.95 * (1 - rr) + 0.2:
            stroke([p0, p1], w=0.65 if rr > 0.4 else 0.75, hand=0.3, lift=0)
        x += L + R(10, 30)
    y += R(6.0, 7.5)

# where the bank slips into the water
pen.line(catmull([(414, 704), (432, 724), (444, 748), (448, 770)], step=1.5), w=1.2, hand=0.6, lift=0.35, piece=(8, 24))


# ---------------------------------------------------------------- 6. the muddy bank

stroke(catmull(GROUND, step=2.0), w=1.9, lift=0.15)
# hatching down the bank's face, fading downward
for k in range(70):
    x = 440 + k * 8.0 + G(1.5)
    if x > 980:
        break
    y0 = ground_y(x) + 4
    if R() < 0.25:
        continue
    L = R(6, 18) * (1.0 if k % 3 else 1.5)
    stroke([(x, y0 + R(0, 2)), (x - L * 0.3, y0 + L)], w=0.7, hand=0.2, lift=0)
    if R() < 0.35:
        y1 = y0 + L + R(8, 22)
        stroke([(x + R(-3, 3), y1), (x - 3 + R(-3, 3), y1 + R(5, 12))], w=0.65, hand=0.2, lift=0)
# mud pushed up at the planted fins; pebbles
for (x, y, r) in [(530, 662, 2.2), (590, 630, 1.6), (850, 600, 2.0), (900, 594, 1.5), (960, 588, 2.2), (640, 612, 1.4)]:
    pen.ellipse(x, y, r * 1.4, r, w=0.9)


# ---------------------------------------------------------------- 7. a hint of early land plants

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


for (x, y, h, lean) in [(150, 672, 40, -0.1), (164, 666, 28, 0.15), (138, 680, 22, -0.2)]:
    sprig(x, y, h, lean)
for (x, y, h, lean) in [(940, 572, 42, 0.12), (954, 574, 30, -0.12)]:
    sprig(x, y, h, lean)


# ---------------------------------------------------------------- place it in the square

# the animal about 850 across, the whole drawing centred
fx = [x for p, _ in pen.strokes[:N_FISH] for x, _ in p]
SC = 830 / (max(fx) - min(fx))
cx = (min(fx) + max(fx)) / 2 - 8
ys = [y for p, _ in pen.strokes for _, y in p]
cy = (min(ys) + max(ys)) / 2
pen.strokes = [([(500 + (x - cx) * SC, 505 + (y - cy) * SC) for x, y in p], w) for p, w in pen.strokes]
# nothing of the ground runs off the square
pen.strokes = [(p, w) for p, w in pen.strokes if max(x for x, _ in p) < 985 and min(x for x, _ in p) > 15] + \
    [([(x, y) for x, y in p if 15 < x < 985], w) for p, w in pen.strokes
     if not (max(x for x, _ in p) < 985 and min(x for x, _ in p) > 15) and sum(1 for x, _ in p if 15 < x < 985) > 1]

pen.strokes = [(p, max(0.6, w)) for p, w in pen.strokes]  # the set's finest line is 0.6
pen.save('../12-quastenflosser.svg', mirror=True)
pen.report()
