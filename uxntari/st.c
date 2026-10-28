/* Frontend Atari ST de uxn/varvara, a compiler avec m68k-atari-mint-gcc.
   Usage : UXN.PRG [rom [arguments...]]   (sans argument : selecteur des *.rom du repertoire courant) */
#include <mint/osbind.h>
#include <mint/ostruct.h>
#include <string.h>
#include "uxn.h"
#include "dev.h"
#include "vid.h"
#include "audio.h"

#define KEY_UNDO 0x61
#define HOLD_FRAMES 3

static int planes, quit;
static u8 held, shift_old;
static int held_age;

/* ---- Souris : le gestionnaire IKBD cumule les deplacements ---- */

volatile long ms_dx, ms_dy;
volatile unsigned char ms_btn = 0xf8;

/* TOS appelle mousevec avec a0 sur le paquet de 3 octets : en-tete, dx, dy */
void mouse_isr(void);
__asm__(
	".text\n"
	".even\n"
	".globl _mouse_isr\n"
	"_mouse_isr:\n"
	"	movem.l %d0/%a0,-(%sp)\n"
	"	move.b (%a0),_ms_btn\n"
	"	move.b 1(%a0),%d0\n"
	"	ext.w %d0\n"
	"	ext.l %d0\n"
	"	add.l %d0,_ms_dx\n"
	"	move.b 2(%a0),%d0\n"
	"	ext.w %d0\n"
	"	ext.l %d0\n"
	"	add.l %d0,_ms_dy\n"
	"	movem.l (%sp)+,%d0/%a0\n"
	"	rts\n");

static _KBDVECS *kbv;
static void (*old_mousevec)(void *);
static int mx, my, mbuttons;

static void
hide_cursor(void)
{
	__asm__ volatile(".word 0xa000\n\t.word 0xa00a" : : : "d0", "d1", "d2", "a0", "a1", "a2", "memory");
}

static void
show_cursor(void)
{
	__asm__ volatile(".word 0xa009" : : : "d0", "d1", "d2", "a0", "a1", "a2", "memory");
}

static long
mouse_install(void)
{
	old_mousevec = kbv->mousevec;
	kbv->mousevec = (void (*)(void *))mouse_isr;
	return 0;
}

static long
mouse_restore(void)
{
	kbv->mousevec = old_mousevec;
	return 0;
}

static long grab_dx, grab_dy;
static int grab_btn;

/* Lecture et remise a zero des cumuls, interruptions masquees (superviseur) */
static long
mouse_grab(void)
{
	unsigned short sr;
	__asm__ volatile("move.w %%sr,%0\n\tori.w #0x0700,%%sr" : "=d"(sr));
	grab_dx = ms_dx;
	grab_dy = ms_dy;
	grab_btn = ms_btn;
	ms_dx = 0;
	ms_dy = 0;
	__asm__ volatile("move.w %0,%%sr" : : "d"(sr));
	return 0;
}

static void
poll_mouse(void)
{
	long dx, dy;
	int btn, left, right, chg;
	Supexec(mouse_grab);
	dx = grab_dx;
	dy = grab_dy;
	btn = grab_btn;
	left = (btn & 2) ? 1 : 0;
	right = (btn & 1) ? 1 : 0;
	btn = left | (right << 2);
	chg = btn ^ mbuttons;
	if(dx || dy) {
		mx += (int)dx;
		my += (int)dy;
		if(mx < 0) mx = 0;
		if(my < 0) my = 0;
		if(mx >= vid_w) mx = vid_w - 1;
		if(my >= vid_h) my = vid_h - 1;
		mouse_pos(mx, my);
	}
	if(chg & mbuttons) mouse_up(chg & mbuttons);
	if(chg & btn) mouse_down(chg & btn);
	mbuttons = btn;
}

/* ---- Console, palette, clavier ---- */

static void
out_console(u8 c)
{
	if(c == 10) Cconout(13);
	Cconout(c);
}

/* Chaque couleur varvara est un quartet de r, g et b ; l'ST garde 3 bits par canal.
   En haute resolution le bit 0 de la couleur 0 inverse l'affichage : on n'y touche pas. */
static void
apply_palette(void)
{
	int i, shift;
	if(planes == 1) return;
	for(i = 0, shift = 4; i < 4; i++, shift ^= 4) {
		int r = (dev[0x8 + i / 2] >> shift) & 0xf;
		int g = (dev[0xa + i / 2] >> shift) & 0xf;
		int b = (dev[0xc + i / 2] >> shift) & 0xf;
		Setcolor(i, ((r >> 1) << 8) | ((g >> 1) << 4) | (b >> 1));
	}
}

static int
arrow_button(int scan)
{
	switch(scan) {
	case 0x48: return 0x10;
	case 0x50: return 0x20;
	case 0x4b: return 0x40;
	case 0x4d: return 0x80;
	case 0x73: return 0x40; /* Control + gauche */
	case 0x74: return 0x80; /* Control + droite */
	case 0x47: return 0x08;
	}
	return 0;
}

/* Control, Alt, Shift -> A, B, Select (Kbshift : bits 0/1 shift, 2 control, 3 alt) */
static void
poll_modifiers(void)
{
	int k = (int)Kbshift(-1);
	u8 s = 0, chg;
	if(k & 3) s |= 0x04;
	if(k & 4) s |= 0x01;
	if(k & 8) s |= 0x02;
	chg = s ^ shift_old;
	if(chg & s) controller_down(chg & s);
	if(chg & shift_old) controller_up(chg & shift_old);
	shift_old = s;
}

/* Le clavier de l'ST ne signale pas le relachement des touches : une fleche
   est consideree relachee HOLD_FRAMES images apres la derniere repetition. */
static void
poll_keys(void)
{
	while(Cconis()) {
		long k = Crawcin();
		int scan = (int)((k >> 16) & 0xff), ascii = (int)(k & 0xff);
		if(scan == KEY_UNDO) {
			quit = 1;
		} else {
			/* d'abord le code de touche : avec Shift une fleche porte aussi un ascii ('8', '2'...) */
			int b = arrow_button(scan);
			if(b) {
				if(held != b) {
					if(held) controller_up(held);
					controller_down(b);
					held = b;
				}
				held_age = 0;
			} else if(ascii)
				controller_key(ascii);
		}
	}
	if(held && ++held_age > HOLD_FRAMES) {
		controller_up(held);
		held = 0;
	}
}

/* ---- Clavier silencieux, curseur normal ---- */

static char saved_conterm;

/* conterm ($484) : bit 0 clic des touches, bit 2 sonnerie (Ctrl-G) */
static long
conterm_quiet(void)
{
	volatile char *c = (char *)0x484;
	saved_conterm = *c;
	*c = saved_conterm & ~5;
	return 0;
}

static long
conterm_restore(void)
{
	*(volatile char *)0x484 = saved_conterm;
	return 0;
}

/* Fleche GEM standard : le bureau laisse l'abeille pendant le chargement */
static const short arrow_form[37] = {
	1, 1, 1, 0, 1,
	(short)0xc000, (short)0xe000, (short)0xf000, (short)0xf800, (short)0xfc00, (short)0xfe00, (short)0xff00, (short)0xff80,
	(short)0xffc0, (short)0xffe0, (short)0xfe00, (short)0xef00, (short)0xcf00, (short)0x8780, (short)0x0780, (short)0x0380,
	0x0000, 0x4000, 0x6000, 0x7000, 0x7800, 0x7c00, 0x7e00, 0x7f00,
	0x7f80, 0x7c00, 0x6c00, 0x4600, 0x0600, 0x0300, 0x0300, 0x0000};

static void
set_arrow(void)
{
	register const short *a0 __asm__("a0") = arrow_form;
	__asm__ volatile(".word 0xa00b" : "+a"(a0) : : "d0", "d1", "d2", "a1", "a2", "memory", "cc");
}

/* ---- Son : voix varvara sur les trois canaux du YM2149 ----
   Un cycle unique (note) donne un son carre a la bonne hauteur ; un echantillon
   (plus de 256 octets : percussion, voix) est rendu par le generateur de bruit. */

static unsigned char ym_cache[16];
static unsigned char ym_saved_mixer;
static long hz200_now;

static long
read_hz200(void)
{
	hz200_now = *(volatile long *)0x4ba;
	return 0;
}

static void
ym_write(int reg, int val)
{
	if(ym_cache[reg] == (unsigned char)val) return;
	ym_cache[reg] = val;
	Giaccess(val, 0x80 | reg);
}

static void
ym_silence(void)
{
	int ch;
	memset(ym_cache, 0xff, sizeof ym_cache);
	for(ch = 0; ch < 3; ch++) ym_write(8 + ch, 0);
	ym_write(7, 0xff);
}

static void
ym_restore(void)
{
	int ch;
	for(ch = 0; ch < 3; ch++) ym_write(8 + ch, 0);
	ym_write(7, ym_saved_mixer);
}

static const unsigned char ym_vol[16] = {0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14, 15};
static long last_hz200;

/* Fait avancer les voix du temps ecoule (horloge a 200 Hz) et met a jour le YM */
static void
audio_tick(void)
{
	int ch, mixer = 0xc0, noise_period = 0;
	Supexec(read_hz200);
	audio_update((hz200_now - last_hz200) * 441 / 2);
	last_hz200 = hz200_now;
	for(ch = 0; ch < 3; ch++) {
		int voice = ch, noise, vol;
		long hz, rate;
		if(ch == 2 && !audio_voice(2, &noise, &hz, &rate, &vol)) voice = 3;
		if(!audio_voice(voice, &noise, &hz, &rate, &vol) || !vol) {
			ym_write(8 + ch, 0);
			mixer |= (1 << ch) | (8 << ch);
			continue;
		}
		ym_write(8 + ch, ym_vol[vol]);
		if(noise) {
			int np = rate ? (int)(2048 / rate) : 31;
			noise_period = np < 1 ? 1 : np > 31 ? 31 : np;
			mixer |= 1 << ch;
		} else {
			long tp = hz ? 125000L / hz : 4095;
			if(tp < 1) tp = 1;
			if(tp > 4095) tp = 4095;
			ym_write(2 * ch, tp & 0xff);
			ym_write(2 * ch + 1, tp >> 8);
			mixer |= 8 << ch;
		}
	}
	if(noise_period) ym_write(6, noise_period);
	ym_write(7, mixer);
}

/* ---- Selecteur de ROM ---- */

#define MAX_ROMS 64
#define LIST_ROWS 14

static void text_palette(void);
static void set_rez(int rez);
static char rom_names[MAX_ROMS][14];
static int rom_count;

/* Liste les fichiers correspondant a pat (ex. "*.rom") ; renvoie le nombre trouve */
static int
scan_roms(const char *pat)
{
	_DTA dta, *old = Fgetdta();
	rom_count = 0;
	Fsetdta(&dta);
	if(Fsfirst(pat, 0) == 0)
		do {
			if(rom_count < MAX_ROMS) {
				strncpy(rom_names[rom_count], dta.dta_name, 13);
				rom_names[rom_count++][13] = 0;
			}
		} while(Fsnext() == 0);
	Fsetdta(old);
	return rom_count;
}

/* Position et boutons du curseur : variables de la ligne A (GCURX, GCURY, MOUSE_BT) */
static volatile short *linea;

static void
linea_init(void)
{
	register volatile short *a0 __asm__("a0");
	__asm__ volatile(".word 0xa000" : "=a"(a0) : : "d0", "d1", "d2", "a1", "a2", "memory");
	linea = a0;
}

#define GCURX (linea[-0x25a / 2])
#define GCURY (linea[-0x258 / 2])
#define MOUSE_BT (linea[-0x254 / 2])

/* Ligne des boutons : [ Basse ] [ Moyenne ] [ Quitter ] ; seul [ Quitter ] en monochrome */
#define BTN_LOW_A 1
#define BTN_LOW_B 9
#define BTN_MED_A 11
#define BTN_MED_B 21
#define BTN_QUIT_A (planes == 1 ? 1 : 23)
#define BTN_QUIT_B (planes == 1 ? 11 : 33)

static int
list_rows(int top)
{
	int n = rom_count - top;
	return n < LIST_ROWS ? n : LIST_ROWS;
}

static void
draw_list(int sel, int top)
{
	int i, nv = list_rows(top);
	hide_cursor();
	text_palette();
	Cconws("\033b\003\033c0");
	Cconws("\033E\033f UXN - choisissez une ROM\r\n\r\n");
	for(i = top; i < top + nv; i++) {
		Cconws(i == sel ? "\033p  " : "  ");
		Cconws(rom_names[i]);
		Cconws(i == sel ? "  \033q\r\n" : "\r\n");
	}
	Cconws("\r\n Haut/Bas : choisir  Return : lancer\r\n Clic sur une ROM : lancer\r\n\r\n ");
	if(planes != 1) {
		Cconws(planes == 4 ? "\033p" : "");
		Cconws("[ Basse ]");
		Cconws(planes == 4 ? "\033q" : "");
		Cconws(" ");
		Cconws(planes == 2 ? "\033p" : "");
		Cconws("[ Moyenne ]");
		Cconws(planes == 2 ? "\033q" : "");
		Cconws(" ");
	}
	Cconws("[ Quitter ]\r\n");
	if(planes != 1) Cconws("\r\n F3 basse  F4 moyenne  Undo quitter");
	else Cconws("\r\n Undo : quitter");
	set_arrow();
	show_cursor();
}

/* Clic gauche en (x, y) : renvoie l'indice de ROM, -1 pour quitter, -2 si rien d'utile.
   Un bouton de resolution change la resolution et renvoie -3. */
static int
click_at(int x, int y, int top)
{
	int row = y / (planes == 1 ? 16 : 8), col = x / 8, nv = list_rows(top);
	if(row >= 2 && row < 2 + nv) return top + row - 2;
	if(row == 2 + nv + 4) {
		if(col >= BTN_QUIT_A && col <= BTN_QUIT_B) return -1;
		if(planes != 1 && col >= BTN_LOW_A && col <= BTN_LOW_B) {
			if(planes != 4) set_rez(0);
			return -3;
		}
		if(planes != 1 && col >= BTN_MED_A && col <= BTN_MED_B) {
			if(planes != 2) set_rez(1);
			return -3;
		}
	}
	return -2;
}

/* Renvoie l'indice choisi, ou -1 pour quitter */
static int
select_rom(void)
{
	static int sel, top;
	int redraw = 1, prev = 1;
	if(sel >= rom_count) sel = top = 0;
	linea_init();
	for(;;) {
		int scan, ascii, btn;
		if(redraw) {
			draw_list(sel, top);
			redraw = 0;
		}
		if(!Cconis()) {
			Vsync();
			btn = MOUSE_BT & 1;
			if(btn && !prev) {
				int r = click_at(GCURX, GCURY, top);
				if(r >= 0) return r;
				if(r == -1) return -1;
				if(r == -3) redraw = 1;
			}
			prev = btn;
			continue;
		}
		{
			long k = Crawcin();
			scan = (int)((k >> 16) & 0xff);
			ascii = (int)(k & 0xff);
		}
		if(scan == KEY_UNDO) return -1;
		if(ascii == 13) return sel;
		if(planes != 1 && ((scan == 0x3d && planes == 2) || (scan == 0x3e && planes == 4))) set_rez(scan == 0x3d ? 0 : 1);
		if(scan == 0x48 && sel > 0) sel--;
		if(scan == 0x50 && sel < rom_count - 1) sel++;
		if(sel < top) top = sel;
		if(sel >= top + LIST_ROWS) top = sel - LIST_ROWS + 1;
		redraw = 1;
	}
}

/* ---- Execution d'une ROM ---- */

static short saved_pal[16];
static int orig_rez;

/* Etat de l'ecran a l'entree : palette complete et resolution */
static void
save_screen(void)
{
	int i;
	orig_rez = Getrez();
	for(i = 0; i < 16; i++) saved_pal[i] = Setcolor(i, -1);
	Supexec(conterm_quiet);
	ym_saved_mixer = Giaccess(0, 7);
	ym_silence();
}

static void
restore_screen(void)
{
	int i;
	if(Getrez() != orig_rez) Setscreen((void *)-1L, (void *)-1L, orig_rez);
	for(i = 0; i < 16 && orig_rez != 2; i++) Setcolor(i, saved_pal[i]);
	Supexec(conterm_restore);
	ym_restore();
}

/* Basse (0) ou moyenne (1) resolution ; le texte est redessine par l'appelant */
static void
set_rez(int rez)
{
	Setscreen((void *)-1L, (void *)-1L, rez);
	planes = rez == 0 ? 4 : 2;
	text_palette();
}

/* Texte lisible : fond blanc (couleur 0), encre noire (couleur 3) */
static void
text_palette(void)
{
	if(planes == 1) return;
	Setcolor(0, 0x777);
	Setcolor(3, 0x000);
}

/* Renvoie 0 si la ROM n'a pas pu etre chargee */
static int
run_rom(const char *rom, int argc, char **argv)
{
	int i;
	quit = 0;
	held = shift_old = 0;
	held_age = 0;
	mbuttons = 0;
	uxn_reset(0);
	on_stdout = out_console;
	on_stderr = out_console;
	on_palette = apply_palette;
	if(!dev_load(rom)) return 0;
	vid_init((u8 *)Physbase(), planes);
	dev_boot(argc > 2);
	apply_palette();
	hide_cursor();
	kbv = (_KBDVECS *)Kbdvbase();
	Supexec(mouse_install);
	mx = vid_w / 2;
	my = vid_h / 2;
	Supexec(read_hz200);
	last_hz200 = hz200_now;
	uxn_eval(0x100);
	for(i = 2; i < argc; i++)
		console_send_arg(argv[i], i == argc - 1);

	while(!dev_halted() && !quit) {
		Vsync();
		poll_modifiers();
		poll_keys();
		poll_mouse();
		screen_frame();
		audio_tick();
	}
	ym_silence();

	Supexec(mouse_restore);
	show_cursor();
	dev_shutdown();
	text_palette();
	if(dev[0xf] & 0x7f) {
		Cconws("\033EHalted with code ");
		Cconout('0' + ((dev[0xf] & 0x7f) / 10) % 10);
		Cconout('0' + (dev[0xf] & 0x7f) % 10);
		Cconws("\r\n");
		Crawcin();
	}
	return 1;
}

static void
fail(const char *rom)
{
	Cconws("Could not load ");
	Cconws(rom);
	Cconws("\r\n");
	Crawcin();
}

/* Sans argument : selecteur sur les ROM de A:\ (sinon du repertoire courant),
   et retour au selecteur quand la ROM se termine. */
int
main(int argc, char **argv)
{
	int rez;
	save_screen();
	rez = Getrez();
	if(rez == 1) {
		Setscreen((void *)-1L, (void *)-1L, 0);
		rez = Getrez();
	}
	planes = rez == 2 ? 1 : rez == 1 ? 2 : 4;
	text_palette();
	if(argc > 1) {
		if(!run_rom(argv[1], argc, argv)) fail(argv[1]);
		restore_screen();
		return 0;
	}
	for(;;) {
		int k;
		if(!scan_roms("*.rom")) {
			Cconws("\033EAucune ROM (*.rom) dans le repertoire courant.\r\n");
			Crawcin();
			restore_screen();
			return 1;
		}
		k = select_rom();
		if(k < 0) break;
		if(!run_rom(rom_names[k], 2, (char *[]){"UXN", rom_names[k]})) fail(rom_names[k]);
		Cconws("\033E\033e");
	}
	restore_screen();
	Cconws("\033E\033e");
	return 0;
}
