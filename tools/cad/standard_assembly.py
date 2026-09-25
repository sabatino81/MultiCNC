#!/usr/bin/env python3
"""Base Standard · "digital mule": assieme parametrico dimensionale.

Brutto ma dimensionalmente corretto. Costruisce l'assieme dai parametri di
standard_params.py e dai componenti commerciali di parts.py (le stesse funzioni che
generano gli STEP in cad/step/: qui rotaie, pattini, viti e chiocciole sono istanziati
separatamente perché nell'assieme si muovono). Per HOME, CENTER e MAX:
- esporta lo STEP dell'assieme (cad/standard/standard_mule_<config>.step);
- controlla collisioni (volume comune) e giochi minimi tra parti in moto relativo;
- calcola bounding box, footprint e massa stimata;
e scrive cad/standard/report.json e la pagina base/cad-standard.html.

Uso (dalla radice, con CadQuery): python tools/cad/standard_assembly.py [--no-step]
"""
import itertools
import json
import math
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "bom"))
import cadquery as cq  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402

import parts  # noqa: E402
import standard_params as P  # noqa: E402

OUT = ROOT / "cad" / "standard"
D = P.derived()
ORIGIN = (0, 0, 0)

# ---------------------------------------------------------------- primitive


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(axis, a0, a1, c1, c2, r):
    """Cilindro lungo 'x', 'y' o 'z' da a0 ad a1; (c1, c2) = le altre due coordinate in ordine xyz."""
    w = cq.Workplane("XY").circle(r).extrude(a1 - a0)
    if axis == "z":
        return w.translate((c1, c2, a0))
    if axis == "x":
        return w.rotate(ORIGIN, (0, 1, 0), 90).translate((a0, c1, c2))
    return w.rotate(ORIGIN, (1, 0, 0), -90).translate((c1, a0, c2))


def tube(axis, a0, a1, c1, c2, r_out, r_in):
    return cyl(axis, a0, a1, c1, c2, r_out).cut(cyl(axis, a0 - 1, a1 + 1, c1, c2, r_in))


# orientazioni dei componenti commerciali (locale parts.py: lunghezza X, larghezza Y, altezza Z)
def to_x_on_face(w):          # guida X sulla faccia trave: altezza → −Y, larghezza → Z
    return w.rotate(ORIGIN, (1, 0, 0), 90)


def to_y_on_floor(w):         # guida Y sul basamento: lunghezza → Y
    return w.rotate(ORIGIN, (0, 0, 1), 90)


def to_z_toward_y(w):         # guida Z: lunghezza → Z, altezza → +Y, larghezza → X
    return w.rotate(ORIGIN, (0, 1, 0), -90).rotate(ORIGIN, (0, 0, 1), -90)


def screw_shaft(name, length):
    s, (bk, bf) = parts.SCREWS[name], parts.ENDS[name]
    thread = length - bk - bf
    r_end = s["d"] / 2 - 2
    return (cyl("x", 0, bf, 0, 0, r_end)
            .union(cyl("x", bf, bf + thread, 0, 0, s["d"] / 2))
            .union(cyl("x", bf + thread, length, 0, 0, r_end)))


def screw_nut(name, flange_end=False):
    """Chiocciola lungo +X da 0; flangia sul lato x = 0, o sul lato x = L se flange_end."""
    s = parts.SCREWS[name]
    f0 = s["L"] - s["B"] if flange_end else 0
    body = cyl("x", 0, s["L"], 0, 0, s["D"] / 2).union(cyl("x", f0, f0 + s["B"], 0, 0, s["A"] / 2))
    return body.cut(cyl("x", -1, s["L"] + 1, 0, 0, s["d"] / 2))


def support(kind, x0):
    """Supporto BK/BF lungo X da x0, faccia di montaggio a z = −h, asse a z = 0."""
    q = P.SUPPORTS[kind]
    b = box(x0, x0 + q["T"], -q["W"] / 2, q["W"] / 2, -q["h"], q["H"] - q["h"])
    return b.cut(cyl("x", x0 - 1, x0 + q["T"] + 1, 0, 0, q["bore"] / 2 + 0.1))


def screw_ends(axis_cfg):
    bk, bf = parts.ENDS[axis_cfg["screw"]]
    return bk, bf, axis_cfg["screw_len"] - bk - bf


# ---------------------------------------------------------------- costruzione per gruppo
AL, STEEL = "custom", "commercial"


class Asm:
    def __init__(self):
        self.parts = {}

    def add(self, name, wp, group, kind, bom=None, color="gray"):
        self.parts[name] = dict(shape=wp.val() if hasattr(wp, "val") else wp, group=group,
                                kind=kind, bom=bom, color=color)


def head_box(cx, cy, coupling_z):
    h = P.HEAD
    return box(cx - h["W"] / 2, cx + h["W"] / 2, cy - h["D"] / 2, cy + h["D"] / 2, coupling_z - h["L"], coupling_z)


def transfer_path():
    """Traiettoria del centro testa (x, y, coupling z): magazine → sopra la trave → davanti → giù → lungo −X → dentro lungo +Y (D030)."""
    sx, sy = P.STORE_POSE
    top, dock_z, ya = P.TRANSFER_TOP, D["coupling_top"], P.DOCK_APPROACH_Y
    legs = [((sx, sy, top), (sx, ya, top)), ((sx, ya, top), (sx, ya, dock_z)), ((sx, ya, dock_z), (P.DOCK_X, ya, dock_z)),
            ((P.DOCK_X, ya, dock_z), (P.DOCK_X, 0.0, dock_z))]
    n = P.TRANSFER_STEPS
    lens = [math.dist(p0, p1) for p0, p1 in legs]
    pts = []
    for (p0, p1), ln in zip(legs, lens):
        k = max(2, round(n * ln / sum(lens)))
        pts += [tuple(p0[m] + (p1[m] - p0[m]) * i / k for m in range(3)) for i in range(k)]
    return pts + [legs[-1][1]]


def master_shape(X, cz, wall=None):
    """Master ToolDock scatolata (D029, D030) sotto la slitta Z, dal piano del coupling cz alla faccia inferiore della slitta."""
    M, mw = P.MASTER, (wall if wall is not None else P.MASTER["wall"])
    return box(X - M["W"] / 2, X + M["W"] / 2, -P.HEAD["D"] / 2, D["slide_back"], cz, cz + M["T"]).cut(
        box(X - M["W"] / 2 + mw, X + M["W"] / 2 - mw, -P.HEAD["D"] / 2 + mw, D["slide_back"] - mw, cz + mw, cz + M["T"] - mw))


def add_head(a, X, cz, S):
    """Testa reale di riferimento SycoTec 5045 AC-ER11 (D030) appesa sotto il coupling cz: receiver, mount a tazza
    con camicia, spindle e service envelope del connettore / cavo (D031, variante S["connector_mode"])."""
    z_top = cz - S["receiver_t"]
    z_rear = z_top - S["connector"]
    z_h1, z_h0 = z_rear - S["rear"], z_rear - S["rear"] - S["housing"]
    z_neck = z_h0 - S["neck"]
    z_nose = z_neck - S["nose"]
    rw = S["receiver_w"] / 2
    a.add("head_receiver", box(X - rw, X + rw, -rw, rw, z_top, cz), "ZSLIDE", AL, "MC-TD-002", "tomato")
    cb_ = S["clamp_block"] / 2
    zc0 = z_h1 - 10
    # mount a tazza chiusa dal receiver al fondo del collare: collare sul Ø45 h6, cavità per retro e connettore, finestra cavo
    env = P.CONNECTOR_ENVELOPES[S["connector_mode"]]
    win = max(25.0, env["bend_r"] + 10.0)
    mount = box(X - cb_, X + cb_, -cb_, cb_, zc0 - S["clamp_len"], z_top)
    mount = mount.cut(cyl("z", zc0 - S["clamp_len"] - 1, zc0 + 1, X, 0.0, S["d"] / 2 + 0.1))
    mount = mount.cut(cyl("z", zc0, z_top + 1, X, 0.0, S["d"] / 2 + 1.5))
    mount = mount.cut(box(X + 10, X + cb_ + 1, -19, 19, z_top - win, z_top + 1))     # finestra di uscita del cavo verso +x
    a.add("head_mount", mount, "ZSLIDE", AL, "MC-SP-003", "lightgray")
    spindle = (cyl("z", z_h1, z_rear, X, 0.0, 44.8 / 2).union(cyl("z", z_h0, z_h1, X, 0.0, S["d"] / 2))
               .union(cyl("z", z_neck, z_h0, X, 0.0, 44.8 / 2)).union(cyl("z", z_nose, z_neck, X, 0.0, S["nut_d"] / 2)))
    a.add("head_spindle", spindle, "ZSLIDE", STEEL, "MC-SP-001", "silver")
    # service envelope parametrico (D031): non è la geometria del connettore, è lo spazio riservato a spina e cavo
    a.add("head_connector", box(X - 15, X + max(15.0, env["side"]), -18, 18, z_rear, z_top), "ZSLIDE", "volume", None, "black")


def build(X, Y, Zd, cfg=None):
    a = Asm()
    zx, t_top, t_bot = D["zx"], D["table_top"], D["table_bottom"]
    xa, ya, za = P.X_AXIS, P.Y_AXIS, P.Z_AXIS
    L, U, BM, T, C = P.LADDER, P.UPRIGHT, P.BEAM, P.TABLE, P.PLATE
    xcen = P.TRAVEL["X"] / 2
    ytc = T["D"] / 2                    # centro tavola (locale)
    xtc = T["W"] / 2
    y_x_axis = D["beam_face"] + BM["recess_d"] - P.X_SCREW_PAD - P.SUPPORTS[xa["bk"]]["h"]
    y_z_axis = D["slide_back"] + P.SUPPORT_GAP_Z + P.SUPPORTS[za["bk"]]["h"]
    z_y_axis = -L["H"] + L["pad_t"] + P.SUPPORTS[ya["bk"]]["h"]      # vite Y fra i longheroni

    # ============ FRAME · telaio a scala (D027) ============
    H, w = L["H"], L["wall"]

    def rtube_y(x0, x1, y0, y1):     # tubo rettangolare con asse lungo Y
        return box(x0, x1, y0, y1, -H, 0).cut(box(x0 + w, x1 - w, y0 - 1, y1 + 1, -H + w, -w))

    dz = L["cross_drop"]                 # traverse ribassate sotto il passaggio dei pattini Y

    def rtube_x(x0, x1, y0, y1):     # tubo rettangolare con asse lungo X
        return box(x0, x1, y0, y1, -H, -dz).cut(box(x0 - 1, x1 + 1, y0 + w, y1 - w, -H + w, -w - dz))
    rails_x = (xtc - ya["rail_spacing"] / 2, xtc + ya["rail_spacing"] / 2)
    lw = L["long_w"]
    for tag, xr in zip("LR", rails_x):
        a.add(f"frame_longeron_{tag}", rtube_y(xr - lw / 2, xr + lw / 2, *L["long_y"]), "FRAME", AL, "MC-BAS-001", "gray")
    inner0, inner1 = rails_x[0] + lw / 2, rails_x[1] - lw / 2
    yc = (D["beam_face"] + D["beam_back"]) / 2
    rear_y = (yc - U["depth"] / 2, yc + U["depth"] / 2)
    pw = L["pocket_w"]
    pocket = box(xtc - pw / 2, xtc + pw / 2, -400, 400, -H + w, 1)        # passaggio chiocciola Y fino al fondo del tubo
    a.add("frame_cross_front", rtube_x(inner0, inner1, *L["front_y"]), "FRAME", AL, "MC-BAS-001", "gray")
    sy_th = ya["screw_len"] - sum(parts.ENDS[ya["screw"]])
    bf_pad = (-sy_th / 2 - P.SUPPORTS[ya["bf"]]["T"] - 5, -sy_th / 2)
    bk_pad = (sy_th / 2 + 2, sy_th / 2 + 2 + P.SUPPORTS[ya["bk"]]["T"] + 5)
    a.add("frame_cross_bf", rtube_x(inner0, inner1, *L["bf_y"]).cut(pocket).union(box(xtc - pw / 2, xtc + pw / 2, bf_pad[0], bf_pad[1], -H, -H + L["pad_t"])),
          "FRAME", AL, "MC-BAS-001", "gray")
    ry1 = max(rear_y[1], bk_pad[1] + 5)       # la traversa posteriore arriva sotto il supporto BK Y
    rear = box(P.BEAM_X[0], P.BEAM_X[1], rear_y[0], ry1, -H, -dz).cut(box(P.BEAM_X[0] - 1, P.BEAM_X[1] + 1, rear_y[0] + w, ry1 - w, -H + w, -w - dz))
    for xr in rails_x:   # i longheroni attraversano la traversa posteriore
        rear = rear.cut(box(xr - lw / 2, xr + lw / 2, rear_y[0] - 1, ry1 + 1, -H - 1, 1))
    rear = rear.cut(pocket).union(box(xtc - pw / 2, xtc + pw / 2, rear_y[0], ry1, -H, -H + w)).union(
        box(xtc - pw / 2, xtc + pw / 2, bk_pad[0], bk_pad[1], -H, -H + L["pad_t"]))
    a.add("frame_cross_rear", rear, "FRAME", AL, "MC-BAS-001", "gray")
    end = rtube_x(inner0, inner1, *L["end_y"]).cut(cyl("y", L["end_y"][0] - 1, L["end_y"][1] + 1, xtc, z_y_axis, 20))
    a.add("frame_cross_end", end, "FRAME", AL, "MC-BAS-001", "gray")

    for side, (x0, x1) in (("L", (P.BEAM_X[0], P.BEAM_X[0] + U["t"])), ("R", (P.BEAM_X[1] - U["t"], P.BEAM_X[1]))):
        uw = U["wall"]
        up = box(x0, x1, rear_y[0], rear_y[1], -dz, D["beam_bottom"]).cut(box(x0 + uw, x1 - uw, rear_y[0] + uw, rear_y[1] - uw, -dz + uw, D["beam_bottom"] - uw))
        a.add(f"upright_{side}", up, "FRAME", AL, "MC-GAN-002", "gray")

    bf, bb = D["beam_face"], D["beam_back"]
    bx0, bx1, t = P.BEAM_X[0], P.BEAM_X[1], BM["wall"]
    rh, rd = BM["recess_h"] / 2, BM["recess_d"]
    beam = box(bx0, bx1, bf, bb, D["beam_bottom"], D["beam_top"]).cut(
        box(bx0 + BM["end"], bx1 - BM["end"], bf + t, bb - t, D["beam_bottom"] + t, D["beam_top"] - t))
    beam = beam.cut(box(bx0 - 1, bx1 + 1, bf - 1, bf + rd, zx - rh, zx + rh))
    beam = (beam.union(box(bx0, bx1, bf + rd, bf + rd + t, zx - rh - t, zx + rh + t))
            .union(box(bx0, bx1, bf, bf + rd + t, zx + rh, zx + rh + t))
            .union(box(bx0, bx1, bf, bf + rd + t, zx - rh - t, zx - rh)))
    a.add("beam", beam, "FRAME", AL, "MC-GAN-001", "gray")

    x_rail0 = xcen - xa["rail_len"] / 2
    for tag, dz in (("top", xa["rail_spacing"] / 2), ("bot", -xa["rail_spacing"] / 2)):
        a.add(f"x_rail_{tag}", to_x_on_face(parts.rail(xa["rail"], xa["rail_len"])).translate((x_rail0, bf, zx + dz)),
              "FRAME", STEEL, "MC-LIN-151", "steelblue")

    bkx, bfx, thx = screw_ends(xa)
    sx0 = xcen - thx / 2 - bfx
    a.add("x_screw", screw_shaft(xa["screw"], xa["screw_len"]).translate((sx0, y_x_axis, zx)), "FRAME", STEEL, "MC-BS-1605X", "silver")
    rot_face = lambda wp: wp.rotate(ORIGIN, (1, 0, 0), 90)  # noqa: E731  normale di montaggio → −Y
    a.add("x_bf", rot_face(support(xa["bf"], sx0 + bfx - P.SUPPORTS[xa["bf"]]["T"])).translate((0, y_x_axis, zx)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("x_bk", rot_face(support(xa["bk"], sx0 + bfx + thx + 2)).translate((0, y_x_axis, zx)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("x_pads", box(sx0 - 10, sx0 + bfx, bf + rd - P.X_SCREW_PAD, bf + rd, zx - 30, zx + 30)
          .union(box(sx0 + bfx + thx + 2, sx0 + bfx + thx + 27, bf + rd - P.X_SCREW_PAD, bf + rd, zx - 30, zx + 30)),
          "FRAME", AL, "MC-BRK-001", "gray")
    mx = parts.MOTORS[xa["motor"]]
    cplx = P.COUPLING[xa["screw"]]
    a.add("x_coupling", tube("x", sx0 + xa["screw_len"] - 10, bx1 - mx[8] + 10, y_x_axis, zx, cplx["D"] / 2, parts.SCREWS[xa["screw"]]["d"] / 2 - 2 + 0.3),
          "FRAME", STEEL, "MC-CPL-001", "gold")
    a.add("x_motor_plate", box(bx1 - BM["end"], bx1, y_x_axis - 32, bf + rd, zx - 35, zx + 35).cut(cyl("x", bx1 - 10, bx1 + 1, y_x_axis, zx, 20)),
          "FRAME", AL, "MC-BRK-001", "gray")
    a.add("x_motor", parts.motor(xa["motor"]).rotate(ORIGIN, (0, 1, 0), 90).translate((bx1, y_x_axis, zx)), "FRAME", STEEL, "MC-MOT-001", "black")

    yr0 = -ya["rail_len"] / 2
    for tag, x in zip("LR", rails_x):
        a.add(f"y_rail_{tag}", to_y_on_floor(parts.rail(ya["rail"], ya["rail_len"])).translate((x, yr0, 0)), "FRAME", STEEL, "MC-LIN-155", "steelblue")
    bky, bfy, thy = screw_ends(ya)
    sy0 = -thy / 2 - bfy
    rot_y = lambda wp: wp.rotate(ORIGIN, (0, 0, 1), 90)  # noqa: E731
    a.add("y_screw", rot_y(screw_shaft(ya["screw"], ya["screw_len"])).translate((xtc, sy0, z_y_axis)), "FRAME", STEEL, "MC-BS-1605Y", "silver")
    a.add("y_bf", rot_y(support(ya["bf"], sy0 + bfy - P.SUPPORTS[ya["bf"]]["T"])).translate((xtc, 0, z_y_axis)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("y_bk", rot_y(support(ya["bk"], sy0 + bfy + thy + 2)).translate((xtc, 0, z_y_axis)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    my = parts.MOTORS[ya["motor"]]
    cply = P.COUPLING[ya["screw"]]
    a.add("y_coupling", tube("y", sy0 + ya["screw_len"] - 10, L["end_y"][1] - my[8] + 10, xtc, z_y_axis, cply["D"] / 2, parts.SCREWS[ya["screw"]]["d"] / 2 - 2 + 0.3),
          "FRAME", STEEL, "MC-CPL-001", "gold")
    a.add("y_motor", parts.motor(ya["motor"]).rotate(ORIGIN, (1, 0, 0), -90).translate((xtc, L["end_y"][1], z_y_axis)), "FRAME", STEEL, "MC-MOT-001", "black")

    # riserve di volume permanenti (nessuna davanti alla trave, D027)
    a.add("chain_x_volume", box(bx0, bx1, bf + P.CHAIN_X["inset"], bf + P.CHAIN_X["inset"] + P.CHAIN_X["w"], D["beam_top"], D["beam_top"] + P.CHAIN_X["h"]), "FRAME", "volume", None, "orange")
    a.add("chain_y_volume", box(P.CHAIN_Y["x0"], P.CHAIN_Y["x1"], L["long_y"][0], L["long_y"][1], 0, P.CHAIN_Y["h"]), "FRAME", "volume", None, "orange")
    M = P.MAGAZINE
    a.add("magazine_volume", box(*M["x"], *M["y"], *M["z"]), "FRAME", "volume", None, "violet")
    if cfg == "DOCK":   # alcune pose della testa lungo la traiettoria del trasferitore (solo visualizzazione)
        for k, (cx, cy, cz) in enumerate(transfer_path()[::10]):
            a.add(f"transfer_head_{k}", head_box(cx, cy, cz), "TRANSFER", "volume", None, "violet")

    # ============ TABLE (si muove in Y) ============
    g = P.GRID
    holes = [(g["x0"] + i * g["pitch"], g["y0"] + j * g["pitch"]) for i in range(g["nx"]) for j in range(g["ny"])]
    tb = box(0, T["W"], 0, T["D"], T["T"] - T["skin"], T["T"])
    tb = tb.union(box(0, T["W"], 0, T["rim"], 0, T["T"])).union(box(0, T["W"], T["D"] - T["rim"], T["D"], 0, T["T"]))
    tb = tb.union(box(0, T["rim"], 0, T["D"], 0, T["T"])).union(box(T["W"] - T["rim"], T["W"], 0, T["D"], 0, T["T"]))
    for (x, y) in holes + [P.R1, P.R2]:
        tb = tb.union(cyl("z", 0, T["T"], x, y, T["boss_d"] / 2))
    for x in rails_x:
        for y in (ytc - ya["block_pitch"] / 2, ytc + ya["block_pitch"] / 2):
            tb = tb.union(box(x - T["pad_w"] / 2, x + T["pad_w"] / 2, y - T["pad_l"] / 2, y + T["pad_l"] / 2, 0, T["T"]))
    ny = parts.SCREWS[ya["screw"]]
    tb = tb.union(box(xtc - 40, xtc + 40, ytc + ny["L"] / 2 - 5, ytc + ny["L"] / 2 + 25, 0, T["T"]))
    for (x, y) in holes:
        tb = tb.cut(cyl("z", -1, T["T"] + 1, x, y, g["hole"] / 2))
    tb = tb.cut(cyl("z", -1, T["T"] + 1, P.R1[0], P.R1[1], P.R_BORE / 2))
    tb = tb.cut(box(P.R2[0] - P.R2_SLOT / 2 + P.R_BORE / 2, P.R2[0] + P.R2_SLOT / 2 - P.R_BORE / 2, P.R2[1] - P.R_BORE / 2, P.R2[1] + P.R_BORE / 2, -1, T["T"] + 1)
                .union(cyl("z", -1, T["T"] + 1, P.R2[0] - P.R2_SLOT / 2 + P.R_BORE / 2, P.R2[1], P.R_BORE / 2))
                .union(cyl("z", -1, T["T"] + 1, P.R2[0] + P.R2_SLOT / 2 - P.R_BORE / 2, P.R2[1], P.R_BORE / 2)))
    a.add("table", tb.translate((0, -Y, t_bot)), "TABLE", AL, "MC-TBL-001", "lightgray")
    for i, x in enumerate(rails_x):
        for j, y in enumerate((ytc - ya["block_pitch"] / 2, ytc + ya["block_pitch"] / 2)):
            a.add(f"y_block_{i}{j}", to_y_on_floor(parts.block(ya["block"])).translate((x, y - Y, 0)), "TABLE", STEEL, "MC-LIN-156", "steelblue")
    nut_y0 = ytc - ny["L"] / 2 - Y
    a.add("y_nut", rot_y(screw_nut(ya["screw"], flange_end=True)).translate((xtc, nut_y0, z_y_axis)), "TABLE", STEEL, "MC-BS-1605Y", "silver")
    ny1 = nut_y0 + ny["L"]
    a.add("y_nut_bracket", box(xtc - 30, xtc + 30, ny1, ny1 + P.NUT_BRACKET_T, z_y_axis - 24, t_bot)
          .cut(cyl("y", ny1 - 1, ny1 + P.NUT_BRACKET_T + 1, xtc, z_y_axis, ny["d"] / 2 + 0.5)), "TABLE", AL, "MC-BRK-001", "gray")

    # ============ XCAR (si muove in X): guide Z, vite, supporti e motore Z fissi sul carrello ============
    cf, cb = D["carriage_front"], D["carriage_back"]
    zb = parts.BLOCKS[za["block"]]
    z_rail0 = D["z_rail_bottom"]
    z_rail1 = z_rail0 + za["rail_len"]
    tab_min = D["slide_bottom_low"] + C["slide_len"]      # fondo piastrina chiocciola con Z giù
    bkz, bfz, thz = screw_ends(za)
    zs0 = tab_min - P.SUPPORT_GAP_Z - bfz                  # BF sotto la piastrina, gioco D027
    z_screw_top = zs0 + za["screw_len"]
    tower_top = z_screw_top + 20
    car_bot = zx - xa["rail_spacing"] / 2 - parts.BLOCKS[xa["block"]]["W"] / 2 - C["below_x_blocks"]
    car = box(X - C["carriage_w"] / 2, X + C["carriage_w"] / 2, cf, cb, car_bot, z_rail1)
    car = car.union(box(X - C["tower_w"] / 2, X + C["tower_w"] / 2, cf, cb, z_rail1 - 1, tower_top))
    car = car.cut(box(X - C["slot_w"] / 2, X + C["slot_w"] / 2, cf - 1, cb + 1, zs0 - 10, tower_top + 1))
    cfl = P.CARRIAGE_FLANGE           # D030: ali in avanti ai lati, fuori dalla slitta e dal corridoio di docking (+Y)
    for sgn in (-1, 1):
        x_in, x_out = X + sgn * (C["carriage_w"] / 2), X + sgn * (C["carriage_w"] / 2 + cfl["t"])
        car = car.union(box(min(x_in, x_out), max(x_in, x_out), cf - cfl["depth"] - 10, cb, car_bot, z_rail1))
    a.add("x_carriage", car, "XCAR", AL, "MC-XC-001", "gray")
    for i, dz in enumerate((xa["rail_spacing"] / 2, -xa["rail_spacing"] / 2)):
        for j, dx in enumerate((-xa["block_pitch"] / 2, xa["block_pitch"] / 2)):
            a.add(f"x_block_{i}{j}", to_x_on_face(parts.block(xa["block"])).translate((X + dx, bf, zx + dz)), "XCAR", STEEL, "MC-LIN-152", "steelblue")
    to_z_minus_y = lambda wp: to_z_toward_y(wp).rotate(ORIGIN, (0, 0, 1), 180)  # noqa: E731  altezza → −Y
    for i, dx in enumerate((-za["rail_spacing"] / 2, za["rail_spacing"] / 2)):
        a.add(f"z_rail_{i}", to_z_minus_y(parts.rail(za["rail"], za["rail_len"])).translate((X + dx, cf, z_rail0)), "XCAR", STEEL, "MC-LIN-153", "steelblue")
    nx_ = parts.SCREWS[xa["screw"]]
    nut_x0 = X - nx_["L"] / 2
    a.add("x_nut", screw_nut(xa["screw"], flange_end=True).translate((nut_x0, y_x_axis, zx)), "XCAR", STEEL, "MC-BS-1605X", "silver")
    nx1 = nut_x0 + nx_["L"]
    a.add("x_nut_bracket", box(nx1, nx1 + P.NUT_BRACKET_T, cb, y_x_axis + 18, zx - 28, zx + 28)
          .cut(cyl("x", nx1 - 1, nx1 + P.NUT_BRACKET_T + 1, y_x_axis, zx, nx_["d"] / 2 + 0.5)), "XCAR", AL, "MC-BRK-001", "gray")
    rot_z = lambda wp: wp.rotate(ORIGIN, (0, 1, 0), -90).rotate(ORIGIN, (0, 0, 1), -90)  # noqa: E731
    a.add("z_screw", screw_shaft(za["screw"], za["screw_len"]).rotate(ORIGIN, (0, 1, 0), -90).translate((X, y_z_axis, zs0)), "XCAR", STEEL, "MC-BS-1204Z", "silver")

    def z_support(kind, z0):
        return rot_z(support(kind, z0)).translate((X, y_z_axis, 0))
    a.add("z_bf", z_support(za["bf"], zs0 + bfz - P.SUPPORTS[za["bf"]]["T"]), "XCAR", STEEL, "MC-BKBF-001", "dimgray")
    a.add("z_bk", z_support(za["bk"], zs0 + bfz + thz + 2), "XCAR", STEEL, "MC-BKBF-001", "dimgray")
    mz = parts.MOTORS[za["motor"]]
    cplz = P.COUPLING[za["screw"]]
    z_motor_face = tower_top + 10
    a.add("z_coupling", tube("z", z_screw_top - 10, z_motor_face - mz[8] + 10, X, y_z_axis, cplz["D"] / 2, parts.SCREWS[za["screw"]]["d"] / 2 - 2 + 0.3),
          "XCAR", STEEL, "MC-CPL-001", "gold")
    a.add("z_motor_bracket", box(X - 45, X + 45, y_z_axis - 30, y_z_axis + 30, tower_top, z_motor_face).cut(cyl("z", tower_top - 1, z_motor_face + 1, X, y_z_axis, 20)),
          "XCAR", AL, "MC-BRK-001", "gray")
    a.add("z_motor", parts.motor(za["motor"]).translate((X, y_z_axis, z_motor_face)), "XCAR", STEEL, "MC-MOT-001", "black")

    # ============ ZSLIDE (si muove in X e Z): slitta corta con i pattini Z ============
    sb = D["slide_bottom_low"] + (P.TRAVEL["Z"] - Zd)
    slide = box(X - C["slide_w"] / 2, X + C["slide_w"] / 2, D["slide_front"], D["slide_back"], sb, sb + C["slide_len"])
    sfl = P.SLIDE_FLANGE              # D030: ali anteriori sopra il piano del coupling
    for sgn in (-1, 1):
        x_out, x_in = X + sgn * C["slide_w"] / 2, X + sgn * (C["slide_w"] / 2 - sfl["t"])
        slide = slide.union(box(min(x_in, x_out), max(x_in, x_out), D["slide_front"] - sfl["depth"], D["slide_front"], sb, sb + C["slide_len"]))
    a.add("z_slide", slide, "ZSLIDE", AL, "MC-Z-001", "gray")
    zbc = sb + C["block_offset"] + zb["L"] / 2 + za["block_pitch"] / 2
    for i, dx in enumerate((-za["rail_spacing"] / 2, za["rail_spacing"] / 2)):
        for j, dz in enumerate((-za["block_pitch"] / 2, za["block_pitch"] / 2)):
            a.add(f"z_block_{i}{j}", to_z_minus_y(parts.block(za["block"])).translate((X + dx, cf, zbc + dz)), "ZSLIDE", STEEL, "MC-LIN-154", "steelblue")
    nz = parts.SCREWS[za["screw"]]
    tab0 = sb + C["slide_len"]
    a.add("z_nut_tab", box(X - 26, X + 26, D["slide_front"], y_z_axis + 22, tab0, tab0 + P.TAB_T).cut(cyl("z", tab0 - 1, tab0 + P.TAB_T + 1, X, y_z_axis, nz["d"] / 2 + 0.5)),
          "ZSLIDE", AL, "MC-BRK-001", "gray")
    a.add("z_nut", screw_nut(za["screw"]).rotate(ORIGIN, (0, 1, 0), -90).translate((X, y_z_axis, tab0 + P.TAB_T)), "ZSLIDE", STEEL, "MC-BS-1204Z", "silver")
    coupling_z = sb - P.MASTER["T"]
    a.add("tooldock_master", master_shape(X, coupling_z), "ZSLIDE", AL, "MC-TD-001", "tomato")
    add_head(a, X, coupling_z, P.SPINDLE)
    a.add("head_volume", box(X - P.HEAD["W"] / 2, X + P.HEAD["W"] / 2, -P.HEAD["D"] / 2, P.HEAD["D"] / 2, coupling_z - P.HEAD["L"], coupling_z),
          "ZSLIDE", "volume", None, "tomato")

    datums = {
        "MACHINE_ORIGIN": (0.0, 0.0, t_top),
        "PALLET_R1": (P.R1[0], P.R1[1] - Y, t_top),
        "PALLET_R2": (P.R2[0], P.R2[1] - Y, t_top),
        "TOOLDOCK_MASTER": (X, 0.0, coupling_z),
        "DOCK_POSITION": (P.DOCK_X, 0.0, D["coupling_top"]),
        "TOOL_TIP": (X, 0.0, coupling_z - P.HEAD["L"]),
    }
    return a, datums


# ---------------------------------------------------------------- analisi
DESIGNED = [  # coppie in moto relativo che si toccano per progetto (guida-pattino, vite-chiocciola, vite-foro)
    ("x_rail", "x_block"), ("y_rail", "y_block"), ("z_rail", "z_block"),
    ("x_screw", "x_nut"), ("y_screw", "y_nut"), ("z_screw", "z_nut"),
    ("x_screw", "x_nut_bracket"), ("y_screw", "y_nut_bracket"), ("z_screw", "z_nut_tab"),
    # tavola 6 mm sopra la rotaia Y: MGN15H H 16 − rotaia 10 (luce di catalogo)
    ("head_volume", "table"), ("y_rail", "table"), ("transfer_head", "head_volume"), ("transfer_head", "tooldock_master"),
    ("magazine_volume", "transfer_head"), ("head_volume", "head_"), ("transfer_head", "head_"), ("head_spindle", "table"),
    # superficie che porta la rotaia ↔ pattino: luce H1 di catalogo (HGH15 4,3 mm, MGN15 4 mm)
    ("beam", "x_block"), ("frame_longeron", "y_block"), ("x_carriage", "z_block"),
]


def designed(n1, n2):
    return any((n1.startswith(p) and n2.startswith(q)) or (n2.startswith(p) and n1.startswith(q)) for p, q in DESIGNED)


def bb_gap(b1, b2):
    dx = max(b1.xmin - b2.xmax, b2.xmin - b1.xmax, 0)
    dy = max(b1.ymin - b2.ymax, b2.ymin - b1.ymax, 0)
    dz = max(b1.zmin - b2.zmax, b2.zmin - b1.zmax, 0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def pair_check(n1, s1, n2, s2, b1, b2):
    """Ritorna ('collision', vol) | ('clear', dist) | None se lontani oltre CLEAR_PASS."""
    if bb_gap(b1, b2) > P.CLEAR_PASS:
        return None
    common = s1.intersect(s2)
    vol = common.Volume() if common is not None else 0.0
    if vol > 1.0:
        return ("collision", vol)
    ext = BRepExtrema_DistShapeShape(s1.wrapped, s2.wrapped)
    ext.Perform()
    return ("clear", ext.Value()) if ext.IsDone() else None


def level(dist):
    return "FAIL" if dist < P.CLEAR_FAIL - 0.05 else ("WARNING" if dist < P.CLEAR_PASS - 0.05 else "PASS")


def analyse(a, all_pairs):
    names = list(a.parts)
    bbs = {n: a.parts[n]["shape"].BoundingBox() for n in names}
    collisions, warnings = [], []
    for n1, n2 in itertools.combinations(names, 2):
        p1, p2 = a.parts[n1], a.parts[n2]
        if not all_pairs and p1["group"] == p2["group"]:
            continue
        if p1["group"] == p2["group"] == "TRANSFER":
            continue
        r = pair_check(n1, p1["shape"], n2, p2["shape"], bbs[n1], bbs[n2])
        if r is None:
            continue
        if r[0] == "collision" and not (designed(n1, n2) and ("TRANSFER" in (p1["group"], p2["group"]) or "volume" in (p1["kind"], p2["kind"]))):
            collisions.append(dict(a=n1, b=n2, volume_mm3=round(r[1], 1)))
            continue
        if r[0] == "collision" or p1["group"] == p2["group"] or designed(n1, n2):
            continue
        lv = level(r[1])
        if lv != "PASS":
            warnings.append(dict(a=n1, b=n2, clearance_mm=round(r[1], 2), level=lv))
    return collisions, warnings


GROUP_OFFSET = {"FRAME": lambda X, Y, Zd: (0, 0, 0), "TABLE": lambda X, Y, Zd: (0, -Y, 0),
                "XCAR": lambda X, Y, Zd: (X, 0, 0), "ZSLIDE": lambda X, Y, Zd: (X, 0, -Zd)}


def placed(base, X, Y, Zd):
    """Parti dell'assieme HOME spostate come corpi rigidi per gruppo (per lo sweep, senza ricostruire)."""
    out = {}
    for n, p in base.parts.items():
        if p["group"] not in GROUP_OFFSET:
            continue
        dx, dy, dz = GROUP_OFFSET[p["group"]](X, Y, Zd)
        sh = p["shape"] if (dx, dy, dz) == (0, 0, 0) else p["shape"].moved(cq.Location(cq.Vector(dx, dy, dz)))
        out[n] = dict(p, shape=sh)
    return out


def sweep():
    """Griglia SWEEP_N³ del workspace: solo collisioni e giochi tra gruppi in moto relativo."""
    base, _ = build(0.0, 0.0, 0.0)
    n = P.SWEEP_N
    grid = lambda T: [T * i / (n - 1) for i in range(n)]  # noqa: E731
    worst, collisions, count = {}, [], 0
    for X in grid(P.TRAVEL["X"]):
        for Y in grid(P.TRAVEL["Y"]):
            for Zd in grid(P.TRAVEL["Z"]):
                parts_ = placed(base, X, Y, Zd)
                names = list(parts_)
                bbs = {k: parts_[k]["shape"].BoundingBox() for k in names}
                count += 1
                for n1, n2 in itertools.combinations(names, 2):
                    g1, g2 = parts_[n1]["group"], parts_[n2]["group"]
                    if g1 == g2:
                        continue
                    r = pair_check(n1, parts_[n1]["shape"], n2, parts_[n2]["shape"], bbs[n1], bbs[n2])
                    if r is None:
                        continue
                    if r[0] == "collision":
                        if not designed(n1, n2):
                            collisions.append(dict(a=n1, b=n2, volume_mm3=round(r[1], 1), axes=[X, Y, -Zd]))
                        continue
                    if designed(n1, n2):
                        continue
                    key = f"{n1} ↔ {n2}"
                    if key not in worst or r[1] < worst[key][0]:
                        worst[key] = (r[1], [X, Y, -Zd])
    close = sorted(({"pair": k, "clearance_mm": round(v[0], 2), "axes": v[1], "level": level(v[0])} for k, v in worst.items()),
                   key=lambda d: d["clearance_mm"])
    return dict(configs=count, grid=n, collisions=collisions, closest=close[:20],
                fails=[c for c in close if c["level"] == "FAIL"], warnings=[c for c in close if c["level"] == "WARNING"])


def transfer_check():
    """Testa vera lungo la traiettoria del trasferitore, macchina in DOCK (X 440, Y 0, Z alto)."""
    X, Y, Zd = P.CONFIGS["DOCK"]
    base, _ = build(X, Y, Zd)
    others = {n: p for n, p in base.parts.items() if not n.startswith("head_") and n != "magazine_volume"}
    bbs = {n: p["shape"].BoundingBox() for n, p in others.items()}
    pts = transfer_path()
    worst, collisions = {}, []
    far = P.CLEAR_PASS
    P.CLEAR_PASS = 60.0          # per la traiettoria riporta anche i giochi fino a 60 mm
    for k, (cx, cy, cz) in enumerate(pts):
        hb = head_box(cx, cy, cz).val()
        hbb = hb.BoundingBox()
        for n, p in others.items():
            if n == "tooldock_master" and k == len(pts) - 1:
                continue            # a fine corsa la testa è sotto la master: contatto di progetto
            r = pair_check("head", hb, n, p["shape"], hbb, bbs[n])
            if r is None:
                continue
            if r[0] == "collision":
                collisions.append(dict(part=n, step=k, pose=[round(c, 1) for c in (cx, cy, cz)], volume_mm3=round(r[1], 1)))
            elif n != "tooldock_master" and (n not in worst or r[1] < worst[n][0]):
                worst[n] = (r[1], k)
    P.CLEAR_PASS = far
    close = sorted(({"part": n, "clearance_mm": round(v[0], 2), "step": v[1], "level": level(v[0])} for n, v in worst.items()),
                   key=lambda d: d["clearance_mm"])
    return dict(steps=len(pts), waypoints=[[round(c, 1) for c in pts[0]], [round(c, 1) for c in pts[-1]]],
                transfer_top=P.TRANSFER_TOP, collisions=collisions, closest=close[:10])


def dist(a, n1, n2):
    ext = BRepExtrema_DistShapeShape(a.parts[n1]["shape"].wrapped, a.parts[n2]["shape"].wrapped)
    ext.Perform()
    return round(ext.Value(), 1)


def travel_margins(a):
    """Margini a fine corsa: pattini dentro le rotaie (D019 ≥ 10 mm) e chiocciole dai supporti."""
    def bb(n):
        return a.parts[n]["shape"].BoundingBox()
    out = {}
    for ax, rail, blocks, lo, hi in (("X", "x_rail_top", ["x_block_00", "x_block_01"], "xmin", "xmax"),
                                     ("Y", "y_rail_L", ["y_block_00", "y_block_01"], "ymin", "ymax"),
                                     ("Z", "z_rail_0", ["z_block_00", "z_block_01"], "zmin", "zmax")):
        r = bb(rail)
        bmin = min(getattr(bb(b), lo) for b in blocks)
        bmax = max(getattr(bb(b), hi) for b in blocks)
        out[f"{ax}_rail_margin_mm"] = [round(bmin - getattr(r, lo), 1), round(getattr(r, hi) - bmax, 1)]
    out["nut_to_supports_mm"] = {
        "X": [dist(a, "x_nut", "x_bf"), dist(a, "x_nut_bracket", "x_bk")],
        "Y": [dist(a, "y_nut_bracket", "y_bk"), dist(a, "y_nut", "y_bf")],
        "Z": [dist(a, "z_nut", "z_bk"), dist(a, "z_nut_tab", "z_bf")],
    }
    return out


def bbox_of(a, only=None):
    xs, ys, zs = [], [], []
    for n, p in a.parts.items():
        if only and p["kind"] not in only:
            continue
        b = p["shape"].BoundingBox()
        xs += [b.xmin, b.xmax]; ys += [b.ymin, b.ymax]; zs += [b.zmin, b.zmax]
    return [round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1), round(min(zs), 1), round(max(zs), 1)]


def masses(a):
    import data_standard as S
    bom = {r[0]: r for _, rows in S.G for r in rows}
    custom, extra = {}, {}
    for n, p in a.parts.items():
        if p["kind"] != AL:
            continue
        kg = p["shape"].Volume() * P.AL_DENSITY
        (custom if p["bom"] in bom else extra)[n] = (p["bom"], round(kg, 2))
    by_id = {}
    for n, (bid, kg) in custom.items():
        by_id.setdefault(bid, 0.0)
        by_id[bid] += kg
    machine_bom = sum(r[4] * r[8] for r in bom.values() if r[9] == "M")
    replaced = sum(bom[i][4] * bom[i][8] for i in by_id)
    mule_total = machine_bom - replaced + sum(by_id.values()) + sum(kg for _, kg in extra.values())
    rows = [dict(bom=i, part=bom[i][2], bom_kg=round(bom[i][4] * bom[i][8], 2), mule_kg=round(v, 2)) for i, v in by_id.items()]
    return dict(custom=rows, not_in_bom=[dict(part=n, kg=kg) for n, (_, kg) in extra.items()],
                machine_bom_kg=round(machine_bom, 1), machine_mule_kg=round(mule_total, 1))


COLORS = {"gray": (0.62, 0.66, 0.72), "lightgray": (0.82, 0.84, 0.88), "steelblue": (0.27, 0.51, 0.71),
          "silver": (0.75, 0.75, 0.75), "dimgray": (0.41, 0.41, 0.41), "gold": (0.85, 0.65, 0.13),
          "black": (0.1, 0.1, 0.12), "orange": (1.0, 0.55, 0.0), "violet": (0.6, 0.4, 0.9), "tomato": (1.0, 0.39, 0.28)}


def export_step(a, datums, path):
    asm = cq.Assembly(name="MultiCNC_Standard_mule")
    for n, p in a.parts.items():
        asm.add(cq.Workplane().add(p["shape"]), name=n, color=cq.Color(*COLORS[p["color"]], 0.35 if p["kind"] == "volume" else 1.0))
    for n, (x, y, z) in datums.items():
        asm.add(cq.Workplane().sphere(3).translate((x, y, z)), name=f"DATUM_{n}", color=cq.Color(1, 0, 0))
    asm.save(str(path))


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    write_step = "--no-step" not in sys.argv
    report = dict(generated_by="tools/cad/standard_assembly.py", derived={k: round(v, 1) for k, v in D.items()},
                  params=dict(travel=P.TRAVEL, x=P.X_AXIS, y=P.Y_AXIS, z=P.Z_AXIS, dock_x=P.DOCK_X, magazine=P.MAGAZINE), configs={})
    env = []
    for cfg, (X, Y, Zd) in P.CONFIGS.items():
        a, datums = build(X, Y, Zd, cfg)
        col, warn = analyse(a, all_pairs=(cfg == "HOME"))
        bb = bbox_of(a, only={AL, STEEL})
        env.append(bb)
        entry = dict(axes=dict(X=X, Y=Y, Z=-Zd if Zd else 0.0), parts=len(a.parts), bbox_mm=bb, margins=travel_margins(a),
                     collisions=col, clearance_warnings=warn,
                     datums={k: [round(c, 1) for c in v] for k, v in datums.items()})
        if write_step:
            path = OUT / f"standard_mule_{cfg.lower()}.step"
            export_step(a, datums, path)
            entry["step"] = f"cad/standard/{path.name}"
        report["configs"][cfg] = entry
        print(f"{cfg:6} parti {len(a.parts)} · collisioni {len(col)} · avvisi gioco {len(warn)} · bbox {bb}")
        for c in col:
            print("   COLLISIONE", c)
        for w in warn:
            print("   gioco", w)
        if cfg == "HOME":
            report["mass"] = masses(a)
            report["head"] = head_report(a)
    report["envelope_mm"] = [min(b[0] for b in env), max(b[1] for b in env), min(b[2] for b in env),
                             max(b[3] for b in env), min(b[4] for b in env), max(b[5] for b in env)]
    e = report["envelope_mm"]
    report["footprint_mm"] = [round(e[1] - e[0], 1), round(e[3] - e[2], 1)]
    report["height_mm"] = round(e[5] - e[4], 1)
    t1 = time.time()
    report["sweep"] = sweep()
    sw = report["sweep"]
    print(f"sweep {sw['configs']} configurazioni · collisioni {len(sw['collisions'])} · FAIL {len(sw['fails'])} · WARNING {len(sw['warnings'])} · {time.time() - t1:.0f} s")
    for c in sw["closest"][:8]:
        print("   ", c)
    report["transfer"] = transfer_check()
    tr = report["transfer"]
    print(f"trasferitore {tr['steps']} pose · collisioni {len(tr['collisions'])} · più vicini {tr['closest'][:4]}")
    report["stiffness"] = stiffness_report()
    report["connector_variants"] = connector_variants()
    for mode, v in report["connector_variants"].items():
        print("connettore", mode, "L", v["L"], "CoG", v["cog_below_coupling"], "kg", v["mass"], "k", v["k"])
    report["checks"] = design_checks(report)
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if write_step:
        write_page(report)
    print("massa", report["mass"]["machine_mule_kg"], "kg (BOM", report["mass"]["machine_bom_kg"], ")",
          "footprint", report["footprint_mm"], "altezza", report["height_mm"], f"· {time.time() - t0:.0f} s")



# ---------------------------------------------------------------- verifiche di progetto e pagina
K_TIP_RAILS = 30.0       # D015: rigidezza alla punta dovuta alle guide X, N/µm
K_BLOCK = {"Z0": 196.0, "ZA": 365.0, "ZB": 483.0}   # HGH15CA radiale, HIWIN G99TE23-2203 (D022)
D015_ASSUMED = dict(a=80.0, b=180.0)


V0 = dict(b=455.7, height=1003.7, mass=50.5, collisions=1, zx=481.7)   # mule v0, commit 3e5d70a
V1 = dict(b=220.0, height=850.0, mass=41.8, a=153.0, k=(0.43, 0.18, 0.80))  # mule v1.1, commit 151b3a0 (D028)


def head_report(a, S=None, cz=None):
    """Massa e baricentro della testa reale sotto il coupling (D016 / ICD v4: ≤ 80 mm; deroga D031 ≤ 100 mm)."""
    S = S or P.SPINDLE
    cz = a.parts["tooldock_master"]["shape"].BoundingBox().zmin if cz is None else cz
    items = []
    for n in ("head_receiver", "head_mount"):
        sh = a.parts[n]["shape"]
        items.append((sh.Volume() * P.AL_DENSITY, sh.Center().z))
    sp = a.parts["head_spindle"]["shape"].BoundingBox()
    z_h1 = cz - S["receiver_t"] - S["connector"] - S["rear"]
    items.append((S["mass"], z_h1 - S["housing"] / 2))
    m = sum(k for k, _ in items)
    cog = cz - sum(k * z for k, z in items) / m
    return dict(mass=round(m, 2), cog_below_coupling=round(cog, 0), L=round(cz - sp.zmin, 1), ref=S["ref"],
                inertia_moment_Nm=round(m * 2.0 * cog / 1000, 2), connector_mode=S["connector_mode"], gap=S["connector"])


def connector_variants():
    """D031: la stessa testa con i due service envelope del connettore; rigidezza D028 al centro corsa, coupling invariato."""
    out = {}
    base = P.SPINDLE
    try:
        for mode, env in P.CONNECTOR_ENVELOPES.items():
            S = P.spindle(mode)
            h = Asm()
            add_head(h, 0.0, 0.0, S)
            r = head_report(h, S, 0.0)
            P.SPINDLE = S
            k = stiffness_report()
            r.update(k={ax: k[ax]["N_per_um"] for ax in "XYZ"}, fits_L=r["L"] <= P.HEAD["L"] + 0.5,
                     z_loss=round(max(0.0, r["L"] - P.HEAD["L"]), 1), note=env["note"], plug=env["plug"], bend_r=env["bend_r"])
            out[mode] = r
    finally:
        P.SPINDLE = base
    return out


def stiffness_report():
    """Rigidezza alla punta del mule corrente con il modello D028 (centro corsa)."""
    sys.path.insert(0, str(ROOT / "tools" / "calc"))
    import compliance_d028 as C
    C.D = P.derived()
    r = C.compliance(*P.CONFIGS["CENTER"])
    r.pop("_mass", None)
    return {ax: dict(N_per_um=round(r[ax]["N_per_um"], 2),
                     top=sorted(((k, round(v * 100)) for k, v in r[ax]["share"].items() if v > 0.04), key=lambda t: -t[1])[:4]) for ax in "XYZ"}


def design_checks(report):
    h = P.X_AXIS["rail_spacing"]
    b = D["b_tip_below_x_rails"]

    def kmin(bb):
        return K_TIP_RAILS * (0.25 + (bb / h) ** 2)
    m = report["mass"]
    col = {c: len(v["collisions"]) for c, v in report["configs"].items()}
    warn = {c: len(v["clearance_warnings"]) for c, v in report["configs"].items()}
    return dict(
        d015=dict(h=h, b_assumed=D015_ASSUMED["b"], b_real=round(b, 1), a_assumed=D015_ASSUMED["a"], a_real=round(D["a_tool_to_x_face"], 1),
                  k_min_real=round(kmin(b), 0), k_za=K_BLOCK["ZA"], margin_za=round(K_BLOCK["ZA"] / kmin(b), 1),
                  pass_real=kmin(b) <= K_BLOCK["ZA"], b_ok=b <= P.B_TARGET[1], z_lever=round(D["z_lever_low"], 1)),
        mass=dict(mule=m["machine_mule_kg"], bom=m["machine_bom_kg"], gate=P.MASS_GATE_KG, target=P.MASS_TARGET_KG,
                  pass_gate=m["machine_mule_kg"] <= P.MASS_GATE_KG + 0.05, pass_target=m["machine_mule_kg"] <= P.MASS_TARGET_KG + 0.05),
        collisions=col, warnings=warn,
    )


def fmt(x):
    if isinstance(x, float):
        s = f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return s[:-2] if s.endswith(",0") else s
    return str(x)


def write_page(report):
    c = report["checks"]
    d15 = c["d015"]
    e = report["envelope_mm"]
    rows_cfg = ""
    for cfg, v in report["configs"].items():
        ax = v["axes"]
        colls = "<br>".join(f'{x["a"]} ↔ {x["b"]} · {fmt(x["volume_mm3"])} mm³' for x in v["collisions"]) or "nessuna"
        warns = "<br>".join(f'{x["a"]} ↔ {x["b"]} · {fmt(x["clearance_mm"])} mm' for x in v["clearance_warnings"]) or "nessuno"
        mg = v["margins"]
        marg = " · ".join(f'{k[0]} {fmt(min(mg[k]))}' for k in ("X_rail_margin_mm", "Y_rail_margin_mm", "Z_rail_margin_mm"))
        nuts = " · ".join(f'{k} {fmt(min(vv))}' for k, vv in mg["nut_to_supports_mm"].items())
        cls = "status-critical" if v["collisions"] else "status-ok"
        step = f'<a href="../{v["step"]}" download style="color:var(--accent-2)">STEP ↓</a>' if "step" in v else ""
        rows_cfg += (f'<tr><td><b>{cfg}</b></td><td style="white-space:nowrap">X {fmt(ax["X"])}<br>Y {fmt(ax["Y"])}<br>Z {fmt(ax["Z"] + 0.0)}</td>'
                     f'<td class="{cls}">{colls}</td><td>{warns}</td><td>{marg}</td><td>{nuts}</td><td>{step}</td></tr>\n')
    m = report["mass"]
    mass_rows = "".join(f'<tr><td>{r["bom"]}</td><td>{r["part"]}</td><td>{fmt(r["mule_kg"])}</td></tr>' for r in m["custom"])
    home = report["configs"]["HOME"]["datums"]
    dat_rows = "".join(f'<tr><td><code>{k}</code></td><td>{", ".join(fmt(v) for v in xyz)}</td></tr>' for k, xyz in home.items())
    ok, ko = '<td class="status-ok">PASSA</td>', '<td class="status-critical">NON PASSA</td>'
    warn_td = '<td class="status-target">WARNING</td>'
    sw, tr, hd, kk = report["sweep"], report["transfer"], report["head"], report["stiffness"]
    part_ok = '<td class="status-target">PARZIALE</td>'
    nocoll = not any(c["collisions"].values())
    nowarn = not any(c["warnings"].values())
    crit = [
        ("Un solo file di parametri <code>tools/cad/standard_params.py</code>", ok, ""),
        ("Assieme <code>tools/cad/standard_assembly.py</code>, configurazioni HOME / CENTER / MAX / DOCK", ok, ""),
        ("Guide, pattini, viti e motori dai modelli MultiCNC", part_ok, "Stesse funzioni di <code>parts.py</code> che generano gli STEP; pattini e chiocciole istanziati a parte perché si muovono"),
        ("Custom: telaio, spalle, trave, tavola Y, slitta Z, carrello X, staffe", ok, ""),
        ("Datum MACHINE_ORIGIN, PALLET_R1/R2, TOOLDOCK_MASTER, DOCK_POSITION", ok, ""),
        ("Corse reali 450 × 350 × 140 con margini D019 ≥ 10 mm", ok, ""),
        ("X HGR15/HGH15CA ZA 640 · Y MGN15H Z1 630 + SFU1605 centrale · Z HGR15/HGH15CA 310 + SFU1204 260", ok, ""),
        ("Tavola 450 × 350 × 10, R1/R2, griglia 9 × 7", ok, ""),
        ("A · Pattini Z sulla slitta, guide, vite, BK/BF e motore Z sul carrello", ok, ""),
        (f"D030 · Testa {hd['ref']} appesa, coupling → dado ≤ {fmt(P.HEAD['L'])} mm", ok if hd["L"] <= P.HEAD["L"] + 0.5 else ko, f'{fmt(hd["L"])} mm con service envelope {hd["connector_mode"]} ({fmt(hd["gap"])} mm): ipotesi, non quota del fornitore (D031)'),
        (f"D030 · Asse spindle a {fmt(P.HEAD_AXIS_FROM_SLIDE)} mm dalla slitta, inviluppo ICD v4 a ≥ {fmt(P.CLEAR_PASS)} mm", ok if not sw["fails"] else ko, "Congelato per la Standard v2 (D031); 40 mm resta solo uno scenario ICD v5"),
        (f"D030 · Testa ≤ 4 kg (classe S)", ok if hd["mass"] <= 4.0 else ko, f'{fmt(hd["mass"])} kg'),
        (f"D030 · Baricentro testa ≤ {fmt(P.HEAD_COG_MAX)} mm sotto il coupling (ICD v4)", ok if hd["cog_below_coupling"] <= P.HEAD_COG_MAX else ko,
         f'{fmt(hd["cog_below_coupling"])} mm; momento d\'inerzia sul clamp {fmt(hd["inertia_moment_Nm"])} N·m a 2 m/s² contro ~18 N·m di taglio (D014)'),
        (f"D031 · Deroga provvisoria Standard: baricentro ≤ {fmt(P.HEAD_COG_WAIVER)} mm (golden reference)", ok if hd["cog_below_coupling"] <= P.HEAD_COG_WAIVER else ko,
         "ICD v4 invariata; con lo spindle OEM: &lt; 80 nessun problema, 95–100 revisione della classe S, &gt; 100 testa da riprogettare"),
        (f"A · b ≤ {fmt(P.B_TARGET[1])} mm e D015 verificata con a e b misurati", ok if d15["b_ok"] and d15["pass_real"] else ko, f'b = {fmt(d15["b_real"])} mm · {fmt(d15["k_min_real"])} N/µm richiesti · ZA ×{fmt(d15["margin_za"])}'),
        ("B · Telaio a scala separato dalla cabina", ok, "Longheroni Y + traverse fronte / BF / posteriore / motore"),
        (f"C · Docking unico a X {fmt(P.DOCK_X)}, magazine dietro la spalla destra, nessun volume permanente davanti alla trave", ok, "Corridoio del trasferitore controllato solo in DOCK"),
        ("Nessuna collisione in HOME, CENTER, MAX, DOCK", ok if nocoll else ko, ""),
        (f"Sweep {sw['grid']} × {sw['grid']} × {sw['grid']} = {sw['configs']} configurazioni, vertici compresi: nessuna collisione", ok if not sw["collisions"] else ko, "Solo verifica, senza STEP"),
        (f"Giochi: &lt; {fmt(P.CLEAR_FAIL)} mm FAIL · {fmt(P.CLEAR_FAIL)}–{fmt(P.CLEAR_PASS)} mm WARNING · ≥ {fmt(P.CLEAR_PASS)} mm PASS", ok if not sw["fails"] and not sw["warnings"] and nowarn else (warn_td if not sw["fails"] else ko),
         f'{len(sw["fails"])} FAIL · {len(sw["warnings"])} WARNING nello sweep; gioco minimo {fmt(sw["closest"][0]["clearance_mm"]) if sw["closest"] else "—"} mm'),
        (f"Trasferitore: testa reale lungo {tr['steps']} pose magazine → dock", ok if not tr["collisions"] else ko, f'gioco minimo {fmt(tr["closest"][0]["clearance_mm"])} mm ({tr["closest"][0]["part"]})' if tr["closest"] else ""),
        (f"D · Soglia dura massa ≤ {fmt(P.MASS_GATE_KG)} kg", ok if c["mass"]["pass_gate"] else ko, f'{fmt(c["mass"]["mule"])} kg nel mule · {fmt(c["mass"]["bom"])} kg in BOM: accettato come prototipo strutturale sovrappeso (D031), 42 kg resta hard target'),
        (f"D · Target di progetto ≤ {fmt(P.MASS_TARGET_KG)} kg prima di cablaggi e dettagli", ok if c["mass"]["pass_target"] else warn_td, f'mancano {fmt(round(c["mass"]["mule"] - P.MASS_TARGET_KG, 1))} kg: alleggerimento solo dopo la FEA a solidi D031'),
        ("D014 · Rigidezza alla punta ≥ 10 N/µm (TARGET, modello D028)", ko, f'{fmt(kk["X"]["N_per_um"])} / {fmt(kk["Y"]["N_per_um"])} / {fmt(kk["Z"]["N_per_um"])} N/µm in X / Y / Z al centro corsa'),
    ]
    crit_rows = "".join(f"<tr><td>{t}</td>{r}<td>{n}</td></tr>" for t, r, n in crit)
    kv = " / ".join(fmt(kk[ax]["N_per_um"]) for ax in "XYZ")
    cmp_rows = "".join(f"<tr><td>{k}</td><td>{v0}</td><td>{v1}</td><td><b>{v2}</b></td></tr>" for k, v0, v1, v2 in [
        ("Braccio b (punta ↔ guide X, Z giù)", f'{fmt(V0["b"])} mm', f'{fmt(V1["b"])} mm', f'{fmt(d15["b_real"])} mm'),
        ("Braccio a (asse ↔ faccia trave)", "153 mm", f'{fmt(V1["a"])} mm', f'{fmt(d15["a_real"])} mm'),
        ("Testa", "inviluppo rigido", "inviluppo rigido", f'SycoTec 5045 reale, {fmt(hd["mass"])} kg'),
        ("Rigidezza X / Y / Z (N/µm, D028)", "—", " / ".join(fmt(v) for v in V1["k"]), kv),
        ("Altezza macchina", f'{fmt(V0["height"])} mm', f'{fmt(V1["height"])} mm', f'{fmt(report["height_mm"])} mm'),
        ("Massa macchina", f'{fmt(V0["mass"])} kg', f'{fmt(V1["mass"])} kg', f'{fmt(c["mass"]["mule"])} kg'),
        ("Collisioni nello sweep", str(V0["collisions"]), "0", str(len(sw["collisions"]))),
    ])
    cv = []
    for mode, v in report["connector_variants"].items():
        extra = "" if v["fits_L"] else " · +" + fmt(v["z_loss"])
        lcls = "status-ok" if v["fits_L"] else "status-critical"
        g = v["cog_below_coupling"]
        gcls = "status-ok" if g <= P.HEAD_COG_MAX else ("status-target" if g <= P.HEAD_COG_WAIVER else "status-critical")
        kx = " / ".join(fmt(v["k"][ax]) for ax in "XYZ")
        cv.append(f'<tr><td>{mode}</td><td>{fmt(v["gap"])} mm</td><td class="{lcls}">{fmt(v["L"])} mm{extra}</td>'
                  f'<td class="{gcls}">{fmt(g)} mm</td><td>{fmt(v["mass"])} kg</td><td>{kx}</td><td>{v["note"]}</td></tr>')
    cv_rows = "".join(cv)
    k_rows = "".join(f'<tr><td>{ax}</td><td>{fmt(kk[ax]["N_per_um"])}</td><td>{" · ".join(f"{t} {v}%" for t, v in kk[ax]["top"])}</td></tr>' for ax in "XYZ")
    views = "".join(f'<figure style="margin:0"><img src="../cad/standard/views/{n}.png" alt="Mule Standard {n}" style="width:100%;background:#fff;border-radius:10px"><figcaption style="color:var(--dim);font-size:12px;margin-top:6px">{n.replace("_", " · ").upper()}</figcaption></figure>'
                    for n in ("home_iso", "dock_iso", "max_iso", "max_front", "max_side", "dock_top"))
    sw_rows = "".join(f'<tr><td>{x["pair"]}</td><td class="{ {"PASS": "status-ok", "WARNING": "status-target", "FAIL": "status-critical"}[x["level"]] }">{fmt(x["clearance_mm"])} mm · {x["level"]}</td><td>X {fmt(float(x["axes"][0]))} · Y {fmt(float(x["axes"][1]))} · Z {fmt(float(x["axes"][2]) + 0.0)}</td></tr>' for x in sw["closest"][:10])
    tr_rows = "".join(f'<tr><td>{x["part"]}</td><td class="status-ok">{fmt(x["clearance_mm"])} mm</td><td>posa {x["step"]} di {tr["steps"]}</td></tr>' for x in tr["closest"][:6])
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — CAD Standard · mule</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/cad/standard_assembly.py: non modificare a mano. -->
<a class="back" href="index.html">← Base Standard</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · CAD v2 · digital mule · D030 / D031</div><h1>Digital mule<br>Standard v2.</h1><p class="lead">Assieme parametrico dimensionale della Standard, brutto ma corretto. Il v2 monta la testa corta di riferimento {hd["ref"]} appesa sotto il coupling (golden reference, non fornitore di produzione), con master scatolata, slitta Z e carrello X a canale e spalle scatolate, sulla stessa architettura del v1 (trave bassa, telaio a scala, docking a X {fmt(P.DOCK_X)} con magazine dietro la spalla destra). ICD meccanica v4 invariata. Tutte le quote vengono da <code>tools/cad/standard_params.py</code>; lo script costruisce l'assieme in HOME, CENTER, MAX e DOCK, cerca collisioni e giochi, misura ingombri e masse e rigenera questa pagina.</p><div class="badges"><span class="badge ok">CAD v2 · mule</span><span class="badge">{report["configs"]["HOME"]["parts"]} parti · 4 configurazioni</span><span class="badge">Valori MULE da rivedere</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{kv}</strong><span>N/µm alla punta X / Y / Z · target D014 ≥ 10</span></div>
  <div class="metric"><strong>{fmt(report["height_mm"])}</strong><span>mm · altezza, dal fondo telaio al motore Z</span></div>
  <div class="metric"><strong>{fmt(c["mass"]["mule"])} kg</strong><span>massa macchina · soglia dura {fmt(P.MASS_GATE_KG)} kg</span></div>
  <div class="metric"><strong>{len(sw["collisions"])} · {len(sw["fails"])} · {len(sw["warnings"])}</strong><span>collisioni · FAIL · WARNING su {sw["configs"]} configurazioni</span></div>
</section>

<section class="section"><h2>Criteri di accettazione</h2><div class="table-wrap"><table>
<tr><th>Criterio</th><th>Esito</th><th>Nota</th></tr>
{crit_rows}
</table></div></section>

<section class="section split">
  <div class="panel"><span class="kicker">v0 → v1 → v2</span><h2>Più rigida vicino alla punta.</h2><div class="table-wrap"><table><tr><th>Grandezza</th><th>v0</th><th>v1.1</th><th>v2</th></tr>{cmp_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Rigidezza del mule corrente dal modello D028 al centro corsa, punto di misura sul dado ER11:</p><div class="table-wrap"><table><tr><th>Asse</th><th>N/µm</th><th>Contributi principali</th></tr>{k_rows}</table></div></div>
  <div class="panel"><span class="kicker">Masse dal mule</span><h2>{fmt(c["mass"]["mule"])} kg.</h2><div class="table-wrap"><table><tr><th>Riga BOM</th><th>Parte</th><th>kg</th></tr>{mass_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">La BOM Standard usa queste masse ({fmt(m["machine_bom_kg"])} kg); commerciali ed elettronica con le masse della BOM. Il v2 supera la soglia dura: carrello a canale, master scatolata, mount e receiver della testa reale pesano più delle piastre del v1. D031: 42 kg resta hard target e il v2 è accettato come prototipo strutturale sovrappeso. Le leve misurate (ali 20 mm, master e spalle con pareti sottili) arrivano a ~43,4 kg perdendo rigidezza e non si applicano; la trave con parete 5 mm toglie ~1 kg quasi senza perdita ed è una variante della FEA a solidi, non una modifica congelata.</p></div>
</section>

<section class="section"><h2>Connettore · service envelope D031</h2><p>Il connettore M23 non è una quota: il mule riserva uno spazio parametrico per spina e cavo tra receiver e retro dello spindle, in due varianti. Il mule (sweep e STEP) usa <b>{P.CONNECTOR_MODE}</b>; l'altra si confronta sulla sola testa con il coupling nella stessa posizione. Si sostituiscono entrambe con il disegno del connettore del fornitore.</p><div class="table-wrap"><table><tr><th>Variante</th><th>Spazio sopra il retro</th><th>Coupling → dado</th><th>Baricentro</th><th>Testa</th><th>X / Y / Z (N/µm)</th><th>Nota</th></tr>{cv_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Con la presa assiale la testa esce dall'inviluppo classe S: a parità di coupling la punta scende e la corsa Z utile si riduce della stessa quantità, oppure trave e coupling salgono. Il budget del 90° è tutto lo spazio che L {fmt(P.HEAD["L"])} lascia: un connettore a 90° reale più alto sfora.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">ToolDock · D021 / D027</span><h2>Docking a X {fmt(P.DOCK_X)}.</h2><p>Posizione unica di docking a X {fmt(P.DOCK_X)}, Y 0, coupling a {fmt(D["coupling_top"])} mm con Z in alto: 10 mm prima del fine corsa, dentro i 450 mm utili. Il magazine indicizzato sta dietro la spalla destra (volume riservato {fmt(P.MAGAZINE["x"][1] - P.MAGAZINE["x"][0])} × {fmt(P.MAGAZINE["y"][1] - P.MAGAZINE["y"][0])} × {fmt(P.MAGAZINE["z"][1] - P.MAGAZINE["z"][0])} mm). Solo la testa selezionata arriva davanti alla trave: il trasferitore la solleva sopra trave e catena X nel corridoio x {fmt(P.TRANSFER_X[0])}–{fmt(P.TRANSFER_X[1])}, oltre il carrello, la porta davanti alla macchina (y {fmt(P.DOCK_APPROACH_Y)}), la abbassa, la allinea lungo −X e la presenta lungo +Y sotto la master (D030: le ali del carrello impediscono l\'ingresso lungo −X). D031: +Y è solo il percorso di presentazione del magazine; l\'accoppiamento cinematico, il pull-stud e lo sgancio a camma restano sul moto Z della CNC (D016): trasferitore +Y → testa in posizione → pickup / drop in Z. Il corridoio esiste solo durante il cambio e viene controllato in DOCK. Il meccanismo del trasferitore è da progettare.</p></div>
  <div class="panel"><span class="kicker">Ingombri</span><h2>Motori ancora a sbalzo.</h2><p>Inviluppo X {fmt(e[0])} … {fmt(e[1])}, Y {fmt(e[2])} … {fmt(e[3])}, Z {fmt(e[4])} … {fmt(e[5])} mm, footprint {fmt(report["footprint_mm"][0])} × {fmt(report["footprint_mm"][1])} mm con i motori. Il motore X sporge oltre la trave e il motore Y oltre il telaio di ~97 mm; il motore Z sul carrello porta l'altezza a {fmt(report["height_mm"])} mm. Rinvii a cinghia da valutare quando la meccanica è chiusa. Il magazine aggiunge profondità dietro il ponte fino a y = {fmt(P.MAGAZINE["y"][1])}.</p></div>
</section>

<section class="section"><h2>Configurazioni</h2><div class="table-wrap"><table>
<tr><th>Config</th><th>Assi</th><th>Collisioni</th><th>Giochi &lt; {fmt(P.CLEAR_PASS)} mm</th><th>Margine pattini-rotaie (mm)</th><th>Chiocciola-supporti (mm)</th><th>Assieme</th></tr>
{rows_cfg}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Collisione = volume comune &gt; 1 mm³. Giochi controllati tra parti in moto relativo, escluse le coppie che si toccano per progetto (guida-pattino, vite-chiocciola, vite-foro, punta-tavola a Z giù, testa-master nel corridoio) e la luce H1 di catalogo tra superficie di montaggio e pattino. Volumi riservati (catene, magazine, testa, corridoio) inclusi nel controllo.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Sweep del workspace</span><h2>{sw["configs"]} configurazioni.</h2><p>Griglia {sw["grid"]} × {sw["grid"]} × {sw["grid"]} su X, Y e Z, vertici del cubo compresi: nessuna collisione, {len(sw["fails"])} FAIL, {len(sw["warnings"])} WARNING. I dieci giochi più piccoli tra parti in moto relativo:</p><div class="table-wrap"><table><tr><th>Coppia</th><th>Gioco</th><th>Dove (peggiore)</th></tr>{sw_rows}</table></div></div>
  <div class="panel"><span class="kicker">Trasferitore</span><h2>La testa vera, posa per posa.</h2><p>Testa {fmt(P.HEAD["W"])} × {fmt(P.HEAD["D"])} × {fmt(P.HEAD["L"])} mm lungo {tr["steps"]} pose: magazine ({fmt(P.STORE_POSE[0])}, {fmt(P.STORE_POSE[1])}) → sopra trave e catena X con coupling a {fmt(P.TRANSFER_TOP)} mm → davanti → giù a {fmt(D["coupling_top"])} mm → lungo −X fino a X {fmt(P.DOCK_X)} → presentazione lungo +Y sotto la master. Macchina in DOCK. Nessuna collisione; i giochi più piccoli:</p><div class="table-wrap"><table><tr><th>Parte</th><th>Gioco</th><th>Dove</th></tr>{tr_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Da progettare nel trasferitore: ritenuta meccanica della testa da 4 kg anche senza alimentazione, e la forcella di presentazione deve reggere la reazione di sgancio D016 (~0,7 kN sullo Z) senza fare da molla attaccata alla trave.</p></div>
</section>

<section class="section"><div class="callout"><b>Corsa Z ≠ altezza massima del pezzo.</b> Sotto la trave ci sono {fmt(P.CLEAR_UNDER_BEAM)} mm sopra la tavola. Con un pallet da {fmt(P.PALLET_T)} mm il pezzo più alto che passa sotto la trave è ~{fmt(P.CLEAR_UNDER_BEAM - P.PALLET_T)} mm, meno fixture e utensile; con i rialzi +75 mm (D007) sale di conseguenza. Nelle specifiche commerciali si dichiarano separatamente corsa Z (140 mm) e altezza pezzo per configurazione.</div></section>

<section class="section"><h2>Viste di controllo</h2><p style="margin:-4px 0 14px"><a class="btn primary" href="viewer-3d.html">Apri il mule in 3D</a> <a class="btn" href="viewer-3d.html?m=standard_dock.glb">DOCK in 3D</a></p><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:18px">{views}</div></section>

<section class="section split">
  <div class="panel"><span class="kicker">Datum · HOME</span><h2>Riferimenti.</h2><div class="table-wrap"><table><tr><th>Datum</th><th>x, y, z (mm)</th></tr>{dat_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Sistema macchina: z = 0 sul piano dei longheroni, asse utensile sempre su y = 0 (ponte fisso). PALLET_R1/R2 si muovono con la tavola; TOOLDOCK_MASTER con la slitta Z.</p></div>
  <div class="panel"><span class="kicker">Rigenerare</span><h2>Un comando.</h2><p><code>python tools/cad/standard_assembly.py</code> (CadQuery) riscrive STEP, <code>cad/standard/report.json</code> e questa pagina; <code>python tools/cad/render_views.py</code> rigenera le viste. Ogni quota si cambia solo in <code>standard_params.py</code>.</p></div>
</section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    (ROOT / "base" / "cad-standard.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
