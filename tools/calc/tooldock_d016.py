#!/usr/bin/env python3
"""D016 · ToolDock: forza del clamp e vantaggio meccanico della camma di sgancio.

Coupling cinematico a 3 sfere su cerchio di raggio R (ICD v1: Ø80 mm), preload P
lungo l'asse del pull-stud. Una sfera si stacca quando il suo carico assiale va a
zero: P/3 - Fz/3 - M*y/(1.5 R²) = 0, con y = R per la sfera più scarica.
Quindi P_min = Fz + 2 M / R; si applica un fattore di sicurezza S al distacco.

Carichi da D014: forza radiale alla punta × distanza punta–coupling, più peso e
inerzia della testa al baricentro (≤ 80 mm sotto, ≤ 25 mm dall'asse, ICD v1).
"""
from math import pi

G = 9.81
R = 0.040          # m, raggio cerchio sfere (ICD v1)
S = 1.5            # fattore di sicurezza contro il distacco
EFF = 0.9          # rendimento vite a ricircolo
Z_USE = 0.5        # quota della spinta di stallo Z usata per aprire il clamp
BASES = {
    #          F_rad  arm   m_head  a_xy  a_z  pull  Z motor Nm  Z lead m
    "Light":    (50,  0.100, 2.0,   3.0,  2.0,  15,  0.6,        0.004),
    "Standard": (150, 0.120, 4.0,   2.0,  2.0,  45,  2.0,        0.004),
    "Pro":      (300, 0.150, 7.0,   1.5,  2.0,  90,  3.0,        0.004),
}
COG_Z, COG_R = 0.080, 0.025


def analyse(F, arm, m, a_xy, a_z, pull, tz, lead):
    M = F * arm + m * G * COG_R + m * a_xy * COG_Z          # Nm
    Fz = m * G + m * a_z + pull                              # N, tende a staccare la testa
    p_min = Fz + 2 * M / R
    p_req = S * p_min
    z_stall = 2 * pi * tz * EFF / lead
    ma_req = p_req / (Z_USE * z_stall)
    contact = p_req / (6 * 0.7071)                           # N per contatto, rulli a 45°
    return dict(M=M, Fz=Fz, p_min=p_min, p_req=p_req, z_stall=z_stall, ma_req=ma_req, contact=contact)


if __name__ == "__main__":
    for name, args in BASES.items():
        r = analyse(*args)
        print(f"{name:9} M {r['M']:5.1f} Nm  Fz {r['Fz']:4.0f} N  P_min {r['p_min']:5.0f} N  "
              f"P (S={S}) {r['p_req']:5.0f} N  spinta Z stallo {r['z_stall']:5.0f} N  "
              f"vantaggio camma minimo {r['ma_req']:.2f}:1  carico per contatto {r['contact']:4.0f} N")
