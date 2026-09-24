#!/usr/bin/env python3
"""D020 · Potenza garantita ai moduli con linea 48 V MODULE AUX dedicata (ICD v3).

La linea moduli non dipende più dal profilo motion: 48 V aux garantito =
80% del PSU dedicato, limitato dal rating del connettore (240 W).
24 V: PSU HDR-100-24 comune (~92 W); garantito = 80% − carico logica macchina,
arrotondato per difetto a 40 W su tutte le basi (D022). Picchi dei motori non toccano più la linea moduli.
"""
CONNECTOR_48V, CONNECTOR_24V = 240, 48
BASES = {"Light": (150, 30), "Standard": (150, 30), "Pro": (350, 34)}  # PSU aux 48 V W, logica 24 V W
PSU24 = 92   # HDR-100-24: 24 V × 3,83 A ≈ 92 W (la variante -24N è ~100 W, non-LPS)

if __name__ == "__main__":
    for n, (aux48, logic) in BASES.items():
        g48 = min(aux48 * 0.8, CONNECTOR_48V)
        g24 = min(PSU24 * 0.8 - logic, CONNECTOR_24V)
        print(f"{n:9} 48 V MODULE AUX {aux48} W -> garantito {g48:.0f} W · 24 V -> garantito {g24:.0f} W")
