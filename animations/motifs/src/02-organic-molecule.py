"""02 Organic molecule: six rings swimming in the primordial soup.

Maxim, on the passed drawing (one large benzene ring): "keep the organic
molecule as is but have multiple of them swimming in some 'Ursuppe'."

So the ring is kept exactly as it was drawn (a perfectly regular hexagon with
three alternating Kekule double bonds, each a second, shorter line just inside
the ring; no letters; the line laid down in two close passes; the tidy cast
shadow of ticks along the light from the upper left), and several of them, at
different sizes, turns and depths, swim in a warm, shallow early sea, seen in
section as in a natural-history plate: the surface line with a fine broken
line under it, the water as tidy rows of broken, gently waving lines that
open up near the surface, close up with depth and dissolve at the sides, fine
suspended particles, bubbles rising from a vent in the sediment floor and from
a crack, breaking at the surface with small ripples; beyond the water a far
volcanic shore on the horizon, its plume of smoke drifting off (early Earth),
drawn light because it is far away.

Depth: the nearest ring is the passed drawing's ring, frontal and heaviest;
the others are smaller and lighter the farther they are, and turned in the
water (foreshortened about an axis), so they tumble rather than tile. The
water shows through every ring but keeps clear of its lines and shadow; the
farthest ring lies deep enough that the water's lines pass in front of it.

Not mirrored (slot 02 faces as drawn). Run from this folder:
    python3 02-organic-molecule.py
"""

import math

from pen import Pen, lerp, inside, clip_segments, resample, catmull, ellipse_pts

pen = Pen(seed=202)
rng = pen.rng

LIGHT = 60.0                          # the rings' shadows fall this way (degrees, y down)
LU = (math.cos(math.radians(LIGHT)), math.sin(math.radians(LIGHT)))

# ---------------------------------------------------------------- the scene's frame

SURF_Y = 250.0                        # mean water surface
FLOOR_Y = 868.0                       # mean sediment floor
X0, X1 = 70.0, 930.0                  # the plate's width
VENT = 702.0                          # the vent's mound, on the floor


def surface_y(x):
    """The water surface: long low swells and small waves on them."""
    return (SURF_Y + 4.0 * math.sin(x * 0.011 + 0.6) + 2.2 * math.sin(x * 0.047 + 1.9)
            + 1.0 * math.sin(x * 0.11 + 0.3))


def floor_y(x):
    """The sediment floor, with a low mound (the vent) right of centre."""
    mound = -44.0 * math.exp(-((x - VENT) / 62.0) ** 2)
    return FLOOR_Y + 9.0 * math.sin(x * 0.013 + 2.0) + 4.0 * math.sin(x * 0.041) + mound


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def edges(y):
    """Where the water's lines end, left and right, at height y: a soft, uneven vignette."""
    u = (y - SURF_Y) / (FLOOR_Y - SURF_Y)
    inset = 10.0 + 170.0 * (u - 0.35) ** 2
    l = X0 + inset + 22.0 * math.sin(y * 0.017 + 1.3) + 10.0 * math.sin(y * 0.061)
    r = X1 - inset - 22.0 * math.sin(y * 0.015 + 4.1) - 10.0 * math.sin(y * 0.053 + 2.0)
    return l, r


def fade(x, y):
    """1 well inside the water, falling to 0 at its left and right edges."""
    l, r = edges(y)
    return smooth(l, l + 220.0, x) * smooth(r, r - 220.0, x)


# ---------------------------------------------------------------- the rings

def hull(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


class Ring:
    """One benzene ring, drawn as the passed drawing drew it, scaled.

    near   1 for the nearest ring ... 0 for the farthest: sets weight and passes
    """

    def __init__(self, c, R, rot, near, tilt=0.0, tilt_axis=0.0):
        self.c, self.R, self.rot, self.near = c, R, rot, near
        self.f = math.cos(math.radians(tilt))      # the ring turned away from us about an axis
        self.ax = math.radians(tilt_axis)
        s = (R / 405.0) ** 0.6                      # the shadow shrinks more gently than the ring
        self.sh_from = 10.0 * s
        self.sh_len = 29.0 * s
        self.w = 1.5 + 1.2 * near                   # 2.7 for the nearest
        self.passes = 2 if near > 0.45 else 1
        self.sh_w = 0.62 + 0.13 * near
        self.sh_gap = 5.0 + 1.0 * near
        pts = [self.corner(k) for k in range(6)]
        sh = [(x + LU[0] * self.sh_len, y + LU[1] * self.sh_len) for x, y in pts]
        self.body = hull(pts + sh)

    def P(self, lx, ly):
        """A point given in the ring's own frontal frame (centre 0, 0) on the page."""
        a = math.radians(self.rot)
        x, y = lx * math.cos(a) - ly * math.sin(a), lx * math.sin(a) + ly * math.cos(a)
        ca, sa = math.cos(self.ax), math.sin(self.ax)
        u, v = x * ca + y * sa, -x * sa + y * ca     # along / across the tilt axis
        v *= self.f
        return (self.c[0] + u * ca - v * sa, self.c[1] + u * sa + v * ca)

    def corner(self, k, r=None):
        a = math.radians(-90 + 60 * k)
        rr = self.R if r is None else r
        return self.P(rr * math.cos(a), rr * math.sin(a))

    def inner(self, k):
        R = self.R
        a = math.radians(-90 + 60 * k)
        b = math.radians(-90 + 60 * (k + 1))
        pa, pb = (R * math.cos(a), R * math.sin(a)), (R * math.cos(b), R * math.sin(b))
        m = lerp(pa, pb, 0.5)
        ml = math.hypot(*m)
        ux, uy = -m[0] / ml, -m[1] / ml
        o = 0.16 * R
        qa = (pa[0] + ux * o, pa[1] + uy * o)
        qb = (pb[0] + ux * o, pb[1] + uy * o)
        return lerp(qa, qb, 0.13), lerp(qa, qb, 0.87), (ux, uy)

    def draw(self):
        c, R = self.c, self.R
        gap = 1.2
        for j in range(self.passes):
            d = (j - (self.passes - 1) / 2) * gap
            r = R + d / math.cos(math.radians(30))
            stroke([self.corner(k % 6, r) for k in range(7)], self.w)
        inners = []
        for k in (0, 2, 4):
            a, b, (ux, uy) = self.inner(k)
            inners.append((self.P(*a), self.P(*b)))
            for j in range(self.passes):
                d = (j - (self.passes - 1) / 2) * gap
                stroke([self.P(a[0] + ux * d, a[1] + uy * d), self.P(b[0] + ux * d, b[1] + uy * d)], self.w)
        # the cast shadow: ticks along the light, all one length
        srcs = [(self.corner(k), self.corner(k + 1)) for k in range(6)] + inners

        def mv(p, d):
            return (p[0] + LU[0] * d, p[1] + LU[1] * d)
        swept = [[mv(a, self.sh_from), mv(b, self.sh_from), mv(b, self.sh_len), mv(a, self.sh_len)] for a, b in srcs]
        self.segs, self.swept = srcs, [[mv(a, 0.0), mv(b, 0.0), mv(b, self.sh_len), mv(a, self.sh_len)] for a, b in srcs]
        guard = 1.5 + 0.4 * self.w

        def in_shadow(p):
            if not any(inside(p, q) for q in swept):
                return False
            for a, b in srcs:
                abx, aby = b[0] - a[0], b[1] - a[1]
                t = max(0.0, min(1.0, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / (abx * abx + aby * aby)))
                if math.hypot(p[0] - a[0] - abx * t, p[1] - a[1] - aby * t) < guard:
                    return False
            return True
        nx, ny = -LU[1], LU[0]
        ts = [x * nx + y * ny for q in swept for x, y in q]
        c0 = c[0] * nx + c[1] * ny
        t = min(ts) + self.sh_gap * 0.5
        while t < max(ts):
            base = (c[0] + nx * (t - c0), c[1] + ny * (t - c0))
            p0 = (base[0] - LU[0] * (R + 60), base[1] - LU[1] * (R + 60))
            p1 = (base[0] + LU[0] * (R + 60), base[1] + LU[1] * (R + 60))
            for run in clip_segments([p0, p1], in_shadow):
                if math.dist(run[0], run[-1]) > 1.8:
                    stroke([run[0], run[-1]], self.sh_w)
            t += self.sh_gap

    def near_lines(self, p, m):
        """Is p within m of one of the ring's lines or in (or within m of) its shadow?
        (The water shows through a ring, but keeps clear of its lines.)"""
        if any(inside(p, q) for q in self.swept):
            return True
        for poly in [list(sg) for sg in self.segs] + self.swept:
            n = len(poly)
            for i in range(n - (1 if n == 2 else 0)):
                a, b = poly[i], poly[(i + 1) % n]
                abx, aby = b[0] - a[0], b[1] - a[1]
                L2 = abx * abx + aby * aby or 1
                t = max(0.0, min(1.0, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / L2))
                if math.hypot(p[0] - a[0] - abx * t, p[1] - a[1] - aby * t) < m:
                    return True
        return False

    def keeps_out(self, p, m):
        """Is p within m of the ring or its shadow, inside included?"""
        if inside(p, self.body):
            return True
        n = len(self.body)
        for i in range(n):
            a, b = self.body[i], self.body[(i + 1) % n]
            abx, aby = b[0] - a[0], b[1] - a[1]
            L2 = abx * abx + aby * aby or 1
            t = max(0.0, min(1.0, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / L2))
            if math.hypot(p[0] - a[0] - abx * t, p[1] - a[1] - aby * t) < m:
                return True
        return False


def stroke(pts, w):
    """A sure, ruled pass (the rings): no wobble, no lifts, an even weight."""
    pen.raw(resample(pts, 3.0), w * pen.r(0.98, 1.02))


# nearest first: (centre, corner radius, turn in degrees, nearness)
RINGS = [
    Ring((420.0, 592.0), 178.0, 0.0, 1.0),
    Ring((742.0, 448.0), 100.0, 14.0, 0.72, tilt=34.0, tilt_axis=70.0),
    Ring((196.0, 382.0), 70.0, -11.0, 0.5, tilt=48.0, tilt_axis=-20.0),
    Ring((738.0, 742.0), 60.0, 31.0, 0.36, tilt=28.0, tilt_axis=140.0),
    Ring((168.0, 700.0), 42.0, 22.0, 0.2, tilt=55.0, tilt_axis=10.0),
    Ring((548.0, 330.0), 32.0, 40.0, 0.0, tilt=38.0, tilt_axis=100.0),
]
VEILED = {5}            # deep enough that the water's lines pass in front of it


def clear_of_rings(p, m=12.0):
    """For bubbles and particles: outside every ring, with a margin."""
    return not any(r.keeps_out(p, m * (0.4 + 0.6 * r.near)) for i, r in enumerate(RINGS) if i not in VEILED)


def clear_of_lines(p, m=9.0):
    """For the water's lines: anywhere but on or close to a ring's lines and shadow."""
    return not any(r.near_lines(p, m * (0.45 + 0.55 * r.near)) for i, r in enumerate(RINGS) if i not in VEILED)


# ---------------------------------------------------------------- draw: rings first (front), then the soup

for r in RINGS:
    r.draw()


def wline(pts, w, hand=0.25):
    pen.line(pts, w=w, hand=hand, lift=0.0, piece=(60, 160), occlude=False)


# the surface: one sure line across, breaking up at either end
xs = [X0 + 8 + k * 3.0 for k in range(int((X1 - X0 - 16) / 3.0))]
pts = [(x, surface_y(x)) for x in xs]
n = len(pts)
a, b = int(n * 0.08), int(n * 0.92)
wline(pts[a:b], 1.7)
for lo, hi in ((0, a), (b, n)):
    k = lo
    while k < hi - 2:
        ln = rng.randint(3, 8)
        seg = pts[k:min(hi, k + ln)]
        if len(seg) > 1:
            wline(seg, 1.2, 0.15)
        k += ln + rng.randint(2, 4)
# a fine broken line just under it, the surface seen a little from above
x = X0 + 70
while x < X1 - 70:
    L = rng.uniform(30, 90)
    seg = [(xx, surface_y(xx) + 7.5) for xx in [x + L * i / 10 for i in range(11)]]
    if fade(x + L / 2, SURF_Y + 30) > 0.35:
        wline(seg, 0.8, 0.15)
    x += L + rng.uniform(25, 70)

# the water: rows of broken, gently waving lines, opening up near the surface and closing with depth
y = SURF_Y + 22.0
while y < FLOOR_Y - 10:
    u = (y - SURF_Y) / (FLOOR_Y - SURF_Y)
    l, r = edges(y)
    x = l + rng.uniform(0, 40)
    ph = rng.uniform(0, 6.3)
    while x < r:
        f = fade(x, y)
        L = rng.uniform(22, 90) * (0.45 + 0.55 * f) * (1.15 - 0.3 * u)
        xe = min(r, x + L)
        if rng.random() < (0.25 + 0.75 * f) * (0.6 + 0.4 * smooth(0.0, 0.55, u)):
            seg = [(xx, y + 2.0 * math.sin(xx * 0.065 + ph)) for xx in [x + (xe - x) * i / 16 for i in range(17)]]
            for run in clip_segments(seg, lambda p: clear_of_lines(p) and p[1] < floor_y(p[0]) - 10):
                if math.dist(run[0], run[-1]) > 7:
                    wline(run, 0.7 + 0.16 * u, 0.2)
        x = xe + rng.uniform(14, 46) * (1.25 - 0.55 * u) * (1.6 - 0.6 * f)
    y += 30.0 - 16.0 * u + rng.uniform(-1.0, 1.0)

# the floor: a sediment line, breaking up at its ends
fx = [X0 + 40 + k * 3.0 for k in range(int((X1 - X0 - 80) / 3.0))]
fpts = [(x, floor_y(x)) for x in fx]
n = len(fpts)
a, b = int(n * 0.07), int(n * 0.93)
pen.line(fpts[a:b], w=1.5, hand=0.35, lift=0.06, piece=(50, 120), occlude=False)
for lo, hi in ((0, a), (b, n)):
    k = lo
    while k < hi - 2:
        ln = rng.randint(3, 7)
        seg = fpts[k:min(hi, k + ln)]
        if len(seg) > 1:
            wline(seg, 1.0, 0.2)
        k += ln + rng.randint(2, 5)
# the vent: a mouth at the top of the mound
vx, vy = VENT, floor_y(VENT)
pen.line(ellipse_pts(vx, vy + 2.5, 13, 3.5, 0.0, math.pi * 0.0, math.pi * 1.0), w=1.2, hand=0, lift=0, occlude=False)
pen.line(ellipse_pts(vx, vy + 2.5, 13, 3.5, 0.0, math.pi * 1.0, math.pi * 2.0), w=1.0, hand=0, lift=0, occlude=False)
# the mound's shaded right flank
for k in range(7):
    x = vx + 12 + k * 7.0
    y0 = floor_y(x) + 3
    wline([(x, y0), (x + 6, y0 + 16 - k * 1.5)], 0.7, 0.1)
# pebbles, a few, resting on the floor
for x, rx, ry in ((148, 12, 6), (172, 7, 4), (318, 9, 5), (338, 5, 3), (512, 14, 6.5), (612, 8, 4.5),
                  (790, 11, 5.5), (812, 6, 3.5), (872, 9, 4.5)):
    cy = floor_y(x) - ry + 1.5
    pen.line(ellipse_pts(x, cy, rx, ry, 0.0, math.pi * 1.0, math.pi * 2.0), w=1.1, hand=0, lift=0, occlude=False)
    pen.line(ellipse_pts(x, cy, rx * 0.7, ry * 0.55, 0.0, math.radians(15), math.radians(75)), w=0.7, hand=0, lift=0, occlude=False)
# the sediment in section: short strokes under the floor, thinning downward
for j in range(3):
    off = 10.0 + j * 10.0
    x = X0 + 80 + rng.uniform(0, 40) + j * 40
    while x < X1 - 80 - j * 40:
        L = rng.uniform(14, 40) * (1 - 0.2 * j)
        seg = [(xx, floor_y(xx) + off) for xx in [x + L * i / 6 for i in range(7)]]
        wline(seg, 0.7, 0.2)
        x += L + rng.uniform(16, 44) * (1 + 0.7 * j)


# bubbles: rising from the vent and from a crack, growing as they rise
def bubble(x, y, r):
    if r < 3.0:
        pen.dot(x, y, r=max(1.0, r * 0.7), w=0.9)
        return
    pen.line(ellipse_pts(x, y, r, r * 0.96, 0, 0, 2 * math.pi + 0.15, step=1.2), w=0.9 + 0.03 * r, hand=0, lift=0, occlude=False)
    pen.line(ellipse_pts(x, y, r * 0.55, r * 0.55, 0, math.radians(195), math.radians(250), step=0.8), w=0.7, hand=0, lift=0, occlude=False)


def bubble_column(x0, y0, y1, n, r0, r1, sway, ph):
    for k in range(n):
        u = (k + 0.5) / n
        y = y0 + (y1 - y0) * u ** 0.85
        x = x0 + sway * math.sin(u * 6.5 + ph) + rng.uniform(-3, 3)
        r = r0 + (r1 - r0) * u + rng.uniform(-0.5, 0.5)
        if clear_of_rings((x, y), 5 + r):
            bubble(x, y, r)


bubble_column(vx, vy - 16, SURF_Y + 20, 17, 2.4, 9.0, 11.0, 0.4)
bubble_column(vx + 22, vy - 50, SURF_Y + 70, 7, 2.0, 6.0, 8.0, 2.1)
bubble_column(318.0, floor_y(318.0) - 16, SURF_Y + 26, 11, 2.0, 7.5, 10.0, 4.0)

# where bubbles break: a small dome on the surface and ripples running off either side
for bx, sc in ((vx + 4, 1.0), (322.0, 0.85)):
    by = surface_y(bx)
    pen.line(ellipse_pts(bx, by, 7 * sc, 5 * sc, 0, math.pi * 1.05, math.pi * 1.95, step=0.8), w=1.0, hand=0, lift=0, occlude=False)
    for j, d in enumerate((15, 26)):
        for sgn in (-1, 1):
            cx = bx + sgn * d * sc
            pen.line(ellipse_pts(cx, surface_y(cx) - 0.5, 5.5 * sc, 2.6 * sc, 0, math.pi * 1.1, math.pi * 1.9, step=0.8),
                     w=0.85 - 0.1 * j, hand=0, lift=0, occlude=False)

# beyond the water: a far volcanic shore on the horizon, smoking (light: it is far off)
def volcano(xl, xr, xc, top, crater, w):
    """A cone from xl to xr on the horizon, its crater (half width `crater`) at xc, `top` above
    the surface; the slopes concave, steep under the rim and spreading at the foot."""
    yt = SURF_Y - top

    def left_at(t):                       # t 0 at the foot, 1 at the rim
        x = xl + (xc - crater - xl) * t
        return (x, surface_y(xl) + (yt - surface_y(xl)) * t ** 1.45)

    def right_at(t):                      # t 0 at the rim, 1 at the foot
        x = xc + crater + (xr - xc - crater) * t
        return (x, yt + (surface_y(xr) - yt) * (1 - (1 - t) ** 1.45))
    left = [left_at(i / 30) for i in range(31)]
    rim = [(xc - crater + 2 * crater * t, yt + 4.0 * math.sin(math.pi * t)) for t in [i / 8 for i in range(1, 8)]]
    right = [right_at(i / 30) for i in range(31)]
    pen.line(left + rim + right, w=w, hand=0.3, lift=0.04, piece=(40, 110), occlude=False)
    # the shadowed right flank: form lines of the cone, running from under the rim to the foot
    apex = (xc + crater * 0.5, yt + 2)
    for k in range(5):
        t = 0.30 + 0.15 * k                               # where along the right slope's foot it lands
        foot = right_at(t)
        foot = (foot[0] - 6, foot[1] + (surface_y(foot[0]) - foot[1]) * 0.9 - 2)
        a = lerp(apex, foot, 0.22 + 0.04 * k)
        pen.line([a, lerp(a, foot, 0.5), foot], w=0.65, hand=0.2, lift=0, occlude=False)
    return (xc, yt + 2)


def plume(x, y, w):
    """Smoke from the crater: billows climbing and drifting to the left, drawn as
    the outline of their union, with a little shade along their undersides."""
    puffs = [(0, -6, 8), (-5, -22, 11), (-15, -40, 14), (-30, -58, 16), (-50, -72, 18), (-76, -80, 19),
             (-104, -84, 17), (-130, -84, 14), (-152, -82, 10),
             (-22, -50, 10), (-44, -62, 12), (-70, -66, 13), (-98, -70, 12), (-124, -72, 10)]
    circles = [(x + dx, y + dy, r) for dx, dy, r in puffs]

    def in_other(p, i, grow=0.0):
        return any(math.dist(p, (cx, cy)) < r + grow for j, (cx, cy, r) in enumerate(circles) if j != i)
    for i, (cx, cy, r) in enumerate(circles):
        ring_pts = ellipse_pts(cx, cy, r, r, 0, 0, 2 * math.pi, step=1.2)
        for run in clip_segments(ring_pts, lambda p: not in_other(p, i)):
            if math.dist(run[0], run[-1]) > 2 or len(run) > 3:
                pen.line(run, w=w, hand=0.15, lift=0, occlude=False)
        # shade: an inner arc along the billow's underside
        arc = ellipse_pts(cx, cy, r * 0.72, r * 0.72, 0, math.radians(25), math.radians(120), step=1.0)
        for run in clip_segments(arc, lambda p: not in_other(p, i, 2.0)):
            if len(run) > 3:
                pen.line(run, w=0.65, hand=0.1, lift=0, occlude=False)


tip = volcano(748.0, 940.0, 852.0, 84.0, 11.0, 1.15)
plume(tip[0], tip[1] - 2, 0.85)
# a low far island on the left
il = [(x, surface_y(x) - 26.0 * math.sin(math.pi * (x - 92.0) / 150.0) ** 0.7) for x in [92.0 + 150.0 * i / 30 for i in range(31)]]
pen.line(il, w=0.95, hand=0.3, lift=0.04, piece=(40, 110), occlude=False)
for k in range(4):
    x = 168.0 + k * 13.0
    yy = surface_y(x) - 26.0 * math.sin(math.pi * (x - 92.0) / 150.0) ** 0.7
    pen.line([(x, yy + 4), (x + 5, surface_y(x) - 3)], w=0.65, hand=0.15, lift=0, occlude=False)

# fine particles suspended in the water
placed = 0
tries = 0
while placed < 85 and tries < 6000:
    tries += 1
    x, y = rng.uniform(X0 + 40, X1 - 40), rng.uniform(SURF_Y + 25, FLOOR_Y - 25)
    if rng.random() > fade(x, y) or y > floor_y(x) - 14 or not clear_of_rings((x, y), 16):
        continue
    pen.dot(x, y, r=rng.uniform(0.9, 1.6), w=1.0)
    placed += 1

pen.save('../02-organic-molecule.svg')
pen.report()
