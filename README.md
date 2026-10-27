# uxnbox

Petits projets autour de la plateforme [Varvara/Uxn](https://wiki.xxiivv.com/site/uxntal.html) de Hundredrabbits.

| Dossier | Contenu |
|---|---|
| [`xo/`](xo/) | Morpion 3×3 et 5×5 contre l'ordinateur (Uxntal) |
| [`defender/`](defender/) | Shoot'em up horizontal (Uxntal) |
| [`uxntari/`](uxntari/) | Une VM uxn/varvara pour Atari ST, en C (`UXN.PRG` fourni) |
| [`uxntracker/`](uxntracker/) | Tracker 4 voies (carré AY + instruments type SID), lit et écrit le format `.cct` de ChooChooTracker (Uxntal) |

## Outils à la racine

| Fichier | Description |
|---|---|
| `uxn11` | VM graphique (X11), compilée depuis [`~rabbits/uxn11`](https://git.sr.ht/~rabbits/uxn11) |
| `uxn2` | VM graphique (SDL2), source dans `src/uxn2.c` (fork de [`~rabbits/uxn2`](https://git.sr.ht/~rabbits/uxn2) avec les options `-2x` / `-3x` pour le zoom) |
| `uxncli` | VM sans affichage (terminal), compilée depuis [`~rabbits/uxncli`](https://git.sr.ht/~rabbits/uxncli) |
| `drifblim.rom` | Assembleur pour uxn11 / uxn2 (fichiers en entrée et sortie) |
| `drifloon.rom` | Assembleur pour uxncli (stdin vers stdout) |

Chaque projet se compile avec son propre `Makefile`, qui utilise ces outils (`../uxncli`, `../drifloon.rom`).

## Lancer une ROM

```sh
./uxn11 rom.rom
./uxn2 -2x rom.rom    # zoom ×2 (-3x pour ×3)
```

## Assembler un fichier .tal

```sh
./uxn11 drifblim.rom source.tal sortie.rom                  # avec affichage
cat source.tal | ./uxncli drifloon.rom > sortie.rom         # sans affichage (ne pas utiliser 2>&1)
```

## Recompiler les VM

```sh
cc -DNDEBUG -O2 -g0 -s src/uxn11.c -lX11 -lutil -o uxn11                                   # libx11-dev
cc $(sdl2-config --cflags) -DNDEBUG -O2 -g0 -s src/uxn2.c -o uxn2 $(sdl2-config --libs)    # libsdl2-dev
cc -DNDEBUG -O3 -g0 -s src/uxncli.c -o uxncli
```
