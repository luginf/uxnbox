#!/bin/sh
# Compare l'audio de audio.c avec le code de reference (ancien depot uxn, commit 2903488).
# Necessite git et gcc, et un acces reseau pour cloner le depot.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
C=$HERE/..
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
git clone -q https://git.sr.ht/~rabbits/uxn "$W/uxn"
R() { git -C "$W/uxn" show "2903488:src/devices/audio.$1"; }
{
    cat <<'EOT'
typedef unsigned char Uint8; typedef signed char Sint8; typedef unsigned short Uint16; typedef signed short Sint16; typedef unsigned int Uint32;
#define PEEK2(d) ((d)[0] << 8 | (d)[1])
struct { Uint8 ram[65536]; } uxn;
extern int ref_done[4];
#define audio_render ref_audio_render
#define audio_start ref_audio_start
#define audio_get_vu ref_get_vu
#define audio_get_position ref_get_position
#define audio_finished_handler ref_finished
typedef signed int Sint32;
Uint8 ref_get_vu(int); Uint16 ref_get_position(int); int ref_audio_render(int,Sint16*,Sint16*); void ref_audio_start(int,Uint8*); void ref_finished(int);
EOT
    R h | grep '^#define'
    R c | grep -v '#include'
    echo 'void ref_finished(int i) { ref_done[i] = 1; }'
} > "$W/ref.c"
gcc -O1 -w -I"$C" -o "$W/audiotest" "$HERE/audio_test.c" "$W/ref.c" "$C/audio.c" "$C/uxn.c"
"$W/audiotest"
