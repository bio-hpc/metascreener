#!/bin/bash
# 
#	Authors:	 Carlos Martínez Cortés           (  cmartinez1@ucam.edu  )
#                        Antonio Jesús Banegas Luna       (  ajbanegas@ucam.edu   )
#			 Alfonso Pérez Garrido.   	  (  aperez@ucam.edu      )
#			 Miguel Carmena Bargueño	  (  mcarmena@ucam.edu    )
#			 Horacio Pérez Sánchez   	  (  hperez@ucam.edu      )
#
#_______________________________________________________________________________________________________________________________

error=0		  
paraMError="" 	  
txtError=""  	  
informe=""	  
fecha=$(date +"%Y-%m-%d")
pathSL="MetaScreener/login_node/"
path_metascreener="${PWD}/MetaScreener/"

if [ ! -f "singularity/metascreener.simg" ] || [ ! -f "singularity/metascreener_22.04.simg" ]; then
  echo -e "${RED}WARNING: You need singularity images to use MetaScreener"
  echo "Downloading singularity images..."
  wget --no-check-certificate -r "https://drive.usercontent.google.com/download?id=1L3HZ2l1XARqzEKaV14jToUtUOCmo4OjV&export=download&authuser=1&confirm=t&uuid=0c83343d-17fe-4282-bf07-9a2321537a9a&at=APZUnTW_78yhd6klINcZBOjxIU6g:1706872870521" -O singularity/singularity.zip > /dev/null 2>&1
  unzip singularity/singularity.zip -d singularity/ > /dev/null 2>&1
  rm singularity/singularity.zip
fi

function f_help(){
	source ${pathSL}help.sh $1
	if [ ! -z "$txtError" ];then 
		echo ""
		echo -e "${RED}ERROR: ${BROWN}"$txtError"${NONE}"
		echo ""
	fi
	exit
}


#______________________________________________________________________
#
#	Function for check input error
#____________________________________________________________________
function f_Error()
{
	
	laError="MetaScreener.sh,"
	case $error in
		1)  txtError="$laError Incorrect docking program"   ; f_help;;
		2)  txtError="$laError Incorrect docking technique for that program"; f_help;;
		3)  txtError="$laError Extension not valid for docking program"; f_help;;
		4)  txtError="$laError Ligand or protein file empty"; f_help;;
		5)  txtError="$laError Cluster hostname not found"; f_help;;
		6)  txtError="$laError No docking option found"; f_help;;
		7)  txtError="$laError numJobs, x, y, or z are empty"; f_help;;
		8)  txtError="$laError Protein file, ligand folder or ligand file DOES NOT EXIST";f_help;;
		9)  txtError="$laError You cannot use hyphens (-) in protein or ligand file names";f_help;;
		10) txtError="$laError Wrong queue manager, ";f_help;;
		11) txtError="$laError Renice parameter wrong, check help";f_help;;
		12) txtError="$laError Unknown Parameter $paraMError, check help";f_help;;
	esac
}
#___________________________________________________________________________________________________________________________________________________________#
#																																							                                                                              #
#															MAIN																							                                                                            #
#___________________________________________________________________________________________________________________________________________________________#

source ${pathSL}colors.sh
source ${pathSL}parameters.sh
source ${pathSL}debug.sh
source ${pathSL}create_conf.sh

source ${path_login_node}/folders_experiment.sh

if [ "$mode_test" != "N/A" ];then
	if [ "$software" != "" ]  && [ "$option" != "" ];then
		if [ -f "${pathSL}/test_params/test_params_${option}_${software}.sh" ]; then
			source ${pathSL}/test_params/test_params_${option}_${software}.sh
		else
			txtError="No parameters found for the test ${option} ${software}"
			f_help
		fi
	else
		source ${pathSL}/test_params/test_params_default.sh # Default test BD AD with debug
	fi
fi

source ${path_login_node}check_renice.sh

source ${path_login_node}verify_input_data.sh


f_Error
source ${path_login_node}create_dirs.sh

source ${path_login_node}create_params.sh
f_Error

if [ -f "${path_login_node}techniques/SLTechnique${option}.sh" ];then 
	source ${path_login_node}techniques/SLTechnique${option}.sh
else
	error=2
	f_Error
fi











