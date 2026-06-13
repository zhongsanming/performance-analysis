"""Vector Addition from triton tutorial, removed most of the comment for clarity"""

import torch

import triton
import triton.language as tl

DEVICE = triton.runtime.driver.active.get_active_torch_device()


# add a dead simple autotune config
@triton.autotune(
    configs=[
        triton.Config({"BLOCK_SIZE": 64}, num_warps=2),
        triton.Config({"BLOCK_SIZE": 128}, num_warps=4),
    ],
    key=["BLOCK_SIZE"],
    do_bench=triton.testing.do_bench_cudagraph
)
@triton.jit
def add_kernel(x_ptr, y_ptr, output_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    output = x + y
    tl.store(output_ptr + offsets, output, mask=mask)


def add(x: torch.Tensor, y: torch.Tensor):
    output = torch.empty_like(x)
    assert x.device == DEVICE and y.device == DEVICE and output.device == DEVICE
    n_elements = output.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)
    # remove fixed BLOCK_SIZE
    add_kernel[grid](x, y, output, n_elements)
    return output


if __name__ == "__main__":
    torch.manual_seed(0)
    size = 98432
    x = torch.rand(size, device=DEVICE)
    y = torch.rand(size, device=DEVICE)

    # use it with cuda graph before any cache exists
    # the sync call inside do_bench_cudagraph will invalidate the cuda graph capture
    with torch.cuda.stream(torch.cuda.Stream()):
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            add(x, y)
        torch.cuda.synchronize()

        g.replay()
        torch.cuda.synchronize()
