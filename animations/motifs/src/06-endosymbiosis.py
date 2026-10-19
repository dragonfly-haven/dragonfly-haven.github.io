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


def bez_centre(p0, a0, l0, p3, a3, l3):
    """A smooth centre line leaving p0 at angle a0 and arriving at p3 heading a3 (degrees)."""
    p1 = (p0[0] + l0 * math.cos(math.radians(a0)), p0[1] + l0 * math.sin(math.radians(a0)))
    p2 = (p3[0] - l3 * math.cos(math.radians(a3)), p3[1] - l3 * math.sin(math.radians(a3)))
    return bezier(p0, p1, p2, p3, step=1.0)


def sprout(deg, p3, a3, l0=90, l3=90, w0=11.5, w1=7.5):
    p0 = from_host(deg, -14)
    return Tube(bez_centre(p0, deg, l0, p3, a3, l3), w0, w1)


def branch(parent, frac, turn, p3, a3, l0=50, l3=50, w0=9.0, w1=7.0):
    p0, a = parent.at(frac)
    a0 = math.degrees(a) + turn
    return Tube(bez_centre(p0, a0, l0, p3, a3, l3), w0, w1, flare=1.5, flare_len=6.0)


# ================================================================ layout

# ---- the rod being taken in, upper right, lying against the host
ROD_HL, ROD_R = 70.0, 31.0
ROD_GAP = 7.0
ROD_ON = math.radians(-46)
_rad = R + ROD_R + ROD_GAP
RC = (C[0] + _rad * math.cos(ROD_ON), C[1] + _rad * math.sin(ROD_ON))
RA = ROD_ON + math.pi / 2
ra = (math.cos(RA), math.sin(RA))            # along the rod (toward the lower right)
rn = (math.cos(ROD_ON), math.sin(ROD_ON))    # away from the host


def rod_pt(t, o):
    return (RC[0] + ra[0] * t + rn[0] * o, RC[1] + ra[1] * t + rn[1] * o)


def rod_region(grow=0.0):
    return Region(capsule_pts(RC[0], RC[1], RA, ROD_HL, ROD_R + grow, step=2.0))


ROD_REG = rod_region()


def wrap_arm(sign, t_base, t_over, w0=11.0, w1=7.5):
    """A protrusion that leaves the host beside the rod, crosses over its front
    and curls round its outer edge, the tip tucked behind the rod.
    Returns (front tube, back tube)."""
    s = sign
    base = from_host(math.degrees(ROD_ON) + s * math.degrees(abs(t_base) / _rad) * 1.0, -12)
    # control points in rod coordinates (t along the rod, o out from the host)
    ctrl = [base,
            rod_pt(s * (abs(t_base) - 4), -ROD_R - 14),
            rod_pt(s * (abs(t_base) - 16), -ROD_R + 6),
            rod_pt(s * (abs(t_over) + 8), ROD_R - 6),
            rod_pt(s * abs(t_over), ROD_R + 13),
            rod_pt(s * (abs(t_over) - 14), ROD_R + 16),
            rod_pt(s * (abs(t_over) - 26), ROD_R + 6),
            rod_pt(s * (abs(t_over) - 34), ROD_R - 12)]
    centre = resample(catmull(ctrl, step=1.0), 1.0)
    # split where the centre line, outside the rod, is about to turn back behind it
    n = len(centre)
    split = None
    for i in range(n // 2, n):
        p = centre[i]
        o = (p[0] - RC[0]) * rn[0] + (p[1] - RC[1]) * rn[1]
        if o > ROD_R + 13:
            split = i
            break
    split = split or n - 1
    L = length(centre)
    front = Tube(centre[:split + 1], w0, w1, cap=False, L_total=L)
    back = Tube(centre[split:], w0, w1, flare=0.0, s_from=length(centre[:split + 1]), L_total=L)
    return front, back


arm1_f, arm1_b = wrap_arm(-1, 100, 34)
arm2_f, arm2_b = wrap_arm(+1, 98, 30)

# ---- other protrusions, some branching once
p_left = sprout(190, (48, 452), 250, l0=110, l3=90)
p_left_b = branch(p_left, 0.5, -38, (96, 690), 115, l0=50, l3=40)
p_ll = sprout(136, (138, 962), 120, l0=120, l3=80)
p_bot = sprout(78, (672, 968), 30, l0=70, l3=70)
p_right = sprout(14, (958, 600), 70, l0=110, l3=60)
p_right_b = branch(p_right, 0.56, 42, (880, 820), 100, l0=50, l3=50)

groups = [[arm1_f, arm1_b], [arm2_f, arm2_b], [p_left, p_left_b], [p_ll], [p_bot], [p_right, p_right_b]]
all_tubes = [t for g in groups for t in g]
front_tubes = [t for t in all_tubes if t not in (arm1_b, arm2_b)]


def tube_hide(p):
    return any(p in t.region for t in front_tubes)


# ================================================================ drawing

# ---- protrusions
for g in groups:
    for t in g:
        others = [o for o in g if o is not t]
        behind_rod = t in (arm1_b, arm2_b)

        def hide(p, others=others, behind_rod=behind_rod):
            if in_host(p) or any(p in o.region for o in others):
                return True
            return behind_rod and p in ROD_REG

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


rod(RC[0], RC[1], RA, ROD_HL, ROD_R, hide=lambda p: tube_hide(p) or in_host(p))
rod(232, 178, math.radians(30), ROD_HL, ROD_R, hide=tube_hide,
    flag=(-1, 160, 56, 10.0, math.radians(-12)))

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


ink_outline(face_edge, tube_hide, 1.8, 2.7, wmul=crease)
limb = []
for i in range(1441):
    a = 2 * math.pi * i / 1440
    p = (C[0] + R * math.cos(a), C[1] + R * math.sin(a))
    pu = (p[0] - C[0]) * U[0] + (p[1] - C[1]) * U[1]
    limb.append(p if SIN_T * pu < D_CUT - 0.5 else None)
cur = []
# rotate so the visible arc is one run
i0 = limb.index(None)
limb = limb[i0:] + limb[1:i0 + 1]
arc = [p for p in limb if p is not None]
ink_outline(arc, tube_hide, 1.8, 2.8, sign=1)
# the membrane's thickness at the cut
ink([face_pt(R_FACE - 7, 2 * math.pi * i / 1200) for i in range(1201)], 0.95, hand=0.15)

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
    for q in pts + [None]:
        if q is None:
            if len(cur) > 1 and length(cur) > 12:
                cur = resample(cur, 1.0)
                cut = min(len(cur) // 6, 4)
                cur = cur[cut:len(cur) - cut]
                for run in runs(cur, lambda p: tube_hide(p) or classify(p) != 'shell', minlen=8):
                    ink(run, W_HATCH, hand=0.12, piece=(80, 160))
            cur = []
        else:
            cur.append(q)

# ---- inside, on the cut face

# the enclosed alphaproteobacterium, cut through: outer and inner membrane
EB = (-80.0, -100.0)
EB_ANG = math.radians(-22)
EB_HL, EB_R = 68.0, 31.0
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R)], 1.7)
ink([plane(x, y) for x, y in capsule_pts(EB[0], EB[1], EB_ANG, EB_HL, EB_R - 6.5)], 1.05)
for run in coil_ring(EB[0] + 4, EB[1] - 1, 30, 9, EB_ANG, 6.0, 8, map_pt=plane, gap=2.6):
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
    if any((X - a) ** 2 + (Y - b) ** 2 < 62 ** 2 for a, b in ribo):
        continue
    ribo.append((X, Y))
for X, Y in ribo:
    q = plane(X, Y)
    pen.dot(q[0], q[1], r=4.0, w=1.2)

pen.save(OUT)
pen.report()
