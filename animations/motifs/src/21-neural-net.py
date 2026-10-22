"""21 - the future: people in nature looking at a far metropolis, under a sky
whose stars form neural networks.

STAGE 2 (draft A, "big sky", chosen by Maxim): a family stands on a knoll at
the left, seen from behind, hand in hand, an old tree framing them at the edge.
Below them a meadow plain falls away, with belts of woodland and single trees,
to a calm lake; the metropolis rises from its far shore in three ranks (low
domes and terraces, towers with saucers, skybridges and a great arch, then the
tallest spires), with low hills behind it. Three ways lead to it: the main
road sweeping up from the lower right, a second road coming out from behind
the knoll, and a skyway on slender piers from the right. Above, a faint band
of the Milky Way and plain stars, among which five small neural networks are
made of stars.

    python3 21-neural-net.py            -> ../21-neural-net.svg
    python3 21-neural-net.py <path>     -> <path>

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

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, length, clip_segments, scanlines, offset

OUT = sys.argv[1] if len(sys.argv) > 1 else '../21-neural-net.svg'


class ScenePen(Pen):
    """A Pen whose occluders sit on a grid, so a busy scene stays quick."""

    def __init__(self, seed):
        super().__init__(seed)
        self.cell = 25
        self.grid = defaultdict(list)
        self.polys = []
        self.halos = []

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
        for x0, y0, st, cells in self.halos:
            if (int(round((p[0] - x0) / st)), int(round((p[1] - y0) / st))) in cells:
                return True
        c = self.cell
        for k in self.grid.get((int(p[0] // c), int(p[1] // c)), ()):
            poly, bb = self.polys[k]
            if bb[0] <= p[0] <= bb[2] and bb[1] <= p[1] <= bb[3] and inside(p, poly):
                return True
        return False

    def add_halo(self, box, r=4.0, step=2.0):
        """A thin margin of clear paper round everything already drawn inside
        box: lines drawn later stop just short of those outlines."""
        x0, y0, x1, y1 = box
        nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
        k = int(math.ceil(r / step))
        disc = [(i, j) for i in range(-k, k + 1) for j in range(-k, k + 1) if i * i + j * j <= k * k]
        cells = set()
        for i in range(nx):
            for j in range(ny):
                if self.hidden((x0 + i * step, y0 + j * step)):
                    for di, dj in disc:
                        cells.add((i + di, j + dj))
        self.halos.append((x0, y0, step, cells))

    def visible(self, pts):
        if not self.polys:
            return [list(pts)]
        return clip_segments(pts, lambda p: not self.hidden(p))


pen = ScenePen(seed=2101)
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

YH = 600.0             # horizon
HC = 20.0              # camera height over the plain (m)
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


def hairy_head(hc, rx, ry, w=1.8, amp=0.03):
    """The back of a head as its hair's outline: an oval with small locks."""
    ph1, ph2 = R(0, 6.3), R(0, 6.3)
    pts = []
    N = int(2 * math.pi * max(rx, ry) / 1.0)
    for k in range(N + 1):
        a = 2 * math.pi * k / N
        top = max(0.0, -math.sin(a))  # locks on the crown and sides, a smooth nape
        r = 1 + amp * top * (0.6 * math.sin(9 * a + ph1) + 0.4 * math.sin(14 * a + ph2))
        pts.append((hc[0] + math.cos(a) * rx * r, hc[1] + math.sin(a) * ry * r))
    pen.line(pts, w=w, hand=0.25, lift=0.04)
    return pts


def hair_short(hc, rx, ry, crown, n, u, tousle=0.0, seed_side=1):
    """Short hair on the back of a head: strands sweeping from the crown whorl
    down and round to the nape and sides, of varied length, clumped, and more
    of them on the shade (right) side."""
    head = ellipse_pts(hc[0], hc[1], rx, ry, 0, 0, 2 * math.pi, step=1.0)
    for k in range(n):
        f = (k + R(0.2, 0.8)) / n
        a = math.pi * (0.04 + 0.92 * f)            # 0 = right side ... pi = left side, through the bottom
        r0 = R(0.22, 0.5)
        st = (crown[0] + math.cos(a) * rx * r0 * 0.7, crown[1] + math.sin(a) * ry * r0 * 0.45 + ry * 0.04)
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
    head = hairy_head(hc, 0.088 * u, 0.102 * u, amp=0.035)
    nape = C(f.Ps([(-0.082, -0.858), (-0.06, -0.836), (-0.03, -0.826), (0, -0.822), (0.03, -0.829), (0.058, -0.838),
                   (0.082, -0.858)]), step=1)
    fine(nape, w=1.1, hand=0.3)
    # tousled short hair, from a whorl at the crown
    hair_short(hc, 0.088 * u, 0.102 * u, f.P((0.014, -0.962)), 14, u, tousle=0.14)
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
    fine(C(f.Ps([(-0.137, -0.424), (0, -0.42), (0.137, -0.424)]), step=1), w=0.8)            # the hem's turn
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
    tips = [(-0.084, -0.66), (-0.072, -0.634), (-0.052, -0.62), (-0.036, -0.626), (-0.018, -0.607), (0.004, -0.612),
            (0.026, -0.602), (0.05, -0.617), (0.068, -0.628), (0.086, -0.662)]
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
    fine(C(f.Ps([(-0.172, -0.072), (-0.1, -0.064), (0, -0.064), (0.1, -0.064), (0.172, -0.072)]), step=1), w=0.8)
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
    lengthwise(sl, sr, 0.64, 0.97, spacing=5.6, clip=dress, t0=0.03, t1=0.99)
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
    head = hairy_head(hc, 0.057 * u, 0.067 * u, amp=0.025)
    nape = C(f.Ps([(-0.054, -0.905), (-0.036, -0.887), (-0.012, -0.881), (0.012, -0.882), (0.036, -0.888),
                   (0.054, -0.905)]), step=1)
    fine(nape, w=1.1)
    hair_short(hc, 0.057 * u, 0.067 * u, f.P((0.01, -0.978)), 13, u)
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
    fine(C(f.Ps([(-0.125, -0.352), (-0.06, -0.347), (-0.008, -0.348)]), step=1), w=0.8)  # the hem's turn
    fine(C(f.Ps([(0.008, -0.348), (0.06, -0.347), (0.125, -0.352)]), step=1), w=0.8)
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
    lengthwise(ul, ur, 0.6, 0.97, spacing=5.5, clip=coat)
    ll = C(f.Ps([(-0.106, -0.592), (-0.111, -0.50), (-0.12, -0.40), (-0.127, -0.34)]))
    lr = C(f.Ps([(0.106, -0.592), (0.111, -0.50), (0.12, -0.40), (0.127, -0.34)]))
    lengthwise(ll, lr, 0.58, 0.97, spacing=5.5, clip=coat)
    across(ll, lr, spacing=6.0, frac=(0.18, 0.34), bow=2.0, w=0.65, t0=0.12, t1=0.9, from_b=True, clip=coat)
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
    """A road on the plain: its edges, heavier near; a dashed lane marking down
    the middle (dashes 3 m long every 8 m); and lines along the inside of the
    left kerb, which is in its own shadow (only where they lie 5 apart)."""
    left, right, mid, foot = road_edges(ctrl, W)
    wf = depth_w(2.0, 0.8)
    weighted(left, wf)
    weighted(right, wf)
    cum = 0.0
    run = []
    marks = []
    for i, ((X, Z, _), p) in enumerate(zip(foot, mid)):
        if i:
            cum += math.hypot(X - foot[i - 1][0], Z - foot[i - 1][1])
        if cum % 8.0 < 3.0 and p[1] > YH + 5:
            run.append(p)
        elif run:
            marks.append(run)
            run = []
    if run:
        marks.append(run)
    for rn in marks:
        if len(rn) > 1 and length(rn) > 1.2:
            pen.line(rn, w=depth_w(1.1, 0.62)(rn[0][1]), hand=0, lift=0)
    for k in (1, 2, 3):
        d = 5.0 * k
        line = []
        for a, b in zip(left, right):
            L = dist(a, b)
            if L > 3.4 * d + 14:
                line.append(lerp(a, b, d / L))
            elif line:
                break
        if len(line) > 3:
            for pc in pieces(line, on=(30, 110), off=(6, 26), start_off=False):
                pen.line(pc, w=0.66, hand=0.2, lift=0.1, piece=(20, 60))
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
    rail = [(p[0], p[1] - F * 0.9 / Z) for (X, Z, Y), p in zip(foot, near) if F * 0.9 / Z > 2.2]
    if len(rail) > 3:
        weighted(rail, depth_w(1.0, 0.62))
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
        LAKE_PIERS.append((bot[0], bot[1], ht))
        ht_w, mid_w, foot_w = F * 2.8 / Z, F * 1.35 / Z, F * 1.7 / Z
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
                xc = (sp[0] + sp[1]) / 2
                x0, x1 = sp[0] + 1.6, min(sp[1] - 1.0, xc + (sp[1] - sp[0]) * 0.08)
                if x1 - x0 > 3:
                    pen.line([(x0, y), (x1, y)], w=0.6, hand=0, lift=0.5, piece=(2.2, 4.5))
            y -= 5.5


def skybridge(x0, x1, y, sag, w=0.9):
    pts = catmull([(x0, y), ((x0 + x1) / 2, y + sag), (x1, y)], step=2)
    pen.line(pts, w=w, hand=0.1, lift=0)
    pen.line([(x, yy + 3) for x, yy in pts], w=0.7, hand=0.1, lift=0)


# ---------------------------------------------------------------- the sky

# ---------------------------------------------------------------- ground

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


def scallop_arc(c, r, a0, a1, per, amp):
    """An arc of a circle edged with small outward bumps (a clump of leaves)."""
    pts = ellipse_pts(c[0], c[1], r, r, 0, a0, a1, step=0.8)
    out = []
    s = 0.0
    for k, p in enumerate(pts):
        if k:
            s += dist(pts[k - 1], p)
        b = amp * abs(math.sin(math.pi * s / per)) ** 0.6
        dx, dy = p[0] - c[0], p[1] - c[1]
        L = math.hypot(dx, dy) or 1
        out.append((p[0] + dx / L * b, p[1] + dy / L * b))
    return out


def tree(bx, by, h, w=None, allow_hidden=False):
    """A round-crowned broadleaf tree, its foot at (bx, by), h tall on the page,
    in the engraver's shorthand: a crown of leafy clumps, lit from the upper
    left; each clump's lower edge scalloped where it lies over the clumps
    behind, and its shaded side hatched; a short trunk and a cast shadow.
    Skipped (False) where it would run into something already drawn in front."""
    if h < 5:
        return False
    R0 = h * R(0.32, 0.38)
    cx, cy = bx + G(h * 0.02), by - h + R0 * 0.95
    m = int(R(5, 8)) if h > 20 else 5
    tall = R(0.95, 1.3)
    lobes = [(cx + G(R0 * 0.05), cy + R0 * 0.1, R0 * 0.5)]
    for k in range(m):
        a = -math.pi / 2 + 2 * math.pi * (k + R(-0.3, 0.3)) / m
        lr = R0 * R(0.36, 0.54)
        d = (R0 - lr) * R(0.8, 1.05)
        lobes.append((cx + math.cos(a) * d * 1.05, cy + math.sin(a) * d * 0.9 * tall, lr))
    crown = crown_shape(cx, cy, R0, lobes, scallop=min(1.8, R0 * 0.06) if h > 12 else 0.0)
    tb = cy + R0 * 0.55
    tw0, tw1 = max(1.2, h * 0.05), max(0.9, h * 0.032)
    lean = G(h * 0.015)
    trunk = [(bx - tw0, by), (bx - tw1 + lean, tb), (bx + tw1 + lean, tb), (bx + tw0, by)]
    probe = crown[::3] + trunk + [(bx - h * 0.3, by), (bx + h * 0.4, by)]
    if not allow_hidden and (any(pen.hidden(q) for q in probe) or not all(14 < q[0] < 986 for q in probe)):
        return False
    if w is None:
        w = clamp(0.7 + h / 55, 0.75, 1.6)
    pen.line(crown, w=w, hand=0.3, lift=0.05)
    inner = [(cx + (p[0] - cx) * 0.94, cy + (p[1] - cy) * 0.94) for p in crown]
    if h > 18:
        # each clump's lower edge, where it lies over the clumps behind it
        for lx, ly, lr in lobes:
            if ly < cy - R0 * 0.3:
                continue
            arc = scallop_arc((lx, ly), lr, math.radians(5), math.radians(160), max(4.5, lr / 2.0),
                              min(1.5, lr * 0.08))
            for run in clip_segments(arc, lambda p: inside(p, inner)):
                if length(run) > 4:
                    pen.line(run, w=w * 0.6, hand=0.2, lift=0.03)

    def tone(p):
        g = ((p[0] - cx) * SHADE[0] + (p[1] - cy) * SHADE[1]) / R0
        best = -1.0
        for lx, ly, lr in lobes:
            if math.hypot(p[0] - lx, p[1] - ly) < lr:
                best = max(best, ((p[0] - lx) * SHADE[0] + (p[1] - ly) * SHADE[1]) / lr)
        return 0.6 * g + 0.5 * best
    if h > 9:
        region_hatch(crown, -52, 5.0 if h > 30 else 5.5, lambda p: inside(p, crown) and tone(p) > 0.26, w=0.66,
                     minlen=2.0)
    if h <= 9:
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


# =============================================================== stage 2 parts

def wavefn(amp, freqs=(0.01, 0.03)):
    """A gentle random wave along a coordinate, for hand-drawn edges."""
    ph = [R(0, 6.28) for _ in range(3)]
    fs = [R(*freqs) for _ in range(3)]
    return lambda v: amp * sum(math.sin(v * f + p) for f, p in zip(fs, ph)) / 2


def tangents(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        out.append((tx / L, ty / L))
    return out


def var_offset(pts, rads, side):
    """A polyline moved sideways by a different distance at each point."""
    return [(p[0] - t[1] * r * side, p[1] + t[0] * r * side) for p, t, r in zip(pts, tangents(pts), rads)]


def pieces(pts, on=(25, 90), off=(12, 45), start_off=True):
    """A polyline broken into runs with gaps between (lengths in units)."""
    out = []
    pts = resample(pts, 1.5)
    s_at = [0.0]
    for k in range(1, len(pts)):
        s_at.append(s_at[-1] + dist(pts[k - 1], pts[k]))
    s = R(0, off[1]) if start_off else 0.0
    while s < s_at[-1]:
        e = s + R(*on)
        run = [p for p, sa in zip(pts, s_at) if s <= sa <= e]
        if len(run) > 1:
            out.append(run)
        s = e + R(*off)
    return out


# ---------------------------------------------------------------- the old tree at the left edge

class Limb:
    def __init__(self, ctrl, r0, r1, power=0.9):
        self.pts = catmull(ctrl, step=2.0)
        n = len(self.pts)
        self.rads = [r0 + (r1 - r0) * (i / max(1, n - 1)) ** power for i in range(n)]

    def poly(self):
        a = var_offset(self.pts, self.rads, 1)
        b = var_offset(self.pts, self.rads, -1)
        return a + b[::-1]


def leaf_poly(B, a, L, Wd, bend=0.0):
    """A pointed oval leaf from its base B along angle a."""
    ca, sa = math.cos(a), math.sin(a)
    side = []
    for k in range(10):
        u = k / 9
        hw = Wd / 2 * math.sin(math.pi * u ** 0.85) ** 0.75
        side.append((u, hw))
    loc = [(u * L, hw + bend * L * u * (1 - u)) for u, hw in side]
    loc += [(u * L, -hw + bend * L * u * (1 - u)) for u, hw in reversed(side[1:-1])]
    return [(B[0] + x * ca - y * sa, B[1] + x * sa + y * ca) for x, y in loc]


def frame_tree(GY=852.0):
    """The old broadleaf tree at the left edge that frames the people, in the
    hand of 14 ginkgo: a crown of leaf clumps (fine leaves inside, bolder at
    the edges, shade between the leaves on each clump's lower right), its
    limbs and trunk outlined, with lines along their shadow side and bark
    fissures; the knoll's grass stands in front of its foot."""
    # the trunk: centre line and half widths, flaring at the foot
    tc = catmull([(58, GY + 2), (62, 770), (70, 690), (80, 615), (93, 548)], step=2.0)
    n = len(tc)
    tr = []
    for i, p in enumerate(tc):
        u = i / (n - 1)
        flare = 20 * max(0.0, 1 - (GY - p[1]) / 70) ** 2.0
        tr.append(27 - 9 * u + flare)
    wl, wr = wavefn(1.6), wavefn(1.6)
    t_left = [(p[0] - r + wl(p[1]), p[1]) for p, r in zip(tc, tr)]
    t_right = [(p[0] + r + wr(p[1]), p[1]) for p, r in zip(tc, tr)]
    trunk_poly = t_left + t_right[::-1]

    limbs = [
        Limb([(84, 575), (118, 532), (150, 512), (196, 470), (226, 446), (256, 414)], 14, 3),   # low, out to the right
        Limb([(92, 556), (124, 488), (166, 430), (178, 380), (214, 318), (240, 266)], 13, 3),   # up to the right
        Limb([(95, 552), (112, 470), (108, 400), (124, 320), (112, 236), (116, 160), (98, 84)], 16, 3.5),  # leader
        Limb([(84, 566), (66, 500), (54, 452), (30, 400), (24, 340), (10, 300)], 11, 3),         # up the left edge
        Limb([(118, 360), (150, 318), (172, 262), (198, 214), (206, 160), (230, 104)], 8.5, 2),
        Limb([(114, 262), (88, 224), (70, 176), (34, 132)], 7.5, 2),
        Limb([(110, 170), (140, 120), (152, 82), (186, 40)], 6.5, 2),
        Limb([(110, 420), (82, 380), (70, 330), (52, 290)], 6.5, 2),
    ]
    # the clumps of leaves, front first: centre, radii, and the limb they hang on
    clumps = [
        (252, 404, 44, 30, 0),
        (190, 446, 40, 25, 0),
        (236, 262, 48, 38, 1),
        (182, 336, 46, 36, 1),
        (226, 124, 44, 36, 4),
        (166, 196, 48, 38, 4),
        (100, 76, 58, 40, 2),
        (40, 152, 44, 36, 5),
        (28, 306, 40, 40, 3),
        (118, 284, 42, 38, 2),
        (72, 226, 40, 34, 5),
        (154, 34, 48, 28, 6),
        (58, 396, 36, 30, 3),
        (126, 396, 36, 28, 0),
        (60, 300, 38, 32, 7),
        (200, 390, 36, 30, 1),
        (160, 110, 40, 32, 6),
        (36, 40, 40, 32, 2),
        (260, 182, 34, 30, 4),
    ]

    def in_clump(p, pad=1.0):
        for cx, cy, rx, ry, _ in clumps:
            if ((p[0] - cx) / (rx * pad)) ** 2 + ((p[1] - cy) / (ry * pad)) ** 2 < 1:
                return True
        return False

    def tone(p):
        best = -2.0
        for cx, cy, rx, ry, _ in clumps:
            dx, dy = (p[0] - cx) / rx, (p[1] - cy) / ry
            if dx * dx + dy * dy < 1:
                best = max(best, dx * SHADE[0] + dy * SHADE[1])
        return best

    # leaves
    leaves = []
    grid = defaultdict(list)
    Lf = 11.0
    for ci, (cx, cy, rx, ry, _) in enumerate(clumps):
        for _ in range(int(math.pi * rx * ry / 9)):
            a = R(0, 2 * math.pi)
            rr = math.sqrt(R())
            c = (cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr)
            if rr > 0.8 and R() < 0.45:
                continue  # a ragged clump edge
            gx, gy = int(c[0] // 10), int(c[1] // 10)
            if any(dist(c, q) < Lf * 0.74 for i in range(gx - 1, gx + 2) for j in range(gy - 1, gy + 2)
                   for q in grid[(i, j)]):
                continue
            grid[(gx, gy)].append(c)
            ox, oy = (c[0] - cx) / rx, (c[1] - cy) / ry
            vx, vy = ox * 0.8 + G(0.45), oy * 0.8 + 0.45 + G(0.45)
            ang = math.atan2(vy, vx)
            L = Lf * R(0.8, 1.15)
            B = (c[0] - math.cos(ang) * L / 2, c[1] - math.sin(ang) * L / 2)
            poly = leaf_poly(B, ang, L, L * R(0.42, 0.56), bend=G(0.12))
            t = ox * SHADE[0] + oy * SHADE[1]
            edge = rr > 0.72 and not any(
                ((c[0] - qx) / (qrx * 0.85)) ** 2 + ((c[1] - qy) / (qry * 0.85)) ** 2 < 1
                for k2, (qx, qy, qrx, qry, _) in enumerate(clumps) if k2 != ci)
            if edge:
                w = 1.25 if t > 0.1 else 1.05
            else:
                w = 0.92 if t > 0.1 else 0.78
            leaves.append(dict(poly=poly, c=c, B=B, ang=ang, L=L, w=w, t=t))
    for lf in leaves:
        pen.line(lf['poly'] + [lf['poly'][0]], w=lf['w'], hand=0.2, lift=0.03, piece=(30, 90))
        if lf['t'] < 0.0 and lf['L'] > 11 and R() < 0.25:
            B, a, L = lf['B'], lf['ang'], lf['L']
            pen.line([(B[0] + math.cos(a) * L * 0.12, B[1] + math.sin(a) * L * 0.12),
                      (B[0] + math.cos(a) * L * 0.72, B[1] + math.sin(a) * L * 0.72)], w=0.62, hand=0, lift=0)
        pen.occlude(lf['poly'])
    # shade between the leaves on the shadow side of each clump (the sky gaps stay white)
    cover = set()
    for lf in leaves:
        gx, gy = int(lf['c'][0] // 6), int(lf['c'][1] // 6)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                cover.add((i, j))
    box = [(0, 0), (310, 0), (310, 480), (0, 480)]
    for p0, p1 in scanlines(box, -52, 5.0, R()):
        run, runs = [], []
        for p in resample([p0, p1], 1.5):
            ok = (int(p[0] // 6), int(p[1] // 6)) in cover and in_clump(p) and tone(p) + G(0.07) > 0.22
            if ok:
                run.append(p)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for rn in runs:
            if length(rn) > 3:
                pen.line(rn, w=R(0.66, 0.74), hand=0.2, lift=0.1, piece=(12, 40))
    # twigs into the clumps
    for cx, cy, rx, ry, li in clumps:
        lb = limbs[li]
        k = min(range(len(lb.pts)), key=lambda i: dist(lb.pts[i], (cx, cy)))
        k = max(0, min(len(lb.pts) - 1, k - 3))
        q = lb.pts[k]
        mid = ((q[0] + cx) / 2 + G(4), (q[1] + cy) / 2 + G(4))
        pen.line(catmull([q, mid, (cx, cy)], step=2), w=1.15, hand=0.3, lift=0, taper=0.35)
        for _ in range(3):
            a = R(0, 2 * math.pi)
            e = (cx + math.cos(a) * rx * 0.7, cy + math.sin(a) * ry * 0.7)
            pen.line(catmull([(cx, cy), ((cx + e[0]) / 2 + G(3), (cy + e[1]) / 2 + G(3)), e], step=2), w=0.85,
                     hand=0.3, lift=0, taper=0.4)
    # limbs: outlined, heavier on the shadow side; their foot runs into the trunk
    for lb in limbs:
        poly = lb.poly()
        ts = tangents(lb.pts)
        for side in (1, -1):
            edge = var_offset(lb.pts, lb.rads, side)
            tg = ts[len(ts) // 3]
            nrm = (-tg[1] * side, tg[0] * side)
            shadow = (nrm[0] * LIGHT[0] + nrm[1] * LIGHT[1]) < 0
            w = min(2.1, 1.1 + 0.05 * lb.rads[0]) + (0.25 if shadow else 0.0)
            for run in clip_segments(edge, lambda p: not inside(p, trunk_poly)):
                pen.line(run, w=w, hand=0.45, lift=0.04, taper=0.25)
        n = len(lb.pts)
        sides = []
        for i in range(n):
            nrm = (-ts[i][1], ts[i][0])
            sides.append(1 if (nrm[0] * LIGHT[0] + nrm[1] * LIGHT[1]) < 0 else -1)
        for k in (1, 2):
            run = []
            for i in range(n):
                r = lb.rads[i]
                if r < 5 * k + 1.5:
                    continue
                off = (r - 4.6 * k) * sides[i]
                run.append((lb.pts[i][0] - ts[i][1] * off, lb.pts[i][1] + ts[i][0] * off))
            if len(run) > 3:
                for rn in clip_segments(run, lambda p: not inside(p, trunk_poly)):
                    pen.line(rn, w=0.8 - 0.05 * k, hand=0.3, lift=0.3, piece=(10, 34))
        for f in range(int(lb.rads[0] / 3.5)):
            u = R(-0.55, 0.55)
            s0 = R(0.0, 0.55)
            s1 = min(1.0, s0 + R(0.08, 0.2))
            i0, i1 = int(s0 * (n - 1)), int(s1 * (n - 1))
            if i1 - i0 < 4 or lb.rads[i1] < 4.5:
                continue
            seg = [(lb.pts[i][0] - ts[i][1] * lb.rads[i] * u, lb.pts[i][1] + ts[i][0] * lb.rads[i] * u)
                   for i in range(i0, i1)]
            for rn in clip_segments(seg, lambda p: not inside(p, trunk_poly)):
                pen.line(rn, w=R(0.72, 0.86), hand=0.4, lift=0.25)
        pen.occlude(poly)
    # the trunk
    pen.line(t_left, w=2.2, hand=0.7, lift=0.03)
    pen.line(t_right, w=2.6, hand=0.7, lift=0.03)
    # lines along the shadow side, counted in from the right edge
    for k in (1, 2, 3, 4):
        run = [(p[0] - 4.8 * k, p[1]) for p, r in zip(t_right, tr) if 2 * r - 4.8 * k > 6 and p[1] > 540]
        if len(run) > 3:
            pen.line(run, w=0.84 - 0.04 * k, hand=0.4, lift=0.3, piece=(10, 40))
    # bark fissures, more toward the shadow
    for f in range(24):
        u = R(-0.75, 0.6) if R() < 0.4 else R(-0.1, 0.75)
        y0 = R(560, GY - 6)
        L = R(30, 110)
        seg = []
        for p, r in zip(tc, tr):
            if y0 - L < p[1] < y0:
                seg.append((p[0] + r * u + G(0.4), p[1]))
        if len(seg) > 3:
            pen.line(seg, w=R(0.72, 0.9), hand=0.6, lift=0.3, piece=(8, 30))
    pen.occlude(trunk_poly)
    # its roots into the ground, and its shadow across the knoll to the lower right
    for sx, dx, dy in ((-1, -16, 9), (1, 22, 7), (1, 8, 15)):
        b = t_left[0] if sx < 0 else t_right[0]
        pen.line(catmull([(b[0] - sx * 2, b[1] - 12), (b[0] + dx * 0.4, b[1] + dy * 0.4), (b[0] + dx, b[1] + dy)],
                         step=2), w=1.6, hand=0.4, lift=0, taper=0.4)
    return trunk_poly


# ---------------------------------------------------------------- more plants

def dandelion(x, y, h, r, lean=0.0):
    """A seed clock: a stem and a ball of fine rays."""
    head = (x + lean * h, y - h)
    pen.line(catmull([(x, y), (x + lean * h * 0.4 + G(1), y - h * 0.5), head], step=2), w=0.85, hand=0.2, lift=0)
    for k in range(16):
        a = 2 * math.pi * k / 16 + R(-0.1, 0.1)
        p0 = (head[0] + math.cos(a) * r * 0.22, head[1] + math.sin(a) * r * 0.22)
        p1 = (head[0] + math.cos(a) * r, head[1] + math.sin(a) * r)
        pen.line([p0, p1], w=0.62, hand=0, lift=0)
    dot(head[0], head[1], r=1.1, w=1.0)


def bellflower(x, y, h, lean=0.15, n=3):
    """A harebell: a thin bowed stem with bells hanging from it."""
    top = (x + lean * h, y - h)
    stem = catmull([(x, y), (x + lean * h * 0.3, y - h * 0.55), top, (top[0] + h * 0.12, top[1] + h * 0.06)],
                   step=1.5)
    pen.line(stem, w=0.85, hand=0.15, lift=0)
    for k in range(n):
        q = stem[int(len(stem) * (0.55 + 0.42 * k / max(1, n - 1))) - 1]
        bw, bh = R(5.5, 7.5), R(7, 9)
        a = R(-0.25, 0.25)
        tip = (q[0] + math.sin(a) * 3, q[1] + 3)
        body = [(tip[0] - bw * 0.62, tip[1] + bh), (tip[0] - bw * 0.42, tip[1] + bh * 0.7),
                (tip[0] - bw * 0.3, tip[1] + bh * 0.15), tip, (tip[0] + bw * 0.3, tip[1] + bh * 0.15),
                (tip[0] + bw * 0.42, tip[1] + bh * 0.7), (tip[0] + bw * 0.62, tip[1] + bh)]
        pen.line([q, tip], w=0.7, hand=0, lift=0)
        pen.line(catmull(body, step=1), w=0.95, hand=0.1, lift=0)
        mouth = ellipse_pts(tip[0], tip[1] + bh, bw * 0.62, 1.3, 0, 0, math.pi, step=0.8)
        pen.line(mouth, w=0.8, hand=0, lift=0)
        pen.occlude(body + [(tip[0] + bw * 0.62, tip[1] + bh + 1.3), (tip[0] - bw * 0.62, tip[1] + bh + 1.3)])


def seed_grass(x, y, h, lean=0.1):
    """A tall grass with a nodding head of spikelets."""
    pts = catmull([(x, y), (x + lean * h * 0.35, y - h * 0.5), (x + lean * h, y - h)], step=1.5)
    pen.line(pts, w=0.85, hand=0.15, lift=0, taper=0.4)
    top = pts[int(len(pts) * 0.62):]
    for i in range(1, len(top), 3):
        q = top[i]
        a, b = top[i - 1], top[min(len(top) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        tx, ty = tx / L, ty / L
        s = 1 if (i // 3) % 2 else -1
        ln = 4.5 * (1 - i / len(top) * 0.5)
        tip = (q[0] + (tx * 0.7 - ty * s * 0.7) * ln, q[1] + (ty * 0.7 + tx * s * 0.7) * ln)
        pen.line([q, tip], w=0.8, hand=0, lift=0, taper=0.3)


# ---------------------------------------------------------------- the knoll's form

def knoll_hatch(top, x_max=660, cx=300.0):
    """Contour hatching on the knoll: level lines across its face, bowing
    toward us as they go round it, lit from the upper left, so they are kept
    only on the shaded right flank and low down, broken."""
    lefts = [p for p in top if p[0] < cx]
    rights = [p for p in top if p[0] >= cx]
    y = top_min = min(p[1] for p in top) + 10
    while y < 1000:
        xr = min(rights, key=lambda p: abs(p[1] - y))[0]
        if y <= lefts[0][1]:
            xl = min(lefts, key=lambda p: abs(p[1] - y))[0]
        else:
            xl = lefts[0][0] - (y - lefts[0][1]) * 1.6
        if xr - xl < 30:
            y += 7.5
            continue
        sag = min(26.0, (xr - xl) * 0.07) * (0.5 + (y - top_min) / 300)
        arc = catmull([(xl, y), (xl + (xr - xl) * 0.3, y + sag * 0.84), ((xl + xr) / 2, y + sag),
                       (xl + (xr - xl) * 0.75, y + sag * 0.75), (xr - 2, y + 1)], step=2)
        ph = R(0, 6.28)
        run, runs = [], []
        for p in arc:
            u = (p[0] - xl) / (xr - xl)
            t = 1.0 * u ** 1.5 + 0.1 * clamp((y - 900) / 100, 0, 1) + 0.1 * math.sin(p[0] * 0.05 + ph) + G(0.04)
            if t > 0.66 and 8 < p[0] < x_max and p[1] < 994:
                run.append(p)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for rn in runs:
            for pc in pieces(rn, on=(10, 34), off=(6, 22), start_off=True):
                if length(pc) > 5:
                    pen.line(pc, w=R(0.64, 0.74), hand=0.35, lift=0.12, piece=(12, 40))
        y += 7.5


# ---------------------------------------------------------------- the middle ground

def fold(sx0, sx1, sy, rise=0.10, shade=True, w=None):
    """A fold of the meadow: a gentle swell across the plain at page height sy,
    from page x sx0 to sx1, its crest drawn broken; below it on the right a
    few short strokes of its shadow (lit from the upper left)."""
    Z = Z_of(sy)
    X0, X1 = (sx0 - CXP) * Z / F, (sx1 - CXP) * Z / F
    ph = R(0, 6.28)
    crest = []
    n = 60
    for k in range(n + 1):
        u = k / n
        X = X0 + (X1 - X0) * u
        bump = math.sin(math.pi * u) ** 1.3 * (1 + 0.25 * math.sin(u * 9 + ph))
        z = Z * (1 + rise * bump)
        crest.append(P(X, 0, z))
    near = clamp((sy - YH) / 300, 0, 1)
    if w is None:
        w = 0.66 + 0.3 * near
    for pc in pieces(crest, on=(30 + 80 * near, 80 + 160 * near), off=(6, 16 + 20 * near), start_off=False):
        pen.line(pc, w=w, hand=0.3, lift=0.1, piece=(15, 50))
    if shade:
        k = 1
        while True:
            d = 5.0 * k
            sub = [(p[0], p[1] + d) for p in crest]
            i0 = int(len(sub) * (0.42 + 0.1 * k))
            i1 = int(len(sub) * (0.9 - 0.04 * k))
            if i1 - i0 < 4 or d > 4 + 22 * near:
                break
            seg = [q for q in sub[i0:i1] if q[1] < sy + 2]
            if len(seg) > 3:
                pen.line(seg, w=0.64, hand=0.2, lift=0.25, piece=(8, 24))
            k += 1
    return crest


def grass_ticks(n, x_range, y0, y1, keep=None):
    """Small tufts scattered over the meadow, smaller with distance."""
    for _ in range(n):
        y = y0 + (y1 - y0) * R() ** 0.8
        x = R(*x_range)
        if keep and not keep((x, y)):
            continue
        Z = Z_of(y)
        h = F * R(0.5, 0.9) / Z
        if h < 2.2 or pen.hidden((x, y)):
            continue
        if h > 7:
            tuft(x, y, h, n=int(R(3, 5)), w=0.8, lean=R(-0.2, 0.2))
        else:
            for k in range(3):
                pen.line([(x + (k - 1) * h * 0.35, y), (x + (k - 1) * h * 0.55 + G(0.3), y - h * R(0.7, 1.0))],
                         w=0.65, hand=0, lift=0)


def belt(x0, x1, y, Hm=13.0, rr=(3.5, 5.5), w=None, shade_from=0.45):
    """A belt of woodland across the plain at page height y: a scalloped
    canopy edge, the lower part in shadow (fine upright strokes), each
    crown's lower right side hatched; it hides what lies behind."""
    Z = Z_of(y)
    s = F / Z
    crowns = []
    x = x0
    while x < x1:
        r = s * R(*rr)
        h = s * Hm * R(0.75, 1.15)
        crowns.append((x, y - h + r, r))
        x += r * R(1.0, 1.5)
    top = []
    xs = [x0 + k * 0.8 for k in range(int((x1 - x0) / 0.8) + 1)]
    for xx in xs:
        yt = None
        for cx, cy, r in crowns:
            if abs(xx - cx) < r:
                v = cy - math.sqrt(r * r - (xx - cx) ** 2)
                yt = v if yt is None else min(yt, v)
        if yt is None:
            yt = y - 2
        top.append((xx, yt))
    # small leafy bumps along the canopy edge
    per = max(3.0, s * 1.6)
    amp = min(1.4, s * 0.35)
    tb = [(p[0], p[1] - amp * abs(math.sin(math.pi * p[0] / per)) ** 0.6) for p in top]
    poly = tb + [(x1, y + 0.5), (x0, y + 0.5)]
    if w is None:
        w = clamp(0.62 + s * 0.12, 0.62, 1.2)
    pen.line(tb, w=w, hand=0.2, lift=0.05)
    # the lower edges of the nearer crowns, where they lie over the ones behind
    if s > 1.2:
        for cx, cy, r in crowns[::2]:
            arc = scallop_arc((cx, cy), r, math.radians(15), math.radians(150), max(3.5, r / 2.2), min(1.2, r * 0.08))
            runs = clip_segments(arc, lambda p: inside(p, poly) and p[1] < y - 1)
            for rn in runs:
                if length(rn) > 3:
                    pen.line(rn, w=w * 0.65, hand=0.15, lift=0.05)
    # the shade: each crown's lower right, at the angle of the trees' hatching,
    # and the dark foot of the wood
    hgt = max(1.0, y - min(p[1] for p in tb))

    def dark(p):
        if not inside(p, poly):
            return False
        best = -2
        for cx, cy, r in crowns:
            dd = math.hypot(p[0] - cx, p[1] - cy)
            if dd < r * 1.05:
                best = max(best, ((p[0] - cx) * SHADE[0] + (p[1] - cy) * SHADE[1]) / r)
        return best > 0.3 or p[1] > y - hgt * 0.22
    region_hatch(poly, -52, 5.0 if s > 1.5 else 5.5, dark, w=0.64, minlen=1.5, hand=0.1)
    pen.line([(x0, y + 0.6), (x1, y + 0.6)], w=0.7, hand=0.3, lift=0.3, piece=(8, 30))
    pen.occlude(poly)
    return poly


# ---------------------------------------------------------------- water

LAKE_PIERS = []


def lake(poly, towers, shore_y):
    """A calm lake: its near shore, rows of fine level strokes (closer toward
    the far shore), broken, and drawn thicker in the columns under the towers
    and piers, which are their reflections."""
    near = [p for p in poly if p[1] > shore_y + 3]
    cols = []
    for t in towers:
        if t['depth'] > 2.0 and t['kind'] not in ('ring',):
            continue
        x, w, h = t['x'], t['w'], t['h']
        if t['kind'] == 'dome':
            cols.append((x - w * 0.85, x + w * 0.85, h))
        elif t['kind'] == 'arch':
            cols.append((x - w / 2 + 1, x - w / 2 + 10, h))
            cols.append((x + w / 2 - 10, x + w / 2 - 1, h))
        elif t['kind'] == 'terrace':
            cols.append((x - w / 2 + 2, x + w / 2 - 2, h))
        else:
            cols.append((x - w * 0.42, x + w * 0.42, h))
    for px, py, ph in LAKE_PIERS:
        if inside((px, py + 1), poly):
            cols.append((px - 1.5, px + 1.5, ph + (py - shore_y)))
    y = shore_y + 3.5
    gap = 5.0
    while True:
        sp = span_at(poly, y)
        if not sp:
            break
        xa, xb = sp[0] + 3, sp[1] - 3
        if xb - xa < 6:
            break
        dy = y - shore_y
        # the reflections
        segs = []
        for c0, c1, h in cols:
            if dy < h and c1 > xa and c0 < xb:
                segs.append((max(xa, c0 + G(0.6)), min(xb, c1 + G(0.6))))
        segs.sort()
        merged = []
        for a, b in segs:
            if merged and a <= merged[-1][1] + 2:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        for a, b in merged:
            if b - a > 1.5:
                pen.line([(a, y), (b, y + 0.2)], w=0.66, hand=0.05, lift=0.3, piece=(4, 14))
        # open water: a few short strokes
        x = xa + R(0, 30)
        while x < xb:
            L = R(8, 26)
            if not any(a - 3 < x < b + 3 or a - 3 < x + L < b + 3 for a, b in merged) and R() < 0.55:
                pen.line([(x, y), (min(xb, x + L), y)], w=0.62, hand=0.1, lift=0)
            x += L + R(14, 40)
        y += gap
        gap *= 1.18
    return near


# ---------------------------------------------------------------- the city, stage 2

def tower_curve(x, base, w, h, bend):
    """A tower that tapers to a point and curves gently to one side."""
    n = 30
    left, right = [], []
    for k in range(n + 1):
        t = k / n
        ax = x + bend * math.sin(t * math.pi / 2) ** 1.6
        hw = w / 2 * (1 - t) ** 0.55 * (1 - 0.12 * t) + 0.3 * (1 - t)
        left.append((ax - hw, base - h * t))
        right.append((ax + hw, base - h * t))
    return left + right[::-1], right


def terrace_poly(x, b, w, h, tiers):
    """A low stepped building with rounded steps (terraces with gardens)."""
    th = h / tiers
    half = []
    for k in range(tiers):
        hw = w / 2 * (1 - 0.22 * k)
        y0, y1 = b - k * th, b - (k + 1) * th
        half += [(hw, y0), (hw, y1 + 1.6), (hw - 1.6, y1)]
    half.append((0.0, b - h))
    right = [(x + px, py) for px, py in half]
    left = [(x - px, py) for px, py in reversed(half[:-1])]
    return right + left, th


def city(cx, base, s=1.0, wline=1.1):
    """The metropolis in three ranks: the tallest spires at the back, a middle
    rank of towers (curving and tapering, saucer-topped, slabs and the great
    arch), and a front rank of low domes and terraces along the far shore.
    Returns the towers drawn (for reflections and skybridges)."""
    towers = []

    def T(kind, dx, w, h, depth, **kw):
        towers.append(dict(kind=kind, x=cx + dx * s, w=w * s, h=h * s, depth=depth, kw=kw))

    # the back rank: the tallest spires
    T('ring', 0, 30, 372, 2.3)
    T('needle', -112, 22, 300, 2.5)
    T('needle', 126, 22, 322, 2.6)
    T('needle', -222, 15, 222, 2.8)
    T('needle', 222, 15, 205, 2.9)
    for k in range(18):
        dx = -300 + k * 35 + R(-10, 10)
        T('shaft', dx, R(10, 17), R(50, 140), 3.0 + R(0, 0.4))
    # the middle rank: towers
    T('curve', -50, 22, 232, 1.4, bend=-16)
    T('curve', 58, 22, 250, 1.5, bend=16)
    T('disc', -152, 15, 206, 1.2)
    T('disc2', 176, 14, 222, 1.3)
    T('disc', 300, 11, 150, 1.6)
    T('arch', -205, 150, 182, 1.0)
    T('slab', 248, 34, 126, 1.0)
    T('slab', -302, 30, 104, 1.1)
    T('slab', -100, 24, 118, 1.25)
    T('curve', 100, 15, 150, 1.7, bend=-8)
    # the front rank: low domes and terraces on the shore
    T('dome', -30, 64, 42, 0.3)
    T('terrace', 112, 86, 40, 0.25, tiers=4)
    T('terrace', -262, 70, 32, 0.3, tiers=3)
    T('dome', 232, 44, 28, 0.35)
    T('dome', -148, 38, 25, 0.4)
    T('terrace', 312, 52, 26, 0.4, tiers=3)

    towers.sort(key=lambda t: t['depth'])
    for t in towers:
        x, w, h = t['x'], t['w'], t['h']
        b = base + (3.2 - t['depth']) * 1.2 * s
        t['b'] = b
        wl = wline * (1.0 if t['depth'] < 1.0 else (0.9 if t['depth'] < 2 else 0.8))
        kind = t['kind']
        right_edge = None
        if kind in ('needle', 'ring'):
            poly = tower_needle(x, b, w, h)
        elif kind in ('shaft', 'slab'):
            poly = tower_shaft(x, b, w, h, top_taper=0.85 if kind == 'slab' else 0.6)
        elif kind in ('disc', 'disc2'):
            poly = tower_shaft(x, b, w, h * 0.78, top_taper=0.8)
        elif kind == 'curve':
            poly, right_edge = tower_curve(x, b, w, h, t['kw']['bend'])
        elif kind == 'arch':
            poly = ellipse_pts(x, b, w / 2, h, 0, math.pi, 2 * math.pi, step=2)
        elif kind == 'dome':
            poly = ellipse_pts(x, b, w, h, 0, math.pi, 2 * math.pi, step=2)
        elif kind == 'terrace':
            poly, th = terrace_poly(x, b, w, h, t['kw']['tiers'])
        t['poly'] = poly
        # decorations first (they stand in front of the body)
        if kind == 'ring':
            for f, rr in ((0.5, 1.9), (0.64, 1.6), (0.78, 1.3)):
                yy = b - h * f
                half_w = w * 0.5 * (1 - f) ** 0.9 + 2
                ring = ellipse_pts(x, yy, half_w * rr + 4 * s, 4.5 * s, 0, 0, math.pi, step=1.5)
                pen.line(ring, w=wl, hand=0.1, lift=0)
                back = ellipse_pts(x, yy, half_w * rr + 4 * s, 4.5 * s, 0, math.pi, 2 * math.pi, step=1.5)
                pen.occlude([(p[0], p[1] + 0.6) for p in ring]
                            + [(x - half_w * rr - 4 * s, yy - 0.5), (x + half_w * rr + 4 * s, yy - 0.5)])
                pen.line(back, w=wl * 0.8, hand=0.1, lift=0)
            sparkle(x, b - h - 4 * s, 9 * s, w=1.0)
        if kind in ('disc', 'disc2'):
            levels = (0.78,) if kind == 'disc' else (0.62, 0.86)
            for k, f in enumerate(levels):
                yy = b - h * f
                rx = w * (2.1 if k == len(levels) - 1 else 1.6)
                disc = ellipse_pts(x, yy, rx, rx * 0.22, 0, 0, 2 * math.pi, step=1.5)
                pen.line(disc, w=wl, hand=0.1, lift=0)
                under = ellipse_pts(x, yy + rx * 0.05, rx * 0.8, rx * 0.2, 0, 0.15, math.pi - 0.15, step=1.5)
                pen.line(under, w=0.62, hand=0, lift=0)
                pen.occlude(disc)
                if t['depth'] < 2.2 and k == len(levels) - 1:
                    sparkle(x - rx * 0.86, yy - 0.5, 4.0 * s, w=0.85, diag=0.0)
            yy = b - h * levels[-1]
            rx = w * 2.1
            cap = ellipse_pts(x, yy - rx * 0.12, w * 0.7, w * 0.55, 0, math.pi, 2 * math.pi, step=1.5)
            pen.line(cap, w=wl, hand=0.1, lift=0)
            pen.line([(x, yy - rx * 0.12 - w * 0.55), (x, b - h)], w=wl * 0.9, hand=0, lift=0)
            pen.occlude(cap + [cap[0]])
        if kind == 'arch':
            outer = poly
            inner = ellipse_pts(x, b, w / 2 - 9 * s, h - 12 * s, 0, math.pi, 2 * math.pi, step=2)
            # the band thins toward the crown
            pen.line(inner, w=wl, hand=0.1, lift=0)
            pen.line(outer, w=wl * 1.05, hand=0.1, lift=0)
            band = outer + list(reversed(inner))
            shade(band, 90, 5.0, w=0.64, keep=lambda p, x=x: p[0] > x + 6, hand=0.1)
            # ribs across the band
            for a in [math.pi + math.pi * k / 9 for k in range(1, 9)]:
                p0 = (x + math.cos(a) * (w / 2 - 9 * s), b + math.sin(a) * (h - 12 * s))
                p1 = (x + math.cos(a) * w / 2, b + math.sin(a) * h)
                pen.line([p0, p1], w=0.62, hand=0, lift=0)
            sparkle(x, b - h - 3, 5 * s, w=0.85, diag=0.0)
            pen.occlude(band)
            continue
        pen.line(poly, w=wl, hand=0.12, lift=0)
        if kind == 'dome':
            for f in (-0.5, 0.0, 0.5):
                mer = ellipse_pts(x, b, w * abs(f) + 0.01, h, 0, math.pi * (1.5 if f >= 0 else 1.0),
                                  math.pi * (2.0 if f >= 0 else 1.5), step=1.5)
                if f != 0:
                    pen.line(mer, w=0.62, hand=0, lift=0)
            pen.line([(x, b - h), (x, b)], w=0.62, hand=0, lift=0)
            lat = ellipse_pts(x, b - h * 0.55, w * 0.83, h * 0.1, 0, 0, math.pi, step=1.5)
            pen.line(lat, w=0.62, hand=0, lift=0)
            # the shaded right side of the dome
            shade(poly, 90, 5.0, w=0.62, keep=lambda p, x=x, w=w: p[0] > x + w * 0.55, hand=0.05,
                  shrink=(0.05, 0.15))
        elif kind == 'terrace':
            ntier = t['kw']['tiers']
            for k in range(ntier):
                hw = w / 2 * (1 - 0.22 * k)
                y1 = b - (k + 1) * th
                # the parapet of each terrace, and its row of openings
                pen.line([(x - hw + 1, y1 + 2.6), (x + hw - 1, y1 + 2.6)], w=0.62, hand=0, lift=0)
                xx = x - hw + 4
                while xx < x + hw * 0.45:
                    pen.line([(xx, y1 + 4.5), (xx, min(b - k * th - 1, y1 + 4.5 + th * 0.45))], w=0.62, hand=0,
                             lift=0)
                    xx += 5.5
                shade([(x + hw * 0.6, y1 + 1.6), (x + hw, y1 + 1.6), (x + hw, b - k * th), (x + hw * 0.6, b - k * th)],
                      90, 5.0, w=0.62, hand=0.05, shrink=(0.0, 0.05))
        elif kind == 'curve':
            # lines down the shaded side, following the curve
            for k in (1, 2):
                run = [(p[0] - 4.6 * k, p[1]) for p in right_edge]
                run = [q for q, p in zip(run, right_edge) if inside(q, poly)]
                if len(run) > 3:
                    pen.line(run, w=0.64, hand=0.05, lift=0.05)
            tower_detail(poly, 'needle', x, b, w, h, t['depth'])
        else:
            shade(poly, 90, 5.0 if w > 14 else 6.0, w=0.64, keep=lambda p, x=x, w=w: p[0] > x + w * 0.12, hand=0.1,
                  shrink=(0.0, 0.05))
            tower_detail(poly, 'disc' if kind == 'disc2' else kind, x, b, w,
                         h * (0.78 if kind in ('disc', 'disc2') else 1.0), t['depth'])
        if kind in ('needle', 'ring') and h > 150 * s:
            sparkle(x, b - h - 3 * s, 7 * s, w=0.9, diag=0.0)
        pen.occlude(poly)
    # the quay along the shore, in front of everything
    return towers


def craft(x, y, L, d=1, trail=70):
    """A small flying craft: a long lens with a canopy, and a faint trail."""
    body = ellipse_pts(x, y, L / 2, L * 0.15, 0, 0, 2 * math.pi, step=0.8)
    pen.line(body + [body[0]], w=0.95, hand=0, lift=0)
    can = ellipse_pts(x + d * L * 0.12, y - L * 0.08, L * 0.17, L * 0.13, 0, math.pi, 2 * math.pi, step=0.8)
    pen.line(can, w=0.85, hand=0, lift=0)
    pen.line([(x - L * 0.38, y + L * 0.03), (x + L * 0.38, y + L * 0.03)], w=0.62, hand=0, lift=0)
    pen.occlude(body)
    pen.occlude(can + [can[0]])
    tail = x - d * L / 2
    for dy in (-1.2, 1.2):
        pts = [(tail - d * 3, y + dy * 0.6), (tail - d * trail, y + dy * 2.2)]
        pen.line(pts, w=0.62, hand=0, lift=0.5, piece=(4, 10))


def glow(x0, x1, y0, n=5):
    """The city's faint glow: fine level lines over the horizon, shorter as
    they rise, seen only between the towers."""
    for k in range(n):
        y = y0 - 6 * k - 1.2 * k * k
        f = 1 - k / (n + 0.5)
        mid = (x0 + x1) / 2
        half = (x1 - x0) / 2 * f
        pts = [(mid - half, y), (mid + half, y)]
        for pc in pieces(pts, on=(20, 70), off=(6, 20), start_off=False):
            pen.line(pc, w=0.62, hand=0.1, lift=0.2, piece=(10, 30))


# ---------------------------------------------------------------- the sky, stage 2

def milky_way(ctrl, half, n_dots=260, minsep=5.5, avoid=()):
    """A faint band of the Milky Way: a drift of the smallest stars, thicker
    along its middle, and two long broken strands at its edges (as the arms
    of 01 galaxy). Returns the band's middle line."""
    mid = resample(catmull(ctrl, step=2.0), 2.0)
    ts = tangents(mid)
    placed = []
    tries = 0
    while len(placed) < n_dots and tries < n_dots * 30:
        tries += 1
        i = int(R(0, len(mid) - 1))
        v = G(0.45)
        if abs(v) > 1.05:
            continue
        p = (mid[i][0] - ts[i][1] * v * half + G(2), mid[i][1] + ts[i][0] * v * half + G(2))
        if not (12 < p[0] < 988 and 12 < p[1] < YH - 20) or any(f(p) for f in avoid):
            continue
        if any(dist(p, q) < minsep for q in placed[-150:]):
            continue
        placed.append(p)
    for p in placed:
        if pen.hidden(p):
            continue
        if R() < 0.88:
            dot(p[0], p[1], r=R(0.4, 0.65), w=0.62)
        else:
            dot(p[0], p[1], r=R(0.8, 1.1), w=0.85)
    return mid


def net_of_stars(cx, cy, sizes, W, H, rot=0.0, node=1.7, cross=0.55, gap=8.0):
    """A neural network made of stars: its nodes are stars of a few sizes
    (some small crosses), its links the finest broken lines, fully connected
    from each layer to the next."""
    c, s_ = math.cos(rot), math.sin(rot)
    layers = []
    for li, n in enumerate(sizes):
        u = (li / (len(sizes) - 1) - 0.5) * W
        col = []
        for k in range(n):
            v = ((k - (n - 1) / 2) / max(1, max(sizes) - 1)) * H
            px, py = u + G(1.5), v + G(1.5)
            col.append((cx + px * c - py * s_, cy + px * s_ + py * c))
        layers.append(col)
    for li in range(len(layers) - 1):
        for a in layers[li]:
            for b in layers[li + 1]:
                d = dist(a, b)
                if d < 2 * gap + 4:
                    continue
                pen.line([lerp(a, b, gap / d), lerp(a, b, 1 - gap / d)], w=0.6, hand=0, lift=0.42, piece=(4, 10))
    nodes = [p for col in layers for p in col]
    for li, col in enumerate(layers):
        for p in col:
            u = R()
            if u < cross:
                sparkle(p[0], p[1], R(3.6, 5.0) * node / 1.7, w=0.95, rot=R(-0.15, 0.15), diag=0.0)
            elif u < cross + 0.12:
                sparkle(p[0], p[1], R(6.5, 8.5) * node / 1.7, w=1.05, rot=R(-0.1, 0.1), diag=0.3)
            else:
                dot(p[0], p[1], r=node * R(0.75, 1.15), w=1.15)
    return nodes


def star_sky(n, region, avoid, minsep=16):
    """Plain stars of many sizes: the smallest dots, small dots, small crosses
    and a few larger four-pointed stars (as in 01 galaxy)."""
    placed = []
    tries = 0
    x0, y0, x1, y1 = region
    while len(placed) < n and tries < n * 40:
        tries += 1
        p = (R(x0, x1), R(y0, y1))
        if any(dist(p, q) < minsep for q in placed) or any(f(p) for f in avoid):
            continue
        placed.append(p)
    for p in placed:
        if pen.hidden(p):
            continue
        u = R()
        if u < 0.04:
            sparkle(p[0], p[1], R(8, 12), w=1.15, rot=R(-0.1, 0.1))
        elif u < 0.14:
            sparkle(p[0], p[1], R(3.5, 5), w=0.9, rot=R(-0.15, 0.15), diag=0.0)
        elif u < 0.38:
            dot(p[0], p[1], r=R(1.1, 1.5), w=1.1)
        else:
            dot(p[0], p[1], r=R(0.55, 0.9), w=0.85)


def far_hills(pts, w=0.8, hatch_right=True):
    """Low hills far behind the city: a fine broken line and a few strokes on
    their shaded slopes."""
    line = catmull(pts, step=2)
    pen.line(line, w=w, hand=0.3, lift=0.12)
    if hatch_right:
        for i in range(2, len(line) - 2, 3):
            a, b = line[i - 2], line[i + 2]
            slope = (b[1] - a[1]) / max(0.1, b[0] - a[0])
            if slope > 0.12 and R() < 0.55:
                p = line[i]
                L = R(5, 11)
                pen.line([(p[0] + 1.5, p[1] + 2.5), (p[0] + 1.5 + L * 0.6, p[1] + 2.5 + L * 0.8)], w=0.62, hand=0,
                         lift=0)
    return line


def woods(x0, x1, y_far, y_near, n, Hm=(8.0, 12.0)):
    """A wood of separate trees in a patch of the plain, nearest first, so the
    nearer crowns hide the farther ones."""
    cand = []
    for _ in range(n):
        X, Z = ground_of(R(x0, x1), y_far + (y_near - y_far) * R())
        cand.append((Z, X))
    cand.sort()
    for Z, X in cand:
        b = P(X, 0, Z)
        tree(b[0], b[1], F * R(*Hm) / Z, allow_hidden=True)


# =============================================================== the scene

knoll_top = catmull([(20, 846), (110, 808), (210, 792), (320, 792), (420, 812), (500, 846), (570, 890),
                     (630, 940), (660, 1000)], step=2)


def knoll_y(x):
    return min(knoll_top, key=lambda p: abs(p[0] - x))[1]


# ---- the foreground: the old tree, the people on the knoll, flowers and grasses
for x in (24, 44, 72, 96, 114):
    tuft(x, 858 + R(-3, 6), R(22, 34), n=int(R(4, 7)), w=1.05, lean=R(-0.2, 0.2), occ=True)
frame_tree(852)
front_grass(160, 420, 801, 9, 26)
family(286, 800, 220)

plants = []
for k in range(70):
    x = R(14, 645)
    yk = knoll_y(x)
    y = yk + R(4, 160) * R() ** 1.3
    if y > 978 or (14 < x < 125 and y < 875):
        continue
    plants.append((y, 'tuft', x))
for spec in [(120, 845, 'daisy'), (162, 882, 'daisy'), (424, 840, 'daisy'), (470, 884, 'daisy'), (84, 902, 'daisy'),
             (250, 905, 'daisy'), (330, 930, 'daisy'), (520, 930, 'daisy'),
             (205, 850, 'umbel'), (380, 880, 'umbel'), (560, 960, 'umbel'),
             (300, 860, 'dandelion'), (140, 930, 'dandelion'), (455, 925, 'dandelion'),
             (180, 905, 'bell'), (350, 905, 'bell'), (505, 900, 'bell'), (230, 960, 'bell'),
             (110, 880, 'seed'), (270, 880, 'seed'), (430, 900, 'seed'), (600, 975, 'seed'), (60, 935, 'seed')]:
    plants.append((spec[1], spec[2], spec[0]))
plants.sort(reverse=True)  # nearest first
for y, kind, x in plants:
    grow = 1 + (y - 780) / 260
    if kind == 'tuft':
        tuft(x, y, R(18, 44) * grow, n=int(R(3, 7)), w=1.0, lean=R(-0.15, 0.25), occ=True)
    elif kind == 'daisy':
        daisy(x, y, R(46, 64) * grow, R(7, 9) * min(1.3, grow), lean=R(-0.1, 0.15))
    elif kind == 'umbel':
        umbel(x, y, R(60, 80) * grow, R(9, 12), lean=R(-0.08, 0.08))
    elif kind == 'dandelion':
        dandelion(x, y, R(44, 60) * grow, R(7, 9), lean=R(-0.08, 0.12))
    elif kind == 'bell':
        bellflower(x, y, R(42, 58) * grow, lean=R(0.05, 0.25), n=int(R(2, 4)))
    elif kind == 'seed':
        seed_grass(x, y, R(70, 100) * grow, lean=R(0.0, 0.25))
for (bx, by, a, L, cu) in [(40, 975, -1.25, 150, 0.35), (75, 985, -0.7, 170, 0.35), (175, 992, -1.05, 120, 0.3),
                           (120, 880, -0.55, 95, 0.3), (590, 992, -2.0, 110, -0.3)]:
    frond((bx, by), a, L, curl=cu)
knoll_hatch(knoll_top)
flank = [p for p in knoll_top if p[0] > 440]
for k in (1, 2, 3):
    run = offset(flank, -5.0 * k)
    run = run[int(len(run) * 0.12 * k):]
    for pc in pieces(run, on=(30, 90), off=(5, 14), start_off=False):
        pen.line(pc, w=0.74 - 0.03 * k, hand=0.3, lift=0.1, piece=(15, 40))
pen.line(knoll_top, w=2.0, hand=0.7, lift=0.15)
pen.occlude(knoll_top + [(1000, 1000), (0, 1000), (0, 828)])
# a thin margin of clear paper round the people against the land behind
pen.add_halo((150, 570, 432, 812), r=4.0)

# ---- the near verge at the lower right, by the road
verge = []
for k in range(18):
    verge.append((R(925, 992), 'tuft', R(770, 990)))
verge += [(962, 'daisy', 905), (975, 'dandelion', 822), (984, 'seed', 948), (958, 'bell', 860)]
verge.sort(reverse=True)
for y, kind, x in verge:
    if kind == 'tuft':
        tuft(x, y, R(24, 50), n=int(R(3, 6)), w=1.05, lean=R(-0.2, 0.1), occ=True)
    elif kind == 'daisy':
        daisy(x, y, 62, 8.5, lean=-0.08)
    elif kind == 'dandelion':
        dandelion(x, y, 56, 8, lean=-0.05)
    elif kind == 'seed':
        seed_grass(x, y, 96, lean=-0.2)
    elif kind == 'bell':
        bellflower(x, y, 50, lean=-0.15, n=3)
frond((990, 994), -2.25, 130, curl=-0.3)

# ---- the nearer trees stand in front of the ways (which lie flat on the plain) and of the skyway's piers
groves([(752, 716, 1), (566, 742, 1)])
woods(880, 1010, 694, 752, 9, Hm=(7.0, 10.0))
groves([(690, 690, 1)])

# ---- the ways to the city
R1 = [(860, 1010), (760, 880), (640, 760), (590, 690), (612, 648), (648, 622), (654, 608), (650, 603.5)]
R3 = [(560, 1000), (540, 900), (512, 820), (494, 750), (492, 690), (480, 645), (464, 618), (456, 604.5)]
ground_road(R1, 9.0)
ground_road(R3, 5.5)
skyway([(1010, 700), (900, 672), (820, 640), (775, 620), (740, 608), (705, 603)], 8.0,
       elev=lambda t: 26 + 50 * t ** 1.5, pylon_every=70.0, min_sep=38.0)

# ---- the middle ground, nearest first: woods, single trees, then the folds of the meadow
groves([(548, 676, 1), (930, 664, 1)])
belt(120, 470, 656, Hm=11.0)
groves([(520, 640, 2), (596, 632, 1), (430, 628, 2)])
belt(8, 362, 614, Hm=12.0)
for (x0, x1, y, rise) in [(600, 1000, 860, 0.06), (660, 1000, 790, 0.08), (420, 640, 790, 0.07), (640, 920, 712, 0.1),
                          (8, 160, 760, 0.08), (500, 640, 712, 0.1), (8, 330, 690, 0.1), (540, 680, 662, 0.12),
                          (300, 470, 636, 0.12), (8, 200, 628, 0.12)]:
    fold(x0, x1, y, rise=rise)
grass_ticks(110, (8, 992), 650, 950)

# ---- the city on the far shore, the lake before it, the hills behind
towers = city(650, YH + 1.5, 1.0, wline=1.1)
skybridge(600, 706, 470, 7)
skybridge(706, 826, 430, 7)
skybridge(500, 598, 520, 5)
lake_poly = [(664, 606.5), (1000, 606.5)] + catmull(
    [(1000, 641), (960, 646), (880, 650), (790, 647), (722, 638), (686, 625), (670, 614), (664, 606.5)], step=2)
lake(lake_poly, towers, 606.5)
pen.line(catmull([(1000, 641), (960, 646), (880, 650), (790, 647), (722, 638), (686, 625), (670, 614)], step=2),
         w=0.9, hand=0.3, lift=0.25, piece=(10, 30))
for x in (676, 700, 742, 905, 958):
    yy = span_at(lake_poly, 620) and min(p[1] for p in lake_poly if abs(p[0] - x) < 6 and p[1] > 610) or 640
    tuft(x, yy + 1, R(6, 9), n=4, w=0.7, lean=R(-0.1, 0.1))
glow(480, 880, 596, n=3)
far_hills([(8, 590), (90, 582), (200, 586), (330, 576), (420, 568), (540, 562), (650, 568), (760, 558), (870, 568),
           (992, 578)])
horizon_line(8, 664, YH + 4)
craft(470, 345, 22, d=-1)
craft(735, 252, 12, d=1, trail=40)

# ---- the sky: the Milky Way, five networks of stars, plain stars
nets = [
    dict(cx=410, cy=268, sizes=[3, 4, 3], W=160, H=88, rot=-0.08),
    dict(cx=830, cy=92, sizes=[2, 3, 2], W=130, H=70, rot=0.1),
    dict(cx=560, cy=46, sizes=[2, 3, 2], W=96, H=46, rot=-0.15),
    dict(cx=905, cy=302, sizes=[2, 3, 1], W=90, H=58, rot=0.06),
    dict(cx=345, cy=442, sizes=[2, 2, 1], W=64, H=36, rot=0.1),
]
boxes = []
for nt in nets:
    net_of_stars(nt['cx'], nt['cy'], nt['sizes'], nt['W'], nt['H'], nt['rot'])
    boxes.append((nt['cx'], nt['cy'], nt['W'] / 2 + 18, nt['H'] / 2 + 18))
avoid = [lambda p, b=b: abs(p[0] - b[0]) < b[2] and abs(p[1] - b[1]) < b[3] for b in boxes]
milky_way([(320, -10), (450, 60), (600, 130), (760, 185), (900, 215), (1010, 235)], 44, n_dots=300, avoid=avoid)
star_sky(220, (14, 14, 986, YH - 14), avoid)


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
