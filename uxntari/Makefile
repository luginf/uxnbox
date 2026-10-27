# Atari ST : make            (m68k-atari-mint-gcc)
# Hote     : make host-test  (gcc, voir tests/run.sh)
CC = m68k-atari-mint-gcc
CFLAGS = -O2 -Wall -Wextra -Wno-unused-value -std=gnu99
SRC = uxn.c dev.c vid.c file.c audio.c

UXN.PRG: st.c $(SRC) uxn.h dev.h vid.h file.h audio.h
	$(CC) $(CFLAGS) -s -o $@ st.c $(SRC)

host-test:
	tests/run.sh

audio-test:
	tests/audio.sh

clean:
	rm -f UXN.PRG
