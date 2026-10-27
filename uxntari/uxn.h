/* Coeur uxn : memoire, piles, opcodes. Portable, sans dependance Atari. */
#ifndef UXN_H
#define UXN_H

#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;

extern u8 ram[65536];
extern u8 dev[256];
extern u8 stk[2][256]; /* 0 = travail, 1 = retour */
extern u8 sp[2];
extern u8 (*on_dei)(u8 port);
extern void (*on_deo)(u8 port);

void uxn_reset(int soft);
int uxn_eval(u16 start);
int peek2(int a);
void poke2(int a, int v);

#endif
