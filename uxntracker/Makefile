ROM    = tracker.rom
SRC    = tracker.tal
UXN2   = ../uxn2
UXN11  = ../uxn11
UXNCLI = ../uxncli
ASM    = ../drifloon.rom
WORK   = /tmp/uxntracker-test

.PHONY: all run run11 data test cct-check clean

all: $(ROM)

$(ROM): $(SRC) $(ASM)
	cat $(SRC) | $(UXNCLI) $(ASM) > $(ROM)

run: $(ROM)
	$(UXN2) -2x $(ROM)

run11: $(ROM)
	$(UXN11) $(ROM)

# regenere police, table des periodes et textes du .cct dans tracker.tal
data:
	python3 tools/gen_data.py

# aller-retour sauvegarde / rechargement sous uxncli, sans ecran
test: $(ROM)
	python3 tests/selftest.py $(WORK)

# fait relire le fichier du test par le vrai chargeur de ChooChooTracker (voir README)
cct-check: test
	sh tests/cct_check.sh $(WORK)/song.cct

clean:
	rm -f $(ROM)
