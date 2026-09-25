#!/usr/bin/env python3
"""Risultati FEA D031 in 3D per il visualizzatore web (base/viewer-3d.html).

Uso (dalla radice): python tools/fea/export_results.py
Legge i .frd di CalculiX in build/fea/<tag>/ (prodotti da d031.py e d031_z.py), estrae la superficie esterna della
mesh (tetra quadratici: per le tensioni facce a 6 nodi divise in 4 triangoli con i nodi di metà spigolo, per gli
spostamenti solo i vertici come anteprima leggera), applica la deformata amplificata e colora i vertici con lo spostamento |u| (µm) o la tensione di Von Mises
(MPa). Scrive fea/d031/glb/<tag>_<caso>_<campo>.glb e fea/d031/glb/index.json (elenco, scale, intervalli).
Richiede numpy e trimesh.
"""
import json
import pathlib
from collections import Counter

import numpy as np
import trimesh

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = ROOT / "build" / "fea"
OUT = ROOT / "fea" / "d031" / "glb"
SCALE = 150.0                              # amplificazione della deformata
# scala sequenziale a una tinta, chiaro → scuro (valore basso → alto)
RAMP = np.array([[0.99, 0.95, 0.86], [0.99, 0.80, 0.55], [0.96, 0.55, 0.26], [0.84, 0.29, 0.13], [0.55, 0.10, 0.07]])

RUNS = [  # (tag, nomi degli step nell'ordine del .frd, titolo, [(caso, campo)])
    ("pilot_nom", ["Fx", "Fy", "Fz", "Mx", "My", "REL"], "Pilota · master + testa (slitta rigida)",
     [("Fx", "u"), ("Fy", "u"), ("Fz", "u"), ("Fy", "vm")]),
    ("z_strip", ["Fx", "Fy", "Fz", "REL"], "Slitta Z · striscia 12 mm (mule v2)", [("Fy", "u"), ("Fz", "u"), ("Fy", "vm")]),
    ("z_flange", ["Fx", "Fy", "Fz", "REL"], "Slitta Z · flangia posteriore 50 mm", [("Fy", "u")]),
    ("z_saddle", ["Fx", "Fy", "Fz", "REL"], "Slitta Z · sella a U sulle ali", [("Fy", "u"), ("Fz", "u")]),
    ("z_both", ["Fx", "Fy", "Fz", "REL"], "Slitta Z · flangia + sella", [("Fy", "u"), ("Fz", "u"), ("Fy", "vm")]),
    ("z_saddle_tab16", ["Fx", "Fy", "Fz", "REL"], "Mule v3 · sella + piastrina chiocciola 16 mm", [("Fy", "u"), ("Fz", "u"), ("Fy", "vm"), ("REL", "vm")]),
]
CASE = {"Fx": "150 N radiale X", "Fy": "150 N radiale Y", "Fz": "200 N assiale Z", "Mx": "18 N·m attorno a X",
        "My": "18 N·m attorno a Y", "REL": "0,7 kN di sgancio"}
FIELD = {"u": ("spostamento |u|", "µm"), "vm": ("tensione di Von Mises", "MPa")}


def read_frd(path, steps):
    """Nodi, tetraedri (4 vertici) e, per step, spostamenti e tensioni nodali."""
    nodes, elems, disp, stress = {}, [], {}, {}
    mode, k_d, k_s, cur, pending = None, 0, 0, None, None
    with open(path) as f:
        for line in f:
            if line.startswith("    2C"):
                mode = "n"
                continue
            if line.startswith("    3C"):
                mode = "e"
                continue
            if line.startswith(" -4  DISP"):
                mode, cur = "d", {}
                disp[steps[k_d]] = cur
                k_d += 1
                continue
            if line.startswith(" -4  STRESS"):
                mode, cur = "s", {}
                stress[steps[k_s]] = cur
                k_s += 1
                continue
            if line.startswith(" -3"):
                mode = None
                continue
            if mode == "n" and line.startswith(" -1"):
                nodes[int(line[3:13])] = (float(line[13:25]), float(line[25:37]), float(line[37:49]))
            elif mode == "e":
                if line.startswith(" -1"):
                    pending = int(line.split()[2])            # tipo elemento (6 = tetra a 10 nodi)
                elif line.startswith(" -2") and pending == 6:
                    ids = [int(v) for v in line.split()[1:]]
                    elems.append(ids[:10])                   # C3D10: 4 vertici + 6 nodi di metà spigolo
                    pending = None
            elif mode in ("d", "s") and line.startswith(" -1"):
                n = int(line[3:13])
                cnt = 3 if mode == "d" else 6
                cur[n] = [float(line[13 + 12 * j:25 + 12 * j]) for j in range(cnt)]
    return nodes, np.array(elems), disp, stress


# facce del tetra quadratico (ordine CalculiX: 4 vertici, poi 0-1, 1-2, 2-0, 0-3, 1-3, 2-3), normale uscente:
# (a, b, c, ab, bc, ca)
TET10_FACES = [[0, 2, 1, 6, 5, 4], [0, 1, 3, 4, 8, 7], [1, 2, 3, 5, 9, 8], [0, 3, 2, 7, 9, 6]]


def surface_linear(tets):
    """Solo i triangoli d'angolo delle facce esterne: anteprima leggera per le mappe di spostamento."""
    faces = np.vstack([tets[:, f[:3]] for f in TET10_FACES])
    key = np.sort(faces, axis=1)
    cnt = Counter(map(tuple, key))
    return faces[np.array([cnt[tuple(k)] == 1 for k in key])]


def surface(tets):
    """Facce esterne della mesh C3D10 (quelle che compaiono una volta sola), ciascuna a 6 nodi divisa in 4 triangoli
    con i nodi di metà spigolo: la superficie mostrata usa tutti i nodi del tetra quadratico, non solo i vertici."""
    faces = np.vstack([tets[:, f] for f in TET10_FACES])
    key = np.sort(faces[:, :3], axis=1)
    cnt = Counter(map(tuple, key))
    f6 = faces[np.array([cnt[tuple(k)] == 1 for k in key])]
    a, b, c, ab, bc, ca = f6.T
    return np.vstack([np.c_[a, ab, ca], np.c_[ab, b, bc], np.c_[ca, bc, c], np.c_[ab, bc, ca]])


def colors(v, lo, hi):
    t = np.clip((v - lo) / max(hi - lo, 1e-12), 0, 1) * (len(RAMP) - 1)
    i = np.minimum(t.astype(int), len(RAMP) - 2)
    f = (t - i)[:, None]
    c = RAMP[i] * (1 - f) + RAMP[i + 1] * f
    return np.hstack([(c * 255).astype(np.uint8), np.full((len(v), 1), 255, np.uint8)])


def vm(s):
    s = np.asarray(s)
    sx, sy, sz, txy, tyz, tzx = s.T
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def gantry_runs():
    """Deformate del gantry FEA (fase 3): la mesh più fine in fea/d031/gantry.json."""
    f = ROOT / "fea" / "d031" / "gantry.json"
    if not f.exists():
        return []
    runs = json.loads(f.read_text())["runs"].values()
    best = min(runs, key=lambda v: (v["hc"], v["h"]))
    return [(best["tag"], ["Fx", "Fy", "Fz"], "Gantry mule v3 · spalle, trave, carrello, slitta, testa", [("Fx", "u"), ("Fy", "u"), ("Fz", "u"), ("Fy", "vm")])]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for tag, steps, title, wanted in RUNS + gantry_runs():
        frd = WORK / tag / f"{tag}.frd"
        if not frd.exists():
            print("manca", frd)
            continue
        nodes, tets, disp, stress = read_frd(frd, steps)
        surf = {"vm": surface(tets), "u": surface_linear(tets)}     # tensioni: facce quadratiche complete
        for case, field in wanted:
            tri = surf[field]
            used = np.unique(tri)
            remap = {n: i for i, n in enumerate(used)}
            faces = np.vectorize(remap.get)(tri)
            X = np.array([nodes[n] for n in used])
            U = np.array([disp[case].get(n, (0, 0, 0)) for n in used])
            val = np.linalg.norm(U, axis=1) * 1000.0 if field == "u" else vm([stress[case].get(n, (0,) * 6) for n in used])
            lo, hi = 0.0, float(np.percentile(val, 99.5) if field == "vm" else val.max())
            mesh = trimesh.Trimesh(vertices=X + SCALE * U, faces=faces, vertex_colors=colors(val, lo, hi), process=False)
            name = f"{tag}_{case}_{field}.glb"
            mesh.export(OUT / name)
            index.append(dict(file=name, title=title, case=CASE[case], field=FIELD[field][0], unit=FIELD[field][1],
                              lo=round(lo, 2), hi=round(hi, 2), max=round(float(val.max()), 2), scale=SCALE,
                              saturated="99,5° percentile" if field == "vm" else None,
                              surface="quadratica (6 nodi per faccia)" if field == "vm" else "lineare (vertici)",
                              ramp=[[round(float(c), 3) for c in r] for r in RAMP]))
            print(name, f"{(OUT / name).stat().st_size / 1e6:.1f} MB", round(hi, 2), FIELD[field][1])
    (OUT / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
