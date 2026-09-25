#!/usr/bin/env python3
"""D028 · Modello di cedevolezza strutturale della Base Standard (mule v1).

Modello 3D a travi (Timoshenko, 6 gdl per nodo) e molle a 6 gdl, costruito dalla
geometria di tools/cad/standard_params.py. Non è una FEA a solidi: serve a capire
dove sta la cedevolezza tra punta utensile e pezzo, prima di disegnare nervature
e alleggerimenti.

Anello strutturale: punta → testa (rigida) → accoppiamento ToolDock → master →
slitta Z → pattini e vite Z → carrello X → pattini e vite X → trave → spalle →
telaio → pattini e vite Y → tavola → punto di contatto sul pezzo.
Carico: 1 N tra punta e tavola nel punto lavorato, in X, Y e Z.
Ripartizione: energia di deformazione per sottosistema (somma = cedevolezza totale).

Uso (con numpy): python tools/calc/compliance_d028.py [--json out.json]
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools" / "cad"))
import standard_params as P  # noqa: E402
import parts  # noqa: E402

D = P.derived()
AL = dict(E=70000.0, G=26000.0)
ST = dict(E=210000.0, G=81000.0)
RIGID = dict(E=2.1e8, G=8.1e7)

# ------------------------------------------------------------------ rigidezze (N/mm, Nmm/rad)
K_BLOCK = {  # HIWIN G99TE23-2203 radiale (D022); laterale assunta uguale (serie a carico uguale in 4 direzioni)
    "HGH15CA": 365e3, "MGN15H": 202e3,
}
K_NUT = {"SFU1605": 150e3, "SFU1204": 100e3}          # chiocciola C7 senza precarico elevato (stima)
K_BEARING = {"BK12": 200e3, "BK10": 150e3}            # coppia di cuscinetti a contatto obliquo (stima)
K_THETA_MOTOR = 1.0e5                                 # Nmm/rad: tenuta NEMA23 2 Nm ≈ T × 50 denti rotore
PITCH = {"SFU1605": 5.0, "SFU1204": 4.0}
D_ROOT = {"SFU1605": 13.5, "SFU1204": 9.9}
HERTZ_PRELOAD = 1600.0                                # N, clamp classe S (D016)
T_TABLE_EFF = 8.0                                     # spessore equivalente tavola a flessione (pelle 6 + boss/bordo), MULE
T_SHEAR_PANEL = 3.0                                   # pannello inferiore opzionale del telaio


# ------------------------------------------------------------------ sezioni
def rect(b, h):
    """Rettangolo pieno: b lungo y locale, h lungo z locale."""
    a_, b_ = max(b, h), min(b, h)
    J = a_ * b_ ** 3 * (1 / 3 - 0.21 * b_ / a_ * (1 - b_ ** 4 / (12 * a_ ** 4)))
    A = b * h
    return dict(A=A, Iy=b * h ** 3 / 12, Iz=h * b ** 3 / 12, J=J, Asy=A / 1.2, Asz=A / 1.2)


def tube(b, h, t):
    """Tubo rettangolare: b lungo y locale, h lungo z locale, parete t."""
    A = b * h - (b - 2 * t) * (h - 2 * t)
    Iy = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
    Iz = (h * b ** 3 - (h - 2 * t) * (b - 2 * t) ** 3) / 12
    Am = (b - t) * (h - t)
    J = 4 * Am ** 2 * t / (2 * ((b - t) + (h - t)))
    return dict(A=A, Iy=Iy, Iz=Iz, J=J, Asy=2 * t * b, Asz=2 * t * h)


def comp(rects):
    """Sezione composta da rettangoli (cy, cz, b, h) in coordinate locali: b lungo y, h lungo z. Torsione da sezione aperta."""
    A = sum(b * h for _, _, b, h in rects)
    yc = sum(cy * b * h for cy, _, b, h in rects) / A
    zc = sum(cz * b * h for _, cz, b, h in rects) / A
    Iy = sum(b * h ** 3 / 12 + b * h * (cz - zc) ** 2 for _, cz, b, h in rects)
    Iz = sum(h * b ** 3 / 12 + b * h * (cy - yc) ** 2 for cy, _, b, h in rects)
    J = sum(max(b, h) * min(b, h) ** 3 / 3 for _, _, b, h in rects)
    return dict(A=A, Iy=Iy, Iz=Iz, J=J, Asy=A / 1.5, Asz=A / 1.5)


def default_sections():
    """Sezioni del mule corrente da standard_params (D030: canali, master scatolata, spalle scatolate, testa 5045)."""
    C_, out = P.PLATE, {}
    if hasattr(P, "CARRIAGE_FLANGE"):
        f = P.CARRIAGE_FLANGE
        h = C_["carriage_t"] + f["depth"] + 10
        off = (C_["carriage_t"] - h) / 2
        out["carriage"] = comp([(0, 0, C_["carriage_w"], C_["carriage_t"])] +
                               [(s_ * (C_["carriage_w"] + f["t"]) / 2, off, f["t"], h) for s_ in (-1, 1)])
    if hasattr(P, "SLIDE_FLANGE"):
        f = P.SLIDE_FLANGE
        off = -(C_["slide_t"] + f["depth"]) / 2
        out["slide"] = comp([(0, 0, C_["slide_w"], C_["slide_t"])] +
                            [(s_ * (C_["slide_w"] - f["t"]) / 2, off, f["t"], f["depth"]) for s_ in (-1, 1)])
    if "wall" in P.MASTER:
        out["master"] = tube(P.MASTER["W"], P.MASTER["T"], P.MASTER["wall"])
    if "wall" in P.UPRIGHT:
        out["upright"] = tube(P.UPRIGHT["t"], P.UPRIGHT["depth"], P.UPRIGHT["wall"])
    if hasattr(P, "SPINDLE"):
        S = P.SPINDLE
        out["head"] = dict(real5045=True)
    return out


RIGID_SEC = dict(A=1e4, Iy=1e8, Iz=1e8, J=1e8, Asy=1e4, Asz=1e4)


# ------------------------------------------------------------------ modello FE
class Model:
    def __init__(self):
        self.nodes, self.elems, self.fixed = [], [], []

    def node(self, x, y, z):
        self.nodes.append(np.array([x, y, z], float))
        return len(self.nodes) - 1

    def beam(self, n1, n2, sec, mat, tag, up=(0, 0, 1)):
        self.elems.append(("beam", n1, n2, sec, mat, tag, np.array(up, float)))

    def rigid(self, n1, n2):
        v = self.nodes[n2] - self.nodes[n1]
        up = (0, 0, 1) if abs(v[2]) < 0.9 * np.linalg.norm(v) + 1e-9 else (1, 0, 0)
        if np.linalg.norm(v) < 1e-9:
            self.elems.append(("spring", n1, n2, np.full(6, 1e12), "rigid"))
        else:
            self.beam(n1, n2, RIGID_SEC, RIGID, "rigid", up)

    def spring(self, n1, n2, k6, tag):
        self.elems.append(("spring", n1, n2, np.array(k6, float), tag))


def beam_k(xyz1, xyz2, sec, mat, up):
    L = np.linalg.norm(xyz2 - xyz1)
    ex = (xyz2 - xyz1) / L
    upv = up if abs(np.dot(up, ex)) < 0.99 else np.array([1.0, 0, 0]) if abs(ex[0]) < 0.9 else np.array([0, 1.0, 0])
    ez = upv - np.dot(upv, ex) * ex
    ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    E, G = mat["E"], mat["G"]
    A, Iy, Iz, J = sec["A"], sec["Iy"], sec["Iz"], sec["J"]
    py = 12 * E * Iz / (G * sec["Asy"] * L ** 2)   # Timoshenko: flessione nel piano xy
    pz = 12 * E * Iy / (G * sec["Asz"] * L ** 2)
    k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = E * A / L
    k[0, 6] = k[6, 0] = -E * A / L
    k[3, 3] = k[9, 9] = G * J / L
    k[3, 9] = k[9, 3] = -G * J / L
    for (v, th, I, ph, s) in ((1, 5, Iz, py, 1), (2, 4, Iy, pz, -1)):
        c = E * I / (L ** 3 * (1 + ph))
        k[v, v] = k[v + 6, v + 6] = 12 * c
        k[v, v + 6] = k[v + 6, v] = -12 * c
        k[v, th] = k[th, v] = k[v, th + 6] = k[th + 6, v] = s * 6 * c * L
        k[v + 6, th] = k[th, v + 6] = k[v + 6, th + 6] = k[th + 6, v + 6] = -s * 6 * c * L
        k[th, th] = k[th + 6, th + 6] = (4 + ph) * c * L ** 2
        k[th, th + 6] = k[th + 6, th] = (2 - ph) * c * L ** 2
    R = np.vstack([ex, ey, ez])
    T = np.zeros((12, 12))
    for i in range(4):
        T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
    return T.T @ k @ T


def assemble(m):
    n = len(m.nodes) * 6
    K = np.zeros((n, n))
    ek = []
    for e in m.elems:
        if e[0] == "beam":
            _, a, b, sec, mat, tag, up = e
            ke = beam_k(m.nodes[a], m.nodes[b], sec, mat, up)
        else:
            _, a, b, k6, tag = e
            ke = np.zeros((12, 12))
            for i in range(6):
                ke[i, i] = ke[i + 6, i + 6] = k6[i]
                ke[i, i + 6] = ke[i + 6, i] = -k6[i]
        dofs = [6 * a + i for i in range(6)] + [6 * b + i for i in range(6)]
        K[np.ix_(dofs, dofs)] += ke
        ek.append((ke, dofs, tag))
    return K, ek


def solve(m, loads):
    K, ek = assemble(m)
    n = K.shape[0]
    free = np.ones(n, bool)
    for nd in m.fixed:
        free[6 * nd:6 * nd + 3] = False
    F = np.zeros(n)
    for nd, f in loads:
        F[6 * nd:6 * nd + 3] += f
    u = np.zeros(n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    energy = {}
    for ke, dofs, tag in ek:
        ue = u[dofs]
        energy[tag] = energy.get(tag, 0.0) + 0.5 * ue @ ke @ ue
    return u, energy


# ------------------------------------------------------------------ geometria della Standard
def screw_axial(name, bearing, free_len):
    E = ST["E"]
    k_shaft = E * math.pi * D_ROOT[name] ** 2 / 4 / max(free_len, 20.0)
    k_motor = K_THETA_MOTOR * (2 * math.pi / PITCH[name]) ** 2
    return 1 / (1 / k_shaft + 1 / (F_NUT * K_NUT[name]) + 1 / (F_BEARING * K_BEARING[bearing]) + 1 / (F_MOTOR * k_motor))


def block_k(kind, axis_free, normal):
    """Molla a 6 gdl del pattino: radiale lungo 'normal', laterale sul terzo asse, libero lungo la rotaia."""
    kr = K_BLOCK[kind]
    k = np.zeros(6)
    lat = ({0, 1, 2} - {axis_free, normal}).pop()
    k[normal], k[lat] = kr, kr * F_LAT
    Lb = parts.BLOCKS[kind]["L"]
    k[3 + axis_free] = kr * 8.0 ** 2            # rollio del singolo pattino (stima)
    k[3 + normal] = k[3 + lat] = kr * (Lb / 4) ** 2
    return k


COUPLING_R = 40.0                                     # raggio del cerchio delle sfere (Ø80, ICD v4)
F_LAT = 1.0          # rigidezza laterale pattini / radiale (sensibilità)
F_NUT = 1.0
F_BEARING = 1.0
F_MOTOR = 1.0


def coupling_k():
    R, rb = COUPLING_R, 5.0
    Pc = HERTZ_PRELOAD / 3 / 2 / math.cos(math.radians(45))       # per contatto
    Es = ST["E"] / (2 * (1 - 0.3 ** 2))
    delta = (9 * Pc ** 2 / (16 * rb * Es ** 2)) ** (1 / 3)
    kc = 1.5 * Pc / delta
    kz = 3 * kc
    kxy = 1.5 * kc
    krxy = kc * R ** 2 * 1.5
    krz = 3 * kc * R ** 2
    return np.array([kxy, kxy, kz, krxy, krxy, krz]), kc


def build(X, Y, Zd, shear_panel=False, sec=None):
    """sec: sezioni alternative per le analisi di sensibilità; di default quelle del mule corrente."""
    sec = {**default_sections(), **(sec or {})}
    m = Model()
    Lg, U, BM, T, C = P.LADDER, P.UPRIGHT, P.BEAM, P.TABLE, P.PLATE
    xa, ya, za = P.X_AXIS, P.Y_AXIS, P.Z_AXIS
    xtc = T["W"] / 2
    rails_x = (xtc - ya["rail_spacing"] / 2, xtc + ya["rail_spacing"] / 2)
    yc_beam = (D["beam_face"] + D["beam_back"]) / 2
    z_long, z_cross = -Lg["H"] / 2, -(Lg["H"] + Lg["cross_drop"]) / 2
    cross_h = Lg["H"] - Lg["cross_drop"]
    y_front, y_bf, y_end = (sum(Lg["front_y"]) / 2, sum(Lg["bf_y"]) / 2, sum(Lg["end_y"]) / 2)
    ytc = T["D"] / 2
    blocks_y_local = (ytc - ya["block_pitch"] / 2, ytc + ya["block_pitch"] / 2)
    sy_th = ya["screw_len"] - sum(parts.ENDS[ya["screw"]])
    y_bk = sy_th / 2 + 2 + P.SUPPORTS[ya["bk"]]["T"] / 2
    z_y_axis = -Lg["H"] + Lg["pad_t"] + P.SUPPORTS[ya["bk"]]["h"]
    ny = parts.SCREWS[ya["screw"]]["L"]

    # ---------- telaio a scala
    ys = sorted({Lg["long_y"][0], y_front, y_bf, yc_beam, y_end, Lg["long_y"][1]} | {yl - Y for yl in blocks_y_local})
    long_nodes = {}
    for xr in rails_x:
        ids = [m.node(xr, y, z_long) for y in ys]
        for a, b in zip(ids, ids[1:]):
            m.beam(a, b, tube(Lg["long_w"], Lg["H"], Lg["wall"]), AL, "telaio", up=(0, 0, 1))
        long_nodes[xr] = dict(zip(ys, ids))
    cross = {}
    for tag, yv, depth, xs in (("front", y_front, 40.0, rails_x), ("bf", y_bf, 40.0, rails_x), ("end", y_end, 40.0, rails_x),
                               ("rear", yc_beam, U["depth"], (P.BEAM_X[0] + U["t"] / 2, rails_x[0], xtc, rails_x[1], P.BEAM_X[1] - U["t"] / 2))):
        ids = [m.node(x, yv, z_cross) for x in xs]
        for a, b in zip(ids, ids[1:]):
            m.beam(a, b, tube(depth, cross_h, Lg["wall"]), AL, "telaio", up=(0, 0, 1))
        cross[tag] = dict(zip(xs, ids))
        for xr in rails_x:
            m.rigid(long_nodes[xr][yv], cross[tag][xr])
    if shear_panel:   # pannello inferiore come controventi equivalenti a taglio, a quota fondo telaio
        bays = [y_front, y_bf, yc_beam, y_end]
        b = rails_x[1] - rails_x[0]
        for y0, y1 in zip(bays, bays[1:]):
            a_ = y1 - y0
            Ld = math.hypot(a_, b)
            cos2 = (b / Ld) ** 2
            Ad = AL["G"] * T_SHEAR_PANEL * a_ * Ld / (b * AL["E"] * cos2) / 2
            corners = [m.node(x, y, -Lg["H"]) for x, y in ((rails_x[0], y0), (rails_x[1], y0), (rails_x[0], y1), (rails_x[1], y1))]
            for c_, (x, y) in zip(corners, ((rails_x[0], y0), (rails_x[1], y0), (rails_x[0], y1), (rails_x[1], y1))):
                m.rigid(long_nodes[x][y], c_)
            sec = dict(A=Ad, Iy=1.0, Iz=1.0, J=1.0, Asy=Ad, Asz=Ad)
            m.beam(corners[0], corners[3], sec, AL, "telaio")
            m.beam(corners[1], corners[2], sec, AL, "telaio")
    m.fixed += [long_nodes[xr][Lg["long_y"][0]] for xr in rails_x] + [long_nodes[xr][Lg["long_y"][1]] for xr in rails_x]
    m.fixed += [cross["rear"][P.BEAM_X[0] + U["t"] / 2], cross["rear"][P.BEAM_X[1] - U["t"] / 2]]

    # ---------- spalle e trave
    zx = D["zx"]
    beam_x = sorted({P.BEAM_X[0] + U["t"] / 2, P.BEAM_X[1] - U["t"] / 2, X - xa["block_pitch"] / 2, X + xa["block_pitch"] / 2, X, xtc,
                     P.TRAVEL["X"] / 2 + (xa["screw_len"] - sum(parts.ENDS[xa["screw"]])) / 2 + 14.5})
    bnodes = [m.node(x, yc_beam, zx) for x in beam_x]
    for a, b in zip(bnodes, bnodes[1:]):
        m.beam(a, b, tube(BM["depth"], BM["height"], BM["wall"]), AL, "trave", up=(0, 0, 1))
    bmap = dict(zip(beam_x, bnodes))
    for xe in (P.BEAM_X[0] + U["t"] / 2, P.BEAM_X[1] - U["t"] / 2):
        base_n = cross["rear"][xe]
        n0 = m.node(xe, yc_beam, -Lg["cross_drop"])
        m.rigid(base_n, n0)
        n1 = m.node(xe, yc_beam, D["beam_bottom"])
        m.beam(n0, n1, sec.get("upright", rect(U["t"], U["depth"])), AL, "spalle", up=(0, 1, 0))
        m.rigid(n1, bmap[xe])

    # ---------- carrello X e pattini X
    zb = parts.BLOCKS[za["block"]]
    sb = D["slide_bottom_low"] + (P.TRAVEL["Z"] - Zd)
    zbc = sb + C["block_offset"] + zb["L"] / 2 + za["block_pitch"] / 2
    z_blocks = (zbc - za["block_pitch"] / 2, zbc + za["block_pitch"] / 2)
    car_bot = zx - xa["rail_spacing"] / 2 - parts.BLOCKS[xa["block"]]["W"] / 2 - C["below_x_blocks"]
    car_top = D["z_rail_bottom"] + za["rail_len"]
    y_car = (D["carriage_front"] + D["carriage_back"]) / 2
    zc_list = sorted({car_bot, zx - xa["rail_spacing"] / 2, zx + xa["rail_spacing"] / 2, *z_blocks, car_top})
    cnodes = [m.node(X, y_car, z) for z in zc_list]
    for a, b in zip(cnodes, cnodes[1:]):
        m.beam(a, b, sec.get("carriage", rect(C["carriage_w"], C["carriage_t"])), AL, "carrello X", up=(0, 1, 0))
    cmap = dict(zip(zc_list, cnodes))
    y_xblock = (D["beam_face"] + D["carriage_back"]) / 2
    for dz in (xa["rail_spacing"] / 2, -xa["rail_spacing"] / 2):
        for dx in (-xa["block_pitch"] / 2, xa["block_pitch"] / 2):
            na = m.node(X + dx, y_xblock, zx + dz)
            nb = m.node(X + dx, y_xblock, zx + dz)
            m.rigid(bmap[X + dx], na)
            m.spring(na, nb, block_k(xa["block"], axis_free=0, normal=1), "guide X + vite X")
            m.rigid(nb, cmap[zx + dz])
    x_bk = P.TRAVEL["X"] / 2 + (xa["screw_len"] - sum(parts.ENDS[xa["screw"]])) / 2 + 14.5
    kx = screw_axial(xa["screw"], xa["bk"], x_bk - X)
    ns1, ns2 = m.node(X, y_xblock, zx), m.node(X, y_xblock, zx)
    m.rigid(bmap[x_bk], ns1)            # la reazione assiale va al BK sulla trave
    m.spring(ns1, ns2, [kx, 0, 0, 0, 0, 0], "guide X + vite X")
    m.rigid(ns2, cmap[zx - xa["rail_spacing"] / 2])

    # ---------- slitta Z e pattini Z
    y_slide = (D["slide_front"] + D["slide_back"]) / 2
    zs_list = sorted({sb, *z_blocks, sb + C["slide_len"]})
    snodes = [m.node(X, y_slide, z) for z in zs_list]
    for a, b in zip(snodes, snodes[1:]):
        m.beam(a, b, sec.get("slide", rect(C["slide_w"], C["slide_t"])), AL, "slitta Z", up=(0, 1, 0))
    smap = dict(zip(zs_list, snodes))
    y_zblock = (D["slide_back"] + D["carriage_front"]) / 2
    for zbz in z_blocks:
        for dx in (-za["rail_spacing"] / 2, za["rail_spacing"] / 2):
            na, nb = m.node(X + dx, y_zblock, zbz), m.node(X + dx, y_zblock, zbz)
            m.rigid(cmap[zbz], na)
            m.spring(na, nb, block_k(za["block"], axis_free=2, normal=1), "guide Z + vite Z")
            m.rigid(nb, smap[zbz])
    tab = sb + C["slide_len"]
    z_bk_top = tab - P.SUPPORT_GAP_Z - parts.ENDS[za["screw"]][1] + za["screw_len"] - 20
    kz = screw_axial(za["screw"], za["bk"], z_bk_top - tab)
    nz1, nz2 = m.node(X, y_zblock, tab), m.node(X, y_zblock, tab)
    m.rigid(cmap[car_top], nz1)
    m.spring(nz1, nz2, [0, 0, kz, 0, 0, 0], "guide Z + vite Z")
    m.rigid(nz2, smap[tab])

    # ---------- ToolDock: master a sbalzo + accoppiamento cinematico, testa rigida
    zm = sb - P.MASTER["T"] / 2
    nm0 = m.node(X, y_slide, zm)
    m.rigid(smap[sb], nm0)
    nm1 = m.node(X, 0.0, zm)
    m.beam(nm0, nm1, sec.get("master", rect(P.MASTER["W"], P.MASTER["T"])), AL, "master ToolDock", up=(0, 0, 1))
    zcpl = sb - P.MASTER["T"]
    nc1, nc2 = m.node(X, 0.0, zcpl), m.node(X, 0.0, zcpl)
    m.rigid(nm1, nc1)
    kcpl, _ = coupling_k()
    m.spring(nc1, nc2, kcpl * COUPLING_SCALE, "accoppiamento ToolDock")
    tip = m.node(X, 0.0, zcpl - P.HEAD["L"])
    hd = sec.get("head")
    if hd is None:                      # testa rigida (D028 v0)
        m.rigid(nc2, tip)
    elif hd.get("real5045"):            # D030: SycoTec 5045 appeso: receiver, dorso, mount a collare, corpo, cuscinetti, naso
        S = P.SPINDLE
        z_rear = zcpl - S["receiver_t"] - S["connector"]
        zc0 = z_rear - S["rear"] - 10
        zc1 = zc0 - S["clamp_len"]
        z_h0 = z_rear - S["rear"] - S["housing"]
        z_b = z_h0 - S["neck"]
        n1 = m.node(X, 0.0, zcpl - S["receiver_t"])
        m.rigid(nc2, n1)
        n2 = m.node(X, 0.0, zc0)
        cb = S["clamp_block"]
        d_cup = S["d"] + 3
        cup = dict(A=cb ** 2 - math.pi * d_cup ** 2 / 4, Iy=cb ** 4 / 12 - math.pi * d_cup ** 4 / 64, Iz=cb ** 4 / 12 - math.pi * d_cup ** 4 / 64,
                   J=0.14 * cb ** 4 - math.pi * d_cup ** 4 / 32, Asy=0.4 * cb ** 2, Asz=0.4 * cb ** 2)
        m.beam(n1, n2, cup, AL, "testa (spindle + utensile)", up=(1, 0, 0))     # tazza sopra il collare (finestra connettore trascurata)
        n3 = m.node(X, 0.0, zc1)
        blk = dict(A=cb ** 2 - math.pi * S["d"] ** 2 / 4, Iy=cb ** 4 / 12 - math.pi * S["d"] ** 4 / 64, Iz=cb ** 4 / 12 - math.pi * S["d"] ** 4 / 64,
                   J=0.14 * cb ** 4 - math.pi * S["d"] ** 4 / 32, Asy=0.5 * cb ** 2, Asz=0.5 * cb ** 2)
        # collare e corpo spindle lavorano in parallelo: corpo in acciaio inox (tubo equivalente sp. 5) dentro il collare
        m.beam(n2, n3, blk, AL, "testa (spindle + utensile)", up=(1, 0, 0))
        do, di = S["d"], S["d"] - 10
        body = dict(A=math.pi / 4 * (do ** 2 - di ** 2), Iy=math.pi / 64 * (do ** 4 - di ** 4), Iz=math.pi / 64 * (do ** 4 - di ** 4),
                    J=math.pi / 32 * (do ** 4 - di ** 4), Asy=math.pi / 8 * (do ** 2 - di ** 2), Asz=math.pi / 8 * (do ** 2 - di ** 2))
        m.beam(n2, n3, body, ST, "testa (spindle + utensile)", up=(1, 0, 0))
        n4 = m.node(X, 0.0, z_b)
        m.beam(n3, n4, body, ST, "testa (spindle + utensile)", up=(1, 0, 0))
        n5 = m.node(X, 0.0, z_b)
        kb = S["k_bearing"]
        m.spring(n4, n5, [kb, kb, 3 * kb, kb * 25.0 ** 2, kb * 25.0 ** 2, 1e12], "testa (spindle + utensile)")
        dn = 16.0
        nose = dict(A=math.pi * dn ** 2 / 4, Iy=math.pi * dn ** 4 / 64, Iz=math.pi * dn ** 4 / 64, J=math.pi * dn ** 4 / 32,
                    Asy=0.9 * math.pi * dn ** 2 / 4, Asz=0.9 * math.pi * dn ** 2 / 4)
        m.beam(n5, tip, nose, ST, "testa (spindle + utensile)", up=(1, 0, 0))
    else:                               # testa reale: receiver + corpo spindle a sbalzo dal collare + cuscinetti + mandrino
        nclamp = m.node(X, 0.0, zcpl - hd["clamp"])
        m.rigid(nc2, nclamp)
        nnose = m.node(X, 0.0, zcpl - hd["nose"])
        do, di = hd["body_d"], hd["body_d"] - 2 * hd["body_t"]
        body = dict(A=math.pi / 4 * (do ** 2 - di ** 2), Iy=math.pi / 64 * (do ** 4 - di ** 4), Iz=math.pi / 64 * (do ** 4 - di ** 4),
                    J=math.pi / 32 * (do ** 4 - di ** 4), Asy=math.pi / 8 * (do ** 2 - di ** 2), Asz=math.pi / 8 * (do ** 2 - di ** 2))
        m.beam(nclamp, nnose, body, ST, "testa (spindle + utensile)", up=(1, 0, 0))
        nshaft = m.node(X, 0.0, zcpl - hd["nose"])
        kb = hd["k_bearing"]
        m.spring(nnose, nshaft, [kb, kb, 3 * kb, kb * 30.0 ** 2, kb * 30.0 ** 2, 1e12], "testa (spindle + utensile)")
        dm = hd["mandrel_d"]
        mand = dict(A=math.pi * dm ** 2 / 4, Iy=math.pi * dm ** 4 / 64, Iz=math.pi * dm ** 4 / 64, J=math.pi * dm ** 4 / 32,
                    Asy=0.9 * math.pi * dm ** 2 / 4, Asz=0.9 * math.pi * dm ** 2 / 4)
        m.beam(nshaft, tip, mand, ST, "testa (spindle + utensile)", up=(1, 0, 0))

    # ---------- tavola (griglia di travi) e pattini Y, vite Y
    xs = sorted({0.0, rails_x[0], xtc, rails_x[1], T["W"], X})
    ysl = sorted({0.0, blocks_y_local[0], ytc, ytc + ny / 2, blocks_y_local[1], T["D"], Y})
    zt = D["table_bottom"] + T["T"] / 2
    grid = {(x, yl): m.node(x, yl - Y, zt) for x in xs for yl in ysl}

    def strip(vals, i):
        lo = (vals[i] - vals[i - 1]) / 2 if i > 0 else 0
        hi = (vals[i + 1] - vals[i]) / 2 if i < len(vals) - 1 else 0
        return max(lo + hi, 10.0)
    for j, yl in enumerate(ysl):
        for a, b in zip(xs, xs[1:]):
            m.beam(grid[(a, yl)], grid[(b, yl)], rect(strip(ysl, j), sec.get("table_t", T_TABLE_EFF)), AL, "tavola", up=(0, 0, 1))
    for i, x in enumerate(xs):
        for a, b in zip(ysl, ysl[1:]):
            m.beam(grid[(x, a)], grid[(x, b)], rect(strip(xs, i), sec.get("table_t", T_TABLE_EFF)), AL, "tavola", up=(0, 0, 1))
    for xr in rails_x:
        for yl in blocks_y_local:
            na, nb = m.node(xr, yl - Y, 8.0), m.node(xr, yl - Y, 8.0)
            m.rigid(long_nodes[xr][yl - Y], na)
            m.spring(na, nb, block_k(ya["block"], axis_free=1, normal=2), "guide Y + vite Y")
            m.rigid(nb, grid[(xr, yl)])
    nyn = m.node(xtc, ytc + ny / 2 - Y, z_y_axis)
    m.rigid(grid[(xtc, ytc + ny / 2)], nyn)
    nyb = m.node(xtc, ytc + ny / 2 - Y, z_y_axis)
    ky = screw_axial(ya["screw"], ya["bk"], y_bk - (ytc + ny / 2 - Y))
    m.spring(nyn, nyb, [0, ky, 0, 0, 0, 0], "guide Y + vite Y")
    m.rigid(nyb, cross["rear"][xtc])
    work = m.node(X, 0.0, D["table_top"])
    m.rigid(grid[(X, Y)], work)
    return m, tip, work


COUPLING_SCALE = 1.0
SUBSYSTEMS = ["telaio", "spalle", "trave", "guide X + vite X", "carrello X", "guide Z + vite Z", "slitta Z", "master ToolDock",
              "accoppiamento ToolDock", "testa (spindle + utensile)", "tavola", "guide Y + vite Y"]


def mass_by_tag(m):
    out = {}
    for e in m.elems:
        if e[0] == "beam" and e[5] != "rigid":
            L = np.linalg.norm(m.nodes[e[2]] - m.nodes[e[1]])
            f = 0.5 if e[5] == "tavola" else 1.0     # la griglia della tavola conta la piastra due volte
            out[e[5]] = out.get(e[5], 0.0) + f * e[3]["A"] * L * P.AL_DENSITY
    return out


def compliance(X, Y, Zd, shear_panel=False, sec=None):
    m, tip, work = build(X, Y, Zd, shear_panel, sec)
    out = {"_mass": mass_by_tag(m)}
    for i, ax in enumerate("XYZ"):
        d = np.zeros(3)
        d[i] = 1.0
        u, energy = solve(m, [(tip, d), (work, -d)])
        c = (u[6 * tip:6 * tip + 3] - u[6 * work:6 * work + 3]) @ d       # mm/N
        out[ax] = dict(um_per_N=c * 1e3, N_per_um=1 / (c * 1e3),
                       share={s: 2 * energy.get(s, 0.0) / c for s in SUBSYSTEMS},
                       rigid_share=2 * energy.get("rigid", 0.0) / c)
    return out


def main():
    configs = {"CENTER": P.CONFIGS["CENTER"]}
    for X in (0.0, P.TRAVEL["X"]):
        for Y in (0.0, P.TRAVEL["Y"]):
            for Zd in (0.0, P.TRAVEL["Z"]):
                configs[f"X{int(X)} Y{int(Y)} Z{-int(Zd)}"] = (X, Y, Zd)
    res = {k: compliance(*v) for k, v in configs.items()}
    panel = compliance(*P.CONFIGS["CENTER"], shear_panel=True)
    # scenari: sezioni equivalenti scatolate/nervate (stesso ingombro), una alla volta e combinate
    SC = [
        ("Master ToolDock scatolata 120 × 50 sp. 8", dict(master=tube(P.MASTER["W"], 50.0, 8.0)), 1.0, 0.0),
        ("Slitta Z scatolata 150 × 50 sp. 8", dict(slide=tube(150.0, 50.0, 8.0)), 1.0, 0.0),
        ("Carrello X scatolato 170 × 60 sp. 6", dict(carriage=tube(170.0, 60.0, 6.0)), 1.0, 0.0),
        ("Spalle scatolate 60 × 120 sp. 6", dict(upright=tube(60.0, 120.0, 6.0)), 1.0, 0.0),
        ("Tavola equivalente 14 mm", dict(table_t=14.0), 1.0, 0.0),
        ("Accoppiamento ToolDock ×4 (Ø, precarico, contatti conformi)", {}, 4.0, 0.0),
        ("Pannello inferiore telaio 3 mm", {"_panel": True}, 1.0, 0.0),
    ]
    three = {}
    for _, sv, _, _ in SC[:3]:
        three.update(sv)
    SC.append(("Master + slitta Z + carrello X scatolati", three, 1.0, 0.0))
    combo = {}
    for _, sv, _, _ in SC[:5]:
        combo.update(sv)
    SC.append(("Tutte le sezioni scatolate + tavola 14", combo, 1.0, 0.0))
    SC.append(("… + accoppiamento ×4", combo, 4.0, 0.0))
    global COUPLING_SCALE
    base = res["CENTER"]
    m0 = sum(base["_mass"].values())
    scen = []
    for name, sv, cs, _ in SC:
        COUPLING_SCALE = cs
        sv = dict(sv)
        panel_ = sv.pop("_panel", False)
        r = compliance(*P.CONFIGS["CENTER"], shear_panel=panel_, sec=sv)
        dkg = sum(r["_mass"].values()) - m0
        if panel_:
            span = P.Y_AXIS["rail_spacing"] + P.LADDER["long_w"]
            dkg = span * (P.LADDER["long_y"][1] - P.LADDER["long_y"][0]) * T_SHEAR_PANEL * P.AL_DENSITY
        scen.append(dict(name=name, dkg=round(dkg, 2), coupling_scale=cs,
                         N_per_um={ax: round(r[ax]["N_per_um"], 2) for ax in "XYZ"},
                         um_per_N={ax: round(r[ax]["um_per_N"], 3) for ax in "XYZ"},
                         top_share={ax: sorted(((k, round(v * 100)) for k, v in r[ax]["share"].items()), key=lambda t: -t[1])[:3] for ax in "XYZ"}))
    COUPLING_SCALE = 1.0
    # peso del singolo sottosistema: quanto cambia la cedevolezza se il sottosistema diventa 2× più rigido
    halving = {}
    for tag in SUBSYSTEMS:
        halving[tag] = {ax: round(base[ax]["um_per_N"] * base[ax]["share"][tag] / 2, 3) for ax in "XYZ"}
    worst = {ax: max(((k, r[ax]["um_per_N"]) for k, r in res.items()), key=lambda t: t[1]) for ax in "XYZ"}
    kcpl, kc = coupling_k()
    Lg = P.LADDER
    span = P.Y_AXIS["rail_spacing"] + Lg["long_w"]
    panel_kg = span * (Lg["long_y"][1] - Lg["long_y"][0]) * T_SHEAR_PANEL * P.AL_DENSITY
    for k in res:
        res[k].pop("_mass", None)
    report = dict(target_N_per_um=10.0, configs=res, scenarios=scen, halving=halving, masses_model=base.get("_mass", {}), worst=worst, shear_panel=dict(center=panel, added_kg=round(panel_kg, 2), t=T_SHEAR_PANEL),
                  inputs=dict(k_block=K_BLOCK, k_nut=K_NUT, k_bearing=K_BEARING, k_theta_motor=K_THETA_MOTOR, coupling_contact_N_per_um=round(kc / 1e3, 1),
                              coupling_k=[round(v, 1) for v in kcpl], t_table_eff=T_TABLE_EFF,
                              screw_axial_center_N_per_um={"X": round(screw_axial(P.X_AXIS["screw"], P.X_AXIS["bk"], 277) / 1e3, 1),
                                                           "Y": round(screw_axial(P.Y_AXIS["screw"], P.Y_AXIS["bk"], 214) / 1e3, 1),
                                                           "Z": round(screw_axial(P.Z_AXIS["screw"], P.Z_AXIS["bk"], 150) / 1e3, 1)}),
                  geometry=dict(a=D["a_tool_to_x_face"], b=D["b_tip_below_x_rails"], z_lever=D["z_lever_low"]))
    c = res["CENTER"]
    print("CENTER  " + "  ".join(f"{ax}: {c[ax]['um_per_N']:.3f} µm/N ({c[ax]['N_per_um']:.1f} N/µm)" for ax in "XYZ"))
    for ax in "XYZ":
        sh = sorted(c[ax]["share"].items(), key=lambda t: -t[1])
        print(f"  {ax}: " + ", ".join(f"{k} {v * 100:.0f}%" for k, v in sh if v > 0.01), f"(rigidi {c[ax]['rigid_share'] * 100:.1f}%)")
    print("peggiore", {ax: (k, round(v, 3)) for ax, (k, v) in worst.items()})
    for sc in scen:
        print(f"  {sc['name']:<58} {sc['dkg']:+5.2f} kg", sc["N_per_um"])
    print("pannello", {ax: round(panel[ax]["um_per_N"], 3) for ax in "XYZ"}, "kg", report["shear_panel"]["added_kg"])
    write_page(report)
    if "--json" in sys.argv:
        pathlib.Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def it(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def write_page(r):
    c = r["configs"]["CENTER"]
    tgt = r["target_N_per_um"]
    w = r["worst"]
    sub_rows = ""
    for tag in SUBSYSTEMS:
        cells = ""
        for ax in "XYZ":
            v = c[ax]["share"][tag] * 100
            cells += (f'<td><div style="display:flex;align-items:center;gap:8px"><span style="display:inline-block;height:8px;border-radius:4px;background:#e8601f;width:{max(v, 0.5) * 1.2:.0f}px"></span>'
                      f'<span>{it(v, 0)}%</span></div></td>')
        sub_rows += f"<tr><td>{tag}</td>{cells}</tr>"
    sc_rows = "".join(
        f'<tr><td>{sc["name"]}</td><td>{"+" if sc["dkg"] >= 0 else ""}{it(sc["dkg"])} kg</td>'
        + "".join(f'<td>{it(sc["N_per_um"][ax])}</td>' for ax in "XYZ") + "</tr>" for sc in r["scenarios"])
    best = r["scenarios"][-1]
    three = next(sc for sc in r["scenarios"] if sc["name"].startswith("Master + slitta"))
    gain = {ax: three["N_per_um"][ax] / c[ax]["N_per_um"] for ax in "XYZ"}
    inp = r["inputs"]
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — Rigidezza · D028</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/calc/compliance_d028.py: non modificare a mano. -->
<a class="back" href="cad-standard.html">← CAD Standard · mule</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D028 · modello di cedevolezza v0</div><h1>Rigidezza<br>alla punta.</h1><p class="lead">Modello 3D a travi Timoshenko e molle a 6 gdl della Standard mule v1, costruito dalle quote di <code>standard_params.py</code>: telaio a scala, spalle, trave, pattini e viti con le rigidezze HIWIN e le catene assiali, carrello X, slitta Z, master e accoppiamento ToolDock, griglia della tavola. Carico di 1 N tra punta utensile e punto lavorato sul pezzo; la ripartizione per sottosistema viene dall'energia di deformazione. Non è una FEA a solidi: serve a decidere dove mettere o togliere materiale.</p><div class="badges"><span class="badge ok">D028 · modello v0</span><span class="badge">Target D014: ≥ {it(tgt, 0)} N/µm</span><span class="badge">Testa e utensile rigidi</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{it(c["X"]["N_per_um"])}</strong><span>N/µm in X al centro corsa</span></div>
  <div class="metric"><strong>{it(c["Y"]["N_per_um"])}</strong><span>N/µm in Y al centro corsa</span></div>
  <div class="metric"><strong>{it(c["Z"]["N_per_um"])}</strong><span>N/µm in Z al centro corsa</span></div>
  <div class="metric"><strong>≥ {it(tgt, 0)}</strong><span>N/µm richiesti da D014 · oggi NON PASSA</span></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">Rigidezza e cedevolezza</span><h2>Mule v1 così com'è.</h2><div class="table-wrap"><table>
    <tr><th></th><th>X</th><th>Y</th><th>Z</th></tr>
    <tr><td>Centro corsa · µm/N</td>{"".join(f'<td>{it(c[ax]["um_per_N"], 3)}</td>' for ax in "XYZ")}</tr>
    <tr><td>Centro corsa · N/µm</td>{"".join(f'<td class="status-critical">{it(c[ax]["N_per_um"])}</td>' for ax in "XYZ")}</tr>
    <tr><td>Caso peggiore (8 vertici) · µm/N</td>{"".join(f'<td>{it(w[ax][1], 3)}<br><small style="color:var(--dim)">{w[ax][0]}</small></td>' for ax in "XYZ")}</tr>
  </table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Bracci reali dal mule: a = {it(r["geometry"]["a"], 0)} mm, b = {it(r["geometry"]["b"], 0)} mm, leva Z {it(r["geometry"]["z_lever"], 0)} mm. Testa, mandrino e utensile sono rigidi nel modello: la macchina vera sarà più cedevole.</p></div>
  <div class="panel"><span class="kicker">Dove sta la cedevolezza · centro corsa</span><h2>Le piastre piatte.</h2><div class="table-wrap"><table><tr><th>Sottosistema</th><th>X</th><th>Y</th><th>Z</th></tr>{sub_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Master strutturale e accoppiamento cinematico sono separati: da solo, un accoppiamento ×4 porta X da 0,43 a 0,49 N/µm, mentre la master scatolata da sola lo porta a 0,85. La master ToolDock (piastra da {it(P.MASTER["T"], 0)} mm a sbalzo), la slitta Z ({it(P.PLATE["slide_t"], 0)} mm) e il carrello X ({it(P.PLATE["carriage_t"], 0)} mm) lavorano nel loro spessore. Telaio, spalle, trave e guide X pesano pochi punti: non sono il problema oggi.</p></div>
</section>

<section class="section"><h2>Cosa conviene fare · rigidezza per kg</h2><div class="table-wrap"><table>
<tr><th>Scenario (al centro corsa)</th><th>Δ massa</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th></tr>
<tr><td><b>Mule v1 attuale</b></td><td>—</td>{"".join(f'<td><b>{it(c[ax]["N_per_um"])}</b></td>' for ax in "XYZ")}</tr>
{sc_rows}
</table></div><p style="color:var(--dim);font-size:13px;margin-top:12px">Sezioni equivalenti a parità di ingombro in pianta. L'accoppiamento ×4 non pesa ma cambia l'interfaccia meccanica congelata (ICD v4): diametro delle sfere, precarico o contatti conformi.</p></section>

<section class="section split">
  <div class="panel" style="border-color:rgba(46,230,166,.35)"><span class="kicker">Proposte per il mule v2</span><h2>Scatolare, non ispessire.</h2><div class="spec-list">
    <div class="spec-row"><b>Sì subito</b><p>Master ToolDock, slitta Z e carrello X da piastre piatte a sezioni scatolate o nervate: {"+" if three["dkg"] >= 0 else ""}{it(three["dkg"], 1)} kg in tutto, rigidezza ×{it(gain["X"], 1)} in X, ×{it(gain["Y"], 1)} in Y, ×{it(gain["Z"], 1)} in Z ({it(three["N_per_um"]["X"], 1)} / {it(three["N_per_um"]["Y"], 1)} / {it(three["N_per_um"]["Z"], 1)} N/µm).</p></div>
    <div class="spec-row"><b>No</b><p>Pannello inferiore del telaio: +1,9 kg per meno dell'1% sull'anello. Il telaio a scala non è il limite oggi.</p></div>
    <div class="spec-row"><b>Non toccare</b><p>La trave (6 kg): pesa pochi punti sull'anello. Non va alleggerita né appesantita prima della FEA a solidi.</p></div>
    <div class="spec-row"><b>Tavola</b><p>È il primo contributo in Z. Più spessore costa molto in massa: meglio nervature sotto la pelle o appoggi pattini più vicini al pezzo.</p></div>
  </div></div>
  <div class="panel" style="border-color:rgba(255,84,112,.35)"><span class="kicker">Stato rispetto a D014</span><h2>Target non ancora raggiunto.</h2><p>D028 v0 non raggiunge il target D014 di ≥ 10 N/µm, che resta TARGET. Anche con tutte le sezioni scatolate, tavola equivalente 14 mm e accoppiamento 4 volte più rigido il modello dà ~{it(best["N_per_um"]["X"], 1)} / {it(best["N_per_um"]["Y"], 1)} / {it(best["N_per_um"]["Z"], 1)} N/µm in X / Y / Z. Prima di rivedere D014 servono la geometria reale della testa, la cedevolezza locale ottimizzata (carrello X, Z, master e testa: i primi 100–200 mm della catena) e la validazione del modello al banco: è lo studio <a href="tooldock-d029.html" style="color:var(--accent-2)">D029</a>. Per riferimento, con il carico radiale Standard di 150 N: 2 N/µm → 75 µm, 3 N/µm → 50 µm, 10 N/µm → 15 µm di deformazione elastica.</p></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">Ipotesi del modello</span><h2>Cosa c'è dentro.</h2><div class="spec-list">
    <div class="spec-row"><b>Pattini</b><p>HGH15CA ZA {it(inp["k_block"]["HGH15CA"] / 1e3, 0)} N/µm, MGN15H Z1 {it(inp["k_block"]["MGN15H"] / 1e3, 0)} N/µm radiali (D022); laterale assunta uguale; momenti del singolo pattino stimati.</p></div>
    <div class="spec-row"><b>Viti</b><p>Catena assiale albero + chiocciola + cuscinetti + tenuta del motore (NEMA23 ≈ 100 N·m/rad): ~{it(inp["screw_axial_center_N_per_um"]["X"], 0)} / {it(inp["screw_axial_center_N_per_um"]["Y"], 0)} / {it(inp["screw_axial_center_N_per_um"]["Z"], 0)} N/µm in X / Y / Z a metà corsa.</p></div>
    <div class="spec-row"><b>ToolDock</b><p>3 sfere Ø10 su Ø80 in V a 45°, Hertz sfera-piano a precarico 1,6 kN (D016): {it(inp["coupling_contact_N_per_um"], 0)} N/µm per contatto.</p></div>
    <div class="spec-row"><b>Tavola</b><p>Griglia di travi con spessore equivalente {it(inp["t_table_eff"], 0)} mm (pelle 6 mm + boss e bordo).</p></div>
    <div class="spec-row"><b>Vincoli</b><p>Giunti bullonati rigidi, banco rigido, 6 appoggi (estremi dei longheroni e della traversa posteriore).</p></div>
  </div></div>
  <div class="panel"><span class="kicker">Rigenerare</span><h2>Un comando.</h2><p><code>python tools/calc/compliance_d028.py</code> (numpy, stesso ambiente del CAD) rilegge <code>standard_params.py</code> e riscrive questa pagina. Il prossimo passo è la FEA a solidi dei pezzi che il modello indica come critici, dopo averli ridisegnati scatolati.</p></div>
</section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    (ROOT / "base" / "compliance-d028.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
