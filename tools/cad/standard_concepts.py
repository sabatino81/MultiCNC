#!/usr/bin/env python3
"""D032 · varianti del mule Standard come override espliciti del mule v3 (baseline certificata D031).

standard_params.py resta il mule v3; un concept è un dizionario di attributi di standard_params che vengono
sovrascritti in memoria da apply(nome). apply("V3") ripristina la baseline. Dopo apply, i moduli già importati che
tengono in cache le quote derivate (standard_assembly, d031, compliance_d028) vengono riallineati.

Uso: standard_assembly.py --concept A1 (CAD, sweep, trasferitore, masse in cad/concepts/A1/)
     tools/fea/d031_gantry.py --concept A1 (gantry FEA con energia, fea/d032/A1.json)

Concept A (compact chain, ICD v4): asse spindle a 53 mm, piano cinematico, Ø80, pull-stud, datum e inviluppo ICD
invariati; si cambia la struttura attorno all'asse, una modifica alla volta:
A0 = mule v3 · A1 = master + slitta monoscocca · A2 = A1 + carrello scatolato · A3 = A2 + trave ad alta inerzia a
massa costante · A4 = combinazione ottimizzata.
"""
import copy
import sys

import standard_params as P

_BASE = {k: copy.deepcopy(v) for k, v in vars(P).items() if k.isupper()}

CONCEPTS = {
    "V3": dict(desc="Mule v3 (baseline D031)", over={}),
    "A0": dict(desc="A0 · mule v3, riferimento", over={}),
    # A1: la master diventa una scatola chiusa con la slitta: pareti laterali contro le ali, parete anteriore e
    # cielo sopra il piano della master, schiena = faccia anteriore della slitta (incollata). Sostituisce la sella.
    "A1": dict(desc="A1 · master + slitta monoscocca, h 100", over={"MONOCOQUE": dict(h=100.0, wall=6.0), "SADDLE": None}),
    "A1s": dict(desc="A1s · monoscocca bassa, h 60", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None}),
    # A2: A1s + carrello X a cassone: zaino scatolato dietro la piastra, sopra trave e catena X (z ≥ 392, 16 mm dalla
    # catena), profondo fino a y 200; pattini X, guide Z, asse, ToolDock e master A1s invariati.
    "A2": dict(desc="A2 · A1s + carrello a cassone (zaino 4 mm)", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                                                                         "CARRIAGE_BOX": dict(z0=392.0, y1=200.0, wall=4.0)}),
}


def apply(name):
    """Ripristina la baseline e applica gli override del concept; riallinea le quote derivate nei moduli caricati."""
    if name not in CONCEPTS:
        raise SystemExit(f"concept sconosciuto {name}: {', '.join(CONCEPTS)}")
    for k, v in _BASE.items():
        setattr(P, k, copy.deepcopy(v))
    for k in [k for k in vars(P) if k.isupper() and k not in _BASE]:
        delattr(P, k)
    for k, v in CONCEPTS[name]["over"].items():
        setattr(P, k, copy.deepcopy(v))
    d = P.derived()
    for mod in ("standard_assembly", "d031", "compliance_d028"):
        m = sys.modules.get(mod)
        if m is not None and hasattr(m, "D"):
            m.D = d
    return CONCEPTS[name]


def overrides(name):
    return CONCEPTS[name]["over"]
