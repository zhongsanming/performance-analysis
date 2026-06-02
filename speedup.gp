# ==========================================================
# Multiplot matrix: 4 implementations × 6 common values
# Heatmap, coloured by latency (interpolated)
# Data columns: M  K  N  NOTMA  DEVICETMA  HOSTTMA (no header)
# ==========================================================

# Which dimension to fix? Choose "M", "N", or "K"
fixed_dim = (ARGC >= 1) ? ARG1 : "K"
fixed_val = (ARGC >= 2) ? int(ARG2) : 2048
datafile = (ARGC >= 3) ? ARG3 : "data.txt"
out_dir = (ARGC >= 4) ? ARG4 : "visualization"

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

set palette defined (\
  -1.0 "#00008B", \
  -0.9 "#00008B", \
  -0.9 "#161898", \
  -0.8 "#161898", \
  -0.8 "#2C31A5", \
  -0.7 "#2C31A5", \
  -0.7 "#4349B2", \
  -0.6 "#4349B2", \
  -0.6 "#5962BF", \
  -0.5 "#5962BF", \
  -0.5 "#6F7ACC", \
  -0.4 "#6F7ACC", \
  -0.4 "#8593D8", \
  -0.3 "#8593D8", \
  -0.3 "#9CABE5", \
  -0.2 "#9CABE5", \
  -0.2 "#B2C4F2", \
  -0.1 "#B2C4F2", \
  -0.1 "#C8DCFF", \
   0   "#C8DCFF", \
   0   "#FFC8C8", \
   0.1 "#FFC8C8", \
   0.1 "#F2B2B2", \
   0.2 "#F2B2B2", \
   0.2 "#E59C9C", \
   0.3 "#E59C9C", \
   0.3 "#D88585", \
   0.4 "#D88585", \
   0.4 "#CB6F6F", \
   0.5 "#CB6F6F", \
   0.5 "#BF5959", \
   0.6 "#BF5959", \
   0.6 "#B24343", \
   0.7 "#B24343", \
   0.7 "#A52C2C", \
   0.8 "#A52C2C", \
   0.8 "#981616", \
   0.9 "#981616", \
   0.9 "#8B0000", \
   1.0 "#8B0000"  \
)

# set palette viridis

set cblabel "Speedup Ratio"     # or "ms"
set cbrange [-1:1]
set pm3d map
set contour base
set cntrparam levels discrete 0
set view map
set pm3d at b

set dgrid3d 32 gauss 4.0   # interpolates sparse data
set pm3d interpolate 2,2

unset key

set xtics 256
set ytics 256
set xrange [0:4096+128]
set yrange [0:4096+128]
set xlabel xl
set ylabel yl
set grid
set size ratio -1

set terminal pngcairo size 2500,1200 enhanced
set output sprintf("./%s/heatmap_host_tma_speedup_%s_%d.png", out_dir, fixed_dim, fixed_val)

# Multiplot layout: rows = num_impl, columns = num_fixed
# set lmargin at screen 0.02   # reserve space for ylabel on left
# set bmargin at screen 0.02   # reserve space for xlabel at bottom
# set multiplot layout rows,num_fixed margins 0.04,0.96,0.04,0.96 spacing 0.05 title sprintf("Latency heatmaps – fixing %s", fixed_dim) font ",32"

set title sprintf("HostTMA vs NoTMA speed up with %s = %d", fixed_dim, fixed_val)

splot datafile using xcol:ycol:(column(5) / column(7) - 1.0) if (column(fixed_col) == fixed_val) with pm3d notitle
