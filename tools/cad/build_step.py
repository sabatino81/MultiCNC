#!/usr/bin/env python3
"""Esporta gli STEP MultiCNC dei componenti commerciali in cad/step/.

Richiede CadQuery (pip install cadquery, meglio in un ambiente virtuale).
Uso dalla radice del repository:  python tools/cad/build_step.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import cadquery as cq  # noqa: E402
import parts  # noqa: E402

OUT = ROOT / "cad" / "step"

MODELS = {
    # guide: rotaia con 2 pattini, lunghezze D019
    "mgn12_rail_620_2xMGN12H": lambda: parts.rail_with_blocks("MGN12", "MGN12H", 620, spacing=100),
    "mgn12_rail_280_2xMGN12H": lambda: parts.rail_with_blocks("MGN12", "MGN12H", 280, spacing=70),
    "mgn15_rail_630_2xMGN15H": lambda: parts.rail_with_blocks("MGN15", "MGN15H", 630, spacing=200),
    "hgr15_rail_640_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 640, spacing=100),
    "hgr15_rail_310_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 310, spacing=80),
    "hgr15_rail_320_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 320, spacing=90),
    "hgr15_rail_350_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 350, spacing=110),
    "hgr20_rail_650_2xHGH20CA": lambda: parts.rail_with_blocks("HGR20", "HGH20CA", 650, spacing=100),
    # viti con chiocciola a flangia, lunghezza totale D019
    "sfu1204_260": lambda: parts.ballscrew("SFU1204", 260),
    "sfu1204_470": lambda: parts.ballscrew("SFU1204", 470),
    "sfu1204_570": lambda: parts.ballscrew("SFU1204", 570),
    "sfu1605_350": lambda: parts.ballscrew("SFU1605", 350),
    "sfu1605_490": lambda: parts.ballscrew("SFU1605", 490),
    "sfu1605_590": lambda: parts.ballscrew("SFU1605", 590),
    # motori closed-loop
    "nema17_closed_loop": lambda: parts.motor("NEMA17_CL"),
    "nema23_closed_loop_2nm": lambda: parts.motor("NEMA23_CL_2NM"),
    "nema23_closed_loop_3nm": lambda: parts.motor("NEMA23_CL_3NM"),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.step"):
        old.unlink()
    manifest = {}
    for name, make in MODELS.items():
        shape = make()
        path = OUT / f"{name}.step"
        cq.exporters.export(shape, str(path))
        bb = shape.val().BoundingBox()
        manifest[name] = {"file": f"{name}.step", "bytes": path.stat().st_size,
                          "bbox_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]}
        print(f"{name:28} {path.stat().st_size/1024:7.1f} KB  bbox {manifest[name]['bbox_mm']}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
