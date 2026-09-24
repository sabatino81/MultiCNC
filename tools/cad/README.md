# CAD parametrico MultiCNC

`parts.py` definisce in CadQuery i componenti commerciali ricorrenti (rotaie e pattini HIWIN, viti SFU con chiocciola, motori NEMA17/23 closed-loop). `build_step.py` li esporta in `cad/step/` insieme a `manifest.json`.

```sh
python3 -m venv .venv && .venv/bin/pip install cadquery   # una volta
.venv/bin/python tools/cad/build_step.py                  # rigenera gli STEP
python3 tools/bom/build.py                                 # aggiorna i link nelle BOM
```

La mappa riga BOM → file STEP è `OWN` in `tools/bom/cad_sources.py`.
