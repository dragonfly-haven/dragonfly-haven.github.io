"""02 Organic molecule: adenine, drawn as a chemist draws it.

Adenine (C5H5N5) is a prebiotic building block: it forms from hydrogen cyanide
and has been found in meteorites, and it is one of the four bases of RNA, so it
stands between the galaxy (01) and the RNA (03).

It is drawn as a textbook skeletal formula, in the conventional orientation:
the purine's regular hexagon (N1 C2 N3 C4 C5 C6) on the left, fused along
C4-C5 to a regular pentagon (C4 C5 N7 C8 N9) on the right, the amino group on
top. All bonds are one length and the rings have true angles. Kekule double
bonds N1=C6, C2=N3, C4=C5 and N7=C8 are a second, shorter line just inside the
ring. Heteroatoms are lettered with pen strokes (no SVG text) in a plain
technical hand; carbons are not lettered and their hydrogens are implied, as
in any skeletal formula. Bonds stop short of the letters.

Not mirrored (slot 02 faces as drawn). Run from this folder:
    python3 02-organic-molecule.py
"""

import math

from pen import Pen, lerp, dist

pen = Pen(seed=202)

# ---------------------------------------------------------------- sizes

L = 228.0           # bond length
LH = 72.0           # letter (cap) height
SUB = 0.62          # subscript height, as a share of LH
W_BOND = 2.5        # bonds
W_INNER = 2.1       # the inner line of a double bond
W_LET = 2.3         # lettering
INNER_OFF = 0.17    # inner line: offset into the ring, as a share of L
INNER_CUT = 0.13    # inner line: left off each end, as a share of L
MARGIN = 9.0        # clear paper between a bond's end and a letter

# ---------------------------------------------------------------- the skeleton (units of L, y up)

r3 = math.sqrt(3) / 2
apo5 = 0.5 / math.tan(math.radians(36))      # pentagon: centre to side
R5 = 0.5 / math.sin(math.radians(36))        # pentagon: centre to corner
P5 = (r3 + apo5, 0.0)                        # pentagon centre


def pent(deg):
    a = math.radians(deg)
    return (P5[0] + R5 * math.cos(a), P5[1] + R5 * math.sin(a))


A = {
    'C6': (0.0, 1.0),
    'N1': (-r3, 0.5),
    'C2': (-r3, -0.5),
    'N3': (0.0, -1.0),
    'C4': (r3, -0.5),
    'C5': (r3, 0.5),
    'N7': pent(72),
    'C8': pent(0),
    'N9': pent(-72),
    'N6': (0.0, 2.0),                        # the amino nitrogen
}
HEX_C = (0.0, 0.0)

BONDS = [('C6', 'N1'), ('N1', 'C2'), ('C2', 'N3'), ('N3', 'C4'), ('C4', 'C5'), ('C5', 'C6'),
         ('C5', 'N7'), ('N7', 'C8'), ('C8', 'N9'), ('N9', 'C4'), ('C6', 'N6')]
DOUBLE = [('N1', 'C6', HEX_C), ('C2', 'N3', HEX_C), ('C4', 'C5', HEX_C), ('N7', 'C8', P5)]

# ---------------------------------------------------------------- lettering (glyphs: unit cap height, y down, top left at 0,0)


def arc(cx, cy, rx, ry, d0, d1, n=24):
    return [(cx + rx * math.cos(math.radians(d0 + (d1 - d0) * k / n)),
             cy - ry * math.sin(math.radians(d0 + (d1 - d0) * k / n))) for k in range(n + 1)]


GLYPHS = {
    'N': (0.70, [[(0, 1), (0, 0), (0.70, 1), (0.70, 0)]]),
    'H': (0.66, [[(0, 0), (0, 1)], [(0.66, 0), (0.66, 1)], [(0, 0.5), (0.66, 0.5)]]),
    '2': (0.62, [arc(0.30, 0.29, 0.30, 0.29, 165, -40) + [(0.0, 1.0), (0.64, 1.0)]]),
}


def glyph_strokes(ch, x, y, h):
    """A glyph's strokes with its top left at (x, y) on the page, cap height h."""
    w, strokes = GLYPHS[ch]
    return [[(x + px * h, y + py * h) for px, py in s] for s in strokes], w * h


# ---------------------------------------------------------------- layout on the page

def page(p, s=1.0):
    return (OX + p[0] * L * s, OY - p[1] * L * s)


OX, OY = 0.0, 0.0      # set once the bounding box is known (two passes)


def layout():
    """Letters (as strokes) and the boxes the bonds must keep out of."""
    letters, boxes = [], {}
    nw = GLYPHS['N'][0] * LH

    def put(ch, x, y, h):
        st, w = glyph_strokes(ch, x, y, h)
        letters.extend(st)
        return (x, y, x + w, y + h)

    for name in ('N1', 'N3', 'N7', 'N9', 'N6'):
        cx, cy = page(A[name])
        boxes[name] = [put('N', cx - nw / 2, cy - LH / 2, LH)]
    # NH2 on the amino nitrogen: H after the N, the 2 smaller and lower
    cx, cy = page(A['N6'])
    gap = 0.20 * LH
    hx = cx + nw / 2 + gap
    boxes['N6'].append(put('H', hx, cy - LH / 2, LH))
    sx = hx + GLYPHS['H'][0] * LH + 0.10 * LH
    sh = SUB * LH
    boxes['N6'].append(put('2', sx, cy + LH / 2 - sh + 0.30 * sh, sh))
    # the hydrogen on N9, written under its N
    cx, cy = page(A['N9'])
    hw = GLYPHS['H'][0] * LH
    boxes['N9'].append(put('H', cx - hw / 2, cy + LH / 2 + 0.36 * LH, LH))
    return letters, boxes


def in_boxes(p, bl, m=MARGIN):
    return any(b[0] - m <= p[0] <= b[2] + m and b[1] - m <= p[1] <= b[3] + m for b in bl)


def trim(a, b, ba, bb):
    """The part of segment a-b outside the letter boxes at either end."""
    n = 400
    t0, t1 = 0.0, 1.0
    if ba:
        k = 0
        while k < n and in_boxes(lerp(a, b, k / n), ba):
            k += 1
        t0 = k / n
    if bb:
        k = n
        while k > 0 and in_boxes(lerp(a, b, k / n), bb):
            k -= 1
        t1 = k / n
    return lerp(a, b, t0), lerp(a, b, t1)


def ink(pts, w, hand=0.15):
    """A sure, even stroke: one piece, no lifts, the weight barely varying."""
    n0 = len(pen.strokes)
    pen.line(pts, w=w, hand=hand, lift=0.0, piece=(5000, 5000), occlude=False)
    for i in range(n0, len(pen.strokes)):
        p, _ = pen.strokes[i]
        pen.strokes[i] = (p, w * pen.r(0.97, 1.03))


def bbox_of(strokes):
    xs = [x for s in strokes for x, _ in s]
    ys = [y for s in strokes for _, y in s]
    return min(xs), min(ys), max(xs), max(ys)


def build():
    letters, boxes = layout()
    bonds = []
    for a, b in BONDS:
        p, q = trim(page(A[a]), page(A[b]), boxes.get(a), boxes.get(b))
        bonds.append([p, q])
    inner = []
    for a, b, c in DOUBLE:
        pa, pb, pc = page(A[a]), page(A[b]), page(c)
        # offset toward the ring's centre
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        Lb = math.hypot(dx, dy)
        nx, ny = -dy / Lb, dx / Lb
        mid = lerp(pa, pb, 0.5)
        if (pc[0] - mid[0]) * nx + (pc[1] - mid[1]) * ny < 0:
            nx, ny = -nx, -ny
        o = INNER_OFF * L
        qa = (pa[0] + nx * o, pa[1] + ny * o)
        qb = (pb[0] + nx * o, pb[1] + ny * o)
        qa, qb = lerp(qa, qb, INNER_CUT), lerp(qa, qb, 1 - INNER_CUT)
        qa, qb = trim(qa, qb, boxes.get(a), boxes.get(b))
        inner.append([qa, qb])
    return letters, bonds, inner


# first pass: find the extent, then centre it on the page
letters, bonds, inner = build()
x0, y0, x1, y1 = bbox_of(letters + bonds)
OX, OY = 500 - (x0 + x1) / 2, 500 - (y0 + y1) / 2
letters, bonds, inner = build()

import sys
VAR = sys.argv[1] if len(sys.argv) > 1 else 'plain'
if VAR == 'heavy':
    W_BOND, W_INNER, W_LET = 2.9, 2.5, 2.7
for s in bonds:
    ink(s, W_BOND)
for s in inner:
    ink(s, W_INNER)
for s in letters:
    ink(s, W_LET, hand=0.08)
if VAR == 'double':
    from pen import offset, resample
    for s in bonds + inner + letters:
        ink(offset(resample(s, 2.0), 1.5), 2.2)
if VAR == 'shadow':
    from pen import offset, resample
    for s in bonds + inner:
        a, b = s
        dx, dy = b[0]-a[0], b[1]-a[1]
        Lb = math.hypot(dx, dy); nx, ny = -dy/Lb, dx/Lb
        if nx + ny < 0: nx, ny = -nx, -ny
        sh = [(a[0]+nx*6, a[1]+ny*6), (b[0]+nx*6, b[1]+ny*6)]
        sh = [lerp(sh[0], sh[1], 0.04), lerp(sh[0], sh[1], 0.96)]
        ink(sh, 0.9)

pen.save(sys.argv[2] if len(sys.argv) > 2 else '../02-organic-molecule.svg')
pen.report()
