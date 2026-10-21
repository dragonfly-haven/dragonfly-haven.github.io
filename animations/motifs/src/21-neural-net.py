"""21 - the future: people in nature looking at a far metropolis, under a sky
whose stars form neural networks.

COMPOSITION DRAFT (stage 1 of the design worked out with Maxim): main masses,
people, roads, city silhouette, horizon and the neural-net constellations
roughly in place, with a little tone. Detail comes after his notes.

Two compositions are drafted from the same parts:
    python3 21-neural-net.py            draft A -> ../21-neural-net.svg
    python3 21-neural-net.py B <path>   draft B -> <path>
A: low horizon, big sky; the people stand on a knoll at the left, the city
   rises right of centre, a road sweeps up from the lower right and a skyway
   on pylons comes in from the right.
B: high horizon, long road; the people stand near the bottom, a long road
   winds from their feet up to a wide city across the middle, a skyway curves
   in from the left, a smaller sky above.
Groves of round park trees stand out on the plain in both.

The ground and roads are drawn in a true perspective (a camera at height HC
over a flat plain, horizon at YH), so the roads narrow as they should. Things
are drawn front to back; each solid shape hides what is drawn after it.
Not mirrored (slot 21 faces as drawn).

(The passed neural-net figure this replaces is backed up in the scratchpad;
base/21-neural-net.svg holds the older hand-drawn net and is not read.)
"""

import math
import sys
from collections import defaultdict

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, length, clip_segments, scanlines

VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'A'
OUT = sys.argv[2] if len(sys.argv) > 2 else '../21-neural-net.svg'


class ScenePen(Pen):
    """A Pen whose occluders sit on a grid, so a busy scene stays quick."""

    def __init__(self, seed):
        super().__init__(seed)
        self.cell = 25
        self.grid = defaultdict(list)
        self.polys = []

    def occlude(self, poly):
        poly = list(poly)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        bb = (min(xs), min(ys), max(xs), max(ys))
        k = len(self.polys)
        self.polys.append((poly, bb))
        c = self.cell
        for i in range(int(bb[0] // c), int(bb[2] // c) + 1):
            for j in range(int(bb[1] // c), int(bb[3] // c) + 1):
                self.grid[(i, j)].append(k)

    def hidden(self, p):
        c = self.cell
        for k in self.grid.get((int(p[0] // c), int(p[1] // c)), ()):
            poly, bb = self.polys[k]
            if bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3] and inside(p, poly):
                return True
        return False

    def visible(self, pts):
        if not self.polys:
            return [list(pts)]
        return clip_segments(pts, lambda p: not self.hidden(p))


pen = ScenePen(seed=2101 if VARIANT == 'A' else 2102)
R = pen.r
G = pen.g


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def mirror_half(right):
    """A closed outline from its right half (top to bottom), mirrored about x=0."""
    left = [(-x, y) for x, y in reversed(right)]
    return right + left


def place(pts, x0, y0, s):
    return [(x0 + x * s, y0 + y * s) for x, y in pts]


# ---------------------------------------------------------------- the scene's set-up

if VARIANT == 'A':
    YH = 600.0         # horizon
    HC = 20.0          # camera height over the plain (m)
else:
    YH = 435.0
    HC = 34.0
F = 700.0              # focal length (units)
CXP = 500.0


def Z_of(sy):
    return F * HC / (sy - YH)


def P(X, Y, Z):
    """World (X right, Y up, Z depth, metres) to the page."""
    return (CXP + F * X / Z, YH + F * (HC - Y) / Z)


def ground_of(sx, sy):
    """Page point below the horizon back to the plain."""
    Z = Z_of(sy)
    return ((sx - CXP) * Z / F, Z)


# ---------------------------------------------------------------- small marks

def dot(x, y, r=1.4, w=1.2):
    pen.dot(x, y, r=r, w=w)


def sparkle(x, y, L, w=1.2, rot=0.0, diag=0.3):
    """A four-pointed star: two tapered crossing strokes, shorter faint diagonals."""
    for k in range(2):
        a = rot + k * math.pi / 2
        Lk = L * (1.0 if k == 0 else 0.8)
        p0 = (x - math.cos(a) * Lk, y - math.sin(a) * Lk)
        p1 = (x + math.cos(a) * Lk, y + math.sin(a) * Lk)
        pen.line([p0, (x, y), p1], w=w, hand=0, lift=0, piece=(2.5, 4), taper=0.92)
    if diag:
        for k in range(2):
            a = rot + math.pi / 4 + k * math.pi / 2
            Ld = L * diag
            p0 = (x - math.cos(a) * Ld, y - math.sin(a) * Ld)
            p1 = (x + math.cos(a) * Ld, y + math.sin(a) * Ld)
            pen.line([p0, p1], w=w * 0.6, hand=0, lift=0, piece=(2, 3), taper=0.9)
    dot(x, y, r=1.1, w=w)


def ruled(pts, w, hand=0.15):
    pen.line(pts, w=w, hand=hand, lift=0, piece=(200, 400))


def shade(poly, angle, spacing, w=0.7, keep=None, hand=0.3, shrink=(0.02, 0.12)):
    pen.hatch(poly, angle=angle, spacing=spacing, w=w, jitter=0.1, shrink=shrink, hand=hand, keep=keep)


# ---------------------------------------------------------------- drawing helpers for figures

LIGHT = (-0.6, -0.8)          # toward the light (upper left), as in the set
SHADE = (0.6, 0.8)


def C(ctrl, closed=False, step=1.2):
    return catmull(ctrl, closed=closed, step=step)


def clip_in(pts, poly):
    if poly is None:
        return [list(pts)]
    return clip_segments(pts, lambda p: inside(p, poly))


def fine(pts, w=1.0, hand=0.35, lift=0.04):
    pen.line(pts, w=w, hand=hand, lift=lift, piece=(30, 90))


def frac_pts(rail, n):
    """n+1 points spread evenly along a polyline."""
    pts = resample(rail, max(0.3, length(rail) / max(1, n * 4)))
    return [pts[min(len(pts) - 1, int(round(k * (len(pts) - 1) / n)))] for k in range(n + 1)]


def lengthwise(lit, shade_rail, u0, u1, spacing=5.6, t0=0.02, t1=0.98, w=0.7, clip=None, wave=0.0, hand=0.3,
               ends=(0.0, 0.0)):
    """Strokes running along a form between its lit rail (u=0) and its shade
    rail (u=1), both drawn the same way: at fractions u0..u1 across, spaced
    about `spacing` units where the form is widest."""
    N = 40
    A, B = frac_pts(lit, N), frac_pts(shade_rail, N)
    wmax = max(dist(a, b) for a, b in zip(A, B))
    n = max(1, int((u1 - u0) * wmax / spacing) + 1)
    for k in range(n):
        u = u0 + (u1 - u0) * (k + 0.5) / n
        a = t0 + R(0, ends[0])
        b = t1 - R(0, ends[1])
        pts = []
        ph = R(0, 6.3)
        for i in range(N + 1):
            t = i / N
            if t < a or t > b:
                continue
            p = lerp(A[i], B[i], u)
            if wave:
                p = (p[0] + wave * math.sin(t * 9 + ph), p[1])
            pts.append(p)
        if len(pts) < 2:
            continue
        for run in clip_in(C(pts, step=2.0), clip):
            if length(run) > 3:
                pen.line(run, w=w * R(0.88, 1.12), hand=hand, lift=0.04, piece=(30, 90))


def ticks(line, side, spacing=5.4, L=(4, 9), w=0.7, t0=0.1, t1=0.95, ang=0.35, clip=None, gap=1.0):
    """Short strokes leaving a line on one side (a fold's shadow), side +1 to
    the right of the line's travel (page x+ for a line drawn downward)."""
    pts = resample(line, 0.8)
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + dist(pts[i - 1], pts[i]))
    tot = cum[-1]
    s = tot * t0 + R(0, spacing * 0.5)
    i = 0
    while s < tot * t1:
        while i < len(pts) - 2 and cum[i + 1] < s:
            i += 1
        p, q = pts[i], pts[i + 1]
        tx, ty = q[0] - p[0], q[1] - p[1]
        tl = math.hypot(tx, ty) or 1
        tx, ty = tx / tl, ty / tl
        if side > 0:
            nx, ny = ty, -tx
        else:
            nx, ny = -ty, tx
        # lean the stroke a little down the line
        dx, dy = nx + tx * ang, ny + ty * ang
        dl = math.hypot(dx, dy)
        dx, dy = dx / dl, dy / dl
        u = (s / tot - t0) / max(1e-6, t1 - t0)
        ln = (L[0] + (L[1] - L[0]) * math.sin(math.pi * min(1, u * 1.1)) ** 0.7) * R(0.8, 1.15)
        a0 = (p[0] + nx * gap, p[1] + ny * gap)
        a1 = (a0[0] + dx * ln, a0[1] + dy * ln)
        for run in clip_in([a0, a1], clip)[:1]:
            if length(run) > 2:
                pen.line(run, w=w * R(0.88, 1.12), hand=0.15, lift=0, piece=(30, 90))
        s += spacing * R(0.92, 1.08)


def across(railA, railB, spacing=6.0, frac=(0.3, 0.55), bow=1.5, w=0.7, t0=0.05, t1=0.95, from_b=True, clip=None):
    """Cross-contour hatching on a tube, strokes from rail B toward rail A, bowing down."""
    N = 60
    A, B = frac_pts(railA, N), frac_pts(railB, N)
    tot = (length(railA) + length(railB)) / 2
    n = max(1, int(tot * (t1 - t0) / spacing))
    for k in range(n):
        t = t0 + (t1 - t0) * (k + 0.5 + G(0.1)) / n
        i = int(clamp(t, 0, 1) * N)
        f = R(*frac)
        p0, p1 = (B[i], A[i]) if from_b else (A[i], B[i])
        q0, q1 = lerp(p0, p1, 0.05), lerp(p0, p1, f)
        m = lerp(q0, q1, 0.5)
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        if ny < 0:
            nx, ny = -nx, -ny
        seg = C([q0, (m[0] + nx * bow * f, m[1] + ny * bow * f), q1], step=1.5)
        for run in clip_in(seg, clip)[:1]:
            if length(run) > 2:
                pen.line(run, w=w * R(0.88, 1.12), hand=0.2, lift=0, piece=(30, 90))


def tube(ctrl, widths, cap0=True, cap1=True):
    """A limb or sleeve round a spine: returns (lit rail, shade rail, outline)."""
    sp = resample(C(ctrl, step=0.8), 0.8)
    n = len(sp)
    cum = [0.0]
    for i in range(1, n):
        cum.append(cum[-1] + dist(sp[i - 1], sp[i]))
    tot = cum[-1] or 1
    m = len(widths) - 1

    def wat(f):
        x = f * m
        k = min(m - 1, int(x))
        return widths[k] + (widths[k + 1] - widths[k]) * (x - k)
    ra, rb = [], []
    for i, p in enumerate(sp):
        a, b = sp[max(0, i - 1)], sp[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = dy / L, -dx / L
        hw = wat(cum[i] / tot) / 2
        ra.append((p[0] + nx * hw, p[1] + ny * hw))
        rb.append((p[0] - nx * hw, p[1] - ny * hw))

    def cap(c, t, r, frm, to, bulge):
        # a rounded end from point frm to point to, bulging along t
        out = []
        for k in range(1, 12):
            a = math.pi * k / 12
            v = (frm[0] - c[0], frm[1] - c[1])
            # rotate v toward the end direction
            ca, sa = math.cos(a), math.sin(a)
            px = c[0] + v[0] * ca + t[0] * r * sa * bulge
            py = c[1] + v[1] * ca + t[1] * r * sa * bulge
            out.append((px, py))
        return out
    t1 = (sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1])
    l1 = math.hypot(*t1) or 1
    t1 = (t1[0] / l1, t1[1] / l1)
    t0 = (sp[0][0] - sp[1][0], sp[0][1] - sp[1][1])
    l0 = math.hypot(*t0) or 1
    t0 = (t0[0] / l0, t0[1] / l0)
    end = cap(sp[-1], t1, widths[-1] / 2, ra[-1], rb[-1], 0.6 if cap1 else 0.15)
    start = cap(sp[0], t0, widths[0] / 2, rb[0], ra[0], 0.9 if cap0 else 0.15)
    outline = ra + end + list(reversed(rb)) + start
    # which rail is lit: the one toward the light
    ma = sum((p[0] - q[0]) * LIGHT[0] + (p[1] - q[1]) * LIGHT[1] for p, q in zip(ra, sp))
    lit, shd = (ra, rb) if ma > 0 else (rb, ra)
    tube.last = dict(a=ra, b=rb, end=end)
    return lit, shd, outline


def hand(W, d, L, wd, fingers=True, w=1.3):
    """A hand seen from the back: a rounded mitten from the wrist W along unit d."""
    ux, uy = d
    nx, ny = -uy, ux

    def Q(s, t):
        return (W[0] + ux * s * L + nx * t * wd, W[1] + uy * s * L + ny * t * wd)
    out = C([Q(0, -0.46), Q(0.32, -0.55), Q(0.66, -0.5), Q(0.9, -0.32), Q(1.0, -0.04), Q(0.96, 0.24), Q(0.78, 0.47),
             Q(0.5, 0.56), Q(0.22, 0.56), Q(0, 0.46)], step=0.8)
    pen.line(out, w=w, hand=0.2, lift=0)
    if fingers:
        for t in (-0.22, 0.04, 0.28):
            fine([Q(0.58, t), Q(0.93, t * 1.05)], w=0.7, hand=0.1)
        fine([Q(0.12, 0.34), Q(0.42, 0.36)], w=0.6, hand=0.1)   # a tendon
    poly = out + [Q(-0.05, 0.46), Q(-0.05, -0.46)]
    pen.occlude(poly)
    return poly


def ik(S, W, a, b, bend):
    """Elbow of a two-bone arm from shoulder S toward wrist W (clamped to
    reach); the elbow is pushed toward the unit vector `bend`."""
    dx, dy = W[0] - S[0], W[1] - S[1]
    d = math.hypot(dx, dy) or 1e-6
    if d > (a + b) * 0.995:
        k = (a + b) * 0.995 / d
        dx, dy, d = dx * k, dy * k, (a + b) * 0.995
        W = (S[0] + dx, S[1] + dy)
    x0 = (a * a - b * b + d * d) / (2 * d)
    h = math.sqrt(max(0.0, a * a - x0 * x0))
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    if nx * bend[0] + ny * bend[1] < 0:
        nx, ny = -nx, -ny
    return (S[0] + ux * x0 + nx * h, S[1] + uy * x0 + ny * h), W


# ---------------------------------------------------------------- the family, seen from behind

class Fig:
    """A figure's own frame: x across, y up negative, feet at 0, height 1;
    placed in the group (scale s, centre cx, feet dy) and the group on the page."""

    def __init__(self, ox, oy, H, cx, s, dy):
        self.ox, self.oy, self.H, self.cx, self.s, self.dy = ox, oy, H, cx, s, dy
        self.u = H * s

    def P(self, p):
        return (self.ox + (self.cx + p[0] * self.s) * self.H, self.oy + (p[1] * self.s + self.dy) * self.H)

    def Ps(self, pts):
        return [self.P(p) for p in pts]

    def mirror(self, pts):
        return [(-x, y) for x, y in pts]


def outline_of(left, bottom, right_up, top=None):
    pts = C(left) + C(bottom)[1:] + C(right_up)[1:]
    if top:
        pts += C(top)[1:]
    return pts


def sleeve(fig, S, E, W, widths, w=1.8, body_cx=None, t_in=0.24):
    """An arm in a sleeve, shoulder to wrist (page points), with a cuff band.
    Its outer edge runs on from the shoulder; its inner edge only shows from
    the armpit down, where it parts from the body."""
    lit, shd, out = tube([S, E, W], widths, cap0=False, cap1=False)
    T = tube.last
    ra, rb, end = T['a'], T['b'], T['end']
    if body_cx is None:
        body_cx = fig.P((0, 0))[0]

    def score(r):
        return abs(r[0][0] - body_cx) - 0.6 * (r[0][1] - S[1])
    if score(ra) >= score(rb):
        outer, inner, cap = ra, rb, end
    else:
        outer, inner, cap = rb, ra, list(reversed(end))
    k_in = int(len(inner) * t_in)
    pen.line(outer + cap + list(reversed(inner[k_in:])), w=w, hand=0.45, lift=0.05)
    # the cuff: a band a little up from the wrist
    k = max(2, int(len(lit) * 0.9))
    a, b = lit[k], shd[k]
    m = lerp(a, b, 0.5)
    fine(C([a, (m[0], m[1] + 1.2), b], step=1), w=0.9)
    lengthwise(lit[:k], shd[:k], 0.6, 0.96, spacing=5.3, t0=0.1, t1=0.98, clip=out, w=0.7)
    # creases at the elbow, on the inner side
    ke = len(lit) // 2
    for j in (-5, 0, 5):
        i = int(clamp(ke + j, 1, len(inner) - 2))
        p, q = inner[i], outer[i]
        fine(C([lerp(p, q, 0.04), (lerp(p, q, 0.25)[0], lerp(p, q, 0.25)[1] + 1.4), lerp(p, q, 0.42)], step=1),
             w=0.7, hand=0.2)
    pen.occlude(out)
    return out


def hair_short(hc, rx, ry, crown, n, u, tousle=0.0, seed_side=1):
    """Short hair on the back of a head: strands sweeping from the crown whorl
    down and round to the nape and sides, of varied length, clumped, and more
    of them on the shade (right) side."""
    head = ellipse_pts(hc[0], hc[1], rx, ry, 0, 0, 2 * math.pi, step=1.0)
    for k in range(n):
        f = (k + R(0.2, 0.8)) / n
        a = math.pi * (0.04 + 0.92 * f)            # 0 = right side ... pi = left side, through the bottom
        r0 = R(0.08, 0.45)
        st = (crown[0] + math.cos(a) * rx * r0 * 0.6, crown[1] + R(0.0, 0.35) * ry * r0)
        reach = R(0.72, 0.98) if R() < 0.75 else R(0.45, 0.7)
        en = (hc[0] + math.cos(a) * rx * reach, hc[1] + math.sin(a) * ry * reach * 0.9 + ry * 0.05)
        tw = 0.18 * rx * (1 if k % 2 else -0.6)            # the sweep round the whorl
        m = lerp(st, en, 0.5)
        m = (m[0] - math.sin(a) * tw + G(0.5), m[1] + math.cos(a) * tw * 0.3)
        pts = [st, m, en]
        if tousle:
            pts.append((en[0] + math.cos(a + 1.2) * tousle * rx, en[1] + math.sin(a + 1.2) * tousle * ry))
        wv = 0.75 if math.cos(a) > -0.2 else 0.68
        for run in clip_in(C(pts, step=1.0), head):
            if length(run) > 3:
                fine(run, w=wv * R(0.9, 1.1), hand=0.25)
    # the whorl itself: two small curls
    for r in (0.12, 0.22):
        arc = ellipse_pts(crown[0], crown[1] + ry * 0.04, rx * r, ry * r * 0.8, 0, R(0, 1), R(3.5, 4.8), step=0.6)
        fine(arc, w=0.65, hand=0.1)


def family(ox, oy, H):
    """A woman, a child and a man, hand in hand, seen from behind, looking
    out at the city. (ox, oy) is the middle of their feet line on the page; H
    the man's height. Plain, timeless dress: a long sashed dress, a knee coat
    over trousers, a child's tunic over leggings."""
    Wf = Fig(ox, oy, H, -0.385, 0.93, 0.0)
    Cf = Fig(ox, oy, H, 0.0, 0.60, 0.015)
    Mf = Fig(ox, oy, H, 0.395, 1.0, 0.004)

    def gp(g):
        return (ox + g[0] * H, oy + g[1] * H)
    GL, GR = gp((-0.272, -0.405)), gp((0.274, -0.415))     # where the hands meet

    # -- the parents' hands that hold the child's (they are nearest the eye there)
    wS = Wf.P((0.106, -0.788))
    wW = (GL[0] + 0.006 * H, GL[1] - 0.052 * H)
    wE, wW = ik(wS, wW, 0.175 * Wf.u, 0.16 * Wf.u, (1, 0))
    d = (GL[0] - wW[0] - 0.004 * H, GL[1] + 0.03 * H - wW[1])
    dl = math.hypot(*d)
    hand(wW, (d[0] / dl, d[1] / dl), 0.085 * Wf.u, 0.05 * Wf.u)
    mS = Mf.P((-0.116, -0.794))
    mW = (GR[0] - 0.006 * H, GR[1] - 0.054 * H)
    mE, mW = ik(mS, mW, 0.18 * H, 0.17 * H, (-1, 0))
    d = (GR[0] - mW[0] + 0.004 * H, GR[1] + 0.03 * H - mW[1])
    dl = math.hypot(*d)
    hand(mW, (d[0] / dl, d[1] / dl), 0.088 * H, 0.052 * H)

    # ------------------------------------------------ the child (in front)
    f = Cf
    u = f.u
    hc = f.P((0, -0.885))
    head = ellipse_pts(hc[0], hc[1], 0.088 * u, 0.102 * u, 0, 0, 2 * math.pi, step=1.0)
    # ears, then the head and hair
    for sgn in (-1, 1):
        ear = f.Ps([(sgn * 0.084, -0.912), (sgn * 0.101, -0.906), (sgn * 0.104, -0.884), (sgn * 0.093, -0.866),
                    (sgn * 0.082, -0.866)])
        pen.line(C(ear, step=0.8), w=1.2, hand=0.2, lift=0)
    pen.line(head, w=1.8, hand=0.35, lift=0.05)
    nape = C(f.Ps([(-0.082, -0.858), (-0.06, -0.836), (-0.03, -0.826), (0, -0.822), (0.03, -0.829), (0.058, -0.838),
                   (0.082, -0.858)]), step=1)
    fine(nape, w=1.1, hand=0.3)
    # tousled short hair, from a whorl at the crown
    hair_short(hc, 0.088 * u, 0.102 * u, f.P((0.014, -0.968)), 17, u, tousle=0.14)
    pen.occlude(head)
    # neck
    fine(C(f.Ps([(-0.033, -0.826), (-0.035, -0.8)]), step=1), w=1.0)
    fine(C(f.Ps([(0.033, -0.826), (0.035, -0.8)]), step=1), w=1.0)
    # arms raised a little to the parents' hands
    for sgn, G_ in ((-1, GL), (1, GR)):
        S = f.P((sgn * 0.112, -0.742))
        dd = (G_[0] - S[0], G_[1] - S[1])
        dl = math.hypot(*dd)
        Wt = (G_[0] - dd[0] / dl * 0.05 * u, G_[1] - dd[1] / dl * 0.05 * u)
        E, Wt = ik(S, Wt, 0.16 * u, 0.15 * u, (0, 1))
        hd = (G_[0] - Wt[0], G_[1] - Wt[1])
        hl = math.hypot(*hd)
        hand(Wt, (hd[0] / hl, hd[1] / hl), 0.075 * u, 0.055 * u, fingers=False, w=1.2)
        sleeve(f, S, E, Wt, [0.068 * u, 0.058 * u, 0.05 * u], w=1.7, t_in=0.16)
    # tunic
    tl = [(-0.048, -0.796), (-0.098, -0.778), (-0.133, -0.752), (-0.13, -0.69), (-0.121, -0.6), (-0.124, -0.51),
          (-0.142, -0.408)]
    hem = [(-0.142, -0.408), (-0.07, -0.401), (0, -0.404), (0.07, -0.4), (0.142, -0.408)]
    tr = list(reversed(f.mirror(tl)))
    top = [(0.048, -0.796), (0, -0.792), (-0.048, -0.796)]
    tunic = outline_of(f.Ps(tl), f.Ps(hem), f.Ps(tr), f.Ps(top))
    pen.line(tunic, w=1.8, hand=0.45, lift=0.06)
    fine(C(f.Ps([(-0.054, -0.781), (0, -0.773), (0.054, -0.781)]), step=1), w=0.9)          # collar band
    fine(C(f.Ps([(-0.118, -0.58), (0, -0.572), (0.118, -0.58)]), step=1), w=0.85)            # a soft belt
    fine(C(f.Ps([(-0.12, -0.556), (0, -0.549), (0.12, -0.556)]), step=1), w=0.85)
    for x0, x1 in ((-0.05, -0.07), (0.045, 0.07)):
        fine(C(f.Ps([(x0, -0.545), (x1, -0.42)]), step=1), w=0.8)
    rl = f.Ps([(-0.13, -0.74), (-0.123, -0.6), (-0.13, -0.5), (-0.14, -0.41)])
    rr = f.Ps([(0.13, -0.74), (0.123, -0.6), (0.13, -0.5), (0.14, -0.41)])
    lengthwise(C(rl), C(rr), 0.64, 0.97, spacing=5.4, clip=tunic, t0=0.04)
    pen.occlude(tunic)
    # legs in leggings, little boots
    for sgn in (-1, 1):
        ol = [(sgn * 0.106, -0.42), (sgn * 0.098, -0.3), (sgn * 0.09, -0.16), (sgn * 0.084, -0.075)]
        bt = [(sgn * 0.084, -0.075), (sgn * 0.056, -0.071), (sgn * 0.03, -0.075)]
        il = [(sgn * 0.03, -0.075), (sgn * 0.028, -0.2), (sgn * 0.022, -0.32), (sgn * 0.012, -0.42)]
        boot = C(f.Ps([(sgn * 0.088, -0.09), (sgn * 0.091, -0.035), (sgn * 0.083, -0.006), (sgn * 0.058, 0.0),
                       (sgn * 0.032, -0.006), (sgn * 0.026, -0.035), (sgn * 0.028, -0.09)]), step=0.8)
        pen.line(boot, w=1.6, hand=0.25, lift=0)
        fine(C(f.Ps([(sgn * 0.09, -0.02), (sgn * 0.058, -0.016), (sgn * 0.027, -0.02)]), step=1), w=0.8)
        pen.occlude(boot + [boot[0]])
        leg = outline_of(f.Ps(ol), f.Ps(bt), f.Ps(il))
        pen.line(leg, w=1.6, hand=0.35, lift=0.04)
        lit = C(f.Ps([(sgn * 0.02, -0.41), (sgn * 0.028, -0.2), (sgn * 0.03, -0.08)]))
        shd = C(f.Ps([(sgn * 0.104, -0.41), (sgn * 0.092, -0.2), (sgn * 0.084, -0.08)]))
        if sgn < 0:
            lit, shd = shd, lit
        lengthwise(lit, shd, 0.6, 0.96, spacing=5.3, clip=leg + [leg[0]])
        pen.occlude(leg)

    # ------------------------------------------------ the woman
    f = Wf
    u = f.u
    hl_ = [(0, -0.996), (-0.038, -0.99), (-0.058, -0.96), (-0.062, -0.92), (-0.066, -0.875), (-0.082, -0.83),
           (-0.092, -0.77), (-0.091, -0.71), (-0.084, -0.66)]
    tips = [(-0.084, -0.66), (-0.066, -0.63), (-0.05, -0.645), (-0.028, -0.612), (-0.006, -0.634), (0.018, -0.606),
            (0.04, -0.632), (0.062, -0.616), (0.086, -0.662)]
    hr_ = [(0.086, -0.662), (0.093, -0.712), (0.094, -0.772), (0.084, -0.832), (0.068, -0.877), (0.063, -0.92),
           (0.058, -0.96), (0.038, -0.99), (0, -0.996)]
    hair = C(f.Ps(hl_)) + C(f.Ps(tips), step=0.8)[1:] + C(f.Ps(hr_))[1:]
    pen.line(hair, w=1.8, hand=0.45, lift=0.05)
    railL = C(f.Ps(hl_))
    railR = C(f.Ps(list(reversed(hr_))))
    # locks: strands flowing from the crown, waving a little, more of them on the shade side
    N = 40
    A, B = frac_pts(railL, N), frac_pts(railR, N)
    for k, uu in enumerate([0.07, 0.19, 0.31, 0.43, 0.55, 0.66, 0.76, 0.85, 0.93]):
        t0 = 0.04 + 0.1 * abs(uu - 0.5) + R(0, 0.04)
        ph = R(0, 6.3)
        pts = []
        for i in range(N + 1):
            t = i / N
            if t < t0:
                continue
            p = lerp(A[i], B[i], uu)
            off = (1.2 + 1.6 * t) * math.sin(t * 7.5 + ph) * (u / 200)
            pts.append((p[0] + off, p[1] + t * t * 0.01 * u))
        wv = 0.95 if k in (2, 5, 7) else 0.72
        for run in clip_in(C(pts, step=1.5), hair):
            if length(run) > 4:
                fine(run, w=wv, hand=0.35)
    # the light catches the crown: a few short strokes there only
    for k in range(3):
        a = R(0.2, 0.8)
        p0 = lerp(A[3], B[3], a)
        fine([p0, (p0[0] + R(-2, 2), p0[1] + 0.05 * u)], w=0.65)
    pen.occlude(hair)
    # her free left arm, hanging, and the right reaching to the child
    S = f.P((-0.106, -0.788))
    E = f.P((-0.135, -0.625))
    Wl = f.P((-0.127, -0.475))
    hand(Wl, (0.12, 0.99), 0.085 * u, 0.05 * u)
    sleeve(f, S, E, Wl, [0.058 * u, 0.051 * u, 0.045 * u], w=1.7)
    sleeve(f, wS, wE, wW, [0.058 * u, 0.051 * u, 0.045 * u], w=1.7)
    # the dress: a fitted bodice with a sash, a long skirt falling in folds
    dl_ = [(-0.05, -0.86), (-0.088, -0.84), (-0.117, -0.818), (-0.127, -0.792), (-0.114, -0.725), (-0.097, -0.66),
           (-0.089, -0.605), (-0.099, -0.545), (-0.122, -0.43), (-0.148, -0.27), (-0.166, -0.14), (-0.178, -0.046)]
    hem = [(-0.178, -0.046), (-0.15, -0.036), (-0.12, -0.041), (-0.088, -0.033), (-0.05, -0.04), (-0.015, -0.032),
           (0.022, -0.041), (0.058, -0.033), (0.094, -0.042), (0.13, -0.034), (0.158, -0.04), (0.18, -0.046)]
    dr_ = list(reversed(f.mirror(dl_)))
    dr_[0] = (0.18, -0.046)
    top = [(0.05, -0.86), (0, -0.866), (-0.05, -0.86)]
    dress = outline_of(f.Ps(dl_), f.Ps(hem), f.Ps(dr_), f.Ps(top))
    pen.line(dress, w=1.9, hand=0.45, lift=0.06)
    for yy in (-0.614, -0.59):
        fine(C(f.Ps([(-0.094, yy), (-0.04, yy + 0.003), (0.04, yy + 0.003), (0.094, yy)]), step=1), w=1.0)
    # the sash's knot and ends at the back
    fine(C(f.Ps([(0.01, -0.59), (0.022, -0.53), (0.03, -0.48)]), step=1), w=0.9)
    fine(C(f.Ps([(0.028, -0.59), (0.044, -0.535), (0.05, -0.495)]), step=1), w=0.9)
    folds = [[(-0.055, -0.585), (-0.08, -0.33), (-0.118, -0.041)], [(-0.02, -0.585), (-0.03, -0.3), (-0.05, -0.04)],
             [(0.022, -0.585), (0.03, -0.32), (0.022, -0.041)], [(0.06, -0.585), (0.08, -0.32), (0.094, -0.042)],
             [(0.09, -0.48), (0.13, -0.22), (0.158, -0.04)]]
    for fl in folds:
        ln = C(f.Ps(fl), step=1.5)
        fine(ln, w=1.0, hand=0.4)
        ticks(ln, +1, spacing=5.4, L=(3, 8), t0=0.35, t1=0.97, clip=dress, ang=0.6)
    # shade down the right side of the skirt and bodice
    sl = C(f.Ps([(-0.099, -0.545), (-0.122, -0.43), (-0.148, -0.27), (-0.166, -0.14), (-0.178, -0.05)]))
    sr = C(f.Ps([(0.099, -0.545), (0.122, -0.43), (0.148, -0.27), (0.166, -0.14), (0.178, -0.05)]))
    lengthwise(sl, sr, 0.72, 0.97, spacing=5.6, clip=dress, t0=0.03, t1=0.99)
    bl = C(f.Ps([(-0.112, -0.73), (-0.095, -0.66), (-0.089, -0.62)]))
    br = C(f.Ps([(0.112, -0.73), (0.095, -0.66), (0.089, -0.62)]))
    lengthwise(bl, br, 0.66, 0.96, spacing=5.4, clip=dress)
    pen.occlude(dress)
    for sgn in (-1, 1):
        heel = C(f.Ps([(sgn * 0.058, -0.044), (sgn * 0.06, -0.014), (sgn * 0.048, -0.002), (sgn * 0.03, -0.004),
                       (sgn * 0.024, -0.03), (sgn * 0.026, -0.044)]), step=0.8)
        pen.line(heel, w=1.5, hand=0.2, lift=0)

    # ------------------------------------------------ the man
    f = Mf
    u = f.u
    hc = f.P((0, -0.931))
    head = ellipse_pts(hc[0], hc[1], 0.057 * u, 0.067 * u, 0, 0, 2 * math.pi, step=1.0)
    for sgn in (-1, 1):
        ear = f.Ps([(sgn * 0.054, -0.948), (sgn * 0.066, -0.944), (sgn * 0.069, -0.925), (sgn * 0.06, -0.906),
                    (sgn * 0.052, -0.906)])
        pen.line(C(ear, step=0.8), w=1.2, hand=0.2, lift=0)
    pen.line(head, w=1.8, hand=0.35, lift=0.05)
    nape = C(f.Ps([(-0.054, -0.905), (-0.036, -0.887), (-0.012, -0.881), (0.012, -0.882), (0.036, -0.888),
                   (0.054, -0.905)]), step=1)
    fine(nape, w=1.1)
    hair_short(hc, 0.057 * u, 0.067 * u, f.P((0.01, -0.985)), 16, u)
    pen.occlude(head)
    fine(C(f.Ps([(-0.03, -0.884), (-0.033, -0.866)]), step=1), w=1.0)
    fine(C(f.Ps([(0.03, -0.884), (0.033, -0.866)]), step=1), w=1.0)
    # his free right arm, and the left to the child
    S = f.P((0.116, -0.794))
    E = f.P((0.143, -0.63))
    Wr = f.P((0.137, -0.478))
    hand(Wr, (-0.1, 0.995), 0.088 * u, 0.052 * u)
    sleeve(f, S, E, Wr, [0.068 * u, 0.059 * u, 0.051 * u], w=1.8)
    sleeve(f, mS, mE, mW, [0.068 * u, 0.059 * u, 0.051 * u], w=1.8)
    # the coat: a stand collar, a yoke, a back seam and vent, a waist seam
    cl_ = [(-0.052, -0.868), (-0.094, -0.849), (-0.128, -0.828), (-0.141, -0.80), (-0.13, -0.745), (-0.113, -0.70),
           (-0.105, -0.605), (-0.111, -0.50), (-0.12, -0.40), (-0.127, -0.335)]
    hem = [(-0.127, -0.335), (-0.06, -0.329), (0.0, -0.331), (0.06, -0.329), (0.127, -0.335)]
    cr_ = list(reversed(f.mirror(cl_)))
    top = [(0.052, -0.868), (0, -0.876), (-0.052, -0.868)]
    coat = outline_of(f.Ps(cl_), f.Ps(hem), f.Ps(cr_), f.Ps(top))
    pen.line(coat, w=2.0, hand=0.45, lift=0.06)
    fine(C(f.Ps([(-0.056, -0.85), (0, -0.854), (0.056, -0.85)]), step=1), w=1.0)        # collar
    fine(C(f.Ps([(-0.126, -0.79), (-0.06, -0.778), (0, -0.776), (0.06, -0.778), (0.126, -0.79)]), step=1), w=0.85)
    fine(C(f.Ps([(0, -0.854), (0.0, -0.65), (0.001, -0.45)]), step=1), w=1.0)          # back seam
    fine(C(f.Ps([(0.001, -0.45), (0.006, -0.39), (0.007, -0.333)]), step=1), w=1.0)    # the vent
    fine(C(f.Ps([(0.001, -0.45), (-0.004, -0.39), (-0.005, -0.333)]), step=1), w=0.8)
    fine(C(f.Ps([(-0.106, -0.606), (-0.05, -0.598), (0, -0.597), (0.05, -0.598), (0.106, -0.606)]), step=1), w=0.9)
    for fl in ([(-0.07, -0.59), (-0.08, -0.47), (-0.088, -0.345)], [(0.066, -0.59), (0.078, -0.47), (0.09, -0.345)],
               [(-0.06, -0.77), (-0.064, -0.70), (-0.066, -0.625)], [(0.055, -0.77), (0.058, -0.70), (0.06, -0.625)]):
        ln = C(f.Ps(fl), step=1.5)
        fine(ln, w=0.9, hand=0.35)
        ticks(ln, +1, spacing=5.6, L=(3, 7), t0=0.3, t1=0.95, clip=coat, ang=0.5)
    ul = C(f.Ps([(-0.13, -0.77), (-0.113, -0.70), (-0.106, -0.615)]))
    ur = C(f.Ps([(0.13, -0.77), (0.113, -0.70), (0.106, -0.615)]))
    lengthwise(ul, ur, 0.66, 0.97, spacing=5.5, clip=coat)
    ll = C(f.Ps([(-0.106, -0.592), (-0.111, -0.50), (-0.12, -0.40), (-0.127, -0.34)]))
    lr = C(f.Ps([(0.106, -0.592), (0.111, -0.50), (0.12, -0.40), (0.127, -0.34)]))
    lengthwise(ll, lr, 0.7, 0.97, spacing=5.5, clip=coat)
    pen.occlude(coat)
    # trousers and shoes
    for sgn in (-1, 1):
        shoe = C(f.Ps([(sgn * 0.075, -0.06), (sgn * 0.077, -0.02), (sgn * 0.068, -0.003), (sgn * 0.047, 0.0),
                       (sgn * 0.025, -0.003), (sgn * 0.019, -0.02), (sgn * 0.021, -0.06)]), step=0.8)
        pen.line(shoe, w=1.7, hand=0.2, lift=0)
        fine(C(f.Ps([(sgn * 0.076, -0.014), (sgn * 0.047, -0.01), (sgn * 0.02, -0.014)]), step=1), w=0.85)
        pen.occlude(shoe + [shoe[0]])
        ol = [(sgn * 0.1, -0.35), (sgn * 0.091, -0.25), (sgn * 0.081, -0.14), (sgn * 0.073, -0.052)]
        bt = [(sgn * 0.073, -0.052), (sgn * 0.047, -0.046), (sgn * 0.021, -0.052)]
        il = [(sgn * 0.021, -0.052), (sgn * 0.021, -0.2), (sgn * 0.016, -0.35)]
        leg = outline_of(f.Ps(ol), f.Ps(bt), f.Ps(il))
        pen.line(leg, w=1.8, hand=0.35, lift=0.04)
        inner = C(f.Ps([(sgn * 0.017, -0.345), (sgn * 0.021, -0.2), (sgn * 0.022, -0.06)]))
        outer = C(f.Ps([(sgn * 0.099, -0.345), (sgn * 0.09, -0.25), (sgn * 0.08, -0.14), (sgn * 0.073, -0.06)]))
        lit, shd = (outer, inner) if sgn < 0 else (inner, outer)
        lengthwise(lit, shd, 0.58, 0.96, spacing=5.4, clip=leg)
        # creases behind the knee
        for yy in (-0.235, -0.218):
            fine(C(f.Ps([(sgn * 0.03, yy), (sgn * 0.055, yy + 0.004), (sgn * 0.078, yy)]), step=1), w=0.7)
        pen.occlude(leg)


# ---------------------------------------------------------------- plants

def blade(base, h, lean, w=1.0, curl=0.0):
    x, y = base
    tip = (x + lean * h, y - h)
    mid = (x + lean * h * 0.4 + curl * h * 0.15, y - h * 0.55)
    pen.line(catmull([base, mid, tip], step=2), w=w, hand=0.25, lift=0.02, taper=0.6, piece=(30, 90))


def tuft(x, y, h, n=5, spread=0.5, w=1.0, lean=0.0, occ=False):
    for k in range(n):
        u = (k + 0.5) / n - 0.5
        blade((x + u * h * 0.18, y + abs(u) * 2), h * R(0.6, 1.0), lean + u * spread + G(0.08), w=w * R(0.85, 1.1),
              curl=G(0.5))
    if occ:
        # the tuft hides what stands behind it, near its foot
        pen.occlude([(x - h * 0.16, y + 2), (x + h * 0.16, y + 2), (x + lean * h * 0.5 + h * 0.05, y - h * 0.55),
                     (x + lean * h * 0.5 - h * 0.05, y - h * 0.55)])


def front_grass(x0, x1, y, n, h):
    """Tufts along the feet of the people, drawn before them so they stand in the grass."""
    for k in range(n):
        x = x0 + (x1 - x0) * (k + R(0.1, 0.9)) / n
        tuft(x, y + R(-2, 6), h * R(0.7, 1.15), n=int(R(3, 6)), w=1.0, lean=R(-0.15, 0.2), occ=True)


def daisy(x, y, h, r, lean=0.0, w=1.0):
    head = (x + lean * h, y - h)
    pen.line(catmull([(x, y), (x + lean * h * 0.3 + G(1), y - h * 0.5), head], step=2), w=w * 0.9, hand=0.2,
             lift=0)
    pen.line(ellipse_pts(head[0], head[1], r * 0.32, r * 0.3, 0, 0, 2 * math.pi, step=0.8), w=w * 1.1, hand=0,
             lift=0)
    for k in range(9):
        a = 2 * math.pi * k / 9 + R(-0.1, 0.1)
        p0 = (head[0] + math.cos(a) * r * 0.45, head[1] + math.sin(a) * r * 0.42)
        p1 = (head[0] + math.cos(a) * r, head[1] + math.sin(a) * r * 0.85)
        pen.line([p0, p1], w=w * 0.85, hand=0, lift=0)


def umbel(x, y, h, r, lean=0.0, w=1.0):
    top = (x + lean * h, y - h)
    pen.line(catmull([(x, y), (x + lean * h * 0.35, y - h * 0.5), top], step=2), w=w * 0.9, hand=0.2, lift=0)
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.3
        tip = (top[0] + math.cos(a) * r, top[1] + math.sin(a) * r * 0.75)
        pen.line([top, tip], w=0.7, hand=0, lift=0)
        dot(tip[0], tip[1], r=1.0, w=1.0)


def frond(base, angle, L, curl=0.25, w=1.2, side_len=0.22):
    """A fern frond: a curved stem with leaflets in pairs, shorter toward the tip."""
    pts = []
    for k in range(13):
        t = k / 12
        a = angle + curl * t * t * 2.2
        if pts:
            px, py = pts[-1]
            pts.append((px + math.cos(a) * L / 12, py + math.sin(a) * L / 12))
        else:
            pts.append(base)
    rach = catmull(pts, step=2)
    pen.line(rach, w=w, hand=0.25, lift=0.02, taper=0.5)
    fine = resample(rach, 10.0)
    for i in range(1, len(fine) - 1):
        t = i / (len(fine) - 1)
        a, b = fine[i - 1], fine[i + 1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        tx, ty = tx / tl, ty / tl
        ln = L * side_len * (1 - t) ** 0.8 + 3
        for s in (1, -1):
            nx, ny = -ty * s, tx * s
            q = fine[i]
            tip = (q[0] + (nx * 0.8 + tx * 0.6) * ln, q[1] + (ny * 0.8 + ty * 0.6) * ln)
            pen.line(catmull([q, ((q[0] + tip[0]) / 2 + tx * 1.5, (q[1] + tip[1]) / 2 + ty * 1.5), tip], step=2),
                     w=0.75, hand=0.15, lift=0, taper=0.4)


# ---------------------------------------------------------------- roads and ways

def road_edges(ctrl, W, elev=None, n=400):
    """A road drawn from its centreline (control points on the page, where it
    would lie on the plain), W metres wide, optionally lifted by elev(t) metres.
    Returns the near and far edge on the page, the centreline, and the ground
    points (for pylons)."""
    cl = catmull(ctrl, step=0.6)
    cl = resample(cl, max(0.5, length(cl) / n))
    wpts = [ground_of(x, max(y, YH + 0.8)) for x, y in cl]
    left, right, mid, foot = [], [], [], []
    for i, (X, Z) in enumerate(wpts):
        a = wpts[max(0, i - 1)]
        b = wpts[min(len(wpts) - 1, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz) or 1
        nx, nz = -tz / L, tx / L
        Y = elev(i / (len(wpts) - 1)) if elev else 0.0
        left.append(P(X + nx * W / 2, Y, Z + nz * W / 2))
        right.append(P(X - nx * W / 2, Y, Z - nz * W / 2))
        mid.append(P(X, Y, Z))
        foot.append((X, Z, Y))
    return left, right, mid, foot


def weighted(pts, wfn, hand=0.15, pieces=12):
    """A stroke whose weight changes along it (wfn of the page y), in pieces that meet."""
    n = len(pts)
    step = max(2, n // pieces)
    for i in range(0, n - 1, step):
        seg = pts[i:min(n, i + step + 1)]
        if len(seg) >= 2:
            y = seg[len(seg) // 2][1]
            pen.line(seg, w=wfn(y), hand=hand, lift=0, piece=(200, 400))


def depth_w(near, far):
    span = 1000 - YH
    return lambda y: far + (near - far) * clamp((y - YH) / span, 0, 1) ** 0.8


def ground_road(ctrl, W):
    left, right, mid, _ = road_edges(ctrl, W)
    wf = depth_w(2.0, 0.8)
    weighted(left, wf)
    weighted(right, wf)
    # the centre line, fine, and two lane lines
    wc = depth_w(1.0, 0.6)
    weighted(mid, wc)
    # tone: fine lines along the road near the edges, to give it a surface
    for f in (0.18, 0.82):
        lane = [lerp(a, b, f) for a, b in zip(left, right)]
        cut = [p for p in lane if p[1] > YH + 6]
        if len(cut) > 2:
            weighted(cut, depth_w(0.8, 0.6))
    poly = left + list(reversed(right))
    pen.occlude(poly)
    return left, right


def skyway(ctrl, W, elev, pylon_every=60.0, min_sep=34.0):
    left, right, mid, foot = road_edges(ctrl, W, elev)
    # deck: near edge, far edge, and the fascia below the near edge
    near = left if sum(p[1] for p in left) > sum(p[1] for p in right) else right
    far = right if near is left else left
    wf = depth_w(2.0, 0.8)
    weighted(near, wf)
    weighted(far, depth_w(1.4, 0.7))
    under = []
    for (X, Z, Y), p in zip(foot, near):
        under.append((p[0], p[1] + F * 1.6 / Z))
    weighted(under, depth_w(1.6, 0.7))
    pen.occlude(far + list(reversed(under)))
    # piers: tapered, flaring into the deck, a fixed distance apart along the
    # way (and never closer than min_sep on the page), so they recede in depth
    cum = [0.0]
    for a, b in zip(foot, foot[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    nxt = pylon_every * 0.6
    last = None
    for i, (X, Z, Y) in enumerate(foot):
        if cum[i] < nxt:
            continue
        nxt += pylon_every
        top, bot = P(X, Y - 1.6, Z), P(X, 0, Z)
        ht = bot[1] - top[1]
        if ht < 14 or (last and abs(bot[0] - last[0]) < min_sep):
            continue
        if not (0 < bot[0] < 1000):
            continue
        last = bot
        ht_w, mid_w, foot_w = F * 2.3 / Z, F * 0.95 / Z, F * 1.3 / Z
        lpts = C([(top[0] - ht_w, top[1]), (top[0] - mid_w * 1.25, top[1] + ht * 0.16), (bot[0] - mid_w, top[1] + ht * 0.55),
                  (bot[0] - foot_w, bot[1])], step=1.5)
        rpts = C([(top[0] + ht_w, top[1]), (top[0] + mid_w * 1.25, top[1] + ht * 0.16), (bot[0] + mid_w, top[1] + ht * 0.55),
                  (bot[0] + foot_w, bot[1])], step=1.5)
        wp = clamp(F * 0.03 / Z * 30, 0.75, 1.9)
        pen.line(lpts, w=wp * 0.9, hand=0.1, lift=0)
        pen.line(rpts, w=wp * 1.1, hand=0.1, lift=0)
        poly = lpts + list(reversed(rpts))
        if mid_w > 4:
            cen = [lerp(a, b, 0.5) for a, b in zip(lpts, rpts)]
            lengthwise(cen, rpts, 0.35, 0.92, spacing=5.2, clip=poly, w=0.65, t0=0.12)
        pen.line([(bot[0] - foot_w * 1.6, bot[1]), (bot[0] + foot_w * 3, bot[1] + 0.5)], w=0.7, hand=0.1, lift=0)
        pen.occlude(poly)
    return near, far


# ---------------------------------------------------------------- the city

def tower_needle(x, base, w, h):
    half = [(0.0, -h), (w * 0.06, -h * 0.93), (w * 0.2, -h * 0.72), (w * 0.36, -h * 0.4), (w * 0.5, 0.0)]
    pts = catmull(half, step=2)
    return [(x + px, base + py) for px, py in pts] + [(x - px, base + py) for px, py in reversed(pts)]


def tower_shaft(x, base, w, h, top_taper=0.7):
    half = [(0.0, -h - w * 0.4), (w * 0.3, -h - w * 0.1), (w * 0.5 * top_taper, -h), (w * 0.5 * (0.5 + top_taper / 2), -h * 0.5),
            (w * 0.5, 0.0)]
    pts = catmull(half, step=2)
    return [(x + px, base + py) for px, py in pts] + [(x - px, base + py) for px, py in reversed(pts)]


def span_at(poly, y):
    """Where a horizontal line at y crosses a polygon: (left x, right x) or None."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return (min(xs), max(xs)) if len(xs) >= 2 else None


def tower_detail(poly, kind, x, b, w, h, depth):
    """Banding and window rows: bands right across the tower; rows of windows
    on its lit face only, in groups, fewer on the far towers; the shaded face
    carries the vertical hatching."""
    if kind in ('needle', 'ring'):
        bands = (0.14, 0.31, 0.47)
        groups = ((0.02, 0.12), (0.17, 0.28), (0.34, 0.44))
    elif kind == 'disc':
        bands = (0.2, 0.42, 0.62)
        groups = ((0.04, 0.17), (0.25, 0.38), (0.46, 0.58))
    else:
        bands = (0.3, 0.62)
        groups = ((0.06, 0.26), (0.36, 0.56), (0.66, 0.86))
    for f in bands:
        sp = span_at(poly, b - h * f)
        if sp and sp[1] - sp[0] > 3:
            pen.line([(sp[0] + 0.4, b - h * f), (sp[1] - 0.4, b - h * f - 0.3)], w=0.65, hand=0, lift=0)
    if depth >= 2.8 or w < 11:
        return
    for g0, g1 in groups[: (3 if depth < 1.6 else 2)]:
        y = b - h * g0 - 3.0
        while y > b - h * g1:
            sp = span_at(poly, y)
            if sp:
                x0, x1 = sp[0] + 1.6, min(sp[1] - 1.0, x + (sp[1] - sp[0]) * 0.08)
                if x1 - x0 > 3:
                    pen.line([(x0, y), (x1, y)], w=0.6, hand=0, lift=0.5, piece=(2.2, 4.5))
            y -= 5.5


def city(cx, base, s, wline=1.1):
    """The metropolis on the horizon, s = scale. Returns its outline polygons."""
    towers = []

    def T(kind, dx, w, h, depth, **kw):
        towers.append(dict(kind=kind, x=cx + dx * s, w=w * s, h=h * s, depth=depth, kw=kw))

    # landmark: a very tall needle with rings round it
    T('ring', 0, 30, 340, 1.0)
    T('needle', -96, 24, 255, 1.5)
    T('needle', 92, 22, 280, 1.2)
    T('needle', 178, 16, 175, 2.4)
    T('needle', -180, 18, 168, 2.1)
    T('disc', -44, 13, 210, 0.8)
    T('disc', 50, 12, 228, 2.6)
    T('disc', 240, 10, 120, 2.0)
    T('arch', -140, 56, 112, 0.5)
    T('slab', 132, 36, 122, 0.6)
    T('slab', -232, 28, 84, 1.0)
    T('slab', 226, 30, 96, 1.3)
    T('dome', -118, 62, 40, 0.15)
    T('dome', 205, 38, 25, 0.3)
    T('dome', 18, 44, 28, 0.1)
    for k in range(16):
        dx = -270 + k * 36 + R(-10, 10)
        T('shaft', dx, R(10, 18), R(40, 120), 3.0 + R(0, 0.5))
    towers.sort(key=lambda t: t['depth'])
    outlines = []
    for t in towers:
        x, w, h = t['x'], t['w'], t['h']
        b = base + (3.2 - t['depth']) * 1.2 * s
        wl = wline * (1.0 if t['depth'] < 2 else 0.85)
        kind = t['kind']
        if kind in ('needle', 'ring'):
            poly = tower_needle(x, b, w, h)
        elif kind in ('shaft', 'slab'):
            poly = tower_shaft(x, b, w, h, top_taper=0.85 if kind == 'slab' else 0.6)
        elif kind == 'disc':
            poly = tower_shaft(x, b, w, h * 0.78, top_taper=0.8)
        elif kind == 'arch':
            outer = ellipse_pts(x, b, w / 2, h, 0, math.pi, 2 * math.pi, step=2)
            poly = outer
        elif kind == 'dome':
            poly = ellipse_pts(x, b, w, h, 0, math.pi, 2 * math.pi, step=2)
        # decorations drawn first (they are in front of the body)
        if kind == 'ring':
            for f, rr in ((0.5, 1.9), (0.64, 1.6), (0.78, 1.3)):
                yy = b - h * f
                half_w = w * 0.5 * (1 - f) ** 0.9 + 2
                ring = ellipse_pts(x, yy, half_w * rr + 4 * s, 4.5 * s, 0, 0, math.pi, step=1.5)
                pen.line(ring, w=wl, hand=0.1, lift=0)
                back = ellipse_pts(x, yy, half_w * rr + 4 * s, 4.5 * s, 0, math.pi, 2 * math.pi, step=1.5)
                band = ring + back
                pen.occlude([(p[0], p[1] + 0.6) for p in ellipse_pts(x, yy, half_w * rr + 4 * s, 4.5 * s, 0, 0, math.pi, step=2)]
                            + [(x - half_w * rr - 4 * s, yy - 0.5), (x + half_w * rr + 4 * s, yy - 0.5)])
                pen.line(back, w=wl * 0.8, hand=0.1, lift=0)
            sparkle(x, b - h - 4 * s, 9 * s, w=1.0)
        if kind == 'disc':
            yy = b - h * 0.78
            rx = w * 2.1
            disc = ellipse_pts(x, yy, rx, rx * 0.22, 0, 0, 2 * math.pi, step=1.5)
            pen.line(disc, w=wl, hand=0.1, lift=0)
            cap = ellipse_pts(x, yy - rx * 0.12, w * 0.7, w * 0.55, 0, math.pi, 2 * math.pi, step=1.5)
            pen.line(cap, w=wl, hand=0.1, lift=0)
            pen.line([(x, yy - rx * 0.12 - w * 0.55), (x, b - h)], w=wl * 0.9, hand=0, lift=0)
            pen.occlude(disc)
            pen.occlude(cap + [cap[0]])
            if t['depth'] < 2.2:
                sparkle(x - rx * 0.86, yy - 0.5, 4.0 * s, w=0.85, diag=0.0)
        if kind == 'arch':
            inner = ellipse_pts(x, b, w / 2 - 7 * s, h - 10 * s, 0, math.pi, 2 * math.pi, step=2)
            pen.line(inner, w=wl, hand=0.1, lift=0)
            pen.line(outer, w=wl, hand=0.1, lift=0)
            band = outer + list(reversed(inner))
            shade(band, 90, 5.0, w=0.65, keep=lambda p, x=x: p[0] > x, hand=0.1)
            pen.occlude(band)
            outlines.append(band)
            continue
        pen.line(poly, w=wl, hand=0.12, lift=0)
        if kind == 'dome':
            for f in (-0.5, 0.0, 0.5):
                mer = ellipse_pts(x, b, w * abs(f) + 0.01, h, 0, math.pi * (1.5 if f >= 0 else 1.0),
                                  math.pi * (2.0 if f >= 0 else 1.5), step=1.5)
                if f != 0:
                    pen.line(mer, w=0.65, hand=0, lift=0)
            pen.line([(x, b - h), (x, b)], w=0.65, hand=0, lift=0)
            lat = ellipse_pts(x, b - h * 0.55, w * 0.83, h * 0.1, 0, 0, math.pi, step=1.5)
            pen.line(lat, w=0.65, hand=0, lift=0)
        else:
            # shade side: fine vertical lines on the right
            shade(poly, 90, 5.0 if w > 14 else 6.0, w=0.65, keep=lambda p, x=x, w=w: p[0] > x + w * 0.12, hand=0.1,
                  shrink=(0.0, 0.05))
            tower_detail(poly, kind, x, b, w, h * (0.78 if kind == 'disc' else 1.0), t['depth'])
        if kind in ('needle', 'ring') and h > 150 * s:
            sparkle(x, b - h - 3 * s, 7 * s, w=0.9, diag=0.0)
        pen.occlude(poly)
        outlines.append(poly)
    return outlines


def skybridge(x0, x1, y, sag, w=0.9):
    pts = catmull([(x0, y), ((x0 + x1) / 2, y + sag), (x1, y)], step=2)
    pen.line(pts, w=w, hand=0.1, lift=0)
    pen.line([(x, yy + 3) for x, yy in pts], w=0.7, hand=0.1, lift=0)


# ---------------------------------------------------------------- the sky

def constellation(cx, cy, sizes, W, H, rot=0.0, node=2.2, link=0.6, gap=6.0):
    """A neural network as a constellation: stars as nodes, fine links between
    the layers (each node of one layer to every node of the next)."""
    c, s_ = math.cos(rot), math.sin(rot)
    layers = []
    for li, n in enumerate(sizes):
        u = (li / (len(sizes) - 1) - 0.5) * W
        col = []
        for k in range(n):
            v = ((k - (n - 1) / 2) / max(1, max(sizes) - 1)) * H
            px, py = u + G(1.2), v + G(1.2)
            col.append((cx + px * c - py * s_, cy + px * s_ + py * c))
        layers.append(col)
    for li in range(len(layers) - 1):
        for a in layers[li]:
            for b in layers[li + 1]:
                d = dist(a, b)
                if d < 2 * gap + 4:
                    continue
                pen.line([lerp(a, b, gap / d), lerp(a, b, 1 - gap / d)], w=link, hand=0, lift=0, piece=(300, 500))
    nodes = [p for col in layers for p in col]
    for li, col in enumerate(layers):
        for p in col:
            if li in (0, len(layers) - 1) and R() < 0.5:
                sparkle(p[0], p[1], node * 3.2, w=1.1, rot=R(-0.2, 0.2), diag=0.0)
            else:
                dot(p[0], p[1], r=node, w=1.4)
    return nodes


def starfield(n, region, avoid, minsep=20):
    """Plain stars: dots of a few sizes, a handful of sparkles."""
    placed = []
    tries = 0
    x0, y0, x1, y1 = region
    while len(placed) < n and tries < n * 40:
        tries += 1
        p = (R(x0, x1), R(y0, y1))
        if any(dist(p, q) < minsep for q in placed) or any(f(p) for f in avoid):
            continue
        placed.append(p)
    for i, p in enumerate(placed):
        if pen.hidden(p):
            continue
        u = R()
        if u < 0.06:
            sparkle(p[0], p[1], R(7, 12), w=1.15, rot=R(-0.1, 0.1))
        elif u < 0.35:
            dot(p[0], p[1], r=R(1.3, 1.8), w=1.25)
        else:
            dot(p[0], p[1], r=R(0.8, 1.2), w=1.0)


# ---------------------------------------------------------------- ground

def plain_marks(n, x_range, y_far=4.0):
    """Short level strokes on the plain, shorter and closer toward the horizon."""
    for _ in range(n):
        sy = YH + y_far + (1000 - YH - y_far) * R() ** 1.8
        sx = R(*x_range)
        X, Z = ground_of(sx, sy)
        L = R(6, 16)
        p0, p1 = P(X - L / 2, 0, Z), P(X + L / 2, 0, Z)
        if p1[0] - p0[0] < 3:
            continue
        pen.line([p0, p1], w=0.7, hand=0.2, lift=0.1)



def region_hatch(poly, angle, spacing, pred, w=0.68, minlen=3.0, hand=0.2, broken=False):
    """Parallel strokes across a shape, kept only where pred(point) holds."""
    for p0, p1 in scanlines(poly, angle, spacing, R()):
        for run in clip_segments([p0, p1], pred):
            if length(run) < minlen:
                continue
            seg = [run[0], run[-1]]
            if broken:
                pen.line(seg, w=w * R(0.88, 1.1), hand=hand, lift=0.45, piece=(4, 10))
            else:
                pen.line(seg, w=w * R(0.88, 1.1), hand=hand, lift=0.05, piece=(30, 90))


def crown_shape(cx, cy, R0, lobes, scallop):
    """The outline of a crown made of round lobes (their union, seen from its
    middle), edged with small leafy scallops."""
    N = max(48, int(2 * math.pi * R0 / 1.2))
    out = []
    for k in range(N):
        a = 2 * math.pi * k / N
        ux, uy = math.cos(a), math.sin(a)
        best = 0.0
        for lx, ly, lr in lobes:
            ox, oy = cx - lx, cy - ly
            b = ox * ux + oy * uy
            disc = b * b - (ox * ox + oy * oy - lr * lr)
            if disc >= 0:
                best = max(best, -b + math.sqrt(disc))
        out.append((cx + ux * best, cy + uy * best))
    if scallop > 0:
        per = max(5.0, R0 / 3.5)
        pts = resample(out + [out[0]], 0.8)
        s = 0.0
        res = []
        for i, p in enumerate(pts):
            if i:
                s += dist(pts[i - 1], p)
            dx, dy = p[0] - cx, p[1] - cy
            L = math.hypot(dx, dy) or 1
            bump = scallop * abs(math.sin(math.pi * s / per)) ** 0.6
            res.append((p[0] + dx / L * bump, p[1] + dy / L * bump))
        out = res
    return out


def tree(bx, by, h, w=None):
    """A round-crowned broadleaf tree, its foot at (bx, by), h tall on the page:
    a crown of lobes lit from the upper left, the lobes on the shade side
    edged and hatched, a short trunk and a cast-shadow stroke. Skipped (False)
    where it would run into something already drawn in front of it."""
    if h < 5:
        return False
    R0 = h * R(0.33, 0.4)
    cx, cy = bx + G(h * 0.02), by - h + R0 * 1.02
    m = 7 if h > 30 else 5
    lobes = [(cx, cy + R0 * 0.08, R0 * 0.62)]
    for k in range(m):
        a = -math.pi / 2 + 2 * math.pi * (k + R(-0.18, 0.18)) / m
        lr = R0 * R(0.42, 0.54)
        d = R0 - lr
        lobes.append((cx + math.cos(a) * d * 1.05, cy + math.sin(a) * d * 0.9, lr))
    crown = crown_shape(cx, cy, R0, lobes, scallop=min(2.0, R0 * 0.07) if h > 12 else 0.0)
    tb = cy + R0 * 0.55
    tw0, tw1 = max(1.2, h * 0.055), max(0.9, h * 0.035)
    lean = G(h * 0.015)
    trunk = [(bx - tw0, by), (bx - tw1 + lean, tb), (bx + tw1 + lean, tb), (bx + tw0, by)]
    probe = crown[::3] + trunk + [(bx - h * 0.3, by), (bx + h * 0.4, by)]
    if any(pen.hidden(q) for q in probe):
        return False
    if w is None:
        w = clamp(0.7 + h / 55, 0.75, 1.6)
    pen.line(crown, w=w, hand=0.3, lift=0.05)
    if h > 20:
        # inner lobe edges, on each lobe's shade side, where it overlaps the crown
        inner = [(cx + (p[0] - cx) * 0.93, cy + (p[1] - cy) * 0.93) for p in crown]
        for lx, ly, lr in lobes[1:]:
            if ly < cy - R0 * 0.25:
                continue
            arc = ellipse_pts(lx, ly, lr, lr, 0, math.radians(-25), math.radians(150), step=1.0)
            for run in clip_segments(arc, lambda p: inside(p, inner)):
                if length(run) > 4:
                    pen.line(run, w=w * 0.6, hand=0.3, lift=0.2, piece=(6, 14))
    # shade: stronger toward the crown's lower right, and on each lobe's own lower right

    def shade_at(p):
        g = ((p[0] - cx) * SHADE[0] + (p[1] - cy) * SHADE[1]) / R0
        lb = -1.0
        for lx, ly, lr in lobes:
            dd = math.hypot(p[0] - lx, p[1] - ly)
            if dd < lr:
                lb = max(lb, ((p[0] - lx) * SHADE[0] + (p[1] - ly) * SHADE[1]) / lr)
        return 0.65 * g + 0.45 * lb
    if h > 9:
        sp = 5.2 if h > 30 else 5.6
        region_hatch(crown, -50, sp, lambda p: inside(p, crown) and shade_at(p) > 0.28, w=0.68, minlen=2.5,
                     broken=h > 24)
        if h > 40:
            region_hatch(crown, 20, 6.0, lambda p: inside(p, crown) and shade_at(p) > 0.62, w=0.65, minlen=2.5,
                         broken=True)
    else:
        for k in range(3):
            a = R(0.2, 1.2)
            p = (cx + math.cos(a) * R0 * 0.55, cy + math.sin(a) * R0 * 0.55)
            pen.line([p, (p[0] + R0 * 0.35, p[1] - R0 * 0.3)], w=0.65, hand=0.1, lift=0)
    pen.occlude(crown)
    pen.line([trunk[0], trunk[1]], w=w * 0.95, hand=0.2, lift=0)
    pen.line([trunk[3], trunk[2]], w=w * 1.05, hand=0.2, lift=0)
    if tw0 > 3:
        pen.line([lerp(trunk[0], trunk[3], 0.7), lerp(trunk[1], trunk[2], 0.7)], w=0.65, hand=0.2, lift=0)
    pen.occlude(trunk)
    # the shadow it casts on the grass
    pen.line([(bx - h * 0.12, by + 0.6), (bx + h * 0.42, by + 1.2)], w=0.75, hand=0.2, lift=0.3, piece=(6, 14))
    return True


def groves(specs, spread=1.0):
    """Several groves on the plain, every tree drawn nearest first, so the
    nearer ones hide the farther. specs: (page x, page y, count)."""
    cand = []
    for sx, sy, n in specs:
        X0, Z0 = ground_of(sx, sy)
        for _ in range(n):
            X = X0 + G(spread) * Z0 / F * 40
            Z = max(40.0, Z0 * (1 + G(0.12)))
            cand.append((Z, X, R(10, 16)))
    cand.sort()
    for Z, X, Hm in cand:
        b = P(X, 0, Z)
        tree(b[0], b[1], F * Hm / Z)


def horizon_line(x0, x1, y):
    pen.line([(x0, y), (x1, y)], w=1.0, hand=0.4, lift=0.35, piece=(30, 90))


def hills(pts, w=0.9, hatch=True):
    line = catmull(pts, step=2)
    pen.line(line, w=w, hand=0.4, lift=0.15)
    return line


# =============================================================== draft A
if VARIANT == 'A':
    # the knoll the people stand on, at the left
    knoll_top = catmull([(20, 846), (110, 808), (210, 792), (320, 792), (420, 812), (500, 846), (570, 890),
                         (630, 940), (660, 1000)], step=2)
    # people: a man, a child and a woman, looking out to the city
    front_grass(160, 420, 801, 9, 26)
    family(286, 800, 220)
    # foreground plants on the knoll
    for k in range(40):
        x = R(30, 600)
        yk = min(knoll_top, key=lambda p: abs(p[0] - x))[1]
        y = yk + R(4, 120) * (R() ** 1.5)
        if y > 960:
            continue
        tuft(x, y, R(18, 42) * (1 + (y - 780) / 260), n=int(R(3, 7)), w=1.0, lean=R(-0.15, 0.25))
    for (x, y, h, r) in [(120, 845, 70, 9), (160, 880, 56, 8), (420, 838, 60, 8), (470, 880, 48, 7), (80, 900, 40, 7)]:
        daisy(x, y, h, r, lean=R(-0.1, 0.15))
    for (x, y, h, r) in [(205, 850, 82, 12), (380, 880, 66, 10)]:
        umbel(x, y, h, r, lean=R(-0.08, 0.08))
    for (bx, by, a, L) in [(40, 975, -1.25, 150), (75, 985, -0.7, 170)]:
        frond((bx, by), a, L, curl=0.35)
    pen.line(knoll_top, w=2.0, hand=0.7, lift=0.15)
    # a little tone on the knoll's face, following the slope
    for k in range(40):
        x = R(60, 640)
        yk = min(knoll_top, key=lambda p: abs(p[0] - x))[1]
        y = yk + R(10, 150)
        if y > 990:
            continue
        L = R(14, 34)
        slope = 0.35 if x > 380 else 0.05
        pen.line([(x - L / 2, y - slope * L / 2), (x + L / 2, y + slope * L / 2)], w=0.72, hand=0.3, lift=0.1)
    pen.occlude(knoll_top + [(1000, 1000), (0, 1000), (0, 828)])

    # grass on the near verge at the lower right
    for k in range(12):
        x = R(780, 970)
        y = R(930, 990)
        tuft(x, y, R(24, 46), n=int(R(3, 6)), w=1.05, lean=R(-0.2, 0.1))

    # the road: sweeps up from the lower right into the valley and on to the city
    ground_road([(860, 1010), (760, 880), (640, 760), (590, 690), (612, 648), (648, 622), (654, 608), (650, 603.5)], 9.0)
    # the skyway: comes in on pylons from the right
    skyway([(1010, 700), (900, 672), (820, 640), (775, 620), (740, 608), (705, 603)], 7.0,
           elev=lambda t: 26 + 50 * t ** 1.5, pylon_every=70.0, min_sep=38.0)

    groves([(470, 640, 4), (540, 625, 3), (720, 640, 5), (860, 618, 3), (420, 612, 3), (585, 607, 3), (940, 660, 3)])

    # the city
    outlines = city(650, YH + 1.5, 1.0, wline=1.1)
    skybridge(560, 650, 470, 8)
    skybridge(650, 742, 430, 7)
    skybridge(470, 554, 520, 5)

    # the far land: low hills either side, the horizon, marks on the plain
    hills([(30, 604), (90, 596), (170, 590), (260, 594), (330, 586), (420, 594), (470, 600)])
    hills([(860, 598), (910, 590), (970, 596)])
    horizon_line(30, 970, YH + 4)
    plain_marks(110, (30, 970))

    # the sky: four neural-net constellations among plain stars
    nets = [
        dict(cx=235, cy=215, sizes=[3, 4, 4, 2], W=270, H=165, rot=-0.10),
        dict(cx=805, cy=125, sizes=[3, 4, 2], W=170, H=110, rot=0.12),
        dict(cx=110, cy=455, sizes=[2, 3, 1], W=110, H=70, rot=0.05),
        dict(cx=500, cy=82, sizes=[2, 3, 2], W=120, H=70, rot=-0.18),
    ]
    boxes = []
    for nt in nets:
        constellation(nt['cx'], nt['cy'], nt['sizes'], nt['W'], nt['H'], nt['rot'])
        boxes.append((nt['cx'], nt['cy'], nt['W'] / 2 + 22, nt['H'] / 2 + 22))
    avoid = [lambda p, b=b: abs(p[0] - b[0]) < b[2] and abs(p[1] - b[1]) < b[3] for b in boxes]
    starfield(120, (25, 25, 975, YH - 12), avoid)

# =============================================================== draft B
else:
    # people near the bottom, on the verge left of the road, looking up it to the city
    front_grass(210, 500, 931, 10, 30)
    family(356, 930, 244)
    # foreground nature along the bottom
    for k in range(30):
        x = R(30, 970)
        y = R(890, 990)
        if 470 < x < 760 and y < 985:
            continue  # the road
        tuft(x, y, R(26, 56), n=int(R(3, 7)), w=1.05, lean=R(-0.2, 0.2))
    for (x, y, h, r) in [(110, 940, 80, 10), (190, 965, 64, 9), (840, 950, 76, 10), (900, 975, 58, 8), (470, 975, 50, 8)]:
        daisy(x, y, h, r, lean=R(-0.1, 0.15))
    for (x, y, h, r) in [(230, 960, 96, 13), (800, 970, 88, 12)]:
        umbel(x, y, h, r, lean=R(-0.08, 0.08))
    for (bx, by, a, L) in [(45, 990, -1.0, 170), (955, 992, -2.1, 160)]:
        frond((bx, by), a, L, curl=0.35 if bx < 500 else -0.35)
    verge = catmull([(20, 900), (150, 884), (300, 880), (440, 888), (520, 900)], step=2)
    verge2 = catmull([(700, 905), (800, 890), (900, 884), (980, 886)], step=2)
    pen.line(verge, w=1.6, hand=0.6, lift=0.2)
    pen.line(verge2, w=1.6, hand=0.6, lift=0.2)
    pen.occlude(verge + [(520, 1000), (20, 1000)])
    pen.occlude(verge2 + [(980, 1000), (700, 1000)])

    # the long road, winding from the foreground up to the city gate
    ground_road([(640, 1010), (590, 900), (470, 790), (420, 690), (470, 590), (540, 520), (530, 470), (506, 447),
                 (500, 438.5)], 10.0)
    # the skyway, curving in from the left on pylons
    skyway([(-10, 640), (120, 600), (240, 540), (330, 495), (400, 462), (450, 444), (480, 438)], 7.0,
           elev=lambda t: 22 + 70 * t ** 1.4, pylon_every=70.0, min_sep=40.0)

    groves([(300, 520, 4), (640, 520, 5), (760, 480, 4), (880, 545, 4), (200, 470, 3), (420, 458, 3), (600, 452, 3),
            (900, 455, 3), (130, 600, 3), (720, 600, 4)])
    outlines = city(500, YH + 1.5, 0.92 * 1.0, wline=1.05)
    skybridge(412, 500, YH - 140, 8)
    skybridge(500, 585, YH - 175, 7)
    skybridge(330, 408, YH - 95, 5)
    hills([(30, 440), (80, 430), (150, 434), (210, 438)])
    hills([(790, 437), (860, 428), (930, 432), (975, 438)])
    horizon_line(30, 970, YH + 3)
    plain_marks(130, (30, 970))

    nets = [
        dict(cx=170, cy=190, sizes=[3, 4, 3, 2], W=230, H=150, rot=-0.08),
        dict(cx=830, cy=160, sizes=[2, 4, 2], W=160, H=120, rot=0.1),
        dict(cx=345, cy=70, sizes=[2, 3, 1], W=110, H=64, rot=0.15),
        dict(cx=665, cy=58, sizes=[3, 2], W=70, H=60, rot=-0.1),
    ]
    boxes = []
    for nt in nets:
        constellation(nt['cx'], nt['cy'], nt['sizes'], nt['W'], nt['H'], nt['rot'])
        boxes.append((nt['cx'], nt['cy'], nt['W'] / 2 + 22, nt['H'] / 2 + 22))
    avoid = [lambda p, b=b: abs(p[0] - b[0]) < b[2] and abs(p[1] - b[1]) < b[3] for b in boxes]
    starfield(90, (25, 25, 975, YH - 10), avoid)

# keep everything inside the square, a little in from its edges
M = 8.0


def in_frame(q):
    return M <= q[0] <= 1000 - M and M <= q[1] <= 1000 - M


framed = []
for pts, w in pen.strokes:
    if all(in_frame(q) for q in pts):
        framed.append((pts, w))
        continue
    for run in clip_segments(pts, in_frame):
        if len(run) >= 2 and length(run) > 0.8:
            framed.append((run, w))
# the set's finest line is 0.6
pen.strokes = [(p, max(0.6, w)) for p, w in framed]
pen.save(OUT)
pen.report()
