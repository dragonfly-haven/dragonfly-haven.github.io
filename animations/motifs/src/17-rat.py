"""17 - rat: a brown rat (Rattus norvegicus) standing alert in profile, drawn in ink.

Redrawn with pen.py; the earlier drawing served only as a reference for the head.
A deep chest and shoulder, a slight dip behind the shoulders and a high rounded rump
over a well-muscled haunch; the hind leg runs from the thigh to the knee, down to
the heel and along a long plantigrade foot with five clawed toes; the foreleg shows
its elbow, the forearm and a small hand of four clawed fingers and a thumb nub.
Blunt snout with its nose pad and cleft lip, the upper incisors, a large rounded
ear with its rim and inner fold, a dark eye with a highlight, whiskers in a fan.
The naked tail is about as long as the body, thick at the root and tapering, ringed
with fine scale bands and a few sparse hairs; it sweeps down behind and forward
along the ground.

The fur is engraving strokes that follow the lie of the hair and so the form:
back along the body, over the shoulder and down the foreleg, in arcs around the
haunch and down the shank; dark along the back and upper flank, lighter on the
cheek and haunch where the light falls, pale on the belly; guard hairs break the
outline along the back. Drawn facing right; saved mirrored.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw

from pen import Pen, catmull, resample, dist, lerp, length, ellipse_pts

pen = Pen(seed=1717)
rng = random.Random(17)


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


def halo(lines, width):
    """A mask of the space around drawn lines, which hatching keeps clear of."""
    im = Image.new('L', (1000 * MS, 1000 * MS), 0)
    d = ImageDraw.Draw(im)
    for pts in lines:
        d.line([(x * MS, y * MS) for x, y in pts], fill=255, width=int(width * 2 * MS))
    return np.array(im) > 0


def normal_out(curve, t, inside):
    """Unit normal of a curve at t pointing away from the point `inside`."""
    tx, ty = curve.tangent(t)
    nx, ny = -ty, tx
    p = curve.at(t)
    if (inside[0] - p[0]) * nx + (inside[1] - p[1]) * ny > 0:
        nx, ny = -nx, -ny
    return nx, ny, tx, ty


# ---------------------------------------------------------------- flow fields and fur

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
        th = np.arctan2(T[:, 1], T[:, 0])
        C2, S2 = np.cos(2 * th), np.sin(2 * th)
        self.step = step
        xs = np.arange(0, 1001, step)
        self.n = len(xs)
        gx, gy = np.meshgrid(xs, xs)
        g = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
        U = np.zeros(len(g))
        V = np.zeros(len(g))
        for i0 in range(0, len(g), 3000):
            q = g[i0:i0 + 3000]
            d = np.hypot(q[:, None, 0] - P[None, :, 0], q[:, None, 1] - P[None, :, 1])
            wgt = Wt[None, :] / (d + 6.0) ** 3
            # directions are axial (a hair stroke has no head or tail): blend doubled angles
            U[i0:i0 + 3000] = (wgt * C2[None, :]).sum(1)
            V[i0:i0 + 3000] = (wgt * S2[None, :]).sum(1)
        L = np.hypot(U, V) + 1e-12
        self.U = (U / L).reshape(self.n, self.n)      # doubled-angle components
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
        a = 0.5 * math.atan2(v, u)
        return (math.cos(a), math.sin(a))


def streamlines(field, ok, sep, seeds, step=1.5, test=0.6, minlen=8.0, maxlen=260.0):
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
        prev = None
        while total < maxlen:
            d1 = field.dir(p)
            if prev is not None and d1[0] * prev[0] + d1[1] * prev[1] < 0:
                d1 = (-d1[0], -d1[1])
            mid = (p[0] + sign * d1[0] * step / 2, p[1] + sign * d1[1] * step / 2)
            d2 = field.dir(mid)
            if d2[0] * d1[0] + d2[1] * d1[1] < 0:
                d2 = (-d2[0], -d2[1])
            q = (p[0] + sign * d2[0] * step, p[1] + sign * d2[1] * step)
            if not ok(q) or near(q, test * sep(q)):
                break
            if len(out) > 8 and dist(q, out[-8]) < step * 2:
                break
            out.append(q)
            total += step
            prev = d2
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
        for i in range(0, len(line), 4):
            p = line[i]
            d = field.dir(p)
            sp = sep(p)
            for sgn in (1, -1):
                queue.append((p[0] - d[1] * sp * sgn, p[1] + d[0] * sp * sgn))
    return lines


GX = np.arange(60, 960, 2.0)
GY = np.arange(280, 760, 2.0)
GXX, GYY = np.meshgrid(GX, GY)


def dmap(pts):
    """Distance from every grid point to a polyline (sampled every 2 units)."""
    P = np.array(resample(list(pts), 2.0))
    q = np.stack([GXX.ravel(), GYY.ravel()], 1)
    out = np.empty(len(q))
    for i0 in range(0, len(q), 5000):
        c = q[i0:i0 + 5000]
        out[i0:i0 + 5000] = np.sqrt(((c[:, None, :] - P[None, :, :]) ** 2).sum(-1)).min(1)
    return out.reshape(GXX.shape)


def blob(cx, cy, r):
    """A soft round bump of radius r on the grid, 1 at its centre."""
    return np.exp(-((GXX - cx) ** 2 + (GYY - cy) ** 2) / (2.0 * r * r))


def lookup(M, p):
    j = int(round((p[0] - GX[0]) / 2))
    i = int(round((p[1] - GY[0]) / 2))
    if 0 <= i < M.shape[0] and 0 <= j < M.shape[1]:
        return float(M[i, j])
    return 0.0


def hair_stroke(seg, turn=6.0, bow=1.0):
    """A fur stroke: turned a few degrees about its root and bowed a little, so rows
    of strokes read as hair, not as grain."""
    if len(seg) < 3:
        return seg
    m = seg[0]
    a = rng.gauss(0, math.radians(turn))
    ca, sa = math.cos(a), math.sin(a)
    rot = [(m[0] + (x - m[0]) * ca - (y - m[1]) * sa, m[1] + (x - m[0]) * sa + (y - m[1]) * ca) for x, y in seg]
    a0, a1 = rot[0], rot[-1]
    L = dist(a0, a1) or 1
    nx, ny = -(a1[1] - a0[1]) / L, (a1[0] - a0[0]) / L
    b = rng.uniform(-bow, bow)
    n = len(rot) - 1
    return [(x + nx * b * math.sin(math.pi * i / n), y + ny * b * math.sin(math.pi * i / n)) for i, (x, y) in enumerate(rot)]


def fur(region, field, D, box, wbase=0.66, wvar=0.8, maxlen=220.0, seedstep=7, lenscale=1.0):
    """Fur for a region: streamlines spaced by darkness (close where dark), each broken
    into hair strokes, long and close where dark, short and gappy toward the light."""
    def ok(p):
        x, y = int(p[0] * MS), int(p[1] * MS)
        return 0 <= x < 1000 * MS and 0 <= y < 1000 * MS and region[y, x] and lookup(D, p) > 0.05

    def sep(p):
        d = min(1.0, max(0.0, lookup(D, p)))
        return 5.0 + 5.5 * (1 - d) ** 1.5

    x0, y0, x1, y1 = box
    seeds = [(x + rng.uniform(-2, 2), y + rng.uniform(-2, 2)) for x in range(x0, x1, seedstep) for y in range(y0, y1, seedstep)]
    rng.shuffle(seeds)
    lines = streamlines(field, ok, sep, seeds, maxlen=maxlen)
    n = 0
    for line in lines:
        if length(line) < 4:
            continue
        Cl = Curve(line, step=0.8)
        s = rng.uniform(0, 9)
        while s < Cl.L:
            p = Cl.at(s / Cl.L)
            raw = lookup(D, p)
            d = min(1.0, max(0.0, raw))
            deep = max(0.0, min(0.35, raw - 1.0))
            dl = (7 + 12 * d + 10 * d ** 3 + rng.uniform(-2.5, 3.0)) * lenscale
            gap = 1.6 + 6.0 * (1 - d) ** 1.4 + rng.uniform(-0.5, 1.6)
            if rng.random() < 0.2 + 1.0 * d:
                seg = Cl.part(s / Cl.L, min(1.0, (s + dl) / Cl.L), 1.0)
                seg = hair_stroke(seg)
                draw(seg, w=wbase + wvar * d ** 1.5 + 1.3 * deep, hand=0.15, lift=0, piece=(40, 90), taper=0.45)
                n += 1
            s += dl + gap
    return n


# ---------------------------------------------------------------- the rat's plan (facing right)

GROUND = 646

# head and back, from the top of the nose pad to the root of the tail
TOPLINE = Curve(C([(877, 410), (862, 403), (843, 396), (822, 388), (800, 380), (780, 374), (760, 371),
                   (740, 373), (722, 379), (705, 389), (688, 398), (668, 404), (648, 407), (625, 411),
                   (600, 416), (572, 416), (540, 411), (505, 404), (470, 399), (440, 398), (412, 403),
                   (388, 415), (368, 433), (354, 455), (347, 478), (346, 498)]))
# snout tip: nose pad, cleft upper lip, chin
NOSE = C([(877, 410), (884, 414), (888, 421), (887, 429), (882, 435), (875, 437)], step=1.0)
LIP = C([(875, 437), (874, 444), (870, 451), (862, 455), (850, 456)], step=1.0)
CHIN = C([(863, 461), (858, 467), (850, 471)], step=1.0)
# under the jaw, the throat and the chest to the front of the foreleg
UNDER = Curve(C([(850, 471), (828, 477), (806, 485), (787, 495), (770, 508), (757, 524), (749, 542),
                 (744, 558)]))
# near foreleg: front and back of the forearm, from the chest and the elbow to the wrist
FL_FRONT = Curve(C([(744, 558), (737, 580), (730, 600), (725, 616), (722, 630)]))
FL_BACK = Curve(C([(700, 566), (689, 571), (684, 580), (688, 594), (696, 612), (703, 631)]))
# belly from the knee forward to the elbow
BELLY = Curve(C([(520, 570), (545, 576), (580, 580), (620, 580), (655, 576), (680, 570), (700, 566)]))
# hind leg: buttock down to the heel; shank front from the knee to the ankle
REAR = Curve(C([(349, 516), (353, 536), (363, 558), (378, 581), (396, 603), (412, 620), (422, 630)]))
SHANK = Curve(C([(520, 570), (506, 583), (491, 598), (478, 612), (469, 622)]))
THIGH = Curve(C([(533, 436), (540, 476), (539, 515), (532, 547), (520, 570)]))   # front of the thigh mass
EYE = (806, 400)


def body_poly():
    return (TOPLINE.pts()[::3] + REAR.pts()[::3] + [(445, 630), (469, 622)]
            + list(reversed(SHANK.pts()[::3])) + BELLY.pts()[::3] + FL_BACK.pts()[::3]
            + list(reversed(FL_FRONT.pts()[::3])) + list(reversed(UNDER.pts()[::3]))
            + CHIN[::-1] + LIP[::-1] + NOSE[::-1])


# ---------------------------------------------------------------- digits, hands and feet

def digit(base, tip, thick=5.0, claw=5.0, w=1.3, joints=(0.5,)):
    """A finger or toe lying forward from its base to its tip: plump, a little swollen
    at the joints and at the tip pad, with a short hooked claw. Returns its outline."""
    bx, by = base
    tx, ty = tip
    L = dist(base, tip)
    ux, uy = (tx - bx) / L, (ty - by) / L
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny                   # the digit's upper side
    half = thick / 2

    def wd(t):
        bump = sum(0.1 * math.exp(-((t - j) / 0.09) ** 2) for j in joints)
        return half * (1 - 0.22 * t) * (1 + bump) * (1 + 0.12 * math.exp(-((t - 0.9) / 0.08) ** 2))

    ts = np.linspace(0, 1, 18)
    top = [(bx + ux * L * t + nx * wd(t), by + uy * L * t + ny * wd(t)) for t in ts]
    bot = [(bx + ux * L * t - nx * wd(t) * 0.9, by + uy * L * t - ny * wd(t) * 0.9) for t in ts]
    r = wd(1)
    cap = [(tx + ux * r * 0.8 * math.sin(a) + nx * r * (math.cos(a) if math.cos(a) > 0 else 0.9 * math.cos(a)),
            ty + uy * r * 0.8 * math.sin(a) + ny * r * (math.cos(a) if math.cos(a) > 0 else 0.9 * math.cos(a)))
           for a in np.linspace(0, math.pi, 9)]
    # claw from the top of the tip, hooking forward and down
    c0 = lerp(top[-3], cap[1], 0.5)
    ctip = (tx + ux * (r * 0.8 + claw) - nx * r * 0.9, ty + uy * (r * 0.8 + claw) - ny * r * 0.9)
    c_out = C([c0, (tx + ux * (r * 0.8 + claw * 0.55) + nx * r * 0.55, ty + uy * (r * 0.8 + claw * 0.55) + ny * r * 0.55), ctip], step=0.5)
    c_in = C([cap[4], (tx + ux * (r * 0.8 + claw * 0.45) - nx * r * 0.2, ty + uy * (r * 0.8 + claw * 0.45) - ny * r * 0.2), ctip], step=0.5)
    draw(c_out, w=1.3, hand=0, lift=0)
    draw(c_in, w=0.85, hand=0, lift=0)
    draw(top + cap, w=w, hand=0.1, lift=0)
    draw(bot, w=w * 1.12, hand=0.1, lift=0)
    for j in joints:
        i = int(round(j * 17))
        draw([lerp(bot[i], top[i], 0.15), lerp(bot[i], top[i], 0.8)], w=0.7, hand=0, lift=0)
    return top + cap + [ctip] + list(reversed(bot))


def near_hand():
    """Near forefoot: the palm on the ground, four slender clawed fingers fanned
    forward, a thumb nub behind them."""
    for base, tip, th, j in (((729, 641.5), (744, 647), 4.6, (0.5,)), ((733, 639), (751, 645.5), 4.8, (0.45,)),
                             ((735, 636.5), (755, 641.5), 4.8, (0.45,)), ((733, 633.5), (751, 636), 4.4, (0.45,))):
        occlude(digit(base, tip, thick=th, claw=4.2, w=1.25, joints=j))
    dors = C([(722, 630), (729, 632.5), (736, 635)], step=1)
    palm = C([(705, 633), (707, 640), (713, 645.2), (729, 646.5)], step=1)
    draw(dors, w=1.6, hand=0.1, lift=0)
    draw(palm, w=1.8, hand=0.1, lift=0)
    # the thumb: a small rounded nub with a flat nail, at the inner side of the wrist
    nub = ellipse_pts(711, 637.5, 3.6, 2.8, -0.35, math.pi * 0.9, math.pi * 2.2, step=0.5)
    draw(nub, w=1.1, hand=0, lift=0)
    draw(C([(713.8, 635.2), (716.2, 637.2), (715.4, 639.4)], step=0.5), w=0.9, hand=0, lift=0)
    hand = [(703, 631), (722, 629), (736, 633), (741, 640), (729, 647.5), (712, 646), (704, 640)]
    occlude(hand)


def near_foot():
    """Near hind foot: plantigrade, the long sole flat from the heel to the toes, five
    clawed toes (the short first toe on the far side)."""
    toes = [((516, 642.5), (533, 647.5), 5.6, (0.45,)),        # fifth, the outer, nearest
            ((520, 640), (545, 646.5), 6.0, (0.38, 0.7)),
            ((522, 637.5), (551, 643), 6.0, (0.38, 0.7)),
            ((520, 634.5), (547, 637.5), 5.6, (0.38, 0.7)),
            ((511, 631.5), (527, 631), 4.8, (0.5,))]           # first, short, on the far side
    for base, tip, th, j in toes:
        occlude(digit(base, tip, thick=th, claw=5.0, w=1.3, joints=j))
    top = C([(469, 622), (484, 628), (500, 632.5), (514, 635), (520, 637)], step=1.5)
    sole = C([(421, 641), (430, 646.5), (460, 647.5), (490, 647.5), (517, 647)], step=1.5)
    heel = C([(422, 630), (418.5, 636), (421, 641)], step=1)
    draw(top, w=1.7, hand=0.2, lift=0)
    draw(sole, w=2.0, hand=0.2, lift=0)
    draw(heel, w=1.9, hand=0, lift=0)
    # the ankle crease and a few short hairs on the top of the foot and the heel
    draw(C([(468, 624), (464, 632), (465, 640)], step=1), w=0.8, hand=0, lift=0)
    for k in range(7):
        a = (473 + k * 6.3 + rng.uniform(-1, 1), 628 + k * 1.1 + rng.uniform(0, 1.5))
        b = (a[0] + 6 + rng.uniform(0, 2), a[1] + 2.0 + rng.uniform(0, 1))
        draw([a, b], w=0.7, hand=0, lift=0, taper=0.4)
    for k in range(6):
        a = (428 + k * 6.5 + rng.uniform(-1, 1), 634 + rng.uniform(0, 3))
        draw([a, (a[0] + 6, a[1] + 1.5)], w=0.65, hand=0, lift=0, taper=0.4)
    occlude(top + [(522, 640), (515, 648)] + list(reversed(sole)) + heel[::-1] + [(445, 628)])


# ---------------------------------------------------------------- head

def draw_eye():
    cx, cy = EYE
    rx, ry = 7.8, 7.2
    hx, hy, hr = cx - 2.4, cy - 2.6, 2.5          # the highlight
    w = 1.7
    turns = max(1.0, max(rx, ry) / (w * 0.75))
    n = int(turns * 60)
    pts = []
    for k in range(n + 1):
        u = k / n
        a = u * turns * 2 * math.pi
        pts.append((cx + rx * u * math.cos(a), cy + ry * u * math.sin(a)))
    pts += ellipse_pts(cx, cy, rx, ry, 0, turns * 2 * math.pi, turns * 2 * math.pi + 2 * math.pi, step=0.6)
    run = []
    for p in resample(pts, 0.5):
        if dist(p, (hx, hy)) < hr + 0.9:
            if len(run) > 1:
                pen.line(run, w=w, hand=0, lift=0, piece=(400, 800), occlude=False)
            run = []
        else:
            run.append(p)
    if len(run) > 1:
        pen.line(run, w=w, hand=0, lift=0, piece=(400, 800), occlude=False)
    # lids: a fine ring around the bulging eye, fuller above
    draw(ellipse_pts(cx, cy, rx + 2.6, ry + 2.4, 0, math.pi * 0.95, math.pi * 2.05, step=0.8), w=1.0, hand=0, lift=0, clip=False)
    draw(ellipse_pts(cx, cy, rx + 2.3, ry + 2.0, 0, math.pi * 0.2, math.pi * 0.75, step=0.8), w=0.8, hand=0, lift=0, clip=False)
    occlude(ellipse_pts(cx, cy, rx + 4.5, ry + 4.2, step=1.5))


EAR = C([(766, 380), (770, 363), (767, 347), (759, 335), (747, 328), (734, 327), (722, 333), (715, 344),
         (714, 358), (718, 371), (726, 383)], step=1.2)


def draw_ear():
    """The large rounded ear, thin and nearly naked, with its rim and inner folds."""
    E = Curve(EAR)
    draw(E.part(0, 0.97), w=1.9, hand=0.2, lift=0, taper=0.15)
    rim = Curve(C([(763, 364), (761, 350), (753, 340), (741, 334), (730, 335), (722, 343), (719, 355),
                   (720, 367), (723, 376)], step=1))
    draw(rim.part(0.04, 1), w=1.05, hand=0.1, lift=0.05, taper=0.3)
    fold = Curve(C([(759, 381), (754, 370), (746, 361), (737, 356), (730, 359)], step=1))
    draw(fold.pts(), w=1.25, hand=0.1, lift=0, taper=0.2)
    draw(C([(738, 382), (734, 374), (730, 368)], step=1), w=1.0, hand=0, lift=0, taper=0.3)
    # shade in the bowl of the ear, under the rim
    for k in range(6):
        a = 0.2 + k * 0.1
        p0 = lerp(rim.at(a), fold.at(min(1, 0.3 + k * 0.13)), 0.15)
        p1 = lerp(rim.at(a), fold.at(min(1, 0.3 + k * 0.13)), 0.68)
        draw([p0, p1], w=0.7, hand=0.1, lift=0, taper=0.4)
    for t in (0.3, 0.42, 0.55, 0.67):
        nx, ny, tx, ty = normal_out(E, t, (742, 360))
        p = E.at(t)
        draw([(p[0] - nx * 0.5, p[1] - ny * 0.5), (p[0] + nx * 4 - tx * 2, p[1] + ny * 4 - ty * 2)], w=0.6, hand=0, lift=0)
    occlude(EAR)


SNOUT_TIP = NOSE + LIP[1:] + [(866, 456), (866, 465), (871, 465), (872, 452)]


def draw_snout():
    """Nose pad with its nostril, the cleft lip, the upper incisors, the chin."""
    draw(NOSE, w=2.0, hand=0, lift=0)
    draw(C([(884.5, 417.5), (881, 420), (880.5, 424.5), (883.5, 427)], step=0.5), w=1.3, hand=0, lift=0)
    draw(C([(874, 411), (877.5, 417), (877, 425), (875.5, 433)], step=0.7), w=0.8, hand=0, lift=0)
    draw(LIP, w=1.6, hand=0, lift=0)
    draw(C([(876, 435), (873, 440), (872.5, 445)], step=0.6), w=0.8, hand=0, lift=0)
    # upper incisors showing under the lip
    draw([(866.5, 455), (866.8, 464.5)], w=1.2, hand=0, lift=0)
    draw([(870.5, 454), (870, 464)], w=1.2, hand=0, lift=0)
    draw([(866.6, 464.6), (870.2, 464.2)], w=1.0, hand=0, lift=0)
    draw([(868.6, 455), (868.5, 463.5)], w=0.6, hand=0, lift=0)
    draw(C([(850, 456), (842, 456), (836, 454)], step=0.8), w=1.1, hand=0, lift=0, taper=0.3)
    draw(CHIN, w=1.7, hand=0, lift=0)
    occlude(SNOUT_TIP)


def whiskers():
    """A neat fan of whiskers from the whisker pad, longest in the middle rows,
    each curving gently back at its tip; a pair over the eye."""
    out = []
    n = 12
    for i in range(n):
        u = i / (n - 1)
        root = (860 - 7 * math.sin(math.pi * u) + rng.uniform(-1, 1), 420 + 30 * u)
        ang = math.radians(-26 + 56 * u + rng.uniform(-2, 2))
        L = 70 + 44 * math.sin(math.pi * (0.25 + 0.6 * u)) + rng.uniform(-6, 6)
        dx, dy = math.cos(ang), math.sin(ang)
        bend = 0.12 * L
        mid = (root[0] + dx * L * 0.5, root[1] + dy * L * 0.5 + bend * 0.25)
        tip = (root[0] + dx * L, root[1] + dy * L + bend)
        out.append((C([root, mid, tip], step=2), 0.85 - 0.15 * abs(u - 0.5)))
    for k, (ang, L) in enumerate(((112, 34), (126, 40), (140, 30))):
        a = math.radians(ang)
        root = (852 - k * 3, 447 + k)
        tip = (root[0] + math.cos(a) * L, root[1] + math.sin(a) * L)
        mid = lerp(root, tip, 0.5)
        out.append((C([root, (mid[0] + 2, mid[1] - 2), tip], step=2), 0.7))
    for root, tip in (((813, 387), (849, 350)), ((809, 386), (839, 342))):
        mid = lerp(root, tip, 0.5)
        out.append((C([root, (mid[0] + 3, mid[1] + 2), tip], step=2), 0.7))
    for pts, w in out:
        draw(pts, w=w, hand=0, lift=0, piece=(200, 400), taper=0.7)
    for r in range(4):
        for c in range(4 - (r == 3)):
            x = 851 + c * 6.2 - r * 1.5 + rng.uniform(-0.6, 0.6)
            y = 423 + r * 7.5 + c * 1.2
            pen.dot(x, y, r=0.8, w=1.0)
    return [pts for pts, _ in out]


# ---------------------------------------------------------------- body outline

def guard_hairs(curve, t0, t1, inside, every=(16, 30), n=(1, 3), length_=(6, 11), w=0.8, back=1.0):
    """Guard hairs breaking the outline: small tufts leaning back from the contour."""
    t = t0 + rng.uniform(0, every[1]) / curve.L
    while t < t1:
        nx, ny, tx, ty = normal_out(curve, t, inside)
        if tx * back < 0:
            tx, ty = -tx, -ty
        for k in range(rng.randint(*n)):
            tt = t + rng.uniform(-3, 3) / curve.L
            p = curve.at(tt)
            L = rng.uniform(*length_)
            a = math.radians(rng.uniform(18, 38))
            ox = nx * math.sin(a) + tx * math.cos(a)
            oy = ny * math.sin(a) + ty * math.cos(a)
            root = (p[0] - nx * 2.5, p[1] - ny * 2.5)
            tip = (p[0] + ox * L, p[1] + oy * L)
            mid = lerp(root, tip, 0.5)
            draw(C([root, (mid[0] + nx * 0.6, mid[1] + ny * 0.6), tip], step=1), w=w, hand=0, lift=0,
                 piece=(200, 400), taper=0.6)
        t += rng.uniform(*every) / curve.L


def body_lines():
    """The outline of head, body and near limbs, and the few inner lines. Returns the
    lines, so the fur can keep clear of them."""
    lines = []
    T = TOPLINE
    lines.append((T.part(0.0, 0.33), 1.9, 0.25, 0.0))
    lines.append((T.part(0.33, 0.62), 2.0, 0.35, 0.08))
    lines.append((T.part(0.62, 1.0), 2.1, 0.35, 0.08))
    lines.append((UNDER.part(0, 1), 2.2, 0.3, 0.04))
    lines.append((FL_FRONT.part(0, 1), 2.0, 0.25, 0.0))
    lines.append((FL_BACK.part(0, 1), 2.1, 0.2, 0.0))
    lines.append((BELLY.part(0, 1), 2.3, 0.35, 0.05))
    lines.append((REAR.part(0, 1), 2.3, 0.3, 0.04))
    lines.append((SHANK.part(0, 1), 2.0, 0.2, 0.0))
    for pts, w, hand, lift in lines:
        draw(pts, w=w, hand=hand, lift=lift, piece=(30, 80))
    inner = []
    inner.append((THIGH.part(0.45, 0.97), 1.15))                       # front of the thigh mass
    inner.append((THIGH.part(0.2, 0.38), 0.9))
    inner.append((C([(690, 575), (695, 560), (703, 546)], step=1), 1.0))   # elbow: the triceps edge
    inner.append((C([(853, 413), (846, 425), (845, 439), (849, 451)], step=1), 0.85))   # whisker pad
    for pts, w in inner:
        draw(pts, w=w, hand=0.25, lift=0.1, taper=0.35)
    guard_hairs(T, 0.36, 0.97, (500, 480), every=(14, 26), n=(1, 3), length_=(6, 12), w=0.8, back=1)
    guard_hairs(BELLY, 0.05, 0.92, (600, 520), every=(20, 34), n=(1, 2), length_=(5, 9), w=0.75, back=1)
    guard_hairs(REAR, 0.1, 0.8, (430, 530), every=(18, 30), n=(1, 2), length_=(5, 9), w=0.75, back=1)
    guard_hairs(UNDER, 0.45, 0.95, (760, 470), every=(18, 28), n=(1, 2), length_=(4, 8), w=0.7, back=-1)
    return [pts for pts, *_ in lines] + [pts for pts, _ in inner]


# ---------------------------------------------------------------- tail

TAIL_C = Curve(C([(356, 506), (322, 517), (290, 535), (261, 561), (239, 593), (227, 628), (229, 659),
                  (245, 679), (273, 690), (311, 695), (352, 695), (393, 690), (430, 683)]))


def tail_r(t):
    return 1.3 + 10.2 * (1 - t) ** 1.35


def draw_tail():
    T = TAIL_C
    ts = np.linspace(0, 1, 400)
    A, B = [], []
    for t in ts:
        p = T.at(t)
        tx, ty = T.tangent(t)
        nx, ny = -ty, tx                      # left of travel (the inside of the J)
        r = tail_r(t)
        A.append((p[0] + nx * r, p[1] + ny * r))
        B.append((p[0] - nx * r, p[1] - ny * r))
    draw(A, w=1.5, hand=0.2, lift=0.03, piece=(40, 90), taper=0.2)
    draw(B, w=2.0, hand=0.2, lift=0.03, piece=(40, 90), taper=0.25)
    draw(ellipse_pts(*T.at(1.0), tail_r(1.0), tail_r(1.0), math.atan2(*reversed(T.tangent(1.0))),
                     -math.pi / 2, math.pi / 2, step=0.4), w=1.1, hand=0, lift=0)
    # a shadow line inside the outer edge of the thick half
    sh = []
    for t in np.linspace(0.05, 0.55, 120):
        p = T.at(t)
        tx, ty = T.tangent(t)
        r = tail_r(t)
        sh.append((p[0] + ty * (r - 3.0), p[1] - tx * (r - 3.0)))
    draw(sh, w=0.75, hand=0.1, lift=0.1, taper=0.4)
    # scale rings: fine regular bands across the tail
    s = 20.0
    while s < T.L - 6:
        t = s / T.L
        p = T.at(t)
        tx, ty = T.tangent(t)
        nx, ny = -ty, tx
        r = tail_r(t)
        bow = 0.22 * r
        a = (p[0] + nx * r * 0.88, p[1] + ny * r * 0.88)
        b = (p[0] - nx * r * 0.93, p[1] - ny * r * 0.93)
        m = (p[0] + tx * bow, p[1] + ty * bow)
        draw(C([a, m, b], step=0.8), w=0.68, hand=0, lift=0)
        s += 6.0
    # sparse short hairs
    s = 30.0
    side = 1
    while s < T.L - 12:
        t = s / T.L
        p = T.at(t)
        tx, ty = T.tangent(t)
        nx, ny = -ty * side, tx * side
        r = tail_r(t)
        root = (p[0] + nx * (r - 0.5), p[1] + ny * (r - 0.5))
        L = rng.uniform(5, 8)
        tip = (root[0] + (nx * 0.55 + tx * 0.85) * L, root[1] + (ny * 0.55 + ty * 0.85) * L)
        draw([root, tip], w=0.62, hand=0, lift=0, taper=0.5)
        side = -side
        s += rng.uniform(22, 36)
    occlude(A + list(reversed(B)))


# ---------------------------------------------------------------- far legs (in shadow)

def far_legs():
    """The far fore- and hind leg, mostly hidden, in shadow: close fur down the limb."""
    # far foreleg: a strip of forearm ahead of the near one, and its hand
    front = C([(752, 548), (750, 578), (748, 605), (748, 628)], step=1.5)
    for base, tip, th in (((757, 636), (774, 640.5), 4.2), ((759, 633.5), (777, 636.5), 4.2),
                          ((757, 631), (773, 631.5), 3.8)):
        occlude(digit(base, tip, thick=th, claw=3.8, w=1.15))
    draw(front, w=1.7, hand=0.2, lift=0)
    draw(C([(748, 628), (753, 630), (759, 631)], step=1), w=1.4, hand=0, lift=0)
    draw(C([(737, 638), (745, 640.5), (757, 641)], step=1), w=1.5, hand=0, lift=0)
    poly = [(700, 540)] + front + [(759, 631), (757, 641), (736, 640)]
    reg = poly_mask(poly) & ~OCC
    limb_fur(reg, [(front, 1.0), ([(735, 560), (733, 600), (735, 632)], 0.8)], (722, 540, 760, 642))
    occlude(poly)
    # far hind leg: the shank under the belly, the foot ahead of the near one
    shank = C([(568, 578), (555, 595), (541, 611), (531, 624)], step=1.5)
    for base, tip, th in (((573, 637), (594, 641), 5.0), ((575, 634.5), (598, 637), 5.0),
                          ((572, 632), (591, 632.5), 4.4)):
        occlude(digit(base, tip, thick=th, claw=4.4, w=1.2))
    draw(shank, w=1.7, hand=0.2, lift=0)
    draw(C([(531, 624), (550, 629.5), (569, 633)], step=1), w=1.4, hand=0, lift=0)
    draw(C([(520, 641), (548, 642), (572, 641)], step=1), w=1.5, hand=0, lift=0)
    poly = [(505, 572)] + shank + [(569, 633), (572, 641), (500, 642)]
    reg = poly_mask(poly) & ~OCC
    limb_fur(reg, [(shank, 1.0), ([(530, 580), (515, 600), (505, 625)], 0.8)], (495, 570, 575, 642))
    occlude(poly)


def limb_fur(reg, guides, box):
    D = np.full(GXX.shape, 0.95)
    fur(reg, Field(guides), D, box, seedstep=4)


# ---------------------------------------------------------------- ground

def ground():
    for k, (x0, x1) in enumerate([(440, 770), (480, 735), (530, 690)]):
        y = GROUND + 4 + k * 6
        draw([(x0 + rng.uniform(-6, 6), y), (x1 + rng.uniform(-6, 6), y + rng.uniform(-0.4, 0.4))],
             w=0.8, hand=0.4, lift=0.15, taper=0.5)
    draw(C([(790, GROUND + 1.5), (850, GROUND + 1.5), (900, GROUND + 2)]), w=1.0, hand=0.6, lift=0.25, taper=0.4)
    draw(C([(130, GROUND + 2), (170, GROUND + 1.5), (212, GROUND + 1.5)]), w=1.0, hand=0.6, lift=0.25, taper=0.4)


# ---------------------------------------------------------------- drawing

def main():
    draw_eye()
    draw_ear()
    draw_snout()
    wl = whiskers()
    near_hand()
    near_foot()
    lines = body_lines()

    # --- fur tone
    dtop = dmap(TOPLINE.pts())
    dund = dmap(UNDER.pts() + FL_FRONT.pts())
    dbel = dmap(BELLY.pts())
    drear = dmap(REAR.pts())
    dthigh = dmap(THIGH.pts())
    D = 0.40 + 0.52 * np.exp(-dtop / 70.0)                           # dark along the back
    D = D - 0.42 * np.exp(-((dtop - 5.0) / 3.5) ** 2)                 # a lit rim along the back
    D = D - 0.35 * np.exp(-dbel / 22.0) * (GXX < 700)                # pale belly
    D = D - 0.38 * blob(470, 465, 34)                                # haunch lit on its upper front
    D = D + 0.30 * np.exp(-drear / 22.0) * (GYY > 470)               # dark behind and below
    D = D + 0.22 * np.exp(-dthigh / 12.0) * (GXX > THIGH.at(0.5)[0] - 4) * (GYY > 460)   # flank fold
    D = D - 0.30 * blob(705, 455, 26)                                # point of the shoulder lit
    D = D + 0.22 * blob(645, 505, 30)                                # dark behind it
    D = D + 0.20 * blob(692, 585, 12)                                # behind the elbow
    head = GXX > 715
    D = np.where(head, D - 0.22 * blob(797, 440, 26) - 0.35 * np.clip((GXX - 822) / 40.0, 0, 1), D)
    deye = np.hypot(GXX - EYE[0], GYY - EYE[1])
    D = D + 0.35 * np.exp(-((deye - 13) / 4.0) ** 2)
    D[np.minimum(np.minimum(dtop, dund), np.minimum(dbel, drear)) < 3.2] = -1

    region = poly_mask(body_poly()) & ~OCC & ~halo(lines, 2.6) & ~halo(wl, 1.2)
    field = Field([
        (TOPLINE.part(0.25, 1.0), 1.0),
        (TOPLINE.part(0.0, 0.3), 0.6),
        (UNDER.pts(), 0.7),
        (BELLY.pts(), 0.9),
        (FL_FRONT.pts(), 0.9),
        (FL_BACK.part(0.3, 1.0), 0.9),
        (REAR.pts(), 1.0),
        (SHANK.pts(), 0.9),
        # over the shoulder and down the foreleg
        (C([(705, 412), (692, 440), (686, 480), (690, 520), (700, 560)]), 0.7),
        # the barrel: hair sweeping back and a little down the flank
        (C([(640, 432), (600, 444), (560, 458), (530, 472)]), 0.6),
        (C([(660, 520), (620, 538), (580, 550), (545, 558)]), 0.5),
        # the haunch: arcs about the hip
        (C([(545, 425), (500, 418), (455, 420), (418, 435), (392, 462), (382, 495), (386, 530),
            (400, 565), (420, 595), (445, 615)]), 1.0),
        (C([(515, 465), (485, 460), (458, 470), (440, 495), (436, 525), (446, 558), (465, 588),
            (480, 605)]), 0.9),
        (THIGH.pts(), 0.8),
        # head: back from the nose, over the crown, down the cheek to the throat
        (C([(872, 425), (850, 420), (825, 418), (800, 420), (775, 428), (750, 440)]), 0.7),
        (C([(860, 408), (835, 400), (810, 393), (785, 388), (760, 388)]), 0.6),
        (C([(840, 458), (815, 465), (790, 476), (770, 492), (758, 510)]), 0.6),
        (C([(765, 400), (770, 430), (772, 460), (768, 490)]), 0.4),
    ])
    nfur = fur(region, field, D, (340, 360, 890, 640))
    occlude(body_poly())

    draw_tail()
    for k in range(5):
        p = TAIL_C.at(0.02)
        q = (p[0] - 9 + rng.uniform(-1, 1), p[1] + (k - 2) * 3.5)
        draw([(p[0] + 2, p[1] + (k - 2) * 3.8), q], w=0.75, hand=0, lift=0, taper=0.5, clip=False)

    far_legs()
    ground()

    print('fur strokes', nfur)
    pen.save('../17-rat.svg', mirror=True)
    pen.report()


if __name__ == '__main__':
    main()
