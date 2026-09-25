#!/usr/bin/env python3
"""Modelli 3D del mule Standard per il visualizzatore web (base/viewer-3d.html): glTF binario per configurazione.

Uso (dalla radice, con CadQuery): python tools/cad/export_glb.py
Scrive cad/standard/glb/standard_<config>.glb. I volumi riservati (catene, magazine, inviluppi) non entrano.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import cadquery as cq  # noqa: E402
import standard_assembly as A  # noqa: E402

OUT = ROOT / "cad" / "standard" / "glb"


def export(cfg):
    a, _ = A.build(*A.P.CONFIGS[cfg], cfg)
    asm = cq.Assembly(name=f"MultiCNC_Standard_mule_{cfg}")
    for name, p in a.parts.items():
        if p["kind"] == "volume":
            continue
        r, g, b = A.COLORS[p["color"]]
        asm.add(cq.Workplane().add(p["shape"]), name=name, color=cq.Color(r, g, b, 1.0))
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"standard_{cfg.lower()}.glb"
    asm.save(str(f), exportType="GLTF", tolerance=0.4, angularTolerance=0.35)
    return f


def main():
    for cfg in ("HOME", "CENTER", "MAX", "DOCK"):
        f = export(cfg)
        print(cfg, f.name, f"{f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
