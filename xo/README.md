# xo - Morpion / Tic-tac-toe

Deux versions d'un morpion jouable contre l'ordinateur sur la plateforme [Varvara/Uxn](https://wiki.xxiivv.com/site/uxntal.html) de Hundredrabbits. Ce dossier est un fork de https://git.sr.ht/~bouncepaw/uxnerie (variante : on peut jouer contre l'ordinateur).

| ROM | Grille | Victoire | Écran |
|---|---|---|---|
| `xo.rom` | 3×3 | 3 alignés | 107×107 |
| `xo5.rom` | 5×5 | **4 alignés** | 128×128 |

## Lancer

```sh
make run3   # 3×3 (uxn2, zoom ×2)
make run    # 5×5 (uxn2, zoom ×2)
```

Ou directement, depuis ce dossier :

```sh
../uxn11 xo.rom
../uxn2 -2x xo5.rom   # zoom ×2 (-3x pour ×3)
```

F1 pendant le jeu cycle entre ×1 / ×2 / ×3.

## Compiler depuis les sources

```sh
make        # compile xo.rom et xo5.rom
make clean  # supprime les ROMs
```

Prérequis : `../uxncli` et `../drifloon.rom` (voir le README du dossier principal).

## Jouer

**Clavier**

| Touche | Action |
|---|---|
| ←↑→↓ | Déplacer le curseur |
| `A` / `Espace` | Poser une pièce |

**Souris**

- Survoler une case : déplace le curseur
- Clic gauche sur une case libre : pose la pièce
- Clic sur le bouton **R** (bas droite) : redémarrer à tout moment

## Règles

- Le joueur joue **X**, l'IA joue **O**, X commence toujours
- **3×3** : aligner 3 symboles identiques (ligne, colonne ou diagonale)
- **5×5** : aligner **4** symboles identiques
- Match nul si le plateau est rempli sans vainqueur (symbole triste affiché)

## IA

L'IA suit une heuristique par ordre de priorité :

1. **Gagner** : compléter un alignement gagnant
2. **Bloquer** : empêcher le joueur de gagner
3. **Centre** : prendre la case centrale
4. **Coin** : prendre un coin libre
5. **Case libre** : n'importe quelle case disponible

## Architecture technique

Écrit en Uxntal, assemblé avec [drifloon](https://git.sr.ht/~rabbits/uxn11).

- Deux couches d'affichage Varvara : BG (plateau + pièces) et FG (curseur souris)
- Détection d'entrée souris via front montant sur `Mouse/state`
- Le bouton R est actif en permanence, même en fin de partie

## Fichiers

```
xo.tal          source 3×3
xo5.tal         source 5×5
xo.rom          ROM compilée 3×3
xo5.rom         ROM compilée 5×5
Makefile
```

## Licence

AGPLv3-only, voir `LICENSE`.
