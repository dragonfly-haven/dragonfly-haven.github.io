"""16 - crow: a carrion crow / raven standing in profile, drawn in engraved flow lines.

Built on the earlier drawing (base/16-crow.svg, stored mirrored): its strokes are
read back facing right, joined into the lines they were inked as, sorted into
contour, bill, eye, legs, ground and plumage, and re-inked lighter. A third of the
plumage lines is dropped evenly (one row in three, counted in from the contours,
never two neighbouring lines), the heaviest weights are eased, and the nasal
bristles and a slightly shaggy throat are redrawn, so the bird reads as a black
bird drawn in line rather than a black blot at 1x.
"""

import re

from pen import Pen, dist, length, resample, catmull

BASE = 'base/16-crow.svg'
OUT = '../16-crow.svg'

# ------------------------------------------------------------ the base drawing

def load_chains(path):
    """The base strokes (raw coordinates face right; the file's group flips them),
    joined back into continuous inked runs."""
    t = open(path).read()
    chains = []
    for d, w in re.findall(r'<path d="([^"]*)"[^>]*stroke-width="([\d.]+)"', t):
        nums = [float(v) for v in re.findall(r'-?[\d.]+', d)]
        pts = list(zip(nums[0::2], nums[1::2]))
        w = float(w)
        if chains and dist(chains[-1]['p'][-1], pts[0]) < 0.05:
            c = chains[-1]
            c['p'].extend(pts[1:])
            c['wl'].append((w, length(pts)))
        else:
            chains.append({'p': list(pts), 'wl': [(w, length(pts))]})
    for c in chains:
        tot = sum(l for _, l in c['wl']) or 1
        c['w'] = sum(w * l for w, l in c['wl']) / tot
        c['L'] = length(c['p'])
    return chains


# chain indices in the base, by what they draw
BEAK_EDGE = {0, 2}
BEAK_INNER = {1, 55, 56, 57, 58}       # the gape and the shading on the upper mandible
BRISTLES = set(range(3, 12))            # redrawn below, fewer and finer
EYE = set(range(12, 17))
CONTOUR = {17, 49, 18, 21, 22, 20, 26, 24, 23, 28, 35, 45, 46, 47, 50, 89, 90}
FEATHER_EDGE = {19}
LEGS = {25, 27, 29, 30, 31, 32, 33, 34, 48} | set(range(36, 45)) | set(range(51, 55)) | set(range(59, 89))
GROUND = {343, 345, 347, 349, 355, 358, 361, 374, 375, 376, 380, 385, 386, 391, 393, 398, 422}
CROSS = set(range(344, 422)) - GROUND          # the belly and flank cross-hatching
THIGH = set(range(217, 243))
THROAT = (362, 440)      # y range of the shaggy throat on the breast contour
HACKLE = 15              # length of one throat hackle


def plumage_lines(chains, idx):
    """Groups plumage chains into lines: a run broken by pen lifts is one line."""
    lines = []
    for i in idx:
        c = chains[i]
        if lines and lines[-1][-1] == i - 1 and dist(chains[i - 1]['p'][-1], c['p'][0]) < 4.5:
            lines[-1].append(i)
        else:
            lines.append([i])
    return lines


def neighbours(samples, near=6.5, share=0.3, fixed=None):
    """Which sampled lines run alongside which: closer than `near` over at least
    `share` of the shorter one. Samples from index `fixed` on are edges."""
    cell = near
    grid = {}
    for k, pts in enumerate(samples):
        for x, y in pts:
            grid.setdefault((int(x // cell), int(y // cell)), []).append((k, x, y))
    nbrs = [set() for _ in samples]
    for k, pts in enumerate(samples):
        hits = {}
        for x, y in pts:
            gx, gy = int(x // cell), int(y // cell)
            seen = set()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j, qx, qy in grid.get((gx + dx, gy + dy), ()):
                        if j != k and j not in seen and (qx - x) ** 2 + (qy - y) ** 2 < near * near:
                            seen.add(j)
            for j in seen:
                hits[j] = hits.get(j, 0) + 1
        for j, h in hits.items():
            if h >= share * min(len(pts), len(samples[j])) and (fixed is None or (k < fixed and j < fixed)):
                nbrs[k].add(j)
                nbrs[j].add(k)
            elif fixed is not None and k < fixed <= j and h >= share * len(pts):
                # a line runs along an edge only if it does so for a good share of itself
                nbrs[k].add(j)
                nbrs[j].add(k)
    return nbrs


def thin(chains, lines, edges, period=3, phase=1, near=6.5):
    """Drops one line in `period`, evenly: lines are numbered in rows inward from
    the edge lines (the contours, never dropped), and every row with
    row % period == phase goes."""
    samp = [sum((resample(chains[i]['p'], 2.0) for i in ln), []) for ln in lines]
    m = len(lines)
    samp += [resample(chains[i]['p'], 2.0) for i in edges]
    nbrs = neighbours(samp, near, fixed=m)
    row = [None] * len(samp)
    queue = []
    for e in range(m, len(samp)):
        row[e] = 0
        queue.append(e)
    while True:
        while queue:
            nxt = []
            for k in queue:
                for j in nbrs[k]:
                    if row[j] is None:
                        row[j] = row[k] + 1
                        nxt.append(j)
            queue = nxt
        rest = [k for k in range(m) if row[k] is None]
        if not rest:
            break
        # a bundle no edge touches: start from its loneliest line
        k = min(rest, key=lambda k: (len(nbrs[k]), k))
        row[k] = 1
        queue = [k]
    # never two neighbouring lines (where rows counted from two edges meet)
    gone = set()
    for k in sorted(range(m), key=lambda k: (row[k], k)):
        if row[k] % period == phase and not (nbrs[k] & gone):
            gone.add(k)
    return {i for k in gone for i in lines[k]}


# ------------------------------------------------------------ drawing

def main():
    chains = load_chains(BASE)
    n = len(chains)
    special = BEAK_EDGE | BEAK_INNER | BRISTLES | EYE | CONTOUR | FEATHER_EDGE | LEGS | GROUND
    plume = [i for i in range(n) if i not in special]

    drop = set()
    body = [i for i in plume if i not in CROSS and i not in THIGH]
    edges = sorted(CONTOUR | FEATHER_EDGE | BEAK_EDGE)
    drop |= thin(chains, plumage_lines(chains, body), edges)
    drop |= thin(chains, plumage_lines(chains, sorted(CROSS)), [], period=2, phase=1)
    drop |= thin(chains, plumage_lines(chains, sorted(THIGH)), [], period=3, phase=1)
    ink = lambda idx: sum(chains[i]['L'] for i in idx)
    print('dropped: body %.2f  cross %.2f  thigh %.2f' % (
        ink(drop & set(body)) / ink(body), ink(drop & CROSS) / ink(CROSS), ink(drop & THIGH) / ink(THIGH)))

    # the whole bird a little larger, centred
    xs = [x for c in chains for x, _ in c['p']]
    ys = [y for c in chains for _, y in c['p']]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = 1.05

    def place(pts):
        return [(500 + (x - cx) * k, 505 + (y - cy) * k) for x, y in pts]

    def shade(pts):
        """0 on the lit back, 1 in the shadowed belly."""
        my = sum(y for _, y in pts) / len(pts)
        return max(0.0, min(1.0, (my - 340) / 290))

    # the throat stretch of the breast contour (chain 17 runs up from the breast to the bill)
    breast = resample(chains[17]['p'], 1.0)
    run = [0.0]
    for q0, q1 in zip(breast, breast[1:]):
        run.append(run[-1] + dist(q0, q1))
    s_top = next(run[i] for i in range(len(breast)) if breast[i][1] < THROAT[0])
    s_bot = next(run[i] for i in range(len(breast)) if breast[i][1] < THROAT[1])
    n_h = int(round((s_top - s_bot) / HACKLE))
    throat_frames = []
    for j in range(n_h):
        sj = s_bot + (j + 1) * HACKLE          # each hackle hangs from a point higher up
        i0 = min(range(len(breast)), key=lambda i: abs(run[i] - sj))
        a_, b_ = breast[min(len(breast) - 1, i0 + 3)], breast[max(0, i0 - 3)]
        L = dist(a_, b_) or 1
        t = ((b_[0] - a_[0]) / L, (b_[1] - a_[1]) / L)   # down the throat
        nrm = (-t[1], t[0])
        if nrm[0] < 0:
            nrm = (-nrm[0], -nrm[1])                   # outward, in front of the bird
        throat_frames.append((breast[i0], nrm, t))
    keep_upper = [q for q, r in zip(breast, run) if r >= s_top - 1]
    chains[17]['p'] = [q for q, r in zip(breast, run) if r <= s_bot + 1]

    pen = Pen(seed=16)
    pen.line(place(keep_upper), w=2.3, hand=0.2, lift=0.0, piece=(12, 40))
    for i, c in enumerate(chains):
        if i in drop:
            continue
        pts = place(c['p'])
        if i in BRISTLES:
            continue
        if i in BEAK_EDGE:
            w, hand = 2.2, 0.0
        elif i in BEAK_INNER:
            w, hand = 1.3 if i == 1 else 1.1, 0.0
        elif i in EYE:
            w, hand = min(2.4, c['w']), 0.0
        elif i in CONTOUR:
            w, hand = 2.3 + 0.25 * shade(c['p']), 0.2
        elif i in FEATHER_EDGE:
            w, hand = 1.5, 0.2
        elif i in LEGS:
            w, hand = max(0.9, 0.72 * c['w'] + 0.05), 0.0
        elif i in GROUND:
            w, hand = 1.0, 0.3
        elif i in CROSS:
            w, hand = 1.7, 0.2
        elif i in THIGH:
            w, hand = 1.8, 0.2
        else:
            w, hand = 1.8 + 0.65 * shade(c['p']), 0.2
        pen.line(pts, w=w, hand=hand, lift=0.0, piece=(12, 40))

    # nasal bristles: a tuft lying forward over the nostril from the forehead
    for j in range(5):
        u = j / 4
        root = (743 + 6 * u, 305 + 17 * u)
        tip = (781 - 6 * u, 312 + 14 * u)
        mid = (root[0] * 0.5 + tip[0] * 0.5, root[1] * 0.5 + tip[1] * 0.5 - 2.5)
        pen.line(place(catmull([root, mid, tip], step=2)), w=0.95, hand=0, lift=0, piece=(80, 120))

    # the shaggy throat: the throat line breaks into a few pointed hackles, each
    # hanging over the next like shingles, tips forward and down
    for j, (P, nrm, t) in enumerate(throat_frames):
        at = lambda dn, dt: (P[0] + nrm[0] * dn + t[0] * dt, P[1] + nrm[1] * dn + t[1] * dt)
        seg = HACKLE
        out = 3.2 + 1.2 * ((j * 7) % 3) / 2
        tip = at(out, seg + 2)
        pen.line(place(catmull([at(-0.8, -1), at(out * 0.45, seg * 0.55), tip], step=1.5)), w=2.2, hand=0, lift=0, piece=(80, 120))
        pen.line(place([tip, at(-1.0, seg - 2.5)]), w=1.5, hand=0, lift=0, piece=(80, 120))
        if j % 2 == 0:
            # a shaft line inside the bigger hackles
            pen.line(place(catmull([at(-6, 2), at(-2.5, seg * 0.6), at(out - 2, seg + 0.5)], step=1.5)), w=0.9, hand=0, lift=0, piece=(80, 120))

    pen.save(OUT, mirror=True)
    pen.report()


if __name__ == '__main__':
    main()
