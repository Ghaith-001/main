# Auto-generated Vivado HLS TCL script — 1N4007
open_project 1N4007_prj
set_top myproject
add_files firmware/myproject.cpp
add_files firmware/myproject.h
add_files firmware/parameters.h
add_files -tb tb_data/tb_input_features.dat
add_files -tb tb_data/tb_output_predictions.dat
open_solution solution1
set_part {xc7a35tcpg236-1}
create_clock -period 10 -name default
csynth_design
export_design -format ip_catalog
exit
