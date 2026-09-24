#!/usr/bin/env python3
"""D017 · Budget di potenza per base: cosa può chiedere un modulo al ToolDock.

48 V aux garantito = PSU motion − assorbimento medio motori in lavorazione − 20% margine.
24 V aux garantito = PSU logica − carico macchina − 20% margine.
Assorbimenti motori: stime per closed-loop in lavorazione (non picco), da misurare al banco.
"""
BASES = {
    #          PSU48  motori (n × W)  PSU24  carico logica W
    "Light":    (200, 3, 30,           60,   30),
    "Standard": (350, 3, 70,           60,   30),
    "Pro":      (600, 3, 90,           60,   34),   # il lift non si muove durante il taglio
}
MARGIN = 0.20
CONNECTOR_48V_W = 48 * 5   # rating P4/P5

if __name__ == "__main__":
    for n, (p48, k, w, p24, logic) in BASES.items():
        aux48 = p48 * (1 - MARGIN) - k * w
        aux24 = p24 * (1 - MARGIN) - logic
        print(f"{n:9} 48 V: PSU {p48} W, motori {k*w} W -> aux garantito {aux48:.0f} W  |  "
              f"24 V: PSU {p24} W, logica {logic} W -> aux garantito {aux24:.0f} W  |  connettore {CONNECTOR_48V_W} W")
