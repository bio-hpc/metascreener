#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: This class has of possible parameters
# ______________________________________________________________________________________________________________________
import os
import sys
from .Profiles import Profiles

from .debug import BColors
from .GraphicsGenerator import GraphicsGenerator
import subprocess


class ConfigHolder(object):

    def print_error(self, tag, txt):
        print('{}ERROR: {} {}  {} '.format(BColors.FAIL, tag, BColors.ENDC, txt) )

    def print_format(self, txt1, txt2, txt3):
        print(self.format_paramp.format(txt1, txt2, txt3))

    def print_format_help(self, txt1, txt2):
        print (self.format_paramp_h.format(BColors.GREEN+txt1, BColors.BLUE+txt2 + BColors.ENDC))

    def execute(self, tag, command):
        try:
            color = BColors.GREEN
            
            self.debug.show(tag + str(command), color)
            output = subprocess.check_output(command, shell=True)
            self.debug.show(str(tag) + str(output), color)
            if sys.version_info[0] == 3:
                return str(output, 'utf-8')
            else:
                return str(output)
        except Exception as e:
            self.print_error(tag, e)



    def execute_stderr(self, tag, cmd):
        color = BColors.GREEN
        self.debug.show(tag + cmd, color)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

        self.debug.show(str(tag) + str(output), color)
        if sys.version_info[0] == 3:
            return str(output, 'utf-8')
        else:
            return str(output)

    def print_best_poses(self):
        for i in self.best_poses:
            print(i.score, i.filename, i.coords)
        print(len(self.best_poses))

    def print_plot_data(self):
        for i in self.plot_data:
            print (i)

    def __init__(self, python_run):
        self.error_array = []
        self.best_poses = []
        self.plot_data = []
        self.format_paramp = '{0:>5}{1:<25} {2:<20}'
        self.format_paramp_h = '{0:>13}\t{1:<40}'
        self.perfiles = Profiles(self)
        self.file_input = ''
        self.file_target = ''
        self.file_target_pdb = ''
        self.file_query = ''
        #
        #   Default options, these options can be modified by changing profiles
        #
        self.cores = 1
        self.option = ""
        self.software = ""
        self.dpi = 200
        self.mode_debug = 0
        self.engCorte = 0
        self.resn_poseview_detct = []
        self.python_exe = python_run
        self.format_graph = 'svg'


        #
        #   Pymol
        #
        self.visualize_target = "surface"
        self.color_target = "green"
        self.transparency_target = "0.7"

        # To be defined later
        self.createFolders = True
        self.name_target, self.ext_target = None, None
        self.name_query, self.ext_query = None, None
        self.name_input = None
        self.cpy_file_target = None
        #
        #   Paths
        #   
        self.external_sw_folder = "MetaScreener/external_sw/"
        self.extra_metascreener = "MetaScreener/extra_metascreener/used_by_metascreener/"
        self.login_node = "MetaScreener/login_node/"
        self.graph_energies = os.path.join(self.extra_metascreener, "create_ligand_graphs.py")
        self.ligand_pml = os.path.join(self.extra_metascreener, "create_ligand_pymol.py")
        self.ligand_plip = os.path.join(self.extra_metascreener, "create_ligand_plip.py")
        self.ligand_poseview = os.path.join(self.extra_metascreener, "create_ligand_poseview.py")
        self.generate_cube_pymol = os.path.join(self.extra_metascreener, "generate_cube_pymol.py")
        self.generate_headr_pml_pml = os.path.join(self.extra_metascreener, "create_header_pml.py")

        self.convert_to = os.path.join(self.extra_metascreener, "convert_to.py")


        self.debug = None
        self.graphicsGenerator = GraphicsGenerator()

    def extract_names(self):
        self.name_target, self.ext_target = self.get_name_type(self.file_target)
        self.name_query, self.ext_query = self.get_name_type(self.file_target)
        self.name_input = os.path.basename(self.file_input)

    @staticmethod
    def get_name_type(path):
        if os.path.isfile(path):
            tmp = os.path.basename(path)
            return os.path.splitext(tmp)
        else:
            return None, None

    def setattr(self, k, v):
        setattr(self, k, v)

    def set_profile_cfg(self, profile):
        self.perfiles.set_profile_cfg(profile)




