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
import pathlib
import sys

import standard_params as P

_CALC = str(pathlib.Path(__file__).resolve().parents[1] / "calc")   # compliance_d028 (override del ToolDock)
if _CALC not in sys.path:
    sys.path.insert(0, _CALC)

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
    # C (ToolDock challenger, candidato ICD v5): base A1s; diametro e preload delle sfere separati; receiver allargato
    # quanto basta a ospitare le sfere (patch Ø12 + 8 mm) e inviluppo testa largo di conseguenza.
    "C0": dict(desc="C0 · A1s, riferimento", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None}),
    "C1a": dict(desc="C1a · coupling Ø100, preload 1,6 kN", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                "compliance_d028.COUPLING_R": 50.0, "SPINDLE_BASE": "sp:receiver_w=116", "HEAD": "head:W=116"}),
    "C1b": dict(desc="C1b · coupling Ø110, preload 1,6 kN", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                "compliance_d028.COUPLING_R": 55.0, "SPINDLE_BASE": "sp:receiver_w=126", "HEAD": "head:W=126"}),
    "C1p": dict(desc="C1p · coupling Ø80, preload 2,4 kN", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                "compliance_d028.HERTZ_PRELOAD": 2400.0}),
    "C2": dict(desc="C2 · C1b + receiver 8 mm", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
               "compliance_d028.COUPLING_R": 55.0, "SPINDLE_BASE": "sp:receiver_w=126,receiver_t=8", "HEAD": "head:W=126,L=213"}),
    "C3a": dict(desc="C3a · C2 + connettore a uscita laterale (braccio ~196 mm)", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                "compliance_d028.COUPLING_R": 55.0, "SPINDLE_BASE": "sp:receiver_w=126,receiver_t=8", "HEAD": "head:W=126,L=196",
                "CONNECTOR_ENVELOPES": "env:SIDE_EXIT", "CONNECTOR_MODE": "SIDE_EXIT"}),
    "C3c": dict(desc="C3c · C1b + connettore a uscita laterale, receiver 15 (braccio ~203 mm)", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                "compliance_d028.COUPLING_R": 55.0, "SPINDLE_BASE": "sp:receiver_w=126", "HEAD": "head:W=126,L=203",
                "CONNECTOR_ENVELOPES": "env:SIDE_EXIT", "CONNECTOR_MODE": "SIDE_EXIT"}),
    "A2": dict(desc="A2 · A1s + carrello a cassone (zaino 4 mm)", over={"MONOCOQUE": dict(h=60.0, wall=6.0), "SADDLE": None,
                                                                         "CARRIAGE_BOX": dict(z0=392.0, y1=200.0, wall=4.0)}),
}


def sp(**kw):
    """SPINDLE_BASE della baseline con alcune quote cambiate."""
    return {**_BASE["SPINDLE_BASE"], **kw}


def env(**extra):
    """CONNECTOR_ENVELOPES della baseline con varianti aggiunte."""
    return {**_BASE["CONNECTOR_ENVELOPES"], **extra}


def head(**kw):
    return {**_BASE["HEAD"], **kw}


_MOD_BASE = {}
SIDE_EXIT = dict(gap=8.0, side=40.0, plug=8.0, bend_r=0.0,
                 note="connettore a uscita laterale dal retro dello spindle (candidato D032 C3): 8 mm tra receiver e retro")


def _resolve(v):
    """Scorciatoie: 'sp:k=v,...' (SPINDLE_BASE), 'head:k=v,...' (HEAD), 'env:SIDE_EXIT' (CONNECTOR_ENVELOPES)."""
    if isinstance(v, str) and ":" in v:
        kind, rest = v.split(":", 1)
        if kind == "env":
            return env(**{rest: SIDE_EXIT})
        kw = {a.split("=")[0]: float(a.split("=")[1]) for a in rest.split(",")}
        return sp(**kw) if kind == "sp" else head(**kw)
    return copy.deepcopy(v)


def apply(name):
    """Ripristina la baseline e applica gli override del concept; riallinea le quote derivate nei moduli caricati."""
    if name not in CONCEPTS:
        raise SystemExit(f"concept sconosciuto {name}: {', '.join(CONCEPTS)}")
    for k, v in _BASE.items():
        setattr(P, k, copy.deepcopy(v))
    for k in [k for k in vars(P) if k.isupper() and k not in _BASE]:
        delattr(P, k)
    import importlib
    for key, v in _MOD_BASE.items():          # ripristina gli attributi di altri moduli (es. compliance_d028.COUPLING_R)
        mod, attr = key.split(".")
        setattr(importlib.import_module(mod), attr, v)
    for k, v in CONCEPTS[name]["over"].items():
        if "." in k:                           # override di un modulo di calcolo: "modulo.ATTRIBUTO"
            mod, attr = k.split(".")
            m_ = importlib.import_module(mod)
            _MOD_BASE.setdefault(k, getattr(m_, attr))
            setattr(m_, attr, copy.deepcopy(v))
        else:
            setattr(P, k, _resolve(v))
    P.SPINDLE = P.spindle()                    # la testa segue SPINDLE_BASE e il service envelope del connettore
    d = P.derived()
    for mod in ("standard_assembly", "d031", "compliance_d028", "d031_gantry"):
        m = sys.modules.get(mod)
        if m is not None and hasattr(m, "D"):
            m.D = d
        if m is not None and hasattr(m, "S"):
            m.S = P.SPINDLE
    return CONCEPTS[name]


def overrides(name):
    return CONCEPTS[name]["over"]
