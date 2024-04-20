#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jochem Nelen
#   Author: Carlos Martinez Cortes
#   Email:  jnelen@ucam.edu
#   Description: Performs ESSENCE-Dock Consensus scoring and post-processing for input docking runs
# ______________________________________________________________________________________________________________________

import argparse
import glob
import itertools
import json
import math
import os
import subprocess
import sys
import time
import warnings
from concurrent.futures import TimeoutError
from os.path import basename, join, splitext
from shutil import copyfile
from statistics import mean

from openbabel import pybel
from pebble import ProcessPool
from spyrmsd import io
from spyrmsd.rmsd import rmsdwrapper
from tqdm import tqdm

beginTime = time.time()
parser = argparse.ArgumentParser(
    description="Performs ESSENCE-Dock Consensus scoring for input docking runs"
)

parser.add_argument(
    "-f",
    "--file",
    type=argparse.FileType("r"),
    required=True,
    help="output file from the ESSENCE-Dock_cross.py",
)
parser.add_argument(
    "-r",
    "--receptor",
    required=False,
    default="no_receptor",
    type=str,
    help="Path to the protein receptor",
)
parser.add_argument(
    "-o", "--output", required=True, help="Path to the output directory"
)
parser.add_argument(
    "-n",
    "--max_results",
    required=False,
    default=50,
    type=int,
    help="The amount of molecules to include in the PyMol Session file",
)
parser.add_argument("-s", "--silent", required=False, default=False, help="Silent Mode")
parser.add_argument(
    "-t", "--timeout", default=3, required=False, help="Max time spent per compound"
)
parser.add_argument(
    "-c", "--cpus", default=1, required=False, help="Max number of CPUs to use"
)
parser.add_argument(
    "-raw",
    "--raw",
    required=False,
    default=False,
    help="Don't perform post-processing (PLIPS and PSE) for the best results",
)
parser.add_argument("-dd", required=False, help="Path to the DiffDock docking run")

warnings.filterwarnings("ignore", category=UserWarning)

args = parser.parse_args()

silentMode = False
skipPostProcessing = False
diffDockPath = args.dd
processDiffDock = False
max_results = args.max_results

timeoutLimit = float(args.timeout)

if "SLURM_CPUS_ON_NODE" in os.environ:
    max_workers = os.environ["SLURM_CPUS_ON_NODE"]
else:
    max_workers = args.cpus

print(f"using {max_workers} CPUs, timeoutlimit: {timeoutLimit}s")
if args.silent == "true":
    silentMode = True

if args.raw == "true":
    skipPostProcessing = True

if not args.receptor == "no_receptor":
    proteinPath = args.receptor
    proteinName = splitext(basename(proteinPath))[0] + "_"
else:
    proteinName = ""

ob_log_handler = pybel.ob.OBMessageHandler()
pybel.ob.obErrorLog.SetOutputLevel(0)

FILE_EXT = {}
FILE_EXT["AD"] = ".pdbqt"
FILE_EXT["LF"] = ".mol2"
FILE_EXT["GN"] = ".pdbqt"
FILE_EXT["DD"] = ".sdf"

lines = args.file.readlines()
softwares = lines[0].strip().split(",")
allSoftwares = softwares

DiffDockDict = {}


def formatTime(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    if hours > 0:
        return f"{int(hours)}h {int(minutes)}min {int(seconds)}s"
    else:
        return f"{int(minutes)}min {int(seconds)}s"


## ESSENCE-Dock scoringfunction
def calcESSENCEDockScore(line, calcRmsd=True):
    lineSplit = line.strip().split()
    compoundName = lineSplit[-1]

    compoundDict = {}

    bindingEnergies = []
    ranks = []

    spyrmsdMolDict = {}

    outputLineList = [compoundName]

    for i, sw in enumerate(softwares):
        ## iterate over the first indices and add them to the compoundDict: path, energy and rank
        compoundDict[sw] = {}

        if not "--" in lineSplit[3 * i]:
            rank, energy, path = (
                lineSplit[3 * i],
                lineSplit[(3 * i) + 1],
                lineSplit[(3 * i) + 2],
            )
        else:
            rank, energy, path = 9999999, 99, "N/A"

        ranks.append(float(rank))
        bindingEnergies.append(float(energy))

        molPath = path.replace("/energies/", "/molecules/") + FILE_EXT[sw]

        try:
            mol = io.loadmol(molPath)
        except:
            mol = None

        compoundDict[sw]["rank"] = rank
        compoundDict[sw]["energy"] = energy
        compoundDict[sw]["energy_path"] = path
        compoundDict[sw]["molpath"] = molPath

        spyrmsdMolDict[sw] = mol

        ## Add individual docking data to the CSV
        outputLineList += [str(rank), str(energy)]

    if processDiffDock == True:
        compoundDict["DD"] = {}
        if compoundName in DiffDockDict:
            compoundDict["DD"]["molpath"] = DiffDockDict[compoundName]
            compoundDict["DD"]["energy"] = "NoScore"
        else:
            compoundDict["DD"]["molpath"] = "N/A"
        try:
            mol = io.loadmol(DiffDockDict[compoundName])
        except:
            mol = None

        spyrmsdMolDict["DD"] = mol

    ## Calculate RMSDs
    if calcRmsd:
        RMSDlist = []

        for combination in combinations:
            mol1 = spyrmsdMolDict[combination[0]]
            mol2 = spyrmsdMolDict[combination[1]]

            if mol1 == None or mol2 == None:
                RMSDlist.append(99)
                outputLineList.append(str(99))
                continue

            try:
                rmsd = rmsdwrapper(mol1, mol2)
            except:
                rmsd = [99]

            rmsd = round(rmsd[0], 4)

            RMSDlist.append(rmsd)
            outputLineList.append(str(rmsd))
    else:
        RMSDlist = [99] * len(combinations)
        outputLineList += ["99"] * len(combinations)

    if len(RMSDlist) > 1:
        meanRMSD = round(mean(RMSDlist), 3)
        outputLineList.append(str(meanRMSD))
    else:
        meanRMSD = RMSDlist[0]

    ## Find valid path to calculate rotatable bonds. pdb(qt) format is excluded if other softwares are available because it doesn't always define double bonds properly
    rotBondsPath = "N/A"
    for sw in allSoftwares:
        if onlyPDBtype == False:
            if not "N/A" in compoundDict[sw]["molpath"] and not ".pdb" in FILE_EXT[sw]:
                rotBondsPath = compoundDict[sw]["molpath"]
                break
        else:
            if not "N/A" in compoundDict[sw]["molpath"]:
                rotBondsPath = compoundDict[sw]["molpath"]
                break

    if rotBondsPath == "N/A":
        print(
            f"Skipping molecule {compoundName}, could not accurately determine rotatable bonds.."
        )
        compoundDict["score"] = 99
        outputLineList += [
            "-1",
            str(round(mean(ranks), 1)),
            str(round(mean(bindingEnergies), 3)),
            "99\n",
        ]
        compoundDict["output"] = ",".join(outputLineList)
        return compoundDict

    ## Calculate Rotatable Bonds
    try:
        rotbondMol = next(pybel.readfile(rotBondsPath.split(".")[-1], rotBondsPath))
        rotBonds = rotbondMol.OBMol.NumRotors()
    except:
        print(
            f"Skipping molecule {compoundName}, could not accurately determine rotatable bonds.."
        )
        compoundDict["score"] = 99
        outputLineList += [
            "-1",
            str(round(mean(ranks), 1)),
            str(round(mean(bindingEnergies), 3)),
            "99\n",
        ]
        compoundDict["output"] = ",".join(outputLineList)
        return compoundDict

    outputLineList.append(str(rotBonds))

    ## Calculate Mean_Binding_Energy and Mean_Rank
    meanRank = str(round(mean(ranks), 1))
    meanBindingEnergy = str(round(mean(bindingEnergies), 3))
    outputLineList += [str(meanRank), str(meanBindingEnergy)]

    ## Calculate ESSENCE-Dock_Score
    ESSENCEDockScore = round(
        (math.sqrt((2 / float(meanRMSD))) * float(meanBindingEnergy))
        * (math.sqrt(math.log(rotBonds + 1) + 1)),
        3,
    )
    compoundDict["score"] = float(ESSENCEDockScore)
    outputLineList.append(str(ESSENCEDockScore))

    outputLine = ",".join(outputLineList) + "\n"

    compoundDict["output"] = outputLine
    return compoundDict


## Check if a DiffDock Run is included, if so make DiffDockDict
if not diffDockPath == "N/A":
    DDpaths = glob.glob(f"{diffDockPath}/molecules/*{FILE_EXT['DD']}")
    for DDpath in DDpaths:
        DDname = basename(DDpath).split("VS_DD_")[-1].split("_rank1")[0]
        DiffDockDict[DDname] = DDpath

    allSoftwares = softwares + ["DD"]
    processDiffDock = True

## Determine if only pdbqt ligands are present
onlyPDBtype = True
for sw in allSoftwares:
    if not ".pdb" in FILE_EXT[sw]:
        onlyPDBtype = False
if onlyPDBtype == True:
    print(
        "Only .pdb(qt) ligand types present.. Rotatable Bond count might have inaccuracies.."
    )

consensusPath = f"{args.output}/{'_'.join(allSoftwares)}_{proteinName}ESSENCE-Dock_Consensus_AllCompounds.csv"

## Make Header
headerList = ["Ligand_Name"]

for sw in softwares:
    headerList += [f"{sw}_Rank", f"{sw}_Binding_Energy"]

RMSDlist = []

combinations = list(itertools.combinations(allSoftwares, 2))
for combination in combinations:
    RMSDlist.append(f"RMSD_{combination[0]}_{combination[1]}")
if len(RMSDlist) > 1:
    RMSDlist.append("RMSD_Average")

headerList += RMSDlist
headerList += ["Rotatable_Bonds", "Mean_Rank", "Mean_Binding_Energy"]
headerList.append("ESSENCE-Dock_Score")
headerLine = ",".join(headerList) + "\n"

dockingDict = {}

## Start processing the compounds
with ProcessPool(max_workers=int(max_workers)) as pool:
    future = pool.map(calcESSENCEDockScore, lines[1:], timeout=timeoutLimit)

    iterator = future.result()
    pbar = tqdm(total=len(lines[1:]), disable=silentMode, ascii=True)
    idx = 1
    while True:
        try:
            result = next(iterator)
            dockingDict[result["output"].split(",")[0]] = result
            pbar.update(1)
            idx += 1
        except StopIteration:
            break
        except TimeoutError:
            failedLine = lines[idx]
            failedCompound = failedLine.strip().split()[-1]

            print(failedCompound, "timed out")
            dockingDict[failedCompound] = calcESSENCEDockScore(
                failedLine, calcRmsd=False
            )
            pbar.update(1)
            idx += 1
        except Exception as error:
            failedLine = lines[idx]
            failedCompound = failedLine.strip().split()[-1]
            dockingDict[failedCompound] = calcESSENCEDockScore(
                failedLine, calcRmsd=False
            )
            print(failedCompound, "failed to process")
            print(error.traceback)
            pbar.update(1)
            idx += 1
    pbar.close()


## Sort the outputFile
sorted_keys = sorted(dockingDict, key=lambda k: dockingDict[k]["score"])
with open(consensusPath, "w") as outputFileAllSorted:
    outputFileAllSorted.write(headerLine)
    for key in sorted_keys:
        outputFileAllSorted.write(dockingDict[key]["output"])
print(f"\nWrote ESSENCE-Dock Calculations to {consensusPath}")

if skipPostProcessing == True:
    print("\nSkipping post-processing..")
    sys.exit(f"Finished calculations after {formatTime(round(time.time()-beginTime))}")

## Post-processing
print(
    f"\nESSENCE-Dock scoring done after {formatTime(round(time.time()-beginTime))}. Starting post-processing on top {max_results} compounds now.."
)
beginPostProcessTime = time.time()

moleculesPath = f"{args.output}/Molecules/"
if not os.path.isdir(moleculesPath):
    os.mkdir(moleculesPath)

postprocess_path = f"{args.output}/{'_'.join(allSoftwares)}_{proteinName}ESSENCE-Dock_Consensus_Top{max_results}"
pml_path = postprocess_path + ".pml"

interactionDict = {}

## Defining post-processing functions
PYTHON_RUN = "python"
PLIP_SCRIPT = (
    PYTHON_RUN
    + " "
    + join(
        "MetaScreener",
        "extra_metascreener",
        "used_by_metascreener",
        "create_ligand_plip_ESSENCE-Dock.py {} {} {} {}",
    )
)
PYMOL_SCRIPT = (
    PYTHON_RUN
    + " "
    + join(
        "MetaScreener",
        "extra_metascreener",
        "used_by_metascreener",
        "create_ligand_pymol_ESSENCE-Dock.py {} {} {} {}",
    )
)
PML_HEAD_PYMOL = (
    PYTHON_RUN
    + " MetaScreener/extra_metascreener/used_by_metascreener/create_header_pml.py -t {}"
)


def cp_file(file, folder):
    copyfile(file, join(folder, basename(file)))


def execute_command(cmd):
    return subprocess.check_output(cmd, shell=True).decode("UTF-8")


def add_receptor(receptor, folder_molecules):
    cp_file(receptor, folder_molecules)
    receptor = "Molecules/" + basename(receptor)
    cmd = PML_HEAD_PYMOL.format(receptor)
    return subprocess.check_output(cmd, shell=True).decode("UTF-8")

## Start generating PLIPS for the top compounds
with open(postprocess_path + ".csv", "w") as outputFileTop:
    outputFileTop.write(headerLine)

    pml_lst = [add_receptor(proteinPath, moleculesPath)]
    proteinPath = moleculesPath + basename(proteinPath)

    compoundRank = 0
    for i, key in enumerate(
        tqdm(sorted_keys[:max_results], disable=silentMode, ascii=True)
    ):
        outputFileTop.write(dockingDict[key]["output"])
        interactionDict[key] = {}

        groupList = []
        for sw in allSoftwares:
            molPath = dockingDict[key][sw]["molpath"]

            if not "N/A" in molPath:
                try:
                    cp_file(molPath, moleculesPath)
                except:
                    print(
                        f"Couldn't find the ligand at {molPath}. Is the extension {FILE_EXT[sw]} as configured in FILE_EXT?"
                    )
                    continue

                cpPath = moleculesPath + basename(molPath)
                prefix = splitext(cpPath)[0]
                interactionsPath = f"{prefix}_interactions.json"

                compoundScore = dockingDict[key][sw]["energy"]
                if not compoundScore == "NoScore":
                    compoundScore = round(float(compoundScore), 2)

                ## Calculate PLIP interaction
                execute_command(PLIP_SCRIPT.format(proteinPath, cpPath, prefix, str(max_workers)))

                ## Handle cases where something goes wrong
                try:
                    with open(interactionsPath, "r") as interactionJSONFile:
                        interactionJSON = json.load(interactionJSONFile)
                except:
                    print(
                        f"Error: Something went wrong while generating the PLIP interaction for VS_{sw}_{key}, adding it to PSE without PLIP interactions.."
                    )
                    interactionDict[key][sw] = {}
                    cmd = PYMOL_SCRIPT.format(
                        f"{cpPath}", proteinPath, f"{compoundScore}", ""
                    )
                    pml_lst.append(execute_command(cmd))
                    groupList.append(
                        f"{splitext(basename(molPath))[0]}_{compoundScore}"
                    )
                    continue

                ## Parse PLIP interaction to interactionDict
                interactionDict[key][sw] = {}
                for interactionType in interactionJSON["interactions_groups"].keys():
                    interactionList = []
                    for interaction in interactionJSON["interactions_groups"][
                        interactionType
                    ]["interactions"]:
                        interactionSplit = interaction.split("|")
                        interactionList.append(
                            f"{interactionSplit[1]}{interactionSplit[0]}"
                        )
                    interactionDict[key][sw][interactionType] = interactionList

                ## Generate PML code
                cmd = PYMOL_SCRIPT.format(
                    f"Molecules/{basename(molPath)}",
                    proteinPath,
                    f"{compoundScore}",
                    interactionsPath,
                )
                pml_lst.append(execute_command(cmd))
                groupList.append(f"{splitext(basename(molPath))[0]}_{compoundScore}")

        ## Group different Docking Softwares under the same group
        group_name = f"{compoundRank+1}_{key}_{dockingDict[key]['score']}"
        pml_lst.append(f"\ncmd.group('{group_name}', '{' '.join(groupList)}')\n")
        pml_lst.append(f"cmd.disable('{group_name}')\n")

        compoundRank += 1

## Write PML file
pmlPath = f"{postprocess_path}.pml"
with open(pmlPath, "w") as pmlFile:
    for line in pml_lst:
        pmlFile.write(line)

## Write interactionDict to json file
interactionDictPath = f"{args.output}/{'_'.join(allSoftwares)}_{proteinName}ESSENCE-Dock_PLIP_interactions_Top{max_results}.json"
with open(interactionDictPath, "w") as interactionJSONFileOutput:
    json.dump(interactionDict, interactionJSONFileOutput, indent=4)
    print(f"\nWrote Protein-Interaction json-file to {interactionDictPath}")

## Create and write interaction csv file
interactionCsvPath = f"{args.output}/{'_'.join(allSoftwares)}_{proteinName}ESSENCE-Dock_PLIP_interactions_Top{max_results}.csv"

ligandList = []
residueList = []

# Get all the residue interaction so they can be sorted
for ligand in interactionDict:
    for mode in interactionDict[ligand].keys():
        ligandList.append(ligand + "_" + mode)
        for interactionType in interactionDict[ligand][mode]:
            for residue in interactionDict[ligand][mode][interactionType]:
                if residue not in residueList:
                    residueList.append(residue)

## Sort residue on residue number
residueList = sorted(residueList, key=lambda x: float(x[3:]))

with open(interactionCsvPath, "w") as interactionJSONFileOutput:
    ## Write CSV Header
    interactionJSONFileOutput.write(",".join([""] + residueList) + "\n")

    ## Get the PLIP interactions from the interactionDict
    for ligand in ligandList:
        csvLine = [ligand]
        ligandSplit = ligand.split("_")

        ligandName = "_".join(ligandSplit[:-1])
        dockingMethod = ligandSplit[-1]
        ligandInteractions = []

        ## Get all the specific PLIP interactions and add them to a list
        for interactionType in interactionDict[ligandName][dockingMethod].keys():
            for residue in interactionDict[ligandName][dockingMethod][interactionType]:
                ligandInteractions.append(residue)

        ## Count the specific PLIP interactions for each ligand
        for residue in residueList:
            if residue in ligandInteractions:
                csvLine.append(str(ligandInteractions.count(residue)))
            else:
                csvLine.append("0")

        interactionJSONFileOutput.write(",".join(csvLine) + "\n")
    print(f"Wrote Protein-Interaction Spreadsheet to {interactionCsvPath}")

print(
    f"\nFinished post-processing after {formatTime(round(time.time()-beginPostProcessTime))}"
)
sys.exit(f"Finished all calculations after {formatTime(round(time.time()-beginTime))}")
