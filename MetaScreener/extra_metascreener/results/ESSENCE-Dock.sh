#!/usr/bin/env bash
#
#   Author: Jochem Nelen
#   Author: Carlos Martinez Cortes
#   Email:  jnelen@ucam.edu
#   Description: Performs the ESSENCE-Dock workflow using molecular docking runs as input
# ______________________________________________________________________________________________________________________

NONE='\033[00m' #no color
GREEN='\033[00;32m'
PURPLE='\033[00;35m'
CYAN='\033[00;36m'

ms_path=${PWD/metascreener*/}/metascreener
simg="singularity exec --bind=${PWD} $ms_path/singularity/ESSENCE-Dock.simg"
extra_metascreener="$ms_path/MetaScreener/extra_metascreener"

if [ ! -f "$ms_path/singularity/ESSENCE-Dock.simg" ]; then
	echo "The required ESSENCE-Dock Singularity image doesn't seem to be present. Would you like to download it automatically? "
	echo "(Y/y) Download Singularity image automatically"
	echo "(N/n) Exit"
	read -r answer
	while [ "${answer,,}" != "y" ] && [ "${answer,,}" != "yes" ] && [ "${answer,,}" != "n" ] && [ "${answer,,}" != "no" ]; do
		echo "Would you like to download the Singularity image automatically?"
		echo "(Y/y) Download Singularity image automatically"
		echo "(N/n) Exit" 
		read -r answer 
	done
	if [ "${answer,,}" = "y" ] || [ "${answer,,}" = "yes" ]; then 
		wget --no-check-certificate -r "https://drive.usercontent.google.com/download?id=1yN63r8sl26VMZJtdrAG4e_JQFFlb1eE8&confirm=t" -O ${ms_path}/singularity/ESSENCE-Dock.simg
		echo "The Singularity image has been downloaded"
	else 
		echo "Exiting.. Please install the Singularity image and try again"
		exit
	fi	
fi

printHelp(){
	printf "${GREEN} %6s ${CYAN}%5s ${NONE}%-s \n" "-$1 )" "[ $2 ]" "$3"
}

function help()
{
	echo -e "${GREEN}Help:"
	printf "\t${CYAN}%s${NONE} \n"  "[ O=Optional, N=Necessary ]"
	echo ""
	echo -e "${PURPLE}Options${NONE} "
	echo -e "${PURPLE}____________________________________________________${NONE} "
	printHelp "f | d" "N" "Path to the individual docking run folders"
	printHelp "o | out" "N" "What Folder to save the results to"
	printHelp "p | r" "O" "The protein receptor used for the docking (PDB format recommended). Only optional when there no postprocessing is performed"
	printHelp "np | no-postprocessing | raw" "O" "Skip post-processing of the best results, so no PSE or PLIP interactions are generated. Post-processing is performed by default"
	printHelp "n | nc" "O" "Amount of compounds to include in the final PyMol Session. Default is 50"
	printHelp "cl | cluster" "O" "String with options to launch in the cluster. Important: Always accompany this flag with an argument! For example: \"-p standard --time 12:00:00 ...\""
	printHelp "c | cpus" "O" "Number of CPUs to use"
	printHelp "t | timeout" "O" "Max time spent processing per compound"
	printHelp "s | silent" "O" "Silent Mode: Don't show the progression of the ESSENCE-Dock consensus calculations. Only works without the -cl flag: silent mode disabled by default"
	printHelp "ns | nosilent" "O" "No Silent Mode: Show the progression of the ESSENCE-Dock consensus calculations. Only works with the -cl flag: silent mode enabled by default"
	printHelp "sc | skip-cleanup" "O" "Skip the cleanup: intermediate files will not be removed"
	printHelp "debug" "O" "Explicitly posts the individual commands, useful for debugging. Will also keep the intermediate results"
	printHelp "h | help" "O" "Print help"
	echo ""
	exit
}

folders=no_folder
receptor=no_receptor
out=no_out
silent=false
CLsilent=true
numberOfCompounds=50
DiffDockPath="N/A"
noPostProcessing=false
skipcleanup=false
cluster_opt=sequential
input_dirs=0
debug=false
CPUS=1
timeoutLimit=3
# Parameters
while (( $# ))
	do
		if [[ "$1" == \-[a-z]* ]] || [[ "$1" == \-[A-Z]* ]] || [[ "$1" == \-\-[a-z]* ]] || [[ "$1" == \--[A-Z]* ]];then
			case `printf "%s" "$1" | tr '[:lower:]' '[:upper:]'`  in
				-F | -D)
						if [[ "$2" == *"VS_DD_"* ]]; then
							DiffDockPath=$2
							folders=""
						else
							folders=$2
						fi
						input_dirs=$((input_dirs + 1))
						shift
						while [[ $2 != -* ]] && [[ $2 != "" ]]
						do
							input_dirs=$((input_dirs + 1))
							if [[ "$2" == *"VS_DD_"* ]]; then
								DiffDockPath=$2   
							else
								folders="${folders} $2"                     
							fi                                                                  
							shift
						done;;
					-R | -P)  receptor=$2;;
					-N | -NC)  numberOfCompounds=$2;;
					--DEBUG | -DEBUG )  debug=true;;
					--OUT | -OUT | -O )  out=$2;;
					--SILENT | -SILENT | -S)  silent=true;;
					--SKIP-CLEANUP | -SKIP-CLEANUP | -SC)  skipcleanup=true;;
					--NOSILENT | -NOSILENT | -NS)  CLsilent=false;;
					--NO-POSTPROCESSING | -NO-POSTPROCESSING | -RAW | -NP)  noPostProcessing=true;;
					--CLUSTER | -CLUSTER | -CL)  cluster_opt=$2;;
					--CPUS | -CPU | -C)  CPUS=$2;;
					--TIMEOUT | -TIMEOUT | -T)  timeoutLimit=$2;;
					--HELP | -HELP | -H) help
			esac
		fi
	shift
done

# Mandatory options
if [[ "$folders" == "no_folder" ]];then
	echo -e "\e[31mERROR: Please provide the path to the individual docking runs.\e[0m";
	help
fi

if [[ "$receptor" == "no_receptor" && "$noPostProcessing" == false ]];then
	echo -e "\e[31mERROR: Please provide the protein receptor using postprocessing.\e[0m";
	help
fi
if [[ ! "$numberOfCompounds" =~ ^[0-9]+$ ]];then
	echo -e "\e[31mERROR: Please provide a valid number for the amount of final compounds to be processed.\e[0m";
	help
fi

if [[ ! $input_dirs -gt 1 ]];then
	echo -e "\e[31mERROR: Please provide more than 1 docking run as input\e[0m";
	help
fi

# Prepare commands
if [[ "$out" == "no_out" ]];then 
	echo -e "\e[31mERROR: Output Missing.\e[0m";
	help;
else
	out="${out%/}_$(date +%Y_%m_%d)"
fi

if [ -d $out ];then
	while [ "${input,,}" != "y" ] && [ "${input,,}" != "yes" ] && [ "${input,,}" != "n" ] && [ "${input,,}" != "no" ]; do
		echo "The output directory ${out} already exists. To continue you must delete this directory. Do you want to delete it? "
		echo "(Y/y) Delete folder"
		echo "(N/n) Exit"
		read  input
	done
	if [ "${input,,}" == "y" ] || [ "${input,,}" == "yes" ];then
		rm -r ${out}
		mkdir ${out}
	elif [ "${input,,}" == "n" ] || [ "${input,,}" == "no" ];then
		exit
	fi
	else
		mkdir ${out}
	fi

lst="${out}/Preprocessed_"$(basename ${receptor} | cut -f 1 -d ".")".txt"
cross="${simg} python ${extra_metascreener}/results/cross/ESSENCE-Dock_cross.py ${folders} -o ${lst}"

# Execute the commands
if [[ "$cluster_opt" == "sequential" ]];then
	join="${simg} python ${extra_metascreener}/results/join/ESSENCE-Dock_Consensus.py -o ${out} -r ${receptor} -dd ${DiffDockPath} -f ${lst} -s ${silent} -n ${numberOfCompounds} -raw ${noPostProcessing} -c ${CPUS} -t ${timeoutLimit}"
	echo "Preparing docking runs for ESSENCE-Dock Consensus.."
	if $debug; then
		echo -e "\e[0;34m[DEBUG]  Full Command:\n${cross}\e[0m"
	fi
	$cross
	echo "Starting ESSENCE-Dock Consensus Calculations.."
	if $debug; then
		echo -e "\e[0;34m[DEBUG] Full Command:\n${join}\e[0m"
	fi
	time $join
	
	if ! $noPostProcessing; then
		echo -e "\nGenerating Final PSE file.."
		for pml in $(find ${out}/* -name *.pml)
		do
		echo "cmd.save(\"$(basename ${pml} ".pml").pse\")" >> $pml
		done
		find ${out}/* -name *.pml -execdir ${simg} pymol -c -q -k -Q {} \; > /dev/null

		if [[ "$skipcleanup" == false && "$debug" == false ]];then
			echo "Cleaning up temporary files.."
			rm ${out}/*.pml
			rm -r ${out}/Molecules/
		fi

	fi

	if [[ "$skipcleanup" == false && "$debug" == false ]];then
			rm ${lst}
	fi

else
	join="${simg} python ${extra_metascreener}/results/join/ESSENCE-Dock_Consensus.py -o ${out} -r ${receptor} -dd ${DiffDockPath} -f ${lst} -s ${CLsilent} -n ${numberOfCompounds} -raw ${noPostProcessing} -c ${CPUS} -t ${timeoutLimit}"
	receptorName="${receptor##*/}" 
	mkdir "$out/job_data/"
	name_job="${out}/job_data/ESSENCE-Dock_Consensus_${receptorName%.*}.sh"
	echo "#!/bin/bash" > $name_job
	if $debug; then
		echo -e "\e[0;34m[DEBUG]  Full Command:\n${cross}\e[0m"
	fi
  
	echo "${cross}" >> $name_job
	if $debug; then
		echo -e "\e[0;34m[DEBUG] Full Command:\n${join}\e[0m"
	fi 
  	echo "time ${join}" >> $name_job
  	
	if [[ "$noPostProcessing" == false ]];then
		echo "for pml in \$(find ${out}/*.pml)" >> $name_job
		echo "do" >> $name_job
		echo "echo \"cmd.save(\\\"\$(basename \${pml} \".pml\").pse\\\")\" >> \$pml" >> $name_job
		echo "done" >> $name_job
		echo "find ${out}/* -name *.pml -execdir ${simg} pymol -c -q -k -Q {} \; > /dev/null" >> $name_job
		
		if [[ "$skipcleanup" == false && "$debug" == false ]];then
			echo "rm ${out}/*.pml" >> $name_job
			echo "rm -r ${out}/Molecules/" >> $name_job
		fi

	fi

	if [[ "$skipcleanup" == false && "$debug" == false ]];then
			echo "rm ${lst}" >> $name_job
	fi

	sbatchCommand="sbatch ${cluster_opt} -o ${out}/job_data/ESSENCE_Dock_job%j.out --job-name=ESSENCE-Dock ${name_job}"
	$sbatchCommand
fi

