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

L'écran fait 384x240. Le ROM tient en 19 Ko. La variante DS (`tools/make_ds.py`) fait 256x192 : lignes de 8 px,
le reste est identique (tous les écrans tiennent en 32 colonnes). Elle démarre sans l'échange A/B. Elle n'a été vue que sous uxn2, pas sur une vraie DS.

## Utilisation

Le morceau suit le modèle de CCT : un **song** de 64 lignes sur 4 pistes, qui cite des **chaînes** (128 au
plus, 16 lignes de phrase + transposition), qui citent des **phrases** (128 au plus, 16 lignes de note + instrument).
Les pistes sont indépendantes et suivent la lecture de CCT : chacune suit sa chaîne et sa ligne de song. Une chaîne s'arrête
à sa première ligne vide, puis la piste passe à la ligne suivante du song ; si cette case est vide (ou après la ligne 64), la
piste revient au début du bloc de cases non vides qui vient de finir. Une piste dont la case de départ est vide reste muette.
Le tempo est un nombre de ticks à 50 Hz par ligne (comme CCT, 06 par défaut), réglé dans l'écran Groove.

### Les écrans

Comme dans CCT, on passe d'un écran à l'autre avec **Select + direction** ; la carte `SCPI` en bas à droite
montre l'écran courant. Il n'y a pas d'écran Table pour l'instant.

```
 PROJECT              GROOVE
    |                 |
  SONG --- CHAIN --- PHRASE --- INSTRUMENT
    |
 SETTINGS
    |  (ligne HELP)
  HELP
```

Song a Project au-dessus et Settings en dessous ; Chain est à droite de Song, Phrase à droite de Chain,
Instrument à droite de Phrase ; Groove est au-dessus de Phrase. Help s'ouvre par la ligne HELP de Settings
(Select + haut en revient). Tab passe à l'écran suivant de la rangée (Song, Chain, Phrase, Instrument).

| Écran | Contenu | Curseur |
|---|---|---|
| SONG | 16 lignes par page, 4 colonnes (T1 à T4) de numéros de chaîne | croix ; B + haut / bas saute de 16 lignes |
| CHAIN | la chaîne sous le curseur du song : 16 lignes (phrase, transposition) | croix ; B + croix déplace la case du song |
| PHRASE | la phrase de la ligne de chaîne : 16 lignes (note, instrument, volume `VL` 00 à 7F ; les numéros de ligne 0, 4, 8 et C sont d'une autre couleur) | croix ; B + haut / bas change de ligne de chaîne, B + gauche / droite de piste |
| INSTRUMENT | l'instrument courant (voir plus bas) | haut / bas choisit le champ |
| PROJECT | nom du fichier, SAVE, LOAD, NEW SONG, CLOSE | haut / bas |
| SETTINGS | A/B SWAP, KEYBOARD (AZERTY / QWERTY), HELP | haut / bas, A change ou ouvre |
| GROOVE | tempo | A + gauche / droite |
| HELP | rappel des commandes sur 3 pages (manette, écrans, clavier) | gauche / droite (ou Select + gauche / droite) change de page, B revient à Settings |

Les écrans ne créent rien en les ouvrant : une chaîne ou une phrase est allouée (le premier numéro libre) au
moment où on y écrit, par A ou par une touche de piano. S'il n'en reste plus, le message `NO FREE SLOT` s'affiche.

### Manette et clavier

Les commandes de la manette suivent celles de [ChooChooTracker](https://github.com/luginf/Choochootracker/blob/main/docs/USER_MANUAL.md)
(A = EDIT, B = OPT, Start = PLAY, Select = SELECT). Au clavier : Alt = A, Ctrl = B, Maj = Select, Home = Start
(uxn ne voit pas les touches X et Z que CCT utilise par défaut).

**A et B échangés** : les émulateurs envoient Ctrl pour A et Alt pour B, mais A est à droite dans CCT et sur une
manette. Le tracker échange donc les deux boutons (`tracker.rom` démarre ainsi ; la touche `\` ou la ligne **A/B SWAP**
de l'écran Settings bascule). Cet échange vaut pour tout ce qui arrive en entrée, y compris une vraie manette :
la variante DS démarre sans échange.

| Manette | Action | Équivalent CCT |
|---|---|---|
| croix | déplacer le curseur | idem |
| A (appui bref) | case vide : pose la dernière valeur (chaîne, phrase, note, instrument) ; note : la rejoue | tap EDIT |
| A + gauche / droite | valeur -1 / +1 | EDIT + gauche / droite |
| A + haut / bas | valeur +1 / -1 octave (notes), +16 / -16 (chaînes, phrases) | EDIT + haut / bas |
| A + B | case vide : note OFF ; sinon efface la case | EDIT + OPT |
| B + croix | selon l'écran (voir le tableau des écrans) | OPT + direction |
| B + gauche / droite (Instrument) | instrument précédent / suivant (0 à 7) | OPT + gauche / droite |
| Select + croix | écran voisin | SELECT + direction |
| Start | lecture / arrêt (depuis la ligne de song du curseur) | PLAY |
| A + Start (Instrument) | écoute l'instrument | EDIT + PLAY |
| Start (écran Phrase) | joue seulement la phrase du curseur, en boucle, sur la piste du curseur ; Start l'arrête | PLAY |
| Select + Start (écran Phrase) | joue toutes les chaînes à partir de la ligne de song du curseur, comme Start ailleurs | SEL + PLAY |
| B + Start | arrêt général : lecture stoppée, les 4 voix remises à zéro et coupées (aussi fait par NEW SONG et LOAD) | OPT + PLAY |
| A deux fois vite (Song, Chain) | sur une chaîne ou une phrase déjà posée, passe au prochain numéro libre | double EDIT |

Dans l'écran Instrument : haut / bas choisit le champ, A + gauche / droite change la valeur d'un pas fin,
A + haut / bas d'un grand pas (comme EDIT sur une valeur dans CCT), les flèches seules ne changent rien.
Dans PROJECT : haut / bas, A valide, B ferme (ou répond non), Select + bas ferme aussi.

Différences avec CCT : pas d'écran Table ni de groove à plusieurs pas (un seul tempo) ; pas de sélection ni
de copier-coller par la manette ; la saisie d'un instrument se fait par A sur la colonne `IN` de la phrase ;
le mode jazz n'a pas Insert, ni Ctrl+S, ni la suppression de ligne avec décalage (Retour arrière et Suppr effacent seulement la case).

| Clavier | Action |
|---|---|
| Échap | mode jazz on / off (indicateur `JAZZ`) : seul ce mode active les touches de piano sur PHRASE |
| rangée de touches de piano (jazz) | poser une note (et la jouer), puis descendre d'une ligne |
| `[` `]` ou `-` `=` | octave -1 / +1 (0 à 7), utilisée par le mode jazz |
| `'` | note OFF, puis descendre d'une ligne |
| Retour arrière / Suppr | effacer la case |
| Espace ou Home | lecture / arrêt |
| `\` | échange A et B (voir ci-dessus) |
| `;` | disposition clavier AZERTY / QWERTY |
| Tab | écran suivant (Song, Chain, Phrase, Instrument) |
| Entrée | écran PROJECT |

La note posée par A et le mode jazz utilisent l'instrument sélectionné (`INS`). Dans l'écran Instrument,
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

## Écran PROJECT

Entrée (ou Select + haut depuis SONG) ouvre l'écran : **NAME**, **RANDOM NAME**, **SAVE**, **LOAD**, **NEW SONG**,
**CLOSE**. Haut / bas pour choisir, A (ou Entrée) pour valider, B (ou Échap) pour fermer, Select + bas ferme aussi.
Un `*` à côté du titre indique des modifications non enregistrées ; LOAD et NEW demandent alors confirmation (Y / N,
ou A / B), et SAVE demande confirmation si le fichier existe déjà.

- **NAME** : A passe en édition du nom (sans l'extension, `.cct` est ajouté tout seul, 11 caractères au plus).
  Haut / bas change la lettre sous le curseur (a-z, 0-9, `-`, `_`), gauche / droite déplace le curseur, la case libre
  à droite ajoute une lettre, B efface la dernière lettre, A valide. Au clavier on peut aussi taper le nom.
- **RANDOM NAME** : nom de 8 lettres (consonne, voyelle, ...), pour enregistrer sans clavier.
- **LOAD** : liste les fichiers `.cct` du dossier courant (16 au plus, noms de 11 caractères au plus, d'après une seule lecture de 1 Ko du dossier) ; haut / bas
  choisit, A charge, B revient. Si le dossier ne se lit pas ou ne contient aucun `.cct`, le nom courant est chargé.

La carte en bas à droite montre l'écran courant : `SCPI` au milieu, `P` (Project) au-dessus de `S`, `G` (Groove)
au-dessus de `P`, `S` (Settings) dessous.

## Instruments

Chaque ligne de phrase porte une note et un numéro d'instrument (celui qui est sélectionné au moment de la saisie,
affiché `INS` en haut ; B + gauche / droite dans l'écran Instrument le change). L'instrument 0 est le carré AY (tenue). Les instruments 1 à 7 sont de type SID,
modifiables dans l'écran Instrument : forme d'onde (triangle, dent de scie, impulsion, bruit, combinables par
ET logique), largeur d'impulsion, modulation de largeur (profondeur, vitesse), enveloppe ADSR logicielle
avec vrai niveau de sustain, durée de gate, arpège. Haut / bas choisit le champ, A + gauche / droite change la
valeur d'un pas fin et A + haut / bas d'un grand pas. Sept préréglages sont fournis (PULSE PWM, SAW LEAD,
TRI BASS, NOISE HAT, PLUCK, PAD, ARP PULSE).

La première ligne de l'écran Instrument, `PRESET`, affiche le nom de l'instrument. Dessus, A + gauche / droite
parcourt les préréglages en boucle (les 7 ci-dessus puis SQUARE, le carré AY) et remplace l'instrument, nom
compris ; n'importe quel numéro, 0 compris, peut devenir SID ou AY. Les champs en dessous règlent ensuite le son. Le nom suit
l'instrument dans le fichier `.cct`.

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

- Song : une ligne par ligne du song, quatre numéros de chaîne (`00 01 -- 05`, `--` = vide), jusqu'à 64 lignes.
- Chaîne : seules celles qui sont citées dans le song ou non vides sont écrites ; 16 lignes `%03X %02X`
  (numéro de phrase sur trois chiffres, transposition ; une ligne vide est `--- 00`).
- Phrase : seules celles qui sont citées par une chaîne ou non vides ; 16 lignes `C-4 00 -- --- 00 --- 00 --- 00`.
  Les OFF sont `OFF -- -- ...`.
- Groove 0 : le tempo (deux fois la même valeur).
- Instrument 0 : AY1 « Square » (tenue, mixer 01). Instruments 1 à 7 : type 27 (SID), 25 paramètres.
- Chaque ligne de phrase porte l'instrument de la ligne (`--` sur les OFF et cases vides).

Au chargement on lit : le song (quatre premières colonnes, 64 lignes), les chaînes et phrases de numéro 00 à 7F
(les autres sont ignorées), le groove 0 (première valeur) et les instruments 0 à 7. Seuls les types 1 (AY1) et 27 (SID)
sont repris ; un autre type devient un carré AY. Tout le reste est ignoré : volumes, FX, tables, grooves à plusieurs pas,
pistes au-delà de la quatrième, noms de plus de 9 caractères (tronqués). Réenregistrer un fichier CCT riche depuis ici
en perd donc ces parties.

## Vérification

- `make test` : le ROM de test (`tests/selftest.py`, construit à partir de `tracker.tal`) remplit un morceau
  (song, chaînes avec transposition, phrases, un instrument modifié), écrit `song.cct`, vide la mémoire, recharge
  et compare octet par octet. Il vérifie aussi, tout cela sans écran :
  - la lecture : 100 ticks à tempo 1, la suite de notes déclenchées (piste, note, instrument) est comparée à un modèle
    écrit en Python (transposition, fin de chaîne, passage à la ligne de song suivante, retour au début du bloc, piste muette) ;
  - les 8 écrans, dessinés dans un tampon de texte : pas plus de 32 colonnes (la DS), pile équilibrée, textes attendus
    (`python3 tests/selftest.py <dossier> -v` les affiche) ;
  - la manette : A bref, A + direction, A + B, Select + direction, enchaînés comme par une vraie manette.
  Il peut aussi lire un `.cct` existant : `python3 tests/selftest.py <dossier> <fichier.cct>`.
- `make cct-check` : `tests/cct_check.cpp` appelle `projectLoad` de ChooChooTracker sur le fichier écrit
  et affiche ce que CCT en a compris : song, chaînes (phrase / transposition), phrases et les 8 instruments
  (CCT accepte les blocs SID : `validSID`). Nécessite les objets compilés de CCT (`CCT_DIR`, défaut
  `~/src/forks/Choochootracker`, après `make -f Makefile.test` dans `tracker/`).
- Aucun test ne lance uxn2 : l'affichage réel et le son restent à essayer à la main.

Sur Nintendo DS (`tracker-ds.rom`), le son est correct depuis que la forme d'onde d'un instrument SID n'est
plus recalculée à chaque tick (seulement si le niveau ou la largeur d'impulsion change, avec un remplissage
rapide pour l'impulsion seule) : la première version déformait le son. Sur Atari ST avec `uxntari` à 32 MHz,
le son était correct mais l'affichage lent, d'où le redessin partiel pendant la lecture (deux lignes de la
phrase par ligne jouée). Sous uxn2 l'audio était factice : pas écouté. uxn11 n'a pas d'audio, il faut uxn2.

## Fichiers

| Fichier | Rôle |
|---|---|
| `tracker.tal` | le programme ; le bloc entre les marqueurs `GENERATED` est produit par `tools/gen_data.py` |
| `tools/gen_data.py` | police 5x7, table des périodes AY, textes fixes du `.cct`, aide, titres |
| `tests/selftest.py` | aller-retour, lecture, écrans et manette sous uxncli |
| `tests/cct_check.cpp`, `tests/cct_check.sh` | relecture par le chargeur de CCT |
