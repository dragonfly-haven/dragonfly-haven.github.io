"""02 Organic molecule: the six ring, benzene in Kekule's form.

Maxim: "Organic Molecule - more chemistry like", then "Just use the six ring
motif." So the drawing is the iconic hexagon of organic chemistry, drawn as a
chemist draws it: a large, perfectly regular hexagon (a carbon at each corner;
carbons and their hydrogens unlettered, as in any skeletal formula) with three
alternating double bonds, each a second, shorter line just inside the ring,
parallel to its bond. No substituents: a bare line end in a skeletal formula
would mean a methyl group, so the C-H bonds stay implied.

Hand: sleek and technical (brief-rework.md): straight, sure lines, no lifts,
an even weight. The ring is one closed line laid down in two close parallel
passes, which makes a fuller line than a single stroke can be in the site's
dash engine; the inner lines are laid down the same way, so all bonds match,
as the convention requires.

Alone, the ring looked thin and empty beside the galaxy (01) and the RNA (03),
so it gets one restrained enrichment: the figure stands just off the paper,
lit from the upper left, and casts a tidy drawn shadow down and to the right:
fine ticks, all parallel to the light and all the same length, filling the
area each line sweeps as it is moved along the light from SH_FROM to SH_LEN.
The sliver of paper left between a line and its shadow is widest where the
light falls square across the line and narrower where it grazes it, as under
a real lifted figure; it keeps the ticks from reading as the hatching of a
fixed surface.

Not mirrored (slot 02 faces as drawn). Run from this folder:
    python3 02-organic-molecule.py
"""

import math

from pen import Pen, lerp, inside, clip_segments, resample

pen = Pen(seed=202)

R = 405.0                   # corner radius = bond length: the ring is 701 across, 810 tall
C = (494.0, 490.0)          # ring centre, a little up and left so ring and shadow sit centred

W_RING, ROWS, ROW_GAP = 2.7, 2, 1.2       # the ring: weight, passes, their spacing
INNER_OFF = 0.16            # inner line: distance into the ring, as a share of R
INNER_CUT = 0.13            # inner line: left off each end, as a share of R
DOUBLE = (0, 2, 4)          # double bonds, corner k to k+1 (corner 0 at the top, clockwise)

LIGHT = 60.0                # the shadow falls this way (degrees, y down): light from the upper left
SH_LEN = 29.0               # how far the shadow is thrown, along the light
SH_GAP = 6.0                # shadow ticks: spacing across the light
SH_W = 0.75                 # shadow ticks: weight
SH_FROM = 10.0              # ... and from how far: the sliver of paper between line and shadow


def corner(k, r=R):
    a = math.radians(-90 + 60 * k)
    return (C[0] + r * math.cos(a), C[1] + r * math.sin(a))


def stroke(pts, w):
    """One sure pass: no lifts, an even weight."""
    pen.raw(resample(pts, 3.0), w * pen.r(0.98, 1.02))


def inner_line(k):
    """The second line of the double bond from corner k to k+1."""
    a, b = corner(k), corner(k + 1)
    m = lerp(a, b, 0.5)
    ux, uy = C[0] - m[0], C[1] - m[1]
    ul = math.hypot(ux, uy)
    o = INNER_OFF * R
    qa = (a[0] + ux / ul * o, a[1] + uy / ul * o)
    qb = (b[0] + ux / ul * o, b[1] + uy / ul * o)
    return lerp(qa, qb, INNER_CUT), lerp(qa, qb, 1 - INNER_CUT)


# ---- the ring: one closed line per pass, each pass a true hexagon (corners mitred)
for j in range(ROWS):
    d = (j - (ROWS - 1) / 2) * ROW_GAP
    r = R + d / math.cos(math.radians(30))
    stroke([corner(k % 6, r) for k in range(7)], W_RING)

# ---- the three inner lines
inners = [inner_line(k) for k in DOUBLE]
for a, b in inners:
    m = lerp(a, b, 0.5)
    ul = math.dist(m, C)
    ux, uy = (C[0] - m[0]) / ul, (C[1] - m[1]) / ul
    for j in range(ROWS):
        d = (j - (ROWS - 1) / 2) * ROW_GAP
        stroke([(a[0] + ux * d, a[1] + uy * d), (b[0] + ux * d, b[1] + uy * d)], W_RING)

# ---- the cast shadow
ux, uy = math.cos(math.radians(LIGHT)), math.sin(math.radians(LIGHT))
nx, ny = -uy, ux                                   # across the light
srcs = [(corner(k), corner(k + 1)) for k in range(6)] + inners


def moved(p, d):
    return (p[0] + ux * d, p[1] + uy * d)


swept = [[moved(a, SH_FROM), moved(b, SH_FROM), moved(b, SH_LEN), moved(a, SH_LEN)] for a, b in srcs]


def near_line(p, d):
    for a, b in srcs:
        abx, aby = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / (abx * abx + aby * aby)))
        if math.hypot(p[0] - a[0] - abx * t, p[1] - a[1] - aby * t) < d:
            return True
    return False


def in_shadow(p):
    return any(inside(p, q) for q in swept) and not near_line(p, 4.0)


ts = [x * nx + y * ny for a, b in srcs for x, y in (a, b)]
c0 = C[0] * nx + C[1] * ny
t = min(ts) - SH_LEN + SH_GAP * 0.5
while t < max(ts) + SH_LEN:
    base = (C[0] + nx * (t - c0), C[1] + ny * (t - c0))
    p0 = (base[0] - ux * 600, base[1] - uy * 600)
    p1 = (base[0] + ux * 600, base[1] + uy * 600)
    for run in clip_segments([p0, p1], in_shadow):
        if math.dist(run[0], run[-1]) > 2.5:
            stroke([run[0], run[-1]], SH_W)
    t += SH_GAP

pen.save('../02-organic-molecule.svg')
pen.report()
