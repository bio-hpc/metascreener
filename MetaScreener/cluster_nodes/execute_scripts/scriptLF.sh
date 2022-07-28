#!/usr/bin/env bash

graph_global_field="Van_Der_Wals":"E(sol)":"E(H-bonds)":"E(elect)":"E(internal)":"E(tors)":"E(Metal)":"E(dihedral)":"E(penalty)":"dG_of_binding,_kcal/mol"
graph_global_color="b":"g":"r":"c":"m":"#eeefaa":"y":"#aaefff":"#bbefaa":"k"
graph_atoms_field="E(VDW)":"E(sol)":"E(H-bonds)":"E(elect)":"E(internal)":"E(metal)":"E(total)"
graph_atoms_color="b":"g":"r":"c":"m":"#eeefaa":"#bbefaa":"k"


execute_script()
{
	TAG=`echo $(basename $BASH_SOURCE)`

	OLDIFS=$IFS
	IFS='-' read -r -a array <<< "$opt_aux"
	refined_energy=""
	for element in "${array[@]}"
	do
		aux=`echo $element | cut -f1 -d' ' | tr a-z A-Z`
		param=`echo $element | cut -f2 -d' ' | tr a-z A-Z`
		case "$aux" in
			REFINED_ENERGY)	refined_energy=$param;;
		esac
	done
	IFS=$OLDIFS;
	if [ $refined_energy != "LF" ] && [ $refined_energy != "GR" ];then
		  echo "ERROR: bad -refined_energy $refined_energy"
		  exit
	fi

	opt_aux=`echo "${opt_aux/-refined_energy $refined_energy/}"`
	case $option in
		VS)
               query_aux=${query//'/'/'_'}
               out_aux=${folder_out_ucm}${option}_${software}_${name_target}_${query_aux}_${x}_${y}_${z}
               coords=$x":"$y":"$z
			execute "${path_external_sw}leadFinder/leadfinder --load-grid=${out_grid}_grid.bin \
			--protein=${CWD}${target} --ligand=${CWD}${query} --output-tabular=${out_energies}.log \
			--output-poses=${out_molec}.mol2 --text-report=${out_energies}.eng --max-poses=${numPoses}   $opt_aux &>  $out_aux.ucm "
		;;
		BD  )
			execute "source ${path_cluster_nodes}generate_grid.sh"
			execute "${path_external_sw}leadFinder/leadfinder --load-grid=${out_grid}_grid.bin \
			--protein=${CWD}${target} --ligand=${CWD}${query} --output-tabular=${out_energies}.log \
			--output-poses=${out_molec}.mol2 --text-report=${out_energies}.eng --max-poses=${numPoses}   $opt_aux &>  $out_aux.ucm "
            	execute "coords=\"`${path_extra_metascreener}used_by_metascreener/get_center_ligand.py ${out_molec}.mol2`\""
			execute "rm ${out_grid}_grid.bin"
		;;
	esac
	if [ ${numPoses} -gt 1 ];then
	  babel ${out_molec}.mol2 ${out_molec}_.mol2 -m 2> /dev/null
	  rm ${out_molec}.mol2
       for i in `seq 1 $numPoses`;do
	    create_out "${i}"
	  done
     else
       create_out
     fi
}

function create_out()
{
    file_result=${out_molec}.mol2
    execute "global_score=\"`cat ${out_energies}.log |grep '^/' | grep -P "mol2\t0\t$1\t" |awk '{print \$4}'`\""
    if [ ${numPoses} -gt 1 ];then
      cat ${out_energies}.eng | sed -n "/Detailed energy of pose     $1 :/,/dG of binding/p" > ${out_energies}_$1.eng
    fi
    graph_global_score $1
    graph_atom_score $1 2> /dev/null # here
    if [ ${numPoses} -gt 1 ];then
      if [ -s ${out_energies}_$1.eng ];then
        execute "standar_out_file _${1}"
      else
        rm ${out_energies}_$1.eng
      fi
    else
      execute "standar_out_file"
    fi
}
function  graph_global_score
{
    n_lines=(`cat ${out_energies}_$1.eng |grep -A 13 "Total Energy components :" |wc -l`)
    if [ $n_lines == 14 ];then
      g_ener=(`cat ${out_energies}_$1.eng |grep -A 13 "Total Energy components :" |tail -13`)
      graph_global_score=${g_ener[1]}:${g_ener[5]}:${g_ener[7]}:${g_ener[9]}:${g_ener[11]}:${g_ener[19]}:${g_ener[3]}:${g_ener[21]}:${g_ener[25]}:${g_ener[30]}
    else
      g_ener=(`cat ${out_energies}_$1.eng |grep -A 11 "Total Energy components :" |tail -11`)
      graph_global_score=${g_ener[1]}:${g_ener[5]}:${g_ener[7]}:${g_ener[9]}:${g_ener[11]}:${g_ener[13]}:${g_ener[3]}:${g_ener[15]}:${g_ener[19]}:${g_ener[24]}
    fi
}
function graph_atom_score
{
    start_ener=`grep -n Name ${out_energies}_$1.eng |head -1 | awk -F: '{print $1}'`
    start_ener=`expr $start_ener + 1`
    end_ener=`grep -n Total  ${out_energies}_$1.eng| head -1 |awk -F: '{print $1}'`
    end_ener=`expr $end_ener - 2`
    graph_atoms_score=`sed -n "$start_ener,$end_ener p" ${out_energies}_$1.eng |awk '{print $5":"$7":"$8":"$9":"$10":"$11 "\\\n"}'`
    graph_atoms_score=`echo $graph_atoms_score |sed 's/\ //g'`
    graph_atoms_type=`sed -n "$start_ener,$end_ener p"  ${out_energies}_$1.eng | awk '{print $1"_"$2":"}'`
    graph_atoms_type=`echo $graph_atoms_type |sed 's/\ //g'`
}
