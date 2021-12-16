#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Autor:   Jorge De La Peña Garcia (jorge.dlpg@gmail.com)
#       Fecha:   3/3/2017
#       version: 1
#
try:
    from string import strip
except:
    pass
import sys
import subprocess
import os
import re
from add_paths import *
add_paths()
from GraphicsGenerator import GraphicsGenerator
graphicsGenerator = GraphicsGenerator()


SCRIPT_CONVERT_TO = "MetaScreener/extra_metascreener/used_by_metascreener/convert_to.py"
CONVERT_TO = '{} {} {} {} '
POSEVIEW_DIR = "MetaScreener/external_sw/poseview/"
POSEVIEW_CMD = POSEVIEW_DIR + "poseview"
POSEVIEW_SETTINGS = POSEVIEW_DIR + "settings.pxx"
POSEVIEW_RUN = POSEVIEW_CMD+ ' -t \'\' -c {} -p {} -l {} -o {} 2>/dev/null'


def execute_poseview(target, lig, out_graph):
    cmd = POSEVIEW_RUN.format(
        POSEVIEW_SETTINGS,
        target,
        lig,
        out_graph
    )
    try:
        return subprocess.check_output(cmd, shell=True)
    except:
        print("ERROR; PoseViewGraph.py " + target + " " + lig)



def help():
    print("Error: Parameters")
    print("1º Receptor ")
    print("2º Ligand")
    print("3º Output")
    exit()


def convert_molecule(file_1, file_pdb):
    cmd = CONVERT_TO.format(PYTHON_RUN, SCRIPT_CONVERT_TO, file_1, file_pdb)
    subprocess.check_output(cmd, shell=True)


def make_poseview_histogram(out_poseview, out):
    out_hist = os.path.splitext(out)[0]
    lbls, vals = parse_poseview_log(out_poseview)
    title = os.path.basename(out_hist) +  '\nEnergetic contributions to binding energy (Calculated with poseview)'
    out_put =  out_hist + '_povw_hist'

    graphicsGenerator.generate_histogram_poseview(vals, lbls, title, 'Contribution (kcal/mol)', out_put)


def parse_poseview_log(out_poseview):

    score_re = re.compile(r'^\|\s+(\w+)\s+(\w+)?\s+\|\s+([-.\d]+)?\s+\|', re.I | re.M)
    scores = score_re.findall(out_poseview)

    iname = []
    labels = []
    values = []
    for score in scores:

        if score[0].lower() == 'total':
            continue
        iname.append(score[0] + score[1])
        if score[2]:
            labels.append('\n'.join(iname))
            values.append(float(score[2]))
            iname = []
    return labels, values


if __name__ == "__main__":

    if len(sys.argv) != 4:
        help()
    rec = sys.argv[1]
    lig = sys.argv[2]
    out = sys.argv[3]

    if not os.path.isfile(POSEVIEW_CMD):
        print ("ERROR: "+POSEVIEW_CMD+" doesn't exist")
        exit()
    if not os.path.isfile(lig) or not os.path.isfile(rec):
        print ("ERROR: Receptor or ligand doesn't exist")
        exit()
    rec_name, rec_ext = os.path.splitext(rec)
    lig_name, lig_ext = os.path.splitext(lig)

    if rec_ext != ".pdb" and rec_ext != ".mol2":
        convert_molecule(rec, rec_name+".pdb")
        rec = rec_name+".pdb"
    if lig_ext != ".mol2":
        convert_molecule(lig, lig_name + ".mol2")
        lig = lig_name + ".mol2"

    out_poseview = str(execute_poseview(rec, lig, out)).strip()#.encode().decode('utf8')
    out_poseview.replace("\\n","\\\n")
    posvw_name = os.path.splitext(out)[0]
    with open(posvw_name + '.povw', 'wt') as funit:
        funit.write(out_poseview)

    make_poseview_histogram(out_poseview, out)




