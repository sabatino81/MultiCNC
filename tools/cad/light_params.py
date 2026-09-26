"""Base Light Core (D023, D024) · parametri del mule: stesse chiavi di standard_params.py, sovrascritte dove la Light
è diversa. Si usa con `--base light` (tools/cad/base_select.py). Valori MULE / TARGET.

- MGN12 / MGN12H su X, Y, Z (D019), SFU1204 su tutti gli assi con BK10/BF10, NEMA17 (D026: encoder a innesto nel
  Platform Pack), spindle BLDC 300–500 W ad aria ER11, ToolDock manuale (clamp a camma ≥ 0,5 kN, stesse sedi del
  clamp automatico), tavola 9 mm con pelle 4 (D018), rialzi +50 mm.
- Spalle: piastre Al 5083 6 mm ai lati della trave (non sotto), motore X sulla spalla destra.
- Telaio: profili 40 × 60 (non 40 × 40): l'asse Y e la staffa della chiocciola stanno dentro il telaio con 8 mm di gioco.
- Trave 50 × 120 con canale vite (non un profilo 40 × 80): il canale deve contenere BK10/BF10 (60 mm) fra le guide X a 104 mm
  con 8 mm dai pattini, e la chiocciola SFU1204 con 8 mm dal fondo del canale.
"""
import copy

import standard_params as _S

globals().update({k: copy.deepcopy(v) for k, v in vars(_S).items() if k.isupper()})

BASE, BASE_LABEL, BOM_DATA, FILE_PREFIX = "light", "Light Core", "data_light", "light"
UPRIGHT_MODE = "plate"
TD_CLAMP = "manual"
RISER_H = 50.0

X_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=620.0, block_pitch=80.0, rail_spacing=104.0, screw="SFU1204",
              screw_len=570.0, motor="NEMA17_CL", bk="BK10", bf="BF10")
Y_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=620.0, block_pitch=200.0, rail_spacing=300.0, screw="SFU1204",
              screw_len=480.0, motor="NEMA17_CL", bk="BK10", bf="BF10")   # 480, non 470 (D019): 8 mm fra staffa chiocciola e BK a fine corsa
Z_AXIS = dict(rail="MGN12", block="MGN12H", rail_len=280.0, block_pitch=70.0, rail_spacing=104.0, screw="SFU1204",
              screw_len=260.0, motor="NEMA17_CL", bk="BK10", bf="BF10")

TABLE = dict(W=450.0, D=350.0, T=9.0, skin=4.0, boss_d=16.0, rim=12.0, pad_w=32.0, pad_l=52.0)
MASTER = dict(W=120.0, T=30.0, wall=5.0)
SPINDLE_BASE = dict(ref="BLDC 400 W ER11 Ø52 (classe, fornitore da qualificare)", d=52.0, nut_d=22.0, nose=22.0, neck=10.0,
                    housing=125.0, rear=25.0, total=182.0, mass=1.0, p_s1=400.0, p_max=500.0, rpm=(3000, 12000), voltage=48.0,
                    current_s1=9.0, current_max=11.0, sealing_air_lpm=0.0, collet_max=7.0, receiver_t=12.0,
                    clamp_len=45.0, clamp_block=66.0, receiver_w=96.0, k_bearing=20e3, jacket=False)
CONNECTOR_ENVELOPES = {"RIGHT_ANGLE_ASSUMED": dict(gap=12.0, side=30.0, plug=12.0, bend_r=0.0,
                                                   note="cavo del BLDC in uscita laterale (MULE)")}
CONNECTOR_MODE = "RIGHT_ANGLE_ASSUMED"

CARRIAGE_FLANGE = dict(t=8.0, depth=28.0)
SLIDE_FLANGE = dict(t=8.0, depth=28.0)
SADDLE = dict(t=8.0, h=40.0)
PLATE = dict(carriage_t=8.0, slide_t=8.0, carriage_w=152.0, below_x_blocks=12.0, slot_w=72.0, tower_w=100.0,
             slide_w=136.0, slide_len=130.0, block_offset=5.0)
LADDER = dict(H=60.0, wall=2.5, long_w=40.0, long_y=(-350.0, 350.0), front_y=(-350.0, -310.0), bf_y=(-250.0, -210.0),
              end_y=(310.0, 350.0), pocket_w=80.0, pad_t=13.0, cross_drop=5.0)   # profili 40 × 60: la staffa della chiocciola Y passa a 8 mm dal fondo
UPRIGHT = dict(t=6.0, depth=120.0, wall=None)
BEAM = dict(depth=50.0, height=120.0, wall=3.0, wall_face=4.0, recess_h=76.0, recess_d=41.0, end=3.0)
BEAM_X = (-110.0, 550.0)
X_SCREW_PAD = 7.0
NUT_BRACKET_T = 8.0
TAB_T = 12.0
CHAIN_X = dict(w=50.0, h=45.0, inset=10.0)
CHAIN_Y = dict(x0=513.0, x1=542.0, h=45.0, z0=12.0)   # catena Y bassa fra la testa a X max e la spalla destra
HEAD_AXIS_FROM_SLIDE = 65.0   # MGN12 (rotaia 8 mm) sul carrello: inviluppo testa ±70 a 8 mm dalle guide Z
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
    "MGN12 / MGN12H su X, Y e Z, SFU1204 con BK10/BF10 su tutti gli assi, NEMA17; spindle BLDC 400 W ER11 Ø52 (classe) nel mount comune.",
    "Telaio a scala in profili 40 × 60 (non 40 × 40): asse Y e staffa della chiocciola dentro il telaio con 8 mm di gioco e NEMA17 sotto la tavola.",
    "Spalle a piastra 6 mm ai lati della trave, flangia ICD §5 in basso (rialzi +50 mm); motore X sulla faccia esterna della spalla destra.",
    "Trave 50 × 120 con canale vite (non 40 × 80): BK10/BF10 fra le guide X a 104 mm con 8 mm dai pattini; vite Y 480 mm (non 470) per 8 mm a fine corsa.",
    "Asse spindle a 65 mm dalla slitta (Standard 53): con le guide MGN12 l'inviluppo testa ±70 resta a 8 mm dalle guide Z.",
    "ToolDock manuale: albero a camma nella master sul pull-stud comune (≥ 0,5 kN); sedi del clamp automatico e dei connettori del Platform Pack già lavorate.",
    "Massa dal CAD sopra il target di 18 kg (D010): la topologia della Standard, ridotta, non basta; servirebbe una Light a piastre (vite X sopra una trave a profilo, telaio a piastre) come nella BOM.",
)


def derived():
    return _S.derived(globals())


def spindle(mode=None):
    return _S.spindle(mode, globals())


SPINDLE = spindle()
