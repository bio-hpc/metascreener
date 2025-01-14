#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Generates all necessary folder for analyze the results
# ______________________________________________________________________________________________________________________
import os
import shutil
import glob


class CreateFolders(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.create_paths()

    def create_paths(self):
        for kdir, vdir in self.cfg.SHUTTLEMOL_DIRS.items():
            vdir = os.path.join(self.cfg.file_input, vdir)
            self.cfg.SHUTTLEMOL_DIRS[kdir] = vdir

        for kdir, vdir in self.cfg.OUTPUT_DIRS.items():
            vdir = os.path.join(self.cfg.file_input, vdir)
            self.cfg.OUTPUT_DIRS[kdir] = vdir

            if self.cfg.createFolders and os.path.exists(vdir) and vdir != self.cfg.file_input:
                print("  + Delete directory '{}' already exist".format(vdir))
                shutil.rmtree(vdir)

            if not os.path.exists(vdir):
                print("  + Create directory {}".format(vdir))
                os.makedirs(vdir)

