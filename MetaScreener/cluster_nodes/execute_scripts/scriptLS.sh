#!/usr/bin/env bash
execute_script()
{	
    
	unset DISPLAY
	TAG=`echo $(basename $BASH_SOURCE)`
	lib=`echo $(basename $query)`
	if [ ${option} == "VS" ];then
		# If global timeout (-TD) and items per job (-IJ) are set, derive LigandScout
		# per-compound timeout (-T) in minutes: TD(sec) / 60 / items_per_job.
		if [ "${time_experiment}" != "N/A" ] && [ -n "${time_experiment}" ] && \
		   [ "${items_per_job}" != "N/A" ] && [ -n "${items_per_job}" ]; then
			# Ensure items_per_job is a positive integer
			if [ "${items_per_job}" -gt 0 ] 2>/dev/null; then
				td_min=$(( time_experiment / 60 ))
				if [ "${td_min}" -lt 1 ]; then
					td_min=1
				fi
				T_per_compound=$(( td_min / items_per_job ))
				if [ "${T_per_compound}" -lt 1 ]; then
					T_per_compound=1
				fi
				# Remove any previous -T value and append the computed one
				opt_aux=$(echo "${opt_aux}" | sed -E 's/-T[[:space:]]*[0-9]+//g;s/-T[0-9]+//g')
				opt_aux="${opt_aux} -T${T_per_compound}"
			fi
		fi

		opt_aux=${opt_aux/-TT/-T}
		opt_aux=${opt_aux/-sf/-S}
		execute "${path_external_sw}ligandScout/iscreen -q ${CWD}${target} -d ${CWD}${query} -M${mem//[^0-9]/} -C ${cores} -F ${ini} -L ${fin} -P -o ${out_molec}.sdf ${opt_aux} &>${out_aux}.ucm"

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


