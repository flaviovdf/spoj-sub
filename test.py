import sys

for l in sys.stdin:
    d = int(l)
    if int(l) == 42:
        break
    print d
