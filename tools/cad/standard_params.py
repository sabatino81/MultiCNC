"""Base Standard · parametri geometrici del "digital mule" (unica fonte di verità CAD).

Mule v1 (D027): pattini Z sulla slitta mobile e guide Z sul carrello X; trave abbassata
e disaccoppiata dalla zona guide Z; telaio a scala (due longheroni Y + traverse); docking
unico a X 440 con magazine dietro la spalla destra, nessun volume permanente davanti alla trave.

Sistema di riferimento macchina (fisso al telaio):
- X lungo la trave (sinistra → destra), Y dal fronte al retro, Z verso l'alto;
- z = 0 è il piano superiore dei longheroni (appoggio guide Y);
- l'asse utensile sta sempre sul piano y = 0 (ponte fisso, D006): la tavola si muove in Y;
- x = 0 è la posizione dell'asse utensile con X in HOME.

Coordinate asse (come le vede il controllo): X 0…450, Y 0…350, Z 0…−140 (0 = alto).
Con tavola a Y, un punto della tavola a coordinata locale (xl, yl) sta in (xl, yl − Y):
l'utensile in (X, Y) tocca sempre il punto (X, Y) della superficie utile.

Valori da decisioni congelate: D006, D015, D016, D018, D019, D021, D022, D027, ICD v4.
Valori marcati MULE sono scelte dell'assieme, da rivedere dopo l'analisi.
Tutte le quote in mm.
"""

# ------------------------------------------------------------------ corse (D019, TARGET)
TRAVEL = {"X": 450.0, "Y": 350.0, "Z": 140.0}
DOCK_X = 440.0             # D027: unica posizione di docking, 10 mm prima del fine corsa X
CONFIGS = {  # posizioni asse (X, Y, Z_giù) per l'analisi
    "HOME": (0.0, 0.0, 0.0),
    "CENTER": (225.0, 175.0, 70.0),
    "MAX": (450.0, 350.0, 140.0),
    "DOCK": (DOCK_X, 0.0, 0.0),
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
CLEAR_UNDER_BEAM = TRAVEL["Z"] + 10.0     # luce sotto la trave sopra la tavola (non è l'altezza massima del pezzo: va tolto pallet/fixture)
PALLET_T = 15.0            # pallet tipico sopra la tavola (MULE): pezzo max sotto la trave = luce − pallet; +75 mm con i rialzi (D007)
PLATE = dict(carriage_t=15.0, slide_t=12.0, carriage_w=170.0, below_x_blocks=18.0,
             slot_w=70.0, tower_w=100.0, slide_w=150.0, slide_len=160.0, block_offset=5.0)
LADDER = dict(H=60.0, wall=4.0,                                  # tubi rettangolari Al
              long_w=40.0, long_y=(-350.0, 350.0),              # longheroni sotto le guide Y
              front_y=(-350.0, -310.0), bf_y=(-250.0, -210.0),  # traverse
              end_y=(310.0, 350.0), pocket_w=80.0, pad_t=12.0, cross_drop=5.0)
UPRIGHT = dict(t=15.0, depth=120.0)
BEAM = dict(depth=80.0, height=140.0, wall=6.0, recess_h=90.0, recess_d=31.0, end=6.0)
BEAM_X = (-155.0, 605.0)  # estensione trave = larghezza fra le facce esterne delle spalle
NUT_BRACKET_T = 10.0
X_SCREW_PAD = 7.0          # spessori sotto BK/BF X nel canale della trave (MULE)
SUPPORT_GAP_Z = 8.0        # D028: gioco BK/BF Z ↔ slitta e piastrina (≥ 8 mm)
TAB_T = 10.0               # piastrina chiocciola Z sulla slitta
CLEAR_FAIL = 5.0           # D027/D028: sotto questo gioco tra parti in moto relativo → FAIL
CLEAR_PASS = 8.0           # 5–8 mm → WARNING; ≥ 8 mm → PASS (obiettivo nominale 8–10 mm)
CLEAR_WARN = CLEAR_PASS    # soglia di controllo dei giochi
MASS_GATE_KG = 42.0        # D027: soglia dura del mule (non più 32,8 kg)
MASS_TARGET_KG = 40.0      # D028: target di progetto prima di cablaggi e dettagli; 35–37 kg solo se la FEA lo concede
B_TARGET = (250.0, 300.0)  # D027: braccio b ideale / massimo

# ------------------------------------------------------------------ riserve di volume
CHAIN_X = dict(w=75.0, h=60.0, inset=5.0)        # sopra la trave, arretrata dalla faccia guide
CHAIN_Y = dict(x0=520.0, x1=570.0, h=60.0)        # a destra della tavola
MAGAZINE = dict(x=(500.0, 680.0), y=(280.0, 460.0), z=(180.0, 620.0))  # dietro la spalla destra (D027)
TRANSFER_X = (530.0, 640.0)                       # corridoio del trasferitore oltre il carrello
TRANSFER_TOP = 616.0                              # coupling della testa sopra trave e catena X (fondo testa 20 mm sopra la catena)
STORE_POSE = (590.0, 370.0)                       # centro testa nel magazine (x, y), coupling a TRANSFER_TOP
TRANSFER_STEPS = 40                               # campioni lungo la traiettoria magazine → dock
SWEEP_N = 5                                       # griglia 5 × 5 × 5 del workspace (vertici compresi)


def derived():
    """Quote derivate dalla catena di quote. Ritorna un dict."""
    import parts
    xb, zb = parts.BLOCKS[X_AXIS["block"]], parts.BLOCKS[Z_AXIS["block"]]
    yb = parts.BLOCKS[Y_AXIS["block"]]
    d = {}
    d["table_bottom"] = yb["H"]                           # tavola sui pattini Y
    d["table_top"] = d["table_bottom"] + TABLE["T"]
    # catena in Y dall'asse utensile verso la trave
    d["slide_front"] = HEAD_AXIS_FROM_SLIDE
    d["slide_back"] = d["slide_front"] + PLATE["slide_t"]           # testa pattini Z (sulla slitta)
    d["carriage_front"] = d["slide_back"] + zb["H"]                 # base guide Z (sul carrello)
    d["carriage_back"] = d["carriage_front"] + PLATE["carriage_t"]  # testa pattini X
    d["beam_face"] = d["carriage_back"] + xb["H"]                   # base guide X
    d["beam_back"] = d["beam_face"] + BEAM["depth"]
    # catena in Z
    d["tip_bottom"] = d["table_top"] + TIP_AT_Z_BOTTOM
    d["coupling_bottom"] = d["tip_bottom"] + HEAD["L"]              # coupling con Z tutto giù
    d["coupling_top"] = d["coupling_bottom"] + TRAVEL["Z"]
    d["slide_bottom_low"] = d["coupling_bottom"] + MASTER["T"]
    d["z_block_span"] = Z_AXIS["block_pitch"] + zb["L"]
    d["z_rail_bottom"] = d["slide_bottom_low"] + PLATE["block_offset"] - MARGIN
    d["beam_bottom"] = d["table_top"] + CLEAR_UNDER_BEAM
    d["zx"] = d["beam_bottom"] + BEAM["height"] / 2                  # centro guide X
    d["beam_top"] = d["zx"] + BEAM["height"] / 2
    d["a_tool_to_x_face"] = d["beam_face"]                           # braccio "a" D015
    d["b_tip_below_x_rails"] = d["zx"] - d["tip_bottom"]             # braccio "b" D015 a Z giù
    d["z_lever_low"] = d["slide_bottom_low"] + PLATE["block_offset"] - d["tip_bottom"]  # punta ↔ pattino Z più basso
    return d
