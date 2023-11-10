#!/usr/bin/env bash
#
#   Author: Jorge de la PeÃ±a GarcÃ­a
#   Author: Carlos MartÃ­nez CortÃ©s
#   Email:  cmartinez1@ucam.edu
#   Description: Parameters of metascreener
# ______________________________________________________________________________________________________________________


#______________________________________________________________________________________________________________________
#
#			Read template with posible parameters
#_________________________________________________________________________________________________________________________
read_file_template()
{
	source ${pathSL}special_params.sh
	read_template_params $software

	if [ "$error" == "0" ];then

		for i in `seq 1 $contadorFile`;do
			error=12
			IFS='::' read -ra ADDR <<< "${file[$i]}"
			if [ "$1" == "${ADDR[4]}" ];then
				if [ "${ADDR[2]}" == "Y" ];then
					error=0		
					allComand=`echo "$allComand" |sed -e "s,${ADDR[4]} $2,,g"`
					optAdicionals="$optAdicionals ${ADDR[4]} $2"
					shift
					break
				else
					error=0
					if [[ "$1" != \-* ]];then
						error=12
					fi
					allComand=`echo "$allComand" |sed -e "s,${ADDR[4]},,g"`
					optAdicionals="$optAdicionals ${ADDR[4]}"
					break
				fi
			fi
		done
	fi

}
function empty_variable()
{
	if [ -z $2 ];then
		val="N/A"
	else
		val=$2
	fi
    if [ -z "$1" ];then
        echo $val
    else
        echo $1
    fi
}


if [ -z $CWD ];then
	 CWD=${PWD}/
fi

if [ -z "${name_job}" ];then
    name_job=""
fi

folder_experiment=`empty_variable $folder_experiment`

scoreCorte=`empty_variable $scoreCorte 0`
numPoses=`empty_variable $numPoses 1`
torsion=`empty_variable $torsion 12`
numAminoacdo=`empty_variable $numAminoacdo 0`


if  [ -z "$optAdicionals" ];then
	optAdicionals=""
fi
if [ -z "$allComand" ];then
    allComand="$0 $@"
fi


# Default values

nodos=`empty_variable $nodos 1` 				#	One node by default
debug=`empty_variable $debug -1`

name_target=`empty_variable $name_target no_target `       #	Target's name without path and extension
name_query=`empty_variable $name_query`         # Query's	name without path and extension
check=`empty_variable $check`
proteinName=`empty_variable $proteinName`
flex=`empty_variable $flex`				        #	flexibility: only for vina
flexFile=`empty_variable $flexFile`
secuencial=`empty_variable $secuencial `        #	Execute without send jobs to cluster
outJob=`empty_variable $outJob `
histograms=`empty_variable $histograms `        #	Generate histograms or not
time_hist=`empty_variable $time_hist `			    # Maximum time of histogram job
grid=`empty_variable $grid `
grid_bin=`empty_variable $grid_bin `            #	Precalculated grid
cores=`empty_variable $cores `	                # Number of cores
mem=`empty_variable $mem `                      # Memory to use
mem_hist=`empty_variable $mem_hist `            # Memory to use in get_histogram
time_job=`empty_variable $time_job `
versionHelp=`empty_variable $versionHelp`
renice=`empty_variable $renice`
GPU=`empty_variable $GPU`                       #	Use GPU or not
time_experiment=`empty_variable $time_experiment`       #	Maximum docking time
specialCommand=`empty_variable $specialCommand`
ext_query=`empty_variable $ext_query`           # Query's extension
ext_target=`empty_variable $ext_target`         # Target's extension
resName=`empty_variable $resName`
num_amino_acid=`empty_variable $num_amino_acid 0`
gridSizeX=`empty_variable $gridSizeX`
gridSizeY=`empty_variable $gridSizeY`
gridSizeZ=`empty_variable $gridSizeZ`
queue=`empty_variable $queue`		   	            # Partition for the resource allocation
chain=`empty_variable $chain`                   #	Target's chain
lanzTimeOut=`empty_variable $lanzTimeOut`       #	Launch timeout
email=`empty_variable $email`                   # Send results to email (doesn't work in all clusters)
number_execution=`empty_variable $number_execution -1`
bd_exhaustiveness=`empty_variable $bd_exhaustiveness  1` # Exhaustiveness in BD
bd_atom_default=`empty_variable $bd_atom_default CA`
target=`empty_variable $target no_target`
target_pdb=`empty_variable $target_pdb no_target`          # Target in pdb format
mode_test=`empty_variable $mode_test`           # Test Metascreener with a simple BD
check_mol2=`empty_variable $check_mol2`         # Don't check mol2 protein residues
project=`empty_variable $project`
rf=`empty_variable $rf 500`
rb=`empty_variable $rb 50`

#
#	Set parameters
#
while (( $# ))
 do

    if [[ "$1" == \-[a-z]* ]] || [[ "$1" == \-[A-Z]* ]] || [[ "$1" == \-\-[a-a]* ]] || [[ "$1" == \--[A-Z]* ]];then
	   case `printf "%s" "$1" | tr '[:lower:]' '[:upper:]'`  in
			-X )  x=$2;;			# Center position x
			-Y )  y=$2;;			# Center position y
			-Z )  z=$2;;			# Center position z
			-D )  folder_experiment=${2%/}/;;
			-T )  target=$2;;
			-PDB ) target_pdb=$2;;
    	-Q )  query=$2;;
			-SE) secuencial=$2;;
			-FX) flex=$2;;
			-FL) flexFile=$2;; 		# To indicate the previously generated flexibility file (prepare_flexreceptor4.py)
			-DY)  dinamyc="-dy";;	# To indicate dynamic flexibility, there must be a BD previously (Vina)
			-DD)  dirDinamyc=$2;;	# To indicate flexibility's directory
			-FI) ficheroBD=$2 ;;  # Flexibility file
			-NC )  numPoses=$2 ;;
			-AN)  t=$2;;
			-HI) histograms="y";;
			-THI) time_hist=$2;;
	    -MHI) mem_hist=$2;;
			-O )option=`echo $2 | awk '{print toupper($0)}'`   ;;			# BD | VS
			-S )  software=`echo $2 | awk '{print toupper($0)}'`;;
			-PN) proteinName=$2;;
			-J )  num_per_job=$2;;
			-DE ) debug=$2;; 		# Debug mode
			-V  ) versionHelp="ve";;
      -NN )  nodos=$2;;
			-EM ) email=$2;;
	    -RF ) rf=$2;;
      -RB ) rb=$2;;
			## Internal use
			-RE) resName=$2;;
			-NT) name_target=$2;;
			-O ) option=$2;;
			-I ) confAdicionalI=$2;;
			-F ) confAdicionalF=$2;;
			-C ) CWD=$2;;
			-NJ) name_job=$2;;
			-BE) bd_exhaustiveness=$2;;
			-NA) num_amino_acid=$2;;
			-CH) chain=$2;;
			-CK) check="ck";;
			-TR) torsion=$2;;
			-TD) time_experiment=$2;;
			-NI) renice=$2;;
			-CO) cores=$2;;
			-GPU) GPU=1;;
			-SC ) scoreCorte=$2;;		# Score threshold
			-MM ) mem=$2;;
			-EJ ) number_execution=$2 ;;
			-NQ ) name_query=$2;;
			-IN ) ini=$2;;			    # Start for VS in files
			-FN ) fin=$2;;      		# Stop for VS in files
			-SA ) outJob=$2;;
			-TJ ) time_job=$2;;
			-LTO ) lanzTimeOut=$2;;
			-PJ) project=$2;;
			-QU  ) queue=$2;;
			-GRID )grid=$2;;
		  -G ) grid_bin=$2;;
			-BDA ) bd_atom_default=$2;;
			-EXP ) ext_target=$2;;
			-EXL ) ext_query=$2;;
			-GX ) gridSizeX=$2;;
 	    -GY ) gridSizeY=$2;;
      -GZ ) gridSizeZ=$2;;
      -PROFILE)  profile=$2;;
			-TEST) mode_test="Y";;
			-h|-H ) f_help $2;;
	    -CHK ) check_mol2="N";;

			*)
        path_login_node=${pathSL}
				read_file_template $1 $2
				paraMError="para option $1"

	    esac
	fi
  shift
done

