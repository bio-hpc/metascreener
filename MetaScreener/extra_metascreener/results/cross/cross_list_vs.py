#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Examine multiples VSs and generates a resume of the results.
# ______________________________________________________________________________________________________________________
import argparse
import glob
import json
import os
from os.path import dirname, join
import os.path
from collections import OrderedDict
from subprocess import Popen, PIPE, STDOUT
import datetime
from shutil import copyfile
import tarfile
import time

FORMAT_OUT = 'lst_{}{}.txt'
PYTHON_RUN = "python "
JOIN_CL_SESSIONS = "MetaScreener/extra_metascreener/results/join/join_cl_json_vs_session.py"
F_JOIN_SESSIONS = PYTHON_RUN + ' ' + JOIN_CL_SESSIONS + ' -f {} -d {} -r {} -o {} -v'

parser = argparse.ArgumentParser()
parser.add_argument('folder', type=str, nargs='+', help='Execution folders (2 at least) ')
parser.add_argument('-c', '--cutoff', default=-8, type=float, help='Energy cuttoff')
parser.add_argument('-r', '--receptor', default='', type=str)
parser.add_argument('-o', '--output', default='', type=str, help='name of output file')

args = parser.parse_args()
if len(args.folder) == 1:
    parser.print_help()
    exit()

def read_energies(dir):
    dct = {}
    with open(dir + "/Resume.csv") as csv:
        line = csv.readline() # header
        line = csv.readline()
        cnt = 1
        while line:
            line.strip()
            key = line.split(';')[4]
            data = float(line.split(';')[0])
            if data <= args.cutoff:
                dct[key] = data
            line = csv.readline()
            cnt += 1
    return dct


def make_tarfile(source_dir, output_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def execute_cmd(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True)
    for line in iter(p.stdout.readline, b''):
        print(line.strip())
    p.stdout.close()
    p.wait()


directories = ''
all = OrderedDict()
first_sw = ""
name_out = ''

start = time.time()
for dir in args.folder:
    index = dir.find('VS_')
    directories += '{} '.format(dirname(dirname(dir)))
    sw = dir[index + 3:index + 5]
    if (sw not in name_out):
        name_out += '{}_'.format(sw)
    if (sw == "LS"):
        print("Software LS is not supported")
        exit()
    energies = read_energies(dir)
    if len(energies) > 0:
        all[sw] = energies
    if first_sw == "":
        first_sw = sw
print("Time for read and sort all single energy files: %s seconds " % (time.time() - start))

name_out = name_out[:-1]

if args.output == '':
    prefix_out = os.path.basename(args.folder[0])
    prefix_out = prefix_out[prefix_out.find(first_sw) + len(first_sw):]
else:
    prefix_out = '_' + args.output

file_out = FORMAT_OUT.format(name_out, prefix_out)

header = " Rank ".join(all.keys()) + " Rank Molecule"
header = ", ".join(all.keys())
print(file_out)
f_out = open(file_out, 'w')
print(header)
f_out.write('{}\n'.format(header))
rank = 1;
print("Total number of folders: " + str(len(all)))

start = time.time()
if len(all) == 0:
    print("No results have been found with energy better than " + str(args.cutoff))
    exit()
for molecule in all[first_sw]:
    score = all[first_sw][molecule]
    score_aux = ""
    for k, v in all.items():
        if k != first_sw:
            if v.has_key(molecule):
                score_aux += '{} {} '.format(v.keys().index(molecule)+1, v[molecule])
            else:
                score_aux += "-- --"
    print(' {} {} {} {} '.format(rank, score, score_aux, molecule))
    f_out.write(' {} {} {} {} \n'.format(rank, score, score_aux, molecule))
    rank += 1
f_out.close()
print("Time sort all files: %s seconds " % (time.time() - start))

if (args.receptor):
    if (os.path.isfile(args.receptor)):
        out_join = file_out[:file_out.rindex("_")]
        cmd = F_JOIN_SESSIONS.format(file_out, directories, args.receptor, out_join)
        f_cl = output = '{}_{}'.format(out_join, datetime.date.today())
        print(cmd)
        execute_cmd(cmd)
        copyfile(file_out, join(f_cl, file_out))
        make_tarfile(f_cl, '{}.tar.gz'.format(f_cl))
    else:
        print("Error receptor does not exists")
