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

    # we assume the order of the common keys is the same of all input files
    data = tuple(_read(inp) for inp in inputs)
    keys = tuple(k for k, _ in data)
    total_order = list(e for k in keys for e in k)
    values = tuple(v for _, v in data)
    common_keys = sorted(
        reduce(set[str].intersection, map(set, (k for k, _ in data))),
        key=lambda k: total_order.index(k),
    )

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
        dicts: tuple[dict[str, str]]
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


if __name__ == "__main__":
    main()
