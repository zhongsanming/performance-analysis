foreach ($mode in ("e2e", "kernel")) {
    foreach ($cg in ("no-cudagraph", "cudagraph")) {
        mkdir ./visualization-$cg-$mode

        # heatmap
        foreach ($dim in ("M", "N", "K")) {
            gnuplot.exe -c .\heatmap.gp $dim ./export/data-$cg-$mode.txt ./visualization-$cg-$mode
        }

        # trend
        foreach ($dim in ("K", "M", "N")) {
            for ($size = 128; $size -le 4096; $size += 128) {
                gnuplot.exe -c .\trend.gp $dim $size $size ./export/data-$cg-$mode.txt ./visualization-$cg-$mode
            }
        }

        # slice
        foreach ($dim in ("K", "M", "N")) {
            for ($size = 128; $size -le 4096; $size += 128) {
                gnuplot.exe -c .\slice.gp $dim $size ./export/data-$cg-$mode.txt ./visualization-$cg-$mode
            }
        }

        # cuda graph compare
        gnuplot.exe -c .\cudagraph.gp ./export/data-$mode.txt ./visualization-$cg-$mode
    }
}
