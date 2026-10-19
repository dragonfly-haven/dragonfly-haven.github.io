"""10 - trilobite: final polish of the passed drawing (reviewed 8 / 9 / 8).

The generator of this drawing was lost, so the passed SVG, kept in
base/10-trilobite.svg, is the source. This script reads it, changes only what
the review notes (src/reviews.md) point at, and writes every other path out
exactly as it was. Paths are picked by position and shape (with counts
checked), in the unmirrored frame: head at the right, tail at the left.

- Tail: the oval ring round the end of the axis gives way to a small pygidium,
  a shield joined to the last thoracic segments, its lower margin shaded with
  short concentric arcs; the axis runs into it with three axial rings that
  fade toward the tip.
- Head: the glabella (the central lobe) gets a heavier outline; the facial
  sutures and the furrow strokes at the eye tips are thinned; the crosshatch
  at the glabella's front loses its cross strokes, leaving the parallel
  contour strokes that follow the form.
- The neck node on the occipital ring is dropped (it reads as a squiggle at 1x).
- Thorax: the lower row of pleurae is shaded a little, a fine stroke running
  on down each pleura from its short furrow mark, each a different length; the
  repeated short strokes of both rows are cut to varying lengths so the
  segments do not repeat exactly.

Saved mirrored (slots 10-20 face the text). Run from this folder:
    python3 10-trilobite.py
"""

import math
import random
import re

from pen import Pen, catmull, resample, length, dist, lerp, offset, _n

BASE = 'base/10-trilobite.svg'
OUT = '../10-trilobite.svg'

PATH_RE = re.compile(r'<path d="([^"]*)"[^>]*stroke-width="([\d.]+)"')

pen = Pen(seed=1010)
rng = random.Random(10)


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


lines, paths = parse(BASE)

# a stroke's pieces meet end to start: group them back into strokes ("chains")
chains = []
for p in paths:
    if chains and chains[-1][-1]['pts'][-1] == p['pts'][0]:
        chains[-1].append(p)
    else:
        chains.append([p])


def cpts(c):
    out = list(c[0]['pts'])
    for p in c[1:]:
        out += p['pts'][1:]
    return out


def clen(c):
    return sum(length(p['pts']) for p in c)


def cbox(c):
    pts = cpts(c)
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return min(xs), min(ys), max(xs), max(ys)


def wmax(c):
    return max(p['w'] for p in c)


def wmin(c):
    return min(p['w'] for p in c)


def find(pred, n=None, what=''):
    out = [c for c in chains if pred(c)]
    if n is not None:
        assert len(out) == n, (what, len(out), [cbox(c) for c in out])
    return out


drop = set()      # line indices left out
replace = {}      # line index -> [(pts, w), ...] written in its place
added = []        # new strokes (from pen) go at the end


def drop_chain(c):
    for p in c:
        drop.add(p['i'])


def reweight(c, f):
    """New weights for a stroke's pieces: f(old weight, piece index, piece count)."""
    for k, p in enumerate(c):
        replace[p['i']] = [(p['pts'], f(p['w'], k, len(c)))]


def cut(pts, s0, s1):
    """The part of a polyline between arc lengths s0 and s1."""
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


def trim(c, keep0, keep1):
    """Keeps only arc-length share keep0..keep1 of a stroke, pieces keeping their weights."""
    total = clen(c)
    s0, s1 = keep0 * total, keep1 * total
    s = 0.0
    for p in c:
        L = length(p['pts'])
        part = cut(p['pts'], s0 - s, s1 - s) if (s + L > s0 and s < s1) else []
        if len(part) >= 2 and length(part) > 0.5:
            replace[p['i']] = [(part, p['w'])]
        else:
            drop.add(p['i'])
        s += L


def x_at(pts, y):
    """Where a near-vertical polyline crosses height y (None if it does not)."""
    for a, b in zip(pts, pts[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
            return a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
    return None


def add(pts, w, **kw):
    kw.setdefault('occlude', False)
    start = len(pen.strokes)
    pen.line(pts, w=w, **kw)
    added.extend(pen.strokes[start:])


# ================================================================ tail: a pygidium
# old: the ring (two heavy half-ovals), its hatching, a tick in the axis tip and
# the two heavy rings across the tip. kept: the tip's outline and the two short
# rib strokes leaving the axis at its corners.
ring = find(lambda c: wmax(c) >= 2.0 and abs(cbox(c)[0] - 186) < 3 and cbox(c)[2] > 238 and clen(c) > 70, 2, 'ring')
tip_rings = find(lambda c: len(c) == 1 and 1.5 <= c[0]['w'] <= 2.0 and 220 < cbox(c)[0] < 235
                 and cbox(c)[3] - cbox(c)[1] > 40 and cbox(c)[2] - cbox(c)[0] < 4, 2, 'tip rings')
tail_hatch = find(lambda c: wmax(c) <= 1.15 and 190 < cbox(c)[0] and cbox(c)[2] < 232
                  and 515 < cbox(c)[1] and cbox(c)[3] < 545, 4, 'tail hatch')
tick = find(lambda c: wmax(c) <= 1.0 and 214 < cbox(c)[0] and cbox(c)[2] < 221 and 500 < cbox(c)[1] and cbox(c)[3] < 516, 1, 'tick')
for c in ring + tip_rings + tail_hatch + tick:
    drop_chain(c)

# the tip's outline, to fit the rings into
tip = find(lambda c: len(c) == 6 and abs(cbox(c)[0] - 210) < 1.5 and cbox(c)[2] > 239, 2, 'axis tip')
tip.sort(key=lambda c: cbox(c)[1])
tip_top, tip_bot = cpts(tip[0]), cpts(tip[1])


def y_on(pts, x):
    for a, b in zip(pts, pts[1:]):
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            return a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
    return None


# three axial rings, each lighter and shorter than the one before
for x, w in ((233.0, 1.45), (225.5, 1.05), (218.5, 0.75)):
    y0, y1 = y_on(tip_top, x) + 1.8, y_on(tip_bot, x) - 1.8
    bow = 1.4  # bulging gently toward the tip, as the rings round off
    add(catmull([(x + 0.4, y0), (x - bow, (y0 + y1) / 2), (x + 0.4, y1)], step=2.0), w, hand=0.25, lift=0, piece=(14, 30), taper=0.35)

# the plate: a rounded shield from corner to corner of the last segment
CX, CY, RX, RY, EXP = 241.0, 500.0, 43.0, 51.5, 2.35


def shield(theta, inset=0.0):
    c, s = math.cos(theta), math.sin(theta)
    fx = math.copysign(abs(c) ** (2 / EXP), c)
    fy = math.copysign(abs(s) ** (2 / EXP), s)
    return (CX + (RX - inset) * fx, CY + (RY - inset) * fy)


def shield_arc(t0, t1, inset=0.0, n=60):
    return [shield(math.radians(t0 + (t1 - t0) * k / n), inset) for k in range(n + 1)]


add(shield_arc(268, 180), 2.0, hand=0.5, lift=0, taper=0.25)     # upper margin, lit
add(shield_arc(180, 92), 2.4, hand=0.5, lift=0, taper=0.25)      # lower margin, in shadow
# shading: short arcs along the lower margin, fading inward
add(shield_arc(100, 158, 5.5), 1.0, hand=0.3, lift=0, taper=0.5)
add(shield_arc(106, 146, 11.0), 0.8, hand=0.3, lift=0, taper=0.5)
add(shield_arc(114, 134, 16.5), 0.65, hand=0.3, lift=0, taper=0.5)
# and a single light one above
add(shield_arc(204, 236, 5.5), 0.7, hand=0.3, lift=0, taper=0.5)

# ================================================================ head
# glabella outline: its sides (the long contour from the eye tips round the
# neck) and its front (the inner curve before the border)
glab_side = find(lambda c: len(c) == 7 and abs(cbox(c)[0] - 611) < 2 and abs(cbox(c)[2] - 764) < 2, 1, 'glabella sides')[0]
reweight(glab_side, lambda w, k, n: max(w, 2.05 + 0.1 * (k % 2)))
glab_front = find(lambda c: len(c) == 5 and 729 < cbox(c)[0] < 735 and 773 < cbox(c)[2] < 777 and cbox(c)[1] < 420 and cbox(c)[3] > 580, 1, 'glabella front')[0]
reweight(glab_front, lambda w, k, n: [1.6, 2.1, 1.9, 1.7, 1.5][k])

# the cross strokes of the crosshatch at the glabella's front
cross = find(lambda c: len(c) <= 3 and wmax(c) <= 1.15 and 8 < clen(c) < 36
             and cbox(c)[0] > 722 and 452 < cbox(c)[1] and cbox(c)[3] < 584
             and (cpts(c)[-1][0] - cpts(c)[0][0]) * (cpts(c)[-1][1] - cpts(c)[0][1]) < 0, 16, 'front cross strokes')
for c in cross:
    drop_chain(c)
# and the few that cross the suture just below the front eye tip
cross2 = find(lambda c: len(c) <= 2 and wmax(c) <= 1.15 and 10 < clen(c) < 20
              and 726 < cbox(c)[0] and cbox(c)[2] < 757 and 588 < cbox(c)[1] and cbox(c)[3] < 606
              and (cpts(c)[-1][0] - cpts(c)[0][0]) * (cpts(c)[-1][1] - cpts(c)[0][1]) < 0, 3, 'eye tip cross strokes')
for c in cross2:
    drop_chain(c)

# facial sutures, from the eye tips to the margin, fore and aft
sutures = find(lambda c: len(c) == 1 and c[0]['w'] == 1.3 and 45 < clen(c) < 60
               and (abs(cbox(c)[0] - 721) < 2 or abs(cbox(c)[0] - 610) < 2), 4, 'sutures')
for c in sutures:
    reweight(c, lambda w, k, n: 0.85)
# the short strokes at the front eye tips
tips = find(lambda c: len(c) == 1 and 1.0 <= c[0]['w'] <= 1.2 and 10 < clen(c) < 15
            and 719 < cbox(c)[0] < 723 and (405 < cbox(c)[1] < 420 or 580 < cbox(c)[1] < 595), 4, 'eye tip strokes')
for c in tips:
    reweight(c, lambda w, k, n: 0.8)
# glabellar furrows starting at the eye tips (heavy where they meet the outline)
furrows = find(lambda c: len(c) == 3 and [p['w'] for p in c] == [1.8, 1.5, 1.2] and 700 < cbox(c)[0] < 720, 4, 'glabellar furrows')
for c in furrows:
    reweight(c, lambda w, k, n: [1.25, 1.05, 0.9][k])

# ================================================================ the neck node
node = find(lambda c: len(c) == 1 and 615 < cbox(c)[0] < 620 and cbox(c)[2] < 630 and 492 < cbox(c)[1] < 498 and clen(c) < 22, 2, 'neck node')
for c in node:
    drop_chain(c)

# ================================================================ thorax
furrow_rows = find(lambda c: len(c) == 11 and wmax(c) >= 2.4 and wmin(c) <= 0.9 and cbox(c)[2] < 610, 34, 'pleural furrows')
lower = sorted([c for c in furrow_rows if cbox(c)[1] > 520], key=lambda c: -cbox(c)[0])
upper = sorted([c for c in furrow_rows if cbox(c)[1] < 480], key=lambda c: -cbox(c)[0])
assert len(lower) == len(upper) == 17

used = set()
n_shade = n_curve = n_upper = 0
for F in lower:
    fp = cpts(F)                  # from the axis (top) outward
    top, bot = fp[0], fp[-1]
    # the lighter curve where the pleura turns back toward its spine
    curves = [c for c in chains if len(c) in (2, 3, 4, 5) and 0.95 <= wmin(c) and wmax(c) <= 1.45 and 20 < clen(c) < 62
              and dist(cpts(c)[0], bot) < 9 and cpts(c)[-1][1] > cpts(c)[0][1]]
    C = curves[0] if len(curves) == 1 else None
    # the short furrow mark beside the furrow, toward the tail
    marks = [c for c in chains if id(c) not in used and len(c) <= 3 and wmax(c) <= 1.25 and 8 < clen(c) < 40
             and abs(cpts(c)[0][1] - top[1]) < 12 and 4 < top[0] - cpts(c)[0][0] < 13
             and cbox(c)[3] - cbox(c)[1] > cbox(c)[2] - cbox(c)[0]]
    assert len(marks) <= 1, (top, len(marks))
    if marks:  # (the last, shortest pleura has none)
        D = marks[0]
        used.add(id(D))
        dp = cpts(D)
        # shade: a fine stroke carrying on down the pleura from the mark and
        # round its turn, alongside the furrow, each a different length
        fx = x_at(fp, dp[-1][1])
        if fx is not None:
            tail = []
            if C:  # the curve, moved to carry straight on from the furrow's end
                cp = cpts(C)
                tail = [(x - cp[0][0] + bot[0], y - cp[0][1] + bot[1]) for x, y in cp[1:]]
            guide = resample(catmull(resample(fp + tail, 8.0), step=1.0), 1.0)
            k0 = min(range(len(guide)), key=lambda k: abs(guide[k][1] - dp[-1][1]))
            reach = length(fp) - k0 + (0.55 * clen(C) if C else -6)
            want = reach * rng.uniform(0.5, 1.0)
            run = guide[k0 + 3:k0 + 3 + int(want)]
            if len(run) >= 8:
                d = -(fx - dp[-1][0])
                add(offset(run, d), rng.uniform(0.75, 0.9), hand=0.3, lift=0, piece=(20, 45), taper=0.45)
                n_shade += 1
    # the curve itself cut to varying lengths
    if C:
        trim(C, 0.0, rng.uniform(0.62, 1.0))
        n_curve += 1

# the upper row's short secondary strokes beside each furrow: varying lengths too
for F in upper:
    fp = cpts(F)
    lo = fp[0]  # at the axis
    marks = [c for c in chains if len(c) == 2 and 0.85 <= wmin(c) and wmax(c) <= 1.05 and 30 < clen(c) < 48
             and abs(cbox(c)[3] - lo[1]) < 6 and abs(cbox(c)[2] - lo[0]) < 12]
    if len(marks) == 1:
        trim(marks[0], 0.0, rng.uniform(0.55, 1.0))
        n_upper += 1
print(f'lower row: {n_shade} shading strokes, {n_curve} curves cut; upper row: {n_upper} strokes cut')

# ================================================================ write
out = []
for i, ln in enumerate(lines):
    if ln.strip() == '</g>':
        out += [path_line(pts, w) for pts, w in added]
        out.append(ln)
        continue
    if i in drop and i not in replace:
        continue
    if i in replace:
        out += [path_line(pts, w) for pts, w in replace[i]]
        continue
    out.append(ln)
with open(OUT, 'w') as f:
    f.write('\n'.join(out) + '\n')

# report on the whole drawing as written
rep = Pen()
for p in paths:
    if p['i'] in drop and p['i'] not in replace:
        continue
    for pts, w in replace.get(p['i'], [(p['pts'], p['w'])]):
        rep.raw(pts, w)
for pts, w in added:
    rep.raw(pts, w)
print(f'dropped {len(drop - set(replace))} paths, changed {len(replace)}, added {len(added)}')
rep.report()
