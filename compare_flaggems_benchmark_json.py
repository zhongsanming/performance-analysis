import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import click


def list_to_tuple(l):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]  # noqa: E741
    if not isinstance(l, list):
        return l  # pyright: ignore[reportUnknownVariableType]
    return tuple(list_to_tuple(k) for k in l)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


class BenchmarkState(Enum):
    Passed = "passed"
    Failed = "failed"
    Skipped = "skipped"


class BenchmarkLevel(Enum):
    Core = "core"
    Comprehensive = "comprehensive"


class BenchmarkMode(Enum):
    Operator = "operator"
    Kernel = "kernel"
    Wrapper = "wrapper"


class BenchmarkDtype(Enum):
    bfloat16 = "torch.bfloat16"
    float16 = "torch.float16"
    float32 = "torch.float32"
    float64 = "torch.float64"
    int16 = "torch.int16"
    int32 = "torch.int32"
    complex64 = "torch.complex64"
    # bool = "torch.bool"


@dataclass
class BenchmarkResult:
    legacy_shape: str | None
    shape_detail: tuple[Any, ...]  # pyright: ignore[reportExplicitAny]
    latency_base: float | None
    latency: float | None
    gbps_base: float | None
    gbps: float | None
    speedup: float | None
    accuracy: float | None
    tflops: float | None
    utilization: float | None
    compared_speedup: float | None
    error_msg: str | None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BenchmarkResult":  # pyright: ignore[reportExplicitAny]
        legacy_shape: str | None = data.get("legacy_shape")
        shape_detail: tuple[Any, ...] = list_to_tuple(data.get("shape_detail", []))  # pyright: ignore[reportAny, reportExplicitAny, reportUnknownVariableType]
        latency_base: float | None = data.get("latency_base")
        latency: float | None = data.get("latency")
        gbps_base: float | None = data.get("gbps_base")
        gbps: float | None = data.get("gbps")
        speedup: float | None = data.get("speedup")
        accuracy: float | None = data.get("accuracy")
        tflops: float | None = data.get("tflops")
        utilization: float | None = data.get("utilization")
        compared_speedup: float | None = data.get("compared_speedup")
        error_msg: str | None = data.get("error_msg")
        return BenchmarkResult(
            legacy_shape=legacy_shape,
            shape_detail=shape_detail,
            latency_base=latency_base,
            latency=latency,
            gbps_base=gbps_base,
            gbps=gbps,
            speedup=speedup,
            accuracy=accuracy,
            tflops=tflops,
            utilization=utilization,
            compared_speedup=compared_speedup,
            error_msg=error_msg,
        )


@dataclass
class BenchmarkDetail:
    op_name: str
    dtype: BenchmarkDtype
    mode: BenchmarkMode
    level: BenchmarkLevel
    result: list[BenchmarkResult]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BenchmarkDetail":  # pyright: ignore[reportExplicitAny]
        op_name: str = data.get("op_name", "")  # pyright: ignore[reportAny]
        dtype: BenchmarkDtype = BenchmarkDtype(data.get("dtype", ""))
        mode: BenchmarkMode = BenchmarkMode(data.get("mode", ""))
        level: BenchmarkLevel = BenchmarkLevel(data.get("level", ""))
        result: list[BenchmarkResult] = [
            BenchmarkResult.from_dict(res)  # pyright: ignore[reportAny]
            for res in data.get("result", [])  # pyright: ignore[reportAny]
        ]
        return BenchmarkDetail(
            op_name=op_name, dtype=dtype, mode=mode, level=level, result=result
        )


@dataclass
class BenchmarkData:
    details: list[BenchmarkDetail]
    result: BenchmarkState
    test_case: str
    reason: str | None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BenchmarkData":  # pyright: ignore[reportExplicitAny]
        details: list[BenchmarkDetail] = [
            BenchmarkDetail.from_dict(detail)  # pyright: ignore[reportAny]
            for detail in data.get("details", [])  # pyright: ignore[reportAny]
        ]
        result: BenchmarkState = BenchmarkState(data.get("result", "passed"))
        test_case: str = data.get("test_case", "")  # pyright: ignore[reportAny]
        reason: str | None = data.get("reason")
        return BenchmarkData(
            details=details, result=result, test_case=test_case, reason=reason
        )


def read_benchmark_result(path: Path) -> dict[str, BenchmarkData]:
    with open(path) as fp:
        raw: dict[str, dict[str, Any]] = json.load(fp)  # pyright: ignore[reportExplicitAny, reportAny]
        return {k: BenchmarkData.from_dict(v) for k, v in raw.items()}


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
            total.append((key, (lat_base, lat, (lat_base - lat) / lat * 100)))
    total.sort(key=lambda x: -x[1][2])
    print('"operator","base","after","speedup","mode","dtype","shape"')
    for (name, mode, dtype, shape), (lat_base, lat, speedup) in total:
        print(f'"{name}",{lat_base:.4f},{lat:.4f},{speedup:.2f}%,"{mode}","{dtype}","{shape}"')
    return
    _res = dict(map(lambda x: (x[0][0], x[1]), total))
    # print(_res)
    for name, (lat_base, lat, speedup) in sorted(_res.items(), key=lambda x: x[1]):
        if speedup < 5.0:
            continue
        print(f"{name} => {speedup}%")
    n_total = len(_res)
    n_speedup = len(list(filter(lambda x: x[1][2] >= 5.0, _res.items())))
    print(f'{n_speedup} / {n_total} => {n_speedup / n_total}')
    # _res = defaultdict(bool)
    # for (name, _, _, _), speedup in total:
        # _res[name] = _res[name] or speedup > 5.0
    # print(len(list(filter(lambda k: k[1], _res.items()))) / len(_res))


if __name__ == "__main__":
    main()
