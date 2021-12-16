#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Pe��a Garc��a
#   Author: Carlos Mart��nez Cort��s
#   Email:  cmartinez1@ucam.edu
#   Description: Script that automates the filtering process to find the best results in the tests performed with MetaScreener
# ______________________________________________________________________________________________________________________
import re
import subprocess
import time
import sys
from Get_histogram import *

PROG_OPT_RE = re.compile(r'^([A-Z\d]+)[_-](?:([A-Z\d]+)[_-])?')


def execute(instance, text, cfg):
    start_time = time.time()
    print("+ " + text)
    instance(cfg)
    print("- End " + text + "-- {:.1f} s".format(time.time() - start_time))


def check_profile(cfg):
    if cfg.profile == "RAW":
        cmd = 'tar cvzf {} {}'.format(cfg.file_input + ".tar.gz", cfg.file_input)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)


if __name__ == "__main__":

    time_start = time.time()

    cfg = ConfigHolder(PYTHON_RUN)
    InputParams(cfg, sys.argv)
    check_profile(cfg)

    execute(CreateFolders, "Create folders", cfg)

    execute(ReadData, "Read Data", cfg)

    execute(GlobalHistogram, "Generating Global histogram", cfg)

    execute(SaveResults, "Saving Results", cfg)

    if cfg.profile != "UNCLUSTERED_BD":
        execute(Clustered, "Clusterizado BD", cfg)
    else:
        execute(SavePoses, "Saving all poses files", cfg)

    prefix_out = os.path.join(cfg.OUTPUT_DIRS['workdir'], cfg.name_input + "_clustered_finger_print")
    CreateFingerPrint(cfg, prefix_out)

    if cfg.plip:
        execute(PlipGraph, "Calculating PLIP interactions", cfg)

    execute(GenerateFilePymol, "Creating PyMOL Files", cfg)

    if cfg.opcion == "BD" and cfg.distanceGraph:
        execute(DistanceGraph, "Generating distance Graphs", cfg)

    if cfg.poseview:
        if os.path.isfile("MetaScreener/external_sw/poseview/poseview"):
            execute(PoseviewGraph, "Generating Poseview files", cfg)
        else:
            print("+ Generating Poseview files")
            print("ERROR: MetaScreener/external_sw/poseview/poseview doesn't exist")
            print("The poseview will not be generated")

    execute(EnergyHistogram, "Generating Energy Histogram", cfg)

    if cfg.opcion == "SD":
        print(MutacionGraphs, "+ Generating Mutation Graph", cfg)

    if cfg.join_images:
        execute(JoinImages, "Join Images", cfg)

    if cfg.compress:
        execute(ResultPacker, "Compressing Results", cfg)

    print("- Finished experiment -- {:.1f} s".format(time.time() - time_start))




