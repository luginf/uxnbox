#!/usr/bin/env python3
"""Test sans ecran : sauve un morceau, vide la memoire, recharge, compare.

Fabrique un ROM de test a partir de tracker.tal (on remplace le point d'entree
par un pilote qui appelle do-save / do-load), l'execute sous uxncli dans un
repertoire temporaire et affiche l'etat avant sauvegarde et apres rechargement.

Usage : python3 tests/selftest.py <repertoire de travail> [fichier.cct a charger]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent

DRIVER = r"""
|10 @Console &vector $2 &read $1 &pad $5 &write $1 &error $1
|0100
@@SAVEBODY
@test-main
	;init-inst JSR2
	;s-defname ;fname #0009 ;copy JSR2
	;pat #1000 #ff ;fill JSR2
	#03 ;len STA
	#05 ;spd STA
	#0123 ;ins #00c0 ADD2 #000e ADD2 STA2
	#0a ;ins #00c0 ADD2 #0007 ADD2 STA
	#58 ;ins #00c0 ADD2 #0036 ADD2 STA
	#30 #00 #00 #00 ;t-set JSR2
	#03 ;cur-inst STA
	#1e #00 #04 #01 ;t-set JSR2
	#00 ;cur-inst STA
	#fe #00 #08 #02 ;t-set JSR2
	#5f #00 #0f #03 ;t-set JSR2
	#00 #00 #03 #00 ;t-set JSR2
	#6b #00 #06 #01 ;t-set JSR2
	#39 #01 #00 #00 ;t-set JSR2
	#2c #01 #07 #00 ;t-set JSR2
	#fe #01 #0f #00 ;t-set JSR2
	;do-save JSR2
	;t-msg JSR2
	;dump JSR2
	;dump-ins JSR2
	;t-sep JSR2
	;pat #1000 #ff ;fill JSR2
	;ins #0200 #00 ;fill JSR2
	#01 ;len STA
	#03 ;spd STA
	;do-load JSR2
	;t-msg JSR2
	;dump JSR2
	;dump-ins JSR2
	;t-sep JSR2
	#00 ;cur-s STA
	;song-del JSR2
	;dump JSR2
	#0f .System/debug DEO
BRK

@@LOADBODY
@test-load
	;pat #1000 #ff ;fill JSR2
	#01 ;len STA
	#06 ;spd STA
	;do-load JSR2
	;t-msg JSR2
	;dump JSR2
BRK

@@HELPERS
@t-set ( v s r vc -- )
	;cur-v STA ;cur-r STA ;cur-s STA ;set-cell JMP2
@t-nib ( n -- )
	#0f AND DUP #0a LTH ;&d JCN2
	#07 ADD
	&d #30 ADD .Console/write DEO
JMP2r
@t-hex ( b -- )
	DUP #04 SFT ;t-nib JSR2
	;t-nib JMP2
@t-nl #0a .Console/write DEO
JMP2r
@t-sep #2d .Console/write DEO ;t-nl JMP2
@t-msg ;msg LDA2 #0000 NEQ2 ;&p JCN2
JMP2r
	&p
	;msg LDA2 ;t-str JSR2 ;t-nl JMP2
@t-str ( str* -- )
	&l LDAk ;&go JCN2
	POP2
JMP2r
	&go LDAk .Console/write DEO INC2 ;&l JMP2
@dump
	;len LDA ;t-hex JSR2 #20 .Console/write DEO ;spd LDA ;t-hex JSR2 ;t-nl JSR2
	#0000 ;t-i STA2
	&l
		;pat ;t-i LDA2 ADD2 LDA ;t-hex JSR2
		;t-i LDA2 INC2 ;t-i STA2
		;t-i LDA2 NIP #0f AND ;&nonl JCN2
		;t-nl JSR2
		&nonl
		;t-i LDA2 ;len LDA #00 SWP #0080 MUL2 LTH2 ;&l JCN2
JMP2r
@dump-ins
	#0000 ;t-i STA2
	&l
		;ins ;t-i LDA2 ADD2 LDA ;t-hex JSR2
		;t-i LDA2 INC2 ;t-i STA2
		;t-i LDA2 NIP #0f AND ;&nonl JCN2
		;t-nl JSR2
		&nonl
		;t-i LDA2 #0200 LTH2 ;&l JCN2
JMP2r
@t-i $2
"""

def main():
    work = Path(sys.argv[1])
    work.mkdir(parents=True, exist_ok=True)
    src = (HERE / "tracker.tal").read_text()
    marker = "|0100\n@on-reset"
    assert marker in src
    head, rest = DRIVER.split("@@SAVEBODY")
    save, rest = rest.split("@@LOADBODY")
    load, helpers = rest.split("@@HELPERS")
    if len(sys.argv) > 2:
        # mode chargement seul : lit un fichier existant, sans rien ecrire
        body = load.replace("@test-load", "@test-main")
    else:
        body = save
    test = src.replace(marker, head + body + helpers + "\n@on-reset")
    if len(sys.argv) > 2:
        test = test.replace('"song.cct', '"' + Path(sys.argv[2]).name)
    # t-i est place apres le code : il tombe dans la zone des donnees, c'est voulu
    (work / "selftest.tal").write_text(test)
    asm = subprocess.run([str(ROOT / "uxncli"), str(ROOT / "drifloon.rom")],
                         input=test.encode(), stdout=subprocess.PIPE, cwd=work)
    (work / "selftest.rom").write_bytes(asm.stdout)
    run = subprocess.run([str(ROOT / "uxncli"), "selftest.rom"], cwd=work,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = run.stdout.decode()
    sys.stdout.write(out)
    if len(sys.argv) > 2:
        return
    # mode aller-retour : bloc 1 (avant sauvegarde) == bloc 2 (apres rechargement),
    # et bloc 3 (apres suppression du motif 0) == les motifs 1 et 2 du bloc 1
    blocks = [b.strip().split("\n") for b in out.split("\n-\n")]
    ok = len(blocks) == 3
    if ok:
        b1 = [l for l in blocks[0] if len(l) == 32 or (len(l) == 5 and l[2] == ' ')]
        b2 = [l for l in blocks[1] if len(l) == 32 or (len(l) == 5 and l[2] == ' ')]
        b3 = blocks[2]
        ok = b1 == b2 and b3[0] == "02 05" and b3[1:] == b1[1 + 8:1 + 24]
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

main()
