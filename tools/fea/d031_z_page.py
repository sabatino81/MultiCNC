#!/usr/bin/env python3
"""Pagina base/fea-d031-z.html dai risultati di tools/fea/d031_z.py (fea/d031/zslide.json). Non modificare a mano la pagina."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGE = ROOT / "base" / "fea-d031-z.html"


def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def write(r):
    d28 = r["d028"]
    V = r["variants"]
    base = V.get("strip")
    rows, best = [], None
    for tag, v in V.items():
        k = [v["k"][n] for n in ("Fx", "Fy", "Fz")]
        mach = [1.0 / (d28[ax]["rest"] + 1.0 / kk) for ax, kk in zip("XYZ", k)]
        v["_k"], v["_mach"], v["_kmin"] = k, mach, min(k[:2])
        if best is None or v["_kmin"] > best["_kmin"]:
            best = v
    for tag, v in V.items():
        dom = any(o["mass"]["master"] <= v["mass"]["master"] and o["_kmin"] >= v["_kmin"]
                  and (o["mass"]["master"] < v["mass"]["master"] or o["_kmin"] > v["_kmin"]) for o in V.values())
        dm = (v["mass"]["master"] - base["mass"]["master"]) * 1000 if base else 0.0
        rows.append(f'<tr><td>{v["desc"]}{"" if dom else " · <b>Pareto</b>"}</td><td>{it(v["mass"]["master"], 2)} kg</td><td>{("+" if dm > 0 else "") + it(dm, 0)} g</td>'
                    f'<td>{it(v["_k"][0], 2)}</td><td>{it(v["_k"][1], 2)}</td><td>{it(v["_k"][2], 2)}</td><td>{it(v["worst_um"], 0)}</td>'
                    f'<td>{it((v["mass"]["master"]) / v["_kmin"], 2)}</td><td>{" / ".join(it(x, 2) for x in v["_mach"])}</td></tr>')
    lim = [1.0 / d28[ax]["rest"] for ax in "XYZ"]
    kb, ks = best["_k"], base["_k"] if base else best["_k"]
    d_rows = "".join(f'<tr><td>{ax}</td><td>{it(d28[ax]["k_local"], 2)}</td><td>{it(ks[i], 2)}</td><td>{it(kb[i], 2)}</td>'
                     f'<td>{" · ".join(f"{t} {it(s, 0)}%" for t, s in d28[ax]["share"].items())}</td></tr>' for i, ax in enumerate("XYZ"))
    mesh = base["mesh"] if base else best["mesh"]
    v3 = r.get("v3", {})
    sad = V.get("saddle")
    v3_list = ([("Sella + piastrina 10 mm (fase 2a)", sad)] if sad else []) + [(v["desc"], v) for v in v3.values()]
    v3_rows = "".join(f'<tr><td>{d}</td><td>{it(v["k"]["Fx"], 2)}</td><td>{it(v["k"]["Fy"], 2)}</td><td><b>{it(v["k"]["Fz"], 2)}</b></td><td>{it(v["mass"]["struct"], 2)} kg</td></tr>' for d, v in v3_list)
    v3_gain = (it((v3["saddle_tab16"]["k"]["Fz"] / sad["k"]["Fz"] - 1) * 100, 0) + "%") if sad and "saddle_tab16" in v3 else "—"
    v3_lim = it(v3["saddle_tabrigid"]["k"]["Fz"], 1) if "saddle_tabrigid" in v3 else "—"
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — FEA slitta Z · D031</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d031_z.py (tools/fea/d031_z_page.py): non modificare a mano. -->
<a class="back" href="fea-d031.html">← FEA a solidi · pilota</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D031 · FEA a solidi · fase 2a</div><h1>Master<br>↔ slitta Z.</h1><p class="lead">Sottoassieme <b>testa + master + slitta Z</b> del mule v2 con la pipeline del <a href="fea-d031.html" style="color:var(--accent-2)">pilota</a>: la slitta è ora un solido incollato alla master, i quattro pattini HGH15CA ZA e la vite Z sono le molle calibrate D028, il carrello X è rigido. Mount a tazza {it(r["clamp"], 0)} mm. Si confrontano quattro topologie del collegamento master ↔ slitta. Solo rigidezze: le tensioni si chiudono con il submodel sulla topologia scelta. Valori di progetto, non misure.</p><div class="badges"><span class="badge ok">D031 · fase 2a</span><span class="badge">Carrello X rigido</span><span class="badge">Mesh nominale {it(r["h"], 0)} / {it(2.5, 1)} mm</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{it(ks[1], 2)} → {it(kb[1], 2)}</strong><span>N/µm in Y: striscia 12 mm → {best["desc"].lower()}</span></div>
  <div class="metric"><strong>{("+" if (best["mass"]["master"] - base["mass"]["master"]) > 0 else "") + it((best["mass"]["master"] - base["mass"]["master"]) * 1000, 0)} g</strong><span>massa aggiunta alla master</span></div>
  <div class="metric"><strong>{" / ".join(it(x, 2) for x in best["_mach"])}</strong><span>N/µm stimati sulla macchina con questa topologia (resto D028)</span></div>
  <div class="metric"><strong>{" / ".join(it(x, 2) for x in lim)}</strong><span>N/µm di limite con testa, master, slitta e guide Z rigide</span></div>
</section>

<section class="section"><p><a class="btn primary" href="viewer-3d.html?m=z_strip_Fy_u.glb">Striscia in 3D · 150 N Y</a> <a class="btn" href="viewer-3d.html?m=z_saddle_Fy_u.glb">Sella in 3D</a> <a class="btn" href="viewer-3d.html?m=z_both_Fy_u.glb">Flangia + sella in 3D</a> <a class="btn" href="viewer-3d.html?m=z_strip_Fz_u.glb">Striscia · 200 N Z (piastrina chiocciola)</a></p></section>

<section class="section"><h2>Topologie del collegamento</h2><div class="table-wrap"><table>
<tr><th>Topologia</th><th>Master</th><th>Δ massa</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th><th>Δ punta worst µm</th><th>kg / (N/µm)</th><th>Macchina X / Y / Z (stima)</th></tr>
{"".join(rows)}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Rigidezze al dado ER11 rispetto al carrello X (rigido), casi 150 N X, 150 N Y, 200 N Z; Δ punta worst = massimo |u| tra i casi di forza e i combinati 150 N radiali + 200 N assiali. Massa = master con flangia e guance (slitta e testa uguali per tutte). kg / (N/µm) = massa della master sulla rigidezza radiale minima; <b>Pareto</b> = nessun'altra topologia è insieme più leggera e più rigida. Macchina = modello a travi D028 con questo sottoassieme al posto del suo: resto della macchina invariato.</p></section>

<section class="section"><h2>Mule v3 · piastrina chiocciola Z</h2><div class="table-wrap"><table>
<tr><th>Variante (con la sella)</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th><th>Struttura</th></tr>
{v3_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">La piastrina che porta la chiocciola Z sporge ~52 mm dietro la slitta. Da 10 a 16 mm (solo verso l'alto: verso il basso il gioco dal BF è già 8 mm) Z sale del {v3_gain}; con la piastrina infinitamente rigida il limite è {v3_lim} N/µm. Il resto della cedevolezza in Z viene dal braccio di ~95 mm tra asse utensile e vite (la slitta beccheggia sui pattini) e dalla catena assiale della vite. Il mule v3 adotta sella + piastrina 16 mm.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">Modello</span><h2>Cosa cambia rispetto al pilota.</h2><p><b>Slitta Z</b> del mule: piastra 150 × 12 × 160 con ali anteriori 10 × 35 e piastrina chiocciola 52 × 64 × 10, incollate alla master (bullonatura = incollaggio). <b>Pattini</b>: per ciascuno una molla a 6 gdl D028 (365 N/µm radiale e laterale, libera lungo la rotaia) tra la sua impronta sulla faccia posteriore della slitta e il carrello. <b>Vite Z</b>: catena assiale D028 (albero, chiocciola, BK, tenuta del motore) sulla faccia superiore della piastrina, sotto la chiocciola. Testa, accoppiamento a tre sfere, cuscinetti, punto di misura e carichi come nel pilota.</p><p><b>Topologie</b>: striscia = master appoggiata solo sul bordo inferiore da 12 mm della piastra (mule v2); flangia = parete posteriore della master che risale di {it(r["flange_h"], 0)} mm sulla faccia anteriore della slitta tra le ali; sella = guance laterali alte {it(r["cheek_h"], 0)} mm incollate alle facce interne delle due ali; flangia + sella = entrambe. Ingombri da verificare nel CAD (trasferitore, catene) prima di congelarne una.</p></div>
  <div class="panel"><span class="kicker">FEA ↔ D028</span><h2>Stessa catena, due modelli.</h2><div class="table-wrap"><table><tr><th>Asse</th><th>D028</th><th>FEA striscia</th><th>FEA migliore</th><th>Quote D028 nella macchina</th></tr>{d_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Catena locale = master, accoppiamento, testa, slitta Z, guide e vite Z. In Z la FEA è molto sotto D028: il modello a travi collega la vite alla slitta con un vincolo rigido, mentre nel mule la piastrina chiocciola da 10 mm lavora a flessione a sbalzo dietro la slitta. Nominale {mesh["elements"]:,} elementi ({mesh["dof"] // 1000}k gdl).</p></div>
</section>

<section class="section"><div class="callout"><b>Prossimo.</b> Submodel delle tensioni sulla topologia scelta (1–1,5 mm alla radice e sui raccordi reali), piastrina chiocciola Z irrigidita, poi rapidamente il gantry completo (carrello X, trave, spalle) con le stesse molle D028: se il gantry conferma l'ordine di grandezza, la scelta è tra riposizionare D014 per la Standard e una revisione architetturale più profonda.</div></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d031_z.py</code> (CadQuery, gmsh, CalculiX <code>ccx</code>): quattro topologie, <code>fea/d031/zslide.json</code> e questa pagina; <code>python tools/fea/d031_z_page.py</code> rigenera solo la pagina.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    write(json.loads((ROOT / "fea" / "d031" / "zslide.json").read_text()))
