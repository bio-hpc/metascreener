#!/usr/bin/env bash
#_______________________________________________________________________________________________________________________
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Docking with Vina
# ______________________________________________________________________________________________________________________

vGauss1=-0.035579
vGauss2=-0.005156
vRepulsion=0.840245
vHydrophobic=-0.035069
vHydrogen=-0.587439
vRot=0.05846

graph_global_color="b":"g":"r":"c":"m":"y":"k"
graph_global_field="Gauss1":"Gauss2":"Repulsion":"Hydrophobic":"Hydrogen_Bonds":"Rotational":'Total_Affinity'
graph_atoms_color="b":"g":"#E92424":"c":"m"
graph_atoms_field="Gauss1":"Gauss2":"Repulsion":"hydrophobic":"Hydrogen_Bonds"
read_params()
{

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

	if [ $refined_energy != "AD" ] && [ $refined_energy != "GR" ] && [ $refined_energy != "QU" ]  && [ $refined_energy != "ALL" ];then
		echo "ERROR: bad -refined_energy $refined_energy"
		exit
	fi
	
	opt_aux=`echo "${opt_aux/-refined_energy $refined_energy/}"`
	

}
execute_script()
{
	read_params 

	TAG=`echo $(basename $BASH_SOURCE)`
	
	checkAminChainFlex
	debugY "$TAG option: ${option} flexibilidad: ${flexFile} chain: ${chain} "
	tokken='\-----+------------+----------+----------'
	execute "${path_external_sw}autodock/vina --out ${out_molec}.pdbqt --receptor ${CWD}${target} --ligand ${CWD}${query} ${b} ${fileFlexi} \
	--center_x ${x} --center_y ${y} --center_z ${z} --size_x ${gridSizeX} --size_y ${gridSizeY} --size_z ${gridSizeZ} --num_modes ${numPoses} --cpu ${cores} ${opt_aux} &> ${out_aux}.ucm"
	if [[ "${error}" == "0" ]];then
		case ${option} in
			VS*)
				if [[ "$error" == "0" ]];then
					execute "funcionAdScore"
				fi
				coords=${x}":"${y}":"${z}
				create_out
			;;
			BD*)
				execute "funcionAdScore"
				execute "coords=\"`${path_extra_metascreener}used_by_metascreener/get_center_ligand.py ${out_molec}.pdbqt`\""
				create_out
			;;
		esac
	fi
}
function create_out()
{
	gauss_1=`cat ${out_energies}.en | grep "gauss\ 1"|awk -v vg="$vGauss1" -F: '{print $2*vg}'`
	gauss_2=`cat ${out_energies}.en | grep "gauss\ 2"|awk -v vg="$vGauss2" -F: '{print $2*vg}'`
	v_repulsion=`cat ${out_energies}.en | grep "repulsion"|tail -1|awk -v vg="$vRepulsion" -F: '{print $2*vg}'`
	v_hydrophobic=`cat ${out_energies}.en | grep "hydrophobic"|tail -1|awk -v vg="$vHydrophobic" -F: '{print $2*vg}'`
	v_hydrogen=`cat ${out_energies}.en | grep "Hydrogen"|tail -1|awk -v vg="$vHydrogen" -F: '{print $2*vg}'`
	v_rot=`cat ${out_molec}.pdbqt |tail -1 | awk -v vg="$vRot" '{print $2*vg}'`
	file_result=${out_molec}.pdbqt
	execute "global_score=\"` cat ${out_energies}.en |grep Affinity:|awk '{print $2}'`\""	
	graph_global_score=${gauss_1}:${gauss_2}:${v_repulsion}:${v_hydrophobic}:${v_hydrogen}:${v_rot}:${global_score}
	star_energies_atom=`cat ${out_energies}.en |grep -n "___________" |awk -F: '{print $1}' |head  -1`
	end_energies_atom=`cat ${out_energies}.en |grep -n "___________" |awk -F: '{print $1}' |head  -2 |tail -1`
	graph_atoms_score=`cat ${out_energies}.en|sed -n "$star_energies_atom,$end_energies_atom p" |grep -v "\_____" | \
	 awk -v a="${vGauss1}" -v b="${vGauss2}" -v c="${vRepulsion}" -v d="${vHydrophobic}" -v e="${vHydrogen}" '{print $7*a":"$8*b":"$9*c":"$10*d":"$11*e "\\\n"}'`
	graph_atoms_score=`echo $graph_atoms_score |sed 's/\ //g'`
	graph_atoms_type=`cat ${out_energies}.en|sed -n "$star_energies_atom,$end_energies_atom p" |grep -v "\_____" | awk '{print $2"_"$1":"}'`
	graph_atoms_type=`echo $graph_atoms_type |sed 's/\ //g'`

	if [ $refined_energy  == "ALL" ];then
	    refined_dm
	    refined_ad
	elif [ $refined_energy  == "GR" ];then
	    refined_dm

	elif [ $refined_energy  == "QU" ];then
        refined_qu
	fi

    execute "standar_out_file"

}
refined_dm()
{
	python2.7 ${path_extra_metascreener}/used_by_metascreener/get_energy_gromcas.py ${target} ${out_molec}.pdbqt > ${out_energies}".enmd"
    aux=`cat ${out_energies}".enmd" |tail -1`
	global_score_md=`echo $aux | cut -d ":" -f 2`
}
refined_qu()
{
    python2.7 ${path_extra_metascreener}/used_by_metascreener/get_energy_xtb.py ${target} ${out_molec}.pdbqt > ${out_energies}".enqu"
	global_score_qu=`cat ${out_energies}".enqu" |grep TOTAL |awk '{print $4}'`
}

checkAminChainFlex()
{
	if [ -z "$num_amino_acid" ];then
          num_amino_acid=0
    fi
    if [ -z "$chain" ];then
          chain=A
    fi
	b=""

	fileFlexi=""
	if [ "$flexFile" != "N/A" ];then
		fileFlexi="--flex "${CWD}$flexFile
	fi
	funcionFlexibilidad
}

funcionFlexibilidad()
{
	if [ "$flex" != "N/A" ];then ##si no es null
		pythonsh=${path_external_sw}mgltools_x86_64Linux2_latest/bin/pythonsh
		prepRec=${path_external_sw}mgltools_x86_64Linux2_latest/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_flexreceptor4.py
		if [ "$option" == "BD" ];then
			dirFL=${directorio}${aux}
			if [ -d  ${dirFL} ] ;then
				rm -r $dirFL
			fi
			mkdir -p $dirFL
			fl=$(python2 ${path_extra_metascreener}used_by_metascreener/get_flex_for_CA.py ${CWD}${target} $num_amino_acid | tee ${dirFL}/${number_execution}flex_str_${name_target}_${chain}_${num_amino_acid}.txt)
		else
			echo python ${path_extra_metascreener}used_by_metascreener/distanceXYZ.py $target $x $y $z $flex
			fl=`python ${path_extra_metascreener}used_by_metascreener/distanceXYZ.py $target $x $y $z $flex`
			
			aux=${chain}${name_target}-${nomLigando}-${x}-${y}-${z}-${num_amino_acid}
			dirFL=${directorio}${aux}
			if [ -d  "$dirFL" ] ;then
				rm -r $dirFL
			fi
			mkdir -p $dirFL


			fl=$(cat ${CWD}targets/${name_target}F.txt  | head -1 | awk '{print \$2}' | tee ${dirFL}/flex_str_${name_target}_${chain}_${num_amino_acid}.txt)
		fi

		cp ${CWD}${target} ${dirFL}/${name_target}.pdbqt
		${pythonsh}  ${prepRec} -r ${dirFL}/${name_target}.pdbqt -s ${fl} -g ${dirFL}/${name_target}_rigid.pdbqt -x ${dirFL}/${name_target}_flex.pdbqt > /dev/null
		target=$(basename $directorio)/${aux}/${name_target}_rigid.pdbqt
		b="--flex ${dirFL}/${name_target}_flex.pdbqt"
	fi
}

funcionAdScore()
{


	if [ "${flex}" == "N/A" ] && [ "${flexFile}" == "N/A" ];then

		debugY "$TAG: Rigido numPoses: $numPoses"
		if [ "$numPoses" -eq "1" ];then
			sed -i '1d' $out_molec.pdbqt
			sed -i  '$d' $out_molec.pdbqt
			execute "${path_external_sw}autodock/vina --score_only --ligand $out_molec.pdbqt --receptor  ${CWD}${target} --cpu ${cores} > ${out_energies}.en"
		else
			${path_external_sw}autodock/vina_split --input ${out_molec}.pdbqt > /dev/null
			for i in `seq 1 $numPoses` ;do
				${path_external_sw}autodock/vina --score_only --ligand ${out_molec}_ligand_${i}.pdbqt --receptor  ${CWD}${target} --cpu ${cores}> ${out_energies}_${i}.en
				mv ${out_molec}_ligand_${i}.pdbqt ${out_molec}_${i}.pdbqt
			done
		fi

	else

		debugY "scriptAD: Flexible "
		if [ "$numPoses" -eq "1" ]; then
			execute "sed -i '1d' ${out_molec}.pdbqt"
			execute "sed -i '\$d' ${out_molec}.pdbqt"

			numLinBorrar=`cat ${out_molec}.pdbqt | grep -n "BEGIN_RES" | head -1 | awk  -F: '{print $1}'`

			if [ "x${numLinBorrar}" == "x" ]; then
			    cp ${dirFL}/${name_target}_flex.pdbqt ${out_molec}-flex.pdbqt
			else
                n=`expr $numLinBorrar - 1`
                execute "sed '1,$n'd ${out_molec}.pdbqt >  ${out_molec}-flex.pdbqt"

                numFinLinea=`wc -l ${out_molec}.pdbqt | awk '{print $1}'`
                execute "sed -i '$numLinBorrar,$numFinLinea'd ${out_molec}.pdbqt"
            fi
            execute "${path_external_sw}autodock/vina --score_only  --flex $out_molec-flex.pdbqt --ligand $out_molec.pdbqt --receptor ${dirFL}/${name_target}_rigid.pdbqt > $out_energies.en"
		fi
	fi
}
