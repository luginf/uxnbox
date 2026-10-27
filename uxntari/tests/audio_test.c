/* Compare audio.c avec le code de reference de l'ancien emulateur uxn (audio.c du depot
   git.sr.ht/~rabbits/uxn, commit 2903488) : instants de fin des notes, volume (port output)
   et position. Voir audio.sh. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "audio.h"
typedef unsigned char Uint8; typedef signed short Sint16; typedef unsigned short Uint16;
Uint8 ref_get_vu(int); Uint16 ref_get_position(int); int ref_audio_render(int,Sint16*,Sint16*); void ref_audio_start(int,Uint8*);
extern struct { Uint8 ram[65536]; } uxn;
int ref_done[4];
int main(void)
{
	int t, bad = 0;
	static Sint16 buf[2 * 441];
	for(t = 0; t < 400; t++) {
		int step, mdone = -1, rdone = -1, i, v = t % 4, pitch;
		u8 *d = dev + 0x30 + 16 * v;
		srand(t);
		for(i = 0; i < 65536; i++) ram[i] = uxn.ram[i] = rand();
		memset(dev, 0, 256);
		d[8] = rand(); d[9] = rand();
		if(t % 3) { d[8] &= 0x33; d[9] &= 0x33; }
		d[0xa] = (t % 5 == 0) ? rand() & 3 : (t % 5 == 1) ? 0 : 0;
		d[0xb] = rand();
		if(t % 5 >= 2) { d[0xa] = 0; d[0xb] = 1 + rand() % 255; }
		d[0xc] = rand() & 0x7f; d[0xd] = rand();
		d[0xe] = rand();
		pitch = rand() % 112;
		d[0xf] = pitch | ((t & 1) ? 0x80 : 0);
		{
			Uint8 rd[16]; int ok = pitch < 108 && (d[0xa] << 8 | d[0xb]);
			if(!ok) continue;
			memcpy(rd, d, 16);
			/* passe 1 : instants de fin (ref_get_vu arrete la voix de reference : pas appele ici) */
			memset(ref_done, 0, sizeof ref_done);
			ref_audio_start(v, rd);
			audio_start(v);
			for(step = 0; step < 400; step++) {
				int noise, vol; long hz, rate;
				ref_audio_render(v, buf, buf + 2 * 441);
				audio_update(441);
				if(ref_done[v] && rdone < 0) rdone = step;
				if(!audio_voice(v, &noise, &hz, &rate, &vol) && mdone < 0) mdone = step;
				if(rdone >= 0 || mdone >= 0) break;
			}
			/* passe 2 : volume et position pendant la note */
			ref_audio_start(v, rd);
			audio_start(v);
			for(step = 0; step < 400; step++) {
				int noise, vol, vu1, vu2, p1, p2; long hz, rate;
				if(!audio_voice(v, &noise, &hz, &rate, &vol)) break;
				vu1 = ref_get_vu(v); vu2 = audio_vu(v);
				p1 = ref_get_position(v); p2 = audio_position(v);
				if(p1 == 0 && p2 != 0 && step > 0) break; /* voix de reference arretee par ref_get_vu */
				if(vu1 != vu2 || abs(p1 - p2) > 1) { printf("t=%d step=%d vu %d/%d pos %d/%d\n", t, step, vu1, vu2, p1, p2); bad++; break; }
				ref_audio_render(v, buf, buf + 2 * 441);
				audio_update(441);
			}
		}
		if(rdone != mdone) { printf("t=%d fin ref=%d mine=%d pitch=%d\n", t, rdone, mdone, pitch); bad++; }
	}
	printf("%d erreurs\n", bad);
	return bad != 0;
}
