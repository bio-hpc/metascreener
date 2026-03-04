#!/usr/bin/env bash

#____________________________________________________________________
#	Generate Grid for LF
#__________________________________________________________________

# Persistent grid file associated to the target
persistent_grid="${CWD}${target}.grid.bin"

# 1) If a grid file is explicitly provided, use it
if [[ "$grid_bin" != "N/A" ]]; then
  cp ${CWD}${grid_bin} ${out_grid}_grid.bin
fi

# 2) Otherwise, if a persistent grid for this target exists, reuse it
elif [ -f "${persistent_grid}" ]; then
	cp "${persistent_grid}" "${out_grid}_grid.bin"
fi

# 3) If we still don't have a grid for this run, generate it and persist it
if [ ! -f "${out_grid}_grid.bin" ]; then

	echo "Generate Grid ($x $y $z) wait a few minutes "
	debugC "generateGridLF: grid-center=${x},${y},${z} >${out_grid}.par"
	debugC "generateGridLF: grid-size=${gridSizeX},${gridSizeY},${gridSizeZ} >>${out_grid}.par"
	echo "grid-center=${x},${y},${z}" >"${out_grid}.par"
	echo "grid-size=${gridSizeX},${gridSizeY},${gridSizeZ}" >>"${out_grid}.par"

	debugC "generateGridLF: ${path_external_sw}leadFinder/leadfinder \
	--grid-only \
	--protein=${CWD}${target} \
	--save-grid=${out_grid}_grid.bin \
	-np ${cores} \
	--parameters=${out_grid}.par >> ${out_grid}_G.ucm"
	
	${path_external_sw}leadFinder/leadfinder \
		--grid-only \
		--protein="${CWD}${target}" \
		--save-grid="${out_grid}_grid.bin" \
		-np "${cores}" \
		--parameters="${out_grid}.par" >> "${out_grid}_G.ucm" 2>/dev/null
	
	# Save a persistent copy associated to this target for future runs
	cp "${out_grid}_grid.bin" "${persistent_grid}"
	
	rm ${out_grid}".par"
fi

