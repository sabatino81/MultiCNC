#!/usr/bin/env python3
"""D019 · Lunghezze reali di guide e viti per asse e per base.

Guida: L_rail >= corsa + 2*margine + interasse pattini + lunghezza pattino
(entrambi i pattini sempre interamente sulla rotaia).
Vite (lunghezza TOTALE, estremità lavorate comprese):
L_vite >= corsa + 2*margine + lunghezza chiocciola + 2*gioco + estremità lato BK + estremità lato BF.
Margine per lato: homing, fine corsa e hard stop. Arrotondamento ai 10 mm.
Quote estremità: tipiche per supporti BK/BF, da confermare con il fornitore.
"""
import math

MARGIN = 10.0     # mm per lato
CLEAR = 5.0       # mm per lato tra chiocciola e supporti
BLOCK_L = {"MGN12H": 45.4, "MGN15H": 58.8, "HGH15CA": 61.4, "HGH20CA": 77.5}  # schede HIWIN
NUT_L = {"SFU1204": 35.0, "SFU1605": 42.0}
ENDS = {"SFU1204": (45.0, 10.0), "SFU1605": (55.0, 10.0)}   # lato BK, lato BF

# base: asse -> (corsa, pattino, interasse pattini, vite)
AXES = {
    "Light":    {"X": (450, "MGN12H", 100, "SFU1204"), "Y": (350, "MGN12H", 200, "SFU1204"), "Z": (140, "MGN12H", 70, "SFU1204")},
    "Standard": {"X": (450, "HGH15CA", 100, "SFU1605"), "Y": (350, "MGN15H", 200, "SFU1605"), "Z": (140, "HGH15CA", 80, "SFU1204")},
    "Pro":      {"X": (450, "HGH20CA", 100, "SFU1605"), "Y": (350, "HGH20CA", 200, "SFU1605"), "Z": (140, "HGH15CA", 90, "SFU1204")},
}


def up10(x):
    return int(math.ceil(x / 10.0) * 10)


def lengths(travel, blk, spacing, screw):
    rail = up10(travel + 2 * MARGIN + spacing + BLOCK_L[blk])
    bk, bf = ENDS[screw]
    scr = up10(travel + 2 * MARGIN + NUT_L[screw] + 2 * CLEAR + bk + bf)
    return rail, scr


if __name__ == "__main__":
    for base, axes in AXES.items():
        for ax, (t, blk, sp, scr) in axes.items():
            r, s = lengths(t, blk, sp, scr)
            print(f"{base:9} {ax}: corsa {t} mm · {blk} a {sp} mm -> guida >= {r} mm · {scr} totale >= {s} mm")
