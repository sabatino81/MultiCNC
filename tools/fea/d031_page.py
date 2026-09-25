#!/usr/bin/env python3
"""Pagina base/fea-d031.html dai risultati di tools/fea/d031.py (fea/d031/pilot.json). Non modificare a mano la pagina."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGE = ROOT / "base" / "fea-d031.html"
FORCE = ("Fx", "Fy", "Fz")
LOCAL = ("master ToolDock", "accoppiamento ToolDock", "testa (spindle + utensile)")


def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pareto(rows):
    """Varianti non dominate su (massa ↓, rigidezza minima X/Y ↑)."""
    return {a["tag"] for a in rows if not any(
        b["mass"] <= a["mass"] and b["kmin"] >= a["kmin"] and (b["mass"] < a["mass"] or b["kmin"] > a["kmin"]) for b in rows)}


def machine(r, k_fea):
    """D028 macchina intera con la catena locale (master + accoppiamento + testa) sostituita dalla FEA, e limite
    con la catena locale infinitamente rigida: il resto della macchina resta quello di D028."""
    out = {}
    for ax, k in zip("XYZ", k_fea):
        d = r["d028"][ax]
        c = 1.0 / d["k_machine"]
        rest = c * (1.0 - sum(d["share"][t] for t in LOCAL) / 100.0)
        out[ax] = dict(d028=d["k_machine"], fea=1.0 / (rest + 1.0 / k), limit=1.0 / rest)
    return out


def write(r):
    nom, fine, conv, st, d28 = r["nominal"], r["fine"], r["convergence"], r["self_test"], r["d028"]
    opt = r.get("nominal_opt", nom)
    c = nom["cases"]
    kf = [fine["cases"][n]["k_N_um"] for n in FORCE]
    kx, ky, kz = kf
    fine_pct = it((1 - fine["h"] / r["h_nom"]) * 100, 0)
    dmax = max(v["delta"] for v in conv.values())
    mc = machine(r, kf)
    case_rows = "".join(
        f'<tr><td>{v["desc"]}</td><td>{" / ".join(it(u, 1) for u in v["tip_um"])}</td><td>{it(v["tip_abs_um"], 1)}</td>'
        f'<td>{it(v["k_N_um"], 2) if "k_N_um" in v else "—"}</td></tr>' for v in c.values())
    rel = c["REL"]
    cmp_rows = "".join(
        f'<tr><td>{ax}</td><td><b>{it(k, 2)}</b></td><td>{it(d28[ax]["k_local"], 2)}</td><td>{it(k / d28[ax]["k_local"], 2)}</td>'
        f'<td>{" · ".join(f"{t} {it(s, 0)}%" for t, s in d28[ax]["share"].items())}</td></tr>' for ax, k in zip("XYZ", kf))
    mc_rows = "".join(f'<tr><td>{ax}</td><td>{it(v["d028"], 2)}</td><td><b>{it(v["fea"], 2)}</b></td><td>{it(v["limit"], 2)}</td><td>10</td></tr>'
                      for ax, v in mc.items())
    conv_rows = "".join(
        f'<tr><td>{n}</td><td>{it(v["nom"], 2)}</td><td>{it(v["fine"], 2)}</td><td class="{"status-ok" if v["delta"] < 0.05 else "status-critical"}">{it(v["delta"] * 100, 1)}%</td></tr>'
        for n, v in conv.items())
    hot_rows = ""
    for n in FORCE:
        a, b = c[n]["vm_hot"]["MPa"], fine["cases"][n]["vm_hot"]["MPa"]
        hot_rows += (f'<tr><td>{c[n]["desc"]}</td><td>{it(c[n]["vm_peak"]["MPa"], 1)} → {it(fine["cases"][n]["vm_peak"]["MPa"], 1)}</td>'
                     f'<td>{it(a, 1)} → {it(b, 1)}</td><td class="status-target">+{it((b / a - 1) * 100, 0)}%</td></tr>')
    oc = opt["cases"]
    body_rows = "".join(
        f'<tr><td>{oc[n]["desc"]}</td>' + "".join(f'<td>{it(oc[n]["vm_hot_body"][b], 1)}</td>' for b in ("master", "head_al", "spindle_body", "shaft")) + "</tr>"
        for n in ("Fx", "Fy", "Fz", "FxFz", "FyFz", "Mx", "My", "REL")) if "vm_hot_body" in oc["Fx"] else ""
    var = []
    for tag, v in r["variants"].items():
        cc = v["cases"]
        k = [cc[n]["k_N_um"] for n in FORCE]
        var.append(dict(tag=tag, desc=v["desc"], mass=v["mass"]["master"] + v["mass"]["head_al"], k=k, kmin=min(k[:2]),
                        worst=max(cc[n]["tip_abs_um"] for n in ("Fx", "Fy", "Fz", "FxFz", "FyFz"))))
    front = pareto(var)
    vv = {x["tag"]: x for x in var}
    m0 = vv["master_w8"]["mass"] if vv else 0.0
    var_rows = "".join(
        f'<tr><td>{x["desc"]}{" · <b>Pareto</b>" if x["tag"] in front else ""}</td><td>{it(x["mass"], 2)} kg</td>'
        f'<td>{("+" if x["mass"] - m0 > 0 else "") + it((x["mass"] - m0) * 1000, 0)} g</td>'
        f'<td>{it(x["k"][0], 2)}</td><td>{it(x["k"][1], 2)}</td><td>{it(x["k"][2], 1)}</td><td>{it(x["worst"], 0)}</td>'
        f'<td>{it(x["mass"] / x["kmin"], 2)}</td></tr>' for x in var)
    findings = (f'La catena locale è più cedevole di quanto dica D028: {it(kx, 2)} / {it(ky, 2)} N/µm in X / Y contro {it(d28["X"]["k_local"], 2)} / {it(d28["Y"]["k_local"], 2)} '
                f'(FEA / D028 = {it(kx / d28["X"]["k_local"], 2)} / {it(ky / d28["Y"]["k_local"], 2)}). Il modello a travi incastra la master sulla slitta; nel mule la master appoggia '
                f'sotto la slitta solo sulla striscia da 12 mm della piastra e sporge di ~123 mm verso il naso: in Y lavora a flessione e la radice è anche la zona più sollecitata. ')
    if vv:
        findings += (f'La parete della master aiuta ma non cambia il problema: 8 → 10 mm dà Y {it(vv["master_w8"]["k"][1], 2)} → {it(vv["master_w10"]["k"][1], 2)} N/µm per '
                     f'+{it((vv["master_w10"]["mass"] - m0) * 1000, 0)} g, 8 → 6 mm la fa scendere a {it(vv["master_w6"]["k"][1], 2)}. Il mount 56 mm toglie '
                     f'{it((m0 - vv["mount_56"]["mass"]) * 1000, 0)} g e perde solo {it((1 - vv["mount_56"]["k"][1] / vv["master_w8"]["k"][1]) * 100, 0)}% in Y: si tiene per la fase 2.')
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — FEA a solidi · D031</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d031.py (tools/fea/d031_page.py): non modificare a mano. -->
<a class="back" href="cad-standard.html">← CAD Standard · mule</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D031 · FEA a solidi · fase 1 pilota chiusa</div><h1>FEA<br>a solidi.</h1><p class="lead">Fase 1 della D031, chiusa: FEA lineare statica del modello pilota <b>master ToolDock + testa 5045-style</b> del mule v2 e la pipeline (Gmsh, tetra quadratici, CalculiX) che servirà per tutti gli altri pezzi. Guide, viti e ToolDock restano molle equivalenti calibrate come in D028, così il confronto è diretto. <b>Stato: spostamenti convergenti, tensioni non ancora convergenti.</b> Valori di progetto, non misure.</p><div class="badges"><span class="badge ok">Spostamenti convergenti</span><span class="badge">Tensioni non convergenti</span><span class="badge">Slitta Z rigida in questa fase</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{it(kx, 2)} / {it(ky, 2)} / {it(kz, 1)}</strong><span>N/µm della catena locale X / Y / Z (FEA, mesh fine)</span></div>
  <div class="metric"><strong>{it(mc["X"]["fea"], 2)} / {it(mc["Y"]["fea"], 2)} / {it(mc["Z"]["fea"], 2)}</strong><span>N/µm stimati sulla macchina: D028 con la catena locale FEA</span></div>
  <div class="metric"><strong>{it(mc["X"]["limit"], 2)} / {it(mc["Y"]["limit"], 2)} / {it(mc["Z"]["limit"], 2)}</strong><span>N/µm di limite con testa, master e ToolDock infinitamente rigidi</span></div>
  <div class="metric"><strong>{it(dmax * 100, 1)}%</strong><span>variazione alla punta con la mesh −{fine_pct}% · limite 5%</span></div>
</section>

<section class="section"><div class="callout" style="border-color:rgba(255,84,112,.45)"><b>Dove finisce la strada delle ottimizzazioni locali.</b> Sostituendo in D028 la sola catena locale (master + accoppiamento + testa) con quella della FEA, la macchina scende da {it(mc["X"]["d028"], 2)} / {it(mc["Y"]["d028"], 2)} / {it(mc["Z"]["d028"], 2)} a <b>{it(mc["X"]["fea"], 2)} / {it(mc["Y"]["fea"], 2)} / {it(mc["Z"]["fea"], 2)} N/µm</b>. Anche rendendo infinitamente rigida tutta quella zona, con il resto della macchina D028 invariato il limite è <b>{it(mc["X"]["limit"], 2)} / {it(mc["Y"]["limit"], 2)} / {it(mc["Z"]["limit"], 2)} N/µm</b>: il target D014 di 10 N/µm non si raggiunge lavorando solo su master e mount. Vanno migliorati, ma poi emerge subito il resto della struttura. Stima: slitta Z rigida qui, quindi il valore reale può essere più basso; lo conferma il gantry FEA.</div></section>

<section class="section split">
  <div class="panel"><span class="kicker">Modello</span><h2>Solidi dove conta, molle dove D028 le ha calibrate.</h2><p><b>Master</b> scatolata del mule (120 × 135 × 40, parete variabile), incastrata sulla striscia di appoggio sotto la slitta Z (y ≥ 53 mm, faccia superiore). <b>Accoppiamento ToolDock</b>: tre sfere su Ø80 a 90° / 210° / 330° (orientamento ipotizzato), per sfera una molla normale e una tangenziale kc di Hertz D028 tra patch rigide Ø12 su master e receiver: sommate danno esattamente la molla a 6 gdl di D028, ma le piastre sotto le sfere si deformano. <b>Testa</b>: receiver e mount a tazza incollati; corpo spindle come tubo in acciaio Ø45 / Ø35 incollato nel collare; cuscinetti con la molla D028; albero Ø16 fino al dado ER11. Il connettore non entra: il service envelope è un controllo CAD separato.</p><p><b>Carichi</b> su un punto di riferimento sul dado ER11 (corpo rigido sulla faccia del naso), mai su un nodo; sgancio sulla sede del clamp (Ø30 sulla faccia interna del fondo della master). Casi unitari risolti, combinati per sovrapposizione lineare: 150 N radiali totali + 200 N assiali, mai 150 X + 150 Y insieme. Materiali elastici effettivi: alluminio E 70 GPa, ν 0,33; acciaio 210 GPa, ν 0,30; snervamento non ancora usato.</p></div>
  <div class="panel"><span class="kicker">Verifiche</span><h2>Autotest e convergenza.</h2><p><b>Autotest</b>: con i moduli elastici ×10³ la FEA ridà la cedevolezza analitica di accoppiamento D028 e cuscinetti: attesi {it(st["expected"]["X"], 3)} N/µm in X e Y e {it(st["expected"]["Z"], 2)} in Z, ottenuti {it(st["got"]["X"], 3)} / {it(st["got"]["Y"], 3)} / {it(st["got"]["Z"], 2)} (errore {it(st["err"] * 100, 2)}%).</p><p><b>Mesh</b>: globale {it(r["h_nom"], 0)} mm, locale {it(r["h_local"], 1)} mm su sfere, radice della master, estremità del collare, cuscinetti e naso; fine con tutte le dimensioni −{fine_pct}%. Nominale {nom["mesh"]["elements"]:,} elementi ({nom["mesh"]["dof"] // 1000}k gdl), fine {fine["mesh"]["elements"]:,} ({fine["mesh"]["dof"] // 1000}k gdl). Spostamento alla punta:</p><div class="table-wrap"><table><tr><th>Caso</th><th>|u| nominale µm</th><th>|u| fine µm</th><th>Δ</th></tr>{conv_rows}</table></div></div>
</section>

<section class="section"><p><a class="btn primary" href="viewer-3d.html?m=pilot_nom_Fy_u.glb">Deformata in 3D · 150 N Y</a> <a class="btn" href="viewer-3d.html?m=pilot_nom_Fx_u.glb">150 N X</a> <a class="btn" href="viewer-3d.html?m=pilot_nom_Fy_vm.glb">Von Mises · 150 N Y</a></p></section>

<section class="section"><h2>Casi di carico · spostamenti</h2><div class="table-wrap"><table>
<tr><th>Caso</th><th>Punta X / Y / Z (µm)</th><th>|u| (µm)</th><th>N/µm</th></tr>
{case_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Mesh nominale; spostamento del dado ER11 rispetto alla slitta Z (qui rigida). Sgancio: la sede del clamp sale di {it(rel["seat_um"], 1)} µm sotto 0,7 kN.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">FEA ↔ D028</span><h2>Stessa catena, due modelli.</h2><div class="table-wrap"><table><tr><th>Asse</th><th>FEA N/µm</th><th>D028 N/µm</th><th>FEA / D028</th><th>Quote D028 nella macchina intera</th></tr>{cmp_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">D028 locale = cedevolezza di master, accoppiamento e testa al centro corsa, dalla ripartizione dell'energia del modello a travi.</p></div>
  <div class="panel"><span class="kicker">Macchina intera · stima</span><h2>D028 con la catena FEA.</h2><div class="table-wrap"><table><tr><th>Asse</th><th>D028</th><th>D028 + FEA locale</th><th>Limite, zona locale rigida</th><th>D014</th></tr>{mc_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">N/µm al centro corsa. Il resto della macchina (telaio, spalle, trave, guide e viti, carrello X, slitta Z, tavola) è quello del modello a travi D028.</p></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">Tensioni · non convergenti</span><h2>Basse, ma non ancora un dato.</h2><div class="table-wrap"><table><tr><th>Caso</th><th>Picco nominale → fine (MPa)</th><th>Hotspot nominale → fine (MPa)</th><th>Δ hotspot</th></tr>{hot_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Hotspot = massimo a più di 6 mm da vincoli e patch rigide. Cresce del 18–25% con la mesh fine: gli spigoli vivi del mule (senza raccordi) sono singolari. Nessun segnale di crisi di resistenza: il problema dominante è la cedevolezza. Le tensioni si chiudono con un submodel (1–1,5 mm solo alla radice master ↔ slitta e sui raccordi, raccordi reali al posto degli spigoli vivi), non con una mesh globale più fine.</p></div>
  <div class="panel"><span class="kicker">Tensioni per corpo · baseline</span><h2>Mesh ottimizzata.</h2><div class="table-wrap"><table><tr><th>Caso</th><th>Master</th><th>Receiver / mount</th><th>Corpo spindle</th><th>Albero Ø16</th></tr>{body_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Hotspot in MPa sulla mesh nominale con ottimizzazione high-order (Jacobiano scalato minimo {it(opt["mesh"].get("min_sj", 0), 2)}). Nell'albero Ø16 i 45 MPa dei casi a 18 N·m coincidono con M / W analitico. Nella prima mesh, senza ottimizzazione, alcune varianti avevano picchi nodali isolati non fisici (fino a migliaia di MPa) da tetra quadratici distorti: per questo le tensioni delle varianti non si usano.</p></div>
</section>

<section class="section"><div class="callout"><b>Lettura del pilota.</b> {findings}</div></section>

<section class="section"><h2>Varianti · master e mount</h2><div class="table-wrap"><table>
<tr><th>Variante</th><th>Massa</th><th>Δ massa</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th><th>Δ punta worst µm</th><th>kg / (N/µm)</th></tr>
{var_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Mesh nominale, spostamenti. Massa = master + receiver + mount (lo spindle non cambia). kg / (N/µm) = massa sulla rigidezza radiale minima tra X e Y; <b>Pareto</b> = nessun'altra variante è insieme più leggera e più rigida. Δ punta worst = massimo |u| tra i casi di forza.</p></section>

<section class="section"><div class="callout"><b>Fase 2 D031.</b> (1) Submodel delle tensioni con mesh 1–1,5 mm solo alla radice master ↔ slitta e sui raccordi reali. (2) Sottoassieme head + master + slitta Z con mount 56 mm e tre topologie del collegamento master ↔ slitta: baseline con la striscia da 12 mm; master con flangia posteriore profonda 40–60 mm fissata alla slitta; sella a U collegata anche alle due ali laterali della slitta, con il carico portato su due piani. La parete 10 mm da sola (+181 g, Y 0,68 → 0,82) non cambia il problema; la topologia del vincolo può cambiare la rigidezza di multipli con poca massa. (3) Poi rapidamente il gantry completo, prima di altre varianti locali: se conferma l'ordine di grandezza, la scelta è tra riposizionare D014 per la Standard e una revisione architetturale più profonda.</div></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d031.py</code> (CadQuery, gmsh, CalculiX <code>ccx</code>): autotest, mesh nominale e fine, varianti, <code>fea/d031/pilot.json</code> e questa pagina; <code>python tools/fea/d031_page.py</code> rigenera solo la pagina. File di lavoro in <code>build/fea/</code>, non versionati.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    write(json.loads((ROOT / "fea" / "d031" / "pilot.json").read_text()))
