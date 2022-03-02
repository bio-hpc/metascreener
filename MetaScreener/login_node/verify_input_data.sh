#!/usr/bin/env bash
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Code in charge of validating the necessary options for the operation of metascreener: recetor, query, jobs, protocols, ...
# ______________________________________________________________________________________________________________________

#
#	Read template of parameters
#
readParam()
{

	if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
		echo `cat ${path_login_node}templateParams/template${software}.txt |grep "#${2}" | cut -d : -f 2`
	else
		echo "$1"
	fi
}
readParams()
{
	
	if [ -f "${path_login_node}/templateParams/template${software}.txt" ];then
		extensionesProt=`readParam "$extensionesProt" "LanzExtensionProtQ"`
		extensionesLig=`readParam "$extensionesLig" "LanzExtensionligB"` 
		cores=`readParam "$cores" "LanzCores"`
		time_experiment=`readParam "$time_experiment" "LanzTimeExecution"`
		x=`readParam "$x" "LanzCoordX"`
		y=`readParam "$y" "LanzCoordY"`
		z=`readParam "$z" "LanzCoordZ"`
		grid=`readParam "$grid" "LanzGrid"`
		mem=`readParam "$mem" "LanzMem"`
		optionsLanz=`readParam "$optionsLanz" "lanzOptions"`
		gridSizeX=`readParam "$gridSizeX" "lanzSizeGridX"`
		gridSizeY=`readParam "$gridSizeY" "lanzSizeGridY"`
		gridSizeZ=`readParam "$gridSizeZ" "lanzSizeGridZ"`
		lanzTimeOut=`readParam "$lanzTimeOut" "lanzTimeOut"`
		lanzCreateResume=`readParam "$lanzCreateResumen" "lanzCreateResumen"`
	else
		txtError="-s .Not Available Software, see the help"
		f_help
	fi
}

#
#	Show verion and rev
#
showVersion()
{
	codVersion=`git rev-list --reverse HEAD |tail -1`
	numVersion=`git rev-list --reverse HEAD |wc -l`
	rama=`git branch -avv |grep "\*" |awk '{print $2}'`
	version="${GREEN}Version: ${BLUE}${numVersion} ${GREEN}Rev( ${BLUE}${codVersion}${GREEN} ) ${NONE}"
	echo ""
	echo -e "${GREEN}${version}${GREEN} Branch: ${BLUE}$rama${NONE}"
	echo ""
	exit
}

#
#	Check if option is empty
#
isEmpty()
{
	if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
		txtError="$2"
	 	f_help
	fi
}

#
#	Search in a array ($1) if a word is found ($2)
#
existInLst()
{

	
	auxIFS=$IFS
	
	IFS=',' read -ra extx <<< "$1"
	aux=""

	for i in "${extx[@]}"; do
    	if [ "${2}" == "${i}" ];then
	   		aux=$i
	   	fi
	done
	IFS=$auxIFS
	echo "$aux"
}

#
#	Verify that the x y z or numJobs are not empty
#
verifyXYZ()
{
	if [[ ${option} == "BD"* ]] || [[ ${option} == "VSR" ]];then
		x=0;y=0;z=0;
	fi
	if [ -z $x ] || [ -z $y ] || [ -z $z ];then
		error=7
	fi
}

#
#	Validates if target's extension is valid for SW
#
validateExtProt()
{   
	if [ -f ${target} ];then
		
		extensionProtAux="."${target##*.}
		ext_target=`existInLst "$extensionesProt" "$extensionProtAux"`
		if [ "$ext_target" == "" ];then
			txtErrror="-s Software does not support that extension "
			f_help
		fi 
	else
		txtErrror="-t Target file does not exist"
		f_help
	fi
}

#
#	Validate query's extension
#
validate_ext_query()
{
	ext_query=""
	if [[ "$option" == *"VS"* ]];then
	    if [ "$extensionesLig" != "" ];then
            auxIFS=$IFS
            IFS=',' read -ra extx <<< "$extensionesLig"
            for i in "${extx[@]}"; do
                aux=`find ${query}/ -name "*${i}" -maxdepth 1 2> /dev/null|wc -l`

                if [ $aux != 0 ] ;then
                    ext_query=$i
                    break;
                fi
            done
            IFS=$auxIFS
            if [ "$ext_query" == "" ];then
                txtErrror="-q You must enter a folder with valid queries for the software"
                f_help
            fi
        fi
	else
		if [ -f "$query" ];then
			extensionLigAux="."${query##*.}
			ext_query=`existInLst "$extensionesLig" "$extensionLigAux"`
			if [ "$ext_query" == "" ];then
				txtErrror="-s The Software does not support ligand's extension"
				f_help
			fi
		else
			txtErrror="Querie does not exist"
			f_help
		fi
	fi
	name_query=$(basename "$query")

	name_query="${name_query%.*}"

}

OpcionesExtras()
{

	if [ $software == "S3" ] || [ $software == "s3" ];then
		sed -i -r "s|Java Path=.+|Java Path=${path_external_sw}jre/|" ${path_external_sw}ChemAxon/JChem/bin/java.ini
	elif [ $option == "SD" ];then
				extension=".pdb"
	fi
}

#
#	Find a name for the job
#
find_name_job()
{
    if [ "${name_job}" == "" ]; then
        if [ "$secuencial" == "N/A" ] && [ "$command_show_jobs" != "N/A" ];then
            fckUser=$USER
            MAXJOBS=500
            for (( i=1; i<=MAXJOBS; i++ ))
            do
                name_job=${option}_${software}_$i
                a=`$command_show_jobs -u $fckUser |grep -w $name_job |wc -l`
                if [ $a -eq 0 ];then
                    break
                fi
            done
        else
            name_job=${option}_${software}_sequential
        fi
    fi
}

#
#	MAIN
#
if [ "$check" != "N/A" ];then
	source ${path_login_node}preDebug.sh
	exit
fi
if [ "${versionHelp}" != "N/A" ];then
	showVersion
fi

isEmpty "$software" 				"-s Software is empty"
readParams
isEmpty "$option" 					"-o Option is empty"
isEmpty "$queue"					"-qu Queue is empty"

if [ "$extensionesLig"  != "" ];then
    isEmpty "$query" 					"-q Ligand is empty"
else
    query="no_query"
fi


if [ "$extensionesProt" != "" ];then
	isEmpty "$target" 			"-t Receptor is empty"
	validateExtProt
	name_target=$(basename $target)
	name_target="${name_target%.*}"
fi
echo ${software}
if [ "${extensionesProt}" == ".mol2" ];then
  if ([ ${software} == "LF" ] || [ ${software} == "FB" ] ) && [ ${check_mol2} != "N" ] ;then
    result_check=`python ${path_extra_metascreener}/used_by_metascreener/check_protein_mol2.py $target`
    if [ "${result_check}" != "" ];then
        echo -e "\n${result_check}\n"
        read -p "Press enter to continue"
    fi
  fi
fi


isEmpty "$num_per_job" 				"-j Not indicated number of jobs"
isEmpty "$protocolP" 				"-prp Not indicated protocol for convert target"
isEmpty "$protocolL" 				"-prl Not indicated protocol for convert querie or queries"

if [ ! -f "${path_login_node}techniques/SLTechnique${option}.sh" ];then
	txtErrror="-o ${option} option does not exist"
	f_help
fi

valid_option=false
OLD_IFS=${IFS}
IFS=',' read -ra ADDR <<< "$optionsLanz"
for i in "${ADDR[@]}"; do
    if [[ "${i}" == "${option}" ]];then
        valid_option=true
    fi
done
IFS=${OLD_IFS}
if [[ $valid_option == false ]];then
    txtErrror="Error option ($option) not valid for $software"
    f_help
fi

validate_ext_query
OpcionesExtras
verifyXYZ
find_name_job


debugB "_________________________________________Input Data________________________________________"
debugB ""
debugB "verifiInputData.sh: Mem: $mem"
debugB "verifiInputData.sh: cores: $cores"
debugB "verifiInputData.sh: time_experiment: $time_experiment"
debugB "verifiInputData.sh: x: $x"
debugB "verifiInputData.sh: y: $y"
debugB "verifiInputData.sh: z: $z"
debugB "verifiInputData.sh: grid: $grid"
debugB "verifiInputData.sh: name_target: $name_target"
debugB "verifiInputData.sh: ext_target: $ext_target"
debugB "verifiInputData.sh: name_query: $name_query"
debugB "verifiInputData.sh: ext_query: $ext_query"
debugB "verifiInputData.sh: Nomjob: $name_job"
debugB "verifiInputData.sh: Error: $error"
debugB ""


