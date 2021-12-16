#!/bin/bash
#_________________________________________________________________________________________
# Generates grid if needed
#_________________________________________________________________________________________
if [ ${grid} == "Y" ];then
	source  ${path_cluster_nodes}grids/generateGrid${software}.sh
fi 






















