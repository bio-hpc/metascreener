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
        printHelp "t" "N" "Folder with .pmz files."
        printHelp "l" "N" "Folder where the library is."
        printHelp "qu" "N" "Partition for the resource allocation."
        printHelp "AS" "O" "Lower stop of -a parameter."
        printHelp "AE" "O" "Upper stop of -a parameter."
        printHelp "TT" "O" "Time for LigandScout."
        printHelp "j" "O" "Number of job per execution."
        echo ""
        exit
}


target=no_target
library=no_library
queue=no_queue
ini=0
fin=5
JOBS_PER_EXECUTION=15
time=50m

while (( $# ))
 do
    if [[ "$1" == \-[a-z]* ]] || [[ "$1" == \-[A-Z]* ]] || [[ "$1" == \-\-[a-a]* ]] || [[ "$1" == \--[A-Z]* ]];then
           case `printf "%s" "$1" | tr '[:lower:]' '[:upper:]'`  in
                        -T )  target=$2;;
                        -L )  library=$2;;
                        -QU)  queue=$2;;
                        -AE )  fin=$2;;
                        -AS )  ini=$2;;
                        -J )  JOBS_PER_EXECUTION=$2;;
                        -TT ) time=$2;;
                        -H )  ayuda
            esac
        fi
  shift
done

if [[ "$library" == "no_library" ]] || [[ "$target" == "no_target" ]] || [[ "$queue" == "no_queue" ]];then
        echo -e "\e[31mERROR: Parameter Missing or Invalid.\e[0m"; 
        ayuda
fi

lib="$(basename $library)"
lib="${lib%.*}"
mkdir -p "LS_${lib}/"

for i in $(ls -p $target | grep -v /);do
                filename=${i%.*}
                extension="${i##*.}"
                if [[ $extension == "pmz" ]] || [[ $extension == "pml" ]];then
                        for j in $(seq $ini $fin);do
                          ./ms.sh -t $target/${i} -q ${library} -s LS -o VS -j ${JOBS_PER_EXECUTION}  -prp LS -prl LS -tj 24:00:00 -d LS_${lib}/LS_${filename}_${lib}_a_${j}   -a ${j} -TT ${time}  -sf relative -qu ${queue}
                        done
                fi
              
done
