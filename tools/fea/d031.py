#!/usr/bin/env python3
"""D031 · FEA a solidi della Standard (mule v2) · fase 1: modello pilota master ToolDock + testa 5045-style.

Uso (dalla radice, con CadQuery, gmsh e ccx): python tools/fea/d031.py [--quick]
Scrive fea/d031/pilot.json e rigenera base/fea-d031.html. File di lavoro (.inp, .frd) in build/fea/ (non versionati).

Modello pilota:
- master scatolata (mule v2, parete variabile) incastrata sulla striscia di appoggio sotto la slitta Z
  (y ≥ slide_front, faccia superiore): la slitta è rigida in questa fase;
- accoppiamento ToolDock: tre sfere su Ø80 a 120° (90°, 210°, 330°, ipotesi MULE); per sfera una molla normale
  (Z) e una tangenziale da kc Hertz di D028 tra due patch rigide Ø12 su master e receiver: la somma coincide con la
  molla a 6 gdl di D028, le piastre però si deformano;
- testa: receiver + mount a tazza incollati, corpo spindle come tubo in acciaio Ø45 / Ø35 incollato nel collare
  (come D028), cuscinetti con la molla a 6 gdl di D028, albero Ø16 fino al dado ER11 (punto di misura, D029);
- il connettore non entra: il service envelope è solo un controllo CAD (D031).
Carichi su un punto di riferimento sul dado ER11 (corpo rigido sulla faccia del naso), mai su un nodo.
"""
import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools" / "cad"))
sys.path.insert(0, str(ROOT / "tools" / "calc"))
sys.path.insert(0, str(HERE))
import ccx  # noqa: E402
import standard_assembly as A  # noqa: E402
import standard_params as P  # noqa: E402
import cadquery as cq  # noqa: E402

OUT = ROOT / "fea" / "d031"
WORK = ROOT / "build" / "fea"
PAGE = ROOT / "base" / "fea-d031.html"
D = P.derived()
S = P.SPINDLE
BALL_ANGLES = (90.0, 210.0, 330.0)
BALL_PATCH_R = 6.0
H_NOM, H_LOCAL = 6.0, 2.5           # mm: globale e locale (D031: 5–8 e 2–3 mm)
FINE = 0.75                          # mesh di convergenza: dimensioni −25% (−30% supera la memoria del container con SPOOLES)
CONV_LIMIT = 0.05                    # spostamento alla punta entro 5%
HOT_EXCL = 6.0                       # mm dai vincoli e dalle patch rigide per la tensione "hotspot"

UNIT = [  # step risolti: (nome, descrizione, [(punto, dof, valore)]) · punto: "tip", "tip_rot", "release"
    ("Fx", "150 N radiale X", [("tip", 1, 150.0)]),
    ("Fy", "150 N radiale Y", [("tip", 2, 150.0)]),
    ("Fz", "200 N assiale Z", [("tip", 3, 200.0)]),
    ("Mx", "18 N·m ToolDock attorno a X", [("tip_rot", 1, 18000.0)]),
    ("My", "18 N·m ToolDock attorno a Y", [("tip_rot", 2, 18000.0)]),
    ("REL", "0,7 kN di sgancio (D016)", [("release", 3, 700.0)]),
]
COMBINED = [  # sovrapposizione lineare: 150 N radiali totali, mai 150 X + 150 Y insieme
    ("FxFz", "150 N X + 200 N Z", ("Fx", "Fz")),
    ("FyFz", "150 N Y + 200 N Z", ("Fy", "Fz")),
]


def cyl(z0, z1, r, r_in=0.0):
    c = cq.Workplane("XY").circle(r)
    if r_in:
        c = c.circle(r_in)
    return c.extrude(z1 - z0).translate((0, 0, z0)).val()


def geometry(master_wall=None, clamp_block=None):
    """Solidi del pilota con il coupling nel piano z = 0 e l'asse spindle su x = y = 0."""
    Sx = dict(S, clamp_block=clamp_block or S["clamp_block"])
    h = A.Asm()
    A.add_head(h, 0.0, 0.0, Sx)
    z_top = -Sx["receiver_t"]
    z_rear = z_top - Sx["connector"]
    z_b = z_rear - Sx["rear"] - Sx["housing"] - Sx["neck"]
    z_tip = z_b - Sx["nose"]
    r_bore = Sx["d"] / 2 + 0.1
    g = dict(
        master=A.master_shape(0.0, 0.0, master_wall).val(),
        receiver=h.parts["head_receiver"]["shape"], mount=h.parts["head_mount"]["shape"],
        body=cyl(z_b, z_rear, r_bore, r_bore - 5.1),                   # corpo spindle equivalente, sp. 5 (D028)
        shaft=cyl(z_tip, z_b, 8.0),                                     # albero Ø16 fino al dado (D028)
        z=dict(top=z_top, rear=z_rear, b=z_b, tip=z_tip, collar0=z_rear - Sx["rear"] - 10 - Sx["clamp_len"],
               collar1=z_rear - Sx["rear"] - 10, master_top=P.MASTER["T"], r_bore=r_bore))
    return g


def coupling_springs():
    import compliance_d028 as C
    k6, kc = C.coupling_k()
    return k6, kc


def build_model(tag, h, master_wall=None, clamp_block=None, cases=None):
    g = geometry(master_wall, clamp_block)
    z = g["z"]
    m = ccx.Model(tag, WORK / tag)
    m.body("master", g["master"], "AL")
    m.body("head", [g["receiver"], g["mount"], g["body"]], "AL")     # il corpo spindle diventa acciaio sotto
    m.body("shaft", g["shaft"], "STEEL")
    hl = H_LOCAL * h / H_NOM
    import compliance_d028 as C
    R = C.COUPLING_R
    balls = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in BALL_ANGLES]
    for (bx, by) in balls:
        m.refine_at(bx, by, 0.0, 12.0, hl)
    for x in np.linspace(-60, 60, 7):
        m.refine_at(x, D["slide_front"], z["master_top"], 10.0, hl)       # radice della master sulla slitta
    for zz in (z["collar0"], z["collar1"], z["b"], z["top"]):
        for a in range(0, 360, 45):
            m.refine_at(z["r_bore"] * math.cos(math.radians(a)), z["r_bore"] * math.sin(math.radians(a)), zz, 8.0, hl)
    m.refine_at(0, 0, z["tip"] + 12, 16.0, hl)
    info = m.mesh(h)
    # il corpo spindle è acciaio: separo gli elementi del tubo dal resto della testa
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
    m.body_nodes["head_al"] = np.unique(conn[~tube])
    eps = 1e-3
    # vincolo: striscia di appoggio sotto la slitta
    fixed = m.select("master", lambda x, y, zz: (np.abs(zz - z["master_top"]) < eps) & (y >= D["slide_front"] - eps))
    m.fix("slide", fixed)
    patches = [fixed]
    # accoppiamento: tre sfere
    _, kc = coupling_springs()
    for i, ((bx, by), ang) in enumerate(zip(balls, BALL_ANGLES)):
        pm = m.select("master", lambda x, y, zz: (np.abs(zz) < eps) & (np.hypot(x - bx, y - by) <= BALL_PATCH_R))
        ph = m.select("head", lambda x, y, zz: (np.abs(zz) < eps) & (np.hypot(x - bx, y - by) <= BALL_PATCH_R))
        a = m.rigid_body(f"ball{i}_m", pm, (bx, by, 0.0))
        b = m.rigid_body(f"ball{i}_h", ph, (bx, by, 0.0))
        m.spring(f"ball{i}_n", a[0], 3, b[0], 3, kc)
        t = (-math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0.0)
        m.spring_dir(f"ball{i}_t", a[0], b[0], t, kc)
        patches += [pm, ph]
    # cuscinetti: anello frontale del corpo ↔ faccia superiore dell'albero, molla D028
    ring = m.select("spindle_body", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    top = m.select("shaft", lambda x, y, zz: np.abs(zz - z["b"]) < eps)
    hb = m.rigid_body("bearing_h", ring, (0, 0, z["b"]))
    sb = m.rigid_body("bearing_s", top, (0, 0, z["b"]))
    kb = S["k_bearing"]
    m.spring6("bearing", hb, sb, [kb, kb, 3 * kb, kb * 25.0 ** 2, kb * 25.0 ** 2, 1e9])
    # punto di misura e di carico: faccia del dado ER11
    nose = m.select("shaft", lambda x, y, zz: np.abs(zz - z["tip"]) < eps)
    tip = m.rigid_body("tip", nose, (0, 0, z["tip"]))
    # sgancio: sede del clamp sulla faccia interna del fondo della master, Ø30 attorno al pull-stud
    wall = master_wall if master_wall is not None else P.MASTER["wall"]
    seat = m.select("master", lambda x, y, zz: (np.abs(zz - wall) < eps) & (np.hypot(x, y) <= 15.0))
    rel = m.rigid_body("release", seat, (0, 0, wall))
    patches += [ring, top, nose, seat]
    pts = {"tip": tip[0], "tip_rot": tip[1], "release": rel[0]}
    for name, _, loads in cases:
        m.step(name, [(pts[p], d, v) for p, d, v in loads])
    monitor = [tip[0], tip[1], rel[0]]
    masses = {"master": m.body_mass("master"), "head_al": m.body_mass("head")}
    return m, info, monitor, pts, patches, masses


CACHE_KEY = "pilot-v2-highorder"   # cambia quando cambiano modello o post-processing


def solve(tag, h, cases=None, **kw):
    """Risolve (o riusa build/fea/<tag>/result.json se stessi parametri) e salva subito il risultato."""
    cases = cases or UNIT
    key = dict(v=CACHE_KEY, h=h, cases=[c[0] for c in cases], kw=kw, E={k: v["E"] for k, v in ccx.MATERIALS.items()})
    cache = WORK / tag / "result.json"
    if cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == key:
            return old["result"]
    r = json.loads(json.dumps(_solve(tag, h, cases, **kw), default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dict(key=key, result=r)))
    return r


def _solve(tag, h, cases, **kw):
    t0 = time.time()
    m, info, monitor, pts, patches, masses = build_model(tag, h, cases=cases, **kw)
    t_mesh = time.time() - t0
    disp, st = m.run(monitor)
    excl = np.vstack([m.xyz(p) for p in patches])
    tree = cKDTree(excl)
    body_of = {}
    for b in ("master", "head_al", "spindle_body", "shaft"):
        for n in m.body_nodes[b]:
            body_of.setdefault(int(n), b)
    mesh_ids = np.unique(np.concatenate([c.ravel() for _, c in m.elements.values()]))
    far = (tree.query(m.xyz(mesh_ids))[0] > HOT_EXCL) & ~np.isin(mesh_ids, m.poor_nodes())
    bodies = np.array([body_of.get(int(n)) for n in mesh_ids])
    U, SIG = {}, {}
    for name, _, _ in cases:
        U[name] = np.array(disp[name][pts["tip"]]) * 1000.0            # µm
        ids, sg = st[name]
        order = {n: i for i, n in enumerate(ids)}
        SIG[name] = sg[[order[n] for n in mesh_ids]]
    combined = [c for c in COMBINED if all(p in U for p in c[2])]
    for name, desc, parts_ in combined:
        U[name] = sum(U[p] for p in parts_)
        SIG[name] = sum(SIG[p] for p in parts_)
    out = {}
    for name, desc in [(c[0], c[1]) for c in cases] + [(c[0], c[1]) for c in combined]:
        u = U[name]
        r = dict(desc=desc, tip_um=[round(float(v), 3) for v in u], tip_abs_um=round(float(np.linalg.norm(u)), 3))
        if name in ("Fx", "Fy", "Fz"):
            d = {"Fx": 0, "Fy": 1, "Fz": 2}[name]
            f = {"Fx": 150.0, "Fy": 150.0, "Fz": 200.0}[name]
            r["k_N_um"] = round(f / abs(float(u[d])), 3)
        if name == "REL":
            r["seat_um"] = round(float(disp[name][pts["release"]][2]) * 1000.0, 3)
        val = ccx.Model.von_mises(SIG[name])
        i = int(np.argmax(val))
        j = int(np.argmax(np.where(far, val, -1)))
        r["vm_peak"] = dict(MPa=round(float(val[i]), 2), at=[round(float(c), 1) for c in m.nodes[int(mesh_ids[i])]], body=body_of.get(int(mesh_ids[i])))
        r["vm_hot"] = dict(MPa=round(float(val[j]), 2), at=[round(float(c), 1) for c in m.nodes[int(mesh_ids[j])]], body=body_of.get(int(mesh_ids[j])))
        r["vm_hot_body"] = {b: round(float(np.max(np.where(far & (bodies == b), val, 0.0))), 2) for b in ("master", "head_al", "spindle_body", "shaft")}
        out[name] = r
    return dict(tag=tag, h=h, mesh=info, mesh_s=round(t_mesh, 1), solve_s=m.solve_s,
                mass=dict(master=round(masses["master"], 3), head_al=round(masses["head_al"], 3)), cases=out)


def d028_local():
    """Stessa catena locale (master + accoppiamento + testa) nel modello D028 al centro corsa: N/µm."""
    import compliance_d028 as C
    C.D = P.derived()
    r = C.compliance(*P.CONFIGS["CENTER"])
    tags = ("master ToolDock", "accoppiamento ToolDock", "testa (spindle + utensile)")
    out = {}
    for ax in "XYZ":
        c = (1.0 / r[ax]["N_per_um"]) * sum(r[ax]["share"].get(t, 0.0) for t in tags)
        out[ax] = dict(k_local=round(1.0 / c, 3), share={t: round(r[ax]["share"].get(t, 0.0) * 100, 1) for t in tags},
                       k_machine=round(float(r[ax]["N_per_um"]), 3))
    return out


VARIANTS = [  # (tag, descrizione, kwargs)
    ("master_w8", "Master parete 8 (mule v2)", {}),
    ("master_w6", "Master parete 6", dict(master_wall=6.0)),
    ("master_w10", "Master parete 10", dict(master_wall=10.0)),
    ("mount_56", "Mount a tazza 56 × 56", dict(clamp_block=56.0)),
    ("mount_66", "Mount a tazza 66 × 66", dict(clamp_block=66.0)),
]


def self_test():
    """Materiali ×10³: la FEA deve ridare la cedevolezza analitica di accoppiamento (D028) e cuscinetti."""
    import compliance_d028 as C
    saved = {k: v["E"] for k, v in ccx.MATERIALS.items()}
    try:
        for v in ccx.MATERIALS.values():
            v["E"] *= 1e3
        r = solve("selftest", 10.0, cases=UNIT[:3])
    finally:
        for k, v in saved.items():
            ccx.MATERIALS[k]["E"] = v
    k6, _ = C.coupling_k()
    kb, L = S["k_bearing"], -geometry()["z"]["tip"]
    exp = dict(X=1 / (1 / k6[0] + L ** 2 / k6[4] + 2 / kb) / 1000, Z=1 / (1 / k6[2] + 1 / (3 * kb)) / 1000)
    got = dict(X=r["cases"]["Fx"]["k_N_um"], Y=r["cases"]["Fy"]["k_N_um"], Z=r["cases"]["Fz"]["k_N_um"])
    err = max(abs(got["X"] - exp["X"]) / exp["X"], abs(got["Y"] - exp["X"]) / exp["X"], abs(got["Z"] - exp["Z"]) / exp["Z"])
    return dict(expected={k: round(v, 3) for k, v in exp.items()}, got=got, err=round(err, 4), ok=err < 0.01)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="solo baseline e convergenza")
    ap.add_argument("--resume", action="store_true", help="riusa nominale e mesh fine da fea/d031/pilot.json")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(stage="pilot", date=time.strftime("%Y-%m-%d"), h_nom=H_NOM, h_local=H_LOCAL, fine=FINE,
               balls=BALL_ANGLES, d028=d028_local(), variants={})
    res["self_test"] = self_test()
    print("autotest molle", res["self_test"], flush=True)
    if args.resume:
        old = json.loads((OUT / "pilot.json").read_text())
        base, fine = old["nominal"], old["fine"]
    else:
        base = solve("pilot_nom", H_NOM)
        print("nominale", base["mesh"], base["solve_s"], "s", flush=True)
        fine = solve("pilot_fine", H_NOM * FINE, cases=UNIT[:3])
        print("fine", fine["mesh"], fine["solve_s"], "s", flush=True)
    conv = {}
    for c in ("Fx", "Fy", "Fz"):
        a, b = base["cases"][c]["tip_abs_um"], fine["cases"][c]["tip_abs_um"]
        conv[c] = dict(nom=a, fine=b, delta=round(abs(a - b) / b, 4))
    res.update(nominal=base, fine=fine, convergence=conv, converged=all(v["delta"] < CONV_LIMIT for v in conv.values()))
    print("convergenza", conv, "→", res["converged"], flush=True)
    for tag, desc, kw in ([] if args.quick else VARIANTS):
        r = base if tag == "master_w8" else solve(tag, H_NOM, **kw)
        r["desc"] = desc
        res["variants"][tag] = r
        k = [r["cases"][c]["k_N_um"] for c in ("Fx", "Fy", "Fz")]
        print(f"{tag:12} massa {r['mass']} k {k} peak {r['cases']['FxFz']['vm_peak']['MPa']} MPa", flush=True)
    (OUT / "pilot.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    try:
        import d031_page
        d031_page.write(res)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
