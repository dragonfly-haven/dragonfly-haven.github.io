"""03 RNA: a single strand folded into a hairpin.

One sugar-phosphate backbone drawn as a flat ribbon, the bases as short pegs
standing off its inner side. The strand comes down from a single-stranded 5'
arm, turns up one side of a short paired stem (the pegs meet across it, a
long purine with a short pyrimidine), round a loop of unpaired bases that
tilts away from us, and back down, leaving as a 3' tail. The ribbon is
modelled as in 04 DNA: hatching along its shadowed edge, and across the band
where it twists and shows its back.
"""

import math

from pen import Pen, catmull, resample, dist, lerp

pen = Pen(seed=303)

HW = 16.0          # half width of the ribbon (as in 04)
PEG_HW = 7.0       # half thickness of a base peg (as in 04)
SP = 60.0          # base spacing along the strand
S = 186.0          # stem: strand centre to strand centre
GAP = 3.0          # gap where two paired pegs meet

ANG = math.radians(-62)
D = (math.cos(ANG), math.sin(ANG))      # stem axis, base to loop
P = (-D[1], D[0])                       # across the stem, strand 1 to strand 2
B0 = (500.0, 600.0)                     # stem base, on its axis (the drawing is centred afterwards)
NBP = 6
LS = (NBP - 1) * SP                     # first to last pair
E0, E1 = 30.0, 30.0                     # straight strand below the first / above the last pair
RL = 138.0                              # loop radius (ribbon centre), before the tilt
TILT_Y0 = LS + 12.0                     # the loop tilts away from here up
TILT_K = 0.58                           # how much the tilted loop is foreshortened along the stem
TILT_L = 45.0                           # how gradually the tilt sets in
LIGHT = (-0.6, -0.8)                    # light from the upper left


def fr(x, y):
    """A point given across (x, along P) and along (y, along D) the stem, from its base."""
    return (B0[0] + x * P[0] + y * D[0], B0[1] + x * P[1] + y * D[1])


def pt(side, u):
    """Point on the stem: side -1 strand 1, +1 strand 2; u along the axis from the first pair."""
    return fr(side * S / 2, u)


def warp(p):
    """The loop tilts away from us: beyond the stem, distances along the axis shrink."""
    x = (p[0] - B0[0]) * P[0] + (p[1] - B0[1]) * P[1]
    y = (p[0] - B0[0]) * D[0] + (p[1] - B0[1]) * D[1]
    if y > TILT_Y0:
        e = y - TILT_Y0
        y = TILT_Y0 + TILT_K * e + (1 - TILT_K) * TILT_L * (1 - math.exp(-e / TILT_L))
    return fr(x, y)


def warp_line(a, b, n=6):
    return [warp(lerp(a, b, k / n)) for k in range(n + 1)]


# ---------------------------------------------------------------- the strand's path (before the tilt)

dc = math.sqrt(max(0.0, RL ** 2 - (S / 2) ** 2))
LCY = LS + E1 + dc * 0.8


def loop_pts():
    out = []
    n = 8
    for k in range(n + 1):
        a = math.pi - math.pi * k / n          # from -P over +D to +P
        out.append(fr(RL * math.cos(a), LCY + RL * math.sin(a)))
    return out


def stem_line(side, u0, u1, n=6):
    return [pt(side, u0 + (u1 - u0) * k / n) for k in range(n + 1)]


# the 5' arm comes down from the upper left and turns up into the stem; the 3' tail turns out
# the other way below the stem and falls away to the lower right. Either side of the stem the
# strand runs across its foot, so the first unpaired bases hang clear, not facing each other


def scr(dx, dy):
    """A point given as an offset in the picture from the stem base."""
    return (B0[0] + dx, B0[1] + dy)


def corner(start, side, a, b):
    """The turn at the foot of the stem, as points on a quarter ellipse reaching `a` below the
    strand's end (along -D) and `b` out to its side (along P): side -1 runs in along +P and
    turns up into strand 1 at `start`; side +1 leaves strand 2 at `start` and turns out along +P.
    Unequal reaches give a loose, uneven bend rather than an elbow."""
    out = []
    for k in range(9):
        f = math.radians(90 * k / 8)
        if side < 0:
            c = (start[0] - P[0] * b, start[1] - P[1] * b)
            out.append((c[0] - D[0] * a * math.cos(f) + P[0] * b * math.sin(f), c[1] - D[1] * a * math.cos(f) + P[1] * b * math.sin(f)))
        else:
            c = (start[0] + P[0] * b, start[1] + P[1] * b)
            out.append((c[0] - P[0] * b * math.cos(f) - D[0] * a * math.sin(f), c[1] - P[1] * b * math.cos(f) - D[1] * a * math.sin(f)))
    return out


foot1 = corner(pt(-1, -E0), -1, 50.0, 44.0)
foot2 = corner(pt(+1, -E0), +1, 54.0, 46.0)
arm5 = [scr(-392, -425), scr(-362, -295), scr(-312, -168), scr(-240, -78), (foot1[0][0] - P[0] * 45, foot1[0][1] - P[1] * 45)] + foot1[:-1]
tail3 = foot2[1:] + [(foot2[-1][0] + P[0] * 34, foot2[-1][1] + P[1] * 34), scr(192, 176), scr(262, 226), scr(302, 315), scr(308, 418)]

ctrl = arm5 + stem_line(-1, -E0, LS + E1) + loop_pts() + stem_line(+1, LS + E1, -E0) + tail3
line = resample(catmull(ctrl, step=2.0), 2.0)

sl = [0.0]
for i in range(1, len(line)):
    sl.append(sl[-1] + dist(line[i - 1], line[i]))
TOTAL = sl[-1]


def at(s):
    """Point and unit tangent at arc length s (before the tilt)."""
    s = max(0.0, min(TOTAL, s))
    lo, hi = 0, len(sl) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if sl[m] <= s:
            lo = m
        else:
            hi = m
    t = (s - sl[lo]) / ((sl[hi] - sl[lo]) or 1)
    p = lerp(line[lo], line[hi], t)
    i0, i1 = max(0, lo - 3), min(len(line) - 1, hi + 3)
    dx, dy = line[i1][0] - line[i0][0], line[i1][1] - line[i0][1]
    L = math.hypot(dx, dy) or 1
    return p, (dx / L, dy / L)


def nearest_s(p):
    return min((dist(p, q), sl[i]) for i, q in enumerate(line))[1]


s_bot1 = nearest_s(pt(-1, -E0))
s_bot2 = nearest_s(pt(+1, -E0))


def ease(u):
    u = max(0.0, min(1.0, u))
    return 0.5 - 0.5 * math.cos(math.pi * u)


def twist(s):
    """How far the ribbon is turned from facing us (0 faces us, pi shows its back)."""
    tw = 0.0
    # a full turn down the 5' arm
    a, b = 70.0, 330.0
    tw += 2 * math.pi * ease((s - a) / (b - a))
    # a half turn in the 3' tail, ending on the ribbon's back
    a = s_bot2 + 150.0
    tw += math.pi * 0.85 * ease((s - a) / (TOTAL - 12 - a))
    return tw


# ---------------------------------------------------------------- ribbon samples (tilted)

samples = []
s = 0.0
while s <= TOTAL + 0.01:
    p, t = at(s)
    nl = (t[1], -t[0])          # left of travel
    c = math.cos(twist(s))
    e1 = (p[0] + nl[0] * HW * c, p[1] + nl[1] * HW * c)
    e2 = (p[0] - nl[0] * HW * c, p[1] - nl[1] * HW * c)
    samples.append(dict(s=s, p=warp(p), cos=c, e1=warp(e1), e2=warp(e2)))
    s += 1.6

# ---------------------------------------------------------------- the ribbon

for key in ('e1', 'e2'):
    pen.line([x[key] for x in samples], w=2.4, hand=1.1, piece=(26, 80), occlude=False)
for smp in (samples[0], samples[-1]):
    a, b = smp['e1'], smp['e2']
    L = dist(a, b) or 1
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    pen.line([(a[0] - u[0] * 2, a[1] - u[1] * 2), (b[0] + u[0] * 2.5, b[1] + u[1] * 2.5)], w=2.0, hand=0.3, occlude=False)


def shade_stroke(i):
    """The hatch stroke across the band at sample i: from the shadowed edge, part way or right across."""
    smp = samples[i]
    a, b = smp['e1'], smp['e2']
    c = smp['cos']
    # which edge lies away from the light
    mid = smp['p']
    da = (a[0] - mid[0]) * LIGHT[0] + (a[1] - mid[1]) * LIGHT[1]
    db = (b[0] - mid[0]) * LIGHT[0] + (b[1] - mid[1]) * LIGHT[1]
    if da > db:
        a, b = b, a
    away = abs(da - db) / (2 * HW) if HW else 0
    if c < 0:
        f = 0.9                                   # the ribbon's back: right across
    else:
        f = 0.5 + 0.25 * away + 0.45 * (1 - c)    # its face: a band along the shadowed edge, wider as it turns
    return a, b, min(0.92, f), away, c


def wander(s):
    """A slow, uneven swell along the strand, 0..1, so the hatching is not a rail track."""
    return 0.5 + 0.3 * math.sin(s / 41.0 + 1.3) + 0.2 * math.sin(s / 14.0 + 0.4)


last = None
acc = 0.0
for i in range(1, len(samples) - 1):
    acc += dist(samples[i - 1]['p'], samples[i]['p'])
    a, b, f, away, c = shade_stroke(i)
    s = samples[i]['s']
    arm = s < s_bot1 - 40                         # the 5' arm, above its turn into the stem
    if c > 0.5:
        # on the ribbon's face: opener where it is lit, and opener still along the 5' arm
        sp = 6.0 + (4.5 if arm else 1.2) * (1 - away) ** 2 + (0.8 if arm else 0.0)
    else:
        sp = 6.0
    if acc < sp:
        continue
    if dist(a, b) < 5:
        continue
    if c >= 0 and away < 0.12:
        continue                                  # where the ribbon runs along the light, it is lit on both edges
    if arm and c >= 0.5 and pen.rng.random() < 0.5 * max(0.0, (0.45 - away) / 0.45):
        acc = 0.0
        continue                                  # and on the lit stretches of the arm it is left open here and there
    acc = 0.0
    t0 = pen.r(0.02, 0.1)
    if c >= 0.5:
        t1 = f * (0.75 + 0.42 * wander(s)) * pen.r(0.84, 1.04)
        if arm:
            t1 *= 0.6 + 0.4 * min(1.0, away / 0.6)
    else:
        t1 = f * pen.r(0.85, 1.0)
    t1 = min(0.95, t1)
    q0, q1 = lerp(a, b, t0), lerp(a, b, t1)
    if last is not None and min(dist(q0, last[0]), dist(q1, last[1])) < 5.4:
        continue
    last = (q0, q1)
    if dist(q0, q1) > 3:
        pen.line([q0, q1], w=pen.r(0.88, 1.1), hand=0.35, lift=0.04, piece=(40, 120), occlude=False)

# the pegs go under the ribbon
for i in range(0, len(samples) - 4, 4):
    q = samples[i:i + 5]
    pen.occlude([x['e1'] for x in q] + [x['e2'] for x in q[::-1]])

# ---------------------------------------------------------------- bases

pegs = []   # (root on the centre line, direction, length, half width of the ribbon there), before the tilt
pair_len = S - 2 * HW - GAP
purine = [1, 0, 0, 1, 0, 1]
for k in range(NBP):
    f = 0.58 if purine[k] else 0.42
    pegs.append((pt(-1, k * SP), P, pair_len * f, HW))
    pegs.append((pt(+1, k * SP), (-P[0], -P[1]), pair_len * (1 - f), HW))


def unpaired(s, L):
    p, t = at(s)
    pegs.append((p, (-t[1], t[0]), L, HW * abs(math.cos(twist(s)))))


s_a, s_b = nearest_s(pt(-1, LS)), nearest_s(pt(+1, LS))
loop_lens = [62, 46, 64, 62, 46, 64, 46, 62, 48]
for k in range(len(loop_lens)):
    unpaired(s_a + (s_b - s_a) * (k + 1) / (len(loop_lens) + 1), loop_lens[k])
arm_lens = [64, 48, 64, 64, 48, 64, 48, 64, 48, 64, 64, 48]
for k, L in enumerate(arm_lens):
    s = nearest_s(pt(-1, 0)) - SP * (k + 1)
    if s > 26:
        unpaired(s, L)
for k, L in enumerate([48, 64, 48, 64, 64, 48]):
    s = nearest_s(pt(+1, 0)) + SP * (k + 1)
    if s < TOTAL - 26:
        unpaired(s, L)


def over(a, b, da, db):
    """A segment run on past its ends by da and db."""
    L = dist(a, b) or 1
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    return [(a[0] - ux * da, a[1] - uy * da), (b[0] + ux * db, b[1] + uy * db)]


def peg(root, d, L, hwr):
    """A base: a short flat stick from under the ribbon's edge, its free end square, shaded."""
    n = (-d[1], d[0])
    a = (root[0] + d[0] * (hwr - 3), root[1] + d[1] * (hwr - 3))
    b = (root[0] + d[0] * (hwr + L), root[1] + d[1] * (hwr + L))
    sides = []
    for sg in (1, -1):
        p0 = (a[0] + sg * n[0] * PEG_HW, a[1] + sg * n[1] * PEG_HW)
        p1 = (b[0] + sg * n[0] * PEG_HW, b[1] + sg * n[1] * PEG_HW)
        sides.append(warp_line(p0, p1))
    lit = n[0] * LIGHT[0] + n[1] * LIGHT[1] > 0      # the +n side faces the light
    w_lit, w_dark = 1.6, 2.0
    # a hand overshoots the corners a little
    e0 = over(sides[0][-2], sides[0][-1], 0, pen.r(0.5, 2.5))[1]
    e1 = over(sides[1][-2], sides[1][-1], 0, pen.r(0.5, 2.5))[1]
    pen.line(sides[0][:-1] + [e0], w=w_lit if lit else w_dark, hand=0.6)
    pen.line(sides[1][:-1] + [e1], w=w_dark if lit else w_lit, hand=0.6)
    pen.line(over(sides[0][-1], sides[1][-1], pen.r(0.3, 1.6), pen.r(0.3, 1.6)), w=1.7, hand=0.2, lift=0)
    # shaded with short slanted strokes across it, as on the atoms of 02
    A0, A1 = warp(a), warp(b)
    Lw = dist(A0, A1)
    off = (hwr + 3.5) / max(1.0, hwr + L + 3) * Lw     # start clear of the ribbon's edge
    slant = 0.45 * 2 * PEG_HW * Lw / (L + 3)
    t = off + pen.r(0, 1.0)
    while t + slant < Lw - 3:
        u0, u1 = t / Lw, (t + slant) / Lw
        c0 = lerp(_along(sides[0], u0), _along(sides[1], u0), 0.14)
        c1 = lerp(_along(sides[0], u1), _along(sides[1], u1), 0.86)
        pen.line([c0, c1], w=pen.r(1.15, 1.35), hand=0.2, lift=0)
        t += 5.85 + pen.r(-0.15, 0.25)


def _along(pts, u):
    """Point a share u of the way along a polyline."""
    total = sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    want = u * total
    for i in range(len(pts) - 1):
        d = dist(pts[i], pts[i + 1])
        if want <= d or i == len(pts) - 2:
            return lerp(pts[i], pts[i + 1], min(1.0, want / (d or 1)))
        want -= d
    return pts[-1]


for root, d, L, hwr in pegs:
    peg(root, d, L, hwr)

# centre the drawing in the square
xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
print('extent', round(max(xs) - min(xs)), round(max(ys) - min(ys)))
# a touch smaller, and nudged down and left so the weight of the loop sits nearer the centre
SCALE, NUDGE = 0.965, (-18.0, 16.0)
pen.strokes = [([((x - cx) * SCALE + 500 + NUDGE[0], (y - cy) * SCALE + 500 + NUDGE[1]) for x, y in p], w) for p, w in pen.strokes]
pen.save('../03-rna.svg', mirror=False)
pen.report()
