#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#       Check protein's atoms
#       return:
#             true if protein ok
#             False if broken atoms
#
#       dependency:
#           MetaScreener/extra_metascreener/used_by_metascreener/standar_file_coords.py"
#_______________________________________________________________________________________________________________________
import sys
import subprocess
python_version = int(sys.version.split(".")[0])

standar_file_coords = "MetaScreener/extra_metascreener/used_by_metascreener/standar_file_coords.py"


def read_pdb_file(filename):
    cnt_lines = 0
    cmd = "python {} {} ".format(standar_file_coords, filename)

    first_atom = None
    first_chain = None
    chains = 0
    # number of protein chains

    if python_version == 3:
        array_target = str(subprocess.check_output(cmd, shell=True), 'utf-8').split("\n")
    else:
        array_target = subprocess.check_output(cmd, shell=True).split("\n")

    for i in array_target:
        if not i.startswith("#") and not i.strip() == "":
            aux = i.split(":")
            if len(aux) > 4:                                    # eliminated possible pymol errors
                if not first_atom:                              # first time
                    first_atom = int(aux[6])
                    chains = 1
                if not first_chain:
                    first_chain = aux[7]
                else:
                    if first_chain != aux[7]:
                        first_chain = aux[7]
                        first_atom = int(aux[6])
                        chains += 1
                    else:
                        if first_atom + 1 == int(aux[6]) or first_atom == int(aux[6]):
                            first_atom = int(aux[6])
                        else:
                            chains = 'Line: {}\t Chain: {} Atom: {}\t Chain: {} Atom: {}'.format(cnt_lines, first_chain, first_atom, aux[3], aux[6])
                            break
        cnt_lines += 1
    return chains


if len(sys.argv) != 2:
    print("ERROR: Enter a protein file")
    exit()

protein = sys.argv[1]
print(read_pdb_file(protein))
