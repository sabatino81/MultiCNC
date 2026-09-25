# MultiCNC — note per Claude

## Git e deploy
- **Pusha sempre su `main`** dopo ogni modifica completata, senza chiedere conferma: il sito è in produzione su Vercel (https://multi-cnc.vercel.app, progetto `multi-cnc`, team SoccerQ) e si ridistribuisce da solo a ogni push su `main`.
- Prima del push: `git fetch origin main`. Se `main` è avanzato, fai merge (mai rebase, amend o force-push su `main`).
- Se la sessione ha un branch di lavoro assegnato, pusha anche lì, così resta allineato a `main`.
- Dopo il push, controlla che il deploy di produzione Vercel per quel commit sia `READY`.

## Progetto
- Sito statico HTML/CSS/JS in italiano, senza build. Lo stile sta in `assets/styles.css`; menu, pager, ricerca e footer sono iniettati da `assets/nav.js`.
- L'albero di navigazione (`TREE` in `assets/nav.js`) è l'elenco ufficiale dei capitoli: una pagina nuova va aggiunta lì, togliendo il badge `NEXT`/`PLANNED`.
- I link devono restare relativi (niente `href="/..."`): il sito deve funzionare da `file://`, dalla radice del dominio e da un sottopercorso.
- Versione della documentazione: unica, oggi V0.6 (`VERSION` in `nav.js`, README, dashboard).
- I valori non misurati sono **TARGET**, non specifiche commerciali.
- Le decisioni architetturali si registrano in `docs/decisions.html` (D001…) e vanno riflesse in tutte le pagine e nella BOM che toccano.
- Basi (D007): Light / Standard / Pro; la Standard è in sviluppo. `bom/base.html` = BOM Standard, `bom/base-light.html` = BOM Light Core (D024, prezzi TARGET a lotto da 50, tetto €1.050), `bom/base-pro.html` = BOM Pro (non in sviluppo attivo), `bom/platform-pack.html` = BOM Platform Pack (D026, upgrade della Light Core). Cabina opzionale (D025) come accessorio nelle BOM.
- BOM: le tabelle delle tre BOM si generano da `tools/bom/data_*.py` con `python3 tools/bom/build.py` (vedi `tools/bom/README.md`). Non modificare a mano righe, KPI o totali nell'HTML. Prima del push esegui `python3 tools/bom/build.py --check`; se cambiano costi o masse, aggiorna anche i testi e le altre pagine che li citano.
- STEP MultiCNC: si generano da `tools/cad/parts.py` con `tools/cad/build_step.py` (CadQuery, vedi `tools/cad/README.md`) in `cad/step/`; non modificare a mano.
- CAD Standard (digital mule): quote solo in `tools/cad/standard_params.py`; `tools/cad/standard_assembly.py` rigenera `cad/standard/` (STEP, report) e `base/cad-standard.html`, `tools/cad/render_views.py` le viste. Non modificare a mano la pagina né gli STEP. I file STEP dei produttori si linkano, non si ripubblicano.
- Calcoli di progetto in `tools/calc/` (D015 guide, D016 ToolDock, D017 potenza, D028 cedevolezza della Standard: `compliance_d028.py`, rigenera `base/compliance-d028.html`; D029 ToolDock e testa: `tooldock_d029.py`, rigenera `base/tooldock-d029.html`): se cambiano gli input, rilancia lo script e aggiorna la pagina che ne riporta i risultati. Le pagine D028 e D029 sono fotografie del mule v1.1: `compliance_d028.py` ora legge i default del mule v2 (D030), quindi non rigenerarle senza decidere se aggiornarne il testo.
- FEA a solidi (D031): `tools/fea/` (Gmsh + CalculiX, vedi `tools/fea/README.md`); `python tools/fea/d031.py` rigenera `fea/d031/pilot.json` e `base/fea-d031.html` (non modificare a mano). Guide, viti e ToolDock restano molle calibrate D028 finché non ci sono misure al banco. Fase 2a: `python tools/fea/d031_z.py` → `fea/d031/zslide.json`, `base/fea-d031-z.html`. Fase 3: `python tools/fea/d031_gantry.py` → `fea/d031/gantry.json`, `base/fea-d031-gantry.html`.
- Vista 3D (`base/viewer-3d.html`, three.js r160 in `assets/vendor/three/`): `tools/cad/export_glb.py` rigenera `cad/standard/glb/`, `tools/fea/export_results.py` rigenera `fea/d031/glb/` (dai .frd in `build/fea/`). Rilanciali quando cambiano mule o FEA.
- D032 (aperta): Standard stiffness architecture v4. D014 si separa in carico di servizio (XY e Z), carico strutturale (150 / 200 N) e rigidezza derivata dal budget di deformazione; ogni concept si valuta con la FEA D031 e contro 42 kg; ICD v4 invariata finché 2–3 concept non sono confrontati.
- Testa Standard (D030): spindle corto appeso, riferimento SycoTec 5045 AC-ER11 come golden reference, non fornitore di produzione (prezzi BOM = TARGET OEM). D031: asse a 53 mm, presentazione del magazine lungo +Y con accoppiamento in Z, 42 kg hard target (v2 sovrappeso accettato fino alla FEA), deroga baricentro ≤ 100 mm, ICD v4 invariata; il connettore è un service envelope (`CONNECTOR_ENVELOPES`, `CONNECTOR_MODE` in `standard_params.py`), non una quota. Mule v3 (D031): sella a U master ↔ ali della slitta (`SADDLE`) e piastrina chiocciola Z 16 mm (`TAB_T`); le FEA pilota e fase 2a costruiscono le loro varianti dal mule v2 (`saddle=False`).
