#!/usr/bin/env python3
"""08 Choanoflagellate colony: a rosette of Salpingoeca rosetta.

A ball of small cells packed together, their narrow bases meeting in the
middle. Each cell is an egg-shaped body whose broad outer end carries a collar
of straight microvilli, slightly flared, with one long waving flagellum rising
from the middle of the collar; all point outward.

Built in 3D (orthographic): every body is a pear made of two half-ellipsoids,
every collar a truncated cone. A depth buffer over the square says which
surface is seen where, so the outer ends of the cells pack into a ball of
domes, cells foreshorten from end-on in the middle to profile at the rim, and
the far side shows only as collars and flagella peeking round the edge.
Outlines are traced from that buffer; bodies are shaded with rings that follow
each dome, set where its surface turns from the light or toward the limb.
"""

import math

import numpy as np

from pen import Pen

SEED = 8
pen = Pen(seed=SEED)
rng = np.random.default_rng(SEED)

CX, CY = 500.0, 500.0
N_CELLS = 50
R_APEX = 275.0                    # centre to the tip of each cell
LIGHT = np.array([-0.45, -0.6, 0.66])
LIGHT /= np.linalg.norm(LIGHT)
EZ = np.array([0.0, 0.0, 1.0])
H = 1000                          # depth buffer: one cell per drawing unit


def unit(v):
    return v / np.linalg.norm(v)


def rot(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def scr(P):
    """3D (x right, y down, z toward the eye, origin at the ball's centre) -> drawing x, y."""
    return CX + P[..., 0], CY + P[..., 1]


def fib_sphere(n):
    ga = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        out.append(np.array([r * math.cos(ga * i), y, r * math.sin(ga * i)]))
    return out


# ---------------------------------------------------------------- the cells

cells = []
R = rot(0.42, -0.31, 0.15)
for i, d0 in enumerate(fib_sphere(N_CELLS)):
    d = unit(R @ unit(d0 + rng.normal(0, 0.035, 3)))
    a = EZ if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = unit(np.cross(d, a))
    e2 = np.cross(d, e1)
    W = 105 * rng.uniform(0.96, 1.04)
    b = W / 2
    apex = R_APEX * rng.uniform(0.98, 1.02)
    a_up = 0.6 * W
    sh = apex - a_up                         # shoulder: where the egg is widest
    a_low = sh - 12.0
    c = dict(id=i, d=d, e1=e1, e2=e2, W=W, b=b, a_up=a_up, a_low=a_low, C=sh * d, apex=apex)
    Pd = np.outer(d, d)
    c['M_up'] = Pd / a_up ** 2 + (np.eye(3) - Pd) / b ** 2
    c['M_low'] = Pd / a_low ** 2 + (np.eye(3) - Pd) / b ** 2
    # collar: base ring where the dome is rb wide, flaring 1.3x, about a body long
    rb = 0.25 * W
    ub = a_up * math.sqrt(1 - (rb / b) ** 2)
    c['rb'], c['rt'] = rb, 1.38 * rb
    c['cbase'] = c['C'] + ub * d
    c['Lc'] = 0.62 * W
    c['ctip'] = c['cbase'] + c['Lc'] * d
    cells.append(c)


def pear_depth(c, X, Y):
    """Front surface depth (and which half) of cell c's body at drawing points X, Y; -inf off it."""
    C, d = c['C'], c['d']
    q0 = np.stack([X - CX - C[0], Y - CY - C[1], np.full_like(X, -C[2])], axis=-1)
    best = np.full(X.shape, -np.inf)
    for M, sgn in ((c['M_up'], 1), (c['M_low'], -1)):
        A = M[2, 2]
        B = q0 @ M[2]
        C0 = np.einsum('...i,ij,...j->...', q0, M, q0) - 1
        disc = B * B - A * C0
        ok = disc >= 0
        sq = np.sqrt(np.where(ok, disc, 0))
        for Z in ((-B + sq) / A, (-B - sq) / A):
            ax = q0 @ d + Z * d[2]
            valid = ok & (sgn * ax >= -1e-6)
            best = np.where(valid & (Z > best), Z, best)
    return best


def pear_normal(c, P):
    """Outward normal of cell c's body at surface points P (n, 3)."""
    q = P - c['C']
    ax = q @ c['d']
    n = np.where((ax >= 0)[:, None], q @ c['M_up'], q @ c['M_low'])
    return n / np.linalg.norm(n, axis=1)[:, None]


# ---------------------------------------------------------------- depth buffers

body_z = np.full((H, H), -np.inf, np.float32)
body_id = np.full((H, H), -1, np.int16)
col_z = np.full((H, H), -np.inf, np.float32)
col_id = np.full((H, H), -1, np.int16)


def box(pts, pad=3):
    x0 = int(max(0, math.floor(min(p[0] for p in pts) - pad)))
    x1 = int(min(H - 1, math.ceil(max(p[0] for p in pts) + pad)))
    y0 = int(max(0, math.floor(min(p[1] for p in pts) - pad)))
    y1 = int(min(H - 1, math.ceil(max(p[1] for p in pts) + pad)))
    return x0, x1, y0, y1


def hull2(points):
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def inside_poly(X, Y, poly):
    hit = np.zeros(X.shape, bool)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cond = (y0 > Y) != (y1 > Y)
        xi = x0 + (Y - y0) * (x1 - x0) / ((y1 - y0) if y1 != y0 else 1e-12)
        hit ^= cond & (X < xi)
    return hit


def ring3(center, r, c, n=48, a0=0.0):
    t = np.linspace(a0, a0 + 2 * math.pi, n, endpoint=False)
    return center + r * (np.cos(t)[:, None] * c['e1'] + np.sin(t)[:, None] * c['e2'])


for c in cells:
    d = c['d']
    ends = [c['C'] + c['a_up'] * d, c['C'] - c['a_low'] * d]
    ext = [scr(e) for e in ends]
    pts = [(x + sx * c['b'], y + sy * c['b']) for x, y in ext for sx in (-1, 1) for sy in (-1, 1)]
    x0, x1, y0, y1 = box(pts)
    X, Y = np.meshgrid(np.arange(x0, x1 + 1, dtype=float), np.arange(y0, y1 + 1, dtype=float))
    z = pear_depth(c, X, Y)
    sub = body_z[y0:y1 + 1, x0:x1 + 1]
    win = z > sub
    sub[win] = z[win]
    body_id[y0:y1 + 1, x0:x1 + 1][win] = c['id']
    # the collar as an opaque cone for what lies behind it
    rp = np.concatenate([ring3(c['cbase'], c['rb'], c), ring3(c['ctip'], c['rt'], c)])
    xs, ys = scr(rp)
    poly = hull2([(float(x), float(y)) for x, y in zip(xs, ys)])
    x0, x1, y0, y1 = box(poly)
    X, Y = np.meshgrid(np.arange(x0, x1 + 1, dtype=float), np.arange(y0, y1 + 1, dtype=float))
    inn = inside_poly(X, Y, poly)
    b2 = np.array(scr(c['cbase']))
    t2 = np.array(scr(c['ctip']))
    seg = t2 - b2
    L2 = float(seg @ seg)
    if L2 > 1:
        t = np.clip(((X - b2[0]) * seg[0] + (Y - b2[1]) * seg[1]) / L2, 0, 1)
    else:
        t = np.ones_like(X)
    zax = c['cbase'][2] + t * (c['ctip'][2] - c['cbase'][2])
    rr = c['rb'] + t * (c['rt'] - c['rb'])
    zc = np.where(inn, zax + 0.6 * rr * math.sqrt(max(0.0, 1 - d[2] ** 2)), -np.inf)
    sub = col_z[y0:y1 + 1, x0:x1 + 1]
    win = zc > sub
    sub[win] = zc[win]
    col_id[y0:y1 + 1, x0:x1 + 1][win] = c['id']


def look(X, Y):
    """Buffer indices for drawing points."""
    i = np.clip(np.rint(Y).astype(int), 0, H - 1)
    j = np.clip(np.rint(X).astype(int), 0, H - 1)
    return i, j


# ---------------------------------------------------------------- strokes

def runs_of(mask):
    out, cur = [], []
    for k, m in enumerate(mask):
        if m:
            cur.append(k)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def plen(P):
    return float(np.hypot(*np.diff(P, axis=0).T).sum()) if len(P) > 1 else 0.0


def dense(P3, step=1.0):
    """Resamples (n, 3) 3D points so their drawing-plane spacing is about step."""
    P3 = np.asarray(P3, float)
    d2 = np.hypot(np.diff(P3[:, 0]), np.diff(P3[:, 1]))
    s = np.concatenate([[0], np.cumsum(d2)])
    if s[-1] < 1e-6:
        return P3[:1]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.stack([np.interp(t, s, P3[:, j]) for j in range(3)], axis=1)


def draw_runs(P2, keep, w, min_len=4.0, **kw):
    for r in runs_of(keep):
        if len(r) < 2:
            continue
        seg = P2[r]
        if plen(seg) >= min_len:
            pen.line([tuple(p) for p in seg], w=w, occlude=False, **kw)


# ---------------------------------------------------------------- outlines from the buffer

_SEG = {1: [(3, 2)], 2: [(2, 1)], 3: [(3, 1)], 4: [(0, 1)], 5: [(3, 0), (2, 1)], 6: [(0, 2)],
        7: [(3, 0)], 8: [(0, 3)], 9: [(0, 2)], 10: [(0, 1), (3, 2)], 11: [(0, 1)], 12: [(3, 1)],
        13: [(2, 1)], 14: [(3, 2)]}


def trace(mask):
    """Marching squares: the boundary loops of a boolean mask, as (row, col) polylines."""
    m = np.pad(mask, 1).astype(np.int8)
    idx = m[:-1, :-1] * 8 + m[:-1, 1:] * 4 + m[1:, 1:] * 2 + m[1:, :-1]
    segs = []
    for i, j in zip(*np.nonzero((idx > 0) & (idx < 15))):
        mid = {0: (i, j + 0.5), 1: (i + 0.5, j + 1), 2: (i + 1, j + 0.5), 3: (i + 0.5, j)}
        for a, b in _SEG[int(idx[i, j])]:
            segs.append((mid[a], mid[b]))
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    loops = []
    seen = set()
    for start in adj:
        if start in seen:
            continue
        loop = [start]
        seen.add(start)
        prev, cur = None, start
        while True:
            nb = [n for n in adj[cur] if n != prev and n not in seen]
            if not nb:
                break
            prev, cur = cur, nb[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(np.array(loop, float) - 1.0)
    return loops


def smooth(P, k=3, closed=True):
    if len(P) < 2 * k + 2:
        return P
    out = np.zeros_like(P)
    for s in range(-k, k + 1):
        out += np.roll(P, s, axis=0) if closed else P
    return out / (2 * k + 1)


def draw_outlines():
    for c in cells:
        cid = c['id']
        ys, xs = np.nonzero(body_id == cid)
        if len(xs) < 20:
            continue
        y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
        y0, x0 = max(0, y0), max(0, x0)
        mask = body_id[y0:y1, x0:x1] == cid
        for loop in trace(mask):
            if len(loop) < 12:
                continue
            P = smooth(smooth(np.column_stack([loop[:, 1] + x0, loop[:, 0] + y0]), 5), 4)
            t = np.roll(P, -2, axis=0) - np.roll(P, 2, axis=0)
            n = np.column_stack([t[:, 1], -t[:, 0]])
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
            # make n point out of the region
            io, jo = look(P[:, 0] + 2.5 * n[:, 0], P[:, 1] + 2.5 * n[:, 1])
            flip = body_id[io, jo] == cid
            if flip.mean() > 0.5:
                n = -n
            io, jo = look(P[:, 0] + 2.5 * n[:, 0], P[:, 1] + 2.5 * n[:, 1])
            ii, ji = look(P[:, 0] - 2.0 * n[:, 0], P[:, 1] - 2.0 * n[:, 1])
            oid = body_id[io, jo]
            zo = body_z[io, jo]
            zi = body_z[ii, ji]
            sil = oid == -1
            occ = (oid != -1) & (zi > zo + 12)
            cre = (oid != -1) & (np.abs(zi - zo) <= 12) & (oid > cid)
            under = col_z[ii, ji] > zi + 0.5
            ip, jp = look(P[:, 0], P[:, 1])
            under |= col_z[ip, jp] > body_z[ip, jp] + 0.5
            kind = np.where(sil, 3, np.where(occ, 2, np.where(cre, 1, 0)))
            kind[under] = 0
            # start somewhere the line is drawn, so a loop does not split at index 0
            if (kind == 0).any():
                s0 = int(np.argmax(kind == 0))
                P, kind = np.roll(P, -s0, axis=0), np.roll(kind, -s0)
            else:
                P, kind = np.vstack([P, P[:4]]), np.concatenate([kind, kind[:4]])
            # merge into runs of drawn line; weight by the heaviest kind in the run
            for r in runs_of(kind > 0):
                seg = P[r]
                if plen(seg) < 4:
                    continue
                k = np.bincount(kind[r], minlength=4)
                kk = int(np.argmax(k[1:]) + 1)
                w = {3: 2.1, 2: 1.75, 1: 1.25}[kk]
                pen.line([tuple(p) for p in seg[::2]] + [tuple(seg[-1])], w=w, occlude=False, hand=0.5, lift=0.08)


# ---------------------------------------------------------------- shading

def shade_of(n, c):
    """0 lit ... 1 dark: the cell's own surface against the light, plus the
    ball's (darker on its shadow side and toward its limb)."""
    lam = np.clip(n @ LIGHT, 0, None)
    own = 1 - np.clip(0.62 * lam + 0.38 * np.clip(n[:, 2], 0, None), 0, 1)
    d = c['d']
    ball = 1 - min(1.0, 0.6 * max(0.0, float(d @ LIGHT)) + 0.4 * max(0.0, float(d[2])))
    return 0.72 * own + 0.28 * ball


def seen_on_body(c, P3):
    X, Y = scr(P3)
    i, j = look(X, Y)
    ok = (body_id[i, j] == c['id']) & (P3[:, 2] >= body_z[i, j] - 6.0) & ~(col_z[i, j] > P3[:, 2] + 0.5)
    if 'nuc' in c:
        nx, ny, nr = c['nuc']
        ok &= np.hypot(X - nx, Y - ny) > nr
    return ok


def draw_shading(c):
    """Rings round the cell's axis, drawn where its surface turns from the light,
    spaced evenly as seen; a few strokes along the axis cross the darkest."""
    d, b = c['d'], c['b']
    n_phi = 160
    phis = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)
    cosr, sinr = np.cos(phis)[:, None], np.sin(phis)[:, None]

    def ring_at(u):
        a = c['a_up'] if u >= 0 else c['a_low']
        rho = b * math.sqrt(max(0.0, 1 - (u / a) ** 2))
        return c['C'] + u * d + rho * (cosr * c['e1'] + sinr * c['e2'])

    u_top = (c['cbase'] - c['C']) @ d
    us = []
    last = None
    for u in np.arange(u_top, -0.75 * c['a_low'], -0.5):
        P = ring_at(u)
        if last is None:
            us.append(u)
            last = P
            continue
        dd = np.hypot(P[:, 0] - last[:, 0], P[:, 1] - last[:, 1])
        if dd.min() >= 5.6:
            us.append(u)
            last = P
    jit = rng.uniform(-0.04, 0.04, len(us))
    for k, u in enumerate(us[1:], 1):
        P = ring_at(u)
        n = pear_normal(c, P)
        sh = shade_of(n, c)
        thr = 0.3 + jit[k]
        vis = seen_on_body(c, P)
        keep = vis & (sh > thr)
        P2 = np.column_stack(scr(P))
        # roll so a run does not split at index 0
        s0 = int(np.argmax(~keep)) if (~keep).any() else 0
        P2, keep, sh = np.roll(P2, -s0, axis=0), np.roll(keep, -s0), np.roll(sh, -s0)
        for r in runs_of(keep):
            if len(r) < 3:
                continue
            seg = P2[r]
            if plen(seg) < 5:
                continue
            w = 0.62 + 0.3 * float(np.clip((sh[r].mean() - 0.45) / 0.5, 0, 1))
            pen.line([tuple(p) for p in seg], w=w, occlude=False, hand=0.3, lift=0.04, piece=(40, 120))
    # cross strokes along the axis on the darkest side
    n_m = int(2 * math.pi * b / 6.5)
    for m in range(n_m):
        phi = 2 * math.pi * (m + rng.uniform(0.3, 0.7)) / n_m
        uu = np.linspace(u_top, -0.6 * c['a_low'], 80)
        P = np.array([c['C'] + u * d + b * math.sqrt(max(0.0, 1 - (u / (c['a_up'] if u >= 0 else c['a_low'])) ** 2))
                      * (math.cos(phi) * c['e1'] + math.sin(phi) * c['e2']) for u in uu])
        sh = shade_of(pear_normal(c, P), c)
        keep = seen_on_body(c, P) & (sh > 0.64 + rng.uniform(-0.03, 0.03))
        draw_runs(np.column_stack(scr(P)), keep, 0.62 * rng.uniform(0.95, 1.05), min_len=6, hand=0.3, lift=0.04)


def draw_inside(c):
    """A small nucleus (with its nucleolus) and a food vacuole or two, seen
    through the lit flank of cells that are turned partly sideways."""
    d = c['d']
    if abs(d[2]) > 0.62:
        return
    lp = LIGHT - (LIGHT @ d) * d
    if np.linalg.norm(lp) < 0.2:
        return
    lp = unit(lp)
    rn = 0.105 * c['W']
    t = np.linspace(0, 2 * math.pi, 40, endpoint=False)

    def clear(x, y, r):
        ring = np.column_stack([x + r * np.cos(t), y + r * np.sin(t)])
        i, j = look(ring[:, 0], ring[:, 1])
        return bool(((body_id[i, j] == c['id']) & ~(col_z[i, j] > body_z[i, j])).all())

    for u, off, turn in ((-0.16, 0.2, 0.0), (-0.12, 0.22, 0.0), (-0.18, 0.18, 0.6), (-0.18, 0.18, -0.6), (-0.06, 0.3, 0.0), (-0.06, 0.3, 0.7), (-0.06, 0.3, -0.7)):
        sd = math.cos(turn) * lp + math.sin(turn) * np.cross(d, lp)
        Nc = c['C'] + u * c['a_low'] * d + off * c['b'] * sd
        x, y = scr(Nc)
        if clear(x, y, rn + 3):
            break
    else:
        return
    c['nuc'] = (x, y, rn + 2.5)
    a0 = rng.uniform(0, 2 * math.pi)
    tt = np.linspace(a0, a0 + 2 * math.pi + 0.25, 44)
    pen.line([(x + rn * math.cos(q), y + rn * 0.88 * math.sin(q)) for q in tt], w=0.62, occlude=False, hand=0.35, lift=0.45,
             piece=(6, 14))
    # food vacuoles toward the base
    for k in range(2):
        V = Nc - rng.uniform(0.18, 0.28) * c['a_low'] * d + rng.uniform(-0.25, 0.25) * c['b'] * np.cross(d, sd)
        vx, vy = scr(V)
        rv = rng.uniform(3.0, 4.2)
        if not clear(vx, vy, rv + 3):
            continue
        tt = np.linspace(0, 2 * math.pi + 0.3, 22)
        pen.line([(vx + rv * math.cos(q), vy + rv * math.sin(q)) for q in tt], w=0.85, occlude=False, hand=0, lift=0)


# ---------------------------------------------------------------- collars and flagella

def collar_seen(c, P3):
    X, Y = scr(P3)
    i, j = look(X, Y)
    behind_body = P3[:, 2] < body_z[i, j] - 1.0
    other = (col_id[i, j] != -1) & (col_id[i, j] != c['id'])
    behind_collar = other & (P3[:, 2] < col_z[i, j] - 0.5)
    return ~(behind_body | behind_collar)


def draw_collar(c):
    """Straight microvilli with staggered tips. Seen from the side only the near
    half, the mouth left open; looked into, a broken mouth ring (and, end-on,
    the base ring with short ticks round the rim). Collars of cells on the far
    side are fewer, lighter, shorter lines."""
    d = c['d']
    open_mouth = d[2] > 0.5
    endon = d[2] > 0.8
    back = d[2] < -0.1
    if d[2] < -0.28:
        return                             # far side: hidden but for a stub, so the ball's edge stays clean
    M = 14
    ph = rng.uniform(0, 2 * math.pi)
    b2 = np.array(scr(c['cbase']))
    t2 = np.array(scr(c['ctip']))
    ax2 = t2 - b2
    across = np.array([-ax2[1], ax2[0]])
    across = across / (np.linalg.norm(across) + 1e-9)
    for k in range(M):
        if back and k % 2:
            continue
        phi = ph + 2 * math.pi * k / M + rng.normal(0, 0.03)
        e = math.cos(phi) * c['e1'] + math.sin(phi) * c['e2']
        if not open_mouth and e[2] < -0.12:
            continue                       # the far half, behind the near one
        A = c['cbase'] + c['rb'] * e
        B = c['ctip'] + c['rt'] * e * rng.uniform(0.97, 1.03) + rng.uniform(-0.02, 0.07) * c['Lc'] * d
        if endon:
            A = A + 0.55 * (B - A)         # seen end-on: short ticks round the rim
        if d[2] < -0.3:
            B = A + 0.72 * (B - A)
        P = dense([A, B], 1.0)
        edge = abs(float(e[0] * across[0] + e[1] * across[1])) ** 8
        w = 0.6 if back else (0.7 + 0.25 * edge)
        draw_runs(P[:, :2] + np.array([CX, CY]), collar_seen(c, P), w * rng.uniform(0.95, 1.05),
                  min_len=3, hand=0.12, lift=0.0, piece=(60, 140))
    rings = [(c['ctip'], c['rt'], 0.75 if open_mouth else 0.65)]
    if endon:
        rings.append((c['cbase'], c['rb'], 0.72))
    for center, r, w in rings:
        a0 = rng.uniform(0, 2 * math.pi)
        t = np.linspace(a0, a0 + 2 * math.pi + 0.12, 120)
        P = center + r * (np.cos(t)[:, None] * c['e1'] + np.sin(t)[:, None] * c['e2'])
        keep = collar_seen(c, P)
        if not open_mouth:
            if back:
                continue
            keep &= (P - center)[:, 2] > -0.05 * r      # only the near half
        if not endon:
            # a broken mouth: the tips of the microvilli, not a hoop
            keep &= np.sin(5 * (t - a0) + rng.uniform(0, 6.3)) > -0.35
        draw_runs(P[:, :2] + np.array([CX, CY]), keep, w, min_len=4, hand=0.15, lift=0.08)


def draw_flagellum(c):
    d = c['d']
    start = c['C'] + c['a_up'] * d
    FL = 185 * rng.uniform(0.92, 1.06)
    toward = max(0.0, d[2])
    side = np.cross(d, EZ)
    if np.linalg.norm(side) > 0.3:
        side = unit(side)
        tl = rng.normal(0, 0.4)
        w1 = math.cos(tl) * side + math.sin(tl) * np.cross(d, side)
    else:
        w1 = c['e1']
    w2 = np.cross(d, w1)
    amp = 0.065 * FL * float(np.clip(1.6 - 1.2 * toward, 0.35, 1.0))
    waves = rng.uniform(1.5, 2.0)
    ph = rng.uniform(0, 2 * math.pi)
    bend = rng.normal(0, 0.07) * FL
    pts = []
    for t in np.linspace(0, 1, 140):
        g = min(1.0, t / 0.3)
        lat = amp * g * g * (3 - 2 * g) * math.sin(2 * math.pi * waves * t + ph)
        pts.append(start + t * FL * d + lat * w1 + bend * t * t * w2)
    P = dense(pts, 1.0)
    X, Y = scr(P)
    i, j = look(X, Y)
    bid = body_id[i, j]
    hide = P[:, 2] < body_z[i, j] - 1.0
    hide |= (bid != -1) & (bid != c['id'])            # never over another cell
    hide |= (col_id[i, j] != -1) & (col_id[i, j] != c['id'])   # nor across its collar
    other = (col_id[i, j] != -1) & (col_id[i, j] != c['id'])
    hide |= other & (P[:, 2] < col_z[i, j] - 0.5)
    P2 = np.column_stack([X, Y])
    for r in runs_of(~hide):
        seg = P2[r]
        L = plen(seg)
        # the run leaving the collar, or a long stretch coming out from behind the ball
        if (r[0] <= 2 and L >= 4) or L >= 30:
            pen.line([tuple(p) for p in seg], w=1.35, occlude=False, hand=0.3, lift=0.04, taper=0.45, piece=(30, 80))


# ---------------------------------------------------------------- draw

order = sorted(cells, key=lambda c: -c['d'][2])
draw_outlines()
for c in order:
    draw_collar(c)
    draw_flagellum(c)
for c in order:
    draw_inside(c)
    draw_shading(c)

pen.save('../08-choanoflagellate-colony.svg', mirror=False)
pen.report()
