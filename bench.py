import math
import sys
import json
import time
import statistics
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, List, Tuple

import torch

import click

import flag_gems

from triton.testing import do_bench, do_bench_cudagraph

from flag_gems.ops.mm import mm_no_tma

try:
    from flag_gems.runtime.backend._nvidia.hopper.ops.mm import (
        mm_host_tma,
        mm_device_tma,
    )

    COLUMNS = ("no_tma", "dev_tma", "host_tma")
except Exception as e:
    print(
        f"Failed to import mm_host_tma, mm_device_tma due to {e}"
        f" this is expected when running with triton <= 3.3",
        file=sys.stderr,
    )
    mm_host_tma = None
    mm_device_tma = None
    COLUMNS = ("v33",)


def _quantile(a, q):
    n = len(a)
    a = sorted(a)

    def get_quantile(q):
        if not (0 <= q <= 1):
            raise ValueError("Quantiles must be in the range [0, 1]")
        point = q * (n - 1)
        lower = math.floor(point)
        upper = math.ceil(point)
        t = point - lower
        return (1 - t) * a[lower] + t * a[upper]

    return [get_quantile(q) for q in q]


def _summarize_statistics(times, quantiles, return_mode):
    if quantiles is not None:
        ret = _quantile(times, quantiles)
        if len(ret) == 1:
            ret = ret[0]
        return ret
    if return_mode == "all":
        return times
    elif return_mode == "min":
        return min(times)
    elif return_mode == "max":
        return max(times)
    elif return_mode == "mean":
        return statistics.mean(times)
    elif return_mode == "median":
        return statistics.median(times)


def do_bench_cudagraph_e2e(fn, rep=20, grad_to_none=None, quantiles=None, return_mode="mean"):
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
    import torch
    assert return_mode in ["min", "max", "mean", "median", "all"]

    with torch.cuda.stream(torch.cuda.Stream()):
        # warmup
        fn()
        if grad_to_none is not None:
            for x in grad_to_none:
                x.detach_()
                x.requires_grad_(True)
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
        ret = []
        n_retries = 10
        for _ in range(n_retries):
            start = time.time()
            g.replay()
            torch.cuda.synchronize()
            end = time.time()
            ret += [(end - start) * 1000 / n_repeat]
        return _summarize_statistics(ret, quantiles, return_mode)


class BenchFunction(Enum):
    DoBench = "do_bench"
    DoBenchCudaGraph = "do_bench_cudagraph"
    DoBenchCudaGraphEE = "do_bench_cudagraph_e2e"

    def func(self) -> Callable[[Callable[[], Any]], float]:
        if self == BenchFunction.DoBench:
            return do_bench
        if self == BenchFunction.DoBenchCudaGraph:
            return do_bench_cudagraph
        if self == BenchFunction.DoBenchCudaGraphEE:
            return do_bench_cudagraph_e2e
        raise ValueError(f"Unknown bench function: {self}")

def benchmark(
    fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    a: torch.Tensor,
    b: torch.Tensor,
    fn_bench: Callable[[Callable[[], Any]], float],
):
    try:
        ms = fn_bench(lambda: fn(a, b))
    except Exception:
        ms = math.nan
    print(f"\t{ms:.6f}", end="")


def load_shapes(shape_file: Path) -> List[Tuple[int, int, int]]:
    with open(shape_file) as fp:
        return json.load(fp)


def gen_shapes(start: int, stop: int, step: int):
    return  [
        (m, k, n)
        for k in range(start, stop, step)
        for m in range(start, stop, step)
        for n in range(start, stop, step)
    ]


@click.command()
@click.option("--shapes", type=Path, default=None)
@click.option("--start", type=int, default=128)
@click.option("--stop", type=int, default=4097)
@click.option("--step", type=int, default=128)
@click.option("--bench", type=BenchFunction, default=BenchFunction.DoBench)
def main(shapes: Optional[Path], start: int, stop: int, step: int, bench: BenchFunction):
    fn_bench = bench.func()
    SHAPES = gen_shapes(start, stop, step) if shapes is None else load_shapes(shapes)
    dtype = torch.float16

    header = f"#{'M':>4}\t{'K':>5}\t{'N':>5}"
    header += "".join(f"\t{col:>8}" for col in COLUMNS)
    print(header)
    for M, K, N in SHAPES:
        print(f"{M:5d}\t{K:5d}\t{N:5d}", end="")
        # Create test tensors
        a: torch.Tensor = torch.randn(M, K, dtype=dtype, device=flag_gems.device)
        b: torch.Tensor = torch.randn(K, N, dtype=dtype, device=flag_gems.device)

        benchmark(mm_no_tma, a, b, fn_bench)
        if mm_device_tma is not None:
            benchmark(mm_device_tma, a, b, fn_bench)
        if mm_host_tma is not None:
            benchmark(mm_host_tma, a, b, fn_bench)
        print()


if __name__ == "__main__":
    main()
