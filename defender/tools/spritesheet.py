#!/usr/bin/env python3
"""Round-trip the Defender sprites between defender.tal and an editable PNG.

  python3 tools/spritesheet.py export   # defender.tal -> sprites.png
  python3 tools/spritesheet.py import    # sprites.png  -> patches defender.tal

The sprites are 1bpp (on/off). In the PNG a pixel is "on" when it is painted
clearly brighter than the dark background; faint guide lines stay near the
background colour so they read as "off". Edit at the pixel level (each logical
pixel is an SxS block) and keep "off" pixels dark.
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TAL  = os.path.join(HERE, '..', 'defender.tal')
PNG  = os.path.join(HERE, '..', 'sprites.png')

S      = 16          # pixels per logical pixel
TILE   = 8           # logical tile size
CELL   = S * TILE    # 128
GAP    = 24
LABEL  = 22
MARGIN = 24

BG     = (17, 34, 51)        # dark blue (game colour 0)
GUIDE  = (32, 50, 68)        # faint grid, close to BG -> reads as "off"
ONTHR  = 60                  # colour-distance threshold for "on"
COLORS = {'white': (238, 238, 238), 'green': (68, 221, 85), 'orange': (255, 136, 34)}

# name, grid col, grid row, ink colour
TILES = [
    ('ship-l',   0, 0, 'white'),  ('ship-r',   1, 0, 'white'),
    ('shipT-l',  2, 0, 'white'),  ('shipT-r',  3, 0, 'white'),
    ('shipH1-l', 0, 1, 'white'),  ('shipH1-r', 1, 1, 'white'),
    ('shipH2-l', 2, 1, 'white'),  ('shipH2-r', 3, 1, 'white'),
    ('en1a',     0, 2, 'green'),  ('en1b',     1, 2, 'green'),
    ('en2a',     2, 2, 'orange'), ('en2b',     3, 2, 'orange'),
    ('shot',     0, 3, 'orange'),
]

def cell_origin(col, row):
    x = MARGIN + col * (CELL + GAP)
    y = MARGIN + row * (CELL + GAP + LABEL) + LABEL
    return x, y

def parse_tile(text, name):
    m = re.search(r'^@%s\s+([0-9a-fA-F ]+?)\s*(\(|$)' % re.escape(name), text, re.M)
    if not m:
        raise SystemExit('tile not found in defender.tal: ' + name)
    hexs = m.group(1).replace(' ', '')
    by = bytes.fromhex(hexs)[:8]
    return [[(by[r] >> (7 - c)) & 1 for c in range(8)] for r in range(8)]

def tile_to_hex(rows):
    by = [sum((rows[r][c] & 1) << (7 - c) for c in range(8)) for r in range(8)]
    s = ''.join('%02x' % b for b in by)
    return ' '.join(s[i:i+4] for i in range(0, 16, 4))

def font():
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, 14)
    return ImageFont.load_default()

def export():
    text = open(TAL).read()
    cols = max(c for _, c, _, _ in TILES) + 1
    rows = max(r for _, _, r, _ in TILES) + 1
    W = MARGIN * 2 + cols * CELL + (cols - 1) * GAP
    H = MARGIN * 2 + rows * (CELL + LABEL) + (rows - 1) * GAP
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f = font()
    for name, col, row, ck in TILES:
        ox, oy = cell_origin(col, row)
        d.text((ox, oy - LABEL + 4), name, fill=(150, 160, 180), font=f)
        # faint per-pixel guide grid (near-BG so it reads as off)
        for k in range(TILE + 1):
            d.line([(ox + k * S, oy), (ox + k * S, oy + CELL)], fill=GUIDE)
            d.line([(ox, oy + k * S), (ox + CELL, oy + k * S)], fill=GUIDE)
        bits = parse_tile(text, name)
        ink = COLORS[ck]
        for r in range(TILE):
            for c in range(TILE):
                if bits[r][c]:
                    x0, y0 = ox + c * S + 1, oy + r * S + 1
                    d.rectangle([x0, y0, x0 + S - 2, y0 + S - 2], fill=ink)
    img.save(PNG)
    print('wrote', PNG, '(%dx%d)' % (W, H))

def imp():
    img = Image.open(PNG).convert('RGB')
    px = img.load()
    text = open(TAL).read()
    for name, col, row, ck in TILES:
        ox, oy = cell_origin(col, row)
        bits = [[0] * 8 for _ in range(8)]
        for r in range(TILE):
            for c in range(TILE):
                cx, cy = ox + c * S + S // 2, oy + r * S + S // 2
                pr, pg, pb = px[cx, cy]
                dist = ((pr - BG[0]) ** 2 + (pg - BG[1]) ** 2 + (pb - BG[2]) ** 2) ** 0.5
                bits[r][c] = 1 if dist > ONTHR else 0
        new = tile_to_hex(bits)
        text, n = re.subn(r'(^@%s\s+)[0-9a-fA-F ]+?(\s*(?:\(|$))' % re.escape(name),
                          lambda m: m.group(1) + new + (' ' if m.group(2).strip().startswith('(') else '') + m.group(2).lstrip(),
                          text, count=1, flags=re.M)
        if n != 1:
            raise SystemExit('could not patch ' + name)
        print('%-9s -> %s' % (name, new))
    open(TAL, 'w').write(text)
    print('patched', TAL)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'export'
    (export if cmd == 'export' else imp)()
