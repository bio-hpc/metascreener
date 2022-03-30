# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import datetime
import shutil
import operator
import glob
import json
import subprocess
import re
import argparse
from collections import OrderedDict

FOLDER_ENERGIES = "/clustered_poses/"
FOLDER_MOLECULES = "./clustered_poses/"
FOLDER_INTERACTIONS = "/clustered_interactions/"
PYTHON_RUN = "python"
PML_LIGAND_PYMOL = PYTHON_RUN + " MetaScreener/extra_metascreener/used_by_metascreener/create_ligand_pymol.py {} {} {} {} {} {}"
PML_HEAD_PYMOL = PYTHON_RUN + " MetaScreener/extra_metascreener/used_by_metascreener/create_header_pml.py {} -head {} -tail {}"
GLOBAL_ENERGY = 'global_score'

key_pat = re.compile(r"^(\D+)(\d+)$")   #usado para ordenar el diccionario

def key(item):
    m = key_pat.match(item[0])
    return m.group(1), int(m.group(2))


class Group:

    def __init__(self, cl):
        self.name_prot = cl.name_prot
        self.groups = cl.group
        self.cluster = cl


    def add_element(self, element):
        self.groups = self.groups + ' ' + element


class Cluster:
    def __init__(self, cl, f_molecules, f_o):
        for i in range(0, len (cl['coords'])):
            cl['coords'][i] = round(cl['coords'][i],2)
        self.dict_lig_name = cl['lig_name']

        self.coords = cl['coords']
        self.cluster = cl ['cluster']
        self.sw = cl['sw']
        self.score = cl['score']
        pattern = cl['folder'] + "/{}/{}_*{}"
        self.folder = cl['folder']        
        self.f_json = glob.glob(pattern.format('energies', cl['best_pose'], '.json'))[0]
        self.f_molecules = f_molecules
        self.f_interactions_json = glob.glob(pattern.format('clustered_interactions', cl['best_pose'], '.json'))[0]
        self.data_json = read_json(self.f_json)
        self.interactions_json = read_json(self.f_interactions_json)
        self.n_l_aux = self.data_json ['name']
        self.name_prot = os.path.splitext(os.path.basename(self.data_json['file_ori_target']))[0]

        self.file_receptor_ori = os.path.join(self.folder, FOLDER_MOLECULES, self.name_prot + os.path.splitext(self.data_json['file_result'])[1])
        self.file_receptor = "../" + os.path.basename(os.path.normpath(f_molecules)) + "/" + self.name_prot +  os.path.splitext(self.data_json['file_result'])[1]

        aux = os.path.splitext(os.path.basename(self.data_json['file_result']))[0] +os.path.splitext(self.data_json['file_result'])[1]
        self.f_molecule_out = "../" + os.path.basename(os.path.normpath(f_molecules)) + "/" +aux

        self.name_lig = os.path.splitext(os.path.basename(self.data_json['file_result']))[0]

        self.f_o = f_o

        self.file_pml_rec = self.f_o + "/pymol_rec.pml"
        self.file_pml_score = self.f_o + "/pymol_score.pml"


class Clusters:
    def __init__(self, lst_cluster, folder, f_o, f_molecules, cnt_cluster):

            self.folder = folder
            self.clusters = OrderedDict()

            for cl in lst_cluster:
                for i in cl:
                    if i['lig_name'] not in self.clusters:
                        self.clusters[i['lig_name']] = []

                    self.clusters[i['lig_name']].append(Cluster(i, f_molecules, f_o))
        

    def get_ligand_pml(self, num_cl):
        for key, lst_cl in self.clusters.items():
            for cl in lst_cl:
                cmd = PML_LIGAND_PYMOL.format(
                    cl.f_molecule_out,
                    cl.f_json,
                    cl.f_interactions_json,
                    0,#num_cl,
                    1,
                    "STANDARD_BD"
                )
                cl.pml = subprocess.check_output(cmd, shell=True)

                aux = cl.pml.split("\n")
                group = aux[len(aux)-3]

                group = group.split("'")[1]

                cl.group = '{}_{}_CL_{}_{}'.format(cl.dict_lig_name.replace('_(*)','_warning'), cl.sw, cl.cluster,  round(cl.score,2))
                cl.pml = cl.pml.replace(group, cl.group)

    def write_pml(self, n_cl, file_pml_score, cnt_cluster):
        #group = "CCL_{}{}".format(cnt_cluster,n_cl)
        aux_group =""
                
        f = open(file_pml_score, "a")
        i=0
        score=0.0
        for key, lst_cl in self.clusters.items():
            for cl in lst_cl:
                i+=1
                score+=cl.score
                f.write(cl.pml)
                aux_group += " "+cl.group
        group = "CCL_{}{}{}".format(cnt_cluster,n_cl,round((score/i),2))
        group = "cmd.group('{}', '{}')\n".format(group, aux_group)
        f.write(group)
        f.close()

    def copy_data(self):
        f1 = "energies/"
        f2 = "clustered_affinities/"
        f3 = "clustered_interactions/"
        f4 = "energies/"
        f5 = "molecules/"
        for key, lst_cl in self.clusters.items():
            for cl in lst_cl:
                copy_files(cl.folder + "/" + f2 + cl.name_lig, ".png", cl.f_molecules)
                copy_files(cl.folder + "/" + f3 + cl.name_lig, ".png", cl.f_molecules)
                copy_files(cl.folder + "/" + f3 + cl.name_lig, ".json", cl.f_molecules)
                copy_files(cl.folder + "/" + f4 + cl.name_lig, ".json", cl.f_molecules)
                copy_files(cl.folder + "/" + f5 + cl.name_lig, os.path.splitext(cl.data_json['file_result'])[1], cl.f_molecules)

    def print_obj(self):
        print((self.name_lig, self.score))

    def get_pml(self):
        print((self.new_load))
        print((self.pseudoatom))
        print((self.shape_show))
        print((self.group))

def write_protein_pml(file_pml, protein_file, f_molecules):

    name_protein = os.path.basename(protein_file.name).split(".")[0]
    
    if os.path.exists(protein_file.name):
        shutil.copy(protein_file.name, f_molecules)
    else:
        print(("File not exist " + file))
    f_rec = os.path.join('./../molecules/',os.path.basename(protein_file.name))


    cmd = PML_HEAD_PYMOL.format(" -t "+f_rec, False, True)
    f = open(file_pml, "a")
    f.write(subprocess.check_output(cmd, shell=True))
    f.close()

    return name_protein


def read_json(file ):
   
    with open(file) as json_file:  
        data = json.load(json_file)
    return data

def copy_files(path_prefix, ext, folder_for_cp):
    for file in glob.glob(path_prefix+ '*' +ext):
        if os.path.exists(file):
            shutil.copy(file, folder_for_cp)
        else:
            print(("File not exist "+file))


def get_better_score_efficiency(folder, energy_col,  max_ligs_for_bd):
    f = folder+FOLDER_ENERGIES
    data = {}
    for file in glob.glob(f + '*.json'):

        name = os.path.splitext(os.path.basename(file))[0]
        data_json = read_json(file)
        words = [i.replace("(","_").replace(")","").replace("/","_").replace(",","_").replace(" ","_") for i in data_json["graph_global_field"]]
        if energy_col in words:
            index = words.index(energy_col)
            data[name] = float(data_json["graph_global_score"][index])
        elif energy_col == GLOBAL_ENERGY:
            data[name] = float(data_json[GLOBAL_ENERGY])

    if len(data) > max_ligs_for_bd:        
        return sorted(list(data.items()), key=operator.itemgetter(1))[:max_ligs_for_bd]
    else:
        return sorted(list(data.items()), key=operator.itemgetter(1))


def generateexcel(lst, folder_out_ ):
    f = open(folder_out_+"/excel.csv","w")
    for i in lst:
        for j in i:
            f.write( j.name_lig+" , "+str(j.score)+"\n")
    f.close()

def add_struct(n_cl, clusters, file_pml_score, cnt_cluster):
    clusters.copy_data()
    clusters.get_ligand_pml(n_cl)
    clusters.write_pml(n_cl, file_pml_score, cnt_cluster)


def create_dir(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        shutil.rmtree(folder)
        os.makedirs(folder)

def get_score(cl, type_score):
    for i in range(0,len(cl.data_json['graph_global_field'])):
        s = cl.data_json['graph_global_field'][i].replace("(", "_").replace(")", "").replace("/", "_").replace(",", "_").replace(" ", "_")
        if  s == type_score:
           return i


def create_folders(folders_energies):
    lst_enum = {}
    for folder in folders_energies:
        name = out_folder + "_" + folder
        create_dir(name)
        lst_enum[name] = []
    return lst_enum


print ('')
parser = argparse.ArgumentParser(description='Generates a pymol session with the previously generated results from cross_list_bd_diferent_ligand', epilog="Exmaple ")
parser.add_argument('receptor', help='Experiment bd protein', type=argparse.FileType('r'))
parser.add_argument('file_json', help='File json created with cross_list_bd_diferent_ligand', type=argparse.FileType('r'))
parser.add_argument('folder_out', help='Folder_out')
parser.add_argument('-d','--debug', help='mode debug', action='store_true', default=True )
if len(sys.argv) == 1:
    parser.print_help()
    print ('')
    sys.exit(1)
args = parser.parse_args()
args.folder_out = '{}_{}'.format(args.folder_out, datetime.date.today())
array_bd_cl = json.load(open(args.file_json.name), object_pairs_hook=OrderedDict)


#
#  Create Folders
#
f_molecules = args.folder_out+"/molecules/"
f_o = args.folder_out+"/pymol/"
create_dir(f_molecules)
create_dir(f_o)

dict_clusters = OrderedDict()
cnt_cluster = 0
for n_cl, l_c in array_bd_cl.items():
    dict_clusters[n_cl] = OrderedDict()
    dict_clusters[n_cl] = (Clusters(l_c, n_cl, f_o, f_molecules, cnt_cluster))
    cnt_cluster += 1


if args.debug:
    cnt_cluster = 0
    for coords, g_lig in dict_clusters.items():
        print('{} {}  '.format(cnt_cluster, coords))
        for lig, group_lig  in g_lig.clusters.items():
            for item in group_lig:
                print ('  {:<25} {:>15} {} {}').format(item.coords, lig, item.sw,item.score)
        print ("")
        cnt_cluster += 1

file_pml_score = f_o + "pymol_score.pml"
f = open(file_pml_score, 'w')
cmd = PML_HEAD_PYMOL.format("", True, False)
f.write(subprocess.check_output(cmd, shell=True))
f.close()
write_protein_pml(file_pml_score, args.receptor, f_molecules)

cnt_cluster = 1
for n_cl, clusters in dict_clusters.items():

    add_struct(n_cl, clusters, file_pml_score, cnt_cluster)
    cnt_cluster += 1

