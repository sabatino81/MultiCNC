#!/usr/bin/env python3
"""D032 · pagina base/fea-d032.html: matrice dei concept del mule Standard (CAD + FEA del gantry).

Uso (dalla radice): python tools/fea/d032_page.py
Legge cad/standard/report.json (mule v3 = A0), cad/concepts/<nome>/report.json (sweep, trasferitore, masse),
fea/d032/<nome>.json (gantry FEA con energia) e fea/d031/gantry.json (resto macchina D028: telaio, tavola, asse Y).
Non modificare a mano la pagina.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools" / "cad"))
PAGE = ROOT / "base" / "fea-d032.html"
SERVICE = dict(XY=80.0, Z=150.0)                   # D032 SERVICE HIGH (PROVISIONAL)
T_MIN = dict(XY=4.0, Z=7.5)
T_DES = dict(XY=6.0, Z=8.0)
GATE = dict(XY=3.0, Z=4.0, kg=42.0)
ORDER = ["A0", "A1s", "A1", "A2", "A3", "A4", "B", "C"]   # A1 resta come variante diagnostica (upper bound)
EN = [("zslide", "slitta Z + master"), ("tooldock", "ToolDock"), ("carriage", "carrello X"), ("head", "testa"), ("beam", "trave"),
      ("uprights", "spalle"), ("zblocks", "pattini Z"), ("xblocks", "pattini X"), ("zscrew", "vite Z"), ("xscrew", "vite X"), ("bearing", "cuscinetti")]


def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load():
    import standard_concepts as SC
    rest = json.loads((ROOT / "fea" / "d031" / "gantry.json").read_text())["d028"]
    rows = []
    for name in ORDER:
        f = ROOT / "fea" / "d032" / f"{name}.json"
        if not f.exists():
            continue
        fea = json.loads(f.read_text())
        cadf = ROOT / ("cad/standard/report.json" if name == "A0" else f"cad/concepts/{name}/report.json")
        cad = json.loads(cadf.read_text()) if cadf.exists() else None
        k = {ax: fea["k"][n] for ax, n in zip("XYZ", ("Fx", "Fy", "Fz"))}
        mach = {ax: 1.0 / (rest[ax]["rest"] + 1.0 / k[ax]) for ax in "XYZ"}
        rows.append(dict(name=name, desc=SC.CONCEPTS.get(name, {}).get("desc", name), k=k, mach=mach, fea=fea, cad=cad))
    return rows


def write(rows):
    base = next((r for r in rows if r["name"] == "A0"), rows[0])
    m0 = base["cad"]["mass"]["machine_mule_kg"] if base["cad"] else None
    body = ""
    for r in rows:
        cad = r["cad"]
        mass = cad["mass"]["machine_mule_kg"] if cad else None
        kxy = min(r["mach"]["X"], r["mach"]["Y"])
        dxy, dz = SERVICE["XY"] / kxy, SERVICE["Z"] / r["mach"]["Z"]
        sweep = (f'{len(cad["sweep"]["collisions"])} · {len(cad["sweep"]["fails"])} · {len(cad["sweep"]["warnings"])}' if cad else "—")
        trans = (f'{it(cad["transfer"]["closest"][0]["clearance_mm"], 0)} mm' if cad and cad["transfer"]["closest"] else "—")
        gate = kxy >= GATE["XY"] and r["mach"]["Z"] >= GATE["Z"] and mass is not None and mass <= GATE["kg"]
        dkg = (mass - m0) if (mass is not None and m0 is not None) else None
        gain = (kxy - min(base["mach"]["X"], base["mach"]["Y"])) / dkg if dkg and dkg > 0.05 else None
        to42 = (mass - GATE["kg"]) if mass is not None else None
        # quota del margine slitta + master (energia in Y di A0) recuperata: cedevolezza tolta in Y / quota A0
        c0, c1 = 1.0 / base["k"]["Y"], 1.0 / r["k"]["Y"]
        share0 = base["fea"]["energy"]["Fy"].get("zslide", 0.0) / base["fea"]["work"]["Fy"]
        rec = (c0 - c1) / (c0 * share0) if share0 else None
        rec100 = rec / (dkg * 10.0) if rec is not None and dkg and dkg > 0.05 else None
        body += (f'<tr><td>{r["desc"]}</td><td>{" / ".join(it(r["k"][a], 2) for a in "XYZ")}</td><td><b>{" / ".join(it(r["mach"][a], 2) for a in "XYZ")}</b></td>'
                 f'<td class="{"status-ok" if dxy <= 20 else "status-critical"}">{it(dxy, 0)} µm</td><td class="{"status-ok" if dz <= 20 else "status-critical"}">{it(dz, 0)} µm</td>'
                 f'<td>{it(mass, 1) + " kg" if mass is not None else "—"}</td><td>{("+" if dkg and dkg > 0 else "") + it(dkg, 2) + " kg" if dkg is not None else "—"}</td>'
                 f'<td>{it(to42, 1) + " kg" if to42 is not None else "—"}</td>'
                 f'<td>{it(gain, 2) if gain is not None else "—"}</td>'
                 f'<td>{(it(rec * 100, 0) + "%") if rec is not None and r is not base else "—"}{(" · " + it(rec100 * 100, 0) + "% / 100 g") if rec100 is not None else ""}</td>'
                 f'<td>{sweep}</td><td>{trans}</td>'
                 f'<td class="{"status-ok" if gate else "status-critical"}">{"PASSA" if gate else "NO"}</td></tr>')
    ref = json.loads((ROOT / "fea" / "d031" / "gantry.json").read_text())["runs"].get("gantry_h6_c12", {}).get("k")
    nonreg = ""
    if ref and base["name"] == "A0":
        dd = max(abs(base["k"][a] - ref[n]) / ref[n] for a, n in zip("XYZ", ("Fx", "Fy", "Fz")))
        nonreg = (f'<p style="margin-top:10px"><b>Non-regressione A0</b>: gantry {" / ".join(it(base["k"][a], 3) for a in "XYZ")} N/µm contro la baseline D031 6 / 12 '
                  f'{" / ".join(it(ref[n], 3) for n in ("Fx", "Fy", "Fz"))}: scarto massimo {it(dd * 100, 2)}% ({"PASSA" if dd < 0.005 else "DA SPIEGARE"}).</p>')
    def ok(r, n):                               # la somma delle energie deve dare il lavoro del carico (entro 2%)
        return abs(sum(r["fea"]["energy"][n].values()) / r["fea"]["work"][n] - 1.0) < 0.02

    def cell(r, g, n):
        return f'{it(r["fea"]["energy"][n].get(g, 0) / r["fea"]["work"][n] * 100, 0)}%' if ok(r, n) else "n.v."
    en_rows = ""
    for g, lab in EN:
        en_rows += f'<tr><td>{lab}</td>' + "".join(f'<td>{cell(r, g, "Fy")} · {cell(r, g, "Fz")}</td>' for r in rows) + "</tr>"
    en_rows += '<tr><td>Somma / lavoro del carico</td>' + "".join(
        f'<td>{it(sum(r["fea"]["energy"]["Fy"].values()) / r["fea"]["work"]["Fy"] * 100, 1)}% · {it(sum(r["fea"]["energy"]["Fz"].values()) / r["fea"]["work"]["Fz"] * 100, 1)}%</td>' for r in rows) + "</tr>"
    en_head = "".join(f'<th>{r["name"]} · Y / Z</th>' for r in rows)
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — Concept D032</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d032_page.py: non modificare a mano. -->
<a class="back" href="fea-d031-gantry.html">← FEA gantry · D031</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D032 · Standard stiffness architecture v4</div><h1>Concept<br>a confronto.</h1><p class="lead">Varianti del mule Standard come override espliciti del mule v3 (<code>tools/cad/standard_concepts.py</code>): per ciascuna CAD con sweep, trasferitore e masse, e FEA del gantry con la pipeline D031 (solidi + molle D028, energia di deformazione per gruppo). La macchina è il gantry FEA in serie con telaio, tavola e asse Y del modello a travi. Target D032 PROVISIONAL: macchina ≥ {it(T_MIN["XY"], 0)} XY / {it(T_MIN["Z"], 1)} Z N/µm minimo, ~{it(T_DES["XY"], 0)} / ~{it(T_DES["Z"], 0)} di progetto; gate ≥ {it(GATE["XY"], 0)} XY / ≥ {it(GATE["Z"], 0)} Z entro {it(GATE["kg"], 0)} kg. Valori di progetto, non misure.</p><div class="badges"><span class="badge ok">D032 · concept A: kill criterion scattato</span><span class="badge">ICD v4 invariata in A</span><span class="badge">Asse spindle 53 mm fisso</span></div></div>

<section class="section"><h2>Matrice</h2><div class="table-wrap"><table>
<tr><th>Variante</th><th>Gantry X / Y / Z N/µm</th><th>Macchina X / Y / Z N/µm</th><th>δXY a {it(SERVICE["XY"], 0)} N</th><th>δZ a {it(SERVICE["Z"], 0)} N</th><th>Massa mule</th><th>Δ massa</th><th>Da recuperare → 42 kg</th><th>ΔK min XY per kg</th><th>Margine slitta + master recuperato</th><th>Sweep coll · FAIL · WARN</th><th>Trasferitore</th><th>Gate</th></tr>
{body}</table></div>{nonreg}
<p style="color:var(--dim);font-size:13px;margin-top:12px">δ = deformazione della sola macchina (naso spindle ↔ punto di lavoro) a SERVICE HIGH: 20 µm è l'intero budget, quindi il verde qui vuol dire solo "entro il budget totale", non "entro la quota macchina". ΔK min XY per kg = aumento della rigidezza radiale minima della macchina (N/µm) per kg aggiunto rispetto ad A0. Margine slitta + master recuperato = cedevolezza del gantry tolta in Y diviso la quota di energia di slitta + master in A0 ({it(base["fea"]["energy"]["Fy"].get("zslide", 0) / base["fea"]["work"]["Fy"] * 100, 0)}%: tetto del gantry con slitta + master perfette ≈ {it(base["k"]["Y"] / (1 - base["fea"]["energy"]["Fy"].get("zslide", 0) / base["fea"]["work"]["Fy"]), 2)} N/µm), anche per 100 g aggiunti. δ dalle rigidezze (modello lineare): δXY = {it(SERVICE["XY"], 0)} N / K min XY, δZ = {it(SERVICE["Z"], 0)} N / KZ. Monoscocca A1 modellata con giunti perfettamente solidali: la cedevolezza di bullonatura o incollaggio non è inclusa, il risultato è un limite superiore del giunto reale. Sweep su 125 configurazioni; trasferitore = gioco minimo lungo le 42 pose. Mesh della FEA come la baseline diagnostica D031 (6 / 12 mm).</p></section>

<section class="section"><h2>Dove si deforma · energia per gruppo</h2><div class="table-wrap"><table><tr><th>Gruppo</th>{en_head}</tr>{en_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Quota dell'energia di deformazione del gantry a 150 N Y e a 200 N Z; la somma per colonna deve dare il lavoro del carico ½·F·u. "n.v." = colonna non valida (somma fuori dal 2%). A1 · Z: il valore anomalo (5.371 N·mm di slitta + master contro 9,3 N·mm di lavoro) sta nel .dat di CalculiX, non nel lettore; rilanciando A1 a 200 N Z con l'energia elemento per elemento il gruppo vale 1,51 N·mm, nessun elemento anomalo (massimo 0,005 N·mm): uscita spuria non riproducibile. Spostamenti e rigidezze non dipendono da questa uscita.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Concept A · compact chain</span><h2>Una modifica alla volta.</h2><p>A0 mule v3 → A1 master + slitta monoscocca (la master diventa una scatola chiusa con la faccia anteriore della slitta: pareti laterali contro le ali, parete anteriore e cielo, sostituisce la sella) → A2 + carrello X scatolato → A3 + trave ad alta inerzia a massa costante (fondo trave fisso, cresce verso l'alto) → A4 combinazione. Fissi: asse spindle a 53 mm, piano cinematico e Ø80 del ToolDock, pull-stud, datum, inviluppo ICD v4, testa.</p></div>
  <div class="panel"><span class="kicker">Lettura</span><h2>Architettura o percentuale?</h2><p>La colonna δXY a 80 N dice subito se una variante è un progresso architetturale: oggi ~{it(SERVICE["XY"] / min(base["mach"]["X"], base["mach"]["Y"]), 0)} µm; a 1,5 N/µm sarebbero ~53 µm, a 3 ~27 µm, a 6 ~13 µm. Se A1 + A2 non spostano drasticamente XY, il concept A difficilmente passa il gate senza intervenire sul ToolDock e il concept C diventa prioritario.</p></div>
</section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/cad/standard_assembly.py --concept NOME</code> (CAD, sweep, trasferitore, masse) e <code>python tools/fea/d031_gantry.py --concept NOME</code> (FEA con energia) per ogni concept di <code>standard_concepts.py</code>, poi <code>python tools/fea/d032_page.py</code>.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    write(load())
