#!/usr/bin/env python3
"""Rigenera le tabelle BOM delle tre basi a partire da tools/bom/data_*.py.

Per ogni pagina aggiorna: righe della tabella (con la colonna CAD / STEP da
cad_sources.py), KPI (righe, costo, massa macchina, massa esterna) e riga "Stima ingegneristica attuale". Il resto della pagina
(testi, callout, pannelli) non viene toccato.

Uso (dalla radice del repository):
    python3 tools/bom/build.py          # riscrive le pagine
    python3 tools/bom/build.py --check  # verifica soltanto; exit 1 se non allineate
"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cad_sources import cell  # noqa: E402
BASES = ["light", "standard", "pro", "platform"]
WHERE = {"M": "macchina", "A": "accessorio"}


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"data_{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compute(mod):
    rows, n, eur, km, kc, groups = [], 0, 0, 0.0, 0.0, {}
    for group, items in mod.G:
        rows.append(f'<tr class="group-row"><td colspan="11">{group}</td></tr>')
        for (i, gr, c, ql, qn, cand, spec, e, k, w, sc, st) in items:
            sub, kg = e * qn, k * qn
            if w != "A":
                n += 1
                eur += sub
                if w == "M":
                    km += kg
                    groups[group] = groups.get(group, 0) + kg
                else:
                    kc += kg
            where = WHERE.get(w, mod.EXTERNAL_LABEL)
            rows.append(
                f'<tr><td>{i}</td><td>{gr}</td><td>{c}</td><td class="qty">{ql}</td>'
                f'<td>{cand}</td><td>{spec}</td><td class="money">€{e}</td>'
                f'<td class="money">€{sub:,}</td><td class="money">{kg:.1f} <small>{where}</small></td>'
                f'<td class="status-{sc}">{st}</td><td class="cad">{cell(i)}</td></tr>'
            )
    return {"rows": "\n".join(rows), "n": n, "eur": eur, "km": round(km, 1), "kc": round(kc, 1), "groups": groups}


def it(x):
    """Formato italiano: 3104 -> 3.104, 31.0 -> 31,0."""
    return f"{x:,}".replace(",", ".") if isinstance(x, int) else str(x).replace(".", ",")


def render(html, d):
    start = html.index('<tr class="group-row"><td colspan="11">A ·')
    end = re.search(r'<tr class="group-row"><td colspan="11">[A-Z] · Totali', html).start()
    html = html[:start] + d["rows"] + "\n" + html[end:]

    kpis = [str(d["n"]), "€" + it(d["eur"]), it(d["km"]) + " kg", it(d["kc"]) + " kg"]
    found = list(re.finditer(r'<div class="bom-kpi"><strong>([^<]*)</strong>', html))
    if len(found) != 4:
        raise SystemExit("attesi 4 KPI nella pagina, trovati %d" % len(found))
    for m, v in reversed(list(zip(found, kpis))):
        html = html[: m.start(1)] + v + html[m.end(1):]

    html, count = re.subn(
        r'<td class="money"><b>€[\d,]+</b></td><td class="money"><b>[\d.]+ \+ [\d.]+</b></td>',
        f'<td class="money"><b>€{d["eur"]:,}</b></td><td class="money"><b>{d["km"]} + {d["kc"]}</b></td>',
        html,
    )
    if count != 1:
        raise SystemExit("riga 'Stima ingegneristica attuale' non trovata")
    return html


def main():
    check = "--check" in sys.argv
    stale = []
    for name in BASES:
        mod = load(name)
        d = compute(mod)
        page = ROOT / mod.PAGE
        old = page.read_text(encoding="utf-8")
        new = render(old, d)
        status = "ok" if new == old else ("DA AGGIORNARE" if check else "aggiornata")
        print(f"{mod.PAGE:24} {d['n']:3} righe  €{it(d['eur']):>6}  {it(d['km']):>5} kg macchina  {it(d['kc']):>5} kg esterno  [{status}]")
        for g, v in d["groups"].items():
            print(f"    {g}: {v:.2f} kg")
        if new != old:
            stale.append(mod.PAGE)
            if not check:
                page.write_text(new, encoding="utf-8")
    if check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
