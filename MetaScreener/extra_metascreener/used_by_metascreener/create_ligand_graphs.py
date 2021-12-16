#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import sys

from add_paths import *
add_paths()

from GraphicsGenerator import GraphicsGenerator
from Tools import *
graphicsGenerator = GraphicsGenerator()


def booolean(b):
    if (b.upper() == "TRUE"):
        return True
    elif (b.upper() == "FALSE"):
        return False
    else:
        print ("ERROR param "+b)
        exit()

def help():
    print("Error parameters")
    print("1º energy json")
    print("2º prefix afinities")
    print("3º [ True | false ] graph global")
    print("4º [ True | false ] graph atom")
    print("5º [ True | false ] graph heat_map")
    print ("Si no introduces parametros 3, 4,  5 por defecto son todas")
    exit()


if len(sys.argv) < 3 or len(sys.argv) > 6:
    help()

if not os.path.isfile(sys.argv[1]):
    help()

simulation_json = sys.argv[1]
prefix_simulation = sys.argv[2]
g_global = True if len (sys.argv) < 4 else booolean(sys.argv[3])
g_atom = True if len (sys.argv) < 5 else booolean(sys.argv[4])
g_heat_map = True if len (sys.argv) < 6 else booolean(sys.argv[5])

json_simulation = {}
if simulation_json:
    json_simulation = read_json(simulation_json)
dir_name, basename = os.path.split(simulation_json)
file_name, _ = os.path.splitext(basename)

if g_global:
    out_put ='{}{}_global'.format(prefix_simulation, file_name )
    graphicsGenerator.generate_global_graph(json_simulation['graph_global_field'], json_simulation['graph_global_score'],
                                        json_simulation['graph_global_color'], file_name, out_put)
if g_atom:
    out_put ='{}{}_atom'.format(prefix_simulation, file_name )
    graphicsGenerator.generate_atom_graph(json_simulation['graph_atoms_field'], json_simulation['graph_atoms_score'],
                                      json_simulation['graph_atoms_type'], json_simulation['graph_atoms_color'],
                                      file_name, out_put)
if g_heat_map:
    out_put ='{}{}_atom_hist'.format(prefix_simulation, file_name )
    graphicsGenerator.heat_map(json_simulation['graph_atoms_field'], json_simulation['graph_atoms_score'], json_simulation['graph_atoms_type'],
                                        "Atoms", out_put)
