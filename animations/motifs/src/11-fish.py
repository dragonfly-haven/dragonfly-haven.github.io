"""11 - fish: final polish of the passed drawing (reviewed 9 / 9 / 8).

The generator of this drawing was lost, so the passed SVG, kept in
base/11-fish.svg, is the source. This script reads it, changes only what the
review notes (src/reviews.md) point at, and writes every other path out
exactly as it was. Paths are picked by position and shape (with counts
checked), in the unmirrored frame: head at the right.

- Belly: the ruler-straight ventral line gets a gentle swell mid-belly and a
  slight waist at the tail base. It is done as a smooth displacement of
  everything near the belly (the line, the fins hanging from it, the lower
  scale rows, fading out up the flank), so nothing comes apart.
- Pelvic fins: the far fin, which stood out as a second spike, is tucked
  behind the near one as a sliver along its leading edge.
- Shoulder: the rear one of the two heavy lines behind the gill cover is
  thinned and broken, so the pair no longer reads as a helmet seam.
- The eye's outer ring is thinned; the scale marks thin toward the belly.

Saved mirrored (slots 10-20 face the text). Run from this folder:
    python3 11-fish.py
"""

import math
import re

from pen import Pen, resample, length, dist, lerp, offset, _n

BASE = 'base/11-fish.svg'
OUT = '../11-fish.svg'

PATH_RE = re.compile(r'<path d="([^"]*)"[^>]*stroke-width="([\d.]+)"')

pen = Pen(seed=1111)


# ---------------------------------------------------------------- reading the base

def parse(path):
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
    d = 'M' + ' '.join(f'{_n(x)} {_n(y)}' if k else f'{_n(x)} {_n(y)}L' for k, (x, y) in enumerate(pts))
    d = d.replace('L ', 'L')
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w, 2)}" stroke-linecap="round"/>'


def box(p):
    xs, ys = [q[0] for q in p['pts']], [q[1] for q in p['pts']]
    return min(xs), min(ys), max(xs), max(ys)


def plen(p):
    return length(p['pts'])


def find(pred, n, what):
    out = [p for p in paths if pred(p)]
    assert len(out) == n, (what, len(out), [box(p) for p in out])
    return out


def cut(pts, s0, s1):
    out, s = [], 0.0
    for a, b in zip(pts, pts[1:]):
        d = dist(a, b)
        if d == 0:
            continue
        lo, hi = max(s0, s), min(s1, s + d)
        if lo < hi:
            pa, pb = lerp(a, b, (lo - s) / d), lerp(a, b, (hi - s) / d)
            if not out or dist(out[-1], pa) > 1e-6:
                out.append(pa)
            out.append(pb)
        s += d
    return out


def smooth(e0, e1, v):
    t = min(1.0, max(0.0, (v - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


lines, paths = parse(BASE)
drop = set()     # line indices left out
new = {}         # line index -> [(pts, w)] in its place (geometry and/or weight changed)
added = []       # new strokes

# ---------------------------------------------------------------- the belly line (as it was)
belly = find(lambda p: p['w'] > 2.9 and plen(p) > 300 and abs(box(p)[0] - 324.4) < 1 and abs(box(p)[2] - 665.5) < 1, 1, 'belly')[0]
BEL = sorted(belly['pts'])  # by x
BX0, BX1 = BEL[0][0], BEL[-1][0]


def belly_y(x):
    for a, b in zip(BEL, BEL[1:]):
        if a[0] <= x <= b[0] and b[0] > a[0]:
            return a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
    return None


# ================================================================ scale marks thin toward the belly
# short strokes on the flank above the belly line: weight eases from half at the
# belly to unchanged about 75 units up
# (on the tail stalk, past the belly line's end, the line is carried on
# straight and the thinning fades out toward the tail fin)
slope = (BEL[1][1] - BEL[0][1]) / (BEL[1][0] - BEL[0][0])
n_thin = 0
for p in paths:
    if plen(p) > 25 or p is belly:
        continue
    x0, y0, x1, y1 = box(p)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    by = belly_y(cx)
    fade = 1.0
    if by is None and 240 < cx < BX0:
        by = BEL[0][1] + (cx - BX0) * slope
        fade = smooth(240, BX0 + 6, cx)
    if by is None or cy > by - 1.5:
        continue
    h = by - cy
    f = 1.0 - 0.5 * fade * (1.0 - smooth(8, 78, h))
    if f < 0.99 and p['w'] > 0.8:
        nw = max(0.75 if p['w'] > 1.0 else 0.65, p['w'] * f)
        if abs(nw - p['w']) > 0.04:
            new[p['i']] = [(p['pts'], nw)]
            n_thin += 1

# ================================================================ eye: thinner outer ring
eye = find(lambda p: p['w'] >= 2.0 and abs((box(p)[0] + box(p)[2]) / 2 - 879.5) < 1.5 and abs((box(p)[2] - box(p)[0]) / 2 - 28.2) < 1.5, 1, 'eye outer ring')[0]
new[eye['i']] = [(eye['pts'], 1.35)]

# ================================================================ shoulder: the rear line thinned and broken
rear = find(lambda p: abs(p['w'] - 1.7) < 0.01 and 180 < plen(p) < 205 and abs(p['pts'][0][0] - 731.8) < 1 and abs(p['pts'][-1][1] - 501.8) < 1, 1, 'shoulder rear line')[0]
L = plen(rear)
pieces = []
for t0, t1, w in ((0.08, 0.40, 1.05), (0.47, 0.70, 1.15), (0.76, 0.93, 1.05)):
    part = resample(cut(rear['pts'], t0 * L, t1 * L), 2.0)
    start = len(pen.strokes)
    pen.line(part, w=w, hand=0.3, lift=0, piece=(20, 50), taper=0.5, occlude=False)
    pieces += pen.strokes[start:]
new[rear['i']] = pieces

# ================================================================ pelvic fins: the far one as a sliver
far_edge = find(lambda p: abs(p['pts'][0][0] - 597.6) < 0.5 and abs(p['pts'][0][1] - 542.7) < 0.5 and abs(p['pts'][-1][1] - 604.9) < 0.5, 1, 'far fin front edge')
far_back = find(lambda p: abs(p['pts'][0][0] - 592.8) < 0.5 and abs(p['pts'][0][1] - 604.9) < 0.5, 1, 'far fin back edge')
far_rays = find(lambda p: p['w'] < 1.0 and 575 < box(p)[0] and box(p)[2] < 592 and 558 < box(p)[1] and box(p)[3] < 595 and box(p)[3] - box(p)[1] > 7, 2, 'far fin rays')
for p in far_edge + far_back + far_rays:
    drop.add(p['i'])
near_edge = find(lambda p: abs(p['pts'][0][0] - 591.9) < 0.5 and abs(p['pts'][0][1] - 541.5) < 0.5 and abs(p['pts'][-1][1] - 598.7) < 0.5, 1, 'near fin front edge')[0]
ne = resample(near_edge['pts'], 1.0)
n = len(ne)
sl = []
for k, q in enumerate(ne[:int(n * 0.86)]):
    t = k / (n - 1)
    d = 5.5 * (1 - smooth(0.45, 0.86, t))
    sl.append(offset(ne[max(0, k - 2):k + 3], d)[min(k, 2)])
sl = [(597.0, belly_y(597.0) + 0.6)] + sl[3:]
start = len(pen.strokes)
pen.line(sl, w=1.35, hand=0.3, lift=0, piece=(18, 40), taper=0.45, occlude=False)
added += pen.strokes[start:]

# ================================================================ belly: a gentle swell and a waist at the tail base
SWELL, WAIST = 8.0, 2.6
XA, XB = BX0 + 5.0, BX1     # 329 .. 665
REACH = 90.0                # how far up the flank the move fades out


def dy_belly(x):
    if not XA < x < XB:
        return 0.0
    u = (XB - x) / (XB - XA)                     # 0 at the pectoral fin, 1 at the tail base
    d = SWELL * math.sin(math.pi * u ** 0.756) ** 2   # deepest about 40% along
    if x < XA + 95:
        d -= WAIST * math.sin(math.pi * (x - XA) / 95) ** 2
    return d


def move(pt):
    x, y = pt
    d = dy_belly(x)
    if d == 0.0:
        return pt
    by = belly_y(x)
    if by is None:
        return pt
    h = by - y                                   # height above the belly line
    f = 1.0 - smooth(0.0, REACH, h)
    return (x, y + d * f)


n_moved = 0
for p in paths:
    if p['i'] in drop:
        continue
    pts = new[p['i']] if p['i'] in new else [(p['pts'], p['w'])]
    moved = [([move(q) for q in s], w) for s, w in pts]
    if any(dist(a, b) > 0.05 for (s0, _), (s1, _) in zip(pts, moved) for a, b in zip(s0, s1)):
        new[p['i']] = moved
        n_moved += 1
added = [([move(q) for q in s], w) for s, w in added]

# ================================================================ write
out = []
for i, ln in enumerate(lines):
    if ln.strip() == '</g>':
        out += [path_line(s, w) for s, w in added]
        out.append(ln)
        continue
    if i in drop:
        continue
    if i in new:
        out += [path_line(s, w) for s, w in new[i]]
        continue
    out.append(ln)
with open(OUT, 'w') as f:
    f.write('\n'.join(out) + '\n')

rep = Pen()
for p in paths:
    if p['i'] in drop:
        continue
    for s, w in new.get(p['i'], [(p['pts'], p['w'])]):
        rep.raw(s, w)
for s, w in added:
    rep.raw(s, w)
print(f'scale marks thinned {n_thin}, paths moved by the belly swell {n_moved}, dropped {len(drop)}, added {len(added)}')
rep.report()
