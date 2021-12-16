#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#
import sys
import os
import subprocess
import argparse

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def is_tool(name):
    """Check whether `name` is on PATH."""
    from distutils.spawn import find_executable
    return find_executable(name) is not None


ALLOW_EXT_IN = [".pdbqt", ".mol2", ".sdf", ".pdb", ".smi", ]
ALLOW_EXT_OUT = [".pdbqt", ".mol2", ".sdf", ".pdb", ".ldb", '.xyz']
AMINOACIDS = ['CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL', 'ALA', 'ARG', 'ASN', 'ASP']

path_ext_sw = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'external_sw/')

BABEL_EXE = 'babel '

#
#   pdbqt sw
#_______________________________________________________________________________________________________________________
path_mgltools = path_ext_sw + "mgltools/"
python_exe = path_mgltools + "bin/pythonsh"
pdbqt_to_pdb = python_exe+" "+path_mgltools+"MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py -f {} -o {}"
PREPARE_LIGAND_4 = python_exe+" "+path_mgltools+"MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py -l {} -o {} -A 'hydrogens -U \\\'\\\' "
PREPARE_RECEPTOR_4 = python_exe+" "+path_mgltools+"MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py -r {} -o {} -A checkhydrogens"

#
# Chembl
#
MOL2_PDB_LIGAND = path_ext_sw+'ChemAxon/JChem/bin/molconvert -3:S{{fine}}[mmff94]L{{3}} mol2 {0} -o {2} #{1} {3} -F'
MOL2_PDB_RECEPTOR =path_ext_sw+'ChemAxon/JChem/bin/molconvert -3:S{{fine}}[mmff94]L{{3}} mol2 {0} -o {2} #{1} {3} -F'

#
#   Ls Software
#_______________________________________________________________________________________________________________________
SDF_LDB_CONVERT = path_ext_sw+"/ligandScout/idbgen -i {} -o {}  -A ON --num-processes 1 --slave-memory 4 --num-cores 4 --set-memory 2"
SDF_LDB_CONVERT_MULTICONFORMER =  path_ext_sw+"/ligandScout/idbgen -i {} -o {} -t icon-best --num-processes 1 --slave-memory 4 --num-cores 4 --set-memory 2"


#
#	smiles to sdf
#
SMILES_SDF_CONVERT_CONFORMATIONS = path_ext_sw+"/omega/bin/omega2 -in {} -out {}  -warts true -rms 0.1 -strictstereo false -strictatomtyping false"
SMILES_SDF_CONVERT = path_ext_sw+"/omega/bin/omega2 -in {} -out {} -maxconfs 1 -strictstereo false -strictatomtyping false"
#
#   babel run
#_______________________________________________________________________________________________________________________
babel_run = BABEL_EXE+" {} {}"

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
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX)
    #stdout = proc.stdout.read()
    q = Queue()
    stdout = Thread(target=enqueue_output, args=(proc.stdout, q))
    stdout.daemon = True  # thread dies with the program
    stdout.start()
    stderr = proc.stderr.read()

    if stderr and "ERROR" in '{}'.format(stderr).upper():
        print ("{}ERROR: {} {} ".format(bcolors.FAIL, stderr.strip(), bcolors.ENDC))
        print ('{}ERROR CMD: {} {}'.format(bcolors.FAIL, cmd, bcolors.ENDC))
    else:
        print ('{} {} {}'.format(bcolors.HEADER, cmd, bcolors.ENDC))
    
    
    return stdout

#
#   Conversion methods
#_______________________________________________________________________________________________________________________
def conv_sdf_ldb(mol_in, mol_out):
    if multiconformation == True:
        cmd = SDF_LDB_CONVERT_MULTICONFORMER.format(mol_in, mol_out )
    elif not multiconformation:
        cmd = SDF_LDB_CONVERT.format(mol_in, mol_out)
    else:
        print ("ERROR: You must indicate parameter multiconformation")
        exit()
    return execute_cmd(cmd)


def con_pdbqt_pdb(mol_in, mol_out):
    cmd = pdbqt_to_pdb.format(mol_in, mol_out)
    return execute_cmd(cmd)


def conv_pdb_pdbqt(mol_in, mol_out):
    cmd = prepare_pdbqt.format(mol_in, mol_out)
    return execute_cmd(cmd)

def conv_pdb_mol2(mol_in, mol_out):
    cmd = mol2_pdb.format(
        mol_in,
        os.path.splitext(mol_in)[1][1:],
        mol_out,
        os.path.splitext(mol_out)[1][1:])
    return execute_cmd(cmd)


def conv_mol2_pdb(mol_in, mol_out):

    cmd = mol2_pdb.format(
        mol_in,
        os.path.splitext(mol_in)[1][1:],
        mol_out,
        os.path.splitext(mol_out)[1][1:]
    )
    return execute_cmd(cmd)


def conv_pdb_sdf(mol_in, mol_out):
    cmd = babel_run.format(mol_in, mol_out)
    return execute_cmd(cmd)


def conv_sdf_pdb(mol_in, mol_out):
    cmd = babel_run.format(mol_in, mol_out)
    return execute_cmd(cmd)

def conv_babel_3d(mol_in, mol_out):
    cmd = OBABEL_EXE + " --gen3D -h  {} {} ".format(mol_in, mol_out)
    return execute_cmd(cmd)


def conv_babel(mol_in, mol_out):
    cmd = babel_run.format(mol_in, mol_out)
    return execute_cmd(cmd)

def conv_smiles_sdf(mol_in, mol_out):
    cmd = SMILES_SDF_CONVERT.format(mol_in, mol_out)
    return execute_cmd(cmd)


def remove_pdb():
    cmd = "rm " + mol_out + ".pdb"
    return subprocess.check_output(cmd, shell=True)


def remove_mol2():
    cmd = "rm " + mol_out + ".mol2"
    return subprocess.check_output(cmd, shell=True)


def is_receptor(file_in):
    cmd = "cat {}".format(file_in)    
    aux = subprocess.check_output(cmd, shell=True)
    aux=str(aux).strip().encode().decode('utf8')
    cont_residues = 0
    for i in AMINOACIDS:
        if i in aux:
            cont_residues += 1
    receptor = False
    if cont_residues > 4:
        receptor = True
    return receptor


def pdbqt_in():
    if ext_mol_out == ".pdb":
        con_pdbqt_pdb(file_in, file_out)
    elif ext_mol_out == ".mol2":
        con_pdbqt_pdb(file_in, mol_out + ".pdb")
        conv_pdb_mol2(mol_out + ".pdb", file_out)
        remove_pdb()
    elif ext_mol_out == ".sdf":
        con_pdbqt_pdb(file_in, mol_out + ".pdb")
        conv_pdb_mol2(mol_out + ".pdb", file_out)
        remove_pdb()
    elif ext_mol_out == ".xyz":
        conv_babel(file_in, file_out)
    else:
        print("Conversion error")


def mol2_in():
    if ext_mol_out == ".pdbqt":
        conv_pdb_pdbqt(file_in, file_out)
    elif ext_mol_out == ".pdb":
        conv_mol2_pdb(file_in, file_out)
    elif ext_mol_out == ".sdf":
        conv_babel(file_in, file_out)
    elif ext_mol_out == ".xyz":
        conv_babel(file_in, file_out)

    else:
        print("Conversion error")


def pdb_in():
    if ext_mol_out == ".pdbqt":
        conv_pdb_pdbqt(file_in, file_out)
    elif ext_mol_out == ".mol2":
        conv_pdb_mol2(file_in, file_out)
    elif ext_mol_out == ".sdf":
        conv_pdb_sdf(file_in, file_out)
    elif ext_mol_out == ".xyz":

        conv_babel(file_in, file_out)

def sdf_in():
    if ext_mol_out == ".pdbqt":
        conv_sdf_pdb(file_in, mol_out + ".pdb")
        conv_pdb_pdbqt(mol_out + ".pdb", mol_out + ".pdbqt")
    elif ext_mol_out == ".mol2":
        conv_pdb_mol2(file_in, file_out)
    elif ext_mol_out == ".ldb":
        conv_sdf_ldb(file_in, mol_out + ".ldb")
    elif ext_mol_out == ".xyz":
        conv_babel(file_in, file_out)


def smi_in():
    if ext_mol_out == ".pdbqt":
        conv_babel_3d(file_in, mol_out + ".mol2")
        conv_pdb_pdbqt(mol_out+".mol2", mol_out+".pdbqt")
        remove_mol2()
    if ext_mol_out == ".mol2":
    	conv_smiles_sdf(file_in, mol_out + ".sdf")
    	conv_pdb_mol2(mol_out+".sdf", mol_out+".mol2")
    	cmd = "rm " + mol_out + ".sdf"
    	return subprocess.check_output(cmd, shell=True)        
    elif ext_mol_out == ".xyz":
        conv_babel(file_in, file_out)
    elif ext_mol_out == ".sdf":
    	conv_smiles_sdf(file_in, file_out)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

#
#   Main
#_______________________________________________________________________________________________________________________
parser = argparse.ArgumentParser()
parser.add_argument("i", help="1º input structure", type=argparse.FileType('r'))
parser.add_argument("o", help="2º output Structure", type=argparse.FileType('w'))
parser.add_argument("-m", "--multiple_conformation", help="multiple conformations, LS", default=False,  action='store_true')
parser.add_argument("-b", "--babel", help="Use babel", default=False,  action='store_true')
args = parser.parse_args()

file_in = args.i.name
file_out = args.o.name
mol_in, ext_mol_in = os.path.splitext(file_in)
mol_out, ext_mol_out = os.path.splitext(file_out)
multiconformation = args.multiple_conformation




prepare_pdbqt = PREPARE_RECEPTOR_4 if is_receptor(file_in) else PREPARE_LIGAND_4
mol2_pdb = MOL2_PDB_RECEPTOR if is_receptor(file_in) else MOL2_PDB_LIGAND

if ext_mol_in not in ALLOW_EXT_IN:
    print("Input format error, only allowed")
    print(ALLOW_EXT_IN)
    exit()
elif ext_mol_out not in ALLOW_EXT_OUT:
    print("Output format error, only allowed ")
    print(ALLOW_EXT_OUT)
    exit()
elif ext_mol_out == ext_mol_in:
    print("Ligands with the same format error")
    exit()
elif is_receptor(file_in) and ext_mol_out == ".ldb":
    print("Error: The use of proteins for LS(ldb) is not allowed")
    exit()
elif ext_mol_out == ".ldb" and len(sys.argv) != 4:
    help();

if args.babel:
    conv_babel(file_in, file_out)
elif ext_mol_in == ".pdbqt":
    pdbqt_in()
elif ext_mol_in == ".mol2":
    mol2_in()
elif ext_mol_in == ".pdb":
    pdb_in()
elif ext_mol_in == ".sdf":
    sdf_in()
elif ext_mol_in == ".smi":
    smi_in()














