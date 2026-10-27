#include <stdio.h>
#include <time.h>
#include "dev.h"
#include "vid.h"
#include "file.h"
#include "audio.h"

void (*on_stdout)(u8 c);
void (*on_stderr)(u8 c);
void (*on_palette)(void);

static int console_vec, screen_vec, controller_vec, mouse_vec;
static int rX, rY, rA, rMX, rMY, rMA, rML, rDX, rDY, rL1, rL2;

static void null_byte(u8 c) { (void)c; }
static void null_void(void) {}

/* ---- Acces aux registres (mots de deux octets) ---- */

static int
get_d2(int p)
{
	return (dev[p & 0xff] << 8) | dev[(p + 1) & 0xff];
}

static void
set_d2(int p, int v)
{
	dev[p & 0xff] = (v >> 8) & 0xff;
	dev[(p + 1) & 0xff] = v & 0xff;
}

/* ---- Sorties de texte (stderr) ---- */

static void
err_str(const char *s)
{
	while(*s) on_stderr((u8)*s++);
}

static void
err_hex(int v)
{
	on_stderr((u8)"0123456789abcdef"[(v >> 4) & 0xf]);
	on_stderr((u8)"0123456789abcdef"[v & 0xf]);
}

/* ---- System ---- */

static void
system_print(const char *name, int r)
{
	int i;
	err_str(name);
	on_stderr((u8)(sp[r] - 8) ? ' ' : '|');
	for(i = (sp[r] - 8) & 0xff; i != sp[r]; i = (i + 1) & 0xff) {
		err_hex(stk[r][i]);
		on_stderr(i == 0xff ? '|' : ' ');
	}
	on_stderr('<');
	err_hex(sp[r]);
	on_stderr(10);
}

/* Remplissage et copie dans la memoire (banque 0 seulement) */
static void
system_expansion(void)
{
	int ex = get_d2(2), cmd = ram[ex], length = peek2(ex + 1), bank = peek2(ex + 3), addr = peek2(ex + 5), i;
	if(length > 0x10000 - addr) length = 0x10000 - addr;
	if(cmd == 0) {
		if(bank == 0)
			for(i = 0; i < length; i++) ram[addr + i] = ram[(ex + 7) & 0xffff];
	} else if(cmd == 1 || cmd == 2) {
		int dbank = peek2(ex + 7), daddr = peek2(ex + 9);
		if(length > 0x10000 - daddr) length = 0x10000 - daddr;
		if(bank == 0 && dbank == 0) {
			if(daddr > addr)
				for(i = length - 1; i >= 0; i--) ram[daddr + i] = ram[addr + i];
			else
				for(i = 0; i < length; i++) ram[daddr + i] = ram[addr + i];
		}
	} else {
		err_str("Unknown command: ");
		err_hex(cmd);
		on_stderr(10);
	}
}

/* ---- Screen ---- */

/* Recopie la taille effective (limitee a celle de l'ecran de l'ST) dans les registres */
static void
screen_size(void)
{
	set_d2(0x22, vid_w);
	set_d2(0x24, vid_h);
}

static void
screen_pixel(void)
{
	int ctrl = dev[0x2e], layer = (ctrl >> 6) & 1, idx = ctrl & 3;
	int x = rX < 0 ? 0 : rX, y = rY < 0 ? 0 : rY;
	if(x < vid_w && y < vid_h) {
		if(ctrl & 0x80) {
			int x1 = (ctrl & 0x10) ? 0 : x, x2 = (ctrl & 0x10) ? x : vid_w;
			int y1 = (ctrl & 0x20) ? 0 : y, y2 = (ctrl & 0x20) ? y : vid_h;
			vid_fill(x1, x2, y1, y2, layer, idx);
		} else {
			vid_fill(x, x + 1, y, y + 1, layer, idx);
			if(rMX) rX += (ctrl & 0x10) ? -1 : 1;
			if(rMY) rY += (ctrl & 0x20) ? -1 : 1;
		}
	}
}

static void
screen_sprite(void)
{
	int ctrl = dev[0x2f], i, x = rX, y = rY;
	int flipx = ctrl & 0x10, flipy = ctrl & 0x20;
	int dx = flipx ? -rDY : rDY, dy = flipy ? -rDX : rDX;
	int incr = (ctrl & 0x80) ? rMA * 2 : rMA;
	for(i = 0; i <= rML; i++) {
		vid_tile(x, y, rA, ctrl);
		x += dx;
		y += dy;
		rA = (rA + incr) & 0xffff;
	}
	if(rMX) rX += flipx ? -rDX : rDX;
	if(rMY) rY += flipy ? -rDY : rDY;
}

static void
screen_auto(void)
{
	rMX = (dev[0x26] & 1) != 0;
	rMY = (dev[0x26] & 2) != 0;
	rMA = (dev[0x26] & 4) ? 8 : 0;
	rML = dev[0x26] >> 4;
	rDX = rMX * 8;
	rDY = rMY * 8;
}

/* ---- Datetime ---- */

static int
date_byte(int port)
{
	time_t t = time(NULL);
	struct tm *tm = localtime(&t);
	int year, yday;
	static struct tm zero;
	if(!tm) tm = &zero;
	year = tm->tm_year + 1900;
	yday = tm->tm_yday;
	switch(port) {
	case 0xc0: return (year >> 8) & 0xff;
	case 0xc1: return year & 0xff;
	case 0xc2: return tm->tm_mon;
	case 0xc3: return tm->tm_mday;
	case 0xc4: return tm->tm_hour;
	case 0xc5: return tm->tm_min;
	case 0xc6: return tm->tm_sec;
	case 0xc7: return tm->tm_wday;
	case 0xc8: return (yday >> 8) & 0xff;
	case 0xc9: return yday & 0xff;
	case 0xca: return tm->tm_isdst > 0;
	}
	return 0;
}

/* ---- Crochets de lecture et d'ecriture ---- */

static u8
dei(u8 port)
{
	switch(port) {
	case 0x04: return sp[0];
	case 0x05: return sp[1];
	case 0x28: dev[0x29] = rX & 0xff; return (rX >> 8) & 0xff;
	case 0x2a: dev[0x2b] = rY & 0xff; return (rY >> 8) & 0xff;
	case 0x2c: dev[0x2d] = rA & 0xff; return (rA >> 8) & 0xff;
	case 0x32: case 0x42: case 0x52: case 0x62: {
		int p = audio_position((port >> 4) - 3);
		dev[port + 1] = p & 0xff;
		return p >> 8;
	}
	case 0x34: case 0x44: case 0x54: case 0x64: return audio_vu((port >> 4) - 3);
	case 0xc0: case 0xc2: case 0xc3: case 0xc4: case 0xc5: case 0xc6: case 0xc7: case 0xc8: case 0xca:
		/* l'annee et le jour de l'annee sont sur deux octets */
		dev[0xc1] = date_byte(0xc1);
		dev[0xc9] = date_byte(0xc9);
		return date_byte(port);
	}
	return dev[port];
}

static void
deo(u8 port)
{
	switch(port) {
	case 0x03: system_expansion(); break;
	case 0x04: sp[0] = dev[4]; break;
	case 0x05: sp[1] = dev[5]; break;
	case 0x09: case 0x0b: case 0x0d: on_palette(); break;
	case 0x0e:
		if(dev[0xe] & 1) {
			system_print("WST", 0);
			system_print("RST", 1);
		}
		break;
	case 0x11: console_vec = get_d2(0x10); break;
	case 0x18: on_stdout(dev[0x18]); break;
	case 0x19: on_stderr(dev[0x19]); break;
	case 0x1a: err_hex(dev[0x1a]); break;
	case 0x1b: err_hex(dev[0x1a]); err_hex(dev[0x1b]); break;
	case 0x21: screen_vec = get_d2(0x20); break;
	case 0x23: case 0x25:
		vid_resize(get_d2(0x22) & 0xfff, get_d2(0x24) & 0xfff);
		screen_size();
		break;
	case 0x26: screen_auto(); break;
	case 0x29: rX = (short)get_d2(0x28); break;
	case 0x2b: rY = (short)get_d2(0x2a); break;
	case 0x2d: rA = get_d2(0x2c); break;
	case 0x2e: screen_pixel(); break;
	case 0x2f: screen_sprite(); break;
	case 0x3f: case 0x4f: case 0x5f: case 0x6f: audio_start((port >> 4) - 3); break;
	case 0x81: controller_vec = get_d2(0x80); break;
	case 0x91: mouse_vec = get_d2(0x90); break;
	case 0xa5: set_d2(0xa2, file_stat(0, get_d2(0xa4), rL1)); break;
	case 0xa6: set_d2(0xa2, file_delete(0)); break;
	case 0xa9: set_d2(0xa2, file_init(0, get_d2(0xa8))); break;
	case 0xab: rL1 = get_d2(0xaa); break;
	case 0xad: set_d2(0xa2, file_read(0, get_d2(0xac), rL1)); break;
	case 0xaf: set_d2(0xa2, file_write(0, get_d2(0xae), rL1, dev[0xa7])); break;
	case 0xb5: set_d2(0xb2, file_stat(1, get_d2(0xb4), rL2)); break;
	case 0xb6: set_d2(0xb2, file_delete(1)); break;
	case 0xb9: set_d2(0xb2, file_init(1, get_d2(0xb8))); break;
	case 0xbb: rL2 = get_d2(0xba); break;
	case 0xbd: set_d2(0xb2, file_read(1, get_d2(0xbc), rL2)); break;
	case 0xbf: set_d2(0xb2, file_write(1, get_d2(0xbe), rL2, dev[0xb7])); break;
	}
}

/* ---- Demarrage ---- */

/* Charge la ROM en $100, 65280 octets au plus */
int
dev_load(const char *path)
{
	FILE *f = fopen(path, "rb");
	if(!f) return 0;
	if(fread(ram + 0x100, 1, 0x10000 - 0x100, f) == 0) { fclose(f); return 1; }
	fclose(f);
	return 1;
}

/* A appeler apres uxn_reset et vid_init, avant l'evaluation du vecteur $100 */
void
dev_boot(int has_args)
{
	console_vec = screen_vec = controller_vec = mouse_vec = 0;
	rX = rY = rA = rMX = rMY = rMA = rML = rDX = rDY = rL1 = rL2 = 0;
	file_reset(0);
	file_reset(1);
	audio_reset();
	if(!on_stdout) on_stdout = null_byte;
	if(!on_stderr) on_stderr = null_byte;
	if(!on_palette) on_palette = null_void;
	if(has_args) dev[0x17] = 1;
	screen_size();
	on_dei = dei;
	on_deo = deo;
}

void
dev_shutdown(void)
{
	file_reset(0);
	file_reset(1);
}

int
dev_halted(void)
{
	return dev[0xf] != 0;
}

/* ---- Evenements ---- */

void
console_input(int c, int kind)
{
	dev[0x12] = c;
	dev[0x17] = kind;
	if(console_vec) uxn_eval(console_vec);
}

void
console_send_arg(const char *s, int last)
{
	while(*s) console_input((u8)*s++, CONSOLE_ARG);
	console_input(10, last ? CONSOLE_END : CONSOLE_EOA);
}

void
screen_frame(void)
{
	if(screen_vec) uxn_eval(screen_vec);
}

void
controller_down(int mask)
{
	if(mask) {
		dev[0x82] |= mask;
		if(controller_vec) uxn_eval(controller_vec);
	}
}

void
controller_up(int mask)
{
	if(mask) {
		dev[0x82] &= ~mask;
		if(controller_vec) uxn_eval(controller_vec);
	}
}

void
controller_key(int key)
{
	if(key) {
		dev[0x83] = key;
		if(controller_vec) uxn_eval(controller_vec);
		dev[0x83] = 0;
	}
}

void
mouse_down(int mask)
{
	dev[0x96] |= mask;
	if(mouse_vec) uxn_eval(mouse_vec);
}

void
mouse_up(int mask)
{
	dev[0x96] &= ~mask;
	if(mouse_vec) uxn_eval(mouse_vec);
}

void
mouse_pos(int x, int y)
{
	set_d2(0x92, x);
	set_d2(0x94, y);
	if(mouse_vec) uxn_eval(mouse_vec);
}

void
mouse_scroll(int x, int y)
{
	set_d2(0x9a, x);
	set_d2(0x9c, -y);
	if(mouse_vec) uxn_eval(mouse_vec);
	set_d2(0x9a, 0);
	set_d2(0x9c, 0);
}
