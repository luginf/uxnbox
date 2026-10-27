# Genere une ROM uxn aleatoire qui dessine : python3 genrom.py graine sortie.rom [largeur hauteur]
import random, sys

seed = int(sys.argv[1])
out = sys.argv[2]
rnd = random.Random(seed)
w = int(sys.argv[3]) if len(sys.argv) > 3 else rnd.choice([640, 200, 333, 64, 513 - 512 + 100])
h = int(sys.argv[4]) if len(sys.argv) > 4 else rnd.choice([200, 100, 77, 40])
code = bytearray()


def lit(v):
    code.extend([0x80, v & 0xff])


def lit2(v):
    code.extend([0xa0, (v >> 8) & 0xff, v & 0xff])


def deo(port, v):
    lit(v)
    lit(port)
    code.append(0x17)


def deo2(port, v):
    lit2(v)
    lit(port)
    code.append(0x37)


DATA = 0x4000
deo2(0x22, w)
deo2(0x24, h)
for _ in range(rnd.randint(50, 250)):
    k = rnd.random()
    deo(0x26, rnd.choice([0, 0, 1, 2, 3, 4, 7, rnd.randrange(256)]))
    deo2(0x28, rnd.randint(-14, w + 14))
    deo2(0x2a, rnd.randint(-14, h + 14))
    if k < 0.2:
        deo(0x2e, rnd.randrange(256))
    else:
        deo2(0x2c, DATA + rnd.randrange(0, 1900))
        deo(0x2f, rnd.randrange(256))
code.append(0x00)
rom = bytes(code)
assert len(rom) < DATA - 0x100
rom = rom + bytes(DATA - 0x100 - len(rom)) + bytes(rnd.randrange(256) for _ in range(2048))
open(out, "wb").write(rom)
