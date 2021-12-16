#!/bin/bash

NONE='\033[00m' #no color
GREEN='\033[00;32m'
PURPLE='\033[00;35m'
CYAN='\033[00;36m'

printHelp(){
        printf "${GREEN} %6s ${CYAN}%5s ${NONE}%-s \n" "-$1 )" "[ $2 ]" "$3"
}

function ayuda()
{
        echo -e "${GREEN}Help: $option ${NONE}"
        printf "\t${CYAN}%s${NONE} \n"  "[ O=optional, N=Necesary ]"
        echo ""
        echo -e "${PURPLE}Options${NONE} "
        echo -e "${PURPLE}____________________________________________________${NONE} "
        printHelp "t" "N" "Folder with proteins."
        printHelp "q" "N" "Folder with ligands."
        printHelp "s" "N" "Available Software [ AD | LF ]"
        printHelp "qu" "N" "Partition for the resource allocation."
        printHelp "j" "O" "Number of job per execution."
        echo ""
        exit
}

target=no_target
querie=no_library
queue=no_queue
software=no_software
jobs=10

while (( $# ))
 do
    if [[ "$1" == \-[a-z]* ]] || [[ "$1" == \-[A-Z]* ]] || [[ "$1" == \-\-[a-a]* ]] || [[ "$1" == \--[A-Z]* ]];then
           case `printf "%s" "$1" | tr '[:lower:]' '[:upper:]'`  in
                        -T )  target=$2;;
                        -Q )  querie=$2;;
                        -S )  software=`echo $2 | awk '{print toupper($0)}'`;;
                        -QU)  queue=$2;;
                        -J )  jobs=$2;;
                        -H )  ayuda
            esac
        fi
  shift
done

if [[ "$querie" == "no_library" ]] || [[ "$target" == "no_target" ]] || [[ "$queue" == "no_queue" ]] || [[ "$software" == "no_software" ]] ;then
        echo -e "\e[31mERROR: Parameter Missing or Invalid.\e[0m";
        ayuda
fi

if [[ $software == "AD" ]];then
  target_files=(`find $target -maxdepth 1 -name "*.pdbqt"`)
  queries_files=(`find $querie -maxdepth 1 -name "*.pdbqt"`)
elif [[ $software == "LF" ]];then
  target_files=(`find $target -maxdepth 1 -name "*.mol2"`)
  queries_files=(`find $querie -maxdepth 1 -name "*.mol2"`)
fi

if [ ${#target_files[@]} -eq 0 ] || [ ${#queries_files[@]} -eq 0 ];then
  echo echo -e "\e[31mERROR: A folder with at least one target and one query.\e[0m";
fi

total_jobs=$((${#target_files[@]}*${#queries_files[@]}*($jobs+1)))
echo -e "${CYAN}The approximate number of jobs is $total_jobs${PURPLE} (${#target_files[@]} protein with ${#queries_files[@]} ligands with $jobs+1 jobs each)${NONE}."
while true; do
  read -p "$(echo -e ${CYAN}Are you sure to run the BDs?${NONE})" yn
  case $yn in
    [Yy]* ) break;;
    [Nn]* ) exit;;
    * ) echo -e "\e[31mPlease answer yes or no.\e[0m";;
  esac
done


for target in `ls ${target_files[@]}`
do
  for querie in `ls ${queries_files[@]}`
  do
    echo "BD $software for protein $target with ligand $querie and $jobs jobs"
    ./sm.sh -t $target -q $querie -o BD -s $software -j $jobs -hi y -qu $queue
  done
done
