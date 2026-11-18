# Active DGUS HMI package — v3

This directory is the current 320×480 HMI contract supplied on 2026-11-18.
The source package is retained as provided, including page backgrounds, icon-library
source rasters, placement maps, VP_map.csv, serial frames and QA scripts.

The ESP32 firmware must be built against this package. Do not use the archived
`RMP_HMI/archive/DGUS_Assets_320x480_DRAFT_legacy` package for release or commissioning.
Before hardware release, generate the complete `DWIN_SET` in DGUS Designer and
bench-test it on the exact DMG48320C035_03WN order-code variant.

## Reproducible QA tooling
The supplied `tools/*.py` scripts accept `DGUS_FONT_DIR=/path/to/approved/ttf` for pixel-identical Poppins/JBM renders. On CI or a clean workstation they fall back deterministically to the installed DejaVu Sans family so geometry, VP and export checks remain executable; release artwork must use the approved design fonts.
