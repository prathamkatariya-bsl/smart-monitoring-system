# Borosil RMP - DWIN HMI on the DMG48320C035_03W (3.5", 320x480)
Implementation guide for DGUS V7.651. It replaces the 240x320 / DMG32240C024 assumptions in the earlier guide. Items I could not confirm are tagged **[VERIFY]**.

## 1. What the new module is
| Item | Value | Source / confidence |
|---|---|---|
| Panel | 3.5", **320 x 480 portrait**, IPS, full viewing angle | DWIN / distributor listings - confirmed |
| Controller / OS | DWIN **T5L(1)**, DGUS II pre-installed | listings - confirmed |
| Colour | **16.7 M (24-bit)** - less banding than the old 262K panel, but still avoid large gradients | listings; some pages say 262K -> **[VERIFY]** in the datasheet |
| Interface | UART (TTL/CMOS), 10-pin 1.0 mm FPC; some variants expose RS232 | listings - confirm your connector |
| Power | 4.5-5.5 V | listings |
| Download | SD card or online serial | listings |
| Buzzer | **Built-in buzzer** on this family | listings; **[VERIFY]** on your variant |
| Touch | **Depends on the suffix**: `_03WN` none, `_03WTR` resistive, `_03WTC` capacitive | confirmed for the family |

**Action 1 - confirm the exact order code.** You wrote `DMG48320C035_03W` without the suffix. The suffix decides touch (N / TR / TC). The design uses physical keys (Up, Down, Select, Mode), so `_03WN` (no touch) is the natural fit. If you receive a touch variant, the touch return keys in the VP map also work, but the firmware must still handle the four keys.
**Action 2 - the buzzer.** Your document says one hardware siren is driven by the ESP32 and that Silence must mute every sound path. A built-in DWIN buzzer is a second sound path: leave it disabled in the CFG and never write the buzzer register **[VERIFY register/option in the guide]**.

## 2. What stays and what changes versus the 240x320 package
| Stays | Changes |
|---|---|
| Page numbers 0-9 (and the doc-ID mapping), all VP addresses, byte lengths, icon values, serial frames, key logic | **Every x, y, w, h**; background size (320x480); icon library images that are scaled; font cells; the VP-map coordinates and the placement maps |
Consequence: the old `DGUS_Assets_v2.zip` backgrounds and `VP_map.csv` coordinates cannot be used on this panel. Regenerate them from the updated design (section 6).

## 3. Same pixel density - what that means for text
- Old module: 240 px over about 36.7 mm active width = about 6.5 px/mm.
- New module: 320 px over about 49 mm active width = about 6.5 px/mm **[VERIFY active area in the datasheet]**.
So a 13 px character is **the same physical size on both panels**. The 3.5" panel gives you more area, not smaller text; to make text *physically* larger you must raise the pixel size. Larger fonts in your updated Figma are therefore the right move.

Suggested minimums on this panel (physical height of a capital letter about 2.5-3 mm at arm's length):
| Role | Minimum | DGUS cell for dynamic text |
|---|---|---|
| Secondary values (IP, UUID, diagnostics) | 16 px | 10x20 |
| Primary values (process name, limits) | 20 px | 12x24 |
| Large values (RPM, torque, duration, alarm rate) | 32 px | 20x40 |
| Hero temperature | 48 px | 28x56 |
| Static labels / captions (in the picture) | 12-14 px | - |
Rule: **cell width = font px x 0.6** for a monospaced font. Always set the text box to `chars x cell width` by `cell height` (your screenshot of 152x16 for 19 chars at 8x16 was already correct). Use only cell sizes that exist in your font tool **[VERIFY list in 0# word bank generating]**.

## 4. Crisp text on DGUS (what to set)
1. Text Display -> Encoding Mode **0x00 = 8bit** for ASCII-only strings (GBK is only needed for double-byte characters). If GBK looked better on the old panel, compare again on this one.
2. FONT0_ID = the font you generated/selected for that size; keep FONT1_ID unused.
3. Try the **"DGUSII Text (text display without aliasing)"** variable listed in the DGUS II guide (section 7.18) **[VERIFY: I confirmed it exists, not its settings]**.
4. Static text is baked into the BMP: export from Figma at exactly 1x (320x480), with text on whole-pixel positions; avoid text below 12 px.
5. Text colour field is RGB565: `F7BF` primary, `9D99` secondary, `84B7` muted, `079F` cyan, `15D0` green, `F4E1` amber, `EA28` red, `FF08` yellow, `FFFF` white.

## 5. DGUS project for this module
1. DGUS Tool V7.651 -> New -> resolution **320 x 480**, folder e.g. `C:\RMP_HMI\project_320x480`.
2. Keep **page numbers 0-9** and the same VP map; coordinates come from the new design.
3. Backgrounds: BMP **24-bit, 320x480**, named `0.bmp ... 9.bmp` -> ICL tool -> `32.ICL` into `DWIN_SET`.
4. Icon libraries 33-39 (conn pill, quality pill, status dot, alarm header, mute button, running footer, audit state) - **re-export at the new scale**; the alarm header becomes full width (320 px).
5. Font: `0_DWIN_ASC.HZK` from the 0# tool with the cells in section 3; copy to `DWIN_SET`.
6. CFG: baud 115200 8N1 (agree with firmware), start page 0, touch per variant, **buzzer off**, write-ACK as firmware wants.
7. DWIN OS file for the module's UART - do not change unless hardware confirms **[VERIFY]**.
8. Generate -> copy the whole `DWIN_SET` to a FAT32 (4096-byte allocation) SD card -> power-cycle to flash. Confirm the module has a TF slot or exposes the SD pins.
9. Bench-test with hex frames exactly as in the earlier `05_serial_test_frames.txt` (the VP addresses did not change).

## 6. Getting the updated design into DGUS
1. In Figma, duplicate the final frames into a section "DGUS EXPORT", each **320 x 480**, named `0` ... `9`.
2. Hide or delete every dynamic layer (the layers named `VP 0x....`) so the pictures contain only static items.
3. Export each frame as PNG at **1x**; check the file is exactly 320x480.
4. Export the dynamic fields' x, y, w, h (layer names carry the VP) into the VP map; check each box = chars x cell width by cell height.
5. Icon-library images: export each state component at 1x.
Then follow section 5.

## 7. Open items
- Exact suffix (N/TR/TC), connector and UART voltage level (3.3 V from the ESP32 vs the module's TTL/RS232 pins).
- Color depth (24-bit vs 18-bit) and active area from the datasheet.
- Font cell list, 0xFFFF end-marker option name, ICL number range, SD allocation unit.
- Whether the built-in buzzer can be fully disabled in your CFG.
