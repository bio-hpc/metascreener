#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import subprocess
from add_paths import *
add_paths()

F_CONFIGHOLDER = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))+"/analyze_results/Get_histogram/ConfigHolder.py"
VISUALIZE_QUERY = "lines"
from interactions_colors import COLORS_INTERACTIONS
generate_cube = os.path.dirname(__file__)+"/generate_cube_pymol.py"


def get_type_energy(eng, n_e):
    lst_int = []
    if eng in COLORS_INTERACTIONS:
        lst_int.append("######")
        for k, v in COLORS_INTERACTIONS[eng].items():

            if k == 'color':
                lst_int.append("cmd.color('{}', '{}') ".format(v, n_e))
            else:
                lst_int.append("cmd.set('{}', '{}', '{}') ".format(k, v, n_e))
        lst_int.append("######")

        return lst_int
    else:
        print("ERROR: interaction: " + eng)
        exit()


def draw_energy(energy, n_lines):
    lst_aux = []
    aux = energy.split("|")
    point_prot = aux[len(aux)-1]
    point_lig = aux[len(aux)-2]
    lst_aux.append("pseudoatom tmp, pos=[ "+point_lig+" ]")
    lst_aux.append("pseudoatom tmp_2, pos=[ " + point_prot + " ]")
    lst_aux.append("cmd.distance('"+n_lines+"', 'tmp', 'tmp_2')")
    lst_aux.append("cmd.delete('tmp')")
    lst_aux.append("cmd.delete('tmp_2')")
    return  lst_aux


def paint_scores(table_scores):
    name_target = os.path.splitext(os.path.basename(protein))[0]

    lst = []
    for name_energy, energies in table_scores['interactions_groups'].items():
        res = ""
        _, _, n_lines = get_names_groups(name_energy)
        for i in energies['interactions']:
            lst = lst +draw_energy( i, n_lines)
            aux = i.split("|")
            res += aux[0]+" and " + name_target + " and chain " + aux[2] + " or resi "

        res = res[:-8]
        lst = lst + get_type_energy(name_energy, n_lines)
        n_group, n_sticks, n_lines = get_names_groups(name_energy )
        lst.append("cmd.create('" + n_sticks + "', 'resi  " + res + "')")
        lst.append("cmd.label('''(name CA+C1*+C1' and (byres(" + n_sticks +
                    ")))''','''\"%s-%s\"%(resn,resi)''') ")
        lst.append("util.cba(13,\"" + n_sticks + "\",_self=cmd)  ")
        lst.append("cmd.hide(\"surface\", \""+n_sticks+"\") ")
        lst.append("cmd.show('"+VISUALIZE_QUERY+"', '" + n_sticks + "')")
        lst.append("group " + n_group + " , " + n_sticks + " " + n_lines + " ")
        lst.append("cmd.disable('" + n_group + "')")
    return lst


def get_names_groups( name_energy):
        n_group = name_energy + "-" + name_lig
        n_stick = "stick-"+name_energy + "-" + name_lig
        n_lines = "lines-"+name_energy + "-" + name_lig
        return n_group, n_stick, n_lines


def help():
    print("Error parameters")
    print("1 ligand path")
    print("2 protein path")
    print("3 energy json")
    print("4 interactions json")

    exit()


if len(sys.argv) <= 3 or len(sys.argv) >= 6:
    help()

ligand = sys.argv[1]
protein = sys.argv[2]
compoundScore = sys.argv[3]

	
json_interactions = None

if len(sys.argv) >= 5:
	interactions = sys.argv[4]
	if os.path.isfile(interactions):
	    with open(interactions, 'r') as f:
	        json_interactions = json.load(f)

name_lig, ext_lig = os.path.splitext(os.path.basename(ligand))
print("#\n# {} \n#".format(name_lig))

pml = []
#
#   Add Ligand
#

pml.append("cmd.load('{0}', '{1}')\ncmd.show_as('sticks', '{1}')".format(ligand, name_lig))

#
#
#   Energies plip
#
str_interactions=""
if json_interactions:
    aux = paint_scores(json_interactions)
    pml = pml + aux
    for name_energy, energies in json_interactions['interactions_groups'].items():
        n_group, _, _ = get_names_groups(name_energy)
        str_interactions += n_group + " "
    
pml.append("cmd.group('{0}','{1} {2}')\n".format(name_lig + " " + str(compoundScore), name_lig, str_interactions))
for i in pml:
    print(i)
