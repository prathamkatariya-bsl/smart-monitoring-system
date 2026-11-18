# Borosil RMP - DWIN DGUS HMI v3.0: first-timer build guide (DMG48320C035_03W, 320 x 480)
Tool: **DGUS V7.651**. Everything here uses the files in this package. Items I could not confirm are tagged **[VERIFY]** - keep DWIN's *T5L_DGUSII Application Development Guide* open as tie-breaker. Menu names are given as I know them from V7.6xx; if a label differs on your build, trust the build and note it.

## 0. What changed versus the 240x320 package (firmware team: apply 1-8)
1. **Resolution is 320 x 480.** Every x/y/w/h, every background and every icon library image was regenerated. Old 240x320 assets cannot be reused.
2. **Page numbers are contiguous 0-9; doc IDs stay firmware constants:** `0x0000`->0, `0x0001`->1, `0x0010`->2, `0x0002`->3, `0x0003`->4, `0x0011`->5, `0x0012`->6, `0x0013`->7, `0x0014`->8, `0x0020`->9. The Idle screen is merged into Assignment (page 1 = UNASSIGNED, page 2 = ASSIGNED).
3. **Why two Assignment pages:** text colour is fixed per text control. Assigned shows the analyst in green, unassigned in white, and the two button pairs differ (disabled vs live). Two pages is the simplest, least fragile option.
4. **Keypad-only UI (no phone, no QR).** UP / DOWN move a focus ring between actionable blocks (and scroll the diagnostics list), SELECT = OK on the focused block, MODE = back one level, hold MODE 3 s = Diagnostics. No wrap at list ends. Focus is drawn by **icon variables** (button/row state images), so the ESP32 writes one 2-byte value per focus change.
5. **Dynamic text is ASCII only**, in JetBrains Mono on the DGUS cell grid (10x20, 12x24, 16x32, 20x40, 28x56). Static text (Poppins) is baked into the background pictures; units, degree sign and middle dot are painted in.
6. **Connectivity pill (lib 33) and quality pill (lib 34) are icon variables.** Running uses the quality pill (text + colour) instead of the bare dot of the 240x320 refined sketch, because status must never be colour-only. The connectivity pill is exported but not placed (see open questions).
7. **Diagnostics = the existing 7 rows shown 5 at a time.** Because a DGUS variable cannot move, the 5 visible rows are *slots*: slot k always shows row (window+k). Firmware rewrites 5 captions, 5 values, 5 dots, 5 row-state icons and the scroll thumb on every scroll.
8. **DWIN buzzer OFF.** The product has one ESP32-driven hardware siren and Silence must mute every sound path. Disable the module buzzer in the CFG and never write the buzzer register.
9. The old document's VP table overlapped itself and put loose BMPs in DWIN_SET. Use `VP_map.csv` (checked by script) and the file list in section 9.

## 1. Package contents
| Folder / file | Use |
|---|---|
| `01_backgrounds_bmp/0..9.bmp` (+ `_png`, `_named`) | Static page pictures, **24-bit, exactly 320x480**. File name = DGUS page number. |
| `02_icon_libraries/<lib>_<name>_<w>x<h>/<value>.bmp|png` | One folder per icon library; image N = variable value N. |
| `03_placement_map/` | magenta = text, orange = icon, cyan = bar, green = touch (exact boxes). |
| `04_preview_with_sample_values/` | Each design state as it should look with values written. |
| `VP_map.csv` | Every variable per page: VP, widget, x, y, w, h, bytes, cell, align, colour (+RGB565), max chars. Retired v2.0 addresses are listed and reserved. |
| `05_serial_test_frames.txt` | Hex frames for every page/VP/state (length-checked). |
| `06_firmware_change_list.md`, `07_qa_checklist.md` | For the embedded team / QA. |
| `tools/` | Generator: `spec3.py` (single source of truth), `render3.py`, `export3.py`, `docs3.py`. |

## 2. Prerequisites
1. DGUS Tool V7.651 (Windows), unzipped to a path without spaces, e.g. `C:\DWIN\DGUS`.
2. Fonts: install *JetBrains Mono* (free) so the font tool can see it.
3. SD card 4-16 GB, **FAT32, 4096-byte allocation unit**, empty except `DWIN_SET` [VERIFY in DWIN guide].
4. 5 V supply, USB-TTL adapter at 3.3 V, serial terminal in hex mode (SSCOM / Realterm).
5. Hardware questions: exact order code suffix (**N** none / **TR** resistive / **TC** capacitive - default design assumes N); TF slot location; which UART is wired to the ESP32.

## 3. Create the project
1. DGUS Tool -> **New**, resolution **320 x 480**, folder `C:\RMP_HMI\project_320x480`. Save once (creates `DWprj.hmi` and `DWIN_SET`). Keep the whole folder in Git.
2. Copy this package to `C:\RMP_HMI\assets`.

## 4. Background library (sector 32)
1. Put `0.bmp ... 9.bmp` in a folder named `32`. Keep the numbers 0-9. If the tool sorts 0,1,2,10 fix the order.
2. **ICL tool** -> choose folder -> quality 100 -> Generate -> `32.ICL` into **DWIN_SET**.
3. The number in an ICL file name is the flash sector; each file needs a unique number. 32 = pictures, **33-46 = icon libraries** [VERIFY that 46 is inside the allowed range in the flash-layout chapter; if the range ends earlier, tell me and I will merge the button libraries].
4. Logo: replace the placeholder wordmark in `0.bmp` (area x 60-260, y 64-150) with your logo, keeping 320x480 / 24-bit.

## 5. Icon libraries (one ICL per folder)
| Lib (ICL file) | Name | Image size | VP | Value -> image | Used on page |
|---|---|---|---|---|---|
| 33.ICL | conn_pill | 104x28 | 0x2018 (reserved) | 0=ONLINE; 1=OFFLINE | none (see open questions) |
| 34.ICL | quality_pill | 96x28 | 0x1301 | 0=GOOD; 1=SUSPECT; 2=BAD | 6 |
| 35.ICL | status_dot | 12x12 | 0x1310, 0x1311, 0x1312, 0x1313, 0x1314 | 0=good; 1=suspect; 2=bad; 3=off | 9 |
| 36.ICL | alarm_header | 320x48 | 0x1308 | 0=bright; 1=dim | 7 |
| 37.ICL | mute_button | 308x68 | 0x1309 | 0=SILENCE (focus); 1=SILENCED (disabled); 2=SILENCE (normal) | 7 |
| 38.ICL | run_footer_hint | 296x24 | 0x1307 | 0=hint; 1=silenced | 6 |
| 39.ICL | audit_state | 272x24 | 0x130A | 0=saving; 1=stored | 8 |
| 40.ICL | btn_accept | 308x68 | 0x1330 | 0=normal; 1=focus; 2=disabled | 2 |
| 41.ICL | btn_reject | 308x56 | 0x1331 | 0=normal; 1=focus; 2=disabled | 2 |
| 42.ICL | btn_start | 308x68 | 0x1332 | 0=normal; 1=focus; 2=disabled | 5 |
| 43.ICL | btn_cancel | 308x56 | 0x1333 | 0=normal; 1=focus; 2=disabled | 5 |
| 44.ICL | btn_return | 308x68 | 0x1334 | 0=normal; 1=focus; 2=disabled | 9 |
| 45.ICL | diag_row | 288x68 | 0x1320, 0x1321, 0x1322, 0x1323, 0x1324 | 0=normal; 1=focus | 9 |
| 46.ICL | scroll_thumb | 6x336 | 0x1325 | 0=rows 1-5; 1=rows 2-6; 2=rows 3-7 | 9 |

Rule that bites everyone: **change a picture -> regenerate its ICL -> copy to DWIN_SET -> Generate again.** Old pictures usually mean an old ICL on the card. All images carry their own opaque background (page background or card colour), so set the Icon Display to **opaque** [VERIFY]. Focus images contain the white 3 px ring and a 3 px pre-blended halo and are 12 px larger than the button so they redraw the margin cleanly.

## 6. Font, configuration, DWIN OS
1. **Font:** *0# word bank generating* -> JetBrains Mono -> cells **10x20, 12x24, 16x32, 20x40, 28x56** [VERIFY that all five are offered; if 28x56 is missing, snap the hero temperature to the nearest offered cell, e.g. 24x48 or 32x64, and tell me so I can reflow]. Output `0_DWIN_ASC.HZK` -> DWIN_SET.
2. **CFG** (`T5LCFG*.CFG`): baud **115200 8N1**, start page **0**, touch per variant (off for N), **DWIN buzzer OFF** [VERIFY option name], write-ACK only if firmware wants it (`5A A5 03 82 4F 4B`), rotation only if the screen comes up rotated.
3. **DWIN OS file** for the module's UART: do not change unless hardware confirms the UART [VERIFY].

## 7. Font clarity (why text blurs and how to fix it)
Causes: (a) anti-aliased *static* text under 12 px (this design has nothing under 14 px); (b) text box not equal to chars x cell width - glyphs get clipped or mis-spaced; (c) wrong encoding or FONT0_ID; (d) background BMP scaled instead of exactly 320x480.
Set: Text Display **Encoding mode 0x00 = 8bit** (ASCII only; compare GBK if it ever looks better); **FONT0_ID** = the 0# font; FONT1_ID unused; end marker **0xFFFF** on; box **exactly chars x cell width** by cell height (the tables below are already computed).
Test: write the longest strings from `05_serial_test_frames.txt` and look at 1-pixel stems at arm's length. Optionally try the **"DGUSII Text (text display without aliasing)"** variable (DGUS II guide section 7.18) for crisper text [VERIFY settings - I confirmed it exists, not its parameters].
Colour field is RGB565: F7BF primary, 9D99 secondary, 84B7 muted, 079F cyan, 15D0 green, F4E1 amber, EA28 red, FF08 yellow, FFFF white. Per-variable values are printed in the tables (recompute for any new colour).

## 8. Place the variables, page by page
Variable configuration (F3): select the page, draw a variable, then **type** x/y/w/h - never eyeball. Same VP on several pages must keep the same length (checked). Icon-library numbers and values are in section 5.

### Page 0 - Boot / POST (doc page 0x0000, picture `0.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x1306` | boot_progress | Progress Bar | 12 | 384 | 296 | 8 | 0-100, fill `#00F0FF` |
| `0x1060` | fw_version | Text Display | 12 | 412 | 160 | 20 | 18 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 16 chars |

### Page 1 - Assignment - UNASSIGNED (doc page 0x0001, picture `1.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2020` | lab_name | Text Display | 12 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x2000` | reactor_title | Text Display | 168 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x3000` | analyst_name | Text Display | 24 | 112 | 272 | 32 | 20 bytes, FONT0_ID cell 16x32 (V-L), align c, colour `#F4F7FC` = RGB565 `F7BF`, max 17 chars |
| `0x3020` | process_name | Text Display | 24 | 236 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |

### Page 2 - Assignment - ASSIGNED (doc page 0x0010, picture `2.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2020` | lab_name | Text Display | 12 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x2000` | reactor_title | Text Display | 168 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x3000` | analyst_name | Text Display | 24 | 112 | 272 | 32 | 20 bytes, FONT0_ID cell 16x32 (V-L), align c, colour `#10B981` = RGB565 `15D0`, max 17 chars |
| `0x3020` | process_name | Text Display | 24 | 236 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x1330` | btn_accept | Icon Display | 6 | 346 | 308 | 68 | library 40, opaque; 0=normal; 1=focus; 2=disabled |
| `0x3010` | touch: accept | Return Key Code (optional) | 12 | 352 | 296 | 56 | returns `0000` - only on a touch variant |
| `0x1331` | btn_reject | Icon Display | 6 | 418 | 308 | 56 | library 41, opaque; 0=normal; 1=focus; 2=disabled |
| `0x3010` | touch: reject | Return Key Code (optional) | 12 | 424 | 296 | 44 | returns `0001` - only on a touch variant |

### Page 3 - Network Setup (doc page 0x0002, picture `3.bmp`)
_No variables: fully static page (picture only)._

### Page 4 - Device Not Claimed (doc page 0x0003, picture `4.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2050` | device_uuid | Text Display | 24 | 176 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#00F0FF` = RGB565 `079F`, max 22 chars |
| `0x3280` | mac_address | Text Display | 24 | 252 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x3210` | ip_address | Text Display | 24 | 316 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x3220` | mqtt_broker | Text Display | 24 | 380 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |

### Page 5 - Pre-Start (doc page 0x0011, picture `5.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2020` | lab_name | Text Display | 12 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x2000` | reactor_title | Text Display | 168 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x3000` | analyst_name | Text Display | 24 | 60 | 272 | 32 | 20 bytes, FONT0_ID cell 16x32 (V-L), align l, colour `#00F0FF` = RGB565 `079F`, max 17 chars |
| `0x3020` | process_name | Text Display | 24 | 96 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x3080` | max_temp | Text Display | 176 | 158 | 60 | 24 | 8 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F4F7FC` = RGB565 `F7BF`, max 5 chars |
| `0x3090` | max_speed | Text Display | 176 | 218 | 60 | 24 | 8 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F4F7FC` = RGB565 `F7BF`, max 5 chars |
| `0x30A0` | max_roc | Text Display | 176 | 278 | 60 | 24 | 8 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F59E0B` = RGB565 `F4E1`, max 5 chars |
| `0x1332` | btn_start | Icon Display | 6 | 346 | 308 | 68 | library 42, opaque; 0=normal; 1=focus; 2=disabled |
| `0x3030` | touch: start | Return Key Code (optional) | 12 | 352 | 296 | 56 | returns `0000` - only on a touch variant |
| `0x1333` | btn_cancel | Icon Display | 6 | 418 | 308 | 56 | library 43, opaque; 0=normal; 1=focus; 2=disabled |
| `0x3030` | touch: cancel | Return Key Code (optional) | 12 | 424 | 296 | 44 | returns `0001` - only on a touch variant |

### Page 6 - Running (doc page 0x0012, picture `6.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2020` | lab_name | Text Display | 12 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x2000` | reactor_title | Text Display | 168 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x3000` | analyst_name | Text Display | 24 | 60 | 272 | 32 | 20 bytes, FONT0_ID cell 16x32 (V-L), align l, colour `#00F0FF` = RGB565 `079F`, max 17 chars |
| `0x3020` | process_name | Text Display | 24 | 96 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x1301` | temp_quality_pill | Icon Display | 200 | 142 | 96 | 28 | library 34, opaque; 0=GOOD; 1=SUSPECT; 2=BAD |
| `0x1100` | temp_value | Text Display | 64 | 170 | 168 | 56 | 8 bytes, FONT0_ID cell 28x56 (V-HERO), align r, colour `#00F0FF` = RGB565 `079F`, max 6 chars |
| `0x1130` | rpm_value | Text Display | 24 | 280 | 120 | 40 | 8 bytes, FONT0_ID cell 20x40 (V-XL), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 6 chars |
| `0x1140` | torque_value | Text Display | 180 | 280 | 120 | 40 | 8 bytes, FONT0_ID cell 20x40 (V-XL), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 6 chars |
| `0x2040` | clock | Text Display | 246 | 344 | 50 | 20 | 8 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#9DB0CF` = RGB565 `9D99`, max 5 chars |
| `0x11C0` | duration | Text Display | 24 | 368 | 160 | 40 | 10 bytes, FONT0_ID cell 20x40 (V-XL), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 8 chars |
| `0x1307` | run_footer | Icon Display | 12 | 432 | 296 | 24 | library 38, opaque; 0=hint; 1=silenced |

### Page 7 - Critical Alarm (doc page 0x0013, picture `7.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x1308` | alarm_header_flash | Icon Display | 0 | 0 | 320 | 48 | library 36, opaque; 0=bright; 1=dim |
| `0x1180` | alarm_param | Text Display | 24 | 68 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#FDE047` = RGB565 `FF08`, max 22 chars |
| `0x1190` | alarm_temp | Text Display | 68 | 104 | 168 | 56 | 8 bytes, FONT0_ID cell 28x56 (V-HERO), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 6 chars |
| `0x11A0` | alarm_limit | Text Display | 164 | 184 | 72 | 24 | 8 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#FCA5A5` = RGB565 `FD34`, max 6 chars |
| `0x1170` | alarm_rate | Text Display | 96 | 216 | 140 | 40 | 10 bytes, FONT0_ID cell 20x40 (V-XL), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 7 chars |
| `0x1309` | mute_button | Icon Display | 6 | 406 | 308 | 68 | library 37, opaque; 0=SILENCE (focus); 1=SILENCED (disabled); 2=SILENCE (normal) |
| `0x3040` | touch: silence siren | Return Key Code (optional) | 12 | 412 | 296 | 56 | returns `0001` - only on a touch variant |

### Page 8 - Batch Completed (doc page 0x0014, picture `8.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x2020` | lab_name | Text Display | 12 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x2000` | reactor_title | Text Display | 168 | 14 | 140 | 20 | 16 bytes, FONT0_ID cell 10x20 (V-S), align r, colour `#FFFFFF` = RGB565 `FFFF`, max 14 chars |
| `0x3000` | analyst_name | Text Display | 24 | 60 | 272 | 32 | 20 bytes, FONT0_ID cell 16x32 (V-L), align l, colour `#00F0FF` = RGB565 `079F`, max 17 chars |
| `0x3020` | process_name | Text Display | 24 | 96 | 264 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 22 chars |
| `0x3100` | total_duration | Text Display | 166 | 204 | 96 | 24 | 10 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F4F7FC` = RGB565 `F7BF`, max 8 chars |
| `0x3110` | final_temp | Text Display | 166 | 256 | 96 | 24 | 10 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F4F7FC` = RGB565 `F7BF`, max 8 chars |
| `0x3120` | samples_logged | Text Display | 166 | 308 | 96 | 24 | 10 bytes, FONT0_ID cell 12x24 (V-M), align r, colour `#F4F7FC` = RGB565 `F7BF`, max 8 chars |
| `0x130A` | audit_state | Icon Display | 24 | 344 | 272 | 24 | library 39, opaque; 0=saving; 1=stored |
| `0x3050` | touch: release | Return Key Code (optional) | 12 | 412 | 296 | 56 | returns `0001` - only on a touch variant |

### Page 9 - Diagnostics (doc page 0x0020, picture `9.bmp`)
| VP | Name | Widget | x | y | w | h | Settings |
|---|---|---|---|---|---|---|---|
| `0x1320` | diag_row_0 | Icon Display | 8 | 52 | 288 | 68 | library 45, opaque; 0=normal; 1=focus |
| `0x1325` | diag_scroll | Icon Display | 300 | 56 | 6 | 336 | library 46, opaque; 0=rows 1-5; 1=rows 2-6; 2=rows 3-7 |
| `0x3300` | diag_caption_0 | Text Display | 44 | 64 | 80 | 20 | 10 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 8 chars |
| `0x1310` | diag_dot_0 | Icon Display | 24 | 68 | 12 | 12 | library 35, opaque; 0=good; 1=suspect; 2=bad; 3=off |
| `0x3290` | diag_value_0 | Text Display | 24 | 86 | 252 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 21 chars |
| `0x1321` | diag_row_1 | Icon Display | 8 | 120 | 288 | 68 | library 45, opaque; 0=normal; 1=focus |
| `0x3310` | diag_caption_1 | Text Display | 44 | 132 | 80 | 20 | 10 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 8 chars |
| `0x1311` | diag_dot_1 | Icon Display | 24 | 136 | 12 | 12 | library 35, opaque; 0=good; 1=suspect; 2=bad; 3=off |
| `0x32A0` | diag_value_1 | Text Display | 24 | 154 | 252 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 21 chars |
| `0x1322` | diag_row_2 | Icon Display | 8 | 188 | 288 | 68 | library 45, opaque; 0=normal; 1=focus |
| `0x3320` | diag_caption_2 | Text Display | 44 | 200 | 80 | 20 | 10 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 8 chars |
| `0x1312` | diag_dot_2 | Icon Display | 24 | 204 | 12 | 12 | library 35, opaque; 0=good; 1=suspect; 2=bad; 3=off |
| `0x32B0` | diag_value_2 | Text Display | 24 | 222 | 252 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 21 chars |
| `0x1323` | diag_row_3 | Icon Display | 8 | 256 | 288 | 68 | library 45, opaque; 0=normal; 1=focus |
| `0x3330` | diag_caption_3 | Text Display | 44 | 268 | 80 | 20 | 10 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 8 chars |
| `0x1313` | diag_dot_3 | Icon Display | 24 | 272 | 12 | 12 | library 35, opaque; 0=good; 1=suspect; 2=bad; 3=off |
| `0x32C0` | diag_value_3 | Text Display | 24 | 290 | 252 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 21 chars |
| `0x1324` | diag_row_4 | Icon Display | 8 | 324 | 288 | 68 | library 45, opaque; 0=normal; 1=focus |
| `0x3340` | diag_caption_4 | Text Display | 44 | 336 | 80 | 20 | 10 bytes, FONT0_ID cell 10x20 (V-S), align l, colour `#8196BC` = RGB565 `84B7`, max 8 chars |
| `0x1314` | diag_dot_4 | Icon Display | 24 | 340 | 12 | 12 | library 35, opaque; 0=good; 1=suspect; 2=bad; 3=off |
| `0x32D0` | diag_value_4 | Text Display | 24 | 358 | 252 | 24 | 24 bytes, FONT0_ID cell 12x24 (V-M), align l, colour `#F4F7FC` = RGB565 `F7BF`, max 21 chars |
| `0x1334` | btn_return | Icon Display | 6 | 406 | 308 | 68 | library 44, opaque; 0=normal; 1=focus; 2=disabled |
| `0x3060` | touch: return | Return Key Code (optional) | 12 | 412 | 296 | 56 | returns `0001` - only on a touch variant |

### Text-box limits and the analyst-name rule
| VP | Box (chars x cell) | Max chars | Bytes | Rule if longer |
|---|---|---|---|---|
| `0x1060` fw_version | 16 x 10 = 160 px, h 20 | 16 | 18 | truncate (firmware) |
| `0x1100` temp_value | 6 x 28 = 168 px, h 56 | 6 | 8 | truncate (firmware) |
| `0x1130` rpm_value | 6 x 20 = 120 px, h 40 | 6 | 8 | truncate (firmware) |
| `0x1140` torque_value | 6 x 20 = 120 px, h 40 | 6 | 8 | truncate (firmware) |
| `0x1170` alarm_rate | 7 x 20 = 140 px, h 40 | 7 | 10 | truncate (firmware) |
| `0x1180` alarm_param | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x1190` alarm_temp | 6 x 28 = 168 px, h 56 | 6 | 8 | truncate (firmware) |
| `0x11A0` alarm_limit | 6 x 12 = 72 px, h 24 | 6 | 8 | truncate (firmware) |
| `0x11C0` duration | 8 x 20 = 160 px, h 40 | 8 | 10 | truncate (firmware) |
| `0x2000` reactor_title | 14 x 10 = 140 px, h 20 | 14 | 16 | truncate (firmware) |
| `0x2020` lab_name | 14 x 10 = 140 px, h 20 | 14 | 16 | truncate (firmware) |
| `0x2040` clock | 5 x 10 = 50 px, h 20 | 5 | 8 | truncate (firmware) |
| `0x2050` device_uuid | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x3000` analyst_name | 17 x 16 = 272 px, h 32 | 17 | 20 | "First L." then first name cut to 17 chars |
| `0x3020` process_name | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x3080` max_temp | 5 x 12 = 60 px, h 24 | 5 | 8 | truncate (firmware) |
| `0x3090` max_speed | 5 x 12 = 60 px, h 24 | 5 | 8 | truncate (firmware) |
| `0x30A0` max_roc | 5 x 12 = 60 px, h 24 | 5 | 8 | truncate (firmware) |
| `0x3100` total_duration | 8 x 12 = 96 px, h 24 | 8 | 10 | truncate (firmware) |
| `0x3110` final_temp | 8 x 12 = 96 px, h 24 | 8 | 10 | truncate (firmware) |
| `0x3120` samples_logged | 8 x 12 = 96 px, h 24 | 8 | 10 | truncate (firmware) |
| `0x3210` ip_address | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x3220` mqtt_broker | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x3280` mac_address | 22 x 12 = 264 px, h 24 | 22 | 24 | truncate (firmware) |
| `0x3290` diag_value_0 | 21 x 12 = 252 px, h 24 | 21 | 24 | truncate (firmware) |
| `0x32A0` diag_value_1 | 21 x 12 = 252 px, h 24 | 21 | 24 | truncate (firmware) |
| `0x32B0` diag_value_2 | 21 x 12 = 252 px, h 24 | 21 | 24 | truncate (firmware) |
| `0x32C0` diag_value_3 | 21 x 12 = 252 px, h 24 | 21 | 24 | truncate (firmware) |
| `0x32D0` diag_value_4 | 21 x 12 = 252 px, h 24 | 21 | 24 | truncate (firmware) |
| `0x3300` diag_caption_0 | 8 x 10 = 80 px, h 20 | 8 | 10 | truncate (firmware) |
| `0x3310` diag_caption_1 | 8 x 10 = 80 px, h 20 | 8 | 10 | truncate (firmware) |
| `0x3320` diag_caption_2 | 8 x 10 = 80 px, h 20 | 8 | 10 | truncate (firmware) |
| `0x3330` diag_caption_3 | 8 x 10 = 80 px, h 20 | 8 | 10 | truncate (firmware) |
| `0x3340` diag_caption_4 | 8 x 10 = 80 px, h 20 | 8 | 10 | truncate (firmware) |

Analyst name (16x32 box, **17 characters**): show the full name if it is 17 characters or fewer; otherwise **"First L."** (first name + initial of the last name + full stop); if that still exceeds 17, cut the first name to 17 characters. Reference code is in section 3 of `06_firmware_change_list.md`.

## 9. Generate and flash
1. **File -> Save**, then **File -> Generate** (rewrites `13TouchFile.bin`, `14ShowFile.bin`, `22_Config.bin`).
2. DWIN_SET must contain: the three BINs, `32.ICL`, `33..46.ICL`, `0_DWIN_ASC.HZK`, the `T5LCFG*.CFG`, the DWIN OS file. **No loose BMPs.**
3. Copy the whole DWIN_SET to the SD-card root, power off, insert the card, power on, wait for the update message, power off, remove the card, power on.
4. Never hand-edit `22_Config.bin`; Generate overwrites it.

## 10. Bench test with no ESP32
USB-TTL (TX->display RX, RX->display TX, common ground), 115200 8N1, hex mode. Walk every page with `05_serial_test_frames.txt`: page switch, every variable, every icon value, the diagnostics state sequence, alarm header 0/1 each second. Pass: picture matches `04_preview...`, text aligned and cleared, no clipping, no garbage.

## 11. Troubleshooting
| Symptom | Likely cause / fix |
|---|---|
| Old picture still showing | Old ICL on the card: regenerate ICL **and** 13/14/22, wipe DWIN_SET on the card, copy again. |
| Black/white screen | Missing/bad `14ShowFile.bin` or ICL not in DWIN_SET. |
| Wrong picture on a page | Image numbering off (0,1,10,2): fix order in the ICL tool. |
| Text missing | Font file missing, wrong FONT0_ID, or non-ASCII byte sent. |
| Text clipped / blurred | Box != chars x cell, string longer than bytes, wrong encoding (section 7). |
| Old text remains | End marker 0xFFFF off. |
| Focus ring leaves a ghost | Icon variable not opaque, or its ICL is stale. |
| Buzzer chirps | CFG buzzer not disabled, or firmware wrote the buzzer register. |
| Serial dead | Baud mismatch, TX/RX swapped, 5 V on a 3.3 V line, or changed DWIN OS file. |
| Page will not switch | Frame needs `5A 01` before the 2-byte page number. |

## 12. Open items for the owner
Exact suffix (N/TR/TC) and connector/UART level; colour depth (24 vs 18-bit) and active area; font cell list; ICL range up to 46; 0xFFFF option name; buzzer-disable option; DWIN OS file; connectivity pill placement; logo file.
