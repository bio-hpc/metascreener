#!/usr/bin/env bash

#____________________________________________________________________
#	Generate Grid for LF
#__________________________________________________________________

if [[ $grid_bin != "N/A" ]];then
  cp ${CWD}${grid_bin} ${out_grid}_grid.bin
fi

if [ ! -f ${out_grid}"_grid.bin" ];then

	echo "Generate Grid ($x $y $z) wait a few minutes "
	debugC "generateGridLF: grid-center=${x},${y},${z} >${out_grid}.par"
	debugC "generateGridLF: grid-size=${gridSizeX},${gridSizeY},${gridSizeZ} >>${out_grid}.par"
	echo "grid-center=${x},${y},${z}" >${out_grid}.par
	echo "grid-size=${gridSizeX},${gridSizeY},${gridSizeZ}" >>${out_grid}.par

	debugC "generateGridLF: ${path_external_sw}leadFinder/leadfinder \
	--grid-only \
	--protein=${CWD}${target} \
	--save-grid=${out_grid}grid.bin \
	-np ${cores} \
	--parameters=${out_grid}.par >> ${out_grid}_G.ucm"
	
	${path_external_sw}leadFinder/leadfinder\
	--grid-only \
	--protein=${CWD}${target} \
	--save-grid=${out_grid}_grid.bin \
	-np ${cores} \
	--parameters=${out_grid}.par >> ${out_grid}_G.ucm 2>/dev/null
	rm ${out_grid}".par"
fi

