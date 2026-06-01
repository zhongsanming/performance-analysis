import sys

def _read(f):
    with open(f) as fp:
        return {
            tuple(int(x) for x in line.strip().split()[:3]): tuple(float(x) for x in line.strip().split()[3:])
            for line in fp
            if not line.startswith('#')
        }

def main():
    f0, f1 = sys.argv[1:]
    d0, d1 = _read(f0), _read(f1)
    for k, v0 in d0.items():
        assert k in d1
        for h in k:
            print(f"\t{h:5d}", end="")
        for a0, a1 in zip(v0, d1[k]):
            print(f"\t{a1/a0:2.6f}", end="")
        print()



if __name__ == '__main__':
    main()
