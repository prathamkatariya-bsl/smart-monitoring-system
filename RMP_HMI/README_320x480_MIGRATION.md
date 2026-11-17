# DWIN DMG48320C035_03WN migration

The original `RMP_HMI` package targets 240x320. The production target is the DWIN DMG48320C035_03WN commercial-grade 320x480 portrait panel.

Use `DGUS_Assets_320x480_DRAFT/layout_320x480.json` and `VP_map_320x480.csv` as the source-of-truth migration contract. The generated BMPs are draft geometric conversions for UI/UX review; they are not a final pharmaceutical release artwork package. The original `DWIN_SET` remains unchanged until the final DGUS project is exported and bench-tested on the exact panel.

The firmware owns MODE/UP/DOWN/SELECT navigation, 25 ms debounce, 500 ms hold-to-repeat, stop-at-edge focus behavior, and the three-row diagnostics window. DGUS should bind its highlight/list controls to VPs `0x1320`–`0x1323`.
