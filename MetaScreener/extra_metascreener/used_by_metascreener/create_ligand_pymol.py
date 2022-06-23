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


def get_cube_pymol(json_simulation):
    if 'size_grid' in json_simulation:
        size_grid_x = int(json_simulation['size_grid'].split(",")[0])
        if size_grid_x > 0:
            cmd = "{} {} {}::{}::{} {} ".format(
                PYTHON_RUN,
                generate_cube,
                float(json_simulation['coords'][0]),
                float(json_simulation['coords'][1]),
                float(json_simulation['coords'][2]),
                float(json_simulation['size_grid'].split(",")[0]))        
            return subprocess.check_output(cmd, shell=True).decode("utf-8")
    return ""


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


def paint_scores(table_scores, json_simulation ):
    name_target = os.path.splitext(os.path.basename(json_simulation['file_ori_target']))[0]

    lst = []
    for name_energy, energies in table_scores['interactions_groups'].items():
        res = ""
        _, _, n_lines = get_names_groups(name_energy, json_simulation)
        for i in energies['interactions']:
            lst = lst +draw_energy( i, n_lines)
            aux = i.split("|")
            res += aux[0]+" and " + name_target+" and chain " + aux[2] + " or resi "

        res = res[:-8]
        lst = lst + get_type_energy(name_energy, n_lines)
        n_group, n_sticks, n_lines = get_names_groups(name_energy, json_simulation )
        lst.append("cmd.create('" + n_sticks + "', 'resi  " + res + "')")
        lst.append("cmd.label('''(name CA+C1*+C1' and (byres(" + n_sticks +
                    ")))''','''\"%s-%s\"%(resn,resi)''') ")
        lst.append("util.cba(13,\"" + n_sticks + "\",_self=cmd)  ")
        lst.append("cmd.hide(\"surface\", \""+n_sticks+"\") ")
        lst.append("cmd.show('"+VISUALIZE_QUERY+"', '" + n_sticks + "')")
        lst.append("group " + n_group + " , " + n_sticks + " " + n_lines + " ")
        lst.append("cmd.disable('" + n_group + "')")
    return lst


def get_names_groups( name_energy, json_simulation):
        n_group = name_energy + "-" + json_simulation['file_name']
        n_stick = "stick-"+name_energy + "-" + json_simulation['file_name']
        n_lines = "lines-"+name_energy + "-" + json_simulation['file_name']
        return n_group, n_stick, n_lines


def help():
    print("Error parameters")
    print("1º ligand path")
    print("2º energy json")
    print("3º interations json")
    print("4º num Cluster")
    print("5º grid [ 0 | 1 ]")
    print("6º profile")

    exit()


if len(sys.argv) != 7:
    help()

if not os.path.isfile(sys.argv[2]): # or not os.path.isfile(sys.argv[3]):
    help()

ligand = sys.argv[1]
simulation_json = sys.argv[2]
interactions = sys.argv[3]
num_site = sys.argv[4]
grid = sys.argv[5]
profile = sys.argv[6]
json_interactions = None

if os.path.isfile(interactions):
    with open(interactions, 'r') as f:
        json_interactions = json.load(f)

if simulation_json:
    with open(simulation_json, 'r') as f:
        json_simulation = json.load(f)
name_lig, ext_lig = os.path.splitext(os.path.basename(ligand))
print("#\n# {} \n#".format(name_lig))
json_simulation['file_name'] = name_lig
pml = []
#
#   Add Ligand
#



pml.append("cmd.load('./{0}', '{1}')\ncmd.show_as('sticks', '{1}')".format(ligand, name_lig ) )



#
#   Generate Grid
#
if grid == "1" and profile != "UNCLUSTERED_BD":
    pml.append("Gr{1} = {0}\ncmd.load_cgo(Gr{1}, 'Gr{1}')\ncmd.hide('cgo')".format(get_cube_pymol(json_simulation).replace("\n", ""), num_site))


#
#
#   Energies plip
#
str_interactions=""
if json_interactions:
    aux = paint_scores(json_interactions, json_simulation)
    pml = pml + aux
    for name_energy, energies in json_interactions['interactions_groups'].items():
        n_group, _, _ = get_names_groups(name_energy, json_simulation)
        str_interactions += n_group + " "

if ( 'global_score_qu' in json_simulation and json_simulation['global_score_qu'] != "" and json_simulation['global_score_qu'] != 0 ):
	g_score="global_score_qu"
elif ( 'global_score_md' in json_simulation and  json_simulation['global_score_md'] != "" and json_simulation['global_score_md'] != 0 and json_simulation['global_score_md'] != "0"):
	g_score="global_score_md"
else :
	g_score="global_score"
score = round(float(json_simulation[g_score]), 2)

if json_simulation['option'] == "BD" and profile != "UNCLUSTERED_BD":
    cl_group = 'CL_{} {}'.format(num_site, score, 3)
    pml.append("cmd.group('{0}','Gr{3}  {1} {2}'  )\n".format(
        cl_group, json_simulation['file_name'], str_interactions, num_site))

elif json_simulation['option'] == "BD" and profile == "UNCLUSTERED_BD":
    pml.append("cmd.group('{0}','{1} {2}'  )\n".format(
        score, json_simulation['file_name'], str_interactions))
    
elif json_simulation['option'] == "VS":
    pml.append("cmd.group('{0}','{1} {2}'  )\n".format(json_simulation['file_name'] + " " + str(score),
                                                        json_simulation['file_name'], str_interactions))

for i in pml:
    print(i)


