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
- Versione della documentazione: unica, oggi V0.5 (`VERSION` in `nav.js`, README, dashboard).
- I valori non misurati sono **TARGET**, non specifiche commerciali.
- Le decisioni architetturali si registrano in `docs/decisions.html` (D001…) e vanno riflesse in tutte le pagine e nella BOM che toccano.
- Basi (D007): Light / Standard / Pro; la Standard è in sviluppo. `bom/base.html` = BOM Standard, `bom/base-pro.html` = riferimento Pro.
- BOM (`bom/base.html`): i KPI (numero righe, totale) devono coincidere con la tabella; ricalcolali quando cambi righe o prezzi.
