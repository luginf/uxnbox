#!/bin/sh
# Compile tests/cct_check.cpp contre les objets deja compiles de ChooChooTracker
# (make -C tracker -f Makefile.test les produit dans build/tests/obj) et lui
# fait lire le fichier donne en argument.
#   CCT_DIR : racine du depot ChooChooTracker (defaut ~/src/forks/Choochootracker)
set -e
CCT_DIR=${CCT_DIR:-$HOME/src/forks/Choochootracker}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${TMPDIR:-/tmp}/uxntracker-cct-check
mkdir -p "$OUT"
OBJ=$CCT_DIR/tracker/build/tests/obj/up
[ -d "$OBJ" ] || { echo "objets CCT introuvables dans $OBJ" >&2; exit 2; }
# pd_voice.o est souvent perime par rapport aux en-tetes et inutile pour charger un projet
LIBO=$(cd "$OBJ" && find . -name '*.o' | grep -v pd_voice | sed "s|^\.|$OBJ|")
INC="-I$CCT_DIR/tracker -I$CCT_DIR/tracker/src -I$CCT_DIR/chipnomad_lib -I$CCT_DIR/chipnomad_lib/chips \
 -I$CCT_DIR/chipnomad_lib/link -I$CCT_DIR/chipnomad_lib/external/ayumi -I$CCT_DIR/chipnomad_lib/external/gb_apu \
 -I$CCT_DIR/chipnomad_lib/external/mutable -I$CCT_DIR/tracker/external"
c++ -std=c++17 -DTEST $INC -c "$HERE/cct_check.cpp" -o "$OUT/cct_check.o"
c++ "$OUT/cct_check.o" $LIBO -lm -pthread -o "$OUT/cct_check"
"$OUT/cct_check" "$1"
