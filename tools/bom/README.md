# BOM generator

Le tabelle delle tre BOM sono generate da dati Python, non scritte a mano.

| Base | Dati | Pagina |
|---|---|---|
| Light | `data_light.py` | `bom/base-light.html` |
| Standard | `data_standard.py` | `bom/base.html` |
| Pro | `data_pro.py` | `bom/base-pro.html` |

## Uso

Dalla radice del repository:

```sh
python3 tools/bom/build.py          # riscrive righe, KPI e totali nelle tre pagine
python3 tools/bom/build.py --check  # verifica soltanto; exit 1 se una pagina non è allineata
```

Lo script stampa per ogni base righe, costo prototipo, massa sulla macchina, massa esterna e massa per gruppo.

## Formato di una riga

```python
("MC-TD-001", "ToolDock", "Master kinematic plate", "1", 1,
 "Custom 3-point kinematic interface", "Montata sul carrello Z",
 150, 0.6, "M", "critical", "CRITICAL DESIGN")
```

id · gruppo · componente · quantità (etichetta) · quantità (numero) · candidate · specifica · €/cad · kg/cad · dove · classe stato · stato

- **dove**: `M` sulla macchina, `C` nel quadro o in unità esterne, `A` accessorio (elencato ma escluso dai totali).
- **classe stato**: `design`, `source`, `validate`, `critical`, `ok` (colore della pillola).
- **Codici**: `MC-` parti comuni alle tre basi, `ML-` solo Light, `MP-` solo Pro; le parti della sola Standard usano ancora `MC-`.

## Colonna CAD / STEP

`cad_sources.py` decide cosa mostrare per ogni id:

- `BY_ID` → link alla pagina ufficiale del produttore (`VENDOR`), verificato a mano;
- id di parti custom (`CUSTOM`) → "MultiCNC CAD · in arrivo";
- tutto il resto → "Generico · STEP dal fornitore scelto".

I file dei produttori non vanno copiati nel repository: le loro condizioni d'uso di solito ne vietano la ripubblicazione.

## Cosa non fa

Aggiorna solo tabella, i 4 KPI e la riga "Stima BOM prototipo attuale". Testi, callout, target e pannelli restano nell'HTML: se un cambio di dati li rende falsi (per esempio una massa citata nel callout), vanno corretti a mano insieme alle altre pagine che citano quei numeri.
