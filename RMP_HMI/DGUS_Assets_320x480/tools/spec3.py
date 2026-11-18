# Single source of truth - Borosil RMP DWIN HMI v3.0, 320x480 (DMG48320C035_03W). Keypad-only.
# spec3.py -> render3.py (BMP/PNG/previews) -> export3.py (VP map, serial frames) -> figma_json.py (Figma frames)
import math
import os
from pathlib import Path
from PIL import ImageFont
W, H = 320, 480
# Set DGUS_FONT_DIR to the approved Poppins/JBM TTF directory for pixel-identical
# artwork. The repository/system fallback keeps QA scripts reproducible outside
# the original design workstation; it is not a substitute for release fonts.
_FONT_ROOT = Path(os.environ.get('DGUS_FONT_DIR', __file__)).resolve()
if _FONT_ROOT.is_file():
    _FONT_ROOT = _FONT_ROOT.parent.parent / 'fonts'
_FONT_DIRS = [_FONT_ROOT, Path('/usr/share/fonts/truetype/dejavu'), Path('/usr/share/fonts/truetype/liberation2')]
FM = {('P',400):'Poppins-Regular',('P',500):'Poppins-Medium',('P',600):'Poppins-SemiBold',('P',700):'Poppins-Bold',('P',800):'Poppins-ExtraBold',
      ('J',400):'JBM-Regular',('J',500):'JBM-Medium',('J',600):'JBM-Bold',('J',700):'JBM-Bold',('J',800):'JBM-ExtraBold'}
_fc = {}
def font(f, wt, px, S=4):
    k = (f, wt, px, S)
    if k not in _fc:
        preferred = FM[(f, wt)] + '.ttf'
        candidates = [d / preferred for d in _FONT_DIRS]
        # DejaVu Sans is a deterministic fallback for CI/non-design machines.
        candidates += [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if wt >= 600 else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
        for candidate in candidates:
            if candidate.exists():
                _fc[k] = ImageFont.truetype(str(candidate), int(round(px * S)))
                break
        else:
            raise FileNotFoundError(f'No TTF found for {f}/{wt}; set DGUS_FONT_DIR')
    return _fc[k]
def tw(s, f, wt, sz, ls=0):
    return font(f, wt, sz).getlength(s) / 4 + ls * max(len(s) - 1, 0)

def mix(a, b, t):
    a = a.lstrip('#'); b = b.lstrip('#')
    ca = [int(a[i:i+2], 16) for i in (0, 2, 4)]; cb = [int(b[i:i+2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))
def lum(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def contrast(a, b):
    la, lb = lum(a), lum(b); la, lb = max(la, lb), min(la, lb); return (la + 0.05) / (lb + 0.05)
def rgb565(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i+2], 16) for i in (0, 2, 4)]
    return '%04X' % (((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

C = dict(bg='#0A1020', header='#0E1729', surface='#121B30', sunken='#0E1729', border='#273657', border2='#3A4A6E',
         tp='#F4F7FC', ts='#9DB0CF', tm='#8196BC', cyan='#00F0FF', blue='#38BDF8',
         green='#10B981', greenB='#047857', greenBg='#0A291D', amber='#F59E0B', amberHdr='#B45309', amberBg='#3A2A0A',
         red='#EF4444', redD='#DC2626', redBg='#450A0A', redBg2='#1F1010', redLt='#FCA5A5', redLine='#7F1D1D', yellow='#FDE047', yellowLt='#FEF08A',
         indigo='#1D4ED8', royal='#2563EB', slate='#334155', slateTxt='#CBD5E1', dark='#1A0F14',
         disFill='#182036', disTxt='#5B6B8C', white='#FFFFFF')
C['halo'] = mix(C['bg'], '#FFFFFF', 0.28)       # pre-blended focus halo (no runtime alpha)
C['hl'] = mix(C['surface'], '#FFFFFF', 0.10)    # card top highlight

# ---------------- type scale ----------------
ST = {'title': ('P', 700, 18, 28), 'button': ('P', 700, 16, 24), 'label': ('P', 500, 16, 24), 'caption': ('P', 600, 16, 24), 'unit': ('P', 500, 16, 24)}
DS = {'S': (10, 500), 'M': (12, 700), 'L': (16, 800), 'XL': (20, 800), 'HERO': (28, 800)}   # style -> (cell width, JBM weight); cell h = 2w; size = w/0.6
def dpx(style): return DS[style][0] / 0.6

ICONS = {
 'check': '<path d="M20 6 9 17l-5-5"/>', 'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', 'play': '<polygon points="6 3 20 12 6 21 6 3"/>',
 'arrow-left': '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
 'hourglass': '<path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/>',
 'triangle-alert': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
 'flame': '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
 'volume-x': '<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><line x1="22" x2="16" y1="9" y2="15"/><line x1="16" x2="22" y1="9" y2="15"/>',
 'flask': '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
 'circle-check': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
 'wifi': '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
}

# ---------------- element builders ----------------
def R(x, y, w, h, fill=None, stroke=None, sw=1, r=0, name=None, role=None):
    return dict(t='rect', x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, r=r, name=name, role=role)
def T(x, y, w, s, style, c, al='l', name=None, sz=None, wt=None, f=None, lh=None, ls=0, dis=False):
    ff, ww, ss, ll = ST[style] if style else ('P', 600, 16, 24)
    return dict(t='text', x=x, y=y, w=w, s=s, f=f or ff, wt=wt or ww, sz=sz or ss, h=lh or ll, c=c, al=al, ls=ls, name=name or style, dis=dis, style=style)
def I(n, x, y, sz, c, sw=2): return dict(t='icon', n=n, x=x, y=y, sz=sz, c=c, sw=sw)
def bytes_for(chars): return int(math.ceil((chars + 2) / 2.0) * 2)
def SLOT(vp, name, x, y, chars, style, al, c, sample, rate='on change'):
    cw = DS[style][0]
    return dict(t='slot', vp=vp, name=name, x=x, y=y, w=chars * cw, h=cw * 2, chars=chars, cell=cw, style=style, al=al, c=c, sample=sample,
                bytes=bytes_for(chars), wt=DS[style][1], rate=rate)
def ISLOT(vp, name, x, y, lib, sample, rate='on change'): return dict(t='islot', vp=vp, name=name, x=x, y=y, lib=lib, sample=sample, rate=rate)
def PSLOT(vp, name, x, y, w, h, val, fill, track, r=4): return dict(t='pslot', vp=vp, name=name, x=x, y=y, w=w, h=h, val=val, fill=fill, track=track, r=r, rate='on change')
def TOUCH(vp, val, name, x, y, w, h, key): return dict(t='touch', vp=vp, val=val, name=name, x=x, y=y, w=w, h=h, key=key)

def card(x, y, w, h, fill=None, stroke=None, sw=1, r=8, name='card'):
    return [R(x, y, w, h, fill or C['surface'], stroke or C['border'], sw, r, name), R(x + 8, y + 1, w - 16, 1, C['hl'], name='bevel highlight')]

# ---------------- buttons (state: normal / focus / disabled) ----------------
THEME = {  # key -> (fill, stroke, fg, focus fill, focus stroke, focus fg)
 'accept': (C['greenB'], None, '#FFFFFF'), 'start': (C['royal'], None, '#FFFFFF'), 'release': (C['greenB'], None, '#FFFFFF'),
 'return': (C['slate'], None, '#FFFFFF'), 'cancel': (C['slate'], None, C['slateTxt']), 'silence': (C['amber'], None, C['bg']),
 'reject': (C['redD'], C['red'], '#FFFFFF'),
}
def btn(key, x, y, w, h, label, icon, state='normal', r=8):
    fill, stroke, fg = THEME[key]
    if state == 'disabled': fill, stroke, fg = C['disFill'], C['border'], C['disTxt']
    els = []
    if state == 'focus':
        els += [R(x - 6, y - 6, w + 12, h + 12, C['halo'], r=r + 6, name='focus glow (halo)'), R(x - 3, y - 3, w + 6, h + 6, '#FFFFFF', r=r + 3, name='focus ring')]
    els.append(R(x, y, w, h, fill, stroke, 2 if stroke else 1, r, name=f'button - {label} - {state}', role='button'))
    if state != 'disabled':
        els += [R(x + 4, y + 1, w - 8, 1, mix(fill, '#FFFFFF', 0.28), name='bevel highlight'), R(x + 4, y + h - 2, w - 8, 1, mix(fill, '#000000', 0.35), name='bevel shadow')]
    lw = tw(label, 'P', 700, 16); total = lw + (32 if icon else 0); x0 = x + (w - total) / 2
    if icon: els.append(I(icon, round(x0), y + (h - 24) // 2, 24, fg, 2.5)); x0 += 32
    els.append(T(round(x0), y + (h - 24) // 2, math.ceil(lw) + 4, label, 'button', fg, name='label', dis=(state == 'disabled')))
    return els

BTNS = {  # lib -> (key, label, icon, w, h)  (w,h = button; image adds 6 px margin each side)
 40: ('accept', 'ACCEPT ASSIGNMENT', 'check', 296, 56), 41: ('reject', 'REJECT ASSIGNMENT', 'x', 296, 44),
 42: ('start', 'START PROCESS', 'play', 296, 56), 43: ('cancel', 'CANCEL / RETURN', 'x', 296, 44),
 44: ('return', 'RETURN TO MONITORING', 'arrow-left', 296, 56),
}
BTN_VP = {40: 0x1330, 41: 0x1331, 42: 0x1332, 43: 0x1333, 44: 0x1334}

# ---------------- icon libraries ----------------
def pill(txt, fill, fg, w, h, dot=None):
    els = [R(0, 0, w, h, fill, r=h // 2)]
    tx0 = 0
    if dot: els.append(R(10, h // 2 - 4, 8, 8, dot, r=4)); tx0 = 22
    els.append(T(tx0, (h - 24) // 2, w - tx0, txt, 'caption', fg, al='c', name='pill text', lh=24, wt=700))
    return els
def libs():
    L = {}
    L[33] = dict(name='conn_pill', w=104, h=28, bg=C['header'], states=['ONLINE', 'OFFLINE'], imgs=[pill('ONLINE', C['greenB'], '#FFFFFF', 104, 28, '#FFFFFF'), pill('OFFLINE', C['redD'], '#FFFFFF', 104, 28, '#FFFFFF')])
    L[34] = dict(name='quality_pill', w=96, h=28, bg=C['surface'], states=['GOOD', 'SUSPECT', 'BAD'], imgs=[pill('GOOD', C['greenB'], '#FFFFFF', 96, 28), pill('SUSPECT', C['amber'], C['bg'], 96, 28), pill('BAD', C['redD'], '#FFFFFF', 96, 28)])
    L[35] = dict(name='status_dot', w=12, h=12, bg=C['surface'], states=['good', 'suspect', 'bad', 'off'], imgs=[[R(0, 0, 12, 12, c, r=6)] for c in (C['green'], C['amber'], C['red'], C['tm'])])
    L[36] = dict(name='alarm_header', w=320, h=48, bg=C['bg'], states=['bright', 'dim'], imgs=[
        [R(0, 0, 320, 48, C['redD']), I('triangle-alert', 12, 12, 24, '#FFFFFF'), T(48, 10, 224, 'CRITICAL SAFETY ALARM', 'title', '#FFFFFF', name='title'), I('flame', 284, 12, 24, C['yellow'])],
        [R(0, 0, 320, 48, C['redLine']), I('triangle-alert', 12, 12, 24, C['redLt']), T(48, 10, 224, 'CRITICAL SAFETY ALARM', 'title', C['redLt'], name='title'), I('flame', 284, 12, 24, C['redLt'])]])
    L[37] = dict(name='mute_button', w=308, h=68, bg=C['bg'], states=['SILENCE (focus)', 'SILENCED (disabled)', 'SILENCE (normal)'], imgs=[
        [R(0, 0, 308, 68, C['bg'])] + btn('silence', 6, 6, 296, 56, 'SILENCE HARDWARE SIREN', 'volume-x', 'focus'),
        [R(0, 0, 308, 68, C['bg'])] + btn('silence', 6, 6, 296, 56, 'SIREN SILENCED', 'volume-x', 'disabled'),
        [R(0, 0, 308, 68, C['bg'])] + btn('silence', 6, 6, 296, 56, 'SILENCE HARDWARE SIREN', 'volume-x', 'normal')])
    L[38] = dict(name='run_footer_hint', w=296, h=24, bg=C['bg'], states=['hint', 'silenced'], imgs=[
        [T(0, 2, 296, 'Short-press Select to mute alerts', 'unit', C['tm'], name='hint', sz=14, lh=20)],
        [R(0, 0, 296, 24, C['amberBg'], C['amber'], 1, 12), I('volume-x', 10, 4, 16, C['amber']), T(32, 2, 258, 'SIREN SILENCED - monitoring on', 'unit', C['amber'], wt=700, name='hint', sz=14, lh=20)]])
    L[39] = dict(name='audit_state', w=272, h=24, bg=C['surface'], states=['saving', 'stored'], imgs=[
        [I('hourglass', 0, 4, 16, C['amber']), T(24, 2, 248, 'Saving to server...', 'unit', C['amber'], wt=600, sz=14, lh=20)],
        [I('circle-check', 0, 4, 16, C['green']), T(24, 2, 248, 'Signed & stored (TimescaleDB)', 'unit', C['green'], wt=600, sz=14, lh=20)]])
    for lib, (key, label, icon, bw, bh) in BTNS.items():
        L[lib] = dict(name='btn_' + label.split()[0].lower(), w=bw + 12, h=bh + 12, bg=C['bg'], states=['normal', 'focus', 'disabled'],
                      imgs=[[R(0, 0, bw + 12, bh + 12, C['bg'])] + btn(key, 6, 6, bw, bh, label, icon, s) for s in ('normal', 'focus', 'disabled')])
    L[45] = dict(name='diag_row', w=288, h=68, bg=C['bg'], states=['normal', 'focus'], imgs=[
        [R(0, 0, 288, 68, C['bg']), R(4, 4, 280, 60, C['surface'], C['border'], 1, 8), R(12, 5, 264, 1, C['hl'])],
        [R(0, 0, 288, 68, C['bg']), R(0, 0, 288, 68, C['halo'], r=10), R(2, 2, 284, 64, '#FFFFFF', r=8), R(4, 4, 280, 60, C['surface'], C['blue'], 1, 8), R(12, 5, 264, 1, C['hl'])]])
    th = lambda s: [R(0, 0, 6, 336, C['bg']), R(0, 0, 6, 336, C['border'], r=3), R(0, [0, 48, 96][s], 6, 240, C['blue'], r=3)]
    L[46] = dict(name='scroll_thumb', w=6, h=336, bg=C['bg'], states=['rows 1-5', 'rows 2-6', 'rows 3-7'], imgs=[th(0), th(1), th(2)])
    return L
LIBS = libs()
LIB_VP = {33: 0x2018, 34: 0x1301, 35: None, 36: 0x1308, 37: 0x1309, 38: 0x1307, 39: 0x130A, 40: 0x1330, 41: 0x1331, 42: 0x1332, 43: 0x1333, 44: 0x1334, 45: None, 46: 0x1325}

# ---------------- screens ----------------
def hdr_dyn():
    return [R(0, 0, W, 48, C['indigo'], name='header', role='header'), R(0, 47, W, 1, mix(C['indigo'], '#FFFFFF', 0.25), name='header rule'),
            SLOT(0x2020, 'lab_name', 12, 14, 14, 'S', 'l', '#FFFFFF', 'QC Lab 1', 'on change'), SLOT(0x2000, 'reactor_title', 168, 14, 14, 'S', 'r', '#FFFFFF', 'Reactor 25', 'on change')]
def hdr_static(title, fill, icon=None, center=False):
    els = [R(0, 0, W, 48, fill, name='header', role='header'), R(0, 47, W, 1, mix(fill, '#FFFFFF', 0.22), name='header rule')]
    if center: els.append(T(0, 10, W, title, 'title', '#FFFFFF', al='c', name='title'))
    else: els.append(T(12, 10, 264, title, 'title', '#FFFFFF', name='title'))
    if icon: els.append(I(icon, 284, 12, 24, '#FFFFFF'))
    return els
def ctx_card():
    return card(12, 56, 296, 72) + [SLOT(0x3000, 'analyst_name', 24, 60, 17, 'L', 'l', C['cyan'], 'Deepa Nair', 'on assignment'),
                                    SLOT(0x3020, 'process_name', 24, 96, 22, 'M', 'l', C['tp'], 'Synthesis Batch B-42', 'on assignment')]
def row3(y0, pitch, rows, vcol, ucol, vchars=6):
    """label (Label style) | value (V-M, right aligned, box ends at vcol) | unit. rows: (label,vp,name,sample,color,unit)"""
    els = []
    for i, (lab, vp, nm, smp, col, unit) in enumerate(rows):
        y = y0 + i * pitch
        els.append(T(24, y, 150, lab, 'label', C['ts'], name='label - ' + lab))
        els.append(SLOT(vp, nm, vcol - vchars * 12, y, vchars, 'M', 'r', col, smp, 'on assignment' if vp < 0x3100 else 'once'))
        if unit: els.append(T(ucol, y + (2 if len(unit) > 3 else 0), 296 - ucol, unit, 'unit', C['tm'], name='unit', sz=(14 if len(unit) > 3 else None), lh=(20 if len(unit) > 3 else None)))
        if i < len(rows) - 1: els.append(R(24, y + 36 + (pitch - 56) // 2 * 0 + (pitch - 52 if pitch > 56 else 0) // 2, 272, 1, C['border'], name='row rule'))
    return els

DIAG = [('SSID', 'BSL_PUNE'), ('IP', '172.16.50.162'), ('MQTT', '172.16.50.138:18883'), ('mTLS', 'CONNECTED (TLSv1.2)'), ('RTD', 'ACTIVE (430.0 Rref)'), ('RS232', 'HEIDOLPH (9600 8N1)'), ('MAC', 'E8:F6:0A:E3:90:FB')]
ROW_Y = [56 + i * 68 for i in range(5)]

def build(page, state=None, export=False):
    st = state or {}; els = []; f = st.get('focus')
    bs = lambda k: 'focus' if f == k else 'normal'
    if page == 0:
        els = [R(0, 0, W, H, C['bg'], name='background'),
               T(0, 64, W, 'BOROSIL', None, C['blue'], al='c', name='LOGO PLACEHOLDER - replace with company logo', sz=45, wt=800, lh=60, ls=1),
               T(0, 122, W, 'Scientific', None, C['cyan'], al='c', name='logo sub', sz=22, wt=400, lh=30, ls=5),
               T(0, 176, W, 'Reactor Monitoring', None, C['ts'], al='c', name='subtitle', sz=20, wt=500, lh=28), T(0, 204, W, 'Platform', None, C['ts'], al='c', name='subtitle', sz=20, wt=500, lh=28)]
        els += card(12, 252, 296, 104, name='POST card')
        for i, s in enumerate(['MAX31865 RTD ... OK', 'RS232 Motor .... OK', 'Crypto / NVS ... OK']):
            els.append(T(24, 268 + i * 24, 272, s, None, C['green'], f='J', wt=500, sz=16, lh=24, name='POST line'))
        els += [PSLOT(0x1306, 'boot_progress', 12, 384, 296, 8, 65, C['cyan'], C['border']), SLOT(0x1060, 'fw_version', 12, 412, 16, 'S', 'l', C['tm'], 'FW v0.1.0-p4', 'once at boot')]
    elif page in (1, 2):
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_dyn()
        els += card(12, 56, 296, 144, stroke=C['blue'], sw=2, name='analyst card')
        els.append(SLOT(0x3000, 'analyst_name', 24, 112, 17, 'L', 'c', C['tp'] if page == 1 else C['green'], 'Unassigned' if page == 1 else 'Deepa Nair', 'on assignment'))
        els += [R(12, 208, 296, 80, C['sunken'], r=8, name='process bar'), SLOT(0x3020, 'process_name', 24, 236, 22, 'M', 'l', C['tp'], 'Process Unassigned' if page == 1 else 'Synthesis Batch B-42', 'on assignment')]
        s1, s2 = ('disabled', 'disabled') if page == 1 else (bs('accept'), bs('reject'))
        els += btn('accept', 12, 352, 296, 56, 'ACCEPT ASSIGNMENT', 'check', s1) + btn('reject', 12, 424, 296, 44, 'REJECT ASSIGNMENT', 'x', s2)
        if page == 2:
            v = {'accept': (1, 0), 'reject': (0, 1)}.get(f, (0, 0))
            els += [ISLOT(0x1330, 'btn_accept', 6, 346, 40, v[0]), ISLOT(0x1331, 'btn_reject', 6, 418, 41, v[1]), TOUCH(0x3010, 0, 'accept', 12, 352, 296, 56, 'SELECT on ACCEPT'), TOUCH(0x3010, 1, 'reject', 12, 424, 296, 44, 'SELECT on REJECT')]
    elif page == 3:
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_static('NETWORK SETUP REQUIRED', C['amberHdr'], 'wifi')
        for i, (lab, val, col) in enumerate([('1. Connect to Wi-Fi:', 'Borosil-RMP-Setup', C['cyan']), ('2. Open browser to:', 'http://192.168.4.1', C['tp'])]):
            y = 56 + i * 164
            els += card(12, y, 296, 156) + [T(24, y + 28, 272, lab, 'label', C['ts'], name='step %d' % (i + 1)), T(24, y + 84, 272, val, None, col, f='J', wt=800, sz=24, lh=32, name='SSID' if i == 0 else 'URL')]
        els += card(12, 384, 296, 56, stroke=C['amberHdr'], name='status card') + [T(12, 400, 296, 'Listening for credentials...', 'label', C['amber'], al='c', name='status')]
    elif page == 4:
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_static('DEVICE NOT CLAIMED', C['slate'], center=True)
        els += card(12, 56, 296, 72, C['amberBg'], C['amber'], name='warning card') + [I('triangle-alert', 28, 80, 32, C['amber']), T(76, 64, 224, 'Log into Web Admin', 'title', C['amber'], name='warning line 1'), T(76, 92, 224, '& Claim Device', 'title', C['amber'], name='warning line 2')]
        els += card(12, 136, 296, 284)
        blk = [('HARDWARE IDENTIFIER (UUID)', 0x2050, 'device_uuid', '01a1af2d...6bc7', C['cyan'], 148), ('MAC', 0x3280, 'mac_address', 'E8:F6:0A:E3:90:FB', C['tp'], 224), ('IP', 0x3210, 'ip_address', '172.16.50.162', C['tp'], 288), ('MQTT', 0x3220, 'mqtt_broker', '172.16.50.138:18883', C['tp'], 352)]
        for cap, vp, nm, smp, col, y in blk:
            els += [T(24, y, 272, cap, 'caption', C['tm'], name='caption - ' + cap, sz=(14 if len(cap) > 12 else None), lh=(20 if len(cap) > 12 else None)), SLOT(vp, nm, 24, y + 28, 22, 'M', 'l', col, smp, 'once' if vp in (0x2050, 0x3280) else 'on change')]
        els.append(R(24, 212, 272, 1, C['border'], name='divider'))
    elif page == 5:
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_dyn() + ctx_card()
        els += card(12, 136, 296, 192)
        els += row3(158, 60, [('Max Temperature', 0x3080, 'max_temp', '250.0', C['tp'], '°C'), ('Max Speed', 0x3090, 'max_speed', '1500', C['tp'], 'RPM'), ('Heating Rate', 0x30A0, 'max_roc', '+5.0', C['amber'], '°C/min')], 236, 244, 5)
        els += btn('start', 12, 352, 296, 56, 'START PROCESS', 'play', bs('start')) + btn('cancel', 12, 424, 296, 44, 'CANCEL / RETURN', 'x', bs('cancel'))
        v = {'start': (1, 0), 'cancel': (0, 1)}.get(f, (0, 0))
        els += [ISLOT(0x1332, 'btn_start', 6, 346, 42, v[0]), ISLOT(0x1333, 'btn_cancel', 6, 418, 43, v[1]), TOUCH(0x3030, 0, 'start', 12, 352, 296, 56, 'SELECT on START'), TOUCH(0x3030, 1, 'cancel', 12, 424, 296, 44, 'SELECT on CANCEL')]
    elif page == 6:
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_dyn() + ctx_card()
        els += card(12, 136, 296, 104) + [T(24, 142, 80, 'Tr', None, C['tm'], f='P', wt=600, sz=24, lh=28, name='caption - Tr'), ISLOT(0x1301, 'temp_quality_pill', 200, 142, 34, 0, '1 Hz'),
               SLOT(0x1100, 'temp_value', 64, 170, 6, 'HERO', 'r', C['cyan'], '250.2', '1 Hz'), T(240, 190, 56, '°C', None, C['blue'], wt=500, sz=24, lh=32, name='unit')]
        for i, (cap, vp, nm, smp) in enumerate([('RPM', 0x1130, 'rpm_value', '1500'), ('N·cm', 0x1140, 'torque_value', '200.5')]):
            x = 12 + i * 156
            els += card(x, 248, 140, 80) + [T(x + 12, 256, 116, cap, 'caption', C['tm'], name='caption - ' + cap), SLOT(vp, nm, x + 12, 280, 6, 'XL', 'l', C['tp'], smp, '1 Hz')]
        els += card(12, 336, 296, 80) + [T(24, 342, 120, 'DURATION', 'caption', C['tm'], name='caption - Duration'), SLOT(0x2040, 'clock', 246, 344, 5, 'S', 'r', C['ts'], '14:32', 'every 1 s'),
                                        SLOT(0x11C0, 'duration', 24, 368, 8, 'XL', 'l', C['tp'], '01:24:10', 'every 1 s'), ISLOT(0x1307, 'run_footer', 12, 432, 38, 0)]
    elif page == 7:
        els = [R(0, 0, W, H, C['bg'], name='background')] + LIBS[36]['imgs'][st.get('dim', 0)][:]
        els += card(12, 56, 296, 212, C['redBg'], C['red'], 2, name='alarm card')
        els += [SLOT(0x1180, 'alarm_param', 24, 68, 22, 'M', 'l', C['yellow'], 'THERMAL RUNAWAY', 'on alarm'), T(24, 120, 60, 'Tr', None, C['redLt'], f='P', wt=600, sz=24, lh=28, name='caption - Tr'),
                SLOT(0x1190, 'alarm_temp', 68, 104, 6, 'HERO', 'r', '#FFFFFF', '250.2', '1 Hz'), T(244, 124, 52, '°C', None, '#FFFFFF', wt=500, sz=24, lh=32, name='unit'), R(24, 172, 272, 1, C['redLine'], name='row rule'),
                T(24, 184, 150, 'Heating Rate', 'label', C['redLt'], name='label'), SLOT(0x11A0, 'alarm_limit', 164, 184, 6, 'M', 'r', C['redLt'], '+99.0', 'on alarm'), T(244, 186, 52, '°C/min', 'unit', C['redLt'], name='unit', sz=14, lh=20),
                SLOT(0x1170, 'alarm_rate', 96, 216, 7, 'XL', 'r', '#FFFFFF', '+105.2', '1 Hz'), T(244, 228, 52, '°C/min', 'unit', C['redLt'], name='unit', sz=14, lh=20)]
        els += card(12, 276, 296, 112, C['redBg2'], C['redLine'], name='action card') + [T(24, 296, 272, 'Cut Heating Power or', None, C['yellowLt'], f='J', wt=700, sz=20, lh=28, name='instruction 1'), T(24, 336, 272, 'Revert to Cooling', None, C['yellowLt'], f='J', wt=700, sz=20, lh=28, name='instruction 2')]
        els += btn('silence', 12, 412, 296, 56, 'SILENCE HARDWARE SIREN', 'volume-x', 'focus' if not export else 'normal')
        els += [ISLOT(0x1308, 'alarm_header_flash', 0, 0, 36, 0, 'toggle 1 Hz while alarm active'), ISLOT(0x1309, 'mute_button', 6, 406, 37, 0), TOUCH(0x3040, 1, 'silence siren', 12, 412, 296, 56, 'SELECT')]
    elif page == 8:
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_dyn() + ctx_card()
        els += card(12, 136, 296, 244) + [I('circle-check', 24, 152, 24, C['green']), T(56, 152, 240, 'BATCH COMPLETED', 'title', C['green'], name='title'), R(24, 190, 272, 1, C['border'], name='row rule')]
        rows = [('Total Duration', 0x3100, 'total_duration', '02:45:18', C['tp'], None), ('Final Temp', 0x3110, 'final_temp', '24.2', C['tp'], '°C'), ('Samples Logged', 0x3120, 'samples_logged', '9,918', C['tp'], None)]
        els += row3(204, 52, rows, 262, 268, 8) + [ISLOT(0x130A, 'audit_state', 24, 344, 39, 1)]
        els += btn('release', 12, 412, 296, 56, 'RELEASE VESSEL TO IDLE', 'check', 'focus') + [TOUCH(0x3050, 1, 'release', 12, 412, 296, 56, 'SELECT')]
    elif page == 9:
        ws = st.get('win', 1); fo = st.get('focus', 'row0')   # window start 1..3 ; focus 'rowK' (slot K) or 'return'
        els = [R(0, 0, W, H, C['bg'], name='background')] + hdr_static('SYSTEM DIAGNOSTICS', C['header'], 'flask')
        for k in range(5):
            y = ROW_Y[k]; foc = (fo == 'row%d' % k)
            if foc: els += [R(8, y - 4, 288, 68, C['halo'], r=10, name='focus glow (halo)'), R(10, y - 2, 284, 64, '#FFFFFF', r=8, name='focus ring')]
            els += card(12, y, 280, 60, stroke=C['blue'] if foc else C['border'], name='row card - slot %d' % k)
        els += [R(300, 56, 6, 336, C['border'], r=3, name='scroll track'), R(300, 56 + (ws - 1) * 48, 6, 240, C['blue'], r=3, name='scroll thumb')]
        els += btn('return', 12, 412, 296, 56, 'RETURN TO MONITORING', 'arrow-left', 'focus' if fo == 'return' else 'normal')
        for k in range(5):
            cap, val = DIAG[ws - 1 + k]; y = ROW_Y[k]
            els += [ISLOT(0x1320 + k, 'diag_row_%d' % k, 8, y - 4, 45, 1 if fo == 'row%d' % k else 0), ISLOT(0x1310 + k, 'diag_dot_%d' % k, 24, y + 12, 35, 0),
                    SLOT(0x3300 + 0x10 * k, 'diag_caption_%d' % k, 44, y + 8, 8, 'S', 'l', C['tm'], cap), SLOT(0x3290 + 0x10 * k, 'diag_value_%d' % k, 24, y + 30, 21, 'M', 'l', C['tp'], val)]
        els += [ISLOT(0x1325, 'diag_scroll', 300, 56, 46, ws - 1), ISLOT(0x1334, 'btn_return', 6, 406, 44, 1 if fo == 'return' else 0), TOUCH(0x3060, 1, 'return', 12, 412, 296, 56, 'SELECT on RETURN')]
    if export: els = [e for e in els if e['t'] in ('rect', 'text', 'icon')]
    return els

PAGES = {0: ('00_boot', '0x0000', 'Boot / POST'), 1: ('01_assign_unassigned', '0x0001', 'Assignment - UNASSIGNED'), 2: ('02_assign_assigned', '0x0010', 'Assignment - ASSIGNED'),
         3: ('03_network_setup', '0x0002', 'Network Setup'), 4: ('04_not_claimed', '0x0003', 'Device Not Claimed'), 5: ('05_prestart', '0x0011', 'Pre-Start'),
         6: ('06_running', '0x0012', 'Running'), 7: ('07_alarm', '0x0013', 'Critical Alarm'), 8: ('08_completed', '0x0014', 'Batch Completed'), 9: ('09_diagnostics', '0x0020', 'Diagnostics')}
# design frames in Figma: (name, page, state)
FRAMES = [('S0 - Boot', 0, {}), ('S1 - Assignment - UNASSIGNED (buttons disabled)', 1, {}), ('S2a - Assignment - ASSIGNED - focus ACCEPT', 2, {'focus': 'accept'}), ('S2b - Assignment - ASSIGNED - focus REJECT', 2, {'focus': 'reject'}),
          ('S3 - Network Setup', 3, {}), ('S4 - Device Not Claimed', 4, {}), ('S5a - Pre-Start - focus START', 5, {'focus': 'start'}), ('S5b - Pre-Start - focus CANCEL', 5, {'focus': 'cancel'}),
          ('S6 - Running', 6, {}), ('S7 - Critical Alarm', 7, {}), ('S8 - Batch Completed', 8, {}),
          ('S9a - Diagnostics - rows 1-5 - focus row 1', 9, {'win': 1, 'focus': 'row0'}), ('S9b - Diagnostics - rows 2-6 - focus row 6 (scrolled)', 9, {'win': 2, 'focus': 'row4'}),
          ('S9c - Diagnostics - rows 3-7 - focus row 7 (last)', 9, {'win': 3, 'focus': 'row4'}), ('S9d - Diagnostics - rows 3-7 - focus RETURN', 9, {'win': 3, 'focus': 'return'})]

# ---------------- automatic checks ----------------
def checks():
    issues = []
    def under(els, i, e):
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2; col = C['bg']
        for p in els[:i]:
            if p['t'] == 'rect' and p.get('fill') and p['x'] <= cx <= p['x'] + p['w'] and p['y'] <= cy <= p['y'] + p['h'] and p['h'] > 2: col = p['fill']
        return col
    for name, page, st in FRAMES:
        els = build(page, st)
        for i, e in enumerate(els):
            if e['t'] == 'text':
                eff = e['sz']
                if eff < 14: issues.append(f'{name}: text <14px {e["s"]}')
                w = tw(e['s'], e['f'], e['wt'], e['sz'], e['ls'])
                if w > e['w'] + 0.5: issues.append(f'{name}: OVERFLOW "{e["s"]}" {w:.0f}>{e["w"]}')
                if e['x'] < 0 or e['x'] + e['w'] > W + 0.1: issues.append(f'{name}: text box out of frame "{e["s"]}"')
                if not e.get('dis'):
                    bg = under(els, i, e); cr = contrast(e['c'], bg)
                    if cr < 4.5: issues.append(f'{name}: CONTRAST {cr:.2f} "{e["s"]}" {e["c"]} on {bg}')
            elif e['t'] == 'slot':
                if len(e['sample']) > e['chars']: issues.append(f'{name}: SAMPLE too long {e["name"]}')
                if e['w'] != e['chars'] * e['cell'] or e['h'] != 2 * e['cell']: issues.append(f'{name}: box != chars x cell {e["name"]}')
                bg = under(els, i, e); cr = contrast(e['c'], bg)
                if cr < 4.5: issues.append(f'{name}: CONTRAST {cr:.2f} slot {e["name"]} {e["c"]} on {bg}')
            if e['t'] in ('rect', 'text', 'slot', 'islot', 'icon'):
                x, y = e['x'], e['y']
                ww = e.get('w', LIBS[e['lib']]['w'] if e['t'] == 'islot' else e.get('sz', 0)); hh = e.get('h', LIBS[e['lib']]['h'] if e['t'] == 'islot' else e.get('sz', 0))
                if x < -0.1 or y < -0.1 or x + ww > W + 0.1 or y + hh > H + 0.1: issues.append(f'{name}: OUT OF FRAME {e.get("name", e["t"])} {x},{y},{ww},{hh}')
    for lib, L in LIBS.items():
        for si, im in enumerate(L['imgs']):
            for i, e in enumerate(im):
                if e['t'] == 'text':
                    w = tw(e['s'], e['f'], e['wt'], e['sz'], e['ls'])
                    if w > e['w'] + 0.5: issues.append(f'lib{lib}/{si}: OVERFLOW "{e["s"]}" {w:.0f}>{e["w"]}')
                    if not e.get('dis') and e['wt']:
                        bg = L['bg']
                        for p in im[:i]:
                            if p['t'] == 'rect' and p.get('fill') and p['x'] <= e['x'] + e['w'] / 2 <= p['x'] + p['w'] and p['y'] <= e['y'] + e['h'] / 2 <= p['y'] + p['h']: bg = p['fill']
                        if contrast(e['c'], bg) < 4.5: issues.append(f'lib{lib}/{si}: CONTRAST {contrast(e["c"], bg):.2f} "{e["s"]}"')
    return issues

if __name__ == '__main__':
    iss = checks(); print('\n'.join(iss) if iss else 'ALL SPEC CHECKS PASS'); print(len(LIBS), 'libs')
