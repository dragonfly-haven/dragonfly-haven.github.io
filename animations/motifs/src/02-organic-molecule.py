"""02 Organic molecule: six rings swimming in the primordial soup.

Maxim, on the passed drawing (one large benzene ring): "keep the organic
molecule as is but have multiple of them swimming in some 'Ursuppe'."

So the ring is kept exactly as it was drawn (a perfectly regular hexagon with
three alternating Kekule double bonds, each a second, shorter line just inside
the ring; no letters; the line laid down in two close passes; the tidy cast
shadow of ticks along the light from the upper left), and several of them, at
different sizes, turns and depths, swim in a warm, shallow early sea, seen in
section and engraved as in a natural-history plate, lit from the upper left:

- the water: rows of broken, gently waving lines, open under the surface and
  closing up with depth to about 5.6 apart (longer near the floor), so it
  darkens toward the bottom; over the outer fifth at either side the rows grow
  shorter, sparser and ragged, so the mass has a soft, slightly oval outline;
- the surface: a sure line that breaks up into short strokes before the sides,
  a fine broken line under it, a few glints and wavelets;
- the floor in section: the sediment's surface, strata below it (fine level
  dashes, a band of diagonal hatching, a few grains of grit) fading downward and
  to the sides; a vent mound shaded on its lower right, bubbles rising from it
  and from a crack, breaking at the surface; pebbles with shaded undersides
  and short cast shadows; fine particles suspended in the water;
- above: three fine, broken, wavering wisps of steam lifting off the water over
  the crack, and on the far horizon a volcano (form lines on its shadowed
  flank, ridges on the lit one) whose plume rolls off to the left as one cloud,
  small and tight at the vent, broader and flatter downwind and thinning out
  into broken strokes: a sure edge on its shaded underside, a fine broken one
  toward the light, a few fold arcs inside and curved hatching along its
  underside.

Depth: the nearest ring is the passed drawing's ring, frontal and heaviest;
the others are smaller and lighter the farther they are, and turned in the
water (foreshortened about an axis), so they tumble rather than tile. Every
ring has a clean halo: the water's lines stop 7 units short of its lines and
shadow and never cross the gap inside a double bond; the water shows through
the two large rings, and the small ones are kept clean inside.

Not mirrored (slot 02 faces as drawn). Run from this folder:
    python3 02-organic-molecule.py
"""

import math
import random

from pen import Pen, lerp, inside, clip_segments, resample, catmull, ellipse_pts

pen = Pen(seed=202)
rng = pen.rng
rng2 = random.Random(2002)          # for the final polish, so the passed parts keep their draws

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


XC = 500.0                            # the plate's centre line


def half_width(y):
    """Half the width of the water's mass at height y: a soft, slightly oval outline."""
    u = (y - SURF_Y) / (FLOOR_Y - SURF_Y)
    return 412.0 * math.sqrt(max(0.0, 1 - ((u - 0.45) / 1.05) ** 2)) * (1 + 0.03 * math.sin(y * 0.043 + 0.7))


def fade(x, y, edge=0.80):
    """1 well inside the water, falling to 0 over its outer fifth at either side."""
    d = abs(x - XC) / half_width(y)
    return smooth(1.0, edge, d)


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
        # the band between each double bond's two lines
        self.bands = []
        for k, (qa, qb) in zip((0, 2, 4), inners):
            a, b = self.corner(k), self.corner(k + 1)
            self.bands.append([a, b, qb, qa])
        xs = [x for q in self.swept for x, _ in q]
        ys = [y for q in self.swept for _, y in q]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
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
        """Is p within m of one of the ring's lines, in (or within m of) its shadow, or between
        the two lines of a double bond? (The water shows through a ring, but keeps clear of its lines.)"""
        x0, y0, x1, y1 = self.bbox
        if p[0] < x0 - m or p[0] > x1 + m or p[1] < y0 - m or p[1] > y1 + m:
            return False
        if any(inside(p, q) for q in self.swept) or any(inside(p, q) for q in self.bands):
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
        xs = [x for x, _ in self.body]
        ys = [y for _, y in self.body]
        if p[0] < min(xs) - m or p[0] > max(xs) + m or p[1] < min(ys) - m or p[1] > max(ys) + m:
            return False
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


def clear_of_rings(p, m=12.0):
    """For bubbles and particles: outside every ring, with a margin."""
    return not any(r.keeps_out(p, m * (0.4 + 0.6 * r.near)) for r in RINGS)


HALO = 7.0              # the water's lines stop this far short of a ring's lines and shadow


def clear_of_lines(p):
    """For the water's lines: clear of every ring's lines, shadow and double-bond gaps; the water
    shows through the two large rings, the small ones are kept clean inside."""
    for r in RINGS:
        if r.R >= 90:
            if r.near_lines(p, HALO):
                return False
        elif r.keeps_out(p, HALO):
            return False
    return True




# ---------------------------------------------------------------- draw: rings first (front), then the soup

for r in RINGS:
    r.draw()


def wline(pts, w, hand=0.25, lift=0.0):
    pen.line(pts, w=w, hand=hand, lift=lift, piece=(60, 160), occlude=False)


def broken_line(fn, xa, xb, solid, w_solid, w_broken):
    """A line y = fn(x) from xa to xb: solid over the middle, then breaking up into ever
    shorter, sparser strokes before it reaches either side."""
    sa, sb = solid
    pts = [(x, fn(x)) for x in [sa + (sb - sa) * i / int((sb - sa) / 3) for i in range(int((sb - sa) / 3) + 1)]]
    wline(pts, w_solid)
    for direction, x_from, x_to in ((-1, sa, xa), (1, sb, xb)):
        x = x_from + direction * rng.uniform(3, 7)
        while (x - x_to) * direction < 0:
            t = abs(x - x_from) / abs(x_to - x_from)          # 0 at the solid end, 1 at the side
            L = (34 - 26 * t) * rng.uniform(0.7, 1.3)
            xe = x + direction * L
            seg = [(xx, fn(xx)) for xx in [x + (xe - x) * i / 6 for i in range(7)]]
            wline(seg, w_broken - 0.35 * t, 0.15)
            x = xe + direction * (5 + 22 * t) * rng.uniform(0.7, 1.4)


# ---- the surface, a fine broken line under it, and a few glints and wavelets
broken_line(surface_y, XC - 415.0, XC + 412.0, (215.0, 790.0), 1.7, 1.3)
x = XC - 0.72 * half_width(SURF_Y)
while x < XC + 0.72 * half_width(SURF_Y):
    L = rng.uniform(30, 90) * (0.4 + 0.6 * fade(x, SURF_Y, 0.55))
    seg = [(xx, surface_y(xx) + 7.5) for xx in [x + L * i / 10 for i in range(11)]]
    wline(seg, 0.8, 0.15)
    x += L + rng.uniform(25, 70)
for gx, gl in ((268.0, 22.0), (300.0, 12.0), (352.0, 26.0), (395.0, 14.0), (448.0, 20.0), (602.0, 16.0), (640.0, 24.0)):
    gy = surface_y(gx) + rng.uniform(13, 19)
    wline([(gx, gy), (gx + gl * 0.5, gy - 0.4), (gx + gl, gy)], 0.75, 0.1)
for wx, ww in ((180.0, 16.0), (330.0, 20.0), (520.0, 18.0), (585.0, 13.0), (655.0, 15.0)):
    pen.line(ellipse_pts(wx, surface_y(wx) + 2.0, ww, 4.5, 0.0, math.pi * 1.15, math.pi * 1.85, step=1.0),
             w=0.85, hand=0, lift=0, occlude=False)

# ---- the water: rows of broken, gently waving lines, open under the surface and closing with
# depth to about 5.6 apart, longer near the floor; shorter, sparser and ragged over the outer fifth
y = SURF_Y + 20.0
while y < FLOOR_Y + 14:
    u = min(1.0, (y - SURF_Y) / (FLOOR_Y - SURF_Y))
    hw = half_width(y)
    xl = XC - hw + rng2.uniform(-25, 25)              # each row ends a little in or out
    xr = XC + hw + rng2.uniform(-25, 25)
    x = xl + rng.uniform(0, 30)
    ph = rng.uniform(0, 6.3)
    amp = 0.5 + 1.5 * (1 - u)
    while x < xr:
        f = smooth(xl, xl + 0.2 * hw, x) * smooth(xr, xr - 0.2 * hw, x)
        L = (26 + 120 * u ** 1.3) * rng.uniform(0.6, 1.4) * (0.3 + 0.7 * f)
        xe = min(xr, x + L)
        if rng.random() < 0.15 + 0.85 * f ** 0.8:
            seg = [(xx, y + amp * math.sin(xx * 0.06 + ph)) for xx in [x + (xe - x) * i / max(2, int((xe - x) / 6)) for i in range(max(2, int((xe - x) / 6)) + 1)]]
            for run in clip_segments(seg, lambda p: p[1] < floor_y(p[0]) - 6 and clear_of_lines(p)):
                if math.dist(run[0], run[-1]) > 6:
                    wline(run, 0.66 + 0.2 * u, 0.15)
        x = xe + (38 - 26 * u) * rng.uniform(0.5, 1.5) * (1 + 1.8 * (1 - f))
    y += 5.6 + 21.0 * (1 - u) ** 1.7 + rng.uniform(-0.4, 0.4)

# ---- the floor in section: the sediment's surface, strata below fading down and to the sides
broken_line(floor_y, XC - 0.97 * half_width(FLOOR_Y), XC + 0.97 * half_width(FLOOR_Y), (225.0, 780.0), 1.5, 1.2)


def stratum(depth, y):
    return floor_y(y) + depth


# stratum lines
for depth, reach, w in ((17.0, 0.72, 0.95), (38.0, 0.6, 0.85), (60.0, 0.45, 0.75)):
    hw = half_width(FLOOR_Y) * reach
    x = XC - hw + rng.uniform(0, 20)
    while x < XC + hw:
        f = smooth(1.0, 0.7, abs(x - XC) / hw)
        L = rng.uniform(40, 120) * (0.4 + 0.6 * f)
        xe = min(XC + hw, x + L)
        if rng.random() < 0.3 + 0.7 * f:
            seg = [(xx, floor_y(xx) * 0.6 + FLOOR_Y * 0.4 + depth) for xx in [x + (xe - x) * i / 8 for i in range(9)]]
            wline(seg, w, 0.25)
        x = xe + rng.uniform(8, 30) * (1 + 1.5 * (1 - f))
# between the floor and the first stratum: fine sediment, short level dashes
for depth in (6.0, 11.5):
    hw = half_width(FLOOR_Y) * 0.78
    x = XC - hw + rng.uniform(0, 20)
    while x < XC + hw:
        f = smooth(1.0, 0.7, abs(x - XC) / hw)
        L = rng.uniform(8, 22)
        if rng.random() < 0.2 + 0.7 * f:
            seg = [(xx, floor_y(xx) + depth) for xx in [x, x + L / 2, x + L]]
            wline(seg, 0.65, 0.1)
        x += L + rng.uniform(6, 16) * (1 + 2 * (1 - f))
# between the first and second: diagonal hatching
hw = half_width(FLOOR_Y) * 0.62
x = XC - hw
while x < XC + hw:
    f = smooth(1.0, 0.65, abs(x - XC) / hw)
    if rng.random() < 0.15 + 0.85 * f:
        top = floor_y(x) * 0.6 + FLOOR_Y * 0.4 + 17.0 + 2.5
        bot = floor_y(x) * 0.6 + FLOOR_Y * 0.4 + 38.0 - 2.5
        wline([(x, top), (x + (bot - top) * 0.55, bot)], 0.65, 0.1)
    x += 6.5
# between the second and third: a scatter of grit
for k in range(60):
    xx = XC + rng.uniform(-1, 1) * half_width(FLOOR_Y) * 0.5
    yy = floor_y(xx) * 0.6 + FLOOR_Y * 0.4 + rng.uniform(43, 56)
    keep = rng.random() < smooth(1.0, 0.6, abs(xx - XC) / (half_width(FLOOR_Y) * 0.5))
    r0 = rng.uniform(0.8, 1.4)
    if keep and k % 3 == 0:                         # a third of them, as grains rather than specks
        pen.line(ellipse_pts(xx, yy, 2.2 + r0, 1.5 + 0.6 * r0, 0.0), w=0.9, hand=0, lift=0, occlude=False)

# ---- the vent: a mouth on the mound's top, the mound shaded on its lower right
vx, vy = VENT, floor_y(VENT)
pen.line(ellipse_pts(vx, vy + 2.5, 13, 3.5, 0.0, 0.0, math.pi), w=1.2, hand=0, lift=0, occlude=False)
pen.line(ellipse_pts(vx, vy + 2.5, 13, 3.5, 0.0, math.pi, 2 * math.pi), w=1.0, hand=0, lift=0, occlude=False)
for k in range(9):
    x0 = vx + 10 + k * 6.5
    y0 = floor_y(x0) + 2.5
    L = 26 - 2.0 * k
    wline([(x0, y0), (x0 + 0.3 * L, y0 + 0.5 * L), (x0 + 0.5 * L, y0 + L)], 0.7, 0.1)

# ---- pebbles on the floor: each with its shaded underside and a short cast shadow
for x, rx, ry in ((232, 12, 6), (254, 7, 4), (330, 9, 5), (512, 14, 6.5), (612, 8, 4.5),
                  (790, 11, 5.5), (808, 6, 3.5)):
    cy = floor_y(x) - ry + 1.5
    pen.line(ellipse_pts(x, cy, rx, ry, 0.0, math.pi * 1.0, math.pi * 2.0), w=1.1, hand=0, lift=0, occlude=False)
    for j in range(2):
        rr = 0.75 - 0.3 * j
        pen.line(ellipse_pts(x, cy, rx * rr, ry * rr, 0.0, math.radians(-30), math.radians(70)), w=0.7, hand=0, lift=0, occlude=False)
    fy = floor_y(x + rx + 6)
    wline([(x + rx * 0.6, fy + 1.5), (x + rx + 12, fy + 1.5)], 0.75, 0.05)


# ---- bubbles: rising from the vent and from a crack, growing as they rise
def bubble(x, y, r):
    if r < 3.0:
        pen.dot(x, y, r=max(1.0, r * 0.7), w=0.9)
        return
    pen.line(ellipse_pts(x, y, r, r * 0.96, 0, 0, 2 * math.pi + 0.15, step=1.2), w=0.9 + 0.03 * r, hand=0, lift=0, occlude=False)
    pen.line(ellipse_pts(x, y, r * 0.55, r * 0.55, 0, math.radians(195), math.radians(250), step=0.8), w=0.7, hand=0, lift=0, occlude=False)


bubbles = []


def bubble_column(x0, y0, y1, n, r0, r1, sway, ph):
    for k in range(n):
        u = (k + 0.5) / n
        y = y0 + (y1 - y0) * u ** 0.85
        x = x0 + sway * math.sin(u * 6.5 + ph) + rng.uniform(-3, 3)
        r = r0 + (r1 - r0) * u + rng.uniform(-0.5, 0.5)
        if clear_of_rings((x, y), 5 + r):
            bubbles.append((x, y, r))


bubble_column(vx, vy - 16, SURF_Y + 20, 17, 2.4, 9.0, 11.0, 0.4)
bubble_column(vx + 22, vy - 50, SURF_Y + 70, 7, 2.0, 6.0, 8.0, 2.1)
bubble_column(318.0, floor_y(318.0) - 16, SURF_Y + 26, 11, 2.0, 7.5, 10.0, 4.0)
for b in bubbles:
    bubble(*b)

# where bubbles break: a small dome on the surface and ripples running off either side
for bx, sc in ((vx + 4, 1.0), (322.0, 0.85)):
    by = surface_y(bx)
    pen.line(ellipse_pts(bx, by, 7 * sc, 5 * sc, 0, math.pi * 1.05, math.pi * 1.95, step=0.8), w=1.0, hand=0, lift=0, occlude=False)
    for j, d in enumerate((15, 26)):
        for sgn in (-1, 1):
            cx = bx + sgn * d * sc
            pen.line(ellipse_pts(cx, surface_y(cx) - 0.5, 5.5 * sc, 2.6 * sc, 0, math.pi * 1.1, math.pi * 1.9, step=0.8),
                     w=0.85 - 0.1 * j, hand=0, lift=0, occlude=False)


def billows(circles, w_shade, w_lit, hatch=3):
    """Rolling billows of smoke or steam, nearest first, lit from the upper left. Each shows its
    contour where no nearer billow hides it: a sure line on the shaded lower right, a fine broken
    one toward the light; curved parallel hatching follows each billow's lower right."""
    occ0 = len(pen.occluders)
    for cx, cy, r in circles:
        ry = r * 0.88
        a0 = math.radians(-35)
        pen.line(ellipse_pts(cx, cy, r, ry, 0, a0, math.radians(165), step=1.2), w=w_shade, hand=0.1, lift=0.04, piece=(30, 80))
        # toward the light: a few short, fine pieces
        arc = ellipse_pts(cx, cy, r, ry, 0, math.radians(165), math.radians(325), step=1.2)
        k = int(rng.uniform(0, 4))
        while k < len(arc) - 2:
            ln = rng.randint(4, 9)
            pen.line(arc[k:k + ln], w=w_lit, hand=0.05, lift=0, piece=(400, 800))
            k += ln + rng.randint(3, 8)
        for j, (fr, b0, b1) in enumerate(((0.8, -15, 125), (0.62, 5, 105), (0.45, 25, 85))[:hatch]):
            if r * fr < 4:
                break
            pen.line(ellipse_pts(cx, cy, r * fr, ry * fr, 0, math.radians(b0), math.radians(b1), step=1.0),
                     w=0.62, hand=0.05, lift=0, piece=(400, 800))
        pen.occlude(ellipse_pts(cx, cy, r + 1.0, ry + 1.0, 0, step=2.0))
    del pen.occluders[occ0:]


# ---- warm vapour: a few fine wisps wavering up off the water over the crack, each a thin
# open curve of its own, breaking up and fading as it rises
def wisp(x0, y0, h, lean, w):
    f1, f2 = rng2.uniform(0.7, 1.2), rng2.uniform(1.8, 2.6)
    p1, p2 = rng2.uniform(0, 6.3), rng2.uniform(0, 6.3)
    a1 = rng2.uniform(6.0, 9.0)
    pts = []
    for i in range(61):
        u = i / 60
        amp = a1 * (0.3 + 0.9 * u)
        x = x0 - lean * u ** 1.4 + amp * (0.75 * math.sin(u * f1 * 2 * math.pi + p1) + 0.25 * math.sin(u * f2 * 2 * math.pi + p2))
        pts.append((x, y0 - h * u))
    # lay it down in pieces that shorten and part further as it rises
    fine = resample(pts, 1.5)
    s_at = [0.0]
    for k in range(1, len(fine)):
        s_at.append(s_at[-1] + math.dist(fine[k - 1], fine[k]))
    total = s_at[-1]
    k = 0
    while k < len(fine) - 2:
        u = s_at[k] / total
        want = (26 - 18 * u) * rng2.uniform(0.7, 1.3)
        j = k + 1
        while j < len(fine) - 1 and s_at[j] - s_at[k] < want:
            j += 1
        pen.line(fine[k:j + 1], w=w * (1 - 0.3 * u), hand=0.1, lift=0, piece=(400, 800), occlude=False)
        gap = (2 + 9 * u) * rng2.uniform(0.7, 1.4)
        while j < len(fine) - 1 and s_at[j] - s_at[k] < want + gap:
            j += 1
        k = j


for x0, dy, h, lean, w in ((313.0, 5.0, 88.0, 16.0, 0.75), (296.0, 13.0, 60.0, 24.0, 0.65),
                           (339.0, 8.0, 72.0, 2.0, 0.7)):
    wisp(x0, surface_y(x0) - dy, h, lean, w)


# ---- beyond the water: a far volcano on the horizon, its plume rolling off to the left
def volcano(xl, xr, xc, top, crater, w):
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
    pen.line(left + rim + right, w=w, hand=0.25, lift=0.03, piece=(40, 110), occlude=False)
    # the shadowed right flank: form lines of the cone, from under the rim to the foot, closer
    # together toward the dark edge, each stopping a little above the horizon
    apex = (xc + crater * 0.4, yt + 3)
    k = 0
    for t in [0.22 + 0.78 * (1 - (1 - i / 7) ** 1.5) for i in range(8)]:
        foot = right_at(t)
        foot = (foot[0] - 4.0, surface_y(foot[0]) - 3.0 - 6.0 * (1 - t))
        foot = (foot[0], min(foot[1], right_at(t)[1] + (surface_y(foot[0]) - right_at(t)[1]) * 0.98))
        start = 0.34 + 0.16 * ((k * 7) % 3) / 2
        a = lerp(apex, foot, start)
        m = lerp(a, foot, 0.5)
        m = (m[0] - 2.0, m[1] + 2.0)
        pen.line(catmull([a, m, foot], step=3.0), w=0.7, hand=0.15, lift=0, occlude=False)
        k += 1
    # ridges on the lit left flank
    for t0, t1, dx in ((0.93, 0.45, -10.0), (0.85, 0.3, -26.0), (0.9, 0.6, 8.0)):
        a, b = left_at(t0), left_at(t1)
        a = (a[0] + 8 + dx * 0.1, a[1] + 4)
        b = (b[0] + 16 + dx, b[1] + 10)
        pen.line(catmull([a, lerp(a, b, 0.5), b], step=3.0), w=0.7, hand=0.25, lift=0, occlude=False)
    return (xc, yt + 2)


def plume(x, y):
    """The volcano's plume, as one cloud: small and tight at the vent, broader and flatter
    downwind. Its outer edge is a sure line on the shaded underside and a fine broken one toward
    the light, thinning out into broken strokes at the far end; a few fold arcs inside, and a
    row of curved hatching along the shaded underside."""
    # billows as ellipses (dx, dy, rx, ry), from the vent downwind
    E = [(0, -8, 7, 6.5), (-3, -20, 10, 9), (-11, -35, 13, 11), (-24, -51, 17, 13), (-43, -66, 22, 15),
         (-68, -77, 27, 16), (-99, -84, 31, 16), (-134, -87, 32, 14.5), (-168, -87, 29, 12),
         (-199, -85, 23, 9), (-225, -83, 16, 6.5),
         (-56, -84, 15, 10), (-90, -99, 20, 11), (-126, -100, 19, 9.5), (-160, -98, 15, 7.5)]
    E = [(x + dx, y + dy, rx, ry) for dx, dy, rx, ry in E]

    def in_e(p, e, grow=0.0):
        cx, cy, rx, ry = e
        return ((p[0] - cx) / (rx + grow)) ** 2 + ((p[1] - cy) / (ry + grow)) ** 2 < 1.0

    def in_union(p, skip=None, grow=0.0):
        return any(in_e(p, e, grow) for i, e in enumerate(E) if i != skip)

    x_far = x - 150.0                       # beyond this the cloud thins out
    for i, (cx, cy, rx, ry) in enumerate(E):
        pts = ellipse_pts(cx, cy, rx, ry, 0, 0, 2 * math.pi, step=1.2)
        for run in clip_segments(pts, lambda p: not in_union(p, i)):
            # split the run into lit and shaded pieces by the way the edge faces
            cur, cur_lit = [], None
            pieces = []
            for p in run:
                nx_, ny_ = (p[0] - cx) / rx, (p[1] - cy) / ry
                lit = (nx_ * -0.6 + ny_ * -0.8) > 0.15
                if cur and lit != cur_lit:
                    pieces.append((cur, cur_lit))
                    cur = [cur[-1]]
                cur.append(p)
                cur_lit = lit
            if len(cur) > 1:
                pieces.append((cur, cur_lit))
            for seg, lit in pieces:
                far = smooth(x_far, x_far - 90.0, seg[len(seg) // 2][0])     # 0 near, 1 at the far end
                if not lit and far < 0.2:
                    pen.line(seg, w=0.95, hand=0.1, lift=0.03, piece=(30, 90), occlude=False)
                    continue
                # toward the light, and all of the far end: fine broken strokes, sparser far off
                k = int(rng2.uniform(0, 3))
                while k < len(seg) - 2:
                    ln = rng2.randint(4, 9) if lit else rng2.randint(6, 12)
                    pen.line(seg[k:k + ln], w=(0.65 if lit else 0.85 - 0.2 * far), hand=0.05, lift=0, piece=(400, 800), occlude=False)
                    k += ln + rng2.randint(3, 7) + int(10 * far)
    # fold arcs: where a billow rolls in front of the next one downwind, its lower right shows
    for i in (2, 4, 5, 6, 12):
        cx, cy, rx, ry = E[i]
        arc = ellipse_pts(cx, cy, rx, ry, 0, math.radians(-10), math.radians(115), step=1.2)
        for run in clip_segments(arc, lambda p: in_union(p, i, -2.0)):
            if len(run) > 5:
                pen.line(run, w=0.75, hand=0.05, lift=0, piece=(400, 800), occlude=False)
    # curved hatching along the shaded underside, just inside the edge
    for i, (cx, cy, rx, ry) in enumerate(E[:9]):
        for fr in (0.8, 0.62):
            if ry * (1 - fr) < 2.5 or rx * fr < 5:
                continue
            arc = ellipse_pts(cx, cy, rx * fr, ry * fr, 0, math.radians(15), math.radians(130), step=1.0)
            for run in clip_segments(arc, lambda p: not in_union(p, i) or not in_union(p, i, -1.0)):
                pass
            # only where this billow's own underside is the cloud's underside
            keep = [p for p in arc if not any(in_e((p[0], p[1] + ry * (1 - fr) + 2), e) for j, e in enumerate(E) if j != i)]
            if len(keep) > 6:
                runs, cur = [], [keep[0]]
                for a, b in zip(keep, keep[1:]):
                    if math.dist(a, b) > 2.0:
                        runs.append(cur)
                        cur = [b]
                    else:
                        cur.append(b)
                runs.append(cur)
                for run in runs:
                    if len(run) > 5:
                        pen.line(run, w=0.62, hand=0.05, lift=0, piece=(400, 800), occlude=False)


tip = volcano(742.0, 910.0, 834.0, 82.0, 10.0, 1.2)
plume(tip[0], tip[1] - 2)

# ---- fine particles suspended in the water
placed = 0
tries = 0
while placed < 90 and tries < 6000:
    tries += 1
    x, y = rng.uniform(XC - 430, XC + 430), rng.uniform(SURF_Y + 25, FLOOR_Y - 25)
    if rng.random() > fade(x, y) or y > floor_y(x) - 14 or not clear_of_rings((x, y), 16):
        continue
    if any(math.dist((x, y), (bx, by)) < br + 5 for bx, by, br in bubbles):
        continue
    pen.dot(x, y, r=rng.uniform(0.9, 1.6), w=1.0)
    placed += 1

pen.save('../02-organic-molecule.svg')
pen.report()
