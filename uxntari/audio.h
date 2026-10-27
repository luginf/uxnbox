/* Peripheriques audio de varvara ($30, $40, $50, $60) : quatre voix, enveloppe ADSR,
   modele de lecture de l'implementation de reference (44100 Hz, un echantillon
   de 8 bits en boucle). Aucun son ici : le frontend lit l'etat des voix et le
   convertit pour son materiel (voir audio_voice). */
#ifndef AUDIO_H
#define AUDIO_H

#include "uxn.h"

#define AUDIO_VOICES 4
#define AUDIO_RATE 44100

void audio_reset(void);
void audio_start(int voice);               /* ecriture du port pitch : lance une note */
void audio_update(long samples);           /* fait avancer le temps, appelle les vecteurs */
int audio_vu(int voice);                   /* port output */
int audio_position(int voice);             /* port position */

/* Etat d'une voix pour le frontend : renvoie 0 si elle est muette.
   noise = 1 pour un echantillon (len > 256), 0 pour un cycle unique (note).
   hz : frequence de la note ; rate : vitesse de lecture en 1/256 (256 = note 60) ;
   vol : volume lineaire 0-15 (maximum des deux canaux, enveloppe comprise). */
int audio_voice(int voice, int *noise, long *hz, long *rate, int *vol);

#endif
