#!/usr/bin/env bash
#lanzTechnique:BD - Blind Docking

funcionBlindDocking()
{

	numFicheros=`python ${path_extra_metascreener}used_by_metascreener/standar_file_coords.py ${CWD}${target} |grep -v "##" |grep ${bd_atom_default} |wc -l`
	x=0
	y=0
	z=0
	numAminoacdo=0
	send_jobs

}
source ${path_login_node}lanza_job.sh

funcionBlindDocking


