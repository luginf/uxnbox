#!/usr/bin/env python3
"""Regenere le bloc de donnees de tracker.tal (entre les marqueurs GENERATED).

Contenu genere : police 5x7, table des periodes AY (12TET, 1773400 Hz),
textes du fichier .cct (en-tete fidele a l'ecriture de ChooChooTracker 11.0,
bloc d'instrument AY1) et chaines de l'interface.

Usage : python3 tools/gen_data.py          (depuis uxntracker/)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TAL = HERE / "tracker.tal"
BEGIN = "( ==== BEGIN GENERATED (tools/gen_data.py) ==== )"
END = "( ==== END GENERATED ==== )"

# ---------------------------------------------------------------- police 5x7
G = {}
def glyph(ch, *rows):
    assert len(rows) == 7 and all(len(r) == 5 for r in rows), ch
    G[ch] = rows

glyph("0", ".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###.")
glyph("1", "..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###.")
glyph("2", ".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####")
glyph("3", ".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###.")
glyph("4", "...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#.")
glyph("5", "#####", "#....", "####.", "....#", "....#", "#...#", ".###.")
glyph("6", ".###.", "#....", "#....", "####.", "#...#", "#...#", ".###.")
glyph("7", "#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#...")
glyph("8", ".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###.")
glyph("9", ".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##..")
glyph("A", ".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#")
glyph("B", "####.", "#...#", "#...#", "####.", "#...#", "#...#", "####.")
glyph("C", ".###.", "#...#", "#....", "#....", "#....", "#...#", ".###.")
glyph("D", "####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####.")
glyph("E", "#####", "#....", "#....", "####.", "#....", "#....", "#####")
glyph("F", "#####", "#....", "#....", "####.", "#....", "#....", "#....")
glyph("G", ".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###.")
glyph("H", "#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#")
glyph("I", ".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###.")
glyph("J", "..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##..")
glyph("K", "#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#")
glyph("L", "#....", "#....", "#....", "#....", "#....", "#....", "#####")
glyph("M", "#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#")
glyph("N", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#")
glyph("O", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.")
glyph("P", "####.", "#...#", "#...#", "####.", "#....", "#....", "#....")
glyph("Q", ".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#")
glyph("R", "####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#")
glyph("S", ".####", "#....", "#....", ".###.", "....#", "....#", "####.")
glyph("T", "#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..")
glyph("U", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.")
glyph("V", "#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#..")
glyph("W", "#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#")
glyph("X", "#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#")
glyph("Y", "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..")
glyph("Z", "#####", "....#", "...#.", "..#..", ".#...", "#....", "#####")
glyph("-", ".....", ".....", ".....", "#####", ".....", ".....", ".....")
glyph("#", ".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#.")
glyph(".", ".....", ".....", ".....", ".....", ".....", ".##..", ".##..")
glyph(",", ".....", ".....", ".....", ".....", ".##..", "..#..", ".#...")
glyph(":", ".....", ".##..", ".##..", ".....", ".##..", ".##..", ".....")
glyph(";", ".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#...")
glyph("/", "....#", "....#", "...#.", "..#..", ".#...", "#....", "#....")
glyph("+", ".....", "..#..", "..#..", "#####", "..#..", "..#..", ".....")
glyph("=", ".....", ".....", "#####", ".....", "#####", ".....", ".....")
glyph(">", "#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#....")
glyph("<", "....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#")
glyph("*", ".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", ".....")
glyph("'", "..#..", "..#..", ".#...", ".....", ".....", ".....", ".....")
glyph("[", ".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###.")
glyph("]", ".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###.")
glyph("!", "..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#..")
glyph("?", ".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#..")
glyph("(", "...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#.")
glyph(")", ".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#...")
glyph("\\", "#....", "#....", ".#...", "..#..", "...#.", "....#", "....#")

def font_block():
    out = ["@font"]
    for code in range(0x20, 0x60):
        ch = chr(code)
        rows = G.get(ch, ["....."] * 7)
        bs = []
        for r in rows:
            v = 0
            for i, c in enumerate(r):
                if c == "#":
                    v |= 0x40 >> i          # colonne 0 en bit 6 : 1 px de marge a gauche
            bs.append(v)
        bs.append(0)
        hx = "".join("%02x" % b for b in bs)
        label = {" ": "space", "(": "lparen", ")": "rparen"}.get(ch, ch)
        out.append("\t%s %s %s %s ( %s )" % (hx[0:4], hx[4:8], hx[8:12], hx[12:16], label))
    return "\n".join(out)

# ------------------------------------------------------------ periodes AY
CLOCK = 1773400
def periods():
    vals = []
    for idx in range(108):
        f = 440.0 * 2 ** ((idx - 57) / 12.0)
        vals.append(min(4095, int(round(CLOCK / (16.0 * f)))))
    return vals

def periods_block():
    v = periods()
    out = ["@periods"]
    for i in range(0, 108, 12):
        out.append("\t" + " ".join("%04x" % x for x in v[i:i + 12]) + " ( octave %d )" % (i // 12))
    return "\n".join(out)

# ------------------------------------------------------------- textes .cct
def cct_header():
    L = []
    a = L.append
    a("# ChooChooTracker Module 11.0")
    a("")
    a("- Title: uxn tracker")
    a("- Author: ")
    a("- Frame rate: 50.000000")
    a("- Chips count: 4")
    a("- Track inserts: 1,8,2")
    for t in range(8):
        for s in range(2):
            a("- Insert: %d,%d,0,0,0,0,0,0,0,0,0,0" % (t, s))
    a("- Master inserts: 1,2")
    a("- Master insert: 0,0,0,0,0,0,0,0,0,0,0")
    a("- Master insert: 1,0,0,0,0,0,0,0,0,0,0")
    a("- Track volumes: " + ",".join(["100"] * 8))
    a("- Track pans: " + ",".join(["128"] * 8))
    a("- Reverb sends: " + ",".join(["0"] * 8))
    a("- Delay sends: " + ",".join(["0"] * 8))
    a("- Track tilts: " + ",".join(["128"] * 8))
    a("- Reverb: 100,180,160,16000,150,0,180,153,150")
    a("- Delay: 100,0,9,50,12000,0,2,6,160,25,25")
    a("- Tilt pivot: 1000")
    a("- MIDI CC mappings: 32")
    for i in range(32):
        a("- MIDI CC: %d,1,0,0,0,0" % i)
    a("- Linear pitch: 0")
    a("- Signed track speed: 1")
    a("- Perceptual effects: 1")
    a("- Scale: 1,0,0,0,4095,255")
    a("- Chip type: AY8910")
    a("- *AY8910* Clock: %d" % CLOCK)
    a("- *AY8910* AY/YM: 0")
    a("- *AY8910* Stereo: ABC")
    a("- *AY8910* Stereo separation: 50")
    a("- *AY8910* PWM range: 0")
    a("")
    a("## Pitch table")
    a("")
    a("- Title: 12TET %dHz" % CLOCK)
    a("")
    a("```")
    return "\n".join(L) + "\n"

MODS = """- Modulation:
- Mod1: 0,0,0,0,0,0,0,0
- Mod2: 1,0,0,0,0,0,0,0
- Mod3: 2,0,0,0,0,0,0,0
- Mod4: 2,0,0,0,0,0,0,0
- Chip data:
"""
AY_BODY = ("- Name: Square\n- Type: 1\n- Table speed: 1\n- Volume: 255\n- Pan: 128\n- Transpose: 1\n"
           + MODS + "- Volume envelope: 0,0,15,0\n- Auto envelope: 0,0\n- Default mixer: 01\n")
SID_HEAD = "\n- Type: 27\n- Table speed: 1\n- Volume: 255\n- Pan: 128\n- Transpose: 1\n" + MODS + "- SID identity: 1,"

# texte -> octets : mots en "mot, espaces en 20, fins de ligne en 0a
def tal_text(label, s):
    lines = [("@%s" % label)]
    for line in s.split("\n")[:-1] if s.endswith("\n") else s.split("\n"):
        toks = []
        parts = re.split(r"( )", line)
        for p in parts:
            if p == "":
                continue
            toks.append("20" if p == " " else '"' + p)
        toks.append("0a")
        lines.append("\t" + " ".join(toks))
    if not s.endswith("\n"):
        lines[-1] = lines[-1].rsplit(" 0a", 1)[0]
    lines.append("\t00")
    return "\n".join(lines)

TEXTS = [
    ("t-head", cct_header()),
    ("t-song", "```\n\n## Song\n\n```\n"),
    ("t-chains", "```\n\n## Chains\n"),
    ("t-chain-h", "\n### Chain "),
    ("t-fence-open", "\n\n```\n"),
    ("t-chain-r0", " 00\n"),
    ("t-chain-rest", "--- 00\n" * 15 + "```\n"),
    ("t-groove-h", "\n## Grooves\n\n### Groove 0\n\n```\n"),
    ("t-groove-rest", "--\n" * 14 + "```\n"),
    ("t-phrases", "\n## Phrases\n\n"),
    ("t-phrase-h", "### Phrase "),
    ("t-inst-on", " 00"),
    ("t-inst-off", " --"),
    ("t-row-tail", " -- --- 00 --- 00 --- 00\n"),
    ("t-fence-close", "```\n"),
    ("t-insts-h", "\n## Instruments\n"),
    ("t-inst-h", "\n### Instrument "),
    ("t-nn", "\n\n"),
    ("t-ay-body", AY_BODY),
    ("t-sid-1", "- Name: "),
    ("t-sid-2", SID_HEAD),
    ("t-sid-3", "\n- SID name: "),
    ("t-sid-4", "\n- SID parameters: "),
    ("t-tail", "\n## Tables\nEOF\n"),
    ("t-dd", "--"),
    ("t-dashes", "---"),
]

# --------------------------------------------------- chaines de l'interface
HELP_PAGES = [
    ["A TAP PLACE / REPLAY",
     "A+L/R VALUE +-1",
     "A+U/D VALUE +-12 / 16",
     "A+B CLEAR / OFF",
     "B+U/D SONG JUMP 16",
     "B+DIRS CHAIN SONG CELL",
     "B+DIRS PHRASE CHAIN/TRK",
     "B+L/R INST PREV / NEXT",
     "SEL+DIRS SCREEN MAP",
     "START PLAY / STOP",
     "A+START PREVIEW (INST)"],
    ["SONG 64 ROWS X 4 TRACKS",
     "CHAIN 16 X PHRASE + TRANSP",
     "PHRASE 16 X NOTE + INST",
     "INSTRUMENT PRESET LINE",
     " A+L/R PICKS A PRESET",
     " AND ITS NAME, KEEPS NOTES",
     " THEN TUNE WAVE AND ADSR",
     "PROJECT NAME RANDOM",
     " SAVE LOAD NEW SONG",
     "GROOVE SPEED (TEMPO)",
     "SETTINGS A/B SWAP KEYBOARD"],
    ["ESC JAZZ PIANO KEYS",
     None,                   # rangee de touches selon la disposition (jazz)
     "[ ] OR -/= OCTAVE",
     "TAB NEXT  ENTER PROJECT",
     "' OFF  BKSP CLEAR",
     "\\ A/B SWAP ; LAYOUT",
     "ALT=A CTRL=B IF SWAPPED",
     "SHF=SEL HOME=START"],
]
UI = [
    ("s-title", "UXN TRACKER"),
    ("s-play", "PLAY"),
    ("s-stop", "STOP"),
    ("s-song", "SONG "),
    ("s-spd", "SPD "),
    ("s-oct", "OCT "),
    ("s-ins", "INS "),
    ("s-jazz", "JAZZ"),
    ("s-keys", "KEYS "),
    ("s-azerty", "AZERTY"),
    ("s-qwerty", "QWERTY"),
    ("s-none", "---"),
    ("s-off", "OFF"),
    ("s-row-az", "WSXDCVGBHNJ,"),
    ("s-row-qw", "ZSXDCVGBHNJM"),
    ("s-saved", "SAVED"),
    ("s-save-err", "SAVE ERROR"),
    ("s-loaded", "LOADED"),
    ("s-load-err", "LOAD ERROR"),
    ("s-newsong", "NEW SONG"),
    ("s-h-song", "## Song"),
    ("s-h-chains", "## Chains"),
    ("s-h-phr", "## Phrases"),
    ("s-h-groove", "## Grooves"),
    ("s-h-inst", "## Instruments"),
    ("s-h-any", "## "),
    ("s-h-chain", "### Chain "),
    ("s-h-phrase", "### Phrase "),
    ("s-h-groove1", "### Groove "),
    ("s-h-inst1", "### Instrument "),
    ("s-p-type", "- Type: "),
    ("s-p-sidp", "- SID parameters: "),
    ("s-p-sidn", "- SID name: "),
    ("s-p-sidi", "- SID identity: "),
    ("s-defname", "song.cct"),
    ("s-square", "SQUARE"),
    ("s-m0", "NAME "),
    ("s-mr", "RANDOM NAME"),
    ("s-ehint", "UP/DN CHAR L/R MOVE A OK B DEL"),
    ("s-fhint", "A LOAD  B BACK"),
    ("s-lload", "LOAD FILE"),
    ("s-m1", "SAVE"),
    ("s-m2", "LOAD"),
    ("s-m3", "NEW SONG"),
    ("s-m4", "CLOSE"),
    ("s-on", "ON"),
    ("s-menu", "PROJECT"),
    ("s-unsaved", "UNSAVED CHANGES"),
    ("s-c1", "FILE EXISTS. OVERWRITE? Y/N"),
    ("s-c2", "LOAD: DISCARD UNSAVED? Y/N"),
    ("s-c3", "NEW: DISCARD UNSAVED? Y/N"),
    ("s-mhint", "A/ENTER OK  B/ESC BACK"),
    ("s-ay-note", "AY SQUARE: NO PARAMETERS"),
    ("s-inst-h", "INSTRUMENT "),
    ("s-map", "SCPI"),
    ("s-t0", "SONG"),
    ("s-t1", "CHAIN"),
    ("s-t2", "PHRASE"),
    ("s-t3", "INSTRUMENT"),
    ("s-t4", "PROJECT"),
    ("s-t5", "SETTINGS"),
    ("s-t6", "GROOVE"),
    ("s-t7", "HELP"),
    ("s-hpg", "PAGE "),
    ("s-hof", "/3  L/R PAGE  B QUIT"),
    ("s-preset", "PRESET"),
    ("s-chn", "CHAIN "),
    ("s-phr", "PHRASE "),
    ("s-row", "ROW "),
    ("s-trk", "TRK "),
    ("s-ph", "PH"),
    ("s-tr", "TR"),
    ("s-hnote", "NOTE"),
    ("s-hin", "IN"),
    ("s-nofree", "NO FREE SLOT"),
    ("s-spdl", "SPEED"),
    ("s-ghint", "A+L/R CHANGE"),
    ("s-set0", "A/B SWAP"),
    ("s-set1", "KEYBOARD"),
    ("s-set2", "HELP"),
    ("s-shint", "A TOGGLE / OPEN"),
]
FIELDS = [   # (nom, parametre SID, max, pas, grand pas)
    ("WAVE", 1, 8, 1, 1),
    ("PULSE", 6, 4095, 64, 512),
    ("PWM DEPTH", 19, 2047, 16, 128),
    ("PWM RATE", 20, 1000, 1, 10),
    ("ATTACK", 2, 15, 1, 4),
    ("DECAY", 3, 15, 1, 4),
    ("SUSTAIN", 4, 15, 1, 4),
    ("RELEASE", 5, 15, 1, 4),
    ("GATE", 14, 1000, 1, 10),
    ("ARP", 24, 4, 1, 1),
]
SID_BASE = [0, 4, 1, 6, 10, 5, 512, 800, 8, 1, 0, 0, 2, 50, 0, 0, 0, 0, 0, 128, 3, 0, 0, 65535, 0]
# (nom, wave, pulse, pwm depth, pwm rate, A, D, S, R, gate, arp)
PRESETS = [
    ("PULSE PWM", 4, 1536, 900, 25, 0, 6, 10, 5, 0, 0),
    ("SAW LEAD",  2, 2048, 0, 0,    0, 9, 12, 6, 0, 0),
    ("TRI BASS",  1, 2048, 0, 0,    0, 8, 15, 4, 0, 0),
    ("NOISE HAT", 8, 2048, 0, 0,    0, 3, 0, 3, 3, 0),
    ("PLUCK",     4, 512, 0, 0,     0, 7, 0, 4, 0, 0),
    ("PAD",       2, 2048, 0, 0,    9, 8, 12, 9, 0, 0),
    ("ARP PULSE", 4, 1024, 400, 40, 0, 6, 9, 4, 0, 1),
]
ARP = [(0, 0, 0), (0, 4, 7), (0, 3, 7), (0, 7, 12), (0, 5, 9)]
ATK_TICKS = [1, 1, 1, 1, 2, 3, 3, 4, 5, 12, 25, 40, 50, 150, 250, 400]
DEC_TICKS = [1, 1, 2, 4, 6, 8, 10, 12, 15, 38, 75, 120, 150, 450, 750, 1200]

def plain(label, s):
    toks = []
    for p in re.split(r"( )", s):
        if p == "":
            continue
        toks.append("20" if p == " " else '"' + p)
    toks.append("00")
    return "@%s %s" % (label, " ".join(toks))

def help_block(name, items, x, y0):
    out = ["@" + name, "\t#01 ;col STA"]
    for i, h in enumerate(items):
        out.append("\t#%02x #%02x ;at JSR2" % (x, y0 + i))
        if h is None:
            out.append("\t;layout LDA ;&q JCN2 ;s-row-az ;&p JMP2 &q ;s-row-qw &p ;put-str JSR2")
        else:
            out.append("\t;%s%d ;put-str JSR2" % (name, i))
    out.append("JMP2r")
    for i, h in enumerate(items):
        if h is not None:
            out.append(plain("%s%d" % (name, i), h))
    return "\n".join(out)

def words(vals):
    return " ".join("%04x" % v for v in vals)

def tables_block():
    out = []
    out.append("@tri64")
    t = [(i * 8 + 4) if i < 32 else ((63 - i) * 8 + 4) for i in range(64)]
    out += ["\t" + " ".join("%02x" % x for x in t[i:i + 16]) for i in range(0, 64, 16)]
    out.append("@saw64")
    t = [i * 4 + 2 for i in range(64)]
    out += ["\t" + " ".join("%02x" % x for x in t[i:i + 16]) for i in range(0, 64, 16)]
    import math
    out.append("@sinhalf")
    t = [int(round(127 * math.sin(math.pi * i / 32))) for i in range(32)]
    out += ["\t" + " ".join("%02x" % x for x in t[i:i + 16]) for i in range(0, 32, 16)]
    out.append("@atk-ticks\n\t" + words(ATK_TICKS))
    out.append("@dec-ticks\n\t" + words(DEC_TICKS))
    out.append("@arptab\n\t" + " ".join("%02x %02x %02x" % r for r in ARP))
    out.append("@sid-base\n\t" + words(SID_BASE))
    out.append("@ifields ( param, max, step, big step )")
    for name, p, mx, st, big in FIELDS:
        out.append("\t%02x %04x %04x %04x ( %s )" % (p, mx, st, big, name))
    out.append("@ifnames " + " ".join("=ifn%d" % i for i in range(len(FIELDS))))
    for i, f in enumerate(FIELDS):
        out.append(plain("ifn%d" % i, f[0]))
    out.append("@mitems =s-m0 =s-mr =s-m1 =s-m2 =s-m3 =s-m4")
    out.append("@titles " + " ".join("=s-t%d" % i for i in range(8)))
    out.append("@setitems =s-set0 =s-set1 =s-set2")
    out.append("@presets ( name x10, then wave pulse depth rate A D S R gate arp )")
    for (name, *vals) in PRESETS:
        assert len(name) <= 9
        nb = name.encode() + b"\0" * (10 - len(name))
        hx = " ".join("%02x" % b for b in nb)
        out.append("\t%s %s ( %s )" % (hx, words(vals), name))
    return "\n".join(out)

def semis_block():
    return "@semis 09 0b 00 02 04 05 07 ( A B C D E F G )\n@notenames \"C-C#D-D#E-F-F#G-G#A-A#B-"

def generated():
    parts = [font_block(), periods_block(), semis_block(), tables_block(),
             "@hpages =hpa =hpb =hpc"] + [help_block(n, pg, 2, 4) for n, pg in zip(("hpa", "hpb", "hpc"), HELP_PAGES)]
    for label, s in UI:
        parts.append(plain(label, s))
    for label, s in TEXTS:
        parts.append(tal_text(label, s))
    return BEGIN + "\n" + "\n".join(parts) + "\n" + END

def main():
    # controle des periodes contre le tableau ecrit par ChooChooTracker
    ref = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if ref and ref.exists():
        txt = ref.read_text()
        m = re.findall(r"^([A-G][-#]\d) (\d+)$", txt, re.M)
        got = [int(v) for _, v in m][:108]
        if got != periods():
            bad = [i for i, (a, b) in enumerate(zip(got, periods())) if a != b]
            sys.exit("periodes differentes de %s aux indices %s" % (ref, bad[:10]))
        print("periodes identiques a", ref)
    src = TAL.read_text()
    pat = re.compile(re.escape(BEGIN) + ".*?" + re.escape(END), re.S)
    if not pat.search(src):
        sys.exit("marqueurs introuvables dans tracker.tal")
    TAL.write_text(pat.sub(lambda m: generated(), src))
    print("tracker.tal mis a jour")

if __name__ == "__main__":
    main()
