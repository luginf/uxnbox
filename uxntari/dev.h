/* Peripheriques varvara : system, console, screen, controller, mouse, file, datetime.
   L'Atari fournit seulement la sortie console, la palette et la memoire video.
   Les voix audio sont dans audio.c ; le frontend les convertit en son.
   Limites : une seule banque de memoire, pas de processus fils. */
#ifndef DEV_H
#define DEV_H

#include "uxn.h"

enum { CONSOLE_STD = 1, CONSOLE_ARG = 2, CONSOLE_EOA = 3, CONSOLE_END = 4 };

extern void (*on_stdout)(u8 c);
extern void (*on_stderr)(u8 c);
extern void (*on_palette)(void);

int dev_load(const char *path);
void dev_boot(int has_args);
void dev_shutdown(void);
int dev_halted(void);
void console_input(int c, int kind);
void console_send_arg(const char *s, int last);
void screen_frame(void);
void controller_down(int mask);
void controller_up(int mask);
void controller_key(int key);
void mouse_down(int mask);
void mouse_up(int mask);
void mouse_pos(int x, int y);
void mouse_scroll(int x, int y);

#endif
