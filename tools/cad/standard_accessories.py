#!/usr/bin/env python3
"""Base Standard · CAD degli accessori (fuori dai totali della BOM): rialzi spalle, magazine ToolDock, cabina.

Chiamato da standard_parts.py (export(OUT)). Gli STEP stanno nelle coordinate macchina in HOME, così si sovrappongono
allo STEP del mule. Livelli:
- MC-RS-001 rialzi spalle +75 mm (D007, D008, ICD v4 §5): pezzo di dettaglio, stesso pattern sopra e sotto;
- MC-TD-006 magazine 2 posti + trasferitore (D021, D027, D030): CAD di layout, non di fabbricazione. Posti, navetta,
  assi del trasferitore e forcella sono dimensionati sulla traiettoria del mule (magazine → sopra la trave → davanti →
  giù → −X → +Y fino al dock a X 440); guide, motori e strutture restano TARGET finché il magazine non entra in progetto;
- MC-ENC-001 cabina: telaio 30 × 30 indipendente con piedi propri, agganciato al basamento e mai al ponte (D025),
  pannelli PC 4 mm, porta frontale con interlock, vasca trucioli, attacco aspirazione Ø100.
"""
import math

import cadquery as cq

import standard_params as P
import standard_detail as SD
from standard_detail import box, cyl

AL_RHO = P.AL_DENSITY
PC_RHO = 1.20e-6
STEEL_RHO = 7.85e-6


def fused(solids):
    s = solids[0]
    for x in solids[1:]:
        s = s.fuse(x)
    return s.clean()


# ---------------------------------------------------------------- rialzi spalle (ICD v4 §5)
def riser(side, h=None):
    h = h or P.RISER_H
    """Blocco scatolato 80 × 140 × h: fondo e cielo 16 mm, pareti 8; fondo filettato M8 (viti dal basso attraverso la
    traversa, come la spalla), cielo passante (viti dalla finestra frontale nella flangia della spalla), spine Ø10 H7
    su entrambe le facce. Si monta fra traversa posteriore e spalla."""
    I = SD.ICD_UPRIGHT
    D = P.derived()
    yc = (D["beam_face"] + D["beam_back"]) / 2
    fx = (P.BEAM_X[0] - P.UPRIGHT["t"], P.BEAM_X[1] + P.UPRIGHT["t"]) if P.UPRIGHT_MODE == "plate" else P.BEAM_X
    x0 = fx[0] if side == "L" else fx[1] - I["flange"][0]
    x1 = x0 + I["flange"][0]
    xc = (x0 + x1) / 2
    y0, y1 = yc - I["flange"][1] / 2, yc + I["flange"][1] / 2
    z0 = -P.LADDER["cross_drop"]                 # faccia superiore della traversa posteriore
    z1 = z0 + h
    t, w = 16.0, 8.0
    b = box(x0, x1, y0, y1, z0, z1).cut(box(x0 + w, x1 - w, y0 + w, y1 - w, z0 + t, z1 - t))
    b = b.cut(box(x0 + w, x1 - w, y0 - 1, y0 + w + 0.1, z0 + t, z1 - t))   # finestra d'accesso frontale alle viti del cielo
    for sx in (-1, 1):                          # sotto: filettato (viti dal basso come la spalla); sopra: passante, dalla finestra
        for sy in (-1, 1):
            x, y = xc + sx * I["rect"][0] / 2, yc + sy * I["rect"][1] / 2
            b = b.cut(cyl("z", z0 - 1, z0 + t - 2, x, y, SD.TAP["M8"] / 2))
            b = b.cut(cyl("z", z1 - t - 1, z1 + 1, x, y, SD.CLR["M8"] / 2))
    for sy in (-1, 1):
        y = yc + sy * I["pins"] / 2
        b = b.cut(cyl("z", z0 - 1, z0 + 12, xc, y, I["pin_d"] / 2)).cut(cyl("z", z1 - 12, z1 + 1, xc, y, I["pin_d"] / 2))
    return b


# ---------------------------------------------------------------- magazine e trasferitore (layout)
def magazine():
    """Posti, navetta e trasferitore come solidi di layout, trasferitore nella posa di prelievo dal magazine.
    Ritorna {nome: solido}."""
    D = P.derived()
    out = {}
    sx, sy = P.STORE_POSE
    top = P.TRANSFER_TOP
    hd = P.HEAD
    ux1 = P.BEAM_X[1] + (P.UPRIGHT["t"] if P.UPRIGHT_MODE == "plate" else 0.0)
    if P.UPRIGHT_MODE == "lift":        # Pro: faccia posteriore del montante destro del Gantry Lift
        import parts as _pt
        yu1 = D["beam_back"] + P.LIFT["bracket_t"] + _pt.BLOCKS[P.LIFT["block"]]["H"] + P.LIFT["spacer"] + P.UPRIGHT["t"]
    else:
        yu1 = (D["beam_face"] + D["beam_back"]) / 2 + P.UPRIGHT["depth"] / 2      # faccia posteriore della spalla destra
    # colonna scatolata 60 × 60 × 4 sulla faccia posteriore della spalla destra, fino all'asse Y del trasferitore
    zt = top + 170.0
    z_fl = -P.LADDER["cross_drop"] + SD.ICD_UPRIGHT["flange_t"]      # sopra la flangia ICD della spalla
    out["mag_column"] = box(ux1 - 60, ux1, yu1, yu1 + 60, z_fl, zt).cut(box(ux1 - 56, ux1 - 4, yu1 + 4, yu1 + 56, z_fl + 4, zt - 4))
    # magazine: 2 posti su una navetta lungo X (passo 130); il posto scelto va a x = STORE_POSE, l'altro a +130
    pitch = 130.0
    zf = top - 15.0                            # forcella sotto il receiver (coupling a TRANSFER_TOP)
    yb = sy + hd["D"] / 2                       # fondo della forcella (lato +y); la testa esce verso −y
    out["mag_shuttle_rail"] = box(sx - 70, sx + pitch + 70, yb + 5, yb + 17, zf - 60, zf - 48)
    out["mag_shuttle_plate"] = box(sx - 60, sx + pitch + 60, yb - 5, yb + 5, zf - 60, zf)
    out["mag_arm"] = box(ux1 - 60, ux1, yu1 + 60, yb + 17, zf - 60, zf - 40)
    for k in range(2):
        x = sx + k * pitch
        out[f"mag_fork_{k}"] = box(x - 58, x + 58, sy - 30, yb - 5, zf - 10, zf).cut(box(x - 49, x + 49, sy - 31, yb - 15, zf - 11, zf + 1))
        out[f"mag_sensor_{k}"] = box(x - 6, x + 6, yb - 15, yb - 5, zf - 22, zf - 10)
    out["mag_motor"] = box(sx + pitch + 70, sx + pitch + 130, yb - 20, yb + 36, zf - 76, zf - 20)
    # trasferitore: asse Y (trave 60 × 100 sp. 4 da y −190 a y 470) sopra la colonna, carro e albero Z sul lato +x,
    # braccio X che prende il receiver dal lato +x: sopra la trave a TRANSFER_TOP, giù davanti, −X fino al dock, +Y
    xt = sx + hd["W"] / 2 + 40.0             # asse Y del trasferitore oltre la testa nel magazine
    yt0, yt1 = P.DOCK_APPROACH_Y - 40.0, sy + 100.0
    out["xfer_y_beam"] = box(xt, xt + 60, yt0, yt1, zt, zt + 100).cut(box(xt + 4, xt + 56, yt0 - 1, yt1 + 1, zt + 4, zt + 96))
    out["xfer_y_bracket"] = box(ux1 - 60, xt + 60, yu1, yu1 + 60, zt - 12, zt)
    out["xfer_y_rail"] = box(xt + 15, xt + 45, yt0 + 10, yt1 - 10, zt - 18, zt - 12)
    out["xfer_y_motor"] = box(xt + 2, xt + 58, yt1, yt1 + 90, zt + 22, zt + 78)
    out["xfer_z_carriage"] = box(xt, xt + 60, sy - 60, sy + 60, zt - 60, zt - 18)
    out["xfer_z_mast"] = box(xt + 10, xt + 50, sy - 30, sy + 30, D["coupling_top"] - 60, zt - 60)
    out["xfer_x_arm"] = box(sx + hd["W"] / 2 + 2, xt + 10, sy - 20, sy + 20, top - 40, top - 20)
    out["xfer_gripper"] = box(sx + hd["W"] / 2 - 8, sx + hd["W"] / 2 + 2, sy - 40, sy + 40, top - 40, top - 5)
    # camma di sgancio 3:1 del dock (D016): sul braccio, dove Z porta il rullo della leva della master a X 440
    out["dock_cam"] = box(sx + 80, sx + 110, sy - 20, sy + 20, top + 90, top + 110)
    return out


# ---------------------------------------------------------------- cabina
def cabin():
    """Telaio 30 × 30, pannelli PC, porta, vasca trucioli, aspirazione Ø100; piedi propri, aggancio al basamento.
    Ingombro dalla macchina (report dell'assieme) più magazine, con 60 mm di luce per lato."""
    import json
    import pathlib
    rep_ = pathlib.Path(__file__).resolve().parents[2] / "cad" / P.FILE_PREFIX / "report.json"
    env = json.loads(rep_.read_text())["envelope_mm"] if rep_.exists() else [-155.0, 702.0, -350.0, 447.0, -68.0, 815.0]
    M = P.MAGAZINE
    x0, x1 = min(env[0], M["x"][0]) - 75.0, max(env[1], M["x"][1]) + 60.0
    y0, y1 = env[2] - 80.0, max(env[3], M["y"][1]) + 80.0
    z0 = -P.LADDER["H"] - 8.0 - 3.0 - 30.0 - P.LADDER.get("bottom_plate", 0.0)   # vasca trucioli (3 mm) sotto i piedi (pad 8 mm)
    z1 = max(env[5], M["z"][1]) + 120.0
    p = 30.0
    out = {}
    edges = []
    for x in (x0, x1 - p):
        for y in (y0, y1 - p):
            edges.append(box(x, x + p, y, y + p, z0, z1))
    for z in (z0, z1 - p):
        for y in (y0, y1 - p):
            edges.append(box(x0, x1, y, y + p, z, z + p))
        for x in (x0, x1 - p):
            edges.append(box(x, x + p, y0, y1, z, z + p))
    for x in (x0 + 330, x1 - 330 - p):             # montanti della porta frontale
        edges.append(box(x, x + p, y0, y0 + p, z0, z1))
    out["cab_frame"] = fused(edges)
    t = 4.0
    panels = [box(x0 - t, x0, y0, y1, z0 + p, z1), box(x1, x1 + t, y0, y1, z0 + p, z1), box(x0, x1, y1, y1 + t, z0 + p, z1),
              box(x0, x1, y0, y1, z1, z1 + t).cut(cyl("z", z1 - 1, z1 + t + 1, x1 - 200, y1 - 160, 50.0))]
    out["cab_panels"] = fused(panels)
    out["cab_door"] = box(x0 + 330 + p, x1 - 330 - p, y0 - t - 2, y0 - 2, z0 + 120, z1 - 40)
    out["cab_side_fronts"] = fused([box(x0, x0 + 330, y0 - t, y0, z0 + p, z1), box(x1 - 330, x1, y0 - t, y0, z0 + p, z1)])
    out["cab_chip_tray"] = box(x0 + p, x1 - p, y0 + p, y1 - p, z0 + p, z0 + p + 3).cut(box(x0 + p + 3, x1 - p - 3, y0 + p + 3, y1 - p - 3, z0 + p + 2, z0 + p + 4))
    out["cab_extraction"] = cyl("z", z1 + t, z1 + t + 80, x1 - 200, y1 - 160, 50.0).cut(cyl("z", z1, z1 + t + 81, x1 - 200, y1 - 160, 47.0))
    out["cab_interlock"] = box(x1 - 330 - p - 20, x1 - 330 - p, y0 - 26, y0 - 6, z0 + 500, z0 + 560)
    for (x, y) in ((x0 + 15, y0 + 15), (x1 - 15, y0 + 15), (x0 + 15, y1 - 15), (x1 - 15, y1 - 15)):
        out[f"cab_foot_{int(x)}_{int(y)}"] = cyl("z", z0 - 20, z0, x, y, 20.0)
    # aggancio al basamento (mai al ponte): 2 staffe dal telaio cabina ai longheroni, lato fronte
    for xr in (P.TABLE["W"] / 2 - P.Y_AXIS["rail_spacing"] / 2, P.TABLE["W"] / 2 + P.Y_AXIS["rail_spacing"] / 2):
        out[f"cab_link_{int(xr)}"] = box(xr - 15, xr + 15, y0 + p, P.LADDER["long_y"][0], -P.LADDER["H"] + 20.0, -P.LADDER["H"] + 30.0)
    return out


ITEMS = [  # (bom, titolo, nota, funzione, densità per nome)
    ("RS", "Rialzi spalle", "Dettaglio: ICD v4 §5 sopra e sotto (2 spine Ø10 H7 + 4 M8 su 120 × 60); fondo filettato, cielo passante con finestra d'accesso.",
     lambda: {"riser_L": riser("L"), "riser_R": riser("R")}),
    ("MC-TD-006", "Magazine 2 posti + trasferitore", "Layout, non fabbricazione: colonna sulla spalla destra, navetta a 2 posti (passo 130), "
     "asse Y del trasferitore sopra la colonna, carro Z, braccio X e forcella fino al dock a X 440; camma di sgancio 3:1 (D016). Guide e motori TARGET.",
     magazine),
    ("MC-ENC-001", "Cabina", "Telaio 30 × 30 con piedi propri, agganciato al basamento e mai al ponte (D025); pannelli PC 4 mm, porta con interlock, "
     "vasca trucioli sotto i piedi della macchina, aspirazione Ø100; racchiude anche magazine e trasferitore.", cabin),
]


def density(name):
    if name == "cab_frame":                    # profilo 30 × 30 a cava: ~0,85 kg/m contro 2,43 del pieno
        return AL_RHO * 0.85 / 2.43
    if name.startswith("cab_panels") or name.startswith("cab_door") or name.startswith("cab_side"):
        return PC_RHO
    if name.startswith(("cab_foot", "xfer_y_rail", "mag_shuttle_rail")):
        return STEEL_RHO
    return AL_RHO


def items():
    """Accessori della base scelta (P.ACCESSORIES): codici BOM della base."""
    out = []
    for bom, title, note, fn in ITEMS:
        for code in P.ACCESSORIES:
            if (bom == "RS" and code.endswith("RS-001")) or code == bom or (bom == "MC-ENC-001" and code.endswith("ENC-001")):
                t = f"{title} +{P.RISER_H:g} mm" if bom == "RS" else title
                out.append((code, t, note, fn))
    return out


def export(out_dir):
    import render_views as R
    from PIL import Image
    R.VIEWS.setdefault("iso_back", ((1.0, -1.3, -0.9), (0, 0, 1)))
    rows = []
    for bom, title, note, fn in items():
        solids = fn()
        asm = cq.Assembly(name=bom)
        for n, s in solids.items():
            asm.add(cq.Workplane().add(s), name=n, color=cq.Color(0.62, 0.66, 0.72, 0.4 if n.startswith(("cab_panels", "cab_door", "cab_side")) else 1.0))
        f = out_dir / f"{bom}.step"
        asm.save(str(f))
        kg = sum(s.Volume() * density(n) for n, s in solids.items())
        print(bom, "massa", round(kg, 2), flush=True)
        comp = cq.Compound.makeCompound(list(solids.values()))
        b = comp.BoundingBox()
        parts = {n: dict(shape=s, kind="volume" if n.startswith(("cab_panels", "cab_door", "cab_side")) else "custom", color="gray") for n, s in solids.items()}
        ims = [R.render(parts, v, size=300) for v in ("iso", "iso_back", "top")]
        w, h = sum(i.width for i in ims) + 40, max(i.height for i in ims)
        img = Image.new("RGB", (w, h), (255, 255, 255))
        x = 0
        for i in ims:
            img.paste(i, (x, (h - i.height) // 2))
            x += i.width + 20
        img.save(out_dir / "views" / f"{bom}.png", optimize=True)
        rel = f"cad/{P.FILE_PREFIX}/parts"
        rows.append(dict(bom=bom, title=title, note=note, part=bom, file=f"{rel}/{bom}.step",
                         view=f"{rel}/views/{bom}.png", kg=None if bom == "MC-TD-006" else round(kg, 2),
                         size_mm=[round(b.xlen, 0), round(b.ylen, 0), round(b.zlen, 0)], solids=sorted(solids)))
        print(bom, title, rows[-1]["size_mm"], rows[-1]["kg"], "kg", flush=True)
    return rows
