#!/usr/bin/env python3
"""Base Standard · esportazione dei pezzi custom di dettaglio (uno STEP per pezzo e uno per riga BOM).

Uso (dalla radice, con CadQuery e Pillow): python tools/cad/standard_parts.py
Costruisce l'assieme HOME con le lavorazioni di standard_detail.py e scrive:
- cad/standard/parts/<BOM>_<pezzo>.step (coordinate locali: angolo minimo del pezzo nell'origine);
- cad/standard/parts/<BOM>.step (tutti i pezzi della riga, nelle coordinate macchina HOME);
- cad/standard/parts/views/<pezzo>.png (isometrica + pianta), cad/standard/parts/manifest.json;
- la pagina base/cad-parts.html (generata: non modificarla a mano).
Gli accessori (rialzi, magazine, cabina) vengono da standard_accessories.py se presente.
"""
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import cadquery as cq  # noqa: E402

import base_select  # noqa: E402,F401  (--base light|standard|pro)
import standard_assembly as A  # noqa: E402
import standard_params as P  # noqa: E402

OUT = ROOT / "cad" / P.FILE_PREFIX / "parts"
PAGE = ROOT / "base" / ("cad-parts.html" if P.BASE == "standard" else f"cad-{P.FILE_PREFIX}-parts.html")
STEEL_RHO = 7.85e-6
# pezzi custom in acciaio (nell'assieme hanno kind "commercial" perché la loro massa sta nella riga BOM del clamp)
MADE_STEEL = ("td_pull_stud", "td_clamp_piston", "td_release_rod", "td_release_lever", "td_cam_shaft", "td_cam_lever")
PROCESS = [  # (prefisso, materiale, lavorazione) · MULE: da confermare con il fornitore
    ("frame_", "EN AW-6082 T6, tubi 40 × 60 / 120 × 60 sp. 4", "saldato TIG, distensionato, fresato su pad, sedi guide Y e facce spalle"),
    ("upright_", "EN AW-6082 T6, piatti 6 + flangia 16", "saldato e fresato; fori spine Ø10 H7 alesati"),
    ("beam", "EN AW-6082 T6, piatti 6 + blocchi pieni", "saldato, distensionato, fresato su faccia guide X e canale vite"),
    ("x_carriage", "EN AW-6082 T651, piastra 60", "fresato dal pieno (piastra 15 + ali + torre)"),
    ("z_slide", "EN AW-6082 T651, piastra 50", "fresato dal pieno"),
    ("tooldock_master", "EN AW-7075 T651", "fresato; sedi rulli rettificate, piano di accoppiamento lappato"),
    ("head_receiver", "EN AW-7075 T651", "fresato; sedi sfere e piano di accoppiamento lappati"),
    ("head_mount", "EN AW-6082 T6", "tornito e fresato; Ø45 H6 alesato, gole O-ring"),
    ("table", "EN AW-5083 piastra rettificata 10", "fresata: tasche fra i boss, sedi inserti M6, boccole R1/R2"),
    ("td_clamp_housing", "EN AW-7075 T651", "tornito"),
    ("td_lever_post", "EN AW-7075 T651", "fresato"),
    ("td_pull_stud", "42CrMo4 bonificato", "tornito e rettificato; comune a tutte le teste (ICD v4)"),
    ("td_clamp_piston", "100Cr6 temprato 60 HRC", "tornito e rettificato"),
    ("td_release_rod", "C45", "tornito"),
    ("td_release_lever", "C45 temprato a induzione sul rullo", "fresato"),
    ("", "EN AW-6082 T6", "fresato"),
]


def process(name):
    over = getattr(P, "PROCESS", {})          # materiali e lavorazioni della base (light_params.py, pro_params.py)
    return next((m, pr) for k, m, pr in [(k, *v) for k, v in over.items()] + PROCESS if name.startswith(k))


def custom_parts(a):
    return {n: p for n, p in a.parts.items() if p["kind"] == A.AL or n in MADE_STEEL}


def local(shape):
    b = shape.BoundingBox()
    return shape.moved(cq.Location(cq.Vector(-b.xmin, -b.ymin, -b.zmin))), b


def count_holes(shape):
    return sum(1 for f in shape.Faces() if f.geomType() == "CYLINDER")


def view(part, path):
    import render_views as R
    from PIL import Image
    R.VIEWS.setdefault("iso_back", ((1.0, -1.3, -0.9), (0, 0, 1)))
    ims = [R.render({"p": part}, v, size=300) for v in ("iso", "iso_back", "top")]
    w, h = sum(i.width for i in ims) + 40, max(i.height for i in ims)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    x = 0
    for i in ims:
        img.paste(i, (x, (h - i.height) // 2))
        x += i.width + 20
    img.save(path, optimize=True)


def main():
    t0 = time.time()
    (OUT / "views").mkdir(parents=True, exist_ok=True)
    a, _ = A.build(*P.CONFIGS["HOME"], "HOME")
    cp = custom_parts(a)
    rows, by_bom = [], {}
    for n, p in cp.items():
        sh = p["shape"]
        rho = STEEL_RHO if n in MADE_STEEL else P.AL_DENSITY
        loc, b = local(sh)
        f = f"{p['bom']}_{n}.step"
        rel = f"cad/{P.FILE_PREFIX}/parts"
        cq.exporters.export(cq.Workplane().add(loc), str(OUT / f))
        view(dict(p, shape=sh), OUT / "views" / f"{n}.png")
        mat, pr = process(n)
        rows.append(dict(part=n, bom=p["bom"], file=f"{rel}/{f}", view=f"{rel}/views/{n}.png",
                         size_mm=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], kg=round(sh.Volume() * rho, 3),
                         holes=count_holes(sh), material=mat, process=pr, home_min=[round(b.xmin, 1), round(b.ymin, 1), round(b.zmin, 1)]))
        by_bom.setdefault(p["bom"], []).append(n)
        print(n, p["bom"], rows[-1]["size_mm"], rows[-1]["kg"], "kg", rows[-1]["holes"], "fori", flush=True)
    files = {}
    for bom, names in by_bom.items():
        asm = cq.Assembly(name=bom)
        for n in names:
            asm.add(cq.Workplane().add(a.parts[n]["shape"]), name=n, color=cq.Color(*A.COLORS[a.parts[n]["color"]], 1.0))
        asm.save(str(OUT / f"{bom}.step"))
        files[bom] = f"cad/{P.FILE_PREFIX}/parts/{bom}.step"
    acc = []
    try:
        import standard_accessories as ACC
        acc = ACC.export(OUT)
    except ImportError:
        pass
    manifest = dict(generated_by="tools/cad/standard_parts.py", date=time.strftime("%Y-%m-%d"), rows=rows, bom_files=files,
                    accessories=acc, hardware=a.hardware, notes=a.notes)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_page(manifest)
    print("pezzi", len(rows), "righe BOM", len(files), f"{time.time() - t0:.0f} s")


def it(x, d=1):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def write_page(m):
    import importlib
    S = importlib.import_module(P.BOM_DATA)
    bom = {r[0]: r for _, rows in S.G for r in rows}
    groups = {}
    for r in m["rows"]:
        groups.setdefault(r["bom"], []).append(r)
    order = [i for _, rows in S.G for i, *_ in rows if i in groups]
    sec = ""
    for i in order:
        rs = groups[i]
        kg = sum(r["kg"] for r in rs)
        cards = ""
        for r in rs:
            cards += (f'<div class="panel" style="min-width:0"><img src="../{r["view"]}" alt="{r["part"]}" loading="lazy" style="width:100%;height:auto;border-radius:8px;background:#fff">'
                      f'<h3 style="margin:10px 0 4px;font-size:15px"><code>{r["part"]}</code></h3>'
                      f'<p style="color:var(--dim);font-size:13px;margin:0">{" × ".join(it(v, 0) for v in r["size_mm"])} mm · {it(r["kg"], 2)} kg · {r["holes"]} superfici cilindriche<br>{r["material"]}<br>{r["process"]}</p>'
                      f'<p style="margin:8px 0 0;font-size:13px"><a href="../{r["file"]}" download>STEP pezzo ↓</a></p></div>')
        name = bom[i][2] if i in bom else i
        sec += (f'<section class="section"><h2>{i} · {name}</h2><p style="color:var(--dim);font-size:13px">{len(rs)} pezzi · {it(kg, 2)} kg dal CAD'
                f'{(" · BOM " + it(bom[i][4] * bom[i][8], 2) + " kg") if i in bom else ""} · <a href="../{m["bom_files"][i]}" download>STEP della riga (coordinate HOME) ↓</a></p>'
                f'<div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px">{cards}</div></section>')
    acc = ""
    for r in m.get("accessories", []):
        acc += (f'<div class="panel" style="min-width:0"><img src="../{r["view"]}" alt="{r["part"]}" loading="lazy" style="width:100%;height:auto;border-radius:8px;background:#fff">'
                f'<h3 style="margin:10px 0 4px;font-size:15px">{r["bom"]} · {r["title"]}</h3><p style="color:var(--dim);font-size:13px;margin:0">{r["note"]}<br>'
                f'{" × ".join(it(v, 0) for v in r["size_mm"])} mm · {(it(r["kg"], 1) + " kg") if r["kg"] is not None else "massa n.d. (solidi di layout)"}</p><p style="margin:8px 0 0;font-size:13px"><a href="../{r["file"]}" download>STEP ↓</a></p></div>')
    if acc:
        acc = f'<section class="section"><h2>Accessori (fuori dai totali)</h2><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px">{acc}</div></section>'
    hw = "".join(f'<tr><td>{h["std"]}</td><td>{h["item"]}</td><td>{h["qty"]}</td><td>{h["where"]}</td></tr>' for h in m["hardware"])
    n_hw = sum(h["qty"] for h in m["hardware"])
    notes = "".join(f"<li>{n}</li>" for n in m["notes"])
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — CAD pezzi · {P.BASE_LABEL}</title><link rel="stylesheet" href="../assets/styles.css"></head><body><main class="shell page">
<!-- Pagina generata da tools/cad/standard_parts.py: non modificare a mano. -->
<a class="back" href="cad-{P.FILE_PREFIX}.html">← CAD {P.BASE_LABEL}</a>
<div class="pagehead"><div class="eyebrow">02 · Base {P.BASE_LABEL} · CAD di dettaglio</div><h1>I pezzi<br>della {P.BASE_LABEL}.</h1><p class="lead">Ogni pezzo custom della {P.BASE_LABEL} con le lavorazioni che lo collegano ai vicini: fori delle guide e dei pattini, supporti delle viti, flange delle chiocciole, motori, interfaccia spalla ICD v4, ToolDock (rulli, sfere, pull-stud, clamp, porte e connettori). Le quote vengono dagli stessi parametri del mule e dalle posizioni reali dei componenti commerciali: un pezzo cambia solo cambiando <code>{P.BASE}_params.py</code> o <code>standard_detail.py</code>.</p><div class="badges"><span class="badge ok">{len(m["rows"])} pezzi</span><span class="badge">{n_hw} elementi di viteria</span><span class="badge">{P.BASE_LABEL} · ICD v4</span><span class="badge">MULE · TARGET</span></div></div>
<section class="section"><div class="callout"><b>Scelte di dettaglio.</b><ul style="margin:8px 0 0">{notes}</ul></div></section>
{sec}{acc}
<section class="section"><h2>Viteria e minuteria</h2><p style="color:var(--dim);font-size:13px">Compilata dalle lavorazioni (riga BOM MC-HW-001). Lunghezze MULE, da verificare in assieme reale.</p><div class="table-wrap"><table><tr><th>Norma</th><th>Articolo</th><th>Q.tà</th><th>Dove</th></tr>{hw}</table></div></section>
<section class="section"><h2>Rigenerare</h2><p><code>python tools/cad/standard_parts.py{"" if P.BASE == "standard" else " --base " + P.BASE}</code> (poi <code>standard_assembly.py</code> per assieme, controlli e pagina CAD). STEP in coordinate locali: angolo minimo del pezzo nell'origine; lo STEP di ogni riga BOM tiene le coordinate macchina in HOME.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools" / "bom"))
    main()
