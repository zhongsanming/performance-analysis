from collections import defaultdict
from pathlib import Path

import click
import numpy as np

from performance_analysis import read_benchmark_result, BenchmarkData, BenchmarkMode, BenchmarkDtype, BenchmarkState


def is_jitter(latencies: list[float]) -> bool:
    if len(latencies) < 4:
        return False
    arr = np.array(latencies)
    # mean = np.mean(arr)
    # std = np.std(arr)
    # cv = std / mean if mean > 0 else 0
    # print(cv)

    # diffs = np.abs(np.diff(arr))
    # avg_consecutive_jitter = np.mean(diffs)

    p25 = np.percentile(arr, 25)
    p75 = np.percentile(arr, 75)
    iqr = p75 - p25
    ub = p75 + 6.0 * iqr
    # print(f"{arr=}, {p25=}, {p75=}, {iqr=}, {ub=}")
    return np.any(arr > ub)


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
@click.argument('input', nargs=-1)
def main(input: list[Path]):
    total = defaultdict(list)
    for path in input:
        for k, v in flatten(read_benchmark_result(path)).items():
            total[k].append(v)
    total = {k: sorted(v) for k, v in total.items()}
    for k, v in total.items():
        if is_jitter(v):
            print(f'{k} => {v}')


if __name__ == "__main__":
    main()

