/* Banc d'essai sur l'hote : charge une ROM, relie la console a stdin/stdout
   et peut sauvegarder l'etat des couches video.
   Usage : harness [-f images] [-d fichier] [-1|-4] [-n] rom.rom [args..]
     -f N   evalue N fois le vecteur ecran
     -d F   ecrit les couches (un chiffre hexa par pixel : fond + 4 * premier plan)
     -1     ecran monochrome (haute resolution) au lieu de moyenne resolution
     -4     basse resolution (320x200) au lieu de moyenne resolution
     -n     ne lit pas stdin */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../uxn.h"
#include "../dev.h"
#include "../vid.h"

static u8 scrbuf[VID_BYTES];

static void out_stdout(u8 c) { fputc(c, stdout); }
static void out_stderr(u8 c) { fputc(c, stderr); }

int
main(int argc, char **argv)
{
	int i, x, y, v, bad = 0, frames = 0, planes = 2, nostdin = 0, nargs = 0, c;
	const char *dump = NULL, *rom = NULL;
	for(i = 1; i < argc; i++) {
		if(!rom && !strcmp(argv[i], "-f") && i + 1 < argc) frames = atoi(argv[++i]);
		else if(!rom && !strcmp(argv[i], "-d") && i + 1 < argc) dump = argv[++i];
		else if(!rom && !strcmp(argv[i], "-1")) planes = 1;
		else if(!rom && !strcmp(argv[i], "-4")) planes = 4;
		else if(!rom && !strcmp(argv[i], "-n")) nostdin = 1;
		else if(!rom) rom = argv[i];
		else nargs++;
	}
	if(!rom) {
		puts("usage: harness [-f images] [-d fichier] [-1|-4] [-n] rom.rom [args..]");
		return 1;
	}
	vid_init(scrbuf, planes);
	uxn_reset(0);
	on_stdout = out_stdout;
	on_stderr = out_stderr;
	if(!dev_load(rom)) {
		printf("Could not load %s\n", rom);
		return 1;
	}
	dev_boot(nargs > 0);
	uxn_eval(0x100);
	for(i = argc - nargs; i < argc; i++)
		console_send_arg(argv[i], i == argc - 1);
	for(i = 0; i < frames; i++)
		if(!dev_halted()) screen_frame();
	if(!nostdin && !dev_halted()) {
		while((c = getchar()) != EOF) console_input(c, CONSOLE_STD);
		console_input(10, CONSOLE_END);
	}
	/* Verification interne : l'ecran doit etre la composition des couches */
	for(y = 0; y < vid_h; y++)
		for(x = 0; x < vid_w; x++) {
			v = vid_layers(x, y);
			if(planes == 1) v = ((v & 3) || (v >> 2)) ? 1 : 0;
			else v = (v >> 2) ? v >> 2 : v & 3;
			if(vid_screen(x, y) != v) bad++;
		}
	if(bad) fprintf(stderr, "screen/layers mismatch: %d\n", bad);
	if(dump) {
		FILE *f = fopen(dump, "w");
		for(y = 0; y < vid_h; y++) {
			for(x = 0; x < vid_w; x++)
				fputc("0123456789abcdef"[vid_layers(x, y)], f);
			fputc('\n', f);
		}
		fclose(f);
	}
	dev_shutdown();
	return dev[0xf] & 0x7f;
}
