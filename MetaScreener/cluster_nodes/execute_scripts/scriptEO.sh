#!/usr/bin/env bash
execute_script()
{	
    
	unset DISPLAY
	TAG=`echo $(basename $BASH_SOURCE)`
	lib=`echo $(basename $query)`
	if [ ${option} == "VS" ];then
	     path=$PWD
	     cd ${path_external_sw}openeye/eon/
	     prefix=$( echo ${out_molec} | sed -e 's/\/.*\///g' )
	     execute "./eon -dbase ${CWD}${target} -query ${CWD}${query} -prefix ${prefix} &> ${out_aux}.ucm"
	     mkdir ${folder_experiment}/energies/${prefix}
	     mv ${prefix}* ${folder_experiment}/energies/${prefix}
	     cd $path
	else
		echo "EO only works with VS technique"
		exit
	fi
}


