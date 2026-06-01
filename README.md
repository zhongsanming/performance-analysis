# Performance Analysis

## benchmark

To reproduce benchmark

 1. install FlagTree v3.3 and v3.4 via venv

 2. install extract_mm branch of https://github.com/zhongsanming/FlagGems

 3. install dependencies `click`, run `python bench.py --help` to see all arguments

 4. run `python bench.py | tee result_3_3.txt` and `python bench.py | tee result_3_4.txt` in v3.3 and v3.4 respectively

 5. or run `python bench.py --use-cudagraph | tee result_3_3.txt` and `python bench.py --use-cudagraph | tee result_3_4.txt` in v3.3 and v3.4 respectively

 6. join the result with `python join.py result_3_3.py result_3_4.py > data.txt`, data.txt is the default filename used by visualization script

Note: redirected files on Windows contains `Byte Order Mark` which gnuplot can't process correctly, so you'll have to manually copy and paste it into another file with some editor like vscode.

## visualization

To reproduce visualization

 1. install gnuplot

 2. run `./visualize.ps1` on windows

Note: visualization script only support M/N/K size in 128:4097:128 range.

## data

- "./export/data-cudagraph-e2e.txt": end to end time with cudagraph
- "./export/data-no-cudagraph-e2e.txt": end to end time without cudagraph
- "./export/data-cudagraph-kernel.txt": kernel time with cudagraph
- "./export/data-no-cudagraph-kernel.txt": kernel time without cudagraph
- "./export/data-e2e.txt": end to end time w/o cudagraph
- "./export/data-kernel.txt": kernel time w/o cudagraph
- "./export/data-common-shapes-cudagraph-e2e.txt": end to end time with cudagraph for common shapes
- "./export/data-common-shapes-cudagraph-kernel.txt": kernel time with cudagraph for common shapes
- "./export/data-common-shapes-no-cudagraph-e2e.txt": end to end time without cudagraph for common shapes
- "./export/data-common-shapes-no-cudagraph-kernel.txt": kernel time without cudagraph for common shapes
