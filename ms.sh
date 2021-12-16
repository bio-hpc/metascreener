#!/bin/bash
# 
#	Authors:	 Jorge De La Peña García 	  (  jpena@ucam.edu       )
#                        Carlos Martínez Cortés           (  cmartinez1@ucam.edu  )
#                        Antonio Jesús Banegas Luna       (  ajbanegas@ucam.edu   )
#			 Ricardo Rodriguez Schmidt	  (  rrschmidt@ucam.edu   )
#			 Alfonso Pérez Garrido.   	  (  aperez@ucam.edu      )
#			 Miguel Carmena Bargueño	  (  mcarmena@ucam.edu    )
#			 Horacio Pérez Sánchez   	  (  hperez@ucam.edu      )
#
#_______________________________________________________________________________________________________________________________

error=0		  
paraMError="" 	  
txtErrror=""  	  
informe=""	  
fecha=$(date +"%Y-%m-%d")
pathSL="MetaScreener/login_node/"
path_metascreener="${PWD}/MetaScreener/"

if [ ! -f "singularity/metascreener.simg" ]; then
  echo -e "${RED}WARNING: singularity/metascreener.simg does not exist"
  echo "Downloading singularity/metascreener.simg..."
  wget --no-check-certificate -r "https://drive.google.com/u/1/uc?export=download&confirm=TLUF&id=1L3HZ2l1XARqzEKaV14jToUtUOCmo4OjV" -O singularity/singularity.zip > /dev/null 2>&1
  unzip singularity/singularity.zip -d singularity/ > /dev/null 2>&1
  rm singularity/singularity.zip
fi

function f_help(){
	source ${pathSL}help.sh $1
	if [ ! -z "$txtErrror" ];then 
		echo ""
		echo -e "${RED}ERROR: ${BROWN}"$txtErrror"${NONE}"
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
		1)  txtErrror="$laError Incorrect docking program"   ; f_help;;
		2)  txtErrror="$laError Incorrect docking technique for that program"; f_help;;
		3)  txtErrror="$laError Extension not valid for docking program"; f_help;;
		4)  txtErrror="$laError Ligand or protein file empty"; f_help;;
		5)  txtErrror="$laError Cluster hostname not found"; f_help;;
		6)  txtErrror="$laError No docking option found"; f_help;;
		7)  txtErrror="$laError numJobs, x, y, or z are empty"; f_help;;
		8)  txtErrror="$laError Protein file, ligand folder or ligand file DOES NOT EXIST";f_help;;
		9)  txtErrror="$laError You cannot use hyphens (-) in protein or ligand file names";f_help;;
		10) txtErrror="$laError Wrong queue manager, ";f_help;;
		11) txtErrror="$laError Renice parameter wrong, check help";f_help;;
		12) txtErrror="$laError Unknown Parameter $paraMError, check help";f_help;;
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
			txtErrror="No parameters found for the test ${option} ${software}"
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











