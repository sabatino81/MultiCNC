#!/usr/bin/env python3
"""D031 · fase 3: gantry completo del mule v3 (spalle, trave, carrello X, slitta Z, master, testa 5045-style).

Uso (dalla radice, con CadQuery, gmsh e ccx): python tools/fea/d031_gantry.py [--h H] [--coarse HC]
Scrive fea/d031/gantry.json e rigenera base/fea-d031-gantry.html. File di lavoro in build/fea/ (non versionati).

Solidi dal mule v3 in CENTER (stesse funzioni di standard_assembly.py): spalle + trave + spessori BK/BF X
incollati, vincolati alla base delle spalle (il telaio resta nel modello a travi D028); carrello X con la staffa
della chiocciola X; slitta Z con piastrina chiocciola 16 mm e master con sella a U; testa come nel pilota.
Molle D028: 4 pattini HGH15CA ZA X tra carrello e guida sulla trave, catena assiale della vite X sul BK in trave,
4 pattini HGH15CA ZA Z tra slitta e carrello, catena della vite Z sul BK sul carrello, tre sfere del ToolDock,
cuscinetti dello spindle. Carichi sul dado ER11: 150 N X, 150 N Y, 200 N Z; combinati per sovrapposizione.
Mesh graduata: fine (H) attorno a testa, slitta e carrello, grossa (HC) su trave e spalle.
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
from d031 import A, P, S, cq  # noqa: E402

OUT = F.OUT
WORK = F.WORK
CASES = [c for c in F.UNIT if c[0] in ("Fx", "Fy", "Fz")]
REST_TAGS = ("telaio", "tavola", "guide Y + vite Y")        # resta nel modello a travi D028


def parts_center():
    a, _ = A.build(*P.CONFIGS["CENTER"], "CENTER")
    return a, {n: p["shape"] for n, p in a.parts.items()}


def bb(sh):
    b = sh.BoundingBox()
    return b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax


def build(tag, h, hc, rigid=(), stiff_springs=()):
    import compliance_d028 as C
    a, sh = parts_center()
    X0 = (bb(sh["tooldock_master"])[0] + bb(sh["tooldock_master"])[1]) / 2
    cz = bb(sh["tooldock_master"])[4]
    g = F.geometry(clamp_block=56.0)
    mv = lambda s: s.translate(cq.Vector(X0, 0.0, cz))  # noqa: E731
    z = {k: (v + cz if isinstance(v, float) and k != "r_bore" and k != "master_top" else v) for k, v in g["z"].items()}
    m = ccx.Model(tag, WORK / tag)
    m.body("gantry", [sh["beam"], sh["upright_L"], sh["upright_R"], sh["x_pads"]], "AL")
    m.body("carriage", [sh["x_carriage"], sh["x_nut_bracket"]], "AL")
    m.body("struct", [sh["tooldock_master"], sh["z_slide"], sh["z_nut_tab"]], "AL")
    m.body("head", [mv(g["receiver"]), mv(g["mount"]), mv(g["body"])], "AL")
    m.body("shaft", mv(g["shaft"]), "STEEL")
    hl = F.H_LOCAL * h / F.H_NOM
    R = C.COUPLING_R
    balls = [(X0 + R * math.cos(math.radians(t)), R * math.sin(math.radians(t))) for t in F.BALL_ANGLES]
    for (bx, by) in balls:
        m.refine_at(bx, by, cz, 12.0, hl)
    for zz in (z["collar0"], z["collar1"], z["b"], z["top"]):
        for t in range(0, 360, 45):
            m.refine_at(X0 + z["r_bore"] * math.cos(math.radians(t)), z["r_bore"] * math.sin(math.radians(t)), zz, 8.0, hl)
    m.refine_at(X0, 0, z["tip"] + 12, 16.0, hl)
    # zona fine: testa, master, slitta e carrello (box), grossa altrove
    xb = bb(sh["x_carriage"])
    m.box_size = (xb[0] - 10, xb[1] + 10, -80.0, xb[3] + 10, z["tip"] - 10, xb[5] + 10, h)
    info = m.mesh(hc)
    ids, conn = m.elements["head"]
    p = m.xyz(conn[:, :4].ravel()).reshape(-1, 4, 3).mean(axis=1)
    rr = np.hypot(p[:, 0] - X0, p[:, 1])
    tube = (rr < z["r_bore"] + 0.01) & (rr > z["r_bore"] - 5.2) & (p[:, 2] < z["rear"] + 0.01)
    m.elements["spindle_body"] = (ids[tube], conn[tube])
    m.elements["head"] = (ids[~tube], conn[~tube])
    q = m.quality["head"]
    m.quality["spindle_body"], m.quality["head"] = q[tube], q[~tube]
    m.bodies.append(("spindle_body", [], "STEEL"))
    m.body_nodes["spindle_body"] = np.unique(conn[tube])
    # trave e spalle: stessa mesh incollata, due gruppi di elementi (split per l'asse Z)
    gid, gconn = m.elements.pop("gantry")
    gq = m.quality.pop("gantry")
    gc = m.xyz(gconn[:, :4].ravel()).reshape(-1, 4, 3).mean(axis=1)
    upr = gc[:, 2] < bb(sh["beam"])[4]
    m.elements["uprights"], m.elements["beam"] = (gid[upr], gconn[upr]), (gid[~upr], gconn[~upr])
    m.quality["uprights"], m.quality["beam"] = gq[upr], gq[~upr]
    m.bodies = [b for b in m.bodies if b[0] != "gantry"] + [("beam", [], "AL"), ("uprights", [], "AL")]
    m.energy_groups = {
        "uprights": (["uprights"], ()), "beam": (["beam"], ()), "carriage": (["carriage"], ()),
        "zslide": (["struct"], ()), "head": (["head", "spindle_body", "shaft"], ()),
        "xblocks": ((), ("x_block",)), "xscrew": ((), ("xscrew",)), "zblocks": ((), ("z_block",)), "zscrew": ((), ("zscrew",)),
        "tooldock": ((), ("ball",)), "bearing": ((), ("bearing",)),
    }
    if rigid:                                   # diagnostica: corpi resi "infinitamente" rigidi
        rigid = set(rigid) | ({"beam", "uprights"} if "gantry" in rigid else set())
        m.bodies = [(n, s_, "RIGID" if n in rigid else mt) for n, s_, mt in m.bodies]
    eps = 1e-3

    def patch(body, fn, name):
        n = m.select(body, fn)
        if len(n) < 3:
            raise SystemExit(f"patch {name} vuota")
        return n

    # vincolo: base delle spalle sul telaio
    zb0 = bb(sh["upright_L"])[4]
    m.fix("frame", patch("gantry", lambda x, y, zz: np.abs(zz - zb0) < eps, "base spalle"))
    # pattini X: faccia posteriore del carrello ↔ impronta sulla guida (faccia della trave)
    kbx = C.block_k(P.X_AXIS["block"], axis_free=0, normal=1)
    y_face = bb(sh["x_rail_top"])[3]
    for bn in ("x_block_00", "x_block_01", "x_block_10", "x_block_11"):
        x0, x1, y0, y1, z0, z1 = bb(sh[bn])
        rail = sh["x_rail_top"] if z0 > bb(sh["x_rail_bot"])[5] else sh["x_rail_bot"]
        rz0, rz1 = bb(rail)[4], bb(rail)[5]
        pc = patch("carriage", lambda x, y, zz: (np.abs(y - y0) < eps) & (x >= x0 - eps) & (x <= x1 + eps) & (zz >= z0 - eps) & (zz <= z1 + eps), bn)
        pb = patch("gantry", lambda x, y, zz: (np.abs(y - y_face) < eps) & (x >= x0 - eps) & (x <= x1 + eps) & (zz >= rz0 - eps) & (zz <= rz1 + eps), bn + "_rail")
        c0 = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        m.spring6(bn, m.rigid_body(bn + "_c", pc, c0), m.rigid_body(bn + "_b", pb, c0), list(kbx))
    # vite X: staffa della chiocciola sul carrello ↔ BK sulla trave (spessori), catena assiale D028
    xa = P.X_AXIS
    x_bk = P.TRAVEL["X"] / 2 + (xa["screw_len"] - sum(C.parts.ENDS[xa["screw"]])) / 2 + 14.5
    kx = C.screw_axial(xa["screw"], xa["bk"], x_bk - P.CONFIGS["CENTER"][0])
    nb = bb(sh["x_nut_bracket"]); nt = bb(sh["x_nut"]); kb_ = bb(sh["x_bk"]); pd = bb(sh["x_pads"])
    pn = patch("carriage", lambda x, y, zz: (np.abs(x - nb[0]) < eps) & (y >= nt[2] - eps) & (y <= nt[3] + eps) & (zz >= nt[4] - eps) & (zz <= nt[5] + eps), "staffa X")
    pk = patch("gantry", lambda x, y, zz: (np.abs(y - pd[2]) < eps) & (x >= kb_[0] - eps) & (x <= kb_[1] + eps) & (zz >= kb_[4] - eps) & (zz <= kb_[5] + eps), "BK X")
    ra = m.rigid_body("xnut", pn, (nb[0], (nt[2] + nt[3]) / 2, (nt[4] + nt[5]) / 2))
    rb = m.rigid_body("xbk", pk, ((kb_[0] + kb_[1]) / 2, pd[2], (kb_[4] + kb_[5]) / 2))
    m.spring("xscrew", ra[0], 1, rb[0], 1, kx)
    # pattini Z: faccia posteriore della slitta ↔ impronta sulla guida Z (faccia anteriore del carrello)
    kbz = C.block_k(P.Z_AXIS["block"], axis_free=2, normal=1)
    yz = bb(sh["z_rail_0"])[3]
    for bn in ("z_block_00", "z_block_01", "z_block_10", "z_block_11"):
        x0, x1, y0, y1, z0, z1 = bb(sh[bn])
        rail = sh["z_rail_0"] if x1 < X0 else sh["z_rail_1"]
        rx0, rx1 = bb(rail)[0], bb(rail)[1]
        ps = patch("struct", lambda x, y, zz: (np.abs(y - y0) < eps) & (x >= x0 - eps) & (x <= x1 + eps) & (zz >= z0 - eps) & (zz <= z1 + eps), bn)
        pc = patch("carriage", lambda x, y, zz: (np.abs(y - yz) < eps) & (x >= rx0 - eps) & (x <= rx1 + eps) & (zz >= z0 - eps) & (zz <= z1 + eps), bn + "_rail")
        c0 = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        m.spring6(bn, m.rigid_body(bn + "_s", ps, c0), m.rigid_body(bn + "_c", pc, c0), list(kbz))
    # vite Z: piastrina chiocciola ↔ BK Z sul carrello, catena assiale D028
    za = P.Z_AXIS
    tb = bb(sh["z_nut_tab"]); zn = bb(sh["z_nut"]); zk = bb(sh["z_bk"])
    tab = tb[4]
    z_bk_top = tab - P.SUPPORT_GAP_Z - C.parts.ENDS[za["screw"]][1] + za["screw_len"] - 20
    kz = C.screw_axial(za["screw"], za["bk"], z_bk_top - tab)
    nx, ny, nr = (zn[0] + zn[1]) / 2, (zn[2] + zn[3]) / 2, (zn[1] - zn[0]) / 2
    pt = patch("struct", lambda x, y, zz: (np.abs(zz - tb[5]) < eps) & (np.hypot(x - nx, y - ny) <= nr), "piastrina Z")
    # nel mule il BK Z sta nella fessura del carrello senza attacco disegnato: si aggancia alle due facce della
    # fessura sulla sua altezza (alette laterali, ipotesi MULE; D028 lo collega rigidamente al carrello)
    sw = P.PLATE["slot_w"] / 2
    pz = patch("carriage", lambda x, y, zz: (np.abs(np.abs(x - X0) - sw) < eps) & (zz >= zk[4] - eps) & (zz <= zk[5] + eps), "BK Z")
    ra = m.rigid_body("znut", pt, (nx, ny, tb[5]))
    rb = m.rigid_body("zbk", pz, ((zk[0] + zk[1]) / 2, yz, (zk[4] + zk[5]) / 2))
    m.spring("zscrew", ra[0], 3, rb[0], 3, kz)
    # ToolDock, cuscinetti, punta
    _, kc = C.coupling_k()
    for i, ((bx, by), ang) in enumerate(zip(balls, F.BALL_ANGLES)):
        pm = patch("struct", lambda x, y, zz: (np.abs(zz - cz) < eps) & (np.hypot(x - bx, y - by) <= F.BALL_PATCH_R), f"sfera {i} master")
        ph = patch("head", lambda x, y, zz: (np.abs(zz - cz) < eps) & (np.hypot(x - bx, y - by) <= F.BALL_PATCH_R), f"sfera {i} testa")
        a1, b1 = m.rigid_body(f"ball{i}_m", pm, (bx, by, cz)), m.rigid_body(f"ball{i}_h", ph, (bx, by, cz))
        m.spring(f"ball{i}_n", a1[0], 3, b1[0], 3, kc)
        m.spring_dir(f"ball{i}_t", a1[0], b1[0], (-math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0.0), kc)
    ring = patch("spindle_body", lambda x, y, zz: np.abs(zz - z["b"]) < eps, "cuscinetti corpo")
    top = patch("shaft", lambda x, y, zz: np.abs(zz - z["b"]) < eps, "cuscinetti albero")
    hb, sb = m.rigid_body("bearing_h", ring, (X0, 0, z["b"])), m.rigid_body("bearing_s", top, (X0, 0, z["b"]))
    kb = S["k_bearing"]
    m.spring6("bearing", hb, sb, [kb, kb, 3 * kb, kb * 25.0 ** 2, kb * 25.0 ** 2, 1e9])
    nose = patch("shaft", lambda x, y, zz: np.abs(zz - z["tip"]) < eps, "naso")
    tip = m.rigid_body("tip", nose, (X0, 0, z["tip"]))
    for name, _, loads in CASES:
        m.step(name, [(tip[0] if pt_ == "tip" else tip[1], d, v) for pt_, d, v in loads])
    if stiff_springs:                           # diagnostica: molle con questi prefissi ×1000 (quasi rigide)
        m.springs = [(n, a_, d1, b_, d2, k * 1000.0 if n.startswith(tuple(stiff_springs)) else k) for n, a_, d1, b_, d2, k in m.springs]
    mass = {b: round(m.body_mass(b), 3) for b in ("beam", "uprights", "carriage", "struct", "head")}
    return m, info, [tip[0], tip[1]], tip, mass


def d028_split():
    import compliance_d028 as C
    C.D = P.derived()
    rr = C.compliance(*P.CONFIGS["CENTER"])
    out = {}
    for ax in "XYZ":
        c = 1.0 / rr[ax]["N_per_um"]
        rest = c * sum(rr[ax]["share"].get(t, 0.0) for t in REST_TAGS)
        out[ax] = dict(k_machine=round(float(rr[ax]["N_per_um"]), 3), rest=rest, k_gantry_d028=round(1.0 / (c - rest), 3),
                       limit=round(1.0 / rest, 3), share={t: round(v * 100, 1) for t, v in rr[ax]["share"].items() if v > 0.005})
    return out


def solve(tag, h, hc, rigid=(), stiff_springs=(), energy=False):
    cache = WORK / tag / "result.json"
    key = dict(v="gantry-v1", h=h, hc=hc, tab=P.TAB_T, saddle=P.SADDLE)
    if getattr(P, "CONCEPT", None):
        import standard_concepts
        key["concept"] = P.CONCEPT
        key["over"] = json.loads(json.dumps(standard_concepts.overrides(P.CONCEPT), default=str))
    if energy:
        key["energy"] = True
    if rigid:
        key["rigid"] = sorted(rigid)
    if stiff_springs:
        key["stiff_springs"] = sorted(stiff_springs)
    if cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == key:
            return old["result"]
    t0 = time.time()
    m, info, monitor, tip, mass = build(tag, h, hc, rigid, stiff_springs)
    disp, _ = m.run(monitor)
    energy = m.read_energy()
    U = {n: np.array(disp[n][tip[0]]) * 1000.0 for n, _, _ in CASES}
    U["FxFz"], U["FyFz"] = U["Fx"] + U["Fz"], U["Fy"] + U["Fz"]
    k = {n: round(f / abs(float(U[n][d])), 3) for n, d, f in (("Fx", 0, 150.0), ("Fy", 1, 150.0), ("Fz", 2, 200.0))}
    r = dict(tag=tag, h=h, hc=hc, rigid=sorted(rigid), mesh=info, solve_s=m.solve_s, total_s=round(time.time() - t0, 1), mass=mass, k=k,
             tip_um={n: [round(float(v), 2) for v in u] for n, u in U.items()},
             worst_um=round(max(float(np.linalg.norm(U[n])) for n in U), 1),
             energy={n: {g: round(e, 6) for g, e in energy.get(n, {}).items()} for n, _, _ in CASES},
             work={n: round(0.5 * f * abs(float(U[n][d])) / 1000.0, 6) for n, d, f in (("Fx", 0, 150.0), ("Fy", 1, 150.0), ("Fz", 2, 200.0))})
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dict(key=key, result=r)))
    return r


DIAG = [  # (nome, corpi rigidi): la cedevolezza tolta misura il peso di ciascun gruppo
    ("gantry", ("gantry",)),
    ("carriage", ("carriage",)),
    ("zgroup", ("struct", "head", "spindle_body", "shaft")),
    ("tooldock", (), ("ball",)),                                        # molle delle tre sfere ×1000
    ("rails", (), ("x_block", "z_block", "xscrew", "zscrew")),          # pattini e viti X/Z ×1000
    ("beam", ("beam",)),                                                  # split per Z (D032)
    ("uprights", ("uprights",)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", type=float, default=6.0, help="mesh fine attorno a testa, slitta e carrello")
    ap.add_argument("--coarse", type=float, default=12.0, help="mesh grossa su trave e spalle")
    ap.add_argument("--check", action="store_true", help="solo mesh, senza soluzione")
    ap.add_argument("--diag", action="store_true", help="diagnostica: gantry, carrello e gruppo Z resi rigidi uno alla volta")
    ap.add_argument("--energy", action="store_true", help="energia di deformazione per gruppo sulla baseline diagnostica")
    ap.add_argument("--concept", help="D032: variante di tools/cad/standard_concepts.py (gantry con energia, fea/d032/<nome>.json)")
    args = ap.parse_args()
    if args.concept:
        import standard_concepts
        c = standard_concepts.apply(args.concept)
        P.CONCEPT = args.concept
        r = solve(f"d032_{args.concept}_h{args.h:g}_c{args.coarse:g}", args.h, args.coarse, energy=True)
        r.update(concept=args.concept, desc=c["desc"])
        out = ROOT / "fea" / "d032"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{args.concept}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, default=float))
        print(args.concept, r["k"], r["mass"], r["solve_s"], "s", flush=True)
        return
    if args.check:
        m, info, *_ = build("gantry_check", args.h, args.coarse)
        print(info)
        return
    res = dict(stage="gantry", date=time.strftime("%Y-%m-%d"), d028=d028_split(), runs={}, diag={})
    old = OUT / "gantry.json"
    if old.exists():
        prev = json.loads(old.read_text())
        res["runs"], res["diag"] = prev.get("runs", {}), prev.get("diag", {})
        if "energy" in prev:
            res["energy"] = prev["energy"]
    if args.energy:
        r = solve(f"gantry_h{args.h:g}_c{args.coarse:g}_energy", args.h, args.coarse, energy=True)
        res["energy"] = r
        e = r["energy"]["Fy"]
        print("energia", {k: round(v / r["work"]["Fy"] * 100, 1) for k, v in e.items()}, "somma", round(sum(e.values()) / r["work"]["Fy"] * 100, 1), flush=True)
    elif args.diag:
        for name, rig, *spr in DIAG:
            r = solve(f"gantry_h{args.h:g}_c{args.coarse:g}_rigid_{name}", args.h, args.coarse, rig, tuple(spr[0]) if spr else ())
            res["diag"][name] = r
            print(name, r["k"], r["solve_s"], "s", flush=True)
            old.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float))
    else:
        r = solve(f"gantry_h{args.h:g}_c{args.coarse:g}", args.h, args.coarse)
        res["runs"][r["tag"]] = r
        print(r["tag"], r["k"], r["mesh"], r["solve_s"], "s", flush=True)
    old.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float))
    import d031_gantry_page
    d031_gantry_page.write(json.loads(old.read_text()))


if __name__ == "__main__":
    main()
