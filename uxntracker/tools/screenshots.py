#!/usr/bin/env python3
"""Copies d'ecran du tracker, sans fenetre ni son : on charge un .cct, on pose le curseur, on
laisse le tracker dessiner, puis on lit les couches video avec le noyau d'uxntari compile sur l'hote
(tests/harness.c, avec un ecran logique de 384x240 au lieu de celui de l'ST).

  python3 tools/screenshots.py [morceau.cct] [dossier de sortie]

Ecrit project.png, settings.png, song.png, chain.png, phrase.png et instrument.png. """
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
TARI = ROOT / "uxntari"
CCT = Path(sys.argv[1]) if len(sys.argv) > 1 else TARI / "snowdin.cct"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "docs"
W, H, ZOOM = 384, 240, 2
# palette posee par on-reset : r 1d4f, g 1dbb, b 2ef3, un quartet par couleur
PAL = [(0x11, 0x11, 0x22), (0xdd, 0xdd, 0xee), (0x44, 0xbb, 0xff), (0xff, 0xbb, 0x33)]

# (nom, ecran, curseurs) ; chaine sous le curseur = ligne de song 2, piste 2
SCREENS = [
    ("project", 4), ("settings", 5), ("song", 0), ("chain", 1), ("phrase", 2), ("instrument", 3),
]

SHOT = """
@shot
	;snow-stem ;stem #0007 ;copy JSR2 #07 ;sn STA ;mk-fname JSR2
	;do-load JSR2
	#0000 ;msg STA2
	#02 ;c-sr STA #01 ;c-tk STA #00 ;c-cr STA #00 ;c-pr STA #00 ;cur-inst STA
	#%02x ;goto-scr JSR2
JMP2r
@snow-stem "snowdin
"""


def build_harness(work):
    for f in list(TARI.glob("*.c")) + list(TARI.glob("*.h")):
        if f.name != "st.c":
            shutil.copy(f, work / f.name)
    src = (TARI / "tests" / "harness.c").read_text().replace("../", "")
    (work / "harness.c").write_text(src)
    vid_h = (work / "vid.h").read_text().replace("#define VID_BYTES 32000", "#define VID_BYTES 64000")
    (work / "vid.h").write_text(vid_h)
    vid_c = (work / "vid.c").read_text().replace("planes == 1 ? 400 : 200", "planes == 1 ? 400 : 240")
    (work / "vid.c").write_text(vid_c)
    subprocess.run(["gcc", "-O1", "-w", "-std=gnu99", "-D_POSIX_C_SOURCE=200809L", "-o", "harness",
                    "uxn.c", "dev.c", "vid.c", "file.c", "audio.c", "harness.c"], cwd=work, check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tal = (HERE / "tracker.tal").read_text()
    hook = "\t;on-controller .Controller/vector DEO2\nBRK"
    assert tal.count(hook) == 1
    with tempfile.TemporaryDirectory() as d:
        work = Path(d)
        build_harness(work)
        shutil.copy(CCT, work / "snowdin.cct")
        for name, scr in SCREENS:
            src = tal.replace(hook, "\t;on-controller .Controller/vector DEO2\n\t;shot JSR2\nBRK") + SHOT % scr
            rom = subprocess.run([str(ROOT / "uxncli"), str(ROOT / "drifloon.rom")], input=src.encode(),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=work).stdout
            (work / (name + ".rom")).write_bytes(rom)
            subprocess.run(["./harness", "-n", "-f", "3", "-d", name + ".txt", name + ".rom"], cwd=work,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            rows = (work / (name + ".txt")).read_text().split("\n")[:H]
            img = Image.new("RGB", (W, H))
            px = img.load()
            for y, row in enumerate(rows):
                for x, ch in enumerate(row[:W]):
                    v = int(ch, 16)
                    px[x, y] = PAL[(v >> 2) or (v & 3)]
            img = img.resize((W * ZOOM, H * ZOOM), Image.NEAREST)
            img.save(OUT / (name + ".png"), optimize=True)
            print("ecrit", OUT / (name + ".png"))


main()
