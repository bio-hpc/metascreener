#
#	Checks if a renice has been entered and for which queue manager it will be
#
check_renice()
{
	if [ $secuencial == "N/A" ];then
		if [ "$renice" != "N/A" ];then
			if [ "${queue_manager}" == "QSTATPBD" ];then
				if [ $renice -lt -1024 ] || [ $renice -gt 1023 ];then
					error=11
				fi  
			elif [ "${queue_manager}" == "SBATCH" ];then
				if [ $renice -lt 0 ] || [ $renice -gt 10000 ];then
					error=11
				fi  
			fi
		fi
	fi
}

check_renice


