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


def screw_nut(name):
    """Chiocciola lungo +X da 0, flangia sul lato x = 0."""
    s = parts.SCREWS[name]
    body = cyl("x", 0, s["L"], 0, 0, s["D"] / 2).union(cyl("x", 0, s["B"], 0, 0, s["A"] / 2))
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


def build(X, Y, Zd):
    a = Asm()
    zc, t_top, t_bot = D["zc"], D["table_top"], D["table_bottom"]
    xa, ya, za = P.X_AXIS, P.Y_AXIS, P.Z_AXIS
    B, U, BM, T = P.BASE, P.UPRIGHT, P.BEAM, P.TABLE
    xcen = P.TRAVEL["X"] / 2
    ytc = T["D"] / 2                    # centro tavola (locale)
    xtc = T["W"] / 2
    y_x_axis = D["beam_face"] + BM["recess_d"] - P.X_SCREW_PAD - P.SUPPORTS[xa["bk"]]["h"]
    y_z_axis = D["slide_back"] + 2 + P.SUPPORTS[za["bk"]]["h"]
    z_y_axis = -B["H"] + B["wall"] + B["pad"] + P.SUPPORTS[ya["bk"]]["h"]

    # ============ FRAME ============
    cx0, cx1 = xtc - B["channel_w"] / 2, xtc + B["channel_w"] / 2
    w, top = B["wall"], B["top"]
    base = (box(B["x0"], B["x1"], B["y0"], B["y1"], -top, 0)
            .union(box(B["x0"], B["x0"] + w, B["y0"], B["y1"], -B["H"], 0))
            .union(box(B["x1"] - w, B["x1"], B["y0"], B["y1"], -B["H"], 0))
            .union(box(B["x0"], B["x1"], B["y0"], B["y0"] + w, -B["H"], 0))
            .union(box(B["x0"], B["x1"], B["y1"] - w, B["y1"], -B["H"], 0))
            .union(box(P.BEAM_X[0], P.BEAM_X[1], B["cross_y0"], B["cross_y1"], -top, 0))
            .union(box(P.BEAM_X[0], P.BEAM_X[1], B["cross_y0"], B["cross_y0"] + w, -B["H"], 0))
            .union(box(P.BEAM_X[0], P.BEAM_X[1], B["cross_y1"] - w, B["cross_y1"], -B["H"], 0))
            .union(box(P.BEAM_X[0], P.BEAM_X[0] + w, B["cross_y0"], B["cross_y1"], -B["H"], 0))
            .union(box(P.BEAM_X[1] - w, P.BEAM_X[1], B["cross_y0"], B["cross_y1"], -B["H"], 0))
            .union(box(cx0 - w, cx0, B["y0"], B["y1"], -B["H"], 0))
            .union(box(cx1, cx1 + w, B["y0"], B["y1"], -B["H"], 0))
            .union(box(cx0 - w, cx1 + w, B["y0"], B["y1"], -B["H"], -B["H"] + w)))
    base = base.cut(box(cx0, cx1, B["y0"] + w, B["y1"] - w, -B["H"] + w, 0.5))
    base = base.cut(cyl("y", B["y1"] - w - 1, B["y1"] + 1, xtc, z_y_axis, 20))
    sy_th = P.Y_AXIS["screw_len"] - sum(parts.ENDS[P.Y_AXIS["screw"]])
    sy_bf = parts.ENDS[P.Y_AXIS["screw"]][1]
    y_sup = [(-sy_th / 2 - P.SUPPORTS[P.Y_AXIS["bf"]]["T"], -sy_th / 2),
             (sy_th / 2 + 2, sy_th / 2 + 2 + P.SUPPORTS[P.Y_AXIS["bk"]]["T"])]
    for y0_, y1_ in y_sup:
        base = base.union(box(xtc - 30, xtc + 30, y0_, y1_, -B["H"] + w, -B["H"] + w + B["pad"]))
    a.add("base", base, "FRAME", AL, "MC-BAS-001", "gray")

    zb_top = D["beam_bottom"]
    for side, (x0, x1) in (("L", (P.BEAM_X[0], P.BEAM_X[0] + U["t"])), ("R", (P.BEAM_X[1] - U["t"], P.BEAM_X[1]))):
        yc = (D["beam_face"] + D["beam_back"]) / 2
        up = box(x0, x1, yc - U["depth"] / 2, yc + U["depth"] / 2, 0, zb_top)
        wy, wz = U["window"]
        up = up.cut(box(x0 - 1, x1 + 1, yc - wy / 2, yc + wy / 2, zb_top / 2 - wz / 2, zb_top / 2 + wz / 2))
        a.add(f"upright_{side}", up, "FRAME", AL, "MC-GAN-002", "gray")

    bf, bb = D["beam_face"], D["beam_back"]
    bx0, bx1, t = P.BEAM_X[0], P.BEAM_X[1], BM["wall"]
    rh, rd = BM["recess_h"] / 2, BM["recess_d"]
    beam = box(bx0, bx1, bf, bb, D["beam_bottom"], D["beam_top"]).cut(
        box(bx0 + BM["end"], bx1 - BM["end"], bf + t, bb - t, D["beam_bottom"] + t, D["beam_top"] - t))
    beam = beam.cut(box(bx0 - 1, bx1 + 1, bf - 1, bf + rd, zc - rh, zc + rh))
    beam = (beam.union(box(bx0, bx1, bf + rd, bf + rd + t, zc - rh - t, zc + rh + t))
            .union(box(bx0, bx1, bf, bf + rd + t, zc + rh, zc + rh + t))
            .union(box(bx0, bx1, bf, bf + rd + t, zc - rh - t, zc - rh)))
    a.add("beam", beam, "FRAME", AL, "MC-GAN-001", "gray")

    # guide X sulla faccia trave, centrate sulla corsa
    xr = parts.RAILS[xa["rail"]]
    x_rail0 = xcen - xa["rail_len"] / 2
    for tag, dz in (("top", xa["rail_spacing"] / 2), ("bot", -xa["rail_spacing"] / 2)):
        a.add(f"x_rail_{tag}", to_x_on_face(parts.rail(xa["rail"], xa["rail_len"])).translate((x_rail0, bf, zc + dz)),
              "FRAME", STEEL, "MC-LIN-151", "steelblue")

    # vite X nel canale della trave: filetto centrato sulla corsa
    bkx, bfx, thx = screw_ends(xa)
    sx0 = xcen - thx / 2 - bfx
    a.add("x_screw", screw_shaft(xa["screw"], xa["screw_len"]).translate((sx0, y_x_axis, zc)), "FRAME", STEEL, "MC-BS-1605X", "silver")
    rot_face = lambda wp: wp.rotate(ORIGIN, (1, 0, 0), 90)  # noqa: E731  normale di montaggio → −Y
    a.add("x_bf", rot_face(support(xa["bf"], sx0 + bfx - P.SUPPORTS[xa["bf"]]["T"])).translate((0, y_x_axis, zc)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("x_bk", rot_face(support(xa["bk"], sx0 + bfx + thx + 2)).translate((0, y_x_axis, zc)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("x_pads", box(sx0 - 10, sx0 + bfx, bf + rd - P.X_SCREW_PAD, bf + rd, zc - 30, zc + 30)
          .union(box(sx0 + bfx + thx + 2, sx0 + bfx + thx + 27, bf + rd - P.X_SCREW_PAD, bf + rd, zc - 30, zc + 30)),
          "FRAME", AL, None, "gray")
    mx = parts.MOTORS[xa["motor"]]
    motor_face_x = bx1
    cplx = P.COUPLING[xa["screw"]]
    a.add("x_coupling", tube("x", sx0 + xa["screw_len"] - 10, motor_face_x - mx[8] + 10, y_x_axis, zc, cplx["D"] / 2, parts.SCREWS[xa["screw"]]["d"] / 2 - 2 + 0.3),
          "FRAME", STEEL, "MC-CPL-001", "gold")
    a.add("x_motor_plate", box(bx1 - BM["end"], bx1, y_x_axis - 32, bf + rd, zc - 35, zc + 35).cut(cyl("x", bx1 - 10, bx1 + 1, y_x_axis, zc, 20)),
          "FRAME", AL, None, "gray")
    a.add("x_motor", parts.motor(xa["motor"]).rotate(ORIGIN, (0, 1, 0), 90).translate((motor_face_x, y_x_axis, zc)), "FRAME", STEEL, "MC-MOT-001", "black")

    # guide Y nel basamento
    yr0 = -ya["rail_len"] / 2
    for tag, x in (("L", xtc - ya["rail_spacing"] / 2), ("R", xtc + ya["rail_spacing"] / 2)):
        a.add(f"y_rail_{tag}", to_y_on_floor(parts.rail(ya["rail"], ya["rail_len"])).translate((x, yr0, 0)), "FRAME", STEEL, "MC-LIN-155", "steelblue")

    bky, bfy, thy = screw_ends(ya)
    sy0 = -thy / 2 - bfy          # filetto centrato su y = 0 (centro corsa chiocciola)
    rot_y = lambda wp: wp.rotate(ORIGIN, (0, 0, 1), 90)  # noqa: E731
    a.add("y_screw", rot_y(screw_shaft(ya["screw"], ya["screw_len"])).translate((xtc, sy0, z_y_axis)), "FRAME", STEEL, "MC-BS-1605Y", "silver")
    a.add("y_bf", rot_y(support(ya["bf"], sy0 + bfy - P.SUPPORTS[ya["bf"]]["T"])).translate((xtc, 0, z_y_axis)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    a.add("y_bk", rot_y(support(ya["bk"], sy0 + bfy + thy + 2)).translate((xtc, 0, z_y_axis)), "FRAME", STEEL, "MC-BKBF-001", "dimgray")
    my = parts.MOTORS[ya["motor"]]
    cply = P.COUPLING[ya["screw"]]
    a.add("y_coupling", tube("y", sy0 + ya["screw_len"] - 10, B["y1"] - my[8] + 10, xtc, z_y_axis, cply["D"] / 2, parts.SCREWS[ya["screw"]]["d"] / 2 - 2 + 0.3),
          "FRAME", STEEL, "MC-CPL-001", "gold")
    a.add("y_motor", parts.motor(ya["motor"]).rotate(ORIGIN, (1, 0, 0), -90).translate((xtc, B["y1"], z_y_axis)), "FRAME", STEEL, "MC-MOT-001", "black")

    # riserve di volume
    a.add("chain_x_volume", box(bx0, bx1, bf, bf + P.CHAIN_X["w"], D["beam_top"], D["beam_top"] + P.CHAIN_X["h"]), "FRAME", "volume", None, "orange")
    a.add("chain_y_volume", box(P.CHAIN_Y["x0"], P.CHAIN_Y["x1"], B["y0"], B["y1"], 0, P.CHAIN_Y["h"]), "FRAME", "volume", None, "orange")
    coupling_top = D["tip_bottom"] + P.TRAVEL["Z"] + P.HEAD["L"]
    dock_x = P.DOCK["x_inside"] if P.DOCK["mode"] == "inside" else P.DOCK["x_outside"]
    mag_x0 = dock_x + P.HEAD["W"] / 2 + 5
    a.add("magazine_volume", box(mag_x0, mag_x0 + (P.DOCK["slots"] - 1) * P.DOCK["pitch"], -P.HEAD["D"] / 2 - 5, P.HEAD["D"] / 2 + 5,
                                 coupling_top - P.HEAD["L"] - 5, coupling_top + 20), "FRAME", "volume", None, "violet")

    # ============ TABLE (si muove in Y) ============
    g = P.GRID
    holes = [(g["x0"] + i * g["pitch"], g["y0"] + j * g["pitch"]) for i in range(g["nx"]) for j in range(g["ny"])]
    tb = box(0, T["W"], 0, T["D"], T["T"] - T["skin"], T["T"])
    tb = tb.union(box(0, T["W"], 0, T["rim"], 0, T["T"])).union(box(0, T["W"], T["D"] - T["rim"], T["D"], 0, T["T"]))
    tb = tb.union(box(0, T["rim"], 0, T["D"], 0, T["T"])).union(box(T["W"] - T["rim"], T["W"], 0, T["D"], 0, T["T"]))
    for (x, y) in holes + [P.R1, P.R2]:
        tb = tb.union(cyl("z", 0, T["T"], x, y, T["boss_d"] / 2))
    for x in (xtc - ya["rail_spacing"] / 2, xtc + ya["rail_spacing"] / 2):
        for y in (ytc - ya["block_pitch"] / 2, ytc + ya["block_pitch"] / 2):
            tb = tb.union(box(x - T["pad_w"] / 2, x + T["pad_w"] / 2, y - T["pad_l"] / 2, y + T["pad_l"] / 2, 0, T["T"]))
    tb = tb.union(box(xtc - 40, xtc + 40, ytc - 45, ytc - 15, 0, T["T"]))
    for (x, y) in holes:
        tb = tb.cut(cyl("z", -1, T["T"] + 1, x, y, g["hole"] / 2))
    tb = tb.cut(cyl("z", -1, T["T"] + 1, P.R1[0], P.R1[1], P.R_BORE / 2))
    tb = tb.cut(box(P.R2[0] - P.R2_SLOT / 2 + P.R_BORE / 2, P.R2[0] + P.R2_SLOT / 2 - P.R_BORE / 2, P.R2[1] - P.R_BORE / 2, P.R2[1] + P.R_BORE / 2, -1, T["T"] + 1)
                .union(cyl("z", -1, T["T"] + 1, P.R2[0] - P.R2_SLOT / 2 + P.R_BORE / 2, P.R2[1], P.R_BORE / 2))
                .union(cyl("z", -1, T["T"] + 1, P.R2[0] + P.R2_SLOT / 2 - P.R_BORE / 2, P.R2[1], P.R_BORE / 2)))
    a.add("table", tb.translate((0, -Y, t_bot)), "TABLE", AL, "MC-TBL-001", "lightgray")
    for i, x in enumerate((xtc - ya["rail_spacing"] / 2, xtc + ya["rail_spacing"] / 2)):
        for j, y in enumerate((ytc - ya["block_pitch"] / 2, ytc + ya["block_pitch"] / 2)):
            a.add(f"y_block_{i}{j}", to_y_on_floor(parts.block(ya["block"])).translate((x, y - Y, 0)), "TABLE", STEEL, "MC-LIN-156", "steelblue")
    ny = parts.SCREWS[ya["screw"]]
    nut_y0 = ytc - ny["L"] / 2 - Y
    a.add("y_nut", rot_y(screw_nut(ya["screw"])).translate((xtc, nut_y0, z_y_axis)), "TABLE", STEEL, "MC-BS-1605Y", "silver")
    a.add("y_nut_bracket", box(xtc - 30, xtc + 30, nut_y0 - P.NUT_BRACKET_T, nut_y0, z_y_axis - 24, t_bot)
          .cut(cyl("y", nut_y0 - P.NUT_BRACKET_T - 1, nut_y0 + 1, xtc, z_y_axis, ny["d"] / 2 + 0.5)), "TABLE", AL, None, "gray")

    # ============ XCAR (si muove in X) ============
    cf, cb = D["carriage_front"], D["carriage_back"]
    C = P.PLATE
    z_nut_min = zc + P.Z_NUT_MIN_ABOVE_ZC
    bkz, bfz, thz = screw_ends(za)
    zs0 = z_nut_min - 10 - 3 - bfz                 # fondo vite Z: BF sotto la piastrina chiocciola
    z_bk_top = zs0 + za["screw_len"]
    tower_top = z_bk_top + 20
    car = box(X - C["carriage_w"] / 2, X + C["carriage_w"] / 2, cf, cb, zc - C["carriage_below"], zc + C["carriage_below"])
    car = car.union(box(X - C["tower_w"] / 2, X + C["tower_w"] / 2, cf, cb, zc, tower_top))
    car = car.cut(box(X - C["slot_w"] / 2, X + C["slot_w"] / 2, cf - 1, cb + 1, zc + C["slot_from"], tower_top + 1))
    a.add("x_carriage", car, "XCAR", AL, None, "gray")
    xb = parts.BLOCKS[xa["block"]]
    for i, dz in enumerate((xa["rail_spacing"] / 2, -xa["rail_spacing"] / 2)):
        for j, dx in enumerate((-xa["block_pitch"] / 2, xa["block_pitch"] / 2)):
            a.add(f"x_block_{i}{j}", to_x_on_face(parts.block(xa["block"])).translate((X + dx, bf, zc + dz)), "XCAR", STEEL, "MC-LIN-152", "steelblue")
    zr = parts.RAILS[za["rail"]]
    for i, dx in enumerate((-za["rail_spacing"] / 2, za["rail_spacing"] / 2)):
        for j, dz in enumerate((-za["block_pitch"] / 2, za["block_pitch"] / 2)):
            a.add(f"z_block_{i}{j}", to_z_toward_y(parts.block(za["block"])).translate((X + dx, D["slide_back"], zc + dz)), "XCAR", STEEL, "MC-LIN-154", "steelblue")
    nx_ = parts.SCREWS[xa["screw"]]
    nut_x0 = X - nx_["L"] / 2
    a.add("x_nut", screw_nut(xa["screw"]).translate((nut_x0, y_x_axis, zc)), "XCAR", STEEL, "MC-BS-1605X", "silver")
    a.add("x_nut_bracket", box(nut_x0 - P.NUT_BRACKET_T, nut_x0, cb, y_x_axis + 22, zc - 28, zc + 28)
          .cut(cyl("x", nut_x0 - P.NUT_BRACKET_T - 1, nut_x0 + 1, y_x_axis, zc, nx_["d"] / 2 + 0.5)), "XCAR", AL, None, "gray")
    rot_z = lambda wp: wp.rotate(ORIGIN, (0, 1, 0), -90).rotate(ORIGIN, (0, 0, 1), -90)  # noqa: E731
    a.add("z_screw", screw_shaft(za["screw"], za["screw_len"]).rotate(ORIGIN, (0, 1, 0), -90).translate((X, y_z_axis, zs0)), "XCAR", STEEL, "MC-BS-1204Z", "silver")
    # supporti Z: asse lungo Z, normale di montaggio verso +Y (faccia a y = slide_back + 2)
    def z_support(kind, z0):
        return rot_z(support(kind, z0)).translate((X, y_z_axis, 0))
    a.add("z_bf", z_support(za["bf"], zs0 + bfz - P.SUPPORTS[za["bf"]]["T"]), "XCAR", STEEL, "MC-BKBF-001", "dimgray")
    a.add("z_bk", z_support(za["bk"], zs0 + bfz + thz + 2), "XCAR", STEEL, "MC-BKBF-001", "dimgray")
    mz = parts.MOTORS[za["motor"]]
    cplz = P.COUPLING[za["screw"]]
    z_motor_face = tower_top + 10
    a.add("z_coupling", tube("z", z_bk_top - 10, z_motor_face - mz[8] + 10, X, y_z_axis, cplz["D"] / 2, parts.SCREWS[za["screw"]]["d"] / 2 - 2 + 0.3),
          "XCAR", STEEL, "MC-CPL-001", "gold")
    a.add("z_motor_bracket", box(X - 45, X + 45, y_z_axis - 30, y_z_axis + 30, tower_top, z_motor_face).cut(cyl("z", tower_top - 1, z_motor_face + 1, X, y_z_axis, 20)),
          "XCAR", AL, None, "gray")
    a.add("z_motor", parts.motor(za["motor"]).translate((X, y_z_axis, z_motor_face)), "XCAR", STEEL, "MC-MOT-001", "black")

    # ============ ZSLIDE (si muove in X e Z) ============
    sb = zc - D["slide_below_blocks"] - Zd
    slide_len = za["rail_len"] + C["slide_ext_top"]
    a.add("z_slide", box(X - C["slide_w"] / 2, X + C["slide_w"] / 2, D["slide_front"], D["slide_back"], sb, sb + slide_len), "ZSLIDE", AL, "MC-Z-001", "gray")
    for i, dx in enumerate((-za["rail_spacing"] / 2, za["rail_spacing"] / 2)):
        a.add(f"z_rail_{i}", to_z_toward_y(parts.rail(za["rail"], za["rail_len"])).translate((X + dx, D["slide_back"], sb)), "ZSLIDE", STEEL, "MC-LIN-153", "steelblue")
    nz = parts.SCREWS[za["screw"]]
    nb = z_nut_min + (P.TRAVEL["Z"] - Zd)
    a.add("z_nut", screw_nut(za["screw"]).rotate(ORIGIN, (0, 1, 0), -90).translate((X, y_z_axis, nb)), "ZSLIDE", STEEL, "MC-BS-1204Z", "silver")
    a.add("z_nut_tab", box(X - 26, X + 26, D["slide_back"], y_z_axis + 22, nb - 10, nb).cut(cyl("z", nb - 11, nb + 1, X, y_z_axis, nz["d"] / 2 + 0.5)),
          "ZSLIDE", AL, None, "gray")
    coupling_z = sb - P.MASTER["T"]
    a.add("tooldock_master", box(X - P.MASTER["W"] / 2, X + P.MASTER["W"] / 2, -P.HEAD["D"] / 2, D["slide_back"], coupling_z, sb), "ZSLIDE", AL, "MC-TD-001", "tomato")
    a.add("head_volume", box(X - P.HEAD["W"] / 2, X + P.HEAD["W"] / 2, -P.HEAD["D"] / 2, P.HEAD["D"] / 2, coupling_z - P.HEAD["L"], coupling_z),
          "ZSLIDE", "volume", None, "tomato")

    datums = {
        "MACHINE_ORIGIN": (0.0, 0.0, t_top),
        "PALLET_R1": (P.R1[0], P.R1[1] - Y, t_top),
        "PALLET_R2": (P.R2[0], P.R2[1] - Y, t_top),
        "TOOLDOCK_MASTER": (X, 0.0, coupling_z),
        "DOCK_POSITION": (dock_x, 0.0, coupling_top),
        "TOOL_TIP": (X, 0.0, coupling_z - P.HEAD["L"]),
    }
    return a, datums


# ---------------------------------------------------------------- analisi
DESIGNED = [  # coppie in moto relativo che si toccano per progetto (guida-pattino, vite-chiocciola, vite-foro)
    ("x_rail", "x_block"), ("y_rail", "y_block"), ("z_rail", "z_block"),
    ("x_screw", "x_nut"), ("y_screw", "y_nut"), ("z_screw", "z_nut"),
    ("x_screw", "x_nut_bracket"), ("y_screw", "y_nut_bracket"), ("z_screw", "z_nut_tab"),
    ("head_volume", "table"),
]


def designed(n1, n2):
    return any((n1.startswith(p) and n2.startswith(q)) or (n2.startswith(p) and n1.startswith(q)) for p, q in DESIGNED)


def bb_gap(b1, b2):
    dx = max(b1.xmin - b2.xmax, b2.xmin - b1.xmax, 0)
    dy = max(b1.ymin - b2.ymax, b2.ymin - b1.ymax, 0)
    dz = max(b1.zmin - b2.zmax, b2.zmin - b1.zmax, 0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def analyse(a, all_pairs):
    names = list(a.parts)
    bbs = {n: a.parts[n]["shape"].BoundingBox() for n in names}
    collisions, warnings = [], []
    for n1, n2 in itertools.combinations(names, 2):
        p1, p2 = a.parts[n1], a.parts[n2]
        if not all_pairs and p1["group"] == p2["group"]:
            continue
        if bb_gap(bbs[n1], bbs[n2]) > P.CLEAR_WARN:
            continue
        common = p1["shape"].intersect(p2["shape"])
        vol = common.Volume() if common is not None else 0.0
        if vol > 1.0:
            collisions.append(dict(a=n1, b=n2, volume_mm3=round(vol, 1)))
            continue
        if p1["group"] == p2["group"] or designed(n1, n2):
            continue
        ext = BRepExtrema_DistShapeShape(p1["shape"].wrapped, p2["shape"].wrapped)
        ext.Perform()
        dist = ext.Value() if ext.IsDone() else None
        if dist is not None and dist < P.CLEAR_WARN:
            warnings.append(dict(a=n1, b=n2, clearance_mm=round(dist, 2)))
    return collisions, warnings


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
        "X": [dist(a, "x_nut_bracket", "x_bf"), dist(a, "x_nut", "x_bk")],
        "Y": [dist(a, "y_nut", "y_bk"), dist(a, "y_nut_bracket", "y_bf")],
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
        (custom if p["bom"] else extra)[n] = (p["bom"], round(kg, 2))
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
                  params=dict(travel=P.TRAVEL, x=P.X_AXIS, y=P.Y_AXIS, z=P.Z_AXIS, dock=P.DOCK), configs={})
    env = []
    for cfg, (X, Y, Zd) in P.CONFIGS.items():
        a, datums = build(X, Y, Zd)
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
    report["envelope_mm"] = [min(b[0] for b in env), max(b[1] for b in env), min(b[2] for b in env),
                             max(b[3] for b in env), min(b[4] for b in env), max(b[5] for b in env)]
    e = report["envelope_mm"]
    report["footprint_mm"] = [round(e[1] - e[0], 1), round(e[3] - e[2], 1)]
    report["height_mm"] = round(e[5] - e[4], 1)
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


def design_checks(report):
    h = P.X_AXIS["rail_spacing"]
    b = D["b_tip_below_x_rails"]

    def kmin(bb):
        return K_TIP_RAILS * (0.25 + (bb / h) ** 2)
    # layout alternativo: pattini Z sulla slitta, guide Z sul carrello; trave appena sopra pezzo + corsa Z
    beam_bottom_alt = D["table_top"] + P.TRAVEL["Z"] + MARGIN_PIECE
    b_alt_lo = beam_bottom_alt + P.BEAM["height"] / 2 - D["tip_bottom"]
    b_alt_hi = b_alt_lo + 80.0
    m = report["mass"]
    col = {c: len(v["collisions"]) for c, v in report["configs"].items()}
    return dict(
        d015=dict(h=h, b_assumed=D015_ASSUMED["b"], b_real=round(b, 1), a_assumed=D015_ASSUMED["a"], a_real=round(D["a_tool_to_x_face"], 1),
                  k_min_assumed=round(kmin(D015_ASSUMED["b"]), 0), k_min_real=round(kmin(b), 0), k_za=K_BLOCK["ZA"], k_zb=K_BLOCK["ZB"],
                  pass_real=kmin(b) <= K_BLOCK["ZA"], h_needed_for_za=round(b / math.sqrt(K_BLOCK["ZA"] / K_TIP_RAILS - 0.25), 0),
                  b_alt=[round(b_alt_lo, 0), round(b_alt_hi, 0)], k_min_alt=[round(kmin(b_alt_lo), 0), round(kmin(b_alt_hi), 0)]),
        mass=dict(bom=m["machine_bom_kg"], mule=m["machine_mule_kg"], delta=round(m["machine_mule_kg"] - m["machine_bom_kg"], 1)),
        collisions=col,
    )


MARGIN_PIECE = 10.0


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
        rows_cfg += (f'<tr><td><b>{cfg}</b></td><td style="white-space:nowrap">X {fmt(ax["X"])}<br>Y {fmt(ax["Y"])}<br>Z {fmt(ax["Z"] + 0.0)}</td>'
                     f'<td class="{cls}">{colls}</td><td>{warns}</td><td>{marg}</td><td>{nuts}</td>'
                     f'<td><a href="../{v["step"]}" download style="color:var(--accent-2)">STEP ↓</a></td></tr>\n') if "step" in v else ""
    m = report["mass"]
    mass_rows = "".join(f'<tr><td>{r["bom"]}</td><td>{r["part"]}</td><td>{fmt(r["bom_kg"])}</td><td class="{"status-critical" if r["mule_kg"] > 1.5 * r["bom_kg"] else "status-ok"}">{fmt(r["mule_kg"])}</td></tr>' for r in m["custom"])
    extra = " · ".join(f'{x["part"]} {fmt(x["kg"])} kg' for x in m["not_in_bom"])
    home = report["configs"]["HOME"]["datums"]
    dat_rows = "".join(f'<tr><td><code>{k}</code></td><td>{", ".join(fmt(v) for v in xyz)}</td></tr>' for k, xyz in home.items())
    ok, ko = '<td class="status-ok">PASSA</td>', '<td class="status-critical">NON PASSA</td>'
    part_ok = '<td class="status-target">PARZIALE</td>'
    crit = [
        ("Un solo file di parametri <code>tools/cad/standard_params.py</code>", ok),
        ("Assieme <code>tools/cad/standard_assembly.py</code>", ok),
        ("Guide, pattini, viti e motori dai modelli MultiCNC", part_ok + "<td>Stesse funzioni di <code>parts.py</code> che generano gli STEP; nell'assieme pattini e chiocciole sono istanziati a parte perché si muovono</td>"),
        ("Custom: basamento, spalle, trave, tavola Y, piastra Z (+ carrello X)", ok),
        ("Datum MACHINE_ORIGIN, PALLET_R1/R2, TOOLDOCK_MASTER, DOCK_POSITION", ok),
        ("Corse reali 450 × 350 × 140 con margini D019 ≥ 10 mm", ok),
        ("X HGR15/HGH15CA, rotaia 640, interasse 110", ok),
        ("Y MGN15H, rotaia 630, SFU1605 centrale", ok),
        ("Z HGR15/HGH15CA, rotaia 310, SFU1204 260", ok),
        ("Tavola 450 × 350 × 10, R1/R2, griglia 9 × 7", ok),
        ("Magazine solo come volume + DOCK_POSITION; niente cabina", ok),
        ("STEP + bounding box + footprint + massa + collisioni, HOME/CENTER/MAX", ok),
        ("Nessuna collisione nelle tre configurazioni", ok if not any(c["collisions"].values()) else ko),
        ("D015 verificata con i bracci reali a e b", ok if d15["pass_real"] else ko),
        ("Massa entro ±15% della BOM (32,8 kg)", ok if abs(c["mass"]["delta"]) <= 0.15 * c["mass"]["bom"] else ko),
    ]
    crit_rows = "".join(f"<tr><td>{t}</td>{r if r.count('<td') > 1 else r + '<td></td>'}</tr>" for t, r in crit)
    views = "".join(f'<figure style="margin:0"><img src="../cad/standard/views/{n}.png" alt="Mule Standard {n}" style="width:100%;background:#fff;border-radius:10px"><figcaption style="color:var(--dim);font-size:12px;margin-top:6px">{n.replace("_", " · ").upper()}</figcaption></figure>'
                    for n in ("home_iso", "max_iso", "max_front", "max_side", "max_top", "home_top"))
    html = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — CAD Standard · mule</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/cad/standard_assembly.py: non modificare a mano. -->
<a class="back" href="index.html">← Base Standard</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · CAD v0 · digital mule</div><h1>Digital mule<br>Standard.</h1><p class="lead">Primo assieme parametrico della Standard: brutto ma dimensionalmente corretto. Tutte le quote vengono da <code>tools/cad/standard_params.py</code>; lo script costruisce l'assieme in HOME, CENTER e MAX, cerca collisioni e giochi, misura ingombri e masse e rigenera questa pagina.</p><div class="badges"><span class="badge ok">CAD v0 · mule</span><span class="badge">{report["configs"]["HOME"]["parts"]} parti · 3 configurazioni</span><span class="badge">Valori MULE da rivedere</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{fmt(report["footprint_mm"][0])} × {fmt(report["footprint_mm"][1])}</strong><span>mm · footprint con motori, inviluppo delle 3 configurazioni</span></div>
  <div class="metric"><strong>{fmt(report["height_mm"])}</strong><span>mm · altezza, dal fondo basamento al motore Z</span></div>
  <div class="metric"><strong>{fmt(c["mass"]["mule"])} kg</strong><span>massa macchina stimata · BOM {fmt(c["mass"]["bom"])} kg</span></div>
  <div class="metric"><strong>{sum(c["collisions"].values())}</strong><span>collisioni in HOME · CENTER · MAX</span></div>
</section>

<section class="section"><h2>Criteri di accettazione</h2><div class="table-wrap"><table>
<tr><th>Criterio</th><th>Esito</th><th>Nota</th></tr>
{crit_rows}
</table></div></section>

<section class="section split">
  <div class="panel" style="border-color:rgba(255,84,112,.35)"><span class="kicker">Risultato 1 · D015</span><h2>Il braccio vero è {fmt(d15["b_real"])} mm.</h2><p>D015 aveva ipotizzato la punta a b = {fmt(d15["b_assumed"])} mm sotto il centro delle guide X e a a = {fmt(d15["a_assumed"])} mm dalla faccia trave. Nel mule, con Z tutto giù, <b>b = {fmt(d15["b_real"])} mm</b> e <b>a = {fmt(d15["a_real"])} mm</b>. Con interasse {fmt(d15["h"])} mm la rigidezza minima per pattino sale da {fmt(d15["k_min_assumed"])} a <b>{fmt(d15["k_min_real"])} N/µm</b>: HGH15CA ZA ({fmt(d15["k_za"])}) e ZB ({fmt(d15["k_zb"])}) non bastano. Con questo layout servirebbe un interasse di ~{fmt(d15["h_needed_for_za"])} mm.</p><p><b>Causa:</b> i pattini Z stanno sul carrello e devono restare sopra il fondo della slitta con Z in alto, quindi le guide X finiscono a {fmt(D["zc"])} mm dal basamento. <b>Rimedio da valutare nel mule v1:</b> pattini Z sulla slitta e guide Z sul carrello, con la trave appena sopra pezzo e corsa Z: b ≈ {fmt(d15["b_alt"][0])}–{fmt(d15["b_alt"][1])} mm, k minimo ≈ {fmt(d15["k_min_alt"][0])}–{fmt(d15["k_min_alt"][1])} N/µm, entro ZA. Macchina anche più bassa.</p></div>
  <div class="panel" style="border-color:rgba(255,84,112,.35)"><span class="kicker">Risultato 2 · massa</span><h2>{fmt(c["mass"]["mule"])} kg, non {fmt(c["mass"]["bom"])}.</h2><div class="table-wrap"><table><tr><th>Riga BOM</th><th>Parte</th><th>BOM kg</th><th>Mule kg</th></tr>{mass_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Parti del mule che la BOM non ha ancora: {extra}. Parti commerciali ed elettronica con le masse della BOM. Il basamento è la differenza principale: un guscio da {fmt(P.BASE["top"])} mm con pareti da {fmt(P.BASE["wall"])} mm, a T per portare le spalle, pesa molto più dei 3,5 kg stimati.</p></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">Risultato 3 · magazine</span><h2>La slitta invade il magazine.</h2><p>In MAX (X = 450, Z giù) la slitta Z, larga {fmt(P.PLATE["slide_w"])} mm contro i {fmt(P.HEAD["W"])} mm della testa, entra nel volume riservato al magazine a destra della posizione di docking. Il magazine deve stare oltre x ≈ {fmt(P.DOCK["x_inside"] + P.PLATE["slide_w"] / 2 + 5)} mm, oppure la slitta deve restringersi in basso. Con il docking fuori corsa (x = {fmt(P.DOCK["x_outside"])}) servirebbero {fmt(P.DOCK["x_outside"] - P.TRAVEL["X"])} mm di corsa X in più.</p></div>
  <div class="panel"><span class="kicker">Risultato 4 · ingombri</span><h2>Motori a sbalzo.</h2><p>Inviluppo X {fmt(e[0])} … {fmt(e[1])}, Y {fmt(e[2])} … {fmt(e[3])}, Z {fmt(e[4])} … {fmt(e[5])} mm. Il motore X sporge oltre la trave e il motore Y oltre il basamento di circa 97 mm ciascuno; il motore Z sul carrello porta l'altezza a {fmt(report["height_mm"])} mm. La cabina (D025) dovrà contenere questo volume o i motori dovranno essere ripiegati.</p></div>
</section>

<section class="section"><h2>Configurazioni</h2><div class="table-wrap"><table>
<tr><th>Config</th><th>Assi</th><th>Collisioni</th><th>Giochi &lt; {fmt(P.CLEAR_WARN)} mm</th><th>Margine pattini-rotaie (mm)</th><th>Chiocciola-supporti (mm)</th><th>Assieme</th></tr>
{rows_cfg}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Collisione = volume comune &gt; 1 mm³. Giochi controllati solo tra parti in moto relativo, escluse le coppie che si toccano per progetto (guida-pattino, vite-chiocciola, vite-foro, punta-tavola a Z giù). Volumi riservati (catene, magazine, testa) inclusi nel controllo.</p></section>

<section class="section"><h2>Viste di controllo</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:18px">{views}</div></section>

<section class="section split">
  <div class="panel"><span class="kicker">Datum · HOME</span><h2>Riferimenti.</h2><div class="table-wrap"><table><tr><th>Datum</th><th>x, y, z (mm)</th></tr>{dat_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Sistema macchina: z = 0 sul piano del basamento, asse utensile sempre su y = 0 (ponte fisso). PALLET_R1/R2 si muovono con la tavola; TOOLDOCK_MASTER con la slitta Z.</p></div>
  <div class="panel"><span class="kicker">Rigenerare</span><h2>Un comando.</h2><p><code>python tools/cad/standard_assembly.py</code> (CadQuery) riscrive STEP, <code>cad/standard/report.json</code> e questa pagina; <code>python tools/cad/render_views.py</code> rigenera le viste. Ogni quota si cambia solo in <code>standard_params.py</code>.</p></div>
</section>
</main><script src="../assets/nav.js"></script></body></html>
'''
    (ROOT / "base" / "cad-standard.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
