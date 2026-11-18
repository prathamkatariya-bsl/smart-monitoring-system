# 07 - QA checklist
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
