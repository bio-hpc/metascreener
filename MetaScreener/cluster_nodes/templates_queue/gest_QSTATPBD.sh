#!/usr/bin/env bash
echo "#!/bin/sh" 								> $name_template_job
if [ "$project" != "N/A" ];then
	echo "#PBS -A "${project}					>>$name_template_job
fi
if [ "$queue" != "N/A" ];then
	echo "#PBS -q "${cluster_queue} 			>>$name_template_job
fi
if [ "$renice" != "N/A" ];then
	echo "#PBS -p $renice" 						>>$name_template_job
fi
if [ "${GPU}" != "N/A" ];then
	echo "#SBATCH --gres=gpu:${GPU}" 					>>$name_template_job
fi

echo "#PBS -o ${folder_out_jobs}${outJob}.out "	>>$name_template_job
echo "#PBS -e ${folder_out_jobs}${outJob}.err "	>>$name_template_job
echo "#PBS -N ${name_job}"							>>$name_template_job
echo "#PBS -l walltime=$time_job"				>>$name_template_job
echo "#PBS -l nodes=${nodos}:ppn=${cores}"              >>$name_template_job

source ${path_cluster_nodes}templates_queue/codigo.sh


