import argparse
from os.path import splitext
import shutil
import re
TOKEN_START_MOL2 = '@<TRIPOS>ATOM'
TOKEN_END_MOL2 = '@<TRIPOS>BOND'
data_molecule = False
FORMAT_MOL_MOD = "{:>6} {:<6}{:>13}{:>13}{:>13} {:<7}{:>6} {:<10} {:>9} {} "


def convert_number(residue):
    str_num = ""
    for i in residue:
        if i.isdigit():
            str_num += i
    return int(str_num)

def write_molecule(lst, file_name):
    shutil.copy(args.file.name, args.file.name + ".bk")
    f = open(file_name, 'w')
    for i in lst:
        f.write('{}\n'.format(i))
    f.close()

parser = argparse.ArgumentParser( description="Rename the amino acids in a protein mol2 to start at 1")
parser.add_argument("file", type=argparse.FileType("r"))
args = parser.parse_args()
name_mol, ext_mol = splitext(args.file.name)
is_correct_format = True
lst_mol = []
if ext_mol != ".mol2":
    print ("\nError, need mol2 file\n")
    exit()

f_mol = open(args.file.name)
for line in f_mol:
    line = line.strip()
    if data_molecule and line != "" and not TOKEN_END_MOL2 in line:
        aux = re.sub(' +', ' ', line).split(" ")        
        res_ind = int(aux[6])
        res_num = convert_number(aux[7])
        if res_ind != res_num:
            is_correct_format = False

            lst_mol.append(FORMAT_MOL_MOD.format(aux[0], aux[1], aux[2], aux[3], aux[4], aux[5], res_num, aux[7], aux[8], aux[9] if len(aux) == 10 else ""))
        else:
            lst_mol.append(line)
    else:
        lst_mol.append(line)

    if TOKEN_START_MOL2 in line or TOKEN_END_MOL2 in line:
        data_molecule = not data_molecule
f_mol.close()
if (not is_correct_format):
    write_molecule(lst_mol, args.file.name)
    print ("Protein's indexes have been renamed to the numbers of residues.")

