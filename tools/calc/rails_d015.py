#!/usr/bin/env python3
"""D015 · Guide Standard: MGN15H vs HGH15CA sui load case D014.

Modello a corpo rigido del carrello X: 2 guide sulla faccia della trave a distanza
verticale h, 2 pattini per guida a passo s. Forza applicata alla punta utensile,
a distanza b (verticale) dal centro delle guide e a (orizzontale) dalla faccia.
Ogni pattino è una molla di rigidezza k [N/µm] nella direzione di carico.

Dati pattini: schede HIWIN (hiwin.de), consultate il 2026-09-24.
La rigidezza dei pattini NON è nelle schede: lo script ricava la rigidezza minima
richiesta, da confrontare con le tabelle HIWIN per precarico o con prova al banco.
"""
BLOCKS = {  # C [N], C0 [N], massa [kg]
    "MGN15H": dict(C=6370, C0=9110, kg=0.09),
    "HGH15CA": dict(C=14700, C0=23470, kg=0.18),
}
F_RAD, F_AX, F_CRASH = 150.0, 200.0, 2300.0   # D014 Standard [N]
K_TIP_TARGET = 10.0     # D014: rigidezza statica alla punta ≥ 10 N/µm
RAIL_SHARE = 1 / 3      # quota della cedevolezza totale concessa alle guide X
a, b, s = 80.0, 180.0, 100.0  # mm, geometria Standard (ipotesi, Z tutto giù)


def block_loads(h):
    fy = F_RAD / 4 + (F_RAD * b / h) / 2                 # spinta verso la trave + momento
    fx = (F_RAD * b / h) / 2 + (F_RAD * a / s) / 2       # avanzamento lungo X
    fz = (F_AX * a / h) / 2 + F_AX / 4                   # foratura
    crash = (F_CRASH * b / h) / 2                        # stallo asse X alla punta
    return dict(fy=fy, fx=fx, fz=fz, crash=crash)


def compliance_factor(h):
    """δ_tip = F/k · (1/4 + (b/h)²) per il caso FY (traslazione + rotazione)."""
    return 0.25 + (b / h) ** 2


def k_required(h):
    k_rails_tip = K_TIP_TARGET / RAIL_SHARE   # N/µm alla punta dovuti alle sole guide
    return k_rails_tip * compliance_factor(h)


# Asse Y (tavola mobile, D006): pattini sotto la tavola, guide a interasse h_y,
# forza di taglio sul pezzo ad altezza b_y sopra il piano dei pattini.
h_y, b_y = 300.0, 130.0   # mm (ipotesi: guide Y a 300 mm, pezzo alto fino a 100 mm)


def k_required_y():
    return (K_TIP_TARGET / RAIL_SHARE) * (0.25 + (b_y / h_y) ** 2)


# Caso angolo (review 2): utensile a x = 225 mm dal centro tavola, forza in Y.
# L'imbardata è ripresa solo dalle forze laterali dei 4 pattini (interasse lungo Y s_y):
# θ = M / (k s_y²), spostamento all'utensile = F x² / (k s_y²); si somma il ribaltamento b_y/h_y.
x_corner, s_y = 225.0, 200.0


def k_required_y_corner():
    factor = (x_corner / s_y) ** 2 + (b_y / h_y) ** 2
    return (K_TIP_TARGET / RAIL_SHARE) * factor, factor, F_RAD * x_corner / 1000


if __name__ == "__main__":
    print(f"Asse Y: fattore {0.25 + (b_y / h_y) ** 2:.2f}  k minimo per pattino: {k_required_y():.0f} N/µm")
    kc, fc, myaw = k_required_y_corner()
    lat = myaw * 1000 / (2 * s_y)
    print(f"Asse Y angolo: momento di imbardata {myaw:.2f} Nm, forza laterale per pattino {lat:.0f} N, "
          f"fattore {fc:.2f}, k laterale minimo per pattino {kc:.0f} N/µm, fs MGN15H {BLOCKS['MGN15H']['C0']/lat:.0f}")
    for h in (70.0, 90.0, 110.0, 130.0):
        L = block_loads(h)
        pmax = max(L["fy"], L["fx"], L["fz"])
        print(f"h = {h:.0f} mm  fattore b/h: {compliance_factor(h):.2f}  k minimo per pattino: {k_required(h):.0f} N/µm")
        print(f"   carico max pattino (design) {pmax:.0f} N · crash {L['crash']:.0f} N")
        for n, d in BLOCKS.items():
            print(f"   {n:8} fs design {d['C0']/pmax:6.1f}   fs crash {d['C0']/L['crash']:4.1f}")
