import sys
from pathlib import Path

import click

from performance_analysis import read_benchmark_result, BenchmarkData, BenchmarkMode, BenchmarkDtype, BenchmarkState


def flatten(
    data: dict[str, BenchmarkData],
) -> dict[tuple[str, BenchmarkMode, BenchmarkDtype, str], float]:
    return {
        # maybe str(res.shape_detail[0]) ? I don't think so
        # level is not important
        (detail.op_name, detail.mode, detail.dtype, str(res.shape_detail)): res.latency
        for _k, v in data.items()
        if v.result == BenchmarkState.Passed
        for detail in v.details
        for res in detail.result
        if res.latency is not None
    }


@click.command()
@click.option("-i", "--input", type=Path, required=True)
@click.option("-b", "--base", type=Path, required=True)
def main(input: Path, base: Path):
    assert input.is_dir()
    total: list[tuple[tuple[str, BenchmarkMode, BenchmarkDtype, str], tuple[float, float, float]]] = []
    for path in input.iterdir():
        data = flatten(read_benchmark_result(path))
        _base = base / path.name
        if not _base.exists():
            continue
        data_base = flatten(read_benchmark_result(_base))
        for key, lat in data.items():
            if (lat_base := data_base.get(key)) is None:
                print(f"{key} does not exist in base", file=sys.stderr)
                continue
            total.append((key, (lat_base, lat, lat_base / lat)))
    total.sort(key=lambda x: -x[1][2])
    print('operator\tbase\tafter\tspeedup\tmode\tdtype\tshape')
    for (name, mode, dtype, shape), (lat_base, lat, speedup) in total:
        print(f'{name}\t{lat_base:.6f}\t{lat:.6f}\t{speedup:.4f}\t{mode.value}\t{dtype.value}\t"{shape.replace(" ", "")}"')


if __name__ == "__main__":
    main()
