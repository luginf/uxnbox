# uxntracker

Un petit tracker 4 voies pour [Varvara/Uxn](https://wiki.xxiivv.com/site/uxntal.html), en Uxntal.
Quatre canaux, 8 instruments (un carré façon AY et 7 instruments de type SID), et un fichier `.cct` au
même format texte que [ChooChooTracker](https://github.com/luginf/Choochootracker) : ce qui est
enregistré ici se rouvre dans CCT (4 pistes, instruments AY1 et SID), et un `.cct` écrit par CCT se charge ici.

```
make            # assemble tracker.rom
make run        # lance avec uxn2 en zoom x2 (song.cct est lu/écrit dans le dossier courant)
make run11      # lance avec uxn11 (X11, sans audio : pour le son, utiliser uxn2)
make test       # aller-retour sauvegarde / rechargement sous uxncli, sans écran
make cct-check  # fait relire le fichier du test par le vrai chargeur de CCT (voir plus bas)
make data       # régénère police, table des périodes et textes du .cct (tools/gen_data.py)
```

L'écran fait 384x240. Le ROM tient en 15 Ko.

## Utilisation

Le morceau est une liste de **motifs** (jusqu'à 32), chacun de 16 lignes sur 4 voix.
Le tempo est un nombre de ticks à 50 Hz par ligne (comme CCT, 06 par défaut).

| Touche | Action |
|---|---|
| Flèches | déplacer le curseur (voix / ligne) |
| rangée de touches de piano | poser une note (et la jouer), puis descendre d'une ligne |
| `-` / `=`, ou Maj + haut / bas | octave -1 / +1 (0 à 7) |
| Maj + gauche / droite | instrument précédent / suivant (0 à 7) |
| Tab | bascule grille / éditeur d'instrument |
| `'` | note OFF (coupe la voix), puis descendre d'une ligne |
| Retour arrière / Suppr | effacer la case |
| Espace ou Home | lecture / arrêt (depuis le haut du motif courant) |
| Ctrl + gauche / droite | motif précédent / suivant (à la fin, ajoute un motif vide) |
| Ctrl + haut / bas | tempo +1 / -1 (ticks par ligne) |
| Ctrl + retour arrière | supprimer le motif courant |
| `;` | disposition clavier AZERTY / QWERTY |
| Entrée ou Échap | menu fichier (voir plus bas) |

Pendant la lecture l'affichage suit le morceau ; on peut éditer en jouant.

Les touches de piano, sur deux rangées (la rangée affichée à droite est celle de la disposition active) :

```
QWERTY  bas  : z s x d c v g b h n j m    haut : q 2 w 3 e r 5 t 6 y 7 u
AZERTY  bas  : w s x d c v g b h n j ,    haut : a . z . e r . t . y . u
```

Chaque rangée est une octave chromatique de C à B ; la rangée du haut est l'octave au-dessus.
En AZERTY les dièses de la rangée du haut ne sont pas des touches ASCII sans Maj, ils manquent.

## Menu fichier

Entrée ou Échap ouvre le menu : **NAME** (nom du fichier, modifiable : a-z, 0-9, `.`, `_`, `-`, 15 caractères),
**SAVE**, **LOAD**, **NEW SONG**, **CLOSE**. Haut / bas pour choisir, Entrée pour valider, Échap pour fermer.
Plus aucune touche ne charge ou n'enregistre directement. Un `*` à côté du titre indique des modifications
non enregistrées ; LOAD et NEW demandent alors confirmation (Y / N), et SAVE demande confirmation si le
fichier existe déjà.

## Instruments

Chaque case porte une note et un numéro d'instrument (celui qui est sélectionné au moment de la saisie,
affiché `INS` en haut). L'instrument 0 est le carré AY (tenue). Les instruments 1 à 7 sont de type SID,
modifiables dans la vue Tab : forme d'onde (triangle, dent de scie, impulsion, bruit, combinables par
ET logique), largeur d'impulsion, modulation de largeur (profondeur, vitesse), enveloppe ADSR logicielle
avec vrai niveau de sustain, durée de gate, arpège. Haut / bas choisit le champ, gauche / droite change la
valeur, Ctrl + gauche / droite fait un grand pas. Sept préréglages sont fournis (PULSE PWM, SAW LEAD,
TRI BASS, NOISE HAT, PLUCK, PAD, ARP PULSE).

Limites : Varvara fige la hauteur à chaque déclenchement (demi-tons entiers), donc ni vibrato, ni glissando,
ni fréquence fixe. Filtre, ring, sync et les autres paramètres SID sont conservés tels quels dans le
fichier mais ne s'entendent pas ici.

## Son

Les 4 voix sont les 4 canaux Audio de Varvara. L'ADSR matériel est à 0 (la note tient jusqu'à la suivante
ou jusqu'à OFF) ; enveloppe, forme d'onde et largeur d'impulsion des instruments SID sont réécrites dans le
tampon d'échantillon à 50 Hz. La numérotation est celle de CCT : `C-4` = 261,6 Hz et
`A-4` = 440 Hz (pitch Varvara = indice de la table + 12). Varvara ne joue pas au-delà de B-7 : `C-8`
et plus sont stockés et sauvegardés mais restent muets.

## Correspondance avec le format .cct

Le fichier est écrit en `ChooChooTracker Module 11.0`, en-tête copié de ce que produit CCT :
`Chips count: 4` (dans ce fork, une puce = une piste), AY8910 à 1773400 Hz, table de périodes 12TET
(identique à celle de CCT, vérifiée), `Frame rate: 50`.

- Motif `s`, voix `v` : chaîne = phrase = numéro `4*s + v`. Le song contient ces numéros, ou `--` si
  la voix est vide dans ce motif (on n'écrit alors ni chaîne ni phrase).
- Une chaîne = une seule ligne qui pointe sa phrase (transposition 00).
- Une phrase = 16 lignes `C-4 00 -- --- 00 --- 00 --- 00`. Les OFF sont `OFF -- -- ...`.
- Groove 0 : le tempo (deux fois la même valeur).
- Instrument 0 : AY1 « Square » (tenue, mixer 01). Instruments 1 à 7 : type 27 (SID), 25 paramètres.
- Chaque ligne de phrase porte l'instrument de la case (`--` sur les OFF et cases vides).

Au chargement on lit : les lignes du song (quatre premières colonnes, 32 lignes), la **première
ligne** de chaque chaîne, les **notes** de chaque phrase, et la première valeur du groove 0.
Pour les instruments 0 à 7, seuls les types 1 (AY1) et 27 (SID) sont repris ; un autre type devient un
carré AY. Tout le reste est ignoré : volumes, FX, tables, transpositions de chaîne, lignes de chaîne au-delà
de la première, pistes au-delà de la quatrième, noms de plus de 9 caractères (tronqués).
Réenregistrer un fichier CCT riche depuis ici en perd donc ces parties.

## Vérification

- `make test` : le ROM de test (`tests/selftest.py`, construit à partir de `tracker.tal`) remplit un
  morceau, écrit `song.cct`, vide la mémoire, recharge et compare octet par octet ; vérifie aussi la
  suppression d'un motif ; les 8 instruments (dont un paramètre et un nom modifiés) font aussi l'aller-retour. Il peut aussi lire un `.cct` existant : `python3 tests/selftest.py <dossier> <fichier.cct>`.
- `make cct-check` : `tests/cct_check.cpp` appelle `projectLoad` de ChooChooTracker sur le fichier écrit
  et affiche ce que CCT en a compris. Nécessite les objets compilés de CCT (`CCT_DIR`, défaut
  `~/src/forks/Choochootracker`, après `make -f Makefile.test` dans `tracker/`).
- `make cct-check` affiche aussi les 8 instruments : CCT accepte les blocs SID (`validSID`) et relit
  l'instrument de chaque case.
- Contrôlé sous Xvfb (xdotool) avec uxn2 : menu (enregistrer, charger, nouveau avec confirmation), vue
  instruments, changement d'octave, rechargement.

Le rendu sonore n'a pas été écouté (audio factice) : enveloppe, PWM et arpège sont implémentés mais non
validés à l'oreille. uxn11 n'a pas d'audio, il faut uxn2.

## Fichiers

| Fichier | Rôle |
|---|---|
| `tracker.tal` | le programme ; le bloc entre les marqueurs `GENERATED` est produit par `tools/gen_data.py` |
| `tools/gen_data.py` | police 5x7, table des périodes AY, textes fixes du `.cct` |
| `tests/selftest.py` | test d'aller-retour sous uxncli |
| `tests/cct_check.cpp`, `tests/cct_check.sh` | relecture par le chargeur de CCT |
