#!/usr/bin/env python3
"""20 - A couple of the 1690s, the time of the Amish split (1693).

Plain rural dress of the Swiss and Alsatian Anabaptists: he in a low-crowned
broad-brimmed felt hat, hair to the collar and a full untrimmed beard, a plain
collarless coat without lace or ornament over a long waistcoat, knee breeches,
stockings and plain tied shoes; she in a close white cap, a kerchief over her
shoulders, a fitted bodice and full skirt with an apron, and a basket. They
stand side by side, hand in hand, turned three-quarters to the right.

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


# ================================================================ THE MAN

# ---- joined hands (front-most). We see the back of her left hand. His right
# hand holds it: his thumb lies over the back of her hand, his fingers come
# round its lower edge, their tips (nails showing) resting on it; her fingers
# pass behind his palm and their tips curl round the far edge of his hand.
# his thumb, over the back of her hand
thumb = [(521, 559), (510, 557.5), (499, 558.5), (492, 560.5), (488, 564), (489, 568.5), (494, 570.5), (506, 571),
         (515, 573), (522, 575)]
F([(521, 559), (510, 557.5), (499, 558.5), (492, 560.5), (488, 564), (489, 568.5), (494, 570.5)], w=1.5)
F([(494, 570.5), (506, 571), (515, 573), (521, 575)], w=1.6)
F([(491, 561.5), (495.5, 561), (497, 564.5), (494, 567.5), (490.5, 567)], w=0.9)    # nail
F([(503.5, 559), (504.5, 563), (503.5, 567)], w=0.7)                                # joint
pen.occlude(R(thumb))
# his fingers round the lower edge of her hand, tips on its back
edge = [(463, 556), (468, 566), (476, 575), (486, 583), (497, 590), (509, 594), (521, 596)]
outer = [(457, 567), (464, 578), (474, 588), (486, 596), (500, 601), (515, 604), (530, 602)]
E = resample(C(edge), 0.5)
O = resample(C(outer), 0.5)
cuts = [0.22, 0.4, 0.57, 0.73, 0.86]                 # where one finger meets the next, along the edge
for k in range(4):
    t0, t1 = cuts[k], cuts[k + 1]
    tm = (t0 + t1) / 2
    e0, e1, em = E[int(t0 * (len(E) - 1))], E[int(t1 * (len(E) - 1))], E[int(tm * (len(E) - 1))]
    o0, o1, om = O[int(t0 * (len(O) - 1))], O[int(t1 * (len(O) - 1))], O[int(tm * (len(O) - 1))]
    inn = (em[0] - om[0], em[1] - om[1])
    L = math.hypot(*inn)
    u = (inn[0] / L, inn[1] / L)
    n = (-u[1], u[0])
    r = dist(e0, e1) * 0.42
    reach = 7.0 if k < 3 else 5.0
    c = (em[0] + u[0] * reach, em[1] + u[1] * reach)
    s0 = (c[0] + n[0] * r, c[1] + n[1] * r)
    s1 = (c[0] - n[0] * r, c[1] - n[1] * r)
    if dist(s0, e0) > dist(s1, e0):
        s0, s1 = s1, s0
        n = (-n[0], -n[1])
    cap = [(c[0] + n[0] * r * math.cos(q) + u[0] * r * math.sin(q), c[1] + n[1] * r * math.cos(q) + u[1] * r * math.sin(q))
           for q in [i * math.pi / 10 for i in range(11)]]
    if k == 0:
        F([lerp(o0, e0, 0.1), e0, s0], w=1.2)
    F([s0] + cap + [s1], w=1.25)
    F([s1, e1, lerp(o1, e1, 0.1)], w=1.2)
    nail = [(c[0] + n[0] * r * 0.55 * math.cos(q) + u[0] * (r * 0.55 * math.sin(q) - r * 0.15),
             c[1] + n[1] * r * 0.55 * math.cos(q) + u[1] * (r * 0.55 * math.sin(q) - r * 0.15))
            for q in [i * math.pi / 8 for i in range(9)]]
    F(nail[1:-1], w=0.7)
outer = [O[int(cuts[0] * (len(O) - 1))]] + [p_ for p_ in outer if dist(p_, outer[0]) > dist(O[int(cuts[0] * (len(O) - 1))], outer[0])]
S(outer, w=1.6, hand=0.5)
his_fingers = [E[int(cuts[0] * (len(E) - 1))]] + edge[4:] + [(533, 600)] + outer[::-1]
pen.occlude(R(his_fingers))
# her fingertips curling round the far edge of his hand
for (y0, y1) in ((563, 572), (572, 581), (581, 590)):
    F([(541, y0), (546, y0 + 1.5), (548, (y0 + y1) / 2), (546, y1 - 1), (540, y1)], w=1.2)
pen.occlude(R([(540, 563), (547, 564), (549, 576), (548, 590), (540, 590)]))
# her hand: the back from the wrist to the knuckles
her_hand = [(462, 551), (484, 546), (497, 551), (509, 557), (521, 562), (521, 590), (506, 594), (490, 585),
            (476, 573), (467, 562)]
F([(484, 546), (491, 549), (499, 553), (508, 557)], w=1.5)
F([(463, 553), (466, 561), (472, 569)], w=1.5)
for (q0, m_, q1) in (((514, 575), (517, 578), (516, 583)), ((511, 584), (514, 587), (512, 591))):
    F([q0, m_, q1], w=0.9)                                                          # her knuckles
pen.occlude(R(her_hand))
# his hand from the wrist: the thumb's root, the edge of the palm
his_hand = [(507, 556), (538, 557), (543, 570), (546, 584), (542, 596), (533, 603), (521, 596), (521, 575)]
S([(538, 557), (542, 568), (544, 582), (542, 594), (535, 601)], w=1.7)
F([(521, 575), (522, 586), (524, 594)], w=0.8)                                      # the palm's edge
F([(525, 561), (530, 570), (531, 580)], w=0.7)                                      # the thumb's root
pen.occlude(R(his_hand))

# ---- his right sleeve (near arm) with a plain turned-back cuff
cuffN = [(511, 509), (531, 514), (552, 520), (546, 540), (540, 557), (521, 553), (502, 548), (506, 528)]
S([(511, 509), (531, 514), (552, 520)], w=1.5)
S([(511, 509), (506, 528), (502, 548)], w=2.0)
S([(552, 520), (546, 540), (540, 557)], w=2.0)
S([(502, 548), (521, 553), (540, 557)], w=1.8)
F([(508, 551), (520, 557), (533, 560)], w=0.9)                  # shirt cuff
across([(511, 512), (506, 528), (503, 545)], [(551, 522), (546, 540), (540, 555)], spacing=6,
       frac=(0.3, 0.5), bow=1.5, w=0.65)
pen.occlude(R(cuffN))
sleeveN_out = [(557, 321), (547, 348), (540, 392), (536, 432), (527, 474), (514, 510)]
sleeveN_in = [(586, 352), (581, 392), (573, 432), (561, 473), (550, 517)]
S(sleeveN_out, w=2.2)
S(sleeveN_in, w=1.9)
S([(572, 436), (563, 444), (552, 456)], w=1.25)                 # elbow creases
S([(574, 451), (564, 460), (556, 467)], w=1.15)
S([(569, 467), (558, 477)], w=1.0)
S([(539, 430), (543, 441)], w=0.8)
S([(556, 338), (552, 372), (548, 400)], w=0.9)
across(sleeveN_out, sleeveN_in, spacing=6.5, frac=(0.22, 0.42), bow=2.5, w=0.7, from_b=True)
pen.occlude(R(sleeveN_out + sleeveN_in[::-1]))

# ---- his head: a natural full beard, a plain weathered face, hair under the
# hat falling to the collar, the ear showing (the brim passes behind the head).
# The face is kept a pale plane: texture only in the hair and the beard.
beard = [(652, 201), (655, 214), (662, 225), (672, 232), (682, 236), (690, 236), (700, 230), (708, 231),
         (713, 238), (715, 250), (714, 263), (711, 276), (707, 285), (702, 293), (696, 300), (692, 306),
         (686, 300), (679, 297), (668, 289), (658, 276), (651, 261), (647, 245), (648, 228), (650, 212)]
# moustache over the upper lip, and the lower lip below it
must = [(679, 247), (681, 240), (687, 235), (694, 231), (701, 229), (708, 230), (713, 235), (716, 241),
        (712, 244), (705, 240), (699, 240), (692, 242), (685, 246)]
F([(701, 229), (694, 231), (687, 235), (681, 241), (679, 247), (682, 249)], w=1.6)
F([(707, 230), (712, 234), (716, 240), (714, 244)], w=1.5)
F([(686, 245), (692, 241.5), (699, 240), (706, 241), (712, 244)], w=1.0)
for (a0, b0) in (((692, 233), (686, 241)), ((700, 232), (697, 240)), ((708, 233), (710, 240))):
    F([a0, b0], w=0.75)
pen.occlude(R(must))
F([(692, 248), (698, 250), (705, 248)], w=1.2)                     # lower lip
pen.occlude(R([(689, 246), (698, 248), (708, 246), (707, 255), (691, 255)]))


def wavy(ctrl, w=0.8, amp=1.3, wl=22.0, t0=0.0, t1=1.0, hand=0.25):
    """A hair: a smooth line through ctrl with a slow sideways wave that
    dies away at its root."""
    P = resample(C(ctrl, step=1.0), 1.0)
    ph = pen.r(0, TAU)
    out = []
    for k, p in enumerate(P):
        q = P[min(len(P) - 1, k + 1)]
        r = P[max(0, k - 1)]
        dx, dy = q[0] - r[0], q[1] - r[1]
        L = math.hypot(dx, dy) or 1
        f = min(1.0, k / 10.0)
        o = amp * f * math.sin(TAU * k / wl + ph)
        out.append((p[0] - dy / L * o, p[1] + dx / L * o))
    a, b = int(t0 * (len(out) - 1)), int(t1 * (len(out) - 1))
    if b - a > 3:
        pen.line(out[a:b + 1], w=w, hand=hand, lift=0.0)


# the beard's outline: by the ear, along the jaw in locks, an uneven point
F([(650, 232), (648, 246), (651, 260)], w=1.3, hand=0.5)
F([(651, 260), (656, 272), (662, 282), (668, 289)], w=1.5, hand=0.5)
F([(668, 289), (673, 291), (676, 295), (680, 297)], w=1.5, hand=0.5)
F([(680, 297), (685, 299), (689, 303), (692, 307)], w=1.6, hand=0.5)
F([(692, 307), (695, 301), (699, 297), (703, 293)], w=1.6, hand=0.5)
F([(703, 293), (705, 289), (708, 284)], w=1.5, hand=0.5)
S([(708, 285), (711, 276), (714, 264), (715, 251), (713, 242)], w=1.7, hand=0.6)
# its edge on the cheek: one soft broken line
pen.line(C([(652, 204), (654, 213), (660, 222), (668, 229), (677, 234), (684, 237)]), w=0.9, hand=0.4, lift=0.25,
         piece=(8, 16))
# hairs: long and wavy, parting a little below the lip
for ctrl, ww, amp, t0, t1 in [
        ([(654, 212), (652, 238), (655, 262)], 0.8, 1.0, 0.0, 1.0),
        ([(660, 224), (659, 250), (662, 277)], 0.8, 1.2, 0.05, 0.95),
        ([(667, 230), (666, 258), (670, 286)], 0.8, 1.4, 0.0, 1.0),
        ([(674, 236), (674, 262), (677, 293)], 0.85, 1.5, 0.05, 0.97),
        ([(681, 240), (681, 268), (685, 297)], 0.85, 1.5, 0.0, 1.0),
        ([(688, 252), (688, 278), (690, 303)], 0.9, 1.8, 0.0, 1.0),
        ([(694, 256), (692, 280), (692, 306)], 0.9, 1.6, 0.0, 1.0),
        ([(700, 256), (702, 276), (697, 298)], 0.85, 1.5, 0.0, 1.0),
        ([(706, 252), (708, 270), (703, 292)], 0.85, 1.3, 0.0, 0.97),
        ([(712, 246), (712, 265), (707, 284)], 0.8, 1.0, 0.0, 0.95),
        ([(664, 248), (664, 266), (667, 283)], 0.75, 1.2, 0.0, 1.0),
        ([(677, 256), (678, 276), (681, 293)], 0.75, 1.3, 0.0, 1.0),
        ([(657, 242), (656, 256), (659, 270)], 0.7, 1.0, 0.0, 1.0)]:
    wavy(ctrl, w=ww, amp=amp, t0=t0, t1=t1)
F([(697, 255), (696.5, 261), (697, 267)], w=0.8)                    # the parting
pen.occlude(R(beard))

# face: brow, nose and cheek in profile; one firm eye under a plain brow
face = [(652, 165), (672, 164), (692, 166), (695, 182), (698, 193), (694, 201), (703, 211),
        (716, 224), (708, 230), (700, 230), (690, 237), (672, 232), (652, 214), (652, 190)]
S([(692, 167), (695, 181), (698, 192)], w=1.8)
F([(698, 192), (695, 200), (697, 205), (705, 213), (712, 220), (715, 224), (714, 228), (709, 230)], w=1.7)
F([(709, 230), (704, 230), (700, 228)], w=1.3)
F([(703, 222), (698, 224), (698, 228), (702, 230)], w=1.2)       # nostril wing
F([(660, 203.5), (665.5, 200.3), (672, 199.6), (678.5, 202.5)], w=2.6)   # upper lid
F([(666, 206.5), (672, 207), (676, 205)], w=0.8)
pen.blot(671.5, 203.8, 3.0, w=2.2)
F([(689, 203), (693, 201), (698, 202.5)], w=1.6)                 # far eye
pen.blot(694.2, 203.5, 1.7, w=1.4)
F([(655, 195), (661, 191.5), (669, 190.5), (680, 193.5)], w=1.9)  # brows
F([(688, 194), (694, 192.5), (699, 193.5)], w=1.5)
pen.occlude(R(face))

# ear
ear = [(651, 199), (645, 196), (639, 201), (636, 212), (637, 223), (641, 231), (647, 233), (651, 228),
       (652, 214)]
F([(651, 199), (645, 196), (639, 201), (636, 212), (637, 223), (641, 231), (647, 233), (650, 229)], w=1.5)
F([(646, 202), (641, 207), (641, 217), (644, 223)], w=0.9)       # inner rim
pen.occlude(R(ear))

# hair under the hat, combed back over the ear and falling to the collar
hair_back = [(608, 176), (601, 200), (600, 226), (603, 252), (610, 274), (620, 292), (632, 302)]
hair_front = [(656, 170), (654, 186), (650, 196), (638, 210), (638, 232), (645, 252), (652, 270), (660, 290)]
hair = [(608, 170), (630, 166), (656, 166), (654, 186), (650, 196), (638, 210), (638, 232), (645, 252),
        (652, 270), (661, 292), (650, 300), (640, 304), (632, 303), (620, 292), (610, 274), (603, 252),
        (600, 226), (601, 200)]
S([(608, 176), (602, 196), (601, 216)], w=1.9, hand=0.8)
S([(603, 210), (600, 230), (603, 250), (608, 266)], w=1.9, hand=0.8)
S([(605, 260), (611, 278), (620, 292), (630, 301)], w=1.8, hand=0.8)
F([(630, 301), (636, 306), (642, 301), (648, 305), (654, 298), (661, 296)], w=1.3, hand=0.5)
F([(612, 280), (615, 292)], w=0.9)
F([(622, 291), (626, 300)], w=0.9)
strands(hair_back, hair_front, [0.08 + 0.84 * k / 8 + pen.g(0.02) for k in range(9)], w=0.8,
        t0=(0.0, 0.1), t1=(0.75, 1.0), wave=2.6)
strands(hair_back, hair_front, [0.04, 0.12, 0.2], w=0.75, t0=(0.3, 0.5), t1=(0.85, 1.0), wave=2.2)
# hair over the temple, swept back above the ear
for k in range(2):
    y0 = 178 + k * 8
    F([(654 - k, y0), (646 - k, y0 + 6), (636 - k * 2, y0 + 14)], w=0.75)
pen.occlude(hair)
# the shirt's plain collar showing between hair and beard
F([(632, 303), (645, 306), (660, 303), (670, 300)], w=1.1)
pen.occlude(R([(630, 300), (670, 296), (672, 306), (632, 308)]))

# ---- hat: broad brim seen a little from below, with a slight wave in it
# (up at the sides, down at front and back); low round crown, creased on top,
# a plain band stitched along both edges
bcx, bcy, brx, bry, brot = 656, 167, 118, 13, -0.025


def brim_pts(a0, a1, drx=0.0, dcy=0.0, step=2.0):
    out = []
    for (x, y) in ellipse_pts(bcx, bcy + dcy, brx + drx, bry, brot, a0, a1, step=step):
        th = math.atan2((y - bcy - dcy) / bry, (x - bcx) / (brx + drx))
        out.append((x, y - 3.4 * math.cos(2 * th) + 1.0 * math.sin(3 * th + 0.7)))
    return out


brim = brim_pts(0, TAU)
pen.line(brim_pts(0.02, math.pi - 0.02), w=1.7, hand=0.6)
tone(R([(540, 163), (580, 171), (612, 176), (612, 168), (580, 160), (545, 157)]), 80, 5.5, w=0.65)
tone(R([(702, 170), (740, 168), (772, 162), (772, 156), (740, 160), (702, 161)]), 80, 5.5, w=0.65)
pen.line(brim_pts(math.pi - 0.03, TAU + 0.03), w=2.3, hand=0.6)
pen.line(brim_pts(math.pi + 0.35, TAU - 0.35, drx=-3, dcy=-3.2), w=1.0, hand=0.4)
pen.occlude(brim)
crown = [(610, 157), (609, 140), (612, 127), (622, 119), (641, 115), (660, 114), (679, 115), (692, 118),
         (700, 126), (704, 139), (702, 157)]
S(crown[:5], w=2.2)
S(crown[3:9], w=2.2)
S(crown[7:], w=2.2)
F([(628, 121), (640, 125), (654, 127), (668, 125), (681, 120)], w=1.2, hand=0.4)   # the crease on top
F([(646, 128), (657, 130), (667, 128)], w=0.7)
band_t = [(609, 142), (632, 138), (657, 137), (682, 138), (703, 142)]
band_b = [(609, 155), (632, 151), (657, 150), (682, 151), (703, 155)]
S(band_t, w=1.4)
S(band_b, w=1.2)
for rail, d in ((band_t, 2.6), (band_b, -2.6)):                  # stitching
    P = resample(C([(x, y + d) for x, y in rail]), 1.0)
    for k in range(2, len(P) - 4, 6):
        pen.line(P[k:k + 4], w=0.8, hand=0.0, lift=0.0)
across([(668, 120), (674, 128), (676, 136)], [(693, 119), (701, 127), (703, 137)], spacing=5.5,
       frac=(0.45, 0.85), bow=-1.2, w=0.65)
tone(R([(668, 146), (684, 147), (703, 151), (703, 147), (684, 143), (668, 142)]), 75, 5.0, w=0.6)
across([(618, 122), (614, 130), (612, 137)], [(636, 117), (632, 127), (630, 137)], spacing=7,
       frac=(0.1, 0.3), bow=-1, w=0.6, from_b=False)
pen.occlude(R(crown))

# ---- his left hand and sleeve (far arm), hanging relaxed beside the coat
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
cuffF = [(752, 528), (770, 529), (789, 531), (791, 547), (790, 562), (771, 562), (754, 561), (753, 545)]
S([(752, 528), (770, 529), (789, 531)], w=1.5)
S([(789, 531), (791, 547), (790, 562)], w=2.0)
S([(790, 562), (771, 562), (754, 561)], w=1.6)
S([(754, 561), (753, 545), (752, 528)], w=1.8)
F([(759, 563), (771, 566), (783, 565)], w=0.8)
across([(752, 531), (753, 545), (754, 559)], [(789, 533), (791, 547), (790, 560)], spacing=6,
       frac=(0.5, 0.8), bow=1.5, w=0.65)
pen.occlude(R(cuffF))

# ---- the coat: closed to the waist on hooks, its skirts parting below
coat_upper = [(626, 300), (600, 305), (575, 312), (557, 322), (560, 360), (575, 400), (588, 440),
              (590, 470), (742, 470), (741, 420), (738, 360), (743, 322), (726, 305), (708, 299),
              (690, 312)]
sleeveF_out = [(744, 321), (759, 350), (769, 398), (776, 450), (783, 498), (788, 530)]
sleeveF_in = [(734, 380), (742, 430), (748, 480), (752, 530)]
S([(628, 302), (600, 306), (576, 313), (557, 322)], w=2.1)        # shoulders
S([(701, 306), (712, 301), (727, 305), (744, 321)], w=2.0)
F([(632, 304), (646, 310), (660, 312), (672, 313)], w=1.2, hand=0.6)   # neckline
coat_front_top = [(676, 314), (673, 360), (674, 410), (677, 470)]
S(coat_front_top, w=1.6)
for y in range(328, 468, 16):                                      # hooks and eyes down the front
    x = 673 + (y - 314) * 0.024
    F([(x - 6, y), (x + 1, y - 0.3), (x + 3.5, y + 1.6), (x + 1.5, y + 3)], w=1.3)
    F([(x + 3, y + 4.5), (x + 7, y + 4)], w=1.0)
S([(560, 323), (569, 331), (579, 341), (586, 352)], w=0.9)         # armhole seam
S([(588, 360), (591, 410), (594, 484)], w=1.15)                    # side-front seam
S([(729, 307), (735, 324), (737, 344)], w=0.85)
S([(722, 312), (724, 350), (727, 400), (729, 450)], w=1.15)
S([(592, 372), (612, 396), (636, 418), (658, 432)], w=0.9)         # pulled by the reaching arm
S([(594, 398), (614, 420), (634, 440)], w=0.8)
ticks([(592, 372), (612, 396), (636, 418), (658, 432)], ang=100, spacing=6, maxlen=8, w=0.6, t0=0.1, t1=0.9)
S([(642, 458), (656, 462), (668, 461)], w=0.8)                     # creasing at the waist
S([(741, 340), (738, 380), (740, 425), (742, 470)], w=2.0)
# shading: the far front in shadow, the hollow below the beard, under the arm
strands([(682, 318), (678, 380), (681, 468)], [(738, 320), (737, 390), (741, 468)],
        [0.5, 0.6, 0.7, 0.8, 0.9], w=0.7, t0=(0.0, 0.2), t1=(0.6, 0.95), wave=0.8, hand=0.4)
ticks(coat_front_top, ang=150, spacing=6, maxlen=14, w=0.65, t0=0.05, t1=0.95)
tone(R([(612, 314), (640, 312), (660, 316), (672, 318), (670, 334), (640, 334), (614, 328)]), 62, 6.5, w=0.65,
     skip=0.15)
ticks([(588, 360), (589, 410), (590, 465)], ang=-15, spacing=6.5, maxlen=14, w=0.65)
pen.occlude(R(coat_upper))
S(sleeveF_out, w=2.1)
S(sleeveF_in, w=1.8)
across(sleeveF_in, sleeveF_out, spacing=6.5, frac=(0.45, 0.75), bow=2, w=0.65, from_b=True)
S([(766, 410), (770, 440)], w=0.8)
S([(752, 340), (761, 380), (767, 420)], w=0.8)                      # sleeve seam
S([(749, 458), (759, 465), (767, 477)], w=1.25)                     # elbow creases
S([(751, 476), (760, 484), (765, 492)], w=1.1)
S([(770, 440), (776, 452)], w=1.0)
pen.occlude(R(sleeveF_out + sleeveF_in[::-1]))

# coat skirts, to the knee
near_skirt = [(590, 468), (586, 515), (571, 590), (558, 660), (546, 710), (582, 716), (620, 718),
              (654, 714), (659, 640), (667, 556), (677, 472)]
far_skirt = [(681, 472), (695, 556), (707, 640), (715, 709), (745, 707), (779, 700), (767, 625),
             (756, 560), (746, 505), (742, 470)]
S([(590, 466), (586, 515), (572, 590), (559, 660), (546, 710)], w=2.1)
S([(546, 710), (566, 714), (590, 717), (620, 719), (654, 715)], w=2.0)
S([(677, 472), (667, 556), (659, 640), (654, 715)], w=1.8)
S([(681, 472), (695, 556), (707, 640), (715, 709)], w=1.8)
S([(687, 486), (700, 556), (712, 640), (719, 704)], w=0.9)          # its facing
S([(715, 709), (745, 708), (779, 701)], w=2.0)
S([(742, 468), (746, 505), (756, 560), (767, 625), (779, 701)], w=2.1)
S([(588, 545), (612, 547), (640, 545)], w=1.4)                     # pocket flaps
S([(588, 545), (587, 557), (612, 563), (639, 559), (640, 545)], w=1.4)
S([(712, 542), (728, 541), (746, 539)], w=1.3)
S([(713, 542), (714, 554), (731, 556), (747, 551)], w=1.3)
pleats_n = [[(594, 484), (586, 550), (575, 630), (566, 713)],
            [(607, 575), (604, 650), (601, 717)]]
for pl in pleats_n:
    S(pl, w=1.1)
ticks(pleats_n[0], ang=10, spacing=6, maxlen=12, w=0.65, t0=0.15, t1=0.98)
ticks(pleats_n[1], ang=10, spacing=6, maxlen=10, w=0.65, t0=0.1, t1=0.98)
S([(733, 488), (738, 560), (746, 640), (751, 708)], w=1.0)
F([(550, 704), (590, 711), (620, 713), (651, 709)], w=0.7, hand=0.5)        # hem stitching
F([(718, 703), (745, 702), (776, 696)], w=0.7, hand=0.5)
S([(636, 580), (641, 640), (640, 700)], w=0.9)                             # over the thigh
ticks([(636, 580), (641, 640), (640, 700)], ang=0, spacing=6, maxlen=7, w=0.6, t0=0.1, t1=0.9)
for rail in ([(591, 549), (591, 555), (612, 559.5), (636.5, 556), (637, 549)], [(716, 545.5), (717, 551), (731, 552.5), (744, 548)]):
    P = resample(C(rail), 1.0)                                              # flap stitching
    for k in range(1, len(P) - 3, 5):
        pen.line(P[k:k + 3], w=0.85, hand=0.0, lift=0.0)
strands([(684, 476), (697, 556), (709, 640), (716, 706)], [(743, 472), (755, 560), (767, 630), (778, 700)],
        [0.22, 0.36, 0.5, 0.62, 0.74, 0.86], w=0.7, t0=(0.0, 0.25), t1=(0.7, 1.0), wave=1.0, hand=0.4)
ticks([(677, 474), (667, 556), (659, 640), (655, 713)], ang=180, spacing=6.5, maxlen=16, w=0.65, t0=0.0, t1=1.0,
      prof=lambda u: 5 + 10 * u)
tone(R([(560, 670), (600, 682), (652, 682), (654, 714), (620, 718), (582, 716), (546, 710)]), 62, 7.5, w=0.65,
     skip=0.2)
pen.occlude(R(near_skirt))
pen.occlude(R(far_skirt))

# the waistcoat in the opening, ending a little above the coat's hem; breeches below
S([(679, 476), (682, 560), (684, 640), (685, 692)], w=1.1)                  # its closing
for y in range(496, 684, 20):
    x = 679 + (y - 476) * 0.028
    pen.ellipse(x + 4, y, 2.2, 2.0, w=0.9, hand=0.0, lift=0.0)
S([(658, 684), (670, 689), (685, 693), (699, 689), (712, 682)], w=1.4)      # its hem
ticks([(678, 476), (668, 556), (660, 640), (657, 684)], ang=0, spacing=6, maxlen=6, w=0.6, t0=0.02, t1=0.98)
ticks([(681, 474), (695, 556), (707, 640), (712, 682)], ang=180, spacing=6, maxlen=8, w=0.6, t0=0.02, t1=0.98)
tone(R([(684, 640), (707, 640), (712, 682), (699, 689), (685, 693)]), 115, 7.0, w=0.6)
S([(684, 695), (683, 705), (681, 716)], w=1.1)
tone(R([(657, 686), (670, 691), (685, 695), (712, 684), (715, 709), (680, 718), (655, 714)]), 68, 5.5, w=0.65)
pen.occlude(R([(677, 472), (681, 472), (712, 682), (715, 709), (655, 714), (660, 640)]))


def buckle(cx, cy, ang, bw, bh):
    """A plain square buckle on the shoe's latchets: frame and pin."""
    a = math.radians(ang)
    d, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))

    def P(s_, t_):
        return (cx + d[0] * s_ + n[0] * t_, cy + d[1] * s_ + n[1] * t_)
    box = [P(-bw / 2, -bh / 2), P(bw / 2, -bh / 2), P(bw / 2, bh / 2), P(-bw / 2, bh / 2)]
    pen.line(box + [box[0], box[1]], w=1.35, hand=0.0, lift=0.0)
    pen.line([P(0, -bh / 2), P(0, bh / 2)], w=0.9, hand=0.0, lift=0.0)
    pen.occlude(box)


# ---- legs: breeches below the coat, knee bands, stockings, plain tied shoes
# the near foot turned out a little toward us
shoeN = [(608, 899), (602, 912), (601, 926), (600, 938), (616, 943), (639, 947), (658, 954), (669, 955),
         (673, 945), (667, 937), (652, 926), (641, 915), (641, 898), (635, 891), (628, 894), (616, 904)]
S([(608, 899), (602, 912), (601, 926)], w=2.0)                            # heel of the upper
S([(601, 926), (600, 938), (616, 943), (618, 934)], w=1.8)                # heel block
S([(617, 936), (639, 946), (658, 953), (669, 955)], w=2.0)                # sole
S([(669, 955), (673, 945), (667, 937)], w=2.0)                            # square toe
S([(667, 937), (652, 926), (641, 915)], w=1.8)                            # vamp
S([(641, 915), (641, 902), (641, 895), (635, 890), (629, 893), (627, 902)], w=1.5)   # tongue
S([(627, 902), (617, 905), (608, 899)], w=1.5)                            # topline
S([(619, 931), (640, 939.5), (659, 946.5), (670, 949)], w=1.25)          # the sole's edge
S([(652, 925), (648.5, 933), (647, 943)], w=1.1)                          # seam over the toe
S([(619, 905), (630, 908), (640, 913)], w=1.1)                            # latchets
buckle(631, 908.5, 21, 10, 7)
tone(R([(617, 912), (641, 919), (654, 929), (666, 939), (670, 945), (659, 945), (640, 938), (620, 929)]), 30, 6.5,
     w=0.65, skip=0.2)
pen.occlude(R(shoeN))
shoeF = [(692, 897), (688, 910), (690, 922), (692, 931), (708, 932), (730, 930), (752, 932), (764, 930),
         (766, 922), (758, 915), (742, 908), (730, 900), (727, 886), (720, 882), (713, 886), (701, 897)]
S([(692, 897), (688, 910), (690, 922)], w=1.9)
S([(690, 922), (692, 931), (708, 932), (708, 924)], w=1.7)
S([(708, 926), (730, 929), (752, 932), (764, 930)], w=1.9)
S([(764, 930), (766, 922), (758, 915)], w=1.9)
S([(758, 915), (742, 908), (730, 900)], w=1.7)
S([(730, 900), (728, 890), (726, 884), (719, 882), (713, 886), (713, 895)], w=1.4)
S([(713, 895), (702, 898), (692, 897)], w=1.4)
S([(710, 924.5), (732, 926.5), (752, 928.5), (764, 927.5)], w=1.2)        # the sole's edge
S([(745, 908.5), (742, 916), (741, 925)], w=1.05)                          # seam over the toe
S([(704, 899), (716, 898), (729, 902)], w=1.0)
buckle(718, 899.5, 5, 9, 6.5)
tone(R([(703, 904), (730, 905), (744, 911), (760, 918), (765, 924), (752, 926), (730, 923), (710, 920)]), 30, 6.5,
     w=0.65, skip=0.2)
pen.occlude(R(shoeF))

S([(590, 716), (591, 730), (594, 742)], w=1.9)                    # near leg: breeches, band
S([(651, 716), (649, 730), (646, 742)], w=1.8)
S([(593, 731), (620, 734), (648, 731)], w=1.1)
S([(594, 742), (620, 745), (646, 742)], w=1.5)
F([(594, 736), (589, 745), (586, 757)], w=0.9)
for y in (719, 726):
    pen.ellipse(596, y, 1.8, 1.8, w=0.8, hand=0.0, lift=0.0)
    pen.ellipse(725, y - 3, 1.6, 1.8, w=0.8, hand=0.0, lift=0.0)
F([(594, 737), (592, 752)], w=0.9)
S([(676, 718), (676, 730), (678, 740)], w=1.8)                    # far leg
S([(729, 709), (731, 726), (728, 740)], w=1.9)
S([(677, 729), (703, 731), (730, 728)], w=1.1)
S([(678, 740), (703, 743), (728, 740)], w=1.5)
tone(R([(622, 718), (651, 716), (649, 731), (624, 734)]), 62, 6, w=0.6)
tone(R([(700, 712), (729, 709), (730, 727), (703, 730)]), 62, 6, w=0.6)
pen.occlude(R([(590, 716), (651, 716), (646, 744), (594, 744)]))
pen.occlude(R([(676, 712), (730, 708), (728, 742), (678, 742)]))

legN_back = [(595, 744), (586, 770), (585, 800), (593, 842), (603, 880), (607, 904)]
legN_front = [(646, 744), (648, 770), (644, 810), (637, 858), (632, 904)]
legF_back = [(678, 742), (671, 768), (673, 800), (683, 845), (690, 882), (693, 898)]
legF_front = [(728, 742), (733, 768), (732, 796), (725, 836), (718, 868), (714, 898)]
S(legN_back, w=2.1)
S(legN_front, w=1.9)
S(legF_back, w=1.9)
S(legF_front, w=2.0)
across(legN_back, legN_front, spacing=7.0, frac=(0.28, 0.45), bow=3, w=0.65, t0=0.05, t1=0.97)
across(legF_back, legF_front, spacing=7.0, frac=(0.42, 0.62), bow=3, w=0.65, t0=0.05, t1=0.97)
tone(R([(678, 743), (728, 743), (727, 766), (675, 764)]), 62, 6.5, w=0.6)
F([(611, 885), (615, 892)], w=0.8)                                 # ankle bones
F([(606, 878), (616, 882), (628, 879)], w=0.7)                     # stockings wrinkling
F([(608, 889), (618, 893), (630, 890)], w=0.7)
F([(693, 875), (703, 879), (714, 876)], w=0.7)
F([(694, 886), (704, 889), (713, 887)], w=0.7)
F([(709, 878), (712, 885)], w=0.8)
pen.occlude(R(legN_back + legN_front[::-1]))
pen.occlude(R(legF_back + legF_front[::-1]))


# ================================================================ THE WOMAN

# ---- her right hand gripping the basket's handle: the back of the hand, the
# knuckles, four fingers curled down round the handle, the thumb over it
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

# ---- the basket, a cloth over what it carries
bx, by = 272, 652
rim_rx, rim_ry = 70, 15
handle_o = [(203, 652), (207, 625), (225, 604), (250, 594), (272, 592), (296, 594), (318, 604), (334, 625), (341, 652)]
handle_i = [(212, 652), (216, 628), (231, 612), (252, 602), (272, 600), (293, 602), (312, 612), (326, 628), (332, 652)]
cloth_top = [(212, 650), (221, 635), (239, 625), (262, 620), (286, 621), (308, 627), (326, 638), (333, 650)]
cloth_hem = [(329, 655), (318, 664), (302, 672), (290, 676), (276, 668), (262, 671), (250, 676), (238, 668), (228, 655)]
S(cloth_top, w=1.6)
S(cloth_hem[::-1], w=1.4)
F([(250, 676), (252, 662), (256, 648)], w=0.8)
F([(290, 676), (288, 660), (284, 646)], w=0.8)
F([(238, 640), (252, 634), (268, 632)], w=0.7)
ticks([(262, 624), (286, 625), (308, 632), (325, 645)], ang=100, spacing=5.5, maxlen=10, w=0.6, t0=0.3, t1=0.95)
ticks([(256, 650), (252, 662), (250, 674)], ang=0, spacing=5, maxlen=8, w=0.55)
ticks([(284, 646), (288, 660), (290, 674)], ang=0, spacing=5, maxlen=10, w=0.55)
pen.occlude(R(cloth_top + cloth_hem))
S(handle_o, w=1.7)
S(handle_i, w=1.3)
# the handle is a twisted withy: slanting turns all along it
HA = resample(C(handle_o), 1.0)
HB = resample(C(handle_i), 1.0)
nturn = 15
for k in range(1, nturn):
    t = k / nturn
    ta = min(1.0, t + 0.012)
    pa, pb = HA[int(ta * (len(HA) - 1))], HB[int(max(0.0, t - 0.012) * (len(HB) - 1))]
    F([lerp(pa, pb, 0.08), lerp(pa, pb, 0.92)], w=0.65)
pen.occlude(R(handle_o + handle_i[::-1]))
rim = ellipse_pts(bx, by, rim_rx, rim_ry, 0.0, 0, TAU, step=2.0)
pen.line(ellipse_pts(bx, by, rim_rx, rim_ry, 0, -0.05, math.pi + 0.05, step=2.0), w=2.0, hand=0.5)
pen.line(ellipse_pts(bx, by + 7, rim_rx - 1, rim_ry, 0, 0.05, math.pi - 0.05, step=2.0), w=1.4, hand=0.5)
# the rim bound with a withy: wraps slanting round the rim band
for k in range(1, 16):
    a = 0.1 + (math.pi - 0.2) * k / 16
    p0 = (bx + rim_rx * math.cos(a + 0.07), by + rim_ry * math.sin(a + 0.07))
    p1 = (bx + (rim_rx - 1) * math.cos(a - 0.07), by + 7 + rim_ry * math.sin(a - 0.07))
    F([lerp(p0, p1, 0.05), lerp(p0, p1, 0.95)], w=0.95)
bot_rx, bot_ry, bot_y = 54, 11, 716
S([(bx - rim_rx + 1, by + 4), (bx - 66, by + 25), (bx - 60, by + 48), (bx - bot_rx, bot_y)], w=2.0)
S([(bx + rim_rx - 1, by + 4), (bx + 67, by + 25), (bx + 61, by + 48), (bx + bot_rx, bot_y)], w=2.0)
pen.line(ellipse_pts(bx, bot_y, bot_rx, bot_ry, 0, 0.0, math.pi, step=2.0), w=2.0, hand=0.5)
pen.line(ellipse_pts(bx, bot_y - 5, bot_rx + 2, bot_ry, 0, 0.12, math.pi - 0.12, step=2.0), w=0.9, hand=0.3)


def wall(a, f):
    """A point on the basket's front wall: angle a round it, f from rim band (0) to foot (1)."""
    y0, rx0, ry0 = by + 8, rim_rx - 1, rim_ry
    y1, rx1, ry1 = bot_y - 5, bot_rx + 2, bot_ry
    yy, ry = y0 + (y1 - y0) * f, ry0 + (ry1 - ry0) * f
    rx = rx0 + (rx1 - rx0) * f + 4 * math.sin(math.pi * f)
    return (bx + rx * math.cos(a), yy + ry * math.sin(a))


# stakes: upright rods from the rim to the foot
stakes = [math.pi / 2 + j * 0.26 for j in range(-5, 6)]
for j, a in enumerate(stakes):
    pen.line(C([wall(a, f) for f in (0.0, 0.35, 0.7, 1.0)]), w=1.05 if abs(j - 5) < 4 else 0.9, hand=0.2, lift=0.0)
# weavers: rows passing in front of and behind the stakes, so each row waves
for r in range(6):
    f = (r + 0.6) / 6.2
    pts = []
    for i in range(121):
        a = 0.05 + (math.pi - 0.1) * i / 120
        q = wall(a, f)
        ph = (a - stakes[0]) / 0.26 * math.pi + r * math.pi
        pts.append((q[0], q[1] + 1.3 * math.sin(ph)))
    pen.line(pts, w=0.8, hand=0.2, lift=0.0)
pen.occlude(R(rim[::4]))
pen.occlude([(bx - rim_rx, by), (bx + rim_rx, by), (bx + 67, by + 25), (bx + 61, by + 48)] +
            ellipse_pts(bx, bot_y, bot_rx, bot_ry, 0, 0, math.pi, step=4.0) + [(bx - 60, by + 48), (bx - 66, by + 25)])

# ---- her sleeves
cuffW = [(263, 546), (293, 549), (291, 564), (263, 563)]
S([(263, 546), (278, 549), (294, 549)], w=1.6)                      # her cuff, turned back
S([(264, 552), (278, 554.5), (292, 554)], w=0.9)
S([(263, 563.5), (277, 566), (291, 565)], w=1.6)
S([(263, 546), (263, 556), (263.5, 563)], w=1.5)
S([(293, 549), (292, 557), (291, 565)], w=1.5)
tone(R([(279, 555), (292, 555), (291, 564), (279, 565)]), 75, 5.0, w=0.6)
pen.occlude(R(cuffW))
sleeveW_out = [(298, 360), (285, 392), (278, 434), (272, 482), (268, 526), (265, 563)]
sleeveW_in = [(318, 384), (311, 430), (304, 470), (297, 515), (290, 564)]
S(sleeveW_out, w=2.1)
S(sleeveW_in, w=1.8)
S([(304, 466), (297, 472), (292, 482)], w=0.9)
S([(291, 380), (284, 430), (278, 490), (274, 540)], w=0.75)         # sleeve seam
S([(300, 480), (294, 488)], w=0.8)
S([(296, 496), (289, 502)], w=0.8)
S([(275, 456), (279, 466)], w=0.8)
across(sleeveW_out, sleeveW_in, spacing=6.5, frac=(0.25, 0.45), bow=2.5, w=0.65, from_b=True)
pen.occlude(R(sleeveW_out + sleeveW_in[::-1]))
cuffW2 = [(454, 535), (482, 528), (487, 545), (459, 551)]
S([(454, 535), (468, 531.5), (482, 528)], w=1.6)
S([(456, 541), (470, 537.5), (484, 534.5)], w=0.9)
S([(459, 551), (473, 548.5), (487, 545)], w=1.6)
S([(482, 528), (485, 537), (487, 545)], w=1.7)
S([(454, 535), (456, 543), (459, 551)], w=1.4)
pen.occlude(R(cuffW2))
sleeveW2_out = [(436, 352), (446, 386), (453, 430), (462, 478), (472, 512), (482, 531)]
sleeveW2_in = [(428, 432), (436, 470), (446, 505), (456, 536)]
S(sleeveW2_out, w=2.1)
S(sleeveW2_in, w=1.8)
across(sleeveW2_in, sleeveW2_out, spacing=6.5, frac=(0.45, 0.75), bow=2.5, w=0.65, from_b=True)
S([(448, 470), (442, 478)], w=0.8)
S([(452, 482), (444, 490)], w=0.8)                                  # elbow creases
S([(455, 495), (448, 502)], w=0.7)
S([(437, 370), (447, 405), (453, 440), (457, 466)], w=0.9)          # pull toward his hand
ticks([(437, 370), (447, 405), (453, 440), (457, 466)], ang=15, spacing=6, maxlen=7, w=0.6, t0=0.1, t1=0.9)
pen.occlude(R(sleeveW2_out + [(456, 536), (446, 505), (436, 470), (428, 432), (430, 380)]))

# ---- her head: the face, the ties of her cap, then the close pleated cap
# the cap's strings hang loose from under her jaw over the kerchief
for (top, bot, sway) in [((351, 297), (346, 372), 2.0), ((392, 305), (394, 360), -1.5)]:
    mid = (lerp(top, bot, 0.5)[0] + sway, lerp(top, bot, 0.5)[1])
    rib = C([top, mid, bot])
    F(rib, w=0.95)
    F(offset(rib, 2.6), w=0.85)
    pen.occlude(rib + offset(rib, 2.6)[::-1])
# face: far contour from the temple over the brow, the nose, lips and chin
F([(405, 229), (406, 239), (407, 244)], w=1.6)
F([(407, 244), (404, 251), (405, 254), (409, 260), (412, 265), (412.5, 268), (410, 270), (407, 271), (404, 270)],
  w=1.5)
F([(406, 263), (402, 264), (400, 268), (403, 271)], w=1.0)              # nostril wing
F([(408, 272), (406, 276), (407, 280)], w=1.1)                          # upper lip, in profile
F([(407, 280), (405, 283), (407, 286), (404, 290)], w=1.2)              # the lips' fronts
F([(391, 284), (396, 284.5), (401, 284.5), (405, 283.5)], w=1.3)        # mouth
F([(389, 282.5), (390, 285.5)], w=0.7)                                  # its corner
F([(395, 289.5), (398.5, 291.8), (402, 291.5), (404.5, 289.5)], w=1.1)  # a full lower lip
F([(404, 274), (403, 279)], w=0.6)                                      # philtrum
F([(404, 290), (402, 296), (398, 301), (391, 304), (384, 304)], w=1.6)  # chin
F([(384, 304), (374, 301), (364, 295), (357, 289)], w=1.4)              # jaw
# eyes: lids, lashes, irises
F([(372, 252), (376, 248), (382, 247), (388, 250)], w=1.5)
F([(374, 246), (380, 244), (387, 246)], w=0.65)                         # lid crease
F([(375, 254), (381, 255), (387, 252)], w=0.7)
for (x0, y0) in ((373, 251), (375, 249), (377.5, 247.5)):
    F([(x0, y0), (x0 - 2.5, y0 - 2)], w=0.6)                            # lashes
pen.blot(383.5, 250.6, 2.0, w=1.3)
F([(397, 251), (401, 248), (405, 250)], w=1.3)
F([(399, 253), (403, 253)], w=0.6)
pen.blot(401.5, 250.5, 1.4, w=1.1)
F([(368, 245), (373, 241.5), (380, 239.8), (386, 240.5), (391, 243)], w=1.6)   # brows, clearly arched
F([(397.5, 243.5), (401, 241.5), (405, 242)], w=1.3)
S([(389, 305), (388, 316)], w=1.4)                                      # neck
S([(358, 296), (357, 313)], w=1.5)
ticks([(359, 298), (358, 312)], ang=0, spacing=5, maxlen=10, w=0.6)
ticks([(386, 306), (378, 304), (368, 300)], ang=95, spacing=5, maxlen=6, w=0.6, minlen=2)
# hair under the cap's edge, parted and drawn back to the temples
F([(374, 231), (385, 227), (394, 225), (405, 229)], w=1.0)
for k in range(4):
    F([(393 - k * 0.5, 223 + k * 0.5), (385 - k * 3, 226 + k * 1.5), (375 - k * 2, 231 + k)], w=0.65)
F([(395, 223), (400, 226), (405, 229)], w=0.7)
F([(366, 236), (364, 244), (366, 252)], w=0.7)                          # a strand at the temple
pen.occlude(R([(372, 224), (405, 228), (407, 244), (414, 267), (403, 290), (386, 306), (388, 312), (357, 311),
               (356, 290), (352, 270), (358, 245)]))
# cap: close linen, its front band finely pleated, its crown drawn into pleats
cap_front = [(352, 300), (350, 280), (352, 258), (359, 240), (371, 226), (389, 219), (404, 222), (409, 230)]
cap_band = [(345, 297), (343, 276), (346, 254), (353, 235), (366, 219), (386, 210), (403, 212), (410, 221)]
cap_back = [(410, 221), (402, 210), (386, 201), (365, 197), (344, 201), (328, 211), (319, 228), (316, 248),
            (319, 268), (327, 284), (339, 295), (352, 300)]
S(cap_front, w=1.5)
S(cap_band, w=1.2)
S(cap_back, w=1.9)
A = resample(C(cap_front), 1.0)
B = resample(C(cap_band), 1.0)
for k in range(1, 16):
    t = k / 16
    pa, pb = A[int(t * (len(A) - 1))], B[int(t * (len(B) - 1))]
    F([lerp(pa, pb, 0.15), lerp(pa, pb, 0.85)], w=0.6)
# pleats fanning from the nape to the band
focus = (338, 290)
Bb = resample(C(cap_back[:8]), 1.0)
for k in range(9):
    t = 0.04 + 0.92 * k / 8
    tgt = Bb[int((1 - t) * (len(Bb) - 1))]
    p0 = lerp(focus, tgt, 0.18)
    p1 = lerp(focus, tgt, 0.9)
    m = lerp(p0, p1, 0.5)
    d = (p1[0] - p0[0], p1[1] - p0[1])
    L = math.hypot(*d) or 1
    bow = 3.0
    F(catmull([p0, (m[0] + d[1] / L * bow, m[1] - d[0] / L * bow), p1], step=2.0), w=0.85)
    if k % 2 == 0 and k < 8:
        ticks([lerp(p0, p1, 0.1), (m[0] + d[1] / L * bow, m[1] - d[0] / L * bow), lerp(p0, p1, 0.85)],
              ang=math.degrees(math.atan2(d[1], d[0])) + 70, spacing=5.5, maxlen=4, w=0.6, minlen=1.5)
F([(331, 284), (338, 290), (345, 292)], w=1.0)                          # where the pleats are drawn in
F([(339, 287), (332, 268), (330, 246), (336, 224), (350, 208), (369, 200)], w=1.1, hand=0.4)   # the back seam
ticks([(319, 262), (326, 282), (339, 294), (350, 299)], ang=-60, spacing=5.5, maxlen=7, w=0.6)
pen.occlude(R(cap_back + cap_band[::-1]))

# ---- kerchief over her shoulders, pinned at the throat, tucked in front
kerchief = [(352, 311), (330, 316), (312, 326), (300, 341), (296, 358), (299, 372), (306, 381), (332, 395),
            (358, 411), (382, 428), (394, 444), (404, 418), (420, 390), (435, 368), (437, 352), (432, 336),
            (418, 323), (393, 315)]
S([(352, 311), (330, 316), (312, 326), (300, 341), (296, 358), (299, 372), (306, 381)], w=2.0)
S([(306, 381), (332, 395), (358, 411), (382, 428), (394, 444)], w=1.7)
S([(394, 444), (404, 418), (420, 390), (435, 366)], w=1.7)
S([(392, 315), (418, 323), (432, 336), (437, 352), (435, 368)], w=2.0)
F([(356, 313), (366, 318), (377, 320), (389, 315)], w=1.4)          # its folded edge round the neck
F([(352, 316), (364, 323), (378, 325.5), (392, 320)], w=1.0)
F([(306, 377), (300, 368), (299, 357)], w=0.9)                       # the fold over the shoulder
S([(381, 320), (386, 337), (390, 354)], w=1.2)                      # the near end over the far
F([(372, 334.5), (394, 326)], w=1.2)                                # a straight pin
pen.blot(371, 335, 2.3, w=1.3)
S([(346, 318), (326, 342), (312, 370)], w=0.9)                      # folds from the neck
S([(364, 322), (352, 356), (344, 392)], w=0.9)
S([(404, 322), (413, 342), (417, 364)], w=0.9)
S([(421, 327), (429, 341), (431, 358)], w=0.8)                      # over the far shoulder
S([(334, 318), (318, 333), (308, 352)], w=0.8)                      # over the near shoulder
F([(309, 376), (334, 390), (360, 406), (383, 423), (391, 436)], w=0.8, hand=0.5)   # hem
F([(394, 434), (404, 412), (420, 386), (431, 368)], w=0.8, hand=0.5)
ticks([(346, 318), (326, 342), (312, 370)], ang=40, spacing=6, maxlen=9, w=0.55, t0=0.2, t1=0.95)
ticks([(364, 322), (352, 356), (344, 392)], ang=20, spacing=6, maxlen=9, w=0.55, t0=0.25, t1=0.95)
ticks([(383, 318), (387, 336), (390, 354)], ang=15, spacing=6, maxlen=10, w=0.6, t0=0.02, t1=0.95)
ticks([(418, 323), (432, 336), (437, 352), (435, 366)], ang=170, spacing=6, maxlen=13, w=0.55)
ticks([(420, 390), (404, 418), (394, 442)], ang=-120, spacing=6, maxlen=10, w=0.55)
ticks([(358, 315), (370, 319), (382, 319)], ang=80, spacing=5.5, maxlen=7, w=0.55, minlen=2)
pen.occlude(R(kerchief))

# ---- apron, gathered into its band
apron = [(347, 482), (340, 560), (331, 680), (323, 800), (318, 838), (350, 846), (395, 851), (435, 846),
         (469, 836), (463, 720), (453, 600), (441, 481)]
S([(347, 482), (340, 560), (331, 680), (323, 800), (318, 838)], w=1.8)
S([(441, 481), (453, 600), (463, 720), (469, 836)], w=1.8)
S([(318, 838), (334, 842), (346, 846), (352, 843), (372, 849), (395, 852), (412, 849), (430, 847), (437, 850),
   (452, 842), (469, 836)], w=1.8)
S([(373, 490), (371, 512), (369, 534)], w=0.9)                      # gathers under the band
S([(386, 490), (385, 506)], w=0.8)
S([(424, 488), (427, 512)], w=0.8)
F([(351, 488), (344, 560), (335, 680), (327, 800), (322, 834)], w=0.7, hand=0.4)      # its hems
F([(437, 487), (449, 600), (459, 720), (465, 831)], w=0.7, hand=0.4)
F([(322, 832), (346, 839), (372, 843), (395, 846), (430, 841), (465, 830)], w=0.7, hand=0.4)
S([(405, 491), (407, 515), (409, 530)], w=0.9)
ticks([(350, 488), (372, 491), (396, 492), (420, 489), (440, 486)], ang=90, spacing=6, maxlen=12, w=0.55,
      t0=0.0, t1=1.0, prof=lambda u: 6 + 6 * math.sin(7 * u) ** 2)
apron_folds = [[(362, 488), (357, 560), (352, 650)],
               [(392, 489), (394, 560), (397, 620)],
               [(418, 488), (425, 570), (431, 660)],
               [(350, 760), (347, 810), (346, 843)],
               [(432, 740), (435, 800), (437, 846)]]
for fl in apron_folds:
    S(fl, w=1.0)
ticks(apron_folds[0], ang=0, spacing=6.5, maxlen=8, w=0.6, t0=0.05, t1=0.95)
ticks(apron_folds[2], ang=0, spacing=6.5, maxlen=9, w=0.6, t0=0.05, t1=0.95)
ticks(apron_folds[4], ang=0, spacing=6.5, maxlen=8, w=0.6, t0=0.05, t1=0.95)
ticks(apron_folds[1], ang=0, spacing=6.5, maxlen=7, w=0.55, t0=0.05, t1=0.95)
ticks(apron_folds[3], ang=0, spacing=6.5, maxlen=7, w=0.55, t0=0.05, t1=0.95)
ticks([(441, 484), (453, 600), (463, 720), (468, 834)], ang=185, spacing=6.5, maxlen=12, w=0.6, power=0.4)
S([(328, 470), (360, 474), (396, 478), (430, 471)], w=1.4)         # band
S([(330, 479), (362, 483), (396, 487), (431, 480)], w=1.4)
pen.occlude(R(apron))
pen.occlude(R([(328, 470), (360, 474), (396, 478), (430, 471), (431, 481), (396, 488), (362, 484), (330, 480)]))

# ---- bodice below the kerchief
S([(318, 384), (322, 430), (328, 470)], w=1.8)
S([(436, 364), (432, 420), (430, 471)], w=1.8)
S([(395, 442), (396, 470)], w=1.1)
for y in (450, 459, 467):                                           # hooks at the front
    F([(392, y), (398.5, y), (400, y + 1.6)], w=0.8)
F([(356, 416), (357, 444), (359, 470)], w=0.8)                      # a dart
tone(R([(306, 380), (332, 395), (360, 412), (386, 430), (395, 444), (396, 471), (328, 470), (322, 430), (318, 382)]),
     62, 8.5, w=0.65, skip=0.15)
tone(R([(403, 415), (419, 388), (436, 364), (432, 420), (430, 471), (396, 471), (395, 442)]), 62, 7.0, w=0.65)
pen.occlude(R([(306, 380), (395, 442), (436, 364), (432, 420), (430, 471), (328, 470), (322, 430), (318, 382)]))

# ---- skirt
skirt_L = [(328, 476), (310, 520), (292, 600), (275, 690), (258, 780), (242, 860), (230, 905)]
skirt_R = [(431, 476), (448, 520), (462, 600), (475, 700), (488, 800), (498, 870), (504, 903)]
hem = [(230, 905), (248, 913), (262, 909), (282, 919), (306, 923), (322, 919), (345, 927), (375, 930),
       (405, 929), (428, 925), (446, 927), (470, 919), (490, 913), (504, 903)]
S(skirt_L, w=2.2)
S(skirt_R, w=2.2)
S(hem, w=2.0)
skirt_folds = [[(318, 520), (300, 640), (284, 760), (262, 909)],
               [(328, 600), (318, 720), (308, 840), (305, 921)],
               [(324, 650), (309, 770), (293, 862), (285, 918)],
               [(306, 560), (290, 680), (270, 800), (250, 908)],
               [(455, 560), (466, 660), (476, 760), (486, 850), (496, 908)],
               [(444, 858), (449, 892), (451, 925)],
               [(376, 860), (374, 896), (372, 928)]]
for fl in skirt_folds:
    S(fl, w=1.2)
ticks(skirt_folds[0], ang=-15, spacing=6, maxlen=18, w=0.65, t0=0.05, t1=0.99, power=0.5)
ticks(skirt_folds[1], ang=-15, spacing=6, maxlen=14, w=0.65, t0=0.05, t1=0.99, power=0.5)
ticks(skirt_folds[2], ang=-15, spacing=6.5, maxlen=8, w=0.65, t0=0.1, t1=0.99, power=0.5)
ticks(skirt_folds[3], ang=-15, spacing=6.5, maxlen=7, w=0.65, t0=0.1, t1=0.99, power=0.5)
ticks(skirt_folds[5], ang=-15, spacing=6, maxlen=10, w=0.65, t0=0.05, t1=0.99, power=0.5)
ticks(skirt_folds[6], ang=-15, spacing=6, maxlen=10, w=0.65, t0=0.05, t1=0.99, power=0.5)
skirt = skirt_L + [(262, 909), (304, 921), (345, 927), (405, 929), (446, 927), (490, 913)] + skirt_R[::-1]
# shading as strokes running down with the skirt's folds: the far side in shadow
strands([(452, 590), (461, 700), (468, 836), (471, 916)], [(460, 590), (474, 700), (489, 810), (503, 900)],
        [0.3, 0.62, 0.9], w=0.7, t0=(0.0, 0.15), t1=(0.8, 1.0), wave=0.8, hand=0.4)
strands([(296, 600), (281, 700), (265, 800), (248, 905)], [(331, 600), (326, 700), (321, 800), (318, 900)],
        [0.25, 0.55, 0.85], w=0.65, t0=(0.45, 0.65), t1=(0.85, 1.0), wave=0.8, hand=0.4)
ticks([(318, 840), (350, 848), (395, 853), (435, 848), (469, 838)], ang=75, spacing=6, maxlen=22, w=0.65,
      t0=0.0, t1=1.0, prof=lambda u: 10 + 12 * u)
pen.occlude(R(skirt))
F([(234, 897), (262, 902), (284, 911), (306, 915), (345, 920), (375, 922), (405, 922), (446, 920), (470, 912),
   (490, 906), (501, 896)], w=0.7, hand=0.5)                         # the skirt's hem
S([(334, 929), (338, 937), (350, 941), (366, 942), (377, 938), (379, 931)], w=1.7)   # sturdy shoes
S([(339, 940), (356, 945), (375, 942)], w=1.0)
F([(352, 930), (358, 935), (364, 933)], w=0.8)
S([(418, 929), (422, 935), (434, 938), (450, 938), (459, 933), (459, 928)], w=1.6)
S([(423, 937), (440, 941), (457, 937)], w=0.9)

# ---- the ground: their shadows fall to the right
for (x0, x1, y) in [(470, 560, 932), (500, 590, 924), (690, 830, 940), (760, 860, 931), (520, 560, 940),
                    (180, 236, 912), (200, 245, 922), (780, 880, 948), (150, 220, 932)]:
    pen.line([(x0, y), (x1, y)], w=0.8, hand=0.5)
tone(R([(504, 905), (560, 915), (600, 925), (560, 930), (500, 930), (472, 922)]), 0, 5.5, w=0.65)
tone(R([(676, 940), (720, 935), (780, 932), (800, 938), (760, 946), (680, 947)]), 0, 5.5, w=0.65)
tone(R([(640, 950), (668, 948), (700, 951), (690, 958), (650, 958)]), 0, 5.0, w=0.65)

pen.save('../20-couple-1690s.svg', mirror=True)
pen.report()
