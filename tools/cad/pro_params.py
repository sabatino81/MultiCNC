"""Base Pro (D011) · parametri del mule: stesse chiavi di standard_params.py, sovrascritte dove la Pro è diversa.
Si usa con `--base pro` (tools/cad/base_select.py). Pro non è in sviluppo attivo: CAD di riferimento, valori MULE / TARGET.

- HGR20 / HGH20CA su X e Y, HGR15 / HGH15CA su Z (D019), SFU1605 X/Y con BK12/BF12 e SFU1204 Z, NEMA23 3 Nm,
  spindle 1,5 kW Ø80 ER16 ad acqua (inviluppo classe P in revisione: L 280), tavola piena 12 mm (D018), master e
  receiver comuni (ICD v4), clamp classe P ≥ 3,8 kN.
- Sotto i 70 kg (D037): basamento a scala in tubi 80 × 60 × 4 senza fondo, con 4 sbalzi sotto i montanti del lift;
  trave scatolata 100 × 170 con pareti 4 e faccia guide 8; carrello e slitta 12 mm.
- Gantry Lift motorizzato 0–150 mm: montanti a piastra 12 mm finestrati dietro le estremità della trave, una guida HGR15 e una
  vite SFU1605 per montante, sincronizzate da una cinghia HTD con un motore G, bloccaggio a cunei. La trave scorre
  davanti ai montanti: motore X e catene restano liberi. Il magazine si sposta oltre il montante destro.
"""
import copy

import standard_params as _S

globals().update({k: copy.deepcopy(v) for k, v in vars(_S).items() if k.isupper()})

BASE, BASE_LABEL, BOM_DATA, FILE_PREFIX = "pro", "Pro", "data_pro", "pro"
UPRIGHT_MODE = "lift"
TD_CLAMP = "auto"
LIFT = dict(stroke=150.0, rail="HGR15", block="HGH15CA", rail_len=350.0, block_pitch=100.0, screw="SFU1605",
            screw_len=350.0, bk="BK12", bf="BF12", motor="NEMA23_CL_2NM", bracket_t=32.0, plate_w=120.0, spacer=0.0,
            bracket_pocket=(60.0, 12.0), tie_h=30.0)

X_AXIS = dict(rail="HGR20", block="HGH20CA", rail_len=650.0, block_pitch=110.0, rail_spacing=130.0, screw="SFU1605",
              screw_len=590.0, motor="NEMA23_CL_3NM", bk="BK12", bf="BF12")
Y_AXIS = dict(rail="HGR20", block="HGH20CA", rail_len=650.0, block_pitch=200.0, rail_spacing=300.0, screw="SFU1605",
              screw_len=490.0, motor="NEMA23_CL_3NM", bk="BK12", bf="BF12")
Z_AXIS = dict(rail="HGR15", block="HGH15CA", rail_len=320.0, block_pitch=90.0, rail_spacing=120.0, screw="SFU1204",
              screw_len=260.0, motor="NEMA23_CL_3NM", bk="BK10", bf="BF10")

TABLE = dict(W=450.0, D=350.0, T=12.0, skin=12.0, boss_d=16.0, rim=12.0, pad_w=48.0, pad_l=82.0)
HEAD = dict(W=110.0, D=140.0, L=280.0)        # classe P in revisione (ICD v4): lo spindle Ø80 non sta in L 220
SPINDLE_BASE = dict(ref="Spindle 1,5 kW Ø80 ER16 raffreddato ad acqua (classe, fornitore da qualificare)", d=80.0, nut_d=32.0,
                    nose=30.0, neck=10.0, housing=175.0, rear=20.0, total=235.0, mass=4.5, p_s1=1500.0, p_max=1500.0,
                    rpm=(6000, 24000), voltage=220.0, current_s1=7.0, current_max=8.0, sealing_air_lpm=0.0, collet_max=10.0,
                    receiver_t=15.0, clamp_len=80.0, clamp_block=100.0, receiver_w=110.0, k_bearing=60e3, jacket=False)
CONNECTOR_ENVELOPES = {"RIGHT_ANGLE_ASSUMED": dict(gap=25.0, side=45.0, plug=25.0, bend_r=0.0,
                                                   note="connettore a 90° dello spindle Ø80 (MULE)")}
CONNECTOR_MODE = "RIGHT_ANGLE_ASSUMED"
HEAD_COG_WAIVER = 140.0

CARRIAGE_FLANGE = dict(t=10.0, depth=35.0)
SLIDE_FLANGE = dict(t=10.0, depth=35.0)
SADDLE = dict(t=10.0, h=50.0)
PLATE = dict(carriage_t=12.0, slide_t=12.0, carriage_w=190.0, below_x_blocks=18.0, slot_w=70.0, tower_w=110.0,
             slide_w=160.0, slide_len=170.0, block_offset=5.0)
LADDER = dict(H=80.0, wall=4.0, long_w=60.0, long_y=(-330.0, 350.0), front_y=None, bf_y=(-250.0, -200.0),
              end_y=(300.0, 350.0), pocket_w=80.0, pad_t=14.0, cross_drop=5.0, rear="outrigger", bk_cross=True,
              flange_window=(40.0, 76.0), flange_pocket=6.0)   # D037: scala 80 × 60 × 4 senza fondo, sbalzi sotto i montanti del lift
UPRIGHT = dict(t=12.0, depth=120.0, wall=None, windows=((60.0, 280.0), (320.0, 540.0)), window_x=((18.0, 38.0),))
BEAM = dict(depth=100.0, height=170.0, wall=4.0, wall_face=8.0, recess_h=100.0, recess_d=38.0, end=5.0)
BEAM_X = (-155.0, 605.0)
CHAIN_X = dict(w=75.0, h=60.0, inset=5.0)
CHAIN_Y = dict(x0=513.0, x1=557.0, h=60.0, z0=12.0, y=(-350.0, 270.0))   # catena Y davanti al montante destro del lift
MAGAZINE = dict(x=(640.0, 820.0), y=(360.0, 540.0), z=(380.0, 720.0))
STORE_POSE = (730.0, 450.0)
TRANSFER_TOP = 700.0
TRANSFER_X = (680.0, 790.0)
MASS_GATE_KG = 72.0        # D011: ~70 kg accettati, sottogruppi spedibili
MASS_TARGET_KG = 70.0

BOM_MAP = {
    "MC-BAS-001": "MP-BAS-001", "MC-GAN-001": "MP-GAN-001", "MC-GAN-002": "MP-GAN-002", "MC-Z-001": "MP-Z-001",
    "MC-TBL-001": "MP-TBL-001", "MC-XC-001": "MP-XC-001", "MC-BRK-001": "MP-BRK-001", "MC-SP-003": "MP-SP-003",
    "MC-SP-001": "MP-SP-001", "MC-LIN-151": "MP-LIN-201", "MC-LIN-152": "MP-LIN-202", "MC-LIN-155": "MP-LIN-201",
    "MC-LIN-156": "MP-LIN-202", "MC-LIN-153": "MP-LIN-151", "MC-LIN-154": "MP-LIN-152", "MC-BS-1605X": "MP-BS-1605X",
    "MC-BS-1605Y": "MP-BS-1605Y", "MC-BS-1204Z": "MP-BS-1204Z", "MC-BKBF-001": "MP-BKBF-001", "MC-CPL-001": "MP-CPL-001",
    "MC-MOT-001": "MP-MOT-001",
}
ACCESSORIES = ("MC-TD-006", "MP-ENC-001")
PROCESS = {   # materiali e lavorazioni dei pezzi custom (pagina Pezzi Pro) · MULE
    "frame_": ("EN AW-6082 T6, tubi 80 × 60 × 4", "saldato TIG, distensionato, fresato su pad, sedi guide Y e appoggi flange dei montanti"),
    "upright_": ("EN AW-6082 T651, piastra 12 finestrata + flangia 12 scaricata", "fresato; sede guida HGR15 rettificata, fori spine Ø10 H7 alesati"),
    "beam": ("EN AW-6082 T6, scatolato 100 × 170 (faccia 8, pareti 4)", "saldato, distensionato, fresato su faccia guide X, canale vite e appoggi staffe lift"),
    "x_carriage": ("EN AW-6082 T651, piastra 12 + ali 10 + torre", "fresato"),
    "z_slide": ("EN AW-6082 T651, piastra 12 + ali 10", "fresato"),
    "lift_": ("EN AW-6082 T651", "fresato; staffe trave a C con faccia pattini 12 mm"),
    "table": ("EN AW-5083 piastra rettificata 12", "fresata piena: sedi inserti M6, boccole R1/R2"),
}
CAD_NOTES = (
    "Stessa cinematica e stessa ICD v4 (ponte fisso, tavola Y, ToolDock comune); master e clamp come la Standard, pacco molle classe P ≥ 3,8 kN (TARGET).",
    "HGR20 / HGH20CA su X e Y, HGR15 / HGH15CA su Z, SFU1605 X/Y con BK12/BF12, SFU1204 Z, NEMA23 3 Nm; tavola piena 12 mm (D018).",
    "Spindle 1,5 kW Ø80 ER16 ad acqua (classe): inviluppo testa L 280 (classe P in revisione nella ICD), receiver 110 × 110 per il mount Ø80.",
    "Basamento a scala in tubi 80 × 60 × 4 senza fondo (D037): longheroni, traversa BF, traversa BK Y, traversa di coda con il motore Y e 4 sbalzi sotto le flange ICD §5 dei montanti del lift; niente traversa anteriore.",
    "Gantry Lift: montanti a piastra 12 mm con 4 finestre ai lati della guida, una guida HGR15 con 2 pattini e una vite SFU1605 per lato, staffe della trave a C (32 mm, faccia pattini 12), cinghia HTD di sincronismo, motore G diretto sulla vite sinistra, bloccaggi a cuneo, traversa superiore 12 × 30.",
    "La trave (scatolato 100 × 170, pareti 4, faccia guide 8) scorre davanti ai montanti: motore X, catene e ToolDock restano liberi a ogni quota del lift; il magazine si sposta oltre il montante destro (x 730).",
    "Massa dal CAD sotto i ~70 kg di D011 (D037); le masse delle viti a sfere sono quelle del CAD (vite piena + chiocciola, limite superiore).",
)


def derived():
    return _S.derived(globals())


def spindle(mode=None):
    return _S.spindle(mode, globals())


SPINDLE = spindle()
