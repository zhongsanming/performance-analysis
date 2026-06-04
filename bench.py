import json
import math
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal

import click
import flag_gems  # pyright: ignore[reportMissingImports]
import torch
from torch import Tensor
from triton.testing import do_bench, do_bench_cudagraph, _summarize_statistics  # pyright: ignore[reportMissingImports, reportUnknownVariableType]


def do_bench_cudagraph_e2e(
    fn: Callable[[], Any],  # pyright: ignore[reportExplicitAny]
    rep: int = 20,
    grad_to_none: list[Tensor] | None = None,
    quantiles: list[float] | None = None,
    return_mode: Literal["min", "max", "mean", "median", "all"] = "mean",
) -> float:
    """
    Benchmark the runtime of the provided function.

    :param fn: Function to benchmark
    :type fn: Callable
    :param rep: Repetition time (in ms)
    :type rep: int
    :param grad_to_none: Reset the gradient of the provided tensor to None
    :type grad_to_none: torch.tensor, optional
    :param return_mode: The statistical measure to return. Options are "min", "max", "mean", "median", or "all". Default is "mean".
    :type return_mode: str
    """
    assert return_mode in ["min", "max", "mean", "median", "all"]

    with torch.cuda.stream(torch.cuda.Stream()):
        # warmup
        fn()
        if grad_to_none is not None:
            for x in grad_to_none:
                _ = x.detach_()
                _ = x.requires_grad_(True)
                x.grad = None
        # step 1 - we estimate the amount of time the kernel call takes
        # NOTE: this estimate isn't super accurate because the GPU isn't warmed up at this point
        #       but it is probably good enough
        # NOTE: we don't use a graph to estimate the runtime because creating a graph is expensive,
        #       ~300ms on A100, so we default to the same method used in `do_bench` (minus the L2
        #       cache flush).
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        start_event.record()
        for _ in range(5):
            fn()
        end_event.record()
        torch.cuda.synchronize()
        estimate_ms = start_event.elapsed_time(end_event) / 5
        # Rewrite to avoid possible division by 0 issues with fast benchmarks
        n_repeat = 1000 if estimate_ms == 0 else max(1, int(rep / estimate_ms))
        # step 2 - construct a cuda graph with `n_repeat` unrolled function calls to minimize
        # host overhead
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            for _ in range(n_repeat):
                if grad_to_none is not None:
                    for x in grad_to_none:
                        x.grad = None
                fn()
        torch.cuda.synchronize()
        # measure time and return
        ret: list[float] = []
        n_retries = 10
        for _ in range(n_retries):
            start = time.time()
            g.replay()
            torch.cuda.synchronize()
            end = time.time()
            ret.append((end - start) * 1000 / n_repeat)
        return _summarize_statistics(ret, quantiles, return_mode)  # pyright: ignore[reportUnknownVariableType]


def do_bench_e2e(fn: Callable[[], Any], rep: int = 20) -> float:  # pyright: ignore[reportExplicitAny]
    """
    Benchmark the runtime of the provided function.

    :param fn: Function to benchmark
    :type fn: Callable
    :param rep: Repetition time (in ms)
    :type rep: int
    """
    # warm up
    fn()
    start = time.time()
    for _ in range(5):
        fn()
    torch.cuda.synchronize()
    end = time.time()
    estimate_ms = (end - start) * 1000 / 5
    n_repeat = 1000 if estimate_ms == 0 else max(1, int(rep / estimate_ms))

    start = time.time()
    for _ in range(n_repeat):
        fn()
    torch.cuda.synchronize()
    end = time.time()
    latency = (end - start) * 1000 / n_repeat
    return latency


class BenchFunction(Enum):
    DoBench = "do_bench"
    DoBenchEE = "do_bench_e2e"
    DoBenchCudaGraph = "do_bench_cudagraph"
    DoBenchCudaGraphEE = "do_bench_cudagraph_e2e"

    def func(self) -> Callable[[Callable[[], Any]], float]:  # pyright: ignore[reportExplicitAny]
        if self == BenchFunction.DoBench:
            return do_bench  # pyright: ignore[reportUnknownVariableType]
        if self == BenchFunction.DoBenchEE:
            return do_bench_e2e
        if self == BenchFunction.DoBenchCudaGraph:
            return do_bench_cudagraph  # pyright: ignore[reportUnknownVariableType]
        if self == BenchFunction.DoBenchCudaGraphEE:
            return do_bench_cudagraph_e2e
        raise ValueError(f"Unknown bench function: {self}")


def benchmark(
    fn: Callable[[Tensor, Tensor], Tensor],
    a: Tensor,
    b: Tensor,
    fn_bench: Callable[[Callable[[], Any]], float],  # pyright: ignore[reportExplicitAny]
):
    try:
        ms = fn_bench(lambda: fn(a.clone(), b.clone()))
    except Exception:
        ms = math.nan
    print(f"\t{ms:.6f}", end="")


def load_shapes(shape_file: Path) -> list[tuple[int, int, int]]:
    with open(shape_file) as fp:
        return json.load(fp)  # pyright: ignore[reportAny]


def gen_shapes(start: int, stop: int, step: int):
    return [
        (m, k, n)
        for k in range(start, stop, step)
        for m in range(start, stop, step)
        for n in range(start, stop, step)
    ]


def get_impl(vanilla: bool) -> list[tuple[str, Callable[[Tensor, Tensor], Tensor]]]:
    if vanilla:
        return [("torch.mm", torch.matmul)]

    from flag_gems.ops.mm import mm_no_tma  # pyright: ignore[reportMissingImports, reportUnknownVariableType]

    try:
        from flag_gems.runtime.backend._nvidia.hopper.ops.mm import (  # pyright: ignore[reportMissingImports]
            mm_dev_tma,  # pyright: ignore[reportUnknownVariableType]
            mm_host_tma,  # pyright: ignore[reportUnknownVariableType]
        )

        return [
            ("no_tma", mm_no_tma),
            ("dev_tma", mm_dev_tma),
            ("host_tma", mm_host_tma),
        ]
    except Exception as e:
        print(
            f"Failed to import mm_host_tma, mm_device_tma due to {e}"  # pyright: ignore[reportImplicitStringConcatenation]
            f" this is expected when running with triton <= 3.3",
            file=sys.stderr,
        )
        return [("v33", mm_no_tma)]


@click.command()
@click.option("--shapes", type=Path, default=None)
@click.option("--start", type=int, default=128)
@click.option("--stop", type=int, default=4097)
@click.option("--step", type=int, default=128)
@click.option("--bench", type=BenchFunction, default=BenchFunction.DoBench)
@click.option("--vanilla", is_flag=True)
def main(
    shapes: Path | None,
    start: int,
    stop: int,
    step: int,
    bench: BenchFunction,
    vanilla: bool,
):
    impls = get_impl(vanilla)
    fn_bench = bench.func()
    SHAPES = gen_shapes(start, stop, step) if shapes is None else load_shapes(shapes)
    dtype = torch.float16  # pyright: ignore[reportPrivateImportUsage]

    with flag_gems.use_gems():  # pyright: ignore[reportUnknownMemberType]
        header = f"#{'M':>4}\t{'K':>5}\t{'N':>5}"
        header += "".join(f"\t{name:>8}" for name, _ in impls)
        print(header)
        for M, K, N in SHAPES:
            print(f"{M:5d}\t{K:5d}\t{N:5d}", end="")
            # Create test tensors
            a: Tensor = torch.randn(M, K, dtype=dtype, device=flag_gems.device)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            b: Tensor = torch.randn(K, N, dtype=dtype, device=flag_gems.device)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

            for _, impl in impls:
                benchmark(impl, a, b, fn_bench)
            print()


if __name__ == "__main__":
    main()
