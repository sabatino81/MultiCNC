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

# STEP MultiCNC (cad/step/, generati da tools/cad/build_step.py): id -> file
OWN = {
    "MC-LIN-151": "hgr15_rail_600_2xHGH15CA", "MC-LIN-152": "hgr15_rail_600_2xHGH15CA",
    "MC-LIN-153": "hgr15_rail_300_2xHGH15CA", "MC-LIN-154": "hgr15_rail_300_2xHGH15CA",
    "MC-LIN-155": "mgn15_rail_600_2xMGN15H", "MC-LIN-156": "mgn15_rail_600_2xMGN15H",
    "MC-BS-1605X": "sfu1605_600", "MC-BS-1605Y": "sfu1605_550", "MC-BS-1204Z": "sfu1204_300",
    "MC-MOT-001": "nema23_closed_loop_2nm",
    "ML-LIN-151": "mgn12_rail_600_2xMGN12H", "ML-LIN-152": "mgn12_rail_600_2xMGN12H",
    "ML-LIN-153": "mgn12_rail_250_2xMGN12H", "ML-LIN-154": "mgn12_rail_250_2xMGN12H",
    "ML-BS-1204X": "sfu1204_600", "ML-BS-1204Y": "sfu1204_550", "ML-BS-1204Z": "sfu1204_300",
    "ML-MOT-001": "nema17_closed_loop",
    "MP-LIN-201": "hgr20_rail_600_2xHGH20CA", "MP-LIN-202": "hgr20_rail_600_2xHGH20CA",
    "MP-LIN-151": "hgr15_rail_300_2xHGH15CA", "MP-LIN-152": "hgr15_rail_300_2xHGH15CA",
    "MP-GL-LIN1": "hgr15_rail_350_2xHGH15CA", "MP-GL-LIN2": "hgr15_rail_350_2xHGH15CA",
    "MP-BS-1605X": "sfu1605_600", "MP-BS-1605Y": "sfu1605_550", "MP-BS-1204Z": "sfu1204_300",
    "MP-GL-BS": "sfu1605_350", "MP-MOT-001": "nema23_closed_loop_3nm", "MP-GL-MOT": "nema23_closed_loop_2nm",
}

# parti progettate da noi: lo STEP uscirà dal CAD parametrico MultiCNC
CUSTOM = re.compile(r"-(BAS|GAN|Z|RS)-|-TBL-001$|-TD-00[1236]$|-SP-003$|-GL-LOCK$")


def cell(part_id):
    mine = ""
    if part_id in OWN:
        mine = (f'<a class="cad-own" href="../cad/step/{OWN[part_id]}.step" download>STEP MultiCNC ↓</a>'
                f'<small>modello a quote reali</small>')
    if part_id in BY_ID:
        url, vendor, note = VENDOR[BY_ID[part_id]]
        return mine + (f'<a class="cad-link" href="{url}" target="_blank" rel="noopener">{vendor} ↗</a>'
                       f'<small>{note}</small>')
    if CUSTOM.search(part_id):
        return '<span class="cad-custom">MultiCNC CAD</span><small>in arrivo</small>'
    if mine:
        return mine
    return '<span class="cad-generic">Generico</span><small>STEP dal fornitore scelto</small>'
