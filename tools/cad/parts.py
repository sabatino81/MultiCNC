"""Modelli parametrici MultiCNC dei componenti commerciali (CadQuery).

Geometria semplificata a quote reali: serve per layout, ingombri e CAD di
assieme, non sostituisce il modello del produttore per il disegno di dettaglio.

Fonti quote:
- pattini MGN12H, MGN15H, HGH15CA, HGH20CA: schede HIWIN su hiwin.de (2026-09-24);
- rotaie MGN/HGR: quote tipiche catalogo HIWIN (larghezza, altezza, passo fori), da verificare;
- viti SFU e chiocciole: quote tipiche SFU, da verificare con il fornitore scelto;
- motori NEMA17/23 closed-loop: flangia standard NEMA, lunghezze tipiche con encoder.
"""
import cadquery as cq

# ---------------------------------------------------------------- guide lineari
# rotaia: larghezza WR, altezza HR, passo P, foro passante d, lamatura D x h
RAILS = {
    "MGN12": dict(WR=12, HR=8, P=25, d=3.5, D=6.0, h=4.5),
    "MGN15": dict(WR=15, HR=10, P=40, d=3.5, D=6.0, h=5.0),
    "HGR15": dict(WR=15, HR=15, P=60, d=4.5, D=7.5, h=5.3),
    "HGR20": dict(WR=20, HR=17.5, P=60, d=6.0, D=9.5, h=8.5),
}
# pattino: altezza totale H (da base rotaia), luce H1, larghezza W, lunghezza L,
# interasse fori B (trasversale) x C (longitudinale), filetto M
BLOCKS = {
    "MGN12H": dict(rail="MGN12", H=13, H1=3, W=27, L=45.4, B=20, C=20, M=3),
    "MGN15H": dict(rail="MGN15", H=16, H1=4, W=32, L=58.8, B=25, C=25, M=3),
    "HGH15CA": dict(rail="HGR15", H=28, H1=4.3, W=34, L=61.4, B=26, C=26, M=4),
    "HGH20CA": dict(rail="HGR20", H=30, H1=4.6, W=44, L=77.5, B=32, C=36, M=5),
}


def rail(name, length):
    r = RAILS[name]
    body = cq.Workplane("XY").box(length, r["WR"], r["HR"], centered=(False, True, False))
    n = int((length - 20) // r["P"]) + 1
    first = (length - (n - 1) * r["P"]) / 2
    pts = [(first + i * r["P"], 0) for i in range(n)]
    return (body.faces(">Z").workplane().pushPoints([(x - length / 2, y) for x, y in pts])
            .cboreHole(r["d"], r["D"], r["h"]))


def block(name):
    b = BLOCKS[name]
    r = RAILS[b["rail"]]
    body_h = b["H"] - b["H1"]
    body = (cq.Workplane("XY").workplane(offset=b["H1"])
            .box(b["L"], b["W"], body_h, centered=(True, True, False)))
    channel_h = r["HR"] - b["H1"] + 0.5
    channel = (cq.Workplane("XY").workplane(offset=b["H1"])
               .box(b["L"] + 2, r["WR"] + 0.6, channel_h, centered=(True, True, False)))
    body = body.cut(channel)
    holes = [(sx * b["C"] / 2, sy * b["B"] / 2) for sx in (-1, 1) for sy in (-1, 1)]
    return body.faces(">Z").workplane().pushPoints(holes).hole(b["M"] * 0.85, depth=b["M"] * 1.5)


def rail_with_blocks(rail_name, block_name, length, n_blocks=2, spacing=None):
    asm = rail(rail_name, length)
    spacing = spacing or length / (n_blocks + 1)
    for i in range(n_blocks):
        x = length / 2 + (i - (n_blocks - 1) / 2) * spacing
        asm = asm.union(block(block_name).translate((x, 0, 0)))
    return asm


# ---------------------------------------------------------------- viti a ricircolo
# d vite, nut: diametro D, flangia A x spessore B, lunghezza L, PCD fori, n fori, foro
SCREWS = {
    "SFU1204": dict(d=12, D=22, A=42, B=8, L=35, pcd=32, holes=6, hole=4.5),
    "SFU1605": dict(d=16, D=28, A=48, B=10, L=42, pcd=38, holes=6, hole=5.5),
}


def ballscrew(name, length):
    s = SCREWS[name]
    shaft = cq.Workplane("YZ").circle(s["d"] / 2).extrude(length)
    ends = (cq.Workplane("YZ").circle(s["d"] / 2 - 2).extrude(-15)
            .union(cq.Workplane("YZ").workplane(offset=length).circle(s["d"] / 2 - 2).extrude(12)))
    x0 = length / 2 - s["L"] / 2
    nut = cq.Workplane("YZ").workplane(offset=x0).circle(s["D"] / 2).extrude(s["L"])
    flange = (cq.Workplane("YZ").workplane(offset=x0).circle(s["A"] / 2).extrude(s["B"])
              .faces("<X").workplane().polarArray(s["pcd"] / 2, 0, 360, s["holes"])
              .hole(s["hole"]))
    return shaft.union(ends).union(nut).union(flange)


# ---------------------------------------------------------------- motori NEMA
MOTORS = {
    #              lato  corpo  encoder  pilota x h   interasse fori  foro  albero d x l
    "NEMA17_CL":   (42.3, 48,   21,      22, 2.0,     31.0,           3.4,  5, 24),
    "NEMA23_CL_2NM": (56.4, 76, 21,      38.1, 1.6,   47.14,          5.1,  8, 21),
    "NEMA23_CL_3NM": (56.4, 112, 21,     38.1, 1.6,   47.14,          5.1,  8, 21),
}


def motor(name):
    side, body, enc, pilot, ph, hs, hd, sd, sl = MOTORS[name]
    m = cq.Workplane("XY").box(side, side, body, centered=(True, True, False)).edges("|Z").chamfer(side * 0.06)
    m = m.faces("<Z").workplane().rect(hs, hs, forConstruction=True).vertices().hole(hd, depth=6)
    m = m.union(cq.Workplane("XY").workplane(offset=body).rect(side * 0.9, side * 0.9).extrude(enc))
    m = m.union(cq.Workplane("XY").circle(pilot / 2).extrude(-ph))
    m = m.union(cq.Workplane("XY").workplane(offset=-ph).circle(sd / 2).extrude(-sl))
    return m
