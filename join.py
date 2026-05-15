import sys


def main():
    def _key(items):
        return int(items[0]), int(items[1]), int(items[2])

    def _value(items):
        return tuple(float(item) for item in items[3:])

    def _read(f):
        with open(f) as fp:
            return {
                _key(line.strip().split()): _value(line.strip().split())
                for line in fp
                if not line.strip().startswith("#")
            }

    # assume 3.3, 3.4
    f0, f1 = sys.argv[1:]
    d0, d1 = _read(f0), _read(f1)
    result = dict()
    for (k0, v0), (k1, v1) in zip(d0.items(), d1.items()):
        assert k0 == k1
        result[k0] = v0 + v1

    print(f"#{'M':>4}\t{'K':>5}\t{'N':>5}\t{'v3.3':>8}\t{'no_tma':>8}\t{'dev_tma':>8}\t{'host_tma':>8}")
    for (m, k, n), [v33, no_tma, dev_tma, host_tma] in result.items():
        print(f"{m:5d}\t{k:5d}\t{n:5d}\t{v33:.6f}\t{no_tma:.6f}\t{dev_tma:.6f}\t{host_tma:.6f}")


if __name__ == "__main__":
    main()
