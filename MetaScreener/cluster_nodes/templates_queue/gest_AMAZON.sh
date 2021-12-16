#!/usr/bin/env bash
echo "#!/bin/bash" 						                > $name_template_job
echo "#$ -cwd"							                >>$name_template_job
echo "#$ -o ${folder_out_jobs}${outJob}.out"			>>$name_template_job
echo "#$ -e ${folder_out_jobs}${outJob}.out"			>>$name_template_job
echo "#$ -N $name_job"					                >>$name_template_job
echo "#$ -l mem_free=${mem}"			            	>>$name_template_job
echo "#$ -l s_rt=$time_job"				                >>$name_template_job
echo "#$ -S /bin/bash"				                	>>$name_template_job
if [ "${GPU}" != "N/A" ];then
	echo "#$ -l ngpu=${GPU}" 					        >>$name_template_job
fi
echo "#$ -l excl=true"                                  >>$name_template_job
echo "#$ -l gpu_type=nv_k20"                            >>$name_template_job
echo "#$ -pe mpi_rr   ${cores}"                         >>$name_template_job
echo "#$ -r y"                                          >>$name_template_job
source ${path_cluster_nodes}templates_queue/codigo.sh
