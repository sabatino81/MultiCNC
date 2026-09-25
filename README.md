# MultiCNC

MultiCNC is a modular, high-precision desktop CNC platform.

This repository is the engineering source of truth for the project: business case, architecture, BOMs, modules, interfaces, decisions and technical documentation.

## Documentation
Open `index.html` for the navigable engineering dashboard (works from disk, any web root or GitHub Pages subpath).

## Current design principles
- Three bases (Light Core ~18 kg, Standard ~45 kg (mule v2, soglia 42 kg, target 35–37 kg), Pro ~70 kg) sharing work area, pallets, kinematics and the **common mechanical interface** of the ToolDock (ICD v4).
- Two electrical profiles (ICD v4, D026): **Core** on the Light Core (grblHAL, open-loop, manual ToolDock clamp) and **Platform** on Standard and Pro (Mesa + LinuxCNC, closed-loop, automatic ToolDock, data bus).
- The **Platform Pack** is a field upgrade that brings the Light Core to the Platform profile, reusing motors, mechanics and cabling (D026).
- Automatic ToolDock for complete head/module changes on the Platform profile; same master, receiver and pull-stud on every base.
- ATC is separate from ToolDock: ATC changes cutters inside an ATC spindle; ToolDock changes the complete process module.
- Optional enclosure on every base, as an independent skin fixed to the base frame, never to the gantry (D025).
- Modular expansion rather than a fully-loaded base: PCB, aluminium, thermoforming, diode laser, fiber MOPA, knife, dispenser and vision are modular capabilities.
- Specifications marked **TARGET** are engineering goals until validated on hardware. Light Core and Platform Pack BOMs are volume-50 cost targets; Standard and Pro BOMs are single-unit prototype estimates.

## Status
V0.6 — Business chapter, Light Core / Platform Pack, ICD v4, optional enclosure; Standard in development — 25 Sep 2026.
