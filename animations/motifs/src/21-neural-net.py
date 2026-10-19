"""21 - neural net: a feed-forward network as a fine engraved figure.

The last drawing of the sequence, so the cleanest: a textbook diagram of a
fully connected feed-forward net, drawn from scratch with ruled lines.

- Five layers left to right, 4 - 6 - 6 - 6 - 3 nodes, on one vertical pitch,
  each column centred on the square's middle line, so the net is symmetric.
- Nodes are exact circles, one radius per layer, each a firm outline. The
  outline carries a shade line, as in a ruled patent figure: light from the
  upper left, so it swells toward the lower right (2.3 to 3.0). Nodes that
  fire have a thin inner ring filled with neat parallel hatching; two are
  half lit, hatched only on the lower-right (shade) half; the rest are plain.
- Every connection is a straight fine line (0.6) that stops exactly at the two
  node outlines (114 of them). Three strong weights (2.5) trace paths from the
  inputs to the winning output; that output wears a second outer ring.
  Where four or more connections cross at one point (halfway between layers)
  the thin ones leave a short gap so the dashes do not pile into a dot.
- Input arrows come in on the left, output arrows leave on the right, each
  with a small solid arrowhead; the winning output's arrow is heavier.

Everything is ruled (no hand wobble), so the strokes go in with pen.raw at
exact weights. Not mirrored (slot 21 faces as drawn). Run from this folder:
    python3 21-neural-net.py

(base/21-neural-net.svg holds the older hand-drawn net; it is no longer read.)
"""

import math

from pen import Pen, ellipse_pts

OUT = '../21-neural-net.svg'
pen = Pen(seed=2121)

# ---------------------------------------------------------------- layout
SIZES = [4, 6, 6, 6, 3]
RADII = [24, 26, 26, 26, 28]
GAP_X = 165          # between layer columns
PITCH = 112          # between nodes in a column
CX, CY = 500, 500

W_OUT_LIGHT = 2.3    # node outline, lit side
W_OUT_DARK = 3.0     # node outline, shade side
W_RING = 0.8
W_LINK = 0.6
W_STRONG = 2.5
W_HATCH = 0.7
W_ARROW = 1.7
W_ARROW_WIN = 2.2

xs = [CX + (i - (len(SIZES) - 1) / 2) * GAP_X for i in range(len(SIZES))]
nodes = []  # nodes[layer][k] = (x, y, r)
for li, n in enumerate(SIZES):
    col = []
    for k in range(n):
        col.append((xs[li], CY + (k - (n - 1) / 2) * PITCH, RADII[li]))
    nodes.append(col)

HALO = 6.5          # the winning output's outer ring, this far outside its outline

# Three strong paths from inputs to the winning output (layer, index per step).
WIN = 1
PATHS = [
    [0, 0, 1, 1, WIN],   # over the top
    [1, 3, 2, 3, WIN],   # through the middle
    [3, 4, 5, 4, WIN],   # along the bottom
]
strong = set()
lit = set()
for p in PATHS:
    for li, k in enumerate(p):
        lit.add((li, k))
        if li:
            strong.add((li - 1, p[li - 1], k))
# Half-lit nodes: some activation that did not carry through.
HALF = {(1, 1), (2, 3)} - lit


# ---------------------------------------------------------------- helpers
def circle(x, y, r, w, a0=0.0):
    pen.raw(ellipse_pts(x, y, r, r, 0, a0, a0 + 2 * math.pi, step=1.2), w)


def shaded_circle(x, y, r, w_light, w_dark, pieces=16):
    """A node outline with a shade line: light from the upper left, so the
    stroke swells smoothly toward the lower right, as in a ruled figure.
    Drawn as arcs that meet end to start, each at its own weight."""
    for k in range(pieces):
        a0 = -math.pi / 2 + 2 * math.pi * k / pieces
        a1 = a0 + 2 * math.pi / pieces
        mid = (a0 + a1) / 2
        t = max(0.0, math.cos(mid - math.pi / 4))  # 1 at the lower right
        t = t * t * (3 - 2 * t)
        pen.raw(ellipse_pts(x, y, r, r, 0, a0, a1, step=1.2), w_light + (w_dark - w_light) * t)


def hatch_disc(x, y, r, spacing, angle_deg=-45, w=W_HATCH, half=False):
    """Parallel chords across a disc, centred on it (an exact ruled fill).
    half=True keeps only the chords on the lower-right side of the diameter
    (the shade side of the shade line), as a half-lit node."""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)    # along the lines
    nx, ny = -uy, ux                     # across them (toward the lower right)
    n = int((2 * r) // spacing)
    if n % 2 == 0:
        n -= 1
    for j in range(n):
        o = (j - (n - 1) / 2) * spacing
        if half and o < spacing * 0.5:
            continue
        h = math.sqrt(max(0.0, r * r - o * o))
        if h < 2.0:
            continue
        mx, my = x + nx * o, y + ny * o
        pen.raw([(mx - ux * h, my - uy * h), (mx + ux * h, my + uy * h)], w)


def arrow(tail, tip, w, head=14.0, half=4.4):
    """A ruled shaft with a small solid arrowhead at the tip: the head's
    outline, filled with close strokes running along the arrow (the shaft
    itself runs on to the tip as the middle one)."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    base = (tip[0] - ux * head, tip[1] - uy * head)
    pen.raw([tail, (tip[0] - ux * 1.5, tip[1] - uy * 1.5)], w)
    b1 = (base[0] + nx * half, base[1] + ny * half)
    b2 = (base[0] - nx * half, base[1] - ny * half)
    pen.raw([b2, b1, tip, b2], 1.6)
    for o in (-2.0, 2.0):
        # a stroke along the arrow, from the base to where it meets the sides
        reach = head * (1 - abs(o) / half) - 1.0
        q0 = (base[0] + nx * o + ux * 0.6, base[1] + ny * o + uy * 0.6)
        pen.raw([q0, (q0[0] + ux * reach, q0[1] + uy * reach)], 1.6)


def link_ends(a, b, br_extra=0.0):
    """A connection's ends, exactly on the two node outlines."""
    ax, ay, ar = a
    bx, by, br = b
    br += br_extra
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    return (ax + ux * ar, ay + uy * ar), (bx - ux * br, by - uy * br)


def cross(p, q):
    """Where two segments cross, as (point, t along p, t along q), or None."""
    (x1, y1), (x2, y2) = p
    (x3, y3), (x4, y4) = q
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(d) < 1e-9:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d
    if not (0.02 < t < 0.98 and 0.02 < u < 0.98):
        return None
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t), t, u


# ---------------------------------------------------------------- connections
links = []  # dict(ends, w, strong, gap)
for li in range(len(SIZES) - 1):
    for i, a in enumerate(nodes[li]):
        for j, b in enumerate(nodes[li + 1]):
            halo = HALO if (li + 1 == len(SIZES) - 1 and j == WIN) else 0.0
            st = (li, i, j) in strong
            links.append(dict(ends=link_ends(a, b, halo), w=W_STRONG if st else W_LINK,
                              strong=st, layer=li, cuts=[]))

# Where four to six connections cross at one point (as they do halfway
# between two layers, the pattern of a full net), their dashes would pile into
# a dot that reads as an extra node. There the thin lines leave a short gap and
# only the flattest one (or a strong line) runs through, as a clean crossing.
PILE_GAP = 3.5  # half the gap, in units along the line
PILE_MIN = 4    # lines through one point that make a pile
for li in range(len(SIZES) - 1):
    group = [k for k, l in enumerate(links) if l['layer'] == li]
    hits = []  # (point, link index, t)
    for m, k1 in enumerate(group):
        for k2 in group[m + 1:]:
            c = cross(links[k1]['ends'], links[k2]['ends'])
            if c:
                hits.append((c[0], k1, c[1]))
                hits.append((c[0], k2, c[2]))
    piles = []  # [point, {link: t}]
    for pt, k, t in hits:
        for pile in piles:
            if math.hypot(pile[0][0] - pt[0], pile[0][1] - pt[1]) < 1.0:
                pile[1].setdefault(k, t)
                break
        else:
            piles.append([pt, {k: t}])
    for pt, members in piles:
        if len(members) < PILE_MIN:
            continue
        thin = [k for k in members if not links[k]['strong']]
        if len(thin) < len(members):
            keep = set()           # a strong line runs through alone
        else:
            def slope(k):
                (x0, y0), (x1, y1) = links[k]['ends']
                return abs((y1 - y0) / (x1 - x0))
            flat = min(slope(k) for k in thin)
            keep = {k for k in thin if slope(k) < flat + 1e-6}
        for k in thin:
            if k not in keep:
                links[k]['cuts'].append(members[k])

for l in sorted(links, key=lambda l: l['strong']):
    (x0, y0), (x1, y1) = l['ends']
    L = math.hypot(x1 - x0, y1 - y0)
    g = PILE_GAP / L
    t = 0.0
    for c in sorted(l['cuts']):
        pen.raw([(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), (x0 + (x1 - x0) * (c - g), y0 + (y1 - y0) * (c - g))], l['w'])
        t = c + g
    pen.raw([(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), (x1, y1)], l['w'])
print('gaps at piles:', sum(len(l['cuts']) for l in links))

# ---------------------------------------------------------------- nodes
for li, col in enumerate(nodes):
    for k, (x, y, r) in enumerate(col):
        shaded_circle(x, y, r, W_OUT_LIGHT, W_OUT_DARK)
        ri = r - 5.5
        if (li, k) in lit:
            circle(x, y, ri, W_RING, a0=-math.pi / 2)
            hatch_disc(x, y, ri - 2.2, 5.2)
        elif (li, k) in HALF:
            circle(x, y, ri, W_RING, a0=-math.pi / 2)
            hatch_disc(x, y, ri - 2.2, 5.2, half=True)

# the winning output: a second, outer ring
wx, wy, wr = nodes[-1][WIN]
circle(wx, wy, wr + HALO, 1.3, a0=-math.pi / 2)

# ---------------------------------------------------------------- arrows
ARROW_LEN = 62
for (x, y, r) in nodes[0]:
    tip = (x - r - 6, y)
    arrow((tip[0] - ARROW_LEN, y), tip, W_ARROW)
for k, (x, y, r) in enumerate(nodes[-1]):
    gap = r + (HALO + 6 if k == WIN else 6)
    tail = (x + gap, y)
    arrow(tail, (tail[0] + ARROW_LEN, y), W_ARROW_WIN if k == WIN else W_ARROW)

pen.save(OUT)
pen.report()
