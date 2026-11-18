# DWIN 320×480 HMI package

The active HMI target is the DWIN DMG48320C035_03WN portrait panel at 320×480. The current migration contract is in `DGUS_Assets_320x480/` and includes backgrounds, icon-library sources, placement maps, `VP_map.csv`, serial test frames and DGUS implementation guides.

The supplied v3 package is the active geometry and interaction contract. It is not a final pharmaceutical release package until the DGUS tool generates the panel binaries and the result is bench-tested on the exact display. Superseded 240×320 material is retained under `archive/legacy-240x320/` and is not an active source of truth.

Use [`../docs/hmi.md`](../docs/hmi.md) for the navigation contract, release workflow and validation checklist.
