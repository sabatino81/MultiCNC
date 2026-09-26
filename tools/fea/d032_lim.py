#!/usr/bin/env python3
"""D032-LIM · stiffness envelope: quanta rigidezza manca, a massa bloccata (nessun credito di massa).

Uso (dalla radice): python tools/fea/d032_lim.py
Legge fea/d032/C3c.json (gantry FEA, riferimento strutturale), fea/d031/gantry.json (resto della macchina nel modello a
travi D028: telaio, tavola, asse Y) e, se c'è, fea/d032/LIM4_check.json (verifica FEA con E e k ×4). Scrive
base/fea-d032-lim.html. Non modificare a mano la pagina.

In un modello lineare, moltiplicare per f tutte le rigidezze di un sottosistema (moduli dei solidi e molle) ne divide per
f la cedevolezza: il gantry scalato vale f · K_C3c esattamente, e la macchina è il gantry in serie con il resto
(eventualmente scalato di g). Non è una geometria: è il requisito, espresso come moltiplicatore.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGE = ROOT / "base" / "fea-d032-lim.html"
FACTORS = [1.0, 2.0, 4.0, 8.0, float("inf")]
GATE = dict(X=3.0, Y=3.0, Z=4.0)
DES = dict(X=6.0, Y=6.0, Z=8.0)
SERVICE = dict(X=80.0, Y=80.0, Z=150.0)


def it(x, d=2):
    if x == float("inf"):
        return "∞"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def machine(kg, rest, f=1.0, g=1.0):
    cg = 0.0 if f == float("inf") else 1.0 / (f * kg)
    cr = 0.0 if g == float("inf") else rest / g
    return float("inf") if cg + cr == 0 else 1.0 / (cg + cr)


def need_gantry(target, rest, kg):
    """Moltiplicatore del solo gantry per arrivare al target con il resto invariato (None = impossibile)."""
    c = 1.0 / target - rest
    return None if c <= 0 else (1.0 / c) / kg


def main():
    c3c = json.loads((ROOT / "fea" / "d032" / "C3c.json").read_text())
    rest = {ax: v["rest"] for ax, v in json.loads((ROOT / "fea" / "d031" / "gantry.json").read_text())["d028"].items()}
    kg = {ax: c3c["k"][n] for ax, n in zip("XYZ", ("Fx", "Fy", "Fz"))}
    cadf = ROOT / "cad" / "concepts" / "C3c" / "report.json"
    mass = json.loads(cadf.read_text())["mass"]["machine_mule_kg"] if cadf.exists() else None
    chk = ROOT / "fea" / "d032" / "LIM4_check.json"
    check = json.loads(chk.read_text()) if chk.exists() else None
    m1 = {ax: machine(kg[ax], rest[ax]) for ax in "XYZ"}

    def row(label, f, g):
        m = {ax: machine(kg[ax], rest[ax], f, g) for ax in "XYZ"}
        cells = "".join(f'<td class="{"status-ok" if m[ax] >= DES[ax] else ("status-target" if m[ax] >= GATE[ax] else "status-critical")}">{it(m[ax], 2)}</td>' for ax in "XYZ")
        dxy = SERVICE["X"] / min(m["X"], m["Y"]) if min(m["X"], m["Y"]) != float("inf") else 0.0
        dz = SERVICE["Z"] / m["Z"] if m["Z"] != float("inf") else 0.0
        return f'<tr><td>{label}</td>{cells}<td>{it(dxy, 0)} µm</td><td>{it(dz, 0)} µm</td></tr>'

    g_rows = "".join(row(f"Gantry ×{it(f, 0)}", f, 1.0) for f in FACTORS)
    w_rows = "".join(row(f"Macchina intera ×{it(f, 0)}", f, f) for f in FACTORS)
    need = ""
    for ax in "XYZ":
        ng, nd = need_gantry(GATE[ax], rest[ax], kg[ax]), need_gantry(DES[ax], rest[ax], kg[ax])
        need += (f'<tr><td>{ax}</td><td>{it(m1[ax], 2)}</td><td>{it(1.0 / rest[ax], 2)}</td>'
                 f'<td>{("×" + it(ng, 1)) if ng else "impossibile"}</td><td>{("×" + it(nd, 1)) if nd else "impossibile"}</td>'
                 f'<td>×{it(GATE[ax] / m1[ax], 1)}</td><td>×{it(DES[ax] / m1[ax], 1)}</td></tr>')
    fw_gate = max(GATE[ax] / m1[ax] for ax in "XYZ")
    fw_des = max(DES[ax] / m1[ax] for ax in "XYZ")
    chk_txt = ""
    if check:
        dd = max(abs(check["k"][n] / (4.0 * c3c["k"][n]) - 1.0) for n in ("Fx", "Fy", "Fz"))
        chk_txt = (f'<p style="color:var(--dim);font-size:13px;margin-top:12px"><b>Verifica FEA</b>: C3c con moduli E e rigidezze delle molle ×4 dà '
                   f'{" / ".join(it(check["k"][n], 3) for n in ("Fx", "Fy", "Fz"))} N/µm contro 4 × C3c = {" / ".join(it(4 * c3c["k"][n], 3) for n in ("Fx", "Fy", "Fz"))}: '
                   f'scarto {it(dd * 100, 2)}%. Il moltiplicatore è esatto: il resto della tabella non richiede altre FEA.</p>')
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — D032-LIM · stiffness envelope</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d032_lim.py: non modificare a mano. -->
<a class="back" href="fea-d032.html">← Concept D032</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D032-LIM · stiffness envelope</div><h1>Quanta rigidezza<br>manca.</h1><p class="lead">Studio limite, non un concept: parte da C3c (riferimento strutturale: coupling Ø110, braccio 203 mm, fuori ICD v4, packaging da risolvere) e moltiplica tutte le rigidezze, dei solidi (E) e delle molle (k), prima del solo gantry e poi della macchina intera. <b>Nessun credito di massa</b>: la massa resta quella di C3c{(" (" + it(mass, 1) + " kg)") if mass else ""}. Il risultato è il requisito espresso come moltiplicatore: poi va tradotto in sezioni, interassi, topologie e massa reale.</p><div class="badges"><span class="badge ok">D032-LIM</span><span class="badge">Structural reference only · requires ICD v5 packaging resolution</span><span class="badge">Massa bloccata</span></div></div>

<section class="section"><div class="callout" style="border-color:rgba(255,84,112,.45)"><b>Lettura.</b> Con il resto della macchina attuale (telaio, tavola, asse Y dal modello a travi: da solo {it(1 / rest["X"], 1)} / {it(1 / rest["Y"], 2)} / {it(1 / rest["Z"], 2)} N/µm) scalare il solo gantry non basta: per Y = 3 N/µm servirebbe il gantry ×{it(need_gantry(3.0, rest["Y"], kg["Y"]), 1)}, e Z = 4 o Y = 6 sono impossibili. Scalando la macchina intera il gate {it(GATE["X"], 0)} XY / {it(GATE["Z"], 0)} Z richiede circa <b>×{it(fw_gate, 1)}</b> e il target di progetto {it(DES["X"], 0)} / {it(DES["Z"], 0)} circa <b>×{it(fw_des, 1)}</b> della rigidezza complessiva di C3c, togliendo intanto {it(mass - 42.0, 1) if mass else "~3,7"} kg per tornare a 42 kg. Un vero concept B deve quindi coinvolgere anche tavola, telaio e asse Y, non solo carrello, Z e trave.</div></section>

<section class="section"><h2>Moltiplicatore richiesto</h2><div class="table-wrap"><table>
<tr><th>Asse</th><th>Macchina C3c N/µm</th><th>Resto macchina da solo</th><th>Solo gantry → gate</th><th>Solo gantry → progetto</th><th>Macchina intera → gate</th><th>Macchina intera → progetto</th></tr>
{need}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Gate D032: {it(GATE["X"], 0)} XY / {it(GATE["Z"], 0)} Z N/µm; progetto: ~{it(DES["X"], 0)} / ~{it(DES["Z"], 0)} (PROVISIONAL). "Impossibile" = il resto della macchina da solo è già sotto il target.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Solo gantry scalato</span><h2>Il resto fa da tappo.</h2><div class="table-wrap"><table><tr><th>Caso</th><th>X</th><th>Y</th><th>Z</th><th>δXY 80 N</th><th>δZ 150 N</th></tr>{g_rows}</table></div></div>
  <div class="panel"><span class="kicker">Macchina intera scalata</span><h2>Moltiplicatore uniforme.</h2><div class="table-wrap"><table><tr><th>Caso</th><th>X</th><th>Y</th><th>Z</th><th>δXY 80 N</th><th>δZ 150 N</th></tr>{w_rows}</table></div></div>
</section>
<section class="section"><p style="color:var(--dim);font-size:13px">N/µm della macchina (naso spindle ↔ punto di lavoro): gantry FEA di C3c (baseline 6 / 12 mm) in serie con telaio, tavola e asse Y di D028. Rosso = sotto il gate, giallo = tra gate e progetto, verde = sopra il progetto. δ = deformazione della sola macchina a SERVICE HIGH.</p>{chk_txt}</section>

<section class="section"><div class="callout"><b>Cosa deve ottenere un vero concept B.</b> Circa ×{it(fw_gate, 1)} della rigidezza complessiva per il gate e ×{it(fw_des, 1)} per il target di progetto, sul gantry e sul resto della macchina insieme, scendendo da {it(mass, 1) if mass else "~45,7"} a ≤ 42 kg. In alluminio a massa costante questo non viene da pareti più spesse: serve cambiare sezioni (altezza delle travi, interassi di pattini e guide), topologia (catena punta → pezzo più corta) e forse cinematica. La trave ad alta inerzia (A3) entra lì, non su un'architettura già fermata.</div></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d032_lim.py</code> dai risultati di C3c; la verifica FEA con E e k ×4 si ottiene lanciando C3c con i moduli e le molle moltiplicati (<code>fea/d032/LIM4_check.json</code>).</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")
    print("gate ×", round(fw_gate, 2), "progetto ×", round(fw_des, 2), {ax: round(m1[ax], 3) for ax in "XYZ"})


if __name__ == "__main__":
    main()
