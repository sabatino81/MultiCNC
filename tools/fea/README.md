# FEA a solidi · D031

Pipeline lineare statica per i pezzi del mule Standard: solidi CadQuery dal CAD del mule → mesh Gmsh (tetra
quadratici C3D10, ottimizzati high-order) → `.inp` CalculiX → spostamenti dei punti di riferimento e tensioni nodali.

- `ccx.py`: modulo generico (corpi incollati, corpi rigidi, molle SPRING2 anche rotazionali, molle in direzione
  qualsiasi con equazioni, casi di carico, lettura `.dat` / `.frd`, qualità della mesh).
- `d031.py`: fase 1, modello pilota master ToolDock + testa 5045-style; autotest delle molle, mesh nominale e fine,
  varianti; scrive `fea/d031/pilot.json` e rigenera `base/fea-d031.html` (via `d031_page.py`).

## Requisiti

- Python con CadQuery, numpy, scipy e `gmsh` (`pip install gmsh`; su Linux servono anche `libglu1-mesa`,
  `libxcursor1`, `libxinerama1`, `libxft2`).
- CalculiX `ccx` nel PATH (Ubuntu: `apt install calculix-ccx`, solutore SPOOLES). Un `ccx` compilato con PARDISO
  (per esempio quello di PrePoMax su Windows) è molto più veloce sui modelli grandi.

## Uso

```
python tools/fea/d031.py            # completo: ~40 min con 4 core e SPOOLES
python tools/fea/d031.py --quick    # solo autotest, nominale e mesh fine
python tools/fea/d031.py --resume   # riusa nominale e fine da pilot.json, ricalcola autotest e varianti
python tools/fea/d031_page.py       # solo la pagina dal JSON
```

Fase 2a: `python tools/fea/d031_z.py` (testa + master + slitta Z, quattro topologie master ↔ slitta).
Vista 3D: `python tools/fea/export_results.py` (richiede `trimesh`) scrive le deformate colorate in `fea/d031/glb/` per `base/viewer-3d.html`.

File di lavoro in `build/fea/` (non versionati). Regole D031: carichi su punti di riferimento (mai su un nodo),
spostamento relativo naso ER11 ↔ riferimento, convergenza con dimensioni −30% entro il 5% alla punta, tensione
"hotspot" lontano da vincoli, patch rigide ed elementi scadenti; guide, viti e ToolDock come molle calibrate D028.
