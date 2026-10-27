# Produit refscreen.c, un uxn11 sans X11 qui ecrit les couches video en texte :
#   python3 mkref.py uxn11.c refscreen.c
# Le code ecran et le coeur sont ceux de la reference (lignes avant la partie X11).
import sys

src = open(sys.argv[1]).read().split("\n")
stop = next(i for i, l in enumerate(src) if l.startswith("static Display *emu_dpy;"))
txt = "\n".join(src[:stop])
for inc in ("<X11/Xlib.h>", "<X11/Xutil.h>", "<X11/keysymdef.h>", "<sys/timerfd.h>"):
    txt = txt.replace("#include " + inc, "")
main = r'''
static void emu_redraw(void) {}
static void emu_resize(void) {}
static void emu_screenshot(void) {}
int main(int argc, char **argv) {
	int frames = argc > 2 ? atoi(argv[2]) : 1, i, x, y;
	if(!system_boot(argv[1], 0)) return 1;
	screen_resize(640, 200);
	uxn_eval(0x100);
	for(i = 0; i < frames; i++) { if(screen_vector) uxn_eval(screen_vector); }
	fputs("\f", stdout);
	for(y = 0; y < screen_height; y++) {
		for(x = 0; x < screen_width; x++)
			putchar("0123456789abcdef"[screen_layers[(y + 8) * screen_wmar2 + x + 8] & 15]);
		putchar(10);
	}
	return 0;
}
'''
open(sys.argv[2], "w").write(txt + main)
