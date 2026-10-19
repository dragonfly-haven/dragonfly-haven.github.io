#!/usr/bin/env python3
"""08 Choanoflagellate colony: a rosette of Salpingoeca rosetta.

A ball of small cells joined at their bases in the middle, each an ovoid body
with a funnel collar of fine straight microvilli at its outer end and one long
waving flagellum rising from inside the collar, all pointing outward.

Built in 3D: cells sit on a sphere, are seen in mild perspective, and hide one
another with a small depth test (each body is a chain of spheres along its
axis), so cells on the far side show only where they peek out round the rim.
"""

import math

import numpy as np

from pen import Pen

SEED = 8
pen = Pen(seed=SEED)
rng = np.random.default_rng(SEED)

CX, CY = 500.0, 500.0
FOC = 2600.0                     # viewer distance (mild perspective)
N_CELLS = 54
R0 = 25.0                        # where the cell bases meet, from the centre
SHADE = np.array([0.55, 0.83])   # light from upper left: shadows fall lower right
SHADE /= np.linalg.norm(SHADE)


# ---------------------------------------------------------------- 3D helpers

def unit(v):
    return v / np.linalg.norm(v)


def rot(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def proj(P):
    """3D point (x right, y down, z toward the viewer) -> (sx, sy, z, scale)."""
    k = FOC / (FOC - P[2])
    return (CX + P[0] * k, CY + P[1] * k, P[2], k)


def resample3(arr, step):
    """Resamples a polyline of (x, y, z) rows by its 2D length, carrying z."""
    d = np.hypot(np.diff(arr[:, 0]), np.diff(arr[:, 1]))
    s = np.concatenate([[0], np.cumsum(d)])
    if s[-1] < 1e-6:
        return arr[:1]
    n = max(2, int(s[-1] / step) + 1)
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, arr[:, j]) for j in range(3)], axis=1)


def hull(points):
    """2D convex hull (monotone chain) of rows (x, y, z); keeps z."""
    pts = sorted(points, key=lambda p: (p[0], p[1]))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ---------------------------------------------------------------- the cells

def fib_sphere(n):
    ga = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        out.append(np.array([r * math.cos(ga * i), y, r * math.sin(ga * i)]))
    return out


def _prof(s):
    t = math.acos(1 - 2 * s)
    return math.sin(t) * (0.28 + 0.72 * s) ** 1.2


_PMAX = max(_prof(s) for s in np.linspace(0, 1, 400))


def profile(s):
    """Body radius (as a share of half its width) at axial share s (0 base, 1 apex):
    a pear, narrow at the base where the cells meet, broad under the collar."""
    return _prof(s) / _PMAX


R = rot(0.35, -0.5, 0.2)
cells = []
for i, d0 in enumerate(fib_sphere(N_CELLS)):
    d = unit(R @ unit(d0 + rng.normal(0, 0.06, 3)))
    a = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit(np.cross(d, a))
    v = np.cross(d, u)
    L = 200 * rng.uniform(0.95, 1.04)
    W = 72 * rng.uniform(0.92, 1.06)
    c = dict(id=i, d=d, u=u, v=v, L=L, W=W, r0=R0 * rng.uniform(0.8, 1.2))
    # the body as a chain of spheres along the axis
    sph = []
    for s in np.linspace(0.03, 0.97, 16):
        C = (c['r0'] + s * L) * d
        rho = 0.5 * W * profile(s)
        sx, sy, sz, k = proj(C)
        sph.append((sx, sy, sz, rho * k, rho))
    c['sph'] = np.array(sph)
    # the collar, for hiding other cells' collars and flagella behind it
    c['cbase'] = (c['r0'] + 0.93 * L) * d
    c['Lc'] = 0.44 * L
    c['rb'], c['rt'] = 0.13 * W, 0.46 * W
    csph = []
    for s in np.linspace(0.08, 0.9, 10):
        C = c['cbase'] + s * c['Lc'] * d
        rho = 0.88 * (c['rb'] + s * (c['rt'] - c['rb']))
        sx, sy, sz, k = proj(C)
        csph.append((sx, sy, sz, rho * k, rho))
    c['csph'] = np.array(csph)
    cx_ = c['csph'][:, 0]; cy_ = c['csph'][:, 1]; cr_ = c['csph'][:, 3]
    c['cbbox'] = ((cx_ - cr_).min(), (cy_ - cr_).min(), (cx_ + cr_).max(), (cy_ + cr_).max())
    ring = []
    for sx, sy, sz, sr, _ in sph:
        for a_ in np.linspace(0, 2 * math.pi, 40, endpoint=False):
            ring.append((sx + sr * math.cos(a_), sy + sr * math.sin(a_), sz))
    c['outline'] = np.array(hull(ring))
    c['bbox'] = (c['outline'][:, 0].min(), c['outline'][:, 1].min(), c['outline'][:, 0].max(), c['outline'][:, 1].max())
    c['zc'] = proj((c['r0'] + 0.75 * L) * d)[2]
    c['c2'] = np.array(proj((c['r0'] + 0.55 * L) * d)[:2])
    cells.append(c)


def front_depth(c, P, key='sph'):
    """Depth of the front surface of cell c's body (or collar) at 2D points P (n, 2); -inf where it does not cover them."""
    S = c[key]
    d2 = (P[:, 0:1] - S[None, :, 0]) ** 2 + (P[:, 1:2] - S[None, :, 1]) ** 2
    r2 = S[None, :, 3] ** 2
    cover = d2 < r2
    dz = np.sqrt(np.clip(r2 - d2, 0, None)) / (S[None, :, 3] / S[None, :, 4])
    depth = np.where(cover, S[None, :, 2] + dz, -1e9)
    return depth.max(axis=1)


def hidden(P, Z, skip=None, owner=None, collars=False):
    """Which points are hidden. Strokes on a body (skip = that cell) are hidden
    by whole bodies nearer the eye (painter's order, so cells stay whole);
    collars and flagella by the body surfaces in front of them; with
    collars=True also by the collar cone of any cell but owner."""
    x0, y0, x1, y1 = P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()
    mask = np.zeros(len(P), bool)
    zown = cells[skip]['zc'] if skip is not None else None
    for c in cells:
        if c['id'] != skip:
            bx0, by0, bx1, by1 = c['bbox']
            if not (bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1):
                if zown is not None:
                    if c['zc'] > zown:
                        mask |= front_depth(c, P) > -1e8
                else:
                    mask |= Z < front_depth(c, P) - 0.5
        if (collars or zown is not None) and c['id'] != owner:
            bx0, by0, bx1, by1 = c['cbbox']
            if not (bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1):
                mask |= Z < front_depth(c, P, 'csph') - 0.5
    return mask


def ink(pts3, w, skip=None, owner=None, collars=False, min_run=2.0, **kw):
    """Inks a stroke given as (x, y, z) rows, leaving out what bodies (and collars) in front hide."""
    arr = np.asarray(pts3, float)
    if len(arr) < 2:
        return
    fine = resample3(arr, 1.2)
    hid = hidden(fine[:, :2], fine[:, 2], skip, owner, collars)
    run = []
    for p, h in zip(fine, hid):
        if not h:
            run.append((p[0], p[1]))
        else:
            if len(run) > 1 and _len(run) >= min_run:
                pen.line(run, w=w, occlude=False, **kw)
            run = []
    if len(run) > 1 and _len(run) >= min_run:
        pen.line(run, w=w, occlude=False, **kw)


def _len(run):
    return sum(math.hypot(run[i + 1][0] - run[i][0], run[i + 1][1] - run[i][1]) for i in range(len(run) - 1))


def surf(c, pts2):
    """2D points on cell c's body, with the depth of its front surface."""
    P = np.asarray(pts2, float)
    z = front_depth(c, P)
    return np.column_stack([P, z])


def inside_poly(P, poly):
    x, y = P[:, 0], P[:, 1]
    hit = np.zeros(len(P), bool)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cond = (y0 > y) != (y1 > y)
        with np.errstate(divide='ignore', invalid='ignore'):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0 + 1e-12)
        hit ^= cond & (x < xi)
    return hit


# ---------------------------------------------------------------- drawing

def draw_body(c):
    d = c['d']
    facing = d[2]                        # +1 apex toward viewer, -1 away
    depth = c['zc']
    o = c['outline']
    # contour, started at a random point and closed with a small overlap
    k0 = int(rng.integers(len(o)))
    loop = np.concatenate([o[k0:], o[:k0], o[k0:k0 + 3]])
    loop = resample3(loop, 3.0)
    w = 1.9 if depth > 40 else (1.65 if depth > -60 else 1.4)
    ink(loop, w, skip=c['id'], hand=0.6, lift=0.08)

    # shading: arcs following the outline on the shadow side, more on deeper cells
    P = resample3(np.concatenate([o, o[:1]]), 2.0)[:-1, :2]
    cen = P.mean(axis=0)
    t = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    nrm = np.column_stack([t[:, 1], -t[:, 0]])
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-9
    flip = ((P - cen) * nrm).sum(axis=1) < 0
    nrm[flip] *= -1
    off2 = c['c2'] - np.array([CX, CY])
    rad = np.linalg.norm(off2)
    sd = SHADE.copy()
    if rad > 1:
        sd = unit(0.55 * SHADE + 0.45 * (-off2 / rad) * min(1.0, rad / 160))
    nk = 1 if depth > 60 else (2 if depth > -20 else 3)
    for k in range(1, nk + 1):
        inset = 3.0 + 5.6 * k
        Q = P - nrm * inset
        thr = -0.05 + 0.22 * (k - 1)
        keep = (nrm @ sd) > thr
        # stay clear of narrow parts where the inset would cross itself
        dmin = np.sqrt(((Q[:, None, :] - P[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
        keep &= dmin > inset * 0.8
        keep &= inside_poly(Q, P)
        # runs of kept points (cyclic)
        idx = np.where(keep)[0]
        if len(idx) < 3:
            continue
        runs, cur = [], [idx[0]]
        for a, b in zip(idx[:-1], idx[1:]):
            if b == a + 1:
                cur.append(b)
            else:
                runs.append(cur)
                cur = [b]
        runs.append(cur)
        if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(P) - 1:
            runs[0] = runs[-1] + runs[0]
            runs.pop()
        for r in runs:
            if len(r) < 4:
                continue
            seg = Q[r]
            # the hand stops a little short of each end
            n = len(seg)
            a0 = int(n * rng.uniform(0.0, 0.12))
            a1 = n - int(n * rng.uniform(0.0, 0.12))
            seg = seg[a0:a1]
            if len(seg) < 3:
                continue
            ink(surf(c, seg), 0.72 * rng.uniform(0.9, 1.1), skip=c['id'], hand=0.35, lift=0.05, piece=(40, 120))



def draw_collar(c):
    """The collar: a funnel of straight microvilli round the flagellum's base.
    Seen from the side only its near half is drawn, so the lines fan evenly
    from edge to edge; seen from above, the whole ring and its mouth."""
    d, u, v, W = c['d'], c['u'], c['v'], c['W']
    base = c['cbase']
    tip = base + c['Lc'] * d
    rb, rt = c['rb'], c['rt']
    M = 16
    ph = rng.uniform(0, 2 * math.pi)
    open_mouth = d[2] > 0.45
    # the screen direction across the collar, to weight its two edges
    ax2 = np.array(proj(tip)[:2]) - np.array(proj(base)[:2])
    across = np.array([-ax2[1], ax2[0]])
    across = across / (np.linalg.norm(across) + 1e-9)
    for i in range(M):
        phi = ph + 2 * math.pi * i / M + rng.normal(0, 0.03)
        e = math.cos(phi) * u + math.sin(phi) * v
        if not open_mouth and abs(d[2]) < 0.6 and e[2] < -0.12:
            continue
        a = base + rb * e
        b = tip + rt * e * rng.uniform(0.97, 1.03)
        pts = [proj(a + (b - a) * t)[:3] for t in np.linspace(0, 1, 10)]
        side = abs(float(e[0] * across[0] + e[1] * across[1]))
        w = 0.74 + 0.36 * side ** 8
        ink(pts, w * rng.uniform(0.95, 1.05), owner=c['id'], collars=True, min_run=4.0, hand=0.12, lift=0.0, piece=(60, 140))
    # the mouth: a whole ring when we look into it, else its near half
    a0 = rng.uniform(0, 2 * math.pi)
    ring = []
    for t in np.linspace(a0, a0 + 2 * math.pi + 0.15, 72):
        e = math.cos(t) * u + math.sin(t) * v
        if open_mouth or e[2] > -0.05:
            ring.append(proj(tip + rt * e)[:3])
        elif len(ring) > 2:
            ink(ring, 0.72, owner=c['id'], collars=True, min_run=5.0, hand=0.15, lift=0.1)
            ring = []
        else:
            ring = []
    if len(ring) > 2:
        ink(ring, 0.72, owner=c['id'], collars=True, min_run=5.0, hand=0.15, lift=0.1)


def draw_flagellum(c):
    d, u, v, L = c['d'], c['u'], c['v'], c['L']
    apex = (c['r0'] + 0.98 * L) * d
    FL = 1.06 * L * rng.uniform(0.94, 1.06)
    ps = rng.uniform(0, 2 * math.pi)
    # each beats in a plane turned mostly across the line of sight, so its waves show
    side = np.cross(d, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(side) > 0.3:
        side = unit(side)
        tilt = rng.normal(0, 0.4)
        e1 = math.cos(tilt) * side + math.sin(tilt) * np.cross(d, side)
    else:
        e1 = math.cos(ps) * u + math.sin(ps) * v
    e2 = np.cross(d, e1)
    # flagella aimed at the eye would read as zigzags: they wave less and
    # bend more, so they show as a curve swinging out to one side
    toward = max(0.0, d[2])
    amp = 0.065 * FL * float(np.clip(1.75 - 1.25 * toward, 0.5, 1.0))
    waves = rng.uniform(1.4, 1.9)
    ph = rng.uniform(0, 2 * math.pi)
    bend = rng.normal(0, 0.08) * FL
    if toward > 0.65:
        # swing outward, away from the middle of the ball
        out = np.array([d[0], d[1], 0.0])
        if np.linalg.norm(out) < 0.15:
            out = np.array([math.cos(ps), math.sin(ps), 0.0])
        out = out - (out @ d) * d
        e2 = unit(out)
        bend = 0.4 * (toward - 0.65) / 0.35 * FL * rng.uniform(0.8, 1.1)
    pts = []
    for t in np.linspace(0, 1, 90):
        g = min(1.0, t / 0.35)
        lat = amp * g * g * (3 - 2 * g) * math.sin(2 * math.pi * waves * t + ph)
        P = apex + t * FL * d + lat * e1 + bend * t * t * e2
        pts.append(proj(P)[:3])
    ink(pts, 1.35, owner=c['id'], collars=True, min_run=18.0, hand=0.3, lift=0.04, taper=0.5, piece=(30, 80))


def zbuf(P):
    """Depth of the body surface seen at 2D points P (painter's order); -inf where there is none."""
    z = np.full(len(P), -1e9)
    top = np.full(len(P), -1e9)
    for c in cells:
        fd = front_depth(c, P)
        m = (fd > -1e8) & (c['zc'] > top)
        z[m] = fd[m]
        top[m] = c['zc']
    return z


ENV = R0 + 200 * 0.98


def crevices(angle, extra, w=0.7):
    """Hatching where the eye looks deep into the ball, between the domes of the
    outer cells (deeper and on the shadow side: more)."""
    a = math.radians(angle)
    dr = np.array([math.cos(a), math.sin(a)])
    nr = np.array([-dr[1], dr[0]])
    sp = 5.6
    for off in np.arange(-260, 260, sp):
        off = off + rng.normal(0, 0.5)
        t = np.arange(-270, 270, 1.5)
        P = np.array([CX, CY]) + off * nr + t[:, None] * dr
        z = zbuf(P)
        rel = P - np.array([CX, CY])
        rho = np.linalg.norm(rel, axis=1)
        env = np.sqrt(np.clip(ENV ** 2 - rho ** 2, 0, None))
        delta = env - z
        side = (rel @ SHADE) / (rho + 1e-9) * np.clip(rho / 120, 0, 1)
        T = 40 + extra - 18 * side
        keep = (z > -1e8) & (delta > T)
        idx = np.where(keep)[0]
        if not len(idx):
            continue
        runs, cur = [], [idx[0]]
        for i0, i1 in zip(idx[:-1], idx[1:]):
            if i1 == i0 + 1:
                cur.append(i1)
            else:
                runs.append(cur)
                cur = [i1]
        runs.append(cur)
        for r in runs:
            if len(r) < 4:
                continue
            seg = np.column_stack([P[r], z[r]])
            ink(seg, w * rng.uniform(0.9, 1.1), collars=True, min_run=5.0, hand=0.3, lift=0.04, piece=(40, 120))


order = sorted(cells, key=lambda c: -c['zc'])
for c in order:
    draw_flagellum(c)
    draw_collar(c)
    draw_body(c)

crevices(42, 0)
crevices(-38, 40)

pen.save('../08-choanoflagellate-colony.svg', mirror=False)
pen.report()
