#!/usr/bin/env python3
"""Tests sans ecran, sous uxncli : aller-retour fichier, lecture, ecrans, entrees manette.

Fabrique un ROM de test a partir de tracker.tal (le point d'entree est remplace par un
pilote ; trigger / note-off / draw-char sont remplaces par des versions qui ecrivent dans la
console ou dans un tampon de texte) et l'execute dans un repertoire de travail.

  1. aller-retour : morceau -> do-save -> memoire effacee -> do-load, tout doit etre identique
  2. lecture : 100 ticks (tempo 1), la suite de notes jouees est comparee a un modele en Python
  3. ecrans : chaque ecran est dessine dans un tampon de texte (32 colonnes au plus, pile
     equilibree, quelques textes attendus)
  4. manette : A tap, A+haut, Select+droite, A+B... enchaines comme sur une vraie manette

Usage : python3 tests/selftest.py <repertoire de travail> [fichier.cct a charger]
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent

DRIVER = r"""
|10 @Console &vector $2 &read $1 &pad $5 &write $1 &error $1
|d000 @tbuf $480
|0100
@@FULLBODY
@test-main
	;init-inst JSR2
	;s-defstem ;stem #0005 ;copy JSR2 #04 ;sn STA ;mk-fname JSR2
	;init-all JSR2
	#30 ;lastnote STA
	#05 ;spd STA
	#0123 ;ins #00c0 ADD2 #000e ADD2 STA2
	#0a ;ins #00c0 ADD2 #0007 ADD2 STA
	#58 ;ins #00c0 ADD2 #0036 ADD2 STA
	( song : id row trk )
	#00 #00 #00 ;x-song JSR2
	#01 #00 #01 ;x-song JSR2
	#05 #00 #03 ;x-song JSR2
	#02 #01 #00 ;x-song JSR2
	#7f #00 #02 ;x-song JSR2
	#02 #03 #00 ;x-song JSR2
	( chaines : phrase trans ch row )
	#00 #00 #00 #00 ;x-chn JSR2
	#01 #02 #00 #01 ;x-chn JSR2
	#7f #fe #00 #02 ;x-chn JSR2
	#02 #0c #01 #00 ;x-chn JSR2
	#03 #00 #02 #00 ;x-chn JSR2
	#05 #00 #05 #00 ;x-chn JSR2
	#04 #01 #05 #03 ;x-chn JSR2
	#06 #00 #7f #00 ;x-chn JSR2
	#7f #05 #7f #0f ;x-chn JSR2
	( phrases : note inst p row )
	#30 #00 #00 #00 ;x-phr JSR2
	#34 #01 #00 #04 ;x-phr JSR2
	#fe #ff #00 #08 ;x-phr JSR2
	#5f #03 #00 #0f ;x-phr JSR2
	#3c #03 #01 #00 ;x-phr JSR2
	#40 #01 #01 #06 ;x-phr JSR2
	#24 #00 #02 #00 ;x-phr JSR2
	#2c #00 #02 #07 ;x-phr JSR2
	#39 #01 #03 #00 ;x-phr JSR2
	#40 #02 #04 #02 ;x-phr JSR2
	#30 #00 #05 #01 ;x-phr JSR2
	#32 #02 #05 #05 ;x-phr JSR2
	#6b #00 #06 #03 ;x-phr JSR2
	#1e #05 #06 #09 ;x-phr JSR2
	#6b #07 #7f #0f ;x-phr JSR2
	;x-mark-a JSR2
	;do-save JSR2
	;t-msg JSR2
	;dump-all JSR2
	;dump-ins JSR2
	;x-mark-b JSR2
	;init-all JSR2
	;ins #0200 #00 ;fill JSR2
	#03 ;spd STA
	;do-load JSR2
	;t-msg JSR2
	;dump-all JSR2
	;dump-ins JSR2
	;x-mark-p JSR2
	#01 ;spd STA
	#00 ;c-sr STA
	.System/wst DEI ;x-w STA .System/rst DEI ;x-r STA
	;play-start JSR2
	#00 ;x-k STA
	&pl
		;do-tick JSR2 ;t-nl JSR2
		;x-k LDA INC DUP ;x-k STA #64 LTH ;&pl JCN2
	;play-stop JSR2
	#00 ;playing STA
	.System/wst DEI ;x-w LDA NEQ ;&pbad JCN2
	.System/rst DEI ;x-r LDA NEQ ;&pbad JCN2
	;&pok JMP2
	&pbad #21 .Console/write DEO #21 .Console/write DEO ;t-nl JSR2
	&pok
	;x-mark-s JSR2
	#01 ;c-sr STA
	#00 ;x-k STA
	&sc
		;x-k LDA ;x-screen JSR2
		;x-k LDA INC DUP ;x-k STA #0f LTH ;&sc JCN2
	;x-mark-i JSR2
	;x-input JSR2
	#0f .System/debug DEO
BRK

@@LOADBODY
@test-load
	;s-defname ;fname #0010 ;copy JSR2
	;init-all JSR2
	;do-load JSR2
	;t-msg JSR2
	;dump-all JSR2
	#0f .System/debug DEO
BRK

@@HELPERS
( ---- remplacements de trigger / note-off / draw-char : on journalise ---- )
@trigger ( v n i -- )
	;x-ti STA ;x-tn STA ;x-tv STA
	#54 .Console/write DEO
	;x-tv LDA ;t-hex JSR2 #20 .Console/write DEO
	;x-tn LDA ;t-hex JSR2 #20 .Console/write DEO
	;x-ti LDA ;t-hex JSR2 #20 .Console/write DEO
JMP2r
@note-off ( v -- )
	#4f .Console/write DEO ;t-hex JSR2 #20 .Console/write DEO
JMP2r
@draw-char ( c -- )
	;x-c STA
	;cy LDA2 #000a DIV2 #0030 MUL2
	;cx LDA2 #03 SFT2 ADD2
	;tbuf ADD2 ;x-p STA2
	;x-c LDA ;x-p LDA2 STA
	;cx LDA2 #0008 ADD2 ;cx STA2
JMP2r

( ---- construction du morceau de test ---- )
@x-song ( id row trk -- )
	;song-addr JSR2 STA
JMP2r
@x-chn ( phrase trans ch row -- )
	;chn-addr JSR2 ;sca STA2
	;sca LDA2 INC2 STA
	;sca LDA2 STA
JMP2r
@x-phr ( note inst p row -- )
	;phr-addr JSR2 ;sca STA2
	;sca LDA2 INC2 STA
	;sca LDA2 STA
JMP2r

( ---- sortie ---- )
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
@x-mark ( c -- ) #0a .Console/write DEO #40 .Console/write DEO .Console/write DEO ;t-nl JMP2
@x-mark-a #41 ;x-mark JMP2
@x-mark-b #42 ;x-mark JMP2
@x-mark-p #50 ;x-mark JMP2
@x-mark-s #53 ;x-mark JMP2
@x-mark-i #49 ;x-mark JMP2
@t-msg ;msg LDA2 #0000 NEQ2 ;&p JCN2
JMP2r
	&p
	;msg LDA2 ;t-str JSR2 ;t-nl JMP2
@t-str ( str* -- )
	&l LDAk ;&go JCN2
	POP2
JMP2r
	&go LDAk .Console/write DEO INC2 ;&l JMP2

( addr* len* -- : octets en hexa, 32 par ligne )
@x-dump
	;x-n STA2 ;x-a STA2
	#0000 ;t-i STA2
	&l
		;x-a LDA2 ;t-i LDA2 ADD2 LDA ;t-hex JSR2
		;t-i LDA2 INC2 ;t-i STA2
		;t-i LDA2 NIP #1f AND ;&nonl JCN2
		;t-nl JSR2
		&nonl
		;t-i LDA2 ;x-n LDA2 LTH2 ;&l JCN2
JMP2r
@dump-all
	;slen LDA ;t-hex JSR2 #20 .Console/write DEO ;spd LDA ;t-hex JSR2 ;t-nl JSR2
	;song #0100 ;x-dump JSR2
	;chn #1000 ;x-dump JSR2
	;phr #1000 ;x-dump JSR2
JMP2r
@dump-ins
	;ins #0200 ;x-dump JMP2

( ---- ecrans : on dessine dans tbuf et on verifie la pile ---- )
@x-screen ( n -- )
	DUP #0d LTH ;&nh JCN2
	#0c SUB ;hpage STA #07 ;goto-scr JSR2 ;&go JMP2
	&nh
	DUP #08 LTH ;&norm JCN2
	#07 SUB ;x-m STA #04 ;goto-scr JSR2
	;x-m LDA #05 EQU ;&fo JCN2
	;x-m LDA ;mconf STA #01 ;npos STA ;&go JMP2
	&fo ;flist-open JSR2 ;&go JMP2
	&norm ;goto-scr JSR2
	&go
	;tbuf #0480 #20 ;fill JSR2
	.System/wst DEI ;x-w STA .System/rst DEI ;x-r STA
	;redraw JSR2
	.System/wst DEI ;x-w LDA NEQ ;&bad JCN2
	.System/rst DEI ;x-r LDA NEQ ;&bad JCN2
	;&ok JMP2
	&bad #21 .Console/write DEO #21 .Console/write DEO ;t-nl JSR2
	&ok
	#40 .Console/write DEO #4e .Console/write DEO ;x-k LDA ;t-hex JSR2 ;t-nl JSR2
	#00 ;x-r STA
	&l
		;tbuf ;x-r LDA #00 SWP #0030 MUL2 ADD2 #0030 ;x-dump-text JSR2
		;x-r LDA INC DUP ;x-r STA #18 LTH ;&l JCN2
JMP2r
@x-dump-text ( addr* n -- )
	;x-n STA2 ;x-a STA2
	#0000 ;t-i STA2
	&l
		;x-a LDA2 ;t-i LDA2 ADD2 LDA .Console/write DEO
		;t-i LDA2 INC2 ;t-i STA2
		;t-i LDA2 ;x-n LDA2 LTH2 ;&l JCN2
	;t-nl JMP2

( ---- manette : x-down / x-up emulent bnow / bedge / brel puis appellent do-buttons ---- )
@x-down ( b -- )
	DUP ;bedge STA #00 ;brel STA
	;x-h LDA ORA DUP ;x-h STA ;bnow STA
	;do-buttons JMP2
@x-up ( b -- )
	DUP ;brel STA #00 ;bedge STA
	#ff EOR ;x-h LDA AND DUP ;x-h STA ;bnow STA
	;do-buttons JMP2
@x-tap ( b -- )
	DUP ;x-down JSR2 ;x-up JMP2
@x-input
	#00 ;scr STA #00 ;menu STA #00 ;c-sr STA #00 ;c-tk STA #00 ;c-cr STA #00 ;c-pr STA #00 ;c-fld STA
	#00 ;lastchain STA #00 ;lastphr STA #00 ;cur-inst STA #30 ;lastnote STA #00 ;x-h STA
	;init-all JSR2
	#00 ;modified STA
	( A seul sur une case vide du song : pose la derniere chaine )
	#01 ;x-tap JSR2
	#80 ;x-tap JSR2
	( A + haut : +16 )
	#01 ;x-down JSR2 #10 ;x-tap JSR2 #01 ;x-up JSR2
	;x-state JSR2
	( Select + droite : CHAIN ; A ; A + bas (refuse) ; A + haut )
	#04 ;x-down JSR2 #80 ;x-tap JSR2 #04 ;x-up JSR2
	#01 ;x-tap JSR2
	#01 ;x-down JSR2 #20 ;x-tap JSR2 #10 ;x-tap JSR2 #01 ;x-up JSR2
	;x-state JSR2
	( Select + droite : PHRASE ; A ; A + droite ; A + B ; bas ; A + B )
	#04 ;x-down JSR2 #80 ;x-tap JSR2 #04 ;x-up JSR2
	#01 ;x-tap JSR2
	#01 ;x-down JSR2 #80 ;x-tap JSR2 #01 ;x-up JSR2
	;x-state JSR2
	#01 ;x-down JSR2 #02 ;x-down JSR2 #02 ;x-up JSR2 #01 ;x-up JSR2
	#20 ;x-tap JSR2
	#01 ;x-down JSR2 #02 ;x-down JSR2 #02 ;x-up JSR2 #01 ;x-up JSR2
	;x-state JSR2
	( allocation : piste 2 vide, A sur CHAIN puis sur PHRASE prennent la premiere chaine / phrase libre )
	#04 ;x-down JSR2 #40 ;x-tap JSR2 #40 ;x-tap JSR2 #04 ;x-up JSR2
	#80 ;x-tap JSR2
	#04 ;x-down JSR2 #80 ;x-tap JSR2 #04 ;x-up JSR2
	#01 ;x-tap JSR2
	#20 ;x-tap JSR2
	#04 ;x-down JSR2 #80 ;x-tap JSR2 #04 ;x-up JSR2
	#01 ;x-tap JSR2
	;x-state2 JSR2
	( navigation : Select + gauche, Select + haut )
	;x-nav JSR2
	;x-names JSR2
	;x-presets JSR2
	;x-help JSR2
JMP2r
@x-nav
	#04 ;x-down JSR2 #40 ;x-tap JSR2 #40 ;x-tap JSR2 #04 ;x-up JSR2
	;x-state JSR2
	#04 ;x-down JSR2 #10 ;x-tap JSR2 #04 ;x-up JSR2
	;x-state JSR2
JMP2r
@x-names
	( PROJECT : NAME, haut = lettre suivante, droite x4, haut = ajoute un a, B efface, A valide )
	#10 ;x-tap JSR2 #10 ;x-tap JSR2 #01 ;x-tap JSR2
	#10 ;x-tap JSR2
	#80 ;x-tap JSR2 #80 ;x-tap JSR2 #80 ;x-tap JSR2 #80 ;x-tap JSR2
	#10 ;x-tap JSR2 #02 ;x-tap JSR2 #01 ;x-tap JSR2
	;x-state3 JSR2
	( RANDOM )
	#20 ;x-tap JSR2 #01 ;x-tap JSR2
	;x-state3 JSR2
	( LOAD : liste des .cct, A choisit, comme le morceau est modifie on demande confirmation )
	#20 ;x-tap JSR2 #20 ;x-tap JSR2 #01 ;x-tap JSR2
	;x-state3 JSR2
	#01 ;x-tap JSR2
	;x-state3 JSR2
JMP2r
@x-presets
	#03 ;goto-scr JSR2 #03 ;cur-inst STA ;x-pres JSR2
	#01 ;x-down JSR2 #80 ;x-tap JSR2 #01 ;x-up JSR2 ;x-pres JSR2
	#01 ;x-down JSR2 #40 ;x-tap JSR2 #01 ;x-up JSR2 ;x-pres JSR2
	#01 ;x-down JSR2 #80 ;x-tap JSR2 #01 ;x-up JSR2 ;x-pres JSR2
	#01 ;x-down JSR2 #80 ;x-tap JSR2 #01 ;x-up JSR2 ;x-pres JSR2
	#20 ;x-tap JSR2
	#01 ;x-down JSR2 #80 ;x-tap JSR2 #01 ;x-up JSR2 ;x-pres JSR2
JMP2r
@x-pres
	#50 .Console/write DEO #20 .Console/write DEO
	;cur-inst LDA ;t-hex JSR2 #20 .Console/write DEO
	;ins #00c0 ADD2 LDA ;t-hex JSR2 #20 .Console/write DEO
	;ins #00c4 ADD2 LDA ;t-hex JSR2 ;ins #00c5 ADD2 LDA ;t-hex JSR2 #20 .Console/write DEO
	;ins #00f6 ADD2 ;t-str JSR2 ;t-nl JMP2
@x-help
	#00 ;hpage STA #07 ;goto-scr JSR2
	#80 ;x-tap JSR2 ;x-hs JSR2
	#80 ;x-tap JSR2 ;x-hs JSR2
	#80 ;x-tap JSR2 ;x-hs JSR2
	#40 ;x-tap JSR2 ;x-hs JSR2
	#04 ;x-down JSR2 #40 ;x-tap JSR2 #04 ;x-up JSR2 ;x-hs JSR2
	#02 ;x-tap JSR2 ;x-hs JSR2
JMP2r
@x-hs
	#48 .Console/write DEO #20 .Console/write DEO
	;scr LDA ;t-hex JSR2 #20 .Console/write DEO
	;hpage LDA ;t-hex JSR2 ;t-nl JMP2
@x-state
	#53 .Console/write DEO #20 .Console/write DEO
	;scr LDA ;t-hex JSR2 #20 .Console/write DEO
	;song #0004 ;x-dump-hex JSR2
	;chn #0200 ADD2 #0004 ;x-dump-hex JSR2
	;phr #0200 ADD2 #0004 ;x-dump-hex JSR2
	;t-nl JMP2
@x-state3
	#46 .Console/write DEO #20 .Console/write DEO
	;mconf LDA ;t-hex JSR2 #20 .Console/write DEO
	;fname ;t-str JSR2 ;t-nl JMP2
@x-state2
	#4e .Console/write DEO #20 .Console/write DEO
	;scr LDA ;t-hex JSR2 #20 .Console/write DEO
	;song #0004 ;x-dump-hex JSR2
	;chn #0020 ADD2 #0004 ;x-dump-hex JSR2
	;phr #0004 ;x-dump-hex JSR2
	;t-nl JMP2
@x-dump-hex ( addr* n* -- : sur une ligne )
	;x-n STA2 ;x-a STA2
	#0000 ;t-i STA2
	&l
		;x-a LDA2 ;t-i LDA2 ADD2 LDA ;t-hex JSR2 #20 .Console/write DEO
		;t-i LDA2 INC2 ;t-i STA2
		;t-i LDA2 ;x-n LDA2 LTH2 ;&l JCN2
	#2f .Console/write DEO #20 .Console/write DEO
JMP2r
@t-i $2 @x-n $2 @x-a $2 @x-p $2 @x-c $1 @x-k $1 @x-r $1 @x-w $1 @x-h $1 @x-m $1 @x-ti $1 @x-tn $1 @x-tv $1
"""


def build(work, load_only):
    src = (HERE / "tracker.tal").read_text()
    marker = "|0100\n@on-reset"
    assert marker in src
    # trigger, note-off et draw-char deviennent des versions de test ; les vraies restent sous *-real
    for name in ("trigger", "note-off", "draw-char"):
        src, n = re.subn(r"^@%s(?=[ \n])" % name, "@%s-real" % name, src, flags=re.M)
        assert n == 1, name
    head, rest = DRIVER.split("@@FULLBODY")
    full, rest = rest.split("@@LOADBODY")
    load, helpers = rest.split("@@HELPERS")
    body = load.replace("@test-load", "@test-main") if load_only else full
    test = src.replace(marker, head + body + helpers + "\n@on-reset")
    if load_only:
        test = test.replace('"song.cct', '"' + Path(load_only).name)
    (work / "selftest.tal").write_text(test)
    asm = subprocess.run([str(ROOT / "uxncli"), str(ROOT / "drifloon.rom")],
                         input=test.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work)
    (work / "selftest.rom").write_bytes(asm.stdout)
    for l in asm.stderr.decode().splitlines():
        if "Unused" not in l and "Assembled" not in l:
            print("assembleur :", l)
    run = subprocess.run([str(ROOT / "uxncli"), "selftest.rom"], cwd=work,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return run.stdout.decode()


# ------------------------------------------------------------------ modele de reference
SONG = {(0, 0): 0x00, (0, 1): 0x01, (0, 2): 0x7f, (0, 3): 0x05, (1, 0): 0x02, (3, 0): 0x02}
CHAINS = {0x00: {0: (0x00, 0x00), 1: (0x01, 0x02), 2: (0x7f, 0xfe)}, 0x01: {0: (0x02, 0x0c)},
          0x02: {0: (0x03, 0x00)}, 0x05: {0: (0x05, 0x00), 3: (0x04, 0x01)},
          0x7f: {0: (0x06, 0x00), 15: (0x7f, 0x05)}}
PHRASES = {0x00: {0: (0x30, 0), 4: (0x34, 1), 8: (0xfe, 0xff), 15: (0x5f, 3)},
           0x01: {0: (0x3c, 3), 6: (0x40, 1)}, 0x02: {0: (0x24, 0), 7: (0x2c, 0)},
           0x03: {0: (0x39, 1)}, 0x04: {2: (0x40, 2)}, 0x05: {1: (0x30, 0), 5: (0x32, 2)},
           0x06: {3: (0x6b, 0), 9: (0x1e, 5)}, 0x7f: {15: (0x6b, 7)}}


def expected_play(ticks):
    """Comme CCT : 4 pistes independantes, ligne de phrase (prow) commune ; une chaine s'arrete a sa
    premiere ligne sans phrase ; apres la chaine, une case de song vide (ou la fin) ramene au debut du
    bloc de cases non vides qui vient de finir ; une piste dont la case de depart est vide reste muette."""
    st = [{"sr": 0, "cr": 0, "on": SONG.get((0, t), 0xff) != 0xff} for t in range(4)]

    def cell(t, sr=None):
        return SONG.get((st[t]["sr"] if sr is None else sr, t), 0xff)

    log = []
    prow = 0
    for k in range(ticks):
        ev = []
        for t in range(4):
            if not st[t]["on"]:
                continue
            ch = cell(t)
            ph, tr = CHAINS.get(ch, {}).get(st[t]["cr"], (0xff, 0))
            if ph == 0xff:
                continue
            note, inst = PHRASES.get(ph, {}).get(prow, (0xff, 0xff))
            if note == 0xff:
                continue
            if note == 0xfe:
                ev.append("O%02X" % t)
                continue
            n = note + (tr - 256 if tr >= 0x80 else tr)
            if not 0 <= n < 0x6c:
                continue
            ev.append("T%02X %02X %02X" % (t, n, 0 if inst == 0xff else inst))
        log.append(ev)
        prow += 1
        if prow == 16:
            prow = 0
            for t in range(4):
                if not st[t]["on"]:
                    continue
                nxt = st[t]["cr"] + 1
                ch = cell(t)
                if nxt < 16 and CHAINS.get(ch, {}).get(nxt, (0xff, 0))[0] != 0xff:
                    st[t]["cr"] = nxt
                    continue
                st[t]["cr"] = 0
                sr = st[t]["sr"] + 1
                if sr >= 64 or cell(t, sr) == 0xff:
                    while sr > 0:
                        sr -= 1
                        if cell(t, sr) == 0xff:
                            sr += 1
                            break
                st[t]["sr"] = sr
    return log


def split_sections(out):
    secs = {}
    cur = None
    for line in out.split("\n"):
        if line.startswith("@") and len(line) == 2:
            cur = line[1]
            secs[cur] = []
        elif cur is not None:
            secs[cur].append(line)
        else:
            secs.setdefault("0", []).append(line)
    # la section avant le premier repere (donnees de la sauvegarde) porte le nom "0"
    return secs


def main():
    args = [a for a in sys.argv[1:] if a != "-v"]
    work = Path(args[0])
    work.mkdir(parents=True, exist_ok=True)
    load_only = args[1] if len(args) > 1 else None
    out = build(work, load_only)
    if load_only:
        sys.stdout.write(out)
        return
    secs = split_sections(out)
    bad = []

    # 1. aller-retour : (A) avant la sauvegarde == (B) apres rechargement
    a = [l for l in secs["A"] if l.strip()]
    b = [l for l in secs["B"] if l.strip()]
    if not any(l.startswith("SAVED") for l in a):
        bad.append("sauvegarde : pas de message SAVED")
    if not any(l.startswith("LOADED") for l in b):
        bad.append("chargement : pas de message LOADED")
    hexd = set("0123456789ABCDEF")
    a = [l for l in a if len(l) in (5, 64) and set(l) <= hexd | {" "}]
    b = [l for l in b if len(l) in (5, 64) and set(l) <= hexd | {" "}]
    print("aller-retour : %d lignes avant, %d apres" % (len(a), len(b)))
    if a[0] != "04 05" or a[1][:8] != "00017F05":
        bad.append("en-tete inattendu : %r %r" % (a[0], a[1][:8]))
    if a != b:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                bad.append("difference ligne %d :\n  %s\n  %s" % (i, x, y))
                break
        else:
            bad.append("longueurs differentes %d %d" % (len(a), len(b)))
    else:
        print("aller-retour : identique")

    # 2. lecture
    play = secs["P"][:100]
    exp = expected_play(100)
    got2 = []
    for l in play:
        evs = re.findall(r"T[0-9A-F]{2} [0-9A-F]{2} [0-9A-F]{2}|O[0-9A-F]{2}", l)
        got2.append(evs)
    if got2 != exp:
        for i, (x, y) in enumerate(zip(got2, exp)):
            if x != y:
                bad.append("lecture, tick %d :\n  obtenu %s\n  attendu %s" % (i, x, y))
                break
    else:
        print("lecture : %d ticks identiques au modele (%d notes)" % (len(exp), sum(len(e) for e in exp)))

    if any(l.startswith("!!") for l in secs["P"]):
        bad.append("lecture : pile desequilibree")

    # 3. ecrans
    screens = {}
    cur = None
    for line in secs["S"]:
        if line.startswith("!!"):
            bad.append("pile desequilibree")
        m = re.match(r"@N(..)$", line)
        if m:
            cur = int(m.group(1), 16)
            screens[cur] = []
        elif cur is not None and len(line) >= 0:
            screens[cur].append(line)
    for n in range(13):
        rows = screens.get(n, [])[:24]
        if len(rows) < 24:
            bad.append("ecran %d : %d lignes" % (n, len(rows)))
            continue
        wide = [r for r in rows if len(r.rstrip()) > 32]
        if wide:
            bad.append("ecran %d : ligne de plus de 32 colonnes : %r" % (n, wide[0]))
    for n, w in ((8, "OVERWRITE"), (9, "LOAD: DISCARD"), (10, "NEW: DISCARD")):
        if w not in "\n".join(screens.get(n, [])):
            bad.append("ecran %d : %r absent" % (n, w))
    for n, w in ((11, "tong") if False else (11, "song"), (12, "LOAD FILE"), (12, "song")):
        if w not in "\n".join(screens.get(n, [])):
            bad.append("ecran %d : %r absent" % (n, w))
    want = {0: ["SONG", "T1", "T4", "SCPI"], 1: ["CHAIN", "PH", "TR"],
            2: ["PHRASE", "NOTE", "IN"], 3: ["INSTRUMENT", "PRESET", "SQUARE"],
            13: ["PAGE 2/3", "PRESET"], 14: ["PAGE 3/3", "TAB NEXT"], 4: ["SAVE", "LOAD"],
            5: ["SETTINGS", "A/B SWAP", "KEYBOARD", "HELP"], 6: ["GROOVE", "SPEED"],
            7: ["HELP", "PAGE 1/3", "START"]}
    for n, words in want.items():
        text = "\n".join(screens.get(n, []))
        for w in words:
            if w not in text:
                bad.append("ecran %d : %r absent" % (n, w))
    if "-v" in sys.argv:
        for n in range(8):
            print("--- ecran %d" % n)
            print("\n".join(r.rstrip() for r in screens.get(n, [])[:24]))
    print("ecrans : %d dessines" % len(screens))

    # 4. manette
    fst = []
    for l in secs["I"]:
        m = re.search(r"F [0-9A-F]{2} \S+$", l)
        if m:
            fst.append(m.group(0))
    if len(fst) != 4 or fst[0] != "F 00 tong.cct" or not re.fullmatch(r"F 00 [a-z]{8}\.cct", fst[1]) \
            or fst[2] != "F 05 " + fst[1][5:] or fst[3] != "F 02 song.cct":
        bad.append("noms : %r" % fst)
    states = []
    for l in secs["I"]:
        m = re.search(r"[SN] [0-9A-F]{2} .*$", l)
        if m:
            states.append(m.group(0))
    extra = []
    for l in secs["I"]:
        m = re.match(r"[PH] [0-9A-F]{2} .*$", l.strip())
        if m:
            extra.append(m.group(0))
    exp_extra = ["P 03 1B 0001 XRI BASS", "P 03 1B 0004 PULSE PWM", "P 03 01 0004 SQUARE",
                 "P 03 1B 0004 PULSE PWM", "P 03 1B 0002 SAW LEAD", "P 03 1B 0003 SAW LEAD",
                 "H 07 01", "H 07 02", "H 07 02", "H 07 01", "H 07 00", "H 05 00"]
    if extra != exp_extra:
        bad.append("preset / aide :\n  obtenu  %s\n  attendu %s" % (extra, exp_extra))
    print("manette :", *states, sep="\n  ")
    exp_states = ["S 00 00 10 FF FF / FF 00 FF 00 / FF FF FF FF /",
                  "S 01 00 10 FF FF / 10 00 FF 00 / FF FF FF FF /",
                  "S 02 00 10 FF FF / 10 00 FF 00 / 31 00 FF FF /",
                  "S 02 00 10 FF FF / 10 00 FF 00 / FF FF FE FF /",
                  "N 02 00 10 01 FF / 10 00 00 00 / FF FF 31 00 /",
                  "S 00 00 10 01 FF / 10 00 FF 00 / FF FF FE FF /",
                  "S 04 00 10 01 FF / 10 00 FF 00 / FF FF FE FF /"]
    norm = [re.sub(r"\s+", " ", s).strip() for s in states]
    exp_n = exp_states
    if norm != exp_n:
        for i, (x, y) in enumerate(zip(norm, exp_n)):
            if x != y:
                bad.append("manette, etat %d :\n  obtenu  %s\n  attendu %s" % (i, x, y))
                break
        else:
            bad.append("manette : %d etats au lieu de %d" % (len(norm), len(exp_n)))

    for m in bad:
        print("ECHEC :", m)
    print("PASS" if not bad else "FAIL")
    sys.exit(1 if bad else 0)


main()
