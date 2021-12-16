#!/usr/bin/env bash
#
# Author: Jorge de la Peña García
# Author: Carlos Martínez Cortés
#	Email: 	cmartinez1@ucam.edu
#	Description: 	Create the folder of experiment
#_________________________________________________________________________________________________________________________________________
asigVar()
{
	source ${path_login_node}/folders_experiment.sh
}

create_dirs()
{
	asigVar
	for dir_name in "${arrayFolders[@]}";
	do
		if [ ! -d ${dir_name} ]; then
			mkdir ${dir_name}
		fi
	done
}
#__________________________________________________________________________________________________________________________________________
#
#	Name folder like ${option}_${software}_${name_target}_${name_query}...
#__________________________________________________________________________________________________________________________________________
search_directory()
{

	folder_experiment=${PWD}/${option}_${software}_${name_target}_${name_query}
	if [ "$x" == "0" ] && [ "$y" == "0" ] && [ "$z" == "0" ];then
		if [ "$GPU" != "N/A" ];then	
			folder_experiment=${folder_experiment}_GPU
		else
			folder_experiment=${PWD}/${option}_${software}_${name_target}_${name_query}
		fi
	else
		folder_experiment=${folder_experiment}_${x}_${y}_${z} 	  				#
	fi 

	folder_experiment=${folder_experiment}_${fecha}/
	
}
existeDirectory()
{
	if [ -d $folder_experiment ];then
		while [ "$input" != "Y" ] && [ "$input" != "y" ] && [ "$input" != "N" ] && [ "$input" != "n" ] && [ "$input" != "zz" ] ; do
			echo "CreateFile: The directory ${folder_experiment} already exists. To continue you must delete this directory. Do you want to delete it? "
			echo "(Y/y) Delete folder"
			echo "(N/n) Exit"
			read  input
		done
		if [ "$input" == "Y" ] || [ "$input" == "y" ];then
			rm -r $folder_experiment
			create_dirs
		elif [ "$input" == "n" ] || [ "$input" == "N" ];then
			exit
		elif [ "$input" == "zz" ] || [ "$input" == "ZZ" ];then
			asigVar
		fi
	else
		create_dirs
	fi
}

if [ `echo  $target |grep _ |wc -l` != "0" ] && [ "$option" == "BDVS" ];then
	echo "ERROR target's file cannot have underscores _ "
fi
if [ `echo  $query |grep _ |wc -l` != "0" ] && [ "$option" == "BDVS" ];then
	echo "ERROR query's file cannot have underscores _ "
fi


if [ "$software" == "GRN" ];then
	if [ "$folder_experiment" == "N/A" ];then
		echo "You must specify the test directory with the -d parameter in order to continue"
		exit
	fi
fi

if [ "$folder_experiment" != "N/A" ];then

	folder_experiment=${PWD}/$folder_experiment
	create_dirs
else

	search_directory
	existeDirectory
fi		
debugB "_________________________________________Directories________________________________________"
debugB ""
for dir_name in "${arrayFolders[@]}";do
		debugB "create_dirs.sh:  $dir_name"
done



debugB ""
