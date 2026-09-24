# MultiCNC

MultiCNC is a modular, high-precision desktop CNC platform.

This repository is the engineering source of truth for the project: architecture, BOMs, modules, interfaces, decisions and technical documentation.

## Documentation
Open `index.html` for the navigable engineering dashboard (works from disk, any web root or GitHub Pages subpath).

## Current design principles
- Three bases (Light ~18 kg, Standard ~31 kg, Pro 50–60 kg) sharing work area, ToolDock, pallets and electronics.
- Modular expansion rather than a fully-loaded base.
- Manual pinned risers on Light/Standard; motorized gantry lift with mechanical locking on Pro only.
- One universal automatic ToolDock for complete head/module changes.
- ATC is separate from ToolDock: ATC changes cutters inside an ATC spindle; ToolDock changes the complete process module.
- PCB, aluminium, thermoforming, diode laser, fiber MOPA, knife, dispenser and vision are modular capabilities.
- Specifications marked **TARGET** are engineering goals until validated on hardware.

## Status
V0.5 — Three bases (Light / Standard / Pro), Standard in development — 24 Sep 2026.
