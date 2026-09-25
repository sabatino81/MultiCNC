#!/usr/bin/env python3
"""D031 · fase 2a: sottoassieme testa + master + slitta Z, tre topologie del collegamento master ↔ slitta.

Uso (dalla radice, con CadQuery, gmsh e ccx): python tools/fea/d031_z.py
Scrive fea/d031/zslide.json e rigenera base/fea-d031-z.html. File di lavoro in build/fea/ (non versionati).

Rispetto al pilota: la slitta Z (piastra 150 × 12 × 160 con ali anteriori e piastrina chiocciola) è un solido
incollato alla master; i quattro pattini HGH15CA ZA sono molle D028 a 6 gdl tra la loro impronta sulla faccia
posteriore della slitta e il carrello X (rigido in questa fase); la vite Z è la catena assiale D028 sulla chiocciola.
Mount a tazza 56 mm (fase 1). Topologie:
- STRIP  : mule v2, la master appoggia solo sul bordo inferiore da 12 mm della piastra;
- FLANGE : flangia posteriore della master, 10 mm, risale di FLANGE_H sulla faccia anteriore della slitta tra le ali;
- SADDLE : sella a U, guance laterali della master incollate alle facce interne delle due ali della slitta.
Casi di forza sul dado ER11 (150 N X, 150 N Y, 200 N Z) e sgancio 0,7 kN; combinati per sovrapposizione.
"""
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
from d031 import A, P, D, S, cq  # noqa: E402

OUT = F.OUT
WORK = F.WORK
PAGE = ROOT / "base" / "fea-d031-z.html"
H = F.H_NOM
CLAMP = 56.0                       # mount a tazza 56 mm (fase 1: −176 g, −3% in Y)
FLANGE_H = 50.0                    # flangia posteriore: 40–60 mm richiesti, 50 nel primo giro
FLANGE_T = 10.0
CHEEK_H = 50.0
CASES = [c for c in F.UNIT if c[0] in ("Fx", "Fy", "Fz", "REL")]
VARIANTS = [
    ("strip", "Striscia 12 mm (mule v2)", "STRIP"),
    ("flange", f"Flangia posteriore {FLANGE_H:.0f} mm", "FLANGE"),
    ("saddle", f"Sella a U sulle ali, {CHEEK_H:.0f} mm", "SADDLE"),
    ("both", "Flangia + sella", "BOTH"),
]


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)).val()


def slide_parts():
    """Slitta, piastrina chiocciola, impronte dei pattini e chiocciola dal mule in CENTER, con coupling in z = 0."""
    a, _ = A.build(*P.CONFIGS["CENTER"], "CENTER")
    mb = a.parts["tooldock_master"]["shape"].BoundingBox()
    X, Z0 = (mb.xmin + mb.xmax) / 2, mb.zmin
    mv = lambda sh: sh.translate(cq.Vector(-X, 0, -Z0))  # noqa: E731
    blocks = []
    for n in ("z_block_00", "z_block_01", "z_block_10", "z_block_11"):
        b = a.parts[n]["shape"].BoundingBox()
        blocks.append((b.xmin - X, b.xmax - X, b.ymin, b.zmin - Z0, b.zmax - Z0))
    nb = a.parts["z_nut"]["shape"].BoundingBox()
    nut = ((nb.xmin + nb.xmax) / 2 - X, (nb.ymin + nb.ymax) / 2, nb.zmin - Z0, (nb.xmax - nb.xmin) / 2)
    return mv(a.parts["z_slide"]["shape"]), mv(a.parts["z_nut_tab"]["shape"]), blocks, nut


def master_variant(kind):
    m = A.master_shape(0.0, 0.0).val()
    top, yf = P.MASTER["T"], D["slide_front"]
    if kind in ("FLANGE", "BOTH"):             # flangia sulla faccia anteriore della slitta, tra le ali (|x| < 65)
        m = m.fuse(box(-60.0, 60.0, yf - FLANGE_T, yf, top - 10.0, top + FLANGE_H))
    if kind in ("SADDLE", "BOTH"):             # guance contro le facce interne delle ali (|x| = 65)
        w_in = P.PLATE["slide_w"] / 2 - P.SLIDE_FLANGE["t"]
        y0 = yf - P.SLIDE_FLANGE["depth"]
        for s in (-1, 1):
            x0, x1 = sorted((s * (w_in - 10.0), s * w_in))
            m = m.fuse(box(x0, x1, y0, yf, top - 10.0, top + CHEEK_H))
    return m


def build(tag, kind, h=H):
    g = F.geometry(clamp_block=CLAMP)
    z = g["z"]
    slide, tab, blocks, nut = slide_parts()
    master = master_variant(kind)
    m = ccx.Model(tag, WORK / tag)
    m.body("struct", [master, slide, tab], "AL")
    m.body("head", [g["receiver"], g["mount"], g["body"]], "AL")
    m.body("shaft", g["shaft"], "STEEL")
    hl = F.H_LOCAL * h / F.H_NOM
    import compliance_d028 as C
    R = C.COUPLING_R
    balls = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in F.BALL_ANGLES]
    for (bx, by) in balls:
        m.refine_at(bx, by, 0.0, 12.0, hl)
    for x in np.linspace(-60, 60, 7):
        m.refine_at(x, D["slide_front"], z["master_top"], 10.0, hl)
    for zz in (z["collar0"], z["collar1"], z["b"], z["top"]):
        for a in range(0, 360, 45):
            m.refine_at(z["r_bore"] * math.cos(math.radians(a)), z["r_bore"] * math.sin(math.radians(a)), zz, 8.0, hl)
    m.refine_at(0, 0, z["tip"] + 12, 16.0, hl)
    info = m.mesh(h)
    ids, conn = m.elements["head"]
    p = m.xyz(conn[:, :4].ravel()).reshape(-1, 4, 3).mean(axis=1)
    rr = np.hypot(p[:, 0], p[:, 1])
    tube = (rr < z["r_bore"] + 0.01) & (rr > z["r_bore"] - 5.2) & (p[:, 2] < z["rear"] + 0.01)
    m.elements["spindle_body"] = (ids[tube], conn[tube])
    m.elements["head"] = (ids[~tube], conn[~tube])
    q = m.quality["head"]
    m.quality["spindle_body"], m.quality["head"] = q[tube], q[~tube]
    m.bodies.append(("spindle_body", [], "STEEL"))
    m.body_nodes["spindle_body"] = np.unique(conn[tube])
    eps = 1e-3
    patches = []
    # pattini Z: impronta sulla faccia posteriore della slitta → molla D028 verso il carrello (rigido)
    kblk = C.block_k(P.Z_AXIS["block"], axis_free=2, normal=1)
    for i, (x0, x1, yb, z0, z1) in enumerate(blocks):
        pn = m.select("struct", lambda x, y, zz: (np.abs(y - yb) < eps) & (x >= x0 - eps) & (x <= x1 + eps) & (zz >= z0 - eps) & (zz <= z1 + eps))
        a = m.rigid_body(f"blk{i}", pn, ((x0 + x1) / 2, yb, (z0 + z1) / 2))
        g_ref, g_rot = m.node((x0 + x1) / 2, yb, (z0 + z1) / 2), m.node((x0 + x1) / 2, yb, (z0 + z1) / 2)
        m.spc += [(g_ref, d) for d in (1, 2, 3)] + [(g_rot, d) for d in (1, 2, 3)]
        m.spring6(f"blk{i}", a, (g_ref, g_rot), list(kblk))
        patches.append(pn)
    # vite Z: catena assiale D028 sulla faccia superiore della piastrina, sotto la chiocciola
    za = P.Z_AXIS
    tab_top = P.MASTER["T"] + P.PLATE["slide_len"] + P.TAB_T
    z_bk_top = (P.MASTER["T"] + P.PLATE["slide_len"]) - P.SUPPORT_GAP_Z - C.parts.ENDS[za["screw"]][1] + za["screw_len"] - 20
    kz = C.screw_axial(za["screw"], za["bk"], z_bk_top - (P.MASTER["T"] + P.PLATE["slide_len"]))
    nx, ny, nz0, nr = nut
    pn = m.select("struct", lambda x, y, zz: (np.abs(zz - tab_top) < eps) & (np.hypot(x - nx, y - ny) <= nr))
    a = m.rigid_body("nut", pn, (nx, ny, tab_top))
    g_ref = m.node(nx, ny, tab_top)
    m.spc += [(g_ref, d) for d in (1, 2, 3)]
    m.spring("nut_z", a[0], 3, g_ref, 3, kz)
    patches.append(pn)
    # accoppiamento, cuscinetti, punta, sgancio: come il pilota
    _, kc = C.coupling_k()
    for i, ((bx, by), ang) in enumerate(zip(balls, F.BALL_ANGLES)):
        pm = m.select("struct", lambda x, y, zz: (np.abs(zz) < eps) & (np.hypot(x - bx, y - by) <= F.BALL_PATCH_R))
        ph = m.select("head", lambda x, y, zz: (np.abs(zz) < eps) & (np.hypot(x - bx, y - by) <= F.BALL_PATCH_R))
        a1 = m.rigid_body(f"ball{i}_m", pm, (bx, by, 0.0))
        b1 = m.rigid_body(f"ball{i}_h", ph, (bx, by, 0.0))
        m.spring(f"ball{i}_n", a1[0], 3, b1[0], 3, kc)
        m.spring_dir(f"ball{i}_t", a1[0], b1[0], (-math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0.0), kc)
        patches += [pm, ph]
    ring = m.select("spindle_body", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    top = m.select("shaft", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    hb, sb = m.rigid_body("bearing_h", ring, (0, 0, z["b"])), m.rigid_body("bearing_s", top, (0, 0, z["b"]))
    kb = S["k_bearing"]
    m.spring6("bearing", hb, sb, [kb, kb, 3 * kb, kb * 25.0 ** 2, kb * 25.0 ** 2, 1e9])
    nose = m.select("shaft", lambda x, y, zz: np.abs(zz - z["tip"]) < eps)
    tip = m.rigid_body("tip", nose, (0, 0, z["tip"]))
    wall = P.MASTER["wall"]
    seat = m.select("struct", lambda x, y, zz: (np.abs(zz - wall) < eps) & (np.hypot(x, y) <= 15.0))
    rel = m.rigid_body("release", seat, (0, 0, wall))
    patches += [ring, top, nose, seat]
    pts = {"tip": tip[0], "tip_rot": tip[1], "release": rel[0]}
    for name, _, loads in CASES:
        m.step(name, [(pts[p_], d, v) for p_, d, v in loads])
    ms = m.body_mass("struct")
    mm = m.body_mass("head")
    return m, info, [tip[0], tip[1], rel[0]], pts, dict(struct=ms, head_al=mm, master=master.Volume() * ccx.MATERIALS["AL"]["rho"])


def solve(tag, kind):
    cache = WORK / tag / "result.json"
    key = dict(v="zslide-v1", kind=kind, h=H, clamp=CLAMP, fh=FLANGE_H, ch=CHEEK_H)
    if cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == key:
            return old["result"]
    t0 = time.time()
    m, info, monitor, pts, mass = build(tag, kind)
    disp, _ = m.run(monitor)
    U = {n: np.array(disp[n][pts["tip"]]) * 1000.0 for n, _, _ in CASES}
    U["FxFz"], U["FyFz"] = U["Fx"] + U["Fz"], U["Fy"] + U["Fz"]
    k = {n: round(f / abs(float(U[n][d])), 3) for n, d, f in (("Fx", 0, 150.0), ("Fy", 1, 150.0), ("Fz", 2, 200.0))}
    r = dict(tag=tag, kind=kind, mesh=info, solve_s=m.solve_s, total_s=round(time.time() - t0, 1),
             mass={k_: round(float(v), 3) for k_, v in mass.items()}, k=k,
             tip_um={n: [round(float(v), 2) for v in u] for n, u in U.items()},
             worst_um=round(max(float(np.linalg.norm(U[n])) for n in ("Fx", "Fy", "Fz", "FxFz", "FyFz")), 1),
             seat_um=round(float(disp["REL"][pts["release"]][2]) * 1000.0, 2))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dict(key=key, result=r)))
    return r


def d028_zlocal():
    """Catena locale del sottoassieme nel modello a travi: master + accoppiamento + testa + slitta Z + guide/vite Z."""
    import compliance_d028 as C
    C.D = P.derived()
    rr = C.compliance(*P.CONFIGS["CENTER"])
    tags = ("master ToolDock", "accoppiamento ToolDock", "testa (spindle + utensile)", "slitta Z", "guide Z + vite Z")
    out = {}
    for ax in "XYZ":
        c = 1.0 / rr[ax]["N_per_um"]
        loc = c * sum(rr[ax]["share"].get(t, 0.0) for t in tags)
        out[ax] = dict(k_local=round(1.0 / loc, 3), k_machine=round(float(rr[ax]["N_per_um"]), 3),
                       rest=round(c - loc, 5), share={t: round(rr[ax]["share"].get(t, 0.0) * 100, 1) for t in tags})
    return out


def main():
    res = dict(stage="zslide", date=time.strftime("%Y-%m-%d"), h=H, clamp=CLAMP, flange_h=FLANGE_H, cheek_h=CHEEK_H,
               d028=d028_zlocal(), variants={})
    for tag, desc, kind in VARIANTS:
        r = solve(f"z_{tag}", kind)
        r["desc"] = desc
        res["variants"][tag] = r
        print(f"{tag:7} k {r['k']} massa {r['mass']} {r['solve_s']} s", flush=True)
        (OUT / "zslide.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    import d031_z_page
    d031_z_page.write(res)


if __name__ == "__main__":
    main()
