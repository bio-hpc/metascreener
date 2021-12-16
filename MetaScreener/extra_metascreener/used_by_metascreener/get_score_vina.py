#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Author:   Jorge De La Peña Garcia
#       Author:   Carlos Martínez Cortés
#       Usage:  Generate score with Vina from a protein and a ligand
#       dependencies:
#           MetaScreener/extra_metascreener/used_by_metascreener/convert_to.py
#           MetaScreener/external_sw/autodock/vina
#


import sys
import os
import subprocess
VINA_RUN_SCORE_ONLY = "MetaScreener/external_sw/autodock/vina --score_only --receptor {} --ligand {}"
SCRIPT_CONVERT_TO = "MetaScreener/extra_metascreener/used_by_metascreener/convert_to.py"
PYTHON_RUN = "python"
CONVERT_TO = '{} {} {} {} '

def convert_molecule(file_1, file_2):
    cmd = CONVERT_TO.format(PYTHON_RUN, SCRIPT_CONVERT_TO, file_1, file_2)
    subprocess.check_output(cmd, shell=True)

if len(sys.argv) != 3:
    print("ERROR  Parameters:")
    print("1º Receptor")
    print("1º Ligand")

target, ext_target = os.path.splitext(sys.argv[1])
query, ext_query = os.path.splitext(sys.argv[2])

if ext_target != ".pdbqt":
    convert_molecule(sys.argv[1], target+".pdbqt")

if ext_query != ".pdbqt":
    convert_molecule(sys.argv[2], query+".pdbqt")

query = query + ".pdbqt"
target = target + ".pdbqt"
cmd = VINA_RUN_SCORE_ONLY.format(target, query)
result = subprocess.check_output(cmd, shell=True, executable="/bin/bash")
print (result)

