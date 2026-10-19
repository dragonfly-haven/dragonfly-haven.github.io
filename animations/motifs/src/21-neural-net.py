"""21 - neural net: final polish of the passed drawing (reviewed 9 / 9 / 8).

The generator of this drawing was lost, so the passed SVG, kept in
base/21-neural-net.svg, is the source. This script reads it and changes only
what the review notes (src/reviews.md) point at; every other path is written
out exactly as it was.

- The small vertical ticks above the top node and below the bottom node of
  each column are removed (they read as stray marks at 1x).
- The thinnest connections (a three-piece stroke, every piece under 0.8 wide)
  get a slight low-frequency hand wobble, the same kind pen.py gives its lines,
  with the ends held fixed where they meet the nodes. Their pieces keep their
  weights; only their course moves, by about a unit.

Not mirrored (slot 21 faces as drawn). Run from this folder:
    python3 21-neural-net.py
"""

import math
import re

from pen import Pen, resample, length, dist, _n

BASE = 'base/21-neural-net.svg'
OUT = '../21-neural-net.svg'

PATH_RE = re.compile(r'<path d="([^"]*)"[^>]*stroke-width="([\d.]+)"')


def parse(path):
    """The file's lines, and for each path line its index, points and width."""
    lines = open(path).read().rstrip('\n').split('\n')
    paths = []
    for i, ln in enumerate(lines):
        m = PATH_RE.search(ln)
        if not m:
            continue
        nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', m.group(1))]
        paths.append(dict(i=i, pts=list(zip(nums[0::2], nums[1::2])), w=float(m.group(2))))
    return lines, paths


def path_line(pts, w):
    """A path element written the way pen.py writes it."""
    d = 'M' + ' '.join(f'{_n(x)} {_n(y)}' if k else f'{_n(x)} {_n(y)}L' for k, (x, y) in enumerate(pts))
    d = d.replace('L ', 'L')
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w, 2)}" stroke-linecap="round"/>'


lines, paths = parse(BASE)
pen = Pen(seed=2121)

# ------------------------------------------------ chains (a stroke's pieces meet end to start)
chains = []
for p in paths:
    if chains and chains[-1][-1]['pts'][-1] == p['pts'][0]:
        chains[-1].append(p)
    else:
        chains.append([p])


def chain_pts(c):
    out = list(c[0]['pts'])
    for p in c[1:]:
        out += p['pts'][1:]
    return out


# ------------------------------------------------ note 1: drop the ticks above / below the columns
# Each tick is two hair strokes (0.6 wide, two points, upright) on a column's
# axis, beyond its outermost node. Nodes are the closed heavy rings.
COLUMNS = [152, 265, 421, 588, 723, 822]
drop = set()
for p in paths:
    pts = p['pts']
    if len(pts) != 2 or p['w'] > 0.65:
        continue
    (x0, y0), (x1, y1) = pts
    if abs(x1 - x0) > 1.5 or abs(y1 - y0) < 1.5:
        continue
    cx = (x0 + x1) / 2
    col = min(COLUMNS, key=lambda c: abs(c - cx))
    if abs(col - cx) > 4:
        continue
    drop.add(p['i'])
assert len(drop) == 24, len(drop)  # two pieces per tick, a tick above and below each of six columns

# ------------------------------------------------ note 2: a slight wobble on the thinnest connections
replace = {}
HAND = 0.6
for c in chains:
    if len(c) != 3 or max(p['w'] for p in c) >= 0.8:
        continue
    pts = chain_pts(c)
    total = length(pts)
    a, b = pts[0], pts[-1]
    chord = dist(a, b)
    if total < 60 or chord < 0.9 * total:
        continue  # not a connection
    nx, ny = (b[1] - a[1]) / chord, -(b[0] - a[0]) / chord
    ph1, ph2 = pen.r(0, 6.3), pen.r(0, 6.3)
    f1, f2 = pen.r(0.005, 0.01), pen.r(0.016, 0.028)
    s_base = 0.0
    for p in c:
        piece = resample(p['pts'], 3.0)
        new = []
        s = s_base
        for k, q in enumerate(piece):
            if k:
                s += dist(piece[k - 1], q)
            ease = min(1.0, s / 18.0, (total - s) / 18.0)
            off = HAND * ease * (0.75 * math.sin(s * f1 * 2 * math.pi + ph1) + 0.25 * math.sin(s * f2 * 2 * math.pi + ph2))
            new.append((q[0] + nx * off, q[1] + ny * off))
        s_base += length(p['pts'])
        replace[p['i']] = [(new, p['w'])]
# the pieces of one connection must still meet: make each piece start where the last ended
for c in chains:
    if c[0]['i'] in replace:
        for k in range(1, len(c)):
            prev = replace[c[k - 1]['i']][0][0]
            cur = replace[c[k]['i']][0][0]
            cur[0] = prev[-1]

# ------------------------------------------------ write
out = []
for i, ln in enumerate(lines):
    if i in drop:
        continue
    if i in replace:
        out += [path_line(pts, w) for pts, w in replace[i]]
        continue
    out.append(ln)
with open(OUT, 'w') as f:
    f.write('\n'.join(out) + '\n')

# report on the whole drawing as written
for p in paths:
    if p['i'] in drop:
        continue
    for pts, w in replace.get(p['i'], [(p['pts'], p['w'])]):
        pen.raw(pts, w)
print(f'removed {len(drop)} tick strokes, wobbled {len(replace) // 3} thin connections')
pen.report()
