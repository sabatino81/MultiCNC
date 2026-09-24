# MultiCNC

MultiCNC is a modular, high-precision desktop CNC platform.

This repository is the engineering source of truth for the project: architecture, BOMs, modules, interfaces, decisions and technical documentation.

## Documentation
Open `index.html` for the navigable engineering dashboard (works from disk, any web root or GitHub Pages subpath).

## Current design principles
- Precision-first base machine.
- Modular expansion rather than a fully-loaded base.
- Motorized gantry height adjustment with mechanical locking.
- One universal automatic ToolDock for complete head/module changes.
- ATC is separate from ToolDock: ATC changes cutters inside an ATC spindle; ToolDock changes the complete process module.
- PCB, aluminium, thermoforming, diode laser, fiber MOPA, knife, dispenser and vision are modular capabilities.
- Specifications marked **TARGET** are engineering goals until validated on hardware.

## Status
V0.4 — Base Precision documentation + detailed BOM — 24 Sep 2026.
