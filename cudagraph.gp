#!/usr/bin/env gnuplot

# ============================================================
# Usage: gnuplot -c cudagraph.gp [datafile]
#   datafile : optional, defaults to "data.txt"
#
# Example: gnuplot -c cudagraph.gp data.txt
#   → plots cudagraph improvement vs Size
# ============================================================

# --- argument handling -------------------------------------------------
datafile = (ARGC >= 1) ? ARG1 : "data.txt"
out_dir = (ARGC >= 2) ? ARG2 : "visualization"

# --- define implementation names and column numbers -------------------
impl_names = "V33 V34 DEV-TMA HOST-TMA"   # adjust as needed
impl_cols_no_cg  = "4 5 6 7"
impl_cols_cg  = "8 9 10 11"

# --- plotting settings ------------------------------------------------
set terminal pngcairo size 1200,800 enhanced
set output sprintf("./%s/cudagraph-improve_vs_size.png", out_dir)

set title sprintf("CudaGraph Latency Ratio vs Size") font ",24"
set xlabel "Size" font ",12"
set ylabel "Latency Ratio (CudaGraph / NoCudaGraph)" font ",12"
set yrange [0:]
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
     using (column(2)):((column(int(word(impl_cols_cg,i)))) / (column(int(word(impl_cols_no_cg,i))))) if (column(1) == column(2) && column(1) == column(3)) \
     smooth unique \
     with linespoints ls i title word(impl_names,i)
