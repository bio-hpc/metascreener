#!/bin/bash

executeTecnique()
{
	params=" -d ${folder_experiment} -s $software -o $option -t $target \
	-x $x -y $y -z $z -nt $name_target  -ch ${chain} \
	-fx $flex -in $ini -fn $fin -nc ${numPoses} -fl ${flexFile} \
	-de ${debug} -co ${cores} -gpu ${GPU} -mm ${mem} -tr ${torsion} \
	-sc ${scoreCorte} -grid ${grid} -EXP ${ext_target} -EXL ${ext_query} \
	-RE ${resName} -NA ${num_amino_acid} -GX ${gridSizeX} -GY ${gridSizeY} \
	-GZ ${gridSizeZ} -nn ${nodos} -nj ${name_job} -bda ${bd_atom_default}"

	if [ "$debug" == "-1" ];then
		if [ "${lanzTimeOut}" == "Y" ];then
			eval "timeout $time_experiment $1 $params"
		elif [ "${lanzTimeOut}" == "N" ];then
			eval $1 $params
		else
			"Error: The lanzTimeOut parameter is not defined in the MetaScreener/node_login/templateParams/template${prgrama}.sh template."
			exit
		fi

	else
		debugC "$TAG timeout $time_experiment $1 $params"
		if [ "${lanzTimeOut}" == "Y" ];then
				eval "timeout $time_experiment $1 $params"
		elif [ "${lanzTimeOut}" == "N" ];then
			eval $1 $params
		else
			"Error: The lanzTimeOut parameter is not defined in the MetaScreener/node_login/templateParams/template${prgrama}.sh template."
			exit
		fi
	fi

}

findCords()
{
	coordsAux=`python ${path_extra_metascreener}used_by_metascreener/standar_file_coords.py ${CWD}${target} |grep -v "##" |grep ${bd_atom_default}`
	coords=($coordsAux)
}

extractDataLine()
{
	line=$1
    x=`echo $line | cut -d\: -f1`
	y=`echo $line | cut -d\: -f2`
	z=`echo $line | cut -d\: -f3`
	resName=`echo $line | cut -d\: -f6`
	num_amino_acid=`echo $line | cut -d\: -f7`
	chain=`echo $line | cut -d\: -f8`
	
	if [ -z "$chain" ];then
		chain="N/A"
	fi 
	debugC "baseTechnique.sh: x: $x y: $y z: $z num_amino_acid: $num_amino_acid chain $chain"
}
get_vsr_coords()
{
    coords=`cat ${CWD}${query}/coords.txt |grep $name_target`

    x=`echo $coords | cut -d\: -f2`
	  y=`echo $coords | cut -d\: -f3`
	  z=`echo $coords | cut -d\: -f4`
}
#
#		Main
#_______________________________________________________________________________________________________
source ${CWD}MetaScreener/login_node/read_all_conf.sh

debugC "_________________________________________Technique base ________________________________________"
debugC ""
debugC "baseTechnique.sh: job ${option}-${ini}-${fin}" 
source ${2}MetaScreener/cluster_nodes/techniques/technique${option}.sh
