# CAD parametrico MultiCNC

`parts.py` definisce in CadQuery i componenti commerciali ricorrenti (rotaie e pattini HIWIN, viti SFU con chiocciola, motori NEMA17/23 closed-loop). `build_step.py` li esporta in `cad/step/` insieme a `manifest.json`.

## Digital mule della Standard

- `standard_params.py`: unica fonte di verità geometrica della Standard (corse, componenti, catena di quote, parametri MULE).
- `standard_assembly.py`: costruisce l'assieme in HOME, CENTER e MAX, controlla collisioni, giochi e margini di fine corsa, calcola ingombri e masse, verifica D015 con i bracci reali; scrive `cad/standard/standard_mule_<config>.step`, `cad/standard/report.json` e la pagina `base/cad-standard.html` (generata: non modificarla a mano).
- `render_views.py`: viste ortografiche di controllo in `cad/standard/views/` (richiede Pillow).

```sh
python3 -m venv .venv && .venv/bin/pip install cadquery pillow   # una volta
.venv/bin/python tools/cad/build_step.py                  # rigenera gli STEP dei componenti
.venv/bin/python tools/cad/standard_assembly.py           # assieme, report e pagina
.venv/bin/python tools/cad/render_views.py                # viste
python3 tools/bom/build.py                                 # aggiorna i link nelle BOM
```

La mappa riga BOM → file STEP è `OWN` in `tools/bom/cad_sources.py`.
