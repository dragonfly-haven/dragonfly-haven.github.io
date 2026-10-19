#!/usr/bin/env python3
"""06 Endosymbiosis: an Asgard archaeon taking in an alphaproteobacterium.

The origin of mitochondria as a clean textbook figure in ink (reworked for
Maxim's note "a bit cleaner, more technical, less messy", then after review).

- The host: an Asgard archaeon (like Prometheoarchaeum), a roundish cell drawn
  as a ball with one side sliced off by a tilted plane, lit from the upper left.
- The cut face: light, staggered section hatching (13 apart, as on 07's cut
  faces), thinning toward the light; the cell envelope as a firm edge with a
  thin line just inside; the circular chromosome as one strand folded into
  seven twisted-pair loops radiating from a small centre (a nucleoid, with no
  outer ring that could read as a nucleus), broken where a strand passes under;
  ribosomes as small dots in loose clusters.
- On the face, one alphaproteobacterium already taken in, cut through: outer
  and inner membrane as two clean lines, a thin broken host membrane round it,
  its own small circular genome (one loop, twisted twice) and a few ribosomes.
- The rest of the ball, on the shadow side, shaded with latitude rings about a
  pole just behind the lower right limb (they shrink and close up toward it),
  every ring in the shadow and every second or fourth into the half-tones, never
  closer than 5; a short slanting second set deepens the core shadow.
- The moment of uptake, on that shadow side: a rod goes in end-first through a
  shaded dimple, rising toward the eye and over the limb. Two tapering membrane
  lobes of the host rise round it: the near one in front, wrapping the rod's
  face (its free edge drawn with a thickness line, its underside hatched along
  its form), the far one behind; both end in rounded tips resting on the rod.
- Long, thin, smooth protrusions (two branching once) curve out from the back
  surface.
- Two free bacteria, each with a single polar flagellum: gram-negative rods with
  an inner line for the inner membrane and body lines that follow the outline,
  close on the shadow side.

Lines are steady (low hand wobble, no pen lifts on contours) and heavier on
the side turned from the light; everything is deterministic. Not mirrored
(slot 06). Run from this folder:
    python3 06-endosymbiosis.py
"""

import math
import random

from pen import Pen, bezier, catmull, ellipse_pts, resample, dist, length

OUT = '../06-endosymbiosis.svg'
SEED = 606
pen = Pen(seed=SEED)
rng = random.Random(SEED)

HAND = 0.25                      # steady, technical line
LIGHT = (-0.72, -0.69)           # toward the light (upper left), in the picture plane
_l = math.hypot(*LIGHT)
LIGHT = (LIGHT[0] / _l, LIGHT[1] / _l)
LIGHT3 = (LIGHT[0] * 0.75, LIGHT[1] * 0.75, 0.66)   # ...and a little from the front

W_HATCH = 0.75


# ---------------------------------------------------------------- helpers

def ink(pts, w, hand=HAND, lift=0.0, piece=(60, 140), taper=0.0):
    if len(pts) >= 2 and length(pts) > 1.0:
        pen.line(pts, w=w, hand=hand, lift=lift, piece=piece, taper=taper, occlude=False)


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def normals(pts):
    """Left normals (t_y, -t_x) along a polyline."""
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = unit((b[0] - a[0], b[1] - a[1]))
        out.append((t[1], -t[0]))
    return out


def area_sign(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return 1 if a > 0 else -1


def runs(pts, hide, step=1.0, minlen=2.5):
    """The parts of a polyline where hide(p) is false."""
    fine = resample(pts, step)
    out, cur = [], []
    for p in fine:
        if hide(p):
            if len(cur) > 1:
                out.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        out.append(cur)
    return [r for r in out if length(r) >= minlen]


def lit_weight(n, w_lit, w_dark):
    """Heavier where the outward normal n turns from the light."""
    d = -(n[0] * LIGHT[0] + n[1] * LIGHT[1])
    t = max(0.0, min(1.0, (d + 0.35) / 1.1))
    return w_lit + (w_dark - w_lit) * t


def ink_outline(pts, hide, w_lit, w_dark, sign=None, chunk=24, hand=HAND, wmul=None, minlen=2.5):
    """A contour whose weight follows the light: heavier on the shadow side.
    sign: +1 if the left normal of travel points outward (default: from the
    polygon's orientation, treating pts as closed)."""
    if sign is None:
        sign = area_sign(pts)
    fine = resample(pts, 1.0)
    nrm = [(n[0] * sign, n[1] * sign) for n in normals(fine)]
    vis = [not hide(p) for p in fine]
    i = 0
    N = len(fine)
    while i < N:
        if not vis[i]:
            i += 1
            continue
        j = i
        while j < N and vis[j]:
            j += 1
        seg = list(range(i, j))
        if len(seg) > 2 and length([fine[k] for k in seg]) >= minlen:
            for a in range(0, len(seg) - 1, chunk):
                ids = seg[a:a + chunk + 1]
                if len(ids) < 2:
                    continue
                nx = sum(nrm[k][0] for k in ids) / len(ids)
                ny = sum(nrm[k][1] for k in ids) / len(ids)
                w = lit_weight(unit((nx, ny)), w_lit, w_dark)
                if wmul:
                    w *= wmul(fine[ids[len(ids) // 2]])
                ink([fine[k] for k in ids], w, hand=hand)
        i = j


def inside_poly(p, poly):
    x, y = p
    hit = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            if x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                hit = not hit
    return hit


class Region:
    """A polygon with a bounding box, for fast inside tests."""

    def __init__(self, poly):
        self.poly = poly
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        self.box = (min(xs), max(xs), min(ys), max(ys))

    def __contains__(self, p):
        x0, x1, y0, y1 = self.box
        if p[0] < x0 or p[0] > x1 or p[1] < y0 or p[1] > y1:
            return False
        return inside_poly(p, self.poly)


def seg_cross(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return t, u
    return None


# ---------------------------------------------------------------- the host: a ball with one side sliced off

C = (452.0, 540.0)
R = 300.0
TILT = math.radians(35)          # the cut face's normal, tilted this far from the eye
U_ANG = math.radians(200)        # ...toward this screen direction (left, a little up)
D_CUT = 0.30 * R                 # the cut lies this far in front of the centre
U = (math.cos(U_ANG), math.sin(U_ANG))
E1 = (-U[1], U[0])
SIN_T, COS_T = math.sin(TILT), math.cos(TILT)
R_FACE = math.sqrt(R * R - D_CUT * D_CUT)
FC = (C[0] + D_CUT * SIN_T * U[0], C[1] + D_CUT * SIN_T * U[1])   # the face's centre on screen
# plane coordinates on the cut face: X to the right (foreshortened), Y down
PX = (-U[0] * COS_T, -U[1] * COS_T)
PY = (-E1[0], -E1[1])
if PY[1] < 0:
    PY = (-PY[0], -PY[1])


def plane(X, Y):
    return (FC[0] + X * PX[0] + Y * PY[0], FC[1] + X * PX[1] + Y * PY[1])


def plane_inv(p):
    dx, dy = p[0] - FC[0], p[1] - FC[1]
    X = (dx * PX[0] + dy * PX[1]) / (COS_T * COS_T)
    Y = dx * PY[0] + dy * PY[1]
    return X, Y


def classify(p):
    """'shell' (the outer surface, seen), 'face' (the cut), or None (off the cell)."""
    dx, dy = p[0] - C[0], p[1] - C[1]
    r2 = dx * dx + dy * dy
    if r2 >= R * R:
        return None
    z = math.sqrt(R * R - r2)
    pu = dx * U[0] + dy * U[1]
    if SIN_T * pu + COS_T * z < D_CUT:
        return 'shell'
    if SIN_T * pu - COS_T * z < D_CUT:
        return 'face'
    return None


def in_host(p):
    return classify(p) is not None


def host_reach(phi):
    d = (math.cos(phi), math.sin(phi))
    lo, hi = 0.0, R + 1
    for _ in range(30):
        mid = (lo + hi) / 2
        if in_host((C[0] + d[0] * mid, C[1] + d[1] * mid)):
            lo = mid
        else:
            hi = mid
    return lo


def from_host(deg, out):
    """A point `out` units outside the host's visible edge (negative: inside) at angle deg."""
    a = math.radians(deg)
    rr = host_reach(a) + out
    return (C[0] + rr * math.cos(a), C[1] + rr * math.sin(a))


# ---------------------------------------------------------------- shapes

def capsule_pts(cx, cy, ang, hl, r, step=2.0):
    """A capsule (rod with round ends) outline, closed."""
    a = (math.cos(ang), math.sin(ang))
    e_p = (cx + a[0] * hl, cy + a[1] * hl)
    e_m = (cx - a[0] * hl, cy - a[1] * hl)
    pts = []
    pts += ellipse_pts(e_p[0], e_p[1], r, r, 0, ang - math.pi / 2, ang + math.pi / 2, step=step)
    pts += ellipse_pts(e_m[0], e_m[1], r, r, 0, ang + math.pi / 2, ang + 3 * math.pi / 2, step=step)
    pts.append(pts[0])
    return resample(pts, step)


def capsule_normal(cx, cy, ang, hl, p):
    a = (math.cos(ang), math.sin(ang))
    t = (p[0] - cx) * a[0] + (p[1] - cy) * a[1]
    t = max(-hl, min(hl, t))
    q = (cx + a[0] * t, cy + a[1] * t)
    return unit((p[0] - q[0], p[1] - q[1]))


def break_crossings(pts, depth, gap=3.6):
    """A closed strand as runs, broken where it passes under itself (lower depth)."""
    sl = [0.0]
    for i in range(1, len(pts)):
        sl.append(sl[-1] + dist(pts[i - 1], pts[i]))
    cell = 8.0
    grid = {}
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for gx in range(int(min(a[0], b[0]) // cell), int(max(a[0], b[0]) // cell) + 1):
            for gy in range(int(min(a[1], b[1]) // cell), int(max(a[1], b[1]) // cell) + 1):
                grid.setdefault((gx, gy), []).append(i)
    cuts = []
    seen = set()
    for segs in grid.values():
        for ii in range(len(segs)):
            for jj in range(ii + 1, len(segs)):
                i, j = segs[ii], segs[jj]
                if abs(i - j) < 3 or abs(i - j) > len(pts) - 4 or (i, j) in seen:
                    continue
                seen.add((i, j))
                hit = seg_cross(pts[i], pts[i + 1], pts[j], pts[j + 1])
                if hit:
                    si = sl[i] + hit[0] * (sl[i + 1] - sl[i])
                    sj = sl[j] + hit[1] * (sl[j + 1] - sl[j])
                    cuts.append(si if depth[i] < depth[j] else sj)
    out, cur = [], []
    for i, p in enumerate(pts):
        if any(abs(sl[i] - u) < gap for u in cuts):
            if len(cur) > 1:
                out.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        out.append(cur)
    if len(out) > 1 and dist(out[-1][-1], out[0][0]) < 2.0:
        out[0] = out[-1] + out[0][1:]
        out.pop()
    return out


class Tube:
    """A protrusion: a smooth tube along a centre line, tapering, round-tipped,
    flaring a little where it leaves the cell."""

    def __init__(self, centre, w0, w1, flare=5.0, flare_len=12.0, step=1.5, cap=True, s_from=0.0, L_total=None):
        c = resample(centre, step)
        nn = normals(c)
        sl = [0.0]
        for i in range(1, len(c)):
            sl.append(sl[-1] + dist(c[i - 1], c[i]))
        L = L_total or sl[-1]
        self.c, self.nn, self.sl, self.L = c, nn, sl, sl[-1]
        self.h = [(w0 + (w1 - w0) * (s + s_from) / L) / 2 + flare * math.exp(-(s + s_from) / flare_len) for s in sl]
        self.left = [(p[0] + n[0] * h, p[1] + n[1] * h) for p, n, h in zip(c, nn, self.h)]
        self.right = [(p[0] - n[0] * h, p[1] - n[1] * h) for p, n, h in zip(c, nn, self.h)]
        if cap:
            e, n, he = c[-1], nn[-1], self.h[-1]
            a_l = math.atan2(n[1], n[0])
            a_t = math.atan2(c[-1][1] - c[-2][1], c[-1][0] - c[-2][0])
            sweep = math.pi if math.cos(a_l + math.pi / 2 - a_t) > 0 else -math.pi
            tip = ellipse_pts(e[0], e[1], he, he, 0, a_l, a_l + sweep, step=1.0)
            self.outline = [self.left + tip[1:-1] + self.right[::-1]]
            self.region = Region(self.left + tip[1:-1] + self.right[::-1])
        else:
            self.outline = [self.left, self.right[::-1]]
            self.region = Region(self.left + self.right[::-1])

    def at(self, frac):
        i = int((len(self.c) - 1) * frac)
        a, b = self.c[max(0, i - 2)], self.c[min(len(self.c) - 1, i + 2)]
        return self.c[i], math.atan2(b[1] - a[1], b[0] - a[0])


def bez_centre(p0, a0, l0, p3, a3, l3, wave=0.0, waves=1.0):
    """A smooth centre line leaving p0 at angle a0 and arriving at p3 heading a3
    (degrees), with an optional gentle sideways wave that grows from the base."""
    p1 = (p0[0] + l0 * math.cos(math.radians(a0)), p0[1] + l0 * math.sin(math.radians(a0)))
    p2 = (p3[0] - l3 * math.cos(math.radians(a3)), p3[1] - l3 * math.sin(math.radians(a3)))
    pts = resample(bezier(p0, p1, p2, p3, step=1.0), 1.0)
    if not wave:
        return pts
    nn = normals(pts)
    n = len(pts)
    out = []
    for i, (p, nv) in enumerate(zip(pts, nn)):
        u = i / (n - 1)
        o = wave * math.sin(math.pi * waves * u) * min(1.0, u * 4)
        out.append((p[0] + nv[0] * o, p[1] + nv[1] * o))
    return out


def sprout(deg, p3, a3, l0=90, l3=90, w0=9.5, w1=5.5, wave=0.0, waves=1.0):
    p0 = from_host(deg, -14)
    return Tube(bez_centre(p0, deg, l0, p3, a3, l3, wave, waves), w0, w1, flare=4.5, flare_len=10.0)


def branch(parent, frac, turn, p3, a3, l0=50, l3=50, w0=7.5, w1=5.0, wave=0.0):
    p0, a = parent.at(frac)
    a0 = math.degrees(a) + turn
    return Tube(bez_centre(p0, a0, l0, p3, a3, l3, wave), w0, w1, flare=2.0, flare_len=8.0)




# ================================================================ small 3D helpers

def v_norm(v):
    L = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / L for c in v)


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def lam3(n):
    """Lambert term for a unit normal (x right, y down, z toward the eye)."""
    return v_dot(n, LIGHT3)


def surf(p):
    """The host's front surface under screen point p, relative to the centre."""
    dx, dy = p[0] - C[0], p[1] - C[1]
    return (dx, dy, math.sqrt(max(0.0, R * R - dx * dx - dy * dy)))


class Grid:
    """Points already inked, to keep new hatching at least a set distance away."""

    def __init__(self, cell=6.0):
        self.cell, self.g = cell, {}

    def add(self, pts):
        for p in pts:
            self.g.setdefault((int(p[0] // self.cell), int(p[1] // self.cell)), []).append(p)

    def near(self, p, d):
        gx, gy = int(p[0] // self.cell), int(p[1] // self.cell)
        k = int(d // self.cell) + 1
        for i in range(gx - k, gx + k + 1):
            for j in range(gy - k, gy + k + 1):
                for q in self.g.get((i, j), ()):
                    if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < d * d:
                        return True
        return False


def ink_hatch(pts, hide, w=W_HATCH, minlen=8, trim=4, grid=None):
    """A hatching line: trimmed a little at both ends, broken where hidden."""
    if len(pts) < 2 or length(pts) < minlen:
        return
    pts = resample(pts, 1.0)
    cut = min(len(pts) // 6, trim)
    pts = pts[cut:len(pts) - cut] if cut else pts
    for run in runs(pts, hide, minlen=minlen):
        ink(run, w, hand=0.12, piece=(80, 160))
        if grid is not None:
            grid.add(run)


def split_none(pts):
    """Runs of consecutive non-None points."""
    out, cur = [], []
    for q in pts + [None]:
        if q is None:
            if len(cur) > 1:
                out.append(cur)
            cur = []
        else:
            cur.append(q)
    return out


# ================================================================ layout

ROD_HL, ROD_R = 86.0, 38.0       # the bacteria, all alike (rods about 250 long)
LIGHT_ROD = v_norm((LIGHT[0], LIGHT[1], 0.25))   # for the rods' body lines: more raking
MEMB = 6.5                       # outer to inner membrane of a bacterium

# ---- the bacterium being taken in: it goes in end-first through a dimple on the
# host's shadow side, rising toward the eye and to the upper right
E = (C[0] + 236.0 * math.cos(math.radians(10)), C[1] + 236.0 * math.sin(math.radians(10)))
N_E = v_norm(surf(E))                                   # surface normal at the entry
A3 = v_norm((N_E[0] + 0.30, N_E[1] - 0.78, N_E[2] - 0.22))   # the rod's axis, outward
KXY = math.hypot(A3[0], A3[1])                          # its foreshortening
DIR2 = (A3[0] / KXY, A3[1] / KXY)
RN = (-DIR2[1], DIR2[0])                                # across the rod, toward the lower right
RA = math.atan2(DIR2[1], DIR2[0])
SINK = 44.0                                             # how far its inner end is in
_off = (ROD_HL + ROD_R - SINK) * KXY
RC = (E[0] + DIR2[0] * _off, E[1] + DIR2[1] * _off)
HLP = ROD_HL * KXY                                      # projected half-length
T_E = -_off                                             # the entry, along the rod
T_CUT = T_E + 6.0                                       # where it meets the dimple's floor
BULGE = ROD_R * A3[2]                                   # the cut circle's half-width on screen


def rod_pt(t, o):
    return (RC[0] + DIR2[0] * t + RN[0] * o, RC[1] + DIR2[1] * t + RN[1] * o)


def rod_to(p):
    dx, dy = p[0] - RC[0], p[1] - RC[1]
    return dx * DIR2[0] + dy * DIR2[1], dx * RN[0] + dy * RN[1]


def sunk(p):
    """Below where the rod meets the dimple's floor (hidden)."""
    t, o = rod_to(p)
    u = max(-1.0, min(1.0, o / ROD_R))
    return t < T_CUT - BULGE * math.sqrt(1 - u * u)


# the dimple: a circle of the sphere round the entry, 62 across... in 3D
_rho = 78.0 / R
_t1 = v_norm(v_cross(N_E, (0.0, 0.0, 1.0)))
_t2 = v_cross(N_E, _t1)


def dimple_ring(scale, shift=(0.0, 0.0), n=360):
    g = _rho * scale
    out = []
    for i in range(n + 1):
        f = 2 * math.pi * i / n
        p = [R * (math.cos(g) * N_E[k] + math.sin(g) * (math.cos(f) * _t1[k] + math.sin(f) * _t2[k])) for k in range(3)]
        out.append((C[0] + p[0] + shift[0], C[1] + p[1] + shift[1]))
    return out


DIMPLE = dimple_ring(1.0)
DIMPLE_REG = Region(DIMPLE[:-1])


def lobe(ctrl_out, tip_t, tip_o, ctrl_in, tip_r):
    """A membrane lobe as a closed outline (rod coordinates in, screen points out):
    the outer edge to the tip, a round tip, and the free edge back."""
    out_e = [rod_pt(t, o) for t, o in resample(catmull(ctrl_out, step=1.0), 1.0)]
    in_e = [rod_pt(t, o) for t, o in resample(catmull(ctrl_in, step=1.0), 1.0)]
    tc = rod_pt(tip_t, tip_o)
    a0 = math.atan2(out_e[-1][1] - tc[1], out_e[-1][0] - tc[0])
    a1 = math.atan2(in_e[0][1] - tc[1], in_e[0][0] - tc[0])
    # sweep through the side facing along the rod
    da = (a1 - a0) % (2 * math.pi)
    mid = a0 + da / 2
    if math.cos(mid - RA) < 0:
        da -= 2 * math.pi
    tip = ellipse_pts(tc[0], tc[1], tip_r, tip_r, 0, a0, a0 + da, step=1.0)
    return out_e, tip, in_e


# near lobe: in front, along the rod's lower side, wrapping over its face
NL_OUT = [(T_E - 8, 62), (T_E + 22, 58), (T_E + 62, 51), (T_E + 104, 44), (T_E + 134, 39)]
NL_IN = [(T_E + 134, 21), (T_E + 104, 18), (T_E + 62, 10), (T_E + 24, 0), (T_E - 2, -8)]
nl_out, nl_tip, nl_in = lobe(NL_OUT, T_E + 135, 30, NL_IN, 9.0)
NEAR = Region(nl_out + nl_tip[1:-1] + nl_in)
# far lobe: behind, along the rod's upper side; only its outer edge and tip show
FL_OUT = [(T_E - 4, -64), (T_E + 24, -68), (T_E + 58, -63), (T_E + 92, -53)]
FL_IN = [(T_E + 92, -30), (T_E + 58, -26), (T_E + 24, -24), (T_E - 4, -30)]
fl_out, fl_tip, fl_in = lobe(FL_OUT, T_E + 94, -42, FL_IN, 11.0)
FAR = Region(fl_out + fl_tip[1:-1] + fl_in)
ROD_REG = Region(capsule_pts(RC[0], RC[1], RA, HLP, ROD_R, step=2.0))


def eng_hide(p):
    """Inside the engulfment (rod, lobes, dimple): host lines stay out."""
    return p in NEAR or (p in ROD_REG and not sunk(p)) or p in FAR or p in DIMPLE_REG


# ---- protrusions: long, thin, smooth, two branching once
p_top = sprout(-80, (598, 70), -62, l0=90, l3=80, wave=5, waves=1.2)
p_left = sprout(194, (46, 318), 262, l0=130, l3=110, wave=5, waves=1.2)
p_left_b = branch(p_left, 0.5, -20, (50, 566), 105, l0=50, l3=60)
p_ll = sprout(146, (62, 846), 170, l0=110, l3=120, wave=-5, waves=1.2)
p_bot = sprout(98, (636, 972), 4, l0=90, l3=140, wave=5, waves=1.2)
p_lr = sprout(52, (950, 846), 20, l0=110, l3=90, wave=-5, waves=1.2)
p_lr_b = branch(p_lr, 0.5, 26, (880, 960), 80, l0=40, l3=50)

groups = [[p_top], [p_left, p_left_b], [p_ll], [p_bot], [p_lr, p_lr_b]]
all_tubes = [t for g in groups for t in g]


def tube_hide(p):
    return any(p in t.region for t in all_tubes)


# ================================================================ drawing

# ---- protrusions
for g in groups:
    for t in g:
        others = [o for o in g if o is not t]

        def hide(p, others=others):
            return in_host(p) or any(p in o.region for o in others)

        for ol in t.outline:
            ink_outline(ol, hide, 1.1, 2.1, sign=1)


# ---- the bacteria

def rod(cx, cy, ang, hl, r, hide=lambda p: False, flag=None, outline=True):
    """A rod-shaped, gram-negative bacterium seen whole: a firm outline heavier on
    the shadow side, a thin inner line for its inner membrane, and body lines
    that follow its outline, close on the shadow side and thinning out toward the light."""
    if outline:
        ink_outline(capsule_pts(cx, cy, ang, hl, r, step=1.5), hide, 1.5, 2.5, sign=1)
    for run in runs(capsule_pts(cx, cy, ang, hl, r - MEMB, step=1.5), hide, minlen=6):
        ink(run, 0.9, hand=0.12)
    for k in range(1, 9):
        rk = r - MEMB - 5.6 * k
        if rk < 4:
            break
        d = rk / r
        nz = math.sqrt(1 - d * d)
        lim = 0.16
        if k % 2 == 1:
            lim = 0.40
        if k % 4 == 1:
            lim = 0.62
        line = capsule_pts(cx, cy, ang, hl, rk, step=1.0)
        pts = []
        for p in line:
            m = capsule_normal(cx, cy, ang, hl, p)
            pts.append(p if v_dot((d * m[0], d * m[1], nz), LIGHT_ROD) < lim else None)
        # rotate so a run does not wrap past the start
        if None in pts and pts[0] is not None:
            i0 = pts.index(None)
            pts = pts[i0:] + pts[1:i0 + 1]
        for sgm in split_none(pts):
            ink_hatch(sgm, hide, minlen=10, trim=5)
    if flag:
        end, ln, wave, amp, bend = flag
        a = (math.cos(ang), math.sin(ang))
        pole = (cx + end * a[0] * (hl + r - 1.5), cy + end * a[1] * (hl + r - 1.5))
        d0 = math.atan2(end * a[1], end * a[0])
        pts = []
        s = 0.0
        x, y = pole
        n_steps = int(ln)
        for i in range(n_steps + 1):
            dirn = d0 + bend * (i / n_steps)
            ramp = min(1.0, s / 30.0)
            nx, ny = -math.sin(dirn), math.cos(dirn)
            o = amp * ramp * math.sin(2 * math.pi * s / wave)
            pts.append((x + nx * o, y + ny * o))
            x += math.cos(dirn)
            y += math.sin(dirn)
            s += 1.0
        ink(pts, 1.3, hand=0.0, taper=0.4)


# ---- the engulfment, front to back

# near lobe: outline (heavier below), a thickness line along its free edge,
# and its underside hatched along its form
nl_line = nl_out + nl_tip[1:-1] + nl_in
ink_outline(nl_line, lambda p: False, 1.3, 2.3, sign=area_sign(nl_line + [nl_out[0]]) * 1)
thick = [rod_pt(t, o + 4.0) for t, o in resample(catmull(NL_IN, step=1.0), 1.0)]
for run in runs(thick[6:-10], lambda p: p not in NEAR):
    ink(run, 0.9, hand=0.12)
for k in range(1, 4):
    band = [(t, o - 5.2 * k) for t, o in NL_OUT[:-1]] + [(NL_OUT[-1][0] - 8 * k, NL_OUT[-1][1] - 5.2 * k)]
    pts = [rod_pt(t, o) for t, o in resample(catmull(band, step=1.0), 1.0)]
    ink_hatch(pts, lambda p: p not in NEAR, minlen=10, trim=3 + 4 * k)

# the rod itself, behind the near lobe, its inner end gone into the dimple
rod_hide = lambda p: p in NEAR or sunk(p)
rod(RC[0], RC[1], RA, HLP, ROD_R, hide=rod_hide)
# where it meets the dimple's floor: the near half of the cut circle
cut = []
for i in range(91):
    u = -1 + 2 * i / 90
    cut.append(rod_pt(T_CUT - BULGE * math.sqrt(1 - u * u), ROD_R * u))
for run in runs(cut, lambda p: p in NEAR):
    ink(run, 1.5)

# far lobe: behind the rod, its outer edge and tip; hatched along its form near the rod
fl_line = fl_out + fl_tip[1:-1]
far_hide = lambda p: p in ROD_REG and not sunk(p)
ink_outline(fl_line, far_hide, 1.2, 2.0, sign=area_sign(fl_line + fl_in))
for k in range(1, 3):
    band = [(t, o + 5.2 * k) for t, o in FL_OUT]
    pts = [rod_pt(t, o) for t, o in resample(catmull(band, step=1.0), 1.0)]
    ink_hatch(pts, lambda p: far_hide(p) or p not in FAR, minlen=10, trim=4 + 5 * k)

# the dimple: its rim, and its inner wall shaded where it turns from the light
eng_front = lambda p: p in NEAR or p in FAR or (p in ROD_REG and not sunk(p))
ink_outline(DIMPLE, eng_front, 1.0, 1.6, sign=area_sign(DIMPLE[:-1]))
_dc = (sum(p[0] for p in DIMPLE) / len(DIMPLE), sum(p[1] for p in DIMPLE) / len(DIMPLE))
for k in range(1, 6):
    s = 1.0 - 0.09 * k
    ring = [(_dc[0] + (p[0] - _dc[0]) * s + 2.2 * k * -LIGHT[0], _dc[1] + (p[1] - _dc[1]) * s + 2.2 * k * -LIGHT[1]) for p in DIMPLE]
    pts = []
    for p in ring:
        v = unit((p[0] - _dc[0], p[1] - _dc[1]))
        # the wall on the far side of the hollow from the light is lit; the near side is in shade
        shade = v[0] * LIGHT[0] + v[1] * LIGHT[1]
        pts.append(p if shade > -0.2 + 0.12 * k else None)
    if None in pts and pts[0] is not None:
        i0 = pts.index(None)
        pts = pts[i0:] + pts[1:i0 + 1]
    for sgm in split_none(pts):
        ink_hatch(sgm, eng_front, minlen=8, trim=3)

# ---- free bacteria
rod(242, 188, math.radians(30), ROD_HL, ROD_R, hide=tube_hide,
    flag=(-1, 118, 50, 9.0, math.radians(-60)))
rod(808, 196, math.radians(152), ROD_HL, ROD_R, hide=tube_hide,
    flag=(-1, 104, 50, 9.0, math.radians(-70)))

# ---- the host's outline: the cut face's edge and the shell's limb


def face_pt(rr, phi):
    """A point on a circle of radius rr on the cut face."""
    return plane(rr * math.cos(phi), rr * math.sin(phi))


def face_z(phi, rr=R_FACE):
    """Depth (toward the eye) of the face's edge at angle phi: the face's X axis
    climbs toward the eye by sin(TILT) per unit, its Y axis lies flat."""
    return D_CUT * COS_T + rr * math.cos(phi) * SIN_T


def crease(p):
    """The face's edge is lighter where it is an inner edge (against the shell)."""
    X, Y = plane_inv(p)
    return 0.7 if face_z(math.atan2(Y, X)) > 0 else 1.0


host_hide = lambda p: tube_hide(p) or eng_hide(p)
ink_outline([face_pt(R_FACE, 2 * math.pi * i / 1200) for i in range(1201)], host_hide, 1.75, 2.55, wmul=crease)
limb = []
for i in range(1441):
    a = 2 * math.pi * i / 1440
    p = (C[0] + R * math.cos(a), C[1] + R * math.sin(a))
    pu = (p[0] - C[0]) * U[0] + (p[1] - C[1]) * U[1]
    limb.append(p if SIN_T * pu < D_CUT - 0.5 else None)
i0 = limb.index(None)
limb = limb[i0:] + limb[1:i0 + 1]
for arc in split_none(limb):
    ink_outline(arc, host_hide, 1.75, 2.55, sign=1)
# the cell envelope in section: a thin line just inside the rim
for run in runs([face_pt(R_FACE - 6.0, 2 * math.pi * i / 1200) for i in range(1201)], host_hide):
    ink(run, 0.8, hand=0.12)

# ---- shading on the shell: latitude rings about an axis whose pole lies just
# behind the lower right limb (they shrink and close up toward it), graded by light
POLE = v_norm((0.40, 0.80, -0.34))
_b1 = v_norm(v_cross(POLE, (0.0, 0.0, 1.0)))
_b2 = v_cross(POLE, _b1)
SHELL_GRID = Grid()


def shell_ok(p):
    return classify(p) == 'shell' and not host_hide(p) and math.hypot(p[0] - C[0], p[1] - C[1]) < R - 3.5


D_BETA = math.radians(2.4)
k = 0
beta = D_BETA * 2
while beta < math.radians(150):
    k += 1
    lim = 0.26
    if k % 2 == 1:
        lim = 0.48
    if k % 4 == 1:
        lim = 0.68
    pts = []
    for i in range(721):
        f = 2 * math.pi * i / 720
        q = [R * (math.cos(beta) * POLE[j] + math.sin(beta) * (math.cos(f) * _b1[j] + math.sin(f) * _b2[j])) for j in range(3)]
        p = (C[0] + q[0], C[1] + q[1])
        ok = q[2] > 2.0 and lam3((q[0] / R, q[1] / R, q[2] / R)) < lim and shell_ok(p)
        pts.append(p if ok else None)
    if None in pts and pts[0] is not None:
        i0 = pts.index(None)
        pts = pts[i0:] + pts[1:i0 + 1]
    drawn = Grid()
    for sgm in split_none(pts):
        ink_hatch(sgm, lambda p: SHELL_GRID.near(p, 5.2), minlen=10, trim=4, grid=drawn)
    for cell in drawn.g.values():
        SHELL_GRID.add(cell)
    beta += D_BETA

# a short second set in the core shadow: arcs of the ball parallel to the cut,
# crossing the latitude rings at a slant
CORE_GRID = Grid()
_nf = (SIN_T * U[0], SIN_T * U[1], COS_T)              # the cut face's normal
_e1 = (E1[0], E1[1], 0.0)
_e2 = v_cross(_nf, _e1)
cc = D_CUT - 30.0
while cc > -R + 20:
    rc = math.sqrt(R * R - cc * cc)
    pts = []
    for i in range(721):
        f = 2 * math.pi * i / 720
        q = [cc * _nf[m] + rc * (math.cos(f) * _e1[m] + math.sin(f) * _e2[m]) for m in range(3)]
        p = (C[0] + q[0], C[1] + q[1])
        ang = math.degrees(math.atan2(q[1], q[0]))
        ok = q[2] > 2.0 and lam3((q[0] / R, q[1] / R, q[2] / R)) < -0.40 and 14 < ang < 80 and shell_ok(p)
        pts.append(p if ok else None)
    if None in pts and pts[0] is not None:
        i0 = pts.index(None)
        pts = pts[i0:] + pts[1:i0 + 1]
    drawn = Grid()
    for sgm in split_none(pts):
        ink_hatch(sgm, lambda p: CORE_GRID.near(p, 5.6), minlen=14, trim=6, grid=drawn, w=0.7)
    for cell in drawn.g.values():
        CORE_GRID.add(cell)
    cc -= 11.0

# ---- inside, on the cut face (plane coordinates)

# the enclosed alphaproteobacterium, cut through: outer and inner membrane, and a
# thin, broken membrane of the host round it
EB = (-78.0, -104.0)
EB_ANG = math.radians(-30)
EB_HL, EB_R = 80.0, 37.0
_a = (math.cos(EB_ANG), math.sin(EB_ANG))
_n = (-_a[1], _a[0])
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R)], 1.7)
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R - 8.5)], 1.1)
vac = [plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R + 9.0, step=1.0)]
_L = len(vac)
for i0, i1 in [(0.02, 0.17), (0.22, 0.41), (0.47, 0.60), (0.66, 0.84), (0.89, 0.98)]:
    ink(vac[int(i0 * _L):int(i1 * _L)], 0.8, hand=0.12)
# its own small circular genome: one loop, twisted twice
_g = []
for i in range(901):
    t = 2 * math.pi * i / 900
    x, y = 44 * math.cos(t), 12 * math.sin(3 * t)
    _g.append((EB[0] + 4 + x * _a[0] - y * _a[1], EB[1] + x * _a[1] + y * _a[0], math.cos(3 * t) * math.sin(t)))
for run in break_crossings([plane(x, y) for x, y, _ in _g], [d for _, _, d in _g], gap=3.2):
    ink(run, 1.15, hand=0.1)
for t, o in [(-66, -6), (-56, 15), (62, -15), (70, 8), (-14, -22), (14, 22), (40, 20)]:
    q = plane(EB[0] + _a[0] * t + _n[0] * o, EB[1] + _a[1] * t + _n[1] * o)
    pen.dot(q[0], q[1], r=2.0, w=1.2)

# the host's chromosome: one circular strand folded into looped domains, each a
# twisted pair of strands radiating from a small centre and ending in a loop
NUC = (64.0, 92.0)
N_PETALS = 7
nuc_pts, nuc_depth = [], []
_rng = random.Random(61)
_angs = [2 * math.pi * k / N_PETALS + math.radians(_rng.uniform(-4, 4)) + 0.3 for k in range(N_PETALS)]
_lens = [2, 3, 2, 2, 3, 2, 3]
CORE = 8.0
PERIOD = 25.0
for k, al in enumerate(_angs):
    d = (math.cos(al), math.sin(al))
    nk = (math.sin(al), -math.cos(al))
    L = PERIOD * _lens[k] + 6
    amp = lambda s: 1.6 + 5.8 * min(1.0, s / 16.0)
    seg_a, seg_b = [], []
    bend = math.radians(_rng.uniform(6, 14)) * (1 if k % 2 else -1)
    for i in range(int(L) + 1):
        s = float(i)
        ab = al + bend * (s / L) ** 1.5
        c = (NUC[0] + d[0] * CORE + math.cos(ab) * s, NUC[1] + d[1] * CORE + math.sin(ab) * s)
        nk = (math.sin(ab), -math.cos(ab))
        grow = 1.0 + 0.7 * max(0.0, (s - (L - 14)) / 14) ** 1.5
        off = (amp(s) * math.cos(2 * math.pi * (s - 6) / PERIOD) if s > 6 else amp(s)) * grow
        dep = math.sin(2 * math.pi * (s - 6) / PERIOD) if s > 6 else 0.0
        seg_a.append(((c[0] + nk[0] * off, c[1] + nk[1] * off), dep))
        seg_b.append(((c[0] - nk[0] * off, c[1] - nk[1] * off), -dep))
    # the loop at the end: round from strand a to strand b
    ea, eb = seg_a[-1][0], seg_b[-1][0]
    mc = ((ea[0] + eb[0]) / 2, (ea[1] + eb[1]) / 2)
    rr = dist(ea, eb) / 2
    a0 = math.atan2(ea[1] - mc[1], ea[0] - mc[0])
    sweep = math.pi if math.cos(a0 + math.pi / 2 - ab) > 0 else -math.pi
    loop = [(q, 0.0) for q in ellipse_pts(mc[0], mc[1], rr, rr, 0, a0, a0 + sweep, step=1.0)[1:-1]]
    petal = seg_a + loop + seg_b[::-1]
    # across the centre to the next petal
    if nuc_pts:
        last = nuc_pts[-1]
        first = petal[0][0]
        for j in range(1, 6):
            u = j / 6
            nuc_pts.append((last[0] + (first[0] - last[0]) * u, last[1] + (first[1] - last[1]) * u))
            nuc_depth.append(0.0)
    for q, dp in petal:
        nuc_pts.append(q)
        nuc_depth.append(dp)
# close the ring
last, first = nuc_pts[-1], nuc_pts[0]
for j in range(1, 6):
    u = j / 6
    nuc_pts.append((last[0] + (first[0] - last[0]) * u, last[1] + (first[1] - last[1]) * u))
    nuc_depth.append(0.0)
nuc_pts.append(first)
nuc_depth.append(0.0)
nuc_screen = [plane(x, y) for x, y in nuc_pts]
for run in break_crossings(nuc_screen, nuc_depth, gap=3.8):
    ink(run, 1.15, hand=0.08)
NUC_GRID = Grid(8.0)
NUC_GRID.add(resample(nuc_screen, 2.0))

# ribosomes: small dots in loose, irregular clusters
_rr = random.Random(606)


def eb_dist(X, Y):
    t = (X - EB[0]) * _a[0] + (Y - EB[1]) * _a[1]
    t = max(-EB_HL, min(EB_HL, t))
    return math.hypot(X - (EB[0] + _a[0] * t), Y - (EB[1] + _a[1] * t))


centres = []
tries = 0
while tries < 4000 and len(centres) < 13:
    tries += 1
    X, Y = _rr.uniform(-R_FACE, R_FACE), _rr.uniform(-R_FACE, R_FACE)
    if X * X + Y * Y > (R_FACE - 40) ** 2 or math.hypot(X - NUC[0], Y - NUC[1]) < 110 or eb_dist(X, Y) < EB_R + 34:
        continue
    if any(math.hypot(X - a, Y - b) < 74 for a, b in centres):
        continue
    centres.append((X, Y))
ribo = []
for X, Y in centres:
    n = _rr.choice([3, 4, 4, 5, 6])
    pts = []
    for _ in range(60):
        if len(pts) >= n:
            break
        a = _rr.uniform(0, 2 * math.pi)
        rr = _rr.uniform(0, 17)
        q = (X + rr * math.cos(a), Y + rr * math.sin(a))
        if all(math.hypot(q[0] - b[0], q[1] - b[1]) > 8 for b in pts):
            pts.append(q)
    ribo += pts
for X, Y in ribo:
    q = plane(X, Y)
    pen.dot(q[0], q[1], r=2.6, w=1.3)

# the cut face: very light, widely spaced section hatching, broken and staggered
# as in 07, kept clear of the chromosome, the bacterium and the dots


def face_clear(p):
    X, Y = plane_inv(p)
    if X * X + Y * Y > (R_FACE - 13) ** 2:
        return True
    if eb_dist(X, Y) < EB_R + 16:
        return True
    if NUC_GRID.near(p, 10.0):
        return True
    if any((X - a) ** 2 + (Y - b) ** 2 < 7.5 ** 2 for a, b in ribo):
        return True
    return host_hide(p)


_hr = random.Random(6060)
Yh = -R_FACE + 9.0
while Yh < R_FACE:
    half = math.sqrt(max(0.0, R_FACE ** 2 - Yh * Yh))
    X = -half + _hr.uniform(0, 40)
    while X < half:
        seg = _hr.uniform(50, 150)
        x1 = min(half, X + seg)
        # lighter toward the light: fewer strokes up and to the left
        mid = plane((X + x1) / 2, Yh)
        u = ((mid[0] - FC[0]) * -LIGHT[0] + (mid[1] - FC[1]) * -LIGHT[1]) / R_FACE
        if x1 - X > 12 and _hr.random() < 0.18 + 0.62 * (u + 1) / 2:
            line = [plane(X, Yh), plane(x1, Yh)]
            for run in runs(line, face_clear, minlen=8):
                ink(run, 0.62, hand=0.1, piece=(80, 160))
        X = x1 + _hr.uniform(16, 44)
    Yh += 13.0

pen.save(OUT)
pen.report()
