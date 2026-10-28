#include <string.h>
#include "vid.h"

int vid_w, vid_h, vid_maxw, vid_maxh;

/* blend[mode][couche][couleur] : voir screen_deo_sprite de la reference */
static const u8 blend_lut[16][2][4] = {
	{{0, 0, 1, 2}, {0, 0, 4, 8}},
	{{0, 1, 2, 3}, {0, 4, 8, 12}},
	{{0, 2, 3, 1}, {0, 8, 12, 4}},
	{{0, 3, 1, 2}, {0, 12, 4, 8}},
	{{1, 0, 1, 2}, {4, 0, 4, 8}},
	{{1, 1, 2, 3}, {4, 4, 8, 12}},
	{{1, 2, 3, 1}, {4, 8, 12, 4}},
	{{1, 3, 1, 2}, {4, 12, 4, 8}},
	{{2, 0, 1, 2}, {8, 0, 4, 8}},
	{{2, 1, 2, 3}, {8, 4, 8, 12}},
	{{2, 2, 3, 1}, {8, 8, 12, 4}},
	{{2, 3, 1, 2}, {8, 12, 4, 8}},
	{{3, 0, 1, 2}, {12, 0, 4, 8}},
	{{3, 1, 2, 3}, {12, 4, 8, 12}},
	{{3, 2, 3, 1}, {12, 8, 12, 4}},
	{{3, 3, 1, 2}, {12, 12, 4, 8}}};

static u8 *scr;
static u8 lay[2][VID_BYTES]; /* 0 = fond, 1 = premier plan */
static int planes, line_b, step_sh; /* step_sh : log2 des octets par groupe de 16 pixels */
static u8 rev[256];
static long row_off[400]; /* offset de chaque ligne */
static const u8 mod5[16] = {0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0}; /* blend % 5 != 0 */

void
vid_clear(void)
{
	memset(lay, 0, sizeof lay);
	memset(scr, 0, VID_BYTES);
}

void
vid_init(u8 *s, int nplanes)
{
	int i, j, v;
	scr = s;
	planes = nplanes;
	vid_maxw = planes == 4 ? 320 : 640;
	vid_maxh = planes == 1 ? 400 : 200;
	vid_w = vid_maxw;
	vid_h = vid_maxh;
	line_b = planes == 1 ? 80 : 160;
	step_sh = planes == 4 ? 3 : planes;
	for(i = 0; i < 400; i++)
		row_off[i] = (long)i * line_b;
	for(i = 0; i < 256; i++) {
		for(v = 0, j = 0; j < 8; j++)
			if(i & (1 << j)) v |= 128 >> j;
		rev[i] = v;
	}
	vid_clear();
}

/* Change la taille logique : efface tout, comme la reference */
void
vid_resize(int w, int h)
{
	if(w > vid_maxw) w = vid_maxw;
	if(h > vid_maxh) h = vid_maxh;
	if(w != vid_w || h != vid_h) {
		vid_w = w;
		vid_h = h;
		vid_clear();
	}
}

/* Pose les bits mask de l'octet de colonne col, ligne row, dans la couche,
   avec les valeurs b0 et b1 des deux plans, puis recompose l'ecran. */
static void
put_bits(int layer, int row, int col, int mask, int b0, int b1)
{
	int o, m, f0, f1, g0, g1, keep;
	if(row < 0 || row >= vid_h || col < 0 || (col << 3) >= vid_w) return;
	if(((col + 1) << 3) > vid_w)
		mask &= (0xff << (((col + 1) << 3) - vid_w)) & 0xff;
	if(!mask) return;
	b0 &= mask;
	b1 &= mask;
	o = row_off[row] + ((col >> 1) << step_sh) + (col & 1);
	keep = mask ^ 0xff;
	lay[layer][o] = (lay[layer][o] & keep) | b0;
	f0 = lay[1][o];
	g0 = lay[0][o];
	if(planes >= 2) {
		lay[layer][o + 2] = (lay[layer][o + 2] & keep) | b1;
		f1 = lay[1][o + 2];
		g1 = lay[0][o + 2];
		m = (f0 | f1) ^ 0xff;
		scr[o] = f0 | (g0 & m);
		scr[o + 2] = f1 | (g1 & m);
	} else
		scr[o] = f0 | g0;
}

/* Ecrit un octet entier de la couche (valeurs b0 et b1 des deux plans), sans masque */
static void
put_full(int layer, int o, int b0, int b1)
{
	int f0, f1, m;
	lay[layer][o] = b0;
	f0 = lay[1][o];
	if(planes >= 2) {
		lay[layer][o + 2] = b1;
		f1 = lay[1][o + 2];
		m = (f0 | f1) ^ 0xff;
		scr[o] = f0 | (lay[0][o] & m);
		scr[o + 2] = f1 | (lay[0][o + 2] & m);
	} else
		scr[o] = f0 | lay[0][o];
}

/* Remplit les colonnes [xa, xb) et les lignes [ya, yb) d'une couche avec la couleur idx.
   Les octets entierement couverts passent par put_full : un fond d'ecran est le cas courant. */
void
vid_fill(int xa, int xb, int ya, int yb, int layer, int idx)
{
	int row, col, lo, a, b, mask, b0, b1, c0, c1, full0, full1;
	if(xa < 0) xa = 0;
	if(ya < 0) ya = 0;
	if(xb > vid_w) xb = vid_w;
	if(yb > vid_h) yb = vid_h;
	if(xa >= xb || ya >= yb) return;
	full0 = planes >= 2 ? (idx & 1 ? 0xff : 0) : (idx ? 0xff : 0);
	full1 = planes >= 2 && (idx & 2) ? 0xff : 0;
	c0 = xa >> 3;
	c1 = (xb - 1) >> 3;
	for(row = ya; row < yb; row++)
		for(col = c0; col <= c1; col++) {
			lo = col << 3;
			if(lo >= xa && lo + 8 <= xb) {
				put_full(layer, row_off[row] + ((col >> 1) << step_sh) + (col & 1), full0, full1);
				continue;
			}
			a = xa > lo ? xa - lo : 0;
			b = xb - lo < 8 ? xb - lo : 8;
			mask = (0xff >> a) & (0xff << (8 - b)) & 0xff;
			b0 = full0 & mask;
			b1 = full1 & mask;
			put_bits(layer, row, col, mask, b0, b1);
		}
}

/* Dessine une tuile de 8x8 pixels (1bpp ou 2bpp) en (x, y) */
void
vid_tile(int x, int y, int addr, int ctrl)
{
	int j, c, v, idx, col0, s, src, ch1, ch2, m, b0, b1, mk[4];
	int ok[4], p0[4], p1[4]; /* par couleur : utilisee, bit du plan 0, bit du plan 1 (0 ou 0xff) */
	int layer = (ctrl >> 6) & 1, blend = ctrl & 0xf;
	int flipx = ctrl & 0x10, flipy = ctrl & 0x20, twobpp = ctrl & 0x80;
	int opaque = mod5[blend];
	if(x < -8 || y < -8 || x > vid_w || y > vid_h) return;
	col0 = ((x + 8) >> 3) - 1;
	s = (x + 8) & 7;
	for(c = 0; c < 4; c++) {
		v = blend_lut[blend][layer][c];
		idx = layer ? v >> 2 : v;
		ok[c] = (opaque || c) ? 0xff : 0;
		p0[c] = (planes >= 2 ? idx & 1 : idx) ? 0xff : 0;
		p1[c] = planes >= 2 && (idx & 2) ? 0xff : 0;
	}
	for(j = 0; j < 8; j++) {
		src = flipy ? addr + 7 - j : addr + j;
		ch1 = ram[src & 0xffff];
		ch2 = twobpp ? ram[(src + 8) & 0xffff] : 0;
		if(flipx) {
			ch1 = rev[ch1];
			ch2 = rev[ch2];
		}
		mk[3] = ch1 & ch2;
		mk[2] = ch2 & (ch1 ^ 0xff);
		mk[1] = ch1 & (ch2 ^ 0xff);
		mk[0] = (ch1 | ch2) ^ 0xff;
		m = (mk[0] & ok[0]) | (mk[1] & ok[1]) | (mk[2] & ok[2]) | (mk[3] & ok[3]);
		b0 = (mk[0] & p0[0]) | (mk[1] & p0[1]) | (mk[2] & p0[2]) | (mk[3] & p0[3]);
		b1 = (mk[0] & p1[0]) | (mk[1] & p1[1]) | (mk[2] & p1[2]) | (mk[3] & p1[3]);
		if(!s) {
			put_bits(layer, y + j, col0, m, b0, b1);
			continue;
		}
		put_bits(layer, y + j, col0, m >> s, b0 >> s, b1 >> s);
		put_bits(layer, y + j, col0 + 1, (m << (8 - s)) & 0xff,
			(b0 << (8 - s)) & 0xff, (b1 << (8 - s)) & 0xff);
	}
}

static int
plane_bit(const u8 *mem, int o, int bit)
{
	int v = (mem[o] >> bit) & 1;
	if(planes >= 2) v += 2 * ((mem[o + 2] >> bit) & 1);
	return v;
}

int
vid_layers(int x, int y)
{
	int o = y * line_b + (((x >> 3) >> 1) << step_sh) + ((x >> 3) & 1);
	int bit = 7 - (x & 7);
	return plane_bit(lay[0], o, bit) | (plane_bit(lay[1], o, bit) << 2);
}

int
vid_screen(int x, int y)
{
	int o = y * line_b + (((x >> 3) >> 1) << step_sh) + ((x >> 3) & 1);
	return plane_bit(scr, o, 7 - (x & 7));
}
