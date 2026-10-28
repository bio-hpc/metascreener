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
elif [ "$query_is_tar" = "1" ];then
	ext_re=$(printf '%s' "$ext_query" | sed 's/\./\\./g')
	grep -E "${ext_re}$" "$ms_tar_list" | LC_ALL=C sort > "${folder_experiment}ligands.list"
	rm -f "$ms_tar_list"
	dups=$(awk -F/ '{print $NF}' "${folder_experiment}ligands.list" | LC_ALL=C sort | uniq -d)
	if [ -n "$dups" ];then
		echo "ERROR: the tar library contains different ligand files with the same name:" >&2
		echo "$dups" >&2
		exit 1
	fi
	numFicheros=$(grep -c . "${folder_experiment}ligands.list" || true)
	if [ -z "$numFicheros" ] || [ "$numFicheros" = "0" ];then
		echo "ERROR: no ${ext_query} files found in ${query_tar}" >&2
		exit 1
	fi
	tar_query_rel="${folder_experiment}${name_query}"
	tar_query_rel="${tar_query_rel#"${CWD}"}"
	case "$tar_query_rel" in
		/*)
			echo "ERROR: experiment directory ${folder_experiment} is outside ${CWD}; cannot stage the tar library." >&2
			exit 1
			;;
	esac
	echo "Tar library: ${numFicheros} ${ext_query} ligands in ${query_tar}"
else
  numFicheros=`find ${CWD}${query}/ -maxdepth 1 -name "*${ext_query}" |wc -l`
fi

out_prefix=${option}_${software}_${name_target}_${name_query}_${x}_${y}_${z}
out_grid=${folder_grid}${out_prefix}
out_dock=${folder_grid}${out_prefix}

source ${path_cluster_nodes}generate_grid.sh
pritnDebug
send_jobs







