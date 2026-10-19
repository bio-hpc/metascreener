#!/usr/bin/env bash
#
#	Code for calculate the number of jobs to launch and the dependencies of get_histogram
#	
#_____________________________________________________________________________________________________
jobsIDs=""
comandDependenci=""

convertsecs() {
   ((h=${1}/3600))
  ((m=(${1}%3600)/60))
  ((s=${1}%60))
  printf "%02d:%02d:%02d\n" $h $m $s
}

#
#	Print jobs config
#
printParameters()
{
	debugB "_________________________________________Config Job ________________________________________"
	debugB ""
	debugB "Lanza_job.sh: Total of ligands(VS) or Alpha Carbons(BD): numFicheros: $numFicheros"
	debugB "Lanza_job.sh: Number of jobs to be launched, it may vary by one more if the division is not exact num_per_job: $num_per_job"
	debugB "Lanza_job.sh: Executions that will be made in each job Nruns: $nRuns"
	debugB "Lanza_job.sh: Number of executions for job (nRuns): $nRuns"
	debugB "Lanza_job.sh: Number of jobs launched without remainder (num_per_job): "$num_per_job
	debugB "Lanza_job.sh: Number of dockings for the last job (remainder): $resto"
	debugB "Lanza_job.sh: Time for JOB: $time_job"
	debugB "Lanza_job.sh: Time for docking: $time_experiment"
	debugB ""
}
#____________________________________________________________________________________________________________________________________
#
#	Send jobs to cluster
#_________________________________________________________________________________________________________________________________
send_jobs()
{
	SALIR=0
	final=""
	contIni=0
	if [ -z "$numFicheros" ];then
		echo -e ${REDB}"There was a problem reading ligand. Check your license of ${software}."${NONE}
		exit
	fi
    # Check if items_per_job is specified, if so use it instead of num_per_job
    if [ ! -z "$items_per_job" ] && [ "$items_per_job" != "N/A" ];then
       # Calculate number of jobs based on items per job
       num_per_job=`expr $numFicheros \/ $items_per_job`
       resto=`expr $numFicheros \% $items_per_job`
       nRuns=$items_per_job
       contFin=`expr $contIni \+ $nRuns`
       if [ $resto -gt 0 ];then
          num_per_job=`expr $num_per_job + 1`
       fi
    else
       # Original logic: num_per_job is the number of jobs
       if [ $numFicheros -lt $num_per_job ];then
          echo -e ${REDB}"ERROR You can not launch more jobs than ligands (VS) or Alpha Carbons (BD) "${NONE}
          exit
       fi
       resto=`expr $numFicheros \% $num_per_job`
       nRuns=`expr $numFicheros \/ $num_per_job`
       contFin=`expr $contIni \+ $nRuns`
       balance_jobs
    fi

	if [ "${time_job}" == "N/A" ];then
		if [ $resto -gt $nRuns ];then
			time_job=`expr $resto \* $time_experiment`
			time_job=`convertsecs $time_job`
		else
			time_job=`expr $nRuns \* $time_experiment`
			time_job=`convertsecs $time_job`
		fi
	fi
	printParameters


	source ${pathSL}resume.sh

	# Use a single SLURM job array (one task per chunk) when submitting to Slurm.
	# For sequential runs or other queue managers, keep the classic one-job-per-chunk loop.
	if [ "$secuencial" == "N/A" ] && [ "$queue_manager" == "SBATCH" ]; then
		send_job_array
	else
		while [  $SALIR == 0 ]
		do
			funcionJob
			contIni=$contFin
			contFin=`expr $contFin + $nRuns`
			if [ `expr $contFin + $resto`  -gt `expr $numFicheros` ]; then
		  		 SALIR=1
			fi
		done
		if [ $resto -ne 0 ];then
			contFin=`expr $contIni + $resto`
			funcionJob
		fi
	fi

	if [ "$histograms" != "N/A" ]; then # Excepction for join_ls_sessions
		get_histogram
		if [ "$secuencial" == "N/A" ];then
			debugB "${command_dependency}${jobsIDs}  ${folder_templates_jobs}template_get_hystogram.sh"
			${command_dependency}${jobsIDs}  ${folder_templates_jobs}template_get_hystogram.sh
		else
			debugB "bash  ${folder_templates_jobs}template_get_hystogram.sh"
			bash  ${folder_templates_jobs}template_get_hystogram.sh
			
		fi
	fi
}

#
#	Send all chunks of the experiment as a single SLURM job array.
#	Each array task processes one chunk ([contIni, contFin)), computed at runtime
#	from SLURM_ARRAY_TASK_ID. If the number of tasks exceeds the cluster's
#	MaxArraySize, the run is split into several array submissions, each with an
#	offset; every submission id is collected in jobsIDs so the histogram job can
#	depend (afterok) on all of them.
#
function send_job_array()
{
	# Chunk size and last-chunk remainder are derived from nRuns so the task
	# mapping is identical to the classic per-chunk loop for both -j and -ij modes.
	array_resto=`expr $numFicheros \% $nRuns`
	array_count=`expr $numFicheros \/ $nRuns`
	if [ $array_resto -gt 0 ];then
		array_count=`expr $array_count + 1`
	fi
	if [ $array_count -le 0 ];then
		array_count=1
	fi

	# Cap each array submission to the cluster MaxArraySize (default 1000 indices).
	MAX_ARRAY_SIZE=`empty_variable $max_array_size 1000`
	if ! [[ "$MAX_ARRAY_SIZE" =~ ^[0-9]+$ ]];then
		MAX_ARRAY_SIZE=1000
	fi

	source ${CWD}MetaScreener/login_node/read_all_conf.sh

	array_offset=0
	while [ $array_offset -lt $array_count ]
	do
		remaining=`expr $array_count - $array_offset`
		if [ $remaining -gt $MAX_ARRAY_SIZE ];then
			array_chunk_size=$MAX_ARRAY_SIZE
		else
			array_chunk_size=$remaining
		fi
		array_index_max=`expr $array_chunk_size - 1`

		name_template_job="${folder_templates_jobs}job-${name_target}-${name_query}-array-${array_offset}.sh"

		source ${path_cluster_nodes}/templates_queue/gest_SBATCH_array.sh

		debugB "lanza_job.sh: ${commnad_execute} ${name_template_job} (array 0-${array_index_max} offset ${array_offset})"
		job_id=`${commnad_execute} ${name_template_job}`
		job_id=`eval ${command_get_id_job}`
		echo "+ ARRAY JOB: "${job_id}" (tasks ${array_offset}-`expr $array_offset + $array_index_max`)"
		jobsIDs=${jobsIDs}:${job_id}

		array_offset=`expr $array_offset + $array_chunk_size`
	done
}

#
#	Create a template that will have dependencies on the submitted jobs
# 
function get_histogram()
{
  bind1=/$(echo ${path_metascreener} | cut -d'/' -f2)/
  bind2=/$(echo ${folder_experiment} | cut -d'/' -f2)/

  if [ $bind1 == $bind2 ];then
    bind=$bind1
  else
    bind=$bind1,$bind2
  fi

	echo "#!/bin/sh" >	${folder_templates_jobs}template_get_hystogram.sh
	if [ "$secuencial" == "N/A" ];then
		echo ${queue_direc_output}${folder_out_jobs}post.out 	>>${folder_templates_jobs}template_get_hystogram.sh
		echo ${queue_direc_error}${folder_out_jobs}post.err 	>>${folder_templates_jobs}template_get_hystogram.sh
		if [ "$queue" != "N/A" ];then
			echo ${queue_direc_queue}${queue} 				>>${folder_templates_jobs}template_get_hystogram.sh
		fi
		if [ "$project" != "N/A" ];then
			echo ${queue_direc_project}${project} 				>>${folder_templates_jobs}template_get_hystogram.sh
		fi

		if [ "$mem_hist" == "N/A" ];then
		  echo "#SBATCH --mem=2G" 						>>${folder_templates_jobs}template_get_hystogram.sh
		else
		  echo "#SBATCH --mem=${mem_hist}" 						>>${folder_templates_jobs}template_get_hystogram.sh
		fi

		if [ $email != "N/A" ];then
			echo ${queue_direc_mail_type}					>>${folder_templates_jobs}template_get_hystogram.sh
			echo ${queue_direc_mail_user}${email}			>>${folder_templates_jobs}template_get_hystogram.sh
		fi
		echo ${queue_direc_job_name}"${name_job}_g_h"			>>${folder_templates_jobs}template_get_hystogram.sh
		if [ $time_hist == "N/A" ];then
			time_hist="24:00:00"
		fi
		echo ${queue_direc_time}${time_hist}				>>${folder_templates_jobs}template_get_hystogram.sh
		echo ${queue_direc_cpus}"1"							>>${folder_templates_jobs}template_get_hystogram.sh
	fi
	echo "echo \"start job\" 1>&2"							>>${folder_templates_jobs}template_get_hystogram.sh
	echo "date +\"%s   %c\" 1>&2"							>>${folder_templates_jobs}template_get_hystogram.sh
	echo "${modules_get_histogram}"							>>${folder_templates_jobs}template_get_hystogram.sh

  if [ $software == "AD" ] || [ $software == "LF" ] || [ $software == "GN" ] ;then

    if [[ $target_pdb == "no_target" ]];then
      echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_analize_results}get_histogram_picture.py --prog=$software --opt=$option -i ${folder_experiment} -p $target -l $query --rf $rf --rb $rb --profile ${profile} -d $debug">>${folder_templates_jobs}template_get_hystogram.sh
    else
      echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_analize_results}get_histogram_picture.py --prog=$software --opt=$option -i ${folder_experiment} -p $target --pdb=${target_pdb} -l $query --rf $rf --rb $rb --profile ${profile} -d $debug">>${folder_templates_jobs}template_get_hystogram.sh
    fi

    if [ $option = "VS" ];then
      echo "pml=\`basename ${folder_experiment}\`.pml">>${folder_templates_jobs}template_get_hystogram.sh
    else
      echo "pml=\`basename ${folder_experiment}\`_*.pml">>${folder_templates_jobs}template_get_hystogram.sh
    fi
    echo "find ${folder_experiment} -name \${pml} -execdir singularity exec --bind $bind \$PWD/singularity/metascreener.simg pymol -c -q -k -Q "{}" \; > /dev/null 2>&1">>${folder_templates_jobs}template_get_hystogram.sh
    echo "find ${folder_experiment} -name \`basename ${folder_experiment}\`.pse ! -path ${folder_experiment}\`basename ${folder_experiment}\`.pse -exec cp "{}" ${folder_experiment} \;">>${folder_templates_jobs}template_get_hystogram.sh
    echo "python ${path_extra_metascreener}used_by_metascreener/get_csv.py ${folder_experiment}" >>${folder_templates_jobs}template_get_hystogram.sh

  # For LS only needs a summary in .csv
  elif [ $software == "LS" ];then
    echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_extra_metascreener}results/join/join_ls_sessions.py ${folder_experiment} -q $query -s --pack" >>${folder_templates_jobs}template_get_hystogram.sh
  elif [ $software == "EO" ] || [ $software == "RC" ] ;then
    echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python3 ${path_extra_metascreener}used_by_metascreener/get_openeye_csv.py ${folder_experiment} $software " >>${folder_templates_jobs}template_get_hystogram.sh
  elif [ $software == "DC" ];then
    # Collect per-molecule Dragon ranking CSVs into the experiment root (summary product).
    echo "find ${folder_experiment}molecules -name '*.csv' -exec cp -t ${folder_experiment} {} + 2>/dev/null || true" >>${folder_templates_jobs}template_get_hystogram.sh
    echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python3 ${path_extra_metascreener}used_by_metascreener/pack_experiment.py ${folder_experiment}" >>${folder_templates_jobs}template_get_hystogram.sh
  elif [ $software == "OM" ];then
    # OM is a preparation step: no special summary product beyond time.txt / archive.
    echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python3 ${path_extra_metascreener}used_by_metascreener/pack_experiment.py ${folder_experiment}" >>${folder_templates_jobs}template_get_hystogram.sh
  else
    rm ${folder_templates_jobs}template_get_hystogram.sh
    exit
  fi

     echo "bash ${path_extra_metascreener}used_by_metascreener/get_time_resume.sh ${folder_out_jobs} >> ${folder_experiment}time.txt">>${folder_templates_jobs}template_get_hystogram.sh
    # Files produced after packing are added to (or replaced in) the archive at the very end.
    exp_base=$(basename "${folder_experiment}")
    echo "exp_dir=${folder_experiment%/}" >>${folder_templates_jobs}template_get_hystogram.sh
    echo "tgz=${exp_base}.tar.gz" >>${folder_templates_jobs}template_get_hystogram.sh
    echo "late_files=\"\${exp_dir}/${exp_base}.pse \${exp_dir}/Results_scoring.csv \${exp_dir}/time.txt\"" >>${folder_templates_jobs}template_get_hystogram.sh
    cat >>${folder_templates_jobs}template_get_hystogram.sh << 'EOF'
if [ -f "$tgz" ]; then
  tmp_tar=$(mktemp)
  tmp_tgz=$(mktemp)
  ok=1
  gzip -dc "$tgz" > "$tmp_tar" || ok=0
  for f in $late_files; do
    [ $ok -eq 1 ] && [ -f "$f" ] || continue
    rel=$(realpath --relative-to=. "$f" 2>/dev/null || basename "$f")
    if tar -tf "$tmp_tar" | grep -qxF "$rel"; then
      tar --delete -f "$tmp_tar" "$rel" || ok=0
    fi
    tar -rf "$tmp_tar" "$rel" || ok=0
  done
  if [ $ok -eq 1 ] && gzip -c "$tmp_tar" > "$tmp_tgz"; then
    mv "$tmp_tgz" "$tgz"
  else
    echo "ERROR: could not add late files to $tgz" 1>&2
    rm -f "$tmp_tgz"
  fi
  rm -f "$tmp_tar"
fi
EOF
	# Archive the job-array script(s) once the array has finished (no-op for the classic per-chunk flow).
	echo "mv ${folder_templates_jobs}job-*-array-*.sh ${folder_jobs_done} 2>/dev/null">>${folder_templates_jobs}template_get_hystogram.sh
	echo "mv ${folder_templates_jobs}template_get_hystogram.sh ${folder_jobs_done}">>${folder_templates_jobs}template_get_hystogram.sh
	echo "echo \"end job\" 1>&2">>${folder_templates_jobs}template_get_hystogram.sh
	echo "date +\"%s   %c\" 1>&2">>${folder_templates_jobs}template_get_hystogram.sh

}

#
#	Balance the jobs.
#	With this loop we try to balance jobs to optimize the time
#
function balance_jobs()
{
	while [ $resto -gt $nRuns ]
	do
		num_per_job=`expr $num_per_job - 1`
		resto=`expr $numFicheros \% $num_per_job`
		nRuns=`expr $numFicheros \/ $num_per_job`
		contFin=`expr $contIni \+ $nRuns`
	done

	if [ ${nRuns} -lt ${bd_exhaustiveness} ];then
	    echo "ERROR: bd_exhaustiveness $bd_exhaustiveness is too high "
	    exit
	fi
	if [ $resto -eq 0 ];then
		echo -e ${BLUEB}"Offsetting the load of jobs: the following are launched "$num_per_job   ${NONE}
	else
		echo -e ${BLUEB}"Offsetting the load of jobs: the following are launched "$num_per_job "+1"  ${NONE}
	fi
}
#
#	Send jobs to cluster in packages
#
funcionJob()
{

	jobID=""
	outJob=$contIni-$contFin
	debugB "lanza_job.sh: ${path_login_node}execute_jobs.sh"
	source ${path_login_node}execute_jobs.sh
}






