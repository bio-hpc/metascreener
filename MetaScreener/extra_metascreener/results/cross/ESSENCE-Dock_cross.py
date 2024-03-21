#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jochem Nelen
#   Author: Carlos Martinez Cortes
#   Email:  jnelen@ucam.edu
#   Description: Examine multiples VSs and generates a resume of the results.
# ______________________________________________________________________________________________________________________

import argparse
import os
import time
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument("folder", type=str, nargs="+", help="Folders to process")
parser.add_argument("-o", "--output", default="", type=str, help="name of output file")

args = parser.parse_args()

all_molecules = set()


def read_energies(input_dir):
    dct = {}
    with open(input_dir + "/Results_scoring.csv") as csv:
        lines = csv.readlines()
    for i, line in enumerate(lines[1:]):
        lineSplit = line.strip().split(";")
        compound = lineSplit[4]
        if compound not in all_molecules:
            all_molecules.add(compound)
        energy = float(lineSplit[0])
        path = str(lineSplit[-1])
        dct[compound] = [str(i + 1), energy, path]
    return dct


directories = ""
all = OrderedDict()
first_sw = ""
name_out = ""
ORDER = False

start = time.time()
args.folder.sort()

for dir in args.folder:
    index = dir.find("VS_")
    directories += "{} ".format(dir)
    sw = dir.split("VS_")[-1].split("_")[0]
    if sw not in name_out:
        name_out += "{}_".format(sw)

    energies = read_energies(dir)
    if len(energies) > 0:
        if sw in all.keys():
            all[sw].update(energies)
        else:
            all[sw] = energies
    if first_sw == "":
        first_sw = sw

file_out = args.output

header = " Rank ".join(all.keys()) + " Rank Molecule"
header = ",".join(all.keys())

f_out = open(file_out, "w")
f_out.write("{}\n".format(header))
rank = 1

if len(all) == 0:
    print("No results have been found")
    exit()

for molecule in all_molecules:
    outputLine = ""
    for sw in all.keys():
        if molecule in all[sw]:
            result = all[sw][molecule]
            outputLine += "{} {} {} ".format(result[0], result[1], result[2])
        else:
            outputLine += "-- -- -- "
    outputLine += " " + molecule + "\n"
    f_out.write(outputLine)
    rank += 1
f_out.close()

print(
    "Time to preprocess the individual docking calculations: %ss"
    % (round(time.time() - start, 2))
)
