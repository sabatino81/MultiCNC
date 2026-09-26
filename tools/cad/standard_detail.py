#!/usr/bin/env python3
"""Base Standard · CAD di dettaglio dei pezzi custom (mule v3 → pezzi fabbricabili).

Il mule (standard_assembly.py) posa i pezzi custom come volumi pieni. Qui ogni pezzo riceve le lavorazioni che lo
collegano ai componenti vicini, ricavate dalle posizioni reali dei componenti commerciali nella stessa build:
- fori filettati delle rotaie (HGR15 M4 passo 60, MGN15 M3 passo 40) sulle superfici che le portano;
- fori passanti lamati dei pattini (HGH15CA M4 26 × 26, MGN15H M3 25 × 25) sul pezzo che si muove;
- fori dei supporti BK/BF (2 × M5 a 46 mm), delle flange delle chiocciole (SFU1605 6 × M5 su Ø38, SFU1204 6 × M4 su
  Ø32) e dei motori NEMA23 (4 × Ø5,5 su 47,14 + centraggio Ø38,1);
- interfaccia spalla ICD v4 §5 (2 spine Ø10 H7 a 100 mm + 4 M8 su 120 × 60) sotto e sopra le spalle;
- ToolDock: sedi dei 3 paia di rulli sulla master e delle 3 sfere Ø10 sul receiver (Ø80 a 120°), pull-stud, porte
  aria Ø6 e fluido 2 × Ø4, sedi dei connettori ibrido e dati, clamp a sfere con pacco molle e leva di sgancio 3:1.
Aggiunge i pezzi che nel mule mancavano (piastre ponte dei BK/BF Z, piede del telaio, cartuccia del clamp, leva) e
compila la tabella della viteria. Le quote sono MULE / TARGET: rilette sulle schede dei fornitori prima dell'ordine.

Non si chiama da solo: standard_assembly.build() lo applica se standard_assembly.DETAIL è vero (default). Le FEA
(tools/fea) lavorano sui volumi pieni e lo spengono.
"""
import math
import pathlib
import sys

import cadquery as cq

import parts
import standard_params as P

_CALC = str(pathlib.Path(__file__).resolve().parents[1] / "calc")   # compliance_d028: raggio del coupling
if _CALC not in sys.path:
    sys.path.insert(0, _CALC)

AL, STEEL, VOL = "custom", "commercial", "volume"
TAP = {"M3": 2.5, "M4": 3.3, "M5": 4.2, "M6": 5.0, "M8": 6.8, "M10": 8.5}          # foro di maschiatura
CLR = {"M3": 3.4, "M4": 4.5, "M5": 5.5, "M6": 6.6, "M8": 9.0, "M10": 11.0}         # passante medio ISO 273
CB = {"M3": (6.5, 3.5), "M4": (8.0, 4.5), "M5": (10.0, 5.5), "M6": (11.0, 6.5), "M8": (14.5, 8.5)}  # lamatura ISO 4762
SUPPORT_HOLE_PITCH = {"BK12": 46.0, "BF12": 46.0, "BK10": 46.0, "BF10": 46.0}      # 2 fori M5 sulla larghezza (catalogo tipico)
NEMA23_PITCH, NEMA23_PILOT = 47.14, 38.1
ICD_UPRIGHT = dict(pins=100.0, pin_d=10.0, bolt="M8", rect=(60.0, 120.0), flange_t=16.0, flange=(80.0, 140.0))  # §5
ROLLER = dict(d=8.0, L=12.0, gap=5.0)         # coppia di rulli (spine rettificate DIN 6325) per sfera Ø10
BALL_D = 10.0
PULL_STUD = dict(thread="M10", shank_d=12.0, neck_d=9.0, head_d=15.0, head_h=6.0, L=30.0)   # comune a tutte le teste
CONNECTORS = {  # sedi dei connettori a innesto cieco (inviluppi, fornitore da qualificare): (x, y) centro, w × d × h
    "hybrid": dict(c=(-31.0, 38.0), w=26.0, d=16.0, h=22.0, bom="MC-TD-004"),
    "data": dict(c=(31.0, 38.0), w=22.0, d=16.0, h=22.0, bom="MC-TD-007"),
}
PORTS = [("air", (0.0, -36.0), 6.0), ("fluid_in", (-11.0, -34.0), 4.0), ("fluid_out", (11.0, -34.0), 4.0)]


# ---------------------------------------------------------------- primitive
def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cyl(axis, a0, a1, c1, c2, r):
    """Cilindro lungo 'x', 'y' o 'z' da a0 ad a1 (a0 < a1 o no); (c1, c2) = le altre due coordinate in ordine xyz."""
    a0, a1 = min(a0, a1), max(a0, a1)
    d = {"x": cq.Vector(1, 0, 0), "y": cq.Vector(0, 1, 0), "z": cq.Vector(0, 0, 1)}[axis]
    p = {"x": cq.Vector(a0, c1, c2), "y": cq.Vector(c1, a0, c2), "z": cq.Vector(c1, c2, a0)}[axis]
    return cq.Solid.makeCylinder(r, a1 - a0, p, d)


def compound(solids):
    return cq.Compound.makeCompound(solids)


class Detail:
    """Raccoglie tagli e aggiunte per pezzo e la viteria; applica tutto in una volta."""

    def __init__(self, a):
        self.a = a
        self.cuts, self.adds, self.hw, self.notes = {}, {}, {}, []

    def bb(self, n):
        return self.a.parts[n]["shape"].BoundingBox()

    def cut(self, part, solid):
        self.cuts.setdefault(part, []).append(solid)

    def add(self, part, solid):
        self.adds.setdefault(part, []).append(solid)

    def screw(self, size, length, std="ISO 4762", qty=1, where=""):
        k = (std, f"{size}×{length:g}" if length else size, where)
        self.hw[k] = self.hw.get(k, 0) + qty

    def hole(self, part, axis, face, into, c1, c2, kind, size, depth, cbore=False):
        """Foro sulla faccia 'face' (coordinata lungo axis) che entra nel pezzo nel verso into (+1/−1).
        kind: 'tap' (maschiato, profondità = filetto), 'clr' (passante), 'pin' (spina H7, size = diametro)."""
        d = TAP[size] if kind == "tap" else (CLR[size] if kind == "clr" else float(size))
        self.cut(part, cyl(axis, face - into * 0.5, face + into * depth, c1, c2, d / 2))
        if cbore and kind == "clr":
            D, h = CB[size]
            self.cut(part, cyl(axis, face - into * 0.5, face + into * h, c1, c2, D / 2))

    def apply(self):
        for n in set(self.cuts) | set(self.adds):
            p = self.a.parts[n]
            s = p["shape"]
            if n in self.adds:
                s = s.fuse(*self.adds[n]).clean()
            if n in self.cuts:                     # utensili sovrapposti: un compound per gruppo di tagli disgiunti
                tools = self.cuts[n]
                for i in range(0, len(tools), 1 if len(tools) < 40 else 8):
                    s = s.cut(compound(tools[i:i + (1 if len(tools) < 40 else 8)]))
            p["shape"] = s


def rail_holes(name, length):
    r = parts.RAILS[name]
    n = int((length - 20) // r["P"]) + 1
    first = (length - (n - 1) * r["P"]) / 2
    return [first + i * r["P"] for i in range(n)]


# ---------------------------------------------------------------- interfacce guide
def rails(dt):
    """Fori filettati delle rotaie sulle superfici che le portano (viti dalla rotaia)."""
    a = dt.a
    xa, ya, za = P.X_AXIS, P.Y_AXIS, P.Z_AXIS
    for n in ("x_rail_top", "x_rail_bot"):
        b = dt.bb(n)
        zc = (b.zmin + b.zmax) / 2
        for s in rail_holes(xa["rail"], xa["rail_len"]):
            dt.hole("beam", "y", b.ymax, +1, b.xmin + s, zc, "tap", "M4", 10)
        dt.screw("M4", 20, where="rotaie X → trave", qty=len(rail_holes(xa["rail"], xa["rail_len"])))
    for n, host in (("y_rail_L", "frame_longeron_L"), ("y_rail_R", "frame_longeron_R")):
        b = dt.bb(n)
        xc = (b.xmin + b.xmax) / 2
        for s in rail_holes(ya["rail"], ya["rail_len"]):
            dt.hole(host, "z", b.zmin, -1, xc, b.ymin + s, "tap", "M3", 6)
        dt.screw("M3", 12, where="rotaie Y → longheroni (filetto nel pad di 8 mm)", qty=len(rail_holes(ya["rail"], ya["rail_len"])))
    for n in ("z_rail_0", "z_rail_1"):
        b = dt.bb(n)
        xc = (b.xmin + b.xmax) / 2
        for s in rail_holes(za["rail"], za["rail_len"]):
            dt.hole("x_carriage", "y", b.ymax, +1, xc, b.zmin + s, "tap", "M4", 10)
        dt.screw("M4", 20, where="rotaie Z → carrello X", qty=len(rail_holes(za["rail"], za["rail_len"])))
    # rotaie Y: pad lavorati di 8 mm sotto la rotaia (parete del tubo 4 mm troppo corta per l'M3)
    for n, host in (("y_rail_L", "frame_longeron_L"), ("y_rail_R", "frame_longeron_R")):
        b = dt.bb(n)
        xc = (b.xmin + b.xmax) / 2
        dt.add(host, box(xc - 12, xc + 12, b.ymin, b.ymax, -P.LADDER["wall"] - 4.0, -P.LADDER["wall"] + 0.01))


def blocks(dt):
    """Pattini: viti passanti lamate dal pezzo mobile nei fori filettati del pattino."""
    a = dt.a
    for prefix, host, axis, bset in (("x_block", "x_carriage", "y", P.X_AXIS), ("y_block", "table", "z", P.Y_AXIS),
                                     ("z_block", "z_slide", "y", P.Z_AXIS)):
        kb = parts.BLOCKS[bset["block"]]
        size = f"M{kb['M']}"
        names = [n for n in a.parts if n.startswith(prefix)]
        for n in names:
            b = dt.bb(n)
            cx, cy, cz = (b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, (b.zmin + b.zmax) / 2
            if prefix == "x_block":           # faccia del pattino y = ymin (108) → carrello da cb verso cf, lamatura su cf
                cf, cb_ = dt.bb(host).ymin, b.ymin
                t = cb_ - P.derived()["carriage_front"]
                for dx in (-kb["C"] / 2, kb["C"] / 2):
                    for dz in (-kb["B"] / 2, kb["B"] / 2):
                        dt.hole(host, "y", P.derived()["carriage_front"], +1, cx + dx, cz + dz, "clr", size, t + 1, cbore=True)
            elif prefix == "y_block":         # faccia z = zmax (16) → tavola, viti dall'alto, lamatura sul piano
                top = P.derived()["table_top"]
                for dx in (-kb["B"] / 2, kb["B"] / 2):
                    for dy in (-kb["C"] / 2, kb["C"] / 2):
                        dt.hole(host, "z", top, -1, cx + dx, cy + dy, "clr", size, P.TABLE["T"] + 1, cbore=True)
            else:                             # faccia y = ymin (65) → slitta da slide_back, lamatura su slide_front
                front = P.derived()["slide_front"]
                for dx in (-kb["B"] / 2, kb["B"] / 2):
                    for dz in (-kb["C"] / 2, kb["C"] / 2):
                        x = cx + dx
                        dt.hole(host, "y", front, +1, x, cz + dz, "clr", size, P.PLATE["slide_t"] + 1, cbore=True)
                        # sotto le ali anteriori: foro d'accesso Ø9 attraverso l'ala per chiave e vite
                        if abs(x - a_X(dt)) > P.PLATE["slide_w"] / 2 - P.SLIDE_FLANGE["t"] - CB[size][0] / 2:
                            dt.cut(host, cyl("y", front - P.SLIDE_FLANGE["depth"] - 1, front + 0.1, x, cz + dz, 4.5))
            dt.screw(size, {"x_block": 16, "y_block": 12, "z_block": 16}[prefix], qty=4, where=f"pattini {prefix[0].upper()}")
    dt.notes.append("Carrello X: le teste delle viti dei pattini X alti stanno sotto le guide Z (lamature profonde 4,5 mm): "
                    "si montano prima i pattini X, poi le guide Z.")
    dt.notes.append("Slitta Z: le viti esterne dei pattini Z stanno dietro le ali anteriori; fori d'accesso Ø9 attraverso le ali.")


def a_X(dt):
    b = dt.bb("z_slide")
    return (b.xmin + b.xmax) / 2


# ---------------------------------------------------------------- supporti, chiocciole, motori
def supports(dt):
    a = dt.a
    D = P.derived()
    # X: BK/BF sulla faccia +y (y = 160) degli spessori, viti M5 negli spessori e nella parete del canale trave
    for n in ("x_bf", "x_bk"):
        b = dt.bb(n)
        k = "BF12" if n == "x_bf" else "BK12"
        xc, zc = (b.xmin + b.xmax) / 2, (b.zmin + b.zmax) / 2
        for dz in (-SUPPORT_HOLE_PITCH[k] / 2, SUPPORT_HOLE_PITCH[k] / 2):
            dt.hole("x_pads", "y", b.ymax, +1, xc, zc + dz, "clr", "M5", P.X_SCREW_PAD + 1)
            dt.hole("beam", "y", b.ymax + P.X_SCREW_PAD, +1, xc, zc + dz, "tap", "M5", 6.0)
            dt.cut(n, cyl("y", b.ymin - 1, b.ymax + 1, xc, zc + dz, CLR["M5"] / 2))
        dt.screw("M5", 40, qty=2, where=f"{k} X → spessori → trave")
    # Y: BK/BF sui pad delle traverse (z = −48), viti dall'alto
    for n, host in (("y_bf", "frame_cross_bf"), ("y_bk", "frame_cross_rear")):
        b = dt.bb(n)
        k = "BF12" if n == "y_bf" else "BK12"
        xc, yc = (b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2
        for dx in (-SUPPORT_HOLE_PITCH[k] / 2, SUPPORT_HOLE_PITCH[k] / 2):
            dt.hole(host, "z", b.zmin, -1, xc + dx, yc, "tap", "M5", 10)
            dt.cut(n, cyl("z", b.zmin - 1, b.zmax + 1, xc + dx, yc, CLR["M5"] / 2))
        dt.screw("M5", 45, qty=2, where=f"{k} Y → traversa")
    # Z: nel mule i supporti galleggiano nella fessura del carrello. Si girano con la base verso +y su due piastre
    # ponte (10 mm) avvitate alla faccia posteriore del carrello, a cavallo della fessura (MC-BRK-001).
    zk = parts.ENDS[P.Z_AXIS["screw"]]
    y_ax = D["slide_back"] + P.SUPPORT_GAP_Z + P.SUPPORTS[P.Z_AXIS["bk"]]["h"]
    cb_ = D["carriage_back"]
    for n, k in (("z_bf", P.Z_AXIS["bf"]), ("z_bk", P.Z_AXIS["bk"])):
        q = P.SUPPORTS[k]
        b = dt.bb(n)
        xc = (b.xmin + b.xmax) / 2
        base = y_ax + q["h"]                          # faccia di montaggio verso +y
        body = box(xc - q["W"] / 2, xc + q["W"] / 2, base - q["H"], base, b.zmin, b.zmax).cut(
            cyl("z", b.zmin - 1, b.zmax + 1, xc, y_ax, q["bore"] / 2 + 0.1))
        for dx in (-SUPPORT_HOLE_PITCH[k] / 2, SUPPORT_HOLE_PITCH[k] / 2):
            body = body.cut(cyl("y", base - q["H"] - 1, base + 1, xc + dx, (b.zmin + b.zmax) / 2, CLR["M5"] / 2))
        a.parts[n]["shape"] = body
        bridge = f"{n}_bridge"
        pw = P.PLATE["tower_w"] if n == "z_bk" else P.PLATE["carriage_w"] - 40
        z0, z1 = (b.zmin - 12, b.zmax) if n == "z_bf" else (b.zmin, b.zmax + 12)   # lato piastrina: niente sporgenza (gioco ≥ 8 mm)
        br = box(xc - pw / 2, xc + pw / 2, cb_, base + 10 if base > cb_ else cb_ + 10, z0, z1)
        br = br.cut(box(xc - q["W"] / 2 - 1, xc + q["W"] / 2 + 1, cb_ - 1, base, z0 - 1, z1 + 1)) if base > cb_ + 0.1 else br
        br = br.cut(cyl("y", cb_ - 1, base + 11, xc, y_ax, q["bore"] / 2 + 4))
        a.add(bridge, cq.Workplane().add(br), "XCAR", AL, "MC-BRK-001", "gray")
        for dx in (-SUPPORT_HOLE_PITCH[k] / 2, SUPPORT_HOLE_PITCH[k] / 2):
            dt.hole(bridge, "y", base, +1, xc + dx, (b.zmin + b.zmax) / 2, "tap", "M5", 10)
        for sx in (-1, 1):                            # ponte → carrello: 2 × M5 per lato fuori dalla fessura
            for zz in (z0 + 6, z1 - 6):
                xx = xc + sx * (pw / 2 - 7)
                dt.hole(bridge, "y", base + 10 if base > cb_ else cb_ + 10, -1, xx, zz, "clr", "M5", 30, cbore=True)
                dt.hole("x_carriage", "y", cb_, -1, xx, zz, "tap", "M5", 10)
        dt.screw("M5", 20, qty=2, where=f"{k} Z → piastra ponte")
        dt.screw("M5", 25, qty=4, where="piastra ponte Z → carrello")
    dt.notes.append("BK/BF Z girati con la base verso il retro e avvitati a due piastre ponte sul carrello (mancavano nel mule).")


def nuts(dt):
    """Flange delle chiocciole sulle staffe; staffe sul pezzo mobile."""
    a = dt.a
    D = P.derived()
    b = dt.bb("x_nut_bracket")                     # staffa X fino a y 159: la flangia Ø48 della chiocciola sta tutta sulla staffa
    dt.a.parts["x_nut_bracket"]["shape"] = dt.a.parts["x_nut_bracket"]["shape"].fuse(box(b.xmin, b.xmax, b.ymax - 0.01, b.ymax + 6.0, b.zmin, b.zmax)).clean()
    for nut, brk, host, axis, sname in (("x_nut", "x_nut_bracket", "x_carriage", "x", P.X_AXIS["screw"]),
                                        ("y_nut", "y_nut_bracket", "table", "y", P.Y_AXIS["screw"]),
                                        ("z_nut", "z_nut_tab", "z_slide", "z", P.Z_AXIS["screw"])):
        s = parts.SCREWS[sname]
        size = "M5" if s["hole"] > 5 else "M4"
        nb, bb_ = dt.bb(nut), dt.bb(brk)
        c = ((nb.xmin + nb.xmax) / 2, (nb.ymin + nb.ymax) / 2, (nb.zmin + nb.zmax) / 2)
        # faccia della staffa a contatto con la flangia
        lo, hi = {"x": (bb_.xmin, bb_.xmax), "y": (bb_.ymin, bb_.ymax), "z": (bb_.zmin, bb_.zmax)}[axis]
        nlo, nhi = {"x": (nb.xmin, nb.xmax), "y": (nb.ymin, nb.ymax), "z": (nb.zmin, nb.zmax)}[axis]
        face, into = (lo, +1) if abs(lo - nhi) < abs(hi - nlo) else (hi, -1)
        for k in range(s["holes"]):
            t = math.radians(30 + 60 * k)
            u, v = s["pcd"] / 2 * math.cos(t), s["pcd"] / 2 * math.sin(t)
            if axis == "x":
                c1, c2 = c[1] + u, c[2] + v
            elif axis == "y":
                c1, c2 = c[0] + u, c[2] + v
            else:
                c1, c2 = c[0] + u, c[1] + v
            dt.hole(brk, axis, face, into, c1, c2, "tap", size, (hi - lo) - 0.5)
        dt.screw(size, 16, qty=s["holes"], where=f"flangia chiocciola {sname} → staffa")
    # staffe → pezzo mobile
    b = dt.bb("x_nut_bracket")
    # staffa X: 2 × M5 dal fronte del carrello, passanti nella piastra, filettati nel bordo della staffa (un piede
    # sporgente passerebbe a 1 mm dal BK X a X max)
    xm = (b.xmin + b.xmax) / 2
    for zz in (b.zmin + 8, b.zmax - 8):
        dt.hole("x_carriage", "y", D["carriage_front"], +1, xm, zz, "clr", "M5", P.PLATE["carriage_t"] + 1, cbore=True)
        dt.hole("x_nut_bracket", "y", D["carriage_back"], +1, xm, zz, "tap", "M5", 12)
    dt.screw("M5", 25, qty=2, where="staffa chiocciola X → carrello (dal fronte)")
    b = dt.bb("y_nut_bracket")
    for dx in (-20.0, 20.0):
        dt.hole("y_nut_bracket", "z", b.zmax, -1, (b.xmin + b.xmax) / 2 + dx, (b.ymin + b.ymax) / 2, "tap", "M5", 10)
        dt.hole("table", "z", D["table_top"], -1, (b.xmin + b.xmax) / 2 + dx, (b.ymin + b.ymax) / 2, "clr", "M5", P.TABLE["T"] + 1, cbore=True)
    dt.screw("M5", 20, qty=2, where="staffa chiocciola Y → tavola (dall'alto)")
    b = dt.bb("z_nut_tab")
    xc = (b.xmin + b.xmax) / 2
    for dx in (-18.0, 18.0):                         # piastrina → faccia superiore della slitta (bordo 12 mm)
        dt.hole("z_nut_tab", "z", b.zmax, -1, xc + dx, (D["slide_front"] + D["slide_back"]) / 2, "clr", "M5", P.TAB_T + 1, cbore=True)
        dt.hole("z_slide", "z", b.zmin, -1, xc + dx, (D["slide_front"] + D["slide_back"]) / 2, "tap", "M5", 12)
    dt.screw("M5", 30, qty=2, where="piastrina chiocciola Z → slitta")


def motors(dt):
    a = dt.a
    D = P.derived()
    # X: la piastra motore diventa la testata destra della trave saldata (8 mm, dentro il canale della vite)
    b = dt.bb("x_motor_plate")
    plate = box(b.xmax - 8.0, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)
    a.parts["beam"]["shape"] = a.parts["beam"]["shape"].fuse(plate).clean()
    del a.parts["x_motor_plate"]
    # Y: piastra motore saldata sulla traversa di coda, 10 mm, sale fino a z 7 per i fori alti del NEMA23
    m = dt.bb("y_motor")
    c0, zc = (m.xmin + m.xmax) / 2, (m.zmin + m.zmax) / 2 + 0.0
    zc = -P.LADDER["H"] + P.LADDER["pad_t"] + P.SUPPORTS[P.Y_AXIS["bk"]]["h"]
    hb = dt.bb("frame_cross_end")
    dt.add("frame_cross_end", box(c0 - 35, c0 + 35, hb.ymax - 10, hb.ymax, hb.zmin + 5, 7.0))
    specs = (("x_motor", "beam", "x", (b.xmax - 8.0, b.xmax), ((b.ymin + b.ymax) / 2, (b.zmin + b.zmax) / 2)),
             ("y_motor", "frame_cross_end", "y", (hb.ymax - 10, hb.ymax), (c0, zc)),
             ("z_motor", "z_motor_bracket", "z", (dt.bb("z_motor_bracket").zmin, dt.bb("z_motor_bracket").zmax), None))
    for mot, host, axis, (lo, hi), cc in specs:
        mb = dt.bb(mot)
        if cc is None:
            cc = ((mb.xmin + mb.xmax) / 2, (mb.ymin + mb.ymax) / 2)
        c1, c2 = cc
        for su in (-1, 1):
            for sv in (-1, 1):
                dt.cut(host, cyl(axis, lo - 1, hi + 1, c1 + su * NEMA23_PITCH / 2, c2 + sv * NEMA23_PITCH / 2, 5.5 / 2))
        dt.cut(host, cyl(axis, lo - 1, hi + 1, c1, c2, NEMA23_PILOT / 2 + 0.02))
        dt.screw("M5", 20, qty=4, where=f"motore {axis.upper()} (con dado M5)")
    # staffa motore Z sul cielo della torre: 2 × M6 nel bordo della torre
    b = dt.bb("z_motor_bracket")
    xc = (b.xmin + b.xmax) / 2
    for dx in (-38.0, 38.0):
        dt.hole("z_motor_bracket", "z", b.zmax, -1, xc + dx, (D["carriage_front"] + D["carriage_back"]) / 2, "clr", "M6", 11, cbore=True)
        dt.hole("x_carriage", "z", b.zmin, -1, xc + dx, (D["carriage_front"] + D["carriage_back"]) / 2, "tap", "M6", 14)
    dt.screw("M6", 25, qty=2, where="staffa motore Z → torre carrello")
    dt.notes.append("Piastra motore X saldata come testata della trave (8 mm); piastra motore Y saldata sulla traversa di coda (10 mm, fino a z 7).")


# ---------------------------------------------------------------- telaio, spalle, trave
def frame(dt):
    """Telaio saldato TIG e poi lavorato (pad, sedi guide Y, facce spalle); piedi M10 regolabili."""
    a = dt.a
    L = P.LADDER
    for n in ("frame_longeron_L", "frame_longeron_R"):
        b = dt.bb(n)
        for y in (b.ymin + 30, b.ymax - 30):         # 4 piedi: pad 60 × 50 × 12 sotto i longheroni
            xc = (b.xmin + b.xmax) / 2
            pad = box(xc - 20, xc + 20, y - 30, y + 30, b.zmin - 12, b.zmin + 0.01)
            dt.add(n, pad)
            dt.cut(n, cyl("z", b.zmin - 13, b.zmin + L["wall"] + 1, xc, y, TAP["M10"] / 2))
        dt.screw("M10", 0, std="piede antivibrante M10", qty=2, where="piedi telaio")
    dt.notes.append("Telaio MC-BAS-001: un pezzo saldato (6 tubi + pad), distensionato e poi lavorato su pad, sedi guide Y e facce spalle.")


def uprights(dt):
    """Spalle con flange sotto e sopra al pattern ICD v4 §5; telaio e trave con fori corrispondenti."""
    a = dt.a
    I = ICD_UPRIGHT
    for side in ("L", "R"):
        n = f"upright_{side}"
        b = dt.bb(n)
        xc, yc = (b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2
        inward = 1 if side == "L" else -1
        fx0 = b.xmin if side == "L" else b.xmax - I["flange"][0]     # flangia verso l'interno macchina (solo in basso)
        fx1 = fx0 + I["flange"][0]
        fxc = (fx0 + fx1) / 2
        fy0, fy1 = yc - I["flange"][1] / 2, yc + I["flange"][1] / 2
        # sotto: interfaccia ICD v4 §5 con il basamento. Flangia 80 × 140 × 16 filettata M8; viti dal basso attraverso
        # la traversa posteriore, dentro boccole Ø20 a tutta altezza del tubo (distanziali saldati), spine Ø10 H7
        z0, z1, face = b.zmin, b.zmin + I["flange_t"], b.zmin
        dt.add(n, box(fx0, fx1, fy0, fy1, z0, z1))
        cr = dt.bb("frame_cross_rear")
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = fxc + sx * I["rect"][0] / 2, yc + sy * I["rect"][1] / 2
                dt.hole(n, "z", face, +1, x, y, "tap", I["bolt"], I["flange_t"] - 2)
                dt.add("frame_cross_rear", cyl("z", cr.zmin, face, x, y, 10.0))
                dt.cut("frame_cross_rear", cyl("z", cr.zmin - 1, face + 0.5, x, y, CLR['M8'] / 2))
        for sy in (-1, 1):
            y = yc + sy * I["pins"] / 2
            dt.hole(n, "z", face, +1, fxc, y, "pin", I["pin_d"], 12)
            dt.add("frame_cross_rear", cyl("z", face - 20, face, fxc, y, 10.0))
            dt.hole("frame_cross_rear", "z", face, -1, fxc, y, "pin", I["pin_d"], 14)
        dt.screw("M8", 80, qty=4, where=f"spalla {side} → basamento, dal basso attraverso la traversa (ICD §5)")
        dt.screw("Ø10 m6", 24, std="spina ISO 8734", qty=2, where=f"spalla {side} → basamento (ICD §5)")
        # sopra: giunto interno spalla ↔ trave dentro l'impronta della spalla e sotto la trave (cielo 16 mm, 2 × M8 + 2 spine Ø8)
        top = b.zmax
        dt.add(n, box(b.xmin, b.xmax, b.ymin, b.ymax, top - 16.0, top))
        bf_, bb_y = P.derived()["beam_face"], P.derived()["beam_back"]
        for y in (bf_ + 10, bb_y - 10):
            dt.hole(n, "z", top, -1, xc, y, "clr", "M8", 17)
            dt.hole("beam", "z", top, +1, xc, y, "tap", "M8", 16)
        for y in (bf_ + 30, bb_y - 30):
            dt.hole(n, "z", top, -1, xc, y, "pin", 8.0, 12)
            dt.hole("beam", "z", top, +1, xc, y, "pin", 8.0, 12)
        wx = b.xmax - P.UPRIGHT["wall"] if side == "L" else b.xmin      # parete verso l'interno macchina
        dt.cut(n, box(wx - 0.5, wx + P.UPRIGHT["wall"] + 0.5, bf_ + 2, bb_y - 2, top - 16 - 50, top - 16 - 5))
        dt.screw("M8", 40, qty=2, where=f"spalla {side} → trave (dalla finestra d'accesso della spalla)")
        dt.screw("Ø8 m6", 24, std="spina ISO 8734", qty=2, where=f"spalla {side} → trave")
    # la traversa posteriore deve portare la flangia (140 in y): si allarga di 12 mm verso il fronte
    b = dt.bb("frame_cross_rear")
    w_, y0 = P.LADDER["wall"], b.ymin - 12
    ext = [box(P.BEAM_X[0], P.BEAM_X[1], y0, y0 + w_, b.zmin, b.zmax), box(P.BEAM_X[0], P.BEAM_X[1], y0, b.ymin + 0.01, b.zmax - w_, b.zmax),
           box(P.BEAM_X[0], P.BEAM_X[1], y0, b.ymin + 0.01, b.zmin, b.zmin + w_)]
    for n in ("frame_longeron_L", "frame_longeron_R"):
        lb = dt.bb(n)
        ext = [e.cut(box(lb.xmin, lb.xmax, y0 - 1, b.ymin + 1, b.zmin - 1, b.zmax + 1)) for e in ext]
    xtc, pw = P.TABLE["W"] / 2, P.LADDER["pocket_w"]         # passaggio della vite e della chiocciola Y, come nel mule
    ext = [e.cut(box(xtc - pw / 2, xtc + pw / 2, y0 - 1, b.ymin + 1, b.zmin + w_, b.zmax + 1)) for e in ext]
    for e in ext:
        dt.add("frame_cross_rear", e)
    # trave: blocchi pieni d'estremità saldati sotto la trave (sede delle viti M8 e delle spine)
    Dd = P.derived()
    for side, (x0, x1) in (("L", (P.BEAM_X[0], P.BEAM_X[0] + I["flange"][0])), ("R", (P.BEAM_X[1] - I["flange"][0], P.BEAM_X[1]))):
        dt.add("beam", box(x0, x1, Dd["beam_face"], Dd["beam_back"], Dd["beam_bottom"], Dd["beam_bottom"] + 20))
    dt.notes.append("Trave MC-GAN-001: saldata (piatti 6 mm) con blocchi pieni d'estremità 80 × 80 × 20 per il giunto con le spalle; "
                    "traversa posteriore allargata di 12 mm verso il fronte per portare la flangia ICD §5 delle spalle. L'interfaccia ICD §5 "
                    "(2 spine Ø10 + 4 M8 su 120 × 60) è solo fra spalla e basamento, dove si impilano i rialzi: il giunto spalla ↔ trave "
                    "resta interno alla spalla (una flangia sopra urterebbe il carrello X in HOME).")


# ---------------------------------------------------------------- ToolDock
def tooldock(dt, X, cz):
    """Master: sedi rulli, clamp a sfere, leva di sgancio, sedi connettori e porte; receiver: sfere, pull-stud, porte."""
    a = dt.a
    import compliance_d028 as C
    R = C.COUPLING_R
    M = P.MASTER
    angles = (90.0, 210.0, 330.0)
    rt = P.SPINDLE["receiver_t"]
    for i, t in enumerate(angles):
        th = math.radians(t)
        bx, by = X + R * math.cos(th), R * math.sin(th)
        # master: tasca per la coppia di rulli radiali (asse dei rulli lungo il raggio), rulli Ø8 × 12 affiancati
        ux, uy = math.cos(th), math.sin(th)
        vx, vy = -uy, ux
        # sfera Ø10 con il centro sul piano del coupling, rulli Ø8 tangenti: centri a +4 mm e ±√(9² − 4²) di lato
        sep = math.sqrt((BALL_D / 2 + ROLLER["d"] / 2) ** 2 - (ROLLER["d"] / 2) ** 2)
        for s in (-1, 1):
            cx_, cy_ = bx + s * sep * vx, by + s * sep * vy
            pin = cq.Solid.makeCylinder(ROLLER["d"] / 2, ROLLER["L"], cq.Vector(cx_ - ux * ROLLER["L"] / 2, cy_ - uy * ROLLER["L"] / 2, cz + ROLLER["d"] / 2 + 0.02),
                                        cq.Vector(ux, uy, 0))
            dt.cut("tooldock_master", pin)
            a.add(f"td_roller_{i}{0 if s < 0 else 1}", cq.Workplane().add(pin), "ZSLIDE", STEEL, "MC-TD-001", "silver")
        # receiver: sede conica e sfera Ø10 (metà sporgente sopra il piano del coupling)
        dt.cut("head_receiver", cyl("z", cz - BALL_D / 2 - 0.5, cz + 0.1, bx, by, BALL_D / 2 + 0.02))
        dt.cut("tooldock_master", cq.Solid.makeSphere(BALL_D / 2 + 0.6, cq.Vector(bx, by, cz)))      # scarico sopra la sfera, fra i rulli
        ball = cq.Solid.makeSphere(BALL_D / 2 - 0.02, cq.Vector(bx, by, cz))
        a.add(f"td_ball_{i}", cq.Workplane().add(ball), "ZSLIDE", STEEL, "MC-TD-002", "silver")
    dt.screw("Ø8 × 12", 0, std="spina rettificata DIN 6325 (rullo)", qty=6, where="master ToolDock")
    dt.screw("Ø10 G10", 0, std="sfera 100Cr6", qty=3, where="receiver (incollata / piantata)")
    # pull-stud sul receiver (M10 nel receiver, testa dentro la master)
    ps = PULL_STUD
    stud = (cyl("z", cz - rt + 1, cz, X, 0, TAP["M10"] / 2)
            .fuse(cyl("z", cz, cz + ps["L"] - ps["head_h"] - 6, X, 0, ps["shank_d"] / 2))
            .fuse(cyl("z", cz + ps["L"] - ps["head_h"] - 6, cz + ps["L"] - ps["head_h"], X, 0, ps["neck_d"] / 2))
            .fuse(cyl("z", cz + ps["L"] - ps["head_h"], cz + ps["L"], X, 0, ps["head_d"] / 2)))
    a.add("td_pull_stud", cq.Workplane().add(stud), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    dt.hole("head_receiver", "z", cz, -1, X, 0, "tap", "M10", rt - 1)
    # clamp a sfere nella master: foro Ø36 nel fondo, cartuccia Ø50 che sale oltre il cielo della master
    top = cz + M["T"]
    dt.cut("tooldock_master", cyl("z", cz - 1, cz + M["wall"] + 0.5, X, 0, 17.5))
    dt.cut("tooldock_master", cyl("z", cz + M["wall"], top + 1, X, 0, 25.05))
    cart = cyl("z", cz + M["wall"], top, X, 0, 25.0).fuse(cyl("z", top, top + 44, X, 0, 20.0)).cut(cyl("z", cz + M["wall"] - 1, top + 45, X, 0, 17.0))
    flange = cyl("z", top, top + 6, X, 0, 32.0).cut(cyl("z", top - 1, top + 7, X, 0, 17.0))
    a.add("td_clamp_housing", cq.Workplane().add(cart.fuse(flange)), "ZSLIDE", AL, "MC-TD-003", "tomato")
    piston = cyl("z", cz + 10, cz + 28, X, 0, 16.5).cut(cyl("z", cz + 9, cz + 29, X, 0, ps["head_d"] / 2 + 3.2))
    a.add("td_clamp_piston", cq.Workplane().add(piston), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    springs = cyl("z", cz + 28, top + 38, X, 0, 16.0).cut(cyl("z", cz + 27, top + 39, X, 0, 8.2))
    a.add("td_clamp_springs", cq.Workplane().add(springs), "ZSLIDE", STEEL, "MC-TD-003", "gold")
    rod = cyl("z", cz + ps["L"] + 1, top + 60, X, 0, 4.0)
    a.add("td_release_rod", cq.Workplane().add(rod), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    for k in range(6):
        t = math.radians(60 * k)
        ball = cq.Solid.makeSphere(3.0, cq.Vector(X + (ps["neck_d"] / 2 + 3.0) * math.cos(t), (ps["neck_d"] / 2 + 3.0) * math.sin(t), cz + ps["L"] - ps["head_h"] - 3))
        a.add(f"td_lock_ball_{k}", cq.Workplane().add(ball), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    for sx in (-1, 1):
        for sy in (-1, 1):
            dt.hole("tooldock_master", "z", top, -1, X + sx * 22.6, sy * 22.6, "tap", "M5", M["wall"])
    dt.screw("M5", 12, qty=4, where="flangia cartuccia clamp → master")
    dt.screw("31,5 × 16,3 × 1,75", 0, std="molla a tazza DIN 2093 B (pacco in serie-parallelo, ≥ 1,6 kN TARGET)", qty=8, where="clamp ToolDock")
    dt.screw("Ø6 G10", 0, std="sfera 100Cr6", qty=6, where="clamp a sfere")
    # leva di sgancio 3:1 sul cielo della master: fulcro a 30 mm dall'asse, rullo inseguitore a 90 mm (fuori dalla leva)
    fx = X + 30.0
    lever = box(X - 12, X + 96, -6, 6, top + 62, top + 70).cut(cyl("y", -7, 7, fx, top + 66, 3.0))
    a.add("td_release_lever", cq.Workplane().add(lever), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    post = box(fx - 6, fx + 6, -12, -6.5, top + 6, top + 74).fuse(box(fx - 6, fx + 6, 6.5, 12, top + 6, top + 74)).cut(cyl("y", -13, 13, fx, top + 66, 3.0))
    a.add("td_lever_post", cq.Workplane().add(post), "ZSLIDE", AL, "MC-TD-003", "tomato")
    a.add("td_lever_pin", cq.Workplane().add(cyl("y", -12, 12, fx, top + 66, 2.98)), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    roller = cyl("y", 6.5, 14.5, X + 90, top + 66, 8.0)
    a.add("td_follower", cq.Workplane().add(roller), "ZSLIDE", STEEL, "MC-TD-003", "silver")
    dt.screw("625-2Z", 0, std="cuscinetto rullo inseguitore", qty=1, where="leva di sgancio")
    dt.screw("Ø6 × 30", 0, std="spina ISO 8734 (fulcro)", qty=1, where="leva di sgancio")
    dt.notes.append("Clamp MC-TD-003: pull-stud M10 comune, 6 sfere Ø6 bloccate da un pistone spinto da 8 molle a tazza DIN 2093; "
                    "la leva 3:1 (fulcro a 30 mm, rullo a 90 mm dall'asse) solleva l'asta quando lo Z spinge il rullo sulla camma del "
                    "dock (D016). Forza e corsa del pacco: TARGET da verificare al banco.")
    # porte aria e fluido: fori passanti nel receiver e nel fondo della master, sede O-ring sul piano di accoppiamento
    for name, (px, py), d in PORTS:
        dt.cut("head_receiver", cyl("z", cz - rt - 1, cz + 1, X + px, py, d / 2))
        dt.cut("tooldock_master", cyl("z", cz - 1, cz + M["wall"] + 1, X + px, py, d / 2))
        dt.cut("tooldock_master", cyl("z", cz - 0.1, cz + 1.4, X + px, py, d / 2 + 2.5).cut(cyl("z", cz - 1, cz + 2, X + px, py, d / 2 + 1.0)))
    dt.screw("O-ring 8 × 1,5 / 6 × 1,5", 0, std="O-ring NBR 70", qty=3, where="porte aria/fluido ToolDock")
    # connettori: tasca nel receiver (metà testa) e finestra nel fondo della master (metà macchina)
    for name, c in CONNECTORS.items():
        cx_, cy_ = X + c["c"][0], c["c"][1]
        dt.cut("head_receiver", box(cx_ - c["w"] / 2, cx_ + c["w"] / 2, cy_ - c["d"] / 2, cy_ + c["d"] / 2, cz - rt - 1, cz + 1))
        dt.cut("tooldock_master", box(cx_ - c["w"] / 2, cx_ + c["w"] / 2, cy_ - c["d"] / 2, cy_ + c["d"] / 2, cz - 1, cz + M["wall"] + 1))
        a.add(f"td_conn_{name}_machine", cq.Workplane().add(box(cx_ - c["w"] / 2 + 1, cx_ + c["w"] / 2 - 1, cy_ - c["d"] / 2 + 1, cy_ + c["d"] / 2 - 1, cz + 0.5, cz + c["h"] / 2)),
              "ZSLIDE", STEEL, c["bom"], "black")
        a.add(f"td_conn_{name}_head", cq.Workplane().add(box(cx_ - c["w"] / 2 + 1, cx_ + c["w"] / 2 - 1, cy_ - c["d"] / 2 + 1, cy_ + c["d"] / 2 - 1, cz - c["h"] / 2, cz - 0.5)),
              "ZSLIDE", STEEL, c["bom"], "black")
        dt.screw("secondo scheda", 0, std="fissaggio connettore", qty=2, where=f"connettore {name} (metà testa e metà macchina)")
    # receiver ↔ mount: 4 × M5 dal receiver nel mount; mount: collare a serraggio (taglio + 2 × M5) e camicia
    mb = dt.bb("head_mount")
    mx = (mb.xmin + mb.xmax) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            dt.hole("head_receiver", "z", cz, -1, mx + sx * 24, sy * 24, "clr", "M5", rt + 1, cbore=True)
            dt.hole("head_mount", "z", mb.zmax, -1, mx + sx * 24, sy * 24, "tap", "M5", 12)
    dt.screw("M5", 25, qty=4, where="receiver → mount spindle")
    S = P.SPINDLE
    zc0 = mb.zmin
    a.parts["head_mount"]["shape"] = a.parts["head_mount"]["shape"].fuse(box(mx - 12, mx + 12, mb.ymin - 12, mb.ymin + 0.01, zc0, zc0 + S["clamp_len"])).clean()
    dt.cut("head_mount", box(mx - 1.0, mx + 1.0, mb.ymin - 13, -S["d"] / 2 + 0.5, zc0 - 1, zc0 + S["clamp_len"]))
    for zz in (zc0 + 20, zc0 + S["clamp_len"] - 20):
        dt.cut("head_mount", cyl("x", mx - 13, mx + 13, mb.ymin - 6, zz, CLR["M5"] / 2))
    dt.screw("M5", 25, qty=2, where="collare del mount spindle (orecchia)")
    for zz in (zc0 + 15, zc0 + S["clamp_len"] - 15):          # gole O-ring della camicia
        dt.cut("head_mount", cyl("z", zz - 1.2, zz + 1.2, mx, 0, S["d"] / 2 + 1.6).cut(cyl("z", zz - 2, zz + 2, mx, 0, S["d"] / 2)))
    dt.cut("head_mount", cyl("z", zc0 + 22, zc0 + S["clamp_len"] - 22, mx, 0, S["d"] / 2 + 2.0).cut(cyl("z", zc0, zc0 + S["clamp_len"], mx, 0, S["d"] / 2)))
    dt.screw("O-ring 45 × 2", 0, std="O-ring NBR 70", qty=2, where="camicia del mount")
    dt.notes.append("Mount MC-SP-003: collare sul Ø45 h6 con taglio e 2 × M5, camicia di raffreddamento anulare tra due O-ring, "
                    "alimentata dalle porte Ø4 del receiver.")


def master_to_slide(dt, X, cz):
    """Master ↔ slitta: guance della sella avvitate alle ali (2 × M6 per lato) e 2 × M5 nel bordo inferiore della slitta."""
    D = P.derived()
    top = cz + P.MASTER["T"]
    w_in = P.PLATE["slide_w"] / 2 - P.SLIDE_FLANGE["t"]
    for s in (-1, 1):
        xf = X + s * P.PLATE["slide_w"] / 2
        for yy in (D["slide_front"] - 12,):
            for zz in (top + 12, top + 38):
                dt.hole("z_slide", "x", xf, -s, yy, zz, "clr", "M6", P.SLIDE_FLANGE["t"] + 1, cbore=True)
                dt.hole("tooldock_master", "x", X + s * w_in, -s, yy, zz, "tap", "M6", 9)
        dt.screw("M6", 20, qty=2, where="sella master → ala slitta")
    for dx in (-40.0, 40.0):                          # la master è chiusa: viti lunghe dal piano di accoppiamento (fuori dal receiver)
        yy = (D["slide_front"] + D["slide_back"]) / 2
        dt.hole("tooldock_master", "z", cz, +1, X + dx, yy, "clr", "M5", P.MASTER["T"] + 1, cbore=True)
        dt.hole("z_slide", "z", top, +1, X + dx, yy, "tap", "M5", 12)
    dt.screw("M5", 50, qty=2, where="master → bordo inferiore slitta (dal piano di accoppiamento)")
    dt.screw("Ø6 m6", 20, std="spina ISO 8734", qty=2, where="master ↔ slitta (riferimento)")


# ---------------------------------------------------------------- tavola
def table(dt):
    """Tavola: inserti M6 e boccole R1/R2 già nel mule; qui le sedi degli inserti (Ø8 per inserto M6 in acciaio)."""
    dt.screw("M6 × 12", 0, std="inserto filettato acciaio (filetto utile 9 mm)", qty=P.GRID["nx"] * P.GRID["ny"], where="tavola (ICD §4)")
    dt.screw("Ø8 H7 × 10", 0, std="boccola di riferimento temprata", qty=2, where="tavola R1 / R2")


def detail(a, X, Y, Zd):
    """Applica le lavorazioni di dettaglio all'assieme costruito in (X, Y, Zd)."""
    dt = Detail(a)
    cz = a.parts["tooldock_master"]["shape"].BoundingBox().zmin
    rails(dt)
    blocks(dt)
    supports(dt)
    nuts(dt)
    motors(dt)
    frame(dt)
    uprights(dt)
    tooldock(dt, X, cz)
    master_to_slide(dt, X, cz)
    table(dt)
    dt.apply()
    a.hardware = [dict(std=k[0], item=k[1], where=k[2], qty=v) for k, v in sorted(dt.hw.items())]
    a.notes = dt.notes
    return a
