#!/usr/bin/env bash
#
#	Create a custom configuration file for the cluster in metascreener/config.conf
#
function write_comment()
{
	echo "#" >> ${file_conf}
	echo "# ${1}" >> ${file_conf}
	echo "#" >> ${file_conf}
}

readFile()
{
	aux="N/A"
	while read line
	do
   		if [[ $line != \#* ]];then
	 		host=`echo "$line" | cut -d ":" -f 1`
   			if   echo $1 |grep $host &>/dev/null;then
   			  	aux=`echo "$line" | cut -d ":" -f 2`
   			fi
   		fi
	done < $2
	echo $aux
}

queue_manager="N/A"
command_show_jobs="N/A"
queue_name="N/A"
command_get_id_job=":N/A"
command_dependency="bash "
queue_name=""
queue_direc_output=""
queue_direc_error=""
queue_direc_queue=""
queue_direc_mail_type=""	
queue_direc_mail_user=""
queue_direc_job_name=""
queue_direc_time=""
queue_direc_cpus=""
file_conf=${path_metascreener}/config.cfg

function get_queue_manager()
{

	a=`whereis sbatch|awk -F: '{print $2}'`
	commnad_execute="bash"
	if [ -n "$a" ];then
		command_show_jobs="squeue "
		commnad_execute="sbatch"
		queue_manager="SBATCH"
		command_get_id_job='echo ${job_id}| cut -d " " -f 4'

		command_dependency="sbatch --depend=afterok"
		queue_name="Slurm - Simple Linux Utility for Resource Management"
		queue_direc_output="#SBATCH --output="
		queue_direc_error="#SBATCH --error="
		queue_direc_queue="#SBATCH -p "
		queue_direc_project="#SBATCH -A "
		queue_direc_mail_type="#SBATCH --mail-type=END"
		queue_direc_mail_user="#SBATCH --mail-user="
		queue_direc_job_name="#SBATCH -J "
		queue_direc_time="#SBATCH --time="
		queue_direc_cpus="#SBATCH --cpus-per-task="
	
	else
		a=`whereis qsub|awk -F: '{print $2}'`
		if [ -n "$a" ];then
			
			a=`man qsub | col -bx |grep \#PBS |wc -l`
			if [ -z $a ];then
				error=10
			elif [ $a != 0 ];then
				command_show_jobs="qstat "
				queue_manager="QSTATPBD"
				queue_name="Sun Grid Engine (SGE) with PBS "
				command_get_id_job='echo ${job_id} | cut -d "." -f 1'
				command_dependency="qsub -W depend=afterok"
                commnad_execute="qsub"
				queue_direc_output="#PBS -o "
				queue_direc_error="#PBS -e"
				queue_direc_queue=""
				queue_direc_project="#PBS -A "
				queue_direc_mail_type=""
				queue_direc_mail_user="#PBS -M "
				queue_direc_job_name="#PBS -N "
				queue_direc_time="#PBS -lwalltime="
				queue_direc_cpus="#PBS -l nodes=1:ppn=1"
			else
				queue_name="Sun Grid Engine (SGE) without PBS "
				command_show_jobs="qstat "					 										
				queue_manager="AMAZON"
				command_get_id_job='echo ${job_id} | cut -d "." -f 1'
			fi
		fi
	fi	
}

function get_python_run()
{	

	python_run=`which python`
	python_version=$(${python_run} --version 2>&1)
	python_version=`echo $python_version | cut -d\  -f 2`
	python_run="python"
	echo ${python_run} ${python_version}

}

function get_java_run()
{
	
	java_run=`which java`
	java_version=$(${java_run} -version 2>&1)
	java_version=`echo $java_version | cut -d\  -f 3 | sed -e 's/"//g'`
	echo ${java_run} ${java_version}

}

if [ ! -f $file_conf ] ; then

	nom_serv=`echo $HOSTNAME`
	get_queue_manager

	aux=`get_python_run`
	python_run=`echo $aux | cut -d\  -f 1`
	python_version=`echo $aux | cut -d\  -f 2`
	aux=`get_java_run`
	java_run=`echo $aux | cut -d\  -f 1`
	java_version=`echo $aux | cut -d\  -f 2`

	write_comment "Path"
	echo "path_metascreener: ${path_metascreener}" >> ${file_conf}
	echo "path_login_node: ${path_metascreener}login_node/" >> ${file_conf}
	echo "path_cluster_nodes: ${path_metascreener}cluster_nodes/" >> ${file_conf}
	echo "path_analize_results: ${path_metascreener}analyze_results/" >> ${file_conf}
	echo "path_external_sw: ${path_metascreener}external_sw/" >> ${file_conf}
	echo "path_extra_metascreener: ${path_metascreener}extra_metascreener/" >> ${file_conf}
	
	write_comment "Hostname"
	echo "nom_serv: ${nom_serv}" >> ${file_conf}

	write_comment "Queue manager"
	echo "queue_name: ${queue_name}" >> ${file_conf}
	echo "queue_manager: ${queue_manager}" >> ${file_conf}
	echo "command_show_jobs: ${command_show_jobs}" >> ${file_conf}
	echo "command_get_id_job: ${command_get_id_job}" >> ${file_conf}
	echo "command_dependency: ${command_dependency}" >> ${file_conf}
	echo "queue_direc_output: ${queue_direc_output}" >> ${file_conf}
	echo "queue_direc_error: ${queue_direc_error}" >> ${file_conf}
	echo "queue_direc_queue: ${queue_direc_queue}" >> ${file_conf}
	echo "queue_direc_project: ${queue_direc_project}" >> ${file_conf}
	echo "queue_direc_mail_type: ${queue_direc_mail_type}" >> ${file_conf}
	echo "queue_direc_mail_user: ${queue_direc_mail_user}" >> ${file_conf}
	echo "queue_direc_job_name: ${queue_direc_job_name}" >> ${file_conf}
	echo "queue_direc_time: ${queue_direc_time}" >> ${file_conf}
	echo "queue_direc_cpus: ${queue_direc_cpus}" >> ${file_conf}
	echo "commnad_execute: ${commnad_execute}" >> ${file_conf}

	write_comment "Java"
	echo "java_run: ${java_run}" >> ${file_conf}
	echo "java_version: ${java_version}" >> ${file_conf}


	write_comment "Python"
	echo "python_run: ${python_run}" >> ${file_conf}
	echo "python_version: ${python_version}" >> ${file_conf}

	write_comment "Molecular Dynamics"
	echo "g_mmpbsa: ${path_metascreener}analyze_results/Simulation_gromacs/analyze_trajectory/extra/g_mmpbsa" >> ${file_conf}
	echo "g_gmx: gmx_mpi" >> ${file_conf}
	echo "g_amber_home: ${path_metascreener}external_sw/amber14/" >> ${file_conf}

	source ${path_metascreener}login_node/read_file_conf.sh
	read_file ${path_metascreener}
else
	source ${path_metascreener}login_node/read_file_conf.sh
	read_file ${path_metascreener}
fi




debugB "_________________________________________Global Config________________________________________"
debugB ""
debugB "Create_config.sh path_metascreener: ${path_metascreener}"
debugB "Create_config.sh path_login_node: ${path_login_node}"
debugB "Create_config.sh path_cluster_nodes: ${path_cluster_nodes}"
debugB "Create_config.sh path_analize_results: ${path_analize_results}"
debugB "Create_config.sh path_external_sw: ${path_external_sw}"
debugB "Create_config.sh path_extra_metascreener: ${extra_metascreener}"

debugB "Create_config.sh nom_serv: ${nom_serv}"
debugB "Create_config.sh queue_name: ${queue_name}"
debugB "Create_config.sh queue_manager: ${queue_manager}"
debugB "Create_config.sh command_show_jobs: ${command_show_jobs}"
debugB "Create_config.sh command_get_id_job: ${command_get_id_job}"
debugB "Create_config.sh cluster_project: ${cluster_project}"
debugB "Create_config.sh cluster_queue: ${cluster_queue}"
debugB "Create_config.sh command_dependency: ${command_dependency}"


debugB "Create_config.sh queue_direc_output: ${queue_direc_output}"
debugB "Create_config.sh queue_direc_error: ${queue_direc_error}"
debugB "Create_config.sh queue_direc_queue: ${queue_direc_queue}"
debugB "Create_config.sh queue_direc_project: ${queue_direc_project}"
debugB "Create_config.sh queue_direc_mail_type: ${queue_direc_mail_type}"
debugB "Create_config.sh queue_direc_mail_user: ${queue_direc_mail_user}"
debugB "Create_config.sh queue_direc_time: ${queue_direc_time}"
debugB "Create_config.sh queue_direc_cpus: ${queue_direc_cpus}"


debugB "Create_config.sh java_run: ${java_run}"
debugB "Create_config.sh java_version: ${java_version}"

debugB "Create_config.sh python_run: ${python_run}"
debugB "Create_config.sh python_version: ${python_version}"
debugB ""