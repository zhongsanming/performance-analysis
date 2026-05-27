#!/usr/bin/env gnuplot

# ============================================================
# Usage: gnuplot -c plot_latency.gp <major> <fix1> <fix2> [datafile]
#   major : "M", "K", or "N"   (the column to use as X axis)
#   fix1  : fixed value for the first other dimension
#   fix2  : fixed value for the second other dimension
#   datafile : optional, defaults to "data.txt"
#
# Example: gnuplot -c plot_latency.gp M 1024 2048 data.txt
#   → plots latency vs M for K=1024 and N=2048
# ============================================================

# --- argument handling -------------------------------------------------
if (ARGC < 3) {
    print "Error: insufficient arguments."
    print "Usage: gnuplot -c plot_latency.gp <major> <fix1> <fix2> [datafile]"
    exit 1
}

major = ARG1           # "M", "K", or "N"
fix1  = real(ARG2)     # first fixed value
fix2  = real(ARG3)     # second fixed value
datafile = (ARGC >= 4) ? ARG4 : "data.txt"

# --- define implementation names and column numbers -------------------
impl_names = "V33 V34 DEV-TMA HOST-TMA"   # adjust as needed
impl_cols  = "4 5 6 7"
# impl_names = "V34 DEV-TMA HOST-TMA"   # adjust as needed
# impl_cols  = "5 6 7"

# --- determine X column and filter condition --------------------------
if (major eq "M") {
    xcol = 1
    xlabel = "M"
    col1 = "K"
    col2 = "N"
    # fixed columns: K (col2) and N (col3)
    cond = sprintf("(column(2)==%g && column(3)==%g)", fix1, fix2)
} else if (major eq "K") {
    xcol = 2
    xlabel = "K"
    col1 = "M"
    col2 = "N"
    # fixed columns: M (col1) and N (col3)
    cond = sprintf("(column(1)==%g && column(3)==%g)", fix1, fix2)
} else if (major eq "N") {
    xcol = 3
    xlabel = "N"
    col1 = "M"
    col2 = "K"
    # fixed columns: M (col1) and K (col2)
    cond = sprintf("(column(1)==%g && column(2)==%g)", fix1, fix2)
} else {
    print "Error: major must be M, K, or N"
    exit 1
}

# --- plotting settings ------------------------------------------------
set terminal pngcairo size 1200,800 enhanced
set output sprintf("./visualization/latency_vs_%s_%s%g_%s%g.png", major, col1, fix1, col2, fix2)

set title sprintf("Latency vs %s  (%s=%g, %s=%g)", \
                  xlabel, col1, fix1, col2, fix2) font ",24"
set xlabel xlabel font ",12"
set ylabel "Latency (ms)" font ",12"
set grid
set key outside right top

# Use smooth unique to sort by the X column automatically
# (the data set contains exactly one point per X value after filtering)
set style data linespoints
set style line 1 lc rgb "#1f77b4" pt 7 ps 1.5 lw 2   # blue
set style line 2 lc rgb "#ff7f0e" pt 9 ps 1.5 lw 2   # orange
set style line 3 lc rgb "#2ca02c" pt 5 ps 1.5 lw 2   # green
set style line 4 lc rgb "#d62728" pt 11 ps 1.5 lw 2  # red

# --- plot the four latency columns ------------------------------------
plot for [i=1:words(impl_names)] datafile \
     using (column(xcol)):(column(int(word(impl_cols,i)))) if @cond \
     smooth unique \
     with linespoints ls i title word(impl_names,i)
