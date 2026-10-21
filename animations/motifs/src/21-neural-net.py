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

from pen import Pen, catmull, ellipse_pts, resample, lerp, dist, inside, length, clip_segments

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


# ---------------------------------------------------------------- people, seen from behind

# Right halves of the outlines, in units of the figure's height, feet at y=0.
MAN = [(0.034, -0.868), (0.085, -0.842), (0.125, -0.822), (0.143, -0.792), (0.150, -0.72), (0.153, -0.62),
       (0.148, -0.53), (0.139, -0.465), (0.134, -0.425), (0.118, -0.41), (0.108, -0.43), (0.112, -0.47),
       (0.116, -0.56), (0.112, -0.65), (0.106, -0.705), (0.100, -0.64), (0.094, -0.565), (0.101, -0.50),
       (0.102, -0.44), (0.090, -0.33), (0.074, -0.24), (0.064, -0.13), (0.054, -0.04), (0.060, -0.012),
       (0.042, 0.0), (0.020, -0.012), (0.018, -0.05), (0.021, -0.24), (0.013, -0.42), (0.0, -0.47)]
WOMAN = [(0.030, -0.868), (0.078, -0.845), (0.112, -0.826), (0.128, -0.795), (0.134, -0.72), (0.136, -0.63),
         (0.132, -0.545), (0.125, -0.48), (0.121, -0.44), (0.106, -0.428), (0.097, -0.446), (0.100, -0.49),
         (0.103, -0.57), (0.100, -0.65), (0.094, -0.70), (0.088, -0.64), (0.080, -0.575), (0.096, -0.50),
         (0.128, -0.36), (0.150, -0.215), (0.112, -0.205), (0.058, -0.20), (0.050, -0.12), (0.045, -0.04),
         (0.050, -0.012), (0.034, 0.0), (0.016, -0.012), (0.014, -0.05), (0.014, -0.19), (0.0, -0.198)]
CHILD = [(0.040, -0.800), (0.095, -0.775), (0.130, -0.752), (0.148, -0.70), (0.155, -0.60), (0.150, -0.50),
         (0.142, -0.445), (0.130, -0.410), (0.112, -0.405), (0.106, -0.43), (0.114, -0.50), (0.116, -0.60),
         (0.110, -0.665), (0.104, -0.60), (0.104, -0.52), (0.110, -0.455), (0.104, -0.38), (0.090, -0.22),
         (0.074, -0.045), (0.080, -0.014), (0.052, 0.0), (0.030, -0.012), (0.026, -0.05), (0.027, -0.25),
         (0.016, -0.40), (0.0, -0.44)]
HEAD = {'man': (-0.928, 0.058, 0.068), 'woman': (-0.925, 0.054, 0.066), 'child': (-0.885, 0.085, 0.1)}


def person(kind, x, y, H, lean=0.0):
    """A figure seen from behind, feet at (x, y), H tall; returns its outline."""
    half = {'man': MAN, 'woman': WOMAN, 'child': CHILD}[kind]
    body = catmull(mirror_half(half), closed=True, step=1.5 / H, tension=0.5)
    body = [(px + lean * (-py), py) for px, py in body]
    body = place(body, x, y, H)
    hy, hrx, hry = HEAD[kind]
    hcx = x + lean * (-hy) * H
    head = ellipse_pts(hcx, y + hy * H, hrx * H, hry * H, 0, 0, 2 * math.pi, step=1.2)
    shapes = []
    if kind == 'woman':
        # long hair down the back, over the shoulders
        hair = [(0.0, -0.995), (0.05, -0.985), (0.068, -0.94), (0.07, -0.88), (0.085, -0.80), (0.09, -0.74),
                (0.06, -0.715), (0.0, -0.71)]
        hair = catmull(mirror_half(hair), closed=True, step=1.5 / H)
        hair = place([(px + lean * (-py), py) for px, py in hair], x, y, H)
        pen.line(hair, w=1.6, hand=0.5, lift=0.1)
        for k in range(9):
            u = (k + 0.5) / 9 - 0.5
            top = (hcx + u * 0.09 * H, y - 0.985 * H + abs(u) * 0.05 * H)
            bot = (hcx + u * 0.15 * H, y - 0.725 * H)
            mid = (hcx + u * 0.12 * H + G(0.6), y - 0.85 * H)
            pen.line(catmull([top, mid, bot], step=2), w=0.75, hand=0.4, lift=0.1)
        pen.occlude(hair)
        shapes.append(hair)
    pen.line(head, w=1.6, hand=0.4, lift=0.08)
    if kind != 'woman':
        # short hair: strokes over the back of the head
        for k in range(6 if kind == 'man' else 5):
            u = (k + 0.5) / (6 if kind == 'man' else 5) - 0.5
            top = (hcx + u * hrx * H * 1.2, y + (hy - hry * 0.9) * H)
            bot = (hcx + u * hrx * H * 1.5, y + (hy + hry * 0.55) * H)
            pen.line(catmull([top, ((top[0] + bot[0]) / 2 + G(0.5), (top[1] + bot[1]) / 2), bot], step=2),
                     w=0.75, hand=0.3, lift=0.05)
    pen.occlude(head)
    pen.line(body, w=2.0, hand=0.6, lift=0.12)
    # a few inner lines: the seam down the back, the waist
    pen.line([(x, y - 0.80 * H), (x + lean * 0.6 * H, y - 0.56 * H)], w=0.9, hand=0.4)
    # tone: the back is turned from the city's light; fine hatching, lighter on the left
    shade(body, 78, 5.6, w=0.72, keep=lambda p: p[0] > x - 0.04 * H, hand=0.35)
    shade(body, 78, 9.0, w=0.65, keep=lambda p: p[0] <= x - 0.04 * H and p[1] < y - 0.45 * H, hand=0.35)
    pen.occlude(body)
    return body


# ---------------------------------------------------------------- plants

def blade(base, h, lean, w=1.0, curl=0.0):
    x, y = base
    tip = (x + lean * h, y - h)
    mid = (x + lean * h * 0.4 + curl * h * 0.15, y - h * 0.55)
    pen.line(catmull([base, mid, tip], step=2), w=w, hand=0.25, lift=0.02, taper=0.6, piece=(30, 90))


def tuft(x, y, h, n=5, spread=0.5, w=1.0, lean=0.0):
    for k in range(n):
        u = (k + 0.5) / n - 0.5
        blade((x + u * h * 0.18, y + abs(u) * 2), h * R(0.6, 1.0), lean + u * spread + G(0.08), w=w * R(0.85, 1.1),
              curl=G(0.5))


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


def skyway(ctrl, W, elev, pylon_every=10):
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
    # pylons: slender, tapering, from the deck down to the plain
    k = 0
    n = len(foot)
    i = 0
    while i < n:
        X, Z, Y = foot[i]
        p_top = P(X, Y - 1.6, Z)
        p_bot = P(X, 0, Z)
        hw = clamp(F * 0.9 / Z, 0.6, 9)
        if p_bot[1] - p_top[1] > 7:
            for s in (-1, 1):
                pen.line([(p_top[0] + s * hw * 0.7, p_top[1]), (p_bot[0] + s * hw, p_bot[1])],
                         w=clamp(F * 0.05 / Z * 12, 0.7, 1.6), hand=0.1, lift=0)
            pen.occlude([(p_top[0] - hw * 0.7, p_top[1]), (p_top[0] + hw * 0.7, p_top[1]),
                         (p_bot[0] + hw, p_bot[1]), (p_bot[0] - hw, p_bot[1])])
        # the next pylon, at least `pylon_every` units on along the page
        d = 0.0
        j = i
        while j < n - 1 and d < pylon_every:
            d += dist(near[j + 1], near[j])
            j += 1
        i = j if j > i else n
        k += 1
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


def tree_clump(X, Z, Hm=12.0):
    """A round-crowned park tree far out on the plain, sized by its distance:
    a lobed crown (a few rounded masses), shaded on its lower right, and a
    short trunk."""
    base = P(X, 0, Z)
    h = F * Hm / Z
    if h < 4:
        return False
    cx, cy = base[0], base[1] - h * 0.6
    rx, ry = h * R(0.32, 0.42), h * 0.37
    ctrl = []
    m = 11
    ph = R(0, 6.3)
    for k in range(m):
        a = 2 * math.pi * k / m
        rr = 1 + 0.10 * math.sin(4 * a + ph) + R(-0.06, 0.06)
        ctrl.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr * (0.85 if math.sin(a) > 0 else 1.0)))
    crown = catmull(ctrl, closed=True, step=1.2)
    trunk = [(base[0] - h * 0.035, base[1]), (base[0] - h * 0.03, cy + ry * 0.7),
             (base[0] + h * 0.03, cy + ry * 0.7), (base[0] + h * 0.035, base[1])]
    probe = crown + trunk
    if any(pen.hidden(q) for q in probe[::3]):
        return False
    w = clamp(0.6 + h / 45, 0.7, 1.2)
    pen.line(crown, w=w, hand=0.25, lift=0.05)
    if h > 9:
        shade(crown, 60, 5.0, w=0.65, keep=lambda q: (q[0] - cx) / rx + (q[1] - cy) / ry > 0.3, hand=0.2)
    pen.occlude(crown)
    pen.line(trunk[:2], w=w * 0.9, hand=0.1, lift=0)
    pen.line(trunk[2:], w=w * 0.9, hand=0.1, lift=0)
    pen.occlude(trunk)
    return True


def grove(sx, sy, n, spread):
    """A few trees together, on the plain about page point (sx, sy)."""
    X0, Z0 = ground_of(sx, sy)
    placed = 0
    for _ in range(n * 4):
        if placed >= n:
            break
        dX = G(spread) * Z0 / F * 40
        dZ = G(0.12) * Z0
        if tree_clump(X0 + dX, max(40.0, Z0 + dZ), R(9, 15)):
            placed += 1


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
    person('child', 288, 806, 136)
    person('woman', 236, 798, 200, lean=0.01)
    person('man', 344, 800, 220, lean=-0.01)
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
           elev=lambda t: 26 + 50 * t ** 1.5, pylon_every=34)

    for (sx, sy, n) in [(470, 640, 4), (540, 625, 3), (720, 640, 5), (860, 618, 3), (420, 612, 3), (585, 607, 3),
                        (940, 660, 3)]:
        grove(sx, sy, n, 1.0)

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
    person('child', 352, 934, 150)
    person('woman', 296, 924, 222, lean=0.01)
    person('man', 412, 928, 244, lean=-0.012)
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
           elev=lambda t: 22 + 70 * t ** 1.4, pylon_every=44)

    for (sx, sy, n) in [(300, 520, 4), (640, 520, 5), (760, 480, 4), (880, 545, 4), (200, 470, 3), (420, 458, 3),
                        (600, 452, 3), (900, 455, 3), (130, 600, 3), (720, 600, 4)]:
        grove(sx, sy, n, 1.0)
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

# the set's finest line is 0.6
pen.strokes = [(p, max(0.6, w)) for p, w in pen.strokes]
pen.save(OUT)
pen.report()
