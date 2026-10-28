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
make ds         # variante Nintendo DS : tracker-ds.rom, écran 256x192 (make run-ds pour l'essayer en x3)
make data       # régénère police, table des périodes et textes du .cct (tools/gen_data.py)
```

L'écran fait 384x240. Le ROM tient en 15 Ko. La variante DS (`tools/make_ds.py`) fait 256x192 : lignes de 8 px et
sans le panneau d'aide, le reste est identique. Elle n'a été vue que sous uxn2, pas sur une vraie DS.

## Utilisation

Le morceau est une liste de **motifs** (jusqu'à 32), chacun de 16 lignes sur 4 voix.
Le tempo est un nombre de ticks à 50 Hz par ligne (comme CCT, 06 par défaut).

Deux manières de jouer : la **manette** (croix, A, B, Select, Start) et le **clavier** (mode jazz).
Les commandes de la manette suivent celles de [ChooChooTracker](https://github.com/luginf/Choochootracker/blob/main/docs/USER_MANUAL.md)
(A = EDIT, B = OPT, Start = PLAY, Select = SELECT). Au clavier : Alt = A, Ctrl = B, Maj = Select, Home = Start
(uxn ne voit pas les touches X et Z que CCT utilise par défaut).

**A et B échangés** : les émulateurs envoient Ctrl pour A et Alt pour B, mais A est à droite dans CCT et sur une
manette. Le tracker échange donc les deux boutons (`tracker.rom` démarre ainsi, la touche `\` ou la ligne **A/B SWAP** du menu fichier bascule). Cet
échange vaut pour tout ce qui arrive en entrée, y compris une vraie manette : la variante DS démarre sans échange.

| Manette | Action | Équivalent CCT |
|---|---|---|
| croix | déplacer le curseur | idem |
| A (appui bref) | case vide : pose la dernière note ; case pleine : la rejoue | tap EDIT |
| A + gauche / droite | note -1 / +1 demi-ton | EDIT + gauche / droite |
| A + haut / bas | note +1 / -1 octave | EDIT + haut / bas |
| A + B | case vide : note OFF ; sinon efface la case | EDIT + OPT |
| B + haut / bas | motif précédent / suivant (à la fin, ajoute un motif vide) | OPT + haut / bas (phrase précédente / suivante) |
| B + gauche / droite | instrument précédent / suivant (0 à 7) | OPT + gauche / droite (instrument, écran instrument) |
| Select + gauche / droite | écran : projet (menu fichier) / grille / instruments | SELECT + direction |
| Select + haut / bas | tempo +1 / -1 (ticks par ligne) | écran Groove (pas encore fait) |
| Start | lecture / arrêt | PLAY |
| A + Start (écran instruments) | écoute l'instrument | EDIT + PLAY |

Dans l'écran instruments : haut / bas choisit le champ, A + gauche / droite change la valeur d'un pas fin,
A + haut / bas d'un grand pas (comme EDIT sur une valeur dans CCT), les flèches seules ne changent rien.
Dans le menu fichier : haut / bas, A valide, B ferme (ou répond non), Select + droite ferme.

Différences avec CCT : une seule grille de 4 voix au lieu des écrans Song / Chain / Phrase ; pas de sélection
ni de copier-coller par la manette ; la saisie d'un instrument se fait par B + gauche / droite (instrument
courant) et non colonne par colonne ; le mode jazz n'a pas Insert, ni Ctrl+S, ni la suppression de ligne avec
décalage (Retour arrière et Suppr effacent seulement la case).

| Clavier | Action |
|---|---|
| Échap | mode jazz on / off (indicateur `JAZZ`) : seul ce mode active les touches de piano |
| rangée de touches de piano (jazz) | poser une note (et la jouer), puis descendre d'une ligne |
| `[` `]` ou `-` `=` | octave -1 / +1 (0 à 7), utilisée par le mode jazz |
| `'` | note OFF, puis descendre d'une ligne |
| Retour arrière / Suppr | effacer la case |
| Espace ou Home | lecture / arrêt (depuis le haut du motif courant) |
| A + retour arrière (Alt au clavier) | supprimer le motif courant |
| `\` | échange A et B (voir ci-dessous) |
| `;` | disposition clavier AZERTY / QWERTY |
| Tab | bascule grille / éditeur d'instrument |
| Entrée | menu fichier (voir plus bas) |

La note posée par A et le mode jazz utilisent l'instrument sélectionné (`INS`). Dans l'écran instruments,
les touches de piano écoutent le son sans écrire, même hors jazz. Nommer le fichier demande un clavier ;
sans clavier, `song.cct` est le nom par défaut.

Pendant la lecture l'affichage suit le morceau ; on peut éditer en jouant.

Les touches de piano, sur deux rangées (la rangée affichée à droite est celle de la disposition active) :

```
QWERTY  bas  : z s x d c v g b h n j m    haut : q 2 w 3 e r 5 t 6 y 7 u
AZERTY  bas  : w s x d c v g b h n j ,    haut : a . z . e r . t . y . u
```

Chaque rangée est une octave chromatique de C à B ; la rangée du haut est l'octave au-dessus.
En AZERTY les dièses de la rangée du haut ne sont pas des touches ASCII sans Maj, ils manquent.

## Sur Atari ST (uxntari)

Prendre `tracker-ds.rom` : l'écran de la version normale (384x240) dépasse la basse résolution de l'ST
(320x200), celui de la variante DS (256x192) tient. `uxntari` ne lit pas le joystick (un joystick Atari n'a
qu'un bouton de tir) : la manette est émulée par le clavier de l'ST.

| Bouton de la manette | Touche sur l'ST |
|---|---|
| croix | flèches |
| A | Control (Alt une fois les boutons échangés avec `\`) |
| B | Alt (Control une fois échangés) |
| Select | Shift (gauche ou droit) |
| Start | Home |

Les modificateurs sont lus en continu, donc les combinaisons (A + flèche, B + flèche, Select + flèche) se
tiennent normalement. Le clavier de l'ST ne signale pas le relâchement des flèches : une flèche est
considérée relâchée quelques images après la dernière répétition, ce qui suffit pour les appuis brefs.
Les touches de piano du mode jazz (Échap) et le nom de fichier se saisissent au clavier ST comme ailleurs.

## Menu fichier

Entrée (ou Select + gauche depuis la grille) ouvre le menu : **NAME** (nom du fichier, modifiable : a-z, 0-9, `.`, `_`, `-`, 15 caractères),
**SAVE**, **LOAD**, **NEW SONG**, **CLOSE**. Haut / bas pour choisir, Entrée (ou A) pour valider, Échap (ou B) pour fermer.
Plus aucune touche ne charge ou n'enregistre directement. Un `*` à côté du titre indique des modifications
non enregistrées ; LOAD et NEW demandent alors confirmation (Y / N), et SAVE demande confirmation si le
fichier existe déjà.

## Instruments

Chaque case porte une note et un numéro d'instrument (celui qui est sélectionné au moment de la saisie,
affiché `INS` en haut). L'instrument 0 est le carré AY (tenue). Les instruments 1 à 7 sont de type SID,
modifiables dans la vue Tab : forme d'onde (triangle, dent de scie, impulsion, bruit, combinables par
ET logique), largeur d'impulsion, modulation de largeur (profondeur, vitesse), enveloppe ADSR logicielle
avec vrai niveau de sustain, durée de gate, arpège. Haut / bas choisit le champ, A + gauche / droite change la
valeur d'un pas fin et A + haut / bas d'un grand pas. Sept préréglages sont fournis (PULSE PWM, SAW LEAD,
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

Sur Nintendo DS (`tracker-ds.rom`), le son est correct depuis que la forme d'onde d'un instrument SID n'est
plus recalculée à chaque tick (seulement si le niveau ou la largeur d'impulsion change, avec un remplissage
rapide pour l'impulsion seule) : la première version déformait le son. Sur Atari ST avec `uxntari` à 32 MHz,
le son était correct mais l'affichage lent, d'où le redessin partiel pendant la lecture (deux lignes de la
grille par ligne jouée). Sous uxn2 l'audio était factice : pas écouté. uxn11 n'a pas d'audio, il faut uxn2.

## Fichiers

| Fichier | Rôle |
|---|---|
| `tracker.tal` | le programme ; le bloc entre les marqueurs `GENERATED` est produit par `tools/gen_data.py` |
| `tools/gen_data.py` | police 5x7, table des périodes AY, textes fixes du `.cct` |
| `tests/selftest.py` | test d'aller-retour sous uxncli |
| `tests/cct_check.cpp`, `tests/cct_check.sh` | relecture par le chargeur de CCT |
