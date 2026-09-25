"""Base Standard · parametri geometrici del "digital mule" (unica fonte di verità CAD).

Sistema di riferimento macchina (fisso al telaio):
- X lungo la trave (sinistra → destra), Y dal fronte al retro, Z verso l'alto;
- z = 0 è il piano superiore del basamento (appoggio guide Y);
- l'asse utensile sta sempre sul piano y = 0 (ponte fisso, D006): la tavola si muove in Y;
- x = 0 è la posizione dell'asse utensile con X in HOME.

Coordinate asse (come le vede il controllo): X 0…450, Y 0…350, Z 0…−140 (0 = alto).
Con tavola a Y, un punto della tavola a coordinata locale (xl, yl) sta in (xl, yl − Y):
l'utensile in (X, Y) tocca sempre il punto (X, Y) della superficie utile.

Valori da decisioni congelate: D006, D015, D016, D018, D019, D021, D022, ICD v4.
Valori marcati MULE sono scelte di questo primo assieme, da rivedere dopo l'analisi.
Tutte le quote in mm.
"""

# ------------------------------------------------------------------ corse (D019, TARGET)
TRAVEL = {"X": 450.0, "Y": 350.0, "Z": 140.0}
CONFIGS = {  # posizioni asse (X, Y, Z_giù) per l'analisi
    "HOME": (0.0, 0.0, 0.0),
    "CENTER": (225.0, 175.0, 70.0),
    "MAX": (450.0, 350.0, 140.0),
}
MARGIN = 10.0            # D019: margine per lato su guide e viti

# ------------------------------------------------------------------ componenti (D015, D019, D022)
X_AXIS = dict(rail="HGR15", block="HGH15CA", rail_len=640.0, block_pitch=100.0,
              rail_spacing=110.0, screw="SFU1605", screw_len=590.0, motor="NEMA23_CL_2NM",
              bk="BK12", bf="BF12")
Y_AXIS = dict(rail="MGN15", block="MGN15H", rail_len=630.0, block_pitch=200.0,
              rail_spacing=300.0, screw="SFU1605", screw_len=490.0, motor="NEMA23_CL_2NM",
              bk="BK12", bf="BF12")
Z_AXIS = dict(rail="HGR15", block="HGH15CA", rail_len=310.0, block_pitch=80.0,
              rail_spacing=110.0, screw="SFU1204", screw_len=260.0, motor="NEMA23_CL_2NM",
              bk="BK10", bf="BF10")

# supporti vite (quote tipiche catalogo, da verificare): larghezza, altezza, spessore, altezza asse, foro
SUPPORTS = {
    "BK12": dict(W=60.0, H=43.0, T=25.0, h=25.0, bore=12.0),
    "BF12": dict(W=60.0, H=43.0, T=20.0, h=25.0, bore=12.0),
    "BK10": dict(W=60.0, H=39.0, T=25.0, h=22.0, bore=10.0),
    "BF10": dict(W=60.0, H=39.0, T=20.0, h=22.0, bore=8.0),
}
COUPLING = {"SFU1605": dict(D=32.0, L=30.0), "SFU1204": dict(D=25.0, L=25.0)}

# ------------------------------------------------------------------ tavola e pallet (D018, ICD v4)
TABLE = dict(W=450.0, D=350.0, T=10.0, skin=6.0, boss_d=16.0, rim=12.0,
             pad_w=40.0, pad_l=66.0)
GRID = dict(pitch=50.0, nx=9, ny=7, x0=25.0, y0=25.0, hole=6.0)   # 9 × 7 fori M6, 63 inserti
R1 = (50.0, 50.0)          # boccola tonda Ø8 H7
R2 = (400.0, 50.0)         # asola Ø8, lungo X
R_BORE = 8.0
R2_SLOT = 12.0

# ------------------------------------------------------------------ ToolDock (D016, ICD v4)
HEAD = dict(W=110.0, D=140.0, L=220.0)   # inviluppo testa classe L/S sotto il coupling
MASTER = dict(W=120.0, T=15.0)            # piastra master sotto la slitta Z (MULE)
HEAD_AXIS_FROM_SLIDE = HEAD["D"] / 2      # asse utensile a metà profondità testa (MULE)
TIP_AT_Z_BOTTOM = 0.0                     # punta a Z = −140 sul piano tavola (MULE)

# ------------------------------------------------------------------ strutture custom (MULE)
AL_DENSITY = 2.70e-6      # kg/mm³
PLATE = dict(carriage_t=15.0, slide_t=12.0, carriage_w=170.0, carriage_below=90.0,
             slot_w=64.0, slot_from=50.0, tower_w=100.0, slide_w=170.0, slide_ext_top=20.0)
BASE = dict(x0=25.0, x1=425.0, y0=-350.0, y1=350.0, H=60.0, top=8.0, wall=8.0,
            channel_w=80.0, pad=3.0,
            cross_y0=105.0, cross_y1=285.0)
UPRIGHT = dict(t=15.0, depth=160.0, window=(80.0, 250.0))
BEAM = dict(depth=80.0, height=140.0, wall=6.0, recess_h=90.0, recess_d=26.0, end=6.0)
BEAM_X = (-155.0, 605.0)  # estensione trave = larghezza fra le facce esterne delle spalle
NUT_BRACKET_T = 12.0
Z_NUT_MIN_ABOVE_ZC = 98.0   # fondo chiocciola Z con Z tutto giù, sopra il centro carrello (MULE)
X_SCREW_PAD = 2.0          # spessore spessori sotto BK/BF X nel canale della trave (MULE)
CLEAR_WARN = 3.0          # sotto questo gioco tra parti in moto relativo: avviso

# ------------------------------------------------------------------ riserve di volume
CHAIN_X = dict(w=80.0, h=60.0)                    # sopra la trave
CHAIN_Y = dict(x0=520.0, x1=570.0, h=60.0)        # a destra della tavola
DOCK = dict(mode="inside", x_inside=450.0, x_outside=580.0, slots=2, pitch=130.0)  # D021


def derived():
    """Quote derivate dalla catena di tolleranze. Ritorna un dict."""
    import parts
    xb, zb = parts.BLOCKS[X_AXIS["block"]], parts.BLOCKS[Z_AXIS["block"]]
    yb = parts.BLOCKS[Y_AXIS["block"]]
    d = {}
    d["table_bottom"] = yb["H"]                           # tavola sui pattini Y
    d["table_top"] = d["table_bottom"] + TABLE["T"]
    # catena in Y dall'asse utensile verso la trave
    d["slide_front"] = HEAD_AXIS_FROM_SLIDE
    d["slide_back"] = d["slide_front"] + PLATE["slide_t"]           # base rotaie Z
    d["carriage_front"] = d["slide_back"] + zb["H"]                 # testa pattini Z
    d["carriage_back"] = d["carriage_front"] + PLATE["carriage_t"]  # testa pattini X
    d["beam_face"] = d["carriage_back"] + xb["H"]                   # base rotaie X
    d["beam_back"] = d["beam_face"] + BEAM["depth"]
    # catena in Z
    z_block_half = Z_AXIS["block_pitch"] / 2 + zb["L"] / 2
    d["tip_bottom"] = d["table_top"] + TIP_AT_Z_BOTTOM
    d["slide_below_blocks"] = z_block_half + MARGIN
    d["zc"] = (d["tip_bottom"] + HEAD["L"] + MASTER["T"] + d["slide_below_blocks"]
               + TRAVEL["Z"])                                        # centro guide X e pattini Z
    d["beam_bottom"] = d["zc"] - BEAM["height"] / 2
    d["beam_top"] = d["zc"] + BEAM["height"] / 2
    d["a_tool_to_x_face"] = d["beam_face"]                           # braccio "a" D015
    d["b_tip_below_x_rails"] = d["zc"] - d["tip_bottom"]             # braccio "b" D015 a Z giù
    return d
