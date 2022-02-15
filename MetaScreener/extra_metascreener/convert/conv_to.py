# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Author: Jorge de la Peña García
   Email:  jpena@ucam.edu
   Description: Convert molecule folders between sdf, pdb, pdbqt and mol2 formats

"""
import argparse
import os
from glob import glob
from os.path import join, splitext
import subprocess
import sys

TIME_LIMIT = 'timeout -k 9 '
PYTHON_RUN = 'python'

F_SCRIPT_CONVERT = PYTHON_RUN + ' MetaScreener/extra_metascreener/used_by_metascreener/convert_to.py {} {}'

ON_POSIX = 'posix' in sys.builtin_module_names
from threading  import Thread
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # python 2.x
def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()
def execute_cmd(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
                            close_fds=ON_POSIX)
    q = Queue()
    stdout = Thread(target=enqueue_output, args=(proc.stdout, q))
    stdout.daemon = True  # thread dies with the program
    stdout.start()
    stderr = proc.stderr.read()

    if stderr:
        print ("ERROR: {}".format(stderr.strip()))
        print ('ERROR CMD:  {}'.format(cmd))
    else:
        print ('{}'.format(cmd))

    return stdout


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values.strip()
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

parser = argparse.ArgumentParser()
parser.add_argument('folder_in',  action=readable_dir, help="molecule folder")
parser.add_argument('ext_in', choices=['mol2', 'pdbqt', 'sdf', 'pdb'], help="Input extension [ mol2 | pdbqt | sdf | pdb ]")
parser.add_argument('ext_out', choices=['mol2', 'pdbqt', 'sdf', 'pdb'], help="Output extension [ mol2 | pdbqt | sdf | pdb ]")
parser.add_argument('-t', '--time', default="", help='Set time limit for each conversion. For example: 5m')
args = parser.parse_args()

if (args.time != ""):
    F_SCRIPT_CONVERT = TIME_LIMIT + args.time + ' ' + F_SCRIPT_CONVERT

folder_pattern = join(args.folder_in, '*'+str(args.ext_in))
for molecule in glob(folder_pattern):
    mol = '{}.{}'.format(splitext(molecule)[0], args.ext_out)
    print(molecule)
    execute_cmd (F_SCRIPT_CONVERT.format(molecule, mol))






