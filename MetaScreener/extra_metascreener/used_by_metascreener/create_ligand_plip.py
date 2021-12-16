#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import sys
import os
import subprocess
import shutil
import json
import pymol
from interactions_colors import COLORS_INTERACTIONS
from add_paths import *

add_paths()

PYTHON_RUN = "python "
SCRIPT_CONVERT_TO = "MetaScreener/extra_metascreener/used_by_metascreener/convert_to.py"

F_PREPARE_COMPLEX = 'python /opt/prepare_complex.py {} {} {}'
F_EDIT_SESSION = 'python /opt/edit_sessions.py {}'
CONVERT_TO = '{} {} {} {} -b'
F_PLIP_CMD = 'plipcmd  ' + " -f {} -o {} -y -t --maxthreads {} --nofix"
CORES = 1


def help():
    print("Error: Parameters")
    print("1º [ Receptor | Complex ] ")
    print("2º [ Ligand  | None ]")
    print("3º Output prefix")
    print("4º Receptor in pdb format")
    exit()


def execute_cmd(cmd):
    print(cmd)
    return subprocess.check_output(cmd, shell=True)


def run_plip(out_prefix, num_plip):
    cmd = 'sed -i -e "s/\*\*\*/LIG/g" ' + out_prefix + '_interactions_complex.pdb'
    subprocess.check_output(cmd, shell=True)

    cmd = 'sed -i -e "s/>/ /" ' + out_prefix + '_interactions_complex.pdb'
    subprocess.check_output(cmd, shell=True)

    cmd = 'sed -i -e "s/</ /" ' + out_prefix + '_interactions_complex.pdb'
    subprocess.check_output(cmd, shell=True)

    cmd = F_PLIP_CMD.format(
        out_prefix + "_interactions_complex.pdb",
        out_prefix + "_complex",
        CORES
    )

    if (num_plip > 1):
        cmd += " --inter d"
    try:
        execute_cmd(cmd)
        pattern = glob.glob(out_prefix + '_complex/*.pse')
        fname, _ = os.path.splitext(pattern[0])

        ext = ".pse"
        shutil.move(fname + ext, out_prefix + '_interactions' + ext)

        shutil.move(out_prefix + '_complex/report.txt', out_prefix + '_interactions.txt')

        shutil.rmtree(out_prefix + '_complex')
    except Exception as e:
        print("ERROR: Plip", out_prefix + '_complex')
        print(e)


def convert_molecule(file_1, file_pdb):
    cmd = CONVERT_TO.format(PYTHON_RUN, SCRIPT_CONVERT_TO, file_1, file_pdb)
    subprocess.check_output(cmd, shell=True)


def convert_name_plip(name_plip):
    return name_plip.replace("**", "").replace(" ", "").replace("-", "")


def read_file_plip_txt(prefix_interactions_plip):
    file_txt = prefix_interactions_plip + '.txt'
    file_json = prefix_interactions_plip + '.json'
    table_scores = {}
    key = ""
    start_token = "+=======+"
    mid_token = "+-------+"
    title_token = "**"

    table_scores['interactions_shape'] = COLORS_INTERACTIONS
    table_scores['interactions_groups'] = {}
    if os.path.isfile(file_txt):
        f = open(file_txt)
        for line in f:
            if title_token in line:
                line = line.replace(title_token, "").strip()
                key = convert_name_plip(line)
            if line.startswith("|") and mid_token not in line and start_token not in line:
                line = line.replace(' ', '').strip()[1:-1]
                if key not in table_scores['interactions_groups']:
                    table_scores['interactions_groups'][key] = {}
                    table_scores['interactions_groups'][key]['interactions'] = []
                if len(table_scores['interactions_groups'][key]) == 1:
                    table_scores['interactions_groups'][key]['legend'] = line
                elif line != table_scores['interactions_groups'][key]['legend']:
                    table_scores['interactions_groups'][key]['interactions'].append(line)

        f.close()

    parsed = json.loads(json.dumps(table_scores))

    with open(file_json, 'w') as outfile:
        json.dump(parsed, outfile, indent=4, sort_keys=True)

    return table_scores


if __name__ == "__main__":
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        help()

    rec = sys.argv[1]
    lig = sys.argv[2]
    out_prefix = sys.argv[3]
    if lig == "None":
        lig = None

    if lig != None and not os.path.isfile(lig) or not os.path.isfile(rec):
        print("ERROR: ligand or receptor does not exist")
        exit()

    rec_name, rec_ext = os.path.splitext(rec)

    if len(sys.argv) == 5:
        shutil.copy(sys.argv[4], rec_name + ".pdb")
    elif rec_ext != ".pdb":
        convert_molecule(rec, rec_name + ".pdb")
    rec = rec_name + ".pdb"

    if lig == None:
        shutil.copy(rec, out_prefix + "_interactions_complex.pdb")
    else:
        lig_name, lig_ext = os.path.splitext(lig)
        if lig_ext != ".pdb":
            convert_molecule(lig, lig_name + ".pdb")
            lig = lig_name + ".pdb"
        cmd = F_PREPARE_COMPLEX.format(rec, lig, out_prefix + "_interactions_complex.pdb")
        execute_cmd(cmd)

    pymol.pymol_argv = ['pymol', '-c', '-q', '-k']
    pymol.finish_launching()
    pymol.cmd.reinitialize()
    pymol.cmd.load('{}'.format(rec), object='rec')

    run_plip(out_prefix, len(pymol.cmd.get_chains('rec')))

    pymol.cmd.delete('all')

    read_file_plip_txt(out_prefix + "_interactions")
    cmd = F_EDIT_SESSION.format(out_prefix + "_interactions.pse")

    execute_cmd(cmd)
