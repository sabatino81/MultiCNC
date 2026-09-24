"""Fonti CAD/STEP per la colonna "CAD / STEP" delle BOM.

I modelli dei produttori NON vengono ripubblicati nel sito: le condizioni d'uso
(es. HIWIN) ne vietano la ridistribuzione. Si linka la pagina ufficiale da cui
scaricarli. Link verificati il 2026-09-24.
"""
import re

VENDOR = {
    "hiwin_lg": ("https://www.hiwinsupport.com/cad_download/linear_guideway.aspx", "HIWIN CAD", "account gratuito"),
    "so_23_3nm": ("https://www.omc-stepperonline.com/nema-23-closed-loop-stepper-motor-3-0nm-424oz-in-encoder-1000ppr-4000cpr-23hs45-4204d-e1000", "StepperOnline", "23HS45-4204D-E1000"),
    "so_23_cl": ("https://www.omc-stepperonline.com/nema-23-closed-loop-stepper-motor", "StepperOnline", "NEMA23 closed-loop"),
    "so_kit": ("https://www.omc-stepperonline.com/closed-loop-stepper-kit", "StepperOnline", "kit closed-loop"),
    "mw_lrs200": ("https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-200", "Mean Well", "LRS-200"),
    "mw_lrs350": ("https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-350", "Mean Well", "LRS-350"),
    "mw_lrs600": ("https://www.meanwell.com/webapp/product/search.aspx?prod=LRS-600", "Mean Well", "LRS-600"),
    "mw_hdr60": ("https://www.meanwell.com/webapp/product/search.aspx?prod=HDR-60", "Mean Well", "HDR-60"),
    "mesa": ("http://www.mesanet.com/", "Mesa", "nessuno STEP ufficiale"),
}

# id della riga -> chiave VENDOR
BY_ID = {
    # guide e pattini (tutte le basi, incluso il Gantry Lift della Pro)
    **{i: "hiwin_lg" for i in [
        "MC-LIN-151", "MC-LIN-152", "MC-LIN-153", "MC-LIN-154", "MC-LIN-155", "MC-LIN-156",
        "ML-LIN-151", "ML-LIN-152", "ML-LIN-153", "ML-LIN-154",
        "MP-LIN-201", "MP-LIN-202", "MP-LIN-151", "MP-LIN-152",
        "MP-GL-LIN1", "MP-GL-LIN2"]},
    "MP-MOT-001": "so_23_3nm", "MP-GL-MOT": "so_23_cl", "MC-MOT-001": "so_23_cl",
    "ML-MOT-001": "so_kit", "MC-DRV-001": "so_kit", "ML-DRV-001": "so_kit",
    "MP-DRV-001": "so_kit", "MP-GL-DRV": "so_kit",
    "ML-PWR-001": "mw_lrs200", "MC-PWR-001": "mw_lrs350", "MP-PWR-001": "mw_lrs600",
    "MC-PWR-002": "mw_hdr60",
    "MC-CTRL-001": "mesa",
}

# parti progettate da noi: lo STEP uscirà dal CAD parametrico MultiCNC
CUSTOM = re.compile(r"-(BAS|GAN|Z|TBL|TD|RS)-|-SP-003$|-GL-LOCK$")


def cell(part_id):
    if part_id in BY_ID:
        url, vendor, note = VENDOR[BY_ID[part_id]]
        return (f'<a class="cad-link" href="{url}" target="_blank" rel="noopener">{vendor} ↗</a>'
                f'<small>{note}</small>')
    if CUSTOM.search(part_id):
        return '<span class="cad-custom">MultiCNC CAD</span><small>in arrivo</small>'
    return '<span class="cad-generic">Generico</span><small>STEP dal fornitore scelto</small>'
