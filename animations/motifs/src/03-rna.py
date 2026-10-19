"""03 RNA: a single strand folded into a hairpin.

One sugar-phosphate backbone drawn as a flat ribbon, the bases as short pegs
standing off its inner side. The strand runs in from a single-stranded 5'
tail, up one side of a short paired stem (the pegs meet across it, a long
purine with a short pyrimidine), round a loop of unpaired bases and back
down, leaving as a short 3' tail. Where the ribbon twists and shows its back,
the back is shaded with hatching across the band, as in 04 DNA.
"""

import math

from pen import Pen, catmull, resample, dist, lerp

pen = Pen(seed=303)

HW = 16.0          # half width of the ribbon (as in 04)
PEG_HW = 7.0       # half thickness of a base peg (as in 04)
SP = 60.0          # base spacing along the strand
S = 186.0          # stem: strand centre to strand centre
GAP = 3.0          # gap where two paired pegs meet

ANG = math.radians(-56)
D = (math.cos(ANG), math.sin(ANG))      # stem axis, base to loop
P = (-D[1], D[0])                       # across the stem, strand 1 to strand 2
B0 = (500.0, 600.0)                     # stem base, on its axis (the drawing is centred afterwards)
NBP = 5
LS = (NBP - 1) * SP                     # first to last pair
E0, E1 = 30.0, 30.0                     # straight strand below the first / above the last pair
RL = 138.0                              # loop radius (ribbon centre)
LIGHT = (-0.6, -0.8)                    # light from the upper left


def fr(x, y):
    """A point given across (x, along P) and along (y, along D) the stem, from its base."""
    return (B0[0] + x * P[0] + y * D[0], B0[1] + x * P[1] + y * D[1])


def pt(side, u):
    """Point on the stem: side -1 strand 1, +1 strand 2; u along the axis from the first pair."""
    return fr(side * S / 2, u)


# the loop: a round bulb on the axis beyond the stem
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


# the 5' tail swings in from the left and hooks up into the stem; the 3' tail drops away below
tail5 = [fr(-S / 2 - 290, -E0 + 60), fr(-S / 2 - 255, -E0 - 95), fr(-S / 2 - 140, -E0 - 175), fr(-S / 2 - 30, -E0 - 108)]
tail3 = [fr(S / 2 + 6, -E0 - 95), fr(S / 2 + 70, -E0 - 178), fr(S / 2 + 180, -E0 - 205)]

ctrl = tail5 + stem_line(-1, -E0, LS + E1) + loop_pts() + stem_line(+1, LS + E1, -E0) + tail3
line = resample(catmull(ctrl, step=2.0), 2.0)

sl = [0.0]
for i in range(1, len(line)):
    sl.append(sl[-1] + dist(line[i - 1], line[i]))
TOTAL = sl[-1]


def at(s):
    """Point and unit tangent at arc length s."""
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
s_top1 = nearest_s(pt(-1, LS + E1))
s_top2 = nearest_s(pt(+1, LS + E1))
s_bot2 = nearest_s(pt(+1, -E0))


def ease(u):
    u = max(0.0, min(1.0, u))
    return 0.5 - 0.5 * math.cos(math.pi * u)


def twist(s):
    """How far the ribbon is turned from facing us (0 faces us, pi shows its back)."""
    tw = 0.0
    # a full turn along the 5' tail
    a, b = 25.0, s_bot1 - 55.0
    tw += 2 * math.pi * ease((s - a) / (b - a))
    # the loop rolls away from us over its top
    mid, half = (s_top1 + s_top2) / 2, (s_top2 - s_top1) / 2
    if abs(s - mid) < half:
        tw += 2.3 * ease(1.25 * (1 - abs(s - mid) / half))
    # a half turn in the 3' tail, ending on the ribbon's back
    a = s_bot2 + 45.0
    tw += math.pi * 0.85 * ease((s - a) / (TOTAL - 12 - a))
    return tw


# ---------------------------------------------------------------- ribbon samples

samples = []
s = 0.0
while s <= TOTAL + 0.01:
    p, t = at(s)
    nl = (t[1], -t[0])          # left of travel
    c = math.cos(twist(s))
    e1 = (p[0] + nl[0] * HW * c, p[1] + nl[1] * HW * c)
    e2 = (p[0] - nl[0] * HW * c, p[1] - nl[1] * HW * c)
    samples.append(dict(s=s, p=p, t=t, nl=nl, cos=c, e1=e1, e2=e2))
    s += 1.6


def shade(smp):
    """0 lit .. 1 dark, for the face we see."""
    c = smp['cos']
    if c < 0:
        return 0.62 + 0.38 * (1 - abs(c))
    return 1.0 * (1 - c) ** 1.2


# ---------------------------------------------------------------- the ribbon

for key in ('e1', 'e2'):
    pen.line([x[key] for x in samples], w=2.4, hand=1.1, piece=(26, 80), occlude=False)
for smp in (samples[0], samples[-1]):
    a, b = smp['e1'], smp['e2']
    L = dist(a, b) or 1
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    pen.line([(a[0] - u[0] * 2, a[1] - u[1] * 2), (b[0] + u[0] * 2.5, b[1] + u[1] * 2.5)], w=2.0, hand=0.3, occlude=False)

# hatching across the band where it turns away or shows its back
last = None
acc = 0.0
for i in range(1, len(samples) - 1):
    smp = samples[i]
    acc += dist(samples[i - 1]['p'], smp['p'])
    sh = shade(smp)
    if sh < 0.3:
        last, acc = None, 0.0
        continue
    sp = 9.5 - 4.0 * min(1.0, (sh - 0.3) / 0.6)
    if acc < sp:
        continue
    a, b = smp['e1'], smp['e2']
    if dist(a, b) < 5:
        continue
    if last is not None and min(dist(a, last[0]), dist(b, last[1])) < 5.0:
        continue
    acc = 0.0
    last = (a, b)
    t0 = pen.r(0.04, 0.16)
    t1 = 1 - pen.r(0.04, 0.2) - (0.35 * pen.r() if sh < 0.5 else 0)
    pen.line([lerp(a, b, t0), lerp(a, b, t1)], w=pen.r(0.85, 1.05), hand=0.3, lift=0.04, piece=(40, 120), occlude=False)

# the pegs go under the ribbon
for i in range(0, len(samples) - 4, 4):
    q = samples[i:i + 5]
    pen.occlude([x['e1'] for x in q] + [x['e2'] for x in q[::-1]])

# ---------------------------------------------------------------- bases

pegs = []   # (root on the centre line, direction, length, half width of the ribbon there)
pair_len = S - 2 * HW - GAP
purine = [1, 0, 0, 1, 0]
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
for k, L in enumerate([64, 48, 64, 64, 48, 64, 48, 64]):
    s = nearest_s(pt(-1, 0)) - SP * (k + 1)
    if s > 28:
        unpaired(s, L)
for k, L in enumerate([48, 64, 48, 64]):
    s = nearest_s(pt(+1, 0)) + SP * (k + 1)
    if s < TOTAL - 28:
        unpaired(s, L)


def over(a, b, da, db):
    """A segment run on past its ends by da and db."""
    L = dist(a, b) or 1
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    return [(a[0] - ux * da, a[1] - uy * da), (b[0] + ux * db, b[1] + uy * db)]


def peg(root, d, L, hwr):
    """A base: a short flat stick from under the ribbon's edge, its free end square."""
    n = (-d[1], d[0])
    a = (root[0] + d[0] * (hwr - 3), root[1] + d[1] * (hwr - 3))
    b = (root[0] + d[0] * (hwr + L), root[1] + d[1] * (hwr + L))
    lit = n[0] * LIGHT[0] + n[1] * LIGHT[1] > 0      # the +n side faces the light
    sides = []
    for sg in (1, -1):
        sides.append([(a[0] + sg * n[0] * PEG_HW, a[1] + sg * n[1] * PEG_HW), (b[0] + sg * n[0] * PEG_HW, b[1] + sg * n[1] * PEG_HW)])
    w_lit, w_dark = 1.6, 2.0
    # a hand overshoots the corners a little
    pen.line(over(*sides[0], 0, pen.r(0.5, 2.5)), w=w_lit if lit else w_dark, hand=0.6)
    pen.line(over(*sides[1], 0, pen.r(0.5, 2.5)), w=w_dark if lit else w_lit, hand=0.6)
    pen.line(over(sides[0][1], sides[1][1], pen.r(0.3, 1.6), pen.r(0.3, 1.6)), w=1.7, hand=0.2, lift=0)
    # the base is shaded: short strokes across it, slanted, as on the atoms of 02
    sp = 5.6
    m = int((hwr + L - (hwr + 2)) / sp)
    slant = 0.45
    for j in range(m):
        t = hwr + 3.5 + j * sp + pen.r(-0.2, 0.2)
        if t > hwr + L - 3:
            break
        c0 = (root[0] + d[0] * t + n[0] * (PEG_HW - 2.0), root[1] + d[1] * t + n[1] * (PEG_HW - 2.0))
        c1 = (root[0] + d[0] * (t + slant * 2 * PEG_HW) - n[0] * (PEG_HW - 2.0), root[1] + d[1] * (t + slant * 2 * PEG_HW) - n[1] * (PEG_HW - 2.0))
        if t + slant * 2 * PEG_HW > hwr + L - 2:
            break
        pen.line([c0, c1], w=pen.r(0.9, 1.1), hand=0.2, lift=0)


for root, d, L, hwr in pegs:
    peg(root, d, L, hwr)

# centre the drawing in the square
xs = [x for p, _ in pen.strokes for x, _ in p]
ys = [y for p, _ in pen.strokes for _, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
print('extent', round(max(xs) - min(xs)), round(max(ys) - min(ys)))
pen.strokes = [([(x - cx + 500, y - cy + 500) for x, y in p], w) for p, w in pen.strokes]
pen.save('../03-rna.svg', mirror=False)
pen.report()
