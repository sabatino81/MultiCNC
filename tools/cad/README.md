# CAD parametrico MultiCNC

`parts.py` definisce in CadQuery i componenti commerciali ricorrenti (rotaie e pattini HIWIN, viti SFU con chiocciola, motori NEMA17/23 closed-loop). `build_step.py` li esporta in `cad/step/` insieme a `manifest.json`.

## Digital mule della Standard

- `standard_params.py`: unica fonte di verità geometrica della Standard (corse, componenti, catena di quote, parametri MULE).
- `standard_assembly.py`: costruisce l'assieme in HOME, CENTER, MAX e DOCK (D027), controlla collisioni, giochi e margini di fine corsa, calcola ingombri e masse, verifica D015 con i bracci reali; scrive `cad/standard/standard_mule_<config>.step`, `cad/standard/report.json` e la pagina `base/cad-standard.html` (generata: non modificarla a mano).
- `render_views.py`: viste ortografiche di controllo in `cad/standard/views/` (richiede Pillow).
- `standard_detail.py`: lavorazioni di dettaglio dei pezzi custom (fori di guide, pattini, supporti, chiocciole, motori, interfaccia spalla ICD v4 §5, ToolDock con clamp, porte e connettori) ricavate dalle posizioni reali dei componenti; aggiunge le piastre ponte dei BK/BF Z e compila la viteria. Lo applica `standard_assembly.build()` (`DETAIL = True`); le FEA lo spengono.
- `standard_parts.py`: uno STEP per pezzo custom (coordinate locali) e uno per riga BOM (coordinate HOME) in `cad/standard/parts/`, viste, `manifest.json` (letto dalle BOM) e la pagina `base/cad-parts.html` (generata).
- `standard_accessories.py`: rialzi spalle MC-RS-001 (dettaglio), magazine + trasferitore MC-TD-006 (layout), cabina MC-ENC-001.

```sh
python3 -m venv .venv && .venv/bin/pip install cadquery pillow   # una volta
.venv/bin/python tools/cad/build_step.py                  # rigenera gli STEP dei componenti
.venv/bin/python tools/cad/standard_assembly.py           # assieme, report e pagina
.venv/bin/python tools/cad/render_views.py                # viste
.venv/bin/python tools/cad/standard_parts.py              # STEP e viste dei pezzi di dettaglio, pagina pezzi
python3 tools/bom/build.py                                 # aggiorna i link nelle BOM
```

La mappa riga BOM → file STEP è `OWN` in `tools/bom/cad_sources.py`.
