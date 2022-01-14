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
	if [ $numFicheros -lt $num_per_job ];then
		echo -e ${REDB}"ERROR You can not launch more jobs than ligands (VS) or Alpha Carbons (BD) "${NONE}
		exit

	fi
	resto=`expr $numFicheros \% $num_per_job`
	nRuns=`expr $numFicheros \/ $num_per_job`
	contFin=`expr $contIni \+ $nRuns`
	balance_jobs

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
		  echo "#SBATCH --mem=500M" 						>>${folder_templates_jobs}template_get_hystogram.sh
		else
		  echo "#SBATCH --mem=${mem_hist}" 						>>${folder_templates_jobs}template_get_hystogram.sh
		fi

		if [ $email != "N/A" ];then
			echo ${queue_direc_mail_type}					>>${folder_templates_jobs}template_get_hystogram.sh
			echo ${queue_direc_mail_user}${email}			>>${folder_templates_jobs}template_get_hystogram.sh
		fi
		echo ${queue_direc_job_name}"${name_job}_g_h"			>>${folder_templates_jobs}template_get_hystogram.sh
		if [ $time_hist == "N/A" ];then
			time_hist="5:00:00"
		fi
		echo ${queue_direc_time}${time_hist}				>>${folder_templates_jobs}template_get_hystogram.sh
		echo ${queue_direc_cpus}"1"							>>${folder_templates_jobs}template_get_hystogram.sh
	fi
	echo "echo \"start job\" 1>&2"							>>${folder_templates_jobs}template_get_hystogram.sh
	echo "date +\"%s   %c\" 1>&2"							>>${folder_templates_jobs}template_get_hystogram.sh
	echo "${modules_get_histogram}"							>>${folder_templates_jobs}template_get_hystogram.sh

	if [ $software != "LS" ];then

    if [[ $target_pdb == "no_target" ]];then
      echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_analize_results}get_histogram_picture.py --prog=$software --opt=$option -i ${folder_experiment} -p $target -l $query --profile ${profile} -d $debug">>${folder_templates_jobs}template_get_hystogram.sh
    else
      echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_analize_results}get_histogram_picture.py --prog=$software --opt=$option -i ${folder_experiment} -p $target --pdb=${target_pdb} -l $query --profile ${profile} -d $debug">>${folder_templates_jobs}template_get_hystogram.sh
    fi

    if [ $option = "VS" ];then
      echo "pml=\`basename ${folder_experiment}\`.pml">>${folder_templates_jobs}template_get_hystogram.sh
    else
      echo "pml=\`basename ${folder_experiment}\`_clusters.pml">>${folder_templates_jobs}template_get_hystogram.sh
    fi
    echo "find ${folder_experiment} -name \${pml} -execdir singularity exec --bind $bind \$PWD/singularity/metascreener.simg pymol -c -q -k -Q "{}" \;">>${folder_templates_jobs}template_get_hystogram.sh
    echo "find ${folder_experiment} -name \`basename ${folder_experiment}\`.pse -exec cp "{}" . \;">>${folder_templates_jobs}template_get_hystogram.sh

    echo "python ${path_extra_metascreener}used_by_metascreener/get_csv.py ${folder_experiment}" >>${folder_templates_jobs}template_get_hystogram.sh

  # For LS only needs a summary in .csv
  else
    echo "singularity exec --bind $bind ${PWD}/singularity/metascreener.simg python ${path_extra_metascreener}results/join/join_ls_sessions.py ${folder_experiment} -q $query -s " >>${folder_templates_jobs}template_get_hystogram.sh
  fi

  echo " sh ${path_extra_metascreener}used_by_metascreener/get_time_resume.sh ${folder_out_jobs} >> ${folder_experiment}time.txt">>${folder_templates_jobs}template_get_hystogram.sh

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
		echo -e ${BLUEB}"Conpensando la carga de jobs: se lanzan "$num_per_job   ${NONE}
	else
		echo -e ${BLUEB}"Conpensando la carga de jobs: se lanzan "$num_per_job "+1"  ${NONE}
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






