#!/usr/bin/env python3
"""Pagina base/fea-d031.html dai risultati di tools/fea/d031.py (fea/d031/pilot.json). Non modificare a mano la pagina."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGE = ROOT / "base" / "fea-d031.html"
BODY = {"master": "master", "head_al": "receiver / mount", "spindle_body": "corpo spindle", "shaft": "albero"}


def it(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def where(v):
    return f'{BODY.get(v["body"], v["body"])} ({", ".join(it(c, 0) for c in v["at"])})'


def pareto(rows):
    """Varianti non dominate su (massa ↓, rigidezza minima X/Y ↑)."""
    out = set()
    for a in rows:
        dom = any(b["mass"] <= a["mass"] and b["kmin"] >= a["kmin"] and (b["mass"] < a["mass"] or b["kmin"] > a["kmin"]) for b in rows)
        if not dom:
            out.add(a["tag"])
    return out


def write(r):
    nom, conv, st, d28 = r["nominal"], r["convergence"], r["self_test"], r["d028"]
    c = nom["cases"]
    kx, ky, kz = (c[n]["k_N_um"] for n in ("Fx", "Fy", "Fz"))
    dmax = max(v["delta"] for v in conv.values())
    case_rows = "".join(
        f'<tr><td>{v["desc"]}</td><td>{" / ".join(it(u, 1) for u in v["tip_um"])}</td><td>{it(v["tip_abs_um"], 1)}</td>'
        f'<td>{it(v["vm_peak"]["MPa"], 1)} · {where(v["vm_peak"])}</td><td>{it(v["vm_hot"]["MPa"], 1)} · {where(v["vm_hot"])}</td></tr>'
        for n, v in c.items())
    rel = c["REL"]
    cmp_rows = "".join(
        f'<tr><td>{ax}</td><td><b>{it(k, 2)}</b></td><td>{it(d28[ax]["k_local"], 2)}</td><td>{it(k / d28[ax]["k_local"], 2)}</td>'
        f'<td>{" · ".join(f"{t} {it(s, 0)}%" for t, s in d28[ax]["share"].items())}</td></tr>'
        for ax, k in (("X", kx), ("Y", ky), ("Z", kz)))
    conv_rows = "".join(f'<tr><td>{n}</td><td>{it(v["nom"], 2)}</td><td>{it(v["fine"], 2)}</td><td class="{"status-ok" if v["delta"] < 0.05 else "status-critical"}">{it(v["delta"] * 100, 1)}%</td></tr>'
                        for n, v in conv.items())
    fine_hot = r["fine"]["cases"]
    hot_rows = "".join(f'<tr><td>{n}</td><td>{it(c[n]["vm_peak"]["MPa"], 1)} → {it(fine_hot[n]["vm_peak"]["MPa"], 1)}</td><td>{it(c[n]["vm_hot"]["MPa"], 1)} → {it(fine_hot[n]["vm_hot"]["MPa"], 1)}</td></tr>'
                       for n in conv)
    var = []
    base = r["variants"].get("master_w8")
    for tag, v in r["variants"].items():
        cc = v["cases"]
        m = v["mass"]["master"] + v["mass"]["head_al"]
        k = [cc[n]["k_N_um"] for n in ("Fx", "Fy", "Fz")]
        worst = max(cc[n]["tip_abs_um"] for n in ("Fx", "Fy", "Fz", "FxFz", "FyFz"))
        sig = max(cc[n]["vm_hot_body"][b] for n in cc for b in ("master", "head_al"))    # parti che cambiano nelle varianti
        var.append(dict(tag=tag, desc=v["desc"], mass=m, k=k, kmin=min(k[:2]), worst=worst, sig=sig))
    front = pareto(var)
    s0 = next((x["sig"] for x in var if x["tag"] == "master_w8"), None)
    for x in var:
        x["suspect"] = s0 is not None and x["sig"] > 4 * s0
    m0 = next((x["mass"] for x in var if x["tag"] == "master_w8"), None)
    var_rows = "".join(
        f'<tr><td>{x["desc"]}{" · <b>Pareto</b>" if x["tag"] in front else ""}</td><td>{it(x["mass"], 2)} kg</td>'
        f'<td>{("+" if x["mass"] - m0 > 0 else "") + it((x["mass"] - m0) * 1000, 0)} g</td>'
        f'<td>{it(x["k"][0], 2)}</td><td>{it(x["k"][1], 2)}</td><td>{it(x["k"][2], 1)}</td><td>{it(x["sig"], 1)}{" · da verificare" if x["suspect"] else ""}</td><td>{it(x["worst"], 0)}</td>'
        f'<td>{it(x["mass"] / x["kmin"], 2)}</td></tr>'
        for x in var) if base else '<tr><td colspan="9">Varianti non ancora calcolate (<code>--quick</code>).</td></tr>'
    vv = {x["tag"]: x for x in var}
    findings = (f'La catena locale è più cedevole di quanto dica D028: {it(kx, 2)} / {it(ky, 2)} N/µm in X / Y contro {it(d28["X"]["k_local"], 2)} / {it(d28["Y"]["k_local"], 2)} '
                f'(FEA / D028 = {it(kx / d28["X"]["k_local"], 2)} / {it(ky / d28["Y"]["k_local"], 2)}). Il modello a travi incastra la master sulla slitta; nel mule la master appoggia '
                f'sotto la slitta solo sulla striscia da {it(12, 0)} mm della piastra e sporge di ~{it(123, 0)} mm verso il naso: in Y lavora a flessione e la radice è anche il picco di tensione. ')
    if vv:
        findings += (f'La parete della master rende molto: 8 → 10 mm dà Y {it(vv["master_w8"]["k"][1], 2)} → {it(vv["master_w10"]["k"][1], 2)} N/µm per '
                     f'+{it((vv["master_w10"]["mass"] - vv["master_w8"]["mass"]) * 1000, 0)} g, 8 → 6 mm la fa crollare a {it(vv["master_w6"]["k"][1], 2)}. '
                     f'Il mount invece si può snellire: 60 → 56 mm toglie {it((vv["master_w8"]["mass"] - vv["mount_56"]["mass"]) * 1000, 0)} g e perde solo '
                     f'{it((1 - vv["mount_56"]["k"][1] / vv["master_w8"]["k"][1]) * 100, 0)}% in Y. Indicazione per la fase 2, non decisione: il materiale va spostato '
                     f'dal mount alla master e soprattutto all\'appoggio master ↔ slitta (più lungo in Y o fissato anche alle ali della slitta), da verificare nel sottoassieme head + master + Z. ')
    findings += f'Tensioni basse ovunque (hotspot ≤ ~{it(max(c[n]["vm_hot"]["MPa"] for n in ("Fx", "Fy", "Fz", "FxFz", "FyFz")), 0)} MPa nei casi di forza): la master è guidata dalla rigidezza, non dalla resistenza.'
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — FEA a solidi · D031</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/fea/d031.py (tools/fea/d031_page.py): non modificare a mano. -->
<a class="back" href="cad-standard.html">← CAD Standard · mule</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D031 · FEA a solidi · fase 1 pilota</div><h1>FEA<br>a solidi.</h1><p class="lead">Prima fase della D031: FEA lineare statica del modello pilota <b>master ToolDock + testa 5045-style</b> del mule v2, con la pipeline che servirà per tutti gli altri pezzi. Geometria dal CAD del mule (stesse funzioni di <code>standard_assembly.py</code>), mesh Gmsh a tetraedri quadratici, CalculiX, lettura automatica dei risultati. Guide, viti e ToolDock restano molle equivalenti calibrate come in D028, così il confronto con D028 è diretto. Valori di progetto, non misure.</p><div class="badges"><span class="badge ok">D031 · pilota</span><span class="badge">CalculiX + Gmsh · C3D10</span><span class="badge">Slitta Z rigida in questa fase</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{it(kx, 2)} / {it(ky, 2)} / {it(kz, 1)}</strong><span>N/µm della catena locale X / Y / Z (master + accoppiamento + testa)</span></div>
  <div class="metric"><strong>{it(d28["X"]["k_local"], 2)} / {it(d28["Y"]["k_local"], 2)} / {it(d28["Z"]["k_local"], 0)}</strong><span>N/µm della stessa catena nel modello a travi D028</span></div>
  <div class="metric"><strong>{it(dmax * 100, 1)}%</strong><span>variazione alla punta con la mesh −{it((1 - r["fine"]["h"] / r["h_nom"]) * 100, 0)}% · limite 5%</span></div>
  <div class="metric"><strong>{nom["mesh"]["dof"] // 1000}k</strong><span>gradi di libertà nominali · {it(nom["solve_s"], 0)} s di soluzione</span></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">Modello</span><h2>Solidi dove conta, molle dove D028 le ha calibrate.</h2><p><b>Master</b> scatolata del mule (120 × {it(135, 0)} × 40, parete variabile), incastrata sulla striscia di appoggio sotto la slitta Z (y ≥ {it(53, 0)} mm, faccia superiore). <b>Accoppiamento ToolDock</b>: tre sfere su Ø80 a 90° / 210° / 330° (orientamento ipotizzato), per sfera una molla normale e una tangenziale kc di Hertz D028 tra patch rigide Ø12 su master e receiver: sommate danno esattamente la molla a 6 gdl di D028, ma le piastre sotto le sfere si deformano. <b>Testa</b>: receiver e mount a tazza incollati; corpo spindle come tubo in acciaio Ø45 / Ø35 incollato nel collare; cuscinetti con la molla D028; albero Ø16 fino al dado ER11. Il connettore non entra: il service envelope è un controllo CAD separato.</p><p><b>Carichi</b> su un punto di riferimento sul dado ER11 (corpo rigido sulla faccia del naso), mai su un nodo; sgancio sulla sede del clamp (Ø30 sulla faccia interna del fondo della master). Casi unitari risolti, combinati per sovrapposizione lineare dei tensori: 150 N radiali totali + 200 N assiali, mai 150 X + 150 Y insieme. Materiali elastici effettivi: alluminio E 70 GPa, ν 0,33; acciaio 210 GPa, ν 0,30; snervamento non ancora usato.</p></div>
  <div class="panel"><span class="kicker">Autotest della pipeline</span><h2>Molle e corpi rigidi verificati.</h2><p>Con i moduli elastici ×10³ la FEA deve ridare la cedevolezza analitica di accoppiamento D028 e cuscinetti: attesi {it(st["expected"]["X"], 3)} N/µm in X e Y e {it(st["expected"]["Z"], 2)} in Z, ottenuti {it(st["got"]["X"], 3)} / {it(st["got"]["Y"], 3)} / {it(st["got"]["Z"], 2)}: errore {it(st["err"] * 100, 2)}% ({"PASSA" if st["ok"] else "NON PASSA"}).</p><p><b>Mesh</b>: globale {it(r["h_nom"], 0)} mm, locale {it(r["h_local"], 1)} mm su sfere, radice della master, estremità del collare, cuscinetti e naso; convergenza con tutte le dimensioni −{it((1 - r["fine"]["h"] / r["h_nom"]) * 100, 0)}% (D031 chiede ~30%: con SPOOLES la mesh −30%, ~950k gdl, supera la memoria del container). Nominale {nom["mesh"]["elements"]:,} elementi, fine {r["fine"]["mesh"]["elements"]:,}.</p><div class="table-wrap"><table><tr><th>Caso</th><th>|u| nominale µm</th><th>|u| fine µm</th><th>Δ</th></tr>{conv_rows}</table></div></div>
</section>

<section class="section"><h2>Casi di carico · mesh nominale</h2><div class="table-wrap"><table>
<tr><th>Caso</th><th>Punta X / Y / Z (µm)</th><th>|u| (µm)</th><th>σ VM picco (MPa) · dove</th><th>σ VM hotspot (MPa) · dove</th></tr>
{case_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">Spostamento del dado ER11 rispetto alla slitta Z (qui rigida). Hotspot = massimo a più di 6 mm da vincoli e patch rigide, esclusi i nodi degli elementi con Jacobiano scalato &lt; 0,2 (mesh nominale: minimo {it(nom["mesh"]["min_sj"], 2)}, {nom["mesh"]["poor"]} elementi sotto soglia); gli spigoli vivi rientranti del mule (senza raccordi) restano singolari, quindi il picco va letto con la convergenza: se cresce con la mesh fine è una singolarità, non una tensione di progetto. Sgancio: la sede del clamp sale di {it(rel["seat_um"], 1)} µm sotto 0,7 kN.</p></section>

<section class="section split">
  <div class="panel"><span class="kicker">FEA ↔ D028</span><h2>Stessa catena, due modelli.</h2><div class="table-wrap"><table><tr><th>Asse</th><th>FEA N/µm</th><th>D028 N/µm</th><th>FEA / D028</th><th>Quote D028 nella macchina intera</th></tr>{cmp_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">D028 locale = cedevolezza di master, accoppiamento e testa al centro corsa, dalla ripartizione dell'energia del modello a travi (macchina intera {it(d28["X"]["k_machine"], 2)} / {it(d28["Y"]["k_machine"], 2)} / {it(d28["Z"]["k_machine"], 2)} N/µm).</p></div>
  <div class="panel"><span class="kicker">Tensioni · convergenza</span><h2>Picchi da leggere con cautela.</h2><div class="table-wrap"><table><tr><th>Caso</th><th>Picco nominale → fine</th><th>Hotspot nominale → fine</th></tr>{hot_rows}</table></div></div>
</section>

<section class="section"><div class="callout"><b>Lettura del pilota.</b> {findings}</div></section>

<section class="section"><h2>Varianti · master e mount</h2><div class="table-wrap"><table>
<tr><th>Variante</th><th>Massa</th><th>Δ massa</th><th>X N/µm</th><th>Y N/µm</th><th>Z N/µm</th><th>σ VM hotspot master / mount (MPa)</th><th>Δ punta worst µm</th><th>kg / (N/µm)</th></tr>
{var_rows}</table></div>
<p style="color:var(--dim);font-size:13px;margin-top:12px">"Da verificare": hotspot oltre 4 volte quello della variante di riferimento, isolato in un solo elemento: tipico di un tetraedro distorto, non di una tensione di progetto; si ricontrolla con una mesh diversa prima di usarlo. Massa = master + receiver + mount (lo spindle non cambia). kg / (N/µm) = massa sulla rigidezza radiale minima tra X e Y; <b>Pareto</b> = nessun'altra variante è insieme più leggera e più rigida. Δ punta worst = massimo |u| tra i casi di forza.</p></section>

<section class="section"><div class="callout"><b>Prossimi passi D031.</b> Sottoassiemi head + master + slitta Z, poi + carrello X, poi gantry completo, con la stessa pipeline e le molle D028 per guide e viti; spalle e trave 6 mm baseline + variante 5 mm; tabella finale per variante e frontiera Pareto massa / rigidezza. Obiettivo: recuperare ≥ 2,8 kg mantenendo o migliorando la cedevolezza del mule v2. Il ToolDock resta una molla equivalente finché il test al banco non ne dà la rigidezza misurata.</div></section>

<section class="section"><h2>Rigenerare</h2><p><code>python tools/fea/d031.py</code> (CadQuery, gmsh, CalculiX <code>ccx</code>): autotest, mesh nominale e fine, varianti, <code>fea/d031/pilot.json</code> e questa pagina. File di lavoro in <code>build/fea/</code>, non versionati.</p></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    write(json.loads((ROOT / "fea" / "d031" / "pilot.json").read_text()))
    sys.exit(0)
