#!/usr/bin/env bash
#lanzTechnique:VS - Virtual screening
#______________________________________________________________________________________________________________________________________________#
#                                                                                                                                                                                                                                                                                          #
# VS 1vs1                                                                                                                                      #
#______________________________________________________________________________________________________________________________________________#
pritnDebug()
{
        debugB "SLTechniqueVS.sh: find ${CWD}${query}  -name \"*${ext_query}\" |wc -l"
        debugB "SLTechniqueVS.sh: salida=$directorio$option"-"$software"-"${name_target}-$name_query-$x-$y-$z"
        debugB "SLTechniqueVS.sh: ${pathSD}generate_grid.sh -s $software -x $x -y $y -z $z -d $salida -p $target -c $CWD -o $option"
        debugB "SLTechniqueVS.sh: funcionEnviarJobs"
}
#________________________________________________________________________________________________________________________________
#
#       VS
#_________________________________________________________________________________________________________________________________
source ${path_login_node}lanza_job.sh
if [ ${software} == "LS" ];then
	numFicheros=`${path_external_sw}ligandScout/idbinfo -d ${query} 2> /dev/null |grep Database |awk '{print $3}'`
else
  numFicheros=`find ${CWD}${query}/ -maxdepth 1 -name "*${ext_query}" |wc -l`
fi

out_prefix=${option}_${software}_${name_target}_${name_query}_${x}_${y}_${z}
out_grid=${folder_grid}${out_prefix}
out_dock=${folder_grid}${out_prefix}

source ${path_cluster_nodes}generate_grid.sh
pritnDebug
send_jobs







