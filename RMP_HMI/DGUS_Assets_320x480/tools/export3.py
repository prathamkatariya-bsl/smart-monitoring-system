import csv, os, json, shutil
from pathlib import Path
import spec3 as SP, render3 as RN
ROOT = Path(__file__).resolve().parents[1]
O = os.environ.get('DGUS_EXPORT_DIR', str(ROOT / 'generated'))
Path(O).mkdir(parents=True, exist_ok=True)
Path(O, 'previews').mkdir(parents=True, exist_ok=True)
Path(O, 'libraries').mkdir(parents=True, exist_ok=True)
Path(O, 'maps').mkdir(parents=True, exist_ok=True)
C = SP.C
# ---- collect per page (export state) ----
PAGE_ELS = {pg: SP.build(pg, RN.EXPORT_STATE[pg]) for pg in SP.PAGES}
for pg, st in [(2, {'focus': 'accept'}), (5, {'focus': 'start'})]: PAGE_ELS[pg] = SP.build(pg, st)   # dynamic defaults (initial icon values: focus on primary)
rows = []   # one per (vp, page, val)
for pg, els in PAGE_ELS.items():
    for e in els:
        if e['t'] in ('slot', 'islot', 'pslot', 'touch'): rows.append(dict(e, page=pg))
def words(e): return e['bytes'] // 2 if e['t'] == 'slot' else 1
# ---- checks ----
issues = []
byvp = {}
for r in rows: byvp.setdefault(r['vp'], []).append(r)
for vp, rs in byvp.items():
    kinds = {(r['t'], r.get('bytes'), r.get('lib')) for r in rs}
    if len(kinds) > 1: issues.append(f'0x{vp:04X} inconsistent type/length/lib across pages: {kinds}')
spans = sorted((vp, vp + words(rs[0]) - 1, rs[0]['name']) for vp, rs in byvp.items())
for a, b in zip(spans, spans[1:]):
    if a[1] >= b[0]: issues.append(f'OVERLAP {a} vs {b}')
for r in rows:
    if r['t'] == 'slot':
        if r['w'] != r['chars'] * r['cell'] or r['h'] != 2 * r['cell']: issues.append('BOX != chars x cell ' + r['name'])
        if len(r['sample']) > r['chars'] or len(r['sample']) + 2 > r['bytes'] + 0 and len(r['sample']) != r['bytes']: issues.append('SAMPLE > size ' + r['name'])
    if r['t'] == 'islot':
        L = SP.LIBS[r['lib']]
        if r['x'] < 0 or r['y'] < 0 or r['x'] + L['w'] > 320 or r['y'] + L['h'] > 480: issues.append('ICON out of frame ' + r['name'])
    if r['x'] < 0 or r['y'] < 0: issues.append('neg coord ' + r['name'])
# same-page overlap of boxes (text/icon) - visual collisions
def box(r):
    if r['t'] == 'islot': L = SP.LIBS[r['lib']]; return (r['x'], r['y'], L['w'], L['h'])
    return (r['x'], r['y'], r['w'], r['h'])
for pg in SP.PAGES:
    items = [r for r in rows if r['page'] == pg and r['t'] in ('slot',)]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = box(items[i]), box(items[j])
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]: issues.append(f'page {pg}: text boxes collide {items[i]["name"]} / {items[j]["name"]}')
print('VP/box checks:', issues or 'PASS', '| unique VPs', len(byvp), '| rows', len(rows))

RETIRED = [(0x1110, 'temp_raw'), (0x1120, 'cal_tag'), (0x1150, 'rpm_set'), (0x1160, 'fault_code'), (0x11B0, 'trend_rate'), (0x11D0, 'batch_tag'), (0x1305, 'torque_load_bar'), (0x3070, 'scope_tag'),
           (0x1300, 'temp_quality_dot (Running now uses pill 0x1301; dot lib 35 used by diagnostics slots)'), (0x3200, 'ssid (row-bound; replaced by slot 0x3290..)'), (0x3230, 'mtls_status (replaced by slots)'), (0x3240, 'ntp_status (row removed in v2.1)'),
           (0x3250, 'rtd_status (replaced by slots)'), (0x3260, 'rs232_status (replaced by slots)'), (0x3270, 'flash_status (row removed in v2.1)'), (0x1315, 'dot_rtd (row-bound)'), (0x1316, 'dot_rs232 (row-bound)'), (0x1317, 'dot_flash (row-bound)'), (0x1318, 'dot_mac (row-bound)'),
           (0x2018, 'conn_pill (lib 33 exported; not placed on any v2.1 screen - owner decision pending)'), (0x2010, 'reserved since v2.0')]
WIDGET = {'slot': 'Text Display', 'islot': 'Icon Display (variable icon)', 'pslot': 'Progress Bar Display', 'touch': 'Touch: Return Key Code (optional)'}
VCELL = {10: 'V-S', 12: 'V-M', 16: 'V-L', 20: 'V-XL', 28: 'V-HERO'}
with open(f'{O}/VP_map.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['vp_hex', 'name', 'widget', 'page', 'x', 'y', 'w', 'h', 'bytes', 'cell_wxh', 'style', 'align', 'color', 'rgb565', 'max_chars', 'icon_lib', 'values_or_notes', 'direction', 'rate', 'status'])
    seen = set()
    for r in sorted(rows, key=lambda r: (r['vp'], r['page'], str(r.get('val')))):
        k = (r['vp'], r['page'], r.get('val'))
        if k in seen: continue
        seen.add(k); t = r['t']; vp = f'0x{r["vp"]:04X}'
        if t == 'slot': w.writerow([vp, r['name'], WIDGET[t], r['page'], r['x'], r['y'], r['w'], r['h'], r['bytes'], f"{r['cell']}x{r['cell']*2}", VCELL[r['cell']], r['al'], r['c'], SP.rgb565(r['c']), r['chars'], '', r['sample'], 'ESP32->DWIN', r['rate'], 'active'])
        elif t == 'islot':
            L = SP.LIBS[r['lib']]; w.writerow([vp, r['name'], WIDGET[t], r['page'], r['x'], r['y'], L['w'], L['h'], 2, '', '', '', '', '', '', r['lib'], '; '.join(f'{i}={s}' for i, s in enumerate(L['states'])), 'ESP32->DWIN', r['rate'], 'active'])
        elif t == 'pslot': w.writerow([vp, r['name'], WIDGET[t], r['page'], r['x'], r['y'], r['w'], r['h'], 2, '', '', '', r['fill'], SP.rgb565(r['fill']), '', '', '0..100 (%)', 'ESP32->DWIN', r['rate'], 'active'])
        else: w.writerow([vp, f"{r['name']} (value {r['val']})", WIDGET[t], r['page'], r['x'], r['y'], r['w'], r['h'], 2, '', '', '', '', '', '', '', r['key'], 'DWIN->ESP32', 'on press', 'optional (no-touch module: never fires)'])
    for vp, why in RETIRED: w.writerow([f'0x{vp:04X}', why, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'RETIRED - address reserved, do not reuse'])
# ---- serial frames ----
def fr(addr, payload, cmd=0x82):
    b = bytes([cmd, addr >> 8, addr & 255]) + payload; return ' '.join(f'{x:02X}' for x in bytes([0x5A, 0xA5, len(b)]) + b), b
FR_CHECK = []
def line(label, addr, payload):
    s, b = fr(addr, payload); FR_CHECK.append((len(b), int(s.split()[2], 16))); return f'{label:<24}: {s}'
def txt(e, s=None):
    s = (s if s is not None else e['sample']).encode('ascii'); assert len(s) <= e['chars']
    return s + (b'\xff\xff' if len(s) + 2 <= e['bytes'] else b'')[:e['bytes'] - len(s)] if len(s) < e['bytes'] else s
L_ = ['# Serial test frames - hex mode, 115200 8N1. Paste lines as-is into SSCOM/Realterm (generated by export3.py; length byte checked by script).', '# Text writes end with FF FF when shorter than the variable; Text Display must have end marker 0xFFFF enabled.',
      '# Icon / bar writes: 2-byte value. Page switch: 5A A5 07 82 00 84 5A 01 00 <page>.', '']
for pg, (fn, doc, title) in SP.PAGES.items():
    L_.append(f'## Page {pg} - {title}  (firmware constant: doc page {doc})'); L_.append(line('Go to page', 0x0084, bytes([0x5A, 0x01, 0, pg])))
    seen = set()
    for e in PAGE_ELS[pg]:
        if e['vp'] if 'vp' in e else None:
            pass
        if e['t'] == 'slot' and e['vp'] not in seen: seen.add(e['vp']); L_.append(line(e['name'], e['vp'], txt(e)))
        elif e['t'] == 'islot' and e['vp'] not in seen:
            seen.add(e['vp']); L_.append(line(e['name'], e['vp'], bytes([0, e['sample']])) + '   (' + '; '.join(f'{i}={s}' for i, s in enumerate(SP.LIBS[e['lib']]['states'])) + ')')
        elif e['t'] == 'pslot' and e['vp'] not in seen: seen.add(e['vp']); L_.append(line(e['name'], e['vp'], bytes([0, e['val']])))
    L_.append('')
# state sequences
L_ += ['## State sequences (focus / scroll) - what firmware writes on each key press', '# Page 2 (Assignment): focus ACCEPT -> 0x1330=1,0x1331=0 ; DOWN -> 0x1330=0,0x1331=1']
for a, b in ((1, 0), (0, 1)): L_.append(line(f'btn_accept={a}', 0x1330, bytes([0, a]))); L_.append(line(f'btn_reject={b}', 0x1331, bytes([0, b])))
L_.append('# Page 5 (Pre-Start): focus START / CANCEL')
for a, b in ((1, 0), (0, 1)): L_.append(line(f'btn_start={a}', 0x1332, bytes([0, a]))); L_.append(line(f'btn_cancel={b}', 0x1333, bytes([0, b])))
L_.append('# Page 9 (Diagnostics): window 3-7 (rows MQTT..MAC), thumb value 2, focus slot 4 (MAC)')
ws = 3
for k in range(5):
    cap, val = SP.DIAG[ws - 1 + k]; cs = [e for e in PAGE_ELS[9] if e['t'] == 'slot' and e['name'] == f'diag_caption_{k}'][0]; vs = [e for e in PAGE_ELS[9] if e['t'] == 'slot' and e['name'] == f'diag_value_{k}'][0]
    L_.append(line(f'caption_{k}={cap}', cs['vp'], txt(cs, cap))); L_.append(line(f'value_{k}={val}', vs['vp'], txt(vs, val))); L_.append(line(f'dot_{k}=good', 0x1310 + k, bytes([0, 0]))); L_.append(line(f'row_{k}={"focus" if k == 4 else "normal"}', 0x1320 + k, bytes([0, 1 if k == 4 else 0])))
L_.append(line('scroll thumb=3-7', 0x1325, bytes([0, 2]))); L_.append(line('btn_return=focus', 0x1334, bytes([0, 1]))); L_.append(line('btn_return=normal', 0x1334, bytes([0, 0])))
L_ += ['', '## Alarm (page 7): flash header 0/1 at 1 Hz; silence', line('alarm header dim', 0x1308, bytes([0, 1])), line('alarm header bright', 0x1308, bytes([0, 0])), line('mute=SILENCED', 0x1309, bytes([0, 1])), line('mute=SILENCE focus', 0x1309, bytes([0, 0])),
       line('run_footer=silenced', 0x1307, bytes([0, 1])), line('audit=saving', 0x130A, bytes([0, 0])), line('audit=stored', 0x130A, bytes([0, 1])), '',
       '## Read current page : 5A A5 04 83 00 14 01   -> reply 5A A5 06 83 00 14 01 <page_hi> <page_lo>', '## Touch / return-key frames (only on a touch variant) DWIN -> ESP32:']
for vp, val, n in ((0x3010, 0, 'accept'), (0x3010, 1, 'reject'), (0x3030, 0, 'start'), (0x3030, 1, 'cancel'), (0x3040, 1, 'silence'), (0x3050, 1, 'release'), (0x3060, 1, 'return')):
    L_.append(f'{n:<9}: 5A A5 06 83 {vp>>8:02X} {vp&255:02X} 01 00 {val:02X}')
L_ += ['', '## Write ACK from display (if enabled): 5A A5 03 82 4F 4B']
assert all(a == b for a, b in FR_CHECK), 'frame length mismatch'
open(f'{O}/05_serial_test_frames.txt', 'w').write('\n'.join(L_)); print('serial frames OK:', len(FR_CHECK), 'length-checked')
json.dump(dict(issues=issues, nvp=len(byvp), nframes=len(FR_CHECK)), open(Path(O) / 'export_report.json', 'w'))
