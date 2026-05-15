# ==========================================================
# Multiplot matrix: 4 implementations × 6 common values
# Heatmap, coloured by latency (interpolated)
# Data columns: M  K  N  NOTMA  DEVICETMA  HOSTTMA (no header)
# ==========================================================

# Configuration
datafile = "data.txt"

# Which dimension to fix? Choose "M", "N", or "K"
if (ARGC >= 1) fixed_dim = ARG1 else fixed_dim = "K"
if (ARGC >= 2) fixed_val = int(ARG2) else fixed_val = 2048

# ------------------- Determine axes and filter based on fixed_dim -------------------
if (fixed_dim eq "M") {
    xl = "K"
    yl = "N"
    xcol = 2
    ycol = 3
    fixed_col = 1
    title_prefix = "M ="
} else if (fixed_dim eq "N") {
    xl = "M"
    yl = "K"
    xcol = 1
    ycol = 2
    fixed_col = 3
    title_prefix = "N ="
} else if (fixed_dim eq "K") {
    xl = "M"
    yl = "N"
    xcol = 1
    ycol = 3
    fixed_col = 2
    title_prefix = "K ="
} else {
    print "Error: fixed_dim must be M, N, or K"
    exit
}

# max function for calculate color range
max(a, b) = (a > b) ? a : b

set palette viridis
set cblabel "Latency (ms)"     # or "ms"
set cbrange [0:1]
set view map
set pm3d at b
set dgrid3d 32 gauss 4.0   # interpolates sparse data
set pm3d interpolate 2,2
unset key

set xtics 256
set ytics 256
set xrange [0:4096+128]
set yrange [0:4096+128]
set grid
set size ratio -1

set terminal pngcairo size 2500,1200 enhanced
set output sprintf("./visualization/heatmap_slice_%s_%d.png", fixed_dim, fixed_val)

# Multiplot layout: rows = num_impl, columns = num_fixed
# set lmargin at screen 0.02   # reserve space for ylabel on left
# set bmargin at screen 0.02   # reserve space for xlabel at bottom
# set multiplot layout rows,num_fixed margins 0.04,0.96,0.04,0.96 spacing 0.05 title sprintf("Latency heatmaps – fixing %s", fixed_dim) font ",32"

splot datafile using xcol:ycol:(column(fixed_col) == fixed_val ? (column(7) <= column(6) && column(7) <= column(5) && column(7) <= column(4) ? 1.0 : 0.0) : NaN) with pm3d notitle
