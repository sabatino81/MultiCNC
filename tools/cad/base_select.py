"""Scelta della base per gli script CAD: `--base light|standard|pro` sulla riga di comando o MULTICNC_BASE.

Va importato prima di standard_params: registra <base>_params come "standard_params", così assieme, dettaglio,
pezzi, accessori, GLB e viste lavorano sulla base scelta senza cambiare codice. La Standard resta il default.
"""
import importlib
import os
import sys

if "--base" in sys.argv:
    os.environ["MULTICNC_BASE"] = sys.argv[sys.argv.index("--base") + 1]
BASE = os.environ.get("MULTICNC_BASE", "standard")
if BASE not in ("light", "standard", "pro"):
    raise SystemExit(f"base sconosciuta {BASE}: light, standard, pro")
if BASE != "standard" and getattr(sys.modules.get("standard_params"), "BASE", "standard") != BASE:
    sys.modules["standard_params"] = importlib.import_module(f"{BASE}_params")
