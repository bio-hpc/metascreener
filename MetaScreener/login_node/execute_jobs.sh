#!/usr/bin/env bash
#
# Author: Jorge de la Peña García
# Author: Carlos Martínez Cortés
#	Email:  cmartinez1@ucam.edu
#	Description: Creates the template for the job, and launches it. It is called as many times as the lanzaJob tells it to.
#__________________________________________________________________________________________________________________________

function print_debug()
{
	debugC "_________________________________________Excecute jobs________________________________________"
	debugC ""
	debugC "execute_jobs.sh: name_template_job: $name_template_job"
	debugC "execute_jobs.sh: source ${path_cluster_nodes}/templates_queue/gest_${2}.sh"
	debugC "${1}"
}

function name_template()
{	
  name_template_job="job-"${name_target}-${name_query}                
  name_template_job=$name_template_job"-"$contIni"-"$contFin".sh"    
  name_template_job=${folder_templates_jobs}$name_template_job
  echo $name_template_job     
}

source ${CWD}MetaScreener/login_node/read_all_conf.sh
name_template_job=$(name_template)  
if [ "$secuencial" == "N/A" ];then 
	source ${path_cluster_nodes}/templates_queue/gest_${queue_manager}.sh                  
    print_debug "execute_jobs.sh: ${commnad_execute}"  "${queue_manager}"
    job_id=`${commnad_execute} ${name_template_job}`
    job_id=`eval ${command_get_id_job}`
    echo "+ JOB: "${job_id}
    jobsIDs=${jobsIDs}:${job_id}
else
	source ${path_cluster_nodes}/templates_queue/gest_SBATCH.sh 
    print_debug "execute_jobs.sh: bash $name_template_job" "SBATCH"
    bash $name_template_job 
fi
