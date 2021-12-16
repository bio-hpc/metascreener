#!/usr/bin/env bash
function read_file()
{
	file_conf=${1}/config.cfg
	path_metascreener=`cat ${file_conf} |grep "path_metascreener" |cut -d\  -f 2`
	path_login_node=`cat ${file_conf} |grep "path_login_node" |cut -d\  -f 2`
	path_cluster_nodes=`cat ${file_conf} |grep "path_cluster_nodes" |cut -d\  -f 2`
	path_analize_results=`cat ${file_conf} |grep "path_analize_results" |cut -d\  -f 2`
	path_external_sw=`cat ${file_conf} |grep "path_external_sw" |cut -d\  -f 2`
	path_extra_metascreener=`cat ${file_conf} |grep "extra_metascreener" |cut -d\  -f 2`

	nom_serv=`cat ${file_conf} |grep "nom_serv" |cut -d\  -f 2`
	
	queue_name=`cat ${file_conf} |grep "queue_name" |cut -d\  -f 2`
	queue_manager=`cat ${file_conf} |grep "queue_manager" |cut -d\  -f 2`
	command_show_jobs=`cat ${file_conf} |grep "command_show_jobs" |cut -d\  -f 2`
	command_get_id_job=`cat ${file_conf} |grep "command_get_id_job" |cut -d\: -f 2`
	command_dependency=`cat ${file_conf} |grep "command_dependency" |cut -d\: -f 2`

	commnad_execute=`cat ${file_conf} |grep "commnad_execute" |cut -d\  -f 2`
	queue_direc_output=`cat ${file_conf} |grep "queue_direc_output" |cut -d\: -f 2`
	queue_direc_error=`cat ${file_conf} |grep "queue_direc_error" |cut -d\: -f 2`
	queue_direc_queue=`cat ${file_conf} |grep "queue_direc_queue" |cut -d\: -f 2`
	queue_direc_project=`cat ${file_conf} |grep "queue_direc_project" |cut -d\: -f 2`
	queue_direc_mail_type=`cat ${file_conf} |grep "queue_direc_mail_type" |cut -d\: -f 2`
	queue_direc_mail_user=`cat ${file_conf} |grep "queue_direc_mail_user" |cut -d\: -f 2`
	queue_direc_job_name=`cat ${file_conf} |grep "queue_direc_job_name" |cut -d\: -f 2`
	queue_direc_time=`cat ${file_conf} |grep "queue_direc_time" |cut -d\: -f 2`
	queue_direc_cpus=`cat ${file_conf} |grep "queue_direc_cpus" |cut -d\: -f 2`

	cluster_project=`cat ${file_conf} |grep "cluster_project" |cut -d\  -f 2`
	cluster_queue=`cat ${file_conf} |grep "cluster_queue" |cut -d\  -f 2`
	
	python_run=`cat ${file_conf} |grep "python_run" |cut -d\  -f 2`
	python_version=`cat ${file_conf} |grep "python_version" |cut -d\  -f 2`

	java_run=`cat ${file_conf} |grep "java_run" |cut -d\  -f 2`
	java_version=`cat ${file_conf} |grep "java_version" |cut -d\  -f 2`


    modules_metascreener=`sed -n  '/Metascreener_mol/,/Metascreener_get_histogram/p' MetaScreener/config.cfg |grep -v \# | paste -sd\;`
    modules_get_histogram=`sed -n  '/Metascreener_get_histogram/,/end_modules/p' MetaScreener/config.cfg |grep -v \# | paste -sd\;`

}