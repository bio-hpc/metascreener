#!/usr/bin/env bash
#
#   Author: Carlos Martinez Cortes
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

check_technique()
{
  if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
    echo "Enter a technique [ SBVS, LBVS, BD ]"
    read option
    case `printf "%s" "$option" | tr '[:lower:]' '[:upper:]'` in
      SBVS|VS ) option="VS";;
      LBVS ) option="VS";;
      BD ) option="BD";;
      * ) ;;
    esac
    allComand="${allComand} -o ${option}"
  fi
}

check_sw()
{
  if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
    echo "Enter a software [ AD, DC, GN, LF, LS ]"
    read sw
    case `printf "%s" "$sw" | tr '[:lower:]' '[:upper:]'` in
      AD ) software="AD";;
      DC ) software="DC";;
      GN ) software="GN";;
      LF ) software="LF";;
      LS ) software="LS";;
      * ) ;;
    esac
    allComand="${allComand} -s ${software}"
  fi
}

check_squeue()
{
  if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
    echo "Select a partition in your cluster"
    sinfo -s
    read queue
    allComand="${allComand} -qu ${queue}"
    if [ "$project" == "N/A" ] || [  -z "$project" ] ;then
    echo "Enter account (press enter if not required)"
    read project
    allComand="${allComand} -pj ${project}"
    fi
  fi

}

check_querie()
{
  if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
    if [[ ${option} == "BD" ]] || [[ ${software} == "LS" ]] ;then
      echo "Enter query ($extensionesLig)"
      read -e query
    else
      echo "Enter folder with queries ($extensionesLig)"
      read -e query
    fi
    allComand="${allComand} -q ${query}"
  fi
}

check_target()
{
  if [ "$1" == "no_target" ] || [  -z "$1" ] ;then
    echo "Enter target ($extensionesProt)"
    read -e target
    allComand="${allComand} -t ${target}"
  fi
}

check_jobs()
{
  if [ "$1" == "N/A" ] || [  -z "$1" ] ;then
    echo "How many jobs do you want?"
    read num_per_job
    allComand="${allComand} -j ${num_per_job}"
  fi
}

check_histograms()
{
  if [ "$histograms" == "N/A" ] || [  -z "$histograms" ] ;then
    echo "Do you want to make an analysis of the results (pymol session, plip interaction, postview graphs, ...)?"
    read response
    case `printf "%s" "$response" | tr '[:lower:]' '[:upper:]'` in
      Y|YES ) histograms="y"; allComand="${allComand} -hi y";;
      * ) ;;
    esac
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
	if [[ ${option} == "BD" ]] || [[ ${software} == "LS" ]] ;then
		x=0;y=0;z=0;
        fi
	if [ -z $x ] || [ -z $y ] || [ -z $z ];then
	  echo "Enter the x-coordinate for docking."
	  read x
	  echo "Enter the y-coordinate for docking."
	  read y
	  echo "Enter the z-coordinate for docking."
	  read z
	  allComand="${allComand} -x $x -y $y -z $z"
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
			txtError="-s Software does not support that extension "
			f_help
		fi
	else
		txtError="-t Target file does not exist"
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
                txtError="-q You must enter a folder with valid queries for the software"
                f_help
            fi
        fi
	else
		if [ -f "$query" ];then
			extensionLigAux="."${query##*.}
			ext_query=`existInLst "$extensionesLig" "$extensionLigAux"`
			if [ "$ext_query" == "" ];then
				txtError="-s The Software does not support ligand's extension"
				f_help
			fi
		else
			txtError="Querie does not exist"
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

check_technique "$option"
check_sw "$software"
readParams

if [ "$extensionesLig"  != "" ];then
    check_querie "$query"
else
    query="no_query"
fi


if [ "$extensionesProt" != "" ];then
	check_target "$target"
	validateExtProt
	name_target=$(basename $target)
	name_target="${name_target%.*}"
fi
echo ${software}
if [ "${extensionesProt}" == ".mol2" ];then
  if ([ ${software} == "LF" ] || [ ${software} == "FB" ] ) && [ ${check_mol2} != "N" ] ;then
    result_check=`singularity exec --bind ${PWD} ${PWD}/singularity/metascreener.simg python ${path_extra_metascreener}/used_by_metascreener/check_protein_mol2.py $target`
    if [ "${result_check}" != "" ];then
        echo -e "\n${result_check}\n"
        read -p "Press enter to continue"
    fi
  fi
fi

if [ ! -f "${path_login_node}techniques/SLTechnique${option}.sh" ];then
	txtError="-o ${option} option does not exist"
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
    txtError="Error option ($option) not valid for $software"
    f_help
fi

validate_ext_query
OpcionesExtras
verifyXYZ
find_name_job
check_histograms
check_squeue "$queue"
check_jobs "$num_per_job"

if [[ "${profile}" == "" ]];then
  if [[ ${software} == "LS" ]];then
    profile="STANDARD_VS_LS"
	else
	  profile="STANDARD_${option}"
  fi
fi

# Check software
ext_sw=MetaScreener/external_sw/

if [[ ${software} == "GN" ]]; then
  if [[ ! -f "${ext_sw}gnina/gnina" ]]; then
    echo -e "${RED} Error: ${ext_sw}gnina/gnina doesn't exist. Download the executable to this directory, give it execution permissions and try again.${NONE}"
    exit 1
  fi
  
  if [[ ! "${cores%% *}" =~ ^[0-9]+$ ]]; then
    if [[ "${GPU}" != "N/A" ]]; then
      cores=4
    else
      cores=1
    fi
  fi
fi

if [[ ${software} == "LS" ]] ;then
  if [[ ! -f "${ext_sw}ligandScout/iscreen" ]]; then
    echo -e "${RED} Error: ${ext_sw}ligandScout/iscreen doesn't exist${NONE}"
    exit
  fi
fi

if [[ ${software} == "LF" ]] ;then
  if [[ ! -f "${ext_sw}leadFinder/leadfinder" ]]; then
    echo -e "${RED} Error: ${ext_sw}leadFinder/leadfinder doesn't exist${NONE}"
    exit
  fi
fi

if [[ ${software} == "DC" ]] ;then
  if [[ ! -f "${ext_sw}dragon/dragon6shell" ]]; then
    echo -e "${RED} Error: ${ext_sw}dragon/dragon6shell doesn't exist${NONE}"
    exit
  fi
fi


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


