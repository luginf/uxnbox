/* Derive du style d'evaluation et du code de reference d'uxn/uxn11 de Devine Lu Linvega (licence MIT, voir NOTICE). */
#include "uxn.h"

/* Evaluateur dans le style de uxn11 (ISC) : un corps par opcode et par mode,
   pointeurs de pile sur 8 bits qui bouclent naturellement. */

u8 ram[65536];
u8 dev[256];
u8 stk[2][256];
u8 sp[2];
u8 (*on_dei)(u8 port);
void (*on_deo)(u8 port);

int
peek2(int a)
{
	return (ram[a & 0xffff] << 8) | ram[(a + 1) & 0xffff];
}

void
poke2(int a, int v)
{
	ram[a & 0xffff] = (v >> 8) & 0xff;
	ram[(a + 1) & 0xffff] = v & 0xff;
}

static u8
raw_dei(u8 port)
{
	return dev[port];
}

static void
raw_deo(u8 port)
{
	(void)port;
}

void
uxn_reset(int soft)
{
	int i;
	for(i = 0; i < 256; i++)
		dev[i] = stk[0][i] = stk[1][i] = 0;
	sp[0] = sp[1] = 0;
	for(i = soft ? 0x100 : 0; i < 65536; i++)
		ram[i] = 0;
	if(!on_dei) on_dei = raw_dei;
	if(!on_deo) on_deo = raw_deo;
}

#define Lb(o)       stk[r][(u8)(sp[r] - (o))]
#define Lx(m,o,o2)  ((m) ? Lb(o2) << 8 | Lb((o2) - 1) : Lb(o))
#define Pb(s,v)     stk[s][sp[s]++] = (v);
#define Px(m,s,v)   if(m) {const int t = (v); Pb(s, t >> 8) Pb(s, t)} else Pb(s, v)
#define Lda(m,u,o)  Pb(r, ram[o]) if(m) Pb(r, ram[(u)((o) + 1)])
#define Sta(u,o,v)  if(d) ram[o] = (v) >> 8, ram[(u)((o) + 1)] = (v); else ram[o] = (v);
#define MUTE        (void)x; (void)y; (void)z; (void)r; (void)d;

#define OP(opc,X,Y,Z,k1,k2,P) \
	case opc|0x00: { const int d=0,r=0,x=X,y=Y,z=Z; sp[r]-=d?k2:k1; P MUTE } break; \
	case opc|0x20: { const int d=1,r=0,x=X,y=Y,z=Z; sp[r]-=d?k2:k1; P MUTE } break; \
	case opc|0x40: { const int d=0,r=1,x=X,y=Y,z=Z; sp[r]-=d?k2:k1; P MUTE } break; \
	case opc|0x60: { const int d=1,r=1,x=X,y=Y,z=Z; sp[r]-=d?k2:k1; P MUTE } break; \
	case opc|0x80: { const int d=0,r=0,x=X,y=Y,z=Z; P MUTE } break; \
	case opc|0xa0: { const int d=1,r=0,x=X,y=Y,z=Z; P MUTE } break; \
	case opc|0xc0: { const int d=0,r=1,x=X,y=Y,z=Z; P MUTE } break; \
	case opc|0xe0: { const int d=1,r=1,x=X,y=Y,z=Z; P MUTE } break;

int
uxn_eval(u16 start)
{
	u16 pc = start;
	for(;;)
		switch(ram[pc++]) {
		/* BRK */ case 0x00: return 1;
		/* JCI */ case 0x20: { const u16 a = ram[pc] << 8 | ram[(u16)(pc + 1)]; pc += 2; if(stk[0][--sp[0]]) pc += a; } break;
		/* JMI */ case 0x40: { const u16 a = ram[pc] << 8 | ram[(u16)(pc + 1)]; pc += 2 + a; } break;
		/* JSI */ case 0x60: { const u16 a = ram[pc] << 8 | ram[(u16)(pc + 1)]; pc += 2; { const int r = 1; Pb(r, pc >> 8) Pb(r, pc) } pc += a; } break;
		/* LIT */ case 0x80: { const u8 r = 0; Lda(0, u16, pc); pc += 1; } break;
		/* LI2 */ case 0xa0: { const u8 r = 0; Lda(1, u16, pc); pc += 2; } break;
		/* LIr */ case 0xc0: { const u8 r = 1; Lda(0, u16, pc); pc += 1; } break;
		/* L2r */ case 0xe0: { const u8 r = 1; Lda(1, u16, pc); pc += 2; } break;
		/* INC */ OP(0x01, Lx(d,1,2), 0,         0,1,2, Px(d,r,x+1))
		/* POP */ OP(0x02, 0,         0,         0,1,2, {})
		/* NIP */ OP(0x03, Lx(d,1,2), 0,         0,2,4, Px(d,r,x))
		/* SWP */ OP(0x04, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,x) Px(d,r,y))
		/* ROT */ OP(0x05, Lx(d,1,2), Lx(d,2,4), Lx(d,3,6), 3,6, Px(d,r,y) Px(d,r,x) Px(d,r,z))
		/* DUP */ OP(0x06, Lx(d,1,2), 0,         0,1,2, Px(d,r,x) Px(d,r,x))
		/* OVR */ OP(0x07, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y) Px(d,r,x) Px(d,r,y))
		/* EQU */ OP(0x08, Lx(d,1,2), Lx(d,2,4), 0,2,4, Pb(r,x==y))
		/* NEQ */ OP(0x09, Lx(d,1,2), Lx(d,2,4), 0,2,4, Pb(r,y!=x))
		/* GTH */ OP(0x0a, Lx(d,1,2), Lx(d,2,4), 0,2,4, Pb(r,y>x))
		/* LTH */ OP(0x0b, Lx(d,1,2), Lx(d,2,4), 0,2,4, Pb(r,y<x))
		/* JMP */ OP(0x0c, Lx(d,1,2), 0,         0,1,2, pc=d?x:pc+(signed char)x;)
		/* JCN */ OP(0x0d, Lx(d,1,2), Lb((d)+2), 0,2,3, if(y) pc=d?x:pc+(signed char)x;)
		/* JSR */ OP(0x0e, Lx(d,1,2), 0,         0,1,2, Px(1,!r,pc) pc=d?x:pc+(signed char)x;)
		/* STH */ OP(0x0f, Lx(d,1,2), 0,         0,1,2, Px(d,!r,x))
		/* LDZ */ OP(0x10, Lx(0,1,1), 0,         0,1,1, Lda(d,u8,x))
		/* STZ */ OP(0x11, Lx(0,1,1), Lx(d,2,3), 0,2,3, Sta(u8,x,y))
		/* LDR */ OP(0x12, Lx(0,1,1), 0,         0,1,1, u16 t=pc+(signed char)x; Lda(d,u16,t))
		/* STR */ OP(0x13, Lx(0,1,1), Lx(d,2,3), 0,2,3, u16 t=pc+(signed char)x; Sta(u16,t,y))
		/* LDA */ OP(0x14, Lx(1,2,2), 0,         0,2,2, Lda(d,u16,x))
		/* STA */ OP(0x15, Lx(1,2,2), Lx(d,3,4), 0,3,4, Sta(u16,x,y))
		/* DEI */ OP(0x16, Lx(0,1,1), 0,         0,1,1, Pb(r,on_dei(x)) if(d) Pb(r,dev[(u8)(x+d)]))
		/* DEO */ OP(0x17, Lx(0,1,1), Lx(d,2,3), 0,2,3, if(d) dev[x]=y>>8; dev[(u8)(x+d)]=y; on_deo((u8)(x+d));)
		/* ADD */ OP(0x18, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y+x))
		/* SUB */ OP(0x19, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y-x))
		/* MUL */ OP(0x1a, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,(int)((unsigned)y*(unsigned)x)))
		/* DIV */ OP(0x1b, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,x?y/x:0))
		/* AND */ OP(0x1c, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y&x))
		/* ORA */ OP(0x1d, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y|x))
		/* EOR */ OP(0x1e, Lx(d,1,2), Lx(d,2,4), 0,2,4, Px(d,r,y^x))
		/* SFT */ OP(0x1f, Lx(0,1,1), Lx(d,2,3), 0,2,3, Px(d,r,(y>>(x&0xf))<<(x>>4)))
		}
	return 0;
}
