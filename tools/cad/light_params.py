"""Base Light Core (D023, D024) · parametri del mule: stesse chiavi di standard_params.py, sovrascritte dove la Light
è diversa. Si usa con `--base light` (tools/cad/base_select.py). Valori MULE / TARGET.

- MGN12 / MGN12H su X, Y, Z (D019), SFU1204 su tutti gli assi con BK10/BF10, NEMA17 (D026: encoder a innesto nel
  Platform Pack), spindle BLDC 300–500 W ad aria ER11, ToolDock manuale (clamp a camma ≥ 0,5 kN, stesse sedi del
  clamp automatico), tavola 9 mm con pelle 4 (D018), rialzi +50 mm.
- Light a piastre (D036), sotto i 18 kg: vite X sopra la trave (BK10/BF10 sul cielo di un tubo 40 × 80 senza canale,
  guide X a 52 mm), telaio a scala in tubi 40 × 40 × 1,5 con sbalzi sotto le spalle, vite Z fissa-libera (solo BK10),
  piastre sottili (spalle 4 mm, carrello e slitta 6 mm). Pattern ICD §5 e tavola D018 invariati.
"""
import copy

import standard_params as _S

globals().update({k: copy.deepcopy(v) for k, v in vars(_S).items() if k.isupper()})

BASE, BASE_LABEL, BOM_DATA, FILE_PREFIX = "light", "Light Core", "data_light", "light"
UPRIGHT_MODE = "plate"
TD_CLAMP = "manual"
RISER_H = 50.0

X_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=620.0, block_pitch=80.0, rail_spacing=52.0, screw="SFU1204",
              screw_len=570.0, motor="NEMA17_CL", bk="BK10", bf="BF10")
Y_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=580.0, block_pitch=160.0, rail_spacing=300.0, screw="SFU1204",
              screw_len=480.0, motor="NEMA17_CL", bk="BK10", bf="BF10")   # 480, non 470 (D019): 8 mm fra staffa chiocciola e BK a fine corsa
Z_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=280.0, block_pitch=70.0, rail_spacing=90.0, screw="SFU1204",
              screw_len=260.0, motor="NEMA17_CL", bk="BK10", bf=None)   # vite Z fissa-libera: solo BK10 in alto (corsa 140, NEMA17)

TABLE = dict(W=450.0, D=350.0, T=9.0, skin=4.0, boss_d=16.0, rim=12.0, pad_w=32.0, pad_l=52.0)
MASTER = dict(W=120.0, T=30.0, wall=3.0)
SPINDLE_BASE = dict(ref="BLDC 400 W ER11 Ø52 (classe, fornitore da qualificare)", d=52.0, nut_d=22.0, nose=22.0, neck=10.0,
                    housing=125.0, rear=25.0, total=182.0, mass=1.0, p_s1=400.0, p_max=500.0, rpm=(3000, 12000), voltage=48.0,
                    current_s1=9.0, current_max=11.0, sealing_air_lpm=0.0, collet_max=7.0, receiver_t=12.0,
                    clamp_len=45.0, clamp_block=62.0, receiver_w=96.0, k_bearing=20e3, jacket=False)
CONNECTOR_ENVELOPES = {"RIGHT_ANGLE_ASSUMED": dict(gap=12.0, side=30.0, plug=12.0, bend_r=0.0,
                                                   note="cavo del BLDC in uscita laterale (MULE)")}
CONNECTOR_MODE = "RIGHT_ANGLE_ASSUMED"

CARRIAGE_FLANGE = None                        # piastra piana 6 mm, senza ali
SLIDE_FLANGE = dict(t=5.0, depth=25.0)
SADDLE = dict(t=5.0, h=30.0)
PLATE = dict(carriage_t=6.0, slide_t=6.0, carriage_w=124.0, below_x_blocks=6.0, slot_w=68.0, tower_w=84.0, upper_w=110.0, z_motor_w=70.0,
             slide_w=120.0, slide_len=130.0, block_offset=5.0)
LADDER = dict(H=40.0, wall=1.5, long_w=40.0, long_y=(-295.0, 290.0), front_y=None, bf_y=(-250.0, -210.0),
              end_y=(250.0, 290.0), pocket_w=80.0, pad_t=1.5, cross_drop=5.0, rear="outrigger", rail_pad=3.0,
              flange_window=(40.0, 76.0), boss_d=14.0, foot=(40.0, 40.0, 6.0), flange_pocket=5.0)   # tubi 40 × 40 × 1,5: niente traversa anteriore, sbalzi sotto le spalle
UPRIGHT = dict(t=4.0, depth=80.0, wall=None)
ICD_FLANGE_T = 10.0                            # flangia ICD §5 della spalla: M8 filettati su 8 mm + elicoidale (Light)
BEAM = dict(depth=40.0, height=80.0, wall=2.0, wall_face=4.0, recess_h=0.0, recess_d=0.0, end=2.0, cap=12.0, cap_bosses=True)   # profilo 40 × 80 senza canale
BEAM_X = (-110.0, 550.0)
X_DRIVE = "top"                                # vite X sopra la trave, BK/BF sul cielo
X_TOP = dict(dy=38.0)                          # asse vite X a 38 mm dalla faccia guide: spessori a 8 mm dai pattini X
X_SCREW_PAD = 8.0
NUT_BRACKET_T = 8.0
TAB_T = 10.0
CHAIN_X = dict(w=50.0, h=45.0, inset=8.0)
CHAIN_Y = dict(x0=513.0, x1=542.0, h=45.0, z0=12.0)   # catena Y bassa fra la testa a X max e la spalla destra
HEAD_AXIS_FROM_SLIDE = 67.0   # MGN12 (rotaia 8 mm) sul carrello: inviluppo testa ±70 a 8 mm dalle guide Z
PROCESS = {   # materiali e lavorazioni dei pezzi custom (pagina Pezzi Light Core) · MULE
    "frame_": ("EN AW-6060 T66, tubi 40 × 40 × 1,5 (coda 40 × 80 × 1,5)", "saldato TIG, distensionato, fresato su pad, sedi guide Y e appoggi flange spalle"),
    "upright_": ("EN AW-5083, piatto 4 + flangia 10 scaricata", "tagliato laser, saldato e fresato; fori spine Ø10 H7 alesati"),
    "beam": ("EN AW-6060 T66, tubo 40 × 80 (faccia 4, pareti 2) + blocchetti d'angolo", "saldato, fresato su faccia guide X e cielo (spessori BK/BF)"),
    "x_carriage": ("EN AW-6082 T651, piastra 6 + torre", "fresato"),
    "z_slide": ("EN AW-6082 T651, piastra 6 + ali 5", "fresato"),
    "table": ("EN AW-5083 piastra rettificata 9", "fresata: pelle 4, tasche fra i boss, sedi inserti M6, boccole R1/R2"),
}
MASS_GATE_KG = 18.0        # D010 / D024: Light Core ~18 kg
MASS_TARGET_KG = 17.6

BOM_MAP = {
    "MC-BAS-001": "ML-BAS-001", "MC-GAN-001": "ML-GAN-001", "MC-GAN-002": "ML-GAN-002", "MC-Z-001": "ML-Z-001",
    "MC-TBL-001": "ML-TBL-001", "MC-XC-001": "ML-XC-001", "MC-BRK-001": "ML-BRK-001", "MC-TD-001": "ML-TD-001",
    "MC-TD-002": "ML-TD-002", "MC-TD-003": "ML-TD-003", "MC-SP-003": "ML-SP-003", "MC-SP-001": "ML-SP-001",
    "MC-LIN-151": "ML-LIN-151", "MC-LIN-152": "ML-LIN-152", "MC-LIN-155": "ML-LIN-151", "MC-LIN-156": "ML-LIN-152",
    "MC-LIN-153": "ML-LIN-153", "MC-LIN-154": "ML-LIN-154", "MC-BS-1605X": "ML-BS-1204X", "MC-BS-1605Y": "ML-BS-1204Y",
    "MC-BS-1204Z": "ML-BS-1204Z", "MC-BKBF-001": "ML-BKBF-001", "MC-CPL-001": "ML-CPL-001", "MC-MOT-001": "ML-MOT-002",
    "MC-TD-004": "ML-TD-004", "MC-TD-007": "ML-UP-001",
}
ACCESSORIES = ("ML-RS-001", "MC-TD-006", "MC-ENC-001")
CAD_NOTES = (
    "Stessa cinematica e stessa ICD v4 della Standard (ponte fisso, tavola Y, ToolDock comune): cambiano componenti e sezioni.",
    "MGN12 / MGN12H su X, Y e Z, SFU1204 su tutti gli assi, NEMA17; spindle BLDC 400 W ER11 Ø52 (classe) nel mount comune.",
    "Light a piastre (D036): trave in tubo 40 × 80 senza canale, guide X a 52 mm sulla faccia, vite X e BK10/BF10 sul cielo della trave su spessori 8 mm; staffa della chiocciola X dal retro del carrello sopra la trave.",
    "Telaio a scala in tubi 40 × 40 × 1,5: longheroni, traversa BF, traversa di coda 40 × 80 con BK e motore Y, 4 sbalzi sotto le flange ICD §5 delle spalle; niente traversa anteriore.",
    "Spalle a piastra 4 mm ai lati della trave, flangia ICD §5 10 mm scaricata attorno a M8 e spine (rialzi +50 mm); motore X sulla spalla destra all'altezza della vite.",
    "Vite Z fissa-libera (solo BK10 in alto, corsa 140), guide Z a 90 mm, carrello e slitta 6 mm senza ali; asse spindle a 67 mm dalla slitta (inviluppo testa ±70 a 8 mm dalle guide Z).",
    "ToolDock manuale: albero a camma nella master sul pull-stud comune (≥ 0,5 kN); sedi del clamp automatico e dei connettori del Platform Pack già lavorate.",
    "Massa dal CAD sotto la soglia di 18 kg (D010): tavola D018 invariata; le masse dei commerciali restano quelle della BOM.",
)


def derived():
    return _S.derived(globals())


def spindle(mode=None):
    return _S.spindle(mode, globals())


SPINDLE = spindle()
