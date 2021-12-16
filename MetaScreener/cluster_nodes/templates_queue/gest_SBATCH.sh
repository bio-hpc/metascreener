#!/usr/bin/env bash
echo "#!/bin/sh" 								> $name_template_job
if [ "$renice" != "N/A" ];then
	echo "#SBATCH --nice=$renice"						>>$name_template_job 
fi
if [ "${GPU}" != "N/A" ];then
	echo "#SBATCH --gres=gpu:${GPU}" 					>>$name_template_job 
fi
if [ "${mem}" != "0" ];then
	echo "#SBATCH --mem=${mem}" 						>>$name_template_job
fi
if [ "$project" != "N/A" ];then
	echo ${queue_direc_project}${project}				>>$name_template_job
fi

echo "#SBATCH --output=${folder_out_jobs}${outJob}.out"	>>$name_template_job
echo "#SBATCH --error=${folder_out_jobs}${outJob}.err"	>>$name_template_job
echo "#SBATCH -p "${queue}>>$name_template_job
echo "#SBATCH -J ${name_job}"							>>$name_template_job
echo "#SBATCH --time=$time_job"							>>$name_template_job
echo "#SBATCH --cpus-per-task=$cores"						>>$name_template_job
echo "#SBATCH --nodes=${nodos}"							>>$name_template_job
source ${path_cluster_nodes}templates_queue/codigo.sh

