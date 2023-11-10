#!/bin/bash
# Author: Jorge de la Pe������a Garc������a
# Author: Carlos Mart������nez Cort������s
#	Email:  cmartinez@ucam.edu
#	Description: It takes care of calling the corresponding Software scripts
#_________________________________________________________________________________________________________________________________________________________________________

TAG=""
DELIMITER="\\n"

execute()
{
	debugY "$TAG: $1"
	eval "$1"
	error=$?
}
#
#	Standard output to json
#
function standar_out_file()
{
	out_put=${name_query}${DELIMITER}
	out_put=${out_put}${query}${DELIMITER}
	out_put=${out_put}${target}${DELIMITER}
	out_put=${out_put}${file_result}${DELIMITER}
	out_put=${out_put}${coords}${DELIMITER}
	out_put=${out_put}${number_execution}${DELIMITER}
	out_put=${out_put}${num_amino_acid}${DELIMITER}
	out_put=${out_put}${chain}${DELIMITER}
	out_put=${out_put}${global_score}${DELIMITER}
	out_put=${out_put}${gridSizeX}","${gridSizeY}","${gridSizeZ}${DELIMITER}
	out_put=${out_put}${option}${DELIMITER}
	out_put=${out_put}${software}${DELIMITER}
	out_put=${out_put}${global_score_md}${DELIMITER}
	out_put=${out_put}${global_score_qu}${DELIMITER}
	out_put=${out_put}${DELIMITER}
	out_put=${out_put}${graph_global_color}${DELIMITER}
	out_put=${out_put}${graph_global_field}${DELIMITER}
	out_put=${out_put}${graph_global_score}${DELIMITER}
	out_put=${out_put}${graph_atoms_color}${DELIMITER}
	out_put=${out_put}${graph_atoms_field}${DELIMITER}
	out_put=${out_put}${graph_atoms_type}${DELIMITER}
	out_put=${out_put}${graph_atoms_score}${DELIMITER}
	if [[ ${software} == "GN" ]];then
		out_put=${out_put}${CNNscores}
	fi

	python ${path_cluster_nodes}standar_out_put.py "${out_energies}${1}.json" "$out_put"
}

#
#	Main
#
if [ -z ${check} ];then
	source ${CWD}MetaScreener/login_node/read_all_conf.sh
fi
execute "re='^[0-1]+([.][0-9]+)?$'"

if [ "$x" != "0" ] || [  "$y" != "0" ] || [ "$z" != "0" ];then
    if [ "$number_execution" == "-1" ];then
        aux_query=`basename $query`
        aux_query="${aux_query%.*}"
        execute "out_prefix=${option}_${software}_${name_target}_${aux_query}_${x}_${y}_${z}"
    else
        execute "out_prefix=${number_execution}_${option}_${software}_${name_target}_${name_query}_${x}_${y}_${z}"
    fi

else
   aux_query=`basename $query`
   aux_query="${aux_query%.*}"

   if [ "${software}" == "LS" ];then
   		aux_query=${aux_query}_${ini}_${fin}   	   	
   fi
   execute "out_prefix=${option}_${software}_${name_target}_${aux_query}"
fi

global_score_md=""
global_score_qu=""
opt_aux=`cat ${folder_templates_jobs}parameter_aux.txt`

if [ "${option}" == "VS" ];then
    out_grid=${folder_grid}${option}_${software}_${name_target}_${name_query}_${x}_${y}_${z}
else
    out_grid=${folder_grid}${out_prefix}
fi

out_aux=${folder_out_ucm}${out_prefix}
out_molec=${folder_molec}${out_prefix}
out_energies=${folder_energies}${out_prefix}
execute "source ${path_cluster_nodes}execute_scripts/script${software}.sh"
execute "execute_script"

