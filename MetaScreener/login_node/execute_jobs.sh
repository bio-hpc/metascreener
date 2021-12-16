#!/usr/bin/env bash
#
# Author: Jorge de la Peña García
# Author: Carlos Martínez Cortés
#	Email:  cmartinez1@ucam.edu
#	Description: Crea la plantilla para el job, y lo lanza. Es llamado tantas veces como lanzaJob le indique
#__________________________________________________________________________________________________________________________

function print_debug()
{
	debugC "_________________________________________Excecute jobs________________________________________"
	debugC ""
	debugC "execute_jobs.sh: name_template_job: $name_template_job"
	debugC "execute_jobs.sh: source ${path_cluster_nodes}/templates_queue/gest_${2}.sh"
	debugC "${1}"
}
#
# Busca un nombre adecuado para la plantilla del job
#
function name_template()
{	
  name_template_job="job-"${name_target}-${name_query}                #busco un nombre para el fichero de plantilla  
  name_template_job=$name_template_job"-"$contIni"-"$contFin".sh" #le añado las pos x y z y cont ini cont fin     
  name_template_job=${folder_templates_jobs}$name_template_job
  echo $name_template_job     
}
#
# crea una plantilla y la lanza
#

source ${CWD}MetaScreener/login_node/read_all_conf.sh
name_template_job=$(name_template)  #nombre de la plantilla que se lanzara
if [ "$secuencial" == "N/A" ];then 
	source ${path_cluster_nodes}/templates_queue/gest_${queue_manager}.sh                   #Se crea y se lanza la plantilla del job
    print_debug "execute_jobs.sh: ${commnad_execute}"  "${queue_manager}"
    job_id=`${commnad_execute} ${name_template_job}`
    job_id=`eval ${command_get_id_job}`
    echo "+ JOB: "${job_id}
    jobsIDs=${jobsIDs}:${job_id}
else
	source ${path_cluster_nodes}/templates_queue/gest_SBATCH.sh                   #Se crea y se lanza la plantilla del job
    print_debug "execute_jobs.sh: bash $name_template_job" "SBATCH"
    bash $name_template_job #esjecutar MetaScreener en secuencial
fi



