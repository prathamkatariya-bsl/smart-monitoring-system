# 06 - Firmware change list (v3.0, 320x480)
## 1. Page mapping and behaviour
Page switch: `5A A5 07 82 00 84 5A 01 00 <page>`. Mapping: `0x0000`->0, `0x0001`->1, `0x0010`->2, `0x0002`->3, `0x0003`->4, `0x0011`->5, `0x0012`->6, `0x0013`->7, `0x0014`->8, `0x0020`->9. Wait **1-2 s** after power-up (poll with `5A A5 04 83 00 14 01`) before writing. Heartbeat is optional (none drawn).
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
void fit_name(const char *full, char *out) {            // out >= 18 bytes
  if (strlen(full) <= 17) { strcpy(out, full); return; }
  // first token = first name, last token = last name
  char first[40], last[40]; split_first_last(full, first, last);
  if (last[0] && strlen(first) + 3 <= 17) { sprintf(out, "%s %c.", first, last[0]); return; }   // "Priyadarshini S."
  strncpy(out, first, 17); out[17] = 0;                                                        // first name cut to box width
}
```
Other boxes: truncate to the max chars in the table (guide section 8). ASCII only; send `Raw 35.6 C`-style strings with units baked in the picture. Text writes end with `FF FF` when shorter than the variable.
## 4. Alarm / buzzer
Configure the DWIN buzzer **off**; never write the buzzer register. Silence mutes the ESP32 siren only; the alarm header keeps flashing and the Silence button shows SIREN SILENCED (value 1).
## 5. Touch
Return-key VPs (`0x3010, 0x3030, 0x3040, 0x3050, 0x3060`) are defined but only fire on touch variants; the four keys are authoritative.
