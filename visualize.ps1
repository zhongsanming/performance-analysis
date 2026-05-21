# heatmap
foreach ($dim in ("M", "N", "K")) {
    gnuplot.exe -c .\heatmap.gp $dim $args
}

# trend
foreach ($dim in ("K", "M", "N")) {
    for ($size = 128; $size -le 4096; $size += 128) {
        gnuplot.exe -c .\trend.gp $dim $size $size $args
    }
}

# slice
foreach ($dim in ("K", "M", "N")) {
    for ($size = 128; $size -le 4096; $size += 128) {
        gnuplot.exe -c .\slice.gp $dim $size $args
    }
}
