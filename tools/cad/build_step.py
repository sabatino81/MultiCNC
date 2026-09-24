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
    # guide: rotaia con 2 pattini, lunghezze di riferimento delle BOM
    "mgn12_rail_600_2xMGN12H": lambda: parts.rail_with_blocks("MGN12", "MGN12H", 600),
    "mgn12_rail_250_2xMGN12H": lambda: parts.rail_with_blocks("MGN12", "MGN12H", 250, spacing=70),
    "mgn15_rail_600_2xMGN15H": lambda: parts.rail_with_blocks("MGN15", "MGN15H", 600),
    "hgr15_rail_600_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 600),
    "hgr15_rail_300_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 300, spacing=90),
    "hgr15_rail_350_2xHGH15CA": lambda: parts.rail_with_blocks("HGR15", "HGH15CA", 350, spacing=110),
    "hgr20_rail_600_2xHGH20CA": lambda: parts.rail_with_blocks("HGR20", "HGH20CA", 600),
    # viti con chiocciola a flangia
    "sfu1204_300": lambda: parts.ballscrew("SFU1204", 300),
    "sfu1204_550": lambda: parts.ballscrew("SFU1204", 550),
    "sfu1204_600": lambda: parts.ballscrew("SFU1204", 600),
    "sfu1605_350": lambda: parts.ballscrew("SFU1605", 350),
    "sfu1605_550": lambda: parts.ballscrew("SFU1605", 550),
    "sfu1605_600": lambda: parts.ballscrew("SFU1605", 600),
    # motori closed-loop
    "nema17_closed_loop": lambda: parts.motor("NEMA17_CL"),
    "nema23_closed_loop_2nm": lambda: parts.motor("NEMA23_CL_2NM"),
    "nema23_closed_loop_3nm": lambda: parts.motor("NEMA23_CL_3NM"),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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
