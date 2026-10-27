ROM    = defender.rom
SRC    = defender.tal
UXN11  = ../uxn11
UXN2   = ../uxn2
UXNCLI = ../uxncli
ASM    = ../drifloon.rom

.PHONY: all run run2 clean sprite sheet reimport snd

all: $(ROM)

$(ROM): $(SRC) $(ASM)
	cat $(SRC) | $(UXNCLI) $(ASM) > $(ROM)

sndtest.rom: sndtest.tal $(ASM)
	cat sndtest.tal | $(UXNCLI) $(ASM) > sndtest.rom

snd: sndtest.rom
	$(UXN2) -2x sndtest.rom

run: $(ROM)
	$(UXN2) -2x $(ROM)

run2: $(ROM)
	$(UXN2) -2x $(ROM)

clean:
	rm -f $(ROM) sndtest.rom

sprite:
	$(UXN2) -2x nasu.rom

sheet:
	python3 tools/spritesheet.py export

reimport:
	python3 tools/spritesheet.py import