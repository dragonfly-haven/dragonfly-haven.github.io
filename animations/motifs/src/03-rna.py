"""03 RNA: a single strand folded into a hairpin, drawn as a precise textbook engraving.

One sugar-phosphate backbone as a flat ribbon of constant width, its bases as
narrow bars of one length, evenly spaced along it on one side. The strand
comes down from its 5' end, turns up into a stem of six base pairs (each pair
two bars meeting at the middle, as in 04 DNA, its pair), rounds a loop of
seven unpaired bases (tilted away from us, so it is foreshortened and its far
side drawn lighter) and comes down the other side of the stem into its 3'
tail. The arm and the tail each make one long, even turn, the same way, so
their bases fan out. Tidy parallel hatching only along the edge of the ribbon
away from the light (upper left). Sure, low-wobble lines without lifts,
square-cut ends.
"""

import math

from pen import Pen, bezier, dist, lerp, length, resample

pen = Pen(seed=303)

# ---------------------------------------------------------------- the sure line


def ink(pts, w, hand=0.2, seg=26.0):
    """A sure line: a faint slow wobble, no lifts; w is a weight or a function of the point."""
    total = length(pts)
    if total < 1.0:
        return
    fine = resample(pts, 1.5)
    n = len(fine) - 1
    if hand > 0 and n > 1:
        ph, fq = pen.r(0, 6.3), pen.r(0.005, 0.01)
        moved = []
        s = 0.0
        for k, p in enumerate(fine):
            if k:
                s += dist(fine[k - 1], p)
            a, b = fine[max(0, k - 1)], fine[min(n, k + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            off = hand * math.sin(s * fq * 2 * math.pi + ph) * min(1.0, s / 10, (total - s) / 10)
            moved.append((p[0] + dy / L * off, p[1] - dx / L * off))
        fine = moved
    m = max(1, int(round(total / seg)))
    for q in range(m):
        k0, k1 = n * q // m, n * (q + 1) // m
        piece = fine[k0:k1 + 1]
        if len(piece) >= 2:
            pen.raw(piece, w(piece[len(piece) // 2]) if callable(w) else w)


# ---------------------------------------------------------------- the fold, in the stem's frame

ANG = math.radians(-62)                     # the stem rises up to the right
D = (math.cos(ANG), math.sin(ANG))          # up the stem
P = (-D[1], D[0])                           # across it, from strand 1 to strand 2
B0 = (500.0, 600.0)                         # the stem's foot, between the strands
HW = 15.0                                   # half width of the ribbon (as 04 DNA)
S = 170.0                                   # strand to strand across the stem
SP = 56.0                                   # base to base along the strand
NBP = 6                                     # base pairs in the stem
GAP = 4.0                                   # half the gap where two paired bases meet
LB = (S - 2 * HW) / 2 - GAP                 # every base is a rod of this length
E0, E1 = 28.0, 30.0                         # the stem's strands run on past its end pairs
RC = 56.0                                   # radius of the turns at the stem's foot
RL = 118.0                                  # radius of the loop
U_TOP = (NBP - 1) * SP + E1
H0 = 48.0                                   # the strand leaves the straight stem this far below its top
NK = 40.0                                   # handle length of the neck curves
LIGHT = (-0.6, -0.8)                        # light from the upper left
BASE = 'bar'                                # a base as a rod (one heavy line) or an outlined bar
BW = 5.0                                    # half width of an outlined bar


def fp(p, d):
    """A point given in the stem's frame (across, up)."""
    return (B0[0] + P[0] * p + D[0] * d, B0[1] + P[1] * p + D[1] * d)


def to_frame(x):
    v = (x[0] - B0[0], x[1] - B0[1])
    return (v[0] * P[0] + v[1] * P[1], v[0] * D[0] + v[1] * D[1])


# the loop tilts back: beyond the top of the stem its height is foreshortened
T0, TK, TL = U_TOP + 6.0, 0.6, 40.0


def warp(x):
    p, d = to_frame(x)
    if d > T0:
        e = d - T0
        # the scale eases from 1 to TK over TL
        if e < TL:
            d = T0 + e - (1 - TK) * e * e / (2 * TL)
        else:
            d = T0 + TL - (1 - TK) * TL / 2 + TK * (e - TL)
    return fp(p, d)


def arc(cp, cd, r, a0, a1, n=24):
    return [fp(cp + r * math.cos(a0 + (a1 - a0) * k / n), cd + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def line_pts(p0, d0, p1, d1, n=12):
    return [fp(p0 + (p1 - p0) * k / n, d0 + (d1 - d0) * k / n) for k in range(n + 1)]


# 5' arm: comes down from the upper left and swings in along the foot
arm5 = bezier(fp(-420, 60), fp(-380, -50), fp(-S / 2 - RC - 90, -E0 - RC), fp(-S / 2 - RC, -E0 - RC), step=2)
foot1 = arc(-S / 2 - RC, -E0, RC, -math.pi / 2, 0)                    # turns up into strand 1
stem1 = line_pts(-S / 2, -E0, -S / 2, U_TOP - H0)
# the loop: the strand flares from the stem into a round loop and back
LC = U_TOP + 70.0
BETA = math.radians(28)
SB, CB = math.sin(BETA), math.cos(BETA)
loop = bezier(fp(-S / 2, U_TOP - H0), fp(-S / 2, U_TOP - H0 + NK), fp(-RL * CB + NK * SB, LC - RL * SB - NK * CB),
               fp(-RL * CB, LC - RL * SB), step=2)[1:]
loop += arc(0, LC, RL, math.pi + BETA, -BETA, n=60)[1:]
loop += bezier(fp(RL * CB, LC - RL * SB), fp(RL * CB - NK * SB, LC - RL * SB - NK * CB),
               fp(S / 2, U_TOP - H0 + NK), fp(S / 2, U_TOP - H0), step=2)[1:]
stem2 = line_pts(S / 2, U_TOP - H0, S / 2, -E0)


def turn(start, h0, dh, r, n=30):
    """An arc from `start`, setting off at screen heading h0 (degrees, y down) and turning
    by dh degrees (negative: round to the left)."""
    h = math.radians(h0)
    sg = 1 if dh > 0 else -1
    c = (start[0] - math.sin(h) * r * sg, start[1] + math.cos(h) * r * sg)
    a0 = math.atan2(start[1] - c[1], start[0] - c[0])
    return [(c[0] + r * math.cos(a0 + math.radians(dh) * k / n), c[1] + r * math.sin(a0 + math.radians(dh) * k / n)) for k in range(n + 1)]


H_DOWN = math.degrees(math.atan2(-D[1], -D[0]))   # heading down the stem
# 3' tail: one long, even turn the same way as the 5' arm's, so its bases fan out below
TR3, TT3 = 190.0, 95.0
foot2 = []
tail3 = turn(fp(S / 2, -E0), H_DOWN, -TT3, TR3)

path = []
for part in (arm5, foot1, stem1, loop, stem2, foot2, tail3):
    for q in part:
        if not path or dist(path[-1], q) > 0.5:
            path.append(q)
line = resample(path, 1.5)
sl = [0.0]
for i in range(1, len(line)):
    sl.append(sl[-1] + dist(line[i - 1], line[i]))
TOTAL = sl[-1]


def at(s):
    """Point and unit tangent at arc length s (before the tilt)."""
    s = max(0.0, min(TOTAL, s))
    i = min(len(line) - 2, max(0, int(s / 1.5)))
    while i < len(line) - 2 and sl[i + 1] < s:
        i += 1
    while i > 0 and sl[i] > s:
        i -= 1
    t = (s - sl[i]) / ((sl[i + 1] - sl[i]) or 1)
    p = lerp(line[i], line[i + 1], t)
    a, b = line[max(0, i - 2)], line[min(len(line) - 1, i + 3)]
    L = dist(a, b) or 1
    return p, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def nearest_s(x):
    return min((dist(x, q), sl[i]) for i, q in enumerate(line))[1]


def depth_w(x, near, far):
    """Weight that lightens toward the far side of the tilted loop."""
    p, d = to_frame(x)
    t = max(0.0, min(1.0, (d - (LC - 20)) / (RL + 20)))
    return near + (far - near) * t


# ---------------------------------------------------------------- the ribbon

samples = []
s = 0.0
while s <= TOTAL + 0.01:
    p, t = at(s)
    nl = (t[1], -t[0])                      # left of travel
    samples.append(dict(s=s, c=warp(p), e1=warp((p[0] + nl[0] * HW, p[1] + nl[1] * HW)),
                        e2=warp((p[0] - nl[0] * HW, p[1] - nl[1] * HW))))
    s += 1.5

EDGE = lambda x: depth_w(x, 2.6, 1.8)
for key in ('e1', 'e2'):
    ink([x[key] for x in samples], EDGE)
for smp in (samples[0], samples[-1]):
    ink([smp['e1'], smp['e2']], EDGE, hand=0.1)

# hatching along the edge away from the light: short, even, parallel strokes across the band,
# longer where that edge turns further from the light, none where the band runs into the light
HSP = 6.0
last = None
for i in range(1, len(samples) - 1):
    smp = samples[i]
    a, b = smp['e1'], smp['e2']
    m = smp['c']
    da = (a[0] - m[0]) * LIGHT[0] + (a[1] - m[1]) * LIGHT[1]
    db = (b[0] - m[0]) * LIGHT[0] + (b[1] - m[1]) * LIGHT[1]
    if da > db:
        a, b = b, a                         # a: the edge away from the light
    away = abs(da - db) / (2 * HW)
    if away < 0.3 or dist(a, b) < 6:
        last = None
        continue
    f = 0.22 + 0.3 * min(1.0, (away - 0.3) / 0.6)
    q0, q1 = lerp(a, b, 0.06), lerp(a, b, f)
    # the next stroke comes once both its ends are a full space on from the last one's
    if last is not None and min(dist(q0, last[0]), dist(q1, last[1])) < HSP:
        continue
    last = (q0, q1)
    ink([q0, q1], lambda x: depth_w(x, 1.0, 0.8), hand=0.05)

# ---------------------------------------------------------------- the bases


def rod(s, length_, side=1, inward=None):
    """A base: a rod from the ribbon's edge (right of travel), square across the strand,
    or toward the point `inward` (before the tilt)."""
    p, t = at(s)
    if inward is None:
        d = (-t[1] * side, t[0] * side)
    else:
        L = dist(p, inward) or 1
        d = ((inward[0] - p[0]) / L, (inward[1] - p[1]) / L)
    a = (p[0] + d[0] * HW, p[1] + d[1] * HW)
    b = (p[0] + d[0] * (HW + length_), p[1] + d[1] * (HW + length_))
    if BASE == 'rod':
        pts = [warp(lerp(a, b, k / 8)) for k in range(9)]
        ink(pts, lambda x: depth_w(x, 2.6, 1.9), hand=0.1)
        return
    n = (-d[1], d[0])
    sides = []
    for sg in (1, -1):
        a2 = (a[0] + n[0] * BW * sg, a[1] + n[1] * BW * sg)
        b2 = (b[0] + n[0] * BW * sg, b[1] + n[1] * BW * sg)
        sides.append([warp(lerp(a2, b2, k / 8)) for k in range(9)])
    w = lambda x: depth_w(x, 1.9, 1.4)
    ink(sides[0], w, hand=0.1)
    ink(sides[1], w, hand=0.1)
    ink([sides[0][-1], sides[1][-1]], w, hand=0.0)


# the stem's pairs
s_pair1 = [nearest_s(fp(-S / 2, k * SP)) for k in range(NBP)]
s_pair2 = [nearest_s(fp(S / 2, k * SP)) for k in range(NBP)]
for s1, s2 in zip(s_pair1, s_pair2):
    rod(s1, LB)
    rod(s2, LB)
# the loop's unpaired bases, evenly spaced from the last pair round to the first on the way down
s_a, s_b = s_pair1[-1], s_pair2[-1]
n_loop = 7                                  # a loop of seven unpaired bases
centre = fp(0, LC)
for k in range(n_loop):
    rod(s_a + (s_b - s_a) * (k + 1) / (n_loop + 1), LB, inward=centre)
# the 5' arm and the 3' tail
# (none on the turns at the foot of the stem, where they would cross under it)
s_turn1 = nearest_s(fp(-S / 2 - RC, -E0 - RC))
s_turn2 = nearest_s(tail3[len(tail3) // 4])
for k in range(1, 12):
    s = s_pair1[0] - SP * k
    if 30 < s < s_turn1 - 6:
        rod(s, LB)
for k in range(1, 12):
    s = s_pair2[0] + SP * k
    if s_turn2 + 6 < s < TOTAL - 30:
        rod(s, LB)

# centre the drawing in the square
xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
print('extent', round(max(xs) - min(xs)), round(max(ys) - min(ys)), 'loop bases', n_loop)
SCALE = 1.05
pen.strokes = [([((x - cx) * SCALE + 500, (y - cy) * SCALE + 500) for x, y in p], w) for p, w in pen.strokes]
pen.save('../03-rna.svg', mirror=False)
pen.report()
