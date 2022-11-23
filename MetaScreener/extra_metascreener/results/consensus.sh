#!/usr/bin/env bash
#
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Generates a consensus session with the results of MetaScreener runs.
# ______________________________________________________________________________________________________________________

NONE='\033[00m' #no color
GREEN='\033[00;32m'
PURPLE='\033[00;35m'
CYAN='\033[00;36m'

ms_path=${PWD/metascreener*/}/metascreener
simg="singularity exec --bind=${PWD} $ms_path/singularity/metascreener.simg"
extra_metascreener="$ms_path/MetaScreener/extra_metascreener"

printHelp(){
        printf "${GREEN} %6s ${CYAN}%5s ${NONE}%-s \n" "-$1 )" "[ $2 ]" "$3"
}

function ayuda()
{
        echo -e "${GREEN}Help:"
        printf "\t${CYAN}%s${NONE} \n"  "[ O=optional, N=Necesary ]"
        echo ""
        echo -e "${PURPLE}Options${NONE} "
        echo -e "${PURPLE}____________________________________________________${NONE} "
        printHelp "o" "N" "Option [ BD | VS | LS ]."
        printHelp "f" "N" "String with folder list or folder prefix (only LS)."
        printHelp "r" "O" "Receptor (necesary for VS and BD)."
        printHelp "c" "O" "Cutoff (only LS [0-1])."
        printHelp "out" "O" "Folder output Don't use name with \"_\". Necesary for VS and BD."
        printHelp "cl" "O" "String with options to launch in the cluster. For example: \"-p standard --time 5:00:00 ...\""
        printHelp "h" "O" "Print help"
        echo ""
        exit
}

option=no_option
folders=no_folder
receptor=no_receptor
out=no_out
cluster_opt=sequential
cutoff=0.8

# Parameters
while (( $# ))
 do
    if [[ "$1" == \-[a-z]* ]] || [[ "$1" == \-[A-Z]* ]] || [[ "$1" == \-\-[a-a]* ]] || [[ "$1" == \--[A-Z]* ]];then
           case `printf "%s" "$1" | tr '[:lower:]' '[:upper:]'`  in
                        -O )  option=$2;;
                        -F )
                          folders=$2
                          shift
                          while [[ $2 != -* ]] && [[ $2 != "" ]]
                          do
                            folders="${folders} $2"
                            shift
                          done
                          ;;
                        -R )  receptor=$2;;
                        -C )  cutoff=$2;;
                        -OUT )  out=$2;;
                        -CL)  cluster_opt=$2;;
                        -H )  ayuda
            esac
        fi
  shift
done

# Mandatory options
if [[ "$option" == "no_option" ]] || [[ "$folders" == "no_folder" ]];then
        echo -e "\e[31mERROR: Parameter Missing or Invalid.\e[0m";
        ayuda
fi

# Prepare commands
case `printf "%s" "$option" | tr '[:lower:]' '[:upper:]'` in
  BD )
    if [[ "$receptor" == "no_receptor" ]];then echo -e "\e[31mERROR: Receptor Missing.\e[0m";ayuda;fi
    if [[ "$out" == "no_out" ]];then echo -e "\e[31mERROR: Output Missing.\e[0m";ayuda;fi
    cross="${simg} python ${extra_metascreener}/results/cross/cross_list_bd.py ${folders}"
    join="${simg} python ${extra_metascreener}/results/join/join_cl_json_bd_session.py ${receptor} $(basename ${receptor} | cut -f 1 -d '_')*.json ${out}"
    ;;
  VS )
    if [[ "$receptor" == "no_receptor" ]];then echo -e "\e[31mERROR: Receptor Missing.\e[0m";ayuda;fi
    if [[ "$out" == "no_out" ]];then echo -e "\e[31mERROR: Output Missing.\e[0m";ayuda;fi
    lst="lst_VS_"$(basename ${receptor} | cut -f 1 -d ".")".txt"
    cross="${simg} python ${extra_metascreener}/results/cross/cross_list_vs.py ${folders} -o ${lst}"
    join="${simg} python ${extra_metascreener}/results/join/join_cl_json_vs_session.py -d ${folders} -o ${out} -r ${receptor} -v -f ${lst}"
    ;;
  LS )
    join="${simg} python ${extra_metascreener}/results/join/join_ls_sessions.py ${folders} -c ${cutoff}"
    ;;
  * )
    echo -e "\e[31mERROR: Invalid Option.\e[0m";ayuda;;
esac


if [[ "$cluster_opt" == "sequential" ]];then
  echo ${cross}
  $cross
  echo ${join}
  $join
  if [[ "$option" != "LS" ]];then
    for pml in $(find *${out}* -name *.pml)
    do
      echo "cmd.save(\"$(basename ${pml} ".pml").pse\")" >> $pml
    done
    find *${out}* -name *.pml -execdir ${simg} pymol -c -q -k -Q {} \; > /dev/null
    folder=$(find . -type d -name "${out}_*")
    tar -cf ${folder}.tar.gz ${folder}
  fi
else
  name_job="consensus_${option}.sh"
  echo "#!/bin/bash" > $name_job
  if [[ "$option" != "LS" ]];then
    echo ${cross}
    echo "${cross}" >> $name_job
  fi
  echo ${join}
  echo "${join}" >> $name_job
  if [[ "$option" != "LS" ]];then
    echo "for pml in \$(find ${out}* -name *.pml)" >> $name_job
    echo "do" >> $name_job
    echo "  echo \"cmd.save(\\\"\$(basename \${pml} \\\".pml\\\").pse\\\")\" >> \$pml" >> $name_job
    echo "done" >> $name_job
    echo "find *${out}* -name *.pml -execdir ${simg} pymol -c -q -k -Q {} \; > /dev/null" >> $name_job
    echo "folder=\$(find . -type d -name \"${out}_*\")" >> $name_job
    echo "tar -cf \${folder}.tar.gz \${folder}" >> $name_job
  fi
  echo "rm ${name_job}" >> $name_job
  sbatch $cluster_opt $name_job
fi
