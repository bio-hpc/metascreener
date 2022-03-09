#!/usr/bin/env bash
execute_script()
{	
    
	unset DISPLAY
	TAG=`echo $(basename $BASH_SOURCE)`
	lib=`echo $(basename $query)`
	if [ ${option} == "VS" ];then
		opt_aux=${opt_aux/-TT/-T}
		opt_aux=${opt_aux/-sf/-S}
		execute "${path_external_sw}ligandScout/iscreen -q ${CWD}${target} -d ${CWD}${query} -M ${mem} -C ${cores} -F ${ini} -L ${fin} -P -o ${out_molec}.sdf ${opt_aux} &>${out_aux}.ucm"

		if [ -f "${out_molec}.sdf" ] && [ -s "${out_molec}.sdf" ]; then

			execute "${path_external_sw}tools/babel -m ${out_molec}.sdf ${out_molec}_.sdf &> /dev/null"
			for fich in ${out_molec}_*.sdf; do				
				name=`head -n 1 "${fich}"`						
				name="$(echo -e "${name}" | tr -d '[:space:]')"				
		    	execute "filename=`echo $(basename $fich)`"
		    	filename=${filename%.*}
		    	filename=${filename%_*}_${name}
		    	out_energies=${folder_energies}/${filename}

				execute "H=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"H:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "HBD=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"HBD:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "HBA=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"HBA:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "AR=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"AR:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "PI=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"PI:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "NI=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"NI:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"
				execute "ZNB=`grep \"<Matching Features>\" -A1 $fich | tail -1 | grep -o \"ZNB:[0-9]*\" | uniq -c | awk -F: '{ feature=$2"_"feature} END {print feature}'`"

				execute "score=`grep \"<Score\" -A1 $fich | tail -1`"				
        execute "echo \"${name} ${score} "H:"$H "HBD:"$HBD "HBA:"$HBA "AR:"$AR "PI:"$PI "NI:"$NI "ZNB:"$ZNB\" > ${folder_energies}/${filename}.feat"
				execute "global_score=${score}"
                execute "query=/${name}"
				execute "file_result=$fich"
                execute "standar_out_file"
                mv ${fich} ${folder_grid}
			done

		fi

		
	else
		echo "LS only works with VS technique"
		exit
	fi
}


