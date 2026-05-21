# Performance Analysis

## benchmark

To reproduce benchmark

 1. install FlagTree v3.3 and v3.4 via venv

 2. install extract_mm branch of https://github.com/zhongsanming/FlagGems

 3. install dependencies `click`

 3. run `python bench.py | tee result_3_3.txt` and `python bench.py | tee result_3_4.txt` in v3.3 and v3.4 respectively

 4. join the result with `python join.py result_3_3.py result_3_4.py > data.txt`, data.txt is the default filename used by visualization script

## visualization

To reproduce visualization

 1. install gnuplot

 2. run `./visualize.ps1 data.txt` on windows
