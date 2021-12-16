#!/bin/bash

#
#	Folders of experiment
#
folder_out_jobs=${folder_experiment}jobs_out/
folder_templates_jobs=${folder_experiment}jobs/
folder_jobs_done=${folder_experiment}jobs_done/
folder_grid=${folder_experiment}grids/
folder_out_ucm=${folder_experiment}soft_out/
folder_molec=${folder_experiment}molecules/
folder_energies=${folder_experiment}energies/

arrayFolders=( $folder_experiment $folder_out_jobs $folder_templates_jobs $folder_jobs_done $folder_grid $folder_out_ucm $folder_molec $folder_energies )
