#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 	Author: Jorge de la Peña García
#	Author: Carlos Martínez Cortés
#	Email:  cmartinez1@ucam.edu
#	Description: Generates a json with Metascreener output
#
#	sys.argv[1] output
#	sys.argv[2] data
#	
#	data[0]: Query's name
#	data[1]: Query's file
#	data[2]: Protein's file
#	data[3]: out_molec
#	data[4]: coordinates
#	data[5]: num executions for BD
#	data[6]: num aminoacid
#	data[7]: Target's chain
#	data[8]: score global
#	data[9]: size_grid
#	data[10]: option
#	data[11]: software
#	data[15]: graph global_ color
#	data[16]: graph_global_filed
#	data[17]: graph_global_score
#	data[18]: graph_atom_color
#	data[19]: graph_atom_filed
#	data[20]: graph_atoms_type
#	data[21]: graph_global_score
#	data[22]: graph_global_score
#	data[23]: graph_global_score
#	.....
#_________________________________________________________________________________________________________________________________________________________________________
import json
import sys

file_output=sys.argv[1]
data = sys.argv[2].split("\\n")
atom_score = []

if len(data) > 20:
	for i in range(21,len(data)):
		if data[i]:
			atom_score.append(data[i].split(":"))	
data_json={
	"name":data[0],
	"file_ori_query":data[1],
	"file_ori_target":data[2],
	"file_result":data[3],
	"coords":data[4].split(":"),
	"num_execution":data[5],
	"num_aminoacid":data[6],
	"chain_protein":data[7],
	"global_score":data[8],
	"size_grid":data[9],
	"option":data[10],
	"software":data[11],
	"global_score_md":data[12],
	"global_score_qu":data[13],
	"graph_global_color":data[15].split(":"),
	"graph_global_field":data[16].split(":"),
	"graph_global_score":data[17].split(":"),
	"graph_atoms_color":data[18].split(":"),
	"graph_atoms_field":data[19].split(":"),
	"graph_atoms_type":data[20].split(":"),
	"graph_atoms_score":atom_score,
}

with open(file_output, 'w') as outfile:
	json.dump(data_json, outfile, indent=4, sort_keys=True)


