#!/usr/bin/env python3
"""06 Endosymbiosis: an Asgard archaeon taking in an alphaproteobacterium.

The origin of mitochondria as a clean textbook figure in ink.

- The host: an Asgard archaeon (like Prometheoarchaeum), a roundish cell drawn
  as a sphere cut through its middle by one tilted plane. The cut face looks
  up and to the left, toward the light, and shows the inside on clean paper:
  the cell membrane as a firm edge with a thin inner line, a circular
  chromosome as one regular supercoiled loop (crossings broken where the
  strand passes under), and ribosomes as small rings scattered evenly.
- Inside, on the cut face, one alphaproteobacterium already taken in, its
  gram-negative envelope cut through: outer and inner membrane as two clean
  parallel lines, its own small looped genome and a few ribosomes inside.
- The rest of the host's surface shows as a crescent on the shadow side,
  shaded with meridians of the sphere that thin out where they converge.
- Long, thin, smooth protrusions (some branching once) curve out from the
  host; two of them cradle a rod-shaped bacterium at the upper right, the
  moment it is being taken in.
- One free bacterium nearby with a single polar flagellum.

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
LIGHT = (-0.42, -0.91)           # toward the light (upper left), in the picture plane
_l = math.hypot(*LIGHT)
LIGHT = (LIGHT[0] / _l, LIGHT[1] / _l)
LIGHT3 = (LIGHT[0] * 0.75, LIGHT[1] * 0.75, 0.66)   # ...and a little from the front

W_HATCH = 0.75
HATCH_GAP = 6.0


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

C = (466.0, 546.0)
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


def coil_ring(cx, cy, ra, rb, rot, r, k, side=0.85, n=2400, map_pt=None, gap=3.6):
    """A closed strand coiled regularly around an oval ring (a helix bent into a
    ring, seen from the side), broken where it passes under itself."""
    pts, depth = [], []
    c, s = math.cos(rot), math.sin(rot)
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        ox, oy = ra * math.cos(t), rb * math.sin(t)
        tx, ty = -ra * math.sin(t), rb * math.cos(t)
        L = math.hypot(tx, ty)
        tx, ty = tx / L, ty / L
        nx, ny = ty, -tx
        ph = k * t
        x = ox + r * side * math.sin(ph) * tx + r * math.cos(ph) * nx
        y = oy + r * side * math.sin(ph) * ty + r * math.cos(ph) * ny
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
        depth.append(math.sin(ph))
    if map_pt:
        pts = [map_pt(*p) for p in pts]
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


# ================================================================ layout

# ---- the rod being taken in, upper right: it sits end-first in a shallow cup
# of the host's membrane, which rises round it as two thin arms
ROD_HL, ROD_R = 70.0, 31.0
PHI0 = math.radians(-34)          # where on the host it goes in
RA = PHI0 + math.radians(9)       # the rod's axis, pointing out of the cup
SINK = 46.0                       # how deep its inner end sits below the host's surface
ra = (math.cos(RA), math.sin(RA))
rn = (-ra[1], ra[0])              # across the rod (toward the lower right: arm B's side)
_c0 = (C[0] + (R - SINK) * math.cos(PHI0), C[1] + (R - SINK) * math.sin(PHI0))
RC = (_c0[0] + ra[0] * (ROD_HL + ROD_R), _c0[1] + ra[1] * (ROD_HL + ROD_R))


def rod_pt(t, o):
    return (RC[0] + ra[0] * t + rn[0] * o, RC[1] + ra[1] * t + rn[1] * o)


CUP_GAP = 7.5                     # membrane to bacterium


def arm_w(t, t_tip):
    """Arm width along the rod: broad at the cup's lip, slim at the tip."""
    u = max(0.0, min(1.0, (t + 40) / (t_tip + 40)))
    return 15.0 - 7.0 * u


def membrane_path(tA, tB, dA, dB, t_jA=-30.0, t_jB=-30.0):
    """The host membrane from the limb on arm A's side, up arm A's outer edge,
    round its tip, down its inner edge, round the cup under the rod, up arm B's
    inner edge, round its tip and down to the limb on B's side."""
    o_in = ROD_R + CUP_GAP

    def gap_at(t, t_tip):
        # the tips lean in a little
        return o_in - 3.0 * max(0.0, (t - (t_tip - 30)) / 30)

    pts = []
    # A: fillet from the limb up to the arm's outer edge
    LA_ang = PHI0 - dA
    LA = (C[0] + R * math.cos(LA_ang), C[1] + R * math.sin(LA_ang))
    tanA = (math.sin(LA_ang), -math.cos(LA_ang))     # along the limb, toward the cup
    jA = rod_pt(t_jA, -(gap_at(t_jA, tA) + arm_w(t_jA, tA)))
    pts += bezier(LA, (LA[0] + tanA[0] * 26, LA[1] + tanA[1] * 26),
                  (jA[0] - ra[0] * 26, jA[1] - ra[1] * 26), jA, step=1.0)
    ts = [t_jA + (tA - t_jA) * k / 60 for k in range(1, 61)]
    pts += [rod_pt(t, -(gap_at(t, tA) + arm_w(t, tA))) for t in ts]
    # tip A: half circle from the outer to the inner edge
    wt = arm_w(tA, tA)
    cA = rod_pt(tA, -(gap_at(tA, tA) + wt / 2))
    a0 = math.atan2(-rn[1], -rn[0])
    pts += ellipse_pts(cA[0], cA[1], wt / 2, wt / 2, 0, a0, a0 + math.pi, step=1.0)[1:-1] \
        if math.cos(a0 + math.pi / 2 - RA) > 0 else \
        ellipse_pts(cA[0], cA[1], wt / 2, wt / 2, 0, a0, a0 - math.pi, step=1.0)[1:-1]
    # inner edge of A, down to the cup
    ts = [tA + (-ROD_HL - tA) * k / 80 for k in range(0, 81)]
    pts += [rod_pt(t, -gap_at(t, tA)) for t in ts]
    # the cup under the rod's inner end
    cc = rod_pt(-ROD_HL, 0)
    b0 = math.atan2(-rn[1], -rn[0])
    arc = ellipse_pts(cc[0], cc[1], o_in, o_in, 0, b0, b0 + math.pi, step=1.0)
    if dist(arc[len(arc) // 2], rod_pt(-ROD_HL - o_in, 0)) > 2:
        arc = ellipse_pts(cc[0], cc[1], o_in, o_in, 0, b0, b0 - math.pi, step=1.0)
    pts += arc[1:-1]
    # inner edge of B, up
    ts = [-ROD_HL + (tB + ROD_HL) * k / 80 for k in range(0, 81)]
    pts += [rod_pt(t, gap_at(t, tB)) for t in ts]
    # tip B
    wt = arm_w(tB, tB)
    cB = rod_pt(tB, gap_at(tB, tB) + wt / 2)
    a0 = math.atan2(-rn[1], -rn[0])
    tip = ellipse_pts(cB[0], cB[1], wt / 2, wt / 2, 0, a0, a0 + math.pi, step=1.0)
    if dist(tip[len(tip) // 2], rod_pt(tB + wt / 2, gap_at(tB, tB) + wt / 2)) > 2:
        tip = ellipse_pts(cB[0], cB[1], wt / 2, wt / 2, 0, a0, a0 - math.pi, step=1.0)
    pts += tip[1:-1]
    # outer edge of B, down, and the fillet to the limb
    jB = rod_pt(t_jB, gap_at(t_jB, tB) + arm_w(t_jB, tB))
    ts = [tB + (t_jB - tB) * k / 60 for k in range(0, 60)]
    pts += [rod_pt(t, gap_at(t, tB) + arm_w(t, tB)) for t in ts]
    LB_ang = PHI0 + dB
    LB = (C[0] + R * math.cos(LB_ang), C[1] + R * math.sin(LB_ang))
    tanB = (-math.sin(LB_ang), math.cos(LB_ang))     # along the limb, away from the cup
    pts += bezier(jB, (jB[0] - ra[0] * 26, jB[1] - ra[1] * 26),
                  (LB[0] - tanB[0] * 26, LB[1] - tanB[1] * 26), LB, step=1.0)
    return resample(pts, 1.0), LA_ang, LB_ang


CUP, CUP_A0, CUP_A1 = membrane_path(tA=18.0, tB=34.0, dA=math.radians(17), dB=math.radians(17))
# the cup and arms as a region (closing along the limb), to keep host lines out of it
_close = ellipse_pts(C[0], C[1], R, R, 0, CUP_A1, CUP_A0, step=2.0)
CUP_REG = Region(CUP + _close[1:-1])
ROD_REG = Region(capsule_pts(RC[0], RC[1], RA, ROD_HL, ROD_R, step=2.0))

# ---- other protrusions: long, thin, gently waving, two branching once
p_left = sprout(198, (46, 380), 250, l0=120, l3=90, wave=14, waves=1.6)
p_left_b = branch(p_left, 0.46, -26, (70, 610), 120, l0=40, l3=50, wave=6)
p_ll = sprout(140, (176, 962), 100, l0=110, l3=90, wave=-12, waves=1.6)
p_bot = sprout(80, (640, 978), 20, l0=80, l3=90, wave=10, waves=1.4)
p_right = sprout(10, (958, 640), 80, l0=120, l3=90, wave=-12, waves=1.6)
p_right_b = branch(p_right, 0.45, -32, (950, 430), 280, l0=40, l3=50, wave=5)

groups = [[p_left, p_left_b], [p_ll], [p_bot], [p_right, p_right_b]]
all_tubes = [t for g in groups for t in g]
front_tubes = all_tubes


def tube_hide(p):
    return any(p in t.region for t in front_tubes)

# ================================================================ drawing

# ---- protrusions
for g in groups:
    for t in g:
        others = [o for o in g if o is not t]

        def hide(p, others=others):
            return in_host(p) or any(p in o.region for o in others)

        for ol in t.outline:
            ink_outline(ol, hide, 1.05, 1.75, sign=1)


# ---- rods

def rod(cx, cy, ang, hl, r, hide=lambda p: False, flag=None):
    """A rod-shaped bacterium seen whole: a firm outline heavier on the shadow
    side, shading lines that follow the outline there, an optional flagellum."""
    out = capsule_pts(cx, cy, ang, hl, r, step=1.5)
    ink_outline(out, hide, 1.5, 2.5, sign=1)
    for k in range(1, 4):
        rk = r - HATCH_GAP * k - 0.5
        thr = 0.05 + 0.2 * k
        line = capsule_pts(cx, cy, ang, hl, rk, step=1.0)
        keep = []
        for p in line:
            n = capsule_normal(cx, cy, ang, hl, p)
            d = -(n[0] * LIGHT[0] + n[1] * LIGHT[1])
            keep.append(d > thr)
        if all(keep):
            segs = [line]
        else:
            i0 = keep.index(False)
            line = line[i0:] + line[1:i0 + 1]
            keep = keep[i0:] + keep[1:i0 + 1]
            segs, cur = [], []
            for p, kk in zip(line, keep):
                if kk:
                    cur.append(p)
                elif cur:
                    segs.append(cur)
                    cur = []
            if cur:
                segs.append(cur)
        for sgm in segs:
            if length(sgm) < 14:
                continue
            sgm = resample(sgm, 1.0)
            cut = min(len(sgm) // 4, 5)
            sgm = sgm[cut:len(sgm) - cut]
            for run in runs(sgm, hide, minlen=8):
                ink(run, W_HATCH, hand=0.12, piece=(80, 160))
    if flag:
        end, ln, wave, amp, bend = flag
        a = (math.cos(ang), math.sin(ang))
        pole = (cx + end * a[0] * (hl + r - 1.5), cy + end * a[1] * (hl + r - 1.5))
        d0 = math.atan2(end * a[1], end * a[0])
        pts = []
        s = 0.0
        x, y = pole
        n_steps = int(ln / 1.0)
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


rod(RC[0], RC[1], RA, ROD_HL, ROD_R)
rod(262, 196, math.radians(32), ROD_HL, ROD_R, hide=tube_hide,
    flag=(-1, 150, 54, 10.0, math.radians(-30)))

# ---- the host's outline: the cut face's edge and the shell's limb


def face_pt(rr, phi):
    """A point on a circle of radius rr on the cut face, and its depth (z toward the eye)."""
    X, Y = rr * math.cos(phi), rr * math.sin(phi)
    return plane(X, Y)


def face_z(phi, rr=R_FACE):
    # 3D: centre D n + rr (cos E1' + sin E2'), with the face axes in 3D
    X, Y = rr * math.cos(phi), rr * math.sin(phi)
    # X runs along -E2 = (-cos U, +sin) in (screen, z); Y along -E1 or E1 (z = 0)
    return D_CUT * COS_T + X * SIN_T


face_edge = [face_pt(R_FACE, 2 * math.pi * i / 1200) for i in range(1201)]


def crease(p):
    """The face's edge is lighter where it is an inner edge (against the shell)."""
    X, Y = plane_inv(p)
    phi = math.atan2(Y, X)
    return 0.7 if face_z(phi) > 0 else 1.0


ink_outline(face_edge, lambda p: tube_hide(p) or p in CUP_REG, 1.8, 2.7, wmul=crease)


def ang_in(a, a0, a1):
    a = (a - a0) % (2 * math.pi)
    return a < (a1 - a0) % (2 * math.pi)


limb = []
for i in range(1441):
    a = 2 * math.pi * i / 1440
    p = (C[0] + R * math.cos(a), C[1] + R * math.sin(a))
    pu = (p[0] - C[0]) * U[0] + (p[1] - C[1]) * U[1]
    limb.append(p if SIN_T * pu < D_CUT - 0.5 and not ang_in(a, CUP_A0, CUP_A1) else None)
# rotate so each visible arc is one run
i0 = limb.index(None)
limb = limb[i0:] + limb[1:i0 + 1]
cur = []
for q in limb + [None]:
    if q is None:
        if len(cur) > 1:
            ink_outline(cur, tube_hide, 1.8, 2.8, sign=1)
        cur = []
    else:
        cur.append(q)
# the membrane round the cup and up the two arms
ink_outline(CUP, tube_hide, 1.4, 2.4, sign=1)
# the membrane's thickness at the cut
for run in runs([face_pt(R_FACE - 7, 2 * math.pi * i / 1200) for i in range(1201)], lambda p: p in CUP_REG):
    ink(run, 0.95, hand=0.15)

# ---- shading on the shell: rings of the sphere parallel to the cut (as in 07),
# on the shadow side, spaced evenly where they are widest apart
GAP_RING = 6.6


def ring_ext(c):
    rc = math.sqrt(R * R - c * c)
    return c * SIN_T - rc * COS_T


c = D_CUT
rings = []
while True:
    # step so the rings' outermost points (toward -U) sit GAP_RING apart on screen
    lo, hi = 0.0, min(R, c + R - 1.0)
    e0 = ring_ext(c)
    for _ in range(40):
        mid = (lo + hi) / 2
        if e0 - ring_ext(c - mid) < GAP_RING:
            lo = mid
        else:
            hi = mid
    c = c - hi
    if hi > 60 or c < -R * 0.98:
        break
    rings.append(c)

HGRID = {}


def near_hatch(p, d):
    gx, gy = int(p[0] // 6), int(p[1] // 6)
    for i in range(gx - 1, gx + 2):
        for j in range(gy - 1, gy + 2):
            for q in HGRID.get((i, j), ()):
                if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < d * d:
                    return True
    return False


for k, cc in enumerate(rings):
    rc = math.sqrt(R * R - cc * cc)
    pts = []
    for i in range(721):
        ph = 2 * math.pi * i / 720
        # 3D point: cc n + rc (cos ph E1 + sin ph E2), E1 = (e1, 0), E2 = (cos U, -sin)
        sx = C[0] + cc * SIN_T * U[0] + rc * math.cos(ph) * E1[0] + rc * math.sin(ph) * COS_T * U[0]
        sy = C[1] + cc * SIN_T * U[1] + rc * math.cos(ph) * E1[1] + rc * math.sin(ph) * COS_T * U[1]
        z = cc * COS_T - rc * math.sin(ph) * SIN_T
        nx, ny, nz = (sx - C[0]) / R, (sy - C[1]) / R, z / R
        lam = nx * LIGHT3[0] + ny * LIGHT3[1] + nz * LIGHT3[2]
        ok = z > 4.0 and lam < 0.22 - 0.01 * k
        pts.append((sx, sy) if ok else None)
    if pts[0] is not None and None in pts:
        i0 = pts.index(None)
        pts = pts[i0:] + pts[1:i0 + 1]
    cur = []
    drawn = []
    for q in pts + [None]:
        if q is None:
            if len(cur) > 1 and length(cur) > 12:
                cur = resample(cur, 1.0)
                cut = min(len(cur) // 6, 4)
                cur = cur[cut:len(cur) - cut]
                # never closer than 5 to a ring already drawn (they crowd toward the limb)
                for run in runs(cur, lambda p: tube_hide(p) or classify(p) != 'shell' or p in CUP_REG or near_hatch(p, 5.4)
                                or dist(p, C) > R - 4.0, minlen=10):
                    ink(run, W_HATCH, hand=0.12, piece=(80, 160))
                    drawn += run
            cur = []
        else:
            cur.append(q)
    for p in drawn:
        HGRID.setdefault((int(p[0] // 6), int(p[1] // 6)), []).append(p)

# ---- inside, on the cut face

# the enclosed alphaproteobacterium, cut through: outer and inner membrane
EB = (-80.0, -100.0)
EB_ANG = math.radians(-22)
EB_HL, EB_R = 68.0, 31.0
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R)], 1.7)
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R - 6.5)], 1.05)
for run in coil_ring(EB[0] + 4, EB[1] - 1, 32, 10, EB_ANG, 4.6, 11, map_pt=plane, gap=2.4):
    ink(run, 1.0, hand=0.1)
_a = (math.cos(EB_ANG), math.sin(EB_ANG))
_n = (-_a[1], _a[0])
for t, o in [(-58, -4), (-46, 12), (50, -8), (60, 6), (-20, -16), (30, 15)]:
    q = plane(EB[0] + _a[0] * t + _n[0] * o, EB[1] + _a[1] * t + _n[1] * o)
    pen.dot(q[0], q[1], r=2.6, w=1.0)

# the host's chromosome: one circular strand, supercoiled into regular loops
NUC = (40.0, 85.0)
NUC_RA, NUC_RB, NUC_ROT = 96.0, 68.0, math.radians(-18)
for run in coil_ring(NUC[0], NUC[1], NUC_RA, NUC_RB, NUC_ROT, 13.0, 18, map_pt=plane):
    ink(run, 1.3, hand=0.1)


# ribosomes: small rings, evenly scattered (Poisson disk on the face)
def free_spot(X, Y):
    if X * X + Y * Y > (R_FACE - 30) ** 2:
        return False
    c, s = math.cos(-NUC_ROT), math.sin(-NUC_ROT)
    dx, dy = X - NUC[0], Y - NUC[1]
    lx, ly = dx * c - dy * s, dx * s + dy * c
    if (lx / (NUC_RA + 34)) ** 2 + (ly / (NUC_RB + 34)) ** 2 < 1:
        return False
    t = (X - EB[0]) * _a[0] + (Y - EB[1]) * _a[1]
    t = max(-EB_HL, min(EB_HL, t))
    if math.hypot(X - (EB[0] + _a[0] * t), Y - (EB[1] + _a[1] * t)) < EB_R + 18:
        return False
    return True


ribo = []
tries = 0
while tries < 8000:
    tries += 1
    X, Y = rng.uniform(-R, R), rng.uniform(-R, R)
    if not free_spot(X, Y):
        continue
    if any((X - a) ** 2 + (Y - b) ** 2 < 52 ** 2 for a, b in ribo):
        continue
    ribo.append((X, Y))
for X, Y in ribo:
    q = plane(X, Y)
    pen.dot(q[0], q[1], r=3.6, w=1.2)

pen.save(OUT)
pen.report()
