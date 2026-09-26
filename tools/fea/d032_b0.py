#!/usr/bin/env python3
"""D032 · B0 architecture screen: skeleton brutali a ciclo chiuso punta ↔ pezzo, stessa FEA e stesso criterio di massa.

Uso (dalla radice, con CadQuery, gmsh e ccx): python tools/fea/d032_b0.py --arch A|B|C|R [--check]
                                              python tools/fea/d032_b0.py --page
Scrive fea/d032/B0-<arch>.json e rigenera base/fea-d032-b0.html. File di lavoro in build/fea/ (non versionati).

Non sono CAD: sono cassoni chiusi in alluminio (pareti uniformi, fusi per gruppo = incollati) disposti secondo tre
cinematiche, con la stessa testa (C3c: coupling Ø110, braccio 203 mm, molle ToolDock e cuscinetti D028), lo stesso
modulo Z (ram scatolato, pattini HGH15CA a interasse 114 × 140) e pattini HGH15CA ZA su tutti gli assi (molle D028).
- B0-A: cinematica attuale (tavola Y, gantry fisso X/Z): base a cassoni chiusi, tavola Y scatolata, trave 200 × 100,
  guide X a 150, guide Y a 380, carrello scatolato sottile (asse → guide X 145 mm).
- B0-B: tavola fissa (è il cielo della base scatolata) e gantry mobile in Y su due guide laterali, due viti Y.
- B0-C: tavola XY impilata (sella Y + tavola X) e testa che fa solo Z su un ponte fisso lungo Y con due colonne.
- B0-R: riferimento di calibrazione, il mule v3 ridotto a skeleton (telaio a scala, piastra 8 mm, MGN15H in Y, trave
  80 × 140, guide X a 110, slitta Z a passo 80) con lo stesso modulo testa: dice quanto lo skeleton è ottimista
  rispetto a gantry FEA + resto D028 (C3c: macchina ~1,15 / 0,85 / 1,06 N/µm).
Carico: coppia ±F tra il riferimento sulla punta (dado ER11, 70 mm sopra il piano, CENTER) e un pezzo rigido Ø60 sulla
tavola con il riferimento alla stessa quota: rigidezza relativa utensile ↔ pezzo della sola macchina. Vincolo
isostatico 3-2-1 su tre piedi sotto la base: con una coppia di forze autoequilibrata le reazioni sono nulle e il
risultato non dipende dal banco. Soluzione valida solo con bilancio energetico entro il 2% (come D032).
Massa CENTER stimata = cassoni + receiver e mount della testa (FEA) + quota commerciale e staffe del mule C3c
(20,0 kg) + gli azionamenti in più dell'architettura (B: seconda vite Y con motore, +2,3 kg).
"""
import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import d031 as F  # noqa: E402
import ccx  # noqa: E402
from d031 import P, cq  # noqa: E402
import standard_concepts as SC  # noqa: E402

OUT = ROOT / "fea" / "d032"
WORK = F.WORK
PAGE = ROOT / "base" / "fea-d032-b0.html"
FL = 100.0                       # N, coppia di forze (modello lineare: vale a qualsiasi livello)
TIP_Z = 70.0                     # punta sopra il piano tavola in CENTER (mule v3: 96 − 26)
ALLOW = 20.0                     # kg: commerciali + staffe del mule C3c (45,7 − 25,7 di parti strutturali custom)
MASS_LIMIT = 44.0
GATE = dict(X=3.0, Y=3.0, Z=4.0)
C3C_MACHINE = dict(X=1.15, Y=0.85, Z=1.06)
BLK = "HGH15CA"
ARCHS = ("A", "B", "C", "R")


RIB_PITCH, RIB_MIN = 100.0, 180.0     # diaframmi interni: passo ≤ 100 mm lungo ogni lato ≥ 180 mm, spessore = parete
MASS_TARGET = 44.0                    # kg in CENTER: le pareti di ogni architettura (ram escluso) si scalano fino a qui


def box(name, x0, x1, y0, y1, z0, z1, t=None, tb=None, tt=None, ribs=True, scale=True):
    """Cassone chiuso (pareti t, fondo tb, cielo tt) con diaframmi interni, o pieno (t None)."""
    return dict(name=name, bb=(x0, x1, y0, y1, z0, z1), t=t, tb=tb if tb is not None else t, tt=tt if tt is not None else t,
                ribs=ribs, scale=scale)


def solid(b):
    x0, x1, y0, y1, z0, z1 = b["bb"]
    o = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
    if b["t"] is None:
        return o
    t = b["t"]
    lo = (x0 + t, y0 + t, z0 + b["tb"])
    hi = (x1 - t, y1 - t, z1 - b["tt"])
    s = o.cut(cq.Solid.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], cq.Vector(*lo)))
    if b["ribs"]:
        L = (x1 - x0, y1 - y0, z1 - z0)
        for a in range(3):
            n = int(round(L[a] / RIB_PITCH)) - 1 if L[a] >= RIB_MIN else 0
            for k in range(1, n + 1):
                c = (b["bb"][2 * a] + L[a] * k / (n + 1))
                p0, p1 = list(lo), list(hi)
                p0[a], p1[a] = c - t / 2, c + t / 2
                s = s.fuse(cq.Solid.makeBox(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2], cq.Vector(*p0)))
    return s


def fuse(boxes):
    s = solid(boxes[0])
    for b in boxes[1:]:
        s = s.fuse(solid(b))
    return s.clean()


def scaled(spec, f):
    """Stessa architettura con pareti, fondi, cieli e diaframmi ×f (ram e parti piene invariati)."""
    out = dict(spec, groups={})
    for body, bs in spec["groups"].items():
        out["groups"][body] = [dict(b, t=b["t"] * f, tb=b["tb"] * f, tt=b["tt"] * f) if (b["t"] is not None and b["scale"]) else b for b in bs]
    out["wall_scale"] = f
    return out


# ---------------------------------------------------------------------------------------------- architetture
def ram(back, ZC, lat=57.0, pitch=140.0, support_face=93.0):
    """Modulo Z comune: ram scatolato con il coupling sul fondo (ZC), pattini sulla faccia posteriore."""
    if back == "y":
        r = box("ram", -75, 75, -70, 65, ZC, ZC + 220, 5, 12, scale=False)
    else:
        r = box("ram", -70, 65, -75, 75, ZC, ZC + 220, 5, 12, scale=False)
    g = []
    for i, zz in enumerate((ZC + 40, ZC + 40 + pitch)):
        for j, s in enumerate((-lat, lat)):
            c = (s, (65 + support_face) / 2, zz) if back == "y" else ((65 + support_face) / 2, s, zz)
            g.append(dict(name=f"zblk_{i}{j}", block="ram", rail="zsup", normal=1 if back == "y" else 0, free=2,
                          cb=65.0, cr=support_face, c=c))
    n_ax = 1 if back == "y" else 0
    l_ax = 1 - n_ax
    nut = dict(body="ram", plane=(2, ZC + 220), rect={l_ax: (-20, 20), n_ax: (20, 55)})
    bk = dict(body="zsup", plane=(n_ax, support_face), rect={l_ax: (-25, 25), 2: (ZC + 300, ZC + 330)})
    import compliance_d028 as C
    return r, g, [dict(name="zscr", a=nut, b=bk, axis=2, k=C.screw_axial("SFU1204", "BK10", 150.0))]


def arch_A(ZC):
    import compliance_d028 as C
    r, zg, zs = ram("y", ZC)
    groups = {
        "frame": [box("base", -200, 200, -350, 245, -168, -68, 3), box("base_cross", -320, 320, 145, 245, -168, -68, 3),
                  box("uprights_L", -320, -270, 145, 245, -68, 180, 4), box("uprights_R", 270, 320, 145, 245, -68, 180, 4),
                  box("beam", -320, 320, 145, 245, 180, 480, 4)],
        "table": [box("table", -225, 225, -175, 175, -40, 0, 3, 3, 6)],
        "zsup": [box("carriage", -100, 100, 93, 117, 150, ZC + 340, 4)],
        "ram": [r],
    }
    g = zg + [dict(name=f"yblk_{i}{j}", block="table", rail="frame", normal=2, free=1, cb=-40.0, cr=-68.0, c=(x, y, -54.0))
              for i, x in enumerate((-190, 190)) for j, y in enumerate((-120, 120))]
    g += [dict(name=f"xblk_{i}{j}", block="zsup", rail="frame", normal=1, free=0, cb=117.0, cr=145.0, c=(x, 131.0, z))
          for i, x in enumerate((-60, 60)) for j, z in enumerate((205, 455))]
    s = zs + [dict(name="yscr", a=dict(body="table", plane=(2, -40.0), rect={0: (-20, 20), 1: (-20, 20)}),
                   b=dict(body="frame", plane=(2, -68.0), rect={0: (-20, 20), 1: (200, 230)}), axis=1,
                   k=C.screw_axial("SFU1605", "BK12", 214.0)),
              dict(name="xscr", a=dict(body="zsup", plane=(1, 117.0), rect={0: (-20, 20), 2: (315, 345)}),
                   b=dict(body="frame", plane=(1, 145.0), rect={0: (280, 310), 2: (315, 345)}), axis=0,
                   k=C.screw_axial("SFU1605", "BK12", 277.0))]
    return dict(desc="B0-A · cinematica attuale ripensata: base a cassoni chiusi, tavola Y scatolata, trave 300 × 100, guide più larghe",
                groups=groups, guides=g, screws=s, extra=0.0, wp="table",
                feet=("frame", -168.0, [(-190, -340), (190, -340), (0, 235)]), fine=(-110, 110, -90, 125))


def arch_B(ZC):
    import compliance_d028 as C
    r, zg, zs = ram("y", ZC)
    groups = {
        "base": [box("base", -320, 320, -175, 450, -70, 0, 3, 3, 5)],
        "gantry": [box("uprights_L", -320, -270, 115, 275, 28, 180, 4), box("uprights_R", 270, 320, 115, 275, 28, 180, 4),
                   box("beam", -320, 320, 145, 245, 180, 480, 4)],
        "zsup": [box("carriage", -100, 100, 93, 117, 150, ZC + 340, 4)],
        "ram": [r],
    }
    g = zg + [dict(name=f"yblk_{i}{j}", block="gantry", rail="base", normal=2, free=1, cb=28.0, cr=0.0, c=(x, y, 14.0))
              for i, x in enumerate((-295, 295)) for j, y in enumerate((145, 245))]
    g += [dict(name=f"xblk_{i}{j}", block="zsup", rail="gantry", normal=1, free=0, cb=117.0, cr=145.0, c=(x, 131.0, z))
          for i, x in enumerate((-60, 60)) for j, z in enumerate((205, 455))]
    ky = C.screw_axial("SFU1605", "BK12", 214.0)
    s = zs + [dict(name=f"yscr_{i}", a=dict(body="gantry", plane=(2, 180.0), rect={0: (x0, x1), 1: (180, 210)}),
                   b=dict(body="base", plane=(2, 0.0), rect={0: (x0, x1), 1: (415, 445)}), axis=1, k=ky)
              for i, (x0, x1) in enumerate(((-268, -240), (240, 268)))]
    s.append(dict(name="xscr", a=dict(body="zsup", plane=(1, 117.0), rect={0: (-20, 20), 2: (315, 345)}),
                  b=dict(body="gantry", plane=(1, 145.0), rect={0: (280, 310), 2: (315, 345)}), axis=0,
                  k=C.screw_axial("SFU1605", "BK12", 277.0)))
    return dict(desc="B0-B · tavola fissa (cielo della base scatolata) + gantry mobile Y su guide laterali, due viti Y",
                groups=groups, guides=g, screws=s, extra=2.3, wp="base",
                feet=("base", -70.0, [(-300, -165), (300, -165), (0, 440)]), fine=(-110, 110, -90, 125))


def arch_C(ZC):
    import compliance_d028 as C
    r, zg, zs = ram("x", ZC)
    groups = {
        "frame": [box("base", -110, 200, -415, 415, -201, -131, 3),
                  box("post_F", 93, 193, -415, -355, -131, 210, 3), box("post_R", 93, 193, 355, 415, -131, 210, 3),
                  box("bridge", 93, 193, -415, 415, 210, 500, 3), box("bridge_tower", 93, 153, -100, 100, 500, ZC + 340, 3)],
        "saddle": [box("saddle", -410, 410, -110, 110, -103, -68, 3)],
        "table": [box("table", -225, 225, -175, 175, -40, 0, 3, 3, 6)],
        "ram": [r],
    }
    g = [dict(gg, rail="frame") for gg in zg]
    g += [dict(name=f"yblk_{i}{j}", block="saddle", rail="frame", normal=2, free=1, cb=-103.0, cr=-131.0, c=(x, y, -117.0))
          for i, x in enumerate((-100, 100)) for j, y in enumerate((-60, 60))]
    g += [dict(name=f"xblk_{i}{j}", block="table", rail="saddle", normal=2, free=0, cb=-40.0, cr=-68.0, c=(x, y, -54.0))
          for i, x in enumerate((-150, 150)) for j, y in enumerate((-80, 80))]
    s = [dict(zz, b=dict(zz["b"], body="frame")) for zz in zs]
    s += [dict(name="xscr", a=dict(body="table", plane=(2, -40.0), rect={0: (-20, 20), 1: (-20, 20)}),
               b=dict(body="saddle", plane=(2, -68.0), rect={0: (300, 330), 1: (-20, 20)}), axis=0,
               k=C.screw_axial("SFU1605", "BK12", 277.0)),
          dict(name="yscr", a=dict(body="saddle", plane=(2, -103.0), rect={0: (-20, 20), 1: (-20, 20)}),
               b=dict(body="frame", plane=(2, -131.0), rect={0: (-20, 20), 1: (300, 330)}), axis=1,
               k=C.screw_axial("SFU1605", "BK12", 214.0))]
    return dict(desc="B0-C · tavola XY (sella Y + tavola X) + testa solo Z su ponte fisso lungo Y a due colonne",
                groups=groups, guides=g, screws=s, extra=0.0, wp="table",
                feet=("frame", -201.0, [(-100, -405), (190, -405), (45, 405)]), fine=(-90, 110, -95, 95))


def arch_R(ZC):
    """Mule v3 ridotto a skeleton (calibrazione): stessa disposizione, sezioni e masse del mule."""
    import compliance_d028 as C
    r, zg, zs = ram("y", ZC, lat=55.0, pitch=80.0)
    lon = [box(f"frame_lon_{s}", x0, x1, -350, 350, -84, -24, 3, ribs=False, scale=False) for s, (x0, x1) in (("L", (-170, -130)), ("R", (130, 170)))]
    cross = [box(f"frame_cross_{i}", -130, 130, y0, y1, -84, -29, 3, ribs=False, scale=False) for i, (y0, y1) in enumerate(((-350, -310), (-250, -210), (310, 350)))]
    groups = {
        "frame": lon + cross + [box("frame_rear", -380, 380, 116, 249.5, -84, -29, 3, ribs=False, scale=False),
                                box("uprights_L", -380, -340, 116, 236, -29, 150, 5, ribs=False, scale=False), box("uprights_R", 340, 380, 116, 236, -29, 150, 5, ribs=False, scale=False),
                                box("beam", -380, 380, 136, 216, 150, 290, 6.3, ribs=False, scale=False)],
        "table": [box("table", -225, 225, -175, 175, -8, 0)],
        "zsup": [box("carriage", -95, 95, 93, 108, 130, ZC + 340)],
        "ram": [r],
    }
    g = zg + [dict(name=f"yblk_{i}{j}", block="table", rail="frame", normal=2, free=1, cb=-8.0, cr=-24.0, c=(x, y, -16.0), kind="MGN15H")
              for i, x in enumerate((-150, 150)) for j, y in enumerate((-100, 100))]
    g += [dict(name=f"xblk_{i}{j}", block="zsup", rail="frame", normal=1, free=0, cb=108.0, cr=136.0, c=(x, 122.0, z))
          for i, x in enumerate((-50, 50)) for j, z in enumerate((165, 275))]
    s = zs + [dict(name="yscr", a=dict(body="table", plane=(2, -8.0), rect={0: (-20, 20), 1: (-20, 20)}),
                   b=dict(body="frame", plane=(2, -29.0), rect={0: (-20, 20), 1: (200, 230)}), axis=1,
                   k=C.screw_axial("SFU1605", "BK12", 214.0)),
              dict(name="xscr", a=dict(body="zsup", plane=(1, 108.0), rect={0: (-20, 20), 2: (205, 235)}),
                   b=dict(body="frame", plane=(1, 136.0), rect={0: (280, 310), 2: (205, 235)}), axis=0,
                   k=C.screw_axial("SFU1605", "BK12", 277.0))]
    return dict(fit=False, desc="B0-R · calibrazione: mule v3 ridotto a skeleton (telaio a scala, piastra 8 mm, MGN15H, trave 80 × 140)",
                groups=groups, guides=g, screws=s, extra=0.0, wp="table",
                feet=("frame", -84.0, [(-150, -340), (150, -340), (0, 240)]), fine=(-110, 110, -90, 125))


ARCH_FN = dict(A=arch_A, B=arch_B, C=arch_C, R=arch_R)


def head_geometry():
    SC.apply("C3c")
    F.S = P.SPINDLE
    g = F.geometry(clamp_block=56.0)
    ZC = TIP_Z - g["z"]["tip"]
    return g, ZC


def masses(spec, g):
    """kg dai volumi CadQuery: cassoni per parte, receiver + mount della testa; lo spindle è nella quota commerciale."""
    rho = ccx.MATERIALS["AL"]["rho"]
    parts = {b["name"]: solid(b).Volume() * rho for bs in spec["groups"].values() for b in bs}
    head = (g["receiver"].Volume() + g["mount"].Volume()) * rho
    struct = sum(fuse(bs).Volume() * rho for bs in spec["groups"].values()) + head      # parti fuse: sovrapposizioni una volta
    return dict(parts={k: round(v, 3) for k, v in parts.items()}, head_al=round(head, 3), struct=round(struct, 2),
                allowance=ALLOW, extra=spec["extra"], machine=round(struct + ALLOW + spec["extra"], 1),
                machine_exact=struct + ALLOW + spec["extra"], wall_scale=round(spec.get("wall_scale", 1.0), 3),
                walls={b["name"]: round(b["t"], 2) for bs in spec["groups"].values() for b in bs if b["t"] is not None},
                lands=round(sum(v for k, v in parts.items() if k.startswith("pad_")), 2))


PAD = 6.0          # mm: appoggi pieni (lamature) sotto pattini, rotaie lungo la corsa, viti e pezzo, verso l'interno
TRAVEL = {0: 450.0, 1: 350.0, 2: 140.0}


def add_pads(spec):
    """Appoggi pieni: dove una guida, una vite o il pezzo scaricano su una parete, la parete ha un appoggio da PAD mm."""
    import compliance_d028 as C
    out = dict(spec, groups={k: list(v) for k, v in spec["groups"].items()})
    pads = {k: [] for k in out["groups"]}

    def host(body, ax, c, pt):
        for b in spec["groups"][body]:
            bb = b["bb"]
            if all(bb[2 * a] - 1e-6 <= pt[a] <= bb[2 * a + 1] + 1e-6 for a in range(3) if a != ax):
                if abs(bb[2 * ax] - c) < 1e-6:
                    return bb, 1.0
                if abs(bb[2 * ax + 1] - c) < 1e-6:
                    return bb, -1.0
        raise SystemExit(f"nessun cassone con la faccia {ax}={c} in {body} vicino a {pt}")

    def pad(body, ax, c, rect, pt, name):
        bb, sg = host(body, ax, c, pt)
        lo, hi = [0.0] * 3, [0.0] * 3
        lo[ax], hi[ax] = (c, c + PAD) if sg > 0 else (c - PAD, c)
        for a, (r0, r1) in rect.items():
            lo[a], hi[a] = max(r0, bb[2 * a]), min(r1, bb[2 * a + 1])
        pads[body].append(box(f"pad_{name}", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], ribs=False, scale=False))

    for gd in spec["guides"]:
        kind = gd.get("kind", BLK)
        L, W = C.parts.BLOCKS[kind]["L"], C.parts.BLOCKS[kind]["W"]
        n_, f_ = gd["normal"], gd["free"]
        l_ = 3 - n_ - f_
        c = gd["c"]
        pb, pr = list(c), list(c)
        pb[n_], pr[n_] = gd["cb"], gd["cr"]
        pad(gd["block"], n_, gd["cb"], {f_: (c[f_] - L / 2 - 5, c[f_] + L / 2 + 5), l_: (c[l_] - W / 2 - 5, c[l_] + W / 2 + 5)}, pb, gd["name"])
        pad(gd["rail"], n_, gd["cr"], {f_: (c[f_] - L / 2 - TRAVEL[f_] / 2, c[f_] + L / 2 + TRAVEL[f_] / 2), l_: (c[l_] - 12.5, c[l_] + 12.5)}, pr, gd["name"] + "_rail")
    for sc in spec["screws"]:
        for side in ("a", "b"):
            sp_ = sc[side]
            ax, cc = sp_["plane"]
            pt = [0.0] * 3
            pt[ax] = cc
            for a, (r0, r1) in sp_["rect"].items():
                pt[a] = (r0 + r1) / 2
            pad(sp_["body"], ax, cc, {a: (r0 - 5, r1 + 5) for a, (r0, r1) in sp_["rect"].items()}, pt, f"{sc['name']}_{side}")
    pad(spec["wp"], 2, 0.0, {0: (-55, 55), 1: (-55, 55)}, (0.0, 0.0, 0.0), "workpiece")
    for body, ps in pads.items():
        out["groups"][body] = ps + out["groups"][body]          # prima gli appoggi: gli elementi al loro interno sono loro
    return out


def fitted(arch):
    """Architettura con appoggi e pareti scalate fino a MASS_TARGET in CENTER (secante sulla massa CadQuery)."""
    g, ZC = head_geometry()
    spec = ARCH_FN[arch](ZC)
    if spec.get("fit", True):
        spec = add_pads(spec)
    if not spec.get("fit", True):
        return dict(spec, wall_scale=1.0), g, ZC
    f0, m0 = 1.0, masses(spec, g)["machine_exact"]
    f1 = f0 * 1.1
    m1 = masses(scaled(spec, f1), g)["machine_exact"]
    for _ in range(6):
        f2 = f1 + (MASS_TARGET - m1) * (f1 - f0) / (m1 - m0)
        m2 = masses(scaled(spec, f2), g)["machine_exact"]
        f0, m0, f1, m1 = f1, m1, f2, m2
        if abs(m2 - MASS_TARGET) < 0.02:
            break
    return scaled(spec, f1), g, ZC


# ---------------------------------------------------------------------------------------------- modello
def build(arch, h, hc, rigid_head=False):
    import compliance_d028 as C
    spec, g, ZC = fitted(arch)
    z = {k: (v + ZC if isinstance(v, float) and k not in ("r_bore", "master_top") else v) for k, v in g["z"].items()}
    mv = lambda s: s.translate(cq.Vector(0.0, 0.0, ZC))  # noqa: E731
    m = ccx.Model(f"b0_{arch}", WORK / f"d032_b0_{arch}_h{h:g}_c{hc:g}{'_rh' if rigid_head else ''}")
    for body, bs in spec["groups"].items():
        m.body(body, [fuse(bs)], "AL")
    m.body("head", [mv(g["receiver"]), mv(g["mount"]), mv(g["body"])], "AL")
    m.body("shaft", mv(g["shaft"]), "STEEL")
    hl = F.H_LOCAL * h / F.H_NOM
    R = C.COUPLING_R
    balls = [(R * math.cos(math.radians(t)), R * math.sin(math.radians(t))) for t in F.BALL_ANGLES]
    for (bx, by) in balls:
        m.refine_at(bx, by, ZC, 12.0, hl)
    for zz in (z["collar0"], z["collar1"], z["b"], z["top"]):
        for t in range(0, 360, 45):
            m.refine_at(z["r_bore"] * math.cos(math.radians(t)), z["r_bore"] * math.sin(math.radians(t)), zz, 8.0, hl)
    m.refine_at(0, 0, z["tip"] + 12, 16.0, hl)
    fx0, fx1, fy0, fy1 = spec["fine"]
    m.box_size = (fx0, fx1, fy0, fy1, TIP_Z - 15.0, ZC + 240.0, h)
    info = m.mesh(hc)
    # testa: il tubo del corpo spindle è acciaio
    ids, conn = m.elements["head"]
    p = m.xyz(conn[:, :4].ravel()).reshape(-1, 4, 3).mean(axis=1)
    rr = np.hypot(p[:, 0], p[:, 1])
    tube = (rr < z["r_bore"] + 0.01) & (rr > z["r_bore"] - 5.2) & (p[:, 2] < z["rear"] + 0.01)
    q = m.quality["head"]
    m.elements["spindle_body"], m.elements["head"] = (ids[tube], conn[tube]), (ids[~tube], conn[~tube])
    m.quality["spindle_body"], m.quality["head"] = q[tube], q[~tube]
    m.bodies.append(("spindle_body", [], "STEEL"))
    m.body_nodes["spindle_body"] = np.unique(conn[tube])
    # corpi fusi: elementi divisi per parte (baricentro nel box della parte) per energia e lettura
    part_groups = {}
    for body, bs in spec["groups"].items():
        gid, gconn = m.elements.pop(body)
        gq = m.quality.pop(body)
        gc = m.xyz(gconn[:, :4].ravel()).reshape(-1, 4, 3).mean(axis=1)
        left = np.ones(len(gid), bool)
        for b in bs:
            x0, x1, y0, y1, z0, z1 = b["bb"]
            sel = left & (gc[:, 0] >= x0) & (gc[:, 0] <= x1) & (gc[:, 1] >= y0) & (gc[:, 1] <= y1) & (gc[:, 2] >= z0) & (gc[:, 2] <= z1)
            if sel.any():
                pn = "lands" if b["name"].startswith("pad_") else (b["name"].rsplit("_", 1)[0] if b["name"].split("_")[0] in ("uprights", "frame", "post") else b["name"])
                key = f"{body}__{b['name']}"
                m.elements[key], m.quality[key] = (gid[sel], gconn[sel]), gq[sel]
                m.bodies.append((key, [], "AL"))
                part_groups.setdefault(pn, []).append(key)
                left &= ~sel
        if left.any():
            raise SystemExit(f"{body}: {int(left.sum())} elementi fuori dai box delle parti")
        m.bodies = [bb for bb in m.bodies if bb[0] != body]
    m.energy_groups = {pn: (keys, ()) for pn, keys in part_groups.items()}
    m.energy_groups.update({"head": (["head", "spindle_body", "shaft"], ()), "yblocks": ((), ("yblk",)), "xblocks": ((), ("xblk",)),
                            "zblocks": ((), ("zblk",)), "yscrew": ((), ("yscr",)), "xscrew": ((), ("xscr",)), "zscrew": ((), ("zscr",)),
                            "tooldock": ((), ("ball",)), "bearing": ((), ("bearing",))})
    eps = 1e-3

    def patch(spec_p, name):
        ax, c = spec_p["plane"]
        rect = spec_p["rect"]

        def fn(x, y, zz):
            pp = (x, y, zz)
            ok = np.abs(pp[ax] - c) < eps
            for a_, (lo, hi) in rect.items():
                ok &= (pp[a_] >= lo - eps) & (pp[a_] <= hi + eps)
            return ok
        n = m.select(spec_p["body"], fn)
        if len(n) < 3:
            raise SystemExit(f"patch {name} vuota ({spec_p})")
        return n

    # pattini: impronta del pattino sul corpo mobile, impronta della rotaia (15 mm) sul corpo che la porta
    for gd in spec["guides"]:
        kind = gd.get("kind", BLK)
        L, W = C.parts.BLOCKS[kind]["L"], C.parts.BLOCKS[kind]["W"]
        n_, f_ = gd["normal"], gd["free"]
        l_ = 3 - n_ - f_
        c = gd["c"]
        pb = patch(dict(body=gd["block"], plane=(n_, gd["cb"]), rect={f_: (c[f_] - L / 2, c[f_] + L / 2), l_: (c[l_] - W / 2, c[l_] + W / 2)}), gd["name"])
        pr = patch(dict(body=gd["rail"], plane=(n_, gd["cr"]), rect={f_: (c[f_] - L / 2, c[f_] + L / 2), l_: (c[l_] - 7.5, c[l_] + 7.5)}), gd["name"] + "_rail")
        m.spring6(gd["name"], m.rigid_body(gd["name"] + "_b", pb, c), m.rigid_body(gd["name"] + "_r", pr, c), list(C.block_k(kind, axis_free=f_, normal=n_)))
    for sc in spec["screws"]:
        ends = []
        for side in ("a", "b"):
            sp_ = sc[side]
            n = patch(sp_, f"{sc['name']}_{side}")
            ends.append(m.rigid_body(f"{sc['name']}_{side}", n, tuple(m.xyz(n).mean(axis=0))))
        m.spring(sc["name"], ends[0][0], sc["axis"] + 1, ends[1][0], sc["axis"] + 1, sc["k"])
    # ToolDock: tre sfere tra fondo del ram e receiver
    _, kc = C.coupling_k()
    for i, ((bx, by), ang) in enumerate(zip(balls, F.BALL_ANGLES)):
        pm = patch(dict(body="ram", plane=(2, ZC), rect={0: (bx - F.BALL_PATCH_R, bx + F.BALL_PATCH_R), 1: (by - F.BALL_PATCH_R, by + F.BALL_PATCH_R)}), f"sfera {i} ram")
        ph = patch(dict(body="head", plane=(2, ZC), rect={0: (bx - F.BALL_PATCH_R, bx + F.BALL_PATCH_R), 1: (by - F.BALL_PATCH_R, by + F.BALL_PATCH_R)}), f"sfera {i} testa")
        pm = pm[np.hypot(m.xyz(pm)[:, 0] - bx, m.xyz(pm)[:, 1] - by) <= F.BALL_PATCH_R]
        ph = ph[np.hypot(m.xyz(ph)[:, 0] - bx, m.xyz(ph)[:, 1] - by) <= F.BALL_PATCH_R]
        a1, b1 = m.rigid_body(f"ball{i}_m", pm, (bx, by, ZC)), m.rigid_body(f"ball{i}_h", ph, (bx, by, ZC))
        m.spring(f"ball{i}_n", a1[0], 3, b1[0], 3, kc)
        m.spring_dir(f"ball{i}_t", a1[0], b1[0], (-math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0.0), kc)
    ring = m.select("spindle_body", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    top = m.select("shaft", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    hb, sb = m.rigid_body("bearing_h", ring, (0, 0, z["b"])), m.rigid_body("bearing_s", top, (0, 0, z["b"]))
    kb = P.SPINDLE["k_bearing"]
    m.spring6("bearing", hb, sb, [kb, kb, 3 * kb, kb * 25.0 ** 2, kb * 25.0 ** 2, 1e9])
    tip = m.rigid_body("tip", m.select("shaft", lambda x, y, zz: np.abs(zz - z["tip"]) < eps), (0, 0, z["tip"]))
    wpn = m.select(spec["wp"], lambda x, y, zz: (np.abs(zz) < eps) & (np.hypot(x, y) <= 40.0))
    wp = m.rigid_body("workpiece", wpn, (0, 0, TIP_Z))       # pezzo rigido: il fixture è nel budget a parte
    # vincolo isostatico 3-2-1 sotto la base
    fb, zf, feet = spec["feet"]
    for i, (fx, fy) in enumerate(feet):
        n = m.select(fb, lambda x, y, zz: (np.abs(zz - zf) < eps) & (np.hypot(x - fx, y - fy) <= 15.0))
        ref, _ = m.rigid_body(f"foot{i}", n, (fx, fy, zf))
        m.spc += [(ref, d) for d in ((1, 2, 3), (2, 3), (3,))[i]]
    for name, d in (("Fx", 1), ("Fy", 2), ("Fz", 3)):
        m.step(name, [(tip[0], d, FL), (wp[0], d, -FL)])
    if rigid_head:                               # diagnostica: testa, ToolDock e cuscinetti "infinitamente" rigidi
        m.bodies = [(n, s_, "RIGID" if n in ("head", "spindle_body", "shaft") else mt) for n, s_, mt in m.bodies]
        m.springs = [(n, a_, d1, b_, d2, k * 1000.0 if n.startswith(("ball", "bearing")) else k) for n, a_, d1, b_, d2, k in m.springs]
    return m, info, spec, tip, wp


def _cases(m, tip, wp, names):
    disp, _ = m.run([tip[0], wp[0]])
    energy = m.read_energy()
    out = {}
    for name, d in (("Fx", 0), ("Fy", 1), ("Fz", 2)):
        if name not in names:
            continue
        u = (np.array(disp[name][tip[0]]) - np.array(disp[name][wp[0]])) * 1000.0      # µm, punta − pezzo
        w = 0.5 * FL * abs(float(u[d])) / 1000.0
        e = energy.get(name, {})
        out[name] = dict(du=[round(float(v), 3) for v in u], k=round(FL / abs(float(u[d])), 3), work=round(w, 6),
                         balance=round(sum(e.values()) / w, 4), energy={gg: round(v, 6) for gg, v in e.items()})
    return out


def solve(arch, h, hc, rigid_head=False):
    """Tre casi nello stesso run; un caso fuori dal bilancio energetico (±2%) si risolve da solo in un run separato
    (in CalculiX con SPOOLES il terzo step di un run a più step è risultato a volte numericamente corrotto)."""
    tag = f"d032_b0_{arch}_h{h:g}_c{hc:g}{'_rh' if rigid_head else ''}"
    t0 = time.time()
    m, info, spec, tip, wp = build(arch, h, hc, rigid_head)
    res = _cases(m, tip, wp, ("Fx", "Fy", "Fz"))
    solve_s, single = m.solve_s, []
    for n in [n for n, c in res.items() if abs(c["balance"] - 1.0) > 0.02]:
        print(f"{tag}: bilancio energetico {res[n]['balance']} in {n}, lo risolvo da solo", flush=True)
        m1, _, _, tip1, wp1 = build(arch, h, hc, rigid_head)
        m1.name, m1.dir = f"{m.name}_{n}", m.dir / f"only_{n}"
        m1.dir.mkdir(parents=True, exist_ok=True)
        m1.steps = [st for st in m1.steps if st[0] == n]
        res[n] = _cases(m1, tip1, wp1, (n,))[n]
        solve_s += m1.solve_s
        single.append(n)
    bad = [n for n, c in res.items() if abs(c["balance"] - 1.0) > 0.02]
    g = head_geometry()[0]
    r = dict(arch=arch, desc=spec["desc"], tag=tag, h=h, hc=hc, mesh=info, solve_s=solve_s, total_s=round(time.time() - t0, 1),
             k={n: c["k"] for n, c in res.items()}, du_um={n: c["du"] for n, c in res.items()}, work={n: c["work"] for n, c in res.items()},
             balance={n: c["balance"] for n, c in res.items()}, energy_balance_ok=not bad, solved_alone=single,
             energy={n: c["energy"] for n, c in res.items()}, mass=masses(spec, g), date=time.strftime("%Y-%m-%d"))
    return r


# ---------------------------------------------------------------------------------------------- pagina
def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


GROUP_LABEL = [  # (etichetta, gruppi di energia)
    ("Testa e ToolDock", ("head", "tooldock", "bearing")),
    ("Ram Z + pattini/vite Z", ("ram", "zblocks", "zscrew")),
    ("Carrello X / ponte", ("carriage", "bridge", "post")),
    ("Pattini/vite X", ("xblocks", "xscrew")),
    ("Trave + spalle", ("beam", "uprights")),
    ("Base / telaio", ("base", "base_cross", "frame")),
    ("Tavola / sella", ("table", "saddle")),
    ("Pattini/vite Y", ("yblocks", "yscrew")),
    ("Appoggi", ("lands",)),
]


def page():
    res = {a: json.loads((OUT / f"B0-{a}.json").read_text()) for a in ARCHS if (OUT / f"B0-{a}.json").exists()}
    order = [a for a in ("A", "B", "C", "R") if a in res]

    def cls(v, ax):
        return "status-ok" if v >= GATE[ax] else ("status-target" if v >= 0.7 * GATE[ax] else "status-critical")
    rows = ""
    for a in order:
        r = res[a]
        kk = dict(X=r["k"]["Fx"], Y=r["k"]["Fy"], Z=r["k"]["Fz"])
        mm = r["mass"]["machine"]
        gate = all(kk[ax] >= GATE[ax] for ax in "XYZ") and mm <= MASS_LIMIT
        near = min(kk[ax] / GATE[ax] for ax in "XYZ")
        star = "" if r["energy_balance_ok"] else " *"
        rows += (f'<tr><td><b>B0-{a}</b>{star}<br><span style="color:var(--dim);font-size:12px">{r["desc"].split("·", 1)[1].strip()}</span></td>'
                 + "".join(f'<td class="{cls(kk[ax], ax)}">{it(kk[ax], 2)}</td>' for ax in "XYZ")
                 + f'<td>{it(80 / min(kk["X"], kk["Y"]), 0)} / {it(150 / kk["Z"], 0)} µm</td>'
                 + f'<td class="{"status-ok" if mm <= MASS_LIMIT else "status-critical"}">{it(mm, 1)}</td>'
                 + f'<td>{it(near * 100, 0)}%</td><td>{"PASS" if gate else "—"}</td></tr>')
    # energia per gruppo (% del lavoro) per asse
    en = ""
    for a in order:
        r = res[a]
        for n, ax in (("Fx", "X"), ("Fy", "Y"), ("Fz", "Z")):
            e, w = r["energy"][n], r["work"][n]
            cells = ""
            for lab, keys in GROUP_LABEL:
                v = sum(val for gname, val in e.items() if any(gname == k_ or gname.startswith(k_ + "_") for k_ in keys)) / w * 100
                cells += f'<td>{it(v, 0) if v >= 0.5 else "·"}</td>'
            en += f'<tr><td>B0-{a} {ax}</td>{cells}<td>{it(r["balance"][n] * 100, 1)}%</td></tr>'
    heads = "".join(f"<th>{lab}</th>" for lab, _ in GROUP_LABEL)
    mrows = ""
    for a in order:
        mm = res[a]["mass"]
        parts = ", ".join(f"{k.replace('_', ' ')} {it(v, 1)}" for k, v in sorted(mm["parts"].items(), key=lambda t: -t[1]) if v >= 0.05 and not k.startswith("pad_"))
        parts += f", appoggi {it(mm.get('lands', 0.0), 1)}" if mm.get("lands") else ""
        mrows += (f'<tr><td>B0-{a}</td><td>{it(mm["struct"], 1)}</td><td>{it(mm["allowance"], 1)}{(" + " + it(mm["extra"], 1)) if mm["extra"] else ""}</td>'
                  f'<td>{it(mm["machine"], 1)}</td><td style="font-size:12px;color:var(--dim)">{parts}</td></tr>')
    walls_txt = "; ".join(f'B0-{a} ' + " / ".join(sorted({it(v, 1) for k, v in res[a]["mass"]["walls"].items() if k != "ram"})) + " mm"
                          for a in order if a != "R")
    mesh = "".join(f'<tr><td>B0-{a}</td><td>{res[a]["mesh"]["dof"]:,}</td><td>{it(res[a]["mesh"]["min_sj"], 2)}</td><td>{res[a]["mesh"]["poor"]}</td>'
                   f'<td>{res[a]["h"]:g} / {res[a]["hc"]:g}</td><td>{it(res[a]["solve_s"], 0)} s</td></tr>' for a in order).replace(",", ".")
    rh = {a: json.loads((OUT / f"B0-{a}-rh.json").read_text()) for a in order if (OUT / f"B0-{a}-rh.json").exists()}
    rh_rows, head_k = "", {}
    for a in [a for a in order if a in rh]:
        ks, kt = rh[a]["k"], res[a]["k"]
        hk = {n: (1.0 / (1.0 / kt[n] - 1.0 / ks[n]) if ks[n] > kt[n] else float("inf")) for n in ("Fx", "Fy", "Fz")}
        head_k[a] = hk
        rh_rows += (f'<tr><td>B0-{a}</td>' + "".join(f'<td class="{cls(ks[n], ax)}">{it(ks[n], 2)}</td>' for n, ax in (("Fx", "X"), ("Fy", "Y"), ("Fz", "Z")))
                    + "".join(f'<td>{it(hk[n], 2) if hk[n] != float("inf") else "∞"}</td>' for n in ("Fx", "Fy", "Fz")) + "</tr>")
    rh_sec = ""
    if rh_rows:
        rh_sec = f"""<section class="section"><h2>Senza la testa</h2><div class="table-wrap"><table><tr><th>Architettura</th><th>Struttura X</th><th>Struttura Y</th><th>Struttura Z</th><th>Catena testa X</th><th>Catena testa Y</th><th>Catena testa Z</th></tr>{rh_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Diagnostica: stessa FEA con testa, spindle, sfere del ToolDock e cuscinetti resi rigidi (moduli e molle ×1000). "Struttura" è la macchina senza la catena della testa; "catena testa" è ricavata in serie (1/k<sub>testa</sub> = 1/k<sub>macchina</sub> − 1/k<sub>struttura</sub>) ed è la rigidezza di ToolDock C3c + mount + spindle + cuscinetti vista dalla punta, N/µm.</p></section>"""
    reading = ""
    abc = [a for a in ("A", "B", "C") if a in res]
    if abc:
        kx = [min(res[a]["k"]["Fx"], res[a]["k"]["Fy"]) for a in abc]
        kz = [res[a]["k"]["Fz"] for a in abc]
        reading = (f"Nessuno dei tre skeleton passa il gate: a {it(MASS_TARGET, 0)} kg in XY stanno tutti tra {it(min(kx), 2)} e {it(max(kx), 2)} N/µm "
                   f"(circa un terzo di {it(GATE['X'], 0)}), in Z tutti sopra {it(GATE['Z'], 0)} ({it(min(kz), 1)}–{it(max(kz), 1)} N/µm). ")
        if head_k:
            hx = [min(v["Fx"], v["Fy"]) for v in head_k.values()]
            sx = [min(rh[a]["k"]["Fx"], rh[a]["k"]["Fy"]) for a in head_k]
            reading += (f"La catena della testa C3c (ToolDock Ø110, mount, spindle, cuscinetti, braccio 203 mm) vale da sola ~{it(sum(hx) / len(hx), 1)} N/µm in XY "
                        f"in tutte e tre le architetture: con questa testa {it(GATE['X'], 0)} N/µm in XY è impossibile qualunque sia la struttura. "
                        f"Anche la sola struttura, a testa rigida, resta a {it(min(sx), 1)}–{it(max(sx), 1)} N/µm in XY: servirebbero testa e struttura "
                        f"entrambe a ≥ ~6 N/µm per avere 3 N/µm in serie. ")
        reading += ("Le tre cinematiche differiscono di circa il 10%: B0-B (tavola fissa, gantry mobile) è di poco la migliore in tutti gli assi, B0-C non accorcia "
                    "davvero il ciclo a parità di massa perché la sella in più e il portale a due colonne consumano la massa che il carrello X liberava "
                    "(pareti ~2 mm, energia in base, colonne e ponte). Z non è più il problema: con base e tavola scatolate a diaframmi tutti e tre superano il gate. "
                    "Come previsto dal B0, è la base per rimettere in discussione il requisito XY (o la testa), non per un altro concept della stessa famiglia.")
    best = max((a for a in order if a != "R"), key=lambda a: min(res[a]["k"][n] / GATE[ax] for n, ax in (("Fx", "X"), ("Fy", "Y"), ("Fz", "Z"))), default=None)
    cal = ""
    if "R" in res:
        kr = res["R"]["k"]
        cal = (f'<p style="color:var(--dim);font-size:13px;margin-top:12px"><b>Calibrazione.</b> Lo skeleton del mule v3 (B0-R) dà {it(kr["Fx"])} / {it(kr["Fy"])} / {it(kr["Fz"])} N/µm '
               f'contro {it(C3C_MACHINE["X"])} / {it(C3C_MACHINE["Y"])} / {it(C3C_MACHINE["Z"])} della macchina C3c (gantry FEA + resto D028): rapporto '
               f'{it(kr["Fx"] / C3C_MACHINE["X"])} / {it(kr["Fy"] / C3C_MACHINE["Y"])} / {it(kr["Fz"] / C3C_MACHINE["Z"])}. Gli skeleton non hanno giunti bullonati, '
               f'lamature, tasche né staffe, e i cassoni sono incollati: vanno letti come limite superiore della loro architettura.</p>')
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — B0 architecture screen · D032</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d032_b0.py: non modificare a mano. -->
<a class="back" href="fea-d032-lim.html">← D032-LIM</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D032 · B0 architecture screen</div><h1>Tre architetture,<br>stessa massa.</h1><p class="lead">Dopo D032-LIM (serve circa ×3,8 della rigidezza complessiva di C3c per il gate): tre skeleton brutali, non CAD, misurati con la stessa FEA a ciclo chiuso utensile ↔ pezzo, la stessa testa C3c, lo stesso modulo Z, gli stessi pattini e lo stesso criterio di massa. Gate del survivor: vicino a <b>{it(GATE["X"], 0)} / {it(GATE["Y"], 0)} / {it(GATE["Z"], 0)} N/µm</b> con <b>≤ {it(MASS_LIMIT, 0)} kg</b> stimati in CENTER. Target D032 invariati.</p><div class="badges"><span class="badge ok">D032 · B0</span><span class="badge">Skeleton, non CAD</span><span class="badge">Ciclo chiuso utensile ↔ pezzo</span><span class="badge">MULE · TARGET</span></div></div>

<section class="section"><h2>Risultato</h2><div class="table-wrap"><table>
<tr><th>Architettura</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th><th>δXY 80 N / δZ 150 N</th><th>Massa CENTER kg</th><th>Asse peggiore vs gate</th><th>Gate</th></tr>
{rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Rigidezza relativa naso spindle ↔ pezzo (rigido) sotto una coppia di forze (pezzo rigido Ø80 su un appoggio 110 × 110), vincolo isostatico 3-2-1: è la macchina intera, senza utensile né fixture (che restano nel budget D032 a parte). Verde ≥ gate, giallo ≥ 70% del gate, rosso sotto. δ = deformazione della sola macchina a SERVICE HIGH. * = bilancio energetico fuori dal 2%.</p>{cal}</section>
{rh_sec}
<section class="section"><h2>Dove si deforma</h2><div class="table-wrap"><table><tr><th>Caso</th>{heads}<th>Bilancio</th></tr>{en}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Energia di deformazione per gruppo, % del lavoro della coppia di forze (½ F δ). Somma = bilancio energetico.</p></section>

<section class="section"><h2>Massa</h2><div class="table-wrap"><table><tr><th>Architettura</th><th>Struttura (cassoni + receiver/mount) kg</th><th>Commerciali e staffe kg</th><th>CENTER kg</th><th>Parti (kg)</th></tr>{mrows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Quota commerciale e staffe dal mule C3c ({it(ALLOW, 1)} kg: 45,7 kg meno 25,7 kg di parti strutturali custom, spindle incluso). B0-B aggiunge la seconda vite Y con motore (+2,3 kg). Stesso criterio per A, B e C: cassoni chiusi con diaframmi interni a passo ≤ {it(RIB_PITCH, 0)} mm (spessore = parete) appoggi pieni da {it(PAD, 0)} mm sotto pattini, rotaie (lungo la corsa), viti e pezzo, e pareti scalate insieme finché la macchina fa {it(MASS_TARGET, 0)} kg in CENTER; il ram Z (pareti 5, fondo 12) è uguale per tutti. Pareti risultanti: {walls_txt}. B0-R ha le sezioni del mule senza diaframmi.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Skeleton</span><h2>Cosa c'è dentro.</h2><ul>
  <li><b>B0-A</b>: base a cassoni chiusi (spina 400 × 595 + traversa sotto le spalle, h 100), tavola Y scatolata 450 × 350 × 40, guide Y a 380 (pattini ±120), trave 640 × 100 × 300 su spalle 50 × 100, guide X a 250 (abbracciano i pattini Z), carrello scatolato 24 mm: asse → guide X 145 mm (mule 136, ma su una trave 2× più alta).</li>
  <li><b>B0-B</b>: la base scatolata 640 × 625 × 70 (cielo 5 mm) è la tavola; gantry (stessa trave e carrello di A) su due guide Y laterali a ±295, due viti Y. La trave copre solo la larghezza della tavola.</li>
  <li><b>B0-C</b>: base 310 × 830 × 70, sella Y 820 × 220 × 35 (pattini Y a 200), tavola X scatolata sopra (pattini X a 300 × 160); ponte fisso 100 × 290 lungo Y (luce 710 tra le colonne) con torretta centrale per le guide Z alte, ram Z direttamente sulle sue guide: niente carrello X.</li>
  <li><b>B0-R</b>: calibrazione sul mule v3 (telaio a scala 40 × 60, piastra 8, MGN15H, trave 80 × 140, carrello pieno 15).</li></ul></div>
  <div class="panel"><span class="kicker">Modello</span><h2>Uguale per tutti.</h2><ul>
  <li>Testa C3c (coupling Ø110, braccio 203 mm, sfere e cuscinetti D028), punta 70 mm sopra il piano in CENTER.</li>
  <li>Ram Z scatolato 150 × 135 × 220, pattini HGH15CA a 114 × 140 (R: 110 × 80), vite Z SFU1204 in catena D028.</li>
  <li>Pattini HGH15CA ZA su tutti gli assi (D028, 365 N/µm; R: MGN15H in Y), viti SFU1605 con BK12.</li>
  <li>Tetra quadratici, fine attorno a testa e ram, grossa sui cassoni; soluzione valida solo con bilancio energetico entro il 2%.</li></ul>
  <div class="table-wrap"><table><tr><th>Mesh</th><th>gdl</th><th>minSJ</th><th>scarsi</th><th>h fine / grossa</th><th>soluzione</th></tr>{mesh}</table></div></div>
</section>

<section class="section"><div class="callout" style="border-color:rgba(255,84,112,.45)"><b>Lettura.</b> {reading}</div></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d032_b0.py --arch A</code> (poi B, C, R) e <code>python tools/fea/d032_b0.py --page</code>. Le quote degli skeleton stanno nelle funzioni <code>arch_*</code> dello script.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")
    print("pagina", PAGE, {a: res[a]["k"] for a in order})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", choices=ARCHS)
    ap.add_argument("--h", type=float, default=8.0)
    ap.add_argument("--coarse", type=float, default=18.0)
    ap.add_argument("--check", action="store_true", help="solo masse e mesh")
    ap.add_argument("--mass", action="store_true", help="solo masse")
    ap.add_argument("--page", action="store_true")
    ap.add_argument("--rigid-head", action="store_true", help="diagnostica: testa, ToolDock e cuscinetti rigidi (solo struttura)")
    a = ap.parse_args()
    if a.page:
        page()
        return
    if a.mass or a.check:
        for ar in ([a.arch] if a.arch else ARCHS):
            spec, g, ZC = fitted(ar)
            print(ar, json.dumps(masses(spec, g)), flush=True)
            if a.check:
                m, info, *_ = build(ar, a.h, a.coarse)
                print(ar, info, flush=True)
        return
    r = solve(a.arch, a.h, a.coarse, a.rigid_head)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"B0-{a.arch}{'-rh' if a.rigid_head else ''}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, default=float))
    print(a.arch, r["k"], r["mass"]["machine"], "kg", r["balance"], r["mesh"], r["solve_s"], "s", flush=True)
    page()


if __name__ == "__main__":
    main()
