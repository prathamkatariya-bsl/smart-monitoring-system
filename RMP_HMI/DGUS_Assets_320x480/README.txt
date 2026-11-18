DGUS_Assets_v3_320x480 - Borosil RMP DWIN HMI v3.0 (DMG48320C035_03W, 320x480, keypad-only)
Start with GUIDE_DGUS_V7651_first_timer.md. Layout source of truth: tools/spec3.py (Figma frames were generated from it).
01_backgrounds_*  static pages 0-9 (24-bit 320x480) | 02_icon_libraries  ICL 33-46 | 03_placement_map | 04_preview_with_sample_values
VP_map.csv | 05_serial_test_frames.txt | 06_firmware_change_list.md | 07_qa_checklist.md | tools/
Regenerate: cd tools && python3 spec3.py && python3 render3.py && python3 export3.py && python3 docs3.py (set FD font path in spec3.py).
