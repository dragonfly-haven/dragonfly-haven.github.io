"""16 - crow: a carrion crow standing in profile, glossy black, drawn in ink.

Redrawn with pen.py, the earlier drawing serving only as the reference for pose and
proportions. Stout bill with nasal bristles over the
nostril, a slightly shaggy throat, the closed wing with scalloped covert rows and
stepped flight-feather tips lying over the tail, a rounded tail of separate
feathers, feathered thighs ending above the heel, scaled tarsi and toes.

The black plumage is hatching that follows the form: close and continuous in the
shadows (lower breast, belly, under the wing, the tail's underside), breaking up
into short strokes and white glints on the back, crown and upper wing, which is
how a glossy black bird reads in ink. Drawn facing right; saved mirrored.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw

from pen import Pen, catmull, resample, dist, lerp, length, ellipse_pts

pen = Pen(seed=1616)
rng = random.Random(16)


# ---------------------------------------------------------------- helpers

def C(ctrl, step=2.0):
    return catmull(ctrl, step=step)


class Curve:
    """A polyline with arc-length lookup, t in 0..1."""

    def __init__(self, pts, step=1.0):
        self.p = np.array(resample(list(pts), step), dtype=float)
        d = np.hypot(*np.diff(self.p, axis=0).T)
        self.s = np.concatenate([[0.0], np.cumsum(d)])
        self.L = float(self.s[-1])

    def at(self, t):
        s = min(max(t, 0.0), 1.0) * self.L
        return (float(np.interp(s, self.s, self.p[:, 0])), float(np.interp(s, self.s, self.p[:, 1])))

    def tangent(self, t, h=0.01):
        a, b = self.at(t - h), self.at(t + h)
        L = dist(a, b) or 1.0
        return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

    def part(self, t0, t1, step=1.5):
        n = max(3, int(abs(t1 - t0) * self.L / step))
        return [self.at(t0 + (t1 - t0) * k / n) for k in range(n + 1)]

    def pts(self):
        return [tuple(q) for q in self.p]


# occlusion: a raster of everything already drawn in front (2 px per unit)
MS = 2
OCC = np.zeros((1000 * MS, 1000 * MS), dtype=bool)


def poly_mask(poly):
    im = Image.new('L', (1000 * MS, 1000 * MS), 0)
    ImageDraw.Draw(im).polygon([(x * MS, y * MS) for x, y in poly], fill=255)
    return np.array(im) > 0


def occlude(poly):
    global OCC
    OCC |= poly_mask(poly)


def hidden(p):
    x, y = int(p[0] * MS), int(p[1] * MS)
    return 0 <= x < 1000 * MS and 0 <= y < 1000 * MS and OCC[y, x]


def draw(pts, w=1.2, hand=0.5, lift=0.12, piece=(22, 70), taper=0.0, clip=True):
    """An inked stroke, hidden where something in front was already drawn."""
    pts = list(pts)
    if len(pts) < 2:
        return
    runs = [pts]
    if clip:
        runs, cur = [], []
        for p in resample(pts, 0.8):
            if hidden(p):
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            runs.append(cur)
    for r in runs:
        if length(r) > 1.0:
            pen.line(r, w=w, hand=hand, lift=lift, piece=piece, taper=taper, occlude=False)


# ---------------------------------------------------------------- the bird's plan

# bill
CULMEN = C([(789, 318), (812, 319), (835, 323), (855, 330), (869, 340), (876, 350), (874, 355)])
LOWER_MANDIBLE = C([(872, 355), (852, 357), (828, 358), (806, 358), (791, 356)])
GAPE = C([(785, 341), (806, 342), (830, 344), (852, 347), (866, 351), (872, 355)])

# head, back and rump, from the forehead backwards
TOPLINE = Curve(C([(789, 314), (784, 303), (771, 293), (752, 286), (729, 282), (705, 284), (682, 291),
                   (661, 302), (638, 316), (606, 333), (570, 352), (530, 373), (490, 395), (452, 418),
                   (417, 441), (386, 462), (360, 481), (340, 495)]))
# chin, throat, breast, belly and vent, from the bill downwards and back
UNDER = Curve(C([(791, 357), (781, 363), (768, 373), (756, 387), (745, 405), (735, 426), (725, 451),
                 (715, 479), (706, 509), (696, 539), (682, 567), (662, 591), (636, 609), (604, 621),
                 (568, 628), (530, 628), (495, 622), (462, 613), (430, 605), (400, 600), (372, 598)]))
THROAT = (382, 452)      # y range of the shaggy throat on UNDER
HACKLE = 14

EYE = (760, 318)

# tail: top edge (from the rump back) and underside (from the undertail coverts back)
TAIL_TOP = Curve(C([(340, 495), (300, 513), (256, 532), (212, 550), (174, 564), (147, 574)]))
TAIL_BOT = Curve(C([(372, 598), (330, 601), (282, 604), (232, 607), (188, 609), (158, 611)]))
TAIL_V = [0.0, 0.27, 0.52, 0.76, 1.0]        # feather edges across the tail
TAIL_TIP = [141, 148, 156, 164]               # each feather's tip, x (central feathers longest)

# closed wing: top edge (under the scapulars) and lower edge, bend to tip
WTOP = Curve(C([(642, 366), (612, 377), (570, 393), (520, 413), (468, 436), (418, 462), (372, 489),
                (330, 512), (292, 528), (258, 538), (228, 544), (204, 548)]))
WBOT = Curve(C([(668, 440), (657, 478), (632, 508), (596, 531), (548, 548), (492, 560), (432, 569),
                (372, 576), (316, 581), (266, 585), (228, 588), (204, 590)]))
WFRONT = C([(642, 366), (656, 386), (666, 411), (668, 440)])

# legs: heel (top of the tarsus) and foot joint
LEG_NEAR = ((593, 640), (606, 713))
LEG_FAR = ((529, 638), (533, 715))
GROUND = 719


def W(u, v):
    """A point on the closed wing: u along it (bend 0 .. tip 1), v across (top 0 .. lower edge 1)."""
    return lerp(WTOP.at(u), WBOT.at(u), v)


def wing_poly():
    return WFRONT + WBOT.part(0, 1, 3) + list(reversed(WTOP.part(0, 1, 3)))


def body_poly():
    return (TOPLINE.pts()[::3] + [(352, 540), (372, 598)] + list(reversed(UNDER.pts()[::3]))
            + [(786, 341), (789, 318)])


def tail_poly():
    return (TAIL_TOP.pts()[::3] + [(141, 590)] + list(reversed(TAIL_BOT.pts()[::3]))
            + [(352, 540)])


# ---------------------------------------------------------------- legs and feet

def toe(base, tip, thick=4.0, claw=(8, 6), w=1.5, scutes=True):
    """A toe lying on the ground from its base to its tip, with a hooked claw."""
    bx, by = base
    tx, ty = tip
    L = dist(base, tip)
    ux, uy = (tx - bx) / L, (ty - by) / L
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny                   # the toe's upper side
    ts = np.linspace(0, 1, 14)
    # a toe is plump at its base and between its joints, thin toward the claw
    top = [(bx + ux * L * t + nx * thick * (1 - 0.5 * t) * (1 + 0.12 * math.sin(3 * math.pi * t)),
            by + uy * L * t + ny * thick * (1 - 0.5 * t) * (1 + 0.12 * math.sin(3 * math.pi * t))) for t in ts]
    bot = [(bx + ux * L * t, by + uy * L * t) for t in ts]
    ck, cd = claw
    c0 = lerp(top[-1], bot[-1], 0.25)
    tipc = (c0[0] + ux * ck - nx * cd, c0[1] + uy * ck - ny * cd)
    claw_out = C([c0, (c0[0] + ux * ck * 0.6 + nx * 0.8, c0[1] + uy * ck * 0.6 + ny * 0.8), tipc], step=0.7)
    claw_in = C([bot[-1], (bot[-1][0] + ux * ck * 0.55 - nx * cd * 0.35, bot[-1][1] + uy * ck * 0.55 - ny * cd * 0.35), tipc], step=0.7)
    draw(top, w=w, hand=0.2, lift=0)
    draw(bot, w=w * 1.15, hand=0.2, lift=0)
    draw(claw_out, w=1.5, hand=0, lift=0)
    draw(claw_in, w=1.0, hand=0, lift=0)
    if scutes:
        n = int(L / 6)
        for k in range(1, n):
            i = int(k / n * 13)
            draw([lerp(bot[i], top[i], 0.35), lerp(bot[i], top[i], 0.95)], w=0.75, hand=0, lift=0)
    return top + [tipc] + list(reversed(bot))


def leg(heel, foot):
    """Tarsus with its scutes, and the foot: two forward toes in view and the hind toe."""
    (hx, hy), (fx, fy) = heel, foot
    wd = 5.0
    front = C([(hx + wd, hy), ((hx + fx) / 2 + wd + 0.6, (hy + fy) / 2), (fx + wd - 0.8, fy - 3)], step=1.5)
    back = C([(hx - wd, hy), ((hx + fx) / 2 - wd + 0.3, (hy + fy) / 2), (fx - wd + 0.6, fy - 2)], step=1.5)
    jx, jy = fx, fy + 1
    polys = [toe((jx + 3, jy + 1.5), (jx + 52, GROUND + 0.5), thick=5.0, claw=(11, 7), w=1.6),
             toe((jx - 2, jy + 2), (jx - 32, GROUND + 0.5), thick=4.6, claw=(11, 8), w=1.6),
             toe((jx + 2, jy - 1), (jx + 40, GROUND - 4.5), thick=4.0, claw=(9, 6), w=1.3, scutes=False)]
    occlude(polys[0])
    occlude(polys[1])
    draw(front, w=1.8, hand=0.3, lift=0)
    draw(back, w=1.8, hand=0.3, lift=0)
    # scutes across the tarsus front (a smooth boot above, plates below), shade behind
    F, B = Curve(front), Curve(back)
    n = 8
    for k in range(n):
        t = 0.32 + 0.64 * k / (n - 1)
        a, b = F.at(t), B.at(t + 0.015)
        draw(C([a, lerp(a, b, 0.45), lerp(a, b, 0.7)], step=1), w=0.85, hand=0, lift=0)
    for k in range(4):
        t0 = 0.1 + 0.22 * k
        a, b = B.at(t0), B.at(t0 + 0.13)
        draw([lerp(a, F.at(t0), 0.2), lerp(b, F.at(t0 + 0.13), 0.2)], w=0.75, hand=0, lift=0)
    occlude(front + list(reversed(back)))
    occlude(polys[2])


def thigh(front_pts, back_pts, tufts=5):
    """A soft feathered thigh: a rounded lobe from the belly down to just above the heel,
    a ragged lower edge of feather tips, curved strokes down it, darker behind."""
    F, B = Curve(C(front_pts, step=1.5)), Curve(C(back_pts, step=1.5))
    lower = []
    pa, pb = F.at(1), B.at(1)
    for k in range(tufts):
        a, b = lerp(pa, pb, k / tufts), lerp(pa, pb, (k + 1) / tufts)
        m = lerp(a, b, 0.45)
        lower.append(C([a, (m[0] - 1, m[1] + 3.4), b], step=1))
    draw(F.part(0.12, 1), w=1.6, hand=0.3, lift=0.06)
    draw(B.part(0.5, 1), w=1.2, hand=0.3, lift=0.1)
    for seg in lower:
        draw(seg, w=1.15, hand=0, lift=0)
    # strokes following the lobe, spaced about 5 units, broken toward the lit front
    m = int(dist(F.at(0.5), B.at(0.5)) / 5.0)
    for i in range(1, m):
        f = i / m
        t0 = 0.05 + rng.uniform(0, 0.1)
        t1 = 0.93 - rng.uniform(0, 0.06)
        pts = [lerp(F.at(t), B.at(t), f) for t in np.linspace(t0, t1, 24)]
        if f < 0.22:
            pts = pts[len(pts) // 3:]
        draw(pts, w=0.9 + 0.5 * f, hand=0.3, lift=0.15, taper=0.25)
    poly = F.pts() + [q for seg in lower for q in seg] + list(reversed(B.pts()))
    occlude(poly)


# ---------------------------------------------------------------- the wing

COVERT_ROWS = [  # (u at the top edge, u at the lower edge, scallops)
    (0.14, 0.10, 6),
    (0.25, 0.20, 6),
    (0.37, 0.31, 5),
]
# the flight feathers, stacked like cards: each lower (outer) one lies over the lower
# part of the one above and reaches further back, so every feather shows its outer
# vane as a band along the wing and ends in a rounded tip; the tips step down to the
# wingtip over the tail. (top edge v, tip u) for tertials, secondaries, primaries.
CARDS = [(0.0, 0.55), (0.14, 0.62), (0.28, 0.69), (0.42, 0.76), (0.55, 0.83), (0.66, 0.91), (0.76, 1.0)]
CAPD = 0.026      # how far a rounded tip curves back, in u


def covert_u(row, v):
    a, b, _ = COVERT_ROWS[row]
    return a + (b - a) * v


def cap_u(k, v):
    """The rounded tip of card k at height v: furthest back mid-band."""
    a = CARDS[k][0]
    b = CARDS[k + 1][0] if k + 1 < len(CARDS) else 1.0
    t = min(1.0, max(0.0, (v - a) / (b - a)))
    return CARDS[k][1] - CAPD * (1 - math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7)


def wing_outline_top():
    """The wing's upper outline from the shoulder back: the top edge, then the tips
    stepping down card by card to the wingtip."""
    pts = [W(u, 0.0) for u in np.linspace(0.0, cap_u(0, 0.0), 80)]
    for k in range(len(CARDS)):
        a = CARDS[k][0]
        b = CARDS[k + 1][0] if k + 1 < len(CARDS) else 1.0
        pts += [W(cap_u(k, v), v) for v in np.linspace(a, b, 14)]
        if k + 1 < len(CARDS):
            u0, u1 = cap_u(k, b), cap_u(k + 1, b)
            pts += [W(u, b) for u in np.linspace(u0, u1, 12)]
    return pts


def wing_poly():
    return WFRONT + WBOT.part(0, 1, 3) + list(reversed(wing_outline_top()))


def wing_lines():
    """The wing's drawn lines: outline, covert scallops, flight-feather edges and tips.
    Returns (polyline, weight) pairs, so the hatching can keep clear of them."""
    out = []
    out.append((WFRONT + WBOT.part(0, 0.97, 2), 2.0))
    top = wing_outline_top()
    split = 80
    out.append((top[:split], 1.3))           # under the scapulars
    out.append((top[split - 1:], 1.8))       # the stepped tips
    # covert rows: rounded feather tips
    for row, (ua, ub, n) in enumerate(COVERT_ROWS):
        for i in range(n):
            v0, v1 = i / n, (i + 1) / n
            p0, p1 = W(covert_u(row, v0), v0), W(covert_u(row, v1), v1)
            du = 0.36 * dist(p0, p1) / WTOP.L        # bulge backwards, about a third of its width
            pts = []
            for a in np.linspace(0, math.pi, 13):
                v = v0 + (v1 - v0) * (1 - math.cos(a)) / 2
                pts.append(W(covert_u(row, v) + du * math.sin(a), v))
            out.append((pts, 1.25 if row == 2 else 1.1))
    # flight-feather edges inside the wing, each ending at the tip of the card above
    for k in range(1, len(CARDS)):
        a = CARDS[k][0]
        u0 = covert_u(2, a) - 0.01
        out.append(([W(u, a) for u in np.linspace(u0, cap_u(k - 1, a), 60)], 1.3))
    return out


def wing_hatching(D):
    """Long glossy strokes along each flight feather's visible band, spaced evenly up
    from its lower edge and stopping short of a white margin under its top edge."""
    for k in range(len(CARDS)):
        a = CARDS[k][0]
        b = CARDS[k + 1][0] if k + 1 < len(CARDS) else 1.0
        u_start = covert_u(2, (a + b) / 2) + 0.012
        for i in range(12):
            line = []
            for u in np.linspace(u_start + rng.uniform(0, 0.02), cap_u(k, b) + 0.02, 90):
                hgt = dist(W(u, 0), W(u, 1))
                v = b - (i + 0.55) * 5.3 / hgt
                if v < a + 0.32 * (b - a) or u > cap_u(k, v) - 0.014:
                    break
                q = W(u, v)
                if not hidden(q):
                    line.append(q)
                elif len(line) > 2:
                    break
            if len(line) < 3:
                continue
            # long strokes, a gap here and there where the light catches
            Cl = Curve(line, step=0.8)
            s = rng.uniform(0, 6)
            while s < Cl.L:
                p = Cl.at(s / Cl.L)
                d = min(1.0, max(0.0, lookup(D, p)))
                dl = 14 + 30 * d + rng.uniform(-4, 4)
                gap = 2.0 + 6 * (1 - d) + rng.uniform(-0.5, 1.5)
                if rng.random() < 0.2 + d:
                    seg = Cl.part(s / Cl.L, min(1.0, (s + dl) / Cl.L), 1.2)
                    draw(seg, w=0.72 + 0.85 * d ** 1.5, hand=0.25, lift=0, piece=(40, 90), taper=0.2)
                s += dl + gap


# ---------------------------------------------------------------- body plumage: streamlines

class Field:
    """A direction field blended from guide curves, sampled on a grid."""

    def __init__(self, guides, step=4):
        P, T, Wt = [], [], []
        for pts, wt in guides:
            c = Curve(pts, step=2.0)
            for i in range(len(c.p)):
                a = c.p[max(0, i - 2)]
                b = c.p[min(len(c.p) - 1, i + 2)]
                d = b - a
                d = d / (np.hypot(*d) or 1)
                P.append(c.p[i])
                T.append(d)
                Wt.append(wt)
        P, T, Wt = np.array(P), np.array(T), np.array(Wt)
        self.step = step
        xs = np.arange(0, 1001, step)
        self.n = len(xs)
        gx, gy = np.meshgrid(xs, xs)
        g = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
        U = np.zeros(len(g))
        V = np.zeros(len(g))
        for i0 in range(0, len(g), 4000):
            q = g[i0:i0 + 4000]
            d = np.hypot(q[:, None, 0] - P[None, :, 0], q[:, None, 1] - P[None, :, 1])
            wgt = Wt[None, :] / (d + 6.0) ** 3
            U[i0:i0 + 4000] = (wgt * T[None, :, 0]).sum(1)
            V[i0:i0 + 4000] = (wgt * T[None, :, 1]).sum(1)
        L = np.hypot(U, V) + 1e-9
        self.U = (U / L).reshape(self.n, self.n)
        self.V = (V / L).reshape(self.n, self.n)

    def dir(self, p):
        x, y = p[0] / self.step, p[1] / self.step
        i, j = int(y), int(x)
        if not (0 <= i < self.n - 1 and 0 <= j < self.n - 1):
            return (1.0, 0.0)
        fx, fy = x - j, y - i
        u = (self.U[i, j] * (1 - fx) * (1 - fy) + self.U[i, j + 1] * fx * (1 - fy)
             + self.U[i + 1, j] * (1 - fx) * fy + self.U[i + 1, j + 1] * fx * fy)
        v = (self.V[i, j] * (1 - fx) * (1 - fy) + self.V[i, j + 1] * fx * (1 - fy)
             + self.V[i + 1, j] * (1 - fx) * fy + self.V[i + 1, j + 1] * fx * fy)
        L = math.hypot(u, v) or 1.0
        return (u / L, v / L)


def streamlines(field, ok, sep, seeds, step=1.5, test=0.6, minlen=10.0, maxlen=260.0):
    """Evenly spaced streamlines (after Jobard and Lefer) with a varying separation."""
    cell = 6.0
    grid = {}

    def near(p, d, skip=None):
        cx, cy = int(p[0] // cell), int(p[1] // cell)
        r = int(d // cell) + 1
        for ix in range(cx - r, cx + r + 1):
            for iy in range(cy - r, cy + r + 1):
                for (qx, qy, lid) in grid.get((ix, iy), ()):
                    if lid != skip and (qx - p[0]) ** 2 + (qy - p[1]) ** 2 < d * d:
                        return True
        return False

    def trace(s, sign):
        out = [s]
        total = 0.0
        p = s
        while total < maxlen:
            d1 = field.dir(p)
            mid = (p[0] + sign * d1[0] * step / 2, p[1] + sign * d1[1] * step / 2)
            d2 = field.dir(mid)
            q = (p[0] + sign * d2[0] * step, p[1] + sign * d2[1] * step)
            if not ok(q) or near(q, test * sep(q)):
                break
            # no turning back on itself
            if len(out) > 8 and dist(q, out[-8]) < step * 2:
                break
            out.append(q)
            total += step
            p = q
        return out

    lines = []
    queue = list(seeds)
    qi = 0
    while qi < len(queue):
        s = queue[qi]
        qi += 1
        if not ok(s) or near(s, sep(s) * 0.95):
            continue
        a = trace(s, -1)
        b = trace(s, 1)
        line = list(reversed(a)) + b[1:]
        if length(line) < minlen:
            continue
        lid = len(lines)
        lines.append(line)
        for (x, y) in line:
            grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y, lid))
        # new seeds either side of it
        for i in range(0, len(line), 4):
            p = line[i]
            d = field.dir(p)
            sp = sep(p)
            for sgn in (1, -1):
                queue.append((p[0] - d[1] * sp * sgn, p[1] + d[0] * sp * sgn))
    return lines


# ---------------------------------------------------------------- shading maps

GX = np.arange(110, 900, 2.0)
GY = np.arange(250, 770, 2.0)
GXX, GYY = np.meshgrid(GX, GY)


def dmap(pts):
    """Distance from every grid point to a polyline (sampled every 2 units)."""
    P = np.array(resample(list(pts), 2.0))
    q = np.stack([GXX.ravel(), GYY.ravel()], 1)
    out = np.empty(len(q))
    for i0 in range(0, len(q), 6000):
        c = q[i0:i0 + 6000]
        out[i0:i0 + 6000] = np.sqrt(((c[:, None, :] - P[None, :, :]) ** 2).sum(-1)).min(1)
    return out.reshape(GXX.shape)


def lookup(M, p):
    j = int(round((p[0] - GX[0]) / 2))
    i = int(round((p[1] - GY[0]) / 2))
    if 0 <= i < M.shape[0] and 0 <= j < M.shape[1]:
        return float(M[i, j])
    return 0.0


def halo(lines, width):
    """A mask of the space around drawn lines, which hatching keeps clear of."""
    im = Image.new('L', (1000 * MS, 1000 * MS), 0)
    d = ImageDraw.Draw(im)
    for pts in lines:
        d.line([(x * MS, y * MS) for x, y in pts], fill=255, width=int(width * 2 * MS))
    return np.array(im) > 0


def feather_stroke(seg):
    """A hatching stroke made a little feather-like: turned a few degrees off the
    flow about its middle and bowed slightly, so rows of strokes do not read as grain."""
    if len(seg) < 3:
        return seg
    m = seg[len(seg) // 2]
    a = rng.gauss(0, math.radians(4.5))
    ca, sa = math.cos(a), math.sin(a)
    rot = [(m[0] + (x - m[0]) * ca - (y - m[1]) * sa, m[1] + (x - m[0]) * sa + (y - m[1]) * ca) for x, y in seg]
    a0, a1 = rot[0], rot[-1]
    L = dist(a0, a1) or 1
    nx, ny = -(a1[1] - a0[1]) / L, (a1[0] - a0[0]) / L
    b = rng.uniform(-0.9, 0.9)
    n = len(rot) - 1
    return [(x + nx * b * math.sin(math.pi * i / n), y + ny * b * math.sin(math.pi * i / n)) for i, (x, y) in enumerate(rot)]


def plumage(region, field, D, seeds_box, wbase=0.72, wvar=1.0, maxlen=240.0):
    """Hatching for a region: streamlines spaced by darkness (close where dark), each
    broken into feather strokes, long where dark and short and gappy toward the light."""
    def ok(p):
        x, y = int(p[0] * MS), int(p[1] * MS)
        return 0 <= x < 1000 * MS and 0 <= y < 1000 * MS and region[y, x] and lookup(D, p) > 0.06

    def sep(p):
        d = min(1.0, max(0.0, lookup(D, p)))
        return 5.2 + 6.5 * (1 - d) ** 1.5

    x0, y0, x1, y1 = seeds_box
    seeds = [(x + rng.uniform(-2, 2), y + rng.uniform(-2, 2)) for x in range(x0, x1, 7) for y in range(y0, y1, 7)]
    rng.shuffle(seeds)
    lines = streamlines(field, ok, sep, seeds, maxlen=maxlen)
    ink = 0.0
    for line in lines:
        if length(line) < 5:
            continue
        Cl = Curve(line, step=0.8)
        s = rng.uniform(0, 8)
        while s < Cl.L:
            p = Cl.at(s / Cl.L)
            raw = lookup(D, p)
            d = min(1.0, max(0.0, raw))
            deep = max(0.0, min(0.3, raw - 1.0))
            dl = 8 + 12 * d + 16 * d ** 4 + rng.uniform(-2.5, 2.5)
            gap = 1.8 + 6.5 * (1 - d) ** 1.5 + rng.uniform(-0.6, 1.6)
            if rng.random() < 0.1 + 1.1 * d:
                seg = Cl.part(s / Cl.L, min(1.0, (s + dl) / Cl.L), 1.2)
                seg = feather_stroke(seg)
                draw(seg, w=wbase + wvar * d ** 1.5 + 1.2 * deep, hand=0.2, lift=0, piece=(40, 90), taper=0.35)
                ink += length(seg)
            s += dl + gap
    return lines, ink


NECK_GLINT = C([(690, 300), (705, 330), (712, 365), (710, 400), (702, 440)])


def draw_tail():
    def T(u, v):
        """u along the tail (0 base .. 1 tip), v across (0 top .. 1 underside)."""
        return lerp(TAIL_TOP.at(u), TAIL_BOT.at(u), v)

    def u_at_x(x, v):
        lo, hi = 0.0, 1.0
        for _ in range(30):
            m = (lo + hi) / 2
            if T(m, v)[0] > x:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2

    lines = []
    lines.append((TAIL_TOP.part(0, 0.97), 1.9))
    lines.append((TAIL_BOT.part(0, 0.96), 2.3))
    tips = []
    for k in range(len(TAIL_TIP)):
        va, vb = TAIL_V[k], TAIL_V[k + 1]
        ua, ub = u_at_x(TAIL_TIP[k] + 10, va), u_at_x(TAIL_TIP[k] + 10, vb)
        pa, pb = T(ua, va), T(ub, vb)
        tip = T(u_at_x(TAIL_TIP[k], (va + vb) / 2), (va + vb) / 2)
        # rounded feather tip: a half-ellipse from edge to edge, reaching back to the tip
        cap = []
        for t in np.linspace(0, 1, 15):
            base = lerp(pa, pb, t)
            reach = math.sin(math.pi * t) ** 0.6
            cap.append((base[0] + (tip[0] - (pa[0] + pb[0]) / 2) * reach, base[1] + (tip[1] - (pa[1] + pb[1]) / 2) * reach))
        lines.append((cap, 1.7))
        tips.append(tip)
        if k > 0:
            lines.append(([T(u, va) for u in np.linspace(0.12, ua, 50)], 1.3))
    for pts, w in lines:
        draw(pts, w=w, hand=0.3, lift=0.05)
    region = poly_mask(tail_poly()) & ~OCC & ~halo([pts for pts, _ in lines], 3.4)
    # darker underneath, lit along the top
    dtop = dmap(TAIL_TOP.pts())
    D = 1.05 - 0.6 * np.exp(-dtop / 22.0) - 0.4 * np.exp(-((dtop - 8) / 4.0) ** 2)
    guides = [(TAIL_TOP.pts(), 1.0), (TAIL_BOT.pts(), 1.0)]
    for k in range(1, len(TAIL_V) - 1):
        guides.append(([T(u, TAIL_V[k]) for u in np.linspace(0.05, 0.95, 40)], 1.0))
    field = Field(guides)
    plumage(region, field, D, (140, 490, 380, 615), maxlen=300)


# ---------------------------------------------------------------- drawing

def main():
    # --- legs, feet and thighs (in front of the belly)
    leg(*LEG_NEAR)
    leg(*LEG_FAR)
    thigh([(624, 600), (631, 617), (625, 633), (612, 643)], [(566, 616), (568, 629), (576, 640), (585, 646)])
    thigh([(572, 616), (575, 630), (566, 641), (553, 647)], [(510, 612), (512, 626), (520, 638), (530, 645)], tufts=5)

    # --- the wing, in front of the body and the tail
    wl = wing_lines()
    for pts, w in wl:
        draw(pts, w=w, hand=0.3, lift=0.04, piece=(30, 80))
    dwt = dmap(WTOP.pts())
    Dw = 1.15 - 0.9 * np.exp(-dwt / 36.0)                     # lit along the top, dark below
    Dw = Dw - 0.35 * np.exp(-((dwt - 14) / 8.0) ** 2) * (GXX > 430)   # gloss across the upper coverts
    # coverts: short strokes inside each row of feathers
    cov = [W(covert_u(2, v) + 0.012, v) for v in np.linspace(1, 0, 20)]
    coverts = poly_mask(WFRONT + WBOT.part(0, 0.3, 2) + cov + list(reversed(WTOP.part(0, 0.4, 2))))
    wregion = poly_mask(wing_poly()) & coverts & ~OCC & ~halo([pts for pts, _ in wl], 3.0)
    wguides = [(WTOP.pts(), 1.0), (WBOT.pts(), 1.0)]
    plumage(wregion, Field(wguides), Dw, (440, 360, 680, 560), maxlen=60)
    # flight feathers: long strokes
    occlude_save = OCC.copy()
    np.logical_or(OCC, halo([pts for pts, _ in wl], 2.6), out=OCC)
    wing_hatching(Dw)
    OCC[:] = occlude_save
    occlude(wing_poly())

    # --- bill
    draw(CULMEN, w=2.2, hand=0, lift=0)
    draw(LOWER_MANDIBLE, w=2.0, hand=0, lift=0)
    draw(GAPE, w=1.5, hand=0, lift=0)
    cu, ga = Curve(CULMEN), Curve(GAPE)
    for f, (a, b) in ((0.55, (0.12, 0.8)), (0.75, (0.08, 0.86))):
        line = [lerp(cu.at(a + (b - a) * t), ga.at(a + (b - a) * t), f) for t in np.linspace(0, 1, 30)]
        draw(line, w=0.8, hand=0, lift=0.1)
    lm = Curve(list(reversed(LOWER_MANDIBLE)))
    draw([lerp(ga.at(t), lm.at(t), 0.55) for t in np.linspace(0.1, 0.75, 20)], w=0.75, hand=0, lift=0)
    occlude(CULMEN + list(reversed(LOWER_MANDIBLE)))

    # nasal bristles lying forward over the nostril
    for j in range(6):
        u = j / 5
        root = (779 + 5 * u, 301 + 30 * u)
        tip = (813 - 3 * u + rng.uniform(-1, 1), 316 + 18 * u)
        mid = lerp(root, tip, 0.5)
        draw(C([root, (mid[0], mid[1] - 2.5), tip], step=1.5), w=0.9, hand=0, lift=0)
    occlude([(778, 299), (816, 312), (816, 336), (784, 340)])

    # eye: dark, with a lid line
    pen.blot(EYE[0], EYE[1], 5.6, 5.2, w=1.9)
    draw(ellipse_pts(EYE[0], EYE[1], 8.2, 7.6, 0, math.pi * 1.05, math.pi * 1.95, step=1), w=1.0, hand=0, lift=0)
    occlude(ellipse_pts(EYE[0], EYE[1], 10.5, 10, step=2))

    # --- outline of head and body
    top = TOPLINE.pts()
    draw(top[:int(len(top) * 0.3)], w=2.0, hand=0.4, lift=0.06, piece=(30, 80))
    draw(top[int(len(top) * 0.3) - 2:], w=1.9, hand=0.5, lift=0.12, piece=(30, 80))
    U = UNDER
    ts = np.linspace(0, 1, 800)
    ys = [U.at(t)[1] for t in ts]
    t_top = next(t for t, y in zip(ts, ys) if y >= THROAT[0])
    t_bot = next(t for t, y in zip(ts, ys) if y >= THROAT[1])
    draw(U.part(0, t_top + 0.004), w=2.1, hand=0.2, lift=0)
    draw(U.part(t_bot - 0.004, 0.62), w=2.3, hand=0.4, lift=0.05, piece=(30, 80))
    draw(U.part(0.62, 1.0), w=2.4, hand=0.4, lift=0.05, piece=(30, 80))
    # the throat breaks into a few pointed hackles hanging like shingles
    hackles = []
    n_h = int(round((t_bot - t_top) * U.L / HACKLE))
    for j in range(n_h):
        t_root = t_top + (t_bot - t_top) * j / n_h
        P = U.at(t_root)
        tx, ty = U.tangent(t_root)
        nx, ny = ty, -tx
        if nx < 0:
            nx, ny = -nx, -ny

        def at(dn, dt):
            return (P[0] + nx * dn + tx * dt, P[1] + ny * dn + ty * dt)
        out = 2.8 + 1.0 * ((j * 7) % 3) / 2
        tip = at(out, HACKLE + 2)
        hackles.append(C([at(-0.6, -1), at(out * 0.45, HACKLE * 0.55), tip], step=1.2))
        draw(hackles[-1], w=2.1, hand=0, lift=0)
        draw([tip, at(-1.0, HACKLE - 2.0)], w=1.4, hand=0, lift=0)

    # --- body plumage
    dtop = dmap(TOPLINE.pts())
    dund = dmap(UNDER.pts())
    dneck = dmap(NECK_GLINT)
    front = (GXX > 600) & (GYY < 600)
    D = 1.25 - 1.12 * np.exp(-dtop / 46.0)                          # lit from above
    D = D + 0.15 * np.exp(-dund / 28.0) * front                      # the breast turns from the light
    D = D - 0.62 * np.exp(-((dtop - 14) / 6.0) ** 2) * (GXX < 700)    # gloss along the back
    D = D - 0.6 * np.exp(-((dtop - 8) / 3.2) ** 2) * (GXX >= 700)     # and over the crown
    head = np.clip((GXX - 670) / 35.0, 0, 1) * (GYY < 420)
    D = D + head * np.clip(0.88 - D, 0, None) * (dtop > 13)                # the head is black, bar the crown's glint
    D = D - 0.45 * np.exp(-(dneck / 6.0) ** 2) * (GYY < 470)          # a glint down the neck
    D[np.minimum(dtop, dund) < 3.5] = -1
    bregion = poly_mask(body_poly()) & ~OCC & ~halo(hackles, 2.5) & ~halo([WFRONT + WBOT.pts()], 3.6)
    field = Field([
        (TOPLINE.pts(), 1.0),
        (UNDER.pts(), 1.0),
        (C([(788, 334), (765, 330), (738, 326), (708, 328), (680, 338), (655, 356), (630, 378)]), 0.7),
        (C([(742, 360), (726, 392), (712, 430), (700, 475), (688, 520), (668, 560)]), 0.5),
        (WTOP.pts(), 0.8),
        (WBOT.pts(), 0.8),
        (C([(640, 585), (600, 600), (560, 606), (520, 606), (480, 600), (440, 596), (400, 594)]), 0.6),
    ])
    plumage(bregion, field, D, (340, 280, 800, 640))

    # --- tail: separate feathers, rounded stepped tips
    draw_tail()

    # --- ground
    draw(C([(300, GROUND + 2), (420, GROUND + 1.5), (500, GROUND + 2)]), w=1.1, hand=0.8, lift=0.3)
    draw(C([(680, GROUND + 2), (780, GROUND + 2.5)]), w=1.1, hand=0.8, lift=0.3)
    for k, (x0, x1) in enumerate([(470, 650), (440, 610), (500, 670), (480, 590)]):
        y = GROUND + 6 + k * 5.2
        draw([(x0 + rng.uniform(-8, 8), y), (x1 + rng.uniform(-8, 8), y + rng.uniform(-0.5, 0.5))], w=0.8, hand=0.5, lift=0.3)

    pen.save('../16-crow.svg', mirror=True)
    pen.report()


if __name__ == '__main__':
    main()
