#!/usr/bin/env python3
"""Viste ortografiche ombreggiate del mule Standard (PNG da mesh, painter's algorithm).

Uso (dalla radice, con CadQuery): python tools/cad/render_views.py
Scrive cad/standard/views/<config>_<vista>.png: viste di controllo, non render estetici.
Richiede Pillow (pip install pillow).
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import standard_assembly as A  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = ROOT / "cad" / "standard" / "views"
VIEWS = {  # direzione di vista (dall'osservatore verso la macchina) e "su"
    "iso": ((-1.0, 1.3, -0.9), (0, 0, 1)),
    "front": ((0, 1, 0), (0, 0, 1)),
    "side": ((-1, 0, 0), (0, 0, 1)),
    "top": ((0, 0, -1), (0, 1, 0)),
}
RGB = {k: tuple(int(c * 255) for c in v) for k, v in A.COLORS.items()}


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def render(parts, view, size=900):
    d, up = VIEWS[view]
    d = norm(d)
    r = norm(cross(d, up))
    u = cross(r, d)
    light = norm((-0.4, 0.7, -0.6))
    tris = []
    for name, p in parts.items():
        vol = p["kind"] == "volume"
        verts, faces = p["shape"].tessellate(0.8, 0.5)
        pts = [(v.x, v.y, v.z) for v in verts]
        for (i, j, k) in faces:
            a, b, c = pts[i], pts[j], pts[k]
            n = cross(tuple(b[m] - a[m] for m in range(3)), tuple(c[m] - a[m] for m in range(3)))
            ln = math.sqrt(dot(n, n))
            if ln < 1e-9:
                continue
            n = tuple(x / ln for x in n)
            if dot(n, d) > 0 and not vol:      # faccia posteriore
                continue
            depth = dot(tuple((a[m] + b[m] + c[m]) / 3 for m in range(3)), d)
            shade = 0.45 + 0.55 * abs(dot(n, light))
            tris.append((depth, [(dot(q, r), dot(q, u)) for q in (a, b, c)], p["color"], shade, vol))
    xs = [x for t in tris for x, _ in t[1]]
    ys = [y for t in tris for _, y in t[1]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ss = 2                                    # supersampling per l'antialiasing
    s = (size - 40) * ss / max(x1 - x0, y1 - y0)
    w, h = int((x1 - x0) * s + 40 * ss), int((y1 - y0) * s + 40 * ss)
    tris.sort(key=lambda t: -t[0])
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    solid = ImageDraw.Draw(img)
    for depth, q, col, shade, vol in tris:
        cr, cg, cb = RGB[col]
        pts = [((x - x0) * s + 20 * ss, (y1 - y) * s + 20 * ss) for x, y in q]
        if vol:
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(pts, fill=(cr, cg, cb, 10))
            img.alpha_composite(layer)
            solid = ImageDraw.Draw(img)
        else:
            c = (int(cr * shade), int(cg * shade), int(cb * shade), 255)
            solid.polygon(pts, fill=c, outline=c)
    return img.convert("RGB").resize((w // ss, h // ss), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for cfg in ("HOME", "MAX"):
        a, _ = A.build(*A.P.CONFIGS[cfg])
        for view in VIEWS:
            render(a.parts, view).save(OUT / f"{cfg.lower()}_{view}.png", optimize=True)
            print(cfg, view)


if __name__ == "__main__":
    main()
