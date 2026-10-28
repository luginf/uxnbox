#!/usr/bin/env python3
"""Variante Nintendo DS : ecran 256x192, lignes de 8 px, aide dans les reglages.

Derive tracker-ds.tal de tracker.tal par remplacements exacts (chacun doit
tomber une seule fois), puis l'assemble en tracker-ds.rom avec uxncli/drifloon.
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent

SUBS = [
    ("#0180 .Screen/width DEO2", "#0100 .Screen/width DEO2"),
    ("#00f0 .Screen/height DEO2", "#00c0 .Screen/height DEO2"),
    ("#00 SWP #000a MUL2 ;cy STA2", "#00 SWP #0008 MUL2 ;cy STA2"),
    ("#01 ;swapab STA", "#00 ;swapab STA"),
]

src = (HERE / "tracker.tal").read_text()
for a, b in SUBS:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
(HERE / "tracker-ds.tal").write_text(src)
out = subprocess.run([str(ROOT / "uxncli"), str(ROOT / "drifloon.rom")],
                     input=src.encode(), stdout=subprocess.PIPE, check=True).stdout
(HERE / "tracker-ds.rom").write_bytes(out)
print("tracker-ds.rom : %d octets" % len(out))
