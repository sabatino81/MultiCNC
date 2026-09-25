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
- Calcoli di progetto in `tools/calc/` (D015 guide, D016 ToolDock, D017 potenza): se cambiano gli input, rilancia lo script e aggiorna la pagina che ne riporta i risultati.
