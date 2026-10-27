/* Rendu des sprites varvara dans la memoire video de l'Atari ST.
   Deux couches (fond et premier plan) au format ST, recomposees octet par octet :
   le premier plan est transparent pour la couleur 0.
   planes = 4 : basse resolution (320x200), seuls les plans 0 et 1 servent (4 couleurs)
   planes = 2 : moyenne resolution (640x200, 4 couleurs)
   planes = 1 : haute resolution (640x400), toute couleur non nulle est noire */
#ifndef VID_H
#define VID_H

#include "uxn.h"

#define VID_BYTES 32000

extern int vid_w, vid_h;       /* taille logique, au plus celle de l'ecran */
extern int vid_maxw, vid_maxh;

void vid_init(u8 *scr, int nplanes);
void vid_resize(int w, int h);
void vid_clear(void);
void vid_fill(int xa, int xb, int ya, int yb, int layer, int idx);
void vid_tile(int x, int y, int addr, int ctrl);
int vid_layers(int x, int y); /* fond | premier plan << 2 (pour les tests) */
int vid_screen(int x, int y); /* couleur affichee (pour les tests) */

#endif
