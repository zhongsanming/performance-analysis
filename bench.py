import math
import sys
import json
from pathlib import Path
from typing import Any, Callable, Optional, List, Tuple

import torch
import triton

import click

import flag_gems

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


def load_shapes(shape_file: Path) -> List[Tuple[int, int, int]]:
    with open(shape_file) as fp:
        return json.load(fp)


def bench(
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


@click.command()
@click.option("--shapes", type=Path, default=None)
@click.option("--start", type=int, default=128)
@click.option("--stop", type=int, default=4097)
@click.option("--step", type=int, default=128)
@click.option("--use-cudagraph", is_flag=True)
def main(shapes: Optional[Path], start: int, stop: int, step: int, use_cudagraph: bool):
    fn_bench: Callable[[Callable[[], Any]], float] = (
        triton.testing.do_bench_cudagraph if use_cudagraph else triton.testing.do_bench
    )
    SHAPES = [
        (m, k, n)
        for k in range(start, stop, step)
        for m in range(start, stop, step)
        for n in range(start, stop, step)
    ] if shapes is None else load_shapes(shapes)
    dtype = torch.float16

    header = f"#{'M':>4}\t{'K':>5}\t{'N':>5}"
    header += "".join(f"\t{col:>8}" for col in COLUMNS)
    print(header)
    for M, K, N in SHAPES:
        print(f"{M:5d}\t{K:5d}\t{N:5d}", end="")
        # Create test tensors
        a: torch.Tensor = torch.randn(M, K, dtype=dtype, device=flag_gems.device)
        b: torch.Tensor = torch.randn(K, N, dtype=dtype, device=flag_gems.device)

        bench(mm_no_tma, a, b, fn_bench)
        if mm_device_tma is not None:
            bench(mm_device_tma, a, b, fn_bench)
        if mm_host_tma is not None:
            bench(mm_host_tma, a, b, fn_bench)
        print()


if __name__ == "__main__":
    main()
