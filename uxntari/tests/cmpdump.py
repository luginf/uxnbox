# Compare deux dumps de couches : python3 cmpdump.py mine ref
# Le dump de reference commence apres un saut de page (la sortie de la ROM le precede).
import sys

a = open(sys.argv[1]).read().split("\n")
raw = open(sys.argv[2]).read()
b = (raw.split("\f", 1)[1] if "\f" in raw else raw).split("\n")
n = 0
if len(a) != len(b):
    print("hauteurs differentes", len(a), len(b))
    sys.exit(1)
for y, (la, lb) in enumerate(zip(a, b)):
    if la != lb:
        xs = [x for x in range(min(len(la), len(lb))) if la[x] != lb[x]]
        n += max(len(xs), 1)
        if n <= 12:
            print("ligne", y, "x =", xs[:10])
print("pixels differents :", n)
sys.exit(1 if n else 0)
