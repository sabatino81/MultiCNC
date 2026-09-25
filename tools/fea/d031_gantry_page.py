#!/usr/bin/env python3
"""Pagina base/fea-d031-gantry.html da fea/d031/gantry.json (tools/fea/d031_gantry.py). Non modificare a mano la pagina."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGE = ROOT / "base" / "fea-d031-gantry.html"
TARGET = 10.0


def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def write(r):
    d28 = r["d028"]
    runs = sorted(r["runs"].values(), key=lambda v: (v["hc"], v["h"]), reverse=True)
    nom = runs[-1]                                  # la mesh più fine è il riferimento
    k = [nom["k"][n] for n in ("Fx", "Fy", "Fz")]
    mach = [1.0 / (d28[ax]["rest"] + 1.0 / kk) for ax, kk in zip("XYZ", k)]
    lim = [d28[ax]["limit"] for ax in "XYZ"]
    cmp_rows = "".join(
        f'<tr><td>{ax}</td><td>{it(d28[ax]["k_gantry_d028"], 2)}</td><td><b>{it(k[i], 2)}</b></td><td>{it(k[i] / d28[ax]["k_gantry_d028"], 2)}</td>'
        f'<td>{it(d28[ax]["k_machine"], 2)}</td><td><b>{it(mach[i], 2)}</b></td><td>{it(lim[i], 2)}</td><td>{it(TARGET, 0)}</td></tr>' for i, ax in enumerate("XYZ"))
    conv_rows = "".join(
        f'<tr><td>{it(v["h"], 0)} / {it(v["hc"], 0)} mm</td><td>{v["mesh"]["elements"]:,}</td><td>{v["mesh"]["dof"] // 1000}k</td>'
        f'<td>{" / ".join(it(v["k"][n], 3) for n in ("Fx", "Fy", "Fz"))}</td><td>{it(v["solve_s"], 0)} s</td></tr>' for v in runs)
    conv_note = ""
    if len(runs) > 1:
        a, b = runs[0], runs[-1]
        dd = max(abs(a["k"][n] - b["k"][n]) / b["k"][n] for n in ("Fx", "Fy", "Fz"))
        conv_note = f'Variazione massima della rigidezza tra la mesh più grossa e la più fine: {it(dd * 100, 1)}% ({"entro" if dd < 0.05 else "oltre"} il 5%).'
    share_rows = "".join(
        f'<tr><td>{t}</td>' + "".join(f'<td>{it(d28[ax]["share"].get(t, 0.0), 0)}%</td>' for ax in "XYZ") + '</tr>'
        for t in ("telaio", "tavola", "guide Y + vite Y", "spalle", "trave", "guide X + vite X", "carrello X", "guide Z + vite Z", "slitta Z",
                  "master ToolDock", "accoppiamento ToolDock", "testa (spindle + utensile)"))
    worst_gap = min(m_ / TARGET for m_ in mach)
    DN = {"gantry": "Trave + spalle", "carriage": "Carrello X", "zgroup": "Slitta Z + master + testa", "tooldock": "Accoppiamento ToolDock (3 sfere)",
          "rails": "Pattini e viti X / Z", "beam": "Solo la trave", "uprights": "Solo le spalle"}
    base_run = next((v for v in r["runs"].values() if v["h"] == r.get("diag_h", 6.0) and v["hc"] == 12.0), nom)
    diag_rows = ""
    for name, v in r.get("diag", {}).items():
        cells = ""
        for n in ("Fx", "Fy", "Fz"):
            c0, c1 = 1.0 / base_run["k"][n], 1.0 / v["k"][n]
            cells += f'<td>{it(v["k"][n], 2)} · {it((c0 - c1) / c0 * 100, 0)}%</td>'
        diag_rows += f'<tr><td>{DN.get(name, name)}</td>{cells}</tr>'
    diag_sec = (f"""<section class="section"><h2>Quale parte del gantry pesa · sensibilità massima</h2><div class="table-wrap"><table><tr><th>Reso rigido</th><th>X N/µm · cedevolezza tolta</th><th>Y N/µm · cedevolezza tolta</th><th>Z N/µm · cedevolezza tolta</th></tr>
<tr><td>Baseline diagnostica, mesh 6 / 12 mm</td>{"".join(f'<td>{it(base_run["k"][n], 2)}</td>' for n in ("Fx", "Fy", "Fz"))}</tr>{diag_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px"><b>Upper-bound sensitivity</b>: ogni riga rende quasi perfetto un solo sottosistema (solidi con E ×1000, oppure molle ×1000) e lascia reale tutto il resto, sulla stessa mesh del riferimento. La percentuale risponde a "quanto migliorerebbe al massimo il gantry se questo sottosistema fosse perfetto". Non è una ripartizione additiva: irrigidendo un gruppo cambia il percorso dei carichi, quindi le percentuali possono sommare a più (o meno) del 100%. Gruppo Z = slitta, piastrina chiocciola, master, receiver, mount, corpo spindle e albero; restano reali sfere ToolDock, cuscinetti, pattini e viti. La baseline diagnostica è la mesh 6 / 12 mm ({" / ".join(it(base_run["k"][n], 3) for n in ("Fx", "Fy", "Fz"))} N/µm): le diagnostiche sono calcolate su quella mesh; la testata usa la mesh più fine 6 / 10 mm, entro l'1,2%.</p></section>""" if diag_rows else "")
    en = r.get("energy")
    energy_sec = ""
    if en:
        EN = [("uprights", "Spalle"), ("beam", "Trave"), ("carriage", "Carrello X"), ("zslide", "Slitta Z + master"), ("head", "Testa (receiver, mount, spindle)"),
              ("xblocks", "Pattini X"), ("xscrew", "Vite X"), ("zblocks", "Pattini Z"), ("zscrew", "Vite Z"), ("tooldock", "Accoppiamento ToolDock"), ("bearing", "Cuscinetti spindle")]
        rows_e = "".join(f'<tr><td>{lab}</td>' + "".join(f'<td>{it(en["energy"][n].get(g, 0.0) / en["work"][n] * 100, 0)}%</td>' for n in ("Fx", "Fy", "Fz")) + "</tr>" for g, lab in EN)
        chk = " / ".join(it(sum(en["energy"][n].values()) / en["work"][n] * 100, 1) + "%" for n in ("Fx", "Fy", "Fz"))
        energy_sec = f"""<section class="section"><h2>Dove si deforma oggi · energia di deformazione</h2><div class="table-wrap"><table><tr><th>Gruppo (baseline 6 / 12 mm)</th><th>150 N X</th><th>150 N Y</th><th>200 N Z</th></tr>{rows_e}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Quota dell'energia di deformazione totale per gruppo (solidi dall'energia degli elementi, molle dalla loro energia elastica), sullo stato di carico reale. Seconda lettura, complementare alla sensibilità: la sensibilità dice quanto si guadagnerebbe al massimo rendendo perfetto un gruppo, l'energia dice dove la struttura si deforma oggi. Controllo: somma delle energie / lavoro del carico ½·F·u = {chk}.</p></section>"""
    verdict = (f'Con il gantry reale la macchina stimata è <b>{" / ".join(it(v, 2) for v in mach)} N/µm</b>: tra {it(min(mach) / TARGET * 100, 0)}% e {it(max(mach) / TARGET * 100, 0)}% del target D014. '
               f'Anche con un gantry infinitamente rigido il resto (telaio, tavola, guide e vite Y, dal modello a travi) limiterebbe a {" / ".join(it(v, 2) for v in lim)} N/µm. '
               f'L\'ordine di grandezza è {"confermato" if max(mach) < 3.0 else "da rileggere"}: 10 N/µm non si raggiunge con ottimizzazioni di questa architettura. '
               'È l\'ingresso della decisione architetturale: riposizionare D014 per la Standard oppure rivedere la struttura in modo profondo.')
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — FEA gantry · D031</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d031_gantry.py (tools/fea/d031_gantry_page.py): non modificare a mano. -->
<a class="back" href="fea-d031-z.html">← FEA slitta Z</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D031 · FEA a solidi · fase 3</div><h1>Gantry<br>completo.</h1><p class="lead">FEA lineare statica del <b>gantry del mule v3</b>: spalle e trave reali, carrello X, slitta Z con sella a U e piastrina chiocciola 16 mm, master, testa 5045-style. Pattini, viti e ToolDock sono le molle calibrate D028; il telaio, la tavola e l'asse Y restano nel modello a travi D028. Rigidezza al dado ER11 rispetto alla base delle spalle, al centro corsa. Valori di progetto, non misure.</p><div class="badges"><span class="badge ok">D031 · fase 3</span><span class="badge">Mule v3 · CENTER</span><span class="badge">Telaio e tavola da D028</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{" / ".join(it(v, 2) for v in k)}</strong><span>N/µm del gantry FEA in X / Y / Z</span></div>
  <div class="metric"><strong>{" / ".join(it(v, 2) for v in mach)}</strong><span>N/µm stimati sulla macchina (gantry FEA + resto D028)</span></div>
  <div class="metric"><strong>{" / ".join(it(v, 2) for v in lim)}</strong><span>N/µm di limite con il gantry infinitamente rigido</span></div>
  <div class="metric"><strong>{it(worst_gap * 100, 0)}%</strong><span>del target D014 (10 N/µm) sull'asse peggiore</span></div>
</section>

<section class="section"><div class="callout" style="border-color:rgba(255,84,112,.45)"><b>Lettura.</b> {verdict}</div></section>

<section class="section"><p><a class="btn primary" href="viewer-3d.html?m={nom["tag"]}_Fy_u.glb">Deformata del gantry in 3D · 150 N Y</a> <a class="btn" href="viewer-3d.html?m={nom["tag"]}_Fx_u.glb">150 N X</a> <a class="btn" href="viewer-3d.html?m={nom["tag"]}_Fz_u.glb">200 N Z</a></p></section>

{diag_sec}

{energy_sec}

<section class="section"><h2>Gantry FEA ↔ D028</h2><div class="table-wrap"><table>
<tr><th>Asse</th><th>Gantry D028</th><th>Gantry FEA</th><th>FEA / D028</th><th>Macchina D028</th><th>Macchina con gantry FEA</th><th>Limite, gantry rigido</th><th>D014</th></tr>
{cmp_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">N/µm al centro corsa. Gantry D028 = cedevolezza del modello a travi senza telaio, tavola e asse Y (dalla ripartizione dell'energia); macchina con gantry FEA = gantry FEA in serie con quel resto.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Modello</span><h2>Cosa c'è dentro.</h2><p><b>Solidi</b> dal mule v3 in CENTER: spalle scatolate e trave 80 × 140 incollate, con gli spessori sotto BK/BF X; carrello X a canale con la staffa della chiocciola X; slitta Z, piastrina chiocciola 16 mm e master con sella a U incollate; testa come nel pilota (mount 56 mm). Vincolo alla base delle spalle (faccia sulla traversa posteriore del telaio).</p><p><b>Molle D028</b>: quattro pattini HGH15CA ZA X tra la faccia posteriore del carrello e l'impronta della guida sulla faccia della trave; catena assiale della vite X tra la staffa della chiocciola e il BK sulla trave; quattro pattini HGH15CA ZA Z tra slitta e impronta della guida sul carrello; catena della vite Z tra piastrina e BK Z; tre sfere del ToolDock; cuscinetti dello spindle. Nel mule il BK Z sta nella fessura del carrello senza attacco disegnato: si aggancia alle due facce della fessura (ipotesi MULE). Guide non modellate come solidi (rigidezza propria trascurata, a favore di sicurezza trascurabile).</p></div>
  <div class="panel"><span class="kicker">Mesh</span><h2>Graduata.</h2><p>Tetra quadratici, fine attorno a testa, slitta e carrello, più grossa su trave e spalle a parete sottile; locale 2,5 mm su sfere, collare, cuscinetti e naso.</p><div class="table-wrap"><table><tr><th>Fine / grossa</th><th>Elementi</th><th>Gdl</th><th>X / Y / Z N/µm</th><th>Soluzione</th></tr>{conv_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">{conv_note}</p></div>
</section>

<section class="section"><h2>Dove sta la cedevolezza nel modello a travi</h2><div class="table-wrap"><table><tr><th>Sottosistema (D028, mule v3)</th><th>X</th><th>Y</th><th>Z</th></tr>{share_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Quote di energia di deformazione del modello a travi al centro corsa: dicono dove D028 mette la cedevolezza; la FEA corregge la catena locale e il gantry, ma telaio, tavola e asse Y restano quelli di D028.</p></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d031_gantry.py [--h 6 --coarse 12]</code> (CadQuery, gmsh, CalculiX <code>ccx</code>): <code>fea/d031/gantry.json</code> e questa pagina; <code>python tools/fea/export_results.py</code> per le deformate 3D.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    write(json.loads((ROOT / "fea" / "d031" / "gantry.json").read_text()))
