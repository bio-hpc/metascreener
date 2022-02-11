#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import getopt
import os
import sys
import re
from .debug import Debug
from .debug import BColors
from subprocess import Popen, PIPE
from .debug import Debug


class InputParams(object):

    def __init__(self, cfg, argv):
        self.PROG_OPT_RE = re.compile(r'^([A-Z\d]+)[_-](?:([A-Z\d]+)[_-])?')
        self.cfg = cfg
        self.argv = argv
        self.TAG = "InputPArams"
        self.color = BColors.GREEN
        self.get_input_params()

    def get_input_params(self):
        if len(self.argv) == 1:
            self.cfg.print_format_help("Mandatory options:", "")
            self.cfg.print_format_help("-i", "result folder genereted by MetaScreener")
            self.cfg.print_format_help("-p", "Original target")
            self.cfg.print_format_help("--pdb", "Original target in pdb format")
            self.cfg.print_format_help("-l", "Original query")
            print("")
            self.cfg.print_format_help("Optional options:", "")
            self.cfg.print_format_help("--cores", "Maximum number of cores; Use 0 for autodetect; Default: 1")
            self.cfg.print_format_help("--profile", "webBD STANDARD_BD STANDARD_VS")
            self.cfg.print_format_help("--prog", "Software")
            self.cfg.print_format_help("--opt", "opt")

            self.cfg.print_format_help("-c", "cut-off of energies; Default: 0")
            self.cfg.print_format_help("-z", "Clustering only for BD; Deafult: y")
            self.cfg.print_format_help("-s", "Generate poseview; Deafult: y")
            self.cfg.print_format_help("-t", "Generate plip interactions; Deafult: y")
            self.cfg.print_format_help("-f", "If folder exits don't overwrite; Deafult: y")
            self.cfg.print_format_help("-a", "Generate pymol sessions with plip;"
                                             "Deafult: n")
            self.cfg.print_format_help("--rb", "Number of files saved as bestScore in VS. Default(50)")
            self.cfg.print_format_help("--rf", "Number of files saved in VS. Default (500)")
            self.cfg.print_format_help("-b", "Chain of residues split by ':', type cad_res_num, "
                                             " For example A_TYR_385:A_VAL_434:A_VAL_5")
            self.cfg.print_format_help("-e", "ONLY BD; calcula la distancia entre el centro del ligando original y el"
                                             " centro del ligando "
                                             "de docking; Deafult: n")

            self.cfg.print_format_help("-d", "Debug level; Deafult: 0 (off)")

            print("\nUsage: %s -i input Docking -p proteinFile -l ligFile -c min Score -s poseview y -z clusterizado y"
                  % sys.argv[0] + "\n")
            exit()
        print("Using {} core{} for procesing results.".format(self.cfg.cores, 's' if self.cfg.cores > 1 else ''))
        # Read command line args
        myopts, args = getopt.getopt(self.argv[1:], "i:p:l:c:s:z:t:d:k:f:a:b:r:e:",
                                     ["cores=", "prog=", "opt=", "profile=", "flex", "rb=", "rf=", "pdb="])

        for o, a in myopts:
            if o == '--profile':
                self.cfg.use_profile = a.upper()

        if self.cfg.use_profile:
            self.cfg.set_profile_cfg(self.cfg.use_profile)

        for o, a in myopts:
            if o == '-i':
                self.cfg.file_input = os.path.realpath(a if a.endswith('/') else "{}/".format(a))
            elif o == '-p':
                self.cfg.file_target = a
            elif o == '--pdb':
                self.cfg.file_target_pdb = a
            elif o == '-c':
                self.cfg.engCorte = float(a)
            elif o == '-l':
                self.cfg.file_query = a
            elif o == '-s':
                self.cfg.poseview = a
            elif o == '-z':
                self.cfg.clusterizado = a
            elif o == '-d':
                self.cfg.mode_debug = a
            elif o == '-a':
                self.cfg.plip = a
            elif o == '-f':
                self.cfg.createFolder = a
            elif o == '-e':
                self.cfg.distanceLigs = a
            elif o == '-b':
                aux = a.split(":")
                for i in aux:
                    self.cfg.resnPoseviewDetct.append(i)
            elif o == '--flex':
                self.cfg.flexible = True
            elif o == '--cores':
                self.cfg.cores = int(a)
                max_cores = cpu_count()
                if self.cfg.cores == 0 or self.cfg.cores > max_cores:
                    self.cfg.cores = max_cores
                elif self.cfg.cores < 0:
                    self.cfg.cores = 1
            elif o == '--profile':
                self.cfg.use_profile = a.upper()
            elif o == '--prog':
                self.cfg.programa = a.upper()
            elif o == '--opt':
                if not self.cfg.use_profile:
                    self.cfg.opcion = a.upper()
            elif o == '--rb':
                self.cfg.resultados_best_score = int(a)
            elif o == '--rf':
                self.cfg.resultados_ficheros = int(a)
            else:
                print("\nUsage: %s -i input Docking -p proteinFile -l ligFile -c min Score -s poseview y "
                      "-z clusterizado y -t inteacciones y -d debug [0-10]" % sys.argv[0] + "\n")
                exit()
        self.cfg.debug = Debug(self.cfg.mode_debug)

        self.cfg.file_target = os.path.realpath(self.cfg.file_target)
        if self.cfg.file_target_pdb:
            self.cfg.file_target_pdb = os.path.realpath(self.cfg.file_target_pdb)
        self.cfg.file_query = os.path.realpath(self.cfg.file_query)
        self.cfg.file_input = os.path.realpath(self.cfg.file_input)
        # Get compounds names and input path
        self.cfg.extract_names()

        if not self.cfg.file_target or not os.path.exists(self.cfg.file_target):
            print("Target(s) not indicated(s), aborting.")
            exit()
        elif not self.cfg.file_query or not os.path.exists(self.cfg.file_query):
            print("Query(s) not found, aborting.")
            exit()
        elif not self.cfg.file_input or not os.path.exists(self.cfg.file_input):
            print("Path of docking results not found, aborting.")
            exit()

        self.cfg.print_format("Input files:", "", "")
        self.cfg.print_format("", "Query: ", self.cfg.file_target)
        self.cfg.print_format("", "Ligands: ", self.cfg.file_query)
        self.cfg.print_format("", "Directory MetaScreener: ", self.cfg.file_input + "/")
        #
        #   Test folders
        #
        self.cfg.SHUTTLEMOL_DIRS = self.cfg.perfiles.get_folders()
        self.cfg.OUTPUT_DIRS = self.cfg.perfiles.get_out_folders()
        self.cfg.OUTPUT_GRAPHS = self.cfg.perfiles.get_files_out()
        self.cfg.ext_query = os.path.splitext(self.cfg.file_query)[1].strip()
        self.cfg.ext_target = os.path.splitext(self.cfg.file_target)[1].strip()

        comando = ("find " + self.cfg.file_input + "/" + self.cfg.SHUTTLEMOL_DIRS[
            'folderMolec'] + "/ ")
        aux = self.cfg.execute(self.TAG, comando)
        aux = aux.split("\n")
        if os.path.isdir(aux[0]):
            del aux[0]
        self.cfg.extLigand = str(os.path.splitext(aux[0])[1]).strip()
        self.cfg.print_format("", "Ext Prot: ", self.cfg.ext_target)
        self.cfg.print_format("", "Ext Lig: ", self.cfg.ext_query)
        if self.cfg.mode_debug:
            debug = Debug(self.cfg.mode_debug)
            for i in self.cfg.SHUTTLEMOL_DIRS:
                debug.show(self.TAG + " metascreener Dirs: " + i, self.color)
            for i in self.cfg.OUTPUT_DIRS:
                debug.show(self.TAG + " Out Dirs: " + i + " " + self.cfg.OUTPUT_DIRS[i], self.color)
            for i in self.cfg.OUTPUT_GRAPHS:
                debug.show(self.TAG + " Out Dirs: " + i + " " + self.cfg.OUTPUT_GRAPHS[i]['outPut'], self.color)

        if not self.cfg.programa or not self.cfg.opcion:
            match = self.PROG_OPT_RE.match(self.cfg.nameEntrada)
            if match and len(match.group()) > 1:
                self.cfg.programa = match.group(2).strip()
                self.cfg.opcion = match.group(1).strip()
            else:
                print("The program or the option could not be determined, aborting ")
                exit()
        self.cfg.print_format("\nTest data:", "", "")
        self.cfg.print_format("", "Software: ", self.cfg.programa)
        self.cfg.print_format("", "Technique: ", self.cfg.opcion)
        self.cfg.print_format("", "Molecules:", str(len(aux)) + "\n")


