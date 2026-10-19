"""21 - neural net: a feed-forward network as a fine engraved figure.

The last drawing of the sequence, so the cleanest: a textbook diagram of a
fully connected feed-forward net, drawn from scratch with ruled lines.

- Five layers left to right, 4 - 6 - 6 - 6 - 3 nodes, on one vertical pitch,
  each column centred on the square's middle line, so the net is symmetric.
- Nodes are exact circles, one radius per layer, each a firm outline with a
  thin inner ring. Nodes that fire are filled inside the ring with neat
  parallel hatching; a few are half lit, with sparser hatching.
- Every connection is a straight fine line that stops exactly at the two node
  outlines (114 of them). Three strong weights trace paths from the inputs to
  the winning output, drawn heavier; that output wears a second outer ring.
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
PITCH = 108          # between nodes in a column
CX, CY = 500, 500

W_OUTLINE = 2.1
W_RING = 0.8
W_LINK = 0.7
W_STRONG = 1.7
W_HATCH = 0.7
W_ARROW = 1.3
W_ARROW_WIN = 1.9

xs = [CX + (i - (len(SIZES) - 1) / 2) * GAP_X for i in range(len(SIZES))]
nodes = []  # nodes[layer][k] = (x, y, r)
for li, n in enumerate(SIZES):
    col = []
    for k in range(n):
        col.append((xs[li], CY + (k - (n - 1) / 2) * PITCH, RADII[li]))
    nodes.append(col)

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
HALF = {(1, 1), (2, 3), (3, 0), (0, 2)} - lit


# ---------------------------------------------------------------- helpers
def circle(x, y, r, w, a0=0.0):
    pen.raw(ellipse_pts(x, y, r, r, 0, a0, a0 + 2 * math.pi, step=1.2), w)


def hatch_disc(x, y, r, spacing, angle_deg=-45, w=W_HATCH):
    """Parallel chords across a disc, centred on it (an exact ruled fill)."""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)    # along the lines
    nx, ny = -uy, ux                     # across them
    n = int((2 * r) // spacing)
    if n % 2 == 0:
        n -= 1
    for j in range(n):
        o = (j - (n - 1) / 2) * spacing
        h = math.sqrt(max(0.0, r * r - o * o))
        if h < 2.0:
            continue
        mx, my = x + nx * o, y + ny * o
        pen.raw([(mx - ux * h, my - uy * h), (mx + ux * h, my + uy * h)], w)


def arrow(tail, tip, w, head=15.0, half=4.6):
    """A ruled shaft with a small solid arrowhead at the tip."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    base = (tip[0] - ux * head, tip[1] - uy * head)
    pen.raw([tail, (base[0] + ux * 1.0, base[1] + uy * 1.0)], w)
    b1 = (base[0] + nx * half, base[1] + ny * half)
    b2 = (base[0] - nx * half, base[1] - ny * half)
    pen.raw([tip, b1, b2, tip], 1.0)
    # filled solid: strokes from the tip fanning to the base
    for t in (-0.55, 0.0, 0.55):
        q = (base[0] + nx * half * t + ux * 1.2, base[1] + ny * half * t + uy * 1.2)
        pen.raw([tip, q], 1.3)


def link(a, b, w):
    ax, ay, ar = a
    bx, by, br = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    pen.raw([(ax + ux * ar, ay + uy * ar), (bx - ux * br, by - uy * br)], w)


# ---------------------------------------------------------------- connections
for li in range(len(SIZES) - 1):
    for i, a in enumerate(nodes[li]):
        for j, b in enumerate(nodes[li + 1]):
            if (li, i, j) not in strong:
                link(a, b, W_LINK)
for (li, i, j) in sorted(strong):
    link(nodes[li][i], nodes[li + 1][j], W_STRONG)

# ---------------------------------------------------------------- nodes
for li, col in enumerate(nodes):
    for k, (x, y, r) in enumerate(col):
        circle(x, y, r, W_OUTLINE, a0=-math.pi / 2)
        ri = r - 5.5
        circle(x, y, ri, W_RING, a0=-math.pi / 2)
        if (li, k) in lit:
            hatch_disc(x, y, ri - 2.2, 5.2)
        elif (li, k) in HALF:
            hatch_disc(x, y, ri - 2.2, 8.4)

# the winning output: a second, outer ring
wx, wy, wr = nodes[-1][WIN]
circle(wx, wy, wr + 6, 0.9, a0=-math.pi / 2)

# ---------------------------------------------------------------- arrows
ARROW_LEN = 62
for (x, y, r) in nodes[0]:
    tip = (x - r - 6, y)
    arrow((tip[0] - ARROW_LEN, y), tip, W_ARROW)
for k, (x, y, r) in enumerate(nodes[-1]):
    gap = r + (12 if k == WIN else 6)
    tail = (x + gap, y)
    arrow(tail, (tail[0] + ARROW_LEN, y), W_ARROW_WIN if k == WIN else W_ARROW)

pen.save(OUT)
pen.report()
