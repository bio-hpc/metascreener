#!/bin/bash
name_metascreener="./ms.sh"
path_analize_results="MetaScreener/analyze_results/"
path_external_sw="MetaScreener/external_sw/"
printHelpAux(){
	a=`echo $1 | sed 's/\\\t/\ /g'`
	printf "${GREEN} %8s ${CYAN}%-25s${NONE} %-30s \n" "$a" "$2" "$3"
}
printGlobalHelp(){
	printf "${GREEN} %6s ${CYAN}%5s${BLUE}%s ${NONE}%-s \n" "-$1 )" "[ $2 ]" "$3" "$4"
}
printTitle()
{
	title=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzNombre" | cut -d : -f 2`
	echo -e "${BLUE}\t\t\t\t\t ${title} ${NONE}"
	echo -e "${CYAN}-------------------------------------------------------------------------------------------------------${NONE}"

}
printTitletechnique()
{
	echo -e "${BLUE}\t\t\t\t\t $1 ${NONE}"
	echo -e "${BLUE}\t\t\t\t\t ${title} ${NONE}"
	echo -e "${CYAN}-------------------------------------------------------------------------------------------------------${NONE}"

}
printExampleTechnique()
{
	echo""
	echo -e "${YELLOW}Example: $1${NONE}"
	echo ""
	echo ""
}

printOpTchnique()
{
	cad="["
	for i in `ls ${pathSL}templateParams/*`; do
		ext=`cat $i |grep "#lanzOptions" | awk -F: '{print $2}'`
		if [[ $ext == *"$option"* ]]; then
			aux=`cat $i |grep "#LanzNombre" | awk -F: '{print $2}' |awk -F- '{print $1}'`
				cad="${cad} ${aux}|"
		fi

	done

	cad=${cad%?}

	cad="$cad]"
	printf "${GREEN} %8s ${CYAN}%-135.135s${NONE}\n" "-s|-S" "$cad"

}
printManual()
{
	echo -e "${GREEN}Manual: ${BLUE}$1${NONE}"
}
printExample()
{

	printHelpAux "-j" "[    ]" "Number of jobs for the test."
	printHelpSwexclusivo
	echo ""
	printHelpAux "Default options"

	extensionesProt=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzExtensionProtQ" | cut -d : -f 2`
	extensionesLig=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzExtensionligB" | cut -d : -f 2`
	cores=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzCores" | cut -d : -f 2`
	time_experiment=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzTimeExecution" | cut -d : -f 2`
	grid=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzGrid" | cut -d : -f 2`
	mem=`cat ${pathSL}templateParams/template${option}.txt |grep "#LanzMem" | cut -d : -f 2`
	sizeGridX=`cat ${pathSL}templateParams/template${option}.txt |grep "#lanzSizeGridX" | cut -d : -f 2`
	sizeGridY=`cat ${pathSL}templateParams/template${option}.txt |grep "#lanzSizeGridY" | cut -d : -f 2`
	sizeGridZ=`cat ${pathSL}templateParams/template${option}.txt |grep "#lanzSizeGridZ" | cut -d : -f 2`

	printHelpAux "Receptor/Query Extension:" ${extensionesProt} ""
	printHelpAux "ligands Extension:" ${extensionesLig} ""
	printHelpAux "Grid:" ${grid}
	printHelpAux "Cores:" ${cores}
	printHelpAux "RAM:" ${mem}
	if [ $sizeGridX != 0 ];then
		printHelpAux "SizeGridX: " ${sizeGridX}" Å"
		printHelpAux "SizeGridY: " ${sizeGridY}" Å"
		printHelpAux "SizeGridZ: " ${sizeGridZ}" Å"
	fi

	echo""

	echo -e "${YELLOW}Example: $1${NONE}"
	echo ""
	echo ""
}
#___________________________________________________________________________________
#
#	Lee las posibles tecnicas BD, VS
#___________________________________________________________________________________
function readTechniquesSW (  )
{
	techniques=""
	for i in $(ls $1);do

		i="${i%.*}"
		i="${i##*$2}"
		techniques=${techniques}" | "${i}

	done
	techniques="[ ${techniques:2:${#techniques}-1} ]"
	echo $techniques
}

function getOptions( )
{
	opt=`cat ${pathSL}templateParams/template${option}.txt |grep $1 | cut -d : -f 2`
	opt=`echo $opt | sed s/,/" | "/g`
	opt="[ "$opt" ]"
	echo $opt

}

printOp()
{
	printTitle
	printHelpAux "-t"  "`getOptions "\#LanzExtensionProtQ"`"  "Receptor or target's file."
	printHelpAux "-q"  "`getOptions "\#LanzExtensionligB"`"  "Ligand's file or query's directory."
	printHelpAux "-s" "[ $option ]"   "Software."
	printHelpAux "-o" "`getOptions "\#lanzOptions"`"   "Options available."
	if [ -z `cat ${pathSL}templateParams/template${option}.txt |grep "\LanzCoordX" | cut -d : -f 2` ];then
		printHelpAux "-x|-X" "[  ]"  "X coordinate of docking (only VS)."
		printHelpAux "-y|-Y" "[  ]"  "Y coordinate of docking (only VS)."
		printHelpAux "-z|-Z" "[  ]"  "Z coordinate of docking (only VS)."
	fi

}

printOpOM()
{
        printTitle
        printHelpAux "-t"  "[ number ]"  "Number of conformations (optional)."
        printHelpAux "-q"  "`getOptions "\#LanzExtensionligB"`"  "Ligand's file or query's directory."
        printHelpAux "-s" "[ $option ]"   "Software."
        printHelpAux "-o" "`getOptions "\#lanzOptions"`"   "Options available."
}

printHelpSwexclusivo()
{

		if [ -z $software ];then
			echo ""
			printHelpAux "Extra options"
			path_login_node=$pathSL
			source ${pathSL}special_params.sh
			read_template_params $option
			for i in `seq 1 $contadorFile`;do
				IFS='::' read -ra ADDR <<< "${file[$i]}"
				printHelpAux "(${ADDR[0]})\t" "${ADDR[4]}" "${ADDR[6]}"
			done
		fi

}
echo ""
option=`echo "$1" | tr '[:lower:]' '[:upper:]'`

cat ${pathSL}logo_metascreener.txt
echo -e "${GREEN}Help: $option ${NONE}"

if [  -z "$option" ];then
	echo ""
	printf "\t${CYAN}%s${NONE} \n"  "[ O=optional, D=Depends, N=Necesary ]" 
	echo ""
	echo -e "${PURPLE}Global Options${NONE} "
	echo -e "${PURPLE}____________________________________________________${NONE} "
	printGlobalHelp "d" "O" "" "Folder where test data will be saved."
	printGlobalHelp "t" "D" "" "Receptor or protein target's file."
	printGlobalHelp "pdb" "O" "" "Receptor or target's file in PDB format (Useful when PLIP interactions show any problems)."
	printGlobalHelp "q" "N" "" "Ligand's file or query's directory."
	printGlobalHelp "o" "N" "" "Technique `readTechniquesSW ${pathSL}techniques/ SLTechnique`."
	printGlobalHelp "s" "N" "" "Available Software `readTechniquesSW ${pathSL}templateParams/ template`*."
	echo -e "            * All software requires a license (except AD and GN). You must also put the executables in their MetaScreener/external_software/ directories and give them execution permissions.${NONE}"
	printGlobalHelp "se" "O" " [ Y | N ]" "Sequential Mode Y, queue manager N. (Default N)."
	printGlobalHelp "de" "O" " [ 1-10 ]" "Debug mode range [1-10]. (default 0)."
	printGlobalHelp "hi" "O" "" "At the end of calculations, generate graphs and PyMOL session."
	printGlobalHelp "thi" "O" "" "Time allocated to generate graphs and PyMOL session (Default 24:00:00). Only works if -hi y."
	printGlobalHelp "mhi" "O" "" "Memory, in GB, reserved to generate graphs and PyMOL session (Default 2G). Only works if -hi y."
	printGlobalHelp "v" "O" "" "Show MetaScreener version."
	printGlobalHelp "h" "O" " [ Opt | SW ]" "Show help or specific help for a technique or a program."
	printGlobalHelp "h" "O" " [ allsw ]" "Show all programs (not all software work)."
	printGlobalHelp "h" "O" " [ alltc ]" "Show all techniques (not all techniques work)."
	printGlobalHelp "h" "O" " [ protocols ]" "Show all protocols to prepare proteins and ligands."
	printGlobalHelp "em" "O" "" "Send email when all jobs are finished. (only with -hi y parameter)."
	printGlobalHelp "test" "O" "" "Launch a quick test with default parameters. You can select option (-o) and software (-s) (By default BD AD in sequential with debug)."
	printGlobalHelp "rb" "O" "" "Number of files saved as bestScore in VS. Default (50)."
	printGlobalHelp "rf" "O" "" "Number of files saved in VS. Default (500)."
	
	echo ""
	echo -e "${PURPLE}Queue Manager Options${NONE}"
	echo -e "${PURPLE}____________________________________________________${NONE}"
	printGlobalHelp "qu" "N" "" "Set a specific partition for resource allocation. We recommend the available partition with more idle nodes (Check with \"sinfo -s\")."
	printGlobalHelp "pj" "O" "" "Set a project or an account for the jobs."
	printGlobalHelp "td" "O" "" "Set execution time of a program. Default ./ms.sh -h software (Not all programs have this option)."
	printGlobalHelp "tj" "O" "" "Time allocated to the job. Default multiply -td by runs in a job. Format 00:05:00."
	printGlobalHelp "mm" "O" "" "Memory reserved for a job, in GB."
	printGlobalHelp "j" "O" "" "Number of jobs that will be sent to the supercomputer."
	printGlobalHelp "ni" "O" "" "Priority of the job managers, Sbatch [0-10000] being 10000 the lowest. Qsub [-1024- + 1023] default or higher priority, the higher the number."
	printGlobalHelp "co" "O" "" "Number of cores for execution. Important: can't reserve more cores than those contained in the node."
	printGlobalHelp "nn" "O" "" "Number of nodes for execution."
	printGlobalHelp "gpu" "O" "" "Number of GPUs for execution. Only supported for GN. Important: can't reserve the resources if the supercomputer doesn't have them."
	printGlobalHelp "nj" "O" "" "Name of the job."
	
	echo ""
	echo -e "${PURPLE}Docking Options${NONE}"
	echo -e "${PURPLE}____________________________________________________${NONE}"
	printGlobalHelp "nc" "O" "" "Number of conformations for output docking (only for VS)."
	printGlobalHelp "x" "D" "" "X coordinate of the center of the grid."
	printGlobalHelp "y" "D" "" "Y coordinate of the center of the grid."
	printGlobalHelp "z" "D" "" "Z coordinate of the center of the grid."
	printGlobalHelp "an" "O" "" "Size of the cube when using BDC."
	printGlobalHelp "g" "O" "" "Grid .bin for VS with LF."
	printGlobalHelp "gx" "O" "" "Size X of grid for some docking programs."
	printGlobalHelp "gy" "O" "" "Size Y of grid for some docking programs."
	printGlobalHelp "gz" "O" "" "Size Z of grid for some docking programs."
	printGlobalHelp "be" "O" "" "Exhaustiveness in BD. Default (1)."
	printGlobalHelp "bda" "O" "" "Type of atom to filter for Blind docking. Default (CA)."
	printGlobalHelp "chk" "O" "" "Don't check mol2 protein's residues."
	
	echo ""
	echo -e "${PURPLE}Similarity Options${NONE}"
	echo -e "${PURPLE}____________________________________________________${NONE}"
	printGlobalHelp "sc" "O" "" "Threshold for some similarity programs. Results lower than this score will be deleted."
	echo ""
else
option=`echo "$1" | tr '[:lower:]' '[:upper:]'`

case $option in
	BD)
		printTitletechnique "Blind Docking"
		printOpTchnique
		printHelpAux "-o|-O" "[ BD ]" "Option (VirtualScreening VS o BlindDoking BD)."
		printExampleTechnique "Example: ${name_metascreener} -t targets/test/1le0.pdbqt -s AD -q queries/test/GLA.pdbqt -o BD -j 5";;

 	VS)
		printTitletechnique "Virtual Screening"
		printHelpAux "-t|-T" "[ mol2 | pdbqt ]"  "Receptor to check."
		printHelpAux "-q|-Q" "[ mol2 | pdbqt ]"  "Ligand to check."
		printOpTchnique
		printHelpAux "-o|-O" "[ VS ]" "Option (VirtualScreening vs)"
		printHelpAux "-x|-X" "[  ]"  "X coordinate of docking"
		printHelpAux "-y|-Y" "[  ]"  "Y coordinate of docking"
		printHelpAux "-z|-Z" "[  ]"  "Z coordinate of docking"
		printExampleTechnique "${name_metascreener} -t targets/1DFC_rec.mol2 -q queries/10-lig-zinc-mol2/ -o VS -s FB -j 1 -x 34.719 -y 108.24 -z 20.85";;

	LS)
		printOp
		printExample "${name_metascreener} -t targets/PHM_Migrastatin_and_Dorrigocin_FAST.pmz -s LS -q queries/10-lig-zinc/ -o VS -j 2";;
        DC)
          	printOp
          	printExample "${name_metascreener} -t targets/FDB_v10_mol2_name.csv -s DC -q queries/10-lig-zinc/ -o VS -j 1";;
	S3)
          	printOp
          	printExample "${name_metascreener} -t queries/ADPF.ser -q queries/ligThomas/ -o VS -s S3 -j 10";;	
	AD)
		printOp
		printExample "${name_metascreener} -t targets/test/1le0.pdbqt -s AD -q queries/test/GLA.pdbqt -o BD -j 5 "
		echo -e "${GREEN}prepare receptor: 2 ways"
		
		echo -e "path=MetaScreener/external_ws/mgltools_x86_64Linux2_latest/"
		echo ""
		echo -e "-path+/bin/adt 	GUI Interactive GUI for creating a receptor."
		echo -e "-path+/bin/pythonsh path+MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py	Command Line Creates a receptor from a PDB file 
with a protein-ligand complex."
		echo ""
		echo -e "${GREEN}Manual: ${BLUE}http://autodock.scripps.edu/faqs-help/how-to/how-to-prepare-a-receptor-file-for-autodock4"
		echo -e "${YELLOW}Example: ${path}bin/pythonsh ${path}MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py -r receptor[.pdb|mol2] -o 
receptor_out.pdbqt -A checkhydrogens${NONE}"
		echo ""
		echo -e "${GREEN}prepare ligand:"
		echo -e "${YELLOW}Example: ${path}bin/pythonsh ${path}MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py -q ligand[pdb|mol2] -o 
ligand_out.pdbqt -A 'hydrogens' -U \'\'${NONE}"
		echo ""
		;;
	GN)
		printOp
		printExample "${name_metascreener} -t targets/test/1le0.pdbqt -s GN -q queries/test/GLA.pdbqt -o BD -j 5 ";;
	LF)
		printOp
		printHelpAux "-pdb"  "[ .pdb ]"  "Receptor or target's file in pdb format (Usesful if plip interactions show any problems)."
		printExample "Example: ${name_metascreener} -t targets/test/1le0.pdbqt -s LF -q queries/test/GLA.pdbqt -o BD -j 5";;
        EO)
                printOp
                printExample "${name_metascreener} -t targets/test/1le0.mol2 -s EO -q queries/test/ -o VS -j 1";;
        RC)
                printOp
                printExample "${name_metascreener} -t targets/test/1le0.mol2 -s RC -q queries/test/ -o VS -j 1";;
        OM)
                printOpOM
                printExample "${name_metascreener} -t 200 -s OM -q queries/test/ -o VS -j 1";;                
	PDBQT)
		printOp
		printExample "Example: ${name_metascreener} -q queries/natural_products_mol2/ -o VS -s PDBQT -j 100"
		;;

	ALLSW)
		for i in `ls ${pathSL}templateParams/*`; do
			swAbrev=`cat $i |grep "#LanzNombre" | awk -F: '{print $2}'|awk -F- '{print $1}'`
			sw=`cat $i |grep "#LanzNombre" | awk -F: '{print $2}'|awk -F- '{print $2}'`
			printHelpAux "$swAbrev" "$sw"
		done
		echo ""
		;;

	ALLTC)
		for i in `ls ${pathSL}techniques/*`; do

			tcAbrev=`cat $i |grep "#lanzTechnique" | awk -F: '{print $2}'|awk -F- '{print $1}'`
			tc=`cat $i |grep "#lanzTechnique" | awk -F: '{print $2}'|awk -F- '{print $2}'`
			printHelpAux "$tcAbrev" "$tc"
		done
		echo ""
		;;

	*)
		printHelpAux "Help not found"
esac
exit
fi
