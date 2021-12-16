#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from glob import glob
import json
from os.path import isdir
import os

PREFIX_INTERACTIONS = "_interactions.json"
F_PLIP_JSON = "/clustered_interactions/"
F_PLIP_JSON_SIM = "/energies/"

def read_pml(folder):
    lines = []
    for i in glob(folder + '*.pml'):
        f = open(i)
        for line in f:
            lines.append(line)
        f.close()
    return lines


def get_cl(lines_pml, name):
    name = name.replace("_interactions","")

    for i in lines_pml:
        if i.startswith("cmd.group(") and name in i:
            return (i.split("'")[1]+"_"+name).replace(" ","_")

    with open(folder+F_PLIP_JSON_SIM+name+".json") as f:
        data = json.load(f)
    return data['global_score']+"_"+name


def map_residues(folder, num_map):
    if num_map != 0:
        import subprocess
        for i in range(len(lst_residues)):
            aux = lst_residues[i].split("_")
            lst_residues[i] = str(int(aux[1]) + num_map)
        for i in glob(folder + 'clustered_poses/*.pdb'):
            cmd = "python MetaScreener/extra_metascreener/used_by_metascreener/standar_file_coords.py "+i
            out = subprocess.check_output(cmd, shell=True)
            for i in out.split("\n"):
                if not i.startswith("#") and  i != "":
                    aux = i.split(":")
                    for j in range(len(lst_residues)):
                        if aux[len(aux)-2] == lst_residues[j]:
                            lst_residues[j]='{}_{}'.format(aux[len(aux)-3],lst_residues[j])
                            break
    return lst_residues


def sum_residues( res, num_map):
    if num_map != 0:
        aux = res.split("_")
        return aux[0]+"_"+str( int(aux[1])+num_map)
    else:
        return res


def help():
    print("HELP")
    print("Positional parameters")
    print("1. prefix | folder")
    print("2. residues [ all | VAL_293:TYR_299:THR_305:SER_300:PHE_306:PHE_301:PHE_298:PHE_289:MET_304:LYS_297:LYS_291:ILE_302:HIS_303:GLU_296:GLU_292:GLN_307:GLN_290:CYS_295:ASP_294 ]")
    print("3. input gap")
    print("4. output gap")
    exit()

inputGap = 0
outputGap = 0

if len(sys.argv) < 3 or len(sys.argv) > 5:
    help()

lst_residues = sys.argv[2].split(":")
if len(sys.argv) == 5:
    inputGap = int(sys.argv[3])
    outputGap = int(sys.argv[4])
elif len(sys.argv) == 4:
    inputGap = outputGap = int(sys.argv[3])

prefix = sys.argv[1]
lst_dirs = glob('{}*/'.format(prefix))

if len(lst_dirs) == 0:
    print ("Error not directories with this prefix were found")
    exit(0)

if lst_residues != "all":
    lst_residues = map_residues(lst_dirs[0],-inputGap)

for folder in lst_dirs:
    if isdir(folder):
        print("folder: "+folder)
        folder_json= folder+F_PLIP_JSON
        dict_json = {}

        for i in glob(folder_json+'*.json'):

            with open(i) as f:
                data = json.load(f)
            dict_json[i]=data
        lines_pml = read_pml(folder)

        clusters = {}
        for k, v in dict_json.iteritems():

            name = os.path.basename(k)
            name = name[:len(name) - len(PREFIX_INTERACTIONS)]

            cl = get_cl(lines_pml, name)
            for k_2, v_2 in v['interactions_groups'].iteritems():
                for i in v_2['interactions']:
                    aux_res = i.split('|')[1]+"_"+i.split('|')[0]
                    if aux_res in lst_residues or lst_residues[0]== "all":
                        if cl not in clusters:
                            clusters[cl] = {}
                        if aux_res not in clusters[cl]:

                            clusters[cl][str(sum_residues(aux_res, outputGap))]=[]
                        if k_2[0:6] not in clusters[cl][str(sum_residues(aux_res, outputGap))]:
                            clusters[cl][str(sum_residues(aux_res, outputGap))].append(k_2[0:6])
        lst = []
        for cl, v in clusters.iteritems():
            line = ""
            num=0
            for k_2, v_2 in v.iteritems():
                num += len(v_2)
                line += k_2 +"("+ str(' '.join(v_2))+") "
            lst.append('{}; {}; {}'.format(cl, num, line))

        for i in sorted(lst, key = lambda x: len(x.split(" ")), reverse=True):
       	    print("\t"+i)
	print("")