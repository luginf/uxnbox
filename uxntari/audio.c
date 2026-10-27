/* Suit le comportement du code audio de l'ancien depot uxn de Devine Lu Linvega (licence MIT, voir NOTICE). */
#include "audio.h"

#define NOTE_PERIOD 0x10000L /* AUDIO_RATE * 0x4000 / 11025 */
#define ADSR_STEP (AUDIO_RATE / 0xf)

typedef struct {
	unsigned long count, advance, period, age, a, d, s, r;
	long i, len;
	int volume[2];
	int repeat, active;
} Voice;

static Voice voices[AUDIO_VOICES];

static const unsigned long advances[12] = {
	0x80000, 0x879c8, 0x8facd, 0x9837f, 0xa1451, 0xaadc1,
	0xb504f, 0xbfc88, 0xcb2ff, 0xd7450, 0xe411f, 0xf1a1c};

void
audio_reset(void)
{
	int i;
	for(i = 0; i < AUDIO_VOICES; i++) voices[i].active = 0;
}

/* Niveau de l'enveloppe, 0 a 0x888 ; -1 quand elle est finie */
static long
envelope(const Voice *c, unsigned long age)
{
	if(!c->r) return 0x888;
	if(age < c->a) return 0x888L * age / c->a;
	if(age < c->d) return 0x444L * (2 * c->d - c->a - age) / (c->d - c->a);
	if(age < c->s) return 0x444;
	if(age < c->r) return 0x444L * (c->r - age) / (c->r - c->s);
	return -1;
}

void
audio_start(int voice)
{
	Voice *c = &voices[voice];
	const u8 *d = dev + 0x30 + 0x10 * voice;
	int pitch = d[0xf] & 0x7f, addr = d[0xc] << 8 | d[0xd], adsr = d[8] << 8 | d[9];
	c->active = 0;
	c->len = d[0xa] << 8 | d[0xb];
	if(c->len > 0x10000 - addr) c->len = 0x10000 - addr;
	c->volume[0] = d[0xe] >> 4;
	c->volume[1] = d[0xe] & 0xf;
	c->repeat = !(d[0xf] & 0x80);
	if(pitch >= 108 || !c->len) return;
	c->advance = advances[pitch % 12] >> (8 - pitch / 12);
	c->a = ADSR_STEP * (adsr >> 12);
	c->d = ADSR_STEP * (adsr >> 8 & 0xf) + c->a;
	c->s = ADSR_STEP * (adsr >> 4 & 0xf) + c->d;
	c->r = ADSR_STEP * (adsr & 0xf) + c->s;
	c->age = 0;
	c->i = 0;
	c->count = 0;
	/* un cycle unique (note) ou un echantillon qu'on rejoue */
	c->period = c->len <= 0x100 ? NOTE_PERIOD * 337 / 2 / c->len : NOTE_PERIOD;
	c->active = 1;
}

static void
finished(int voice)
{
	int vec = dev[0x30 + 0x10 * voice] << 8 | dev[0x31 + 0x10 * voice];
	if(vec) uxn_eval(vec);
}

/* samples : duree ecoulee, en echantillons a 44100 Hz (au plus 4000 a la fois) */
void
audio_update(long samples)
{
	int v;
	if(samples > 4000) samples = 4000;
	if(samples <= 0) return;
	for(v = 0; v < AUDIO_VOICES; v++) {
		Voice *c = &voices[v];
		int done = 0;
		if(!c->active) continue;
		c->count += c->advance * samples;
		c->i += c->count / c->period;
		c->count %= c->period;
		if(c->i >= c->len) {
			if(c->repeat) c->i %= c->len;
			else done = 1;
		}
		c->age += samples;
		/* la reference evalue l'enveloppe a l'age de l'echantillon precedent */
		if(envelope(c, c->age - 1) < 0) done = 1;
		if(done) {
			c->active = 0;
			finished(v);
		}
	}
}

int
audio_vu(int voice)
{
	const Voice *c = &voices[voice];
	int i, sum[2] = {0, 0};
	if(!c->active) return 0;
	for(i = 0; i < 2; i++) {
		long e;
		if(!c->volume[i]) continue;
		e = envelope(c, c->age);
		sum[i] = 1 + (e < 0 ? 0 : e) * c->volume[i] / 0x800;
		if(sum[i] > 0xf) sum[i] = 0xf;
	}
	return (sum[0] << 4) | sum[1];
}

int
audio_position(int voice)
{
	return voices[voice].i & 0xffff;
}

int
audio_voice(int voice, int *noise, long *hz, long *rate, int *vol)
{
	const Voice *c = &voices[voice];
	long e;
	int m;
	if(!c->active) return 0;
	e = envelope(c, c->age);
	m = c->volume[0] > c->volume[1] ? c->volume[0] : c->volume[1];
	*vol = e < 0 ? 0 : (int)(m * e / 0x888);
	*noise = c->len > 0x100;
	*hz = (long)(c->advance * 10 / 2504); /* 44100 * advance / 11042816 */
	*rate = (long)(c->advance >> 8);
	return 1;
}
