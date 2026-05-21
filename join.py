from pathlib import Path
from functools import reduce

import click


def _key(values: dict[str, str], keys: list[str]) -> list[str]:
    return [values[k] for k in keys]


def _to_dict(keys: list[str], values: list[str]) -> dict[str, str]:
    assert len(keys) == len(values)
    return dict(zip(keys, values))


def _read(f: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(f) as fp:
        header: str = next(fp)
        if not header.startswith("#"):
            raise ValueError("No header is found, can't perform join.")

        keys = header[1:].strip().split()
        return keys, [
            _to_dict(keys, [v.strip() for v in line.strip().split()]) for line in fp
        ]


@click.command()
@click.pass_context
@click.argument("inputs", nargs=-1, type=click.Path())
def main(ctx: click.Context, inputs: tuple[Path, ...]):
    if len(inputs) == 0:
        click.echo(ctx.get_help())
        return

    data = tuple(_read(inp) for inp in inputs)
    keys = tuple(k for k, _ in data)
    total_order = list(e for k in keys for e in k)
    values = tuple(v for _, v in data)
    common_keys = sorted(
        reduce(set[str].intersection, map(set, (k for k, _ in data))),
        key=lambda k: total_order.index(k),
    )
    # value_keys = sorted(reduce(set[str].union, map(set, (k for k, _ in data))) - set(common_keys), key=lambda k: total_order.index(k))
    # values = tuple(sorted(value, key=lambda d: _key(d, common_keys)) for value in values)

    print("#", end="")
    for key in common_keys:
        print(f"\t{key:>8}", end="")
    for keys, _ in data:
        for k in keys:
            if k in common_keys:
                continue
            print(f"\t{k:>8}", end="")
    print()

    for dicts in zip(*values):
        common = [_key(d, common_keys) for d in dicts]
        assert len(set(",".join(x) for x in common)) == 1
        key = common[0]
        for k in key:
            print(f"\t{k:>8}", end="")
        for d in dicts:
            for k, v in d.items():
                if k in common_keys:
                    continue
                print(f"\t{v:>8}", end="")
        print()

    # f0, f1 = sys.argv[1:]
    # d0, d1 = _read(f0), _read(f1)
    # result = dict()
    # for (k0, v0), (k1, v1) in zip(d0.items(), d1.items()):
    #     assert k0 == k1
    #     result[k0] = v0 + v1

    # print(
    #     f"#{'M':>4}\t{'K':>5}\t{'N':>5}\t{'v3.3':>8}\t{'no_tma':>8}\t{'dev_tma':>8}\t{'host_tma':>8}"
    # )
    # for (m, k, n), [v33, no_tma, dev_tma, host_tma] in result.items():
    #     print(
    #         f"{m:5d}\t{k:5d}\t{n:5d}\t{v33:.6f}\t{no_tma:.6f}\t{dev_tma:.6f}\t{host_tma:.6f}"
    #     )


if __name__ == "__main__":
    main()
