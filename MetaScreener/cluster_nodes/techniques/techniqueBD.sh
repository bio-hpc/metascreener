#!/bin/bash
TAG="tecniqueBD"
findCords
final=`expr $fin - 1`
for num_execution in `seq $ini $final`;
do
    if  [ $((${num_execution}%${bd_exhaustiveness})) == 0 ];then
	    extractDataLine "${coords[num_execution]}"
	    executeTecnique "bash ${path_cluster_nodes}run_software.sh  -c $CWD -q $query -nq $name_query -na ${numAminoacdo} -ch ${chain} -ej ${num_execution} "	    
	 fi
done