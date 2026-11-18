import csv, shutil, os
import spec3 as SP, export3 as EX
O = EX.O; rows = EX.rows; C = SP.C
def fit_name(full, n=17):
    full = ' '.join(full.split())
    if len(full) <= n: return full
    p = full.split(); short = f'{p[0]} {p[-1][0]}.' if len(p) > 1 else p[0]
    return short if len(short) <= n else p[0][:n]
assert fit_name('Deepa Nair') == 'Deepa Nair' and len(fit_name('Anandakrishnan Kumar')) <= 17 and all(len(fit_name(n)) <= 17 for n in ('Venkatasubramanian Iyer', 'Priyadarshini Subramaniam', 'A B C D E F G H I J K L'))
def tbl_for(pg):
    out = ['| VP | Name | Widget | x | y | w | h | Settings |', '|---|---|---|---|---|---|---|---|']; seen = set()
    for r in sorted([r for r in rows if r['page'] == pg], key=lambda r: (r['y'], r['x'], r['vp'])):
        k = (r['vp'], r.get('val'))
        if k in seen: continue
        seen.add(k); t = r['t']; vp = f'`0x{r["vp"]:04X}`'
        if t == 'slot': out.append(f"| {vp} | {r['name']} | Text Display | {r['x']} | {r['y']} | {r['w']} | {r['h']} | {r['bytes']} bytes, FONT0_ID cell {r['cell']}x{r['cell']*2} ({SP.DS and {10:'V-S',12:'V-M',16:'V-L',20:'V-XL',28:'V-HERO'}[r['cell']]}), align {r['al']}, colour `{r['c']}` = RGB565 `{SP.rgb565(r['c'])}`, max {r['chars']} chars |")
        elif t == 'islot': L = SP.LIBS[r['lib']]; out.append(f"| {vp} | {r['name']} | Icon Display | {r['x']} | {r['y']} | {L['w']} | {L['h']} | library {r['lib']}, opaque; " + '; '.join(f'{i}={s}' for i, s in enumerate(L['states'])) + ' |')
        elif t == 'pslot': out.append(f"| {vp} | {r['name']} | Progress Bar | {r['x']} | {r['y']} | {r['w']} | {r['h']} | 0-100, fill `{r['fill']}` |")
        else: out.append(f"| {vp} | touch: {r['name']} | Return Key Code (optional) | {r['x']} | {r['y']} | {r['w']} | {r['h']} | returns `{r['val']:04X}` - only on a touch variant |")
    return '\n'.join(out)
PG = SP.PAGES
LIBTAB = ['| Lib (ICL file) | Name | Image size | VP | Value -> image | Used on page |', '|---|---|---|---|---|---|']
usedon = {}
for r in rows:
    if r['t'] == 'islot': usedon.setdefault(r['lib'], set()).add(r['page'])
for lib, L in SP.LIBS.items():
    vp = ', '.join(sorted({f"0x{r['vp']:04X}" for r in rows if r['t'] == 'islot' and r['lib'] == lib})) or '0x2018 (reserved)'
    LIBTAB.append(f"| {lib}.ICL | {L['name']} | {L['w']}x{L['h']} | {vp} | " + '; '.join(f'{i}={s}' for i, s in enumerate(L['states'])) + f" | {','.join(map(str, sorted(usedon.get(lib, [])))) or 'none (see open questions)'} |")
LIBTAB = '\n'.join(LIBTAB)
BOX = ['| VP | Box (chars x cell) | Max chars | Bytes | Rule if longer |', '|---|---|---|---|---|']
seenb = set()
for r in sorted(rows, key=lambda r: r['vp']):
    if r['t'] == 'slot' and r['vp'] not in seenb:
        seenb.add(r['vp']); rule = '"First L." then first name cut to 17 chars' if r['vp'] == 0x3000 else 'truncate (firmware)'
        BOX.append(f"| `0x{r['vp']:04X}` {r['name']} | {r['chars']} x {r['cell']} = {r['w']} px, h {r['h']} | {r['chars']} | {r['bytes']} | {rule} |")
BOX = '\n'.join(BOX)
mapping = ', '.join(f"`{d}`->{p}" for p, (fn, d, t) in PG.items())

GUIDE = f"""# Borosil RMP - DWIN DGUS HMI v3.0: first-timer build guide (DMG48320C035_03W, 320 x 480)
Tool: **DGUS V7.651**. Everything here uses the files in this package. Items I could not confirm are tagged **[VERIFY]** - keep DWIN's *T5L_DGUSII Application Development Guide* open as tie-breaker. Menu names are given as I know them from V7.6xx; if a label differs on your build, trust the build and note it.

## 0. What changed versus the 240x320 package (firmware team: apply 1-8)
1. **Resolution is 320 x 480.** Every x/y/w/h, every background and every icon library image was regenerated. Old 240x320 assets cannot be reused.
2. **Page numbers are contiguous 0-9; doc IDs stay firmware constants:** {mapping}. The Idle screen is merged into Assignment (page 1 = UNASSIGNED, page 2 = ASSIGNED).
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
1. DGUS Tool V7.651 (Windows), unzipped to a path without spaces, e.g. `C:\\DWIN\\DGUS`.
2. Fonts: install *JetBrains Mono* (free) so the font tool can see it.
3. SD card 4-16 GB, **FAT32, 4096-byte allocation unit**, empty except `DWIN_SET` [VERIFY in DWIN guide].
4. 5 V supply, USB-TTL adapter at 3.3 V, serial terminal in hex mode (SSCOM / Realterm).
5. Hardware questions: exact order code suffix (**N** none / **TR** resistive / **TC** capacitive - default design assumes N); TF slot location; which UART is wired to the ESP32.

## 3. Create the project
1. DGUS Tool -> **New**, resolution **320 x 480**, folder `C:\\RMP_HMI\\project_320x480`. Save once (creates `DWprj.hmi` and `DWIN_SET`). Keep the whole folder in Git.
2. Copy this package to `C:\\RMP_HMI\\assets`.

## 4. Background library (sector 32)
1. Put `0.bmp ... 9.bmp` in a folder named `32`. Keep the numbers 0-9. If the tool sorts 0,1,2,10 fix the order.
2. **ICL tool** -> choose folder -> quality 100 -> Generate -> `32.ICL` into **DWIN_SET**.
3. The number in an ICL file name is the flash sector; each file needs a unique number. 32 = pictures, **33-46 = icon libraries** [VERIFY that 46 is inside the allowed range in the flash-layout chapter; if the range ends earlier, tell me and I will merge the button libraries].
4. Logo: replace the placeholder wordmark in `0.bmp` (area x 60-260, y 64-150) with your logo, keeping 320x480 / 24-bit.

## 5. Icon libraries (one ICL per folder)
{LIBTAB}

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
"""
for pg, (fn, doc, title) in PG.items():
    GUIDE += f"\n### Page {pg} - {title} (doc page {doc}, picture `{pg}.bmp`)\n" + (tbl_for(pg) if any(r['page'] == pg for r in rows) else '_No variables: fully static page (picture only)._') + '\n'
GUIDE += f"""
### Text-box limits and the analyst-name rule
{BOX}

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
"""
open(f'{O}/GUIDE_DGUS_V7651_first_timer.md', 'w').write(GUIDE)

FW = f"""# 06 - Firmware change list (v3.0, 320x480)
## 1. Page mapping and behaviour
Page switch: `5A A5 07 82 00 84 5A 01 00 <page>`. Mapping: {mapping}. Wait **1-2 s** after power-up (poll with `5A A5 04 83 00 14 01`) before writing. Heartbeat is optional (none drawn).
| Screen (page) | Entry | UP / DOWN | SELECT | MODE |
|---|---|---|---|---|
| 0 Boot | power-up | - | - | - |
| 1 Assignment UNASSIGNED | no assignment | - (buttons disabled) | - | hold 3 s Diagnostics |
| 2 Assignment ASSIGNED | assignment received | focus ACCEPT <-> REJECT (default ACCEPT, no wrap) | ACCEPT -> page 5 ; REJECT -> reject event, page 1 | back one level / hold 3 s Diagnostics |
| 3 Network Setup | no Wi-Fi credentials | - | - | hold 3 s Diagnostics |
| 4 Device Not Claimed | not bound | - | - | hold 3 s Diagnostics |
| 5 Pre-Start | accepted | focus START <-> CANCEL (default START) | START -> page 6 ; CANCEL -> page 2 | = CANCEL |
| 6 Running | started | - | short press = silence alerts (0x1307=1) | hold 3 s Diagnostics |
| 7 Critical Alarm | alarm | - | SILENCE (mutes the ESP32 siren; 0x1309=1) | - |
| 8 Batch Completed | completed | - | RELEASE VESSEL TO IDLE -> page 1 | - |
| 9 Diagnostics | MODE hold 3 s | UP/DOWN move focus row 1..7 then RETURN; window scrolls (no wrap) | on RETURN -> previous screen | back |
## 2. VP and icon changes
Use `VP_map.csv` (61 variables, overlap-free). Retired v2.0 addresses are listed there and stay reserved. New: button state icons `0x1330-0x1334` (0 normal, 1 focus, 2 disabled), diagnostics slots (`0x3290+0x10k` values, `0x3300+0x10k` captions, `0x1310+k` dots, `0x1320+k` row state, `0x1325` scroll thumb 0..2). `0x1309` values: 0 SILENCE (focus), 1 SILENCED (disabled), 2 SILENCE (normal). On every page entry write all icon variables of that page (the picture shows the normal state until you do). Toggle `0x1308` 0/1 at 1 Hz during an alarm.
## 3. Name rule (analyst_name 0x3000: 16x32 cell, 17 characters)
```c
// n = 17. Returns display string.
void fit_name(const char *full, char *out) {{            // out >= 18 bytes
  if (strlen(full) <= 17) {{ strcpy(out, full); return; }}
  // first token = first name, last token = last name
  char first[40], last[40]; split_first_last(full, first, last);
  if (last[0] && strlen(first) + 3 <= 17) {{ sprintf(out, "%s %c.", first, last[0]); return; }}   // "Priyadarshini S."
  strncpy(out, first, 17); out[17] = 0;                                                        // first name cut to box width
}}
```
Other boxes: truncate to the max chars in the table (guide section 8). ASCII only; send `Raw 35.6 C`-style strings with units baked in the picture. Text writes end with `FF FF` when shorter than the variable.
## 4. Alarm / buzzer
Configure the DWIN buzzer **off**; never write the buzzer register. Silence mutes the ESP32 siren only; the alarm header keeps flashing and the Silence button shows SIREN SILENCED (value 1).
## 5. Touch
Return-key VPs (`0x3010, 0x3030, 0x3040, 0x3050, 0x3060`) are defined but only fire on touch variants; the four keys are authoritative.
"""
open(f'{O}/06_firmware_change_list.md', 'w').write(FW)
QA = """# 07 - QA checklist
## A. Script checks (run `python3 spec3.py && python3 export3.py`)
- [ ] spec3: no text < 14 px, no text overflow (PIL-measured), WCAG >= 4.5:1 for every text/background pair except disabled, nothing outside 320x480, every dynamic box = chars x cell
- [ ] export3: no VP address overlap (text = bytes/2 words, icon/bar/touch = 1 word), same VP = same length on every page, no colliding text boxes per page
- [ ] export3: every serial frame's length byte equals its payload length
- [ ] every `01_backgrounds_bmp/N.bmp` is 24-bit 320x480
## B. On-device (per page 0-9, with `05_serial_test_frames.txt`)
- [ ] picture matches `04_preview` (no stale ICL), no loose BMPs on the card
- [ ] each text aligns in its box, clears when shorter (0xFFFF), longest samples fit, no garbage
- [ ] analyst-name rule with 10 / 17 / 18 / 25 character names
- [ ] every icon value shows the right image, opaque, no ghost edges; focus ring + halo identical in all button states
- [ ] page 2/5: UP/DOWN move focus, default focus on primary, no wrap
- [ ] page 9: window 1-5 -> 3-7, focus first/last row, RETURN, scroll thumb 0/1/2
- [ ] alarm header toggles at 1 Hz; Silence changes 0x1309 to 1; DWIN buzzer silent in every state
- [ ] power-up: page 0 then correct page after 1-2 s; read-page frame returns current page
- [ ] legibility at arm's length; compare 8bit vs GBK encoding and the no-aliasing text variable
"""
open(f'{O}/07_qa_checklist.md', 'w').write(QA)
README = """DGUS_Assets_v3_320x480 - Borosil RMP DWIN HMI v3.0 (DMG48320C035_03W, 320x480, keypad-only)
Start with GUIDE_DGUS_V7651_first_timer.md. Layout source of truth: tools/spec3.py (Figma frames were generated from it).
01_backgrounds_*  static pages 0-9 (24-bit 320x480) | 02_icon_libraries  ICL 33-46 | 03_placement_map | 04_preview_with_sample_values
VP_map.csv | 05_serial_test_frames.txt | 06_firmware_change_list.md | 07_qa_checklist.md | tools/
Regenerate: cd tools && python3 spec3.py && python3 render3.py && python3 export3.py && python3 docs3.py (set FD font path in spec3.py).
"""
open(f'{O}/README.txt', 'w').write(README)
shutil.copy('/home/claude/pack/UPLOAD_PACK_320x480_handoff/03_guides/GUIDE_DMG48320C035_03W_implementation.md', f'{O}/GUIDE_DMG48320C035_03W_implementation.md')
os.makedirs(f'{O}/tools', exist_ok=True)
for fn in ('spec3.py', 'render3.py', 'export3.py', 'docs3.py'): shutil.copy(f'/home/claude/build/{fn}', f'{O}/tools/{fn}')
print('docs written', fit_name('Priyadarshini Subramaniam'), '|', fit_name('Anandakrishnan Kumar'))
