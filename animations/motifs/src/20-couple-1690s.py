#!/usr/bin/env python3
"""20 - An American couple of the 1890s, the Belle Epoque.

(The slug still reads couple-1690s: the couple was first drawn as a pair of
the 1690s, the time of the Amish split, and was restyled at Maxim's word to
look more modern.)

An American couple of the Gay Nineties. He in a straw boater, his hair cut
short and a trimmed moustache, a sack suit worn open over a buttoned waistcoat
with a watch chain across it, a high starched collar and a knotted tie, white
shirt cuffs, long creased trousers and laced shoes; she a Gibson girl, her
hair swept up into a full pompadour and a knot on the crown, a shirtwaist
with a high collar, a small bow tie and leg-of-mutton sleeves, a belted narrow
waist, a long gored skirt, and a small framed handbag. They stand side by
side, hand in hand, turned three-quarters to the right. Far off behind them a
factory flying its flag, its chimney smoking, and telegraph poles.

Drawn facing right with the light from the upper left; saved mirrored so that
on the page the couple faces the text.
"""

import bisect
import math

from pen import Pen, catmull, clip_segments, dist, ellipse_pts, inside, lerp, offset, resample


class InkPen(Pen):
    """Pen whose occlusion test first checks bounding boxes (many occluders here)."""

    def __init__(self, seed=1):
        super().__init__(seed)
        self.boxes = []

    def occlude(self, poly):
        poly = list(poly)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        self.occluders.append(poly)
        self.boxes.append((min(xs), min(ys), max(xs), max(ys)))

    def visible(self, pts):
        if not self.occluders:
            return [list(pts)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        cand = [(o, b) for o, b in zip(self.occluders, self.boxes)
                if not (b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1)]
        if not cand:
            return [list(pts)]

        def keep(p):
            x, y = p
            for o, b in cand:
                if b[0] <= x <= b[2] and b[1] <= y <= b[3] and inside(p, o):
                    return False
            return True
        return clip_segments(pts, keep)

    def save(self, path, mirror=False):
        """Keeps every stroke within the set's weights, 0.6 to 3."""
        self.strokes = [(p, min(3.0, max(0.6, w))) for p, w in self.strokes]
        super().save(path, mirror)


pen = InkPen(seed=1693)
TAU = 2 * math.pi


# ---------------------------------------------------------------- helpers

def C(ctrl, closed=False, step=2.0):
    return catmull(ctrl, closed=closed, step=step)


def S(ctrl, w=2.0, closed=False, hand=0.8, **kw):
    """A stroke through control points."""
    pen.line(C(ctrl, closed), w=w, hand=hand, **kw)


def F(ctrl, w=1.1, hand=0.3, **kw):
    """A fine detail stroke (faces, hands): little wobble, no lifts."""
    pen.line(C(ctrl), w=w, hand=hand, lift=0.0, **kw)


def R(ctrl):
    """A closed region through control points."""
    return C(ctrl, closed=True)


def clipped(seg, poly):
    if poly is None:
        return [seg]
    return clip_segments(seg, lambda p: inside(p, poly))


def ticks(ctrl, ang, spacing=6.0, maxlen=18.0, minlen=3.0, w=0.7, t0=0.05, t1=0.95,
          gap=1.2, clip=None, power=0.7, prof=None, hand=0.3, bow=0.0):
    """Short parallel strokes leaving a line on one side (fold shadows):
    each starts at the line and runs at angle `ang` (degrees, y down), its
    length swelling to maxlen in the middle of the run."""
    P = resample(C(ctrl), 0.5)
    cum = [0.0]
    for i in range(1, len(P)):
        cum.append(cum[-1] + dist(P[i - 1], P[i]))
    total = cum[-1]
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    s = t0 * total + pen.r(0, spacing * 0.5)
    while s < t1 * total:
        i = min(len(P) - 2, bisect.bisect_left(cum, s))
        p, q = P[i], P[i + 1]
        tx, ty = q[0] - p[0], q[1] - p[1]
        tl = math.hypot(tx, ty) or 1
        cr = abs(tx / tl * d[1] - ty / tl * d[0])
        u = (s / total - t0) / max(1e-6, t1 - t0)
        L = prof(u) if prof else maxlen * (max(0.0, math.sin(math.pi * u)) ** power)
        L *= pen.r(0.8, 1.15)
        if L >= minlen:
            a0 = (p[0] + d[0] * gap, p[1] + d[1] * gap)
            a1 = (p[0] + d[0] * (gap + L), p[1] + d[1] * (gap + L))
            if bow:
                m = lerp(a0, a1, 0.5)
                b = pen.g(bow)
                seg = catmull([a0, (m[0] - d[1] * b, m[1] + d[0] * b), a1], step=2.0)
            else:
                seg = [a0, a1]
            runs = clipped(seg, clip)
            if runs:
                pen.line(runs[0], w=w * pen.r(0.85, 1.15), hand=hand, lift=0.03, piece=(40, 120))
        s += spacing / max(0.35, cr) * pen.r(0.92, 1.08)


def across(railA, railB, spacing=6.5, frac=(0.35, 0.6), bow=2.0, w=0.7, t0=0.04, t1=0.96,
           from_b=True, clip=None, fprof=None):
    """Cross-contour hatching on a tube: strokes from rail B toward rail A
    (or A toward B), a fraction of the way across, bowing downward."""
    A = resample(C(railA), 1.0)
    B = resample(C(railB), 1.0)
    la = len(A) - 1
    lb = len(B) - 1
    avg = (la + lb) / 2.0
    n = max(1, int(avg * (t1 - t0) / spacing))
    for k in range(n):
        t = t0 + (t1 - t0) * (k + 0.5 + pen.g(0.12)) / n
        t = min(1.0, max(0.0, t))
        pa = A[int(t * la)]
        pb = B[int(t * lb)]
        f = pen.r(*frac)
        if fprof:
            f *= fprof(t)
        if f < 0.06:
            continue
        p0, p1 = (pb, pa) if from_b else (pa, pb)
        q0 = lerp(p0, p1, 0.04)
        q1 = lerp(p0, p1, f)
        m = lerp(q0, q1, 0.5)
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        if ny < 0:
            nx, ny = -nx, -ny
        bb = bow * f
        seg = catmull([q0, (m[0] + nx * bb, m[1] + ny * bb), q1], step=2.0)
        for run in clipped(seg, clip)[:1]:
            pen.line(run, w=w * pen.r(0.85, 1.15), hand=0.3, lift=0.03, piece=(40, 120))


def strands(railL, railR, us, w=0.85, t0=(0.0, 0.15), t1=(0.75, 1.0), wave=1.2, clip=None, hand=0.5):
    """Hair: strands flowing between two rails (both running top to bottom),
    each at a fraction u across, starting and ending at random heights."""
    A = resample(C(railL), 1.0)
    B = resample(C(railR), 1.0)
    for u in us:
        a, b = pen.r(*t0), pen.r(*t1)
        if b - a < 0.08:
            continue
        ph = pen.r(0, TAU)
        fr = pen.r(1.5, 3.0)
        pts = []
        N = 24
        for k in range(N + 1):
            t = a + (b - a) * k / N
            pa = A[int(t * (len(A) - 1))]
            pb = B[int(t * (len(B) - 1))]
            p = lerp(pa, pb, u)
            off = wave * math.sin(t * fr * TAU + ph)
            pts.append((p[0] + off, p[1]))
        for run in clipped(pts, clip):
            pen.line(run, w=w * pen.r(0.85, 1.15), hand=hand, lift=0.08, piece=(30, 90))


def frame(W, ang, sc=1.0):
    """Local coordinates for a hand: s runs along it from the wrist (at W,
    pointing at angle `ang` degrees), t across it, positive to the image's right."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    p = (math.sin(a), -math.cos(a))

    def f(pts):
        return [(W[0] + sc * (s * d[0] + t * p[0]), W[1] + sc * (s * d[1] + t * p[1])) for s, t in pts]
    return f


def tone(poly, angle, spacing, w=0.7, skip=0.0, shrink=(0.0, 0.1), keep=None, curve=0.0):
    pen.hatch(poly, angle=angle, spacing=spacing, w=w, skip=skip, shrink=shrink, keep=keep, curve=curve, hand=0.35)



def scallops(rail, r=2.2, w=0.8):
    """A frill: small arcs hanging below a rail, one after another."""
    P = resample(C(rail), 0.5)
    cum = [0.0]
    for i in range(1, len(P)):
        cum.append(cum[-1] + dist(P[i - 1], P[i]))
    s = 0.0
    while s + 2 * r <= cum[-1]:
        i0 = bisect.bisect_left(cum, s)
        i1 = min(len(P) - 1, bisect.bisect_left(cum, s + 2 * r))
        a, b = P[i0], P[i1]
        m = lerp(a, b, 0.5)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        if ny < 0:
            nx, ny = -nx, -ny
        F([a, (m[0] + nx * r * 1.1, m[1] + ny * r * 1.1), b], w=w, hand=0.05)
        s += 2 * r


def hatch_keep(poly, angle, spacing, keep, w=0.65, skip=0.0):
    pen.hatch(poly, angle=angle, spacing=spacing, w=w, skip=skip, shrink=(0.0, 0.08), keep=keep, hand=0.3)


# ================================================================ THE MAN

# ---- joined hands (front-most), hand in hand: his right hand hangs from the
# cuff with its back to us; her left hand lies palm to palm behind it, and her
# fingers come round its far edge and across its back, nails showing. His
# fingers curl round behind her hand; their bent joints show below.
mh = frame((522, 558), 108, 0.9)       # s down his hand from the wrist, t across it (+ to the right)
# her fingers across the back of his hand, the nearer ones over the further
her_f = [(6.0, 12.6, -1.0), (11.8, 18.6, -4.5), (17.8, 24.4, -2.5), (23.6, 29.4, 1.5)]
for k, (s0, s1, tt) in enumerate(her_f):
    r = (s1 - s0) / 2
    sc = (s0 + s1) / 2
    cap = [(sc - r * math.cos(q), tt + r - r * math.sin(q)) for q in [i * math.pi / 10 for i in range(11)]]
    F(mh([(s0, 15.5), (s0, 8)] + cap + [(s1, 8), (s1, 15.5)]), w=1.3 if k in (0, 3) else 1.2)
    F(mh([(s0 + 0.4, 15.5), (s0 + 1.5, 18.0), (sc, 19.2), (s1 - 1.5, 18.0), (s1 - 0.4, 15.5)]), w=1.2)   # round his edge
    nail = [(sc - r * 0.55 * math.cos(q), tt + r + 0.8 - r * 0.55 * math.sin(q)) for q in [i * math.pi / 8 for i in range(1, 8)]]
    F(mh(nail), w=0.75)
    F(mh([(s0 + 1.6, 10 + k), (sc, 9.5 + k), (s1 - 1.6, 10 + k)]), w=0.65)                         # a joint
    pen.occlude(R(mh([(s0, 19.5), (s0, tt + r)] + cap + [(s1, tt + r), (s1, 19.5)])))
# her thumb, over the back of his hand by the wrist
thumbW = [(495, 550), (505, 552.5), (513, 556.5), (517.5, 560), (517, 564), (513, 565), (505, 562.5), (497, 559.5)]
F([(495, 550), (505, 552.5), (513, 556.5), (517.5, 560), (517, 564), (513, 565)], w=1.3)
F([(513, 565), (505, 562.5), (498, 560)], w=1.3)
F([(512.5, 558.5), (515.5, 560.5), (514.5, 563)], w=0.7)                                           # its nail
pen.occlude(R(thumbW))
# his hand: the back, from the wrist to where the fingers bend round her hand
his_hand = mh([(-2, -14), (18, -15.2), (34, -15.5), (42, -13), (45, -4), (44, 6), (41, 13), (34, 15.5),
               (18, 15.5), (-2, 14)])
F(mh([(-2, -14), (10, -14.8), (22, -15.4), (33, -15.5)]), w=1.6)
F(mh([(-2, 14), (8, 15), (12, 15.5)]), w=1.5)
F(mh([(30, 15.5), (34, 15.5), (36, 15)]), w=1.4)
for k, (t0, t1, sb) in enumerate([(-15.5, -8, 44.0), (-8, -0.5, 46.0), (-0.5, 7.5, 45.0), (7.5, 15, 41.5)]):
    tm = (t0 + t1) / 2
    F(mh([(33.5, t0), (sb - 3.5, t0 + 0.3), (sb, tm), (sb - 3.5, t1 - 0.3), (33.5, t1)]), w=1.3)   # a bent finger
    F(mh([(31.5, t0 + 1.6), (33.2, tm), (31.5, t1 - 1.6)]), w=0.85)                               # its knuckle
F(mh([(2, -7), (13, -8)]), w=0.6)                                                                   # tendons
F(mh([(2, 0), (5, 1)]), w=0.6)
pen.occlude(R(his_hand))
# her hand behind, from her wrist to his hand
her_hand = [(463, 552), (483, 547), (496, 550), (511, 556), (502, 582), (496, 581), (485, 578), (475, 571), (468, 563)]
F([(483, 547), (490, 548.5), (496, 550)], w=1.5)
F([(464, 553), (467, 562), (474, 570), (484, 577), (495, 581), (500, 581.5)], w=1.5)
F([(478, 557), (487, 564), (494, 571)], w=0.65)
pen.occlude(R(her_hand))

# ---- his right shirt cuff, starched white, a link through it; the sleeve
# of the lounge coat ends a little above it
cuffN = [(507, 532), (527, 537), (547, 541), (541, 556), (521, 551), (503, 546)]
S([(507, 532), (504, 539), (503, 546)], w=1.5)
S([(547, 541), (544, 549), (541, 556)], w=1.5)
S([(503, 546), (521, 551), (541, 556)], w=1.5)
pen.ellipse(523, 545, 2.4, 2.0, w=0.9, hand=0.0, lift=0.0)                 # the cuff link
pen.occlude(R(cuffN))
sleeveN_out = [(557, 321), (547, 348), (540, 392), (536, 432), (527, 474), (515, 508), (507, 532)]
sleeveN_in = [(586, 352), (581, 392), (573, 432), (561, 473), (552, 512), (547, 541)]
S(sleeveN_out, w=2.2)
S(sleeveN_in, w=1.9)
S([(507, 532), (527, 537), (547, 541)], w=1.8)                            # the sleeve's end
F([(511, 528), (528, 532.5), (546, 536)], w=0.7)                          # its stitching
S([(572, 436), (563, 444), (552, 456)], w=1.2)                            # elbow creases
S([(574, 451), (564, 460), (556, 467)], w=1.1)
S([(569, 467), (558, 477)], w=0.95)
S([(539, 430), (543, 441)], w=0.8)
S([(556, 338), (552, 372), (548, 400)], w=0.9)
across(sleeveN_out, sleeveN_in, spacing=6.5, frac=(0.22, 0.42), bow=2.5, w=0.68, from_b=True)
pen.occlude(R(sleeveN_out + sleeveN_in[::-1]))

# ---- the straw boater: a flat brim of plaited straw, a low flat-topped
# crown circled by a dark ribbon; it sits level on his head
hm = (656, 172)
brimM = ellipse_pts(hm[0], hm[1], 64, 10, -0.03, 0, TAU, step=2.0)
pen.line(ellipse_pts(hm[0], hm[1], 64, 10, -0.03, -0.04, math.pi + 0.04, step=2.0), w=2.1, hand=0.3)
pen.line(ellipse_pts(hm[0], hm[1], 64, 10, -0.03, math.pi + 0.04, TAU - 0.04, step=2.0), w=1.3, hand=0.3)
pen.line(ellipse_pts(hm[0], hm[1] + 2.0, 61.5, 9.2, -0.03, 0.12, math.pi - 0.12, step=2.0), w=0.75, hand=0.2)
for k in range(1, 26):                                               # the straw's plait, round the brim
    a = 0.1 + (math.pi - 0.2) * k / 26
    p0 = (hm[0] + 64 * math.cos(a), hm[1] + 10 * math.sin(a))
    p1 = (hm[0] + 55 * math.cos(a + 0.035), hm[1] + 8.4 * math.sin(a + 0.035))
    F([p0, p1], w=0.6, hand=0.0)
tone(R([(600, 176), (630, 181), (660, 182), (690, 180), (712, 175), (700, 182), (660, 186), (620, 183)]), 70, 5.5,
     w=0.6, skip=0.2)                                                 # the brim's shadow side
pen.occlude(brimM)
S([(616, 171), (615, 160), (616, 150)], w=1.9)                        # the crown's sides
S([(696, 150), (697, 160), (696, 170)], w=1.9)
pen.line(ellipse_pts(656, 150, 40, 6, -0.03, 0, TAU, step=2.0), w=1.5, hand=0.2)   # its flat top
for k in range(1, 4):                                                 # plaited rows round the crown
    y = 150 + k * 2.6
    F([(616.5, y + 0.5), (636, y + 4.8), (656, y + 6), (676, y + 4.8), (695.5, y + 0.4)], w=0.6, hand=0.1)
band = [(615.5, 160), (636, 165), (656, 166.5), (676, 165), (696.5, 159.5), (696.5, 169.5), (676, 175), (656, 177),
        (636, 175), (616, 170)]
S([(615.5, 160), (636, 165), (656, 166.5), (676, 165), (696.5, 159.5)], w=1.1, hand=0.2)   # the ribbon
hatch_keep(R(band), 100, 5.0, lambda p: True, w=0.68)
F([(619, 163), (612, 159), (610, 166), (618, 167.5), (612, 173), (619, 172)], w=0.85)   # its bow
pen.occlude(R([(616, 172), (615, 160), (616, 149), (636, 145), (656, 144), (676, 145), (696, 149), (697, 160), (696, 171),
               (656, 178)]))

# ---- his head: clean-shaven but for a trimmed moustache, the face kept a
# pale plane; hair cut short at the back and sides
must = [(692, 235), (698, 231), (703, 230), (708, 232), (711, 236), (712, 240), (709, 243.5), (702, 244),
        (695, 245), (688, 247.5), (682.5, 247), (684, 242)]
F([(683, 247), (682, 243), (686, 239), (692, 235), (698, 231), (703, 230), (708, 232), (711, 236), (712, 240),
   (709, 243.5)], w=1.5)
F([(709, 243.5), (702, 244), (695, 245), (688, 247.5), (683, 247)], w=1.25)
for (a0, b0) in (((704, 233), (706, 241)), ((698, 234), (699, 242)), ((692, 238), (691, 244)), ((687, 242), (686, 246))):
    F([a0, b0], w=0.7)
pen.occlude(R(must))
# lips and chin in profile, the mouth's line, the jaw back to the ear
F([(709, 244), (710, 247.5), (708, 251), (704.5, 253.5), (705, 256), (708, 260), (708.5, 264), (705, 268),
   (698, 270.5), (690, 271)], w=1.6)
F([(708, 245.5), (701, 246.5), (694, 246.5)], w=1.1)                       # the mouth
F([(696, 250.5), (701.5, 251.5), (706, 250.5)], w=0.7)                     # under the lower lip
F([(698, 270.5), (686, 267.5), (672, 262), (662, 255), (656, 247), (653, 239)], w=1.6)   # the jaw, firm to its angle
# nose, eyes, brows, the forehead under the brim
S([(694, 181), (696, 188), (698, 192)], w=1.8)
F([(698, 192), (695.5, 199), (697, 204), (704, 212), (710, 219), (713, 223.5), (712.5, 227.5), (708.5, 229.5)], w=1.7)
F([(708.5, 229.5), (704, 230), (700, 228)], w=1.3)
F([(703, 222), (698, 224), (698, 228), (702, 230)], w=1.2)       # nostril wing
F([(683.5, 196), (684.5, 204), (688, 211.5), (694, 217.5), (699, 221.5)], w=0.95, hand=0.15)   # the nose's bridge
F([(661, 203.6), (666, 200.6), (671.5, 200), (677.4, 202.8)], w=1.9)   # upper lid
F([(664, 199), (670, 197.2), (676, 198.6)], w=0.6)                # its crease
F([(666.6, 206.0), (671.5, 206.4), (674.8, 204.7)], w=0.8)
pen.blot(671.2, 203.7, 2.5, w=2.0)
F([(687.5, 203.5), (691, 201.5), (694.5, 202.5)], w=1.5)         # far eye
pen.blot(691.4, 203.3, 1.5, w=1.3)
F([(655, 195), (661, 191.5), (669, 190.5), (680, 193.5)], w=1.9)  # brows
F([(687, 194.5), (692.5, 193), (697, 193.8)], w=1.5)
face = [(656, 178), (694, 179), (698, 193), (694, 201), (703, 211), (716, 224), (713, 240), (711, 250),
        (709, 263), (700, 271), (688, 272), (670, 260), (656, 246), (652, 232), (653, 200)]
pen.occlude(R(face))

# ear
ear = [(651, 199), (645, 196), (639, 201), (636, 212), (637, 223), (641, 231), (647, 233), (651, 228),
       (652, 214)]
F([(651, 199), (645, 196), (639, 201), (636, 212), (637, 223), (641, 231), (647, 233), (650, 229)], w=1.5)
F([(646, 202), (641, 207), (641, 217), (644, 223)], w=0.9)       # inner rim
pen.occlude(R(ear))

# short hair: close round the back of the skull, which rounds in to the nape
hair = [(606, 170), (655, 178), (655, 190), (651, 198), (645, 195), (638, 199), (636, 214), (636, 228), (637, 236),
        (634, 246), (624, 239), (614, 227), (608, 212), (605, 192)]
back = [(607, 172), (605, 190), (608, 208), (614, 224), (623, 237), (634, 246)]
S(back, w=1.9, hand=0.5)
F([(634, 246), (636.5, 240), (637.5, 232)], w=1.0, hand=0.3)         # the hairline behind the ear
F([(655, 180), (655.5, 190), (652, 198)], w=1.1)                       # the sideburn
for k, d in enumerate((5.5, 11.5, 17.5, 24.0)):                        # short hair, row on row round the skull
    rail = offset(C(back, step=1.0), d if offset(C(back), 1)[0][0] > back[0][0] else -d)
    for seg in [rail[i:i + 9] for i in range(k * 3, len(rail) - 6, 12)]:
        F(seg, w=0.72, hand=0.1)
for k in range(4):
    F([(653 - k * 2.5, 182 + k * 4), (643 - k * 3, 186 + k * 4.5)], w=0.65)   # combed back from the temple
pen.occlude(R(hair))
F([(634, 246), (637, 261), (641, 277)], w=1.5)                         # the back of the neck
F([(690, 271), (692, 277)], w=1.1)                                  # the throat
ticks([(655, 243), (668, 256), (684, 266)], ang=95, spacing=5.5, maxlen=7, w=0.6, minlen=2)   # under the jaw
pen.occlude(R([(634, 246), (651, 236), (664, 254), (684, 266), (696, 271), (696, 279), (641, 279), (637, 261)]))

# ---- the far hand and its shirt cuff, beside the coat
fh = frame((771, 563), 93)
# seen from the thumb side: the thumb lies forward along the index finger,
# the fingers hang loosely, their tips curling in toward the palm
far_hand = fh([(0, -12), (12, -13), (24, -14), (36, -14), (41, -15), (45, -15), (49, -12), (52, -10), (56, -5),
               (55, -2), (54, 2), (53, 5), (50, 7), (45, 8), (38, 9), (33, 10), (28, 13), (20, 15), (10, 14), (0, 12)])
F(fh([(0, 12), (10, 14), (20, 15), (28, 13), (32, 11), (34, 8), (32, 5), (26, 5), (18, 5), (11, 7)]), w=1.5)  # thumb
F(fh([(29, 9), (32, 7), (30, 6)]), w=0.6)                                                     # its nail
F(fh([(32, 9), (38, 9), (45, 8), (50, 7), (53, 5), (54, 2), (52, 0)]), w=1.5)                # index
F(fh([(52, 0), (55, -2), (56, -5), (53, -7), (51, -7)]), w=1.4)                              # middle
F(fh([(51, -7), (52, -10), (49, -12), (46, -12)]), w=1.4)                                    # ring
F(fh([(46, -12), (45, -15), (41, -15), (36, -14), (24, -14), (12, -13), (0, -12)]), w=1.6)  # little, palm edge
F(fh([(52, 0), (44, 1), (36, 2)]), w=0.9)                                                     # fingers parted
F(fh([(51, -7), (43, -7), (35, -6)]), w=0.85)
F(fh([(46, -12), (39, -11)]), w=0.8)
F(fh([(26, 13), (29, 11)]), w=0.6)
ticks(fh([(2, -12), (14, -13), (26, -14), (38, -14)]), ang=-10, spacing=4.5, maxlen=5, w=0.6, minlen=2)
pen.occlude(R(far_hand))
cuffF = [(755, 548), (789, 547), (788, 560), (756, 561)]
S([(755, 548), (756, 555), (756, 561)], w=1.5)
S([(789, 547), (789, 554), (788, 560)], w=1.6)
S([(756, 561), (772, 562), (788, 560)], w=1.5)
pen.occlude(R(cuffF))

# ---- the sack coat, worn open: lapels rolled to the top button, the
# fronts rounding away below to show the waistcoat
NF = [(660, 303), (663, 330), (661, 370), (656, 405), (652, 425), (649, 480), (647, 540), (643, 563), (632, 574),
      (618, 578)]
FF = [(704, 302), (706, 320), (703, 360), (700, 400), (698, 425), (700, 480), (703, 540), (708, 562), (720, 572),
      (735, 573)]
lapN_out = [(635, 324), (640, 352), (645, 387), (652, 425)]
lapF_out = [(716, 314), (712, 340), (705, 385), (698, 425)]
S(NF, w=1.8)
S(FF, w=1.6)
S(lapN_out, w=1.5)
S(lapF_out, w=1.2)
F([(626, 300), (632, 294), (641, 292), (652, 296), (661, 303)], w=1.5)   # the coat's collar behind his neck
F([(624, 300), (632, 312), (639, 318)], w=1.4)                      # its edge, to the notch
F([(645, 317.5), (635, 324)], w=1.4)                                # the lapel's top
F([(656, 305), (643, 319)], w=1.0)                                  # the gorge
F([(700, 300), (712, 304), (716, 314)], w=1.2)                      # the far collar
F([(707, 309), (716, 316)], w=0.9)
F([(643, 334), (646, 336)], w=0.8)                                  # buttonhole in the lapel
for y in (440, 472, 504):
    x = 649.5 - (y - 440) * 0.04
    F([(x - 7, y), (x - 2, y + 0.2)], w=0.85)                       # buttonholes down the near front
ticks(lapN_out, ang=10, spacing=6, maxlen=6, w=0.6, t0=0.15, t1=0.9)    # shadow under the lapel's edge
ticks([(706, 320), (703, 360), (700, 400), (698, 425)], ang=10, spacing=6, maxlen=6, w=0.6)
across([(706, 316), (712, 340), (705, 385), (699, 422)], [(716, 316), (714, 340), (708, 385), (700, 422)],
       spacing=6.5, frac=(0.5, 0.9), bow=0.5, w=0.6)
pen.occlude(R([(660, 303), (663, 330), (661, 370), (656, 405), (652, 425), (645, 387), (640, 352), (635, 324),
               (645, 317), (656, 305)]))
pen.occlude(R([(704, 302), (706, 320), (703, 360), (700, 400), (698, 425), (705, 385), (712, 340), (716, 314),
               (712, 304)]))
# the body of the coat
S([(626, 300), (600, 305), (576, 313), (557, 322)], w=2.1)          # shoulders
S([(704, 302), (712, 301), (727, 305), (744, 321)], w=2.0)
S([(586, 360), (588, 420), (590, 470), (588, 520), (584, 576)], w=2.1)   # the near side, under the arm
S([(584, 576), (600, 578), (618, 578)], w=2.0)                      # the hem
S([(741, 340), (738, 380), (740, 425), (742, 470), (746, 520), (750, 570)], w=2.0)
S([(720, 572), (735, 573), (750, 570)], w=1.9)
S([(560, 323), (569, 331), (579, 341), (586, 352)], w=0.9)          # armhole seam
S([(729, 307), (735, 324), (737, 344)], w=0.85)
S([(605, 382), (607, 440), (609, 524)], w=0.95)                     # the front dart
S([(722, 330), (724, 380), (726, 440), (729, 522)], w=1.0)          # the far side seam
S([(597, 372), (612, 371), (627, 369)], w=1.2)                      # breast pocket
F([(602, 371), (605, 364), (608, 369), (612, 362.5), (615, 368), (619, 365), (622, 370)], w=0.85)   # a folded handkerchief
S([(591, 527), (614, 527.5), (637, 526)], w=1.4)                    # pocket flaps
S([(591, 527), (591, 539), (614, 540), (637, 538), (637, 526)], w=1.3)
S([(712, 525), (727, 524.5), (742, 523)], w=1.2)
S([(712, 525), (713, 536), (728, 536), (743, 534), (742, 523)], w=1.2)
S([(592, 380), (606, 396), (622, 410)], w=0.85)                     # pulled by the reaching arm
S([(594, 404), (607, 416), (620, 428)], w=0.75)
ticks([(592, 380), (606, 396), (622, 410)], ang=100, spacing=6, maxlen=7, w=0.6, t0=0.1, t1=0.9)
S([(612, 470), (628, 476), (642, 474)], w=0.75)                     # creasing at the waist
# shading: the far side of the coat in shadow, under the arm, the near hem
strands([(706, 330), (703, 400), (701, 480), (706, 560)], [(740, 330), (739, 400), (743, 480), (749, 566)],
        [0.5, 0.66, 0.8, 0.92], w=0.7, t0=(0.15, 0.35), t1=(0.75, 0.97), wave=0.8, hand=0.4)
ticks([(588, 362), (589, 410), (590, 465), (588, 520)], ang=-15, spacing=6.5, maxlen=13, w=0.65)
tone(R([(586, 548), (630, 556), (645, 552), (643, 563), (632, 574), (618, 578), (584, 576)]), 62, 7.0, w=0.6,
     skip=0.2)
coatN = [(626, 300), (600, 305), (575, 312), (557, 322), (560, 360), (575, 400), (588, 440), (590, 470), (588, 520),
         (584, 576), (600, 578), (618, 578), (632, 574), (643, 563), (647, 540), (649, 480), (652, 425), (656, 405),
         (661, 370), (663, 330), (660, 303), (641, 291), (630, 295)]
coatF = FF + [(750, 570), (746, 520), (742, 470), (740, 425), (738, 380), (741, 340), (743, 322), (727, 305),
              (712, 301)]
pen.occlude(R(coatN))
pen.occlude(R(coatF))

# ---- the waistcoat: buttoned high, pointed below, a watch chain across it
# from a buttonhole to the pocket
chain = resample(C([(683, 417), (678, 428), (670, 435), (662, 434), (656, 429)]), 2.6)
for k, p in enumerate(chain[:-1]):
    q = chain[k + 1]
    m = lerp(p, q, 0.5)
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    pen.ellipse(m[0], m[1], 1.6, 0.9 if k % 2 else 1.2, rot=a, w=0.75, hand=0.0, lift=0.0)
F([(680, 417.5), (686, 416.5)], w=1.2)                              # the bar through the buttonhole
F([(670, 435.5), (671, 441)], w=0.8)                                # a fob hanging from it
pen.ellipse(671.5, 444, 2.4, 2.8, w=0.9, hand=0.0, lift=0.0)
pen.occlude(R([(681, 412), (688, 416), (680, 432), (671, 450), (664, 440), (654, 433), (656, 425), (668, 431)]))
F([(652, 427), (664, 426)], w=1.0)                                  # its pocket
waist_poly = [(661, 303), (666, 306), (682, 362), (702, 306), (705, 303), (706, 320), (703, 360), (700, 400), (698, 425),
              (700, 480), (700, 492), (692, 499), (682, 507), (664, 498), (649, 492), (649, 480), (652, 425),
              (656, 405), (661, 370), (663, 330)]
S([(666, 306), (674, 334), (682, 362)], w=1.3)                      # its opening
S([(702, 306), (692, 334), (682, 362)], w=1.2)
S([(649, 491), (664, 498), (682, 507), (692, 499), (700, 492)], w=1.5)   # its points
S([(682, 362), (682.5, 430), (682.5, 506)], w=1.0)
for y in range(374, 500, 21):
    pen.ellipse(684.5, y, 1.9, 1.8, w=0.95, hand=0.0, lift=0.0)
F([(688, 452), (698, 451)], w=0.9)                                  # the far pocket
hatch_keep(R(waist_poly), 68, 5.5, lambda p: True, w=0.62, skip=0.05)
pen.occlude(R(waist_poly))

# ---- the shirt front and the tie, knotted under the high collar
tie = [(689, 298), (699, 298), (697, 307), (695, 330), (690, 352), (680, 352), (687, 330), (691, 307)]
F([(689, 298), (699, 298), (697, 307), (691, 307), (689, 298)], w=1.3)          # the knot
F([(691, 307), (687, 330), (680, 352)], w=1.2)
F([(697, 307), (695, 330), (690, 352)], w=1.2)
F([(693, 308), (690, 322)], w=0.6)
hatch_keep(R(tie), 120, 5.0, lambda p: True, w=0.6)
pen.occlude(R(tie))
F([(674, 312), (680, 330)], w=0.6)                                  # the shirt's pleat
pen.occlude(R([(666, 306), (682, 362), (702, 306), (700, 298), (670, 300)]))
# the high starched collar, straight round the neck, its fronts meeting under the chin
F([(692, 278), (691.5, 288), (691, 297)], w=1.4)
F([(699, 279), (699.5, 288), (700, 296)], w=1.1)
F([(692, 278), (676, 277), (660, 277.5), (648, 278), (641, 277.5)], w=1.4)
F([(641, 277.5), (640.5, 285), (640, 292)], w=1.2)
F([(699, 279), (704, 278), (707, 280)], w=1.0)
F([(691, 297), (676, 298.5), (662, 300)], w=1.1)
F([(696, 297), (700, 296), (704, 300)], w=0.9)
pen.occlude(R([(641, 277), (692, 277), (707, 279), (705, 302), (640, 296)]))

# ---- his far coat sleeve, behind the body
sleeveF_out = [(744, 321), (759, 350), (769, 398), (776, 450), (783, 498), (788, 530), (789, 547)]
sleeveF_in = [(734, 380), (742, 430), (748, 480), (752, 530), (755, 548)]
S(sleeveF_out, w=2.1)
S(sleeveF_in, w=1.8)
S([(755, 548), (772, 549.5), (789, 547)], w=1.7)
across(sleeveF_in, sleeveF_out, spacing=6.5, frac=(0.45, 0.75), bow=2, w=0.65, from_b=True)
S([(766, 410), (770, 440)], w=0.8)
S([(752, 340), (761, 380), (767, 420)], w=0.8)                      # sleeve seam
S([(749, 458), (759, 465), (767, 477)], w=1.2)                      # elbow creases
S([(751, 476), (760, 484), (765, 492)], w=1.05)
S([(770, 440), (776, 452)], w=0.95)
pen.occlude(R(sleeveF_out + sleeveF_in[::-1]))


# ---- trousers: long, pressed to a crease, breaking over the shoes
S([(683, 507), (684, 560), (680, 598), (669, 613)], w=1.0)          # the fly
F([(658, 614), (664, 617.5), (670, 614)], w=1.3)                    # the fork
NB = [(588, 578), (589, 640), (591, 720), (596, 800), (600, 870), (602, 912)]
NFL = [(658, 614), (652, 660), (650, 720), (645, 800), (641, 870), (642, 914)]
FB = [(670, 614), (676, 660), (677, 750), (683, 820), (688, 870), (691, 902)]
FFL = [(738, 576), (737, 640), (734, 720), (728, 800), (722, 860), (719, 900)]
S(NB, w=2.0)
S(NFL, w=1.9)
S(FB, w=1.8)
S(FFL, w=2.0)
S([(627, 582), (626, 700), (623, 800), (622, 900)], w=0.85, hand=0.4)   # the creases
S([(713, 578), (709, 700), (705, 800), (705, 898)], w=0.8, hand=0.4)
F([(602, 912), (614, 915.5), (629, 917.5), (642, 914)], w=1.6)     # the hems
F([(691, 902), (705, 904), (719, 900)], w=1.5)
F([(604, 886), (614, 892), (626, 893)], w=0.8)                     # breaking over the shoe
F([(629, 890), (637, 886), (641, 880)], w=0.75)
F([(690, 878), (700, 883), (710, 882)], w=0.75)
F([(711, 880), (719, 874)], w=0.7)
F([(600, 600), (612, 610), (628, 614)], w=0.7)                     # at the hip
across(NB, NFL, spacing=7.0, frac=(0.22, 0.4), bow=3, w=0.65, t0=0.04, t1=0.97)
across(FB, FFL, spacing=6.5, frac=(0.45, 0.7), bow=3, w=0.65, t0=0.04, t1=0.97)
tone(R([(588, 578), (651, 578), (655, 596), (620, 600), (589, 594)]), 62, 6.0, w=0.6)    # under the coat's hem
tone(R([(677, 578), (737, 576), (737, 598), (676, 600)]), 62, 6.0, w=0.6)
tone(R([(649, 506), (682, 507), (700, 492), (704, 545), (708, 562), (720, 572), (738, 576), (676, 612), (658, 614),
        (651, 578), (647, 540)]), 68, 6.5, w=0.6, skip=0.15)
pen.occlude(R([(645, 490), (705, 490), (712, 578), (677, 616), (651, 616), (645, 578)]))
pen.occlude(R(NB + NFL[::-1] + [(651, 578)]))
pen.occlude(R(FB + FFL[::-1] + [(677, 578)]))

# ---- laced shoes with capped toes, the near one turned out a little
shoeN = [(603, 913), (601, 926), (600, 938), (616, 943), (639, 947), (658, 954), (669, 955), (673, 945), (667, 937),
         (652, 926), (642, 914)]
S([(603, 913), (601, 926), (601, 936)], w=1.9)
S([(601, 936), (604, 942), (617, 943), (618, 936)], w=1.7)                 # heel
S([(617, 937), (639, 946), (658, 953), (667, 955)], w=2.0)                 # sole
S([(667, 955), (673, 950), (672, 943), (667, 937)], w=2.0)                 # round toe
S([(667, 937), (652, 926), (642, 916)], w=1.7)                             # vamp
S([(619, 931), (640, 939.5), (659, 946.5), (670, 949)], w=1.2)             # the sole's edge
S([(654, 927), (650, 935), (649, 945)], w=1.1)                             # the toe cap
for k in range(3):                                                          # the lacing
    t = k / 2.0
    a = lerp((633, 917), (646, 924), t)
    pen.ellipse(a[0] - 2.6, a[1] + 2.4, 0.9, 0.9, w=0.7, hand=0.0, lift=0.0)
    F([(a[0] - 2.6, a[1] + 2.4), (a[0] + 2.2, a[1] - 1.8)], w=0.85)
F([(645, 924), (648, 930), (652, 931)], w=0.8)                              # an end of the lace
tone(R([(617, 925), (641, 929), (654, 933), (666, 940), (670, 946), (659, 945), (640, 938), (620, 931)]), 30, 6.5,
     w=0.62, skip=0.2)
pen.occlude(R(shoeN))
shoeF = [(691, 902), (689, 912), (690, 922), (692, 931), (708, 932), (730, 930), (752, 932), (764, 930),
         (766, 922), (758, 915), (742, 908), (719, 900)]
S([(691, 902), (689, 912), (690, 922)], w=1.8)
S([(690, 922), (692, 931), (708, 932), (708, 924)], w=1.6)
S([(708, 926), (730, 929), (752, 932), (762, 930)], w=1.9)
S([(762, 930), (766, 925), (764, 919), (758, 915)], w=1.9)
S([(758, 915), (742, 908), (720, 902)], w=1.6)
S([(710, 924.5), (732, 926.5), (752, 928.5), (763, 927.5)], w=1.15)
S([(748, 911), (744, 919), (743, 927)], w=1.0)
for k in range(3):
    t = k / 2.0
    a = lerp((722, 903), (738, 908), t)
    F([(a[0] - 1.6, a[1] + 2.6), (a[0] + 1.8, a[1] - 1.8)], w=0.8)
tone(R([(703, 908), (730, 908), (744, 913), (760, 919), (765, 924), (752, 926), (730, 923), (710, 920)]), 30, 6.5,
     w=0.62, skip=0.2)
pen.occlude(R(shoeF))


# ================================================================ THE WOMAN

fist = [(264, 562), (260, 576), (261, 590), (262, 604), (269, 608), (276, 609), (283, 607), (290, 604),
        (296, 596), (297, 584), (293, 570), (290, 562)]
F([(290, 563), (294, 572), (297, 582), (297.5, 590), (295, 596.5), (290, 599), (285, 598.5), (283, 595.5),
   (285, 593), (290, 591)], w=1.5)                                             # the thumb over the handle
F([(285.5, 595.5), (288, 597.5), (291, 596.5)], w=0.75)                        # its nail
F([(291, 585), (294, 590)], w=0.7)
pen.occlude(R([(291, 572), (297, 582), (297.5, 590), (295, 596.5), (290, 599), (285, 598.5), (283, 595.5),
               (285, 593), (289, 588)]))
F([(264, 562), (260.5, 575), (261, 588)], w=1.6)                               # back of the hand
for k, (x0, x1, yb) in enumerate([(261, 268.5, 606), (268.5, 275.5, 608), (275.5, 282.5, 607), (282.5, 288, 603)]):
    xm = (x0 + x1) / 2
    F([(x0, 589 + k * 0.3), (x0 + 0.2, yb - 4), (xm, yb), (x1 - 0.2, yb - 4), (x1, 591)], w=1.3)   # a finger
    F([(x0 + 0.8, 590 + k * 0.3), (x0 + 1.8, 587.6), (xm, 586.6 + k * 0.2), (x1 - 1.8, 587.6), (x1 - 0.8, 590)], w=1.0)   # knuckle
    F([(x0 + 1.6, yb - 7.5), (xm, yb - 6.5), (x1 - 1.6, yb - 7.5)], w=0.65)                        # its joint
F([(268, 570), (271, 580)], w=0.6)                                             # tendons
F([(276, 570), (278, 580)], w=0.6)
pen.occlude(R(fist))

# ---- her handbag on a short handle: a framed purse with a kiss-lock clasp
for (top, bot) in (((265, 601), (252, 644)), ((293, 601), (305, 644))):
    mid = lerp(top, bot, 0.5)
    rib = C([top, (mid[0] + (-2 if top[0] < 280 else 2), mid[1]), bot])
    F(rib, w=1.05)
    F(offset(rib, 2.2), w=0.85)
    pen.occlude(rib + offset(rib, 2.2)[::-1])
pen.ellipse(277, 641, 2.6, 2.6, w=1.0, hand=0.0, lift=0.0)          # the clasp's two balls
pen.ellipse(283, 641, 2.6, 2.6, w=1.0, hand=0.0, lift=0.0)
pen.occlude(R([(273, 637), (287, 637), (287, 645), (273, 645)]))
frame_t = [(246, 649), (262, 645), (280, 643.5), (298, 645), (313, 649)]
frame_b = [(247, 654), (262, 650), (280, 648.5), (298, 650), (312, 654)]
S(frame_t, w=1.6, hand=0.2)
S(frame_b, w=1.2, hand=0.2)
pen.occlude(R(frame_t + frame_b[::-1]))
bag = [(247, 654), (241, 676), (243, 700), (258, 710), (280, 713), (301, 710), (316, 700), (317, 676), (312, 654)]
S([(247, 654), (241, 676), (243, 698), (258, 709.5), (280, 713), (301, 710), (316, 699), (317, 676), (312, 654)],
  w=1.9)
F([(262, 652), (258, 675), (262, 700)], w=0.8)                      # gathers at the frame
F([(280, 650), (280, 680), (281, 708)], w=0.7)
F([(298, 652), (301, 676), (298, 702)], w=0.8)
across([(248, 657), (242, 677), (244, 699)], [(312, 657), (317, 677), (315, 699)], spacing=6, frac=(0.25, 0.45),
       bow=2, w=0.62)
pen.occlude(R(bag))

# ---- her sleeve ends: tight at the wrist, a narrow frill falling from each
S([(263, 548), (278, 550.5), (293, 550)], w=1.5)
scallops([(263, 550), (278, 552.5), (293, 552)], r=2.3, w=0.85)
pen.occlude(R([(262, 546), (294, 548), (294, 557), (262, 556)]))
S([(456, 540), (470, 537), (484, 534)], w=1.5)
scallops([(456, 542), (470, 539), (485, 536)], r=2.3, w=0.85)
pen.occlude(R([(454, 537), (485, 530), (488, 541), (459, 548)]))

# ---- her near sleeve: the leg-of-mutton, full at the shoulder, close below
sleeveW_out = [(318, 324), (299, 330), (283, 348), (275, 376), (278, 406), (286, 430), (287, 452), (281, 490),
               (272, 525), (263, 548)]
sleeveW_in = [(333, 399), (319, 424), (305, 446), (299, 468), (296, 506), (293, 550)]
S(sleeveW_out, w=2.1)
S(sleeveW_in, w=1.8)
S([(326, 326), (332, 352), (335, 378), (333, 399)], w=1.4)          # its seam against the bodice
for (a0, a1) in (((309, 329), (304, 340)), ((316, 327), (313, 339)), ((323, 327), (322, 338)), ((302, 333), (295, 342))):
    F([a0, a1], w=0.75)                                              # gathered into the shoulder
F([(303, 338), (289, 368), (288, 400), (295, 428)], w=0.85)        # the puff's folds
F([(316, 340), (305, 376), (306, 410)], w=0.85)
F([(325, 345), (318, 380), (320, 400)], w=0.75)
F([(288, 446), (299, 451)], w=0.8)                                   # where it closes in at the elbow
F([(284, 470), (296, 474)], w=0.7)
across([(278, 400), (286, 430), (288, 452)], [(332, 401), (318, 425), (304, 447)], spacing=6.0, frac=(0.25, 0.5),
       bow=2.5, w=0.62, from_b=True)
across([(286, 456), (281, 490), (272, 525), (265, 545)], [(299, 468), (297, 490), (296, 520), (293, 546)],
       spacing=6.5, frac=(0.25, 0.45), bow=1.5, w=0.62, from_b=True)
pen.occlude(R(sleeveW_out + sleeveW_in[::-1] + [(345, 320)]))

# ---- her head: the face, then the boater, the pompadour and the ear
F([(405, 229), (406, 239), (407, 244)], w=1.6)
F([(407, 244), (405, 251), (406, 255), (409, 260.5), (411, 264.5), (411.3, 267.3), (409.4, 269.2), (406.6, 269.7),
   (404, 268.8)], w=1.5)
F([(405.5, 262.5), (402, 263.5), (400.5, 267), (403, 269.5)], w=1.0)    # nostril wing
F([(394.5, 246.5), (395.2, 253), (397.6, 258.6), (401.2, 262.6)], w=0.85, hand=0.15)   # the nose's bridge
F([(405.5, 270.5), (406.8, 275), (408.2, 279.2)], w=1.1)                # upper lip, in profile
F([(408.2, 279.2), (406.3, 282.4), (407.6, 285.4), (405.2, 288.6)], w=1.2)   # the lips' fronts
F([(391, 282.6), (396, 283.8), (401.5, 284), (406.3, 282.6)], w=1.25)   # the mouth, its corner lifting
F([(393.5, 280.4), (399, 279.6), (404.5, 279.9)], w=0.7)               # the upper lip's edge
F([(395, 288), (398.5, 290.2), (402, 290), (405, 288.4)], w=1.1)        # a full lower lip
F([(404, 273.5), (403.2, 277.5)], w=0.6)                                # philtrum
F([(405.2, 288.6), (403.6, 294), (400, 298.6), (393, 302), (385, 302.2)], w=1.6)   # a soft, smaller chin
F([(385, 302.2), (374, 299.6), (364, 294), (357, 288)], w=1.4)          # jaw
# eyes: lids, lashes, irises
F([(373, 251.8), (376.5, 248), (381.6, 247), (387, 249.8)], w=1.5)
F([(375, 246.4), (380, 244.6), (385.8, 246.4)], w=0.65)                 # lid crease
F([(376, 253.6), (381, 254.4), (386, 252)], w=0.7)
for (x0, y0) in ((373.8, 251.2), (375.6, 249.2), (377.8, 247.9)):
    F([(x0, y0), (x0 - 2.2, y0 - 1.8)], w=0.6)                          # lashes
pen.blot(382.4, 250.6, 1.9, w=1.25)
F([(398, 251), (401.2, 248.4), (404.4, 250.2)], w=1.25)
F([(399.5, 252.8), (403, 252.8)], w=0.6)
pen.blot(401.3, 250.5, 1.25, w=1.05)
F([(368, 245), (373, 241.8), (380, 240.2), (386, 240.8), (391, 243)], w=1.35)   # brows, softly arched
F([(397.5, 243.5), (401, 241.8), (405, 242.2)], w=1.15)
F([(387, 302.5), (389, 308.5)], w=1.2)                                   # the throat
ticks([(386, 304), (378, 302), (368, 298)], ang=95, spacing=5, maxlen=5, w=0.6, minlen=2)
pen.occlude(R([(372, 226), (405, 228), (407, 244), (413, 267), (409, 280), (403, 292), (386, 304), (390, 312), (360, 308),
               (358, 290), (360, 268), (362, 246)]))
# the hair, Gibson-girl fashion: swept up all round into a full, soft
# pompadour, gathered in a knot on the crown
hairW = [(405, 229), (411, 222), (415, 212), (413, 202), (404, 195), (388, 191), (370, 190), (352, 192), (336, 198),
         (325, 210), (319, 228), (318, 246), (324, 264), (332, 278), (342, 287), (348, 291), (346, 282), (342, 268), (344, 256),
         (352, 251), (360, 249), (364, 240), (372, 232), (385, 228), (396, 227)]
S([(405, 229), (411, 222), (415, 212), (413, 202), (404, 195), (388, 191), (370, 190)], w=1.6, hand=0.4)
S([(338, 197), (325, 210), (319, 228), (318, 246), (323, 264), (332, 278), (342, 287), (348, 291)], w=1.8, hand=0.5)
F([(405, 229), (396, 227), (385, 228), (372, 232), (364, 240), (360, 250), (353, 254)], w=1.0)   # the hairline
for k in range(9):                                                    # up from the face, over the roll, back
    t = k / 8.0
    p0 = lerp((403, 228), (361, 247), t)
    end = lerp((354, 197), (326, 236), t)
    c1 = (p0[0] + 5 - 4 * t, p0[1] - 11 + 2 * t)
    c2 = lerp((400, 200), (338, 222), t)
    pts = catmull([p0, c1, c2, end], step=1.5)
    pen.line(pts, w=0.72, hand=0.25, lift=0.15, piece=(14, 30))
for k in range(4):                                                    # from the nape up the back of the head
    F([(346 - k * 2.6, 286 - k * 5), (330 + k * 1.5, 254 - k * 3), (334 + k * 2.5, 216 - k), (348, 196 + k)],
      w=0.72, hand=0.15)
F([(411, 208), (403, 213), (400, 224)], w=0.8)                       # the roll's underside
ticks([(412, 210), (403, 215), (400, 225)], ang=10, spacing=5, maxlen=5, w=0.55, minlen=2)
pen.occlude(R(hairW))
knot = ellipse_pts(350, 189, 14, 8, -0.2, 0, TAU, step=2.0)
pen.line(ellipse_pts(350, 189, 14, 8, -0.2, 2.6, 6.8, step=2.0), w=1.6, hand=0.3)
F([(339, 192), (348, 184.5), (360, 185)], w=0.8)                      # its coils
F([(342, 194.5), (351, 190), (362, 190.5)], w=0.75)
pen.occlude(knot)
F([(357, 254), (351, 252), (346, 257), (345, 266), (348, 276), (353, 281), (357.5, 279)], w=1.4)   # the ear
F([(352, 258), (349, 264), (351, 272)], w=0.75)
pen.occlude(R([(358, 250), (346, 254), (344, 268), (349, 280), (358, 282)]))
F([(348, 291), (349, 298)], w=1.2)                                     # the nape

# ---- her high collar, boned, a brooch at its front
F([(390, 308), (372, 304.5), (356, 300.5), (347, 298)], w=1.4)
F([(394, 328), (376, 327), (358, 322), (345, 319)], w=1.4)
F([(390, 308), (392, 318), (394, 328)], w=1.4)
F([(347, 298), (346, 309), (345, 319)], w=1.1)
for x in (356, 366, 377):
    F([(x, 303.5 + (x - 356) * 0.03), (x - 0.5, 323 + (x - 356) * 0.15)], w=0.6)
F([(390, 323), (383, 319), (382, 326.5), (390, 324)], w=1.0)          # a small bow tie at the collar
F([(393, 323), (400, 319.5), (401, 327), (393, 324.5)], w=1.0)
pen.blot(391.5, 323.7, 1.6, w=1.1)
F([(390.5, 325.5), (388.5, 333)], w=0.85)
F([(392.5, 325.5), (395, 333.5)], w=0.85)
pen.occlude(R([(382, 318), (401, 318), (402, 328), (396, 335), (387, 335), (381, 327)]))
pen.occlude(R([(390, 308), (347, 298), (345, 319), (394, 328)]))

# ---- the shirtwaist blouse: shaped over the bust, pin tucks down the front, small
# buttons; the belt drawn in at a narrow waist
S([(318, 324), (330, 321), (345, 319)], w=1.8)                        # near shoulder
S([(394, 328), (405, 343), (415, 366), (419, 392), (415, 418), (410, 442), (412, 462)], w=2.0)   # the front
S([(333, 400), (337, 430), (342, 462)], w=1.8)                        # the near side
S([(380, 325), (404, 327), (424, 327)], w=1.7)                        # far shoulder
for y in range(338, 458, 17):
    x = 392 + 7 * math.sin(math.pi * (y - 328) / 135)
    pen.ellipse(x, y, 1.6, 1.6, w=0.85, hand=0.0, lift=0.0)
for dx in (7, 13, 19):
    F([(390 - dx * 0.8, 334), (397 - dx, 380), (397 - dx, 420), (394 - dx * 0.9, 460)], w=0.65, hand=0.2)
F([(404, 395), (410, 410)], w=0.7)                                    # the bust's shadow
ticks([(394, 330), (405, 345), (415, 368), (419, 392), (415, 418), (410, 442), (412, 460)], ang=185, spacing=6,
      maxlen=12, w=0.6, t0=0.05, t1=0.98, power=0.5)
ticks([(343, 410), (360, 420), (375, 422)], ang=90, spacing=6, maxlen=8, w=0.55, minlen=2)
tone(R([(334, 402), (352, 412), (362, 440), (352, 462), (342, 462), (337, 430)]), 62, 6.5, w=0.6)
pen.occlude(R([(345, 319), (394, 328), (405, 343), (415, 366), (419, 392), (415, 418), (410, 442), (412, 462),
               (342, 462), (337, 430), (333, 400), (318, 324)]))
belt = [(342, 461), (378, 464.5), (413, 460), (414, 475), (378, 479), (343, 476)]
S([(342, 461), (378, 464.5), (413, 460)], w=1.5)
S([(343, 476), (378, 479), (414, 475)], w=1.5)
F([(394, 461), (394, 477.5)], w=1.2)                                  # the buckle
F([(404, 460.5), (404, 476.5)], w=1.2)
F([(394, 461), (404, 460.5)], w=1.0)
F([(394, 477.5), (404, 476.5)], w=1.0)
F([(398, 465), (399, 473)], w=0.8)
hatch_keep(R(belt), 80, 5.0, lambda p: not (393 < p[0] < 405), w=0.62)
pen.occlude(R(belt))

# ---- her far sleeve, reaching for his hand: the puff above, close below
sleeveW2_out = [(424, 327), (446, 334), (461, 356), (466, 388), (460, 418), (453, 444), (458, 472), (466, 500),
                (474, 520), (484, 534)]
sleeveW2_in = [(424, 438), (436, 470), (446, 505), (456, 540)]
S(sleeveW2_out, w=2.1)
S(sleeveW2_in, w=1.8)
F([(432, 332), (446, 352), (452, 385), (446, 414)], w=0.85)          # the puff's folds
F([(427, 340), (438, 372), (437, 402)], w=0.75)
across([(419, 395), (424, 420), (430, 445)], [(466, 392), (460, 418), (453, 444)], spacing=6.0, frac=(0.35, 0.6),
       bow=2.5, w=0.62, from_b=True)
across(sleeveW2_in, [(452, 446), (460, 475), (468, 505), (482, 532)], spacing=6.5, frac=(0.4, 0.7), bow=2, w=0.62,
       from_b=True)
F([(452, 470), (444, 478)], w=0.8)                                    # creases at the elbow
F([(456, 484), (447, 491)], w=0.75)
pen.occlude(R(sleeveW2_out + sleeveW2_in[::-1] + [(419, 395)]))

# ---- the gored skirt: close over the hips, flaring smoothly to the hem
skirt_L = [(343, 476), (326, 530), (306, 610), (286, 700), (266, 790), (248, 860), (231, 905)]
skirt_R = [(414, 476), (430, 530), (446, 610), (463, 700), (480, 790), (494, 860), (504, 903)]
hem = [(231, 905), (248, 912), (264, 909), (284, 918), (306, 922), (324, 918), (345, 926), (375, 929),
       (405, 928), (428, 924), (446, 926), (470, 918), (490, 912), (504, 903)]
S(skirt_L, w=2.2)
S(skirt_R, w=2.2)
S(hem, w=2.0)
gores = [[(358, 480), (338, 600), (306, 760), (284, 917)],
         [(377, 481), (373, 600), (365, 760), (360, 928)],
         [(397, 480), (408, 600), (420, 760), (428, 924)]]
for g in gores:
    S(g, w=0.9, hand=0.5)
flutes = [[(318, 700), (300, 800), (264, 909)], [(340, 760), (330, 850), (324, 918)],
          [(392, 780), (395, 860), (405, 928)], [(450, 760), (460, 850), (470, 918)],
          [(300, 780), (284, 860), (276, 912)]]
for fl in flutes:
    S(fl, w=1.0)
ticks(flutes[0], ang=-15, spacing=6, maxlen=14, w=0.62, t0=0.1, t1=0.99, power=0.6)
ticks(flutes[1], ang=-15, spacing=6, maxlen=10, w=0.62, t0=0.1, t1=0.99, power=0.6)
ticks(flutes[2], ang=-15, spacing=6, maxlen=10, w=0.62, t0=0.1, t1=0.99, power=0.6)
ticks(flutes[3], ang=-15, spacing=6, maxlen=12, w=0.62, t0=0.1, t1=0.99, power=0.6)
ticks([(346, 482), (378, 485), (412, 481)], ang=90, spacing=6.5, maxlen=6, w=0.55, minlen=2)   # under the belt
strands([(430, 540), (446, 620), (461, 720), (476, 820), (488, 910)], [(432, 535), (449, 615), (465, 705), (482, 795), (503, 900)],
        [0.0, 0.5, 1.0], w=0.7, t0=(0.0, 0.1), t1=(0.85, 1.0), wave=0.6, hand=0.4)
strands([(412, 560), (432, 680), (450, 800), (468, 915)], [(436, 560), (455, 680), (472, 800), (488, 910)],
        [0.3, 0.7], w=0.65, t0=(0.15, 0.3), t1=(0.85, 1.0), wave=0.6, hand=0.4)
strands([(305, 640), (288, 740), (268, 840), (250, 905)], [(330, 640), (318, 740), (306, 840), (300, 915)],
        [0.25, 0.6], w=0.62, t0=(0.45, 0.6), t1=(0.85, 1.0), wave=0.6, hand=0.4)
skirt = skirt_L + [(264, 909), (306, 922), (345, 926), (405, 928), (446, 926), (490, 912)] + skirt_R[::-1]
pen.occlude(R(skirt))
F([(235, 897), (264, 902), (284, 910), (306, 914), (345, 919), (375, 921), (405, 921), (446, 919), (470, 911),
   (490, 905), (501, 896)], w=0.7, hand=0.5)                         # the skirt's hem
S([(338, 929), (346, 936), (362, 939), (380, 937)], w=1.6)          # her pointed shoes
F([(345, 935), (362, 941), (379, 938)], w=0.9)
S([(424, 928), (432, 934), (448, 936), (466, 932)], w=1.5)
F([(431, 934), (448, 939), (465, 934)], w=0.85)

# ---- far off behind them, a factory: a saw-toothed shed and its chimney smoking
fx0, fx1, fy = 818, 972, 884
F([(fx0, fy), (fx1, fy)], w=0.9, hand=0.3)
F([(fx0, fy), (fx0, 864)], w=0.9)
F([(fx1, fy), (fx1, 864)], w=0.85)
teeth = [(fx0, 864)]
for k in range(7):
    x = 832 + k * 20
    teeth += [(x, 864), (x, 850), (x + 20, 864)]
pen.line(teeth[:-1] + [(fx1, 864)], w=0.85, hand=0.1, lift=0.0)
for k in range(7):
    x = 832 + k * 20
    F([(x + 2, 853), (x + 2, 862)], w=0.6, hand=0.0)                # the north lights
for x in range(826, 966, 12):
    F([(x, 872), (x, 879)], w=0.6, hand=0.0)                         # windows
tone(R([(fx0, 864), (fx1, 864), (fx1, 884), (fx0, 884)]), 0, 6.0, w=0.6, skip=0.35)
pen.occlude(R([(fx0, 849), (fx1, 849), (fx1, 885), (fx0, 885)]))
F([(888, 864), (890.5, 722)], w=1.0, hand=0.2)                      # the chimney
F([(902, 864), (899.5, 722)], w=1.0, hand=0.2)
F([(888.5, 724), (901.5, 724)], w=0.9)
F([(889, 731), (901, 731)], w=0.7)
F([(938, 850), (939, 800)], w=0.85)                                  # a smaller one
F([(946, 850), (945, 800)], w=0.85)
F([(938.5, 801), (945.5, 801)], w=0.75)
for k, (amp, y0, x1) in enumerate([(5, 718, 985), (6, 710, 975), (4, 726, 960)]):
    pts = []
    for i in range(41):
        t = i / 40
        x = 895 + (x1 - 895) * t
        y = y0 - 34 * t + amp * math.sin(t * 7 + k)
        pts.append((x, y))
    pen.line(pts, w=0.7 - 0.05 * k, hand=0.3, lift=0.25, piece=(10, 26))
for k in range(2):
    pts = [(942 + 30 * i / 20, 796 - 14 * i / 20 + 3 * math.sin(i / 3 + k)) for i in range(21)]
    pen.line(pts, w=0.62, hand=0.3, lift=0.3, piece=(8, 18))

F([(961, 849), (961.5, 806)], w=0.8)                                # the factory's flag
flag = [(962, 807), (972, 808.5), (984, 807), (984, 821), (972, 822.5), (962, 821)]
F(flag[:4], w=0.8)
F(flag[3:] + [(962, 821)], w=0.8)
for k in range(1, 4):                                                 # its stripes
    yy = 807 + k * 3.5
    F([(962, yy), (972, yy + 1.5), (984, yy)], w=0.6, hand=0.05)
hatch_keep(R([(962, 807), (970, 808.2), (970, 814.5), (962, 814)]), 45, 5.0, lambda p: True, w=0.6)

# telegraph poles running off to the left, the wires sagging between them
poles = [(48, 884, 776), (116, 884, 788), (180, 884, 798)]
for (x, yb, yt) in poles:
    F([(x, yb), (x + 0.6, yt)], w=1.0, hand=0.15)
    F([(x - 9, yt + 5), (x + 10, yt + 5)], w=0.9, hand=0.05)          # crossarm
    for dx in (-7, 8):
        F([(x + dx, yt + 5), (x + dx, yt + 2)], w=0.7)                 # insulators
for dx in (-7, 8):
    for (a, b) in zip(poles[:-1], poles[1:]):
        p0, p1 = (a[0] + dx, a[2] + 2), (b[0] + dx, b[2] + 2)
        mid = (lerp(p0, p1, 0.5)[0], lerp(p0, p1, 0.5)[1] + 5)
        pen.line(catmull([p0, mid, p1], step=2.0), w=0.6, hand=0.1, lift=0.0)
    p0 = (poles[0][0] + dx, poles[0][2] + 2)
    pen.line(catmull([p0, (p0[0] - 20, p0[1] + 4), (10, p0[1] + 2)], step=2.0), w=0.6, hand=0.1, lift=0.0)
    p0 = (poles[-1][0] + dx, poles[-1][2] + 2)
    pen.line(catmull([p0, (p0[0] + 18, p0[1] + 4), (222, p0[1] + 6)], step=2.0), w=0.6, hand=0.1, lift=0.0)

# ---- the ground: their shadows fall to the right
for (x0, x1, y) in [(470, 560, 932), (500, 590, 924), (690, 830, 940), (760, 860, 931), (520, 560, 940),
                    (180, 236, 912), (200, 245, 922), (780, 880, 948), (150, 220, 932)]:
    pen.line([(x0, y), (x1, y)], w=0.8, hand=0.5)
tone(R([(504, 905), (560, 915), (600, 925), (560, 930), (500, 930), (472, 922)]), 0, 5.5, w=0.65)
tone(R([(676, 940), (720, 935), (780, 932), (800, 938), (760, 946), (680, 947)]), 0, 5.5, w=0.65)
tone(R([(640, 950), (668, 948), (700, 951), (690, 958), (650, 958)]), 0, 5.0, w=0.65)

pen.save('../20-couple-1690s.svg', mirror=True)
pen.report()
