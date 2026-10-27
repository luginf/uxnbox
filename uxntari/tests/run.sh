#!/bin/sh
# Teste le coeur et les peripheriques portables sur l'hote.
# Necessite : gcc, python3, git, uxnasm. Les ROM de test et le code de
# reference viennent de uxn11 (UXN11=dossier existant, sinon clone temporaire).
# Usage : tests/run.sh [nombre de ROM aleatoires]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
N=${1:-100}
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
UXN11=${UXN11:-$W/uxn11}
[ -d "$UXN11" ] || git clone -q --depth 1 https://git.sr.ht/~rabbits/uxn11 "$UXN11"

gcc -O1 -Wall -Wextra -std=c99 -pedantic -D_POSIX_C_SOURCE=200809L -o "$W/HARNESS" \
    "$ROOT"/uxn.c "$ROOT"/dev.c "$ROOT"/vid.c "$ROOT"/file.c "$ROOT"/audio.c "$HERE"/harness.c
python3 -I "$HERE/mkref.py" "$UXN11/src/uxn11.c" "$W/refscreen.c"
gcc -O1 -w -D_GNU_SOURCE "$W/refscreen.c" -o "$W/refscreen" -lutil
H=$W/HARNESS
fails=0
check() { # nom, sortie : au moins un "pass" et aucun "fail"
    if echo "$2" | grep -q fail || ! echo "$2" | grep -q pass; then echo "ECHEC $1"; echo "$2" | grep fail | head -3; fails=$((fails+1)); else echo "ok    $1"; fi
}

for t in opctest system; do
    uxnasm "$UXN11/etc/tests/$t.tal" "$W/$t.rom" >/dev/null
    check "$t" "$("$H" -n "$W/$t.rom" 2>&1)"
done
uxnasm "$UXN11/etc/tests/datetime.tal" "$W/datetime.rom" >/dev/null
# la date affichee doit etre celle de la machine (jour de l'annee a partir de 0)
out=$("$H" -n "$W/datetime.rom" 2>&1)
if echo "$out" | grep -q "^$(date +%Y-%m-%d)" && echo "$out" | grep -q "day of the year is: $(( $(date +%j | sed 's/^0*//') - 1 ))"; then echo "ok    datetime"; else echo "ECHEC datetime"; echo "$out"; fails=$((fails+1)); fi
uxnasm "$UXN11/etc/tests/console.tal" "$W/console.rom" >/dev/null
check console "$(printf ghi | "$H" "$W/console.rom" abc def 2>&1)"
uxnasm "$UXN11/etc/tests/file.tal" "$W/file.rom" >/dev/null
mkdir "$W/files" && (cd "$W/files" && check file "$("$H" -n "$W/file.rom" 2>&1)")

# expansion : remplissage et copie entre banques, banque 1 chargee depuis la fin de la ROM
uxnasm "$HERE/expansion.tal" "$W/exp.rom" >/dev/null
python3 -I -c "import sys; b=open(sys.argv[1],'rb').read(); open(sys.argv[1],'wb').write(b+bytes(0xff00-len(b))+b'QRST')" "$W/exp.rom"
if [ "$("$H" -n "$W/exp.rom" 2>&1)" = Qz ]; then echo "ok    expansion (banques)"; else echo "ECHEC expansion"; fails=$((fails+1)); fi

for t in screen screen.auto screen.bounds screen.pixel; do
    uxnasm "$UXN11/etc/tests/$t.tal" "$W/$t.rom" >/dev/null
    "$H" -n -f 3 -d "$W/$t.mine" "$W/$t.rom" >/dev/null 2>"$W/err" || true
    "$W/refscreen" "$W/$t.rom" 3 > "$W/$t.ref"
    if python3 -I "$HERE/cmpdump.py" "$W/$t.mine" "$W/$t.ref" >/dev/null && [ ! -s "$W/err" ]; then echo "ok    $t"; else echo "ECHEC $t"; fails=$((fails+1)); fi
done

i=1
bad=0
while [ $i -le "$N" ]; do
    python3 -I "$HERE/genrom.py" $i "$W/r.rom"
    "$H" -n -d "$W/r.mine" "$W/r.rom" >/dev/null 2>"$W/err" || true
    "$W/refscreen" "$W/r.rom" 0 > "$W/r.ref"
    if ! python3 -I "$HERE/cmpdump.py" "$W/r.mine" "$W/r.ref" >/dev/null || [ -s "$W/err" ]; then echo "ECHEC rom aleatoire $i"; bad=$((bad+1)); fi
    i=$((i+1))
done
[ $bad -eq 0 ] && echo "ok    $N roms aleatoires (ecran moyenne resolution)" || fails=$((fails+1))
python3 -I "$HERE/genrom.py" 7 "$W/m.rom" 640 400
"$H" -1 -n -d "$W/m.mine" "$W/m.rom" 2>&1 | grep mismatch && fails=$((fails+1)) || echo "ok    ecran monochrome coherent"

# basse resolution (320x200) : memes images que la reference
i=1
bad=0
while [ $i -le 20 ]; do
    python3 -I "$HERE/genrom.py" $i "$W/l.rom" 320 200
    "$H" -4 -n -d "$W/l.mine" "$W/l.rom" >/dev/null 2>"$W/err" || true
    "$W/refscreen" "$W/l.rom" 0 > "$W/l.ref"
    if ! python3 -I "$HERE/cmpdump.py" "$W/l.mine" "$W/l.ref" >/dev/null || [ -s "$W/err" ]; then echo "ECHEC rom basse resolution $i"; bad=$((bad+1)); fi
    i=$((i+1))
done
[ $bad -eq 0 ] && echo "ok    20 roms aleatoires (basse resolution)" || fails=$((fails+1))

[ $fails -eq 0 ] && echo "TOUT PASSE" || { echo "$fails ECHEC(S)"; exit 1; }
