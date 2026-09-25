#!/usr/bin/env python3
"""D029 · ToolDock / Head Structural Optimisation (studio, ICD v4 resta la baseline).

Campagna parametrica sul modello di cedevolezza D028 (tools/calc/compliance_d028.py):
1. master, slitta Z e carrello X scatolati (proposta D028);
2. testa reale: spindle 0,8 kW ER11 Ø65 × 208 mm raffreddato ad aria al posto dell'inviluppo rigido;
3. offset asse utensile ↔ slitta Z: 35 / 45 / 55 / 70 mm;
4. accoppiamento Ø80 / 1,6 kN (baseline) e varianti Ø90 / 2,4 kN, Ø100 / 3,2 kN;
5. ripartizione separata master strutturale / accoppiamento cinematico;
6. sensibilità ai parametri incerti (pattini, chiocciole, cuscinetti, motore, accoppiamento, spindle);
7. previsioni per il test al banco del solo ToolDock.

La geometria delle varianti vale solo nel modello: la variante scelta va riportata in
standard_params.py e ricontrollata con il CAD (collisioni, sweep, trasferitore).
Uso (con numpy): python tools/calc/tooldock_d029.py
"""
import copy
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "cad"))
import compliance_d028 as C  # noqa: E402
import standard_params as P  # noqa: E402

BASE = copy.deepcopy(dict(HEAD=P.HEAD, AXIS=P.HEAD_AXIS_FROM_SLIDE))

# spindle candidato (quote tipiche di mercato, da confermare sul pezzo reale)
SPINDLE = dict(name="0,8 kW ER11 Ø65 × 208 mm, aria", d=65.0, body=208.0, mass=2.2,
               receiver=15.0, clamp_band=40.0, nut=20.0, stickout=0.0, k_bearing=40e3, body_t=5.0, mandrel_d=17.0)
TOOL = dict(d=6.0, stickout=25.0, E=600000.0)          # fresa in metallo duro Ø6 in ER11 (max 7 mm): fuori dal punto di misura D014


def tool_k():
    d, L, E = TOOL["d"], TOOL["stickout"], TOOL["E"]
    return 3 * E * math.pi * d ** 4 / 64 / L ** 3       # N/mm, mensola incastrata sulla pinza
RECEIVER_MASS = 0.6
BOXED = dict(master=C.tube(P.MASTER["W"], 50.0, 8.0), slide=C.tube(150.0, 50.0, 8.0), carriage=C.tube(170.0, 60.0, 6.0))
COUPLINGS = [("Ø80 · 1,6 kN (ICD v4)", 40.0, 1600.0), ("Ø90 · 2,4 kN", 45.0, 2400.0), ("Ø100 · 3,2 kN", 50.0, 3200.0)]


def head_hanging():
    s = SPINDLE
    L = s["receiver"] + s["body"] + s["nut"] + s["stickout"]
    return L, dict(clamp=s["receiver"] + s["clamp_band"], nose=s["receiver"] + s["body"], body_d=s["d"], body_t=s["body_t"],
                   k_bearing=s["k_bearing"], mandrel_d=s["mandrel_d"])


def head_envelope():
    """Testa che sta nell'inviluppo 220 mm: spindle più corto della stessa classe (ipotesi)."""
    s = SPINDLE
    L = 220.0
    return L, dict(clamp=s["receiver"] + s["clamp_band"], nose=L - s["nut"] - s["stickout"], body_d=s["d"], body_t=s["body_t"],
                   k_bearing=s["k_bearing"], mandrel_d=s["mandrel_d"])


def head_through():
    """Testa passante: l'accoppiamento abbraccia il corpo dello spindle a metà altezza."""
    s = SPINDLE
    nose = s["body"] / 2
    L = nose + s["nut"] + s["stickout"]
    return L, dict(clamp=20.0, nose=nose, body_d=s["d"], body_t=s["body_t"], k_bearing=s["k_bearing"], mandrel_d=s["mandrel_d"])


HEADS = {"appesa (reale)": head_hanging, "nell'inviluppo 220": head_envelope, "passante": head_through}


def run(head=None, axis=70.0, coupling=COUPLINGS[0], sec=None, rigid_head_L=None, factors=None):
    """Ritorna la cedevolezza al centro corsa per la variante."""
    P.HEAD = dict(BASE["HEAD"])
    s = dict(sec or {})
    if head is not None:
        L, hd = HEADS[head]()
        P.HEAD["L"] = L
        s["head"] = hd
    elif rigid_head_L:
        P.HEAD["L"] = rigid_head_L
    P.HEAD_AXIS_FROM_SLIDE = axis
    C.D = P.derived()
    _, C.COUPLING_R, C.HERTZ_PRELOAD = coupling
    for k, v in (factors or {}).items():
        setattr(C, k, v)
    L_used = P.HEAD["L"]
    try:
        r = C.compliance(*P.CONFIGS["CENTER"], sec=s)
    finally:
        C.COUPLING_R, C.HERTZ_PRELOAD = 40.0, 1600.0
        for k in (factors or {}):
            setattr(C, k, 1.0)
        P.HEAD, P.HEAD_AXIS_FROM_SLIDE = dict(BASE["HEAD"]), BASE["AXIS"]
        C.D = P.derived()
    r.pop("_mass", None)
    return dict(N_per_um={ax: round(r[ax]["N_per_um"], 2) for ax in "XYZ"},
                share={ax: {k: round(v * 100, 1) for k, v in r[ax]["share"].items()} for ax in "XYZ"},
                L=L_used)


def bench(coupling, L):
    """Test al banco del solo accoppiamento: leva L, carico laterale F, master e receiver rigidi."""
    _, R, Pre = coupling
    C.COUPLING_R, C.HERTZ_PRELOAD = R, Pre
    k, kc = C.coupling_k()
    C.COUPLING_R, C.HERTZ_PRELOAD = 40.0, 1600.0
    per_N = L ** 2 / k[3] + 1 / k[0]            # mm/N
    return dict(k_rot_Nm_per_urad=round(k[3] / 1e9, 3), k_lat_N_per_um=round(k[0] / 1e3, 1), contact_N_per_um=round(kc / 1e3, 1),
                um_at={F: round(F * per_N * 1e3, 1) for F in (50, 100, 150)}, N_per_um=round(1 / (per_N * 1e3), 2))


def cog_below_coupling(head):
    s = SPINDLE
    L, hd = HEADS[head]()
    body_mid = hd["nose"] - s["body"] / 2
    return round((s["mass"] * body_mid + RECEIVER_MASS * s["receiver"] / 2) / (s["mass"] + RECEIVER_MASS), 0)


def main():
    out = {}
    steps = [
        ("D028 · mule v1.1, testa rigida 220", dict()),
        ("+ master, slitta Z e carrello X scatolati", dict(sec=BOXED)),
        ("+ testa reale appesa (spindle Ø65 × 208)", dict(sec=BOXED, head="appesa (reale)")),
        ("testa reale nell'inviluppo 220 (spindle più corto)", dict(sec=BOXED, head="nell'inviluppo 220")),
        ("testa reale passante (accoppiamento a metà spindle)", dict(sec=BOXED, head="passante")),
    ]
    out["steps"] = [dict(name=n, **run(**kw)) for n, kw in steps]
    out["axis"] = {head: [dict(axis=a, **run(sec=BOXED, head=head, axis=a)) for a in (35.0, 45.0, 55.0, 70.0)]
                   for head in ("appesa (reale)", "passante")}
    out["coupling"] = {head: [dict(name=c[0], **run(sec=BOXED, head=head, coupling=c)) for c in COUPLINGS]
                       for head in ("appesa (reale)", "passante")}
    best_kw = dict(sec=BOXED, head="passante", axis=45.0, coupling=COUPLINGS[1])
    out["best"] = dict(name="Scatolati + testa passante + asse a 45 mm + Ø90 · 2,4 kN", **run(**best_kw))
    plus = dict(best_kw, sec=dict(BOXED, upright=C.tube(60.0, 120.0, 6.0)))
    out["best_plus"] = [dict(name="… + spalle scatolate 60 × 120 sp. 6 (+0,2 kg)", **run(**plus)),
                        dict(name="… + tavola equivalente 14 mm (+2,6 kg)", **run(**dict(plus, sec=dict(plus["sec"], table_t=14.0))))]
    hang_kw = dict(sec=BOXED, head="appesa (reale)", axis=45.0, coupling=COUPLINGS[1])
    out["best_hanging"] = dict(name="Scatolati + testa appesa + asse a 45 mm + Ø90 · 2,4 kN", **run(**hang_kw))
    sens = []
    for label, f in [("Laterale pattini = 0,5 × radiale", dict(F_LAT=0.5)), ("Chiocciole ×0,5", dict(F_NUT=0.5)), ("Chiocciole ×2", dict(F_NUT=2.0)),
                     ("Cuscinetti vite ×0,5", dict(F_BEARING=0.5)), ("Tenuta motore ×0,5", dict(F_MOTOR=0.5)),
                     ("Accoppiamento ×0,5 (Hertz ottimistico)", dict(COUPLING_SCALE=0.5)), ("Accoppiamento ×2", dict(COUPLING_SCALE=2.0))]:
        sens.append(dict(name=label, **run(**best_kw, factors=f)))
    for label, kb in (("Cuscinetti spindle 20 N/µm", 20e3), ("Cuscinetti spindle 80 N/µm", 80e3)):
        SPINDLE["k_bearing"] = kb
        sens.append(dict(name=label, **run(**best_kw)))
        SPINDLE["k_bearing"] = 40e3
    out["sensitivity"] = sens
    out["bench"] = {c[0]: {L: bench(c, L) for L in (124.0, 220.0, 243.0)} for c in COUPLINGS}
    out["tool"] = dict(k_N_per_um=round(tool_k() / 1e3, 1), **TOOL,
                       best_with_tool={ax: round(1 / (1 / out["best"]["N_per_um"][ax] + (1e3 / tool_k() if ax != "Z" else 0)), 2) for ax in "XYZ"})
    out["heads"] = {h: dict(L=HEADS[h]()[0], cog=cog_below_coupling(h), mass=round(SPINDLE["mass"] + RECEIVER_MASS, 1)) for h in HEADS}
    for st in out["steps"]:
        print(f"{st['name']:<55} L {st['L']:>5.0f}", st["N_per_um"])
    for h, rows in out["axis"].items():
        print("asse", h, [(r["axis"], r["N_per_um"]) for r in rows])
    for h, rows in out["coupling"].items():
        print("coupling", h, [(r["name"], r["N_per_um"]) for r in rows])
    print("best", out["best"]["N_per_um"], "appesa", out["best_hanging"]["N_per_um"])
    for sn in sens:
        print("  sens", sn["name"], sn["N_per_um"])
    print("teste", out["heads"])
    print("banco", {k: v[220.0] for k, v in out["bench"].items()})
    write_page(out)
    (ROOT / "tools" / "calc" / "tooldock_d029.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def it(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def nrow(name, r, extra=""):
    return f'<tr><td>{name}</td>{extra}' + "".join(f"<td>{it(r['N_per_um'][ax])}</td>" for ax in "XYZ") + "</tr>"


def shares_row(r, tags):
    return "".join(f"<tr><td>{t}</td>" + "".join(f"<td>{it(r['share'][ax].get(t, 0.0), 0)}%</td>" for ax in "XYZ") + "</tr>" for t in tags)


def write_page(o):
    s = SPINDLE
    step_rows = "".join(nrow(st["name"], st, f'<td>{it(st["L"], 0)} mm</td>') for st in o["steps"])
    axis_rows = ""
    for h, rows in o["axis"].items():
        for r in rows:
            note = " <small style='color:var(--crit)'>solo teorico con Ø65</small>" if r["axis"] < s["d"] / 2 + 5 else ""
            axis_rows += nrow(f"{h} · asse a {it(r['axis'], 0)} mm{note}", r)
    cpl_rows = "".join(nrow(f"{h} · {r['name']}", r) for h, rows in o["coupling"].items() for r in rows)
    sens_rows = "".join(nrow(sn["name"], sn) for sn in o["sensitivity"])
    best, bh = o["best"], o["best_hanging"]
    tags = ["master ToolDock", "accoppiamento ToolDock", "testa (spindle + utensile)", "slitta Z", "guide Z + vite Z", "carrello X",
            "guide X + vite X", "trave", "spalle", "telaio", "tavola", "guide Y + vite Y"]
    head_rows = "".join(f'<tr><td>{h}</td><td>{it(v["L"], 0)} mm</td><td>{it(v["mass"], 1)} kg</td>'
                        f'<td class="{"status-ok" if v["cog"] <= 80 else "status-critical"}">{it(v["cog"], 0)} mm</td>'
                        f'<td class="{"status-ok" if v["L"] <= 220 else "status-critical"}">{"sì" if v["L"] <= 220 else "no"}</td></tr>'
                        for h, v in o["heads"].items())
    b0 = o["bench"][COUPLINGS[0][0]]
    bench_rows = "".join(f'<tr><td>{c}</td><td>{it(v[220.0]["k_rot_Nm_per_urad"] * 1e3, 0)} N·m/mrad</td>'
                         + "".join(f'<td>{it(v[220.0]["um_at"][F], 0)} µm</td>' for F in (50, 100, 150))
                         + f'<td>{it(v[243.0]["um_at"][150], 0)} µm</td></tr>' for c, v in o["bench"].items())
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#05070b"><title>MultiCNC — ToolDock e testa · D029</title><link rel="stylesheet" href="../assets/styles.css"><style>.split>.panel{{min-width:0}}</style></head><body><main class="shell page">
<!-- Pagina generata da tools/calc/tooldock_d029.py: non modificare a mano. -->
<a class="back" href="compliance-d028.html">← Rigidezza · D028</a>
<div class="pagehead"><div class="eyebrow">02 · Base Standard · D029 · studio · ICD v4 baseline</div><h1>ToolDock<br>e testa.</h1><p class="lead">Ottimizzazione strutturale dei primi 100–300 mm della catena, vicino alla punta: master, slitta Z, carrello X, accoppiamento e testa reale. Stessa architettura, stessa trave, stesso telaio. Campagna parametrica sul modello D028; la ICD v4 resta la baseline finché il test al banco non conferma il modello. D014 (≥ 10 N/µm) resta TARGET.</p><div class="badges"><span class="badge ok">D029 · studio</span><span class="badge">Spindle candidato: {s["name"]}</span><span class="badge">Centro corsa · N/µm</span></div></div>

<section class="metric-grid">
  <div class="metric"><strong>{it(o["steps"][0]["N_per_um"]["X"])} → {it(best["N_per_um"]["X"])}</strong><span>N/µm in X, da D028 al miglior caso D029</span></div>
  <div class="metric"><strong>{it(o["steps"][0]["N_per_um"]["Y"])} → {it(best["N_per_um"]["Y"])}</strong><span>N/µm in Y</span></div>
  <div class="metric"><strong>{it(o["steps"][0]["N_per_um"]["Z"])} → {it(best["N_per_um"]["Z"])}</strong><span>N/µm in Z</span></div>
  <div class="metric"><strong>≥ 10</strong><span>N/µm target D014 · non ancora raggiunto</span></div>
</section>

<section class="section"><h2>1–2 · Piastre scatolate e testa reale</h2><div class="table-wrap"><table>
<tr><th>Variante</th><th>Coupling → punta</th><th>X</th><th>Y</th><th>Z</th></tr>{step_rows}
</table></div><p style="color:var(--dim);font-size:13px;margin-top:12px">Testa reale: corpo spindle in acciaio Ø{it(s["d"], 0)} (parete equivalente {it(s["body_t"], 0)} mm) a sbalzo dal collare del receiver, cuscinetti {it(s["k_bearing"] / 1e3, 0)} N/µm al naso, dado ER11 {it(s["nut"], 0)} mm: il punto di misura è la faccia del dado ER11 (asse albero Ø{it(s["mandrel_d"], 0)} dal naso al dado), non la punta di una fresa: una fresa in metallo duro Ø{it(TOOL["d"], 0)} con {it(TOOL["stickout"], 0)} mm di sporgenza vale da sola ~{it(o["tool"]["k_N_per_um"], 1)} N/µm, e il miglior caso D029 con quella fresa scende a {it(o["tool"]["best_with_tool"]["X"])} / {it(o["tool"]["best_with_tool"]["Y"])} N/µm in X / Y. D014 va quindi riferito al naso dello spindle (o a un mandrino di prova rigido), non all'utensile.</p></section>

<section class="section split">
  <div class="panel" style="border-color:rgba(255,84,112,.35)"><span class="kicker">Testa reale vs ICD v4</span><h2>Lo spindle appeso non ci sta.</h2><div class="table-wrap"><table><tr><th>Montaggio</th><th>Coupling → punta</th><th>Massa testa</th><th>Baricentro sotto il coupling (ICD ≤ 80)</th><th>Nell'inviluppo 220</th></tr>{head_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Con lo spindle Ø65 × 208 appeso sotto il coupling la punta arriva a {it(o["heads"]["appesa (reale)"]["L"], 0)} mm e il baricentro a {it(o["heads"]["appesa (reale)"]["cog"], 0)} mm: fuori dall'inviluppo classe S e dal limite di baricentro su cui è dimensionato il clamp (D016). Serve uno spindle più corto oppure la testa passante.</p></div>
  <div class="panel"><span class="kicker">Testa passante</span><h2>Accoppiamento attorno allo spindle.</h2><p>Il cerchio delle sfere abbraccia il corpo dello spindle a metà altezza: la parte alta dello spindle sale dentro una master cava e la leva dal coupling alla punta scende a {it(o["heads"]["passante"]["L"], 0)} mm, con il baricentro quasi sul piano del coupling. Richiede una master ad anello, una slitta Z con finestra e una nuova definizione dell'inviluppo sopra il coupling: è una modifica di ICD, da valutare solo dopo il test al banco.</p></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">3 · Offset asse utensile ↔ slitta Z</span><h2>Più vicino, più rigido.</h2><div class="table-wrap"><table><tr><th>Variante</th><th>X</th><th>Y</th><th>Z</th></tr>{axis_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Oggi l'asse sta a 70 mm dalla faccia della slitta (metà profondità dell'inviluppo). Con uno spindle Ø{it(s["d"], 0)} il minimo realistico è ~45 mm (raggio + parete del receiver); 35 mm è solo teorico. Il braccio a verso la trave scende di conseguenza.</p></div>
  <div class="panel"><span class="kicker">4 · Accoppiamento cinematico</span><h2>Ø80 → Ø100.</h2><div class="table-wrap"><table><tr><th>Variante</th><th>X</th><th>Y</th><th>Z</th></tr>{cpl_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Raggio e precarico insieme: più precarico significa pacco molle e camma D016 da ricalcolare (Z allo sgancio, fatica ≥ 20.000 cicli).</p></div>
</section>

<section class="section split">
  <div class="panel"><span class="kicker">5 · Ripartizione · miglior caso</span><h2>{best["name"]}.</h2><div class="table-wrap"><table><tr><th>Sottosistema</th><th>X</th><th>Y</th><th>Z</th></tr>{shares_row(best, tags)}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Stesso caso con la testa appesa (ICD v4): {it(bh["N_per_um"]["X"])} / {it(bh["N_per_um"]["Y"])} / {it(bh["N_per_um"]["Z"])} N/µm.</p></div>
  <div class="panel"><span class="kicker">6 · Sensibilità · miglior caso</span><h2>Quanto sono sicuri i numeri.</h2><div class="table-wrap"><table><tr><th>Parametro</th><th>X</th><th>Y</th><th>Z</th></tr>{nrow("Miglior caso nominale", best)}{sens_rows}</table></div></div>
</section>

<section class="section"><h2>Dopo il locale · cosa viene fuori</h2><div class="table-wrap"><table><tr><th>Variante</th><th>X</th><th>Y</th><th>Z</th></tr>{nrow(best["name"], best)}{"".join(nrow(r["name"], r) for r in o["best_plus"])}</table></div><p style="color:var(--dim);font-size:13px;margin-top:12px">Sistemata la zona vicino alla punta, i contributi diventano globali e distribuiti: spalle (piastre da 15 mm che lavorano nel loro spessore in X), tavola in Z, telaio e trave. Le spalle scatolate costano pochissimo; la tavola più rigida costa massa.</p></section>

<section class="section"><h2>7 · Test al banco del solo ToolDock</h2><div class="split" style="display:grid;gap:22px">
  <div class="panel"><span class="kicker">Prova</span><h2>Prima di congelare qualsiasi interfaccia.</h2><div class="spec-list">
    <div class="spec-row"><b>Setup</b><p>Master + receiver + pull-stud su banco rigido (piastra di ghisa o granito), clamp al precarico di classe S; leva di prova in acciaio Ø30 fissata al receiver con punto di carico a 124, 220 e 243 mm sotto il coupling (testa passante, inviluppo, spindle appeso).</p></div>
    <div class="spec-row"><b>Carichi</b><p>50 / 100 / 150 N laterali (dinamometro o pesi con rinvio), in X e in Y, 3 cicli di carico-scarico per livello; poi a 2 livelli di precarico del clamp.</p></div>
    <div class="spec-row"><b>Misura</b><p>Comparatore da 1 µm al punto di carico e un secondo comparatore sul receiver vicino al coupling, per separare rotazione dell'accoppiamento e flessione della leva. Ripetibilità: 10 sgancio/aggancio con misura del ritorno a zero.</p></div>
    <div class="spec-row"><b>Esito</b><p>Se la rigidezza misurata sta entro ±30% della previsione, il modello Hertz resta valido per D029; se è molto più bassa, prima di tutto va cambiato il tipo di contatto, non il resto della macchina.</p></div>
  </div></div>
  <div class="panel"><span class="kicker">Previsione del modello</span><h2>Spostamento al punto di carico.</h2><div class="table-wrap"><table><tr><th>Accoppiamento</th><th>Rigidezza rot.</th><th>50 N @220</th><th>100 N @220</th><th>150 N @220</th><th>150 N @243</th></tr>{bench_rows}</table></div><p style="color:var(--dim);font-size:13px;margin-top:10px">Solo accoppiamento (Hertz sfera Ø10 – piano, contatti a 45°), master e leva rigidi. La rigidezza di Hertz cresce con il carico: a 150 N la curva non sarà lineare, ed è proprio questo che la prova deve mostrare.</p></div>
</div></section>

<section class="section"><div class="callout"><b>Lettura:</b> la direzione giusta è locale. Con le piastre scatolate, una testa reale più corta o passante, l'asse più vicino alla slitta e un accoppiamento un po' più grande, il modello passa da {it(o["steps"][0]["N_per_um"]["X"])} / {it(o["steps"][0]["N_per_um"]["Y"])} / {it(o["steps"][0]["N_per_um"]["Z"])} a {it(best["N_per_um"]["X"])} / {it(best["N_per_um"]["Y"])} / {it(best["N_per_um"]["Z"])} N/µm in X / Y / Z senza toccare trave, telaio o materiali; con spalle scatolate e tavola più rigida arriva a {it(o["best_plus"][-1]["N_per_um"]["X"])} / {it(o["best_plus"][-1]["N_per_um"]["Y"])} / {it(o["best_plus"][-1]["N_per_um"]["Z"])}. Il target D014 non è ancora raggiunto. Prossimi passi: test al banco del ToolDock (valida o smentisce il modello Hertz), scelta dello spindle, FEA a solidi di carrello, slitta, master e spalle scatolati. Solo dopo si sceglie tra ICD v5 e revisione di D014.</div></section>
</main><script src="../assets/nav.js"></script></body></html>
"""
    (ROOT / "base" / "tooldock-d029.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
