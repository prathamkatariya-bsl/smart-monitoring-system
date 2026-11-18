import os, io, math, shutil
from pathlib import Path
from PIL import Image, ImageDraw
import cairosvg
import spec3 as SP
C = SP.C; S_ = 4; W, H = SP.W, SP.H
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def draw_text(d, e):
    fo = SP.font(e['f'], e['wt'], e['sz']); asc, desc = fo.getmetrics(); w = SP.tw(e['s'], e['f'], e['wt'], e['sz'], e['ls'])
    x0 = e['x'] + (e['w'] - w) / 2 if e['al'] == 'c' else (e['x'] + e['w'] - w if e['al'] == 'r' else e['x'])
    base = (e['y'] + (e['h'] - (asc + desc) / S_) / 2) * S_ + asc
    if e['ls'] == 0: d.text((x0 * S_, base), e['s'], font=fo, fill=rgb(e['c']), anchor='ls')
    else:
        cx = x0 * S_
        for ch in e['s']: d.text((cx, base), ch, font=fo, fill=rgb(e['c']), anchor='ls'); cx += fo.getlength(ch) + e['ls'] * S_
def draw_icon(img, e):
    sz = e['sz']; svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{sz}" height="{sz}" viewBox="0 0 24 24" fill="none" stroke="{e["c"]}" stroke-width="{e["sw"]}" stroke-linecap="round" stroke-linejoin="round">{SP.ICONS[e["n"]]}</svg>'
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(sz * S_), output_height=int(sz * S_))
    ic = Image.open(io.BytesIO(png)).convert('RGBA'); img.paste(ic, (int(round(e['x'] * S_)), int(round(e['y'] * S_))), ic)
def draw_els(img, els, ox=0, oy=0):
    d = ImageDraw.Draw(img)
    for e in els:
        if e['t'] == 'rect':
            box = [(e['x'] + ox) * S_, (e['y'] + oy) * S_, (e['x'] + ox + e['w']) * S_ - 1, (e['y'] + oy + e['h']) * S_ - 1]; r = e['r'] * S_
            if e.get('fill'): d.rounded_rectangle(box, radius=r, fill=rgb(e['fill']))
            if e.get('stroke'): d.rounded_rectangle(box, radius=r, outline=rgb(e['stroke']), width=int(e['sw'] * S_))
        elif e['t'] == 'text': draw_text(d, dict(e, x=e['x'] + ox, y=e['y'] + oy))
        elif e['t'] == 'icon': draw_icon(img, dict(e, x=e['x'] + ox, y=e['y'] + oy))
def lib_img(lib, idx):
    L = SP.LIBS[lib]; img = Image.new('RGB', (L['w'] * S_, L['h'] * S_), rgb(L['bg'])); draw_els(img, L['imgs'][idx])
    return img.resize((L['w'], L['h']), Image.LANCZOS)
def sample_slot(img, e):
    d = ImageDraw.Draw(img); cw = e['cell']; fo = SP.font('J', e['wt'], cw / 0.6); s = e['sample']; n = len(s) * cw
    x0 = e['x'] if e['al'] == 'l' else (e['x'] + e['w'] - n if e['al'] == 'r' else e['x'] + (e['w'] - n) / 2)
    asc, desc = fo.getmetrics(); base = (e['y'] + (e['h'] - (asc + desc) / S_) / 2) * S_ + asc
    for i, ch in enumerate(s): d.text(((x0 + i * cw + cw / 2) * S_, base), ch, font=fo, fill=rgb(e['c']), anchor='ms')
EXPORT_STATE = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}, 9: {'win': 1, 'focus': 'none'}}
def static_els(page, st=None): return SP.build(page, EXPORT_STATE[page] if st is None else st, export=True)
def render_static(page, st=None):
    img = Image.new('RGB', (W * S_, H * S_), rgb(C['bg'])); draw_els(img, static_els(page, st)); return img.resize((W, H), Image.LANCZOS)
def render_preview(page, st):
    img = Image.new('RGB', (W * S_, H * S_), rgb(C['bg'])); els = SP.build(page, st); draw_els(img, [e for e in els if e['t'] in ('rect', 'text', 'icon')])
    for e in els:
        if e['t'] == 'islot':
            L = SP.LIBS[e['lib']]; img.paste(lib_img(e['lib'], e['sample']).resize((L['w'] * S_, L['h'] * S_)), (e['x'] * S_, e['y'] * S_))
        elif e['t'] == 'pslot':
            d = ImageDraw.Draw(img); d.rounded_rectangle([e['x'] * S_, e['y'] * S_, (e['x'] + e['w']) * S_, (e['y'] + e['h']) * S_], radius=e['r'] * S_, fill=rgb(e['track']))
            d.rounded_rectangle([e['x'] * S_, e['y'] * S_, (e['x'] + e['w'] * e['val'] / 100) * S_, (e['y'] + e['h']) * S_], radius=e['r'] * S_, fill=rgb(e['fill']))
    for e in els:
        if e['t'] == 'slot': sample_slot(img, e)
    return img.resize((W, H), Image.LANCZOS)
def render_map(page, st=None):
    out = render_static(page, st).convert('RGB'); out = out.resize((W * 2, H * 2), Image.NEAREST); d = ImageDraw.Draw(out, 'RGBA')
    for e in SP.build(page, EXPORT_STATE[page] if st is None else st):
        if e['t'] == 'slot': col = (255, 0, 200); w, h = e['w'], e['h']
        elif e['t'] == 'islot': col = (255, 160, 0); w, h = SP.LIBS[e['lib']]['w'], SP.LIBS[e['lib']]['h']
        elif e['t'] == 'pslot': col = (0, 220, 255); w, h = e['w'], e['h']
        elif e['t'] == 'touch': col = (80, 255, 80); w, h = e['w'], e['h']
        else: continue
        d.rectangle([e['x'] * 2, e['y'] * 2, (e['x'] + w) * 2 - 1, (e['y'] + h) * 2 - 1], outline=col + (255,), fill=col + (40,) if e['t'] != 'touch' else None)
    return out
def sheet(imgs, cols, scale=1, pad=10, bg=(30, 30, 30)):
    ims = [i.resize((int(i.width * scale), int(i.height * scale))) for i in imgs]; w, h = ims[0].size; rows = math.ceil(len(ims) / cols)
    s = Image.new('RGB', (cols * (w + pad) + pad, rows * (h + pad) + pad), bg)
    for k, im in enumerate(ims): s.paste(im, (pad + (k % cols) * (w + pad), pad + (k // cols) * (h + pad)))
    return s
def build_all(O):
    shutil.rmtree(O, ignore_errors=True)
    for dn in ['01_backgrounds_bmp', '01_backgrounds_png', '01_backgrounds_named', '02_icon_libraries', '03_placement_map', '04_preview_with_sample_values']: os.makedirs(f'{O}/{dn}')
    statics, maps, prevs = [], [], []
    for pg, (fn, doc, title) in SP.PAGES.items():
        im = render_static(pg); assert im.size == (320, 480)
        im.save(f'{O}/01_backgrounds_bmp/{pg}.bmp'); im.save(f'{O}/01_backgrounds_png/{pg}.png'); im.save(f'{O}/01_backgrounds_named/{fn}.bmp')
        mp = render_map(pg); mp.save(f'{O}/03_placement_map/MAP_{pg}_{fn}.png'); statics.append(im); maps.append(mp)
    for i, (name, pg, st) in enumerate(SP.FRAMES):
        pv = render_preview(pg, st); pv.save(f'{O}/04_preview_with_sample_values/PREVIEW_{i:02d}_{name.split(" - ")[0]}.png'); prevs.append(pv)
    sheet(statics, 5, 0.8).save(f'{O}/contact_sheet_backgrounds.png'); sheet(maps, 5, 0.5).save(f'{O}/contact_sheet_placement_map.png'); sheet(prevs, 5, 0.8).save(f'{O}/contact_sheet_preview.png')
    for lib, L in SP.LIBS.items():
        dd = f'{O}/02_icon_libraries/{lib}_{L["name"]}_{L["w"]}x{L["h"]}'; os.makedirs(dd)
        for i in range(len(L['imgs'])): im = lib_img(lib, i); im.save(f'{dd}/{i}.bmp'); im.save(f'{dd}/{i}.png')
if __name__ == '__main__':
    out = os.environ.get('DGUS_RENDER_DIR', str(Path(__file__).resolve().parents[1] / 'generated'))
    build_all(out); print(f'rendered: {out}')
