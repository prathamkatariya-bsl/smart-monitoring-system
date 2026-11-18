# 2026-11-18 — DGUS HMI v3 integration

## Supplied change

Integrated the supplied `DGUS_Assets_v3_320x480` package for the DMG48320C035_03WN 320×480 portrait panel.

## HMI contract changes

- Replaced the generated draft package with the supplied v3 backgrounds, icon-library source rasters, placement maps, VP map, serial frames, QA checklist and implementation guides.
- Page map is now: boot 0; assignment-unassigned 1; assignment-assigned 2; network setup 3; device-not-claimed 4; pre-start 5; running 6; alarm 7; completed 8; diagnostics 9.
- Retired the v2 VPs listed by the supplied VP map; firmware no longer writes those addresses.
- Added active button icon state VPs 0x1330–0x1334.
- Updated diagnostics to seven logical rows rendered through five visible slots, with a three-position scroll thumb and a selectable RETURN action.
- Applied the supplied text-box widths and character limits, including the 17-character analyst-name field and v3 28×56 hero values.

## Firmware behavior

- Assignment and pre-start focus state is rendered through the v3 icon libraries.
- Diagnostics UP/DOWN navigation supports five visible rows, scroll positions 1–5 through 3–7, and a final RETURN focus.
- MODE remains the safe back action; SELECT on diagnostics RETURN exits to the previous screen.
- Display writes use only the active v3 VP contract.

## Verification

- All supplied background BMPs validated at 320×480.
- Supplied VP map validated: 100 rows, 72 active and 28 retired.
- Static scan confirms no active firmware writes to retired v2 VPs.
- Backend/frontend verification is rerun after clean dependency installation.
- ESP-IDF compilation and physical DGUS bench qualification require the ESP-IDF toolchain and exact display hardware.
