#!/usr/bin/env python3
"""Pipeline FEA lineare statica D031: solidi CadQuery → mesh Gmsh (tetra quadratici) → .inp CalculiX → risultati.

Unità: mm, N, MPa. Pensata per modelli piccoli (componenti e sottoassiemi del mule Standard):
- volumi dello stesso "corpo" condividono i nodi (fragment Gmsh = incollati); corpi diversi hanno mesh separate
  e si collegano solo con molle, corpi rigidi ed equazioni;
- corpi rigidi su patch di nodi (REF NODE per le traslazioni, ROT NODE per le rotazioni, come in CalculiX);
- molle lineari SPRING2 tra gradi di libertà globali, anche rotazionali (DOF dei ROT NODE);
- molle in una direzione qualsiasi del piano XY con nodi ausiliari ed *EQUATION.
Richiede gmsh (pip) e ccx (CalculiX) nel PATH.
"""
import math
import pathlib
import subprocess
import time

import numpy as np

MATERIALS = {  # proprietà elastiche effettive; lega e stato non ancora scelti (D031)
    "AL": dict(E=70000.0, nu=0.33, rho=2.70e-6),
    "STEEL": dict(E=210000.0, nu=0.30, rho=7.85e-6),
    "RIGID": dict(E=7.0e7, nu=0.30, rho=2.70e-6),      # solo diagnostica: parte "infinitamente" rigida
}
POOR_SJ = 0.2                                        # tetra quadratici sotto questa qualità: tensioni nodali inaffidabili
GMSH_TO_CCX_TET10 = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]   # Gmsh e Abaqus/CalculiX differiscono sugli ultimi due nodi di spigolo


class Model:
    def __init__(self, name, workdir):
        self.name = name
        self.dir = pathlib.Path(workdir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.bodies = []            # (nome, [shape cadquery], materiale)
        self.refine = []            # (x, y, z, raggio, h) zone di infittimento
        self.extra_nodes = {}       # id → (x, y, z)
        self.rigid = []             # (nome, node_ids, ref, rot)
        self.springs = []           # (nome, n1, dof1, n2, dof2, k)
        self.equations = []         # [(nodo, dof, coeff), ...]
        self.spc = []               # (nodo, dof)
        self.fixed_sets = []        # (nome, node_ids) tutti i gdl bloccati
        self.steps = []             # (nome, [(nodo, dof, valore)])
        self.next_id = None

    # ------------------------------------------------------------------ geometria e mesh
    def body(self, name, shapes, material):
        self.bodies.append((name, shapes if isinstance(shapes, list) else [shapes], material))

    def refine_at(self, x, y, z, r, h):
        self.refine.append((x, y, z, r, h))

    def mesh(self, h, order=2, verbose=False):
        import gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
        gmsh.model.add(self.name)
        self.body_vols = {}
        for name, shapes, _ in self.bodies:
            tags = []
            for i, sh in enumerate(shapes):
                f = self.dir / f"{name}_{i}.brep"
                sh.exportBrep(str(f))
                tags += [t for d, t in gmsh.model.occ.importShapes(str(f)) if d == 3]
            if len(tags) > 1:
                out, _ = gmsh.model.occ.fragment([(3, t) for t in tags[:1]], [(3, t) for t in tags[1:]])
                tags = [t for d, t in out if d == 3]
            self.body_vols[name] = tags
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeMin", h / 4)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        fields = []
        for (x, y, z, r, hl) in self.refine:
            fid = gmsh.model.mesh.field.add("Ball")
            gmsh.model.mesh.field.setNumber(fid, "XCenter", x)
            gmsh.model.mesh.field.setNumber(fid, "YCenter", y)
            gmsh.model.mesh.field.setNumber(fid, "ZCenter", z)
            gmsh.model.mesh.field.setNumber(fid, "Radius", r)
            gmsh.model.mesh.field.setNumber(fid, "Thickness", r)
            gmsh.model.mesh.field.setNumber(fid, "VIn", hl)
            gmsh.model.mesh.field.setNumber(fid, "VOut", h)
            fields.append(fid)
        box = getattr(self, "box_size", None)       # (x0, x1, y0, y1, z0, z1, h): zona a mesh fine, grossa (h globale) fuori
        if box:
            fid = gmsh.model.mesh.field.add("Box")
            for k_, v_ in zip(("XMin", "XMax", "YMin", "YMax", "ZMin", "ZMax", "VIn"), box):
                gmsh.model.mesh.field.setNumber(fid, k_, v_)
            gmsh.model.mesh.field.setNumber(fid, "VOut", h)
            gmsh.model.mesh.field.setNumber(fid, "Thickness", 20.0)
            fields.append(fid)
        if fields:
            fmin = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(fmin, "FieldsList", fields)
            gmsh.model.mesh.field.setAsBackgroundMesh(fmin)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)          # HXT, multithread
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("Netgen")
        gmsh.model.mesh.setOrder(order)                         # nodi di spigolo sulla geometria reale
        gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
        gmsh.model.mesh.optimize("HighOrderElastic")           # raddrizza i tetra quadratici distorti sulle superfici curve
        gmsh.model.mesh.optimize("HighOrder")
        tags, coords, _ = gmsh.model.mesh.getNodes()
        self.nodes = dict(zip(tags.astype(int), coords.reshape(-1, 3)))
        self.elements = {}          # corpo → (ids, conn ccx)
        self.body_nodes = {}
        eid = 1
        self.quality = {}
        for name, vols in self.body_vols.items():
            conns, quals = [], []
            for v in vols:
                et, _, en = gmsh.model.mesh.getElements(3, v)
                for t, n in zip(et, en):
                    if t != 11:                                     # 11 = tetra a 10 nodi
                        raise SystemExit(f"elemento Gmsh inatteso {t} in {name}")
                    conns.append(n.astype(int).reshape(-1, 10)[:, GMSH_TO_CCX_TET10])
                    etags = gmsh.model.mesh.getElements(3, v)[1][0]
                    quals.append(np.array(gmsh.model.mesh.getElementQualities(etags, "minSJ")))
            conn = np.vstack(conns)
            ids = np.arange(eid, eid + len(conn))
            eid += len(conn)
            self.elements[name] = (ids, conn)
            self.quality[name] = np.concatenate(quals)            # Jacobiano scalato minimo per elemento
            self.body_nodes[name] = np.unique(conn)
        gmsh.finalize()
        self.next_id = max(self.nodes) + 1
        self.n_elem = eid - 1
        allq = np.concatenate(list(self.quality.values()))
        return dict(nodes=len(self.nodes), elements=self.n_elem, dof=3 * len(self.nodes),
                    min_sj=round(float(allq.min()), 3), poor=int((allq < POOR_SJ).sum()))

    def poor_nodes(self):
        """Nodi degli elementi con Jacobiano scalato < POOR_SJ: esclusi dalla tensione hotspot."""
        out = [c[self.quality[n] < POOR_SJ].ravel() for n, (_, c) in self.elements.items() if n in self.quality]
        return np.unique(np.concatenate(out)) if out else np.array([], int)

    # ------------------------------------------------------------------ selezioni
    def xyz(self, ids):
        return np.array([self.nodes[i] for i in ids])

    def select(self, body, fn):
        """Nodi del corpo per cui fn(x, y, z) è vera (vettoriale)."""
        ids = self.body_nodes[body]
        p = self.xyz(ids)
        return ids[fn(p[:, 0], p[:, 1], p[:, 2])]

    def node(self, x, y, z):
        i = self.next_id
        self.next_id += 1
        self.extra_nodes[i] = (x, y, z)
        return i

    # ------------------------------------------------------------------ vincoli, molle, carichi
    def rigid_body(self, name, ids, at):
        if len(ids) < 3:
            raise SystemExit(f"patch {name}: solo {len(ids)} nodi")
        ref, rot = self.node(*at), self.node(*at)
        self.rigid.append((name, ids, ref, rot))
        return ref, rot

    def spring(self, name, n1, d1, n2, d2, k):
        self.springs.append((name, n1, d1, n2, d2, k))

    def spring6(self, name, a, b, k6):
        """Molla a 6 gdl tra due corpi rigidi a=(ref, rot), b=(ref, rot): k6 = [kx, ky, kz, krx, kry, krz]."""
        for d in range(3):
            if k6[d] > 0:
                self.spring(f"{name}_t{d + 1}", a[0], d + 1, b[0], d + 1, k6[d])
            if k6[d + 3] > 0:
                self.spring(f"{name}_r{d + 1}", a[1], d + 1, b[1], d + 1, k6[d + 3])

    def spring_dir(self, name, na, nb, direction, k):
        """Molla lungo una direzione (dx, dy, dz) tra le traslazioni di due nodi, con nodi ausiliari ed equazioni."""
        d = np.array(direction, float) / np.linalg.norm(direction)
        aux = []
        for n in (na, nb):
            t = self.node(*(self.extra_nodes.get(n) or self.nodes[n]))
            self.equations.append([(t, 1, -1.0)] + [(n, j + 1, d[j]) for j in range(3) if abs(d[j]) > 1e-12])
            self.spc += [(t, 2), (t, 3)]
            aux.append(t)
        self.spring(name, aux[0], 1, aux[1], 1, k)

    def fix(self, name, ids):
        self.fixed_sets.append((name, ids))

    def step(self, name, loads):
        """loads: [(nodo, dof, valore)]; forze sui REF NODE, momenti (N·mm) sui ROT NODE."""
        self.steps.append((name, loads))

    # ------------------------------------------------------------------ scrittura, soluzione, lettura
    def write(self, monitor):
        f = self.dir / f"{self.name}.inp.new"
        L = ["*HEADING", f"MultiCNC D031 {self.name}", "*NODE"]
        L += [f"{i},{x:.6f},{y:.6f},{z:.6f}" for i, (x, y, z) in self.nodes.items()]
        L += [f"{i},{x:.6f},{y:.6f},{z:.6f}" for i, (x, y, z) in self.extra_nodes.items()]
        for name, (ids, conn) in self.elements.items():
            L.append(f"*ELEMENT, TYPE=C3D10, ELSET=E_{name}")
            for e, c in zip(ids, conn):
                L.append(f"{e}," + ",".join(str(n) for n in c[:8]) + ",")
                L.append(",".join(str(n) for n in c[8:]))
        eid = self.n_elem + 1
        for (sname, n1, d1, n2, d2, k) in self.springs:
            L += [f"*ELEMENT, TYPE=SPRING2, ELSET=S_{sname}", f"{eid},{n1},{n2}", f"*SPRING, ELSET=S_{sname}", f"{d1},{d2}", f"{k:.6e}"]
            eid += 1
        for m in {b[2] for b in self.bodies}:
            p = MATERIALS[m]
            L += [f"*MATERIAL, NAME={m}", "*ELASTIC", f"{p['E']},{p['nu']}"]
        for name, _, m in self.bodies:
            L.append(f"*SOLID SECTION, ELSET=E_{name}, MATERIAL={m}")
        for (name, ids, ref, rot) in self.rigid:
            L.append(f"*NSET, NSET=R_{name}")
            L += [",".join(str(i) for i in ids[j:j + 12]) for j in range(0, len(ids), 12)]
            L.append(f"*RIGID BODY, NSET=R_{name}, REF NODE={ref}, ROT NODE={rot}")
        if self.equations:
            L.append("*EQUATION")
            for eq in self.equations:
                L.append(str(len(eq)))
                L.append(",".join(f"{n},{d},{c:.9f}" for n, d, c in eq))
        L.append("*NSET, NSET=MONITOR")
        L.append(",".join(str(n) for n in monitor))
        L.append("*BOUNDARY")
        for (name, ids) in self.fixed_sets:
            L += [f"{i},1,3" for i in ids]
        L += [f"{n},{d},{d}" for n, d in self.spc]
        for sname, loads in self.steps:
            L += ["*STEP", "*STATIC", "*CLOAD, OP=NEW"]
            L += [f"{n},{d},{v:.6e}" for n, d, v in loads]
            L += ["*NODE PRINT, NSET=MONITOR", "U", "*NODE FILE", "U", "*EL FILE", "S", "*END STEP"]
        f.write_text("\n".join(L) + "\n")
        return f

    def run(self, monitor, threads=4):
        new = self.write(monitor)
        inp = self.dir / f"{self.name}.inp"
        frd = self.dir / f"{self.name}.frd"
        t0 = time.time()
        if inp.exists() and frd.exists() and inp.read_bytes() == new.read_bytes():   # stessa mesh e stessi carichi: riusa
            new.unlink()
            self.solve_s = float((self.dir / "solve_s.txt").read_text()) if (self.dir / "solve_s.txt").exists() else 0.0
            return self.read_dat(), self.read_frd()
        new.replace(inp)
        env = {"OMP_NUM_THREADS": str(threads), "CCX_NPROC_EQUATION_SOLVER": str(threads), "PATH": "/usr/bin:/bin"}
        r = subprocess.run(["ccx", "-i", self.name], cwd=self.dir, capture_output=True, text=True, env=env)
        if r.returncode != 0 or "ERROR" in r.stdout:
            raise SystemExit("CalculiX:\n" + r.stdout[-3000:] + r.stderr[-2000:])
        self.solve_s = round(time.time() - t0, 1)
        (self.dir / "solve_s.txt").write_text(str(self.solve_s))
        return self.read_dat(), self.read_frd()

    def read_dat(self):
        """Spostamenti dei nodi MONITOR per ogni step: {step: {nodo: (ux, uy, uz)}}."""
        out, cur, k = {}, None, 0
        for line in (self.dir / f"{self.name}.dat").read_text().splitlines():
            if line.strip().startswith("displacements"):
                cur = self.steps[k][0]
                out[cur] = {}
                k += 1
                continue
            parts = line.split()
            if cur and len(parts) == 4:
                try:
                    out[cur][int(parts[0])] = tuple(float(v) for v in parts[1:])
                except ValueError:
                    pass
        return out

    def read_frd(self):
        """Tensori delle tensioni nodali per step: {step: (id nodi, array n × 6 [sx, sy, sz, txy, tyz, tzx])}
        (estrapolate ai nodi e mediate da CalculiX). Lineari: si sommano tra step per i casi combinati."""
        res, k, block, ids, vals = {}, 0, None, [], []
        for line in open(self.dir / f"{self.name}.frd"):
            if line.startswith(" -4  STRESS"):
                block, ids, vals = self.steps[k][0], [], []
                k += 1
                continue
            if block is None:
                continue
            if line.startswith(" -3"):
                res[block] = (np.array(ids), np.array(vals))
                block = None
                continue
            if line.startswith(" -1"):
                ids.append(int(line[3:13]))
                vals.append([float(line[13 + 12 * j:25 + 12 * j]) for j in range(6)])
        return res

    @staticmethod
    def von_mises(s):
        sx, sy, sz, txy, tyz, tzx = s.T
        return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + tyz ** 2 + tzx ** 2))

    def body_mass(self, name):
        """Massa del corpo dalla mesh (volume dei tetra × densità), kg."""
        ids, conn = self.elements[name]
        p = self.xyz(conn[:, :4].ravel()).reshape(-1, 4, 3)
        v = np.abs(np.einsum("ij,ij->i", np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), p[:, 3] - p[:, 0])) / 6
        mat = next(m for n, _, m in self.bodies if n == name)
        return float(v.sum() * MATERIALS[mat]["rho"])
