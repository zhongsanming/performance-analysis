# ==========================================================
# Multiplot matrix: 4 implementations × 6 common values
# Heatmap, coloured by latency (interpolated)
# Data columns: M  K  N  NOTMA  DEVICETMA  HOSTTMA (no header)
# ==========================================================

# Which dimension to fix? Choose "M", "N", or "K"
fixed_dim = (ARGC >= 1) ? ARG1 : "K"
datafile = (ARGC >= 2) ? ARG2 : "data.txt"

fixed_list = "128 256 512 1024 2048 4096"

# unjoined data
# impl_names = "V34 DEV-TMA HOST-TMA"
# impl_cols = "5 6 7"               # column numbers for each implementation
impl_names = "V33 V34 DEV-TMA HOST-TMA"
impl_cols = "4 5 6 7"               # column numbers for each implementation

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
# set cblabel "Latency (ms)"     # or "ms"
set view map
set pm3d at b
set dgrid3d 32 gauss 4.0   # interpolates sparse data
set pm3d interpolate 2,2
unset key

set xtics 1024
set ytics 1024
set xrange [0:4096+128]
set yrange [0:4096+128]
set grid
set size ratio -1

set terminal pngcairo size 2500,1200 enhanced
set output sprintf("./visualization/heatmap_matrix_%s.png", fixed_dim)

# Count number of fixed values and implementations
num_fixed = words(fixed_list)
num_impl = words(impl_names)

# Multiplot layout: rows = num_impl, columns = num_fixed
# set tmargin at screen 0.94   # reserve space for title on top
# set lmargin at screen 0.02   # reserve space for ylabel on left
# set bmargin at screen 0.02   # reserve space for xlabel at bottom
set multiplot layout num_impl,num_fixed margins 0.04,0.96,0.06,0.94 spacing 0.05 title sprintf("Latency heatmaps – fixing %s", fixed_dim) font ",24"
# set multiplot layout num_impl,num_fixed title sprintf("Latency heatmaps – fixing %s", fixed_dim) font ",24"

# Loop over implementations (rows)
do for [i=1:num_impl] {
    impl_name = word(impl_names, i)
    col = int(word(impl_cols, i))
    # Loop over fixed values (columns)
    do for [j=1:num_fixed] {
        fixed_val = int(word(fixed_list, j))

        # Set title only for first row
        if (i == 1) {
            set title sprintf("%s %g", title_prefix, fixed_val)
        } else {
            set title ""
        }

        # Set ylabel only for first column
        if (j == 1) {
            set ylabel yl
        } else {
            set ylabel ""
        }

        # Set xlabel only for last row
        if (i == num_impl) {
            set xlabel xl
        } else {
            set xlabel ""
        }

        # use same color range for different impl
        if (i != 1) {
            cmax = 0
            do for [k=2:num_impl] {
                kcol = int(word(impl_cols, k))
                stats datafile using (column(fixed_col)==fixed_val?column(kcol):NaN) nooutput
                cmax = max(STATS_max, cmax)
            }
            set cbrange [0:cmax]
        }

        # Plot heatmap with ternary filtering
        splot datafile using xcol:ycol:(column(fixed_col) == fixed_val ? column(col) : NaN) with pm3d notitle
    }
}
unset multiplot
